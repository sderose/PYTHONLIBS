#!/usr/bin/env python3
#
# pythonStartup.py: Set up packages and variables to speed up quick experiments.
# 2021-09-08: Written by Steven J. DeRose
#
# Code to run when using python interctively, to import a lot and create example
# instances of various types.
# Run with:
#     python -i -m pythonStartup.py
# or set PYTHONSTARTUP to point here.
#
#pylint: disable=W0611,W0212
# flake8: noqa
# fmt:off
#
__metadata__ = {
    "title"        : "pythonStartup",
    "description"  : "Init various things for interactive Python.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-09-08",
    "modified"     : "2025-01-04",
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
import typing
from typing import IO, Dict, List, Union, Any, Iterable, Callable, Type
from enum import Enum
from io import StringIO
import subprocess
from subprocess import check_output, CalledProcessError

from datetime import date, datetime
from time import time, ctime

import unicodedata

import xml
from xml import dom
from xml.dom import minidom
from xml.dom.minidom import Document, Node, Element, Text
from xml import sax
from xml.parsers import expat
from html.entities import codepoint2name, name2codepoint
import html5lib

#import DomExtensions
#import sjdUtils
#su = sjdUtils.sjdUtils()

c = 1+1j
f = 0.0
i = 1
j = 2
k = 3

l = [ 1, 2, 3 ]
d = { 'a':1, 'b':2, 'c':3 }

class e(Enum):
    NONE = 0
    A = 1
    B = 2
    C = 3

sio = StringIO("This is a small StringIO buffer.")

t = ( 1, 2, 3 )
NT = namedtuple('NT', [ 'a', 'b', 'c' ])
theNT = NT(1, 2, 3)

impl = minidom.getDOMImplementation()
doc = impl.createDocument("", "html", None)
docEl = doc.documentElement

for cnum in range(10):
    newEl = doc.createElement("p")
    newEl.appendChild(doc.createTextNode("for the snark was a boojum"))
    newEl.setAttribute("n", str(cnum))
    docEl.appendChild(newEl)

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
        print("    %-12s %-25s %s" % (gkey, type(thing).__name__, thing))

class myClass(dict):
    myClassVar = 1

    def __init__(self):
        super(myClass, self).__init__()
        self.i = 1


print("Vars: c, f, i j k, l, d, t, NT theNT, myClass.")
print("Classes: collections[], argparse, codecs, inspect, logging, math.")
print("Xml: impl, doc, docEl (html/p[10]), Document, Node, Element, Text,...")
print("Ready. Use 'show()' to see available vars.")

if (sys.argv[-1] == "-h"):
    print("""
interactive.py

This simply imports a ton of common libraries, and sets example variables of
many types. It's meant to be run via:

    python -i -m interactive

so that you don't have to type a lot for a quick experiment.
""")
