#!/usr/bin/env python3
#
# BlockFormatter.
# Upgrade for Python argparse, that don't forcibly wrap all text.
#
#pylint: disable=W0212
#
import sys, os, re, codecs
import argparse
from collections import namedtuple
from html.entities import nametocodepoint

import ColorManager

try:
    import mathAlphanumerics
    gotMath = True
except ImportError:
    gotMath = False

__metadata__ = {
    'title'        : "BlockFormatter",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2013-04-18",
    'modified'     : "2020-08-13",
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

This simple class is like the default argparse formatter except for a few
things:

* it does ''not'' wrap across blank lines. That is, blank lines stay there.
* it retains newlines before lines starting with punctuation commonly used
for format codes, such as [=*#].
* it can optionally map inline style markers such as in Markdown-ish
markup languages, to visible display changes such as:
** ANSI terminal colors and effects
** Inserted surrounding characters such as quotation marks
** Translation to special Unicode variants such as MATHEMATICAL BOLD, ITALIC,
SANS-SERIF, etc. (see also `mathAlphanumerics.py`).

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
(they will actually be empty on output, however).

Lines starting with punctuation common used for formatting codes, such
as equals, pound, and asterisk, retain the preceding newline.

Lines that are indented get a newline and indentation before them,
but no blank line (unless there was one there in the input too). Tabs will be
expanded in the indentation, assuming tabstops every 4 spaces.

Unindented lines following an indented lines, will be wrapped with it, but all
the resulting visual lines will be indented to match.

==Options==

There is a class variable in BlockFormatter, `_options`, which is a dict that
defaults to:

    _options = {
        'verbose':     0,
        'inlines':     True,
        'showInvis':   False,
        'tabStops':    4,
        'hangIndent':  2,
        'xescapes':    False,
        'uescapes':    False,
        'entities':    False,
        'breakLong':   False,
        'altFill':     None,
        'quotes':      '""',
    }

There is not yet an API to change or set these, but you can set them
from code like:
    BlockFormatter._options.set(tabStops, 8)

or by lines at the start of a source file like:

    #set inline = 1

They can also be set by a config file as described below (in progress),
like:
    set inline = 1

'verbose' can be increased to generate debugging messages.

'inlines' can be set to map MarkDown-ish inline markup to cause
special formatting effects. The particular style effect for each case (and
for additional regex-specific cases) can be defined in a config file.

'showInvis' causes all C0 control characters (except the newlines
used to line-break the
output) to appear instead as their Unicode "control pictures", near U+2400.

'tabStops' is the interval to assume for expanding tabs.

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


=Config files and customization=

On startup, this script will look for a single configuration file, along the
path specified in environment variable `BLOCKFORMATTERPATH`, and then
in your home directory.

The format of the config file is:

* Lines beginning with '#' are treated as comments.

* Lines beginning with an option name (see above) following by a colon, and
a value of the correct type, set the named option to that value.
The `altFill` option cannot be set this way, however, since it has to be
set to an actual Python function.

* Lines beginning with 'INLINE:' define inline markup and styles. The colon
must be followed by two quoted strings, which contain the literal characters
that mark the start and end of a marked-up inline component. For example,
for the convention of putting asterisks around words to be emphasized, the
two strings would each contain an asterisk.

After the two strings come keywords that determine the effect(s) to be applied
to such content (the delimiters themselves are discarded).

The default inline style definitions are (conventions vary quite
a lot, so I've just chosen ones that seem quite common):

    INLINE: '*'    '*'    "bold"
    INLINE: '_'    '_'    "bold blue"
    INLINE: '`'    '`'    "underline"
    INLINE: "'''"  "'''"  "bold"
    INLINE: "''"   "''"   "italic"
    INLINE: '['    ']'    "underline blue"

''NOTE'': These are checked by regexes, in the order specified. Thus, you need
to specify a match for "'''" before one for "''", or insert some extra
complexity, such as look-behind assertions to ensure that there's andappropriate boundary before the starting delimter (say, space, start of string, opening
punctuation like '(', etc.).

When choosing styles, please consider the needs of people with
visual differences, such as colorblindness or sensitivity to blinking.

Later I expect to add control for very basic block-level layout objects.
These should work similar to INLINE, but without specifying start/end
delimiters, because the block types will be
fixed and determined by MarkDown and similar conventions:

** ULIST n: This determines a style for unordered lists `n` levels deep.
Depth is counted separately for unordered vs. ordered lists -- so a
MarkDown line starting `*#*#*` is a level 3 unordered list, though nested
5 lists deep overall (please don't do this).

** OLIST n:
** HEAD n:
** INDENT:


==Format values==

* First, an ANSI terminal foreground color, background color, and effect,
as one, two, or three slash-separated tokens in that order.
This is the same convention provided by my `colorString.py` package
and described in `colorNames.md`
[http://github/com/sderose/Color/colorString.py]. For example:
    RED
    WHITE/BLUE
    RED/WHITE/BOLD

The color names are:
    "black"   : 0
    "red"     : 1
    "green"   : 2
    "yellow"  : 3
    "blue"    : 4
    "magenta" : 5
    "cyan"    : 6
    "white"   : 7
    "default" : 9

The effect names are:
    "bold"       : 1   aka 'bright'
    "faint"      : 2
    "italic"     : 3   (rare)
    "underline"  : 4   aka 'ul'
    "blink"      : 5
    "fblink"     : 6?  aka 'fastblink' (rare)
    "reverse"    : 7   aka 'inverse'
    "concealed"  : 8   aka 'invisible' or 'hidden'
    "strike"     : 9   aka 'strikethru' or 'strikethrough'
    "plain"      : 0   (can be used to express "no special effect")

Not all terminal programs support all effects, although most do
support all these colors and the BOLD effect. Test your terminal
by running my `colorstring.pm` or `colorstring.py` package with `--list`.

* Second, a "font" as provided by my `mathAlphanumerics.py`. This does not use
actual fonts, but maps the Latin
alphabet and ASCII digits to alternate Unicode ranges with the Unicode
font you may be using (if any). For the config file, spaces in the
names are replaced by underscores (hyphens are also accepted, mainly
because Unicode uses them in some of the standard names):

    BOLD
    BOLD_FRAKTUR (no digits)
    BOLD_ITALIC (no digits)
    BOLD_SCRIPT (no digits)
    CIRCLED
    DOUBLE-STRUCK
    FRAKTUR (no digits)
    FULLWIDTH
    ITALIC (no digits)
    MONOSPACE
    NEGATIVE_CIRCLED (no lowercase or digits)
    NEGATIVE_SQUARED (no lowercase or digits)
    PARENTHESIZED (no digit zero)
    REGIONAL_INDICATOR_SYMBOL (no lowercase or digits)
    SANS-SERIF
    SANS-SERIF_BOLD
    SANS-SERIF_BOLD_ITALIC (no digits)
    SANS-SERIF_ITALIC (no digits)
    SCRIPT (no digits)
    SQUARED (no lowercase or digits)
    SUBSCRIPT (no lowercase or uppercase, only digits)
    SUPERSCRIPT (no lowercase or uppercase, only digits)

Characters not provided by Unicode are left unchanged.

"bold" and "italic" are provided both by Unicode, and by ANSI terminal
effects. Underline and strike-through may be added to `mathAlphanumerics` via
Unicode combining characters, though this is not yet implemented here.
Monospace is a Unicode Mathematical variant, but also the typical choice for
many terminal programs, so probably won't be very distinctive.
The results in such edge cases are not yet defined -- let me know if you
encounter particular problem that should be addressed.

If the `mathAlphanumerics` package is not found, or if your terminal program
does not support the requested colors and effect, they won't happen. In that
case you may want to upgrade to a better terminal program (say, `iTerm2`),
or reconfigure the styles.

* Third, there are a few more special keywords:

** quote
** pre
** link (identifies a cross-reference, though a viewer might not act)

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

My `mathAlphanumerics.py` supports mapping Latin letters to the many Unicode
font-like variations, such as "SANS-SERIF BOLD ITALIC", etc.


=Known bugs and limitations=

# Long tokens such as URIs should be able to break at slashes, etc.

# It seems that the API in `argparse` for formatting
(such as it is), is not considered "public" -- so attempts to subclass it
could break any time. See [https://stackoverflow.com/questions/29484443]. But
it also does not seem to change much. I have no idea why more attention
has not been paid to this; it seems to me a very basic/common tool.

# Option to page the output, or send directly to 'less'


=To do=

* Option to support inline markup like MarkDown, and URIs.
  (maybe also <i> <b> <u> <tt> <br> <hr> too?
    em/string/big/sup/sub/del/ins/parma/tt/var
* Config file
* add a #include operator
** Like in C, or
** Like in C++.
* Support img if iTerm2 `imgcat` is available?

=Rights=

This program is Copyright 2014 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see [here|"https://creativecommons.org"].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[https://github/com/sderose].

Thanks to Anthon van der Neut for help on integrating with `argparse`. Also:
    * [http://stackoverflow.com/questions/3853722]
    * [https://bitbucket.org/ruamel/std.argparse/src]
    * [http://hg.python.org/cpython/file/2.7/Lib/argparse.py]
    * [https://docs.python.org/2/library/textwrap.html]


=History=

2014-2015: Written by Steven J. DeRose, along with `MarkupHelpFormatter`.
They started together in `MarkupHelpFormatter.py`.

2020-03-04: I split this class out to a separate file, and improved it a bit,
for example indenting non-first lines of indented blocks, expanding tabs,
adding the various options.

2020-08-13: Adding support for config file to specify styles. Inlines class
to do various kinds of inline markup. lint. `mathAlphanumerics.py` integration.

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

latestBF = None

def warn(level, msg):
    if (lastBF._options.get('verbose') >= level):
        sys.stderr.write(msg+'\n')

def makeVis(s):
    return re.sub(r'([\x01-\x0F\x11-\x1F])', toPix, s)  # NOT NEWLINE!

def toPix(mat):
    """Make control chars and space visible.
    """
    return chr(0x2400 + ord(mat.group(1)))

def xescapes(s):
    """Replace \\xFF escapes (but doesn't notice if the \\ is itself escaped).
    """
    return re.sub(r'\\x([0-9a-f][0-9a-f])',
        lambda mat: chr(int(mat.group(1), 16)), s, re.I)

def uescapes(s):
    """Replace 4-hex-digits Unicode charactewr escapes (but doesn't
    notice if the \\ is itself escaped).
    """
    return re.sub(r'\\u([0-9a-f][0-9a-f][0-9a-f][0-9a-f])',
        lambda mat: chr(int(mat.group(1), 16)), s, re.I)


##############################################################################
# Maintain the package's options
#
uint = int

class Options:
    optionDefs = {
        # name         type  default
        'verbose':    (uint, 0),      # Extra messages?
        'inlines':    (bool, True),   # Support inline MarkDown?
        'showInvis':  (bool, False),  # Replace invisible chars
        'tabStops':   (uint, 4),      # Expand tabs per this interval
        'hangIndent': (int,  2),      # non-first lines of list items.
        'xescapes':   (bool, False),  # Recognize \xFF codes
        'uescapes':   (bool, False),  # Recognize \uFFFF codes
        'entities':   (bool, False),  # Expand &#65; &#x41; &bull; etc.
        'breakLong':  (bool, False),  # split long tokens (like URLs)
        'altFill':    (callable, None), # Replacement for _fill_text().
    }

    def __init__(self):
        self.options = {}
        for k in Options.optionDefs:
            self.options[k] = Options.optionDefs[k][1]

    def set(self, name, value):
        assert name in self.options
        self.options[name] = value

    def get(self, name):
        assert name in self.options
        return self.options[name]

    def doSetLine(self, txt):
        pass


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
    _options = {}

    def __init__(self):
        super(BlockFormatter, self).__init__(None)
        self._styles = StyleSpec()
        self._options = Options()
        latestBF = self

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
            warn(2, "\n******* BLOCK %d (len %d) *******" % (i, len(blocks[i])))
            item, istring = BlockFormatter.doSpecialChars(blocks[i])

            #print("### width %s, indent '%s', ind %s:\n    |%s|%s|" %
            #    (width, indent, ind, mat.group(1), mat.group(2)))
            # _fill_text return a string with newlines, not a list.

            if (istring!=''): indParam = indent + istring + (' '*hang)
            else: indParam = indent

            if (callable(BlockFormatter._options['altFill'])):
                withNewlines = BlockFormatter._options['altFill'](
                    item, width, indParam)
            else:
                withNewlines = super(BlockFormatter, self)._fill_text(
                    item, width, indParam)
            if (istring and withNewlines.startswith(' '*hang)):
                withNewlines = withNewlines[hang:]  # Un-hang first line

            blocks[i] = withNewlines
        warn(2, "\n******* FORMATTING DONE *******\n")
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
            if (args.verbose): print("+%s: %s" % (blockType, blocks[-1]))
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
        for x in re.finditer(r'\s*(\S.{,%d}(?=[-/\s]))' %
            (width-indentString-2), item, re.MULTILINE):
            print("Wrap trial: '%s'" % (x.group(1)))
            lines.append(indentString + x.group(1))
        return "\n".join(lines)



###############################################################################
#
class Block:
    """Allocate one of these for each visual block, such as a paragraph,
    list item, bq, head, rule, bnf production, etc.
    TODO: Track line number(s) from source file for messages?
    """
    NONE     = 0
    PARA     = 1
    HEAD     = 2
    ITEM     = 3
    CODE     = 4
    TROW     = 5
    TCELL    = 6
    DEFN     = 7
    EBNF     = 10
    RULE     = 11

    def __init__(self,
        blockType,
        rNum = 0,                        # Line number where it started
        nBlanksAbove = 0,                # number of blank lines before?
        leadSpace = 0,                   # line-initial spaces/tabs?
        markup = '',                     # leading punctuation/markup?
        txt=''                           # not space/markup part of line
        ):
        # Properties of the block *as read in*
        self.blockType = blockType       # markup usually tells us
        self.nBlanksAbove = nBlanksAbove # blank lines before?
        self.leadSpace = leadSpace       # line-initial spaces/tabs?
        self.markup = markup             # leading punctuation/markup?
        self.txt = txt                   # rest of line(s)

        # Properties for rendering and output
        self.style = None


##############################################################################
# Style definitions (cf MStyle)
#
# fontFeatures
PLAIN = 0x0
BOLD = 0x01
ITAL = 0x02
DOUB = 0x08
UNDL = 0x04

STRK = 0x10      # strikethrough
TURN = 0x20      # rotated 180
BLNK = 0x40      # blink
NEGA = 0x8000    # inverse?

SANS = 0x0100
MONO = 0x0200
FRAK = 0x0400
SCRP = 0x0800

CIRC = 0x1000
SQUA = 0x2000
PARE = 0x4000

SUP  = 0x010000
SUB  = 0x020000
WIDE = 0x040000  # Fullwidth
READ = 0x080000  # Use control pictures and hx

class StyleSpec:
    """cf utData/enumerations/CSSProperties.py and MStyle.py
    """
    def __init__(self, **kwargs):
        self.border         = [ 0, 0, 0, 0]
        self.color          = None
        self.bgcolor        = None
        self.display        = StyleSpec.displayValues['BLOCK']
        self.fontFamily     = StyleSpec.UFakeFontInfos['PLAIN']
        self.fontStyle      = StyleSpec.fontStyleValues['normal']
        self.fontWeight     = StyleSpec.fontWeightValues['medium']
        self.margin         = [ 0, 0, 0, 0]
        self.textAlign      = StyleSpec.textAlignmentValues['LEFT']
        self.textDecoration = False
        # "text-overflow":
        # vertical-align
        self.whitespace     = 'wrap'
        self.width          = 79
        for k, v in kwargs.items():
            pass

    styleProps = {
        'border':         ( ),  #[ 0, 0, 0, 0]
        'color':          ( ),  #None
        'bgcolor':        ( ),  #None
        'display':        ( ),  #StyleSpec.displayValues['BLOCK']
        'fontFamily':     ( ),  #StyleSpec.unicodeFakeFontInfos['PLAIN']
        'fontStyle':      ( ),  #StyleSpec.fontStyleValues['normal']
        'fontWeight':     ( ),  #StyleSpec.fontWeightValues['medium']
        'margin':         ( ),  #[ 0, 0, 0, 0]
        'textAlign':      ( ),  #StyleSpec.textAlignmentValues['LEFT']
        'textDecoration': ( ),  #False
   }

    globalValues = {
        "inherit"   : -1,
        "initial"   : -2,
        "unset"     : -3,
    }

    valueDataTypes = {
        "bool"      : 2,
        "string"    : 3,
        "integer"   : 4,
        "float"     : 5,
        "percentage"    : 6,
        "ratio"     : 7,

        "length"    : 11,
        "angle"     : 12,
        "color"     : 13,

        "attrName"  : 100,
        "XPath"     : 101,
        "XPtr"      : 102,
        "url"       : 103
    }

    # Enumerated keywords for various props
    #
    colorValues = {
        "black"     : 0,
        "red"       : 1,
        "green"     : 2,
        "yellow"    : 3,
        "blue"      : 4,
        "magenta"   : 5,
        "cyan"      : 6,
        "white"     : 7,
        "default"   : 9,
    }

    displayValues = {
        'NONE'         : 0,   #
        'INLINE'       : 11,  #
        'BLOCK'        : 22,  #
        'TABLE_CELL'   : 36,  #
    }

    fontFamilyValues = {
        'PLAIN'        : 0,
        'SANS-SERIF'   : 1,
        'FRAKTUR'      : 2,
        'SCRIPT'       : 3,
        'MONOSPACE'    : 4,
    }

    fontStyleValues = {
        'normal'       : 0,
        'italic'       : 1,
    }

    fontWeightValues = {
        'medium'       : 0,
        'demibold'     : 1,
        'bold'         : 2,
    }

    listStyleTypeValues = {
    }
    """class ListStyleTypeValues(Enum):
    INITIAL             = 1
    INHERIT             = 2
    NONE                = 3

    # BULLETS
    DISC                =  10  # Default value. a filled circle
    CIRCLE              =  11  # a circle
    SQUARE              =  12  # a square

    # NUMBERS
    ARMENIAN            = 100  # traditional Armenian numbering
    CJKIDEOGRAPHIC      = 101  # plain ideographic numbers
    DECIMAL             = 102  # a number
    DECIMALLEADINGZERO  = 103  # a number with leading zeros (01, 02, 03, etc.)
    GEORGIAN            = 104  # traditional Georgian numbering
    HEBREW              = 105  # traditional Hebrew numbering
    HIRAGANA            = 106  # traditional Hiragana numbering
    HIRAGANAIROHA       = 107  # traditional Hiragana iroha numbering
    KATAKANA            = 108  # traditional Katakana numbering
    KATAKANAIROHA       = 109  # traditional Katakana iroha numbering
    LOWERALPHA          = 110  # lower case alpha (a, b, c, d, e, etc.)
    LOWERGREEK          = 111  # lower case greek
    LOWERLATIN          = 112  # lower case latin (a, b, c, d, e, etc.)
    LOWERROMAN          = 113  # lower case roman (i, ii, iii, iv, v, etc.)
    UPPERALPHA          = 114  # upper case alpha (A, B, C, D, E, etc.)
    UPPERGREEK          = 115  # upper case greek
    UPPERLATIN          = 116  # upper case latin (A, B, C, D, E, etc.)
    UPPERROMAN          = 117  # upper case roman (I, II, III, IV, V, etc.)

    # Non-CSS???
    DINGBAT             = -101
    TITLE               = -100
    HEX                 = -16
    OCTAL               =  -8
    """


    textAlignmentValues = {
        "left"          : 1,
        "center"        : 2,
        "right"         : 3,
        "decimal"       : 4,
        "justify_all"   : 1,
        "start"         : 1,
        "end"           : 1,
        "match-parent"  : 1,
        # "." center
    }

    textDecorationValues = {
        'none'          : 0,
        'underline'     : 1,
        'strike'        : 2,
    }

    verticalAlignValues = {
        "baseline"      : 1,
        "sub"           : 1,
        "super"         : 1,
        "text-top"      : 1,
        "text-bottom"   : 1,
        "middle"        : 1,
        "top"           : 1,
        "bottom"        : 1,
        # <length>
        # <percentage> values
    }

    whitespaceValues = {
        "normal"        : 1,
        "nowrap"        : 1,
        "pre"           : 1,
        "pre-wrap"      : 1,
        "pre-line"      : 1,
        "break-spaces"  : 1,
    }

    # TODO: Issue that there are clear features here, but nowhere near all
    # feature combinations can occur.
    #
    UNONE = 0x0000

    UBOLD = 0x0001
    UITAL = 0x0002
    USANS = 0x0004
    UMONO = 0x0008

    UFRAK = 0x0010
    USCRP = 0x0020
    UDOUB = 0x0040

    USUB  = 0x0100
    USUP  = 0x0200
    UWIDE = 0x0400

    UCIRC = 0x1000
    USQUA = 0x2000
    UPARE = 0x4000
    UNEGA = 0x8000

    UFakeFontInfos = {
        'PLAIN'                   : (UNONE           , 'ULD'),
        'BOLD'                    : (UBOLD           , 'ULD'),
        'ITALIC'                  : (UITAL           , 'UL-'),
        'BOLD_ITALIC'             : (UBOLD | UITAL   , 'UL-'),

        'SANS_SERIF'              : (USANS           , 'ULD'),
        'SANS_SERIF_BOLD'         : (USANS | UBOLD   , 'ULD'),
        'SANS_SERIF_ITALIC'       : (USANS | UITAL   , 'UL-'),
        'SANS_SERIF_BOLD_ITALIC'  : (USANS | UBOLD | UITAL , 'UL-'),

        'FRAKTUR'                 : (UFRAK           , 'UL-'),
        'BOLD_FRAKTUR'            : (UFRAK | UBOLD   , 'UL-'),

        'SCRIPT'                  : (USCRP           , 'UL-'),
        'BOLD_SCRIPT'             : (USCRP | UBOLD   , 'UL-'),

        'MONOSPACE'               : (UMONO           , 'ULD'),

        'DOUBLE_STRUCK'           : (UDOUB           , 'ULD'),
        'FULLWIDTH'               : (UWIDE           , 'ULD'),

        'CIRCLED'                 : (UCIRC           , 'ULD'),
        'NEGATIVE_CIRCLED'        : (UCIRC | UNEGA   , 'U--'),
        'SQUARED'                 : (USQUA           , 'U--'),
        'NEGATIVE_SQUARED'        : (USQUA | UNEGA   , 'U--'),
        'PARENTHESIZED'           : (UPARE           , 'ULD'),  # (no 0)

        'SUBSCRIPT'               : (USUB            , '--D'),
        'SUPERSCRIPT'             : (USUP            , '--D'),

        #'REGIONAL_INDICATOR_SYMBOL': (1  , 'U--'),
    }

    # TODO: Find a sensible way to treat the list of what a Unicode
    # ANSI-color terminal can do, and how it maps to CSS and OHCO.
    #
    effectValues = {
        "bold"       : 1,   # aka 'bright'
        "faint"      : 2,   #
        "italic"     : 3,   # (rare)
        "underline"  : 4,   # aka 'ul'
        "blink"      : 5,   #
        "fblink"     : 6,   # aka 'fastblink' (rare)
        "reverse"    : 7,   # aka 'inverse'
        "concealed"  : 8,   # aka 'invisible' or 'hidden'
        "strike"     : 9,   # aka 'strikethru' or 'strikethrough'
        "plain"      : 0,   # (can be used to express "no special effect")
    }

    def doStyleDefLine(self, txt):
        tokens = re.split(r'\s+', txt)
        if (tokens[0] not in StyleSpec.displayValues):
            raise ValueError("Unrecognized style keyword '%s'." % (tokens[0]))


###############################################################################
# Bundles of style properties.
#
class LineType:  # TODO: Later
    def __init__(self):
        self.color  = TextStyle.Color('BLUE')
        self.weight = 1
        self.dash   = [ 1, 1 ]

class BorderType:  # Takes LineTypes   # TODO: Later
    def __init__(self):
        self.uBoxDraw = (bool,  False)
        self.bottom   = ( LineType, None )
        self.left     = ( LineType, None )
        self.right    = ( LineType, None )
        self.miter    = ( object,   None )

class ListType:
    def __init__(self):
        self.level        = None    # From 1
        self.styleType    = None    # Bullet, Number, Head
        self.markerValue  = 1
        self.markerText   = None    # code point or 'disc' etc.
        self.markerPath   = None    # For run-in titles, deflist terms, etc.
        self.markerPos    = None    #

class Transclusion:
    def __init__(self):
        self.literal      = (str, None)
        self.xpath        = (str, None)
        self.url          = (str, None)


###############################################################################
# Full-up style defs.
#
class TextStyle:
    """Wayyyyy oversimplified stylesheet mechanism.
    """
    Color = str  # Switch to enum later
    Effect = str
    MFont = str

    textProps = {
        # fonts etc.
        'bold'        : (bool,  False),
        'italic'      : (bool,  False),
        'sans'        : (bool,  False),
        'mono'        : (bool,  False),
        'underline'   : (bool,  False),
        'strike'      : (bool,  False),
        'super'       : (bool,  False),
        'sub'         : (bool,  False),
        'ufont'       : (MFont,  None),

        # color etc.
        'color'       : (Color, None),
        'bgcolor'     : (Color, None),
        'effect'      : (Effect,None),

        # hypertext
        'before'      : (Transclusion, None),
        'after'       : (Transclusion, None),
        'hot'         : (bool, False)
    }

    def __init__(self):
        for k, v in StyleSpec.styleProps:
            self.__dict__[k] = v


class BlockStyle(TextStyle):  # TODO: Later
    blockProps = {
        'marginTop'     : None,
        'marginBottom'  : None,
        'marginLeft'    : None,
        'marginRight'   : None,
        'marginFirst'   : None,

        'textAlignment' : None,
        'whitespace'    : None,    # wrap, trunc, hang
        'marker'        : None,
        'markerPos'     : None,
        'border'        : (BorderType, None),
        "border-collapse": None,
        "padding"       : None,

        "hidden"        : None,
        "listType"      : None,
        "borderType"    : None,
        "borderPAd"     : None,
    }

    def __init__(self):
        for k, v in StyleSpec.styleProps:
            self.__dict__[k] = v


###############################################################################
# Since there are no real element/component/construct names in MarkDown etc.,
# we define some. Was going to use the nearest HTML thing for familiarity, but:
""" HTML        POD     MD

    em          I       ''...''
    i           I       ''...''
    u           I       ''...''  # Depr="1"/>

    b           B       '''...'''
    strong      B       '''...'''
    var         B       '''...'''

    q           "..."   "..."

    a           L       [...]

    code        C       `...`
    input       C       `...`
    kbd         C       `...`
    tt          C       `...`
    dir         F       `...`    # Depr="1"/>

    center     ***
    font
    label
    legend
    optgroup
    option
    select
    textarea
    abbr
    acronym
    bdo
    big         ***
    cite
    dfn
    img
    s
    samp
    small
    span
    strike      ***
    sub         ***
    sup         ***

==> Unicode other stuff: script, doublestruck, enclosed, sans-serif, fraktur

    # INLINE-BLOCKS
    #
    applet  Content="meta" Depr="1"
    del     Subs="sem"
    iframe
    ins     Subs="sem"
    map     Content="meta"
    object  Subs="link"
    script  Content="meta"
    button  Content="meta"
"""

dv = StyleSpec.displayValues

StylableThings = {
    'P':        { 'display':dv['BLOCK'], },
    'H1':       { 'display':dv['BLOCK'], },
    'H2':       { 'display':dv['BLOCK'], },
    'H3':       { 'display':dv['BLOCK'], },
    'H4':       { 'display':dv['BLOCK'], },
    'H5':       { 'display':dv['BLOCK'], },
    'H6':       { 'display':dv['BLOCK'], },
    'ULI':      { 'display':dv['BLOCK'], },
    'OLI':      { 'display':dv['BLOCK'], },
    'DLI':      { 'display':dv['BLOCK'], },
    'PRE':      { 'display':dv['BLOCK'], },
    'TROW':     { 'display':dv['BLOCK'], },
    'TCELL':    { 'display':dv['BLOCK'], },
    'EBNF':     { 'display':dv['BLOCK'], },
    'HR':       { 'display':dv['BLOCK'], },
    #
    # cf htmlMap, below
    #
    'BOLD':     { 'display':dv['INLINE'], },           # ''md'', POD B, <b>
    'ITAL':     { 'display':dv['INLINE'], },           # '''md''', POD I, <i>
    'MONO':     { 'display':dv['INLINE'], },           # `md`, POD C, <tt>
    'LINK':     { 'display':dv['INLINE'], },           # [md], POD L, <a>
    'STRIKE':   { 'display':dv['INLINE'], },           # [md], POD L, <a>
    'SUB':      { 'display':dv['INLINE'], },           # ''md'', POD B, <b>
    'SUP':      { 'display':dv['INLINE'], },           # ''md'', POD B, <b>

    'VAR':      { 'display':dv['INLINE'], },           # ''md'', POD B, <b>
    'Q':        { 'display':dv['INLINE'], },           # ''md'', POD B, <b>
    'ACRONYM':  { 'display':dv['INLINE'], },           # ''md'', POD B, <b>
    'ABBR':     { 'display':dv['INLINE'], },           # ''md'', POD B, <b>
}


###############################################################################
#
class Inlines:
    """Take a batch of patterns and apply them, changing their content to
    some kind of formatting in accord with some defined style.
    """
    StyleTuple = namedtuple('StyleTuple',
        [ 'displayType', 'delim1', 'delim2', 'effects', 'regex' ])

    # Recognized style keywords. Simplify syntax by making the enum ones
    # all unique. But then what syntax for things like lengths?
    #
    styleKeywordMap = {
        # input name    prop  value
        'bold':         { 'weight':BOLD },
        'italic':       { 'style':ITAL },
        'underline':    { 'textDecoration':UNDL },

        # font 'familyies'
        'fullwidth':    { 'fontFamily':WIDE},
        'doubleStrick': { },
        # Block props
        'rule':         { },
        'quote':        { },
        'center':       { },
        'case':         { },
        'inverted':     { },
        'turned':       { },
        'struck':       { },

        #sup/sub
        #strike (unicode solidus overlay?)
        #(cf [https://yaytext.com/strike]
        #[https://en.wikipedia.org/wiki/Strikethrough#Combining_characters]
    }

    colorKeywords = {
        'red':          (),
        'green':        (),
        'blue':         (),
        'cyan':         (),
        'magenta':      (),
        'yellow':       (),
        'white':        (),
        'black':        (),
    }


    defaultMap = [
        ('INLINE', '*',   '*',   "bold"),
        ('INLINE', '_',   '_',   "bold blue"),
        ('INLINE', '`',   '`',   "underline"),
        ('INLINE', "'''", "'''", "italic"),      # Check before "''" one!
        ('INLINE', "''",  "''",  "italic"),
        ('INLINE', '[',   ']',   "underline blue"),
    ]

    podMap = [
        ('INLINE', 'B<',  '>',   "bold"),
        ('INLINE', 'L<',  '>',   "bold blue"),
        ('INLINE', 'F<',  '>',   "underline"),
        ('INLINE', 'I<',  '>',   "italic"),
        ('INLINE', 'C<',  '>',   "underline blue"),
    ]

    # Maybe support inline HTML a bit?
    # As is, this doesn't allow attributes
    #
    htmlMap = [
        ('INLINE', '<B>',   '</B>',      "bold"),
        ('INLINE', '<I>',   '</I>',      "italic"),
        ('INLINE', '<SUB>', '</SUB>',    "subscript red"),
        ('INLINE', '<SUP>', '</SUP>',    "superscript green"),
        ('INLINE', '<TT>',  '</TT>',     "underline monospace"),
        ('INLINE', '<U>',   '</U>',      "underline"),
        ('INLINE', '<VAR>', '</VAR>',    "monospace blue"),
        # ABBR, ACRONYM, BIG, CITE, CODE, DFN, EM, DEL, INS,
        # KBD, Q, S, SMALL, STRIKE, STRONG
    ]

    qstr = r'(\'[^\']*\'|"[^"]*")'
    configLineExpr = r'\s*(\w+)\s*:\s*%s\s*%s\s*(.*)' % (qstr, qstr)

    def __init__(self):
        self.pathVar = os.environ['PWD']
        self.styleMap = []

        for m in Inlines.defaultMap:
            self.addMap(m[0], m[1], m[2], m[3])

    def addConfigFile(self):
        try:
            cfpath = os.environ['BLOCKFORMATTERPATH']
        except KeyError:
            cfpath = ''
        cfpath = ':' + self.pathVar
        for dirName in cfpath.split(sep=':'):
            warn(1, "Trying for config file in '%s'" % (dirName))
            if (not os.path.isdir(dirName)): continue
            cfile = os.path.join(dirName, 'blockFormatter.cfg')
            if (not os.path.exists(cfile)): continue
            cfh = codecs.open(cfile, 'rb', encoding='utf-8')
            for i, rec in enumerate(cfh.readlines()):
                if (rec.startswith('#')): continue
                mat = re.match(Inlines.configLineExpr, rec)
                if (not mat):
                    warn(0, "Config file line %d: Bad syntax: %s" %
                        (i, rec))
                    continue
                self.addMap(*(mat.groups))
            break  # Just read first config file

    def addMap(self, displayType, delim1, delim2, effects):
        # TODO: Check for duplicates
        regex = re.compile(r'' + delim1 + '(.*?)' + delim2)
        st = Inlines.StyleTuple(displayType, delim1, delim2, effects, regex)
        self.styleMap.append(st)

    def translateInlines(self, s):
        for mapEntry in self.styleMap:
            for mat in re.finditer(mapEntry['regex'], s):
                if (mat.group(s)): pass

    # Uncolorizing (mostly for line-length measurement)
    # See my colorManager.py.
    #
    colorRegex = re.compile(r'\x1b\[\d+(;\d+)*m')

    def uncoloredLen(self, s):
        """Return the length of a string in characters, not counting any ANSI
        terminal color escapes or any trailing whitespace.
        """
        return(len(self.uncolorize(s)))

    def uncolorize(self, s):
        """Remove any ANSI terminal color escapes from a string.
        """
        t = re.sub(self.colorRegex, '', s)
        return(t)


###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        try:
            #from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
               description=descr) #, formatter_class=BlockFormatter)
        except ImportError:
            print("Can't set up argparse with BlockFormatter.")
            sys.exit()

        parser.add_argument(
            "--altFill",          action='store_true',
            help='Use an alternate method to fill lines.')
        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--inlines",          action='store_true',
            help='Do something special for inline Markdown-like markup.')
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
    lastBF = BlockFormatter()

    args = processOptions()
    lastBF._options.set('verbose', args.verbose)
    if (args.altFill):
        lastBF._options.set('altFill', BlockFormatter._alt_fill)

    print("*** Testing BlockFormatter.py ***\n")

    if (len(args.files) == 0):
        warn(0, "No files specified, using own help text...")
        tfile = "/tmp/BlockFormatter.md"
        fh = codecs.open(tfile, "wb", encoding=args.iencoding)
        fh.write(descr)
        fh.close()
        args.files.append(tfile)

    for path0 in args.files:
        warn(0, "\n******* Starting test file '%s'" % (path0))
        fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
        testText = fh0.read()
        hf = BlockFormatter()
        print(hf._format_text(testText))

    warn(0, "*** DONE ***")
    sys.exit()
