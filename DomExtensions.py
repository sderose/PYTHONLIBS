#!/usr/bin/env python
#
# DomExtensions: A bunch of useful additions to the DOM API.
#
#pylint: disable=W0613, W0212
#
from __future__ import print_function
import sys
import re
#import string
import codecs
import xml.dom, xml.dom.minidom
from xml.dom.minidom import Node

descr = """
=head1 Usage

An XML-manipulation package that sits on top of a DOM implementation
and provides higher-level, XPath-like methods.
You can use I<patchDOM>() to monkey-patch these routines into a class
(default: I<xml.dom.Node>).

It's very often useful to walk around the XPath 'axes' in a DOM tree.
When doing so, it's often useful to consider only element nodes,
or only #text nodes, or only element nodes of a certain element type, or
with a certain attribute or attribute-value pair.

    import xml.dom
    dd.patchDom(toPatch=xml.dom.Node)
    dd = xml.dom.minidom.Document()

then use any of the additional methods on toPatch=xml.dom.Node

DomExtensions also provides support for:

* generating and interpreting XPointers.
* attributes whose values inherit, similar to xml:lang
* quick testing of containment and order relationships
* creation of formatted XML for tags, subtrees, etc., including indentation
* escaping for content, attributes, cdata, pis, and comments
* managing whitespace-only text nodes and Unicode whitespace normalization
* more flexible local restructuring such as wrapping unwrapping, splitting,
and combining nodes.
* node iterators so you don't have to recurse and filter
* higher-level methods such as for finding left and right extremes of
a subtree; lowest common ancestor; etc.
* change or case-fold element type names.

=head2 Node-selection methods

For the relevant XPath axes there are methods that will return the n-th
node of a given type and/or attribute along that axis.
For example (using the Child axis, but you can substitute
Descendant, PrecedingSibling, FollowingSibling, Preceding, Following,
or Ancestor:

    selectChild(node, n, type, attributeName, attributeValue)

This will return the I<n>th child of I<node> which:
is of the given element I<type>,
and has the given I<attributeName>=I<attributeValue> pair.
All arguments except I<node> are optional.

=over

=item * I<n> must currently be positive, though using negative numbers
to count back from the end will likely be added.

=item * If I<type> is undefined or '', any node type is allowed.
If it is '*', any *element* is allowed.
In either case, attribute constraints may still apply.
Full regexes are not (yet) supported.

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

=item * B<getInheritedAttribute(node, name)>

Return the value of attribute I<name>, from the first node along the
I<ancestor-or-self> axis of I<node> that specifies it.
Thus, the attribute's value is inherited down the tree, similar to I<xml:lang>.

=item * B<getCompoundAttr(self, name, sep='#', keepMissing=False)

Return the concatenation of the values of the named attribute,
from all ancestors (and self). Separate them with 'sep'.
This facilitates a notion of compound keys (or hierarchical IDs).

=item * B<leftBranch>(node)

Return the leftmost descendant of I<node>.
If I<node>'s first child has no children of its own, then it is
also I<node>'s first descendant; otherwise, it will not be.

=item * B<rightBranch>(node)

Return the rightmost (last) descendant of I<node>.

=item * B<getNChildNodes(node)>

Return the number of (direct) child nodes. This is preferable to asking
for C<len(node.childNodes)>, because some implementations may not keep
all childNodes as a physical array underneath, and would have to collect it,
only to then measure it and discard the collection again (hopefully they'll
cache it, but still....).

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

=item * B<XPointerCompare(x1, x2)>

Compare two XPointer child-sequences (see I<getXPointer>)
for relative document order, returning -1, 0, or 1.
This does not require actually looking at a document, so no document or
node is passed.

=item * B<nodeCompare(n1, n2)>

Compare two nodes for document order, returning -1, 0, or 1.

=item * B<XPointerInterpret(document, x)>

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

=item * B<normalize>(node)

Coalesce adjacent text nodes, and delete empty ones.

=item * B<insertPrecedingSibling>(I<node, newNode>)

=item * B<insertFollowingSibling>(I<node, newNode>)

=item * B<insertParent>(I<node, type>)

=item * B<mergeWithFollowingSibling>(node)

The following-sibling of I<node> is deleted, but its text content
is appended to I<node>.
This drops any sub-structure of the current and sibling.
New. See also the C<diffCorefs> command.

=item * B<mergeWithPrecedingSibling>(node)

=item * B<groupSiblings(node1, node2, typeForNewParent)>

Group all the nodes from I<node1> through I<node2> together, under a
new node of type I<typeForNewParent>. Fails if the specified nodes are
not siblings or are not defined.

=item * B<promoteChildren>(node)

Remove I<node> but keep all its children, which becomes siblings at the same
place where I<node> was.

=item * B<splitNode>(node, childNode, offset)

Breaks I<node> into 2 new sibling nodes of the same type.
The children preceding and including I<childNode> end up
under the first resulting sibling node; the rest under the second.
However, if I<childNode> is a text node and I<offset> is provided,
then I<childNode> will also be split, with the characters preceding and
including I<offset> (counting from 1) becoming a final text node under
the first new sibling node, and the rest becoming an initial text node
under the second.
(not yet supported)

=item * B<forEachNode(node, preCallback, postCallback)>

Traverse the subtree headed at I<node>,
calling the callbacks before and after traversing each node's subtree.

=item * B<forEachTextNode(node, preCallback, postCallback)>

Like I<forEachNode>(), but callbacks are I<only> called when at text nodes.

=item * B<forEachElement(node, preCallback, postCallback)>

Like I<forEachNode>(), but callbacks are I<only> called when at element nodes.

=item * B<forEachElementOfType(node, type, preCallback, postCallback)>

Like I<forEachNode>(), but callbacks are I<only> called when at
element nodes whose type name matches I<type> (which may be a regex).

=item * B<generateSaxEvents(self, handlers=None)>

Generate the same SAX events that would be encountered if the node passed
were parsed as a document. I<handlers> is a dict, with some or all of theDoc
following keys, whose values are the handlers to be called when that event
type occurs (or None):

    'XmlDeclHandler',
    'StartElementHandler',
    'EndElementHandler',
    'CharacterDataHandler',
    'ProcessingInstructionHandler',
    'CommentHandler'.

Events are not generated (yet) for Initial or Final, and CDATA marked sections
generate a regular CharacterDataHandler event.

=item * B<collectAllText(node, delimiter)>

Concatenate together the content of
all the text nodes in the subtree headed at I<node>,
putting I<delimiter> (default: space) in between.


=item * B<collectAllXml2>(node,
    delim=" ",
    indentString='    ',
    emitter=None,
    schemaInfo=None,
    lineBreak="\n",
    emptyForm="HTML",
    strip=False
)

(newer version of collectAllXml, in testing).
I<emitter' can be an instance of class Emitter (also defined here), which
will get passed the generated result strings in document order. The provided
class has options to write them to a path or file handle, collect them in
a string buffer, or call some other callback for each. By default, the result
is collected in a string and passed back whole.

=item * B<collectAllXml> (node, delim=" ", indentString='    ',
    emitter=None, schemaInfo=None)

Generate the XML representation for the subtree headed at I<node>.
It knows about elements, attributes, pis, comments, and appropriate escaping.
However, it won't do anything for CDATA sections (other than escape as
needed), XML Declaration, DOCTYPE, or any DTD nodes.

=item * B<export(element, fileHandle, includeXmlDecl, includeDoctype)>

Save the subtree headed at I<element> to the I<fileHandle>.
If I<includeXmlDecl> is present and True, start with an XML declaration.
If I<includeDoctype> is present and True, include a DOCTYPE declaration,
using I<element>'s type as the document-element name, and include any
DTD information that was available in the DOM (unfinished).
See also XML::DOM::Node::toString(),
XML::DOM::Node::printToFile(), XML::DOM::Node::printToFileHandle().

This is effectively shorthand for I<collectAllXml>(), but isn't implemented
that way yuet.

=back


=head2 Index (internal package)

(not yet implemented)

=over

=item * B<buildIndex>(attributeName)

Return a hash table in which each
entry has the value of the specified I<attributeName> as key, and the element
on which the attribute occurred as value.
This is similar to the XSLT 'key' feature.

=item * B<find(value)>

=back


=head2 Character stuff (internal methods)

=over

=item * B<escapeXmlAttribute(string)>

Escape the string as needed for it to
fit in an attribute value (amp, lt, and quot).

=item * B<escapeXml(string)>

Escape the string as needed for it to
fit in XML text content (amp, lt, and gt when following "]]").

=item * B<escapeCDATA(string)>

Escape the string as needed for it to
fit in a CDATA marked section (only gt when following ']]').
XML does not specify a way to escape this. The result produced here is "]]&gt;".

=item * B<escapeComment(string)>

Escape the string as needed for it to
fit in a comment ('--').
XML does not specify a way to escape this. The result produced here is "-&#x002d;".

=item * B<escapePI(string)>

Escape the string as needed for it to
fit in a processing instruction (just '?>').
XML does not specify a way to escape this. The result produced here is "]]&gt;".

=item * B<escapeASCII(string)>

Escape the string as needed for it to
fit in XML text content, *and* recodes and non-ASCII characters as XML
numeric characters references.

=item * B<unescapeXml(string)>

Change XML numeric characters references, as
well as references to the 5 pre-defined XML named entities, into the
corresponding literal characters.

=item * B<normalizeSpace(self, s, allUnicode=False)>

Do the usual XML white-space normalization on the string I<s>.
If I<allUnicode> is set, include not just the narrow set of C<[ \t\r\n]>,
but all Unicode whitespace (which, btw, does not include ZERO WIDTH SPACE U+200b).

=back


=head1 Known bugs and limitations

I<selectChild>() and its kin should probably permit selecting elements and
attributes via regexes.


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

C<dtdKnowledge.pm> -- Only available in Perl so far. Provides pretty-printing specs for schemas, to be used by I<collectAllXml>().


=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see L<http://www.derose.net/steve/utilities> or
L<http://github/com/sderose>.


=head1 History

*Written 2010-04-01~23 by Steven J. DeRose (in Perl).
*...
*2012-01-10 sjd: Start port to Python.
*2016-01-05: Fix previous/next. Add monkey-patching.
*2018-02-07: Sync with new AJICSS Javascript API. Add/fix various.
*2018-04-11: Support unescaping HTML named special character entities.
*2019-12-13ff: Clean up inline doc. Emitter class. collectAllXml2. lint.
Pull in other extensions implemented in my BaseDom.py (nee RealDOM.py).
Generate SAX.


=head1 To do

* Sync with XPLib.js
* Consider additions from https://lxml.de/api/index.html:
*     strip_attributes,....
* Move in matchesToElements from mediaWiki2HTML.
* Make all select... use a generic axisSelect? Probably not, because it
might make it harder to optimize for particular axes.
* Add insertPrecedingSibling, insertFollowingSibling, insertParent, insertAfter.
* Implement splitNode (see help)
* Find next node of given qgi? Select by qgi?
* Perhaps integrate XmlOutput.pm under Emitter?
* String to tag converter, like for quotes?
* String to entity ref, like for quotes, dashes, odd spaces, etc.
* Un-namespace methods: merge ns1/ns2; change prefix/url; drop all;....
* Normalize line-breaks within text nodes
* Allow choice of how to 'escape' PIs and comments.

=cut
"""

