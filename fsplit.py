#!/usr/bin/env python
#
# fsplit.py: A better (I hope) str.split() or csv package.
# 2020-02-28: Written. Copyright by Steven J. DeRose.
#
#pylint: disable=W0603,W0511
#
import sys
import argparse
import re
from typing import Dict, Any

__metadata__ = {
    'title'        : "fsplit.py",
    'description'  : "A better (I hope) str.split() or csv package.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-02-28",
    'modified'     : "2020-08-08",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

An enhanced `split()` function, and APIs using it that are modelled on
Python's `csv` library (see [https://docs.python.org/3/library/csv.html]).
This library, however, can also handle:

===A wider range of syntax options===

* Multi-character delimiters (unlike most utilities)
* Multiple alternative quotechars (for example, single and double)
* Distinct open and close quotechars
* Unicode quote characters (curly, angle, etc)
* Expanding special chars like
\\xFF (`xescapes`); \\uFFFF (`uescapes`); &#xFFFFF;, &bull;, etc. (`entities`)
* Ignoring repeated delimiters (like `sed` can) (`multidelimiter`)

===Datatype-related features===

* Checking and casting input fields to specified datatypes (`typeList` -- see
also `Datatypes.py`).
* Formatting output fields like Python `format()`
* Auto-sensing datatypes of input data and casting (for example, r'\\d+'
to int, ISO 8601 dates, Python complex numbers,...).

* Formatting output fields appropriately for their datatypes
* Auto-casting output strings appropriately for their apparent datatypes.

It also handles the usual features of `csv` and `string.split()`:

* Escaped (backslashed) characters (`escapechar`)
* Doubled delimiters (`doublequote`)
* Quoted fields (`quotechar` and `quoting`)
* Field names specified in header or via API
* Optionally discarding leading whitespace (`skipinitialspace`)
* Limiting the number of splits (`maxsplit`)

See "To do" and my related scripts such as Record.py, Homogeneous.py, Datatypes.py for some features that may be added.


=Usage=

It's probably cleanest (and slightly faster) to define the set of
options you want as a `DialectX` (similar to `csv.Dialect`) and then just
pass it to `fsplit()` along with each record in turn:

    myForm = DialectX('bestCSVever',
        delimiter='\\t',
        doublequote=False,
        escapechar='\\\\',
        quotechar='"',
        xescapes=True)
    for rec in f.readlines():
        myFields = fsplit(rec, dialect=myForm)
        print("Record %d:\\n    " + join("\\n    ", myFields))

If you prefer, you can pass the format options directly to `fsplit()`:
    for rec in f.readlines():
        myFields = fsplit(rec, delimiter='\\t',
            doublequote=False, escapechar='\\\\', quotechar='"', xescapes=True)
        print("Record %d:\\n    " + join("\\n    ", myFields))

Or you can operate at the file level, using any of these:

* DictReader(f, fieldnames=None, restkey=None, restval=None, dialect=None)

`f` must be an open file handler or other readable. Usage is just like
the corresponding class in `csv`:

    import fsplit
    with codecs.open('names.csv', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row['first_name'], row['last_name'])

fieldname can be read via a header record, and/or specified to the constructor.

* DictWriter(f, fieldnames, restval='', extrasaction='raise', dialect=None)

    import fsplit
    with codecs.open('names.csv', 'w', encoding='utf-8') as csvfile:
        fieldnames = ['first_name', 'last_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'first_name': 'Baked', 'last_name': 'Beans'})
        writer.writerow({'first_name': 'Lovely', 'last_name': 'Spam'})
        writer.writerow({'first_name': 'Wonderful', 'last_name': 'Spam'})

* reader()

* writer()


==DialectX options==

A dialect has many options. Several match ones from `csv`, with
the same names and at least the same values. Those like in `csv` include:

* ''delimiter'':str = "\\t" -- The field separator character or string.

* ''doublequote'':bool = True -- If set, allow putting `quotechar` inside
a quoted string, by doubling it. I'm not fond of this defaulting True,
but that's what Python `csv` does, so I stuck with it.

* ''escapechar'':str = "\\\\" -- If set, this character can be put before
the quotechar, delimiter, or itself, to make that character literal rather
than special. The escapechar can also be used before any of
'f', 'n', 'r', 't', 'v', '\\\\', or '0' for the usual meanings.

* ''lineterminator'':str = "\\n" -- What string to write out to indicate
end-of-record.

* ''quotechar'':str = '"' -- Sets what characters or character-pairs are recognized
as quotes (`setupQuoteMap()` handles all of this). Where Python `csv` and
many *nix utilities only accept a single delimiter characters, this also
accepts distinct open and close quotes, as well as an option to allow both
single and double quotes. You can also specify the type of quote via
mnemonics, including ALL, which allows any of 12 Unicode symmetric pairs
as well as plain apostrophe and double quote.

The known pairs are defined in `UQuotePairs`, an array of triples, each like:

    (0x00AB, 0x00BB, "[LEFT,RIGHT]-POINTING DOUBLE ANGLE QUOTATION MARK" )

''Note'': One sometimes seems back-quote as open paired with either
apostrophe or itself as close. These are not supported, but should work
if set explicitly or as entries to `UQuotePairs`.

** ''None'': or '', no characters are treated as quotes.
** ''a single character'': that character is the only recognized quote,
and serves as both open and close.
** ''a 2-character string'': the first character is treated as open quote,
and the second as the corresponding close quote. Only the close quote is
subject to `doublequote`, though both are subject to `escapechar`.
With `MINIMAL` quoting, only the close quote gets escaped within values.
** ''SINGLE'': A synonym for "'".
** ''DOUBLE'': A synonym for '"'.
** ''ANGLE'': A synonym for u"\\xAB\\xBB" (Unicode
LEFT-POINTING DOUBLE ANGLE QUOTATION MARK and
RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK).
** ''CURLY'': A synonym for u"\\u201C\\u201D" (Unicode
LEFT DOUBLE QUOTATION MARK and
RIGHT DOUBLE QUOTATION MARK).
** ''BOTH'': single quote (apostrophe) and double quote are each
recognized as quotes, as is common in programming and markup languages.
** ''ALL'': single and double quotes are supported (as with "BOTH"),
as well as a wide range of Unicode quotation marks, including curly single
and double, angle quotes, and so on.

* ''quoting'': When fields should be quoted. Specify one of these
constants, whose names and values are intended to be the same as in `csv`:

    fsplit.QUOTE_MINIMAL    = 0  # only quote if needed.
    fsplit.QUOTE_ALL        = 1  # quote all fields.
    fsplit.QUOTE_NONNUMERIC = 2  # quote all non-numeric fields.
    fsplit.QUOTE_NONE       = 3  # never quote fields, but use escapechar

* ''skipinitialspace'':bool = True -- If set, `s` has any initial (Unicode)
whitespace stripped before parsing.

* ''strict'':bool = True -- If set, problems raise `ValueError`
instead of being worked around or ignored.


===Additional options===

The following options are not available in Python's `csv` package:

* ''comment'':str = None -- If set and not '', lines starting with
this string are treated as comments rather than data.

* ''entities'':bool = False -- If set, character references are recognized
and replaced as in HTML. Decimal (&#8226;), hexadecimal (&#x2022;), and named
(&bull;) forms are all supported.
NOTE: These are converted by Python's `html.unescape()` method, which does not
raise an error for Unknown entities such as `&foo;`.

* ''maxsplit'':int = None -- If specified, splitting stops after this many splits
have occurred (making this many + 1 tokens).

* ''minsplit'':int = None -- If specified, an exception is raised if fewer than
this many splits are made.

* ''multidelimiter'':bool = False -- If set, multiple adjacent delimiters do
NOT result in empty tokens, but be treated the same as a single delimiter.
This would typically be done when the delimiter is just a space.
Empty fields can, however, be inserted by quoting them (because the delimiters
on each side are no longer "adjacent").

* ''typeList'' = None -- If set, this option must be either a list of
`type`s, or the keyword "AUTO". If provided as a list of types, the parsed
fields are cast to the specified datatypes, in respective order.
Casts can of course fail, resulting in exceptions (providing
rudimentary validation). If there are more fields
than entries in the list, the remaining items stay as strings.
Empty fields always pass. The list should contain the actual types, not
their string names. For example:

    types = [ int, int, float, bool, str ]

If using `bool`, remember that Python
takes any non-empty string as True, even strings like "0" or "False".

If specified as `AUTO` instead of a list of types (or the default None),
tokens are examined and automatically cast to the
most specific type they can, from among datetime, int, float, complex, or str.
Booleans are not attempted (though see below under [autoTyping]).

The `typeList` option is still experimental.

* ''uescapes'':bool = True -- If set, escapes like \\uFFFF may be used.
This uses `escapechar` (not necessarily backslash).
If `escapechar` is set but not `uescapes`, an escapechar before 'u' will
not raise an error (even with `strict`), because that escape just ensures
(unnecessarily) that the 'u' is literal.

* ''xescapes'':bool = True -- If set, escapes like \\xFF may be used.
This uses `escapechar` (not necessarily backslash).
If `escapechar` is set but not `xescapes`, an escapechar before 'x' will
not raise an error (even with `strict`), because that escape just ensures
(unnecessarily) that the 'x' is literal.


===autoTyping===

If `typeList='AUTO'` is specified, each field is passed to this function, which
tries to cast it to the most specific appropriate type:

    autoType(tok:str, boolCasterFunc=None, specialFloats=False)

Leading and trailing whitespace are stripped before testing for various types.
However, items that remain as strings are returned with the whitespace intact
(unless the `skipinitialspace` option is also set).

If `boolCaster` is supplied, it must take a string argument (the token,
with leading and trailing whitespace intact), and return True or False,
or raise ValueError if the value is not an acceptable string representation of
a boolean (by whatever rules the implementer likes). By default no such
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

Python `csv` [https://docs.python.org/3/library/csv.html].

`csv2xml.py` -- Obsolete precursor to `fsplit.py`, but has a number of
possibly useful export formats.


For a more complete list, including generalized and Unicode-aware ports
of several *nix utilities, see [http://github.com/sderose/CSV] and
[http://github.com/sderose/XML/CONVERT].


=Known bugs and Limitations=

Multi-char delim test is failing.

reader, writer, DictReader, and DictWriter are new and not well tested.
They do not yet support quoted fields that cross lines, either.

Not sure whether you can (or should be able to) escape in mid-delimiter.

What's the right rule for a quote not immediately following a delimiter?
As in
    1, "two", 3, 4"five"5, 6

It might be nice to have a way to change the set of backslash codes,
such as \\b for BEL, etc.

If using `bool` with the `types` option,
only the empty string counts as "False".
Probably should add a way to specify other acceptable values, like "0",
"0.0", "1E-200000", "#F", r'^\\s*$', or "False".
I have added a `boolCaster()` function for this, but not connected it.

fieldnames passed to DictReader should probably be allowed to override any
read from a header record. But currently they're compared and an exception
is raised if they don't match.


=To do=

* Test `quotedNewline` support.

* More flexible delimiters:
    ** regex delimiters
    ** the "whitespace to nonspace transition" approach (like awk, column, and sort)
    ** Support for cycling delimiters (like 'paste -d)

* Special treatment of empty/missing fields
* Field Defaults
* Controllable Boolean values (see csv2xml.py)
* Creating NamedTuple or tuple instead of list or dict?

* Maybe support CONLL format (see Stanford Corenlp output options)?
This is TSV, but with a blank line between groups of records (each of which
amounts to a sentence). Easiest support may be to return one extra field,
which is a generated group number, incremented at each blank line. And maybe
throw an exception on the blank lines, so the user can tell?

* Support for a wider range of formats (probably will be done by separate packages with much the same API), such as:
    ** HTML and XML tables
    ** XSV
    ** MECS, TAG, Clix, and similar markup systems
    ** MediaWiki and MarkDown tables
    ** JSON {[]}, [[]], etc., and similar Perl and Python arrangements
    ** s-expressions
    ** SQL INSERT statements

* Sub/alternate class for fixed column widths?


=History=

Written by Steven J. DeRose, 2020-02-28.

* 2020-08-07: Add classes and API to look essentially like Python `csv`,
including `DictReader` and `DictWriter`.
Separate options into a "Dialect" class, add `add_my_arguments`.
Start `multidelimiter`. Add `comment`. Rewrite doc.

* 2020-09-06: Better error messages. Renamed 'types' to 'typeList'.
Refactor test cases and error handling.

* 2020-10-21: Start support for controlling order of fields with DictWriter.
Pull in `formatScalar` from my `alogging`.


=Rights=

Copyright 2020-02-28 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].

=Options=
"""

###############################################################################
#
# These are the same values as in Python's csv package
QUOTE_MINIMAL       = 0  # only quote if needed.
QUOTE_ALL           = 1  # quote all fields.
QUOTE_NONNUMERIC    = 2  # quote all non-numeric fields.
QUOTE_NONE          = 3  # never quote fields, but use escapechar

#POINTING_CHAR = "\u261e"  # Pointing finger
POINTING_CHAR = "\u23E9"  # Double arrow button

class DialectX:
    """Just a bundle of settings for now.
    """
    def __init__(self,
        dialectName:str,

        # Options like Python 'csv' package:
        delimiter:str            = "\t",    # What char?
        doublequote:bool         = True,    # TODO Support ""
        escapechar:str           = "\\",    # Backslashing?
        lineterminator:str       = "\n",    # What's the line-break?
        quotechar:str            = '"',     # What's the quote mark?
        quoting:int              = QUOTE_NONNUMERIC,  # What to quote
        skipinitialspace:bool    = True,    # Strip leading spaces
        strict:bool              = True,

        # Other options:
        comment:str              = None,    # Marker for comment lines
        entities:bool            = False,
        maxsplit:bool            = None,    # Limit to this many fields
        minsplit:bool            = None,    # Scream if < this many fields
        multidelimiter:bool      = False,   # Ignore repeated delimiters?
        typeList:bool            = None,    # To support datatypes
        uescapes:bool            = False,   # Interpret \uFFFF
        xescapes:bool            = False,   # Interpret \xFF
        quotedNewline:bool       = False    # Allow multiline quoted values
    ):
        self.dialectName         = dialectName

        # Options like Python 'csv' package:
        self.delimiter           = delimiter
        self.doublequote         = doublequote
        self.escapechar          = escapechar
        self.lineterminator      = lineterminator
        self.quotechar           = quotechar
        self.quoting             = quoting
        self.skipinitialspace    = skipinitialspace
        self.strict              = strict

        # Other options:
        self.comment             = comment
        self.entities            = entities
        self.maxsplit            = maxsplit
        self.minsplit            = minsplit
        self.multidelimiter      = multidelimiter
        self.typeList            = typeList  # Could also be "AUTO"
        self.uescapes            = uescapes
        self.xescapes            = xescapes
        self.quotedNewline       = quotedNewline

        global dialects
        dialects[dialectName] = self

    __theOptionNames__ = {
        # name               ( type, default )
        "delimiter":         ( str, "\t" ),
        "doublequote":       ( bool, False ),
        "escapechar":        ( str, "\\" ),
        "lineterminator":    ( str, "\n" ),
        "quotechar":         ( str, '"' ),
        "quoting":           ( str, "MINIMAL" ),
        #  [ 'ALL', 'MINIMAL', 'NONNUMERIC', 'NONE'],
        "skipinitialspace":  ( bool, True ),
        "strict":            ( bool, True ),

        # fsplit only:
        "comment":           ( str,  None ),
        "entities":          ( bool, False ),
        "maxsplit":          ( int,  None ),
        "minsplit":          ( int,  None ),
        "multidelimiter":    ( bool, False ),
        "types":             ( str,  None ),
        "uescapes":          ( bool, False ),
        "xescapes":          ( bool, False ),
        "quotedNewline":     ( bool, False ),
    }

    def apply_arguments(self, theArgs:argparse.Namespace) -> None:
        """Call this to move the arguments (typically added by
        add_my_arguments), to the current instance.
        """
        for k in DialectX.__theOptionNames__:
            if (k in theArgs.__dict__ and theArgs.__dict__[k] is not None):
                self.__dict__[k] = theArgs.__dict__[k]

    @staticmethod
    def add_my_arguments(parser, prefix="", csvOnly=False):
        """Add argparse arguments for our options.
        @param prefix: If specified, add this at the start of all the names,
        to prevent name conflicts.
        @param csvOnly: If set, don't include arguments specific to fsplit.
        """
        pre = "--" + prefix

        # Options like Python 'csv' package:
        parser.add_argument(
            pre+"delimiter",          type=str, default="\t",
            help='.')
        parser.add_argument(
            pre+"doublequote",        action="store_true",
            help='.')
        parser.add_argument(
            pre+"escapechar",         type=str, default="\\",
            help='.')
        parser.add_argument(
            pre+"lineterminator",     type=str, default="\n",
            help='.')
        parser.add_argument(
            pre+"quotechar",          type=str, default='"',
            help='.')
        parser.add_argument(
            pre+"quoting",            type=str, default="MINIMAL",
            choices=[ 'ALL', 'MINIMAL', 'NONNUMERIC', 'NONE'],
            help='When should fields be quoted?.')
        parser.add_argument(
            pre+"skipinitialspace",   type=bool, default=True,
            help='.')
        parser.add_argument(
            pre+"strict",             type=bool, default=True,
            help='.')

        if (csvOnly): return

        # Other options, as for my fsplit.py package.
        parser.add_argument(
            pre+"comment",            type=str, default=None,
            help='.')
        parser.add_argument(
            pre+"entities",           action="store_true",
            help='.')
        parser.add_argument(
            pre+"maxsplit",           type=int, default=None,
            help='.')
        parser.add_argument(
            pre+"minsplit",           type=int, default=None,
            help='.')
        parser.add_argument(
            pre+"multidelimiter",     action="store_true",
            help='.')
        parser.add_argument(
            pre+"types",              type=str, action="append",
            choices=[ 'str', 'int', 'float', 'bool' ],
            help='A list of types for the fields (repeatable).')
        parser.add_argument(
            pre+"uescapes",           action="store_true",
            help='.')
        parser.add_argument(
            pre+"xescapes",           action="store_true",
            help='.')

        return


###############################################################################
#
class DictReader:
    """Modelled after Python 'csv' package.
    """
    def __init__(self,
        f,                  # file handle, File object, etc.
        fieldnames=None,    # iterable of names (None->use header rec)
        restkey=None,       # store any extras as list under this key
        restval=None,       # default any missing fields to this value
        dialect=None,       #
        # *args,  # ???
        #**theKwds
        ):
        self.f          = f
        self.recnum     = 0
        self.fieldnames = fieldnames or []
        self.restkey    = restkey
        self.restval    = restval
        self.dialect    = dialect

        self.line_num   = 0
        self.fieldnamesFromHeader = []

        # TODO: set up the kwargs

    def __next__(self):
        """Read and back the next record as a dict of fields by name.
        Quoted fields that span lines are still experimental; and by
        definition are unbounded, making is kinda awful to debug.
        """
        startingRecnum = self.recnum
        priorParts = ""
        while (1):
            rec = self.f.readline()
            self.recnum += 1
            if (rec==""):
                if (priorParts != ""):
                    raise ValueError("EOF found parsing record started at %d."
                        % (startingRecnum))
                return None
            if (self.dialect.comment and
                rec.startswith(self.dialect.comment)):
                pass
            rec = priorParts + rec
            if (self.line_num==0 and self.dialect.header):
                self.line_num += 1
                self.fieldnamesFromHeader = fsplit(rec, self.dialect)
                if (self.fieldnames and
                    self.fieldnamesFromHeader != self.fieldnames):
                    raise ValueError("Header does not match " +
                        "dialect fieldnames:\n    %s\n    %s" %
                        (self.fieldnames != self.fieldnamesFromHeader))
            else:
                try:
                    fields = fsplit(rec, self.dialect)
                except UnclosedQuote:
                    priorParts += rec
                    continue
                fieldDict = {}
                for fNum, fd in fields:
                    fieldDict[self.fieldnames[fNum]] = fd
                return fieldDict
        return None  # EOF


###############################################################################
# Thrown when parsing a line and it ends mid-quote, iff the dialect
# says that's ok. Caller should catch it, append next line, and call again.
#
class UnclosedQuote(Exception):
    pass


###############################################################################
#
staticDialect = None
staticFile = None
dialects = {}

def reader(csvfile, **formatParams):
    """Python's CSV doesn't treat this as a class (unlike DictReader).
    """
    global staticDialect
    staticDialect = DialectX(**formatParams)
    for rec in csvfile.readlines():
        if (staticDialect.comment and
            rec.startswith(staticDialect.comment)): continue
        fields = fsplit(rec, staticDialect)
        yield fields
    return None


###############################################################################
#
class DictWriter:
    """Like 'writer' but takes dicts, and writes their members in the
    order specified by 'fieldnames'.

    When using 'writerow()', if 'fieldnames':
        is None: fields are written in alphabetical order.
        mentions a field that is not known, it is written as "".
        mentions a field that is missing, it is written as ""
            (or an type-appropriate default, if the type is known).
        does not list a field that does exist, it is omitted.

    The goal here is that the same inventory of fields will be written for
    every record, regardless of whether some are sometimes missing or extra.
    For some potential output formats, it may be ok to omit missing/ empty/
    default fields. This is not yet supported.
    """

    # For specifying fieldFormats: format strings like "%-8.4f", etc.
    _formatRegex = r'%-?\d+(\.\d+)[dxobsfg]'

    def __init__(self,
        f,
        #*args1,
        fieldnames:list=None,
        fieldformats:list=None,
        restval:str='',
        extrasaction:str='raise',
        dialect:str='excel'
        #**kwds1
        ):
        self.f            = f
        self.fieldnames   = fieldnames
        self.restval      = restval
        self.extrasaction = extrasaction
        self.dialect      = dialects[dialect]

        if (fieldnames):
            if (not isinstance(fieldnames, list)):
                raise ValueError("fieldnames must be a list.")
            if (fieldformats and not len(fieldnames) == len(fieldformats)):
                raise ValueError("")
        if (fieldformats):
            for f in fieldformats:
                if (not re.match(DictWriter._formatRegex, f)):
                    raise ValueError("Unparseable fieldFormat '%s'." % (f))

    def writeheader(self) -> None:
        self.writerow(self.fieldnames)

    def writerows(self, rows:list) -> int:
        rnum = 0
        for row in rows:
            rnum += 1
            self.writerow(row)
        return rnum

    def writerow(self, row:dict) -> None:
        buf = ""
        if (self.fieldnames is None):
            self.fieldnames = sorted(row.keys())
        for _, fname in enumerate(self.fieldnames):
            #fname = self.fieldnames[fnum]
            fval = row[fname] if fname in row else ""
            formattedVal = self.formatOneField(fname, fval)
            buf += formattedVal + self.dialect.delimiter
        buf[-len(self.dialect.delimiter):] = self.dialect.lineterminator
        self.f.write(buf)

    def writecomment(self, s:str):
        self.f.write(self.dialect.comment + s + self.dialect.lineterminator)

    def formatOneField(self, fname:str, fval:Any) -> str:
        return self.formatScalar(fval)

    def formatScalar(self, obj) -> str:  # From alogging.py
        ty = type(obj)
        if (obj is                             None):
            return self.disp_None
        elif (isinstance(obj,                  str)):
            return '"%s"' % (obj)
        elif (isinstance(obj,                  bytearray)):
            return 'b"%s"' % (obj)
        #elif (isinstance(obj,                  buffer)):
        #    return '"%s"' % (obj)
        #elif (isinstance(obj,                  storage)):
        #    return "%s" % (obj)

        elif (isinstance(obj,                  bool)):
            if (obj): return "True"
            return "False"

        elif (isinstance(obj,                  int)):
            return "%8d" % (obj)
        elif (isinstance(obj,                  float)):
            return "%12.4f" % (obj)
        elif (isinstance(obj,                  complex)):
            return "%s" % (obj)

        elif (isinstance(obj,                  dict)):
            return "{|%d|}" % (len(obj))
        elif (isinstance(obj,                  list)):
            return "[|%d|]" % (len(obj))
        elif (isinstance(obj,                  tuple)):
            return "(|%d|)" % (len(obj))
        elif (isinstance(obj,                  set)):
            return "[set |%d|]" % (len(obj))
        elif (isinstance(obj,                  frozenset)):
            return "[frset |%d|]" % (len(obj))

        elif (isinstance(obj,                  object)):
            return "[%s |%d|]" % (ty, len(obj))
        return "[???] %s" % (obj)
        # end formatScalar


###############################################################################
# Why isn't this just a class, like DictWriter?
#
def writer(csvfile, **formatParams):
    global staticDialect, staticFile
    staticDialect = DialectX(**formatParams)
    staticFile = csvfile

def writeheader(fieldnames:list) -> None:
    writerow(fieldnames)

def writerow(row:list) -> None:
    buf = ""
    for field in row:
        buf += field + staticDialect.delimiter
    buf[-len(staticDialect.delimiter):] = staticDialect.lineterminator
    staticFile.write(buf)


###############################################################################
#
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
    (0x00AB, 0x00BB, "[LEFT,RIGHT]-POINTING DOUBLE ANGLE QUOTATION MARK" ),
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

def setupQuoteMap(quoteArg:str) -> Dict:
    """Given a specification of a kind of quoting, return a dict that
    maps one or more "open" quote characters to their corresponding "close"
    quote characters (which may be the same, as with straight quotes and
    apostrophers; or different, as with curly quotes).

    @param quoteArg may be specified:
        as a mnemonic (SINGLE, DOUBLE, BOTH, ANGLE, CURLY, or ALL);
        as a single character to serve as both open and close; or
        as a string of two characters, open then close.
    """
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

def unescapeViaMap(c:str) -> str:
    if (c in escapeMap): return escapeMap[c]
    return c

def dquote(s:str) -> str:
    """Put double angle quotes around a string for display.
    """
    return u"\u00AB" + str(s) + u"\u00BB"

def parseEntity(s:str) -> (str, int):
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


###############################################################################
#
class DatatypeHandler:
    """Check and cast among some types.
    See also: CSV/countData.TrivialTypes;
              PYTHONLIBS/Datatypes.py
              PYTHONLIBS/Homogeneous.py
              XML/SCHEMAS/ElementManager.py:class AttrTypes
              alogging/formatRec
    """
    def __init__(self,
        boolCasterFunc=None,
        datetimeCasterFunc=None,
        specialFloats:bool = False
        ):
        """
        @param datetimeCasterFunc:
            Function to produce date/time/datetime or ValueError.
            Defaults to use the datetimeCaster() method below, for ISO 8601 form.
        @param boolCasterFunc:
            Likewise, but to recognize booleans (for examle, "T" and "Nil".
            Default to None so it doesn't take over commonplace strings.
            No bools are returned unless a function is passed (see boolCaster()).
        @specialfloats:
            If set, "NaN" and (optionally signed) "inf" count as floats.
        """
        if (boolCasterFunc): self.boolCasterFunc = boolCasterFunc
        else: self.boolCasterFunc = self.boolCaster

        if (datetimeCasterFunc): self.datetimeCasterFunc = datetimeCasterFunc
        else: self.datetimeCasterFunc = self.datetimeCaster

        self.specialFloats = specialFloats

    def handleDatatypes(self, d:DialectX, tokens:list) -> None:
        #import Datatypes
        if (isinstance(d.typeList, list)):
            for i, typ in enumerate(d.typeList):
                if (not typ): continue
                tokens[i] = typ(tokens[i])
        elif (d.typeList=='AUTO'):
            for i, token in enumerate(tokens):
                tokens[i] = self.autoType(token)
        else:
            raise ValueError(
                "typeList option must be 'AUTO' or a list of types, not '%s'." %
                (type(d.typeList)))

    @staticmethod
    def datetimeCaster(s:str) -> str:
        """Return a date, time, or datetime object created from a string, or
        raises ValueError otherwise.
        """
        dateRegex = r'\d\d\d\d-\d\d-\d\d'
        timeRegex = r'\d\d:\d\d:\d\d(\.\d+)?(Z|[-+]\d+)?'
        dateTimeRegex = dateRegex + 'T' + timeRegex

        from datetime import datetime
        if (re.match(dateTimeRegex, s)):
            return datetime.datetime(s)
        if (re.match(dateRegex, s)):
            return datetime.date(s)
        if (re.match(timeRegex, s)):
            return datetime.time(s)
        raise ValueError("String cannot be parsed as date and/or time: '%s'" % (s))

    @staticmethod
    def boolCaster(s:str) -> bool:
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

    def autoType(self, tok:str) -> Any:
        """Convert a string to the most specific type we can.

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
        if (self.boolCasterFunc):
            try: return self.boolCasterFunc(tok2)
            except ValueError: pass
        # Prevent 'float' from catching these when not wanted:
        if (not self.specialFloats and tok2 in ("NaN", "inf", "-inf", "+inf")):
            return tok
        if (tok2.isdigit()):
            return int(tok2)
        try: return self.datetimeCasterFunc(tok2)
        except ValueError: pass
        try: return int(tok2, 0)
        except ValueError: pass
        try: return float(tok2)
        except ValueError: pass
        try: return complex(tok2)  # Test *after* float
        except ValueError: pass
        return tok


###############################################################################
# The function that actually parses up lines, dealing with various escaping
# and quoting variations, etc.
#
dtHandler = None                        # TODO: make better

def fsplit(
    s:str,                              # The string to split:
    dialect:DialectX         = None,    # The DialectX to assume

    # Manual options like Python 'csv' package:
    delimiter:str            = "\t",    # Multi-character ok, but not regex
    doublequote:bool         = False,   # TODO
    escapechar:str           = "\\",
    lineterminator:str       = "\n",    # UNUSED?
    quotechar:str            = '"',     # 1 char, 2 chars, or mnemonic
    quoting:int              = QUOTE_NONNUMERIC,
    skipinitialspace:bool    = True,
    strict:bool              = True,

    # Other manual options:
    multidelimiter:bool      = False,
    xescapes:bool            = False,    # Recognize \xFF?
    uescapes:bool            = False,    # Recognize \uFFFF?
    entities:bool            = False,    # Expand HTML special chars?
    minsplit:bool            = None,     # Min number of fields - 1
    maxsplit:bool            = None,     # Max number of fields - 1
    typeList:bool            = None      # type to cast each field to
    ) -> list:
    """Fancier string splitter. Lots of options, and Unicode aware.
    """
    if (dialect is None):
        dialect = DialectX(
            "FROM_ARGS",
            delimiter           = delimiter,
            doublequote         = doublequote,
            escapechar          = escapechar,
            lineterminator      = lineterminator,
            quotechar           = quotechar,
            quoting             = quoting,
            skipinitialspace    = skipinitialspace,
            strict              = strict,
            multidelimiter      = multidelimiter,
            xescapes            = xescapes,
            uescapes            = uescapes,
            entities            = entities,
            minsplit            = minsplit,
            maxsplit            = maxsplit,
            typeList            = typeList,  # mapTypeNames()
        )
    else:
        raise ValueError("dialect is a %s, not a DialectX:\n%s" %
            (type(dialect), dialect))

    d = dialect

    if (d.delimiter == ''):
        return s.split()
    dlen = len(d.delimiter)

    currentQuoteMap = setupQuoteMap(d.quotechar)
    if (d.skipinitialspace): s = s.lstrip()

    tokens = [ "" ]
    toIgnore= 0
    pendingQuote = None
    escaped = False
    i = 0
    for i, c in enumerate(s):
        if (toIgnore):
            toIgnore -= 1

        elif (pendingQuote):
            if (c == pendingQuote):
                if (d.doublequote and len(s)>i+1 and s[i+1]==pendingQuote):
                    tokens[-1] += pendingQuote
                    toIgnore = 1
                else:
                    pendingQuote = None
            else:
                tokens[-1] += c

        elif (escaped):
            escaped = False
            if (d.xescapes and c == 'x'):
                if (len(s)<=i+3):
                    if (d.strict): raise ValueError(
                        "Incomplete xescape at '%s'." % (context(s, i)))
                else:
                    try:
                        tokens[-1] += chr(int(s[i+1:i+3], 16))
                        toIgnore = 2
                    except ValueError as e:
                        if (d.strict):
                            raise ValueError("Bad hexadecimal escape at '%s'." %
                                (context(s, i))) from e
            elif (d.uescapes and c == 'u'):
                if (len(s)<=i+5):
                    if (d.strict): raise ValueError(
                        "Incomplete uescape at '%s'." % (context(s, i)))
                try:
                    tokens[-1] += chr(int(s[i+1:i+5], 16))
                    toIgnore = 4
                except ValueError as e:
                    if (d.strict): raise ValueError(
                        "Bad decimal escape at '%s'." % (context(s, i))) from e
            else:
                tokens[-1] += unescapeViaMap(c)

        elif (c == d.escapechar):
            escaped = True

        elif (d.entities and c == '&'):
            entExpansion, charsUsed = parseEntity(s[i:])
            if (entExpansion is not None):
                tokens[-1] += entExpansion
                toIgnore = charsUsed - 1
            elif (d.strict):
                raise ValueError(
                    "Ill-formed character reference at '%s'." % (context(s, i)))

        elif (c in currentQuoteMap):
            if (d.strict and tokens[-1]!=''):
                raise ValueError(
                    "Quote is not at start of field (preceded by '%s') at '%s'." %
                    (tokens[-1], context(s, i)))
            pendingQuote = currentQuoteMap[c]

        elif (c == d.delimiter[0] and context(s, i).startswith(d.delimiter)):
            if (d.multidelimiter):
                nDelims = 0
                while (s[i+nDelims*dlen].startswith(d.delimiter)): nDelims += 1
                toIgnore = (nDelims * dlen) - 1
            if (d.maxsplit is not None and len(tokens) >= d.maxsplit):
                tokens.append(s[i+len(d.delimiter):])
                break
            tokens.append("")

        else:
            tokens[-1] += c

    if (pendingQuote):
        # If the end of line is still inside quotes, and that's allowed,
        # throw exception, to signal caller to append another line and
        # call us to parse again. Not efficient, but easy.
        if (d.quotedNewline):
            raise UnclosedQuote()
        if (d.strict):
            raise ValueError("Unresolved quote (expected '%s') at '%s'." %
                (pendingQuote, context(s, i)))
    if (d.strict and (escaped or pendingQuote)):
        raise ValueError("Unresolved escapechar at '%s'." % (context(s, i)))
    if (d.minsplit is not None and len(tokens) < d.minsplit+1):
        raise ValueError("min %d tokens needed, but found %d at '%s'." %
            (d.minsplit, len(tokens), context(s, i)))
    # maxsplit just stops splitting, no error.

    if (d.typeList): dtHandler.handleDatatypes(d, tokens)
    return tokens

def context(txt:str, i:int, sideSize=16):
    """Extract a little context around a given point, and mark the spot.
    """
    stPos = i - sideSize
    if (stPos < 0): stPos = 0
    enPos = i + sideSize
    if (enPos > len(txt)): enPos = len(txt)
    return txt[stPos:i] + POINTING_CHAR + txt[i:enPos]

typeMap = {
    'str':    str,
    'bool':   bool,
    'int':    int,
    'float':  float,
}

def mapTypeNames(types):
    """Convert a string type name, or an actual type, to the type.
    This is useful if a caller wants to let the user specify types, say,
    in command-line options, where they can't get a real Python type.
    """
    realTypes = []
    for t in types:
        if (isinstance(t, type)):
            realTypes.append(t)
        elif (isinstance(t, str) and t in typeMap):
            realTypes.append(typeMap[t])
        else:
            realTypes.append(None)
    return realTypes


###############################################################################
# Main
#
if __name__ == "__main__":
    def anyInt(x):
        return int(x, 0)

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
               description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(
            description=descr)

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

    def testPlus(s, **kwargs):
        """Run a test that we expect to pass (or at least not die).
        """
        print("\nTest string: %s" % (dquote(s)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s"' % (k, v)
        if (buf): print(" args: " + buf)
        theFields = []
        try:
            if (kwargs):
                theFields = fsplit(s, **kwargs)
            else:
                theFields = fsplit(s)
        except ValueError as e:
            print("******* Exception:\n    %s" % (e))
        if (theFields): print("    ==> %s" % (theFields))
        return theFields

    def testMinus(s, **kwargs):
        """Run a test that we expect to fail.
        """
        print("\nTest string: %s" % (dquote(s)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s"' % (k, v)
        if (buf): print(" args: " + buf)
        theFields = []
        try:
            if (kwargs):
                theFields = fsplit(s, **kwargs)
            else:
                theFields = fsplit(s)
            print("    ******* Ooops, error was not raised *******")
        except ValueError as e:
            print("    (expected) Exception: %s" % (e))
        if (theFields): print("    ==> %s" % (theFields))
        return theFields

    def phead(msg): print("\n******* %s" % (msg))

    phead("TAB")
    s0 = ""
    testPlus(s0)
    s0 = "no split happens"
    testPlus(s0)
    s0 = "wee fish\tewe\ta mare\tegrets\tmoose"
    testPlus(s0)

    s0 = "wee fish,ewe,a mare,egrets,moose"
    phead("Commas, but delim not set")
    testPlus(s0)

    phead("Commas, delim set")
    testPlus(s0, delimiter=',')

    phead("TAB, but escaping the one before 'egrets'")
    s0 = "wee fish\tewe\ta mare\\\tegrets\tmoose"
    testPlus(s0)

    phead("Escaping:")
    s0 = "aard\\u0076ark|beagle|cat|d\\x6Fg|&#101;&#x67;r&eacute;&#X00000074;"

    print("vbar, without special escaping options")
    testPlus(s0, delimiter='|')
    print("vbar, with xescapes")
    testPlus(s0, delimiter='|', xescapes=True)
    print("vbar, with uescapes")
    testPlus(s0, delimiter='|', uescapes=True)
    print("vbar, with entities")
    testPlus(s0, delimiter='|', entities=True)
    print("vbar, with all of those")
    testPlus(s0, delimiter='|', xescapes=True, uescapes=True, entities=True)

    phead("Multi-char delim:")
    s0 = "lorem##ipsum##dolor##sit##amet"
    testPlus(s0, delimiter='##')

    phead("Quoting:")
    s0 = 'wee fish$ewe$"a mare"$egrets$"moo$e"'
    testPlus(s0, delimiter='$', quotechar='"')

    s0 = "wee fish$ewe$'a mare'$egrets$'moo$e'"
    testPlus(s0, delimiter='$', quotechar="'")

    s0 = "'wee fish'$ewe$‘a mare’$egrets$“moo$e”"
    testPlus(s0, delimiter='$', quotechar='“”')

    s0 = "'wee fish'$ewe$‘a mare’$egrets$“moo$e”"
    testPlus(s0, delimiter='$', quotechar='“”')

    #SINGLE DOUBLE ANGLE CURLY ALL
    # quotes inside quotes

    if (0):  # TODO: Check and fix
        phead("Doubling quotes")
        s0 = """'Lorem ipsum ''dolor'' sit amet','consectetur adipiscing elit','sed do
    eiusmod tempor incididunt ut labore et ''dolor''e magna aliqua','Ut enim ad minim
    veniam','quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
    commodo consequat','Duis aute irure ''dolor'' in reprehenderit in voluptate velit
    esse cillum ''dolor''e eu fugiat nulla pariatur','Excepteur sint occaecat
    cupidatat non ''proident''','''sunt'' in culpa qui officia deserunt mollit anim id
    est laborum'"""
        print("Test string: %s" % (dquote(s0)))
        toks = fsplit(s0, delimiter=",", quotechar="'", doublequote=True)
        for i0, tok0 in enumerate(toks):
            print("    %2d: /%s/" % (i0, dquote(tok0)))

    phead("minsplit, maxsplit:")
    s0 = "lorem##ipsum##dolor##sit##amet"
    testPlus(s0, delimiter='##', minsplit=99, strict=True)
    testPlus(s0, delimiter='##', maxsplit=3, strict=True)

    phead("autotype feature:")
    s0 = "hello,1,,3.14159,-6.022E+23,1.618+2j,NaN,-inf,+inf,world"
    print("Test string: %s" % (dquote(s0)))
    stuffs = fsplit(s0, delimiter=',', typeList='AUTO')
    for i0, stuff in enumerate(stuffs):
        print("    %d: %-16s %s" % (i0, dquote(stuff), type(stuff)))

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
        "hello &wo:rld;",
        "hello &#world;",
        "hello &#08FF;",
        "hello &#x00GG;",
        # unclosed quotes, swapped polarity, not at start of field,....
    ]
    for s0 in errTests:
        testMinus(s0, delimiter=',', strict=True,
                xescapes=True, uescapes=True, entities=True)

    if (not args.quiet):
        sys.stderr.write("\nDone.\n")
