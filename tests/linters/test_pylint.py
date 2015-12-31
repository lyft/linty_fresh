import unittest

from linty_fresh.linters import pylint
from linty_fresh.problem import Problem


class PyLintTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), pylint.parse(''))

    def test_parse_errors(self):
        test_string = '''
src/linters/pylint.py:10: [E302] expected 2 blank lines, found 1
tests/linters/pylint.py:42: [E302] expected 2 blank lines, found 1
::
'''
        result = pylint.parse(test_string)
        self.assertEqual(2, len(result))

        self.assertIn(Problem('src/linters/pylint.py',
                              10,
                              '[E302] expected 2 blank lines, found 1'),
                      result)

        self.assertIn(Problem('tests/linters/pylint.py',
                              42,
                              '[E302] expected 2 blank lines, found 1'),
                      result)
