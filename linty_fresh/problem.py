import itertools
from collections import OrderedDict


class Problem(object):
    def __init__(self, file_path: str, line: str, message: str) -> None:
        self.path = file_path
        self.line = int(line)
        self.message = message

    def __hash__(self):
        return hash((self.path, self.line, self.message))

    def __eq__(self, other):
        return ((self.path, self.line, self.message) ==
                (other.path, other.line, other.message))

    def to_json(self):
        return OrderedDict({
            'path': self.path,
            'line': self.line,
            'message': self.message
        })

    @staticmethod
    def from_json(json_object) -> 'Problem':
        return Problem(json_object['path'],
                       json_object['line'],
                       json_object['message'])

    @staticmethod
    def group_by_path_and_line(problems):
        def key_func(problem):
            return problem.path, problem.line

        sorted_problems = sorted(problems, key=key_func)
        return [(location, list(problems)) for (location, problems) in
                itertools.groupby(sorted_problems, key_func)]


class TestProblem(object):
    def __init__(self, test_group: str, test_name: str, message: str,
                 stack_trace: str) -> None:
        self.test_group = test_group.strip()
        self.test_name = test_name.strip()
        self.message = message.strip()
        self.stack_trace = stack_trace.strip()

    def __hash__(self):
        return hash((self.test_group, self.test_name, self.message,
                    self.stack_trace))

    def __eq__(self, other):
        return ((self.test_group,
                 self.test_name,
                 self.message,
                 self.stack_trace) ==
                (other.test_group,
                 other.test_name,
                 other.message,
                 other.stack_trace))

    def to_json(self):
        return OrderedDict({
            'test_group': self.test_group,
            'test_name': self.test_name,
            'message': self.message,
            'stack_trace': self.stack_trace
        })

    @staticmethod
    def from_json(json_object) -> 'TestProblem':
        return TestProblem(json_object['test_group'],
                           json_object['test_name'],
                           json_object['message'],
                           json_object['stack_trace']
                           )

    @staticmethod
    def group_by_group(problems):
        def key_func(problem):
            return problem.test_group

        sorted_problems = sorted(problems, key=key_func)
        return [(location, list(problems)) for (location, problems) in
                itertools.groupby(sorted_problems, key_func)]
