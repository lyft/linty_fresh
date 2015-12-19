from xml.etree import ElementTree

from linty_fresh.problem import Problem

from typing import Set


def parse(contents: str) -> Set[Problem]:
    result = set()  # type: Set[Problem]
    try:
        root = ElementTree.fromstring(contents)
    except ElementTree.ParseError:
        return result
    for file in root.findall('file'):
        file_name = file.get('name')
        for error in file.findall('error'):
            result.add(Problem(
                file_name,
                error.get('line'),
                '{}: {}'.format(
                    error.get('source'),
                    error.get('message'))))
    return result
