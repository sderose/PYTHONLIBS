#!/usr/bin/env python
#
# Homogeneous.py: Implement homogeneous subclasses of list, dict, etc.
#
# 2020-02-19: Written. Copyright by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse

__metadata__ = {
    'title'        : "Homogeneous.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-02-19",
    'modified'     : "2020-02-19",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Subclasses of `list` and `dict` that enforce the datatypes of keys and/or values.

For example:

    myDict = hdict(keyType=str, valueType=int)
    myDict['fooBar'] = 12
    myDict[12] = 'foo'

Attempts to add, access, or replace items using the wrong datatypes,
will raise a `TypeError` exception.

If you set `valueNone=True`, then `None` is also an acceptable value.

If the required type is a class name, you can choose whether subclasses are
acceptable or not (default: True)

    myList = hlist(valueType=someClass, valueSubs=False)

If desired, set `valueTest` to a function that returns True only for values
that are acceptable:

    probabilityList = hlist(valueType=float,
        valueTest = lambda x: (x>=0.0 and x<=1.0))

or

    ages = hlist(keyType=str, keyTest = lambda s: re.match(r'\\w+', x),
        valueType=int, valueTest = lambda x: (x>=0 and x<=130))

Other operations are all intended to work normally.

=Related Commands=

`LooseDict`

=Known bugs and Limitations=

There is no way to constrain the size of the hlist or hdict itself.

Perhaps `valueTest` failures should raise ValueError instead of TypeError,
but I decided to just use TypeError for everything.

=Ownership=

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see L<http://www.derose.net/steve/utilities> or
L<http://github/com/sderose>.

=History=

=Options=
"""


###############################################################################
#
class hlist(list):
    def __init__(self, valueType:type=None, valueSubs:bool=True,
        valueNone:bool=False, valueTest=None):
        super(hlist, self).__init__()
        self.valueType = valueType
        self.valueSubs = valueSubs
        self.valueNone = valueNone
        self.valueTest = valueTest

    def __setitem__(self, n, value):
        if (not self.valueNone and value is None):
            raise TypeError("hlist requires non-None value.")
        if (self.valueType is not None and not isinstance(value, self.valueType)):
            raise TypeError("hlist requires values of type %s, but got %s." %
                self.valueType, type(value))
        if (self.valueTest is not None and not self.valueTest(value)):
            raise TypeError("hlist value %s fails required test." % (value))
        self[n] = value


###############################################################################
#
class hdict(dict):
    """
    """
    def __init__(self,
        keyType=None, keySubs:bool=True, keyNone:bool=False, keyTest=None,
        valueType:type=None, valueSubs:bool=True, valueNone:bool=False, valueTest=None):
        super(hdict, self).__init__()
        self.keyType = keyType
        self.keySubs = keySubs
        self.keyNone = keyNone
        self.keyTest = keyTest
        self.valueType = valueType
        self.valueSubs = valueSubs
        self.valueNone = valueNone
        self.valueTest = valueTest

    def __setitem__(self, key, value):
        super(hdict, self).__setitem__(key, value)
        if (not self.keyNone and key is None):
            raise TypeError("hlist requires non-None key.")
        if (self.keyType is not None and not isinstance(key, self.keyType)):
            raise TypeError("hlist requires keys of type %s, but got %s." %
                self.keyType, type(key))
        if (not self.valueNone and value is None):
            raise TypeError("hlist requires non-None value.")
        if (self.valueType is not None and not isinstance(value, self.valueType)):
            raise TypeError("hlist requires values of type %s, but got %s." %
                self.valueType, type(value))
        self[key] = value


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
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

        args0 = parser.parse_args()
        return args0

    ###########################################################################
    #
    args = processOptions()
    print("Testing...")

    ld = hdict()
    ld['foobar'] = 12

    if (not args.quiet):
        sys.stderr.write("Done.\n")
