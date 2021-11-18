#!/usr/bin/env python3
#
# strBuf.py: A mutable string buffer, fast changes even for big strings.
# 2021-08-03: Written by Steven J. DeRose.
#
#pylint: disable=W0221  # To allow added 'inplace' args.
#
import sys
#import os
import re
#import codecs
import math
#import string
#from enum import Enum
from typing import Callable, Iterable  # IO, Dict, List, Union

__metadata__ = {
    "title"        : "strBuf.py",
    "description"  : "A mutable string buffer, fast changes even for big strings.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08-03",
    "modified"     : "2021-08-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

This provides the `StrBuf` class, which is intended as a mutable version of Python
`str`, that is quickly changeable even for very large strings (not just the end,
where changes are already very fast in Python).

The concept is simple: Big strings are kept as a list of parts, each of a maximum
size (set when constructed). Parts can grow and shrink without having to do anything to
other parts, until they grow past the limit (when a new part is inserted), or drop to
size zero (when they are deleted). For simplicity there is always at least one part,
even for the empty string).

Most of the usual str methods are available, but not all (yet).

For methods that change the string, like case-folds, padding, trimming, etc, there is
an extra "inplace" argument which defaults to True (some have not yet been added).
When True, the operation is done to the original string, rather
than returning a copy (remember, these are ''mutable'' strings here).

Since the length of any single part is limited, some operations won't get slower regardless
of how big the total string gets. For example, inserting or deleting substrings is much
faster than with regular Python strings (except at the end, which is fast anyway).

The length of each part is cached as it changes (I think counting lengths
all the time is a bad thing). This means that to get the total length, we just take
the sum of the cached lengths. That's still linear in the string length, but much
faster than measuring each string every time. It also means that finding the nth character
in a huge string, can skip through all the prior parts at about one instruction each,
instead of measuring them all (which is itself non-trivial with UTF-8).

