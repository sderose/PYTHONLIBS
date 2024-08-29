#!/usr/bin/env python3
#
# BlockFormatter.
# Upgrade for Python argparse, that don't forcibly wrap all text.
#
#pylint: disable=W0212
#
import sys, re, codecs
import argparse
import logging

lg = logging.getLogger("BlockFormatter")

__metadata__ = {
    "title"        : "BlockFormatter",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2013-04-18",
    "modified"     : "2020-03-04",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/",
    "description"  :
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

To use it:
    doc = ""
    First paragraph of documentation,
    which wraps to fill output lines.

    Second paragraph.
    ...
    ""
    parser = argparse.ArgumentParser(description=doc,
        formatter_class=BlockFormatter)

==Behavior==

Blank lines remain. This includes lines that contain only space and TAB, though
(they will be actually empty on output, however).

Lines that are indented get a newline and indentation before them,
but no blank line (unless there was one there in the input too). Tabs will be
expanded in the indentation, assuming tabstops every 4 spaces.

Unindented lines following an indented lines, will be wrapped with it, but all
the resulting visual lines will be indented to match.

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
    }

There is not yet an API to change or set these, but you can set them
directly like:
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

=Related commands and libraries=

See also my formatter for MarkDown, MediaWiki, and POD (same API as this):
`MarkupHelpFormatter`.

A different Python Markdown formatter: [https://pypi.org/project/markdown-formatter/]

My `argparsePP.py`:
* Hooks up MarkupHelpFormatter
* Adds a showDefaults option
* Adds a shortMetavars option
* Supports alternative hyphen conventions
* Supports adding 'toggle' attributes, with 'no-' prefix (changeable)

=Known bugs and limitations=

* Long tokens such as URIs should be able to break at slashes, etc.

* It seems that the API in `argparse` for formatting
(such as it is), is not considered "public" -- so attempts to subclass it
could break any time. See [https://stackoverflow.com/questions/29484443]. But
it also does not seem to change much. I have no idea why more attention
has not been paid to this; it seems to me a very basic/common tool.

* Option to page the output, or send directly to 'less'

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

=Options=
"""

##############################################################################
#
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

    "lt": '<', "gt": '>', "apos": "'", "quo": '"', "amp": '&',
}

def makeVis(s):
    return re.sub(r'([\x01-\x0F\x11-\x1F])', toPix, s)  # NOT NEWLINE!

def toPix(mat):
    """Make control chars and space visible.
    """
    return chr(0x2400 + ord(mat.group(1)))

def xescapes(s):
    """Replace \\x escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r'\\x([0-9a-f][0-9a-f])',
        lambda mat: chr(int(mat.group(1), 16)), s, re.I)

def uescapes(s):
    """Replace \\u escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r'\\u([0-9a-f][0-9a-f][0-9a-f][0-9a-f])',
        lambda mat: chr(int(mat.group(1), 16)), s, re.I)


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
        "verbose":     0,         # Extra messages?
        "showInvis":   False,     # Replace invisible chars
        "tabStops":    4,         # Expand tabs per this interval
        "hangIndent":  2,         # Add to non-first lines of list items etc.
        "xescapes":    False,     # Recognize \xFF codes
        "uescapes":    False,     # Recognize \uFFFF codes
        "entities":    False,     # Recognize &#65; &#x41; &bull; etc.
        "breakLong":   False,     # Can split inside long tokens (like URLs)
        "altFill":     None,      # Replacement for _fill_text().
    }

    def _fill_text(self, text, width, indent):
        """Override the aggressive line-filler, to do these things:
            * Retain blank lines
            * Keep newline before line-initial [*#] (probably list items)
            * For indented blocks, apply their indented to following unindented
              lines in the same block.
        NOTE: 'indent' expects a string, not a number of columns.
        """
        hang = BlockFormatter._options['hangIndent']

         # Divide at blank lines
        blocks = re.split(r'\n[ \t]*\n', text, re.MULTILINE | re.UNICODE)
        blocks[0] = blocks[0].lstrip("\n")
        for i in range(len(blocks)):
            lg.log(logging.INFO-2, "\n******* BLOCK %d (len %d) *******" % (i, len(blocks[i])))
            block = blocks[i]
            items = [ ]
            # Divide block at newlines followed by punct or indentation
            for item in re.split(r'\n(?=[ \t*=#â¢])', block,  re.UNICODE):
                lg.log(logging.INFO-2, "ITEM: %s" % (item))
                srcIndent = ""
                mat = re.match(r'^([ \t]+)', item)
                if (mat):
                    srcIndent = mat.group(1).expandtabs(
                        BlockFormatter._options['tabStops'])
                    item = item[len(mat.group(1)):]

                if (BlockFormatter._options['xescapes']):
                    item = xescapes(item)
                if (BlockFormatter._options['uescapes']):
                    item = uescapes(item)
                if (BlockFormatter._options['entities']):
                    assert False, "entities not yet implemented"

                #print("### width %s, indent '%s', ind %s:\n    |%s|%s|" %
                #    (width, indent, ind, mat.group(1), mat.group(2)))
                # _fill_text return a string with newlines, not a list.

                if (srcIndent): indParam = indent + srcIndent + (' '*hang)
                else: indParam = indent

                if (callable(BlockFormatter._options['altFill'])):
                    withNewlines = self._options['altFill'](
                        item, width, indParam)
                else:
                    withNewlines = super(BlockFormatter, self)._fill_text(
                        item, width, indParam)
                if (srcIndent and withNewlines.startswith(' '*hang)):
                    withNewlines = withNewlines[hang:]  # Un-hang first line

                if (BlockFormatter._options['showInvis']):
                    withNewlines = makeVis(withNewlines)

                items.append(withNewlines)
            blocks[i] = "\n".join(items)
        lg.log(logging.INFO-2, "\n******* FORMATTING DONE *******\n")
        return "\n\n".join(blocks)

    @staticmethod
    def _alt_fill(item, width, indentString):
        """In case _fill_text changes or goes away....
        """
        lines = []
        for x in re.finditer(r'\s*(\S.{,%d}(?=[-/\s]))' % (width-indentString-2),
            item, re.MULTILINE):
            print("Wrap trial: '%s'" % (x.group(1)))
            lines.append(indentString + x.group(1))
        return "\n".join(lines)


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)

        parser.add_argument(
            "--altFill",        action='store_true',
            help='Use an alternate method to fill lines.')
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
            "--unicode",          action='store_const',  dest='iencoding',
            const='utf8', help='Assume utf-8 for input files.')
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
        return(args0)

    ###########################################################################
    #

    args = processOptions()
    BlockFormatter._options['verbose'] = args.verbose
    if (args.altFill):
        BlockFormatter._options['altFill'] = BlockFormatter._alt_fill

    print("*** Testing BlockFormatter.py ***\n")

    if (len(args.files) == 0):
        lg.log(logging.INFO-0, "No files specified, using own help text...")
        tfile = "/tmp/BlockFormatter.md"
        fh = codecs.open(tfile, "wb", encoding=args.iencoding)
        fh.write(descr)
        fh.close()
        args.files.append(tfile)

    for path0 in args.files:
        lg.log(logging.INFO-0, "\n******* Starting test file '%s'" % (path0))
        fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
        testText = fh0.read()
        hf = BlockFormatter(None)
        print(hf._format_text(testText))

    lg.log(logging.INFO-0, "*** DONE ***")
    sys.exit()