__metadata__ = {
    'title'        : "DomExtensions",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2010-01-10",
    'modified'     : "2019-12-24",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

PY3 = sys.version_info[0] == 3
if PY3:
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): str(s, encoding, errors)
    def cmp(a, b): return  ((a > b) - (a < b))


###############################################################################
#
def patchDOM(toPatch=xml.dom.Node, getItem=True):
    """Some people capitalize acronyms.
    """
    patchDom(toPatch, getItem)

def patchDom(toPatch=xml.dom.Node, getItem=True):
    """Monkey-patch the extension methods into a given class.
    TODO: Could do by scanning class for all callables....
    """
    testCase = getattr(xml.dom.Node, "selectAncestor", None)
    if (testCase and callable(testCase)): return

    if (getItem): toPatch.getItem   = getItem

    toPatch.selectAncestor          = selectAncestor
    toPatch.selectChild             = selectChild
    toPatch.selectDescendant        = selectDescendant
    toPatch.selectDescendantR       = selectDescendantR

    toPatch.selectPreceding         = selectPreceding
    toPatch.selectPrevious          = selectPreceding
    toPatch.getPrecedingAbsolute    = getPrecedingAbsolute
    toPatch.getPreceding            = getPreceding
    toPatch.getPrevious             = getPreceding
    toPatch.previous                = getPreceding

    toPatch.selectFollowing         = selectFollowing
    toPatch.getFollowingAbsolute    = getFollowingAbsolute
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

    toPatch.getLeastCommentAncestor = getLeastCommentAncestor
    toPatch.getLeftBranch           = getLeftBranch
    toPatch.getRightBranch          = getRightBranch
    toPatch.getNChildNodes          = getNChildNodes
    toPatch.getChildNumber          = getChildNumber
    toPatch.getDepth                = getDepth
    toPatch.getFQGI                 = getFQGI

    toPatch.isWithinType            = isWithinType
    toPatch.isDescendantOf          = isDescendantOf
    toPatch.isWithin                = isWithin

    toPatch.getXPointer             = getXPointer
    toPatch.XPointerCompare         = XPointerCompare
    toPatch.nodeCompare             = nodeCompare
    toPatch.XPointerInterpret       = XPointerInterpret

    toPatch.nodeMatches             = nodeMatches
    toPatch.getInheritedAttribute   = getInheritedAttribute
    toPatch.getCompoundAttr         = getCompoundAttr
    toPatch.getEscapedAttributeList = getEscapedAttributeList

    toPatch.removeWhiteSpaceNodes   = removeWhiteSpaceNodes
    toPatch.removeNodesByTagName    = removeNodesByTagName
    toPatch.untagNodesByTagName     = untagNodesByTagName
    toPatch.renameByTagName         = renameByTagName
    toPatch.forceTagCase            = forceTagCase
    toPatch.getAllDescendants       = getAllDescendants

    toPatch.normalizeAllSpace       = normalizeAllSpace
    toPatch.normalize               = normalize
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
    toPatch.generateSaxEvents       = generateSaxEvents

    toPatch.collectAllText          = collectAllText
    toPatch.collectAllXml2          = collectAllXml2
    toPatch.collectAllXml2r         = collectAllXml2r
    toPatch.collectAllXml           = collectAllXml
    toPatch.export                  = export

    toPatch.escapeXmlAttribute      = escapeXmlAttribute
    toPatch.escapeXml               = escapeXml
    toPatch.escapeCDATA             = escapeCDATA
    toPatch.escapeComment           = escapeComment
    toPatch.escapePI                = escapePI
    toPatch.escapeASCII             = escapeASCII

    toPatch.unescapeXml             = unescapeXml
    toPatch.normalizeSpace          = normalizeSpace

    #NamedNodeMap.iteritems = nnmIteritems
    return


