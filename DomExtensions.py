#!/usr/bin/env python
#
# DomExtensions -- useful methods on top of xml.dom.minidom.
#   See also my ReadDOM.py, which implements ground-up.
#
# Written 2010-04-01~23 by Steven J. DeRose (in Perl).
# ...
# 2012-01-10 sjd: Start port to Python.
# 2016-01-05: Fix previous/next. Add monkey-patching.
# 2018-02-07: Sync with new AJICSS Javascript API. Add/fix various.
# 2018-04-11: Support unescaping HTML named special character entities.
#
# To do:
#     Sync with XPLib.js
#     Add __getitem__() per RealDOM.py etc.
#     Make all select... use a generic axisSelect?
#     integrate collect/export/tostring/etc. with emitter.
#     Add insertPrecedingSibling, insertFollowingSibling, insertParent,
#         insertAfter
#     Implement splitNode (see pod)
#     Move in matchesToElements from mediaWiki2HTML
#     Find next node of given qgi? Select by qgi?
#     Add output options, perhaps via XmlOutput.pm?
#     Generate SAX stream from the DOM?
#     String to tag, like for quotes?
#     String to entity ref, like for quotes, dashes, odd spaces, etc.
#
from __future__ import print_function
import sys
import re
#import string
import codecs
import xml.dom, xml.dom.minidom
from xml.dom.minidom import Node

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2010-01-10",
    'language'     : "Python 3.7",
    'version_date' : "2018-11-27",
}
__version__ = __metadata__['version_date']

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring
else:
    string_types = str
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): str(s, encoding, errors)
    def cmp(a, b): return  ((a > b) - (a < b))

###############################################################################
#
def patchDOM(toPatch=xml.dom.Node):
    patchDom(toPatch)

def patchDom(toPatch=xml.dom.Node):
    """Monkey-patch needed methods into a given class.
    """
    testCase = getattr(xml.dom.Node, "selectAncestor", None)
    if (testCase and callable(testCase)): return

    toPatch.selectAncestor          = selectAncestor

    toPatch.selectChild             = selectChild
    toPatch.selectDescendant        = selectDescendant
    toPatch.selectDescendantR       = selectDescendantR

    toPatch.selectPreceding         = selectPreceding
    toPatch.selectPrevious          = selectPreceding
    toPatch.getPreceding            = getPreceding
    toPatch.getPrevious             = getPreceding
    toPatch.previous                = getPreceding

    toPatch.selectFollowing         = selectFollowing
    toPatch.selectNext              = selectFollowing
    toPatch.getFollowing            = getFollowing
    toPatch.getNext                 = getFollowing
    toPatch.next                    = getFollowing

    toPatch.selectPrecedingSibling  = selectPrecedingSibling
    toPatch.selectPreviousSibling   = selectPrecedingSibling
    toPatch.getPrecedingSibling     = getPrecedingSibling
    toPatch.getPreviousSibling      = getPrecedingSibling

    toPatch.selectFollowingSibling  = selectFollowingSibling
    toPatch.selectNextSibling       = selectFollowingSibling
    toPatch.getFollowingSibling     = getFollowingSibling
    toPatch.getNextSibling          = getFollowingSibling

    toPatch.getLeftBranch           = getLeftBranch
    toPatch.getRightBranch          = getRightBranch
    toPatch.getDepth                = getDepth
    toPatch.getFQGI                 = getFQGI
    toPatch.isWithin                = isWithin

    toPatch.getXPointer             = getXPointer
    toPatch.XPointerCompare         = XPointerCompare
    toPatch.nodeCompare             = nodeCompare
    toPatch.XPointerInterpret       = XPointerInterpret

    toPatch.nodeMatches             = nodeMatches
    toPatch.getInheritedAttribute   = getInheritedAttribute
    toPatch.getEscapedAttributeList = getEscapedAttributeList

    toPatch.removeWhiteSpaceNodes   = removeWhiteSpaceNodes
    toPatch.normalizeAllSpace       = normalizeAllSpace
    toPatch.insertPrecedingSibling  = insertPrecedingSibling
    toPatch.insertFollowingSibling  = insertFollowingSibling
    toPatch.insertParent            = insertParent
    toPatch.mergeWithFollowingSibling = mergeWithFollowingSibling
    toPatch.mergeWithPrecedingSibling = mergeWithPrecedingSibling
    toPatch.groupSiblings           = groupSiblings
    toPatch.promoteChildren         = promoteChildren

    toPatch.forEachNode             = forEachNode
    toPatch.forEachTextNode         = forEachTextNode
    toPatch.forEachElement          = forEachElement
    toPatch.forEachElementOfType    = forEachElementOfType

    toPatch.collectAllText          = collectAllText
    toPatch.collectAllXml2          = collectAllXml2
    toPatch.collectAllXml2r         = collectAllXml2r
    toPatch.collectAllXml           = collectAllXml
    toPatch.export                  = export

    toPatch.escapeXmlAttribute      = escapeXmlAttribute
    toPatch.escapeXml               = escapeXml
    toPatch.escapeASCII             = escapeASCII
    toPatch.unescapeXml             = unescapeXml
    toPatch.normalizeSpace          = normalizeSpace

    #NamedNodeMap.iteritems = nnmIteritems
    return



