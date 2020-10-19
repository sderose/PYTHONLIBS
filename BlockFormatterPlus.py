#!/usr/bin/env python
#
# BlockFormatterPlus: Like BlockFormatter, but also hooks in handling
# of inline markup, and use of color and Unicode pseudo-fonts.
# Upgrade for Python argparse, that don't forcibly wrap all text.
#
#pylint: disable=W0212
#
import sys, re, codecs
import argparse
from enum import Enum, Flag
from collections import namedtuple

import ColorManager
try:
    from mathAlphanumerics import mathAlphanumerics
except ImportError as e:
    print(e)
    print("Looked in:\n    %s" % ("\n    ".join(sys.path)))

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY3:
    def unichr(n): return chr(n)

__metadata__ = {
    'title'        : "BlockFormatterPlus.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-08-27 (forked from BlockFormatter.py)",
    'modified'     : "2020-08-27",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/",
    'description'  :
        'Simple formatter class for Python argparse (level 2).',
}
__version__ = __metadata__['modified']

descr = """
=Description=

This
package
defines
a text formatter
 that can be used with Python's
`argparse` package in order to get better formatting in terminal software.

It is a pluggable upgrade to `BlockFormatter.py`,
and so keeps the same class name. To use it:

    from BlockFormatterPlus import BlockFormatterPlus
    descr = "..."
    parser = argparse.ArgumentParser(description=descr,
        formatter_class=BlockFormatterPlus)

Pr, to use it as an independent formatter:

    from BlockFormatter import BlockFormatter
    doc = "..."
    hf = BlockFormatter(None)
    print(hf._format_text(doc))


This is "Level 2" of a series of formatters. Level 1 just upgrades argparse
to retain apparently-meaningful lines breaks rather than wrapping everything
no matter what. For example, blank lines stay, and lines that begin with
common "block" signals like "*", "=", and indentation also keep the
preceding line-break. Other lines wrap.

This add the ability to format inline markup by mapping it to ANSI terminals
colors (using my `ColorManager.py`), and to Unicode alternate Latin alphabets
such as MATHEMATICAL ITALIC and others (using my `mathAlphanumerics`).
The codes are similar to those
used in MediaWiki and git-style MarkDown (which are ery different from
"true" Markdown, btw). They include:

    `text`          Monospace plus color
    ''text''        Italic
    '''text'''      Bold
    _text_          Bold
    *text*          Italic
    [text]          Links.

BlockFormatterPlus (like most terminal programs)
only handles monospace fonts. Because of that, markup
like `text` of `<tt>` also causes an additional e, such as color.

I may add HTML "inline" elements, too, at least as an option.

Links are colorized, but whether they're active depends on the software
involved in display. For example, if you're using `iTerm2`, you can set it
to open URLs on demand; but the shell doesn't know anything about that.

Markdown-ish formats come in very wide variations,
such as MarkDown per se, CommonMark, MarkDownExtra, github MarkDown, WikiPedia markup, and many more. I expect to add several pre-defined sets and a way
to select among them.

The next version (`BlockFormatterPlusPlus`, or "level 3") is expected
to add much more flexible control of how input
is parsed, as well as a style system for choosing what formatting effects
to apply when various objects or formatting commands are detected.

All of these formatters are intended to raise the bar for layout in
typical ANSI terminal environments, not to take the place of word processors,
page layout tools, or Web browsers. Think of them as `man++` rather than
`HTML--`. Thus, I do not expect to add proportional font support, anything
involving images (well, maybe hooks to `iTerm2 imgcat`...), etc.

I do anticipate adding a feature that simply converts the input to normal
(and hopefully clean) HTML, and passes it off to a browser. But I think
many people might like to have an in-terminal formatter that is designed
for the terminal environment, but can look a lot better than `man` or `info`
pages. Just like many users are happy writing *nix pipes rather than
learning ex[tp]ensive GUIs to do basic file-manipulation.


==Options==

There is a class variable `_options`, which is a dict that
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
        'comment':     '#',
        'quotes':      'STRAIGHT',
    }

There is not yet an API to change or set these, but you can set them
directly like:
    BlockFormatterPlus._options['tabStops'] = 8

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
One such is provided: `_alt_fill`.

'comment' is a string that identifies comment lines (no space before).

'quotes' determines what kind of quotation marks to use, from this list.
They may be passed as string literals, or as values of the Enum `QuoteType`.
* NONE      = 0
* S_PLAIN   = 1
* D_PLAIN   = 2
* S_CURLY   = 3
* D_CURLY   = 4
* S_ANGLE   = 5
* D_ANGLE   = 6
* T_ANGLE   = 7
* BACKP     = 8
* LOW9      = 9


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

* Markdown in practice is extraordinarily inconsistent. If you pick the
wrong variant (once I get variants working), or use an unsupported variant,
some of your markup won't work.


=History=

2014-2015: Written by Steven J. DeRose, along with `MarkupHelpFormatter`.
They were together in `MarkupHelpFormatter.py`.

2020-03-04: I split this class out to a separate file, and improved it a bit,
for example indenting non-first lines of indented blocks, expanding tabs,
adding the various options.

2020-08-22: Improve handling of MarkDown-like lines. Simplify wrapping.
Refactor entity/escape/tab handling.


=To Do=

*Finish inline support.
*Option for `[!url|anchorText]` for transclusion?
*Option to skip to regex, element, or section xptr?
*Markdown convention for anchor/id?
*Option to add blank line above list items
*Add option for TEX special chars (and allow as XML entities, too? :)

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


=Options=
"""

