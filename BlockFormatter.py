#!/usr/bin/env python3
#
# BlockFormatter: Upgrade for Python argparse help formatting.
# 2013-04-18: Written by Steven J. DeRose.
#
# This is "Level" 1, which wraps lines to fit a given width, but retains
# blank lines and line-breaks before MarkDown-ish lists, tables, headings, etc.
# It does no colorizing, fonts, etc.
#
#pylint: disable=W0212
#
import sys
import re
import os
import codecs
import argparse
from typing import Tuple, Dict, Any
import logging

lg = logging.getLogger("BlockFormatter")

__metadata__ = {
    "title"        : "BlockFormatter",
    "description"  : "Simple formatter class for Python argparse.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2013-04-18",
    "modified"     : "2021-11-12",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/",
}
__version__ = __metadata__["modified"]

descr = """
=Description=

This
package
defines
a
class that can be used with Python's
`argparse` package in order to get better formatting.
It recognizes Markdown, POD, blank lines, and/or similar conventions,
and divides the input into paragraph-level blocks, within which text
is wrapped.


==Formatting Behavior==

Blank lines remain. This includes lines that contain only spaces and TABs
(they will actually be empty on output, however).

Lines that are indented get a newline and indentation before them,
but no blank line (unless there was one there in the input too). Tabs are
expanded in the indentation, assuming tabstops every 4 spaces unless
the 'tabstops' option is set.

Unindented lines are wrapped with preceding lines, except:
* when the previous lines looks like a heading, horizontal rule, etc; or
* when the current line starts with a markdown-like block markup such as [*=\\d].

If you set environment variable "BF_ENABLE", it will use ANSI terminal escapes
to emphasize headings.

==BlockFormatter(argparse.HelpFormatter)==

This simple class is like the default argparse formatter except that
it does ''not'' wrap lines across blank lines. That is, blank lines stay there.

===To use it with argparse===

    from BlockFormatter import BlockFormatter

    doc = ""
    =Description=

    This is a simple formatter. You can use it with `argparse` in order to
    get prettier formatting. You can just use blank lines and indentation,
    or use MarkDown-like conventions (like asterisk at start of line) that
    will also preventing aggressive line-wrapping.

    # This is just a (non-displayed) comment.

    * It's useful.
    * It's easy.
    * It's *upgradeable*.
    ...
    ""

    BlockFormatter._options["comment"] = "#"
    parser = argparse.ArgumentParser(description=doc,
        formatter_class=BlockFormatter)

Options are discussed below.

===To use it from Python in general===

    from BlockFormatter import BlockFormatter
    doc = "..."
    hf = BlockFormatter(None)
    BlockFormatter._options["tabStops"] = 8
    ...
    print(hf._format_text(doc))

===To use it from the command line===

    BlockFormatter.py [options] [file.md]

==Options==

There is a class variable `BlockFormatter._options`, which is a dict that
defaults to:

    _options = {
        "verbose":     0,
        "showInvis":   False,
        "tabStops":    4,
        "hangIndent":  2,
        "xescapes":    False,
        "uescapes":    False,
        "entities":    False,
        "breakLong":   False,
        "altFill":     None,
        "comment":     "//",
        "pager":       None,
    }

If you are using `BlockFormatter` via the command line, you can set these
with options, such as "--showInvis" or "--tab 8".
If you are using it from Python code (such as with `argparse`,
you can set them directly, like:
    BlockFormatter._options["tabStops"] = 8

"verbose" can be increased to generate debugging messages.

"tabStops" is the interval to assume for expanding tabs.

"showInvis" causes all C0 control characters (except the newlines
used to line-break the
output) to appear instead as their Unicode "control pictures", near U+2400.

"hangIndent" is the number of extra columns to indent non-first lines of
indented blocks (for example, 2 to indent past a bullet and following space for
list-items).

"xescapes" expands \\xFF-style codes to actual characters (experimental). This
happens after line-breaking, tab expansion, etc.

"uescapes" expands \\uFFFF-style codes to actual characters (experimental).
This happens after "xescapes".

"entities", once implemented, will expand XML/HTML character references.

"breakLong", once implemented, will enable smarter line-breaking when faced
with very long tokens such as URLs.

"altFill" can be set to a callable replacement for _fill_text().
One such is provided: BlockFormatter._alt_fill (experimental).

"comment" is a string that identifies comment lines (no space before).

"page" is the path to a program to send output to, instead of the default.
In the case of argparse,


=Related commands and libraries=

Python's "argparse". It interfaces by passing formatter_class=BlockFormatter
to the constructor (however, I gather there is no promise that this will
not change). Inside, it uses these methods:

    def print_usage(self, file=None):
        if file is None:
            file = _sys.stdout
        self._print_message(self.format_usage(), file)

    def print_help(self, file=None):
        if file is None:
            file = _sys.stdout
        self._print_message(self.format_help(), file)

    def _print_message(self, message, file=None):
        if message:
            if file is None:
                file = _sys.stderr
            file.write(message)


==This series of formatters==

This is the lowest level of my formatters: it only outputs a single, monospace
font, with no support for color, bold, etc.

One step up is `BlockFormatterPlus`, which adds:
* more general support for ANSI terminal basic color and effects (by integrating
my `ColorManager.py` package (q.v.)), and
font variation via Unicode's alternate Latin alphabets
(see my `mathAlphanumerics.py` package). This provides
italic, bold, script, double-struck, sans-serif, etc.).

Another step up, but not really finished/working yet, is my formatter for
MarkDown, MediaWiki, and POD, which adds customizable input parsing and
output styles.

==Other related items==

A different Python Markdown formatter (though not, to my knowledge,
integrated with argparse), is [https://pypi.org/project/markdown-formatter/].

My `argparsePP.py` add various other features to argparse, such as
alternative hyphenation conventions; reversible boolean; and many more types.

My `markdown2Xml.py` converts various kinds of Markdown to various XML
schemas, HTML, etc.

My `pod2markdown.py` converts Perl "POD" to Markdown.


=Known bugs and limitations=

* It seems that the API in `argparse` for formatting
is not considered "public" -- so attempts like this to subclass it
could break any time. See [https://stackoverflow.com/questions/29484443].
But it also does not seem to change much.

* Does not support the MarkDown way of marking headings by adding a
following line of "=" for level 1, or "-". I like the Wikipedia and other
variants much better, for what I think are very good reasons.

* Does not support MarkDown per se's "Two spaces at the end of a line
produces a line break." I think using impossible-to-see markup that
some editors will quietly delete is a non-starter.


=To Do=

* Hook up _alt_fill for line-wrapping to allow U+200B ZERO WIDTH SPACE.
* Handle backslashed line-initials.
* Finish support for command-line setting of options.
* Long tokens such as URIs should be able to break at slashes, etc.
* Option to page the output, or send directly to "less".
* Keep in sync with `BlockFormatterPlus`, etc.
* Add "<" to block-indicators?
* Add ">" to block-indicators, for "included mail"?


=Rights=

This program is Copyright 2014 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see [here|"https://creativecommons.org"].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].

Thanks to Anthon van der Neut for help on integrating with `argparse`. Also:
    * [http://stackoverflow.com/questions/3853722]
    * [https://bitbucket.org/ruamel/std.argparse/src]
    * [http://hg.python.org/cpython/file/2.7/Lib/argparse.py]
    * [https://docs.python.org/2/library/textwrap.html]


=History=

2014-2015: Written by Steven J. DeRose, along with `MarkupHelpFormatter`.
They were together in `MarkupHelpFormatter.py`.

2020-03-04: I split this class out to a separate file and improved it a bit,
for example indenting non-first lines of indented blocks, expanding tabs,
adding the various options.

2020-08-22: Improve handling of MarkDown-like lines. Simplify wrapping.
Refactor entity/escape/tab handling.

2020-10-08ff: Add `ansify()` for simple emphasis.

2021-11-12: mypy checks.


=Options=
"""


