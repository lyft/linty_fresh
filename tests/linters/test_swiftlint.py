import unittest
import os
from linty_fresh.linters import swiftlint
from linty_fresh.problem import Problem


class SwiftlintTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), swiftlint.parse(''))

    def test_parse_errors(self):
        test_string = [
            '{}/Classes/Foo + Bar/Foo + Menu/Controllers/'
            'SomeController.swift:42: warning: '
            'Documentation Comment Violation: Needs documentation '
            'comment'.format(os.path.curdir),
            '{}/Classes/Foo + Bar/Foo + Menu/Controllers/'
            'AnotherController.swift:50:5: warning: '
            'Documentation Comment Violation: Needs documentation '
            'comment'.format(os.path.curdir)]
        result = swiftlint.parse('\n'.join(test_string))
        self.assertEqual(2, len(result))

        self.assertIn(
            Problem('Classes/Foo + Bar/Foo + Menu/Controllers/'
                    'SomeController.swift',
                    42,
                    'Documentation Comment Violation: '
                    'Needs documentation comment'),
            result)

        self.assertIn(
            Problem('Classes/Foo + Bar/Foo + Menu/Controllers/'
                    'AnotherController.swift',
                    50,
                    'Documentation Comment Violation: '
                    'Needs documentation comment'),
            result)
