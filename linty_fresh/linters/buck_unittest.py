from typing import Set
from xml.etree import ElementTree

from linty_fresh.problem import TestProblem


def parse(contents: str, **kwargs) -> Set[TestProblem]:
    result = set()
    try:
        root = ElementTree.fromstring(contents)
    except ElementTree.ParseError:
        return result
    for test in root.findall('test'):
        if test.get('status') == 'FAIL':
            test_group = test.get('name')
            for tr in test.findall('testresult'):
                message = None
                stack_trace = None
                for m in tr.findall('message'):
                    if m.text:
                        message = m.text
                for st in tr.findall('stacktrace'):
                    if st.text:
                        stack_trace = st.text
                if stack_trace and message:
                    test_name = tr.get('name')
                    result.add(TestProblem(
                        test_group,
                        test_name,
                        message,
                        stack_trace
                    ))
    return result