##############################################################################
# There are more Unicode chars that can go here....
#
esc = chr(27)
quoteChars = {
    "lsquo":   chr(0x2018), "rsquo":   chr(0x2019),
    "ldquo":   chr(0x201C), "rdquo":   chr(0x201D),
    "lsaquo":  chr(0x2039), "rsaquo":  chr(0x203A),
    "ldaquo":  chr(0x00AB), "rdaquo":  chr(0x00BB),
}
dashChars = {
    "endash":  chr(0x2013), "emdash":  chr(0x2014),
    "shy":     chr(0x00AD), "hypoint": chr(0x2027),
    "hyminus": chr(0x002D),
}
spaceChars = {
    "ensp":    chr(0x2002), "emsp":    chr(0x2003),
    "thinsp":  chr(0x2009), "hairsp":  chr(0x200A),
    "zerosp":  chr(0x200B), "nbsp":    chr(0x00A0),
}
specialChars = {
    "lt":      "<",            "gt":      ">",
    "apos":    "'",            "quo":     '"',
    "amp":     "&",            "hellip":  chr(0x2026),
}

specialChars.update(quoteChars)
specialChars.update(dashChars)
specialChars.update(spaceChars)
breakableExpr = r"[-\s%s]" % (specialChars)

def makeVis(s:str):
    """Turn control characters into Unicode Control Pictures.
    TODO: Make wrapping treat these as breakable?
    """
    return re.sub(r"([\x01-\x0F\x11-\x1F])",  # NOT NEWLINE!
        lambda mat: chr(0x2400 + ord(mat.group(1))), s)

