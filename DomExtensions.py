#!/usr/bin/env python3
#
# DomExtensions: A bunch of (hopefully) useful additions to the DOM API.
# 2010-01-10: Written by Steven J. DeRose.
#
#pylint: disable=W0613, W0212, E1101
#
import sys
import re
import codecs
from enum import Enum
from typing import List, IO, Callable, Any, Union, Match, Iterable
from collections import namedtuple

import xml.dom
import xml.dom.minidom
from xml.dom.minidom import Node, NamedNodeMap, Element, Document
from html.entities import codepoint2name, name2codepoint

import logging
lg = logging.getLogger("DomExtensions.py")
lg.setLevel(logging.INFO)

def cmp(a, b) -> int: return ((a > b) - (a < b))

__metadata__ = {
    "title"        : "DomExtensions",
    "description"  : "A bunch of (hopefully) useful additions to the DOM API.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2010-01-10",
    "modified"     : "2021-07-08",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

An XML-manipulation package that sits on top of a generic DOM implementation
and provides a lot of higher-level methods, and more Pythonic syntax.

Or you may want to just take __getitem__, which lets you navigate DOM
trees very much like nested Python dicts and lists (see below for
details):   myRoot[4][2][3:"p"]...

This package also provides access along all of the XPath axes, so you can
easily get the n-th ancestor, descendant, preceding nodes (which are different
from preceding *sibling* nodes, also available), etc. Or iterate along an axis
in either direction.

It provides many "geometric" operations in the tree, such as
locating the left or right "branch", determing the sequence of nodeNames down to
a node, determining the child number of a node among its siblings (counting
text nodes or not),
comparing node order, containment, and some support for ranges (which also
can be in semi-precedence and other relationships). And it can map back and
forth a node plus optional local offset, to and from global text offsets.

It provides "bulk" operations such as removing all white-space-only nodes,
removing or renaming all instances of attributes or elements, and much more.

It also provides operations inspired by other work. It can generate and
interpretg XPointers; do what I see as the more useful BS4 "find" operations
and a variety of CSS selectors;
generate equivalent SAX event sequences from any subtree; etc.

This is intended to achieve a few basic things:

* provide more Pythonic bindings of DOM functionality
* save people from repeatedly implementing commonly-needed XML operations
* let people use operations they may be familiar with when coming to XML and DOM
from a variety of related milieux.

Comments are welcome, as are bug reports.
There is also a Perl version of this, though sometimes it falls behind this one.


==Usage==

You can use ''patchDOM''() to monkey-patch these routines into a class
(default: ''xml.dom.minidom.Node''):

    from DomExtensions import DomExtensions
    import xml.dom
    DomExtensions.patchDom(toPatch=xml.dom.minidom.Node)

or to just enable support for using Python's
subscript brackets: `myNode[...]`, do:

    DomExtensions.enableBrackets(toPatch=xml.dom.minidom.Node)

See [##Using \\[\\] notation], below, for the details. In short, you can say things
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

    DomExtensions.enableBrackets(toPatch=xml.dom.minidom.Node)

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

Several values have special meanings:

* "*" means any element child, but no text, comment, pi, or cdata nodes.
* "#text", "#comment", "#cdata", and "#pi" mean just children of that node type.
* a name beginning with `@`, such as "@id", gets the attribute

    if ("*" in myNode)...
    if ("#text" in myNode)...

To avoid ambiguity, the values including element type name as well as these
special names, are chere alled "kinds" of nodes.

As usual in Python, this only checks direct children; if a child
happens to have children of its own, `in` doesn't know anything about them.

Remember that in XML, the element type name is not a key, like in a Python `dict`,
but a type name. There can be any number of `p` elements in section, for example.
So a kind in brackets leads to a list coming back (which might have only one
, or might have many)

===Fancier cases===

The author recommends that you get used to the simpler cases first.

You can combine integer indexes and range, with element type constraints
(except for attributes -- you can't say ['@id':0:-1]).

If you want the fourth paragraph child element, use:

    myNode['p':3]

This is not quite the same as doing the opposite order! `myNode['p':3]` instead
finds the fourth child (of whatever type), and returns it if it is a `p`.
In other words, the indexes are interpreted in order from left to right. This
is familiar to XPath users, but there isn't really a comparable case with
Python lists.

If the fourth child is not a `p` element, `IndexError` is raised, just as for
any other "not found" case. Unfortunately, "in" has no way to test more than
the simplest condition, just as in Python you can't ask `[1:2] in myList`.
It may be more Pythonic the following way, which works fine:

    try:
        myStuff = myNode['p':3]
    except IndexError:
        myStuff = []

The same two cases can be used with a range instead of a singleton index:

    myNode["#text", 3:-1]

gets all text nodes from the fourth one to the last, while

    myNode[0:20:"*"]

gets all elements (but not other kinds of nodes) which are among the first 20 children of `myNode`.

==Choosing nodes along XPath axes==

A second major feature of DomExtensions, is called "Axis Selection".
It provides support for
walking all the XPath 'axes' in a DOM tree, such as
ancestors, children, descendants, siblings, and so on. Each axis is available
via a method called 'select' plus the axis name.

Because it's often useful to consider only element nodes,
or only text nodes, or only element nodes of a certain element type, or
with a certain attribute or attribute-value pair, optional arguments can be
used to filter in those ways:

The 'select...' methods return node [n] (counting from 0)
of a given type and/or attributes along a given axis.
For example:

    myNode.selectChild(3, nodeSel='li', attrs={'class':'major'})

This will return the fourth child of `myNode` which:

* is of the given element type name ('li'), and
* has the attribute ''class'' with value ''major''.

All the arguments are optional. If none are provided, the first item
along the axis (that is, #0) is returned.

Constraints:

* ''n'' counts from 0 and defaults to 0.
Most axes support negative indexes; but not yet all of them.

* ''nodeSel'' supports "*", "#text", "#comment", "#cdata", and "#pi", just like
the bracket notation described earlier. It defaults to "*".
The `attrs` argument cannot be used except with an element type name or "*".

qnames (names with a namespace) are not yet supported for ''nodeSel''.

* `attrs`, if provided, must be None or a dict of attribute name:value pairs,
which all must match for an element to be selected.
The kind of matching depends on the type of value passed in the dict:

* int or float: match numerically. Attribute values that are not
strings of Latin decimal digits will not match,
but will not raise exceptions either. Hexadecimal and other forms should
be added. [TODO]
* a compiled regex: the regex is matched against the attribute value.
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

* '''getCompoundAttribute'''(self, name, sep='#', keepMissing=False)

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

* '''compareDocumentPosition'''(n1, n2)

Compare two nodes for document order, returning -1, 0, or 1.

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

* '''compareXPointer'''(x1, x2)

Compare two XPointer child-sequences (see ''getXPointer'')
for relative document order, returning -1, 0, or 1.
This does not require actually looking at a document, so no document or
node is passed.

* '''interpretXPointer'''(document, x)

Interpret the XPointer child sequence in the string
''x'', in the context of the given ''document'',
and return the node it identifies (or None if there is no such node).

* '''getEscapedAttributeList'''(node, sortAttributes=False, quoteChar='"')

Return the entire attribute list for
''node'', as needed to go within a XML start-tag. The attributes are
quoted using `quoteChar`, and any <, &, or `quoteChar` in them
are replaced by the appropriate XML predefined charcter reference.
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
will get passed the generated result strings in document order.
The provided class has options to write them to a path or file handle,
collect them in a string buffer, or call some other callback for each.
By default, the result is collected in a string and passed back whole.

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

* '''buildIndex'''(attributeName)

Return a hash table in which each
entry has the value of the specified ''attributeName'' as key, and the element
on which the attribute occurred as value.
This is similar to the XSLT 'key' feature.

* '''find'''(value)


==Character stuff (internal methods)==

* '''escapeAttribute'''(string, quoteChar='"')

Escape the string as needed for it to
fit in an attribute value (amp, lt, and quot).

* '''escapeText'''(string)

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
If `htmlNames` is True, HTML 4 named entities are used when applicable,
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


=Known bugs and limitations=

* Axis selects should:

** uniformly support negative indexes  (currently only for the self, child,
and descendant axes).
** uniformly allow begin:end ranges.
** permit selecting elements and
attributes via regexes, and support multiple attribute constraints
(probably just allow passing a dict).

* `Node` is not changed to actually inherit from `list`, so there are surely some
list behaviors that I haven't included (yet). Like sorting. Let me know.

* qnames.

* The __getitem__() implementation for []-notation, like normal Python lists,
actually checks for `isinstance(arg, int)`, so `myNode["1"]` will not work.


=Model=

This makes accessing a DOM a lot more like using XPath, but stays in the
"walk around the structure" approach, rather than the "construct a query" one.

So, there are methods to retrieve items from along each XPath axis.

There is not a full filtering language like XPath, but when retrieving node,
you can specify very common constraints, such as:

* whether you want elements, attributes, text nodes, PIs, comments, etc.
* restrictions on the element types wanted (by string or regex)
* restriction to elements with certain attribute values
* whether whitespace-only text nodes "count" (this avoid a lot of testing)
* Going a distance along the axis, not just the "next" item as in DOM (other
than indexing into childNodes).

This also tries to be more Pythonic. For example, you can access child
nodes and attributes with the usual Python [] notation. Since Python []
can handle both strings and integers, you can say any of these:
    myNode[3] gets the 4th child node
    myNode["li"] gets all the child elements of type "li"
    myNode["@class"] gets the class attribute.

There are a few special values. "#text", "#pi", and "#comment" get just
the child nodes of those types, and
    myNode["*"] gets all the element children (very often needed)

You can also combine them and/or slice:
    myNode["p", 3] gets the 4th child element of type "p"
    myNode[1, 4] gets child nodes 1 through 3, just like Python lists
    myNode["p", 1, 4] extracts all the "p" children, then gets [1,4] among those

You can do some other things you'd expect, like copy() instead of cloneNode(), and
using operators instead of compareDocumentPosition.

* insertBefore and appendChild are just list splicing
* cloneNode becomes copy
* compareDocumentPosition becomes <, >, <=, >=, in, and contains.
Possibly PEP 465 infix matrix mult operator "@"? or // __floordiv__ or ** for descendant.
<< and >> for psib/fsib
* countOF for # of a in b
* Could overload elem @ "attrname"
* indexof
** TODO: should in/contains be direct or indirect? cf compareDocumentPosition().
* isEqualNode and isSameNode become == and is
* attributes can be referenced by ["@class"] etc.

Possible additions:
* += and -= may be mapped to preceding/following sibling n
*

=To do=

*** In patchDom(), test to make sure we don't overwrite anything already there.

*** Rename all nodeplus args to nodeSel. Check other naming consistency.

*** Rename all "Attribute" to "Attr"?

Add "tagToRuby".

Reduce redundancy in traversers and generators.

Rename to 'maxidom' or DOMPP?

Option to test/return nodeName always as localname or qname?

For canonical XML, make getEscapedAttributeList() put namespace attrs first,
and escape CR and all > in content.

* Update to use/provide whatwg DOM features like
NodeIterator and TreeWalker [https://dom.spec.whatwg.org/#nodeiterator]
and NodeFilters (latter is there as enum), DOMTokenList,...?

* Find a better solution for getting this to be a true subclass. The main issue is functions
that do constructions. They need to instantiate based on the fancier extended Node.
I think the culprits are (see https://github.com/python/cpython/blob/main/Lib/xml/dom/minidom.py):
    DOMImplementation.createDocument
    DOMImplementation.createDocumentType
    Document.createDocumentFragment
    Document.createElement
    Document.createTextNode
    Document.createCDATASection
    Document.createComment
    Document.createProcessingInstruction
    Document.createAttributec
    Document.createElementNS
    Document.createAttributeNS
    Document._create_entity
    Document._create_notation

** E.g.:
    Make: class XNode(Node), class DOMImplementation(DOMImplementation)
    Subclass all the subclasses of Node, to be based on XNode
    Change all the methods that construct, like:
    *Except* that these are methods on (e.g.) Document, that create OTHER classes....
    So maybe easier to explicitly construct XTextNode, etc -- though that
    doesn't really solve the general problem.

* Support negative 'n' for rest of axis selects.
* Allow creating nodes with no ownerDocument; they get attached when inserted.
* Implement splitNode and wrap/surround(see help)
* Let appendChild, insertBefore, insertAfter, etc. take lists.
* Change eachTextNode, etc. to be real generators.
* Finish type-hinting.
* Add access for items in NamedNodeMaps via [] notation.
* Option for innerXml/outerXml to guarantee Canonical result (in progress).
* Promote attribute to element type?

==Lower priority==

* Add insertParent
* Possibly support myNode[["P"]] to scan all descendants (by analogy
with XPath "//" operator).
* Possibly support entire XPath (though other solution integrate it, so maybe not).
* Add a way to turn off all indenting for collectAllXml2 with one option.
* Implement a few useful BS4 bits (see class BS4Features) (and add to help).
* String to tag converter, like for quotes?
* Normalize line-breaks, Unicode whitespace within text nodes
* Consider additions from https://lxml.de/api/index.html:
** strip_attributes,....
* Possibly, extend `innerXML`, `innerText`, etc. to be able to exclude
certain subtrees, such as for embedded footnotes, speaker tags interrupting
speeches, etc.?
* Move in matchesToElements from mediaWiki2HTML.
* Sync with XPLib.js
* Find next node of given qgi? Select by qgi?
* String to entity ref, like for quotes, dashes, odd spaces, etc.
* Un-namespace methods: merge ns1/ns2; change prefix/url; drop all;....
* Allow choice of how to 'escape' PIs and comments.
* More optional parameters for Document.create___ (like attrs on element).
* More flexibility on createAttribute etc.


=Related commands=

`JSLIBS/DomExtension.js` -- obsolete but similar Javascript version.

`DOMTableTools.py` -- DOM additions specifically for tables.

`testDom.py` -- a package of test cases to exercise DOM and this.

`BaseDom.py` -- A very simple DOM implementation in pure Python. Mostly for testing.

`Dominus.py` -- a disk-resident DOM implementation that can handle absurdly
large documents.

`XmlOutput.pm` -- Makes it easy to produce WF XML output. Provides methods
for escaping data correctly for each relevant context; knows about character
references, namespaces, and the open-element context; has useful methods for
inferring open and close tags to keep things in sync.


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
* 2021-07-08: Add some methods omitted from patchDom(). Add checking for such.
Type-hinting. Proof and sort patchDom list vs. reality.
* 2021-07-20: Fix eachNode for attribute nodes. Add removeNodesByNodeType().
* 2022-01-27: Fix various annoying bugs with NodeTypes Enum. Remember that the Document
element is really an element. Improve handling for bool and for multi-token values
in getAttributeAs(). Turn off default of appending id comment in getEndTag().
* 2023-02-06: Clean up parent/sibling insert/wrap methods.
* 2023-04-28; Move table stuff to DOMTableTools.py. Implement comparison operators.
* 2023-07-21: Fix getFQGI(), getContentType(). Add getTextLen().


=Rights=

Copyright 2010, 2020, Steven J. DeRose. This work is licensed under a Creative
Commons Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].

Many of the methods here are based on
[https://www.w3.org/TR/1999/REC-xpath-19991116/] and on my paper:
"JSOX: A Justly Simple Objectization for XML,
or: How to do better with Python and XML."
Balisage Series on Markup Technologies, vol. 13 (2014).
[https://doi.org/10.4242/BalisageVol13.DeRose02].


=Options=
"""


###############################################################################
#
_regexType = type(re.compile(r'a*'))

class XMLStrings:
    """This class contains static methods and variables for basic XML
    operations such as testing syntax forms, escaping strings, etc.
    """
    _xmlSpaceExpr = r"[ \t\n\r]+"

    _xmlSpaceChars = " \t\r\n"
    _xmlSpaceRegex = re.compile("[%s]+" % (_xmlSpaceChars))
    _xmlSpaceOnlyRegex = re.compile("^[%s]*$" % (_xmlSpaceChars))


    # This excludes colon (":"), since we want to distinguish QNames.
    _nameStartChar = str("[_A-Za-z" +
        "\u00C0-\u00D6" + "\u00D8-\u00F6" + "\u00F8-\u02FF" +
        "\u0370-\u037D" + "\u037F-\u1FFF" + "\u200C-\u200D" +
        "\u2070-\u218F" + "\u2C00-\u2FEF" + "\u3001-\uD7FF" +
        "\uF900-\uFDCF" + "\uFDF0-\uFFFD" +
        "\u10000-\uEFFFF" +
        "]")
    _nameChar  = re.sub(
        "^\\[", "[-.0-9\u00B7\u0300-\u036F\u203F-\u2040", _nameStartChar)
    _justName = _nameStartChar + _nameChar + "*"
    _xmlName  = r"^%s$" % (_justName)
    _xmlQName = r"^(%s:)?%s$" % (_xmlName, _xmlName)
    _xmlPName = r"^(%s:)%s$" % (_xmlName, _xmlName)

    @staticmethod
    def isXmlName(s:str) -> bool:
        """Return True for a NON-namespace-prefixed    (aka) local name.
        """
        if (re.match(XMLStrings._xmlName, s, re.UNICODE)): return True
        return False

    @staticmethod
    def isXmlQName(s:str) -> bool:
        """Return True for a namespace-prefixed OR unprefixed name.
        """
        if (re.match(XMLStrings._xmlQName, s, re.UNICODE)): return True
        return False

    @staticmethod
    def isXmlPName(s:str) -> bool:
        """Return True only for a namespace-prefixed name.
        """
        if (re.match(XMLStrings._xmlPName, s, re.UNICODE)): return True
        return False

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
            * pi: #PI
            * comment: #COMMENT
            * text: #PI (should there be a non-white-space-only textnode selector?)
            * and we allow "*" to mean any element
        fragment, namespace, etc. are just special cases of more basic types.
        """
        if (XMLStrings.isXmlQName(s)): return True
        if (s in [ "*", "#text", "#comment", "#cdata", "#pi" ]): return True
        if (s[0] == "@" and XMLStrings.isXmlName(s[1:])): return True
        return False

    @staticmethod
    def isXmlNumber(s:str) -> bool:
        """Check whether the token is a NUMTOKEN.
        """
        return bool(re.match(r"\d+$", s))


    ###########################################################################
    # GENERAL METHODS ON STRINGS
    #
    @staticmethod
    def escapeAttribute(s:str, quoteChar:str='"') -> str:
        """Turn characters special in (double-quoted) attributes, into char refs.
        Set to "'" if you prefer single-quoting your attributes, in which case
        that character is replaced by a character reference instead.
        This always uses the predefined XML named special character references.
        """
        s = XMLStrings.nukeNonXmlChars(s)
        s = s.replace('&', "&amp;")
        s = s.replace('<', "&lt;")
        if (quoteChar == '"'): s = s.replace('"', "&quot;",)
        else: s = s.replace("'", "&apos;")
        return s
    escapeXmlAttribute = escapeAttribute

    @staticmethod
    def escapeText(s:str, escapeAllGT:bool=False) -> str:
        """Turn things special in text content, into char refs.
        This always uses the predefined XML named special character references.
        """
        s = XMLStrings.nukeNonXmlChars(s)
        s = s.replace('&',   "&amp;")
        s = s.replace('<',   "&lt;")
        if (escapeAllGT): s = s.replace('>', "&gt;")
        else: s = s.replace(']]>', "]]&gt;")
        return s

    escapeXmlText = escapeText

    @staticmethod
    def escapeCDATA(s:str, replaceWith:str="]]&gt;") -> str:
        """XML Defines no particular escaping for this, we use char-ref syntax.
        """
        s = XMLStrings.nukeNonXmlChars(s)
        s = s.replace(']]>', replaceWith)
        return s

    @staticmethod
    def escapeComment(s:str, replaceWith:str="-&#x002d;") -> str:
        """XML Defines no particular escaping for this, we use char-ref syntax.
        """
        s = XMLStrings.nukeNonXmlChars(s)
        s = s.replace('--', replaceWith)
        return s

    @staticmethod
    def escapePI(s:str, replaceWith:str="?&gt;") -> str:
        """XML Defines no particular escaping for this, we use char-ref syntax.
        """
        s = XMLStrings.nukeNonXmlChars(s)
        s = s.replace(r'\?>', replaceWith)
        return s

    @staticmethod
    def escapeASCII(s:str, width:int=4, base:int=16, htmlNames:bool=True) -> str:
        """Turn all non-ASCII characters into character references.
        @param width: zero-pad numbers to at least this many digits.
        @param base: 10 for decimal, 16 for hexadecimal.
        @param htmlNames: If True, use HTML 4 named entities when applicable.
        """
        # TODO: What is the right type to use for mat? _sre.SRE_Match ?
        def escASCIIFunction(mat:Match) -> str:
            """Turn all non-ASCII chars to character refs.
            """
            code = ord(mat.group[1])
            nonlocal width, base, htmlNames
            if (htmlNames and code in codepoint2name):
                return "&%s;" % (codepoint2name[code])
            if (base == 10):
                return "&#%*d;" % (width, code)
            return "&#x%*x;" % (width, code)

        s = XMLStrings.nukeNonXmlChars(s)
        s = re.sub(r'([^[:ascii:]])r', escASCIIFunction, s)
        s = XMLStrings.escapeText(s)
        return s

    @staticmethod
    def nukeNonXmlChars(s:str) -> str:
        """Remove the C0 control characters not allowed in XML.
        Unassigned Unicode characters higher up are left unchanged.
        """
        return re.sub("[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(s))

    @staticmethod
    def unescapeXml(s:str) -> str:
        """Escape as needed for XML content: lt, amp, and ]]>.
        """
        return re.sub(r'&(#[xX])?(\w+);', XMLStrings.unescapeXmlFunction, s)

    @staticmethod
    def unescapeXmlFunction(mat:Match) -> str:
        """Convert HTML entities and numeric character references to literal chars.
        """
        if (len(mat.group(1)) == 2):
            return chr(int(mat.group[2], 16))
        elif (mat.group(1)):
            return chr(int(mat.group[2], 10))
        elif (mat.group(2) in name2codepoint):
            return name2codepoint[mat.group(2)]
        else:
            raise ValueError("Unrecognized entity: '%s'." % (mat.group(0)))

    @staticmethod
    def normalizeSpace(s:str, allUnicode:bool=False) -> str:
        """By default, this only normalizes *XML* whitespace,
        per the XML spec, section 2.3, grammar rule 3.

        NOTE: Most methods of removing Unicode whitespace in Python do not work
        for Unicode. See https://stackoverflow.com/questions/1832893/

        U+200B ZERO WIDTH SPACE is left untouched below.
        """
        if (allUnicode):
            s = re.sub(r'(?u)\s+', " ", s, re.UNICODE)
        else:
            s = re.sub(XMLStrings._xmlSpaceRegex, " ", s)
        s = s.strip(' ')
        return s

    @staticmethod
    def stripSpace(s:str, allUnicode:bool=False) -> str:
        """Remove leading and trailing space, but don't touch internal.
        """
        if (allUnicode):
            s = re.sub(r'^(?u)\s+|(?u)\s+$', " ", s, re.UNICODE)
        else:
            s = re.sub(r'^%s|%s$' %
                (XMLStrings._xmlSpaceRegex, XMLStrings._xmlSpaceRegex), "", s)
        return s


###############################################################################
# A couple fake types, for type-hinting parameters.
# Would be nicer but non-trivial to implement these as subclasses of str.
#
NMToken = str  # An XML name token (mainly for type hint readability)
NodeSel = str  # Union(XMLQName, "@"+XMLQName, "*", "#text", "#comment", "#cdata", "#pi")


###############################################################################
# Exceptions and assertions
#
class NOT_SUPPORTED_ERR(Exception):
    pass

class HIERARCHY_REQUEST_ERR(Exception):
    """Thrown when requested navigation through the tree cannot be done.
    """

def assertElement(self:Node):
    assert self.nodeType==Node.ELEMENT_NODE, "We're at a %s, not an element." % (
        self.nameOfNodeType())


###############################################################################
#
class Axes(Enum):
    """A list of the XPath axes. With a bit each, so they can be ORed.
    That's mainly to enable an "or self" axis for every other axis (though it
    seems unlikely for ATTRIBUTE). For other combinations, a definition of
    relative order would be needed. For example, in what order would nodes
    along PSIBLING|FSIBLING be checked? Also, some nodes occur in
    multiple axes relative to a given starting node (e.g., CHILD|DESCENDANT).
    For the present, only SELF can be combined with others.

    Possibly introduce axis-specific prefixes to __getitem__ -- like current "@",
    but all the others apply only to element targets?
    """
    NONE            = 0x000  #
    SELF            = 0x001  # .
    ANCESTOR        = 0x002  # ..
    CHILD           = 0x004  # /
    DESCENDANT      = 0x008  # //
    PSIBLING        = 0x010  # <  # or arrows?
    FSIBLING        = 0x020  # >
    PRECEDING       = 0x040  # <<
    FOLLOWING       = 0x080  # >>
    ATTRIBUTE       = 0x100  # @

    ANCESTOR_SELF   = 0x003  #
    DESCENDANT_SELF = 0x009  #


###############################################################################
#
class DOCUMENT_POSITIONS(Enum):
    """Like DOM's compareDocumentPosition but more complete.
    See DOM Node.Node.DOCUMENT_POSITION_xxx.
    """
    DOCPOS_EQUAL = 0  # Not defined in DOM, bit 0 is what you get....
    DOCPOS_DISCONNECTED = 1
    DOCPOS_PRECEDING = 2
    DOCPOS_FOLLOWING = 4
    DOCPOS_CONTAINS = 8
    DOCPOS_CONTAINED_BY = 16
    #
    DOCPOS_IMPLEMENTATION_SPECIFIC = 32
    #
    DOCPOS_SWAPPABLE = 32 ^ 8 ^ 16  # Like <b><i>hello></i></b>
    DOCPOS_SEMI_PRECEDING = 32 ^ 2  # For overlap
    DOCPOS_SEMI_FOLLOWING = 32 ^ 4  # For overlap


###############################################################################
#
class NodeSelKind(Enum):
    """Major types of arguments for DEgetitem etc.
    This has two main uses:

    1: given one of the 3 args to __getitem__, identify what kind it is.
       Int seems most likely, which is why that's here.
    2: Helping interpret the similar arg to many selection/navigation
       methods, e.g., selectChild("#pi", n=1). In that case, the
       arg can also be a regex, which specifies matching nodeNames.

    The model here is:
        There are BRANCHES and LEAVES.
        BRANCHES have a name, attribute dict, and child list.
        ELEMENTS, DOCUMENT, DOC_FRAG are all BRANCHES.
        All other node types are leaves, with one data item (usually a string).
        Attributes are LEAVES, named by "@" plus their usual name, with the
        value as their data (usually a string).
    """
    ARG_NONE      = 0x000  # Failed
    ARG_INT       = 0x001  # (this is for the non-nodeKind (index) args only)
    ARG_NAME      = 0x002  # Any QName
    ARG_REGEX     = 0x004  # A compiled regex, to match vs. element names
    ARG_ATTR      = 0x008  # @ + QName
    ARG_STAR      = 0x010  # "*"
    ARG_TEXT      = 0x020  # #text
    ARG_PI        = 0x040  # #pi
    ARG_COMMENT   = 0x080  # #comment
    ARG_CDATA     = 0x100  # #cdata

    ARG_NONCOM    = 0xF7F  # Anything BUT comments

    # Possible additions:
    # ARG_space    =        # for white-space-only text nodes,
    # ARG_realtext =        # for non-white-space-only text nodes,
    # ARG_basic    =        # for union of text, element, and cdata

    @staticmethod
    def getKind(someArg:Union[str, int]) -> 'NodeSelKind':  # nee def argType()
        """Categorize one of the arguments to __getitem__().
        """
        if (someArg is None):
            return NodeSelKind.ARG_NONE
        if (isinstance(someArg, int)):
            return NodeSelKind.ARG_INT

        if (XMLStrings.isXmlName(someArg)):
            return NodeSelKind.ARG_NAME
        if (someArg == "*"):
            return NodeSelKind.ARG_STAR

        if (someArg[0] == "@" and XMLStrings.isXmlName(someArg[1:])):
            return NodeSelKind.ARG_ATTR
        if (someArg == "#noncom"):
            return NodeSelKind.ARG_NONCOM
        # Next 3 can all be handled by _getListItemsByKind_()
        if (someArg == "#text"):
            return NodeSelKind.ARG_TEXT
        if (someArg ==  "#comment"):
            return NodeSelKind.ARG_COMMENT
        if (someArg == "#pi"):
            return NodeSelKind.ARG_PI
        if (someArg == "#cdata"):
            return NodeSelKind.ARG_CDATA
        #if (someArg == ".."): return NodeSelKind.ARG_ANCESTOR

        raise ValueError("Argument '%s' not of udentifiable kind." % (someArg))

def isLeafType(node:Node) -> bool:
    """Return whether the node is of a nodeType that can only ever be a leaf.
    Not to be confused with isLeaf().
    """
    return (node.nodeType in [
        Node.TEXT_NODE, Node.CDATA_SECTION_NODE, Node.COMMENT_NODE,
        Node.ATTRIBUTE_NODE, Node.PROCESSING_INSTRUCTION_NODE,
    ])

def isLeaf(node:Node) -> bool:
    """Return whether the node is in fact a leaf (no childnodes).
    """
    return bool(node.childNodes)


###############################################################################
# Methods to patch on DOM Node.
#
#try:
#    from BaseDom import BaseDom
#    BaseDom.usePythonExceptions()
#except ImportError as e:
#    sys.stderr.write("DomExtensions: Could not import BaseDom for Exceptions.\n")
#
def DEgetitem(self:Node, n1, n2=None, n3=None) -> List:
    """Access nodes via Python list notation, based on my paper:
      DeRose, Steven J. JSOX: A Justly Simple Objectization for XML:
      Or: How to do better with Python and XML.
      Balisage Series on Markup Technologies, vol. 13 (2014).
      https://doi.org/10.4242/BalisageVol13.DeRose02.

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

    TODO: Test support for negatives -- anything missing?
    TODO: Test cases like [1:] and [:5]

    TODO: Perhaps allow name ".." for ancestor axis?
    TODO: Perhaps extend [] to support jQuery-style CSS selectors?
    TODO: Perhaps allow regexes for name?
    TODO: Perhaps move attrs to setAttr space, access w/ . notation?
    """
    typ1 = NodeSelKind.getKind(n1)
    typ2 = NodeSelKind.getKind(n2)
    typ3 = NodeSelKind.getKind(n3)
    if (n3 is not None): nargs = 3
    elif (n2 is not None): nargs = 2
    else: nargs = 1

    if (typ2==NodeSelKind.ARG_ATTR or typ3==NodeSelKind.ARG_ATTR or
        (typ1==NodeSelKind.ARG_ATTR and nargs > 1)):
        raise IndexError("No other indexes allowed with @xxx.")

    if (nargs == 1):
        if (typ1 == NodeSelKind.ARG_INT):                 # [0]
            return self.childNodes[n1]
        if (typ1 == NodeSelKind.ARG_ATTR):                # ['@id']
            return self.attributes.getNamedItem(n1[1:])
        return self._getChildNodesByKind_(n1)             # ['p'] ['#text'] ['*']

    elif (nargs == 2):
        if (typ1 == NodeSelKind.ARG_INT):
            if (typ2 == NodeSelKind.ARG_INT):             # [0:2]
                return self.childNodes[n1:n2]
            return self._getChildNodesByKind_(n2)[n1]     # [0:'p']
        else:
            if (typ2 == NodeSelKind.ARG_INT):             # ['x':0]
                return self._getChildNodesByKind_(n1)[n2]
            else:                                         # ['x':'x']
                raise IndexError("More than one non-int index.")

    else:  # nargs==3
        if (typ1 == NodeSelKind.ARG_INT and
            typ2 == NodeSelKind.ARG_INT):
            if (typ3 == NodeSelKind.ARG_INT):             # [0:5:2]
                return self.childNodes[n1:n2:n3]
            else:                                         # [0:5:'p']
                nodeList = self.childNodes[n1:n2]
                return self._getListItemsByKind_(nodeList, n3)
        elif (typ2 == NodeSelKind.ARG_INT and             # ['x':0:1]
              typ3 == NodeSelKind.ARG_INT):
            return self._getChildNodesByKind_(n1)[n2:n3]
        else:                                             # FAIL
            raise IndexError(
                "No 2 adjacent ints in [%s:%s:%s] for a Node." % (n1, n2, n3))

def containsKind(self:Node, nodeSel:NodeSel, orSelf:bool=False, direct:bool=False) -> bool:
    """Test whether the node contains a node of the given nodeSel kind.
    @param orSelf: If True, the node itself counts.
    @param direct: If True, indirect descendants do not count.
    """
    if (orSelf):
        if (self.nodeMatches(nodeSel)): return True
    if (direct):
        if (self.selectChild(1, nodeSel) is not None): return True
    else:
        if (self.selectDescendant(1, nodeSel) is not None): return True
    return False

def _getChildNodesByKind_(self:Node, nodeSel:NodeSel) -> list:
    """Return a list of this node's children of a given kind.
    """
    if (isLeafType(self)): return None
    return self._getListItemsByKind_(self.childNodes, nodeSel)

def _getListItemsByKind_(self:Node, theList:list, nodeSel:NodeSel) -> list:
    """No attributes or ints here.
    """
    nk = NodeSelKind.getKind(nodeSel)
    if (nk not in [ NodeSelKind.ARG_PI, NodeSelKind.ARG_COMMENT,
        NodeSelKind.ARG_CDATA, NodeSelKind.ARG_STAR, NodeSelKind.ARG_NAME ]):
        raise IndexError(
            "Node index '%s' is not a #-type, '*', or element type." % (nodeSel))
    inodes = []
    for item in theList:
        if (item.nodeType==Node.ELEMENT_NODE and
            (nodeSel=='*' or item._nodeName==nodeSel)):
            inodes.append(item)
    return inodes


###############################################################################
# Methods to make minidom (or whatever) look more like JS DOM.
#
breakEndTags = False  # TODO: Temporary....

def outerXML(self:Node, indent:str=None, usePretty:bool=False) -> str:
    """Collect the XML-serialized subtree, including the start and end tags.
    @param indent: If set, pretty-print as we go.
    @param usePretty: If set, apply alternate serializer toprettyxml().
    """
    if (usePretty):
        buf = self.toprettyxml()
        return buf.getvalue()

    return self.getStartTag() + self.innerHTML(indent=indent) + self.getEndTag()

def innerXML(self:Node, cOptions=None, indent:str=None, depth:int=0) -> str:
    """Collect the XML-serialized subtree, but not the start and end tags.
    @param indent: If set, pretty-print as we go.
    """
    indentString = "" if (not indent) else ("\n" + indent*depth)
    t = ""
    for curNode in self.childNodes:
        ty = curNode.nodeType
        if (ty == Node.TEXT_NODE):
            #sys.stderr.write("#TEXT: %s" % (curNode.nodeValue))
            t += curNode.nodeValue
        elif (ty==Node.DOCUMENT_NODE or
              ty==Node.DOCUMENT_FRAGMENT_NODE or
              ty==Node.ELEMENT_NODE):
            t += indentString + curNode.getStartTag()
            for ch in (curNode.childNodes):
                t += ch.innerXML(cOptions=cOptions, depth=depth+1)
            if (breakEndTags): t += indentString
            t += curNode.getEndTag()
        elif (ty == Node.CDATA_SECTION_NODE):
            t += "<![CDATA[%s]]>" % (XMLStrings.escapeCDATA(curNode.data))
        elif (ty == Node.ENTITY_REFERENCE_NODE):
            pass
        elif (ty == Node.ENTITY_NODE):
            pass
        elif (ty == Node.PROCESSING_INSTRUCTION_NODE):
            t += indentString + "<?%s?>" % (curNode.data)
        elif (ty == Node.COMMENT_NODE):
            t += indentString + "<!--%s-->" % (curNode.data)
        elif (ty == Node.DOCUMENT_TYPE_NODE):
            t += "<!DOCTYPE %s>" % (curNode.data)
        elif (ty == Node.NOTATION_NODE):
            pass
        #elif (ty == Node.ATTRIBUTE_NODE):
        #    (done by Node.ELEMENT_NODE)
        else:
            sys.exit("Unknown node type %d." % (ty))
    return t

def outerHTML(self:Node, cOptions=None, indent:str=None) -> str:
    return self.outerXML(cOptions=cOptions, indent=indent)
def innerHTML(self:Node, cOptions=None, indent:str=None) -> str:
    return self.innerXML(cOptions=cOptions, indent=indent)

def innerText(self:Node, sep:str='', stripWS:bool=False) -> str:
    """Like usual innertext, but a function (instead of a property), and allows
    inserting something in between all the text nodes (typically a space,
    so text of list items etc. don't join up. But putting in spaces around
    HTML inlines like i and b may occasionally be wrong.
    TODO: Should 'stripWS' only do XML WS? Add option for inline-list?
    """
    if (self.nodeType == Node.TEXT_NODE or
        self.nodeType == Node.CDATA_SECTION_NODE):
        #sys.stderr.write("innerText got '%s'.\n" % (self.nodeValue or ""))
        txt = self.nodeValue or ""
        if (stripWS): txt = txt.strip()
        return txt
    if (self.nodeType != Node.ELEMENT_NODE):  # PI, comment
        return ""
    t = ""
    for childNode in self.childNodes:
        if (t): t += sep
        t += innerText(childNode, sep=sep)
    return t


###############################################################################
# Methods to add to NamedNodeMap to make it more usable.
# xml.dom.minidom claims to have this, but I have had problems with it.
# http://epydoc.sourceforge.net/stdlib/xml.dom.minidom.NamedNodeMap-class.html
#
def NNM_iteritems(self:NamedNodeMap):
    """Let us iterate (I think this got added eventually).
    """
    for k in self.keys:
        yield (k, self[k])

def NNM_getitem(self:NamedNodeMap, which):
    """Allow accessing attributes by number.
    """
    if (isinstance(which, int)):
        return self.items()[which]
    else:
        return self.getNamedItem(which).value


###############################################################################
# Extended "Axis selects".
#
# Methods for finding the nth node along a given axis, that has a given
# element type and/or attribute/value.
#
# TODO: Support negative to go from end in remaining cases.
#
def selectSelf(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    if (self.nodeMatches(nodeSel, attrs)):
        if (n == 0 or n == -1): return self
    return None

def selectAncestor(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """Return the first/nth ancestor that fits the requirements.
    TODO: Support negative n.
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectPreceding() doesn't support negative indexes yet.")
    cur = self.parentNode
    return cur.selectAncestorOrSelf(n=n, nodeSel=nodeSel, attrs=attrs)

def selectAncestorOrSelf(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """Like selectAncestor(), but the node itself is also considered.
    n=-01 means the outermost one (if no
    other constraints are given, the document element).
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectPreceding() doesn't support negative indexes yet.")
    found = 0
    cur = self
    while (cur):
        if (cur.nodeMatches(nodeSel, attrs)):
            found += 1
            if (found >= n): return cur
        cur= cur.parentNode
    return None

def selectChild(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """n=-01 means the last one.
    """
    found = 0
    if (isLeafType(self)): return None
    if (n >= 0):
        lg.info("At %s: '%s' (%s).", self.nodeType, self.nodeName, type(self))
        cur = self.firstChild
        while (cur):
            if (self.nodeMatches(nodeSel, attrs)):
                found += 1
                if (found >= n): return cur
            cur = cur.nextSibling
    else:
        cur = self.selectLastChild()
        while (cur):
            if (self.nodeMatches(nodeSel, attrs)):
                found += 1
                if (found >= -n): return cur
            cur = cur.precedingSibling

    return None

def selectDescendantOrSelf(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """TODO: Support negative n.
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectDescendantOrSelf() doesn't support negative indexes yet.")
    if (self.nodeMatches(nodeSel, attrs)):
        if (n == 0): return self
        n -= 1
    return _selectDescendantR(n, nodeSel, attrs)

def selectDescendant(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    return _selectDescendantR(n, nodeSel, attrs)

def _selectDescendantR(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    found = 0
    if (n >= 0):
        if (self.nodeMatches(nodeSel, attrs)):
            found += 1
            if (found >= n): return self
        for ch in self.childNodes:
            node = self.getDescendantByAttributeR(ch, n, nodeSel, attrs)
            if (node):
                found += 1
                if (found >= n): return ch
        return None
    else:
        cur = self.rightBranch
        while (cur != self):
            if (cur.nodeMatches(nodeSel, attrs)): found += 1
            if (found >= -n): return cur
            cur = cur.getPreceding()
        return None

def selectPreceding(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """TODO: Support -n
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectPreceding() doesn't support negative indexes yet.")
    cur = getPreceding(self)
    found = 0
    while (cur):
        if (isWithin(self, cur)): continue  # No ancestors, please.
        if (cur.nodeMatches(nodeSel, attrs)):
            found += 1
            if (found >= n): return cur
        cur = getPreceding(cur)
    return None

def getPreceding(self:Node) -> Node:
    """Get the immediately preceding node, if any. This includes earlier
    descendents of ancestors, but not ancestors themselves, as in XPath.
    """
    cur = self
    while (cur):
        ns = cur.precedingSibling
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
        ns = cur.previousSibling
        if (ns):
            rb = ns.rightBranch()
            if (rb): return rb
            return ns
        cur = cur.parentNode
    return None

def selectFollowing(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """As in XPath, does not include descendants.
    See https://stackoverflow.com/questions/44377798/
    TODO: Support -n
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectFollowing() doesn't support negative indexes yet.")
    cur = self.getFollowing()
    found = 0
    while (cur):
        if (cur.nodeMatches(nodeSel, attrs)):
            found += 1
            if (found >= n): return cur
        cur = self.getFollowing()
    return None

def getFollowing(self:Node) -> Node:
    """As in XPath, does not include descendants.
    See https://stackoverflow.com/questions/44377798/
    """
    cur = self
    while (cur):
        ns = cur.nextSibling
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
        ns = cur.nextSibling
        if (ns): return ns
        cur = cur.parentNode
    return None

def selectPrecedingSibling(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """TODO: Support -n
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectPrecedingSibling() doesn't support negative indexes yet.")
    cur = self.previousSibling
    found = 0
    while (cur):
        if (cur.nodeMatches(nodeSel, attrs)):
            found += 1
            if (found >= n): return cur
        cur = cur.previousSibling
    return None

def selectFollowingSibling(self:Node, n:int=0, nodeSel:NodeSel="", attrs:dict=None) -> Node:
    """TODO: Support -n
    """
    if (n < 0):
        raise NOT_SUPPORTED_ERR("selectFollowingSibling() doesn't support negative indexes yet.")
    cur = self.getFollowingSibling()
    found = 0
    while (cur):
        if (cur.nodeMatches(nodeSel, attrs)):
            found += 1
            if (found >= n): return cur
        cur = cur.getFollowingSibling()
    return None

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
    """Find the furthest node down if you always go left.
    """
    cur = self
    while (cur.firstChild): cur = cur.firstChild
    return cur

def getRightBranch(self:Node) -> Node:
    """Find the furthest node down if you always go right.
    """
    cur = self
    while (cur.lastChild): cur = cur.lastChild
    return cur

def selectFirstChild(self:Node, nodeSel:NodeSel=None) -> Node:
    # TODO: Unify nodeSel
    if (isLeafType(self)): return None
    for ch in self.childNodes:
        if (ch.nodeSel == nodeSel): return ch
        if (nodeSel=="*" and ch.nodeType==Node.ELEMENT_NODE): return ch
    return None

def selectLastChild(self:Node, nodeSel:NodeSel=None) -> Node:
    if (isLeafType(self)): return None
    for ch in reversed(self.childNodes):
        if (ch.nodeName == nodeSel): return ch
        if (nodeSel=="*" and ch.nodeType==Node.ELEMENT_NODE): return ch
    return None

def getNChildNodes(self:Node, nodeSel:NodeSel=None) -> int:
    """Return the number of children of the current node.
    @param nodeSel: If "*", count only elements; If an actual name,
    count only element of that name.
    """
    if (isLeafType(self)): return None
    if (not nodeSel): return len(self.childNodes)
    n = 0
    for ch in self.childNodes:
        if (nodeSel is None or
            (ch.nodeType == Node.ELEMENT_NODE and
             (nodeSel=='*' or nodeSel==ch.nodeName))): n += 1
    return n

def getChildNumber(self:Node, nodeSel:NodeSel=None) -> int:
    """Return the number of this node among its siblings, counting only
    siblings that match the given nodeSel (default: all).
    *** This counting is 1-based! ***
    @param nodeSel:
        None: count everything
        element type name: count only those
        "*": count all/only elements
        "#text", "#pi", "#comment": count only those.
        "#noncom": count all non-comment nodes (TODO: experimental)
    TODO: Should we care about non-coalesced text nodes?
    TODO: NodeSel option to count only non-whitespace-only text nodes?
    """
    n = 0
    for ch in self.parentNode.childNodes:
        if (nodeSel is None): n += 1
        elif (self.nodeMatches(nodeSel)): n += 1
        if (ch==self): return n
    return None

getMyIndex = getChildNumber  # TODO: Move under synonyms

def getDepth(self:Node) -> int:
    """How far down are we? Document element is 1.
    """
    d = 0
    cur = self
    while (cur):
        d = d + 1
        cur = cur.parentNode
    return d

def getFQGI(self:Node, sep:str="/", leaf:bool=False, levelMax:int=0,
    prefix:bool=True) -> Union[str, list]:
    """Return the sequence of element type names of all ancestors, in
    document order, separated by `sep`.
    If `sep` is falsish ("", None, etc), return a list, outermost first.
    If `leaf` is set, "#text", "#pi", etc. is included if applicable.
    if `levelMax` > 0, only that many levels are gathered (working upwards).
    If `prefix` is set to False, namespace prefixes are removed.
    """
    cur = self
    flist = []
    levelsDone = 0
    if (cur.nodeType != Node.ELEMENT_NODE):
        f = cur.nodeName  # Such as "#text", #document"
        if (f and leaf):
            flist.insert(0, f)
            levelsDone += 1
        cur = cur.parentNode
    while (cur and (levelMax==0 or levelMax>levelsDone)):
        nn = cur.nodeName
        if (not prefix): nn = re.sub(r"^[^:]*:", "", nn)
        flist.insert(0, nn)
        levelsDone += 1
        cur = cur.parentNode
    if (sep):
        return sep.join(flist)
    return flist

def isWithinType(self:Node, nodeSel:NodeSel) -> bool:
    """Test whether a node has an ancestor of a specified element type.
    You can do this equally well with selectAncestor().
    TODO: Rename to hasAncestor()?
    """
    cur = self
    while (cur):
        if (cur.nodeName == nodeSel): return True  # TODO Fix
        cur = cur.parentNode
    return False

# TODO: Patch onto __contains__?
def isWithin(self:Node, node:Node) -> bool:
    """Test whether some specific node is an ancestor of the given node.
    """
    cur = self.parentNode
    while (cur):
        if (cur == node): return True
        cur = cur.parentNode
    return False

isDescendantOf = isWithin

CONTENT_EMPTY = 0
#CONTENT_WSN = 1
CONTENT_TEXT = 2
#CONTENT_TEXT_WSN = 3
CONTENT_ELEMENT = 4
#CONTENT_ELEMENT_WSN = 5
CONTENT_MIXED = 6
#CONTENT_ELEMENT_TEXT_WSN = 7
CONTENT_ODD = 8

def getContentType(self) -> int:
    """Test whether this elements has text and/or element children. Returns one of:
        CONTENT_EMPTY   -- no child nodes
        CONTENT_TEXT    -- only TEXT child nodes
        CONTENT_ELEMENT -- only ELEMENT child nodes
        CONTENT_MIXED   -- mixed content (TEXT and ELEMENT child nodes)
        CONTENT_ODD     -- child nodes include non-TEXT, non-ELEMENT nodes
            (such as PI, COMMENT, CDATA)
    TODO: Perhaps CDATA should count as just text?
    TODO: Perhaps treat WSN as if absent?
    """
    nChildNodes = len(self.childNodes)
    if (nChildNodes == 0): return self.CONTENT_EMPTY
    eChilds = self.selectChild(n=0, nodeSel='*')
    tChilds = self.selectChild(n=0, nodeSel='#text')
    if (len(eChilds) == nChildNodes): return self.CONTENT_ELEMENT
    if (len(tChilds) == nChildNodes): return self.CONTENT_TEXT
    if (len(eChilds)+ len(tChilds) == nChildNodes): return self.CONTENT_MIXED
    return self.CONTENT_ODD


###############################################################################
# XPointer support
#
def getXPointer(self:Node, textOffset:int=None, idAttrName:NMToken=None) -> str:
    """Get a simple numeric XPointer to *either* an entire element or text
    node, or to a specific character inside some text node, unless there

    With `textOffset`, dig down and find the specified character (not byte!)
    among the descendants, and return a precise pointer there, unless
    there's not enough text -- then treat as if no `textOffset` was given.
    If it's exactly 1 greater, point just after the last content character.

    TODO: Extend to full-fledged ranges?
    """
    assert isinstance(self, Node)
    xp = getXPointerToNode(self, idAttrName=idAttrName)
    if (textOffset is None): return xp
    assert textOffset >= 0
    if (self.nodeType == Node.TEXT_NODE):  # Find the right text node
        if (textOffset >= 0 and textOffset <= len()): xp += "#%d" % (textOffset)
        return xp
    theTextNode, localOffset = findTextByOffset(self, textOffset=textOffset)
    xp = getXPointerToNode(theTextNode, idAttrName=idAttrName) + "#%d" % (localOffset)
    return xp

def getXPointerToNode(self:Node, idAttrName:NMToken="id", nodeSel:NodeSel=None) -> str:
    """Get a simple XPointer to a node (no specific character points!). These
    are just a sequence of child-numbers, e.g.  /1/12/352/4/1.
        ==> These count text nodes, too, unless you set "whatToCount" to some
        specific selector, such as "*" (for just elements).

    If `idAttrName` is not empty (it defaults to "id"), and that attribute
    is set on an ancestor(s), then the XPointer will use the innermost such value
    as the leading component and go no further up, e.g. myId/4/1.
    """
    f = ""
    cur = self
    while (cur and cur.nodeType != Node.DOCUMENT_NODE):
        idValue = cur.getAttribute(idAttrName) if idAttrName else ""
        if (idValue):
            return idValue + "/" + f
        f = str(getChildNumber(cur, nodeSel)+1) + "/" + f
        cur = cur.parentNode
    return "/" + f

def getXPathToNode(self:Node, idAttrName:NMToken="id",
    byType:bool=True, nodeSel:NodeSel=None) -> str:
    """Basically like getXPointerToNode(), but generates an XPath expression.
    The default (byType=True) counts each child among its own type (thus,
    the number will usually be quite different than "raw" numbers:
        /chap[1]/sec[6]/para[80]/note[2]/para[1]
    A slightly dumber form is with byType=False, and just uses element numbers:
        /*[1]/*[12]/*[352]/*[4]/*[1]
    Just as with getXPointerToNode, if you set idAttrName and a value is found
    for that attribute on the way up, traversal stops and that ID is used
    as the first component. For example, if you set idAttrName="id", and the
    upper para from the previous example has id="theRightValue", you get:
        //*[@id=theRightValue]/note[2]/para[1]
    """
    f = ""
    cur = self
    while (cur and cur.nodeType != Node.DOCUMENT_NODE):
        idValue = cur.getAttribute(idAttrName) if idAttrName else ""
        if (idValue):
            f = "//*[@%s='%s']/%s" % (idAttrName, idValue, f)
            break
        elif (byType):
            curName = cur.nodeName
            f = "%s[%d]/%s" % (curName, cur.getChildNumber(curName)+1, f)
        else:
            f = "*[%d]/%s" % (cur.getChildNumber(nodeSel)+1, f)
        cur = cur.parentNode
    return f

def findTextByOffset(self:Node, textOffset:int=0):
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

def getTextNodesIn(node:Node) -> list:
    """Return just the text nodes under the specified starting node.
    By default, includes descendant text nodes; should add option to
    only consider direct ones.
    See https://stackoverflow.com/questions/298750/
    TODO: Just use eachTextNode
    """
    textNodes = []
    if (node.nodeType == Node.TEXT_NODE):
        textNodes.append(node)
    else:
        for i in (range(len(node.childNodes))):
            textNodes.extend(node.getTextNodes(node.childNodes[i]))
    return textNodes

### Comparison operators for DOCUMENT ORDER
#
def __lt__(self, other):
    return (self.compareDocumentPosition(other) == Node.DOCPOS_CONTAINS or
           self.compareDocumentPosition(other) == Node.DOCPOS_PRECEDING)
def __le__(self, other):
    return (self is other or
        self.compareDocumentPosition(other) == Node.DOCPOS_CONTAINS or
        self.compareDocumentPosition(other) == Node.DOCPOS_PRECEDING)
def __eq__(self, other):
    return self is other
def __ge__(self, other):
    return (self is other or
        self.compareDocumentPosition(other) == Node.DOCPOS_CONTAINED_BY or
        self.compareDocumentPosition(other) == Node.DOCPOS_FOLLOWING)
def __gt__(self, other):
    return (self.compareDocumentPosition(other) == Node.DOCPOS_CONTAINED_BY or
           self.compareDocumentPosition(other) == Node.DOCPOS_FOLLOWING)

def  __contains__(self, other):
    return self.compareDocumentPosition(other) == Node.DOCPOS_CONTAINS

def sameAs(self, other) -> bool:
    """Test whether two nodes have the same tree, text, attrs.
    TODO: Worth adding a shallow version, or unordered, or options to
    ignore attrs,...?
    """
    if (self.nodeType != other.nodeType): return False
    if (self.nodeName != other.nodeName): return False
    if (self.nodeType != Node.ELEMENT_NODE): return (self.data == other.data)

    for a in self.attributes:
        if (self.getAttribute(a) != other.getAttribute(a)): return False
    for a in other.attribute:
        if (not self.hasAttribute(a)): return False

    nch1 = len(self.childNodes) if self.childNodes else 0
    nch2 = len(other.childNodes) if other.childNodes else 0
    if (nch1 != nch2): return False
    for i in range(nch1):
        if (not sameAs(self.childNodes[i], other.childNodes[i])): return False

    return True

def compareDocumentPositionViaXPointer(self:Node, other:Node):
    """Compare two nodes for order. Return same as compareDocumentPosition.
    """
    return self.compareXPointer(self.getXPointer(), other.getXPointer())

def compareXPointer(self:Node, xp1:str, xp2:str) -> int:
    """Compare two purely numeric XPointers for relative order.
    Does not support ones with IDs.
    """
    if (not re.match(r'(/\d+)+$', xp1)):
        raise ValueError("Invalid XPointer child sequence 1: '%s'." % (xp1))
    if (not re.match(r'(/\d+)+$', xp2)):
        raise ValueError("Invalid XPointer child sequence 2: '%s'." % (xp2))
    t1 = re.split(r'/', xp1)
    t2 = re.split(r'/', xp2)
    i = 0
    while (i<len(t1) and i<len(t2)):
        if (t1[i] < t2[i]): return Node.DOCPOS_PRECEDING
        if (t1[i] > t2[i]): return Node.DOCPOS_FOLLOWING
        i = i + 1
    # At least one of them ran out...
    c = cmp(len(t1), len(t2))
    if (c < 0): return Node.DOCPOS_CONTAINS
    elif (c > 0): return Node.DOCPOS_CONTAINED_BY
    else: return Node.DOCPOS_EQUAL

def interpretXPointer(self:Node, xp:str) -> Node:
    """Given an XPointer string, find the node (if it exists).
    """
    lg.info("interpretXPointer for '%s'.", xp)
    document = self.ownerDocument
    node = document.documentElement
    steps = re.split(r'/', xp)
    if (steps[0] == ""): del steps[0]
    if (not steps[0].isdigit()):  # Leading ID:
        node = document.getElementById(steps[0])
        lg.info("XPointer ID '%s' got node of type '%s'.",
            steps[0], node.nodeName if node else "[NONE]")
        if (not node):
            lg.error("Reference to nonexistent ID in XPointer: %s", xp)
            return None
        del steps[0]
    for i, step in enumerate(steps):
        childNum = int(step)
        lg.info("Trying XPointer step %d to #%d (from a %s).", i, childNum, node.nodeName)
        if (node.nodeType not in [ Node.ELEMENT_NODE, Node.DOCUMENT_NODE ]):
            lg.error("XPointer step %d (%s) from non-node in: %s", i, step, xp)
            return None
        nChildren = len(node.childNodes)
        if (childNum<=0 or childNum>nChildren):
            lg.error("XPointer step %d to #%d out of range (%d).", i, childNum, nChildren)
            return None
        node = node.childNodes[childNum-1]  # getChildAtIndex(step)
    return node


###############################################################################
# TODO UPDATE TO MATCH AJICSS.js
#
def nodeMatches(self:Node, nodeSel:NodeSel="*", attrs:Union[dict, re.Pattern]=None) -> bool:
    """Check if a node matches the supported selection constraints.
    Used by all the selectAXIS() methods.

    @param nodeSel is as for __getitem__, described under class NodeSelKind.
        (NOT integers in this case as opposed to for __getitem__).
        A literal nodeName for an element
        At attribute name, prefixed with "@"
        '*' (the default), to match any element, but no non-element
        '#text', '#pi', '#comment', or '#cdata'
        '#noncom' matches any non-comment node
        A compiled regex, which is matched against element names

    @param attrs: a dict of attribute name:value pairs, all of which must match.
    If the value for any attribute in the dict is truly None, then that
    attribute must *not* be on the element at all ('' does not match None!).
    If the value in the dict is an int/float/complex, the attribute
        value is cast to that, and if successful, compared numerically.
    If the value is passed as a compiled regex, it is matched against.

    TODO Support nodeTypes in sync w/ Javascript packages.
    TODO Perhaps allow matching against any token(s) of an attribute?
        (can do already with regex and \\b)
    TODO Case-ignorant compares
        (can do already with regex and \\L lor \\U)
    """
    nsm = self.nodeSelMatches(nodeSel)
    if (not nsm): return False

    if (not attrs): return True
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
            elif (ty == complex):
                try:
                    if (complex(attrVal) != tgtVal): return False
                except ValueError:
                    return False
            else:
                if (attrVal != tgtVal): return False
    return True

def nodeSelMatches(self, nodeSel:NodeSel) -> bool:
    """Evaluate whether the Node matches *just* the specified nodeSel args.
    """
    if (not nodeSel): return True
    nsk = NodeSelKind.getKind(nodeSel)
    if (nsk == NodeSelKind.ARG_NAME):
        return bool(self.nodeType == Node.ELEMENT_NODE and
                    self.nodeName == nodeSel)
    elif (nsk == NodeSelKind.ARG_REGEX):
        return (self.nodeType == Node.ELEMENT_NODE and
                re.search(nodeSel, self.nodeName))
    elif (nsk == NodeSelKind.ARG_ATTR):
        return (self.nodeType == Node.ATTRIBUTE_NODE and
                self.nodeName == nodeSel[1:])
    elif (nsk == NodeSelKind.ARG_STAR):
        return (self.nodeType == Node.ELEMENT_NODE)
    elif (nsk == NodeSelKind.ARG_TEXT):
        return (self.nodeType == Node.TEXT_NODE)
    elif (nsk == NodeSelKind.ARG_COMMENT):
        return (self.nodeType == Node.COMMENT_NODE)
    elif (nsk == NodeSelKind.ARG_NONCOM):
        return (self.nodeType != Node.COMMENT_NODE)
    elif (nsk == NodeSelKind.ARG_PI):
        return (self.nodeType == Node.PROCESSING_INSTRUCTION_NODE)
    elif (nsk == NodeSelKind.ARG_CDATA):
        return (self.nodeType == Node.CDATA_SECTION_NODE)
    else:
        raise KeyError("Unknown NodeSelKind %s" % (nodeSel))

####### Produce node syntax
#
def getStartTag(self:Node, sortAttributes:bool=False, discards:list=None,
    makeEmpty:bool=False) -> str:
    """Generate a start tag for the given element.
    @param sortAttributes: Put the attributes in alphabetical order,
        as for Canonical XML.
    @param discards: Don't include these attributes.
    """
    assertElement(self)
    # assert (not sortAttributes)
    anames = []
    if (self.attributes):
        for a, _v in (self.attributes.items()):
            if (discards and a in discards): continue
            anames.append(a)
        if (sortAttributes): anames = sorted(anames)

    buf = ""
    for a in (anames):
        buf += ' %s="%s"' % (a, self.getEscapedAttribute(a))
    return "<%s%s%s>" % (self.nodeName, buf, "/" if makeEmpty else "")

def getEndTag(self:Node, appendAttr:NMToken=None) -> str:
    """Generate a normal end tag for the given element.
    @param appendAttr: If set, and the given element has an attribute with
    this name, put that attribute as a comment following the end-tag. This
    can be handy to add @id for readability.
    """
    assertElement(self)
    buf = "</%s>" % (self.nodeName)
    if (appendAttr and self.getAttribute(appendAttr)):
        buf += '<!-- id="%s" -->' % (self.getAttribute(appendAttr))
    return buf

def getPI(self:Node) -> str:
    assert self.nodeType == Node.PROCESSING_INSTRUCTION_NODE
    return "<?%s %s?>" % (self.target, self.data)

def getComment(self:Node) -> str:
    assert self.nodeType == Node.COMMENT_NODE
    return "<!--%s -->" % (self.data)

####### Attributes
#
def getInheritedAttribute(self:Node, aname:NMToken) -> str:
    """Search upward to find an assignment to an attribute, and return the
    nearest non-empty one (or None if none is found).
    The search starts with the node itself.
    This is like the defined semantics of xml:lang.
    """
    cur = self
    while (cur):
        avalue = cur.getAttribute(aname)
        if (avalue is not None and avalue!=''): return avalue
        cur = cur.parentNode
    return None

def getEscapedAttribute(self:Node, aname:NMToken, quoteChar:str='"') -> str:
    """Retrieve the value of a named attribute, and return it after escaping
    any occurrences of the `quoteChar` (usually double quote).
    """
    avalue = self.getAttribute(aname)
    return XMLStrings.escapeAttribute(avalue, quoteChar='"')

def getCompoundAttribute(self:Node, name:NMToken, sep:str='#',
    keepMissing:bool=False) -> str:  ### Not DOM
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

__falseBooleanValues__ = [ "", "0", "F", "false" ]  # nil? #F? FALSE? False?

def getAttributeAs(
    self:Node,
    name:NMToken,
    typ:type,
    default:Any,
    nilOK:bool=False,
    split:bool=False
    ) -> Any:
    """Get the attribute, and cast/convert it to the specified type.
    If absent, or present as "" and 'nilOK' is set, return the default.
    If present but casting fails, raise ValueError (booleans are looser --
    any value in __falseBooleanValues__ is False, others True).
    If 'split', the attribute is stripped and split on whitespace,
        the pieces are cast to the given typ, and a list is returned.
    TODO: Should define and support NMTOKEN, NUMTOKEN, etc.
    TODO: add arg to specify True and False strings to accept for boolean?
    """
    val = self.getAttribute(name)
    if (val is None): return default
    if (val == "" and nilOK): return default
    if (not split):
        if (typ == bool):
            castVal = val.strip() not in __falseBooleanValues__
        else:
            castVal = typ(val)
        return castVal
    else:
        parts = re.split(XMLStrings._xmlSpaceExpr, val.strip())
        castVals = []
        for part in parts:
            if (typ == bool):
                castVal = part.strip() not in __falseBooleanValues__
            else:
                castVal = typ(part)
            castVals.append(castVal)
        return castVals

def getEscapedAttributeList(self:Node, sortAttributes:bool=False, quoteChar:str='"') -> str:
    """Assemble the entire attribute list, escaped as needed to write out as XML.
    TODO: At least for canonical XML, put namespace attrs first.
    """
    assertElement(self)
    assert quoteChar in "'\""

    buf = ""
    if (not (self)): return None
    alist = self.attributes
    if (not (alist)): return buf
    anames = alist.keys()
    if (sortAttributes): anames = sorted(anames)
    for aname in anames:
        avalue = self.getEscapedAttribute(aname, quoteChar=quoteChar)
        if (quoteChar == "'"): buf += "%s='%s'" % (aname, avalue)
        else: buf += ' %s="%s"' % (aname, avalue)
    return buf

####### Attribute token handlers

def addAttributeToken(self:Node, attrName:NMToken, token:str, duplicates:bool=False) -> bool:
    """Make sure the attribute includes the specified token.
    @return: True if it was actually add (that is, it wasn't there before).
    """
    assertElement(self)
    attrValue = self.getAttribute(attrName)
    if re.match(r"\b%s\b" % (token), attrValue): return False
    self.setAttribute(attrName, attrValue + token)
    return True

def removeAttributeToken(self:Node, attrName:NMToken, token:str) -> bool:
    """Delete an attribute value token if present.
    @return: True if it was actually there before being removed.
    """
    assertElement(self)
    attrValue = self.getAttribute(attrName)
    attrValue2 = re.sub(r"\b%s\b" % (token), "", attrValue)
    if (attrValue2 != attrValue):
        self.setAttribute(attrName, attrValue2)
        return True
    return False

def hasAttributeToken(self:Node, attrName:NMToken, token:str, ignoreCase:bool=False) -> bool:
    """Return whether the given attribute exists and contains a (space-separated)
    token matching 'token'.
    """
    assertElement(self)
    attrValue = self.getAttribute(attrName)
    return re.search(r"\b%s\b" % (token), attrValue, flags=re.I if ignoreCase else 0)

####### Global changes / Node removers

def removeWhiteSpaceNodes(self:Node) -> None:
    """Drop all text nodes that contain only whitespace characters.
    """
    # print "running removeWhiteSpaceNodesCB\n"
    eachNodeCB(self, callbackA=removeWhiteSpaceNodesCB, callbackB=None)

def removeWhiteSpaceNodesCB(self:Node) -> None:
    """This only deals with XML whitespace, not all Unicode.
    """
    if (self.nodeType != Node.TEXT_NODE): return
    t = self.data
    mat = re.search(XMLStrings._xmlSpaceOnlyRegex, t, "")
    if (mat): self.parentNode.removeChild(self)

# TODO Combine into removeNodesByKind

def removeNodesByTagName(self:Node, nodeName:NMToken) -> int:
    """TODO Change to use nodeSel?
    """
    nodes = self.getElementsByTagName(nodeName)
    ct = 0
    for node in nodes:
        node.parent.removeChild(node)
        ct += 1
    return ct

def removeNodesByNodeType(self:Node, nodeType:str) -> int:
    """Remove all nodes of a given nodeType, such as PIs, comments, namespace nodes....
    TODO: Not sure if this iteration is happy if deleting elements....
    """
    ct = 0
    for node in self.eachNode():
        if (node.nodeType != nodeType): continue
        node.parent.removeChild(node)
        ct += 1
    return ct


###############################################################################
#
def forceTagCase(root:Node, upper:bool=False, attributesToo:bool=False) -> None:
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

def normalizeAllSpace(self:Node):
    """Normalize space in all descendants.
    """
    eachNodeCB(self, callbackA=_normalizeAllSpaceCB, callbackB=None)

def _normalizeAllSpaceCB(self:Node):
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

def addElementSpaces(self:Node, exceptions:Iterable=None):
    """Add spaces around all elements *except* those in list 'exceptions'.
    This is useful because most elements entail word-boundaries (say, things
    CSS would consider display:block). But little elements may not: such as
    HTML b, i, etc., and TEI var, sic, corr, etc.
    """
    raise NOT_SUPPORTED_ERR("No addElementSpaces")

def isWSN(self:Node):
    """Return true if this is a white-space-only text node, or a null text node
    (minidom can have text nodes whose data is None).
    """
    if (self.nodeType != Node.TEXT_NODE): return False
    if (self.nodeValue is None): return True
    if (self.nodeValue.strip() == ""): return True
    return False

###############################################################################
# Node creation/insertion/mod methods.
# TODO: Let caller supply attribute, too.
#
def renameByTagName(root:Node, oldName:NMToken, newName:NMToken) -> None:
    """Change the name for all elements of a given element type name.
    """
    for t in root.getElementsByTagName(oldName):
        t.nodeName = newName

def insertPrecedingSibling(self:Node, newNode:Node) -> Node:
    self.parentNode.insertBefore(newNode, self)
    return newNode

def insertFollowingSibling(self:Node, newNode) -> Node:
    par = self.parentNode
    r = self.followingSibling()
    if (r): par.insertBefore(newNode, r)
    else: par.appendChild(newNode)
    return newNode

def createParent(self:Node, nodeName:NMToken) -> Node:
    """See also: groupSiblings(), below.
    """
    newNode = self.getOwnerDocument.createElement(nodeName)
    self.parentNode.replaceChild(newNode, self)
    newNode.appendChild(self)
    return newNode

def groupSiblings(self:Node, firstNode:Node, lastNode:Node, nodeName:NMToken) -> Node:
    """Take a block of one or more contiguous siblings and enclose them in a new
    intermediate parent node (which goes at the level they *used* to be at).
    See also: insertParent(), above.
    """
    if (not firstNode or not lastNode):
        raise ValueError(
            "Must supply firstNode and lastNode to groupSiblings().\n")
    oldParent1 = firstNode.parentNode
    oldParent2 = lastNode.parentNode
    if (not (oldParent1 == oldParent2)):
        raise ValueError(
            "groupSiblings: firstNode and lastNode are not siblings!\n")

    newNode = firstNode.getOwnerDocument().createElement(nodeName)
    oldParent1.insertChildBefore(newNode, firstNode)
    curNode = firstNode
    while (curNode):
        nextNode = curNode.followingSibling
        oldParent1.removeChild(curNode)
        newNode.appendChild(curNode)
        if (curNode == lastNode): break
        curNode = nextNode
    return newNode

def mergeWithFollowingSibling(self:Node) -> Node:
    """Following sibling goes away, but its children are appended to the node.
    """
    if (not (self)): return None
    sib = self.followingSibling
    if (not sib): return False
    while (sib.hasChildNodes()):
        cur = sib.removeChild(self.selectFirstChild())
        self.appendChild(cur)
    self.parentNode.removeChild(sib)
    return self

def mergeWithPrecedingSibling(self:Node) -> Node:
    """Preceding sibling goes away, but its children are appended to the node.
    """
    if (not (self)): return None
    sib = self.precedingSibling
    if (not sib): return False
    while (self.hasChildNodes()):
        cur = sib.selectLastChild()
        sib.removeChild(cur)
        self.insertBefore(cur, self.selectFirstChild())
    self.parentNode.removeChild(sib)
    return self

def promoteChildren(self:Node) -> Node:
    """Remove the given node itself, promoting all its children.
    Sometimes known as "unwrapping".
    See also: promoteChildrenByParentName().
    Returns the *last* of the former children.
    """
    if (isLeafType(self)): return None
    parent = self.parentNode
    cur = self.selectFirstChild()
    while (cur):
        self.removeChild(cur)
        parent.insertBefore(cur, self)
        cur = self.selectFirstChild()
    parent.removeChild(self)
    return cur

def removeParentsByName(self:Node, nodeName:NMToken) -> None:
    """Find all elements of a given element type, and remove them, leaving their
    descendants otherwise intact.
    """
    if (isLeafType(self)): return None
    for t in self.getElementsByTagName(nodeName):
        t.promoteChildren()

def moveChildToAttribute(self:Node, pname:NMToken,
    chname:NMToken, aname:NMToken, onDup:str="skip") -> int:
    """Within the subtree under `root`, check all elements named `pname` that
    have a child of type `chname`, and move the text content of that child onto
    attribute `aname` of the parent. The child element is deleted.

    Cases of interest:
        * What if the parent already has an `aname` attribute?
        * What if there's more than one child of that type?
        * What if the child has attributes of its own?
        * What if the child has subelements of its own?

    You can check that all cases in a given subtree lack these cases, by
    calling `findNonAttributable`.
    """
    if (isLeafType(self)): return 0
    nDone = 0
    for node in self.eachNode(pname):
        if (node.hasAttribute(aname)): continue
        chNodes = node.getChildNodes(chname)
        if (len(chNodes) != 1): continue
        ch = chNodes[0]
        attrs = ch.getsAttribute()
        if (attrs and len(attrs)>0): continue
        if (ch.getElements("*")): continue
        node.setAttribute(aname, innerText(ch))
        node.removeChild(ch)
        nDone += 1
    return nDone

def findNonAttributable(self:Node, pname:NMToken, chname:NMToken, aname:NMToken) -> Node:
    """Basically a dry run for `moveChildToAttribute`.
    @return The first node that can't have a child move up onto an attribute.
    """
    if (isLeafType(self)): return None
    for node in self.eachNode(pname):
        if (node.hasAttribute(aname)): return node
        chNodes = node.getChildNodes(chname)
        if (len(chNodes) != 1): return node
        ch = chNodes[0]
        attrs = ch.getsAttribute()
        if (attrs and len(attrs)>0): return node
        if (ch.getElements("*")): return node
    return None


###############################################################################
# Traversal / Generators for the various XPath axes.
#
# TODO: Add option to consider Unicode WSN, hard spaces, controls, etc.

# TODO: Add eachNodeByKind()?

# TODO: Generalize to ByKind
#
def getAllDescendants(root:Node, excludeTypes:list=None, includeTypes:list=None):
    """Get a list of all descendants of the given node, in document order.
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

def eachNodeCB(self:Node, callbackA:Callable=None, callbackB:Callable=None, depth:int=1):
    """Traverse a subtree given its root, and call separate callbacks before
    and after traversing each subtree. Callbacks might, for example,
    respectively generate the start- and end-tags for elements, and generate
    the text or data for other kinds of nodes.
    Attribute and namespace nodes are not visited.
    Callbacks are allowed to be None if not needed.
    If a callback returns True, stop traversing.
    """
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

def eachNode(self:Node, wsn:bool=True, attributeNodes:bool=True, depth:int=1) -> Node:
    """Generate all descendant nodes (see also eachTextNode, eachElement)
    @param wsn: If False, skip white-space-only nodes.
    @param attributeNodes: If False, skip attribute nodes.
    TODO: Upgrade this and similar, to use NodeKind/NodeSel.
    """
    yield self

    # TODO Check, this isn't quite how to iterate through attribute *nodes*
    if (attributeNodes and self.attributes):
        nAttrs = self.attributes.length
        for i in range(nAttrs):
            yield self.attributes.item(i)

    if (self.hasChildNodes()):
        for ch in self.childNodes:
            if (not wsn and ch.nodeType==Node.TEXT_NODE and
                self.nodeValue is not None and self.nodeValue.strip() == ''): continue
            for chEvent in eachNode(ch, depth=depth+1):
                yield chEvent
    return

def reversedEachNode(self:Node, wsn:bool=True, depth:int=1) -> Node:
    """Generate all descendant nodes in reverse order.
    @param wsn: If False, skip white-space-only nodes.
    Note: this *always* skips attribute nodes.
    """
    if (self.hasChildNodes()):
        for ch in reversed(self.childNodes):
            for chEvent in reversedEachNode(ch, wsn=wsn, depth=depth+1):
                yield chEvent
    if (self.nodeType != Node.TEXT_NODE
        or wsn or (self.nodeValue is not None and self.nodeValue.strip() != '')):
        yield self
    return

def eachTextNode(self:Node, wsn:bool=True, depth:int=1) -> Node:
    """Generate all descendant text nodes.
    @param wsn: If False, skip white-space-only nodes.
    """
    if (self.nodeType == Node.TEXT_NODE):
        if (wsn or self.nodeValue.strip() != ''):
            yield self
    if (self.hasChildNodes()):
        for ch in self.childNodes:
            for chEvent in eachTextNode(ch, depth+1):
                yield chEvent
    return

def eachElement(self:Node, etype:NMToken=None, depth:int=1) -> Element:
    """Generate all element node descendants, optionally limiting to one type.
    """
    if (self.nodeType==Node.ELEMENT_NODE):
        if (not etype or self.nodeName == etype): yield self
    if (self.hasChildNodes()):
        for ch in self.childNodes:
            for chEvent in eachElement(ch, etype=None, depth=depth+1):
                yield chEvent
    return

def eachAttribute(self:Node, etype:NMToken=None, aname:NMToken=None, depth:int=1) -> tuple:
    """Generate all attributes in a given subtree, optionally limiting to one
    attribute name and/or one element type.
    @return a 2-tuple of an element node, and the name of one of its attributes.
    TODO: Should this return attrNodes per se?
    """
    if (self.nodeType==Node.ELEMENT_NODE):
        if (not etype or self.nodeName == etype):
            if (aname):
                if (self.hasAttribute(aname)):
                    yield self, aname
            else:
                if (self.attributes):
                    for a, _v in self.attributes.items():
                        yield self, a
    if (self.hasChildNodes()):
        for ch in self.childNodes:
            for chNode, chAname in eachAttribute(ch, etype=None, depth=depth+1):
                yield chNode, chAname
    return

# TODO: eachComment, eachPI, eachCDATA? No, just add nodeKind args to above.
#
def generateNodes(self:Node) -> Node:
    """Traverse a subtree given its root, and yield the nodes preorder.
    """
    yield self
    for ch in self.childNodes:
        yield ch.generateNodes()
    return


###############################################################################
# A SAX interface directly to the DOM.
#
def generateSaxEvents(self:Node, handlers:dict=None):
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

def genSax(self:Node, handlers:dict):
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
def collectAllText(self:Node, delim:str=" ", depth:int=1) -> str:
    """Cat together all descendant text nodes, optionally with separators
    between. See also innerText(), collectAllXml().
    @param delim: What to put between the separate text nodes
    @param depth: Just tracks the recursion level.
    TODO Option to collect only *directly* contained textnodes?

    *** Might be nicer to be like BaseDom.py (nee RealDOM.py), and define
    tostring() separately for each subclass of Node.
    """
    if (not (self)): return ""
    textBuf = ""
    if (self.nodeType == Node.TEXT_NODE):
        dat = self.data
        if (dat):
            if (depth > 1): textBuf = delim + dat
            else: textBuf = dat
    elif (self.hasChildNodes()):
        for ch in self.childNodes:
            textBuf = textBuf + collectAllText(ch, delim, depth+1)
    return textBuf

def getTextLen(self:Node, includeWSN:bool=True) -> int:
    """Return the total length of all text node descendants of a node.
    This should be much faster than doing len(collectAllText), because
    it avoids all that string copying and catting.
    """
    if (not (self)):
        return 0
    if (self.nodeType == Node.TEXT_NODE):
        if (self.data): return 0
        if (not includeWSN and self.data.isspace()): return 0
        return len(self.data)
    if (self.hasChildNodes()):
        tot = 0
        for ch in self.childNodes:
            tot += getTextLen(ch)
        return tot
    return 0


###############################################################################
#
def collectAllXml2(self:Node,
    breakComments:bool=True,      # Break/indent before comments
    breakEnds:bool=True,          # Break before end tags
    breakPIs:bool=True,           # Break/indent before processing instructions
    breakStarts:bool=True,        # Break before start tags
    canonical:bool=False,         # Generate Canonical XML
    delim:str=" ",                # put between text nodes
    emitter:Callable=None,        # What Emitter object to use
    emptyForm:str="HTML",         # Which syntax to use for empty elements: HTML, XML, SGML, NONE
    indentString:str='    ',      # Repeat this to indent ("" not to)
    indentText:bool=False,        # Break/indent before text nodes
    lineBreak:str="\n",           # String to use for line-breaks
    quoteChar:str='"',            # For quoting attrs, etc.

    schemaInfo=None,              # Any schema-specific info (not yet used)
    sortAttributes:bool=False,    # Put attrs in alphabetical order
    strip:bool=False,             # Strip whitespace off text nodes?
    xmlDcl:bool=True,
    doctype:bool=True,
    normAttrs:bool=True,
    ) -> str:
    """Collect a subtree as WF XML, with appropriate escaping. Can also
    put a delimiter before each start-tag; if it contains '\n', then the
    XML will also be hierarchically indented. -color applies.

    @param emitter: An object that supports the API of 'Emitter' (see below).
    All results are sent to this object. Default: Emitter('STRING'),
    which concatenates everything into a string (other options include writing
    to a file or passing to a callback; or you can implement something else).

    Canonical includes these features, some of which can be set separately:
        oencoding:  UTF-8
        lineBreak:  \n
        normAttrs:  Attributes whitespace-normalized
                    No CDATA sections or unnecessary entities
        xmlDcl:     No XML declaration
        doctype:    No Doctype
        emptyForm:  Empty elements become start/end
        quoteChar:  Normalized whitespace outside the document element and inside tags
        sortAttributes:  Attributes are alphabetized
        quoteChar:  Attributes are double-quoted
                    No redundant namespace declarations
                    xml:base is cleaned up
    """
    if (emitter is None):
        emitter = Emitter("STRING")
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
        strip,
        xmlDcl,
        doctype,
        normAttrs,
        )
    self.collectAllXml2r(cOptions)
    return emitter.string

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
    'xmlDcl',
    'doctype',
    'normAttrs',
]
CollectorOptionsDef = namedtuple('CollectorOptions', CollectorOptionsNames)

def ind(cOptions, depth:int, name:NMToken="", isStart:bool=True, isEnd:bool=False) -> str:
    """Generate any needed linebreak + indentation. Should only be called
    for things that expect that (e.g., maybe not text).
    """
    pre = post = ""
    if (cOptions.schemaInfo):  # TODO: Finish
        si = cOptions.schemaInfo
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

def addArgsForCollectorOptions(parser, prefix:str="") -> None:
    for optName in CollectorOptionsNames:
        oname = "--%s%s" % (prefix, optName)
        if (optName in [ 'delim', 'indentString', 'lineBreak', 'emptyForm' ]):
            parser.add_argument(oname, type=str)
        else:
            parser.add_argument(oname, action='store_true')
    return

def collectAllXml2r(self:Node, cOptions, depth:int=1):
    """The recursive part of collectAllXml2().
    """
    #sys.stderr.write("%scollectAllXml22 on a %s.\n" % (" " * depth, type(self)))
    # Save the options
    # Calculate whitespace to put around the element
    name = self.nodeName
    ntype = self.nodeType

    em = cOptions.emitter

    #sys.stderr.write("Emitting nodeType %d, name %s\n" % (ntype, name))

    # Assemble the data and/or markup
    #
    if (ntype == Node.ELEMENT_NODE):                  # 1 ELEMENT
        textBuf = "%s<%s%s" % (ind(cOptions, depth, name=name),
            name, getEscapedAttributeList(self,
                sortAttributes=cOptions.sortAttributes,
                quoteChar=cOptions.quoteChar))
        if (len(self.childNodes) == 0): textBuf += " />"
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
        em.emit(buf + XMLStrings.escapeText(s))

    elif (ntype == Node.CDATA_SECTION_NODE):          # 4 CDATA
        buf = ""
        if (cOptions.indentText): buf = ind(cOptions, depth, "#cdata")
        em.emit(buf + "<![CDATA[%s]]>" % (XMLStrings.escapeCDATA(self.data)))
    elif (ntype == Node.ENTITY_REFERENCE_NODE):       # 5
        pass #nop = 1
    elif (ntype == Node.ENTITY_NODE):                 # 6
        pass #nop = 1
    elif (ntype == Node.PROCESSING_INSTRUCTION_NODE): # 7 PI
        buf = ""
        if (cOptions.breakPIs): buf = ind(cOptions, depth, "#pi")
        em.emit(buf + "<?%s %s?>" % (self.target, XMLStrings.escapePI(self.data)))

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

def collectAllXml(
    self:Node,                # Root of subtree to generate XML for
    delim:str="",             # Put before each start tag
    indentString:str='    ',  # Repeat to construct indentation
    schemaInfo=None,          # Something to put ahead of the fragment
    lineBreak:str="\n",       # Linebreak to use (or '')
    depth:int=1
    ) -> str:
    """Collect a subtree as WF XML, with appropriate escaping. Can also
    put a delimiter before each start-tag; if it contains '\n', then the
    XML will also be hierarchically indented. -color applies.
    """
    name = self.nodeName
    ntype = self.nodeType

    # Calculate whitespace to put around the element
    if (indentString): istr = (indentString * depth)
    else: istr = delim

    # Assemble the data and/or markup
    textBuf = ""
    if (ntype == Node.ELEMENT_NODE):                  # 1 ELEMENT:
        attlist = getEscapedAttributeList(self, sortAttributes=False, quoteChar='"')
        textBuf += lineBreak + self + "<" + name + attlist
        if (len(self.childNodes) == 0):
            textBuf += "/>"
        else:
            textBuf += ">"
            for ch in self.childNodes:
                textBuf += ch.collectAllXml(delim=delim, lineBreak=lineBreak, depth=depth+1)
            textBuf += "</" + name + ">" + lineBreak
    elif (ntype == Node.ATTRIBUTE_NODE):              # 2 ATTR
        raise ValueError("Why are we seeing an attribute node?")
    elif (ntype == Node.TEXT_NODE):                   # 3 TEXT
        textBuf += XMLStrings.escapeText(self.data)
    elif (ntype == Node.CDATA_SECTION_NODE):          # 4 CDATA
        textBuf += XMLStrings.escapeText(self.data)
    elif (ntype == Node.ENTITY_REFERENCE_NODE):       # 5 ENTITY REF (deprecated)
        pass
    elif (ntype == Node.ENTITY_NODE):                 # 6 ENTITY
        pass
    elif (ntype == Node.PROCESSING_INSTRUCTION_NODE): # 7 PI
        textBuf += "<?" + self.target + " " + self.data + "?>"
    elif (ntype == Node.COMMENT_NODE):                # 8 COMMENT
        textBuf = textBuf + istr + "<!--" + self.data + "-->"
        if (indentString): textBuf += lineBreak
    elif (ntype == Node.DOCUMENT_NODE):               # 9
        pass
    elif (ntype == Node.DOCUMENT_TYPE_NODE):          # 10
        textBuf += "<!DOCTYPE %s>" % (self.nodeName) + lineBreak
    elif (ntype == Node.DOCUMENT_FRAGMENT_NODE):      # 11
        pass
    elif (ntype == Node.NOTATION_NODE):               # 12  (deprecated)
        pass
    else:
        raise ValueError("startCB: Bad DOM node type returned: %d" % ntype)

    return textBuf
# collectAllXml


###############################################################################
#
fhGlobal = None  # TODO Unglobalize this, probably via partial functions.

# TODO Unify with collectAllXml
def export(
    self:Node,
    someElement:Element,
    fh:IO,
    includeXmlDecl:bool=True,
    includeDoctype:bool=False
    ) -> None:
    """Write the whole thing to some file.
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
    elif (typ == Node.TEXT_NODE):                    # 3
        buf = self.data
    elif (typ == Node.CDATA_SECTION_NODE):           # 4
        buf = "<![CDATA["
    elif (typ == Node.PROCESSING_INSTRUCTION_NODE):  # 7
        buf = "<?%s %s?>" % (self.target, XMLStrings.escapePI(self.data))
    #elif (typ == Node.DOCUMENT_TYPE_NODE):           # 10
    #    buf = "<!DOCTYPE>"
    else:
        pass
    fhGlobal.write(buf)

def endCB(self:Node):
    buf = ""
    typ = self.nodeType
    if (typ == Node.ELEMENT_NODE):                   # 1:
        buf = "</" + self.nodeName + ">"
    elif (typ == Node.CDATA_SECTION_NODE):           # 4
        buf = "]]>"
    else:
        pass
    fhGlobal.write(buf)

# END of DomExtensions definitions


###############################################################################
# Various places to put output data.
#
class Emitter:
    """Used by collectallXml, etc. to transmit data to any of several targets.
    This allows the same code to write to a file, a buffer, or whatever.
    """
    def __init__(self, where:str, arg:str=None):
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

    def emit(self, text:str) -> None:
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

    def lastCharEmitted(self) -> str:
        return self.lastChar


###############################################################################
#
class DomIndex(dict):
    """Index on an attribute.
    Adds every element Node that has a given attribute, to a hash keyed on that
    attribute's value (the values are thus lists).
    @param unique: If set, duplicates raise IndexError (as you might want for IDs).
    """
    def __init__(self, docOrNode:Node, aname:NMToken, unique:bool=False):
        """Scan a document (or at least a subtree) and build a dict of the
        values found for a given attribute.
        @param document: Document or subtree head Node to scan.
        @param aname: Name of attribute to be indexed.
        @param duplicates: If True, just replace when there's a duplicate.
        TODO: Option to save list in case of duplicates.
        """
        super(DomIndex, self).__init__()

        if (docOrNode.nodeType == Node.DOCUMENT_NODE):
            self.document = docOrNode
            self.rootNode = docOrNode.documentElement
        else:
            self.document = docOrNode.ownerDocument
            self.rootNode = docOrNode.ownerDocument.documentElement

        self.attrName = aname
        node = self.rootNode
        finalNode = node.rightBranch
        while (node):
            if (node.nodeType==Node.ELEMENT_NODE):
                key = node.getAttribute(aname)
                if (not key): continue
                if (key not in self): self[key] = [ node ]
                elif (not unique): self[key].append(node)
                else: raise IndexError("Duplicate key '%s'." % (key))
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
    def string(node:Node) -> str:
        raise NOT_SUPPORTED_ERR

    @staticmethod
    def strings(node:Node) -> str:
        """Generate the series of all text node descendants as strings.
        """
        for node in getAllDescendants(node, includeTypes=[ Node.TEXT_NODE ]):
            yield node.data

    @staticmethod
    def stripped_strings(node:Node, normSpace:bool=False, allUnicode:bool=False) -> str:
        """Generate the series of all text node descendants as strings,
        but with leading and trailing space stripped. Also, skip any text
        nodes that are white-space-only.
        TODO: Probably should also have an option to normalize internal space,
        and perhaps Unicode as well as XML whitespace.
        """
        for node in getAllDescendants(node, includeTypes=[ Node.TEXT_NODE ]):
            if (normSpace):
                ss = XMLStrings.normalizeSpace(node.data, allUnicode=allUnicode)
            else:
                ss = XMLStrings.stripSpace(node.data, allUnicode=allUnicode)
            if (ss): yield ss

    @staticmethod
    def find_all(node:Node, name:NMToken, attrs:dict=None, recursive:bool=True, string=None,
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
    def BSfind_matcher(node:Node, name:NMToken, attrs:dict=None,
        string=None, class_=None, **kwargs):
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
    def find(node:Node, **kwargs):
        """ Syntactic sugar.
        """
        return BS4Features.find_all(node, limit=1, **kwargs)

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
    """More Pythonic than just constants as in generic DOM. For example,
    you can use nodeType.name to get the string name, like "ELEMENT_NODE",
    and they're actually a type so you can test membership.
    """
    NO_NODE                     = 0  # Added non-associating value.
    ELEMENT_NODE                = 1
    ATTRIBUTE_NODE              = 2
    TEXT_NODE                   = 3
    CDATA_SECTION_NODE          = 4
    ENTITY_REFERENCE_NODE       = 5  # Removed in DOM4.
    ENTITY_NODE                 = 6  # Removed in DOM4.
    PROCESSING_INSTRUCTION_NODE = 7
    COMMENT_NODE                = 8
    DOCUMENT_NODE               = 9
    DOCUMENT_TYPE_NODE          = 10
    DOCUMENT_FRAGMENT_NODE      = 11
    NOTATION_NODE               = 12 # Removed in DOM4.

    @staticmethod
    def fromint(n:int):
        """Map an int nodeType to the enum.
        """
        try:
            return NodeTypes(n)
        except ValueError:
            return NodeTypes.NO_NODE

    @staticmethod
    def isCore(node:Node) -> bool:
        """Return True iff this node is element, text, or cdata.
        """
        nt = NodeTypes.fromint(node.nodeType)
        return (nt in
            [ NodeTypes.ELEMENT_NODE,
              NodeTypes.TEXT_NODE, NodeTypes.CDATA_SECTION_NODE ])

    @staticmethod
    def nameOfNodeType(x:Union[Node, int]):
        """Takes either a node or a nodeType int. Return the string name
        for the nodeType.
        """
        if (isinstance(x, Node)): x = x.nodeType
        nt = NodeTypes(x)
        return nt.name


###############################################################################
#
class DomExtensions:
    def __init__(self):
        self.DE = 1

    @staticmethod
    def enableBrackets(toPatch=Node) -> None:
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
        toPatch.__contains__ = containsKind

    @staticmethod
    def patchDOM(classes=None, getItem:bool=True) -> None:
        """Some people capitalize acronyms.
        @param classes: Pass either a class, or a list of them (or default).
        """
        DomExtensions.patchDom(classes=classes, getItem=getItem)

    @staticmethod
    def patchDom(
        classes=None,             # What class(es) to monkey-patch
        getItem:bool=True,        # Include the __getitem__ mod?
        axisSelects:bool=True,    # Include axis selectors?
        synonyms:bool=False,      # preceding/previous, following/next
        xptr:bool=True,           # XPointer and compareDocumentPosition
        namedNodeMap:bool=True    # Make NNM more like Python iterables.
        ) -> None:
        """Monkey-patch the extension methods into a given class.
        See also patchDomAuto(), following.
        """
        if (not classes):
            classes = [ Node, Document, Element ]
        elif (not isinstance(classes, list)):
            classes = [ classes ]
        lg.info("====To patch: ")
        for toPatch in classes:
            lg.warning("*** Patching class %s ***\n", toPatch)
            testCase = getattr(toPatch, "selectAncestor", None)
            if (testCase and callable(testCase)): return

            if (getItem):
                toPatch.__getItem__ = DEgetitem
                toPatch.__contains__ = containsKind

            if (namedNodeMap):
                DomExtensions.patchNamedNodeMap()

            toPatch.nameOfNodeType          = NodeTypes.nameOfNodeType

            toPatch.outerHTML               = outerHTML
            toPatch.innerHTML               = innerHTML
            toPatch.outerXML                = outerXML
            toPatch.innerXML                = innerXML
            toPatch.innerText               = innerText

            if (axisSelects):
                # SELF
                toPatch.selectSelf              = selectSelf

                # ANCESTOR, A-O-S, CHILD, DESC
                toPatch.selectAncestor          = selectAncestor
                toPatch.selectAncestorOrSelf    = selectAncestorOrSelf
                toPatch.selectChild             = selectChild
                toPatch.selectDescendant        = selectDescendant
                #toPatch.selectDescendantR       = selectDescendantR

                # PRECEDING, FOLLOWING
                toPatch.selectPreceding         = selectPreceding
                toPatch.getPreceding            = getPreceding
                toPatch.selectPrevious          = selectPreceding
                toPatch.getPrecedingAbsolute    = getPrecedingAbsolute
                toPatch.selectFollowing         = selectFollowing
                toPatch.getFollowing            = getFollowing
                toPatch.getFollowingAbsolute    = getFollowingAbsolute

                # SIBLINGS
                toPatch.selectPrecedingSibling  = selectPrecedingSibling
                toPatch.getPrecedingSibling     = getPrecedingSibling
                toPatch.selectFollowingSibling  = selectFollowingSibling
                toPatch.getFollowingSibling     = getFollowingSibling

                if (synonyms):
                    toPatch.getPrevious             = getPreceding
                    toPatch.previous                = getPreceding
                    toPatch.selectNext              = selectFollowing
                    toPatch.getNext                 = getFollowing
                    toPatch.next                    = getFollowing
                    toPatch.selectPreviousSibling   = selectPrecedingSibling
                    toPatch.getPreviousSibling      = getPrecedingSibling
                    toPatch.selectNextSibling       = selectFollowingSibling
                    toPatch.getNextSibling          = getFollowingSibling
                    toPatch.tostring                = toPatch.toString  # More Pythonic

            toPatch.getLeastCommonAncestor  = getLeastCommonAncestor
            toPatch.getLeftBranch           = getLeftBranch
            toPatch.getRightBranch          = getRightBranch
            toPatch.selectFirstChild        = selectFirstChild
            toPatch.selectLastChild         = selectLastChild
            toPatch.getNChildNodes          = getNChildNodes
            toPatch.getChildNumber          = getChildNumber
            toPatch.getDepth                = getDepth
            toPatch.getMyIndex              = getMyIndex
            toPatch.getFQGI                 = getFQGI

            # Positional
            toPatch.isWithinType            = isWithinType
            toPatch.isDescendantOf          = isDescendantOf
            toPatch.isWithin                = isWithin
            toPatch.getContentType          = getContentType

            cmpMethod = getattr(toPatch, "compareDocumentPosition", None)
            if (not cmpMethod):
                toPatch.compareDocumentPosition = compareDocumentPositionViaXPointer
                toPatch.DOCPOS_DISCONNECTED = 1
                toPatch.DOCPOS_PRECEDING    = 2
                toPatch.DOCPOS_FOLLOWING    = 4
                toPatch.DOCPOS_CONTAINS     = 8
                toPatch.DOCPOS_CONTAINED_BY = 16
                toPatch.DOCPOS_IMPLEMENTATION_SPECIFIC = 32
                # TODO: Add iteratively from Enum DOCUMENT_POSITIONS (above)
            toPatch.sameAs                  = sameAs

            toPatch.compareDocumentPositionViaXPointer = compareDocumentPositionViaXPointer
            # XPointer, XPath, etc.
            if (xptr):
                toPatch.getXPointer         = getXPointer
                toPatch.findTextByOffset    = findTextByOffset
                toPatch.getXPointerToNode   = getXPointerToNode
                toPatch.getXPathToNode      = getXPathToNode
                toPatch.compareXPointer     = compareXPointer
                toPatch.interpretXPointer   = interpretXPointer

            toPatch.nodeMatches             = nodeMatches
            toPatch.nodeSelMatches          = nodeSelMatches

            # Produce node syntax
            toPatch.getStartTag             = getStartTag
            toPatch.getEndTag               = getEndTag
            toPatch.getPI                   = getPI
            toPatch.getComment              = getComment

            # Attributes
            toPatch.getInheritedAttribute   = getInheritedAttribute
            toPatch.getEscapedAttribute     = getEscapedAttribute
            toPatch.getCompoundAttribute    = getCompoundAttribute
            toPatch.getAttributeAs          = getAttributeAs

            toPatch.getEscapedAttributeList = getEscapedAttributeList
            toPatch.addAttributeToken       = addAttributeToken
            toPatch.removeAttributeToken    = removeAttributeToken
            toPatch.hasAttributeToken       = hasAttributeToken

            # Global changes / Node removers
            toPatch.removeWhiteSpaceNodes   = removeWhiteSpaceNodes
            toPatch.removeNodesByTagName    = removeNodesByTagName
            toPatch.removeNodesByNodeType   = removeNodesByNodeType
            toPatch.removeParentsByName     = removeParentsByName
            toPatch.renameByTagName         = renameByTagName
            toPatch.forceTagCase            = forceTagCase

            # TABLES (support moved to be in DOMTableTools.py)

            toPatch.normalizeAllSpace       = normalizeAllSpace
            toPatch.normalize               = normalize

            # Local tree changes
            toPatch.insertPrecedingSibling  = insertPrecedingSibling
            toPatch.insertFollowingSibling  = insertFollowingSibling
            toPatch.createParent            = createParent
            toPatch.mergeWithFollowingSibling = mergeWithFollowingSibling
            toPatch.mergeWithPrecedingSibling = mergeWithPrecedingSibling
            toPatch.groupSiblings           = groupSiblings
            toPatch.promoteChildren         = promoteChildren
            toPatch.moveChildToAttribute    = moveChildToAttribute
            toPatch.findNonAttributable     = findNonAttributable

            # Traversal / Generators for the various XPath axes
            toPatch.getAllDescendants       = getAllDescendants
            toPatch.eachNodeCB              = eachNodeCB
            toPatch.eachNode                = eachNode
            toPatch.reversedEachNode        = reversedEachNode
            toPatch.eachTextNode            = eachTextNode
            toPatch.eachElement             = eachElement
            toPatch.eachAttribute           = eachAttribute
            toPatch.generateNodes           = generateNodes
            toPatch.generateSaxEvents       = generateSaxEvents

            # Collect/export
            toPatch.collectAllText          = collectAllText
            toPatch.getTextLen              = getTextLen

            # getTextNodesIn
            toPatch.collectAllXml2          = collectAllXml2
            toPatch.collectAllXml2r         = collectAllXml2r
            toPatch.collectAllXml           = collectAllXml
            toPatch.export                  = export

            # Escaping and other string-only functions are not patched in.

            DomExtensions.checkPatch(toPatch)
        return

    @staticmethod
    def patchNamedNodeMap() -> None:
        # ? NamedNodeMap.__iteritems__ = NNM_iteritems
        NamedNodeMap.__getitem__ = NNM_getitem

    @staticmethod
    def patchDomAuto(
        toPatch=Node,
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
            toPatch.__contains__ = containsKind

        toPatchDir = dir(toPatch)
        nAdded = 0
        de = DomExtensions()
        for k in dir(de):
            try:
                v = getattr(de, k)
                if (not axisSelects and v.startswith("select")): continue
                if (excludes and v in excludes): continue
                if (not callable(v)): continue
                if (k in toPatchDir): print("******* Overriding '%s'." % (k))
                toPatch.setAttr(k, v)
                nAdded += 1
            except AttributeError:
                print(" %-30s  *** FAILED ***" % (k))
        return nAdded

    @staticmethod
    def checkPatch(classes=None) -> int:
        """Make sure we didn't miss adding anybody.
        @return Number of errors.
        """
        if (not classes): classes = [ Node ]
        elif (isinstance(classes, type)): classes = [ classes ]
        nFails = 0
        #sys.stderr.write("checkPatch: 'classes' is %s\n" % (type(classes)))
        if (isinstance(classes, Iterable)):
            for toPatch in classes:
                nFails += DomExtensions.checkPatchForOne(toPatch)
        else:
            nFails += DomExtensions.checkPatchForOne(classes)
        return nFails

    @staticmethod
    def checkPatchForOne(toPatch) -> int:
        sys.stderr.write("checkPatch: Checking '%s' (%s)\n" %
            (toPatch.__name__, type(toPatch)))
        inPatch = toPatch.__dict__.keys()
        nMissing = 0
        for k, v in DomExtensions.__dict__.items():
            if (not callable(v)): continue
            if (k.startswith("__") or k.startswith("patch")): continue
            if (k in inPatch): continue
            sys.stderr.write("checkPatch: Did not get into patch: '%s'.\n" % (k))
            nMissing += 1
        return nMissing


###############################################################################
# Test driver
#
if __name__ == "__main__":
    import argparse

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
            "--showMethods", action='store_true',
            help='Display a list of the methods defined.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files', type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return args0

    ###########################################################################
    #
    args = processOptions()

    if (args.showMethods):
        from subprocess import check_output
        buf0 = str(check_output([ "grep", "-E", "^(class| *def )", __file__ ]))
        print(re.sub(r"\\n", "\n", buf0))
        sys.exit()

    lg.info("Patching extensions onto xml.dom.minidom.Node...")
    DomExtensions.patchDOM()
    # Of course it doesn't have the method, until we've patched it in....
    if (callable(Node.getDepth)):
        lg.info("Patch succeeded.")
    else:
        lg.info("Patch failed.")
    #pylint: enable=E1101

    if (len(args.files) == 0):
        tfileName = "testDoc.xml"
        lg.warning("No files specified, trying %s.", tfileName)
        args.files.append(tfileName)

    for path0 in args.files:
        fh0 = codecs.open(path0, "rb", encoding="utf-8")
        theDOM = xml.dom.minidom.parse(fh0)
        fh0.close()
        theDoc = theDOM.renameByTagName('p', 'para')

    lg.info("Done.")
