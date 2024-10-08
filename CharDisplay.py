#!/usr/bin/env python3
#
# CharDisplay.py: Show tons of info about a character(s).
# 2018-04-21: Written by Steven J. DeRose
#
#pylint: disable=I1101
#
import sys
import argparse
import unicodedata
import re
import string
from enum import Enum
from typing import List

from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote
from urllib.request import urlopen
from html.entities import codepoint2name, name2codepoint
from html import unescape

import logging
lg = logging.getLogger("CharDisplay")

__metadata__ = {
    "title"        : "CharDisplay",
    "description"  : "Show tons of info about a character(s).",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 2.7.6, 3.6",
    "created"      : "2018-04-21",
    "modified"     : "2023-02-21",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

Display detailed information about a single Unicode character.

Can be used as a library, or from the command line to identify characters
by their code points, or the literal character:

    CharDisplay 65 0x2400 012 x

This accepts decimal, hex, and octal code point numbers, as well
as literal characters (all shown in the example above).
However, it does not support specifying characters by their HTML entity name,
Unicode full name, Unix jargon name, etc. (for which see my `ord`).

==Legend==

An example display, for U+FB00 when using this as a command, is:

    Unicode Name     LATIN SMALL LIGATURE FF
    Script           Latin
    Category         "Ll" (Letter, Lowercase)
    Block            Alphabetic Presentation Forms
    Plane            0: Basic Multilingual
    Literal          ",,xEF,,xAC,,x80"
    Bases            o001754000 d064256 0xfb00
    Unicode          U+fb00, utf8 \\xefac80 URI %EF%AC%80 (URI? False; FPI? False)
    Entities         &#xfb00;  &#64256;  None
    Unix jargon
    Numeric value
    Is Bidi          L
    Is Combining
    ea width         N
    IsMirror
    Decompose        <compat> 0066 0066
    Normalizations   NFC "\\xEF\\xAC\\x80", NFKC "ff", NFD "\\xEF\\xAC\\x80", NFD "ff"

There is a `--python` option to write some info as Python literal inits, but
for such uses, see `strfchr.py` instead.

==Notes on some parts:==

* Category: A 2-letter name defined by the Unicode standard,
saying what "kind" of character it is.
To see a list, use `--help-categories`.

* '''Literal''': The character itself. How this shows up depends on your
terminal program and settings, shell capabilities, etc.

* '''Unicode''': Shows several ways to express the character. "U+xxxx" is
commonly used in print; the UTF-8 equivalent is given as a series of hex
digits; the same UTF-8 is also given with each byte %-escaped as it would
be in a URL. Finally, there is a note to indicate whether the character is
allowed or not within URLs (without being escaped); that will show "False"
for all non-ASCII characters, and for quite a few ASCII punctuation marks.

* '''Entities''': Shows ways to express the character (other than literally)
within XML or HTML. If HTML 4 defines a named entity for the character,
that is shown last (otherwise, "None")

* '''Unix''' jargon: This shows traditional ways of referring to the character
other than the official Unicode name (if any).

* '''eawidth''':

* '''width''':

* '''NumericValue''': Many unicode characters represent numbers. The most
obvious are the digits 0-9, but there are also
digits in many other scripts;
circled, parenthesized, superscript, or otherwise special digits;
Roman Numerals; fractions; and so on. This line gives the numeric
value associated with the character. For some fractions such
as 1/7, the value is approximate. A few characters that one might expect
to have numeric values, such as pi and Euler's constant. do not.

* '''IsURI''':

* '''IsFPI''':

* '''IsBidi''':

* '''IsCombining''':

* '''IsCombined''':

* '''IsMirror''':

* '''MirrorOf''':

* '''Decomp''': The decomposition of the character, according to
NFD and NFKD, but shown as code points for the individual characters.

* '''Normalizations''': Unicode defines 4 different "normalized" forms
(they are availabe in Python via `unicodedata.normalize(form, [which])`),
for [which] in 'NFC', 'NFD', 'NFKC', or 'NFKD'
(see [https://docs.python.org/2/library/unicodedata.html]:
The forms with "K" use compatibility equivalence: certain characters are
unified with other characters.
For example, U+2160 (ROMAN NUMERAL ONE) and U+0049
(LATIN CAPITAL LETTER I).

Compatibility composition does ''not'' merge characters such as uppercase
English A and Greek alpha, or even soft hyphen. However, forms NKFC and
NFKD do normalize non-breaking space to regular space.

* If the code point is in the range 0x80 to 0xFF, an additional line is displayed
saying what that code point is in the "Mac Roman" character set, and what the
Unicode code point for ''that'' is (unless you set `--nomac`).


=Related Commands=

My `ord`, `chr`, `countChars`, `strfchr.py`.


=Known Bugs and Limitations=

Unicode category names do not display correctly (though mnemonics do).


=To do=

* Option to sanity-check types/values generated, via CProps info.


=Rights=

Copyright 2015 by Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].


=History=

* 2018-04-21: Written by Steven J. DeRose.
* 2018-10-02: Make Py 2/3 compatible. Support --cat for single letters.
Make it avoid non-Unicode (hence nameless) code points. Add --python.
* 2018-11-16: Fix hex display of Unicode normalized forms. Fix html and urllib
includes.
* 2020-02-12: New layout conventions.
* 2021-04-09ff: Enumerate prop names and sync with strfchr.py.
Accept string and other arguments, not just codepoints.
Change property internal names to uppercase. Drop redundant data.
Add actual names for C0 control chars (not just mnemonics).
* 2021-07-09: Add protectDisplay() to avoid displaying literal control chars
or other troublesome ones.
* 2021-07-23: Add MacRoman from Perl `chr`, display it when applicable, and provide
--nomac to suppress.
* 2023-02-21: Drop last Py2 support. Add POSIX regex categories. Switch
charProperties to CProps enum.
* 2023-09-20: Clean up error handling. Fix command-line processing.


=Options=
"""


###############################################################################
# (Data also available in tupleSets/cp1252.xsv, and in "chr")
#
cp1252ToUnicode = {
    0x80 : 0x20AC,   # EURO SIGN
    # 0x81 UNUSED
    0x82 : 0x201A,   # SINGLE LOW-9 QUOTATION MARK
    0x83 : 0x0192,   # LATIN SMALL LETTER F WITH HOOK
    0x84 : 0x201E,   # DOUBLE LOW-9 QUOTATION MARK
    0x85 : 0x2026,   # HORIZONTAL ELLIPSIS
    0x86 : 0x2020,   # DAGGER
    0x87 : 0x2021,   # DOUBLE DAGGER
    0x88 : 0x02C6,   # MODIFIER LETTER CIRCUMFLEX ACCENT
    0x89 : 0x2030,   # PER MILLE SIGN
    0x8A : 0x0160,   # LATIN CAPITAL LETTER S WITH CARON
    0x8B : 0x2039,   # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    0x8C : 0x0152,   # LATIN CAPITAL LIGATURE OE
    # 0x8D UNUSED
    0x8E : 0x017D,   # LATIN CAPITAL LETTER Z WITH CARON
    # 0x8F UNUSED
    # 0x90 UNUSED
    0x91 : 0x2018,   # LEFT SINGLE QUOTATION MARK
    0x92 : 0x2019,   # RIGHT SINGLE QUOTATION MARK
    0x93 : 0x201C,   # LEFT DOUBLE QUOTATION MARK
    0x94 : 0x201D,   # RIGHT DOUBLE QUOTATION MARK
    0x95 : 0x2022,   # BULLET
    0x96 : 0x2013,   # EN DASH
    0x97 : 0x2014,   # EM DASH
    0x98 : 0x02DC,   # SMALL TILDE
    0x99 : 0x2122,   # TRADE MARK SIGN
    0x9A : 0x0161,   # LATIN SMALL LETTER S WITH CARON
    0x9B : 0x203A,   # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    0x9C : 0x0153,   # LATIN SMALL LIGATURE OE
    # 0x9D UNUSED
    0x9E : 0x017E,   # LATIN SMALL LETTER Z WITH CARON
    0x9F : 0x0178,   # LATIN CAPITAL LETTER Y WITH DIAERESIS
}

###############################################################################
# See http://en.wikipedia.org/wiki/Mac_OS_Roman
# (from Perl code in "chr")
#
macRomanData = {
    # mac: ( Unucode Entity    Unicode Name
    ####### C1 #######
    0x80 : ( 0x00C4, "Auml",   "LATIN CAPITAL LETTER A WITH DIAERESIS", ),
    0x81 : ( 0x00C5, "Aring",  "LATIN CAPITAL LETTER A WITH RING ABOVE", ),
    0x82 : ( 0x00C7, "Ccedil", "LATIN CAPITAL LETTER C WITH CEDILLA", ),
    0x83 : ( 0x00C9, "Eacute", "LATIN CAPITAL LETTER E WITH ACUTE", ),
    0x84 : ( 0x00D1, "Ntilde", "LATIN CAPITAL LETTER N WITH TILDE", ),
    0x85 : ( 0x00D6, "Ouml",   "LATIN CAPITAL LETTER O WITH DIAERESIS", ),
    0x86 : ( 0x00DC, "Uuml",   "LATIN CAPITAL LETTER U WITH DIAERESIS", ),
    0x87 : ( 0x00E1, "aacute", "LATIN SMALL LETTER A WITH ACUTE", ),
    0x88 : ( 0x00E0, "agrave", "LATIN SMALL LETTER A WITH GRAVE", ),
    0x89 : ( 0x00E2, "acirc",  "LATIN SMALL LETTER A WITH CIRCUMFLEX", ),
    0x8A : ( 0x00E4, "auml",   "LATIN SMALL LETTER A WITH DIAERESIS", ),
    0x8B : ( 0x00E3, "atilde", "LATIN SMALL LETTER A WITH TILDE", ),
    0x8C : ( 0x00E5, "aring",  "LATIN SMALL LETTER A WITH RING ABOVE", ),
    0x8D : ( 0x00E7, "ccedil", "LATIN SMALL LETTER C WITH CEDILLA", ),
    0x8E : ( 0x00E9, "eacute", "LATIN SMALL LETTER E WITH ACUTE", ),
    0x8F : ( 0x00E8, "egrave", "LATIN SMALL LETTER E WITH GRAVE", ),
    0x90 : ( 0x00EA, "ecirc",  "LATIN SMALL LETTER E WITH CIRCUMFLEX", ),
    0x91 : ( 0x00EB, "euml",   "LATIN SMALL LETTER E WITH DIAERESIS", ),
    0x92 : ( 0x00ED, "iacute", "LATIN SMALL LETTER I WITH ACUTE", ),
    0x93 : ( 0x00EC, "igrave", "LATIN SMALL LETTER I WITH GRAVE", ),
    0x94 : ( 0x00EE, "icirc",  "LATIN SMALL LETTER I WITH CIRCUMFLEX", ),
    0x95 : ( 0x00EF, "iuml",   "LATIN SMALL LETTER I WITH DIAERESIS", ),
    0x96 : ( 0x00F1, "ntilde", "LATIN SMALL LETTER N WITH TILDE", ),
    0x97 : ( 0x00F3, "oacute", "LATIN SMALL LETTER O WITH ACUTE", ),
    0x98 : ( 0x00F2, "ograve", "LATIN SMALL LETTER O WITH GRAVE", ),
    0x99 : ( 0x00F4, "ocirc",  "LATIN SMALL LETTER O WITH CIRCUMFLEX", ),
    0x9A : ( 0x00F6, "ouml",   "LATIN SMALL LETTER O WITH DIAERESIS", ),
    0x9B : ( 0x00F5, "otilde", "LATIN SMALL LETTER O WITH TILDE", ),
    0x9C : ( 0x00FA, "uacute", "LATIN SMALL LETTER U WITH ACUTE", ),
    0x9D : ( 0x00F9, "ugrave", "LATIN SMALL LETTER U WITH GRAVE", ),
    0x9E : ( 0x00FB, "ucirc",  "LATIN SMALL LETTER U WITH CIRCUMFLEX", ),
    0x9F : ( 0x00FC, "uuml",   "LATIN SMALL LETTER U WITH DIAERESIS", ),
    ####### G1 #######
    0xA0 : ( 0x2020, "dagger", "DAGGER", ),
    0xA1 : ( 0x00B0, "deg",    "DEGREE SIGN", ),
    0xA2 : ( 0x00A2, "cent",   "CENT SIGN", ),
    0xA3 : ( 0x00A3, "pound",  "POUND SIGN", ),
    0xA4 : ( 0x00A7, "sect",   "SECTION SIGN", ),
    0xA5 : ( 0x2022, "bull",   "BULLET", ),
    0xA6 : ( 0x00B6, "para",   "PILCROW SIGN", ),
    0xA7 : ( 0x00DF, "szlig",  "LATIN SMALL LETTER SHARP S", ),
    0xA8 : ( 0x00AE, "reg",    "REGISTERED SIGN", ),
    0xA9 : ( 0x00A9, "copy",   "COPYRIGHT SIGN", ),
    0xAA : ( 0x2122, "trade",  "TRADE MARK SIGN", ),
    0xAB : ( 0x00B4, "acute",  "ACUTE ACCENT", ),
    0xAC : ( 0x00A8, "uml",    "DIAERESIS", ),
    0xAD : ( 0x2260, "ne",     "NOT EQUAL TO", ),
    0xAE : ( 0x00C6, "AElig",  "LATIN CAPITAL LETTER AE", ),
    0xAF : ( 0x00D8, "Oslash", "LATIN CAPITAL LETTER O WITH STROKE", ),
    0xB0 : ( 0x221E, "infin",  "INFINITY", ),
    0xB1 : ( 0x00B1, "plusmn", "PLUS-MINUS SIGN", ),
    0xB2 : ( 0x2264, "le",     "LESS-THAN OR EQUAL TO", ),
    0xB3 : ( 0x2265, "ge",     "GREATER-THAN OR EQUAL TO", ),
    0xB4 : ( 0x00A5, "yen",    "YEN SIGN", ),
    0xB5 : ( 0x00B5, "micro",  "MICRO SIGN", ),
    0xB6 : ( 0x2202, "part",   "PARTIAL DIFFERENTIAL", ),
    0xB7 : ( 0x2211, "sum",    "N-ARY SUMMATION", ),
    0xB8 : ( 0x220F, "prod",   "N-ARY PRODUCT", ),
    0xB9 : ( 0x03C0, "pi",     "GREEK SMALL LETTER PI", ),
    0xBA : ( 0x222B, "int",    "INTEGRAL", ),
    0xBB : ( 0x00AA, "ordf",   "FEMININE ORDINAL INDICATOR", ),
    0xBC : ( 0x00BA, "ordm",   "MASCULINE ORDINAL INDICATOR", ),
    0xBD : ( 0x03A9, "Omega",  "GREEK CAPITAL LETTER OMEGA", ),
    0xBE : ( 0x00E6, "aelig",  "LATIN SMALL LETTER AE", ),
    0xBF : ( 0x00F8, "oslash", "LATIN SMALL LETTER O WITH STROKE", ),
    0xC0 : ( 0x00BF, "iquest", "INVERTED QUESTION MARK", ),
    0xC1 : ( 0x00A1, "iexcl",  "INVERTED EXCLAMATION MARK", ),
    0xC2 : ( 0x00AC, "not",    "NOT SIGN", ),
    0xC3 : ( 0x221A, "radic",  "SQUARE ROOT", ),
    0xC4 : ( 0x0192, "fnof",   "LATIN SMALL LETTER F WITH HOOK", ),
    0xC5 : ( 0x2248, "asymp",  "ALMOST EQUAL TO", ),
    0xC6 : ( 0x2206, "",       "INCREMENT", ),
    0xC7 : ( 0x00AB, "laquo",  "LEFT-POINTING DOUBLE ANGLE QUOTATION MARK", ),
    0xC8 : ( 0x00BB, "raquo",  "RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK", ),
    0xC9 : ( 0x2026, "hellip", "HORIZONTAL ELLIPSIS", ),
    0xCA : ( 0x00A0, "nbsp",   "NO-BREAK SPACE", ),
    0xCB : ( 0x00C0, "Agrave", "LATIN CAPITAL LETTER A WITH GRAVE", ),
    0xCC : ( 0x00C3, "Atilde", "LATIN CAPITAL LETTER A WITH TILDE", ),
    0xCD : ( 0x00D5, "Otilde", "LATIN CAPITAL LETTER O WITH TILDE", ),
    0xCE : ( 0x0152, "OElig",  "LATIN CAPITAL LIGATURE OE", ),
    0xCF : ( 0x0153, "oelig",  "LATIN SMALL LIGATURE OE", ),
    0xD0 : ( 0x2013, "ndash",  "EN DASH", ),
    0xD1 : ( 0x2014, "mdash",  "EM DASH", ),
    0xD2 : ( 0x201C, "ldquo",  "LEFT DOUBLE QUOTATION MARK", ),
    0xD3 : ( 0x201D, "rdquo",  "RIGHT DOUBLE QUOTATION MARK", ),
    0xD4 : ( 0x2018, "lsquo",  "LEFT SINGLE QUOTATION MARK", ),
    0xD5 : ( 0x2019, "rsquo",  "RIGHT SINGLE QUOTATION MARK", ),
    0xD6 : ( 0x00F7, "divide", "DIVISION SIGN", ),
    0xD7 : ( 0x25CA, "loz",    "LOZENGE", ),
    0xD8 : ( 0x00FF, "yuml",   "LATIN SMALL LETTER Y WITH DIAERESIS", ),
    0xD9 : ( 0x0178, "Yuml",   "LATIN CAPITAL LETTER Y WITH DIAERESIS", ),
    0xDA : ( 0x2044, "frasl",  "FRACTION SLASH", ),
    0xDB : ( 0x20AC, "euro",   "EURO SIGN", ),
    0xDC : ( 0x2039, "lsaquo", "SINGLE LEFT-POINTING ANGLE QUOTATION MARK", ),
    0xDD : ( 0x203A, "rsaquo", "SINGLE RIGHT-POINTING ANGLE QUOTATION MARK", ),
    0xDE : ( 0xFB01, "",       "LATIN SMALL LIGATURE FI", ),
    0xDF : ( 0xFB02, "",       "LATIN SMALL LIGATURE FL", ),
    0xE0 : ( 0x2021, "Dagger", "DOUBLE DAGGER", ),
    0xE1 : ( 0x00B7, "middot", "MIDDLE DOT", ),
    0xE2 : ( 0x201A, "sbquo",  "SINGLE LOW-9 QUOTATION MARK", ),
    0xE3 : ( 0x201E, "bdquo",  "DOUBLE LOW-9 QUOTATION MARK", ),
    0xE4 : ( 0x2030, "permil", "PER MILLE SIGN", ),
    0xE5 : ( 0x00C2, "Acirc",  "LATIN CAPITAL LETTER A WITH CIRCUMFLEX", ),
    0xE6 : ( 0x00CA, "Ecirc",  "LATIN CAPITAL LETTER E WITH CIRCUMFLEX", ),
    0xE7 : ( 0x00C1, "Aacute", "LATIN CAPITAL LETTER A WITH ACUTE", ),
    0xE8 : ( 0x00CB, "Euml",   "LATIN CAPITAL LETTER E WITH DIAERESIS", ),
    0xE9 : ( 0x00C8, "Egrave", "LATIN CAPITAL LETTER E WITH GRAVE", ),
    0xEA : ( 0x00CD, "Iacute", "LATIN CAPITAL LETTER I WITH ACUTE", ),
    0xEB : ( 0x00CE, "Icirc",  "LATIN CAPITAL LETTER I WITH CIRCUMFLEX", ),
    0xEC : ( 0x00CF, "Iuml",   "LATIN CAPITAL LETTER I WITH DIAERESIS", ),
    0xED : ( 0x00CC, "Igrave", "LATIN CAPITAL LETTER I WITH GRAVE", ),
    0xEE : ( 0x00D3, "Oacute", "LATIN CAPITAL LETTER O WITH ACUTE", ),
    0xEF : ( 0x00D4, "Ocirc",  "LATIN CAPITAL LETTER O WITH CIRCUMFLEX", ),
    # WARNING: Apple uses U+F8FF for their logo, but that's private-use.
    0xF0 : ( 0xF8FF, "",       "APPLE LOGO", ),
    0xF1 : ( 0x00D2, "Ograve", "LATIN CAPITAL LETTER O WITH GRAVE", ),
    0xF2 : ( 0x00DA, "Uacute", "LATIN CAPITAL LETTER U WITH ACUTE", ),
    0xF3 : ( 0x00DB, "Ucirc",  "LATIN CAPITAL LETTER U WITH CIRCUMFLEX", ),
    0xF4 : ( 0x00D9, "Ugrave", "LATIN CAPITAL LETTER U WITH GRAVE", ),
    0xF5 : ( 0x0131, "",       "LATIN SMALL LETTER DOTLESS I", ),
    0xF6 : ( 0x02C6, "circ",   "MODIFIER LETTER CIRCUMFLEX ACCENT", ),
    0xF7 : ( 0x02DC, "tilde",  "SMALL TILDE", ),
    0xF8 : ( 0x00AF, "macr",   "MACRON", ),
    0xF9 : ( 0x02D8, "",       "BREVE", ),
    0xFA : ( 0x02D9, "",       "DOT ABOVE", ),
    0xFB : ( 0x02DA, "",       "RING ABOVE", ),
    0xFC : ( 0x00B8, "cedil",  "CEDILLA", ),
    0xFD : ( 0x02DD, "",       "DOUBLE ACUTE ACCENT", ),
    0xFE : ( 0x02DB, "",       "OGONEK", ),
    0xFF : ( 0x02C7, "",       "CARON", ),
} # macRomanData

assert len(macRomanData) == 128

# TODO: Move to separate test process
for i in sorted(macRomanData.keys()):
    if (i<128 or i>255 or len(macRomanData[i]) != 3):
        lg.critical("macRomanData table error, entry %d is %s", i, repr(macRomanData[i]))
        sys.exit()
    ucp, ent, nam = macRomanData[i]
    if ((not isinstance(ucp, int)) or ucp < 0XA0 or ucp > 0xFB02):
        raise ValueError(
            "macRomanData[%04x]: Unicode equivalent %04x out of range." % (i, ucp))
    if (ent):
        cpOfEntity = name2codepoint[ent]
        if (cpOfEntity != ucp):
            raise ValueError(
                "macRomanData[%04x]: entity '%s' maps to %04x ('%s'), not %04x." %
                (i, ent, cpOfEntity, codepoint2name[cpOfEntity], ucp))
    if (not re.match(r"[- A-Z0-9]{5,}$", nam)):
        raise ValueError("macRomanData for %04x: bad name '%s'." % (i, nam))

ASCII = [
    #Dec, Lit|Mnem, Name,                Hex, fpiOK,uriOK
    #
    [  0, "NUL", "NULL",                 0x00, "-", "-" ],
    [  1, "SOH", "Start of Heading",     0x01, "-", "-" ],
    [  2, "STX", "End of heading",       0x02, "-", "-" ],
    [  3, "ETX", "End of text",          0x03, "-", "-" ],
    [  4, "EOT", "End of transmission",  0x04, "-", "-" ],
    [  5, "ENQ", "Enquiry",              0x05, "-", "-" ],
    [  6, "ACK", "Acknowledge",          0x06, "-", "-" ],
    [  7, "BEL", "Bell",                 0x07, "-", "-" ],

    [  8, "BS", "Backspace",             0x08, "-", "-" ],
    [  9, "TAB","Horizontal tabulation", 0x09, "-", "-" ],
    [ 10, "LF", "Line feed",             0x0A, "+", "-" ],
    [ 11, "VT", "Vertical tabulation",   0x0B, "-", "-" ],
    [ 12, "FF", "Form feed",             0x0C, "-", "-" ],
    [ 13, "CR", "Carriage return",       0x0D, "+", "-" ],
    [ 14, "SO", "Shift out",             0x0E, "-", "-" ],
    [ 15, "SI", "Shift in",              0x0F, "-", "-" ],

    [ 16, "DLE", "Data link escape",     0x10, "-", "-" ],
    [ 17, "DC1", "Device control 1",     0x11, "-", "-" ],
    [ 18, "DC2", "Device control 2",     0x12, "-", "-" ],
    [ 19, "DC3", "Device control 3",     0x13, "-", "-" ],
    [ 20, "DC4", "Device control 4",     0x14, "-", "-" ],
    [ 21, "NAK", "Negative acknowledge", 0x15, "-", "-" ],
    [ 22, "SYN", "Synchronous Idle",     0x16, "-", "-" ],
    [ 23, "ETB", "End of transmission block", 0x17, "-", "-" ],

    [ 24, "CAN", "Cancel",               0x18, "-", "-" ],
    [ 25, "EM",  "End message",          0x19, "-", "-" ],
    [ 26, "SUB", "Substitute character", 0x1a, "-", "-" ],
    [ 27, "ESC", "Escape",               0x1B, "-", "-" ],
    [ 28, "FS",  "Field Separator",      0x1c, "-", "-" ],
    [ 29, "GS",  "Group Separator",      0x1d, "-", "-" ],
    [ 30, "RS",  "Record Separator",     0x1e, "-", "-" ],
    [ 31, "US",  "Unit Separator",       0x1f, "-", "-" ],

    [ 32, "SPACE","SPACE",               0x20, "+", "-" ],
    [ 33, "!",  "exclamation mark",      0x21, "-", "+" ],
    [ 34, '"',  "quotation mark",        0x22, "-", "*" ],
    [ 35, "#",  "number sign",           0x23, "-", "-" ],
    [ 36, "$",  "dollar sign",           0x24, "-", "+" ],
    [ 37, "%",  "percent sign",          0x25, "-", "(escape)" ],
    [ 38, "&",  "ampersand",             0x26, "-", "*" ],
    [ 39, "'",  "apostrophe",            0x27, "+", "+" ],

    [ 40, "(",  "left parenthesis",      0x28, "+", "+" ],
    [ 41, ")",  "right parenthesis",     0x29, "+", "+" ],
    [ 42, "*",  'asterisk',              0x2A, "-", '+' ],
    [ 43, "+",  "plus sign",             0x2B, "+", "+" ],
    [ 44, ",",  "comma",                 0x2C, "+", "-" ],
    [ 45, "-",  "hyphen, minus sign",    0x2D, "+", "+" ],
    [ 46, ".",  "full stop",             0x2E, "+", "+" ],
    [ 47, "/",  "solidus",               0x2F, "+", "~" ],

    [ 48, "0",  "digit 0",               0x30, "+", "+" ],
    [ 49, "1",  "digit 1",               0x31, "+", "+" ],
    [ 50, "2",  "digit 2",               0x32, "+", "+" ],
    [ 51, "3",  "digit 3",               0x33, "+", "+" ],
    [ 52, "4",  "digit 4",               0x34, "+", "+" ],
    [ 53, "5",  "digit 5",               0x35, "+", "+" ],
    [ 54, "6",  "digit 6",               0x36, "+", "+" ],
    [ 55, "7",  "digit 7",               0x37, "+", "+" ],
    [ 56, "8",  "digit 8",               0x38, "+", "+" ],

    [ 57, "9",  "digit 9",               0x39, "+", "+" ],
    [ 58, ",",  "colon",                 0x3A, "+", "~" ],
    [ 59, ";",  "semicolon",             0x3B, "-", "~" ],
    [ 60, "<",  "less-than sign",        0x3C, "-", "*" ],
    [ 61, "=",  "equals sign",           0x3D, "+", "~" ],
    [ 62, ">",  "greater-than sign",     0x3E, "-", "*" ],
    [ 63, "?",  "question mark",         0x3F, "+", "~" ],

    [ 64, "@",  "commercial at",         0x40, "-", "~" ],
    [ 65, "A",  "capital letter A",      0x41, "+", "+" ],
    [ 66, "B",  "capital letter B",      0x42, "+", "+" ],
    [ 67, "C",  "capital letter C",      0x43, "+", "+" ],
    [ 68, "D",  "capital letter D",      0x44, "+", "+" ],
    [ 69, "E",  "capital letter E",      0x45, "+", "+" ],
    [ 70, "F",  "capital letter F",      0x46, "+", "+" ],
    [ 71, "G",  "capital letter G",      0x47, "+", "+" ],

    [ 72, "H",  "capital letter H",      0x48, "+", "+" ],
    [ 73, "I",  "capital letter I",      0x49, "+", "+" ],
    [ 74, "J",  "capital letter J",      0x4A, "+", "+" ],
    [ 75, "K",  "capital letter K",      0x4B, "+", "+" ],
    [ 76, "L",  "capital letter L",      0x4C, "+", "+" ],
    [ 77, "M",  "capital letter M",      0x4D, "+", "+" ],
    [ 78, "N",  "capital letter N",      0x4E, "+", "+" ],
    [ 79, "O",  "capital letter O",      0x4F, "+", "+" ],

    [ 80, "P",  "capital letter P",      0x50, "+", "+" ],
    [ 81, "Q",  "capital letter Q",      0x51, "+", "+" ],
    [ 82, "R",  "capital letter R",      0x52, "+", "+" ],
    [ 83, "S",  "capital letter S",      0x53, "+", "+" ],
    [ 84, "T",  "capital letter T",      0x54, "+", "+" ],
    [ 85, "U",  "capital letter U",      0x55, "+", "+" ],
    [ 86, "V",  "capital letter V",      0x56, "+", "+" ],
    [ 87, "W",  "capital letter W",      0x57, "+", "+" ],

    [ 88, "X",  "capital letter X",      0x58, "+", "+" ],
    [ 89, "Y",  "capital letter Y",      0x59, "+", "+" ],
    [ 90, "Z",  "capital letter Z",      0x5A, "+", "+" ],
    [ 91, "[",  "left square bracket",   0x5B, "-", "-" ],
    [ 92, "\\", "reverse solidus",       0x5C, "-", "-" ],
    [ 93, "]",  "right square bracket",  0x5D, "-", "*" ],
    [ 94, "^",  "circumflex",            0x5E, "-", "-" ],
    [ 95, "_",  "underscore",            0x5F, "-", "+" ],

    [ 96, "`",  "grave",                 0x60, "-", "-" ],
    [ 97, "a",  "small letter a",        0x61, "+", "+" ],
    [ 98, "b",  "small letter b",        0x62, "+", "+" ],
    [ 99, "c",  "small letter c",        0x63, "+", "+" ],
    [ 100, "d", "small letter d",        0x64, "+", "+" ],
    [ 101, "e", "small letter e",        0x65, "+", "+" ],
    [ 102, "f", "small letter f",        0x66, "+", "+" ],
    [ 103, "g", "small letter g",        0x67, "+", "+" ],

    [ 104, "h", "small letter h",        0x68, "+", "+" ],
    [ 105, "i", "small letter i",        0x69, "+", "+" ],
    [ 106, "j", "small letter j",        0x6A, "+", "+" ],
    [ 107, "k", "small letter k",        0x6B, "+", "+" ],
    [ 108, "l", "small letter l",        0x6C, "+", "+" ],
    [ 109, "m", "small letter m",        0x6D, "+", "+" ],
    [ 110, "n", "small letter n",        0x6E, "+", "+" ],
    [ 111, "o", "small letter o",        0x6F, "+", "+" ],

    [ 112, "p", "small letter p",        0x70, "+", "+" ],
    [ 113, "q", "small letter q",        0x71, "+", "+" ],
    [ 114, "r", "small letter r",        0x72, "+", "+" ],
    [ 115, "s", "small letter s",        0x73, "+", "+" ],
    [ 116, "t", "small letter t",        0x74, "+", "+" ],
    [ 117, "u", "small letter u",        0x75, "+", "+" ],
    [ 118, "v", "small letter v",        0x76, "+", "+" ],
    [ 119, "w", "small letter w",        0x77, "+", "+" ],

    [ 120, "x", "small letter x",        0x78, "+", "+" ],
    [ 121, "y", "small letter y",        0x79, "+", "+" ],
    [ 122, "z", "small letter z",        0x7A, "+", "+" ],
    [ 123, "{", "left curly bracket",    0x7B, "-", "-" ],
    [ 124, "|", "vertical bar",          0x7C, "-", "-" ],
    [ 125, "}", "right curly bracket",   0x7D, "-", "-" ],
    [ 126, "~", "tilde",                 0x7E, "-", "-" ],
    [ 127, "\xFF", "DELETE or Y WITH DIAERESIS", 0x7F, "-", "-" ],
]

for i in range(0, 128):
    if (ASCII[i][0] != i or len(ASCII[i]) != 6):
        lg.error("ASCII table error, entry %d is %s", i, repr(ASCII[i]))
        sys.exit()

C0Names = [  # Not in unicodedata.name...
    "NULL",
    "START OF HEADING",
    "START OF TEXT",
    "END OF TEXT",
    "END OF TRANSMISSION",
    "ENQUIRY",
    "ACKNOWLEDGE",
    "BELL",
    "BACKSPACE",
    "CHARACTER TABULATION",
    "LINE FEED (LF)",
    "LINE TABULATION",
    "FORM FEED (FF)",
    "CARRIAGE RETURN (CR)",
    "SHIFT OUT",
    "SHIFT IN",
    "DATA LINK ESCAPE",
    "DEVICE CONTROL ONE",
    "DEVICE CONTROL TWO",
    "DEVICE CONTROL THREE",
    "DEVICE CONTROL FOUR",
    "NEGATIVE ACKNOWLEDGE",
    "SYNCHRONOUS IDLE",
    "END OF TRANSMISSION BLOCK",
    "CANCEL",
    "END OF MEDIUM",
    "SUBSTITUTE",
    "ESCAPE",
    "INFORMATION SEPARATOR FOUR",
    "INFORMATION SEPARATOR THREE",
    "INFORMATION SEPARATOR TWO",
    "INFORMATION SEPARATOR ONE",
]
assert len(C0Names) == 32

# Second string here has special, reserved, etc. chars.
okInUriExpr = r"[%s]" % ("!$'()*+-._0-9A-Za-z" + r'"%&/:;<=>\?@]')

# And for SGML Formal Public Identifiers.
okInFpiExpr = r"[\n\r '()+,-./0-9:=?A-Za-z]"

def okInFPI(n:int) -> bool: return (n<128 and ASCII[n][4] == "+")
def okInURI(n:int) -> bool: return (n<128 and ASCII[n][5] == "+")

C0Mnemonics = [
    "NUL", "SOH", "STX", "ETX", "EOT", "ENQ", "ACK", "BEL",
    "BS",  "HT",  "LF",  "VT",  "FF",  "CR",  "SO",  "SI",
    "DLE", "DC1", "DC2", "DC3", "DC4", "NAK", "SYN", "ETB",
    "CAN", "EM",  "SUB", "ESC", "FS",  "GS",  "RS",  "US",
    "SP"
]
assert len(C0Mnemonics) == 33

C1Mnemonics = [
    "PAD", "HOP",  "BPH", "NBH", "IND", "NEL", "SSA", "ESA",
    "HTS", "HTJ",  "VTS", "PLD", "PLU",  "RI", "SS2", "SS3",
    "DCS", "PU1",  "PU2", "STS", "CCH",  "MW", "SPA", "EPA",
    "SOS", "SGCI", "SCI", "CSI",  "ST", "OSC",  "PM", "APC",
    "NBS"
]
assert len(C1Mnemonics) == 33

# Perhaps should add:
#    arrows, dingbats, alpha/syll/ideo, emoji (is that a script?)
#    domains: game, music, display, cartography, alchemy
#
###############################################################################
# Unicode "general categories", available via unicodedata.category(c)
# https://stackoverflow.com/questions/1832893/
# regex also supports single-char cover categories, I think.
#
unicodeCategories = {  # Replaces categoryAbbr2Name
    "C":   "Other (all subtypes)",
    "L":   "Letter (all subtypes)",
    "M":   "Mark (all subtypes)",
    "N":   "Number (all subtypes)",
    "P":   "Punctuation (all subtypes)",
    "S":   "Symbol (all subtypes)",
    "Z":   "Separator (all subtypes)",

    "Cc":  "Other, Control",
    "Cf":  "Other, Format",
    "Cn":  "Other, Not Assigned",
    "Co":  "Other, Private Use",
    "Cs":  "Other, Surrogate",
    "LC":  "Letter, Cased",
    "Ll":  "Letter, Lowercase",
    "Lm":  "Letter, Modifier",
    "Lo":  "Letter, Other",
    "Lt":  "Letter, Titlecase",
    "Lu":  "Letter, Uppercase",
    "Mc":  "Mark, Spacing Combining",
    "Me":  "Mark, Enclosing",
    "Mn":  "Mark, Nonspacing",
    "Nd":  "Number, Decimal Digit",
    "Nl":  "Number, Letter",
    "No":  "Number, Other",
    "Pc":  "Punctuation, Connector",
    "Pd":  "Punctuation, Dash",
    "Pe":  "Punctuation, Close",
    "Pf":  "Punctuation, Final quote",
    "Pi":  "Punctuation, Initial quote",
    "Po":  "Punctuation, Other",
    "Ps":  "Punctuation, Open",
    "Sc":  "Symbol, Currency",
    "Sk":  "Symbol, Modifier",
    "Sm":  "Symbol, Math",
    "So":  "Symbol, Other",
    "Zl":  "Separator, Line",
    "Zp":  "Separator, Paragraph",
    "Zs":  "Separator, Space",
}
if (len(unicodeCategories) != 38):
    lg.critical("Bad item count for unicodeCategories: %d.", len(unicodeCategories))
    sys.exit()

_blocks = []
def _initBlocks(text):
    pattern = re.compile(r"([0-9A-F]+)\.\.([0-9A-F]+);\ (\S.*\S)")
    for line in text.splitlines():
        m = pattern.match(line)
        if m:
            start, end, name = m.groups()
            _blocks.append((int(start, 16), int(end, 16), name))

# retrieved from http://unicode.org/Public/UNIDATA/Blocks.txt
_initBlocks('''
# Blocks-5.1.0.txt
# Date: 2008-03-20, 17:41:00 PDT [KW]
#
# Unicode Character Database
# Copyright (c) 1991-2008 Unicode, Inc.
# For terms of use, see http://www.unicode.org/terms_of_use.html
# For documentation, see UCD.html
#
# Note:   The casing of block names is not normative.
#         For example, "Basic Latin" and "BASIC LATIN" are equivalent.
#
# Format:
# Start Code..End Code; Block Name
#
# Note:   When comparing block names, casing, whitespace, hyphens,
#         and underbars are ignored.
#         For example, "Latin Extended-A" and "latin extended a" are equivalent.
#         For more information on the comparison of property values,
#            see UCD.html.
#
#  All code points not explicitly listed for Block
#  have the value No_Block.

# Property: Block
#
# @missing: 0000..10FFFF; No_Block

0000..007F; Basic Latin
0080..00FF; Latin-1 Supplement
0100..017F; Latin Extended-A
0180..024F; Latin Extended-B
0250..02AF; IPA Extensions
02B0..02FF; Spacing Modifier Letters
0300..036F; Combining Diacritical Marks
0370..03FF; Greek and Coptic
0400..04FF; Cyrillic
0500..052F; Cyrillic Supplement
0530..058F; Armenian
0590..05FF; Hebrew
0600..06FF; Arabic
0700..074F; Syriac
0750..077F; Arabic Supplement
0780..07BF; Thaana
07C0..07FF; NKo
0900..097F; Devanagari
0980..09FF; Bengali
0A00..0A7F; Gurmukhi
0A80..0AFF; Gujarati
0B00..0B7F; Oriya
0B80..0BFF; Tamil
0C00..0C7F; Telugu
0C80..0CFF; Kannada
0D00..0D7F; Malayalam
0D80..0DFF; Sinhala
0E00..0E7F; Thai
0E80..0EFF; Lao
0F00..0FFF; Tibetan
1000..109F; Myanmar
10A0..10FF; Georgian
1100..11FF; Hangul Jamo
1200..137F; Ethiopic
1380..139F; Ethiopic Supplement
13A0..13FF; Cherokee
1400..167F; Unified Canadian Aboriginal Syllabics
1680..169F; Ogham
16A0..16FF; Runic
1700..171F; Tagalog
1720..173F; Hanunoo
1740..175F; Buhid
1760..177F; Tagbanwa
1780..17FF; Khmer
1800..18AF; Mongolian
1900..194F; Limbu
1950..197F; Tai Le
1980..19DF; New Tai Lue
19E0..19FF; Khmer Symbols
1A00..1A1F; Buginese
1B00..1B7F; Balinese
1B80..1BBF; Sundanese
1C00..1C4F; Lepcha
1C50..1C7F; Ol Chiki
1D00..1D7F; Phonetic Extensions
1D80..1DBF; Phonetic Extensions Supplement
1DC0..1DFF; Combining Diacritical Marks Supplement
1E00..1EFF; Latin Extended Additional
1F00..1FFF; Greek Extended
2000..206F; General Punctuation
2070..209F; Superscripts and Subscripts
20A0..20CF; Currency Symbols
20D0..20FF; Combining Diacritical Marks for Symbols
2100..214F; Letterlike Symbols
2150..218F; Number Forms
2190..21FF; Arrows
2200..22FF; Mathematical Operators
2300..23FF; Miscellaneous Technical
2400..243F; Control Pictures
2440..245F; Optical Character Recognition
2460..24FF; Enclosed Alphanumerics
2500..257F; Box Drawing
2580..259F; Block Elements
25A0..25FF; Geometric Shapes
2600..26FF; Miscellaneous Symbols
2700..27BF; Dingbats
27C0..27EF; Miscellaneous Mathematical Symbols-A
27F0..27FF; Supplemental Arrows-A
2800..28FF; Braille Patterns
2900..297F; Supplemental Arrows-B
2980..29FF; Miscellaneous Mathematical Symbols-B
2A00..2AFF; Supplemental Mathematical Operators
2B00..2BFF; Miscellaneous Symbols and Arrows
2C00..2C5F; Glagolitic
2C60..2C7F; Latin Extended-C
2C80..2CFF; Coptic
2D00..2D2F; Georgian Supplement
2D30..2D7F; Tifinagh
2D80..2DDF; Ethiopic Extended
2DE0..2DFF; Cyrillic Extended-A
2E00..2E7F; Supplemental Punctuation
2E80..2EFF; CJK Radicals Supplement
2F00..2FDF; Kangxi Radicals
2FF0..2FFF; Ideographic Description Characters
3000..303F; CJK Symbols and Punctuation
3040..309F; Hiragana
30A0..30FF; Katakana
3100..312F; Bopomofo
3130..318F; Hangul Compatibility Jamo
3190..319F; Kanbun
31A0..31BF; Bopomofo Extended
31C0..31EF; CJK Strokes
31F0..31FF; Katakana Phonetic Extensions
3200..32FF; Enclosed CJK Letters and Months
3300..33FF; CJK Compatibility
3400..4DBF; CJK Unified Ideographs Extension A
4DC0..4DFF; Yijing Hexagram Symbols
4E00..9FFF; CJK Unified Ideographs
A000..A48F; Yi Syllables
A490..A4CF; Yi Radicals
A500..A63F; Vai
A640..A69F; Cyrillic Extended-B
A700..A71F; Modifier Tone Letters
A720..A7FF; Latin Extended-D
A800..A82F; Syloti Nagri
A840..A87F; Phags-pa
A880..A8DF; Saurashtra
A900..A92F; Kayah Li
A930..A95F; Rejang
AA00..AA5F; Cham
AC00..D7AF; Hangul Syllables
D800..DB7F; High Surrogates
DB80..DBFF; High Private Use Surrogates
DC00..DFFF; Low Surrogates
E000..F8FF; Private Use Area
F900..FAFF; CJK Compatibility Ideographs
FB00..FB4F; Alphabetic Presentation Forms
FB50..FDFF; Arabic Presentation Forms-A
FE00..FE0F; Variation Selectors
FE10..FE1F; Vertical Forms
FE20..FE2F; Combining Half Marks
FE30..FE4F; CJK Compatibility Forms
FE50..FE6F; Small Form Variants
FE70..FEFF; Arabic Presentation Forms-B
FF00..FFEF; Halfwidth and Fullwidth Forms
FFF0..FFFF; Specials
10000..1007F; Linear B Syllabary
10080..100FF; Linear B Ideograms
10100..1013F; Aegean Numbers
10140..1018F; Ancient Greek Numbers
10190..101CF; Ancient Symbols
101D0..101FF; Phaistos Disc
10280..1029F; Lycian
102A0..102DF; Carian
10300..1032F; Old Italic
10330..1034F; Gothic
10380..1039F; Ugaritic
103A0..103DF; Old Persian
10400..1044F; Deseret
10450..1047F; Shavian
10480..104AF; Osmanya
10800..1083F; Cypriot Syllabary
10900..1091F; Phoenician
10920..1093F; Lydian
10A00..10A5F; Kharoshthi
12000..123FF; Cuneiform
12400..1247F; Cuneiform Numbers and Punctuation
1D000..1D0FF; Byzantine Musical Symbols
1D100..1D1FF; Musical Symbols
1D200..1D24F; Ancient Greek Musical Notation
1D300..1D35F; Tai Xuan Jing Symbols
1D360..1D37F; Counting Rod Numerals
1D400..1D7FF; Mathematical Alphanumeric Symbols
1F000..1F02F; Mahjong Tiles
1F030..1F09F; Domino Tiles
20000..2A6DF; CJK Unified Ideographs Extension B
2F800..2FA1F; CJK Compatibility Ideographs Supplement
E0000..E007F; Tags
E0100..E01EF; Variation Selectors Supplement
F0000..FFFFF; Supplementary Private Use Area-A
100000..10FFFF; Supplementary Private Use Area-B

# EOF
''')


###############################################################################

# See https://gist.github.com/anonymous/2204527 and
# https://stackoverflow.com/questions/9868792/
#
script_data = {
  "scriptNames": [
    "Common",      "Latin",        "Greek",        "Cyrillic",   "Armenian",
    "Hebrew",      "Arabic",       "Syriac",       "Thaana",     "Devanagari",
    "Bengali",     "Gurmukhi",     "Gujarati",     "Oriya",      "Tamil",
    "Telugu",      "Kannada",      "Malayalam",    "Sinhala",    "Thai",
    "Lao",         "Tibetan",      "Myanmar",      "Georgian",   "Hangul",
    "Ethiopic",    "Cherokee", "Canadian_Aboriginal","Ogham",    "Runic",
    "Khmer",       "Mongolian",    "Hiragana",     "Katakana",   "Bopomofo",
    "Han",         "Yi",           "Old_Italic",   "Gothic",     "Deseret",
    "Inherited",   "Tagalog",      "Hanunoo",      "Buhid",      "Tagbanwa",
    "Limbu",       "Tai_Le",       "Linear_B",     "Ugaritic",   "Shavian",
    "Osmanya",     "Cypriot",      "Braille",      "Buginese",   "Coptic",
    "New_Tai_Lue", "Glagolitic",   "Tifinagh",   "Syloti_Nagri", "Old_Persian",
    "Kharoshthi",  "Balinese",     "Cuneiform",    "Phoenician", "Phags_Pa",
    "Nko",         "Sundanese",    "Lepcha",       "Ol_Chiki",   "Vai",
    "Saurashtra",  "Kayah_Li",     "Rejang",       "Lycian",     "Carian",
    "Lydian",      "Cham",         "Tai_Tham",     "Tai_Viet",   "Avestan",
    "Egyptian_Hieroglyphs","Samaritan", "Lisu",    "Bamum",      "Javanese",
    "Meetei_Mayek","Imperial_Aramaic", "Old_South_Arabian",
                            "Inscriptional_Parthian", "Inscriptional_Pahlavi",
    "Old_Turkic",  "Kaithi",       "Batak",        "Brahmi",     "Mandaic",
    "Chakma", "Meroitic_Cursive", "Meroitic_Hieroglyphs","Miao", "Sharada",
    "Sora_Sompeng","Takri"
  ],
  "categoryAbbrs": [  # This is MISSING several categories (see unicodeCategories)
    "Cc", "Zs", "Po", "Sc", "Ps", "Pe", "Sm", "Pd",
    "Nd", "Sk", "Pc", "So", "Pi", "Cf", "No", "L",
    "Pf", "Lm", "Mc", "Lo", "Zl", "Zp", "Nl", "Mn", "Me"
  ],

  "idx": [  # Start, end, script, category
####### 0x0000...
(0x000,0x01f, 0, 0), (0x020,0x020, 0, 1), (0x021,0x023, 0, 2), (0x024,0x024, 0, 3),
(0x025,0x027, 0, 2), (0x028,0x028, 0, 4), (0x029,0x029, 0, 5), (0x02a,0x02a, 0, 2),
(0x02b,0x02b, 0, 6), (0x02c,0x02c, 0, 2), (0x02d,0x02d, 0, 7), (0x02e,0x02f, 0, 2),
(0x030,0x039, 0, 8), (0x03a,0x03b, 0, 2), (0x03c,0x03e, 0, 6), (0x03f,0x040, 0, 2),
(0x041,0x05a, 1,15), (0x05b,0x05b, 0, 4), (0x05c,0x05c, 0, 2), (0x05d,0x05d, 0, 5),
(0x05e,0x05e, 0, 9), (0x05f,0x05f, 0,10), (0x060,0x060, 0, 9), (0x061,0x07a, 1,15),
(0x07b,0x07b, 0, 4), (0x07c,0x07c, 0, 6), (0x07d,0x07d, 0, 5), (0x07e,0x07e, 0, 6),
(0x07f,0x09f, 0, 0), (0x0a0,0x0a0, 0, 1), (0x0a1,0x0a1, 0, 2), (0x0a2,0x0a5, 0, 3),
(0x0a6,0x0a6, 0,11), (0x0a7,0x0a7, 0, 2), (0x0a8,0x0a8, 0, 9), (0x0a9,0x0a9, 0,11),
(0x0aa,0x0aa, 1,19), (0x0ab,0x0ab, 0,12), (0x0ac,0x0ac, 0, 6), (0x0ad,0x0ad, 0,13),
(0x0ae,0x0ae, 0,11), (0x0af,0x0af, 0, 9), (0x0b0,0x0b0, 0,11), (0x0b1,0x0b1, 0, 6),
(0x0b2,0x0b3, 0,14), (0x0b4,0x0b4, 0, 9), (0x0b5,0x0b5, 0,15), (0x0b6,0x0b7, 0, 2),
(0x0b8,0x0b8, 0, 9), (0x0b9,0x0b9, 0,14), (0x0ba,0x0ba, 1,19), (0x0bb,0x0bb, 0,16),
(0x0bc,0x0be, 0,14), (0x0bf,0x0bf, 0, 2), (0x0c0,0x0d6, 1,15), (0x0d7,0x0d7, 0, 6),
(0x0d8,0x0f6, 1,15), (0x0f7,0x0f7, 0, 6), (0x0f8,0x1ba, 1,15), (0x1bb,0x1bb, 1,19),
(0x1bc,0x1bf, 1,15), (0x1c0,0x1c3, 1,19), (0x1c4,0x293, 1,15), (0x294,0x294, 1,19),
(0x295,0x2af, 1,15), (0x2b0,0x2b8, 1,17), (0x2b9,0x2c1, 0,17), (0x2c2,0x2c5, 0, 9),
(0x2c6,0x2d1, 0,17), (0x2d2,0x2df, 0, 9), (0x2e0,0x2e4, 1,17), (0x2e5,0x2e9, 0, 9),
(0x2ea,0x2eb,34, 9), (0x2ec,0x2ec, 0,17), (0x2ed,0x2ed, 0, 9), (0x2ee,0x2ee, 0,17),
(0x2ef,0x2ff, 0, 9), (0x300,0x36f,40,23), (0x370,0x373, 2,15), (0x374,0x374, 0,17),
(0x375,0x375, 2, 9), (0x376,0x377, 2,15), (0x37a,0x37a, 2,17), (0x37b,0x37d, 2,15),
(0x37e,0x37e, 0, 2), (0x384,0x384, 2, 9), (0x385,0x385, 0, 9), (0x386,0x386, 2,15),
(0x387,0x387, 0, 2), (0x388,0x38a, 2,15), (0x38c,0x38c, 2,15), (0x38e,0x3a1, 2,15),
(0x3a3,0x3e1, 2,15), (0x3e2,0x3ef,54,15), (0x3f0,0x3f5, 2,15), (0x3f6,0x3f6, 2, 6),
(0x3f7,0x3ff, 2,15), (0x400,0x481, 3,15), (0x482,0x482, 3,11), (0x483,0x484, 3,23),
####### 0x0400...
(0x485,0x486,40,23), (0x487,0x487, 3,23), (0x488,0x489, 3,24), (0x48a,0x527, 3,15),
(0x531,0x556, 4,15), (0x559,0x559, 4,17), (0x55a,0x55f, 4, 2), (0x561,0x587, 4,15),
(0x589,0x589, 0, 2), (0x58a,0x58a, 4, 7), (0x58f,0x58f, 4, 3), (0x591,0x5bd, 5,23),
(0x5be,0x5be, 5, 7), (0x5bf,0x5bf, 5,23), (0x5c0,0x5c0, 5, 2), (0x5c1,0x5c2, 5,23),
(0x5c3,0x5c3, 5, 2), (0x5c4,0x5c5, 5,23), (0x5c6,0x5c6, 5, 2), (0x5c7,0x5c7, 5,23),
(0x5d0,0x5ea, 5,19), (0x5f0,0x5f2, 5,19), (0x5f3,0x5f4, 5, 2), (0x600,0x604, 6,13),
(0x606,0x608, 6, 6), (0x609,0x60a, 6, 2), (0x60b,0x60b, 6, 3), (0x60c,0x60c, 0, 2),
(0x60d,0x60d, 6, 2), (0x60e,0x60f, 6,11), (0x610,0x61a, 6,23), (0x61b,0x61b, 0, 2),
(0x61e,0x61e, 6, 2), (0x61f,0x61f, 0, 2), (0x620,0x63f, 6,19), (0x640,0x640, 0,17),
(0x641,0x64a, 6,19), (0x64b,0x655,40,23), (0x656,0x65e, 6,23),
(0x65f,0x65f,40,23), (0x660,0x669, 0, 8), (0x66a,0x66d, 6, 2), (0x66e,0x66f, 6,19),
(0x670,0x670,40,23), (0x671,0x6d3, 6,19), (0x6d4,0x6d4, 6, 2), (0x6d5,0x6d5, 6,19),
(0x6d6,0x6dc, 6,23), (0x6dd,0x6dd, 0,13), (0x6de,0x6de, 6,11), (0x6df,0x6e4, 6,23),
(0x6e5,0x6e6, 6,17), (0x6e7,0x6e8, 6,23), (0x6e9,0x6e9, 6,11), (0x6ea,0x6ed, 6,23),
(0x6ee,0x6ef, 6,19), (0x6f0,0x6f9, 6, 8), (0x6fa,0x6fc, 6,19), (0x6fd,0x6fe, 6,11),
(0x6ff,0x6ff, 6,19), (0x700,0x70d, 7, 2), (0x70f,0x70f, 7,13), (0x710,0x710, 7,19),
(0x711,0x711, 7,23), (0x712,0x72f, 7,19), (0x730,0x74a, 7,23), (0x74d,0x74f, 7,19),
(0x750,0x77f, 6,19), (0x780,0x7a5, 8,19), (0x7a6,0x7b0, 8,23), (0x7b1,0x7b1, 8,19),
(0x7c0,0x7c9,65, 8), (0x7ca,0x7ea,65,19), (0x7eb,0x7f3,65,23),
(0x7f4,0x7f5,65,17), (0x7f6,0x7f6,65,11), (0x7f7,0x7f9,65, 2),
(0x7fa,0x7fa,65,17), (0x800,0x815,81,19), (0x816,0x819,81,23),
####### 0x0800...
(0x81a,0x81a,81,17), (0x81b,0x823,81,23), (0x824,0x824,81,17),
(0x825,0x827,81,23), (0x828,0x828,81,17), (0x829,0x82d,81,23),
(0x830,0x83e,81, 2), (0x840,0x858,94,19), (0x859,0x85b,94,23),
(0x85e,0x85e,94, 2), (0x8a0,0x8a0, 6,19), (0x8a2,0x8ac, 6,19), (0x8e4,0x8fe, 6,23),
(0x900,0x902, 9,23), (0x903,0x903, 9,18), (0x904,0x939, 9,19), (0x93a,0x93a, 9,23),
(0x93b,0x93b, 9,18), (0x93c,0x93c, 9,23), (0x93d,0x93d, 9,19), (0x93e,0x940, 9,18),
(0x941,0x948, 9,23), (0x949,0x94c, 9,18), (0x94d,0x94d, 9,23), (0x94e,0x94f, 9,18),
(0x950,0x950, 9,19), (0x951,0x952,40,23), (0x953,0x957, 9,23), (0x958,0x961, 9,19),
(0x962,0x963, 9,23), (0x964,0x965, 0, 2), (0x966,0x96f, 9, 8), (0x970,0x970, 9, 2),
(0x971,0x971, 9,17), (0x972,0x977, 9,19), (0x979,0x97f, 9,19), (0x981,0x981,10,23),
(0x982,0x983,10,18), (0x985,0x98c,10,19), (0x98f,0x990,10,19),
(0x993,0x9a8,10,19), (0x9aa,0x9b0,10,19), (0x9b2,0x9b2,10,19),
(0x9b6,0x9b9,10,19), (0x9bc,0x9bc,10,23), (0x9bd,0x9bd,10,19),
(0x9be,0x9c0,10,18), (0x9c1,0x9c4,10,23), (0x9c7,0x9c8,10,18),
(0x9cb,0x9cc,10,18), (0x9cd,0x9cd,10,23), (0x9ce,0x9ce,10,19),
(0x9d7,0x9d7,10,18), (0x9dc,0x9dd,10,19), (0x9df,0x9e1,10,19),
(0x9e2,0x9e3,10,23), (0x9e6,0x9ef,10, 8), (0x9f0,0x9f1,10,19),
(0x9f2,0x9f3,10, 3), (0x9f4,0x9f9,10,14), (0x9fa,0x9fa,10,11),
(0x9fb,0x9fb,10, 3), (0xa01,0xa02,11,23), (0xa03,0xa03,11,18),
(0xa05,0xa0a,11,19), (0xa0f,0xa10,11,19), (0xa13,0xa28,11,19),
(0xa2a,0xa30,11,19), (0xa32,0xa33,11,19), (0xa35,0xa36,11,19),
(0xa38,0xa39,11,19), (0xa3c,0xa3c,11,23), (0xa3e,0xa40,11,18),
(0xa41,0xa42,11,23), (0xa47,0xa48,11,23), (0xa4b,0xa4d,11,23),
(0xa51,0xa51,11,23), (0xa59,0xa5c,11,19), (0xa5e,0xa5e,11,19),
(0xa66,0xa6f,11, 8), (0xa70,0xa71,11,23), (0xa72,0xa74,11,19),
(0xa75,0xa75,11,23), (0xa81,0xa82,12,23), (0xa83,0xa83,12,18),
(0xa85,0xa8d,12,19), (0xa8f,0xa91,12,19), (0xa93,0xaa8,12,19),
(0xaaa,0xab0,12,19), (0xab2,0xab3,12,19), (0xab5,0xab9,12,19),
(0xabc,0xabc,12,23), (0xabd,0xabd,12,19), (0xabe,0xac0,12,18),
(0xac1,0xac5,12,23), (0xac7,0xac8,12,23), (0xac9,0xac9,12,18),
(0xacb,0xacc,12,18), (0xacd,0xacd,12,23), (0xad0,0xad0,12,19),
(0xae0,0xae1,12,19), (0xae2,0xae3,12,23), (0xae6,0xaef,12, 8),
(0xaf0,0xaf0,12, 2), (0xaf1,0xaf1,12, 3), (0xb01,0xb01,13,23),
(0xb02,0xb03,13,18), (0xb05,0xb0c,13,19), (0xb0f,0xb10,13,19),
(0xb13,0xb28,13,19), (0xb2a,0xb30,13,19), (0xb32,0xb33,13,19),
(0xb35,0xb39,13,19), (0xb3c,0xb3c,13,23), (0xb3d,0xb3d,13,19),
(0xb3e,0xb3e,13,18), (0xb3f,0xb3f,13,23), (0xb40,0xb40,13,18),
(0xb41,0xb44,13,23), (0xb47,0xb48,13,18), (0xb4b,0xb4c,13,18),
(0xb4d,0xb4d,13,23), (0xb56,0xb56,13,23), (0xb57,0xb57,13,18),
(0xb5c,0xb5d,13,19), (0xb5f,0xb61,13,19), (0xb62,0xb63,13,23),
(0xb66,0xb6f,13, 8), (0xb70,0xb70,13,11), (0xb71,0xb71,13,19),
(0xb72,0xb77,13,14), (0xb82,0xb82,14,23), (0xb83,0xb83,14,19),
(0xb85,0xb8a,14,19), (0xb8e,0xb90,14,19), (0xb92,0xb95,14,19),
(0xb99,0xb9a,14,19), (0xb9c,0xb9c,14,19), (0xb9e,0xb9f,14,19),
(0xba3,0xba4,14,19), (0xba8,0xbaa,14,19), (0xbae,0xbb9,14,19),
(0xbbe,0xbbf,14,18), (0xbc0,0xbc0,14,23), (0xbc1,0xbc2,14,18),
(0xbc6,0xbc8,14,18), (0xbca,0xbcc,14,18), (0xbcd,0xbcd,14,23),
(0xbd0,0xbd0,14,19), (0xbd7,0xbd7,14,18), (0xbe6,0xbef,14, 8),
(0xbf0,0xbf2,14,14), (0xbf3,0xbf8,14,11), (0xbf9,0xbf9,14, 3),
(0xbfa,0xbfa,14,11), (0xc01,0xc03,15,18), (0xc05,0xc0c,15,19),
####### 0x0C00...
(0xc0e,0xc10,15,19), (0xc12,0xc28,15,19), (0xc2a,0xc33,15,19),
(0xc35,0xc39,15,19), (0xc3d,0xc3d,15,19), (0xc3e,0xc40,15,23),
(0xc41,0xc44,15,18), (0xc46,0xc48,15,23), (0xc4a,0xc4d,15,23),
(0xc55,0xc56,15,23), (0xc58,0xc59,15,19), (0xc60,0xc61,15,19),
(0xc62,0xc63,15,23), (0xc66,0xc6f,15, 8), (0xc78,0xc7e,15,14),
(0xc7f,0xc7f,15,11), (0xc82,0xc83,16,18), (0xc85,0xc8c,16,19),
(0xc8e,0xc90,16,19), (0xc92,0xca8,16,19), (0xcaa,0xcb3,16,19),
(0xcb5,0xcb9,16,19), (0xcbc,0xcbc,16,23), (0xcbd,0xcbd,16,19),
(0xcbe,0xcbe,16,18), (0xcbf,0xcbf,16,23), (0xcc0,0xcc4,16,18),
(0xcc6,0xcc6,16,23), (0xcc7,0xcc8,16,18), (0xcca,0xccb,16,18),
(0xccc,0xccd,16,23), (0xcd5,0xcd6,16,18), (0xcde,0xcde,16,19),
(0xce0,0xce1,16,19), (0xce2,0xce3,16,23), (0xce6,0xcef,16, 8),
(0xcf1,0xcf2,16,19), (0xd02,0xd03,17,18), (0xd05,0xd0c,17,19),
(0xd0e,0xd10,17,19), (0xd12,0xd3a,17,19), (0xd3d,0xd3d,17,19),
(0xd3e,0xd40,17,18), (0xd41,0xd44,17,23), (0xd46,0xd48,17,18),
(0xd4a,0xd4c,17,18), (0xd4d,0xd4d,17,23), (0xd4e,0xd4e,17,19),
(0xd57,0xd57,17,18), (0xd60,0xd61,17,19), (0xd62,0xd63,17,23),
(0xd66,0xd6f,17, 8), (0xd70,0xd75,17,14), (0xd79,0xd79,17,11),
(0xd7a,0xd7f,17,19), (0xd82,0xd83,18,18), (0xd85,0xd96,18,19),
(0xd9a,0xdb1,18,19), (0xdb3,0xdbb,18,19), (0xdbd,0xdbd,18,19),
(0xdc0,0xdc6,18,19), (0xdca,0xdca,18,23), (0xdcf,0xdd1,18,18),
(0xdd2,0xdd4,18,23), (0xdd6,0xdd6,18,23), (0xdd8,0xddf,18,18),
(0xdf2,0xdf3,18,18), (0xdf4,0xdf4,18, 2), (0xe01,0xe30,19,19),
(0xe31,0xe31,19,23), (0xe32,0xe33,19,19), (0xe34,0xe3a,19,23),
(0xe3f,0xe3f, 0, 3), (0xe40,0xe45,19,19), (0xe46,0xe46,19,17),
(0xe47,0xe4e,19,23), (0xe4f,0xe4f,19, 2), (0xe50,0xe59,19, 8), (0xe5a,0xe5b,19, 2),
(0xe81,0xe82,20,19), (0xe84,0xe84,20,19), (0xe87,0xe88,20,19),
(0xe8a,0xe8a,20,19), (0xe8d,0xe8d,20,19), (0xe94,0xe97,20,19),
(0xe99,0xe9f,20,19), (0xea1,0xea3,20,19), (0xea5,0xea5,20,19),
(0xea7,0xea7,20,19), (0xeaa,0xeab,20,19), (0xead,0xeb0,20,19),
(0xeb1,0xeb1,20,23), (0xeb2,0xeb3,20,19), (0xeb4,0xeb9,20,23),
(0xebb,0xebc,20,23), (0xebd,0xebd,20,19), (0xec0,0xec4,20,19),
(0xec6,0xec6,20,17), (0xec8,0xecd,20,23), (0xed0,0xed9,20, 8),
(0xedc,0xedf,20,19), (0xf00,0xf00,21,19), (0xf01,0xf03,21,11),
(0xf04,0xf12,21, 2), (0xf13,0xf13,21,11), (0xf14,0xf14,21, 2),
(0xf15,0xf17,21,11), (0xf18,0xf19,21,23), (0xf1a,0xf1f,21,11),
(0xf20,0xf29,21, 8), (0xf2a,0xf33,21,14), (0xf34,0xf34,21,11),
(0xf35,0xf35,21,23), (0xf36,0xf36,21,11), (0xf37,0xf37,21,23),
(0xf38,0xf38,21,11), (0xf39,0xf39,21,23), (0xf3a,0xf3a,21, 4),
(0xf3b,0xf3b,21, 5), (0xf3c,0xf3c,21, 4), (0xf3d,0xf3d,21, 5), (0xf3e,0xf3f,21,18),
(0xf40,0xf47,21,19), (0xf49,0xf6c,21,19), (0xf71,0xf7e,21,23),
(0xf7f,0xf7f,21,18), (0xf80,0xf84,21,23), (0xf85,0xf85,21, 2),
(0xf86,0xf87,21,23), (0xf88,0xf8c,21,19), (0xf8d,0xf97,21,23),
(0xf99,0xfbc,21,23), (0xfbe,0xfc5,21,11), (0xfc6,0xfc6,21,23),
(0xfc7,0xfcc,21,11), (0xfce,0xfcf,21,11), (0xfd0,0xfd4,21, 2),
(0xfd5,0xfd8, 0,11), (0xfd9,0xfda,21, 2), (0x1000,0x102a,22,19),
####### 0x100...
(0x102b,0x102c,22,18), (0x102d,0x1030,22,23), (0x1031,0x1031,22,18),
(0x1032,0x1037,22,23), (0x1038,0x1038,22,18), (0x1039,0x103a,22,23),
(0x103b,0x103c,22,18), (0x103d,0x103e,22,23), (0x103f,0x103f,22,19),
(0x1040,0x1049,22, 8), (0x104a,0x104f,22, 2), (0x1050,0x1055,22,19),
(0x1056,0x1057,22,18), (0x1058,0x1059,22,23), (0x105a,0x105d,22,19),
(0x105e,0x1060,22,23), (0x1061,0x1061,22,19), (0x1062,0x1064,22,18),
(0x1065,0x1066,22,19), (0x1067,0x106d,22,18), (0x106e,0x1070,22,19),
(0x1071,0x1074,22,23), (0x1075,0x1081,22,19), (0x1082,0x1082,22,23),
(0x1083,0x1084,22,18), (0x1085,0x1086,22,23), (0x1087,0x108c,22,18),
(0x108d,0x108d,22,23), (0x108e,0x108e,22,19), (0x108f,0x108f,22,18),
(0x1090,0x1099,22, 8), (0x109a,0x109c,22,18), (0x109d,0x109d,22,23),
(0x109e,0x109f,22,11), (0x10a0,0x10c5,23,15), (0x10c7,0x10c7,23,15),
(0x10cd,0x10cd,23,15), (0x10d0,0x10fa,23,19), (0x10fb,0x10fb, 0, 2),
(0x10fc,0x10fc,23,17), (0x10fd,0x10ff,23,19), (0x1100,0x11ff,24,19),
(0x1200,0x1248,25,19), (0x124a,0x124d,25,19), (0x1250,0x1256,25,19),
(0x1258,0x1258,25,19), (0x125a,0x125d,25,19), (0x1260,0x1288,25,19),
(0x128a,0x128d,25,19), (0x1290,0x12b0,25,19), (0x12b2,0x12b5,25,19),
(0x12b8,0x12be,25,19), (0x12c0,0x12c0,25,19), (0x12c2,0x12c5,25,19),
(0x12c8,0x12d6,25,19), (0x12d8,0x1310,25,19), (0x1312,0x1315,25,19),
(0x1318,0x135a,25,19), (0x135d,0x135f,25,23), (0x1360,0x1368,25, 2),
(0x1369,0x137c,25,14), (0x1380,0x138f,25,19), (0x1390,0x1399,25,11),
(0x13a0,0x13f4,26,19), (0x1400,0x1400,27, 7), (0x1401,0x166c,27,19),
(0x166d,0x166e,27, 2), (0x166f,0x167f,27,19), (0x1680,0x1680,28, 1),
(0x1681,0x169a,28,19), (0x169b,0x169b,28, 4), (0x169c,0x169c,28, 5),
(0x16a0,0x16ea,29,19), (0x16eb,0x16ed, 0, 2), (0x16ee,0x16f0,29,22),
(0x1700,0x170c,41,19), (0x170e,0x1711,41,19), (0x1712,0x1714,41,23),
(0x1720,0x1731,42,19), (0x1732,0x1734,42,23), (0x1735,0x1736, 0, 2),
(0x1740,0x1751,43,19), (0x1752,0x1753,43,23), (0x1760,0x176c,44,19),
(0x176e,0x1770,44,19), (0x1772,0x1773,44,23), (0x1780,0x17b3,30,19),
(0x17b4,0x17b5,30,23), (0x17b6,0x17b6,30,18), (0x17b7,0x17bd,30,23),
(0x17be,0x17c5,30,18), (0x17c6,0x17c6,30,23), (0x17c7,0x17c8,30,18),
(0x17c9,0x17d3,30,23), (0x17d4,0x17d6,30, 2), (0x17d7,0x17d7,30,17),
(0x17d8,0x17da,30, 2), (0x17db,0x17db,30, 3), (0x17dc,0x17dc,30,19),
(0x17dd,0x17dd,30,23), (0x17e0,0x17e9,30, 8), (0x17f0,0x17f9,30,14),
(0x1800,0x1801,31, 2), (0x1802,0x1803, 0, 2), (0x1804,0x1804,31, 2),
(0x1805,0x1805, 0, 2), (0x1806,0x1806,31, 7), (0x1807,0x180a,31, 2),
(0x180b,0x180d,31,23), (0x180e,0x180e,31, 1), (0x1810,0x1819,31, 8),
(0x1820,0x1842,31,19), (0x1843,0x1843,31,17), (0x1844,0x1877,31,19),
(0x1880,0x18a8,31,19), (0x18a9,0x18a9,31,23), (0x18aa,0x18aa,31,19),
(0x18b0,0x18f5,27,19), (0x1900,0x191c,45,19), (0x1920,0x1922,45,23),
(0x1923,0x1926,45,18), (0x1927,0x1928,45,23), (0x1929,0x192b,45,18),
(0x1930,0x1931,45,18), (0x1932,0x1932,45,23), (0x1933,0x1938,45,18),
(0x1939,0x193b,45,23), (0x1940,0x1940,45,11), (0x1944,0x1945,45, 2),
(0x1946,0x194f,45, 8), (0x1950,0x196d,46,19), (0x1970,0x1974,46,19),
(0x1980,0x19ab,55,19), (0x19b0,0x19c0,55,18), (0x19c1,0x19c7,55,19),
(0x19c8,0x19c9,55,18), (0x19d0,0x19d9,55, 8), (0x19da,0x19da,55,14),
(0x19de,0x19df,55,11), (0x19e0,0x19ff,30,11), (0x1a00,0x1a16,53,19),
(0x1a17,0x1a18,53,23), (0x1a19,0x1a1b,53,18), (0x1a1e,0x1a1f,53, 2),
(0x1a20,0x1a54,77,19), (0x1a55,0x1a55,77,18), (0x1a56,0x1a56,77,23),
(0x1a57,0x1a57,77,18), (0x1a58,0x1a5e,77,23), (0x1a60,0x1a60,77,23),
(0x1a61,0x1a61,77,18), (0x1a62,0x1a62,77,23), (0x1a63,0x1a64,77,18),
(0x1a65,0x1a6c,77,23), (0x1a6d,0x1a72,77,18), (0x1a73,0x1a7c,77,23),
(0x1a7f,0x1a7f,77,23), (0x1a80,0x1a89,77, 8), (0x1a90,0x1a99,77, 8),
(0x1aa0,0x1aa6,77, 2), (0x1aa7,0x1aa7,77,17), (0x1aa8,0x1aad,77, 2),
(0x1b00,0x1b03,61,23), (0x1b04,0x1b04,61,18), (0x1b05,0x1b33,61,19),
(0x1b34,0x1b34,61,23), (0x1b35,0x1b35,61,18), (0x1b36,0x1b3a,61,23),
(0x1b3b,0x1b3b,61,18), (0x1b3c,0x1b3c,61,23), (0x1b3d,0x1b41,61,18),
(0x1b42,0x1b42,61,23), (0x1b43,0x1b44,61,18), (0x1b45,0x1b4b,61,19),
(0x1b50,0x1b59,61, 8), (0x1b5a,0x1b60,61, 2), (0x1b61,0x1b6a,61,11),
(0x1b6b,0x1b73,61,23), (0x1b74,0x1b7c,61,11), (0x1b80,0x1b81,66,23),
(0x1b82,0x1b82,66,18), (0x1b83,0x1ba0,66,19), (0x1ba1,0x1ba1,66,18),
(0x1ba2,0x1ba5,66,23), (0x1ba6,0x1ba7,66,18), (0x1ba8,0x1ba9,66,23),
(0x1baa,0x1baa,66,18), (0x1bab,0x1bab,66,23), (0x1bac,0x1bad,66,18),
(0x1bae,0x1baf,66,19), (0x1bb0,0x1bb9,66, 8), (0x1bba,0x1bbf,66,19),
(0x1bc0,0x1be5,92,19), (0x1be6,0x1be6,92,23), (0x1be7,0x1be7,92,18),
(0x1be8,0x1be9,92,23), (0x1bea,0x1bec,92,18), (0x1bed,0x1bed,92,23),
(0x1bee,0x1bee,92,18), (0x1bef,0x1bf1,92,23), (0x1bf2,0x1bf3,92,18),
(0x1bfc,0x1bff,92, 2), (0x1c00,0x1c23,67,19), (0x1c24,0x1c2b,67,18),
(0x1c2c,0x1c33,67,23), (0x1c34,0x1c35,67,18), (0x1c36,0x1c37,67,23),
(0x1c3b,0x1c3f,67, 2), (0x1c40,0x1c49,67, 8), (0x1c4d,0x1c4f,67,19),
(0x1c50,0x1c59,68, 8), (0x1c5a,0x1c77,68,19), (0x1c78,0x1c7d,68,17),
(0x1c7e,0x1c7f,68, 2), (0x1cc0,0x1cc7,66, 2), (0x1cd0,0x1cd2,40,23),
(0x1cd3,0x1cd3, 0, 2), (0x1cd4,0x1ce0,40,23), (0x1ce1,0x1ce1, 0,18),
(0x1ce2,0x1ce8,40,23), (0x1ce9,0x1cec, 0,19), (0x1ced,0x1ced,40,23),
(0x1cee,0x1cf1, 0,19), (0x1cf2,0x1cf3, 0,18), (0x1cf4,0x1cf4,40,23),
(0x1cf5,0x1cf6, 0,19), (0x1d00,0x1d25, 1,15), (0x1d26,0x1d2a, 2,15),
(0x1d2b,0x1d2b, 3,15), (0x1d2c,0x1d5c, 1,17), (0x1d5d,0x1d61, 2,17),
(0x1d62,0x1d65, 1,17), (0x1d66,0x1d6a, 2,17), (0x1d6b,0x1d77, 1,15),
(0x1d78,0x1d78, 3,17), (0x1d79,0x1d9a, 1,15), (0x1d9b,0x1dbe, 1,17),
(0x1dbf,0x1dbf, 2,17), (0x1dc0,0x1de6,40,23), (0x1dfc,0x1dff,40,23),
(0x1e00,0x1eff, 1,15), (0x1f00,0x1f15, 2,15), (0x1f18,0x1f1d, 2,15),
(0x1f20,0x1f45, 2,15), (0x1f48,0x1f4d, 2,15), (0x1f50,0x1f57, 2,15),
(0x1f59,0x1f59, 2,15), (0x1f5b,0x1f5b, 2,15), (0x1f5d,0x1f5d, 2,15),
(0x1f5f,0x1f7d, 2,15), (0x1f80,0x1fb4, 2,15), (0x1fb6,0x1fbc, 2,15),
(0x1fbd,0x1fbd, 2, 9), (0x1fbe,0x1fbe, 2,15), (0x1fbf,0x1fc1, 2, 9),
(0x1fc2,0x1fc4, 2,15), (0x1fc6,0x1fcc, 2,15), (0x1fcd,0x1fcf, 2, 9),
(0x1fd0,0x1fd3, 2,15), (0x1fd6,0x1fdb, 2,15), (0x1fdd,0x1fdf, 2, 9),
(0x1fe0,0x1fec, 2,15), (0x1fed,0x1fef, 2, 9), (0x1ff2,0x1ff4, 2,15),
(0x1ff6,0x1ffc, 2,15), (0x1ffd,0x1ffe, 2, 9), (0x2000,0x200a, 0, 1),
####### 0x2000...
(0x200b,0x200b, 0,13), (0x200c,0x200d,40,13), (0x200e,0x200f, 0,13),
(0x2010,0x2015, 0, 7), (0x2016,0x2017, 0, 2), (0x2018,0x2018, 0,12),
(0x2019,0x2019, 0,16), (0x201a,0x201a, 0, 4), (0x201b,0x201c, 0,12),
(0x201d,0x201d, 0,16), (0x201e,0x201e, 0, 4), (0x201f,0x201f, 0,12),
(0x2020,0x2027, 0, 2), (0x2028,0x2028, 0,20), (0x2029,0x2029, 0,21),
(0x202a,0x202e, 0,13), (0x202f,0x202f, 0, 1), (0x2030,0x2038, 0, 2),
(0x2039,0x2039, 0,12), (0x203a,0x203a, 0,16), (0x203b,0x203e, 0, 2),
(0x203f,0x2040, 0,10), (0x2041,0x2043, 0, 2), (0x2044,0x2044, 0, 6),
(0x2045,0x2045, 0, 4), (0x2046,0x2046, 0, 5), (0x2047,0x2051, 0, 2),
(0x2052,0x2052, 0, 6), (0x2053,0x2053, 0, 2), (0x2054,0x2054, 0,10),
(0x2055,0x205e, 0, 2), (0x205f,0x205f, 0, 1), (0x2060,0x2064, 0,13),
(0x206a,0x206f, 0,13), (0x2070,0x2070, 0,14), (0x2071,0x2071, 1,17),
(0x2074,0x2079, 0,14), (0x207a,0x207c, 0, 6), (0x207d,0x207d, 0, 4),
(0x207e,0x207e, 0, 5), (0x207f,0x207f, 1,17), (0x2080,0x2089, 0,14),
(0x208a,0x208c, 0, 6), (0x208d,0x208d, 0, 4), (0x208e,0x208e, 0, 5),
(0x2090,0x209c, 1,17), (0x20a0,0x20b9, 0, 3), (0x20d0,0x20dc,40,23),
(0x20dd,0x20e0,40,24), (0x20e1,0x20e1,40,23), (0x20e2,0x20e4,40,24),
(0x20e5,0x20f0,40,23), (0x2100,0x2101, 0,11), (0x2102,0x2102, 0,15),
(0x2103,0x2106, 0,11), (0x2107,0x2107, 0,15), (0x2108,0x2109, 0,11),
(0x210a,0x2113, 0,15), (0x2114,0x2114, 0,11), (0x2115,0x2115, 0,15),
(0x2116,0x2117, 0,11), (0x2118,0x2118, 0, 6), (0x2119,0x211d, 0,15),
(0x211e,0x2123, 0,11), (0x2124,0x2124, 0,15), (0x2125,0x2125, 0,11),
(0x2126,0x2126, 2,15), (0x2127,0x2127, 0,11), (0x2128,0x2128, 0,15),
(0x2129,0x2129, 0,11), (0x212a,0x212b, 1,15), (0x212c,0x212d, 0,15),
(0x212e,0x212e, 0,11), (0x212f,0x2131, 0,15), (0x2132,0x2132, 1,15),
(0x2133,0x2134, 0,15), (0x2135,0x2138, 0,19), (0x2139,0x2139, 0,15),
(0x213a,0x213b, 0,11), (0x213c,0x213f, 0,15), (0x2140,0x2144, 0, 6),
(0x2145,0x2149, 0,15), (0x214a,0x214a, 0,11), (0x214b,0x214b, 0, 6),
(0x214c,0x214d, 0,11), (0x214e,0x214e, 1,15), (0x214f,0x214f, 0,11),
(0x2150,0x215f, 0,14), (0x2160,0x2182, 1,22), (0x2183,0x2184, 1,15),
(0x2185,0x2188, 1,22), (0x2189,0x2189, 0,14), (0x2190,0x2194, 0, 6),
(0x2195,0x2199, 0,11), (0x219a,0x219b, 0, 6), (0x219c,0x219f, 0,11),
(0x21a0,0x21a0, 0, 6), (0x21a1,0x21a2, 0,11), (0x21a3,0x21a3, 0, 6),
(0x21a4,0x21a5, 0,11), (0x21a6,0x21a6, 0, 6), (0x21a7,0x21ad, 0,11),
(0x21ae,0x21ae, 0, 6), (0x21af,0x21cd, 0,11), (0x21ce,0x21cf, 0, 6),
(0x21d0,0x21d1, 0,11), (0x21d2,0x21d2, 0, 6), (0x21d3,0x21d3, 0,11),
(0x21d4,0x21d4, 0, 6), (0x21d5,0x21f3, 0,11), (0x21f4,0x22ff, 0, 6),
(0x2300,0x2307, 0,11), (0x2308,0x230b, 0, 6), (0x230c,0x231f, 0,11),
(0x2320,0x2321, 0, 6), (0x2322,0x2328, 0,11), (0x2329,0x2329, 0, 4),
(0x232a,0x232a, 0, 5), (0x232b,0x237b, 0,11), (0x237c,0x237c, 0, 6),
(0x237d,0x239a, 0,11), (0x239b,0x23b3, 0, 6), (0x23b4,0x23db, 0,11),
(0x23dc,0x23e1, 0, 6), (0x23e2,0x23f3, 0,11), (0x2400,0x2426, 0,11),
(0x2440,0x244a, 0,11), (0x2460,0x249b, 0,14), (0x249c,0x24e9, 0,11),
(0x24ea,0x24ff, 0,14), (0x2500,0x25b6, 0,11), (0x25b7,0x25b7, 0, 6),
(0x25b8,0x25c0, 0,11), (0x25c1,0x25c1, 0, 6), (0x25c2,0x25f7, 0,11),
(0x25f8,0x25ff, 0, 6), (0x2600,0x266e, 0,11), (0x266f,0x266f, 0, 6),
(0x2670,0x26ff, 0,11), (0x2701,0x2767, 0,11), (0x2768,0x2768, 0, 4),
(0x2769,0x2769, 0, 5), (0x276a,0x276a, 0, 4), (0x276b,0x276b, 0, 5),
(0x276c,0x276c, 0, 4), (0x276d,0x276d, 0, 5), (0x276e,0x276e, 0, 4),
(0x276f,0x276f, 0, 5), (0x2770,0x2770, 0, 4), (0x2771,0x2771, 0, 5),
(0x2772,0x2772, 0, 4), (0x2773,0x2773, 0, 5), (0x2774,0x2774, 0, 4),
(0x2775,0x2775, 0, 5), (0x2776,0x2793, 0,14), (0x2794,0x27bf, 0,11),
(0x27c0,0x27c4, 0, 6), (0x27c5,0x27c5, 0, 4), (0x27c6,0x27c6, 0, 5),
(0x27c7,0x27e5, 0, 6), (0x27e6,0x27e6, 0, 4), (0x27e7,0x27e7, 0, 5),
(0x27e8,0x27e8, 0, 4), (0x27e9,0x27e9, 0, 5), (0x27ea,0x27ea, 0, 4),
(0x27eb,0x27eb, 0, 5), (0x27ec,0x27ec, 0, 4), (0x27ed,0x27ed, 0, 5),
(0x27ee,0x27ee, 0, 4), (0x27ef,0x27ef, 0, 5), (0x27f0,0x27ff, 0, 6),
(0x2800,0x28ff,52,11), (0x2900,0x2982, 0, 6), (0x2983,0x2983, 0, 4),
(0x2984,0x2984, 0, 5), (0x2985,0x2985, 0, 4), (0x2986,0x2986, 0, 5),
(0x2987,0x2987, 0, 4), (0x2988,0x2988, 0, 5), (0x2989,0x2989, 0, 4),
(0x298a,0x298a, 0, 5), (0x298b,0x298b, 0, 4), (0x298c,0x298c, 0, 5),
(0x298d,0x298d, 0, 4), (0x298e,0x298e, 0, 5), (0x298f,0x298f, 0, 4),
(0x2990,0x2990, 0, 5), (0x2991,0x2991, 0, 4), (0x2992,0x2992, 0, 5),
(0x2993,0x2993, 0, 4), (0x2994,0x2994, 0, 5), (0x2995,0x2995, 0, 4),
(0x2996,0x2996, 0, 5), (0x2997,0x2997, 0, 4), (0x2998,0x2998, 0, 5),
(0x2999,0x29d7, 0, 6), (0x29d8,0x29d8, 0, 4), (0x29d9,0x29d9, 0, 5),
(0x29da,0x29da, 0, 4), (0x29db,0x29db, 0, 5), (0x29dc,0x29fb, 0, 6),
(0x29fc,0x29fc, 0, 4), (0x29fd,0x29fd, 0, 5), (0x29fe,0x2aff, 0, 6),
(0x2b00,0x2b2f, 0,11), (0x2b30,0x2b44, 0, 6), (0x2b45,0x2b46, 0,11),
(0x2b47,0x2b4c, 0, 6), (0x2b50,0x2b59, 0,11), (0x2c00,0x2c2e,56,15),
(0x2c30,0x2c5e,56,15), (0x2c60,0x2c7b, 1,15), (0x2c7c,0x2c7d, 1,17),
(0x2c7e,0x2c7f, 1,15), (0x2c80,0x2ce4,54,15), (0x2ce5,0x2cea,54,11),
(0x2ceb,0x2cee,54,15), (0x2cef,0x2cf1,54,23), (0x2cf2,0x2cf3,54,15),
(0x2cf9,0x2cfc,54, 2), (0x2cfd,0x2cfd,54,14), (0x2cfe,0x2cff,54, 2),
(0x2d00,0x2d25,23,15), (0x2d27,0x2d27,23,15), (0x2d2d,0x2d2d,23,15),
(0x2d30,0x2d67,57,19), (0x2d6f,0x2d6f,57,17), (0x2d70,0x2d70,57, 2),
(0x2d7f,0x2d7f,57,23), (0x2d80,0x2d96,25,19), (0x2da0,0x2da6,25,19),
(0x2da8,0x2dae,25,19), (0x2db0,0x2db6,25,19), (0x2db8,0x2dbe,25,19),
(0x2dc0,0x2dc6,25,19), (0x2dc8,0x2dce,25,19), (0x2dd0,0x2dd6,25,19),
(0x2dd8,0x2dde,25,19), (0x2de0,0x2dff, 3,23), (0x2e00,0x2e01, 0, 2),
(0x2e02,0x2e02, 0,12), (0x2e03,0x2e03, 0,16), (0x2e04,0x2e04, 0,12),
(0x2e05,0x2e05, 0,16), (0x2e06,0x2e08, 0, 2), (0x2e09,0x2e09, 0,12),
(0x2e0a,0x2e0a, 0,16), (0x2e0b,0x2e0b, 0, 2), (0x2e0c,0x2e0c, 0,12),
(0x2e0d,0x2e0d, 0,16), (0x2e0e,0x2e16, 0, 2), (0x2e17,0x2e17, 0, 7),
(0x2e18,0x2e19, 0, 2), (0x2e1a,0x2e1a, 0, 7), (0x2e1b,0x2e1b, 0, 2),
(0x2e1c,0x2e1c, 0,12), (0x2e1d,0x2e1d, 0,16), (0x2e1e,0x2e1f, 0, 2),
(0x2e20,0x2e20, 0,12), (0x2e21,0x2e21, 0,16), (0x2e22,0x2e22, 0, 4),
(0x2e23,0x2e23, 0, 5), (0x2e24,0x2e24, 0, 4), (0x2e25,0x2e25, 0, 5),
(0x2e26,0x2e26, 0, 4), (0x2e27,0x2e27, 0, 5), (0x2e28,0x2e28, 0, 4),
(0x2e29,0x2e29, 0, 5), (0x2e2a,0x2e2e, 0, 2), (0x2e2f,0x2e2f, 0,17),
(0x2e30,0x2e39, 0, 2), (0x2e3a,0x2e3b, 0, 7), (0x2e80,0x2e99,35,11),
(0x2e9b,0x2ef3,35,11), (0x2f00,0x2fd5,35,11), (0x2ff0,0x2ffb, 0,11),
####### 0x3000...
(0x3000,0x3000, 0, 1), (0x3001,0x3003, 0, 2), (0x3004,0x3004, 0,11),
(0x3005,0x3005,35,17), (0x3006,0x3006, 0,19), (0x3007,0x3007,35,22),
(0x3008,0x3008, 0, 4), (0x3009,0x3009, 0, 5), (0x300a,0x300a, 0, 4),
(0x300b,0x300b, 0, 5), (0x300c,0x300c, 0, 4), (0x300d,0x300d, 0, 5),
(0x300e,0x300e, 0, 4), (0x300f,0x300f, 0, 5), (0x3010,0x3010, 0, 4),
(0x3011,0x3011, 0, 5), (0x3012,0x3013, 0,11), (0x3014,0x3014, 0, 4),
(0x3015,0x3015, 0, 5), (0x3016,0x3016, 0, 4), (0x3017,0x3017, 0, 5),
(0x3018,0x3018, 0, 4), (0x3019,0x3019, 0, 5), (0x301a,0x301a, 0, 4),
(0x301b,0x301b, 0, 5), (0x301c,0x301c, 0, 7), (0x301d,0x301d, 0, 4),
(0x301e,0x301f, 0, 5), (0x3020,0x3020, 0,11), (0x3021,0x3029,35,22),
(0x302a,0x302d,40,23), (0x302e,0x302f,24,18), (0x3030,0x3030, 0, 7),
(0x3031,0x3035, 0,17), (0x3036,0x3037, 0,11), (0x3038,0x303a,35,22),
(0x303b,0x303b,35,17), (0x303c,0x303c, 0,19), (0x303d,0x303d, 0, 2),
(0x303e,0x303f, 0,11), (0x3041,0x3096,32,19), (0x3099,0x309a,40,23),
(0x309b,0x309c, 0, 9), (0x309d,0x309e,32,17), (0x309f,0x309f,32,19),
(0x30a0,0x30a0, 0, 7), (0x30a1,0x30fa,33,19), (0x30fb,0x30fb, 0, 2),
(0x30fc,0x30fc, 0,17), (0x30fd,0x30fe,33,17), (0x30ff,0x30ff,33,19),
(0x3105,0x312d,34,19), (0x3131,0x318e,24,19), (0x3190,0x3191, 0,11),
(0x3192,0x3195, 0,14), (0x3196,0x319f, 0,11), (0x31a0,0x31ba,34,19),
(0x31c0,0x31e3, 0,11), (0x31f0,0x31ff,33,19), (0x3200,0x321e,24,11),
(0x3220,0x3229, 0,14), (0x322a,0x3247, 0,11), (0x3248,0x324f, 0,14),
(0x3250,0x3250, 0,11), (0x3251,0x325f, 0,14), (0x3260,0x327e,24,11),
(0x327f,0x327f, 0,11), (0x3280,0x3289, 0,14), (0x328a,0x32b0, 0,11),
(0x32b1,0x32bf, 0,14), (0x32c0,0x32cf, 0,11), (0x32d0,0x32fe,33,11),
(0x3300,0x3357,33,11), (0x3358,0x33ff, 0,11), (0x3400,0x4db5,35,19),
(0x4dc0,0x4dff, 0,11), (0x4e00,0x9fcc,35,19), (0xa000,0xa014,36,19),
####### 0xA000...
(0xa015,0xa015,36,17), (0xa016,0xa48c,36,19), (0xa490,0xa4c6,36,11),
(0xa4d0,0xa4f7,82,19), (0xa4f8,0xa4fd,82,17), (0xa4fe,0xa4ff,82, 2),
(0xa500,0xa60b,69,19), (0xa60c,0xa60c,69,17), (0xa60d,0xa60f,69, 2),
(0xa610,0xa61f,69,19), (0xa620,0xa629,69, 8), (0xa62a,0xa62b,69,19),
(0xa640,0xa66d, 3,15), (0xa66e,0xa66e, 3,19), (0xa66f,0xa66f, 3,23),
(0xa670,0xa672, 3,24), (0xa673,0xa673, 3, 2), (0xa674,0xa67d, 3,23),
(0xa67e,0xa67e, 3, 2), (0xa67f,0xa67f, 3,17), (0xa680,0xa697, 3,15),
(0xa69f,0xa69f, 3,23), (0xa6a0,0xa6e5,83,19), (0xa6e6,0xa6ef,83,22),
(0xa6f0,0xa6f1,83,23), (0xa6f2,0xa6f7,83, 2), (0xa700,0xa716, 0, 9),
(0xa717,0xa71f, 0,17), (0xa720,0xa721, 0, 9), (0xa722,0xa76f, 1,15),
(0xa770,0xa770, 1,17), (0xa771,0xa787, 1,15), (0xa788,0xa788, 0,17),
(0xa789,0xa78a, 0, 9), (0xa78b,0xa78e, 1,15), (0xa790,0xa793, 1,15),
(0xa7a0,0xa7aa, 1,15), (0xa7f8,0xa7f9, 1,17), (0xa7fa,0xa7fa, 1,15),
(0xa7fb,0xa7ff, 1,19), (0xa800,0xa801,58,19), (0xa802,0xa802,58,23),
(0xa803,0xa805,58,19), (0xa806,0xa806,58,23), (0xa807,0xa80a,58,19),
(0xa80b,0xa80b,58,23), (0xa80c,0xa822,58,19), (0xa823,0xa824,58,18),
(0xa825,0xa826,58,23), (0xa827,0xa827,58,18), (0xa828,0xa82b,58,11),
(0xa830,0xa835, 0,14), (0xa836,0xa837, 0,11), (0xa838,0xa838, 0, 3),
(0xa839,0xa839, 0,11), (0xa840,0xa873,64,19), (0xa874,0xa877,64, 2),
(0xa880,0xa881,70,18), (0xa882,0xa8b3,70,19), (0xa8b4,0xa8c3,70,18),
(0xa8c4,0xa8c4,70,23), (0xa8ce,0xa8cf,70, 2), (0xa8d0,0xa8d9,70, 8),
(0xa8e0,0xa8f1, 9,23), (0xa8f2,0xa8f7, 9,19), (0xa8f8,0xa8fa, 9, 2),
(0xa8fb,0xa8fb, 9,19), (0xa900,0xa909,71, 8), (0xa90a,0xa925,71,19),
(0xa926,0xa92d,71,23), (0xa92e,0xa92f,71, 2), (0xa930,0xa946,72,19),
(0xa947,0xa951,72,23), (0xa952,0xa953,72,18), (0xa95f,0xa95f,72, 2),
(0xa960,0xa97c,24,19), (0xa980,0xa982,84,23), (0xa983,0xa983,84,18),
(0xa984,0xa9b2,84,19), (0xa9b3,0xa9b3,84,23), (0xa9b4,0xa9b5,84,18),
(0xa9b6,0xa9b9,84,23), (0xa9ba,0xa9bb,84,18), (0xa9bc,0xa9bc,84,23),
(0xa9bd,0xa9c0,84,18), (0xa9c1,0xa9cd,84, 2), (0xa9cf,0xa9cf,84,17),
(0xa9d0,0xa9d9,84, 8), (0xa9de,0xa9df,84, 2), (0xaa00,0xaa28,76,19),
(0xaa29,0xaa2e,76,23), (0xaa2f,0xaa30,76,18), (0xaa31,0xaa32,76,23),
(0xaa33,0xaa34,76,18), (0xaa35,0xaa36,76,23), (0xaa40,0xaa42,76,19),
(0xaa43,0xaa43,76,23), (0xaa44,0xaa4b,76,19), (0xaa4c,0xaa4c,76,23),
(0xaa4d,0xaa4d,76,18), (0xaa50,0xaa59,76, 8), (0xaa5c,0xaa5f,76, 2),
(0xaa60,0xaa6f,22,19), (0xaa70,0xaa70,22,17), (0xaa71,0xaa76,22,19),
(0xaa77,0xaa79,22,11), (0xaa7a,0xaa7a,22,19), (0xaa7b,0xaa7b,22,18),
(0xaa80,0xaaaf,78,19), (0xaab0,0xaab0,78,23), (0xaab1,0xaab1,78,19),
(0xaab2,0xaab4,78,23), (0xaab5,0xaab6,78,19), (0xaab7,0xaab8,78,23),
(0xaab9,0xaabd,78,19), (0xaabe,0xaabf,78,23), (0xaac0,0xaac0,78,19),
(0xaac1,0xaac1,78,23), (0xaac2,0xaac2,78,19), (0xaadb,0xaadc,78,19),
(0xaadd,0xaadd,78,17), (0xaade,0xaadf,78, 2), (0xaae0,0xaaea,85,19),
(0xaaeb,0xaaeb,85,18), (0xaaec,0xaaed,85,23), (0xaaee,0xaaef,85,18),
(0xaaf0,0xaaf1,85, 2), (0xaaf2,0xaaf2,85,19), (0xaaf3,0xaaf4,85,17),
(0xaaf5,0xaaf5,85,18), (0xaaf6,0xaaf6,85,23), (0xab01,0xab06,25,19),
(0xab09,0xab0e,25,19), (0xab11,0xab16,25,19), (0xab20,0xab26,25,19),
(0xab28,0xab2e,25,19), (0xabc0,0xabe2,85,19), (0xabe3,0xabe4,85,18),
(0xabe5,0xabe5,85,23), (0xabe6,0xabe7,85,18), (0xabe8,0xabe8,85,23),
(0xabe9,0xabea,85,18), (0xabeb,0xabeb,85, 2), (0xabec,0xabec,85,18),
(0xabed,0xabed,85,23), (0xabf0,0xabf9,85, 8), (0xac00,0xd7a3,24,19),
(0xd7b0,0xd7c6,24,19), (0xd7cb,0xd7fb,24,19), (0xf900,0xfa6d,35,19),
####### 0xF000...
(0xfa70,0xfad9,35,19), (0xfb00,0xfb06, 1,15), (0xfb13,0xfb17, 4,15),
(0xfb1d,0xfb1d, 5,19), (0xfb1e,0xfb1e, 5,23), (0xfb1f,0xfb28, 5,19),
(0xfb29,0xfb29, 5, 6), (0xfb2a,0xfb36, 5,19), (0xfb38,0xfb3c, 5,19),
(0xfb3e,0xfb3e, 5,19), (0xfb40,0xfb41, 5,19), (0xfb43,0xfb44, 5,19),
(0xfb46,0xfb4f, 5,19), (0xfb50,0xfbb1, 6,19), (0xfbb2,0xfbc1, 6, 9),
(0xfbd3,0xfd3d, 6,19), (0xfd3e,0xfd3e, 0, 4), (0xfd3f,0xfd3f, 0, 5),
(0xfd50,0xfd8f, 6,19), (0xfd92,0xfdc7, 6,19), (0xfdf0,0xfdfb, 6,19),
(0xfdfc,0xfdfc, 6, 3), (0xfdfd,0xfdfd, 0,11), (0xfe00,0xfe0f,40,23),
(0xfe10,0xfe16, 0, 2), (0xfe17,0xfe17, 0, 4), (0xfe18,0xfe18, 0, 5),
(0xfe19,0xfe19, 0, 2), (0xfe20,0xfe26,40,23), (0xfe30,0xfe30, 0, 2),
(0xfe31,0xfe32, 0, 7), (0xfe33,0xfe34, 0,10), (0xfe35,0xfe35, 0, 4),
(0xfe36,0xfe36, 0, 5), (0xfe37,0xfe37, 0, 4), (0xfe38,0xfe38, 0, 5),
(0xfe39,0xfe39, 0, 4), (0xfe3a,0xfe3a, 0, 5), (0xfe3b,0xfe3b, 0, 4),
(0xfe3c,0xfe3c, 0, 5), (0xfe3d,0xfe3d, 0, 4), (0xfe3e,0xfe3e, 0, 5),
(0xfe3f,0xfe3f, 0, 4), (0xfe40,0xfe40, 0, 5), (0xfe41,0xfe41, 0, 4),
(0xfe42,0xfe42, 0, 5), (0xfe43,0xfe43, 0, 4), (0xfe44,0xfe44, 0, 5),
(0xfe45,0xfe46, 0, 2), (0xfe47,0xfe47, 0, 4), (0xfe48,0xfe48, 0, 5),
(0xfe49,0xfe4c, 0, 2), (0xfe4d,0xfe4f, 0,10), (0xfe50,0xfe52, 0, 2),
(0xfe54,0xfe57, 0, 2), (0xfe58,0xfe58, 0, 7), (0xfe59,0xfe59, 0, 4),
(0xfe5a,0xfe5a, 0, 5), (0xfe5b,0xfe5b, 0, 4), (0xfe5c,0xfe5c, 0, 5),
(0xfe5d,0xfe5d, 0, 4), (0xfe5e,0xfe5e, 0, 5), (0xfe5f,0xfe61, 0, 2),
(0xfe62,0xfe62, 0, 6), (0xfe63,0xfe63, 0, 7), (0xfe64,0xfe66, 0, 6),
(0xfe68,0xfe68, 0, 2), (0xfe69,0xfe69, 0, 3), (0xfe6a,0xfe6b, 0, 2),
(0xfe70,0xfe74, 6,19), (0xfe76,0xfefc, 6,19), (0xfeff,0xfeff, 0,13),
(0xff01,0xff03, 0, 2), (0xff04,0xff04, 0, 3), (0xff05,0xff07, 0, 2),
(0xff08,0xff08, 0, 4), (0xff09,0xff09, 0, 5), (0xff0a,0xff0a, 0, 2),
(0xff0b,0xff0b, 0, 6), (0xff0c,0xff0c, 0, 2), (0xff0d,0xff0d, 0, 7),
(0xff0e,0xff0f, 0, 2), (0xff10,0xff19, 0, 8), (0xff1a,0xff1b, 0, 2),
(0xff1c,0xff1e, 0, 6), (0xff1f,0xff20, 0, 2), (0xff21,0xff3a, 1,15),
(0xff3b,0xff3b, 0, 4), (0xff3c,0xff3c, 0, 2), (0xff3d,0xff3d, 0, 5),
(0xff3e,0xff3e, 0, 9), (0xff3f,0xff3f, 0,10), (0xff40,0xff40, 0, 9),
(0xff41,0xff5a, 1,15), (0xff5b,0xff5b, 0, 4), (0xff5c,0xff5c, 0, 6),
(0xff5d,0xff5d, 0, 5), (0xff5e,0xff5e, 0, 6), (0xff5f,0xff5f, 0, 4),
(0xff60,0xff60, 0, 5), (0xff61,0xff61, 0, 2), (0xff62,0xff62, 0, 4),
(0xff63,0xff63, 0, 5), (0xff64,0xff65, 0, 2), (0xff66,0xff6f,33,19),
(0xff70,0xff70, 0,17), (0xff71,0xff9d,33,19), (0xff9e,0xff9f, 0,17),
(0xffa0,0xffbe,24,19), (0xffc2,0xffc7,24,19), (0xffca,0xffcf,24,19),
(0xffd2,0xffd7,24,19), (0xffda,0xffdc,24,19), (0xffe0,0xffe1, 0, 3),
(0xffe2,0xffe2, 0, 6), (0xffe3,0xffe3, 0, 9), (0xffe4,0xffe4, 0,11),
(0xffe5,0xffe6, 0, 3), (0xffe8,0xffe8, 0,11), (0xffe9,0xffec, 0, 6),
(0xffed,0xffee, 0,11), (0xfff9,0xfffb, 0,13), (0xfffc,0xfffd, 0,11),
####### 0x10000...
(0x10000,0x1000b,47,19), (0x1000d,0x10026,47,19), (0x10028,0x1003a,47,19),
(0x1003c,0x1003d,47,19), (0x1003f,0x1004d,47,19), (0x10050,0x1005d,47,19),
(0x10080,0x100fa,47,19), (0x10100,0x10102, 0, 2), (0x10107,0x10133, 0,14),
(0x10137,0x1013f, 0,11), (0x10140,0x10174, 2,22), (0x10175,0x10178, 2,14),
(0x10179,0x10189, 2,11), (0x1018a,0x1018a, 2,14), (0x10190,0x1019b, 0,11),
(0x101d0,0x101fc, 0,11), (0x101fd,0x101fd,40,23), (0x10280,0x1029c,73,19),
(0x102a0,0x102d0,74,19), (0x10300,0x1031e,37,19), (0x10320,0x10323,37,14),
(0x10330,0x10340,38,19), (0x10341,0x10341,38,22), (0x10342,0x10349,38,19),
(0x1034a,0x1034a,38,22), (0x10380,0x1039d,48,19), (0x1039f,0x1039f,48, 2),
(0x103a0,0x103c3,59,19), (0x103c8,0x103cf,59,19), (0x103d0,0x103d0,59, 2),
(0x103d1,0x103d5,59,22), (0x10400,0x1044f,39,15), (0x10450,0x1047f,49,19),
(0x10480,0x1049d,50,19), (0x104a0,0x104a9,50, 8), (0x10800,0x10805,51,19),
(0x10808,0x10808,51,19), (0x1080a,0x10835,51,19), (0x10837,0x10838,51,19),
(0x1083c,0x1083c,51,19), (0x1083f,0x1083f,51,19), (0x10840,0x10855,86,19),
(0x10857,0x10857,86, 2), (0x10858,0x1085f,86,14), (0x10900,0x10915,63,19),
(0x10916,0x1091b,63,14), (0x1091f,0x1091f,63, 2), (0x10920,0x10939,75,19),
(0x1093f,0x1093f,75, 2), (0x10980,0x1099f,97,19), (0x109a0,0x109b7,96,19),
(0x109be,0x109bf,96,19), (0x10a00,0x10a00,60,19), (0x10a01,0x10a03,60,23),
(0x10a05,0x10a06,60,23), (0x10a0c,0x10a0f,60,23), (0x10a10,0x10a13,60,19),
(0x10a15,0x10a17,60,19), (0x10a19,0x10a33,60,19), (0x10a38,0x10a3a,60,23),
(0x10a3f,0x10a3f,60,23), (0x10a40,0x10a47,60,14), (0x10a50,0x10a58,60, 2),
(0x10a60,0x10a7c,87,19), (0x10a7d,0x10a7e,87,14), (0x10a7f,0x10a7f,87, 2),
(0x10b00,0x10b35,79,19), (0x10b39,0x10b3f,79, 2), (0x10b40,0x10b55,88,19),
(0x10b58,0x10b5f,88,14), (0x10b60,0x10b72,89,19), (0x10b78,0x10b7f,89,14),
(0x10c00,0x10c48,90,19), (0x10e60,0x10e7e, 6,14), (0x11000,0x11000,93,18),
(0x11001,0x11001,93,23), (0x11002,0x11002,93,18), (0x11003,0x11037,93,19),
(0x11038,0x11046,93,23), (0x11047,0x1104d,93, 2), (0x11052,0x11065,93,14),
(0x11066,0x1106f,93, 8), (0x11080,0x11081,91,23), (0x11082,0x11082,91,18),
(0x11083,0x110af,91,19), (0x110b0,0x110b2,91,18), (0x110b3,0x110b6,91,23),
(0x110b7,0x110b8,91,18), (0x110b9,0x110ba,91,23), (0x110bb,0x110bc,91, 2),
(0x110bd,0x110bd,91,13), (0x110be,0x110c1,91, 2), (0x110d0,0x110e8,100,19),
(0x110f0,0x110f9,100, 8), (0x11100,0x11102,95,23),  (0x11103,0x11126,95,19),
(0x11127,0x1112b,95,23),  (0x1112c,0x1112c,95,18),  (0x1112d,0x11134,95,23),
(0x11136,0x1113f,95, 8),  (0x11140,0x11143,95, 2),  (0x11180,0x11181,99,23),
(0x11182,0x11182,99,18),  (0x11183,0x111b2,99,19),  (0x111b3,0x111b5,99,18),
(0x111b6,0x111be,99,23),  (0x111bf,0x111c0,99,18),  (0x111c1,0x111c4,99,19),
(0x111c5,0x111c8,99, 2),  (0x111d0,0x111d9,99, 8),  (0x11680,0x116aa,101,19),
(0x116ab,0x116ab,101,23), (0x116ac,0x116ac,101,18), (0x116ad,0x116ad,101,23),
(0x116ae,0x116af,101,18), (0x116b0,0x116b5,101,23), (0x116b6,0x116b6,101,18),
(0x116b7,0x116b7,101,23), (0x116c0,0x116c9,101, 8), (0x12000,0x1236e,62,19),
(0x12400,0x12462,62,22), (0x12470,0x12473,62, 2), (0x13000,0x1342e,80,19),
(0x16800,0x16a38,83,19), (0x16f00,0x16f44,98,19), (0x16f50,0x16f50,98,19),
(0x16f51,0x16f7e,98,18), (0x16f8f,0x16f92,98,23), (0x16f93,0x16f9f,98,17),
(0x1b000,0x1b000,33,19), (0x1b001,0x1b001,32,19), (0x1d000,0x1d0f5, 0,11),
(0x1d100,0x1d126, 0,11), (0x1d129,0x1d164, 0,11), (0x1d165,0x1d166, 0,18),
(0x1d167,0x1d169,40,23), (0x1d16a,0x1d16c, 0,11), (0x1d16d,0x1d172, 0,18),
(0x1d173,0x1d17a, 0,13), (0x1d17b,0x1d182,40,23), (0x1d183,0x1d184, 0,11),
(0x1d185,0x1d18b,40,23), (0x1d18c,0x1d1a9, 0,11), (0x1d1aa,0x1d1ad,40,23),
(0x1d1ae,0x1d1dd, 0,11), (0x1d200,0x1d241, 2,11), (0x1d242,0x1d244, 2,23),
(0x1d245,0x1d245, 2,11), (0x1d300,0x1d356, 0,11), (0x1d360,0x1d371, 0,14),
(0x1d400,0x1d454, 0,15), (0x1d456,0x1d49c, 0,15), (0x1d49e,0x1d49f, 0,15),
(0x1d4a2,0x1d4a2, 0,15), (0x1d4a5,0x1d4a6, 0,15), (0x1d4a9,0x1d4ac, 0,15),
(0x1d4ae,0x1d4b9, 0,15), (0x1d4bb,0x1d4bb, 0,15), (0x1d4bd,0x1d4c3, 0,15),
(0x1d4c5,0x1d505, 0,15), (0x1d507,0x1d50a, 0,15), (0x1d50d,0x1d514, 0,15),
(0x1d516,0x1d51c, 0,15), (0x1d51e,0x1d539, 0,15), (0x1d53b,0x1d53e, 0,15),
(0x1d540,0x1d544, 0,15), (0x1d546,0x1d546, 0,15), (0x1d54a,0x1d550, 0,15),
(0x1d552,0x1d6a5, 0,15), (0x1d6a8,0x1d6c0, 0,15), (0x1d6c1,0x1d6c1, 0, 6),
(0x1d6c2,0x1d6da, 0,15), (0x1d6db,0x1d6db, 0, 6), (0x1d6dc,0x1d6fa, 0,15),
(0x1d6fb,0x1d6fb, 0, 6), (0x1d6fc,0x1d714, 0,15), (0x1d715,0x1d715, 0, 6),
(0x1d716,0x1d734, 0,15), (0x1d735,0x1d735, 0, 6), (0x1d736,0x1d74e, 0,15),
(0x1d74f,0x1d74f, 0, 6), (0x1d750,0x1d76e, 0,15), (0x1d76f,0x1d76f, 0, 6),
(0x1d770,0x1d788, 0,15), (0x1d789,0x1d789, 0, 6), (0x1d78a,0x1d7a8, 0,15),
(0x1d7a9,0x1d7a9, 0, 6), (0x1d7aa,0x1d7c2, 0,15), (0x1d7c3,0x1d7c3, 0, 6),
(0x1d7c4,0x1d7cb, 0,15), (0x1d7ce,0x1d7ff, 0, 8), (0x1ee00,0x1ee03, 6,19),
(0x1ee05,0x1ee1f, 6,19), (0x1ee21,0x1ee22, 6,19), (0x1ee24,0x1ee24, 6,19),
(0x1ee27,0x1ee27, 6,19), (0x1ee29,0x1ee32, 6,19), (0x1ee34,0x1ee37, 6,19),
(0x1ee39,0x1ee39, 6,19), (0x1ee3b,0x1ee3b, 6,19), (0x1ee42,0x1ee42, 6,19),
(0x1ee47,0x1ee47, 6,19), (0x1ee49,0x1ee49, 6,19), (0x1ee4b,0x1ee4b, 6,19),
(0x1ee4d,0x1ee4f, 6,19), (0x1ee51,0x1ee52, 6,19), (0x1ee54,0x1ee54, 6,19),
(0x1ee57,0x1ee57, 6,19), (0x1ee59,0x1ee59, 6,19), (0x1ee5b,0x1ee5b, 6,19),
(0x1ee5d,0x1ee5d, 6,19), (0x1ee5f,0x1ee5f, 6,19), (0x1ee61,0x1ee62, 6,19),
(0x1ee64,0x1ee64, 6,19), (0x1ee67,0x1ee6a, 6,19), (0x1ee6c,0x1ee72, 6,19),
(0x1ee74,0x1ee77, 6,19), (0x1ee79,0x1ee7c, 6,19), (0x1ee7e,0x1ee7e, 6,19),
(0x1ee80,0x1ee89, 6,19), (0x1ee8b,0x1ee9b, 6,19), (0x1eea1,0x1eea3, 6,19),
(0x1eea5,0x1eea9, 6,19), (0x1eeab,0x1eebb, 6,19), (0x1eef0,0x1eef1, 6, 6),
(0x1f000,0x1f02b, 0,11), (0x1f030,0x1f093, 0,11), (0x1f0a0,0x1f0ae, 0,11),
(0x1f0b1,0x1f0be, 0,11), (0x1f0c1,0x1f0cf, 0,11), (0x1f0d1,0x1f0df, 0,11),
(0x1f100,0x1f10a, 0,14), (0x1f110,0x1f12e, 0,11), (0x1f130,0x1f16b, 0,11),
(0x1f170,0x1f19a, 0,11), (0x1f1e6,0x1f1ff, 0,11), (0x1f200,0x1f200,32,11),
(0x1f201,0x1f202, 0,11), (0x1f210,0x1f23a, 0,11), (0x1f240,0x1f248, 0,11),
(0x1f250,0x1f251, 0,11), (0x1f300,0x1f320, 0,11), (0x1f330,0x1f335, 0,11),
(0x1f337,0x1f37c, 0,11), (0x1f380,0x1f393, 0,11), (0x1f3a0,0x1f3c4, 0,11),
(0x1f3c6,0x1f3ca, 0,11), (0x1f3e0,0x1f3f0, 0,11), (0x1f400,0x1f43e, 0,11),
(0x1f440,0x1f440, 0,11), (0x1f442,0x1f4f7, 0,11), (0x1f4f9,0x1f4fc, 0,11),
(0x1f500,0x1f53d, 0,11), (0x1f540,0x1f543, 0,11), (0x1f550,0x1f567, 0,11),
(0x1f5fb,0x1f640, 0,11), (0x1f645,0x1f64f, 0,11), (0x1f680,0x1f6c5, 0,11),
(0x1f700,0x1f773, 0,11), (0x20000,0x2a6d6,35,19), (0x2a700,0x2b734,35,19),
(0x2b740,0x2b81d,35,19), (0x2f800,0x2fa1d,35,19), (0xe0001,0xe0001, 0,13),
(0xe0020,0xe007f, 0,13), (0xe0100,0xe01ef,40,23)
  ]}  # end of script_data{ "scriptNames", "categoryAbbrs", "idx" }

# Sanity-check
nsn = len(script_data["scriptNames"])
if (nsn != 102):
    lg.critical("Bad entry count for scriptNames: %d.", nsn)
    sys.exit()
ncn = len(script_data["categoryAbbrs"])
if (ncn != 25):
    lg.critical("Bad entry count for categoryAbbrs: %d.", ncn)
    sys.exit()
nidx = len(script_data["idx"])
if (nidx != 1637):
    lg.critical("Bad entry count for idx: %d.", nidx)
    sys.exit()


def script_cat(codepoint:int) -> (str, str):
    """ For the given unicode character, return a tuple (Scriptname, Category).
    Sadly, unicodedata does not have script or block (it does have category).
    So we do a binary search in codepoint space.
    See https://stackoverflow.com/questions/9868792/
    """
    l = 0
    #cat = unicodedata.category(chr(codepoint))
    r = len(script_data["idx"]) - 1
    while r >= l:
        m = (l + r) >> 1
        if codepoint < script_data["idx"][m][0]:
            r = m - 1
        elif codepoint > script_data["idx"][m][1]:
            l = m + 1
        else:
            return (
                script_data["scriptNames"][script_data["idx"][m][2]],
                script_data["categoryAbbrs"][script_data["idx"][m][3]])
    return "Unknown", "??"

def myCodepoint2name(n:int) -> str:
    if (not isinstance(n, int)): n = ord(n)
    return unicodedata.name(chr(n))

def myCodepoint2script(n:int) -> str:
    if (not isinstance(n, int)): n = ord(n)
    a, _ = script_cat(n)
    return a

def myCodepoint2category(n:int) -> str:
    if (not isinstance(n, int)): n = ord(n)
    _, a = script_cat(n)
    return a

def _compile_scripts_txt():
    # build indexes above, from "scripts.txt"

    idx = []
    names = []
    cats = []

    import textwrap

    url = "http://www.unicode.org/Public/UNIDATA/Scripts.txt"
    f = urlopen(url)
    for ln in f:
        p = re.findall(r"([0-9A-F]+)(?:\.\.([0-9A-F]+))?\W+(\w+)\s*#\s*(\w+)", ln)
        if p:
            a, b, name, cat = p[0]
            if name not in names:
                names.append(name)
            if cat not in cats:
                cats.append(cat)
            idx.append((int(a, 16), int(b or a, 16), names.index(name), cats.index(cat)))
    idx.sort()

    print('script_data = {\n"names":%s,\n"cats":%s,\n"idx":[\n%s\n]}' % (
        "\n".join(textwrap.wrap(repr(names), 80)),
        "\n".join(textwrap.wrap(repr(cats), 80)),
        "\n".join(textwrap.wrap(
            ", ".join("(0x0%x,0x0%x,%d,%d)" % c for c in idx), 80))))


###############################################################################
#
unixJargon = {
    "!" : "Common: bang; pling; excl; not; shriek; ball-bat. " +
           "Rare: factorial; exclam; smash; cuss; boing; yell; wow; hey; " +
           "wham; eureka; spark-spot; soldier, control",
    "\"" : "Common: double quote; quote. " +
           "Rare: literal mark; double-glitch; snakebite; dirk; " +
           "rabbit-ears; double prime",
    "#" : "Common: number sign; pound; pound sign; hash; " +
           "sharp; crunch; hex; mesh. " +
           "Rare: grid; cross-hatch; octothorpe; flash; pig-pen; " +
           "tic-tac-toe; scratchmark; thud; thump; splat",
    "$" : "Common: dollar. " +
           "Rare: currency symbol; buck; cash; bling; string (from BASIC); " +
           "escape (when used as the echo of ASCII ESC); ding; cache; big money",
    "%" : "Common: percent; mod; grapes. " +
           "Rare: double-oh-seven",
    "&" : "Common: amp; amper; and, and sign. " +
           "Rare: address (from C); reference (from C++); andpersand; " +
           "bitand; background (from sh(1) ); pretzel",
    "'" : "Common: single quote; quote. " +
           "Rare: prime; glitch; tick; irk; pop; spark;",
    "(" : "Common: l paren; l parenthesis; leftight; open; paren; " +
           "o paren; o parenthesis; l parenthesis; l banana. " +
           "Rare: so; lparen; o round bracket, l round bracket, wax; " +
           "parenthisey; l ear",
    ")" : " Common: r paren; r parenthesis; right; close; the-sis; " +
           "c paren; c parenthesis; r parenthesis; r banana. " +
           "Rare: al-ready; rparen; c round bracket, r round bracket, " +
           "wane; unparenthisey; r ear",
    "*" : "Common: star; splat. " +
           "Rare: wildcard; gear; dingle; mult; spider; aster; " +
           "times; twinkle; glob; Nathan Hale",
    "+" : "Common: add. " +
           "Rare: cross; intersection",
    "," : "" +
           "Rare: tail",
    "-" : "Common: dash. " +
           "Rare: worm; option; dak; bithorpe",
    "." : "Common: dot; point. " +
           "Rare: radix point; full stop; spot",
    "/" : "Common: slash; stroke; forward slash. " +
           "Rare: diagonal; solidus; over; slak; virgule; slat",
    ":" : "Common: . " +
           "Rare: dots; two-spot",
    ";" : "Common: semi. " +
           "Rare: weenie; hybrid, pit-thwong",
    "<" : "Common: bra; l angle; l angle bracket; l broket. " +
           "Rare: from; read from; comes-from; in; crunch; tic; angle",
    ">" : "Common: ket; r angle; r angle bracket; r broket. " +
           "Rare: into, towards; write to; gozinta; out; zap; tac; right angle",
    "=" : "Common: gets; takes. " +
           "Rare: quadrathorpe; half-mesh",
    "?" : "Common: query; ques . " +
           "Rare: quiz; whatmark; what; wildchar; huh; hook; " +
           "buttonhook; hunchback",
    "@" : "Common: at sign; at; strudel. " +
           "Rare: each; vortex; whorl; whirlpool; cyclone; snail; " +
           "ape; cat; rose; cabbage;",
    "V" : "" +
           "Rare: book",
    "[" : "Common: l square bracket; l bracket; bracket. " +
           "Rare: square; U turn",
    "]" : "Common: r square bracket; r bracket; unbracket. " +
           "Rare: un-square; U turn back",
    "\\" : "Common: backslash, hack, whack; escape; reverse slash; " +
           "slosh; backslant; backwhack. " +
           "Rare: bash; reversed virgule; reverse solidus; rsol; backslat",
    "^" : "Common: hat; control; uparrow; caret. " +
           "Rare: xor sign, chevron; shark; shark-fin; to the; " +
           "to the power of; fang; pointer",
    "_" : "Common: underscore; underbar; under. " +
           "Rare: score; backarrow; skid; flatworm",
    "`" : "Common: backquote; left quote; left single quote; " +
           "open quote; grave. " +
           "Rare: backprime; backspark; unapostrophe; birk; blugle; " +
           "back tick; back glitch; push; quasiquote",
    "{" : "Common: o brace; l brace; l squiggly; l squiggly bracket, " +
           "l squiggly brace; l curly bracket, l curly brace. " +
           "Rare: brace; curly-curly; l squirrelly; embrace",
    "}" : "Common: c brace; r brace; r squiggly; r squiggly bracket, " +
           "r squiggly brace; r curly bracket; r curly brace. " +
           "Rare: unbrace; un-curly; r squirrelly; bracelet",
    "|" : "Common: bar; or; or-bar; v-bar; pipe; vertical bar. " +
           "Rare: gozinta; thru; pipesinta; spike",
    "~" : "Common: squiggle; twiddle; not. " +
           "Rare: approx; wiggle; swung dash; enyay"
}


###############################################################################
# TODO: Finish sync with ord and strfchr
#
class CProps(Enum):
    #propname         ( typ, cat, description, ),
    ERROR =          ( str, "E", "", ),
    CODEPOINT =      ( int, "U", "code point", ),
    LITERAL =        ( str, "U", "literal character", ),

    # Unicode info
    BLOCKNAME =      ( str, "U", "block Name", ),
    CATEGORYABBR =   ( str, "U", "category Abbreviation", ),
    CATEGORYNAME =   ( str, "U", "category Name", ),
    PLANENAME =      ( str, "U", "plane Name", ),
    PLANENUMBER =    ( int, "U", "plane Number", ),
    SCRIPTNAME =     ( str, "U", "script Name", ),
    #UNAME =          ( str, "U", "Unicode name", ),
    #UNORM =          ( str, "U", "Unicode name, as identifier", ),
    JARGON =         ( str, "P", "jargon", ),

    EAWIDTH =        ( "?", "P", "East Asian width", ),
    WIDTH =          ( "?", "P", "Width", ),
    NUMERICVALUE =   ( float, "P", "Numeric value, if any.", ),

    ISURI =          ( "?", "P", "Is allowed in URIs?", ),
    #ISFPI =          ( "?", "P", "Is allowed in FPIs?", ),
    ISBIDI =         ( "?", "P", "Is bidirectional?", ),
    ISCOMBINING =    ( "?", "P", "Is a combining character?", ),
    ISCOMBINED =     ( "?", "P", "Is a combined character?", ),
    ISMIRROR =       ( "?", "P", "Is part of a mirror pair?", ),
    #MIRROROF =

    DECOMP =         ( str, "P", "decomp", ),
    NFC =            ( str, "P", "NFC", ),
    NFKC =           ( str, "P", "NFKC", ),
    NFD =            ( str, "P", "NFD", ),
    NFKD =           ( str, "P", "NFKD", ),

    # Alternate representations
    URI =            ( str, "F", "uri", ),
    DECENTITY =      ( str, "F", "DECENTITY", ),
    HEXENTITY =      ( str, "F", "HEXENTITY", ),
    NAMEDENTITY =    ( str, "F", "HTML named entity reference", ),


###############################################################################
# POSIX regex category support
#
posixCategories = [
    "alnum",  # \\w\\d          digits, letters
    "alpha",  # \\w             letters
    "ascii",  # [\\x00-\\x7F]   ASCII characters
    "blank",  # [ \\t]          space and TAB only
    "cntrl",  # [\\x00-\\x1F\\x80-\\x9F]  Control characters
    "digit",  # \\d             digits
    "graph",  #                 graphic characters
    "lower",  #                 lowercase letters
    "print",  #                 graphic characters and space
    "punct",  #                 punctuation
    "space",  # \\s             all whitespaces
    "upper",  #                 uppercase letters
    "word",   # \\w             word characters
    "xdigit", #  [0-9a-fA-f]    hexadecimal digits
]

noRegex = False  # Have we tried and failed to import "regex"?

def getPosixCategories(c:chr) -> List:
    """Return the list of POSIX regex character categories this char is in.
    Python re doesn't currently support them, so we try to use regex and
    warn if it can't be imported.

    """
    global noRegex
    if (noRegex):
        return [ "" ]
    try:
        import regex
    except ImportError:
        if (not args.quiet): lg.error(
            "Cannot import 'regex' to determine POSIX categories. Install it.")
        noRegex = True
        return [ "" ]
    foundCats = []
    for catName in posixCategories:
        if (regex.match(r"[[:%s:]]" % catName, c)): foundCats.append(catName)
    return foundCats


###############################################################################
#
def getCharInfo(n:int):  # TODO Cut over to use strfchr CharInfo object
    """Make a dictionary with a lot of info about the given code point.
    See https://docs.python.org/2/library/unicodedata.html
    """
    charInfo = { "n": n, "ERROR": None }

    if (n > 0x1FFFF):
        raise ValueError("[getCharInfo: Out of range (0x%06x)]" % (n))

    if (n == 0xEFBFBD):
        raise ValueError("getCharInfo: UTF-8 of U+FFFD (Replacement Character) 0xEFBFBD")

    literal = charInfo["LITERAL"]  = chr(n)

    # Unicodedata does not return names for C0 controls....
    if (n < 32):
        charInfo["UNAME" ] = C0Names[n]
    else:
        try:
            charInfo["UNAME" ] = unicodedata.name(literal)
        except ValueError:
            lg.critical("unicodedata.name() failed for '%s'.", literal)
            charInfo["UNAME" ] = "???"
    assert charInfo["UNAME"]

    # Unicode info
    charInfo["BLOCKNAME"]    = myCodepoint2block(n)
    charInfo["CATEGORYABBR"] = unicodedata.category(literal)
    charInfo["CATEGORYNAME"] = None
    if (charInfo["CATEGORYABBR"] in unicodeCategories):
        charInfo["CATEGORYNAME"] = unicodeCategories[charInfo["CATEGORYABBR"]][1]
    charInfo["PLANENUMBER"]  = n >> 16
    charInfo["PLANENAME"]    = getPlaneName(charInfo["PLANENUMBER"])
    charInfo["SCRIPTNAME"]   = myCodepoint2script(n)

    charInfo["EAWIDTH"]      = unicodedata.east_asian_width(literal)
    #charInfo["WIDTH"]        = unicodedata.east_asian_width(literal)
    charInfo["NUMERICVALUE"] = unicodedata.numeric(literal, None)

    charInfo["ISURI"]        = re.match(okInUriExpr, literal) and True
    charInfo["ISFPI"]        = re.match(okInFpiExpr, literal) and True
    #charInfo["ISNUMERIC"]    =
    charInfo["ISBIDI"]       = unicodedata.bidirectional(literal)
    charInfo["ISCOMBINING"]  = unicodedata.combining(literal)
    #charInfo["ISCOMBINED"]   =
    charInfo["ISMIRROR"]     = unicodedata.mirrored(literal)
    #charInfo["MIRROROF"]     =

    charInfo["DECOMP"]       = unicodedata.decomposition(literal)
    charInfo["NFC"]          = unicodedata.normalize("NFC",  literal)
    charInfo["NFKC"]         = unicodedata.normalize("NFKC", literal)
    charInfo["NFD"]          = unicodedata.normalize("NFD",  literal)
    charInfo["NFKD"]         = unicodedata.normalize("NFKD", literal)

    # Alternate forms
    # LITERAL, SLASH0/2/4/8
    charInfo["DECENTITY"]    = "&#%d;" % (n)
    charInfo["HEXENTITY"]    = "&#x%05x;" % (n)
    # BININT, OCTINT, DECINT, HEXINT, UPLUS
    #print("type: %s" % (type(codepoint2name)))
    if (n in codepoint2name):
        charInfo["NAMEDENTITY"] = "  &%s;" % (codepoint2name[n])
    else:
        charInfo["NAMEDENTITY"] = None
    buf = "\\\\x"
    myBytes = literal.encode("utf-8")
    for b in myBytes: buf += "%02x" % (b)
    charInfo["UTF8"]         = buf
    charInfo["URI"]          = urlquote(literal.encode("utf-8"))

    if (n<=33): charInfo["MNEMONIC"] = C0Mnemonics[n]
    elif (n>=128 and n<=160): charInfo["MNEMONIC"] = C1Mnemonics[n-128]
    else: charInfo["MNEMONIC"] = ""
    charInfo["CONTROLPIC"] = chr(0x2400+n) if (n<32) else ""

    # Properties
    #
    charInfo["fpiOK"]     = okInFPI(n)
    charInfo["uriOK"]     = okInURI(n)
    charInfo["bidi"]      = unicodedata.bidirectional(literal)
    charInfo["combining"] = unicodedata.combining(literal)
    charInfo["eawidth"]   = unicodedata.east_asian_width(literal)
    charInfo["mirror"]    = unicodedata.mirrored(literal)
    charInfo["decomp"]    = unicodedata.decomposition(literal)
    charInfo["NFC"]       = unicodedata.normalize("NFC",  literal)
    charInfo["NFKC"]      = unicodedata.normalize("NFKC", literal)
    charInfo["NFD"]       = unicodedata.normalize("NFD",  literal)
    charInfo["NFKD"]      = unicodedata.normalize("NFKD", literal)

    charInfo["POSIXCATS"] = getPosixCategories(literal)
    charInfo["JARGON"] = None
    if (literal in unixJargon): charInfo["JARGON"] = unixJargon[literal]

    if (args.verbose):
        buf = "CharInfo for U+%05x:\n" % (n)
        for k, v in charInfo.items():
            buf += "    %-16s %s\n" % (k, v)
        lg.info("%s    =======\n\n", buf)
    return charInfo

def makeDisplay(n:int, full=True) -> str:
    """Make a terminal-friendly display of many properties of the Unicode
    character at the given codepoint 'n'.
    """
    try:
        charInfo = getCharInfo(n)
    except ValueError as e:
        raise ValueError from e  #("getCharInfo() failed: %s" % (e))

    try:
        msg = "\n".join([
            fmtline("Unicode Name",     charInfo["UNAME" ]),
            fmtline("Script",           charInfo["SCRIPTNAME"]),
            fmtline("Category",         "'%s' (%s)" % (
                charInfo["CATEGORYABBR"], charInfo["CATEGORYNAME"])),
            fmtline("Block",            charInfo["BLOCKNAME"]),
            fmtline("Plane",            "%d: %s" % (
                charInfo["PLANENUMBER"], charInfo["PLANENAME"])),
            fmtline("Literal",          "'" + protectDisplay(charInfo["LITERAL"]) + "'"),
            fmtline("Bases",            "o%08o d%06d 0x%05x" % (n, n, n)),
            fmtline("Unicode",          "U+%05x, utf8 %s, URI %s (URI? %s, FPI? %s)" % (
                n,  charInfo["UTF8"], charInfo["URI"],
                "Y" if charInfo["ISURI"] else "N", "Y" if charInfo["ISFPI"] else "N")),
            fmtline("Entities",         "%s  %s  %s" % (
                charInfo["HEXENTITY"], charInfo["DECENTITY"], charInfo["NAMEDENTITY"])),
            fmtline("Unix jargon",      charInfo["JARGON"] or "")
        ]) + "\n"
        if (full):
            if ("MIRROROF" in charInfo):
                mChar = charInfo["MIRROROF"]
            else:
                mChar = ""
                if (not args.quiet):
                    msg += "    ******* No MIRROROF property *******\n"
            if (mChar != ""): mDisp = "U+%04x" % (mChar)
            else: mDisp = "-none-"
            msg += "\n".join([
                fmtline("Numeric value", charInfo["NUMERICVALUE"]),
                fmtline("Is Bidi",       charInfo["ISBIDI"]),
                fmtline("Is Combining",  charInfo["ISCOMBINING"]),
                #fmtline("Is Combined",   charInfo["ISCOMBINED"]),
                fmtline("Mirror",        charInfo["ISMIRROR"]),
                fmtline("Mirror of",     mDisp),
                fmtline("ea width",      charInfo["EAWIDTH"]),

                fmtline("Decompose",     "???"),  #charInfo["DECOMP"]),  # TODO: Fix Decompose
                fmtline("Normalizations",
                    "NFC '%s' %s, NFKC '%s' %s, NFD '%s' %s, NFKD '%s' %s" %
                    (protectDisplay(charInfo["NFC"]),  stringToHex(charInfo["NFC"]),
                     protectDisplay(charInfo["NFKC"]), stringToHex(charInfo["NFKC"]),
                     protectDisplay(charInfo["NFD"]),  stringToHex(charInfo["NFD"]),
                     protectDisplay(charInfo["NFKD"]), stringToHex(charInfo["NFKD"])
                    )),
                fmtline("Posix regex",   "[ " + ", ".join(charInfo["POSIXCATS"]) + " ]")
            ])
            if (not args.nomac and n>=128 and n <=255 and n in macRomanData):
                macData = macRomanData[n]
                macDescr = "%s (U+%04x)" % (macData[2], macData[0])
                msg += "\n" + fmtline("But on Mac:", macDescr)

    except KeyError as e:  # KeyError as e:
        print("KeyError raised in makeDisplay(0x%04x, full=%s): key: '%s'," %
            (n, full, e))
        for k in sorted(charInfo.keys()):
            print("    %-20s  %s" % ('"'+k+'"', charInfo[k]))
        msg = "[FAIL]"

    if (n in cp1252ToUnicode):
        lg.info("CP1252 warning for %d.", n)
        msg += ("\n    WARNING: May be intended as CP1252. If so use U+%05x (%s)."
            % (cp1252ToUnicode[n], unicodedata.name(chr(cp1252ToUnicode[n]))))
    elif (n == 0xFF): msg += (
        "\n    WARNING: 0XFF may be DELETE or LATIN SMALL LETTER Y WITH DIAERESIS")

    if (n<32):
        lit = "(C0 control: " + C0Mnemonics[n]
        if (n>0 and n<26): lit += ", ^" + string.ascii_uppercase[n-1]
        lit += ")\n"
        msg += lit
    elif (n>127 and n<160):
        lit = "(C1 control: " + C1Mnemonics[n-128] + ")\n"
        msg += lit

    return msg + "\n"

def protectDisplay(c, alt="[omitted]"):
    """See if the character is one that messes with display too much, and
    replace it with something more palatable.
    c may be a character or an int code point.
    """
    if isinstance(c, int): c = chr(c)
    if (re.match(r"[\\s\\x00-\\x1F\\x80-\\x9F]", c, flags=re.UNICODE)): return alt
    return c

def stringToHex(x) -> str:
    """Show all the BYTES in hex.
    """
    buf = "0x"
    for byte in x.encode(encoding='utf-8'):
        buf += "%02x" % (byte)
    return buf

def fmtline(label:str, data) -> str:
    """Make a nice lined-up key/value display.
    """
    return "    %-16s %s" % (label, data or "")

def getPlaneName(pnum:int) -> str:
    if   (pnum ==  0): pname = "Basic Multilingual"
    elif (pnum ==  1): pname = "Supplementary Multilingual"
    elif (pnum ==  2): pname = "Supplementary Ideographic"
    elif (pnum == 16): pname = "Supplementary Private Use Area B"
    elif (pnum == 15): pname = "Supplementary Private Use Area A"
    elif (pnum == 14): pname = "Supplementary Special-purpose"
    elif (pnum >=  3): pname = "Unassigned"
    else: pname = "-UNKNOWN-"
    return pname

# See https://stackoverflow.com/questions/243831/
#
def myCodepoint2block(n:int) -> str:
    for start, end, block_name in _blocks:
        if start <= n <= end:
            return block_name
    return None


def getCodePoint(cspec) -> int:
    """Try to turn whatever comes in, into a codepoint. Takes many
    of the alternate forms provided by strfchr():
        x             -- LITERAL
        &#8226;       -- DECENTITY
        &#x2022;      -- HEXENTITY
        &bull;        -- NAMEDENTITY
        o20042        -- OCTINT (octal code point)
        d08226        -- DECINT (decimal code point)
        0x02022       -- HEXINT (hex code point)
        U+02022       -- UPLUS
        %e2%80%a2     -- URI (escaped UTF8)
        \\xe2\\x80\\xa2  -- UTF8
        MNEMONIC
        BULLET        -- UNAME (Unicode character name)
        bull          -- NAMEDENTITY without delimiters   ??? TODO
    """
    if (isinstance(cspec, str)):
        cspec = cspec.strip()
    else:
        cspec = chr(cspec)
    uspec = cspec.upper()
    if (len(cspec) == 1):
        return ord(cspec)

    # Full entities
    if (cspec.startswith("&") and cspec.endswith(";")):
        c = unescape(cspec)                                # XML entities
        if (len(c)==1): return ord(c)

    if (cspec.isdigit()):                                  # OCTINT, DECINT
        if (cspec[0] == "0"): return int(cspec, 8)
        return int(cspec, 10)
    if (re.match(r"0X[\\dA-F]+$", uspec, re.I)):            # HEXINT
        return int(uspec[2:], 16)
    if (re.match(r"U\\+[\\dA-F]+$", uspec, re.I)):           # UPLUS
        return int(uspec[2:], 16)
    if (re.match(r"(%[\\da-f][\\dA-F])+$", uspec, re.I)):    # URI
        return ord(urlunquote(uspec))
    if (re.match(r"(\\\\x[\\dA_F][\\dA-F])+$", uspec, re.I)):  # UTF8
        uriForm = re.sub(r"\\\\x", "%", uspec)
        return ord(urlunquote(uriForm))
    if (uspec in C0Mnemonics):                             # MNEMONIC
        return C0Mnemonics.index(uspec)
    if (uspec in C1Mnemonics):
        return C1Mnemonics.index(uspec) + 0x80
    try:                                                   # UNAME
        uspec2 = uspec.replace("_", " ")                   # UNORM
        n = unicodedata.lookup(uspec2)
        return n
    except KeyError:
        pass
    return None


###############################################################################
#
if __name__ == "__main__":
    def anyInt(x):
        lg.info("Parsing arg '%s'.", x)
        try:
            return int(x, 0)
        except ValueError:
            return ord(x[0])

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--category", type=str, default=None,
            choices=sorted(unicodeCategories.keys()),
            help="""List characters in the specified 2-letter category.
            See also showUnicodeCharsInClass.py.""")
        parser.add_argument(
            "--help-categories", action="store_true",
            help="Display a list of character categories and exit.")
        parser.add_argument(
            "--maxChar", type=int, default=sys.maxunicode,
            help="When displaying a range of code points, skip any above this.")
        parser.add_argument(
            "--minChar", type=int, default=0,
            help="When displaying a range of code points, skip any below this.")
        parser.add_argument(
            "--nomac", action="store_true",
            help="Suppress 'but on Mac' line for ccode points 128-255.")
        parser.add_argument(
            "--python", action="store_true",
            help="Make --cat write Python tuples, not just messages.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version",
            version="%s (Python %s)" % (__version__, sys.version_info[0]),
            help="Display version information, then exit.")

        parser.add_argument(
            "charSpecs", type=anyInt, nargs=argparse.REMAINDER,
            help="Unicode code point numbers (base 8, 10, or 16).")

        args0 = parser.parse_args()

        if (args0.help_categories):
            print("Unicode character categories:")
            for k, v in unicodeCategories.items():
                print("    %-2s  %s" % (k, v))
            sys.exit()

        if (lg and args0.verbose):
            logging.basicConfig(level=logging.INFO - args0.verbose)

        return(args0)


    ###########################################################################
    # Main
    #
    args = processOptions()

    if (args.category):
        found = 0
        for codePoint in (range(args.minChar, args.maxChar + 1)):
            c0 = chr(codePoint)
            categ = unicodedata.category(c0)
            if (not categ.startswith(args.category)): continue
            try:
                nam = unicodedata.name(c0)
            except ValueError:
                if (args.verbose): lg.info(
                    "No name for char '%s' (U+%05x)\n", c0, codePoint)
                continue
            if (args.python):
                print("    ( 0x%05x, '%s',\t\"%s\" )," % (codePoint, c0, nam))
            else:
                print("U+%05x: '%s' %s" % (codePoint, c0, nam))
            found += 1
        print("\nCharacters found in category '%s' (%s): %d." %
            (args.category, unicodeCategories[args.category], found))
        sys.exit()

    for cspec0 in (args.charSpecs):
        n0 = getCodePoint(cspec0)
        if (n0 is None):
            print("******* Cannot identify '%s'." % (cspec0))
        else:
            print(makeDisplay(n0))
