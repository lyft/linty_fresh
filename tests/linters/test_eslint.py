import unittest

from linty_fresh.linters import eslint
from linty_fresh.problem import Problem

class PyLintTest(unittest.TestCase):
  def test_empty_parse(self):
    self.assertEqual(set(), eslint.parse(''))

  def test_parse_errors(self):
    test_string = '''
fullOfProblems.js: line 1, col 10, Error - "addOne" is defined but never used (no-unused-vars)
fullOfProblems.js: line 3, col 20, Warning - Missing semicolon. (semi)
'''

    result = eslint.parse(test_string)
    self.assertEqual(2, len(result))
    self.assertIn(Problem('fullOfProblems.js',
                          1,
                          'Error - "addOne" is defined but never used (no-unused-vars)'),
                          result)

    self.assertIn(Problem('fullOfProblems.js',
                          3,
                          'Warning - Missing semicolon. (semi)'),
                          result)
