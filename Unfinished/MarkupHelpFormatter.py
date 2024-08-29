#!/usr/bin/env python3
#
# MarkupHelpFormatter.py.
# Upgrades for Python argparse, that don't forcibly wrap all text.
#
import os
import sys
import re
import string
import argparse
import html
import logging

lg = logging.getLogger("MarkupHelpFormatter")

__metadata__ = {
    "title"        : "MarkupHelpFormatter",
    "description"  :
        "Markdown/MediaWiki/POD formatter class for Python argparse.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2013-04-18",
    "modified"     : "2020-01-29",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/",
}
__version__ = __metadata__["modified"]


descr = """
=Description=

This package defines a formatter class that can be used with Python's
I<argparse> package, in order to get better formatting.

It consists of these major parts:

* a Loader that can read MarkDown, MediaWiki, and POD markup
* a MicroDoc structure, or "Honey, I shrink the DOM" (a document is a sequence
of blocks, each of which is a sequence of format-runs; plus some hack for tables)
* a Renderer that generates decent output for an ANSI terminal, using color and
Unicode Latin variants.
* MarkupHelpFormatter, which interfaces it all to argparse.

==MarkupHelpFormatter(argparse.HelpFormatter)==

This class is much fancier. It supports several markup systems within
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
    * Surprise
    * Better formatting
    * An almost ''fanatical'' devotion to markup
    ...
"",
    formatter_class=MarkupHelpFormatter
    )

==Supported Markup syntax(es)==

In short, this class supports much of I<Markdown>, I<POD>, and
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


==MediaWiki and MarkDown==

B<MediaWiki> markup is what WikiPedia uses. It is very similar to MarkDown.
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


===MarkDown===

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


==POD==

B<POD> is short for "Plain Old Documentation". A description is available at
L<here|"http://en.wikipedia.org/wiki/Plain_Old_Documentation">

POD reserves only "=" at start of line, where
a keyword follows. Some POD software (not including this class)
requires a blank line preceding any such component.
Some example components:

    =encoding utf8

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


=Options available in MarkupHelpFormatter=

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

==Input capabilities and options==

    Name          Default       Description
    "entities"    : True     -- expand HTML character entities and refs
    "backslashes" : False    -- expand Python-style backslash-codes
    "pod"         : True     -- recognize POD ("plain old doc") markup

    "html"        : True     -- Allow some HTML
    "mediawiki"   : True     -- recognize basic MediaWiki markup
    "markdown"    : True     -- recognize basic Markdown markup
    "mailEmph"    : True     -- recognize email-style emphasis
    "defs"        : True     -- recognize BNF-style grammar/deflist markup
    "tabSize"     : 4        -- interval of incoming tab-stops


==Output capabilities and options==

TODO: Sync with style implementation

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


=Using MarkupHelpFormatter in your Python programs=

    import MarkupHelpFormatter
    parser = argparse.ArgumentParser(
        description='...',
        epilog='...',
        formatter_class=MarkupHelpFormatter
    )

If desired, you can also set options (see above), for example:

    MarkupHelpFormatter.InputOptions["mediawiki"] = True


==Notes==

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


=Related commands and libraries=

A different Python Markdown formatter: [https://pypi.org/project/markdown-formatter/]

=Known bugs and limitations=

Tables are not yet supported.

Some details of MarkDown, such as "underlined" headings, are not supported.

The program does not try to figure out just which ANSI terminal
capabilities your terminal program supports. For example, a few
support italics, blinking text, 256 colors, or even multiple fonts.
The default formatting avoids uncommon capabilities. You can get at
some others via "=set" and =style (see above).


=History=

2013-04-18: Written by Steven J. DeRose.
Thanks to Anthon van der Neut for help on integrating with `argparse`. Also:
    [http://stackoverflow.com/questions/3853722]
    [https://bitbucket.org/ruamel/std.argparse/src]
    [http://hg.python.org/cpython/file/2.7/Lib/argparse.py]
    [https://docs.python.org/2/library/textwrap.html]

2020-01-29: Start addressing issues with extensibility, such as for BNF grammars,
tables, etc. And bugs like premature line-breaking, numbering, hanging indents,
etc. Start supporting Unicode Mathematical font features for better
range of formatting.

2020-03-01: `ParagraphHelpFormatter` class split out to become `BlockFormatter.py`.
Slightly improved at the same time, such as to handle tabs and indented blocks.
Start separating loader, renderer, and document representation, instead
of transforming straight to escape-codes inline.

2021-04: Clean up.


=Rights=

This program is Copyright 2013 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see L<here|"https://creativecommons.org">.

For the most recent version, see L<http://www.derose.net/steve/utilities/> or
L<http://github/com/sderose>.


=To do=

* Add a way to move the autogenerated 'Options' section to a given location.
* More testing, especially __main__ and Unicode.
* Preserve spaces within quotes and in indented/pre lines.
* Prematurely breaks lines sometimes; problem with uncoloredLength()?
Or may not be removing pre-existing LFs right.
* Finish sectionNums. Clear list-numbering properly
* Add MarkDown and Mediawiki Deflist, Blockquote
* Support hanging indent on lists
* Indent paragraph immediately following list-item? At least for POD
* Option to reset colors for light background (let =SET refer env. vars?)
* Integrate mathAlphanumerics.py to get bold, italic, etc.
* Possibly hook up to 'man -H'


==Low priority==

* Support backslash+x etc. in =set ULmarkers.
* Option to break URIs and paths at '/' doesn't always work
* Option to page the output, or send to 'less'
* Finish XHTML output option (and browser as pager)
* Is there an easy way to check if terminal supports underlining, etc.?
* How best to support links?
* Support POD's Z<> (suppress POD) markup
* Once HTML generation is done, add =set for css and js to include.


=Options=
"""


##############################################################################
#
verbose = 0

