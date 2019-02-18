#!/usr/bin/env python
#
# SimplifyUnicode
#
# 2010-11-19ff: Written by Steven J. DeRose (in Perl)
# ...
# 2012-01-10 sjd: Port to Python.
#
# To do:
#     ?? Generalize to be able to operate on any \p{name} classes??
#     Deal with ligature/accent interaction (combining long s).
#     Add stripXML, nine, num, ignorecase, degeminate, punct?
#     Perhaps just work off of actual long names? "LATIN LETTER A" -> "A"...
#
# Possible additions:
#     old italic, gothic, etc. U'10300?
#     roman numerals, enclosed alphanumerics
#     vertical forms U'fe00
#     Greek and Cyrillic and Hebrew math variants?
#     ellipsis, punc ligatures U'203c...
#     sup/sub U'2070
#     Halfwidth/fullwidth U'ff00
#     Non-Latin ligatures.
#     supplemental punct U'
#     Arrows? U'2190, 2799, 27f0, 2900, 2b00
#     letterlike symbols U'2100, fractions,
#     braille U'2800
#     high surrogates U'd800, low surrogates U'dc00
#
# Integrate into:
#     findKeyWords
#     normalizeXML
#     tuples
#     vocab
#
import re
import unicodedata

try:
    x = unichr(0x0a)
except NameError:
    def unichr(n): return chr(n)

