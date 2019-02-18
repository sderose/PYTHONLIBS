#!/usr/bin/env python
#
# Element-stack manager for an XML parser. Steven J. DeRose, 2013-02-25.
#     cf ElementManager.pm.
#
# 2013-02-25: Create based on ElementManager.pm.
# 2015-09-19: Finally get back to it; hook up to multiXML.py
#
# To do:
#     Finish ~ mecs/concur/xconcur way to treat element closes.
#     Integrate into littleParser.py, multiXml.py.
#     Namespaces? Anything special?
#     SAX events?
#
import sys
import re
# os, re
#import string


###############################################################################
###############################################################################
#
class AttributeDefinition:
    """The information gleaned for one attribute, from an ATTLIST declaration.
    These are always owned by ElementDefinition instances.
    """
    typeList = {  # Types of attributes
        "ID":1, "IDREF":2, "IDREFS":3,
        "ENTITY":11, "ENTITIES":12,
        "CDATA":21,
        "NAME":31, "NMTOKEN":32, "NAMES":33, "NMTOKENS":34,
    }

    def __init__(self, aname, atype, adefault, anotation):
        if (type not in AttributeDefinition.typeList):
            sys.stderr.write("Bad type '"+atype+"' for attribute '"+aname+"'\n")
            atype = "CDATA"
        self.aname      = aname
        self.atype      = atype
        self.adefault   = adefault
        self.anotation  = anotation



###############################################################################
###############################################################################
#
class ElementDefinition:
    """The information about one element type, from an ELEMENT declaration.
    AttributeDefinition instances for the element, are referenced from here.
    """
    def __init__(self, ename, model=""):
        self.ename    = ename
        self.model    = model
        self.attrs    = {}

    def defineAttribute(self, aname, atype, default, notation):
        if (aname in self.attrs):
            sys.stderr.write("Duplicate attribute '%s' for '%s'\n" %
                (aname, self.ename))
            return(0)
        self.attrs[aname] = AttributeDefinition(aname, atype, default, notation)
        return(1)



###############################################################################
###############################################################################
# One currently-open element.
#
class ElementStackFrame:
    """Represents one element that is currently open. Parsers maintain a
    stack of these (or, in CONCUR or other overlap situations, a more complex
    data structure of them).
    """
    def __init__(self, ename, attrs, nsPrefix, nsURI, parent, userData):
        self.theElementManager = None
        self.ename         = ename          # Name of the open element
        self.nsPrefix      = nsPrefix
        self.nsURI         = nsURI
        self.attrs         = []
        self.id            = attrs or {}
        self.lang          = ""
        self.allNameSpaces = {}
        self.newNameSpaces = {}
        self.dftNameSpace  = None
        self.userData      = userData

        self.lang          = parent.lang
        self.nameSpacePrefix = nsPrefix
        self.nameSpaceURI    = nsURI

    def setLang(self, lang):
        self.lang          = lang

    def setNameSpace(self, nsPrefix, nsURI):
        self.nameSpacePrefix = nsPrefix
        self.nameSpaceURI    = nsURI


