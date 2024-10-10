#!/usr/bin/env python3
#
# XmlNlpLoad.pm: "Pull text from XML and arrange for NLP tools.
# 2018-05-07: Written by Steven J. DeRose.
#

import xml.dom
import xml.dom.minidom
from domextensions import DomExtensions

from alogging import ALogger
lg = ALogger(1)

__metadata__ = {
    "title"        : "XmlNlpLoad",
    "description"  : "Pull text from XML and arrange for NLP tools.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-05-07",
    "modified"     : "2021-03-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """

[far from finished]


=To Do=

* Add DOMExtensions support for untagElements.


=History=

  2018-05-07, 2018-08-16: Written by Steven J. DeRose.
  2021-03-03: New layout.

"""


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
        self.runTidyFirst    =  False
        self.noSpaceElements =  None
        self.dropElements    =  None
        self.untagElements   =  None
        self.mergeElements   =  None
        self.selectElements  =  None
        self.justText        =  False

        self.thePath         = None
        self.theFH           = None
        self.theEncoding     = 'utf-8'
        self.theDOM          = None

    def setHTMLConventions(self):
        inlines = (" a abbr acronym b bdo big cite code dfn em i img input " +
            " kbd q s small span strike strong sub sup tt var" +
            " applet center dir font samp strike w")
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
            assert False, "untagElements not yet implemented."
            #for etype in self.untagElements:
            #    theDOM.untagByTagName(etype)
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