###########################################################################
def __getitem__(self, n1, n2=None, n3=None):
    """
    Access nodes via Python list notation, based on my paper:
      DeRose, Steven J. JSOX: A Justly Simple Objectization for XML:
      Or: How to do better with Python and XML.
      Balisage Series on Markup Technologies, vol. 13 (2014).
      https://doi.org/10.4242/BalisageVol13.DeRose02.

    TODO: Count from 0 or 1 for this?
    TODO: Perhaps allow regexes for name?
    TODO: Perhaps extend [] to support any jQuery-style CSS selector?

    For example:
       myElement['p']       get the 1st 'p' child
       myElement['p':3]     get the 3rd 'p' child
       myElement[3:'p']         [same as ['p':3]]
       myElement['p':3:8]   get the 3rd through 7th 'p' children
       myElement[3:8]       get the 3rd through 7th children
       myElement[3:8:'p']   of the 3rd through 7th children, get the 'p's
       myElement['@class']  get the 'class' attribute's value
       myElement[1:10:2]    get every other childNode from 1 to 10.
    """
    nargs = 1
    if (n2 is not None): nargs = 2
    if (n3 is not None): nargs = 3

    if (nargs==1):
        if (isinstance(n1, int)):
            return self.childNodes[n1]
        if (n1 == '*'):
            return self._getChildNodesByName_('*')
        if (n1.startswith('@')):
            return self.attributes.getNamedItem(n1[1:])
        return self._getChildNodesByName_(n1)[0]

    elif (nargs==2):
        if (isinstance(n1, int)):
            if (isinstance(n2, int)):
                return self.childNodes[n1:n2]
            else:
                return self._getChildNodesByName_(n2)[n1]
        else:
            if (isinstance(n2, int)):
                return self._getChildNodesByName_(n1)[n2]
            else:
                raise TypeError("Found [str, non-int] for a Node")

    else: # nargs==3
        if (isinstance(n1, int) and isinstance(n2, int)):
            if (isinstance(n3, int)):
                return self.childNodes[n1:n2:n3]
            else:
                nodeList = self.childNodes[n1:n2]
                return self._getListItemsByName_(nodeList, n3)
        elif (isinstance(n2, int) and isinstance(n3, int)):
            return self._getChildNodesByName_(n1)[n2:n3]
        else:
            raise TypeError(
                "No 2 adjacent ints in [%s,%s,%s] for a Node." %
                (n1, n2, n3))

def _getChildNodesByName_(self, name):
    """
    Return a list of this node's children of a given element name
    '*' gets all element children, but no pi, comment, text....
    """
    cnodes = []
    for ch in self.childNodes:
        if (ch.nodeType==ELEMENT_NODE and
            (name=='*' or ch._nodeName==name)):
            cnodes.append(ch)
    return cnodes

def _getListItemsByName_(self, theList, name):
    """
    """
    inodes = []
    for item in theList:
        if (item.nodeType==ELEMENT_NODE and
            (name=='*' or item._nodeName==name)):
            inodes.append(item)
    return inodes


###############################################################################
# Methods to make minidom (or whatever) look like JS DOM.
#
def nnmIteritems(self):  # For NamedNodeMap, which lacks this.
    """
    """
    for k in self.keys:
        yield (k, self[k])

def outerHtml(self):
    """
    """
    t = self.getStartTag() + self.innerHTML() + self.getEndTag()
    return t

def innerHtml(self):
    """
    """
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
            t += "<![CDATA[%s]]>" % (escapeCDATA(curNode.textContent))
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
        #elif (ty == ATTRIBUTE_NODE):
        #    (done by ELEMENT_NODE)
        else:
            sys.exit("Unknown node type %d." % (ty))
    return t

