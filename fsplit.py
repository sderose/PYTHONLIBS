#!/usr/bin/env python
#
# fsplit.py: A better (I hope) split().
#
# 2020-02-28: Written. Copyright by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import re
#import string
#import codecs

__metadata__ = {
    'title'        : "fsplit.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-02-28",
    'modified'     : "2020-02-28",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

An enhanced `split()` function, that can handle:

* Multi-character delimiters
* More than one allowed quotechar (for example, single and double)
* Unicode quote characters (curly, angle, etc)
* Special chars like \xFF, \uFFFF, &#xFFFFF;, &bull;, etc.
* Option to ignore repeated delimiters
* min/max number of results

as well as the usual features of Python's csv package:

* Escaped (backslashed) delimiter
* Doubled delimiter
* Quoted fields (where open and close quote are the same character)
* Option to discard leading whitespace

Maybe will add:
* Whitespace-to-non transition (incl. Unicode whitespace)
* Special treatment of empty/missing fields
* Defaults?
* Type-checking and numeric conversions
* Controllable Boolean values
* Split to NamedTuple or tuple or list or dict?
* Sub/alternate class for fixed column widths?
* Support for cycling delimiters (like 'paste -d)
* Maybe defaults?
* support MediaWiki macros and tables; HTML and XML seqs?

* readline variant that can do the right thing even w/ newlines in fields?

And maybe a bracket parser that makes nested lists or similar, but can still do
backslashing and such. Same i/f but add left and right pairs to accept?

=Usage=

    myTuple = namedtuple('myTuple', [age, name, married, lat, longt])

    myList = fsplit(s, delimiter='\t',
        doublequote=False, escapechar='\\', quotechar='"',
        xescapes=True, uescapes=True, entities=False,
        types=[int, str, bool, str, float, '*'], min=5, max=5,
        returnClass=myTuple
        )

==The options==

* s:str -- The string to be split into tokens/fields.

* delimiter:str = "\t" -- The field separator character or string.

* doublequote:bool = False -- If set, allow putting `quotechar` inside
a quoted string, by doubling it.

* escapechar:str = "\\" -- If set, this character can be put before
the quotechar, delimiter, or itself, to make that character literal rather
than special. The escapechar can also be used before any of
'f', 'n', 'r', 't', 'v', '\\', or '0' for the usual meanings.

* lineterminator:str = "\n" --
UNUSED?

* quotechar:str = '"' -- Sets what characters or character-pairs are recognized
as quotes (setupQuoteMap() handles all of this).

** If set to None or '', no characters are treated as quotes.
** If set to a single character, that character is the only recognized quote,
and serves as both open and close.
** If set to a 2-character string, the first character is treated as open quote,
and the second as the corresponding close quote. Only the close quote is
subject to `doublequote`, though both are subject to `escapechar`.
** If set to "BOTH", then both single quote (apostrophe) and double quote are
recognized as quotes, as is common in programming and markup languages.
** If set to "ALL", single and double quotes are supported (as with "BOTH"),
as well as a wide range of Unicode quotation marks, including curly single
and double, angle quotes, and so on.

The known pairs are defined in `UQuotePairs`, an array of triples, each like:

    (0x00AB, 0x00BB, "[LEFT,RIGHT]-POINTING DOUBLE ANGLE QUOTATION MARK *" )

* skipinitialspace:bool = True -- If set, `s` has any initial (Unicode)
whitespace stripped before parsing.

* strict:bool = True -- If set, problems raise `ValueError`
instead of being worked around or ignored.

* multidelimiter:bool = False -- If set, multiple adjacent delimiters do
NOT result in empty tokens, but be treated the same as a single delimiter.
This would typically be done when the delimiter is just a space.
Empty fields can, however, be inserted by quoting them (because the delimiters
on each side are no longer "adjacent").

* xescapes:bool = True -- If set, escapes like \xFF may be used.
This uses `escapechar` (not necessarily backslash).

* uescapes:bool = True -- If set, escapes like \uFFFF may be used.
This uses `escapechar` (not necessarily backslash).

* entities:bool = False -- If set, character references are recognized
and replaced as in HTML. Decimal (&#8226;), hexadecimal (&#x2022;), and named
(&bull;) forms are all supported.

* types:list = None -- ''Not yet implemented''. If provided, the parsed
tokens are cast to the specified datatypes, in respective order.
Casts can of course fail, resulting in exceptions. If there are more tokens
than entries in this list, the remaining items stay as strings.
Empty fields always pass. The list should contain the actuall types, not
their string names. For example:
    types=[ int, int, float, bool, str ]

* min:int = None -- If specified, an exception is raised if fewer than
this many tokens are found.

* max:int = None -- If specified, an exception is raised if more than
this many tokens are found.

* returnClass:class = None -- If specified, an attempt is made to convert
the list of tokens to the given class before it is returned. This is mainly
meant to be used for subclasses of `list` or for named tuples.

=Related Commands=

==Python csv package==

[https://docs.python.org/3/library/csv.html]. Its format
parameters are pretty nice, but it lacks:

* multi-character delimiters,
* regex delimiters
* the "whitespace to nonspace transition" approach (like awk, column, and sort)
* ignoring repeated delimiters (except skipinitialspace)
* cyclic delimiter lists (like paste)

Python package options:

* Dialect.delimiter -- A one-character string used to separate fields. It defaults to ','.

* Dialect.doublequote -- It defaults to True.

* Dialect.escapechar -- A one-character string used by the writer to escape the delimiter if quoting is set to QUOTE_NONE and the quotechar if doublequote is False. It defaults to None, which disables escaping.

* Dialect.lineterminator -- Defaults to '\r\n'. The reader is hard-coded to recognise either '\r' or '\n' as end-of-line, and ignores lineterminator.

* Dialect.quotechar -- A one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters. It defaults to '"'.

* Dialect.quoting -- Controls when quotes should be generated by the writer and recognised by the reader:

    csv.QUOTE_ALL -- quote all fields.

    csv.QUOTE_MINIMAL -- only quote those fields which contain special characters such as delimiter, quotechar or any of the characters in lineterminator.

    csv.QUOTE_NONNUMERIC -- quote all non-numeric fields. Convert all non-quoted fields to type float.

    csv.QUOTE_NONE -- never quote fields, but use escapechar. If escapechar is needed but not set, raise Error.

* Dialect.skipinitialspace -- When True, whitespace immediately following the delimiter is ignored. The default is False.

* Dialect.strict -- When True, raise exception Error on bad CSV input. The default is False.


==Field-related *nix commands==

The initial goal was to cover all the line-splitting capabilities of the
usual *nix filters:

* awk
    FS     regular expression used to separate fields; also settable by option -Ffs (fields then referred to via $1,...). Default: whitespace. FS='' means one field per character.
    OFS    output field separator (default blank)

* column
     -s      Specify a set of characters to be used to delimit columns for the -t option.

     -t      Determine the number of columns the input contains and create a table.  Columns are delimited with whitespace, by default, or with the characters supplied using the -s option.  Useful for pretty-printing displays.

* cut
    -b bytes -c chars -f fields -d delim (default TAB)
    E.g. cut -c 1-16,26-38

* join
    -o list     Which fields to output
    -t char     Use character char as a field delimiter
    -e string   Replace empty output fields with string.
    -t c    The input line terminator is c instead of a newline.

* msort

* paste
    -d list     Use one or more of the provided characters to replace the newline instead of the default tab. used circularly. Recognizes \n\t\\\0/
    -s          Concatenate all of the lines of each separate input file in command line order.  The newline character is replaced with the tab character, unless otherwise specified by the -d option.

* sort
    -b, --ignore-leading-blanks     Ignore leading blank space when determining the start and end of a restricted sort key (see -k).  If -b is specified before the
             first -k option, it applies globally to all key specifications.  Otherwise, -b can be attached independently to each field argument of the key specifications.  -b.

    -k field1[,field2], --key=field1[,field2]    Repeatable. m.n (m,n > 0) and can be followed by one or more of the modifiers b, d, f, i, n, g, M and r

    -t char, --field-separator=char    Each occurrence of char is significant. If -t is not specified, the default field separator is a sequence of blank space characters, and consecutive blank spaces do not delimit an empty field. To use NUL as field separator, use -t '\0'.

    -z, --zero-terminated   Use NUL as record separator.

* tab2space
    -tabs          preserve tabs, e.g. for Makefile
    -t<n>          set tabs to <n> (default is 4) spaces

* uniq
     -f num  Ignore the first num fields.  A field is a string of non-blank characters separated from adjacent fields by blanks. Field numbers are one based.
     -s chars  Ignore the first chars characters. With -f, the first chars characters after the first num fields will be ignored.


===Column numbers only, no fields===

* colrm (N)
    [start [stop]]

* expand
    -t tab1,tab2,...,tabn  If only a single number, use multiples of it. Default 8.

* lam
    -f min.max  Print line fragments according to the format string min.max, where min is the minimum field width and max the maximum field width. If min begins with a zero, zeros will be added to make up the field width, and if it begins with a `-', the fragment will be left-adjusted within the field.
    -s sepstring
             Print sepstring before printing line fragments from the next file.

* look
    -t      Specify a string termination character, i.e., only compared up to and including the first occurrence of termchar

* sed
    Recognizes \a\f\r\t\v\\ (not \n!)

* unexpand
    -a      By default, only leading blanks and tabs are reconverted to maximal strings of tabs.  If the -a option is given, then tabs are inserted whenever they would compress the resultant file by replacing two or more characters.


=Known bugs and Limitations=

Not sure whether you can (or should be able to) escape in mid-delimiter.

What's the right rule for a quote not immediately following a delimiter?

=History=

Written by Steven J. DeRose, 2020-02-28.

=To do=

=Rights=

Copyright 2020-02-28 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see L<http://www.derose.net/steve/utilities/>
or L<http://github.com/sderose>.

=Options=
"""

escapeMap = {
    #'b':     "\b",  # Bell?
    'f':     "\f",  # FF
    'n':     "\n",  # LF
    'r':     "\r",  # CR
    't':     "\t",  # TAB
    'v':     "\v",  # VTAB
    '\\':    "\\",  # BACKSLASH
    '0':     "\0",  # NULL
}

UQuotePairs = [  # From my UnicodeSpecials.py
    (0x00AB, 0x00BB, "[LEFT,RIGHT]-POINTING DOUBLE ANGLE QUOTATION MARK *" ),
    (0x2018, 0x2019, "[LEFT,RIGHT] SINGLE QUOTATION MARK" ),
    (0x201A, 0x201B, "SINGLE [LOW-9, HIGH-REVERSED-9] QUOTATION MARK" ),
    (0x201C, 0x201D, "[LEFT,RIGHT] DOUBLE QUOTATION MARK" ),
    (0x201E, 0x201F, "DOUBLE [LOW-9, HIGH-REVERSED-9] QUOTATION MARK" ),
    (0x2039, 0x203A, "SINGLE [LEFT,RIGHT]-POINTING ANGLE QUOTATION MARK" ),
    (0x2E02, 0x2E03, "[LEFT,RIGHT] SUBSTITUTION BRACKET" ),
    (0x2E04, 0x2E05, "[LEFT,RIGHT] DOTTED SUBSTITUTION BRACKET" ),
    (0x2E09, 0x2E0A, "[LEFT,RIGHT] TRANSPOSITION BRACKET" ),
    (0x2E0C, 0x2E0D, "[LEFT,RIGHT] RAISED OMISSION BRACKET" ),
    (0x2E1C, 0x2E1D, "[LEFT,RIGHT] LOW PARAPHRASE BRACKET" ),
    (0x2E20, 0x2E21, "[LEFT,RIGHT] VERTICAL BAR WITH QUILL" ),
]

quoteMap = {
    '"':     '"',
    "'":     "'",
}

lastQuoteArg = None
lastQuoteMap = None

def setupQuoteMap(quoteArg):
    global lastQuoteArg, lastQuoteMap
    if (lastQuoteArg and lastQuoteArg == quoteArg):
        return lastQuoteMap
    lastQuoteMap = {}
    if (not quoteArg):
        pass
    elif (len(quoteArg) == 1):
        lastQuoteMap[quoteArg] = quoteArg
    elif (len(quoteArg) == 2):
        lastQuoteMap[quoteArg[0]] = quoteArg[1]
    elif (quoteArg == 'BOTH'):
        lastQuoteMap = quoteMap
    elif (quoteArg == 'ALL'):
        for tup in UQuotePairs:
            lastQuoteMap[chr(tup[0])] = chr(tup[1])
    else:
        raise ValueError("Unknown quotechar value '%s'." % (quoteArg))
    lastQuoteArg = quoteArg
    return lastQuoteMap

def unescapeViaMap(c):
    if (c in escapeMap): return escapeMap[c]
    return c

def parseEntity(s):
    from html import unescape
    mat = re.match(r'(&#(\d+)|(x[\da-f]+)|(\w[\d\w]*);)', s)
    if (not mat): return None, 0
    return unescape(mat.group(1)), len(mat.group(1))

def autoType(tok):
    """Convert a string to the most specific type we can.
    """
    from datetime import date
    newTok = None
    if (newTok is None):
        try:
            newTok = date.fromisoformat(tok)
        except ValueError:
            pass
    if (newTok is None):
        try:
            newTok = int(tok)
        except ValueError:
            pass
    if (newTok is None):
        try:
            newTok = float(tok)
        except ValueError:
            pass
    if (newTok is None):
        try:
            newTok = complex(tok)
        except ValueError:
            pass
    if (newTok is None):
        newTok = tok
    return newTok


def fsplit(
    # The string to split:
    s,
    # Options like Python 'csv' package:
    delimiter		    = "\t",
    doublequote		    = False,  # TODO
    escapechar		    = "\\",
    lineterminator		= "\n",   # UNUSED?
    quotechar		    = '"',
    skipinitialspace	= True,
    strict              = True,
    # Other options:
    multidelimiter      = False,
    xescapes			= True,
    uescapes			= True,
    entities			= False,
    minsplits			= None,
    maxsplits	        = None,
    types			    = None,
    returnClass			= None
    ):
    """High-end string splitter. Lots of options, and Unicode smarts.
    """
    if (delimiter == ''):
        return s.split()
    dlen = len(delimiter)

    currentQuoteMap = setupQuoteMap(quotechar)
    if (skipinitialspace): s = s.lstrip()

    tokens = [ "" ]
    pendingQuote = None
    for i, c in enumerate(s):
        if (toIgnore):
            toIgnore -= 1

        elif (pendingQuote):
            if (c == pendingQuote):
                if (doublequote and len(s)>=i+1 and s[i+1]==pendingQuote):
                    tokens[-1] += pendingQuote
                    toIgnore = 1
                else:
                    pendingQuote = None
            else:
                tokens[-1] += c

        elif (c == escapechar):
            if (xescapes and c == 'x' and len(s)>=i+4):
                try:
                    tokens[-1] += chr(int(s[i+2:i+4], 16))
                    toIgnore = 3
                except ValueError:
                    if (strict): raise ValueError(
                        "Bad sequence '%s'." % (s[i:i+4]))
            elif (uescapes and c == 'u' and len(s)>=i+6):
                try:
                    tokens[-1] += chr(int(s[i+2:i+6], 16))
                    toIgnore = 5
                except ValueError:
                    if (strict): raise ValueError(
                        "Bad sequence '%s'." % (s[i:i+6]))
            elif (len(s)>=i+1):
                tokens[-1] += unescapeViaMap(s[i+1])
                toIgnore = 1
            else:
                if (strict): raise ValueError("Final char is escapechar.")

        elif (entities and c == '&'):
            entExpansion, charsUsed = parseEntity(s[i:])
            if (entExpansion is not None):
                tokens[-1] += entExpansion
                toIgnore = charsUsed - 1
            elif (strict):
                raise("Ill-formed character reference")

        elif (c in currentQuoteMap):
            if (strict and tokens[-1]!=''):
                raise ValueError("Quote is not at start of field")
            pendingQuote = currentQuoteMap[c]

        elif (c == delimiter[0] and s[i:].startswith(delimiter)):
            if (multidelimiter):
                raise ValueError("multidelimiter not yet implemented.")
            tokens.append("")
            toIgnore = dlen - 1

        else:
            tokens[-1] += c

    if (minsplits is not None and len(tokens) < minsplits):
        raise ValueError("min %d tokens needed, but found %d." %
            (minsplits, len(tokens)))
    if (maxsplits is not None and len(tokens) > maxsplits):
        raise ValueError("max %d tokens needed, but found %d." %
            (maxsplits, len(tokens)))

    if (types):
        if (isinstance(types, list)):
            for i, typ in enumerate(types):
                if (not typ): continue
                tokens[i] = typ(tokens[i])
        elif (types=='*'):
            for i, tok in enumerate(types):
                tok = autoType(tok)

    if (returnClass is not None):
        tokens = returnClass(tokens)
    return tokens


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    def anyInt(x):
        return int(x, 0)

    def processOptions():
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    print("Testing...")

    if (not args.quiet):
        sys.stderr.write(0,"Done.\n")