def toPix(mat):
    """Make control chars and space visible.
    """
    return chr(0x2400 + ord(mat.group(1)))

def xescapes(s:str):
    """Replace \\x escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r"\\x([0-9a-f][0-9a-f])",
        lambda mat: chr(int(mat.group(1), 16)), s, re.I)

def uescapes(s:str):
    """Replace \\u escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r"\\u([0-9a-f][0-9a-f][0-9a-f][0-9a-f])",
        lambda mat: chr(int(mat.group(1), 16)), s, re.I)


##############################################################################
# (for more complete support see ColorManager.py)
#
ansiCodes = {
    "bold":      ( "\x1B[1m", "\x1B[22m" ),  # TODO Check off-code?
    "faint":     ( "\x1B[2m", "\x1B[0m" ),
    "italic":    ( "\x1B[3m", "\x1B[0m" ),  # (rare)
    "underline": ( "\x1B[4m", "\x1B[0m" ),  # aka 'ul'
    "blink":     ( "\x1B[5m", "\x1B[0m" ),
    "fblink":    ( "\x1B[6m", "\x1B[0m" ),  # aka 'fastblink'   (rare)
    "reverse":   ( "\x1B[7m", "\x1B[0m" ),  # aka 'inverse'
    "concealed": ( "\x1B[8m", "\x1B[0m" ),  # aka 'invisible' or 'hidden'
    "strike":    ( "\x1B[9m", "\x1B[0m" ),  # aka 'strikethru' or 'strikethrough'
    "plain":     ( "\x1B[0m", "\x1B[0m" ),  # (can be used to express "no special effect")
    "inverse":   ( "\x1B[7m", "\x1B[27m" ),

    #
    "black":     ( "\x1B[30m", "\x1B[m" ),
    "red":       ( "\x1B[31m", "\x1B[m" ),
    "green":     ( "\x1B[32m", "\x1B[m" ),
    "yellow":    ( "\x1B[33m", "\x1B[m" ),
    "blue":      ( "\x1B[34m", "\x1B[m" ),
    "magenta":   ( "\x1B[35m", "\x1B[m" ),
    "cyan":      ( "\x1B[36m", "\x1B[m" ),
    "white":     ( "\x1B[37m", "\x1B[m" ),
}

