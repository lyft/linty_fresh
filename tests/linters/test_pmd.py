import unittest
import os
from linty_fresh.linters import pmd
from linty_fresh.problem import Problem


class PmdTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), pmd.parse(''))

    def test_parse_errors(self):
        test_string = """\
<?xml version="1.0" encoding="UTF-8"?>
<pmd version="5.5.0" timestamp="2016-07-06T11:29:03.360">
    <file name="{0}/DriverRideDrivingToWaypointController.java">
        <violation beginline="287" endline="287" begincolumn="58" endcolumn="61" rule="UnusedFormalParameter" ruleset="Unused Code" package="me.lyft.android.ui.driver.ridescreens" class="DriverRideDrivingToWaypointController" method="displayWaypointAddress" variable="ride" externalInfoUrl="https://pmd.github.io/pmd-5.5.0/pmd-java/rules/java/unusedcode.html#UnusedFormalParameter" priority="3">
        Avoid unused method parameters such as 'ride'.
    </violation>
    </file>
    <file name="{0}/AddCouponView.java">
        <violation beginline="24" endline="24" begincolumn="1" endcolumn="38" rule="UnusedImports" ruleset="Import Statements" package="me.lyft.android.ui.payment" externalInfoUrl="https://pmd.github.io/pmd-5.5.0/pmd-java/rules/java/imports.html#UnusedImports" priority="4">
        Avoid unused imports such as 'me.lyft.android.common.Strings'
        </violation>
    </file>
</pmd>
        """.format(os.path.curdir)

        result = pmd.parse(test_string)
        self.assertEqual(2, len(result))
        self.assertIn(Problem('./DriverRideDrivingToWaypointController.java',
                              287,
                              'UnusedFormalParameter: Avoid unused method'
                              " parameters such as 'ride'."),
                      result)

        self.assertIn(Problem('./AddCouponView.java',
                              24,
                              'UnusedImports: Avoid unused imports such as'
                              " 'me.lyft.android.common.Strings'"),
                      result)
