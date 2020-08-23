#!/usr/bin/env python
#
# markdownToXML.py based on prior Perl mediaWiki2HTML. See also
# cleanMediaWiki.py and readWikipediaDump.py.
#
# This just handles converting MarkDown-like constructs.
# For macros and links (such as in Wikipedia), see cleanMediaWiki.py,
# which calls this.
#
# 2018-05-18: Ported from Perl. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
from __future__ import print_function
import sys, os
import argparse
import re
import htmlentitydefs
import StringIO

import XmlOutput
from alogging import ALogger
lg = ALogger(1)

try:
    x = unichr(0x0a)
except NameError:
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): return str(s, encoding, errors)

__metadata__ = {
    'title'        : "markDownToXML.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 2.7.6",
    'created'      : "2018-05-18",
    'modified'     : "2018-05-18",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Convert MediaWiki's MarkDown-like markup system to HTML/XML, trying to
retain most of the underlying information.

See L<https://www.mediawiki.org/wiki/Markup_spec#Can_be_used_anywhere>.

In particular (and quite unlike many other packages):

    * Leave existing HTML untouched
    * Convert macros and their arguments (even deeply nested)
    * Convert [[]], ISBN, and other links
    * Convert MediaWiki mark(up/down) conventions

=Known bugs and limitations=

Does not handle <nowiki> to suppress conversion.

Does nothing with <math>.

=Related Commands=

There are many, many parsers and converters for Mediawiki data.
The "reference" one, the Wikipedia parser, is in PHP.
A list of 'parsers' is at L<https://www.mediawiki.org/wiki/Alternative_parsers>.
I looked at a lot, and most seems to be extremely specialized.

There are also Python packages that "convert" MarkDown and/or MediaWiki
to HTML; but the ones I tried all failed in various ways.

    https://github.com/trentm/python-markdown2
    import markdown2
    buf = markdown2.markdown(self.rawText)
    return buf.encode('utf-8')

    https://github.com/dcramer/py-wikimarkup
    from wikimarkup import parse
    return parse(self.rawText)

=Rights=

Copyright 2018, Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].

