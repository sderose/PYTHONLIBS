#!/usr/bin/env python3
#
# test_strbuf: Basic testing for strbuf  or other string classes.
# 2021-08-03: Written by Steven J. DeRose.
#
#pylint: disable=W0221  # To allow added 'inplace' args.
#
import unittest
import codecs
import math
import string
from types import SimpleNamespace
from typing import List  # Callable, Iterable, IO, Dict, Union
import time
import gc
import random
import logging

from strbuf import StrBuf
import array
from basedomtypes import SIO
# from io import StringIO
# from mutablestring import mstring
# (str, bytes, list)

lg = logging.getLogger()

__metadata__ = {
    "title"        : "test_strbuf",
    "description"  : "Test driver for strbuf or other string classes.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2023-08-05",
    "modified"     : "2025-01-07",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

Test at least basic functionality for StrBuf or other str-like classes.

=To do=

See if there's a standard Python str test suite to apply.
"""

args = SimpleNamespace(**{
    "atEnd": False,   # "Do appending rather than prepending."
    "deletePer": 0,   # "If set, do a random delection every N adds."
    "maxPower":  2,   # "Last power of 2 for size to run timing for."
    "missing": False, # "List methods that are on str but not StrBuf."
    "partDft": 512,   # "Size preference for separate blocks of a string."
    "partMax": 1024,  # "Size limit for separate blocks of a string."
    "smokeLength": 0, # "Size for random smoketest string.")
    "width": 40,
})

def loadDict(path:str="/usr/share/dict/words") -> List:
    theWords = []
    with codecs.open(path, "rb", encoding="utf-8") as ifh:
        theWords.extend([ x.strip() for x in ifh.readlines() ])
        print("Loaded %d words from %s." % (len(theWords), path))
    return theWords

dictWords = loadDict()
nwords = len(dictWords)

w1 = (
    "Adam Beth Cris Dave ever fond grow high isle jump " +
    "knot lamp melt nope Owen Paul quit rope sees test " +
    "Urdo vent wrap Xeno yurt zoom " )

src = """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
    eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
    enim ad minim veniam, quis nostrud exercitation ullamco laboris
    nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
    reprehenderit in voluptate velit esse cillum dolore eu fugiat
    nulla pariatur. Excepteur sint occaecat cupidatat non proident,
    sunt in culpa qui officia deserunt mollit anim id est laborum."""

def genText(n:int=20000) -> str:
    s = ""
    n = min(n, len(dictWords))
    while len(s) < n:
        s += dictWords[random.randrange(0, nwords)] + " "
    return s

def warmup() -> str:
    print("Warming up the CPU...")
    buf = ""
    for _i in range(10000):
        cp = random.randrange(32, 126)
        buf += chr(cp)
    return buf

def timer(maxPower: int, partMax: int, words:List):
    warmup()
    print("\nTesting StrBuf")
    s = StrBuf("")
    s.setSizes(partMax=partMax)
    for p in range(maxPower+1):
        print("\n\n================= 2**%d" % (p))
        gc.collect()
        n = 2**p
        t0 = time.time()
        s.clear()
        for i in range(n):
            if (args.atEnd): s.append(words[i % nwords] + " ")
            else: s.insert(0, words[i % nwords] + " ")
            lg.warning("### '%s'", s)
            if (args.deletePer and i % args.deletePer == 0):
                delStart = random.randint(0, len(s)-10)
                delEnd = delStart + random.randint(
                    0, math.floor(args.partMax*1.5))
                if (delEnd >= len(s)): delEnd = delStart + 5
                lg.warning("Deleting [%d:%d]", delStart, delEnd)
                s.delete(delStart,delEnd)
        t1 = time.time()
        msec = 1000.0 * (t1-t0)
        print("Added 2**%-2d (%8d) words:  %8.3fms: %6.3f µs/word, final len %10d" %
            (p, n, msec, msec*1000/n, len(s)))
        m = s.min()
        print("Min: '%s' (U+%04x)" % (m, ord(m)))
        s.clear()

def makeOne(s:str):
    #return str(s)
    return SIO(s)
    return StrBuf(s)


###############################################################################
#
class testStrBuf(unittest.TestCase):
    def setUp(self):
        self.s1 = makeOne(w1)
        self.assertEqual(len(self.s1), len(w1))
        self.s2 = makeOne(src)
        self.short = makeOne("Laughably short string")

    def testCast(self):
        self.assertIsInstance(bool(self.s1), bool)
        self.assertIsInstance(str(self.s1), str)

        self.assertEqual(bool(self.s1), True)
        self.assertEqual(str(self.s1), self.s1.getvalue())

        with self.assertRaises(ValueError):
            int(self.s1, 10)

    @unittest.skip
    def testCompare(self):
        other = self.short
        self.assertFalse(self.s1 == other)
        self.assertTrue(self.s1 >= other)
        self.assertTrue(self.s1 > other)
        self.assertFalse(self.s1 <= other)
        self.assertFalse(self.s1 < other)
        self.assertTrue(self.s1 != other)
        self.assertEqual(self.s1.__cmp__(other), 1)

        self.assertEqual(len(self.s1.splitlines(keepends=True)), 1)

        self.assertEqual(len(self.s2.splitlines(keepends=True)), 7)

    def testSearch(self):
        tgt = w1[0:len(w1)>>1]
        tgt2 = w1[len(w1)>>2:]
        sub = "the"

        self.assertEqual(self.s1.startswith(tgt), True)
        self.assertEqual(self.s1.endswith(tgt), False)
        self.assertEqual(self.s1.startswith(tgt2), False)
        self.assertEqual(self.s1.endswith(tgt2), True)
        with self.assertRaises(ValueError):
            self.s1.index(sub, 100, 2000)
        self.assertEqual(self.s1 in tgt, False)
        self.assertEqual("Paul" in str(self.s1), True)
        self.assertNotEqual(self.s1.find("Paul"), None)
        self.assertEqual("xyzzy0" in str(self.s1), False)
        self.assertEqual(self.s1.find("xyzzy0"), -1)

    def testInfo(self):
        self.assertEqual(len(self.s1), len(w1))
        #self.assertEqual(self.s1.hash(), w1.hash())
        for i in range(len(self.s1)):
            self.assertEqual(self.s1[i], w1[i])

    def testProperties(self):
        #fillchar = "*"
        inplace = True
        other = "Some other text"
        s2 = self.s1 * 3  # TODO inplace?
        s3 = self.s1 + other
        self.assertEqual(len(s2.getvalue()), len(self.s1.getvalue())*3)
        self.assertEqual(len(s2), len(self.s1)*3)

        # TODO
        #w = args.width
        #self.assertEqual(len(self.s1.zfill(w, inplace)), w)
        #self.assertEqual(len(self.s1.ljust(w, fillchar, inplace)), w)
        #self.assertEqual(len(self.s1.rjust(w, fillchar, inplace)), w)
        #self.assertEqual(len(self.s1.center(w, fillchar, inplace)), w)
        #s2 = self.s1.reverse(inplace=False)

        # TODO More Unicode examples.
        for wShort in [ "", "abc", "XYZ", "0354", "\u2420", "Python7", " \t\n\r\f" ]:
            sShort = makeOne(wShort)
            self.assertEqual(sShort.isalnum(),      wShort.isalnum())
            self.assertEqual(sShort.isalpha(),      wShort.isalpha())
            self.assertEqual(sShort.isascii(),      wShort.isascii())
            self.assertEqual(sShort.isdecimal(),    wShort.isdecimal())
            self.assertEqual(sShort.isdigit(),      wShort.isdigit())
            self.assertEqual(sShort.isidentifier(), wShort.isidentifier())
            self.assertEqual(sShort.islower(),      wShort.islower())
            self.assertEqual(sShort.isnumeric(),    wShort.isnumeric())
            self.assertEqual(sShort.isprintable(),  wShort.isprintable())
            self.assertEqual(sShort.isspace(),      wShort.isspace())
            self.assertEqual(sShort.istitle(),      wShort.istitle())
            self.assertEqual(sShort.isupper(),      wShort.isupper())
            #self.s1.isa(isaWhat)

    ##############################################################################
    ### Mutators
    ### Since a StrBuf is mutable, anything that produces a modified version has
    ### to decide whether to matate in place, or create and return a new object.
    ### Those methods all take an optional 'inplace' argument.
    ###
    def testMutators(self):
        if (not isinstance(self.s1, (StrBuf, array.array, list))):
            print("Skipping testMutators for class %s." % (type(self.s1)))
            return

        pre = w1[0:10]
        suf = w1[-10:]

        tmp = makeOne(w1)
        tmp.removeprefix(suf, inplace=True)
        self.assertEqual(str(tmp), w1)
        self.assertTrue(tmp.startswith(pre))
        tmp.removeprefix(pre, inplace=True)
        self.assertEqual(str(tmp), w1[10:])

        tmp = makeOne(w1)
        tmp.removesuffix(pre, inplace=True)
        self.assertEqual(str(tmp), w1)
        self.assertEqual(w1[-10:], str(tmp[-10:]))
        self.assertTrue(tmp.endswith(suf))
        tmp.removesuffix(suf, inplace=True)
        self.assertEqual(str(tmp), w1[0:-10])

        tmp = makeOne(w1)
        tmp.delete(100, 200)
        self.assertEqual(str(tmp), w1[0:100] + w1[100:])

        s2 = makeOne()
        s3 = s2.reversed()
        self.assertEqual(len(s2) == len(s3))
        self.assertEqual(str(s2) == str(s3).reversed())

        reps = 1000
        s2 = makeOne("")
        for i in range(reps): s2.append(w1smoke)
        self.assertEqual(len(s2), reps * len(w1smoke))
        self.assertEqual(str(s2), w1smoke * reps)

    def testModify(self):
        if (not isinstance(self.s1, (StrBuf, array.array, list))):
            print("Skipping testModify for class %s." % (type(self.s1)))
            return

        s2 = genText(n=10000)
        tgt = s2[100:200]
        self.s1.partition(tgt)
        self.s1.append(s2)
        #self.s1.appendShort(pnum, s)  ######## __?
        #self.s1.prependShort(pnum, s)  ######## __?
        #s3 = self.s1.copy().insert(100, s2)
        insertAt = 100
        self.s1.addString(insertAt, s2)
        self.assertEqual(self.s1, w1[0:insertAt] + s2 + w1[insertAt:])

        sJoiner = "###"
        tokens = [ dictWords[random.randint(0, nwords)] for i in range(1000) ]
        sbTokens = [ makeOne(t) for t in tokens ]
        tjoined = sJoiner.join(tokens)
        sbtjoined = sJoiner.join(sbTokens)
        self.assertEqual(tjoined, sbtjoined)

    def testNormalizers(self):
        if (not isinstance(self.s1, (StrBuf, array.array, list))):
            print("Skipping testNormalizers for class %s." % (type(self.s1)))
            return

        self.assertIsInstance(self.s1.tostring(), str)
        self.assertEqual(self.s1.tostring(), self.s1)

        w2 = "Hello\tto\t\tall\tthish...."
        s2 = makeOne(w2)
        s3 = self.s1.expandtabs(4)
        self.assertFalse("\t" in s3)
        s2.strip("Hh.")
        print(s2)
        s2.lstrip("Hel")
        self.assertEqual(s2, w2[4:])
        s2.rstrip("")
        self.assertEqual(s2, w2[4:])

    def testCaseFolders(self):
        if (not isinstance(self.s1, (StrBuf, array.array, list))):
            print("Skipping testCaseFolders for class %s." % (type(self.s1)))
            return

        inplace = True
        wShort = "All THE words (73) are here."
        sShort = makeOne(wShort)

        self.assertEqual(sShort.casefold(inplace=True),    wShort.casefold())
        self.assertEqual(sShort.lower(inplace=True),       wShort.lower())
        self.assertEqual(sShort.capitalize(inplace=True),  wShort.capitalize())
        self.assertEqual(sShort.title(inplace=True),       wShort.title())
        self.assertEqual(sShort.swapcase(inplace=True),    wShort.swapcase())

        self.assertEqual(sShort.casefold(inplace=False),   wShort.casefold())
        self.assertEqual(sShort.lower(inplace=False),      wShort.lower())
        self.assertEqual(sShort.capitalize(inplace=False), wShort.capitalize())
        self.assertEqual(sShort.title(inplace=False),      wShort.title())
        self.assertEqual(sShort.swapcase(inplace=False),   wShort.swapcase())

        table = str.maketrans(string.ascii_lowercase, string.ascii_uppercase)
        self.assertEqual(sShort.translate(table, inplace), wShort.translate(table))
        self.assertEqual(sShort.upper(inplace),      wShort.upper())
        #assert sShort.applyToAllParts(what, inplace) == wShort.applyToAllParts(what)

    def testStrBufSpecials(self):
        if (not isinstance(self.s1, StrBuf)):
            print("Skipping testStrBufSpecials for class %s." % (type(self.s1)))
            return

        self.assertEqual(self.s1.copy(), self.s1)
        # This should assert if something's wrong.
        self.s1.check()
        # TODO ??? self.s1.iter()

        #tmp.__delByPairs__(pnum0, offset0, pnum1, offset1)
        tmp = makeOne(w1)
        # Ensure there *are* at least 3 parts...
        while len(tmp.parts) < 3:
            tmp += w1
        lenPre = len(tmp)
        len3 = len(tmp.parts[3])
        tmp.deletePart(3)
        self.assertEqual(len(tmp), lenPre - len3)

        s2 = self.s1.copy()
        nParts = len(s2.parts)
        for i in range(nParts, 0, -1):
            s2.splitPart(i, len(s2.parts[i])>>2)
        self.assertEqual(s2, self.s1)
        #self.s1.insertPart(pnum, s)

        s2.clear()
        self.assertEqual(s2, "")

        #self.s1.availInPart(pnum, forDft)
        self.s1.getPackingFactor()
        self.s1.__coalesce__(3)
        tgt = self.s1[200:20]
        #self.s1.local2global(pnum, localOffset)
        if isinstance(self.s1, StrBuf):
            StrBuf.longestPrefixAtEnd(self.s1, tgt)
        #self.s1.getChars(st, fin)
        #self.s1.getChar(tgt)
        #self.s1.findCharN(tgt)

        s = makeOne(w1smoke)
        x1 = " Some additional text"

        p, o = s.findCharN(3)
        print("findCharN(3) gives part %d, offset %d (total len %d)."
            % (p, o, len(s)))
        p, o  = s.findCharN(-3)
        print("findCharN(-3) gives part %d, offset %d (total len %d)."
            % (p, o, len(s)))
        print("s[0:10] is '%s'." % (s[0:10]))
        print("s[-10:] is '%s'." % (s[-10:]))


        self.s1.__repack__()
        return


###############################################################################
#
class testSomeMore(unittest.TestCase):
    def setUp(self):
        self.s1 = makeOne(w1)

    def testsmoke(self):
        w1smoke = w1
        if (args.smokeLength):
            w1smoke += genText(n=args.smokeLength)
        s = makeOne(w1smoke)

        tgt = "knot"
        tgtPos = 50
        if (w1smoke.index(tgt) != tgtPos):
            print("counted wrong for 'knot', it's at %d." % (w1smoke.index(tgt)))
        if (s.index(tgt) != tgtPos):
            print("wrong index for 'knot', string class thinks it's at %d."
                % (s.index(tgt)))
            print("    string class has:\n%s" % (str(s)))

if __name__ == '__main__':
    unittest.main()
