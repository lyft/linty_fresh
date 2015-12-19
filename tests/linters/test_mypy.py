import unittest

from linty_fresh.linters import mypy
from linty_fresh.problem import Problem


class PyLintTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), mypy.parse(''))

    def test_parse_errors(self):
        test_string = '''
src/linters/pylint.py: note: expected 2 blank lines, found 1
tests/linters/pylint.py:42: error: "module" has no attribute "foo"
tests/linters/pylint.py:33: error: "module" has no attribute "bar"
'''

        result = mypy.parse(test_string)
        self.assertEqual(2, len(result))
        self.assertIn(Problem('tests/linters/pylint.py',
                              42,
                              'error: "module" has no attribute "foo"'),
                      result)

        self.assertIn(Problem('tests/linters/pylint.py',
                              33,
                              'error: "module" has no attribute "bar"'),
                      result)
