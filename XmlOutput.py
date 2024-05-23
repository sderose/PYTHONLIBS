#!/usr/bin/env python3
#
# XmlOutput.py: Make it easier to write out WF XML.
# Perl original written 2010-12-22 by Steven J. DeRose.
# Port to Python: 2012-01-10 sjd.
#
# Allow the PY2 compatibility block below:
#pylint: disable=E0401, E0602
#
import sys
import re
import codecs
import string
#import xml

from typing import IO, Dict, Union
from html.entities import codepoint2name
#from html.parser import HTMLParser

PY2 = sys.version_info[0]

__metadata__ = {
    "title"        : "XmlOutput",
    "description"  : "Make it easier to write out WF XML.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2012-01-10",
    "modified"     : "2021-07-20",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Notes=

A Python module to help with generating XML output.
This library lets you issue open and close commands (and many others),
generating the corresponding XML output as you go.
It keeps the output element and xml:lang stacks and some other state
information, handles escaping automatically for all syntactic contexts,
and generally tries to
ensure the output is well-formed XML. It can also make an XML-generating
application more readable by encapsulating a lot of mechanical tasks (such as
checking whether certain elements are current open; adjusting DIVs to get
up or down to a desired level; close all open instances of a given element type(s),
and so on.

==Example==

  from XmlOutput import XmlOutput
  x = XmlOutput()
  xo.setOption("indent", True)
  xo.setOption("breakETAGO", False)
  xo.startDocument("html", systemID="html4.dtd")
  xo.openElements([ "html", "head", "title" ])
  makeText("RFC file: " + f)
  xo.closeThroughElement("head")
  xo.openElement("body")
  xo.openElement("p", 'id="foo"')
  xo.makeText("Hello, world.")
  xo.endDocument()

Attributes can be passed to openElement() and its kin as a full string,
a Python dict, or even be queued ahead of time to be issued on whatever
element is opened next.

The encoding (see '''setOutput'''()) defaults to `utf-8`.
To just get stack maintenance and error-checking, but not to produce
actual output, set `xo.outputFH` to None.

To output to a string, use Python's built-in `StringIO` package.

==Testing==

Run a self-test by just invoking the file from the command-line.


=Methods=

* ''__init__''(encoding="utf-8")

Create a new instance of the XmlOutput object. The output character
encoding can be set here, or on '''setOutput'''() (see below).


==Option and information set/get methods==

* ''getVersion''()

Return the version date of the module.

* ''getOption(name)''

Return the current value of option '''name''' (see following).

* ''setOption(name, value)''

Set option '''name''' to '''value'''.
The name is checked for being a known option, but no
checking is done on the value (values are Boolean unless otherwise noted).

** ''ASCIIOnly'' -- Use entities for all non-ASCII content characters.
** ''breakSTAGO'' -- Break before start-tags. Default True.
** ''breakAttrs'' -- Break before each attribute. Default False.
** ''breakSTAGC'' -- Break after start-tags. Default False.
** ''breakETAGO'' -- Break before end-tags. Default False.
** ''breakETAGC'' -- Break after end-tags. Default True.
** ''divTag'' -- what element type is used for nested containers,
like (the default) HTML `div`. See method '''adjustToRank''' for a handy
way to ensure that these get handled right even if the source document
only has headings (`Hn` or similar).
There is presently no special support for numbered `div`s such as found
in many other schemas (div1, div2, ...).
** ''escapeHREFs'' -- Apply %xx escaping to all attributes that appear
to be URIs. That is, ones that match r'(https?|mailto|ftp|local)://'.
Default False. See also '''escapeURI'''(s), which this uses, but can also
be called directly.
** ''escapeText'' -- Escape "<", "&", and "]]>" in text. Default True.
No, it is not necessary to escape ">" or "]" in general.
** ''fixNames'' -- Correct any requested element type names to be
valid XML NAMEs. Default False.
** ''HTMLEntities'' -- Use HTML entities for special
characters when possible. This requires that the F<HTMLparser> library
be installed.
** ''htmlFormat'' -- Do not issue XML-style empty elements. Default False.
** ''idAttrName'' -- Specify an attribute name to treat as an XML ID
(mainly for use with '''trackIDs'''. Default `id`. There is, sadly, no support
here for identifying IDs via DTD or XSD declarations.
** ''indent'' -- Pretty-print the XML output. See also '''iString'''.
Default True.
** ''iri'' -- Allow non-ASCII characters in URIs. Default True.
** ''iString'' -- Use this string as the (repeated) indent-string
for pretty-printing. Default `    ` (4 spaces).
** ''normalizeText'' -- Normalize white-space in output text nodes.
See also '''normalizeTag'''().
** ''encoding'' -- Write output in this character encoding.
** ''suppressWSN'' -- Do not output white-space-only text nodes.
** ''sysgenPrefix'' -- Set what string is prefixed to a serial number
with the '''sysgen'''() call.
** ''trackIDs'' -- (unsupported) Warn if an ID attribute value is
re-used (this does not see any DTD, it just goes by attribute name).
See also '''idAttrName'''.
** ''URIchars'' -- What characters are allowed (unescaped) in URIs.
If the '''iri''' option is set, all non-ASCII characters are also allowed.
Default: "-.\\w\\d_!\\'()*+"

* ''setCantRecurse(types)''

Prevent any element type listed (space-separated) in '''types'''
from being opened recursively.
For example, if this is set for `p` and the open elements
are html/body/div/p/footnote/, attempting to open another `p`, will close
elements until there are no `p` elements left open, after which
the new `p` is opened (in this example, 2 elements would thus be closed).

* ''setSpace(types, n)''

Cause '''n''' extra newlines to be issued before the start of each instance
of any element type in '''types''' (which can be either a list of individual names,
 or a string containing white-space-separated names).
The newlines will only be generated if an element also has '''breakSTAGO'''
set, and if it has not been set be `inline` (via '''setInline'''().

* ''setInline(types)''

Add each (space-separated) element type in '''types''' to a list of elements
to be treated as inline (thus getting no breaks around it despite
general options for breaking).

If '''types''' is "#HTML", the HTML 4 inline tags are added to the list:
A ABBR ACRONYM B BASEFONT BDO BIG BR CITE CODE DFN
EM FONT I IMG INPUT KBD LABEL Q S SAMP SELECT SMALL
SPAN STRIKE STRONG SUB SUP TEXTAREA TT U VAR.
Some other tags are only sometimes inline
(APPLET BUTTON DEL IFRAME INS MAP OBJECT SCRIPT).
These are not added by #HTML,
but some or all can be added with another call to '''setInline'''().

* ''setEmpty(types)''

Cause any element type listed (space-separated) in '''types''' to always be
written out as an empty element when opened (thus, no '''closeElement'''() call
is needed for them).

* ''setSuppress(types)''

Record that elements of any type listed (space-separated) in '''types'''
(and their entire subtrees) should not be output.
Not to be confused with the '''suppressWSN''' option.

* ''getCurrentElementName''()

Return the element type name of the innermost open element.

* ''getCurrentFQGI''()

Return the sequence of the types of all open elements, from the top down.
For example, `html/body/div/div/ul/li/p/i`.

* ''getCurrentLanguage''()

Return the present (possibly inherited) value of `xml:lang`. The language
is set by issuing an actual `xml:lang` attribute.

* ''getDepth''()

Return how many elements are presently open.


==XML attribute creation methods==

* ''queueAttribute(name, value)''

Add an attribute, to be issued with the next start-tag.
If an attribute called '''named''' is already queued, replace it.

* ''getQueuedAttributes''()

Return all queued attributes (if any) as an attribute string.
They are not cleared. This is typically only called internally.

* ''clearQueuedAttributes() ''

Discard any queued attributes. This happens automatically when they are
issued, for example via an '''openElement()''' call.

* ''dictToAttrs(dct, sortAttrs=False, normValues=False)''

This is used by `openElement` etc., if they are passed attributes
as a Python dict rather than an attribute string. It turns the dict
into a string attribute list. The values are escaped as needed (there is no
provision for telling it '''not''' to escape them), and assembled with a
single space before each attribute (even the first!), no spaces around "=",
and double quotes around the values. If '''sortAttrs''' is True,
the attributes are concatenated in alphabetical order.
If '''normValues''' is True, each value is processed by '''normalizeSpace'''().


==XML element creation methods==

* ''openElement(etype, attrs=None, makeEmpty=False, nobreak=False)''

Open an instance of the specified element type ('''etype''').

If '''attrs''' is specified, it may be a ready-to-use attribute string, or
a Python dict (whose values are escaped automatically).

(method `dictToAttrs`() can be used to turn any appropriate Python dict
into an attribute list).

If there are queued attributes (see '''queueAttribute'''()), they are
also issued and then de-queued.

If '''makeEmpty''' is specified and true, the element is written as an empty
element (and thus does not remain on the open-element stack).

If '''nobreak''' is True, the tag is not followed by a
line-break even if it normally would be.

* ''openElements(theList)''

Call '''openElement'''() on each item of '''theList'''.
Each such item should be a list or tuple of up to 4 items,
which are just passed on as the arguments to '''openElement''',
if the order [ etype, attrs, makeEmtpty, nobreak ].
Or just pass a string containing one or more whitespace-separated names.

* ''openElementUnlessOpen(gi, attrs=None, nobreak=False)''

Works like '''openElement'''(), except that it does nothing if the element
is '''already''' open. it need not be the innermost/current open element;
for that, see `openElementUnlessCurrent`.

* ''openElementUnlessCurrent(gi, attrs=None, nobreak=False)''

Works like '''openElement'''(), except that it does nothing if the element
is already the innermost/current open element (for that case,
see `openElementUnlessOpen`).

* ''closeElement(type, nobreak=False)''

Close the specified element.
If '''type''' is not open at all, a warning is issued and nothing is closed.
If '''type''' is open but is not the innermost/current open element,
a warning is issued and all elements out to and including it are closed.

If '''type''' is omitted, the innermost element is closed regardless of type.

''Note:'' To close an element even if there are other
elements to close first, and avoid the warning, use '''closeThroughElement'''().

* ''closeAllElements''(nobreak=False)

Close all open elements.

* ''closeToElement(type, nobreak=False)''

Close down to, but not including, the specified element.
If no element of the type is open, nothing happens.
If multiple instances are open, closing stops before closing the
innermost one.

* ''closeThroughElement(type)''

Close down to and including, the specified element.
If no element of the type is open, nothing happens.
If multiple instances are open, closing stops with the
innermost one.

* ''howManyAreOpen(typelist)''

Return the number of instances of the listed element types that are open.
'''typelist''' may be a (space-delimited) string or a list.

* ''closeAllOfThese(typelist)''

Close all instances of any element types in
'''typelist''', which may be a space-delimited string or an actual list.

* ''adjustToRank(n)''

This is for structures which do not have a depth number as part of
the element type name, but do nest. For example, the HTML `div` element.
The recursive element type (you only get one) is specified by the '''divTag''' option.

It is intended to make it easy to build such nested/container structures,
even when input only has (non-nested) headings (like much HTML).
It creates items at whatever level is needed at any given moment.
For example, '''adjustToRank(4)''' would open and close whatever divs are
needed, to get things in the right place to issue an h4, with divs directly
corresponding to hn levels.

SPecifically, this method:
** closes elements down to and including the '''n'''th
nested "div" (if any); then
** opens divs (automatically adding a
'''class="level_X"''' attribute to each), until '''n''' are open.

This leaves everything ready for writing a div title (or in HTML, Hn heading).
If already at level '''n''', it closes the div and opens a new one.
If already nested deeper, the deeper stuff is closed first.
If shallower, it opens as many "div"s as needed.

* ''makeEmptyElement(type, attrs)''

Output an XML empty element of the given element '''type''' and '''attributes'''.
Queued attributes (if any) are also applied. The behavior is affected by
the '''htmlFormat''' option. See also the related '''setEmpty()''' method.

* ''makeSmallElement(type, attrs, text)''

Open an XML element of the given element '''type''' and '''attributes''',
issue the given '''text''' content within it, and then close it.
Queued attributes (if any) are also applied.


==Document and global methods==

* ''setOutput(self, pathOrHandle, version="1.0", encoding="utf-8")''

Opens the requested file (or StringIO instance), and sets the values
for the XML Declaration parameters '''version''' and '''encoding'''. Either or both
of the last two can be set to '' or None, to indicate that they should be
entirely omitted from the XML Declaration. This is mainly
to accommodate `lxml`, which apparently has issues with '''encoding'''
(see [https://stackoverflow.com/questions/2686709]).

* ''startDocument''(doctypename, publicID="", systemID="")

Shorthand for '''makeXMLDeclaration'''() and '''makeDoctype'''().
See also '''endDocument'''().

* ''startHTML(version, title="")''

Shorthand for getting from start to having `body` open.
'''version''' should be one of "4strict", "4transitional" (or just "4"), "xhtml",
or "html5". In all but the last, an XML declaration is issued. Then the
DOCTYPE, html, head, the whole title, end head, and body.

* ''endDocument''()

Do a '''closeAllElements()''', and then close the output file.
See also '''startDocument'''() and '''startHTML'''().

* ''makeXMLDeclaration(self)''

Issue an XML declaration. '''version''' and/or '''encoding''' are generated
in accord with the latest setting from `setOutput`(), which can include
setting them to `None` in order to suppress them.

* ''makeDoctype(doctypename, publicID="", systemID="", xmlDecl=True)''

Output a DOCTYPE declaration.
Also calls `makeXMLDeclaration()` if it hasn't been called already,
unless `xmlDecl` is pass as False.


==Various other methods==

* ''makeComment(text)''

Output an XML comment. '''text''' is escaped as needed.

* ''makeText(text)''

Output '''text''' as XML content. XML delimiters are escaped as needed,
unless the '''escapeText''' option is unset.
With the '''ASCIIOnly''' option, all non-ASCII characters
are turned into character references.

* ''makeRaw(text)''

Dumps '''text''' to the output, with no escaping, no stack management, etc.
This is usually a bad idea, but just in case....

* ''makePI(target, text)''

Create a Processing Instruction directed to the specified '''target''',
with the given '''content'''. '''text''' is escaped as needed.

* ''makeCharRef(e, printIt=True)''

Create and return an entity or character reference, from an integer or
name (the name is not required to be one of the HTML 4 or XML predefined
entities, but must consist only of XML Name characters).
Unless `printIt` is set false, also print it.
If '''e''' is numeric, it results in a 4-digit (or more if needed),
hexadecimal or decimal (according to the 'entityBase' setting),
numeric character reference.
Otherwise '''e''' is treated as an entity name. It is '''not''' required to
be a known HTML entity name.

* ''normalizeTag(tag)''

Given a complete start (or empty) tag, normalize it to canonical XML
form. That is, normalize whitespace, and alphabetize the attributes.

* ''doPrint(s)''

Write the text in '''s''' literally to the output
(this is mainly used internally).
No escaping is done. All bets are off as far as producing well-formed XML.


==Character and name handling==

* ''fixName(name)''

Ensure that the argument is a valid XML NAME.
Any other characters become "_".

* ''escapeXmlContent''(s)

Escape XML delimiters as needed in text content.

* ''normalizeSpace''(s)

Do the equivalent of XSLT's normalize-space() function on '''s'''.
That is, remove leading and trailing whitespace, and reduce any internal
runs of whitespace to a single regular space character.

* ''escapeURI''(s)

Escape non-URI characters in `s` using the URI %xx convention.
If the '''iri''' option is set, don't escape chars just because they're
non-ASCII; only escape URI-prohibited ASCII characters.
See also options '''URIchars''' and '''escapeHREFs'''.


* ''escapeXmlAttribute(s)''

Escape the string '''s''' to be acceptable as an attribute value
(removing <, &, and "). If the '''ASCIIOnly''' option is set, escape non-ASCII
characters in '''s''' as well.

* ''escapeNonASCII(s)''

Replace any non-ASCII characters in the text with entity references.

* ''sysgen''()

Returns a unique identifier each time it's called. A prefix is
applied, set via the '''sysgenPrefix''' option.
Other than the prefix, this just generates a counter.


=Known bugs and limitations=

Doesn't know anything about namespaces (should at least track which ones
are declared and in effect, unify prefixes, avoid nested re-declarations, etc).

Doesn't know anything about conforming to a particular schema.

Automation of `xml:lang` attributes is not finished.

Pretty-printing is incomplete. For example,
'''breakAttrs''' does not put breaks between attributes that are
specified via the second argument to '''openElement'''() and its kin. To get
those breaks, use '''queueAttribute'''() instead.


=History=

* Ported from Perl original written 2010-12-22 by Steven J. DeRose.
* 2012-01-10 sjd: Port to Python.
* 2012-01-25 sjd: Clean up. Redo options.
* 2012-12-21 sjd: More work on porting.
* 2015-04-03: Make escaping to ASCII option work for all contexts.
Add HTMLEntities option.
* 2015-06-02: More port. pylint. escaping comments, pis, uris. entities.
* 2018-06-01: Hook up to StringIO.
* 2018-07-16: Add entityBase.
* 2018-07-21: Add startHTML(), openElements(). Separate makeXMLDeclaration().
* 2018-09-12: Add normalizeTag().
* 2018-10-15: Fix encoding/version options to allow None. Better self-test.
Allow either string or real list for rest of name-lists. Fix bug in
dictToAttrs() and use it in getQueuedAttributes().
* 2018-11-15: Set encoding even when output file is already open. Clean msgs.
Fix py 2/3 for htmlentitydefs. Add startDocument(). Check output for
illegal control characters. self.encoding vs. options['oencoding']!
* 2019-12-11: Start adding support to directly create a DOM.
* 2020-09-09: Better i/f and error-checking for openElements().
Add closeElements(). Improve help. Fix bugs in setEmpty(). Catch errors on
reconfigure for encoding, and warn instead of dieing.
Start `makeDOM` class. Add tests for legit XML NAMEs from XmlRegexes.py.
* 2021-07-20: Add typehinting, normalize a few names, drop Python 2 accommodations.


=To do=

* Finish `makeDOM` class and option.
* Do fancier indenting?
* Option to omit inheritable xml:lang and xmlns attributes.
* Finish div interpolation? See cleanMediaWiki.py:DivWrapper.
* MECS or TAG option with extended open/close semantics? See multiXML.
* Add an '''insertFile'''(escape=True) method?


=Rights=

Copyright 2010-12-22, 2012-01-10 by Steven J. DeRose.
This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

verbose = 0

def warning(msg:str) -> None:
    sys.stderr.write(msg+"\n")


###############################################################################
#
class XmlOutput:
    def __init__(
        self,
        HTMLEntities: bool = False,
        encoding: str = "utf-8",
        createDOM: bool = False,
        out: IO = None
    ):
        self.outputFH         = None
        self.theDOM           = None
        if (createDOM): self.theDOM = makeDOM()
        elif (out):  self.outputFH = out
        else: self.outputFH = sys.stdout

        self.xmlVersion       = "1.0"
        self.didXMLDcl        = False
        self.tagStack         = []
        self.langStack        = []
        self.syntax           = XmlSyntax()

        self.queuedAttributes = {}

        # Lists of elements to treat specially
        self.spaceSpecs       = {}          # elementType: nNewlines
        self.cantRecurse      = {}          # Cannot contain themselves
        self.inlines          = {}          # Treat as inline (not newlines)
        self.empties          = {}          # Always treat as empty
        self.suppressed       = {}          # Don't write these types at all

        self.sysgenCounter    = 1           # For generated IDs
        self.htmlp            = None        # For encoding HTML entities

        # options
        self.options = {
            "ASCIIOnly"        : False,     # Everything else -> entities
            "sysgenPrefix"     : "gen",     # For generated IDs

            # Places to break (^):  ^<p ^a="b"^>^...^</p^>^
            "breakSTAGO"       : True,      # Newline before start-tag
            "breakAttrs"       : False,     # Newline before each attribute
            "breakSTAGC"       : False,     # Newline after start-tag
            "breakETAGO"       : False,     # Newline before end-tag
            "breakETAGC"       : True,      # Newline after end-tag

            "divTag"           : "div",     # Tag to use for recursive DIV

            "checkCharset"     : True,      # Raise exception on bad chars
            "entityBase"       : 16,        # Hex or decimal for numeric chars?
            "escapeHREFs"      : False,     # Do URI %xx escaping as needed
            "escapeText"       : True,      # Escape < and & in text.
            "fixNames"         : False,     # Correct any non-WF names
            "htmlFormat"       : False,
            "HTMLEntities"     : False,     # See below
            "idAttrName"       : "id",
            "indent"           : True,
            "iri"              : True,      # Allow Unicode in URIs?
            "iString"          : "    ",    # String to repeat to make indents
            "normalizeText"    : False,
            "encoding"         : encoding,
            "suppressWSN"      : False,
            "trackIDs"         : False,     # Unused
            "URIchars"         : "-.\\w\\d_!\\'()*+",
            }

        if (HTMLEntities):
            self.setOption("HTMLEntities", True)

    def setOutput(self, pathOrHandle, version="1.0", encoding=None) -> bool:
        """Use this to determine where stuff goes: either to a
        file (specified by path or a handle), or to a string by
        using Python's StringIO class. Pass encoding=None to
        prevent writing any encoding at all in the XML declaration.
        """
        if (encoding): self.setOption("encoding", encoding)
        self.xmlVersion = version

        if (isinstance(pathOrHandle, str)):
            #warning("setOutput for path '%s'" % (pathOrHandle))
            try:
                self.outputFH = codecs.open(
                    pathOrHandle, "wb", encoding=self.getOption("encoding"))
            except IOError as e:
                warning("Failed to open '%s': %s (encoding %s):    \n%s" %
                    (pathOrHandle, e, self.getOption("encoding"), e))
                return False
        else:
            # https://stackoverflow.com/questions/4374455/
            #warning("setOutput for handle '%s'" % (pathOrHandle))
            succeeded = False
            try:
                self.outputFH = pathOrHandle
                pathOrHandle.reconfigure(encoding=self.getOption("encoding"))
                succeeded = True
            except AttributeError:
                pass
            try:
                self.outputFH = codecs.getwriter(
                    self.getOption("encoding"))(pathOrHandle)
                succeeded = True
            except AttributeError:
                pass
            if (not succeeded):
                warning("Could not configure output encoding!")
        return True

    def getOption(self, oname):
        assert (oname in self.options)
        return(self.options[oname])

    def setOption(self, oname, ovalue) -> None:
        assert (oname in self.options)
        self.options[oname] = ovalue

    def setSpace(self, enames, nNewlines) -> None:
        """Determine how many newlines get inserted before particular
        element types for output.
        @param enames: Element types, in a list or space-separated string.
        @param nNewlines: How many newlines to put before any of these.
        """
        if (isinstance(enames, str)):
            enames = re.split(r"\s+", enames)
        for e in (enames):
            if (not self.syntax.isXmlName(e)):
                raise ValueError("'%s' is not a legit XML NAME." % (e))
            self.spaceSpecs[e] = nNewlines

    def setInline(self, enames) -> None:
        """Define the listed names as "inline" tags, which mainly affects
        whether we put linebreaks around them in pretty-printing.
        @param enames: Element type names, either as a list or in a
        white-space-separated string.
        """
        if (isinstance(enames, str)):
            enames = re.split(r"\s+", enames)
        for e in (enames):
            if (not self.syntax.isXmlName(e)):
                raise ValueError("'%s' is not a legit XML NAME." % (e))
            self.inlines[e] = 1

    def setEmpty(self, enames) -> None:
        if (isinstance(enames, str)):
            enames = re.split(r"\s+", enames)
        for e in (enames):
            if (not self.syntax.isXmlName(e)):
                raise ValueError("'%s' is not a legit XML NAME." % (e))
            self.empties[e] = 1

    def setSuppress(self, enames) -> None:
        if (isinstance(enames, str)):
            enames = re.split(r"\s+", enames)
        for e in (enames):
            if (not self.syntax.isXmlName(e)):
                raise ValueError("'%s' is not a legit XML NAME." % (e))
            self.suppressed[e] = 1

    def setCantRecurse(self, enames) -> None:
        """Define the listed names as not being allowed to contain themselves.
        """
        if (isinstance(enames, str)):
            enames = re.split(r"\s+", enames)
        for e in (enames):
            if (not self.syntax.isXmlName(e)):
                raise ValueError("'%s' is not a legit XML NAME." % (e))
            self.cantRecurse[e] = 1

    def setHTML(self) -> None:
        """Set the list of known inline and non-recursive tags as for HTML.
        """
        self.setInline(
          "A ABBR ACRONYM B BASEFONT BDO BIG CENTER CITE CODE DFN DIR " +
          "EM FONT I IMG INPUT LABEL LEGEND KBD OPTGROUP OPTION " +
          "Q S SAMP SELECT SMALL SPAN STRIKE STRONG SUB SUP TEXTAREA TT U VAR"
            # Sometimes inline:
            #   APPLET BUTTON DEL IFRAME INS MAP OBJECT SCRIPT"
        )
        self.setCantRecurse("BR HR HEAD BODY H1 H2 H3 H4 H5 H6 IMG INS P PRE DEL")
        self.options["divTag"] = "DIV"

    def startHTML(self, version="4strict", title="") -> None:
        if (version == "4strict"):
            ids = [ "HTML", "-//W3C//DTD HTML 4.01//EN",
                "http://www.w3.org/TR/html4/strict.dtd" ]
        elif (version == "xhtml"):
            ids = [ "html", "-//W3C//DTD XHTML 1.1//EN",
                "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd" ]
        elif (version == "html5"):  # Meh
            ids = [ "html", None, None ]
        else:  # (version == 4 or version == "4transitional"):
            ids = [ "HTML", "-//W3C//DTD HTML 4.01 Transitional//EN",
                "http://www.w3.org/TR/html4/loose.dtd" ]


        self.setHTML()
        self.makeDoctype(ids[0], ids[1], ids[2])
        if (version == "xhtml"):
            self.queueAttribute("xmlns", "http://www.w3.org/1999/xhtml")
        self.openElement("html")
        self.openElement("head")
        self.openElement("meta",
            { "http-equiv":"content-type", "content":"text/html; charset=utf-8"
        })
        self.makeSmallElement("title", None, title)
        self.closeElement("head")
        self.openElement("body")
        return


    ###########################################################################
    # INQUIRIES
    #
    def getCurrentElementName(self):
        if (self.getDepth()>0):
            return(self.tagStack[-1])
        return(None)

    def getCurrentFQGI(self):
        if (self.getDepth()>0):
            return("/".join(self.tagStack))
        return(None)

    def getCurrentLanguage(self):
        if (len(self.langStack)>0):
            return(self.langStack[-1])
        return(None)

    def getDepth(self):
        """Return the number of elements that are currently open.
        """
        return(len(self.tagStack))

    def getIndentString(self, newline: bool=True, offset=0):
        """Return and newline and indent.
        To get just the spaces, pass newline=False.
        """
        if (not self.options["indent"]): return("")
        level = self.getDepth() + offset
        nl = ""
        if (newline): nl = "\n"
        return(nl + (self.options["iString"] * level))

    def howManyAreOpen(self, giList=None):
        """Return the number of instances that are open, of any of the
        element types listed in "giList" (which may be a Python list, or
        a string of whitespace-separated names). If omitted or None,
        returns the same thing as getDepth().
        """
        if (not giList):
            return(self.getDepth())

        if (isinstance(giList, str)):
            giList = re.split(r"\s+", giList)
        nOpen = 0
        for i in (range(0, self.getDepth())):
            for j in (range(0, len(giList))):
                if (giList[j] == self.tagStack[i]):
                    nOpen += 1
                    break
        return(nOpen)


    ###########################################################################
    # ATTRIBUTE QUEUEING
    #
    def queueAttribute(self, aname, avalue) -> None:
        """Add an attribute-value pair, to be issued with the next generated
        start-tag (in addition to any that are passed at that time. After
        being issued, the queued attributes are cleared.
        TODO: What if one is already queued w/ same name?
        """
        if (not self.syntax.isXmlName(aname)):
            raise ValueError("'%s' is not a legit XML NAME." % (aname))
        if (aname in self.queuedAttributes):
            warning("queueAttribute: Attribute '" + aname + "' already queued.")
        self.queuedAttributes[aname] = ""
        if (avalue):
            avalue = "%s" % (avalue)
            self.queuedAttributes[aname] = self.escapeXmlAttribute(avalue)

    def getQueuedAttributes(self):
        """Return an attribute string including all the queued attributes
        (if any), plus a leading space.
        """
        return self.dictToAttrs(self.queuedAttributes)

    def clearQueuedAttributes(self) -> None:
        self.queuedAttributes = {}


    ###########################################################################
    ####### OPEN
    #
    def openElements(self, theList) -> None:
        """Call openElement() for each item of theList.
        @param theList represents a list of elements to open. It can be
            * a string, which is split into a list of tokens.
            * A list
        In either case, there is then a list, in which the item(s) must be:
            * A single string element name
            * A list or tuple of [ name, attrs:dict, makeEmpty, nobreak:bool ]
                (these are the arguments to openElement(). Later ones can
                be left off.
        """
        if (isinstance(theList, str)):
            theList = re.split(r"\s+", theList)
        if (not isinstance(theList, list)):
            raise ValueError(
                "Pass a string or list, not %s." % (type(theList)))

        for i, stuff in enumerate(theList):
            if (isinstance(stuff, str)):
                self.openElement(stuff)
            elif (not isinstance(stuff, (list, tuple))):
                raise ValueError("Item %d is not string, list, or tuple, but %s"
                    % (i, type(stuff)))
            if (len(stuff) == 1):
                self.openElement(stuff[0])
            elif (len(stuff) == 2):
                self.openElement(stuff[0], attrs=stuff[1])
            elif (len(stuff) == 3):
                self.openElement(stuff[0], attrs=stuff[1],
                    makeEmpty=stuff[2])
            elif (len(stuff) == 4):
                self.openElement(stuff[0], attrs=stuff[1],
                    makeEmpty=stuff[2], nobreak=stuff[3])
            else:
                raise ValueError("Item %d is length %d, not in 0...4."
                    % (len(stuff)))
        return

    def openElement(self, gi, attrs=None, makeEmpty: bool=False, nobreak: bool=False) -> None:
        """Start a new XML element by issuing the start-tag. Add to stack.
        "attrs" may be a string or a dict.
        With "makeEmpty" or an element that has been declared always empty
        (via setEmpty()), make it an empty element.
        "nobreak" suppresses any newline after the start-tag.
        """
        if (not self.syntax.isXmlName(gi)):
            raise ValueError("'%s' is not a legit XML NAME." % (gi))
        if (gi in self.cantRecurse):
            while(self.howManyAreOpen(gi) > 0):
                self.closeElement()
        extra = 0
        if (gi in self.spaceSpecs):
            extra = self.spaceSpecs[gi]
        elif (gi in self.inlines):
            pass
        elif (self.options["breakSTAGO"] or self.options["indent"]):
            extra = 1
        if (extra>0):
            self.doPrint(("\n " * extra) + self.getIndentString(newline=False))

        out = ""
        if (self.options["indent"]): out += self.getIndentString()
        out = "<" + gi
        if (isinstance(attrs, dict)):
            attrs = self.dictToAttrs(attrs)
        if (attrs):
            if (self.options["breakAttrs"]):
                out += self.getIndentString()
            out += " " + attrs
        out += self.getQueuedAttributes()
        #warning("\n***** %s *****" % (out))

        self.clearQueuedAttributes()

        if (makeEmpty or gi in self.empties):
            out += "/>"
        else:
            out += ">"
            self.tagStack.append(gi)
            if (len(self.langStack)==0): self.langStack = ["en"]
            self.langStack.append(self.langStack[-1])

        if (self.options["breakSTAGC"] and gi not in self.inlines
            and not nobreak):
            out += "\n"
        self.doPrint(out)

    def openElementUnlessOpen(self, gi, attrs="", nobreak: bool=False) -> None:
        if (self.howManyAreOpen(gi) > 0): return
        self.openElement(gi, attrs, nobreak)


    def openElementUnlessCurrent(self, gi, attrs="", nobreak: bool=False) -> None:
        if (self.getCurrentElementName() == gi): return
        self.openElement(gi, attrs, nobreak)


    def dictToAttrs(self, dct, sortAttributes: bool=None, sortAttrs: bool=None, normValues: bool=False):
        """Turn a dict into an attribute list.
        """
        # Backward-compatible naming, for the moment:
        if (sortAttributes is None): sortAttributes = sortAttrs
        if (sortAttributes is None): sortAttributes = False

        if (self.options["breakAttrs"]):
            sep = self.getIndentString()
        else:
            sep = " "
        anames = dct.keys()
        if (sortAttrs): anames.sort()
        attrString = ""
        for a in (anames):
            if (not self.syntax.isXmlName(a)):
                raise ValueError("'%s' is not a legit XML NAME." % (a))
            v = dct[a]
            if (normValues): v = self.normalizeSpace(v)
            attrString += "%s%s=\"%s\"" % (sep, a, self.escapeXmlAttribute(v))
        return attrString

    ###########################################################################
    ####### CLOSE
    #
    def closeElements(self, theList) -> None:
        if (isinstance(theList, str)):
            theList = re.split(r"\s+", theList)
        if (not isinstance(theList, list)):
            raise ValueError(
                "Pass a string or list, not %s." % (type(theList)))

        for i, stuff in enumerate(theList):
            if (isinstance(stuff, str)):
                self.closeElement(stuff)
            else:
                raise ValueError("Item %d is not an element type name, but %s."
                    % (i, type(stuff)))
        return

    def closeElement(self, gi="", nobreak=0):
        """Close the current XML element and remove from the stack.
        If "gi" is passed, it must match the element to be closed.
        A warning is issued if any attributes remain queued.
        """
        if (self.getDepth() <= 0):
            warning("closeElement(): No ('%s') or anything else open." % (gi))
            return
        if (not gi):
            gi = self.getCurrentElementName()

        if (gi and gi != self.getCurrentElementName()):
            warning("closeElement(): '%s' is not the current element (stack: %s)."
                % (gi, self.getCurrentFQGI()))
            return

        if (len(self.queuedAttributes)):
            warning("closeElement(): Should not be these queued attributes: '" +
                ", ".join(sorted(self.queuedAttributes)) + "'.")
            self.clearQueuedAttributes()

        out = "</" + gi + ">"
        # Don't indent unless also breaking.
        if (not nobreak):
            if (self.options["breakETAGO"] and gi not in self.inlines):
                out = self.getIndentString(offset=-1) + out
            if (self.options["breakETAGC"] and gi not in self.inlines):
                out += "\n"
        self.doPrint(out)
        self.tagStack.pop()
        self.langStack.pop()

    def closeAllElements(self, nobreak: bool=False):
        """Close all open elements.
        """
        while (self.getDepth()):
            self.closeElement(nobreak=nobreak)

    def closeToElement(self, gi, nobreak: bool=False):
        """Close elements up to but not including the "gi" specified.
        If more than one of "gi" is open, close only to the innermost.
        """
        if (self.howManyAreOpen(gi) == 0): return
        while (self.getDepth()):
            if (self.getCurrentElementName() == gi): break
            self.closeElement(nobreak=nobreak)

    def closeElementIfOpen(self, gi="", nobreak: bool=False):
        """Close through element "gi" if there is one open, else do nothing.
        """
        self.closeThroughElement(gi, nobreak)

    def closeThroughElement(self, gi, nobreak: bool=False):
        """Close elements up to AND including the innermost "gi" specified.
        """
        if (self.howManyAreOpen(gi) == 0): return
        while (self.getDepth()):
            cur = self.getCurrentElementName()
            self.closeElement(nobreak=nobreak)
            if (cur == gi): break

    def closeAllOfThese(self, giList, nobreak: bool=False):
        """Call this with a list of space-separated element type names,
        to make sure all instances of any of those element types are closed.
        """
        if (" " in giList):
            giList = re.split(r"\s+", giList)
        while (self.howManyAreOpen(giList)>0):
            self.closeElement(nobreak=nobreak)

    def adjustToRank(self, target):
        """Close and/or open DIVs or similar elements, in order to get all set
        to issue a heading at a given (numbered) level (counting from 0).
        """
        theTag = self.options["divTag"]
        while (self.howManyAreOpen(theTag) >= target):
            self.closeThroughElement(theTag)
        for cur in (range(self.howManyAreOpen(theTag), target)):
            self.queueAttribute("class", "level_%s" % cur)
            self.openElement(theTag)
        # Now we're ready to put in the title (for example, Hn in HTML).



    ###########################################################################
    # OTHER CONSTRUCTS
    #
    def startDocument(self, documentElement, publicID="", systemID="", xmlDecl: bool=True):
        self.makeXMLDeclaration()
        self.makeDoctype(documentElement=documentElement,
            publicID=publicID, systemID=systemID, xmlDecl=xmlDecl)

    def endDocument(self):
        self.closeAllElements()
        if (self.outputFH and self.outputFH != sys.stdout):
            self.outputFH.close()
            self.outputFH = None

    def makeXMLDeclaration(self):
        ver = enc = ""
        if (self.xmlVersion): ver = ' version="%s"' % (self.xmlVersion)
        if (self.getOption("encoding")): enc = ' encoding="%s"' % (self.getOption("encoding"))
        self.doPrint("<?xml%s%s?>" % (ver, enc))
        self.didXMLDcl = True

    def makeDoctype(self, documentElement, publicID="", systemID="", xmlDecl: bool=True):
        if (xmlDecl and not self.didXMLDcl):
            self.makeXMLDeclaration()
        if (publicID is None and systemID is None):  # Hack for HTML5.
            self.doPrint("<!DOCTYPE %s>" % (documentElement))
        else:
            self.doPrint('<!DOCTYPE %s PUBLIC "%s" "%s" []>' %
                (documentElement, publicID, systemID))

    def makeEmptyElement(self, gi, attrs=""):
        self.openElement(gi, attrs, 1)

    def makeSmallElement(self, gi, attrs="", text=""):
        if (attrs and not re.match(r"""\w+\s*=\s*('[^']*'|"[^"]*")""", attrs)):
            warning("Bad attribute string arg to makeSmallElement: '" + attrs + "'")
        self.openElement(gi, attrs=attrs, nobreak=1)
        self.makeText(text)
        self.closeElement(gi)

    def makeComment(self, text):
        self.doPrint(self.getIndentString() + "<!-- %s -->" %
            (self.escapeXmlComment(text)))

    def makeText(self, text):
        if (self.options["suppressWSN"] and re.match(r"\s*", text)):
            return
        if (self.options["normalizeText"]):
            text = self.normalizeSpace(text)
        if (self.options["escapeText"]):
            text = self.escapeXmlContent(text)
        self.doPrint(text)

    def makeRaw(self, text):
        """If you really, really want to just dump a string into the output
        with no escaping or checking, you can.
        """
        self.doPrint(text)

    def makePI(self, target, text):
        self.doPrint(self.getIndentString() +
            "<?%s %s?>" % (target, self.escapeXmlPi(text)))

    def makeCharRef(self, nameOrNumber, printIt: bool=True):
        """Make an entity or named character reference.
        """
        if (type(nameOrNumber) == int or re.match(r"\d+$", nameOrNumber)):
            n = int(nameOrNumber)
            if (self.options["entityBase"] == 10): rc = "&#%04d;" % (n)
            else: rc = "&#%04x;" % (n)
        elif (re.match(r"[-:.\w]+$", nameOrNumber, re.UNICODE)):
            rc = "&%s;" % (nameOrNumber)
        else:
            rc = "<!-- BAD ENTITY '%s' -->" % (nameOrNumber)
            raise ValueError("makeCharRef: Non XML NAME character in '%s'" %
                (nameOrNumber))
        if (printIt): self.doPrint(rc)
        return rc


    ###########################################################################
    #
    xcObj = None

    def normalizeTag(self, tag):
        """Turn a tag into Canonical XML form. This is a perhaps-useful
        utility, but doesn't connect all that much with others.
        See XmlRegexes.py for regexes.
        """
        if (XmlOutput.xcObj is None):
            from XmlRegexes import XmlRegexes
            XmlOutput.xcObj = XmlRegexes()
        if (not re.match(XmlOutput.xcObj.x["stag"], tag)):
            raise ValueError("Not an XML start-tag: '%s'." % (tag))
        mat = re.match(r"<(\S+)", tag)
        typeName = mat.group(1)
        attrDict = {}
        for mat in re.finditer(XmlOutput.xcObj.x["attr"], tag):
            attrDict[mat.group(2)] = mat.group(3)
        return "<%s %s>" % (typeName, self.dictToAttrs(
            attrDict, sortAttrs=True, normValues=True))


    ###########################################################################
    # All XML output goes through here.
    #
    def doPrint(self, x):
        assert (self.outputFH is not None)
        #warning("%s==>%s<==" % (self.outputFH, x))
        if (self.getDepth()):
            fqgi = self.getCurrentFQGI()
            for gi in (re.split(r"/", fqgi)):
                if (gi in self.suppressed):
                    return
        if (PY2 and self.options["encoding"]):
            x = x.encode(self.options["encoding"])
        if (self.options["checkCharset"]):
            mat = re.search(r"([\x00-\x08\x0b\x0c\x0e-\x1F])", x)
            if (mat): raise ValueError(
                "Illegal C0 control character 0x%02x in '%s' (encoding: '%s')."
                    % (ord(mat.group(1)), x, self.options["encoding"]))
        if (self.outputFH):
            #warning("doPrint passed %s." % (type(x)))
            if (not isinstance(x, str)):
                warning("Attempting to write non-string (type %s)." %
                    (type(x)))
                x = x.encode("utf-8")
            #warning("after test: %s." % (type(x)))
            if (self.outputFH == sys.stdout):
                self.outputFH.print(x)
            else:
                print(x)


    ###########################################################################
    # ESCAPING
    #
    def fixName(self, name):
        """Turn a string into a valid XML name (imperfect char set).
        """
        name = re.sub(r"[^-:._\w\d]", "_", name, re.UNICODE)
        if (name == "" or re.match(r"[-_:\d]", name)):
            name = "A." + name
        return(name)

    def normalizeSpace(self, s):
        """This is slightly more aggressive than the normalization defined
        in the XML spec -- it also catches other whitespace characters,
        such as nonbreaking, em, en, and thin spaces.
        """
        if (not (s)):
            return("")
        s = s.rstrip().lstrip()
        s = re.sub(r"\s+", " ", s, re.UNICODE)
        return(s)

    def escapeXmlContent(self, s):
        """Don't use for escaping attribute values, that's different, see below).
        Quietly deletes any prohibited control characters!
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = s.replace("&",   "&amp;",)
        s = s.replace("<",   "&lt;")
        s = s.replace("]]>", "]]&gt;")
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        return(s)

    def escapeXml(self, s):
        self.escapeXmlContent(s)

    def escapeURI(self, s):
        s = re.sub(r'([^-!\$\'()*+.0-9:;=?\@A-Z_a-z])',
                   self.charToURIFunction, s)
        return(s)

    def charToURIFunction(self, mat):
        c = mat.group(1)
        if (ord(c) >= 127):
            theBytes = c.encode("utf-8")
            buf = ""
            for b in theBytes:
                buf += "%{0:02x}".format(b)
        else:
            buf = "%{0:02x}".format(ord(c))
        return(buf)

    def escapeXmlAttribute(self, s="", apostrophes=0):
        """Escape as need for quoted attributes.
        Quietly deletes any non-XML control characters!
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = s.replace("&",  "&amp;")
        s = s.replace("<",  "&lt;")
        if (apostrophes):
            s = s.replace("'", "&apos;")
        else:
            s = s.replace('"', "&quot;")
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        if (self.options["escapeHREFs"] and
            re.match(r"(https?|mailto|ftp|local)://", s)):
            s = self.escapeURI(s)
        return(s)

    def escapeXmlPi(self, s):
        """Escape as needed for processing instructions.
        XML doesn't define a standard escaping for this, so I chose one.
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = re.sub(r"\?>",  "?&gt;", s)
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        return(s)

    def escapeXmlComment(self, s):
        """Escape as needed for comment.
        XML doesn't define a standard escaping for this, so I chose one.
        """
        s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
        s = re.sub(r"--", "\u2014", s)
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        return(s)

    def escapeNonASCII(self, s):
        """Turn anything but ASCII printable characters into HTML entity
        references (if available), or numeric character references.
        """
        if (not (s)): return("")
        rc = ""
        for i in range(len(s)):
            if (s[i] in string.printable):
                rc += s[i]
            elif (s[i] in codepoint2name):
                rc += "&%s;" % (codepoint2name[s[i]])
            else:
                rc += self.makeCharRef(ord(s[i]), printIt=False)
        return(rc)

    def sysgen(self):
        self.sysgenCounter = self.sysgenCounter + 1
        return(self.options["sysgenPrefix"] + self.sysgenCounter)


###############################################################################
# makeDOM
#
class makeDOM:
    from xml.dom.minidom import Node
    from xml.dom.minidom import Document
    from xml.dom import minidom  # noqa: F821

    def __init__(self):
        self.theDOM = Document()
        self.domStack = []
        raise NotImplementedError("Direct DOM construction is still a TODO.")

    def openElement(self, eName: str, attrs: Union[Dict, None]=None) -> None:
        newNode = self.theDOM.createElement(eName)
        for k, v in attrs:
            newNode.addAttribute(k, v)
        self.domStack[-1].appendChild(newNode)
        self.domStack.append(newNode)

    def closeElement(self, eName: str=None) -> None:
        if (self.domStack[-1].nodeType != Node.ELEMENT_NODE or
            (eName and self.domStack[-1].nodeName!=eName)):
            warning("CloseElement is for '%s', but DOM is at '%s'." %
                (eName, self.domStack[-1].nodeType))
        self.domStack.pop()

    def makeComment(self, txt: str) -> None:
        newNode = self.theDOM.createComment(txt)
        self.domStack[-1].appendChild(newNode)

    def makePI(self, tgt: str, txt: str) -> None:
        newNode = self.theDOM.createProcessingInstruction(tgt, txt)
        self.domStack[-1].appendChild(newNode)

    def getDOM(self):
        return self.theDOM


###########################################################################
# Type-checks (excerpted from
# [https://github.com/sderose/XML.git/PARSERS/blob/master/XmlRegexes.py])
# TODO: Cut this over to use
#     https://github.com/sderose/XML.git/PARSERS/blob/master/XmlRegexes.py
#
class XmlSyntax:
    def __init__(self, check: bool=True):
        xmlSpaceList         = "\t\n\r\x20"
        xmlSpace             = r"[%s]" % (xmlSpaceList)

        xmlNameStartCharRanges = [
            (ord(":"), ord(":")),
            (ord("A"), ord("Z")),
            (ord("_"), ord("_")),
            (ord("a"), ord("z")),
            (0x00c0,   0x00d6),
            (0x00d8,   0x00f6),
            (0x00f8,   0x02ff),
            (0x0370,   0x037d),
            (0x037f,   0x1fff),
            (0x200c,   0x200d),
            (0x2070,   0x218f),
            (0x2c00,   0x2fef),
            (0x3001,   0xd7ff),
            (0xf900,   0xfdcf),
            (0xfdf0,   0xfffd),
            #(0x10000, 0xeffff),
        ]
        xmlNameStartChar = r"["
        for st, en in xmlNameStartCharRanges:
            xmlNameStartChar += XmlSyntax.makeCharRange(st, en)
        xmlNameStartChar += r"]"

        xmlNameCharAdditionalRanges = [
            (ord("-"), ord("-")),
            (ord("."), ord(".")),
            (ord(":"), ord(":")),
            (ord("0"), ord("9")),
            # ???   0x00b7  MIDDLE DOT
            (0x0300,   0x036f),
            (0x203f,   0x2040),
        ]
        xmlNameChar = xmlNameStartChar[0:-1]  # Drop the "]"
        for st, en in xmlNameCharAdditionalRanges:
            xmlNameChar += XmlSyntax.makeCharRange(st, en)
        xmlNameChar += r"]"

        xmlCharAdditionalRanges = [
            (0xD7FF,   0xD7FF),
            (0xE000,   0xFFFD),
            #(0x10000, 0x0FFFF),
        ]
        xmlChar = xmlNameChar[0:-1]
        for st, en in xmlCharAdditionalRanges:
            xmlChar += XmlSyntax.makeCharRange(st, en)
        xmlChar += r"]"

        xmlName               = r"(" +xmlNameStartChar+xmlNameChar+ r"*)"
        xmlNmToken            = r"(" +xmlNameChar+ r"+)"
        qlit                  = r'(".*?"|\'.*?\')'
        attr                  = r"(\s+(" +xmlName+ r")\s*=\s*(" +qlit+ r"))"
        subset                = r"\[" + r"[^\]]*" + r"\]"   ### TODO: Imprecise
        xmlText               = r"([^<&]+)"

        self.xc = {
            "xmlChar"          : xmlChar,
            "xmlNmToken"       : xmlNmToken,
            "qlit"             : qlit,
            "attr"             : attr,
            "subset"           : subset,
            "text"             : xmlText,
            "xmlSpace"         : xmlSpace,
            "xmlNameStartChar" : xmlNameStartChar,
            "xmlNameChar"      : xmlNameChar,
            "xmlName"          : xmlName,
        }

        if (check):
            for k, v in self.xc.items():
                try:
                    re.compile(v)
                except re.error as e:
                    msg = "%s" % (e)
                    mat = re.search(r" at position (\d+)", msg)
                    if (mat):
                        pos = int(mat.group(1))
                        print("Exception on regex %s: /%s[HERE]%s/\n    %s" %
                            (k, v[0:pos], v[pos:], e))
                    else:
                        print("Exception on regex %s: /%s/\n    %s" %
                            (k, v, e))

    @staticmethod
    def makeCharRange(st: int, en: int):
        """Given a starting and ending code point (the end is the *real* end,
        not one past it as with Python slices), return a string representation
        that can be put inside a regex []-group.
        """
        if (st < 31 or en < st or en > 0x1FFFF):
            warning("Bad char range (discarded): %05x ... %05x." % (st, en))
            return ""
        if (st==en):
            return XmlSyntax.UEscape(st)
        return XmlSyntax.UEscape(st) + "-" + XmlSyntax.UEscape(en)

    @staticmethod
    def UEscape(codePoint: int):
        if (codePoint > 0xFFFF):
            return "\\U" + ("%08x" % (codePoint))
        return "\\u" + ("%04x" % (codePoint))

    def isXmlChar(self, c: str) -> bool:
        """Return whether I<c> is an XML Character.
        """
        if (re.match(self.xc["xmlChar"], c)): return True
        return False

    def isXmlSpaceChar(self, c: str) -> bool:
        """Check if I<c> is a valid XML space character.
        """
        if (re.match(self.xc["xmlSpace"], c)): return True
        return False

    def isXmlNameStartChar(self, c: str) -> bool:
        """Check if I<c> is a valid XML name-start character.
        """
        if (re.match(self.xc["xmlNameStartChar"], c)): return True
        return False

    def isXmlNameChar(self, c: str) -> bool:
        """Check if I<c> is a well-formed XML name character.
        """
        if (re.match(self.xc["xmlNameChar"], c)): return True
        return False

    def isXmlName(self, s: str) -> bool:
        """Check if I<n> is a well-formed XML (element/attribute/etc) name.
        """
        if (re.match(self.xc["xmlName"], s)): return True
        return False

    def isXmlNmtoken(self, s: str) -> bool:
        """Check if I<c> is a well-formed XML name token.
        """
        if (re.match(self.xc["xmlNmToken"], s)): return True
        return False


###############################################################################
#
if __name__ == "__main__":
    import argparse

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--encoding", "--oencoding", type=str, default="utf-8",
            help="What character encoding to use for the input.")
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

    def exercise(x, encoding=None):
        """Call a bunch of things for a basic smoke-test.
        """
        if (encoding != "utf-8"):
            warning("\n******* WARNING: sys.stdout with encoding '%s'!\n\n" %
                (encoding))
        x.setOutput(sys.stdout, version="1.0", encoding=encoding)
        #x.setSpace(enames, code)
        x.setInline([ "i", "b", "u", "tt", "a" ])
        x.setEmpty([ "br", "hr", "img" ])
        x.setCantRecurse([ "p" ])
        x.startDocument("html", publicID="-//foo", systemID="my.dtd")

        x.openElements([ "html", "head", "style" ])
        x.makeComment("""
    body   { margin:36pt; }
    li     { color:#F00; margin-top:12pt; }
    """)
        x.closeElement("style")
        x.makeSmallElement("title", attrs=None, text="Some title text")
        x.closeElement("head")

        x.openElement("body")
        x.openElement("p", attrs="id='foo1'")
        x.makeText("A paragraph typically has some text. Like ")
        x.openElement("i", nobreak=1)
        x.makeText("this italic phrase")
        x.closeElement("i", nobreak=1)
        x.makeRaw(", or this ")
        x.openElement("b", nobreak=1)
        x.makeText("this bold phrase ")
        x.closeElement("b", nobreak=1)
        x.makeRaw(", or this ")
        x.openElement("u")
        x.makeText("this underline phrase ")
        x.closeElement("u")
        x.makeText("followed by 4 ellipses: ")
        x.makeCharRef(0x2026)
        x.makeCharRef(8230)
        x.makeCharRef("8230")
        x.makeCharRef("hellip")

        #print("Open elements %d, current isw '%s' (should be 3, 'p'). %s '%s'"
        #    % (x.getDepth(), x.getCurrentElementName(),
        #    x.getCurrentFQGI(), x.getCurrentLanguage()))
        x.closeElement("p")

        x.makePI("xmllint", "foo=bar baz=? whoot=?>")

        x.makeSmallElement("p", text="Some brief paragraph text.")

        x.openElement("p")
        x.makeText("A paragraph typically has some text.")
        x.openElement("p")
        x.makeText("A paragraph after an unclosed one.")
        x.openElement("p")
        x.makeText("A paragraph after another unclosed one.")
        #print("paragraphs open: %d." % (x.howManyAreOpen("p")))
        x.closeAllOfThese("p")
        #print("paragraphs open now: %d." % (x.howManyAreOpen("p")))

        x.makeEmptyElement("hr", attrs="class='a'")

        x.queueAttribute("zork", "zerg")
        x.clearQueuedAttributes()
        x.queueAttribute("id", "queuedValue")
        x.queueAttribute("class", "red green blue")
        #print("\n*** queued: %s ***" % (x.getQueuedAttributes()))
        x.openElement("p")
        x.makeText("This paragraph should have 2 queued attributes.")

        x.endDocument()

        #x.setSuppress(self, enames)
        #x.setHTML(self)
        #x.startHTML(version, title="")
        #x.queueAttribute(aname, avalue)
        #x.openElementUnlessOpen(gi, attrs="", nobreak=0)
        #x.openElementUnlessCurrent(gi, attrs="", nobreak=0)
        #x.closeAllElements(nobreak=0)
        #x.closeToElement(gi, nobreak=0)
        #x.closeElementIfOpen(gi="", nobreak=0)
        #x.closeThroughElement(gi, nobreak=0)
        #x.adjustToRank(target)
        return


    from xml.dom.minidom import Node
    import html5lib

    xo = XmlOutput()

    def traverse(root):
        if (root.nodeType == Node.TEXT_NODE):
            xo.makeText(root.nodeValue)
        elif (root.nodeType == Node.COMMENT_NODE):
            xo.makeComment(root.nodeValue)
        elif (root.nodeType == Node.PROCESSING_INSTRUCTION_NODE):
            xo.makePI(root.nodeName, root.nodeValue)
        elif (root.nodeType == Node.ELEMENT_NODE):
            xo.openElement(root.nodeName)
            for ch in root.childNodes:
                traverse(ch)
            xo.closeElement()
        else:
            warning("******* Unknown node type: %d" % (root.nodeType))
        return

    ####### MAIN #######
    #
    args = processOptions()

    if (not args.files):
        warning("******* Running smoke-test ******")
        exercise(xo, encoding=args.encoding)
    else:
        for path in (args.files):
            warning("\n\n" + ("#" * 79))
            warning("####### XmlOutput: '%s'" % (path))
            try:
                fh = codecs.open(path, "rb", encoding=args.encoding)
                dom = html5lib.parse(fh, treebuilder="dom")
            except IOError:
                warning("    Cannot open or parse '%s'." % (path))
                continue

            xo.makeDoctype("HTML")
            traverse(dom.documentElement)
            xo.endDocument()

    if (not args.quiet):
        warning("\n******* Done *******")
