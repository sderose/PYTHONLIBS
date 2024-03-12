#!/usr/bin/env python3
#
# PowerWalk: More capable version os Python's os.walk.
# 2018-04-21: `PowerWalk.py` split out of my `countTags.py`.
#
#pylint: disable=W0212,W0603
#
import sys
import os
import argparse
import re
import random
import urllib
import stat
from collections import namedtuple, defaultdict
from os.path import getatime, getctime, getmtime, getsize, splitext
from enum import Enum
from shutil import copyfile
from subprocess import check_output, CalledProcessError
from typing import Dict, Any, Union, List  # , Callable

# Libraries for particular file "formats":
import codecs
import io

#from versionStatus import getGitStatus  # gitStatus

assert sys.version_info[0] >= 3

verbose = 0  # Also set by PowerWalk.setOptions("verbose")
stats = defaultdict(int)

def warning(lvl:int, msg:str):
    if (verbose>=lvl): sys.stderr.write("%s\n" % (msg))

# try:
#     import zip
# except ImportError:
#     warning(0, "Cannot import module 'zip'.")
try:
    import gzip
except ImportError:
    warning(0, "Cannot import module 'gzip'.")
try:
    import tarfile
except ImportError:
    warning(0, "Cannot import module 'tarfile'.")
# try:
#     import uu
# except ImportError:
#     warning(0, "Cannot import module 'uu'.")
# try:
#     import bz2
# except ImportError:
#     warning(0, "Cannot import module 'bz2'.")
# try:
#     import zlib
# except ImportError:
#     warning(0, "Cannot import module 'zlib'.")  # supports gzip
# try:
#     import zipfile
# except ImportError:
#     warning(0, "Cannot import module 'zipfile'.")


