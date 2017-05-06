import unittest
from linty_fresh.linters import passthrough
from linty_fresh.problem import Problem


class PassthroughTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), passthrough.parse(''))

    def test_parse_errors(self):
        test_string = [
            '        Something happened!',
            "More stuff 'happened'\n\n",
        ]

        result = passthrough.parse('\n'.join(test_string))
        self.assertEqual(1, len(result))

        self.assertIn(Problem('', 0,
                              'Something happened!\n'
                              "More stuff 'happened'"), result)
