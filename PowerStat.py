#!/usr/bin/env python
#
# PowerStat.py
# 2020-11-23: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys, os
import codecs
#from collections import defaultdict, namedtuple

#from sjdUtils import sjdUtils
#from alogging import ALogger
#su = sjdUtils()
#lg = ALogger(1)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    #import HTMLParser
    #from htmlentitydefs import codepoint2name, name2codepoint
    string_types = basestring
else:
    #from html.parser import HTMLParser
    #from html.entities import codepoint2name, name2codepoint
    import re
    string_types = str
    from io import StringIO
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): str(s, encoding, errors)
    if (sys.version_info[1] < 7):
        def isascii(s):
            if (re.match(r'^[[:ascii:]]+$', s)): return True
            return False

__metadata__ = {
    'title'        : "PowerStat.py",
    'description'  : "A Python clone (more or less) of 'stat'.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-11-23",
    'modified'     : "2020-11-23",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

Do pretty much what *nix `stat` does, but from and for Python.

==Usage==

    PowerStat.py [options] [files]


=Related Commands=


=Known bugs and Limitations=


=History=

* 2020-11-23: Written by Steven J. DeRose.


=To do=


=Rights=

Copyright 2020-11-23 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


dirCount = 0
fileCount = 0


###############################################################################
#
def warn(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
    if (lvl < 0): sys.exit()

def doOneFile(path):
    """Read and deal with one individual file.
    """
    if (not path):
        if (sys.stdin.isatty()): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = codecs.open(path, "rb", encoding=args.iencoding)
        except IOError as e:
            sys.stderr.write("Cannot open '%s':\n    %s" %
                (e), stat="readError")
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        if (args.tickInterval and (recnum % args.tickInterval==0)):
            sys.stderr.write("Processing record %s." % (recnum))
        rec = rec.rstrip()
        if (rec == ''): continue  # Blank record
        print(rec)
    return(recnum)

###############################################################################
#
class PowerStat:
    """Extract and format info much like 'stat'.
    A format item is like:
        % flag? space? size? prec? fmt? sub? datum
    There's a lot in stat that still isn't accessible this way. Perhaps
    Add datum field like {statName}', to just use any name python stat knows?
    (see https://docs.python.org/3/library/stat.html)
    """
    flag    = r'(?P<flag>[#+-0])?'
    space	= r'(?P<space>[ ])?'
    size	= r'(?P<size>\d)?'
    prec	= r'(?P<prec>\.\d+)?'
    fmt	    = r'(?P<fmt>[DOUXFS])?'  # dec, oct, udec, hex, float, s
    sub	    = r'(?P<sub>[HLM])?'    # which part for pdrT
    datum	= r'(?P<datum>[diplugramcBzbkfvNTYZ])'
    # datum += r'|{<?P<datumName>\w+)'

    itemExpr = ('%' + flag + space + size + prec + fmt + sub + datum +
        "|%(?P<esc>[nt%@])")

    @staticmethod
    def format(path, fmtSpec):
        st = os.stat(path)
        buf = re.sub(
            PowerStat.itemExpr,
            partial(PowerStat.makeItem, st=st),
            fmtSpec)
        return buf

    @staticmethod
    def makeItem(mat, st=None):
        """Interpret one '%'-code, as defined by *nix 'stat' command.
        """
        if (mat.group('esc')):
            k = mat.group('esc')[1]
            if   (k == 'n'): return('\n')
            elif (k == 't'): return('\t')
            elif (k == '%'): return('%')
            elif (k == '@'): return('@')
            else: raise ValueError(
                "Unrecognized escape '%s'." % (mat.group('esc')))

        fmtCode = 's'
        if mat.group('fmt'):
            if (mat.group('fmt') == 'Y'): fmtCode = 's'
            else: fmtCode = mat.group('fmt').lower()

        datumValue = PowerStat.getDatum(st,
            mat.group('datum'), mat.group('sub'), fmtCode)

        fmt = ("%" + ("%d" % (mat.group('size'))) + mat.group('prec') + fmtCode)
        val = fmt % (datumValue)
        if (mat.group('fmt') == 'Y'): val = ' -> ' + val
        return val

    @staticmethod
    def getDatumByName(st, datumName):
        try:
            return st.__getitem__[datumName]
        except KeyError:
            return None

    @staticmethod
    def getDatum(st, itemLetter, subCode, fmtCode):
        # Cases that use 'sub' code
        if (itemLetter == 'p'):  # type and perm
            return PowerStat.doPermissionBits(st, subCode, fmtCode)

        if (itemLetter == 'd'):  # device
            dev = st.st_DEV
            if   (subCode == 'H'):  # major number
                return dev
            elif (subCode == 'L'):  # minor number
                return dev
            else: raise ValueError(
                "Unrecognized d subCode '%s'." % (subCode))

        elif (itemLetter == 'r'):  # dev # for device special ***
            assert (st.IFBLK or st.IFCHR)
            dev = st.st_DEV
            if   (subCode == 'H'):  # major number
                return dev
            elif (subCode == 'L'):  # minor number
                return dev
            else: raise ValueError(
                "Unrecognized r subCode '%s'." % (subCode))

        elif (itemLetter == 'T'):  # file type like ls -F   ***
            dev = st.st_XXX
            if   (subCode == 'H'):  # long form
                return dev
            elif (subCode == 'L'):  # single-char flag
                return dev
            else: raise ValueError(
                "Unrecognized d subCode '%s'." % (subCode))

        # Datetimes (returned as epoch times
        # (stat has a -t [fmt] option, which passes these through strftime)
        elif (itemLetter == 'a'):  # access time
            return st.ST_ATIME
        elif (itemLetter == 'm'):  # mod time
            return st.ST_MTIME
        elif (itemLetter == 'c'):  # cre time
            return st.ST_CTIME
        elif (itemLetter == 'B'):  # inode birth time       ***
            return st.ST_XXX

        # Numerics
        elif (itemLetter == 'i'):  # inode
            return st.ST_INO
        elif (itemLetter == 'l'):  # hard link count
            return st.ST_NLINK
        elif (itemLetter == 'u'):  # owner uid
            return st.ST_UID
        elif (itemLetter == 'g'):  # group id
            return st.ST_GID
        elif (itemLetter == 'z'):  # size in bytes
            return st.ST_SIZE
        elif (itemLetter == 'b'):  # num blocks             ***
            return st.ST_XXX
        elif (itemLetter == 'k'):  # optimal blocksize      ***
            return st.ST_XXX
        elif (itemLetter == 'v'):  # inode generation num   ***
            return st.ST_XXX

        # Other
        elif (itemLetter == 'f'):  # user flags             ***
            return st.ST_XXX
        elif (itemLetter == 'N'):  # file name              ***
            return st.ST_XXX
        elif (itemLetter == 'Y'):  # symlink target         ***
            return st.ST_XXX
        elif (itemLetter == 'Z'):  # rdev major,minor or size ***
            return st.ST_XXX
        else:
            raise ValueError("Unrecognized datum code '%s'." % (itemLetter))

    @staticmethod
    def doPermissionBits(st, subCode, fmtCode):
        """Python 3.3 adds stat.filemode(mode), to gen the 10-char string.
        """
        if  (subCode == 'H'):
            permFlags = ''
            if (fmtCode == 's'):  # User permission bits
                permFlags += 'r' if (st.S_IRUSR) else '-'
                permFlags += 'w' if (st.S_IWUSR) else '-'
                permFlags += 'x' if (st.S_IXUSR) else '-'
            else:
                permFlags = 'TYP'
                return permFlags
        elif (subCode == 'M'):
            permFlags = ''
            if (fmtCode == 's'):  # Group bits
                permFlags += 'r' if (st.S_IRGRP) else '-'
                permFlags += 'w' if (st.S_IWGRP) else '-'
                permFlags += 'x' if (st.S_IXGRP) else '-'
            else: # TODO ???
                permFlags += 'u' if (st.S_ISUID) else '-'
                permFlags += 'g' if (st.S_ISGID) else '-'
                permFlags += 's' if (st.S_ISVTX) else '-'
            return permFlags
        elif (subCode == 'L'):
            permFlags = ''
            if (fmtCode == 's'):  # Other bits
                permFlags += 'r' if (st.S_IROTH) else '-'
                permFlags += 'w' if (st.S_IWOTH) else '-'
                permFlags += 'x' if (st.S_IXOTH) else '-'
            else:
                permFlags = 'UGO'  # TODO ???
            return permFlags
        else: raise ValueError(
            "Unrecognized p subCode '%s'." % (subCode))
        return st.ST_XXX

    @staticmethod
    def readableSize(n):
        suffixes = " KMGTP"
        rank = math.floor(math.log(n, 1000))
        if (rank >= len(suffixes)): rank = len(suffixes) - 1
        if (rank == 0):
            buf = "%d" % (n)
        else:
            scaled = n/(1000**rank)
            buf = "%6.2f%s" % (scaled, suffixes[rank])
        return buf


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def anyInt(x):
        return int(x, 0)

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--color",  # Don't default. See below.
            help='Colorize the output.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        if (args0.color == None):
            args0.color = ("USE_COLOR" in os.environ and sys.stderr.isatty())
        #lg.setColors(args0.color)
        #if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)

    ###########################################################################
    #
    fileCount = 0
    args = processOptions()

    if (len(args.files) == 0):
        warn(0, "stat.py: No files specified....")
        doOneFile(None)
    else:
        pw = PowerWalk(args.files, open=False, close=False,
            encoding=args.iencoding, recursive=args.recursive)
        pw.setOptionsFromArgparse(args)
        for path0, fh0, what0 in pw.traverse():
            if (what0 != PWType.LEAF): continue
            fileCount += 1
            if (path0.endswith(".xml")): doOneXmlFile(path0)
            else: doOneFile(path0)

    if (not args.quiet):
        warn(0, "stat.py: Done, %d files.\n" % (pw.getStat('regular')))
