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

CLASS_NAME = re.compile(r'[A-Z]\w+\.[A-Z]\w+$')


def parse(contents: str, **kwargs) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    for line in contents.splitlines():
        match = XCODEBUILD_LINE_REGEX.match(line)
        if match:
            groups = match.groupdict()
            path = groups['path']
            line = groups['line'] or 0
            level = groups['level']
            message = groups['message']
            reference = groups['reference']
            if reference:
                message = '{}: {}'.format(reference, message)

            if CLASS_NAME.match(path) and level == 'note':
                # Ignore non-file references (ex UIKit.UIScrollViewDelegate)
                continue

            result.add(Problem(os.path.relpath(path), line, message))
    return result
