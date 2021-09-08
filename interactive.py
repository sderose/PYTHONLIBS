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
#pylint: disable=W0611
#
import sys
import os
import string
import re
import math
from math import ceil, floor, log, exp
import stat
import random
import argparse
import logging
import pprint

from datetime import date, datetime
from time import time, ctime
from collections import defaultdict, namedtuple, OrderedDict, deque, Counter
from enum import Enum
from io import StringIO
from typing import IO, Dict, List, Union, Any, Iterable, Callable, Type

import subprocess
from subprocess import check_output, CalledProcessError
import inspect
from functools import partial

import codecs
import unicodedata

import xml, xml.dom, xml.dom.minidom
from xml.dom.minidom import Document, Node, Element, Text, NamedNodeMap
import xml.sax
from xml.parsers import expat
from html.entities import codepoint2name, name2codepoint
import html5lib

import json


import DomExtensions
from PowerWalk import PowerWalk, PWType
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

class myClass(dict):
    def __init__(self):
        super(myClass, self).__init__()
        self.i = 1
        

print("Vars: c, f, i j k, l, d, t, NT theNT, myClass")
print("Ready")