###########################################################################
# Access nodes via Python list notation, based on my paper:
#   DeRose, Steven J. JSOX: A Justly Simple Objectization for XML:
#   Or: How to do better with Python and XML. Presented at
#   Balisage: The Markup Conference 2014, Washington, DC, August 5-8, 2014.
#   In Proceedings of Balisage: The Markup Conference 2014.
#   Balisage Series on Markup Technologies, vol. 13 (2014).
#   https://doi.org/10.4242/BalisageVol13.DeRose02.
#
# FIX: Count from 0 or 1 for this?
# FIX: Perhaps allow regexes for name?
#
# For example:
#    myElement['p']       gets the 1st 'p' child
#    myElement['p':3]     gets the 3rd 'p' child
#    myElement[3:'p']         [same as ['p':3]]
#    myElement['p':3:8]   gets the 3rd through 7th 'p' children
#    myElement[3:8]       gets the 3rd through 7th children
#    myElement[3:8:'p']   of the 3rd through 7th children, gets the 'p's
#    myElement['@class']  get the 'class' attribute's value
#    myElement[1:10:2]    get every other childNodes from 1 to 10.
# Add:
#    myElement['@foo']    get the attribute named 'foo'.
#        Attribute are defined unordered, so ['@1'] is not allowed.
#        Perhaps extend [] to support any jQuery-style CSS selector?
#
def __getitem__(self, n1, n2=None, n3=None):
    nargs = 1
    if (n2 is not None): nargs = 2
    if (n3 is not None): nargs = 3

    if (nargs==1):
        if (isinstance(n1, int)):
            return(self.childNodes[n1])
        if (n1 == '*'):
            return(self._getChildNodesByName_('*'))
        if (n1.startswith('@')):
            return(self.attributes.getNamedItem(n1[1:]))
        return(self._getChildNodesByName_(n1)[0])

    elif (nargs==2):
        if (isinstance(n1, int)):
            if (isinstance(n2, int)):
                return(self.childNodes[n1:n2])
            else:
                return(self._getChildNodesByName_(n2)[n1])
        else:
            if (isinstance(n2, int)):
                return(self._getChildNodesByName_(n1)[n2])
            else:
                raise TypeError("Found [str, non-int] for a Node")

    else: # nargs==3
        if (isinstance(n1, int) and isinstance(n2, int)):
            if (isinstance(n3, int)):
                return(self.childNodes[n1:n2:n3])
            else:
                nodeList = self.childNodes[n1:n2]
                return(self._getListItemsByName_(nodeList, n3))
        elif (isinstance(n2, int) and isinstance(n3, int)):
            return(self._getChildNodesByName_(n1)[n2:n3])
        else:
            raise TypeError(
                "No 2 adjacent ints in [%s,%s,%s] for a Node." %
                (n1, n2, n3))

# Return a list of this node's children of a given element name
# '*' gets all element children, but no pi, comment, text....
#
def _getChildNodesByName_(self, name):
    cnodes = []
    for ch in self.childNodes:
        if (ch.nodeType==ELEMENT_NODE and
            (name=='*' or ch._nodeName==name)):
            cnodes.append(ch)
    return(cnodes)

def _getListItemsByName_(self, theList, name):
    inodes = []
    for item in theList:
        if (item.nodeType==ELEMENT_NODE and
            (name=='*' or item._nodeName==name)):
            inodes.append(item)
    return(inodes)


###############################################################################
# Methods to make minidom (or whatever) look like JS DOM.
#
def nnmIteritems(self):  # For NamedNodeMap, which lacks this.
    for k in self.keys:
        yield (k, self[k])

def outerHtml(self):
    t = self.getStartTag() + self.innerHTML() + self.getEndTag()
    return(t)

def innerHtml(self):
    t = ""
    for curNode in self.childNodes:
        ty = curNode.nodeType
        if (ty == TEXT_NODE):
            t += curNode.nodeValue
            break
        elif (ty == ELEMENT_NODE):
            t += curNode.getStartTag() +  curNode.innerHTML() + curNode.getEndTag()
            break
        elif (ty == CDATA_SECTION_NODE):
            t += "<![CDATA[%s]]>" % (curNode.textContent)
            break
        elif (ty == ENTITY_REFERENCE_NODE):
            break
        elif (ty == ENTITY_NODE):
            break
        elif (ty == PROCESSING_INSTRUCTION_NODE):
            t += "<?%s?>" % (curNode.textContent)
            break
        elif (ty == COMMENT_NODE):
            t += "<!--%s-->" % (curNode.textContent)
            break
        elif (ty == DOCUMENT_NODE or ty == DOCUMENT_FRAGMENT_NODE):
            t += curNode.getStartTag()
            for ch in (curNode.childNodes):
                t += ch.innerHTML
            t += curNode.getEndTag()
            break
        elif (ty == DOCUMENT_TYPE_NODE):
            t += "<!DOCTYPE %s>" % (curNode.textContent)
            break
        elif (ty == NOTATION_NODE):
            break

        elif (ty == ELEMENT_DECL_NODE):
            break
        elif (ty == ATT_DEF_NODE):
            break
        elif (ty == XML_DECL_NODE):
            t += '<?xml version="1.0" encoding="utf8"?>'
            break
        elif (ty == ATTLIST_DECL_NODE):
            pass
        #elif (ty == ATTRIBUTE_NODE):
        #    (done by ELEMENT_NODE)
        else:
            sys.exit("Unknown node type")
    return(t)

def innerText(self, sep=''):
    """Like usual innertext, but a function (instead of a property), and allows
    inserting something in between all the text nodes (typically a space,
    so text of list items etc. don't join up. But putting in spaces around
    HTML inlines like i and b, is occasionally wrong.
    """
    t = ""
    for curNode in self.childNodes:
        if (curNode.nodeType == Node.TEXT_NODE):
            t += sep + curNode.nodeValue
        elif (curNode.nodeType == Node.ELEMENT_NODE):
            t += sep + curNode.innerText
    return(t)


###############################################################################
# Methods for finding the nth node along a given axis, that has a given
# element type and/or attribute/value.
#
def selectAncestor(self, n=1, elType=None, aname=None, avalue=None):
    if (not elType): elType = ""
    self = self.getParentNode(self)
    while (self):
        if (self.nodeMatches(elType,aname,avalue)):
            n = n - 1
            if (n<=0):
                return(self)
        self= self.getParentNode(self)
    return(None)

# No selectAncestorOrSelf

def selectChild(self, n=1, elType=None, aname=None, avalue=None):
    if (not elType): elType = ""
    self = self.getFirstChild()
    while (self):
        if (self.nodeMatches(elType,aname,avalue)):
            n = n - 1
            if (n<=0):
                return(self)
        self = self.nextSibling()
    return(None)

def selectDescendant(self, n=1, elType=None, aname=None, avalue=None):
    return(selectDescendantR(n, elType, aname, avalue))

def selectDescendantR(self, n=1, elType=None, aname=None, avalue=None):
    if (self.nodeMatches(elType,aname,avalue)):
        n = n - 1
        if (n<=0): return(self)
    for ch in self.getChildNodes():
        node = self.getDescendantByAttributeR(ch,n,elType,aname,avalue)
        if (node):
            n = n - 1
            if (n<=0): return(node)
    return(None)


# No selectDescendantOrSelf

# Does not include ancestors
def selectPreceding(self, n=1, elType=None, aname=None, avalue=None):
    if (not elType): elType = ""
    cur=getPreceding(self)
    while (cur):
        if (isWithin(self, cur)): continue  # No ancestors, please.
        if (cur.nodeMatches(elType,aname,avalue)):
            n = n - 1
            if (n<=0): return(cur)
        cur=getPreceding(cur)
    return(None)

def getPreceding(self):  # FIX !!!
    node = self.getPreviousSibling()
    if (node): return(node.getFirstChildrightBranch())
    return(self.parentNode)

