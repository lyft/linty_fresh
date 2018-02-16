import argparse
import asyncio
import sys
from typing import Any, Dict  # noqa

from linty_fresh.linters import (android, buck_unittest, checkstyle, mypy,
                                 passthrough, pmd, pylint, swiftlint,
                                 xcodebuild)
from linty_fresh.reporters import github_reporter
from linty_fresh.storage.git_storage_engine import GitNotesStorageEngine

REPORTERS = {
    'github': github_reporter,
}  # type: Dict[str, Any]

LINTERS = {
    'android': android,
    'checkstyle': checkstyle,
    'mypy': mypy,
    'passthrough': passthrough,
    'pmd': pmd,
    'pylint': pylint,
    'swiftlint': swiftlint,
    'xcodebuild': xcodebuild,
    'androidunittest': buck_unittest
}  # type: Dict[str, Any]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--reporter', type=str, nargs='+', default=['github'],
                        help='The reporter to use when reporting errors.')
    parser.add_argument('--linter', type=str, required=True,
                        help='The type of lint file to parse.')
    parser.add_argument('--linter_name', type=str, default=None,
                        help='Override linter name for PR reporting')
    parser.add_argument('--store_problems', default=False, action='store_true',
                        help='Whether or not to store lint errors as git '
                             'notes and filter out problems')
    parser.add_argument('files', type=str, nargs='+',
                        help='The lint file being parsed.')
    parser.add_argument('--pass-warnings', default=False, action='store_true',
                        help='(ANDROID ONLY) Pass Android linter on warnings.')
    parser.add_argument('--delete_previous_comments', default=False,
                        action='store_true',
                        help='Delete stale linter comments.')

    for name, reporter in REPORTERS.items():
        reporter.register_arguments(parser)
    return parser


async def run_loop(args):
    args = create_parser().parse_args()
    reporters = []
    for reporter in args.reporter:
        if reporter not in REPORTERS:
            raise Exception('Reporter {} is invalid, options are {}'.format(
                reporter, ','.join(list(REPORTERS.keys()))
            ))
        reporters.append(REPORTERS[reporter].create_reporter(args))

    problems = set()
    if args.linter not in LINTERS:
        raise Exception('Linter {} is invalid, options are {}'.format(
            args.linter, ','.join(list(LINTERS.keys()))
        ))
    linter = LINTERS[args.linter]
    for lint_file_path in args.files:
        with open(lint_file_path, 'r') as lint_file:
            problems.update(linter.parse(
                lint_file.read(), **vars(args)))
    storage_engine = GitNotesStorageEngine('origin')

    awaitable_array = []

    if args.store_problems:
        awaitable_array.append(storage_engine.store_problems(problems))
        existing_problems = await storage_engine.get_existing_problems()
        problems = problems.difference(existing_problems)

    linter_name = args.linter_name or linter
    awaitable_array.extend([reporter.report(linter_name, problems) for
                            reporter in
                            reporters])
    try:
        await asyncio.gather(*awaitable_array)
    except github_reporter.HadLintErrorsException:
        sys.exit(1)


def main():
    args = create_parser().parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_loop(args))
    loop.close()


if __name__ == '__main__':
    main()