esc = chr(27)
specialChars = {
    "lsquo":   chr(0x2018),    "rsquo":   chr(0x2019),
    "ldquo":   chr(0x201C),    "rdquo":   chr(0x201D),
    "lsaquo":  chr(0x2039),    "rsaquo":  chr(0x203A),
    "ldaquo":  chr(0x00AB),    "rdaquo":  chr(0x00BB),

    "endash":  chr(0x2013),    "emdash":  chr(0x2014),
    "shy":     chr(0x00AD),    "hypoint": chr(0x2027),
    "hyminus": chr(0x002D),

    "ensp":    chr(0x2002),    "emsp":    chr(0x2003),
    "thinsp":  chr(0x2009),    "hairsp":  chr(0x200A),
    "zerosp":  chr(0x200B),    "nbsp":    chr(0x00A0),

    "lt": "<", "gt": ">", "apos": "'", "quo": '"', "amp": "&",
}

def makeDispayedLines(lines):
    assert (isinstance(lines, list))
    buf = ""
    for line in lines:
        buf += "    >>>%s\n" % (re.sub(r"([\x01-\x20])", toPix, line))
    return buf

def toPix(mat):
    """Make control chars and space visible.
    """
    return chr(0x2400 + ord(mat.group(1)))


##############################################################################
#
class MarkupHelpFormatter(argparse.HelpFormatter):
    """A formatter for argparse.
    Accepts most of MarkDown and POD, and generates a rendering suitable for
    ANSI terminal with color support.
    See further documentation at the end of the source file.
    """


###############################################################################
#
class MicroDoc:
    """A very tiny representation of a document. The model is:

    Microdoc --> StyleSpec, Block+
    Block --> BlockTypeName, FormatRun+
    FormatRun --> RunTypeName, text

    Note there is no recursion here, just these 3 levels.
    """
    def __init__(self, docPath=None, stylePath=None):
        self.docPath = docPath
        self.stylePath = stylePath
        self.styleSheet = StyleSheet()
        if (stylePath): self.loadStyle(stylePath)

        self.blocks = []
        if (docPath): self.loadDoc(docPath)

    def loadStyle(self, stylePath):
        pass

    def loadDoc(self, path):
        pass

    def renderToDisplay(self):
        r = Renderer(self.styleSheet, self.blocks)
        vLines = r.render()
        for vLine in vLines:
            print(vLine)

    def renderToLines(self):
        vLines = renderer().render(self.styleSheet, self.blocks)


