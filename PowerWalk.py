#!/usr/bin/env python
#
# PowerWalk: More capable version os Python's os.walk.
#
# 2018-04-21: Split out of countTags.py.
#
# To do (see "Future extensions" in the doc, below)
#
from __future__ import print_function
import sys, os
import argparse
import re
#import string
#import math
#import subprocess
import codecs
#import unicodedata
import gzip
import tarfile

#import pudb
#pudb.set_trace()

from alogging import ALogger
from MarkupHelpFormatter import MarkupHelpFormatter

__version__ = "2018-04-21"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-04-21",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-04-17",
}

lg = ALogger(1)


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
# Add? regex on name. links. text v. binary. permissions filter.
# See also lss, findIdenticalFiles, grep, find.
#
class PowerWalk:
    def __init__(self, topLevelItems=None, options=None):
        if (not topLevelItems):
            self.topLevelItems = [ os.environ['PWD'] ]
        elif (isinstance(topLevelItems, list)):
            self.topLevelItems = topLevelItems
        else:
            self.topLevelItems = [ topLevelItems ]

        self.options = {
            "containers"          : False,
            "openTar"             : False,
            "openGzip"            : False,
            "followLinks"         : False,

            "maxFiles"            : 0,
            "maxDepth"            : 0,

            "mode"                : "rb",
            "iencoding"           : "utf-8",

            "backups"             : False,
            "excludeExtensions"   : [],
            "hidden"              : False,
            "includeExtensions"   : [],
            "recursive"           : False,

            "sampleFactor"        : None,     #
            "sort"                : "",

            "notify"              : False,    # Tell caller on starting dir, etc.
        }
        if (options):
            for k, v in options.items():
                self.setOption(k,v)

        self.stats = {
            "nodesTried"          : 0,
            "itemsReturned"       : 0,
            "regular"			  : 0,
            "directory"			  : 0,
            "hidden"			  : 0,
            "excludedExtension"	  : 0,
            "nonIncludedExtension": 0,
            "tar"				  : 0,
            "gzip"				  : 0,
            "backup"			  : 0,
            "other"				  : 0,
        }

    def setOption(self, name, value):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        self.options[name] = value

    def getOption(self, name):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        return self.options[name]

    def showStats(self, writer=sys.stderr):
        writer.write("\nFiles processed:\n")
        for k, v in (self.stats.items()):
            writer.write("    %-20s %8d\n" % (k, v))

    @staticmethod
    def addTraversalOptions(parser, prefix=''):
        """Provide an easy way to add all our options to a main program.
        """
        prefix = "--" + prefix
        parser.add_argument(
            prefix + "backups",           action='store_true',
            help='Include (seeming) backup files,like .bak, ~x, #x#,....')
        parser.add_argument(
            prefix + "excludeExtensions", type=str, action='append',
            help='Exclude files with any of these extensions (repeatable).')
        parser.add_argument(
            prefix + "hidden",            action='store_true',
            help='Include files whose names begin with ".".')
        parser.add_argument(
            prefix + "--iencoding",       type=str, metavar='E', default="utf-8",
            help='Assume this character set. Default: utf-8.')
        parser.add_argument(
            prefix + "includeExtensions", type=str, action='append',
            help='Include (only) files with any of these extensions (repeatable).')
        parser.add_argument(
            prefix + "recursive",         action='store_true',
            help='Descend into subdirectories.')
        parser.add_argument(
            prefix + "sort",              type=str, default="R",
            help='Sort alphabetically by tag ("A"), or by rank/frequency ("R", the default).')
        return parser


    def traverse(self):
        #print("At traverse top.")
        for tl in (self.topLevelItems):
            for item in self.ttraverse(tl):
                self.stats["nodesTried"] += 1
                if (self.options["maxFiles"] and
                    self.stats["nodesTried"] > self.options["maxFiles"]): return
                yield item
        return

    def ttraverse(self, path, depth=0):
        if (self.options['maxDepth'] > 0 and depth > self.options['maxDepth']): return
        if (os.path.isdir(path)):
            if (self.options['containers']): yield(path, "DIR_START")
            self.trySomething('directory', path)
            if (not self.options['recursive']): return
            children = os.listdir(path)
            if (self.options['sort']):
                children = self.chSort(path, children)
            for ch in children:
                chPath = os.path.join(path, ch)
                for path2 in self.ttraverse(chPath, depth+1):
                    yield path2
            if (self.options['containers']): yield(path, "DIR_END")

        elif (tarfile.is_tarfile(path)):
            self.trySomething("tar file", path)
            if (self.options['containers']): yield(path, "TAR_START")
            if (self.options['openTar']):
                tfObject = tarfile.open(path, "r:*")
                for tfMember in (tfObject.getmembers):
                    if (tfMember.isfile()):
                        fh2 = tfObject.extractfile(tfMember)
                        self.stats["itemsReturned"] += 1
                        yield(path+"[untarred]", fh2)
                        fh2.close()
                    elif (tfMember.isdir()):
                        self.trySomething("tar subdir", path)
                    else:  # also issyn, islnk, ischr, isblk, isfifo, isdev
                        lg.vMsg(0, "Non-file, non-dir) in tar file.",
                            stat="bad tar member type")
                tfObject.close()
            if (self.options['containers']): yield(path, "TAR_END")

        elif (path.endswith(".gz")):
            self.trySomething('gzip', path)
            if (self.options['openGzip']):
                if (self.options['containers']): yield(path, "GZIP_START")
                lg.vMsg(1, "gzip file '%s'." % (path), stat='gzip file')
                fh2 = gzip.open(path, self.options['mode'])
                self.stats["itemsReturned"] += 1
                yield(path+"[ungzipped]", fh2)
                fh2.close()
            if (self.options['containers']): yield(path, "GZIP_END")

        elif (os.path.islink(path)):
            if (self.options['followLinks']):
                tgt = os.readlink(path)
                for lpath, lfh in (self.ttraverse(tgt, depth+1)):
                    yield lpath, lfh

        else:  # regular file?
            base = os.path.basename(path)
            (root, ext) = os.path.splitext(base)
            ext = ext.strip(". \t\n\r")

            if (not self.options['hidden'] and base.startswith(".")):
                self.trySomething("hidden", path, "exclude")

            elif (self.options['excludeExtensions'] and ext in
                self.options['excludeExtensions']):
                self.trySomething('excludedExtension', path, "exclude")

            elif (self.options['includeExtensions'] and ext not in
                self.options['includeExtensions']):
                self.trySomething('nonIncludedExtension', path, "exclude")

            elif (not self.options['backups'] and
                self.isBackup(path, base, root, ext)):
                self.trySomething("backup", path, "exclude")

            else:
                self.trySomething('regular', path)
                fh = codecs.open(
                    path, mode=self.options['mode'], encoding=self.options['iencoding'])
                # Py 2: codecs.open returns old-style class StreamReaderWriter
                if (sys.version_info < (3, 0)):
                    if ('__class__' in fh and
                        fh.__class__.__name__ != 'StreamReaderWriter'):
                        raise ValueError("Got type '%s' (%s) for %s." %
                            (type(fh), fh.__class__.__name__, path))
                self.stats["itemsReturned"] += 1
                yield(path, fh)
        return

    def chSort(self, curPath, chList):
        """Sort a file-list returned from os.listdir somehow.
        """
        if (self.options['sort'] == 'name'):
            chList.sort()
        elif (self.options['sort'] == 'iname'):
            chList.sort(key=lambda x: x.lowercase())
        elif (self.options['sort'] == 'atime'):
            chList.sort(key=lambda x: os.path.getatime(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'ctime'):
            chList.sort(key=lambda x: os.path.getctime(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'mtime'):
            chList.sort(key=lambda x: os.path.getmtime(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'size'):
            chList.sort(key=lambda x: os.path.getsize(os.path.join(curPath, x)))
        elif (self.options['sort'] == 'extension'):
            chList.sort(key=lambda x: os.path.splitext(os.path.join(curPath, x))[1])
        return chList

    def trySomething(self, what, path, statusMsg="included"):
        """Count the kind of thing, and maybe say something.
        """
        self.stats[what] += 1
        if (self.options['notify']):
            lg.vMsg(1, "Trying %s: '%s' [%s]" % (what, path, statusMsg))
        return

    # See also diffDirs.py, findDuplicateFiles, lss
    #
    def isBackup(self, path, base, root, ext):
        keywords = r'(backup|copy)'
        if (not base): return False
        if (base[0] in "~#" or base[-1] in "~#"): return True
        if (ext == "bak" or ext == "bcnk"): return True
        if (re.search(keywords + r'\b( \d+)?( of)\b', root, re.IGNORECASE)):
            return True

        if (re.search(r'\b(backup|copy|bak)\b', root, re.IGNORECASE)):
            if (not args.quiet):
                lg.vMsg(0, "Warning: questionable backup? '%s'" % (path))
            return True
        return False


###############################################################################
#
if __name__ == "__main__":

    def processOptions():
        parser = argparse.ArgumentParser(
            description="""
=pod

=head1 Usage

Similar to Python's built-in C<os.walk()>, but offers many
additional features. It returns the complete path, and a file
handle, to each selected item.

You can even get things that have to be opened in special ways, such
as the items in C<gzip> or C<tar> files.

Can be used as an iterator/generator. For example, this prints an
outline of the file directory subtree of the current directory. Special
items for opening and closing recursive directories, zip files, and tar files
are generated because of the 'containers' option:

    depth = 0
    pw = PowerWalk(".")
    pw.setOption('recursive', True)
    pw.setOption('containers', True)
    pw.setOption('includeExtensions', [ 'txt' ])
    for path, fh in pw.traverse():
        if (isinstance(fh, str) and fh.endswith("START")):
            print(" " * depth + "*** %s %s" % (fh, srcFile))
            depth += 1
        elif (isinstance(fh, str) and fh.endswith("END")):
            depth -= 1
            print(" " * depth + "*** %s %s" % (fh, srcFile))
        else:
            print(" " * depth + srcFile)
            doOneFile(srcFile)

=head1 Methods

=over

=item * B<__init__(self, topLevelItems=None, options=None)>

Create a PowerWalk instance, which will traverse all the specified
items. If C<topLevelItems> is None, the current directory is used;
if it is a list, all the named files and/or directories will be used;
otherwise, just the one named file or directory.

C<options> is a dict of option name:value pairs. For example, to
traverse all the subdirectories of the specified items (if any),
pass C<options> containing (at least) 'recursive':True.
Options can also be set later using C<setOption> (see below).

=item * B<setOption(self, name, value)>

Change the value of an available option, chosen from this list:

=over

=item * "containers"

If True (the default), a start and end event will be returned for each
directory, gzip, or tar file that is entered.

=item * "openTar"

If True (the default), C<tar> files will be opened as if they were
directories, and the individual items within them will be returned.

=item * "openGzip"

If True (the default), C<gzip> files will be opened as if they were
directories, and the individual items within them will be returned.

=item * "followLinks"

If True (the default is False), *nix symbolic links will be followed, and
their targets opened or traversed as if they had been at the link's location.
This does not include Mac "aliases", weblocs, etc.

=item * "maxFiles"

Stop after choosing this many files. Default: 0 (unlimited).

=item * "maxDepth"

Do not recurse deeper than this. Default: 0 (unlimited).

=item * "mode"

What C<mode> to pass to C<codecs.open>. Default: "rb".

=item * "iencoding"

Use this character encoding for input. Default: "utf-8"

=item * "backups"

Include .bak and similar files? Default: False

=item * "excludeExtensions"

List of file extension not to allow. Default: [].
See also I<includeExtensions>.

=item * "hidden"

Include hidden (.-initial) files? Default: False

=item * "includeExtensions"

List of (only) file extension to allow. Default: [].
See also I<excludeExtensions>.

=item * "recursive"

Traverse through subdirectories? Default: False

=item * "sampleFactor"

Include only this % of the available files. Default: None

=item * "sort"

Sort the items in each directory in the specified way.
Default: "" (just use whatever C<os.listdir> returns).

=over

=item * "name":  sort by filename

=item * "iname": sort by filename, ignoring case.

=item * "atime": file access time

=item * "ctime": file creation time

=item * "mtime": file modification time

=item * "size": File length in bytes

=item * "extension": Extension as returned by C<os.path.splitext>

=back

=item * "notify"

Display a message as each new file starts. Default: False

=back


=item * B<getOption(self, name)>

Return the value of an available option (see I<setOption>).

=item * B<showStats(self, writer=sys.stderr)>

Display a few statistics.

=item * B<addTraversalOptions(parser, prefix='')>

Add these options to a Python C<argparse> instance.

=item * B<traverse(self, path, depth=0)>

Iterate, returning the chosen files (or pseudo-files, such as items
from a zip, tar, or siilar archive). Each iteration returns a tuple of
(path, fh), where C<fh> is a readable. For regular files this is as returned
by C<codecs.open()> with the C<mode> and C<encoding> specified as options.
For items within tar, gzip, or other supported archive types, it will be
the readable interface from the corresponding package.

Ignored items (such as backups if the option to include them has not
been set), are quietly skipped.

Containers such as directories and archive files, generate start and end
events, with the appropriate path, but instead of a file handle or similar,
a string is returned: DIR_START, DIR_END, GZIP_START, GZIP_END, TAR_START,
TAR_END. These events can be suppressed by setting the C<containers> option
to False.

=item * B<trySomething(self, what, path)>

Internal method, called to issue a I<notify> message saying what kind
of thing is starting (when the I<notify> option is set).

=item * B<isBackup(self, path, base, root, ext)>

Test whether the given file's name indicates it is a backup, spare copy,
duplicte, or similar file. This method knows
quite a few naming conventions, but surely not all (for example, OS conventions such as "backup of" presumably localize). For example, filenames that:

=over

=item * start or ends with tilde or pound-sign

=item * have extension 'bak' or 'bcnk'

=item * match r'^(backup|copy) (\\(?\\d+\\)? )?of'

=item * match r'\\b(backup|copy|bak)\\b' (but in these cases a warning is
issued unless I<--quiet> is in effect).

=back

Some specific conventions

=over

=item * Mac OS X "Duplicate" does  C<foo.txt> -> C<foo copy.txt> -> C<foo copy 2.txt>

=item * emacs backups append '~' or '~\\d+~' to the filename
For relevant emacs settings, see
L<https://stackoverflow.com/questions/151945/>).

=item * emacs auto-save files put '#' at start and end of filename (but
are usually deleted when you exit).

=back


=head1 Possible extensions

=over

=item * Filter by permissions, owner and group ids; date; text vs. binary.

=item * Filter by regex for filename or dirname or path (cf 'find')

=item * Filter by mindepth, name, path, iname, ipath, xattr

=item * Support hard or soft links

=item * Support .webloc files and Mac aliases and bookmarks
(see https://stackoverflow.com/questions/48862093/how-to-read-change-and-write-macos-file-alias-from-python,
http://mac-alias.readthedocs.io/en/latest/ and
https://docs.python.org/2/library/macostools.html)

=item * Protect against circular links?

=item * Sampling of every nth file, first n from each directory, etc.

=item * Limit total size of files

=item * Support additional compression methods

=item * Support URLs on command-line

=item * Protect against caller changing working dir (unlike C<os.walk>)

=item * *nix C<file>-style output

=back


=head1 Known bugs and limitations

Should this do 'notify' events by callback, special inline events, or exceptions?

Sort should provide an invert option.


=head1 Related commands

C<find> + C<exec>

=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see L<http://creativecommons.org/licenses/by-sa/3.0/>.

For the most recent version, see L<http://www.derose.net/steve/utilities/>.

When using as a mainline (mainly to see what files will
be walked), the options are:

=cut
            """,
            formatter_class=MarkupHelpFormatter
        )
        parser.add_argument(
            "--quiet", "-q",       action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v",     action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version",           action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        PowerWalk.addTraversalOptions(parser)

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    # Main
    #
    args = processOptions()

    if (not args.files): args.files = [ os.environ['PWD'] ]
    pw = PowerWalk(args.files)
    if (args.verbose): pw.setOption('notify', True)
    pw.setOption('recursive', True)
    for path0, fh0 in pw.traverse():
        print("%s %s" % (path0, fh0))
