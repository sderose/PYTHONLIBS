#!/usr/bin/env python
#
# BlockFormatter.
# Upgrade for Python argparse, that don't forcibly wrap all text.
#
# This is "Level" 1, which wraps lines to fit a given width, but retains
# blank lines and line-breaks before MarkDown-ish lists, tables, headings, etc.
# It does no colorizing, fonts, etc.
#
#pylint: disable=W0212
#
import sys, re, codecs
import argparse
#import html

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    def unbackslash(self, s):
        return s.decode('string_escape') # python2
else:
    def unbackslash(self, s):
        return bytes(s, "utf-8").decode("unicode_escape") # python3
    def unichr(n): return chr(n)

__metadata__ = {
    'title'        : "BlockFormatter.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2013-04-18",
    'modified'     : "2020-08-22",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/",
    'description'  :
        'Simple formatter class for Python argparse.',
}
__version__ = __metadata__['modified']

descr = """
=Description=

This
package
defines
a
class that can be used with Python's
`argparse` package in order to get better formatting.

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

    * It's useful.
    * It's easy.
    * It's upgradeable.
    ...
    ""

    parser = argparse.ArgumentParser(description=doc,
        formatter_class=BlockFormatter)

===To use it as an independent formatter===

    from BlockFormatter import BlockFormatter
    doc = "..."
    hf = BlockFormatter(None)
    print(hf._format_text(doc))


==Behavior==

Blank lines remain. This includes lines that contain only spaces and TABs
(they will actually be empty on output, however).

Lines that are indented get a newline and indentation before them,
but no blank line (unless there was one there in the input too). Tabs will be
expanded in the indentation, assuming tabstops every 4 spaces.

Unindented lines will be wrapped with preceding lines, except:
* when the previous lines looks like a heading, horizontal rule, etc; or
* when the current line start with a markdown-like block markup such as [*=\d].

==Options==

There is a class variable `BlockFormatter._options`, which is a dict that
defaults to:

    _options = {
        'verbose':     0,
        'showInvis':   False,
        'tabStops':    4,
        'hangIndent':  2,
        'xescapes':    False,
        'uescapes':    False,
        'entities':    False,
        'breakLong':   False,
        'altFill':     None,
        'comment':     '//',
    }

If you are using `BlockFormatter` via the command line, you can set these
with options. If you are using it from Python code (such as with `argparse`,
you can set them directly like:
    BlockFormatter._options['tabStops'] = 8

'verbose' can be increased to generate debugging messages.

'tabStops' is the interval to assume for expanding tabs.

'showInvis' causes all C0 control characters (except the newlines
used to line-break the
output) to appear instead as their Unicode "control pictures", near U+2400.

'hangIndent' is the number of extra columns to indent non-first lines of
indented blocks (for example, 2 to indent past a bullet and following space for
list-items).

'xescapes' expands \\xFF-style codes to actual characters (experimental). This
happens after line-breaking, tab expansion, etc.

'uescapes' expands \\uFFFF-style codes to actual characters (experimental).
This happens after 'xescapes'.

'entities', once implemented, will expand XML/HTML character references.

'breakLong', once implemented, will enable smarter line-breaking when faced
with very long tokens such as URLs.

'altFill' can be set to a callable replacement for _fill_text().
One such is provided: BlockFormatter._alt_fill (experimental).

'comment' is a string that identifies comment lines (no space before).


=Related commands and libraries=

This is the lowest level of my formatters: it only outputs a single, monospace
font, with no support for color, bold, etc.

One step up is `BlockFormatterPlus`, which adds:
* support for ANSI terminal basic color and effects (by integrating my `ColorManager.py` package (q.v.)), and
* emulation of font variation via Unicode's alternate Latin alphabets (by
integrating my `mathAlphanumerics.py` package (q.v.). This provides
italic, bold, script, double-struck, sans-serif, and other variations
(but only for Latin letters and Arabic digits).

Another step up, but not really finished/working yet, is my formatter for MarkDown, MediaWiki, and POD, which adds customizable input parsing and
output styles.

A different Python Markdown formatter (though not, to my knowledge, integrated with argparse), is [https://pypi.org/project/markdown-formatter/].

My `argparsePP.py` variant adds some other features to argparse itself:

* Adds a showDefaults option
* Adds a shortMetavars option (to save space on the screen)
* Supports alternative hyphen conventions
* Supports adding 'toggle' attributes, with '--no-' prefix (changeable)
* Add an 'anyInt' type that accepts decimal, hex, or octal numbers


=Known bugs and limitations=

* It seems that the API in `argparse` for formatting
(such as it is), is not considered "public" -- so attempts to subclass it
could break any time. See [https://stackoverflow.com/questions/29484443].
But it also does not seem to change much.

* Does not support the MarkDown way of marking headings by adding a
following line of "=" for level 1, or "-". I like the Wikipedia and other
variants much better, for what I think are very good reasons.

* Does not support MarkDown per se's "Two spaces at the end of a line
produces a line break." I think using impossible-to-see markup that
some editors will freely delete, is a non-starter.

=To Do=

* Handle backslashed line-initials.
* Finish support for command-line setting of options.
* Long tokens such as URIs should be able to break at slashes, etc.
* Option to page the output, or send directly to 'less'.
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

2020-03-04: I split this class out to a separate file, and improved it a bit,
for example indenting non-first lines of indented blocks, expanding tabs,
adding the various options.

2020-08-22: Improve handling of MarkDown-like lines. Simplify wrapping.
Refactor entity/escape/tab handling.


=Options=
"""

