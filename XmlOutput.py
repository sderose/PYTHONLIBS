#!/usr/bin/env python
#
# XmlOutput.py
#
# Allow the PY2 compatibility block below:
#pylint: disable=E0401, E0602
#
from __future__ import print_function
import sys
import re
import codecs
import string
import xml

descr = """

=pod

=head1 Notes

A Python module to help with generating XML output (also available with the
same API in Perl).

It keeps the output element and language stacks and some other state information,
handles escaping automatically for all syntactic contexts,
and generally tries to
ensure that you end up with well-formed XML. It also makes your XML-generating
application more readable, because you only have to deal with high-level,
(hopefully) intuitive methods (e.g., closeThroughElement("foo"),
makeComment(text),...), and they encapsulate a lot of mechanical tasks such as
checking the open-element stack for certain element types.

=head2 Example

  from XmlOutput import XmlOutput
  x = XmlOutput()
  xo.setOption('indent', True)
  xo.setOption('breakETAGO', False)
  xo.startDocument("html", systemID="html4.dtd")
  xo.openElement("html")
  xo.openElement("head")
  xo.openElement("title")
  makeText("RFC file: " + $f)
  xo.closeElement("title")
  xo.closeElement("head")
  xo.openElement("body")
  xo.openElement("p", 'id="foo"')
  xo.makeText("Hello, world.")
  xo.endDocument()

Note that if you don't set an encoding (via the constructor or I<setOutput>()),
it defaults to C<utf-8>. If you are writing to C<sys.stdout>, or processing
downstream, be sure that's what you want.
If you just want the stack maintenance and error-checking, but not to produce
actual output, set C<xo.outputFH> to None.

If you want to output to a string, use Python's built-in C<stringio> package.

=head2 Testing

You can run a self-test by just invoking the file from the command-line.

=head1 Methods

=over

=item * B<__init__>(encoding="utf-8")

Create a new instance of the XmlOutput object. You can set the output character
encoding here, of on I<setOutput>() (see below).

=item * B<getVersion>()

Return the version date of the module.

=item * B<getOption(name)>

Return the current value of option I<name> (see following).

=item * B<setOption(name, value)>

Set option I<name> to I<value>.
The name is checked for being a known option, but no
checking is done on the value (values are Boolean unless otherwise noted).

=over

=item * B<ASCIIOnly> -- Use entities for all non-ASCII content characters.

=item * B<breakSTAGO> -- Break before start-tags. Default True.

=item * B<breakAttrs> -- Break before each attribute. Default False.

=item * B<breakSTAGC> -- Break after start-tags. Default False.

=item * B<breakETAGO> -- Break before end-tags. Default False.

=item * B<breakETAGC> -- Break after end-tags. Default True.

=item * B<divTag> -- what element type is used for nested containers,
like (the default) HTML C<div>. See method I<adjustToRank> for a handy
way to ensure that these get handled right even if the source document
only has headings (C<Hn> or similar).
There is presently no special support for numbered C<div>s (div1, div2, ...).

=item * B<escapeHREFs> -- Apply %xx escaping to all attributes that appear
to be URIs. That is, ones that match r'(https?|mailto|ftp|local)://'.
Default False. See also I<escapeURI>(s), which this uses, but can also
be called directly.

=item * B<escapeText> -- Escape "<" and "&" in text. Default True.

=item * B<fixNames> -- Correct any requested element type names to be
valid XML NAMEs. Default False.

=item * B<HTMLEntities> -- Use HTML entities for special
characters when possible. This requires that the F<HTMLparser> library
be installed.

=item * B<htmlFormat> -- Do not issue XML-style empty elements. Default False.

=item * B<idAttrName> -- Specify an attribute name to treat as an XML ID
(mainly for use with I<trackIDs>. Default C<id>.

=item * B<indent> -- Pretty-print the XML output. See also I<iString>.
Default True.

=item * B<iri> -- Allow non-ASCII characters in URIs. Default True.

=item * B<iString> -- Use this string as the (repeated) indent-string
for pretty-printing. Default C<    > (4 spaces).

=item * B<normalizeText> -- Normalize white-space in output text nodes.
See also I<normalizeTag>().

=item * B<encoding> -- Write output in this character encoding.

=item * B<suppressWSN> -- Do not output white-space-only text nodes.

=item * B<sysgenPrefix> -- Set what string is prefixed to a serial number
with the I<sysgen>() call.

=item * B<trackIDs> -- (unsupported) Warn if an "id" attribute value is
re-used (this does not see any DTD, it just goes by attribute name).
See also I<idAttrName>.

=item * B<URIchars> -- What characters are allowed (unescaped) in URIs.
If the I<iri> option is set, all non-ASCII characters are also allowed.
Default: "-.\\w\\d_!\\'()*+"

=back

=item * B<setCantRecurse(types)>

Prevent any element type listed (space-separated) in I<types>
from being opened recursively.
For example, if you set this for C<p>, and the open elements
are html/body/div/p/footnote/, and you attempt to open another C<p>, then
elements are closed until there are no C<p> elements left open, after which
a new C<p> is opened (in this example, 2 elements would thus be closed).

=item * B<setSpace(types, n)>

Cause I<n> extra newlines to be issued before the start of each instance
of any element type in I<types> (which can be either a list of individual names, or a string containing white-space-separated names).
The newlines will only be generated if an element also has I<breakSTAGO>
set, and if it has not been set be C<inline> (via I<setInline>().

=item * B<setInline(types)>

Add each (space-separated) element type in I<types> to a list of elements
to be treated as inline (thus getting no breaks around it despite
general options for breaking).

If I<types> is "#HTML", the HTML 4 inline tags are added to the list:
A ABBR ACRONYM B BASEFONT BDO BIG BR CITE CODE DFN
EM FONT I IMG INPUT KBD LABEL Q S SAMP SELECT SMALL
SPAN STRIKE STRONG SUB SUP TEXTAREA TT U VAR.
Some other tags are only sometimes inline
(APPLET BUTTON DEL IFRAME INS MAP OBJECT SCRIPT).
These are not added by #HTML,
but some or all can be added with another call to I<setInline>().

=item * B<setEmpty(types)>

Cause any element type listed (space-separated) in I<types> to be
written out as an empty element when opened (thus, no I<closeElement>() call
is needed for them).

=item * B<setSuppress(types)>

Record that elements of any type listed (space-separated) in I<types>
(and their entire subtrees) should not be output.
Not to be confused with the I<suppressWSN> option.

=item * B<getCurrentElementName>()

Return the element type name of the innermost open element.

=item * B<getCurrentFQGI>()

Return the sequence of the types of all open elements, from the top down.
For example, C<html/body/div/div/ul/li/p/i>.

=item * B<getCurrentLanguage>()

Return the present (possibly inherited) value of C<xml:lang>.

=item * B<getDepth>()

Return how many elements are presently open.

=item * B<queueAttribute(name, value)>

Add an attribute, to be issued with the next start-tag.
If an attribute called I<named> is already queued, replace it.

=item * B<getQueuedAttributes>()

Return all queued attributes (if any) as an attribute string.
They are not cleared. This is typically only called internally.

=item * B<clearQueuedAttributes() >

Discard any queued attributes.


=item * B<openElements(theList)>

Call I<openElement>() on each item of I<theList>.
Each such item should be a list or tuple of up to 4 items,
which are just  passed on as the arguments to I<openElement>.

=item * B<openElement(type, attrs=None, makeEmpty=False, nobreak=False)>

Open an instance of the specified element I<type>.
If I<attrs> is specified, it may be a ready-to-use attribute string, or
a Python dict (whose values will be escaped).

(method C<dictToAttrs>() can be used to turn any appropriate Python dict
into an attribute list).

If there are queued attributes (see I<queueAttribute>()), they are
also issued and then de-queued.

If I<makeEmpty> is specified and true, the element is written as an empty
element (and thus does not remain on the open-element stack).

If I<nobreak> is specified and true, the tag is not followed by a
line-break even if it normally would.

=item * B<openElementUnlessOpen(gi, attrs=None, nobreak=False)>

Works like I<openElement>(), except that it does nothing it the element
is I<already> open (it need not be the innermost/current open element).

=item * B<openElementUnlessCurrent(gi, attrs=None, nobreak=False)>

Works like I<openElement>(), except that it does nothing it the element
is the innermost/current open element.

=item * B<dictToAttrs(dct, sortAttrs=False, normValues=False)>

This is used by C<openElement> and its kind, if you pass them attributes
as a Python dict, rather than an attribute string. It turns the dict
into an attribute list. The values will be escaped as needed (there is not
provision for telling it I<not> to escape them), and assembled with a
single space before each attribute (even the first!), no spaces around "=",
and double quotes around the values. If you set I<sortAttrs> to True,
the attributes will be concatenated in alphabetical order.
If you set I<normValues> to True, each value will be processed by
I<normalizeSpace>(). This method can also be called directly if desired.

=item * B<closeElement(type, nobreak=False)>

Close the specified element.
If I<type> is not open at all, a warning is issued and nothing is closed.
If I<type> is open but is not the innermost/current open element,
a warning is issued and all elements out to  and including it are closed.

If I<type> is omitted, the innermost element is closed regardless of type.

B<Note:> To close an element even if there are other
elements also close, and avoid the warning, use I<closeThroughElement>().

=item * B<closeAllElements>(nobreak=False)

Close all open elements.

=item * B<closeToElement(type, nobreak=False)>

Close down to, but not including, the specified element.
If the element is not open, nothing happens.

=item * B<closeThroughElement(type)>

Close down to and including, the specified element.
If the element is not open, nothing happens.

=item * B<howManyAreOpen(typelist)>

Return the number of instances of the listed element types that are open.
I<typelist> may be a string (which will be split to tokens), or a list.

=item * B<closeAllOfThese(typelist)>

Close all instances of any element types in the (space-delimited)
list I<typelist>.

=item * B<adjustToRank(n)>

This is for structures which do not have a depth number as part of
the element type name, but do nest. For example, the HTML C<div> element.
The recursive element type is specified by the I<divTag> option.

It is intended to make it easy to build such nested/container structures,
even when your input only has (non-nested) headings (like much HTML), or
you don't want to track levels, instead creating items at whatever level
is needed at any given moment.

This method closes elements down to and including the I<n>th
nested "div" (if any); then it opens divs (automatically adding a
I<class="level_X"> attribute to each, until I<n> are open. This leaves
everything ready for writing a div title (or in HTML, Hn heading).
If you are already at level I<n> it closes the div and opens a new one.
If you are nested deeper, the deeper stuff is closed first.
And if you aren't that deep, it opens as many "div"s as needed.
The default name is "div", but you can change that via the I<divTag> option.


=item * B<setOutput(self, pathOrHandle, version="1.0", encoding="utf-8")>

Opens the requested file (or StringIO instance), and sets the values
for the XML Declaration parameters I<version> and I<encoding>. Either or both
of the last two can be set to '' or None, to indicate that they should be
entirely omitted from the XML Declaration. This is mainly
to accommodate C<lxml>, which apparently has issues with I<encoding>
(see L<https://stackoverflow.com/questions/2686709/>).

=item * B<startDocument>(doctypename, publicID="", systemID="")

You can call this to do I<makeXMLDeclaration>() and I<makeDoctype>().
See also I<endDocument>().

=item * B<startHTML(version, title="")>

Shorthand for getting you from start to having C<body> open.
I<version> should be one of "4strict", "4transitional" (or just "4"), "xhtml",
or "html5". In all but the last, an XML declaration is issued. Then the
DOCTYPE, html, head, a title, end head, and body.

=item * B<endDocument>()

Do a closeAllElements(), and then close the output file.
See also I<startDocument>() and I<startHTML>().

=item * B<makeXMLDeclaration(self)>

Issue an XML declaration. I<version> and/or I<encoding> are generated
in accord with the latest setting from C<setOutput>(), which can include
setting them to C<None> in order to suppress them.

=item * B<makeDoctype(doctypename, publicID="", systemID="")>

Output a DOCTYPE declaration.
Also calls C<makeXMLDeclaration()> if it hasn't been called already,
unless both I<publicID> and I<systemID> are explicitly set to C<None>.

=item * B<makeEmptyElement(type, attrs)>

Output an XML empty element of the given element I<type> and I<attributes>.
Queued attributes (if any) are also applied.

=item * B<makeSmallElement(type, attrs, text)>

Output a complete XML element of the given element I<type> and I<attributes>,
containing the given I<text>.
Queued attributes (if any) are also applied.

=item * B<makeComment(text)>

Output an XML comment. I<text> is escaped as needed.

=item * B<makeText(text)>

Output I<text> as XML content. XML delimiters are escaped as needed,
unless you unset the I<escapeText> option.
If you set the I<ASCIIOnly> option, all non-ASCII characters
are turned into character references.

=item * B<makeRaw(text)>

Dumps I<text> to the output, with no escaping, no stack management, etc.
This is usually a bad idea, but just in case....

=item * B<makePI(target, text)>

Create a Processing Instruction directed to the specified I<target>,
with the given I<content>. I<text> is escaped as needed.

=item * B<makeCharRef(e, printIt=True)>

Create and return an entity or character reference, from an integer or
name (the name is not required to be one of the HTML 4 or XML predefined
entities, but must consist only of XML Name characters).
Unless C<printIt> is set false, also print it.
If I<e> is numeric, it results in a 4-digit (or more if needed),
hexadecimal or decimal (according to the 'entityBase' setting),
numeric character reference.
Otherwise I<e> is treated as an entity name. It is I<not> required to
be a known HTML entity name.

=item * B<normalizeTag(tag)>

Given a complete start (or empty) tag, normalize it to canonical XML
form. That is, normalize whitespace, and alphabetize the attributes.

=item * B<doPrint(s)>

Write I<s> literally to the output (this is mainly used internally).
No escaping is done. If you use this method (or I<makeRaw()>, which just
calls it), all bets are off as far as producing well-formed XML.

=item * B<fixName(name)>

Ensure that the argument is a valid XML NAME.
Any other characters become "_".

=item * B<escapeXmlContent>(s)

Escape XML delimiters as needed in text content.

=item * B<normalizeSpace>(s)

Do the equivalent of XSLT's normalize-space() function on I<s>.
That is, remove leading and trailing whitespace, and reduce any internal
runs of whitespace to a single regular space character.

=item * B<escapeURI>(s)

Escape non-URI characters in C<s> using the URI %xx convention.
If the I<iri> option is set, don't escape chars just because they're
non-ASCII; only escape URI-prohibited ASCII characters.
See also options I<URIchars> and I<escapeHREFs>.


=item * B<escapeXmlAttribute(s)>

Escape the string I<s> to be acceptable as an attribute value
(removing <, &, and "). If the I<ASCIIOnly> option is set, escape non-ASCII
characters in I<s> as well.

=item * B<escapeNonASCII(s)>

Replace any non-ASCII characters in the text with entity references.

=item * B<sysgen>()

Returns a unique identifier each time it's called. You can control the
prefix applied, via the I<sysgenPrefix> option.
Other than the prefix, this just generates a counter.

=back


=head1 Known bugs and limitations

Should hook up to XML::DOM so you can just write out a subtree in one step, or
create an actual DOM with no "writing" per se.

Doesn't know anything about namespaces (should at least track which ones
are declared and in effect, unify prefixes, avoid nested re-declarations, etc).

Automation of C<xml:lang> attributes is not finished.

Pretty-printing is incomplete. For example,
I<breakAttrs> does not put breaks between attributes that are
specified via the second argument to I<openElement>() and its kin. To get
those breaks, use I<queueAttribute>() instead.

Perhaps add an I<insertFile>(escape=True) method?

Doesn't know anything about conforming to a particular schema.

=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see L<http://creativecommons.org/licenses/by-sa/3.0>.

For the most recent version, see L<http://www.derose.net/steve/utilities> or
L<http://github.com/sderose>.

=head1 Options


=head1 History

*Ported from Perl original written 2010-12-22 by Steven J. DeRose.
*2012-01-10 sjd: Port to Python.
*2012-01-25 sjd: Clean up. Redo options.
*2012-12-21 sjd: More work on porting.
*2015-04-03: Make escaping to ASCII option work for all contexts.
Add HTMLEntities option.
*2015-06-02: More port. pylint. escaping comments, pis, uris. entities.
*2018-06-01: Hook up to StringIO.
*2018-07-16: Add entityBase.
*2018-07-21: Add startHTML(), openElements(). Separate makeXMLDeclaration().
*2018-09-12: Add normalizeTag().
*2018-10-15: Fix encoding/version options to allow None. Better self-test.
Allow either string or real list for rest of name-lists. Fix bug in
dictToAttrs() and use it in getQueuedAttributes().
*2018-11-15: Set encoding even when output file is already open. Clean msgs.
Fix py 2/3 for htmlentitydefs. Add startDocument(). Check output for
illegal control characters. self.encoding vs. options['oencoding']!
*2019-12-11: Start adding support to directly create a DOM.

=head1 To do
*    Add shorter synonyms? open/close/empty/small/text/current/isopen
*    Do fancier indenting.
*    Option to omit inheritable xml:lang and xmlns attributes.
*    Div interpolation? See cleanMediaWiki.py:DivWrapper.
*    Possibly add a MECS option with extended open/close semantics?

=cut
"""

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    from htmlentitydefs import codepoint2name
    #import HTMLParser
    string_types = basestring
