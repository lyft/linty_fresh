import unittest

from linty_fresh.linters import checkstyle
from linty_fresh.problem import Problem


class CheckstyleTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), checkstyle.parse(''))

    def test_parse_errors(self):
        test_string = """\
<?xml version='1.0' encoding='UTF-8'?>
    <checkstyle version='4.3'>
        <file name='scripts/run&#95;tests.sh' >
            <error line='31'
             column='26' severity='info'
             message='Double quote to prevent globbing and word splitting.'
             source='ShellCheck.SC2086' />
        </file>
        <file name='scripts/setup.sh' >
            <error
             line='3'
             column='1'
             severity='warning'
             message='FOO appears unused. Verify it or export it.'
             source='ShellCheck.SC2034' />
        </file>
</checkstyle>
"""

        result = checkstyle.parse(test_string)
        self.assertEqual(2, len(result))
        self.assertIn(Problem('scripts/run_tests.sh',
                              31,
                              'ShellCheck.SC2086: Double quote to prevent '
                              'globbing and word splitting.'),
                      result)

        self.assertIn(Problem('scripts/setup.sh',
                              3,
                              'ShellCheck.SC2034: FOO appears unused. '
                              'Verify it or export it.'),
                      result)