def effect(mat, effectName:str) -> str:
    return ansiCodes[effectName][0] + mat.group() + ansiCodes[effectName][1]

def ansify(blockText:str) -> str:
    """Turn typical markdown into itself + ANSI effects.
    This doesn't drop the delimiters. If it did, it would have to happen before
    line-breaking, and line-breaking would need to be careful to step around escapes.
    """
    t = blockText
    t = re.sub(r"(`[^`]+`)",      lambda foo: effect(foo, "bold"), t)      # `command`
    t = re.sub(r"(^[=#].*$)",     lambda foo: effect(foo, "inverse"), t)   # =heading=
    t = re.sub(r"(\[[^\]\n]+\])", lambda foo: effect(foo, "blue"), t)      # [link]
    t = re.sub(r"('''[^']+''')",  lambda foo: effect(foo, "magenta"), t)   # '''italic'''
    #t = re.sub(r"( ''[^']+'' )",    lambda foo: effect(foo, "bold"), t)      # ''bold''
    return t


##############################################################################
# See markdown2Xml.py
#
blockTypes = set([
    "BLANK",       # whitespace-only (block-separator)
    "PRE",         # Pretty much just means "indented"
    "HEAD",        # whatever level
    "RULE",        # horizontal rule
    "TROW",        # table row
    "ITEM",        # list item
    "DT",          # definition term (?)
    "DD",          # definition description
    "PARA",        # plain paragraph
    "COMMENT",     # comment line/obj
    ])

class Block:
    """A single block (para, listitem, headings, table row, etc), as
    teased out by linesToBlocks().
    """
    def __init__(self, btype:str="PARA", text: str="", level:int=0, typeSequence=None, cols:int=None):
        assert btype in blockTypes
        self.btype = btype                # kind of block
        self.text = text                  # accumulated text content
        self.level = level                # heading OR indentation level
        self.typeSequence = typeSequence  # nested listed, such as "##*#*"
        self.cols = cols                  # num columns in a table row

    def add(self, text):
        self.text += text


