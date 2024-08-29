#!/usr/bin/env python3
#
# test_strbuf: Basic testing for strbuf library.
# 2021-08-03: Written by Steven J. DeRose.
#
#pylint: disable=W0221  # To allow added 'inplace' args.
#
import sys
#import os
import re
import codecs
import math
import string
#from typing import Callable, Iterable  # IO, Dict, List, Union

import argparse
import time
import gc
import random

import logging

from strbuf import StrBuf

lg = logging.getLogger()

__metadata__ = {
    "title"        : "test_strbuf",
    "description"  : "Test driver for strbuf library.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2023-08-05",
    "modified"     : "2023-08-05",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

Test at least basic functionality.

=To do=

See if there's a standard Python str test suite to apply.
"""

src = """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
    eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
    enim ad minim veniam, quis nostrud exercitation ullamco laboris
    nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
    reprehenderit in voluptate velit esse cillum dolore eu fugiat
    nulla pariatur. Excepteur sint occaecat cupidatat non proident,
    sunt in culpa qui officia deserunt mollit anim id est laborum."""

w1 = (
    "Adam Beth Cris Dave ever fond grow high isle jump " +
    "knot lamp melt nope Owen Paul quit rope sees test " +
    "Urdo vent wrap Xeno yurt zoom " )

dictWords = []
nwords = len(dictWords)
w1 = ""

width = 40

def testBasic(s1:StrBuf):
    s1.copy()
    s1.iter()
    s1.check()

def testCast(s1:StrBuf):
    s1.bool()
    s1.int()
    s1.str()
    s1.tostring()

def testCompare(s1:StrBuf):
    other = StrBuf("Laughably short string")
    s1.eq(other)
    s1.ge(other)
    s1.gt(other)
    s1.le(other)
    s1.lt(other)
    s1.ne(other)
    s1.cmp(other)

    s1.splitlines(keepends=True)

def testSearch(s1:StrBuf):
    tgt = w1[0:len(w1)>>1]
    tgt2 = w1[len(w1)>>2:]
    sub = "the"

    s1.startswith(tgt)
    s1.endswith(tgt)
    s1.startswith(tgt2)
    s1.endswith(tgt2)
    s1.index(sub, 100, 2000)  ############
    s1.__in__(tgt)
    s1.string_contains(tgt)
    s1.contains(sub)
    s1.find(sub, 100, 200)

def testModify(s1:StrBuf):
    s2 = genText(n=10000)
    tgt = s2[100:200]
    s1.partition(tgt)
    s1.append(s2)
    #s1.appendShort(pnum, s)  ######## __?
    #s1.prependShort(pnum, s)  ######## __?
    #s3 = s1.copy().insert(100, s2)
    insertAt = 100
    s1.addString(insertAt, s2)

    sJoiner = "###"
    tokens = [ dictWords[random.randint(0, nwords)] for i in range(1000) ]
    sbTokens = [ StrBuf(t) for t in tokens ]
    tjoined = sJoiner.join(tokens)
    sbtjoined = sJoiner.join(sbTokens)
    assert tjoined == sbtjoined

def testPartStuff1(s1:StrBuf):
    s2 = s1.copy()
    nParts = len(s2.parts)
    for i in range(nParts, 0, -1):
        s2.splitPart(i, s2.parts[i].len()>>2)
    assert s2 == s1
    #s1.insertPart(pnum, s)

def testNormalize(s1:StrBuf):
    s2 = "Hello\tto\t\tall\tthish...."
    s3 = s1.expandtabs(4)
    s3.clear()
    print(s3)
    s2.strip("Hh.")
    print(s2)
    s2.lstrip("Hel")
    print(s2)
    s2.rstrip("")
    print(s2)

def testRemove(s1:StrBuf):
    affix = "Huh?"
    s1.removeprefix(affix)
    s1.removesuffix(affix)
    s1.delete(100, 200)
    #s1.__delByPairs__(pnum0, offset0, pnum1, offset1)
    lenPre = len(s1)
    len3 = len(s1.parts[3])
    s1.deletePart(3)
    assert len(s1) == lenPre - len3

def testInfo(s1:StrBuf):
    assert s1.len() == w1.len()
    assert s1.hash() == w1.hash()
    for i in range(len(s1)):
        assert s1[i] == w1[i]

def testPartStuff2(s1:StrBuf):
    #s1.availInPart(pnum, forDft)
    s1.getPackingFactor()
    s1.__coalesce__(3)
    tgt = s1[200:20]
    #s1.local2global(pnum, localOffset)
    s1.longestPrefixAtEnd(tgt) #################
    #s1.getChars(st, fin)
    #s1.getChar(tgt)
    #s1.findCharN(tgt)
    return

def testProperties(s1:StrBuf, fillchar:str="*", inplace:bool=True):
    s1max = s1.max()
    s1min = s1.min()
    print("s1max %s, s1min %s" % (s1max, s1min))
    other = "Some other text"
    s2 = s1 * 3 #################### inplace?
    s3 = s1 + other #################### inplace?
    s1.zfill(width, inplace)
    s1.ljust(width, fillchar, inplace)
    s1.rjust(width, fillchar, inplace)
    s1.center(width, fillchar, inplace)
    s2 = s1.reverse(inplace=False)
    s3 = s2.reverse(inplace=False)
    assert s1 != s2 and s1 == s3

    # Add Unicode examples.
    for wShort in [ "", "a", "A", "0", "\u2420", "Python7", " \t\n\r\f" ]:
        sShort = StrBuf(wShort)
        assert sShort.isalnum() == wShort.isalnum()
        assert sShort.isalpha() == wShort.isalpha()
        assert sShort.isascii() == wShort.isascii()
        assert sShort.isdecimal() == wShort.isdecimal()
        assert sShort.isdigit() == wShort.isdigit()
        assert sShort.isidentifier() == wShort.isidentifier()
        assert sShort.islower() == wShort.islower()
        assert sShort.isnumeric() == wShort.isnumeric()
        assert sShort.isprintable() == wShort.isprintable()
        assert sShort.isspace() == wShort.isspace()
        assert sShort.istitle() == wShort.istitle()
        assert sShort.isupper() == wShort.isupper()
        #s1.isa(isaWhat)

def testInPlace(inplace:bool=True):
    wShort = "All THE words (73) are here."
    sShort = StrBuf(wShort)

    assert sShort.capitalize(inplace) == wShort.capitalize()
    assert sShort.casefold(inplace) == wShort.casefold()
    assert sShort.lower(inplace) == wShort.lower()
    assert sShort.swapcase(inplace) == wShort.swapcase()
    assert sShort.title(inplace) == wShort.title()
    table = str.maketrans(string.ascii_lowercase, string.ascii_uppercase)
    assert sShort.translate(table, inplace) == wShort.translate(table)
    assert sShort.upper(inplace) == wShort.upper()
    #assert sShort.applyToAllParts(what, inplace) == wShort.applyToAllParts(what)


###############################################################################
# Main
#
def genText(path:str="/usr/share/dict/words", n:int=20000):
    global nwords
    if not dictWords:
        with codecs.open(path, "rb", encoding="utf-8") as ifh:
            dictWords.append([ x.strip() for x in ifh.readlines() ])
        nwords = len(dictWords)
        print("Loaded %d words from %s." % (nwords, path))
    s = ""
    while len(s) < n:
        s += dictWords[random.randint(0, nwords)] + " "
    return s

def smoketest(_s1:StrBuf):
    global w1
    if (args.smokeLength):
        w1 += genText(n=args.smokeLength)

    s = StrBuf(w1)
    w2 = s.tostring()
    if (w2 != w1):
        print("Initial mismatch:\n    %s\n    %s" % (w1, w2))
    if (len(s) != len(w1)):
        print("Initial len %d vs. %d" % (len(s), len(w1)))

    for i, c in enumerate(w1):
        assert c == w2[i]

    x1 = " Some additional text"

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

    assert s.startswith(w1[0:10])
    assert not s.startswith("xyzzy")
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

    if (str(s.upper()) != w1.upper()):
        print("upper failed:\n    %s\n    %s" % (w1, w2))
    if (str(s.lower()) != w1.lower()):
        print("lower failed:\n    %s\n    %s" % (w1, w2))



# TODO This doesn't work....
def reportMissing():
    for x in dir(str):
        xs = str(x)
        strThing = getattr(str, xs)
        strbufThing = getattr(StrBuf, xs)
        if (strbufThing is strThing): msg = "INHERITED"
        else: msg = "DEFINED"
        print("%-20s %s" % (x, msg))

def timer(maxPower: int, partMax: int):
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
        "--partDft", type=int, default=512,
        help="Size prefereance for separate blocks of a string.")
    parser.add_argument(
        "--partMax", type=int, default=1024,
        help="Size limit for separate blocks of a string.")
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress most messages.")
    parser.add_argument(
        "--smokeLength", type=int, default=0,
        help="Size for random smoketest string.")
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

print("Warming up the CPU...")
for _i in range(100):
    words = re.split(r"\s+", src)
    nwords = len(words)

sBase = StrBuf(w1)
#sBase.setSizes(partMax=args.partMax, partDft=args.partDft)

smoketest(sBase.copy())

testBasic(sBase.copy())
testCast(sBase.copy())
testCompare(sBase.copy())
testSearch(sBase.copy())
testModify(sBase.copy())
testPartStuff1(sBase.copy())
testNormalize(sBase.copy())
testRemove(sBase.copy())
testInfo(sBase.copy())
#testPartStuff2(sBase.copy())  # TODO Add
testProperties(sBase.copy())
testInPlace(sBase.copy())

if (args.missing):
    reportMissing()
    sys.exit()
timer(args.maxPower, args.partMax)
