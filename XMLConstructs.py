#!/usr/bin/env python
#
# sjdUtils: some generally useful stuff.
#
# 2018-01-11: Split out of sjdUtils.py.
#
#import sys
import re
import htmlentitydefs

XMLConstructsObject = None  # On demand

def getXMLConstructs(self):
    if (XMLConstructsObject is None):
        XMLConstructsObject = XMLConstructs()
        return XMLConstructsObject


###############################################################################
# Functions used on RHS of regex changes
#
def UEscapeFunction(mat):
    return("\\u%04x;" % (ord(mat.group(1))))
def controlSymbolsFunction(mat):
    return(unichr(0x2400 + ord(mat.group(1))))
def escHexFn(m):
    utf = m.group(1).encode('utf-8')
    buf = ""
    for byt in utf: buf += "_%02x" % (ord(byt))
    return(buf)
def unescFn(m):
    return(chr(hex(m.group(1))))


################################################################################
class XMLConstructs:
    """Define and compile a bunch of regexes useful for XML parsing.
    See also:
        XML/ multiXML.py, littleParser.py
        PERLLIBS/ XmlOutput.pm, XmlTuples.pm, YMLParser.pm
    """
    def __init__(self):
        self.x = self.makeRegexList()
        # Only compile when asked.
        self.xc = None

    def isXmlChar(self, c):
        """Return whether I<c> is an XML Character.
        """
        if (re.match(self.xc['xmlChar'], c)): return(1)
        return(0)

    def isXmlSpaceChar(self, c):
        """Return True iff I<c> is a valid XML space character.
        """
        if (re.match(self.xc['xmlSpace'], c)): return(1)
        return(0)

    def isXmlNameStartChar(self, c):
        """Return True iff I<c> is a valid XML name-start character.
        """
        if (re.match(self.xc['xmlNameStartChar'], c)): return(1)
        return(0)

    def isXmlNameChar(self, c):
        """Return True iff I<c> is a well-formed XML name character.
        """
        if (re.match(self.xc['xmlNameChar'], c)): return(1)
        return(0)

    def isXmlName(self, n):
        """Return True iff I<n> is a well-formed XML (element/attribute/etc) name.
        """
        if (re.match(self.xc['xmlName'], n)): return(1)
        return(0)

    def isXmlNmtoken(self, n):
        """Return True iff I<c> is a well-formed XML name token.
        """
        if (re.match(self.xc['xmlNmToken'], n)): return(1)
        return(0)

    def makeXmlName(self, n, asciiOnly=True):
        """Clean up the given string to be a well-formed XML name.
        """
        if (asciiOnly):
            n = re.sub(self.xc['xmlNonNameCharA'], r'_', n)
        else:
            n = re.sub(self.xc['xmlNonNameCharU '], r'_', n, re.U)
        if (not self.isXmlNameStartChar(n[0])): n = "_" + n
        return(n)

    def escapeXmlName(self, s, asciiOnly=False):
        """Turn non-name-characters in I<s> to _xx, so that any string
        becomes a legitimate (if long!) XML Name.
        """
        if (asciiOnly):
            s = re.sub(self.xc['xmlNonNameCharA'], escHexFn, s, re.I)
        else:
            s = re.sub(self.xc['xmlNonNameCharU'], escHexFn, s, re.I|re.U)
        return(s)

    def unescapeXmlName(self, s, escapeChar="_"):
        """Undo the escaping done by I<escapeXmlName>.
        """
        if (escapeChar=='_'):
            s = re.sub(self.unescape, unescFn, s, re.I)
        else:
            s = re.sub(r'('+escapeChar+r'[0-9a-f][0-9a-f])', unescFn, s, re.I)
        return(s)


    ### Regexes for XML

    def compileRegexList(self):
        self.xc = {}
        for k, v in self.x.items():
            try:
                self.xc[k] = re.compile(v)
            except Exception as e:
                print("XMLConstructs setup failed compiling: %s:\n    %s" % (v, e))
        return self.xc

    def getXMLRegex(self):
        mongo = '|'.join([
            self.x['stag'],
            self.x['empty'],
            self.x['etag'],
            self.x['ms'],
            self.x['com'],
            self.x['pi'],
            self.x['xdcl'],
            self.x['DOCTYPE'],
            self.x['gent'],
            self.x['text'],
        ])
        return mongo

    def makeRegexList(self):
        # Character classes
        xmlChar          = u"[\t\n\r\x20-\uD7FF\uE000-\uFFFD]"
            #"\x{00010000}-\x{0010FFFF}"
        xmlSpace         = r"[\t\n\r\x20]"
        xmlNameStartCharList = (
            u":A-Z_a-z\xc0-\xd6\xd8-\xf6\xf8-\u02ff\u0370-\u037d\u037f-\u1fff" +
            u"\u200c\u200d\u2070-\u218f\u2c00-\u2fef" +
            u"\u3001-\ud7ff\uf900-\ufdcf" + u"\ufdf0-\ufffd")
            #"\x{00010000}-\x{000effff}"
        xmlNameCharList = r"-.0-9\u00b7\\u0300-\u036f\u203f-\u2040"+xmlNameStartCharList
        xmlNameStartChar      = r'[' +xmlNameStartCharList+ r']'
        xmlNameChar           = r'[' +xmlNameCharList+ r']'

        xmlNonNameCharA       = r'([^-.:\w])'
        xmlNonNameCharU       = r'([^-.:\w])'

        # Basic delimiters
        mso                   = r'<!\[CDATA\['
        msc                   = r']]>'
        como                  = r'<!--'
        comc                  = r'-->'
        pio                   = r'<\?'
        pic                   = r'\?>'
        mdo                   = r'<!'
        mdc                   = r'\s*>'

        # Low-level constructs (these are also copied in the dict)
        xmlName               = r'(' +xmlNameStartChar+xmlNameChar+ r'*)'
        xmlNmToken            = r'(' +xmlNameChar+ r'+)'
        qlit                  = r'(".*?"|\'.*?\')'
        attr                  = r'(\s+(' +xmlName+ r')\s*=\s*(' +qlit+ r'))'
        subset                = r'\[' + r'[^\]]*' + r'\]'   ### FIX: Imprecise
        text                  = r'([^<&]+)'

        x = {}

        x['xmlChar']          = xmlChar
        x['xmlNmToken']       = xmlNmToken
        x['qlit']             = qlit
        x['attr']             = attr
        x['subset']           = subset
        x['text']             = text

        x['xmlSpace']         = xmlSpace
        x['xmlNameStartChar'] = xmlNameStartChar
        x['xmlNameChar']      = xmlNameChar

        x['xmlNonNameCharA']  = xmlNonNameCharA
        x['xmlNonNameCharU']  = xmlNonNameCharU

        x['xmlName']          = xmlName        # Tags
        x['stag']             = r'<' +xmlName+attr+ r'*\s*>'
        x['empty']            = r'<' +xmlName+attr+ r'*\s*/>'
        x['etag']             = r'</' +xmlName+ r'\s*>'

        # Entity and character references
        x['pent']     = r'%' +xmlName+ r';'
        x['nent']     = r'&' +xmlName+ r';'
        x['dent']     = r'&#(\d+);'
        x['hent']     = r'&#([\da-fA-f]+);'
        x['gent']     = r'&(#\d+|#[xX][\da-fA-F]+|' +xmlName+ r');'

        # Other constructs
        x['ms']       = '(?P<ms>'   + mso + r'([^\]|][^\]|\]\][^>])*)' +msc
        x['com']      = '(?P<com>'  + como+ r'([^-]|-[^-])*)' +comc
        x['pi']       = '(?P<pi>'   + pio + r'([^?]|\?[^?]))' +pic
        x['xdcl']     = '(?P<xdcl>' + pio + r'XML\s+([^?]|\?[^?]))' +pic
        x['DOCTYPE']  = (mdo+ r'DOCTYPE\s+'  +xmlName+ r'\s+(PUBLIC|SYSTEM)' +
             r'\s*' +qlit+ r'(\s*' +qlit+ r')?' + r'\s*' +subset+ r'\s*>' )
        x['ELEMENT']  = mdo + r'ELEMENT\s+'  +xmlName+ r'\s+(.*?)' +mdc
        x['ATTLIST']  = mdo + r'ATTLIST\s+'  +xmlName+ r'\s+(.*?)' +mdc
        x['ENTITY']   = mdo + r'ENTITY\s+(\s+)?' +xmlName+ r'\s+(.*?)' +mdc
        x['NOTATION'] = mdo + r'NOTATION\s+' +xmlName+ r'\s+(.*?)' +mdc

        x['document'] = '(' + ('|'.join([
            x['stag'],
            x['empty'],
            x['etag'] ,
            x['nent'],
            x['dent'],
            x['hent'],
            x['ms'],
            x['com'],
            x['xdcl'],
            x['pi'],
        ])) + ')'
        return x

    # =========================================================================
    def oneRegex(self, s):
        for mat in (re.finditer(self.x['document'], s)):
            print("***" + mat.group(1))
        return

    # =========================================================================
    def next(self, text):
        """A trivial XML pull parser built on the regexes.
        Returns:
            A tuple representing the next SAX-like event.
            Item [1] tells how much of 'text' the caller should drop from text.
        """
        if (not text): return('FIN', "")
        c1 = text[0]
        try: c2 = text[1]
        except IndexError: c2 = ''
        if (c1 == '<'):
            if (c2 == '!'):
                for x in ['com','DOCTYPE','ELEMENT','ATTLIST','ENTITY','NOTATION','ms']:
                    mat = re.match(self.xc[x], text)
                    if (mat): return(x, mat.end()-mat.start(), mat.group(1))
                return('ERROR', '')
            elif (c2 == '?'):
                for x in ['xdcl', 'pi' ]:
                    mat = re.match(self.xc[x], text)
                    if (mat): return(x, mat.end()-mat.start(), mat.group(1))
                return('ERROR', '')
            elif (c2 == '/'):
                mat = re.match(self.xc['etag'], text)
                if (mat): return('ETAG', mat.end()-mat.start(), mat.group(1))
                return('ERROR', '')
            else:
                mat = re.match(self.xc['stag'], text)
                eType = None
                if (mat):
                    eType = 'STAG'
                else:
                    mat = re.match(self.xc['empty'], text)
                    if (mat): eType = 'EMPTY'
                if (not mat): return('ERROR', '')
                tag = mat.match
                retItems = [ eType, mat.end()-mat.start(), mat.group(1)]
                for mat in re.finditer(self.xc['attr'], tag):
                    retItems.append(mat.group(1))
                    retItems.append(mat.group(2))
                return(retItems)
        elif (c1 == '&'):
            mat = re.match(self.xc['pent'], text)
            if (mat): return('PARAM', mat.end()-mat.start(), mat.group(1))
            mat = re.match(self.xc['nent'], text)
            if (mat):
                try:
                    cp = htmlentitydefs.name2codepoint[mat.group(1)]
                    return('TEXT', mat.end()-mat.start(), unichr(cp))
                except:
                    return('ERROR', mat.end()-mat.start(), 'Unknown entity "%s".' % (mat.group(1)))
            mat = re.match(self.xc['dent'], text)
            if (mat): return('TEXT', mat.end()-mat.start(), chr(int(mat.group(1),10)))
            mat = re.match(self.xc['hent'], text)
            if (mat): return('TEXT', mat.end()-mat.start(), chr(int(mat.group(1),16)))
            return('ERROR', mat.end()-mat.start(), '')
        else:
            mat = re.match(self.xc['text'], text)
            return('TEXT', mat.end(), text[0:mat.end()])

