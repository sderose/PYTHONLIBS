#!/usr/bin/env python3
#
# isBackup
# 2020-09-15: Written by Steven J. DeRose (just forwards to PowerWalk).
#
import sys

import PowerWalk

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

__metadata__ = {
    'title'        : "isBackup",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-09-15",
    'modified'     : "2020-09-15",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

Test whether files seem to be backups, based on their name.
This is really just a wrapper on `PowerWalk.py`.


=Related Commands=

Similar code is/was in my:
    FileManagement/checkSumDirs.py
    FileManagement/diffDirs.py
    FileManagement/lsoutline
    Text/globalChange
    XML/ANALYZE/countTags.py
    XML/ANALYZE/countTags.py.bak


=Known bugs and Limitations=

Conventions vary a lot, and some involve localization ("Backup 3 of x").
So there are no guarantees.


=History=

* 2020-09-15: Written by Steven J. DeRose.


=To do=


=Rights=

Copyright 2020-09-15 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--recursive", action='store_true',
            help='Descend into subdirectories.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files', type=str, nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        sys.stderr.write("No files specified.\n")
        sys.exit()
    pw = PowerWalk.PowerWalk(args.files, open=False, containers=False,
        recursive=args.recursive)
    for path, fh, typ in pw.traverse():
        rc = PowerWalk.isBackup(path)
        print("%s %s" % ("Y" if rc else "N", path))
