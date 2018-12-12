import argparse
import asyncio
import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, MutableMapping, Optional, Set, TypeVar

import aiohttp

from linty_fresh.problem import Problem, TestProblem


PR_URL_REGEX = re.compile(r'https?://.*?github.com/'
                          r'(?:repos/)?'
                          r'(?P<organization>[^/]*)/'
                          r'(?P<repo>[^/]*)/pulls?/'
                          r'(?P<pr_number>\d*)')
HUNK_REGEX = re.compile(r'@@ \-\d+,\d+ \+(\d+),\d+ @@')
FILE_START_REGEX = re.compile(r'\+\+\+ b/(.*)')
LINK_REGEX = re.compile(r'<(?P<url>.+)>; rel="(?P<rel>\w+)"')
NEW_FILE_SECTION_START = 'diff --git a'
MAX_LINT_ERROR_REPORTS = 10


class HadLintErrorsException(Exception):
    pass


class ExistingGithubMessage(object):
    def __init__(self,
                 comment_id: Optional[int],
                 path: str,
                 position: int,
                 body: str) -> None:
        self.comment_id = comment_id
        self.path = path
        self.position = position
        self.body = body

    def __hash__(self):
        return hash((self.path, self.position, self.body))

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return (self.path == other.path and
                    self.position == other.position and
                    self.body == other.body)
        return False

GenericProblem = TypeVar('GenericProblem', Problem, TestProblem)