# Does not include descendants!
def selectFollowing(self, n=1, elType=None, aname=None, avalue=None):
    if (not elType): elType = ""
    self=getFollowing(self)
    while (self):
        if (self.nodeMatches(elType,aname,avalue)):
            n = n - 1
            if (n<=0): return(self)
        self=getFollowing(self)
    return(None)

# Does not include descendants!
def getFollowing(self):
    cur = self.rightBranch()
    while (cur):
        ns = cur.nextSibling()
        if (ns): return(ns)
        cur = cur.parentNode
    return(None)

def getFollowingAbsolute(self):
    if (self.firstChild): return(self.firstChild)
    cur = self
    while (cur):
        ns = cur.nextSibling()
        if (ns): return(ns)
        cur = cur.parentNode
    return(None)

def selectPrecedingSibling (self, n=1, elType=None, aname=None, avalue=None):
    if (not elType): elType = ""
    self = self.getPreviousSibling()
    while (self):
        if (self.nodeMatches(elType,aname,avalue)):
            n = n - 1
            if (n<=0): return(self)
        self = self.getPreviousSibling()
    return(None)

def getPrecedingSibling(self):
    return(self.getPreviousSibling())

def selectFollowingSibling(self, n=1, elType=None, aname=None, avalue=None):
    if (not elType): elType = ""
    self=getFollowingSibling(self)
    while (self):
        if (self.nodeMatches(elType,aname,avalue)):
            n = n - 1
            if (n<=0): return(self)
        self=getFollowingSibling(self)
    return(None)

def getFollowingSibling(self):
    return(self.getFollowingSibling())

# No select for root, self, attribute, or namespace axes.


###############################################################################
#
def getLeftBranch(self):
    while (self.firstChild): self = self.firstChild
    return(self)

def getRightBranch(self):
    while (self.lastChild): self = self.lastChild
    return(self)

def getDepth(self):
    d = 0
    while (self):
        d = d + 1
        self = self.getParentNode()
    return(d)

def getChildIndex(self): # First child is [0]!
    par = self.parentNode
    if (not par): return(-1)
    for i, sib in enumerate(par.childNodes):
        if sib.isSameNode(self): return(i)
    raise(ValueError)

def getFQGI(self):
    f = ""
    while (self):
        f = "/" + self.getNodeName() + f
        self = self.getParentNode()
    return f

def isWithinType(self, gi):
    while (self):
        if (self.getNodeName() == gi): return True
        self = self.getParentNode()
    return False

def isWithin(self, node):
    cur = self.getParentNode()
    while (cur):
        if (cur == node): return True
        cur = cur.getParentNode()
    return(False)


###############################################################################
# XPointer support
#
def getXPointer(self):
    f = ""
    while (self):
        f = "/%s%s" % (self.getParentNode().getChildIndex(self)+1, f)
        self = self.getParentNode()
    return(f)

def XPointerCompare(self, xp1, xp2):
    """Compare two XPointers for relative order.
    """
    t1 =  re.split(r'/',xp1)
    t2 =  re.split(r'/',xp2)
    i = 0
    while (i<len(t1) and i<len(t2)):
        if (t1[i] < t2[i]): return(-1)
        if (t1[i] > t2[i]): return(1)
        i = i + 1
    # At least one of them ran out...
    return(cmp(len(t1),len(t2)))

def nodeCompare(self, other):
    """Compare two nodes for order.
    """
    return(self.XPointerCompare(self.getXPointer(), other.getXPointer()))

def XPointerInterpret(self,  xp):
    """Given an XPointer string, find the node (if it exists).
    """
    document = self.ownerDocument()
    node = document.getDocumentElement()
    t = re.split(r'/',xp)
    if (re.match(r'^\d+',t[0])):               # Leading ID:
        idNode = document.getNamedNode(t[0])
        if (not idNode): return(None)
    i = 0
    while (i<len(t)):
        node = node.getChildAtIndex(t[i])
        if (not node): return(None)
        i = i + 1
    return(node)


###############################################################################
# @TODO UPDATE TO MATCH AJICSS.js
#
def nodeMatches(self, elType=None, aname=None, avalue=None):
    """Check if a node matches the supported selection constraints:
        An integer DOM nodeType number
        /regex/ to match node name (like BS4)
        '*' or '' (default) for any element
        '#' plus a DOM nodeType name (can omit '_NODE', or abbreviate)
        '#WSOTN' for non-white-space-only text nodes,
        '#NWSOTN' for anything that's not a WSOTN
        '#ET' for elements and non-white-space-only text nodes
        A literal node name

    If aname is non-nil, attribute must exist
    If avalue is non-nill, attribute aname must = avalue.
    Used by all the selectAXIS() methods.

    @TODO: Support nodeTypes in sync w/ Javascript packages.
    """
    if (elType and elType != ""):              # check type constraint:
        if (elType == "*"):
            if (self.getNodeType()!=1): return(0)
        else:
            if (self.getNodeName() != elType): return(0)

    if (not aname): return(1)
    if (self.getNodeName == "#text"): return(0)

    thisvalue = self.getAttribute(aname)
    if (not thisvalue):                              # attr specified, absent:
        return(0)
    if (not avalue or thisvalue == avalue):          # attr matches:
        return(1)
    return(0)


# Search upward to find an assignment to an attribute -- like xml:lang.
#
def getInheritedAttribute(self, aname):
    while (self):
        avalue = self.getAttribute(aname)
        if (avalue): return(avalue)
        self = self.getParentNode()
    return(None)

def getStartTag(self):
    buf = "<%s" % (self.nodeName)
    if (self.getAttribute('id')):
        buf += ' id="%s"' % (self.getAttribute('id'))
    for a in (self.attributes):
        if (a == 'id'): continue
        buf += ' %s="%s"' % (a, self.getAttribute(a))
    buf += ">"
    return buf

def getEndTag(self, comment=True):
    buf = "</%s>" % (self.nodeName)
    if (comment and self.getAttribute('id')):
        buf += '<!-- id="%s" -->' % (self.getAttribute('id'))
    return buf

# Assemble the entire attribute list, escaped as needed to write out as XML.
#
def getEscapedAttributeList(self):
    buf = ""
    if (not (self)): return(None)
    alist = self.getAttributes()
    if (not (alist)): return(buf)
    for i in (range(0,alist.getLength())):
        anode = alist.item(i)
        aname = anode.getName()
        avalue = escapeXmlAttribute(anode.getValue())
        buf = buf + " aname=\"" + avalue + "\""
    return(buf)


# Pull in code from JavaScript...
def addAttributeToken(self, attrName, token):
    raise NotImplementedError("No addAttributeToken")