###############################################################################
#
class SimplifyUnicode:
    dispChoices = [   # for accents, ligatures, maths
        'unchanged', 'split', 'join', 'unaccent', 'space', 'delete', 'markup',
    ]

    def __init__(self, **kwargs):
        self.version       = "2015-08-15"
        self.options = {
            'entities'       : 0,
            'uriEscapes'     : 0,

            'dashes'         : 0,
            'keepMdash'      : 0,
            'halfWidths'     : 0,
            'ligaturesAll'   : 0,
            'spaces'         : 0,

            'bQuotes'        : 0,
            'dQuotes'        : 0,
            'sQuotes'        : 0,
            'quotes'         : 0,

            'accents'        : "unchanged",
            'ligatures'      : "unchanged",
            'maths'          : "unchanged",
            'numbers'        : "unchanged",
            'supers'         : "unchanged",
            'subs'           : "unchanged",
        }

        if (kwargs):
            for k, v in kwargs.items():
                self.setOption(k,v)

        # internal data
        self.dQuoteChars    = self.setupDQuotes()     # Strings
        self.sQuoteChars    = self.setupSQuotes()
        self.spaceChars     = self.setupSpaces()
        self.dashChars      = self.setupDashes()
        self.ligatureChars  = self.setupLigatures()
        self.mathStarts     = self.setupListOfMathAlphabets()  # HashRefs
        self.lig2seqBasic   = None
        self.seq2ligBasic   = None
        self.lig2seq        = None
        self.seq2lig        = None
        return(None)


    #############################################################################
    # Apply all the selected simplifications
    #
    def simplify(self, rec):
        if (self.options['entities']):
            rec = self.handle_Entities(rec)
        if (self.options['uriEscapes']):
            rec = self.handle_UriEscapes(rec)
        if (self.options['accents'] != "unchanged"):
            rec = self.handle_Diacritics(rec)
        if (self.options['ligatures'] != "unchanged"):
            rec = self.handle_Ligatures(rec)
        if (self.options['maths'] != "unchanged"):
            rec = self.handle_Maths(rec)
        if (self.options['dashes']):
            rec = self.normalize_DashChars(rec)
        if (self.options['quotes']):
            rec = self.normalize_DQuoteChars(rec)
            rec = self.normalize_SQuoteChars(rec)
            rec = re.sub("`","'",rec)
        else:
            if (self.options['dQuotes']):
                rec = self.normalize_DQuoteChars(rec)
            if (self.options['sQuotes']):
                rec = self.normalize_SQuoteChars(rec)
            if (self.options['bQuotes']):
                rec = re.sub("`","'",rec)

        if (self.options['spaces']):
            rec = self.normalize_SpaceChars(rec)
        if (self.options['halfWidths']):
            print("widths not yet supported.")
            exit(0)
        if (self.options['numbers']):
            print("numbers not yet supported.")
            exit(0)

        return(rec)


    ###########################################################################
    #
    def setOption (self, oname, v):
        if (not oname or oname not in self.options):
            raise ValueError(
                "Bad option name passed to simplifyUicode.setOption.")
        if (oname in [ "--accents", "--ligatures", "--maths",
            "--numbers", "--subs", "--supers", ]):
            if (v in SimplifyUnicode.dispChoices):
                self.options[oname] = v
            else:
                raise ValueError("Bad disp value '%s' for option '%s'." %
                    (v, oname))
        else:
            self.options[oname] = bool(v)
        return(v)

    def getOption(self, oname, v):
        return(self.options[oname])


    ###########################################################################
    #
    def normalize_Space(self, s):
        s = re.sub(r'\s\s+', " ", s.rstrip().lstrip())
        return(s)


    def normalize_SpaceChars(self, s):
        s = re.sub(r'['+self.spaceChars+r']'," ",s)
        return(s)


    def normalize_DashChars(self, s):
        s = re.sub(r'['+self.dashChars+r']',"-",s)
        return(s)


    def normalize_DQuoteChars(self, s):
        s = re.sub(r'['+self.dQuoteChars+r']',"\"",s)
        return(s)


    def normalize_SQuoteChars(self, s):
        s = re.sub(r'['+self.sQuoteChars+r']',"'",s)
        return(s)


    def normalize_Widths(self, s):
        buf = ""
        for i in (range(0,len(s))):
            n = ord(s[i:i+1])
            if (n>=0xFF01 and n<=0xFF5E): # halfwidth ASCII:
                buf += unichr(n - 0xFF01 + 0x21)
            elif (0 and n>=0xFF71 and n<=0xFF9F):  # halfwidth Katakana
                buf += + unichr(n - 0xFF71 + 0x30A1)
            else:
                buf += + unichr(n)
        return(buf)


    ###########################################################################
    #

    def handle_Entities(self, rec):
        rec = re.sub(r'&#x([a-f0-9]+);',
            lambda x: unichr(int(x.group[1],16)), rec)
        rec = re.sub(r'&#([0-9]+);',
            lambda x: unichr(int(x.group[1],10)), rec)
        rec = re.sub(r'&lt;'   , "<",  rec)
        rec = re.sub(r'&gt;'   , ">",  rec)
        rec = re.sub(r'&apos;' , "'",  rec)
        rec = re.sub(r'&quot;' , "\"", rec)
        #rec = re.sub(r'&nbsp;' , "/ ", rec)
        rec = re.sub(r'&amp;'  , "&",  rec)
        return(rec)

    def handle_UriEscapes(self, rec):
        rec = re.sub(r'([a-fA-F0-9][a-fA-F0-9])',
            lambda x: unichr(int(x.group[1],16)), rec)
        return(rec)


    def handle_Diacritics(self, rec):
        ac = self.options['accents']
        if (ac == "split"):
            print("unsupported -accents handling '" +ac + "'")
            exit(0)
        elif (ac == "join"):
            print("unsupported -accents handling '" +ac + "'")
            exit(0)
        elif (ac == "space"):
            print("unsupported -accents handling '" +ac + "'")
            exit(0)
        elif (ac == "del"):
            print("unsupported -accents handling '" +ac + "'")
            exit(0)
        elif (ac == "translit"):
            raise ValueError("translit not yet supported, sorry.")
            #rec = NFD(rec)
            #rec = re.sub(r"\pM","",rec)
        else:
            # unchanged
            pass
        return(rec)


    def handle_Ligatures(self, ligatures):
        s = ""
        s2lRef = self.seq2lig
        s2l = s2lRef
        if (ligatures == "space"):
            for lig in s2l:
                s = re.sub(lig," ",s)
        elif (ligatures == "del"):
            for lig in s2l:
                s = re.sub(lig,"",s)
        elif (ligatures == "split"):
            for lig in s2l:
                s = re.sub(lig,"s2l[lig]",s)
                print("unsupported -ligatures handling '" +ligatures + "'")
                exit(0)
        elif (ligatures == "join"):
            for lig in s2l:
                s = re.sub(lig,"s2l[lig]",s)
                print("unsupported -ligatures handling '" +ligatures + "'")
                exit(0)
        else:
            # unchanged
            pass
        return(s)


    # This is for mathematical variants on A-Z, not math symbols in general.
    #
    def handle_Maths(self, rec):
        buf = ""
        for i in (range(0,len(rec))):
            c = rec[i,i]
            letter = self.math2letter(ord(c))
            if (letter):
                buf = buf + letter
            else:
                buf = buf + c
        return(buf)



    ###########################################################################
    # Return basic ASCII letter if we got a math letter; else undef.
    #
    def math2letter(self, n):
        mathStartsRef = self.mathStarts
        ms = mathStartsRef
        for mathRange in (ms):
            if (n<mathRange or n>=mathRange+26): continue
            diff = n - mathRange
            theType = ms[mathRange]
            if (theType == "UPPER"):
                return("ABCDEFGHIJKLMNOPQRSTUVWXYZ",diff[1:])
            elif (theType == "LOWER"):
                return("abcdefghijklmnopqrstuvwxyz",diff[1:])
            else:
                print("Bad math alphabet type '%s'." % (theType))
                exit(0)
        return(None)



    ###########################################################################
    ###########################################################################
    # Following setupXxx() methods create lists of characters to map.
    #
    def setupDashes(self):
        dashChars = (
            # Leave out regular hyphen so doesn't mess up regex, and since it's
            # what we normalize *to*.
            #
            u'\u00ad' + # soft hyphen
            u'\u058a' + # armenian hyphen
            u'\u1806' + # mongolian todo soft hyphen
            u'\u1b60' + # balinese pameneng (line-breaking hyphen)
            u'\u2010' + # 008208) + hyphen) +        '-',
            u'\u2011' + # non-breaking hyphen,
            u'\u2012' + # figure dash
            u'\u2013' + # 008211) + ndash,         '-',
            u'\u2014' + # 008212, mdash,         '--',
            u'\u2015' + # 008213, horbar,        '--',
            u'\u2027' + # hyphenation point
            u'\u2043' + # hyphen bullet
            u'\u2053' + # swung dash
            #u'\u21E0' .	# LEFTWARDS DASHED ARROW
            #u'\u21E1' .	# UPWARDS DASHED ARROW
            #u'\u21E2' .	# RIGHTWARDS DASHED ARROW
            #u'\u21E3' .	# DOWNWARDS DASHED ARROW
            u'\u229d' + # circled dash
            u'\u2448' + # ocr dash

            # Box-drawing dashes
            #
            #u'\u2504' .	# ... LIGHT TRIPLE DASH HORIZONTAL
            #u'\u2505' .	# ... HEAVY TRIPLE DASH HORIZONTAL
            #u'\u2508' .	# ... LIGHT QUADRUPLE DASH HORIZONTAL
            #u'\u2509' .	# ... HEAVY QUADRUPLE DASH HORIZONTAL
            #u'\u254C' .	# ... LIGHT DOUBLE DASH HORIZONTAL
            #u'\u254D' .	# ... HEAVY DOUBLE DASH HORIZONTAL

            u'\u2e17' + # double oblique hyphen
            u'\u2E1A' + # HYPHEN WITH DIAERESIS
            u'\u301c' + # wave dash
            u'\u3030' + # wavy dash
            u'\u30a0' + # katakana-hiragana double hyphen
            u'\uFE49' + # DASHED OVERLINE
            u'\uFE4D' + # DASHED LOW LINE
            u'\uFE58' + # small em dash
            u'\ufe63' + # small hyphen-minus
            u'\uff0d' + # fullwidth hyphen-minus
            "")
        return(dashChars)


    def setupDQuotes(self):
        dQuoteChars = (
            u'\u00AB' +   # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK *
            u'\u00BB' +   # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK *
            u'\u201C' +   # LEFT DOUBLE QUOTATION MARK
            u'\u201D' +   # RIGHT DOUBLE QUOTATION MARK
            u'\u201E' +   # DOUBLE LOW-9 QUOTATION MARK
            u'\u201F' +   # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
            u'\u2358' +   # APL FUNCTIONAL SYMBOL QUOTE UNDERBAR
            u'\u235E' +   # APL FUNCTIONAL SYMBOL QUOTE QUAD
            u'\u275D' +   # HEAVY DOUBLE TURNED COMMA QUOTATION MARK ORNAMENT
            u'\u275E' +   # HEAVY DOUBLE COMMA QUOTATION MARK ORNAMENT
            u'\u301D' +   # REVERSED DOUBLE PRIME QUOTATION MARK
            u'\u301E' +   # DOUBLE PRIME QUOTATION MARK
            u'\u301F' +   # LOW DOUBLE PRIME QUOTATION MARK
        "")
        return(dQuoteChars)


    def setupSQuotes(self):
        sQuoteChars = (
            u'\u2018' +   # LEFT SINGLE QUOTATION MARK
            u'\u2019' +   # RIGHT SINGLE QUOTATION MARK
            u'\u201A' +   # SINGLE LOW-9 QUOTATION MARK
            u'\u201B' +   # SINGLE HIGH-REVERSED-9 QUOTATION MARK
            u'\u2039' +   # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
            u'\u203A' +   # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
            u'\u275B' +   # HEAVY SINGLE TURNED COMMA QUOTATION MARK ORNAMENT
            u'\u275C' +   # HEAVY SINGLE COMMA QUOTATION MARK ORNAMENT
            u'\u276E' +   # HEAVY LEFT-POINTING ANGLE QUOTATION MARK ORNAMENT
            u'\u276F' +   # HEAVY RIGHT-POINTING ANGLE QUOTATION MARK ORNAMENT
        "")
        return(sQuoteChars)



    def setupSpaces(self):
        spaceChars = (
            u'\u0009' +    # TAB
            u'\u000A' +    # LINE FEED
            u'\u000B' +    # VERTICAL TAB
            u'\u000C' +    # FORM FEED
            u'\u000D' +    # CARRIAGE RETURN
            u'\u0020' +    # SPACE
            u'\u00A0' +    # NO-BREAK SPACE

            u'\u1680' +    # OGHAM SPACE MARK

            u'\u2002' +    # EN SPACE
            u'\u2003' +    # EM SPACE
            u'\u2004' +    # THREE-PER-EM SPACE
            u'\u2005' +    # FOUR-PER-EM SPACE
            u'\u2006' +    # SIX-PER-EM SPACE
            u'\u2007' +    # FIGURE SPACE
            u'\u2008' +    # PUNCTUATION SPACE
            u'\u2009' +    # THIN SPACE
            u'\u200A' +    # HAIR SPACE
            u'\u200B' +    # ZERO WIDTH SPACE
            u'\u202F' +    # NARROW NO-BREAK SPACE
            u'\u205F' +    # MEDIUM MATHEMATICAL SPACE

            u'\u2409' +    # SYMBOL FOR HORIZONTAL TABULATION
            u'\u240B' +    # SYMBOL FOR VERTICAL TABULATION
            u'\u2420' +    # SYMBOL FOR SPACE

            u'\u3000' +    # IDEOGRAPHIC SPACE
            u'\u303F' +    # IDEOGRAPHIC HALF FILL SPACE

            u'\uFEFF' +    # ZERO WIDTH NO-BREAK SPACE (= byte-order mark)
        "")
        return(spaceChars)


    # Arabic ligatures are not here yet, because there are hundreds of them.
    #
    def setupLigatures(self):
        seq2ligBasic = {
            u'\ufb00' : 'ff',  # 'LATIN SMALL LIGATURE FF'
            u'\ufb01' : 'fi',  # 'LATIN SMALL LIGATURE FI'
            u'\ufb02' : 'fl',  # 'LATIN SMALL LIGATURE FL'
            u'\ufb03' : 'ffi', # 'LATIN SMALL LIGATURE FFI'
            u'\ufb04' : 'ffl', # 'LATIN SMALL LIGATURE FFL'
        }

        seq2lig = {
            # Latin
            u'\u0132' : 'IJ',  # 'LATIN CAPITAL LIGATURE IJ'
            u'\u0133' : 'ij',  # 'LATIN SMALL LIGATURE IJ'
            u'\u0152' : 'OE',  # 'LATIN CAPITAL LIGATURE OE'
            u'\u0153' : 'oe',  # 'LATIN SMALL LIGATURE OE'
            u'\ufb00' : 'ff',  # 'LATIN SMALL LIGATURE FF'
            u'\ufb01' : 'fi',  # 'LATIN SMALL LIGATURE FI'
            u'\ufb02' : 'fl',  # 'LATIN SMALL LIGATURE FL'
            u'\ufb03' : 'ffi', # 'LATIN SMALL LIGATURE FFI'
            u'\ufb04' : 'ffl', # 'LATIN SMALL LIGATURE FFL'
            u'\ufb05' : 'st',  # 'LATIN SMALL LIGATURE LONG S T'
            u'\ufb06' : 'st',  # 'LATIN SMALL LIGATURE ST'

            # Cyrillic
            u'\u04a4' : u'\u041d'+u'\u0413',  # 'CAPITAL EN GHE'
            u'\u04a5' : u'\u043d'+u'\u0433',  # 'SMALL EN GHE'
            u'\u04b4' : u'\u0422'+u'\u0426',  # 'CAPITAL TE TSE'
            u'\u04b5' : u'\u0442'+u'\u0446',  # 'SMALL TE TSE'
            u'\u04d4' : u'\u0410'+u'\u0415',  # 'CAPITAL A IE'
            u'\u04d5' : u'\u0430'+u'\u0435',  # 'SMALL A IE'

            # Other ### FIX
            u'\u0587' : '',  # 'ARMENIAN SMALL LIGATURE ECH YIWN'
            u'\u05f0' : '',  # 'HEBREW LIGATURE YIDDISH DOUBLE VAV'
            u'\u05f1' : '',  # 'HEBREW LIGATURE YIDDISH VAV YOD'
            u'\u05f2' : '',  # 'HEBREW LIGATURE YIDDISH DOUBLE YOD'
            u'\ua7f9' : '',  # 'MODIFIER LETTER SMALL LIGATURE OE'
            u'\ufb13' : '',  # 'ARMENIAN SMALL LIGATURE MEN NOW'
            u'\ufb14' : '',  # 'ARMENIAN SMALL LIGATURE MEN ECH'
            u'\ufb15' : '',  # 'ARMENIAN SMALL LIGATURE MEN INI'
            u'\ufb16' : '',  # 'ARMENIAN SMALL LIGATURE VEW NOW'
            u'\ufb17' : '',  # 'ARMENIAN SMALL LIGATURE MEN XEH'
            u'\ufb1f' : '',  # 'HEBREW LIGATURE YIDDISH YOD YOD PATAH'
            u'\ufb4f' : '',  # 'HEBREW LIGATURE ALEF LAMED'
            u'\ufe20' : '',  # 'COMBINING LIGATURE LEFT HALF'
            u'\ufe21' : '',  # 'COMBINING LIGATURE RIGHT HALF'
        }

        lig2seqBasic = {}
        lig2seq = {}

        # Add the basic to the main map
        for seq in (seq2ligBasic):
            seq2lig[seq] = seq2ligBasic[seq]

        # Make both reverse maps
        for seq in (seq2lig):
            lig = seq2lig[seq]
            lig2seq[lig] = seq
            if (seq in seq2ligBasic):
                lig2seqBasic[lig] = seq
        return

    def setupSupers(self):
        supers = {
            u'\u2070' : '0',  # 'SUPERSCRIPT ZERO'
            u'\u00b9' : '1',  # 'SUPERSCRIPT ONE'
            u'\u00b2' : '2',  # 'SUPERSCRIPT TWO'
            u'\u00b3' : '3',  # 'SUPERSCRIPT THREE'
            u'\u2074' : '4',  # 'SUPERSCRIPT FOUR'
            u'\u2075' : '5',  # 'SUPERSCRIPT FIVE'
            u'\u2076' : '6',  # 'SUPERSCRIPT SIX'
            u'\u2077' : '7',  # 'SUPERSCRIPT SEVEN'
            u'\u2078' : '8',  # 'SUPERSCRIPT EIGHT'
            u'\u2079' : '9',  # 'SUPERSCRIPT NINE'
            u'\u2071' : 'i',  # 'SUPERSCRIPT LATIN SMALL LETTER I'
            u'\u207f' : 'n',  # 'SUPERSCRIPT LATIN SMALL LETTER N'
            u'\u207a' : '+',  # 'SUPERSCRIPT PLUS SIGN'
            u'\u207b' : '-',  # 'SUPERSCRIPT MINUS'
            u'\u207c' : '=',  # 'SUPERSCRIPT EQUALS SIGN'
            u'\u207d' : '(',  # 'SUPERSCRIPT LEFT PARENTHESIS'
            u'\u207e' : ')',  # 'SUPERSCRIPT RIGHT PARENTHESIS'
            u'\u0670' : u'\u0627', # 'ARABIC LETTER SUPERSCRIPT ALEF'
            u'\u0711' : u'\u0711', # 'SYRIAC LETTER SUPERSCRIPT ALAPH'
        }
        return(supers)

    def setupSubs(self):
        subs = {
            # Are the rest of the Latin letters hiding somewhere???
            #     Like: bcdfgqwyz ?
            u'\u2090' : 'a',  # 'LATIN SUBSCRIPT SMALL LETTER A'
            u'\u2091' : 'e',  # 'LATIN SUBSCRIPT SMALL LETTER E'
            u'\u2095' : 'h',  # 'LATIN SUBSCRIPT SMALL LETTER H'
            u'\u1d62' : 'i',  # 'LATIN SUBSCRIPT SMALL LETTER I'
            u'\u2c7c' : 'j',  # 'LATIN SUBSCRIPT SMALL LETTER J'
            u'\u2096' : 'k',  # 'LATIN SUBSCRIPT SMALL LETTER K'
            u'\u2097' : 'l',  # 'LATIN SUBSCRIPT SMALL LETTER L'
            u'\u2098' : 'm',  # 'LATIN SUBSCRIPT SMALL LETTER M'
            u'\u2099' : 'n',  # 'LATIN SUBSCRIPT SMALL LETTER N'
            u'\u2092' : 'o',  # 'LATIN SUBSCRIPT SMALL LETTER O'
            u'\u209a' : 'p',  # 'LATIN SUBSCRIPT SMALL LETTER P'
            u'\u1d63' : 'r',  # 'LATIN SUBSCRIPT SMALL LETTER R'
            u'\u209b' : 's',  # 'LATIN SUBSCRIPT SMALL LETTER S'
            u'\u209c' : 't',  # 'LATIN SUBSCRIPT SMALL LETTER T'
            u'\u1d64' : 'u',  # 'LATIN SUBSCRIPT SMALL LETTER U'
            u'\u1d65' : 'v',  # 'LATIN SUBSCRIPT SMALL LETTER V'
            u'\u2093' : 'x',  # 'LATIN SUBSCRIPT SMALL LETTER X'
            u'\u2094' : u'\u0259',  # 'LATIN SUBSCRIPT SMALL LETTER SCHWA'

            u'\u0656' : u'\u0627',  # 'ARABIC SUBSCRIPT ALEF'
            u'\u1d66' : u'\u1d66',  # 'GREEK SUBSCRIPT SMALL LETTER BETA'
            u'\u1d67' : u'\u1d67',  # 'GREEK SUBSCRIPT SMALL LETTER GAMMA'
            u'\u1d68' : u'\u1d68',  # 'GREEK SUBSCRIPT SMALL LETTER RHO'
            u'\u1d69' : u'\u1d69',  # 'GREEK SUBSCRIPT SMALL LETTER PHI'
            u'\u1d6a' : u'\u1d6a',  # 'GREEK SUBSCRIPT SMALL LETTER CHI'

            u'\u2080' : '0',  # 'SUBSCRIPT ZERO'
            u'\u2081' : '1',  # 'SUBSCRIPT ONE'
            u'\u2082' : '2',  # 'SUBSCRIPT TWO'
            u'\u2083' : '3',  # 'SUBSCRIPT THREE'
            u'\u2084' : '4',  # 'SUBSCRIPT FOUR'
            u'\u2085' : '5',  # 'SUBSCRIPT FIVE'
            u'\u2086' : '6',  # 'SUBSCRIPT SIX'
            u'\u2087' : '7',  # 'SUBSCRIPT SEVEN'
            u'\u2088' : '8',  # 'SUBSCRIPT EIGHT'
            u'\u2089' : '9',  # 'SUBSCRIPT NINE'

            u'\u208a' : '+',  # 'SUBSCRIPT PLUS SIGN'
            # u'\u2a27' : '',  # 'PLUS SIGN WITH SUBSCRIPT TWO'
            u'\u208b' : '-',  # 'SUBSCRIPT MINUS'
            u'\u208c' : '=',  # 'SUBSCRIPT EQUALS SIGN'
            u'\u208d' : '(',  # 'SUBSCRIPT LEFT PARENTHESIS'
            u'\u208e' : ')',  # 'SUBSCRIPT RIGHT PARENTHESIS'
        }
        return(subs)

    def setupListOfMathAlphabets(self):
        """List where each math-version of the Latin alphabet occurs, and
        what it is.
        """
        mathAlphabetStarts = {
            # Start      Case     Tag(s)   Description
            0x0249c : [ "LOWER",  'parenthesized'],  # no upper!
            0x024b6 : [ "UPPER",  'circled'],
            0x024d0 : [ "LOWER",  'circled'],
            0x1d400 : [ "UPPER",  'mathematical bold'],
            0x1d41A : [ "LOWER",  'mathematical bold'],
            0x1d434 : [ "LOWER",  'mathematical italic'],
            0x1d44E : [ "UPPER",  'mathematical italic'],
            0x1d468 : [ "UPPER",  'mathematical bold italic'],
            0x1d482 : [ "LOWER",  'mathematical bold italic'],
            0x1d49C : [ "UPPER",  'mathematical script'],
            0x1d4B6 : [ "LOWER",  'mathematical script'],
            0x1d4D0 : [ "UPPER",  'mathematical bold script'],
            0x1d4EA : [ "LOWER",  'mathematical bold script'],
            0x1d504 : [ "UPPER",  'mathematical fraktur'],
            0x1d51E : [ "LOWER",  'mathematical fraktur'],
            0x1d538 : [ "UPPER",  'mathematical double-struck'],
            0x1d552 : [ "LOWER",  'mathematical double-struck'],
            0x1d56C : [ "UPPER",  'mathematical bold fraktur'],
            0x1d586 : [ "LOWER",  'mathematical bold fraktur'],
            0x1d58A : [ "LOWER",  'mathematical sans-serif'],
            0x1d5A0 : [ "UPPER",  'mathematical sans-serif'],
            0x1d5D4 : [ "UPPER",  'mathematical sans-serif bold'],
            0x1d5EE : [ "LOWER",  'mathematical sans-serif bold'],
            0x1d608 : [ "UPPER",  'mathematical sans-serif italic'],
            0x1d622 : [ "LOWER",  'mathematical sans-serif italic'],
            0x1d63C : [ "UPPER",  'mathematical sans-serif bold italic'],
            0x1d656 : [ "LOWER",  'mathematical sans-serif bold italic'],
            0x1d670 : [ "UPPER",  'mathematical monospace'],
            0x1d68a : [ "LOWER",  'mathematical monospace'],
            }
        for k, v in mathAlphabetStarts.items():
            cl = re.sub(r' ', '_', v[1])
            cl = re.sub(r'mathematical', '_M', cl)
            sty = ""
            if (re.search(r'\bbold\b', v[1])):
                sty += "font-weight:bold; "
            if (re.search(r'\bitalic\b', v[1])):
                sty += "font-slant:italic; "
            if (re.search(r'\bsans-serif\b', v[1])):
                sty += "font-family:sans-serif; "
            if (re.search(r'\bscript\b', v[1])):
                sty += "font-family:cursive; "
            if (re.search(r'\bfraktur\b', v[1])):
                sty += "font-family:Fraktur, Gothic, Blackletter; "
            if (re.search(r'\bmonospace\b', v[1])):
                sty += "font-family:monospace; "
            if (re.search(r'\bdouble-struck\b', v[1])):
                sty += "font-family:'Double Struck', 'Double Strike', 'Blackboard bold'; "
            if (re.search(r'\bparenthesized\b', v[1])): form = '(%s)'
            elif (re.search(r'\bparenthesized\b', v[1])): form = '%s'  # ??? FIX
            else: form = '%s'

            st = '<span class="%s" style="%s">' % (cl, sty)
            en = '</span>'
            mathAlphabetStarts[k].append(st + form + en)

        # FIX:
        #     U+ff41	FULLWIDTH LATIN SMALL LETTER A
        #
        #     U+1d6a4:  dotless i, j
        #     U+1d6a8	MATHEMATICAL BOLD CAPITAL ALPHA
        #     U+1d6c2	MATHEMATICAL BOLD SMALL ALPHA
        #     U+1d6e2	MATHEMATICAL ITALIC CAPITAL ALPHA
        #     U+1d6fc	MATHEMATICAL ITALIC SMALL ALPHA
        #     U+1d71c	MATHEMATICAL BOLD ITALIC CAPITAL ALPHA
        #     U+1d736	MATHEMATICAL BOLD ITALIC SMALL ALPHA
        #     U+1d756	MATHEMATICAL SANS-SERIF BOLD CAPITAL ALPHA
        #     U+1d770	MATHEMATICAL SANS-SERIF BOLD SMALL ALPHA
        #     U+1d790	MATHEMATICAL SANS-SERIF BOLD ITALIC CAPITAL ALPHA
        #     U+1d7aa	MATHEMATICAL SANS-SERIF BOLD ITALIC SMALL ALPHA
        #
        #     U+1d7ce	MATHEMATICAL BOLD DIGIT ZERO
        #     U+1d7d8	MATHEMATICAL DOUBLE-STRUCK DIGIT ZERO
        #     U+1d7e2	MATHEMATICAL SANS-SERIF DIGIT ZERO
        #     U+1d7ec	MATHEMATICAL SANS-SERIF BOLD DIGIT ZERO
        #     U+1d7f6	MATHEMATICAL MONOSPACE DIGIT ZERO
        #
        #     U+2460	CIRCLED DIGIT ONE
        #     U+2469	CIRCLED NUMBER TEN
        #     U+24ea	CIRCLED DIGIT ZERO
        #     U+24eb	NEGATIVE CIRCLED NUMBER ELEVEN
        #     U+24f5	DOUBLE CIRCLED DIGIT ONE
        #     U+2776	DINGBAT NEGATIVE CIRCLED DIGIT ONE
        #     U+2780	DINGBAT CIRCLED SANS-SERIF DIGIT ONE
        #     U+278a	DINGBAT NEGATIVE CIRCLED SANS-SERIF DIGIT ONE
        #     U+3248	CIRCLED NUMBER TEN ON BLACK SQUARE
        #     U+3251	CIRCLED NUMBER TWENTY ONE

        return



    ###########################################################################
    # Experimental
    #     ("WITH" may be a bit too lenient)
    #
    def simplifyUName(self, c, name):
        """Shorten up a formal Unicode character name for display.
        """
        num = unicodedata.numeric(c,12345)
        if (num != 12345):
            return(str(num))
        if (re.search(r'\bSINGLE .* QUOTATION MARK',name)):
            return("APOSTROPHE")
        if (re.search(r'\bDOUBLE .* QUOTATION MARK',name)):
            return("DOUBLE QUOTATION MARK")
        if (re.search(r'\bSYMBOL QUOTE',name)):
            return("DOUBLE QUOTATION MARK")
        if (re.search(r'\bSPACE$',name)):
            return("SPACE")
        if (re.search(r'\b(DASH|HYPHEN)\b',name)):
            return("HYPHEN")

        # Strip out keywords that seem reliably to indicate variants.
        # Also?: COMBINING|MODIFIER LETTER|SUBSCRIPT|SUPERSCRIPT|TURNED
        # "ABOVE"...? "AND JOINED WITH..."? n POINTED DOUBLE TRIPLE
        # vowel sign vs. letter? TAG?? SURPALINEAR SUBLINEAR SLANTED ROTATED
        # symbol for (controls), PRESENTATION FORM FOR
        # BLACK WHITE BLAC-FEATHERED
        x = (r'(MONOSPACE|BOLD|ITALIC|SCRIPT|FRAKTUR|DOUBLE-STRUCK' +
             r'|BLACK|FLATTENED|OUTLINED|OCR|HEAVY' +
             r'|SANS-SERIF|PARENTHESIZED|' +
             r'|NEGATIVE CIRCLED|DOUBLE CIRCLED|CIRCLED' +
             r'|MATHEMATICAL' +
             r'|FULLWIDTH|HALFWIDTH-LETTER|SMALL|MEDIUM' +
             r')\s+')
        sname = re.sub(x, '', name)
        x = (r'(INITIAL|MEDIAL|FINAL)\s*FORM', '', sname)
        x = (r'\s+WITH\s.*$', '', sname)
        x = (r'\s+SMALL\s+CAPITAL\s.*$', " SMALLCAP ", sname)
        return(sname)

