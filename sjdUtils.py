#!/usr/bin/env python3
#
# sjdUtils: some generally useful stuff.
#
from __future__ import print_function
import sys
import os
import re
import argparse
import random
import time
import math

import ColorManager
from alogging import ALogger

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring # noqa: F821
else:
    string_types = str
    def xrange(x): return iter(range(x))
    def cmp(a, b): return ((a > b) - (a < b))
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'):
        return str(s, encoding, errors)

__metadata__ = {
    'title'        : "sjdUtils",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2011-12-09",
    'modified'     : "2020-08-20",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Provide some very basic useful utilities, mostly for escaping, colorizing,
timing, and handling error messages.

    from sjdUtils import sjdUtils
    su.setVerbose(level)
    ...
    su = sjdUtils()
    su.setColors(useColor)
    ...

Messaging support is now in `alogging`, which works a lot like Python's
`logging.Logger`, but has nicer layout (I think), support for -v levels,
statistics, color, and a simpler (although much less flexible) structure:

    from alogging import ALogger   # For messaging/logging features
    lg = ALogger(1)
    lg.warn(msg)
    lg.vMsg(args.verbose, msg)
    lg.vIndent()
    ...

A nearly identical `sjdUtils.pl` is also available for Perl.


=Methods=

==General methods==

* '''sjdUtils'''(verbose=0, colors=False)

Constructor.

* '''getOption''' ''(name)''
Get the value of option ''name'', from the list below.
Returns `None` if you try to get an unknown option.

* '''setOption''' ''(name, value)''
Set option ''name'', from the list below, to ''value''.

* '''setVerbose''' ''(value)''
Tell the logger to set its level of reporting to ''value'' (higher=more).

* '''getVerbose''' ''()''
Return the logger's level of reporting.


** Option: ''colorEnabled''
Globally enables/disables use of color.
Scripts may wish to set this to True if environment variable ''CLI_COLOR'' is
set and the relevant output is going to a terminal.
See also the ''setColors''() method, below.

** Option: ''defaultEncoding''
Set the name of the character encoding to be used when not otherwise specified.

** Option: ''loremText'' (string)
The text to be returned by ''lorem(type='a')''.
Default: the usual ''lorem ipsum...''.


==XML-related methods==

=* '''indentXml'''(s, iString="  ", maxIndent=0, breakAttrs=0, elems={}, html=False)

Re-flow the XML string ''s'' to outline form, using repetitions of ''iString''
to create indentation (up to a maximum of ''maxIndent'' levels.
If ''breakAttrs'' is true, put each attribute on a separate line, too.

''elems'' is a dictionary that maps each element type name to either
`block` or `indent`, and affects line-breaking accordingly.

* '''indentXML''' -- synonym for '''indentXml'''.

* '''colorizeXmlTags(s, color="")'''
Surround XML markup with ANSI terminal escapes to display it
in the specified color. Default: the color for the "x" message type.
See also the ''ColorManager'' class, described below.

* '''colorizeXmlContent(s, color="")'''
Surround XML content (not markup) with ANSI terminal codes to display
it in the specified color. Default: the color for the "x" message type.

''See XmlRegexes packge for relevant 'isa' functions for character classes.''


==JSON-related methods==

* '''indentJson(s, iString="    ", maxIndent=0)'''
Like ''indentXml'', but for JSON.


==Simple string-formatting methods==

* '''rpad(s, width=0, padChar=" ", quoteChar="")'''

Like Python's ljust(), but can also quote before padding.
If ''quoteChar'' is specified, its first character is used as the
opening quote, and its last character as the closing quote.

* '''lpad(s, width=0, padChar="0", quoteChar="")'''

Like Python's rjust(), but can also quote before padding.
If ''quoteChar'' is specified, its first character is used as the
opening quote, and its last character as the closing quote.

* '''lpadc(s, width=0, padChar="0", quoteChar="", sepChar=",")'''

Like ''lpad'', but also inserts ''sepChar''s every three digits
(Python 3 has that feature in ''format'').
If ''quoteChar'' is specified, its first character is used as the
opening quote, and its last character as the closing quote.

 ''sepChar'' now accepts a few special values as well. If set to "COLOR"
(and color is enabled), alternate groups of three digits will be colorized
(presently just red). If "UNDER", they will be underlined (again assuming
color is enabled and the terminal supports it).

* '''align(list, delim=',', stripTrail=True, maxLen=None, padChar=' ')'''

Aligns the tokens or items within each member of ''list'' so they print
out in neat columns (assuming a monospace font).

'list' must be an array; either of (sub)-lists or of strings that can be
split into (sub-)lists using ''delim''.

For each "column" (going down 'mylist' and taking the nth item
in each (sub-)list, ''align()'' finds the max length that occurs.
Then it all the items in each column to that column's max length.
Finally, it assembles the items of each (sub-)list, separated by ''delim''
into a string. It returns a list of those (padded) strings.

If a column contains any non-numeric entries, then its values will all
be quoted (with double-quotes), and left-justified. Otherwise, its value
will be unquoted and right-justified.

'''Note''': There is no provision for ignoring instances of ''delim''
if they are in quotes, backslashed, etc.

* '''toHNumber(n, base=1000)'''

Convert a number to human-readable form, like several *nix commands.
For example, "123456789" would become "123.45M".
This conversion generally loses precision.
Base must be 1000 or 1024.

* '''fromHNumber(n, base=1000)'''

Convert a number from human-readable form, the opposite of ''toHNumber''.
For example, "123M" would become "123000000".
Base must be 1000 or 1024.

* '''unquote(s, fancy=False)'''

Remove single or double quotes from around a string, if present.
A quote all by itself (such as ''"''), remains.
Polarized quotes must match up properly.
Deals with most but not all Unicode quotes. Mainly, it's not clear what to
do with:

    U+201a   'SINGLE LOW-9 QUOTATION MARK',
    U+201b   'SINGLE HIGH-REVERSED-9 QUOTATION MARK',
    U+2032 - U+2037
    U+275f   'HEAVY LOW SINGLE COMMA QUOTATION MARK ORNAMENT',
    U+2760   'HEAVY LOW DOUBLE COMMA QUOTATION MARK ORNAMENT',

* '''quote(s, curly=False, escape='\\')'''

Return ''s'' with a double-quote character (U+0022) added on each end.
If ''escape'' is some character E, first put E before each instance
of U+0022 in ''s''.
If ''curly'' is True, use curly quotes (U+201c and U+201d) instead of straight.
Other quote types are not currently supported, and curly ones are not
escaped by ''escape''.


==Unicode stuff==

If running in Python 3, it defines `unichr` to just be `chr` so it
still works.

* '''isUnicodeCodePoint'''(c)

Return whether the character is a valid Unicode code point.
This isn't terribly smart yet.

* '''strip_accents'''(s)

Remove diacritics from the string ''s''. This is done by normalizing ''s''
to "NFD" (thus separating diacritics from their base character
 ''where possible'', and then stripping non-spacing marks. This does not
convert things like "LATIN SMALL LETTER L WITH STROKE", however.

* '''[Useful constants]'''

The following variables are Unicode strings containing the relevant characters:

** '''UQuotes''' -- All quotation-mark characters

** '''ULSQuotes''' -- Left single quotes

** '''ULDQuotes''' -- Left double quotes

** '''ULQuotes''' -- Left quotes

** '''URSQuotes''' -- Right single quotes

** '''URDQuotes''' -- Right double quotes

** '''URQuotes''' -- Right quotes


==Miscellaneous methods==

* '''isNumeric()'''

* '''isInteger()'''


==Escaping methods==

* '''getUTF8'''

* '''showControls'''

Turn C0 control characters into their Unicode "Control Pictures" (tiny
mnemonics, at U+2400 and following).

* '''showInvisibles or vis'''

Many unprintable character visible.

* '''escapeRegex'''

Backslash regex metacharacters in a string.

* '''escapeXmlContent''' or '''escapeXml''' or '''escapeXmlText'''.

Turn '<', '&', and the '>' in ']]>' into '&lt;', '&amp;', and '&gt;' instead.

* '''escapeXmlAttribute'''

Turn '<', '&', and '"' into '&lt;', '&amp;', and '&quot;' instead.
You can set `apostrophes=True` if you also want to convert "'" to '&apos;'.

* '''escapeXmlPi'''

Turn "?>" into "?&gt;". XML does not define a particular way to represent '?>'
within processing instructions, but you have to escape it somehow....
You can set `target=[string]` to something else if you prefer.
At least at the moment, this also nukes any non-XML control characters.

* '''escapeXmlComment'''

Turns "--" into em dash (U+2014). XML does not define how to represent '--'
within comments, but you have to escape it somehow....
You can set `target=[string]` to something else if you prefer.

* '''normalizeXmlSpace(s)'''

Normalize whitespace per XML definition. This affects Python (non-Unicode) \\s.

* '''expandXml(s)'''

Expand any special-character references in ''s''.
This uses the Python `HTMLParser` package's "unescape()" method.

* '''backslash(s)'''

Put a backslash before each t, r, n, t, and \\ within ''s''.
In addition, replace non-ASCII characters with backslash + xXX or uXXXX
(depending on whether their numeric value fits in 2 hexadecimal digits or not).

* '''unbackslash(s)'''

Unescapes (converts) backslash-codes within ''s'' to literal characters.
Handles [abefnrt\\], as well as 0777, xFF, and uFFFF styles.

* '''escapeURI(s)'''

Turn ASCII characters prohibited in URIs, into %FF style.
'''Warning''': May not work for Unicode yet.

* '''unescapeURI(s, escapeChar='%')'''

Replace %FF style escapes (as used in URIs) with literal characters.
You can change ''escapeChar'' to use it for other things, like '=' for MIME.
'''Warning''': May not work for Unicode yet.


==Other (miscellaneous) methods==

* '''isoDateTime(t?)'''

Returns the present date and time in (one) ISO format, 19 characters long.
Example: 2011-11-30T23:22:05.

* '''isoDate(t?)'''
Returns the date portion of isoDateTime. Example: 2011-11-30.

* '''isoTime(t?)'''

Returns the time portion of isoDateTime. Example: 23:22:05.

* '''elapsedTime(start, end?, seconds=False)'''

Returns the difference between ''start'' and ''end'', which should be values
directly from ''time()'' (not returned values from ''isoTime'', for example).
The elapsed time is in the form `hh:mm:ss` unless
 ''seconds'' is True, in which case you just get the raw number of seconds.

* '''lorem(length=79, loremType="a", mode='frequency', xtab=None)'''

Return some sample text of a given type and length. The `loremType` are:
    a -- ASCII text, by detault the usual "lorem ipsum", but you can set a
different text via the `loremText` option.
    r -- Randomly generated ASCII text (see ''randomChar''(), below)

`randomizeChars`, `unicodeMin`, and `unicodeMax` can be set, for cause ASCII vowels randomly changes some of the characters to various non-Latin-1 ones.

`mode` is simply passed on to `randomChar()` when loremType="r".

`xtab` can be a translation table, that will be applied to the generated text.
See also `getRandomXtab()`.

* '''getRandomXtab(fromChars='aeiouAEIOU', uMin=0x00A1, uMax=0x2FF)'''

Generate a translation table, mapping each of the `fromChars` to a random
Unicode character in the specified inclusive range.

All code points seem to be assigned in at least these ranges:
    0x00A1 to 0x2FF  Latin
    0x0400 to 0x52F  Cyrillic
    0x2200 to 0x23F3 Math ops and technical
    0x3041 to 0x3096 Hiragana


* '''randomChar(rgen=random.Random(), mode='uniform')'''

Generates a single random character (used by ''lorem(type='r')'')

If ''mode'' is `frequency`, ASCII lowercase letters and space are generated,
in accordance with approximate probabilities in English text.
Option `letterFreqs` holds a dictionary of char->frequencies.
The keys include 26 lower-case letters, plus space.

If ''mode'' is `uniform`, ASCII printable characters are generated,
with uniform probabilities.

* '''availableFileNum'''(base, width=4, min=1, max=1000, sep='', which='free')

Find a filename from a numbered series. ''base'' is split into path, filename,
and extension. Candidate filenames are of the form:

    path + '/' + filename + sep + number + '.' + extension

except that, if there was no extension in ''base'', the final '.' + extension
will not be included. ''number'' must be exactly ''width'' digits
(with extra zeros on the left as needed).

The script will look for existing files whose names match this pattern
(shell globs are not supported!).
What filename is then returned, depends on the ''which'' parameter:

** '''next''': the file with number one greater than the
last extant file, is returned. '''Warning''': If this overflows into
the ''width''+1st digit, the longer name is quietly returned.

** '''firstfree''': the first such filename that does not
exist is returned. There could be additional files with greater numbers.

** '''lastappend''': the last existing file if
it is appendable, otherwise the first such file that does not exist.

* '''Note''': On many file systems, directories with more than about 1000 files
in them get really slow. This method is still experimental.
See also the `incrementFilename.py` command.


=The ColorManager class=

This is a separate class defined in `ColorManager.py`,
to make it easy to manage ANSI terminal color escape sequences.
Its methods
are also patched in to `sjdUtils.py`, so when color is enabled you can just
call them as if they were methods of `sjdUtils.py` itself.

The color names available are defined in `bingit/SHELL/colorNames.pod`,
which supercedes anything in specific scripts (although they ''should'' match).

A dictionary of the usable names is in `colorStrings`; a printable
form can be retrieve via ''getColorStrings()'', or a printable list
via ''tostring()''.

* '''__init__(effects=None)'''

Set up the color manager. ''effects'' is merely passed down to
 ''setupColors()''.

* '''setupColors(effects=None)'''

(iternal) Work out all known color, effect, and combination names, and
put them in a hash that maps them to their escape sequences.
If 'effects' is not None, it must be a list of the effect names
to include. That list may be empty.

* '''addColor(newName, oldName)'''

Adds a synonym for an existing color.

* '''isColorName(name)'''

Returns True iff ''name'' is a known color name.

* '''getColorString(name)'''

* '''getColorStrings(paramColor, defaultColor)'''

* '''tostring(sampleText='sample', filter=None)'''

Return a printable buffer with one line for each defined color name.
Each line consist of colorized ''sampleText'' and then the color name.

If ''filter'' is supplied, it is treated as a regular expression, and any
color names that do not match it are excluded. This is useful because
there are about 1000 combinations available.

* '''colorize(argColor='red', s="", endAs="off")'''

Return ''s'', but with the ANSI terminal escape to display it in the specified
 ''argColor'' added at the start, and the escape to switch to color ''endAs''
added at the end.

* '''uncolorize''' ''(s)''

Remove any ANSI terminal color escapes from ''s'' (via `ColorManager.py`).
Also available as standalone Python script `uncolorize`.

* '''uncoloredLen''' ''(s)''

Return the length of ''s'', but ignoring any ANSI terminal color strings.
This is just shorthand for `len(uncolorize(s))`.


=Known bugs and limitations=

If you ''colorize''() a string, it resets the color to default at the end.
Thus, if you insert colorized string A within colorized string B, the portion
of B following A will ''not'' be colorized.
You can specify the ''endAs'' option when colorizing A to avoid this.

Some method names could be better.

Randomly-generated text should be more flexible: mixed-case, Markov generator....
But may not be useful enough to keep around anyway.

Human-readable numbering should also support factors of 1024.

ColorManager has no support for 256-color terminals.

showControls seems unhappy with CR (0x0D).

escaping calls aren't testing well at the moment.

indentJSON should use strip() or similar.

=To do=

* Add colorizing option to lpadc?
* Resync Perl version.

=History=

* 2011-12-09: Port from Perl to Python by Steven J. DeRose.
* 2012-01-09 sjd: Sync port.
* 2012-01-24 sjd: Make into an actual class; globals too hard otherwise.
* 2012-01-30 sjd: Fix color escapes.
* 2012-02-24 sjd: Add calls to 'inspect' to report error locations.
* 2012-02-27 sjd: Add getVerbose(), text arg to _warn methods. Add warn().
Generalize message types.
* 2012-04-11 sjd: Sync with Perl version.
* 2012-11-01 sjd: Add indentJson(). Drop targetFile. Add vMsg, etc.
* Sync more w/ Perl version: xml type checks,....
* 2012-11-07 sjd: Fixing isoTime().
* 2012-11-19 sjd: Fix escapeURI().
* 2013-03-04 sjd: Add vPush(), vPop().
* 2013-03-25 sjd: Implement vDepth indenting, add pline().
* 2013-06-28 sjd: Partial sync w/ Perl version.
* 2014-04-22: Add getVerbose. Fix SUset for 'verbose'. Sync msgTypes w/ Perl.
Fiddle with messaging.
* 2014-06-09ff: Improve indentJson. Add synonym indentJSON, availableFileNum.
* 2014-06-1f: Improve availableFileNum.
* 2014-07-01: Add setOption/getOption synonym, clean up traceback a little.
* 2014-07-17: Fix colorEnabled. Sync vPush() etc. w/ Perl version.
* 2014-09-05: Add toUTF8(), handle unicode messages, add types for lorem().
* 2014-12-17: Add 'stat' parameter to eMsg, vMsg, hMsg, Msg to keep count of
named statistics. Also add bumpStat(), getStat(), showStatS().
* 2015-01-15f: Improve stats handling/escaping. Add appendStat(), expandXml().
* 2015-03-26: Clean up defineMsgType(). Add 'infix' argument for messages.
* 2015-07-27: Add Python logger-like message calls, with fill-ins.
* Add uncoloredLength, make pline() ignore color escapes.
* 2015-10-13f: Move messaging support into separate 'alogging' package,
* which has been ported to sit on top of Python's 'logging' package.
Split color to internal class. Add XMLExprs() class.
Add quote/unquote methods. Remove teefile option. Implement try_module().
Write unit tests and fix several bugs. Add HNumber 'base' arg.
* 2016-09-09: Add strip_accents().
* 2016-10-04: Move more stuff into XmlRegexes class (nee XMLExprs).
* 2016-10-31: Move ColorManager out to be a separate package.
* 2016-12-13: Add align().
* 2018-01-11: Move XmlRegexes out to separate package.
* 2018-03-20: Don't die if ColorManager not available.
* 2018-08-16: Keep unichr() defined even in Python 3.
* 2018-09-25ff: Clean up more PY 2 vs. 3 details.
* 2018-10-05: add className()
* 2018-11-27: Add splitPlus().
* 2020-01-22: Move doc, POD->MarkDown, lint, metadata.
* 2020-08-27: unbackslash() for both Python 2 and 3.
* 2020-09-03: Add shrinkuser().

=Rights=

Copyright 2011, Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0/].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].

=Options=
"""

# Provide way to get class-name regardless of old/new, 2/3
# Old-style classes have type 'instance', kinda pointless.
# See https://stackoverflow.com/questions/510972/
#
def className(obj):
    return obj.__class__.__name__

# Both:
#    from html.parser import HTMLParser
#    from io import open
#    from builtins import chr
#


###############################################################################
# Useful sets of Unicode characters
#
UQuotes = (
    unichr(0x0022) +  # 'QUOTATION MARK'
    unichr(0x0027) +  # 'APOSTROPHE'
    unichr(0x301f) +  # 'LOW DOUBLE PRIME QUOTATION MARK'
    unichr(0xff02) +  # 'FULLWIDTH QUOTATION MARK'
    unichr(0xff07) +  # 'FULLWIDTH APOSTROPHE'
    ""
)
ULSQuotes = (
    unichr(0x2018) +  # 'LEFT SINGLE QUOTATION MARK',
    #unichr(0x201a) +  # 'SINGLE LOW-9 QUOTATION MARK',
    #unichr(0x201b) +  # 'SINGLE HIGH-REVERSED-9 QUOTATION MARK',
    # 2032 - 2037 ??? FIX ???
    unichr(0x2039) +  # 'SINGLE LEFT-POINTING ANGLE QUOTATION MARK',
    unichr(0x275b) +  # 'HEAVY SINGLE TURNED COMMA QUOTATION MARK ORNAMENT',
    #unichr(0x275f) +  # 'HEAVY LOW SINGLE COMMA QUOTATION MARK ORNAMENT',
    unichr(0x276e) +  # 'HEAVY LEFT-POINTING ANGLE QUOTATION MARK ORNAMENT',
    ""
)
ULDQuotes = (
    unichr(0x00ab) +  # 'LEFT-POINTING DOUBLE ANGLE QUOTATION MARK',
    unichr(0x201c) +  # 'LEFT DOUBLE QUOTATION MARK',
    unichr(0x201e) +  # 'DOUBLE LOW-9 QUOTATION MARK',
    unichr(0x275d) +  # 'HEAVY DOUBLE TURNED COMMA QUOTATION MARK ORNAMENT',
    #unichr(0x2760) +  # 'HEAVY LOW DOUBLE COMMA QUOTATION MARK ORNAMENT',
    unichr(0x301d) +  # 'REVERSED DOUBLE PRIME QUOTATION MARK',
    ""
)
ULQuotes = ULSQuotes + ULDQuotes

URSQuotes = (
    unichr(0x2019) +  # 'RIGHT SINGLE QUOTATION MARK',
    unichr(0x203a) +  # 'SINGLE RIGHT-POINTING ANGLE QUOTATION MARK',
    unichr(0x275c) +  # 'HEAVY SINGLE COMMA QUOTATION MARK ORNAMENT',
    unichr(0x276f) +  # 'HEAVY RIGHT-POINTING ANGLE QUOTATION MARK ORNAMENT',
    ""
)
URDQuotes = (
    unichr(0x00bb) +  # 'RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK',
    unichr(0x201d) +  # 'RIGHT DOUBLE QUOTATION MARK',
    unichr(0x201f) +  # 'DOUBLE HIGH-REVERSED-9 QUOTATION MARK',
    unichr(0x275e) +  # 'HEAVY DOUBLE COMMA QUOTATION MARK ORNAMENT',
    unichr(0x301e) +  # 'DOUBLE PRIME QUOTATION MARK',
    ""
)
URQuotes = URSQuotes + URDQuotes

char2escape = {
    "\a"   : "\\a",  # bell
    "\b"   : "\\b",  # backspace
    #"\e"   : "\\e",  # escape
    "\f"   : "\\f",  # form feed
    "\n"   : "\\n",  # line feed
    "\r"   : "\\r",  # carriage return
    "\t"   : "\\t",  # tab
    "\\"   : "\\\\", # backslash
    }
spaceCodes = {
    "SP"       : unichr(0x2420), # SP
    "B"        : unichr(0x2422), # B/
    "U"        : unichr(0x2423), # _
    "OK"       : ' ',
    "NBSP"     : unichr(0x00A0), # Non-breaking space
    }
lfCodes = {
    "LF"       : unichr(0x240A),
    "NL"       : unichr(0x2424),
    "OK"       : "\n",
    }


# See http://stackoverflow.com/questions/517923
#
import unicodedata
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

#straightenSingles = unicode.maketrans(
#    ULQuotes+URQuotes, "'" * (len(ULQuotes)+len(URQuotes)))
#straightenDoubles = unicode.maketrans(
#    ULQuotes+URQuotes, '"' * (len(ULQuotes)+len(URQuotes)))


###############################################################################
# Functions used on RHS of regex changes
#
def UEscapeFunction(mat):
    return("\\u%04x;" % (ord(mat.group(1))))
def controlSymbolsFunction(mat):
    return(unichr(0x2400 + ord(mat.group(1))))
def escHexFn(m):
    utf = m.group(1).encode('utf-8')
    buf = ""
    for byt in utf: buf += "_%02x" % (ord(byt))
    return(buf)
def unescFn(m):
    return(chr(hex(m.group(1))))


###############################################################################
#
class sjdUtils:
    """A variety of low-level utilities used by many of my scripts.
    Includes pretty-printing XML and JSON, times and dates, lorem text,
    escaping and unescaping special characters, etc.
    """
    def __init__(self, verbose=0, colors=1, logger=None, old=True):
        self.version        = __version__
        self.localeInfo     = None
        self.htmlp          = None
        self.lg             = logger or ALogger(1)
        # Define some of the logger's methods locally, for backward
        # compatibility:
        if (old):
            self.vMsg           = self.lg.vMsg
            self.hMsg           = self.lg.hMsg
            self.eMsg           = self.lg.vMsg

        self.lg             = logger or ALogger(1)
        self.showStats      = self.lg.showStats

        # Init some extra color stuff:
        self.colorManager   = None
        self.addColor = None
        self.getColorString = None
        self.getColorStrings = None
        self.tostring = None
        #self.colorize = None
        #self.uncolorize = None
        self.uncoloredLen = None

        self.options = {
            "colorEnabled": 0,   # Using terminal color?
            "loremText": (       # Traditional filler text
            "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do "
            + "eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            + "Ut enim ad minim veniam, quis nostrud exercitation ullamco "
            + "laboris nisi ut aliquip ex ea commodo consequat. "
            + "Duis aute irure dolor in reprehenderit in voluptate "
            + "velit esse cillum dolore eu fugiat nulla pariatur. "
            + "Excepteur sint occaecat cupidatat non proident, sunt in "
            + "culpa qui officia deserunt mollit anim id est laborum."
            ),
            "letterFreqs" : []
        }

        # See loremText(type='r'), below.
        # See also Charsets/letterFrequencies.py.
        #
        self.letterFreqsTotal = 0  # setUtilsOption() sets this.
        self.setUtilsOption("letterFreqs", [ # Rough, from Wikipedia
            ('e',   12702),
            (' ',   17000), # Estimate for non-word chars
            ('t',    9056),
            ('a',    8167),
            ('o',    7507),
            ('i',    6966),
            ('n',    6749),
            ('s',    6327),
            ('h',    6094),
            ('r',    5987),
            ('d',    4253),
            ('l',    4025),
            ('c',    2782),
            ('u',    2758),
            ('m',    2406),
            ('w',    2360),
            ('f',    2228),
            ('g',    2015),
            ('y',    1974),
            ('p',    1929),
            ('b',    1492),
            ('v',     978),
            ('k',     772),
            ('j',     153),
            ('x',     150),
            ('q',      95),
            ('z',      74)
          ])

        self.multipliers = [
            # Suf  1000    1024   Name
            ( "K", 1E+3,  1<<10, "Kilo" ),  # Karl
            ( "M", 1E+6,  1<<20, "Mega" ),  # Marx
            ( "G", 1E+9,  1<<30, "Giga" ),  # gave
            ( "T", 1E12,  1<<40, "Tera" ),  # the
            ( "P", 1E15,  1<<50, "Peta" ),  # people
            ( "E", 1E18,  1<<60, "Exa" ),   # eleven
            ( "Z", 1E21,  1<<70, "Zetta" ), # zeppelins,
            ( "Y", 1E24,  1<<80, "Yotta" ), # yo!
        ]

        self.unescape           = re.compile(r'_[0-9a-f][0-9a-f]')
        self.setColors(colors)
        self.setVerbose(verbose)
        return(None)

    def getLogger(self):
        """At least for now, just have one logger via sjdUtils.
        """
        return(self.lg)

    def setColors(self, enabled):
        """Set up or take down the ColorManager package.
        Monkey-patch keys methods so they're easily available from here.
        """
        haveColorManager = self.try_module('ColorManager')
        if (not haveColorManager): return

        if (not enabled):
            self.addColor = None
            self.getColorString = None
            self.getColorStrings = None
            self.tostring = None
            self.uncoloredLen = None
            self.colorManager = None
            self.options['colorEnabled'] = False
        else:
            self.colorManager = ColorManager.ColorManager()
            self.addColor = self.colorManager.addColor
            self.getColorString = self.colorManager.getColorString
            self.getColorStrings = self.colorManager.getColorStrings
            self.tostring = self.colorManager.tostring
            self.uncoloredLen = self.colorManager.uncoloredLen
            self.options['colorEnabled'] = True
        return

    def getColorManager(self):
        return(self.colorManager)

    def colorize(self, argColor='red', s="", endAs="off"):
        if (not self.colorManager): return s
        return self.colorManager.colorize(argColor, s, endAs)

    def uncolorize(self, s):
        if (not self.colorManager): return s
        return self.colorManager.uncolorize(s)


    ###########################################################################
    # Options
    #
    def setUtilsOption(self, name, value=1):
        return(self.setOption(name, value))
    def setOption(self, name, value=1):
        """Set option `name`, from the list below, to `value`.

        * Option: `colorEnabled`

        Globally enables/disables use of color.
        Script may wish to set this to True if environment variable `CLI_COLOR` is
        set and the relevant output is going to a terminal.
        See also the `setColors()` method, below.

        * Option: defaultEncoding

        Set the name of the character encoding to be used when not otherwise specified.

        * Option: loremText (string)

        The text to be returned by lorem(type='a').
        Default: the usual lorem ipsum....
        """
        self.options[name] = value
        if (name=="letterFreqs"):
            self.letterFreqsTotal = 0
            for tup in (self.options["letterFreqs"]):
                self.letterFreqsTotal += tup[1]
        return(1)

    def getUtilsOption(self, name):
        return(self.getOption(name))
    def getOption(self, name):
        """Return the current value of an option (see setOption()).
        """
        return(self.options[name])

    def getVersion(self):
        return(self.version)

    def setVerbose(self, v):
        """Tell the logger to set the level of message to be reported.
        """
        if (self.lg): self.lg.setVerbose(v)
        return(self.setUtilsOption("verbose", v))

    def getVerbose(self):
        """Return the logger's level of message currently set to be reported.
        """
        return(self.getUtilsOption("verbose"))


    ###########################################################################
    # XML stuff
    #
    def indentXML(
        self, s, iString="  ", maxIndent=0,
        breakAttrs=0, elems=None, html=False):
        """Breaks before start-tags and end-tags, etc.
        Puts in spurious breaks if "<" occurs within PI, comment, CDATA MS.
        If you want it really right, use my DomExtensions::collectAllXml().
        """
        return(self.indentXml(
          s, iString=iString, maxIndent=maxIndent,
          breakAttrs=breakAttrs, elems=elems, html=html))

    # Also inline-block:
    #   "del", "iframe", "ins", "map", "object", "script", "button",
    htmlInlineElements = [
        "a",        "abbr",     "acronym", "b",       "bdo",      "big",
        "cite",     "code",     "dfn",     "em",      "i",        "img",
        "input",    "kbd",      "label",   "legend",  "optgroup", "option",
        "select",   "textarea", "q",       "s",       "small",    "span",
        "strike",   "strong",   "sub",     "sup",     "tt",       "var",
        "applet",   "center",   "dir",     "font",    "samp",     "strike",
        "address",  "area",     "audio",   "bm",      "details",  "command",
        "datalist", "font",     "u",
    ]

    def indentXml(
        self, s, iString="  ", maxIndent=0,
        breakAttrs=0, elems=None, html=False):
        """Insert newlines and indentation in an XML string. Does not use
        an actual parser, but is quick and pretty reliable.
        @param iString: String to repeat to make indentation
        @param maxIndent: Don't indent more than this many levels
        @param breakAttrs: Put attributes on their own lines
        @param elems: Dict of elements, map each to 'inline' or 'block'
        @param html: Apply HTML 'inline' element list (can override w/ elems)
        """
        if (elems is None): elems = {}
        if (html):
            for e in sjdUtils.htmlInlineElements:
                if (e not in elems): elems[e] = 'inline'
        s = re.sub(r'\n', '', s)
        s = re.sub(r'(<[^/])', "\n\\1", s)
        lines = re.split(r'\n', s)
        #print(lines)
        depth = 0

        ind = ""
        for i in (range(0, len(lines))):
            effectiveDepth = depth
            if (maxIndent and depth>maxIndent):
                effectiveDepth = maxIndent
            ind = iString * effectiveDepth
            iLine = ind + lines[i]

            if (re.match(r'</', lines[i])):                 # end-tag
                lines[i] = iLine[2:]
                depth -= 1
            elif (re.match(r'<[_.\w][^>]*/>', lines[i])):   # empty
                lines[i] = iLine
            elif (re.match(r'<(br|hr)\b', lines[i])):       # HTML empty
                lines[i] = iLine
            elif (re.match(r'<\w', lines[i])):              # start-tag
                if (breakAttrs):
                    iLine = re.sub(r'([-:_.\w\d]+=)',
                                   "\n"+ind+"\\1", iLine)
                lines[i] = iLine
                depth += 1
            else:
                lines[i] = iLine

        s = "\n".join(lines)
        # No break before end-tag after text
        #s = re.sub(r's([^> ])\n\s+<', "\\1", s)
        for e in (elems):
            if (elems[e] == "inline"):
                s = re.sub(r'\n\s*<'+e+r'\b', r'\t<'+e, s)
            #elif (elems[e] == "block"):
            #    s = re.sub('\n(\s*<'+e+r')\b', '\n\n\1', s)

        return(s+"\n")
    # indentXML


    def colorizeXmlTags(self, s, color=""):
        """Surround XML markup with ANSI terminal escapes to display it
        in the specified color (default: the color for the "x" message type).
        """
        self.setColors(1)
        (con, coff) = self.lg.getPickedColorString(color, "x")
        s = re.sub(r'(<.*?>)', con+"\\1"+coff, s)
        return(s)


    def colorizeXmlContent(self, s, color=""):
        """Surround XML content (not markup) with ANSI terminal codes to display
        it in the specified color (default: the color for the "x" message type).
        """
        #print(type(s))
        if (not s): return(s)
        self.setColors(1)
        (con, coff) = self.lg.getPickedColorString(color, "x")
        rhs = re.sub(r'\[', "\\[", ">"+con+"\\1"+coff+"<")
        #print("*** rhs '%s'\ns '%s'" % (repr(rhs), s))
        s = re.sub(self.colorManager.colorizeXmlContentExpr, rhs, s)
        return(s)


    ###########################################################################
    #
    def getJsonIndent(self, level, maxIndent, iString=None):
        """Internal. Return a newline plus indentation for indentJson>().
        """
        if (iString is None): iString = self.options["iString"]
        effLevel = level
        if (maxIndent and level>maxIndent): effLevel = maxIndent
        return("\n" + (iString * effLevel))

    def indentJson(self, s, iString="    ", maxIndent=0):
        buf = ""
        level = 0
        inQuote = False
        ss = "%s" % (s)
        #print(ss)
        sslen = len(ss)
        i = 0
        while (i<sslen):
            c = ss[i]
            if (inQuote):
                buf += c
                if (c in "'\""): inQuote = False
            elif (c in "'\""):
                buf += c
                inQuote = False
            elif (c == '{' or c == '['):
                mat = re.match(r'([\[\{]\s*[\]\}])', ss[i:])
                if (mat):
                    buf += mat.group(1)
                    i += len(mat.group(1))
                    continue
                elif (re.search(r':\s*$', ss[0:i])):
                    buf += c
                    level += 1
                    buf += self.getJsonIndent(level, maxIndent, iString)
                else:
                    buf += self.getJsonIndent(level, maxIndent, iString) + c
                    level += 1
                    buf += self.getJsonIndent(level, maxIndent, iString)
            elif (c == '}' or c == ']'):
                level -= 1
                buf += c
            elif (c == ','):
                buf += c + self.getJsonIndent(level, maxIndent, iString)
                if (ss[i+1]==' '): i += 1
            else:
                buf += c
            i += 1
        return(buf)


    ###########################################################################
    # Format strings and numbers for nicer printing.
    #
    def rpad(self, s, width=0, padChar=" ", quoteChar=""):
        """Like ljust(), but can also quote before padding.
        """
        if (not isinstance(s, string_types)): s = str(s)
        if (quoteChar): s = quoteChar[0] + unicode(s) + quoteChar[-1]
        return(s.ljust(width, padChar))

    def lpad(self, s, width=0, padChar="0", quoteChar=""):
        """Like rjust(), but can also quote before padding.
        """
        if (not isinstance(s, string_types)): s = str(s)
        if (quoteChar): s = quoteChar[0] + s + quoteChar[-1]
        return(s.rjust(width, padChar))

    def lpadc(self, s, width=0, padChar="0", quoteChar="", sepChar=","):
        """Like lpad(), but inserting `sepChar` every three digits.
        (Python 3 has that feature in `format`).
        Can also quote before padding.
        """
        buf = ""
        if (not isinstance(s, string_types)): s = str(s)
        while (len(s) > 3):
            triple = s[len(s)-3:]
            if (sepChar=="COLOR"):
                triple = self.colorize("bold", triple)
            elif (sepChar=="UNDER"):
                triple = self.colorize("bold", triple)
            else:
                triple = sepChar + triple
            buf = triple + buf
            s = s[0:len(s)-3]
        buf = s + buf
        if (quoteChar): s = quoteChar[0] + s + quoteChar[-1]
        needed = width - len(buf)
        while (needed > 0):
            buf = padChar + buf
            needed -= 1
        return(buf)

    def align(self, mylist, delim=',', stripTrail=True, maxLen=None, padChar=' '):
        """Pad sub-items (of the members of 'mylist'), to line them up.
        @todo: ignore delim if in quotes, or backslashed?
        @todo: Avoid quoting in all-numeric columns.
        """
        tokenized = []
        maxLens = []
        allNumeric = []
        for s in mylist:
            if (isinstance(s, string_types)):
                tokens = s.split(sep=delim)
            else:
                tokens = list(s)
            tokenized.append(tokens)
            for i, token in enumerate(tokens):
                if (token is None): thisLen = 4
                else: thisLen = len(token)
                if (maxLen and thisLen>maxLen): thisLen = maxLen
                if (len(maxLens) <= i):
                    maxLens.append(thisLen)
                    allNumeric.append(True)
                elif (thisLen > maxLens[i]): maxLens[i] = thisLen
                if (not self.isNumeric(token)): allNumeric[i] = False
        paddedList = []
        delimLen = len(delim)
        for tokens in tokenized:
            buf = ''
            for i, token in enumerate(tokens):
                if (token is None): token = 'None'
                if (allNumeric[i]):
                    buf += (token+delim+' ').rjust(
                        maxLens[i]+delimLen+1, padChar)
                else:
                    buf += ('"'+token+'"'+delim+' ').ljust(
                        maxLens[i]+delimLen+3, padChar)
            if (stripTrail): buf = buf.strip()
            paddedList.append(buf)
        return paddedList

    def toHNumber(self, n, base=1000):
        """Convert a number to human-readable form, like several *nix commands.
        For example, "123456789" would become "123M".
        """
        if (base==1000): col = 1
        else: col = 2
        fs = "{0:3.2f}{1:1s}"
        rc = unicode(n)
        for i in (range(len(self.multipliers)-1, 0, -1)):
            factor = self.multipliers[i][col]
            if (n > factor):
                rc = fs.format(n / factor, self.multipliers[i][0])
                break
        return(rc)

    def fromHNumber(self, n, base=1000):
        """Undo toHNumber() notation. For example, "123M" would become
        "123000000". Round-trip conversions lose precision.
        """
        if (base==1000): col = 1
        else: col = 2
        rc = n
        for i in range(len(self.multipliers)):
            suffix = self.multipliers[i][0]
            if (n.endswith(suffix)):
                return(float(n[0:-1]) * self.multipliers[i][col])
        return(rc)

    def unquote(self, s, fancy=False):
        """Remove single or double quotes from around a string, if present.
        A quote all by itself, remains.
        Deals with most but not all Unicode quotes.
        """
        if (len(s)<2): return(s)
        if (s[0] in UQuotes and s[-1] == s[0]): return(s[1:-1])
        if (fancy and s[0] in ULQuotes and s[-1] in URQuotes ):
            if (ULQuotes.find(s[0]) == URQuotes.find(s[-1])):
                return(s[1:-1])
        return(s)

    def quote(self, s, curly=False, escape='\\'):
        """Return the argument with a double-quote character added on each end.
        If 'curly' is True, use curly double quotes.
        If 'escape' is set, put it before any internal (straight) quotes.
        """
        if (curly):
            if (escape):
                re.sub(r'('+unichr(0x201c)+unichr(0x201d)+r')', escape+'\\1', s)
            s = unichr(0x201c) + s + unichr(0x201d)
        else:
            if (escape):
                s = re.sub(r'"', escape+'"', s)
            s = '"' + s + '"'
        return(s)

    ###########################################################################
    # Return 1 iff the argument is interpretable as a number.
    #
    def isNumeric(self, n):
        """Return True if n castable to float().
        """
        try:
            float(n)
            return(True)
        except (TypeError, ValueError):
            return(False)

    def isInteger(self, n):
        """Return True if n castable to int and float,
        and the resulting values are equal.
        """
        try:
            return(float(n) == int(n))
        except (TypeError, ValueError):
            return(False)


    ###########################################################################
    # Escape reserved characters for various contexts.
    #
    def isUnicodeCodePoint(self, c):
        try:
            n = int(c)
            return(n>=0 and n<=0x10FFFF)
        except (TypeError, ValueError):
            return(False)

    def getUTF8(self, c):
        u = ""
        if (not isinstance(c, string_types)):
            c = unicode(c)
        try:
            u = c.encode('utf-8')
        except UnicodeDecodeError as e:
            print("getUTF8: UnicodeDecodeError in '%s': %s" % (c, e))
        return(u)

    def makePrintable(self, c, mode="DFT", spaceAs=None, lfAs=None):
        spaceChar = " "
        if (spaceAs and spaceAs in spaceCodes):
            spaceChar = spaceCodes[spaceAs]
        lfChar = unichr(0x240A)
        if (lfAs and lfAs in lfCodes):
            lfChar = lfCodes[lfAs]

        o = ord(c)
        buf = "c"

        if (mode == "DFT"):  # cf unbackslash()
            if (c in char2escape): buf = char2escape[c]
            elif (o == 10): buf = lfChar
            elif (o <= 31): buf = "\\x%02x" % (o)
            elif (o == 32): buf = spaceChar
            elif (o <= 126): buf = c
            elif (o == 127): buf = "\\x%02x" % (o)
            elif (o <= 255): buf = "\\x%02x" % (o)
            else: buf = "\\x{%x}" % (o)
        else:
            print("makePrintable mode '%s' unsupported." % (mode))
        return buf

    def showControls(self, s, space=unichr(0x2422), lf=unichr(0x240A)):
        """Convert control characters into Unicode "control pictures".
        Space lets you choose U+2422 = bSlash, U+2423 = underbar, U+2420 = SP.
        LF lets you choose U+240a = LF, U+2424 = NL.
        """
        if (s is None): return("")
        s = re.sub(r' ', space, s)
        s = re.sub(r'\n', lf, s)
        # What does this do with C1 controls??
        s = re.sub(r'([[:cntrl:]])', controlSymbolsFunction, s)  # See top
        return(s)

    def vis(self, s):
        """Show non-ASCII characters as 4-digit hexadecimal escapes.
        """
        if (s is None): return("")
        return(self.showInvisibles(s))

    def showInvisibles(self, s):
        """Return s with non-ASCII and control characters replaced by
        hexadecimal escapes such as `\\uFFFF`.
        """
        if (s is None): return("")
        s = re.sub(r'([^[:ascii:]]|[[:cntrl:]])', UEscapeFunction, s)
        return(s)

    def escapeRegex(self, s):
        """Put backslashes in front of potential regex meta-characters in s.
        """
        if (s is None): return("")
        s = re.sub(r'([().?*+\[\]{}^\\\\])', "\\\\\\1", s)
        return(s)

    def escapeXmlContent(self, s):
        """Turn ampersands, less-than signs, and greater-than signs that are
        preceded by two close square brackets, into XML entity references.
        Also delete any non-XML C0 control characters.
        This escaping is appropriate for XML text content.
        """
        if (s is None): return("")
        if (not isinstance(s, string_types)): s = str(s)
        s = s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'&',   "&amp;",  s)
        s = re.sub(r'<',   "&lt;",   s)
        s = re.sub(r']]>', "]]&gt;", s)
        return(s)

    def escapeXml(self, s):
        """Synonym for escapeXmlContent().
        """
        return(self.escapeXmlContent(s))

    def escapeXmlText(self, s):
        """Synonym for escapeXmlContent().
        """
        return(self.escapeXmlContent(s))

    def escapeXmlAttribute(self, s, apostrophes=False):
        """Turn ampersands, less-than signs, and double-quotes
        into XML entity references. If `apos` is true, then leave
        double-quotes unchanged, but turn single-quotes into `&apos;` instead.
        Also delete any non-XML C0 control characters.
        This escaping is appropriate for XML attribute values.
        """
        if (s is None): return("")
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'&',  "&amp;", s)
        s = re.sub(r'<',  "&lt;", s)
        if (apostrophes):
            s = re.sub(r"'", "&apos;", s)
        else:
            s = re.sub(r'"', "&quot;", s)
        return(s)

    def escapeXmlPi(self, s, target="?&gt;"):
        """Turn "?>" into "?&gt;" within a string.
        One way to escape data to go inside XML Processing Instructions.
        Note: XML allows but does not recognize "&gt;" inside PIs.
        """
        if (s is None): return("")
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'\?>', target, s)
        return(s)

    def escapeXmlComment(self, s, target="\u2014"):
        """Turns "--" into em dash (U+2014) within s. "--" is not allowed
        inside XML comments. This is not a method defined by XML.
        """
        if (s is None): return("")
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'--', target, s)
        return(s)

    def normalizeXmlSpace(self, s):
        """Reduce runs of space, tab, linefeed, and cr to a single space, and
        strip the same characters off start and end of a string.
        """
        if (s is None): return("")
        s = re.sub(r'\s+', ' ', s)
        s = re.sub(r'^ ', '', s)
        s = re.sub(r' $', '', s)
        return(s)

    def expandXml(self, s):  # aka unescape or expandEntities
        """Turn HTML4 entites and numeric character references into literals.
        """
        if (s is None): return("")
        if (PY2):
            import HTMLParser
        else:
            from html.parser import HTMLParser
        if (not self.htmlp): self.htmlp = HTMLParser.HTMLParser()
        return(self.htmlp.unescape(s))

    # Handle c-like \\ codes, include octal, hex, Unicode.
    #
    def charFromHexFunction(self, mat):
        return(unichr(int(mat.group(1), 16)))

    def charFromOctalFunction(self, mat):
        return(unichr(int(mat.group(1), 8)))

    def charToURIFunction(self, mat):
        c = mat.group(1)
        if (ord(c) >= 127):
            theBytes = c.encode('utf-8')
            buf = ""
            for b in theBytes:
                buf += "%{0:02x}".format(b)
        else:
            buf = "%{0:02x}".format(ord(c))
        return(buf)

    def charToXXFunction(self, c):
        o = ord(c)
        if (o > 255):
            return("\\u{0:04x}".format(ord(c)))
        else:
            return("\\x{0:02x}".format(ord(c)))

    # Handle \\ codes.
    #
    def backslash(self, s):
        """Insert backslash before space, non-ASCII, and backslash characters.
        """
        s = re.sub(r"\t",  r"\\t", s)
        s = re.sub(r"\r",  r"\\r", s)
        s = re.sub(r"\n",  r"\\n", s)
        s = re.sub(r"\f",  r"\\f", s)
        s = re.sub(r"\\",  r"\\\\", s)
        s = re.sub(r"([^[:ascii:]])", self.charToXXFunction, s)
        return(s)

    if PY2:
        def unbackslash(self, s):
            return s.decode('string_escape') # python2
    else:
        def unbackslash(self, s):
            return bytes(s, "utf-8").decode("unicode_escape") # python3

    # Handle URI escaping.
    #
    # Doesn't escape non-ASCII correctly (should expand to UTF-8 first)
    def escapeURI(self, s):
        """Map non-URI characters in the string to %FF-style codes.
        """
        s = re.sub(r'([^-!\$\'()*+.0-9:;=?\@A-Z_a-z])',
                   self.charToURIFunction, s)
        return(s)

    def unescapeURI(self, s, escapeChar='%'):
        if (s):
            s = re.sub(escapeChar+r'([0-9a-f][0-9a-f])',
                       self.charFromHexFunction, s, flags=re.I)
        return(s)

    def escapeQuotes(self, s):
        return re.sub(r'["\\]', sjdUtils.qEscaper, s)

    @staticmethod
    def qEscaper(mat):
        if (mat.group(0) == '"'): return "\\\""
        elif (mat.group(0) == '\\'): return "\\\\"
        return mat.group(0)


    ###########################################################################
    # Human-readable times and dates.
    #
    def isoDateTime(self, s=None):
        if (s is None): s = time.time()
        ltime = time.localtime(s)
        #(sec,min,hour,mday,mon,year,wday,yday,isdst)
        return("{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}".format(
                ltime.tm_year, ltime.tm_mon+1, ltime.tm_mday,
                ltime.tm_hour, ltime.tm_min, ltime.tm_sec))

    def isoDate(self, s=None):
        if (s is None): s = time.time()
        return(self.isoDateTime(s)[0:10])

    def isoTime(self, s=None):
        if (s is None): s = time.time()
        return(self.isoDateTime(s)[11:])

    def elapsedTime(self, startTime, endTime=None, seconds=True):
        """Subtract two epoch times, and return the difference.
        With 'seconds' True, as number of seconds, otherwise as hh:mm:ss.
        """
        if (endTime is None): endTime = time.time()
        elapsed = endTime - startTime
        if (seconds): return(elapsed)
        h = int(elapsed / 3600)
        m = int(elapsed / 60) % 60
        s = int(elapsed) % 60
        return("{0:02d}:{1:02d}:{2:02d}".format(h, m, s))

    # Should vary it if it needs to be repeated.
    def lorem(self, length=79, loremType="a", mode='frequency', xtab=None):
        """Return a given length of sample text, either by replicating
        the 'loremText' option value (which defaults to the usual), or
        by generating it randomly. In either case, you can also have it
        translated, for example by passing an xtab obtained from
        getRandomXtab(), to make sure Unicode gets exercised.
        """
        assert loremType in "ar"

        buf = ""
        if (loremType=="r"):
            #import random
            rgen = random.Random()
            for _ in range(0, length):
                buf += self.randomChar(rgen, mode=mode)
        else:
            if (self.options["loremText"]==""):
                self.options["loremText"] = "Missing loremText. "
            reps = math.ceil(length / len(self.options["loremText"]))
            buf = self.options["loremText"] * reps
            buf = buf[0:length]

        if (xtab): buf = buf.translate(xtab)
        return(buf)

    def getRandomXtab(self, fromChars='aeiouAEIOU', uMin=0x00A1, uMax=0x2FF):
        """Translate the fromChars passed, to random Unicode code points
        from the given range.
        """
        assert len(fromChars)>0 and uMin>=32 and uMin<=uMax and uMax<0x1FFFF
        toChars = ""
        rgen = random.Random()
        while (len(toChars) < len(fromChars)):
            toChars += chr(rgen.randint(uMin, uMax))
        xtab = str.maketrans(fromChars, toChars)
        return xtab

    def randomChar(self, rgen=random.Random(), mode='frequency'):
        if (mode=='frequency'): # derive from GNG instead
            rgen = random.Random()
            r = rgen.randint(1, self.letterFreqsTotal)
            for tup in self.options["letterFreqs"]:
                r -= tup[1]
                if (r<1): return(tup[0])
            return(' ')
        else: # uniform (or unknown)
            c = chr(random.randint(32, 95))
        return(c)


    ###########################################################################
    # Miscellaneous
    #
    # In Python 3, use 'importlib' instead of 'imp'.
    def try_module(self, moduleName, quiet=False):
        import imp
        try:
            imp.find_module(moduleName)
        except ImportError:
            if (not quiet): sys.stderr.write(
                "sjdUtils.try_module(): Can't find module'%s'." % (moduleName))
            return(False)
        return(True)

    def findHighestSuffixedName(self, baseDir, filename, ext):
        """Return the highest integer found as a suffix to the given
        filename (there could be earlier gaps).
        """
        expr = re.compile(filename + r'(\d+)' + ext + r'$')
        maxN = 0
        for ch in (os.listdir(baseDir)):
            mat = re.match(expr, ch)
            if (not mat): continue
            n = int(mat.group(1))
            if (n > maxN): maxN = n
        return maxN

    def splitPath(self, path):
        """Mainly for sjdUtils.pm compatibility. Python has os.path.
        """
        mat = re.match(r'^(.*/)?([^/]*?)(\.(\w*))?$', path)
        dir0 = fil0 = ext0 = ""
        dir0 = mat.group(1)
        fil0 = mat.group(2)
        ext0 = mat.group(4)
        return ( dir0, fil0, ext0 )

    def shrinkuser(self, path):
        """More or less the opposite of os.path.expanduser().
        TODO: normcase()? realpath()? relpath to an arg?
        """
        try:
            path = os.path.normpath(path)
            h = os.environ['HOME'].rstrip(' /')
            if (path.startswith(h)): path = '~/' + path[len(h):]
        except KeyError:
            pass
        try:
            c = os.environ['PWD'].rstrip(' /')
            if (path.startswith(c)): path = path[len(c):]
        except KeyError:
            pass
        return path

    def localize(self):
        self.lg.error("sjdUtils: localize() not yet supported.")

    def toUTF8(self, s, srcEncoding=None):
        if (isinstance(s, str)):
            s.encode('utf-8')
        elif (srcEncoding):
            s.decode(srcEncoding).encode('utf-8')
        return(s)

    @staticmethod
    def splitPlus(st, delim=" ", esc="\\", unbackslash=False, empties=True):
        """Basically the same as string split(), but supports backslashing
        the delimiter, and discarding empty tokens.
        Does NOT decode backslash/escape codes by default.
        TODO: Add support for multi-char delimiters.
        """
        assert (len(delim) == 1)
        assert (len(esc) <= 1)
        tokens = []
        token = ""
        gotEscape = False
        for ch in st:
            if (gotEscape):
                token += ch
                gotEscape = False
            elif (ch == esc):
                token += ch
                gotEscape = True
            elif (ch == delim):
                if (token!='' or empties): tokens.append(token)
                token = ""
            else:
                token += ch
        if (token != ''):
            tokens.append(token)
        if (unbackslash):
            for i, token in enumerate(tokens):
                tokens[i] = token.decode('string_escape')
        return tokens


###############################################################################
#
if __name__ == "__main__":
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
           description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(
        description=descr)

    parser.add_argument(
        "--version", action='version', version=__version__,
        help='Display version information, then exit.')
    args = parser.parse_args()
    sys.exit()
