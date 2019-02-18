#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
###############################################################################
# A more complete DOM, unlike minidom, which is reasonable but incomplete,
# or ElementTree, which is... problematic.
#
# SEE ALSO my DomExtensions.py (should sync APIs).
#
# By Steven J. DeRose, ~Feb 2016.
# 2018-04-18: lint.
#
# To do:
#     Define these abstracts:
#
#     Split into 2 layers: one just DOM, one my extensions.
#     Finish
#     Hook up additional parsers (html5lib, YML)
#     Integrate 'DOMinµs'
#     No need to keep sibling chains when you have ownerDoc and childNodes[];
#         minimal speed increase.
#     SEE: 'NoDOM' document.
#     Sync completely with DomExtensions and XPLib.
#     Integrate dominus?
#     Add a way to produce NLTK-style stuff:
#         sent, tok, pos, etc; but keeping all the orig. structure.
#
import sys
import re
#import strings
import collections
import codecs
#import xml.dom.minidom
from xml.dom.minidom import Node as miniNode
#from xml.dom.minidom import Document as miniDocument

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    import HTMLParser
    string_types = basestring
else:
    from html.parser import HTMLParser
    string_types = str
    def unichr(n): return chr(n)

__version__  = "0.1"
__author__   = "Steven J. DeRose"
__origDate__ = "2016-02-06"
__revDate__  = "2018-04-18"
__license__  = "Creative Commons Attribute-Share-alike 3.0"


###############################################################################
# General utilities
#
XMLEntities = {
     '&quo;'  : '"',
     '&apos;' : "'",
     '&lt;'   : '<',
     '&gt;'   : '>',
     '?&gt;'  : '?>',
}

escMap = {
    '"'       : '&quo;',
    "'"       : '&apos;',
    '<'       : '&lt;',
    '>'       : '&gt;',
    '?>'      : '?&gt;',
    '-->'     : '- - >',
    ']]>'     : '&rsqb;]>',
}
def _escaper(mat):
    return(escMap[mat.group(1)])
def escapeAttribute(s):
    return(re.sub(r'(["<&])', _escaper, s))
def escapeText(s):
    return(re.sub(r'(<|&|]]>])', _escaper, s))
def escapePI(s):
    return(re.sub(r'(\?>)', _escaper, s))
def escapeComment(s):
    return(re.sub(r'(-->)', _escaper, s))


###############################################################################
# Useful enumerations
#

# Node types (sync w/ minidom.Node)
#
UNSPECIFIED_NODE            = 0  ### Not DOM
ELEMENT_NODE                = 1
ATTRIBUTE_NODE              = 2
TEXT_NODE                   = 3
CDATA_SECTION_NODE          = 4
ENTITY_REFERENCE_NODE       = 5
ENTITY_NODE                 = 6
PROCESSING_INSTRUCTION_NODE = 7
COMMENT_NODE                = 8
DOCUMENT_NODE               = 9
DOCUMENT_TYPE_NODE          = 10
DOCUMENT_FRAGMENT_NODE      = 11
NOTATION_NODE               = 12

TROJAN_START_NODE           = 32
TROJAN_END_NODE             = 33

nodeTypeList = [
    'UNSPECIFIED_NODE',             # 0  ### Not DOM
    'ELEMENT_NODE',                 # 1
    'ATTRIBUTE_NODE',               # 2
    'TEXT_NODE',                    # 3
    'CDATA_SECTION_NODE',           # 4
    'ENTITY_REFERENCE_NODE',        # 5
    'ENTITY_NODE',                  # 6
    'PROCESSING_INSTRUCTION_NODE',  # 7
    'COMMENT_NODE',                 # 8
    'DOCUMENT_NODE',                # 9
    'DOCUMENT_TYPE_NODE',           # 10
    'DOCUMENT_FRAGMENT_NODE',       # 11
    'NOTATION_NODE',                # 12
]

trojanTypeList = {
    'TROJAN_START_NODE'           : 32,  ### Not DOM
    'TROJAN_SUSPEND_NODE'         : 33,  ### Not DOM
    'TROJAN_RESUME_NODE'          : 34,  ### Not DOM
    'TROJAN_END_NODE'             : 35,  ### Not DOM
}


# Attribute default values (not yet used)
ATTRIBUTE_NODEFAULT         = 0
ATTRIBUTE_IMPLIED           = 1
ATTRIBUTE_REQUIRED          = 2
ATTRIBUTE_FIXED             = 3
ATTRIBUTE_CONST             = 4  # Requires extra data...


# Attribute declared values (aka datatypes) (not yet used)
#
ATTRIBUTE_NOTYPE        = 0
ATTRIBUTE_CDATA         = 1
ATTRIBUTE_ID            = 2
ATTRIBUTE_IDREF         = 3
ATTRIBUTE_IDREFS        = 4
ATTRIBUTE_NMTOKEN       = 5
ATTRIBUTE_NMTOKENS      = 6
ATTRIBUTE_ENTITY        = 7
ATTRIBUTE_ENTITIES      = 8
ATTRIBUTE_NOTATION      = 9
ATTRIBUTE_ENUM          = 10  # Requires extra data...

# Very basic additional datatypes (not yet used)  ### Not DOM
#
ATTRIBUTE_BOOLEAN       = 16
ATTRIBUTE_UNSIGNED      = 17
ATTRIBUTE_INTEGER       = 18
ATTRIBUTE_REAL          = 19
ATTRIBUTE_DATE          = 20
ATTRIBUTE_TIME          = 21
ATTRIBUTE_DATETIME      = 22

# Fancier extensions (not yet used)  ### Not DOM
#
ATTRIBUTE_IDSTEP        = 32
ATTRIBUTE_TROJAN_START  = 33
ATTRIBUTE_TROJAN_END    = 34
ATTRIBUTE_URI           = 35
ATTRIBUTE_XPOINTER      = 36
ATTRIBUTE_XPATH         = 37
ATTRIBUTE_SVGPATH       = 38
ATTRIBUTE_SEXP          = 39
ATTRIBUTE_REGEX         = 40  # There are flavors, though...
ATTRIBUTE_JSON          = 41


# Exceptions
#     w3.org/TR/1998/REC-DOM-Level-1-19981001/level-one-core.html
#     http://stackoverflow.com/questions/1319615
#
# FIX: Hook these up where appropriate
#
class INDEX_SIZE_ERR(Exception):              pass  # 1
class DOMSTRING_SIZE_ERR(Exception):          pass  # 2
class HIERARCHY_REQUEST_ERR(Exception):       pass  # 3
class WRONG_DOCUMENT_ERR(Exception):          pass  # 4
class INVALID_CHARACTER_ERR(Exception):       pass  # 5
class NO_DATA_ALLOWED_ERR(Exception):         pass  # 6
class NO_MODIFICATION_ALLOWED_ERR(Exception): pass  # 7
class NOT_FOUND_ERR(Exception):               pass  # 8
class NOT_SUPPORTED_ERR(Exception):           pass  # 9
class INUSE_ATTRIBUTE_ERR(Exception):         pass  # 10