# End of SimplifyUnicodePackage



###############################################################################
###############################################################################
#
pod="""

=pod

=head1 Usage

  from SimplifyUnicode import SimplifyUnicode
  ...
  s = SimplifyUnicode()
  s.setOptions("dashes", 1)
  myString = s.simplify(myString)

This module maps many classes of Unicode characters to more basic ones.
For example, it can strip accents; normalize spaces, dashes, or quotes;
fiddle with ligatures, math characters; and so on.

B<Note>: This is documentation for the library. There is also a shell
command C<simplifyUnicode>, which exposes the options (see under
L<setOption>(), below), and runs files through as needed.

(Python version)

=head2 What to do with I<accents>, I<ligatures>, I<maths>, I<super>, I<sub>.

Most options are simply left off or turned on. However, several options
provide more flexibility for how the relevant characters are treated:

=over

=item I<unchanged> -- leave as-is.

=item I<split> -- expand the character to its separate component parts
(not generally applicable to I<--maths>)

=item I<join> -- combine when possible -- for example, turn 'fi' into
a ligature, 'a' plus acute accent to the combined character, etc.

=item I<unaccent> -- remove any accent or special property, making the
character "plain" (usually it becomes a single ASCII character).

=item I<space> -- replace the affected character by a space.

=item I<delete> -- delete  the affected character entirely.

=item I<markup> -- where possible, replace the special property of an
affected character by markup. For example, a mathematical bold "G" will
be turned into a regular "G" inside <b>...</b>.

=back


=head1 Methods

=over

=item * B<__init__({options})>

The constructor. Any of the options listed below under I<setOption>(), can
also be set via the constructor.

=item * b<string = su.simplify(string)>

Simplifies the Unicode string according to the current options.

=item * B<setOption(name,value)>

Use this method to configure just what kinds of characters will be
normalized:

=over

=item * B<accents> I<disp>

Handle accents and other diacritics according to I<disp> (see above).

=item * B<bQuotes>

Normalize backquote to apostrophe.

=item * B<dashes>

Turn em dash, en dash, hyphen, etc. to hyphen.

=item * B<dquotes>

Turn many kinds of double quotes to double-quote.

=item * B<entities>

Turn XML numeric and predefined references
into literal Unicode characters.

=item * B<halfWidths>

Normalize halfwidth characters to normal width.

=item * B<ligatureDomain>

Whether I<ligatures> does only the basics, or all.

=item * B<ligatures>

Turn ligatures to some form:
join, split, deleted, space, unchanged.

=item * B<maths>

Normalize alternate math Latin alphabets to ASCII.

=item * B<numbers>

Normalize alternate forms of numbers to ASCII.

=item * B<quotes>

Shorthand for I<bquotes squotes dquotes>.

=item * B<spaces>

Normalize various whitespace chars to ASCII space.

=item * B<squotes>

Turn many kinds of single quotes to apostrophe.

=item * B<uriEscapes>

Resolve URI %-escapes.

=back

=back



=head1 Related Commands

C<simplifyUnicode> is a command-line interface to this package.

Lists of characters in certain classes (ligatures, dashes, etc.) can be
obtained, including in the form of Perl or other code, with C<ord>.
For example:

    ord --listFormat python --find 'ligature'


=head1 Known bugs and Limitations

Does not include Arabic ligatures, because there are so many.

Does not include alternate mathematical Greek alphabets.


=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see http://www.derose.net/steve/utilities/.

=cut
"""
