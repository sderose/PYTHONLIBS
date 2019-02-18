#!/usr/bin/env python
#
# DictTuple.py: A cross between namedtuple and dict.
#
# To do:
#
from __future__ import print_function
from collections import namedtuple

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-06-09",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-11-15",
}
__version__ = __metadata__['version_date']


###############################################################################
#
DictTupleDefItem = namedtuple('DictTupleItem',
    ['name', 'type', 'default', 'nullable' ])

class DictTupleDef:
    def __init__(self, name, items=None):
        self.name = name
        self.locked = False
        self.items = {}
        if (items is None): return
        assert (isinstance(items, list)
        for item in items:
            assert (isinstance(item, list) and len(item) = 4)
            self.items[item[0]] = self.defineItem(item[0], item[1], item[2], item[3])

    def lock(self):
        self.locked = True

    def defineItem(self, name, typ=None, dft=None, nullable=True):
        if (name in self.items):
            raise KeyError("item '%s' already defined." % (name))
        return DictTupleDefItem(name, typ, dft, nullable)

class DictTuple(dict):
    def __init__(self, dfn):
        super(DictTuple, self).__init__()
        if (not isinstance(dfn, DictTupleDef)):
            raise TypeError("Not a DictTupleDef.")
        self.dfn = dfn

    def __setitem__(self, key, value):
        """
        See https://stackoverflow.com/questions/2060972/
        """
        if (key not in self.dfn.items):
            raise KeyError("item '%s' not defined." % (key))
        it = self.dfn.items[key]
        if (it['type'] and not isinstance(value, it['type'])):
            raise TypeError("value for item '%s' is type %s (need %s)." %
                (key, type(value), it['type']))
        if (value is None and not it['nullable']):
            raise TypeError("value for item '%s' may not be None." % (key))
        super(DictTuple, self).__setitem__(key, value)

    def isValid(self):
        for key, value in self.dfn.items.items():
            if (key not in self.dfn.items):
                raise KeyError("item '%s' not defined." % (key))
            it = self.dfn.items[key]
            if (it['type'] and not isinstance(value, it['type'])):
                raise TypeError("value for item '%s' is type %s (need %s)." %
                    (key, type(value), it['type']))
            if (value is None and not it['nullable']):
                raise TypeError("value for item '%s' may not be None." % (key))
        return True


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    descr = """
=pod

=head1 Description

This is a subclass of I<dict>, that is a cross between I<namedtuple> and I<dict>.
Features include:

=over

=item * Like I<namedtuple>, you create a new class that knows a specific
set of named items. Instances can contain only those items.

=item * Like I<dict>, it is mutable, and the members are unordered.

=item * Like I<defaultdict>, you can set a default (for each item).

=item * Like none of these, you can specify a datatype (for each item),
and whether an assigned value must be exactly that type, a subclass,
or castable (not yet implemented).

=item * You can also specify whether None is an acceptable value.

=back

=head1 Usage

To instantiate a DictTuple, you need to pass a name, and a list of the allowed
items. This is like I<namedtuple>, except that each item is more than just
a name; it is a 4-tuple containing these 4 features:
    ['name', 'type', 'default', 'nullable' ]

This 4-tuple is internally defined as a namedtuple called I<DictTupleItem>. You
can make these ahead of time, or just pass in lists or tuples of the 4 featurs.

=head1 Methods

=head1 Known bugs and limitations

B<Unfinished>

Need to be clear about the notion of constraining what keys are allowed in the
dict, and what the structure of the values is. This should be just about the former.

=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see http://www.derose.net/steve/utilities/.

=cut
"""
    import argparse

    def processOptions():
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')
        parser.add_argument(
            'files', type=str, nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')
        args0 = parser.parse_args()
        return(args0)

    class EmpRecord:
        def __init__(self):
            self.exist = True

    args = processOptions()

    print("Unfinished")
    myItems = [
        # 'name',   'type', 'default', 'nullable'
        [ 'fName',  str,    None,      False ],
        [ 'lName',  str,    None,      False ],
        [ 'age',    int,    None,      True ],
        [ 'state',  str,    [ 'AK', 'HI', 'WA' ], True ],
        [ 'info',   EmpRecord, None,   True ],

    dt = DictTuple(