###############################################################################
# MLDeclaration: XML declaration info, or similar if we support other syntaxes.
#
class MLDeclaration:
    def __init__(self, language='XML', version='1.0', encoding='utf-8', standalone=True):
        self.caseInsensitive = True
        self.language = language
        self.XMLSettings = {
            'version'    :  version,
            'encoding'   :  encoding,
            'standalone' :  standalone,
        }
        self.HTMLSettings = {
            'version'    :  '4',
            'strict'     :  False,
        }
        self.YMLSettings = {
            'yml'                    : True,  # Global enable
            'attrsInPIs'             : True,
            'expandEntities'         : True,
            'entitiesInPIs'          : True,
            'shortAttrs'             : True,
            'ymlOmitEnd'             : True,
            'ymlEmptyEnd'            : "</>",
            'ymlQuad'                : unichr(0x11),  # ^Q
            'ymlReopen'              : unichr(0x12),  # ^R
            'ymlStartAttributes'     : unichr(0x13),  # ^S
            'ymlTerminateAttributes' : unichr(0x14),  # ^T
            'ymlUp'                  : unichr(0x15),  # ^U
       }


###############################################################################
#
#
class simplisticSchemaHTML:
    def __init__(self):
        return

    inlines = [
        "del", "iframe", "a", "abbr", "acronym", "b", "bdo", "big",
        "cite", "code", "dfn", "em", "i", "img", "ins", "kbd",
        "q", "s", "small", "span", "strike", "strong", "sub", "sup",
        "tt", "var", "center", "dir", "font", "samp", "strike", "u",
    ]
    empties = [
        "area", "base", "br", "col", "frame", "hr", "img", "input",
        "isindex", "link", "meta", "menu", "param",
    ]
    okChild = {  # FIX: More entries needed...
        "html":  [ "head", "body" ],
        "head":  [ "title", "meta", "script", "link", "base" ],
        "p":     [ "li", ],
        "ul":    [ "li", ],
        "ol":    [ "li", ],
        "dl":    [ "dh", "dd" ],
        "li":    [ "dl", "ul", "ol", "p", "blockquote", ],
        "div":   [ "div", "dl", "ul", "ol", "p", "blockquote", ],
        "table": [ "thead", "tbody", "tfoot", "tr" ],
        "thead": [ "tr" ],
        "tbody": [ "tr" ],
        "tfoot": [ "tr" ],
        "tr":    [ "td", "th" ],
        # body, h1...h6, td, th, pre
    }

    # Since Python HTMLParser (of "import soul" fame???) cannot infer
    # omitted end-tags, here's a quick hack that will cover nearly all of
    # them for HTML. Unlisted types can contain all/only inlines.
    #
    # There are some exception: ins contain contain anything...
    # What should happen for completely unknown elements as par or ch?
    #
    def canContain(self, par, ch):
        if (par in DOMBuilderHTML.empties):      return False
        if (ch  in DOMBuilderHTML.inlines):      return True
        if (par in DOMBuilderHTML.inlines):      return False
        if (par not in DOMBuilderHTML.okChild):  return True
        if (ch  in DOMBuilderHTML.okChild[par] or
            "*" in DOMBuilderHTML.okChild[par]): return True
        return False



###############################################################################
# Classes Attr and NamedNodeMap -- for attribute lists
#
# This is a little weird, because each Node owns a NamedNodeMap (which is
# not a subclass of Node), and the NamedNodeMap then owns an array and a hash
# of Attr objects (Attr *is* a subclass of Node).
#
# FIX: Should this really be a subclass of Node?
# FIX: Need to be able to retrieve with or without namespace.
# FIX: Deal with case-ignorance for HTML
#
class Attr:
    def __init__(self, name, value, nsPrefix=None, nsURI=None, ownerDocument=None, parentNode=None):
        self.ownerDocument = ownerDocument
        self.parentNode    = parentNode
        self.name          = name
        self.value         = value
        self.nsPrefix      = nsPrefix
        self.nsURI         = nsURI

        # Acc. DOM, Attributes have a parent (the element), but are not
        # listed in the element childNodes.
        #
        if (parentNode and parentNode.nodeType!=ELEMENT_NODE):
            raise ValueError("parentNode for attr '%s' is %d, not %d." %
                (name, parentNode.nodeType, ELEMENT_NODE))

    def isEqualAttr(self, other):
        if (self.name       == other.name and
            self.value      == other.value and
            self.nsPrefix   == other.nsPrefix and
            self.nsURI      == other.nsURI): return True
        return False

# FIX: use OrderedDict, or not?
#
class NamedNodeMap(collections.OrderedDict):
    def __init__(self, ownerDocument=None, parentNode=None):
        self.ownerDocument = ownerDocument
        self.parentNode    = parentNode
        self.theAttrs      = []        # Array of 'Attr' objects
        self.byLocalName   = {}        # Same objects, indexed by name

    def __len__(self):
        return len(self.theAttrs)

    def getNamedItem(self, name):
        if (name in self.byLocalName):
            return(self.byLocalName[name])
        return(None)

    def setNamedItem(self, name, value,):
        parts = name.split(':',1)
        if (len(parts) == 2):
            nsPrefix = parts[0]
            localName = parts[1]
        else:
            nsPrefix = None
            localName = name

        if (localName in self.byLocalName):
            self.byLocalName[localName].name = value
        newAttr = Attr(localName, value, nsPrefix, None,        # FIX
            self.ownerDocument, self.parentNode)
        self.theAttrs.append(newAttr)
        self.byLocalName[name] = newAttr
        # FIX: Also make in index by qname?

    def removeNamedItem(self, name):
        if (name in self.byLocalName):
            del self.byLocalName[name]
            pos = self.getIndexOf(name)
            if (pos is not None): del self.theAttrs[pos]

    def getIndexOf(self, name):  ### Not DOM
        for i in range(self.theAttrs):
            anode = self.theAttrs[i]
            if (anode.name == name): return(i)
        return(None)

    def item(self, index):
        if (index >=0 and index < len(self.theAttrs)):
            return(self.theAttrs[index])
        return(None)

    def tostring(self):
        s = ""
        for key, val in self.items():
            s += ' %s="%s"' % (key, escapeAttribute(val))
        return(s)

    def getNamedItemNS(self, name):
        raise NotImplementedError

    def setNamedItemNS(self, name, value):
        raise NotImplementedError

    def removeNamedItemNS(self, name):
        raise NotImplementedError

    def clone(self):
        other = NamedNodeMap(
            ownerDocument=self.ownerDocument, parentNode=self.parentNode)
        for anode in self.theAttrs:
            other.setNamedItem(anode._nodeName, anode.data)
        return other