__metadata__ = {
    "title"        : "PowerWalk",
    "description"  : "Like os.walk, but with many features of *nix 'find', etc.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-04-21",
    "modified"     : "2023-12-01",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr="""
=Description=

PowerWalk is similar to Python's built-in `os.walk()`, but offers many
additional features, especially for file selection. In that respect it is
more similar to the *nix `find` command, but can be used either as a shell
command or as an API.

It has a simple iterator that returns a triple for each item,
containing a path, an (optional) open file handle (for non-containers), and a flag
that says whether this triple represents a container OPEN (such as starting a new
directory or tar file), an actual LEAF item, or a container CLOSE.

PowerWalk can also:
* skip returning items for OPEN and CLOSE of containers;
* return all paths in absolute form;
* open and/or close leaf files for you;
* open several kinds of compressed and container formats (such as `tar`),
* include or exclude by extensions, name patterns, path patterns, permissions, dates, etc.;
* exclude hidden or backup items, or by filesystem type or `file` matches;
* sort the items of each directory in various orders;
* random-sample only a % of eligible items;
* raise Exceptions instead of returning items for OPEN and CLOSE.


==Usage as a command==

If run on its own, `PowerWalk` displays the paths of selected
files under the specified
directory(s), or the current directory if none are specified (with `-r`
you must specify "*", sorry).

The default output format is pretty much like 'ls'. Thus, a recursive list
comes out with a heading for each directory, like this:
    subDir1        file1           subdir2        file2

    ./subDir1:
    file1.1    file1.2...

    ./subDir2:
    file2.1          file2.2...

Slightly unlike "ls", you can get recursion via "-r" or "--recursive"
as well as "-R". With "ls", "-r" gets reverse sorting; in PowerWalk get
that with "--reverseSort" (or abbreviations such as "--rev"), or various
other sorts with "--sort [what]".

To get a flat list of absolute paths (such as to feed to another command via "``",
in *nix you'd probably switch to "find". Here you can do:

    PowerWalk -R --flat
would give:
    [TODO: Add sample output]

To get all items quoted, use "--quote".
To avoid separate lines for directories, add "--type f"

Several special options apply in that case:

* `--copyTo [path]` -- Copy the chosen files to this directory. This flattens
whatever arrangement they come from -- all the leafs end up together.
See also
`--serialize`, which supports multiple files with the same name,
by appending numbers.

* `--exec` "[...{}...]\\;" -- Run a given command on each selected item,
much like `find --exec`. Output from the runs is printed unless
you specify `--quiet`.

* `--fileTypeFlag` -- Append a flag-character like "ls -F".

* `--serialize` -- put a serial number on each file with `--copyTo`
(use `--serializeFormat` to set the format (default "_%04d")).

===Command output format===

* `--oformat` [x] -- formats the list as 'plain', 'json', 'html',
or 'sexp' (LISP s-expressions).
Setting this to other than "plain" (the default), overrides specific
delimiter options described below.

* `--openQuote "x"` and `--closeQuote "y"` -- set delimiters to be put
before and after each name (typically both would be set to '"' or "'").
`--quote` may be used as shorthand to set both to "'", or
`--no-quote` to set both to "" (nothing). These options
are overridden by `--oformat` settings that demand certain quoting,
such as json, html, and sexp.

* `--anonymousClose` -- if set, do not print the name of directories or
other containers as they close.

* `--openDirString` and `--closeDirString` -- Display these around
the contents of directories and other containers (after their name').
For examle, "{" and "}". Default: "" and "".

* `--iString [s]` -- Repeat this string to create indentation.
Default: "    ".

* `--itemSep` -- Put this in to separate items (e.g., a comma).


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
  ** `--includeExtensions` and `--excludeExtensions` match file extensions
(without the ".") against full regexes. In particular, the "|" operator
is supported for "or". For example: `--ie "(py|pl|pm|cc)" works.
  ** `--includeFileInfos` and `--excludeFileInfos` match
characteristics reported by the *nix `file` command.
For example, this makes it easy to get Python files whether they have a `.py`
extension of not.

  ** `--backups` includes backup files, hidden files, etc.
  ** There is no `--dirOnly` option, but to get only directories, just use
"--type d".
  ** `--followLinks` makes PowerWalk treat *nix links if various ways.
  The values are defined by Enum "PWDisp" (for "disposition"):
      PWDisp.IGNORE: Ignore the link
      PWDisp.RETURN: Return the link itself
      PWDisp.FOLLOW: Resolve the link to its destination (if possible),
and return that.
  ** `--followWeblocs` makes PowerWalk follow Mac .webloc files,
  which contain a wrapped-up URL, and fetch the referenced document.
  ** `--recursive` or `-r` (which you'll often want) makes `PowerWalk` descend
  into sub-directories (but not tar or other container files -- for which
  there are separate options). If directories are specified directly, rathern
  than just being reached, the wil be recursed into in any case. Not sure
  if this is best or not.
  See "Known bugs and limitations" for more information.
  ** `--minDepth` and `maxDepth` constrain what
  directory or container depth limits to return files from.
  ** `--type [t]` is similar to the same-name option in `find`, except that
  you can give more than one type-letter in the argument. It lets you choose
one or more of: "b" (block special), "c" (character special), "d" (directory),
"f" (regular file), "l" (symbolic link), "p" (FIFO), "s" (socket).


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

PowerWalk can be used as an iterator/generator. To just get a lot of
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

You can ignore the OPEN and CLOSE events for directories (as shown here), or
turn off the `containers` option to have them not be generated at all.

The following example prints an
outline of the file directory subtree of the current directory.
The 'open' and 'close' options (both default to False), open each leaf
file for you, passing the handle back in `fh` (otherwise, `fh` is always
passed back as None), and close it on the next call to `traverse()`:

    depth = 0
    pw = PowerWalk(args.files, recursive=True, containers=True, open=True, close=True)
    pw.setOption("includeExtensions", "txt")
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

If you'd rather not hear about directory boundaries at all, do:

    pw = PowerWalk("myDir", recursive=True, containers=False)
    for itemInfo in pw.traverse():
        path, fh, _what = itemInfo
        nrecs = len(list(fh.readlines()))
        print("%6d lines in %s" % (nrecs, path))

Or you can have an exception thrown on directory start/end
(some might say that's more Pythonic):

    pw = PowerWalk("myDir", recursive=True, exceptions=True)
    while True:
        try:
            path, fh, what = pw.traverse():
            nrecs = len(list(fh.readlines()))
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

The package also supplies a few useful independent tests and methods:

* isBackup(path) -- .bak, #foo#, Backup 3 of foo, etc.
* isHidden(path) -- Initial dot.
* isGenerated(path) -- extensions like .py, .o, etc.
* getGitStatus(path) -- (used to be here, now moved to ''versionStatus.py'').


=Methods=

The main method is `traverse()`, which unfortunately comes last in the
alphabetical list below.

==__init__(self, topLevelItems=None, options:Dict=None)==

Create a PowerWalk instance, which can traverse all the specified
items. If `topLevelItems` is None, the current directory is used;
if it is a list, all the named files and/or directories will be used;
otherwise, it should be a string path to one named file or directory.

`options` is a dict of option name:value pairs. For example, to
traverse all the subdirectories of the specified items (if any),
pass `options` containing (at least) "recursive":True.
Options can also be set later using `setOption` (see below).

==addOptionsToArgparse(parser, prefix="", singletons=True)==

Add PowerWalk's options to a Python `argparse` instance.
If `prefix` is specified, it
is prefixed to each name (after the hyphens) to avoid name conflicts.
If `singletons` is True, this will include single-character synonyms.
Currently that's just `-r` for `--recursive`.


==getOption(self, name)==

Return the value of an available option (see ''setOption'').

==isBackup(path) [static]==

Test whether the given file's name indicates it is a backup, spare copy,
duplicate, or similar file. This method knows
quite a few naming conventions, but surely not all (for example, OS conventions
such as "backup of" presumably localize). For example, filenames that:

* start or end with tilde or pound-sign

* have extension "bak" or "bck"

* match r"^(backup|copy) (\\(?\\d+\\)? )?of"

* match r"\\b(backup|copy|bak)\\b" (but in these cases a warning is
issued unless ''--quiet'' is in effect).

* Mac OS X "Duplicate" does `foo.txt` -> `foo copy.txt` -> `foo copy 2.txt`

* emacs backups append "~" or "~\\d+~" to the filename
For relevant emacs settings, see
[https://stackoverflow.com/questions/151945]).

* emacs auto-save files put "#" at start and end of filename (but
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

    n = pw.getStat("regular")

gets you the total number of regular (non-dir, non-tar, non-ignored....) items
that have been returned so far.

The statistics include the number of files of each of these kinds:
    * backup: apparent backup files
    * directory
    * gzip
    * hiddenDir: directories that were skipped
    * hiddenFile: files that were skipped
    * regular
    * tar
    * tarSubdir: subdirectories inside tar files

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
    * ignoredBackups: Due to being an apparent backup file.
    * ignoredByExclExtensions: The file extension was excluded.
    * ignoredByExclNames: The file name was excluded.
    * ignoredByExclPaths: The file path was excluded.
    * ignoredByInclExtensions: The file extension was included.
    * ignoredByInclNames: The file name was included.
    * ignoredByInclPaths: The file path was included.
    * ignoredByMinDepth: Files found at too shallow nesting depth.
    * ignoredHiddens: Due to having a dot-initial name.
    * ignoredSamples: Due to `--sampleFactor`.


=======

==setOption(self, name, value)==

Change the value of an available option. Options can also
be set on the constructor via like-named keyword options, or en masse
using ` addOptionsToArgparse()` and `applyOptionsFromArgparse()`.
''Note'': There are a few more options that are not part of
the PowerWalk class, but are available when this script is run standalone.
They are described in the full list of options at the end of this help.


===File selection options===

''Note'': Regexes given for these options (where applicable), do not
automatically have "^" and "$" added. They match if they match anywhere
in the string. You can of course add one or both of those metacharacters
explicitly to the option value.

* "backups": Include `.bak` and similar files? Default: False.

* "excludeExtensions": Regex for item extensions not to allow. Default: "".
See also ''includeExtensions''. As with `grep` and many other
tools, exclusions override inclusions if both apply to the same file.
The "or" operator ("|") is allowed in the regex, which is an easy
way to exclude (or include) multiple extensions.

* "excludeFileInfos": Regex for `file` command results not to allow. Default: "".
See also ''includeFileInfos''.

* "excludeNames": Regex for item basenames not to allow. Default: "".
This matches against the names ''without'' any extension.
See also ''includeNames''.

* "excludePaths": Regex for paths not to allow. Default: "".
See also ''includePaths''.

* "hidden": Include hidden (.-initial) files '''and''' directories.
This option differs from most other file selection options, in that it
affects directories. This is to address things like excluding `.git` and the
many config directories commonly placed in home directories.
Default: False (that is, hidden items are ignored). Items under
ignored directories are '''entirely''' skipped -- their descendants are not
traversed, examined, or counted.

* "includeExtensions": Regex for (only) item extensions to allow. Default: "".
See also ''excludeExtensions''.

* "includeFileInfos": Regex to match what the *nix `file` command (q.v.) says
about the file. For example, some versions of `file` return descriptions like:

    ** POSIX shell script text executable, ASCII text
    ** directory
    ** MacOS Alias file
    ** ASCII text, with very long lines, with no line terminators
    ** XML 1.0 document text, ASCII text
    ** Python script text executable, UTF-8 Unicode text, with very long lines,
with CRLF, CR, LF line terminators, with escape sequences, with overstriking
    ** Debian binary package (format 2.0), with control.tar.gz, data compression xz

* "includeNames": Regex for (only) item basenames to allow. Default: "".
This matches against the names ''without'' any extension.
See also ''excludeNames''.


===Container and similar options===

* "followLinks": How to treat *nix symbolic
links: IGNORE, RETURN, or FOLLOW.
This does not include Mac "aliases", Windows "shortcuts", weblocs, etc.

* "followWeblocs": How to treat MacOS .webloc files (which basically just
encapsulate a URL): IGNORE, RETURN, or FOLLOW. For FOLLOW, the file will
be fetched, saved in the directory specified by the `--tempFileDir` option,
and returned as if it had been local.

* "openGzip": If True (the default), `gzip` files will be opened as if they were
directories, and the individual items within them will be returned.

* "openTar": If True (the default), `tar` files will be opened as containers
(optionally generating PWType.OPEN and PWType.CLOSE events),
and the individual items within them will be returned.


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

* `absolute`:  Always map returned paths to absolute form.

* `containers` (default True): If True,
then open and close events will be generated
for each container (such as a directory, gzip, or tar file) that is entered.
The third member of the returned tuple (`what`) is PWType.OPEN and
PWType.CLOSE, respectively.

* `dirsSeparate`: "dirs": sort directories before files;
"files": sort files before directories; "mix": leave them intermixed (default).

* `exceptions` (default False): If True, then containers (and ignorable
files (if `ignorables` is also set) will be signaled by raising exceptions
rather than returning regular events. The exceptions will be of types
ItemOpening, ItemClosing, and ItemIgnorable.

* `ignorables` (default False): If True, then events will be generated
even for items (containers and leaves) that are filtered out -- such as
hidden files or directories, etc. Such events will have `what`
returned as PWType.IGNORE.

* `maxDepth` (default 0 (unlimited)): Do not recurse deeper than this.

* `maxFiles` (default 0 (unlimited)): Stop after returning this many
files (events for ignorable
items do not count).

* `maxSize`

* `minDepth`

* `minSize`

* `notify`: Display a message as each new file starts. Default: False

* `recursive` (default False): Traverse through subdirectories?

* `reverseSort`: Sort in opposite order.

* `sampleFactor` (default: 100.0): Include only this % of the eligible files.
If set to a value above 0.0 and below 100.0, each leaf item that would have
been returned, has only this % change of actually being returned.
Others are reclassified as ignorable. The result will only
amount to approximately the requested percentage.

* `sort`: Sort the items in each directory in the specified way
(see also `--reverseSort` and `--dirsSeparate`).
Default: "none" (just use whatever `os.listdir` returns). Other choices:

** `name`:  sort by filename
** `iname`: sort by filename, ignoring case.
** `atime`: file access time
** `ctime`: file creation time
** `mtime`: file modification time
** `size`: File length in bytes
** `ext`: Extension as returned by `os.path.splitext`

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

* --excludeExtensions doesn't work.

* If you specify -r --type f, it fails to recurse.

* If you don't specify -r, it won't even list a directory that's specified
at the very top level. Currently, I've hacked it so that directories that
are specified directly, at the top level, are always recursed into
regardless of the setting of `--recursive`. I'm not certain what the ideal
behavior is:

** `ls` (unless you set `-d`) lists content for all directories specified directly.
** `ls -d -r` seems to not recurse at all.
** `ls *" lists all the files, ''then'' all the directories with their files.

* Default indented list unindents some files, and/or fails to display
directory events.

* `--exec` is still experimental, and related `find` options like `--execdir`
are not there at all.

* The script will warn if it can't find all the file-format libraries
installed (for tar, gzip, etc.),
but it will work fine as long as you don't specifically need the missing ones.

* For command-line use, there are options for whether/how to quote filenames.
But escaping the specified quote character(s) is rudimentary.
Specifically, it messes up multi-character quotation marks,
and it can only backslash.

* I've used this almost exclusively for reading (for example, picking
out just the desired files from an NLP corpus like OANC or MASC). Writing
is not yet thoroughly tested. I imagine writing doesn't work well for container
files (tar, gzip, etc.).

* Statistics of the current run as well as the current
nesting depth of the traversal (in `.depth`) are separated into a
`TraversalState` object. A reference to that object is
kept directly in the PowerWalk object instance as `PowerWalk.travState`.
So if you try to run two traversals from the same PowerWalk instance, you may
have problems accessing them via PowerWalk. However, PowerWalk
itself doesn't use it, so it should be ok. It's really only stored there
so command-line usage can display statistics at the end.
That won't work if you modify it to run a second
`PowerWalk.traverse()` before printing statistics that way. If you create two
separate PowerWalk instances in such cases, you should be fine.

* You can only specify one regex for each of the include/exclude options
that take regexes. These options do not apply to directories (ideally, they
should be separately settable for directories and files (and maybe other containers).

* The protection against circular links is unfinished.


=To do=

==Most wanted==

* At top level, if it's a dir then issue an open event for it, and
make sure we get all it's children. *******

* Option to not report dirs (probably just apply `--type` f to main.

* Protect against circular links.

* Be able to accept/return Path objects.

* Add move/link/cat similar to `--copyTo`, and support setting
xattr to say where copied from.

* Support additional compression methods.

* Make a cleaner design for the various output format punctuation.

* Plain indented ls doesn't indent first dir name?

==Output options==

* Replace `--absolute` with a choice of normalized, real, rel, or abs?
* Enhance `--serialize` to support pulling in ancestor dir names,
like `renameFiles`. Perhaps, port and integrate `renameFiles`?
* Add `ls`-like and `stat`-like (cf PowerStat.py) displays?
Integrate PowerStat for output formatting.
* Displayed lines for open/close can't be entirely omitted via `--oformat`.
* Option to write directory outline in HTML.
* Rsync-like option: but just use system cp, and only if newer/differentSize....
* With --copy or --sync, construct isomorphic tree instead of copying all to
a single target (limit to one input dir?).
* way to colorize files by variuos criteria (say, by using the `file` command
to differentiate Perl vs. Python)
* Change --count to be like grep --count.
* Add -f to do ls -f effect.

==Filter / file selection options==

* Possibly, way to exclude a dir but then override to include certain subs?
* Consolidate filter options to be more like rsync?
    --filter [rel][what] /pattern/
    rel  ::= include|exclude|+|-|<=>|
    what ::= name|path|ext|info|
           | cre|mod|acc|inodeCre
* Add option to return *only* dirs (or containers?)
* Option to block traversal into .apps, .dmg, etc.
* Option to specify a file like .gitignore or .dockerignore, specifying
file patterns to exclude (or maybe to specify options in general)?
* Perhaps add --name, --iname, --path, --ipath that match globs instead of
regexes, for `find` compatibility?
See discussion of Python `fnmatch` in
[https://stackoverflow.com/questions/27726545/], or pathlib, or PurePAth.match().
* Add `--files-without-match` and `--files-with-matches` like `grep`.
* permissions -- see `passesPerm()` below.
* owner and group ids (and none), inum -- cf `PowerStat.py`
* file-flags like for `find -flags`, `chflags`, 'ls -F'; or circled chars?
* Mac fs metadata (kmdItem... and all that). See my `macFinderInfo`.
* Option to not cross device or filesystem bounds (see `find -x`)
* distinguish maxfiles tried vs. succeeded
* Dates and times (options have been added, but don't do anything yet)
    -amin n:  modified n minutes ago (rounded up)
    -atime n[smhdw] modified n (default days) ago. Can do `-1h30m`.
    -anewer
    (likewise with -c... for ctime, -m... for mtime, -B... inode creation)
    -newer [file]: if newer mod than [file
    -newerXY [file]]: if newer [aBcm] than [file]'s [aBcM].
* depth
* Ones that require a comparison type:
    ** atime, ctime, mtime, mindepth, cf Bmin [aBcm]?(newer|time|min)
    ** depth
    ** newer/old cre/mod/acc time vs. specified file
    ** date, age, and file size (chars, bytes, blocks, kmgtp), file count.
    *** including MIME "Date:" for email files
* Is under git or other version-control (and maybe, is committed/pushed?)
See getGitStatus().  Not yet integrated.
* Add specific support for .gitignore and cvs equivalent.

What do various *nix utilities do for <=> tests in options?
* empty
* exec(dir)
* group/nogroup, user/nouser/uname/uid/
* -print0
* "i" prefix for specific tests
* -xattr, -xattrname (and xattr k op v)
* negation and maybe booleans?
* --files-with-match, --files-without-match (repeatable?)
* Review `rsync` for useful selection options (say, git-exclude, cvs-exclude?)

==Other options==

* Make --include* --exclude* repeatable. Should they mean union or intersection?
* Option to sniff encoding rather than set globally?
* Limit max/min/total size of files
* Support Mac aliases, bookmarks, and webloc files.
See my `resolveLinks` attempt, and [https://pypi.org/project/mac_alias/].
See [https://stackoverflow.com/questions/48862093]
(how-to-read-change-and-write-macos-file-alias-from-python),
[http://mac-alias.readthedocs.io/en/latest] and
[https://docs.python.org/2/library/macostools.html].
* Support URLs?
* Sampling of every nth file, first n from each directory, etc.

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


=Related commands=

`find` + `-exec` does a really nice job of finding things.
PowerWalk is mainly intended to be easier to use
from Python code, especially for people (like corpus linguists) who work with
tons of sample files in complicated directory and container structures.

[https://github.com/sderose/FileManagement/lss],
[https://github.com/sderose/FileManagement/findIdenticalFiles].

[https://github.com/sderose/FileManagement/lsoutline] produces a file listing
similar to what PowerWalk produces
when run from the command line. But you can do fancier selection here (that
script may be upgraded to just use PowerWalk underneath).


=References=

See [../FileSelectionOptionsOfNixCommands.md] for a survey of what different
*nix command provide for file-selection, sorting, format support, etc.


=History=

* 2006-06-07: `countTags.py` written by Steven J. DeRose, with some similar options.
* 2018-04-21: `PowerWalk.py` split out of `countTags.py`.
* 2020-06-10: New layout. Static methods.
* 2020-08-28ff: Add exception-based directory/error event handling. Lint.
* 2020-09-01: Add `namedtuple` PWFrame as what to return. Add Enum
`PWType` for what kind of thing is being returned. Reorganize options
into categories in help and where listed in code. Add `--exceptions`
and several new filtering options, type-check them.
Refactor event generation, item stack, and statistics into TraversalState class.
* 2020-09-15: Fix several bugs in filtering, improve reporting and
option-setting. Add `--includeFileInfos` and `--excludeFileInfos`.
* 2020-10-06: Fix `--includeNames`, make it and `--excludeName` use extension.
Add `--copyTo` and `--serialize`.
* 2020-10-09: Add `--exex`.
* 2020-10-14: Improve how topLevelItems are passed and defaulted.
Clean up `errorEvents` options vs. `errors` statistic.
* 2020-10-20f: Add `--type` similar to *nix `find`. Fix depth counting.
* 2020-11-24: Add `--no-recursive`. Make exceptions subclass of a cover type.
Add `--reverseSort` and clean up sorting. Make top-level dirs always recurse.
* 2021-01-11: Fix quote escaping bug.
* 2021-03-09: Add `--serializeFormat`, and file-time options (latter are not
operational yet).
* 2021-04-09: Sync competing changes. Add `--dirsSeparate`.
* 2021-04-19: Hook up `--perm` to start testing.
Filter by git status. More option re. symlinks, start Mac .webloc support.
Improve doc, typehints, etc. Track inodes of directories to try to protect
against circular symlinks.
* 2022-02-14: Normalize quotes. Add --fileType.
* 2022-03-23: Improve output format quoting options.
* 2022-07-05: Start breaking out a cleaner listing i/f via classes ItemFmt, Lister...
* 2023-11-27: Refactor main, OutputFormatter. Drop ItemFmt.
Rename --filetype to --fileTypeFlag and alias -F. Add alias -R for recursive.
* 2023-12-01: Let --type and --gitStatus take multiple letters.

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
def isStreamable(x) -> bool:
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
# The "exceptions" option signals directory start/end by raising exceptions.
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
#
class PWType(Enum):
    """These are the types of events that are stored as the third item in
    PWFrame objects (see next section), which are kept on the TraversalState
    stack during active traversals.
    """
    OPEN    = 1          # The beginning of a directory, tar file, etc.
    CLOSE   = 2          # The end of a directory, tar file, etc.
    IGNORE  = 3          # Notification of a filtered-out object
    LEAF    = 4          # An actual readable/writable object
    ERROR   = -1         # Generic error
    MISSING = -2         # Specific error, item not found

class PWDisp(Enum):
    """Choices of what to do with links, such as *ix symlinks, Mac aliases,
    Mac .weblocs, etc.
    """
    IGNORE = 0
    RETURN = 1
    FOLLOW = 2


###############################################################################
# PWFrame bundles the stuff you need to know in each entry on the "travState"
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
#  .inode is the inode number. This is kept because symblinks can make
#     circles. Yes, it happened to me. Thanks, Valve.
#
PWFrame = namedtuple("PWFrame", [ "path", "fh", "what", "inode" ])

def isPWFrameOK(ts:PWFrame) -> bool:
    if (not isinstance(ts.path, str)):
        warning(0, "Bad PWFrame.path: %s." % (type(ts.path)))
        return False
    if (ts.fh is not None and not isStreamable(ts.fh)):
        warning(0, "Bad PWFrame.fh: %s." % (ts.fh or "[None]"))
        return False
    if (not isinstance(ts.what, PWType)):
        warning(0, "Bad PWFrame.what: %s." % (ts.what))
        return False
    if (not isinstance(ts.inode, int)):
        warning(0, "Bad PWFrame.inode: %s." % (ts.inode))
        return False
    return True


###############################################################################
#
class TraversalState(list):
    """Instantiate for each traversal.
    This object is passed down the recursive traversal.
    The main (list) content is a stack of PWFrame namedtuples, which in turn
    consists of [ "path", "fh", "what", "inode" ].

    It has methods that do "the right thing" when called for an item
    confirmed as an OPEN, CLOSE, LEAF, IGNORE, or ERROR (based on the
    options in effect, a reference to which is passed to the constructor).
    """
    def __init__(self, options:Dict):
        super(TraversalState, self).__init__()
        self.depth = 0
        self.iString = "    "
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
            "ignoredByExcludeFileInfos"  : 0,
            "ignoredByIncludeExtensions" : 0,
            "ignoredByGitStatus"         : 0,
            "ignoredByIncludeNames"      : 0,
            "ignoredByIncludePaths"      : 0,
            "ignoredByIncludeFileInfos"  : 0,
            "ignoredByExcludeDir"        : 0,
            "ignoredByIncludeDir"        : 0,

            "ignoredByMinDepth"          : 0,
            "ignoredByPerm"              : 0,
            "ignoredByType"              : 0,
        }

    def getStats(self, showZeroes=True) -> str:
        """Generate a displayable list of the statistics.
        """
        buf = "\nItems processed:\n"
        for k in sorted(self.stats.keys()):
            if (showZeroes or self.stats[k]>0):
                buf += "    %-30s %8d\n" % (k, self.stats[k])
        return buf

    def getStat(self, name:str) -> int:
        return self.stats[name]

    def bump(self, name:str, n=1) -> None:
        """Increment a named statistic.
        """
        if (name not in self.stats):
            raise ValueError("No stat named '%s'." % (name))
        self.stats[name] += n

    def indent(self) -> str:
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
    def openContainer(self, path:str, fh:object, inode:int=0) -> Union[PWFrame, None]:
        """Create and push a stack frame for the thing we found.
        Files that are filtered out don't even get here. But for containers,
        we mightgenerate events or excpetions (see options["containers")
        """
        thePWFrame = PWFrame(path, fh, PWType.OPEN, inode=inode)
        assert isPWFrameOK(thePWFrame)

        self.bump("containersOpened")
        self.append(thePWFrame)
        self.depth += 1  # not thread-safe
        if (self.depth > self.stats["maxDepthReached"]):
            self.stats["maxDepthReached"] = self.depth

        warning(1, "In openContainer, containers %d, exceptions %d." %
            (self.options["containers"], self.options["exceptions"]))
        if (not self.options["containers"]):
            return None
        elif (self.options["exceptions"]):
            raise ItemOpening
        return thePWFrame

    def handleLeaf(self, path:str, fh:object) -> PWFrame:
        """Create and push a stack frame for the thing we found.
        Files that are filtered out don't even get here. But for containers,
        we mightgenerate events or excpetions (see options["containers")
        """
        warning(2, "handleLeaf: %s" % (path))
        thePWFrame = PWFrame(path, fh, PWType.LEAF, inode=0)
        assert isPWFrameOK(thePWFrame)
        self.bump("leafs")
        return thePWFrame

    def handleIgnorable(self, path:str) -> Union[PWFrame, None]:
        """Called for an ignorable item:
            * If caller doesn't want them, return None
            * If called wants them as exceptions, raise one then return None
            * Otherwise stack it, return the PWFrame, then pop it.
        Caller should do this for leaves:
            tsf = self.handleIgnorable(travState, path)
            if (tsf): yield tsf
        """
        #warning(1, "handleIgnorable: %s" % (path))
        self.bump("ignored")
        if (not self.options["ignorables"]):
            return None
        elif (self.options["exceptions"]):
            raise ItemIgnorable
        else:
            return PWFrame(path, None, PWType.IGNORE, inode=0)

    def handleError(self, path:str, message:str="Item Error",
        errorType:PWType=PWType.ERROR) -> Union[PWFrame, None]:
        """Called for missing, unopenable, etc.
        """
        warning(1, "handleError: %s" % (path))
        self.bump("errors")
        if (not self.options["errorEvents"]):
            return None
        elif (self.options["exceptions"]):
            if (errorType == PWType.MISSING):
                raise ItemMissing(message + " [%s]" % (path))
            else:
                raise ItemError(message + " [%s]" % (path))
        else:
            return PWFrame(path, None, errorType, inode=0)

    def closeContainer(self) -> Union[PWFrame, None]:
        """Called at the end of any node, whether container or leaf.
        For leafs, don't yield a separate event, just pop the stack.
        """
        warning(2, "In closeContainer, containers %d, exceptions %d." %
            (self.options["containers"], self.options["exceptions"]))
        thePWFrame = self[-1]
        self.depth -= 1  # not thread-safe
        warning(1, "closeContainer: %s" % (thePWFrame.path))
        self.pop()
        if (thePWFrame.what == PWType.OPEN):
            if (not self.options["containers"]):
                return None
            elif (self.options["exceptions"]):
                raise ItemClosing
            return PWFrame(thePWFrame.path, thePWFrame.fh or None,
                PWType.CLOSE, inode=thePWFrame.inode)
        raise IOError("Trying to close a %s" % (thePWFrame))


###############################################################################
#
class PowerWalk:
    """A class to traverse files in the file system, combining a lot of
    filtering and decoding features, drawing on many *nix commands for
    inspiration. See the features description under -h, and the utility
    to add them to argparse: addOptionsToArgparse().
    """
    typeLetters = "bcdflpsDPW"
    typeLetterExpr = r"^[" + typeLetters + r"]*$"
    gitStatuses = " MADRCU?!"
    gitStatusExpr = r"^[" + gitStatuses + r"]+"

    __optionTypes:Dict[str, Any] = {

        # Name filtering
        "excludeExtensions"   : "REGEX",
        "excludeNames"        : "REGEX",
        "excludePaths"        : "REGEX",
        "excludeFileInfos"    : "REGEX",
        "includeExtensions"   : "REGEX",
        "includeNames"        : "REGEX",
        "includePaths"        : "REGEX",
        "includeFileInfos"    : "REGEX",

        "includeDir"          : "REGEX",
        "excludeDir"          : "REGEX",

        "absolute"            : bool,
        "backups"             : bool,
        "close"               : bool,
        "containers"          : bool,
        "dirsSeparate"        : str,
        "encoding"            : str,
        "exceptions"          : bool,
        "followLinks"         : PWDisp,
        "followWeblocs"       : PWDisp,
        "gitStatus"           : str,
        "hidden"              : bool,
        "ignorables"          : bool,
        "maxDepth"            : int,            # TODO -> find-style?
        "maxFiles"            : int,            # TODO -> find-style?
        "maxSize"             : int,            # TODO -> find-style?
        "minDepth"            : int,            # TODO -> find-style?
        "minSize"             : int,            # TODO -> find-style?
        "mode"                : str,
        "notify"              : bool,
        "open"                : bool,
        "openGzip"            : bool,
        "openTar"             : bool,
        "perm"                : str,
        "recursive"           : bool,
        "reverseSort"         : bool,
        "sampleFactor"        : float,
        "sort"                : str,
        "type"                : str,
        "verbose"             : int,
    }

    def handlePathsArg(self, topLevelItems:Union[List, str]):
        if (not topLevelItems):
            return [ os.environ["PWD"] ]
        elif (isinstance(topLevelItems, list)):
            return topLevelItems
        elif (isinstance(topLevelItems, str)):
            return[ topLevelItems ]
        else:
            raise ValueError("First arg must be path, list, or None for PWD.")

    def __init__(self, topLevelItems=None, **kwargs):
        self.topLevelItems = self.handlePathsArg(topLevelItems)

        self.travState = None  # Used during traversal (not thread-safe!) TO DO

        # Datatypes for most options. A few are added algorithmically, such as
        # --newer[Bcma][aBcm] (see addTimeOptions()).
        # Options specific to the command are not included here.
        #
        self.options = {
            "excludeExtensions"   : "",
            "excludeNames"        : "",
            "excludePaths"        : "",
            "excludeFileInfos"    : "",
            "includeExtensions"   : "",
            "includeNames"        : "",
            "includePaths"        : "",
            "includeFileInfos"    : "",

            "includeDir"          : "",
            "excludeDir"          : "",

            "absolute"            : False,
            "backups"             : False,
            "close"               : False,    # Do fh.close() on leafs for user.
            "containers"          : True,     # Events for container start/end?
            "dirsSeparate"        : "MIX",    # Separate dirs vs. files in sort?
            "encoding"            : "utf-8",  # Character encoding
            "errorEvents"         : False,    # Return events for errors?
            "exceptions"          : False,    # Exception for containers?
            "followLinks"         : PWDisp.IGNORE,
            "followWeblocs"       : PWDisp.IGNORE,

            "gitStatus"           : "",
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
            "perm"                : "",       # Test permissions
            "recursive"           : False,
            "reverseSort"         : False,
            "sampleFactor"        : 100.0,    # Take everything.
            "sort"                : "",       # TODO: Test in tar, zip, etc.
            "type"                : "",
            "verbose"             : 0,
        }
        self.permOptions = []                 # Parsed version of --perm

        if (kwargs):
            for k, v in kwargs.items():
                self.setOption(k, v, strict=True)

    def getOption(self, name:str):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        return self.options[name]

    def setOption(self, name:str, value:Any, strict:bool=False) -> None:
        """Note: If the options are coming in from argparse, an unset
        list or dict will perhaps be None, so fix to an empty one.
        """
        if (name not in self.__optionTypes):
            if (strict):
                raise ValueError("Unknown option '%s'." % (name))
        elif (name == "perm"):
            self.permOptions = self.makeActions(value) if (value) else []
        else:
            theType = self.__optionTypes[name]
            if (theType == "REGEX"):
                warning(1, "setOption for '%s' to '%s' type %s." % (name, value, theType))
                if (value):
                    try:
                        self.options[name] = re.compile(value)
                    except (re.error, TypeError) as e:
                        warning(0, "Cannot compile regex for option %s: %s\n    %s" %
                            (name, value, e))
                warning(1, "    compiled to: '%s' (type %s)." %
                    (self.options[name], type(self.options[name])))
                return
            if (value is None):
                if (theType == list): value = []
                elif (theType == dict): value = {}
                elif (theType == str): value = ""
                elif (theType == bool): value = False
                elif (theType == PWDisp): value = PWDisp.IGNORE
                else: value = 0
            try:
                ###self.options[name] = theType(value)
                if (name=="verbose"):
                    global verbose
                    verbose = value
                elif (name in [ "excludeNames", "includeNames" ] and "." in value):
                    warning(0, "Option --%s '%s' won't match against extensions." %
                        (name, value))  # TODO: Check
            except (TypeError, re.error) as e:
                warning(0, "Cannot cast value '%s' for option '%s' to %s:\n    %s"
                    % (value, name, theType.__name__, e))

    def applyOptionsFromArgparse(self, argsObj=None, prefix:str="") -> None:
        """Have to ignore any that aren't ours.
        """
        for k, v in argsObj.__dict__.items():
            if (not k.startswith(prefix)):  # Not ours
                continue
            k = k[len(prefix)]
            if (k == "type" and not re.match(PowerWalk.typeLetterExpr, v)):
                warning("Unrecognized --type letter in '%s'.", v)
            if (k == "gitStatus" and not re.match(PowerWalk.gitStatusExpr, v)):
                warning("Unrecognized --gitStatus letter in '%s'.", v)
            if (k in self.options):
                self.setOption(k, v, strict=False)
        #showOptions(argsObj)

    @staticmethod
    def addOptionsToArgparse(parser, prefix:str="", singletons:bool=True):
        """Provide an easy way to add all our options to a main program's
        argparse instance. Use applyOptionsFromArgparse() after, to
        copy them back here from the argparse result, ignoring any others.
        @param prefix: Put this before all names to avoid name conflicts.
            You can include leading "--", but it will be added if not included.
        @param singletons: If set, include single-char synonyms (which, btw,
            do *not* get prefixed).
        """
        if (not prefix.startswith("-")):
            prefix = "--" + prefix

        for thing in [ "Extensions", "Names", "Paths", "FileInfos" ]:
            for sign, abbr in [ ("Include", "i"), ("Exclude", "x") ]:
                n1 = prefix + sign.lower() + thing
                n2 = prefix + sign.lower() + "-" + thing
                n3 = prefix + abbr + thing
                parser.add_argument(n1, n2, n3, type=str, metavar="R",
                help="%s items with %s matching this regex." %
                    (sign, thing.lower()))

        PowerWalk.addTimeOptions(parser, prefix=prefix)

        # And the grep-like ones
        parser.add_argument(
            prefix + "include", action="store_true",
            help="Like grep. Still experimental.")
        parser.add_argument(
            prefix + "exclude", action="store_true",
            help="Like grep. Still experimental.")
        parser.add_argument(
            prefix + "includeDir", prefix + "include-dir", action="store_true",
            help="Like grep. Still experimental.")
        parser.add_argument(
            prefix + "excludeDir", prefix + "exclude-dir", action="store_true",
            help="Like grep. Still experimental.")

        # The rest, alphabetically
        parser.add_argument(
            prefix + "absolute", action="store_true",
            help="Return paths in absolute form.")
        parser.add_argument(
            prefix + "backups", action="store_true",
            help="Include (seeming) backup items,like .bak, ~x, #x#,....")
        parser.add_argument(
            prefix + "close", action="store_true",
            help="Close leaf items when done (requires --open).")
        parser.add_argument(
            prefix + "containers", action="store_true", default=True,
            help="Generate events (or --exceptions) for container open/close.")
        parser.add_argument(
            prefix + "no-containers", action="store_false",
            dest="containers",
            help="Do not generate events (or --exceptions) for container open/close.")
        parser.add_argument(
            prefix + "dirsSeparate", type=str, default="mix",
            choices = [ "mix", "dirs", "files" ],
            help='If --sort is used, put "dirs" first, or "files", or "mix" them.')
        parser.add_argument(
            prefix + "encoding", type=str,metavar="E", default="utf-8",
            help="Assume this character set. Default: utf-8.")
        parser.add_argument(
            prefix + "errorEvents", action="store_true",
            help="Return events for errors like unopenable items.")
        parser.add_argument(
            prefix + "exceptions", action="store_true",
            help="Report container oper/close as exceptions, not events.")
        parser.add_argument(
            prefix + "followLinks", metavar="D", type=PWDisp, default=PWDisp.IGNORE,
            help="Follow *nix links to the destination.")
        parser.add_argument(
            prefix + "followWeblocs", metavar="D", type=PWDisp, default=PWDisp.IGNORE,
            help="Follow MacOS .webloc links to the destination.")
        parser.add_argument(
            "--gitStatus", "--git-status", type=str, default="",
            help="Git status letter(s) as for git -s [%s]. UNFINISHED."
            % (PowerWalk.gitStatuses))
        parser.add_argument(
            prefix + "hidden", "-a", action="store_true",
            help="Include file and directories whose names begin with dot.")
        parser.add_argument(
            prefix + "ignorables", action="store_true",
            help="Return events (or exceptions) for ignorable items.")

        parser.add_argument(
            prefix + "maxDepth", metavar="N", type=int, default=0,
            help="Do not traverse more than this many levels down.")
        parser.add_argument(
            prefix + "maxFiles", metavar="N", type=int, default=0,
            help="Do not return more than this many leaf items.")
        parser.add_argument(
            prefix + "maxSize", metavar="N", type=int, default=0,
            help="Skip files larger than this.")
        parser.add_argument(
            prefix + "minDepth", metavar="N", type=int, default=0,
            help="Do not return items fewer than this many levels down.")
        parser.add_argument(
            prefix + "minSize", metavar="N", type=int, default=0,
            help="Skip files smaller than this.")
        parser.add_argument(
            prefix + "mode", type=str, default="rb",
            choices = [ "r", "rb", "w", "wb", "a", "ab" ],
            help="Mode (read vs. write and binary). Default: rb.")
        parser.add_argument(
            prefix + "notify", action="store_true",
            help="Some extra notifications")
        parser.add_argument(
            prefix + "open", action="store_true",
            help="Open leaf items and return a readable handle.")
        parser.add_argument(
            prefix + "openTar", action="store_true",
            help="Open tar files as if they were directories.")
        parser.add_argument(
            prefix + "openGzip", action="store_true",
            help="Open openGzip files as if they were directories.")
        parser.add_argument(
            prefix + "perm", type=str, default="",
            help="Test permissions, such as +gw or -ux (experimental).")

        if (singletons):
            parser.add_argument(
                prefix+"recursive", "-r", "-R", action="store_true",
                help="Descend into subdirectories.")
        else:
            parser.add_argument(
                prefix + "recursive", action="store_true",
                help="Descend into subdirectories.")
        parser.add_argument(
            prefix + "no-recursive", action="store_false", dest="recursive",
            help="Do NOT descend into subdirectories.")

        parser.add_argument(
            prefix + "reverseSort", action="store_true",
            help="If --sort is used, reverse the order.")
        parser.add_argument(
            prefix + "sampleFactor", metavar="%", type=float, default=100.0,
            help="Sample only this percentage of eligible items.")
        parser.add_argument(
            prefix + "sort", type=str, default="none",
            choices = [ "none", "name", "iname",
                "atime", "ctime", "mtime", "size", "ext" ],
            help="Sort directory members by what? Default: none. ")

        parser.add_argument(
            prefix + "type", type=str, default="",
            help='Like the "find" command, plus Door, Port, Whiteout,'
            ' and can give multiple letters.')

        # Test that all the known options are available.
        for op in PowerWalk.__optionTypes.keys():
            if (prefix+op not in parser._option_string_actions):
                warning(0, "addOptionsToArgparse: '%s' not added.\nList is: %s." %
                    (prefix+op,
                    ", ".join(parser._option_string_actions.keys())))
                sys.exit()

        return parser

    @staticmethod
    def addTimeOptions(parser, prefix:str="") -> None:
        """Add a boatload of options for testing filetimes, based on `find`.
        """
        def timeArg(s):
            """Check validity of values for -[aBcm]time.
            (and ...min? and where's ...max?).
            Also allow absolute times via ISO 8601?
            """
            if s=="" or not re.match(r"(\d+w)?(\d+d)?(\d+h)?(\d+m)?(\d+s)?$", s):
                raise ValueError("Option requires a valid time string.")

        def fileArg(f):
            """Should there be a way to compare the file against a relative path,
            not absolute?
            """
            if (not os.path.exists(f)):
                raise ValueError("Option requires an existing file.")

        things = { "a":"access", "B":"inode creation",
            "c":"creation", "m":"modification" }
        for abbr, _txt in things.items():
            parser.add_argument(prefix + abbr + "newer", metavar="F", type=fileArg,
                help=argparse.SUPPRESS)
            # Possibly, `find` only takes an int for -xmin?
            parser.add_argument(prefix + abbr + "min", metavar="F", type=timeArg,
                help=argparse.SUPPRESS)
            parser.add_argument(prefix + abbr + "time", metavar="F", type=timeArg,
                help=argparse.SUPPRESS)
            for abbr2 in things.keys():
                parser.add_argument(prefix + "newer" + abbr + abbr2,
                    metavar="F", type=fileArg, help=argparse.SUPPRESS)

    def getStat(self, name:str):
        return self.travState.stats[name]

    def traverse(self, topLevelItems=None):
        """Use ttraverse on one or more top-level files or dirs,
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
            if (self.options["absolute"]):
                tl = os.path.abspath(tl)
            warning(1, "\n******* Starting top-level item '%s'." % (tl))
            for tsf in self.ttraverse(tl, trav):
                trav.bump("nodesTried")
                warning(2, "tried %d, max %d." %
                    (trav.stats["nodesTried"], self.options["maxFiles"]))
                if (self.options["maxFiles"] and
                    trav.stats["nodesTried"] > self.options["maxFiles"]): break
                yield tsf[0:3]
        if (self.options["exceptions"]):
            raise Finished()
        return

    def ttraverse(self, path:str, trav:TraversalState) -> Union[PWFrame, None]:
        """Recurse as needed.
        @param path: The path as accumulated down any recursion.
        """
        warning(2, "%sttraverse at '%s'" % ("  "*len(trav), path))

        if (self.options["maxDepth"] > 0 and               # MAXDEPTH REACHED
            len(trav) > self.options["maxDepth"]):
            return

        try:
            theStat = os.stat(path)
        except (FileNotFoundError, OSError) as e:
            warning(0, "Unexpected error statting '%s':\n    %s" % (path, e))
            self.travState.bump("errors")
            return False

        # filter-checking can raise FileNotFound, /OSError.
        if (not self.passesFilters(path, theStat, trav)):  # IGNORABLE FILE
            tsf = trav.handleIgnorable(path)
            if (tsf): yield tsf

        elif (not os.path.exists(path)):                   # NOT FOUND
            tsf = trav.handleError(path, "Item not found")
            if (tsf): yield tsf

        elif (os.path.isdir(path)):                        # DIRECTORY
            # Well, I found this wonder:
            #    ~/Library/Application Support/Steam/Steam.AppBundle/
            #    Steam/Contents/MacOS/Frameworks/Steam Helper EH.app/Contents/
            # which contains a symlink "Frameworks", to ../../../Frameworks.
            # TODO Check inode vs. stack to see if we're circular

            trav.bump("directory")
            self.recordEvent(trav, "directory")
            # If a dir was specified explicit at the top level, that seems
            # special, and we should look in it (at least for things like
            # ".", and counting files. But always? not sure.
            #
            if (not self.options["recursive"]
                and trav.depth > 0):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                tsf = trav.openContainer(path, fh=None, inode=theStat.st_ino)
                warning(1, "Opening dir '%s' (tsf %s)." % (path, tsf))
                if (tsf): yield tsf
                children = os.listdir(path)
                if (self.options["sort"]):
                    children = self.chSort(
                        path, children, self.options["reverseSort"])
                for ch in children:
                    chPath = os.path.join(path, ch)
                    for chFrame in self.ttraverse(chPath, trav):
                        yield chFrame
                tsf = trav.closeContainer()
                warning(1, "Closing dir '%s', tsf %s." % (path, tsf))
                if (tsf): yield tsf

        elif (False and tarfile.is_tarfile(path)):         # TAR FILE
            self.recordEvent(trav, "tar")
            if (not self.options["openTar"]):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                tfObject = tarfile.open(path, "r:*")
                tsf = trav.openContainer(path, fh=None, inode=theStat.st_ino)
                if (tsf): yield tsf
                for tfMember in (tfObject.getmembers):
                    if (tfMember.isfile()):
                        fh2 = tfObject.extractfile(tfMember)
                        yield trav.handleLeaf(path, fh2)
                        if (self.options["close"] and fh2):
                            fh2.close()
                    elif (tfMember.isdir()):
                        self.recordEvent(trav, "tarSubdir")
                        # TODO: add tar internal recursion!
                    else:  # also issyn, islnk, ischr, isblk, isfifo, isdev
                        warning(0, "Non-file, non-dir) in tar file.")
                tfObject.closeContainer()
                tsf = trav.closeContainer()
                if (tsf): yield tsf

        elif (path.endswith(".gz")):                       # GZIP FILE
            self.recordEvent(trav, "gzip")
            if (not self.options["openGzip"]):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            else:
                fh2 = gzip.open(path, mode=self.options["mode"],
                    encoding=self.options["encoding"])
                tsf = trav.openContainer(path, fh=None, inode=theStat.st_ino)
                if (tsf): yield tsf
                yield trav.handleLeaf(path, fh2)
                if (self.options["close"]): fh2.close()
                tsf = trav.closeContainer()
                if (tsf): yield tsf

        elif (os.path.islink(path)):                       # LINK
            disp = self.options["followLinks"]             # Weblocs
            if (disp == PWDisp.IGNORE):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            elif (disp == PWDisp.RETURN):  # TODO: Iterate?
                fh = self.openLeafIfNeeded(path)
                yield trav.handleLeaf(path, fh)
                if (self.options["close"] and fh): fh.close()
            elif (disp == PWDisp.FOLLOW):
                tgt = os.readlink(path)
                for tsf in (self.ttraverse(tgt, trav)):
                    yield tsf
            else:
                raise KeyError("Bad followLinks value %s." % (disp))

        elif (path.endswith(".webloc")):
            disp = self.options["followWeblocs"]             # Weblocs
            if (disp == PWDisp.IGNORE):
                tsf = trav.handleIgnorable(path)
                if (tsf): yield tsf
            elif (disp == PWDisp.RETURN):
                fh = self.openLeafIfNeeded(path)
                yield trav.handleLeaf(path, fh)
                if (self.options["close"] and fh): fh.close()
            elif (disp == PWDisp.FOLLOW):
                # TODO Check the PWType for this
                fh = self.fetchWebloc(path)
                yield trav.handleLeaf(path, fh)
                fh.close()
            else:
                raise KeyError("Bad followWeblocs value %s." % (disp))

        elif (self.options["sampleFactor"] < 100 and       # NON-SAMPLE
            random.random()*100.0 > self.options["sampleFactor"]):
            tsf = trav.handleIgnorable(path)
            trav.bump("ignoredSamples")
            if (tsf): yield tsf

        else:                                              # SELECTED FILE
            fh = self.openLeafIfNeeded(path)
            yield trav.handleLeaf(path, fh)
            if (self.options["close"] and fh): fh.close()

        return

    def openLeafIfNeeded(self, path:str):
        if (not self.options["open"]):
            fh = None
        else:
            fh = codecs.open(path, mode=self.options["mode"],
                encoding=self.options["encoding"])
        return fh

    def passesFilters(self, path:str, theStat:os.stat_result, trav:TraversalState) -> bool:
        """Check the file at "path" against all the filters, and
        return True iff it's one the user wants. 'hidden' applies to
        containers (such as directories) and to leafs (such as files).
        Most other filters apply only to one or the other.
        """
        if (not os.path.isdir(path)):
            return self.filePassesFilters(path, theStat, trav)
        # For directories, we have to avoid circularity:
        newInode = theStat.st_ino
        if (newInode):
            for ancPWFrame in self.travState:
                if (ancPWFrame.inode != newInode): continue
                self.travState.bump("errors")
                warning(0, "Directory 'tree' has cyclic link at %s. Skipped." % (path))
                return False
        return self.dirPassesFilters(path, theStat, trav)

    def dirPassesFilters(self, path:str, _theStat:os.stat_result, trav:TraversalState) -> bool:
        if (self.options["type"] and "d" not in self.options["type"]):
            self.recordEvent(trav, "ignoredByType")
            return False
        # ignoredByPerm ??
        if (not self.options["hidden"] and isHidden(path)):
            self.recordEvent(trav, "hiddenDir")
            return False
        if (self.options["excludeDir"] and
            re.search(self.options["excludeDir"], path)):
            self.recordEvent(trav, "ignoredByExcludeDir")
            return False
        if (self.options["includeDir"] and
            not re.search(self.options["includeDir"], path)):
            self.recordEvent(trav, "ignoredByIncludeDir")
            return False
        self.recordEvent(trav, "directory")
        return True

    def filePassesFilters(self, path:str, theStat:os.stat_result,
        trav:TraversalState) -> bool:
        """Test most of the file-filtering conditions.
        Return True only if the all pass (reaching the final "else").
        """
        _, tail = os.path.split(path)
        (_, extPart) = os.path.splitext(tail)
        extPart = extPart.strip(". \t\n\r")

        warning(1, "Checking filters for '%s', ext '%s' (exclExt '%s')." %
            (tail, extPart, self.options["excludeExtensions"]))

        passes = False  # Assume the worst for now...

        if (not self.passesType(path, theStat)):
            self.recordEvent(trav, "ignoredByType")
        elif (self.permOptions and
            not self.passesPerm(path, theStat, self.permOptions)):
            self.recordEvent(trav, "ignoredByPerm")
        elif (len(trav)<self.options["minDepth"]):
            self.recordEvent(trav, "ignoredByMinDepth")
        elif (not self.options["hidden"] and isHidden(path)):
            self.recordEvent(trav, "hiddenFile")

        elif (self.options["excludeExtensions"] and
            re.search(self.options["excludeExtensions"], extPart)):
            self.recordEvent(trav, "ignoredByExcludeExtensions")
        elif (self.options["includeExtensions"] and
            not re.search(self.options["includeExtensions"], extPart)):
            self.recordEvent(trav, "ignoredByIncludeExtensions")

        elif (self.options["gitStatus"] and
            getGitStatus(path) not in self.options["gitStatus"]):
            self.recordEvent(trav, "ignoredByGitStatus")
        elif (self.options["excludeNames"] and
            re.search(self.options["excludeNames"], tail)):
            self.recordEvent(trav, "ignoredByExcludeNames")
        elif (self.options["includeNames"] and
            not re.search(self.options["includeNames"], tail)):
            self.recordEvent(trav, "ignoredByIncludeNames")
        elif (self.options["excludePaths"] and
            re.search(self.options["excludePaths"], path)):
            self.recordEvent(trav, "ignoredByExcludePaths")
        elif (self.options["includePaths"] and
            not re.search(self.options["includePaths"], path)):
            self.recordEvent(trav, "ignoredByIncludePaths")
        elif (self.options["excludeFileInfos"] and
            re.search(self.options["excludeFileInfos"], getFileInfo(path))):
            self.recordEvent(trav, "ignoredByExcludeFileInfos")
        elif (self.options["includeFileInfos"] and
            not re.search(self.options["includeFileInfos"], getFileInfo(path))):
            self.recordEvent(trav, "ignoredByIncludeFileInfos")

        elif (not self.options["backups"] and isBackup(path)):
            self.recordEvent(trav, "backup")
        else:
            self.recordEvent(trav, "regular")
            passes = True

        warning(2, "%s filter: %s" % ("PASS" if passes else "FAIL", tail))
        return passes

    def passesType(self, _path:str, theStat:os.stat_result) -> bool:
        """Test like "find -type", return if it's ok.
        """
        mode = theStat.st_mode
        ty = self.options["type"]
        if (not ty):
            return True

        if ("b" in ty and stat.S_ISBLK(mode)): return True  # block special
        if ("c" in ty and stat.S_ISCHR(mode)): return True  # character special
        if ("d" in ty and stat.S_ISDIR(mode)): return True  # directory
        if ("f" in ty and stat.S_ISREG(mode)): return True  # regular file
        if ("l" in ty and stat.S_ISLNK(mode)): return True  # symbolic link
        if ("p" in ty and stat.S_ISFIFO(mode)): return True # FIFO
        if ("s" in ty and stat.S_ISSOCK(mode)): return True # socket

        # Python ones that go beyond "find -type" -- but mypy complains,
        # and I'm not sure yet what the issue is with those and the S_IF analogs.
        #if ("D" in ty and theStat.S_IFDOOR): return True
        if ("P" in ty and theStat.S_IFPORT): return True   # Port
        if ("W" in ty and theStat.S_IFWHT):  return True   # whiteout
        return True

    def passesPerm(self, _path:str, theStat:os.stat_result, permOptions:list) -> bool:
        """Check the file's permission and related bits, against the
        specs provided in the option, as parsed earlier by makeActions.
        @param direction: "-" requires it to be off; "+" on.
        """
        #theActions = self.makeActions(perm) # Done in setOption().
        #s = os.stat(path)
        for direction, mask in permOptions:
            if (direction == "-"):
                if (theStat.st_mode & mask): return False
            elif (direction == "+"):
                if not (theStat.st_mode & mask): return False
            else:
                raise ValueError("Huh?")
        return True

    maskValues = {
       "us": int("04000", 8),  # (the setuid bit).
       "gs": int("02000", 8),  # (the setgid bit).
       "t":  int("01000", 8),  # (the sticky bit).
       "ur": int("00400", 8),  # read by owner.
       "uw": int("00200", 8),  # write by owner.
       "ux": int("00100", 8),  # execution (for dirs, search) by owner.
       "gr": int("00040", 8),  # read by group members.
       "gw": int("00020", 8),  # write by group members.
       "gx": int("00010", 8),  # execution (for dirs, search) by group members.
       "or": int("00004", 8),  # read by others.
       "ow": int("00002", 8),  # write by others.
       "ox": int("00001", 8),  # execution (for dirs, search) by others.
    }

    @staticmethod
    def makeActions(perm:str) -> list:
        """Parse a --perm argument(s?) to a list of atomic (single-bit) changes,
        each a 3-tuple of (who, op, perm).

        "find" takes: -perm [-|+]mode
            where mode can be octal or like chmod.

        If the mode is octal, only bits 07777
        For -mode, it's true if at least all of the
            bits in the mode are set in the file's mode bits.
        For +mode, it's true if any of the bits are set.
        Otherwise, it's true if the bits exactly match the file's mode bits.

        The symbolic mode is described by the following grammar:
           mode         ::= clause [, clause ...]
           clause       ::= [who ...] [action ...] action
           action       ::= op [perm ...]
           who          ::= a | u | g | o
           op           ::= + | - | =
           perm         ::= r | s | t | w | x | X | u | g | o

        X is x if the item is a directory or had any x to start with (+ only).

        Thus:  ugo+rwx,o-x set all 9 main bits on, then turns off other write.
        Here, though, we're just testing, not changing, so we need to know
        which direction to test (op), and what mask to use.

        For example, "ug+rw a-x" becomes this, but with the actual mask
        value for the right bit in the second slot (see dict above).
        [
            ( "+", "ur" ),
            ( "+", "uw" ),
            ( "+", "gr" ),
            ( "+", "gw" ),
            ( "-", "ux" ),
            ( "-", "gx" ),
            ( "-", "ox" ),
        ]

        Order matters, because later settings can override earlier ones.

        chmod also has settings for ACLs (access control lists).
        """
        warning(1, "makeActions for arg '%s'." % (perm))
        try:
            return [ int(perm, 8) ]
        except ValueError:
            pass

        whoCodes = "augo"
        opCodes = "-+="
        permCodes = "rstwxXugo"
        clauseExpr = r"([%s]+)([%s][%s]+)" % (whoCodes, opCodes, permCodes)

        actions = []
        for clause in (re.split(r",\s*", perm)):
            mat = re.match(clauseExpr, clause)
            if (not mat):
                raise ValueError("Unknown perm code '%s' (regex r'%s')." %
                    (clause, clauseExpr))
            who = mat.group(1)
            curAct = "+"
            for tok in re.split(r"([-+=])", mat.group(2)):
                if (tok in opCodes):
                    curAct = tok
                else:
                    for pcode in tok:
                        whoExpanded = who.replace("a", "ugo")
                        for w in whoExpanded:
                            actions.append(
                                (curAct, PowerWalk.maskValues[w+pcode]))
        return actions

    def chSort(self, curPath:str, chList:list, reverse=False) -> list:
        """Sort a file-list returned from os.listdir somehow.
        """
        warning(2, "Sorting by '%s'." % (self.options["sort"]))
        if (self.options["sort"] == "none"):
            return chList

        sby = self.options["sort"]
        if (self.options["dirsSeparate"] == "mix"):
            return self.doTheSort(
                curPath, chList, sortBy=sby, reverse=reverse)

        chDirList = []
        for i in reversed(range(len(chList))):
            if (os.path.isdir(os.path.join(curPath, chList[i]))):
                chDirList.append(chList[i])
                del chList[i]
        chList = self.doTheSort(
            curPath, chList, sortBy=sby, reverse=reverse)
        chDirList = self.doTheSort(
            curPath, chDirList, sortBy=sby, reverse=reverse)
        if (self.options["dirsSeparate"] == "dirs"):
            chDirList.extend(chList)
            return chDirList
        elif (self.options["dirsSeparate"] == "files"):
            chList.extend(chDirList)
            return chList
        else:
            raise KeyError("Unknown value '%s' for --dirsSeparate." %
                (self.options["dirsSeparate"]))

    def doTheSort(self, curPath:str, chList:list, sortBy:str, reverse=False) -> list:
        #pylint: disable=C3001
        if (sortBy == "name"):
            theLambda = None
            #chList.sort()
        elif (sortBy == "iname"):
            theLambda = lambda x: x.lower()
        elif (sortBy == "atime"):
            theLambda = lambda x: getatime(os.path.join(curPath, x))
        elif (sortBy == "ctime"):
            theLambda = lambda x: getctime(os.path.join(curPath, x))
        elif (sortBy == "mtime"):
            theLambda = lambda x: getmtime(os.path.join(curPath, x))
        elif (sortBy == "size"):
            theLambda = lambda x: getsize(os.path.join(curPath, x))
        elif (sortBy == "ext"):
            theLambda = lambda x: splitext(os.path.join(curPath, x))[1]
        else:
            raise ValueError("Unknown sort method '%s'." % (sortBy))
        chList.sort(key=theLambda, reverse=reverse)
        return chList

    def recordEvent(self, theStack:list, thing:str) -> None:
        """Count the kind of thing, and maybe say something.
        """
        self.travState.bump(thing)
        if (len(theStack) == 0):
            warning(2, "%s  Trying: empty stack (%s)" %
                ("  "*len(theStack), thing))
            return
        if (self.options["notify"]):
            frame = theStack[-1]
            warning(2, "Trying %s: '%s' (cont=%s)" %
                (thing, frame.path, frame.what))
        return

    #import io
    def fetchWebloc(self, path:str) -> io.StringIO:
        with codecs.open(path, "rb", encoding="utf-8") as wfh:
            xml = wfh.read()
        mat = re.match(r"<string>(.*?)<string>", xml)
        if (not mat):
            raise ValueError("Can't find URL in %s." % (path))
        buf = io.StringIO()
        buf.write(str(check_output([ "curl", mat.group(1)])))
        return buf


###############################################################################
# Generic filename tests.
#
# See also diffDirs.py, findDuplicateFiles, lss, renameFiles.
#
def isBackup(path:str, descendants=False) -> bool:
    """Given a path, check the basename for whether it's a backup file.
    If "descendants" is set, also count if a containing dir name has "backup".

    Conventions vary, we catch quite a few, such as:
        foo.txt.bak
        #foo.txt#
        #foo#.txt
        ~foo.txt~
        Backup (\\d+) of foo.txt           -- Mac OS
        Copy (\\d+) of foo.txt             -- Mac OS
        foo.txt backup( \\d*)
        foo.txt (2020-09-15 13-34-38-374) -- bbedit backup convention

    Should anything with r"\\bbackup\\b" at all, count?
    TODO: Perhaps add option for user to pass additional regex?
    TODO: Do we need something for temp files? /tmp..., .tmp, .temp...?
    TODO: Call this from other utils that need it...

    """
    bbeditDate = r" \(\d\d\d\d-\d\d-\d\d \d\d-\d\d-\d\d-\d+\)$"
    b = os.path.basename(path)
    root, ext = os.path.splitext(b)
    keywords = r"(backup|copy)"
    if (not b): return False
    if (b[0] in "~#" or b[-1] in "~#"): return True
    if (ext == "bak"): return True
    if (re.search(keywords + r"\b( \d+)?( of)\b", root, re.IGNORECASE)):
        return True
    if (re.search(r"\b(backup|copy|bak)\b", root, re.IGNORECASE)):
        return True
    if (descendants and re.match(r"\bbackups?\b", path)):
        return True
    if (re.match(bbeditDate, path)):
        return True
    return False

def isHidden(name:str) -> bool:
    """Given a path, check the basename for initial dot.
    """
    return os.path.basename(name).startswith(".")

def isGenerated(name:str) -> bool:
    """Is the name one that you probably don't need to archive, diff, or
    do certain other things with, since it's derived?
    """
    b = os.path.basename(name)
    gExprs = [
        r"^\.DS_Store",
        r"\.pyc$",
        r"\.so$",
    ]
    for ge in gExprs:
        if (re.search(ge, b)): return(True)
    return(False)


def getGitStatus(path:str) -> Union[str, None]:
    """See what sort of git state we're in (see `git status --help` for -s):
        " " = unmodified
        M = modified
        A = added
        D = deleted
        R = renamed
        C = copied
        U = updated but unmerged
        ? = untracked
        ! = ignored
        0 = Error

    TODO: Add a code to mean "not in a git repo at all", so user can
    treat files outside git distinctly from untracked files in git areas.
    """
    try:
        tokens = [ "git", "status", "-s", path ]
        buf = check_output(tokens)
    except CalledProcessError:
        return "0"
    if str(buf[0]) in " MADRCU?!": return str(buf[1])
    warning(0, "Unknown code '%s' from git status -s '%s'." % (str(buf[0]), path))
    return None

def getFileInfo(path:str) -> str:
    """See what the "file" command has to say about something...
    """
    buf = check_output([ "file", "-b", path ])
    return str(buf)

def xset(path:str, prop:str, val:Any) -> None:
    #import xattr
    warning(0, "--xattr is not yet supported for %s: %s=%s." % (path, prop, val))
    sys.exit()


###############################################################################
# TODO: Move out to separate driver.
#
if __name__ == "__main__":
    class OutputFormatter:
        """Various output formats of dir/file lists???
        Well, at least a small attempt....

        Scoping representation
            * Introducer delim before/after indent change (incl. newline, {}[]?)
            * item separator
            * The very start and end
            * final comma in aggregates
            * Representation of empty containers

        Orthogonal (?) choices?
            * Indentation
            * n per line and alignment
            * Quoting and escaping
            * # levels to show above current item
            * Type-flag characters or not
            * Abbr like ~
            * Include path components above very top?
            * added info per item (cf PowerStat)
            * LSCOLORS?
            * sorting, incl. dirs before items

        E.g.:
            /Users/
                /Users/plato/
                    /Users/plato/soc_dialogs/
                        /Users/plato/soc_dialogs/apology
                        /Users/plato/soc_dialogs/crito
                        /Users/plato/soc_dialogs/doubtful/
                            /Users/plato/soc_dialogs/doubtful/Memorabilia
                        /Users/plato/soc_dialogs/euthryphro
                    /Users/xenophon/
                        /Users/xenophon/xfiles.txt
                    /Users/zerophiles/

            /Users/
            /Users/plato/
            /Users/plato/soc_dialogs/
            /Users/plato/soc_dialogs/apology
            /Users/plato/soc_dialogs/crito
            /Users/plato/soc_dialogs/doubtful/
            /Users/plato/soc_dialogs/doubtful/Memorabilia
            /Users/plato/soc_dialogs/euthryphro
            /Users/xenophon/
            /Users/xenophon/xfiles.txt
            /Users/zerophiles/

            /Users/
                plato/
                    soc_dialogs/
                        apology
                        crito
                        doubtful/
                            Memorabilia
                        euthryphro
                xenophon/
                    xfiles.txt
                zerophiles/

            plato
                soc_dialogs
                    apology
                    crito
                    doubtful
                        Memorabilia
                    euthryphro
            xenophon/
                xfiles.txt
            zerophiles/

            JSON-ish...

            { "Users": [
                { "plato": [
                    { "soc_dialogs": [
                        "apology",
                        "crito",
                        { "doubtful": [
                            "Memorabilia"
                        ]},
                        "euthryphro"
                    ]}
                ]}
                { "xenophon": [
                    "xfiles.txt"
                ]}
                { "zerophiles": [
                ]}
             ]}

            cf https://stackoverflow.com/questions/69170524/
            {
                "Users": {
                    "plato": {
                        "soc_dialogs": {
                            "apology": Null,
                            "crito": Null,
                            "doubtful": {
                                "Memorabilia": Null
                            },
                            "euthryphro": Null
                        }
                    }
                    "xenophon": {
                        "xfiles.txt": Null
                    }
                    "zerophiles": {
                    }
                }
             }

            ("Users"
                ("plato"
                    ("soc_dialogs"
                        "apology"
                        "crito"
                        ("doubtful"
                            "Memorabilia"
                        )
                        "euthryphro"
                    )
                )
                ("xenophon"
                    "xfiles.txt"
                )
                ("zerophiles"
                )
            )

            (old HTML dir tag and server feature)

            <catalog root="/home/xyz">
                <dir name="soc_dialogs">
                    <item name="apology" />
                    <item name="crito" />
                    <dir name="doubtful">
                        <item name="Memorabilia" />
                    </dir>
                    <item name="euthryphro" />
                </dir>
                <dir name="xenophon">
                    <item name="xfiles.txt" />
                </dir>
                <dir name="zerophiles">
                </dir>
            </catalog>

            Like ls -R
            soc_dialogs:
                apology        crito
                doubtful/      euthryphro
                xenophon/      zerophiles/

            doubtful:
                Memorabilia

            xenophon:
                xfiles.txt

            zerophiles:

            SQL
            ID  Par  Name
            ---------------------
             1    0  Users
             2    1  plato
             3    2  soc_dialogs
             4    3  apology
             5    3  crito
             6    3  doubtful
             7    6  Memorabilia
             8    3  euthryphro
             9    1  xenophon
            10    9  xfiles.txt
            11    1  zerophiles

        Big issue seems to be how to differentiate
            dirs, which contain (file|dir)*, from
            items, which are atoms (wrt file system).
        You can't tell dir from file by whether it's a list or not, unless you
        do something special to distinguish empty dirs...
        """
        OFDefaults = {
            #"anonymousClose":   False,
            "openDirString":    "{ ",
            "closeDirName":     False,
            "closeDirString":   " }",
            "itemSep":          "",
            "openQuote":        "",
            "closeQuote":       "",
            "fileTypeFlag":     False,
            "iString":          "    ",
            "oformat":          "outline",
            "short":            False,
            "showInvisibles":   "literal",
        }

        def __init__(self):
            self.OFOptions = self.OFDefaults.copy()

        @staticmethod
        def addOutputFormatOptions(parser:argparse.ArgumentParser,
            prefix:str="", showHelp:bool=False) -> None:
            """Add options for how to format output, mainly filelists.
            (should become a general tree-layout class)
            """
            noHelp = False if (showHelp) else argparse.SUPPRESS
            if (not prefix.startswith("--")): prefix = "--" + prefix

            #parser.add_argument(
            #    prefix+"anonymousClose", action="store_true",
            #    help="Suppress display of container-close.")
            parser.add_argument(
                prefix+"openDirString", metavar="S", type=str, default="",
                help=noHelp or "Display after directory name on open.")
            parser.add_argument(
                prefix+"closeDirName", action="store_true",
                help="Repeat dir name before closeDirString.")
            parser.add_argument(
                prefix+"closeDirString", metavar="S", type=str, default="",
                help="Display at directory close.")
            parser.add_argument(
                prefix+"itemSep", metavar="S", type=str, default="",
                help="Put this in to separate items (e.g., a comma).")
            parser.add_argument(
                prefix+"openQuote", metavar="Q", type=str, default="",
                help="Put this before reported items (see also --quote).")
            parser.add_argument(
                prefix+"closeQuote", metavar="Q", type=str, default="",
                help="Put this after the reported paths (see also --quote).")
            parser.add_argument(
                prefix+"fileTypeFlag", "-F", action="store_true",
                help="Append a file-type indicator character, like ls -F.")
            parser.add_argument(
                prefix+"iString", metavar="S", type=str, default="    ",
                help="Repeat this string to create indentation.")
            parser.add_argument(
                prefix+"oformat", prefix+"utputFormat", prefix+"output-format",
                type=str, default="outline",
                choices = [ "plain", "outline", "json", "html", "sexp" ],
                help="Format the output in this way.")
            parser.add_argument(
                prefix+"short", action="store_true",
                help="Only show the bottom-level name in the outline view.")
            parser.add_argument(
                prefix+"showInvisibles", type=str, default="literal",
                choices=[ "literal", "octal", "hex", "pix", "url" ],
                help="How to display unusual characters.")

        def applyOutputFormatOptions(
            self, parser:argparse.ArgumentParser, prefix:str="") -> None:
            for ofoName in self.OFDefaults.keys():
                try:
                    val = getattr(parser, prefix+ofoName)
                    self.OFOptions[ofoName] = val
                except AttributeError:
                    self.OFOptions[ofoName] = self.OFDefaults[ofoName]

        def mapNamedOFOs(self, formatName:str=None) -> None:
            """Map named output format types to their consequences.
            """
            if (not formatName): formatName = self.OFOptions["oformat"]

            if (formatName == "plain"):
                self.OFOptions["openDirString"] = ""
                self.OFOptions["closeDirName"] = False
                self.OFOptions["closeDirString"] = ""
                self.OFOptions["itemSep"] = ""
                self.OFOptions["openQuote"] = ""
                self.OFOptions["closeQuote"] = ""
                #self.OFOptions["anonymousClose"] = True

            elif (formatName == "outline"):
                self.OFOptions["openDirString"] = ""
                self.OFOptions["closeDirName"] = False
                self.OFOptions["closeDirString"] = ""
                self.OFOptions["itemSep"] = ""
                self.OFOptions["openQuote"] = ""
                self.OFOptions["closeQuote"] = ""

            elif (formatName == "json"):
                warning(0, "Overriding quote settings for --oformat json")
                self.OFOptions["openDirString"] = "["
                self.OFOptions["closeDirName"] = False
                self.OFOptions["closeDirString"] = "]"
                self.OFOptions["itemSep"] = ","
                self.OFOptions["openQuote"] = '"'
                self.OFOptions["closeQuote"] = '"'
                #self.OFOptions["anonymousClose"] = True

            elif (formatName == "html"):
                warning(0, "Overriding quote settings for --oformat html")
                self.OFOptions["openDirString"] = "<ol>"
                self.OFOptions["closeDirName"] = False
                self.OFOptions["closeDirString"] = "</ol>"
                self.OFOptions["itemSep"] = ""
                self.OFOptions["openQuote"] = "<li><file>"
                self.OFOptions["closeQuote"] = "</file></li>"
                #self.OFOptions["anonymousClose"] = True

            elif (formatName == "sexp"):
                warning(0, "Overriding quote settings for --oformat sexp")
                self.OFOptions["openDirString"] = "("
                self.OFOptions["closeDirName"] = False
                self.OFOptions["closeDirString"] = ")"
                self.OFOptions["itemSep"] = ""
                self.OFOptions["openQuote"] = '"'
                self.OFOptions["closeQuote"] = '"'
                #self.OFOptions["anonymousClose"] = True

            else:
                warning(0, "Unknown output format '%s'." % (formatName))

        def makeOpenDirDisplay(self, path:str, depth:int) -> str:
            buf = self.makeIndent(depth)
            buf += path
            buf += self.OFOptions["openDirString"]
            return buf

        def makeItemDisplay(self, path:str, depth:int=0) -> str:
            buf = self.makeIndent(depth)
            buf += path
            buf += self.OFOptions["itemSep"]
            return buf

        def makeCloseDirDisplay(self, path:str, depth:int=0) -> str:
            # TODO: Way to suppress itemSep on last item in container?
            buf = self.makeIndent(depth - 1)  # TODO: Review indentation
            if (self.OFOptions["closeDirName"]): buf += path
            buf += args.closeDirString + self.OFOptions["itemSep"]
            return buf

        def makeIndent(self, depth:int=0) -> str:
            #assert depth>=0  # TODO: Fix top-level item opening...
            return(self.OFOptions["iString"] * depth)

        def makeDisplayableName(self, s:str) -> str:
            """Escape/recode invisibles as needed.
            Still have to do flag chars and quotes somewhere else.
            """
            if (self.OFOptions["short"]):
                s = os.path.basename(s)
            which = self.OFOptions["showInvisibles"]
            if (s.isalnum):
                return s
            if (which == "literal"):
                return s
            elif (which == "hex"):
                return re.sub(r"([\x01-\x20\s]",
                    lambda m: "\\u{%x}" % (ord(m.group(1))), s)
            elif (which == "url"):
                return urllib.parse.quote(s)
            elif (which == "visible"):
                return re.sub(r"([\x01-\x20\s]",
                    lambda m:chr(0x2400 + ord(m.group(1))), s)
            else:
                raise KeyError("Unknown --showInvisibles value.")

        __notQuotes__ = "]\\-"

        def quoteFilename(self, f:str, op:str='"', cl:str='"') -> str:
            """This is not as smart as it should be. For example, it will
            do weird things for multi-char quotes, and it only knows how to
            backslash.
            """
            if (op != "" or cl != ""):
                assert op not in self.__notQuotes__ and cl not in self.__notQuotes__
                try:
                    f = re.sub(r"([%s%s])" % (op, cl), "\\1", f)
                except re.error as e:
                    sys.stderr.write("Failed quoting '%s' with '%s'...'%s'.\n    %s" %
                        (f, op, cl, e))
                    sys.exit()
            return op + f + cl

        def getFlagChar(self, abspath:str) -> str:
            """Return the same single character file type flag "ls -F" would,
            to append/suffix to this item.
            NOTE: Pass the absolute path, so we can be sure to stat it right.
            ((from my PowerStat.py getFlag()))
            """
            if (not args.fileTypeFlag): return ""
            st:os.stat_result = os.stat(abspath)
            mode = st.st_mode
            if (stat.S_ISDIR(mode)):  return "/"
            # TODO: Which executable bit(s) does ls -F actually report?
            if (stat.S_ISLNK(mode)):  return "@"
            if (stat.S_ISSOCK(mode)): return "="
            if (stat.S_ISFIFO(mode)): return "|"
            # TODO: Is this not supported on MacOS or something?
            #if (stat.S_ISWHT(mode)):  return "%"
            #if (st.S_ISWHT):  return "%"
            #if (st.S_IXUSR or st.S_IXGRP or st.S_IXOTH): return "*"
            return ""


    ###########################################################################
    # Subcommands of main...
    #
    def itemList():
        pass

    def itemCopy(fromPath:str, tgtDir:str, serialFormat:str=None, serial:int=None):
        if (not os.path.isdir(tgtDir)):
            warning(0, "No directory available at '%s'." % (tgtDir))
            sys.exit()

        _, baseName = os.path.split(fromPath)
        if (serialFormat):
            baseName = serialFormat % (serial, baseName)
        warning(1, "copyTo '%s', base '%s'." % (tgtDir, baseName))
        tgtPath = os.path.join(tgtDir, baseName)
        if (os.path.exists(tgtPath)):
            warning(0, "Target already exists: %s => %s" % (fromPath, tgtPath))
        else:
            copyfile(fromPath, tgtPath)
            if (args.xattrs):
                xset(tgtPath, "kmdItemWhereFroms", "file://"+fromPath)

    def itemExec(path:str, cmd:str, magic:str="{}"):
        # TODO: Add option to change {}?
        if (magic in cmd): cmd.replace(magic, path)
        else: cmd += " " + path
        try:
            buf0 = check_output(cmd, shell=True)
            if (not args.quiet): print(buf0)
        except CalledProcessError as e0:
            warning(0, "exec failed on %s:\n    %s" % (cmd, e0))


    ###########################################################################
    # The main main...
    #
    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser:argparse.ArgumentParser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--copyTo", metavar="P", type=str,
            help="Copy chosen files to this directory (see also --serialize).")
        parser.add_argument(
            "--count", action="store_true",
            help="Just report number of dirs and files found (probably want -r, too).")
        parser.add_argument(
            "--exec", metavar="CMD", type=str,
            help='Run CMD on each selected item (like "find --exec").')
        parser.add_argument(
            "--maxBasenameLength", metavar="N", type=int, default=0,
            help="Report files only ig basename is shorter than this.")
        parser.add_argument(
            "--minBasenameLength", metavar="N", type=int, default=0,
            help="Report files only ig basename is longer than this.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--quote", action="store_true",
            help="Shorthand to set both openQuote and closeQuote to '\"'.")
        parser.add_argument(
            "--serialize", action="store_true",
            help="With --copy, add a serial number to each file.")
        parser.add_argument(
            "--serializeFormat", "--sformat", metavar="F", type=str, default="_%04d",
            help="How to format numbers for --serialize. Default: '_%%04d'.")

        parser.add_argument(
            "--showOptions", action="store_true",
            help="Display all the option values.")
        parser.add_argument(
            "--stats", action="store_true",
            help="Report overall statistics at the end.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")
        parser.add_argument(
            "--xattrs", action="store_true",
            help="With --copyTo, set xattr kmdItemWhereFroms to point back (not yet supported).")

        # Output *format* options -- TODO: make this a lot cleaner.
        #
        parser.add_argument(
            "--flat", action="store_true",
            help="One item per line, with full path (no headings like ls -R)")

        parser.add_argument(
            "--statFormat", action="store_true",
            help='Display output like "stat -f" for each file.')

        PowerWalk.addOptionsToArgparse(parser)
        OutputFormatter.addOutputFormatOptions(parser)

        # Traversal roots -- TODO: fix need for "*" with -R
        #
        parser.add_argument(
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to files, directories, containers to traverse.")

        args0 = parser.parse_args()

        if (args0.quote):  # Overridden by some following oformat values.
            args0.openQuote = args0.closeQuote = "'"

        return(args0)

    def showOptions(ap):
        warning(0, "\nOptions parsed:")
        for k in vars(ap):
            if (k.startswith("_")): continue
            v = getattr(ap, k)
            if (isinstance(v, str)): v = '"' + v + '"'
            warning(0, "    %-20s %s" % (k, v))


    ###########################################################################
    # Main
    #
    args = processOptions()
    verbose = args.verbose

    if (args.verbose > 1 or args.showOptions):
        showOptions(args)
    if (args.copyTo and not os.path.isdir(args.copyTo)):
        assert IOError("No --copyTo directory at '%s'." % (args.copyTo))

    argDict = {}
    for k0 in vars(args).keys():
        argDict[k0] = vars(args)[k0]

    cwd = os.environ["PWD"]
    if (not args.files):
        #args.files = [ os.environ["PWD"] ]
        args.files = os.listdir(os.environ["PWD"])

    of = OutputFormatter()
    if (args.oformat): of.mapNamedOFOs()

    if (args.statFormat):
        import PowerStat
        powerstat = PowerStat.PowerStat(args.statFormat)

    leafNum = 0
    for topItem in args.files:
        pw = PowerWalk(topItem)
        pw.applyOptionsFromArgparse(args)

        whatCounts:defaultdict = defaultdict(int)
        for path0, fh0, what0 in pw.traverse():
            if (args.count):
                whatCounts[what0] += 1
                continue

            abspath0 = os.path.abspath(path0)
            if (args.absolute): printpath0 = abspath0
            else: printpath0 = path0

            flag = of.getFlagChar(abspath0)
            printpath0 = of.makeDisplayableName(printpath0) + flag
            if (args.quote): printpath0 = of.quoteFilename(printpath0)

            indent = of.OFOptions["iString"] * pw.travState.depth

            if (what0 == PWType.OPEN):
                if (args.type and "d" not in args.type): continue
                print(of.makeOpenDirDisplay(printpath0, pw.travState.depth))
            elif (what0 == PWType.LEAF):
                if (args.minBasenameLength and
                    len(os.path.basename(abspath0)) < args.minBasenameLength): continue
                if (args.maxBasenameLength and
                    len(os.path.basename(abspath0)) > args.maxBasenameLength): continue
                leafNum += 1

                if (not args.quiet):
                    print(of.makeItemDisplay(printpath0, pw.travState.depth))
                if (args.statFormat):
                    print(powerstat.format(abspath0))
                if (args.copyTo):
                    itemCopy(fromPath=abspath0, tgtDir=args.copyTo,
                        serialFormat=args.serializeFormat, serial=leafNum)
                if (args.exec):
                    itemExec(path0, args.exec)

            elif (what0 == PWType.CLOSE):
                if (args.type and "d" not in args.type): continue
                print(of.makeCloseDirDisplay(printpath0, pw.travState.depth))
            elif (what0 == PWType.IGNORE):
                print(indent, "IGNORING: ", printpath0, args.itemSep)
            elif (what0 == PWType.ERROR):
                print(indent, "ERROR: ", printpath0, args.itemSep)

    if (args.count):
        print("Dirs: %d\nFiles: %d" %
            (whatCounts[PWType.OPEN], whatCounts[PWType.LEAF]))

    if (args.stats):
        warning(0, pw.travState.getStats(showZeroes=True))