def innerText(self, sep=''):
    """
    Like usual innertext, but a function (instead of a property), and allows
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
    return t


###############################################################################
# Methods for finding the nth node along a given axis, that has a given
# element type and/or attribute/value.
#
# TODO: n counts from 0, or negative to go from end.
#
def selectAncestor(self, n=1, elType=None, aname=None, avalue=None):
    """Return the first/nth ancestor that fits the requirements.
    """
    if (not elType): elType = ""
    cur = self.parentNode()
    return cur.selectAncestorOrSelf(
        n=n, elType=elType, aname=aname, avalue=avalue)

def selectAncestorOrSelf(self, n=1, elType=None, aname=None, avalue=None):
    """Like selectAncestor(), but the node itself is also considered.
    TODO: Support -n
    """
    if (not elType): elType = ""
    found = 0
    cur = self
    while (cur):
        if (cur.nodeMatches(elType, aname, avalue)):
            found += 1
            if (found >= n): return cur
        cur= cur.parentNode()
    return None

def selectChild(self, n=1, elType=None, aname=None, avalue=None):
    """n can be nagative.
    """
    if (not elType): elType = ""
    found = 0
    if (n >= 0):
        cur = self.getFirstChild()
        while (cur):
            if (self.nodeMatches(elType, aname, avalue)):
                found += 1
                if (found >= n): return cur
            cur = cur.nextSibling()
    else:
        cur = self.getLastChild()
        while (cur):
            if (self.nodeMatches(elType, aname, avalue)):
                found += 1
                if (found >= -n): return cur
            cur = cur.precedingSibling()

    return None

def selectDescendant(self, n=1, elType=None, aname=None, avalue=None):
    """
    TODO: Support -n
    """
    return selectDescendantR(n, elType, aname, avalue)

def selectDescendantR(self, n=1, elType=None, aname=None, avalue=None):
    """
    TODO: Support -n
    """
    found = 0
    if (self.nodeMatches(elType, aname, avalue)):
        found += 1
        if (found >= n): return self
    for ch in self.childNodes:
        node = self.getDescendantByAttributeR(ch, n, elType, aname, avalue)
        if (node):
            found += 1
            if (found >= n): return ch
    return None


# TODO: Add selectDescendantOrSelf

def selectPreceding(self, n=1, elType=None, aname=None, avalue=None):
    """
    TODO: Support -n
    """
    if (not elType): elType = ""
    cur = getPreceding(self)
    found = 0
    while (cur):
        if (isWithin(self, cur)): continue  # No ancestors, please.
        if (cur.nodeMatches(elType, aname, avalue)):
            found += 1
            if (found >= n): return cur
        cur=getPreceding(cur)
    return None

def getPreceding(self):
    """Get the immediately preceding node, if any. This includes earlier
    descendents= of ancestors, but not ancestors themselves, as in XPath.
    """
    cur = self
    while (cur):
        ns = cur.precedingSibling()
        if (ns):
            rb = ns.rightBranch()
            if (rb): return rb
        cur = cur.parentNode
    return None

def getPrecedingAbsolute(self):
    """Get the immediately preceding node, but (unlike XPath) also considering
    ancestors themselves.
    """
    cur = self
    while (cur):
        ns = cur.getPrecedingSibling()
        if (ns):
            rb = ns.rightBranch()
            if (rb): return rb
            return ns
        cur = cur.parentNode
    return None

def selectFollowing(self, n=1, elType=None, aname=None, avalue=None):
    """As in XPath, does not include descendants.
    See https://stackoverflow.com/questions/44377798/
    TODO: Support -n
    """
    if (not elType): elType = ""
    cur = self.getFollowing()
    found = 0
    while (cur):
        if (cur.nodeMatches(elType, aname, avalue)):
            found += 1
            if (found >= n): return cur
        cur = self.getFollowing()
    return None

def getFollowing(self):
    """As in XPath, does not include descendants.
    See https://stackoverflow.com/questions/44377798/
    """
    cur = self
    while (cur):
        ns = cur.nextSibling()
        if (ns): return ns
        cur = cur.parentNode
    return None

def getFollowingAbsolute(self):
    """Get the next node in document order, but (unlike XPath), also considering
    descendents (namely the first child).
    """
    if (self.firstChild): return self.firstChild
    cur = self
    while (cur):
        ns = cur.nextSibling()
        if (ns): return ns
        cur = cur.parentNode
    return None

def selectPrecedingSibling(self, n=1, elType=None, aname=None, avalue=None):
    """
    TODO: Support -n
    """
    if (not elType): elType = ""
    cur = self.getPreviousSibling()
    found = 0
    while (cur):
        if (cur.nodeMatches(elType, aname, avalue)):
            found += 1
            if (found >= n): return cur
        cur = cur.getPreviousSibling()
    return None

def selectFollowingSibling(self, n=1, elType=None, aname=None, avalue=None):
    """
    TODO: Support -n
    """
    if (not elType): elType = ""
    cur = self.getFollowingSibling()
    found = 0
    while (cur):
        if (cur.nodeMatches(elType, aname, avalue)):
            found += 1
            if (found >= n): return cur
        cur = cur.getFollowingSibling()
    return None


### Useful synonyms
#
def getPrecedingSibling(self):
    return self.previousSibling
def previousSibling(self):
    return self.previousSibling
def selectPreviousSibling(self, **w):
    self.selectPrecedingSibling(*w)

def getFollowingSibling(self):
    return self.nextSibling
def nextSibling(self):
    return self.nextSibling
def selectNextSibling(self, **w):
    self.selectFollowingSibling(*w)

# No select for root, self, attribute, or namespace axes.


###############################################################################
#
def getLeastCommentAncestor(self, other):
    """Return the smallest node that is an ancestor of both nodes.
    """
    other = other.parentNode
    while (other):
        if (self.isDescendantOf(other)): return other
        other = other.parentNode
    return None

def getLeftBranch(self):
    """
    Find the furthest node down if you always go left.
    """
    cur = self
    while (cur.firstChild): cur = cur.firstChild
    return cur

def getRightBranch(self):
    """
    Find the furthest node down if you always go right.
    """
    cur = self
    while (cur.lastChild): cur = cur.lastChild
    return cur

def getFirstChild(self, nodeType=None):
    return self.selectChild(self, n=1, elType=nodeType)

def getLastChild(self, nodeType=None):
    return self.selectChild(self, n=-1, elType=nodeType)

def getNChildNodes(self, nodeType=None):
    """Return the number of children of the current node.
    TODO: Node implementations that don't use physical arrays
    may want to override this for speed.
    """
    if (not nodeType): return len(self.childNodes)
    n = 0
    for ch in self.childNodes:
        if (ch.nodeType == ELEMENT_NODE and
            (nodeType=='*' or nodeType==ch.nodeName)): n += 1
    return n

def getChildNumber(self, nodeType=None):
    """Return the number of this node among its siblings.
    @param nodeType: If specified, only count siblings that are elements of
    the specified type ('*' for all).
    """
    n = 0
    for ch in self.parentNode.childNodes:
        if (nodeType is None or
            (ch.nodeType == ELEMENT_NODE and
             (nodeType=='*' or nodeType==ch.nodeName))): n += 1
        if (ch==self): return n
    return None

def getDepth(self):
    """
    How far down are we? Document element is 1.
    """
    d = 0
    cur = self
    while (cur):
        d = d + 1
        cur = cur.parentNode()
    return d

def getChildIndex(self, onlyElements=True):
    """Return the position in order, among the node's siblings.
    The first child is [0]!
    """
    assert (self.nodeType in [ ELEMENT_NODE, TEXT_NODE, COMMENT_NODE,
        CDATA_SECTION_NODE, PROCESSING_INSTRUCTION_NODE ])
    par = self.parentNode
    if (not par): return -1
    n = 0
    for sib in par.childNodes:
        if sib.isSameNode(self): return n
        if (onlyElements==False or sib.nodeType==ELEMENT_NODE): n += 1
    raise(ValueError)

def getFQGI(self):
    """
    """
    assert (self.nodeType == ELEMENT_NODE)
    f = ""
    cur = self
    while (cur):
        f = "/" + self.nodeName + f
        cur = cur.parentNode()
    return f

def isWithinType(self, elType):
    """
    Test whether a node has an ancestor of a specified element type.
    """
    cur = self
    while (cur):
        if (cur.nodeName == elType): return True
        cur = cur.parentNode()
    return False

def isDescendantOf(self, node):
    return isWithin(self, node)

def isWithin(self, node):
    """
    Test whether some specific node is an ancestor of the given node.
    """
    cur = self.parentNode()
    while (cur):
        if (cur == node): return True
        cur = cur.parentNode()
    return False


###############################################################################
# XPointer support
#
def getXPointer(self):
    """Get a simple numeric XPointer to the node, as a string.
    """
    f = ""
    cur = self
    while (cur):
        f = "/%s%s" % (cur.parentNode().getChildIndex(cur)+1, f)
        cur = cur.parentNode()
    return f

def XPointerCompare(self, xp1, xp2):
    """Compare two purely numeric XPointers for relative order.
    Does not support ones with IDs.
    """
    if (not re.match(r'\d+(/\d+)*$', xp1)):
        raise ValueError("Invalid XPointer cseq: '%s'." % (xp1))
    if (not re.match(r'\d+(/\d+)*$', xp2)):
        raise ValueError("Invalid XPointer cseq: '%s'." % (xp2))
    t1 =  re.split(r'/', xp1)
    t2 =  re.split(r'/', xp2)
    i = 0
    while (i<len(t1) and i<len(t2)):
        if (t1[i] < t2[i]): return -1
        if (t1[i] > t2[i]): return 1
        i = i + 1
    # At least one of them ran out...
    return cmp(len(t1), len(t2))

def nodeCompare(self, other):
    """Compare two nodes for order.
    """
    return self.XPointerCompare(self.getXPointer(), other.getXPointer())

def XPointerInterpret(self,  xp):
    """Given an XPointer string, find the node (if it exists).
    """
    document = self.ownerDocument()
    node = document.getDocumentElement()
    t = re.split(r'/', xp)
    if (re.match(r'^\d+', t[0])):               # Leading ID:
        idNode = document.getNamedNode(t[0])
        if (not idNode): return None
    i = 0
    while (i<len(t)):
        node = node.getChildAtIndex(t[i])
        if (not node): return None
        i = i + 1
    return node


###############################################################################
# @TODO UPDATE TO MATCH AJICSS.js
#
def nodeMatches(self, elType=None, aname=None, avalue=None):
    """Check if a node matches the supported selection constraints.
    Used by all the selectAXIS() methods.

    @param elType:
        An integer DOM nodeType number
        /regex/ to match node name (like BS4)
        '*' or '' (default) for any element
        '#' plus a DOM nodeType name (can omit '_NODE', or abbreviate)
        '#WSOTN' for non-white-space-only text nodes,
        '#NWSOTN' for anything that's not a WSOTN
        '#ET' for elements and non-white-space-only text nodes
        A literal node name

    @param aname: if non-nil, attribute must exist
    @param avalue: if non-nill, attribute aname must = avalue.

    @TODO: Support nodeTypes in sync w/ Javascript packages.
    """
    if (elType and elType != ""):              # check type constraint:
        if (elType == "*"):
            if (self.nodeType!=ELEMENT_NODE): return 0
        else:
            if (self.nodeName != elType): return 0

    if (not aname): return 1
    if (self.getNodeName == "#text"): return 0

    thisvalue = self.getAttribute(aname)
    if (not thisvalue):                              # attr specified, absent:
        return 0
    if (not avalue or thisvalue == avalue):          # attr matches:
        return 1
    return 0


def getInheritedAttribute(self, aname):
    """Search upward to find an assignment to an attribute, and return the
    nearest non-empty one (or None if none is found).
    This is similar to the defined semantics of xml:lang.
    """
    cur = self
    while (cur):
        avalue = cur.getAttribute(aname)
        if (avalue is not None and avalue!=''): return avalue
        cur = cur.parentNode()
    return None

def getEscapedAttribute(self, aname):
    """
    """
    avalue = self.getAttribute(aname)
    return escapeXmlAttribute(avalue)

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
    return None

def getStartTag(self, sortAttributes=False):
    """
    Generate a start tag for the given element.
    TODO: support sorting.
    """
    assert (sortAttributes==False)
    buf = "<%s" % (self.nodeName)
    if (self.getAttribute('id')):
        buf += ' id="%s"' % (self.getEscapedAttribute('id'))
    for a in (self.attributes):
        if (a == 'id'): continue
        buf += ' %s="%s"' % (a, self.getEscapedAttribute(a))
    buf += ">"
    return buf

def getEndTag(self, appendAttr='id'):
    """
    Generate a canonical end tag for the given element.
    @param appendAttr: If set, and the given element has an attribute with
    this name, put that attribute as a comment following the end-tag. This
    is handy when editing, esp. for large or deep documents.
    """
    buf = "</%s>" % (self.nodeName)
    if (appendAttr and self.getAttribute(appendAttr)):
        buf += '<!-- id="%s" -->' % (self.getAttribute(appendAttr))
    return buf

def getEscapedAttributeList(self, sort=False):
    """
    Assemble the entire attribute list, escaped as needed to write out as XML.
    """
    buf = ""
    if (not (self)): return None
    alist = self.attributes
    if (not (alist)): return buf
    anames = alist.keys()
    if (sort): sort(anames)
    for aname in anames:
        avalue = escapeXmlAttribute(self.getEscapedAttribute(aname))
        buf += '%s="%s"' % (aname, avalue)
    return buf


def addAttributeToken(self, attrName, token):
    """TODO Pull in code from JavaScript...
    """
    raise NotImplementedError("No addAttributeToken")

def removeAttributeToken(self, attrName, token):
    """
    """
    raise NotImplementedError("No removeAttributeToken")

def removeWhiteSpaceNodes(self):
    """
    """
    # print "running removeWhiteSpaceNodesCB\n"
    forEachNode(removeWhiteSpaceNodesCB, None)

def removeWhiteSpaceNodesCB(self):
    """This only deals with XML whitespace, not all Unicode.
    """
    if (not (self.getNodeName == "#text")): return
    t = self.data
    mat = re.search(xmlSpaceRegex, t, "")
    if (mat): return
    self.parentNode().removeChild(self)

def removeNodesByTagName(self, nodeName):
    """
    """
    nodes = self.getElementsByTagName(nodeName)
    ct = 0
    for node in nodes:
        node.parent.removeChild(node)
        ct += 1
    return ct

def untagNodesByTagName(root, nodeName):
    """
    """
    for t in root.getElementsByTagName(nodeName):
        tn = root.getDocument.createTextNode(t.innerText())
        t.parentNode.replaceChild(t, tn)

def renameByTagName(root, oldName, newName):
    """
    """
    for t in root.getElementsByTagName(oldName):
        t.nodeName = newName

def forceTagCase(root, upper=False, attributesToo=False):
    """Force all element (and optionally attribute) names in a subtree,
    to lower (or upper) case.
    """
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
    """
    Get a list of all descendants of the given node, in document order.
    @param excludeTypes: A list of nodeTypes to exclude (such as TEXT_NODE).
    """
    if ((not excludeTypes) or root.nodeType in excludeTypes):
        yield(root)
    for ch in root.childNodes:
        yield getAllDescendants(ch)
    return


###############################################################################
#
def normalizeAllSpace(self):
    """
    """
    forEachNode(normalizeAllSpaceCB, None)

def normalizeAllSpaceCB(self):
    """
    """
    if (self.getNodeName != "#text"): return
    self.setData(self.normalizeSpace(self.data))

def normalize(self):
    """Discard empty text nodes; coalesce adjacent ones.
    """
    for ch in self.childNodes:
        if (ch.nodeType == ELEMENT_NODE):
            ch.normalize()
        elif (ch.nodeType == TEXT_NODE):
            nxt = ch.followingSibling
            if (nxt and nxt.nodeType==TEXT_NODE):
                ch.data += nxt.data
                self.removeChild(nxt)

def addElementSpaces(self, exceptions=None):
    """Add spaces around all elements *except* those in list 'exceptions'.
    This is useful because most elements entail word-boundaries (say, things
    CSS would consider display:block). But little elements may not: such as
    HTML b, i, etc., and TEI var, sic, corr, etc.
    """
    raise NotImplementedError("No addElementSpaces")


###############################################################################
#
def insertPrecedingSibling(self, node):
    """
    """
    self.parentNode().insertBefore(node, self)
    return node

def insertFollowingSibling(self, node):
    """
    """
    par = self.parentNode()
    r = self.getFollowingSibling()
    if (r): par.insertBefore(node, r)
    else: par.appendChild(node)
    return node

def insertParent(self, elType):
    """
    TODO Allow a sequence of siblings
    """
    new = self.getOwnerDocument.createElement(elType)
    self.parentNode().replaceChild(new, self)
    new.appendChild(self)
    return new


###############################################################################
#
def mergeWithFollowingSibling(self, cur):
    """
    Following sibling goes away, but its children are appended to the node.
    """
    if (not (cur)): return None
    sib = cur.getFollowingSibling()
    if (not sib): return False
    while (cur.hasChildNodes()):
        cur.appendChild(sib.getFirstChild())
    cur.parentNode().removeChild(sib)

def mergeWithPrecedingSibling(self, cur):
    """
    Preceding sibling goes away, but its children are appended to the node.
    """
    if (not (cur)): return None
    sib = cur.getPrecedingSibling()
    if (not sib): return False
    while (cur.hasChildNodes()):
        cur.insertBefore(sib.getLastChild(), cur.getFirstChild())
    cur.parentNode().removeChild(sib)


###############################################################################
# Take a block of contiguous siblings and enclose them in a new intermediate
# parent node (which in inserted at the level they *used* to be at).
#
def groupSiblings(self, first, breakNode, newParentType):
    """
    """
    if (not first or not breakNode):
        raise ValueError("Must supply first and breakNode to groupSiblings\n")
    oldParent = first.parentNode()
    oldParent2 = breakNode.parentNode()
    if (not (oldParent == oldParent2)):
        raise ValueError("groupSiblings: first and last are not siblings!\n")
    newParent = first.getOwnerDocument().createElement(newParentType)
    oldParent.insertChildBefore(newParent, first)

    cont = cur = first
    while (cur):
        cont = cur.getFollowingSibling()
        moving = oldParent.removeChild(cur)
        newParent.insertBefore(moving, None)
        cur = cont


###############################################################################
# Remove the given node, promoting all its children.
#
def promoteChildren(self, ):
    """
    """
    parent = self.parentNode()
    cur = self.getFirstChild()
    while (cur):
        cont = cur.getFollowingSibling()
        moving = self.removeChild(cur)
        parent.insertBefore(moving, parent)
        cur = cont
    parent.removeChild(self)



###############################################################################
#
def forEachNode(self, callbackA=None, callbackB=None, depth=1):
    """Traverse a subtree given its root, and call separate callbacks before
    and after traversing each subtree. Callbacks might, for example,
    respectively generate the start- and end-tags for elements, and generate
    the text or data for other kinds of nodes.
    Attribute and namespace nodes are not visited.
    Callbacks are allowed to be None if not needed.

    If a callback returns True, we stop traversing.
    """
    if (not (self)): return 1
    name = self.nodeName
    if (callbackA):
        if (callbackA(name, depth)): return 1
    if (self.hasChildNodes()):
        #print ("Recursing for child nodes at level %s." % (depth+1))
        for ch in self.childNodes:
            rc = forEachNode(ch, callbackA, callbackB, depth+1)
            if (rc): return 1
    if (callbackB):
        if (callbackB(name, depth)): return 1
    return 0 # succeed


def forEachTextNode(self, callbackA=None, callbackB=None, depth=1):
    """Like forEachNode(), but only stops at text nodes.
    """
    if (not (self)): return 1
    name = self.nodeName
    if (callbackA and name == "#text"):
        if (callbackA(name, depth)): return 1
    if (self.hasChildNodes()):
        #print ("Recursing for child nodes at level %s." % (depth+1))
        for ch in self.childNodes:
            rc = forEachTextNode(ch, callbackA, callbackB, depth+1)
            if (rc): return 1
    if (callbackB and name == "#text"):
        if (callbackB(name, depth)): return 1
    return 0 # succeed


def forEachElement(self, callbackA=None, callbackB=None, depth=1):
    """Like forEachNode(), but only stops at element nodes.
    """
    if (not (self)): return 1
    name = self.nodeName
    if (callbackA and self.nodeType==ELEMENT_NODE):
        if (callbackA(name, depth)): return 1
    if (self.hasChildNodes()):
        #print ("Recursing for child nodes at level %s." % (depth+1))
        for ch in self.childNodes:
            rc = forEachElement(ch, callbackA, callbackB, depth+1)
            if (rc): return 1
    if (callbackB and self.nodeType==ELEMENT_NODE):
        if (callbackB(name, depth)): return 1
    return 0 # succeed

def forEachElementOfType(self, elementType, callbackA=None, callbackB=None, depth=1):
    """Like forEachNode(), but only stops at element nodes of a certain type.
    The type may be specified as a regex (watch out for '.' in names).
    """
    if (not self):
        raise ValueError("No element specified.\n")
    if (not elementType):
        raise ValueError("Bad element type '" + elementType + "' specified.\n")
    name = self.nodeName
    if (callbackA and self.nodeType==ELEMENT_NODE and
        re.match(elementType, self.getNodeName)):
        if (callbackA(name, depth)): return 1
    if (self.hasChildNodes()):
        #print ("Recursing for child nodes at level %s." % (depth+1))
        for ch in (self.childNodes):
            rc = forEachElementOfType(
                ch, elementType, callbackA, callbackB, depth+1)
            if (rc): return 1
    if (callbackB and self.nodeType==ELEMENT_NODE and
        re.search(elementType, self.getNodeName)):
        if (callbackB(name, depth)): return 1
    return 0  # succeed

def generateNodes(self):
    """Traverse a subtree given its root, and yield the nodes preorder.
    """
    if (not self): return
    yield self
    for ch in self.childNodes:
        yield ch.generateNodes()
    return

def generateSaxEvents(self, handlers=None):
    handlerNames = [
        'XmlDeclHandler',
        'StartElementHandler',
        'EndElementHandler',
        'CharacterDataHandler',
        'ProcessingInstructionHandler',
        'CommentHandler',
    ]
    for k, v in handlers.items:
        if (k not in handlerNames or (v and not callable(v))):
            raise ValueError("Bad handler '%s'." % (k))

    # Initial?
    if (handlers['XmlDeclHandler']):
        handlers['XmlDeclHandler'](self.ownerDocument.documentElement.nodeType)
    genSax(self, handlers)
    # Final?

def genSax(self, handlers):
    ntype = self.nodeType
    if (ntype == ELEMENT_NODE):                  # 1 ELEMENT
        if (handlers['StartElementHandler']):
            handlers['StartElementHandler'](self.nodeName, self.attributes)
        for ch in self.childNodes:
            genSax(ch, handlers)
        if (handlers['EndElementHandler']):
            handlers['EndElementHandler'](self.nodeName)
    elif (ntype == TEXT_NODE):                   # 3 TEXT
        if (handlers['CharacterDataHandler']):
            handlers['CharacterDataHandler'](self.data)
    elif (ntype == CDATA_SECTION_NODE):          # 4 CDATA
        if (handlers['CharacterDataHandler']):
            handlers['CharacterDataHandler'](self.data)
    elif (ntype == PROCESSING_INSTRUCTION_NODE): # 7 PI
        if (handlers['ProcessingInstructionHandler']):
            handlers['ProcessingInstructionHandler'](self.data)
    elif (ntype == COMMENT_NODE):                # 8 COMMENT
        if (handlers['CommentHandler']):
            handlers['CommentHandler'](self.data)
    elif (ntype == DOCUMENT_NODE):               # 9 DOCUMENT
        if (handlers['CommentHandler']):
            handlers['CommentHandler'](self.data)
    return

###############################################################################
#
# Following are also in xml.dom.
#
ELEMENT_NODE                 = 1
ATTRIBUTE_NODE               = 2    # Deprecated in DOM4
TEXT_NODE                    = 3
CDATA_SECTION_NODE           = 4
ENTITY_REFERENCE_NODE        = 5    # Deprecated in DOM4
ENTITY_NODE                  = 6    # Deprecated in DOM4
PROCESSING_INSTRUCTION_NODE  = 7
COMMENT_NODE                 = 8
DOCUMENT_NODE                = 9
DOCUMENT_TYPE_NODE           = 10
DOCUMENT_FRAGMENT_NODE       = 11
NOTATION_NODE                = 12   # Deprecated in DOM4

def collectAllText(self, delim=" ", depth=1):
    """Cat together all descendant text nodes, optionally with separators
    between. See also innerText(), collectAllXml().
    @todo: Option to collect only *directly* contained textnodes?
    @param delim: What to put between the separate text nodes
    @param depth: Just tracks the recursion level.

    *** Might be nicer to do like BaseDom.py (nee RealDOM.py), and define
    tostring() separately for each subclass of Node.
    """
    if (not (self)): return ""
    textBuf = ""
    if (self.nodeName == "#text"):
        dat = self.data
        if (dat):
            if (depth>1): textBuf = delim + dat
            else: textBuf = dat
    elif (self.hasChildNodes()):
        for ch in self.childNodes:
            textBuf = textBuf + collectAllText(ch, delim, depth+1)
    return textBuf


def getTextNodesIn(node):
    """Return just the text nodes under the specified starting node.
    By default, includes descendant text nodes; should add option to do
    just direct ones.
    See https://stackoverflow.com/questions/298750/
    """
    textNodes = []
    if (node.nodeType == Node.TEXT_NODE):
        textNodes.append(node)
    else:
        for i in (range(len(node.childNodes))):
            textNodes.extend(node.getTextNodes(node.childNodes[i]))
    return textNodes


###############################################################################
#
def collectAllXml2(self,
    delim=" ",               # put between text nodes
    indentString='    ',     # Repeat this to indent ("" not to)
    indentText=False,        # Break/indent before text nodes
    breakStarts=True,        # Break before start tags
    breakEnds=False,         # Break before end tags
    breakComments=True,      # Break/indent before comments
    breakPIs=True,           # Break/indent before processing instructions
    emitter=None,            # What Emitter object to use
    schemaInfo=None,         # Any schema-specific info (not yet used)
    lineBreak="\n",          # String to use for line-breaks
    emptyForm="HTML",        # Which syntax HTML/SGML/XML for empty elements
    strip=False              # Strip whitespace off text nodes?
    ):
    """
    Collect a subtree as WF XML, with appropriate escaping. Can also
    put a delimiter before each start-tag; if it contains '\n', then the
    XML will also be hierarchically indented. -color applies.

    @param emitter: An object that supports the API of 'Emitter' (see below).
    All results are sent to this object. Default: Emitter('STRING'),
    which concatenates everything into a string (other options include writing
    to a file or passing to a callback; or you can implement something else).
    """
    if (emitter is None): emitter = Emitter("STRING")
    cOptions = CollectorOptionsDef(
        delim,
        indentString,
        indentText,
        breakStarts,
        breakEnds,
        breakComments,
        breakPIs,
        emitter,
        schemaInfo,
        lineBreak,
        emptyForm,
        strip
        )
    self.collectAllXml2r(cOptions)
    return emitter.string

from collections import namedtuple
CollectorOptionsDef = namedtuple('CollectorOptions', [
    'delim',          # " "
    'indentString',   # '    '
    'indentText',     # False
    'breakStarts',    # True
    'breakEnds',      # False
    'breakComments',  # True
    'breakPIs',       # True
    'emitter',        # None
    'schemaInfo',     # None
    'lineBreak',      # "\n"
    'emptyForm',      # "HTML" or XML or SGML
    'strip',          # False
    ])

def ind(cOptions, depth, name="", isStart=True, isEnd=False):
    """Generate any needed linebreak + indentation. Should only be called
    for things that expect that (e.g., maybe not text).
    """
    pre = post = ""
    if (cOptions.schemaInfo):  # TODO: Finish
        si = cOptions.schemaInfo
        #isEmpty = si.getProp(name, "empty")
        dtype = si.getProp(name, "display")
        if (dtype and dtype != "inline"):
            nPreBreaks = si.getProp(name, 'pre')
            nPostBreaks = si.getProp(name, 'post')
            if (nPreBreaks > 0): pre = cOptions.lineBreak * nPreBreaks
            if (nPostBreaks > 0): post = cOptions.lineBreak * nPostBreaks
    else:
        if (isStart and cOptions.breakStarts): pre = cOptions.lineBreak
        if (isEnd and cOptions.breakEnds): post = cOptions.lineBreak

    return pre + (cOptions.indentString * max(0, depth-2)) + post

def collectAllXml2r(self, cOptions, depth=1):
    """
    """
    #sys.stderr.write("%scollectAllXml22 on a %s.\n" % (" " * depth, type(self)))
    # Save the options
    # Calculate whitespace to put around the element
    name = self.nodeName
    ntype = self.nodeType

    em = cOptions.emitter

    #sys.stderr.write("Emitting nodeType %d, name %s\n" % (ntype, name))

    isEmpty = 0

    # Assemble the data and/or markup
    #
    if (ntype == ELEMENT_NODE):                  # 1 ELEMENT
        textBuf = "%s<%s%s" % (ind(cOptions, depth, name=name),
            name, getEscapedAttributeList(self))
        if (isEmpty): textBuf += " />"
        else: textBuf += ">"
        em.emit(textBuf)

        for ch in self.childNodes:
            ch.collectAllXml2r(cOptions, depth+1)

        buf = ""
        if (em.lastCharEmitted() == cOptions.lineBreak[-1] or cOptions.breakEnds):
            buf = ind(cOptions, depth, name, isStart=False, isEnd=True)
        em.emit(buf + "</%s>" % (name))

    elif (ntype == ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Unexpected attribute node.")

    elif (ntype == TEXT_NODE):                   # 3 TEXT
        buf = ""
        if (cOptions.indentText): buf = ind(cOptions, depth, "#text")
        if (cOptions.strip): s = self.data.strip()
        else: s = self.data
        em.emit(buf + escapeXml(s))

    elif (ntype == CDATA_SECTION_NODE):          # 4 CDATA
        buf = ""
        if (cOptions.indentText): buf = ind(cOptions, depth, "#cdata")
        em.emit(buf + "<![CDATA[%s]]>" % (escapeCDATA(self.data)))
    elif (ntype == ENTITY_REFERENCE_NODE):       # 5
        pass #nop = 1
    elif (ntype == ENTITY_NODE):                 # 6
        pass #nop = 1
    elif (ntype == PROCESSING_INSTRUCTION_NODE): # 7 PI
        buf = ""
        if (cOptions.breakPIs): buf = ind(cOptions, depth, "#pi")
        em.emit(buf + "<?%s %s?>" % (self.target, escapePI(self.data)))

    elif (ntype == COMMENT_NODE):                # 8 COMMENT
        buf = ""
        if (cOptions.breakComments): buf = ind(cOptions, depth, "#comment")
        em.emit(buf + "<!-- %s -->" % (self.data))
    elif (ntype == DOCUMENT_NODE):               # 9 DOCUMENT_NODE
        #sys.stderr.write("DOCUMENT_NODE: docel %s, nchildren %d." %
        #    (type(self.documentElement), len(self.childNodes)))
        em.emit('<?xml version="1.0" encoding="utf-8"?>')
        if (not self.documentElement):
            for ch in self.childNodes:
                ch.collectAllXml2r(cOptions, depth+1)
        else:
            self.documentElement.collectAllXml2r(cOptions, depth+1)
    elif (ntype == DOCUMENT_TYPE_NODE):          # 10
        em.emit('<!DOCTYPE foo []>')  # TODO
    elif (ntype == DOCUMENT_FRAGMENT_NODE):      # 11
        pass #nop = 1
    elif (ntype == NOTATION_NODE):               # 12
        pass #nop = 1
    else:
        raise ValueError("startCB: Bad DOM nodeType returned: %s." % ntype)
    return


###############################################################################
def collectAllXml(self, delim=" ", indentString='    ',
    schemaInfo=None, lineBreak = "\n", depth=1):
    """
    Collect a subtree as WF XML, with appropriate escaping. Can also
    put a delimiter before each start-tag; if it contains '\n', then the
    XML will also be hierarchically indented. -color applies.
    """
    name = self.nodeName
    ntype = self.nodeType

    # Calculate whitespace to put around the element
    indent = ""
    isEmpty = 0
    if (schemaInfo):
        raise ValueError("Unsupported feature 'schemaInfo'.")
    else:
        if (indentString): indent = (indentString * depth)
        else: indent = delim

    # Assemble the data and/or markup
    textBuf = ""
    if (ntype == ELEMENT_NODE):                  # 1 ELEMENT:
        textBuf += (indentString * depth) + "<" + name + getEscapedAttributeList(self)
        if (isEmpty):
            textBuf = textBuf + "/>"
        else:
            textBuf = textBuf + ">"
            for ch in self.childNodes:
                textBuf = textBuf + collectAllXml(ch, delim, 1, depth+1)
            if (indentString):
                textBuf = textBuf + (indentString * depth)
            textBuf = textBuf + "</" + name + ">" + lineBreak
    elif (ntype == ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Why are we seeing an attribute node?")

    elif (ntype == TEXT_NODE):                   # 3 TEXT
        textBuf = textBuf + escapeXml(self.data)

    elif (ntype == CDATA_SECTION_NODE):          # 4
        pass
    elif (ntype == ENTITY_REFERENCE_NODE):       # 5
        pass
    elif (ntype == ENTITY_NODE):                 # 6
        pass
    elif (ntype == PROCESSING_INSTRUCTION_NODE): # 7 PI
        textBuf += "<?" + self.target + " " + self.data + "?>"

    elif (ntype == COMMENT_NODE):                # 8 COMMENT
        textBuf = textBuf + indent + "<!--" + self.data + "-->"
        if (indentString):
            textBuf = textBuf + lineBreak
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

    return textBuf
# collectAllXml


###############################################################################
fhGlobal = None  # TODO Unglobalize this.

def export(self, someElement, fh, includeXmlDecl=True, includeDoctype=False):
    """
    Write the whole thing to some file.
    See also XML::DOM::Node::toString(), printToFile(), printToFileHandle().
    """
    global fhGlobal
    fhGlobal = fh
    if (includeXmlDecl):
        fhGlobal.write("<?xml version=\"1.0\" encoding=\"utf8\"?>")
    if (includeDoctype):
        rootElType = someElement.getName
        fhGlobal.write("<!DOCTYPE " + rootElType + "PUBLIC '' '' []>")
    forEachNode(someElement, startCB, endCB, 0)


def startCB(self):
    """
    """
    buf = ""
    typ = self.nodeType
    if (typ == ELEMENT_NODE):                   # 1:
        buf = "<" + self.getNodeName + getEscapedAttributeList(self) + ">"
    elif (typ == ATTRIBUTE_NODE):               # 2
        pass
    elif (typ == TEXT_NODE):                    # 3
        buf = self.data
    elif (typ == CDATA_SECTION_NODE):           # 4
        buf = "<![CDATA["
    elif (typ == ENTITY_REFERENCE_NODE):        # 5
        pass
    elif (typ == ENTITY_NODE):                  # 6
        pass
    elif (typ == PROCESSING_INSTRUCTION_NODE):  # 7
        buf = "<?%s %s?>" % (self.target, escapePI(self.data))
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
    else:
        raise ValueError("startCB: Bad DOM nodeType %d." % (typ))
    fhGlobal.write(buf)

def endCB(self):
    """
    """
    buf = ""
    typ = self.nodeType

    if (typ == ELEMENT_NODE):                   # 1:
        buf = "</" + self.nodeName + ">"
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
    else:
        raise ValueError("endCB: Bad DOM nodeType %d." % (typ))

    fhGlobal.write(buf)

# END of DomExtensions definitions


###############################################################################
#
def escapeXmlAttribute(s, dquote=True):
    """
    Turn characters special in (double-quoted) attributes, into char refs.
    dquote: Set True if you prefer single-quoting your attributes.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r'&', "&amp;",   s)
    s = re.sub(r'<', "&lt;",    s)
    if (dquote):  s = re.sub(r'"', "&quot;",  s)
    else:   s = re.sub(r"'", "&apos;",  s)
    return s