###############################################################################
# Node
#
# Almost everything else is a subclass of Node.
# Node has the information about naming and tree relationships.
# Only Elements (and Document) have childNodes, so most child-related
# methods, as well as HTML things like @class, @id, events, etc. go there.
# Most other subclasses do little or nothing extra, and are only ever leaves.
#
class myNode(miniNode):  # Based on the xml.dom.minidom "Node"
    def __init__(self, srcNode=None):
        if (srcNode):
            self.nsPrefix        = srcNode.nsPrefix
            self.nsURI           = srcNode.nsURI
            self.nodeValue       = srcNode.nodeValue
            self.attributes      = srcNode.attributes
            self.nsAttributes    = srcNode.nsAttributes
            self.data            = srcNode.data
            self.userData        = srcNode.userData
            if (hasattr(srcNode, 'nsPrefix')):
                self.nsPrefix    = srcNode.nsPrefix
            else:
                self.nsPrefix    = ""
            # Relationships
            self.ownerDocument   = srcNode.ownerDocument
            self.parentNode      = srcNode.parentNode
            self.childNodes      = srcNode.childNodes
            self.previousSibling = srcNode.previousSibling
            self.nextSibling     = srcNode.nextSibling

            # Meta
            self.startLoc        = srcNode.startLoc
            self.__milestone__   = srcNode.__milestone__
            self.__otherEnd__    = srcNode.__otherEnd__
        return

