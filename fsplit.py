#!/usr/bin/env python3
#
# fsplit.py: A better (I hope) str.split() or csv package.
# 2020-02-28: Written by Steven J. DeRose.
#
#pylint: disable=W0603,W0511
#
import sys
import argparse
import codecs
import re
from collections import namedtuple
from typing import Dict, Any, Union, IO, List, Callable, Final
from enum import Enum
import ast
import html
import datetime
import uuid
import array
import unicodedata

import logging
from Datatypes import Datatypes

lg = logging.getLogger()
dt = Datatypes()

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
datatypes, and so on. See section [Header Format] for more details.
In short, a FieldSchema can be set up in several ways:

* created from a regular header line (by setting the 'header' option as shown
above). The header line may have just names, or more.

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

** ''fname'' -- the field name, typically an identifier token
** ''ftype'' -- one of the known types, or at least its name
** ''fconstraint'' -- a field constraint as a string (see [Header Format] for
the type-dependent values that can be used)
** ''fdefault'' -- a default value (None may mean no default value, or that the
default value is None -- how would you tell?
** ''frequired'' -- if set, the field must always be non-empty in the data
** ''fformat'' -- a preferred output format, for example "%12.4f". Or a Callable
that takes the (possibly typed) field value and returns a string. A Callable
here is probably most useful to handle "special" values such as None, reserved
codes for things like "missing" or "not applicable", etc.
** ''fnormalizer'' -- a Callable which is the first thing applied to a field once
it is split out from the record (this is still after quote removal and unescaping).
The Callable should take and return strings. Several named normalizers can be
spedified in the header, by inserting them before the []-constraint (see section
[Header Format]).
** ''fnum'' -- the field number, counting automatically from 1 as FieldInfo are appended
to a FieldSchema.

* DatatypeHandler -- this supports many basic datatypes, which can be specified
for particular fields via `FieldSchema`. Parsed values can then be tested and
cast as appropriate. The class also has `autoType()`, which will cast a value
to the most specific type it fits (for example, "9" to int, but "9.1" to float).
You can set `reserved` to a Dict, which `autoType()` will search for the
string value that was parsed (minus whitespace). If it is found, the value
from the dict is returned. Otherwise `autoType()` will go on to try other types.

===A wider range of syntax options===

Most of the *nix fielded-data utilities have little or no support for
quoted fields or escaped characters. No two (afaict) support the same range of
delimiter conventions. The Python ''csv' library is stronger, but still lacks
syntax support such as:

* Delimiters
** Multi-character delimiters
** Ignoring repeated delimiters (`delimiterrepeat`) (like `sed`)
** Delimiters used in alternation (`delimitercycle`) (like `paste -d`) (Experimental)

* Quoting
** Multiple alternative quote characterss (for example, single and double)
** Unicode quote characters (curly, angle, etc.)
** Distinct open and close quotechars
** Quoted fields that can include newlines (`quotednewline`)
I dislike this usage, but Python `csv`, RFC 4180, and some spreadsheetss use it.
(Experimental)

* Escaping and special characters
** The common letter-escapes (\\t, \\n, \\r, \\t, \\a (BEL), \\e (ESC))
** Hex escapes like \\xFF (`xescapes`)
** Wide hex escape like \\uFFFF and \\U0001FFFF (`uescapes`)
** HTML/XML character references like &#xFFF;, &#999;, &bull;, etc. (`entities`)

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
    autotype:bool = False
    comment:str = None
    delimitercycle:bool = False
    delimiterrepeat:bool = False
    encoding:str = "utf-8"
    entities:bool = False
    header:bool = False
    maxsplit:int = None
    minsplit:int = 0
    quotednewline:bool = False
    skipfinalspace:bool = False
    uescapes:bool = False
    xescapes:bool = False

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

Python csv does NONNUMERIC by type, so still quotes digit-strings. See [#To do].

* ''skipinitialspace'':bool = False -- If set, records (not fields)
have any initial (Unicode) whitespace stripped before parsing.

* ''strict'':bool = False -- If set, problems raise `ValueError`
instead of being worked around or ignored.

===Additional options===

The following options are not available in Python's `csv` package:

* ''autotype'' = False -- If set, fields with no overriding type declared (via
a header record, '--ifields', or the API)
are examined and cast to the
most specific type they can (from the type supported in header declarations).
Booleans are not attempted (for more information see section [autoTyping]).

* ''comment'':str = None -- If set and not '', lines starting with
this string are treated as comments rather than data. Leading space is NOT
allowed before the delimiter (this might be added).

* ''delimitercycle'':bool = False -- If set, and there are multiple delimiters
specified, use those delimiters in alternation like 'paste -d'.
This is not yet supported, and is not expected to be happy with named
multi-delimiter sets such as BOTH and ALL.

* ''delimiterrepeat'':bool = False -- If set, multiple adjacent delimiters do
NOT result in empty fields, but are treated the same as a single delimiter.
This would typically be done when the delimiter is just a space (which can also
be accomplished with (so far experimental) regex delimiters.
Empty fields can, however, be inserted by quoting them (because the delimiters
on each side are no longer "adjacent"). This option should probably not be
used in combination with a list of delimiters (see 'delimitercycle').

* ''encoding'' = "utf-8" -- what encoding to use. This affects escaping.

* ''entities'':bool = False -- If set, character references are recognized
and replaced as in HTML. Decimal (&#8226;), hexadecimal (&#x2022;), and the
ubiquitous named forms (&bull; etc.) are all supported.
NOTE: These are converted via Python's `html.unescape()` method, which does not
raise an error for unknown entities such as `&foo;`. References do not have to
be inside quotes.

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

* ''skipfinalspace'':bool = False -- If set, records (not fields)
have any trailing (Unicode) whitespace stripped before parsing.

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
    myFlag:bool       "1" or "0" (see below to use other values like T or F)
    age:int           decimal integer
    cookie:xint       hexadecimal integer
    perm:oint         octal integer
    quant:anyint      accepts octal, decimal, or hex
    balance:float     floating-point number
    root:complex      python notation
    lastName:str      string (this doesn't do much).
    dob:date          date (ISO 8601)

Other types will likely be added
(see https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes).

Defaults can be given after an "=", or "!" may be used to indicate
that a non-empty value is ''required''
(default values can contain quotes or delimiters only if escaped the same way as
other data in the file):
    obsolete:bool=0
    payGrade:float!

A ''normalizer'' name can be specified immediately after the type name,
separated by "|". Underneath, a normalizer is a function that takes the
field value (after unescaping and unquoting if applicable), and returns a
string (or raises an error on failure). They can be used for
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
    TF -- fields beginning with [TtYy] go to 1, [FfNn] go to 0 (if the field is
declared type bool, those will then be recognized and cast to True and False.
    ASCII -- non-ASCII characters to \\x, \\u, \\x{} escapes

A value ''constraint'' can also be included in [] immediately after the datatype
and normalizer name. The forms of constraints are type-specific:

* bool: Not currently applicable. A possible
future addition is to give the actual strings to be used for False and True,
since practice for these varies so much.
* int: the constraint can have 2 (possibly-signed) decimal integers, separated
by a comma, that are the minimum and maximum values allowed. These values
are inclusive bounds. The first defaults to 0, the second to the parsing
system's preferred maximum unsgigned integer value (sometimes 2**63 - 1).
* float: similar to those for int, but the minimum and maximum values are floats
(as always, be careful about roundoff errors). These values are inclusive bounds.
* complex: Not currently applicable.
* str: the constraint is a (Python-style) regular expression that each value
must match in its entirety. Such constraints commonly require escaping.
These constraints can be used to implement other things, such as enums:
    compass:str[N|E|W|S|NE|NW|SE|SW]=N
    province:str[NL|PE|NS|NB|QC|ON|MB|SK|AB|BC|YT|NT|NU]!
  or length limits:
    middleInitial:str[.{0,1}]

''Note'': regex constraints regard case.
TODO: Fix this, perhaps by adding a prefix flag, or \\L \\U, or....

When a ''type'' is specified, raw field values are cast to that type
for return (for example, by reader() and DictReader()).
When a field is empty and a default value
was set, the default value is cast to the specified type and returned.
Fields with no type hint in the header default to type 'str'.
Fields with no default set in the header get "" when omitted (which may then
be cast as needed for the datatype, for example to 0).

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

A field for which no type is set is returned as a literal string unless
'autotype' is turned on (see next section).

===autoTyping===

If `autotype` is set on the DialextX, then any field which does not have an explicit
type set (via header, options, or API as described above), is passed to
a function which tries to cast it to an appropriate type.

This has potential problems. Some data uses "1" and "0" for booleans, which
could also be ints (or perhaps floats). Other data might use reserved
words such as "True", "T", or "#T",
which could of course be strings.
Because of this, autotyping never decides something is a boolean.
Similarly, any int could also be a float. Anything at all could be a string.

Leading and trailing whitespace is stripped before testing types.
However, items that remain as strings are returned with the whitespace intact
(unless the `skipinitialspace` or `skipfinalspace` option is also set).

If `reserved` is supplied, it must a dict of what to return for any special
values -- say, "--" for NaN, "#T" for True, or "999" for None, etc.

If `specialFloats` is set, then the strings "NaN", "inf", "-inf", and "+inf"
(all case-sensitive) are recognized as floats (otherwise they are strings).
TODO: -0 should also be distinguished in this case.

Complex numbers must be of the Python form "1+1j".

Numbers are taken as ints if, after space stripping, they contain Latin decimal
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
the given type (which may fail). Remember that Python `bool()`
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

=References=

Johann Mitlohner, et al. "Characteristics of Open Data CSV Files"
[https://www.researchgate.net/profile/Sebastian-Neumaier/publication/308568784_Characteristics_of_Open_Data_CSV_Files/links/6217490eb85f8c427cd62502/Characteristics-of-Open-Data-CSV-Files.pdf]

=Known bugs and Limitations=

Smoke tests for multi-character delimiters are failing.
Not sure whether you can (or should be able to) escape in mid-delimiter.
You cannot combine delimiterrepeat and delimitercycle.

Field names passed to DictReader, or from --ifields,
should probably be allowed to override any
read from a header record. But currently they're compared and an exception
is raised if they don't match. TODO: Check if still true.

'--convert' does not copy comment lines, even if an output dialect command
marker is specified. How best to return comments during parsing?

'escapechar' is recognized both inside and outside of quotes.

'escapechar' at end of line does not make the newline into data (but see
'quotednewline').

Unknown escapes such as \\q just mean the literal character, and no error
is issued even with strict=True. However, syntax errors within \\x \\u and \\U
are reported, and cause in exception if strict=True. The dict listing
known escapes (other than [xuU] is Escaping.escape2char. It can be modified, though
success is not guaranteed especially if you add entries that collide with
other special characters, such as quotes, delimiters, etc.

What's the right rule for a quote not immediately following a delimiter?
As in
    1, "two", 3, 4"five"5, 6

Date and time processing is not supported for dates prior to the Gregorian
calendar change (October 1582). However, it will likely behave correctly
assuming the [[proleptic Gregorian calendar]].

timedelta assumes a year is 365.2425 days (the Gregorian average), and a
month is 30 days.


=To do=

* Add a QUOTING option like NONNUMERIC, but that treats strings of digits
as numerics, rather than going by type.

* Add a convention for putting metasyntax in first record. Maybe like below
(though what is ok for escaping in values?
    #CSVPP: (optname=value)+

* Add smoke tests for datetimes, autotype, quotednewline, normalizers,
constraints, complex headers.

* Lose remaining refs to args from inside classes.

* Way to distinguish only-precise-to-the-hour from on-the-hour, etc.

* Per RC4081 complain about rec-final delimiter if not quoted.

* Delimiter as "whitespace to nonspace transition" (like awk, column, sort).

* Some kind of hysteresis for autotyping? Like, if this field has always been int
and we see "", make it 0; if always float and we see 12, make it 12.0.

* Option to create NamedTuple or tuple instead of list or dict?

* Add a way to get at the last raw record (since reader() parses it),
and the logical/physical record numbers.

* Should regex constraints be enclosed not by {}, but by // or by any \\W?

* Should csv skipinitialspace/skipfinalspace be overridable per-field?
Maybe something more for Unicode spaces, esp. hard-space per se?

* Add predefined dialects: RFC4081, Excel, and any that Python `csv` provides.
Also eponymous ones for each relevant *nix command?

* Make sure it can just take a csv.Dialect for the DialectX arguments.

* Support for a wider range of formats (probably via separate
packages or subclasses with much the same API), such as:
    ** HTML and XML tables (but see my `htmlTable2csv.py`.
    ** MediaWiki and MarkDown tables (but see my `markdown2Xml.py`).
    ** XSV (but see my xsv2others.py).
    ** JSON cases (but see my `json2xml.py`).
    ** s-expressions and perhaps CONLL (but see my `sexp2xml`).
    ** SQL INSERT statements
    ** Tables extracted straight from a SQL API
    ** Fixed column widths, maybe via scanf?

* Way to change the set of backslash codes, such as \\b for BEL, etc.?

* Perhaps support Python \\N{unicode-name}?

* Add way to control case treatment of string constraints (and how does
constraint relate to normalization?)

* Allow years >9999, etc. See https://www.w3.org/TR/xmlschema-2/#isoformats
Don't forget leap seconds.

* Sync regex constraints w/ auto-anchored XSD approach.

* Support XSD regex \\#x and \\p{prop}?


=History=

Written by Steven J. DeRose, 2020-02-28.

* 2020-08-07: Add classes and API to look essentially like Python `csv`,
including `DictReader` and `DictWriter`.
Separate options into a "Dialect" class, add `add_my_arguments`.
Start `multidelimiter` (later renamed `delimiterrepeat`).
Add `comment`. Rewrite doc.

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
Add parseHeaderStrToSchema(), handling of type hints and defaults, open/close
quote support. Add cleanField() to do strip, unquote, unescape, entities,
normalization, etc. Start main beyond basic smoke-test.
Add --convert vs. prettyprinting. Reorg quote pairs and
option defaulting. Add --showQuotes and --showDialectX. Refactor
reader() and writer() to be like csv ones (generator classes).
Ditch 'typelist'. Add DictWriterXSV, SAXReader.
Rename `multidelimiter` to `delimiterrepeat`, 'cycle' to 'delimitercycle'.
Add support for regex delimiters. Factor out class `Escaping`.


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
class Escaping:
    """Manage encoding/decoding of special characters as backslash of other
    escapes, entities, etc. Indiovidual cases are supported by Python built-ins,
    but we need to be switchable to lots of combinations, including weird ones
    the show up in legacy or quirky data.
    Beware of regex and other escapes, like \\L \\U \\s \\d \\w
    """
    escape2char = {
        "0":     "\x00",  # U+00 null  # WARNING: Collides with \\0777 octal
        #"a":     "\x07",  # U+07 bell
        #"b":     "\x08",  # U+08 backspace
        "t":     "\x09",  # U+09 tab
        "n":     "\x0A",  # U+0A line feed
        "v":     "\x0B",  # U+0B vertical tab
        "f":     "\x0C",  # U+0C form feed
        "r":     "\x0D",  # U+0D carriage return
        "e" :    "\x1B",  # U+1B escape
        "\\":    "\x5C",  # U+5C backslash
    }

    char2escape = {
        "\x00":  "\\0",  # U+00 null
        "\x07":  "\\a",  # U+07 bell
        #"\x08":  "\\b",  # U+08 backspace
        "\x09":  "\\t",  # U+09 tab
        "\x0A":  "\\n",  # U+0A line feed
        #"\x0B":  "\\v",  # U+0B vertical tab
        "\x0C":  "\\f",  # U+0C form feed
        "\x0D":  "\\r",  # U+0D carriage return
        "\x1B":  "\\e",  # U+1B escape
        "\x5C":  "\\\\", # U+5C backslash
    }
    def __init__(self):
        assert False, "Don't instantiate static class 'Escaping'."

    @staticmethod
    def decodeEscape(s:str, i:int, lastToken:str, dx:'DialectX') -> (str, int):
        """Having found an escapechar at offset 'i', parse and return
            * what the following sequence represents, and
            * the length to be consumed (incl. the escapechar).
        """
        if (i+1 >= len(s)):
            syntaxError(s, i, lastToken, "escape at end of line", strict=dx.strict)
            return "", 1
        c1 = s[i+1]
        if (c1 == "x"):
            lg.info("got xescape at %s", s[i:])
            if (not dx.xescapes):
                syntaxError(s, i, lastToken,
                    "\\x escape but option is off", strict=dx.strict)
                return ("\\x", 2)
            mat = re.match(r"x([\da-f]{2})|x\{([\da-f]+)\}", s[i:])
            if (not mat):
                syntaxError(s, i, lastToken,
                    "Incomplete \\x escape", strict=dx.strict)
                codePoint = None
                escValue = dx.escapechar + "x"
                escLength = 2
            elif (mat.group(1)):
                codePoint = int(mat.group(1), 16)
                escValue = chr(codePoint)
                escLength = 4
            else:
                codePoint = int(mat.group(2), 16)
                escValue = chr(codePoint)
                escLength = len(mat.group(2)) + 4
            if (codePoint and codePoint > sys.maxunicode):
                syntaxError(s, i, lastToken, "\\x outside Unicode range (%x)."
                    % (codePoint), strict=dx.strict)
                escValue = dx.escapechar + "x"
                escLength = 2

        elif (c1 in "Uu"):
            lg.info("got uescape at %s", s[i:])
            if (not dx.uescapes):
                syntaxError(s, i, lastToken,
                    "\\%s escape but option is off" % (c1), strict=dx.strict)
                return ("\\" + c1, 2)
            if (c1 == "u"):
                mat = re.match(r"u[\da-f]{4}", s[i:])
                if (not mat):
                    syntaxError(s, i, lastToken,
                        "Incomplete \\u escape", strict=dx.strict)
                    escValue = dx.escapechar + "u"
                escValue = chr(int(s[i+1:i+5], 16))
                escLength = 5
            elif (c1 == "U"):
                mat = re.match(r"U[\da-f]{8}", s[i:])
                if (not mat):
                    syntaxError(s, i, lastToken,
                        "Incomplete \\U escape", strict=dx.strict)
                    escValue = dx.escapechar + "U"
                else:
                    escValue = chr(int(s[i+1:i+9], 16))
                    escLength = 9

        else:
            lg.info("got  char escape at %s", s[i:])
            escValue, escLength = Escaping.unescapeViaMap(c1, i, strict=dx.strict)

        return escValue, escLength

    @staticmethod
    def unescapeViaMap(c: str, i=int, strict:bool=False) -> (str, int):
        """If it wasn't some special/long escape like \\x \\u \\U, look up the
        escaped char and return what it means, or just itself.
        Also return the length (currently always 2, but needn't be).
        """
        if (c in Escaping.escape2char): return Escaping.escape2char[c], 2
        if (strict):  # TODO Maybe this is never an error?
            syntaxError(c, i, "", "Unrecognized escape \\%s" % (c), strict=strict)
        return c, 2

    # TODO Sync with regular 'csv' package
    @staticmethod
    def escapeOneChar(dx:'DialectX', c:Union[str, re.Match]) -> str:
        """Can be used on a raw character or an re.Match object with the
        desired character in the 1st capture. Always recodes the character
        somehow (or fails), so only call it when needed (see getProblemChars()).
        """
        if (isinstance(c, re.Match)):
            c = c.group(1)
        assert c in dx.problemChars

        if (c == dx.escapechar):
            return c+c
        if (c == dx.quotechar):
            if (dx.quoting): return c  # Caller must do the quoting! TODO Check
            if (dx.doublequote): return c+c
            elif (dx.entities): return dx.entify(c)
            elif (dx.escapechar): return dx.escapechar + c
            else: return dx.hexify(c)
        if (dx.entities and c in "&<"):  # TODO: Ewww, quote for in attrs.
            # ">" doesn't normally need quoting (see "]]>")
            return dx.entify(c)

        # TODO syntaxError()?
        return c

    @staticmethod
    def entify(c:str, useNames:bool=True) -> str:
        """Many options here -- like an order of preference among
        named/hex/decimal XML character refs.
        """
        n = ord(c)
        if (useNames and n in html.entities.codepoint2name):
            return "&%s;" % (html.entities.codepoint2name[n])
        if (n > 0xFF): return "&#X%04x;" % (n)
        return "&#X%02x;" % (n)

    @staticmethod
    def hexify(c:str) -> str:
        """TODO If not escapechar and xescapes and uescapes, what then?
        """
        n = ord(c)
        if (n <= 0xFF):
            return "\\x%02x" % (n)
        if (n <= 0xFFFF):
            return "\\u%04x" % (n)
        return "\\U%08x" % (n)

    @staticmethod
    def escapeXmlAttribute(s:str, attrQuoteChar:str='"') -> str:
        """Escape as needed for quoted attributes (default: double-quoted).
        Quietly deletes any non-XML control characters!
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = s.replace(r"&",  "&amp;")
        s = s.replace(r"<",  "&lt;")
        if (attrQuoteChar == '"'): s = s.replace(r'"', "&quot;")
        else: s = s.replace(r"'", "&apos;")
        return(s)

    @staticmethod
    def escapeXmlComment(s:str) -> str:
        """Escape as needed for comment.
        XML doesn't define a standard escaping for this, so I chose one.
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = s.replace(r"--", "\u2014")
        return(s)

    @staticmethod
    def escapeSpecial(c:str) -> str:
        """Turn a special character into an escaped letter.
        """
        if (c in Escaping.char2escape): return Escaping.char2escape[c]


###############################################################################
#
# These are the same values as in Python's csv package
class QUOTING(Enum):
    MINIMAL       = 0  # only quote if needed.
    ALL           = 1  # quote all fields.
    NONNUMERIC    = 2  # quote all non-numeric fields.
    NONE          = 3  # never quote fields, but use escapechar if defined

    @staticmethod
    def fromstring(s:str, default:"Quoting"=0):
        try:
            return QUOTING.__members__[s]
        except KeyError:
            return default

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
    Each of the types below can occur as a singleton, or as a list (in which case
    the items are used round-robin).
    """
    NIL           = 0  # The empty string (= split each character)
    CHAR          = 1  # The typical single-char, like TAB or comma
    STR           = 2  # A multi-char delimiter
    SPACES        = 3  # Space / non-space change, sort of like \b
    REGEX         = 4  # A regex to match

#POINTING_CHAR = "\u261e"  # Pointing finger
POINTING_CHAR = "\u23E9"  # Double arrow button

class DialectX:
    """Mainly a bundle of settings.
    """
    __OptionTypes__ = {
        "delimiter":        Union[str, List, re.Pattern],
        "doublequote":      bool,
        "escapechar":       str,
        "lineterminator":   str,
        "quotechar":        str,
        "quoting":          QUOTING,
        "skipinitialspace": bool,
        "strict":           bool,

        # fsplit only:
        "comment":          str,
        "delimitercycle":   bool,
        "encoding":         str,
        "entities":         bool,
        "header":           bool,
        "delimiterrepeat":  bool,  # Cf *nix *paste -d*
        "maxsplit":         int,
        "minsplit":         int,
        "skipfinalspace":   bool,
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

        #lg.info("Default options:\n" + self.tostring())
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
        self.autotype          = False  # bool
        self.comment           = None   # str
        self.delimitercycle    = False  # bool
        self.delimiterrepeat   = False  # bool
        self.encoding          = "utf-8"# str
        self.entities          = False  # bool
        self.header            = False  # bool
        self.maxsplit          = 0      # int
        self.minsplit          = 0      # int
        self.quotednewline     = False  # bool
        self.skipfinalspace    = False  # bool
        self.uescapes          = False  # bool
        self.xescapes          = False  # bool

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
                    raise ValueError(
                        "Unrecognized value '%s' for quoting." % (v)) from e
            typ = self.__OptionTypes__[k]
            if (v is None or isinstance(v, typ)):
                setattr(self, k, v)
            else:
                raise ValueError("Option '%s' has bad value '%s', needs %s."
                    % (k, v, typ))

    def checkOptions(self, strict:bool=False) -> None:
        errs = []

        if (isinstance(self.delimiter, str)):
            if (not self.delimiter or
                self.delimiter == self.escapechar or
                self.delimiter == self.quotechar):
                errs.append("Delimiter empty of conflicting.")
        elif (isinstance(self.delimiter, List)):
            if (not self.delimitercycle):
                errs.append("Delimiter is a list but delimitercycle not set.")
        elif (isinstance(self.delimiter, re.Pattern)):
            if (self.delimitercycle):
                errs.append("Delimiter is a regex but delimitercycle is set.")
        else:
            errs.append("Delimiter is not a list or str or re.Pattern.")
        if (self.delimiterrepeat and self.delimitercycle):
            errs.append("Cannot combine delimiterrepeat and delimitercycle.")

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
        if (self.doublequote and self.escapechar):
            errs.append("Cannot combine doublequote and escapechar.")  # TODO ???

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
            choices=[ "ALL", "MINIMAL", "NONNUMERIC", "NONE"],  # Add NONNUMLIKE
            help="When should fields be quoted?.")
        parser.add_argument(
            pre+"skipinitialspace", action="store_true",
            help="Remove leading space/indentation from records.")
        parser.add_argument(
            pre+"strict", action="store_true",
            help="Raise exception on syntax error.")

        if (csvOnly): return

        # Extended options
        parser.add_argument(
            pre+"autotype", action="store_true",
            help="Try to identify and auto-case fields to datatypes.")
        parser.add_argument(
            pre+"comment", type=str, default=None, metavar="S",
            help="Treat records starting with this string as comments, not data.")
        parser.add_argument(
            pre+"delimitercycle", action="store_true",
            help="Cycle' through multiple delimiters, like `paste -d` (not yet).")
        parser.add_argument(
            pre+"delimiterrepeat", action="store_true",
            help="Treat multiple adjacent delimiters (e.g. space), as just one.")
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
            pre+"quotednewline", action="store_true",
            help="Allow newlines as data within quoted fields.")
        parser.add_argument(
            pre+"skipfinalspace", action="store_true",
            help="Remove trailing space from records.")
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
            if (k == "quoting" and not isinstance(theArgs.__dict__[k], QUOTING)):
                theArgs.__dict__[k] = QUOTING.fromstring(theArgs.__dict__[k])
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
            delimiter, delimitercycle, delimiterrepeat,
            quotechar, doublequote, quotednewline, lineterminator,
            escapechar, uescapes, xescapes, entities, encoding.
        TODO: What about booleans, etc.?
        """
        if (v is None): v = ""
        else: s = str(v)
        if (asciiOnly):
            buf = re.sub(r"([^!-~])", Escaping.escapeOneChar, s, flags=re.U)
        else:
            buf = re.sub(
                r"([" + self.problemChars + "])",
                Escaping.escapeOneChar,
                s,
                flags=re.U
            )
        return buf

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
        # encoding?


###############################################################################
#
predefinedDialects = {}

__RFC4180__ = DialectX(
    "__RFC4180__",
    delimiter            = ",",     # Field separator(s), str or list
    doublequote          = True,    # TODO Support ""
    escapechar           = None,    # Backslashing?
    lineterminator       = "\n",    # What's the line-break?
    quotechar            = '"',     # What's the quote mark?
    quoting              = QUOTING.NONNUMERIC,  # What to quote
    skipinitialspace     = False,   # Strip leading spaces
    skipfinalspace       = False,   # Strip trailing spaces
    strict               = False,

    autotype             = False,   # Attempt automatic datatyping
    header               = False,   # Is there a header record?
    comment              = None,    # Marker for comment lines
    delimitercycle       = False,
    delimiterrepeat      = False,   # Ignore repeated delimiters?
    entities             = False,
    maxsplit             = None,    # Limit to this many fields
    minsplit             = None,    # Scream if < this many fields
    quotednewline        = False,   # Allow multiline quoted values
    xescapes             = False,   # Interpret \xFF
    uescapes             = False,   # Interpret \uFFFF
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
# TODO: Combine with casters?
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
    "XSP":      lambda s: re.sub(r"[ \t\r\n]+", " ", s.strip()),
    "USP":      lambda s: re.sub(r"\s+", " ", s.strip()),
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
                    if (self.restkey not in fieldDict):
                        fieldDict[self.restkey] = str(fd)
                    else:
                        fieldDict[self.restkey] += str(fd)
            if (len(self.fieldNames) > len(fields) and self.restval is not None):
                # TODO: Apply schema defaults if available
                for i in range(len(fields), len(self.fieldNames)):
                    fieldDict[self.fieldNames[i]] = self.restval
            yield fieldDict
        return None  # EOF

    # What's a legit field name to use?
    dftNameExpr:Final = r"^\w([-.$\w ]*)$"

    from pydoc import locate  # see https://stackoverflow.com/questions/11775460/

    # TODO: Move into FieldSchema
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
            raise ValueError("Header does not match expected fields:\n    %s\n    %s"
                % (str(self.fieldNames), str(self.fieldNames)))
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
        However, there is an experimental FieldInfo.addType().

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
            raise ValueError("Cannot parse header item: <<<%s>>>" % (hfield))
        else:
            fname = mat.groups(1) or ""  ####### TODO FIX!!!!
            fnorm = mat.groups(3) or ""
            ftype = mat.groups(4) or ""
            fcons = mat.groups(5) or ""
            fdflt = mat.groups(6) or ""
            lg.info("FInfo fname %s, fnorm %s, ftype %s, fcons %s, fdflt %s, freqd %s.",
                fname, fnorm, ftype, fcons, fdflt, freqd)

            if (fcons):
                fcons = fcons.upper()
                if (fcons not in NamedNormalizers):
                    if (self.dialect.strict):
                        raise ValueError("Could not find normalizer '%s'." % (fcons))
                    ftype = ""

            if (ftype):
                if (fcons):
                    ftype = ftype[0:-len(fcons)]
                if (ftype not in dtHandler.KnownTypes):
                    if (self.dialect.strict):
                        raise ValueError("Could not locate type '%s'." % (ftype))
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
    See isFieldValueOfType(), etc. for that kind of stuff...
    """
    assert dialect
    s = s.rstrip()
    if dialect.skipinitialspace: s = s.lstrip()
    if dialect.skipfinalspace: s = s.rstrip()

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
        # TODO: Lose this assertion
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
                    lg.info("Continued rec %d (%d):\n    %s",
                        self.rec_num, nPhysical, e)
                    continue  ### Go around for continuation line

            self.rec_num += 1
            if (nPhysical > 1):
                lg.info("Logical record included %d physical records.", nPhysical)

            # If this was the header, handle it and go around again for data.
            if (self.rec_num==1):
                if (self.dialect.header):
                    lg.info("read header logical rec as: <<<%s>>>", self.lrec)
                    self.schema = ensureSchema(
                        self.schema, firstRec=self.lrec,
                        dialect=self.dialect, fsArg=args.ifields)  # TODO -args
                    self.fieldNames = self.schema.getFieldNames()
                    continue  # Go around for first data record
                else:
                    self.schema = ensureSchema(
                        None, firstRec=self.lrec,
                        dialect=self.dialect, fsArg=args.ifields)  # TODO -args
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
        self.dialect      = None
        if (dialect in predefinedDialects):
            self.dialect  = predefinedDialects[dialect]
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

    def writerow(self, row: Dict) -> None:
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

    def writerow(self, row: Dict) -> None:
        buf = ""
        if (self.fieldNames is None):
            self.fieldNames = sorted(row.keys())

        for fname in self.fieldNames:
            if (fname not in row):  continue  # TODO restval?
            fval = str(row[fname])            # TODO format?
            buf += self.makeAttr(fname, fval)
        self.f.write("<Rec%s />\n" % (buf))

    def writecomment(self, s: str):
        self.f.write("<!--%s-->" % (Escaping.escapeXmlComment(s)))

    def writetrailer(self):
        self.f.write("</Table>\n</Xsv>\n")

    @staticmethod
    def makeAttr(k:str, v:Any):
        return ' %s="%s"' % (k, Escaping.escapeXmlAttribute(v))


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
    """Read CSV and pass back as if it was XML. Always has a Table and a Record
    element; field names/values can be organized in several ways (see FStyle).
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
            self.callBacks[SAXEvent.Element](self.names["Table"], "(%s)+" % (
                self.names["Table"]))
            for fi in self.schema:
                # Map types more specifically than #CDATA
                self.callBacks[SAXEvent.Attlist](
                    fi.fname, "CDATA", fi.fdefault or '""')
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
UQuotePairs = {  # From my Charsets/UnicodeLists/quote.py.
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

def dquote(s: str, showControls:bool=False) -> str:
    """Put double angle quotes around a string for display,
    and optionally make control chars visible.
    """
    if (showControls):
        s = re.sub(r"([\x00-\x20])",
            lambda m: chr(0x2400 + ord(m.group(1))), s)
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
    #lg.info("Match against '%s':\n%s" % (s, mat))
    if (not mat): return None, 0
    result = unescape(mat.group(0))
    return result, len(mat.group(0))


###############################################################################
#
DTDef = namedtuple("DTDef",
    ( "targetDT", "caster", "constrainer", "XSDName" ))

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
    uuidExpr = r"[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$"

    #identExpr = r"^\w+$"

    @staticmethod
    def addType(hintName:str, theType:type, caster:Callable=None):
        """Add a type to the list of known ones, so it is recognized
        as a type-hint in the header (or equivalent).
        TODO: Maybe allow dropping types, too?
        """
        assert hintName not in dtHandler.KnownTypes
        assert isinstance(theType, type)
        assert isinstance(caster, Callable)
        dtHandler.KnownTypes[hintName] = ( theType, -len(dtHandler.KnownTypes, caster) )

    # Python recognizes these ignoring case
    reservedFloats = [ "nan", "inf", "-inf", "+inf", "-0" ]

    def __init__(self,
        reserved: Dict=None,
        specialFloats: bool=False
        ):
        """
        @specialfloats:
            If set, "NaN" and (optionally signed) "inf" count as floats.
        """
        self.setupDefaultTypes()
        self.reserved = reserved
        self.specialFloats = specialFloats

    def setupDefaultTypes(self):
        """Define the types that can be used in header hints.
        Besides an upper-case name, they each get a target type,
        a function to cast a string to that type, and maybe
        a function to test constraints (TODO: unfinished).
        This is just for CSV fields, so no aggregates/collections/etc.
        Largely based on Python and XSD Datatypes (cf Datatypes.py and
        https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes.

        """
        DT = datetime.datetime
        NOCON = None
        self.KnownTypes = {
            # hint name:  DTDef(targetDT, caster,    constrainer,   XSDName )
            "BOOL":       DTDef(bool,     None,            NOCON,   "boolean"),

            "INT":        DTDef(int, lambda x: int(x, 10), NOCON,   "integer"),
            "XINT":       DTDef(int, lambda x: int(x, 16), NOCON,   None),
            "OINT":       DTDef(int, lambda x: int(x, 8),  NOCON,   None),
            "ANYINT":     DTDef(int, lambda x: int(x, 0),  NOCON,   None),

            "FLOAT":      DTDef(float, float,              NOCON,   "float"),
            "PROB":       DTDef(float, complex,            NOCON,   None),

            "COMPLEX":    DTDef(complex, complex,          NOCON,   None),

            "ARRAY":      DTDef(array.array, self.parseVector, NOCON, None),
            # TODO: int vs. float vs. complex? tensor? size?

            "DATETIME":   DTDef(dt, DT.fromisoformat,      NOCON,   "dateTime"),
            "DATE":       DTDef(datetime.date,
                lambda x: DT.strptime(x, "%Y-%m-%d"),      NOCON,   "date"),
            "USDATE":     DTDef(dt,
                lambda x: DT.strptime(x, "%m/%d/%Y"),      NOCON,   None),
            "EUDATE":     DTDef(datetime.date,
                lambda x: DT.strptime(x, "%d/%m/%Y"),      NOCON,   None),
            "TIME":       DTDef(datetime.time, datetime.time, NOCON, "time"),
            # TODO: XSD gYearMonth, gYear, gMonthDay, gDay,gMonth
            "EPOCH":      DTDef(dt, datetime.date.fromtimestamp, NOCON, None),
            "TIMEDELTA":  DTDef(datetime.timedelta,
                lambda x: self.parseISOTimeDelta,          NOCON,   "duration"),
            # YEAR MONTH DAY JULIAN HOUR MIN SEC OFFSET
            "STR":        DTDef(str, str,                  NOCON,   "string"),
            "IDENT":      DTDef(str, str,                  NOCON,   "NCName"),
            # TODO? XSD NOTATION
            "URI":        DTDef(str, str,                  NOCON,   "anyURI"),
            "UUID":       DTDef(uuid.UUID,
                lambda x: uuid.UUID(hex=x),                NOCON,   None),
        }

    # TODO: XSD Derived datatypes (https://www.w3.org/TR/xmlschema-2/#built-in-derived)
    # normalizedString, token, language,
    # NMTOKEN, NMTOKENS, Name, NCName, ID, IDREF, IDREFS, ENTITY, ENTITIES,
    # int, long, int, short, byte,
    # ?? nonNegativeInteger, positiveInteger, nonPositiveInteger, negativeInteger,
    # ?? unsignedLong, unsignedInt, unsignedShort, unsignedByte,

    def isFieldValueOfType(self, val: Any, typeName:str) -> bool:
        """Determine whether a given field as a string, fits the datatype.
        Does NOT also check constraints or if required (so None or ""
        return False. Caller must reverse if field is options.
        Actual normalizing, typecasting, etc. happen under handleRecord().
        """
        if (isinstance(typeName, type)):
            typeName = typeName.__name__
        typeDef = self.KnownTypes[typeName]

        if (val is None): return True

        try:
            castVal = typeDef.caster(val)
        except ValueError:
            return False

        assert isinstance(castVal, typeDef.targetDT)
        return True

    def castToType(self, typeName:str, val:Any) -> Any:
        """Take a raw string field value and cast it to the hinted type name.
        (for that field). If it's already not a string, cast it anyway.
        TODO: Is there a clean way to cast to a variable type?
        """
        if (isinstance(typeName, type)):
            typeName = typeName.__name__
        typeDef = self.KnownTypes[typeName]

        if (val is None): return None

        try:
            castVal = typeDef.caster(val)
        except ValueError:
            return False

        assert isinstance(castVal, typeDef.targetDT)
        return castVal

    def checkConstraint(self, typeName:str, castVal:Any, fInfo:'FieldInfo') -> bool:
        # TODO: Finish
        if (isinstance(typeName, type)):
            typeName = typeName.__name__
        typeDef = self.KnownTypes[typeName]

        assert isinstance(castVal, typeDef.targetDT)

        if (isinstance(castVal, int)):
            if ((fInfo.fmin and castVal < fInfo.fmin) or
                (fInfo.fmax and castVal > fInfo.fmax)):
                return False
            return True

        if (isinstance(castVal, float)):
            if ((fInfo.fmin and castVal < fInfo.fmin) or
                (fInfo.fmax and castVal > fInfo.fmax)):
                return False
            return True

        if (isinstance(castVal, complex)):
            return True

        if (isinstance(castVal, datetime.datetime)):
            ttuple = datetime.date.timetuple(castVal)
            return (ttuple[0] > 1582)

        if (isinstance(castVal, array.array)):
            # TODO: Maybe check homogeneity?
            return True

        if (isinstance(castVal, str)):
            if (fInfo.fconstraint and not re.search(fInfo.fconstraint, castVal)):
                return False
            return True

        # TODO: Add custom types?

        return False

    timedeltaExpr = r"^P(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?$"
    #                   1      2      3      4 5      6      7
    weekdeltaExpr = r"^P(\d+W)$"

    daysPerYear = 365.2425
    daysPerMonth = 30.0

    @staticmethod
    def parseVector(s:str) -> array.array:
        s2 = s.lstrip(" \t\r\n\f[").rstrip(" \t\r\n\f]")
        return array.array(re.split(r"\s*,\s*", s2))

    @staticmethod
    def stripBrackets(s:str) -> str:
        s = DatatypeHandler.stripSpace(s)
        if (len(s) < 2): return s
        x = s[0] + s[-1]
        if (x in [ "[]", "{}", "()" ]): return x[1:-2]
        return s

    # From my Charsets/UnicodeLists/whitespace.py
    #
    USpaces = "".join(
        "\u0009"  # "CHARACTER TABULATION"         # Not in class Z
        "\u000A"  # "LINE FEED"                    # Not in class Z
        "\u000B"  # "LINE TABULATION"              # Not in class Z
        "\u000C"  # "FORM FEED"                    # Not in class Z
        "\u000D"  # "CARRIAGE RETURN"              # Not in class Z
        "\u0020"  # "SPACE"
        ### WARNING: In CP1252, 0x89 is PER MILLE SIGN (-> U+2030)
        "\u0089"  # "CHARACTER TABULATION WITH JUSTIFICATION"  # Not in class Z
        "\u1680"  # "OGHAM SPACE MARK"
        #"\u180E"  # "MONGOLIAN VOWEL SEPARATOR"    # Not in class Z
        "\u2000"  # "EN QUAD"
        "\u2001"  # "EM QUAD"
        "\u2002"  # "EN SPACE"
        "\u2003"  # "EM SPACE"
        "\u2004"  # "THREE-PER-EM SPACE"
        "\u2005"  # "FOUR-PER-EM SPACE"
        "\u2006"  # "SIX-PER-EM SPACE"
        "\u2007"  # "FIGURE SPACE"
        "\u2008"  # "PUNCTUATION SPACE"
        "\u2009"  # "THIN SPACE"
        "\u200A"  # "HAIR SPACE"
        "\u2028"  # "LINE SEPARATOR"
        "\u2029"  # "PARAGRAPH SEPARATOR"
        "\u200B"  # "ZERO WIDTH SPACE"
        "\u202F"  # "NARROW NO-BREAK SPACE"
        "\u205F"  # "MEDIUM MATHEMATICAL SPACE"
        "\u2060"  # "WORD JOINER"                  # Not in class Z
        "\u3000"  # "IDEOGRAPHIC SPACE"
        "\u303F"  # "IDEOGRAPHIC HALF FILL SPACE"  # Not in class Z
        "\uFeFF"  # "ZERO WIDTH NO-BREAK SPACE"    # aka BOM
        #"\u00A0"  # "NO-BREAK SPACE"

        # These aren't really "spaces", but symbols for them (class So).
        #"\u2420"  # "SYMBOL FOR SPACE"
        #"\u2408"  # "SYMBOL FOR BACKSPACE"
        #"\u2409"  # "SYMBOL FOR HORIZONTAL TABULATION"
        #"\u240a"  # "SYMBOL FOR LINE FEED"
        #"\u240b"  # "SYMBOL FOR VERTICAL TABULATION"
        #"\u240c"  # "SYMBOL FOR FORM FEED"
        #"\u240d"  # "SYMBOL FOR CARRIAGE RETURN"
        #"\u2422"  # "BLANK SYMBOL"
        #"\u2423"  # "OPEN BOX"
        #"\u2424"  # "SYMBOL FOR NEWLINE"
    )

    @staticmethod
    def stripSpace(s:str, method:str="XML"):
        """Remove whitespace from both sides of a string, at several
        levels of eagerness.
        """
        # Since Python's csv package takes skipinitialspace:bool, we
        # treat non-zero ints as equal to "XML".
        if (isinstance(method, int)):
            method = "XML" if method else "NONE"

        if (method == "NONE"): return s
        elif (method == "XML"): toStrip = " \t\r\n"
        elif (method == "LATIN"): toStrip = " \t\r\n\x0B\x0C\xA0"
        elif (method == "SOFT"): toStrip = DatatypeHandler.USpaces
        elif (method == "ALL"): toStrip = DatatypeHandler.USpaces + "\u00A0"
        else:
            assert False, "Unrecognized stripSpace() method '%s'." % (method)

        return s.strip(toStrip)

    @staticmethod
    def parseISOTimeDelta(s:str) -> datetime.timedelta:
        """ISO 8601 format: P[n]Y[n]M[n]DT[n]H[n]M[n]S
        """
        mat = re.match(DatatypeHandler.weekdeltaExpr, s)
        if (mat): return datetime.timedelta(weeks=int(mat.group(1)))

        mat = re.match(DatatypeHandler.timedeltaExpr, s)
        if (not mat): return None

        Y = M = D = h = m = s = 0
        if (mat.group(1)): Y = int(mat.group(1)[0:-1])
        if (mat.group(2)): M = int(mat.group(2)[0:-1])
        if (mat.group(3)): D = int(mat.group(3)[0:-1])
        if (mat.group(5)): h = int(mat.group(5)[0:-1])
        if (mat.group(6)): m = int(mat.group(6)[0:-1])
        if (mat.group(7)): s = int(mat.group(7)[0:-1])
        days = DatatypeHandler.daysPerYear*Y + DatatypeHandler.daysPerMonth*M + D
        return datetime.timedelta(days=days, hours=h, minutes=m, seconds=s)

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

    def autoType(self, tok: str) -> Any:
        """Convert a string to the most specific type we can.

        Values which (after space-stripping) exactly match entries in
        self.reserved, are returned as their value in that Dict. This is
        perhaps most useful for handling Boolean values (#T, nil, etc).

        Complex uses the Python "1+1j" (not "1+1i"!) form.
        Leading and trailing whitespace are stripped for testing, but
        not for returned string values.

        TODZO: uuidm url
        """
        if (not isinstance(tok, str)):
            return tok

        tok2 = DatatypeHandler.stripSpace(tok)

        if (tok2 in self.reserved):
            return self.reserved[tok2]
        if (tok2 == ""):
            return tok
        if (tok2.isdigit()):
            return int(tok2)
        if (self.specialFloats and
            tok2.lower() in self.reservedFloats):
            return float(tok)
        try: return self.datetimeCaster(tok2)
        except ValueError: pass
        try: return int(tok2, 0)
        except ValueError: pass
        try: return float(tok2)
        except ValueError: pass
        try: return complex(tok2)  # Test *after* float and int
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

        tok2 = DatatypeHandler.stripSpace(tok)

        if (tok2 in self.reserved):
            return self.reserved[tok2]
        if (tok2 == ""):
            return "None", None
        # Prevent "float" from catching these when not wanted:
        if (not self.specialFloats and tok2 in ("NaN", "inf", "-inf", "+inf")):
            return "str", tok2
        try: return "datetime", self.datetimeCaster(tok2)
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

    @staticmethod
    def checkTypeList(typeList: List) -> bool:
        """OBSOLETE -- check whether a list of field types is legit.
        Replaced by FieldSchema support.
        """
        if (not isinstance(typeList, list)): return False
        for i, t in enumerate(typeList):
            if (isinstance(t, type)): continue
            if (dt.isADatatype(t)): continue
            if (callable(t)): continue
            sys.stderr.write(
                "Type %d is not a Python or Datatypes type, or callable: %s\n"
                % (i, repr(t)))
            return False
        return True

    @staticmethod
    def checkUUID(u:str, strict:bool=False) -> bool:
        """Check whether this is the hex-string normative form of a UUID.
        Python constructor (used if not 'strict') ignores hyphens, "urn:uuid:"...
        """
        if (not (isinstance(u, str))): return False
        if (strict):
            return re.match(DatatypeHandler.uuidExpr, u)
        try:
            _uuidObj = uuid.UUID(hex=u)
        except ValueError:
            return False
        return True

DTH = DatatypeHandler(specialFloats=True)


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
    __reservedValues__ = {  # TODO: Move into DatatypeHandler?
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
        self.fname = fname
        self.fnum = fnum

        # Save both the type name and the type per se.
        self.ftypeName, self.ftypeReal = self.identifyType(ftype)
        self.ftype = self.ftypeName   # TODO: Clean up further...

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

    def identifyType(self, ftype:Union[str,type,Callable]=None):
        """ftype can be passed as a type-name, an actual type, or any callable.
        If None, it is coerced to the actual type 'str'.
        """
        ftypeName = ftypeReal = None
        if (ftype is None):
            ftypeReal = str
            ftypeName = "str"
        elif (isinstance(ftype, str)):
            ftypeReal = None  # TODO: Fix
            ftypeName = ftype
        elif (isinstance(ftype, Callable)):
            ftypeReal = ftype
            ftypeName = ftype.__name__
        elif (isinstance(ftype, type)):
            if (ftype in dtHandler.KnownTypes):
                ftypeReal = ftype
                ftypeName = ftype.__name__
            else:
                lg.error("Unrecognized type-name '%s' (assuming str).", ftype)
                ftypeReal = str
                ftypeName = "str"
        else:
            assert False, ("Cannot construct FieldInfo for '%s', ftype is type %s."
                % (self.fname, type(ftype)))
        return ftypeName, ftypeReal

    def handleConstraintString(self, ftype:type, fconstraint:str) -> bool:
        """Check whether the constraint field (in [] in the header) is
        appropriate for the given type. This is *not* a check for actual
        values (see isFieldValueOfType() for that).
        TODO: Test more, esp. escaped regexes for strings.
        """
        if (not fconstraint):
            return True

        if (fconstraint[0] == "[" and fconstraint[-1] == "]"):
            fconstraint = fconstraint[1:-1]

        if (ftype == bool):
            pass
        elif (ftype in [ int, "int", "xint", "oint", "anyint" ]):
            mat = re.match(FieldSchema.intConExpr, fconstraint)
            if (mat):
                self.fmin = int(mat.group(1)) if mat.group(1) else 0
                self.fmax = int(mat.group(2)) if mat.group(2) else sys.maxsize
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
        elif (ftype == uuid):
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


###############################################################################
#
class FieldSchema():
    """Keep track of the known fields, each as a FieldInfo.
    The list can be built manually or initialized from a header record, which
    may have just names or a syntax much like Python type-hints.
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
    intConExpr = r"^(%s)?,(%s)?)$" % (DTH.intExpr, DTH.intExpr)
    # OLD: intConExpr = r"^" + DTH.intExpr + "," + DTH.intExpr + "$"
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
        be constructed and passed in 'finfo', or created here from
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

    def handleRecord(self, fields:List) -> List:
        """Given a truly raw sets of fields, apply all the schema stuff:
            * normalize
            * default/required
            * typecast
            * constraint-check
        """
        for i in range(len(fields)):
            finfo = self.getFieldInfo(i)
            if (finfo.normalizer):
                fields[i] = finfo.normalizer(fields[i])
            if (finfo.ftype != str):
                fields[i] = DatatypeHandler.stripSpace(fields[i])
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
    dx = dialect if dialect else DialectX("default")
    dx.applykwOptions(kwargs)
    dx.checkOptions()

    s = s.strip("\uFEFF")  # Lose the dang BOM.
    # TODO: Upgrade to DatatypeHandler.stripSpace(s)
    if (dx.skipinitialspace): s = s.lstrip()
    if (dx.skipfinalspace): s = s.rstrip()

    thisDelim = currentDelim(dx, fieldNum=1)
    if (not thisDelim): return s.split(sep="")

    currentQuoteMap = setupQuoteMap(dx.quotechar)
    pendingQuote = None
    #breakpoint()
    sLen = len(s)
    i = 0
    tokens = [ "" ]
    while (i < sLen):
        c = s[i]
        lg.info("At char %dx: '%s' U+%04x", i, c, ord(c))

        if (c == dx.escapechar):
            lg.info("    Got escape char.")
            escResult, escLength = Escaping.decodeEscape(s, i, tokens[-1], dx=dx)
            tokens[-1] += escResult
            i += escLength - 1

        elif (pendingQuote):
            if (c == pendingQuote):
                lg.info("    Got close quote '%s'.", c)
                if (dx.doublequote and len(s) > i+1 and s[i+1] == pendingQuote):
                    lg.info("    BUT quote is doubled.")
                    tokens[-1] += pendingQuote
                    i += 1
                else:
                    pendingQuote = None
            else:
                tokens[-1] += c

        elif (dx.entities and c == "&"):  # TODO Should this work outside quotes?
            lg.info("    Got entity start.")
            entExpansion, charsUsed = parseEntity(s[i:])
            if (entExpansion is not None):
                tokens[-1] += entExpansion
                i += charsUsed - 1
            else:
                syntaxError(s, i, tokens[-1], "Ill-formed character reference", strict=dx.strict)

        elif (c in currentQuoteMap):
            lg.info("    Got open quote '%s'", c)
            if (tokens[-1] != ""):
                syntaxError(s, i, tokens[-1], "quote not at start of field", strict=dx.strict)
            pendingQuote = currentQuoteMap[c]

        # Delimiters are odd: single-char; multi-char; any-of; cycling; repeatable; \s+
        elif (isinstance(thisDelim, re.Pattern) and re.match(thisDelim, s[i:])):
            lg.info("Matched delimiter regex /%s/ at offset %d.", thisDelim, i)
            mat = re.match(thisDelim, s[i:])
            i += len(mat.group(0)) - 1
            tokens.append("")
            thisDelim = currentDelim(dx, fieldNum=len(tokens))

        elif (not isinstance(thisDelim, re.Pattern) and
              c == thisDelim[0] and s[i:].startswith(thisDelim)):
            lg.info("Got str delimiter '%s' at offset %d.", thisDelim, i)
            i += len(thisDelim)
            if (dx.delimiterrepeat):
                while (s[i:].startswith(thisDelim)):  # TODO: Factor this out, it's lame.
                    i += len(thisDelim)
            i -= 1  # Will increment at top of loop
            if (dx.maxsplit and len(tokens) > dx.maxsplit):
                syntaxError(s, i, tokens[-1],
                    "maxsplit (%d) exceeded." % (dx.maxsplit), strict=dx.strict)
                tokens.append(s[i+len(thisDelim):])
                break
            tokens.append("")
            thisDelim = currentDelim(dx, fieldNum=len(tokens))

        else:
            tokens[-1] += c

        i += 1  # No continues, please.

    # At end of record
    #
    if (pendingQuote):
        # If the end of line is still inside quotes, and that's allowed,
        # throw UnclosedQuote exception to signal caller to append
        # another line and call us to parse again. Not efficient, but easy.
        if (dx.quotednewline):
            raise UnclosedQuote("Logical record is: " + s)
        else:
            syntaxError(s, i, tokens[-1],
                "Unresolved quote (expected '%s')" % (pendingQuote), strict=dx.strict)
        syntaxError(s, i, tokens[-1], "Unclosed quote", strict=dx.strict)

    if (len(tokens) < dx.minsplit+1):
        syntaxError(
            s, i, tokens[i-1] if 1<=i<=len(tokens) else "",
            "min %d fields needed, but found %d" % (dx.minsplit, len(tokens)),
            strict=dx.strict)

    # Apply normalizers, defaults, typecasting, constraint checks, etc.
    if (schema):
        schema.handleRecord(tokens)
    elif (dx.autotype):
        for i, token in enumerate(tokens):
            _typ, val = dtHandler.guessType(token)
            tokens[i] = val

    return tokens

def currentDelim(dx:DialectX, fieldNum:int) -> str:
    """Return the delimiter string currently expected. This can be weird, given
    the variety of ways delimiters work in CSVs, Python, shell commands, etc.
    Note: Fieldnums count from 1 in common parlance!
    If 'cycle' was set, but the delimiters were set as a string, they should
    long since have been split into a real list.
    TODO: Move into DialectX?
    """
    if (isinstance(dx.delimiter, list)):
        return dx.delimiter[(fieldNum-1) % len(dx.delimiter)]
    else:
        return dx.delimiter

def syntaxError(s:str, i:int, lastToken:str, msg:str, strict:bool=True) -> None:
    """Called on finding a syntax error while parsing a record. If 'strict'
    is set, throw an Exception; otherwise just issues an error message.
    """
    msg = getContextMsg(s, i, lastToken, msg)
    if (strict): raise ValueError(msg)
    else: lg.error(msg)

def getContextMsg(
    s:str,
    offset:int=-1,
    lastToken:str="",
    msg:str="???"
    ) -> str:

    theChar = s[offset] if 0<=offset<len(s) else ""
    msg = "At char '%s' (offset %d, last token '%s'): %s, at %s in:\n    >>%s<<" % (
        theChar, offset, lastToken, msg, POINTING_CHAR, context(s, offset))
    if (args.verbose):
        msg += "\n    Full record:\n    >>%s<<" % (s)
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

    def testPlus(s, expect:Union[List,int]=0, **kwargs) -> List:
        """Run a test that we expect to not die, and to find the 'expect'ed
        tokens or number of tokens.
        TODO: Factor out data.
        """
        print("\nTest string: %s" % (dquote(s, args.visible)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s" ' % (k, dquote(v))
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
        if (expect):
            if (isinstance(expect, int)):
                if (expect != len(theFields)):
                    cprint("    ******* Wrong number of fields: expected %d, got %d."
                        % (expect, len(theFields)))
            else:
                if (expect != theFields):
                    cprint("    ******* Wrong field value(s)s: expected:\n    %s" % (theFields))
        return theFields

    def testMinus(s:str, msg:str, **kwargs) -> List:
        """Run a test that we expect to fail.
        Caller should set strict=True so syntaxError() will actually throw
        an Exception for us to catch, not just give a message.
        """
        print("\nTest string: %s" % (dquote(s, args.visible)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s" ' % (k, dquote(v))
        if (buf): print(" args: " + buf)
        theFields = []
        try:
            if (kwargs):
                theFields = fsplit(s, **kwargs)
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
                print((fmt1 + "%s") % (fName, dquote(fValue)))
            else:
                print((fmt1 + "%s") % (fName, dquote(fValue)))
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

    def smokeTest(theDialect:DialectX):
        """Try out various option combinations on sample records.
        """
        testBasics()
        testEscaping()
        testDelims()
        testQuoting()
        testDatatyping()
        testHeaders(theDialect=theDialect)
        testErrors()

    def testBasics():
        s0 = ""
        testPlus(s0)
        s0 = "no split happens"
        testPlus(s0)
        phead("Commas")
        s0 = "wee fish,ewe,a mare,egrets,moose"
        testPlus(s0, expect=5, delimiter=",")

        phead("TAB")
        s0 = "wee fish\tewe\ta mare\tegrets\tmoose"
        testPlus(s0, expect=5, delimiter="\t")
        phead("TAB, but delim not set")
        testPlus(s0)
        phead("TAB, but escaping the one before 'egrets'")
        #s0 = "wee fish\tewe\ta mare\tegrets\tmoose"
        s0 = "wee fish\tewe\ta mare\\\tegrets\tmoose"
        testPlus(s0, expect=4, delimiter="\t", escapechar="\\")

    def testEscaping():
        phead("Escaping:")
        s0 = "aard\\u0076ark|beagle|cat|d\\x7Cg|&#101;&#x7C;r&dquo;&#X0000007C;"
        print("vbar (U+7C), without special escaping options")
        testPlus(s0, expect=5, delimiter="|")
        print("vbar, with xescapes")
        testPlus(s0, expect=5, delimiter="|", xescapes=True)
        print("vbar, with uescapes")
        testPlus(s0, expect=5, delimiter="|", uescapes=True)
        print("vbar, with entities")
        testPlus(s0, expect=5, delimiter="|", entities=True)
        print("vbar, with all of those")
        testPlus(s0, expect=5, delimiter="|", xescapes=True, uescapes=True, entities=True)

        # TODO: Add Escape and quoting together

    def testDelims():
        # Wonky delimiters
        phead("Multi-char delim:")
        s0 = "lorem##ipsum##dolor##sit##amet##consectetur"
        testPlus(s0, expect=6, delimiter="##")
        s0 = "lorem<>ipsum<>dolor<>sit<>amet<>consectetur"
        testPlus(s0, expect=6, delimiter="<>")
        s0 = "lorem<>ipsum<>dolor<>sit<>amet<>conse\\<>ctetur"
        testPlus(s0, expect=6, delimiter="<>", escapechar="\\")
        s0 = "lorem#ipsum###dolor#@#sit@amet##@@##consectetur"
        testPlus(s0, expect=6, delimiter=re.compile(r"[#@]+"))
        s0 = "lorem#ipsum#######dolor##sit#amet##consectetur"
        testPlus(s0, expect=6, delimiter="#", delimiterrepeat=True)

        s0 = "lorem#ipsum@dolor%sit#amet@consectetur"
        testPlus(s0, expect=6, delimiter=[ "#", "@", "%" ], delimitercycle=True)

    def testQuoting():
        phead("Quoting:")
        s0 = 'wee fish$ewe$"a mare"$egrets$"moo$e"'
        testPlus(s0, expect=5, delimiter="$", quotechar='"')
        testPlus(s0, expect=[ "wee fish", "ewe", "a mare", "egrets", "moo$e" ],
            delimiter="$", quotechar='"')

        s0 = "wee fish$ewe$'a mare'$egrets$'moo$e'"
        testPlus(s0, expect=[ "wee fish", "ewe", "a mare", "egrets", "moo$e" ],
            delimiter="$", quotechar="'")

        s0 = "wee fish$ewe$“a mare”$egrets$“moo$e”"
        testPlus(s0, expect=[ "wee fish", "ewe", "a mare", "egrets", "moo$e" ],
            delimiter="$", quotechar='“”')

        # TODO: Add SINGLE DOUBLE ANGLE CURLY ALL
        # TODO: Add quotes inside quotes

        phead("doublequote:")
        s0 = """lorem,ipsum,"(he said) ""dolor"", I think",sit,amet"""
        testPlus(s0, expect=[ "lorem", "ipsum", "(he said) \"dolor\", I think", "sit", "amet" ],
            delimiter=",", doublequote=True)
        s0 = """'Lorem ipsum ''dolor'' sit amet','consectetur adipiscing elit','sed do
        eiusmod tempor incididunt ut labore et ''dolor''e magna aliqua','Ut enim ad minim
        veniam','quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
        commodo consequat','Duis aute irure ''dolor'' in reprehenderit in voluptate velit
        esse cillum ''dolor''e eu fugiat nulla pariatur','Excepteur sint occaecat
        cupidatat non ''proident''','''sunt'' in culpa qui officia deserunt mollit anim id
        est laborum'"""
        print("Test string: %s" % (dquote(s0, args.visible)))
        toks = fsplit(s0, delimiter=",", quotechar="'", doublequote=True)
        for i0, tok0 in enumerate(toks):
            print("    %2d: /%s/" % (i0, dquote(tok0, args.visible)))

    def testDatatyping():
        phead("minsplit, maxsplit:")
        s0 = "lorem#ipsum#dolor#sit#amet"
        testMinus(s0, "Too few splits", delimiter="#", minsplit=99, strict=True)
        testMinus(s0, "Too many splits", delimiter="#", maxsplit=3, strict=True)

        phead("autotype feature:")
        # TODO: Should the IEEE special floats be caught here?
        s0 = "hello,1,,3.14159,-6.022E+23,1.618+2j,NaN,-inf,+inf,world"
        print("Test string: %s" % (dquote(s0, args.visible)))
        typesExpected = [ str, int, None, float, float, complex, float, float, float, str ]
        stuffs = fsplit(s0, delimiter=",", autotype=True)
        for i0, stuff in enumerate(stuffs):
            print("    %d: %-16s %s" %
                (i0, dquote(stuff, args.visible), type(stuff)))
            if (typesExpected[i0] and
                type(stuff).__name__ != typesExpected[i0].__name__):
                print("        ******* Expected type %s, but got %s."
                    % (typesExpected[i0], type(stuff)))

        # phead("type checking:")

    def testHeaders(theDialect:DialectX):
        phead("Headers")
        fNames = [
            "lname", "fname", "dob", "age", "zip", "APR", "torque", "is_nice" ]
        dx0 = FieldSchema(fNames)
        header1 = ",".join(fNames)
        dx0 = FieldSchema(header1)
        header2 = ("lname:str[\\w+], fname:str|NKFC[(le |de )?[A-Z][a-z]+],"
            "dob:DATE, age:int, "
            "zip:str, APR:float, torque:complex, is_nice:bool")
        dx0 = parseHeaderStrToSchema(header2, theDialect)
        header3 = ("lname:str!, fname:str=Smith, dob:DATE!, age:int, "
            "zip:str[[0-9]{5}]!, APR:float=3.14, torque:complex, is_nice:bool=1")
        dx0 = parseHeaderStrToSchema(header3, theDialect)

        # TODO: Add tests to *use* them.

    def testErrors():
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
            ( "hello &",                "Incomplete entity ref" ),
            ( "hello &lt does this work?", "Incomplete entity ref" ),
            ( "hello &gt.",             "Incomplete entity ref" ),
            ( "hello &amp",             "Incomplete entity ref" ),
            ( "hello &wo:rld;",         "Qname entity ref" ),
            ( "hello &#world;",         "Bad decimal char ref" ),
            ( "hello &#08FF;",          "Bad decimal char ref" ),
            ( "hello &#x00GG;",         "Bad hex char ref" ),
            ( "hello,\"you",            "Unclosed quote" ),
            # unclosed quotes, swapped polarity, not at start of field,....
        ]
        #breakpoint()
        for s0, msg0 in errTests:
            testMinus(s0, msg0, delimiter=",", escapechar="\\",
                quotechar='"', doublequote=False, quotednewline=False,
                xescapes=True, uescapes=True, entities=True, strict=True)
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
            help="Make test output more readable (use control pictures).")
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
        smokeTest(theDialect=indx0)
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
