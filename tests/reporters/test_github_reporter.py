import asyncio
import json
import textwrap
import unittest

from mock import MagicMock, call, patch

from linty_fresh.reporters import github_reporter
from linty_fresh.reporters.github_reporter import GithubReporter
from linty_fresh.problem import Problem
from ..utils.fake_client_session import FakeClientResponse, FakeClientSession


class GithubReporterTest(unittest.TestCase):
    github_patch = textwrap.dedent('''\
            diff --git a/some_dir/some_file b/some_dir/some_file
            index abc123..bca321 100644
            --- a/some_dir/some_file
            +++ b/some_dir/some_file
            @@ -38,3 +38,4 @@ 37 - 0
             38 - 1
             39 - 2
             40 - 3
            -DELETED - 4
            -DELETED - 5
            -DELETED - 6
            +41 - 7
            +42 - 8
            @@ -55,3 +58,4 @@ 57 - 9
             58 - 10
            -DELETED - 11
            +59 - 12
            diff --git a/some_dir/some_file b/some_dir/some_file
            index abc123..bca321 100644
            --- a/another_file
            +++ b/another_file
            @@ -0,0 +1,4 @@
            + 1 - 1
            + 2 - 2
            + 3 - 3
            + 4 - 4
            + 5 - 5
            + 6 - 6
            + 7 - 7
            + 8 - 8
            + 9 - 9
            + 10 - 10
            + 11 - 11
            + 12 - 12
            ''')

    @patch('linty_fresh.reporters.github_reporter.aiohttp.ClientSession')
    @patch('os.getenv')
    def test_comment_on_pr(self,
                           mock_getenv,
                           mock_client_session):
        mock_args, fake_client_session = self.create_mock_pr(
            mock_getenv,
            mock_client_session)

        reporter = github_reporter.create_reporter(mock_args)
        async_report = reporter.report('unit-test-linter', [
            Problem('some_dir/some_file', 40, 'this made me sad'),
            Problem('some_dir/some_file', 40, 'really sad'),
            Problem('another_file', 2, 'This is OK'),
            Problem('another_file', 2, 'This is OK'),
            Problem('another_file', 3, 'I am a duplicate!'),
            Problem('another_file', 52, "#close_enough!!!"),
            Problem('missing_file', 42, "Missing file comment!!!"),
        ])

        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_report)

        diff_request = call.get(
            'https://api.github.com/repos/foo/bar/pulls/1234',
            headers={
                'Accept': 'application/vnd.github.diff',
                'Authorization': 'token MY_TOKEN'
            })
        existing_comments_request = call.get(
            'https://api.github.com/repos/foo/bar/pulls/1234/comments',
            headers={
                'Authorization': 'token MY_TOKEN'
            })
        first_comment = call.post(
            'https://api.github.com/repos/foo/bar/pulls/1234/comments',
            headers={
                'Authorization': 'token MY_TOKEN'
            },
            data=json.dumps({
                'commit_id': 'abc123',
                'path': 'another_file',
                'body': textwrap.dedent('''\
                    unit-test-linter says:

                    ```
                    This is OK
                    ```'''),
                'position': 2
            }, sort_keys=True)
        )
        second_comment = call.post(
            'https://api.github.com/repos/foo/bar/pulls/1234/comments',
            headers={
                'Authorization': 'token MY_TOKEN'
            },
            data=json.dumps({
                'commit_id': 'abc123',
                'path': 'some_dir/some_file',
                'body': textwrap.dedent('''\
                    unit-test-linter says:

                    ```
                    this made me sad
                    really sad
                    ```'''),
                'position': 3
            }, sort_keys=True)
        )
        close_enough_comment = call.post(
            'https://api.github.com/repos/foo/bar/pulls/1234/comments',
            headers={
                'Authorization': 'token MY_TOKEN'
            },
            data=json.dumps({
                'commit_id': 'abc123',
                'path': 'another_file',
                'body': textwrap.dedent('''\
                    unit-test-linter says:

                    (From line 52)
                    ```
                    #close_enough!!!
                    ```'''),
                'position': 12
            }, sort_keys=True)
        )
        missing_file_call = call.post(
            'https://api.github.com/repos/foo/bar/issues/1234/comments',
            headers={
                'Authorization': 'token MY_TOKEN'
            },
            data=json.dumps({
                'body': textwrap.dedent('''\
                    unit-test-linter found some problems with lines not modified by this commit:
                    ```
                    missing_file:42:
                    \tMissing file comment!!!
                    ```'''),
            }, sort_keys=True)
        )

        self.assertEqual(6, len(fake_client_session.calls))
        self.assertIn(diff_request, fake_client_session.calls)
        self.assertIn(existing_comments_request, fake_client_session.calls)
        self.assertIn(first_comment, fake_client_session.calls)
        self.assertIn(second_comment, fake_client_session.calls)
        self.assertIn(close_enough_comment, fake_client_session.calls)
        self.assertIn(missing_file_call, fake_client_session.calls)

    @patch('linty_fresh.reporters.github_reporter.aiohttp.ClientSession')
    @patch('os.getenv')
    def test_comment_overflow(self,
                              mock_getenv,
                              mock_client_session):
        mock_args, fake_client_session = self.create_mock_pr(
            mock_getenv,
            mock_client_session)

        reporter = github_reporter.create_reporter(mock_args)

        problems = [Problem('another_file', x, 'Wat') for x in range(1, 13)]

        async_report = reporter.report('unit-test-linter', problems)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_report)

        overflow_message = textwrap.dedent('''\
            unit-test-linter says:

            Too many lint errors to report inline!  12 lines have a problem.
            Only reporting the first 10.''')
        overflow_call = call.post(
            'https://api.github.com/repos/foo/bar/issues/1234/comments',
            headers={
                'Authorization': 'token MY_TOKEN'
            },
            data=json.dumps({
                'body': overflow_message,
            }, sort_keys=True)
        )

        self.assertIn(overflow_call, fake_client_session.calls)
        self.assertEqual(3 + github_reporter.MAX_LINT_ERROR_REPORTS,
                         len(fake_client_session.calls))

    def create_mock_pr(self, mock_getenv, mock_client_session):
        fake_client_session = FakeClientSession(url_map={
            ('https://api.github.com/repos/foo/bar/pulls/1234', 'get'):
                FakeClientResponse(GithubReporterTest.github_patch),
            ('https://api.github.com/repos/foo/bar/pulls/1234/comments',
             'get'): FakeClientResponse(json.dumps([{
                 'path': 'another_file',
                 'position': 3,
                 'body': textwrap.dedent('''\
                     unit-test-linter says:

                     ```
                     I am a duplicate!
                     ```''')}], sort_keys=True)),
            ('https://api.github.com/repos/foo/bar/pulls/1234/comments',
             'post'): FakeClientResponse(''),
            ('https://api.github.com/repos/foo/bar/issues/1234/comments',
             'post'): FakeClientResponse('')
        })

        def session_init_side_effect(headers=None, *args, **kwargs):
            fake_client_session.headers = headers
            return fake_client_session

        mock_args = MagicMock()
        mock_args.pr_url = 'https://github.com/foo/bar/pull/1234'
        mock_args.commit = 'abc123'
        mock_getenv.return_value = 'MY_TOKEN'
        mock_client_session.side_effect = session_init_side_effect

        return mock_args, fake_client_session

    def test_create_line_map(self):
        reporter = GithubReporter('TOKEN', 'foo', 'bar', 12, 'abc123')
        client_session = FakeClientSession(url_map={
            ('https://api.github.com/repos/foo/bar/pulls/12', 'get'):
                FakeClientResponse(GithubReporterTest.github_patch)
        })

        loop = asyncio.get_event_loop()
        line_map = loop.run_until_complete(
            reporter.create_line_to_position_map(client_session))

        self.assertEqual(2, len(line_map))
        self.assertIn('some_dir/some_file', line_map)
        self.assertIn('another_file', line_map)
        self.assertEqual(3, line_map['some_dir/some_file'][40])
        self.assertEqual(7, line_map['some_dir/some_file'][41])
        self.assertEqual(None, line_map['some_dir/some_file'].get(50, None))
        self.assertEqual(12, line_map['some_dir/some_file'][59])

    def test_messages_paging(self):
        reporter = GithubReporter('TOKEN', 'foo', 'bar', 12, 'abc123')
        client_session = FakeClientSession(url_map={
            ('https://api.github.com/repos/foo/bar/pulls/12/comments', 'get'):
                FakeClientResponse(json.dumps([{
                    'path': 'file1',
                    'position': 2,
                    'body': 'hello'
                }], sort_keys=True),
                headers={
                    'link': '<https://api.github.com/repos/foo/bar/'
                            'pulls/12/comments?page=1>; rel="next"'
                }),
            ('https://api.github.com/repos/foo/bar/pulls/12/comments?page=1',
             'get'):
                FakeClientResponse(json.dumps([{
                    'path': 'file2',
                    'position': 3,
                    'body': 'world'
                }], sort_keys=True))
        })

        loop = asyncio.get_event_loop()
        existing_messages = loop.run_until_complete(
            reporter.get_existing_messages(client_session))

        self.assertEqual(2, len(existing_messages))
        self.assertIn(('file1', 2, 'hello'), existing_messages)
        self.assertIn(('file2', 3, 'world'), existing_messages)