###############################################################################
###############################################################################

pod = """

=head1 Class XMLConstructs

This class supplies "isa" functions for various XML character classes,
a few other XML-related utility functions (including a simple "pull" SAX-like
parser,
and a dict of regular expressions for many XML constructs.

Get an instance via:
    xc = su.getXMLConstructs()

The instance includes the following 'isa'-like functions, and a hash named .x
that has all the regexes. They are not compiled until you say:
    cexprs = xc.compileRegexList()

=over

=item * B<isXmlChar(c)>

Return whether I<c> is an XML Character.

=item * B<isXmlSpaceChar(c)>

Return True iff I<c> is a valid XML space character.

=item * B<isXmlNameStartChar(c)>

Return True iff I<c> is a valid XML name-start character.

=item * B<isXmlNameChar(c)>

Return True iff I<c> is a well-formed XML name character.

=item * B<isXmlName(n)>

Return True iff I<n> is a well-formed XML (element/attribute/etc) name.

=item * B<isXmlNmtoken(n)>

Return True iff I<c> is a well-formed XML name token.

=back


=head3 Other functions in XMLConstructs

=over

=item * B<next(xmlString)>

This is also an extremely simple (still experimental)
"pull"-style parser, consisting of one method that returns the next SAX-like
event as a list of [ eventType, data... ].

Experimental.

=item * B<makeXmlName(n, asciiOnly=True)>

Clean up the given string to be a well-formed XML name.
This is done by converting non-name-characters to "_",
and prefixing "_" if the result does not begin with
a name start character.
If I<asciiOnly> is True, non-ASCII name characters are
also changed to "_".

=item * B<escapeXmlName(s, asciiOnly)>

Turn non-name-characters in I<s> to _xx, so that any string
becomes a legitimate (if long!) XML Name.
B<Note>: I<escapeChar> is not yet supported.

=item * B<unescapeXmlName(s)>

Undo the escaping done by I<escapeXmlName>.

=back


=head3 XML constructs as regexes

See L<http://www.w3.org/TR/REC-xml/>. These can be
used to make a simple parser, or as parts of anything else.

The supported construct names (keys to the returned hash of regexes, whether
compiled or raw) are:

Character lists:
    xmlChar, xmlSpace, xmlNameStartChar, xmlNameChar

"Small" items:
    xmlName, qlit, attr, subset, text

Tags:
    stag, empty, etag

Entity and character references:
    pent (parameter entity reference),
    gent (any general entity reference),
    nent (any numeric character reference),
    dent (decimal character reference),
    hent (hexadecimal character reference)

Other:
    ms, com, pi, xdcl, DOCTYPE, ELEMENT, ATTLIST, ENTITY, NOTATION

Using these, you can make a useful (but not, by itself, fully conforming)
parser with:

=over

=item * B<getXMLRegex>()

This will return a fairly large regex, which is a disjunction of smaller regexes
for: start tag, empty tag, end tag, marked section, comment, pi, xml declaration,
DOCTYPE declaration, general entity, and text.

A well-formed XML document should always be a sequence of  matches to this
regex (though not all documents that match are WF XML documents -- for example,
the regex knows nothing about matching or balancing start- and end-tags).

So you can parse by using this regex to "split" some XML, and then examining the
first few characters of each match to identity the construct (to do this most
quickly, check the very first char for '&' or '&'; anything else is a textnode):

    if the first character is '&':
        ENTITY REFERENCE
    elif the first character is NOT '<':
        TEXT NODE
    else check for these insitial strings
        <?xml     XML declaration
        <?        PI
        <!--      COMMENT
        <![CDATA[ MARKED SECTION
        </        END TAG
        <         START TAG

Start-tags are the only items with non-trivial internal syntax; but once you
have one, just strip off the tag name and then use re.finditer() again, with
the 'attr' expression provided (which accepts leading whitespace by itself):

    bigExpr = re.compile(su.getXMLConstructs().getXMLRegex())
    for mat in re.finditer(bigExpr, rawXML):
        m = mat.group()
        if (m[0] == '<' and m[1].isalpha()):
            tmat = re.match(r'(<[^\\s/>]+)', m)
            handleTag(tmat.group(1))
            attrlist = m[len(tmat.group(1)):]
            for amat in re. finditer(attrExpr, attrlist):
                handleAttr(amat.group(1))
        else:
            handleOtherEvent(m)


=for nobody ================================================================

=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see http://www.derose.net/steve/utilities/.
"""
