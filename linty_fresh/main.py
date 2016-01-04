import argparse
import asyncio
import sys

from linty_fresh.linters import checkstyle, mypy, pylint, swiftlint
from linty_fresh.reporters import github_reporter

from typing import Any, Dict  # noqa

from linty_fresh.storage.git_storage_engine import GitNotesStorageEngine

REPORTERS = {
    'github': github_reporter,
}  # type: Dict[str, Any]

LINTERS = {
    'mypy': mypy,
    'pylint': pylint,
    'swiftlint': swiftlint,
    'checkstyle': checkstyle,
}  # type: Dict[str, Any]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--reporter', type=str, nargs='+', default=['github'],
                        help='The reporter to use when reporting errors.')
    parser.add_argument('--linter', type=str, required=True,
                        help='The type of lint file to parse.')
    parser.add_argument('--store_problems', default=False, action='store_true',
                        help='Whether or not to store lint errors as git '
                             'notes and filter out problems')
    parser.add_argument('files', type=str, nargs='+',
                        help='The lint file being parsed.')
    for name, reporter in REPORTERS.items():
        reporter.register_arguments(parser)
    return parser


def manage_results(results):

    results = [result for result in results if result]

    for result in results:
        report_string = '%s: %d problem(s) to send ' \
                        '(%d new' % tuple(result[:3])
        if result[3]:
            report_string += ', max of %d raised' % result[3]
        if result[4]:
            report_string += ', %d could not be sent' % result[4]
        report_string += ')'

        print(report_string, file=sys.stderr)

        return 1

    else:
        print('No problem found')
        return 0


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
            problems.update(linter.parse(lint_file.read()))

    if len(problems):
        awaitable_array = []

        if args.store_problems:
            storage_engine = GitNotesStorageEngine('origin')
            awaitable_array.append(storage_engine.store_problems(problems))
            existing_problems = await storage_engine.get_existing_problems()
            problems = problems.difference(existing_problems)

        awaitable_array.extend([reporter.report(problems) for
                                reporter in
                                reporters])
        results = await asyncio.gather(*awaitable_array)
    else:
        results = ()

    return manage_results(results)


def main():
    args = create_parser().parse_args()
    loop = asyncio.get_event_loop()
    exit_code = loop.run_until_complete(run_loop(args))
    loop.close()
    return exit_code


if __name__ == '__main__':
    exit(main())
