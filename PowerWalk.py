#!/usr/bin/env python3
#
# PowerWalk: More capable version os Python's os.walk.
#
from __future__ import print_function
import sys, os
from os.path import getatime, getctime, getmtime, getsize, splitext, stat
import argparse
import re
from collections import namedtuple, defaultdict
import random
#import math
from enum import Enum
from shutil import copyfile
from subprocess import check_output, CalledProcessError

from alogging import ALogger
lg = ALogger(0)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    #import imp as importlib
    pass
else:
    #import importlib
    pass

verbose = 0  # Also set by PowerWalk.setOptions('verbose')
def warn(lvl, msg):
    if (verbose>=lvl): sys.stderr.write("%s\n" % (msg))


###############################################################################
# Libraries for particular file "formats":
import codecs
import io

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
# try:
#     import uu
# except ImportError:
#     warn(0, "Cannot import module 'uu'.")
# try:
#     import bz2
# except ImportError:
#     warn(0, "Cannot import module 'bz2'.")
# try:
#     import zlib
# except ImportError:
#     warn(0, "Cannot import module 'zlib'.")  # supports gzip
# try:
#     import zipfile
# except ImportError:
#     warn(0, "Cannot import module 'zipfile'.")


__metadata__ = {
    'title'        : "PowerWalk.py",
    'description'  : "Similar to Python os.walk, but with many of the selection features of *nix 'find', and a more flexible interface.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2018-04-21",
    'modified'     : "2020-11-24",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr="""
=Description=

`PowerWalk` is similar to Python's built-in `os.walk()`, but offers many
additional features, especially for file selection (in that respect it is
more similar to the *nix `find` command).

It has a simple iterator that returns a triple for each item,
containing a complete path, an (optional) open file handle
for non-containers, and a flag
that says whether this is a container OPEN (such as starting a new
directory or tar file), an actual LEAF item, or a container CLOSE. You can
set options to get only the LEAF items, or to open the files for you,
or to raise exceptions for OPEN and CLOSE instead of returning them as
regular events.

`PowerWalk` can open several kinds of compressed and
container formats;
include or exclude by extensions, name patterns, and path patterns;
exclude hidden or backup items;
sort the items of a directory in various orders;
and even random-sample only a % of eligible items.

The package also supplies a few useful idependent tests:

* isBackup(path)
* isHidden(path)
* isGenerated(path)


==Usage as a command==

If run on its own, `PowerWalk` will display the paths of selected
files under the specified
directory(s), or the current directory if none are specified. Several
special options apply in that case:

* `--oformat` [x] -- formats the list as plain, json, html, or s-expressions.
Setting this to other than 'plain' (the default), overrides the specific
delimiter options described below.

* `--openQuote 'x'` and `--closeQuote 'x'` -- set delimiters to be put
before and after each name (typically both would be set to '"' or "'").

* `--anonymousClose` -- if set, do not print the name of directories or
other containers as they close.

* `--openDelim` and `--closeDelim` -- Display these around
the contents of directories and other containers (after their name').

* `--copyTo [path]` -- Copy the chosen files to this directory (see also
`--serialize`).

* `--exec` '[...{}...]\\;' -- Run a given command on each selected item,
much like `find --exec`.

* `--iString [s]` -- Repeat this string to create indentation.

* `--itemSep` -- Put this in to separate items (e.g., a comma).

* `--serialize` -- put a serial number on each file with `--copyTo`.

===General options available in command or API use===

* Our chief options, for file '''selection''':
    Note: "include" and "exclude" in option names can be abbreviated to
just "i" and "e", and a hyphen may be used instead of camel-case for
these options.

  ** `--includeNames` and `--excludeNames` are
like grep `-include` and `-exclude`, but take full regexes to match against.
''Note'': matches may occur anywhere within the name (including the extension).
To require a match to the complete name, start the regex with "^" and end it
with "$".
  ** `-include-dirs` and `-exclude-dirs`are
like grep (and also available as `--includeDirs` and `--excludeDirs`),
but take full regexes to match against.
  ** `--includeExtensions` and `--excludeExtensions` match file extensions (without the ".") against full regexes. In particular, the "|" operator
  is supported for "or". For example: `--ie '(py|pl|pm|cc)' works.
  ** `--includeInfos` and `--excludeInfos` match
  characteristics reported by the *nix `file` command.
For example, this makes it easy to get Python files whether they have a `.py`
extension of not.
  ** `--backups` includes backup files, hidden files, etc.
  ** `--recursive` or `-r` (which you'll often want) makes `PowerWalk` descend
  into sub-directories (but not tar or other container files -- for which
  there are separate options). If directories are specified directly, rathern
  than just being reached, the wil be recursed into in any case. Not sure
  if this is best or not.
  See 'Known bugs and limitations' for more information.
  ** `--minDepth` and `maxDepth` constrain what
  directory or container depth limits to return files from.
  **`--followLinks` make PowerWalk follow *nix links.

* Our two options, for '''selection''' and '''container''' files:
  ** `--containers` can be set in order to return events not just for
  files, but also for the OPEN and CLOSE of directories (as well as tar
  or other container files if those are to be opened).
  ** options allow automatic opening of zip, gzip, uuencode, and other
  container files (not all the envisioned ones are supported yet, however).
  One that can have internal filesystems (tar, dmg, etc) can be treated
  as if they were just directories.

* Our three options, for '''selection''', '''containers''', and '''reading''':
  ** `--open` will cause files to be opened automatically, and the handle
  passed back, while `--close` automatically closes them when you request
  the next event.
  ** what encoding to open the file with (`--encoding`, default utf-8)
  ** the file `--mode` (read or write, binary, etc) to apply.

* Amongst our options:
  ** `--sort` enables sorting found files into various orders
(see under "Other Options" below for details).
  ** `--sampleFactor` lets you random-sample only some of the files
  ** `--ignorables` adds events for ignorable leafs (with a special type field)
  ** `--missing` adds events for nonexistent or unopenable files
  ** `--errorEvents` adds events for errors such as unreadable files, etc.

==Usage from code==

`PowerWalk` can be used as an iterator/generator. To just get a lot of
files, each passed back with its full path and an open file handle, do this:

    from PowerWalk import PowerWalk, PWType
    pw = PowerWalk("myDir1", recursive=True, open=True, close=True)
    maxDepth = 0
    for path, fh, what in pw.traverse():
        if (what != PWType.LEAF): continue
        nrecs = len(fh.readlines)
        print("%6d lines in %s" % (nrecs, path))

`what` will be a `PWType` Enum, one of:
    PWType.OPEN  -- Issued when a container (tar, directory, etc.) opens.
    PWType.LEAF  -- Issued when a file-like item is returned.
    PWType.IGNORE -- Issued (only if requested), for items ignored.
    PWType.CLOSE  -- Issued when a container (tar, directory, etc.) closes.
    PWType.MISSING -- Issued when a file cannot be found (or opened).

You can pass a list of paths as the first argument if desired.
Or you can pass one or a list of paths to `pw.traverse()`, which will use
them instead of the one(s) set on the constructor (if any).

You can ignore the OPEN and CLOSE events (as shown here), or turn off the
`containers` option to have them not be generated at all.
You can also turn auto-opening and/or closing of files on or off.

The following example prints an
outline of the file directory subtree of the current directory:

    depth = 0
    pw = PowerWalk(args.files, recursive=True, containers=True)
    pw.setOption('includeExtensions', 'txt')
    for path, fh, what in pw.traverse():
        if (what == PWType.OPEN):
            print("  " * depth + ">>> Starting container %s" % (path))
            depth += 1
        elif (what == PWType.CLOSE):
            depth -= 1
            print("  " * depth + "<<< Ending %s" % (path))
        else:
            print("  " * depth + srcFile)
            doOneFile(srcFile)

If you'd rather think of directory boundaries as exceptional
(some might say that's more Pythonic), you can  do this:

    pw = PowerWalk("myDir", recursive=True, exceptions=True)
    while True:
        try:
            path, fh, what = pw.traverse():
            nrecs = len(fh.readlines)
            print("%6d lines in %s" % (nrecs, path))
        except ItemOpening:
            print("\n\n*** Starting directory")
        except ItemClosing:
            print("\n\n*** Ending directory")
        except Finished:
            break

Files and containers
that are filtered out do not get returned by default, but you can get
a PWType.IGNORE event (or an ItemIgnorable exception)
by setting the `ignorables` option.

''Note'': If you exercise options to traverse down into containers like
tar files, there may be no "path" per se for each individual item. In that case,
the returned path is that of the container, and you'll be given an open
file handle (whether or not you requested them for regular files).


=Methods=

(the main one is `traverse()`, which unfortunately comes last in the
alphabetical list below)

==addOptionsToArgparse(parser, prefix='', singletons=True)==

Add PowerWalk's options to a Python `argparse` instance.
If `singletons` is True, this will include single-character names such
as `-r` as a synonym for `--recursive`. If `prefix` is specified, it
will be prefixed to each name (after the hyphens, of course), to avoid
name conflicts.

==__init__(self, topLevelItems=None, options=None)==

Create a PowerWalk instance, which can traverse all the specified
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

* start or end with tilde or pound-sign

* have extension 'bak' or 'bck'

* match r'^(backup|copy) (\\(?\\d+\\)? )?of'

* match r'\\b(backup|copy|bak)\\b' (but in these cases a warning is
issued unless I<--quiet> is in effect).

* Mac OS X "Duplicate" does `foo.txt` -> `foo copy.txt` -> `foo copy 2.txt`

* emacs backups append '~' or '~\\d+~' to the filename
For relevant emacs settings, see
L<https://stackoverflow.com/questions/151945/>).

* emacs auto-save files put '#' at start and end of filename (but
are usually deleted when you exit).

==isHidden(path) [static]==

Returns whether the file is hidden (for the moment, this just means
that the name starts with "."; Windows and Mac invisible files should
be added).

==isStreamable(obj)==

Returns true if the obj is of one of the known streamable classes.


==getStats(self, writer=sys.stderr)==

Return a printable string listing various statistics, or
get individual stats from the PowerWalk object (they are actually kept
in a dict in a `TraversalState` object: `pw.travState.stats[name]`.

    n = pw.getStat('regular')

gets you the total number of regular (non-dir, non-tar, non-ignored....) items
that have been returned so far.

The statistics include the number of files of each of these kinds:
    * regular
    * directory
    * tar
    * gzip
    * hiddenDir: directories that were skipped
    * hiddenFile: files that were skipped
    * tarSubdir: subdirectories inside tar files
    * backup: apparent backup files

The statistics also include:

    * nodesTried: Total number of files examined. This
includes files that are filtered out, but not the descendants of directories,
tar files, or other containers that are themselves filtered out.
    * containersOpened: Total number of directories, tar files, and other
containers that are actually opened.
    * leafs: Files (not directories or containers) examined.
    * ignored: Total items ignored (see below for finer details).
    * errors: Files that could not be examined or opened, for
example due to not existing.
    * maxDepthReached: How deep the deepest branch of the traversal went.

and the number of files that were skipped for various
reasons (if a file has several reasons to be skipped, only the one that
was checked first is counted):
    * ignoredSamples: Due to `--sampleFactor`.
    * ignoredBackups: Due to being an apparent backup file.
    * ignoredHiddens: Due to having a dot-initial name.
    * ignoredByExclExtensions: The file extension was excluded.
    * ignoredByInclExtensions: The file extension was included.
    * ignoredByExclNames: The file name was excluded.
    * ignoredByInclNames: The file name was included.
    * ignoredByExclPaths: The file path was excluded.
    * ignoredByInclPaths: The file path was included.
    * ignoredByMinDepth: Files found at too shallow nesting depth.


=======

==setOption(self, name, value)==

Change the value of an available option. Options can also
be set on the constructor via like-named keyword options, or en masse
using ` addOptionsToArgparse()` and `setOptionsFromArgparse()`.
''Note'': There are a few more options that are not part of
the PowerWalk class, but are available when this script is run standalone.
They are described in the full list of options at the end of this help.


===File selection options===

''Note'': Regexes given for these options (where applicable), do not
automatically have "^" and "$" added. They match if they match anywhere
in the string. You can of course add one or both of those metacharacters
explicitly to the option value.

* "backups": Include `.bak` and similar files? Default: False

* "hidden": Include hidden (.-initial) files '''and''' directories.
This option differs from most other file selection options, in that it
affects directories. This is to address things like excluding `.git` and the
many config directories commonly placed in home directories.
Default: False (that is, hidden items are ignored). Items under
ignored directories are '''entirely''' skipped -- their descendants are not
traversed, examined, or counted.

* "excludeExtensions": Regex for item extensions not to allow. Default: ''.
See also I<includeExtensions>. As with `grep` and many other
tools, exclusions override inclusions if both apply to the same file.
The "or" operator ("|") is allowed in the regex, which is an easy
way to exclude (or include) multiple extensions.

* "excludeNames": Regex for item basenames not to allow. Default: ''.
This matches against the names ''without'' any extension.
See also I<includeNames>.

* "excludePaths": Regex for paths not to allow. Default: ''.
See also I<includePaths>.

* "includeExtensions": Regex for (only) item extensions to allow. Default: ''.
See also I<excludeExtensions>.

* "includeNames": Regex for (only) item basenames to allow. Default: ''.
This matches against the names ''without'' any extension.
See also I<excludeNames>.

* "excludePaths": Regex for paths not to allow. Default: ''.
See also I<includePaths>.

* "includeInfos": Regex to match what the *nix `file` command (q.v.) says
about the file. For example, some versions of `file` return descriptions like:

    ** POSIX shell script text executable, ASCII text
    ** ASCII text, with very long lines, with no line terminators
    ** Python script text executable, UTF-8 Unicode text, with very long lines, with CRLF, CR, LF line terminators, with escape sequences, with overstriking

* "excludeInfo": Regex for `file` command results not to allow. Default: ''.
See also I<includeInfos>.

===Container and similar options===

* "openGzip": If True (the default), `gzip` files will be opened as if they were
directories, and the individual items within them will be returned.

* "openTar": If True (the default), `tar` files will be opened as containers
(optionally generating PWType.OPEN and PWType.CLOSE events),
and the individual items within them will be returned.

* "followLinks": If True (the default is False), *nix symbolic
links will be followed, and their targets opened or traversed
as if they had been at or under the link's location.
This does not include Mac "aliases", Windows "shortcuts", weblocs, etc.


===Reading options===

* `close`: When the next item is requested, close the handle to the prior
one (only makes sense if `open` is also specified).

* `encoding`: Use this character encoding for input. Default: `utf-8`

* `mode`: What `mode` to pass to `codecs.open` (when the `open`
options is in effect. Default: `rb`.

* `open`: When a non-ignorable leaf is reached, open it and return the handle
as the second item in the returned tuple (which is otherwise None).
''Note'': For items that do not have a normal path, such as files embedded in
container such as tar or zip files, a handle to read them is always returned,
regardless of how the `open` option is set.


===Other options===

* `containers` (default True): If True,
then open and close events will be generated
for each container (such as a directory, gzip, or tar file) that is entered.
The third member of the returned tuple (`what`) is PWType.OPEN and
PWType.CLOSE, respectively.

* `ignorables` (default False): If True, then events will be generated
even for items (containers and leaves) that are filtered out -- such as
hidden files or directories, etc. Such events will have `what`
returned as PWType.IGNORE.

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

* `sampleFactor` (default: 100.0): Include only this % of the eligible files.
If set to a value above 0.0 and below 100.0, each leaf item that would have
been returned, has only this % change of actually being returned.
Others are reclassified as ignorable. The result will only
amount to approximately the requested percentage.

* `sort`: Sort the items in each directory in the specified way.
Default: 'none' (just use whatever `os.listdir` returns). Other choices:

** `name`:  sort by filename
** `iname`: sort by filename, ignoring case.
** `atime`: file access time
** `ctime`: file creation time
** `mtime`: file modification time
** `size`: File length in bytes
** `ext`: Extension as returned by `os.path.splitext`

* `notify`: Display a message as each new file starts. Default: False

==traverse(self)==

Generate a sequence of chosen files (and if requested, pseudo-files,
such as items
from a zip, tar, or other container). Each iteration returns a tuple of
(path, fh), where `fh` is a readable. For regular files this is as returned
by `codecs.open()` with the `mode` and `encoding` specified as options
(if the `open` option is in effect; otherwise fh is returned as None).
For items within tar, gzip, or other supported archive types, it will be
the readable interface from the corresponding package (regardless of whether
`open` is set).

Ignored items (such as backups if the `backups` option has not
been set), are quietly skipped unless the `ignorables` options is set.

Containers such as directories and archive files generate start and end
events with the appropriate path, but the file handle is returned as None,
and the `what` is PWType.OPEN or PWType.CLOSE, respectively.
These events can be suppressed entirely by setting the `containers` option
to False.


=Known bugs and limitations=

* If you don't specify -r, it won't even list a directory that's specified
at the very top level. Currently, I've hacked it so that directories that
are specified directly, at the top level, are always recursed into
regardless of the setting of `--recursive`. I'm not certain what the ideal
behavior is:

** `ls` (unless you set `-d`) lists content for all dirs specified directly.
** `ls -d -r` seems to not recurse at all.
** `ls *" lists all the files, ''then'' all the directories with their files.

* Default indented list unindents some files, and/or fails to display
directory events.

* `--exec` is still experimental, and related `find` options like `--execdir`
are not there at all.

* The script will warn if it can't find all the file-format libraries
installed (for tar, gzip, etc.),
but it will work fine as long as you don't specifically need the missing ones.

* I've used this almost exclusively for reading (for example, picking
out just the desired files from an NLP corpus like OANC or MASC). So writing
is not yet thoroughly tested. I imagine writing doesn't work well for container
files (tar, gzip, etc.).

* Statistics of the current run as well as the current
nesting depth of the traversal (in `.depth`), are separated into a
TraversalState object. A reference to that object is
kept directly in the PowerWalk object instance as `PowerWalk.travState`.
So if you try to run two traversals from the same PowerWalk instance, you may
have problems accessing `PowerWalk.`. However, PowerWalk
itself doesn't use it, so it should be ok. It's really only stored there
so command-line usage can display statistics at the end.
That won't work if you modify it to run a second
`PowerWalk.traverse()` before printing statistics that way. If you create two
separate PowerWalk instances in such cases, you should be fine.

* You can only specify one regex for each of the include/exclude options
that take regexes. These options do not apply to directories (ideally, they
should be separately settable for dirs and files (and maybe other containers).

* There is no protection against circular links.

* With `--serialize`, there is no control over 0-padding (always a minimum
of 4 digits), or whether the serial number is prefixed or suffixed. I provide
other utilities that may help with file organization (see next section).


=Related commands=

`find` + `exec`. Find does a really nice job of finding things. PowerWalk is mainly intended to be even easier to use
from Python code, especially for people (like corpus linguists) who work with
tons of sample files in complicated directory and container structures.

[https://github.com/sderose/FileManagement/lss], [https://github.com/sderose/FileManagement/findIdenticalFiles].

[https://github.com/sderose/FileManagement/lsoutline] produces a file listing
similar to what `PowerWalk` produces
when run from the command line. But you can do fancier selection here (that
script may be upgraded to just use PowerWalk underneath).


=References=

See [../FileSelectionOptionsOfNixCommands.md] for a survey of what different
*nix command provide for file-selection, sorting, format support, etc.


=To do=

==Most wanted==

* Support additional compression methods.

* Protect against circular links.

* add move/link/cat similar to `--copyTo`, and support setting
xattr to say where copied from.

* include/exclude for dirs (and containers?), not just files.

* Option to specify a file like .gitignore or .dockerignore, specifying
files to exclude.

==Additional filters  (cf 'find')==

* permissions, owner and group ids (and none), inum
* date, age, and file size (chars, bytes, blocks, kmgtp), file count
* Mac fs metadata (kmdItem... and all that). See my `macFinderInfo`.
* Option to not cross device or filesystem bounds (see `find -x`)
* distinguish maxfiles tried vs. succeeded
* atime, ctime, mtime, mindepth, cf Bmin [aBcm]?(newer|time|min)
* depth
* empty
* exec(dir)
* group/nogroup, user/nouser/uname/uid/
* newer/old cre/mod/acc time vs. specified file
* -print0
* 'i' prefix for specific tests
* -xattr, -xattrname (and xattr k op v)
* negation and maybe booleans?

==Other options==

* Do files then dirs, sorted separately like ls.

* Option to show invisibles in filenames (ls -B does octal, but ick).
* Limit max/min/total size of files

* `--sort` should provide a `reverse` option, and an option to put
directories before files.

* Support Mac aliases, bookmarks, and webloc files.
See my `resolveLinks` attempt.
[https://pypi.org/project/mac_alias/].
See [https://stackoverflow.com/questions/48862093] (how-to-read-change-and-write-macos-file-alias-from-python),
[http://mac-alias.readthedocs.io/en/latest] and
[https://docs.python.org/2/library/macostools.html].

* Support URLs (can *nix, Mac, or Win aliases point to URLs?

* Sampling of every nth file, first n from each directory, etc.

* Option to "mark" the files, e.g. with an xattr or Finder flag, and do set
operations that refer to the marks.

==Interface==

* Make a way for the caller to find out what kind of container they're in.
Maybe just pass back the container handle? Or they can poke at the path.

* Synchronize with `find` option and/or names where appropriate:
** -L for --followlinks (`find` used to use -follow)
** -s for `-sort name`
** -d (depth-first)?  -depth nq
** -x (don't cross device boundaries) = -mount = -xdev
** -acl?
** -wholename for -path

* Offer warning if no eligible files found in a dir? (cf `find -empty`).

* Possibly a stat-like "%" option for output? See `FileInfo` class.


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
* 2020-09-15: Fix several bugs in filtering, improve reporting and
option-setting. Add `--includeInfos` and `--excludeInfos`.
* 2020-10-06: Fix `--includeNames`, make it and `--excludeName` use extension.
Add `--copyTo` and `--serialize`.
* 2020-10-09: Add `--exex`.
* 2020-10-14: Improve how topLevelItems are passed and defaulted.
Clean up `errorEvents` options vs. `errors` statistic.
* 2020-10-20f: Add `--type` similar to *nix `find`. Fix depth counting.
* 2020-11-24: Add `--no-recursive`. Make exceptions subclass of a cover type.
Add `--reverseSort` and clean up sorting. Make top-level dirs always
recurse.

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
# A bunch of classes for readable stuff. There has to be an easier way....
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
# The 'exceptions' option signals directory start/end by raising exceptions.
# Seems to me cleaner than passing a "magic" event type back.
#
# There is no exception corresponding to sucessfully returning a
# readable/writable leaf item, because that's the unexceptional case.
#
class ItemException(Exception):
    pass
class ItemOpening(ItemException):
    pass
class ItemClosing(ItemException):
    pass
class ItemIgnorable(ItemException):
    pass
class ItemError(ItemException):
    pass
class ItemMissing(ItemError):
    pass
class Finished(ItemException):
    pass


###############################################################################
# These are the types of events that are stored as the third item in
# PWFrame objects (see next section), which are kept on the TraversalState
# stack during active traversals.
#
class PWType(Enum):
    OPEN    = 1          # The beginning of a directory, tar file, etc.
    CLOSE   = 2          # The end of a directory, tar file, etc.
    IGNORE  = 3          # Notification of a filtered-out object
    LEAF    = 4          # An actual readable/writable object
    ERROR   = -1         # Generic error
    MISSING = -2         # Specific error, item not found


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

    It has methods that do "the right thing" when called for an item
    confirmed as an OPEN, CLOSE, LEAF, IGNORE, or ERROR (based on the
    options in effect, a reference to which is passed to the constructor).
    """
    def __init__(self, options):
        super(TraversalState, self).__init__()
        self.depth = 0
        self.iString = '    '
        self.options = options
        self.stats = {
            "nodesTried"                 : 0,  # +
            "containersOpened"           : 0,  # +
            "leafs"                      : 0,  # +
            "ignored"                    : 0,
            "errors"                     : 0,  # +
            "maxDepthReached"            : 0,

            "regular"                    : 0,
            "directory"                  : 0,
            "tar"                        : 0,
            "gzip"                       : 0,
            "hiddenDir"                  : 0,
            "hiddenFile"                 : 0,
            "tarSubdir"                  : 0,
            "backup"                     : 0,

            "ignoredSamples"             : 0,
            "ignoredHiddens"             : 0,  # TODO: Not counted yet
            "ignoredByExcludeExtensions" : 0,
            "ignoredByExcludeNames"      : 0,
            "ignoredByExcludePaths"      : 0,
            "ignoredByExcludeInfos"      : 0,
            "ignoredByIncludeExtensions" : 0,
            "ignoredByIncludeNames"      : 0,
            "ignoredByIncludePaths"      : 0,
            "ignoredByIncludeInfos"      : 0,
            "ignoredByExcludeDir"        : 0,
            "ignoredByIncludeDir"        : 0,

            "ignoredByType"              : 0,
            "ignoredByMinDepth"          : 0,
        }

    def getStats(self, showZeroes=True):
        """Generate a displayable list of the statistics.
        """
        buf = "\nItems processed:\n"
        for k in sorted(self.stats.keys()):
            if (showZeroes or self.stats[k]>0):
                buf += "    %-30s %8d\n" % (k, self.stats[k])
        return buf

    def getStat(self, name):
        return self.stats[name]

    def bump(self, name, n=1):
        """Increment a named statistic.
        """
        if (name not in self.stats):
            raise ValueError("No stat named '%s'." % (name))
        self.stats[name] += n

    def indent(self):
        return self.iString * self.depth

    ###########################################################################
    # Stack managers for the main event types.
    #
    _ = """Event/Exception/Stack managers.
        * If caller doesn't want the event, return None.
        * If called wants it as an exceptions, raise one then return None.
        * Otherwise stack it, return the PWFrame, then pop it.
        ==> Iff this returns a PWFrame the caller should yield it.
    """
    def openContainer(self, path:str, fh:object):
        """Create and push a stack frame for the thing we found.
        Files that are filtered out don't even get here. But for containers,
        we mightgenerate events or excpetions (see options['containers')
        """
        thePWFrame = PWFrame(path, fh, PWType.OPEN)
        assert isPWFrameOK(thePWFrame)

        self.bump("containersOpened")
        self.append(thePWFrame)
        self.depth += 1  # not thread-safe
        if (self.depth > self.stats['maxDepthReached']):
            self.stats['maxDepthReached'] = self.depth

        warn(2, "In openContainer, containers %d, exceptions %d." %
            (self.options['containers'], self.options['exceptions']))
        if (not self.options['containers']):
            return None
        elif (self.options['exceptions']):
            raise ItemOpening
        return thePWFrame

    def handleLeaf(self, path:str, fh:object):
        """Create and push a stack frame for the thing we found.
        Files that are filtered out don't even get here. But for containers,
        we mightgenerate events or excpetions (see options['containers')
        """
        warn(2, "handleLeaf: %s" % (path))
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
        #warn(1, "handleIgnorable: %s" % (path))
        self.bump("ignored")
        if (not self.options['ignorables']):
            return None
        elif (self.options['exceptions']):
            raise ItemIgnorable
        else:
            return PWFrame(path, None, PWType.IGNORE)

    def handleError(self, path:str, message:str="Item Error",
        errorType:PWType=PWType.ERROR):
        """Called for missing, unopenable, etc.
        """
        warn(1, "handleError: %s" % (path))
        self.bump("errors")
        if (not self.options['errorEvents']):
            return None
        elif (self.options['exceptions']):
            if (errorType == PWType.MISSING):
                raise ItemMissing(message + " [%s]" % (path))
            else:
                raise ItemError(message + " [%s]" % (path))
        else:
            return PWFrame(path, None, errorType)

    def closeContainer(self):
        """Called at the end of any node, whether container or leaf.
        For leafs, don't yield a separate event, just pop the stack.
        """
        warn(2, "In closeContainer, containers %d, exceptions %d." %
            (self.options['containers'], self.options['exceptions']))
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
    inspiration. See the features description under -h, and the utility
    to add them to argparse: addOptionsToArgparse().
    """

    __optionTypes = {

        # Name filtering
        "excludeExtensions"   : "REGEX",
        "excludeNames"        : "REGEX",
        "excludePaths"        : "REGEX",
        "excludeInfos"        : "REGEX",
        "includeExtensions"   : "REGEX",
        "includeNames"        : "REGEX",
        "includePaths"        : "REGEX",
        "includeInfos"        : "REGEX",

        "includeDir"          : "REGEX",
        "excludeDir"          : "REGEX",

        "backups"             : bool,
        "close"               : bool,
        "containers"          : bool,
        "encoding"            : str,
        "exceptions"          : bool,
        "followLinks"         : bool,
        "hidden"              : bool,
        "ignorables"          : bool,
        "maxDepth"            : int,
        "maxFiles"            : int,
        "maxSize"             : int,
        "minDepth"            : int,
        "minSize"             : int,
        "mode"                : str,
        "notify"              : bool,
        "open"                : bool,
        "openGzip"            : bool,
        "openTar"             : bool,
        "recursive"           : bool,
        "reverseSort"         : bool,
        "sampleFactor"        : float,
        "sort"                : str,
        "type"                : str,
        "verbose"             : int,
    }

    def handlePathsArg(self, topLevelItems):
        if (not topLevelItems):
            return [ os.environ['PWD'] ]
        elif (isinstance(topLevelItems, list)):
            return topLevelItems
        elif (isinstance(topLevelItems, str)):
            return[ topLevelItems ]
        else:
            raise ValueError("First arg must be path, list, or None for PWD.")

    def __init__(self, topLevelItems=None, **kwargs):
        self.topLevelItems = self.handlePathsArg(topLevelItems)

        self.travState = None  # Used during traversal (not thread-safe!) TO DO

        self.options = {
            "excludeExtensions"   : "",
            "excludeNames"        : "",
            "excludePaths"        : "",
            "excludeInfos"        : "",
            "includeExtensions"   : "",
            "includeNames"        : "",
            "includePaths"        : "",
            "includeInfos"        : "",

            "includeDir"          : "",
            "excludeDir"          : "",

            "backups"             : False,
            "close"               : False,    # Do fh.close() on leafs for user.
            "containers"          : True,     # Events for container start/end?
            "encoding"            : "utf-8",  # Character encoding
            "errorEvents"         : False,    # Return events for errors?
            "exceptions"          : False,    # Exception for containers?
            "followLinks"         : False,
            "hidden"              : False,
            "ignorables"          : False,    # Events even for ignored stuff?
            "maxDepth"            : 0,
            "maxFiles"            : 0,
            "maxSize"             : 0,
            "minDepth"            : 0,
            "minSize"             : 0,
            "mode"                : "rb",     # Read, write, bin, etc.
            "notify"              : False,    # Tell caller on start/end dir
            "open"                : False,    # Do leaf open()s for user.
            "openGzip"            : False,
            "openTar"             : False,
            "recursive"           : False,
            "reverseSort"         : False,
            "sampleFactor"        : 100.0,    # Take everything.
            "sort"                : "",       # TODO: Test in tar, zip, etc.
            "type"                : "",
            "verbose"             : 0,
        }

        if (kwargs):
            for k, v in kwargs.items():
                self.setOption(k, v, strict=True)

    def getOption(self, name):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        return self.options[name]

    def setOption(self, name, value, strict=False):
        """Note: If the options are coming in from argparse, an unset
        list or dict will perhaps be None, so fix to an empty one.
        """
        if (name not in self.__optionTypes):
            if (strict):
                raise ValueError("Unknown option '%s'." % (name))
        else:
            theType = self.__optionTypes[name]
            if (theType == "REGEX"):
                if (value):
                    try:
                        self.options[name] = re.compile(value)
                    except (re.error, TypeError) as e:
                        warn(0, "Cannot compile option %s: %s\n    %s" %
                            (name, value, e))
                return
            if (value is None):
                if (theType == list): value = []
                elif (theType == dict): value = {}
                else: value = 0
            try:
                self.options[name] = theType(value)
                if (name=='verbose'):
                    global verbose
                    verbose = value
                elif (name in [ 'excludeNames', 'includeNames' ] and
                    '.' in value):
                    warn(0, "Option --%s '%s' won't match against extensions." %
                        (name, value))  # TODO: Check
            except (TypeError, re.error) as e:
                warn(0, "Cannot cast value '%s' for option '%s' to %s:\n    %s"
                    % (value, name, theType.__name__, e))

    def setOptionsFromArgparse(self, argsObj=None, prefix=""):
        """Have to ignore any that aren't ours.
        """
        for k, v in argsObj.__dict__.items():
            qname = prefix+k
            if (qname in self.options): self.setOption(qname, v, strict=False)

    @staticmethod
    def addOptionsToArgparse(parser, prefix='', singletons=True):
        """Provide an easy way to add all our options to a main program
        (without getting all the others). Use setOptionsFromArgparse() to
        copy them in from the argparse result, ignoring any others.
        """
        if (not prefix.startswith('-')):
            prefix = "--" + prefix

        for thing in [ "Extensions", "Names", "Paths", "Infos" ]:
            for sign, abbr in [ ("Include", "i"), ("Exclude", "x") ]:
                n1 = prefix + sign.lower() + thing
                n2 = prefix + sign.lower() + "-" + thing
                n3 = prefix + abbr + thing
                parser.add_argument(n1, n2, n3, type=str, metavar='R',
                help='%s items with %s matching this regex.' %
                    (sign, thing.lower()))

        # And the grep-like ones
        parser.add_argument(
            prefix + "include", action='store_true',
            help='Like grep. Still experimental.')
        parser.add_argument(
            prefix + "exclude", action='store_true',
            help='Like grep. Still experimental.')
        parser.add_argument(
            prefix + "includeDir", prefix + "include-dir", action='store_true',
            help='Like grep. Still experimental.')
        parser.add_argument(
            prefix + "excludeDir", prefix + "exclude-dir", action='store_true',
            help='Like grep. Still experimental.')

        parser.add_argument(
            prefix + "backups", action='store_true',
            help='Include (seeming) backup items,like .bak, ~x, #x#,....')
        parser.add_argument(
            prefix + "close", action='store_true',
            help='Close leaf items when done (requires --open).')
        parser.add_argument(
            prefix + "containers", action='store_true', default=True,
            help='Generate events (or --exceptions) for container open/close.')
        parser.add_argument(
            prefix + "no-containers", action='store_false',
            dest='containers',
            help='Do not generate events (or --exceptions) for container open/close.')
        parser.add_argument(
            prefix + "encoding", type=str,metavar='E', default="utf-8",
            help='Assume this character set. Default: utf-8.')
        parser.add_argument(
            prefix + "errorEvents", action='store_true',
            help='Return events for errors like unopenable items.')
        parser.add_argument(
            prefix + "exceptions", action='store_true',
            help='Report container oper/close as exceptions, not events.')
        parser.add_argument(
            prefix + "followLinks", action='store_true',
            help='Follow *nix links to the destination.')
        parser.add_argument(
            prefix + "hidden", action='store_true',
            help='Include file and directories whose names begin with dot.')
        parser.add_argument(
            prefix + "ignorables", action='store_true',
            help='Return events (or exceptions) for ignorable items.')
        parser.add_argument(
            prefix + "notify", action='store_true',
            help='Some extra notifications')
        parser.add_argument(
            prefix + "open", action='store_true',
            help='Open leaf items and return a readable handle.')

        parser.add_argument(
            prefix + "openTar", action='store_true',
            help='Open tar files as if they were directories.')
        parser.add_argument(
            prefix + "openGzip", action='store_true',
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
                prefix + "recursive", action='store_true',
                help='Descend into subdirectories.')
        parser.add_argument(
            prefix + "no-recursive", action='store_false', dest='recursive',
            help='Do NOT descend into subdirectories.')

        ### argparse bug 3.6? Can't have "% " in help string?!!
        parser.add_argument(
            prefix + "sampleFactor", metavar='%', type=float, default=100.0,
            help='Sample only this percentage of eligible items.')
        parser.add_argument(
            prefix + "reverseSort", action='store_true',
            help='If --sort is used, reverse the order.')
        parser.add_argument(
            prefix + "sort",              type=str, default='none',
            choices = [ 'none',
                'name', 'iname', 'atime', 'ctime', 'mtime', 'size', 'ext' ],
            help='Sort directory members by what? Default: none. ')

        parser.add_argument(
            prefix + "type",              type=str, default="",
            choices = [ "b", "c", "d", "f", "l", "p", "s", "D", "P", "W" ],
            help='As for the "find" command, plus Door, Port, Whiteout.')

        # Test that all the known options are available.
        for op in PowerWalk.__optionTypes.keys():
            if (prefix+op not in parser._option_string_actions):
                warn(0, "addOptionsToArgparse: '%s' not added.\nList is: %s." %
                    (prefix+op,
                    ", ".join(parser._option_string_actions.keys())))
                sys.exit()

        return parser

    def getStat(self, name):
        return self.travState.stats[name]

    def traverse(self, topLevelItems=None):
        """Use ttraverse on the given path (or each top-level file or dir,
        to recurse through the files/directories requested and return
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

        if (topLevelItems is not None):
            tops = self.handlePathsArg(topLevelItems)
        else:
            tops = self.topLevelItems

        for tl in (tops):
            warn(1, "\n******* Starting top-level item '%s'." % (tl))
            for tsf in self.ttraverse(tl, trav):
                trav.bump("nodesTried")
                warn(2, "tried %d, max %d." %
                    (trav.stats["nodesTried"], self.options["maxFiles"]))
                if (self.options["maxFiles"] and
                    trav.stats["nodesTried"] > self.options["maxFiles"]): break
                yield tsf
        if (self.options["exceptions"]):
            raise Finished()
        return

    def ttraverse(self, path:str, trav:TraversalState):
        """Recurse as needed.
        """
        warn(2, "%sttraverse at '%s'" % ("  "*len(trav), path))

        if (self.options['maxDepth'] > 0 and               # MAXDEPTH REACHED
            len(trav) > self.options['maxDepth']):
            return

        elif (not self.passesFilters(path, trav)):         # IGNORABLE FILE
            tsf = trav.handleIgnorable(path)
            if (tsf): yield tsf

        elif (not os.path.exists(path)):                   # NOT FOUND
            tsf = trav.handleError(path, "Item not found")
            if (tsf): yield tsf

        elif (os.path.isdir(path)):                        # DIRECTORY
            trav.bump('directory')
            self.recordEvent(trav, 'directory')
            # If a dir was specified explicit at the top level, that seems
            # special, and we should look in it (at least for things like
            # ".", and counting files. But always? not sure.
            #
            if (not self.options['recursive']
                and trav.depth > 0):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                tsf = trav.openContainer(path, None)
                warn(1, "Opening dir '%s' (tsf %s)." % (path, tsf))
                if (tsf): yield tsf
                children = os.listdir(path)
                if (self.options['sort']):
                    children = self.chSort(
                        path, children, self.options['reverseSort'])
                for ch in children:
                    chPath = os.path.join(path, ch)
                    for chFrame in self.ttraverse(chPath, trav):
                        yield chFrame
                tsf = trav.closeContainer()
                warn(1, "Closing dir '%s', tsf %s." % (path, tsf))
                if (tsf): yield tsf

        elif (False and tarfile.is_tarfile(path)):         # TAR FILE
            self.recordEvent(trav, "tar")
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
                        self.recordEvent(trav, "tarSubdir")
                        # TODO: add tar internal recursion!
                    else:  # also issyn, islnk, ischr, isblk, isfifo, isdev
                        warn(0, "Non-file, non-dir) in tar file.")
                tfObject.closeContainer()
                tsf = trav.closeContainer()
                if (tsf): yield tsf

        elif (path.endswith(".gz")):                       # GZIP FILE
            self.recordEvent(trav, 'gzip')
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
            if (not self.options['open']):
                fh = None
            else:
                fh = codecs.open(path, mode=self.options['mode'],
                    encoding=self.options['encoding'])
                # Py 2: codecs.open returns old-style class StreamReaderWriter
                if (PY2 and '__class__' in fh and
                    fh.__class__.__name__ != 'StreamReaderWriter'):
                    raise ValueError("Got type '%s' (%s) for %s." %
                        (type(fh), fh.__class__.__name__, path))
            yield trav.handleLeaf(path, fh)
            if (self.options['close'] and fh):
                fh.close()

        return

    def passesFilters(self, path, trav):
        """Check the file at 'path' against all the filters, and
        return True iff it's one the user wants. 'hidden' applies to
        containers (such as directories) and to leafs (such as files).
        Most other filters apply only to one or the other.
        """
        if (os.path.isdir(path)):
            return self.dirPassesFilters(path, trav)
        return self.filePassesFilters(path, trav)

    def dirPassesFilters(self, path, trav):
        if (self.options['type'] and self.options['type']!='d'):
            self.recordEvent(trav, "ignoredByType")
            return False
        if (not self.options['hidden'] and isHidden(path)):
            self.recordEvent(trav, "hiddenDir")
            return False
        if (self.options['excludeDir'] and
            re.search(self.options['excludeDir'], path)):
            self.recordEvent(trav, 'ignoredByExcludeDir')
            return False
        if (self.options['includeDir'] and
            not re.search(self.options['includeDir'], path)):
            self.recordEvent(trav, 'ignoredByIncludeDir')
            return False
        self.recordEvent(trav, 'directory')
        return True

    def filePassesFilters(self, path, trav):
        """Test most of the file-filtering conditions.
        Return True only if the all pass (reaching the final 'else').
        """
        # TODO: Add --include and --exclude like for grep
        _, tail = os.path.split(path)
        (_, extPart) = os.path.splitext(tail)
        extPart = extPart.strip(". \t\n\r")

        passes = False  # Assume the worst for now...
        if (not self.passesType(path)):
            self.recordEvent(trav, "ignoredByType")

        elif (len(trav)<self.options['minDepth']):
            self.recordEvent(trav, "ignoredByMinDepth")

        elif (not self.options['hidden'] and isHidden(path)):
            self.recordEvent(trav, "hiddenFile")

        elif (self.options['excludeExtensions'] and
            re.search(self.options['excludeExtensions'], extPart)):
            self.recordEvent(trav, 'ignoredByExcludeExtensions')
        elif (self.options['includeExtensions'] and
            not re.search(self.options['includeExtensions'], extPart)):
            self.recordEvent(trav, 'ignoredByIncludeExtensions')

        elif (self.options['excludeNames'] and
            re.search(self.options['excludeNames'], tail)):
            self.recordEvent(trav, 'ignoredByExcludeNames')
        elif (self.options['includeNames'] and
            not re.search(self.options['includeNames'], tail)):
            self.recordEvent(trav, 'ignoredByIncludeNames')

        elif (self.options['excludePaths'] and
            re.search(self.options['excludePaths'], path)):
            self.recordEvent(trav, 'ignoredByExcludePaths')
        elif (self.options['includePaths'] and
            not re.search(self.options['includePaths'], path)):
            self.recordEvent(trav, 'ignoredByIncludePaths')

        elif (self.options['excludeInfos'] and
            re.search(self.options['excludeInfos'], getFileInfo(path))):
            self.recordEvent(trav, 'ignoredByExcludeInfos')
        elif (self.options['includeInfos'] and
            not re.search(self.options['includeInfos'], getFileInfo(path))):
            self.recordEvent(trav, 'ignoredByIncludeInfos')

        elif (not self.options['backups'] and isBackup(path)):
            self.recordEvent(trav, "backup")
        else:
            self.recordEvent(trav, 'regular')
            passes = True

        warn(2, "%s filter: %s" % ("PASS" if passes else "FAIL", tail))
        return passes

    def passesType(self, path):
        """Test like "find -type", return if it's ok.
        """
        mode = os.stat(path).st_mode
        ty = self.options['type']

        if (not ty):
            return True

        elif (ty=="b"):                             # block special
            if (not stat.S_ISBLK(mode)): return False
        elif (ty=="c"):                             # character special
            if (not stat.S_ISCHR(mode)): return False
        elif (ty=="d"):                             # directory
            if (not stat.S_ISDIR(mode)): return False
        elif (ty=="f"):                             # regular file
            if (not stat.S_ISREG(mode)): return False
        elif (ty=="l"):                             # symbolic link
            if (not stat.S_ISLNK(mode)): return False
        elif (ty=="p"):                             # FIFO
            if (not stat.S_ISFIFO(mode)): return False
        elif (ty=="s"):                             # socket
            if (not stat.S_ISSOCK(mode)): return False

        # Python ones that go beyond "find -type"
        elif (ty=="D"):                             # DOOR
            if (not stat.S_ISDOOR(mode)): return False
        elif (ty=="P"):                             # PORT
            if (not stat.S_ISPORT(mode)): return False
        elif (ty=="W"):                             # whiteout
            if (not stat.S_ISWHT(mode)): return False

        else:
            warn(0, "Unknown -type value '%s'." % (ty))
        return True

    def chSort(self, curPath, chList, reverse=False):
        """Sort a file-list returned from os.listdir somehow.
        """
        warn(2, "Sorting by '%s'." % (self.options['sort']))
        if (self.options['sort'] == 'none'):
            return chList

        if (self.options['sort'] == 'name'):
            theLambda = None
            #chList.sort()
        elif (self.options['sort'] == 'iname'):
            theLambda = lambda x: x.lower()
        elif (self.options['sort'] == 'atime'):
            theLambda = lambda x: getatime(os.path.join(curPath, x))
        elif (self.options['sort'] == 'ctime'):
            theLambda = lambda x: getctime(os.path.join(curPath, x))
        elif (self.options['sort'] == 'mtime'):
            theLambda = lambda x: getmtime(os.path.join(curPath, x))
        elif (self.options['sort'] == 'size'):
            theLambda = lambda x: getsize(os.path.join(curPath, x))
        elif (self.options['sort'] == 'ext'):
            theLambda = lambda x: splitext(os.path.join(curPath, x))[1]
        else:
            raise ValueError("Unknown sort method '%s'." %
                (self.options['sort']))
        chList.sort(key=theLambda, reverse=reverse)
        return chList

    def recordEvent(self, theStack:list, thing:str):
        """Count the kind of thing, and maybe say something.
        """
        self.travState.bump(thing)
        if (len(theStack) == 0):
            warn(2, "%s  Trying: empty stack (%s)" %
                ("  "*len(theStack), thing))
            return
        if (self.options['notify']):
            frame = theStack[-1]
            warn(2, "Trying %s: '%s' (cont=%s)" %
                (thing, frame.path, frame.what))
        return


###############################################################################
# Generic filename tests.
#
# See also diffDirs.py, findDuplicateFiles, lss, renameFiles
#
def isBackup(path, descendants=False):
    """Given a path, check the basename whether it's a backup file.
    If 'descendants' is set, also count if a containing dir name has 'backup'.

    Conventions vary, we catch quite a few, such as:
        foo.txt.bak
        #foo.txt#
        #foo#.txt
        ~foo.txt~
        Backup (\\d+) of foo.txt           -- Mac OS
        Copy (\\d+) of foo.txt             -- Mac OS
        foo.txt backup( \\d*)
        foo.txt (2020-09-15 13-34-38-374) -- bbedit backup convention

    Should anything with r'\\bbackup\\b' at all, count?
    Do we need something for temp files? /tmp..., .tmp, .temp...?

    TODO: Call this from other utils that need it...

    """
    bbeditDate = r' \(\d\d\d\d-\d\d-\d\d \d\d-\d\d-\d\d-\d+\)$'
    b = os.path.basename(path)
    root, ext = os.path.splitext(b)
    keywords = r'(backup|copy)'
    if (not b): return False
    if (b[0] in "~#" or b[-1] in "~#"): return True
    if (ext == "bak"): return True
    if (re.search(keywords + r'\b( \d+)?( of)\b', root, re.IGNORECASE)):
        return True
    if (re.search(r'\b(backup|copy|bak)\b', root, re.IGNORECASE)):
        return True
    if (descendants and re.match(r'\bbackups?\b', path)):
        return True
    if (re.match(bbeditDate, path)):
        return True
    return False

def isHidden(name):
    """Given a path, check the basename for initial dot.
    """
    return os.path.basename(name).startswith(".")

def isGenerated(name):
    """Is the name one that you probably don't need to archive, diff, or
    do certain other things with, since it's derived?
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

def getFileInfo(path):
    """See what the "file" command has to say about something...
    """
    buf = check_output([ "file", "-b", path ])
    return buf

def xset(path, prop, val):
    #import xattr
    warn(0, "--xattr is not yet supported for %s: %s=%s." % (path, prop, val))
    sys.exit()


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
            "--anonymousClose", action='store_true',
            help='Suppress container name at close.')
        parser.add_argument(
            "--closeDelim",  metavar='S', type=str, default="    <==",
            help='Display before directory name on close.')
        parser.add_argument(
            "--closeQuote", type=str, default='',
            help='Put this after the reported paths.')
        parser.add_argument(
            "--copyTo",  metavar='P', type=str,
            help='Copy chosen files to this directory (see --serialize).')
        parser.add_argument(
            "--count", action='store_true',
            help='Just report number of dirs and files found (probably want -r, too).')
        parser.add_argument(
            "--exec",  metavar='CMD', type=str,
            help='Run CMD on each selected item (like "find --exec").')
        parser.add_argument(
            "--iString", metavar='S', type=str, default='    ',
            help='Repeat this string to create indentation.')
        parser.add_argument(
            "--itemSep", metavar='S', type=str, default='',
            help='Put this in to separate items (e.g., a comma).')
        parser.add_argument(
            "--oformat", type=str, default='plain',
            choices = [ 'plain', 'json', 'html', 'sexp' ],
            help='format the output in this way.')
        parser.add_argument(
            "--openDelim",  metavar='S', type=str, default="==>",
            help='Display after directory name on open.')
        parser.add_argument(
            "--openQuote", type=str, default='',
            help='Put this before the reported paths.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--short", action='store_true',
            help='Only show the bottom-level name in the outline view.')
        parser.add_argument(
            "--serialize", action='store_true',
            help='With --copy, add a serial number to each file.')
        parser.add_argument(
            "--statFormat", action='store_true',
            help='Display output like "stat -f" for each file.')
        parser.add_argument(
            "--stats", action='store_true',
            help='Report overall statistics at the end.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')
        parser.add_argument(
            "--xattrs", action='store_true',
            help='With --copyTo, set xattr kmdItemWhereFroms to point back (not yet supported).')

        parser.add_argument(
            'files',               type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to files, directories, containers to traverse.')

        PowerWalk.addOptionsToArgparse(parser)

        args0 = parser.parse_args()

        if (args0.copyTo):
            if (not os.path.isdir(args0.copyTo)):
                warn(0, "No directory available at '%s'." % (args0.copyTo))
                sys.exit()

        if (args0.oformat == 'json'):
            args0.openDelim = '['
            args0.closeDelim = ']'
            args0.itemSep = ','
            args0.openQuote = '"'
            args0.closeQuote = '"'
            args0.anonymousClose = True
        elif (args0.oformat == 'html'):
            args0.openDelim = '<ol>'
            args0.closeDelim = '</ol>'
            args0.itemSep = ''
            args0.openQuote = '<li><file>'
            args0.closeQuote = '</file></li>'
            args0.anonymousClose = True
        elif (args0.oformat == 'sexp'):
            args0.openDelim = '('
            args0.closeDelim = ')'
            args0.itemSep = ''
            args0.openQuote = '"'
            args0.closeQuote = '"'
            args0.anonymousClose = True

        return(args0)


    ###########################################################################
    # Main
    #
    args = processOptions()
    verbose = args.verbose
    argDict = {}
    for k0 in vars(args).keys():
        argDict[k0] = vars(args)[k0]

    if (False and args.verbose):
        print("Args:\n%s")
        for k0 in sorted(argDict.keys()):
            print("    %-20s %-12s %s" %
                (k0, type(argDict[k0]).__name__, argDict[k0]))

    cwd = os.environ['PWD']
    if (not args.files): args.files = [ os.environ['PWD'] ]

    pw = PowerWalk(args.files)
    pw.setOptionsFromArgparse(args)

    if (args.statFormat):
        import PowerStat
        powerstat = PowerStat.PowerStat(args.statFormat)


#     pw = PowerWalk(args.files,
#         recursive=args.recursive,
#         notify=args.verbose)

    leafNum = 0
    whatCounts = defaultdict(int)
    for path0, fh0, what0 in pw.traverse():
        if (args.count):
            whatCounts[what0] += 1
            continue
        path0 = path0.replace(cwd, '.')

        if (args.short and pw.travState.depth > 1):
            path0 = os.path.basename(path0)

        ppath = args.openQuote + re.sub(r'"', "\\\"", path0) + args.closeQuote

        indent = args.iString*pw.travState.depth

        if (what0 == PWType.OPEN):
            print("%s%s %s" % (indent[4:], ppath, args.openDelim))
        elif (what0 == PWType.LEAF):
            leafNum += 1
            if (args.statFormat):
                print(powerstat.format(path0))
            elif (not args.quiet):
                print("%s%s%s" % (indent, ppath, args.itemSep))

            if (args.copyTo):
                _, baseName = os.path.split(path0)
                if (args.serialize): baseName = "_%04d%s" % (leafNum, baseName)
                warn(1, "copyTo '%s', base '%s'." % (args.copyTo, baseName))
                tgtPath = os.path.join(args.copyTo, baseName)
                if (os.path.exists(tgtPath)):
                    warn(0, "Target already exists: %s => %s" %
                        (ppath, tgtPath))
                else:
                    copyfile(path0, tgtPath)
                    if (args.xattrs):
                        xset(tgtPath, "kmdItemWhereFroms", "file://"+path0)
            if (args.exec):
                cmd = args.exec
                if ('{}' in cmd): re.sub(r'{}', path0, cmd)
                else: cmd += ' ' + path0
                try:
                    check_output(cmd, shell=True)
                except CalledProcessError as e:
                    warn(0, "Failed on %s:\n    %s" % (cmd, e))
        elif (what0 == PWType.CLOSE):
            print("%s%s%s%s" % (indent, args.closeDelim,
                "" if (args.anonymousClose) else ' '+ppath, args.itemSep))
        elif (what0 == PWType.IGNORE):
            print("%sIGNORING: %s%s" % (indent, ppath, args.itemSep))
        elif (what0 == PWType.ERROR):
            print("%sERROR: %s%s" % (indent, ppath, args.itemSep))

    if (args.count):
        print("Dirs: %d\nFiles: %d" %
            (whatCounts[PWType.OPEN], whatCounts[PWType.LEAF]))

    if (args.stats):
        warn(0, pw.travState.getStats(showZeroes=True))