def removeAttributeToken(self, attrName, token):
    raise NotImplementedError("No removeAttributeToken")


def removeWhiteSpaceNodes(self):
    # print "running removeWhiteSpaceNodesCB\n"
    forEachNode(removeWhiteSpaceNodesCB,None)

def removeWhiteSpaceNodesCB(self):
    if (not (self.getNodeName == "#text")): return
    t = self.getData()
    mat = re.search(r"[^\s]",t,"")
    if (mat): return
    self.getParentNode().removeChild(self)

def removeNodesByTagName(self, nodeName):
    nodes = self.getElementsByTagName(nodeName)
    ct = 0
    for node in nodes:
        node.parent.removeChild(node)
        ct += 1
    return ct

def untagNodesByTagName(root, nodeName):
    for t in root.getElementsByTagName(nodeName):
        tn = root.getDocument.createTextNode(t.innerText())
        t.parentNode.replaceChild(t, tn)

def renameByTagName(root, oldName, newName):
    for t in root.getElementsByTagName(oldName):
        t.nodeName = newName

def forceTagCase(root, upper=False, attributesToo=False):
    for t in getAllDescendants(root, [ TEXT_NODE ]):
        if (t.nodeType == ELEMENT_NODE):
            if (upper): t.nodeName = t.nodeName.toupper()
            else: t.nodeName = t.nodeName.tolower()
            if (attributesToo):
                for a, v in t.attributes.items():
                    if (a.isupper()): continue
                    t.removeAttribute(a)
                    t.setAttribute(a.toupper(), v)
    return

def getAllDescendants(root, excludeTypes=None):
    if ((not excludeTypes) or root.nodeType in excludeTypes):
        yield(root)
    for ch in root.childNodes:
        yield getAllDescendants(ch)
    return


###############################################################################
#
def normalizeAllSpace(self):
    forEachNode(normalizeAllSpaceCB, None)

def normalizeAllSpaceCB(self):
    if (self.getNodeName != "#text"): return
    self.setData(self.normalizeSpace(self.getData()))

def addElementSpaces(self, exceptions=None):
    """Add spaces around all elements *except* those specified.
    This is useful because most elements entail word-boundaries (say, things
    CSS would consider display:block). But little elements may not: such as
    HTML b, i, etc., and TEI var, sic, corr, etc.
    """
    raise NotImplementedError("No addElementSpaces")


###############################################################################
#
def insertPrecedingSibling(self, node):
    self.getParentNode().insertBefore(node, self)
    return(node)

def insertFollowingSibling(self, node):
    par = self.getParentNode()
    r = self.getFollowingSibling()
    if (r): par.insertBefore(node, r)
    else: par.appendChild(node)
    return(node)

# @TODO Allow a sequence of siblings
def insertParent(self, elType):
    new = self.getOwnerDocument.createElement(elType)
    self.getParentNode().replaceChild(new, self)
    new.appendChild(self)
    return(new)


###############################################################################
# Following-sibling goes away, but its children are appended to the node.
#
def mergeWithFollowingSibling(self, cur):
    if (not (cur)): return(None)
    sib = cur.getFollowingSibling()
    if (not sib): return False
    while (cur.hasChildNodes()):
        cur.appendChild(sib.getFirstChild())
    cur.getParentNode().removeChild(sib)

def mergeWithPrecedingSibling(self, cur):
    if (not (cur)): return(None)
    sib = cur.getPrecedingSibling()
    if (not sib): return False
    while (cur.hasChildNodes()):
        cur.insertBefore(sib.getLastChild(), cur.getFirstChild())
    cur.getParentNode().removeChild(sib)


###############################################################################
# Take a block of contiguous siblings and enclose them in a new intermediate
# parent node (which in inserted at the level they *used* to be at).
#
def groupSiblings(self, first, breakNode, newParentType):
    if (not first or not breakNode):
        raise ValueError("Must supply first and breakNode to groupSiblings\n")
    oldParent = first.getParentNode()
    oldParent2 = breakNode.getParentNode()
    if (not (oldParent == oldParent2)):
        raise ValueError("groupSiblings: first and last are not siblings!\n")
    newParent = first.getOwnerDocument().createElement(newParentType)
    oldParent.insertChildBefore(newParent,first)

    cont = cur = first
    while (cur):
        cont = cur.getFollowingSibling()
        moving = oldParent.removeChild(cur)
        newParent.insertBefore(moving,None)
        cur = cont


###############################################################################
# Remove the given node, promoting all its children.
#
def promoteChildren(self, ):
    parent = self.getParentNode()
    cur = self.getFirstChild()
    while (cur):
        cont = cur.getFollowingSibling()
        moving = self.removeChild(cur)
        parent.insertBefore(moving,parent)
        cur = cont
    parent.removeChild(self)



###############################################################################
# Traverse a subtree given its root, and call separate callbacks before
# and after traversing each subtree. Callbacks might, for example,
# respectively generate the start- and end-tags for the element. Callbacks
# are allowed to be undef if not needed.
#
# If a callback returns True, we stop traversing.
#
def forEachNode(self, callbackA=None, callbackB=None, depth=1):
    if (not (self)): return(1)
    name = self.getNodeName()
    if (callbackA):
        if (callbackA(name,depth)): return(1)
    if (self.hasChildNodes()):
        #print "Recursing for child nodes at level " . ($depth+1) . "\n"
        for ch in self.getChildNodes():
            rc = forEachNode(ch,callbackA,callbackB,depth+1)
            if (rc): return(1)
    if (callbackB):
        if (callbackB(name,depth)): return(1)
    return(0) # succeed


def forEachTextNode(self, callbackA=None, callbackB=None, depth=1):
    if (not (self)): return(1)
    name = self.getNodeName()
    if (callbackA and name == "#text"):
        if (callbackA(name,depth)): return(1)
    if (self.hasChildNodes()):
        #print "Recursing for child nodes at level " . ($depth+1) . "\n"
        for ch in self.getChildNodes():
            rc = forEachTextNode(ch,callbackA,callbackB,depth+1)
            if (rc): return(1)
    if (callbackB and name == "#text"):
        if (callbackB(name,depth)): return(1)
    return(0) # succeed


def forEachElement(self, callbackA=None, callbackB=None, depth=1):
    if (not (self)): return(1)
    name = self.getNodeName()
    if (callbackA and self.getNodeType==1):
        if (callbackA(name,depth)): return(1)
    if (self.hasChildNodes()):
        #print "Recursing for child nodes at level " . ($depth+1) . "\n"
        for ch in self.getChildNodes():
            rc = forEachElement(ch,callbackA,callbackB,depth+1)
            if (rc): return(1)
    if (callbackB and self.getNodeType==1):
        if (callbackB(name,depth)): return(1)
    return(0) # succeed


