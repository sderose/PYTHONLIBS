#!/usr/bin/env python
#
# PowerWalk: More capable version os Python's os.walk.
#
from __future__ import print_function
import sys, os
from os.path import getatime, getctime, getmtime, getsize, splitext
import argparse
import re
from collections import namedtuple

# Libraries for particular file "formats":
import codecs
import io
import random
from enum import Enum

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    #import imp as importlib
    pass
else:
    #import importlib
    pass

from alogging import ALogger
lg = ALogger(1)

# We don't actually need the following modules unless requested
#
verbose = 2
def warn(lvl, msg):
    if (verbose>=lvl): sys.stderr.write("%s\n" % (msg))

# try:
#     import zip
# except ImportError:
#     warn(0, "Cannot import module 'zip'.")
try:
    import gzip
except ImportError:
    warn(0, "Cannot import module 'gzip'.")
try:
    import tarfile
except ImportError:
    warn(0, "Cannot import module 'tarfile'.")
try:
    import uu
except ImportError:
    warn(0, "Cannot import module 'uu'.")
try:
    import bz2
except ImportError:
    warn(0, "Cannot import module 'bz2'.")
try:
    import zlib
except ImportError:
    warn(0, "Cannot import module 'zlib'.")  # supports gzip
try:
    import zipfile
except ImportError:
    warn(0, "Cannot import module 'zipfile'.")


