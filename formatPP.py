#!/usr/bin/env python3
#
# formatPP.py: Some extensions to Python built-in format().
# 2021-09-29: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import re
# from string import Formatter
#
__metadata__ = {
    "title"        : "formatPP",
    "description"  : "Some extensions to Python built-in format().",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-09-29",
    "modified"     : "2021-09-29",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

UNFINISHED -- just experimenting with overriding Python str.format().

TODO: You can't monkey-patch a new function into a build-in type (like str), or
assign straight on top of built-in `format()`.

Can be used in place of the built-in `format()`, but as `formatPP()`.

This adds a few formatting codes:

* %q -- like %s, but puts quotes around the argument first.
* %v -- like %s, but makes invisible characters visible.
By default, it turns control characters into Unicode "control pictures" (U+2400...).
* %a -- like %s, but reduce all non-ascii (and all control chars) to \\-codes.

==Usage==

    from formatPP import formatPP
    str.formatPP = formatPP
    ...
    print("The string is %24.24q." % (myString))

This will print `myString` much like %24.24s would, but puts quotation marks around it.

The default quotation marks used are the Unicode DOUBLE ANGLE ones:
    LANGLE = chr(0x00AB)
    RANGLE = chr(0x00BB)

Callers can re-assign to these variables if desired.


=Related Commands and References=

This is an extension to the Python `format` built-in function, on which
see [https://docs.python.org/3/library/string.html#formatspec].

[https://www.python.org/dev/peps/pep-0498/#format-specifiers]

[https://www.python.org/dev/peps/pep-3101/] -- Advanced String Formatting.

[https://stackoverflow.com/questions/47081521/can-you-overload-the-python-3-6-f-strings-operator].

[https://stackoverflow.com/questions/16752818/modifying-pythons-string-formatter]


=Known bugs and Limitations=

It might be nice to have codes for combinations of quoting and translating, or
to express quoting via another synta tic part such as treating it as a sign
or "grouping option".

Surely there are additional types to be added
* boolean as T/F, True/False, or 0/1

=To do=


=History=

* 2021-09-29: Written by Steven J. DeRose.


=Rights=

Copyright 2021-09-29 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl:int, msg:str) -> None:
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg:str) -> None: log(0, msg)
def warning1(msg:str) -> None: log(1, msg)
def warning2(msg:str) -> None: log(2, msg)
def fatal(msg:str) -> None: log(0, msg); sys.exit()

LANGLE = chr(0x00AB)
RANGLE = chr(0x00BB)

builtinFTypes = "bcdeEfFgGnosxX%"
newFTypes = "qva"
typeExpr = r"([" + builtinFTypes + newFTypes + "])"
fspecExpr = r"(.)?([<>=%])?([-+ ])?(#)?(\d+)([_,])?(\.\d+)?" + typeExpr + "$"
#             1   2        3       4   5    6      7           8
#          fill   align    sign    alt wid  grp    prec        type
fspecRE = re.compile(fspecExpr)


###############################################################################
# https://docs.python.org/3/library/string.html?highlight=formatter#string.Formatter
#
class strPP(str):
    def __init__(self, s:str):
        super(strPP, self).__init__(s)

    def format_field(self, fspec):
        return self.formatPP(fspec)

    def formatPP(self, fspec):
        val = self
        fType = fspec[-1]
        if (fType in builtinFTypes):
            return format(val, fspec)
        #mat = re.match(fspecRE, fspec)
        fspec2 = fspec[0:-1] + "s"
        if (fType == 'q'):
            return format(LANGLE+str(val)+RANGLE, fspec2)
        if (fType == 'v'):
            val = re.sub(r"[\x00-\x1F]", self.controlSymbolsFunction, str(val))
            return format(val, fspec2)
        if (fType == 'a'):
            val = re.sub(r"[\x00-\x1F]", self.asciifyFunction, str(val))
            return format(val, fspec2)
        return super(strPP, self).format(fspec)

    @staticmethod
    def controlSymbolsFunction(mat):
        return(chr(0x2400 + ord(mat.group(1))))

    @staticmethod
    def asciifyFunction(mat):
        c = mat.group(1)
        cp = ord(c)
        if (cp > 65535): return "\\U%08x" % (cp)
        if (cp >   255): return "\\u%04x" % (cp)
        if (cp >   127): return "\\x%02x" % (cp)
        if (cp >    31): return c
        return "\\x%02x" % (cp)


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def anyInt(x:str) -> int:
        return int(x, 0)

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()

    #str.formatPP = formatPP
    #str.__format__ = formatPP
    #if (False):
    #    pylint: disable=W0622
    #    format = formatPP
    #    print("This is a sample with %%v:  %v." % ("Some controls are [\t\n\v \x12]."))
    #    print("This is a sample with %%q:  %v." % (" some string "))
    print(strPP("This is a sample with %%v:  %v.").format("Some controls are [\t\n\v \x12]."))
    print(strPP("This is a sample with %%q:  %v.").format(" some string "))
    #if (True):
    #    print(myFormatter("This is a sample with %%v:  %v.", "Some controls are [\t\n\v \x12]."))
    #    print(myFormatter("This is a sample with %%q:  %v.", " some string "))