###############################################################################
###############################################################################
#
class ElementManager:
    """An element stack, as well as applicable schema information.
    """
    def __init__(self):
        self.eStack = []          # Stack of ElementStackFrame's
        self.eDefs = {}
        self.defaultLang = "EN"

        # Stats
        self.startedAt     = ""
        self.childTypes    = []
        self.nChildren     = 0
        self.nDescendants  = 0
        self.nTextNodes    = 0
        self.nWSOs         = 0
        self.nComments     = 0
        self.nPIs          = 0


    def defineElement(self, ename, model):
        self.eDefs[ename] = ElementDefinition(ename, model)

    def defineAttribute(self, ename, aname, atype, adefault, anotation):
        if (ename not in self.eDefs):
            sys.exit(0)
        self.eDefs[ename].defineAttribute(aname, atype, adefault, anotation)

    ###########################################################################
    # This takes attributes in SAX style, as an array.
    # Should probably add some other ways....
    #
    def openElement(self, ns="", ename="", attrMap=None):
        if (not ename):
            sys.stderr.write("openElement: bad args.")
            ename = "_UNKNOWN"

        # (FIX this -- code from multiXML for multiple stacks)
        curSchema = self.eStack[-1]
        if (not curSchema): raise ValueError("unknown schema '%s'" % (ns))

        curFrame = curSchema.theStack[-1]
        if (attrMap is None): attrMap = []
        oldESF = self.eStack[-1]
        newESF = ElementStackFrame(ename, attrMap,
            nsPrefix='', nsURI='', parent=None, userData=None)
        self.eStack.append(newESF)

        if (not curFrame): newESF.setLang(self.defaultLang)
        else: newESF.setLang(curFrame.lang)

        for i in (range(0,len(attrMap),2)):
            aname = attrMap[i]
            avalue = attrMap[i+1]
            if (aname == "xml:lang"):
                newESF.setLang(avalue)
            else:
                mat = re.search("^xmlns:",aname)
                if (mat):
                    if (aname == "xmlns:"): newESF.dftNameSpace = avalue
                    else: newESF.setNameSpace(aname,avalue)

        # UPDATE newNameSpaces and allNameSpaces
        self.allNameSpaces = oldESF.allNameSpaces
        for n in (self.newNameSpaces):
            self.allNameSpaces[n] = self.newNameSpaces
        return(newESF)

    def closeElement(self, ename=""):
        self.eStack.pop()

    def logTextNode(self):
        self.nTextNodes += 1

    def logPI(self):
        self.nPIs += 1

    def logComment(self):
        self.nComments += 1

    def logCDataStart(self):
        self.nComments += 1

    def logCDataEnd(self):
        self.nComments += 1

    ###########################################################################
    #
    def getDepth(self):
        return(len(self.eStack))

    def getCurrentElementName(self):
        return(self.eStack[-1].name)

    def getCurrentFQGI(self):
        fqgi = ""
        for e in (self.eStack):
            fqgi += e + "/"
        return(fqgi.rstrip("/"))

    # Return the position of the current element among its (element?) siblings.
    # This requires us to keep the list (or at least count) of all prior
    # siblings at each level.
    #
    def getElementChildNumber(self):
        d = self.getDepth()
        if (d < 2): return(1)
        return(len(self.eStack[-2].childTags))

    def isOpen(self, theTag):
        for e in (self.eStack):
            if (e.tag == theTag): return(1)
        return(0)

    def nOpen(self, theTag):
        n = 0
        for e in (self.eStack):
            if (e.tag == theTag): n += 1
        return(n)

    def findOutermost(self, tags):
        d = self.getDepth()
        for i in (range(0, d)):
            curTag = self.eStack[i].tag
            mat = re.search("\b"+curTag+"\b",tags)
            if (mat): return(i)
        return(None)

    def getCurrentAttrMap(self):           # ???
        curFrame = self.eStack[-1]
        return(curFrame.getAttrMap())

    def getCurrentAttr(self,aname):           # ???
        curFrame = self.eStack[-1]
        return(curFrame.getAttr(aname))

    def getCurrentLang(self):
        curFrame = self.eStack[-1]
        return(curFrame.getLang())

    def getCurrentNewNameSpaces(self):
        curFrame = self.eStack[-1]
        return(curFrame.newNameSpaces)

    def getElementInfo(self,n):
        return(self.eStack[-n])



    ###############################################################################
    # Namespace mapping. Note that only the *new* declarations are stored at
    # each level (element), since ns prefixes can be overridden. So we search
    # upward from the current element toward the root, and use the innermost
    # declaration in effect.
    #
    def getCurrentDefaultNamespace(self):
        return(self.allNameSpaces[""])

    def getDefaultNameSpace(self):
        for i in (range(self.getDepth()-1, 0, -1)):
            dns = self.eStack[i].dftNameSpace
            if (dns): return(dns)
        return("")

    def getNamespaceURIFromPrefix(self, prefix):
        #return(self.allNameSpaces[prefix])
        if (not prefix): return(self.getDefaultNameSpace())
        for i in (range(self.getDepth()-1, 0, -1)):
            csf = self.eStack[i]
            for j in (range(0, len(csf.newNameSpaces), 2)):
                if (csf.newNameSpaces[j] == prefix):
                    return(csf.newNameSpaces[j+1])
        return(None)

    def getNameSpacePrefixFromUri(self, uri):
        if (not uri): return("")
        for i in (self.getDepth()-1, 0, -1):
            csf = self.eStack[i]
            for i in (range(0, len(csf.newNameSpaces), 2)):
                if (csf.newNameSpaces[i+1] == uri):
                    return(csf.newNameSpaces[i])
        return(None)