##############################################################################
#
class UnimplementedError(Exception):
    pass

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
    if (BlockFormatterPlus._options['verbose']>=level):
        sys.stderr.write("\n*******" + msg+'\n')

def vMsg(level, msg):
    if (BlockFormatterPlus._options['verbose']>=level):
        sys.stderr.write(msg+'\n')

def makeVis(s):
    """Turn control characters into Unicode Control Pictures.
    TODO: Make wrapping treat these as breakable?
    """
    return re.sub(r'([\x01-\x0F\x11-\x1F])', toPix, s)  # NOT NEWLINE!

def toPix(mat):
    """Make control chars and space visible.
    """
    cp = ord(mat.group(1))
    if (cp > ord(' ')): return mat.group(1)
    return unichr(0x2400 + cp)

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
class BlockFormatterPlus(argparse.HelpFormatter):
    """A formatter for argparse. This differs from the default formatter, in
    that it does *not* wrap lines across blank or indented lines.

    Sequence seems to be:
        _format_text(self, txt)
            _format(self, txt, encoding="utf8", color=1, width=0)
                wrap(para, width)
                    _fill_text(self, text, width, indent)
    """
    cm = None  # A ColorManager instance, created by _fill_text()

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
            * Measure and break properly even once color escaped are inserted.
        NOTE: 'indent' expects a string, not a number of columns.
        """

        vMsg(0, "_fill_text called for %d chars." % (len(text)))
        if (not BlockFormatterPlus.cm):
            BlockFormatterPlus.cm = ColorManager.ColorManager()

        hang = BlockFormatterPlus._options['hangIndent']

        # Divide at blank lines line breaks to keep
        blocks = BlockFormatterPlus.makeBlocks(text)
        for i in range(len(blocks)):
            vMsg(2, "\n******* BLOCK %d (len %d) *******" % (i, len(blocks[i])))
            item, istring = BlockFormatterPlus.doSpecialChars(blocks[i])

            #print("### width %s, indent '%s', ind %s:\n    |%s|%s|" %
            #    (width, indent, ind, mat.group(1), mat.group(2)))
            # _fill_text return a string with newlines, not a list.

            if (istring!=''): indParam = indent + istring + (' '*hang)
            else: indParam = indent

            if (callable(self._options['altFill'])):
                print(1)
                withNewlines = BlockFormatterPlus._options['altFill'](
                    item, width, indParam)
            elif (callable(self._fill_despite_color)):
                print(2)
                withNewLines = self._fill_despite_color(
                    item, width, indParam)
            else:
                print(3)
                withNewlines = super(BlockFormatterPlus, self)._fill_text(
                    item, width, indParam)
            if (istring and withNewlines.startswith(' '*hang)):
                withNewlines = withNewlines[hang:]  # Un-hang first line

            blocks[i] = withNewlines
        vMsg(2, "\n******* FORMATTING DONE *******\n")
        blocks.append(self.getSignature())
        return "\n".join(blocks)

    @staticmethod
    def getSignature():
        lDelim, rDelim = ("\u270D", "")      # WRITING HAND
        lDelim, rDelim = ("\u27E6", "27E7")  # M WHITE SQUARE BRACKETS
        lDelim, rDelim = ("\u27EA", "27EB")  # M WHITE DOUBLE ANGLE BRACKETS

        sig = "-- Formatting by BlockFormatterPlus.py --"
        return sig

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
            if (BlockFormatterPlus._options['comment']!='' and
                t.startswith(BlockFormatterPlus._options['comment'])):
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
                BlockFormatterPlus._options['tabStops'])
            item = item[len(mat.group(1)):]
        if (BlockFormatterPlus._options['xescapes']):
            item = xescapes(item)
        if (BlockFormatterPlus._options['uescapes']):
            item = uescapes(item)
        if (BlockFormatterPlus._options['entities']):
            assert False, "entities not yet implemented"
        if (BlockFormatterPlus._options['showInvis']):
            item = makeVis(item)
        return item, indentString

    @staticmethod
    def _alt_fill(item, width, indentString):
        """Wrap the text in 'item' to the given width, with all lines
        indented (prefixed) by 'indentString'.
        Be careful to count correctly around ANSI escapes, and potentially
        fullwidth characters (although we don't expect them, really).

        This should not even be called for pre/code/verbatim-like blocks.
        Though we should have a way to truncate, hang-wrap, etc. for them.

        _fill_text won't suffice at this level, because color escape....
        """
        vMsg(0, "\n******* In _alt_fill")
        lines = []
        for x in re.finditer(
            r'\s*(\S.{,%d}(?=[-/\s]))' % (width-len(indentString)-2),
            item, re.MULTILINE):
            print("Wrap trial: '%s'" % (x.group(1)))
            lines.append(indentString + x.group(1))
        return "\n".join(lines)

    def _fill_despite_color(self, item, width, indentString):
        """Wrap the text in 'item' to the given width, with all lines
        indented (prefixed) by 'indentString'.
        Be careful to count correctly around ANSI escapes, and potentially
        fullwidth characters (although we don't expect them, really).

        This should not even be called for pre/code/verbatim-like blocks.
        Though we should have a way to truncate, hang-wrap, etc. for them.
        """
        # First remove color and break normally
        # OR: make fn to move the color escapes aside, then back.
        ncItem = self.cm.uncolorize(item)
        withBreaks = self._alt_fill(item, width, indentString)
        if (ncItem == item): return withBreaks

        # If needed, use the lengths of those lines to re-extract the
        # corresponding parts from the original (colorized) version.
        lines = withBreaks.split("\n")
        startPos = 0
        for i, lin in enumerate(lines):
            endPos += len(lin)
            # TODO: Finish
        lines = []
        raise UnimplementedError("Finish _fill_despite_color().")
        return "\n".join(lines)

    ColorTag = namedtuple('ColorTag', ['startTextPos', 'escapeSequence'])

    def extractColor(self, item):
        """Remove all the ANSI color escapes, *but* save the offset into
        the resulting (escapeless) string where each of them belongs.
        """
        leaves = re.split(colorRegex, item)
        txt = ""
        colorTags = []
        for leaf in leaves:
            if (leaf.startswith(chr(27))):
                colorTags.append( (len(txt), leaf) )
            else:
                txt += leaf
        return txt, colorTags


###############################################################################
#
class FancyText:
    """Do fancier typography.
    Roman numerals? Emoticons? TEX? Math ops?
    Please don't call this on code blocks....
    """
    qPairs = {  # QUOTATION MARKs (see Charsets/Unicode/asPython/quotes.py)
        # menmonic: [ left,   right],
        'splain':   [ ord("'"), ord("'") ], # Apostrophe / single quotation mark
        'dplain':   [ ord('"'), ord('"') ], # Double quotation mark
        'single':   [ 0x2018, 0x2019 ],  # "LEFT SINGLE QM"
        'double':   [ 0x201C, 0x201D ],  # "LEFT DOUBLE QM"
        'sangle':   [ 0x2039, 0x203A ],  # "SINGLE LEFT-POINTING ANGLE QM"
        'dangle':   [ 0x00AB, 0x00BB ],  # "LEFT-POINTING DOUBLE ANGLE QM *"
        'slow9':    [ 0x201A, 0x201B ],  # "SINGLE LOW-9 QM"
        'dlow9':    [ 0x201E, 0x201F ],  # "DOUBLE LOW-9 QM"
        'sprime':   [ 0x2032, 0x2035 ],  # "PRIME"
        'dprime':   [ 0x301E, 0x301E ],  # "DOUBLE PRIME QM"
        'tprime':   [ 0x2034, 0x2037 ],  # "TRIPLE PRIME"

        'subst':    [ 0x2E02, 0x2E03 ],  # "LEFT SUBSTITUTION BRACKET"
        'dotsubst': [ 0x2E04, 0x2E05 ],  # "LEFT DOTTED SUBSTITUTION BRACKET"
        'transp':   [ 0x2E09, 0x2E0A ],  # "LEFT TRANSPOSITION BRACKET"
        'romission':[ 0x2E0C, 0x2E0D ],  # "LEFT RAISED OMISSION BRACKET"
        'lpara':    [ 0x2E1C, 0x2E1D ],  # "LEFT LOW PARAPHRASE BRACKET"
        'vbarq':    [ 0x2E20, 0x2E21 ],  # "LEFT VERTICAL BAR WITH QUILL"
        #'rdprime':  [ 0x301D, 0x301F ],  # "REVERSED DOUBLE PRIME QM"
        'rdprime':  [ 0x2057, 0x301D ],  # "REVERSED DOUBLE PRIME QM" "QUADRUPLE PRIME"

        'fullwidth':[ 0xFF02, 0xFF02 ],  # Fullwidth Quotation Mark
        'scommaO':  [ 0x275B, 0x275C ],  # Heavy Single Turned Comma QM Ornament
        'dcommaO':  [ 0x275D, 0x275E ],  # Heavy Double Turned Comma QM Ornament
        'hangleO':  [ 0x276E, 0x276F ],  # Heavy Left-pointing Angle QM Ornament
        'sshdcommonO':[ 0x1F677, 0x1F678 ], # Sans-serif Heavy Double Comma QM Ornament
    }

    ligatureMap = {
        "ffi":  "\ufb03",
        "ffl":  "\ufb04",
        "fi":   "\ufb01",
        "fl":   "\ufb02 ",
    }

    fractionMap = {
        "1/4":  chr(0x000bc),  # VULGAR FRACTION ONE QUARTER
        "1/2":  chr(0x000bd),  # VULGAR FRACTION ONE HALF
        "3/4":  chr(0x000be),  # VULGAR FRACTION THREE QUARTERS
        "1/7":  chr(0x02150),  # VULGAR FRACTION ONE SEVENTH
        "1/9":  chr(0x02151),  # VULGAR FRACTION ONE NINTH
        "1/10": chr(0x02152),  # VULGAR FRACTION ONE TENTH
        "1/3":  chr(0x02153),  # VULGAR FRACTION ONE THIRD
        "2/3":  chr(0x02154),  # VULGAR FRACTION TWO THIRDS
        "1/5":  chr(0x02155),  # VULGAR FRACTION ONE FIFTH
        "2/5":  chr(0x02156),  # VULGAR FRACTION TWO FIFTHS
        "3/5":  chr(0x02157),  # VULGAR FRACTION THREE FIFTHS
        "4/5":  chr(0x02158),  # VULGAR FRACTION FOUR FIFTHS
        "1/6":  chr(0x02159),  # VULGAR FRACTION ONE SIXTH
        "5/5":  chr(0x0215a),  # VULGAR FRACTION FIVE SIXTHS
        "1/8":  chr(0x0215b),  # VULGAR FRACTION ONE EIGHTH
        "3/8":  chr(0x0215c),  # VULGAR FRACTION THREE EIGHTHS
        "5/8":  chr(0x0215d),  # VULGAR FRACTION FIVE EIGHTHS
        "7/8":  chr(0x0215e),  # VULGAR FRACTION SEVEN EIGHTHS
        "0/3":  chr(0x02189),  # VULGAR FRACTION ZERO THIRDS
    }

    texChars = {

    }

    @staticmethod
    def zing(s,
        ellipsis=True, quotes=True, ligatures=False,
        dashes=False, fractions=False,
        spacedEm=True, sentenceSpace=False, texChars=False
        ):
        if (ellipsis):
            s = re.sub(r"\.\.\.", "\u2026", s)

        if (quotes):
            # Treat as opener if there's space or newline or nothing before.
            # Else it's a closer. BUT don't mess with any of this in code!
            #
            s = re.sub(r"(?<\s|^)'", chr(FancyText.qPairs['single'][0]), s)
            s = re.sub(r"'",         chr(FancyText.qPairs['single'][1]), s)
            s = re.sub(r'(?<\s|^)"', chr(FancyText.qPairs['double'][0]), s)
            s = re.sub(r'"',         chr(FancyText.qPairs['double'][1]), s)

        if (ligatures):
            s = re.sub(r'(f?f[il])', FancyText.ligatureFn, s)

        # Dashes
        if (dashes):
            if (spacedEm): s = re.sub(r'--', " \u2014 ", s)
            else: s = re.sub(r'--', "\u2014", s)

        if (fractions):
            s = re.sub(r'\b([1-5]/[234568]|1/7|1/9|1/10|0/3)\b',
                FancyText.fractionFn, s)

        if (sentenceSpace):
            s = re.sub(r'([\.?!]) (?! )', "\\1  ", s)
        else:
            s = re.sub(r'([\.?!])  ', "\\1 ", s)

        if (texChars):
            raise UnimplementedError("Not yet, sorry.")

        return s

    @staticmethod
    def ligatureFn(mat):
        return FancyText.ligatureMap[mat.group(1)]

    @staticmethod
    def fractionFn(mat):
        if (mat.group(1) in FancyText.fractionMap):
            return FancyText.fractionMap[mat.group(1)]
        return mat.group(1)


###############################################################################
#
class InlineMapper:
    """Pick a syntax to recognize, that maps each kind of thing to some
    internal kind of object. Should that internal object be descriptive
    or procedural? Or slightly pre-procedural to allow for dynamic adjustment
    for terminal/medium limitations? HTML seem to have the largest set of
    inline distinctions for low-end languages, so use those? Or go straight
    to CSS? Or...?

    Tables are special: rows are commonly marked up in single lines, but
    the cell markup isn't just changing character appearance.

    For now these are hard-coded. The next level formatter should add a
    more general stylesheet mechanism and syntax.
    """
    # Regexes used in multiple variants
    POP3  = r"'''([^']+)'''"                    # '''text'''
    POP2  = r"''([^']+)''"                      # ''text''
    TICK  = r"`([^`]+)`"                        # `text`
    STAR  = r"\*([^*]+)\*"                      # *text*
    STAR2 = r"\*\*([^*]+)\*\*"                  # *text*
    UNDER = r"_([^_]+)_"                        # _text_
    HYPH  = r"--([^-]+)--"                      # --text--
    BRACK = r"\[([^\]]+)\]"                     # [text]

    # MuMultimarkdown has bunch of unusual ones:
    WEIRD = r"`([^`']+)'"                       # `text'
    WEIRD2= r"``([^`']+)''"                     # ``text'' (q)
    CARET = r"\^)[^^]*)\^"                      # ^text^ (super
    TILDE = r"~([^~]*)~"                        # ~text~ (sub)
    FOOTN = r"\[\^(.*?\)]"                      # [^footnote]
    INS   = r"\{\+\+(.*?)\+\+\}"                # inserted
    DEL   = r"\{--(.*?)--\}"                    # deleted

    # attrs =

    def __init__(self, variantName:str="OurMap"):
        if (variantName == "OurMap"):
            self.theMap = self.setup_OurMap()
        else: raise KeyError(
            "Unknown Markup/down variant '%s'." % (variantName))

    @staticmethod
    def HtmlExpr(x):
        return r'<%s(attrs)\s*>(.*?)</%s\s*>' % (x, x)

    def setup_OurMap(self):
        im = InlineMapper
        return [
            # Regex,    HTML,     Format spec
            ( im.POP3,  "I",      TextStyle(italic=1)),
            ( im.POP2,  "B",      TextStyle(bold=1)),
            ( im.TICK,  "TT",     TextStyle(sans_serif=1)),
            ( im.STAR,  "I",      TextStyle(italic=1)),
            ( im.UNDER, "B",      TextStyle(bold=1)),
            ( im.HYPH,  "STRIKE", TextStyle(strike=1)),
            ( im.BRACK, "A",      TextStyle(link=1, ul=1)),
        ]

        # Maps for specific variants. See:
        # [https://www.iana.org/assignments/markdown-variants/]

    def setup_MarkDown(self):      # Markdown                    [RFC7763]
        raise UnimplementedError("Not yet, sorry.")

    def setup_MultiMarkdown(self): # MultiMarkdown               [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_GFM(self):           # GitHub Flavored Markdown    [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_pandoc(self):        # Pandoc                      [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_Fountain(self):      # Fountain                    [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_CommonMark(self):    # CommonMark                  [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_kramdown_rfc2629(self):  # Markdown for RFCs       [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_rfc7328(self):       # Pandoc2rfc                  [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_Extra(self):         # Markdown Extra              [RFC7764]
        raise UnimplementedError("Not yet, sorry.")

    def setup_SSW(self):           # Markdown for SSW [Paulina_Ciupak]
        raise UnimplementedError("Not yet, sorry.")

    def setup_mediaWiki(self):     #
        raise UnimplementedError("Not yet, sorry.")

    def setup_POD(self):           #
        raise UnimplementedError("Not yet, sorry.")

    def setup_HTML(self):          #
        raise UnimplementedError("Not yet, sorry.")


    def formatBlock(self, b):
        """Run through ordered list of regexes to match inline markup.
        For each case found, munge the text by one of:
            * adding ANSI color or effect escapes around it
            * surrounding it with inserted characters (say, quotation marks)
            * translating it to a Unicode alternate, such as MATHEMATICAL BOLD
        TODO: This will only deal with non-overlapping matches. Nested
        matches should still work, though, because markdown is typically
        accomplished by leading and trailing *punctuation*, and punctuation
        should not be changed by any of the contemplated formatting hacks.
        For example, changing `_very_` by dropping the underscores and
        translating the "very" to some Unicode alternates, won't block bolding
        via ANSI bright (though it would block a further translation to
        MATHEMATICAL BOLD -- one reason to check for bold-italic first.
        """
        global theStyle
        theStyle = self
        for matchTuple in self.theMap:
            regex, _, theStyle = matchTuple
            b = re.sub(regex, theStyle.applyViaMatchObject, b)
        return b


###############################################################################
# Enumerated types, mainly for values you can set a style property to.
# SEE MRender and MStyle
#
class ANSI_Color(Enum):
    BLACK   = 0  # Actually means "default"?
    RED     = 1
    GREEN   = 2
    YELLOW  = 3
    BLUE    = 4
    MAGENTA = 5
    CYAN    = 6
    WHITE   = 7
    DEFAULT = 9


class ANSI_Effect(Enum):
    PLAIN      = 0    #  no special effect
    BOLD       = 1    #  aka 'bright'
    FAINT      = 2
    ITALIC     = 3    #  (rare)
    UNDERLINE  = 4    #  aka 'ul'
    BLINK      = 5
    FBLINK     = 6    #  aka 'fastblink' (rare)
    REVERSE    = 7    #  aka 'inverse'
    CONCEALED  = 8    #  aka 'invisible' or 'hidden'
    STRIKE     = 9    #  aka 'strikethru' or 'strikethrough'


# Bit flags to identify the features of Unicode alternates
#
class UBits(Flag):
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


# Cleaner way to request Unicode Mathematical and other (pseudo-)fonts.
# Would like a clean way to split out bold and italic -- though
# you only get the full set of { roman, bold, italic, bold-italic } for
# plain and sans-serif.
# With ANSI effects, you can bold any of them, and maybe italic?
# What happens if you do ANSI bold *and* Mathematical Bold?
#
class UC_Alts(Enum):
    PLAIN                   = (UBits.UNONE               , 'ULD'),
    BOLD                    = (UBits.UBOLD               , 'ULD'),
    ITALIC                  = (UBits.UITAL               , 'UL-'),
    BOLD_ITALIC             = (UBits.UBOLD | UBits.UITAL , 'UL-'),

    SANS_SERIF              = (UBits.USANS               , 'ULD'),
    SANS_SERIF_BOLD         = (UBits.USANS | UBits.UBOLD , 'ULD'),
    SANS_SERIF_ITALIC       = (UBits.USANS | UBits.UITAL , 'UL-'),
    SANS_SERIF_BOLD_ITALIC  = (UBits.USANS | UBits.UBOLD | UBits.UITAL, 'UL-'),

    FRAKTUR                 = (UBits.UFRAK               , 'UL-'),
    BOLD_FRAKTUR            = (UBits.UFRAK | UBits.UBOLD , 'UL-'),

    SCRIPT                  = (UBits.USCRP               , 'UL-'),
    BOLD_SCRIPT             = (UBits.USCRP | UBits.UBOLD , 'UL-'),

    MONOSPACE               = (UBits.UMONO               , 'ULD'),

    DOUBLE_STRUCK           = (UBits.UDOUB               , 'ULD'),
    FULLWIDTH               = (UBits.UWIDE               , 'ULD'),

    CIRCLED                 = (UBits.UCIRC               , 'ULD'),
    NEGATIVE_CIRCLED        = (UBits.UCIRC | UBits.UNEGA , 'U--'),
    SQUARED                 = (UBits.USQUA               , 'U--'),
    NEGATIVE_SQUARED        = (UBits.USQUA | UBits.UNEGA , 'U--'),
    PARENTHESIZED           = (UBits.UPARE               , 'ULD'),  # (no 0)

    SUBSCRIPT               = (UBits.USUB                , '--D'),
    SUPERSCRIPT             = (UBits.USUP                , '--D'),


class TargetType:
    """A followable reference for a link. May go to another section (via
    ID, title, XPointer, XPath, filesystem path, or URL.
    TOOO:/ Switch this to use my Record class.
    """
    def __init__(self):
        self.url      = None
        self.path     = None
        self.idref    = None
        self.title    = None
        self.query    = None
        self.style    = None
        self.showPrev = True


class Transclusion:
    """A class to represent automatically-embedded links.
    TODO Later
    """

class QuoteType(Enum):
    NONE      = 0
    S_PLAIN   = 1
    S_CURLY   = 2
    S_ANGLE   = 3
    S_LOW9    = 4
    D_PLAIN   = 11
    D_CURLY   = 12
    D_ANGLE   = 13
    D_LOW9    = 14
    T_ANGLE   = 21
    BACKP     = 99


###############################################################################
#
class GlobalPropValues(Enum):
    INHERIT    = 1
    INITIAL    = 2
    NONE       = 3


###############################################################################
#
class TextStyle(dict):
    """A full-up style def, which is a dict of typed properties. This is just
    enough for inline objects. Block object style defs have all these plus
    more properties, so make sense as a subclass.
    Cf my `Record.py` package.
    """
    textPropInfos = {
        # fonts etc.
        # propName    : (type,  default),
        'bold'        : (bool,  False),
        'italic'      : (bool,  False),
        'sans'        : (bool,  False),
        'mono'        : (bool,  False),
        'underline'   : (bool,  False),
        'strike'      : (bool,  False),
        'overline'    : (bool,  False),

        'smallCap'    : (bool,  False),
        'allCap'      : (bool,  False),

        'super'       : (bool,  False),
        'sub'         : (bool,  False),

        'ufont'       : (UC_Alts,    None),

        # color etc.
        'color'       : (ANSI_Color, None),
        'bgcolor'     : (ANSI_Color, None),
        'effect'      : (ANSI_Effect,None),

        # hypertext  TODO: later
        'before'      : (Transclusion, None),
        'after'       : (Transclusion, None),
        'hot'         : (bool, False),
    }
    def __init__(self, **kwargs):

        self.bold        = False
        self.italic      = False
        self.sans        = False
        self.mono        = False
        self.underline   = False
        self.strike      = False
        self.overline    = False

        self.smallCap    = False
        self.allCap      = False

        self.super       = False
        self.sub         = False

        self.ufont       = None
        self.quote       = QuoteType.D_CURLY  ## Watch out for code blocks!

        # color etc.
        self.color       = None
        self.bgcolor     = None
        self.effect      = None

        # hypertext  TODO: later
        self.before      = None
        self.after       = None
        self.hot         = False

        # Make sure everybody got initialized
        for k in TextStyle.textPropInfos.keys():
            assert k in self.__dict__

        for k, v in kwargs.items():
            if (k in self.textPropInfos and
                self.textPropInfos[0](v)):
                self[k] = self.textPropInfos[0](v)

        if self.mono: self.quote = QuoteType.D_PLAIN
        super(TextStyle, self).__init__()

    def __setitem__(self, propName, val):
        if (propName not in self.textPropInfos):
            raise ValueError("Cannot set TextStyle property '%s'." % (propName))

        # If they passed one of the GlobalPropValues, that's ok for any prop.
        try:
            gpv = GlobalPropValues[propName]
            super(TextStyle, self).__setitem__(propName, gpv)
        except ValueError:
            pass

        typeNeeded = self.textPropInfos[propName][0]
        if (isinstance(val, typeNeeded)):
            super(TextStyle, self).__setitem__(propName, typeNeeded(val))
        else:
            raise ValueError("TextStyle property '%s' takes %s, not %s." %
                (propName, typeNeeded, type(val)))

    def applyViaMatchObject(self, mat):
        txt = mat.group(1)
        return self.applyProperties(txt)

    def applyProperties(self, txt):
        """Run through the properties and for each that is set by this
        style, do something to apply it to the text.

        On the fly seems quicker and easier, but:
        * How do you know what color is around you, to contrast?
        * How to you keep the regexes from matching overlaps, especially
          after you've started translating and inserting escapes?
        * What about size changes (fullwidth, double-height ANSI, prop?
        But the full tree seems painfully close to DOM.
        """
        if (self.allCap):      txt = Styler.mk_allCap(txt)
        if (self.smallCap):    txt = Styler.mk_link(txt)

        if (self.hot):         txt = Styler.mk_sans(txt)
        if (self.quote):       txt = Styler.mk_quote(txt)

        if (self.underline):   txt = Styler.mk_underline(txt)
        if (self.strike):      txt = Styler.mk_strike(txt)
        if (self.overline):    txt = Styler.mk_overline(txt)

        if (self.bold and self.italic): txt = Styler.mk_bolditalic(txt)
        elif (self.bold):      txt = Styler.mk_bold(txt)
        elif (self.italic):    txt = Styler.mk_italic(txt)

        if (self.sans):        txt = Styler.mk_sans(txt)
        if (self.mono):        txt = Styler.mk_mono(txt)

        if (self.super):       txt = Styler.mk_super(txt)
        if (self.sub):         txt = Styler.mk_sub(txt)
        return txt


###############################################################################
#
class Styler:  # All methods static
    """Actually apply various rendering options/properties. This is
    highly device/medium dependent, which is the main reason it's not just
    part of TextStyle. For example, a request for bold italic could:
        * translate to MATHEMATICAL BOLD ITALIC
        * use ANSI italic and bright effects
        * translate to MATHEMATICAL BOLD and use ANSI italic effect
        * translate to MATHEMATICAL ITALIC and use ANSI bright effect
        * translate to x^Hx^H_
        * mess with colors
        * generate HTML or something else
        * signal a speech module to be emphatic or loud or...
    """
    cm = ColorManager.ColorManager()

    loadedXTabs = {}

    ### Case-related effects
    #
    @staticmethod
    def mk_allCap(txt):
        return txt.upper()

    @staticmethod
    def mk_titleCap(txt):
        return txt.title()

    @staticmethod
    def mk_noCap(txt):
        return txt.lower()

    @staticmethod
    def mk_smallCap(txt):
        raise UnimplementedError()

    ### Quotation-related effects
    #
    @staticmethod
    def mk_quote(txt, quoteOption='D_CURLY'):
        """Add quotes around the text.
        """
        qt = quoteOption
        if (qt=='D_PLAIN'):	# Double straight quotes, then single
            pair = FancyText.qPairs['dplain']
        elif (qt=='D_CURLY'):		# Double open/close quotes, then single
            pair = FancyText.qPairs['double']
        elif (qt=='D_ANGLE'):		# Double angle quotes, then single
            pair = FancyText.qPairs['dangle']
        elif (qt=='D_LOW9'):		# hi-9 on open, low-9 on close
            pair = FancyText.qPairs['dlow9']

        elif (qt=='S_PLAIN'):	# Single straight quotes, then double
            pair = FancyText.qPairs['splain']
        elif (qt=='S_CURLY'):	# Single open/close quotes, then double
            pair = FancyText.qPairs['single']
        elif (qt=='S_ANGLE'):	# Single angle quotes, then double
            pair = FancyText.qPairs['sangle']
        elif (qt=='LOW9'):		# hi-9 on open, low-9 on close
            pair = FancyText.qPairs['slow9']

        elif (qt=='BACKP'):		# "`" on both ends.
            pair = ( ord("`"), ord("`") )
        else:
            raise ValueError("Unknown quote type '%s'." % (qt))

        return chr(pair[0]) + txt + chr(pair[1])

    ### Color and ANSI terminal-related effects
    #
    @staticmethod
    def mk_bolditalic(txt):  # Or use math bold italic
        return(Styler.cm.colorize(txt.group(1), fg="red", effect='bold'))

    @staticmethod
    def mk_bold(txt):  # Or use math bold
        return(Styler.cm.colorize(txt.group(1), effect='bold'))

    @staticmethod
    def mk_italic(txt):  # Or use math italic
        return(Styler.cm.colorize(txt.group(1), fg="red"))

    ### Unicode alternate effects
    #
    @staticmethod
    def mk_sans(txt):
        mathKey = ('Latin', 'SANS-SERIF')
        if (mathKey not in Styler.loadedXTabs):  # First time
            Styler.loadedXTabs[mathKey] = mathAlphanumerics.getTranslateTable(
                mathKey[0], mathKey[1])
        return txt.translate(Styler.loadedXTabs[mathKey])

    @staticmethod
    def mk_mono(txt):
        mathKey = ('Latin', 'MONOSPACE')
        if (mathKey not in Styler.loadedXTabs):  # First time
            Styler.loadedXTabs[mathKey] = mathAlphanumerics.getTranslateTable(
                mathKey[0], mathKey[1])
        return txt.translate(Styler.loadedXTabs[mathKey])

    @staticmethod
    def mk_super(txt):
        mathKey = ('Latin', 'SUPERSCRIPT')
        if (mathKey not in Styler.loadedXTabs):  # First time
            Styler.loadedXTabs[mathKey] = mathAlphanumerics.getTranslateTable(
                mathKey[0], mathKey[1])
        return txt.translate(Styler.loadedXTabs[mathKey])

    @staticmethod
    def mk_sub(txt):
        mathKey = ('Latin', 'SUBSCRIPT')
        if (mathKey not in Styler.loadedXTabs):  # First time
            Styler.loadedXTabs[mathKey] = mathAlphanumerics.getTranslateTable(
                mathKey[0], mathKey[1])
        return txt.translate(Styler.loadedXTabs[mathKey])

    ### Overstrike effects   # TODO: Make length counting handle combiners
    # TODO: Add U+0033c COMBINING SEAGULL BELOW
    #
    @staticmethod
    def mk_underline(txt):
        COMBINER = chr(0x00332)  # COMBINING LOW LINE
        return re.sub(r'(.)', "\\1" + COMBINER, txt)

    @staticmethod
    def mk_underline2(txt):
        COMBINER = chr(0x00333)  # COMBINING DOUBLE LOW LINE
        return re.sub(r'(.)', "\\1" + COMBINER, txt)

    @staticmethod
    def mk_strike(txt):
        COMBINER = chr(0x00305)  # COMBINING OVERLINE
        return re.sub(r'(.)', "\\1" + COMBINER, txt)

    @staticmethod
    def mk_overline(txt):
        COMBINER = chr(0x00305)  # COMBINING OVERLINE
        return re.sub(r'(.)', "\\1" + COMBINER, txt)

    @staticmethod
    def mk_overline2(txt):
        COMBINER = chr(0x0033f)  # COMBINING DOUBLE OVERLINE
        return re.sub(r'(.)', "\\1" + COMBINER, txt)

    @staticmethod
    def mk_slashed(txt):
        COMBINER = chr(0x00338)  # COMBINING LONG SOLIDUS OVERLAY
        return re.sub(r'(.)', "\\1" + COMBINER, txt)

    ### Hypertext-related effects
    #
    @staticmethod
    def mk_link(txt):
        if (':' in txt.group(1)):
            anchor, ref = txt.group(1).split(':', maxsplit=1)
        else:
            anchor = ref = txt.group(1)
        ref = ref.strip("\"'")
        mat = re.match(r'(IETF\s*)?RFC\s*(\d+)', ref)
        msg = Styler.cm.colorize(anchor, fg="blue", bold=1)
        return(msg)

    ### Other effects
    #
    @staticmethod
    def mk_nBrk(txt):  # Prevent line-breaks inside
        return(re.sub(r'\s', unichr(160), txt.group(1)))


###############################################################################
#
class BlockStyle(TextStyle):  # TODO: Later
    blockPropInfos = {
        'marginTop'     : None,
        'marginBottom'  : None,
        'marginLeft'    : None,
        'marginRight'   : None,
        'marginFirst'   : None,

        'textAlignment' : None,
        'whitespace'    : None,    # wrap, trunc, hang
        'marker'        : None,
        'markerPos'     : None,
        #'border'        : (BorderType, None),
        "border-collapse": None,
        "padding"       : None,
        "listType"      : None,
    }
    def __init__(self):
        #for k, v in StyleType.styleProps:
        #    self[k] = v
        super(BlockStyle, self).__init__()


###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatterPlus)

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
            "--split",            action='store_true',
            help='Just split lines.')
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
    BlockFormatterPlus._options['verbose'] = args.verbose
    if (args.altFill):
        BlockFormatterPlus._options['altFill'] = BlockFormatterPlus._alt_fill

    print("*** Testing BlockFormatterPlus.py (level 2) ***\n")

    if (len(args.files) == 0):
        tfile = "/tmp/BlockFormatterPlus.md"
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
            for i0, t0 in enumerate(
                re.split(r'\n', testText, flags=re.MULTILINE | re.UNICODE)):

                print("%04d (%6d)==>%s<==\n" % (i0, lenSoFar, t0))
                lenSoFar += len(t0)
            sys.exit()

        hf = BlockFormatterPlus(None)
        print(hf._format_text(testText))

    vMsg(0, "*** DONE ***")
    sys.exit()
