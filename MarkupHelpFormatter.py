#!/usr/bin/env python
#
# MarkupHelpFormatter.py (includes ParagraphHelpFormatter, too).
#
import os, sys, re, string
import argparse

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring
else:
    string_types = str
    def unichr(n): return chr(n)

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2013-04-18",
    'language'     : "Python 3.7",
    'version_date' : "2018-12-12",
}
__version__ = __metadata__['version_date']

descr = """

=head1 Description

This package defines two classes that can be used with Python's
I<argparse> package, in order to get better formatting.

=head2 class ParagraphHelpFormatter(argparse.HelpFormatter)

This simple class is like the default formatter except that
it does I<not> wrap lines across blank lines. That is, blank lines stay there.

To use it:
    parser = argparse.ArgumentParser(description=""
    First paragraph of documentation,
    which wraps to fill output lines.

    Second paragraph.
    ...
"",
    formatter_class=MarkupHelpFormatter
    )


=head2 class MarkupHelpFormatter(argparse.HelpFormatter)

This class is much fancier. It support several markup systems within
your help text. So you can indicate paragraphs, emphasis, special
characters, links, headings, and so on, and get distinctive formatting
for them. Some control of the styles to be applied is available.

To use it:
    parser = argparse.ArgumentParser(description=""

    ==Description==

    First paragraph of documentation,
    which wraps to fill output lines.

    Our sole virtue:

    *Surprise
    *Better formatting

    Our two virtues:
    *Surprise
    *Better formatting
    *An almost ''fanatical'' devotion to markup
    ...
"",
    formatter_class=MarkupHelpFormatter
    )

=head2 Supported Markup syntax(es)

In short, this class supports most of I<Markdown>, I<POD>, and
I<MediaWiki> markup (not including embedded HTML (yet)).
These are all styled using only the
capabilities of typical ANSI terminal programs, such as fixed-pitch
fonts, color, bold, and fiendishly clever use of whitepsace.

There is no support for images. Links are visually emphasized,
but do not function because I don't see any easy way to make C<bash>,
C<more>, C<less>, etc. deal with them. The user can of course copy
a URI from a link, and paste it into a browser or other URI-aware tool.
HTML output is in the works; once finished, you could use a browser to read
help, and it would support links as well as better formatting.


=head2 MediaWiki

B<MediaWiki> markup is what WikiPedia uses.
Most components are indicated by punctuation marks at the beginning of lines.
A description is available L<here|"http://www.mediawiki.org/wiki/Markup_spec">.

Paragraphs are simply separated by blank lines.

Headings are indicated by a number of leading and trailing "=" characters,
equal to the heading level plus 1.
For example, a second-level heading:

    === Summary ===

Block quotations are indicated by leading ">":

    >As Kierkegaard suggests,
    >Hume was not always, shall we say, perfectly clear.

Lists are indicated by one or more leading "*" or "#" characters,
for bulleted/unordered and for numbered/ordered, respectively.
There is no indicator marking the scope of lists as wholes (among other
things, this poses problems for adjacent or continued lists; but it's typical):

    * Things that float
    *# Apples
    *# Gravy
    *# Very small rocks
    *# Ducks
    * Things that sink
    *# Villagers
    *# Swamp castles

List items to be indented but neither bulleted nor numbered, begin with ":".

Definition list items are of the form ";term:definition".

Tables are not yet supported here, but work is in progress.
MediaWiki tables (see L<here|"https://www.mediawiki.org/wiki/Help:Tables">)
use "{|...|}" to enclose the entire table,
"|+" to indicate captions,
"|-" to separate rows,
and "|" to start cells within a row (or "!" instead of "|" for header cells).
Each cell must start on a new line.

Lines that should not be wrapped, such as program code samples,
should start with whitespace.

Horizontal rules can be invoked via a line starting with
several "=" or "-" characters.

Inline emphasis uses 2 and/or 3 apostrophes on each side:

    This ''word'' is '''really''' important to '''''me and you'''''.


=head3 MarkDown

B<MarkDown> is fairly common. For a description see
L<here|"http://daringfireball.net/projects/markdown/syntax">.
It is very similar to MediaWiki format.

Headings use "#" (verses MediaWiki's "="), and "#" is only needed at the
start, not the end, of heading lines.

Markdown systems sometimes also accept headings indicated
by "underlining" the heading using "=" or "-" on the next line.
That variant is not available here:

    Introduction
    ------------

Block quotations are indicated by a leading ">":

    >As Kierkegaard suggests,
    >Hume was not always, shall we say, perfectly clear.

Lists work like MediaWiki, except that the indicators
only include "*" for unordered and "+" for ordered (not "#").

Lines that should not be wrapped should start with whitespace.

Horizontal rules can be produced by giving a line starting with
several "=", "-", or "*" characters.

Inline emphasis uses "_" or "*" surrounding text:

    This word is *really* important to _me and you_.



=head2 POD

B<POD> is short for "Plain Old Documentation". A description is available at
L<here|"http://en.wikipedia.org/wiki/Plain_Old_Documentation">

POD reserves only "=" at start of line, where
a keyword follows. Some POD software (not including this class)
requires a blank line preceding any such component.
Some example components:

    =head2 Knightly challenges
    =over
    =item * Bravery
    =item * Chastity
    =item * Self-control
    =back
    =head2 Hummility and the omission of Gawain

Note that the boundaries of lists as wholes, must be indicated in
POD using "=over" and "=back" (which can also be used to control
indentation in general).

Paragraphs are indicated by blank lines just as in MediaWiki and MarkDown.

Inline emphasis of various kinds uses a capital letter
followed by the relevant text within pointy-brackets:

    B<hello>  for bold
    I<very>   for italic
    C<grep>   for program code or commands
    F</bin>   for filenames and paths
    L<Intro|"http:...">  for links (to section titles or to URIs). The part
before the "|" (if present) is the anchor text, and the part after it
is a URI or the title of some section in the same document (similar to
the MediaWiki "|" convention in links). Some processors require the 2nd
portion to be quoted.
    S<text>   should prevent line-breaking within I<text>
    X<key>    defines an index entry (unused here)
    Z<>       a "null" code; may be used, for example, to separate one
of these key letters from an immediately following "<":  "NZ<><4" for "N<4".

In case of conflict such as needing literal pointy-brackets within one
of these inline components, one may use <<...>> or <<<...>>>, etc.

Special characters can be encoded as E<name> for:
    The names 'lt' ("<"), 'gt' (">"), 'verbar' ("|") , and 'sol' ("/")
    HTML special character names,
    Character codes such as 0777 (octal), 0xFF (hexadecimal), or 999 (decimal).



=head1 Options available in MarkupHelpFormatter

A number of options are available, by which you can control how
markup is recognized and how components are formatted. The options
can be controlled with the "=set" command, which must appear at the
start of a line, followed by the name of the option to be set, and then
the value to set it to (boolean values use 0 or 1):

    =set pod 0

A few options have values that are lists, generally one for each
heading/section level. In those cases, a level number from 1 to 6
comes between the option name and the value to set.
For example, to make the text of first-level headings red:

    =set headFG 1 red

I expect to add a check for a config file (such as F<~/.MarkupHelpFormatter>),
which will simply be read first, to support global "=set" values.

=head2 Input capabilities and options

    Name          Default       Description
    "entities"    : True     -- expand HTML character entities and refs
    "backslashes" : False    -- expand Python-style backslash-codes
    "pod"         : True     -- recognize POD ("plain old doc") markup
    "mediawiki"   : True     -- recognize basic MediaWiki markup
    "markdown"    : True     -- recognize basic Markdown markup
    "mailEmph"    : True     -- recognize email-style emphasis
    "defs"        : True     -- recognize BNF-style grammar/deflist markup
    "tabSize"     : 4        -- interval of incoming tab-stops


=head2 Output capabilities and options

    Name          Default       Description
    "defaults"    : False    -- Show default values for argparse options
    "width"       : None     -- Window or "set" width (cf. $COLUMNS)
    "color"       : True     -- Use ANSI terminal color escapes
    "breakURIs"   : True     -- Allow newline after '/' in URIs
    "sectionNums" : True     -- Auto-number sections
    "indentSize"  : 4        -- List indentation increment
    "DLWidth"     : 12       -- Area left for definitions in deflists
    "OLPrefix"    : ""       -- Put before list-numbers
    "OLSuffix"    : ""       -- Put after list-numbers
    "OLTypes"     : [ "upper-roman", "upper-alpha", "decimal",
                      "lower-roman", "lower-alpha", "decimal" ]
    "linkColor"   : "blue"   -- Color to show links in
    "RFCformat"   : "https://tools.ietf.org/html/rfc%d" -- for [RFC3653] links
    "ULMarkers"   : [ "*", "-", "o", "." ]    # CSS: disc, circle, square, none

    # Following settings are arrays with entries for heading levels 1-6:
    "headFG"      : [ "blue",   "blue",   "blue",  "blue",  "blue",  "blue"  ]
    "headBG"      : [ "white",  "white",  "white", "white", "white", "white" ]
    "headPrefix"  : [ "\n\n\n", "\n\n\n", "\n\n",  "\n",    "\n",    "\n"    ]
    "headSuffix"  : [ "\n",     "\n",     "\n",    "\n",    "\n",    "\n"    ]

C<ULMarkers> should accept any Unicode strings; but backslash-x
or similar escapes for them are not yet supported.

C<RFCformat> is a format-string for use with Python's "%" operator. It is
used when a link reference such as "RFC1149" (or similar) is found.
The Python "%" operator is used to fill the RFC number into it and make
a complete URI. Sadly, many viewers (such as C<less>) do not have much or
any support for links. If, however, you convert the doc to HTML, the links
should convert fine and work in a browser.

Options can also be set directly from your Python code, for example:

    MarkupHelpFormatter.InputOptions["mediawiki"] = True

=head1 Using MarkupHelpFormatter in your Python programs

    import MarkupHelpFormatter
    parser = argparse.ArgumentParser(
        description='...',
        epilog='...',
        formatter_class=MarkupHelpFormatter
    )

If desired, you can also set options (see above), for example:

    MarkupHelpFormatter.InputOptions["mediawiki"] = True


=head2 Notes

It is good to export the environment variables $ROWS and $COLUMNS
via your F<.bashrc>, F<.bash_profile>, or similar setup file.
That way this and other programs know how big your terminal window
is, and can format accordingly. If these are not available,
the program will guess.

If you send the output to C<more>, you may
need to specify C<-r> to get color to work, and/or
fiddle with I<locale> for bullets and other Unicode to work.

This tool is not yet very polished, but I hope it will be useful.
Bug reports, fixes, and enhancements are welcome.

There are 3 class variables of interest, all dicts:

    MarkupHelpFormatter.DublinCoreMetadata -- info regarding this program.
    MarkupHelpFormatter.InputOptions -- options for the marked-up input.
    MarkupHelpFormatter.OutputOptions -- options for output formatting.


=head1 Known bugs and limitations

Tables are not yet supported.

Some details of MarkDown, such as "underlined" headings, are not supported.

The program does not try to figure out just which ANSI terminal
capabilities your terminal program supports. For example, a few
support italics, blinking text, 256 colors, or even multiple fonts.
The default formatting avoids uncommon capabilities. You can get at
some others via "=set" (see above).


=head1 Authorship and rights

This program is Copyright 2014-2015 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see L<here|"https://creativecommons.org">.

For the most recent version, see L<http://www.derose.net/steve/utilities/> or
L<http://github/com/sderose>.

Thanks to Anthon van der Neut for help on integrating with argparse. Also:
    http://stackoverflow.com/questions/3853722
    https://bitbucket.org/ruamel/std.argparse/src
    http://hg.python.org/cpython/file/2.7/Lib/argparse.py
    https://docs.python.org/2/library/textwrap.html

=head1 To do

*  More testing, especially __main__ and Unicode.
*  Preserve spaces within quotes and in indented/pre lines.
*  Prematurely breaks lines sometimes; problem with uncoloredLength()?
Or may not be removing pre-existing LFs right.
*  Finish sectionNums. Clear list-numbering properly
*  Add MarkDown and Mediawiki Deflist, Blockquote
*  Support hanging indent on lists
*  Indent paragraph immediately following list-item? At least for POD
*  Option to reset colors for light background (let =SET refer env. vars?)
*  Integrate mathUnicode.py to get fancy forms.

=head2 Low priority

*  Support backslash+x etc. in =set ULmarkers.
*  Option to break URIs and paths at '/' doesn't always work
*  Option to page the output, or send to 'less'
*  Finish XHTML output option (and browser as pager)
*  Is there an easy way to check if terminal supports underlining, etc.?
*  How best to support links?
*  Support POD's Z<> (suppress POD) markup
*  Once HTML generation is done, add =set for css and js to include.
"""