##########################################################################
#
class Loader:
    """Read Markdown/POD/etc. and build a MicroDoc structure.
    """
    InputOptions = {
        "mediawiki"   : True,          # headings like ===Title===, ''ital'',...
        "markdown"    : True,
        "pod"         : True,          # headings like =head3 Title, I<ital>,...
        "html"        : True,          # allow some html
        "mailEmph"    : True,          # *very* important
        "entities"    : True,          # &amp;
        "backslashes" : False,
        "defs"        : True,
        "tabSize"     : 4,             # For expanding incoming TABs
    }

    instanceCount = 0

    def __init__(self, *args, **kw):
        MarkupHelpFormatter.instanceCount += 1
        self.whichInstanceAmI = MarkupHelpFormatter.instanceCount
        self.prog = "???"
        if ("prog" in kw): self.prog = kw["prog"]
        self._add_defaults = False
        self.podListLevel = 0
        self.html = outHTML()
        self.htmlp = None
        self.listCounts = []
        self.gaveEscMessage = 0   # Prevent repeat message
        self.errors = []
        super(Loader, self).__init__(prog, *args, **kw)

    def logError(self, msg):
        self.errors.append(msg)

    def setOption(self, line):
        """Parse and execute an "=set" line, to set some option.
        For scalars/options:  =set name value
        """
        mat = re.match(r"^=set\s+(\w+)\s+(.*)", line)
        if (not mat):
            self.logError("Bad =set command: " + line)
            return(False)
        propName = mat.group(1); propVal = mat.group(2)
        Xi = Loader.InputOptions
        Xo = Renderer.OutputOptions
        if (propName == "verbose"):
            global verbose
            verbose = int(propVal)
        elif (propName == "tabsize"):
            Xi["tabsize"] = int(propVal)
        elif (propName in Xi):
            Xi[propName] = bool(propVal)
        elif (propName in Xo):
            if (type(Xo[propName] == list)):
                mat = re.match(r"(\d+)\s+(.*)", propVal)
                if (not mat or int(mat.group(1)) not in Xo[propName]):
                    return(False)
                Xo[propName][mat.group(1)] = mat.group(2)
            else:
                Xo[propName] = propVal
        else:
            return(False)
        return(True)

    def setStyle(self, line):
        """For style things:
            =style class[.level] property value

        """
        quo = r"'[^']*'|\"[^\"]*\"|.*"
        mat = re.match(r"^=style\s+(\w+)(\.\d)?\s+(\w+)\s+%s" % (quo), line)
        if (not mat):
            self.logError("Bad =style syntax:\n    %s" % (line))
            return(False)
        eclass = mat.group(1)  # element-class it applies to
        elvl = mat.group(2)  # level, if applicable
        propName = mat.group(3)  # which property
        propVal = mat.group(4)  # value for the property

        if (eclass not in StyleValues.BlockClasses):
            self.logError("Bad =style class name '%s':\n    %s" % (eclass, line))
            return(False)
        if (propName not in StyleValues.BlockClasses):
            self.logError("Bad =style class name '%s':\n    %s" % (eclass, line))
            return(False)

        Xi = Loader.InputOptions
        Xo = Renderer.OutputOptions
        if (propName == "verbose"):
            global verbose
            verbose = int(propVal)
        elif (propName == "tabsize"):
            Xi["tabsize"] = int(propVal)
        elif (propName in Xi):
            Xi[propName] = bool(propVal)
        elif (propName in Xo):
            if (type(Xo[propName] == list)):
                mat = re.match(r"(\d+)\s+(.*)", propVal)
                if (not mat or int(mat.group(1)) not in Xo[propName]):
                    return(False)
                Xo[propName][mat.group(1)] = mat.group(2)
            else:
                Xo[propName] = propVal
        else:
            return(False)
        return(True)


    def _format_text(self, txt):
        """Called only for "descr" (but twice??).
        """
        sys.stderr.write("*** Entering _format_text for instance %d, textlen %d.\n" %
            (self.whichInstanceAmI, len(txt)))

        lg.log(logging.INFO-1, ">>>In MarkupHelpFormatter._format_text()<<<")
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
        #print("TEXT: %s" % (txt))
        if txt.startswith("D|"):
            self._add_defaults = True
            txt = txt[2:]
        if txt.startswith("R|"):
            return txt[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, txt, width)

    def _get_help_string(self, action):
        if not self._add_defaults:
            return argparse.HelpFormatter._get_help_string(self, action)
        helpStr = action.help
        if "%(default)" not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    helpStr += " (default: %(default)s)"
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
            if (not re.match(r"\s*\{", lin)): break
            cols = re.split(fieldSep, lin.strip("{}"))
            for c in range(len(cols)):
                if (c >= len(maxWidths)): maxWidths.append(0)
                wid = len(cols[c])  # Too simple...
                if (wid>maxWidths[c]): maxWidths[c] = wid
        return(maxWidths)

    def format(self, s, encoding="utf8", color=1, width=0):
        """Recognize line-initial and line-internal markup from several
        systems. Layout with whitespace and color per options.
        """
        lg.log(logging.INFO-1,
            "====Entering MarkupHelpFormatter.format(), passed %s, len %d.\n" %
            (type(s), len(s)))
        self.resetLists()
        # If needed set up entity decoding
        if (self.htmlp is None and
            (Loader.InputOptions["entities"] or Loader.InputOptions["pod"])):
            from html.parser import HTMLParser
            self.htmlp = HTMLParser()

        # Join up regular text lines, and map markup to term capabilities.
        if (width <= 0):
            width = 80
            if ("WIDTH" in os.environ): width = os.environ["WIDTH"]
        lg.log(logging.INFO-1, "format called, width %d (input length %d)" % (width, len(s)))

        theLines = re.split(r"\r\n?|\n", s)
        lg.log(logging.INFO-1, "====Split got %d lines *******" % (len(theLines)))

        blocks = self.makeBlocks(theLines)
        if (verbose):
            msg = ""
            for b in blocks: msg += b.tostring() + "\n"
            if (verbose>=1):
                lg.log(logging.INFO-1, "====Before doing inlines (%d blocks):\n%s" %
                    (len(blocks), msg))
                for i, b in enumerate(blocks):
                    lg.log(logging.INFO-1, "#%03d: %s" % (i, b.tostring()))

        blocks = self.doInlines(blocks)
        lg.log(logging.INFO-1, "====After doing inlines (%d blocks):\n%s" %
            (len(blocks), makeDispayedLines(blocks)))

        # Break block-level objects to fit screen
        #### TODO: How does podListLevel get maintained?
        wrapped = []
        for i in range(0,len(blocks)):
            curWrap = self.wrap(blocks[i], width, marginLeft=self.podListLevel*4)
            lg.log(logging.INFO-1, "    Block #%3d made %d lines" % (i, len(curWrap)))
            wrapped.extend(curWrap)

        lg.log(logging.INFO-1, "====After wrapping , %d entries)" % (len(wrapped)))

        # Concat by hand to get precise locs of errors
        if (False):
            ww = ""
            for i, w in enumerate(wrapped):
                try:
                    ww += "".join(wrapped)
                except UnicodeDecodeError as e:
                    lg.log(logging.INFO-0, "******* UnicodeDecodeError: %s" % (e))
                    ww += w.decode("utf-8")  # Should have happened earlier...
            return(ww)
        return "".join(wrapped)

    def makeBlocks(self, inlines):
        """Check each line for line-initial markup, blank lihes, and indentation.
        Use thoseto group lines into wrappable blocks. Break on hitting:
        Mostly, that means group any lines until hitting:
            * indentation
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
        #grammarFmt = "    %-" + str(Renderer.OutputOptions["DLWidth"]) + "s::= %s\n"

        MDon = Loader.InputOptions["markdown"] or Loader.InputOptions["mediawiki"]
        PODon = Loader.InputOptions["pod"]
        HTMLon = Loader.InputOptions["pod"]
        tabSize = Loader.InputOptions["tabSize"]

        blocks = [ Block("", "TEXT") ]
        blanks = 0
        for i in range(0,len(inlines)):
            line = inlines[i]
            lg.log(logging.INFO-2, "LINE %3d: <<%s>>" % (i, line))
            line = line.expandtabs(tabSize)
            if (HTMLon):
                line = re.sub(r"\s*<!--.*-->\s*$", "", line)

            if (line.startswith("=set")):                  # OUR OPTIONS
                if (not self.setOption(line)):
                    line = "??? " + line
                continue

            if (re.match(r"\s*$", line)):                  # BLANK LINE
                blanks += 1
                continue

            mat = re.match(r"(\s+)", line)                 # Get indentation
            if (mat): indent = mat.group(1)
            else: indent = ""

            mat = re.match(r"\s*(\W+)", line)              # Leading non-alphas
            if (mat):
                leadPunct = mat.group(1)
                leadPunct0 = leadPunct[0]
            else:
                leadPunct = ""

            rest = line[len(indent+leadPunct):]

            # Try to identify what we've got
            blClass = None
            headLevel = 0
            columns = None
            listParam = None

            if (indent != ""):                             # Code or similar
                blClass = StyleValues.BLK_PRE

            elif (not leadPunct):                          # Starts with \w
                # Try to catch BNF defs. Not continuations like /\s+\|/.
                mat = re.match(r"(\w+)\s*::=(.*)", line)
                if (Loader.InputOptions["defs"] and mat):    # Grammar / deflist
                    typ = "BNF"
                    columns = [ mat.group(1), mat.group(2) ]  # TODO FINISH
                elif (blanks == 0                          # Just text
                    and blocks[-1].type in [ "TEXT", "ITEM" ]
                    and indent == blocks[-1].indent):
                    blocks[-1].text += " " + rest
                    # Leave typ==None, no new Block
                else:
                    blClass = StyleValues.BLK_TEXT
                continue

            elif (leadPunct0 in "*+#"):                    # LIST ITEM
                line = rest
                blClass = StyleValues.BLK_ITEM
                #marker = leadPunct  # TODO?
                #prevBlock = blocks[-1]
                listParam = self.listCounts
                # TODO Adjust the list count

            elif (leadPunct0 == ">"):                      # Quotation?
                line = rest
                blClass = StyleValues.BLK_QUOTE
                marker = leadPunct

            elif (leadPunct0 == "|"):                      # Table? Quotation?
                line = rest
                blClass = StyleValues.BLK_ROW
                marker = leadPunct
                columns = line.split(sep="|")  # TODO FINISH

            elif (re.match(r"[-=*]{3,}\s*$", line)):       # Horizontal RULE
                line = leadPunct
                blClass = StyleValues.BLK_RULE

            elif (leadPunct0 == "="):                      # "=" code
                headLevel = 0
                if (line.startswith("==") or               # Markdown heads
                    (MDon and line.endswith("="))):
                    mat = re.match(r"(=+)", line)
                    headLevel = len(mat.group(1)) - 1
                    line = line[len(mat.group(1)):]
                    blClass = StyleValues.BLK_HEAD
                elif (PODon):                              # POD
                    mat = re.match(r"=([a-z]+)", line)
                    if (mat):
                        line, headLevel, typ = self.handlePODCode(line,mat.group(1))

                if (typ is None):                          # Unused POD codes, etc.
                    pass
                elif (headLevel):
                    ### TODO:
                    #Renderer.OutputOptions["headPrefix"][headLevel])
                    #blocks.append(StyleValues.colorize(line,
                    #    fg=Renderer.OutputOptions["headFG"][headLevel],
                    #    bg=Renderer.OutputOptions["headBG"][headLevel],
                    #    bold=1))
                    blClass = StyleValues.BLK_HEAD
                    line = Renderer.OutputOptions["headSuffix"][headLevel]

            else:                                          # UNKNOWN start, just cat
                blocks[-1].text += " " + line
                blanks = 0
                # Leave type==None, so no new block constructed.

            # Construct the block, if any
            if (typ is not None):
                b = self.makeBlock(line, typ=typ, blanks=blanks, indent=indent,
                    level=headLevel, columns=columns, listCounts=listParam)
                if (blClass == StyleValues.BLK_HEAD): self.resetLists()
                blocks.append(b)
                blanks = 0
            # for each line
        return(blocks)

    def handlePODCode(self, line, cmd):
        """(when requested) handle a POD-style line-initial code.
        @return (restOfLine, headingLevel|0, blockType)
        """
        headLevel = 0
        blockType = None
        lg.log(logging.INFO-3, "      POD command '%s'" % (cmd))

        if (cmd == "head"):
            blockType = "HEAD"
            mat2 = re.match(r"=head(\d)", line)
            if (mat2):
                headLevel = int(mat2.group(1))
                lg.log(logging.INFO-3, "      POD heading, level %d" % (headLevel))
                line = line[7:]
            else:
                headLevel = 1
                self.logError("      POD heading, bad level in: " + line)
                line = line[6:]
        elif (cmd == "over"):
            line = ""
            blockType = "OPEN"
            self.podListLevel += 1
        elif (cmd == "back"):
            line = ""
            blockType = "CLOSE"
            if (self.podListLevel>0): self.podListLevel -= 1
        elif (cmd == "item"):
            ind = Renderer.OutputOptions["indentSize"]*self.podListLevel
            line = (" " * ind) + line[6:]
            blockType = "ITEM"
        elif (cmd == "begin"): line = ""
        elif (cmd == "end"):   line = ""
        elif (cmd == "for"):   line = ""
        elif (cmd == "pod"):   line = ""
        elif (cmd == "cut"):   line = ""
        else: blockType = "TEXT"  # unknown POD code, treat as regular line
        return(line, headLevel, blockType)


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
            if (Loader.InputOptions["mediawiki"]):
                b = re.sub("'''''(.*?)'''''", self.mkBI,   b)
                b = re.sub("'''(.*?)'''",     self.mkItal, b)
                b = re.sub("''(.*?)''",       self.mkBold, b)
                b = re.sub(r"(\[.*?\])",      self.mkLink, b)

            if (Loader.InputOptions["pod"]):
                b = re.sub(r"B<(.*?)>",       self.mkBold, b)  # bold
                b = re.sub(r"C<(.*?)>",       self.mkUnd,  b)  # command
                b = re.sub(r"E<(.*?)>",       self.mkChar, b)  # special ch
                b = re.sub(r"F<(.*?)>",       self.mkQuot, b)  # filename
                b = re.sub(r"I<(.*?)>",       self.mkItal, b)  # italic
                b = re.sub(r"L<(.*?)>",       self.mkLink, b)  # link
                b = re.sub(r"S<(.*?)>",       self.mkNBrk, b)  # no-break
                b = re.sub(r"X<(.*?)>",       self.drop,   b)  # index entry
                #b = re.sub(r"Z<(.*?)>",      self.drop,   b)  # No POD

            if (Loader.InputOptions["mailEmph"]):
                b = re.sub(r"\b\*(\w+)\*\b",  self.mkBold, b)
                b = re.sub(r"\b_(\w+)_\b",    self.mkBold, b)

            if (Loader.InputOptions["backslashes"]):
                import ast
                b = ast.literal_eval(b)

            if (Loader.InputOptions["entities"] and self.htmlp is not None):
                #b = self.htmlp.unescape(b)  # Expand HTML entities
                b = html.unescape(b)
            blocks[i] = b
        return(blocks)

    def makeFormatRuns(self):
        """Scan the text of this block, and make any inline items into actual
        format run objects.
        """
        BI = "'''''(?P<BI>[^']+)'''''"
        BD = "'''(?P>BD>[^']+)'''"
        IT = "''(?P<IT>[^']+)''"
        TT = "`(?P<TT>[^`]+)`"
        theExprMD = BI + "|" + BD + "|" + IT + "|" + TT
        theExprPod = r"(?P<PODTYPE>[BCEFILSX])<(?P<POD>.*?)>"
        if (True):  # TODO: only if POD is on
            theExpr = "%s|%s" % (theExprMD, theExprPod)
        else:
            theExpr = theExprMD

        runs = []
        prevEnd = 0
        for mat in re.finditer(theExpr):
            for typ in [ "BI", "BD", "IT", "TT", "POD" ]:
                assert (type=="PPOD" or typ in StyleValues.InlineClasses)
                if (mat.groups(typ) is None): continue
                txt = mat.group(typ)
                if (typ == "POD"): fullType = "POD_" + mat.group("PODTYPE")
                else: fullType = "MDN_" + typ
                print("Run: (%s): '%s'" % (fullType, txt))
                fr = FormatRun(mat.group(1), mat.start(typ), mat.end(typ), emphType=fullType)
            runs.append(fr)

    # Methods to produce each of the requested output effects.
    # TODO: Integrate with mathAlphanumerics package, which provides Latin for:
    # italic, bold, bold italic, script, bold script, fraktur, double-struck;
    # sans-serif in roman, italic, bold, bold italic; monospace,
    # parenthesized, circled; and uppercase squared, circled, and neg sq/c.
    #
    def drop(self, matchobj):
        return matchobj.group(1)
    def mkBold(self, matchobj):
        return(StyleValues.colorize(matchobj.group(1), bold=1))
    def mkItal(self, matchobj):
        return(StyleValues.colorize(matchobj.group(1), fg="red"))
    def mkUnd(self, matchobj):
        return(StyleValues.colorize(matchobj.group(1), fg="underline"))
    def mkBI(self, matchobj):
        return(StyleValues.colorize(matchobj.group(1), fg="red", bold=1))
    def mkLink(self, matchobj):
        if (":" in matchobj.group(1)):
            anchor, ref = matchobj.group(1).split(sep=":", maxsplit=1)
        else:
            anchor = ref = matchobj.group(1)
        ref = ref.strip("\"'")
        mat = re.match(r"(IETF\s*)?RFC\s*(\d+)", ref)
        if (mat):
            ref = MarkupHelpFormatter.OutputOptions["RFCformat"] % (mat.group(2))
        if (verbose>=3):
            self.html.text(anchor)
        msg = StyleValues.colorize(anchor, fg="blue", bold=1)
        return(msg)
    def mkNBrk(self, matchobj):
        return(re.sub(r"\s", chr(160), matchobj.group(1)))
    def mkQuot(self, matchobj):
        """Add quotes around the text.
        """
        if (Renderer.OutputOptions["quoteType"] == "D"):
            return(specialChars["ldquo"] + matchobj.group(1) + specialChars["rdquo"])
        elif (Renderer.OutputOptions["quoteType"] == "S"):
            return(specialChars["lsquo"] + matchobj.group(1) + specialChars["rsquo"])
        elif (Renderer.OutputOptions["quoteType"] == "A"):
            return(specialChars["laquo"] + matchobj.group(1) + specialChars["raquo"])
        else:
            return('"' + matchobj.group(1) + '"')
    def mkChar(self, matchobj):
        txt = matchobj.group(1)
        if   (txt == "lt"):     return("<")
        elif (txt == "gt"):     return(">")
        elif (txt == "verbar"): return("|")
        elif (txt == "sol"):    return("/")
        elif (re.match(r"0x[0-9a-f]+", txt)):
            return(chr(hex(txt)))
        elif (re.match(r"0[0-7]+", txt)):
            return(chr(oct(txt)))
        elif (re.match(r"\d+", txt)):
            return(chr(int(txt)))
        # Try html entities:
        if (self.htmlp is not None):
            c = self.htmlp.unescape("&"+txt+";")
            if (len(c) == 1): return(c)
        return(txt)


###############################################################################
# A wrappable block of text, typically separated from neighbors by blank lines.
#
class Block:
    def __init__(self, text, typ=None, blanks=0, indent="",
        prevBlock=None, marker="", level=0, columns=None, listCounts=None):
        print("    New Block, type %s, blanks %d, level %d." % (typ, blanks, level))
        self.text = text
        assert (typ in Block.bTypes)
        self.type = typ                # One of bTypes
        self.blanks = blanks           # Num preceding blank lines
        self.indent = indent           # Num spaces of left indent to generate
        self.formatRuns = [ FormatRun(self.text) ]

        self.preserveWS = False        # Is this a special area, like code block?
        if (prevBlock):
            self.headCounts = prevBlock.headCounts
            self.listCounts = prevBlock.listCounts
        else:
            self.headCounts = []
        self.marker = marker           # OUTPUT list marker if any
        self.level = level             # For heads
        self.columns = columns         # For ROW and BNF.
        self.listCounts = listCounts   # Current number in each list level

    def render(self, MHFObject=None):
        """Turn this block into a string we can print to a terminal.
            * newlines to wrap properly to specified width
            * indentation
            * list markers and numbers
            * blank lines before headings
            * color escapes for emphasis
            * Unicode-based "fonts"
        """
        towrap = ""
        full = "\n" * self.blanks  # TODO Wrong, this is *input* blank count
        if (self.headCounts): full += ".".join(self.headCounts) + ": "
        elif (self.listCounts): full += ".".join(self.listCounts) + ": "
        elif (self.marker): full += self.marker +  " "
        full += text + "\n"
        rend = self.wrap(full)
        return rend

    def uncoloredLength(self, s):
        """Return the length of a string in characters, not counting any ANSI
        terminal color escapes or any trailing whitespace.
        """
        t = re.sub(colorRegex,    "",s)
        t = re.sub(r"\s+$",       "", t)
        if (t.find(chr(27)) >= 0):
            if (not self.gaveEscMessage):
                lg.log(logging.INFO-0, "MarkupHelpFormatter: " +
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
        #tokens = re.split(r"( +" + colorEndRegex + r")", s)
        leadSpaces = 0
        mat = re.match(r"(\s+)", s)
        if (mat):
            leadSpaces = len(mat.group(1))
            s = s[leadSpaces:]
        tokens = re.split(r"\s+", s)
        line = " " * (marginLeft + leadSpaces)
        lineLen = len(line)
        effWidth = width-marginLeft-marginRight

        ###
        # What about when we break the line in middle of colored text?
        ###

        for token in tokens:
            tokenLen = self.uncoloredLength(token)
            if (lineLen + 1 + tokenLen <= effWidth):
                line += " " + token
                lineLen += 1 + tokenLen
                continue
            # Following doesn't get triggered for L<txt|"http://...">
            if (Renderer.OutputOptions["breakURIs"] and
                  re.search(r"https?://", token)):
                avail = effWidth-lineLen-1
                loc = token.rfind("/", 1, avail)
                #lg.log(logging.INFO-0,
                #    "# Breaking URI, avail %d, token %d, / at %d: '%s'.\n"
                #    % (avail, tokenLen, loc, token))
                if (loc>-1): # break there
                    line += " " + token[0:loc+1]
                    token = token[loc+1:]
            buf += line + "\n"
            line = (" " * (hangingIndent+marginLeft)) + token
            lineLen = marginLeft + tokenLen
        if (line != ""): buf += line + "\n"
        return(buf[1:])  # Why is this?

    def toHTML(self):
        assert(False)

    def tostring(self):
        return("### %5s: bl %1d ind %2d marker '%s' text '%s'" %
            (self.type, self.blanks, len(self.indent), self.marker, self.text))


##########################################################################
#
class ListManager:
    def __init__(self):
        self.formatOptions = {}

    def doListItem(self, line, code):
        """Set up indentation level and marker(s) for a list item.
        TODO: Better to do during makeBlocks or during rendering?
        """

        depth = len(code)
        ind = self.formatOptions["indentSize"] * depth
        buf = (" " * ind)
        while (len(self.listCounts)<=depth): self.listCounts.append(1)
        self.listCounts[depth] += 1
        lg.log(logging.INFO-1, "In doListItem: code %-8s depth %d counts: %s." %
            (code, depth, str(self.listCounts)))
        if (code[-1] == "*"):
            buf += self.getULMarker(depth)
        else:  # "+" for MarkDown, "#" for MediaWiki
            buf += (self.formatOptions["OLPrefix"] + self.getOLMarker(depth) +
                self.formatOptions["OLSuffix"])

        if (self.formatOptions["color"]):
            buf = StyleValues.colorize(buf, fg="blue", bold=True)
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
        if (level >= len(self.formatOptions["ULMarkers"])):
            level = len(self.formatOptions["ULMarkers"]) - 1
        return(self.formatOptions["ULMarkers"][level])

    def getOLMarker(self, level, increment=True):
        """Generate the right ordered list number, given level.
        CSS types: decimal, lower-alpha, upper-latin, upper-roman, none,....
        @param increment: If set, bump the stored number.
        """
        if (level>len(self.listCounts)): n = self.listCounts[-1]
        else: n = self.listCounts[level]
        if (level >= len(self.formatOptions["OLTypes"])):
            theType = self.formatOptions["OLTypes"][-1]
        else:
            theType = self.formatOptions["OLTypes"][level]
        theType = theType.lower()
        if (theType=="lower" or theType=="lower-alpha"):
            return(string.ascii_lowercase[n])
        elif (theType=="upper" or theType=="upper-alpha"):
            return(string.ascii_uppercase[n])
        elif (theType=="decimal"):
            return(str(n))
        elif (theType=="none"):
            return("")
        elif (theType=="lower-roman"):
            return(ListManager.getRoman(n).lower())
        elif (theType=="upper-roman"):
            return(ListManager.getRoman(n).upper())
        return(string.ascii_uppercase[n])

    # List of enough Roman numerals.
    #
    romans = [ "",
        "i", "ii", "iii", "iv", "v",
        "vi", "vii", "viii", "ix", "x",
        "xi", "xii", "xiii", "xiv", "xv",
        "xvi", "xvii", "xviii", "xix", "xx",
        "xxi", "xxii", "xxiii", "xxiv", "xxv",
        "xxvi", "xxvii", "xxviii", "xxix", "xxx",
        "xxxi", "xxxii", "xxxiii", "xxxiv", "xxxv",
        "xxxvi", "xxxvii", "xxxviii", "xxxix", "xl",
        "xli", "xlii", "xliii", "xliv", "xlv",
        "xlvi", "xlvii", "xlviii", "xlix", "l",
        "li", "lii", "liii", "liv", "lv",
        "lvi", "lvii", "lviii", "lix", "lx",
        "lxi", "lxii", "lxiii", "lxiv", "lxv",
        "lxvi", "lxvii", "lxviii", "lxix", "lxx",
        "lxxi", "lxxii", "lxxiii", "lxxiv", "lxxv",
        "lxxvi", "lxxvii", "lxxviii", "lxxix", "lxxx",
        "lxxxi", "lxxxii", "lxxxiii", "lxxxiv", "lxxxv",
        "lxxxvi", "lxxxvii", "lxxxviii", "lxxxix", "xc",
        "xci", "xcii", "xciii", "xciv", "xcv",
        "xcvi", "xcvii", "xcviii", "xcix", "c",
    ]

    @staticmethod
    def getRoman(n):
        """Convert to Roman numerals. Limited range.
        """
        #return( "x" * int(n/10) + ListManager.romans[n % 10])
        return ListManager.romans[n]


###############################################################################
#
class FormatRun:
    """Part of a displayed line.
    """
    def __init__(self, text, begOffset, endOffset, emphType=None):
        self.text = text
        self.begOffset = begOffset
        self.endOffset = endOffset
        self.styleSpec = StyleSpec()

    def render(self):
        return self.text


##############################################################################
#
class StyleValues:
    """Enums for various formatting classes and style property values.
    """
    # DisplayTypes
    DSP_HIDDEN  = 0
    DSP_INLINE  = 1
    DSP_BLOCK   = 2
    DSP_TABLE   = 3
    DSP_TROW    = 4
    DSP_TCELL   = 5
    DSP_IMAGE   = 6  # Not yet...
    DSP_MARKER  = 7  # Bullet, item number, defterm, BNF LHS,...

    # All blocks get slotted into one of these types, plus a nesting
    # level for ITEM and HEAD. There should be a Block subclass for each one.
    BLK_TEXT    = 1
    BLK_ITEM    = 2
    BLK_HEAD    = 3
    BLK_PRE     = 4
    BLK_ROW     = 5
    BLK_BNF     = 6
    BLK_RULE    = 7
    BLK_QUOTE   = 8

    BlockClasses = {
        "TEXT":     { "display":"block", "marginTop":1, },
        "ITEM":     { "display":"block", "marginLeft":4, "marker":"*"},
        "HEAD":     { "display":"block", "font":"bold", },
        "PRE":      { "display":"block", "font":"monospace", },
        "ROW":      { "display":"block", "font":"monospace", },
        "BNF":      { "display":"block", "font":"monospace", },
        "RULE":     { "display":"block", "font":"monospace", },
        "QUOTE":    { "display":"block", "marginLeft":4, },
    }

    # Union of most inline classes known to MD, POD, and HTML.
    # Distinguished by something like a namespace prefix....
    InlineClasses = {
        # Markdown
        "M:BI":     { "bold":1, "ital":1},
        "M:BD":     { "bold":1, },
        "M:IT":     { "italic":1, },
        "M:TT":     { "monospace":1, },
        # POD
        "P:B":      { "bold":1, },
        "P:C":      { "monospace":1, },  # code
        "P:E":      {           },  # escape ### TODO figure something out
        "P:F":      { "monospace":1, },  # filename
        "P:I":      { "italic":1, },
        "P:L":      { "bold":1, "color":"blue", },  # link
        "P:S":      { "bold":1, },
        "P:X":      { "bold":1, },
        # HTML
        "H:B":      { "bold":1, },
        "H:I":      { "italic":1, },
        "H:TT":     { "monospace":1, },
        "H:EM":     { "italic":1, },
        "H:STRONG": { "bold":1, },
        "H:a":      { "bold":1, "color":"blue", },
        "H:abbr":   {           },
        "H:acronym":{           },
        "H:big":    {           },  ###
        "H:code":   { "monospace":1, },
        "H:data":   { "monospace":1, },
        "H:del":    { "strike":1, },
        "H:dfn":    {           },
        "H:em":     { "italic":1, },
        "H:ins":    { "color":"red", },
        "H:kbd":    { "monospace":1, },
        "H:label":  {           },
        "H:q":      { "bold":1, },  ###
        "H:small":  { "bold":1, },  ###
        "H:span":   {           },
        "H:strong": { "bold":1, },
        "H:sub":    { "bold":1, },  ###
        "H:sup":    { "bold":1, },  ###
        "H:u":      { "underline":1, },
        "H:var":    { "monospace":1, },
    }

    # These are the fonts available as Unicode 'Mathematical' variations on
    # Latin. A similar list is available for Greek, and many more for digits.
    # Combining accents could be used to support more languages.
    #
    # Eww, how do BOLD, ITALIC, combine with ANSI terminal effects?
    #
    FontTypes = {
        # Name                        ( Upper    Lower,   Digits   Exceptions )
        "LATIN":                      ( 0x00041, 0x00061, 0x00031, "" ),
        "BOLD":                       ( 0x1d400, 0x1d41a, 0x1d7ce, "" ),
        "ITALIC":                     ( 0x1d434, 0x1d44e, None,    "h" ),
        "BOLD ITALIC":                ( 0x1d468, 0x1d482, None,    "" ),
        "SCRIPT":                     ( 0x1d49c, 0x1d4b6, None,    "BEFHILMR ego" ),
        "BOLD SCRIPT":                ( 0x1d4d0, 0x1d4ea, None,    "" ),
        "FRAKTUR":                    ( 0x1d504, 0x1d51e, None,    "CHIRZ" ),
        "DOUBLE-STRUCK":              ( 0x1d538, 0x1d552, 0x1d7d8, "CHNPQRZ" ),
        "BOLD FRAKTUR":               ( 0x1d56c, 0x1d586, None,    "" ),
        "SANS-SERIF":                 ( 0x1d5a0, 0x1d586, 0x1d7e3, "" ),
        "SANS-SERIF BOLD":            ( 0x1d5d4, 0x1d5ee, 0x1d7ec, "" ),
        "SANS-SERIF ITALIC":          ( 0x1d608, 0x1d622, None,    "" ),
        "SANS-SERIF BOLD ITALIC":     ( 0x1d63c, 0x1d656, None,    "" ),
        "MONOSPACE":                  ( 0x1d670, 0x1d68a, 0x1d7f6, "" ),
        "CIRCLED":                    ( 0x024b6, 0x024d0, 0x0245f, "" ),
        "PARENTHESIZED":              ( 0x1f110, 0x0249c, 0x02473, "" ),

        "FULLWIDTH":                  ( 0x0FF21, 0x0FF41, 0x0FF10, "" ),
        "SUPERCRIPT":                 ( None,    None,    0x02070, "123" ),
        "SUBSCRIPT":                  ( None,    None,    0x02080, "" ),

        # Not available in lower case, only upper
        "SQUARED":                    ( 0x1f130, None,    None,    "" ),
        "NEGATIVE CIRCLED":           ( 0x1f150, None,    0x02775, "" ),
        "NEGATIVE SQUARED":           ( 0x1f170, None,    None,    "" ),
        #"REGIONAL INDICATOR SYMBOL":  ( 0x1f1e6, None,    None,    "" ),
    }

    @staticmethod
    def isFont(s):
        return s.upper() in StyleSpec.KnownFonts

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
    colorRegex    = re.compile(r"\x1b\[\d+(;\d+)*m")
    colorEnd = esc + "[0m"

    @staticmethod
    def colorize(s, fg="default", bg="default", bold=0):
        fgnum = StyleValues.colors[fg]
        cc = []
        if (fg!="default"):
            cc.append(str(fgnum))
        if (bg!="default"):
            bgnum = StyleValues.colors[bg] + 10
            cc.append(str(bgnum))
        if (bold):
            cc.append("1")
        ccstring = ";".join(cc)
        return(esc + "[" + ccstring + "m" + s + StyleValues.colorEnd)

    AlignTypes = { "L": 0, "C": 1, "R": 2, "D": 3, "F": 4, }


##############################################################################
#
class StyleSheet(dict):
    """Loosely modelled on CSS, but vastly simpler since:
    * dimensions only in lines and columns (monospace, etc)
    * only terminal-style formatting (color, ANSI effects, and Unicode)
    * fancy selectors, just a single type-name
    * no style inheritance, cascading, etc.
    """
    def __init__(self, ssName="ssDefault"):
        super(StyleSheet, self).__init__()
        self.ssName = ssName


##############################################################################
#
class Style:
    """A single style definition, which is a set of fairly simple properties.
    Most properties are modelled on CSS, but:
        * The only measurement unit is monospace columns
        * The only fonts alternatives are Unicode ranges (Mathematical Bold...)
        * Color and effects are just ANSI terminal colors
    """
    disp = set(["INLINE", "BLOCK", "NONE", "TROW", "TCELL"])
    wisp = set(["PRE", "WRAP", "NORM", "TRUNC"])
    font = lambda x: x in StyleValues.FontTypes
    color = set(
        ["RED", "YELLOW", "GREEN", "BLUE", "MAGENTA", "CYAN", "WHITE", "BLACK"])
    align = set(["LEFT", "CENTER", "RIGHT", "DECIMAL", "FULL"])
    mark = set(["*", "+", "-", "•"])  # TODO: Add more

    StylePropDefaults = {
        # Whether we're block, inline, hidden, etc.
        "display":         ( disp,  "INLINE" ),
        "whitespace":      ( wisp,  "WRAP" ),

        "unicodeMath":     ( bool,  True ),
        "bold":            ( bool,  False ),
        "ital":            ( bool,  False ),
        "monospace":       ( bool,  False ),
        "underline":       ( bool,  False ),
        "nobreak":         ( bool,  False ),
        "font":            ( font,  "ROMAN" ),
        "backgroundColor": ( color, "default" ),
        "color":           ( color, "default" ),
        "reversed":        ( bool,  False ),

        "markerType":      ( mark,   "BULLET" ),
        "textBefore":      ( str,    "" ),
        "textAfter":       ( str,    "" ),
        "hot":             ( bool,   "" ),

        # Block-only properties
        "align":           ( align,  "LEFT" ),
        "border":          ( bool,  False ),
        "borderColor":     ( bool,  False ),
        "borderUnicode":   ( bool,  True ),
        "marginLeft":      ( int,    0 ),
        "marginRight":     ( int,    0 ),
        "marginTop":       ( int,    0 ),
        "marginBottom":    ( int,    0 ),
        "width":           ( int,    0 ),
    }

    def __init__(self):
        for k, v in StylePropDefaults.items():
            self.__setitem__(k, v)


##########################################################################
# Onward to RENDERING
#
class Renderer:
    def __init__(self, styleSheet, blocks):
        self.styleSheet = styleSheet
        self.blocks = blocks
        self.gaveEscMessage = False

        # TODO: Change these to be more like CSS
        Renderer.OutputOptions = {
            "defaults"    : False,
            "color"       : True,           # Use ANSI terminal color
            "breakURIs"   : True,           # Allow breaking line at / in URIs?
            "sectionNums" : True,           # Generate heading numbers
            "width"       : None,           # Output display width
            "indentSize"  : 4,              # Spaces of indent per level
            "quoteType"   : "D",  # D double curly, S single curly, A angle, else '"'
            "OLPrefix"    : "", # such as "("
            "OLSuffix"    : "", # such as ":"
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

    def render(self):
        """Turn the block/run structure + styleSheet into an array of
        rendered visual lines, properly wrapped, colorized, etc.
        """
        visualLines = []
        for b in self.blocks:
            visualLines.extend(b.render(self.styleSheet))
        return visualLines


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
        if (isinstance(attrs, str)):
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
        txt = re.sub(r"&", "&amp;", txt)
        txt = re.sub(r"<", "&lt;", txt)
        self.dest.write(txt)

    def closeElement(self, tag=None, required=False):
        if (not tag):
            tag = self.tagStack[-1]
        elif (tag not in self.tagStack):
            if (required): lg.log(logging.INFO-1,
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


###############################################################################
# New/untested
#
if __name__ == "__main__":
    print("*** Testing MarkupHelpFormatter.py ***\n")

    while (len(sys.argv) > 1 and sys.argv[1] == "-v"):
        verbose += 1
        del sys.argv[1]
    if (len(sys.argv)<2):
        print("*** Using internal test data ***")
        testText = """=Usage=

This is some test POD for testing MarkupHelpFormatter.
Hopefully these lines wrap,
too, even though they are
not special format objects.



This, however, is a new paragraph.

    While this is an indented block,
    with each "w" starting a new line
    which looks like this.

* Item 1 of an ''unnumbered'' list.
* Item 2 of the same unnumbered list, but with some longer text that we expect should
wrap visual lines but stay as one paragraph block, if this works at all.
*# Then there are numbered subitems
*# And bacon strips.
*# And bacon strips.
* And back out to the first-level
list.

And back `out` of `the` list. Whee.

==Subheadings are cool==

===As are subsubheadings===

Those, in turn, can have content, even with [links].
"""
    else:
        try:
            testText = open(sys.argv[1], "r").read()
        except IOError as e:
            print("Can't read file '%s'." % (sys.argv[1]))
            sys.exit()

    mhf = MarkupHelpFormatter()
    print(mhf._format_text(testText))

    print("\n*** DONE ***\n")
    sys.exit()
