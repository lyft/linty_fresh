import argparse
import asyncio
import json
import os
import re

from collections import defaultdict

import aiohttp

from linty_fresh.problem import Problem

from typing import Any, Dict, List, MutableMapping, NamedTuple, Set


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

ExistingGithubMessage = NamedTuple('ExistingGithubMessage',
                                   [('path', str),
                                    ('position', int),
                                    ('body', str)])


class GithubReporter(object):
    def __init__(self,
                 auth_token: str,
                 organization: str,
                 repo: str,
                 pr_number: int,
                 commit: str) -> None:
        self.auth_token = auth_token
        self.organization = organization
        self.repo = repo
        self.pr = pr_number
        self.commit = commit

    async def report(self, problems: List[Problem]) -> None:
        grouped_problems = Problem.group_by_path_and_line(problems)

        headers = {
            'Authorization': 'token {}'.format(self.auth_token),
        }
        with aiohttp.ClientSession(headers=headers) as client_session:
            (line_map, existing_messages) = await asyncio.gather(
                self.create_line_to_position_map(client_session),
                self.get_existing_messages(client_session))
            lint_errors = 0
            review_comment_awaitable = []
            pr_url = self._get_pr_url()
            no_matching_line_number = []
            for location, problems_for_line in grouped_problems:
                message_for_line = [':sparkles:Linty Fresh Says:sparkles::',
                                    '']

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
                    if (path, position, message) not in existing_messages:
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
                message = ''':sparkles:Linty Fresh Says:sparkles::

Too many lint errors to report inline!  {0} lines have a problem.
Only reporting the first {1}.'''.format(
                    lint_errors, MAX_LINT_ERROR_REPORTS)
                data = json.dumps({
                    'body': message
                })
                review_comment_awaitable.append(
                    asyncio.ensure_future(client_session.post(
                        self._get_issue_url(),
                        data=data)))
            if no_matching_line_number:
                no_matching_line_messages = []
                for location, problems_for_line in no_matching_line_number:
                    path = location[0]
                    line_number = location[1]
                    no_matching_line_messages.append(
                        '{0}:{1}:'.format(path, line_number))
                    for problem in problems_for_line:
                        no_matching_line_messages.append('\t{0}'.format(
                            problem.message))
                message = ('Linters found some problems with lines not '
                           'modified by this commit:\n```\n{0}\n```'.format(
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
            async for line in response.content:
                line = line.decode()
                file_match = FILE_START_REGEX.match(line)
                if file_match:
                    current_file = file_match.groups()[0].strip()
                    right_line_number = -1
                    position = -1
                    continue
                elif line.startswith(NEW_FILE_SECTION_START):
                    current_file = ''
                if not current_file:
                    continue

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

    async def get_existing_messages(
        self, client_session: aiohttp.ClientSession
    ) -> Set[ExistingGithubMessage]:
        url = self._get_pr_url()
        return await self._fetch_messages_from_url(client_session, url)

    @staticmethod
    async def _fetch_messages_from_url(
            client_session, url
    ) -> Set[ExistingGithubMessage]:
        existing_messages = set()  # type: Set[ExistingGithubMessage]
        async with client_session.get(url) as response:
            response = response  # type: aiohttp.ClientResponse
            comments = json.loads(await response.text())
            for comment in comments:
                existing_messages.add(
                    ExistingGithubMessage(path=comment['path'],
                                          position=comment['position'],
                                          body=comment['body']))

            next_url = GithubReporter._find_next_url(response)

        if next_url:
            existing_messages = existing_messages.union(
                await GithubReporter._fetch_messages_from_url(
                    client_session, next_url))

        return existing_messages

    @staticmethod
    def _find_next_url(response: aiohttp.ClientResponse) -> str:
        if 'link' in response.headers:
            links = response.headers['link'].split(',')
            for link in links:
                match = LINK_REGEX.match(link)
                if match and match.group('rel') == 'next':
                    return match.group('url')


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
                              args.commit)
    else:
        raise Exception("{} doesn't appear to be a valid github pr url".format(
            args.pr_url
        ))