verbose = 0
esc = chr(27)
specialChars = {
    "lsquo":   unichr(0x2018),    "rsquo":   unichr(0x2019),
    "ldquo":   unichr(0x201C),    "rdquo":   unichr(0x201D),
    "lsaquo":  unichr(0x2039),    "rsaquo":  unichr(0x203A),
    "ldaquo":  unichr(0x00AB),    "rdaquo":  unichr(0x00BB),

    "endash":  unichr(0x2013),    "emdash":  unichr(0x2014),
    "shy":     unichr(0x00AD),    "hypoint": unichr(0x2027),
    "hyminus": unichr(0x002D),

    "ensp":    unichr(0x2002),    "emsp":    unichr(0x2003),
    "thinsp":  unichr(0x2009),    "hairsp":  unichr(0x200A),
    "zerosp":  unichr(0x200B),    "nbsp":    unichr(0x00A0),

    "lt": '<', "gt": '>', "apos": "'", "quo": '"', "amp": '&',
    }

# List of enough Roman numerals.
# Cf bingit/CCEL/CCEL3DBMakers/makeReferenceTables/makeRomanNumeralRef.sq
#
romans = [ "",
    'i', 'ii', 'iii', 'iv', 'v',
    'vi', 'vii', 'viii', 'ix', 'x',
    'xi', 'xii', 'xiii', 'xiv', 'xv',
    'xvi', 'xvii', 'xviii', 'xix', 'xx',
    'xxi', 'xxii', 'xxiii', 'xxiv', 'xxv',
    'xxvi', 'xxvii', 'xxviii', 'xxix', 'xxx',
    'xxxi', 'xxxii', 'xxxiii', 'xxxiv', 'xxxv',
    'xxxvi', 'xxxvii', 'xxxviii', 'xxxix', 'xl',
    'xli', 'xlii', 'xliii', 'xliv', 'xlv',
    'xlvi', 'xlvii', 'xlviii', 'xlix', 'l',
    'li', 'lii', 'liii', 'liv', 'lv',
    'lvi', 'lvii', 'lviii', 'lix', 'lx',
    'lxi', 'lxii', 'lxiii', 'lxiv', 'lxv',
    'lxvi', 'lxvii', 'lxviii', 'lxix', 'lxx',
    'lxxi', 'lxxii', 'lxxiii', 'lxxiv', 'lxxv',
    'lxxvi', 'lxxvii', 'lxxviii', 'lxxix', 'lxxx',
    'lxxxi', 'lxxxii', 'lxxxiii', 'lxxxiv', 'lxxxv',
    'lxxxvi', 'lxxxvii', 'lxxxviii', 'lxxxix', 'xc',
    'xci', 'xcii', 'xciii', 'xciv', 'xcv',
    'xcvi', 'xcvii', 'xcviii', 'xcix', 'c',
]

