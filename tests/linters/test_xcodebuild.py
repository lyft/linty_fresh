import unittest
import os
from linty_fresh.linters import xcodebuild
from linty_fresh.problem import Problem


class XcodebuildTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), xcodebuild.parse(''))

    def test_parse_errors(self):
        test_string = [
            "<unknown>:0: error: no such file or directory: 'foo.swift'",
            "<unknown>:0: ERROR: no such file or directory: 'case.swift'",
            "{}/Classes/foo/bar baz/qux.swift:201:21: "
            "error: use of unresolved identifier 'FooBar'"
            .format(os.path.curdir),
            "{}/Classes/foo/bar/Protocols/SomeProtocol.swift:7:10: "
            "note: did you mean 'SomeOtherProtocol'?"
            .format(os.path.curdir),
            "{}/Resources/Storyboards & XIBs/Foo.storyboard:kB7-Bl-wC0: "
            "warning: Unsupported configuration of constraint attributes. "
            "This may produce unexpected results at runtime before Xcode 5.1"
            .format(os.path.curdir),
            "UIKit.UIScrollViewDelegate:23:41: "
            "note: requirement 'viewForZooming(in:)' declared here"
        ]

        result = xcodebuild.parse('\n'.join(test_string))
        self.assertEqual(4, len(result))

        self.assertIn(
            Problem('<unknown>',
                    0,
                    "no such file or directory: 'foo.swift'"),
            result)

        self.assertIn(
            Problem('<unknown>',
                    0,
                    "no such file or directory: 'case.swift'"),
            result)

        self.assertIn(
            Problem('Classes/foo/bar baz/'
                    'qux.swift',
                    201,
                    "use of unresolved identifier 'FooBar'"),
            result)

        self.assertIn(
            Problem('Resources/Storyboards & XIBs/'
                    'Foo.storyboard',
                    0,
                    'kB7-Bl-wC0: Unsupported configuration of '
                    'constraint attributes. This may produce unexpected '
                    'results at runtime before Xcode 5.1'),
            result)

    def test_should_not_parse(self):
        test_string = [
            "Details:  log recorder was sent "
            "-stopRecordingWithInfo:completionBlock: after it had already "
            "been asked to stop recording.",
        ]

        result = xcodebuild.parse('\n'.join(test_string))
        self.assertEqual(0, len(result))
