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
