
from typing import Set
from xml.etree import ElementTree

from linty_fresh.problem import Problem


def parse(contents: str) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    try:
        root = ElementTree.fromstring(contents)
    except ElementTree.ParseError:
        return result
    for file in root.findall('file'):
        file_name = file.get('name')
        for violation in file.findall('violation'):
            result.add(Problem(
                file_name,
                violation.get('beginline'),
                '{}: {}'.format(
                    violation.get('rule'),
                    violation.text.strip())))
    return result
