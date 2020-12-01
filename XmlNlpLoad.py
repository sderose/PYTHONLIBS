#!/usr/bin/env python
#
# XmlNlpLoad.pm
#
# 2018-05-07: by Steven J. DeRose.
#
# To do:
#     Test
#
from __future__ import print_function
#import sys, os
#import argparse
#import re
#import string
#import math
#import subprocess
#import codecs
#import gzip
#from collections import defaultdict

#import pudb
#pudb.set_trace()

#from sjdUtils import sjdUtils
from alogging import ALogger
#from MarkupHelpFormatter import MarkupHelpFormatter

import xml.dom
import xml.dom.minidom
from DomExtensions import DomExtensions


__version__ = "2018-08-16"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-05-07",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-08-16",
}

#su = sjdUtils()
lg = ALogger(1)


###############################################################################
#
class XmlNlpLoad:
    """Load an XML document, discard parts not of interest, and break it
    into an array of text samples (possibly each with an assigned type)

    To do:
        Allow drop and untag to say whether to put in spaces.
        Write setHTMLConventions
        Check for xml:lang, html meta encoding
    """

    def __init__(self):
        self.runTidyFirst =     False
        self.noSpaceElements =  None
        self.dropElements =     None
        self.untagElements =    None
        self.mergeElements =    None
        self.selectElements =   None
        self.justText =         False

        self.thePath     = None
        self.theFH       = None
        self.theEncoding = 'utf-8'
        self.theDOM      = None

    def setHTMLConventions(self):
        inlines = (" a abbr acronym b bdo big cite code dfn em i img input " +
            " kbd q s small span strike strong sub sup tt var" +
            " applet center dir font samp strike u")
        self.noSpaceElements = (
            inlines.split(sep=" "))
        drops = 'del object img head form'
        self.dropElements = drops.split(sep=" ")
        self.untagElements = 'ins a'.split(sep=" ")
        self.runTidyFirst = True

    def open(self, path):
        self.thePath = path
        self.theFH = self.theFH.open(self.thePath, "rb", encoding=self.theEncoding)
        return self.theFH

    def close(self):
        # self.theDOM.breakLinks()
        self.theDOM = None
        self.theFH.close()
        self.theFH = None

    def readFrom(self, fh):
        self.thePath = None
        self.theFH = fh

    def loadDOM(self):
        DomExtensions.patchDOM()
        theDOM = xml.dom.minidom.parse(self.theFH)
        if (self.dropElements):
            for etype in self.dropElements:
                theDOM.removeByTagName(etype)
        if (self.untagElements):
            for etype in self.untagElements:
                theDOM.untagByTagName(etype)
        if (self.mergeElements):
            for fromType, toType in self.mergeElements.items():
                theDOM.renameByTagName(fromType, toType)
        self.theDOM.addElementSpaces(self.noSpaceElements)

        self.theDOM = theDOM
        return self.theDOM

    # Make this an iterator
    def getTextByTagName(self, etype):
        nodes = self.theDOM.getElementsByTagName(etype)
        texts = []
        for node in nodes:
            texts.append(node.innertext)
