#!/usr/bin/env python
#
# listdir.py: A slight improvement (I think) on `os.listdir`.
# 2020-12-09: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import os

__metadata__ = {
    'title'        : "listdir",
    'description'  : "A slight improvement (I think) on os.listdir.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-12-09",
    'modified'     : "2020-12-09",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

A slight improvement (I think) on `os.listdir`, that lets you filter by
extension(s), exclude directories, and/or return absolute paths.

==Usage==

    import listdir from listdir
    for path in listdir(myPath, exts=["txt", "html"], abs=True):
        ...whatever...


=Related Commands=

My `PowerWalk.py`, which has much more sophisticated file-selection and
traversal (fairly similar to the *nix `find` command).


=Known bugs and Limitations=

There is no way to request a full but relative path.

A few more features might be useful enough to include, such as excluding
binary and special files, hidden files, backups, and links.


=History=

* 2020-12-09: Written by Steven J. DeRose.


=Rights=

Copyright 2020-12-09 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

###############################################################################
#
def listdir(path, exts:str=None, abspaths=False, dirs=False, hidden=False):
    """Like os.listdir, but can select by extension(s), and return full paths.
    """
    if (exts):
        if (isinstance(exts, str)): exts = [ exts ]
        elif (not isinstance(exts, list)):
            raise ValueError("exts must be a string or list.")

    for p in os.listdir(path):
        if (not hidden and p.startswith('.')): continue
        if (exts):
            _, thisExt = os.path.splitext(p)
            thisExt = thisExt.lstrip('.')
            if (thisExt not in exts): continue
        full = os.path.join(path, p)
        if (not dirs and os.path.isdir(full)): continue
        if (abspaths):
            p = os.path.abspath(p)
        yield p
    return


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def warn(lvl, msg):
        if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
        if (lvl < 0): sys.exit()


    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--abspaths", action='store_true',
            help='Show absolute paths.')
        parser.add_argument(
            "--dirs", action='store_true',
            help='Also show directories.')
        parser.add_argument(
            "--exts", type=str, action='append',
            help="Include files with this extension (repeatable). Don't include dot.")
        parser.add_argument(
            "--hidden", action='store_true',
            help='Also show dot-initial files.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files', type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        warn(-1, "listdir.py: No files specified....")

    for path0 in args.files:
        print("******* Top-level item '%s':" % (path0))
        for p0 in listdir(path0, abspaths=args.abs, dirs=args.dirs,
            exts=args.exts, hidden=args.hidden):
            print("    " + p0)
