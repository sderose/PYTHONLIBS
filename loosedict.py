#!/usr/bin/env python3
#
# loosedict: Enhance dict to handle case-ignoring, abbreviations,.....
# 2018-09-04: Written by Steven J. DeRose.
#
import sys
import argparse
import unicodedata
import re
from typing import Any, List, Callable

__metadata__ = {
    "title"        : "loosedict",
    "description"  : "Enhance dict to handle case-ignoring, abbreviations,....",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-09-04",
    "modified"     : "2023-03-01",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

A subclass of `dict` that stores keys and values exactly as passed,
but indexes them under a normalized form (for example, folded to lowercase).
For example:

    myDict = LooseDict(normFunc=lower)
    myDict["fooBar"] = 12
    print(myDict["FOOBAR"])

prints "12". `lower` was specified here, so keys are normalized by
passing them to `lower`(). This is also the default. Several other common
normalizations are provided:

    * xmlSpace(s) -- per XML
    * unormalize(s, form:str, ignoreCase:bool) --- Unicode normalization forms
"NFKD", "NFD", "NFKC", "NFC", with or without case-folding (to lower) as well.
    * nfkd(s) nfc(s), nfkdi(s), nfci(s) --  the like-named normalizations,
with the "i" suffix adding case-folding
Re. Unicode normalization see [https://www.unicode.org/faq/normalization.html].

There are a few extra methods, mainly to deal with the distinction of the
stored key vs. the normalized one used for searching.
For example, you can get the normalized form of a key. This would print "foobar":

    print(myDict.getNormKey("FooBaR"))

===Abbreviation finding===

This package also provides `findAbbrev(s)`, which checks if the string s is
a unique abbreviation of some key (after normalization). If so, it returns
the actual key; if it abbreviates no actual keys, or is ambiguous, findAbbrev()
returns None. This is a typical behavior for interpreting command-line options.

For convenience, there is also `findByAbbrev(s)`, which does the same but
returns the value instead of the normalized key (or None if ambiguous or not found).

==Managing real vs. normalized keys==

LooseDict is a subclass of dict, and the "real" dict (owned by the parent class)
holds the non-normalized / raw / real keys. A second dict, _normKeys,
keeps the normalized keys, and points to their real-key equivalents.
For any non-normalized key, you can find what (possibly different)
key was last used to store data under the same '''normalized''' key. For example
(again assuming the normalization function used is `lower`):

    myDict["fooBar"] = 2
    myDict["FoobaR"] = 4
    print(myDict.getRealKey("fOOBAr"))

would print "FoobaR", since all these arguments normalized to the same
normKey ("foobar"), and so the second assignment replaces the first (otherwise
you"d have two real keys corresponding to the same normalized key).
At this point, the key "fooBar" (not normalized) is not in the dict; only "FoobaR"
(though you can retrieve the same entry via either form -- that's the point).

Note that entries must still be unique with respect to their ''normalized''
form. If you do:

    myDict = LooseDict()
    myDict["fooBar"] = 12
    myDict["foobar"] = 10
    myDict["FOOBAR"] = 8

then the dict will have just one entry, whose normkey is "foobar" and
realKey is "FOOBAR" (because it was the last one explicitly set), and value is 8.

    for k, y in myDict.items()
        or
    keylist = myDict.keys()

will get you the real (not normalized) keys. You can of course normalize
individually using `getNormKey()`. ''iteritems''() is a Python 2 thing; the
underlying ''__iteritems__''() is implemented directly in this class,
however, so is available even in both Python 2 and 3.

`__eq__` (and therefore "==") compares ''normalized'' keys, so if two dictionaries
use different real keys for the same thing, they can still be equal (assuming,
of course, that the corresponding values also match up).
Calling __eq__ on the parent class (dict) used the real
(not normalized) keys.

Other dict operations are all intended to work normally. For example:

* Setting or getting items with `[]` should work fine.

* 'in' normalizes the key passed, and returns True iff there is an item whose
real key normalizes to that same normalized value.

* 'clear' and 'copy' have no notable differences.

* 'keys' and 'iteritems' should also work fine.
Both return the ''real'' keys,
not the normalized form (of course, you can convert using `getNormKey()`)).
`iteritems()` also can be passed `sortNorm=True` to get
pairs in order of normalized keys (or reversed order if you also pass
`reverse=True`).


=Related Commands=


=Known bugs and Limitations=

Changing the key-normalizing function on an existing instance is not supported.
However, you can copy the dictionary into a new one with the different function.
In that case, be sure there are no real keys present for which the new
normalization function produces the same normalized value.

The normalizer function must be idempotent. That is, after being applied once,
additional applications should make no further changes.
Normalizing an already-normalized key should not denormalize it.
Common normalizations such as case-folding, white-space removal, and
(I think) all the Unicode normalizations, are idempotent.


=To do=

* Integrate findAbbrev() to other commands (`strfchr.py`, `bibtex2html.py`, etc.)
* Considering switching to storing by the normalized keys, with an index to map those
to what real key was last used. That's a little simpler, but I tend to think callers
want the real keys still around, and keeping them in the "real" dict seems clearest.
* Add `items()` variant that hands back actual vs. normalized key?
* Perhaps add notion of explicit aliases (say, separate dict that just maps?)
In the meantime, callers could build that into a custom normalization function.
* Option to distinguish case, but fall back on failed lookup?


=History=

2018-09-04: Written. Copyright by Steven J. DeRose.
2021-07-18: Cleanup.
2023-03-01: Add findAbbrev(), improve names and typehints.
2024-02-18: Add __eq__(), findByAbbrev().


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

    The keys passed in are called the 'real' keys, and items are stored in
    the actual dict, under the real keys used to set them.

    However, each real key is also normalized by 'normFunc'.
    The normalized keys are added to a map in 'normKeys', which maps them
    to the real key from which they were normalized. So a lookup involves using
    that map on the key requested, to get the actual stored/real key, which is
    then sought in the dict.
    """
    def __init__(self, normFunc:Callable=None, sorter:Callable=None):
        super(LooseDict, self).__init__()
        if (normFunc): self.normFunc = normFunc
        else: self.normFunc = str.lower
        if (sorter): self.sorter = sorter
        else: self.sorter = sorted
        self._normKeys = {}  # Map from normalized to real keys
        self.aliases = {}    # Map from alias to real keys

    def __setitem__(self, someKey:Any, value:Any) -> None:
        """This stores the item under the real key the caller passed; but it also
        needs to delete any entry that might exist under a different real key that
        happens to normalize to the same thing.
        """
        normKey = self.getNormKey(someKey)
        print("in setitem for '%s', norm='%s', val='%s'." %
            (someKey, normKey, value))
        if (normKey in self._normKeys):
            oldRealKey = self._normKeys[normKey]
            super(LooseDict, self).__delitem__(oldRealKey)
        self._normKeys[normKey] = someKey
        super(LooseDict, self).__setitem__(someKey, value)
        return

    def __getitem__(self, someKey:Any) -> Any:
        normKey = self.getNormKey(someKey)
        realKey = self._normKeys[normKey]
        return super(LooseDict, self).__getitem__(realKey)

    def __delitem__(self, key) -> None:
        normKey = self.getNormKey(key)
        realKey = self._normKeys[normKey]
        del self[realKey]

    def __eq__(self, dict_, valueNormer:Callable=None):
        """Compare *normalized* keys, not real keys (use superclass to compare
        based on real keys).
        Since it seems likely to be handy sometimes, valueNormer can be
        specified as a function to normalize values during the comparison
        as well. It need not be the same as the key normalizer.
        """
        if (len(self) != len(dict_)): return False
        for k, v in self.items():
            if (k not in dict_): return False
            if (valueNormer):
                if (valueNormer(dict_[k]) != valueNormer(v)): return False
            else:
                if (dict_[k] != v): return False
        return True

    def getRealKey(self, someKey:Any):
        """Returns the real key which was (last) used to set a given dict entry.
        There are typically many real keys that normalize to the same norm key.
        The passed key is normalized, then the norm key is looked up to get
        the real key (if any) that's really in the main dict.
        """
        normKey = self.normFunc(someKey)
        if (normKey not in self._normKeys): return None
        return self._normKeys[normKey]

    def getNormKey(self, someKey:Any) -> Any:
        """Just applies the normalization function to the key passed and
        returns the result.
        """
        return self.normFunc(someKey)

    def __has_key__(self, someKey:Any) -> bool:
        normKey = self.getNormKey(someKey)
        return normKey in self._normKeys

    def clear(self):
        self._normKeys.clear()
        return super(LooseDict, self).clear()

    def copy(self):
        newld = LooseDict(normFunc=self.normFunc)
        for kk in self.keys():
            newld[kk] = self[kk]
        return newld

    def __iteritems__(self, sortNorm:bool=False, reverse:bool=False):
        """Returns all the (realkey, value) pairs, possibly sorted.
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

    ### Support for finding by unique abbreviations.
    #
    def findByAbbrev(self, key:Any) -> Any:
        """Like findAbbrev() but returns the value (or None).
        """
        theKey = self.findAbbrev(key)
        if (not theKey): return None
        return self[theKey]

    def findAbbrev(self, key:Any) -> Any:
        """Finds all the matches in the dict, that the given key abbreviates.
        If there's exactly one, return it; otherwise return None (fail).
        This is the typical behavior for matching command-line option names.

        TODO: Add a way to get all the existing keys that a given key abbreviates,
        even if ambiguous.
        """
        if (self.normFunc): normKey = self.normFunc(key)
        else: normKey = key
        matches = []
        for k in self._normKeys:
            if (k.startswith(normKey)): matches.append(k)
        if (len(matches) == 1): return matches[0]
        return None

    ### Provide several predictable normalizer functions
    #
    @staticmethod
    def xmlSpace(s:str) -> str:
        """Basic whitespace normalization as defined by XML.
        """
        return re.sub(r"[ \t\n\r]+", " ", s.strip(" \t\n\r"))

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
        """Provide easy access to the Unicode normalizations.
        """
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
        normFunc=None,     # Pass all keys through this before hashing
        sorter=None,         # Sort function to use (on norm or reg?)

        keyType=None,        # Keys must be of this type
        valueType=None       # Values must be of this type
        ):
        super(normdict, self).__init__()

        self.default    = default
        if (normFunc == "ignoreCase"):
            self.normFunc = lambda x: x.lower()
        elif (normFunc == "normSpace"):
            self.normFunc = lambda x: re.sub(r'\s+', ' ', x.split())
        else:
            self.normFunc = None

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

    def findAbbrev(self, key: Any) -> Any:
        """Find all the matches in the dict, that the given key abbreviates.
        If there's exactly one, return it; otherwise return None (fail).
        This is the typical behavior for matching command-line option names.
        """
        if (self.normFunc): normKey = self.normFunc(key)
        else: normKey = key
        matches = []
        for k in self.theDict.keys():
            if (k.startswith(normKey)): matches.append(k)
        if (len(matches) == 1): return matches[0]
        return None

    def matchingKeys(self, regexpr) -> List:
        matches = []
        rc = re.compile(regexpr)
        for k in self.theDict.keys():
            if (re.match(rc, k)): matches.append(k)
        return matches

    def str(self):
        return str(self.theDict)

    def __format__(self, compact: bool = True):
        if (not compact): return self.theDict.__format__()
        buf = ""
        for k, v in self.theDict.items():
            buf += "%-30s %s\n" % (k,v)
        return buf

    def __len__(self):
        return len(self.theDict)

    def __getitem__(self, key: Any) -> Any:
        if (self.normFunc): normKey = self.normFunc(key)
        else: normKey = key
        if (self.keyType and isinstance(key, self.keyType)):
            raise TypeError
        if (normKey in self.theDict):
            return self.theDict[normKey]
        if (self.default and not self.keysLocked):
            self.theDict[normKey] = self.default(key)
        else:
            raise KeyError

    def __setitem__(self, key: Any, value: Any) -> None:
        if (self.normFunc): normKey = self.normFunc(key)
        else: normKey = key
        if (self.keyType and not isinstance(key, self.keyType) or
            self.valueType and not isinstance(value, self.valueType)):
            raise TypeError
        if (self.keysLocked and normKey not in self.theDict):
            raise KeyError
        if (self.dataLocked):
            raise KeyError
        self.theDict[normKey] = value

    def __delitem__(self, key: Any) -> None:
        """Should keysLocked prevent deletion, too?
        """
        if (self.normFunc): normKey = self.normFunc(key)
        else: normKey = key
        if (normKey in self.theDict):
            del self.theDict[normKey]
        else:
            raise KeyError

    def __iter__(self):
        return LooseDictIterator(self)

    def __contains__(self, key):
        if (self.normFunc): normKey = self.normFunc(key)
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
