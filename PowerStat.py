#!/usr/bin/env python
#
# PowerStat.py: A Python clone+lib (more or less) of 'stat'.
# 2020-11-23: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys, os
#import codecs
import stat
import math
import time
#from functools import partial

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY3:
    #from html.parser import HTMLParser
    #from html.entities import codepoint2name, name2codepoint
    import re
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): str(s, encoding, errors)
    if (sys.version_info[1] < 7):
        def isascii(s):
            if (re.match(r'^[[:ascii:]]+$', s)): return True
            return False

__metadata__ = {
    'title'        : "PowerStat.py",
    'description'  : "A Python clone+lib (more or less) of 'stat'.",
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

Do pretty much what *nix `stat` does, but from and for Python. This also adds
access to a variety of other file information accessible via the Python `stat`
interface, using an extension of the usul `stat -f` %-string, to accept names
rather than just single letters to specify the datum desired.

==Usage==

    import PowerStat
    statFormat = "-%Hu%Mu%Lu%Hg%Mg%Lg%Ho%Mo%Lo  %8su %8sg %6ds %12sm %sn"
    ps = PowerStat.PowerStat(statFormat)
    for f in myFiles:
        print(ps.format(f))

produces a display quite like `ls -ld`.

Items that don't have %-codes in normal `stats` can be gotten using similar
syntax, but replacing the final single-letter code (such as 'm' for modification
time), by `{name}`, where name is any of identifiers specified at
(for example) [https://docs.python.org/3/library/stat.html] (such as UF_HIDDEN
and many others).


=Related Commands=

*nix `stat`, `lstat`, `strftime`.


=Known bugs and Limitations=

Does not catch and report %-codes that violate the syntax rules. They're just
ignored.


=History=

* 2020-11-23: Written by Steven J. DeRose.


=To do=

Finish `--outputFormat`.


=Rights=

Copyright 2020-11-23 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
def warn(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
    if (lvl < 0): sys.exit()


###############################################################################
#
class StatItem:
    """Store the parsed fields of one %-spec, and format on request.
    Also track where in the input string the field-spec was found, so we can
    replace them correctly later.
        flag    [#+-0 ]                # sign, padding, justify,...
        siz     \\d                    # columns
        prc     \\.\\d+                # precision
        fmtCode [DOUXFS]               # dec, oct, udec, hex, float, str
        subCode [HLM]                  # which part for pdrT
        datum   [diplugramcBzbkfvNTYZ] # what actual data item
    There are also specials like %[nt%@].
    """
    def __init__(self, mat):
        self.pctString   = mat.groups(0)
        self.startOffset = mat.start(0)
        self.endOffset   = mat.end(0)
        self.esc         = mat.group('esc') or False
        self.flag        = mat.group('flag') or ''
        self.siz         = mat.group('siz') or ''
        self.prc         = mat.group('prc') or ''
        self.fmtCode     = mat.group('fmt') or ''
        self.subCode     = mat.group('sub') or ''
        self.datum       = mat.group('datum')

    @staticmethod
    def munge(mat, st):  # TODO: FIX, divide parse/store from format
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

        if (mat.group('datumName')):
            fmtCode = 's'
            raise ValueError(
                "Not yet supported: %s." % (mat.group('datumName')))
        else:
            datumCode = mat.group('datum')
            if (datumCode == 'p'): fmtCode = 'o'
            elif (datumCode in 'amc'): fmtCode = 'd'
            elif (datumCode in 'YTN'): fmtCode = 's'
            else: fmtCode = 'u'

        flag = '0'
        if mat.group('flag'): flag = mat.group('flag')
        siz = ''
        if mat.group('siz'): flag = mat.group('siz')
        prc = ''
        if mat.group('prc'): flag = mat.group('prc')
        if mat.group('fmt'):
            if (mat.group('fmt') == 'Y'): fmtCode = 's'
            else: fmtCode = mat.group('fmt').lower()
        sub = ''
        if mat.group('sub'):
            if (datumCode not in 'pdrT'): raise ValueError(
                "sub code '%s' used for field '%d', not allowed." %
                (sub, datumCode))
            else:
                flag = mat.group('sub')

        datumValue = PowerStat.getDatum(st, datumCode, sub, fmtCode)

        fmt = "%" + siz + prc + fmtCode
        val = fmt % (datumValue)
        if (mat.group('fmt') == 'Y'): val = ' -> ' + val
        return val

    def formatDatum(self, st, theTimeFormat=None):
        """This gets the raw datum given its code and subcode, and then formats
        it as requested.
        """
        # Cases that use 'sub' code
        if (self.datum == 'p'):                 # type and perm
            return PowerStat.doPermissionBits(st, self.subCode, self.fmtCode)

        if (self.datum == 'd'):                 # device
            # TODO: if (self.fmtCode == 's'): actual device name
            # d gives a 4-byte int, where high order byte is major, low minor.
            dev = st[stat.ST_DEV]
            if   (self.subCode == 'H'):              # major number
                return dev >> 24
            elif (self.subCode == 'L'):              # minor number
                return dev & 0xFF
            elif (self.subCode == ''):               # raw number
                return dev
            else: raise ValueError(
                "Unrecognized d self.subCode '%s'." % (self.subCode))

        elif (self.datum == 'r'):               # dev # for device special ***
            assert (st.IFBLK or st.IFCHR)
            dev = st[stat.ST_DEV]
            if   (self.subCode == 'H'):              # major number
                return dev
            elif (self.subCode == 'L'):              # minor number
                return dev
            else: raise ValueError(
                "Unrecognized r self.subCode '%s'." % (self.subCode))

        elif (self.datum == 'T'):               # file type like ls -F   ***
            dev = st.ST_XXX
            # TODO: if (self.fmtCode == 's'): actual file type
            if   (self.subCode == 'H'):              # long form
                return dev
            elif (self.subCode == 'L'):              # single-char self.flag
                return dev
            else: raise ValueError(
                "Unrecognized d self.subCode '%s'." % (self.subCode))

        # Datetimes (returned as epoch times
        # (stat has a -t [fmt] option, which passes these through strftime)
        elif (self.datum in 'amcB'):
            if   (self.datum == 'a'):           # access time
                tim = st[stat.ST_ATIME]
            elif (self.datum == 'm'):           # mod time
                tim = st[stat.ST_MTIME]
            elif (self.datum == 'c'):           # cre time
                tim = st[stat.ST_CTIME]
            elif (self.datum == 'B'):           # inode birth time       ***
                tim = st.st_birthtime
            return PowerStat.formatTime(tim, theTimeFormat)

        # Numerics
        elif (self.datum == 'i'):               # inode
            return st[stat.ST_INO]
        elif (self.datum == 'l'):               # hard link count
            return st[stat.ST_NLINK]
        elif (self.datum == 'u'):               # owner uid
            return st[stat.ST_UID]
        elif (self.datum == 'g'):               # group id
            return st[stat.ST_GID]
        elif (self.datum == 'z'):               # self.size in bytes
            return st[stat.ST_SIZE]

        elif (self.datum == 'b'):               # num blocks             ***
            return st.ST_XXX
        elif (self.datum == 'k'):               # optimal blockself.size ***
            return st.ST_XXX
        elif (self.datum == 'v'):               # inode generation num   ***
            return st.ST_XXX

        # Other
        elif (self.datum == 'f'):               # user self.flags        ***
            return st.ST_XXX

        # Not actually from 'stat' struct (likewise 'T')
        elif (self.datum == 'N'):               # file name              ***
            # TODO: if (self.fmtCode == 's'): actual file name
            return st.ST_XXX
        elif (self.datum == 'Y'):               # symlink target         ***
            return st.ST_XXX
        elif (self.datum == 'Z'):               # rdev major,minor or self.size ***
            return st.ST_XXX
        else:
            raise ValueError("Unrecognized datum code '%s'." % (self.datum))

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
        rank = int(math.log(n, 1000))
        if (rank >= len(suffixes)): rank = len(suffixes) - 1
        if (rank == 0):
            buf = "%d" % (n)
        else:
            scaled = n/(1000**rank)
            buf = "%6.2f%s" % (scaled, suffixes[rank])
        return buf

    @staticmethod
    def formatTime(epochTime, f=None):
        if (f is None): f = "%a, %d %b %Y %H:%M:%S %Z"
        return time.strftime(f, epochTime)



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
    flag    = r'(?P<flag>[#+-0 ])?'     # sign, padding, justify,...
    siz     = r'(?P<siz>\d)?'
    prc     = r'(?P<prc>\.\d+)?'        # only for time fields
    fmt     = r'(?P<fmt>[DOUXFS])?'     # dec, oct, udec, hex, float, str
    sub     = r'(?P<sub>[HLM])?'        # which part for pdrT
    datum   = r'(?P<datum>[diplugramcBzbkfvNTYZ])'
    # datum += r'|{<?P<datumName>\w+)'

    itemExpr = re.compile('%' + flag + siz + prc + fmt + sub + datum +
        "|%(?P<esc>[nt%@])")

    def __init__(self, statFormat=None, timeFormat=None):
        """Parse a `stat -f` argument into an array of literals and %-items.
        """
        self.statFormat = statFormat
        self.theItems = []  # A mix of StatItems and literal strs
        lastEnd = 0
        for mat in re.finditer(PowerStat.itemExpr, statFormat):
            if (mat.start() > lastEnd):
                self.theItems.append(statFormat[lastEnd:mat.start()])
            self.theItems.append(StatItem(mat))
            lastEnd = mat.end()
        if (len(statFormat) > lastEnd):
            self.theItems.append(statFormat[lastEnd:])

        if (timeFormat is None):
            self.timeFormat ="%a %b %d %H:%M:%S %Z %Y"   # asctime
        elif (timeFormat == 'ISO8601'):
            self.timeFormat ="%Y-%m-%dT%H:%M:%S%z"       # ISO 8601
        else:
            self.timeFormat = timeFormat

    def format(self, path):
        st = os.stat(path)
        buf = ''
        for _i, thisItem in enumerate(self.theItems):
            if (isinstance(thisItem, str)):
                buf += thisItem
            else:
                buf += thisItem.format(st)
        return buf

    def formatTime(self, t):
        assert False, "formatTime not yet implemented."

    @staticmethod
    def getDatumByName(st, datumName):
        try:
            return st.__getitem__[datumName]
        except KeyError:
            return None


###############################################################################
# Main
#
if __name__ == "__main__":
    statFormat0 = "-%Hu%Mu%Lu%Hg%Mg%Lg%Ho%Mo%Lo  %8su %8sg %6ds %12sm %sn"
    timeFormat0 = "%Y-%m-%dT%H:%M:%S %Z"
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
            "--outputFormat", "--output-format", "--oformat", "-o",
            type=str, default="plain",
            choices = [ "plain", "html", "xsv", "csv", "tsv" ],
            help='Record/field syntax for output.')
        parser.add_argument(
            "--statFormat", "-s", type=str, default=statFormat0,
            help='stat-like percent-codes to determine output format.')
        parser.add_argument(
            "--timeFormat", "-t", type=str, default=timeFormat0,
            help='strftime-like percent-codes to determine time output format.')
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
    args = processOptions()

    warn(1, "Stat format spec is: '%s'" % (args.statFormat))
    ps = PowerStat(args.statFormat, args.timeFormat)

    if (len(args.files) == 0):
        warn(0, "stat.py: No files specified....")
        sys.exit()
    for f0 in args.files:
        print(ps.format(f0))