class GithubReporter(object):

    def __init__(self,
                 auth_token: str,
                 organization: str,
                 repo: str,
                 pr_number: int,
                 commit: str,
                 delete_previous_comments: bool) -> None:
        self.auth_token = auth_token
        self.organization = organization
        self.repo = repo
        self.pr = pr_number
        self.commit = commit
        self.delete_previous_comments = delete_previous_comments

    async def report(self, linter_name: str,
                     problems: List[GenericProblem]) -> None:
        if not problems:
            grouped_problems = {}
        elif isinstance(list(problems)[0], TestProblem):
            grouped_problems = TestProblem.group_by_group(problems)
        else:
            grouped_problems = Problem.group_by_path_and_line(problems)

        headers = {
            'Authorization': 'token {}'.format(self.auth_token),
        }
        with aiohttp.ClientSession(headers=headers) as client_session:
            (line_map, existing_messages, message_ids) = await asyncio.gather(
                self.create_line_to_position_map(client_session),
                self.get_existing_pr_messages(client_session, linter_name),
                self.get_existing_issue_message_ids(client_session,
                                                    linter_name))
            lint_errors = 0
            review_comment_awaitable = []
            pr_url = self._get_pr_url()
            no_matching_line_number = []
            for location, problems_for_line in grouped_problems:
                message_for_line = ['{0} says:'.format(linter_name), '']

                reported_problems_for_line = set()

                path = location[0]
                line_number = location[1]
                position = line_map.get(path, {}).get(line_number, None)
                if position is None and path in line_map:
                    file_map = line_map[path]
                    closest_line = min(file_map.keys(),
                                       key=lambda x: abs(x-line_number))
                    position = file_map[closest_line]
                    message_for_line.append('(From line {})'.format(
                        line_number))
                message_for_line.append('```')
                if position is not None:
                    for problem in problems_for_line:
                        if problem.message not in reported_problems_for_line:
                            message_for_line.append(problem.message)
                            reported_problems_for_line.add(problem.message)
                    message_for_line.append('```')
                    message = '\n'.join(message_for_line)
                    try:
                        existing_messages.remove(
                            ExistingGithubMessage(None, path, position,
                                                  message))
                    except KeyError:
                        lint_errors += 1
                        if lint_errors <= MAX_LINT_ERROR_REPORTS:
                            data = json.dumps({
                                'body': message,
                                'commit_id': self.commit,
                                'path': path,
                                'position': position,
                            }, sort_keys=True)
                            review_comment_awaitable.append(
                                client_session.post(pr_url, data=data))
                else:
                    no_matching_line_number.append((location,
                                                    problems_for_line))

            if lint_errors > MAX_LINT_ERROR_REPORTS:
                message = """{0} says:

Too many lint errors to report inline!  {1} lines have a problem.
Only reporting the first {2}.""".format(
                    linter_name, lint_errors, MAX_LINT_ERROR_REPORTS)
                data = json.dumps({
                    'body': message
                })
                review_comment_awaitable.append(
                    asyncio.ensure_future(client_session.post(
                        self._get_issue_url(),
                        data=data)))

            if self.delete_previous_comments:
                for message_id in message_ids:
                    review_comment_awaitable.append(
                        asyncio.ensure_future(client_session.delete(
                            self._get_delete_issue_comment_url(message_id))))
                for message in existing_messages:
                    review_comment_awaitable.append(
                        asyncio.ensure_future(client_session.delete(
                            self._get_delete_pr_comment_url(
                                message.comment_id))))

            if no_matching_line_number:
                no_matching_line_messages = []
                for location, problems_for_line in no_matching_line_number:
                    lint_errors += 1
                    path = location[0]
                    line_number = location[1]
                    no_matching_line_messages.append(
                        '{0}:{1}:'.format(path, line_number))
                    for problem in problems_for_line:
                        no_matching_line_messages.append('\t{0}'.format(
                            problem.message))
                message = ('{0} says: I found some problems with lines not '
                           'modified by this commit:\n```\n{1}\n```'.format(
                               linter_name,
                               '\n'.join(no_matching_line_messages)))
                data = json.dumps({
                    'body': message
                })
                review_comment_awaitable.append(
                    asyncio.ensure_future(client_session.post(
                        self._get_issue_url(), data=data)))

            responses = await asyncio.gather(
                *review_comment_awaitable
            )  # type: List[aiohttp.ClientResponse]
            for response in responses:
                response.close()

            if lint_errors > 0:
                raise HadLintErrorsException()

    async def create_line_to_position_map(
        self, client_session: aiohttp.ClientSession
    ) -> MutableMapping[str, Dict[int, int]]:
        result = defaultdict(dict)  # type: MutableMapping[str, Dict[int, int]]
        current_file = ''
        position = -1
        right_line_number = -1

        headers = {
            'Accept': 'application/vnd.github.diff',
        }
        url = ('https://api.github.com/repos/'
               '{organization}/{repo}/pulls/{pr}'.format(
                   organization=self.organization,
                   repo=self.repo,
                   pr=self.pr))
        async with client_session.get(url, headers=headers) as response:
            # Collect the entire response before reading it. If you iterate
            # over lines instead, very long lines cause exceptions
            content = b''
            async for chunk in response.content.iter_any():
                content += chunk

            for line in content.splitlines():
                line = line.decode()
                file_match = FILE_START_REGEX.match(line)
                if file_match:
                    current_file = file_match.groups()[0].strip()
                    right_line_number = -1
                    position = -1

                if current_file and not file_match:
                    position += 1
                    hunk_match = HUNK_REGEX.match(line)
                    if hunk_match:
                        right_line_number = int(hunk_match.groups()[0]) - 1
                    elif not line.startswith('-'):
                        right_line_number += 1
                        result[current_file][right_line_number] = position

        return result

    def _get_pr_url(self) -> str:
        return ('https://api.github.com/repos/'
                '{organization}/{repo}/pulls/{pr}/comments'.format(
                    organization=self.organization,
                    repo=self.repo,
                    pr=self.pr))

    def _get_issue_url(self) -> str:
        return ('https://api.github.com/repos/'
                '{organization}/{repo}/issues/{pr}/comments'.format(
                    organization=self.organization,
                    repo=self.repo,
                    pr=self.pr))

    def _get_delete_pr_comment_url(self, comment_id: int) -> str:
        return ('https://api.github.com/repos/'
                '{organization}/{repo}/pulls/comments/{comment_id}'.format(
                    organization=self.organization,
                    repo=self.repo,
                    comment_id=comment_id))

    def _get_delete_issue_comment_url(self, comment_id: int) -> str:
        return ('https://api.github.com/repos/'
                '{organization}/{repo}/issues/comments/{comment_id}'.format(
                    organization=self.organization,
                    repo=self.repo,
                    comment_id=comment_id))

    async def get_existing_issue_message_ids(
        self, client_session: aiohttp.ClientSession, linter_name: str
    ) -> Set[str]:
        url = self._get_issue_url()
        messages_json = await self._fetch_message_json_from_url(
            client_session, url, linter_name)
        message_ids = set()  # type: Set[str]
        for blob in messages_json:
            if self._is_linter_message(blob['body'], linter_name):
                message_ids.add(blob['id'])

        return message_ids

    async def get_existing_pr_messages(
        self, client_session: aiohttp.ClientSession, linter_name: str
    ) -> Set[ExistingGithubMessage]:
        url = self._get_pr_url()
        existing_messages = set()  # type: Set[ExistingGithubMessage]
        messages_json = await self._fetch_message_json_from_url(
            client_session, url, linter_name)

        for comment in messages_json:
            body = comment['body']
            if not self._is_linter_message(body, linter_name):
                continue

            existing_messages.add(
                ExistingGithubMessage(comment['id'],
                                      comment['path'],
                                      comment['position'],
                                      body))

        return existing_messages

    @staticmethod
    async def _fetch_message_json_from_url(
            client_session, url, linter_name
    ) -> [Any]:
        messages_json = []
        async with client_session.get(url) as response:
            response = response  # type: aiohttp.ClientResponse
            messages = json.loads(await response.text())
            messages_json += messages
            next_url = GithubReporter._find_next_url(response)

        if next_url:
            messages_json += await GithubReporter._fetch_message_json_from_url(
                client_session, next_url, linter_name)

        return messages_json

    @staticmethod
    def _find_next_url(response: aiohttp.ClientResponse) -> str:
        if 'link' in response.headers:
            links = response.headers['link'].split(',')
            for link in links:
                match = LINK_REGEX.match(link)
                if match and match.group('rel') == 'next':
                    return match.group('url')

    @staticmethod
    def _is_linter_message(text: str, linter_name: str) -> bool:
        return text.startswith('{} says:'.format(linter_name))


def register_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--pr_url',
                        type=str,
                        help='The URL for the Pull Request for this commit.')
    parser.add_argument('--commit',
                        type=str,
                        help='The commit being linted.')


def create_reporter(args: Any) -> GithubReporter:
    if not args.pr_url or not args.commit:
        raise Exception('Must specify both a pr_url and a commit to use the '
                        'github reporter.')
    auth_token = os.getenv('GITHUB_AUTH_TOKEN')
    if not auth_token:
        raise Exception('Environment Variable $GITHUB_AUTH_TOKEN must be set '
                        'to use the github reporter.')
    match = PR_URL_REGEX.match(args.pr_url)
    if match:
        groups = match.groupdict()
        return GithubReporter(auth_token,
                              groups['organization'],
                              groups['repo'],
                              int(groups['pr_number']),
                              args.commit,
                              args.delete_previous_comments)
    else:
        raise Exception("{} doesn't appear to be a valid github pr url".format(
            args.pr_url
        ))
