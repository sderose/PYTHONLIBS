#!/usr/bin/env python
#
# DomExtensions: A bunch of (hopefully) useful additions to the DOM API.
#
#pylint: disable=W0613, W0212
#
from __future__ import print_function
import sys
import re
import codecs
from enum import Enum
import xml.dom, xml.dom.minidom
from xml.dom.minidom import Node, NamedNodeMap

PY3 = sys.version_info[0] == 3
if PY3:
    from html.entities import codepoint2name, name2codepoint
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): str(s, encoding, errors)
    def cmp(a, b): return  ((a > b) - (a < b))
else:
    from htmlentitydefs import codepoint2name, name2codepoint

__metadata__ = {
    'title'        : "DomExtensions.py",
    'description'  : "A bunch of (hopefully) useful additions to the DOM API.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2010-01-10",
    'modified'     : "2021-01-02",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

An XML-manipulation package that sits on top of a DOM implementation
and provides a lot of higher-level methods, and more Pythonic syntax.

Or you may want to just take __getitem__, which lets you navigate DOM
trees very much like nested Python dicts and lists (see below for
details).

This and the other additions are intended to provide more Pythonic
bindings of DOM functionality, as well as features to let you use
DOM much more similarly to using XPath, XPtr, etc.


==Usage==

You can use ''patchDOM''() to monkey-patch these routines into a class
(default: ''xml.dom.Node''):

    import DomExtensions
    import xml.dom
    DomExtensions.patchDom(toPatch=xml.dom.Node)

or to just enable support for using Python's
subscript brackets: `myNode[...]`, do:

    DomExtensions.enableBrackets(toPatch=xml.dom.Node)

See L<#Using [] notation>, below, for the details. In short, you can say things
like myNode[0], myNode["p":3:5], myNode["@id"], and so on.

In either case, just use the methods as if they had been on Node and its many
subclasses already:

    dd = xml.dom.minidom.Document()

===Main features===

See L[https://doi.org/10.4242/BalisageVol13.DeRose02] for discussion of the
approach used here.

* Use of Python `[]` notation to get child nodes or attributes of a node.
* Methods for searching along the XPath axes, such as ancestors, children,
descendants, siblings, predecessors, etc.
* Generating and interpreting XPointers
* more flexible local restructuring such as wrapping, unwrapping, splitting,
and combining nodes.
* node iterators so you don't have to recurse and filter
* SAX event generator

DomExtensions also provides support for:

* attributes whose values inherit (similar to xml:lang) or accumulate
* quick testing of containment and order relationships
* creation of formatted XML for tags, subtrees, etc., including indentation
* escaping for content, attributes, cdata, pis, and comments
* managing whitespace-only text nodes and Unicode whitespace normalization
* finding left and right extremes of a subtree, lowest common ancestor, etc.
* change or case-fold element type names.

==Using [] notation==

The most obvious (though optional) feature that DomExtensions adds to
Node and its subclasses, is support for using Python's
subscript brackets: `myNode[...]`.

To enable ''just'' this feature, do:

    DomExtensions.enableBrackets(toPatch=xml.dom.Node)

For example, instead of

    myNode.childNodes[3].childNodes[27].childNodes[0]

you can just write:

    myNode[3][27][0]

You can also do normal Python slices such as `myNode[0:5]` or `myNode[0:-1]`,
and even use Python's third argument to skip through the range several
steps at a time, like `myNode[0:5:2]`.

Warning to Xpath users: This package is being Pythonic, so child numbers count
from 0, like the rest of Python (and Javascript), and the second index is
the index of the first child ''past'' what you want (so x[1:2] gets you a sublist
that contains just one item, the second one.

Warning to Python users: This really does include ''all'' the children, not
just elements but also types that can only be leaves: text, comment, pi, and
cdata (text is by far the most common). Keep reading if you
want to count among just child nodes that are elements.

With DomExtensions you also have the option to specify an element type name,
to get all child elements of that type:

    myNode["p"]

and you can test whether there is a child of a given kind with the usual Python
`in` construct:
    if ("p" in myNode)...

Several names have special meanings:

* "*" means any element child, but no text, comment, pi, or cdata nodes.
* "#text", "#comment", "#cdata", and "#pi" mean just children of that node type.
* a name beginning with `@`, such as "@id", gets the attribute

    if ("*" in myNode)...
    if ("#text" in myNode)...

and so on. As usual in Python, this only checks direct children; if a child
happens to have children of its own, `in` doesn't know anything about them.

Remember that in XML, the element type name is not a key, like in a Python `dict`,
but a type name. There can be any number of `'` elements in section, for example.
So a name in brackets leads to a list coming back (when might have only one
or, but might have many)
or use "*" to get all ''element'' children, but exclude comment, text, pi, and
other nodes.

===Fancier cases===

The author recommends that you get used to the simpler cases first.

You can combine integer indexes and range, with element type constraints
(except for attributes -- you can't say ['@id':0:-1]).

If you want the fourth paragraph child element, use:

    myNode['p':3]

This is not quite the same as doing the opposite order! `myNode['p':3]` instead
finds the fourth child (of whatever type), and returns it if it is a `p`.
In other words, the indexes are interpreted in order from left to right. This
will be familiar to XPath users, but there isn't really a comparable case with
Python lists.

If the fourth child is not a `p` element, `IndexError` will be raised, just as for
any other "not found" case. Unfortunately, "in" has no way to test more than
the simplest condition, just as in Python you can't ask `[1:2] in myList`.
It may be more Pythonic to do it the following way, which works fine:

    try:
        myStuff = myNode['p':3]
    except IndexError:
        myStuff = []

The same two cases can be used with a range instead of a singleton index:

    myNode["#text", 3:-1]

gets all text nodes from the fourth one to the last, while

    myNode[0:20:"*"]

gets all elements which are among the first 20 children of `myNode`.

==Choosing nodes along XPath axes==

A second major feature of DomExtensions, is called "Axis Selection".
It provides support for
walking all the XPath 'axes' in a DOM tree, such as
ancestors, children, descendants, siblings, and so on. Each axis is available
via a method called 'select' plus the axis name.

Because it's often useful to consider only element nodes,
or only #TEXT nodes, or only element nodes of a certain element type, or
with a certain attribute or attribute-value pair, optional arguments can be
used to filter in those ways:

The 'select...' methods return node [n] (counting from 0)
of a given type and/or attributes along a given axis.
For example:

    myNode.selectChild(3, elType='li', attrs={'class':'major'})

This will return the fourth child of `myNode` which:

* is of the given element type name ('li'), and
* has the attribute ''class'' with value ''major''.

All the arguments are optional. If none are provided, the first item
along the axis (that is, #0) is returned.

Constraints:

* ''n'' counts from 0 and defaults to 0.
Most axes support negative indexes; but not yet all of them.

* ''elType'' supports "*", "#text", "#comment", "#cdata", and "#pi", just like
the bracket notation described earlier. It defaults to "*".
The `attrs` argument cannot be used except with an element type name or "*".

qnames (names with a namespace) are not yet supported for ''elType''.

* `attrs`, if provided, must be None or a dict of attribute name:value pairs,
which all must match for an element to be selected.
The kind of matching depends on the type of value passed in the dict:

* int or float: match numerically. Attribute values that are not
strings of Latin decimal digits will not match,
but will not raise exceptions either. Hexadecimal and other forms should
be added. [TODO]
* a compiled regex: will be matched against the attribute value.
* a string: matched literally. [TODO support case-ignoring]

The `attribute`, and `namespace`
axes are not yet supported for ''select...''.

This is far less power than XPath provides, but it facilitates many programming tasks,
such as scanning for all elements of a given type (which I find very common).


==Node-selection methods==

===Tree information and navigation methods===

* '''getInheritedAttribute'''(node, name)

Return the value of attribute ''name'', from the first node along the
''ancestor-or-self'' axis of ''node'' that specifies it.
Thus, the attribute's value is inherited down the tree, similar to ''xml:lang''.

* '''getCompoundAttr'''(self, name, sep='#', keepMissing=False)

Return the concatenation of the values of the named attribute,
from all ancestors (and self). Separate them with 'sep'.
This facilitates a notion of compound keys (or hierarchical IDs).

* '''leftBranch'''(node)

Return the leftmost descendant of ''node''.
If ''node'''s first child has no children of its own, then it is
also ''node'''s first descendant; otherwise, it will not be.

* '''rightBranch'''(node)

Return the rightmost (last) descendant of ''node''.

* '''getNChildNodes'''(node)

Return the number of (direct) child nodes. This is preferable to asking
for `len(node.childNodes)`, because some implementations may not keep
all childNodes as a physical array underneath, and would have to collect it,
only to then measure it and discard the collection again (hopefully they'll
cache it, but still....).

* '''getDepth'''(node)

Return how deeply nested ''node'' is (the document element is ''1'').

* '''isWithin'''(''node'', ''type'')

Return 1 if ''node'' is, or is within, an element of the given ''type'',
otherwise return 0.

* '''getContentType(node)'''

Returns whether the node has element children, text children, both ("mixed"),
or nothing ("empty"). This is currently not graceful about other possibilities,
such as an element that contains only PIs, COMMENTs, etc. ("odd").
The values returned are drawn from:

CONTENT_EMPTY does not make any distinction between (for example) <b></b> and <b/>.

**CONTENT_EMPTY = 0
**CONTENT_TEXT = 1
**CONTENT_ELEMENT = 2
**CONTENT_MIXED = 3
**CONTENT_ODD = -1

* '''getFQGI'''(node)

Return the list of element types of ''node'''s
ancestors, from the root down, separated by '/'.
For example, "html/body/div/ul/li/p/b".
'''Note''': An FQGI does ''not'' identify a specific element instance or location
in a document; for that, see ''getXPointer''().

* '''getXPointer'''(node, textOffset=None)

Return the XPointer child sequence that leads to ''node''.
That is, the list of child-numbers for all the ancestors of the node, from
the root down, separated by '/'. For example, "1/1/5/2/1".
This is a fine unique name for the node's location in the document.
If `textOffset` is given, the XPointer will point to that character of the
concatenated text content of `node` (which will typically be down in some
descendant node).

This does not yet handle ranges, but will when I get around to it. In the
meantime, you can fetch XPointers for the two ends and combine them in
the caller.

* '''XPointerCompare'''(x1, x2)

Compare two XPointer child-sequences (see ''getXPointer'')
for relative document order, returning -1, 0, or 1.
This does not require actually looking at a document, so no document or
node is passed.

* '''compareDocumentPosition'''(n1, n2)

Compare two nodes for document order, returning -1, 0, or 1.

* '''XPointerInterpret'''(document, x)

Interpret the XPointer child sequence in the string
''x'', in the context of the given ''document'',
and return the node it identifies (or undef if there is no such node).

* '''getEscapedAttributeList'''(node, sortAttributes=False, quoteChar='"')

Return the entire attribute list for
''node'', as needed to go within a XML start-tag. The attributes will be
quoted using `quoteChar`, and any <, &, or `quoteChar` in them
will be replaced by the appropriate XML predefined charcter reference.
If `sortAttributes` is set, the attributes will appear in alphabetical order;
otherwise, the order is unspecified.

==Large-scale tree operations==

* '''removeWhiteSpaceNodes'''(node)

Delete all white-space-only text nodes that are descendants of ''node''.

* '''normalizeAllSpace'''(node)

Do the equivalent of XSLT normalize-space()
on all text nodes in the subtree headed at ''node''.
'''Note''': This is ''not'' the same as the XML::DOM::normalize() method, which
instead combines adjacent text nodes.

* '''normalize'''(node)

Coalesce adjacent text nodes, and delete empty ones.

* '''insertPrecedingSibling'''(''node, newNode'')

* '''insertFollowingSibling'''(''node, newNode'')

* '''insertParent'''(''node, type'')

* '''mergeWithFollowingSibling'''(''node'')

The following sibling of ''node'' is deleted, but its text content
is appended to ''node''.
This drops any sub-structure of the current and sibling.
New. See also the `diffCorefs` command.

* '''mergeWithPrecedingSibling'''(node)

* '''groupSiblings'''(node1, node2, typeForNewParent)

Group all the nodes from ''node1'' through ''node2'' together, under a
new node of type ''typeForNewParent''. Fails if the specified nodes are
not siblings or are not defined.

* '''promoteChildren'''(node)

Remove ''node'' but keep all its children, which becomes siblings at the same
place where ''node'' was.

* '''splitNode'''(node, childNode, offset)

Breaks ''node'' into 2 new sibling nodes of the same type.
The children preceding and including ''childNode'' end up
under the first resulting sibling node; the rest under the second.
However, if ''childNode'' is a text node and ''offset'' is provided,
then ''childNode'' will also be split, with the characters preceding and
including ''offset'' (counting from 1) becoming a final text node under
the first new sibling node, and the rest becoming an initial text node
under the second.
(not yet supported)

* '''eachNodeCB'''(node, preCallback, postCallback)

Traverse the subtree headed at ''node'',
calling the callbacks before and after traversing each node's subtree.

* '''eachNode'''(node)

Traverse the subtree headed at ''node'',
yielding it and each descendant in document order.

* '''eachTextNode'''(node)

A generator that yields each text node descendant.

* '''eachElement'''(node, etype=None)

A generator that yields each element node descendant. If `etype` is specified,
skip any that don't match.

* '''generateSaxEvents'''(self, handlers=None)

Generate the same SAX events that would be encountered if the node passed
were parsed as a document. ''handlers'' is a dict, with some or all of theDoc
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

* '''addArgsForCollectorOptions'''(parser, prefix="")

Assuming ''parser'' is an instance of ''argparse'', add the layout options
known for ''collectAllXml2'' and its kin, to that parser. If specified, insert
''prefix'' between the '--' and the plain option name (this lets you avoid
conflicts with other program options).

* '''collectAllText'''(node, delimiter)

Concatenate together the content of
all the text nodes in the subtree headed at ''node'',
putting ''delimiter'' (default: space) in between.


* '''collectAllXml2'''(node,
    'breakComments',  # True
    'breakEnds',      # False
    'breakPIs',       # True
    'breakStarts',    # True
    'canonical',      # False
    'delim',          # " "
    'emitter',        # None
    'emptyForm',      # "HTML" or XML or SGML
    'indentString',   # '    '
    'indentText',     # False
    'lineBreak',      # "\n"
    'quoteChar',      # '"'
    'schemaInfo',     # None
    'sortAttributes', # False
    'strip'           # False
)

(newer version of collectAllXml, in testing).

** `breakComments`: Break and indent before comments
** `breakEnds`: Break and indent before end tags
** `breakPIs`: Break and indent before processing instructions
** `breakStarts`: Break and indent before start tags
** `canonical`: Generate ''Canonical XML'' per [https://www.w3.org/TR/xml-c14n].
** `delim`: Insert this string between adjacent text nodes (if any)
** `emitter`: Use this EWmitter instance for output
** `emptyForm`: Whether to generate `HTML`, `XML`, or `SGML` style empty element
** `indentString`: Repeat this string to create indentation
** `indentText`: Break and indent at start of texst nodes
** `lineBreak`: String to use for line-breaks
** `quoteChar`: Char to use for quoting attributes etc.

** `schemaInfo`: (reserved)
** `sortAttributes`: Put attributes of each element in alphabetical order
** `strip`: Whether to strip leading and trailing whitespace from texst nodes.

`emitter' can be an instance of class Emitter (also defined here), which
will get passed the generated result strings in document order. The provided
class has options to write them to a path or file handle, collect them in
a string buffer, or call some other callback for each. By default, the result
is collected in a string and passed back whole.

* '''collectAllXml''' (node, delim=" ", indentString='    ',
    emitter=None, schemaInfo=None)

Generate the XML representation for the subtree headed at ''node''.
It knows about elements, attributes, pis, comments, and appropriate escaping.
However, it won't do anything for CDATA sections (other than escape as
needed), XML Declaration, DOCTYPE, or any DTD nodes.

This version only supports a few of the ayout options known to '''collectAllXml2'''().

* '''export'''(element, fileHandle, includeXmlDecl, includeDoctype)

Save the subtree headed at ''element'' to the ''fileHandle''.
If ''includeXmlDecl'' is present and True, start with an XML declaration.
If ''includeDoctype'' is present and True, include a DOCTYPE declaration,
using ''element'''s type as the document-element name, and include any
DTD information that was available in the DOM (unfinished).
See also XML::DOM::Node::toString(),
XML::DOM::Node::printToFile(), XML::DOM::Node::printToFileHandle().

This is effectively shorthand for ''collectAllXml''(), but isn't implemented
that way yuet.

==Index (internal package)==

(not yet implemented)

=over

* '''buildIndex'''(attributeName)

Return a hash table in which each
entry has the value of the specified ''attributeName'' as key, and the element
on which the attribute occurred as value.
This is similar to the XSLT 'key' feature.

* '''find'''(value)

=back


==Character stuff (internal methods)==

=over

* '''escapeXmlAttribute'''(string, quoteChar='"')

Escape the string as needed for it to
fit in an attribute value (amp, lt, and quot).

* '''escapeXml'''(string)

Escape the string as needed for it to
fit in XML text content (amp, lt, and gt when following "]]").

* '''escapeCDATA'''(string)

Escape the string as needed for it to
fit in a CDATA marked section (only gt when following ']]').
XML does not specify a way to escape this. The result produced here is "]]&gt;".

* '''escapeComment'''(string)

Escape the string as needed for it to
fit in a comment ('--').
XML does not specify a way to escape this. The result produced here is "-&#x002d;".

* '''escapePI'''(string)

Escape the string as needed for it to
fit in a processing instruction (just '?>').
XML does not specify a way to escape this. The result produced here is "]]&gt;".

* '''escapeASCII'''(s, width=4, base=16, htmlNames=True))

Escape the string as needed for it to fit in XML text content,
''and'' recodes and non-ASCII characters as XML
entities and/or numeric character references.
`width` is the minimum number of digits to be used for numeric character references.
`base` must be 10 or 16, to choose decimal or hexadecimal references.
If `htmlNames` is True, HTML 4 named entities will be used when applicable,
with numeric character references used otherwise.

* '''unescapeXml'''(string)

Change XML numeric character references, as
well as references to the 5 pre-defined XML named entities and the usual
HTML 4 ones, into the corresponding literal characters.

* '''normalizeSpace'''(self, s, allUnicode=False)

Do the usual XML white-space normalization on the string ''s''.
If ''allUnicode'' is set, include not just the narrow set of `[ \t\r\n]`,
but all Unicode whitespace (which, in Python regexes with re.UNICODE,
does not include ZERO WIDTH SPACE U+200b).

* '''stripSpace'''(self, s, allUnicode=False)

Like `normalizeSpace`, but only remove leading and trailing whitespace.
Internal whitespace is left unchanged.

=back


=Known bugs and limitations=

Negative indexes along axes are supported only for the self, child,
and descendant axes so far.

`Node` is not changed to actually inherit from `list`, so there are surely some
list behaviors that I haven't included (yet). Like sorting. Let me know.

''selectChild''() and its kin should probably permit selecting elements and
attributes via regexes, and support multiple attribute constraints.

''selectChild''() and its kin do not yet support filtering by qnames.


The implementation for []-notation, like that or normal Python lists,
actually checks for `isinstance(arg, int)`, so `myNode["1"]` will not work.


=Related commands=

`testDom.py` -- a package of test cases to exercise DOM and this.

`XmlOutput.pm` -- Makes it easy to produce WF XML output. Provides methods
for escaping data correctly for each relevant context; knows about character
references, namespaces, and the open-element context; has useful methods for
inferring open and close tags to keep things in sync.

`BaseDom.py` -- A very simple DOM implementation in pure Python. Mostly for testing.

`Dominus.py` -- a disk-resident DOM implementation that can handle absurdly
large documents.


=History=

* Written 2010-04-01~23 by Steven J. DeRose (originally in Perl).
* ...
* 2012-01-10 sjd: Start port to Python.
* 2016-01-05: Fix previous/next. Add monkey-patching.
* 2018-02-07: Sync with new AJICSS Javascript API. Add/fix various.
* 2018-04-11: Support unescaping HTML named special character entities.
* 2019-12-13ff: Clean up inline doc. Emitter class. collectAllXml2. lint.
Pull in other extensions implemented in my BaseDom.py (nee RealDOM.py).
Generate SAX.
* 2020-05-22: Add a few items from BS4, and a few new features.
* 2021-01-02: Add NodeTypes class, improve XPointer support.
* 2021-03-17: Add getContentType().


=To do=

* Possibly support myNode[["P"]] to scan all descendants (by analogy
with XPath "//" operator).
* Add insertPrecedingSibling, insertFollowingSibling, insertParent, insertAfter
* Allow creating nodes with no ownerDocument; they get attached when inserted
* Implement splitNode and warp/surround(see help)
* Option for innerXml/outerXml to guarantee Canonical result.
* Let appendChild, insertBefore, insertAfter, etc. take lists.
* Change eachTextNode, etc. to be real generators.
* Add type-hinting.
* Add access items in NamedNodeMaps via [] notation.

==Lower priority==

* Add a way to turn off all indenting for collectAllXml2 with one option.
* Implement a few useful BS4 bits (see class BS4Features) (and add to help).
* String to tag converter, like for quotes?
* Normalize line-breaks, Unicode whitespace within text nodes
* Consider additions from https://lxml.de/api/index.html:
** strip_attributes,....
* Move in matchesToElements from mediaWiki2HTML.
* Sync with XPLib.js
* Find next node of given qgi? Select by qgi?
* String to entity ref, like for quotes, dashes, odd spaces, etc.
* Un-namespace methods: merge ns1/ns2; change prefix/url; drop all;....
* Allow choice of how to 'escape' PIs and comments.
* More optional parameters for Document.create___ (like attrs on element).
* More flexibility on createAttribute etc.


=Rights=

Copyright 2020, Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].

The methods here are based on
[https://www.w3.org/TR/1999/REC-xpath-19991116/] and on my paper:
"JSOX: A Justly Simple Objectization for XML,
or: How to do better with Python and XML."
Balisage Series on Markup Technologies, vol. 13 (2014).
[https://doi.org/10.4242/BalisageVol13.DeRose02].


=Options=
"""


###############################################################################
#
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

def isXmlName(s):
    if (re.match(xmlName, s, re.UNICODE)): return True
    return False

ARG_INT       = 1
ARG_ATTRIBUTE = 2
ARG_STAR      = 3
ARG_RESERVED  = 4
ARG_NAME      = 5

try:
    from BaseDom import BaseDom
    BaseDom.usePythonExceptions()
except ImportError as e:
    sys.stderr.write("Could not import BaseDom for Exceptions.\n")

class NOT_SUPPORTED_ERR(Exception):
    pass
class INDEX_SIZE_ERR(Exception):
    pass
class HIERARCHY_REQUEST_ERR(Exception):
    pass

_regexType = type(re.compile(r'a*'))


def DEgetitem(self:Node, n1, n2=None, n3=None):
    """
    Access nodes via Python list notation, based on my paper:
      DeRose, Steven J. JSOX: A Justly Simple Objectization for XML:
      Or: How to do better with Python and XML.
      Balisage Series on Markup Technologies, vol. 13 (2014).
      https://doi.org/10.4242/BalisageVol13.DeRose02.

    TODO: Test support for negatives -- anything missing?
    TODO: Test cases like [1:] and [:5]

    TODO: Perhaps allow name ".." for ancestor axis?
    TODO: Perhaps extend [] to support jQuery-style CSS selectors?
    TODO: Perhaps allow regexes for name?
    TODO: Perhaps move attrs to setAttr space, access w/ . notation....

    For example:
        myElement['p']       get the 1st 'p' child as a scalar
            *** This could just as well have returned ALL 'p' children ***
        myElement['p':2]     get the 3rd 'p' child
        myElement[2:'p']     get 3rd child if it's a 'p'
        myElement['p':2:8]   get the 3rd through 7th 'p' children
        myElement[2:8]       get the 3rd through 7th children
        myElement[2:8:'p']   of the 3rd through 7th children, get the 'p's
        myElement['@class']  get the 'class' attribute's value (no indexes!)
        myElement[1:10:2]    get every other childNode from 1:10.
    """
    typ1 = argType(n1)
    typ2 = argType(n2)
    typ3 = argType(n3)
    if (n3 is not None): nargs = 3
    elif (n2 is not None): nargs = 2
    else: nargs = 1

    if (typ2==ARG_ATTRIBUTE or typ3==ARG_ATTRIBUTE or
        (typ1==ARG_ATTRIBUTE and nargs>1)):
        raise IndexError("No other indexes allowed with @xxx.")

    if (nargs==1):
        if (typ1 == ARG_INT):                              # [0]
            return self.childNodes[n1]
        if (typ1 == ARG_ATTRIBUTE):                        # ['@id']
            return self.attributes.getNamedItem(n1[1:])
        return self._getChildNodesByName_(n1)              # ['p'] ['#text'] ['*']

    elif (nargs==2):
        if (typ1 == ARG_INT):
            if (typ2 == ARG_INT):                          # [0:2]
                return self.childNodes[n1:n2]
            return self._getChildNodesByName_(n2)[n1]      # [0:'p']
        else:
            if (typ2 == ARG_INT):                          # ['x':0]
                return self._getChildNodesByName_(n1)[n2]
            else:                                          # ['x':'x']
                raise IndexError("More than one non-int index.")

    else:  # nargs==3
        if (typ1 == ARG_INT and typ2 == ARG_INT):
            if (typ3 == ARG_INT):                          # [0:5:2]
                return self.childNodes[n1:n2:n3]
            else:                                          # [0:5:'p']
                nodeList = self.childNodes[n1:n2]
                return self._getListItemsByName_(nodeList, n3)
        elif (typ2 == ARG_INT and typ3 == ARG_INT):        # ['x':0:1]
            return self._getChildNodesByName_(n1)[n2:n3]
        else:
            raise IndexError(
                "No 2 adjacent ints in [%s:%s:%s] for a Node." % (n1, n2, n3))

def DEcontains(self:Node, elType:str) -> bool:
    """Test whether the node has a direct child of the given element type.
    """
    if (elType[0] == '@'):
        return self.hasAttribute(elType)
    for ch in self.childNodes:
        if (ch.nodeType == Node.ELEMENT_NODE and
            (elType == '*' or elType == ch.nodeName)): return True
        if (elType[0] == '#' and elType == self.nodeName): return True
        return False

def nameOfNodeType(self:Node):
    nt = self.nodeType
    return NodeTypes[nt]

def _getChildNodesByName_(self:Node, name:str):
    """
    Return a list of this node's children of a given element name
    '*' gets all element children, but no pi, comment, text....
    """
    return self._getListItemsByName_(self.childNodes, name)

def _getListItemsByName_(self:Node, theList, s):
    """This accepts element type names, #text etc., and "*".
    No attributes or ints here.
    """
    typ = argType(s)
    if (typ not in [ ARG_RESERVED, ARG_STAR, ARG_NAME ]):
        raise IndexError(
            "Node index '%s' is not reserved, '*', or element type." % (s))
    inodes = []
    for item in theList:
        if (item.nodeType==Node.ELEMENT_NODE and (s=='*' or item._nodeName==s)):
            inodes.append(item)
    return inodes

def argType(s):
    """Categorize one of the arguments to __getitem__().
    TODO: Switch these to int names instead of strings.
    """
    if (isinstance(s, int)): return ARG_INT

    # Next 3 can all be handled by _getListItemsByName_()
    if (s in [ "#text", "#comment", "#pi", "#cdata" ]): return ARG_RESERVED
    if (isXmlName(s)): return ARG_NAME
    if (s == "*"): return ARG_STAR

    if (s[0] == "@" and isXmlName(s[1:])): return ARG_ATTRIBUTE
    #if (s == ".."): return ARG_ANCESTOR
    if (s is None): return None
    raise IndexError("Bad argument type for '%s'." % (s))


###############################################################################
# Methods to make minidom (or whatever) look like JS DOM.
#
def nnmIteritems(self:NamedNodeMap):
    """
    """
    for k in self.keys:
        yield (k, self[k])

def outerHTML(self:Node, indent:str="    "):
    """
    """
    from io import StringIO
    buf = StringIO()
    if (indent==""): self.toxml(buf)
    else: self.toprettyxml(buf, indent="    ")
    return buf.getvalue()
    #t = self.getStartTag() + self.innerHTML() + self.getEndTag()
    #return t

def innerHTML(self:Node, cOptions=None):
    """Could also use outerHTML and then strip the ends.
    """
    t = ""
    for curNode in self.childNodes:
        ty = curNode.nodeType
        if (ty == Node.TEXT_NODE):
            t += curNode.nodeValue
            break
        elif (ty == Node.ELEMENT_NODE):
            t += curNode.getStartTag() +  curNode.innerHTML() + curNode.getEndTag()
            break
        elif (ty == Node.CDATA_SECTION_NODE):
            t += "<![CDATA[%s]]>" % (escapeCDATA(curNode.textContent))
            break
        elif (ty == Node.ENTITY_REFERENCE_NODE):
            break
        elif (ty == Node.ENTITY_NODE):
            break
        elif (ty == Node.PROCESSING_INSTRUCTION_NODE):
            t += "<?%s?>" % (curNode.textContent)
            break
        elif (ty == Node.COMMENT_NODE):
            t += "<!--%s-->" % (curNode.textContent)
            break
        elif (ty == Node.DOCUMENT_NODE or ty == Node.DOCUMENT_FRAGMENT_NODE):
            t += curNode.getStartTag()
            for ch in (curNode.childNodes):
                t += ch.innerHTML
            t += curNode.getEndTag()
            break
        elif (ty == Node.DOCUMENT_TYPE_NODE):
            t += "<!DOCTYPE %s>" % (curNode.textContent)
            break
        elif (ty == Node.NOTATION_NODE):
            break
        #elif (ty == Node.ATTRIBUTE_NODE):
        #    (done by Node.ELEMENT_NODE)
        else:
            sys.exit("Unknown node type %d." % (ty))
    return t

def outerXML(self:Node, cOptions=None) -> str:
    return self.outerHTML(cOptions=cOptions)
def innerXML(self:Node, cOptions=None) -> str:
    return self.innerHTML(cOptions=cOptions)

def innerText(self:Node, sep:str='') -> str:
    """
    Like usual innertext, but a function (instead of a property), and allows
    inserting something in between all the text nodes (typically a space,
    so text of list items etc. don't join up. But putting in spaces around
    HTML inlines like i and b, is occasionally wrong.
    """
    if (self.nodeType == Node.TEXT_NODE or
        self.nodeType == Node.TEXT_NODE):
        sys.stderr.write(self.nodeValue+"\n")
        return self.nodeValue
    if (self.nodeType != Node.ELEMENT_NODE):  # PI, comment
        return ""
    t = ""
    for childNode in self.childNodes:
        if (childNode.nodeType == Node.ELEMENT_NODE):
            if (t): t += sep
            t += childNode.innerText(sep=sep)
    return t


###############################################################################
# Methods to add to NamedNodeMap to make it more usable.
# xml.dom.minidom claims to have this, but I have had problems with it.
# http://epydoc.sourceforge.net/stdlib/xml.dom.minidom.NamedNodeMap-class.html
#
def NNM_getitem(self:NamedNodeMap, which):
    try:
        x = int(which)
        return self.item(x)
    except ValueError:
        return self.getNamedItem(which).vValue


###############################################################################
# Extended "Axis selects".
#
# Methods for finding the nth node along a given axis, that has a given
# element type and/or attribute/value.
#
# TODO: Support negative to go from end.
#
def selectSelf(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    if (self.nodeMatches(elType, attrs)):
        if (n==0 or n==-1): return self
    return None

def selectAncestor(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """Return the first/nth ancestor that fits the requirements.
    TODO: Support negative n.
    """
    if (n>=0):
        cur = self.parentNode
        return cur.selectAncestorOrSelf(
            n=n, elType=elType, attrs=attrs)
    else:
        raise NOT_SUPPORTED_ERR("selectPreceding() doesn't support negative indexes yet.")

def selectAncestorOrSelf(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """Like selectAncestor(), but the node itself is also considered.
    n=-01 means the outermost one (if no
    other constraints are given, the document element).
    """
    if (n>=0):
        found = 0
        cur = self
        while (cur):
            if (cur.nodeMatches(elType, attrs)):
                found += 1
                if (found >= n): return cur
            cur= cur.parentNode
        return None
    else:
        raise NOT_SUPPORTED_ERR("selectPreceding() doesn't support negative indexes yet.")

def selectChild(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """n=-01 means the last one.
    """
    found = 0
    if (n >= 0):
        cur = self.getFirstChild()
        while (cur):
            if (self.nodeMatches(elType, attrs)):
                found += 1
                if (found >= n): return cur
            cur = cur.nextSibling()
    else:
        cur = self.getLastChild()
        while (cur):
            if (self.nodeMatches(elType, attrs)):
                found += 1
                if (found >= -n): return cur
            cur = cur.precedingSibling()

    return None

def selectDescendantOrSelf(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """TODO: Support negative n.
    """
    if (self.nodeMatches(elType, attrs)):
        if (n==0): return self
        n -= 1
    return selectDescendantR(n, elType, attrs)

def selectDescendant(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """
    """
    return selectDescendantR(n, elType, attrs)

def selectDescendantR(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """
    """
    found = 0
    if (n >= 0):
        if (self.nodeMatches(elType, attrs)):
            found += 1
            if (found >= n): return self
        for ch in self.childNodes:
            node = self.getDescendantByAttributeR(ch, n, elType, attrs)
            if (node):
                found += 1
                if (found >= n): return ch
        return None
    else:
        cur = self.rightBranch
        while (cur != self):
            if (cur.nodeMatches(elType, attrs)): found += 1
            if (found >= -n): return cur
            cur = cur.getPreceding()
        return None

def selectPreceding(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """
    TODO: Support -n
    """
    if (n >= 0):
        cur = getPreceding(self)
        found = 0
        while (cur):
            if (isWithin(self, cur)): continue  # No ancestors, please.
            if (cur.nodeMatches(elType, attrs)):
                found += 1
                if (found >= n): return cur
            cur=getPreceding(cur)
        return None
    else:
        raise NOT_SUPPORTED_ERR("selectPreceding() doesn't support negative indexes yet.")

def getPreceding(self:Node) -> Node:
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

def getPrecedingAbsolute(self:Node) -> Node:
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

def selectFollowing(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """As in XPath, does not include descendants.
    See https://stackoverflow.com/questions/44377798/
    TODO: Support -n
    """
    if (n >= 0):
        cur = self.getFollowing()
        found = 0
        while (cur):
            if (cur.nodeMatches(elType, attrs)):
                found += 1
                if (found >= n): return cur
            cur = self.getFollowing()
        return None
    else:
        raise NOT_SUPPORTED_ERR("selectFollowing() doesn't support negative indexes yet.")

def getFollowing(self:Node) -> Node:
    """As in XPath, does not include descendants.
    See https://stackoverflow.com/questions/44377798/
    """
    cur = self
    while (cur):
        ns = cur.nextSibling()
        if (ns): return ns
        cur = cur.parentNode
    return None

def getFollowingAbsolute(self:Node) -> Node:
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

def selectPrecedingSibling(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """
    TODO: Support -n
    """
    if (n >= 0):
        cur = self.getPreviousSibling()
        found = 0
        while (cur):
            if (cur.nodeMatches(elType, attrs)):
                found += 1
                if (found >= n): return cur
            cur = cur.getPreviousSibling()
        return None
    else:
        raise NOT_SUPPORTED_ERR("selectPrecedingSibling() doesn't support negative indexes yet.")

def selectFollowingSibling(self:Node, n:int=0, elType:str="", attrs=None) -> Node:
    """
    TODO: Support -n
    """
    if (n >= 0):
        cur = self.getFollowingSibling()
        found = 0
        while (cur):
            if (cur.nodeMatches(elType, attrs)):
                found += 1
                if (found >= n): return cur
            cur = cur.getFollowingSibling()
        return None
    else:
        raise NOT_SUPPORTED_ERR("selectFollowingSibling() doesn't support negative indexes yet.")


### Useful synonyms
#
def getPrecedingSibling(self:Node) -> Node:
    return self.previousSibling
def precedingSibling(self:Node) -> Node:
    return self.previousSibling
def selectPreviousSibling(self:Node, **w) -> Node:
    self.selectPrecedingSibling(*w)

def getFollowingSibling(self:Node) -> Node:
    return self.nextSibling
def followingSibling(self:Node) -> Node:
    return self.nextSibling
def selectNextSibling(self:Node, **w) -> Node:
    self.selectFollowingSibling(*w)

# No select for root, self, attribute, or namespace axes.


###############################################################################
#
def getLeastCommonAncestor(self:Node, other:Node) -> Node:
    """Return the smallest node that is an ancestor of both nodes.
    """
    other = other.parentNode
    while (other):
        if (self.isDescendantOf(other)): return other
        other = other.parentNode
    return None

def getLeftBranch(self:Node) -> Node:
    """
    Find the furthest node down if you always go left.
    """
    cur = self
    while (cur.firstChild): cur = cur.firstChild
    return cur

def getRightBranch(self:Node) -> Node:
    """
    Find the furthest node down if you always go right.
    """
    cur = self
    while (cur.lastChild): cur = cur.lastChild
    return cur

def getFirstChild(self:Node, nodeType=None) -> Node:
    return self.selectChild(self, n=0, elType=nodeType)

def getLastChild(self:Node, nodeType=None) -> Node:
    return self.selectChild(self, n=-1, elType=nodeType)

def getNChildNodes(self:Node, nodeType=None) -> int:
    """Return the number of children of the current node.
    TODO: Node implementations that don't use physical arrays
    may want to override this for speed.
    """
    if (not nodeType): return len(self.childNodes)
    n = 0
    for ch in self.childNodes:
        if (ch.nodeType == Node.ELEMENT_NODE and
            (nodeType=='*' or nodeType==ch.nodeName)): n += 1
    return n

def getChildNumber(self:Node, nodeType=None) -> int:
    """Return the number of this node among its siblings.
    @param nodeType: If specified, only count siblings that are elements of
    the specified type ('*' for all).
    """
    n = 0
    for ch in self.parentNode.childNodes:
        if (nodeType is None or
            (ch.nodeType == Node.ELEMENT_NODE and
             (nodeType=='*' or nodeType==ch.nodeName))): n += 1
        if (ch==self): return n
    return None

def getDepth(self:Node) -> int:
    """
    How far down are we? Document element is 1.
    """
    d = 0
    cur = self
    while (cur):
        d = d + 1
        cur = cur.parentNode
    return d

def getMyIndex(self:Node, onlyElements=True) -> int:
    """Return the position in order, among the node's siblings.
    The first child is [0]!
    """
    if (self.nodeType not in [ Node.ELEMENT_NODE, Node.TEXT_NODE, Node.COMMENT_NODE,
        Node.CDATA_SECTION_NODE, Node.PROCESSING_INSTRUCTION_NODE ]):
        raise INDEX_SIZE_ERR("Cannot do getMyIndex() on a %s." %
            (Node.nameOfNodeType(self.nodeType)))
    par = self.parentNode
    if (not par): raise HIERARCHY_REQUEST_ERR("No parent.")
    if (par.nodeType == Node.DOCUMENT_NODE): return 0
    n = 0
    for sib in par.childNodes:
        if sib.isSameNode(self): return n
        if (onlyElements==False or sib.nodeType==Node.ELEMENT_NODE): n += 1
    raise(ValueError)

def getFQGI(self:Node, sep="/") -> str:
    """Return the sequence of element type names of all ancestors, in
    document order, separated by `sep`.
    """
    cur = self
    f = ""
    if (cur.nodeType != Node.ELEMENT_NODE):
        f = cur.nodeName
        cur = cur.parentNode
    while (cur):
        f = self.nodeName + "/" + f
        cur = cur.parentNode
    return f

def isWithinType(self:Node, elType) -> bool:
    """
    Test whether a node has an ancestor of a specified element type.
    """
    cur = self
    while (cur):
        if (cur.nodeName == elType): return True
        cur = cur.parentNode
    return False

def isDescendantOf(self:Node, node:Node) -> bool:
    return isWithin(self, node)

def isWithin(self:Node, node:Node) -> bool:
    """
    Test whether some specific node is an ancestor of the given node.
    """
    cur = self.parentNode
    while (cur):
        if (cur == node): return True
        cur = cur.parentNode
    return False

# TODO: Switch to Enum?
#
CONTENT_EMPTY = 0
CONTENT_TEXT = 1
CONTENT_ELEMENT = 2
CONTENT_MIXED = 3
CONTENT_ODD = -1

def getContentType(self) -> int:
    """Test whether this elements has text and/or element children.
    If there are PI, COMMENT, and/or CDATA children, returns CONTENT_ODD
    (TODO: perhaps CDATA should count as just text?).
    """
    if (len(self.childNodes) == 0): return self.CONTENT_EMPTY
    eChild = self.selectChild(n=0, elType='*')
    tChild = self.selectChild(n=0, elType='#TEXT')
    if (eChild):
        if tChild: return self.CONTENT_MIXED
        else: return self.CONTENT_ELEMENT
    if (tChild): return self.CONTENT_TEXT
    return self.CONTENT_ODD


###############################################################################
# XPointer support
#
def getXPointer(self:Node, textOffset=None) -> str:
    """Get a simple numeric XPointer to the node, as a string.
    With `textOffset`, dig down and find the specified character (not byte!)
    among the descendants, and return a precise pointer there. If the
    offset is beyond the amount of text under `self`, just return an
    XPointer to `self` as if no `textOffset` was given. If it's exactly
    1 greater, return an xpointer that identifies the location just within
    the node, after the last content character.

    TODO: Extend to do full-fledged ranges.
    """
    if (textOffset is None):
        return getXPointerToNode(self)
    assert textOffset >= 0
    if (self.nodeType == Node.TEXT_NODE):  # Find the right text node first.
        xp = getXPointerToNode(self)
        if (textOffset>=0 and textOffset<=len()): xp += "#%d" % (textOffset)
        return xp
    theTextNode, localOffset = findTextByOffset(self, textOffset=textOffset)
    xp = getXPointerToNode(theTextNode) + "#%d" % (localOffset)
    return xp

def findTextByOffset(self:Node, textOffset=0):
    """Given a text offset within the *entire* text under the given node,
    find which particular TEXT_NODE descendant contains it, and how far
    into that TEXT_NODE it is.
    """
    textSeen = 0
    tnode = None
    lastLen = 0
    for tnode in self.getTextNodesIn(self):
        lastLen = len(tnode.data)
        if (textSeen + lastLen > textOffset):
            return tnode, textOffset - textSeen
        textSeen += lastLen
    return tnode, lastLen

def getXPointerToNode(self:Node, idAttrName="id"):
    """Get a simple XPointer to the node, as a string.
    If `idAttrName` is given, the XPointer will use that as an ID, and
    use child sequence numbers from there down. This is much more robust.
    """
    f = ""
    cur = self
    while (cur):
        f = "/%s%s" % (cur.getMyIndex()+1, f)
        cur = cur.parentNode
    return f

def XPointerCompare(self:Node, xp1, xp2):
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

def compareDocumentPosition(self:Node, other:Node):
    """Compare two nodes for order.
    """
    return self.XPointerCompare(self.getXPointer(), other.getXPointer())

def XPointerInterpret(self:Node,  xp):
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
def nodeMatches(self:Node, elType="*", attrs=None):
    """Check if a node matches the supported selection constraints.
    Used by all the selectAXIS() methods.

    @param elType can be any of the following:
        A literal node name for an element
        '*' (the default) for any element
        '#' plus a DOM nodeType name (can omit '_NODE', or abbreviate)
        A compiled regex

        Possible additions:
            An integer DOM nodeType number
            '#WSOTN' for non-white-space-only text nodes,
            '#NWSOTN' for anything that's not a WSOTN
            '#ET' for elements and non-white-space-only text nodes

    @param attrs: a dict of attribute name:value pairs, all of which must match.
    If the value for any attribute in the dict is truly None, then that
    attribute must *not* be on the element at all ('' does not match None!).
    If the value is passed as a compiled regex, it will be matched against.

    @TODO: Support nodeTypes in sync w/ Javascript packages.
    @TODO: Perhaps allow regexes, numeric comparison for numeric values, etc.
    @TODO: Perhaps allow matching against any token(s) of an attribute?
    """
    if (elType):                                     # check type constraint:
        if (elType == "*"):
            if (self.nodeType!=Node.ELEMENT_NODE): return False
        elif (":" in elType):
            raise NOT_SUPPORTED_ERR("Namespaces not yet allowed for select...().")
        else:
            # Would prefer to test _sre.SRE_Pattern, but that doesn't work.
            if (type(elType) == _regexType):
                if (not re.match(elType, self.nodeName)): return False
            else:
                if (self.nodeName != elType): return False

    if (not attrs): return True
    if (self.nodeType == Node.TEXT_NODE): return False

    for tgtName, tgtVal in attrs.items:
        if (":" in tgtName):
            raise NOT_SUPPORTED_ERR("Namespaces not yet allowed for select...().")
        if (not self.hasAttribute(tgtName)):
            if (tgtVal is not None): return False
        else:
            ty = type(tgtVal)
            attrVal = self.getAttribute(tgtName)
            if (ty == _regexType):
                if (not re.match(tgtVal, attrVal)): return False
            elif (ty == int):
                try:
                    if (int(attrVal) != tgtVal): return False
                except ValueError:
                    return False
            elif (ty == float):
                try:
                    if (float(attrVal) != tgtVal): return False
                except ValueError:
                    return False
            else:
                if (attrVal != tgtVal): return False
    return True


def getInheritedAttribute(self:Node, aname):
    """Search upward to find an assignment to an attribute, and return the
    nearest non-empty one (or None if none is found).
    This is similar to the defined semantics of xml:lang.
    """
    cur = self
    while (cur):
        avalue = cur.getAttribute(aname)
        if (avalue is not None and avalue!=''): return avalue
        cur = cur.parentNode
    return None

def getEscapedAttribute(self:Node, aname, quoteChar='"'):
    """
    """
    avalue = self.getAttribute(aname)
    return escapeXmlAttribute(avalue, quoteChar='"')

def getCompoundAttr(self:Node, name, sep='#', keepMissing=False):  ### Not DOM
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

def getStartTag(self:Node, sortAttributes=False):
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

def getEndTag(self:Node, appendAttr='id'):
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

def getEscapedAttributeList(self:Node, sortAttributes=False, quoteChar='"'):
    """
    Assemble the entire attribute list, escaped as needed to write out as XML.
    """
    buf = ""
    if (not (self)): return None
    alist = self.attributes
    if (not (alist)): return buf
    anames = alist.keys()
    if (sortAttributes): anames = sorted(anames)
    for aname in anames:
        avalue = self.getEscapedAttribute(aname, quoteChar=quoteChar)
        if (quoteChar == "'"): buf += "%s='%s'" % (aname, avalue)
        else: buf += '%s="%s"' % (aname, avalue)
    return buf

def addAttributeToken(self:Node, attrName, token, duplicates=False):
    """TODO Pull in code from JavaScript...
    """
    raise NOT_SUPPORTED_ERR("No addAttributeToken")

def removeAttributeToken(self:Node, attrName, token):
    """
    """
    raise NOT_SUPPORTED_ERR("No removeAttributeToken")


def removeWhiteSpaceNodes(self:Node):
    """Drop all text nodes that contain only whitespace characters.
    """
    # print "running removeWhiteSpaceNodesCB\n"
    eachNodeCB(self, callbackA=removeWhiteSpaceNodesCB, callbackB=None)

def removeWhiteSpaceNodesCB(self:Node):
    """This only deals with XML whitespace, not all Unicode.
    """
    if (self.nodeType != Node.TEXT_NODE): return
    t = self.data
    mat = re.search(xmlSpaceOnlyRegex, t, "")
    if (mat): self.parentNode.removeChild(self)

def removeNodesByTagName(self:Node, nodeName):
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
    for t in getAllDescendants(root, [ Node.TEXT_NODE ]):
        if (t.nodeType == Node.ELEMENT_NODE):
            if (upper): t.nodeName = t.nodeName.toupper()
            else: t.nodeName = t.nodeName.tolower()
            if (attributesToo):
                for a, v in t.attributes.items():
                    if (a.isupper()): continue
                    t.removeAttribute(a)
                    t.setAttribute(a.toupper(), v)
    return

def getAllDescendants(root, excludeTypes=None, includeTypes=None):
    """
    Get a list of all descendants of the given node, in document order.
    @param excludeTypes: A list of nodeTypes to exclude (such as TEXT_NODE).
        Descendants of skipped nodes will still be traversed.
    @param excludeTypes: A list of nodeTypes to include. If not specified,
        all (non-excluded) types are ok.
    """
    if ((not excludeTypes) or root.nodeType not in excludeTypes):
        if (not includeTypes or root.nodeType in includeTypes):
            yield(root)
    for ch in root.childNodes:
        yield getAllDescendants(ch)
    return


###############################################################################
#
def normalizeAllSpace(self:Node):
    """
    """
    eachNodeCB(self, callbackA=normalizeAllSpaceCB, callbackB=None)

def normalizeAllSpaceCB(self:Node):
    """
    """
    if (self.nodeType != Node.TEXT_NODE): return
    self.setData(self.normalizeSpace(self.data))

def normalize(self:Node):
    """Discard empty text nodes; coalesce adjacent ones.
    """
    for ch in self.childNodes:
        if (ch.nodeType == Node.ELEMENT_NODE):
            ch.normalize()
        elif (ch.nodeType == Node.TEXT_NODE):
            nxt = ch.followingSibling
            if (nxt and nxt.nodeType==Node.TEXT_NODE):
                ch.data += nxt.data
                self.removeChild(nxt)

def addElementSpaces(self:Node, exceptions=None):
    """Add spaces around all elements *except* those in list 'exceptions'.
    This is useful because most elements entail word-boundaries (say, things
    CSS would consider display:block). But little elements may not: such as
    HTML b, i, etc., and TEI var, sic, corr, etc.
    """
    raise NOT_SUPPORTED_ERR("No addElementSpaces")


###############################################################################
#
def insertPrecedingSibling(self:Node, node):
    """
    """
    self.parentNode.insertBefore(node, self)
    return node

def insertFollowingSibling(self:Node, node):
    """
    """
    par = self.parentNode
    r = self.getFollowingSibling()
    if (r): par.insertBefore(node, r)
    else: par.appendChild(node)
    return node

def insertParent(self:Node, elType):
    """
    TODO Allow a sequence of siblings
    """
    new = self.getOwnerDocument.createElement(elType)
    self.parentNode.replaceChild(new, self)
    new.appendChild(self)
    return new


###############################################################################
#
def mergeWithFollowingSibling(self:Node, cur):
    """
    Following sibling goes away, but its children are appended to the node.
    """
    if (not (cur)): return None
    sib = cur.getFollowingSibling()
    if (not sib): return False
    while (cur.hasChildNodes()):
        cur.appendChild(sib.getFirstChild())
    cur.parentNode.removeChild(sib)

def mergeWithPrecedingSibling(self:Node, cur):
    """
    Preceding sibling goes away, but its children are appended to the node.
    """
    if (not (cur)): return None
    sib = cur.getPrecedingSibling()
    if (not sib): return False
    while (cur.hasChildNodes()):
        cur.insertBefore(sib.getLastChild(), cur.getFirstChild())
    cur.parentNode.removeChild(sib)


###############################################################################
# Take a block of contiguous siblings and enclose them in a new intermediate
# parent node (which in inserted at the level they *used* to be at).
#
def groupSiblings(self:Node, first, breakNode, newParentType):
    """
    """
    if (not first or not breakNode):
        raise ValueError("Must supply first and breakNode to groupSiblings\n")
    oldParent = first.parentNode
    oldParent2 = breakNode.parentNode
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
#
def promoteChildren(self:Node):
    """Remove the given node itself, but promoting all its children.
    Sometimes known as "unwrapping".
    """
    parent = self.parentNode
    cur = self.getFirstChild()
    while (cur):
        cont = cur.getFollowingSibling()
        moving = self.removeChild(cur)
        parent.insertBefore(moving, parent)
        cur = cont
    parent.removeChild(self)

def moveChildToAttribute(root:Node, pname:str, chname:str, aname:str, onDup="skip"):
    """Within the subtree under `root`, check all elements named `ename` that
    have a child of type `chname`, and move the content of that child onto
    attribute `aname` of the parent. The child element is deleted.

    Cases of interest:
        * What if the parent already has an `aname` attribute?
        * What if there's more than child of that type?
        * What if the child has attributes of its own?
        * What if the child has subelements of its own?

    You can check that all cases in a given subtree lack these cases, by
    calling `findNonAttributable`.
    """
    nDone = 0
    for node in root.eachNode(pname):
        if (node.hasAttribute(aname)): continue
        chNodes = node.getChildNodes(chname)
        if (len(chNodes) != 1): continue
        ch = chNodes[0]
        attrs = ch.getsAttribute()
        if (attrs and len(attrs)>0): continue
        if (ch.getElements("*")): continue
        node.setAttribute(aname, ch.innerText())
        node.removeChild(ch)
        nDone += 1
    return nDone

def findNonAttributable(root:Node, pname:str, chname:str, aname:str):
    """Basically a dry run for `moveChildToAttribute`.
    @return The first node that can't have a child move up onto an attribute.
    """
    for node in root.eachNode(pname):
        if (node.hasAttribute(aname)): return node
        chNodes = node.getChildNodes(chname)
        if (len(chNodes) != 1): return node
        ch = chNodes[0]
        attrs = ch.getsAttribute()
        if (attrs and len(attrs)>0): return node
        if (ch.getElements("*")): return node
        nDone += 1
    return None


###############################################################################
#
def eachNodeCB(self:Node, callbackA=None, callbackB=None, depth=1):
    """Traverse a subtree given its root, and call separate callbacks before
    and after traversing each subtree. Callbacks might, for example,
    respectively generate the start- and end-tags for elements, and generate
    the text or data for other kinds of nodes.
    Attribute and namespace nodes are not visited.
    Callbacks are allowed to be None if not needed.

    If a callback returns True, we stop traversing.
    """
    if (not (self)): return 1
    #name = self.nodeName
    if (callbackA):
        if (callbackA(self)): return 1
    if (self.hasChildNodes()):
        #print ("Recursing for child nodes at level %s." % (depth+1))
        for ch in self.childNodes:
            rc = eachNodeCB(ch, callbackA=callbackA,
                callbackB=callbackB, depth=depth+1)
            if (rc): return 1
    if (callbackB):
        if (callbackB(self)): return 1
    return 0 # succeed

# TODO: rename to lose the "for" (&c)
def eachNode(self:Node, wsn=True, depth=1):
    """Generate all descendant nodes.
    @param wsn: If False, skip white-space-only nodes.
    """
    if (not (self)): return
    if (self.nodeType != Node.TEXT_NODE
        or wsn or self.nodeValue.strip() != ''):
        yield self
    if (self.hasChildNodes()):
        for ch in self.childNodes:
            for chEvent in eachTextNode(ch, depth+1):
                yield chEvent
    return

def reversedEachNode(self:Node, wsn=True, depth=1):
    """Generate all descendant nodes in reverse order
    @param wsn: If False, skip white-space-only nodes.
    """
    if (not (self)): return
    if (self.hasChildNodes()):
        for ch in reversed(self.childNodes):
            for chEvent in eachTextNode(ch, depth+1):
                yield chEvent
    if (self.nodeType != Node.TEXT_NODE
        or wsn or self.nodeValue.strip() != ''):
        yield self
    return

def eachTextNode(self:Node, wsn=True, depth=1):
    """Generate all descendant text nodes.
    @param wsn: If False, skip white-space-only nodes.
    """
    if (not (self)): return
    if (self.nodeType == Node.TEXT_NODE):
        if (wsn or self.nodeValue.strip() != ''):
            yield self
    if (self.hasChildNodes()):
        for ch in self.childNodes:
            for chEvent in eachTextNode(ch, depth+1):
                yield chEvent
    return

def eachElement(self:Node, etype=None, depth=1):
    """Generate all element node descendants, optionally limiting to one type.
    """
    if (not (self)): return
    if (self.nodeType==Node.ELEMENT_NODE):
        if (not etype or self.nodeName == etype): yield self
    if (self.hasChildNodes()):
        #print ("Recursing for child nodes at level %s." % (depth+1))
        for ch in self.childNodes:
            for chEvent in eachElement(ch, etype=None, depth=depth+1):
                yield chEvent
    return

def generateNodes(self:Node):
    """Traverse a subtree given its root, and yield the nodes preorder.
    """
    if (not self): return
    yield self
    for ch in self.childNodes:
        yield ch.generateNodes()
    return

def generateSaxEvents(self:Node, handlers=None):
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

def genSax(self:Node, handlers):
    ntype = self.nodeType
    if (ntype == Node.ELEMENT_NODE):                  # 1 ELEMENT
        if (handlers['StartElementHandler']):
            handlers['StartElementHandler'](self.nodeName, self.attributes)
        for ch in self.childNodes:
            genSax(ch, handlers)
        if (handlers['EndElementHandler']):
            handlers['EndElementHandler'](self.nodeName)
    elif (ntype == Node.TEXT_NODE):                   # 3 TEXT
        if (handlers['CharacterDataHandler']):
            handlers['CharacterDataHandler'](self.data)
    elif (ntype == Node.CDATA_SECTION_NODE):          # 4 CDATA
        if (handlers['CharacterDataHandler']):
            handlers['CharacterDataHandler'](self.data)
    elif (ntype == Node.PROCESSING_INSTRUCTION_NODE): # 7 PI
        if (handlers['ProcessingInstructionHandler']):
            handlers['ProcessingInstructionHandler'](self.data)
    elif (ntype == Node.COMMENT_NODE):                # 8 COMMENT
        if (handlers['CommentHandler']):
            handlers['CommentHandler'](self.data)
    elif (ntype == Node.DOCUMENT_NODE):               # 9 DOCUMENT
        if (handlers['CommentHandler']):
            handlers['CommentHandler'](self.data)
    return

###############################################################################
#
def collectAllText(self:Node, delim=" ", depth=1):
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
    if (self.nodeType == Node.TEXT_NODE):
        dat = self.data
        if (dat):
            if (depth>1): textBuf = delim + dat
            else: textBuf = dat
    elif (self.hasChildNodes()):
        for ch in self.childNodes:
            textBuf = textBuf + collectAllText(ch, delim, depth+1)
    return textBuf


def getTextNodesIn(node:Node):
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
def collectAllXml2(self:Node,
    breakComments=True,      # Break/indent before comments
    breakEnds=True,          # Break before end tags
    breakPIs=True,           # Break/indent before processing instructions
    breakStarts=True,        # Break before start tags
    canonical=False,         # Generate Canonical XML
    delim=" ",               # put between text nodes
    emitter=None,            # What Emitter object to use
    emptyForm="HTML",        # Which syntax to use for empty elements
    indentString='    ',     # Repeat this to indent ("" not to)
    indentText=False,        # Break/indent before text nodes
    lineBreak="\n",          # String to use for line-breaks
    quoteChar='"',           # For quoting attrs, etc.

    schemaInfo=None,         # Any schema-specific info (not yet used)
    sortAttributes=False,    # Attrs in alphabetical order
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

    Canonical includes:
        UTF-8
        \n
        attributes normalized
        No CDATA sections or unnecessary entities
        No XML declaration or Doctype
        Empty elements go to start/end
        Normalized whitespace outside the document element and inside tags
        Attributes are alphabetized and double-quoted.
        No redundant namespace declarations
        xml:base is cleaned up
    """
    if (emitter is None): emitter = Emitter("STRING")
    if (emptyForm not in [
        'HTML',      # <br />
        'XML',       # <br/>
        'SGML',      # <br>
        'NONE',      # <br></br>
        ]):
        raise ValueError("Unknown value '%s' for emptyForm option." % (emptyForm))

    if (quoteChar not in [ '"', "'" ]):
        raise ValueError("Bad quoteChar '%s'." % (quoteChar))

    if (canonical):
        breakComments = breakEnds = breakPIs = breakStarts = False
        delim = ""
        emptyForm = "NONE"
        indentString = ""
        indentText = False
        lineBreak = "\n"
        strip = False

    cOptions = CollectorOptionsDef(
        breakComments,
        breakEnds,
        breakPIs,
        breakStarts,
        canonical,
        delim,
        emitter,
        emptyForm,
        indentString,
        indentText,
        lineBreak,
        quoteChar,
        schemaInfo,
        sortAttributes,
        strip
        )
    self.collectAllXml2r(cOptions)
    return emitter.string

from collections import namedtuple
CollectorOptionsNames = [
    'breakComments',  # True
    'breakEnds',      # False
    'breakPIs',       # True
    'breakStarts',    # True
    'canonical',      # False; if True, overrides many other options
    'delim',          # " "
    'emitter',        # None
    'emptyForm',      # HTML, XML, SGML, or NONE
    'indentString',   # '    '
    'indentText',     # False
    'lineBreak',      # "\n"
    'quoteChar',      # '"'
    'schemaInfo',     # None
    'sortAttributes', # False
    'strip',          # False
]
CollectorOptionsDef = namedtuple('CollectorOptions', CollectorOptionsNames)

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
        if (isEnd and cOptions.breakEnds): pre = cOptions.lineBreak

    return pre + (cOptions.indentString * max(0, depth-2)) + post

def addArgsForCollectorOptions(parser, prefix=""):
    for optName in CollectorOptionsNames:
        oname = "--%s%s" % (prefix, optName)
        if (optName in [ 'delim', 'indentString', 'lineBreak', 'emptyForm' ]):
            parser.add_argument(oname, type=str)
        else:
            parser.add_argument(oname, action='store_true')
    return

def collectAllXml2r(self:Node, cOptions, depth=1):
    """The recursive part of collectAllXml2().
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
    if (ntype == Node.ELEMENT_NODE):                  # 1 ELEMENT
        textBuf = "%s<%s%s" % (ind(cOptions, depth, name=name),
            name, getEscapedAttributeList(self,
                sortAttributes=cOptions.sortAttributes,
                quoteChar=cOptions.quoteChar))
        if (isEmpty): textBuf += " />"
        else: textBuf += ">"
        em.emit(textBuf)

        for ch in self.childNodes:
            ch.collectAllXml2r(cOptions, depth+1)

        buf = ""
        if (em.lastCharEmitted() == cOptions.lineBreak[-1]
            or cOptions.breakEnds):
            buf = ind(cOptions, depth, name, isStart=False, isEnd=True)
        em.emit(buf + "</%s>" % (name))

    elif (ntype == Node.ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Unexpected attribute node.")

    elif (ntype == Node.TEXT_NODE):                   # 3 TEXT
        buf = ""
        if (cOptions.indentText): buf = ind(cOptions, depth, "#text")
        if (cOptions.strip): s = self.data.strip()
        else: s = self.data
        em.emit(buf + escapeXml(s))

    elif (ntype == Node.CDATA_SECTION_NODE):          # 4 CDATA
        buf = ""
        if (cOptions.indentText): buf = ind(cOptions, depth, "#cdata")
        em.emit(buf + "<![CDATA[%s]]>" % (escapeCDATA(self.data)))
    elif (ntype == Node.ENTITY_REFERENCE_NODE):       # 5
        pass #nop = 1
    elif (ntype == Node.ENTITY_NODE):                 # 6
        pass #nop = 1
    elif (ntype == Node.PROCESSING_INSTRUCTION_NODE): # 7 PI
        buf = ""
        if (cOptions.breakPIs): buf = ind(cOptions, depth, "#pi")
        em.emit(buf + "<?%s %s?>" % (self.target, escapePI(self.data)))

    elif (ntype == Node.COMMENT_NODE):                # 8 COMMENT
        buf = ""
        if (cOptions.breakComments): buf = ind(cOptions, depth, "#comment")
        em.emit(buf + "<!-- %s -->" % (self.data))
    elif (ntype == Node.DOCUMENT_NODE):               # 9 DOCUMENT
        #sys.stderr.write("DOCUMENT_NODE: docel %s, nchildren %d." %
        #    (type(self.documentElement), len(self.childNodes)))
        em.emit('<?xml version="1.0" encoding="utf-8"?>')
        if (not self.documentElement):
            for ch in self.childNodes:
                ch.collectAllXml2r(cOptions, depth+1)
        else:
            self.documentElement.collectAllXml2r(cOptions, depth+1)
    elif (ntype == Node.DOCUMENT_TYPE_NODE):          # 10
        em.emit('<!DOCTYPE %s []>' % (self.ownerDocument.documentElement.nodeName))
    elif (ntype == Node.DOCUMENT_FRAGMENT_NODE):      # 11
        pass #nop = 1
    elif (ntype == Node.NOTATION_NODE):               # 12
        pass #nop = 1
    else:
        raise ValueError("startCB: Bad DOM nodeType returned: %s." % ntype)
    return


###############################################################################
def collectAllXml(self:Node, delim=" ", indentString='    ',
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
    if (ntype == Node.ELEMENT_NODE):                  # 1 ELEMENT:
        attlist = getEscapedAttributeList(self,
            sortAttributes=False,
            quoteChar='"')
        textBuf += (indentString * depth) + "<" + name + attlist
        if (isEmpty):
            textBuf = textBuf + "/>"
        else:
            textBuf = textBuf + ">"
            for ch in self.childNodes:
                textBuf = textBuf + collectAllXml(ch, delim, 1, depth+1)
            if (indentString):
                textBuf = textBuf + (indentString * depth)
            textBuf = textBuf + "</" + name + ">" + lineBreak
    elif (ntype == Node.ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Why are we seeing an attribute node?")

    elif (ntype == Node.TEXT_NODE):                   # 3 TEXT
        textBuf = textBuf + escapeXml(self.data)

    elif (ntype == Node.CDATA_SECTION_NODE):          # 4
        pass
    elif (ntype == Node.ENTITY_REFERENCE_NODE):       # 5
        pass
    elif (ntype == Node.ENTITY_NODE):                 # 6
        pass
    elif (ntype == Node.PROCESSING_INSTRUCTION_NODE): # 7 PI
        textBuf += "<?" + self.target + " " + self.data + "?>"

    elif (ntype == Node.COMMENT_NODE):                # 8 COMMENT
        textBuf = textBuf + indent + "<!--" + self.data + "-->"
        if (indentString):
            textBuf = textBuf + lineBreak
    elif (ntype == Node.DOCUMENT_NODE):               # 9
        pass
    elif (ntype == Node.DOCUMENT_TYPE_NODE):          # 10
        pass
    elif (ntype == Node.DOCUMENT_FRAGMENT_NODE):      # 11
        pass
    elif (ntype == Node.NOTATION_NODE):               # 12
        pass
    else:
        raise ValueError("startCB: Bad DOM node type returned: %d" % ntype)

    return textBuf
# collectAllXml


###############################################################################
fhGlobal = None  # TODO Unglobalize this, probably via partial functions.

def export(self:Node, someElement, fh, includeXmlDecl=True, includeDoctype=False):
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
    eachNodeCB(someElement, callbackA=startCB, callbackB=endCB, depth=0)


def startCB(self:Node):
    """TODO: Convert to use tostring, getTag, etc.
    """
    buf = ""
    typ = self.nodeType
    if (typ == Node.ELEMENT_NODE):                   # 1:
        buf = "<" + self.nodeName + getEscapedAttributeList(self) + ">"
    elif (typ == Node.ATTRIBUTE_NODE):               # 2
        pass
    elif (typ == Node.TEXT_NODE):                    # 3
        buf = self.data
    elif (typ == Node.CDATA_SECTION_NODE):           # 4
        buf = "<![CDATA["
    elif (typ == Node.ENTITY_REFERENCE_NODE):        # 5
        pass
    elif (typ == Node.ENTITY_NODE):                  # 6
        pass
    elif (typ == Node.PROCESSING_INSTRUCTION_NODE):  # 7
        buf = "<?%s %s?>" % (self.target, escapePI(self.data))
    elif (typ == Node.DOCUMENT_NODE):                # 8
        pass
    elif (typ == Node.DOCUMENT_NODE):                # 9
        pass
    elif (typ == Node.DOCUMENT_TYPE_NODE):           # 10
        buf = "<!DOCTYPE>"
    elif (typ == Node.DOCUMENT_FRAGMENT_NODE):       # 11
        pass
    elif (typ == Node.NOTATION_NODE):                # 12
        pass
    else:
        raise ValueError("startCB: Bad DOM nodeType %d." % (typ))
    fhGlobal.write(buf)

def endCB(self:Node):
    """
    """
    buf = ""
    typ = self.nodeType

    if (typ == Node.ELEMENT_NODE):                   # 1:
        buf = "</" + self.nodeName + ">"
    elif (typ == Node.ATTRIBUTE_NODE):               # 2
        pass
    elif (typ == Node.TEXT_NODE):                    # 3
        pass
    elif (typ == Node.CDATA_SECTION_NODE):           # 4
        buf = "]]>"
    elif (typ == Node.ENTITY_REFERENCE_NODE):        # 5
        pass
    elif (typ == Node.ENTITY_NODE):                  # 6
        pass
    elif (typ == Node.PROCESSING_INSTRUCTION_NODE):  # 7
        pass
    elif (typ == Node.COMMENT_NODE):                 # 8
        pass
    elif (typ == Node.DOCUMENT_NODE):                # 9
        pass
    elif (typ == Node.DOCUMENT_TYPE_NODE):           # 10
        pass
    elif (typ == Node.DOCUMENT_FRAGMENT_NODE):       # 11
        pass
    elif (typ == Node.NOTATION_NODE):                # 12
        pass
    else:
        raise ValueError("endCB: Bad DOM nodeType %d." % (typ))

    fhGlobal.write(buf)

# END of DomExtensions definitions


###############################################################################
# GENERAL METHODS ON STRINGS
#
def escapeXmlAttribute(s, quoteChar='"'):
    """
    Turn characters special in (double-quoted) attributes, into char refs.
    Set to "'" if you prefer single-quoting your attributes.
    """
    s = nukeNonXmlChars(s)
    s = re.sub(r'&', "&amp;",   s)
    s = re.sub(r'<', "&lt;",    s)
    if (quoteChar == '"'): s = re.sub(r'"', "&quot;",  s)
    else: s = re.sub(r"'", "&apos;",  s)
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

def escapeASCII(s, width=4, base=16, htmlNames=True):
    """Turn all non-ASCII characters into character references.
    @param width: zero-pad numbers to at least this many digits.
    @param base: 10 for decimal, 16 for hexadecimal.
    @param htmlNames: If True, use HTML 4 named entities when applicable.
    """
    def escASCIIFunction(mat):
        """Turn all non-ASCII chars to character refs.
        """
        code = ord(mat.group[1])
        if (PY3):
            nonlocal width, base, htmlNames
        else:
            # https://stackoverflow.com/questions/3190706/
            raise ValueError("PY3 dependency: nonlocal.")  # TODO
        if (htmlNames and code in codepoint2name):
            return "&%s;" % (codepoint2name[code])
        if (base==10):
            return "&#%*d;" % (width, code)
        return "&#x%*x;" % (width, code)

    s = nukeNonXmlChars(s)
    s = re.sub(r'([^[:ascii:]])r', escASCIIFunction, s)
    s = escapeXml(s)
    return s

def nukeNonXmlChars(s):
    """Remove the C0 control characters not allowed in XML. Unassigned
    Unicode characters higher up, are left unchanged.
    """
    return re.sub("[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)

def unescapeXml(s):
    """Escape as needed for XML content: lt, amp, and ]]>.
    """
    return re.sub(r'&(#[xX])?(\w+);', unescapeXmlFunction, s)

def unescapeXmlFunction(mat):
    """
    Convert HTML entities, and numeric character references, to literal chars.
    """
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
xmlSpaceOnlyRegex = re.compile("^[%s]*$" % (xmlSpaceChars))

def normalizeSpace(s, allUnicode=False):
    """
    By default, this only normalizes *XML* whitespace,
    per the XML spec, section 2.3, grammar rule 3.

    NOTE: Most methods of removing Unicode whitespace in Python do not work
    for Unicode. See https://stackoverflow.com/questions/1832893/

    U+200B ZERO WIDTH SPACE is left untouched below.
    """
    if (allUnicode):
        s = re.sub(r'(?u)\s+', " ", s, re.UNICODE)
    else:
        s = re.sub(xmlSpaceRegex, " ", s)
    s = s.strip(' ')
    return s

def stripSpace(s:str, allUnicode=False):
    """
    Remove leading and trailing space, but don't touch internal.
    """
    if (allUnicode):
        s = re.sub(r'^(?u)\s+|(?u)\s+$', " ", s, re.UNICODE)
    else:
        s = re.sub(r'^%s|%s$' % (xmlSpaceRegex, xmlSpaceRegex), "", s)
    return s


###############################################################################
# Various places to put output data.
#
class Emitter:
    """Used by collectXML2 etc. to transmit data to any of several targets.
    This allows the same code to write to a file, a buffer, or whatever.
    """
    def __init__(self, where, arg=None):
        self.where       = where
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
            raise ValueError(
                "New Emitter: 'where' is '%s', not STRING|FILE|FH|CALLBACK."
                % (where))
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
    attribute's value. Raises IndexError if a value is not unique unless
    'duplicates' is set to True.
    """
    def __init__(self, docOrNode, aname, duplicates=False):
        """Scan a document (or at least a subtree) and build a dict of the
        values found for a given attribute.
        @param document: Document or subtree head Node to scan.
        @param aname: Name of attribute to be indexed.
        @param duplicates: If True, just replace when there's a duplicate.
        """
        super(DomIndex, self).__init__()

        if (docOrNode.nodeType == Node.DOCUMENT_NODE):
            self.document = docOrNode
            self.rootNode = docOrNode.getDocumentElement()
        else:
            self.document = docOrNode.ownerDocument
            self.rootNode = docOrNode
        self.attrName = aname

        node = self.rootNode
        finalNode = node.rightBranch
        while (node):
            if (node.nodeType==Node.ELEMENT_NODE):
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
#
class BS4Features:
    """Implement a few useful bits from "Beautiful Soup 4".
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/
    """
    @staticmethod
    def string(node):
        raise NOT_SUPPORTED_ERR

    @staticmethod
    def strings(node):
        """Generate the series of all text node descendants as strings.
        """
        for node in getAllDescendants(node, includeTypes=[ Node.TEXT_NODE ]):
            yield node.data

    @staticmethod
    def stripped_strings(node, normSpace=False, allUnicode=False):
        """Generate the series of all text node descendants as strings,
        but with leading and trailing space stripped. Also, skip any text
        nodes that are white-space-only.
        TODO: Probably should also have an option to normalize internal space,
        and perhaps Unicode as well as XML whitespace.
        """
        for node in getAllDescendants(node, includeTypes=[ Node.TEXT_NODE ]):
            if (normSpace):
                ss = normalizeSpace(node.data, allUnicode=allUnicode)
            else:
                ss = stripSpace(node.data, allUnicode=allUnicode)
            if (ss): yield ss

    @staticmethod
    def find_all(node, name, attrs=None, recursive=True, string=None,
        limit=0, class_=None, **kwargs):
        """
        @param name: Can take a string, regex, list, fn, or True.
        @param attrs: A dict of attrs, match them all.
        @param recursive: If False , only check direct children of node.
        @param string: Search by 'string', by which BS means text content.
            Not clear if it can match across text node boundaries.
        @param limit: Max number of nodes to return.
        @param class_: Matches against any token in @class. But if there's a
            space, search literally instead. To check multiple, you can't (BS)
            pass a list, but must switch to CSS selector syntax with CssSelect().
        @param **kwargs: Filter for an attr of that name (value True matches
            any value for the named attribute (even null???) To use attrs
            whose names aren't Python identifiers, pass them in a dict passed
            to 'attrs' instead
        """
        nFound = 0

        if (not recursive):
            for ch in node.childNodes:
                if (BS4Features.BSfind_matcher(ch, name,
                    attrs=attrs, string=string, class_=class_, **kwargs)):
                    yield ch
                    nFound += 1
                    if (limit and nFound >= limit): return
            return

        for desc in getAllDescendants(node):
            if (BS4Features.BSfind_matcher(desc, name,
                attrs=attrs, string=string, class_=class_, **kwargs)):
                yield desc
                nFound += 1
                if (limit and nFound >= limit): return
        return


    @staticmethod
    def BSfind_matcher(node, name,
        attrs=None, string=None, class_=None, **kwargs):
        """Approximate the semantics of filtering params for BS4 find_all() etc.
        """
        if (name and not node.match(name)): return False
        if (attrs):
            for k, v in attrs:
                if (not node.hasAttribute(k)): return False
                elif (node.getAttribute(k) != v): return False
        if (class_):
            if (not node.hasAttribute("class")): return False
            if (not re.search(
                r'\b'+class_+r'\b', node.hasAttribute("class"))):
                return False
        if (kwargs):
            for k, v in kwargs.items():
                if (not node.hasAttribute(k)): return False
                elif (node.getAttribute(k) != v): return False
        return True


    @staticmethod
    def find(node, **kwargs):
        """ Same as find_all limit=1.
        """
        raise NOT_SUPPORTED_ERR

    @staticmethod
    def CssSelect(node):
        """Pick elements via a CSS selector.
        Supports:
            element type
            space for descendant
            > for childNodes
            - for sibling
            . for class
            # for ID
            , for alternatives
            [x] for attr exists
            [x="y"] for attr value
        """
        raise NOT_SUPPORTED_ERR


    @staticmethod
    def select_one(node):
        raise NOT_SUPPORTED_ERR


###############################################################################
#
class NodeTypes(Enum):
    """Much more Pythonic than just constants as in DOM. For example, you
    can get the name, and they're actually a type so you can test membership.
    """
    NO_NODE: 0  # Added non-associating value.
    ELEMENT_NODE: 1
    ATTRIBUTE_NODE: 2
    TEXT_NODE: 3
    CDATA_SECTION_NODE: 4
    ENTITY_REFERENCE_NODE: 5  # Removed in DOM4.
    ENTITY_NODE: 6   # Removed in DOM4.
    PROCESSING_INSTRUCTION_NODE: 7
    COMMENT_NODE: 8
    DOCUMENT_NODE: 9
    DOCUMENT_TYPE_NODE: 10
    DOCUMENT_FRAGMENT_NODE: 11
    NOTATION_NODE: 12  # Removed in DOM4.


###############################################################################
#
class DomExtensions:
    def __init__(self):
        self.DE = 1

    @staticmethod
    def enableBrackets(toPatch=xml.dom.Node):
        """Patch in only the implementationa of __getItem__() and __contains__,
        which let you use list-bracket notation (with all 3 arguments) to pick out
        childNodes or attributes from Nodes. For example:

            myNode[0]            the same as myNode.childNodes[0]
            myNode['p']          gets the first child of element type 'p'
            myNode['p':0:3]      gets the first 3 'p' children of myNode.
            myNode['*':0:3]      gets the first 3 element children of myNode.
            myNode['#text':0:3]  gets the first 3 text node children of myNode.

        @return: A list, a scalar node, or IndexError.
        Raises IndexError any time the request cannot be satisfied.

        With only one integer index, return one item.
        This is true whether or not there is an alpha (nodeName) argument.

        With two integer indexes, return a list, even if it's a singleton.

        TODO: n['p'] should probably get all 'p' children rather than the first.
        TODO: Negative indexes are not yet supported (sorry!).
        TODO: Review exactly when it returns a list vs. a single item.
        """
        toPatch.__getItem__ = DEgetitem
        toPatch.__contains__ = DEcontains

    @staticmethod
    def patchDOM(toPatch=xml.dom.Node, getItem=True):
        """Some people capitalize acronyms.
        """
        DomExtensions.patchDom(toPatch=toPatch, getItem=getItem)

    @staticmethod
    def patchDom(toPatch=xml.dom.Node, getItem=True, axisSelects=True):
        """Monkey-patch the extension methods into a given class.
        See also patchDomAuto(), following.
        """
        testCase = getattr(toPatch, "selectAncestor", None)
        if (testCase and callable(testCase)): return

        if (getItem):
            toPatch.__getItem__ = DEgetitem
            toPatch.__contains__ = DEcontains

        toPatch.outerHTML               = outerHTML
        toPatch.innerHTML               = innerHTML
        toPatch.outerXML                = outerXML
        toPatch.innerXML                = innerXML
        toPatch.innerText               = innerText

        toPatch.nameOfNodeType          = nameOfNodeType

        if (axisSelects):
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

        toPatch.getLeastCommonAncestor  = getLeastCommonAncestor
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
        toPatch.getMyIndex              = getMyIndex
        toPatch.XPointerCompare         = XPointerCompare
        cmpMethod = getattr(toPatch, "compareDocumentPosition", None)
        if (not cmpMethod):
            toPatch.compareDocumentPosition = compareDocumentPosition
        toPatch.XPointerInterpret       = XPointerInterpret

        toPatch.nodeMatches             = nodeMatches
        toPatch.getInheritedAttribute   = getInheritedAttribute
        toPatch.getCompoundAttr         = getCompoundAttr
        toPatch.getEscapedAttribute     = getEscapedAttribute
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

        toPatch.eachNodeCB              = eachNodeCB
        toPatch.eachNode                = eachNode
        toPatch.reversedEachNode        = reversedEachNode
        toPatch.eachTextNode            = eachTextNode
        toPatch.eachElement             = eachElement
        #toPatch.eachElementOfType       = eachElementOfType
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
        toPatch.stripSpace              = stripSpace

        #NamedNodeMap.iteritems = nnmIteritems
        return

    @staticmethod
    def patchDomAuto(
        toPatch=xml.dom.Node,
        getItem:bool=True,      # patch __getItem__ and __contains__.
        axisSelects:bool=True,  # include select...
        excludes=None           # Don't add any listed here
        ) -> int:               # Return how many methods we added.
        """Monkey-patch the extension methods into a given class.
        Iterate over all the callables, so we don't miss anything.
        """
        testCase = getattr(toPatch, "selectAncestor", None)
        if (testCase and callable(testCase)): return

        if (getItem):
            toPatch.__getItem__ = DEgetitem
            toPatch.__contains__ = DEcontains

        toPatchDir = dir(toPatch)
        nAdded = 0
        de = DomExtensions()
        for k in dir(de):
            try:
                v = de.__getattribute__(k)
                if (not axisSelects and v.startswith("select")): continue
                if (excludes and v in excludes): continue
                if (not callable(v)): continue
                if (k in toPatchDir): print("Overriding '%s'." % (k))
                toPatch.setAttr(k, v)
                nAdded += 1
            except AttributeError:
                print(" %-30s  *** FAILED ***" % (k))
        return nAdded

###############################################################################
# Test driver
#
if __name__ == "__main__":
    import argparse

    def warn(lvl, msg):
        if (args.verbose >= lvl): sys.stderr.write(msg + "\n")

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

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
    DomExtensions.patchDOM()
    if (callable(xml.dom.Node.getDepth)):
        warn(0, "Patch succeeded.")
    else:
        warn(0, "Patch failed.")

    if (len(args.files) == 0):
        tfileName = "testDoc.xml"
        warn(0, "No files specified, trying %s." % (tfileName))
        args.files.append(tfileName)

    for path0 in args.files:
        fh0 = codecs.open(path0, "rb", encoding="utf-8")
        theDOM = xml.dom.minidom.parse(fh0)
        fh0.close()
        theDoc = theDOM.renameByTagName('p', 'para')

    warn(0, "Done.")
