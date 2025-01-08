#!/usr/bin/env python3
#
# homogeneous: Implement homogeneous subclasses of list, dict, etc.
# 2020-02-19: Written by Steven J. DeRose.
#
import sys
import argparse
from typing import Union, List, Tuple, Any, Callable, Iterable

__metadata__ = {
    "title"        : "homogeneous",
    "description"  : "Implement homogeneous subclasses of list, dict, etc.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2020-02-19",
    "modified"     : "2024-10-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Subclasses of `list` and `dict` that enforce the datatypes of keys and/or values.

For example, `hlist` implements a homogeneous `list`:

    myList = hlist(valueType=int)

ensures that `myList` will only include items of type `int`. This mainly just
involves the __setitem__ method to do some tests and raise `TypeError` if
a test fails.

`hdist` is analogous, but for `dict`. It can constrain either the key type,
the value type, or both. For example:

    myDict = hdict(keyType=str, valueType=int)

Attempts to add, replace items using the wrong datatypes
will raise a `TypeError` exception. So the first following line is fine,
but the second will raise TypeError (for two reasons, actually: both the
key and the value are of the wrong types):

    myDict['fooBar'] = 12
    myDict[12] = 'foo'

See the next section for how types are checked, and for more options.


==Constraint details==

You can set several properties regarding each thing to be constrained.
The following descriptions use value-constraints for example, but
key constraints work the same way.

* `valueType`: This should be a defined type, such as
`int`, `float`, `complex`, `bool`, `str`, or a class name.

* `valueNone:bool`: If set to True (which is ''not'' the default), then
the value `None` is acceptable.

* `valueTest`: This defaults to `None`, but can be set to a function
that shouild return True only for values that are acceptable. For example,
you can constrain a list to contain only valid probability values like this:

    probabilityList = hlist(valueType=float,
        valueTest = lambda x: (x>=0.0 and x<=1.0))

or

    ages = hlist(keyType=str, keyTest = lambda s: re.match(r'\\w+', x),
        valueType=int, valueTest = lambda x: (x>=0 and x<=130))


=API=

* class hlist(self, valueType:type=None,
valueNone:bool=False, valueTest=None)

This is an extension of the normal Python `list` type, that requires all
members to be of the same type.
"None" is permitted as an item only if valueNone is set.

* class hdict(self, keyType=None, keyNone:bool=False, keyTest=None,
valueType:type]:type=None, valueNone:bool=False, valueTest=None)

This is an extension of the norml Python `dict` type. You can constrain
the type for keys (typically but not necessarily to `str`), and/or the
values.


=Related Commands=

[https://github.com/sderose/PYTHONLIBS/blob/master/Record.py]: Similar
to Python `namedtuple`, but supporting type contraints similer to those
of `homogeneous.py`, as well as value defaults

[https://github.com/sderose/PYTHONLIBS/blob/master/loosedict.py]:
A subclass of `dict` that includes key normalization. For example, matching
string keys via case-folding or Unicode normalization, or
numeric values with rounding, etc.

[https://github.com/sderose/PYTHONLIBS/blob/master/Datatypes.py]:
Support a wide range of named datatype, including XSD's built-ins.


=Known bugs and Limitations=

Perhaps `valueTest` failures should raise ValueError instead of TypeError,
but I decided to just use TypeError for everything.


=To do=

* Perhaps add set, tuple, and others?

`Record` is largely the same but for `namedtuple`.

Should probably add the same idea for other Python container types:
set, frozenset, defaultdict, dequeue, Counter, OrderedDict....


=History=

2020-02-19: Written by Steven J. DeRose.
2020-11-21: Better doc.
2024-10-03: Remove keySubs/valueSubs. Support Tuples of keyType/valueType.
Type-hint valueTest args.
2025-01-08: Tape the tuples of types back out. Implement keyTest and valueTest.


=Rights=

Copyright 2020-02-19 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
class hlist(list):
    """A Python list, but with all values required to be same type.
    @param valueType: what class is allowed as members
    @param valueNone: Is None allowed?
    @param valueTest: a callback to check the values, in addition to
    the type-check implied by valueType.
    """
    def __init__(self,
        valueType:type=None,
        valueNone:bool=False,
        valueTest:Callable=None
        ):
        super(hlist, self).__init__()
        self.valueType = valueType
        self.valueNone = valueNone
        self.valueTest = valueTest

    def __setitem__(self, n, value):
        self._verifyValue(value)
        self[n] = value

    def _verifyValue(self, value) -> None:
        if value is None:
            if self.valueNone: return
            raise TypeError("hlist requires non-None value.")
        if self.valueType is not None and not isinstance(value, self.valueType):
            raise TypeError("hlist requires values of type %s, but got %s."
                % (self.valueType.__name__, type(value).__name__))
        if self.valueTest is not None and not self.valueTest(value):
            raise TypeError("hlist value %s fails required test." % (value))
        return

    def append(self, value:Any) -> None:
        self._verifyValue(value)
        super().append(value)

    def extend(self, values:Iterable) -> None:
        for value in values: self._verifyValue(value)
        super().extend(values)

    #def insert  # TODO insert()


###############################################################################
#
class hdict(dict):
    """A Python dict, but with all keys and/or items required to be same type.
    """
    def __init__(self,
        keyType=None,
        keyNone:bool=False,
        keyTest=None,
        valueType:type=None,
        valueNone:bool=False,
        valueTest=None
        ):
        super(hdict, self).__init__()
        self.keyType = keyType
        self.keyNone = keyNone
        self.keyTest = keyTest
        self.valueType = valueType
        self.valueNone = valueNone
        self.valueTest = valueTest

    def __setitem__(self, key, value):
        self._verifyKeyAndValue(key, value)
        super(hdict, self).__setitem__(key, value)

    def _verifyKeyAndValue(self, key, value) -> None:
        if key is None:
            if not self.keyNone:
                raise TypeError("hdict requires non-None key.")
        elif self.keyType is not None and not isinstance(key, self.keyType):
            raise TypeError("hdict requires keys of type %s, but got %s." %
                (self.keyType.__name__, type(key).__name__))
        if self.keyTest and not self.keyTest(key):
            raise TypeError("hdict key '%s' does not pass keyTest." % (key))

        if value is None:
            if not self.valueNone:
                raise TypeError("hdict requires non-None value.")
        elif self.valueType is not None and not isinstance(value, self.valueType):
            raise TypeError("hdict requires values of type %s, but got %s." %
                (self.valueType.__name__, type(value).__name__))
        if self.valueTest and not self.valueTest(value):
            raise TypeError("hdict value '%s' does not pass valueTest." % (value))

        return