class Node(object):

    def __init__(self, nodeType=UNSPECIFIED_NODE, ownerDocument=None):
        if (not isinstance(nodeType, int)):
            print("nodeType is not an int, but %s: '%s'." %
                (type(nodeType), nodeType))
            nodeType = ELEMENT_NODE  # FIX
        print("Make Node, nodeType %d (%s), ownerDocument %s." %
            (nodeType, nodeTypeList[nodeType], ownerDocument))
        if (not isinstance(ownerDocument, Document) and
            ownerDocument is not None):
            raise ValueError("Bad type (%s) for ownerDocument." %
                (type(ownerDocument)))

        if (nodeType<0 or nodeType>=len(nodeTypeList)):
            raise ValueError("Unknown nodeType (type %s) %d (%s)." %
                (type(nodeType), nodeType, nodeTypeList[nodeType]))

        self.nsPrefix        = ""
        self.nsURI           = ""
        self.nodeValue       = None
        self.attributes      = NamedNodeMap()
        self.nsAttributes    = NamedNodeMap()
        self.data            = ""
        self.userData        = None

        # Relationships
        self.ownerDocument   = ownerDocument
        self.parentNode      = None
        self.childNodes      = []
        self.previousSibling = None
        self.nextSibling     = None

        # Meta
        self.startLoc        = None
        self.__milestone__   = None  # None or TROJAN_START or TROJAN_END
        self.__otherEnd__    = None
        self.hasIDAttribute  = False             # custom

        @property
        def hasIDAttribute(self):
            ename = self._nodeName
            for anode in self.attributes:
                if ('*@'+anode.name in self.ownerDocument.doctype.IDAttrs or
                    ename+'@'+anode.name in self.ownerDocument.theDOM.doctype.IDAttrs):
                    return(anode.name)
            return (None)

        self.nodeType        = nodeType
        self.nodeName        = None

        @property
        def nodeName(self):
            t = self.nodeType
            if (t == ATTRIBUTE_NODE)              : return self._nodeName
            if (t == CDATA_SECTION_NODE)          : return '#cdata-section'
            if (t == COMMENT_NODE)                : return '#comment'
            if (t == DOCUMENT_NODE)               : return '#document'
            if (t == DOCUMENT_FRAGMENT_NODE)      : return '#document-fragment'
            if (t == DOCUMENT_TYPE_NODE)          : return self.doctype.name
            if (t == ELEMENT_NODE)                : return self._nodeName
            if (t == ENTITY_NODE)                 : return self._nodeName
            if (t == ENTITY_REFERENCE_NODE)       : return self._nodeName
            if (t == NOTATION_NODE)               : return self._nodeName
            if (t == PROCESSING_INSTRUCTION_NODE) : return self.target
            if (t == TEXT_NODE)                   : return '#text'
            if (t == UNSPECIFIED_NODE)            : return None
            raise ValueError("Undefined nodeType %d." % (t))

        @nodeName.setter
        def nodeName(self, value):
            self.nodeType = value


    def appendChild(self, newNode):
        newNode.parentNode = self
        if (len(self.childNodes) > 0):
            newNode.previousSibling = self.childNodes[-1]
            self.childNodes[-1].nextSibling = newNode
        self.childNodes.append(newNode)

    # Don't copy the tree relationships
    # Split into separate impl for some/all subclasses
    #
    def cloneNode(self, deep=False):
        """NOTE: Default value for 'deep' has changed in spec and browsers!
        """
        nt = self.nodeType
        if   (nt==ELEMENT_NODE):
            newNode = Element(self._nodeName)
            newNode.attributes = self.attributes.clone()
            newNode.ownerDocument = self.ownerDocument
            newNode.userData = None
            if (deep):
                for ch in self.childNodes:
                    newNode.appendChild(ch.cloneNode(deep=True))
        elif (nt==ATTRIBUTE_NODE):
            newNode = Attr(self._nodeName, self.data)
        elif (nt==TEXT_NODE):
            newNode = Text(self.data)
        elif (nt==PROCESSING_INSTRUCTION_NODE and
            isinstance(nt, ProcessingInstruction)):
            newNode = ProcessingInstruction(self.target, self.data)
        elif (nt==COMMENT_NODE):
            newNode = Comment(self.data)
        elif (nt==DOCUMENT_NODE):
            newNode = Document()
        elif (nt==DOCUMENT_TYPE_NODE):
            newNode = Doctype()
        elif (nt==NOTATION_NODE):
            newNode = Notation()

        if (self.userData): newNode.userData = self.userData
        return(newNode)

    def compareDocumentPosition(self, n2):
        return(self.compareXPointer(self.getXPointer(), n2.getXPointer()))

    def getFeature(self, feature, version):
        if (feature==version): return(None)
        return(None)

    def getUserData(self, key):
        return(self.userData[key])

    def hasAttributes(self):
        return(len(self.attributes) > 0)

    def hasChildNodes(self):
        return(len(self.childNodes) > 0)

    def insertBefore(self, newNode, ch):
        if (ch.parentNode != self):
            raise ValueError("Reference node for insertBefore is not a child.")
        newNode.parentNode = self
        newNode.nextSibling = ch
        newNode.previousSibling = ch.previousSibling
        if (ch.previousSibling is not None):
            ch.previousSibling.nextSibling = ch
        ch.previousSibling = newNode
        self.childNodes.append(newNode)
        newNode.ownerDocument = self.ownerDocument

    def isDefaultNamespace(self, uri):
        raise NotImplementedError

    # https://dom.spec.whatwg.org/#concept-node-equals
    # Overridden by several subclasses (doctype, element, pr, text, comment)
    def isEqualNode(self, n2):  # Node
        if (self.nodeType != n2.nodeType): return False
        if (self.nodeType==DOCUMENT_TYPE_NODE or
            self.nodeType==ELEMENT_NODE or
            self.nodeType==PROCESSING_INSTRUCTION_NODE or
            self.nodeType==TEXT_NODE or
            self.nodeType==COMMENT_NODE):
            raise ValueError("isEqualNode was not properly overridden!")
        # Following can't happen except for elements, right?
        if (len(self.childNodes) != len(n2.childNodes)): return False
        for i in range(len(self.childNodes)):
            if (not self.childNodes[i].isEqualNode(n2.childNodes[i])): return
        return True

    def isSameNode(self, n2):
        return(self is n2)

    def lookupNamespaceURI(self, uri):
        cur = self
        while(cur):
            for nsa in cur.nsAttributes.theAttrs:
                if (nsa.nsURI == uri): return(nsa.nsPrefix)
            cur = cur.parentNode
        return(None)

    def lookupPrefix(self, prefix):
        cur = self
        while(cur):
            for nsa in cur.nsAttributes.theAttrs:
                if (nsa.nsPrefix == prefix): return(nsa.nsURI)
            cur = cur.parentNode
        return(None)

    def normalize(self):
        for ch in self.childNodes:
            if (ch.nodeType == ELEMENT_NODE):
                self.normalize()
            elif (ch.nodeType == TEXT_NODE and
                  ch.nextSibling and
                  ch.nextSibling.nodeTypee == TEXT_NODE):
                ch.textContent += ch.nextSibling.textContent
                self.removeChild(ch.nextSibling)

    def removeChild(self, ch):
        if (ch.parentNode != self):
            raise ValueError("Node to delete is not a child.")
        if (ch.previousSibling is not None):
            ch.previousSibling.nextSibling = ch.nextSibling
        if (ch.nextSibling is not None):
            ch.nextSibling.previousSibling = ch.previousSibling
        ch.parentNode.childNodes.remove(ch)
        ch.previousSibling = ch.nextSibling = ch.parentNode = None

    def replaceChild(self, newNode, ch):
        if (ch.parentNode != self):
            raise ValueError("Node to replace is not a child.")
        newNode.previousSibling = ch.previousSibling
        newNode.nextSibling = ch.nextSibling
        newNode.parentNode = self
        if (ch.previousSibling is not None):
            ch.previousSibling.nextSibling = newNode
        if (ch.nextSibling is not None):
            ch.nextSibling.previousSibling = newNode
        ch.previousSibling = ch.nextSibling = ch.parentNode = None
        for i, curChild in enumerate(self.childNodes):
            if (curChild == ch):
                self.childNodes[i] = newNode
                break

    def setUserData(self, key, data, handler=None):
        if (self.userData is None): self.userData = {}
        self.userData[key] = (data, handler)

    ########## Methods that are not part of standard DOM ##########
    #
    # tostring() is defined on subclasses of Node.

    def getChildNumber(self):  ### Not DOM
        chs = self.parentNode.childNodes
        for i, ch in enumerate(chs):
            if (ch==self): return(i)
        return(None)

    def getInheritedAttr(self, name):  ### Not DOM
        """Return the value of the named attribute, from the nearest
        ancestor (or self) that has it.
        """
        cur = self
        while (cur):
            avalue = cur.attributes.getNamedItem(name)
            if (avalue is not None): return(avalue)
            cur = cur.parentNode
        return(None)

    def getCompoundAttr(self, name, sep='#', keepMissing=False):  ### Not DOM
        """Return the concatenation of the values of the named attribute,
        from all ancestors (and self). Separate them with 'sep'.
        This facilitates a notion of compound keys (or hierarchical IDs).
        """
        val = ""
        cur = self
        while (cur):
            avalue = cur.attributes.getNamedItem(name)
            if (avalue is not None):
                val = avalue + sep + val
            elif (keepMissing):
                val = sep + val
            cur = cur.parentNode
        return(None)


    ###########################################################################
    # Access via Python list notation, cf DeRose 2014.
    #   DeRose, Steven J. “JSOX: A Justly Simple Objectization for XML:
    #   Or: How to do better with Python and XML.” Presented at
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

    ###########################################################################
    # Access a la XPath axes
    #
    # FIX: attr axis, namespace axis,
    #
    def getAncestor(self, nodeTypes=None, nMin=1, nMax=1, allowSelf=False):
        nodes = []
        found = 0
        if (not allowSelf): cur = self.parentNode
        else: cur = self
        while(cur):
            if (nodeTypes is None or cur.nodeType in nodeTypes):
                found += 1
                if (found>=nMin and found <=nMax): nodes.append(cur)
            cur = cur.parentNode
        return(nodes)

    def getAncestorOrSelf(self, nodeTypes=None, nMin=1, nMax=1):
        return(self.getAncestor(nodeTypes,nMin,nMax,True))

    def getChild(self, nodeTypes=None, nMin=1, nMax=1):
        nodes = []
        found = 0
        for cur in self.childNodes:
            if (nodeTypes is None or cur.nodeType in nodeTypes):
                found += 1
                if (found>=nMin and found <=nMax): nodes.append(cur)
        return(nodes)

    def getDescendant(self, nodeTypes=None, nMin=1, nMax=1, allowSelf=False):
        raise NotImplementedError

    def getDescendantOrSelf(self, nodeTypes=None, nMin=1, nMax=1):
        return(self.getDescendant(nodeType,nMin,nMax,True))

    def getPreviousSibling(self, nodeTypes=None, nMin=1, nMax=1):
        nodes = []
        found = 0
        cur = self.previousSibling
        while(cur):
            if (nodeTypes is None or cur.nodeType in nodeTypes):
                found += 1
                if (found>=nMin and found <=nMax): nodes.append(cur)
            cur = cur.previousSibling
        return(nodes)

    def getNextSibling(self, nodeTypes=None, nMin=1, nMax=1):
        nodes = []
        found = 0
        cur = self.nextSibling
        while (cur):
            if (nodeTypes is None or cur.nodeType in nodeTypes):
                found += 1
                if (found>=nMin and found <=nMax): nodes.append(cur)
            cur = cur.nextSibling
        return(nodes)

    def getPrevious(self, nodeTypes=None, nMin=1, nMax=1):
        cur = self
        # Scan up til we find an ancestor with a previous sibling
        while (cur):
            if (cur.previousSibling):
                # Find last descendent (right branch) of the previousSibling
                cur = cur.previousSibling
                while (cur.childNodes):
                    cur = cur.childNodes[0]
                return cur
        return None

    def getNext(self, nodeTypes=None, nMin=1, nMax=1):
        cur = self
        # Scan up til we find a next sibling
        if (cur.childNodes):
            return cur.childNodes[0]
        while (cur):
            if (cur.nextSibling): return cur.nextSibling
            cur = cur.parentNode
        return None


    def getXPointer(self, useID=True, countTypes=None):  ### Not DOM
        if (countTypes is None): countTypes = [ ELEMENT_NODE ]
        xp = ""
        curNode = self
        while (curNode):
            if (useID):
                idName = curNode.hasIDAttribute
                if (idName):
                    xp = curNode.attributes[idName].strip() + "/" + xp
                    return(xp)
            xp = "%d/%s" % (self.getChildNumber(), xp)
            curNode = curNode.parentNode
        return(xp)

    # End class Node



