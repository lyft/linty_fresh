import re

from linty_fresh.problem import Problem

from typing import Set

ESLINT_LINE_REGEX = re.compile(r'(?P<path>[^:]*): line (?P<line>\d*), '
                               r'col (?P<column>\d*), (?P<message>.*)')


def parse(contents: str) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    for line in contents.splitlines():
        match = ESLINT_LINE_REGEX.match(line)
        if match:
            groups = match.groupdict()
            result.add(Problem(groups['path'],
                               groups['line'],
                               groups['message']))
    return result
