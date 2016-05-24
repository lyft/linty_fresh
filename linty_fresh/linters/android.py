from xml.etree import ElementTree

from linty_fresh.problem import Problem

from typing import Set


def parse(contents: str) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    try:
        root = ElementTree.fromstring(contents)
    except ElementTree.ParseError:
        return result
    for issue in root.findall('issue'):
        location = issue.getchildren()[0]
        result.add(Problem(
            location.get('file'),
            location.get('line'),
            '{}: {}'.format(
                issue.get('summary'),
                issue.get('message'))))
    return result
