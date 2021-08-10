#!/usr/bin/env python3
#
# strBuf.py
# 2021-08-03: Written by Steven J. DeRose.
#
import sys
import os
import codecs
#import string
from enum import Enum
from typing import Callable  # IO, Dict, List, Union

__metadata__ = {
    "title"        : "strBuf.py",
    "description"  : "A mutable string buffer, fast even for big strings.",
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
`str`, and as a fast alternative even for very large strings.

The concept is simple: Big strings are kept as a list of parts, each of a maximum
size (set when constructed). Parts can grow and shrink without having to do anything to
other parts (until they grow past the limit, when a new part is inserted, or drop to
size zero, when they are deleted (though there is always at least one part, even for
the empty string).

The length of each part is cached as they change, because I think counting lengths
all the time is a bad thing.

A wife range of the usual str methods is available, but not all (yet).

For methods like case-folds, padding, trimming, etc, there is an extra "inplace" argument
which defaults to True. When True, the operation is done to the original string, rather
than returning a copy (remember, these are ''mutable'' strings here).

Since the length of any single part is limited, many operations won't get slower regardless
of how big the total string gets. For example, inserting or deleting substrings is much
faster than with regular Python strings. 

On the other hand, some operations still have to look at everything. For example
`find()` should take about the same time as with regular strings. It may even be slightly 
slower due to overhead for checking special-cases at part boundaries, and less favorable
locality of references. So this is best used when you want the mutability.


=Related Commands=


=Known bugs and Limitations=

Some methods are simply missing, such as encode/decode, things like rfind, etc.

Most of the operators, such as +=, *, contains, etc. are not yet implemented.

Not at all sure what happens if a string would be auto-case to something else.
What even consitutes "False" for a StrBuf? Should be just ""

I have no idea how other libraries, such as `re`, access strings. So they may or may not
work with this.

A very few methods are partially working. For example:

** `title()` (make each word have
single initial uppercase or titlecase character) doesn't yet check whether each part
boundary is really also a word boundary. Thus, a word split across a part boundary will
end up with 2 capitals.

** the `start` and `end` arguments to `find()` are not entirely working; mainly, `end`
will stop the search at the end of the correct part, but not ignore the excess text
within that last part (if any).

Not all methods that should support `inplace`, do.


=History=

* 2021-08-03ff: Written by Steven J. DeRose.


=To do=


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
        [r]index endswith expandtabs
        [r]split encode replace count
        sequence ops: in, not in, +, *, [], min, max, index, count, [comparison]
        copy extend *= opo remove reverse
    """ 
    def __init__(self, s:str="", partMax:int=2048, partDft:int=1536):
        self.partMax = partMax
        self.partDft = partDft
        self.clear()
        self.append(s)
    
    def clear(self) -> None:
        """Remove all the data. But leave one part, containing the empty string.
        """
        self.parts = [ "" ]
        self.lens = [ 0 ]
        
    def len(self) -> int:
        return sum(self.lens)
    
    def __bool__(self):
        return (self.len()==0)
        
    def __int__(self):  # TODO: Add base arg
        return int(self.tostring())

    def check(self) -> None:
        """Test that our stashed lengths are correct.
        """
        assert len(self.parts) == len(self.lens)
        for i in range(self.parts):
            assert self.lens[i] == len(self.parts[i])
            assert self.lens[i] > 0

    def tostring(self) -> str:
        return "".join(self.parts)

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
    
    def lstrip(self, what=""):  # TODO: inplace?
        while (len(self.parts)>0 and self.lens[0]>0):
            trimmed = self.parts[0].ltrim(what)
            if (trimmed!=""):
                self.parts[0] = trimmed
                self.lens[0] = len(trimmed)
                break
            self.deletePart[0]
        return
        
    def rstrip(self, what=""):  # TODO: inplace?
        while (len(self.parts)>0 and self.lens[-1]>0):
            trimmed = self.parts[-1].rtrim(what)
            if (trimmed!=""):
                self.parts[-1] = trimmed
                self.lens[-1] = len(trimmed)
                break
            self.deletePart[-1]
        return
        
    def __setitem__(self, st:int, fin:int, s:str):
        """Support splicing operations
        """
        self.delete(st, fin)
        self.insert(st, s)
        pnum0, offset0 = self.findCharN(st)
        pnum1, offset1 = self.findCharN(fin)
        
    def append(self, s:str):
        """Add at end of string.
        """
        self.addString(self.len(), s)
    
    def startswith(self, tgt:str) -> bool:
        for i in range(self.parts):
            plen = self.lens[i]
            cmpLen = min(len(tgt), plen)
            if self.parts[i][0:cmpLen] != tgt[0:cmpLen]: return False
            tgt = tgt[cmpLen:]  # remove match part, try rest against next part
        return False
        
    def __in__(self, tgt:str) -> bool:
        return string_contains(tgt)
        
    def string_contains(self, tgt:str) -> bool:
        return (self.find(tgt) is not None)
        
    def index(self, tgt:str, start=0, end=None) -> int:
        offset = self.find(self, tgt, start=start, end=end)
        if (offset<0):
            raise ValueError("String target not found.")
        return offset
        
    def find(self, tgt:str, start=0, end=None) -> int:  # TODO Support start/end
        sPnum, sOffset = self.findCharN(start)
        ePnum, eOffset = self.findCharN(start)
        dregs = ""
        for pnum in range(sPnum, ePnum+1):
            buf = dregs + self.parts[i]
            if (pnum==sPnum): f = buf.find(tgt, start=sOffset)
            else: f = buf.find(tgt)
            if (f is not None):
                if (f < len(dregs)): return self.local2global(pnum-1, self.lens[pnum-1]-len(dregs)+f)
                else: return self.local2global(pnum, f-len(dregs))
            # TODO: Next check the edge!
            if len(self.parts[i]) > len(tgt): dregs = ""
            dregs = self.longestPrefixAtEnd(dregs + self.parts[i], tgt)
        return -1

    def local2global(self, pnum, localOffset) -> int:
        tot = 0
        for i in range(0, pnum): tot += len(self.parts[i])
        return tot + localOffset
        
    @staticmethod
    def longestPrefixAtEnd(s:str, tgt:str) -> str:
        """Return the longest prefix of tgt, that occurs at the end of s ("" if none).
        For example, ('spam and egg', 'ggs') -> 'gg', because 'ggs' could match when
        combined with a following 's' or 'gs', but no further left.
        """
        maxMatch = min(len(tgt), len(s))
        for startAt in range(-maxMatch, -1):
            if (tgt.startswith(s[startAt:])): return s[startAt:]
        return ""
        
    def delete(self, st:int, fin:int) -> None:
        """Delete a range of characters.
        """
        pnum0, offset0 = self.findCharN(st)
        pnum1, offset1 = self.findCharN(fin)
        self.__delByPairs__(self, pnum0, offset0, pnum1, offset1)

    def __delByPairs__(self, pnum0:int, offset0:int, pnum1:int, offset1:int) -> None:
        if (pnum0 == pnum1):
            buf = self.parts[pnum0][0:offset0] + self.parts[pnum0][offset1:]
            self.parts[pnum0] = buf
        else:
            self.parts[pnum0] = self.parts[0:pnum0]
            for pnum in range(pnum0+1, pnum1):
                self.deletePart(pnum)
            self.parts[pnum1] = self.parts[pnum1:]
        # TODO: Add __coalesce__
                
    def deletePart(self, pnum:int) -> bool:
        """Delete a *part*. This should really only happen when the part is already empty.
        Oh, and never truly delete the very last part.
        Accepts negatives.
        """
        if (len(self.parts)==1): 
            self.parts[num] = ""
            self.lens[pnum] = 0
            return False
        del self.parts[pnum]
        del self.lens[pnum]
        return True
        
    def __coalesce__(self, pnum:int) -> bool:
        """See if the given part will fit into its neighbors (if any), with enough
        left over; and if so, split it into them (balancing the leftover space
        as specified), and delete the part.
    """
        availL = self.partMax - self.lens[pnum-1] if pnum>0 else 0
        availR = self.partMax - self.lens[pnum+1] if pnum+1 < len(self.parts) else 0
        factorL = availL / float(availL+availR)  # TODO Maybe balance differently?
        needed = self.lens[pnum]
        putL = floor(needed*factorL)
        putR = needed - putL
        if (putL>availL or putR>availR): return False
        if (putL>0):
            self.parts[pnum-1] += self.parts[pnum][0:putL]
            self.lens[pnum-1] += putL
        if (putR>0):
            self.parts[pnum+1] += self.parts[pnum][putL:]
            self.lens[pnum+1] += putR
        self.deletePart(pnum)
        return True
        
    def insertPart(self, pnum:int, s:str="") -> None:
        """Add a part, immediately before part pnum.
        """
        self.parts.insert(pnum, s)
        self.lens.insert(pnum, len(s))
        
    def addString(self, st:int, s:str) -> None:
        """Insert a string at the given offset. If it's too big to fit in the
        corresponding part, split it up, filling new parts to self.partDft.
        TODO: This never inserts into the following part, but it should.
        """
        slen = len(s)
        pnum, offset = self.findCharN(st)
        curPos = 0
        
        avail = self.availInPart(pnum)
        toCopy = min(slen, avail)
        self.insertIntoPart(pnum, offset, s[0:toCopy])
        curPos += toCopy
        
        availNext = self.availInPart(pnum+1)
        while (curPos <= slen-availNext):
            fin = min(slen, curPos+self.partDft)
            self.insertPart(pnum+1, s[curPos:fin])
            pnum += 1
            curPos = fin
        if (curPos <= slen):
            self.parts[pnum+1] = s[curPos:] + self.parts[pnum+1]
            self.lens[pnum+1] = len(self.parts[pnum+1])
    
    def insertIntoPart(self, pnum:int, offset:int, s:str) -> None:
        """This is only the simple insert, where it all gits.
        See addString() for big ones.
        """
        assert self.lens[pnum] + len(s) <= self.partMax
        self.parts[pnum] = self.parts[pnum][0:offset] + s + self.parts[pnum][offset]
        
    def availInPart(self, pnum:int) -> int:
        """Return the number of chars still available to fit into the part.
        """
        if (pnum >= len(self.parts)): 
            raise IndexError("pnum %d requested, but there are only %d parts." %
                (pnum, len(self.parts)))
        return self.partMax - self.lens[pnum]
        
    def getChars(self, st:int, fin:int) -> str:
        pnum0, offset0 = self.findCharN(st)
        pnum1, offset1 = self.findCharN(fin)
        if (pnum0 == pnum1):
            return self.parts[pnum0][offset0:offset1]
        buf = self.parts[pnum0][offset0:]
        for pnum in range(pnum0+1, pnum1):
            buf += self.parts[pnum]
        buf += self.parts[pnum1][0:offset1]
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
            seen = 0
            for pnum in reverse(range(len(self.parts))):
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
        raise IndexError("Offset %d > length %d." % (tgt, self.len()))
        
        
    def max(self) -> str:
        m = None
        for pnum, part in enumerate(toChange.parts):
            thisMax = max(part)
            if (m is None or thisMax > m): m = thisMax
        return thisMin
        
    def min(self) -> str:
        m = None
        for pnum, part in enumerate(toChange.parts):
            thisMin = min(part)
            if (m is None or thisMin < m): m = thisMin
        return thisMin
        
    ####### Trivial cases: apply to all the parts, just first/last,....
    #
    def zfill(self, n:int, inplace:bool=True):
        return self.ljust(n, padchar="0", inplace=inplace)
        
    def ljust(self, n:int, padchar:str=" ", inplace:bool=True):
        needed = n - self.len()
        if (needed > 0): self += " " * needed
        return self
        
    def rjust(self, n:int, padchar:str=" ", inplace:bool=True):
        needed = n - self.len()
        if (needed > 0): self.insert(0, " " * needed)
        return self
        
    def center(self, n:int, padchar:str=" ", inplace:bool=True):
        needed = n - self.len()
        if (needed > 0):
             self.insert(0, " " * floor(needed/2.0))
             self += " " * ceil(needed/2.0)
        return self
        
    def reverse(self, inplace:bool=True):
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        for pnum, part in enumerate(toChange.parts):
            self.parts[pnum] = self.parts[pnum].reverse()
        self.parts = self.parts.reverse()
        self.lens = self.lens.reverse()
        return toChange
        
    def isalnum(self): return self.isa(isalnum)
    def isalpha(self): return self.isa(isalpha)
    def isascii(self): return self.isa(isascii)
    def isdecimal(self): return self.isa(isdecimal)
    def isdigit(self): return self.isa(isdigit)
    def isidentifier(self): return self.isa(isidentifier)
    def islower(self): return self.isa(islower)
    def isnumeric(self): return self.isa(isnumeric)
    def isprintable(self): return self.isa(isprintable)
    def isspace(self): return self.isa(isspace)
    def istitle(self): return self.isa(istitle)  # TODO: Fix boundary cases
    def isupper(self): return self.isa(isupper)
    
    def isa(self, isaWhat:Callable):
        if self.len() == 0: return False
        for pnum, part in enumerate(self.parts):
            if (self.lens[pnum]) == 0: continue
            if (not part.isalnum()): return False
        return True
    
    # The following operate in place instead of copying so you can avoid copying mongo
    # strings. But there's an option to do actual copying like the str versions.
    #
    def capitalize(self, inplace:bool=True):
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        toChange.lower(inplace=inplace);
        if (toChange.lens[0]>0): toChange.parts[0][0] = toChange.parts[0][0].capitalize()
        return toChange
    def casefold(self, inplace:bool=True): 
        return self.applyToAllParts(casefold, inplace=inplace)
    def lower(self, inplace:bool=True): 
        return self.applyToAllParts(lower, inplace=inplace)
    def swapcase(self, inplace:bool=True): 
        return self.applyToAllParts(swapcase, inplace=inplace)
    # title -- matters whether part boundary is word boundary!  TODO
    def translate(self, table, inplace:bool=True): 
        if (inplace): toChange = self
        else: toChange = self.copy()  # TODO add args
        for pnum, part in enumerate(toChange.parts):
            toChange.parts[pnum] = translate(part, table)
        return toChange
    def upper(self, inplace:bool=True): 
        return self.applyToAllParts(translate, inplace=inplace)
    
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
    
    def timer():
        print("\nStrBuf")
        from theScroll import StrBuf
        s = StrBuf()
        for p in range(maxPower):
            collected = gc.collect()
            n = 2**p
            t0 = time.time()
            s.clear()
            for i in range(n):
                s.insert(0, words[i % nwords] + " ")
                print("###%s" % (s))
            t1 = time.time()
            msec = 1000.0 * (t1-t0)
            print("Adding 2**%-2d (%8d) words:  %8.3fms: %6.3f µs/word, final len %10d" %
                (p, n, msec, msec*1000/n, len(s)))
            s = ""
        print("Done")

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()

    timer()
    
    if (len(args.files) == 0):
        fatal("No files specified....")
    for path0, in args.files:
        doOneFile(path0)
