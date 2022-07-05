#!/usr/bin/env python3
#
# PowerStat.py: A Python clone+lib (more or less) of 'stat'.
# 2020-11-23: Written by Steven J. DeRose.
#
import sys
import os
#from os import stat as osstat  # See lsanc.py for example
#import codecs
import stat
import math
import time
from typing import Any, Dict, Union
import re
import pwd
import grp
#from functools import partial

PY3 = sys.version_info[0] == 3
if (PY3 and sys.version_info[1] < 7):
    def isascii(s):
        if (re.match(r'^[[:ascii:]]+$', s)): return True
        return False

__metadata__ = {
    'title'        : "PowerStat",
    'description'  : "A Python clone+lib (more or less) of 'stat'.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-11-23",
    'modified'     : "2021-08-31",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

[UNFINISHED]

Do pretty much what *nix `stat` does, but from and for Python. This also adds
access to a variety of other file information accessible via the Python `stat`
interface, using an extension of the usual `stat -f` %-string, to accept names
rather than just single letters to specify the datum desired.

==Usage as Command==

    PowerStat.py [file]
    
This will do the same thing as `stat [file]'. Except it isn't right yet.
It does have `-x` to display a more readable form.

The most visible change is that the -f (format) option can take names
instead of just single letters for what to show. See below under "Formats".

==Usage as Library==

    import PowerStat
    statFormat = "-%Hu%Mu%Lu%Hg%Mg%Lg%Ho%Mo%Lo  %8su %8sg %6ds %12sm %sn"
    ps = PowerStat.PowerStat(statFormat)
    for f in myFiles:
        print(ps.format(f))

produces a display quite like `ls -ld`.

Several pre-defined formats are available via a mnemonic name in dict `statFormats`.

Items that don't have %-codes in normal `stats` can be gotten using similar
syntax, but replacing the final single-letter code (such as 'm' for modification
time), by `{name}`, where name is any of identifiers specified at
(for example) [https://docs.python.org/3/library/stat.html] (such as UF_HIDDEN
and many others).

==Additions==

This package also provide a few generally-useful methods, such as:

* PowerStat.StatItem.getFlag(s) -- givne either a path or an os.stat_result,
return the flag character like "ls -F" appends to file names ("/" for directories, etc.).

==Formats==

For the most part, the format specifications here follow those of `stat`.
They can be placed into a format-definition string by prefixing
them with "%", but have a load of syntax, mostly optional:

The first several fields of a format item are very similar to those of `sprintf` or
Python `format()` [https://docs.python.org/3.9/library/string.html#formatspec].

* Optional flags: Any of all of [#+-0] for affect leading zeros, signs, left-alignment, etc.
    #  Prefixes octal with '0', hex with '0x'
    +  Always show sign
    -  Left-align (vs. '<' in Python)
    0  Left-pad with 0 instead of space
       (space) -- Puts a space in the sign columns ('+' overrides ' ')
    
* (Python adds ',' and '_' to manage thousands-separator in integers.
May also want a modifier to magnitude suffixes, like `-H` for many commands.

* size (digits) for minimum field width

* precision ("." + digits)

* fmtCode 
    D  decimal
    O  octal
    U  unsigned decimal
    X  hex
    F  float
    S  string

For some fields, like 'u' for user, the 'S' form is a name, and the H form is the id.
S for dates uses `strftime` formats.

Python also has 'b' for binary, 'c' for char conversion of an int, 'x' vs. 'X' to
control the case of [A-F], and 'n' to insert number separators. Also, they're 
lower case except for 'X'. For floats, [eEfFgGn%] are added.

Truncation (max width) would also be nice, esp. for strings.

* sub [HML] only applies to p (permissions), d (device a file is on), 
r (device number for specials), and T (file type like `ls -F`). `sub` selects the
"High", "Middle", or "Low" aspect

* dataum -- the actual data item being rendered:
    d  device       device (for files)
    i  inode        inode
    p  perm         type and permissions
    l  nlinks       number of hard links
    u  user         user (use fmtCode to pick number vs. name)
    g  group        group (use fmtCode to pick number vs. name)
    r  device       number (for specials)
    a  atime        access time (times have special format controls)
    m  mtime        modification time
    c  ctime        creation time
    B  btime        inode birth time
    z  bytes        size in bytes
    b  blocks       size in blocks
    k  pblock       preferred block size
    f  flags        flags, like `ls -lTdo`
    v  igen         inode generation
    N  name         full name
    R  path         absolute path
    T  type         type (as in `ls -F`)
    Y  target       symlink target
    Z  ???          ('major,minor' for character or block special files, otherwise size)

Added items:
    x  extension    file extension (not including the '.')
                    base name without extension
                    
??? The preceding fields also get synonyms? space sep inside the ()?

    
You can also use, for any of these, the mnemonic name shown above, instead of just
a single letter.

For example, instead of

    stat -f "-%Hu%Mu%Lu%Hg%Mg%Lg%Ho%Mo%Lo  %8su %8sg %6ds %12sm %sn"
    
you could say:

    stat -f "-%(Hu)%(Mu)%(Lu)%(Hg)%(Mg)%(Lg)%(Ho)%(Mo)%(Lo  )%(8su )%(8sg )%(6ds )%(12sm )%sn"

==Examples==

* %uS gets the user name as a string.


=Related Commands=

*nix `stat`, `lstat`, `strftime`.

*nix `stat` has a "-r" ("raw") option, with output like:
    16777221 1152921500312764962 0120755 1 0 0 0 11 1577865600 1577865600 1577865600 1577865600 4096 0 557056 [path]
    
This option is also available here. `man stat` (at least on MacOS) does not explain
the format. It is all decimal fields except for the third field, which is octal
(as usual for permissions bits). The fields in order represent (afaict):

        st.ST_DEV
        st.ST_INO
        st.mode
        st.ST_NLINK
        st.ST_UID
        st.ST_GID
        ?????
        st.ST_SIZE
        st.ST_ATIME
        st.ST_MTIME
        st.ST_CTIME
        st.st_birthtime
        st.st_blksize
        st.st_blocks
        st.st_rdev
        path

Other fields may exist on various OSes, for example:       
        st.st_atime_ns
        st.st_mtime_ns
        st.st_ctime_ns
        st.st_flag
        st.st_gen
        st.st_fstype
        st.st_rsize
        st.st_creator
        st.st_type


=To Do=

* Get defailt output format into sync with `stat` command.
* Add `-l' to output like `ls -lT` (like stat).
* Add `-L` to use stat() instead of lstat()
* Sync up with rest of `stat` options: -F -q -r -s.
* Split device number in -x to match `stat`.


=Known bugs and Limitations=

Unfinished.

stat sometimes returns a mode greater than 0x7777. Not sure what the
extra bits are for, yet. But they're stripped with -x so the output matches
`stat -x`, and then (if present) reported on a separate line.

Does not catch and report %-codes that violate the syntax rules. They're just
ignored.

Finish `--outputFormat`.


=History=

* 2020-11-23: Written by Steven J. DeRose.
* 2021-06-03: More work on parsing/mapping `stat`-style format specs.
* 2021-08-31: Add --namedStatFormats.
* 2021-09-15: Fix bug calculating format() %-strings when fmtCode omitted.
* 2021-12-13: Add -n, -x like `stat`, --human; placeholders for some more.

==Rights=

Copyright 2020-11-23 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
args = None

def log(lvl:int, msg:str) -> None:
    if (not args or args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg:str) -> None: log(0, msg)
def warning1(msg:str) -> None: log(1, msg)
def warning2(msg:str) -> None: log(2, msg)
def fatal(msg:str) -> None: log(0, msg); sys.exit()


###############################################################################
# Provide some useful pre-defined formats
#
# *** Where are these from? `ls'?
#
#    -@    Display extended attribute keys and sizes in long (-l) output.
#    -e    Print the Access Control List (ACL) associated with the file, if present.
#    -g    Display the group name in the long (-l) format output (the owner name is suppressed).
#    -h    When used with the -l option, use unit suffixes: Byte, Kilobyte, etc. in
#          order to reduce the number of digits to three or less using base 2 for sizes.
#    -i    For each file, print the file's file serial number (inode number).
#    -k    If the -s option is specified, print the file size allocation in kilobytes, not blocks.
#    -l    (``ell''.)  List in long format.
#    -n    Display user and group IDs numerically in a long (-l) output.
#    -O    Include the file flags in a long (-l) output.
#    -o    List in long format, but omit the group id.
#    -s    Display the number of blocks actually used by each file, in units of 512 bytes, rounded up.
#
# Times:
#    -c    Use time when file status was last changed for sorting (-t) or long printing (-l).
#    -T    When used with the -l (``ell'') option, display complete time information for the file,
#          including month, day, hour, minute, second, and year.
#    -u    Use time of last access, instead of last modification of the file.
#    -U    Use time of file creation, instead of last modification.
#
# Special chars:
#    -B    Force printing of non-printable characters in file names
#          as \xxx, where xxx is the numeric value of the character in octal.
#    -b    As -B, but use C escape codes whenever possible.
#    -q    Force printing of non-graphic characters in file names as `?'; default for a terminal.
#    -v    Force unedited printing of non-graphic characters; default when output is not to a terminal.
#    -w    Force raw printing of non-printable characters.  Default when output is not to a terminal.
#
# Flags:
#    -F    Display a slash (`/') after each pathname that is a directory, an asterisk (`*') for
#          executable, an at sign (`@') for symbolic link, an equals sign (`=') for socket, a percent
#          sign (`%') for whiteout, and a vertical bar (`|') for FIFO.
#    -p    Write a slash (`/') after each filename if that file is a directory.
#    -%    Distinguish dataless files and directories with a '%' character.
#
# ******* The mnemonics used below are based on `ls` options (q.v).
#
permBits = "%SHp%SMp%SLp"
statFormats:Dict[str, str] = {
        # 0----+----1----+----2----+----3----+----4----+----5----+----6----+----7
    "ls_l":    "-" + permBits + "  %8su %8sg %6ds %12sm %sn",
        # -rwxr-xr-x  1 sderose  staff    21K Jul 13 13:35 BlockFormatter.py
    "ls_g":    "-" + permBits + "  %8sg %6ds %12sm %sn",
        # -rwxr-xr-x  1 staff    21K Jul 13 13:35 BlockFormatter.py
    "ls":      "%sn",
        # BlockFormatter.py
    #"ls_F":    ""
        # BlockFormatter.py*
}

###############################################################################
# More semantically useful types for data
#
class Epoch(float):
    pass
    
class Unsigned(int):
    pass


###############################################################################
#
class StatItem:
    """Store the parsed fields of one %-spec, and format on request.
    @param mat: An entire regex match object, whose content is one %-code.
    The regex puts the various (mostly optional) parts in named captures.

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

    # Map each chosen datum (see `stat`) to the sprintf field type it defaults to.
    defaultFmtCodes = {
        # The first few are not in struct stat:
        #datum code actual-type
        "N": ( "s", str ),       # The name of the file.
        "T": ( "s", str ),       # Flag as in ls -F, or more descriptive if 'H' given.
        "Y": ( "s", str ),       # The target of a symbolic link.
        "Z": ( "s", str ),       # ``major,minor'' from rdev field for char/block special; else size
        #code:  ( sprintfType, datumType )
        "B": ( "t", Epoch ),     # inode birth time
        "a": ( "t", Epoch ),     # access time
        "b": ( "d", Unsigned ),  # Number of blocks allocated for file.
        "c": ( "t", Epoch ),     # creation time
        "d": ( "s", str ),       # Device upon which file resides.
        "f": ( "?", str ),       # User defined flags for file.
        "g": ( "d", Unsigned ),  # Group ID of file's owner.
        "i": ( "d", Unsigned ),  # file's inode number.
        "k": ( "d", Unsigned ),  # Optimal file system I/O operation block size.
        "l": ( "d", Unsigned ),  # Number of hard links to file.
        "m": ( "t", Epoch ),     # mod time
        "p": ( "s", str ),       # File type and permissions.
        "r": ( "d", Unsigned ),  # Device number for character/block device special files.
        "u": ( "d", Unsigned ),  # User id of file's owner
        "v": ( "d", Unsigned ),  # Inode generation number.
        "z": ( "d", Unsigned ),  # The size of file in bytes.
    }

    @staticmethod
    def getItemRegex():
        """Set up regex to parse a single %... item spec from the format string.
        This captures all the parts into named capture buffers.
        """
        flag    = r'(?P<flag>[#+-0 ])?'         # sign, padding, justify,...
        siz     = r'(?P<siz>\d)?'
        prc     = r'(?P<prc>\.\d+)?'            # only for time fields
        fmtCode = r'(?P<fmtCode>[DOUXFS])?'     # dec, oct, udec, hex, float, str
        sub     = r'(?P<sub>[HLM])?'            # which part for pdrT
        datum   = r'(?P<datum>[BNTYZabcdfgiklmpruvz])'

        # Consistency check
        datumsInTable = "".join(sorted(StatItem.defaultFmtCodes.keys()))
        if (not datum.endswith(datumsInTable+'])')):
            fatal("datum regex '%s'\n   does not match keys [%s]" %
                (datum, datumsInTable))

        # datum += r'|{<?P<datumName>\w+)'
        itemExpr = '%' + flag + siz + prc + fmtCode + sub + datum + "|%(?P<esc>[nt%@])"
        return re.compile(itemExpr)

    def __init__(self, mat:re.Match):
        assert isinstance(mat, re.Match)
        self.mat         = mat  # Should go away?
        self.pctString   = mat.group(0)
        self.startOffset = mat.start(0)
        self.endOffset   = mat.end(0)
        self.esc         = mat.group('esc') or False
        self.flag        = mat.group('flag') or ''     # [#+-0 ]?
        self.siz         = self.intCap(mat, 'siz')     # min field width
        self.prc         = mat.group('prc') or ''      # .precision
        self.fmtCode     = mat.group('fmtCode') or ''  # [DOUXFS]?
        # decimal, octal, unsigned decimal, hex, float (only a/m/c timespecs), string.
        self.subCode     = mat.group('sub') or ''      # [HML]?
        self.datum       = mat.group('datum')          # field specifier char
        self.typ         = None                        # As from defaultFmtCodes (?)

        self.sprintfCode = "%"
        if (self.flag in "+-0"): self.sprintfCode += self.flag
        if (self.siz): self.sprintfCode += str(self.siz)
        if (self.prc): self.sprintfCode += self.prc

        if (self.fmtCode is None or self.fmtCode == ''):
            dft, self.typ = self.defaultFmtCodes[self.datum]
            warning1("fmtCode empty, dft '%s' typ '%s'." % (dft, self.typ))
            if (dft!='t'): self.sprintfCode += dft
            else: self.sprintfCode += 's'  # times are strings...
        elif (self.fmtCode in "DOUXFS"):
            self.sprintfCode += self.fmtCode.lower()
            warning1("fmtCode '%s' in DOUXFS '%s'." % (self.fmtCode, self.fmtCode.lower()))
        else:
            assert False, "Bad fmtCode '%s' in:\n%s" % (self.fmtCode, self.tostring())
        warning1("Created format item: '%s'\n%s" % (self.sprintfCode, self.tostring()))

    def tostring(self) -> str:
        buf = "From '%s':\n" % (self.pctString or "-none-")
        for k in [ 'esc', 'flag', 'siz', 'prc', 'fmtCode', 'sub', 'datum' ]:
            buf += "      %-8s = '%s'\n" % (k, self.mat.group(k) or "-none-")
        buf += "    Derived format() code: '%s'." % (self.sprintfCode)
        return buf

    @staticmethod
    def intCap(mat:re.Match, captureName:str, default:int=0) -> int:
        """Retrieve the named capture group from the match object, but cast to int.
        If it's not there, return the default.
        """
        try:
            return int(mat.group(captureName))
        except ValueError:
            return int(default)
        except TypeError:
            return int(default)

    def munge(self, st:os.stat_result):  # TODO: FIX, divide parse/store from format
        """Interpret one '%'-code, as defined by *nix 'stat' command.
        """
        if (self.mat.group('esc')):
            k = self.mat.group('esc')[1]
            if (k == 'n'): return('\n')
            elif (k == 't'): return('\t')
            elif (k == '%'): return('%')
            elif (k == '@'): return('@')
            else: raise ValueError("Unrecognized escape '%s'." % (self.mat.group('esc')))

        if (self.mat.group('datumName')):
            fmtCode = 's'
            raise ValueError(
                "Not yet supported: %s." % (self.mat.group('datumName')))
        else:
            datumCode = self.mat.group('datum')
            if (datumCode == 'p'): fmtCode = 'o'
            elif (datumCode in 'amc'): fmtCode = 'd'
            elif (datumCode in 'YTN'): fmtCode = 's'
            else: fmtCode = 'u'

        flag = ''  # [#+-0 ] for sign, padding, justify,...
        if self.mat.group('flag'): flag = self.mat.group('flag')
        siz = ''
        if self.mat.group('siz'): flag = self.mat.group('siz')
        prc = ''
        if self.mat.group('prc'): flag = self.mat.group('prc')
        if self.mat.group('fmtCode'):
            if (self.mat.group('fmtCode') == 'Y'): fmtCode = 's'
            else: fmtCode = self.mat.group('fmtCode').lower()
        sub = ''
        if self.mat.group('sub'):
            if (datumCode not in 'pdrT'): raise ValueError(
                "sub code '%s' used for field '%d', not allowed." %
                (sub, datumCode))
            else:
                flag = self.mat.group('sub')

        datumValue = self.getDatumValue(st)

        pctCode = "%" + flag + siz + prc + fmtCode
        val = pctCode % (datumValue)
        if (self.mat.group('fmtCode') == 'Y'): val = ' -> ' + val
        return val

    def formatItem(self, st:os.stat_result, theTimeFormat:str=None) -> str:
        """This gets the raw datum given its code and subcode, and then formats
        it as requested.
        This may raise ValueError, as for a bad sprintfCode.
        """
        datum = self.getDatumValue(st)
        if (self.typ == Epoch):
            return self.formatTime(datum, theTimeFormat)
        if (self.typ == Unsigned):
            return self.sprintfCode % (datum)
        else:
            return self.sprintfCode % (datum)

    def getDatumValue(self, st:os.stat_result) -> Any:
        """This gets the raw datum in raw form, given its code and subcode.

        TODO: Fill in the remaining stat_result references.
        """
        # Cases that use 'sub' code
        if (self.datum == 'p'):                 # type and perm
            return self.doPermissionBits(st, self.subCode, self.fmtCode)

        if (self.datum == 'd'):                 # device
            # TODO: if (self.fmtCode == 's'): actual device name
            # d gives a 4-byte int, where high order byte is major, low minor.
            dev = st[stat.ST_DEV]
            if (self.subCode == 'H'):                # major number
                return str(dev >> 24)
            elif (self.subCode == 'L'):              # minor number
                return dev & 0xFF
            elif (self.subCode == ''):               # raw number
                return dev
            else: raise ValueError(
                "Unrecognized d self.subCode '%s'." % (self.subCode))

        elif (self.datum == 'r'):                    # dev # for device special ***
            assert (st[stat.S_IFBLK] or st[stat.S_IFCHR])
            dev = st[stat.ST_DEV]
            if (self.subCode == 'H'):                # major number
                return dev
            elif (self.subCode == 'L'):              # minor number
                return dev
            else: raise ValueError(
                "Unrecognized r self.subCode '%s'." % (self.subCode))

        elif (self.datum == 'T'):               # file type like ls -F   ***
            # TODO: if (self.fmtCode == 's'): actual file type
            if (self.subCode == 'H'):                # long form
                return self.getFlag(st, shortName=False)
            elif (self.subCode == 'L'):              # single-char self.flag
                return self.getFlag(st, shortName=True)
            else: raise ValueError(
                "Unrecognized d self.subCode '%s'." % (self.subCode))

        # Datetimes (returned as epoch times
        # (stat has a -t [format] option, which passes these through strftime)
        elif (self.datum in 'amcB'):
            if (self.datum == 'a'):             # access time
                tim = st[stat.ST_ATIME]
            elif (self.datum == 'm'):           # mod time
                tim = st[stat.ST_MTIME]
            elif (self.datum == 'c'):           # cre time
                tim = st[stat.ST_CTIME]
            elif (self.datum == 'B'):           # inode birth time       ***
                tim = st.st_birthtime
            return tim

        # Numerics
        elif (self.datum == 'i'):               # inode
            return st[stat.ST_INO]
        elif (self.datum == 'l'):               # hard link count
            return st[stat.ST_NLINK]
        elif (self.datum == 'u'):               # owner uid / user id
            return st[stat.ST_UID]
        elif (self.datum == 'g'):               # group id
            return st[stat.ST_GID]
        elif (self.datum == 'z'):               # self.size in bytes
            return st[stat.ST_SIZE]

        #elif (self.datum == 'b'):               # num blocks             ***
        #    return st.ST_XXX
        #elif (self.datum == 'k'):               # optimal blockself.size ***
        #    return st.ST_XXX
        #elif (self.datum == 'v'):               # inode generation num   ***
        #    return st.ST_XXX

        # Other
        #elif (self.datum == 'f'):               # user self.flags        ***
        #    return st.ST_XXX

        # Not actually from 'stat' struct, bit in stat(1)
        #elif (self.datum == 'N'):               # file name              ***
        #    # TODO: if (self.fmtCode == 's'): actual file name
        #    return st[stat.ST_XXX]
        #elif (self.datum == 'R'):               # file name              ***
        #    # TODO: if (self.fmtCode == 's'): actual file name
        #    return st[stat.ST_XXX]
        #elif (self.datum == 'T'):               # file name              ***
        #    # TODO: if (self.fmtCode == 's'): actual file name
        #    return st[stat.ST_XXX]
        #elif (self.datum == 'Y'):               # symlink target         ***
        #    return st[stat.ST_XXX]
        #elif (self.datum == 'Z'):               # rdev major,minor or self.size ***
        #    return st[stat.ST_XXX]
        else:
            raise ValueError("Unrecognized datum code '%s'." % (self.datum))

    @staticmethod
    def getFlag(st:Union[os.stat_result, str], shortName:bool=True) -> str:
        """Return the same single character file type flag that "ls -F" would,
        to append/suffix to this item. Can also provide a long form of it.
        TODO: Find and add the non-short names that it wants....
        """
        if (isinstance(st, str)):
            st = os.stat(st)
        mode = st.st_mode
        if (stat.S_ISDIR(mode)):  return "/" if (shortName) else "/"
        # TODO: Which executagble bit(s) does ls -F actually report?
        if (stat.S_ISLNK(mode)):  return "@" if (shortName) else "@"  # symbolic link
        if (stat.S_ISSOCK(mode)): return "=" if (shortName) else "="  # after each socket
        if (stat.S_ISFIFO(mode)): return "|" if (shortName) else "|"  # FIFO
        # TODO: Is this not supported on MacOS or something?
        #if (stat.S_ISWHT(mode)):  return "%" if (shortName) else "%"  # whiteout
        #if (st.S_ISWHT):  return "%" if (shortName) else "%"  # whiteout
        #if (st.S_IXUSR or st.S_IXGRP or st.S_IXOTH): return "*" if (shortName) else "*"
        return ""

    @staticmethod
    def doPermissionBits(st:os.stat_result, subCode:str, fmtCode:str):
        """Python 3.3 adds stat.filemode(mode), to gen the 10-char string.
        """
        if  (subCode == 'H'):
            permFlags = ''
            if (fmtCode == 's'):  # User permission bits
                permFlags += 'r' if (st[stat.S_IRUSR]) else '-'
                permFlags += 'w' if (st[stat.S_IWUSR]) else '-'
                permFlags += 'x' if (st[stat.S_IXUSR]) else '-'
            else:
                permFlags = 'TYP'
                return permFlags
        elif (subCode == 'M'):
            permFlags = ''
            if (fmtCode == 's'):  # Group bits
                permFlags += 'r' if (st[stat.S_IRGRP]) else '-'
                permFlags += 'w' if (st[stat.S_IWGRP]) else '-'
                permFlags += 'x' if (st[stat.S_IXGRP]) else '-'
            else: # TODO ??? permissions subCodes?
                permFlags += 'u' if (st[stat.S_ISUID]) else '-'
                permFlags += 'g' if (st[stat.S_ISGID]) else '-'
                permFlags += 's' if (st[stat.S_ISVTX]) else '-'
            return permFlags
        elif (subCode == 'L'):
            permFlags = ''
            if (fmtCode == 's'):  # Other bits
                permFlags += 'r' if (st[stat.S_IROTH]) else '-'
                permFlags += 'w' if (st[stat.S_IWOTH]) else '-'
                permFlags += 'x' if (st[stat.S_IXOTH]) else '-'
            else:
                permFlags = 'UGO'  # TODO ??? more permissions flags
            return permFlags
        else: raise ValueError(
            "Unrecognized p subCode '%s'." % (subCode))
        return None  #st.ST_XXX

    @staticmethod
    def readableFileSize(n:int) -> str:
        """Make a readable size like many -H options (or here, --human).
        """
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
    def readableFileType(mode:int, st:os.stat_result=None) -> str:
        """Generate a keyword for the kind of thing.
        """
        if (stat.S_ISBLK(mode)):  return "Block special"
        if (stat.S_ISCHR(mode)):  return "Character special"
        if (stat.S_ISDIR(mode)):  return "Directory"
        if (stat.S_ISDOOR(mode)): return "Door"
        if (stat.S_ISFIFO(mode)): return "FIFO"
        if (stat.S_ISLNK(mode)):  return "Symlink"
        if (stat.S_ISPORT(mode)): return "Port"
        if (stat.S_ISSOCK(mode)): return "Socket"
        if (stat.S_ISWHT(mode)):  return "Whiteout"
        if (stat.S_ISREG(mode)):  return "Rgular file"
        raise ValueError("Could not identify type of file '%s'." % (st.__name__))
        
    @staticmethod
    def readableUserId(uid:int) -> str:
        """Numeric to string user id.
        """
        return pwd.getpwuid(uid).pw_name

    @staticmethod
    def readableGroupId(gid:int) -> str:
        """Numeric to string group id.
        """
        return grp.getgrgid(gid).gr_name

    @staticmethod
    def formatTime(epochTime:int, f:str=None) -> str:
        if (f is None): f = "%a, %d %b %Y %H:%M:%S %Z"
        return time.strftime(f, epochTime)

    @staticmethod
    def epochTimeToAsctime(epochTime:int, local:bool=False) -> str:
        if (local): structTime = time.localtime(epochTime)
        else: structTime = time.gmtime(epochTime)
        return time.asctime(structTime)
        
        
###############################################################################
#
class PowerStat:
    """Extract and format info much like 'stat'.
    A format item is like:
        % flag? space? size? prec? fmtCode? sub? datum

    There's a lot in stat that still isn't accessible this way. Perhaps
    Add datum field like {statName}', to just use any name python stat knows?
    (see https://docs.python.org/3/library/stat.html)
    """

    def __init__(self, statFormat:str=None, timeFormat:str=None):
        """Parse a `stat -f` argument into an array of literals and %-items.
        """
        self.itemExpr = StatItem.getItemRegex()
        self.statFormat = statFormat
        self.theItems = []  # A mix of StatItems and literal strs
        lastEnd = 0
        for mat in re.finditer(self.itemExpr, statFormat):
            if (not mat.group('datum') and not mat.group('esc')):
                fatal("Could not parse format item '%s' after column %d." %
                    (statFormat, lastEnd))
            if (mat.start() > lastEnd):  # Save inter-item literal text
                self.theItems.append(statFormat[lastEnd:mat.start()])
            # We save the entire match object, with named captures:
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

    def format(self, path:str) -> str:
        st = os.stat(path)
        buf = ''
        for i, thisItem in enumerate(self.theItems):
            if (isinstance(thisItem, str)):
                buf += thisItem
            elif (isinstance(thisItem, StatItem)):
                try:
                    buf += "%s" % thisItem.formatItem(st, theTimeFormat=args.timeFormat)
                except ValueError as e:
                    fatal("format error for item, derived sprintf code '%s':\n    %s\n%s" %
                        (thisItem.sprintfCode, thisItem.tostring(), e))
            else:
                assert False, "theItems[%d] is of type %s." % (i, type(thisItem))
        return buf

    @staticmethod
    def getDatumValueByName(st:os.stat_result, datumName:str):
        try:
            return st.__getitem__[datumName]
        except KeyError:
            return None


linuxFormat = """File: "%s"
  Size: %-12s         FileType: %s
  Mode: (%04o/%10s)         Uid: (%5d/ %s)  Gid: (%5d/ %s)
Device: %s   Inode: %-10d Links: %d
Access: %s
Modify: %s
Change: %s"""

def getLinuxFormat(path, st:os.stat_result) -> str:
    if (args.human): sizeStr = StatItem.readableFileSize(st[stat.ST_SIZE])
    else: sizeStr = "%s" % (st[stat.ST_SIZE])
    
    buf = linuxFormat % (
        path,
        sizeStr, StatItem.readableFileType(md, st),
        mdLow, stat.filemode(md), 
        st[stat.ST_UID], StatItem.readableUserId(st[stat.ST_UID]),
        st[stat.ST_GID], StatItem.readableGroupId(st[stat.ST_GID]),
        st[stat.ST_DEV], st[stat.ST_INO], st[stat.ST_NLINK],
        StatItem.epochTimeToAsctime(st[stat.ST_ATIME]),
        StatItem.epochTimeToAsctime(st[stat.ST_MTIME]),
        StatItem.epochTimeToAsctime(st[stat.ST_CTIME])
    )
    return buf

# Based on what I see in MacOS Big Sur.
# It just space-separates decimal fields, no fixed widths. Octal for mode, though.
rawWidths = "8 6 %s 2 3 2 1 4 10 10 10 10 4 0 5"
#rawFormat = re.sub(r"(\d+)", "%\\1d", rawWidths) + " %s"
rawFormat = re.sub(r"(\d+)", "%d", rawWidths) + " %s"
#print(rawFormat)

def getRawFormat(path:str, st:os.stat_result) -> str:
    #print(type(st))
    #for k in dir(st):
    #    if (k.startswith("__")): continue
    #    print("    %-16s -- %s" % (k, getattr(st, k)))
    
    modeStr = "%06o" % (st.st_mode)
    buf = rawFormat % (
        st[stat.ST_DEV], 
        st[stat.ST_INO],
        modeStr,
        st[stat.ST_NLINK],
        st[stat.ST_UID], 
        st[stat.ST_GID], 
        0,  # ?????
        st[stat.ST_SIZE],
        st[stat.ST_ATIME],    # Also st_atime_ns, etc?
        st[stat.ST_MTIME],
        st[stat.ST_CTIME],

        st.st_birthtime,      # FreeBSD and Mac -- No ST_ alias
        st.st_blksize,        # No ST_ alias
        st.st_blocks,         # No ST_ alias  # TODO Could be swapped w/ rdev?
        st.st_rdev,           # No ST_ alias
        
        #st.st_flag,          # No ST_ alias
        #st.st_gen,           # FreeBSD?
        #st.st_fstype,        # Solaris
        #st.st_rsize,         # Mac -- No ST_ alias
        #st.st_creator,       # Mac -- No ST_ alias
        #st.st_type,          # Mac -- No ST_ alias
        path
    )
    return buf

###############################################################################
# Main
#
if __name__ == "__main__":
    # Default formats
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
        # "flags", "-f", action='store_true',
        parser.add_argument(
            "--format", "-f", "--outputFormat", "--output-format", "--oformat", 
            type=str, default="plain",
            choices = [ "plain", "html", "xsv", "csv", "tsv" ],
            help='Record/field syntax for output.')
        parser.add_argument(
            "--human", "-H", action='store_true',
            help='Show file size in human-readable form (KMGTP suffixes).')
        # "ls-format", "-l", action='store_true',
        # "link-per-se", "-L", action='store_true',
        parser.add_argument(
            "--namedStatFormat", "--named-stat-format", type=str, default=None,
            choices=statFormats.keys(),
            help='Use one of the predefined stat formats, instead of specifying --statFormat.')
        parser.add_argument(
            "--no-newline", "-n", action='store_true',
            help='Do not force a newline to appear at the end of each piece of output.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--raw", "-r", action='store_true',
            help="Display raw information, as decimal int fields.")
        parser.add_argument(
            "--statFormat", "--stat-format", "-s", type=str, default=statFormat0,
            help='stat-like percent-codes to determine output format.')
        # "", "-s", action='store_true',
        parser.add_argument(
            "--timeFormat", "--time-format", "-t", type=str, default=timeFormat0,
            help='strftime-like percent-codes to determine time output format.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')
        parser.add_argument(
            "-x", action='store_true',
            help="Output a more readable, but old, Linux-y format.")
        
        parser.add_argument(
            'files', type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        if (args0.color is None):
            args0.color = ("CLI_COLOR" in os.environ and sys.stderr.isatty())
        #lg.setColors(args0.color)
        #if (args0.verbose): lg.setVerbose(args0.verbose)
        if (args0.namedStatFormat):
            args0.statFormat = statFormats[args0.namedStatFormat]

        return(args0)

    ###########################################################################
    #
    args = processOptions()
    ender = "" if (args.no_newline) else "\n"
    
    if (not args.quiet):
        warning0("Stat format spec is: '%s'" % (args.statFormat))
    ps = PowerStat(args.statFormat, args.timeFormat)

    if (len(args.files) == 0):
        warning0("stat.py: No files specified....")
        sys.exit()
    f0 = ""
    for f0 in args.files:
        try:
            st0 = os.stat(f0)
            md:int = st0.st_mode
            mdHigh = md & 0o7777
            mdLow = md | 0o7777
        except IOError as e0:
            sys.stderr.write("Error statting '%s':\n    %s" % (f0, e0))
            continue
            
        buf0 = ""
        if (args.x):
            buf0 = getLinuxFormat(f0, st0)
        elif (args.raw):
            buf0 = getRawFormat(f0, st0)
        else:
            buf0 = ps.format(f0)
        print(buf0, end=ender)
        if (mdHigh): print("    *** mode has high bit(s): %5x ***" % (md))
