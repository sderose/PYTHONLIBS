#!/usr/bin/env python
#
# Datatypes.py
#
# Written 2012-05-07 by Steven J. DeRose.
# 2015-05-11: Convert local data to Python inits. Clean up.
#
# To do:
#     Finish date/time handling.
#     Make nonPositiveInteger and nonNegativeInteger deal with -0.
#
from __future__ import print_function
import sys, re

from sjdUtils import sjdUtils
from alogging import ALogger


###############################################################################
###############################################################################
#
class Datatypes:
    """Define the named datatypes (mostly from XML Schema).
    A few local (non-XML-Schema) types are defined, all starting with "X-".
    Of those, "X-Enum" and "X-Regex" are validated specially.
    Each appends an expression used to check it.
    """

    NAME = r"[_.\w][-_.:\w\d]*"   # Too loose, doesn't exclude ^\d
    fix  = r'[-+]?\d+'
    mant = r'[-+]?\d+(\.\d+)?'
    expt  = r'([eE][-+]?\d+)?'

    datatypedata = {  # Name: (Expr, Min, Max)
        ### Net constructs
        "anyURI":       (r'([a-zA-Z0-9-_.+!*,();\/?:\=&%]Q)+',	None, None),
        "base64Binary": (r'[+\/=a-zA-Z0-9]+',	                None, None),
        "hexBinary":    (r'([0-9a-fA-F][0-9a-fA-F])+',	        None, None),

        ### Truth values
        "boolean":  (r'1|0|True|False',  	                    None, None),

        ### Real numbers
        "decimal":  ('('+mant+')',	                            None, None),
        "double":   ('('+mant+expt+')'+r'|INF|-INF|NaN',	    None, None),
        "float":    ('('+mant+expt+')'+r'|INF|-INF|NaN',	    None, None),

        ### Various integers
        "byte":                 (fix,		-(1 <<  8), (1 <<  8) - 1 ),
        "short":                (fix,		-(1 << 16), (1 << 16) - 1 ),
        "int":                  (fix,		-(1 << 32), (1 << 32) - 1 ),
        "integer":              (fix,		-(1 << 32), (1 << 32) - 1 ),
        "long":                 (fix,		-(1 << 64), (1 << 64) - 1 ),

        "nonPositiveInteger":   (r'(-\d+)|0+',	    -(1 << 32),  0 ),
        "negativeInteger":	    (r'-\d+',		    -(1 << 32), -1 ),
        "nonNegativeInteger":   (r'\+?\d+',	        0,  (1 << 32) - 1 ),
        "positiveInteger":	    (r'\+?\d+',	        1,  (1 << 32) - 1 ),

        "unsignedByte": (r'\+?\d+',    		        0,  0x7F ),
        "unsignedShort":(r'\+?\d+',	    	        0,  0x7FFF ),
        "unsignedInt":  (r'\+?\d+',		            0,  0x7FFFFFFF ),
        "unsignedLong": (r'\+?\d+',		            0,  0x7FFFFFFFFFFFFFFF),

        ### Dates and times (unfinished)
        "date":         (r'[-/\d]+',	        	None, None ),
        "dateTime":     (r'[-/:\d]+',	    	    None, None ),
        "gDay":         (r'[\d]+',		            0,     366 ),
        "gMonth":       (r'[\d]+',		            0,      12 ),
        "gMonthDay":    (r'[-/\d]+',		        0,      31 ),
        "gYear":        (r'[\d]+',	    	        None, None ),
        "gYearMonth":   (r'[-/\d]+',		        0,      12 ),
        "time":         (r'[-:.\d]+',	    	    None, None ),
        "duration":     (r'[-/\d]+',	    	    None, None ),

        ### Strings
        "language":         (r'\w[.:\w]+',	        None, None ),
        "normalizedString": (r'[^\r\n\t]*',         None, None ),
        "string":           (r'.*',	        	    None, None ),
        "token":            (r'\S(\S+)',            None, None ),

        ### XML constructs (note caps)
        "ID":           (NAME,    		            None, None ),
        "IDREF":        (NAME,	    	            None, None ),
        "IDREFS":       (NAME+r'(\s+'+NAME+r')*',   None, None ),
        "Name":         (NAME,    		            None, None ),
        "NCName":       (NAME,	    	            None, None ),
        "NMTOKEN":      (NAME,	    	            None, None ),
        "NMTOKENS":     (NAME+r'(\s+'+NAME+r')*',   None, None ),
        "QName":        (NAME+':'+NAME,		        None, None ),
    }

    xsvdatatypedata = {  # A few non-XML-Schema types
        "X-Enum":       (r'#',	                    None, None ), #...
        "X-Regex":      (r'.+',	                    None, None ), #...
        "X-Char":       (r'.',	                    None, None ),
        "X-ASCII":      (r'[[:ASCII:]]*',	        None, None ),
        "X-HexInt":     (r'([0-9a-fA-F]+)',	        None, None ),
        "X-OctInt":     (r'([0-7]+)',	            None, None ),
    }

    def __init__(self, su=None):
        self.options = {
            "quiet":       0,
            "xsv":         0,
        }
        self.su         = su or sjdUtils()
        self.exprs      = {}
        for k, v in (Datatypes.datatypedata.items()):
            try:
                self.exprs[k] = re.compile(r'^(' + v[0] + r')$')
            except Exception as e:
                self.warn("Datatypes: Bad regex for %-20s '%s':\n    %s" %
                    (k, v[0], e))

    def warn(self, msg):
        if (self.options["quiet"]): return
        sys.stderr.write(msg+"\n")

    def setOption(self, name, value):
        self.options[name] = value

    def getOption(self, name):
        return(self.options[name])

    def isDatatype(self, dtName):
        """Test whether a given datatype name (potentially including the
        appended expression for X-Enum and X-Regex) is known.
        Whether the X- extensions are known, depends on the 'xsv' option.
        """
        if (self.options["xsv"] and
            (dtName in Datatypes.xsvdatatypedata or
             dtName.startswith("X-Enum") or
             dtName.startswith("X-Regex"))): return(True)
        return(dtName in Datatypes.datatypedata)

    def checkValueForType(self, dtName, value):
        """Test whether the given (string) value is of the named datatype.
        If the datatype name is unknown, returns None.
        """
        if (dtName in self.exprs):
            if (not re.match(self.exprs[dtName], value)):
                return(0)
            min = Datatypes.datatypedata[dtName][1]
            if (min is not None and float(value) < min):
                return(0)
            max = Datatypes.datatypedata[dtName][2]
            if (max is not None and float(value) > max):
                return(0)
            return(1)

        if (self.options["xsv"]):
            return(self.tryXSV(dtName, value))

        return(None)


    def tryXSV(self, dtName, value):
        """Called when the 'xsv' option is on, to handle those cases.
        """
        if (dtName.startswith("X-Enum\t")):
            enumVals = re.split(r'\s+', dtName)
            enumVals.pop()
            return(value in enumVals)

        elif (dtName.startswith("X-Regex\t")):
            try: x = re.compile(r'^' + value + r'$')
            except Exception as e: return(None)
            return(re.match(x, value))

        elif (dtName in Datatypes.xsvdatatypedata):
            return(re.match(Datatypes.xsvdatatypedata[dtName], value))

        self.warn("Datatypes.tryXSV: Shouldn't be here.")
        return(0)


