import re

from linty_fresh.problem import Problem

from typing import Set


MYPY_LINE_REGEX = re.compile(r'(?P<path>[^:]*):(?P<line>\d*):\s*'
                             r'(?P<code>\w*)\s*:\s*(?P<message>.*)')


def parse(contents: str) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    for line in contents.splitlines():
        match = MYPY_LINE_REGEX.match(line)
        if match:
            groups = match.groupdict()
            if groups['code'] != 'note':
                result.add(Problem(groups['path'],
                                   groups['line'],
                                   '{}: {}'.format(groups['code'],
                                                   groups['message'])))
    return result