On the other hand, some operations do still have to look at everything. For example
`find()` should take about the same time as with regular strings. Perhaps slightly
slower due to overhead for checking special-cases at part boundaries, and less favorable
locality of reference. So this is best used when you want the mutability. Regex matches
than involve backtracking are probably a bad idea here. So is using these as dict keys,
since hashing huge strings is pricey (and actually, you can't use these, since they're
mutable.


=Related Commands=


=Known bugs and Limitations=

Some methods known to `str` are simply missing, such as encode/decode, things like rfind, etc.

Most of the operators, such as +=, *, contains, etc. are not yet implemented.

Not at all sure what happens if a string would be auto-cast to something else.
What even consitutes "False" for a StrBuf?

I have no idea how other libraries such as `re` access strings. So they may or may not
work with this. Please let me know if you find incompatibilities, esp. if you can pin down
what `str` method(s) are involved.

A very few methods are partially working. For example:

** `title()` (make each word have
single initial uppercase or titlecase character) doesn't yet check whether each part
boundary is really also a word boundary. Thus, a word split across a part boundary will
end up with 2 capitals.

** the `start` and `end` arguments to `find()` are not entirely working; mainly, `end`
will stop the search at the end of the correct part, but not ignore the excess text
within that last part (if any).

Not all methods that should support `inplace`, do.


=To do=

* Write packParts(self, fillFactor=1.0, breakAtWords=False), and/or notice when a
deletion makes a chunkm small enough to coalesce with neighbors, and do so.

* Finish:
    __mod__              ???

    __class__            inherit?
    __dir__              inherit?
    __doc__              inherit?
    __format__
    __getnewargs__       inherit?
    __init_subclass__    inherit?
    __new__              inherit?
    __reduce__
    __reduce_ex__
    __repr__             ???
    __rmod__
    __rmul__
    __sizeof__           inherit?
    __subclasshook__     inherit?

    __delattr__          inherit
    __getattribute__     inherit
    __setattr__          inherit

    count                non-overlapping occurrence of substring
    encode               just do parts (could overset, though
    format
    format_map
    maketrans            inherit
    replace
    rfind
    rindex
    rpartition           pre, match, post
    rsplit
    split


=History=

* 2021-08-03ff: Written by Steven J. DeRose.


=Rights=

Copyright 2021-08-03 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg): log(0, msg)
def warning1(msg): log(1, msg)
def warning2(msg): log(2, msg)
def fatal(msg): log(0, msg); sys.exit()


###############################################################################
# TODO: Should this be a subclass of str? If I take it out, it can't find len().
#
class StrBuf(str):
    """A class to support mutable, big strings with operations anywhere
    (including splicing).
    Break the string into a list of moderate-sized chunks.
    Python strings are very good for many things, but if you're making lots of
    changes (other than purely appends, which are remarkably quick), they can
    easily go south.

    What has to be implmented the hard way?
        https://stackoverflow.com/questions/3820506/location-of-python-string-class-in-the-source-code
        regexes? how do they get the chars to match?
    """
    def __init__(self, s:str="", partMax:int=2048, partDft:int=None):
        super(StrBuf, self).__init__()
        if (partDft is None):
            partDft = partMax * 0.75
        if (partDft > partMax):
            raise ValueError("partDft %d > partMax %d" % (partDft, partMax))
        if (partDft < 1):
            raise ValueError("partDft too low (%d)" % (partDft))

        self.partMax = partMax
        self.partDft = partDft
        self.clear()
        self.parts = [ "" ]
        self.lens = [ 0 ]
        self.append(s)

    def copy(self):
        newSB = StrBuf(partMax=self.partMax, partDft=self.partDft)
        newSB.parts = self.parts.copy()
        newSB.lens = self.lens.copy()
        return newSB

    def __iter__(self):
        """Generate all the characters.
        """
        for pnum in range(self.parts):
            for offset in range(self.parts[pnum]):
                yield self.parts[pnum][offset]
        return

    def check(self) -> None:
        """Test that our stashed lengths are correct.
        """
        assert len(self.parts) > 0
        assert len(self.parts) == len(self.lens)
        for i in range(self.parts):
            assert self.lens[i] == len(self.parts[i])
            assert self.lens[i] <= self.partMax
            assert self.lens[i] > 0 or (i==0 and self.lens[0]==0)


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
    def __eq__(self, other): return self.__cmp__(other) == 0
    def __ge__(self, other): return self.__cmp__(other) >= 0
    def __gt__(self, other): return self.__cmp__(other) > 0
    def __le__(self, other): return self.__cmp__(other) <= 0
    def __lt__(self, other): return self.__cmp__(other) < 0
    def __ne__(self, other): return self.__cmp__(other) != 0
    def __cmp__(self, other):
        # TODO: need to be able to iterate through the chars fast.
        # TODO Fix this
        s2 = str(self)
        o2 = str(other)
        if s2 == o2: return 0
        if s2 < o2: return -1
        return +1

    def __mul__(self, n:int):
        if (n<=0): return StrBuf()
        s1 = str(self)
        s2 = StrBuf()
        for _i in range(n):
            s2.append(s1)
        return s2

    def __add__(self, other, inplace=True):
        if (inplace): toChange = self
        else: toChange = self.copy()
        toChange.append(other)
        return toChange

    # Searching for various content
    #
    def splitlines(self, keepends:bool=False):
        """The Python method splits on a whole mess of possibilities.
        """
        prev = None
        for pnum in len(self.parts):
            LFatEnd = pnum and pnum[-1]=="\n"
            for curr in self.parts[pnum].splitlines():
                if (prev is not None): curr = prev + curr  # leftover from prior part
                prev = curr
            if (LFatEnd):
                yield prev
                prev = ""
        return

    def startswith(self, tgt:str) -> bool:
        tlen = len(tgt)
        for i in range(len(self.parts)):
            plen = self.lens[i]
            cmpLen = min(tlen, plen)
            if str(self.parts[i][0:cmpLen]) != str(tgt[0:cmpLen]): return False
            tgt = tgt[cmpLen:]  # remove matched portion, try rest against next part
            if (tgt==""): return True
        return False

    def endswith(self, tgt:str) -> bool:
        if len(self) < len(tgt): return False
        lastBit = str(self[-len(tgt):])
        return (lastBit==tgt)

    def index(self, sub:str, start=0, end=-1) -> int:
        if (not isinstance(start, int)):
            fatal("index got start as %s." % (type(start)))
        offset = self.find(sub, start=start, end=end)
        if (offset<0):
            raise ValueError("String target not found.")
        return offset

    def __in__(self, tgt:str) -> bool:
        return self.string_contains(tgt)

    def string_contains(self, tgt:str) -> bool:
        return (self.find(tgt) is not None)

    def __contains__(self, sub:str) -> bool:
        return (self.find(sub) is not None)

    def find(self, sub:str, start=0, end=-1) -> int:
        sPnum, sOffset = self.findCharN(start)
        ePnum, eOffset = self.findCharN(end)
        if (sPnum==ePnum):
            rc = self.parts[sPnum].find(sub, sOffset, eOffset)
            if (rc<0): return rc
            return rc + self.local2global(sPnum, rc)
        # Ok, have to search multiple parts...
        dregs = ""
        for pnum in range(sPnum, ePnum+1):
            buf = dregs + self.parts[pnum]
            if (pnum==sPnum): f = buf.find(sub, sOffset)
            else: f = buf.find(sub)
            if (f is not None):
                if (f < len(dregs)):
                    offset = self.local2global(pnum-1, self.lens[pnum-1]-len(dregs)+f)
                else:
                    offset =  self.local2global(pnum, f-len(dregs))
                if (offset+len(sub) > end): return -1
                return offset

            # TODO: Next check the edge! TODO What if split over >2 chunks?
            if len(self.parts[pnum]) > len(sub): dregs = ""
            dregs = self.longestPrefixAtEnd(dregs + self.parts[pnum], sub)
        return -1

    def partition(self, tgt:str) -> tuple:
        offset = self.find(tgt)
        if (offset<0): return offset, None, None
        return (StrBuf(str(self[0:offset])),
                StrBuf(str(self[offset:offset+len(tgt)])),
                StrBuf(str(self[offset+len(tgt):])))


    ### Methods that add to the string
    ###
    def append(self, s:str):
        """Add at end of string.
        """
        slen = len(s)
        pnum = len(self.parts) - 1
        curPos = 0
        availHere = self.partDft - self.lens[pnum]
        if (availHere > 0):
            self.appendShort(pnum, s)
            curPos += availHere
            if (curPos >= slen): return

        availRight = self.availInPart(pnum+1)
        while (slen-curPos > availRight):
            lenToInsert = min(slen-curPos, self.partMax)
            self.insertPart(pnum+1, str(s[curPos:curPos+lenToInsert]))
            curPos += lenToInsert
            pnum += 1
        if (curPos < slen):
            self.prependShort(pnum+1, str(s[curPos:]))

    def appendShort(self, pnum:int, s:str):
        """Append, but it better fit in this part. Else use the real append().
        """
        slen = len(s)
        assert self.lens[pnum] + slen <= self.partMax
        self.parts[pnum] += s
        self.lens[pnum] += slen

    def prependShort(self, pnum:int, s:str):
        """Add to start, but it better fit in this part.
        """
        slen = len(s)
        assert self.lens[pnum] + slen <= self.partMax
        self.parts[pnum] = s + self.parts[pnum]
        self.lens[pnum] += slen

    def insert(self, st:int, s:str) -> None:
        self.addString(st, s)

    def addString(self, st:int, s:str) -> None:
        """Insert a string at the given offset. Try to fit in the relevant part + next,
        balancing them to about equal ending % full.
        If it's too big, add new parts, filling parts to self.partDft.
        TODO: Should have a way to append; -1 would be one char early.
        """
        slen = len(s)

        pnum, offset = self.findCharN(st)

        # Can it fit in the current part?
        avail = self.availInPart(pnum)
        if (avail >= slen):
            self.parts[pnum] = str(self.parts[pnum][0:offset]) + str(s) + str(self.parts[pnum][offset:])
            self.lens[pnum] += slen
            return

        # Break the current part at the offset (if it fits in the next part, it will
        # go there; else a new part will be inserted).
        self.splitPart(pnum, offset)

        # Now it's easy. Add pieces of s, making new parts filled to partDft.
        # If equitable, put the last little bit in the right neighbor.
        curPos = 0
        availHere = self.partDft - self.lens[pnum]
        if (availHere > 0):
            self.appendShort(pnum, str(s[0:availHere]))
            curPos += availHere

        availRight = self.availInPart(pnum+1)
        while (slen-curPos > availRight):
            lenToInsert = min(slen-curPos, self.partMax)
            self.insertPart(pnum+1, s[curPos:curPos+lenToInsert])
            curPos += lenToInsert
            pnum += 1
        if (curPos < slen):
            self.prependShort(pnum+1, str(s[curPos:]))

    def splitPart(self, pnum:int, offset:int=None):
        """Split the given part at the offset, putting the second half into the next
        part if it fits, otherwise in a new part.
        """
        assert offset < self.lens[pnum], "splitPart: offset %d out of range %d." % (offset, self.lens[pnum])
        plen = self.lens[pnum]
        neededR = plen - offset
        availR = 0
        if (pnum+1 < len(self.parts)): self.availInPart(pnum+1)
        if (availR > neededR):
            self.prependShort(pnum+1, str(self.parts[pnum][offset:]))
        else:
            self.insertPart(pnum+1, str(self.parts[pnum][offset:]))
        self.parts[pnum] = str(self.parts[pnum][0:offset])
        self.lens[pnum] = offset

    def insertPart(self, pnum:int, s:str="") -> None:
        """Add a part, immediately before part pnum.
        """
        assert len(s) <= self.partMax
        self.parts.insert(pnum, s)
        self.lens.insert(pnum, len(s))

    def expandtabs(self, tabstops=4):  # TODO Add inplace
        """We just do this one part at a time -- but first, align each one to
        an exact tab-stop so the phase is right, then remove the padding after
        doing a normal str.expandtabs. Expanding will usually change the length,
        so we re-calculate the phase for each part after doing the prior one.
        """
        pnum = 0
        while (pnum<len(self.parts)):
            startOfPart = self.local2global(pnum, 0)
            addToGetAligned = tabstops - (startOfPart % tabstops)
            if (addToGetAligned == tabstops): addToGetAligned = 0
            s = (' ' * addToGetAligned) + str(self.parts[pnum]).expandtabs(tabstops)
            s.parts[pnum] = s[addToGetAligned:]
            s.lens[pnum] = len(s.parts[pnum])
        return self


    ### Methods that remove from the string
    ###
    def clear(self) -> None:
        """Remove all the data. But leave one part, containing the empty string.
        """
        self.parts = [ "" ]
        self.lens = [ 0 ]

    def strip(self, chars=""):  # TODO: inplace?
        self.lstrip(chars)
        self.rstrip(chars)
        return self

    def lstrip(self, chars=""):  # TODO: inplace?
        while (len(self.parts)>0 and self.lens[0]>0):
            trimmed = self.parts[0].ltrim(chars)
            if (trimmed!=""):
                self.parts[0] = trimmed
                self.lens[0] = len(trimmed)
                break
            self.deletePart(0)
        return self

    def rstrip(self, chars="") -> 'StrBuf':  # TODO: inplace?
        while (len(self.parts)>0 and self.lens[-1]>0):
            trimmed = self.parts[-1].rtrim(chars)
            if (trimmed!=""):
                self.parts[-1] = trimmed
                self.lens[-1] = len(trimmed)
                break
            self.deletePart(-1)
        return self

    def removeprefix(self, affix:str):  # Add inplace
        if (not self.startswith(affix)): return self
        self.delete(0, len(affix))
        return self

    def removesuffix(self, affix:str):  # Add inplace
        if (not self.endswith(affix)): return self
        self.delete(-len(affix), -1)
        return self

    def delete(self, st:int, fin:int) -> None:
        """Delete a range of characters (negatives accepted).
        """
        pnum0, offset0 = self.findCharN(st)
        pnum1, offset1 = self.findCharN(fin)
        self.__delByPairs__(pnum0, offset0, pnum1, offset1)
        return self

    def __delByPairs__(self, pnum0:int, offset0:int, pnum1:int, offset1:int) -> None:
        if (pnum0 == pnum1):
            buf = str(self.parts[pnum0][0:offset0]) + str(self.parts[pnum0][offset1:])
            self.parts[pnum0] = buf
        else:
            self.parts[pnum0] = str(self.parts[0:pnum0])
            for pnum in range(pnum0+1, pnum1):
                self.deletePart(pnum)
            self.parts[pnum1] = self.parts[pnum1:]
        # TODO: Add __coalesce__

    def deletePart(self, pnum:int) -> bool:
        """Delete a *part* in its entirety.
        This should really only happen when the part is already empty.
        Oh, and never truly delete the very last part.
        Accepts negative part numbers.
        """
        assert pnum>=0 and pnum<len(self.parts)
        if (len(self.parts)==1):
            self.parts[0] = ""
            self.lens[0] = 0
            return False
        del self.parts[pnum]
        del self.lens[pnum]
        return True


    ### Methods for measuring and poking around
    ###
    def __len__(self) -> int:
        return sum(self.lens)

    def __hash__(self) -> int:
        """Convert the whole thing into a regular string, and hash that, so we
        get the same value as an equal regular str.
        """
        return str(self).__hash__()

    #def __setitem__(self, st:int, fin:int, s:str):
    #    """Support splicing operations
    #    """
    #    self.delete(st, fin)
    #    self.insert(st, s)
    #    pnum0, offset0 = self.findCharN(st)
    #    pnum1, offset1 = self.findCharN(fin)

    def __getitem__(self, sl) -> str:
        """Slice out a substring or a single character.
        Seems like it should return even a slice as a string, not list? TODO
        """
        if (isinstance(sl, int)):
            sPnum, sOffset = self.findCharN(sl)
            return str(self.parts[sPnum][sOffset])

        if (not isinstance(sl, slice)):
            fatal("__getitem__ not given int or slice, but %s." % (type(sl)))

        assert not sl.step
        sPnum, sOffset = self.findCharN(sl.start)
        if (sl.stop is None): ePnum, eOffset = -1, -1
        else: ePnum, eOffset = self.findCharN(sl.stop)
        if (sPnum==ePnum): return StrBuf(str(self.parts[sPnum][sOffset:eOffset]))
        s = StrBuf(str(self.parts[sPnum][sOffset:]))
        for p in range(sPnum+1, ePnum):
            s.append(self.parts[p])
        s.append(str(self.parts[ePnum][0:eOffset]))
        return s

    def join(self, iterable:Iterable):
        """Join is called on the inserted delimiter, not the iterable. So the iterable
        might contain strings or StrBufs or whatever. For the moment, we always construct
        a StrBuf for the result, on the theory that if the delimiter is big enough to
        justify being a StrBuf, a whole bunch of them with other strings too, also is.
        """
        s2 = StrBuf()
        for i, thing in enumerate(iterable):
            if i>0: s2.append(self)
            s2.append(str(thing))
        return s2


    ### Methods specific to this approach
    ###
    def availInPart(self, pnum:int, forDft:bool=False) -> int:
        """Return the number of chars still available to fit into the part.
        If the part doesn't exist, just return 0.
        "Available" means below the max size, not the dft, unless you set 'forDft'.
        """
        if (len(self.parts) <= pnum+1): return 0
        lim = self.partDft if (forDft) else self.partMax
        avail = lim - self.lens[pnum+1]
        return max(0, avail)

    def getPackingFactor(self) -> float:
        """Return a float indicating how full blocks are on average.
        """
        totLen = len(self)
        if (totLen == 0): return 0.0
        return float(totLen) / (self.partMax * len(self.parts))

    def __coalesce__(self, pnum:int) -> bool:
        """See if the given part will fit into its neighbors (if any), with enough
        left over; and if so, split it into them (balancing the leftover space
        as specified), and delete the part.
        TODO Better name for this. Write similar to do global pack to [minPct..maxPct].
        Better than absolute pack, more often avoids copying.
        """
        availL = self.partMax - self.lens[pnum-1] if pnum>0 else 0
        availR = self.partMax - self.lens[pnum+1] if pnum+1 < len(self.parts) else 0
        factorL = availL / float(availL+availR)  # TODO Maybe balance differently?
        needed = self.lens[pnum]
        putL = math.floor(needed*factorL)
        putR = needed - putL
        if (putL>availL or putR>availR): return False
        if (putL>0):
            self.parts[pnum-1] += str(self.parts[pnum][0:putL])
            self.lens[pnum-1] += putL
        if (putR>0):
            self.parts[pnum+1] += str(self.parts[pnum][putL:])
            self.lens[pnum+1] += putR
        self.deletePart(pnum)
        return True

    def local2global(self, pnum:int, localOffset:int) -> int:
        """Given a part number and an offset within that part, return the
        global offset to the same place.
        """
        tot = 0
        for plen in self.lens[0:pnum]: tot += plen
        return tot + localOffset

    @staticmethod
    def longestPrefixAtEnd(s:str, tgt:str) -> str:
        """Return the longest prefix of tgt, that occurs at the end of s ("" if none).
        For example, ('spam and egg', 'ggs') -> 'gg', because 'ggs' could match when
        combined with a following 's' or 'gs', but no further left. This is useful for
        finding whether a target might start there, but be completed in the next part(s).
        """
        maxMatch = min(len(tgt), len(s))
        for startAt in range(-maxMatch, -1):
            if (tgt.startswith(s[startAt:])): return s[startAt:]
        return ""

    def getChars(self, st:int, fin:int) -> str:
        pnum0, offset0 = self.findCharN(st)
        pnum1, offset1 = self.findCharN(fin)
        if (pnum0 == pnum1):
            return str(self.parts[pnum0][offset0:offset1])
        buf = str(self.parts[pnum0][offset0:])
        for pnum in range(pnum0+1, pnum1):
            buf += str(self.parts[pnum])
        buf += str(self.parts[pnum1][0:offset1])
        return buf

    def getChar(self, tgt:int) -> str:
        """Return the actual character at the given offset.
        """
        pnum, offset = self.findCharN(tgt)
        return self.parts[pnum][offset]

    def findCharN(self, tgt:int) -> (int, int):
        """Convert a raw character offset (positive or negative), to a
        part-number and a positive offset within that part.
        """
        if (tgt == 0):
            return 0, 0
        elif (tgt < 0):
            tgt = -tgt
            seen = 0
            for pnum in reversed(range(len(self.parts))):
                plen = self.lens[pnum]
                stillToGo = tgt - seen
                if (stillToGo <= plen):
                    return pnum, plen - stillToGo
                seen += plen
        else:
            seen = 0
            for pnum in range(0, len(self.parts)):
                plen = self.lens[pnum]
                stillToGo = tgt - seen
                if (stillToGo <= plen):
                    return pnum, stillToGo
                seen += plen
        raise IndexError("Offset %d > length %d." % (tgt, len(self)))


    def max(self) -> str:
        m = None
        for pnum, part in enumerate(self.parts):
            thisMax = max(part)
            if (m is None or thisMax > m): m = thisMax
        return thisMax

    def min(self) -> str:
        m = None
        for pnum, part in enumerate(self.parts):
            thisMin = min(part)
            if (m is None or thisMin < m): m = thisMin
        return thisMin


    ####### Trivial cases: apply to all the parts, just first/last,....
    #
    def zfill(self, n:int, inplace:bool=True):
        return self.ljust(n, padchar="0", inplace=inplace)

    def ljust(self, n:int, padchar:str=" ", inplace:bool=True):  # TODO: inplace
        needed = n - len(self)
        if (needed > 0): self += padchar * needed
        return self

    def rjust(self, n:int, padchar:str=" ", inplace:bool=True):  # TODO: i
        needed = n - len(self)
        if (needed > 0): self.insert(0, padchar * needed)
        return self

    def center(self, n:int, padchar:str=" ", inplace:bool=True):  # TODO: i
        needed = n - len(self)
        if (needed > 0):
            self.insert(0, padchar * math.floor(needed/2.0))
            self += " " * math.ceil(needed/2.0)
        return self

    def reverse(self, inplace:bool=True):
        """Reversing each part, then reversing the list of parts, is enough.
        """
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        for pnum in range(len(toChange.parts)):
            self.parts[pnum] = self.parts[pnum].reverse()
        self.parts = self.parts.reverse()
        self.lens = self.lens.reverse()
        return toChange

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
    def istitle(self) -> bool: return self.isa(str.istitle)  # TODO: Fix boundary cases
    def isupper(self) -> bool: return self.isa(str.isupper)

    def isa(self, isaWhat:Callable) -> bool:
        if len(self) == 0: return False
        for pnum, part in enumerate(self.parts):
            if (self.lens[pnum]) == 0: continue
            if (not isaWhat(part)): return False
        return True

    # The following operate in place instead of copying so you can avoid copying mongo
    # strings. But there's an option to do actual copying like the str versions.
    #
    def capitalize(self, inplace:bool=True):
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        toChange.lower(inplace=inplace)
        if (toChange.lens[0]>0): toChange.parts[0][0] = toChange.parts[0][0].capitalize()
        return toChange
    def casefold(self, inplace:bool=True):
        return self.applyToAllParts(str.casefold, inplace=inplace)
    def lower(self, inplace:bool=True):
        return self.applyToAllParts(str.lower, inplace=inplace)
    def swapcase(self, inplace:bool=True):
        return self.applyToAllParts(str.swapcase, inplace=inplace)
    # title -- matters whether part boundary is word boundary!  TODO fix edge case
    def title(self, inplace:bool=True):
        return self.applyToAllParts(str.title, inplace=inplace)
    def translate(self, table, inplace:bool=True):
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        for pnum, part in enumerate(toChange.parts):
            toChange.parts[pnum] = str.translate(part, table)
        return toChange
    def upper(self, inplace:bool=True):
        return self.applyToAllParts(str.upper, inplace=inplace)

    def applyToAllParts(self, what:Callable, inplace:bool=True):
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        for pnum, part in enumerate(toChange.parts):
            toChange.parts[pnum] = what(part)
        return toChange


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    import time
    import gc
    import random

    def smoketest():
        w1 = (
            "Adam Beth Cris Dave ever fond grow high isle jump " +
            "knot lamp melt nope Owen Paul quit rope sees test " +
            "Urdo vent wrap Xeno yurt zoom " )
        x1 = " Some additional text"
        s = StrBuf(w1)
        w2 = s.tostring()
        if (not w2 == w1):
            print("Initial bad:\n    %s\n    %s" % (w1, w2))
        if (not len(s) == len(w1)):
            print("Initial len %d vs. %d" % (len(s), len(w1)))

        i = 0
        for c in w1:
            assert c == w1[i]
            i += 1

        if (not s[0] == "A"):
            print("expecting A at [0] but got '%s' (%s)." % (s[0], type(s[0])))
        if (not str(s[50:54]) == "knot"):
            print("expecting know at 50:54 but got '%s'." % (str(s[50:54])))

        p, o = s.findCharN(3)
        print("findCharN(3) gives part %d, offset %d (total len %d)." % (p, o, len(s)))
        p, o  = s.findCharN(-3)
        print("findCharN(-3) gives part %d, offset %d (total len %d)." % (p, o, len(s)))
        print("s[0:10] is '%s'." % (s[0:10]))
        print("s[-10:] is '%s'." % (s[-10:]))

        s.append(x1)
        assert str(s) == w1 + x1
        assert len(w1+x1) == len(s)

        tgt = "knot"
        tgtPos = 50
        if (w1.index(tgt) != tgtPos):
            print("counted wrong for 'knot', it's at %d." % (w1.index(tgt)))
        if (s.index(tgt) != tgtPos):
            print("wrong index for 'knot', StrBuf thinks it's at %d." % (s.index(tgt)))
            print("    strbuf has:\n%s" % (str(s)))

        assert s.startswith("Adam Beth")
        assert not s.startswith("a")
        if (not s.endswith("text")):
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

        if (not str(s.upper()) == w1.upper()):
            print("upper failed:\n    %s\n    %s" % (w1, w2))

    # TODO This doesn't work....
    def reportMissing():
        for x in dir(str):
            xs = str(x)
            strThing = getattr(str, xs)
            strbufThing = getattr(StrBuf, xs)
            if (strbufThing is strbufThing): msg = "INHERITED"
            else: msg = "DEFINED"
            print("%-20s %s" % (x, msg))

    def timer(maxPower:int, partMax:int):
        print("\nTesting StrBuf")
        s = StrBuf(partMax=partMax)  # "", partMax=partMax
        for p in range(maxPower+1):
            print("\n\n================= 2**%d" % (p))
            gc.collect()
            n = 2**p
            t0 = time.time()
            s.clear()
            for i in range(n):
                if (args.atEnd): s.append(words[i % nwords] + " ")
                else: s.insert(0, words[i % nwords] + " ")
                warning1("### '%s'" % (s))
                if (args.deletePer and i % args.deletePer == 0):
                    delStart = random.randint(0, len(s)-10)
                    delEnd = delStart + random.randint(0, math.floor(args.partMax*1.5))
                    if (delEnd >= len(s)): delEnd = delStart + 5
                    warning1("Deleting [%d:%d]" % (delStart, delEnd))
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
            "--iencoding", type=str, metavar="E", default="utf-8",
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

    if (args.smoketest):
        smoketest()
        sys.exit()
    if (args.missing):
        reportMissing()
        sys.exit()
    timer(args.maxPower, args.partMax)
