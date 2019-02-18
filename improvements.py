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
from __future__ import print_function
import sys
import os, argparse
import re
import string
#import codecs
#import math
#import subprocess
import unicodedata

#import pudb
#pudb.set_trace()

from sjdUtils import sjdUtils
from alogging import ALogger
from MarkupHelpFormatter import MarkupHelpFormatter

global args, su
#lg = ALogger(1)
args = su = None

__version__ = "2015-02-13"

sys.stderr.write("*** improvements is mostly notes, unfinished ***\n")


###############################################################################
#
def processOptions():
    "Parse command-line options and arguments."
    parser = argparse.ArgumentParser(
        description="""

=head1 Description

A small collection of improved versions of various Python gadgets.

(in progress)


=head1 Methods

=over

=item * B<split(string, delim, strip=None, nFields=0, types=None, quote="")>

Split I<string>, returning an array of its fields.

=back


=head1 Known bugs and Limitations

=head1 Licensing

Copyright 2015 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.
        """,
        formatter_class=MarkupHelpFormatter
    )

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
    "unicode":      lambda x: unicode(x),
    "normunicode":  lambda x: x == unicodedata.normalize(x),
    "utf8":         lambda x: x.decode('utf-8'),
}

def isTypableAs(var, typename):
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
    users=[],
    groups=[],
    ):
    """Like os.listdir, but can filter what you get back.
    """
    cands = os.listdir(path)
    picked = []
    for c in cands:
        if (followLinks and os.path.islink(c)):
            c = os.readlink(c)
        cdirs, cbasename = os.path.split(c)
        cfn, cext = os.path.splitext(cbasename)
        if (extensions and not re.search(extensions, c)):        continue
        if (not dirs and os.path.isdir(c)):                      continue
        if (not files and os.path.isfile(c)):                    continue
        if ('r' in permissions and not os.access(c, os.R_OK)):   continue
        if ('w' in permissions and not os.access(c, os.W_OK)):   continue
        if ('x' in permissions and not os.access(c, os.X_OK)):   continue
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
    users=[],
    groups=[],
    ):
    return(None)



###############################################################################
###############################################################################
###############################################################################
# Mainly to allow normalizing keys, e.g., case, accents, utf norm, encoding.
class normdict(dict):
    """A subclass of Python 'dict', with some additional features.
    Perhaps add something for str vs. int casting?
    """
    def __init__(
        self,
        default=None,        # Like defaultdict
        normalizer=None,     # Pass all keys through this before hashing
        sorter=None,         # Sort function to use when needed (on norm or reg?)

        keyType=None,        # Keys must be of this type
        valueType=None       # Values must be of this type
        ):

        self.default    = default
        if (normalizer == "ignoreCase"):
            self.normalizer = string.lower
        elif (normalizer == "normSpace"):
            self.normalizer = lambda x: re.sub(r'\s+', ' ', x.split())
        self.sorter     = sorter
        self.keyType    = keyType
        self.valueType  = valueType

        self.keysLocked = False
        self.dataLocked = False
        self.theDict    = {}

    def lockKeys(self):
        self.keysLocked = True

    def unlockKeys(self):
        self.keysLocked = False

    def lockData(self):
        self.dataLocked = True

    def unlockData(self):
        self.dataLocked = False

    def findAbbrev(self, key):
        if (self.normalizer): normKey = self.normalizer(key)
        else:                 normKey = key
        for k, v in self.theDict.items():
            if (k.startswith(normKey)): return(k)
        return(None)

    def matchingKeys(self, regex):
        matches = []
        rc = re.compile(regex)
        for k, v in self.theDict.items():
            if (re.match(rc, k)): matches.append(k)
        return(matches)

    def str(self):
        return(str(self.theDict))

    def __format__(self, compact=True):
        if (not compact): return(self.theDict.__format__())
        buf = ""
        for k, v in self.theDict.items():
            buf += "%-30s %s\n" % (k,v)
        return(buf)

    def __len__(self):
        return(len(self.theDict))

    def __getitem__(self, key):
        if (self.normalizer): normKey = self.normalizer(key)
        else:                 normKey = key
        if (self.keyType and isinstance(key, self.keyType)):
            raise TypeError
        if (normKey in self.theDict):
            return(self.theDict[normKey])
        if (self.default and not self.keysLocked):
            self.theDict[normKey] = self.default(key)
        else:
            raise KeyError

    def __setitem__(self, key, value):
        if (self.normalizer): normKey = self.normalizer(key)
        else:                 normKey = key
        if (self.keyType and not isinstance(key, self.keyType) or
            self.valueType and not isinstance(value, self.valueType)):
            raise TypeError
        if (self.keysLocked and normKey not in self.theDict):
            raise KeyError
        if (self.dataLocked):
            raise KeyError
        self.theDict[normKey] = value

    def __delitem__(self, key):
        """Should keysLocked prevent deletion, too?
        """
        if (self.normalizer): normKey = self.normalizer(key)
        else:                 normKey = key
        if (normKey in self.theDict):
            del self.theDict[normKey]
        else:
            raise KeyError

    def __iter__(self):
        iter = Object()
        if (self.sorter):
            iter.list = sorted(self.theDict.keys(), compare=self.sorter)
        else:
            iter.list = sorted(self.theDict.keys())
        iter.curPos = 0
        iter.__iter__ = lambda x: self
        while(iter.__next__(self)):
            iter.curPos += 1
            if (iter.curPos >= len(iter.list)): return(None)
            return(iter.list[iter.curPos])

    def __contains__(self, key):
        if (self.normalizer): normKey = self.normalizer(key)
        else:                 normKey = key
        return(normKey in self.theDict)



