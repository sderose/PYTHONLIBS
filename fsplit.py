#!/usr/bin/env python3
#
# fsplit.py: A better (I hope) str.split() or csv package.
# 2020-02-28: Written. Copyright by Steven J. DeRose.
#
#pylint: disable=W0603,W0511
#
import sys
import argparse
import codecs
import re
#from collections import namedtuple
from typing import Dict, Any, Union, IO, List, Callable, Final
from enum import Enum
import ast
import html
import datetime
import array
import unicodedata

import logging
from Datatypes import Datatypes

lg = logging.getLogger()
dt = Datatypes()

def info2(msg, *nargs):
    lg.log(logging.INFO-2, msg, *nargs)

__metadata__ = {
    "title"        : "fsplit",
    "description"  : "A better (I hope) str.split() or csv package.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2020-02-28",
    "modified"     : "2023-11-19",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

An enhanced `split()` function, and APIs using it that are modelled on
Python's `csv` library (see [https://docs.python.org/3/library/csv.html]).

=Usage=

==Usage from command line==

Use this to parse a file(s) and display a block for each record, containing
the record number, followed by a line for each field, with the name and value.
The values are formatted based on their apparent type
(bool, int (or oint or xint), float, complex, string).
The CSV dialect can be specified using options named like the API's options.
For example:

    fsplit.py --delim "\\t" --quotechar '"' myFile.csv

If `--visible` is set, control characters are converted to a readable form
(using Unicode "control pictures").

==Usage from the command line==

To parse a CSV-ish file and see a simple/readable display, just do:
    fsplit.py myFile.csv

Options can be added to specify alternate syntaxes (--delim, etc.),
the presence of a header (--header),
a header-like string (--ifields) for when there is no header record in the file(s),
etc.). For example:
    fsplit.py --header --delim "\t" --quotedouble myFile.csv

