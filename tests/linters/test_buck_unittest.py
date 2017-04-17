import unittest

from linty_fresh.linters import buck_unittest
from linty_fresh.problem import TestProblem

TEST_STRING = """

<tests>
    <test name="com.lyft.android.driver.DaggerTest" status="PASS" time="1055">
        <testresult name="createsObjectGraph" time="1055">
            <message/>
            <stacktrace/>
        </testresult>
    </test>
    <test name="com.lyft.android.locationingest.DriverUpdateUserLocationRequestFactoryTest" status="PASS" time="273">
        <testresult name="includesLocationBatchAndAppRevision" time="273">
            <message/>
            <stacktrace/>
        </testresult>
    </test>
    <test name="com.lyft.ampdroid.BaseTestClass" status="PASS" time="0"/>
    <test name="com.lyft.ampdroid.UtilTests" status="PASS" time="2">
        <testresult name="testOtaDeviceAddress" time="1">
            <message/>
            <stacktrace/>
        </testresult>
        <testresult name="testsCompareEmblemVersions" time="1">
            <message/>
            <stacktrace/>
        </testresult>
    </test>
<test name="TEST_GROUP_NAME_1" status="FAIL" time="53">
    <testresult name="doesNotIncludeMarkersAndRideTypeWhenRideInProgress" time="37">
        <message/>
        <stacktrace/>
    </testresult>
    <testresult name="includesMarkersAndRideTypeWhenRideNotInProgress" time="10">
        <message/>
        <stacktrace/>
    </testresult>
    <testresult name="TEST_TR_NAME_1" time="6">
        <message>TEST_MESSAGE_TEXT_1</message>
        <stacktrace>TEST_STACK_TRACE_TEXT_1
    </stacktrace>
</testresult>
</test>
<test name="TEST_GROUP_NAME_2" status="FAIL" time="53">
    <testresult name="doesNotIncludeMarkersAndRideTypeWhenRideInProgress" time="37">
        <message/>
        <stacktrace/>
    </testresult>
    <testresult name="includesMarkersAndRideTypeWhenRideNotInProgress" time="10">
        <message/>
        <stacktrace/>
    </testresult>
    <testresult name="TEST_TR_NAME_2" time="6">
        <message>TEST_MESSAGE_TEXT_2</message>
        <stacktrace>TEST_STACK_TRACE_TEXT_2
    </stacktrace>
</testresult>
</test>

</tests>

"""


class BuckUnittestTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), buck_unittest.parse(''))

    def test_parse_errors(self):
        result = buck_unittest.parse(TEST_STRING)
        self.assertEqual(2, len(result))

        self.assertIn(TestProblem("TEST_GROUP_NAME_1",
                                  "TEST_TR_NAME_1",
                                  "TEST_MESSAGE_TEXT_1",
                                  "TEST_STRACK_TRACE_TEXT_1"
                                  ), result)

        self.assertIn(TestProblem("TEST_GROUP_NAME_2",
                                  "TEST_TR_NAME_2",
                                  "TEST_MESSAGE_TEXT_2",
                                  "TEST_STRACK_TRACE_TEXT_2"
                                  ), result)