else:
    from html.entities import codepoint2name
    #from html.parser import HTMLParser
    string_types = str
    def unichr(n): return chr(n)

__version__ = "2019-12-11"

def uwarn(m):
    sys.stderr.write(m+"\n")

class XmlOutput:
    def __init__(self, HTMLEntities=False, encoding="utf-8", makeDOM=False, out=None):
        self.outputFH         = None
        self.theDOM           = None
        if (makeDOM): self.theDOM = xml.dom.minidom.Document()
        elif (out):  self.outputFH = out
        else: self.outputFH = sys.stdout

        self.xmlVersion       = "1.0"
        self.didXMLDcl        = False
        self.tagStack         = []
        self.langStack        = []

        self.queuedAttributes = {}

        # Lists of elements to treat specially
        self.spaceSpecs       = {}          # elementType: nNewlines
        self.cantRecurse      = {}          # Cannot contain themselves
        self.inlines          = {}          # Treat as inline (not newlines)
        self.empties          = {}          # Treat as empty
        self.suppressed       = {}          # Don't write at all

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
        return(None)

    def setOutput(self, pathOrHandle, version="1.0", encoding=None):
        """Use this to determine where stuff goes. You can write either to
             file (specified by path or a handle), or to a string by
             using Python's StringIO class. You can pass encoding=None to
             prevent writing any encoding at all in the XML declaration.
        """
        if (encoding): self.setOption('encoding', encoding)
        self.xmlVersion = version

        if (isinstance(pathOrHandle, string_types)):
            #uwarn("setOutput for path '%s'" % (pathOrHandle))
            try:
                self.outputFH = codecs.open(
                    pathOrHandle, 'wb', encoding=self.getOption('encoding'))
            except IOError as e:
                uwarn("Failed to open '%s': %s (encoding %s):    \n%s" %
                    (pathOrHandle, e, self.getOption('encoding'), e))
                return False
        else:
            # https://stackoverflow.com/questions/4374455/
            #uwarn("setOutput for handle '%s'" % (pathOrHandle))
            if (PY2):
                self.outputFH = codecs.getwriter(self.getOption('encoding'))(pathOrHandle)
            else:
                self.outputFH = pathOrHandle
                pathOrHandle.reconfigure(encoding=self.getOption('encoding'))
        return True

    def getOption(self, oname):
        assert (oname in self.options)
        return(self.options[oname])

    def setOption(self, oname, ovalue):
        assert (oname in self.options)
        self.options[oname] = ovalue

    def setSpace(self, enames, nNewlines):
        """Determine how many newlines get inserted before particular
        element types for output.
        @param enames: Element types, in a list or space-separated string.
        @param nNewlines: How many newlines to put before any of these.
        """
        if (isinstance(enames, string_types)):
            enames = re.split(r'\s+', enames)
        for e in (enames):
            self.spaceSpecs[e] = nNewlines

    def setInline(self, enames):
        """Define the listed names as 'inline' tags, which mainly affects
        whether we put linebreaks around them in pretty-printing.
        @param enames: Element type names, either as a list or in a
        white-space-separated string.
        """
        if (isinstance(enames, string_types)):
            enames = re.split(r'\s+', enames)
        for e in (enames):
            self.inlines[e] = 1

    def setEmpty(self, enames):
        if (isinstance(enames, string_types)):
            enames = re.split(r'\s+', enames)
        for e in (enames):
            self.suppressed[e] = 1

    def setCantRecurse(self, enames):
        """Define the listed names as no containing themselves.
        """
        if (isinstance(enames, string_types)):
            enames = re.split(r'\s+', enames)
        for e in (enames):
            self.cantRecurse[e] = 1

    def setSuppress(self,enames):
        if (isinstance(enames, string_types)):
            enames = re.split(r'\s+', enames)
        for e in (enames):
            self.suppressed[e] = 1

    def setHTML(self):
        """Set the list of known inline and non-recursive tags as for HTML.
        """
        self.setInline(
          "A ABBR ACRONYM B BASEFONT BDO BIG CENTER CITE CODE DFN DIR " +
          "EM FONT I IMG INPUT LABEL LEGEND KBD OPTGROUP OPTION " +
          "Q S SAMP SELECT SMALL SPAN STRIKE STRONG SUB SUP TEXTAREA TT U VAR")
            # Sometimes inline:
            #   APPLET BUTTON DEL IFRAME INS MAP OBJECT SCRIPT"
        self.setCantRecurse(
          "BR HR HEAD BODY H1 H2 H3 H4 H5 H6 IMG INS P PRE DEL")
        self.options["divTag"] = "DIV"

    def startHTML(self, version, title=""):
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
        if (version == 'xhtml'):
            self.queueAttribute('xmlns', "http://www.w3.org/1999/xhtml")
        self.openElement("html")
        self.openElement("head")
        self.openElement("meta",
            { 'http-equiv':"content-type", 'content':"text/html; charset=utf-8"
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

    def getIndentString(self, newline=True, offset=0):
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
        element types listed in 'giList' (which may be a Python list, or
        a string of whitespace-separated names). If omitted or None,
        returns the same thing as getDepth().
        """
        if (not giList):
            return(self.getDepth())

        if (isinstance(giList, string_types)):
            giList = re.split(r'\s+',giList)
        nOpen = 0
        for i in (range(0,self.getDepth())):
            for j in (range(0,len(giList))):
                if (giList[j] == self.tagStack[i]):
                    nOpen += 1
                    break
        return(nOpen)


    ###########################################################################
    # ATTRIBUTE QUEUEING
    #
    def queueAttribute(self, aname, avalue):
        """Add an attribute-value pair, to be issued with the next generated
        start-tag (in addition to any that are passed at that time. After
        being issued, the queued attributes are cleared.
        """
        if (aname in self.queuedAttributes):
            uwarn("queueAttribute: Attribute '" + aname + "' already queued.")
        self.queuedAttributes[aname] = ""
        if (avalue):
            avalue = "%s" % (avalue)
            self.queuedAttributes[aname] = self.escapeXmlAttribute(avalue)

    def getQueuedAttributes(self):
        """Return an attribute string including all the queued attributes
        (if any), plus a leading space.
        """
        return self.dictToAttrs(self.queuedAttributes)

    def clearQueuedAttributes(self):
        self.queuedAttributes = {}


    ###########################################################################
    ####### OPEN
    #
    def openElements(self, theList):
        """Call openElement() for each item of theList.
        Each such item can be a name or a tuple of up to 4 items, which
        are just passed on.
        """
        if (isinstance(theList, string_types)):
            theList = re.split(r'\s+', theList)
        for stuff in (theList):
            if (isinstance(stuff, string_types)):
                self.openElement(stuff)
            else:
                self.openElement(*stuff)
        return

    def openElement(self, gi, attrs=None, makeEmpty=False, nobreak=False):
        """Start a new XML element by issuing the start-tag. Add to stack.
        'attrs' may be a string or a dict.
        With 'makeEmpty', make it an empty element.
        'nobreak' suppresses any newline after the start-tag.
        """
        if (gi in self.cantRecurse):
            while(self.howManyAreOpen(gi) > 0):
                self.closeElement()
        extra = 0
        if  (gi in self.spaceSpecs):
            if (self.options["breakSTAGO"] and gi not in self.inlines):
                extra = self.spaceSpecs[gi]
        if (extra>0):
            self.doPrint(("\n " * extra) + self.getIndentString(newline=False))

        out = ""
        if (self.options['indent']): out += self.getIndentString()
        out = "<" + gi
        if (isinstance(attrs, dict)):
            attrs = self.dictToAttrs(attrs)
        if (attrs):
            if (self.options["breakAttrs"]):
                out += self.getIndentString()
            out += " " + attrs
        out += self.getQueuedAttributes()
        #uwarn("\n***** %s *****" % (out))

        self.clearQueuedAttributes()

        if (makeEmpty):
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

    def openElementUnlessOpen(self, gi, attrs="", nobreak=False):
        if (self.howManyAreOpen(gi) > 0): return
        self.openElement(gi, attrs, nobreak)


    def openElementUnlessCurrent(self, gi, attrs="", nobreak=False):
        if (self.getCurrentElementName() == gi): return
        self.openElement(gi, attrs, nobreak)


    def dictToAttrs(self, dct, sortAttrs=False, normValues=False):
        """Turn a dict into an attribute list.
        """
        if (self.options["breakAttrs"]):
            sep = self.getIndentString()
        else:
            sep = " "
        anames = dct.keys()
        if (sortAttrs): anames.sort()
        attrString = ""
        for a in (anames):
            v = dct[a]
            if (normValues): v = self.normalizeSpace(v)
            attrString += "%s%s=\"%s\"" % (sep, a, self.escapeXmlAttribute(v))
        return attrString

    ###########################################################################
    ####### CLOSE
    #
    def closeElement(self, gi="", nobreak=0):
        """Close the current XML element and remove from the stack.
        If 'gi' is passed, it must match the element to be closed.
        A warning is issued if any attributes remain queued.
        """
        if (self.getDepth() <= 0):
            uwarn("closeElement(): No ('%s') or anything else open." % (gi))
            return
        if (not gi):
            gi = self.getCurrentElementName()

        if (gi and gi != self.getCurrentElementName()):
            uwarn("closeElement(): '%s' is not the current element (stack: %s)."
                % (gi, self.getCurrentFQGI()))
            return

        if (len(self.queuedAttributes)):
            uwarn("closeElement(): Should not be these queued attributes: '" +
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

    def closeAllElements(self, nobreak=False):
        """Close all open elements.
        """
        while (self.getDepth()):
            self.closeElement(nobreak=nobreak)

    def closeToElement(self, gi, nobreak=False):
        """Close elements up to but not including the 'gi' specified.
        If more than one of 'gi' is open, close only to the innermost.
        """
        if (self.howManyAreOpen(gi) == 0): return
        while (self.getDepth()):
            if (self.getCurrentElementName() == gi): break
            self.closeElement(nobreak=nobreak)

    def closeElementIfOpen(self, gi="", nobreak=False):
        """Close through element 'gi' if there is one open, else do nothing.
        """
        self.closeThroughElement(gi, nobreak)

    def closeThroughElement(self, gi, nobreak=False):
        """Close elements up to AND including the innermost 'gi' specified.
        """
        if (self.howManyAreOpen(gi) == 0): return
        while (self.getDepth()):
            cur = self.getCurrentElementName()
            self.closeElement(nobreak=nobreak)
            if (cur == gi): break

    def closeAllOfThese(self, giList, nobreak=False):
        """Call this with a list of space-separated element type names,
        to make sure all instances of any of those element types are closed.
        """
        #giList = re.split(r'\s+',giList)
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
    def startDocument(self, documentElement, publicID="", systemID=""):
        self.makeXMLDeclaration()
        self.makeDoctype(documentElement=documentElement,
            publicID=publicID, systemID=systemID)

    def endDocument(self):
        self.closeAllElements()
        if (self.outputFH and self.outputFH != sys.stdout):
            self.outputFH.close()
            self.outputFH = None

    def makeXMLDeclaration(self):
        ver = enc = ""
        if (self.xmlVersion): ver = ' version="%s"' % (self.xmlVersion)
        if (self.getOption('encoding')): enc = ' encoding="%s"' % (self.getOption('encoding'))
        self.doPrint('<?xml%s%s?>' % (ver, enc))
        self.didXMLDcl = True

    def makeDoctype(self, documentElement, publicID="", systemID=""):
        if (publicID is None and systemID is None):  # Hack for HTML5.
            self.doPrint('<!DOCTYPE %s>' % (documentElement))
        else:
            if (not self.didXMLDcl): self.makeXMLDeclaration()
            self.doPrint('<!DOCTYPE %s PUBLIC "%s" "%s" []>' %
                (documentElement, publicID, systemID))

    def makeEmptyElement(self, gi, attrs=""):
        self.openElement(gi, attrs, 1)

    def makeSmallElement(self, gi, attrs="", text=""):
        if (attrs and not re.match(r"""\w+\s*=\s*('[^']*'|"[^"]*")""", attrs)):
            uwarn(
              "Bad attribute string arg to makeSmallElement: '" + attrs + "'")
        self.openElement(gi, attrs=attrs, nobreak=1)
        self.makeText(text)
        self.closeElement(gi)

    def makeComment(self, text):
        self.doPrint(self.getIndentString() + "<!-- %s -->" %
            (self.escapeXmlComment(text)))


    def makeText(self, text):
        if (self.options["suppressWSN"] and re.match(r'\s*',text)):
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


    def makeCharRef(self, nameOrNumber, printIt=True):
        """Make an entity or named character reference.
        """
        if (type(nameOrNumber) == int or re.match(r'\d+$', nameOrNumber)):
            n = int(nameOrNumber)
            if (self.options['entityBase'] == 10): rc = "&#%04d;" % (n)
            else: rc = "&#%04x;" % (n)
        elif (re.match(r'[-:.\w]+$', nameOrNumber, re.UNICODE)):
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
        See XMLConstructs.py for regexes.
        """
        if (XmlOutput.xcObj is None):
            from XMLConstructs import XMLConstructs
            XmlOutput.xcObj = XMLConstructs()
        if (not re.match(XmlOutput.xcObj.x['stag'], tag)):
            raise ValueError("Not an XML start-tag: '%s'." % (tag))
        mat = re.match(r'<(\S+)', tag)
        typeName = mat.group(1)
        attrDict = {}
        for mat in re.finditer(XmlOutput.xcObj.x['attr'], tag):
            attrDict[mat.group(2)] = mat.group(3)
        return "<%s %s>" % (typeName, self.dictToAttrs(
            attrDict, sortAttrs=True, normValues=True))


    ###########################################################################
    # All XML output goes through here.
    #
    def doPrint(self, x):
        assert (self.outputFH != None)
        #uwarn("%s==>%s<==" % (self.outputFH, x))
        if (self.getDepth()):
            fqgi = self.getCurrentFQGI()
            for gi in (re.split(r'/', fqgi)):
                if (gi in self.suppressed):
                    return
        if (PY2 and self.options["encoding"]):
            x = x.encode(self.options["encoding"])
        if (self.options["checkCharset"]):
            mat = re.search(r'([\x00-\x08\x0b\x0c\x0e-\x1F])', x)
            if (mat): raise ValueError(
                "Illegal C0 control character 0x%02x in '%s' (encoding: '%s')."
                    % (ord(mat.group(1)), x, self.options["encoding"]))
        if (self.outputFH): self.outputFH.write(x)


    ###########################################################################
    # ESCAPING
    #
    #
    def fixName(self, name):
        """Turn a string into a valid XML name (imperfect char set).
        """
        name = re.sub(r'[^-:._\w\d]', "_", name, re.UNICODE)
        if (name == "" or re.match(r'[-_:\d]', name)):
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
        s = re.sub(r'\s+', " ", s, re.UNICODE)
        return(s)

    def escapeXmlContent(self, s):
        """Don't use for escaping attribute values, that's different, see below).
        Quietly deletes any prohibited control characters!
        """
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'&',   "&amp;",  s)
        s = re.sub(r'<',   "&lt;",   s)
        s = re.sub(r']]>', "]]&gt;", s)
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
            theBytes = c.encode('utf-8')
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
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'&',  "&amp;", s)
        s = re.sub(r'<',  "&lt;", s)
        if (apostrophes):
            s = re.sub(r"'", "&apos;", s)
        else:
            s = re.sub(r'"', "&quot;", s)
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        if (self.options["escapeHREFs"] and
            re.match(r'(https?|mailto|ftp|local)://', s)):
            s = self.escapeURI(s)
        return(s)

    def escapeXmlPi(self, s):
        """Escape as needed for processing instructions.
        XML doesn't define a standard escaping for this, so I chose one.
        """
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'\?>',  "?&gt;", s)
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        return(s)

    def escapeXmlComment(self, s):
        """Escape as needed for comment.
        XML doesn't define a standard escaping for this, so I chose one.
        """
        s = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f]', "", s)
        s = re.sub(r'--',  u"\u2014", s)
        if (self.options["ASCIIOnly"]):
            s = self.escapeNonASCII(s)
        return(s)

    def escapeNonASCII(self,s):
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

    ###########################################################################
    #
    def sysgen(self):
        self.sysgenCounter = self.sysgenCounter + 1
        return(self.options["sysgenPrefix"] + self.sysgenCounter)


###############################################################################
###############################################################################
#
if __name__ == "__main__":
    import argparse

    def processOptions():
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--encoding", "--oencoding", type=str, default='utf-8',
            help='What character encoding to use for the input.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files', type=str, nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')
        args0 = parser.parse_args()
        return(args0)

    def exercise(x, encoding=None):
        """Call a bunch of things for a basic smoke-test.
        """
        if (encoding != 'utf-8'):
            uwarn("\n******* WARNING: sys.stdout with encoding '%s'!\n\n" % (encoding))
        x.setOutput(sys.stdout, version="1.0", encoding=encoding)
        #x.setSpace(enames, code)
        x.setInline([ 'i', 'b', 'u', 'tt', 'a' ])
        x.setEmpty([ 'br', 'hr', 'img' ])
        x.setCantRecurse([ 'p' ])
        x.startDocument('html', publicID="-//foo", systemID="my.dtd")

        x.openElements([ 'html', 'head', 'style' ])
        x.makeComment("""
    body   { margin:36pt; }
    li     { color:#F00; margin-top:12pt; }
    """)
        x.closeElement('style')
        x.makeSmallElement('title', attrs=None, text="Some title text")
        x.closeElement('head')

        x.openElement('body')
        x.openElement('p', attrs="id='foo1'")
        x.makeText("A paragraph typically has some text. Like ")
        x.openElement('i', nobreak=1)
        x.makeText("this italic phrase")
        x.closeElement('i', nobreak=1)
        x.makeRaw(", or this ")
        x.openElement('b', nobreak=1)
        x.makeText("this bold phrase ")
        x.closeElement('b', nobreak=1)
        x.makeRaw(", or this ")
        x.openElement('u')
        x.makeText("this underline phrase ")
        x.closeElement('u')
        x.makeText("followed by 4 ellipses: ")
        x.makeCharRef(0x2026)
        x.makeCharRef(8230)
        x.makeCharRef('8230')
        x.makeCharRef('hellip')

        #print("Open elements %d, current isw '%s' (should be 3, 'p'). %s '%s'"
        #    % (x.getDepth(), x.getCurrentElementName(),
        #    x.getCurrentFQGI(), x.getCurrentLanguage()))
        x.closeElement('p')

        x.makePI('xmllint', 'foo=bar baz=? whoot=?>')

        x.makeSmallElement('p', text="Some brief paragraph text.")

        x.openElement('p')
        x.makeText("A paragraph typically has some text.")
        x.openElement('p')
        x.makeText("A paragraph after an unclosed one.")
        x.openElement('p')
        x.makeText("A paragraph after another unclosed one.")
        #print("paragraphs open: %d." % (x.howManyAreOpen('p')))
        x.closeAllOfThese('p')
        #print("paragraphs open now: %d." % (x.howManyAreOpen('p')))

        x.makeEmptyElement('hr', attrs="class='a'")

        x.queueAttribute('zork', 'zerg')
        x.clearQueuedAttributes()
        x.queueAttribute('id', 'queuedValue')
        x.queueAttribute('class', 'red green blue')
        #print("\n*** queued: %s ***" % (x.getQueuedAttributes()))
        x.openElement('p')
        x.makeText("This paragraph should have 2 queued attributes.")

        x.endDocument()

        #x.setSuppress(self,enames)
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
            uwarn("******* Unknown node type: %d" % (root.nodeType))
        return

    ####### MAIN #######
    #
    args = processOptions()

    if (not args.files):
        uwarn("******* Running smoke-test ******")
        exercise(xo, encoding=args.encoding)
    else:
        for path in (args.files):
            uwarn("\n\n" + ("#" * 79))
            uwarn("####### XmlOutput: '%s'" % (path))
            try:
                fh = codecs.open(path, 'rb', encoding=args.encoding)
                dom = html5lib.parse(fh, treebuilder="dom")
            except IOError:
                uwarn("    Cannot open or parse '%s'." % (path))
                continue

            xo.makeDoctype('HTML')
            traverse(dom.documentElement)
            xo.endDocument()

    if (not args.quiet):
        uwarn("\n******* Done *******")
