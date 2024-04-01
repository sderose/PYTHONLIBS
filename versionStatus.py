#!/usr/bin/env python3
#
# versionStatus.py: Figure out what VCS a file belongs to, if any.
# 2022-09-29: Written by Steven J. DeRose.
#
import sys
import os
import re
from enum import Enum
from subprocess import check_output, CalledProcessError
import logging
lg = logging.getLogger()

__metadata__ = {
    "title"        : "versionStatus",
    "description"  : "Figure out what VCS a file belongs to, if any.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.9",
    "created"      : "2022-09-29",
    "modified"     : "2022-09-29",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Name=
    """ +__metadata__["title"] + ": " + __metadata__["description"] + """

=Description=

Given a file or directory, see if it's under version control, and what system,
and what state.

Returns or prints the particular VCS name, and if it supported, a
file status (values mostly based on git).
Quite a few VCSes can be identified, but
only git, Mercurial, and SVN have support beyond that yet.


==Usage as a command==

    versionStatus.py [options] [files]

For example:

    versionStatus.py --longStat --head *.cc

could display:
    git          CLEAN      myFile.cc
    git          UNMERGED   myOtherFile.cc
    git          UNTRACKED  temp.cc

See '--help-codes' for a list of VCS names and status codes.

==Usage from Python==

    from versionStatus import getVersionStatus
    systemName, status = getVersionStatus(path)

The systems known are listed in '' is a string called VCS_Type, and the status is an Enum called gitStatus
(even though the codes are all as for git).


=See also=

[https://en.wikipedia.org/wiki/List_of_version-control_software]

My 'backup', which has slight knowledge of git states.


=Known bugs and Limitations=

There are very many more versioning systems out there. I've only done a few.
If you'd like to add some, feel free, and please send me the patch.


=To do=

* A non-existent file is not considered to be in any version control
system, even if its directory is in scope for one.
* Add colors?


=History=

* 2022-09-29: Written by Steven J. DeRose.
* 2024-03-19: Add --help-codes, --head. Catch FileNotFoundError.
Identify a couple more VCS systems, clean up how it's done.

=Rights=

Copyright 2022-09-29 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
class gitStatus(Enum):
    # Most of the symbols are what you get from 'git status --porcelain'....
    # (exceptions: E, \\u2205, X, =.
    # git also uses a second column with sub-codes... And submodules are special.
    #
    ERROR       = "E"
    NO_FILE     = "\u2205"  # EMPTY SET symbol

    NOT_MINE    = "X"       # Not in this VCS (cf UNTRACKED)
    ### TODO: SVN "X" = "present b/c of externals"

    UNTRACKED   = "?"
    IGNORED     = "!"       # TODO: vs. SVN "I"
    CLEAN       = "="       # TODO: vs. SVN "C" = 'clean'; " " in git
    MODIFIED    = "M"
    ADDED       = "A"
    DELETED     = "D"       # TODO: vs. Mercurial "R" = removed
    RENAMED     = "R"       # TODO: SVN "R" = 'replaced'
    COPIED      = "C"       # TODO: SVN "C" = 'conflict'
    UNMERGED    = "U"

    #             "~"       # TODO: SVN "~" = 'changed type'

colorMap = {
    gitStatus.ERROR     : "red",
    gitStatus.NO_FILE   : "red",
    gitStatus.NOT_MINE  : "cyan",
    gitStatus.UNTRACKED : "yellow",
    gitStatus.IGNORED   : "yellow",
    gitStatus.CLEAN     : "green",
    gitStatus.MODIFIED  : "blue",
    gitStatus.ADDED     : "blue",
    gitStatus.DELETED   : "black",
    gitStatus.RENAMED   : "blue",
    gitStatus.COPIED    : "yellow",
    gitStatus.UNMERGED  : "magenta",
}

def getGitStatus(path:str) -> gitStatus:
    """See what sort of git state we're in (see `git status --help` for --porcelain).
    NOTE: It outputs "" for untracked and unchanged files. Some relevant options:
        -uall  -- show untracked
        --ignored=matching

    """
    # See if we're even in a git repo
    try:
        _gitDir = check_output("git rev-parse --show-toplevel 2>/dev/null", shell=True)
    except CalledProcessError:
        return gitStatus.NOT_MINE
    try:
        tokens = [ "git", "status", "--porcelain", "--ignored=matching", path ]
        buf = check_output(tokens)
    except CalledProcessError:
        if (args.verbose): lg.warning("CalledProcessError")
        return gitStatus.NOT_MINE
    if (len(buf) == 0):
        return gitStatus.CLEAN
    # If you don't give the encodoing, you get b'...', making buf0 be "b".
    bufs = str(buf, encoding='utf-8')
    buf0 = bufs[0]
    if (0 and args.verbose): lg.warning(
        "status response length %d, buf0 '%s': '%s'", len(buf), buf0, bufs)
    if (buf0 == " "):
        if (args.verbose): lg.warning("Found space")
        return gitStatus.CLEAN
    if (buf0 in "MADRCU?!"):
        if (args.verbose): lg.warning("Found code '%s'", buf0)
        return gitStatus(buf0)
    lg.warning("Unknown code '%s' from git status for '%s'.", buf0, path)
    return gitStatus.ERROR

def getMercurialStatus(path:str):
    """Really don't know how this behaves...
    See https://book.mercurial-scm.org/read/app-svn.html?highlight=status
    See https://lists.mercurial-scm.org/pipermail/mercurial/2014-March/046784.html
       M = modified
       A = added
       R = removed
       C = clean
       ! = missing (deleted by non-hg command, but still tracked)
       ? = not tracked
       I = ignored
         = origin of the previous file listed as A (added)

    """
    try:
        rc = check_output([ "hg", "status", path ])
    except (CalledProcessError, FileNotFoundError):
        return gitStatus.ERROR
    return rc[0]

def getSVNStatus(path:str):
    """Really don't know how this behaves...
    See https://svnbook.red-bean.com/en/1.8/svn.ref.svn.c.status.html
        ' ' = No modifications.
        'A' = Item is scheduled for addition.
        'D' = Item is scheduled for deletion.
        'M' = Item has been modified.
        'R' = Item has been replaced in your working copy. Was scheduled for deletion,
            and then a new file with the same name was scheduled for addition in its place.
        'C' = The contents conflict with updates received from the repository.
        'X' = Item is present because of an externals definition.
        'I' = Item is being ignored
        '?' = Item is not under version control.
        '!' = Item is missing (e.g., you moved or deleted it without using svn).
        '~' = Item is versioned as one kind of object (file, directory, link),
            but has been replaced by a different kind of object.
    """
    try:
        rc = check_output([ "svn", "status", path ])
    except CalledProcessError:
        return gitStatus.ERROR
    return rc[0]


###############################################################################
#
NO_VCS_NAME = "*UNKNOWN*"

VCSInfos = [
    # name          command  magic           callable
    ( "git",        "git",  ".git",          getGitStatus),
    ( "Mercurial",  "hg",   ".hg",           getMercurialStatus ),
    ( "SVN",        "svn",  ".svn",          getSVNStatus ),
    ( "CVN",        "cvs",  "CVS",           None ),
    ( "Bazaar",     "bzr",  ".bzr",          None ),
    ( "Darcs",      "",     "_darcs",        None ),
    ( "Fossil",     "",     ".fslckout",     None ),
    ( "Monotone",   "",     "_MTN",          None ),
    ( "Perforce",   "",     ".p4config",     None ),
    ( "Plastic",    "SCM",  ".plastic",      None ),
    ( "TFVC",       "TFVC", "$tf",           None ),
    ( "Vault",      "",     "_sgbak",        None ),
    ( "Veracity",   "",     "_veracitylogs", None ),
]


###############################################################################
#
def findOwningVCS(path:str) -> str:
    """Return the name of the owning VCS (if we can find one).
    TODO: Switch to returning whole tuple or index or something.
    """
    for tup in VCSInfos:
        sys.stderr.write("Trying: %s (key file '%s')\n" % (tup[0], tup[2]))
        if (anyParentHasThis(path, tup[2])): return tup[0]
    return NO_VCS_NAME

def anyParentHasThis(path:str, keyDirName:str) -> bool:
    """Scan upwards from a starting file or dir, seeing if it (if a dir) or
    any containing dir, contains a dir named by keyDirName.
    """
    fullPath = os.path.abspath(path)
    if (not os.path.isdir(fullPath)):
        curPath, _tail = os.path.split(fullPath)
        lg.info("    Real %s\n      to %s", fullPath, curPath)
    else:
        curPath = path
    while (curPath):
        tgt = os.path.join(curPath, keyDirName)
        lg.info("    Try: %s\n", tgt)
        if (os.path.isdir(tgt)): return True
        curPath = re.sub(r"/[^/]*$", "", curPath)
    return False

def doCmd(s:str, _path:str) -> str:
    try:
        buf = check_output(s, shell=True)
    except Exception as e:
        lg.error("Exception running: %s:\n    %s", s, e)
        return None
    return buf

def getVersionStatus(path:str, vcsName:str) -> gitStatus:
    """Read and deal with one individual file. Assuming it exists,
    poll various VCS to see who's active and/or owns it.
    """
    if (not os.path.exists(path)):
        return NO_VCS_NAME, gitStatus.NO_FILE
    if (vcsName == "git"):
        return getGitStatus(path)
    elif (vcsName == "Mercurial"):
        return getMercurialStatus(path)
    elif (vcsName == "SVN"):
        return getSVNStatus(path)
    return gitStatus.ERROR


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--color", action="store_true",
            help="Colorize paths to show status.")
        parser.add_argument(
            "--headings", action="store_true",
            help="Show column headings.")
        parser.add_argument(
            "--helpcodes", "--help-codes", action="store_true",
            help="Display the VCS names and status codes.")
        parser.add_argument(
            "--longstatus", "--long-status", action="store_true",
            help="Show words for file status, not just single characters.")
        parser.add_argument(
            "--noclean", "--no-clean", action="store_true",
            help="Do not list unchanged/clean files.")
        parser.add_argument(
            "--nosystem", action="store_true",
            help="Do not list the CVS system name.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--recursive", action="store_true",
            help="Descend into subdirectories.")
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
        if (lg and args0.verbose):
            logging.basicConfig(level=logging.INFO-args0.verbose,
                format='%(message)s')

        return(args0)


    ###########################################################################
    #
    args = processOptions()
    if (args.color):
        from ColorManager import ColorManager
        cm = ColorManager()
    else:
        cm = None

    if (args.helpcodes):
        print("Version control system codes (otherwise '%s'):" % (NO_VCS_NAME))
        for vi in VCSInfos:
            print("    %-12s" % (vi[0]))
        print("(mainly git) Status codes:")
        for name, mem in gitStatus.__members__.items():
            print("    %-12s %s" % (name, gitStatus[name].value))

    if (len(args.files) == 0):
        lg.warning("versionStatus.py: No files specified....")
        sys.exit()

    if (args.headings):
        if (args.nosystem):
            print("%-10s %s" % ("Status", "Path"))
        else:
            print("%-12s %-10s %s" % ("VCSystem", "Status", "Path"))

    for path0 in args.files:
        vcsName0 = findOwningVCS(path0)
        if (vcsName0 is not NO_VCS_NAME):
            _vcs, status = getVersionStatus(path0, vcsName0)
        else:
            status = gitStatus.NOT_MINE
        if (args.noclean and status==gitStatus.CLEAN): continue
        if (args.color):
            path0 = cm.colorize(path0, colorMap[status])
        printStat = status.name if args.longstatus else status.value
        if (args.nosystem):
            print("%-10s %s" % (printStat, path0))
        else:
            print("%-12s %-10s %s" % (vcsName0, printStat, path0))