__metadata__ = {
    'title'        : "PowerWalk.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2018-04-21",
    'modified'     : "2020-09-01",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr="""
=Description=

`PowerWalk` is similar to Python's built-in `os.walk()`, but offers many
additional features, especially for file selection.

It has a simple iterator that returns a triple for each item,
containing a complete path, an open file handle for non-containers, and a flag
that say whether this is a container OPEN, an actual LEAF item, or
a container CLOSE. You can
set an option to get only the LEAF items, or to not open the files for you.

It can open several kinds of compressed and
container formats; include or exclude by extensions, name patterns, and
path patterns; exclude hidden or backup items; sort the items of a directory
in various order; and even random-sample only a % of eligible items.

==Usage as a command==

If run on its own, `PowerWalk` will display the paths of selected
files under the specified
directory(s), or the current directory if none are specified.

* Our chief options, for file '''selection''':
  ** --include and --exclude like grep
  ** whether to include backup files, hidden files, etc.
  ** specific filtering by extension
  ** whether to be recursive (like -r in many commands), and depth limits
  ** whether to follow hard, soft (and eventually Mac and Windows) links
  ** filtering by "file" characteristics (e.g., to get Python w/o .py)
  ** whether to return non-directories, only directories, or both

* Our two options, for '''selection''' and '''container''' files:
  ** automatic decoding of zip, gzip, uuencode, etc.
  ** automatic traversal into tar and similar files

* Our three options, for '''selection''', '''containers''', and '''reading''':
  ** what encoding to open the file with (`--encoding`)
  ** the file `--mode` (read or write, binary, etc) to apply.

* Amongst our options:
  ** sorting found files into various orders (--sort)
  ** whether to random-sample only some of the files
  ** whether to generate events for start and end of containers (--containers)
  ** whether to generate events for ignorable leafs (--ignorables).
  ** whether to generate events for nonexistent or unopenable file (--missing).

==Usage from code==

`PowerWalk` can be used as an iterator/generator:

    pw = PowerWalk(".", recursive=True)
    for path, fh, what in pw.traverse:
        for i, rec in enumerate(fh.readlines()):
            if (what == PWType.LEAF):
                print("%6d: %s" % (i, rec))

`what` will be a PWType Enum, one of:
    PWType.OPEN  -- Issued when a container (tar, directory, etc) opens.
    PWType.LEAF  -- Issued when a file-like item opens.
    PWType.IGNORE -- Issued IF requested, for items ignored.
    PWType.CLOSE  -- Issued when a container (tar, directory, etc) <s.
    PWType.MISSING -- Issued when a file cannot be found (or opened).

For example, this prints an
outline of the file directory subtree of the current directory. Special
items for opening and closing recursive directories, zip files, and tar files
are generated because of the 'containers' option:

    depth = 0
    pw = PowerWalk(".", recursive=True, containers=True)
    pw.setOption('includeExtensions', [ 'txt' ])
    for path, fh, what in pw.traverse():
        if (what == PWType.OPEN):
            print(" " * depth + ">>> Starting container %s" % (path))
            depth += 1
        elif (what == PWType.CLOSE):
            depth -= 1
            print(" " * depth + "<<< Ending %s" % (path))
        else:
            print(" " * depth + srcFile)
            doOneFile(srcFile)

If you don't want OPEN and CLOSE events for containers, turn off
the `containers` option.
If you'd instead like exceptions raised (for ItemOpening and ItemClosing,
then set the `exceptions` option (some might say that's more Pythonic).

Files and containers
that are filtered out do not get returned by default, but you can get
a PWType.IGNORE event (or an ItemIgnorable exception)
by setting the `ignorables` option.

''Note 1'': If you exercise options to traverse down into containers like
tar files, there may be no "path" per se for each individual item. In that case,
the returned path is that of the container.


=Methods=

(the main one is `traverse()`, which unfortunately comes last in the
alphabetical list below)

==addTraversalOptions(parser, prefix='', singletons=True)==

Add PowerWalk's options to a Python `argparse` instance.
If `singletons` is True, this will include single-character names such
as `-r` as a synonym for `--recursive`. If `prefix` is specified, it
will be prefixed to each name (after the hyphens, of course), to avoid
name conflicts.

==__init__(self, topLevelItems=None, options=None)==

Create a PowerWalk instance, which will traverse all the specified
items. If `topLevelItems` is None, the current directory is used;
if it is a list, all the named files and/or directories will be used;
otherwise, just the one named file or directory.

`options` is a dict of option name:value pairs. For example, to
traverse all the subdirectories of the specified items (if any),
pass `options` containing (at least) 'recursive':True.
Options can also be set later using `setOption` (see below).

==getOption(self, name)==

Return the value of an available option (see I<setOption>).


==isBackup(path) [static]==

Test whether the given file's name indicates it is a backup, spare copy,
duplicate, or similar file. This method knows
quite a few naming conventions, but surely not all (for example, OS conventions such as "backup of" presumably localize). For example, filenames that:

* start or ends with tilde or pound-sign

* have extension 'bak' or 'bcnk'

* match r'^(backup|copy) (\\(?\\d+\\)? )?of'

* match r'\\b(backup|copy|bak)\\b' (but in these cases a warning is
issued unless I<--quiet> is in effect).

* Mac OS X "Duplicate" does  `foo.txt` -> `foo copy.txt` -> `foo copy 2.txt`

* emacs backups append '~' or '~\\d+~' to the filename
For relevant emacs settings, see
L<https://stackoverflow.com/questions/151945/>).

* emacs auto-save files put '#' at start and end of filename (but
are usually deleted when you exit).


==isHidden(path) [static]==

Returns whether the file is hidden (for the moment, this just means
that the name starts with "."; Windows and Mac invisible files should
be added.

==isStreamable(obj)==

Returns true if the obj is of one of the known classes:


==showStats(self, writer=sys.stderr)==

Display a few statistics (stored in the PowerWalk instance as pw.stats).


=======

==setOption(self, name, value)==

Change the value of an available option, chosen from this list. These can also
be set on the constructor via like-named keyword options.
''Note'': There are a few more options that are not part of the PowerWalk
class, but are available when this script is run standalong. There are
described in the full list of options generated at the end of this help.


===File selection options===

* "backups": Include .bak and similar files? Default: False

* "hidden": Include hidden (.-initial) files? Default: False

* "excludeExtensions": List of file extension not to allow. Default: [].
See also I<includeExtensions>. Repeatable.

* "excludeNames": Regex of item basenames not to allow. Default: [].
See also I<includeNames>. Repeatable.

* "excludePaths": Regex of paths not to allow. Default: [].
See also I<includePaths>. Repeatable.

* "includeExtensions": List of (only) item extensions to allow. Default: [].
See also I<excludeExtensions>. Repeatable.

* "includeNames": Regex of (only) item basenames to allow. Default: [].
See also I<excludeNames>. Repeatable.

* "excludePaths": Regex of paths not to allow. Default: [].
See also I<includePaths>. Repeatable.


===Container and similar options===

* "openGzip": If True (the default), `gzip` files will be opened as if they were
directories, and the individual items within them will be returned.

* "openTar": If True (the default), `tar` files will be opened as containers
(optionally generating PWType.OPEN and PWType.CLOSE events),
and the individual items within them will be returned.

* "followLinks": If True (the default is False), *nix symbolic links will be followed, and
their targets opened or traversed as if they had been at the link's location.
This does not include Mac "aliases", Windows "shortcuts", weblocs, etc.


===Reading options===

* `close`: When the next item is requested, close the handle to the prior
one (only makes sense if `open` is also specified).

* `encoding`: Use this character encoding for input. Default: `utf-8`

* `mode`: What `mode` to pass to `codecs.open`. Default: `rb`.

* `open`: When a non-ignorable leaf is reached, open it and return the handle
as the second item in the returned tuple (which is otherwise None).
''Note'': For items that do not have a normal path, such as files embedded in
container such as tar or zip files, a handle to read them is always returned,
regardless of how the `open` option is set.


===Other options===

* `containers` (default True): If True,
then open and close events will be generated
for each container (such as a directory, gzip, or tar file) that is entered.
The third member of the returned tuple (`what`) is PWType.OPEN (1) and
PWType.CLOSE (4), respectively.

* `ignorables` (default False): If True, then events will be generated
even for items (containers and leaves) that are filtered out -- such as
hidden files or directories, etc. Such events will have `what`
returned as PWType.IGNORE (3).

* `exceptions` (default False): If True, then containers (and ignorable
files (if `ignorables` is also set) will be signaled by raising exceptions
rather than returning regular events. The exceptions will be of types
ItemOpening, ItemClosing, and ItemIgnorable.

* `maxDepth` (default 0 (unlimited)): Do not recurse deeper than this.

* `maxFiles` (default 0 (unlimited)): Stop after returning this many
files (events for ignorable
items do not count).

* `maxSize`

* `minDepth`

* `minSize`

* `recursive` (default False): Traverse through subdirectories?

* `sampleFactor` (default: 100.0): Include only this % of the available files.
If set to a value above 0.0 and below 100.0, each leaf item that would have
been returned, has only this % change of actually being returned.
Others are reclassified as ignorable.

* `sort`: Sort the items in each directory in the specified way.
Default: "" (just use whatever `os.listdir` returns).

** `name`:  sort by filename
** `iname`: sort by filename, ignoring case.
** `atime`: file access time
** `ctime`: file creation time
** `mtime`: file modification time
** `size`: File length in bytes
** `extension`: Extension as returned by `os.path.splitext`
* `notify`: Display a message as each new file starts. Default: False

==traverse(self, path, depth=0)==

Iterate, returning the chosen files (or pseudo-files, such as items
from a zip, tar, or siilar archive). Each iteration returns a tuple of
(path, fh), where `fh` is a readable. For regular files this is as returned
by `codecs.open()` with the `mode` and `encoding` specified as options.
For items within tar, gzip, or other supported archive types, it will be
the readable interface from the corresponding package.

Ignored items (such as backups if the option to include them has not
been set), are quietly skipped.

Containers such as directories and archive files, generate start and end
events, with the appropriate path, but instead of a file handle or similar,
a string is returned: DIR_START, DIR_END, GZIP_START, GZIP_END, TAR_START,
TAR_END. These events can be suppressed by setting the `containers` option
to False.


=Known bugs and limitations=

* I've used this almost exclusively for reading (for example, picking
out all the desired files from an NLP corpus like OANC or MASC). So writing
is not yet thoroughly tested. I imagine it doesn't work well for containers
(directories, tar, gzip, etc.).

* Script will fail if you don't have all the file-format libraries
installed, even if you don't need certain ones. Fixing.

* Statistics of the current run (a .stats), as well as the current
nesting depth of the traversal (in .depth),
are kept directly in the PowerWalk object instance. So if you try to
run two simultaneous traversal from the same PowerWalk instance, you may
have problems. Other than such statistics it should be ok. The traversal
stack itself is specific to each traversal.

* You can only specify one regex for each of the 4 include/exclude options
that take regexes.


=Related commands=

`find` + `exec`

My `lss`, `findIdenticalFiles`, `grep`, `find`.

My `lsoutline` produces a file listing similar to what `PowerWalk` produces
when run from the command line. But you can do fancier selection here.

=History=

* 2006-06-07: `countTags.py` written by Steven J. DeRose.
* 2018-04-21: `PowerWalk.py` split out of `countTags.py`.
* 2020-06-10: New layout. Static methods.
* 2020-08-28ff: Add exception-based directory/error event handling. Lint.
* 2020-09-01: Add `namedtuple` PWFrame as what to return. Add Enum
`PWType` for what kind of thing is being returned. Reorganize options
into categories in help and where listed in code. Add `--exceptions`
and several new filtering options, type-check them.
Refactor event generation, item stack, and statistics into TraversalState class.

=To do=

* Provide a better way to pass all the relevant options from argparse
in to the constructor.

* Make a way for the caller to find out what kind of container they're in.
Maybe just pass back the container handle? Or they can poke at the path,
of course.

* Make a way for the caller to get the depth. Could store it in the PWFrame,
but that doesn't scale nicely for other things. Maybe bit the bullet and make
a full-fledge iterator object?

* Make opening leafs optional!

* Additional filters  (cf 'find'):

** permissions, owner and group ids (and none), inode
** Add date and age options.
** regex for filename or dirname or path
** mindepth, name, path, iname, ipath, xattr
** text v. binary.
** Add support for identifying file type via *nix 'file', like
traversing all Python files regardless of extension (cf `findViaFile` shell
function in [https:github.com/sderose/BashSetup]).
** Current nesting depth, file count, whether
it's in a tar or gzip or container in general, etc.
** Mac fs metadata (kmdItem... and all that). See my `macFinderInfo`.
** Option to not cross filesystem bounds (say, via links or mount points).

* Compare "PRIMARIES" for `find` and adopt userful ones.
''Issue'': Getting argparse to do arguments with sub-arguments.
** atime, ctime, mtime mindepth
** depth
** newer/old cre/mod/acc time vs. specified file
** -type block special, char special, dir, regular, s-link, FIFI, socket.
** -size n
** -xattr
** negation

* Sort should provide a `reverse` option.

* A callback for filtering? Nah, user can just check and discard.

* Support Mac aliases, bookmarks, and webloc files.
See my `resolveLinks` attempt.
[https://pypi.org/project/mac_alias/].
See [https://stackoverflow.com/questions/48862093] (how-to-read-change-and-write-macos-file-alias-from-python),
[http://mac-alias.readthedocs.io/en/latest] and
[https://docs.python.org/2/library/macostools.html].

* Protect against circular links?

* Protect against caller changing working dir (unlike `os.walk`)

* Sampling of every nth file, first n from each directory, etc.

* Limit total size of files

* Support additional compression methods

* Support URLs (can *nix, Mac, or Wind aliases point to URLs?


=Rights=

Copyright 2006, 2018 by Steven J. DeRose.
This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[https://github.com/sderose].


=Options=
"""


###############################################################################
# Simple way to sample a certain fraction of the files....
#
class Sampling:
    def __init__(self, fraction=1.0):
        self.fraction = fraction
        self.requested = 0
        self.returned = 0

    def reset(self):
        self.requested = 0
        self.returned = 0

    def thisOne(self):
        self.requested += 1
        if (self.returned <= self.requested * self.fraction):
            self.returned += 1
            return True
        return False


###############################################################################
# A bunch of classes. There has to be an easier way to check read/writeability,
# short of try/catch.
# This list may need to be extended.
# See https://docs.python.org/3/library/io.html
#
def isStreamable(x):
    return isinstance(x, (
        io.TextIOWrapper,              # subclass of IOBase
        io.BufferedReader,             # subclass of IOBase
        io.BufferedWriter,             # subclass of IOBase
        codecs.StreamReaderWriter,     # KNOPE
        tarfile.TarFile,               # KNOPE
        gzip.GzipFile,                 # subclass of IOBase
        io.StringIO,                   # subclass of IOBase
        #
        # UUencode
        # bz2
        # zlib  # like gzip
        # zipfile
        #
        # DMG (.dmg, .mg, .smi
        # UDIF,
        # NDIF,
        # SPARSE,
        # IMG (raw disk image, need file system on top)
        # HTML with links, for scraping?
        )
    )


###############################################################################
# One form of traversal signals directory start/end by raising an
# exception, so you can just catch it that way. Seems to me cleaner than
# passes a "magic" event type back, or forcing the user to check.
#
# There is no exception corresponding to sucessfully return a readable/writable
# item, because that's the unexceptional case.
#
class ItemOpening(Exception):
    pass
class ItemClosing(Exception):
    pass
class ItemIgnorable(Exception):
    pass
class ItemMissing(Exception):
    pass
class ItemError(Exception):
    pass


###############################################################################
#
class PWType(Enum):
    OPEN   = 1          # The beginning of a directory, tar file, etc.
    LEAF   = 2          # An actual readable/writable object
    IGNORE = 3          # Notification of a filtered-out object
    CLOSE  = 4          # The end of a directory, tar file, etc.
    ERROR  = -1         # Missing, open error, etc.


###############################################################################
# PWFrame bundles the stuff you need to know in each entry on the 'travState'
# stack, which tracks the state of the traversal.
#
# .path is the absolute path to the file. file-like items within containers
#     like tar files do not have their own paths, so this may be None or
#     the container path plus an artificial suffix.
# .fh is any streamable such as a file handle. This is None unless:
#     a: the item is inside a container, so has no actual "path", or
#     b: the "open" option has been set.
#  .container is PWType, which tells whether this is a container opening or
#     closing, an ignored file event (if requested), an error, or a legit file.
#
PWFrame = namedtuple('PWFrame', [ 'path', 'fh', 'what' ])

def isPWFrameOK(ts:PWFrame):
    if (not isinstance(ts.path, str)):
        warn(0, "Bad PWFrame.path: %s." % (type(ts.path)))
        return False
    if (ts.fh is not None and not isStreamable(ts.fh)):
        warn(0, "Bad PWFrame.fh: %s." % (ts.fh or "[None]"))
        return False
    if (not isinstance(ts.what, PWType)):
        warn(0, "Bad PWFrame.what: %s." % (ts.what))
        return False
    return True


###############################################################################
#
class TraversalState(list):
    """Instantiate for each traversal.
    This object is passed down the recursive traversal.
    The main (list) content is a stack of PWFrame namedtuples.

    It has methods that do "the right thing" when we've called for an item
    confirmed as an OPEN, CLOSE, LEAF, IGNORE, or ERROR (based on the
    options in effect, a reference to which is passed to the constructor).
    """
    def __init__(self, options):
        self.depth = 0
        self.iString = '    '
        self.options = options

        self.stats = {
            "nodesTried"              : 0,  # +
            "containersOpened"        : 0,  # +
            "leafs"                   : 0,  # +
            "ignored"                 : 0,
            "erroneous"               : 0,  # +

            "regular"                 : 0,
            "directory"               : 0,
            "tar"                     : 0,
            "gzip"                    : 0,

            "ignoredSamples"          : 0,
            "ignoredBackups"          : 0,
            "ignoredHiddens"          : 0,
            "ignoredByExclExtensions" : 0,
            "ignoredByInclExtensions" : 0,
            "ignoredByExclNames"      : 0,
            "ignoredByInclNames"      : 0,
            "ignoredByExclPaths"      : 0,
            "ignoredByInclPaths"      : 0,

            "maxDepth"                : 0,

        }
        super(TraversalState, self).__init__()

    def showStats(self, writer=sys.stderr):
        writer.write("\nItems processed:\n")
        for k in sorted(self.stats.keys()):
            writer.write("    %-30s %8d\n" % (k, self.stats[k]))

    def bump(self, name, n=1):
        assert(name in self.stats)
        self.stats[name] += n

    def indent(self):
        return self.iString * self.depth

    ###########################################################################
    # Stack managers for the main event types.
    #
    _ = """Event/Exception/Stack managers.
        * If caller doesn't want the event, return None
        * If called wants it as an exceptions, raise one then return None
        * Otherwise stack it, return the PWFrame, then pop it.
        ==> Iff we return a PWFrame, the caller should yield it.
    """
    def openContainer(self, path:str, fh:object):
        """Create and push a stack frame for the thing we found.
        Files that are filtered out don't even get here. But for containers,
        we mightgenerate events or excpetions (see options['containers')
        """
        if (not isinstance(path, str)):  # TODO: Fix so we don't need this
            warn(0, "open() was passed a %s for path." % (type(path)))
            path = path.path
        thePWFrame = PWFrame(path, fh, PWType.OPEN)
        assert isPWFrameOK(thePWFrame)

        self.bump("containersOpened")
        self.append(thePWFrame)

        if (not self.options['containers']):
            return None
        elif (self.options['exceptions']):
            raise ItemOpening
        self.depth += 1  # not thread-safe
        if (self.depth > self.options['maxdepth']):
            self.options['maxdepth'] = self.depth
        return thePWFrame

    def handleLeaf(self, path:str, fh:object):
        """Create and push a stack frame for the thing we found.
        Files that are filtered out don't even get here. But for containers,
        we mightgenerate events or excpetions (see options['containers')
        """
        warn(1, "handleLeaf: %s" % (path))
        if (not isinstance(path, str)):  # TODO: Fix so we don't need this
            #warn(0, "open() was passed a %s for path." % (type(path)))
            path = path.path
        thePWFrame = PWFrame(path, fh, PWType.LEAF)
        assert isPWFrameOK(thePWFrame)
        self.bump("leafs")
        return thePWFrame

    def handleIgnorable(self, path:str):
        """Called for an ignorable item:
            * If caller doesn't want them, return None
            * If called wants them as exceptions, raise one then return None
            * Otherwise stack it, return the PWFrame, then pop it.
        Caller should do this for leaves:
            tsf = self.handleIgnorable(travState, path)
            if (tsf): yield tsf
        """
        warn(1, "handleIgnorable: %s" % (path))
        self.bump("ignored")
        if (not self.options['ignorables']):
            return None
        elif (self.options['exceptions']):
            raise ItemIgnorable
        else:
            return PWFrame(path, None, PWType.IGNORE)

    def handleError(self, path:str, message:str="Item Error"):
        """Called for missing, unopenable, etc.
        """
        warn(1, "handleError: %s" % (path))
        self.bump("erroneous")
        if (not self.options['errors']):
            return None
        elif (self.options['exceptions']):
            raise ItemError(message + " [%s]" % (path))
        else:
            return PWFrame(path, None, PWType.ERROR)

    def closeContainer(self):
        """Called at the end of any node, whether container or leaf.
        For leafs, don't yield a separate event, just pop the stack.
        """
        thePWFrame = self[-1]
        self.depth -= 1  # not thread-safe
        warn(1, "closeContainer: %s" % (thePWFrame.path))
        self.pop()
        if (thePWFrame.what == PWType.OPEN):
            if (not self.options['containers']):
                return None
            elif (self.options['exceptions']):
                raise ItemClosing
            return PWFrame(thePWFrame.path, thePWFrame.fh or None, PWType.CLOSE)
        raise IOError("Trying to close a %s" % (thePWFrame))



###############################################################################
#
class PowerWalk:
    """A class to traverse files in the file system, combining a lot of
    filtering and decoding features, drawing on many *nix commands for
    inspiration. See the features description under -h.
    """

    __optionTypes = {
        # What to include
        "backups"             : bool,
        "hidden"              : bool,
        "followLinks"         : bool,

        "excludeExtensions"   : list,
        "excludeNames"        : list,
        "excludePaths"        : list,
        "includeExtensions"   : list,
        "includeNames"        : list,
        "includePaths"        : list,

        "maxDepth"            : int,
        "maxFiles"            : int,
        "maxSize"             : int,
        "minDepth"            : int,
        "minSize"             : int,

        "openTar"             : bool,
        "openGzip"            : bool,
        "recursive"           : bool,
        "sampleFactor"        : float,

        # How to open
        "encoding"            : str,
        "mode"                : str,
        "sort"                : str,

        # Events handling and generation
        "close"               : bool,
        "containers"          : bool,
        "exceptions"          : bool,
        "ignorables"          : bool,
        "notify"              : bool,
        "open"                : bool,
    }

    def __init__(self, topLevelItems=None, **kwargs):
        if (not topLevelItems):
            self.topLevelItems = [ os.environ['PWD'] ]
        elif (isinstance(topLevelItems, list)):
            self.topLevelItems = topLevelItems
        else:
            self.topLevelItems = [ topLevelItems ]

        self.travState = None  # Used during traversal (not thread-safe!) TO DO

        self.options = {
            # What to include
            "backups"             : False,
            "hidden"              : False,
            "followLinks"         : False,

            "excludeExtensions"   : [],
            "excludeNames"        : [],
            "excludePaths"        : [],
            "includeExtensions"   : [],
            "includeNames"        : [],
            "includePaths"        : [],

            "maxDepth"            : 0,
            "maxFiles"            : 0,
            "maxSize"             : 0,
            "minDepth"            : 0,
            "minSize"             : 0,

            "openTar"             : False,
            "openGzip"            : False,
            "recursive"           : False,
            "sampleFactor"        : 100.0,    # Take everything.

            # How to open
            "encoding"           : "utf-8",   # Character encoding
            "mode"                : "rb",     # Read, write, bin, etc.
            "sort"                : "",       # TODO: Test in tar, zip, etc.

            # Events handling and generation
            "close"               : False,    # Do fh.close() on leafs for user.
            "containers"          : True,     # Events for container start/end?
            "exceptions"          : False,    # Exception for containers, errs.
            "ignorables"          : False,    # Events even for ignored stuff?
            "notify"              : False,    # Tell caller on start/end dir
            "open"                : True,     # Do leaf open()s for user.
        }

        if (kwargs):
            for k, v in kwargs.items():
                self.setOption(k, v)

    def setOption(self, name, value):
        """Note: If the options are coming in from argparse, an inset
        list will perhaps be None, so fix to an empty list.
        """
        #if (name not in self.options):
        #    raise ValueError("Unknown option '%s'." % (name))
        if (name in self.__optionTypes):
            theType = self.__optionTypes[name]
            if (value is None):
                if (theType == list): value = []
                else: value = 0
            try:
                self.options[name] = theType(value)
            except TypeError as e:
                warn(0, "Error setting option '%s':\n    %s" % (name, e))

    def getOption(self, name):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        return self.options[name]

    @staticmethod
    def addTraversalOptions(parser, prefix='', singletons=True):
        """Provide an easy way to add all our options to a main program.
        """
        prefix = "--" + prefix

        parser.add_argument(
            prefix + "excludeExtensions",
            type=str, metavar='X', action='append',
            help='Exclude items with these extensions (repeatable).')
        parser.add_argument(
            prefix + "excludeNames",
            type=str, metavar='R', action='append',
            help='Exclude base names matching this regex (repeatable).')
        parser.add_argument(
            prefix + "excludePaths",
            type=str, metavar='R', action='append',
            help='Exclude path matching this regex (repeatable).')

        parser.add_argument(
            prefix + "includeExtensions",
            type=str, metavar='X', action='append',
            help='Include (only) items with these extensions (repeatable).')
        parser.add_argument(
            prefix + "includeNames",
            type=str, metavar='R', action='append',
            help='Include (only) base names matching this regex (repeatable).')
        parser.add_argument(
            prefix + "includePaths",
            type=str, metavar='R', action='append',
            help='Include (only) path matching this regex (repeatable).')

        parser.add_argument(
            prefix + "backups",           action='store_true',
            help='Include (seeming) backup items,like .bak, ~x, #x#,....')
        parser.add_argument(
            prefix + "close",             action='store_true',
            help='Close leaf items when done (requires --open).')
        parser.add_argument(
            prefix + "containers",        action='store_true',
            help='Generate events (or --exceptions) for container open/close.')
        parser.add_argument(
            prefix + "encoding", type=str, metavar='E', default="utf-8",
            help='Assume this character set. Default: utf-8.')
        parser.add_argument(
            prefix + "exceptions",        action='store_true',
            help='Report container oper/close as exceptions, not events.')
        parser.add_argument(
            prefix + "followLinks",       action='store_true',
            help='Follow *nix links to the destination.')
        parser.add_argument(
            prefix + "hidden",            action='store_true',
            help='Include items whose names begin with dot.')
        parser.add_argument(
            prefix + "ignorables",        action='store_true',
            help='Return events (or exceptions) for ignorable items.')
        parser.add_argument(
            prefix + "notify",            action='store_true',
            help='Some extra notifications')  # TODO
        parser.add_argument(
            prefix + "open",              action='store_true',
            help='Open leaf items and return a readable handle.')

        parser.add_argument(
            prefix + "openTar",           action='store_true',
            help='Open tar files as if they were directories.')
        parser.add_argument(
            prefix + "openGzip",           action='store_true',
            help='Open openGzip files as if they were directories.')

        parser.add_argument(
            prefix + "maxDepth", metavar='N', type=int, default=0,
            help='Do not traverse more than this many levels down.')
        parser.add_argument(
            prefix + "maxFiles", metavar='N', type=int, default=0,
            help='Do not return more than this many leaf items.')
        parser.add_argument(
            prefix + "maxSize", metavar='N', type=int, default=0,
            help='Skip files larger than this.')

        parser.add_argument(
            prefix + "minDepth", metavar='N', type=int, default=0,
            help='Do not return items fewer than this many levels down.')
        parser.add_argument(
            prefix + "minSize", metavar='N', type=int, default=0,
            help='Skip files smaller than this.')

        parser.add_argument(
            prefix + "mode",              type=str, default="rb",
            choices = [ "r", "rb", "w", "wb", "a", "ab" ],
            help='Mode (read vs. write and binary). Default: rb.')

        if (singletons):
            parser.add_argument(
                prefix+"recursive", "-r", action='store_true',
                help='Descend into subdirectories.')
        else:
            parser.add_argument(
                prefix + "recursive",     action='store_true',
                help='Descend into subdirectories.')
        ### argparse bug 3.6? Can't have "% " in help string?!!
        parser.add_argument(
            prefix + "sampleFactor", metavar='%', type=float, default=100.0,
            help='Sample only this percentage of eligible items.')
        parser.add_argument(
            prefix + "sort",              type=str, default='none',
            choices = [ 'none',
                'alpha', 'ALPHA', 'size', 'adate', 'mdate', 'cdate' ],
            help='Sort directory members by what? Default: none. ' +
                "Not yet supported.")
        return parser

    def traverse(self):
        """Use ttraverse on each top-level file or dir, to
        recurse through the files/directories requested and return
        a PWFrame (a namedtuple of path, file handle, and PWType) for each.

        We have to return the file handle in the case of "files"
        buried in containers such as tar files, because they don't
        have an actual path.

        TODO: This should really make a separate iterator object, to be
        thread-safe for accessing things like depth.
        """

        # Reference the traversal state in the main object, so the caller
        # can get at stats, depth, etc. But this isn't thread-safe, and
        # we don't refer to it via the PowerWalk object.
        #
        trav = self.travState = TraversalState(self.options)

        for tl in (self.topLevelItems):
            warn(1, "\n******* Starting top-level item '%s'." % (tl))
            for tsf in self.ttraverse(tl, trav):
                trav.bump("nodesTried")
                warn(1, "tried %d, max %d." %
                    (trav.stats["nodesTried"], self.options["maxFiles"]))
                if (self.options["maxFiles"] and
                    trav.stats["nodesTried"] > self.options["maxFiles"]): break
                yield tsf
        return

    def ttraverse(self, path:str, trav:TraversalState):
        """Recurse as needed.
        """
        warn(1, "%sttraverse at '%s'" % ("  "*len(trav), path))

        if (self.options['maxDepth'] > 0 and               # MAXDEPTH REACHED
            len(trav) > self.options['maxDepth']):
            warn(0, "maxDepth exceeded.")
            return

        elif (not self.passesFilters(path, trav)):         # IGNORABLE FILE
            tsf = trav.handleIgnorable(path)
            if (tsf): yield tsf

        elif (not os.path.exists(path)):                   # NOT FOUND
            tsf = trav.handleError(path, "Item not found")
            if (tsf): yield tsf

        elif (os.path.isdir(path)):                        # DIRECTORY
            self.trySomething(trav, 'directory')
            if (not self.options['recursive']):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                tsf = trav.openContainer(path, None)
                if (tsf): yield tsf
                children = os.listdir(path)
                if (self.options['sort']):
                    children = self.chSort(path, children)
                for ch in children:
                    chPath = os.path.join(path, ch)
                    for chFrame in self.ttraverse(chPath, trav):
                        yield chFrame
                tsf = trav.closeContainer()
                if (tsf): yield tsf

        elif (False and tarfile.is_tarfile(path)):         # TAR FILE
            self.trySomething(trav, "tar file")
            if (not self.options['openTar']):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                tfObject = tarfile.open(path, "r:*")
                tsf = trav.openContainer(path, None)
                if (tsf): yield tsf
                for tfMember in (tfObject.getmembers):
                    if (tfMember.isfile()):
                        fh2 = tfObject.extractfile(tfMember)
                        yield trav.handleLeaf(path, fh2)
                        if (self.options['close'] and fh2):
                            fh2.close()
                    elif (tfMember.isdir()):
                        self.trySomething(trav, "tar subdir")
                        # TODO: add tar internal recursion!
                    else:  # also issyn, islnk, ischr, isblk, isfifo, isdev
                        warn(0, "Non-file, non-dir) in tar file.")
                tfObject.closeContainer()
                tsf = trav.closeContainer()
                if (tsf): yield tsf

        elif (path.endswith(".gz")):                       # GZIP FILE
            self.trySomething(trav, 'gzip')
            if (not self.options['openGzip']):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                #warn(1, "gzip file '%s'." % (path), stat='gzip file')
                fh2 = gzip.open(path, mode=self.options['mode'],
                    encoding=self.options['encoding'])
                tsf = trav.openContainer(path, None)
                if (tsf): yield tsf
                yield trav.handleLeaf(path, fh2)
                if (self.options['close']): fh2.close()
                tsf = trav.closeContainer()
                if (tsf): yield tsf

        elif (os.path.islink(path)):                       # LINK
            if (not self.options['followLinks']):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            tgt = os.readlink(path)
            for tsf in (self.ttraverse(tgt, trav)):
                yield tsf

        elif (self.options['sampleFactor'] < 100 and       # NON-SAMPLE
            random.random()*100.0 > self.options['sampleFactor']):
            tsf = trav.handleIgnorable(path)
            trav.bump('ignoredSamples')
            if (tsf): yield tsf

        else:                                              # SELECTED FILE
            fh = codecs.open(path, mode=self.options['mode'],
                encoding=self.options['encoding'])
            # Py 2: codecs.open returns old-style class StreamReaderWriter
            if (PY2 and '__class__' in fh and
                fh.__class__.__name__ != 'StreamReaderWriter'):
                raise ValueError("Got type '%s' (%s) for %s." %
                    (type(fh), fh.__class__.__name__, path))
            yield trav.handleLeaf(path, fh)

        return

    def passesFilters(self, path, trav):
        """Check the file at 'path' against all the filters, and
        return True iff it's one the user wants. The same name, date, and
        other filters apply to containers (such as directories) and
        to leafs (such as files)
        """
        base = os.path.basename(path)
        # TODO: Directories with dot in name!
        if (os.path.isdir(base)):
            (_, ext) = base, ""
        else:
            (_, ext) = os.path.splitext(base)
            ext = ext.strip(". \t\n\r")

        if (not self.options['hidden'] and isHidden(base)):
            self.trySomething(trav, "hidden", "exclude")

        elif (self.options['excludeExtensions'] and
            ext in self.options['excludeExtensions']):
            self.trySomething(trav, 'ignoredByExclExtensions', "exclude")
        elif (self.options['includeExtensions'] and
            ext not in self.options['includeExtensions']):
            self.trySomething(trav, 'ignoredByInclExtensions', "exclude")

        elif (self.options['excludeNames'] and
            re.search(self.options['excludeNames'][0], base)):
            self.trySomething(trav, 'ignoredByExclNames', "exclude")
        elif (self.options['includeNames'] and
            not re.search(self.options['includeNames'][0], base)):
            self.trySomething(trav, 'ignoredByInclNames', "exclude")

        elif (self.options['excludePaths'] and
            re.search(self.options['excludePaths'][0], path)):
            self.trySomething(trav, 'ignoredByExclPaths', "exclude")
        elif (self.options['includePaths'] and
            not re.search(self.options['includePaths'][0], path)):
            self.trySomething(trav, 'ignoredByInclPaths', "exclude")

        elif (not self.options['backups'] and isBackup(path)):
            self.trySomething(trav, "backup", "exclude")
        else:
            self.trySomething(trav, 'regular')
            return True

        return False

    def chSort(self, curPath, chList):
        """Sort a file-list returned from os.listdir somehow.
        """
        if (self.options['sort'] == 'name'):
            chList.sort()
        elif (self.options['sort'] == 'iname'):
            chList.sort(key=lambda x: x.lowercase())
        elif (self.options['sort'] == 'atime'):
            chList.sort(key=lambda x: getatime(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'ctime'):
            chList.sort(key=lambda x: getctime(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'mtime'):
            chList.sort(key=lambda x: getmtime(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'size'):
            chList.sort(key=lambda x: getsize(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'extension'):
            chList.sort(key=lambda x: splitext(os.path.join(curPath, x))[1])
        return chList

    def trySomething(self, theStack:list, thing:str, statusMsg:str="included"):
        """Count the kind of thing, and maybe say something.
        """
        if (len(theStack) == 0):
            warn(1, "%s  Trying: empty stack (%s, %s)" %
            ("  "*len(theStack), thing, statusMsg))
            return
        if (self.options['notify']):
            frame = theStack[-1]
            warn(1, "Trying %s: '%s' (cont=%s) [%s]" %
                (thing, frame.path, frame.what, statusMsg))
        return


###############################################################################
# Generic filename tests.
#
# See also diffDirs.py, findDuplicateFiles, lss
#
def isBackup(name):
    b = os.path.basename(name)
    root, ext = os.path.splitext(b)
    keywords = r'(backup|copy)'
    if (not b): return False
    if (b[0] in "~#" or b[-1] in "~#"): return True
    if (ext == "bak"): return True
    if (re.search(keywords + r'\b( \d+)?( of)\b', root, re.IGNORECASE)):
        return True
    if (re.search(r'\b(backup|copy|bak)\b', root, re.IGNORECASE)):
        return True
    return False

def isHidden(name):
    b = os.path.basename(name)
    if (b.startswith(".")): return True
    return False

def isGenerated(name):
    """Is the name one that you probably don't need to archive, diff, or
    do certain other things with, since it's derived.
    """
    b = os.path.basename(name)
    gExprs = [
        r'^\.DS_Store',
        r'\.pyc$',
        r'\.so$',
    ]
    for ge in gExprs:
        if (re.search(ge, b)): return(True)
    return(False)


###############################################################################
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
            "--iString", metavar='S', type=str, default='    ',
            help='Repeat this string to create indentation.')
        parser.add_argument(
            "--quiet", "-q",       action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--quote",             action='store_true',
            help='Put quotes around the reported paths.')
        parser.add_argument(
            "--short",             action='store_true',
            help='Only show the bottom-level name in the outline view.')
        parser.add_argument(
            "--verbose", "-v",     action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version",           action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',               type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to files, directories, containers to traverse.')

        PowerWalk.addTraversalOptions(parser)

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    # Main
    #
    args = processOptions()
    verbose = args.verbose

    argDict = {}
    for k0 in vars(args).keys():
        argDict[k0] = vars(args)[k0]

    if (args.verbose):
        print("Args:\n%s")
        for k0 in sorted(argDict.keys()):
            print("    %-20s %s" % (k0, argDict[k0]))

    cwd = os.environ['PWD']
    if (not args.files): args.files = [ os.environ['PWD'] ]

    pw = PowerWalk(**argDict)

#     pw = PowerWalk(args.files,
#         recursive=args.recursive,
#         notify=args.verbose)

    depth = 0
    for path0, fh0, what0 in pw.traverse():
        path0 = path0.replace(cwd, '.')
        if (args.short and depth > 1):
            path0 = os.path.basename(path0)
        if (args.quote):
            path0 = '"' + re.sub(r'"', "\\\"", path0) + '"'

        if (what0 == PWType.OPEN):
            print("%s>>%s" % (args.iString*depth, path0))
            depth += 1
        elif (what0 == PWType.LEAF):
            print("%s%s" % (args.iString*depth, path0))
        elif (what0 == PWType.CLOSE):
            depth -= 1
            print("%s<<%s" % (args.iString*depth, path0))
        elif (what0 == PWType.IGNORE):
            print("%sIGNORING: %s" % (args.iString*depth, path0))
        elif (what0 == PWType.ERROR):
            print("%sERROR: %s" % (args.iString*depth, path0))

    if (not args.quiet): pw.travState.showStats()