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
* Type-checking, auto-typing

as well as the usual features of Python's csv package and string.split():

* Escaped (backslashed) delimiter
* Doubled delimiter
* Quoted fields (where open and close quote are the same character)
* Option to discard leading whitespace
* maxsplit to limit the number of splits

Maybe will add:
* Whitespace-to-non transition (incl. Unicode whitespace)
* Special treatment of empty/missing fields
* Defaults?
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
        doublequote=False, escapechar='\\', quotechar='"', xescapes=True)

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

You can also pass `SINGLE`, `DOUBLE`, `ANGLE`, or `CURLY`
to get those specific cases.

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
If `escapechar` is set but not `xescapes`, an escapechar before 'x' will
not raise an error (even with `strict`), because that escape just ensures
(unnecessarily) that the 'x' is literal.

* uescapes:bool = True -- If set, escapes like \uFFFF may be used.
This uses `escapechar` (not necessarily backslash).
If `escapechar` is set but not `uescapes`, an escapechar before 'u' will
not raise an error (even with `strict`), because that escape just ensures
(unnecessarily) that the 'u' is literal.

* entities:bool = False -- If set, character references are recognized
and replaced as in HTML. Decimal (&#8226;), hexadecimal (&#x2022;), and named
(&bull;) forms are all supported.
NOTE: These are converted by Python's `html.unescape()` method, which does not
raise an error for Unknown entities such as `&foo;`.


* types = None -- If provided as a list of types, the parsed
tokens are cast to the specified datatypes, in respective order.
Casts can of course fail, resulting in exceptions (this provides very
rudimentary validation). If there are more tokens
than entries in the list, the remaining items stay as strings.
Empty fields always pass. The list should contain the actual types, not
their string names. For example:

    types = [ int, int, float, bool, str ]

If using `bool`, remember that Python
takes any non-empty string as True, even strings like "0" or "False".

If specified as 'AUTO' instead of a list of types,
tokens are examined and automatically cast to the
most specific type they can, from among datetime, int, float, complex, or str.
Booleans are not attempted. The type-inference is handled by `autoType()`,
described below.

This option is still experimental.

* minsplit:int = None -- If specified, an exception is raised if fewer than
this many splits are made.

* maxsplit:int = None -- If specified, splitting stops after this many splits
have occurred (making this many + 1 tokens).

=autoTyping=

If `type='AUTO'` is specified, each field is passed to this function, which
tries to cast it to the most specific appropriate type:

    autoType(tok:str, boolCaster=None, specialFloats=False)

Leading and trailing whitespace are stripped before testing for various types.
However, items that remain as strings are returned with the whitespace intact.

If `boolCaster` is supplied, it must take a string argument (the token,
with leading and trailing whitespace intact), and return True or False,
or raise ValueError if the value is not an acceptable string representation of
a boolean (by whatever rules the implenter likes). By default no such
function is used, and so autoTyping never casts anything to type `bool`.
Python's `bool()` function takes any non-empty string as True, even
'0', '0.0', 'False', etc.

If `specialFloats` is set, then the strings "NaN", "inf", "-inf", and "+inf"
(all case-sensitive) will be taken as floats.

Complex numbers must be of the Python form "1+1j".

Numbers are taken as ints if and only if they contain Latin decimal
digits and nothing else (see Python str.isdigit(). Thus, "1." and "1.0" and
"1.1" and "1E+2" are all returned as floats.

Dates and times are recognized by regex matching against the expressions below,
which are intended for [ISO 8601] format. There are of course many other
formats out there, which this code does not recognize.

    dateRegex = r'\\d\\d\\d\\d-\\d\\d-\\d\\d'
    timeRegex = r'\\d\\d:\\d\\d:\\d\\d(\\.\\d+)?(Z|[-+]\\d+)?'
    dateTimeRegex = dateRegex + 'T' + timeRegex

Anything not recognized as one of the types just described, is a string.

'''Note''': Autotyping is not used if you pass a list of types to
the `fsplit()` option `types`. With a list, each token is explicitly cast to
the nth type (which may fail). In that case, remember that Python `bool()`
takes any non-empty string as True, even "0" or "False".

=Related Commands=

`splitAt`

The Python csv package [https://docs.python.org/3/library/csv.html]. Its format
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

* Dialect.lineterminator -- Defaults to '\\r\\n'. The reader is hard-coded to recognise either '\\r' or '\\n' as end-of-line, and ignores lineterminator.

* Dialect.quotechar -- A one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters. It defaults to '"'.

* Dialect.quoting -- Controls when quotes should be generated by the writer and recognised by the reader:

    csv.QUOTE_ALL -- quote all fields.

    csv.QUOTE_MINIMAL -- only quote those fields which contain special characters such as delimiter, quotechar or any of the characters in lineterminator.

    csv.QUOTE_NONNUMERIC -- quote all non-numeric fields. Convert all non-quoted fields to type float.

    csv.QUOTE_NONE -- never quote fields, but use escapechar. If escapechar is needed but not set, raise Error.

* Dialect.skipinitialspace -- When True, whitespace immediately following the delimiter is ignored. The default is False.

* Dialect.strict -- When True, raise exception Error on bad CSV input. The default is False.


==Field-related *nix commands==

* awk
* column
* cut
* join
* msort
* paste
* sort
* tab2space
* uniq

===Column numbers only, no fields===

* colrm (N)
* expand
* lam
* look
* sed
* unexpand

=Known bugs and Limitations=

Not sure whether you can (or should be able to) escape in mid-delimiter.

What's the right rule for a quote not immediately following a delimiter?

It might be nice to have a way to change the set of backslash codes,
such as \\b for BEL,

If using `bool` with the `types` option, only the empty string counts as "False".
Probably should add a way to specify other acceptable values, like "0",
"0.0", "1E-200000", "#F", r'^\s*$', or "False".
I have added a `boolCaster()` function for this, but not connected it.


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
    elif (quoteArg == 'SINGLE'):
        lastQuoteMap["'"] = "'"
    elif (quoteArg == 'DOUBLE'):
        lastQuoteMap['"'] = '"'
    elif (quoteArg == 'BOTH'):
        lastQuoteMap["'"] = "'"
        lastQuoteMap['"'] = '"'
    elif (quoteArg == 'ANGLE'):
        lastQuoteMap[chr(0x00AB)] = chr(0x00BB)
    elif (quoteArg == 'CURLY'):
        lastQuoteMap[chr(0x201C)] = chr(0x201D)
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

def dquote(s):
    """Put special marks around a string for display.
    """
    return u"\u00AB" + str(s) + u"\u00BB"

def parseEntity(s:str):
    """Handle XML/HTML entity and numeric character references.
    Just pass this off to Python html package (only imported if needed).
    NOTE: Unknown entities, like '&foo;', do not raise an error.
    """
    from html import unescape
    mat = re.match(r'&(#\d+|#x[\da-f]+|\w[\d\w]*);', s, re.I)
    #print("Match against '%s':\n%s" % (s, mat))
    if (not mat): return None, 0
    result = unescape(mat.group(0))
    return result, len(mat.group(0))

def datetimeCaster(s):
    """Return a date, time, or datetime object created from a string, or
    raises ValueError otherwise.
    """
    dateRegex = r'\d\d\d\d-\d\d-\d\d'
    timeRegex = r'\d\d:\d\d:\d\d(\.\d+)?(Z|[-+]\d+)?'
    dateTimeRegex = dateRegex + 'T' + timeRegex

    from datetime import date
    if (re.match(dateTimeRegex, s)):
        return datetime.datetime(s)
    if (re.match(dateRegex, s)):
        return datetime.date(s)
    if (re.match(timeRegex, s)):
        return datetime.time(s)
    raise ValueError("String cannot be parsed as date and/or time: '%s'" % (s))

def boolCaster(s):
    """Returns True (perhaps a paradox, given that I wrote this function
    on 2020-02-29) for more than just the empty string; False for a similar
    range, and raises ValueError otherwise (like for 'xyz').
    """
    if (s.strip in [ '', '0', 'False' ]): return False
    try:
        if (float(s) == 0): return False
    except ValueError:
        pass
    return True

def autoType(tok:str,
    boolCaster = None,
    datetimeCaster = datetimeCaster,
    specialFloats:bool = False
    ):
    """Convert a string to the most specific type we can.

    @dparam datetimeCaster: Function to produce date/time/datetime or ValueError.
      Defaults to use the datetimeCaster() method below, for ISO 8601 form.
    @param boolCaster: Likewise, but to recognize booleans (for examle, "T"
      and "Nil". Default to None so it doesn't take over commonplace strings.
      No bools are returned unless a function is passed (see boolCaster() below).
    @specialfloats: If set, "NaN" and (optionally signed) "inf" count as floats.

    Complex uses the Python "1+1j" (not "1+1i"!) form)
    Leading and trailing whitespace are stripped for testing, but
    not for returned string values.

    Other types to maybe add:
        SVG paths:    "M 10 10 H 90 V 90 H 10 L 10 10"
        n-D vectors:  "(1.0, -2.1)"
    """
    tok2 = tok.strip()

    if (tok2 is ''):
        return tok
    if (boolCaster):
        try: return boolCaster(tok2)
        except ValueError: pass
    # Prevent 'float' from catching these when not wanted:
    if (not specialFloats and tok2 in ("NaN", "inf", "-inf", "+inf")):
        return tok
    if (tok2.isdigit()):
        return int(tok2)
    try: return datetimeCaster(tok2)
    except ValueError: pass
    try: return int(tok2, 0)
    except ValueError: pass
    try: return float(tok2)
    except ValueError: pass
    try: return complex(tok2)  # Test *after* float
    except ValueError: pass
    return tok

def fsplit(
    # The string to split:
    s:str,
    # Options like Python 'csv' package:
    delimiter:str            = "\t",
    doublequote:bool         = False,  # TODO
    escapechar:str           = "\\",
    lineterminator:str       = "\n",   # UNUSED
    quotechar:str            = '"',
    skipinitialspace:bool    = True,
    strict:bool              = True,
    # Other options:
    multidelimiter:bool      = False,
    xescapes:bool            = False,
    uescapes:bool            = False,
    entities:bool            = False,
    minsplit:bool            = None,
    maxsplit:bool            = None,
    types:bool               = None
    ):
    """Fancier string splitter. Lots of options, and Unicode aware.
    """
    if (delimiter == ''):
        return s.split()
    dlen = len(delimiter)

    currentQuoteMap = setupQuoteMap(quotechar)
    if (skipinitialspace): s = s.lstrip()

    tokens = [ "" ]
    toIgnore= 0
    pendingQuote = None
    escaped = False
    for i, c in enumerate(s):
        if (toIgnore):
            toIgnore -= 1

        elif (pendingQuote):
            if (c == pendingQuote):
                if (doublequote and len(s)>i+1 and s[i+1]==pendingQuote):
                    tokens[-1] += pendingQuote
                    toIgnore = 1
                else:
                    pendingQuote = None
            else:
                tokens[-1] += c

        elif (escaped):
            escaped = False
            if (xescapes and c == 'x'):
                if (len(s)<=i+3):
                    if (strict): raise ValueError("Incomplete xescape.")
                else:
                    try:
                        tokens[-1] += chr(int(s[i+1:i+3], 16))
                        toIgnore = 2
                    except ValueError:
                        if (strict): raise ValueError(
                            "Bad hexadecimal escape '%s'." % (s[i-1:i+3]))
            elif (uescapes and c == 'u'):
                if (len(s)<=i+5):
                    if (strict): raise ValueError("Incomplete uescape.")
                try:
                    tokens[-1] += chr(int(s[i+1:i+5], 16))
                    toIgnore = 4
                except ValueError:
                    if (strict): raise ValueError(
                        "Bad decimal escape '%s'." % (s[i-1:i+5]))
            else:
                tokens[-1] += unescapeViaMap(c)

        elif (c == escapechar):
            escaped = True;

        elif (entities and c == '&'):
            entExpansion, charsUsed = parseEntity(s[i:])
            if (entExpansion is not None):
                tokens[-1] += entExpansion
                toIgnore = charsUsed - 1
            elif (strict):
                raise ValueError("Ill-formed character reference")

        elif (c in currentQuoteMap):
            if (strict and tokens[-1]!=''):
                raise ValueError("Quote is not at start of field")
            pendingQuote = currentQuoteMap[c]

        elif (c == delimiter[0] and s[i:].startswith(delimiter)):
            if (multidelimiter):
                raise ValueError("multidelimiter not yet implemented.")
            if (maxsplit is not None and len(tokens) >= maxsplit):
                tokens.append(s[i+len(delimiter):])
                break
            tokens.append("")
            toIgnore = dlen - 1

        else:
            tokens[-1] += c

    if (strict and (escaped or pendingQuote)):
        raise ValueError("Unresolved escapechar.")
    if (strict and pendingQuote):
        raise ValueError("Unresolved quote (expecting '%s')." % (pendingQuote))
    if (minsplit is not None and len(tokens) < minsplit+1):
        raise ValueError("min %d tokens needed, but found %d." %
            (minsplit, len(tokens)))
    # maxsplit just stops splitting, no error.

    if (types):
        if (isinstance(types, list)):
            for i, typ in enumerate(types):
                if (not typ): continue
                tokens[i] = typ(tokens[i])
        elif (types=='AUTO'):
            for i, token in enumerate(tokens):
                tokens[i] = autoType(token)

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

    def phead(msg): print("\n******* %s" % (msg))

    phead("TAB")
    s = ""
    print("Test string: %s" % (dquote(s)))
    print(fsplit(s))
    s = "no split happens"
    print("Test string: %s" % (dquote(s)))
    print(fsplit(s))
    s = "wee fish\tewe\ta mare\tegrets\tmoose"
    print("Test string: %s" % (dquote(s)))
    print(fsplit(s))

    s = "wee fish,ewe,a mare,egrets,moose"
    phead("Commas, but delim not set")
    print("Test string: %s" % (dquote(s)))
    print(fsplit(s))

    phead("Commas, delim set")
    print("Test string: %s" % (dquote(s)))
    print(fsplit(s, delimiter=','))

    phead("TAB, but escaping the one before 'egrets'")
    s = "wee fish\tewe\ta mare\\tegrets\tmoose"
    print("Test string: %s" % (dquote(s)))
    print(fsplit(s))

    phead("Escaping:")
    s = "aard\\u0076ark|beagle|cat|d\\x6Fg|&#101;&#x67;r&eacute;&#X00000074;"
    print("Test string: %s" % (dquote(s)))
    print("vbar, without special escaping options")
    print(fsplit(s, delimiter='|'))
    print("vbar, with xescapes")
    print(fsplit(s, delimiter='|', xescapes=True))
    print("vbar, with uescapes")
    print(fsplit(s, delimiter='|', uescapes=True))
    print("vbar, with entities")
    print(fsplit(s, delimiter='|', entities=True))
    print("vbar, with all of those")
    print(fsplit(s, delimiter='|', xescapes=True, uescapes=True, entities=True))

    phead("Multi-char delim:")
    s = "lorem##ipsum##dolor##sit##amet"
    print("Test string: %s" % (dquote(s)))
    print("'##'")
    print(fsplit(s, delimiter='##'))

    phead("Quoting:")
    s = 'wee fish$ewe$"a mare"$egrets$"moo$e"'
    print("\nTest string: %s" % (dquote(s)))
    print("delim = '$',  quotechar doublequote")
    print(fsplit(s, delimiter='$', quotechar='"'))

    s = "wee fish$ewe$'a mare'$egrets$'moo$e'"
    print("\nTest string: %s" % (dquote(s)))
    print("delim = '$',  quotechar singlequote")
    print(fsplit(s, delimiter='$', quotechar="'"))

    s = "'wee fish'$ewe$‘a mare’$egrets$“moo$e”"
    print("\nTest string: %s" % (dquote(s)))
    print("delim = '$',  quotechar curlies")
    print(fsplit(s, delimiter='$', quotechar='“”'))

    s = "'wee fish'$ewe$‘a mare’$egrets$“moo$e”"
    print("\nTest string: %s" % (dquote(s)))
    print("delim = '$',  quotechar BOTH")
    print(fsplit(s, delimiter='$', quotechar='“”'))

    #SINGLE DOUBLE ANGLE CURLY ALL
    # quotes inside quotes

    phead("Doubling quotes")
    s = """'Lorem ipsum ''dolor'' sit amet','consectetur adipiscing elit','sed do
eiusmod tempor incididunt ut labore et ''dolor''e magna aliqua','Ut enim ad minim
veniam','quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
commodo consequat','Duis aute irure ''dolor'' in reprehenderit in voluptate velit
esse cillum ''dolor''e eu fugiat nulla pariatur','Excepteur sint occaecat
cupidatat non ''proident''','''sunt'' in culpa qui officia deserunt mollit anim id
est laborum'"""
    print("Test string: %s" % (dquote(s)))
    toks = fsplit(s, delimiter=",", quotechar="'", doublequote=True)
    for i, tok in enumerate(toks):
        print("    %2d: /%s/" % (i, dquote(tok)))

    phead("minsplit, maxsplit:")
    s = "lorem##ipsum##dolor##sit##amet"
    print("\nTest string: %s" % (dquote(s)))
    print("delim = '##', minsplit=99, strict=True")
    try:
        print(fsplit(s, delimiter='##', minsplit=99, strict=True))
    except ValueError as e:
        print("    ValueError: %s" % (e))
    print("delim = '##', maxsplit=3, strict=True")
    print(fsplit(s, delimiter='##', maxsplit=3, strict=True))

    phead("autotype feature:")
    s = "hello,1,,3.14159,-6.022E+23,1.618+2j,NaN,-inf,+inf,world"
    print("Test string: %s" % (dquote(s)))
    stuff = fsplit(s, delimiter=',', types='AUTO')
    for i, x in enumerate(stuff):
        print("    %d: %-16s %s" % (i, dquote(x), type(x)))

    phead("type checking:")

    phead("Errors")
    errTests = [
        "hello \\",
        "hello \\x",
        "hello \\xA",
        "hello \\xZZ",
        "hello \\",
        "hello \\u",
        "hello \\uA",
        "hello \\uAAA",
        "hello &",
        "hello &lt does this even work?",
        "hello &gt.",
        "hello &amp",
        "hello &world;",
        # unclosed quotes, swapped polarity, not at start of field,....
    ]
    for s in errTests:
        print("Test string: %s" % (dquote(s)))
        try:
            print(fsplit(s, delimiter=',', strict=True,
                xescapes=True, uescapes=True, entities=True))
            print("    ******* Ooops, error was not raised *******")
        except ValueError as e:
            print("    ValueError: %s" % (e))

    if (not args.quiet):
        sys.stderr.write("\nDone.\n")
