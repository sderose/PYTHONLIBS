#!/usr/bin/env python3
#
# interactive.py: Set up packages and variables to speed up quick experiments.
# 2021-09-08: Written by Steven J. DeRose
#
# Code to run when using python interctively, to import a lot and create example
# instances of various types.
# Run with:
#     python -i -m interactive
#
#pylint: disable=W0611,W0212
# flake8: noqa
# fmt:off
#
__metadata__ = {
    "title"        : "interactive",
    "description"  : "Init various things for interactive Python.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-09-08",
    "modified"     : "2021-09-17",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

import sys
import os

import argparse
import codecs
from functools import partial
import inspect
import json
import logging
import math
from math import ceil, floor, log, exp
import pprint
import random
import re
import stat
import string

from collections import defaultdict, namedtuple, OrderedDict, deque, Counter
from datetime import date, datetime
from enum import Enum
from io import StringIO
import subprocess
from subprocess import check_output, CalledProcessError
from time import time, ctime
import typing
from typing import IO, Dict, List, Union, Any, Iterable, Callable, Type

import unicodedata
import xml
import xml.dom
import xml.dom.minidom
from xml.dom.minidom import Document, Node, Element, Text, NamedNodeMap
import xml.sax
from xml.parsers import expat
from html.entities import codepoint2name, name2codepoint
import html5lib

import DomExtensions
import sjdUtils
su = sjdUtils.sjdUtils()

c = 1+1j
f = 0.0
i = 1
j = 2
k = 3

l = [ 1, 2, 3 ]
d = { 'a':1, 'b':2, 'c':3 }
t = ( 1, 2, 3 )
NT = namedtuple('NT', [ 'a', 'b', 'c' ])
theNT = NT(1, 2, 3)

def show():
    """Display the *relevant* items.
    TODO: How to test builtins that don't trigger isbuiltin()?
    """
    print("Already defined:")
    gkeys = sorted(globals().keys())
    for gkey in gkeys:
        if (gkey.startswith("_")):
            continue
        if (gkey in [ "name2codepoint", "codepoint2name" ]):
            continue
        thing = globals()[gkey]
        if (inspect.isclass(thing) or inspect.ismodule(thing) or
            inspect.isfunction(thing or inspect.isbuiltin(thing))):
            continue
        if (isinstance(thing, (type, typing._GenericAlias, typing._SpecialForm))):
            continue
        print("    %-12s %-30s %s" % (gkey, type(thing).__name__, thing))

class myClass(dict):
    myClassVar = 1

    def __init__(self):
        super(myClass, self).__init__()
        self.i = 1


print("Vars: c, f, i j k, l, d, t, NT theNT, myClass")
print("Ready. Use 'show()' to see available vars.")

if (sys.argv[-1] == "-h"):
    print("""
interactive.py

This simply imports a ton of common libraries, and sets example variables of
many types. It's meant to be run via:

    python -i -m interactive

so that you don't have to type a lot for a quick experiment.
""")