###############################################################################
# Element
#
class Element(Node):
    """Excludes methods/vars specific to browsers.
    """
    def __init__(self, ownerDocument=None, nodeName=None):
        super(Node, self).__init__(
            nodeType=ELEMENT_NODE, ownerDocument=ownerDocument)
        #Node.__init__(nodeType=ELEMENT_NODE, ownerDocument=ownerDocument)
        self._nodeName = nodeName

    # Define DOM and DOM-ish properties

    @property
    def outerHTML(self):
        return self.startTag + self.innerHTML + self.endTag


    @property
    def innerHTML(self):
        t = ""
        for curNode in self.childNodes:
            if (isinstance(curNode, Text)):
                t += curNode.nodeValue
            elif (isinstance(curNode, Element)):
                t += curNode.innerText
        return(t)

    @property
    def startTag(self):
        if (not isinstance(self, Element)): return ''
        t = "<" + self.nodeName
        for at in (self.attributes):
            t += ' %s="%s"' % (at.name, escapeAttribute(at.value))
        return t + ">"

    @property
    def endTag(self):
        if (not isinstance(self, Element)): return ''
        return "</" + self.nodeName + ">"

    @property
    def outerText(self):
        return self.innerText

    @property
    def innerText(self, delim=''):
        t = ""
        for curNode in self.childNodes:
            if (isinstance(curNode, Text)):
                t += curNode.nodeValue + delim
            elif (isinstance(curNode, Element)):
                t += curNode.innerText
        return(t)


    @property
    def nextElementSibling(self):
        myPos = self.childElementNumber
        return self.parentNode.elementChildN(myPos+1)

    @property
    def previousElementSibling(self):
        myPos = self.childElementNumber
        if (myPos <= 1): return None
        return self.parentNode.elementChildN(myPos-1)


    ########## Properties/functions involving counting siblings (not DOM)
    #
    @property
    def childNumber(self):   # Not DOM
        par = self.parentNode
        for i, ch in enumerate(par.childNodes):
            if (ch is self): return i+1
        raise ValueError("Can't calculate child number")

    @property
    def childElementNumber(self):
        par = self.parentNode
        elementCount = 0
        for ch in par.childNodes:
            if (ch.nodeType == ELEMENT_NODE):
                elementCount += 1
                if (ch is self): return elementCount
        return None

    @property
    def childElementCount(self):
        count = 0
        for ch in self.childNodes:
            if (ch.nodeType == ELEMENT_NODE): count += 1
        return count

    @property
    def firstElementChild(self):
        for ch in self.childNodes:
            if (ch.nodeType == ELEMENT_NODE): return ch
        return None

    @property
    def lastElementChild(self):
        nchildren = len(self.childNodes)
        i = nchildren-1
        while (i>=0):
            ch = self.childNodes[i]
            if (ch.nodeType == ELEMENT_NODE): return ch
            i -= 1
        return None

    @property
    def elementChildNodes(self):
        x = []
        for ch in self.childNodes:
            if (ch.nodeType == ELEMENT_NODE): x.append(ch)
        return x

    # Return the nth *element* child of the Node
    def elementChildN(self, n):
        elementCount = 0
        for ch in self.childNodes:
            if (ch.nodeType == ELEMENT_NODE):
                elementCount += 1
                if (elementCount >= n): return(ch)
        return None


    ###########################################################################
    # Misc
    #
    def isEqualNode(self, n2):  # Element
        if (self.nodeType != n2.nodeType): return False
        if (self._nodeName!=n2._nodeName or
            len(self.attributes) != len(n2.attributes) or
            self.nsPrefix != n2.nsPrefix or
            self.nsURI != n2.nsURI): return False

        for anode in self.attributes.theAttrs:
            if (not anode.isEqualAttr(anode.name, n2)): return False

        if (len(self.childNodes) != len(n2.childNodes)): return False

        for i in range(len(self.childNodes)):
            if (not self.childNodes[i].isEqualNode(n2.childNodes[i])): return

        return True

    ###########################################################################
    # Node/Element: Attributes
    #
    # FIX: Review for attribute node vs. value to be returned!
    #
    @property
    def classList(self):
        return re.split(r'\s+', self.getAttribute('class'))

    @property
    def className(self):
        return self.getAttribute('class')

    @property
    def id(self):
        idName = self.hasIDAttribute
        if (idName): return self.getAttribute(idName)
        return None

    def getAttribute(self, an):
        avalue = self.attributes.getNamedItem(an)
        return avalue

    def getAttributeNS(self, ns, an):
        avalue = self.attributes.getNamedItem(an)
        if (False): return avalue
        raise NotImplementedError

    def getAttributeNode(self, an):
        if (an in self.attributes): return { an: self.attributes[an] }
        return None

    def getAttributeNodeNS(self, ns,an):
        raise NotImplementedError

    def hasAttribute(self, an):
        return (an in self.attributes)

    def hasAttributeNS(self, an, ns):
        return (an in self.attributes)

    def hasAttributes(self):
        return len(self.attributes) > 0

    def removeAttribute(self, an):
        if (an in self.attributes): del self.attributes[an]

    def removeAttributeNS(self, ns, an):
        if (an in self.attributes): del self.attributes[an]

    def removeAttributeNode(self, an):
        if (an in self.attributes): del self.attributes[an]

    # Parser just returns NS attributes like any others. So when we
    # set them, grab the NS ones and record them separately as well.
    # It should really make a NamedNodeMap of them, just like regular
    # Attributes, and point to the very same attribute nodes. I think....
    #
    def setAttribute(self, an, av):
        self.attributes.setNamedItem(an, av)
        if (an.startswith("xmlns:")):
            self.nsAttributes.setNamedItem(an[6:], av)

    def setAttributeNS(self, ns, an, av):
        self.attributes.setNamedItem(an, av)
        if (ns=="xmlns"):
            self.nsAttributes.setNamedItem(an, av)

    def setAttributeNode(self, an, av):
        raise NotImplementedError

    def setAttributeNodeNS(self, ns, an, av):
        raise NotImplementedError

    ###########################################################################
    # Fetching elements

    # getElementsByClassName
    #
    # Return element by class name.
    # Works even if it's just one of multiple class tokens.
    #
    def getElementsByClassName(self, className, nodeList=None):
        if (nodeList is None): nodeList = []
        if (self.nodeType != ELEMENT_NODE): return(nodeList)
        if (className in self.getAttribute('class') and
            (' '+className+' ') in (' '+self.getAttribute('class')+' ')):
            nodeList.append(self)
        for ch in self.childNodes:
            ch.getElementsByClassName(className, nodeList)
        return nodeList

    # For HTML these should be case-insensitive.
    #
    def getElementById(self, IDValue):
        if (self.MLDeclaration.caseInsensitive): IDValue = IDValue.lower()
        if (IDValue in self.ownerDocument.IDIndex):
            return(self.ownerDocument.IDIndex[IDValue])
        return(None)
    getElementByID = getElementById  # Gimme a break....

    def getElementsByTagName(self, tagName, nodeList=None):
        if (nodeList is None): nodeList = []
        if (self.nodeType != ELEMENT_NODE): return(nodeList)
        if (self._nodeName == tagName): nodeList.append(self)
        for ch in self.childNodes:
            ch.getElementsByTagName(tagName, nodeList)
        return nodeList

    def getElementsByTagNameNS(self, tagName, nsURI, nodeList=None):
        if (nodeList is None): nodeList = []
        if (self.nodeType != ELEMENT_NODE): return(nodeList)
        if (self._nodeName == tagName and
            self.nsURI == nsURI): nodeList.append(self)
        for ch in self.childNodes:
            ch.getElementsByTagNameNS(tagName, nodeList, nsURI)
        return nodeList


    ########### Node/Element: JQuery-like 'find'?
    # See https://api.jquery.com/find/
    # and http://api.jquery.com/Types/#Selector
    #
    def find(self):                         # Whence?
        raise NotImplementedError

    def findAll(self):                      # Whence?
        raise NotImplementedError


    ########### Node/Element: Modify actual tree
    #
    def insertAdjacentHTML(self, html):
        raise NotImplementedError

    ########### Node/Element:: Other
    #
    def matches(self):
        raise NotImplementedError

    def querySelector(self):
        raise NotImplementedError

    def querySelectorAll(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError


    ###########################################################################
    # Node/Element: XPointer stuff
    #
    # FIX: XPointers can start with IDs, so this should move to Document.
    #
    def compareXPointer(self, xp1, xp2):  ### Not DOM
        if (not re.match(r'\d+(/\d+)*$', xp1)):
            raise ValueError("Invalid XPointer cseq: '%s'." % (xp1))
        if (not re.match(r'\d+(/\d+)*$', xp2)):
            raise ValueError("Invalid XPointer cseq: '%s'." % (xp2))
        steps1 = '/'.split(xp1)
        steps2 = '/'.split(xp2)
        shorter = min(len(steps1), len(steps2))
        for i in range(shorter):
            if (int(steps1[i]) < int(steps2[i])) : return(-1)
            if (int(steps1[i]) > int(steps2[i])) : return( 1)
        if (len(steps1) < len(steps2)): return(-1)
        if (len(steps1) > len(steps2)): return( 1)
        return(0)

    def resolveXPointer(self, xp):  ### Not DOM
        steps = []
        for step in xp.split('/'):
            steps.append(step.split())
        if (steps[0].isdigit()):
            curNode = self.ownerDocument.documentElement
        else:
            curNode = self.getElementByID(steps[9])
            if (not curNode): raise ValueError(
                "Unknown ID value '%s' in XPointer." % (steps[0]))
        for step in (steps[1:]):
            cnum = int(step)
            ch = curNode.childNodes[cnum]
            if (not ch): break
            curNode = ch
        return(curNode)

    ########### Node/Element: Utilities
    #
    def tostring(self, depth=0):  ### Not DOM
        indent = "\n" + self.ownerDocument.iString * depth
        buf = indent + '<' + self._nodeName + self.attributes.tostring() + '>'
        for ch in self.ownerDocument.childNodes:
            buf += ch.tostring(depth+1)
        buf += '</' + self._nodeName + "/>\n"
        return(buf)

    # End class Element


###############################################################################
#
class CDATASection(Node):  # data
    def __init__(self, ownerDocument, data):
        super(Node, self).__init__(ownerDocument=ownerDocument, data=data)
        #Node.__init__(nodeType=CDATA_SECTION_NODE, ownerDocument=ownerDocument)
        self.data          = data

    def tostring(self, depth=0):  ### Not DOM
        indent = self.ownerDocument.iString * min(0,depth)
        buf = indent + '<![CDATA[' + self.data + ']]>'
        return(buf)


###############################################################################
#
class Comment(Node):
    def __init__(self, ownerDocument=None, data=""):
        super(Node, self).__init__(ownerDocument=ownerDocument, data=data)
        #Node.__init__(nodeType=COMMENT_NODE, ownerDocument=ownerDocument)
        self.data          = data

    def isEqualNode(self, n2):  # Comment
        if (self.nodeType != n2.nodeType): return False
        if (self.data==n2.data): return True
        return False

    # Offer options to wrap comments
    def tostring(self, depth=0):  ### Not DOM
        indent = self.ownerDocument.iString * min(0,depth)
        buf = indent + '<!--' + self.data + '-->'
        return(buf)


###############################################################################
# EntityReference
#
# These nodes are special, for apps that need to track physical structure
# as well as logical. This has not been tested here much.
#
class EntityReference(Node):
    def __init__(self, ownerDocument=None, data=""):
        super(Node, self).__init__(ownerDocument=ownerDocument, data=data)
        #Node.__init__(nodeType=ENTITY_NODE, ownerDocument=ownerDocument)
        self.data          = data

    def tostring(self, depth=0):  ### Not DOM
        indent = self.ownerDocument.iString * min(0, depth)
        buf = indent + '&' + self.data + ';'
        return(buf)


###############################################################################
# Notation
#
# This is for entities in a given data notation/format. They are normally
# embedded by declaring an external file or object as an ENTITY, and then
# mentioning that entity name (not actually referencing the entiry), as
# the value of an attribute that was declared as being of type ENTITY.
#
class Notation(Node):
    def __init__(self, ownerDocument=None, data=""):
        super(Node, self).__init__(ownerDocument=ownerDocument, data=data)
        #Node.__init__(nodeType=NOTATION_NODE, ownerDocument=ownerDocument)
        self.data          = data


###############################################################################
#
class ProcessingInstruction(Node):
    def __init__(self, ownerDocument=None, target="", data=""):
        super(Node, self).__init__(ownerDocument=ownerDocument, target=target, data=data)
        #Node.__init__(nodeType=PROCESSING_INSTRUCTION_NODE, ownerDocument=ownerDocument)
        self.target        = target
        self.data          = data

    def isEqualNode(self, n2): #  ProcessingInstruction
        if (self.nodeType != n2.nodeType): return False
        if (self.target!=n2.target or self.data!=n2.data): return False
        return True

    def tostring(self, depth=0):  ### Not DOM
        indent = self.ownerDocument.iString * depth
        buf = indent + '<?' + self.target + ' ' + self.data + "?>\n"
        return(buf)


###############################################################################
#
# Offer options to wrap text/comments.
#
class Text(Node):  # text
    def __init__(self, ownerDocument=None, data=""):
        Node.__init__(nodeType=TEXT_NODE, ownerDocument=ownerDocument)
        self.data          = data

    def isEqualNode(self, n2):  # Text
        if (self.nodeType != n2.nodeType): return False
        if (self.data==n2.data): return True
        return False

    def tostring(self, depth=0):  ### Not DOM
        indent = self.ownerDocument.iString * depth
        return indent + self.data


###############################################################################
#
# The 'doctypeString' argument should be like:
#     html PUBLIC '...' '...'
# or
#     html SYSTEM '...'
#
class Doctype(Node):
    def __init__(self, ownerDocument=None, doctypeString=''):
        Node.__init__(DOCUMENT_TYPE_NODE, ownerDocument)

        self.doctypeString   = doctypeString

        self._nodeName        = None
        self.publicID        = None
        self.systemID        = None

        # Parse the DOCTYPE declaration
        #
        self._nodeName = re.sub(r'^\s*(\w+)\W.*', r'\\1', doctypeString)
        qlit = r'("[^"]*"|\'[^\']*\')'
        mat = re.match(r'\s+PUBLIC\s+'+qlit+r'\s+'+qlit, doctypeString)
        if (mat):
            self.publicID = mat.group(1).strip("'\" ")
            self.systemID = mat.group(2).strip("'\" ")
        else:
            mat = re.match(r'\s+SYSTEM\s+'+qlit, doctypeString)
            if (mat):
                self.systemID = mat.group(1).strip("'\" ")

        # Set up an index of ID attributes, and which attributes 'count'.
        # IDattrs can have any number of entries, of the forms:
        #     nodeName@attrName, or *@attrName ("*" means any element type)
        self.IDAttrs  = []
        if (not self.publicID and not self.systemID):
            self.IDAttrs.append('*@id')

    def isEqualNode(self, n2):  # Doctype
        if (self.nodeType != n2.nodeType): return False
        if (self._nodeName!=n2._nodeName or self.publicID!=n2.publicID or
            self.systemID!=n2.systemID): return False

        if (len(self.childNodes) != len(n2.childNodes)): return False

        for i in range(len(self.childNodes)):
            if (not self.childNodes[i].isEqualNode(n2.childNodes[i])): return

        return True

    def tostring(self, depth=0):  ### Not DOM
        indent = self.ownerDocument.iString * depth
        buf = (indent + '<!DOCTYPE %s  PUBLIC "%s" "%s" []>' + "\n") % (
            self._nodeName, self.publicID, self.systemID)
        return(buf)


###############################################################################
# Cf https://developer.mozilla.org/en-US/docs/Web/API/Document
#
class Document(Node):
    def __init__(self, doctypeString='', isFragment=False):
        super(Node, self).__init__(DOCUMENT_NODE, None)

        self.MLDeclaration = MLDeclaration(
            language   = 'XML',
            version    = '1.0',
            encoding   = 'utf-8',
            standalone = True
        )

        self.isFragment         = isFragment
        self.impl               = 'sjd2016'
        self.version            = __version__

        self.IDIndex            = {}        # Optional caseInsensitive
        self.loadedFrom         = None
        self.characterSet2       = 'utf-8'
        self.mimeType           = 'text/HTML'
        self.uri                = None
        self.iString            = '    '    # For indenting with tostring()

        self.doctypeNode        = Doctype(self, doctypeString)

    @property
    def all(self):  # Obsolete, but trivial to support
        return(self.IDIndex)
    #@property
    #def async(self):
    #    raise NotImplementedError
    @property
    def characterSet(self):
        return self.characterSet
    @property
    def charset(self):
        return self.characterSet
    @property
    def compatMode(self):
        raise NotImplementedError
    @property
    def contentType(self):
        return self.mimeType
    @property
    def doctype(self):
        return self.doctypeNode
    @property
    def documentElement(self):
        return self
    @property
    def documentURI(self):
        return self.uri
    @property
    def domConfig(self):
        raise NotImplementedError
    @property
    def fullscreen(self):
        raise NotImplementedError
    @property
    def hidden(self):
        raise NotImplementedError
    @property
    def implementation(self):
        raise NotImplementedError
    @property
    def inputEncoding(self):
        return self.characterSet

    # Browser-specific-ish stuff:
    @property
    def lastStyleSheetSet(self):
        raise NotImplementedError
    @property
    def pointerLockElement(self):
        raise NotImplementedError
    @property
    def preferredStyleSheetSet(self):
        raise NotImplementedError
    @property
    def scrollingElement(self):
        raise NotImplementedError
    @property
    def selectedStyleSheetSet(self):
        raise NotImplementedError
    @property
    def styleSheets(self):
        raise NotImplementedError
    @property
    def styleSheetSets(self):
        raise NotImplementedError
    @property
    def timeline(self):
        raise NotImplementedError
    @property
    def undoManager(self):
        raise NotImplementedError
    @property
    def URL(self):
        return self.uri
    @property
    def visibilityState(self):
        raise NotImplementedError
    @property
    def xmlEncoding(self):
        return self.xmlEncoding


    # Methods
    #
    # Note: The 'create...' methods pass 'self' as an extra argument,
    # because this is class *Document*, and all the nodes created in a
    # Document store a pointer back, as 'ownerDocument'.
    #
    def createElement(self, tagName, attributes=None):
        newNode = Element(self, nodeName=tagName)
        if attributes:
            for a, v in attributes.items():
                newNode.setAttribute(a, v)
        return(newNode)

    def createDocumentFragment(self):
        newNode = Document(self, isFragment=True)
        return(newNode)

    def createTextNode(self, data):
        newNode = Text(data, self)
        return(newNode)

    def createComment(self, data):
        newNode = Comment(data, self)
        return(newNode)

    def createCDATASection(self, data):
        newNode = CDATASection(self, data)
        return(newNode)

    def createProcessingInstruction(self, target, data):
        newNode = ProcessingInstruction(self, target, data)
        return(newNode)

    def createEntityReference(self, name):
        newNode = EntityReference(self, name)
        return(newNode)

    def tostring(self, depth=0):  # Document
        indent = self.iString * depth
        buf = indent + """<?xml version="1.0" encoding="utf-8"?>\n"""
        buf += self.doctypeNode.tostring() + "\n"
        buf += "\n<!-- n children: %d -->\n" % (len(self.childNodes))
        for ch in self.childNodes:
            buf += ch.tostring()
        return(buf)

    # Discard empty text nodes; coalesce;...
    def normalize(self):  ### Not DOM
        for ch in self.childNodes:
            if (ch.nodeType == ELEMENT_NODE):
                ch.normalize()
            elif (ch.nodeType == TEXT_NODE):
                nxt = ch.nextSibling
                if (nxt and nxt.nodeType==TEXT_NODE):
                    ch.data += nxt.data
                    self.removeChild(nxt)

    # End class Document



###############################################################################
# Build the DOM structure. By construction or by parsing something.
# https://docs.python.org/2/library/htmlparser.html#module-HTMLParser
# Has problems, like no endtag events for omitted tags.
#
class DOMBuilderHTML(HTMLParser):
    def __init__(self):
        super(HTMLParser, self).__init__()
        self.sch = simplisticSchemaHTML()
        self.tagStack = []             # Open Element objects
        self.theMLD = MLDeclaration()

        # Limited schema info, used for pretty-printing
        self.empties = {}
        self.inlines = {}
        self.okChild = {}

    def trace(self, msg):
        print(msg)

    ### Handlers ##############################################################
    # Presuming parser already handled tag case, but not ID values.
    #
    def handle_starttag(self, name, attributes):
        self.trace("handle_starttag: got '%s'" % (name))
        while (self.tagStack and
               not self.sch.canContain(self.tagStack[-1]._nodeName, name)):
            self.handle_endtag(self.tagStack[-1])
        e = theCurrentDoc.createElement(name, attributes)
        for n, v in attributes.items():
            e.setAttribute(n, v)
            if ('*@'+n in theCurrentDoc.doctype.IDAttrs or
                name+'@'+n in theCurrentDoc.doctype.IDAttrs):
                if (self.theMLD.caseInsensitive): v = v.lower()
                if (v in theCurrentDoc.IDIndex):
                    raise ValueError("Duplicate ID value '%s' @ %s." %
                        (v, self.getpos()))
                else:
                    theCurrentDoc.IDIndex[v] = e
        e.startLoc = self.getpos()  # Remember where we parked
        self.tagStack[-1].appendChild(e)
        self.tagStack.append(e)
        return

    def handle_endtag(self, name):
        self.trace("handle_endtag: got '%s'" % (name))
        if (self.tagStack[-1] == name):                    # As expected
            self.tagStack.pop()
        elif (name in self.tagStack):                      # Omitted end-tag(s)
            while (self.tagStack[-1] != name):
                self.handle_endtag(self.tagStack[-1])
        else:
            raise ValueError("Expecting end-tag for '%s' but in context '%s'." %
                (self.tagStack[-1], name))
        self.tagStack.pop()
        return

    def handle_startendtag(self, name, attributes):        # <br/>
        self.trace("handle_startendtag: got '%s'" % (name))
        self.handle_starttag(name, attributes)
        self.handle_endtag(name)
        return

    def handle_data(self, data):     # FIX: Coalesce adjacent text nodes?
        self.trace("handle_data: got '%s'" % (data))
        if (not self.tagStack):
            if (re.match(r'\S', data)):
                raise("Found data outside any element: '%s'." % (data))
            else:
                return
        tn = theCurrentDoc.createTextNode(data)
        self.tagStack[-1].appendChild(tn)
        return

    def handle_entityref(self, name):
        self.trace("handle_entityref: got '%s'" % (name))
        raise ValueError("Skipped entity: '%s'." % (name))

    def handle_charref(self, name):
        self.trace("handle_charref: got '%s'" % (name))
        if (name in XMLEntities):                          # &lt; etc.
            return(XMLEntities[name])
        mat = re.match("#[xX]([0-9a-fA-f]+)", name)        # &#xFFFF;
        if (mat):
            n = int(mat.group(1),16)
            c = unichr(n)
            if (not c or (n<32 and n not in [ 9, 10, 13 ])):
                raise ValueError(
                    "WF: Character reference to non-XML Char 0x%s" % (n))
            return(c)

        mat = re.sub(r"^&#([0-9]+)","",name)                # &#999;
        if (mat):
            n = int(mat.group(1),10)
            c = unichr(n)
            if (not c or  (n<32 and n not in [ 9, 10, 13 ])):
                raise ValueError(
                    "WF: Character reference to non-XML Char 0d%s" % (n))
            return(c)
                                                           # &foo;
        raise ValueError("Unknown entity name '%s'" % (name))

    def handle_comment(self, data):
        self.trace("handle_comment: got '%s'" % (data))
        newCom = theCurrentDoc.createComment(data)
        self.tagStack[-1].appendChild(newCom)
        return

    def handle_decl(self, data):
        self.trace("handle_decl: ignoring '%s'" % (data))
        #newDcl = theCurrentDoc.create(data)
        #self.tagStack[-1].appendChild(newDcl)
        return

    def handle_pi(self, target, data):
        self.trace("handle_pi: got '%s'" % (data))
        newPI = theCurrentDoc.createProcessingInstruction(target, data)
        self.tagStack[-1].appendChild(newPI)
        return

    def handle_unknown_decl(self, data):
        self.trace("handle_unknown_decl: got '%s'" % (data))
        # raise ValueError("Unknown markup declaration: '%s'" % (data))
        newDcl = theCurrentDoc.createComment(data)
        self.tagStack[-1].appendChild(newDcl)
        return



###############################################################################
###############################################################################
#
class Obsolete:
    def __init__(self):
        self.x = 'foo'

    def parsefileHTML(self, path):
        try:
            fh = codecs.open(path, 'r')
        except IOError as e:
            print("Unable to open file '%s':\n    %s" % (path, e))
            sys.exit()
        p = HTMLParser()
        while (True):
            buf = fh.readline()
            if (buf == ''): break
            p.feed(buf)
        p.close()
        p.reset()
        return theCurrentDoc

    def parsestringHTML(self, s):
        print("*** Parsing, string len %d ***\n" % (len(s)))
        p = HTMLParser()
        p.feed(s)
        p.close()
        p.reset()
        return theCurrentDoc


###############################################################################
###############################################################################
#
if __name__ == "__main__":
    h = """<!DOCTYPE html PUBLIC 'x' 'y'>
<html>
<head>
<style type="text/css">
    li        { margin-top:12pt; }
</style>
<title>Sample of the HTML data thingie.</title>
</head>
<body>
<h1>A trivial <a href="http://www.example.com/doc.txt">document</a>.</h1>
<!-- Comments <i>very much</i> allowed.
     Even across the lines. -->
<div id="main">
<p>But with a few things, like the <i>great</i> entities in &ldquo;&#65;&rdquo;.</p>
<p>HTML allows omitting end-tags
<p>Like that and this.
<p>And this, too.
</div>
<div>
<p>What happens with an HTML empty like slashless <br>, or
XML-style: <empty /> tag?</p>
<p>Sometimes you get the <b>best</b> text these files
have to offer, such as in this link: <a href="http://en.wikipedia.org/Funny">funny</a> text.
Do CDATA sections work, such as: <![CDATA[ ones containing <p>? ]]></p>

<ol>
<li><p>And then there is some more plain stuff like:
    <ul>
        <li>Aardvars<li>
        <li>Beagles</li>
        <li>Cats</li>
    </ul>
</p></li>
</ol>

<p>And a PI: <?PItarget This is a <notag> pi?</notag>, ok??> That was a PI.</p>
</div>
</body>
</html>
"""

    print("******* UNFINISHED *******")

    # Also consider: https://docs.python.org/2/library/pyexpat.html
    #
    theCurrentDoc = Document('', 0)

    print("Building the DOM")
    parser = DOMBuilderHTML()
    parser.feed(h)
    print("\nResults:")
    print(theCurrentDoc.tostring())
