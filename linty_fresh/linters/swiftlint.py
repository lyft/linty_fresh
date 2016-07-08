import os
import re
from typing import Set

from linty_fresh.problem import Problem


SWIFTLINT_LINE_REGEX = re.compile(r'(?P<path>[^:]*):(?P<line>\d*):'
                                  r'(?:(?P<column>\d*):)?\s*(?P<level>\w*):'
                                  r'\s*(?P<message>.*)')


def parse(contents: str) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    for line in contents.splitlines():
        match = SWIFTLINT_LINE_REGEX.match(line)
        if match:
            groups = match.groupdict()
            result.add(Problem(os.path.relpath(groups['path']),
                               groups['line'],
                               groups['message']))
    return result