###############################################################################
#
class BlockFormatter(argparse.HelpFormatter):
    """A formatter for argparse. This differs from the default formatter, in
    that it does *not* wrap lines across blank or indented lines, but recognizes
    and responds to simple markup.

    Sequence seems to be:
        _format_text(self, txt)
            _format(self, txt, encoding="utf8", color=1, width=0)
                wrap(para, width)
                    _fill_text(self, text, width, indent)
    """
    _options:Dict[str, Any] = {
        "verbose":     0,         # Extra messages?
        "showInvis":   False,     # Replace invisible chars
        "tabStops":    4,         # Expand tabs per this interval
        "hangIndent":  2,         # Add to non-first lines of list items etc.
        "xescapes":    False,     # Recognize \xFF codes
        "uescapes":    False,     # Recognize \uFFFF codes
        "entities":    False,     # Recognize &#65; &#x41; &bull; etc.
        "breakLong":   False,     # Can split inside long tokens (like URLs)
        "altFill":     None,      # Replacement for _fill_text().
        "comment":     "$",       # Comment indicator
        "externalParser": None,
        "pager":       None,      # Send result to this program (say, "less").
    }

    def __init__(self, prog=None):
        super(BlockFormatter, self).__init__(prog)

    def _fill_text(self, text:str, width:int, indent: str) -> str:
        """Override the aggressive line-filler, to do these things:
            * Retain blank lines
            * Keep newline before line-initial [*#] (probably list items)
            * For indented blocks, apply their indented to following unindented
              lines in the same block.
        NOTE: "indent" expects a string, not a number of columns.
        """
        #print("_fill_text called for %d chars." % (len(text)))
        hang = int(BlockFormatter._options["hangIndent"])

        # Divide at blank lines line breaks to keep
        if (BlockFormatter._options["externalParser"]):
            #from markdown2Xml import markdown2Xml  # From my XML/CONVERT
            #mdx = markdown2Xml()
            #recs = re.split(r"\n", text)
            #blocksObjs = mdx.linesToBlocks(recs)
            #blocks = [ bl.text for bl in blocksObjs ]
            assert False
        else:
            blocks = BlockFormatter.makeBlocks(text)

        for i in range(len(blocks)):
            lg.log(logging.INFO-2, "\n******* BLOCK %d (len %d): //%s//" %
                (i, len(blocks[i]), blocks[i]))
            item, istring = BlockFormatter.doSpecialChars(blocks[i])

            #print("### width %s, indent '%s', ind %s:\n    |%s|%s|" %
            #    (width, indent, ind, mat.group(1), mat.group(2)))
            # _fill_text return a string with newlines, not a list.

            if (istring!=""): indParam = indent + istring + (" "*hang)
            else: indParam = indent

            #pylint: disable=E1102
            if (callable(BlockFormatter._options["altFill"])):
                withNewlines = self._options["altFill"](item, width, indParam)
            #pylint: enable=E1102
            else:
                withNewlines = super(BlockFormatter, self)._fill_text(
                    item, width, indParam)
            if (istring and withNewlines.startswith(" "*hang)):
                withNewlines = withNewlines[hang:]  # Un-hang first line

            if ("BF_ENABLE" in os.environ):
                withNewlines = ansify(withNewlines)

            blocks[i] = withNewlines
        lg.log(logging.INFO-2, "\n******* FORMATTING DONE *******\n")
        return "\n".join(blocks)

    @staticmethod
    def makeBlocks(text: str) -> list:
        """Parse the input line by line and:
            * discard comments
            * combine each wrappable group of lines into one
        Explicit blank lines stay as one block each.
        The returned blocks do NOT have final \n.
        TODO: Use markdown2Xml.py
        """
        blocks = [ "" ]
        breakAfter = False
        for t in re.split(r"\n", text, flags=re.MULTILINE | re.UNICODE):
            blockType = "???"
            if (BlockFormatter._options["comment"]!="" and
                t.startswith(BlockFormatter._options["comment"])):
                blockType = "COMMENT"
            elif (t.strip() == ""):                 # blank line
                blocks.append("")
                breakAfter = True
                blockType = "BLANK"
            elif (t[0] == "="):                     # heading
                blocks.append(t)
                breakAfter = True
                blockType = "HEAD"
            elif (re.match(r"-{3,}|={3,}\s*$", t)): # rule
                blocks.append("=" * 79)
                breakAfter = True
                blockType = "RULE"
            elif (t[0] == "|"):                     # table row
                blocks.append(t)
                breakAfter = True
                blockType = "TROW"
            elif (t[0] in "*#:0123456789 \t"):      # keep line break
                blocks.append(t)
                blockType = "ITEM"
            else:                                   # continued text
                if (breakAfter):
                    blocks.append(t)
                    breakAfter = False
                    blockType = "PARA"

                else:
                    if (blocks[-1] != ""): blocks[-1] += " "
                    blocks[-1] += t
                    blockType = "PARA"
            #print("+%s: %s" % (blockType, blocks[-1]))
            assert blockType in blockTypes
        return blocks

    @staticmethod
    def doSpecialChars(item: str) -> Tuple[str, str]:
        """Expand tabs, escapes, entities, etc.
        Return the expanded text, but with leading indent separate
        TODO: Switch to markdown2Xml.InlineMapper class.
        """
        indentString = ""
        mat = re.match(r"^([ \t]+)", item)
        if (mat):
            indentString = mat.group(1).expandtabs(
                BlockFormatter._options["tabStops"])
            item = item[len(mat.group(1)):]
        if (BlockFormatter._options["xescapes"]):
            item = xescapes(item)
        if (BlockFormatter._options["uescapes"]):
            item = uescapes(item)
        if (BlockFormatter._options["entities"]):
            assert False, "entities not yet implemented"
        if (BlockFormatter._options["showInvis"]):
            item = makeVis(item)
        return item, indentString

    @staticmethod
    def _alt_fill(item:str, width:int, indentString: str) -> str:
        """In case _fill_text changes or goes away....
        The splitting regex forces a break at the longest non-space token
        smaller than line width (minus indent).
        Python \\s does not include U+200b, ZERO WIDTH SPACE and some other.
        TODO: factor out our substitution for \\s, and add more variant spaces.
        """
        lines = []
        tokenExpr = r"%s*(\S.{,%d}(?=%s))" % (
            breakableExpr, width-len(indentString)-2, breakableExpr)
        for x in re.finditer(tokenExpr, item, re.MULTILINE):
            #print("Wrap trial: '%s'" % (x.group(1)))
            lines.append(indentString + x.group(1))
        return "\n".join(lines)


