#!/usr/bin/env python3
#
# strbuf: A mutable string buffer, fast changes even for big strings.
# 2021-08-03: Written by Steven J. DeRose.
#
#pylint: disable=W0221  # To allow added 'inplace' args.
#
import sys
import re
import math
#from collections import UserString
from typing import List, Callable, Iterable, Union  # IO, Dict

__metadata__ = {
    "title"        : "StrBuf",
    "description"  : "A mutable string buffer, fast changes even for big strings.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08-03",
    "modified"     : "2025-01-05",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

This provides the `StrBuf` class, which is intended as a mutable version of
Python `str`, that is quickly changeable even for very large strings (not
just the end, where changes are already very fast in Python).

The concept is simple: Big strings are kept as a list of parts, each of a
maximum size (set when constructed). Parts can grow and shrink without
doing anything to other parts, until they grow past the limit (when
a new part is inserted), or drop to size zero (when they are deleted). For
simplicity there is always at least one part, even for the empty string).

Most of the usual str methods are available, but not all (yet).

For methods that change the string, like case-folds, padding, trimming,
etc, there is an extra "inplace" argument which defaults to True (some have
not yet been added). When True, the operation is done to the original
string, rather than returning a copy (remember, these are ''mutable''
strings here).

Since the length of any single part is limited, some operations won't get
slower regardless of how big the total string gets. For example, inserting
or deleting substrings is much faster than with regular Python strings
(except at the end, which is fast anyway).

The length of each part is cached as it changes (I think counting lengths
all the time is a bad thing). This means that to get the total length, we
just take the sum of the cached lengths. That's still linear in the string
length, but much faster than measuring each string every time. It also
means that finding the nth character in a huge string, can skip through all
the prior parts at about one instruction each, instead of measuring them
all (which is itself non-trivial with UTF-8).