Instead of the pretty-rinted default display, you can convert
a file(s) from one CSV-ish format to another, by using additional
options (but (with "o" prefixed to their names, for "output"),
to specify the output syntax and fields:
    fsplit.py --header --delim "\t" --quotedouble --odelim ":" --oecapechar "\\" myFile.csv

There is also (in progress) a suite of command-line filters built on top.
See [Related Commands].

==Usage as an API==

This works essentially like {Python's built-in "csv" package. A basic example:
    import fsplit
    for recnum:int, fields:List in rdr.items():
        print("Record %d:" % (recnum))
        for fnum, fval in enumerate(fields):
            print("%s: %s" % (rdr.schema[fnum].fname, fvalue))

In this example, rdr.schema is constructed when the first record is read,
because of the 'header' argument.

Note that if the schema (however supplied, see below) specifies a datatype for
one or more fields, the values found in those fields are cast to that
type before they are returned from fspit ('ValueError' is raised if that fails).
If you don't want that behavior, just don't specify datatypes.

Instead of the list of syntax arguments (in this example 'delim', 'escapeChar',
'quotechar', and 'header'), a 'dialect' argument may be passed a Dialect or DialectX
object which was created with the desired syntax options.

A dialect object deals with syntax options such as quoting, escaping, space-stripping,
line-ends, etc. It can be created manually like:
    myDialect = DialectX("monty", delimiter="\t", escapeChar="\\",
        quotechar='"', header=True)
    rdr = fsplit.reader("myFile.csv", dialect=myDialect)
    ...

In addition, fsplit supports 'FieldSchema' objects, which describe
some simple semantics of the data such as the names and order of fields, their
datatypes, and so on. A FieldSchema can be set up in several ways:

* created from a real header line (by setting the 'header' option as shown above)

* created from a header-like string and passed in:
    fakeHead = "name|UPPER:str!,dob:datetime,age:int[0:150],zip"
    mySchema = FieldSchema(fakeHead)
    rdr = fsplit.reader("myFile.csv", dialect=myDialect, schema=mySchema):
    ...

* created from a list of individual header-like items (this lets you avoid
escaping in case delimiters occur in the header information):
    headItems = [ "name|UPPER:str!", "dob:datetime", "age:int[0:150]", "zip" ])
    mySchema = FieldSchema(headItems)

* created with just a list or string of field names (they remain untyped) and passed in
(these are just special cases of the prior two, that use no datatype, normalizations,
constraints, or defaults):
    mySchema = FieldSchema(fieldNames="name,dob,age,zip")
  or
    mySchema = FieldSchema(fieldNames=[ "name", "dob", "age", "zip" ])

* created manually and passed in (this supports some features that can't be
expressed in a regular header record, such as custom normalizer functions
and output format hints):
    mySchema = FieldSchema()
    mySchema.append("name", ftype=str, frequired=True, fnormalizer=str.upper)
    mySchema.append("dob", ftype=datetime, fnormalizer=myDateFunction)
    mySchema.append("age", ftype=int, fmin=0, fmax=150, fformat="%3d")
    mySchema.append("zip", ftype=int, fmin=0, fmax=99999, fformat="%5d")

* left implicit. In that case, after the first record is read but before its fields
are returned, a trivial schema is generated, with untyped fields named "Field_01",
"Field_02", etc.

Dialects and schemas have many more options.

===Classes===

The `fsplit` package includes these classes:

* DialectX -- very much like csv.Dialect, but with more items.
One DialectX is predefined, as `__RFC4180__`, with those settings (`header`
is set to False, since RFC 4180 makes it optional; this does mean that if
there is a header (and you don't set `header` or read the header record
manually), the header record is taken as data.

* DictReader -- like csv.DictReader

* DictWriter -- like csv.DictReader

* UnclosedQuote(Exception) -- When `DictReader` calls `fsplit()` to parse
a record, if the record is incomplete due to ending within a quoted literal,
this exception is raised. `DictReader` then reads and appends the next record,
and tries the parse again.

* FieldSchema(list) -- An ordered list of fields, which can be set up
manually or from a header or similar source. Each field is a FieldInfo instance.
Think of this as a CSV header on steroids.

* FieldInfo encapsulates properties of a specific field. Yu can construct them
directly, with the properties below as arguments (only "fname" is required),
and headers work by parsing each header entry and constructing FieldInfos:

** fname -- the field name, typically an identifier token
** ftype -- one of the known types, or at least its name
** fconstraint -- a field constraint as a string (see [Header Format] for
the type-dependent values that can be used)
** fdefault -- a default value (None may mean no default value, or that the
default value is None -- how would you tell?
** frequired -- if set, the field must always be non-empty in the data
** fformat -- a preferred output format, for example "%12.4f". Or a Callable
that takes the (possibly typed) field value and returns a string. A Callable
here is probably most useful to handle "special" values such as None, reserved
codes for things like "missing" or "not applicable", etc.
** fnormalizer -- a Callable which is the first thing applied to a field once
it is split out from the record (this is still after quote removal and unescaping).
The Callable should take and return strings. Several named normalizers can be
spedified in the header, by inserting them before the []-constraint (see section
[Header Format]).
** fnum -- the field number, counting automatically from 1 as FieldInfo are appended
to a FieldSchema.

* DatatypeHandler -- this supports many basic datatypes, which can be specified
for particular fields via `FieldSchema`. Parsed values can then be tested and
cast as appropriate. The class also has `autoType()`, which will cast a value
to the most specific type it fits (for example, "9" to int, but "9.1" to float).
You can set `boolCasterFunc` to function, to which `autoType()` will pass the
string value that was parsed. It should return True or False, or raise ValueError,
which `autoType()` will catch and go on to try other types.

This library has several features beyond those of the regular `csv`.

===A wider range of syntax options===

Most of the *nix fielded-data utilities have little or no support for
quoted fields or escaped characters. No two (afaict) support the same range of
delimiter conventions. The Python ''csv' library is stronger, but still lacks
syntax support such as:

* Multi-character delimiters (unlike some utilities)
* Multiple alternative quotechars (for example, single and double)
* Distinct open and close quotechars
* Unicode quote characters (curly, angle, etc.)
* Expanding special chars like
\\xFF (`xescapes`); \\uFFFF (`uescapes`); &#xFFFFF;, &bull;, etc. (`entities`)
* Ignoring repeated delimiters (like `sed` can) (see the `multidelimiter` option)
* (in progress) cycling deimiters (like `paste -d`)
* Quoted fields that can include newlines (`quotednewline`)
I strongly dislike this usage, but RFC 4180 and
some common spreadsheet programs write it, so supporting it
seems desirable. There is some support half-hidden in ''csv'' for this.
The `quotednewline` feature is experimental for now.

===Datatype-related features===

Header records here may include not just field names, but also datatypes,
value constraints, and default values (see section [Header format]).
With a sufficient header, fsplit will:
* replace empty fields with that field's default value (if any)
* raise ValueError for empty fields that are declared as required ("!" in the header)
* cast them from the raw strings read to the declared types
(raising ValueError in case of failure).
* test values against the field's constraints, such as min/max values, regexes, etc.
(raising ValueError in case of failure).

Instead of fancy headers, or in addition (for fields which do not declare a type),
'autotype' is available.


=Usage=

It's probably cleanest (and slightly faster) to define the set of
options you want as a `DialectX` (similar to `csv.Dialect`) and then just
pass it to `fsplit()` along with each record in turn:

    myDialectX = DialectX("bestCSVever",
        delimiter=",",
        doublequote=False,
        escapechar="\\\\",
        quotechar='"',
        xescapes=True)

    for rec in f.readlines():
        myFields = fsplit(rec, dialect=myDialectX)
        print("Record %d:\\n    " + join("\\n    ", myFields))

==Default CSV dialect==

The default dialect is the same as for Python `csv`. The shared properties are:
    delimiter:str = ','
    doublequote:bool = True
    escapechar:str = None (no escaping)
    lineterminator:str = '\r\n' (accepts \r and \n, too)
    quotechar:str = '"'
    quoting:enum = QUOTE_MINIMAL
    skipinitialspace:bool = False
    strict:bool: False

The extended properties are:
    comment:str = None
    encoding = "utf-8"
    entities:bool = False
    header:bool = False
    maxsplit:int = None
    minsplit:int = 0
    multidelimiter:bool = False
    autotype:bool = False
    uescapes:bool = False
    xescapes:bool = False
    quotednewline:bool = False

Note: the defaults are not all the same as defined by RFC RFC4180 (q.v.).
However, the RFC settings are available as a predefined DialectX, in __RFC4180__.

==Custom DialectX==

To construct a DialectX you can used individual option arguments like shown
above. Or, if you want to set them via command-line options, you can do this:

    parser = argparse.ArgumentParser(description=...)
    ...
    DialectX.addargs(parser)
    args = parser.parse_args()
    myDialectX = DialectX("bestCSVever", args)

Or you can pass format options directly to `fsplit()`:
    for rec in f.readlines():
        myFields = fsplit(rec, delimiter="\\t",
            doublequote=False, escapechar="\\\\", quotechar='"', xescapes=True)
        print("Record %d:\\n    " + join("\\n    ", myFields))

You can read and parse a line at a time as above (unless you data has newlines in
quoted fields!). Or you can operate at the file level, for example using

    DictReader(f, fieldNames=None, restkey=None, restval=None, dialect=None)

`f` must be an open file handler or other readable. Usage is just like
the corresponding class in `csv`:

    import fsplit
    with codecs.open("names.csv", encoding="utf-8") as csvfile:
        reader = fsplit.DictReader(csvfile)
        for row in reader:
            print(row["first_name"], row["last_name"])

Field names can be read from a header record by setting the `header` option
in a DialectX, and/or specified to the constructor.

* DictWriter(f, fieldNames, restval="", extrasaction="raise", dialect=None)

    import fsplit
    with codecs.open("names.csv", "w", encoding="utf-8") as csvfile:
        fieldNames = ["first_name", "last_name"]
        writer = csv.DictWriter(csvfile, fieldNames=fieldNames)
        writer.writeheader()
        writer.writerow({"first_name": "Baked", "last_name": "Beans"})
        writer.writerow({"first_name": "Lovely", "last_name": "Spam"})
        writer.writerow({"first_name": "Wonderful", "last_name": "Spam"})

* reader()

* writer()

==DialectX options==

A dialect has many options. Several match ones from Python `csv`, with
the same names and at least the same values. You can add them all to an argparse
instance like this:

    myParser = argparse.ArgumentParser()
    ...
    DialectX.addargs(myParser, prefix="", csvOnly=False)
    args = myParser.parse_args()
    dx = DialectX()
    dx.applyargs(myParser, prefix="")

("prefix" can be used to ensure that DialextX's options do not collide
with other options in the argument parser).

The options like those in `csv` include:

* ''delimiter'':str = "," -- The field separator character or string.
This can be a single string, or a list of several. If it's a list, the
delimiters are used in rotation.

* ''doublequote'':bool = True -- If set, allow putting `quotechar` inside
a quoted string, by doubling it. I'm not fond of this defaulting True,
but that's what Python `csv` does, so I stuck with it.

* ''escapechar'':str = None -- If set, this character can be put before
a quotechar, delimiter, or itself, to make that character literal rather
than special. The escapechar can also be used before any of
'f', 'n', 'r', 't', 'v', '\\\\', or '0' for the usual meanings.

* ''lineterminator'':str = "\\n" -- What string to write out to indicate
end-of-record. The three usual sequences are all accepted for input.

* ''quotechar'':str = '"' -- Sets what characters or character-pairs are recognized
as quotes (`setupQuoteMap()` handles all of this). Where Python `csv` and
many *nix utilities only accept a single delimiter characters, this also
accepts:

** ''None'' or '', no characters are treated as quotes.
** ''a single character'': that character is the only recognized quote,
and serves as both open and close.
** ''a 2-character string'': the first character is treated as open quote,
and the second as the corresponding close quote. Only the close quote is
subject to `doublequote`, though both are subject to `escapechar`.
With `MINIMAL` quoting, only the close quote gets escaped within output values.
** Various mnemonic names for Unicode open/close quote pairs,
as well as plain apostrophe and double quote. To see a list, use '--showQuotes'.
** ''BOTH'': single quote (apostrophe) and double quote are each
recognized as quotes, as is common in programming and markup languages.
A string enclosed in single quotes may freely contain double quotes,
and vice versa.
** ''ALL'': single and double quotes (as with "BOTH"),
as well as all the other here-named Unicode quotation marks.

* ''quoting'': Determines when output fields should be quoted. Specify one of
these constants, whose names and values are intended to be the same as in `csv`
(you can instead give the string name of one of them):

    fsplit.QUOTING.MINIMAL    = 0  # only quote if needed (the default)
    fsplit.QUOTING.ALL        = 1  # quote all fields.
    fsplit.QUOTING.NONNUMERIC = 2  # quote all non-numeric fields.
    fsplit.QUOTING.NONE       = 3  # never quote fields, but use escapechar

* ''skipinitialspace'':bool = False -- If set, records (not fields)
have any initial (Unicode) whitespace stripped before parsing.

* ''strict'':bool = False -- If set, problems raise `ValueError`
instead of being worked around or ignored.

===Additional options===

The following options are not available in Python's `csv` package:

* ''comment'':str = None -- If set and not '', lines starting with
this string are treated as comments rather than data. Leading space is NOT
allowed before the delimiter (this might be added).

* ''cycle'':bool = False -- If set, and there are multiple delimiters
specified, use those delimiters in alternation like 'paste -d'.
This is not yet supported, and is not expected to be happy with named
multi-delimiter sets such as BOTH and ALL.

* ''encoding'' = "utf-8" -- what encoding to use. This affects escaping.

* ''entities'':bool = False -- If set, character references are recognized
and replaced as in HTML. Decimal (&#8226;), hexadecimal (&#x2022;), and named
(&bull;) forms are all supported.
NOTE: These are converted via Python's `html.unescape()` method, which does not
raise an error for unknown entities such as `&foo;`.

* ''header'':bool = False -- If set, the first record of each input file is
expected to be a header, giving at least a named for each field.
Headers can be read manually instead, and parsed via parseHeaderStrToSchema().
Field names in the header are also allowed to have suffixes much like Python
type hints, to specify their datatypes, rudimentary constraints (see below), and/or
a default value ("!" to assert the field is required. Via the API, additional
functionality may be added, such as a map from particular string values to
constants (say, "NaN" or "-" to None).

* ''maxsplit'':int = 0 -- If positive, splitting a record stops after
this many splits have occurred (making this many + 1 tokens; 0 means unlimited).

* ''minsplit'':int = 0 -- If specified, an exception is raised if fewer than
this many splits are made.

* ''multidelimiter'':bool = False -- If set, multiple adjacent delimiters do
NOT result in empty tokens, but are treated the same as a single delimiter.
This would typically be done when the delimiter is just a space.
Empty fields can, however, be inserted by quoting them (because the delimiters
on each side are no longer "adjacent"). This option should probably not be
used in combination with a list of cycling deimiters.

* ''autotype'' = False -- If set, fields with no overriding type declared (via
a header record, '--ifields', or the API)
are examined and cast to the
most specific type they can (from the type supported in header declarations).
Booleans are not attempted (for more information see section [autoTyping]).

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

===Header format===

If the 'header' option is set, the first record is treated as a header.
It should give names for all the fields, separated by the same delimiter as
in the rest of the file. The names should typically be identifiers:
starting with a (Unicode) word-character (letter, syllable, or ideograph),
followed by those, digits, and/or underscores.

The header can be just a list of field names, as supported by many CSV-ish
parsers. Or, you can optionally provide more information for some or all
fields. The syntax and meanings are similar to Python type hints:

    name:type=default,name2:type2,name3=default3,...

The types are shown in these examples:
    obsolete:bool       "1" or "0" (see below to use other values like T or F)
    age:int             decimal integer
    cookie:xint         hexadecimal integer
    perm:oint           octal integer
    quant:anyint        accepts octal, decimal, or hex
    balance:float       floating-point number
    root:complex        python notation
    lastName:str        string (this doesn't do much).
    dob:datetime        datetime (ISO 8601)

Other types will likely be added.

Defaults can be given after an "=", or "!" may be used to indicate
that a non-empty value is ''required''
(default values can contain quotes or delimiters only if escaped the same way as
other data in the file):
    obsolete:bool=0
    payGrade:float!

A ''normalizer'' name can be specified immediately after the type name,
separated by "|". Underneath, a normalizer is a function that takes the
field value (after unescaping and unquoting if applicable), and returns a
string (or raises ValueError on failure). They can be used for
case-folding, detecting special "reserved" values (such as "-" for Not
Applicable, which one might map to None), etc.

Custom normalizers can be set via the 'fnormalizer' parameter when
constructing a FieldIngo object in the API, but not via the header.
The following named normalizers are predefined, and can be given in the header::
    UPPER -- force the value to uppercase
    LOWER -- force the value to lowercase
    NFKD, NFKC, NFC, NFD -- apply that Unicode normalization form
    XSP -- apply XML space normalization (just space, TAB, CR, LF)
    USP -- Unicode space normalization (all \\s)
    TF -- fields beginning with [Tt] go to 1, [Ff] go to 0 (if the field is declared
to be type bool, those will then be recognized and cast to True and False.
    ASCII -- non-ASCII characters to \\x, \\u, \\x{} escapes

A value ''constraint'' can also be included in [] immediately after the datatype
and normalizer name. The forms of constraints are type-specific:

* bool: Not currently applicable. A possible
future addition is to give the actual strings to be used for False and True,
since practice for these varies so much.
* int: the constraint is 2 (possibly-signed) decimal integers, separated
by a colon, that are the minimum and maximum values allowed. These values
are inclusive bounds.
* float: as for int, but the minimum and maximum values can be floats
(as always, be careful about roundoff errors). These values
are inclusive bounds.
* complex: Not currently applicable.
* str: the constraint is a (Python-style) regular expression that each value
must match in its entirety. Such constraint commonly require escaping.
These constraints can be used to implement other things, such as enums:
    compass:str[N|E|W|S|NE|NW|SE|SW]=N
    province:str[NL|PE|NS|NB|QC|ON|MB|SK|AB|BC|YT|NT|NU]!
  or length limits:
    middleInitial:str[.{0,1}]

''Note'': regex constraints regard case.
However, Python allows specifying flags within a regex.

When a ''type'' is specified, raw field values are cast to that type
for return (for example, by reader() and DictReader()).
When a field is empty and a default value
was set, the default value is cast to the specified type and returned.
Fields with no type hint in the header default to type 'str', and no default
(which amounts to "").

==What if there's no header record?==

For files lacking a header record, you can do several things:

* do nothing (and don't set '--header') -- in that case, field names like
"Field_01" are assigned as needed.
* add a header record  to your data file(s).
* use the '--ifields' option on the command line, which takes exactly the
same syntax.
* provide the information via the API. To achieve this, construct
a 'FieldSchema' object and use 'append()' to define any number of fields (these
are represented by 'FieldInfo' objects, which can be constructed given only a name,
or with argument or type, constraint, required, and so on).
FieldInfo objects offer extra features such
as mapping reserved strings (say, "True", "False", "N/A", etc. to values.

A field for which no type is set is returned as a literal stringn unless
'autotype' is turned on (see next section).

===autoTyping===

If `autotype` is set on the DialextX, then any field which does not have an explicit
type set (via header, options, or API as described above), is passed to a function which
tries to cast it to an appropriate type.

This has potential problems. Some data uses "1" and "0" for booleans, which could also be
ints (or perhaps floats). Other data might use reserved words such as "True", "T", or "#T",
which could of course be strings. Any int could also be a float.
Anything at all could be a string.
Because of this, autotyping never decides something is a boolean, unless

Leading and trailing whitespace is stripped before testing types.
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
(all case-sensitive) are recognized as floats (otherwise they are strings).

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

My `csv2xml.py` -- Obsolete precursor to `fsplit.py`, but has a number of
possibly useful export formats.

See "also my related scripts such as `Record.py`, `Homogeneous.py`,
`Datatypes.py` for some other features that may be added.

There is also (in progress) a suite of command-line filters built on top.
They mimic the *nix commands that support fields, but aim to unify the "CSV"-ish
support across filters (the usual ones differ in what they can and
cannot parse. Most don't support quoting, escaping, or Unicode.
See [http://github.com/sderose/CSV] and [http://github.com/sderose/XML/CONVERT].

When finished, the suite should include version of:
awk, colrm, column, cut , join, paste, sort, tab2space, uniq, xargs.
Perhaps also: colrm, expand, lam, look, sed, unexpand, fold, and a variant
of 'less' with integrated CSV pretty-printing.


=Known bugs and Limitations=

Smoke tests for incomplete escape sequences are not working right.

fieldNames passed to DictReader, or from --ifields,
should probably be allowed to override any
read from a header record. But currently they're compared and an exception
is raised if they don't match. TODO: Check if still true.

Multi-char delimiters test is failing.
Not sure whether you can (or should be able to) escape in mid-delimiter.

'--convert' does not copy comment lines, even if an output dialect command
marker is specified. How best to return comments during parsing?

For `bool` the default test is whether the field's value begins with [tT1]
or [fF0]. Other initial characters raise ValueError. Change this via normaliztion.
There is also a `boolCaster()` function for helping with the variety of ways
booleans are expressed, but it's not connected.

What's the right rule for a quote not immediately following a delimiter?
As in
    1, "two", 3, 4"five"5, 6


=To do=

* Data subtypes:
** Hex and maybe octal fields; maybe uudecode/base64; currency, %?
** Finish normalizer support
** Improve datetimes. Add subtypes for date, time, ymdhmsz.
Way to distinguish only-precise-to-the-h0our from on-the-hour.
Support timedelta. Add normalizers for US and EU dates, epochtime.

* Add a way to get at the last raw record (since reader() parses it,
and the logical/physical record numbers.

* Lose remaining refs to args from inside classes.

* Should csv 'skipinitialspace' be overridable per-field, and should
there also be trailingspace? And maybe something more for Unicode spaces
and for hard-space per se?

* Add predefined dialects: RC4081, Excel, and any that Python `csv` provides.
Also eponymous ones for each relevant *nix command?

* Per RC4081 complain about rec-final delimiter if not quoted.

* Make sure it can just take a csv.Dialect for the DialectX arguments.

* More flexible delimiters:
    ** regex delimiters?
    ** the "whitespace to nonspace transition" approach (like awk, column, and sort)
    ** repeatable delimiter (that don't generate empty fields)
    ** Finish support for cycling delimiters (like 'paste -d').

* Some kind of hysteresis for autotyping? Like, if this field has always been int
and we see "", make it 0; if always float and we see 12, make it 12.0.

* Option to create NamedTuple or tuple instead of list or dict?

* Support for a wider range of formats (probably via separate
packages or subclasses with much the same API), such as:
    ** HTML and XML tables
    ** MediaWiki and MarkDown tables
    ** XSV
    ** JSON cases
    ** s-expressions
    ** SQL INSERT statements
    ** Tables extracted straight from a SQL API
    ** Fixed column widths, maybe via scanf?
    ** Maybe CONLL (see Stanford Corenlp output options)?

This is TSV, but with a blank line between groups of records (each of which
amounts to a sentence). Could return one extra field with a generated group number;
or throw or return something at the blank lines (maybe similar for comments?).

* Provide a way to change the set of backslash codes, such as \\b for BEL, etc.?


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

* 2021-07-12: Start supporting delimiter dycling like `paste -d`.

* 2023-08-22: Improve help. Update for current Python.

* 2023-09-20ff: Build in __RFC4180__. Clean up support for \\u \\x, add
\\U and \\x{}. Add missing options to addargs(). Add 'header' option and
support for type-hint style header records. Make reader() smart about
unclosed quotes.

* 2023-10-31ff: Refactor. Promote FieldInfo from namedtuple to class.
Add parseHeaderStrToSchema() and handling of type hints and defaults. Start open/close
quote support. Add cleanField() to do strip, unquote, unescape, entities,
normalization, etc. Start main beyond basic smoke-test.
Add --convert vs. prettyprinting. Add UberType info. Reorg quote pairs and
option defaulting. Add --showQuotes and --showDialectX. Refactor
reader() and writer() to be like csv ones (generator classes).
Ditch 'typelist'. Add DictWriterXSV, SAXReader.


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
class QUOTING(Enum):
    MINIMAL       = 0  # only quote if needed.
    ALL           = 1  # quote all fields.
    NONNUMERIC    = 2  # quote all non-numeric fields.
    NONE          = 3  # never quote fields, but use escapechar if defined

class DELIM_PATTERN(Enum):  # TODO Not yet?
    """Try to support all the delimiter conventions out there (man pages for
    these often do not define "space"; perhaps that should be settable here?).
        csv and tsv, etc.
        Python split and re.split
        paste -d [cycle]
        join -t [char]
        sort -t [char]  -- BUT if not set, "a sequence of blank space characters"
        awk  -- whitespace, or the current FS value
        colrm  start [stop]]  -- column numbers only
        column -t -s [cycle]  -- ???
        lam
        uniq -f [n]  -- skip [n] fields, always meaning \\S+ (nonspace sep. by space)
    """
    CHAR          = 1  # The typical single-char, like TAB or comma
    STR           = 2  # A multi-char delimiter
    CYCLE         = 3  # Single chars used cyclically (cf. *nix `paste -d`)
    SPACES        = 4  # Space / non-space change, sort of like \b

#POINTING_CHAR = "\u261e"  # Pointing finger
POINTING_CHAR = "\u23E9"  # Double arrow button

class DialectX:
    """Mainly a bundle of settings.
    """
    __OptionTypes__ = {
        "delimiter":        Union[str, List],
        "doublequote":      bool,
        "escapechar":       str,
        "lineterminator":   str,
        "quotechar":        str,
        "quoting":          QUOTING,
        "skipinitialspace": bool,
        "strict":           bool,

        # fsplit only:
        "comment":          str,
        "cycle":            bool,
        "encoding":         str,
        "entities":         bool,
        "header":           bool,
        "maxsplit":         int,
        "minsplit":         int,
        "multidelimiter":   bool,  # Cf *nix *paste*
        "autotype":         bool,
        "uescapes":         bool,
        "xescapes":         bool,
        "quotednewline":    bool,
    }

    def __init__(self, dialectName:str=None, dialect:'DialectX'=None,
        argNS:argparse.Namespace=None, **kwargs):
        self.dialectName = dialectName

        self.setDefaultOptions()
        if (dialect):
            for oname in self.__OptionTypes__.keys():
                setattr(self, oname, getattr(dialect, oname))

        #info2("Default options:\n" + self.tostring())
        if (argNS): self.applyargs(argNS, prefix="")
        self.applykwOptions(kwargs)
        self.problemChars = self.getProblemChars()
        self.checkOptions(strict=self.strict)

    def setDefaultOptions(self):
        # name                 = default  # type
        self.delimiter         = ","    # str
        self.doublequote       = True   # bool
        self.escapechar        = None   # str
        self.lineterminator    = "\r\n" # str
        self.quotechar         = '"'    # str
        self.quoting           = QUOTING.MINIMAL
        self.skipinitialspace  = False  # bool
        self.strict            = False  # bool

        # fsplit only:
        self.comment           = None   # str
        self.cycle             = False  # bool
        self.encoding          = "utf-8"# str
        self.entities          = False  # bool
        self.header            = False  # bool
        self.maxsplit          = 0      # int
        self.minsplit          = 0      # int
        self.multidelimiter    = False  # bool
        self.autotype          = False  # bool
        self.uescapes          = False  # bool
        self.xescapes          = False  # bool
        self.quotednewline     = False  # bool

        self.problemChars = self.getProblemChars()

        self.checkDialect()

    def applykwOptions(self, kwargs):
        for k, v in kwargs.items():
            if (k not in self.__OptionTypes__):
                raise ValueError("Unrecognized option name '%s'." % (k))
            if (k == "quoting"):
                try:
                    if (not isinstance(v, QUOTING)): v = QUOTING[v]
                except ValueError as e:
                    raise ValueError("Unrecognized value '%s' for quoting." % (v)) from e
            typ = self.__OptionTypes__[k]
            if (v is None or isinstance(v, typ)):
                setattr(self, k, v)
            else:
                raise ValueError("Option '%s' has bad value '%s', needs %s."
                    % (k, v, typ))

    def checkOptions(self, strict:bool=False) -> None:
        errs = []
        if (not self.delimiter or not isinstance(self.delimiter, str)):
            errs.append("Delimiter unset or wrong type.")
            self.delimiter = ","
        if (self.escapechar and len(self.escapechar) > 1):
            errs.append("escapechar too long ('%s')." % (self.escapechar))
        if (isinstance(self.quoting, str)):
            self.quoting = QUOTING[self.quoting]
        if (not isinstance(self.quoting, type(QUOTING.MINIMAL))):
            errs.append("Value '%s' not valid for quoting (it's a %s)."
                % (self.quoting, type(self.quoting)))
        if (self.quotechar and len(self.quotechar) > 2):
            errs.append("Quotechar too long ('%s')." % (self.quotechar))
        if (self.maxsplit and self.minsplit and self.maxsplit < self.minsplit):
            errs.append("maxsplit (%d) < minsplit (%d)." %
                (self.maxsplit or 0, self.minsplit or 0))
        #
        if (self.doublequote and self.escapechar):
            errs.append("Cannot combine doublequote and escapechar")  # TODO ???

        if (errs):
            if (strict):
                raise ValueError("\n".join(errs))
            else:
                lg.error("\n".join(errs))

    @staticmethod
    def addargs(parser, prefix: str="", csvOnly: bool=False):
        """Add argparse arguments for our options.
        @param prefix: If specified, add this at the start of all the names,
        to prevent name conflicts.
        @param csvOnly: If set, don't include arguments specific to fsplit.
        """
        pre = "--" + prefix

        # Options like Python "csv" package:
        parser.add_argument(
            pre+"delimiter", type=str, default=",", metavar="C",
            help="Field separators, one or more characters. Repeatable, in which"+
            " case all are allowed. Default: comma.")
        parser.add_argument(
            pre+"doublequote", pre+"dquote", pre+"quotedouble", action="store_true",
            help="A quote may be doubled to become literal (rather than escaped).")
        parser.add_argument(
            pre+"escapechar", type=str, metavar="C",
            help="This can be used to escape a quote, delimiter, or itself.")
        parser.add_argument(
            pre+"lineterminator", type=str, default="\n", metavar="C",
            help=".")
        parser.add_argument(
            pre+"quotechar", type=str, default='"', metavar="C",
            help="What character to use to quote fields that need it.")
        parser.add_argument(
            pre+"quoting", type=str, default="MINIMAL",
            choices=[ "ALL", "MINIMAL", "NONNUMERIC", "NONE"],
            help="When should fields be quoted?.")
        parser.add_argument(
            pre+"skipinitialspace", action="store_true",
            help=".")
        parser.add_argument(
            pre+"strict", action="store_true",
            help=".")

        if (csvOnly): return

        # Extended options
        parser.add_argument(
            pre+"comment", type=str, default=None, metavar="S",
            help="Treat records starting with this string as comments, not data.")
        parser.add_argument(
            pre+"cycle", action="store_true",
            help="Cycle' through multiple delimiters, like `paste -d` (not yet).")
        parser.add_argument(
            pre+"entities", action="store_true",
            help="Recognize and expand HTML/XML entity references?")
        parser.add_argument(
            pre+"header", action="store_true",
            help="Is the first record a header?")
        parser.add_argument(
            pre+"maxsplit", type=int, default=0, metavar="N",
            help="Do at most this many splits, resulting in this+1 fields.")
        parser.add_argument(
            pre+"minsplit", type=int, default=None, metavar="N",
            help="Do at least this many splits, or report an error.")
        parser.add_argument(
            pre+"multidelimiter", action="store_true",
            help="Treat multiple adjacent delimiters (e.g. space), as just one.")
        parser.add_argument(
            pre+"quotednewline", action="store_true",
            help="Allow newlines as data within quoted fields.")
        parser.add_argument(
            pre+"uescapes", action="store_true",
            help="Recognize \\uFFFF-style special characters.")
        parser.add_argument(
            pre+"xescapes", action="store_true",
            help="Recognize \\xwFF-style special characters.")

        return

    def applyargs(self, theArgs:argparse.Namespace, prefix:str="") -> None:
        """Call this to move the arguments (typically added by
        addargs), to the current instance.
        """
        for k in DialectX.__OptionTypes__:
            if (k in theArgs.__dict__ and theArgs.__dict__[k] is not None):
                self.__dict__[k] = theArgs.__dict__[prefix+k]

    @staticmethod
    def makeVis(mat) -> str:
        n = ord(mat.group(1))
        if (n < 32): return chr(0x2400+n)
        if (n > 127 and n < 160): return "\\x%02x" % (n)
        return "\\u%04x" % (n)

    def tostring(self, display:bool=False) -> str:
        """Readable option settings, as attribute-list or use-readable.
        Useful to save or print to send with your data.
        """
        buf = ""
        for k in sorted(self.__OptionTypes__.keys()):
            val = str(getattr(self, k))  # TODO: Use schema.format value?
            if (display):
                buf += "%-20s %s\n" % (k, re.sub(r"([\x00-\x1F])", self.makeVis, val))
            else:
                buf += " %s\"%s\"" % (k, self.serializeValue(val))
        return buf

    def getProblemChars(self) -> str:
        """Gather up all the characters we'll need to consider for escaping.
        This doesn't consider the mess of escaping multi-char delimiters, or
        escaping cycling delimiters only when in effect (that seems to only be
        relevant for *nix `paste`, which doesn't handle escaping and quoting).
        """
        return (
            (self.delimiter or "") +
            (self.escapechar or "") +
            (self.lineterminator or "") +
            (self.quotechar or "") +
            (self.comment or "")
        )

    def serializeValue(self, v:Any, asciiOnly:bool=False) -> str:
        """Escape/quote the value as needed to be a legit field in the
        given dialect.
        NOTE: Mapping of None, Inf, NaN, True, etc.; non-decimal numbers;
        and specific format defs in the fschema, must be done first.
        Factors:
            delimiter, multidelimiter, cycle
            quotechar, doublequote, quotednewline, lineterminator
            escapechar, uescapes, xescapes, entities
            encoding.
        TODO: What about booleans, etc.? TODO
        """
        if (v is None): v = ""
        else: s = str(v)
        if (asciiOnly):
            buf = re.sub(r"([^!-~])", self.escapeOneChar, s, flags=re.U)
        else:
            buf = re.sub(
                r"[" + self.problemChars + "]",
                lambda m: self.escapeOneChar(m),
                s,
                flags=re.U
            )
        return buf

    # TODO Sync with regular 'csv' package
    def escapeOneChar(self, c:Union[str,re.Match]) -> str:
        """Can be used on a raw character, or an re.Match object with the
        desired character in the 1st capture. Always recodes the character
        somehow (or fails), so only call it when needed (see getProblemChars()).
        """
        if (isinstance(c, re.Match)):
            c = c.group(1)
        assert c in self.problemChars

        if (c == self.escapechar):
            return c+c
        if (c == self.quotechar):
            if (self.quoting): return c  # Caller must do the quoting!
            if (self.doublequote): return c+c
            elif (self.entities): return self.entify(c)
            elif (self.escapechar): return self.escapechar + c
            else: return self.hexify(c)
        if (self.entities and c in "&<"):  # TODO: Ewww, quote for in attrs.
            # ">" doesn't normally need quoting (see "]]>")
            return self.entify(c)

    def entify(self, c:str):
        """Many options here -- like an order of preference among
        named/hex/decimal XML character refs.
        """
        n = ord(c)
        if (n in html.entities.codepoint2name):
            return "&%s;" % (html.entities.codepoint2name[n])
        if (n > 0xFF): return "&#X%04x;" % (n)
        return "&#X%02x;" % (n)

    def hexify(self, c:str):
        """Many options here -- like an order of preference among
        \\x \\u \\U \\x{}; octal escapes; use of UTF-8; etc.
        """
        n = ord(c)
        if (n <= 0xFF):
            return "\\x%02x" % (n)
        assert self.uescapes
        if (n <= 0xFFFF):
            return "\\u%04x" % (n)
        return "\\U%08x" % (n)

    char2escape = {
        "\a"   : "\\a",  # bell
        #"\b"   : "\\b",  # backspace
        #"\e"   : "\\e",  # escape
        "\f"   : "\\f",  # form feed
        "\n"   : "\\n",  # line feed
        "\r"   : "\\r",  # carriage return
        "\t"   : "\\t",  # tab
        #"\v"  : "\\v",  # vertical tab (U+0B)
        "\\"   : "\\\\", # backslash
        }
    def escapeSpecial(self, c):
        if (c in self.char2escape): return self.char2escape[c]

    def checkDialect(self):
        """Check for contradictions in the Dialect options.
        TODO: Remove redundancies with checkOptons().
        """
        for oname in self.__OptionTypes__.keys():
            _val = getattr(self, oname)
        dlm = self.delimiter or ""
        esc = self.escapechar or ""
        quo = self.quotechar or ""
        lin = self.lineterminator or ""
        assert dlm
        assert dlm not in quo
        assert dlm not in lin
        assert dlm not in esc
        if (esc):
            assert esc not in quo
            assert esc not in lin
        if (quo):
            assert quo not in lin
        if (self.doublequote or self.quotednewline):
            assert quo
        if (self.minsplit and self.maxsplit):
            assert 0 <= self.minsplit <= self.maxsplit
        assert self.quoting in list(QUOTING)
        assert self.problemChars == self.getProblemChars()

        # encoding

__RFC4180__ = DialectX(
    "__RFC4180__",
    delimiter            = ",",    # Field separator(s)
    doublequote          = True,    # TODO Support ""
    escapechar           = None,    # Backslashing?
    lineterminator       = "\n",    # What's the line-break?
    quotechar            = '"',     # What's the quote mark?
    quoting              = QUOTING.NONNUMERIC,  # What to quote
    skipinitialspace     = False,   # Strip leading spaces
    strict               = False,

    header               = False,   # Is there a header record?
    comment              = None,    # Marker for comment lines
    entities             = False,
    maxsplit             = None,    # Limit to this many fields
    minsplit             = None,    # Scream if < this many fields
    multidelimiter       = False,   # Ignore repeated delimiters?
    autotype             = False,   # Attempt automatic datatypes
    uescapes             = False,   # Interpret \uFFFF
    xescapes             = False,   # Interpret \xFF
    quotednewline        = False    # Allow multiline quoted values
)

class ISO8601:
    """
    See also (non-builtin) packages 'g' and 'dateutil'.
    TODO Decide about optional parts
    """
    dateExpr = r"\d\d\d\d/[01]\d/[0123]\d]"
    zoneExpr = r"([-+]?\d\d(:[0-5]\d)?)?"
    timeExpr = r"[012]\d(:[0-5]\d(:[0-5]\d(\.\d*)?)?)?" + zoneExpr
    datetimeExpr = "%s(T%s)?" % (dateExpr, timeExpr)

    def __init__(self, s:str):
        #datetime.strptime(date_string, format)
        mat = re.match(self.datetimeExpr, s)
        if (not mat): raise ValueError
        # Maybe construct a regular datetime object.


###############################################################################
# Normalizers
#
def TFNorm(s:str) -> str:
    if (s == ""): raise ValueError
    if (s[1] in "tT1"): return "1"
    if (s[1] in "fF0"): return "0"
    raise ValueError

def ASCIINorm(mat) -> str:
    o = ord(mat.group(1))
    if (0x0020 <= o <= 0x007F): return chr(o)
    if (o <= 0xFF): return "\\x%02x" % (o)
    if (o <= 0xFFFF): return "\\x%04x" % (o)
    return "\\x{%x}" % (o)

# These normalizers are applied by handleRecord().
NamedNormalizers = {
    "UPPER":    str.upper,
    "LOWER":    str.lower,
    "NFKC":     lambda s: unicodedata.normalize("NFKC", s),
    "NFKD":     lambda s: unicodedata.normalize("NFKD", s),
    "NFC":      lambda s: unicodedata.normalize("NFC", s),
    "NFD":      lambda s: unicodedata.normalize("NFD", s),
    "XSP":      lambda s: re.sub(r"[ \t\r\n]+", " ", s),
    "USP":      lambda s: re.sub(r"\s+", " ", s),
    "TF":       TFNorm,  # For booleans
    "ASCII":    lambda s: re.sub(r"([^ -~])", ASCIINorm, s),
}


###############################################################################
#
class DictReader:
    """Modelled after Python "csv".
    """
    def __init__(self,
        f:IO,                    # file handle, File object, etc.
        fieldNames=None,         # iterable of names (None->use header rec)
        restkey: List=None,      # store any extras as list under this key
        restval: Any=None,       # default any missing fields to this value
        dialect: DialectX=None,
        schema: 'FieldSchema'=None,
        # *args,  # ???
        **kwargs
        ):
        self.f = f
        self.fieldNames = fieldNames  # If none, assume header
        self.restkey = restkey        # Field name for leftovers
        self.restval = restval        # Values for missing fields
        if (dialect): self.dialect = dialect
        else: self.dialect = DialectX(**kwargs)
        if (schema): self.schema = schema
        elif (fieldNames): self.schema = FieldSchema(fieldNames)
        else: self.schema = None      # Set up during first read

    def __iter__(self) -> List:
        """Read records into a dict of fields by name.
        Quoted fields that span lines are still experimental.
        """
        rdr = reader(self.f, dialect=self.dialect, schema=self.schema)
        for fields in rdr:
            fieldDict = {}
            for fNum, fd in fields:
                if (fNum < len(self.fieldNames)):
                    fieldDict[self.fieldNames[fNum]] = fd
                elif (self.restkey):
                    if (self.restkey not in fieldDict): fieldDict[self.restkey] = str(fd)
                    else: fieldDict[self.restkey] += str(fd)
            if (len(self.fieldNames) > len(fields) and self.restval is not None):
                # TODO: Apply schema defaults if available
                for i in range(len(fields), len(self.fieldNames)):
                    fieldDict[self.fieldNames[i]] = self.restval
            yield fieldDict
        return None  # EOF

    # What's a legit field name to use?
    dftNameExpr:Final = r"^\w([-.$\w ]*)$"

    from pydoc import locate  # see https://stackoverflow.com/questions/11775460/

    def parseHeaderStrToSchema(self, rec:str, dialect:DialectX,
        nameExpr:str=dftNameExpr) -> 'FieldSchema':
        """Parse a header record.
        It should use the established delimiter and quoting conventions, and
        all the names should match the `nameExpr` regex provided/defaulted,
        """
        schema = FieldSchema()
        for fnum, hfield in enumerate(fsplit(rec, dialect)):
            fi = self.parseOneHeaderItem(hfield, nameExpr, fnum)
            schema.append(fi)

        if (False and self.fieldNames and self.fieldNames != schema.getFieldNames()):
            raise ValueError("Header does not match expected fieldNames:\n    %s\n    %s" %
                (str(self.fieldNames), str(self.fieldNames)))
        return schema

    fnameExpr = r"(%s)"                       # 1
    fnormExpr = r"(\+(\w+))?"                 # 2, 3
    fconsExpr = r"(\[[^\]]*\])?"              # (5)
    ftypeExpr = r"(:\w+%s)?" % (fconsExpr)    # 4
    fdfltExpr = r"(=\w+)?"                    # 6

    # TODO: Switch to named captures?
    #fnameExpr = r"(?P<name>%s)"
    #fnormExpr = r"(?P<>\+(?P<norm>\w+))?"
    #fconsExpr = r"(?P<constr>\[[^\]]*\])?"
    #ftypeExpr = r"(?P<typ>:\w+%s)?" % (fconsExpr)
    #fdfltExpr = r"(?P<dft>=\w+)?"

    itemExpr:Final = fnameExpr + fnormExpr + ftypeExpr + fdfltExpr + r"$"

    def parseOneHeaderItem(self, hfield:str, nameExpr:str, fnum:int) -> 'FieldInfo':
        """After the name, a header item may have a a type-hint suffix and/or
        value, much like Python parameter definitions:
            name=99
            name:int
            name:int=99
            name:int[nneg]=99
        instead of "=" plus a value, "!" may be used to specify that a non-empty
        value is always required:
            name:int!
        Not all Python types can be used -- just those provided in 'KnownTypes'.

        TODO: Add named normalizer(s?):
            name+UPPER:str[]
        """
        hfield = hfield.strip()

        if (hfield[0] in "'\""):
            hfield.strip(hfield[0])
        if hfield.endswith("!"):
            freqd = True
            hfield = hfield[0:-1]
        else:
            freqd = False

        mat = re.match(self.itemExpr % (nameExpr), hfield)
        if (not mat):
            raise ValueError("Cannot parse header item %d: <<<%s>>>" % (fnum, hfield))
        else:
            fname = mat.groups(1) or ""
            fnorm = mat.groups(3) or ""
            ftype = mat.groups(4) or ""
            fcons = mat.groups(5) or ""
            fdflt = mat.groups(6) or ""
            lg.info("FInfo fname %s, fnorm %s, ftype %s, fcons %s, fdflt %s, freqd %s.",
                fname, fnorm, ftype, fcons, fdflt, freqd)

            if (fcons):
                fcons = fcons.upper()
                if (fcons not in NamedNormalizers):
                    if (args.strict):
                        raise ValueError("Could not locate normalizer '%s'." % (fcons))
                    ftype = ""

            if (ftype):
                if (fcons):
                    ftype = ftype[0:-len(fcons)]
                if (ftype not in FieldInfo.KnownTypes):
                    if (args.strict):
                        raise ValueError("Could not locate type named '%s'." % (ftype))
                    ftype = str

            if (fdflt):
                pass
                # TODO: Check value for castability to type/constraint

        finfo = FieldInfo(
            fname, ftype=ftype, fconstraint=fcons, fdefault=fdflt,
            frequired=freqd, fnormalizer=fnorm, fnum=fnum)
        return finfo

###############################################################################
# Thrown when parsing a line and it ends mid-quote, iff the dialect
# says that's ok. Caller can catch it, append next line, and call again.
#
class UnclosedQuote(Exception):
    pass


###############################################################################
#
predefinedDialects = {}

def unclosedQuote(s:str, quotechar:str='"') -> bool:
    """This does not account for backslashing!
    """
    assert quotechar not in "]-"
    expr = r"[^%s]+" % (quotechar)
    justQuotes = re.sub(expr, "", s)
    return len(justQuotes) % 2

def cleanField(s:str, dialect:DialectX) -> str:
    """Remove lead/trail spaces, quotes. Unescape content.

    This does *not* do any FieldInfo-specific operations such as
    normalization, case-folding, casting, special values like Inf/Nan, or defaulting.
    See isValueOk(), etc. for that kind of stuff...
    """
    s = s.rstrip()
    if dialect.skipinitialspace: s = s.lstrip()

    if (not s): return s

    if (s[0]==dialect.quotechar):
        if (len(s)==1):
            lg.error("Field has only an open quote.")
            s = ""
        elif (s[-1]==dialect.quotechar):
            s = s[1:-1]

    if (dialect.doublequote and dialect.quotechar):
        # TODO: Ewww. Interaction with backslash escaping?
        s = s.replace(dialect.quotechar+ dialect.quotechar, dialect.quotechar)

    if (dialect.escapechar and dialect.escapechar in s):
        assert dialect.escapechar == "\\", "Only backslash yet, as escapechar (not '%s')." % (
            dialect.escapechar)
        s = ast.literal_eval(s)
        # TODO Or: s = s.decode("string_escape")

    if (dialect.entities):
        s = html.unescape(s)

    return s


###############################################################################
#
class reader:
    """A generator object that can read logical CSV records even with quoted
    newlines, and returns a lost of each record's parsed raw fields.
    Keeps track of physical and logical record numbers.
    """
    def __init__(
        self, csvfile:IO,
        dialect:DialectX=None,
        schema:'FieldSchema'=None,
        **formatParams
        ):
        """Construct and return an fsplit-based generator object.
        """
        self.csvfile = csvfile
        if (dialect): self.dialect = dialect
        else: self.dialect = DialectX(**formatParams)
        self.schema = schema

        self.fieldNames = None

        self.line_num   = 0           # physical
        self.rec_num    = 0           # logical
        self.lrec       = ""          # last raw logical record

    def __iter__(self):
        """Read a logical record (possibly >1 physical record), and parse it
        into raw fields.
        Python's CSV doesn't treat this as a class (unlike DictReader), so we
        do the same. The main thing beyond readline() is that it handles quoted
        newlines (but it does so only by counting quotes, so doesn't play well
        with escaped quotes).
        """
        self.lrec = ""
        nPhysical = 0
        for rec in self.csvfile.readlines():
            nPhysical += 1

            # TODO Are comments allowed as physical lines inside logical recs?
            if (self.dialect.comment and
                rec.startswith(self.dialect.comment)): continue

            self.lrec += rec
            if (not unclosedQuote(rec, quotechar=self.dialect.quotechar)):
                try:
                    fields = fsplit(self.lrec, self.dialect)
                except UnclosedQuote as e:
                    lg.info("Continued rec %d (%d):\n    %s", self.rec_num, nPhysical, e)
                    continue  ### Go around for continuation line

            self.rec_num += 1
            if (nPhysical > 1):
                info2("Logical record included %d physical records.", nPhysical)

            # If this was the header, handle it and go around again for data.
            if (self.rec_num==1):
                if (self.dialect.header):
                    lg.info("read header logical rec as: <<<%s>>>", self.lrec)
                    self.schema = ensureSchema(
                        self.schema, firstRec=self.lrec,
                        dialect=self.dialect, fsArg=args.ifields)
                    self.fieldNames = self.schema.getFieldNames()
                    continue  # Go around for first data record
                else:
                    self.schema = ensureSchema(
                        None, firstRec=self.lrec,
                        dialect=self.dialect, fsArg=args.ifields)
                    self.fieldNames = self.schema.getFieldNames()

            # Got the fields, so bump stats and yield
            self.rec_num += 1
            yield fields
            self.lrec = ""
            nPhysical = 0
        return None


###############################################################################
#
class DictWriter:
    """Like "writer" but takes dicts, and writes their members in the
    order specified by "fieldNames".

    When using "writerow()", if "fieldNames":
        is None: fields are written in alphabetical order.
        mentions a field that is not known, it is written as "".
        mentions a field that is missing, it is written as ""
            (or an type-appropriate default, if the type is known).
        does not list a field that does exist, it is omitted.

    The goal here is that the same inventory of fields is written for
    every record, regardless of whether some are sometimes missing or extra.
    For some potential output formats, it may be ok to omit missing/ empty/
    default fields. This is not yet supported.
    """

    # For specifying fieldFormats: format strings like "%-8.4f", etc.
    _formatRegex = r"%-?\d+(\.\d+)[dxobsfg]"

    def __init__(self,
        f: IO,
        #*args1,
        fieldNames: Union[List,'FieldSchema'] = None,
        fieldformats: list = None,
        restval: str = "",
        extrasaction: str = "raise",
        dialect: str = "excel",
        disp_None: str = "[none]"
        #**kwds1
        ):
        self.f            = f
        self.fieldNames   = fieldNames
        self.restval      = restval
        self.extrasaction = extrasaction
        self.dialect      = predefinedDialects[dialect]
        self.disp_None    = disp_None

        if (fieldNames):
            if (not isinstance(fieldNames, list)):
                raise ValueError("fieldNames must be a list.")
            if (fieldformats and not len(fieldNames) == len(fieldformats)):
                raise ValueError("")
        if (fieldformats):
            for ff in fieldformats:
                if (not re.match(DictWriter._formatRegex, ff)):
                    raise ValueError("Unparseable fieldFormat '%s'." % (ff))

    def writeheader(self) -> None:
        self.writerow(self.fieldNames)

    def writerows(self, rows: List) -> int:
        rnum = 0
        for row in rows:
            rnum += 1
            self.writerow(row)
        return rnum

    def writerow(self, row: dict) -> None:
        #nDelims = len(self.dialect.delimiter)  # For rotating delims a la *paste*
        buf = ""
        if (self.fieldNames is None):
            self.fieldNames = sorted(row.keys())
        thisDelim = self.dialect.delimiter
        badKeys = set(list(self.fieldNames)) - set(list(row.keys()))
        if (badKeys):
            lg.error("Extra keys found: %s", badKeys)

        for fieldName in self.fieldNames:
            # Some *nix utils support cyclic delimiters....
            #thisDelim = self.dialect.delimiter[ i % nDelims ]  # cf *nix `paste`...
            #fieldName = self.fieldNames[fnum]
            fval = row[fieldName] if fieldName in row else ""
            formattedVal = self.formatOneField(fval)
            buf += formattedVal + thisDelim
        buf[-len(thisDelim):] = self.dialect.lineterminator
        self.f.write(buf)

    def writecomment(self, s: str):
        self.f.write(self.dialect.comment + s + self.dialect.lineterminator)

    def formatOneField(self, fval: Any) -> str:
        return self.formatScalar(fval)

    def formatScalar(self, obj: Any) -> str:  # From alogging.py
        # TODO: Escaping???
        #
        ty = type(obj)
        if (obj is None):
            return self.disp_None
        elif (isinstance(obj, str)):
            return '"%s"' % (obj)
        elif (isinstance(obj, bytearray)):
            return 'b"%s"' % (obj)
        #elif (isinstance(obj, buffer)):
        #    return '"%s"' % (obj)
        #elif (isinstance(obj, storage)):
        #    return "%s" % (obj)

        elif (isinstance(obj, bool)):
            if (obj): return "True"
            return "False"

        elif (isinstance(obj, int)):
            return "%8d" % (obj)
        elif (isinstance(obj, float)):
            return "%12.4f" % (obj)
        elif (isinstance(obj, complex)):
            return "%s" % (obj)

        # Ok, following aren't scalars.....
        elif (isinstance(obj, dict)):
            return "{|%d|}" % (len(obj))
        elif (isinstance(obj, list)):
            return "[|%d|]" % (len(obj))
        elif (isinstance(obj, tuple)):
            return "(|%d|)" % (len(obj))
        elif (isinstance(obj, set)):
            return "[set |%d|]" % (len(obj))
        elif (isinstance(obj, frozenset)):
            return "[frset |%d|]" % (len(obj))

        elif (isinstance(obj, object)):
            return "[%s |%d|]" % (ty, len(obj))
        return "[???] %s" % (obj)
        # end formatScalar


###############################################################################
# TODO: Move to separate package? Add writerXSV().
# TODO: Sax-style reader layer for regular CSVs?
#
class DictWriterXSV(DictWriter):
    def __init__(self,
        f: IO,
        fieldNames: Union[List,'FieldSchema'] = None,
        fieldformats: list = None,
        restval: str = "",
        extrasaction: str = "raise",
        dialect:DialectX = "XSV",
        disp_None: str = "[none]"  # TODO: Move into FieldInfo
        #**kwds1
        ):
        super(DictWriter, self).__init__()
        self.f            = f
        self.schema       = None
        if (isinstance(fieldNames, FieldSchema)):
            self.schema = fieldNames
            self.fieldNames = fieldNames.getFieldNames()
        self.restval      = restval
        self.extrasaction = extrasaction
        self.disp_None    = disp_None

    def writeheader(self, tableName:str="", dcMetadata:Dict=None) -> None:
        attrs = ' name="%s"' if tableName else ""
        if (dcMetadata):
            for k in sorted(list(dcMetadata.keys)):
                attrs += self.makeAttr(k, dcMetadata[k])
        buf = "<Xsv>\n<Table" + attrs + ">"
        for fname in self.fieldNames:
            buf += fname + '="str"'
        self.f.write(buf)

    def writerows(self, rows: List) -> int:
        rnum = 0
        for row in rows:
            rnum += 1
            self.writerow(row)
        return rnum

    def writerow(self, row: dict) -> None:
        buf = ""
        if (self.fieldNames is None):
            self.fieldNames = sorted(row.keys())

        for fname in self.fieldNames:
            if (fname not in row):  continue  # TODO restval?
            fval = str(row[fname])            # TODO format?
            buf += self.makeAttr(fname, fval)
        self.f.write("<Rec%s />\n" % (buf))

    def writecomment(self, s: str):
        self.f.write("<!--%s-->" % (DictWriterXSV.escapeXmlComment(s)))

    def writetrailer(self):
        self.f.write("</Table>\n</Xsv>\n")

    @staticmethod
    def makeAttr(k:str, v:Any):
        return ' %s="%s"' % (k, DictWriterXSV.escapeXmlAttribute(v))

    @staticmethod
    def escapeXmlAttribute(s:str) -> str:
        """Escape as need for quoted attributes.
        Quietly deletes any non-XML control characters!
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = re.sub(r"&",  "&amp;", s)
        s = re.sub(r"<",  "&lt;", s)
        s = re.sub(r'"', "&quot;", s)
        return(s)

    @staticmethod
    def escapeXmlComment(s:str) -> str:
        """Escape as needed for comment.
        XML doesn't define a standard escaping for this, so I chose one.
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = re.sub(r"--", "\u2014", s)
        return(s)


###############################################################################
#
class SAXEvent(Enum):
    """The kinds of events that can be returned from parsing.
    """
    ERROR       = 0
    Init        = 1
    XMLDecl     = 2
    Doctype     = 3
    Element     = 4
    Attlist     = 5
    DoctypeFin  = 6

    Start       = 10
    Char        = 11
    Comment     = 12
    Entity      = 13
    End         = 14

    Final       = 100

class FStyle(Enum):  # Cf Note "XML treatments of CSV ish data"
    """Some options for how to map CSV items into SAX events.
    """
    FieldsAsAttributes  = 1  # <Rec name1="val`"... />
    FieldsAsElements    = 2  # <Rec><Name1>val</Name1>....</Rec>
    FieldsAsTyped       = 3  # <Rec><Name1 type="int">val</Name1>....</Rec>

class SAXreader:
    """Read CSV and pass back as if it was XML. Always has a Table and a Record element;
    the field names and values can be organized in several ways (see FStyle).

    or
        <Rec><Name1>val</Name1>....</Rec>
    """
    def __init__(self,
        f:IO,                    # file handle, File object, etc.
        fieldNames=None,         # iterable of names (None->use header rec)
        restkey: List=None,      # store any extras as list under this key
        restval: Any=None,       # default any missing fields to this value
        dialect: DialectX=None,
        schema: 'FieldSchema'=None,
        **kwargs
        ):
        self.f = f
        self.fieldNames = fieldNames  # If none, assume header
        self.restkey = restkey        # Field name for leftovers
        self.restval = restval        # Values for missing fields

        if (dialect): self.dialect = dialect
        else: self.dialect = DialectX(**kwargs)
        if (schema): self.schema = schema
        elif (fieldNames): self.schema = FieldSchema(fieldNames)
        else: self.schema = None      # Set up during first read

        self.callBacks = {}

        self.names = {
            "Table": "Table",
            "Record": "Record",
            "Field": "Field",
            "TypeAttr": "type",
        }

    def setCallback(self, event:SAXEvent, cb:Callable):
        self.callBacks[event] = cb

    def parse(self, file:str, fieldStyle:FStyle) -> None:
        """Generate SAX-style events representing the data, from any of a few layouts.
        """
        st = ch = en = None
        if (SAXEvent.Start) in self.callBacks: st = self.callBacks[SAXEvent.Start]()
        if (SAXEvent.Char) in self.callBacks: ch = self.callBacks[SAXEvent.Char]()
        if (SAXEvent.End) in self.callBacks: en = self.callBacks[SAXEvent.End]()

        theReader = DictReader(
            file, dialect=self.dialect, schema=self.schema)

        if (SAXEvent.Init) in self.callBacks:
            self.callBacks[SAXEvent.Init]()
        if (SAXEvent.XMLDecl) in self.callBacks:
            self.callBacks[SAXEvent.XMLDecl]()

        if (self.dialect.header):  # TODO: XSD, RelaxNG...
            if (SAXEvent.Doctype) in self.callBacks:
                self.callBacks[SAXEvent.Doctype]()
            self.callBacks[SAXEvent.Element](self.names["Table"], "(%s)+" % (self.names["Table"]))
            for fi in self.schema:
                # Map types more specifically than #CDATA
                self.callBacks[SAXEvent.Attlist](fi.fname, "CDATA", fi.fdefault or '""')
                # TODO: Coalesce
            if (SAXEvent.DoctypeFin) in self.callBacks:
                self.callBacks[SAXEvent.DoctypeFin]()

        if (st): st(self.names["Table"])
        for fdict in theReader:
            #if (SAXEvent.Comment) in self.callBacks:
            #    self.callBacks[SAXEvent.Comment]()

            if (fieldStyle == FStyle.FieldsAsAttributes):
                attrs = []
                for fname in self.fieldNames: # <Rec n1="val`"... />
                    attrs.append(fname)
                    attrs.append(fdict[fname])
                if (st): st(self.names["Record"], *attrs)
                if (en): en(self.names["Record"])

            elif (fieldStyle == FStyle.FieldsAsElements):  # <Rec><n1>val</1>...</Rec>
                if (st): st(self.names["Record"])
                for fname in self.fieldNames:
                    st(fname)
                    ch(fdict[fname])
                    en(fname)
                if (en): en(self.names["Record"])

            elif (fieldStyle == FStyle.FieldsAsTyped):  # <Rec><n1 type="int">val</n1>....</Rec>
                if (st): st(self.names["Record"])
                for fname in self.fieldNames:
                    st(fname, "TypeAttr", self.schema[fname].ftype)
                    ch(fdict[fname])
                    en(fname)
                if (en): en(self.names["Record"])
            else:
                if (SAXEvent.ERROR) in self.callBacks:
                    self.callBacks[SAXEvent.ERROR](
                        "Unknown fieldStyle value %s" % (fieldStyle))

        if (en): en(self.names["Table"])
        if (SAXEvent.Final) in self.callBacks:
            self.callBacks[SAXEvent.Final]()


###############################################################################
#
class FsplitWriter:
    def __init__(self, csvfile:IO, dialect='excel', **formatParams):
        self.dialect = DialectX(dialect=dialect, **formatParams)
        self.csvfile = csvfile

    def writeheader(self, fieldNames: List) -> None:
        self.writerow(fieldNames)

    def writerow(self, row:list) -> None:
        nDelims = len(self.dialect.delimiter)
        buf = ""
        for i, field in enumerate(row):
            thisDelim = self.dialect.delimiter[ i % nDelims ]
            buf += field + thisDelim
        buf[-len(thisDelim):] = self.dialect.lineterminator
        self.csvfile.write(buf)

def writer(csvfile:IO, dialect='excel', **formatParams) -> FsplitWriter:
    return FsplitWriter(csvfile, dialect=dialect, **formatParams)


###############################################################################
#
escapeMap = {
    #"b":     "\b",  # Bell?
    "f":     "\f",  # FF
    "n":     "\n",  # LF
    "r":     "\r",  # CR
    "t":     "\t",  # TAB
    "v":     "\v",  # VTAB
    "\\":    "\\",  # BACKSLASH
    "0":     "\0",  # NULL
}

UQuotePairs = {  # From my 'UnicodeSpecials'
    "SINGLE": ( 0x0027, 0x0027, "APOSTROPHE" ),
    "DOUBLE": ( 0x0022, 0x0022, "QUOTATION MARK" ),
    "BACKP":  ( 0x0060, 0x0027, "GRAVE ACCENT, APOSTROPHE" ),
    "SCURLY": ( 0x2018, 0x2019, "[LEFT,RIGHT] SINGLE QUOTATION MARK" ),
    "DCURLY": ( 0x201C, 0x201D, "[LEFT,RIGHT] DOUBLE QUOTATION MARK" ),
    "SHILO9": ( 0x201A, 0x201B, "SINGLE [LOW-9, HIGH-REVERSED-9] QUOTATION MARK" ),
    "DHILO9": ( 0x201E, 0x201F, "DOUBLE [LOW-9, HIGH-REVERSED-9] QUOTATION MARK" ),
    "SANGLE": ( 0x2039, 0x203A, "SINGLE [LEFT,RIGHT]-POINTING ANGLE QUOTATION MARK" ),
    "DANGLE": ( 0x00AB, 0x00BB, "[LEFT,RIGHT]-POINTING DOUBLE ANGLE QUOTATION MARK" ),
    "SUBST":  ( 0x2E02, 0x2E03, "[LEFT,RIGHT] SUBSTITUTION BRACKET" ),
    "DSUBST": ( 0x2E04, 0x2E05, "[LEFT,RIGHT] DOTTED SUBSTITUTION BRACKET" ),
    "TRANSP": ( 0x2E09, 0x2E0A, "[LEFT,RIGHT] TRANSPOSITION BRACKET" ),
    "ROMISS": ( 0x2E0C, 0x2E0D, "[LEFT,RIGHT] RAISED OMISSION BRACKET" ),
    "LOPARA": ( 0x2E1C, 0x2E1D, "[LEFT,RIGHT] LOW PARAPHRASE BRACKET" ),
    "VBARQ":  ( 0x2E20, 0x2E21, "[LEFT,RIGHT] VERTICAL BAR WITH QUILL" ),
}

lastQuoteArg = None
lastQuoteMap = None

def setupQuoteMap(quoteArg: str) -> Dict:
    """Given a specification of a kind of quoting, return a dict that
    maps one or more "open" quote characters to their corresponding "close"
    quote characters (which may be the same, as with straight quotes and
    apostrophers; or different, as with curly quotes).

    @param quoteArg may be specified:
        as a mnemonic;
        as a single character to serve as both open and close; or
        as a string of two characters, open then close.
    """
    global lastQuoteArg, lastQuoteMap
    if (lastQuoteArg and lastQuoteArg == quoteArg):
        return lastQuoteMap

    lastQuoteMap = {}
    if (not quoteArg):
        return lastQuoteMap
    if (quoteArg in UQuotePairs):
        tup = UQuotePairs[quoteArg]
        lastQuoteMap[chr(tup[0])] = chr(tup[1])
    elif (quoteArg == "BOTH"):
        lastQuoteMap["'"] = "'"
        lastQuoteMap['"'] = '"'
    elif (quoteArg == "ALL"):
        for tup in UQuotePairs:
            lastQuoteMap[chr(tup[1])] = chr(tup[2])
    elif (len(quoteArg) == 1):
        lastQuoteMap[quoteArg] = quoteArg
    elif (len(quoteArg) == 2):
        lastQuoteMap[quoteArg[0]] = quoteArg[1]
    else:
        raise ValueError("Unknown quotechar value '%s'." % (quoteArg))
    lastQuoteArg = quoteArg
    return lastQuoteMap

def unescapeViaMap(c: str) -> str:
    if (c in escapeMap): return escapeMap[c]
    return c

def dquote(s: str) -> str:
    """Put double angle quotes around a string for display.
    """
    if (args.visible):
        s = re.sub(r"([\x00-\x20])", visify, s)
    return "\u00AB" + str(s) + "\u00BB"

def visify(mat):
    return chr(0x2400 + ord(mat.group(1)))

def parseEntity(s: str) -> (str, int):
    """Handle XML/HTML entity and numeric character references.
    Just pass this off to Python html package (only imported if needed).
    NOTE: Unknown entities, like "&foo;", do not raise an error.
    """
    from html import unescape
    mat = re.match(r"&(#\d+|#x[\da-f]+|\w[\d\w]*);", s, flags=re.I|re.U)
    #info2("Match against '%s':\n%s" % (s, mat))
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
    # Regexes for auto-typing, value checking, etc.
    #
    intExpr = r"^[-+]?\d+$"
    floatPart = r"[-+]?\d+(\.\d+)?"
    expPart = r"([eE][-+]?\d+)?"
    floatExpr = r"^" + floatPart + r"$"
    complexExpr = r"^" + floatPart + r"\+" + floatPart + r"[ij]$"
    vectorExpr = r"^\[\s*%s(\s*,\s*%s)*\]$" % (floatPart, floatPart)
    #identExpr = r"^\w+$"

    def __init__(self,
        boolCasterFunc: Callable=None,
        datetimeCasterFunc: Callable=None,
        specialFloats: bool=False
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

    @staticmethod
    def checkTypeList(typeList: List) -> None:
        """OBSOLETE -- check whether a list of field types is legit.
        Replaced by FieldSchema support.
        """
        if (not isinstance(typeList, list)): return
        for i, t in enumerate(typeList):
            if (isinstance(t, type)): continue
            if (dt.isADatatype(t)): continue
            if (callable(t)): continue
            raise ValueError(
                "Type %d is not a Python or Datatypes type, or callable: %s"
                % (i, repr(t)))

    @staticmethod
    def datetimeCaster(s: str) -> str:
        """Return a date, time, or datetime object created from a string, or
        raises ValueError otherwise.
        """
        dateRegex = r"\d\d\d\d-\d\d-\d\d"
        timeRegex = r"\d\d:\d\d:\d\d(\.\d+)?(Z|[-+]\d+)?"
        dateTimeRegex = dateRegex + "T" + timeRegex

        if (re.match(dateTimeRegex, s)):
            return datetime.datetime(s)
        if (re.match(dateRegex, s)):
            return datetime.date(s)
        if (re.match(timeRegex, s)):
            return datetime.time(s)
        raise ValueError("String cannot be parsed as date and/or time: '%s'" % (s))

    @staticmethod
    def boolCaster(s: str) -> bool:
        """Return True or False if the value is whatever the data uses for boolean
        values, Otherwise it should raise ValueError, in which case we
        go on to try other types.
        """
        if (s.strip in [ "False", "True", False, True ]): return bool(s.strip())
        raise ValueError

    def autoType(self, tok: str) -> Any:
        """Convert a string to the most specific type we can.

        Complex uses the Python "1+1j" (not "1+1i"!) form)
        Leading and trailing whitespace are stripped for testing, but
        not for returned string values.

        Other types to maybe add:
            SVG paths:    "M 10 10 H 90 V 90 H 10 L 10 10"
            n-D vectors:  "(1.0, -2.1)"
        """
        if (not isinstance(tok, str)):
            return tok

        tok2 = tok.strip()

        if (tok2 == ""):
            return tok
        if (self.boolCasterFunc):
            try: return self.boolCasterFunc(tok2)
            except ValueError: pass
        # Prevent "float" from catching these when not wanted:
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

    def guessType(self, tok: str, vectors:bool=False) -> (str, Any):
        """Find the most specific type we can justify, and
        return that type's *name* plus the value cast to that type.
        Return the name b/c of ones like xint, anyint, etc.
        Convert type name to actual type via
        Other types to maybe add:
            SVG paths:    "M 10 10 H 90 V 90 H 10 L 10 10"
            n-D vectors:  "(1.0, -2.1)"
        """
        if (not isinstance(tok, str)):
            return type(tok), tok

        tok2 = tok.strip()

        if (tok2 == ""):
            return "None", None
        if (self.boolCasterFunc):
            try: return "bool", self.boolCasterFunc(tok2)
            except ValueError: pass
        # Prevent "float" from catching these when not wanted:
        if (not self.specialFloats and tok2 in ("NaN", "inf", "-inf", "+inf")):
            return "str", tok2
        if (self.datetimeCasterFunc):
            try: return "datetime", self.datetimeCasterFunc(tok2)
            except ValueError: pass
        try: return "int", int(tok2, 0)
        except ValueError: pass
        try: return "float", float(tok2)
        except ValueError: pass
        try: return "complex", complex(tok2)  # Test *after* float
        except ValueError: pass

        if (vectors and re.match(self.vectorExpr, tok2)):
            return "array", self.str2array(tok2)

        return "str", tok

    def str2array(self, s:str) -> array.array:
        values = re.split(r"\s*,\s*", s.strip("[ ]"))
        return array.array, array.array('f', [ float(x) for x in values ])

DTH = DatatypeHandler()


###############################################################################
# TODO: Integrate this tiny schema-ish feature for type-checking etc.
#
class FieldInfo:
    """Information about a particular field, such as name, type, default.
    See also parseHeaderStrToSchema(), which parses declarations then passes
    them here; and class DatatypeHandler; and Datatypes.py.

    'freservedValues' is an optional dict that maps special values to
    desired Python equivalents. For example, a file might use "-" (or even 999)
    to represent missing data points, in which case one could set:
        freservedValues = { "-":None }
    TODO: Parsing and applying constraints and required/defaults
    TODO: Careful about type names as string, actual types, and callable checkers
    """
    # Define the types that can be used in header hints.
    # This is just for CSV fields, so no aggregates/collections/etc.
    # Largely based on Python + XSD Datatypes. However, not all of either.
    # cf Datatypes.py
    #
    KnownTypes = {
        "BOOL":       (bool, 10),
        # TODO: values?  bool[T,Nil]?

        "INT":        (int, 20),
        "XINT":       (int, 11),
        "OINT":       (int, 12),
        "ANYINT":     (int, 13),  # 0xFF or 0777 or 999

        "FLOAT":      (float, 30),
        "PROB":       (float, 31),

        "COMPLEX":    (complex, 40),

        "ARRAY":      (array.array, 50),
        # TODO: int vs. float vs. complex? tensor? size?

        "DATETIME":   (datetime.datetime, 60),
        "DATE":       (datetime.date, 61),
        "TIME":       (datetime.time, 62),
        "EPOCH":      (float, 63),
        "TIMEDELTA":  (datetime.timedelta, 70),
        # YEAR MONTH DAY JULIAN HOUR MIN SEC OFFSET

        "STR":        (str, 100),
        "IDENT":      (str, 101),   # word-char-initial token
        "URI":        (str, 102),
    }

    __reservedValues__ = {
        "None": None,
        "NaN": float("NaN"),
        "Inf": float("Inf"),
        "-Inf": float("-Inf"),
        "-Zero": float("-0"),
        "True": True,
        "False": False,
    }

    def __init__(
        self,
        fname:str,
        ftype:Union[str,type,Callable]=None,
        fconstraint:str=None,
        fdefault:Any=None,  # TODO: Be sure to unescape this
        frequired:bool=False,  # Do not pass "!" as fdefault
        fformat:Union[str,Callable]=None,
        fnormalizer:Callable=None,
        funiq:bool=False,
        fnum:int=-1,
        ):
        assert fname
        #assert fnum>0
        if (not (ftype is None or isinstance(ftype, (type, Callable)))):
            lg.critical("ftype passed as %s (%s).", ftype, type(ftype))
            assert False
        self.fname = fname
        self.fnum = fnum
        if (isinstance(ftype, type)):
            ftype = ftype.__name__
        if (ftype in self.KnownTypes):
            self.ftype = ftype
        else:
            lg.error("Unrecognized type-name '%s'.", ftype)
            ftype = str
        self.fconstraint = fconstraint
        self.fdefault = fdefault
        self.frequired = frequired

        self.fformat = fformat
        self.fnormalizer = fnormalizer
        self.funiq = funiq
        # type=specific constraints:
        self.regexConstraint = None
        self.fmin = None
        self.fmax = None

        if (self.frequired and self.fdefault is not None):
            lg.error("Don't set 'required' when there's also a default value.")
            self.frequired = False

    def handleConstraintString(self, ftype:type, fconstraint:str) -> bool:
        """Check whether the constraint field (in [] in the header) is
        appropriate for the given type. This is *not* a check for actual
        values (see isValueOk() for that).
        TODO: Test a bunch, esp. escaped regexes for strings.
        """
        if (not fconstraint):
            return True

        if (fconstraint[0] == "[" and fconstraint[-1] == "]"):
            fconstraint = fconstraint[1:-1]

        if (ftype == bool):
            pass
        elif (ftype in [ int, "int", "xint", "oint", "anyine" ]):
            mat = re.match(FieldSchema.intConExpr, fconstraint)
            if (mat):
                self.fmin = int(mat.group(1))
                self.fmax = int(mat.group(2))
            else:
                raise ValueError("Invalid integer range constraint '%s'." % (fconstraint))
        elif (ftype == float):
            mat = re.match(FieldSchema.floatConExpr, fconstraint)
            if (mat):
                self.fmin = float(mat.group(1))
                self.fmax = float(mat.group(2))
            else:
                raise ValueError("Invalid float range constraint '%s'." % (fconstraint))
        elif (ftype == complex):
            pass
        elif (ftype == array):
            pass  # TODO: Unfinished. Any fconstraints for vectors?
        elif (ftype == str):
            try:
                _checked = re.compile(fconstraint)
            except re.error as e:
                raise ValueError(
                    "Invalid string  constraint '%s'." % (fconstraint)) from e
        else:
            raise ValueError("Invalid declared type '%s'." % (ftype))
        return

    def isValueOk(self, val: Any) -> bool:
        """Determine whether a given field as a string, fits the datatype and
        constraints (if any); or if not required, is empty.
        Actual normalizing, typecasting, etc. happen under handleRecord().
        """
        if (val is None):
            if (self.frequired): return False

        if (self.ftype == "xint"): val = int(val, 16)
        elif (self.ftype == "oint"): val = int(val, 8)
        elif (self.ftype == "int"): val = int(val, 10)
        elif (self.ftype == "anyint"): val = int(val)
        elif (self.ftype == "float"): val = float(val)
        elif (self.ftype == "complex"): val = complex(val)

        if (0 and not isinstance(val, self.ftype)):  # TODO Finish
            try:
                val = self.castToType(val)
            except ValueError:
                return False
        return True

    def castToType(self, field:Any):
        """Take a raw string field value and case it to the declared type
        for that field. If it's already not a string, cast it anyway.
        TODO: Is there a clean way to cast to a variable type?
        """
        tgtType = self.ftype
        if (isinstance(tgtType, type)): tgtType = tgtType.__name__

        if (tgtType == "bool"):
            val = bool(field)
            return val

        if (tgtType.endswith("int")):
            if (self.ftype == "xint"): val = int(val, 16)
            elif (self.ftype == "oint"): val = int(val, 8)
            elif (self.ftype == "int"): val = int(val, 10)
            elif (self.ftype == "anyint"): val = int(val)
            else: raise KeyError("Unknown int type '%s'." % (self.ftype))
            val = int(field)
            if ((self.fmin and val < self.fmin) or
                (self.fmax and val > self.fmax)):
                raise ValueError("int constraint [%d%d] violated."
                    % (self.fmin, self.fmax))
            return val
        if (tgtType == "float"):
            val = float(field)
            if ((self.fmin and val < self.fmin) or
                (self.fmax and val > self.fmax)):
                raise ValueError("float constraint [%d%d] violated."
                    % (self.fmin, self.fmax))
            return val
        if (tgtType == "complex"):
            val = complex(field)
            #if (): raise ValueError
            return val

        if (tgtType == "datetime"):
            val = datetime.datetime.fromisoformat(field)
            #if (): raise ValueError
            return val
        if (tgtType == "date"):
            val = datetime.datetime.fromisoformat(field)
            #if (): raise ValueError
            return val
        if (tgtType == "time"):
            val = datetime.datetime.fromisoformat(field)
            #if (): raise ValueError
            return val
        if (tgtType == "timedelta"):
            val = datetime.timedelta(field)  # TODO: format?
            #if (): raise ValueError
            return val
        if (tgtType == "epoch"):
            val = datetime.datetime.fromtimestamp(float(field))
            #if (): raise ValueError
            return val

        if (tgtType == "array"):
            val = dtHandler.str2array(field)
            #if (): raise ValueError
            return val

        if (tgtType == "str"):
            val = str
            # TODO: Add ^$? re.I?
            if (self.fconstraint and not re.search(self.fconstraint, val)):
                raise ValueError("str constraint /%s/ violated." % (self.fconstraint))


###############################################################################
#
class FieldSchema():
    """Keep track of the known fields, each as a FieldInfo.
    The list can be built manually, or initialized from a header record, which
    may have just names, or a syntax much ilke Python type-hints.
    See also Homogeneous.py.

    Usage:
        fs = FieldSchema()
        fs.append(FieldInfo("given",  str, "", 1, "%-16s", 1))
        fs.append(FieldInfo("family", str, "", 1, "%-16s", 2))
        fs.append(FieldInfo("age",    int, None, 0, "%3d", 3))
        ...
    """
    # Regexes to check header declaration syntax
    # TODO: Doesn't allow for [] in regex constraints....
    # Header record doesn't allow for unescaped delim in constraints
    #
    fnameExpr = r"(\w+)"
    fconsExpr = r"(\[[^\]]*\])?"
    ftypeExpr = r"(:\w+" + fconsExpr + r")?"
    fdfltExpr = r"(=\w+|!)?"
    hintExpr = fnameExpr + ftypeExpr + fdfltExpr + r"$"

    # More detailed regexes to check internal syntax of constraints (per type)
    intConExpr = r"^" + DTH.intExpr + "," + DTH.intExpr + "$"
    floatConExpr = r"^" + DTH.floatExpr + "," + DTH.floatExpr + "$"
    complexConExpr = r"^" + DTH.complexExpr + "," + DTH.complexExpr + "$"

    def __init__(self, fieldNames:Union[List,str]=None, nameRegex:str=None):
        #super(list, FieldSchema).__init__(self)
        self.nameRegex = nameRegex
        self.theFieldInfos = []
        self.infoDict = {}
        if (fieldNames):
            if (isinstance(fieldNames, str)):
                fieldNames = re.split(r"\W+", fieldNames, flags=re.U)
            for fname in fieldNames:
                self.append(FieldInfo(fname=fname))

    def len(self):
        return len(self.theFieldInfos)

    def __getitem__(self, n:Union[int, str]) -> FieldInfo:
        """Retrieve one FieldInfo object, by name of number.
        TODO: This should count from 1, field numbers....
        TODO: Make up out-of-range names as needed?
        """
        if (isinstance(n, int)): return self.theFieldInfos[n]
        if (n in self.infoDict): return self.infoDict[n]
        raise KeyError("Cannot find field %s." % (n))

    def getFieldInfo(self, n: Union[int, str]) -> FieldInfo:
        return self[n]

    def getFieldNames(self) -> List:
        fnames = []
        for i in range(len(self.theFieldInfos)):
            fnames.append(self.theFieldInfos[i].fname)
        return fnames

    def append(
        self,
        finfo:FieldInfo=None,
        fname:str=None,
        ftype:type=str,
        fconstraint:str=None,
        fdefault:Any=None,
        frequired:bool=False,
        fformat:Union[str,Callable]=None,
        fnormalizer:Callable=None,
        funiq:bool=False
        ) -> FieldInfo:
        """Add a FIeldInfo to the list and the name-index. It can
        be constructed and passed in 'fifo', or created here from
        the other arguments. If no name is given, one is generated.
        """
        fnum = len(self.theFieldInfos)
        if (isinstance(finfo, FieldInfo)):
            if (not finfo.fname): finfo.fname = "Field_%02d" % (len(self))
        else:
            if (not fname): fname = "Field_%02d" % (len(self))
            finfo = FieldInfo(fname, ftype=ftype, fconstraint=fconstraint,
                fdefault=fdefault, frequired=frequired, fformat=fformat,
                fnormalizer=fnormalizer, funiq=funiq, fnum=fnum)

        if (finfo.fname in self.infoDict):
            raise KeyError("Field '%s' already in FieldSchema." % (finfo.fname))
        if (self.nameRegex and not re.match(self.nameRegex, finfo.fname)):
            lg.warning("Field name '%s' does not match nameRegex /%s/.",
                finfo.fname, self.nameRegex)
            # TODO: Map to something acceptable?

        #lg.info("Appending field #%d: '%s'", fnum, finfo.fname)
        self.theFieldInfos.append(finfo)
        self.infoDict[finfo.fname] = finfo
        return finfo

    def handleRecord(self, fields:List) -> List:
        """Given a truly raw sets of fields, apply all the schema stuff:
            * normalizer
            * default/required
            * typecasting
            * constraint-checking
        """
        for i in range(len(fields)):
            finfo = self.getFieldInfo(i)
            if (finfo.normalizer):
                fields[i] = finfo.normalizer(fields[i])
            if (finfo.ftype != str):
                fields[i] = fields[i].strip()
            if (fields[i] == ""):
                if (finfo.frequired):
                    raise ValueError("Missing required field %s." % (finfo.fname))
                if (finfo.default): fields[i] = finfo.default
            if (finfo.ftype):
                fields[i] = finfo.castToType(fields[i], finfo)
            # dtHandler.(self, tokens)  # TODO ????
        return fields


###############################################################################
#
def parseHeaderStrToSchema(
    headerItems:Union[List, str],
    dialect:DialectX=None
    ) -> 'FieldSchema':
    """Parse a single header record, extracting the field names and
    other optional declarations info (type hint, default value, required flag).
    Syntax examples:
        city:str
        surName:str!
        age:int=NaN
        exempt:bool=False
        gender:str[M|F|X]=X
    Issues?
        Space and quote stripping?
        Range limits for numerics (dec/bin size; sign)
            int[0:Inf], int[-2^16:0]
            int[neg, pos, nonneg, nonpos, nonzero]
        Non-decimal integers
            int_8, int_64
        Inf/NaN/Missing/etc
        Strings to recognize for booleans
        string regex
        string normalization (upper, lower, title, nfkd)
        dob:date and date components; duration; time; timezone
        URIs
        Identifiers and QNames
    """
    fs = FieldSchema()

    if (isinstance(headerItems, str)):
        headerItems = fsplit(headerItems, dialect=dialect)

    for fnum, rawItem in enumerate(headerItems):
        #lg.info("headItems[%02d]: '%s'", fnum, rawItem)
        cleandialect = cleanField(rawItem, dialect=dialect)
        mat = re.match(FieldSchema.hintExpr, cleandialect)
        #lg.info("hint parse #%d got [ %s, %s, %s, %s ]\n    from '%s'",
        #    fnum, mat.group(1), mat.group(2), mat.group(3), mat.group(4), cleandialect)
        if (mat):
            fname = mat.group(1)
            ftype = mat.group(2)
            fconstraint = mat.group(3)
            fdefault = mat.group(4)
            finfo = FieldInfo(
                fname, ftype=ftype, fconstraint=fconstraint, fdefault=fdefault,
                fnum=fnum)
        else:
            finfo = FieldInfo(fname=rawItem)
        fs.append(finfo)
    return fs


###############################################################################
# The function that actually parses up lines, dealing with various escaping
# and quoting variations, etc.
#
dtHandler = DatatypeHandler()  # TODO: make better

def fsplit(
    s: str,
    dialect: DialectX=None,
    schema: FieldSchema=None,
    **kwargs
    ) -> List:
    """Fancier string splitter / csv parser. Lots of options, Unicode aware.
    Optionally handles datatyping, casting, and defaulting, too. TODO: Or to callers?
    """
    theDialectX = dialect if dialect else DialectX("default")
    theDialectX.applykwOptions(kwargs)
    theDialectX.checkOptions()

    dx = theDialectX

    nDelims = len(dx.delimiter)
    if (nDelims==1 and dx.delimiter[0] == ""):
        return s.split()
    thisDelim = dx.delimiter[0]
    dlen = thisDelim

    currentQuoteMap = setupQuoteMap(dx.quotechar)
    if (dx.skipinitialspace): s = s.lstrip()

    s = s.strip("\uFEFF")  # Lose the dang BOM.

    tokens = [ "" ]
    toIgnore= 0
    pendingQuote = None
    escaped = False
    i = 0
    for i, c in enumerate(s):
        info2("At char %dx: '%s' U+%04x", i, c, ord(c))
        if (toIgnore):
            toIgnore -= 1

        elif (pendingQuote):    # TODO: Test 'escaped' first? Can we escape outside quotes?
            if (c == pendingQuote):
                info2("    Got close quote '%s'.", c)
                if (dx.doublequote and len(s)>i+1 and s[i+1]==pendingQuote):
                    info2("    BUT quote is doubled.")
                    tokens[-1] += pendingQuote
                    toIgnore = 1
                else:
                    pendingQuote = None
            else:
                tokens[-1] += c

        elif (escaped):
            escaped = False
            if (dx.xescapes and c == "x"):
                mat = re.match(r"x([\da-f]{2})|x\{([\da-f]+)\}", s[i:])
                if (not mat):
                    syntaxError(s, i, tokens, "Incomplete \\x escape")
                theHexString = mat.group(1) if mat.group(1) else mat.group(2)
                n = int(theHexString)
                if (n > sys.maxunicode):
                    syntaxError(s, i, tokens,
                        "\\x escape outside Unicode range (%x)." % (n))
                tokens[-1] += chr(n, 16)
                toIgnore = len(theHexString)

            elif (dx.uescapes and c in "Uu"):
                if (c == "u"):
                    mat = re.match(r"u[\da-f]{4}", s[i:])
                    if (not mat):
                        syntaxError(s, i, tokens, "Incomplete \\u escape")
                    tokens[-1] += chr(int(s[i+1:i+5], 16))
                    toIgnore = 4
                if (c == "U"):
                    mat = re.match(r"U[\da-f]{8}", s[i:])
                    if (not mat):
                        syntaxError(s, i, tokens, "Incomplete \\U escape")
                    tokens[-1] += chr(int(s[i+1:i+9], 16))
                    toIgnore = 8
            else:
                tokens[-1] += unescapeViaMap(c)

        elif (c == dx.escapechar):
            info2("    Got escape char.")
            escaped = True

        elif (dx.entities and c == "&"):
            info2("    Got entity start.")
            entExpansion, charsUsed = parseEntity(s[i:])
            if (entExpansion is not None):
                tokens[-1] += entExpansion
                toIgnore = charsUsed - 1
            else:
                syntaxError(s, i, tokens, "Ill-formed character reference")

        elif (c in currentQuoteMap):
            info2("    Got open quote '%s'", c)
            if (tokens[-1] != ""):
                syntaxError(s, i, tokens, "quote not at start of field")
            pendingQuote = currentQuoteMap[c]

        elif (c == thisDelim[0] and s[i:].startswith(thisDelim)):
            info2("Got the delimiter string")
            if (dx.multidelimiter):
                nDelims = 0
                while (s[i+nDelims*dlen].startswith(thisDelim)): nDelims += 1
                toIgnore = (nDelims * dlen) - 1
            if (dx.maxsplit and len(tokens) > dx.maxsplit):
                syntaxError(s, i, tokens,
                    "maxsplit (%d) exceeded." % (dx.maxsplit))
                tokens.append(s[i+len(thisDelim):])
                break
            tokens.append("")

        else:
            tokens[-1] += c

    # At end of record
    #
    if (pendingQuote):
        # If the end of line is still inside quotes, and that's allowed,
        # throw UnclosedQuote exception to signal caller to append
        # another line and call us to parse again. Not efficient, but easy.
        if (dx.quotednewline):
            raise UnclosedQuote("Logical record is: " + s)
        else:
            syntaxError(s, i, tokens,
                "Unresolved quote (expected '%s')" % (pendingQuote))
    if (escaped or pendingQuote):
        syntaxError(s, i, tokens, "Unresolved escapechar or quote")
    if (len(tokens) < dx.minsplit+1):
        syntaxError(s, i, tokens,
            "min %dx tokens needed, but found %dx" % (dx.minsplit, len(tokens)))

    # Apply normalizers, defaults, typecasting, constraint checks, etc.
    if (schema):
        schema.handleRecord(tokens)
    elif (dx.autotype):
        for i, token in enumerate(tokens):
            _typ, val = dtHandler.guessType(token)
            tokens[i] = val

    return tokens

def syntaxError(s, i, tokens, msg:str):
    msg = getContextMsg(s, i, tokens, msg)
    if (args.strict): raise ValueError(msg)
    else: lg.warning(msg)

contextFmt = (
    "At char '%s' (offset %d): %s (preceding token #%d '%s') at %s in:\n    >>%s<<")
fmt2 =  "\n    Full record:\n    >>%s<<"

def getContextMsg(
    s:str,
    offset:int=-1,
    tokens:List=None,
    msg:str="???") -> str:

    msg = contextFmt % (
        s[offset], offset, msg, len(tokens)-1, tokens[-1],
        POINTING_CHAR, context(s, offset))
    if (not args.quiet):
        msg += fmt2 % (s)
    return msg

def context(txt: str, i: int, sideSize=16) -> str:
    """Extract a little context around a given point, and mark the spot.
    """
    stPos = i - sideSize
    if (stPos < 0): stPos = 0
    enPos = i + sideSize
    if (enPos > len(txt)): enPos = len(txt)
    return txt[stPos:i] + POINTING_CHAR + txt[i:enPos]


###############################################################################
# Subcommands
#
def prettyPrint(ifh:IO, idx:DialectX, ischema:FieldSchema) -> int:
    """Read the file and print it out nicely.
    TODO: Switch to user
    """
    recnum = 0
    r = reader(ifh, dialect=idx, schema=ischema)
    for myFields in r:
        assert isinstance(myFields, list), "myFields is a %s" % (type(myFields))

        recnum += 1
        if (recnum == 1):
            ischema = ensureSchema(ischema, myFields, idx, args.ifields)
            ifieldNames = ischema.getFieldNames()
            continue
            #print("names: %s" % (ifieldNames))
        #myFields = fsplit(rec, dialect=idx)
        if (len(myFields) < 2):
            lg.warning("Record %d doesn't seem to have fields (delim is '%s'):\n    %s",
                recnum, idx.delimiter, myFields)
            continue
        print("\n======= Record %d (%d fields):" % (recnum, len(myFields)))
        for fn, fv in enumerate(myFields):
            if (fn >= len(ifieldNames)):
                ischema.append("")
                ifieldNames = ischema.getFieldNames()
            printByApparentType(fn, ifieldNames[fn], fv)
    return recnum

def convert(
    ifh:IO, idx:DialectX, ischema:FieldSchema,
    ofh:IO, odx:DialectX, oschema:FieldSchema,
    nameMap:Dict=None
    ) -> int:
    """Read using one dialect, write out using another.
    This raises the issue of field name mapping.
    For the moment, the names must match up 1:1 (module "" to delete).
    TODO: But a full field name map is needed in general (see changeNames).
    TODO: Also issues of conversions (base, type, split/join, etc). Not here.
    """
    ifieldNames = ischema.getFieldNames()
    ofieldNames = oschema.getFieldNames()
    idr = DictReader(ifh, fieldNames=ifieldNames, dialect=idx)
    odw = DictWriter(ofh, fieldNames=ofieldNames, dialect=odx)

    if (odx.header):  # TODO: Needed?
        odx.fieldNames = ofieldNames
        odx.writeheader()

    recnum = 0
    for inDict in idr:
        recnum += 1
        if (nameMap): outDict = changeNames(inDict, nameMap)
        else: outDict = inDict
        odw.writerow(outDict)
    return recnum

def ensureSchema(
    schemaArg:Union[FieldSchema, List],  # Pre-made schema or list of field-names
    firstRec:str=None,                    # Header rec, if available/applicable
    dialect:DialectX=None,                # Syntax spec
    fsArg:str=None                        # Header rec from another source, like args)
    ) -> 'FieldSchema':
    """Handle the schema arg to ensure we have *some* kind of schema.
    If the caller passed:
        * a real FieldSchema, use it
        * a list of field names, make a schema from them
        * a dialect with headers, parse firstRec
        * an fsArg (presumably from args.ifields or args.ofields), parse it
        * None of those: parse the firstRec and make up that many generic names.
        * Failing that, make a schema of 99 generic names.
    """
    if (args.verbose):
        lg.info("In ensureSchema:\n"
            "    schemaArg   %s\n"
            "    firstRec     %s\n"
            "    dialect      %s (header is %s)\n"
            "    fsArg        %s\n",
            schemaArg, firstRec, dialect, dialect.header, fsArg)

    if (not dialect.header):
        if (not isinstance(firstRec, str)):
            assert False, "firstRec is %s: %s" % (type(firstRec), firstRec)
        if (re.match(r"^(\w+)(,\w+)+$", firstRec)):
            lg.warning("dialect.header is not set, but first record looks like one:\n"
            "    %s", firstRec)

    if (isinstance(schemaArg, FieldSchema)):
        return schemaArg
    if (isinstance(schemaArg, List)):
        return FieldSchema(schemaArg)
    if (dialect.header):
        return parseHeaderStrToSchema(firstRec, dialect=dialect)
    if (fsArg):
        return parseHeaderStrToSchema(schemaArg, dialect=dialect)
    fields = fsplit(firstRec, dialect)
    if (len(fields) > 1):
        return FieldSchema(makeFakeHeader(len(fields)))
    return FieldSchema(makeFakeHeader(99))


def makeFakeHeader(n:int) -> str:
    return ",".join([ "Field_%02d" % (x+1) for x in range(n) ])

def makeNameMap(ifieldNames:List, ofieldNames:List) -> Dict:
    """Given two lists of names, create a dict mapping names in the first,
    to the corresponding names in the second.
    """
    assert len(ifieldNames) == len(ofieldNames)
    nameMap = {}
    for i in range(len(ifieldNames)):
        assert ofieldNames[i] not in nameMap
        nameMap[ifieldNames[i]] = ofieldNames[i]
    return nameMap

def changeNames(olddict:Dict, nameMap:Dict) -> Dict:
    """Copy a dict, but assigning a new key to some/all items based on
    an oldName->newName map provided in another dict.
    If a name maps to falsish, it's skipped/deleted.
    """
    newDict = {}
    for k, v in olddict.items():
        if (k in nameMap and nameMap[k]):
            assert nameMap[k] not in newDict
            newDict[nameMap[k]] = v
    return newDict


###############################################################################
# Main
#
if __name__ == "__main__":
    try:
        import ColorManager
        cm = ColorManager.ColorManager()
    except ImportError:
        cm = None

    def cprint(msg):
        if (cm): print(cm.colorize(msg, "red"))
        else: print("==========> " + msg)

    def testPlus(s, **kwargs) -> List:
        """Run a test that we expect to pass (or at least not die).
        TODO: Factor out data. Add expected result or save and compare.
        """
        print("\nTest string: %s" % (dquote(s)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s" ' % (k, v)
        if (buf): print(" args: " + buf)
        theFields = []
        try:
            if (kwargs):
                theFields = fsplit(s, **kwargs)
            else:
                theFields = fsplit(s)
        except ValueError as e:
            cprint("******* Exception *******\n    %s\n" % (e))
        if (theFields): print("    ==> |%d| %s" % (len(theFields), theFields))
        return theFields

    def testMinus(s:str, msg:str, **kwargs) -> List:
        """Run a test that we expect to fail. Forces 'strict' option
        so we actually get an Exception.
        """
        print("\nTest string: %s" % (dquote(s)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s" ' % (k, v)
        if (buf): print(" args: " + buf)
        theFields = []
        try:
            if (kwargs):
                theFields = fsplit(s, strict=True, **kwargs)
            else:
                theFields = fsplit(s)
            cprint("******* Ooops, error was not raised (%s) *******\n    ==> %s\n"
                % (msg, theFields))
        except ValueError as e:
            print("    (expected) Exception: %s" % (e))
        return theFields

    def phead(msg) -> None:
        print("\n******* %s" % (msg))

    def printByApparentType(_i:int, fName:str, fValue:str) -> None:
        """Like autotype, but for output....
        """
        fmt1 = "    %-" + str(args.width) + "s "
        gType, castValue = DTH.guessType(fValue)
        if (gType == "str"):
            if (args.visible):
                print((fmt1 + "%s") % (fName, visify(fValue)))
            else:
                print((fmt1 + "%s") % (fName, fValue))
        elif (gType == "None"):
            print((fmt1 + "%s") % (fName, "\u2205"))
        elif (gType == "bool"):
            print((fmt1 + "%8s") % (fName, "True" if castValue else "False"))
        elif (gType == "int" or gType == "anyint"):
            print((fmt1 + "%8d") % (fName, int(fValue)))
        elif (gType == "oint"):
            print((fmt1 + "0o%8o") % (fName, int(fValue)))
        elif (gType == "xint"):
            print((fmt1 + "0x%8x") % (fName, int(fValue)))
        elif (gType == "float"):
            print((fmt1 + "%12.3f") % (fName, float(fValue)))
        elif (gType == "complex"):
            print((fmt1 + "%s") % (fName, complex(fValue)))
        elif (gType in [ "datetime", "date", "time", "epoch" ]):
            print((fmt1 + "%s") % (fName, fValue))
        else:
            print((fmt1 + "%s") % (fName, fValue))

    def smokeTest():
        """Try out various options.
        """
        s0 = ""
        testPlus(s0)
        s0 = "no split happens"
        testPlus(s0)
        phead("Commas")
        s0 = "wee fish,ewe,a mare,egrets,moose"
        testPlus(s0, delimiter=",")

        phead("TAB")
        s0 = "wee fish\tewe\ta mare\tegrets\tmoose"
        testPlus(s0, delimiter="\t")
        phead("TAB, but delim not set")
        testPlus(s0)
        phead("TAB, but escaping the one before 'egrets'")
        s0 = "wee fish\tewe\ta mare\tegrets\tmoose"
        s0 = "wee fish\tewe\ta mare\\\tegrets\tmoose"
        testPlus(s0, delimiter="\t", escapechar="\\")

        phead("Escaping:")
        s0 = "aard\\u0076ark|beagle|cat|d\\x6Fg|&#101;&#x67;r&eacute;&#X00000074;"
        print("vbar, without special escaping options")
        testPlus(s0, delimiter="|")
        print("vbar, with xescapes")
        testPlus(s0, delimiter="|", xescapes=True)
        print("vbar, with uescapes")
        testPlus(s0, delimiter="|", uescapes=True)
        print("vbar, with entities")
        testPlus(s0, delimiter="|", entities=True)
        print("vbar, with all of those")
        testPlus(s0, delimiter="|", xescapes=True, uescapes=True, entities=True)

        phead("Multi-char delim:")
        s0 = "lorem##ipsum##dolor##sit##amet"
        testPlus(s0, delimiter="##")
        s0 = "lorem<>ipsum<>dolor<>sit<>amet"
        testPlus(s0, delimiter="<>")

        phead("Quoting:")
        s0 = 'wee fish$ewe$"a mare"$egrets$"moo$e"'
        testPlus(s0, delimiter="$", quotechar='"')

        s0 = "wee fish$ewe$'a mare'$egrets$'moo$e'"
        testPlus(s0, delimiter="$", quotechar="'")

        s0 = "'wee fish'$ewe$‘a mare’$egrets$“moo$e”"
        testPlus(s0, delimiter="$", quotechar='“”')

        s0 = "'wee fish'$ewe$‘a mare’$egrets$“moo$e”"
        testPlus(s0, delimiter="$", quotechar='“”')

        #SINGLE DOUBLE ANGLE CURLY ALL
        # quotes inside quotes

        phead("doublequote:")
        s0 = """lorem,ipsum,"(he said) ""dolor"", I think",sit,amet"""
        testPlus(s0, delimiter=",", doublequote=True)
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
        s0 = "lorem#ipsum#dolor#sit#amet"
        testMinus(s0, "Too few splits", delimiter="#", minsplit=99)
        testMinus(s0, "Too many splits", delimiter="#", maxsplit=3)

        phead("autotype feature:")
        # TODO: Should the IEEE special floats be caught here?
        s0 = "hello,1,,3.14159,-6.022E+23,1.618+2j,NaN,-inf,+inf,world"
        print("Test string: %s" % (dquote(s0)))
        stuffs = fsplit(s0, delimiter=",", autotype=True)
        for i0, stuff in enumerate(stuffs):
            print("    %d: %-16s %s" % (i0, dquote(stuff), type(stuff)))

        phead("type checking:")

        phead("Errors")
        errTests = [
            ( "hello \\",               "Backslash at end" ),
            ( "hello \\x",              "Incomplete \\x" ),
            ( "hello \\xA",             "Incomplete \\x" ),
            ( "hello \\xZZ",            "Bad hex  \\x" ),
            ( "hello \\",               "???" ),
            ( "hello \\u",              "Incomplete \\u" ),
            ( "hello \\uA",             "Incomplete \\u" ),
            ( "hello \\uAAA",           "Incomplete \\u" ),
            ( "hello &",                "Incomplete enitity ref" ),
            ( "hello &lt does this work?", "Incomplete enitity ref" ),
            ( "hello &gt.",             "Incomplete enitity ref" ),
            ( "hello &amp",             "Incomplete enitity ref" ),
            ( "hello &wo:rld;",         "Qname enitity ref" ),
            ( "hello &#world;",         "Bad decimal char ref" ),
            ( "hello &#08FF;",          "Bad decimal char ref" ),
            ( "hello &#x00GG;",         "Bad hex char ref" ),
            # unclosed quotes, swapped polarity, not at start of field,....
        ]
        for s0, msg0 in errTests:
            testMinus(s0, msg0, delimiter=",",
                xescapes=True, uescapes=True, entities=True)
        return

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
               description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(
            description=descr)

        DialectX.addargs(parser)
        if ("-c" in sys.argv):  # Is this a good idea?
            DialectX.addargs(parser, prefix="o")

        parser.add_argument(
            "-c", action="store_true",
            help="Convert the input to a different CSV-ish format.")
        parser.add_argument(
            "--iencoding", type=str, default="utf-8",
            help="Character encoding for the input.")
        parser.add_argument(
            "--ifields", type=str,
            help="A string to use as header record when there's isn't one.")
        parser.add_argument(
            "--ofields", type=str,
            help="A string to use as output header record (if not same as input one).")
        parser.add_argument(
            "--outputformat", "--oformat", type=str, choices=[ "csv", "xsv" ], default="csv",
            help="Use this to get non-CSV output formats such as XSV (not yet).")  # TODO
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--sax", action="store_true",
            help="Test SAX generation.")
        parser.add_argument(
            "--showDialectX", "--showdx", action="store_true",
            help="Display dialect settings.")
        parser.add_argument(
            "--showQuotes", action="store_true",
            help="Display the named quote-pairs.")
        parser.add_argument(
            "--showSchema", action="store_true",
            help="Display header/schema info.")
        parser.add_argument(
            "--skipRecs", type=int, default=0,         # TODO Add option
            help="Skip this many physical line before starting (not incl. header).")
        parser.add_argument(
            "--validate", action="store_true",
            help="Just report errors (best used with a schemas.")
        parser.add_argument(
            "--visible", action="store_true",
            help="Make test output visible (use control pictures).")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")
        parser.add_argument(
            "--width", type=int, default=16,
            help="Width for label column in prettyprinting.")

        parser.add_argument(
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        if (lg and args0.verbose):
            logging.basicConfig(level=logging.INFO - args0.verbose,
                format="%(message)s")

        return(args0)

    args = processOptions()

    if (args.showQuotes):
        print("Named quote-pairs:")
        for n0, pairInfo in UQuotePairs.items():
            print("    %-8s U+%04x U+%04x %s" % (n0, *pairInfo))
        sys.exit()

    indx0 = DialectX("Salvatore")
    indx0.applyargs(theArgs=args, prefix="")
    if (args.showDialectX):
        print("Input dialect is:\n%s" % (indx0.tostring()))

    inschema0 = parseHeaderStrToSchema(
        args.ifields, dialect=indx0) if (args.ifields) else None

    if (args.c):
        outdx0 = DialectX("Target")
        outdx0.applyargs(theArgs=args, prefix="o")
        if (args.showDialectX):
            print("Output dialect is:\n%s" % (outdx0.tostring()))
        outschema0 = parseHeaderStrToSchema(
            args.ofields, dialect=outdx0) if (args.ofields) else inschema0

    if (not args.files):
        print("Basic testing...")
        smokeTest()
        sys.exit()

    for path in args.files:
        print("\n******* Starting file %s." % (path))
        infh0 = codecs.open(path, "rb", encoding=args.iencoding)

        if (args.c):
            outfh0 = codecs.open(path+".out", "rb", encoding=args.iencoding)
            convert(infh0, indx0, inschema0, outfh0, outdx0, outschema0)
            outfh0.close()
        elif (args.sax):
            raise ValueError("Unfinished.")
        else:
            prettyPrint(infh0, indx0, inschema0)
        infh0.close()

    if (not args.quiet):
        print("\nDone.\n")