##############################################################################
#
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

def hMsg(level, msg):
    if (BlockFormatter._options['verbose']>=level):
        sys.stderr.write("\n*******" + msg+'\n')

def vMsg(level, msg):
    if (BlockFormatter._options['verbose']>=level):
        sys.stderr.write(msg+'\n')

def makeVis(s):
    """Turn control characters into Unicode Control Pictures.
    TODO: Make wrapping treat these as breakable?
    """
    return re.sub(r'([\x01-\x0F\x11-\x1F])', toPix, s)  # NOT NEWLINE!

def toPix(mat):
    """Make control chars and space visible.
    """
    return unichr(0x2400 + ord(mat.group(1)))

def xescapes(s):
    """Replace \\x escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r'\\x([0-9a-f][0-9a-f])',
        lambda mat: unichr(int(mat.group(1), 16)), s, re.I)

def uescapes(s):
    """Replace \\u escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r'\\u([0-9a-f][0-9a-f][0-9a-f][0-9a-f])',
        lambda mat: unichr(int(mat.group(1), 16)), s, re.I)


##############################################################################
#
class BlockFormatter(argparse.HelpFormatter):
    """A formatter for argparse. This differs from the default formatter, in
    that it does *not* wrap lines across blank or indented lines.

    Sequence seems to be:
        _format_text(self, txt)
            _format(self, txt, encoding="utf8", color=1, width=0)
                wrap(para, width)
                    _fill_text(self, text, width, indent)
    """
    _options = {
        'verbose':     0,         # Extra messages?
        'showInvis':   False,     # Replace invisible chars
        'tabStops':    4,         # Expand tabs per this interval
        'hangIndent':  2,         # Add to non-first lines of list items etc.
        'xescapes':    False,     # Recognize \xFF codes
        'uescapes':    False,     # Recognize \uFFFF codes
        'entities':    False,     # Recognize &#65; &#x41; &bull; etc.
        'breakLong':   False,     # Can split inside long tokens (like URLs)
        'altFill':     None,      # Replacement for _fill_text().
        'comment':     '$',       # Comment indicator
    }

    def _fill_text(self, text, width, indent):
        """Override the aggressive line-filler, to do these things:
            * Retain blank lines
            * Keep newline before line-initial [*#] (probably list items)
            * For indented blocks, apply their indented to following unindented
              lines in the same block.
        NOTE: 'indent' expects a string, not a number of columns.
        """
        #print("_fill_text called for %d chars." % (len(text)))
        hang = BlockFormatter._options['hangIndent']

        # Divide at blank lines line breaks to keep
        blocks = BlockFormatter.makeBlocks(text)
        for i in range(len(blocks)):
            vMsg(2, "\n******* BLOCK %d (len %d) *******" % (i, len(blocks[i])))
            item, istring = BlockFormatter.doSpecialChars(blocks[i])

            #print("### width %s, indent '%s', ind %s:\n    |%s|%s|" %
            #    (width, indent, ind, mat.group(1), mat.group(2)))
            # _fill_text return a string with newlines, not a list.

            if (istring!=''): indParam = indent + istring + (' '*hang)
            else: indParam = indent

            if (callable(BlockFormatter._options['altFill'])):
                withNewlines = self._options['altFill'](
                    item, width, indParam)
            else:
                withNewlines = super(BlockFormatter, self)._fill_text(
                    item, width, indParam)
            if (istring and withNewlines.startswith(' '*hang)):
                withNewlines = withNewlines[hang:]  # Un-hang first line

            blocks[i] = withNewlines
        vMsg(2, "\n******* FORMATTING DONE *******\n")
        return "\n".join(blocks)

    @staticmethod
    def makeBlocks(text):
        """Parse the input line by line and:
            * discard comments
            * combine each wrappable group of lines into one
        Explicit blank lines stay as one block each.
        The returned blocks do NOT have final \n.
        """
        blocks = [ "" ]
        breakAfter = False
        for t in re.split(r'\n', text, flags=re.MULTILINE | re.UNICODE):
            blockType = '???'
            if (BlockFormatter._options['comment']!='' and
                t.startswith(BlockFormatter._options['comment'])):
                blockType = 'COMMENT'
                pass
            elif (t.strip() == ''):                 # blank line
                blocks.append("")
                breakAfter = True
                blockType = 'BLANK'
            elif (t[0] == '='):                     # heading
                blocks.append(t)
                breakAfter = True
                blockType = 'HEADING'
            elif (re.match(r'-{3,}|={3,}\s*$', t)): # rule
                blocks.append("=" * 79)
                breakAfter = True
                blockType = 'RULE'
            elif (t[0] == '|'):                     # table
                blocks.append(t)
                breakAfter = True
                blockType = 'TABLE'
            elif (t[0] in "*#:0123456789 \t"):      # keep line break
                blocks.append(t)
                blockType = 'LIST, IND'
            else:                                   # continued text
                if (breakAfter):
                    blocks.append(t)
                    breakAfter = False
                    blockType = 'TEXT POST BR'
                else:
                    if (blocks[-1] != ''): blocks[-1] += ' '
                    blocks[-1] += t
                    blockType = 'TEXT CONTINUE'
            #print("+%s: %s" % (blockType, blocks[-1]))
        return blocks

    @staticmethod
    def doSpecialChars(item):
        """Expand tabs, escapes, entities, etc.
        Return the expanded text, but with leading indent separate
        """
        indentString = ""
        mat = re.match(r'^([ \t]+)', item)
        if (mat):
            indentString = mat.group(1).expandtabs(
                BlockFormatter._options['tabStops'])
            item = item[len(mat.group(1)):]
        if (BlockFormatter._options['xescapes']):
            item = xescapes(item)
        if (BlockFormatter._options['uescapes']):
            item = uescapes(item)
        if (BlockFormatter._options['entities']):
            assert False, "entities not yet implemented"
        if (BlockFormatter._options['showInvis']):
            item = makeVis(item)
        return item, indentString

    @staticmethod
    def _alt_fill(item, width, indentString):
        """In case _fill_text changes or goes away....
        """
        lines = []
        for x in re.finditer(
            r'\s*(\S.{,%d}(?=[-/\s]))' % (width-indentString-2),
            item, re.MULTILINE):
            print("Wrap trial: '%s'" % (x.group(1)))
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
            "--altFill",          action='store_true',
            help='Use an alternate method to fill lines.')
        parser.add_argument(
            "--breakLong",        action='store_true',
            help='Allow breaking long tokens (like URLs) at non-spaces.')
        parser.add_argument(
            "--comment",          type=str, metavar='C', default="//",
            help='Treat lines starting with this, as comment lines.')
        parser.add_argument(
            "--entities",         action='store_true',
            help='Recognize HTML/XML special characters.')
        parser.add_argument(
            "--hangIndent",       type=int, default=2,
            help='Apply hanging indents of this many spaces.')
        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--oencoding",        type=str, metavar='E',
            help='Use this character set for output files.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--showInvis",        action='store_true',
            help='Turn control characters etc. to visible forms.')
        parser.add_argument(
            "--split",            action='store_true',
            help='Just split lines.')
        parser.add_argument(
            "--tabStops",         type=int, default=4,
            help='Assume tabstops every n columns.')
        parser.add_argument(
            "--uescapes",         action='store_true',
            help='Recognize \\uFFFF-style special characters.')
        parser.add_argument(
            "--unicode",          action='store_const',  dest='iencoding',
            const='utf8', help='Assume utf-8 for input files.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')
        parser.add_argument(
            "--xescapes",         action='store_true',
            help='Recognize \\xFF-style special characters.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #

    args = processOptions()
    BlockFormatter._options['verbose'] = args.verbose
    if (args.altFill):
        BlockFormatter._options['altFill'] = BlockFormatter._alt_fill

    print("*** Testing BlockFormatter.py (level 1) ***\n")

    if (len(args.files) == 0):
        tfile = "/tmp/BlockFormatter.md"
        vMsg(0, "No files specified, copying own help text to %s" % (tfile))
        fh = codecs.open(tfile, "wb", encoding=args.iencoding)
        fh.write(descr)
        fh.close()
        args.files.append(tfile)

    for path0 in args.files:
        vMsg(0, "\n******* Starting test file '%s'" % (path0))
        fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
        testText = fh0.read()
        if (args.split):
            print("*** Just splitting")
            lenSoFar = 0
            for i, t in enumerate(
                re.split(r'\n', testText, flags=re.MULTILINE | re.UNICODE)):

                print("%04d (%6d)==>%s<==\n" % (i, lenSoFar, t))
                lenSoFar += len(t)
            sys.exit()

        hf = BlockFormatter(None)
        print(hf._format_text(testText))

    vMsg(0, "*** DONE ***")
    sys.exit()
