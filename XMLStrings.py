#!/usr/bin/env python3
#
# DomExtensions: A bunch of (hopefully) useful additions to the DOM API.
# 2010-01-10: Written by Steven J. DeRose.
#
#pylint: disable=W0613, W0212, E1101
#
import re
from typing import Union, Match, Dict

from xml.dom.minidom import Node
from html.entities import codepoint2name, name2codepoint

import logging
lg = logging.getLogger("DomExtensions.py")
lg.setLevel(logging.INFO)

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
Test that patched nodes end up working ok.

*** Profile

Allow callable for first arg to __getitem__, which is a filter: takes
a node, returns a bit.

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

####### TODO: Unify with sjdUtils/XML/Dominus/XMLStrings!

class XMLStrings:
    """This class contains static methods and variables for basic XML
    operations such as testing syntax forms, escaping strings, etc.
    """
    _xmlSpaceExpr = r"[ \t\n\r]+"

    _xmlSpaceChars = " \t\r\n"
    _xmlSpaceRegex = f"[{_xmlSpaceChars}]+"
    _xmlSpaceOnlyRegex = re.compile("^[%s]*$" % (_xmlSpaceChars))

    # This excludes colon (":"), since we want to distinguish QNames.
    _nameStartChar = (r"_A-Za-z" +
        "\u00C0-\u00D6" + "\u00D8-\u00F6" + "\u00F8-\u02FF" +
        "\u0370-\u037D" + "\u037F-\u1FFF" + "\u200C-\u200D" +
        "\u2070-\u218F" + "\u2C00-\u2FEF" + "\u3001-\uD7FF" +
        "\uF900-\uFDCF" + "\uFDF0-\uFFFD")
        #"\U00010000-\U000EFFFF")
    _nameChar = "-.0-9\u00B7\u0300-\u036F\u203F-\u2040" + _nameStartChar

    _xmlName  = r"^[%s][%s]*$" % (_nameStartChar, _nameChar)
    _xmlQName = r"^(%s(:%s)?$" % (_xmlName, _xmlName)
    _xmlPName = r"^(%s)(:%s)$" % (_xmlName, _xmlName)
    _xmlNmtoken = r"^[%s]+$" % (_nameChar)

    @staticmethod
    def isXmlName(s:str) -> bool:
        """Return True for a NON-namespace-prefixed (aka) local name.
        """
        return bool(re.match(XMLStrings._xmlName, s, re.UNICODE))

    @staticmethod
    def isXmlQName(s:str) -> bool:
        """Return True for a namespace-prefixed OR unprefixed name.
        """
        parts = s.partition(":")
        if (parts[2] and not XMLStrings.isXmlName(parts[2])): return False
        return XMLStrings.isXmlName(parts[0])
        #if (re.match(XMLStrings._xmlQName, s, re.UNICODE)): return True
        #return False

    @staticmethod
    def isXmlPName(s:str) -> bool:
        """Return True only for a namespace-prefixed name.
        """
        parts = s.partition(":")
        return XMLStrings.isXmlName(parts[0]) and XMLStrings.isXmlName(parts[2])
        #if (re.match(XMLStrings._xmlPName, s, re.UNICODE)): return True
        #return False

    @staticmethod
    def isXmlNmtoken(s:str) -> bool:
        return bool(re.match(XMLStrings._xmlNmtoken, s, re.UNICODE))

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
    def escapeComment(s:str, replaceWith:str="-&#x2d;") -> str:
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
        s = s.replace('?>', replaceWith)
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
        assert isinstance(s, str)
        return re.sub(r'&(#[xX]?)?(\w+);', XMLStrings.unescapeXmlFunction, s)

    @staticmethod
    def unescapeXmlFunction(mat:Match) -> str:
        """Convert HTML entities and numeric character references to literal chars.
        """
        if (mat.group(1) is None):
            if (mat.group(2) in name2codepoint):
                return chr(name2codepoint[mat.group(2)])
            raise ValueError("Unrecognized entity name: '%s'." % (mat.group(2)))
        if (len(mat.group(1)) == 2):
            return chr(int(mat.group(2), 16))
        else:
            return chr(int(mat.group(2), 10))

    @staticmethod
    def normalizeSpace(s:str, allUnicode:bool=False) -> str:
        """By default, this only normalizes *XML* whitespace,
        per the XML spec, section 2.3, grammar rule 3.

        NOTE: Most methods of removing Unicode whitespace in Python do not work
        for Unicode. See https://stackoverflow.com/questions/1832893/

        U+200B ZERO WIDTH SPACE is left untouched below.
        """
        if (allUnicode):
            s = re.sub(r"\s+", " ", s, flags=re.UNICODE)
        else:
            s = re.sub(XMLStrings._xmlSpaceRegex, " ", s)
        s = s.strip(" ")
        return s

    @staticmethod
    def stripSpace(s:str, allUnicode:bool=False) -> str:
        """Remove leading and trailing space, but don't touch internal.
        """
        if (allUnicode):
            s = re.sub(r'^\s+|\s+$', "", s, flags=re.UNICODE)
        else:
            s = s.strip(XMLStrings._xmlSpaceChars)
        return s

    @staticmethod
    def makeStartTag(gi:str, attrs:Union[str, Dict]="",
        empty:bool=False, sort:bool=False) -> str:
        tag = "<" + gi
        if (attrs):
            if (isinstance(attrs, str)):
                tag += " " + attrs.strip()
            else:
                tag += XMLStrings.dictToAttrs(attrs, sortAttributes=sort)
        tag += "/>" if empty else ">"
        return tag

    @staticmethod
    def dictToAttrs(dct, sortAttributes: bool=None, normValues: bool=False) -> str:
        """Turn a dict into a serialized attribute list (possibly sorted
        and/or space-normalized). Escape as needed.
        """
        sep = " "
        anames = dct.keys()
        if (sortAttributes): anames.sort()
        attrString = ""
        for a in (anames):
            v = dct[a]
            if (normValues): v = XMLStrings.normalizeSpace(v)
            attrString += f"{sep}{a}=\"{XMLStrings.escapeAttribute(v)}\""
        return attrString

    @staticmethod
    def makeEndTag(node:'Node') -> str:
        return f"</{node.nodeName}>"

    @staticmethod
    def getLocalPart(s:str) -> str:
        #if (not s): return ""
        #return re.sub(r'^.*:', '', s)
        return s.partition(":")[2] or s  # Wow is this faster.

    @staticmethod
    def getNSPart(s:str) -> str:
        #if (not s): return ""
        return s.partition(":")[0] or s
