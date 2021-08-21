#!/usr/bin/env python3
#
# strftime.py: Make strftime available on command line.
# 2021-08-21: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import re
import datetime

__metadata__ = {
    "title"        : "strftime.py",
    "description"  : "Make strftime available on command line.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08-21",
    "modified"     : "2021-08-21",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

namedTimeFormats = {
    "ISO8601-date"      : "%Y-%m-%d",              # '2021-08-21'
    "ISO8601-time"      : "%H:%M:%S",              # '16:45:36'
    "ISO8601-datetime"  : "%Y-%m-%dT%H:%M:%S",     # '2021-08-21T16:45:36'
    "US-date"           : "%m/%d/%Y",              # '08/21/2021'
    "MIME"              : "%a %b %d %H:%M:%S %Y",
    "ASC"               : "%a %b %d %H:%M:%S %Y",  # 'Sat Aug 21 16:45:36 2021'
    "EPOCH"             : None,                    # float(1629579025.866747)
    "IEPOCH"            : None,                    # int(1629579025)
}

descr = """
=Description=

Make strftime() available on command line.

==Usage==

    strftime.py [options] [files]

By default, prints the current date and time in the format generated by
`asctime()` (such as "Sat Aug 21 17:06:28 2021"). 

To refer to a different time, specify it with the --time option.
For the moment, only ISO 8601 format, and int or float *nix epoch timestamps
are accepted.

To choose an output format:
* The default is ASC (as shown above)
* Specify -f and any %-string as for strftime.
* Specify --as and a named format from
""" + " ".join(namedTimeFormats.keys()) + """

=Related Commands=

`strftime()` is a stock *nix function. It does not typically handle Unicode.


=Known bugs and Limitations=


=To do=

Probably makes sense to hook up strptime.


=History=

* 2021-08-21: Written by Steven J. DeRose.


=Rights=

Copyright 2021-08-21 by Steven J. DeRose. This work is licensed under a
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

ISO8601 = r"(\d\d\d\d)-(\d\d)-(\d\d)([@Tt](\d\d):(\d\d):(\d\d)(\.\d_)?)?"

def parseTime(t:str) -> datetime.datetime:
    """Parse a number of plausible time formats.
    TODO: Copy more variations from grepMail.py.
    """
    if (not t):
        return datetime.datetime.now()

    mat = re.match(ISO8601, t)                      # ISO 8601
    if (mat):
        yr = mat.group(1)
        mo = mat.group(2)
        dy = mat.group(3)
        if (mat.group(3)):
            hr = mat.group(4)
            mi = mat.group(5)
            se = mat.group(6)
            ms = mat.group(7)
        else:
            hr = mi = se = ms = 0
        return datetime.datetime(yr, mo, dy, hr, mi, se, ms, tzinfo=None)
        
    try:
        timestamp = datetime.datetime.fromisoformat(t)
        return datetime.datetime.fromtimestamp(timestamp)
    except ValueError:
        pass
        
    try:                                            # Epoch time
        timestamp = float(t)
        return datetime.datetime.fromtimestamp(timestamp)
    except ValueError:
        pass
        
    fatal("Could not parse date/time '%s'." % (t))


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
            "--s", action="store_true",
            help="???")
        parser.add_argument(
            "--maxsize", type=int, default=0,
            help="Maximum character length of resulting string.")
        parser.add_argument(
            "--format", "-f", type=str, metavar="F", default="",
            help="Format to display (see `man strftime(3)`)")
        parser.add_argument(
            "--asFormat", type=str, choices=namedTimeFormats.keys(), default="ASC",
            help="Named format to display.")
        parser.add_argument(
            "--time", type=str, default=None,
            help="The time to format. See -h for accepted formats.")
        parser.add_argument(
            "--locale", type=str, default=None,
            help="Not yet... Specify a locale to constrain formatting.")
            
        parser.add_argument(
            "--color",  # Don't default. See below.
            help="Colorize the output.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: utf-8.")
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

    datetimeObj = parseTime(args.time)
    
    if (args.format): f = args.format
    else: f = namedTimeFormats[args.asFormat]
    sft = datetimeObj.strftime(f)
    if (args.maxsize and len(sft) > args.maxsize):
        sft = sft[0:args.maxsize]
    print(sft)