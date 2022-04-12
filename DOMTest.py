#!/usr/bin/env python3
#
# DOMTest.py: Test harness for DOMExtensions, DOMgetitem, etc.
# 2022-02-02: Written by Steven J. DeRose.
#
#pylint: disable=W0511,W0612,W0613
#
import re
#import os
#import codecs
#import string
#import math
#import subprocess
#from collections import defaultdict, namedtuple
#from typing import IO, Dict, List, Union
import logging
lg = logging.getLogger("main")
from xml.dom import minidom
#from xml.dom.minidom import Document, Node, Element

from DomExtensions import DomExtensions as de
from DomExtensions import XMLStrings, NodeSelKind
from DomExtensions import NodeSelKind as nsk
from DomExtensions import NodeTypes

__metadata__ = {
    "title"        : "DOMTest",
    "description"  : "Test harness for DOMExtensions, DOMgetitem, etc.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2022-02-02",
    "modified"     : "2022-02-02",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

==Usage==

    DomTest.py [options] [files]

Test a DOM implementation, especially my extensions such as:
    * DomExtensions.py
    * pydom
    * domTables


=Related Commands=


=Known bugs and Limitations=

Far from complete.

=To do=


=History=

* 2022-02-02: Written by Steven J. DeRose.


=Rights=

Copyright 2022-02-02 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
# Some sample data
#
sampleDoc = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.5//EN"
"http://www.oasis-open.org/docbook/xml/4.5/docbookx.dtd">
<book xmlns:foo="http://example.com/namespaces/foo"
      xmlns:e="http://example.com/namespaces/e"
      id="theBook">
  <bookinfo>
    <title>My Title</title>
  </bookinfo>

  <chapter id="chap1" class="important">
    <foo:title>Introduction</foo:title>
    <section>
      <title><i>What?</i> Section 1, on <i>Entities</i> with a 2nd text node!</title>
      <p>Hello, paragraph 1.</p>
      <p>Hello, paragraph 2.</p>
      <p>Hello, paragraph <i>3</i>.</p>
      <p>Character references can be &#x68;exadecimal, &#100;ecimal, or named &lt;</p>
      <p>Nested <b> and/or <empty/> <i>elements</i></b> can happen, too.</p>
      <p><![CDATA[ Marked <sections> can contain literal pointies & stuff.]]></p>
    </section>
  </chapter>
  <!-- a comment - with a hyphen - and a >, too. -->
  <?piTarget foo="bar" eggs="spam"?>
  <chapter id="chap2" class="not so important">
    <foo:title>The Basics</foo:title>
    <p id="attrs"
        a="1"
        b="2"
        _c12="3"
        dir="4"
        e:earth="round"
    >Attributes of interest:</p>
  </chapter>

  <chapter id="chap3" class="_tableStuff">
    <foo:title>The Basics</foo:title>
    <p>Creatures of interest:</p>
    <ul id="ul1">
      <li>Aardvark</li>
      <li>Basilisk</li>
      <li>Catoblepas</li>
      <li>Dryad</li>
      <li>Echidna</li>
      <li>Fafnir</li>
      <li>Grendel</li>
      <li>Hydra</li>
      <li>Itcuintlipotzotli </li>
      <li>Jackelope</li>
    </ul>
  </chapter>
</book>
"""

USpaces = {
    # Unicode   width    name
    0x00009:  ( 1.00,    "CHARACTER TABULATION"),
    0x0000A:  ( 0.00,    "LINE FEED"),
    0x0000B:  ( 1.00,    "LINE TABULATION"),
    0x0000C:  ( 0.00,    "FORM FEED"),
    0x0000D:  ( 0.00,    "CARRIAGE RETURN"),
    0x00020:  ( 1.00,    "SPACE"),
    0x00089:  ( 1.00,    "CHARACTER TABULATION WITH JUSTIFICATION"),
    0x01680:  ( 1.00,    "OGHAM SPACE MARK"),
    0x0180E:  ( 1.00,    "MONGOLIAN VOWEL SEPARATOR"),
    0x02000:  ( 0.50,    "EN QUAD"),
    0x02001:  ( 1.00,    "EM QUAD"),
    0x02002:  ( 0.50,    "EN SPACE"),
    0x02003:  ( 1.00,    "EM SPACE"),
    0x02004:  ( 0.33,    "THREE-PER-EM SPACE"),
    0x02005:  ( 0.25,    "FOUR-PER-EM SPACE"),
    0x02006:  ( 0.17,    "SIX-PER-EM SPACE"),
    0x02007:  ( 1.00,    "FIGURE SPACE"),
    0x02008:  ( 1.00,    "PUNCTUATION SPACE"),
    0x02009:  ( 0.00,    "THIN SPACE"),
    0x0200A:  ( 0.10,    "HAIR SPACE"),
    0x02028:  ( 0.00,    "LINE SEPARATOR"),
    0x02029:  ( 0.00,    "PARAGRAPH SEPARATOR"),
    0x0200B:  ( 0.00,    "ZERO WIDTH SPACE"),
    0x0202F:  ( 0.10,    "NARROW NO-BREAK SPACE"),
    0x0205F:  ( 1.00,    "MEDIUM MATHEMATICAL SPACE"),
    0x02060:  ( 1.00,    "WORD JOINER"),
    0x03000:  ( 1.00,    "IDEOGRAPHIC SPACE"),
    0x0303F:  ( 1.00,    "IDEOGRAPHIC HALF FILL SPACE"),

    # These aren't really a "space"....
    #0x000A0:  ( 1.00,    "NO-BREAK SPACE"),
    #0x02420:  ( 1.00, "",   "SYMBOL FOR SPACE"),
    #0x0FEFF:  ( 0.00, "",   "ZERO WIDTH NO-BREAK SPACE (aka BOM)"),
}
USpacesStr = "".join(chr(c) for c in USpaces.keys())


###############################################################################
# Test one document
#
def m(label, msg):
    print("%-30s %s" % (label, msg))

def fail(msg):
    print("Test failed: %s" % (msg))

def test_driver(fh=None):
    if (fh is None):
        dom = minidom.parseString(sampleDoc)
    else:
        dom = minidom.parse(fh)
    doc = dom.documentElement

    #x = subtest_meta(doc)
    x = subtest_xml_strings(doc)
    x = subtest_getItem(doc)
    x = subtest_serialization(doc)
    x = subtest_collectors(doc)

    #x = subtest_selectors(doc)
    #x = subtest_cSS(doc)
    #x = subtest_bS4(doc)
    #x = subtest_xPointer(doc)
    x = subtest_treeGeometry(doc)
    x = subtest_comparisons(doc)
    x = subtest_attributes(doc)
    #x = subtest_treeEditing(doc)
    #x = subtest_tables(doc)


###############################################################################
# Meta
#
def subtest_meta(doc):
    nErrors = 0
    # x = enableBrackets(toPatch=Node)
    de.patchDOM()
    # x = patchNamedNodeMap()
    # x = patchDomAuto(
    assert de.checkPatch() == 0
    return nErrors


###############################################################################
# Basic constructs like strings, tokens, escaping. Things that don't actually
# need a DOM document or node, but just work on strings.
# Mostly, these are staticmethods in DomExtensions.XMLStrings.
#
def subtest_xml_strings(dom):
    nErrors = 0
    x = [
        #            NM QN PN  NUM NodeSelArg
        ( "A",        1, 1, 0,  0,  1),
        ( "_",        1, 1, 0,  0,  1),
        ( ".foo.bar", 0, 0, 0,  0,  0),
        ( "_yup",     1, 1, 0,  0,  1),
        ( ":nope",    0, 0, 0,  0,  0),
        ( "div3",     1, 1, 0,  0,  1),
        ( "div.3-_b", 1, 1, 0,  0,  1),
        ( "#text",    0, 0, 0,  0,  1),
        ( "#foo",     0, 0, 0,  0,  0),
        ( "123",      0, 0, 0,  1,  0),
        ( "0",        0, 0, 0,  1,  0),
        ( "-1",       0, 0, 0,  0,  0),
        ( "+1",       0, 0, 0,  0,  0),
        ( "1.0",      0, 0, 0,  0,  0),
        ( ":",        0, 0, 0,  0,  0),
        ( "foo-bar_baz.12:a1",
                      0, 1, 1,  0,  1),
        ( "html:li",  0, 1, 1,  0,  1),
    ]
    for s, isName, isQName, isPName, isNUM, isNSA in x:
        try:
            assert isName == XMLStrings.isXmlName(s)
            assert isQName == XMLStrings.isXmlQName(s)
            assert isPName == XMLStrings.isXmlPName(s)
            assert isNSA == (NodeSelKind.getKind(s) is not None) # allows initial [#@] and "*"
            assert isNUM == XMLStrings.isXmlNumber(s)
        except (AssertionError, ValueError):
            print("Failed for candidate name '%s'." % (s))
            raise

    for i in range(13):
        m("Node type %d" % (i), NodeTypes(i))

    # Categorizing arugments to selectors
    #               INT NAME ATTR STAR   #X   RE
    x = [
        ( '12',       1,   0,   0,   0,   0,   0 ),
        ( 'a',        0,   1,   0,   0,   0,   0 ),
        ( '@class',   0,   0,   1,   0,   0,   0 ),
        ( '*',        0,   0,   0,   1,   0,   0 ),
        ( '#text',    0,   0,   0,   0,   1,   0 ),
        ( re.compile("^.*$"),
                      0,   0,   0,   0,   0,   1 ),
    ]
    for s, isInt, isName, isAttr, isStar, isReserved, isRegex in x:
        sKind = nsk.getKind(s)
        assert isInt      == bool(sKind == nsk.ARG_INT)
        assert isName     == bool(sKind == nsk.ARG_NAME)
        assert isAttr     == bool(sKind == nsk.ARG_ATTR)
        assert isStar     == bool(sKind == nsk.ARG_STAR)
        assert isReserved == bool(sKind in
            [ nsk.ARG_COMMENT, nsk.ARG_TEXT, nsk.ARG_PI, nsk.ARG_CDATA ])
        assert isRegex    == bool(sKind == nsk.ARG_REGEX)

    # On strings
    # TODO: options for ZML escaping, hex/dec/name entities, width, maybe TEX? Ents
    # TODO: escaping ]]> could be done in a lot of ways....
    assert (XMLStrings.escapeAttribute("""hello 'ew' "ahh" <foo>""", quoteChar='"') ==
        """hello 'ew' &quot;ahh&quot; &lt;foo>""")
    assert (XMLStrings.escapeAttribute("""hello 'ew' "ahh" <foo>""", quoteChar="'") ==
        """hello &apos;ew&apos; "ahh" &lt;foo>""")

    s = "hello <world> &noEnt; <?tgt foo?> <!--comment--> &#65; ]]> phew"
    assert (XMLStrings.escapeText(s) ==
        "hello &lt;world> &amp;noEnt; &lt;?tgt foo?> &lt;!--comment--> ]]&gt; &amp;#65;phew")
    assert (XMLStrings.escapeText(s, escapeAllGT=True) ==
        "hello &lt;world&gt; &amp;noEnt; &lt;?tgt foo?&gt; &lt;!--comment--&gt; ]]&gt; phew")
    assert (XMLStrings.escapeCDATA(s) ==
        "hello <world> &noEnt; <?tgt foo?> <!--comment--> ]]&gt; phew")
    assert (XMLStrings.escapeComment(s, replaceWith="-&#x2d;") ==
        "hello <world> &noEnt; <?tgt foo?> <!-&#x2d;comment-&#x2d;> ]]> phew")
    assert (XMLStrings.escapePI(s, replaceWith="?&gt;") ==
        "hello <world> &noEnt; <?tgt foo?&gt <!--comment--> ]]>; phew")

    s = "alpha \u03b1 nbsp \xA0 sharp-s \xdf pilcrow \xB6 rpilcrow \u204B end"
    assert (XMLStrings.escapeASCII(s, width=4, base=16, htmlNames=True) ==
        "alpha &#x03b1; nbsp &#x00A0; sharp-s &#x00df; pilcrow &#x00B6; rpilcrow &#x204B; end")
    assert (XMLStrings.escapeASCII(s, base=10, htmlNames=False) ==
        "alpha \u03b1 nbsp \xA0 sharp-s \xdf pilcrow \xB6 rpilcrow \u204B end")

    # Check handling of prohibited C0 characters
    bad = ""
    ok = ""
    for i in range(32):
        if (i in [ 9, 10, 13 ]): continue  # These are ok
        bad += "and \\x%02x" % (i)
        ok += "and "
    assert (XMLStrings.nukeNonXmlChars(bad) == ok)
    ents = "decimal &#64; and &#00000000065; and &#x43; and &#X0000044; and &#969; &#x3c9; &omega;"
    lits = "decimal A and B and C and D and \u03c9; \u03c9; \u03c9;"
    assert (XMLStrings.unescapeXml(ents) == lits)

    s = USpacesStr
    assert (XMLStrings.normalizeSpace(s, allUnicode=True) == "")
    assert (XMLStrings.stripSpace(s, allUnicode=True) == "")

    return nErrors


###############################################################################
# getItem
#
def subtest_getItem(doc):
    nErrors = 0
    ul = doc.getElementById("ul1")

    alpha = ".ABCDEFGHIJ"

    # Positive child numbers
    for n in range(1, 11):
        ch = ul[n]
        if (not ch.textContent.startsWith(alpha[n])):
            fail("Child %d has textContent '%s'." % (n, ch.textContent))
        cnum = ch.getCNum()
        if (cnum != n):
            fail("Child %d has cnum %d." % (n, cnum))
        xp = ch.createXPointer()
        ch2 = doc.interpretXPointer(xp)
        if (ch != ch2):
            fail("Child %d xpointer didn't round-trip ('%s')." % (n, xp))

    # Negative child numbers
    for n in range(1, 11):
        ch = ul[-n]
        if (not ch.textContent.startsWith(alpha[-n])):
            fail("(negative) Child %d has textContent '%s'." % (n, ch.textContent))

    # Attributes
    el = doc.getElementById("attrs")
    for aname in el.attributes:
        assert el.getAttribute(aname) == el["@"+aname]
    # TODO: x["@foo", 3]!!
    # TODO: x["#pi", 3]!!

    # PI, comment, etc.
    bk = doc.getElementById("theBook")
    pis = bk["#pi"]
    assert len(pis) == 1
    coms = bk["#comment"]
    assert len(coms) == 1
    elems = bk["*"]
    assert len(elems) == 5
    texts = bk["#text"]
    assert len(texts) == 5

    # x = DEgetitem(self:Node, n1, n2=None, n3=None)
    # x = DEcontains(self:Node, nodeName:NMTokenPlus)

    # x = _getChildNodesByName_(self:Node, nodeKind:NMTokenPlus)
    # x = _getListItemsByName_(self:Node, theList:list, nodeKind:NMTokenPlus)
    return nErrors


###############################################################################
# Serialization, whitespace
#
def subtest_serialization(doc):
    nErrors = 0

    ul = doc.getElementById("ul1")
    el = doc.getElementById("attrs")

    assert (el.getStartTag(sortAttributes=True, discards=None) ==
        'p id="attrs" a="1" b="2" _c12="3" dir="4" e:earth="round"')
    assert (el.getEndTag(appendAttr=None) == "</p>")
    assert (el.getEndTag(appendAttr="dir") == '</p>>!-- dir="4" -->')

    # TODO: Are these even needed?
    assert (doc.getPI() == "")
    assert (doc.getComment(doc) == "")

    assert (el.getEscapedAttributeList(sortAttributes=False, quoteChar="'") ==
        "id='attrs' a='1' b='2' _c12='3' dir='4' e:earth='round'")

    el.setAttribute("class", "red blue")
    assert el.hasAttribute("class")
    assert el.getAttribute("class") == "red blue"
    el.addAttributeToken("class", "green", duplicates=False)
    assert el.getAttribute("class") == "red blue green"
    el.addAttributeToken("class", "green", duplicates=False)
    assert el.getAttribute("class") == "red blue green"
    # TODO What should happen if the addition is multi-token?

    assert (doc.normalizeAllSpace() == "")
    assert (doc.normalize() == "")
    # TODO: Review
    assert (doc.addElementSpaces(exceptions=None) == "")

    return nErrors


###############################################################################
# Selectors: Axis
#
def subtest_selectors(doc):
    nErrors = 0

    home = doc.getElementById("home")
    # x = home.selectSelf(n=0, nodeName="")
    # x = home.selectAncestor(n=0, nodeName="")
    # x = home.selectAncestorOrSelf(n=0, nodeName="")
    # x = home.selectChild(n=0, nodeName="")
    # x = home.selectDescendantOrSelf(n=0, nodeName="")
    # x = home.selectDescendant(n=0, nodeName="")
    # x = home.selectDescendantR(n=0, nodeName="")
    # x = home.selectPreceding(n=0, nodeName="")
    # x = home.getPreceding(doc)
    # x = home.getPrecedingAbsolute(doc)
    # x = home.selectFollowing(n=0, nodeName="")
    # x = home.getFollowing(doc)
    # x = home.getFollowingAbsolute(doc)
    # x = home.selectPrecedingSibling(n=0, nodeName="")
    # x = home.selectFollowingSibling(n=0, nodeName="")
    # x = home.getPrecedingSibling(doc)
    # x = home.precedingSibling(doc)
    # x = home.selectPreviousSibling(**w)
    # x = home.getFollowingSibling(doc)
    # x = home.followingSibling(doc)
    # x = home.selectNextSibling(**w)

    # x = home.nodeMatches(nodeKind="*")
    return nErrors


###############################################################################
# Collectors and iterators
#
def subtest_collectors(doc):
    nErrors = 0

    # TODO: Nuke the inner/outer HTML calls.
    # x = outerHTML(doc, indent="    ", breakEndTags=False)
    # x = innerHTML(doc, cOptions=None, indent="    ", breakEndTags=False, depth=0)
    # x = outerXML(doc, cOptions=None)
    # x = innerXML(doc, cOptions=None)
    # TODO: Nuke innerText in favor of textContent? Except what about sep?
    # x = innerText(doc, sep='')

    # TODO: Nuke the pre/post callbacks???
    # x = eachNodeCB(doc, callbackA=None, callbackB=None, depth=1)
    # x = eachNode(doc, wsn=True, attributeNodes=True, depth=1)

    # TODO: Generalize to each(nodeChoice); keep these as shorthand"
    # x = reversedEachNode(doc, wsn=True, depth=1)
    # x = eachTextNode(doc, wsn=True, depth=1)
    # x = eachElement(doc, etype=None, depth=1)
    # x = eachAttribute(doc, etype=None, aname=None, depth=1)

    # TODO: Review
    # x = generateNodes(doc)

    # x = collectAllText(doc, delim=" ", depth=1)
    # x = getTextNodesIn(node)  # TODO: drop?
    # x = collectAllXml2(doc,...)
    # x = collectAllXml2r(doc, cOptions, depth=1)
    # x = collectAllXml()
    # x = export()
    return nErrors


###############################################################################
# Selectors: CSS-like
#
def subtest_CSS(doc):
    nErrors = 0
    return nErrors


###############################################################################
# Selectors: BS4-like
#
def subtest_BS4(doc):
    nErrors = 0
    return nErrors


###############################################################################
# Selectors: XPointer
#
def subtest_XPointer(doc):
    nErrors = 0

    # x = getXPointerToNode(doc, idAttrName="id")
    # x = getXPointer(doc, textOffset=None)
    # TODO: support comparison w/o document if no IDs, or IDs equal?
    # x = XPointerCompare(doc, xp1, xp2)
    # x = XPointerInterpret(doc,  xp)
    # x = __init__(self, where, arg=None)
    # x = emit(self, text)
    # x = lastCharEmitted(self)
    # x = __init__(self, docOrNode, aname, duplicates=False)
    # x = string(node)
    # x = strings(node)
    # x = stripped_strings(node, normSpace=False, allUnicode=False)
    # x = find_all(node, name, attrs=None, recursive=True, string=None,
    # x = BSfind_matcher(node, name, attrs=None, string=None, class_=None, **kwargs)
    # x = find(node, **kwargs)
    # x = CssSelect(node)
    # x = select_one(node)
    # x = fromint(n)
    # x = isCore(node)
    return nErrors


###############################################################################
# SAX i/o
#
def subtest_SAX(doc):
    nErrors = 0
    # x = generateSaxEvents(doc, handlers=None)
    # x = genSax(doc, handlers):

    # TODO SAX_to_DOM
    return nErrors


###############################################################################
# Tree geometry
#
def subtest_treeGeometry(doc):
    nErrors = 0

    # x = getLeastCommonAncestor(doc, other)
    # x = getLeftBranch(doc)
    # x = getRightBranch(doc)
    # x = getFirstChild(doc, nodeName=None)
    # x = getLastChild(doc, nodeName=None)
    # x = getNChildNodes(doc, nodeKind=None)
    # x = getChildNumber(doc, nodeKind=None)
    # x = getDepth(doc)
    # x = getFQGI(doc, sep="/")
    return nErrors


###############################################################################
# subtest_s and comparisons
#
def subtest_comparisons(doc):
    nErrors = 0

    # x = isWithinType(doc, nodeName)
    # x = isWithin(doc, node)
    # x = getContentType(self)
    # x = findTextByOffset(doc, textOffset=0)
    # x = compareDocumentPosition(doc, other)
    return nErrors


###############################################################################
# Attribute handling
#
def subtest_attributes(doc):
    nErrors = 0

    # x = NNM_iteritems(self)
    # x = NNM_getitem(self, which)

    # x = getInheritedAttribute(doc, aname)
    # x = getEscapedAttribute(doc, aname, quoteChar='"')
    # x = getCompoundAttribute(doc, name, sep='#', keepMissing=False)
    # x = getAttributeAs(
    # x = removeAttributeToken(doc, attrName, token)
    return nErrors


###############################################################################
# Tree editing
#
def subtest_treeEditing(doc):
    nErrors = 0

    # x = removeWhiteSpaceNodes(doc)
    # x = removeWhiteSpaceNodesCB(doc)

    # TODO Unify with the selector mech
    # x = removeNodesByTagName(doc, nodeName)
    # x = removeNodesByNodeType(doc, nodeType)
    # x = untagNodesByTagName(root, nodeName)

    # x = renameByTagName(root, oldName, newName)
    # x = forceTagCase(root, upper=False, attribusubtest_oo=False)

    # TODO Unify with the selector mech
    # x = getAllDescendants(root, excludeTypes=None, includeTypes=None)

    # x = insertPrecedingSibling(doc, node)
    # x = insertFollowingSibling(doc, node)
    # x = insertParent(doc, nodeName)

    # x = mergeWithFollowingSibling(doc, cur)
    # x = mergeWithPrecedingSibling(doc, cur)
    # x = groupSiblings(doc, first, breakNode, newParentType)
    # x = promoteChildren(doc)
    # x = moveChildToAttribute(root, pname, chname, aname, onDup="skip")
    # x = findNonAttributable(root, pname, chname, aname)

    #
    return nErrors


###############################################################################
# Table stuff
#
def subtest_tables(doc):
    nErrors = 0

    # x = getColumn(doc, onlyChild="tbody", colNum=1, colSpanAttr=None)
    # x = getCellOfRow(doc, colNum=1, colSpanAttr=None)
    # x = transpose(doc)
    # x = eliminateSpans(doc, rowSpanAttr="rowspan", colSpanAttr="colspan")
    # x = hasSubTable(doc, tableTag="table")
    #isNormal hasRowSpan hasColSpan nameColumns
    #toMarkDown to JSON fromMarkDown fromJSON toLaTEX
    return nErrors


###############################################################################
# Stuff to add / to do
#
"""
    * split DomExtensions into multiple files
    * add unit subtest_s

    * Finish the table stuff
    * factor the basic selection model throughout (incl regex)
    * move into pre/foll sib (or general target)
    * create nodes much more easily (cf XmlOutput)
        ** element(gi, {attrs}
    * finish rest of negative indexes for selects
    * wrap/unwrap
    * sort/uniq/case attr tokens; cast to set/list.
    * sexp parser for attributes? produce Node subtree handing off attr?
    * support namespace prefixes for ids
    * canonical output
    * range support
    * switch between <x y=z> and <z>, or similar
    * notion of before/start/end/after
    * Add divs given Hn; rank hn/title from div. rank/unrank divs

    * write pydom
        ** Node is a subclass of list
        ** childnodes is just a list of nodes
        ** nodeType is an Enum
        ** attributes are just a dict
        ** order via <=>
        ** del/ins slice/splice/len for nodes
        ** cast attrs by type
        ** supply all xpath axes
        ** classes that go away: namednodemap text->str?, pi, comment, cdata
"""


###############################################################################
# Main
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
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()

    test_driver()


