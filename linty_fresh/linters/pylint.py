import re
from typing import Set

from linty_fresh.problem import Problem

PYLINT_LINE_REGEX = re.compile(r'(?P<path>[^:]+):(?P<line>\d+):\s*'
                               r'(?:(?P<column>\d*):)?\s*'
                               r'(?P<message>.*)')


def parse(contents: str, **kwargs) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    for line in contents.splitlines():
        match = PYLINT_LINE_REGEX.match(line)
        if match:
            groups = match.groupdict()
            result.add(Problem(groups['path'],
                               groups['line'],
                               groups['message']))
    return result
