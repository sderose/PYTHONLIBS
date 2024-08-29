#!/usr/bin/env python3
#
# getLibraryVersions.py: Return or display info on all imported libraries.
# 2022-04-08: Written by Steven J. DeRose.
#
import sys

__metadata__ = {
    "title"        : "getLibraryVersions",
    "description"  : "Return or display info on all imported libraries.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2022-04-08",
    "modified"     : "2022-04-08",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Name=
getLibraryVersions: Return or display info on all imported libraries.
    
    
=Description=

Display the name, version, and source file for each library imported.
Can be run from the command line (listing libraries to import), or
called from code to report the library state when called.

By default, excludes names starting with single or double
underscore, and a list of builtins (but see options).

==Usage from command line==

    getLibraryVersions.py [options] [libraries]

The [libraries] are imported, then those and any others (all filtered
by applicable options) are listed.

==Usage from code==

    from getLibraryVersions import getLibraryVersions
    import .... [whatever else you're doing]
    getLibraryVersions(dunder=False, sunder=False, builts=False, dotted=False)
    

=See also=


=Known bugs and Limitations=

It includes a few libraries that it uses, even if you didn't especially want
them reported.

Many libraries do not have a __version__ attributes, and some (like
"cython_runtime") do not have a __file__ attribute. "???" is displayed
in such cases.


=To do=


=History=

* 2022-04-08: Written by Steven J. DeRose.


=Rights=

Copyright 2022-04-08 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

builtinList = """
abc
argparse
builtins
bz2
codecs
collections
collections.abc
contextlib
copy
copyreg
datetime
encodings
encodings.aliases
encodings.latin_1
encodings.utf_8
enum
errno
fnmatch
functools
genericpath
gettext
google
grp
gzip
hashlib
heapq
importlib
importlib._bootstrap
importlib._bootstrap_external
importlib.abc
importlib.machinery
importlib.util
inspect
io
itertools
json
keyword
locale
lzma
marshal
math
operator
os
os.path
posix
posixpath
pwd
random
re
regex
reprlib
shutil
site
sre_compile
sre_constants
sre_parse
stat
string
subprocess
sys
threading
time
types
typing
typing.io
typing.re
unicodedata
urllib
warnings
zipimport
zlib
""".split(sep="\n")


###############################################################################
#
def showLibraryVersions(dunder=False, sunder=False, builts=False, dotted=False):
    """Collect all imported modules, with their version and path (if
    available), and display them.
    """
    mlist = sorted(list(sys.modules.keys()))
    for m in mlist:
        if (not dunder and m.startswith("__")): continue
        if (not sunder and m.startswith("_") and m[1]!="_"): continue
        #if (not builts and m in builtinList): continue
        if (not builts and "__builtins__" in dir(m)): continue
        if (not dotted and "." in m): continue
        f = v = "???"
        try:
            f = sys.modules[m].__file__
        except AttributeError:
            pass
        try:
            v = sys.modules[m].__version__
        except AttributeError:
            pass
        print("%-30s %20s\n    %s" % (m, v, f))
        
    
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
            "--builts", action="store_true",
            help="Include known builtins.")
        parser.add_argument(
            "--dotted", action="store_true",
            help="Include sub-libraries (names containing periods).")
        parser.add_argument(
            "--dunder", action="store_true",
            help="Include libraries starting with double underscores.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--sunder", action="store_true",
            help="Include libraries starting with single underscores.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "libs", type=str, nargs=argparse.REMAINDER,
            help="Name of additional libraries to import.")

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()
    
    if (not args.quiet and args.libs):
        print("Attempting requested imports...")
        
    for lib in args.libs:
        try:
            __import__(lib)
        except ImportError as e:
            print("*** Unable to import '%s':\n    %s\n" % (lib, e))
    print()
    if (not args.quiet):
        print("=== Libraries loaded, with version and path ===")

    showLibraryVersions(dunder=args.dunder, sunder=args.sunder,
        builts=args.builts, dotted=args.dotted)
    
