import unittest

from linty_fresh.linters import android
from linty_fresh.problem import Problem

test_string = """\
<?xml version="1.0" encoding="UTF-8"?>
<issues format="4" by="lint 25.1.6">

    <issue
        id="ScrollViewSize"
        severity="Error"
        message="This LinearLayout should use `android:layout_height=&quot;wrap_content&quot;`"
        category="Correctness"
        priority="7"
        summary="ScrollView size validation"
        explanation="ScrollView children must set their `layout_width` or `layout_height` attributes to `wrap_content` rather than `fill_parent` or `match_parent` in the scrolling dimension"
        errorLine1="            android:layout_height=&quot;match_parent&quot;"
        errorLine2="            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        quickfix="studio,adt">
        <location
            file="scripts/run&#95;tests.sh"
            line="15"
            column="13"/>
    </issue>

    <issue
        id="DefaultLocale"
        severity="Warning"
        message="Implicitly using the default locale is a common source of bugs: Use `toLowerCase(Locale)` instead"
        category="Correctness"
        priority="6"
        summary="Implied default locale in case conversion"
        explanation="Calling `String#toLowerCase()` or `#toUpperCase()` *without specifying an explicit locale* is a common source of bugs. The reason for that is that those methods will use the current locale on the user&apos;s device, and even though the code appears to work correctly when you are developing the app, it will fail in some locales. For example, in the Turkish locale, the uppercase replacement for `i` is *not* `I`.

If you want the methods to just perform ASCII replacement, for example to convert an enum name, call `String#toUpperCase(Locale.US)` instead. If you really want to use the current locale, call `String#toUpperCase(Locale.getDefault())` instead."
        url="http://developer.android.com/reference/java/util/Locale.html#default_locale"
        urls="http://developer.android.com/reference/java/util/Locale.html#default_locale"
        errorLine1="                final String filterPattern = constraint.toString().toLowerCase().trim();"
        errorLine2="                                                                   ~~~~~~~~~~~">
        <location
            file="scripts/setup.sh"
            line="238"
            column="68"/>
    </issue>

</issues>
"""


class AndroidLintTest(unittest.TestCase):
    def test_empty_parse(self):
        self.assertEqual(set(), android.parse('', fail_warnings=True))

    def test_parse_all(self):
        result = android.parse(test_string, fail_warnings=True)
        self.assertEqual(2, len(result))
        self.assertIn(Problem('scripts/run_tests.sh',
                                      15,
                                      'ScrollView size validation: This LinearLayout '
                                      'should use '
                                      '`android:layout_height="wrap_content"`'),
                      result)

        self.assertIn(Problem('scripts/setup.sh',
                              238,
                              'Implied default locale in case conversion: '
                              'Implicitly using the default locale is a '
                              'common source of bugs: Use '
                              '`toLowerCase(Locale)` instead'),
                      result)

    def test_parse_errors_only(self):
        result = android.parse(test_string, fail_warnings=False)
        self.assertEqual(1, len(result))
        self.assertIn(Problem('scripts/run_tests.sh',
                                      15,
                                      'ScrollView size validation: This LinearLayout '
                                      'should use '
                                      '`android:layout_height="wrap_content"`'),
                      result)
