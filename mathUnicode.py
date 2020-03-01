#!/usr/bin/env python
#
# mathUnicode.py: Map Latin etc. to special math areas.
#
# Written <2006-10-04, Steven J. DeRose.
# 2008-02-11 sjd: Add --perl, perl -w.
# 2008-09-03 sjd: BSD. Improve doc, error-checking, fix bug in -all.
# 2010-03-28 sjd: perldoc. Add \[\] to -ps.
# 2010-09-20ff sjd: Cleanup. Add --color; ls and dircolors support. Simplify
#     numeric handling of codes. Support color combinations. Add -setenv.
#     Change 'fg2_' prefix to 'bold_' and factor out of code.
# 2013-06-11: Add --xterm256, but just for --list.
# 2013-06-27: Add --table. Ditch "fg2_" and "b_" prefixes.
# 2014-07-09: Clean up doc. Add --python. Clean up --perl. fix --list.
# 2015-02-04: Support rest of effects beyond bold.
# 2015-08-25: Start syncing color-refs with sjdUtils.pm.
# 2016-01-01: Get rid of extraneous final newline with -m.
# 2016-07-21: Merge doc on color names w/ sjdUtils.p[my], etc.
# 2016-10-25: Clean up to integrate w/ ColorManager. Change names.
#     Debug new (hashless) way of doing colors.
# ####### 2018-08-29: Port to Python.
# 2018-08-29ff: Split from Perl colorstring, and Ported. Copyright Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
# Merged from incomplete 'UnicodeAltLatin.py' (2018-09-04):
#
# To do:
#     Combine upper/lower case under name.
#     Split into subclasses for latin/greek/digit?
#     Rename
#     Finish exception list entries for missing "0" digits.
#     Integrate non-Latin digits.
#
# Add?
#     aeox schwa hklmnpst; i=1d62, r=1d63, u=1d64, v=1d65, j=2c7c
#     [ 'subscript latin upper (...209c)', 0x02090 ],
#     https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts#Uses
#       superscripts: i=2071 n=207f
#       subscripts: iruv, grk bgrfx 0x1d62...0x1d6a aeoxhklmnpst
#       combining diacriticals marks has aeioucdhmrtvx
#           and suppl for rest of lc latin except jqy (seriously???)
#       spacing modifier letters a few
#       phonetic extensions has some latin/cyr/ipa
#       [ 'subscript latin lower', ],
#       some cyrillic, kanbun, etc.
#     [ 'fullwidth latin upper', 0x0ff21 ],
#     [ 'fullwidth latin lower', 0x0ff41 ],
#     2145-2149 double struck italics???
#     black-letter capital chirz: 0x210c...0x212d = fraktur
#     213c-40 double struck pi, gamma, sigma
#     (couple extras at 1d6a4, dotless i, j)
#     213c-40 double struck pi, gamma, sigma
#
from __future__ import print_function
import sys
#import string

from alogging import ALogger
lg = ALogger(1)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring
else:
    string_types = str
    def unichr(n): return chr(n)

