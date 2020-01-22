#!/usr/bin/env python
#
# improvements.py
#
# 2015-02-13: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#     Integrate regexExtensions?
#     argparsePP: way to add "choices" values as independent options !
#
#pylint: disable=W0613, W0212
#
from __future__ import print_function
import sys
import os, argparse
import re
#import string
#import codecs
#import math
#import subprocess
import unicodedata

#import pudb
#pudb.set_trace()

from MarkupHelpFormatter import MarkupHelpFormatter

args = None

__metadata__ = {
    'title'        : "improvements.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2015-02-13",
    'modified'     : "2020-01-09",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Slightly enhanced versions of various Python gadgets.

(in progress)

=Methods=

* qsplit(s, delim="\t", quote='"', escape="\\")
Split a tring, but support escaping and/or quoting the split-deimiter.

* B<split(string, delim, strip=None, nFields=0, types=None, quote="")>
Split I<string>, returning an array of its fields.

* '''listdir''' -- a slightly enhanced version, that lets you filter out
various kinds of files.

=Known bugs and Limitations=

=Licensing=

Copyright 2015 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.
"""

sys.stderr.write("*** improvements is mostly notes, unfinished ***\n")


###############################################################################
#
def processOptions():
    "Parse command-line options and arguments."
    parser = argparse.ArgumentParser(
        description=descr, formatter_class=MarkupHelpFormatter)

    args0 = parser.parse_args()
    return(args0)


def join(ss, delim, escape="\\"):
    buf = ""
    for s in ss:
        if (delim in s):
            if (escape): s.sub(delim, escape+delim)
            else: raise ValueError
        buf += delim + s
    return(buf)


###############################################################################
# There are many way to check if something is a legit integer:
#
typeList = {
    "int":		    lambda x: float(x) == int(x),
    "int8":		    lambda x: float(x) == int(x) and abs(int(x)) < 1<<7,
    "int16":		lambda x: float(x) == int(x) and abs(int(x)) < 1<<15,
    "int32":		lambda x: float(x) == int(x) and abs(int(x)) < 1<<31,
    "int64":		lambda x: float(x) == int(x) and abs(int(x)) < 1<<63,
    "unsigned":     lambda x: float(x) == int(x) and x >= 0,
    "unsigned8":    lambda x: float(x) == int(x) and x >= 0 and x < 1<8,
    "unsigned16":   lambda x: float(x) == int(x) and x >= 0 and x < 1<16,
    "unsigned32":   lambda x: float(x) == int(x) and x >= 0 and x < 1<32,
    "unsigned64":   lambda x: float(x) == int(x) and x >= 0 and x < 1<64,
    "natural":      lambda x: float(x) == int(x) and x > 0,
    "complex":      lambda x: complex(x),

    "hex":          lambda x: int(x,16),
    "oct":          lambda x: int(x,8),
    "bin":          lambda x: int(x,2),

    "float":        lambda x: float(x),

    "bool":         lambda x: bool(x),
    "str":          lambda x: str(x),
    #"unicode":      lambda x: unicode(x),
    "normunicode":  lambda x: x == unicodedata.normalize(x),
    "utf8":         lambda x: x.decode('utf-8'),
}

def isTypeableAs(var, typename):
    if (typename not in typeList): return(None)
    f = typeList[typename]
    try: rc = f(var)
    except ValueError: return(False)
    return(rc)


###############################################################################
#
def qsplit(s, delim="\t", quote='"', escape="\\"):
    expr = (r'(' +
        r'[^' + delim + quote + ']*' + '|' +
        quote + '([^'+quote+escape+']|'+escape+'.)*' + quote +
        r')')
    fields = re.findall(expr, s)
    return(fields)

def split(s,
    delim,         # String to split on
    strip=None,    # Strip whitespace after parsing (except inside quotes)
    nFields=0,     # Required number of fields
    types=None,    # List of types that fields must be (int? = optional; * = any)
    quote="",      # Quote char for fields that contain delim.
    escape="\\"):  # To escape anything inside quoted fields.
    if (strip): s = s.strip()
    if (quote and quote in s):
        fields = qsplit(s, delim, quote=quote, escape=escape)
    else:
        fields = s.split(delim)
    if (strip):
        for i in range(fields):
            fields[i] = fields[i].strip()
    if (nFields>0 and len(fields)!=nFields):
        raise ValueError
    if (not types):
        return(fields)
    for i, typ in enumerate(types):
        if (not typ or typ == '*'):
            continue
        optional = typ.endswith('?')
        if (fields[i] is None and not optional):
            raise TypeError
        if (optional):
            typ = typ[0:-1]
        if (not isTypeableAs(fields[i], typ)):
            raise TypeError
    return(fields)



###############################################################################
###############################################################################
###############################################################################
# File-system walkers.
#
def listdir(
    path,               # Path to dir to list files from
    followLinks=True,   # Return target of links?
    dirs=True,           # Include directories?
    files=True,          # Include files (not dirs)?
    texts=True,
    binaries=True,
    specials=True,
    include="None",
    exclude="None",
    extensions="",      # Regex that extension must match
    permissions="",     # Must have included permission (rwx)
    users=None,
    groups=None,
    ):
    """Like os.listdir, but can filter what you get back.
    """
    cands = os.listdir(path)
    picked = []
    for c in cands:
        if (followLinks and os.path.islink(c)):
            c = os.readlink(c)
        cdirs, cbasename = os.path.split(c)
        #cfn, cext = os.path.splitext(cbasename)
        if (extensions and not re.search(extensions, c)):        continue
        if (not dirs and os.path.isdir(c)):                      continue
        if (not files and os.path.isfile(c)):                    continue
        if ('r' in permissions and not os.access(c, os.R_OK)):   continue
        if ('w' in permissions and not os.access(c, os.W_OK)):   continue
        if ('x' in permissions and not os.access(c, os.X_OK)):   continue
        if (include and not re.match(include, c)):               continue
        if (exclude and re.match(exclude, c)):                   continue
        if (users or groups):
            stats = os.stat(c)
            if (users and stats.st_uid not in users):            continue
            if (users and stats.st_gid not in groups):           continue
        picked.append(c)
    return(picked)

def fswalk(top, topdown=True, onerror=None, followlinks=False,
    include="None",
    exclude="None",
    dot=False,
    dirs=True,
    files=True,
    texts=True,
    binaries=True,
    specials=True,
    extensions="",      # Regex that extension must match
    permissions=None,
    users=None,
    groups=None,
    ):
    return(None)

