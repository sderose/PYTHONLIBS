#!/usr/bin/env python3
#
# LooseDict.py: Enhance dict to handle case-ignorant or similar lookups.
# 2018-09-04: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import unicodedata
import re
from typing import Any, List, Callable

__metadata__ = {
    'title'        : "LooseDict.py",
    'description'  : "Enhance dict to handle case-ignorant or similar lookups.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2018-09-04",
    'modified'     : "2021-07-08",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

A subclass of `dict` that stores keys and values exactly as passed,
but indexes them under a normalized form, such as folded to lowercase.
For example:

    myDict = LooseDict(key=lower)
    myDict['fooBar'] = 12
    print(myDict['FOOBAR'])

prints "12". `lower` was specified here, so keys are normalized by
passing them to `lower`(). This is also the default.
You can specify some other function as needed.
In particular, LooseDict.nfkd(), LooseDict.nfkdi(),
LooseDict.nfc(), LooseDict.nfci() are provided, to do the eponymous
Unicode normalizations, plus forcing to lower case for the "i" variants
(see [https://www.unicode.org/faq/normalization.html].

There are a few extra methods.
For example, you can get the normalized form of a key:

    print(myDict.getNormKey('FooBaR'))

would print 'foobar'.

For any non-normalized key, you can find what (possibly different)
key was last used to store data under the same '''normalized''' key. For example:

    myDict['fooBar'] = 2
    myDict['FoobaR'] = 4
    print(myDict.getRealKey('fOOBAr'))

would print 'FoobaR', since all these arguments normalized to the same
normKey ('foobar').

Note that entries must still be unique with respect to their ''normalized''
form. If you do:

    myDict = LooseDict()
    myDict['fooBar'] = 12
    myDict['foobar'] = 10
    myDict['FOOBAR'] = 8

The dict will have just one entry, whose normkey is 'foobar', realKey is 'FOOBAR'
(because it was the last one explicitly set), and value is 8.

    for k, y in myDict.items()
        or
    keylist = myDict.keys()

will get you the real (not normalized) keys. You can of course normalize
individually using `getNormKey()`. ''iteritems''() is a Python 2 thing; the
underlying ''__iteritems__''() is implemented directly in this class,
however, so is available even in Python 3.

`__cmp__` uses the regular `dict` method, so compares on the basis of real
(not normalized) keys. This should perhaps change, at least to allow a choice.

Other dict operations are all intended to work normally. For example:

* Setting or getting items with `[]` should work fine.

* 'in' normalizes the key passed, and returns True iff there is an item whose
real key normalizes to that same normalized value.

* 'clear' and 'copy' have no notable differences.

* 'keys' and 'iteritems' should also work fine.
Both return the ''real'' keys,
not the normalized form (of course, you can convert using 'getNormKey').
`iteritems`() also can be passed `sortNorm=True` to get
pairs in order of normalized keys (or reversed order if you also pass
`reverse=True`).


=Related Commands=


=Known bugs and Limitations=

Changing the key-normalizing function on an existing instance is not supported.

The normalizer function must be idempotent. That is, after being applied once,
additional applications should make no further changes. Or in other words,
normalizing an already-normalized key should not denormalize it.


=To do=

* Add an option to find from unique abbreviation of key.
Then integrate that for `strfchr.py`, `bibtex2html.py`, etc.
* Implement __cmp__.
* Perhaps add `items()` variant that hands back actual vs. normalized key?
* Perhaps add notion of explicit aliases (say, separate dict that just maps?)


=History=

2018-09-04: Written. Copyright by Steven J. DeRose.
2021-07-18: Cleanup.


=Rights=

Copyright 2018-09-04 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
class LooseDict(dict):
    """A dict also indexable by *normalized* keys (but it keeps the exact keys,
    too). See also "Emulating container types":
    https://docs.python.org/2/reference/datamodel.html#emulating-container-types
    """
    def __init__(self, key:Any=None, sorter:Callable=None):
        super(LooseDict, self).__init__()
        if (key): self.keyFunction = key
        else: self.keyFunction = str.lower
        if (sorter): self.sorter = sorter
        else: self.sorter = sorted
        self.normKeys = {}  # Map from normalized to real keys

    def __setitem__(self, someKey:Any, value:Any) -> None:
        normKey = self.getNormKey(someKey)
        print("in setitem for '%s', norm='%s', val='%s'." %
            (someKey, normKey, value))
        if (normKey in self.normKeys):
            oldRealKey = self.normKeys[normKey]
            super(LooseDict, self).__delitem__(oldRealKey)
        self.normKeys[normKey] = someKey
        super(LooseDict, self).__setitem__(someKey, value)
        return

    def __getitem__(self, someKey:Any) -> Any:
        normKey = self.getNormKey(someKey)
        realKey = self.normKeys[normKey]
        return super(LooseDict, self).__getitem__(realKey)

    def __delitem__(self, key) -> None:
        normKey = self.getNormKey(key)
        realKey = self.normKeys[normKey]
        del self[realKey]

    def getRealKey(self, someKey:Any):
        normKey = self.keyFunction(someKey)
        if (normKey not in self.normKeys): return None
        return self.normKeys[normKey]

    def getNormKey(self, someKey:Any) -> Any:
        return self.keyFunction(someKey)

    def __has_key__(self, someKey:Any) -> bool:
        normKey = self.getNormKey(someKey)
        return normKey in self.normKeys

    def clear(self):
        self.normKeys.clear()
        return super(LooseDict, self).clear()

    def copy(self):
        newld = LooseDict(key=self.keyFunction)
        for kk in self.keys():
            newld[kk] = self[kk]
        return newld

    def __iteritems__(self, sortNorm:bool=False, reverse:bool=False):
        """Make Python 2 users happy....
        """
        if (sortNorm):
            skeys = self.keys()
        else:
            skeys = sorted(self.keys(), key=self.getNormKey, reverse=reverse)
        for kk in skeys: yield kk, self[kk]
        return None

    def __iter__(self):
        """Return an iterator for the object.
        """
        return LooseDictIterator(self)

    def __contains__(self, key):
        normKey = self.getNormKey(key)
        return super(LooseDict, self).__contains__(normKey)

    #def __cmp__(self, dict_):
    #    return self.__cmp__(self.__dict__, dict_)

    @staticmethod
    def nfkd(s:str) -> str:
        return LooseDict.unormalize(s, 'NFKD', ignoreCase=False)

    @staticmethod
    def nfkdi(s:str) -> str:
        return LooseDict.unormalize(s, 'NFKD', ignoreCase=True)

    @staticmethod
    def nfc(s:str) -> str:
        return LooseDict.unormalize(s, 'NFC', ignoreCase=False)

    @staticmethod
    def nfci(s:str) -> str:
        return LooseDict.unormalize(s, 'NFC', ignoreCase=True)

    @staticmethod
    def unormalize(s:str, form:str="NFC", ignoreCase:bool=True) -> str:
        if (form == "NFKD"): s2 = unicodedata.normalize('NFKD', s)
        elif (form == "NFD"): s2 = unicodedata.normalize('NFD', s)
        elif (form == "NFKC"): s2 = unicodedata.normalize('NFKC', s)
        elif (form == "NFC"): s2 = unicodedata.normalize('NFC', s)
        if (ignoreCase): s2 = s2.lower()
        return s2


###############################################################################
#
class LooseDictIterator:
    """Also used for class normdict, below.
    """
    def __init__(self, theLD):
        self.theLD = theLD
        if (theLD.sorter):
            self.keySeq = sorted(theLD.keys(), compare=theLD.sorter)
        else:
            self.keySeq = sorted(theLD.keys())

    def __next__(self):
        for k in self.keySeq: yield self.theLD[k]


###############################################################################
# An earlier version.... Some added features:
#     * Constrain key Type
#     * Lock and unlock the dict keys and/or data
#     * pass in your own sorter
#
class normdict(dict):
    """A subclass of Python 'dict', with some additional features.
    Perhaps add something for str vs. int casting?
    """
    def __init__(
        self,
        default=None,        # Like defaultdict
        normalizer=None,     # Pass all keys through this before hashing
        sorter=None,         # Sort function to use (on norm or reg?)

        keyType=None,        # Keys must be of this type
        valueType=None       # Values must be of this type
        ):
        super(normdict, self).__init__()

        self.default    = default
        if (normalizer == "ignoreCase"):
            self.normalizer = lambda x: x.lower()
        elif (normalizer == "normSpace"):
            self.normalizer = lambda x: re.sub(r'\s+', ' ', x.split())
        else:
            self.normalizer = None

        self.sorter     = sorter
        self.keyType    = keyType
        self.valueType  = valueType

        self.keysLocked = False
        self.dataLocked = False
        self.theDict    = {}

    def lockKeys(self) -> None:
        self.keysLocked = True

    def unlockKeys(self) -> None:
        self.keysLocked = False

    def lockData(self) -> None:
        self.dataLocked = True

    def unlockData(self) -> None:
        self.dataLocked = False

    def findAbbrev(self, key:Any) -> Any:
        if (self.normalizer): normKey = self.normalizer(key)
        else: normKey = key
        for k in self.theDict.keys():
            if (k.startswith(normKey)): return k
        return None

    def matchingKeys(self, regexpr) -> List:
        matches = []
        rc = re.compile(regexpr)
        for k in self.theDict.keys():
            if (re.match(rc, k)): matches.append(k)
        return matches

    def str(self):
        return str(self.theDict)

    def __format__(self, compact=True):
        if (not compact): return self.theDict.__format__()
        buf = ""
        for k, v in self.theDict.items():
            buf += "%-30s %s\n" % (k,v)
        return buf

    def __len__(self):
        return len(self.theDict)

    def __getitem__(self, key:Any) -> Any:
        if (self.normalizer): normKey = self.normalizer(key)
        else: normKey = key
        if (self.keyType and isinstance(key, self.keyType)):
            raise TypeError
        if (normKey in self.theDict):
            return self.theDict[normKey]
        if (self.default and not self.keysLocked):
            self.theDict[normKey] = self.default(key)
        else:
            raise KeyError

    def __setitem__(self, key:Any, value:Any) -> None:
        if (self.normalizer): normKey = self.normalizer(key)
        else: normKey = key
        if (self.keyType and not isinstance(key, self.keyType) or
            self.valueType and not isinstance(value, self.valueType)):
            raise TypeError
        if (self.keysLocked and normKey not in self.theDict):
            raise KeyError
        if (self.dataLocked):
            raise KeyError
        self.theDict[normKey] = value

    def __delitem__(self, key:Any) -> None:
        """Should keysLocked prevent deletion, too?
        """
        if (self.normalizer): normKey = self.normalizer(key)
        else: normKey = key
        if (normKey in self.theDict):
            del self.theDict[normKey]
        else:
            raise KeyError

    def __iter__(self):
        return LooseDictIterator(self)

    def __contains__(self, key):
        if (self.normalizer): normKey = self.normalizer(key)
        else: normKey = key
        return normKey in self.theDict


###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        args0 = parser.parse_args()
        return args0

    args = processOptions()
    print("Testing LooseDict...")

    ld = LooseDict()
    ld['foobar'] = 12
    ld['FOOBar'] = 10
    ld['FoObAr'] = 8

    for k0, v0 in ld.__iteritems__():
        print("    '%s': %s" % (k0, v0))

    if (not args.quiet):
        sys.stderr.write("Done.\n")