###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)

        parser.add_argument(
            "--altFill", action="store_true",
            help="Use an alternate method to fill lines.")
        parser.add_argument(
            "--breakLong", action="store_true",
            help="Allow breaking long tokens (like URLs) at non-spaces.")
        parser.add_argument(
            "--comment", type=str, metavar="C", default="//",
            help="Treat lines starting with this, as comment lines.")
        parser.add_argument(
            "--entities", action="store_true",
            help="Recognize HTML/XML special characters.")
        parser.add_argument(
            "--externalParser", action="store_true",
            help="Use markdown2Xml.py for parsing, instead of local code.")
        parser.add_argument(
            "--hangIndent", type=int, default=2,
            help="Apply hanging indents of this many spaces.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character set for input files. Default: utf-8.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E",
            help="Use this character set for output files.")
        parser.add_argument(
            "--page", "--less", "--more", action="store_true",
            help="Send the output to `less` instead of just stdout.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--showInvis", action="store_true",
            help="Turn control characters etc. to visible forms.")
        parser.add_argument(
            "--split", action="store_true",
            help="Just split lines.")
        parser.add_argument(
            "--tabStops", type=int, default=4,
            help="Assume tabstops every n columns.")
        parser.add_argument(
            "--uescapes", action="store_true",
            help="Recognize \\uFFFF-style special characters.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")
        parser.add_argument(
            "--xescapes", action="store_true",
            help="Recognize \\xFF-style special characters.")

        parser.add_argument(
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #

    args = processOptions()
    BlockFormatter._options["verbose"] = args.verbose
    BlockFormatter._options["externalParser"] = args.externalParser
    if (args.altFill):
        BlockFormatter._options["altFill"] = BlockFormatter._alt_fill

    print("*** Testing BlockFormatter.py (level 1) ***\n")

    if (len(args.files) == 0):
        tfile = "/tmp/BlockFormatter.md"
        lg.info("No files specified, copying own help text to %s" % (tfile))
        fh = codecs.open(tfile, "wb", encoding=args.iencoding)
        fh.write(descr)
        fh.close()
        args.files.append(tfile)

    for path0 in args.files:
        lg.info("\n******* Starting test file '%s'" % (path0))
        fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
        testText = fh0.read()
        if (args.split):
            print("*** Just splitting")
            lenSoFar = 0
            for i0, t0 in enumerate(
                re.split(r"\n", testText, flags=re.MULTILINE | re.UNICODE)):

                print("%04d (%6d)==>%s<==\n" % (i0, lenSoFar, t0))
                lenSoFar += len(t0)
            sys.exit()

        hf = BlockFormatter(None)
        if (args.page):
            from subprocess import check_output
            tmpfile = "/tmp/BlockFormatter.txt"
            with codecs.open(tmpfile, "wb", encoding="utf-8") as ofh:
                ofh.write(testText)
            check_output([ "less", tmpfile])
        else:
            print(hf._format_text(testText))