On the other hand, some operations do still have to look at everything. For
example `find()` should take about the same time as with regular strings.
Perhaps slightly slower due to overhead for checking special-cases at part
boundaries, and less favorable locality of reference. So this is best used
when you want the mutability. Regex matches than involve backtracking are
probably a bad idea here. So is using these as dict keys, since hashing
huge strings is pricey (and actually, you can't use these, since they're
mutable.


=Related Commands=

See
[https://stackoverflow.com/questions/7255655/how-to-subclass-str-in-python]
.

=Known bugs and Limitations=

It's really hard to do better than just using Python list for strings that
are going to change a lot.
I'll probably made a list subclass that adds all the string functions (I have
one for StringIO already).

Nearly all methods known to `str` are supported, at least by catching them
via __getattr__, casting to str, calling str's method, and
(if the result is also a single string) casting back.
Additional methods may be needed for functionality or performance.

With split(), if a long separator is used and an instance of it is split
across more than just 2 StrBuf parts, it will be missed. Delimiters that
are merely split across *2* StrBuf parts should work fine.

A very few methods are unfinished. For example:

* `title()` (make each word have single initial uppercase or titlecase
character) doesn't yet check whether each part boundary is really also a
word boundary. Thus, a word split across a part boundary will end up with 2
capitals.

* `find()` has `start` and `end` arguments;
`end` will stop the search at the end of the correct part, but not
ignore the excess text within that last part (if any).

* rfind (and rpartition because it uses rfind) are not there.


=To do=

* Add the __getattr__ trick as done in basedomtypes, to cover any remaining
methods.

* Test this with the std Python test cases from
[https://github.com/python/cpython/blob/main/Lib/test/test_str.py]

* Notice when a deletion makes a chunk small enough
to coalesce with neighbors, and do so.

* Check which of these may needed to be added:
    __mod__
    __format__
    __reduce__
    __reduce_ex__
    __rmod__
    __rmul__
    __getstate__() and __setstate__() for pickle

    iter
    int
    count               non-overlapping occurrence of substring
    encode              inplace? just do parts (could overset, though
    replace             inplace
    rpartition          Make str or StrBuf? pre, match, post
    rsplit              Make str or StrBuf?


=History=

* 2021-08-03ff: Written by Steven J. DeRose.
* 2022-02-05: Rename strBuf to StrBuf. Lint.
* 2024-03-12: Integrate insert and append.
* 2025-01-05: Fix bunch of stuff with split, find, index, cmp, ....
Convert test_StrBuf.py to use unittest. Switch to fill-factor instead
of dft fill size. Add __repack__(). Implement rest of 'inplace' options.
Drop manual table of lengths.


=Rights=

Copyright 2021-08-03 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
class StrBuf():
    """A class to support mutable, big strings with operations anywhere
    (including splicing).
    Break the string into a list of moderate-sized chunks.
    Python strings are very good for many things, but if you're making lots of
    changes (other than purely appends, which are remarkably quick), they can
    easily go south; bytearray, [char[, and IOStream have other drawbacks,
    such as overhead, lack of most string methods, etc.

    This could be a subclass of str or UserString, but then it would inherit
    their implementations for anything it doesn't override -- which would not
    always work. Instead, we should explicitly catch those via getattr (as done
    in basedomtypes).

    What has to be implmented the hard way?
        https://stackoverflow.com/questions/3820506/
        regexes? how do they get the chars to match?
    """
    MIN_PART = 100
    PART_MAX = 2048
    FILL_FACTOR = 0.75

    def __init__(self, s:str=""):
        """TODO UserString keeps a regular string in .data; we don't, so
        we better override anything that does.
        """
        #super().__init__("")
        self.parts = [ "" ]
        self.setSizes()
        self.append(s)

    def setSizes(self, partMax:int=None, fillFactor:float=None):
        if not partMax: partMax = StrBuf.PART_MAX
        if not fillFactor: fillFactor = StrBuf.FILL_FACTOR
        if partMax < StrBuf.MIN_PART: raise ValueError(
            f"partMax ({partMax}) not > {StrBuf.MIN_PART}.")
        if fillFactor > 1.0: raise ValueError(
            f"fillFactor ({fillFactor}) must not be > 1.0.")
        if partMax*fillFactor < StrBuf.MIN_PART: raise ValueError(
            f"partMax ({partMax}) * fillFactor ({fillFactor}) < {StrBuf.MIN_PART}.")
        self.fillFactor = math.ceil(partMax * fillFactor)
        self.partMax = partMax
        self.partFill = math.ceil(partMax*fillFactor)
        self.__repack__()

    def __repack__(self, tolerance:int=64) -> None:
        """Move stuff around to get all the parts to about default size,
        within the given tolerance of the current 'partFill' size.
        TODO: This will not yet combine multiple very small parts.
        """
        i = 0
        while i < len(self.parts):
            toAdd = self.partFill - len(self.parts[i])
            if toAdd > tolerance:  # Pull from next part
                if i+1 >= len(self.parts): break
                toMove = min(len(self.parts[i+1], toAdd))
                self.parts[i] = self.parts[i] + self.parts[i+1][0:toMove]
                self.parts[i+1] = self.parts[i+1][toMove:]
                if len(self.parts[i+1]) == 0:
                    self.deletePart(i+1)
            elif toAdd < -tolerance:  # Push to next part
                if i+1 >= len(self.parts):
                    self.parts.append(self.parts[i+1][toMove:])
                    break
                else:
                    self.parts[i+1] =  self.parts[i+1][toMove:]+ self.parts[i]
                self.parts[i] = self.parts[i][0:toMove]
            i += 1
        return

    def __hash__(self) -> int:
        """Convert to a regular string and hash that. Thus we
        get the same value as an equal regular str would. Of course, changing
        the string will change the hash, so if you change the string you won't
        (for example) be able to find it's old entry in a dict (that seems right).
        """
        return str(self).__hash__()

    ### A few valuable methods that str lacks.
    ###
    def clear(self) -> None:
        """Remove all the data. But leave one part, containing the empty string.
        """
        self.parts = [ "" ]

    def copy(self) -> 'StrBuf':
        """Should this copy the exact part-split, or just the data?)
        For now, does an exact/trivial copy. Probably fastest, too.

        """
        newSB = StrBuf("")
        newSB.parts = self.parts.copy()
        return newSB

    def check(self) -> None:
        """Test that our stashed lengths are correct, etc.
        """
        #assert not self.data (if super were UserString)
        assert len(self.parts) > 0
        for part in self.parts:
            assert 0 < len(part) < self.partMax

    def __len__(self) -> int:
        return(sum(len(x) for x in self.parts))

    def __iter__(self):
        """Generate all the characters.
        """
        for part in self.parts:
            for offset in range(len(part)):
                yield part[offset]
        return

    ### Type-casts
    ###
    def __bool__(self) -> bool:
        return (len(self)==0)

    def __int__(self) -> int:  # TODO: Add base arg
        return int(self.tostring())

    def __str__(self) -> str:
        return self.tostring()

    def tostring(self) -> str:
        return "".join(self.parts)

    ### Comparisons and operators
    ###
    def __cmp__(self, other):
        # TODO: need to be able to iterate through the chars fast.
        # TODO Fix this
        s2 = str(self)
        o2 = str(other)
        if s2 == o2: return 0
        if s2 < o2: return -1
        return +1

    def __eq__(self, other): return self.__cmp__(other) == 0
    def __ge__(self, other): return self.__cmp__(other) >= 0
    def __gt__(self, other): return self.__cmp__(other) > 0
    def __le__(self, other): return self.__cmp__(other) <= 0
    def __lt__(self, other): return self.__cmp__(other) < 0
    def __ne__(self, other): return self.__cmp__(other) != 0

    ### Searching for various content
    ###
    def __contains__(self, sub: str) -> bool:
        """Python calls this for the "in" infix operator, BUT it
        calls it on the right-hand argument, not the left. So we
        only get here if we're the target, not the container.
        """
        return (self.find(sub) is not None)

    def startswith(self, tgt: str) -> bool:
        tlen = len(tgt)
        for i in range(len(self.parts)):
            plen = len(self.parts[i])
            cmpLen = min(tlen, plen)
            if str(self.parts[i][0:cmpLen]) != str(tgt[0:cmpLen]): return False
            tgt = tgt[cmpLen:]  # remove matched portion, try rest against next part
            if tgt=="": return True
        return False

    def endswith(self, tgt: str) -> bool:
        if len(self) < len(tgt): return False
        lastBit = str(self[-len(tgt):])
        return lastBit == tgt

    #def string_contains(self, tgt: str) -> bool:
    #    return (self.find(tgt) is not None)

    def find(self, sub: str, start:int = 0, end: int = -1) -> int:
        """Returns -1 if the substring is not found.
        """
        sPnum, sOffset = self.findCharN(start)
        ePnum, eOffset = self.findCharN(end)
        if sPnum==ePnum:
            rc = self.parts[sPnum].find(sub, sOffset, eOffset)
            if rc<0: return rc
            return rc + self.local2global(sPnum, rc)
        # Ok, have to search multiple parts...
        dregs = ""
        for pnum in range(sPnum, ePnum+1):
            buf = dregs + self.parts[pnum]
            if pnum==sPnum: f = buf.find(sub, sOffset)
            else: f = buf.find(sub)
            if f is not None:
                if f < len(dregs):
                    offset = self.local2global(
                        pnum-1, len(self.parts[pnum-1])-len(dregs)+f)
                else:
                    offset =  self.local2global(pnum, f-len(dregs))
                if offset+len(sub) > end: return -1
                return offset

            # TODO: Next check the edge! TODO What if split over >2 chunks?
            if len(self.parts[pnum]) > len(sub): dregs = ""
            dregs = self.longestPrefixAtEnd(dregs + self.parts[pnum], sub)
        return -1

    def rfind(self, sub: str, start:int = 0, end: int = -1) -> int:
        raise AttributeError("rfind and rpartition not yet done.")

    def index(self, sub: str, start = 0, end = -1) -> int:
        """Raises ValueError if the substring is not found
        """
        n = self.find(sub, start=start, end=end)
        if n<0: raise ValueError("String target not found.")
        return n


    ### Splitters
    ###
    def splitlines(self, maxsplit:int=0) -> List:
        """The Python method splits on a whole mess of possibilities,
        not just \\n.
        """
        chunks = []
        maxLeft = maxsplit
        for pnum in len(self.parts):
            curPieces = self.parts[pnum].splitlines(maxsplit=maxLeft)
            if (chunks and curPieces
                and len((chunks[-1] + curPieces[0]).splitlines()) == 1):
                chunks[-1] += curPieces[0]
                chunks.extend(curPieces[1:])
                maxLeft -= len(curPieces) - 1
            else:
                chunks.extend(curPieces)
                maxLeft -= len(curPieces)
        return chunks

    def split(self, sep:str="", maxsplit:int=0) -> List:
        """If there's a delim at the very start or end, you get a '' result there.
        Remember a separator *itself* could be split across a part boundary;
        this catches that, but not if one delim is split across *3* parts.
        """
        chunks = []
        maxLeft = maxsplit
        for pnum in len(self.parts):
            curPieces = self.parts[pnum].split(sep=sep, maxsplit=maxLeft)
            if (chunks and curPieces
                and len((chunks[-1] + curPieces[0]).split(sep=sep)) == 1):
                chunks[-1] += curPieces[0]
                chunks.extend(curPieces[1:])
                maxLeft -= len(curPieces) - 1
            else:
                chunks.extend(curPieces)
                maxLeft -= len(curPieces)
        return chunks

    def partition(self, sep: str) -> tuple:
        offset = self.find(sep)
        if offset<0: return offset, None, None
        return (StrBuf(str(self[0:offset])),
                StrBuf(str(self[offset:offset+len(sep)])),
                StrBuf(str(self[offset+len(sep):])))

    def rpartition(self, sep: str) -> tuple:
        offset = self.rfind(sep)
        if offset<0: return offset, None, None
        return (StrBuf(str(self[0:offset])),
                StrBuf(str(self[offset:offset+len(sep)])),
                StrBuf(str(self[offset+len(sep):])))


    ### Methods that add to the string
    ###
    def append(self, s: str, fillTo:int=None, pnum:int=None) -> None:
        """Add at end of string -- BUT this also has the logic to support
        Yes, I know that regular Python strings lack append(), extend(), etc.,
        despite being iterable and being just like lists in some respects.
        """
        if fillTo is None or fillTo < 1: fillTo = self.fillFactor or self.partMax
        elif fillTo > self.partMax: fillTo = self.partMax

        if pnum is None: pnum = len(self.parts) - 1
        assert pnum >= 0 and pnum < len(self.parts)

        slen = len(s)

        # First, put as much as fits into the left part.
        curPos = 0
        fitsHere = fillTo - len(self.parts[pnum])
        if fitsHere > 0:
            self.appendShort(pnum, str(s[0:fitsHere]))
            curPos += fitsHere

        # Find how much space is comfortably available to the right.
        if pnum == len(self.parts)-1: availRight = 0
        else: availRight = fillTo - len(self.parts[pnum+1])

        # Start appending parts until what's left is small enough to fit on right.
        #
        while (slen-curPos > availRight):
            lenToInsert = min(slen-curPos, fillTo)  # Or
            self.insertPart(pnum+1, str(s[curPos:curPos+lenToInsert]))
            curPos += lenToInsert
            pnum += 1

        # If appending to non-last part, slip in the dregs.
        if curPos < slen:
            self.prependShort(pnum+1, str(s[curPos:]))

    def appendShort(self, pnum: int, s: str):
        """Append, but it better fit in this part. Else use the real append().
        """
        slen = len(s)
        assert len(self.parts[pnum]) + slen <= self.partMax
        self.parts[pnum] += s

    def prependShort(self, pnum: int, s: str):
        """Add to start, but it better fit in this part.
        """
        slen = len(s)
        assert len(self.parts[pnum]) + slen <= self.partMax
        self.parts[pnum] = s + self.parts[pnum]

    def insert(self, st: int, s: str) -> None:
        self.addString(st, s)

    def addString(self, st: int, s: str) -> None:
        """Insert a string at the given offset. Try to fit in the relevant
        part + next, balancing them to about equal ending % full.
        If it's too big, add new parts, filling parts to self.fillFactor.

        TODO: Should have a way to append; -1 would be one char early.

        TODO: Integrate with regular append(). Maybe just split at the point,
        and then append to the left part.
        """
        slen = len(s)

        pnum, offset = self.findCharN(st)

        # Can it fit in the current part?
        avail = self.availInPart(pnum)
        if avail >= slen:
            self.parts[pnum] = (str(self.parts[pnum][0:offset]) + str(s) +
                str(self.parts[pnum][offset:]))
            return

        # Break the current part at the offset (if it fits in the next part,
        # it will go there; else a new part will be inserted).
        self.splitPart(pnum, offset)
        self.append(s, fillTo=self.fillFactor, pnum=pnum)
        return

    def join(self, seq:Iterable):  # No inplace???
        """Join is called on the inserted delimiter, not the iterable. So the
        iterable might contain strings or StrBufs or whatever. For the moment,
        we always construct a StrBuf for the result, on the theory that if
        the delimiter is big enough to justify being a StrBuf, a whole
        bunch of them with other strings too, also is.
        """
        s2 = StrBuf()
        for i, thing in enumerate(seq):
            if i>0: s2.append(self)
            s2.append(str(thing))
        return s2

    def splitPart(self, pnum: int, offset: int = None):
        """Split the given part at the offset, putting the second half into the
        nextpart if it fits, otherwise in a new part.
        """
        assert offset < len(self.parts[pnum]), "splitPart: offset %d out of range %d." % (
            offset, len(self.parts[pnum]))
        plen = len(self.parts[pnum])
        neededR = plen - offset
        availR = 0
        if pnum+1 < len(self.parts): self.availInPart(pnum+1)
        if availR > neededR:
            self.prependShort(pnum+1, str(self.parts[pnum][offset:]))
        else:
            self.insertPart(pnum+1, str(self.parts[pnum][offset:]))
        self.parts[pnum] = str(self.parts[pnum][0:offset])

    def insertPart(self, pnum: int, s: str = "") -> None:
        """Add a part, immediately before part pnum.
        """
        assert len(s) <= self.partMax
        self.parts.insert(pnum, s)

    ### Mutators
    ###

    def strip(self, chars: str = "", inplace: bool = False):
        toChange = self if inplace else self.copy()
        toChange.lstrip(chars)
        toChange.rstrip(chars)
        return toChange

    def lstrip(self, chars: str = "", inplace: bool = False):
        toChange = self if inplace else self.copy()
        while (len(toChange.parts)>0 and toChange.lens[0]>0):
            trimmed = toChange.parts[0].ltrim(chars)
            if trimmed!="":
                toChange.parts[0] = trimmed
                break
            toChange.deletePart(0)
        return toChange

    def rstrip(self, chars: str = "", inplace: bool = False) -> 'StrBuf':
        toChange = self if inplace else self.copy()
        while (len(toChange.parts)>0 and toChange.lens[-1]>0):
            trimmed = toChange.parts[-1].rtrim(chars)
            if trimmed!="":
                toChange.parts[-1] = trimmed
                break
            toChange.deletePart(-1)
        return toChange

    def removeprefix(self, affix:str, inplace:bool=False):
        toChange = self if inplace else self.copy()
        if toChange.startswith(affix): toChange.delete(0, len(affix), inplace=True)
        return toChange

    def removesuffix(self, affix:str, inplace:bool=False):
        toChange = self if inplace else self.copy()
        if toChange.endswith(affix):  toChange.delete(-len(affix), -1)
        return toChange

    def delete(self, st:int, fin:int, inplace:bool=False) -> None:
        """Delete a range of characters (negatives accepted).
        """
        toChange = self if inplace else self.copy()
        pnum0, offset0 = toChange.findCharN(st)
        pnum1, offset1 = toChange.findCharN(fin)
        toChange.__delByPairs__(pnum0, offset0, pnum1, offset1)
        return toChange

    def __delByPairs__(self, pnum0:int, offset0:int, pnum1:int, offset1:int) -> None:
        if pnum0 == pnum1:
            self.parts[pnum0] = str(self.parts[pnum0][0:offset0]) + str(
                self.parts[pnum0][offset1:])
        else:
            self.parts[pnum0] = str(self.parts[0:pnum0])
            for pnum in range(pnum0+1, pnum1):
                self.deletePart(pnum)
            self.parts[pnum1] = self.parts[pnum1:]

    def deletePart(self, pnum: int) -> bool:
        """Delete a *part* in its entirety.
        This should really only happen when the part is already empty.
        Oh, and never truly delete the very last part.
        Accepts negative part numbers.
        """
        if pnum < 0: pnum = len(self.parts) + pnum
        if pnum >= len(self.parts): raise ValueError(
            f"Cannot deletePart({pnum}), only {len(self.parts)} parts.")
        if len(self.parts) == 1:
            self.parts[0] = ""
            return False
        del self.parts[pnum]
        return True

    def expandtabs(self, tabsize:int=4, inplace:bool=False):
        """We just do this one part at a time -- but first, align each one to
        an exact tab-stop so the phase is right, then remove the padding after
        doing a normal str.expandtabs. Expanding will usually change the length,
        so we re-calculate the phase for each part after doing the prior one.
        """
        toChange = self if inplace else self.copy()
        pnum = 0
        while (pnum<len(toChange.parts)):
            startOfPart = toChange.local2global(pnum, 0)
            addToGetAligned = tabsize - (startOfPart % tabsize)
            if addToGetAligned == tabsize: addToGetAligned = 0
            s = (' ' * addToGetAligned) + str(
                toChange.parts[pnum]).expandtabs(tabsize)
            s.parts[pnum] = s[addToGetAligned:]
        return toChange


    ### Methods for measuring and poking around
    ###

    #def __setitem__(self, sl:Union[int, slice], s:str):
    #    """Support splicing operations
    #    """
    #    self.delete(st, fin)
    #    self.insert(st, s)
    #    pnum0, offset0 = self.findCharN(st)
    #    pnum1, offset1 = self.findCharN(fin)

    def __getitem__(self, sl:Union[int, slice]) -> str:
        """Slice out a substring or a single character.
        Seems like it should return even a slice as a string, not list? TODO
        """
        if isinstance(sl, int):
            sPnum, sOffset = self.findCharN(sl)
            return str(self.parts[sPnum][sOffset])

        if not isinstance(sl, slice): raise TypeError(
            "__getitem__ not given int or slice, but %s." % (type(sl)))
        if sl.step: raise TypeError(
            "__getitem__ slicing does not support step.")

        sPnum, sOffset = self.findCharN(sl.start)
        if sl.stop is None: ePnum, eOffset = -1, -1
        else: ePnum, eOffset = self.findCharN(sl.stop)
        if sPnum==ePnum: return StrBuf(str(self.parts[sPnum][sOffset:eOffset]))
        s = StrBuf(str(self.parts[sPnum][sOffset:]))
        for p in range(sPnum+1, ePnum):
            s.append(self.parts[p])
        s.append(str(self.parts[ePnum][0:eOffset]))
        return s

    ### Methods specific to this approach
    ###
    def availInPart(self, pnum: int, forDft: bool = False) -> int:
        """Return the number of chars still available to fit into the part.
        If the part doesn't exist, just return 0.
        "Available" means below max size, not  dft, unless you set 'forDft'.
        """
        if len(self.parts) <= pnum+1: return 0
        lim = self.fillFactor if (forDft) else self.partMax
        avail = lim - len(self.parts[pnum+1])
        return max(0, avail)

    def getPackingFactor(self) -> float:
        """Return a float indicating how full blocks currently are.
        """
        totLen = len(self)
        if totLen == 0: return 0.0
        return float(totLen) / (self.partMax * len(self.parts))

    def __coalesce__(self, pnum: int) -> bool:
        """See if the given part will fit into its neighbors (if any), with
        enough left over; and if so, split it into them (balancing the
        leftover space as specified), and delete the part.
        TODO Review, maybe add more threshold control. See also __repack__().
        """
        availL = self.partMax - len(self.parts[pnum-1]) if pnum>0 else 0
        availR = self.partMax - len(self.parts[pnum+1]) if pnum+1 < len(self.parts) else 0
        factorL = availL / float(availL+availR)
        needed = len(self.parts[pnum])
        putL = math.floor(needed*factorL)
        putR = needed - putL
        if putL>availL or putR>availR: return False
        if putL>0:
            self.parts[pnum-1] += str(self.parts[pnum][0:putL])
        if putR>0:
            self.parts[pnum+1] += str(self.parts[pnum][putL:])
        self.deletePart(pnum)
        return True

    def local2global(self, pnum: int, localOffset: int) -> int:
        """Given a part number and an offset within that part, return the
        global offset to the same place.
        """
        tot = sum(len(x) for x in self.parts[0:pnum])
        return tot + localOffset

    @staticmethod
    def longestPrefixAtEnd(s: str, tgt: str) -> str:
        """Return the longest prefix of tgt, that occurs at the end of s
        ("" if none). For example, ('spam and egg', 'ggs') -> 'gg',
        because 'ggs' could match when combined with a following 's' or 'gs',
        but no further left. This is useful for finding whether a target
        might start there, but be completed in the next part(s).
        """
        maxMatch = min(len(tgt), len(s))
        for startAt in range(-maxMatch, -1):
            if tgt.startswith(s[startAt:]): return s[startAt:]
        return ""

    def getChars(self, st: int, fin: int) -> str:
        pnum0, offset0 = self.findCharN(st)
        pnum1, offset1 = self.findCharN(fin)
        if pnum0 == pnum1:
            return str(self.parts[pnum0][offset0:offset1])
        buf = str(self.parts[pnum0][offset0:])
        for pnum in range(pnum0+1, pnum1):
            buf += str(self.parts[pnum])
        buf += str(self.parts[pnum1][0:offset1])
        return buf

    def getChar(self, tgt: int) -> str:
        """Return the actual character at the given offset.
        """
        pnum, offset = self.findCharN(tgt)
        return self.parts[pnum][offset]

    def findCharN(self, tgt: int) -> (int, int):
        """Convert a raw character offset (positive or negative), to a
        part-number and a positive offset within that part.
        """
        if tgt == 0:
            return 0, 0
        elif tgt < 0:
            tgt = -tgt
            seen = 0
            for pnum in reversed(range(len(self.parts))):
                plen = len(self.parts[pnum])
                stillToGo = tgt - seen
                if stillToGo <= plen:
                    return pnum, plen - stillToGo
                seen += plen
        else:
            seen = 0
            for pnum in range(0, len(self.parts)):
                plen = len(self.parts[pnum])
                stillToGo = tgt - seen
                if stillToGo <= plen:
                    return pnum, stillToGo
                seen += plen
        raise IndexError("Offset %d > length %d." % (tgt, len(self)))

    ### Support more of the usual API
    ###
    def max(self) -> str:
        m = None
        for _pnum, part in enumerate(self.parts):
            thisMax = max(part)
            if m is None or thisMax > m: m = thisMax
        return thisMax

    def min(self) -> str:
        m = None
        for _pnum, part in enumerate(self.parts):
            thisMin = min(part)
            if m is None or thisMin < m: m = thisMin
        return thisMin

    def __mul__(self, n: int, inplace:bool=True):
        if n <= 0: return StrBuf()
        s1 = str(self)
        s2 = StrBuf()
        for _i in range(n):
            s2.append(s1)
        return s2

    def __add__(self, other, inplace:bool=True):
        toChange = self if inplace else self.copy()
        toChange.append(other)
        return toChange

    ####### Trivial cases: apply to all the parts, just first/last,....
    #
    def zfill(self, width: int, inplace:bool=True):
        return self.ljust(width, fillchar="0", inplace=inplace)

    def ljust(self, width: int, fillchar: str = " ", inplace:bool=True):
        toChange = self if inplace else self.copy()
        needed = width - len(toChange)
        if needed > 0: toChange += fillchar * needed
        return toChange

    def rjust(self, width: int, fillchar: str = " ", inplace:bool=True):
        toChange = self if inplace else self.copy()
        needed = width - len(toChange)
        if needed > 0: toChange.insert(0, fillchar * needed)
        return toChange

    def center(self, width: int, fillchar: str = " ", inplace:bool=True):
        toChange = self if inplace else self.copy()
        needed = width - len(toChange)
        if needed > 0:
            toChange.insert(0, fillchar * math.floor(needed/2.0))
            toChange += " " * math.ceil(needed/2.0)
        return toChange

    def reverse(self):
        """Following the convention for Python mutables like lists: reverse vs. reversed.
        Guess I could have done that for caseswapped, uppered, ljusted,....
        """
        return self.reversed(inplace=True)

    def reversed(self, inplace:bool=True):
        """Reversing each part, then reversing the list of parts, is enough.
        """
        toChange = self if inplace else self.copy()
        for pnum in range(len(toChange.parts)):
            toChange.parts[pnum] = toChange.parts[pnum].reversed()
        toChange.parts = toChange.parts.reversed()
        return toChange

    def isa(self, isaWhat: Callable) -> bool:
        if len(self) == 0: return False
        for pnum, part in enumerate(self.parts):
            if (len(self.parts[pnum])) == 0: continue
            if not isaWhat(part): return False
        return True

    def isalnum(self) -> bool: return self.isa(str.isalnum)
    def isalpha(self) -> bool: return self.isa(str.isalpha)
    def isascii(self) -> bool: return self.isa(str.isascii)
    def isdecimal(self) -> bool: return self.isa(str.isdecimal)
    def isdigit(self) -> bool: return self.isa(str.isdigit)
    def isidentifier(self) -> bool: return self.isa(str.isidentifier)
    def islower(self) -> bool: return self.isa(str.islower)
    def isnumeric(self) -> bool: return self.isa( str.isnumeric)
    def isprintable(self) -> bool: return self.isa(str.isprintable)
    def isspace(self) -> bool: return self.isa(str.isspace)
    def istitle(self) -> bool: return self.isa(str.istitle)  # TODO: Fix edge cases
    def isupper(self) -> bool: return self.isa(str.isupper)

    # The following operate in place instead of copying so you can
    # avoid copying mongo strings. But there's an option for actual copying
    # like the str versions.
    #
    def applyToAllParts(self, what: Callable, inplace:bool=True):
        """Some operations can be done piecemeal, so just do them....
        """
        toChange = self if inplace else self.copy()
        for pnum, part in enumerate(toChange.parts):
            toChange.parts[pnum] = what(part)
        return toChange

    def casefold(self, inplace:bool=True):
        return self.applyToAllParts(str.casefold, inplace=inplace)

    def lower(self, inplace: bool=True):
        return self.applyToAllParts(str.lower, inplace=inplace)

    def swapcase(self, inplace:bool=True):
        return self.applyToAllParts(str.swapcase, inplace=inplace)

    def title(self, inplace:bool=True):
        # TODO it matters whether part boundary is word boundary. Fix edge case
        return self.applyToAllParts(str.title, inplace=inplace)

    def upper(self, inplace:bool=True):
        return self.applyToAllParts(str.upper, inplace=inplace)

    def capitalize(self, inplace:bool=True):
        """This ione s special because the operation on the *first* part is
        different from the rest (it assumes the first part is not empty).
        """
        toChange = self if inplace else self.copy()
        print(f"\n\n******* capitalize working on type {type(toChange)}.")
        toChange.lower(inplace=inplace)
        toChange.parts[0] = toChange.parts[0].capitalize()
        for i in range(1, len(toChange.parts)):
            toChange.parts[i] = toChange.parts[i].lower()
        return toChange

    # TODO: write maketrans()
    def translate(self, table, inplace:bool=True):
        toChange = self if inplace else self.copy()
        for pnum, part in enumerate(toChange.parts):
            toChange.parts[pnum] = str.translate(part, table)
        return toChange


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    import time
    import gc
    import random

    w1 = (
        "Adam Beth Cris Dave ever fond grow high isle jump " +
        "knot lamp melt nope Owen Paul quit rope sees test " +
        "Urdo vent wrap Xeno yurt zoom " )
    words = []
    nwords = 0

    def smoketest():
        s = StrBuf(w1)
        w2 = s.tostring()
        if w2 != w1:
            print("Initial mismatch:\n    %s\n    %s" % (w1, w2))
        if len(s) != len(w1):
            print("Initial len %d vs. %d" % (len(s), len(w1)))

        for i, c in enumerate(w1):
            assert c == w2[i]

        x1 = " Some additional text"

        p, o = s.findCharN(3)
        print("findCharN(3) gives part %d, offset %d (total len %d)." %
            (p, o, len(s)))
        p, o  = s.findCharN(-3)
        print("findCharN(-3) gives part %d, offset %d (total len %d)." %
            (p, o, len(s)))
        print("s[0:10] is '%s'." % (s[0:10]))
        print("s[-10:] is '%s'." % (s[-10:]))

        s.append(x1)
        assert str(s) == w1 + x1
        assert len(w1+x1) == len(s)

        tgt = "knot"
        tgtPos = 50
        if w1.index(tgt) != tgtPos:
            print("counted wrong for 'knot', it's at %d." % (w1.index(tgt)))
        if s.index(tgt) != tgtPos:
            print("wrong index for 'knot', StrBuf thinks it's at %d." %
                (s.index(tgt)))
            print("    strbuf has:\n%s" % (str(s)))

        assert s.startswith(w1[0:10])
        assert not s.startswith("xyzzy")
        if not s.endswith("text"):
            print("Didn't find 'text' at end, StrBuf has:\n%s" % (str(s)))
        assert not s.endswith("zoom")

        s.removesuffix(x1)
        assert str(s) == w1
        assert bool(s)

        s.lstrip("Aa dm")
        assert s[0:4] == "Beth"

        reps = 1000
        s2 = StrBuf()
        for i in range(reps): s2.append(w1)
        assert len(s2) == reps * len(w1)
        assert str(s2) == w1 * reps

        if str(s.upper()) != w1.upper():
            print("upper failed:\n    %s\n    %s" % (w1, w2))
        if str(s.lower()) != w1.lower():
            print("lower failed:\n    %s\n    %s" % (w1, w2))


    # TODO reportMissing() doesn't work....
    def reportMissing():
        for x in dir(str):
            xs = str(x)
            strThing = getattr(str, xs)
            strbufThing = getattr(StrBuf, xs)
            if strbufThing is strThing: msg = "INHERITED"
            else: msg = "DEFINED"
            print("%-20s %s" % (x, msg))

    def timer(maxPower: int, partMax: int):
        print("\nTesting StrBuf")
        s = StrBuf("")
        maxRand = math.floor(partMax*1.5)

        for p in range(maxPower+1):
            print("\n\n================= 2**%d" % (p))
            gc.collect()
            n = 2**p
            t0 = time.time()
            s.clear()
            for i in range(n):
                if args.atEnd: s.append(words[i % nwords] + " ")
                else: s.insert(0, words[i % nwords] + " ")
                if args.deletePer and i % args.deletePer == 0:
                    delStart = random.randint(0, len(s)-10)
                    delEnd = delStart + random.randint(0, maxRand)
                    if delEnd >= len(s): delEnd = delStart + 5
                    s.delete(delStart,delEnd)
            t1 = time.time()
            msec = 1000.0 * (t1-t0)
            print("Added 2**%-2d (%8d) words:  %8.3fms: %6.3f µs/word, final len %10d" %
                (p, n, msec, msec*1000/n, len(s)))
            m = s.min()
            print("Min: '%s' (U+%04x)" % (m, ord(m)))
            s.clear()
        print("Done")

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--atEnd", action="store_true",
            help="Do appending rather than prepending.")
        parser.add_argument(
            "--deletePer", type=int, default=0,
            help="If set, do a random delection every N adds.")
        parser.add_argument(
            "--iencoding", "--input-encoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--maxPower", type=int, default=2,
            help="Last power of 2 for size to run timing for.")
        parser.add_argument(
            "--missing", action="store_true",
            help="List methods that are on str but not StrBuf.")
        parser.add_argument(
            "--partMax", type=int, default=1024,
            help="Size limit for separate blocks of a string.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--smoketest", action="store_true",
            help="Run some basic API tests.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    src = """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
    eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
    enim ad minim veniam, quis nostrud exercitation ullamco laboris
    nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
    reprehenderit in voluptate velit esse cillum dolore eu fugiat
    nulla pariatur. Excepteur sint occaecat cupidatat non proident,
    sunt in culpa qui officia deserunt mollit anim id est laborum."""

    print("Warming up the CPU...")
    for _i in range(100):
        words = re.split(r"\s+", src)
        nwords = len(words)

    if args.smoketest:
        smoketest()
        sys.exit()
    if args.missing:
        reportMissing()
        sys.exit()
    timer(args.maxPower, args.partMax)
