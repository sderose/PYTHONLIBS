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
The values will be formatted based on their apparent type (int, float, complex,
string).
The CSV dialect can be specified using options named like the API's options.
For example:

    fsplit.py --delim "\\t" --quotechar '"' myFile.csv

If `--visible` is set, control characters will be converted to a readable form
(using Unicode "control pictures").

==Usage from the command line==

To parse a CSV-ish file and see a simple/readable display, just do:
    fsplit.py myFile.csv

Options can be added to specify alternate syntaxes, the presence of a header
(which then displays the field names on the instances below). For example:
    fsplit.py --header --delim "\t" --quotedouble myFile.csv

A header can instead be supplied on the '--ifields' option (in the same format).

You can convert a file(s) from one CSV-ish format to another, by using
the same options with "o" prefixed to specify the output format:
    fsplit.py --header --delim "\t" --quotedouble --odelim ":" --oecapechar "\\" myFile.csv

There is also a suite of command-line filters built on top, which mimic
the usual *nix commands that support fields. Theses unify the "CSV"-ish
support across filters (all the usual ones differ in what they can and
cannot parse, and most just don't support common features like quoting,
escaping, and Unicode (much less the extended options supported here).

When finished, the suite should include:
awk, colrm, column, cut , join, lam, paste, sort, tab2space, uniq, xargs.
Perhaps also: colrm, expand, lam, look, sed, unexpand, fold, and a varient
of 'less' than shows one record per page.


==Usage as an API==

This works essentially like {Python's built-in "csv" package, except for
having more options. These fall into several categories:

* syntactic options such as more flexible delimiter handling and
escaping (to complement the various *nix "CSV"-ish filters);
* extended header record syntax modeled on Python type hints;
* support for normalization, type-checking, casting to declared types,
value constraints, and default values (see under "Header format" below_);
* Unicode support throughout (even curly-quote quoting).

===Classes===

The `fsplit` package includes these classes:

* DialectX -- very much like csv.Dialect, but with more items.
One DialectX is predefined, as `__RFC4180__`, with those settings (`header`
is set to False, since RFC 4180 makes it optional; this does mean that if
there is a header (and you don't set `header` or read the header record
manually), the header record will be taken as data.

* DictReader -- like csv.DictReader

* DictWriter --

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
** fformat -- a preferred output format, for example "%12.4f"
*** fnormalizer -- a Callable which is the first thing applied to a field once
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
    balance:float       floating-point number
    root:complex        python notation
    lastName:str        string (this doesn't do much).
    dob:datetime        datetime (ISO 8601)

Other types (mainly subtypes) will likely be added).

Defaults can be given after an "=", or "!" may be used to indicate
that a non-empty value is ''required''
(default values can contain quotes or delimiters only if escaped the same way as
other data in the file):
    obsolete:bool=0
    payGrade:float!

A normalizer name can be specified immediately after the type name, separated by "|".
Underneath, a normalize is a function that takes the field value (after unescaping and
unquoting if applicable), and returns a string (or raises ValueError on failure).
They can be used for case-folding, detecting special "reserved" values (such as "-" for
Not applicable, which one might map to None), etc.

Custom normalizers can be set via the 'fnormalizer' parameter when constructing a
FieldIngo object in the API, but not via the header.
The following named normalizers are predefined, and can be given in the header::
    UPPER -- force the value to uppercase
    LOWER -- force the value to lowercase
    NFKD, NFKC, NFC, NFD -- apply that Unicode normalization form
    XSP -- apply XML space normalization (just space, TAB, CR, LF)
    USP -- Unicode space normalization (all \\s)
    TF -- fields beginning with [Tt] go to 1, [Ff] go to 0 (if the field is declared
to be type bool, those will then be recognized and cast to True and False.
    ASCII -- non-ASCII characters to \\x, \\u, \\x{} escapes

A value ''constraint'' can also be included in [] immediately after the datatype and
normalizer name. The form of the constraint is type-specific:

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
* str: the constraint is a regular expression that each value much match in its
entirety. Such constraint commonly require escaping.
These constraints can be used to implement other things, such as enums:
    compass:str[N|E|W|S|NE|NW|SE|SW]=N
    province:str[NL|PE|NS|NB|QC|ON|MB|SK|AB|BC|YT|NT|NU]!

When a type is specified, raw field values will be cast to that type for return
(say, by reader() and DictReader(). When a field is empty, if a default value
was set, that will be cast to the specified type and returned.
Fields with no type hint in the header default to type 'str', and no default
(which amounts to "").

==What if there's no header record?==

For files lacking a header record, you can do several things:

* do nothing (and don't set '--header') -- in that case, field names like
"Field_01" will be assigned as needed.
* add a header record  to your data file(s).
* use the '--ifields' option on the command line, which takes exactly the
same syntax.
* provide the information via the API. To achieve this, construct
a 'FieldSchema' object and use 'append()' to define any number of fields (these
are represented by 'FieldInfo' objects, which can be constructed given only a name,
or with argument or type, constraint, required, and so on).
FieldInfo objects offer extra features such
as mapping reserved strings (say, "True", "False", "N/A", etc. to values.

A field for which no type is set will be returned as a literal stringn unless
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

My `csv2xml.py` -- Obsolete precursor to `fsplit.py`, but has a number of
possibly useful export formats.

For a more complete list, including generalized and Unicode-aware ports
of several *nix utilities, see [http://github.com/sderose/CSV] and
[http://github.com/sderose/XML/CONVERT].


=Known bugs and Limitations=

If using `bool` with the `types` option, only the empty string counts as "False".
reservedValues should work to specify other acceptable values.
There is a `boolCaster()` function for this, but it's not connected.

fieldNames passed to DictReader should probably be allowed to override any
read from a header record. But currently they're compared and an exception
is raised if they don't match.

Multi-char delim test is failing.

'--convert' does not copy comment lines, even if an output dialect command
marker is specified.

Not sure whether you can (or should be able to) escape in mid-delimiter.

What's the right rule for a quote not immediately following a delimiter?
As in
    1, "two", 3, 4"five"5, 6

It might be nice to have a way to change the set of backslash codes,
such as \\b for BEL, etc.


=To do=

See "also my related scripts such as `Record.py`, `Homogeneous.py`,
`Datatypes.py` for some other features that may be added.

* Data subtypes:
** Hex and maybe octal fields; maybe uudecode/base64; currency, %?; datetimes?
** Support normalizers for str fields (case-folding, NFKC etc., entities and escapes)
** Improve datetimes. Finish datetimecaster. Support timedelta. Allow type-hints
of isodate, isotime, epochtime, isotimedelta, usdate, eudate.

* Add predefined dialects: RC4081, Excel, and any that Python `csv` provides.

* Some kind of hysteresis for autotyping. Like, if this field has always been int
and now we see "", make it 0; if if always float and we see 12, make it 12.0.

* Per RC4081 complain about rec-final delimiter if not quoted.
* More flexible delimiters:
    ** regex delimiters?
    ** the "whitespace to nonspace transition" approach (like awk, column, and sort)
    ** repeatable delimiter (that don't generate empty fields)
    ** Finish support for cycling delimiters (like 'paste -d').
* Finish and test field Defaults
* Creating NamedTuple or tuple instead of list or dict?
* Make sure it can just take a csv.Dialect for the DialectX arguments.
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
Start parseHeaderStrToSchema() and handling of type hints and defaults. Start open/close
quote support. Add cleanField() to do strip, unquote, unescape, entities,
normalization, etc. Start main beyond basic smoke-test.
Add --convert vs. prettyprinting. Add UberType info. Reorg quote pairs and
option defaulting. Add --showQuotes and --showDialectX. Refactor
reader() and writer() to be like csv ones (add generator classes).
Ditch 'typelist'.


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
        "comment":          None,
        "cycle":            False,
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
        self.checkOptions()

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
        self.entities          = False  # bool
        self.header            = False  # bool
        self.maxsplit          = None   # int
        self.minsplit          = 0      # int
        self.multidelimiter    = False  # bool
        self.autotype          = False  # bool
        self.uescapes          = False  # bool
        self.xescapes          = False  # bool
        self.quotednewline     = False  # bool

        for oname in self.__OptionTypes__.keys():
            try:
                _val = getattr(self, oname)
            except AttributeError:
                lg.critical("Uninitialized option '%s'.", oname)
                sys.exit()
        return

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

    def checkOptions(self):
        if (not self.delimiter):
            raise ValueError("No delimiter set.")
        #if (not isinstance(delimiter, list)):
        #    delimiter = [ delimiter ]
        # pylint: disable=C0123
        if (type(self.quoting) == str):
            self.quoting = QUOTING[self.quoting]
        if (type(self.quoting) != type(QUOTING.MINIMAL)):
            raise ValueError("Value '%s' not valid for quoting (it's a %s)."
                % (self.quoting, type(self.quoting)))
        if (self.maxsplit and self.minsplit and self.maxsplit < self.minsplit):
            raise ValueError("maxsplit (%d) < minsplit (%d)." %
                (self.maxsplit or 0, self.minsplit or 0))
        if (self.doublequote and self.escapechar):
            raise ValueError("Cannot combine doublequote and escapechar")

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
            pre+"doublequote", action="store_true",
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
            pre+"maxsplit", type=int, default=None, metavar="N",
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
            pre+"types", type=str, action="append",
            choices=[ "str", "int", "float", "bool" ],
            help="A type for the (next) field (repeatable).")
        parser.add_argument(
            pre+"uescapes", action="store_true",
            help="Recognize \\uFFFF-style special characters.")
        parser.add_argument(
            pre+"xescapes", action="store_true",
            help="Recognize \\xwFF-style special characters.")

        return

    def applyargs(self, theArgs: argparse.Namespace, prefix="") -> None:
        """Call this to move the arguments (typically added by
        addargs), to the current instance.
        """
        for k in DialectX.__OptionTypes__:
            if (k in theArgs.__dict__ and theArgs.__dict__[k] is not None):
                self.__dict__[k] = theArgs.__dict__[prefix+k]

    @staticmethod
    def makeVis(mat):
        n = ord(mat.group(1))
        if (n < 32): return chr(0x2400+n)
        if (n > 127 and n < 160): return "\\x%02x" % (n)
        return "\\u%04x" % (n)

    def tostring(self):
        """Readable option settings.
        Useful to save or print out send with your data.
        """
        buf = ""
        for k in sorted(self.__OptionTypes__.keys()):
            val = getattr(self, k)
            if (isinstance(val, str)):
                val = re.sub(r"([\x00-\x1F])", self.makeVis, val)
            buf += "%-20s %s\n" % (k, val)
        return buf

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
#
class UberTypes(Enum):
    NUM   = float
    STR   = str
    DATETIME = datetime.datetime
    TIMEDELTA = datetime.timedelta

class BaseTypes(Enum):
    BOOL  = bool
    INT   = int
    FLOAT = float
    COMPLEX = complex
    ARRAY   = array.array

class SubTypes(Enum):
    IDENT   = (str, 1)   # word-char-initial token
    URI     = (str, 2)

    XINT    = (int, 11)
    UINT    = (int, 12)
    OINT    = (int, 13)
    GINT    = (int, 14)  # 0xFF or 0777 or 999

    PROB    = (float, 21)

    # YEAR MONTH DAY JULIAN HOUR MIN SEC OFFSET

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

NamedNormalizers = {
    "UPPER":    str.upper,
    "LOWER":    str.lower,
    "NFKC":     lambda s: unicodedata.normalize("NFKC", s),
    "NFKD":     lambda s: unicodedata.normalize("NFKD", s),
    "NFC":      lambda s: unicodedata.normalize("NFC", s),
    "NFD":      lambda s: unicodedata.normalize("NFD", s),
    "XSP":      lambda s: re.sub(r"[ \t\r\n]+", " ", s),
    "USP":      lambda s: re.sub(r"\s+", " ", s),
    "TF":       TFNorm,
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
        dialect: DialectX=None
        # *args,  # ???
        #**theKwds
        ):
        self.f          = f
        self.recnum     = 0
        self.fieldNames = fieldNames  # If none, assume header
        self.restkey    = restkey     # Field name for leftovers
        self.restval    = restval     # Values for missing fields
        self.dialect    = dialect

        self.fschema    = None        # Set up during first read
        self.line_num   = 0
        self.rec_num    = 0
        # TODO: set up the kwargs

        """Read records into a dict of fields by name.
        Quoted fields that span lines are still experimental.
        """

    def __iter__(self):
        logicalRec = ""
        for physicalRec in reader(self.f, dialect=self.dialect):
            self.line_num += 1  # physical
            logicalRec += physicalRec
            try:
                fields = fsplit(logicalRec, self.dialect)
            except UnclosedQuote:
                continue  # Go around for continuation line
            self.rec_num += 1  # logical

            if (self.rec_num==1):
                if (self.dialect.header or not self.fieldNames):
                    fs = ensureSchema(self.fschema, logicalRec, self.dialect, args.ifields)
                    self.fieldNames = fs.getFieldNames()
                    continue  # Go around for first data record
                fs = ensureSchema(self.fieldNames, None, self.dialect, args.ifields)
                self.fieldNames = fs.getFieldNames()

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

            logicalRec = ""
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

        TODO: Header doesn't yet support full range of quoting and escaping.
        """
        self.line_num += 1  # TODO: Drop this?

        fschema = FieldSchema()
        for fnum, hfield in enumerate(fsplit(rec, dialect)):
            fi = self.parseOneHeaderItem(hfield, nameExpr, fnum)
            fschema.append(fi)

        if (False and self.fieldNames and self.fieldNames != fschema.getFieldNames()):
            raise ValueError("Header does not match expected fieldNames:\n    %s\n    %s" %
                (str(self.fieldNames), str(self.fieldNames)))
        return fschema

    fnameExpr = r"(%s)"
    fconstraintExpr = r"(\[[^\]]*\])?"
    ftypeExpr = r"(:\w+%s)?" % (fconstraintExpr)
    fdefaultExpr = r"(=\w+)?"
    itemExpr:Final = fnameExpr + ftypeExpr + fdefaultExpr + r"$"

    # Define the types that can be used in header hints. This is just CSV fields, so
    # there's no place for aggregates/collections/etc.
    # cf Datatypes.py
    # Largely based on Python + XSD Datatypes. However, not all of either.
    #
    baseHeaderTypes = {
        #
        ### NUMERICS
        #
        "bool":     (bool,    UberTypes.NUM),
        # TODO: values?  bool[T,Nil]?
        "int":      (int,     UberTypes.NUM),
        # TODO: pos/neg/npos/nneg ?
        "float":    (float,   UberTypes.NUM),
        # TODO: prob, pos/neg/npos/nneg
        "complex":  (complex, UberTypes.NUM),
        # TODO: i or j?
        #
        ### STRINGS
        #
        "str":      (str,     UberTypes.STR),
        # TODO: upper, lower, title, nfkc, etc. (initial \\L, \\U, etc)?
        # TODO: regex constraint; min/max len (or use r".{min, max}"?
        # TODO: escaping in the regex?
        # TODO: enum[x|y|z]
        "ident":    (str,     UberTypes.STR),
        #
        ### TIME STUFF
        # Datetimes are messy.... Just do ISO8601, usdate, eudate, unixEpoch? for now?
        #
        "date":     (datetime.date,       UberTypes.DATETIME),
        "time":     (datetime.time,       UberTypes.DATETIME),
        "datetime": (datetime,            UberTypes.DATETIME),
        "duration": (datetime.timedelta,  UberTypes.DATETIME),
    }

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
        Not all Python types can be used -- just those provided in 'baseHeaderTypes'.
        """
        hfield = hfield.strip()
        ftypename = fconstraint = fdefault = None
        frequired = False

        if (hfield[0] in "'\""):
            hfield.strip(hfield[0])
        if hfield.endswith("!"):
            frequired = True
            hfield = hfield[0:-1]

        mat = re.match(self.itemExpr % (nameExpr), hfield)
        if (not mat):
            raise ValueError("Cannot parse header item %d: <<<%s>>>" % (fnum, hfield))
        else:
            fname = mat.group(1)
            ftype = str
            if (mat.group(2)):
                ftypename = mat.group(2)
                if (mat.group(3)):
                    fconstraint = mat.group(3)
                    ftypename = ftypename[0:-len(fconstraint)]
                if (ftypename in self.baseHeaderTypes):
                    ftype = self.baseHeaderTypes[ftypename][0]
                else:  # TODO: Is this worth an exception? OR leave to caller?
                    raise ValueError("Could not locate type named '%s'." % (ftypename))
            if (mat.group(4)):
                fdefault = mat.group(3)

        finfo = FieldInfo(fname, fnum, ftype, fdefault, frequired)
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

def reader(csvfile:IO, dialect=None, **formatParams):
    """Construct and return an fsplit-based generator object.
    Read a logical record (possibly >1 physical record), and parse it
    into raw fields.
    Python's CSV doesn't treat this as a class (unlike DictReader), so we
    do the same. The main thing beyond readline() is that it handles quoted
    newlines (but it does so only by counting quotes, so doesn't play well
    with escaped quotes).
    """
    if (not dialect): dialect = DialectX(**formatParams)

    buf = ""
    logicalRecnum = 0
    nPhysical = 0
    for rec in csvfile.readlines():
        nPhysical += 1
        # TODO Are comments allowed as physical lines inside logical recs?
        if (dialect.comment and
            rec.startswith(dialect.comment)): continue
        buf += rec
        if (not unclosedQuote(rec, quotechar=dialect.quotechar)):
            lg.info("read header logical rec as: <<<%s>>>", buf)
            fields = fsplit(buf, dialect)
            if (nPhysical > 1):
                info2("Logical record included %d physical records.", nPhysical)
            # If this was the header, handle it and go around again for data.
            logicalRecnum += 1
            yield fields
            nPhysical = 0
    return None


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
class DictWriter:
    """Like "writer" but takes dicts, and writes their members in the
    order specified by "fieldNames".

    When using "writerow()", if "fieldNames":
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
    _formatRegex = r"%-?\d+(\.\d+)[dxobsfg]"

    def __init__(self,
        f: IO,
        #*args1,
        fieldNames: list = None,
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
    mat = re.match(r"&(#\d+|#x[\da-f]+|\w[\d\w]*);", s, re.I)
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

    def guessType(self, tok: str, vectors:bool=False) -> (type, Any):
        """Find the most specific type we can justify, and
        return that type plus the value cast to that type.
        Other types to maybe add:
            SVG paths:    "M 10 10 H 90 V 90 H 10 L 10 10"
            n-D vectors:  "(1.0, -2.1)"
        """
        if (not isinstance(tok, str)):
            return type(tok), tok

        tok2 = tok.strip()

        if (tok2 == ""):
            return type(None), None
        if (self.boolCasterFunc):
            try: return bool, self.boolCasterFunc(tok2)
            except ValueError: pass
        # Prevent "float" from catching these when not wanted:
        if (not self.specialFloats and tok2 in ("NaN", "inf", "-inf", "+inf")):
            return str, tok2
        if (self.datetimeCasterFunc):
            try: return datetime, self.datetimeCasterFunc(tok2)
            except ValueError: pass
        try: return int, int(tok2, 0)
        except ValueError: pass
        try: return float, float(tok2)
        except ValueError: pass
        try: return complex, complex(tok2)  # Test *after* float
        except ValueError: pass

        if (vectors and re.match(self.vectorExpr, tok2)):
            return array.array, self.str2array(tok2)

        return str, tok

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
        fformat:str=None,
        fnormalizer:Callable=None,
        fnum:int=-1
        ):
        assert fname
        #assert fnum>0
        if (not (ftype is None or isinstance(ftype, (type, Callable)))):
            lg.critical("ftype passed as %s (%s).", ftype, type(ftype))
            assert False
        self.fname = fname
        self.fnum = fnum
        self.ftype = ftype
        self.fconstraint = fconstraint
        self.fdefault = fdefault
        self.frequired = frequired
        self.fformat = fformat
        #self.freservedValues = freservedValues  # TODO: drop?
        self.fnormalizer = fnormalizer

        # Futures...
        self.regexConstraint = None
        self.fMin = None
        self.fMax = None

        if (self.frequired and self.fdefault is not None):
            lg.error("Don't set 'required' when there's also a default value.")
            self.frequired = False

    def isConstraintOk(self, ftype:type, fconstraint:str) -> bool:
        """Check whether the constraint field (in []) is appropriate for the given
        type. This is *not* a check for actual values (see isValueOk() for that).
        TODO: Test a bunch, esp. escaped regexes for strings.
        """
        if (not fconstraint): return True

        if (fconstraint[0] == "[" and fconstraint[-1] == "]"):
            fconstraint = fconstraint[1:-1]

        if (ftype == int):
            return re.match(FieldSchema.intConExpr,  fconstraint)
        if (ftype == float):
            return re.match(FieldSchema.floatConExpr,  fconstraint)
        if (ftype == complex):
            return re.match(FieldSchema.complexConExpr,  fconstraint)
        if (ftype == array):
            return True  # TODO: Any fconstraints for vectors?
        if (ftype == str):
            try:
                _c = re.compile(fconstraint)
                return True
            except re.error:
                return False
        return True  # Not ideal...

    def isValueOk(self, val: Any) -> bool:
        """Determine whether a given field as a string, fits the datatype and
        constraints (if any); or if not required, is empty.
        """
        if (val is None):
            if (self.frequired): return False
        if (0 and not isinstance(val, self.ftype)):
            #if (val in self.freservedValues):
            #    val = self.freservedValues[val]
            try:
                val = self.ftype(val)
            except ValueError:
                return False
        return True


###############################################################################
#
class FieldSchema():
    """Keep track of the known fields, each as a FieldInfo. This is largely
    a list, but subclassing list seems troublesome.
    The list can be built manually, or initialized from a header record, which
    may have just names, or a syntax much ilke Python type-hints.
    See also Homogeneous.py.

    OrderedDict is not useful here, b/c you can't fetch by position.

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
    fconstraintExpr = r"(\[[^\]]*\])?"
    ftypeExpr = r"(:\w+" + fconstraintExpr + r")?"
    fdefaultExpr = r"(=\w+|!)?"
    hintExpr = fnameExpr + ftypeExpr + fdefaultExpr + r"$"

    # More detailed regexes to check internal syntax of constraints (per type)
    intConExpr = r"^" + DTH.intExpr + "," + DTH.intExpr + "$"
    floatConExpr = r"^" + DTH.floatExpr + "," + DTH.floatExpr + "$"
    complexConExpr = r"^" + DTH.complexExpr + "," + DTH.complexExpr + "$"

    def __init__(self, fieldNames:List=None, nameRegex:str=None):
        #super(list, FieldSchema).__init__(self)
        self.nameRegex = nameRegex
        self.theFieldInfos = []
        self.infoDict = {}
        if (fieldNames):
            for fname in fieldNames:
                self.append(FieldInfo(fname=fname))

    def len(self):
        return len(self.theFieldInfos)

    def append(
        self,
        finfo:FieldInfo=None,
        fname:str=None,
        ftype:type=str,
        fconstraint:str=None,
        fdefault:Any=None,
        frequired:bool=False,
        fformat:str="%s",
        fnormalizer:Callable=None,
        #freservedValues:Dict=None
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
                fnormalizer=fnormalizer, fnum=fnum)
                #freservedValues=freservedValues)

        if (finfo.fname in self.infoDict):
            raise KeyError("Field '%s' already in FieldSchema." % (finfo.fname))
        if (self.nameRegex and not re.match(self.nameRegex, finfo.fname)):
            lg.warning("Field name '%s' does not match nameRegex /%s/.",
                finfo.fname, self.nameRegex)
            # TODO: Map to something acceptable?

        lg.info("Appending field #%d: '%s'", fnum, finfo.fname)
        self.theFieldInfos.append(finfo)
        self.infoDict[finfo.fname] = finfo
        return finfo

    def getFieldInfo(self, which: Union[int, str]) -> FieldInfo:
        """Retrieve one FieldInfo object, by name of number.
        TODO: This should count from 1, field numbers....
        """
        if (isinstance(which, int)): return self.theFieldInfos[which]
        if (which in self.infoDict): return self.infoDict[which]
        raise KeyError("Cannot find field %s." % (which))

    def getFieldNames(self) -> List:
        fnames = []
        for i in range(len(self.theFieldInfos)):
            fnames.append(self.theFieldInfos[i].fname)
        return fnames

    # TODO: Override getitem() to (at dialect option) to die or make up out-of-range names

    def handleRecord(self, fields:List) -> List:
        """Given a truly raw sets of fields, apply all the schema stuff:
            * normalizer
            * default/required
            * casting
            * constraint-checking
        """
        for i in range(len(fields)):
            finfo = self.getFieldInfo(i)
            if (finfo.normalizer):
                fields[i] = finfo.normalizer(fields[i])
            if (finfo.ftype != str):
                fields[i] = fields[i].strip()
            if (fields[i] is ""):
                if (finfo.frequired):
                    raise ValueError("Missing required field %s." % (finfo.fname))
                if (finfo.default): fields[i] = finfo.default
            if (finfo.ftype):
                fields[i] = self.castToType(fields[i], finfo)
            # dtHandler.(self, tokens)  # TODO ????
        return fields

    def castToType(self, field:Any, finfo:FieldInfo):
        if (finfo.ftype == bool):
            val = bool(field)
            return val
        if (finfo.ftype == int):
            val = int(field)
            if ((finfo.fmin and val < finfo.fmin) or
                (finfo.fmax and val > finfo.fmax)): raise ValueError
            return val
        if (finfo.ftype == float):
            val = float(field)
            if ((finfo.fmin and val < finfo.fmin) or
                (finfo.fmax and val > finfo.fmax)): raise ValueError
            return val
        if (finfo.ftype == complex):
            val = complex(field)
            #if (): raise ValueError
            return val
        if (finfo.ftype == datetime.datetime):
            val = datetime.datetime.fromisoformat(field)
            #if (): raise ValueError
            return val
        if (finfo.ftype == array.array):
            val = dtHandler.str2array(field)
            #if (): raise ValueError
            return val
        if (finfo.ftype == str):
            val = str
            # TODO: Add ^$? re.I
            if (finfo.fconstraint and not re.search(finfo.fconstraint, val)):
                raise ValueError


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
    fschema = FieldSchema()

    if (isinstance(headerItems, str)):
        headerItems = fsplit(headerItems, dialect=dialect)

    for fnum, rawItem in enumerate(headerItems):
        lg.info("headItems[%02d]: '%s'", fnum, rawItem)
        cleandialect = cleanField(rawItem, dialect=dialect)
        mat = re.match(FieldSchema.hintExpr, cleandialect)
        #lg.info("hint parse #%d got [ %s, %s, %s, %s ]\n    from '%s'",
        #    fnum, mat.group(1), mat.group(2), mat.group(3), mat.group(4), cleandialect)
        if (mat):
            fname = mat.group(1)
            ftype = mat.group(2)
            fconstraint = mat.group(3)
            fdefault = mat.group(4)
            finfo = FieldInfo(fname,
                ftype=ftype, fconstraint=fconstraint, fdefault=fdefault, fnum=fnum)
        else:
            finfo = FieldInfo(fname=rawItem)
        fschema.append(finfo)
    return fschema


###############################################################################
# The function that actually parses up lines, dealing with various escaping
# and quoting variations, etc.
#
dtHandler = None  # TODO: make better

def fsplit(
    s: str,                     # The string to split:
    dialect: DialectX=None,     # The DialectX to assume
    fschema: FieldSchema=None,
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
                    msg = getContextMsg(s, i, tokens, "Incomplete \\x escape")
                    raise ValueError(msg)
                theHexString = mat.group(1) if mat.group(1) else mat.group(2)
                n = int(theHexString)
                if (n > sys.maxunicode):
                    raise "\\x escape outside Unicode range (%x)." % (n)
                tokens[-1] += chr(n, 16)
                toIgnore = len(theHexString)

            elif (dx.uescapes and c in "Uu"):
                if (c == "u"):
                    mat = re.match(r"u[\da-f]{4}", s[i:])
                    if (not mat):
                        msg = getContextMsg(s, i, tokens, "Incomplete \\u escape")
                        raise ValueError(msg)
                    tokens[-1] += chr(int(s[i+1:i+5], 16))
                    toIgnore = 4
                if (c == "U"):
                    mat = re.match(r"U[\da-f]{8}", s[i:])
                    if (not mat):
                        msg = getContextMsg(s, i, tokens, "Incomplete \\U escape")
                        raise ValueError(msg)
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
            elif (dx.strict):
                msg = getContextMsg(s, i, tokens, "Ill-formed character reference")
                raise ValueError(msg)

        elif (c in currentQuoteMap):
            info2("    Got open quote '%s'", c)
            if (dx.strict and tokens[-1] != ""):
                msg = getContextMsg(s, i, tokens, "quote not at start of field")
                raise ValueError(msg)
            pendingQuote = currentQuoteMap[c]

        elif (c == thisDelim[0] and s[i:].startswith(thisDelim)):
            info2("Got the delimiter string")
            if (dx.multidelimiter):
                nDelims = 0
                while (s[i+nDelims*dlen].startswith(thisDelim)): nDelims += 1
                toIgnore = (nDelims * dlen) - 1
            if (dx.maxsplit is not None and len(tokens) >= dx.maxsplit):
                tokens.append(s[i+len(thisDelim):])
                break
            tokens.append("")

        else:
            tokens[-1] += c

    # At end of record
    if (pendingQuote):
        # If the end of line is still inside quotes, and that's allowed,
        # throw exception, to signal caller to append another line and
        # call us to parse again. Not efficient, but easy.
        if (dx.quotednewline):
            raise UnclosedQuote()
        if (dx.strict):
            msg = getContextMsg(s, i, tokens,
                "Unresolved quote (expected '%s')" % (pendingQuote))
            raise ValueError(msg)

    if (dx.strict and (escaped or pendingQuote)):
        msg = getContextMsg(s, i, tokens, "Unresolved escapechar")
        raise ValueError(msg)

    if (dx.minsplit is not None and len(tokens) < dx.minsplit+1):
        msgLine = "min %dx tokens needed, but found %dx" % (dx.minsplit, len(tokens))
        msg = getContextMsg(s, i, tokens, msgLine)
        raise ValueError(msg)

    # maxsplit just stops splitting, no error (TODO: Change?)

    if (fschema):
        fschema.handleRecord(tokens)
    elif (dx.autotype):
        for i, token in range(len(tokens)):
            _typ, val = dtHandler.guessType(token)
            tokens[i] = val

    return tokens

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
# Datatyping (move to separate package/class?
#
typeMap = {
    "str":    str,
    "bool":   bool,
    "int":    int,
    "float":  float,
}

def mapTypeNames(types:Union[str, type]):
    """Convert a string type name, or an actual type, to the type.
    This is useful if a caller wants to let the user specify types, say,
    in command-line options, where they can't get a real Python type.
    TODO: Maybe do with an enum instead?
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

def sniffType():
    raise KeyError("Nope.")


###############################################################################
# Subcommands
#
def prettyPrint(ifh:IO, idx:DialectX, ischema:FieldSchema) -> int:
    """Read the file and print it out nicely.
    TODO: Switch to user
    """
    recnum = 0
    for rec in ifh.readlines():
        recnum += 1
        if (recnum == 1):
            ischema = ensureSchema(ischema, rec, idx, args.ifields)
            ifieldNames = ischema.getFieldNames()
            continue
            #print("names: %s" % (ifieldNames))
        myFields = fsplit(rec, dialect=idx)
        if (len(myFields) < 2):
            lg.warning("Record %d doesn't seem to have fields (delim is '%s'):\n    %s",
                recnum, idx.delimiter, rec)
            continue
        print("\n======= Record %d (%d fields):" % (recnum, len(myFields)))
        if (args.verbose):
            print("    %s" % (rec), end="")
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
    fschemaArg:Union[FieldSchema, List],  # Pre-made schema or list of field-names
    firstRec:str=None,                    # Header rec, if available/applicable
    dialect:DialectX=None,                # Syntax spec
    fsArg:str=None                        # Header rec from another source, like args)
    ) -> 'FieldSchema':
    """Handle the fschema arg to ensure we have *some* kind of schema.
    If the caller passed:
        * a real FieldSchema, use it
        * a list of field names, make a schema from them
        * a dialect with headers, parse firstRec
        * an fsArg (presumably from args.ifields or args.ofields), parse it
        * None of those: parse the firstRec and make up that many generic names.
        * Failing that, make a schema of 99 generic names.
    """
    if (args.verbose):
        lg.warning("In ensureSchema:\n"
            "    fschemaArg   %s\n"
            "    firstRec     %s\n"
            "    dialect      %s (header is %s)\n"
            "    fsArg        %s\n",
            fschemaArg, firstRec, dialect, dialect.header, fsArg)

    if (not dialect.header and firstRec and re.match(r"^(\w+)(,\w+)+$", firstRec)):
        lg.warning("dialect.header is not set, but first record looks like one:\n"
            "    %s", firstRec)

    if (isinstance(fschemaArg, FieldSchema)):
        return fschemaArg
    if (isinstance(fschemaArg, List)):
        return FieldSchema(fschemaArg)
    if (dialect.header):
        return parseHeaderStrToSchema(firstRec, dialect=dialect)
    if (fsArg):
        return parseHeaderStrToSchema(fschemaArg, dialect=dialect)
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
    def testPlus(s, **kwargs) -> List:
        """Run a test that we expect to pass (or at least not die).
        TODO: Factor out data. Add expected result or save and compare.
        """
        print("\nTest string: %s" % (dquote(s)))
        buf = ""
        for k, v in kwargs.items(): buf += '%s="%s"  ' % (k, v)
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

    def testMinus(s, **kwargs) -> List:
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

    def phead(msg) -> None:
        print("\n******* %s" % (msg))

    def printByApparentType(_i:int, fName:str, fValue:str) -> None:
        fmt1 = "    %-" + str(args.width) + "s "
        gType, castValue = DTH.guessType(fValue)
        if (gType == str):
            if (args.visible):
                print((fmt1 + "%s") % (fName, visify(fValue)))
            else:
                print((fmt1 + "%s") % (fName, fValue))
        elif (gType is None):
            print((fmt1 + "%s") % (fName, "\u2205"))
        elif (gType == bool):
            print((fmt1 + "%8s") % (fName, "True" if castValue else "False"))
        elif (gType == int):
            print((fmt1 + "%8d") % (fName, int(fValue)))
        elif (gType == float):
            print((fmt1 + "%12.3f") % (fName, float(fValue)))
        elif (gType == complex):
            print((fmt1 + "%s") % (fName, complex(fValue)))
        elif (gType == datetime):
            print((fmt1 + "%s") % (fName, fValue))
        else:
            print((fmt1 + "%s") % (fName, fValue))

    def smokeTest():
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
        testPlus(s0, delimiter=",")

        phead("TAB, but escaping the one before 'egrets'")
        s0 = "wee fish\tewe\ta mare\\\tegrets\tmoose"
        testPlus(s0)

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
        testPlus(s0, delimiter="##", minsplit=99, strict=True)
        testPlus(s0, delimiter="##", maxsplit=3, strict=True)

        phead("autotype feature:")
        s0 = "hello,1,,3.14159,-6.022E+23,1.618+2j,NaN,-inf,+inf,world"
        print("Test string: %s" % (dquote(s0)))
        stuffs = fsplit(s0, delimiter=",", autotype=True)
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
            testMinus(s0, delimiter=",", strict=True,
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
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--showDialectX", "--showdx", action="store_true",
            help="Display dialect settings.")
        parser.add_argument(
            "--showQuotes", action="store_true",
            help="Display the named quote-pairs.")
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
            logging.basicConfig(level=logging.INFO - args0.verbose)

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
        else:
            prettyPrint(infh0, indx0, inschema0)
        infh0.close()

    if (not args.quiet):
        print("\nDone.\n")