def forEachElementOfType(self, elementType, callbackA=None, callbackB=None, depth=1):
    if (not self):
        raise ValueError("No element specified.\n")
    if (not elementType):
        raise ValueError("Bad element type'" + elementType + "'specified.\n")
    name = self.getNodeName()
    if (callbackA and self.getNodeType==1 and
        re.match(elementType,self.getNodeName)):
        if (callbackA(name,depth)): return(1)
    if (self.hasChildNodes()):
        #print "Recursing for child nodes at level " . ($depth+1) . "\n"
        for ch in (self.getChildNodes()):
            rc = forEachElementOfType(
                ch,elementType,callbackA,callbackB,depth+1)
            if (rc): return(1)
    if (callbackB and self.getNodeType==1 and
        re.search(elementType,self.getNodeName)):
        if (callbackB(name,depth)): return(1)
    return(0) # succeed



###############################################################################
# Cat together all descendant text nodes, with delimiters between.
# cf innerText(), above.
#
def collectAllText(self, delim=" ", depth=1):
    if (not (self)): return("")
    name = self.getNodeName()
    textBuf = ""
    if (self.getNodeName() == "#text"):
        dat = self.getData()
        if (dat):
            if (depth>1): textBuf = delim + dat
            else: textBuf = dat
    elif (self.hasChildNodes()):
        for ch in self.getChildNodes():
            textBuf = textBuf + collectAllText(ch,delim,depth+1)
    return(textBuf)


# getTextNodesIn
#
# Based on https://stackoverflow.com/questions/298750/
#
def getTextNodesIn(node):
    """Return just the text nodes under the specified starting node.
    By default, includes descendant text nodes; should add option to do
    just direct ones.
    """
    textNodes = []
    if (node.nodeType == Node.TEXT_NODE):
        textNodes.append(node)
    else:
        for i in (range(len(node.childNodes))):
            textNodes.extend(node.getTextNodes(node.childNodes[i]))
    return textNodes


###############################################################################
# Collect a subtree as WF XML, with appropriate escaping. Can also
# put a delimiter before each start-tag; if it contains '\n', then the
# XML will also be hierarchically indented. -color applies.
#
# NOT FINISHED.
#
def collectAllXml2(self, delim=" ", useHtmlKnowledge=False):
    e = emitter("STRING")
    collectAllXml2r(e, delim, useHtmlKnowledge, 1)
    return(e.string)

# Following should be in xml.dom already
ELEMENT_NODE                 = 1
ATTRIBUTE_NODE               = 2
TEXT_NODE                    = 3
CDATA_SECTION_NODE           = 4
ENTITY_REFERENCE_NODE        = 5
ENTITY_NODE                  = 6
PROCESSING_INSTRUCTION_NODE  = 7
COMMENT_NODE                 = 8
DOCUMENT_NODE                = 9
DOCUMENT_TYPE_NODE           = 10
DOCUMENT_FRAGMENT_NODE       = 11
NOTATION_NODE                = 12

ELEMENT_DECL_NODE            = -101
ATT_DEF_NODE                 = -102
XML_DECL_NODE                = -103
ATTLIST_DECL_NODE            = -104

