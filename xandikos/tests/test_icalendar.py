# Xandikos
# Copyright (C) 2016-2017 Jelmer Vernooĳ <jelmer@jelmer.uk>, et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 3
# of the License or (at your option) any later version of
# the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

"""Tests for xandikos.icalendar."""

import unittest

from xandikos import (
    collation as _mod_collation,
    )
from xandikos.icalendar import (
    CalendarFilter,
    ComponentFilter,
    ICalendarFile,
    TextMatcher,
    validate_calendar,
)
from xandikos.store import InvalidFileContents

EXAMPLE_VCALENDAR1 = b"""\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//bitfire web engineering//DAVdroid 0.8.0 (ical4j 1.0.x)//EN
BEGIN:VTODO
CREATED:20150314T223512Z
DTSTAMP:20150527T221952Z
LAST-MODIFIED:20150314T223512Z
STATUS:NEEDS-ACTION
SUMMARY:do something
UID:bdc22720-b9e1-42c9-89c2-a85405d8fbff
END:VTODO
END:VCALENDAR
"""

EXAMPLE_VCALENDAR_NO_UID = b"""\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//bitfire web engineering//DAVdroid 0.8.0 (ical4j 1.0.x)//EN
BEGIN:VTODO
CREATED:20120314T223512Z
DTSTAMP:20130527T221952Z
LAST-MODIFIED:20150314T223512Z
STATUS:NEEDS-ACTION
SUMMARY:do something without uid
END:VTODO
END:VCALENDAR
"""

EXAMPLE_VCALENDAR_INVALID_CHAR = b"""\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//bitfire web engineering//DAVdroid 0.8.0 (ical4j 1.0.x)//EN
BEGIN:VTODO
CREATED:20150314T223512Z
DTSTAMP:20150527T221952Z
LAST-MODIFIED:20150314T223512Z
STATUS:NEEDS-ACTION
SUMMARY:do something
ID:bdc22720-b9e1-42c9-89c2-a85405d8fbff
END:VTODO
END:VCALENDAR
"""


class ExtractCalendarUIDTests(unittest.TestCase):

    def test_extract_str(self):
        fi = ICalendarFile([EXAMPLE_VCALENDAR1], 'text/calendar')
        self.assertEqual(
            'bdc22720-b9e1-42c9-89c2-a85405d8fbff',
            fi.get_uid())
        fi.validate()

    def test_extract_no_uid(self):
        fi = ICalendarFile([EXAMPLE_VCALENDAR_NO_UID], 'text/calendar')
        fi.validate()
        self.assertEqual(["Missing required field UID"],
                         list(validate_calendar(fi.calendar, strict=True)))
        self.assertEqual([],
                         list(validate_calendar(fi.calendar, strict=False)))
        self.assertRaises(KeyError, fi.get_uid)

    def test_invalid_character(self):
        fi = ICalendarFile([EXAMPLE_VCALENDAR_INVALID_CHAR], 'text/calendar')
        self.assertRaises(InvalidFileContents, fi.validate)
        self.assertEqual(["Invalid character b'\\\\x0c' in field SUMMARY"],
                         list(validate_calendar(fi.calendar, strict=False)))


class CalendarFilterTests(unittest.TestCase):

    def setUp(self):
        self.cal = ICalendarFile([EXAMPLE_VCALENDAR1], 'text/calendar')

    def test_simple_comp_filter(self):
        filter = CalendarFilter(
            None, ComponentFilter('VCALENDAR', [ComponentFilter('VEVENT')]))
        self.assertFalse(filter.check('file', self.cal))
        filter = CalendarFilter(
            None, ComponentFilter('VCALENDAR', [ComponentFilter('VTODO')]))
        self.assertTrue(filter.check('file', self.cal))


class TextMatchTest(unittest.TestCase):

    def test_default_collation(self):
        tm = TextMatcher(b"foobar")
        self.assertTrue(tm.match(b"FOOBAR"))
        self.assertTrue(tm.match(b"foobar"))
        self.assertFalse(tm.match(b"fobar"))

    def test_casecmp_collation(self):
        tm = TextMatcher(b'foobar', collation='i;ascii-casemap')
        self.assertTrue(tm.match(b"FOOBAR"))
        self.assertTrue(tm.match(b"foobar"))
        self.assertFalse(tm.match(b"fobar"))

    def test_cmp_collation(self):
        tm = TextMatcher(b'foobar', 'i;octet')
        self.assertFalse(tm.match(b"FOOBAR"))
        self.assertTrue(tm.match(b"foobar"))
        self.assertFalse(tm.match(b"fobar"))

    def test_unknown_collation(self):
        tm = TextMatcher(b'foobar', collation='i;blah')
        self.assertRaises(_mod_collation.UnknownCollation,
                          tm.match, b"FOOBAR")
