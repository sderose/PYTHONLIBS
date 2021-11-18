#!/usr/bin/env python
#
# DomGetitem.py: Make xml.dom.minidom.Node and ts subclass much more Pythonic.
# 2021-07-21: Extracted from DomExtensions.py, where it also is available.
#
#pylint: disable=W0613, W0212, E1101
#
import sys
import re
#import codecs
#from enum import Enum
from typing import List
#import xml.dom, xml.dom.minidom
from xml.dom.minidom import Node, Document  #, NamedNodeMap

#from html.entities import codepoint2name, name2codepoint

__metadata__ = {
    'title'        : "DomGetitem.py",
    'description'  : "Make xml.dom.minidom.Node and ts subclass much more Pythonic.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2010-01-10",
    'modified'     : "2021-07-21",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

This defines a subclass of xml.minidom.Node, which adds a `__getitem__()` method that
lets you get child nodes of all kinds (elements, comments, pis, attributes, text nodes)
with the usual Python [] notation.

You can instantiate these "PyNode" objects directly, but it is probably better to simply
add the __getitem__ method to the regular class. For one thing, that means that when
you do createElement() or similar, the new Node will also benefit:

    xml.minidom.Node.__getitem__ = pyNode.__getItem__

Like Python [] in general, this implementation accepts up to 3 values inside the [].
For regular lists, the third argument specifies a "step", which allows you, for example,
to get every other item from a list:
    x[1:01:2]

Slicing with 1, 2, or 3 integer arguments can be done Here, selecting among the
childNodes of the given Node. But in addition, the last item can be a string.
That string is used to specify just what nodes you are selecting from. For example:

    myElement[0:-1:'p']       gets all child nodes that are element type 'p'
    myElement[0::'p']         gets the first child node that is element type 'p'

Note that as in Python in general, and in DOM, the first child is [0].

Like Python slicing notation generally, [] with a single numeric argument returns
the single (scalar) item; otherwise slicing returns a list.

Besides child elements, the last argument can be used to get other useful things:

* If the string is "*", the slicing operates over all *element* children of the node,
skipping any text nodes, PIs, comments, etc.

* If the string is one of "#PI", "#COMMENT", or "#TEXT", child nodes of just that
nodeType will be retrieved.

* If the string begins with "@", you get the named attribute:

    myElement['@class']  get the 'class' attribute's value (no indexes!)

In all cases except attributes (which cannot be repeated on a single element),
the one or two preceding integers pick from the chsen category of child nodes, in
the usual Python fashion. With attributes, the integers (if present) choose among the
space-separated tokens within the attribute value.

Some additional examples:
    myElement['p':2]     get the 3rd 'p' child
    myElement[2:'p']     get 3rd child if it's a 'p'
    myElement['p':2:8]   get the 3rd through 7th 'p' children
    myElement[2:8]       get the 3rd through 7th children
    myElement[2:8:'p']   of the 3rd through 7th children, get the 'p's
    myElement[1:10:2]    get every other childNode from 1:10.


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

* Perhaps allow passing in a regex for the string arg?
* Perhaps restrict the string arg to last position only?


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
class PyNode(Node):
    nameStartChar = str(u"[:_A-Za-z" +
        u"\u00C0-\u00D6" + u"\u00D8-\u00F6" + u"\u00F8-\u02FF" +
        u"\u0370-\u037D" + u"\u037F-\u1FFF" + u"\u200C-\u200D" +
        u"\u2070-\u218F" + u"\u2C00-\u2FEF" + u"\u3001-\uD7FF" +
        u"\uF900-\uFDCF" + u"\uFDF0-\uFFFD" +
        u"\u10000-\uEFFFF" +
        ']')
    nameChar  = re.sub(
        u'^\\[', u'[-.0-9\u00B7\u0300-\u036F\u203F-\u2040', nameStartChar)
    xmlName = nameStartChar + nameChar + '*'

    @staticmethod
    def isXmlName(s:str) -> bool:
        if (s is None): return False
        #print("types: expr %s, s %s." % (type(PyNode.xmlName), type(s)))
        if (re.match(PyNode.xmlName, s, re.UNICODE)): return True
        return False

    # Following constants are returned by argType():
    ARG_NONE      = 0
    ARG_INT       = 1
    ARG_ATTRIBUTE = 2
    ARG_STAR      = 3
    ARG_RESERVED  = 4
    ARG_NAME      = 5

    def __init__(self, *args9, **kwargs):
        super(PyNode, self).__init__(self, *args9, **kwargs)

    def __getitem__(self:Node, n1:int, n2:int=None, n3:str=None) -> List:
        """Access nodes via Python list notation.
        """
        typ1 = PyNode.argType(n1)
        typ2 = PyNode.argType(n2)
        typ3 = PyNode.argType(n3)
        print("argTypes are %s, %s, %s." % (typ1, typ2, typ3))
        if (n3 is not None): nargs = 3
        elif (n2 is not None): nargs = 2
        else: nargs = 1

        if (typ2==PyNode.ARG_ATTRIBUTE or typ3==PyNode.ARG_ATTRIBUTE or
            (typ1==PyNode.ARG_ATTRIBUTE and nargs>1)):
            raise IndexError("No other indexes allowed with @xxx.")

        if (nargs==1):
            if (typ1 == PyNode.ARG_INT):                              # [0]
                return self.childNodes[n1]
            if (typ1 == PyNode.ARG_ATTRIBUTE):                        # ['@id']
                warn(0, "Getting attr, arg 1 is '%s'." % (n1))
                return self.getAttribute(n1[1:])
            return self._getChildNodesByName_(n1)              # ['p'] ['#text'] ['*']

        elif (nargs==2):
            if (typ1 == PyNode.ARG_INT):
                if (typ2 == PyNode.ARG_INT):                          # [0:2]
                    return self.childNodes[n1:n2]
                return self._getChildNodesByName_(n2)[n1]      # [0:'p']
            else:
                if (typ2 == PyNode.ARG_INT):                          # ['x':0]
                    return self._getChildNodesByName_(n1)[n2]
                else:                                          # ['x':'x']
                    raise IndexError("More than one non-int index.")

        else:  # nargs==3
            if (typ1 == PyNode.ARG_INT and typ2 == PyNode.ARG_INT):
                if (typ3 == PyNode.ARG_INT):                          # [0:5:2]
                    return self.childNodes[n1:n2:n3]
                else:                                          # [0:5:'p']
                    nodeList = self.childNodes[n1:n2]
                    return self._getListItemsByName_(nodeList, n3)
            elif (typ2 == PyNode.ARG_INT and typ3 == PyNode.ARG_INT):        # ['x':0:1]
                return self._getChildNodesByName_(n1)[n2:n3]
            else:
                raise IndexError(
                    "No 2 adjacent ints in [%s:%s:%s] for a Node." % (n1, n2, n3))

    def DEcontains(self:Node, nodeName:str) -> bool:
        """Test whether the node has a direct child of the given element type.
        """
        if (nodeName[0] == '@'):
            return self.hasAttribute(nodeName)
        for ch in self.childNodes:
            if (ch.nodeType == Node.ELEMENT_NODE and
                (nodeName == '*' or nodeName == ch.nodeName)): return True
            if (nodeName[0] == '#' and nodeName == self.nodeName): return True
            return False

    @staticmethod
    def argType(s:str) -> int:
        """Categorize one of the arguments to __getitem__().
        """
        if (s is None): return PyNode.ARG_NONE
        if (isinstance(s, int)): return PyNode.ARG_INT  # TODO: Allow float, maybe?

        # Next 3 can all be handled by _getListItemsByName_()
        if (s in [ "#text", "#comment", "#pi", "#cdata" ]): return PyNode.ARG_RESERVED
        if (s == "*"): return PyNode.ARG_STAR
        if (s[0] == "@" and PyNode.isXmlName(s[1:])): return PyNode.ARG_ATTRIBUTE
        if (PyNode.isXmlName(s)): return PyNode.ARG_NAME
        #if (s == ".."): return PyNode.ARG_ANCESTOR
        raise IndexError("Unrecognized argument type for '%s'." % (s))

    def _getChildNodesByName_(self:Node, name:str) -> list:
        """Return a list of this node's children of a given element name
        '*' gets all element children, but no pi, comment, text....
        """
        return self._getListItemsByName_(self.childNodes, name)

    def _getListItemsByName_(self:Node, theList:list, s:str) -> list:
        """This accepts element type names, #text etc., and "*".
        No attributes or ints here.
        """
        typ = PyNode.argType(s)
        if (typ not in [ PyNode.ARG_RESERVED, PyNode.ARG_STAR, PyNode.ARG_NAME ]):
            raise IndexError(
                "Node index '%s' is not reserved, '*', or an element type name." % (s))
        inodes = []
        for item in theList:
            if (item.nodeType==Node.ELEMENT_NODE and (s=='*' or item._nodeName==s)):
                inodes.append(item)
        return inodes


###############################################################################
# Test driver
#
if __name__ == "__main__":
    import argparse

    def warn(lvl:int, msg:str) -> None:
        if (args.verbose >= lvl): sys.stderr.write(msg + "\n")

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        args0 = parser.parse_args()
        return args0


    ###########################################################################
    #
    args = processOptions()

    warn(0, "Patching extensions onto xml.dom.minidom.Node...")
    Node.__getitem__ = PyNode.__getitem__
    Node._getChildNodesByName_ = PyNode._getChildNodesByName_
    Node. _getListItemsByName_ = PyNode. _getListItemsByName_

    theDocEl = Document()
    theDocEl.nodeName = "book"
    print("Document nodeName is '%s'." % (theDocEl.nodeName))
    body = theDocEl.createElement("body")
    theDocEl.appendChild(body)
    print("body element nodeName is '%s'." % (body.nodeName))

    nParas = 10
    for i in range(nParas):
        e = theDocEl.createElement("p")
        e.setAttribute("id", "myId_%2d" % (i))
        e.appendChild(theDocEl.createTextNode("This is a some text."))
        body.appendChild(e)

    print("Sample document created.")

    for i in range(0,nParas,2):
        print("ch %d: type '%s'" % (i, body[i].nodeName))
        print("    id: %s" % (body[i]["@id"]))

    warn(0, "Done.")
