import sys
import unittest

from contextlib import contextmanager
from io import StringIO


from linty_fresh.main import manage_results

class ManageResultsTest(unittest.TestCase):

    @contextmanager
    def capture(self):
        old_out, old_err = sys.stdout, sys.stderr
        try:
            stdout, stderr = StringIO(), StringIO()
            sys.stdout, sys.stderr = stdout, stderr
            yield stdout, stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def test_no_problems(self):
        with self.capture() as output:
            result = manage_results([])

        self.assertEqual(result, 0)
        self.assertEqual(output[0].getvalue(), 'No problem found\n')
        self.assertEqual(output[1].getvalue(), '')

    def test_existing_problems(self):
        with self.capture() as output:
            result = manage_results([(
                'GithubReporter',
                5,
                3,
                None,
                2
            )])

        self.assertEqual(result, 1)
        self.assertEqual(output[0].getvalue(), '')
        self.assertEqual(output[1].getvalue(), 'GithubReporter: 5 problem(s) to send '
                                               '(3 new, 2 could not be sent)\n')

    def test_overflow(self):
        with self.capture() as output:
            result = manage_results([(
                'GithubReporter',
                12,
                12,
                10,
                1
            )])

        self.assertEqual(result, 1)
        self.assertEqual(output[0].getvalue(), '')
        self.assertEqual(output[1].getvalue(), 'GithubReporter: 12 problem(s) to send '
                                               '(12 new, max of 10 raised, '
                                               '1 could not be sent)\n')