def collectAllXml2r (self, theEmitter, delim=" ",
    useHtmlKnowledge=False, depth=1):

    # Calculate whitespace to put around the element
    #
    nl = "\n"
    iString = "  "
    name = self.getNodeName()
    indent = postIndent = ""
    isEmpty = 0
    dtdk = None
    if (name == "#text"):
        #warn "got #text, type " . $self.getNodeType() . ", data: " .
        #    $self.getData() . "\n"
        # no indents
        pass

    if (useHtmlKnowledge):  # FIX
        if (not dtdk):
            dtdk = dtdKnowledge()
            dtdk.setupHTML()
        isEmpty = dtdk.isTagOfType(name,"empty")
        dtype = dtdk.getDisplayType(name)
        if (dtype and dtype != "inline"):
            indent = dtdk.getPreSpace(name)
            postIndent = dtdk.getPostSpace(name)
            indent = ""
            if (indent > 0):
                indent = (nl * indent) + (iString * depth)
            postIndent = ""
            if (postIndent > 0):
                postIndent = (nl * postIndent)
    else:
        mat = re.search(r'\n',delim,"")
        if (mat):
            indent = (iString * depth)
            postIndent = "\n"
        else:
            indent = delim

    # Assemble the data and/or markup
    #
    ntype = self.getNodeType()
    if (ntype == ELEMENT_NODE):  # 1 ELEMENT:
        textBuf = indent + "<" + name + getEscapedAttributeList(self)
        if (isEmpty): pass  #nop = 1
        else: textBuf = textBuf + ">"
        theEmitter.emit(textBuf)

        for ch in self.getChildNodes():
            collectAllXml2r(ch,theEmitter,delim,useHtmlKnowledge,depth+1)

        # If we or the last child ended with a line-break, indent end-tag.
        if (theEmitter.lastCharEmitted() == nl): # ELEMENT_NODE
            theEmitter.emit(iString * depth)
        theEmitter.emit("</"+name+">"+postIndent)

    elif (ntype == ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Unexpected attribute node.")

    elif (ntype == TEXT_NODE):                   # 3 TEXT
        theEmitter.emit(escapeXml(self.getData()))

    elif (ntype == CDATA_SECTION_NODE):          # 4
        nop = 1
    elif (ntype == ENTITY_REFERENCE_NODE):       # 5
        nop = 1
    elif (ntype == ENTITY_NODE):                 # 6
        nop = 1
    elif (ntype == PROCESSING_INSTRUCTION_NODE): # 7 PI
        theEmitter.emit("<?%s %s?>" % (self.getNodeName(), self.getData()))

    elif (ntype == COMMENT_NODE):                # 8 COMMENT
        theEmitter.emit(indent+"<!-- %s -->" % (self.getData()))
        mat = re.search(r'\n',delim,"")
        if (mat or useHtmlKnowledge): theEmitter.emit(nl)

    elif (ntype == DOCUMENT_NODE):               # 9
        nop = 1
    elif (ntype == DOCUMENT_TYPE_NODE):          # 10
        nop = 1
    elif (ntype == DOCUMENT_FRAGMENT_NODE):      # 11
        nop = 1
    elif (ntype == NOTATION_NODE):               # 12
        nop = 1
    else:
        raise ValueError("startCB: Bad DOM node type returned: %s." % ntype)
    return()



###############################################################################
# Collect a subtree as WF XML, with appropriate escaping. Can also
# put a delimiter before each start-tag; if it contains '\n', then the
# XML will also be hierarchically indented. -color applies.
#
def collectAllXml(self, delim=" ", useHtmlKnowledge=False, depth=1):
    name = self.getNodeName()
    ntype = self.getNodeType()

    # Calculate whitespace to put around the element
    #
    nl = "\n"
    iString = "  "
    indent = ""
    isEmpty = 0
    if (useHtmlKnowledge):
        if (not dtdk):
            dtdk = dtdKnowledge()
            dtdk.setupHTML()
        isEmpty = dtdk.isTagOfType(name,"empty")
        dtype = dtdk.getDisplayType(name)
        if (dtype and dtype != "inline"):
            indent = dtdk.getPreSpace(name)
            if (indent != ""):
                indent = (nl * indent) + (iString * depth)
    else:
        mat = re.search("nl",delim)
        if (mat): indent = (iString * depth)
        else: indent = delim

    # Assemble the data and/or markup
    #
    textBuf = ""
    if (ntype == ELEMENT_NODE):                  # 1 ELEMENT:
        textBuf += (iString*depth) + "<" + name + getEscapedAttributeList(self)
        if (isEmpty):
            textBuf = textBuf + "/>"
        else:
            textBuf = textBuf + ">"
            for ch in self.getChildNodes():
                textBuf = textBuf + collectAllXml(ch,delim,1,depth+1)
            mat = re.search("nl",textBuf,"")
            if (mat):
                textBuf = textBuf + (iString * depth)
            textBuf = textBuf + "</" + name + ">" + nl

    elif (ntype == ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Why are we seeing an attribute node?")

    elif (ntype == TEXT_NODE):                   # 3 TEXT
        textBuf = textBuf + escapeXml(self.getData())

    elif (ntype == CDATA_SECTION_NODE):          # 4
        pass
    elif (ntype == ENTITY_REFERENCE_NODE):       # 5
        pass
    elif (ntype == ENTITY_NODE):                 # 6
        pass
    elif (ntype == PROCESSING_INSTRUCTION_NODE): # 7 PI
        textBuf += "<?" + self.getNodeName() + " " + self.getData() + "?>"

    elif (ntype == COMMENT_NODE):                # 8 COMMENT
        textBuf = textBuf + indent + "<!--" + self.getData() + "-->"
        mat = re.search("\n",delim,"")
        if (mat or useHtmlKnowledge):
            textBuf = textBuf + nl

    elif (ntype == DOCUMENT_NODE):               # 9
        pass
    elif (ntype == DOCUMENT_TYPE_NODE):          # 10
        pass
    elif (ntype == DOCUMENT_FRAGMENT_NODE):      # 11
        pass
    elif (ntype == NOTATION_NODE):               # 12
        pass
    else:
        raise ValueError("startCB: Bad DOM node type returned: %d" % ntype)

    return(textBuf)
# collectAllXml


###############################################################################
# Write the whole thing to some file.
# See also XML::DOM::Node::toString(), printToFile(), printToFileHandle().
#
#global fhGlobal
fhGlobal = None # There was a BEGIN block here...

def export(self, someElement, fh, includeXmlDecl=True, includeDoctype=False):
    global fhGlobal
    fhGlobal = fh
    if (includeXmlDecl):
        print("<?xml version=\"1.0\" encoding=\"utf8\"?>")
    if (includeDoctype):
        rootGI = someElement.getName
        print("<!DOCTYPE " + rootGI + "PUBLIC '' '' []>")
    forEachNode(someElement,startCB,endCB,0)


def startCB(self):
    buf = ""
    typ = self.getNodeType
    if (typ == ELEMENT_NODE):                   # 1:
        buf = "<" + self.getNodeName + getEscapedAttributeList(self) + ">"
    elif (typ == ATTRIBUTE_NODE):               # 2
        pass
    elif (typ == TEXT_NODE):                    # 3
        buf = self.getData()
    elif (typ == CDATA_SECTION_NODE):           # 4
        buf = "<![CDATA["
    elif (typ == ENTITY_REFERENCE_NODE):        # 5
        pass
    elif (typ == ENTITY_NODE):                  # 6
        pass
    elif (typ == PROCESSING_INSTRUCTION_NODE):  # 7
        buf = "<?" + self.getData() + "?>"
    elif (typ == DOCUMENT_NODE):                # 8
        pass
    elif (typ == DOCUMENT_NODE):                # 9
        pass
    elif (typ == DOCUMENT_TYPE_NODE):           # 10
        buf = "<!DOCTYPE>"
    elif (typ == DOCUMENT_FRAGMENT_NODE):       # 11
        pass
    elif (typ == NOTATION_NODE):                # 12
        pass

    # Following are extensions to DOM (unfinished)
    elif (typ == ELEMENT_DECL_NODE):            # 13
        buf = "<!ELEMENT " + self.getNodeName() + " ANY>"
    elif (typ == ATT_DEF_NODE):                 # 14
        pass
    elif (typ == XML_DECL_NODE):                # 15
        buf = "<?xml version=\"1.0\" encoding=\"utf8\">"
    elif (typ == ATTLIST_DECL_NODE):            # 16
        buf = "<!ATTLIST " + self.getNodeName() + "\n"
    else:
        print("startCB: Bad DOM node type returned: self->getNodeType.\n")
        exit(0)
    print(fhGlobal, buf)


def endCB(self):
    buf = ""
    typ = self.getNodeType()

    if (typ == ELEMENT_NODE):                   # 1:
        buf = "</" + self.getNodeName() + ">"
    elif (typ == ATTRIBUTE_NODE):               # 2
        pass
    elif (typ == TEXT_NODE):                    # 3
        pass
    elif (typ == CDATA_SECTION_NODE):           # 4
        buf = "]]>"
    elif (typ == ENTITY_REFERENCE_NODE):        # 5
        pass
    elif (typ == ENTITY_NODE):                  # 6
        pass
    elif (typ == PROCESSING_INSTRUCTION_NODE):  # 7
        pass
    elif (typ == COMMENT_NODE):                 # 8
        pass
    elif (typ == DOCUMENT_NODE):                # 9
        pass
    elif (typ == DOCUMENT_TYPE_NODE):           # 10
        pass
    elif (typ == DOCUMENT_FRAGMENT_NODE):       # 11
        pass
    elif (typ == NOTATION_NODE):                # 12
        pass

    # Following are extensions to DOM
    elif (typ == ELEMENT_DECL_NODE):            # 13
        pass
    elif (typ == ATT_DEF_NODE):                 # 14
        pass
    elif (typ == XML_DECL_NODE):                # 15
        pass
    elif (typ == ATTLIST_DECL_NODE):            # 16
        buf = ">\n"
    else:
        print("endCB: Bad DOM node " + typ + " returned: " +
              self.getNodeType + ".\n")
        exit(0)

    print(fhGlobal, buf)

# END of DomExtensions definitions


###############################################################################
#
def escapeXmlAttribute(s):
    # We quietly delete the non-XML control characters!
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]',"",s)
    s = re.sub(r'&', "&amp;",   s)
    s = re.sub(r'<', "&lt;",    s)
    s = re.sub(r'"', "&quot;",  s)
    return(s)

def escapeXml(s):
    # We quietly delete the non-XML control characters!
    s = re.sub("[\x00-\x08\x0b\x0c\x0e-\x1f]","",s)
    s = re.sub(r'&',   "&amp;",  s)
    s = re.sub(r'<',   "&lt;",   s)
    s = re.sub(r']]>', "]]&gt;", s)
    return(s)

def escapeASCII(s):
    s = re.sub(r'([^[:ascii:]])r', escASCIIFunction, s)
    s = escapeXml(s)
    return(s)

def escASCIIFunction(mat):
    return "&#x%04x;" % (ord(mat.group[1]))

def unescapeXml(s):
    return re.sub(r'&(#[xX])?(\w+);', unescapeXmlFunction, s)

def unescapeXmlFunction(mat):
    from htmlentitydefs import name2codepoint, codepoint2name
    if (len(mat.group(1)) == 2):
        return unichr(int(mat.group[2], 16))
    elif (mat.group(1)):
        return unichr(int(mat.group[2], 10))
    elif (mat.group(2) in name2codepoint):
        return name2codepoint[mat.group(2)]
    else:
        raise ValueError("Unrecognized entity: '%s'." % (mat.group(0)))

# This only normalizes *XML* whitespace,
# per the XML spec, section 2.3, grammar rule 3.
#
xmlSpaceChars = " \t\r\n"
xmlSpaceRegex = re.compile("[%s]+" % (xmlSpaceChars))
#
def normalizeSpace(self, s):
    s = re.sub(xmlSpaceRegex, " ", s)
    s = s.strip(xmlSpaceChars)
    return(s)


###############################################################################
###############################################################################
# Various places to put output data.
#
class emitter:
    def __init__(self, where, arg=None):
        self.where        = where
        self.lastChar    = ""
        self.fh          = None
        self.string      = ""
        self.file        = ""
        self.cb          = ""

        if (where == "STRING"):
            self.string = ""
        elif (where == "FILE"):
            self.file = arg
            self.fh = codecs.open(self.file, "rb", encoding="utf-8")
        elif (where == "FH"):
            self.fh = arg
        elif (where == "CALLBACK"):
            self.cb = arg
        else:
            print("new emitter: unknown 'where': '" + where + "'.")
            sys.exit(0)
        return(None)

    def emit(self, text):
        if (len(text)>0):
            self.lastChar = text[len(text):-1]
        if (self.where == "STRING"):
            self.string += text
        elif (self.where == "FILE"):
            self.fh.write(text)
        elif (self.where == "FH"):
            self.fh.write(text)
        else:
            self.cb(text)

    def lastCharEmitted(self): return(self.lastChar)



###############################################################################
###############################################################################
# Index should be a separate object.
# Adds every element that has a given attribute, to a hash, keyed on that
# attribute's value. Hopes the values are unique.
#
class DomIndex:
    def __init__(self, document, aname):
        self.theIndex = {}
        self.index = None
        node = document.getDocumentElement()
        while (node):
            if (node.getNodeType==1):               # elements:
                key = node.getAttribute(aname)
                if (key): self.theIndex[key] = node
            node = node.getFolowing()
        self.document = document
        self.attrName = aname
        return(None)

    def find(self, avalue):
        indexRef = self.theIndex
        self.index = indexRef
        return(self.index[avalue])



###############################################################################
###############################################################################
###############################################################################
#

pod = """

=pod

=head1 Description

DomExtensions.py

***UNFINISHED***

An XML-manipulation package that sits on top of XML::DOM
and provides higher-level, XPath-like methods.
You can use I<patchDOM>() to monkey-patch these routines into a class
(default: I<xml.dom.Node>).

It's very often useful to walk around the XPath 'axes' in a DOM tree.
When doing so, it's often useful to consider only element nodes,
or only #text nodes, or only element nodes of a certain element type, or
with a certain attribute or attribute-value pair.

=head2 Node-selection methods

For the relevant XPath axes there are methods that will return the n-th
node of a given type and/or attribute along that axis.
For example (using the Child axis, but you can substitute
Descendant, PrecedingSibling, FollowingSibling, Preceding, Following,
or Ancestor:

    selectChild(node,n,type,attributeName,attributeValue)

This will return the I<n>th child of I<node> which:
is of the given element I<type>,
and has the given I<attributeName>=I<attributeValue> pair.

=over

=item * I<n> must currently be positive, though using negative numbers
to count back from the end will likely be added.

=item * If I<type> is undefined or '', any node type is allowed.
If it is '*', any *element* is allowed.
In either case, attribute constraints may still apply.

=item * If I<attributeName> is undefined or '', no attribute is required.

=item * If I<attributeValue> is undefined or '', the attribute named
by I<attributeName> must be present, but may have any value (including '').

The self, ancestor-or-self, descendant-or-self, attribute, and namespace
axes are I<not> supported for I<select>.

This is far
less power than XPath provides, but it facilitates many programming tasks,
such as scanning for all elements of a given type (which I deem very common).

=back


=head3 Tree information and navigation methods

=over

=item * B<getInheritedAttribute(node,name)>

Return the value of attribute I<name>, from the first node along the
I<ancestor-or-self> axis of I<node> that specifies it.
Thus, the attribute's value is inherited down the tree, similar to I<xml:lang>.

=item * B<leftBranch>(node)

Return the leftmost descendant of I<node>.
If I<node>'s first child has no children of its own, then it is
also I<node>'s first descendant; otherwise, it will not be.

=item * B<rightBranch>(node)

Return the rightmost (last) descendant of I<node>.

=item * B<getDepth>(node)

Return how deeply nested I<node> is (the document element is I<1>).

=item * B<isWithin>(I<node>, I<type>)

Return 1 if I<node> is, or is within, an element of the given I<type>,
otherwise return 0.

=item * B<getFQGI>(node)

Return the list of element types of I<node>'s
ancestors, from the root down, separated by '/'.
For example, "html/body/div/ul/li/p/b".
B<Note>: An FQGI does I<not> identify a specific element instance or location
in a document; for that, see I<getXPointer>().

=item * B<getXPointer>(node)

Return the XPointer child sequence to I<node>.
That is, the list of child-numbers for all the ancestors of the node, from
the root down, separated by '/'. For example, "1/1/5/2/1".
This is a fine unique name for the node's location in the document.

=item * B<XPointerCompare(x1,x2)>

Compare two XPointer child-sequences (see I<getXPointer>)
for relative document order, returning -1, 0, or 1.
This does not require actually looking at a document, so no document or
node is passed.

=item * B<nodeCompare(n1,n2)>

Compare two nodes for document order, returning -1, 0, or 1.

=item * B<XPointerInterpret(document,x)>

Interpret the XPointer child sequence in the string
I<x>, in the context of the given I<document>,
and return the node it identifies (or undef if there is no such node).

=item * B<getEscapedAttributeList>(node)

Return the entire attribute list for
I<node>, as needed to go within a XML start-tag. The attributes will be
quoted using the double-quote character ('"'), and any <, &, or " in them
will be replaced by the appropriate XML predefined charcter reference.

=back


=head2 Large-scale tree operations

=over

=item * B<removeWhiteSpaceNodes>(node)

Delete all white-space-only text nodes that are descendants of I<node>.

=item * B<normalizeAllSpace>(node)

Do the equivalent of XSLT normalize-space()
on all text nodes in the subtree headed at I<node>.
B<Note>: This is I<not> the same as the XML::DOM::normalize() method, which
instead combines adjacent text nodes.

=item * B<insertPrecedingSibling>(I<node, newNode>)

=item * B<insertFollowingSibling>(I<node, newNode>)

=item * B<insertParent>(I<node, type>)

=item * B<mergeWithFollowingSibling>(node)

The following-sibling of I<node> is deleted, but its text content
is appended to I<node>.
This drops any sub-structure of the current and sibling.
New. See also the C<diffCorefs> command.

=item * B<mergeWithPrecedingSibling>(node)

=item * B<groupSiblings(node1,node2,typeForNewParent)>

Group all the nodes from I<node1> through I<node2> together, under a
new node of type I<typeForNewParent>. Fails if the specified nodes are
not siblings or are not defined.

=item * B<promoteChildren>(node)

Remove I<node> but keep all its children, which becomes siblings at the same
place where I<node> was.

=item * B<splitNode>(node, childNode, offset)

Breaks I<node> into 2 new sibling nodes of the same type.
The children preceding and including node I<childNode> end up
under the first resulting sibling node; the rest under the second.
However, if I<childNode> is a text node and I<offset> is provided,
then I<childNode> will also be split, with the characters preceding and
including I<offset> (counting from 1) becoming a final text node under
the first new sibling node, and the rest become an initial text node
under the second.
(not yet supported)


=item * B<forEachNode(node,preCallback,postCallback)>

Traverse the subtree headed at I<node>,
calling the callbacks before and after traversing each node's subtree.

=item * B<forEachTextNode(node,preCallback,postCallback)>

Like I<forEachNode>(), but callbacks are I<only> called when at text nodes.

=item * B<forEachElement(node,preCallback,postCallback)>

Like I<forEachNode>(), but callbacks are I<only> called when at element nodes.

=item * B<forEachElementOfType(node,type,preCallback,postCallback)>

Like I<forEachNode>(), but callbacks are I<only> called when at
element nodes whose type name matches I<type> (which may be a regex).

=item * B<collectAllText(node,delimiter)>

Concatenate together the content of
all the text nodes in the subtree headed at I<node>,
putting I<delimiter> in between.

=item * B<collectAllXml2>(node,delimiter,useLayoutInformation,inlines)

(newer version, in testing)

=item * B<collectAllXml>(node,delimiter,useLayoutInformation,inlines)

Generate the XML representation for the subtree headed at I<node>.
It knows about elements, attributes, pis, comments, and appropriate escaping.
However, it won't do anything for CDATA sections (other than escape as
normal text), XML Declaration, DOCTYPE, or any DTD nodes.

If I<delimiter> contains a newline, the subtree
will include newlines and indentation.
If I<useHtmlLayoutInformation> is True, HTML-specific element information
will be used to help with pretty-printing.

=item * B<export(element, fileHandle, includeXmlDecl, includeDoctype)>

Save the subtree headed at I<element> to the I<fileHandle>.
If I<includeXmlDecl> is present and True, start with an XML declaration.
If I<includeDoctype> is present and True, include a DOCTYPE declaration,
using I<element>'s type as the document-element name, and include any
DTD information that was available in the DOM (unfinished).
See also XML::DOM::Node::toString(),
XML::DOM::Node::printToFile(), XML::DOM::Node::printToFileHandle().

=back


=head2 Index (internal package)

=over

=item * B<buildIndex>(attributeName)

Return a hash table in which each
entry has the value of the specified I<attributeName> as key, and the element on
which the attribute occurred as value. This is similar to the XSLT 'key'
feature.

=item * B<find(value)>

=back


=head2 Character stuff (internal package)

(also available in I<SimplifyUnicode.pm>)

=over

=item * B<escapeXmlAttribute(string)>

Escape the string as needed for it to
fit in an attribute value (amp, lt, and quot).

=item * B<escapeXml(string)>

Escape the string as needed for it to
fit in XML text content (amp, lt, and gt when following ']]').

=item * B<escapeASCII(string)>

Escape the string as needed for it to
fit in XML text content, *and* recodes and non-ASCII characters as XML
numeric characters references.

=item * B<unescapeXml(string)>

Change XML numeric characters references, as
well as references to the 5 pre-defined XML named entities, into the
corresponding literal characters.

=back



=head1 Related commands

C<SimplifyUnicode.pm> -- Reduces variations on Roman characters, ligatures,
dashes, whitespace charadters, quotes, etc. to more basic forms.

C<fakeParser.pm> -- a mostly-conforming XML/HTML parser, but able to survive
most WF errors and correct some. Supports push and pull interface, essentially
SAX.

C<XmlOutput.pm> -- Makes it easy to produce WF XML output. Provides methods
for escaping data correctly for each relevant context; knows about character
references, namespaces, and the open-element context; has useful methods for
inferring open and close tags to keep things in sync.

C<dtdKnowledge.pm> -- Provides pretty-printing specs for I<collectAllXml>().



=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see http://www.derose.net/steve/utilities/.

=cut
"""