def escapeXml(s, escapeAllGT=False):
    """Turn things special in text content, into char refs.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r'&',   "&amp;",  s)
    s = re.sub(r'<',   "&lt;",   s)
    if (escapeAllGT): s = re.sub(r'>', "&gt;", s)
    else: s = re.sub(r']]>', "]]&gt;", s)
    return s

def escapeCDATA(s):
    """XML Defines no particular escaping for this, we use char-ref syntax.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r']]>', "]]&gt;", s)
    return s

def escapeComment(s):
    """XML Defines no particular escaping for this, we use char-ref syntax.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r'--', "-&#x002d;", s)
    return s

def escapePI(s):
    """XML Defines no particular escaping for this, we use char-ref syntax.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r'\?>', "?&gt;", s)
    return s

def escapeASCII(s, width=4, base=16):
    """Turn all non-ASCII characters into character references.
    @param width: zero-pad numbers to at least this many digits.
    @param base: 10 for decimal, 16 for hexadecimal.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r'([^[:ascii:]])r', escASCIIFunction, s)
    s = escapeXml(s)
    return s

entityWidth = 4
entityBase = 16

def escASCIIFunction(mat):
    """Turn all non-ASCII chars to character refs.
    """
    if (entityBase==10):
        return "&#%*d;" % (entityWidth, ord(mat.group[1]))
    else:
        return "&#x%*x;" % (entityWidth, ord(mat.group[1]))

def nukeNonXmlChars(s):
    return re.sub("[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)

def unescapeXml(s):
    """
    """
    return re.sub(r'&(#[xX])?(\w+);', unescapeXmlFunction, s)

def unescapeXmlFunction(mat):
    """
    Convert HTML entities, and numeric character references, to literal chars.
    """
    from htmlentitydefs import name2codepoint  # , codepoint2name
    if (len(mat.group(1)) == 2):
        return unichr(int(mat.group[2], 16))
    elif (mat.group(1)):
        return unichr(int(mat.group[2], 10))
    elif (mat.group(2) in name2codepoint):
        return name2codepoint[mat.group(2)]
    else:
        raise ValueError("Unrecognized entity: '%s'." % (mat.group(0)))

xmlSpaceChars = " \t\r\n"
xmlSpaceRegex = re.compile("[%s]+" % (xmlSpaceChars))
#
def normalizeSpace(self, s, allUnicode=False):
    """
    By default, this only normalizes *XML* whitespace,
    per the XML spec, section 2.3, grammar rule 3.
    NOTE: Most methods of removing Unicode whitespace in Python do not work.
    See https://stackoverflow.com/questions/1832893/
    U+200B ZERO WIDTH SPACE is left untouched.
    """
    if (allUnicode):
        s = re.sub(r'(?u)\s+', " ", s, re.UNICODE)
    else:
        s = re.sub(xmlSpaceRegex, " ", s)
    s = s.strip(' ')
    return s


###############################################################################
###############################################################################
# Various places to put output data.
#
class Emitter:
    """Used by collectXML2 etc. to transmit data to any of several targets.
    This allows the same code to write to a file, a buffer, or whatever.
    """
    def __init__(self, where, arg=None):
        self.where        = where
        self.lastChar    = ""
        self.fh          = None
        self.string      = ""
        self.file        = ""
        self.cb          = ""
        self.totalLen    = 0

        #sys.stderr.write("Setting up emitter, type '%s'.\n" % (where))
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
            raise ValueError("New Emitter: unknown 'where': '%s'." % (where))
        return None

    def emit(self, text):
        #sys.stderr.write("*** Emit '%s'.\n" % (text))
        if (len(text)>0):
            self.lastChar = text[-1]
            self.totalLen += len(text)
        if (self.where == "STRING"):
            self.string += text
        elif (self.where == "FILE"):
            self.fh.write(text)
        elif (self.where == "FH"):
            self.fh.write(text)
        else:
            self.cb(text)

    def lastCharEmitted(self):
        return self.lastChar


###############################################################################
###############################################################################
#
class DomIndex(dict):
    """
    Index on an attribute.
    Adds every element that has a given attribute, to a hash keyed on that
    attribute's value. Hopes the values are unique.
    """
    def __init__(self, docOrNode, aname, duplicates=False):
        """Scan a document (or at least a subtree) and build a dict of the
        values found for a given attribute.
        @param document: Document or subtree head Node to scan.
        @param aname: Name of attribute to be indexed.
        @param duplicates: If True, just replace when there's a duplicate.
        """
        super(DomIndex, self).__init__()

        if (docOrNode.nodeType == DOCUMENT_NODE):
            self.document = docOrNode
            self.rootNode = docOrNode.getDocumentElement()
        else:
            self.document = docOrNode.ownerDocument
            self.rootNode = docOrNode
        self.attrName = aname

        node = self.rootNode
        finalNode = node.rightBranch
        while (node):
            if (node.nodeTypee==ELEMENT_NODE):
                key = node.getAttribute(aname)
                if (key):
                    if (key in self and duplicates==False):
                        raise IndexError("Duplicate key '%s'." % (key))
                    else:
                        self[key] = node
            if (node == finalNode): break
            node = node.getFollowing()

        return None


###############################################################################
###############################################################################
# Test driver
#
if __name__ == "__main__":
    import argparse

    def warn(lvl, msg):
        if (args.verbose >= lvl): sys.stderr.write(msg + "\n")

    def processOptions():
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return args0

    ###########################################################################
    #
    args = processOptions()

    warn(0, "Patching extensions onto xml.dom.Node...")
    patchDOM()
    if (callable(xml.dom.Node.getDepth)):
        warn(0, "Patch succeeded.")
    else:
        warn(0, "Patch failed.")

    if (len(args.files) == 0):
        warn(0, "No files specified....")
        sys.exit()
    else:
        for path0 in args.files:
            fh0 = codecs.open(path0, "rb", encoding="utf-8")
            theDOM = xml.dom.minidom.parse(fh0)
            fh0.close()

            theDoc = theDOM.renameByTagName('p', 'para')

    warn(0, "Done.")
