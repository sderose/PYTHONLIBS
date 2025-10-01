#!/usr/bin/env python3
#
# DomGetitem.py: Make xml.dom.minidom.Node and its subclasses much more Pythonic.
# 2021-07-21: Extracted from DomExtensions.py, where it also is available.
#
#pylint: disable=W0613, W0212, E1101
#
import sys
from enum import Enum
from typing import List, Union
from xml.dom.minidom import Node, Document  #, NamedNodeMap

from ragnaroktypes import NodeType
from runeheim import XmlStrings

__metadata__ = {
    "title"        : "DomGetitem",
    "description"  : "Make xml.dom.minidom.Node and ts subclass much more Pythonic.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2010-01-10",
    "modified"     : "2021-07-21",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

This defines a subclass of xml.minidom.Node adding a `__getitem__()`
method that lets you get child nodes of all kinds (elements, comments, pis,
attributes, text nodes) with the usual Python [] notation.

You can instantiate these "PyNode" objects directly, but it is probably
better to simply add the __getitem__ method to the regular class so
that createElement() items also have it:

    xml.minidom.Node.__getitem__ = pyNode.__getItem__

Like Python [] in general, this implementation accepts up to 3 values
inside the []. The third argument specifies a "step",
which allows you, for example, to get every other item from a list:

    x[1:10:2]

That works the same here, selecting among the childNodes of the given Node.
But in addition, the first or last item can be a string.
That string is used to limit the type and/or name of nodes you are selecting from.
For example:

    myElement["p"]      gets all child nodes of nodeName "p"
    myElement["p":2]    gets all child nodes of nodeName "p", then picks the third of those
    myElement[2:10:"p"] gets child nodes 2 through 9, then picks out those of nodename 'p'

That is, the arguments can include a string filter and an integer range filter,
in either order.

As in Python in general, and in DOM, the first child is [0].

Besides some nodename strings do other useful things:

* If the string begins with "@", you get the named attribute:

    myElement['@class'] get the 'class' attribute's value

* If the string is "*", the slicing operates over those child nodes
 that are elements (skipping any text nodes, PIs, comments, etc.).

* If the string is one of "#pi", "#comment", or "#text", the slicing operates
over those child nodes of just that nodeType.

* If the string is "#NWSN", slicing considers all child nodes that are
NOT empty or whitespace-only text nodes. [TO BE ADDED]

In all cases except attributes (which cannot be repeated on a single element),
one or two integers may precede the type filter. If the integers precede the type
filter, they extract a range as usual for Python list, and then the type filters
chooses nodes from that extracted range. If the integers instead follow
the type filter, the filter picks nodes by type, and then members are picked
from that list of node by integer range.

If the first argument in brackets chooses an attribute, the integers are not
also allowed (in future, they may be permitted in order to choose
among space-separated tokens within the attribute value, as for
example with HTML class attributes).

Some additional examples:
    myElement["p":2]      get the 3rd "p" child
    myElement[2:"p"]      get 3rd child if it"s a "p"
    myElement["p":2:8]    get the 3rd through 7th "p" children
    myElement[2:8]        get the 3rd through 7th children
    myElement[2:8:"p"]    of the 3rd through 7th children, get the "p"s
    myElement[1:10:2]     get every other childNode from 1:10.
    myElement["@class"]   get the "class" attribute.


=Related commands=

This and many other additional methods for DOM are available in my DomExtensions.py
at [http://www.github.com/sderose/PYTHONUTILS].

=References=

This design is based on the following paper:

DeRose, Steven J. 2014. "JSOX: A Justly Simple Objectization for XML:
Or: How to do better with Python and XML."
Balisage Series on Markup Technologies, vol. 13.
[https://doi.org/10.4242/BalisageVol13.DeRose02]


=To Do=

* Profile
* Perhaps allow passing in a regex for the string arg?
* Perhaps restrict the string arg to last position only?
* Finish #NWSN.
* Support __setitem__ for @x or any case that comes out unique?


=History=

* 2010-01-10: DomExtensions.py original.
* 2021-07-21: Extracted from DomExtensions.py (q.v.).


=Rights=

Copyright 2010-01-10 by Steven J. DeRose. This work is licensed under a Creative
Commons Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].


=Options=
"""


###############################################################################
#
class NodeArgs(Enum):
    """This looks at the argument to node[arg], and categorizes it.
    This has to handle ints and strings.
    In the case of slices, this should be applied to each of the 3 items.

    For example:
        "#comment" -> COMMENT_ARG
        "p"        -> ELEMENT_ARG
        "@id"      -> ATTRIBUTE_ARG
    The values are based on the usual Node.nodeType, plus some extras:
        * selection languages (XPath, CSS, etc.)
        * cover terms for sets of nodeTypes ("*" for element|cdata|text).
        * Python's usual int and slice for lists and such
    """
    UNSPECIFIED_ARG             = 0  # Not in DOM
    ELEMENT_ARG                 = 1
    ATTRIBUTE_ARG               = 2
    TEXT_ARG                    = 3
    CDATA_SECTION_ARG           = 4
    ENTITY_REFERENCE_ARG        = 5  # Not in DOM
    ENTITY_ARG                  = 6  # Not in DOM
    PROCESSING_INSTRUCTION_ARG  = 7
    COMMENT_ARG                 = 8
    DOCUMENT_ARG                = 9
    DOCUMENT_TYPE_ARG           = 10
    DOCUMENT_FRAGMENT_ARG       = 11
    NOTATION_ARG                = 12 # Not in DOM

    INT_ARG       = 100  # Python's usual integer args
    STAR_ARG      = 102  # Any element, any name (special)
    WSN_ARG       = 103  # whitespace-only text nodes
    NWSN_ARG      = 104  # any nodes except WSN

    # Possible additions:
    REGEX_ARG     = 20  # A compiled regex to match vs. element names
    CSS_ARG       = 201  # A CSS selector (#id .class, name[att...],...)
    XPATH_ARG     = 202 # An XPath expression

    @staticmethod
    def isReservedWordArg(val):
        """Is the identified arg, of a type that is not an open set?
        That is, is it not an element name, "@"+attribute name, int, or
        one of the (200+) languages?
        """
        return (val in NodeArgs.reservedWords.values())

    # Map the recognized reserved words to the right cateogory. They map to
    # a nodeType when there's a single corresponding one, otherwise to
    # a Callable that returns True if a given node matches.
    # The #-initial words are mostly the same as .nodeType reserved values,
    # but not when .nodeType has an actual name (element, document, pi).
    #
    reservedWords = {
        "#text":     TEXT_ARG,
        "#cdata":    CDATA_SECTION_ARG,
        "#pi":       PROCESSING_INSTRUCTION_ARG,
        "#comment":  COMMENT_ARG,

        "*":         ELEMENT_ARG,
        "#document": DOCUMENT_ARG,           # unused
        "#doctype":  DOCUMENT_TYPE_ARG,      # unused
        "#fragment": DOCUMENT_FRAGMENT_ARG,  # unused

        "#main":     lambda n: n.nodeType in (
            NodeType.ELEMENT_NODE, NodeType.TEXT_NODE, NodeType.CDATA_SECTION_NODE),
        "#notmain":  lambda n: n.nodeType not in (
            NodeType.ELEMENT_NODE, NodeType.TEXT_NODE, NodeType.CDATA_SECTION_NODE),
        "#wsn":      lambda n: n.nodeType == NodeType.TEXT_NODE and n.data.strip() == "",
        # TODO: Do we want text that's not just ws, or anything that's not ws text?
        # And do ws-only cdata count?
        "#notwsn":   lambda n: n.nodeType != NodeType.TEXT_NODE or n.data.strip() != ""
    }

    @staticmethod
    def isNodeKindChoice(s:str) -> bool:
        """Check whether the token is one of our node kind selector arguments.
        These don't take qualifiers unless they're element names). This unifies
        node types into one space (rather than one for type and one for name).
        Almost like DOM nodeType, except attributes are prefixed with "@",
        and PIs are "#pi".
            * element:  same as XmlQName
            * attribute: "@" + XmlName (so you can name attrs relative to an elem)
            * document root:  #document
            * pi: #pi
            * comment: #comment
            * text: #pi (should there be a non-white-space-only textnode selector?)
            * and we allow "*" to mean any element
        fragment, namespace, etc. are just special cases of more basic types.
        """
        if (XmlStrings.isXmlQName(s)): return True
        if (s in [ "*", "#text", "#comment", "#cdata", "#pi" ]): return True
        if (s[0] == "@" and XmlStrings.isXmlName(s[1:])): return True
        return False

    @staticmethod
    def getKind(someArg:Union[str, int]) -> 'NodeArgs':  # nee def argType()
        """Categorize one of the arguments to __getitem__().
        """
        if (someArg is None):
            return NodeArgs.NONE_NODE

        if (isinstance(someArg, int)):
            return NodeArgs.INT_NODE

        if (isinstance(someArg, str)):
            fchar = someArg[0]
            if (fchar == "*"):
                return NodeArgs.STAR_NODE
            elif (fchar == "@"):  # no combo with numeric slicing
                assert XmlStrings.isXmlName(someArg[1:])
                return NodeArgs.ATTRIBUTE_NODE
            elif (fchar == "#"):
                try:
                    return NodeArgs.reservedWords[someArg]
                except KeyError as e:
                    raise KeyError from e
            else:
                if (not XmlStrings.isXmlName(someArg)):
                    raise ValueError("getitem arg is not an XML NAME or reserved word.")
                return NodeArgs.ELEMENT_NODE

        raise ValueError("Unexpected type %s for getitem arg (=%s)."
            % (type(someArg), someArg))

    # Add nodeSelMatches from DomExtensions?


###############################################################################
#
def __domgetitem__(self:Node, n1:int, n2:int=None, n3:str=None) -> List:
    """Access nodes via Python list notation.
    List-like numeric slicing/indexing:
        myNode[2] -- as usual
        myNode[2:-1] -- as usual
        myNode[1:-1:2] -- as usual
    nodeType selection:
        myNode["p"] -- all <p> children
        myNode["*"] -- all element children
        myNode["@xxx"] -- the attribute named xxx
        myNode["#text"] -- all text node children
            #comment, #pi, #cdata -- likewise
        ?    #wsn -- all whitespace-only text node
        ?    #nwsn -- all children except whitespace-only text nodes
        ?    #main -- all element, text, and cdata children (no pi, comment, wsn)
    combined
        myNode["p":0] -- the first <p> child
        myNode["p":0] -- the first <p> child
        myNode["#pi":2:4] -- PI children 2 through 4

    Note: The "#" here is like XML, SGML, and HTML reserved words, not
    like CSS id selectors. One wouldn't likely use [] for id selection among
    direct child nodes anyway.

    This might be extended to support XPath, CSS, custom callbacks...
    """
    if (isinstance(n1, slice)):
        n1 = slice.start; n2 = slice.step; n3 = slice.step
    nargs = 0
    typ1 = typ2 = typ3 = None
    if (n1 is not None):
        nargs = 1
        typ1 = NodeArgs.getKind(n1)
        if (n2 is not None):
            nargs = 2
            typ2 = NodeArgs.getKind(n2)
            if (n3 is not None):
                nargs = 3
                typ3 = NodeArgs.getKind(n3)
    print("getKinds are %s, %s, %s." % (typ1, typ2, typ3))

    if (typ2 == NodeArgs.ATTRIBUTE_NODE or typ3 == NodeArgs.ATTRIBUTE_NODE or
        (typ1 == NodeArgs.ATTRIBUTE_NODE and nargs>1)):
        raise IndexError("No other indexes allowed with @xxx.")

    if (nargs == 1):
        if (typ1 == NodeArgs.INT_NODE):                              # [0]
            return self.childNodes[n1]
        if (typ1 == NodeArgs.ATTRIBUTE_NODE):                        # ['@id']
            warning("Getting attr, arg 1 is '%s'." % (n1))
            return self.getAttribute(n1[1:])
        return self._getChildNodesByName_(n1)              # ['p'] ['#text'] ['*']

    elif (nargs == 2):
        if (typ1 == NodeArgs.INT_NODE):
            if (typ2 == NodeArgs.INT_NODE):                          # [0:2]
                return self.childNodes[n1:n2]
            return self._getChildNodesByName_(n2)[n1]      # [0:'p']
        else:
            if (typ2 == NodeArgs.INT_NODE):                          # ['x':0]
                return self._getChildNodesByName_(n1)[n2]
            else:                                          # ['x':'x']
                raise IndexError("More than one non-int index.")

    else:  # nargs == 3
        if (typ1 == NodeArgs.INT_NODE and typ2 == NodeArgs.INT_NODE):
            if (typ3 == NodeArgs.INT_NODE):                          # [0:5:2]
                return self.childNodes[n1:n2:n3]
            else:                                          # [0:5:'p']
                nodeList = self.childNodes[n1:n2]
                return self._getListItemsByName_(nodeList, n3)
        elif (typ2 == NodeArgs.INT_NODE and typ3 == NodeArgs.INT_NODE):        # ['x':0:1]
            return self._getChildNodesByName_(n1)[n2:n3]
        else:
            raise IndexError(
                "No 2 adjacent ints in [%s:%s:%s] for a " % (n1, n2, n3))


class PyNode(Node):
    __getitem__ = __domgetitem__

    def len(self):
        return len(self.childNodes)

    def what(self):
        """Map from nodeTypes to our names (same as nodeName except for attrs).
        """
        if (self.nodeType == NodeArgs.ATTRIBUTE_NODE): return "@" + self.nodeName
        else: return self.nodeName

    def DEcontains(self:Node, nodeName:str) -> bool:
        """Test whether the node has a direct child of the given type.
        """
        if (nodeName[0] == '@'):
            return self.hasAttribute(nodeName)
        for ch in self.childNodes:
            if (ch.nodeType == NodeType.ELEMENT_NODE):
                if (nodeName == '*' or nodeName == ch.nodeName): return True
            elif (nodeName[0] == '#' and nodeName == self.nodeName): return True
        return False

    def _getChildNodesByName_(self:Node, name:str) -> list:
        """Return a list of this node's children of a given element name
        '*' gets all element children, but no pi, comment, text....
        """
        return self._getListItemsByName_(self.childNodes, name)

    def _getListItemsByName_(self:Node, theList:list, s:str) -> list:
        """This accepts element type names, #text etc., and "*".
        No attributes or ints here.
        """
        argKind = NodeArgs.getKind(s)
        if (argKind != NodeArgs.ELEMENT_ARG
            and not NodeArgs.isReservedWordArg(argKind)):
            raise KeyError(
                "Node index '%s' is not reserved, '*', or an element type name." % (s))
        inodes = []
        for item in theList:
            if (self.matchesArg(s, argKind)): inodes.append(item)
        return inodes

    def matchesArg(self, arg, argKind:NodeArgs):
        nt = self.nodeType

        # Whoops...
        if (argKind == NodeArgs.UNSPECIFIED_ARG):
            return False

        # Element and attribute name selectors
        elif (argKind == NodeArgs.ELEMENT_ARG):
            if (nt == NodeType.ELEMENT_NODE and self.nodeName == arg): return True
        elif (argKind == NodeArgs.ATTRIBUTE_ARG):
            if (nt == NodeType.ATTRIBUTE_NODE and self.name == arg): return True

        # Reserved word selectors that represent nodeTypes
        elif (argKind == NodeArgs.TEXT_ARG):
            if (nt == NodeType.TEXT_NODE): return True
        elif (argKind == NodeArgs.CDATA_SECTION_ARG):
            if (nt == NodeType.CDATA_SECTION_NODE): return True
        elif (argKind == NodeArgs.ENTITY_REFERENCE_ARG):  # Unused
            if (nt == NodeType.ENTITY_REFERENCE_NODE): return True
        elif (argKind == NodeArgs.ENTITY_ARG):  # Unused
            if (nt == NodeType.ENTITY_NODE): return True
        elif (argKind == NodeArgs.PROCESSING_INSTRUCTION_ARG):
            if (nt == NodeType.PROCESSING_INSTRUCTION_NODE): return True
        elif (argKind == NodeArgs.COMMENT_ARG):
            if (nt == NodeType.COMMENT_NODE): return True
        elif (argKind == NodeArgs.DOCUMENT_ARG):                # Name?
            if (nt == NodeType.DOCUMENT_NODE): return True
        elif (argKind == NodeArgs.DOCUMENT_TYPE_ARG):           # Name?
            if (nt == NodeType.DOCUMENT_TYPE_NODE): return True
        elif (argKind == NodeArgs.DOCUMENT_FRAGMENT_ARG):
            if (nt == NodeType.DOCUMENT_FRAGMENT_NODE): return True
        elif (argKind == NodeArgs.NOTATION_ARG):                # Name?
            if (nt == NodeType.NOTATION_NODE): return True

        # Meta-selectors
        elif (argKind == NodeArgs.STAR_ARG):                    # "*" = any element
            if (nt == NodeType.ELEMENT_NODE): return True

        # WSN, NWSN, MAIN, NMAIN

        # CSS, XPath, etc. -- scheme-like prefix?
        #     css:#id
        #     (css)#id
        #     css(#id)
        #     ...?

        return False


###############################################################################
# Test driver
#
if __name__ == "__main__":
    import argparse

    def warning(msg:str) -> None:
        sys.stderr.write(msg + "\n")

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_NODEument(
            "--quiet", "-q", action="store_true",
            help='Suppress most messages.')
        parser.add_NODEument(
            "--verbose", "-v", action="count", default=0,
            help='Add more messages (repeatable).')
        parser.add_NODEument(
            "--version", action="version", version=__version__,
            help='Display version information, then exit.')

        args0 = parser.parse_NODEs()
        return args0


    ###########################################################################
    #
    args = processOptions()

    warning("Patching extensions onto xml.dom.minidom...")

    theDocEl = Document()
    theDocEl.nodeName = "book"
    print("Document nodeName is '%s'." % (theDocEl.nodeName))
    body = theDocEl.createElement("body")
    theDocEl.appendChild(body)
    print("body element nodeName is '%s'." % (body.nodeName))

    nParas = 10
    for i in range(nParas):
        pe = theDocEl.createElement("p")
        pe.setAttribute("id", "myId_%2d" % (i))
        pe.appendChild(theDocEl.createTextNode("This is a some text."))
        body.appendChild(pe)

    print("Sample document created.")

    for i in range(0, nParas, 2):
        print("ch %d: type '%s'" % (i, body[i].nodeName))
        print("    id: %s" % (body[i]["@id"]))

    warning("Done.")
