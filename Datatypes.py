#!/usr/bin/env python3
#
# Datatypes.py: Verify datatypes represented by string data.
# Written 2012-05-07 by Steven J. DeRose.
#
#pylint: disable=W0703
#
import sys
import re

__metadata__ = {
    'title'        : "Datatypes",
    'description'  : "Provide basic type-checking, conversions, formatting.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2012-08-12",
    'modified'     : "2020-08-19",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Usage=

Provide checking for whether strings represent values conforming
to a wide range of fairly atomic datatypes, including XSD's built-in datatypes.

If you set option '''xsv''' a few more types are supported, as described below.

    import Datatypes
    typeChecker = Datatypes()
    myValues = [ '1', '-2', 'False', 'spam' ]
    for s in myValues:
        if (not typeChecker.checkValueForType('int', s)):
            print("String does not represent an integer: '%s'." % (s))

This is intended to handle all the datatypes defined by XML Schema Datatypes
(second edition), plus a few more as described below. It will check strings
for whether they're interpretable as a given type, and if so, whether the
value falls within the required range.

=Methods=

* ''setOption(self, name, value)''

The options include:

* '''quiet'''

* '''xsv''' -- Include support for some extension datatypes.
Default: '''False'''.

* ''getOption(self, name)''

Find the current value of the named option (see '''setOption()''').

* ''isADatatype(self, dtName)''

Return whether '''dtName''' is a known datatype name for this package.
XSV datatypes are accepted iff option '''xsv''' is set.

For X-Enum and X-Match, `dtName` must include a colon and a named that was
added via '''addEnum()''' or '''addPattern()''' (respectively).

* ''checkValueForType(self, dtName, value)''

Return `True` iff '''value''' (a string) is a valid representation of the
datatype named by '''dtName'''.
If the datatype name is unknown, returns `None`.

* ''addEnum(name, values, ignoreCase=True)''

Define a new enumeration, and give it a name.

* ''addPattern(name, regex, ignoreCase=True)''

Define a new regex to match strings against, and give it a name.
The pattern will always have '^' added at the start, and '$' at the end,
and will be compiled when added.


=Supported types=

See [http://www.w3.org/TR/xmlschema-2/],
"XML Schema Part 2: Datatypes Second Edition."
W3C Recommendation 28 October 2004.

Note that this packages checks '''strings''' against given types. Trying to
text an actual Python int, bool, etc. will raise a TypeError exception.

* ''anyURI'', ''base64Binary'', ''hexBinary''

===Truth values===

* ''boolean''

===Real numbers===

* ''decimal'', ''double'', ''float''

===Various integers===

* ''byte'', ''short'', ''int'', ''integer'', ''long'',
''nonPositiveInteger'', ''negativeInteger'', ''nonNegativeInteger'',
''positiveInteger'', ''unsignedByte'', ''unsignedInt'', ''unsignedLong''

===Dates and times===

* ''date'', ''dateTime'', ''gDay'', ''gMonth'', ''gMonthDay'', ''gYear'', ''gYearMonth'', ''time'', ''duration''

===Strings===

* ''language'', ''normalizedString'', ''string'', ''token''

===XML constructs (note caps)===

* ''ID'', ''IDREF'', ''IDREFS'', ''Name'', ''NCName'', ''NMTOKEN'', ''NMTOKENS'', ''QName''

===A few non-XML-Schema types===

These additions are used by my [XSV] format, and might be useful to others too
(handling them requires '''setOption("xsv", 1)'''):

* ''X-UChar'' -- a single Unicode character.

* ''X-XMLChar'' -- a single Unicode character.

* ''X-ASCII'' -- an ASCII string.

* ''X-HexInt'' -- a hexadecimal unsigned integer
(no leading "0x", "x", etc.).

* ''X-OctInt'' -- an octal unsigned integer.

* ''X-Probability'' -- a `float` inclusively between 0.0 and 1.0.

* ''X-Regex'' -- a valid PCRE (well, Python) regular expression.

* ''X-Enum:[name]'' -- Values must be drawn from the named list (do not include
the square brackets), which in
turn must have been defined via ``addEnum()``. Whether to ignore case can
be specified as an option when defining each enum.

* ''X-Match:[name]'' -- Values must match the named regular expression (do not
include the square brackets), which in
turn must have been defined via ``addPattern)``. Whether to ignore case can
be specified as an option when defining each named pattern.


=Related commands=

==Datatype-related==

[https://github.com/sderose/PYTHONLIBS/blob/master/Record.py]: Similar
to Python `namedtuple`, but supporting type contraints similer to those
of `Homogeneous.py`, as well as value defaults

[https://github.com/sderose/PYTHONLIBS/blob/master/LooseDict.py]:
A subclass of `dict` that includes key normalization. For example, matching
string keys via case-folding or Unicode normalization, or
numeric values with rounding, etc.

[https://github.com/sderose/PYTHONLIBS/blob/master/Homogeneous.py]:
Type-checked lists ad dicts.


==XSD-related==

`XmlRegexes.py`: A collection of relevant regexes for XML.


=Known bugs and limitations=

Unfinished.

May not be happy testing max/min limits on 64-bit integers.

No option for trimming whitespace first.

No option for multiple tokens with `X-Enum` or `X-Match`.

The X- types don't check properly with the driver (at least).


=To do=

* Finish date/time handling.

* Lots more testing.

* Should it accept actual Python data, not just strings?

* Add a type that accepts H-style numbers like 3.2M.

* Possibly integrate with formatting featu8res of `csv2xml.py`, `alogging.py`.


=History=

* Written 2012-05-07 by Steven J. DeRose.
* 2015-05-11: Convert local data to Python inits. Clean up.
* 2020-08-12: New layout. Add X-Probability. Much cleaner regexes.
POD to MarkDown. Add methods for defining and applying specific
regexes and enums. Distinguish "Regex" type from "Match".
* 2020-09-02: Pull in accurate Unicode XML character sets from XmlRegexes.py.
* 2020-09-22: Improve test harness, fix several bugs.


=Rights=

Copyright 2012-05-07 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].
"""


###############################################################################
#
class Datatypes:
    """Define the named datatypes (mostly from XML Schema).
    A few local (non-XML-Schema) types can be added, all starting with "X-".
    Of those, "X-Enum" and "X-Match" are validated specially.
    Each appends an expression used to check it.

    See: [https://www.w3.org/TR/xmlschema-2/] ("Datatypes Second Edition")
    """

    ASCII_NMSTART     = r'[_.A-Z]'
    ASCII_NMCHAR      = r'[-_.:\w]'
    ASCII_NAME        = ASCII_NMSTART + ASCII_NMCHAR + "*"

    xmlChar           = "[\t\n\r\x20-\uD7FF\uE000-\uFFFD]"
    #"\x{00010000}-\x{0010FFFF}"
    xmlSpace          = r"[\t\n\r\x20]"
    xmlNameStartCharList = (
        ":A-Z_a-z\xc0-\xd6\xd8-\xf6\xf8-\u02ff\u0370-\u037d\u037f-\u1fff" +
        "\u200c\u200d\u2070-\u218f\u2c00-\u2fef" +
        "\u3001-\ud7ff\uf900-\ufdcf" + "\ufdf0-\ufffd"
        #"\x{00010000}-\x{000effff}"
    )
    xmlNameCharList   = (r"-.0-9\u00b7\\u0300-\u036f\u203f-\u2040" + xmlNameStartCharList)
    xmlNameStartChar  = r'[' +xmlNameStartCharList+ r']'
    xmlNameChar       = r'[' +xmlNameCharList+ r']'

    NAME = xmlNameStartChar + xmlNameChar + "*"
    year = r'\d\d\d\d'
    mon  = r'\d\d'
    day  = r'\d\d'
    date = year + '-' + mon + '-' + day
    time = r'\d\d:\d\d:\d\d(\.\d+)'
    zone = r'([-+]\d\d:\d\d|Z)?'

    uns  = r'\d+'
    fix  = r'[-+]?\d+'
    posi = r'\+?0*[1-9]\d*'
    neg  = r'\-?0*[1-9]\d*'
    mant = r'[-+]?\d+(\.\d+)?'
    expt = r'([eE][-+]?\d+)?'
    flo  = '('+mant+expt+')'+r'|INF|-INF|NaN'

    uri  = r'[a-zA-Z0-9-_.+!*,();\/?:\=&%]+'
    xd   = r'[0-9a-fA-F]'

    __DatatypeData__ = {
        # name:              (regex,             min,  max,  pyType),
        ### Net constructs
        "anyURI":            (uri,               None, None, str),
        "base64Binary":    (r'[+\/=a-zA-Z0-9]+', None, None, str),
        "hexBinary":     (r'(%s%s)+' % (xd, xd), None, None, str),

        ### Truth values
        "boolean":           (r'1|0|True|False', None, None, bool),

        ### Real numbers
        "decimal":           ('('+mant+')',      None, None, float),
        "double":            (flo,               None, None, float),
        "float":             (flo,               None, None, float),

        ### Various integers
        "byte":              (fix,               -(1<< 8), (1<< 8) - 1, int),
        "short":             (fix,               -(1<<16), (1<<16) - 1, int),
        "int":               (fix,               -(1<<32), (1<<32) - 1, int),
        "integer":           (fix,               -(1<<32), (1<<32) - 1, int),
        "long":              (fix,               -(1<<64), (1<<64) - 1, int),

        "nonPositiveInteger":(r'(-\d+)|0+',      -(1<<32),  0,      int),
        "negativeInteger":   (neg,               -(1<<32), -1,      int),
        "nonNegativeInteger":(r'\+?\d+',         0,  (1<<32) - 1,   int),
        "positiveInteger":   (posi,              1,  (1<<32) - 1,   int),

        "unsignedByte":      (posi,              0,  0x7F,          int),
        "unsignedShort":     (posi,              0,  0x7FFF,        int),
        "unsignedInt":       (posi,              0,  0x7FFFFFFF,    int),
        "unsignedLong":      (posi,              0,  0x7FFFFFFFFFFFFFFF, int),

        ### Dates and times (unfinished)  TODO: Check vs. XML Schema Datatypes
        "gDay":              (r'\d+',            1,     366, int),
        "gMonth":            (mon,               1,      12, int),
        "gMonthDay":         (mon+'-'+day,       1,      31, str),
        "gYear":             (year,              None, None, int),
        "gYearMonth":        (year+'-'+mon,      0,      12, str),
        "date":              (date,              None, None, str),
        "dateTime":  (date + 'T' + time + zone,  None, None, str),
        "time":              (time + zone,       None, None, str),
        "duration":          (r'[-/\d]+',        None, None, int),

        ### Strings
        "language":          (r'\w[.:\w]+',      None, None, str),
        "normalizedString":  (r'[^\r\n\t]*',     None, None, str),
        "string":            (r'.*',             None, None, str),
        "token":             (r'\S(\S+)',        None, None, str),

        ### XML constructs (note caps)
        "ID":                (NAME,              None, None, str),
        "IDREF":             (NAME,              None, None, str),
        "IDREFS":    (NAME+r'(\s+'+NAME+r')*',   None, None, str),
        "Name":              (NAME,              None, None, str),
        "NCName":            (NAME,              None, None, str),
        "NMTOKEN":           (NAME,              None, None, str),
        "NMTOKENS":  (NAME+r'(\s+'+NAME+r')*',   None, None, str),
        "QName":     (NAME+':'+NAME,             None, None, str),
    }

    __xsvDatatypeData__ = {  # A few non-XML-Schema types
        #"X-Enum":      [SPECIAL]
        #"X-Match":     [SPECIAL]
        "X-Regex":           (None,              None, None, str),
        "X-UChar":           (r'.',              None, None, str),
        "X-XMLChar":         (r'.',              None, None, str),
        "X-ASCII":           (r'[[:ASCII:]]*',   None, None, str),
        "X-HexInt":          (r'([0-9a-fA-F]+)', None, None, str),
        "X-OctInt":          (r'([0-7]+)',       None, None, str),
        "X-Probability":     (flo,               0.0,  1.0, float),
    }

    def __init__(self):
        self.options = {
            "quiet":       False,
            "xsv":         False,
        }
        self.exprs = {}
        self.enums = {}
        self.patts = {}

        for k2 in (Datatypes.__DatatypeData__):
            v = Datatypes.__DatatypeData__[k2]
            try:
                self.exprs[k2] = re.compile(r'^(' + v[0] + r')$')
            except Exception as e0:
                self.warning("Datatypes: Bad regex for %-20s '%s':\n    %s" %
                    (k2, v[0], e0))

    def warning(self, msg):
        if (self.options["quiet"]): return
        sys.stderr.write(msg+"\n")

    def setOption(self, name, value):
        self.options[name] = value

    def getOption(self, name):
        return self.options[name]

    def addEnum(self, name, values, ignoreCase=True):
        """Add a named enum type, referencable as 'X-Enum:name'.
        """
        newEnum = {}
        for v in values:
            v = v.upper() if (ignoreCase) else v
            if (not re.match('^'+Datatypes.NAME+'$', v)):
                raise ValueError("enum value '%s' for '%s' is not a NAME." %
                    (v, name))
            newEnum[v] = ignoreCase
        self.enums[name] = newEnum

    def addPattern(self, name, regex, ignoreCase=True):
        """Add a named string type constrainted by a given regex, and
        referencable as 'X-Match:name'.
        """
        fullRegex = r'^' + regex + r'$'
        if (ignoreCase): self.patts[name] = re.compile(fullRegex, re.I)
        else: self.patts[name] = re.compile(fullRegex)

    def isADatatype(self, dtName):
        """Test whether a given datatype name (potentially including the
        appended expression for X-Enum and X-Regex) is known.
        Whether the X- extensions are known, depends on the 'xsv' option.
        """
        if (Datatypes.__DatatypeData__): return True
        if (self.options["xsv"]):
            if (dtName in Datatypes.__xsvDatatypeData__): return True
            if (dtName.startswith("X-Enum:") and
                self.isEnum(dtName)): return True
            if (dtName.startswith("X-Match:") and
                self.isPatt(dtName)): return True
        return False

    def checkValueForType(self, dtName, value):
        """Test whether the given (string) value is of the named datatype.

        TODO: Distinguish inclusive vs. exclusive ranges.
        """
        if (dtName in self.exprs):
            if (not re.match(self.exprs[dtName], value)):
                return False
            minV = Datatypes.__DatatypeData__[dtName][1]
            if (minV is not None and float(value) < minV):
                return False
            maxV = Datatypes.__DatatypeData__[dtName][2]
            if (maxV is not None and float(value) > maxV):
                return False
            return True

        if (self.options["xsv"]):
            return self.tryXSV(dtName, value)

        raise ValueError("Unrecognized type '%s'." % (dtName))

    def tryXSV(self, dtName, value):
        """Called when the 'xsv' option is on, to handle those cases.
        """
        if (dtName == 'X-Regex'):
            try:
                re.compile(value)
                return True
            except Exception:
                return False

        elif (dtName.startswith("X-Enum:")):
            enumName = dtName[7:]
            if (enumName not in self.enums):
                raise ValueError("No enum named '%s' defined." % (enumName))
            if (self.enums[enumName]):  # ignore case
                value = value.upper()
            return (value in self.enums[enumName])

        elif (dtName.startswith("X-Matches:")):
            pattName = dtName[10:]
            if (pattName not in self.patts):
                raise ValueError("No pattern named '%s' defined." % (enumName))
            return re.match(self.patts[pattName], value)

        raise ValueError("Unrecognized type '%s'." % (dtName))

    def isEnum(self, dtName):
        pass

    def isPatt(self, dtName):
        pass

    def castToPython(self, value, dtName):
        theType = Datatypes.__DatatypeData__[dtName][3]
        return theType(value)


###############################################################################
#
if __name__ == "__main__":
    import argparse
    from BlockFormatter import BlockFormatter

    def anyInt(x):
        return int(x, 0)

    def processOptions():
        parser = argparse.ArgumentParser(
            description=descr,
            formatter_class=BlockFormatter
        )
        parser.add_argument(
            "--list", action='store_true',
            help='Show a list of the known types.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version',
            version="%s (Python %s)" % (__version__, sys.version_info[0]),
            help='Display version information, then exit.')

        parser.add_argument(
            'strings', type=anyInt, nargs=argparse.REMAINDER,
            help='Strings to try against datatypes.')

        args0 = parser.parse_args()

        return args0

    # Some test data, as tuples of (typeName, expected result, string
    #
    testStrings = [
        ### Wonky strings
        ( "anyURI",                 True,  'http://example.com/foo.html#bar' ),
        ( "base64Binary",           True,  'AMERICANstuff' ),
        ( "hexBinary",              True,  'DEADBEEF' ),

        ### Truth values
        ( "boolean",                False, '' ),

        ### Real numbers
        ( "decimal",                True,  '134217727' ),
        ( "double",                 True,  '-3.1415926535' ),
        ( "float",                  True,  '1' ),

        ### Various integers
        ( "byte",                   True,  '255' ),
        ( "short",                  True,  '65535' ),
        ( "int",                    True,  '12' ),
        ( "integer",                True,  '12' ),
        ( "long",                   True,  '99999999' ),

        ( "nonPositiveInteger",     True,  '-12' ),
        ( "negativeInteger",        True,  '-1' ),
        ( "nonNegativeInteger",     True,  '0' ),
        ( "positiveInteger",        True,  '1776' ),

        ( "unsignedByte",           True,  '127' ),
        ( "unsignedShort",          True,  '32767' ),
        ( "unsignedShort",          False, 'ersatz' ),
        ( "unsignedShort",          False, '65535' ),
        ( "unsignedInt",            False, '2**31' ),

        ### Dates and times         True,  '' ),
        ( "gDay",                   True,  '123' ),
        ( "gMonth",                 True,  '12' ),
        ( "gMonthDay",              True,  '12-31' ),
        ( "gYear",                  True,  '2525' ),
        ( "gYearMonth",             True,  '1942-01' ),
        ( "date",                   True,  '1960-04-02' ),
        ( "dateTime",               True,  '1960-04-02T23:59:59+03:00' ),
        ( "time",                   True,  '23:59:59.999Z' ),
        ( "duration",               True,  '3600' ),

        ### Strings
        ( "language",               True,  'EN.US' ),
        ( "normalizedString",       True,  'This  is  a string. ' ),
        ( "string",                 True,  'uchambuzi' ),
        ( "token",                  True,  'DIV3' ),

        ### XML constructs          True,  '' ),
        ( "ID",                     True,  'DIV3' ),
        ( "IDREF",                  True,  'MY_id_17.2' ),
        ( "IDREFS",                 True,  'A1 A2  A3  ' ),
        ( "Name",                   True,  'bazingaTag' ),
        ( "Name",                   False, '999bazingaTag' ),
        ( "NCName",                 True,  'p12-a_2.ix' ),
        ( "NMTOKEN",                False, ' 999' ),
        ( "NMTOKENS",               True,  ' aardvark beefalo' ),
        ( "QName",                  True,  'svg:g' ),

        # ( "X-Enum",      [SPECIAL]
        # ( "X-Match",     [SPECIAL]
        # ( "X-Regex",     [SPECIAL]
        ( "X-UChar",                True,  'x' ),
        ( "X-UChar",                True,  "\u2402" ),

        ( "X-XMLChar",              True,  'x' ),
        ( "X-XMLChar",              False, "\x27" ),

        ( "X-ASCII",                True,  '!' ),
        ( "X-ASCII",                False, "\u2402" ),

        ( "X-HexInt",               True,  'deadBEEF' ),
        ( "X-HexInt",               False, '123G' ),
        ( "X-HexInt",               False, '0x01' ),

        ( "X-OctInt",               True,  '007' ),
        ( "X-OctInt",               False, '082' ),

        ( "X-Probability",          True,  '0.99' ),
        ( "X-Probability",          True,  '50E-2' ),
        ( "X-Probability",          False,  '1.99' ),
        ( "X-Probability",          False,  '-0.5' ),
    ]

    ###########################################################################
    # Main
    #
    args = processOptions()

    dt = Datatypes()

    if (args.list):
        for k in sorted(dt.__DatatypeData__.keys()):
            regex0, minVal, maxVal, pyType = dt.__DatatypeData__[k]
            print("%-20s (->%-8s): /%s/" % (k, pyType.__name__, regex0))
        sys.exit()

    nPass = nFail = 0
    if (not args.strings):
        for typeName, isOK, s in testStrings:
            print("%-20s [%5s] for '%s'" %
                (typeName, isOK, s))
            try:
                rc = dt.checkValueForType(typeName, s)
            except ValueError as e:
                print("    ERROR: %s" % (e))
            if (rc == isOK):
                print("    PASS")
                nPass += 1
            else:
                print("    FAIL")
                nFail += 1
    print("\nDone. %d pass, %d fail, %6.2f%%." %
        (nPass, nFail, 100.0*nPass/(nPass+nFail)))
    sys.exit()