__metadata__ = {
    'title'        : "mathUnicode.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 2.7.6",
    'created'      : "<2006-10-04",
    'modified'     : "2020-01-29",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Provide support for using the many Unicode variations on the Latin alphabet.

=head2 Usage

    import mathUnicode
    s2 = mathUnicode.convert(text,
            scriptName="Latin", targetName="Mathematical Bold Capital")

or

    xtab = mathUnicode.getTranslateTable(
        'Latin', 'Mathematical Sans-serif Bold Italic')
    s = s.translate(xtab)

Using this package directly from the command line (without -h), will
display a list of the available Latin variations and where their
ranges start in Unicode. Specify I<--greeks> or I<--digits> to get the list
of variants for those (the digits one include sets that run 1-10 rather
than 0-9, but the "start point" is always where the zero at least I<would>
be if it existed.

=head2 Available character variations

Most of these are "Mathematical", and they include variations of several kinds:

=over

=item * fullwidth, script, fraktur, double-struck, sans-serif, and monospace;

=item * Parenthesized, Circled, Squared, Negative-circled, Negative-squared, Regional symbol;

=item * Some of the above also have bold, italic, and/or bold italic variations.

=back

A few Latin variants do not include lower case.

There is also a (smaller) selection of variants of the Greek alphabet, of
digits, and of syllabic and ideographic characters.

In several cases, some of the characters are not in the place one might expect.
For example 'h' might be expected to be the 8th code point in the
"Mathematical Italic Small" range, but in fact that code point (U+1D455) is
undefined. The block is still ordered normally, with the 'i' at U+1D456.
The 'h' is instead at U+210e (Planck Constant). Presumably it was defined
before the rest of the "Mathematical Italic Small" characters.

=Related Commands=

C<ord --math> will show a list of these characters.

C<UnicodeAltLatin.py> a previous draft of this (should merge).


=Known bugs and Limitations=

Digit series that do not include 0 are not all correct yet.

Non-Latin digit series are not yet integrated.

Additional methods should be added, like ready-made string converters.

=Notes=

Not all of the variant alphabets are contiguous blocks of characters.
This script maps them anyway.

There are some additional forms that do not have complete alphabets:

    Some squared CJK
    Circled italic latin C, R
    Double-Struck Italic D, e, i, j
    Squared Latin Small Letter D
    Old Italic letters at U+10300 and following
    circled katakana U+032d0
    some circled hangul and ideographs U+3260
    circled number X on black square U+3248
    superscript and subscript sets (very incomplete)

=Licensing=

Copyright 2006-20209 by Steven J. DeRose. This work is licensed under a Creative
Commons Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].

=Options=
"""

###############################################################################
# Unicode alternate forms of Latin alphabet
#
class Fonts:
    """These are the fonts available as Unicode 'Mathematical' variations on
    Latin. A similar list is available for Greek, and many more for digits.
    Combining accents could be used to support more languages.
    """
    fonts = {
        # Name                        ( Upper    Lower,   Digits   Exceptions )
        'BOLD':                       ( 0x1d400, 0x1d41a, 0x1d7ce, '' ),
        'ITALIC':                     ( 0x1d434, 0x1d44e, None,    'h' ),
        'BOLD ITALIC':                ( 0x1d468, 0x1d482, None,    '' ),
        'SCRIPT':                     ( 0x1d49c, 0x1d4b6, None,    'BEFHILMR ego' ),
        'BOLD SCRIPT':                ( 0x1d4d0, 0x1d4ea, None,    '' ),
        'FRAKTUR':                    ( 0x1d504, 0x1d51e, None,    'CHIRZ' ),
        'DOUBLE-STRUCK':              ( 0x1d538, 0x1d552, 0x1d7d8, 'CHNPQRZ' ),
        'BOLD FRAKTUR':               ( 0x1d56c, 0x1d586, None,    '' ),
        'SANS-SERIF':                 ( 0x1d5a0, 0x1d586, 0x1d7e3, '' ),
        'SANS-SERIF BOLD':            ( 0x1d5d4, 0x1d5ee, 0x1d7ec, '' ),
        'SANS-SERIF ITALIC':          ( 0x1d608, 0x1d622, None,    '' ),
        'SANS-SERIF BOLD ITALIC':     ( 0x1d63c, 0x1d656, None,    '' ),
        'MONOSPACE':                  ( 0x1d670, 0x1d68a, 0x1d7f6, '' ),
        'CIRCLED':                    ( 0x024b6, 0x024d0, 0x0245f, '' ),
        'PARENTHESIZED':              ( 0x1f110, 0x0249c, 0x02473, '' ),

        "Fullwidth":                  ( 0x0FF21, 0x0FF41, 0x0FF10, '' ),
        "Supercript":                 ( None,    None,    0x02070, '123' ),
        "Subscript":                  ( None,    None,    0x02080, '' ),

        # Not available in lower case, only upper
        'SQUARED':                    ( 0x1f130, None,    None,    '' ),
        'NEGATIVE CIRCLED':           ( 0x1f150, None,    0x02775, '' ),
        'NEGATIVE SQUARED':           ( 0x1f170, None,    None,    '' ),
        'REGIONAL INDICATOR SYMBOL':  ( 0x1f1e6, None,    None,    '' ),
    }

###############################################################################
# Support Unicode alternate forms of Latin alphabet
# Greek and digits also defined for some of these
# See also bin/data/unicodeLatinAlphabets.py
#
class mathUnicode:
    oneHotFeatures = [
        'Fullwidth', 'Script', 'Fraktur', 'Double-Struck', 'Sans-serif',
        'Monospace', 'Parenthesized', 'Circled', 'Squared',
        'Negative-circled', 'Negative-squared', 'Regional symbol'
    ]

    biFeatures = [ 'Bold', 'Italic' ]

    # Map from expected but undefined code points, to where the char really is
    #
    exceptions = {
        0X02071: 0X000B9, # SUPERSCRIPT LATIN DIGIT ONE
        0X02072: 0X000B2, # SUPERSCRIPT LATIN DIGIT TWO
        0X02073: 0X000B3, # SUPERSCRIPT LATIN DIGIT THREE
        0X0245F: 0X24EA,  # CIRCLED DIGIT ZERO
        0x02488: None,    # DIGIT FULL STOP ZERO
        0X024F4: None,    # DOUBLE CIRCLED DIGIT ZERO
        0X02775: None,    # NEGATIVE CIRCLED DIGIT 0
        0X02789: None,    # [DINGBAT] CIRCLED SANS-SERIF 0
        #
        0X1D455: 0X210E,  # MATHEMATICAL ITALIC LOWER H (PLANCK CONSTANT)
        0X1D49D: 0X212C,  # MATHEMATICAL SCRIPT UPPER B
        0X1D4A0: 0X2130,  # MATHEMATICAL SCRIPT UPPER E
        0X1D4A1: 0X2131,  # MATHEMATICAL SCRIPT UPPER F
        0X1D4A3: 0X210B,  # MATHEMATICAL SCRIPT UPPER H
        0X1D4A4: 0X2110,  # MATHEMATICAL SCRIPT UPPER I
        0X1D4A7: 0X2112,  # MATHEMATICAL SCRIPT UPPER L
        0X1D4A8: 0X2133,  # MATHEMATICAL SCRIPT UPPER M
        0X1D4AD: 0X211B,  # MATHEMATICAL SCRIPT UPPER R
        0X1D4BA: 0X212F,  # MATHEMATICAL SCRIPT LOWER E
        0X1D4BC: 0X0261,  # MATHEMATICAL SCRIPT LOWER G
        0X1D4C4: 0X2134,  # MATHEMATICAL SCRIPT LOWER O
        0X1D506: 0X212D,  # MATHEMATICAL FRAKTUR UPPER C
        0X1D50B: 0X210C,  # MATHEMATICAL FRAKTUR UPPER H
        0X1D50C: 0X2111,  # MATHEMATICAL FRAKTUR UPPER I
        0X1D515: 0X211C,  # MATHEMATICAL FRAKTUR UPPER R
        0X1D51D: 0X2128,  # MATHEMATICAL FRAKTUR UPPER Z
        0X1D53A: 0X2102,  # MATHEMATICAL DOUBLE-STRUCK UPPER C
        0X1D53F: 0X210D,  # MATHEMATICAL DOUBLE-STRUCK UPPER H
        0X1D545: 0X2115,  # MATHEMATICAL DOUBLE-STRUCK UPPER N
        0X1D547: 0X2119,  # MATHEMATICAL DOUBLE-STRUCK UPPER P
        0X1D548: 0X211A,  # MATHEMATICAL DOUBLE-STRUCK UPPER Q
        0X1D549: 0X211D,  # MATHEMATICAL DOUBLE-STRUCK UPPER R
        0X1D551: 0X2124,  # MATHEMATICAL DOUBLE-STRUCK UPPER Z
    }

    # 'Start' is where the 'natural' range (a, alpha, 0) *would* be
    # 'Min' is where the inventory actually starts (usually 0, but 1 if no digit 0)
    # 'Max' is how many entries there are (including any displaced ones)
    # 'NExceptions' is how many entries are gaps with exceptions elsewhere.
    #
    unicodeLatins = {
        # Name                                            Start   Min Max NExceptions

        "Mathematical Bold Capital"                   : [ 0x1d400, 0, 26, 0 ],
        "Mathematical Bold Small"                     : [ 0x1d41a, 0, 26, 0 ],

        "Mathematical Italic Capital"                 : [ 0x1d434, 0, 26, 0 ],
        "Mathematical Italic Small"                   : [ 0x1d44e, 0, 26, 1 ], # h

        "Mathematical Bold Italic Capital"            : [ 0x1d468, 0, 26, 0 ],
        "Mathematical Bold Italic Small"              : [ 0x1d482, 0, 26, 0 ],

        "Mathematical Sans-serif Capital"             : [ 0x1d5a0, 0, 26, 0 ],
        "Mathematical Sans-serif Small"               : [ 0x1d5ba, 0, 26, 0 ],

        "Mathematical Sans-serif Bold Capital"        : [ 0x1d5d4, 0, 26, 0 ],
        "Mathematical Sans-serif Bold Small"          : [ 0x1d5ee, 0, 26, 0 ],

        "Mathematical Sans-serif Italic Capital"      : [ 0x1d608, 0, 26, 0 ],
        "Mathematical Sans-serif Italic Small"        : [ 0x1d622, 0, 26, 0 ],

        "Mathematical Sans-serif Bold Italic Capital" : [ 0x1d63c, 0, 26, 0 ],
        "Mathematical Sans-serif Bold Italic Small"   : [ 0x1d656, 0, 26, 0 ],

        "Mathematical Script Capital"                 : [ 0x1d49c, 0, 26, 8 ], # BEFHILMR
        "Mathematical Script Small"                   : [ 0x1d4b6, 0, 26, 3 ], # ego

        "Mathematical Bold Script Capital"            : [ 0x1d4d0, 0, 26, 0 ],
        "Mathematical Bold Script Small"              : [ 0x1d4ea, 0, 26, 0 ],

        "Mathematical Fraktur Capital"                : [ 0x1d504, 0, 26, 5 ], # CHIRZ
        "Mathematical Fraktur Small"                  : [ 0x1d51e, 0, 26, 0 ],

        "Mathematical Bold Fraktur Capital"           : [ 0x1d56c, 0, 26, 0 ],
        "Mathematical Bold Fraktur Small"             : [ 0x1d58c, 0, 26, 0 ],

        "Fullwidth Latin Capital"                     : [ 0x0FF21, 0, 26, 0 ],
        "Fullwidth Latin Small"                       : [ 0x0FF41, 0, 26, 0 ],

        "Parenthesized Latin Capital"                 : [ 0x1f110, 0, 26, 0 ],
        "Parenthesized Latin Small"                   : [ 0x0249c, 0, 26, 0 ],

        "Circled Latin Capital"                       : [ 0x024b6, 0, 26, 0 ],
        "Circled Latin Small"                         : [ 0x024d0, 0, 26, 0 ],

        "Mathematical Double-Struck Capital"          : [ 0x1d538, 0, 26, 7 ], # CHNPQRZ
        "Mathematical Double-Struck Small"            : [ 0x1d552, 0, 26, 0 ],

        "Mathematical Monospace Capital"              : [ 0x1d670, 0, 26, 0 ],
        "Mathematical Monospace Small"                : [ 0x1d68a, 0, 26, 0 ],

        # Capital only:
        "Negative Circled Latin Capital"              : [ 0x1f150, 0, 26, 0 ],
        "Negative Circled Latin Small"                : None,

        "Negative Squared Latin Capital"              : [ 0x1f170, 0, 26, 0 ],
        "Negative Squared Latin Small"                : None,

        "Squared Latin Capital"                       : [ 0x1f130, 0, 26, 0 ],
        "Squared Latin Small"                         : None,

        "Regional Symbol Letter Latin Capital"        : [ 0x1f1e6, 0, 26, 0 ],
        "Regional Symbol Letter Latin Small"          : None,

        ########## Unfinished:
        #"Superscript Latin Capital"                   : [],  # in
        #"Superscript Latin Small"                     : [],

        #"Subscript Latin Capital"                     : [],
        #"Subscript Latin Small"                       : [],  # aehijklmnoprstuvx
    }

    unicodeGreeks = {
        "Mathematical Greek Bold Capital"               : [ 0X1D6A8, 0, 26, 0 ],
        "Mathematical Greek Bold Small"                 : [ 0X1D6C2, 0, 26, 0 ],

        "Mathematical Greek Italic Capital"             : [ 0X1D6E2, 0, 26, 0 ],
        "Mathematical Greek Italic Small"               : [ 0X1D6Fc, 0, 26, 0 ],

        "Mathematical Greek Bold Italic Capital"        : [ 0X1D71C, 0, 26, 0 ],
        "Mathematical Greek Bold Italic Small"          : [ 0X1D736, 0, 26, 0 ],

        "Mathematical Greek Sans-serif Bold Capital"    : [ 0X1D756, 0, 26, 0 ],
        "Mathematical Greek Sans-serif Bold Small"      : [ 0X1D770, 0, 26, 0 ],

        # No Mathematical Greek Italic, apparently

        "Mathematical Greek Sans-serif Bold Italic Capital": [ 0X1D790, 0, 26, 0 ],
        "Mathematical Greek Sans-serif Bold Italic Small": [ 0X1D7Aa, 0, 26, 0 ],

        ########## Unfinished:
        #"Superscript Greek Small"                     : [],
        #"Subscript Greek Small"                       : [],
    }

    unicodeDigits = {
        "Mathematical Bold"                    : [ 0x1d7ce, 0, 10, 0 ],
        "Mathematical Double struck"           : [ 0x1d7d8, 0, 10, 0 ],
        "Mathematical Sans-serif"              : [ 0x1d7e3, 0, 10, 0 ],
        "Mathematical Sans-serif bold"         : [ 0x1d7ec, 0, 10, 0 ],
        "Mathematical Monospace"               : [ 0x1d7f6, 0, 10, 0 ],
        "Fullwidth"                            : [ 0x0FF10, 0, 10, 0 ],
        "Supercript"                           : [ 0x02070, 0, 10, 3 ],  # 123
        "Subscript"                            : [ 0x02080, 0, 10, 0 ],
        "Digit comma"                          : [ 0x1f101, 0, 10, 0 ],
        "Digit full stop"                      : [ 0x02488, 0, 20, 0 ],

        # Starting at 1 (but offset is to where zero *would* be)
        "Circled"                              : [ 0x0245f, 0, 20, 1 ],  # 0: U+024ea
        "Dingbat Negative Circled"             : [ 0x02775, 1, 10, 1 ],  # 0: U+024ff
        # 11 to 20 at U+24eb
        "Double Circled"                       : [ 0x024f4, 1, 10, 0 ],  # no 0
        "Dingbat Circled Sans-serif"           : [ 0x02789, 1, 10, 1 ],  # no 0
        "Dingbat Negative Circled Sans-serif"  : [ 0x02775, 1, 10, 0 ],  # no 0
        "Parenthesized"                        : [ 0x02473, 1, 20, 0 ],
    }

    digitSets = {
        # [ NAME                                 CODEPOINT MIN MAX MISSING ]
        'Mathematical bold DIGITS':            [ 0x1d7Ce, 0, 10,    0 ],
        'Mathematical double struck DIGITS':   [ 0x1d7d8, 0, 10,    0 ],
        'Mathematical sans serif DIGITS':      [ 0x1d7e2, 0, 10,    0 ],  # TODO: Cf above!!
        'Mathematical sans serif bold DIGITS': [ 0x1d7ec, 0, 10,    0 ],
        'Mathematical monospace DIGITS':       [ 0x1d7f6, 0, 10,    0 ],
        'fullwidth latin digits':              [ 0x0ff11, 0, 10,    0 ],
        'subscript latin digits':              [ 0x02080, 0, 10,    0 ],
        'superscript latin digits':            [ 0x02070, 0, 10,    0 ],

        'circled DIGITS':                      [ 0x02460, 1, 20,    1 ],
        'parenthesized DIGITS':                [ 0x02474, 1, 20, { 0: None, } ],
        'full stopped DIGITS':                 [ 0x02488, 1, 20, { 0: 0x1f100 } ],
        'DIGITS comma':                        [ 0x1f101, 0, 10,    0 ],
        'double circled DIGITS':               [ 0x024f5, 1, 50, { 0: None } ],
        'dingbat circled sans-serif DIGITS':   [ 0x02780, 1, 10, { 0: 0x1f10b, } ],
        'dingbat negative circled sans-serif DIGITS': [0x0278a,1,10, { 0: 0x1f10c, } ],
        'dingbat negative circled DIGITS':     [ 0x02776, 1, 10, { 0: 0x024ff } ],
        'negative circled DIGITS':             [ 0x024eb, 11, 20, { 0: 0x024ff } ],

        'FULLWIDTH DIGITS':                    [ 0x0ff10, 0, 10,    0 ],

        # circled number on black square 10-80 by 10 @ U+03248, 0 @ ????

        'arabic-indic DIGITS':                 [ 0x00660, 0, 10,    0 ],
        'extended arabic-indic DIGITS':        [ 0x006F0, 0, 10,    0 ],
        'nko DIGITS':                          [ 0x007c0, 0, 10,    0 ],
        'devanagari DIGITS':                   [ 0x00966, 0, 10,    0 ],
        'bengali DIGITS':                      [ 0x009e6, 0, 10,    0 ],
        'gurmukhi DIGITS':                     [ 0x00a66, 0, 10,    0 ],
        'gujarati DIGITS':                     [ 0x00aE6, 0, 10,    0 ],
        'oriya DIGITS':                        [ 0x00b66, 0, 10,    0 ],
        'tamil DIGITS':                        [ 0x00bE6, 0, 10,    0 ],
        'telugu DIGITS':                       [ 0x00c66, 0, 10,    0 ],
        'kannada DIGITS':                      [ 0x00cE6, 0, 10,    0 ],
        'malayalam DIGITS':                    [ 0x00d66, 0, 10,    0 ],
        'sinhala lith DIGITS':                 [ 0x00dE6, 0, 10,    0 ],
        'thai DIGITS':                         [ 0x00E50, 0, 10,    0 ],
        'lao DIGITS':                          [ 0x00Ed0, 0, 10,    0 ],
        'tibetan DIGITS':                      [ 0x00f20, 0, 10,    0 ],
        'MYANMAR DIGITS':                      [ 0x01040, 0, 10,    0 ],
        'MYANMAR SHAN DIGITS':                 [ 0x01090, 0, 10,    0 ],
        'KHMER DIGITS':                        [ 0x017e0, 0, 10,    0 ],
        'MONGOLIAN DIGITS':                    [ 0x01810, 0, 10,    0 ],
        'LIMBU DIGITS':                        [ 0x01946, 0, 10,    0 ],
        'NEW TAI LUE DIGITS':                  [ 0x019d0, 0, 10,    0 ],
        'TAI THAM HORA DIGITS':                [ 0x01a80, 0, 10,    0 ],
        'TAI THAM THAM DIGITS':                [ 0x01a90, 0, 10,    0 ],
        'BALINESE DIGITS':                     [ 0x01b50, 0, 10,    0 ],
        'SUNDANESE DIGITS':                    [ 0x01bb0, 0, 10,    0 ],
        'LEPCHA DIGITS':                       [ 0x01c40, 0, 10,    0 ],
        'OL CHIKI DIGITS':                     [ 0x01c50, 0, 10,    0 ],
        'IDEOGRAPHIC NUMBER':                  [ 0x03007, 0, 10,    0 ],
        'VAI DIGITS':                          [ 0x0a620, 0, 10,    0 ],
        'SAURASHTRA DIGITS':                   [ 0x0a8d0, 0, 10,    0 ],
        'COMBINING DEVANAGARI DIGITS':         [ 0x0a8e0, 0, 10,    0 ],
        'KAYAH LI DIGITS':                     [ 0x0a900, 0, 10,    0 ],
        'JAVANESE DIGITS':                     [ 0x0a9d0, 0, 10,    0 ],
        'CHAM DIGITS':                         [ 0x0aa50, 0, 10,    0 ],
        'MEETEI MAYEK DIGITS':                 [ 0x0abf0, 0, 10,    0 ],

        'roman numerals':                      [ 0x02160, 1, 12,    0 ],
        'small roman numerals':                [ 0x02170, 1, 12,    0 ],

        'playing cards, spades':               [ 0x1f0a1, 1, 10,    0 ],
        'playing cards, hearts':               [ 0x1f0b1, 1, 10,    0 ],
        'playing cards, diamonds':             [ 0x1f0c1, 1, 10,    0 ],
        'playing cards, clubs':                [ 0x1f0d1, 1, 10,    0 ],

        'mahjong tiles, characters':           [ 0x1f007, 1, 10,    0 ],
        'mahjong tiles, bamboos':              [ 0x1f010, 1, 10,    0 ],
        'mahjong tiles, circles':              [ 0x1f019, 1, 10,    0 ],
    } # digitSets


    ###########################################################################
    # Maybe make init take a target spec, then convert() uses it...
    #
    def __init__(self):
        return

    @staticmethod
    def getLatinStartCodePoint(scriptName):
        if (scriptName in mathUnicode.unicodeLatins):
            return mathUnicode.unicodeLatins[scriptName][0]

    @staticmethod
    def getGreekStartCodePoint(scriptName):
        if (scriptName in mathUnicode.unicodeGreeks):
            return mathUnicode.unicodeGreeks[scriptName][0]

    @staticmethod
    def getDigitStartCodePoint(scriptName):
        if (scriptName in mathUnicode.unicodeDigits):
            return mathUnicode.unicodeDigits[scriptName][0]

    @staticmethod
    def convert(ss, scriptName="Latin",
        targetName='Circled Latin Capital'):
        print("In convert, scriptName=%s, targetName=%s." %
            (scriptName, targetName))
        xtab = mathUnicode.getTranslateTable(scriptName, targetName)
        return ss.translate(xtab)

    @staticmethod
    def getTranslateTable(scriptName, targetName):
        #if (PY3):
        #    raise NotImplementedError("No maketrans in Python 3.")
        if (scriptName == 'Latin'):
            tbl = mathUnicode.unicodeLatins
            fromStart = ord('a')
            fromEnd = ord('z')
        elif (scriptName == 'Greek'):
            tbl = mathUnicode.unicodeGreeks
            # There's also latin alpha at U+0251, U+1d90, etc.
            fromStart = 0x03b1  # cap = 0x0391
            # There's also latin and cyrillic omegas
            fromEnd = 0x03c9  # cap = 03a9
        elif (scriptName == 'Digit'):
            tbl = mathUnicode.unicodeDigits
            fromStart = ord('0')
            fromEnd = ord('9')
        else: raise ValueError(
        "Unknown scriptName '%s', must be Latin|Greek|Digit." % (scriptName))

        if (targetName not in tbl):
            raise ValueError(
        "Unknown targetName '%s' for script '%s'." % (targetName, scriptName))

        ustart, umincp, uncp, unExceptions = tbl[targetName]
        fr = to = u""
        toCode = ustart
        for frCode in range(fromStart, fromEnd):
            fr += unichr(frCode)
            to += unichr(toCode)
            toCode += 1
        xtab = str.maketrans(fr, to)
        return xtab


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    def anyInt(x):
        return int(x, 0)

    def processOptions():
        import argparse
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--digits",           action='store_true',
            help='List the digit alternates.')
        parser.add_argument(
            "--greeks",           action='store_true',
            help='List the Greek alternates.')
        parser.add_argument(
            "--latins",           action='store_true',
            help='List the Latin alternates.')
        parser.add_argument(
            "--missing",          type=anyInt, default=0x2623,
            help='Show this code point for undefined characters. Default: biohazard.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--sample",           type=str, default=None,
            help='Sample text to convert (see also --to).')
        parser.add_argument(
            "--to",               type=str,
            default='Circled Latin Capital',
            help='Character variant to convert to (see also --sample).')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        args0 = parser.parse_args()
        if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)


    messageIssued = False

    def showAlternates(altList, MISSING=26):
        global messageIssued
        for k in (sorted(altList.keys())):
            if (altList[k] is None):
                print("    %-50s    DOES NOT EXIST" % (k))
                continue
            try:
                start, mincp, ncp, nExceptions = altList[k]
            except TypeError as e:
                print("******* Error on '%s':\n    %s" % (k, e))
                continue
            print("    %-50s U+%04x..." % (k, start))
            if (not args.verbose): continue
            try:
                buf = ""
                for i in range(mincp, ncp):
                    codePoint = start + i
                    if (codePoint in mathUnicode.exceptions):
                        codePoint = mathUnicode.exceptions[codePoint]
                        if (codePoint is None): codePoint = MISSING
                    buf += " %s " % (unichr(codePoint))
                print(buf)
            except ValueError:
                if (not messageIssued): print(
                    "    ******* Out of unichr() range *******")
                messageIssued = True

    # See https://en.wikipedia.org/wiki/Pangram
    #
    sentences = [
        "Sphinx of black quartz, judge my vow",
        "Jackdaws love my big sphinx of quartz",
        "Pack my box with five dozen liquor jugs",
        "The quick onyx goblin jumps over the lazy dwarf",
        "Cwm fjord bank glyphs vext quiz",
        # = "Symbols in a mountain hollow on the bank of an inlet
        # vexed an eccentric person."
        "How razorback-jumping frogs can level six piqued gymnasts!",
        "Cozy lummox gives smart squid who asks for job pen",
        "Amazingly few discotheques provide jukeboxes",
        "'Now fax quiz Jack!', my brave ghost pled",
        "Watch Jeopardy!, Alex Trebek's fun TV quiz game.",
        "Jived fox nymph grabs quick waltz.",
        "Glib jocks quiz nymph to vex dwarf.",
        "How vexingly quick daft zebras jump!",
        "The five boxing wizards jump quickly.",
        "Mr Jock, TV quiz PhD, bags few lynx",
    ]

    def getRandomSentence():
        import random
        return random.choice(sentences)

    ###########################################################################
    #
    args = processOptions()

    if (not (args.latins or args.greeks or args.digits)):
        args.latins = True

    messageIssued = False
    if (args.latins):
        print("Available alts for Latin:")
        showAlternates(mathUnicode.unicodeLatins, args.missing)
    if (args.greeks):
        print("Available alts for Greek:")
        showAlternates(mathUnicode.unicodeGreeks, args.missing)
    if (args.digits):
        print("Available alts for Digits:")
        showAlternates(mathUnicode.unicodeDigits, args.missing)

    if (args.to):
        args.script = "Latin"
        args.to = args.to.title()
        print("\nSample conversion for %s '%s':" % (args.script, args.to))
        if (args.sample is None):
            args.sample = getRandomSentence()
        s = mathUnicode.convert(args.sample,
            scriptName=args.script, targetName=args.to)
        print(args.sample + "\n" + s)
    sys.exit()