###############################################################################
###############################################################################
#

perldoc = """

=pod

=head1 Usage

import Datatypes

Provide checking for whether strings represent values conforming
to XSD built-in datatypes.

If you set option I<xsv>, a few more types are supported, as described below.



=head1 Methods

=over

=item * B<setOption(self, name, value)>

The options include:

=over

=item * I<quiet>

=item * I<xsv> -- Include support for XSV extension datatyps.
Default: I<False>.

=back

=item * B<getOption(self, name)>

=item * B<isDatatype(self, dtName)>

Return whether I<dtName> is a known datatype name for this package.
XSV datatypes are accepted iff option I<xsv> is set.

=item * B<checkValueForType(self, dtName, value)>

Return C<True> iff I<value> (a string) is a valid representation of the
datatype named by I<dtName>.
If the datatype name is unknown, returns None.


=back


=head1 Supported types

See L<http://www.w3.org/TR/xmlschema-2/>,
"XML Schema Part 2: Datatypes Second Edition."
W3C Recommendation 28 October 2004.

=over

=item * B<anyURI>

=item * B<base64Binary>

=item * B<hexBinary>

=back


=head3 Truth values

=over

=item * B<boolean>

=back


=head3 Real numbers

=over

=item * B<decimal>

=item * B<double>

=item * B<float>

=back


=head3 Various integers

=over

=item * B<byte>

=item * B<short>

=item * B<int>

=item * B<integer>

=item * B<long>


=item * B<nonPositiveInteger>

=item * B<negativeInteger>

=item * B<nonNegativeInteger>

=item * B<positiveInteger>


=item * B<unsignedByte>

=item * B<unsignedInt>

=item * B<unsignedLong>

=back


=head3 Dates and times

B<These are not yet unfinished>

=over

=item * B<date>

=item * B<dateTime>

=item * B<gDay>

=item * B<gMonth>

=item * B<gMonthDay>

=item * B<gYear>

=item * B<gYearMonth>

=item * B<time>

=item * B<duration>

=back


=head3 Strings

=over

=item * B<language>

=item * B<normalizedString>

=item * B<string>

=item * B<token>

=back


=head3 XML constructs (note caps)

=over

=item * B<ID>

=item * B<IDREF>

=item * B<IDREFS>

=item * B<Name>

=item * B<NCName>

=item * B<NMTOKEN>

=item * B<NMTOKENS>

=item * B<QName>

=back


=head3 A few non-XML-Schema types

These additions are used by L<XSV>
(handling them requires I<setOption("xsv", 1)>):

=over

=item * B<X-Enum> -- an enumeration of XML NAMEs, separated by whitespace.

=item * B<X-Regex> -- any string matching a regex (otherwise specified).
In XSV, the regex appears after "X-Regex" in the datatype declaration (which
is in the value of the relevant attribute, on the <Head> element),
separated by a single tab.

=item * B<X-Char> -- a single Unicode character.

=item * B<X-ASCII> -- an ASCII string
(equivalent to C<X-Regex\t[[:ASCII:]]*>).

=item * B<X-HexInt> -- a hexadecimal unsigned integer
(no leading "0x", "x", etc.).

=item * B<X-OctInt> -- an octal unsigned integer.

=back



=head1 Known bugs and limitations

Unfinished.

May not be happy testing max/min limits on 64-bit integers.



=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see L<http://creativecommons.org/licenses/by-sa/3.0/>.

For the most recent version, see L<http://www.derose.net/steve/utilities/>.

=cut
"""