def getRoman(n):
    """Convert to Roman numerals. Limited range.
    """
    #return( 'x' * int(n/10) + romans[n % 10])
    return romans[n]

colors = { # ANSI terminal codes. Background is +10. Switch to ColorManager.py?
    "black"     : 30,
    "red"       : 31,
    "green"     : 32,
    "yellow"    : 33,
    "blue"      : 34,
    "magenta"   : 35,
    "cyan"      : 36,
    "white"     : 37,
    "default"   :  0,
    "bold"      :  1,
    "underline" :  4,
}
colorRegex    = re.compile(r'\x1b\[\d+(;\d+)*m')
colorEnd = esc + "[0m"

def colorize(s, fg="default", bg="default", bold=0):
    fgnum = colors[fg]
    cc = []
    if (fg!="default"):
        cc.append(str(fgnum))
    if (bg!="default"):
        bgnum = colors[bg] + 10
        cc.append(str(bgnum))
    if (bold):
        cc.append('1')
    ccstring = ";".join(cc)
    return(esc + "[" + ccstring + "m" + s + colorEnd)

def hMsg(level, msg):
    if (verbose>=level): sys.stderr.write("\n*******" + msg+'\n')

def vMsg(level, msg):
    if (verbose>=level): sys.stderr.write(msg+'\n')

def makeDispayedLines(lines):
    assert (isinstance(lines, list))
    buf = ""
    for line in lines:
        buf += "    >>>%s\n" % (re.sub(r'([\x01-\x20])', toPix, line))
    return buf

def toPix(mat):
    """Make control chars and space visible.
    """
    return unichr(0x2400 + ord(mat.group(1)))


