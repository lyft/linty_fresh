import os
import re
from typing import Set

from linty_fresh.problem import Problem

XCODEBUILD_LINE_REGEX = re.compile(
    r'(?P<path>[^:]*):'
    r'((?P<line>\d*)|(?P<reference>[^:]*)):'
    r'(?:(?P<column>\d*):)?\s*(?P<level>(error|warn(ing)?|note|info)):'
    r'\s*(?P<message>.*)',
    re.IGNORECASE,
)


def parse(contents: str, **kwargs) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    for line in contents.splitlines():
        match = XCODEBUILD_LINE_REGEX.match(line)
        if match:
            groups = match.groupdict()
            line = groups['line'] or 0
            message = groups['message']
            reference = groups['reference']
            if reference:
                message = '{}: {}'.format(reference, message)

            result.add(Problem(os.path.relpath(groups['path']),
                               line, message))
    return result
