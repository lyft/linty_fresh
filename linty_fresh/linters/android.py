from typing import Set
from xml.etree import ElementTree

from linty_fresh.problem import Problem


def parse(contents: str, pass_warnings: bool, **kwargs) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    try:
        root = ElementTree.fromstring(contents)
    except ElementTree.ParseError:
        return result
    for issue in root.findall('issue'):
        location = issue.getchildren()[0]
        if issue.get('severity') == 'Warning' and pass_warnings:
            pass
        else:
            result.add(Problem(
                location.get('file'),
                location.get('line', '0'),
                '{}: {}'.format(
                    issue.get('summary'),
                    issue.get('message'))))
    return result