##############################################################################
#
class outHTML:
    """Support outputting HTML markup (currently unused).
    """
    def __init__(self, xml=True, dest=None, pretty=True, sign=True):
        self.dest = dest
        self.pretty = pretty
        self.sign = sign
        self.xml = xml
        self.tagStack = []

    def start(self):
        if (self.dest):
            self.dest.write("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
""")
        self.openElement("html", 'xmlns="http://www.w3.org/1999/xhtml"')
        self.openElement("head")
        self.emptyElement("meta",
            'http-equiv="content-type" content="text/html; charset=utf-8"')
        if (self.sign):
            self.emptyElement("meta",
                'name="generator" value="MarkupHelpFormatter.py"')
        self.openElement("title")
        self.text("Python help information")
        self.closeElement("title")
        self.closeElement("head")
        self.openElement("body")

    def end(self):
        while (self.tagStack):
            self.closeElement()

    def openElement(self, tag, attrs=None, empty=False):
        """In future, use this to support XHTML output.
        """
        self.tagStack.append(tag)
        if (not self.dest): return
        buf = "<" + tag
        if (isinstance(attrs, string_types)):
            buf += " " + attrs
        elif (isinstance(attrs, dict)):
            for a, v in attrs.items(): buf += ' %s=\"%s\"' % (a, v)
        if (empty): buf += "/"
        buf += ">"
        if (self.pretty): buf = "\n" + ("  " * len(self.tagStack)) + buf
        self.dest.write(buf)

    def emptyElement(self, tag, attrs=""):
        self.openElement(tag, attrs, empty=True)

    def text(self, txt):
        if (not self.dest): return
        txt = re.sub(r'&', '&amp;', txt)
        txt = re.sub(r'<', '&lt;', txt)
        self.dest.write(txt)

    def closeElement(self, tag=None, required=False):
        if (not tag):
            tag = self.tagStack[-1]
        elif (tag not in self.tagStack):
            if (required): vMsg(1,
                "MarkupHelpFormatter: closing '%s' but stack is [ %s ]." %
                (tag, "/".join(self.tagStack)))
            return(False)
        while (len(self.tagStack)):
            curTag = self.tagStack[-1]
            if (self.dest): self.dest.write("</%s>" % curTag)
            self.tagStack.pop()
            if (curTag == tag): break
        return(True)

    def isOpen(self, tag):
        return(tag in self.tagStack)


##############################################################################
#
class ParagraphHelpFormatter(argparse.HelpFormatter):
    """
A formatter for argparse. This differs from the default formatter, in that
it does *not* wrap lines across blank lines. That is, blank lines stay there.
See below for a class that actually supports simple markup.
"""
    DublinCoreMetadata = {
        "coverage"      : "",
        "contributor"   : "",
        "creator"       : "Steven J. DeRose",
        "date"          : "2015-03-10",
        "description"   :
            "Formatter class for Python argparse with blank line support",
        "format"        : "Unicode text file",
        "identifier"    : "MarkupHelpFormatter.pm/ParagraphHelpFormatter",
        "language"      : "programming:Python",
        "publisher"     : "Steven J. DeRose",
        "relation"      : "",
        "rights"        : "CCLI Attribution-Share-Alike",
        "source"        : "http://www.derose.net",
        "subject"       : "Computer program -- Python -- help formatter",
        "title"         : "ParagraphHelpFormatter",
        "type"          : "Python 2.7 class",
    }

    def __init__(self, *args, **kw):
        super(ParagraphHelpFormatter, self).__init__(args, kw)
        self._add_defaults = False
        super.__init__(*args, **kw)

    def _format_text(self, txt):
        """Called only for 'descr' (but multiple times??)"""
        vMsg(1, ">>>In ParagraphHelpFormatter._format_text(), passed %s<<<" %
            (type(txt)))
        ### Should force/ensure utf-8 here.
        #buf = super(MarkupHelpFormatter, self)._format_text(txt))
        buf = self.format(txt)
        return(buf)
        # calls _fill_text

    def format(self, s, encoding="utf8", color=1, width=0):
        """Wrap each blank-line-separated part of the string separately, then
        re-assemble them still with blank lines between.
        """
        assert (isinstance(s, str))
        hMsg(1, "Entering ParagraphHelpFormatter.format().")
        paras = re.split(r"\n[ \t]*\n, s")
        wrappedParas = []
        for para in paras:
            wrappedParas.append(super.wrap(para, width))
        return(u"\n\n".join(wrappedParas).encode(encoding))



##############################################################################
#
class MarkupHelpFormatter(argparse.HelpFormatter):
    """
A formatter for argparse. See further documentation at the end
of the source file.
"""

    #The following several assignments create *class* variables!
    #
    DublinCoreMetadata = {
        "coverage"      : "",
        "contributor"   : "",
        "creator"       : "Steven J. DeRose",
        "date"          : "2015-03-10",
        "description"   :
            "Markdown/MediaWiki/POD formatter class for Python argparse.",
        "format"        : "Unicode text file",
        "identifier"    : "MarkupHelpFormatter.pm/MarkupHelpFormatter",
        "language"      : "programming:Python",
        "publisher"     : "Steven J. DeRose",
        "relation"      : "",
        "rights"        : "CCLI Attribution-Share-Alike",
        "source"        : "http://www.derose.net",
        "subject"       : "Computer program -- Python -- help formatter",
        "title"         : "MarkupHelpFormatter",
        "type"          : "Python 2.7 class",
    }

    InputOptions = {
        "mediawiki"   : True,
        "pod"         : True,
        "markdown"    : True,
        "mailEmph"    : True,
        "entities"    : True,
        "backslashes" : False,
        "defs"        : True,
        "tabSize"     : 4,
    }

    OutputOptions = {
        "defaults"    : False,
        "color"       : True,
        "breakURIs"   : True,
        "sectionNums" : True,
        "width"       : None,
        "indentSize"  : 4,
        "quoteType"   : 'D',  # D double curly, S single curly, A angle, else '"'
        "OLPrefix"    : "", # such as '('
        "OLSuffix"    : "", # such as ':'
        "headFG"      : ["blue", "blue", "blue", "blue", "blue", "blue"],
        "headBG"      : ["white", "white", "white", "white", "white", "white"],
        "headPrefix"  : ["\n\n\n\n", "\n\n\n", "\n\n", "\n", "\n", "\n"],
        "headSuffix"  : ["\n", "\n", "\n", "\n", "\n", "\n",],
        "ULMarkers"   : ["*", "-", "o", "."],
        "OLTypes"     : ["upper-roman", "upper-alpha", "decimal",
                          "lower-roman", "lower-alpha", "decimal"],
        "DLWidth"     : 12,
        "RFCformat"   : "https://tools.ietf.org/html/rfc%d",
    }

    instanceCount = 0

    def __init__(self, prog="Program", *args, **kw):
        MarkupHelpFormatter.instanceCount += 1
        self.whichInstanceAmI = MarkupHelpFormatter.instanceCount

        self._add_defaults = False
        self.podListLevel = 0
        self.html = outHTML()
        self.htmlp = None
        self.listCounts = []
        self.gaveEscMessage = 0   # Prevent repeat message
        self.errors = []
        super(MarkupHelpFormatter, self).__init__(prog, *args, **kw)

    def logError(self, msg):
        self.errors.append(msg)

    def setOption(self, line):
        """Parse and execute an "=set" line, to set some option.
            For scalers:  =set name value
            For lists:    =set name n value
        """
        mat = re.match(r'^=set\s+(\w+)\s+(.*)', line)
        if (not mat):
            self.logError("Bad =set command: " + line)
            return(False)
        nam = mat.group(1); val = mat.group(2)
        Xi = MarkupHelpFormatter.InputOptions
        Xo = MarkupHelpFormatter.OutputOptions
        if (nam == "verbose"):
            global verbose
            verbose = int(val)
        elif (nam == "tabsize"):
            Xi["tabsize"] = int(val)
        elif (nam in Xi):
            Xi[nam] = bool(val)
        elif (nam in Xo):
            if (type(Xo[nam] == list)):
                mat = re.match(r'(\d+)\s+(.*)', val)
                if (not mat or int(mat.group(1)) not in Xo[nam]):
                    return(False)
                Xo[nam][mat.group(1)] = mat.group(2)
            else:
                Xo[nam] = val
        else:
            return(False)
        return(True)

    def _format_text(self, txt):
        """Called only for 'descr' (but twice??).
        """
        sys.stderr.write("*** Entering _format_text for instance %d, textlen %d.\n" %
            (self.whichInstanceAmI, len(txt)))

        vMsg(1, ">>>In MarkupHelpFormatter._format_text()<<<")
        #buf = super(MarkupHelpFormatter, self)._format_text(txt))
        buf = self.format(txt)
        return(buf)
        # calls _fill_text

    #    def _fill_text(self, text, width, indent):
    #        print("    >>>_fill_text(%s)" % (text))
    #        return(super(MarkupHelpFormatter, self)._format_text(text))
    #        # calls _textwrap.fill
    #
    #    def _get_help_string(self, action):
    #        print("    >>>_get_help_string(%s)" % (action))
    #        return(super(MarkupHelpFormatter, self).action.help)

    def _split_lines(self, txt, width):
        """Called for each option's help text.
        """
        #print('TEXT: %s' % (txt))
        if txt.startswith('D|'):
            self._add_defaults = True
            txt = txt[2:]
        if txt.startswith('R|'):
            return txt[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, txt, width)

    def _get_help_string(self, action):
        if not self._add_defaults:
            return argparse.HelpFormatter._get_help_string(self, action)
        helpStr = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    helpStr += ' (default: %(default)s)'
        return helpStr


    ##########################################################################
    #
    def measureColumns(self, lines, startLine, fieldSep=re.compile("|")):
        """Read down until a table ends, and make a list of the
        maximum width encountered for each column.
        """
        maxWidths = []
        for i in range(startLine, len(lines)):
            lin = lines[i]
            if (not re.match(r'\s*\{', lin)): break
            cols = re.split(fieldSep, lin.strip('{}'))
            for c in range(len(cols)):
                if (c >= len(maxWidths)): maxWidths.append(0)
                wid = len(cols[c])  # Too simple...
                if (wid>maxWidths[c]): maxWidths[c] = wid
        return(maxWidths)

    def format(self, s, encoding="utf8", color=1, width=0):
        """Recognize line-initial and line-internal markup from several
        systems. Layout with whitespace and color per options.
        """
        hMsg(1, "Entering MarkupHelpFormatter.format(), passed %s, len %d.\n" %
            (type(s), len(s)))
        self.resetLists()
        # If needed set up entity decoding
        if (self.htmlp is None and
            (self.InputOptions["entities"] or self.InputOptions["pod"])):
            if (PY2):
                import HTMLParser
                self.htmlp = HTMLParser.HTMLParser()
            else:
                from html.parser import HTMLParser
                self.htmlp = HTMLParser()

        # Join up regular text lines, and map markup to term capabilities.
        if (width <= 0):
            width = 80
            if ("WIDTH" in os.environ): width = os.environ["WIDTH"]
        vMsg(3, "format called, width %d" % (width))

        theLines = re.split(r'\r\n?|\n', s)
        hMsg(1, " Split gets %d lines *******" % (len(theLines)))
        blocks = self.makeBlocks(theLines)
        if (verbose):
            msg = ""
            for b in blocks: msg += b.toString() + "\n"
            hMsg(1, "Before doing inlines (%d blocks):\n%s" %
                (len(blocks), msg))

        blocks = self.doInlines(blocks)
        hMsg(1, "After doing inlines (%d blocks):\n%s" %
            (len(blocks), makeDispayedLines(blocks)))

        # Break block-level objects to fit screen
        #### TODO: How does podListLevel get maintained?
        wrapped = []
        for i in range(0,len(blocks)):
            wrapped.append(self.wrap(
                blocks[i], width, marginLeft=self.podListLevel*4))

        # Concat by hand to get precise locs of errors
        ww = ""
        for i, w in enumerate(wrapped):
            try:
                ww += u"".join(wrapped)
            except UnicodeDecodeError as e:
                vMsg(0, u"******* UnicodeDecodeError: %s" % (e))
                ww += w.decode('utf-8')  # Should have happened earlier...
        return(ww)


    def makeBlocks(self, inlines):
        """Check each line for line-initial markup, and use to group lines into
        wrappable blocks. Mostly, that means group any lines until hitting:
            * change of indentation
            * leading flag char such as for lists, heads, rules, tables [*#|=]
            * blank lines
        Create a "Block" object for each one, that knows its type, margins,...

        @param inlines: An array of lines to do substitutions in.
        @return: An array of Block objects.

        This used to try and change on the fly by inserting newlines and such.
        Now it just creates a list of Block objects with properties, which we'll
        later do inline markup on, then wrap, then issue.
        """
        assert(isinstance(inlines, list))
        grammarFmt = "    %-" + str(self.OutputOptions["DLWidth"]) + "s::= %s\n"
        blocks = [ Block("", 'TEXT') ]
        blanks = 0
        for i in range(0,len(inlines)):
            line = inlines[i]
            line = line.expandtabs(self.InputOptions["tabSize"])

            if (re.match(r'\s*<!--.*-->\s*$',line)):       # COMMENT LINE
                continue

            if (line.startswith("=set")):                  # OPTION
                if (not self.setOption(line)):
                    line = "??? " + line
                continue

            if (re.match(r'\s*$', line)):                  # BLANK LINE
                blanks += 1
                continue

            mat = re.match(r'(\s+)', line)                 # Get indentation
            if (mat): indent = mat.group(1)
            else: indent = ""

            mat = re.match(r'\s*(\W+)', line)              # Get leading \W
            if (mat): leadPunct = mat.group(1)
            else: leadPunct = ""

            rest = line[len(indent+leadPunct):]

            # Try to identify what we've got
            #
            if (not leadPunct):                            # Starts with \w
                # Try to catch BNF defs. Not continuations like /\s+\|/.
                mat = re.match(r'(\w+)\s*::=(.*)', line)
                if (self.InputOptions["defs"] and mat):    # Grammar / deflist
                    b = Block("", "BNF", blanks=blanks)
                    b.columns = [ mat.group(1), mat.group(2) ]
                    blocks.append(b)
                elif (blanks==0 and                        # Just text
                    blocks[-1].type in [ 'TEXT, ITEM' ]
                    and indent == blocks[-1].indent):
                    blocks[-1].text += " " + rest
                else:
                    b = Block(line, 'TEXT', indent=indent)
                    blocks.append(b)
                blanks = 0
                continue

            elif (re.match(r'\s*[-=*]{3,}\s*$', line)):    # Horizontal RULE
                b = Block(leadPunct, 'RULE', indent=indent)
                blocks.append(b)
                blanks = 0

            elif (leadPunct[0] in '*+#'):                  # LIST ITEM
                b = Block(rest, 'ITEM', marker=leadPunct, indent=indent, prevBlock=blocks[-1])
                blocks.append(b)
                blanks = 0

            elif (leadPunct.startswith('>')):              # Quotation?
                b = Block(rest, 'QUOTE', indent=indent, marker=leadPunct)
                blocks.append(b)
                blanks = 0

            elif (leadPunct.startswith('|')):             # Quotation?
                b = Block("", 'ROW', indent=indent, marker=leadPunct)
                b.columns = line.split('|')
                blocks.append(b)
                blanks = 0

            elif (leadPunct.startswith('=')):              # "=" code
                headLevel = 0
                if (line.startswith('==') and              # Markdown heads
                    (self.InputOptions["markdown"] or
                     self.InputOptions["mediawiki"])):
                    mat = re.match(r'(=+)', code)
                    headLevel = len(mat.group(1)) - 1
                    line = line[len(mat.group(1)):]
                    self.resetLists()
                elif (self.InputOptions["pod"]):           # POD
                    mat = re.match(r'=([a-z]+)', line)
                    if (mat):
                        b = Block(line, 'TEXT')
                        blocks.append(b)
                        continue
                    line, headLevel = self.handlePODCode(line,mat.group(1))

                if (headLevel):
                    b = Block(line, 'HEAD')
                    b.level = headLevel
                    ### TODO:
                    #self.OutputOptions["headPrefix"][headLevel])
                    #blocks.append(colorize(line,
                    #    fg=self.OutputOptions["headFG"][headLevel],
                    #    bg=self.OutputOptions["headBG"][headLevel],
                    #    bold=1))
                    b.text = self.OutputOptions["headSuffix"][headLevel]
                    blocks.append(b)
                    self.resetLists()
                    blanks = 0
                else:
                    b = Block(line, 'HEAD')
                    blocks.append(b)
            else:                                          # UNKNOWN start
                blocks[-1].text += ' ' + line
            # for each line
        return(blocks)

    def handlePODCode(self, line, cmd):
        """(when requested) handle a POD-style line-initial code.
        """
        headLevel = 0
        vMsg(3, "      POD command '%s'" % (cmd))
        if (cmd == "head"):
            mat2 = re.match(r'=head(\d)', line)
            if (mat2):
                headLevel = int(mat2.group(1))
                vMsg(3, "      POD heading, level %d" % (headLevel))
                line = line[7:]
            else:
                headLevel = 1
                self.logError("      POD heading, bad level in: " + line)
                line = line[6:]
        elif (cmd == "over"):
            line = ""
            self.podListLevel += 1
        elif (cmd == "back"):
            line = ""
            if (self.podListLevel>0): self.podListLevel -= 1
        elif (cmd == "item"):
            ind = self.OutputOptions["indentSize"]*self.podListLevel
            line = (' ' * ind) + line[6:]
        elif (cmd == "begin"): line = ""
        elif (cmd == "end"):   line = ""
        elif (cmd == "for"):   line = ""
        elif (cmd == "pod"):   line = ""
        elif (cmd == "cut"):   line = ""
        # else: unknown POD code, treated as regular line
        return(line, headLevel)



    ##########################################################################
    # Onward to RENDERING
    #

    def uncoloredLength(self, s):
        """Return the length of a string in characters, not counting any ANSI
        terminal color escapes or any trailing whitespace.
        """
        t = re.sub(colorRegex,    '',s)
        t = re.sub(r'\s+$',       '', t)
        if (t.find(chr(27)) >= 0):
            if (not self.gaveEscMessage):
                vMsg(0, "MarkupHelpFormatter: " +
                    "uncoloredLength() left some escape(s) in %s" % (repr(t)))
                self.gaveEscMessage += 1
        return(len(s))

    def wrap(self, s, width, hangingIndent=0,
        marginLeft=0, marginRight=0): # add other sides
        """Break paragraph blocks at appropriate places for screen width.
        Variant spaces: thin = U+2009, hair = U+200A, watch U+2028, U+2029.
        Could also support soft and regular hyphens, URI "/", etc.
        """
        buf = ""
        #tokens = re.split(r'( +' + colorEndRegex + r')', s)
        leadSpaces = 0
        mat = re.match(r'(\s+)', s)
        if (mat):
            leadSpaces = len(mat.group(1))
            s = s[leadSpaces:]
        tokens = re.split(r'\s+', s)
        line = " " * (marginLeft + leadSpaces)
        lineLen = len(line)
        effWidth = width-marginLeft-marginRight

        ###
        # What about when we break the line in middle of colored text?
        ###

        for token in tokens:
            tokenLen = self.uncoloredLength(token)
            if (lineLen + 1 + tokenLen <= effWidth):
                line += ' ' + token
                lineLen += 1 + tokenLen
                continue
            # Following doesn't get triggered for L<txt|"http://...">
            if (self.OutputOptions["breakURIs"] and
                  re.search(r'https?://', token)):
                avail = effWidth-lineLen-1
                loc = token.rfind('/', 1, avail)
                #vMsg(0,
                #    "# Breaking URI, avail %d, token %d, / at %d: '%s'.\n"
                #    % (avail, tokenLen, loc, token))
                if (loc>-1): # break there
                    line += ' ' + token[0:loc+1]
                    token = token[loc+1:]
            buf += line + '\n'
            line = (" " * (hangingIndent+marginLeft)) + token
            lineLen = marginLeft + tokenLen
        if (line != ""): buf += line + '\n'
        return(buf[1:])  # Why is this?


    ##########################################################################
    #
    def doListItem(self, line, code):
        """Set up indentation level and marker(s) for a list item.
        """
        depth = len(code)
        ind = self.OutputOptions["indentSize"] * depth
        buf = (' ' * ind)
        while (len(self.listCounts)<=depth): self.listCounts.append(1)
        self.listCounts[depth] += 1
        vMsg(1, "In doListItem: code %-8s depth %d counts: %s." %
            (code, depth, str(self.listCounts)))
        if (code[-1] == '*'):
            buf += self.getULMarker(depth)
        else:  # '+' for MarkDown, '#' for MediaWiki
            buf += (self.OutputOptions["OLPrefix"] + self.getOLMarker(depth) +
                self.OutputOptions["OLSuffix"])

        if (self.OutputOptions["color"]):
            buf = colorize(buf, fg="blue", bold=True)
        buf += line[depth:]
        return(buf)

    def resetLists(self):
        """Set last-item-number for all list levels back to 0.
        """
        self.listCounts = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ]

    def getULMarker(self, level):
        """Generate the right unordered list marker, given level.
        CSS types: bullet, disc,....
        """
        if (level >= len(self.OutputOptions["ULMarkers"])):
            level = len(self.OutputOptions["ULMarkers"]) - 1
        return(self.OutputOptions["ULMarkers"][level])

    def getOLMarker(self, level):
        """Generate the right ordered list number, given level.
        CSS types: decimal, lower-alpha, upper-latin, upper-roman, none,....
        """
        if (level>len(self.listCounts)): n = self.listCounts[-1]
        else: n = self.listCounts[level]
        if (level >= len(self.OutputOptions["OLTypes"])):
            theType = self.OutputOptions["OLTypes"][-1]
        else:
            theType = self.OutputOptions["OLTypes"][level]
        theType = theType.lower()
        if (theType=="lower" or theType=="lower-alpha"):
            return(string.ascii_lowercase[n])
        elif (theType=="upper" or theType=="upper-alpha"):
            return(string.ascii_uppercase[n])
        elif (theType=="decimal"):
            return(str(n))
        elif (theType=="none"):
            return('')
        elif (theType=="lower-roman"):
            return(getRoman(n).lower())
        elif (theType=="upper-roman"):
            return(getRoman(n).upper())
        return(string.ascii_uppercase[n])


    ##########################################################################
    # Should this be embedded during rendering, or is it better to map
    # to something else like standardized codes or arrays of format-runs?
    #
    def doInlines(self, blocks):
        """Interpret inline markup and special characters.
        @param blocks: a list of blocks, potentially with inline markup/down/etc
        @return: a list of blocks, with ANSI terminal formatting codes.
        """
        assert (isinstance(blocks, list))
        for i in range(len(blocks)):
            b = blocks[i].text
            if (not isinstance(b, str)):
                print("Bad type for '%s': %s." % (b, type(b)))
                continue
            #print("-->" + b)
            if (self.InputOptions["mediawiki"]):
                b = re.sub("'''''(.*?)'''''", self.mkBI,   b)
                b = re.sub("'''(.*?)'''",     self.mkItal, b)
                b = re.sub("''(.*?)''",       self.mkBold, b)
                b = re.sub(r'(\[.*?\])',      self.mkLink, b)

            if (self.InputOptions["pod"]):
                b = re.sub(r'B<(.*?)>',       self.mkBold, b)  # bold
                b = re.sub(r'C<(.*?)>',       self.mkUnd,  b)  # command
                b = re.sub(r'E<(.*?)>',       self.mkChar, b)  # special ch
                b = re.sub(r'F<(.*?)>',       self.mkQuot, b)  # filename
                b = re.sub(r'I<(.*?)>',       self.mkItal, b)  # italic
                b = re.sub(r'L<(.*?)>',       self.mkLink, b)  # link
                b = re.sub(r'S<(.*?)>',       self.mkNBrk, b)  # no-break
                b = re.sub(r'X<(.*?)>',       self.drop,   b)  # index entry
                #b = re.sub(r'Z<(.*?)>',      self.drop,   b)  # No POD

            if (self.InputOptions["mailEmph"]):
                b = re.sub(r'\b\*(\w+)\*\b',  self.mkBold, b)
                b = re.sub(r'\b_(\w+)_\b',    self.mkBold, b)

            if (self.InputOptions["backslashes"]):
                import ast
                b = ast.literal_eval(b)

            if (self.InputOptions["entities"] and self.htmlp is not None):
                b = self.htmlp.unescape(b)  # Expand HTML entities
            blocks[i] = b
        return(blocks)

    # Methods to produce each of the requested output effects.
    # TODO: Integrate with mathUnicode package, which provides Latin for:
    # italic, bold, bold italic, script, bold script, fraktur, double-struck;
    # sans-serif in roman, italic, bold, bold italic; monospace,
    # parenthesized, circled; and uppercase squared, circled, and neg sq/c.
    #
    def drop(self, matchobj):
        return matchobj.group(1)
    def mkBold(self, matchobj):
        return(colorize(matchobj.group(1), bold=1))
    def mkItal(self, matchobj):
        return(colorize(matchobj.group(1), fg="red"))
    def mkUnd(self, matchobj):
        return(colorize(matchobj.group(1), fg="underline"))
    def mkBI(self, matchobj):
        return(colorize(matchobj.group(1), fg="red", bold=1))
    def mkLink(self, matchobj):
        if (':' in matchobj.group(1)):
            anchor, ref = matchobj.group(1).split(':')
        else:
            anchor = ref = matchobj.group(1)
        ref = ref.strip("\"'")
        mat = re.match(r'(IETF\s*)?RFC\s*(\d+)', ref)
        if (mat):
            ref = MarkupHelpFormatter.OutputOptions['RFCformat'] % (mat.group(2))
        if (verbose>=3):
            self.html.text(anchor)
        msg = colorize(anchor, fg="blue", bold=1)
        return(msg)
    def mkNBrk(self, matchobj):
        return(re.sub(r'\s', unichr(160), matchobj.group(1)))
    def mkQuot(self, matchobj):
        """Add quotes around the text.
        """
        if (self.OutputOptions["quoteType"] == 'D'):
            return(specialChars["ldquo"] + matchobj.group(1) + specialChars["rdquo"])
        elif (self.OutputOptions["quoteType"] == 'S'):
            return(specialChars["lsquo"] + matchobj.group(1) + specialChars["rsquo"])
        elif (self.OutputOptions["quoteType"] == 'A'):
            return(specialChars["laquo"] + matchobj.group(1) + specialChars["raquo"])
        else:
            return('"' + matchobj.group(1) + '"')
    def mkChar(self, matchobj):
        txt = matchobj.group(1)
        if   (txt == 'lt'):     return('<')
        elif (txt == 'gt'):     return('>')
        elif (txt == 'verbar'): return('|')
        elif (txt == 'sol'):    return('/')
        elif (re.match(r'0x[0-9a-f]+', txt)):
            return(unichr(hex(txt)))
        elif (re.match(r'0[0-7]+', txt)):
            return(unichr(oct(txt)))
        elif (re.match(r'\d+', txt)):
            return(unichr(int(txt)))
        # Try html entities:
        if (self.htmlp is not None):
            c = self.htmlp.unescape('&'+txt+';')
            if (len(c) == 1): return(c)
        return(txt)


###############################################################################
# A wrappable block of text, typically separated from neighbors by blank lines.
# 'type' may be 'BLANK' when we've counting blank lines but don't know what we'll
# be getting next.
#
class Block:
    bTypes = [ 'TEXT', 'ITEM', 'HEAD', 'PRE', 'ROW', 'BNF', 'RULE', 'QUOTE', ]

    def __init__(self, text, typ=None, blanks=0, indent="", prevBlock=None, marker=""):
        assert (typ in Block.bTypes)
        self.text = text
        self.columns = []     # For ROW and BNF.
        self.type = typ
        self.level = 0        # For heads
        self.blanks = blanks
        self.indent = indent
        self.marker = marker

        if (prevBlock):
            self.headCounts = prevBlock.headCounts
            self.listCounts = prevBlock.listCounts
        else:
            self.headCounts = []
            self.listCounts = []

        self.listCounts = []

    def render(self):
        full = "\n" * self.blanks
        if (self.headCounts): full += ".".join(self.headCounts) + ": "
        elif (self.listCounts): full += ".".join(self.listCounts) + ": "
        elif (self.marker): full += self.marker +  " "
        full += text + "\n"
        rend = self.wrap(full)
        return rend

    def wrap(self):
        pass

    def toHTML(self):
        pass

    def toString(self):
        return("### %5s: bl %1d ind %2d marker '%s'" %
            self.type, self.blanks, len(self.indent), self.marker)

class FormatRun:
    def __init__(self, text):
        self.text = text
        self.bold = False
        self.ital = False
        self.mono = False
        self.und  = False
        self.nobr = False

    def render(self):
        return self.text
###############################################################################
# New/untested
#
if __name__ == "__main__":
    print("*** Testing MarkupHelpFormatter.py ***\n")

    while (len(sys.argv) > 1 and sys.argv[1] == "-v"):
        verbose += 1
        del sys.argv[1]
    if (len(sys.argv)<2):
        text = """=pod

=head1 Usage

This is some test POD for testing MarkupHelpFormatter.

=over

=item * Item 1

=item * Item 2

=back

And back I<out> of B<the> list. Wee.

=cut
"""
    else:
        try:
            text = open(sys.argv[1], 'r').read()
        except IOError as e:
            print("Can't read file '%s'." % (sys.argv[1]))
            sys.exit()

    mhf = MarkupHelpFormatter()
    print(mhf._format_text(text))

    print("\n*** DONE ***\n")
    sys.exit()