=Options=
"""

blockTypes = set([
    'BLANK',       # whitespace-only (block-separator)
    'PRE',         # Pretty much just means 'indented'
    'HEAD',        # whatever level
    'RULE',        # -----
    'TROW',        # table row
    'ITEM',        # list item
    'DT',
    'DD',
    'PARA',        # unindented (continuation) line
    ])


###############################################################################
#
class markdownToXML:
    def __init__(self):
        self.options = {
            'verbose':      1,
        }
        self.xo = XmlOutput.XmlOutput()

    def convert(self, buf):
        """Read and deal with one individual document/page/file.
        Run a first pass that combines individual lines into blocks, and
        labels each block with a type from the list above.
        """
        assert isinstance(buf, unicode)
        blocks = self.linesToBlocks(buf.split("\n"))
        if (self.options['verbose'] > 1):
            lg.hMsg(1, "BLOCKS")
            for i, block in enumerate(blocks):
                assert isinstance(block, unicode)
                if (0): print("%2d: %-8s [%d]: '%s'" %
                    (i, block['type'], block['level'], block['text']))

        xml = self.blocksToXML(blocks)
        assert isinstance(xml, unicode)
        return xml

    def linesToBlocks(self, recs):
        """Collect up lines that go together into what CSS would call a "block",
        assign a type to the blocks (including details like the specific
        level of a head/list/indent), and pass back an array of the blocks.
        This vastly simplifies later processing, without being gory in itself.
        """
        blocks = [ { 'type':'PARA', 'text':"", 'level':0 } ]
        recnum = 0
        for rec in recs:
            if (blocks[-1]['type'] not in blockTypes):
                lg.error("Bad block type: '%s'." % (blocks[-1]['type']))
            recnum += 1

            if (rec.strip() == ''):                        # BLANK
                if (blocks[-1]['type'] != 'BLANK'):
                    blocks.append({ 'type':'BLANK', 'text':'', 'level':1 })
                else:
                    blocks[-1]['level'] += 1
                continue

            c0 = rec[0]

            if (c0 == ' ' or c0 == "\t"):                  # PRE
                # Should a new PRE start whenever indent changes, or not?
                newLevel = self.countCharsAtStart(rec, ' ')
                if (blocks[-1]['type'] != 'PRE' or
                    blocks[-1]['level'] != newLevel):
                    blocks.append(
                        { 'type':'PRE', 'text':rec+"\n", 'level':newLevel })
                else:
                    blocks[-1]['text'] += rec + "\n"

            elif (c0 == '='):                              # HEAD
                newLevel = self.countCharsAtStart(rec, '=') - 1
                txt = rec.strip().strip('=').strip()
                blocks.append({ 'type':'HEAD', 'text':txt, 'level':newLevel })

            elif (c0 == '-'):                              # RULE
                newLevel = self.countCharsAtStart(rec, '-')
                blocks.append({ 'type':'RULE', 'text':'', 'level':newLevel })

            elif (c0 == '|'):                              # TROW
                cols = rec.split("|")
                blocks.append({ 'type':'TROW', 'text':'', 'level':0, 'cols':cols })

            elif (c0 == '*' or c0 == '#'):                 # ITEM
                newLevel = self.countCharsAtStart(rec, '*=')
                listTypes = rec[0:newLevel].split()
                blocks.append({ 'type':'ITEM',
                    'text':rec[newLevel:], 'level':newLevel,
                    'typeSequence':rec[0:newLevel].split() })

            elif (c0 == ';'):                              # DEF TERM
                blocks.append({ 'type':'DT', 'text':rec[1:], 'level':0 })

            elif (c0 == ':'):                              # DEF DESCR
                blocks.append({ 'type':'DD', 'text':'', 'level':0 })

            elif (rec.startswith("<nowiki>")):             # NOWIKI
                blocks.append({ 'type':'NOWIKI', 'text':'', 'level':0 })
            elif (rec.startswith("</nowiki>")):
                blocks[-1]['text'] += rec
                blocks.append({ 'type':'BLANK', 'text':'', 'level':0 })

            else:                                          # TEXT/PARA
                if (blocks[-1]['type'] in [ 'BLANK', 'RULE', 'TROW' ]):
                    blocks.append({ 'type':'PARA', 'text':rec, 'level':0 })
                else:
                    blocks[-1]['text'] += rec.strip() + ' '

        return(blocks)

    def blocksToXML(self, blocks):
        """Now that each 'block' is together, make them into XHTML with
        legit nesting.
        """
        xo = self.xo
        outBuf = StringIO.StringIO()
        xo.setOutput(outBuf)
        for i, block in enumerate(blocks):
            btype = block['type']
            btext = block['text']
            btext = self.doInlines(btext)
            blevel = block['level']
            if (i==0):
                pass

            elif (btype == 'BLANK'):
                xo.closeAllOfThese(
                    [ 'p', 'dl', 'ul', 'ol', 'table' ])

            elif (btype == 'PRE'):
                xo.openElement('pre', '', btext)

            elif (btype == 'HEAD'):
                xo.makeSmallElement('h%d' % (blevel), "", btext)

            elif (btype == 'RULE'):
                xo.makeEmptyElement('hr')

            elif (btype == 'TROW'):
                if (xo.howManyAreOpen('table') == 0):
                    xo.openElement('table')
                    xo.openElement('tbody')
                else:
                    xo.closeToElement('tbody')
                xo.openElement('tr')
                cells = btext.split("|")
                for cell in cells:
                    xo.makeSmallElement('td', "", cell)
                xo.closeElement('tr')

            elif (btype == 'ITEM'):
                # Do fancier stuff for nested lists...
                xo.closeElementIfOpen('li')
                xo.openElementUnlessOpen('ul')
                xo.openElement('li')
                xo.makeText(btext.strip())

            elif (btype == 'DT'):
                if (xo.howManyAreOpen('dl') == 0):
                    xo.openElement('dl')
                else:
                    xo.closeToElement('dl')
                xo.openElement('dt')
                xo.makeText(btext)

            elif (btype == 'DD'):
                xo.closeToElement('dl')
                xo.openElement('dd')
                xo.makeText(btext)

            elif (btype == 'PARA'):
                xo.makeSmallElement('p', '', btext)

            else:
                lg.error("Unknown block type '%s'." % (btype))
                xo.makeText(btext)

        xo.closeAllElements()
        result = outBuf.getvalue().decode("utf-8")
        outBuf.close()
        return result

    def countCharsAtStart(self, rec, chars='='):
        """Counts how many characters from the given list, occur at the
        beginning of the string. Used for '=' (heads), '*#' (lists), indents...
        Add support for tabs?
        """
        i = 0
        for r in rec:
            if (r not in chars): break
            i += 1
        return i


    ###########################################################################
    # Manage the XML structure going out. This includes doing whatever
    # it takes to get from the current state (element type context), to
    # a desired new one. For example:
    #     To get to heading-N, close divs through N, then open through N
    #     For lists like "*#*# xyz", generate needed opens and closes
    #     For tables, make sure there's a table open (I don't think you
    #     can have 2 tangent tables in MarkDown).
    #
    def adjustLIST(self, line):
        pass

    def doInlines(self, line):
        """Convert various inline markup.
        """
        line = re.sub(r"'''[^']*'''", r'<b>\\1</b>', line)
        line = re.sub(r"''[^']*''", r'<i>\\1</i>', line)
        line = re.sub(r"~~~~~", '<m:date/>', line)
        line = re.sub(r"~~~~", '<m:username/><m:date/>', line)
        line = re.sub(r"~~~", '<m:username/>', line)
        return line


    def doPODInlines(self, line):
        """Convert some inline markup of "POD" variety.
        See https://perldoc.perl.org/perlpod.html
        """
        line = re.sub(r"([BCEFILSXZ])<([^>]*)>", self.podFunc, line)
        return line

    def podFunc(self, mat):
        m1 = mat.group(1)
        m2 = mat.group(2)
        if   (m1 == 'B'): return "<b>%s</b>" % (m2)
        elif (m1 == 'C'): return "<code>%s</code>" % (m2)
        elif (m1 == 'E'):
            if (m2 in htmlentitydefs.name2codepoint):
                return unichr(htmlentitydefs.name2codepoint[m2])
            elif (m2 == 'verbar'):
                return '|'
            elif (m2 == 'sol'):
                return '/'
            elif (re.match(r'0[xX]([\da-fA-F]+)', m2)):
                return unichr(int(m2, 16))
            elif (re.match(r'(0[0-7]+)', m2)):
                return unichr(int(m2, 8))
            elif (re.match(r'(\d+)', m2)):
                return unichr(int(m2, 10))
            print("Unknown POD escape '%s'." % (mat.group()))
            return mat.group()
        elif (m1 == 'F'): return "<tt>%s</tt>" % (m2)
        elif (m1 == 'I'): return "<i>%s</i>" % (m2)
        elif (m1 == 'L'): return "<a href=\"%s\">%s</a>" % (m2, m2)
        elif (m1 == 'S'): return re.sub(r' ', '&ndbp;', m2)
        elif (m1 == 'X'): return "<index>%s</index>" % (m2)
        elif (m1 == 'Z'): return ""
        return mat.group()

    def doEmph(self, buf):
        buf = re.sub(r'\*(\w+)\*', "<em>\\1</em>", buf)
        buf = re.sub(r'_(\w+)_', "<em>\\1</em>", buf)
        buf = re.sub(r'``(([^`]|`[^`])*)``', "<code>\\1</code>", buf)
        buf = re.sub(r'`([^`]*)`', "<code>\\1</code>", buf)

        return buf


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    import codecs

    def processOptionsMDX():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
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
        if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)


    ###########################################################################
    # Main
    #
    args = processOptionsMDX()

    if (len(args.files) == 0):
        lg.error("No files specified....")
        sys.exit()
    else:
        for fArg in (args.files):
            lg.bumpStat("Total Args")
            mdx = markdownToXML()
            htmlFH = codecs.open(fArg, 'rb', encoding=args.iencoding)
            html = htmlFH.read()
            result = mdx.convert(html)
            lg.hMsg(0, "FINAL")
            print(result)

    if (not args.quiet):
        lg.vMsg(0,"Done.")
        lg.showStats()
