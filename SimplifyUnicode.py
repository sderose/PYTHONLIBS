#!/usr/bin/env python3
#
# SimplifyUnicode: Compatibility mapping on steroids.
# 2010-11-19ff: Written by Steven J. DeRose (in Perl)
#
import re
import unicodedata

__metadata__ = {
    "title"        : "SimplifyUnicode",
    "description"  : "Compatibility mapping on steroids.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2010-11-19ff",
    "modified"     : "2020-09-23",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Usage=

  from SimplifyUnicode import SimplifyUnicode
  ...
  s = SimplifyUnicode()
  s.setOptions("dashes", 1)
  myString = s.simplify(myString)

This module maps many classes of Unicode characters to more basic ones.
For example, it can strip accents; normalize spaces, dashes, or quotes;
fiddle with ligatures, math characters; and so on.

'''Note''': This is documentation for the library. There is also a shell
command `simplifyUnicode`, which exposes the options (see under
[setOption](), below), and runs files through as needed.

(Python version)

==What to do with ''accents'', ''ligatures'', ''maths'', ''super'', ''sub''.==

Most options are simply left off or turned on. However, several options
provide more flexibility for how the relevant characters are treated:

* ''unchanged'' -- leave as-is.

* ''split'' -- expand the character to its separate component parts
(not generally applicable to ''--maths'')

* ''join'' -- combine when possible -- for example, turn 'fi' into
a ligature, 'a' plus acute accent to the combined character, etc.

* ''unaccent'' -- remove any accent or special property, making the
character "plain" (usually it becomes a single ASCII character).

* ''space'' -- replace the affected character by a space.

* ''delete'' -- delete  the affected character entirely.

* ''markup'' -- where possible, replace the special property of an
affected character by markup. For example, a mathematical bold "G" will
be turned into a regular "G" inside <b>...</b>.


=Methods=

* '''__init__({options})'''
The constructor. Any of the options listed below under ''setOption''(), can
also be set via the constructor.

* '''string = su.simplify(string)'''
Simplifies the Unicode string according to the current options.

* '''setOption(name,value)'''
Use this method to configure just what kinds of characters will be
normalized:

** '''accents''' ''disp''

Handle accents and other diacritics according to ''disp'' (see above).

** '''bQuotes'''
Normalize backquote to apostrophe.

** '''dashes'''
Turn em dash, en dash, hyphen, etc. to hyphen.

** '''dquotes'''
Turn many kinds of double quotes to double-quote.

** '''entities'''
Turn XML numeric and predefined references
into literal Unicode characters.

** '''halfWidths'''
Normalize halfwidth characters to normal width.

** '''ligatureDomain'''
Whether ''ligatures'' does only the basics, or all.

** '''ligatures'''
Turn ligatures to some form:
join, split, deleted, space, unchanged.

** '''maths'''
Normalize alternate math Latin alphabets to ASCII.

** '''numbers'''
Normalize alternate forms of numbers to ASCII.

** '''quotes'''
Shorthand for ''bquotes squotes dquotes''.

** '''spaces'''
Normalize various whitespace chars to ASCII space.

** '''squotes'''
Turn many kinds of single quotes to apostrophe.

** '''uriEscapes'''
Resolve URI %-escapes.


=Related Commands=

`simplifyUnicode` is a command-line interface to this package.

Lists of characters in certain classes (ligatures, dashes, etc.) can be
obtained, including in the form of Perl or other code, with `ord`.
For example:

    ord --listFormat python --find 'ligature'


=Known bugs and Limitations=

Does not include Arabic ligatures, because there are so many.

Does not include alternate mathematical Greek alphabets.


=To do=

* Add a test driver/standalone.
* ?? Generalize to be able to operate on any \\p{name} classes??
* Deal with ligature/accent interaction (combining long s).
* Add stripXML, nine, num, ignorecase, degeminate, punct?
* Perhaps just work off of actual long names? "LATIN LETTER A" -> "A"...

==Possible additions==

* old italic, gothic, etc. U+10300?
* roman numerals, enclosed alphanumerics
* vertical forms U+fe00
* Greek and Cyrillic and Hebrew math variants?
* ellipsis, punc ligatures U+203c...
* sup/sub U+2070
* Halfwidth/fullwidth U+ff00
* Non-Latin ligatures.
* supplemental punct
* Arrows? U+2190, 2799, 27f0, 2900, 2b00
* letterlike symbols U+2100, fractions,
* braille U+2800
* high surrogates U+d800, low surrogates U+dc00

==Integrate into==

* findKeyWords
* normalizeXML
* tuples
* vocab


=History=

  2010-11-19ff: Written by Steven J. DeRose (in Perl)
  ...
  2012-01-10 sjd: Port to Python.


=Ownership=

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0/].

For the most recent version, see [http://www.derose.net/steve/utilities/].

=Options=
"""


###############################################################################
#
class SimplifyUnicode:
    dispChoices = [  # for accents, ligatures, maths
        'unchanged', 'split', 'join', 'unaccent', 'space', 'delete', 'markup',
    ]

    def __init__(self, **kwargs):
        self.version       = "2015-08-15"
        self.options = {
            "entities"       : 0,
            "uriEscapes"     : 0,

            "dashes"         : 0,
            "keepMdash"      : 0,
            "halfWidths"     : 0,
            "ligaturesAll"   : 0,
            "spaces"         : 0,

            "bQuotes"        : 0,
            "dQuotes"        : 0,
            "sQuotes"        : 0,
            "quotes"         : 0,

            "accents"        : "unchanged",
            "ligatures"      : "unchanged",
            "maths"          : "unchanged",
            "numbers"        : "unchanged",
            "supers"         : "unchanged",
            "subs"           : "unchanged",
        }

        if (kwargs):
            for k, v in kwargs.items():
                self.setOption(k,v)

        # internal data
        self.dQuoteChars    = self.setupDQuotes()     # Strings
        self.sQuoteChars    = self.setupSQuotes()
        self.spaceChars     = self.setupSpaces()
        self.dashChars      = self.setupDashes()

        # TODO: Switch this over to much more recent mathAlphanumerics.py.
        self.mathStarts     = self.setupListOfMathAlphabets()  # HashRefs

        self.lig2seqBasic   = None
        self.seq2ligBasic   = None
        self.lig2seq        = None
        self.seq2lig        = None
        self.setupLigatures()

        self.supers         = self.setupSupers()
        return(None)


    #########################################################################
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
    def setOption(self, oname, v):
        if (not oname or oname not in self.options):
            raise ValueError("Bad option name passed to simplifyUicode.setOption.")
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

    def getOption(self, oname):
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
                buf += chr(n - 0xFF01 + 0x21)
            elif (0 and n>=0xFF71 and n<=0xFF9F):  # halfwidth Katakana
                buf += + chr(n - 0xFF71 + 0x30A1)
            else:
                buf += + chr(n)
        return(buf)


    ###########################################################################
    #
    def handle_Entities(self, rec):
        rec = re.sub(r'&#x([a-f0-9]+);',
            lambda x: chr(int(x.group[1],16)), rec)
        rec = re.sub(r'&#([0-9]+);',
            lambda x: chr(int(x.group[1],10)), rec)
        rec = re.sub(r'&lt;'   , "<",  rec)
        rec = re.sub(r'&gt;'   , ">",  rec)
        rec = re.sub(r'&apos;' , "'",  rec)
        rec = re.sub(r'&quot;' , "\"", rec)
        #rec = re.sub(r'&nbsp;' , "/ ", rec)
        rec = re.sub(r'&amp;'  , "&",  rec)
        return(rec)

    def handle_UriEscapes(self, rec):
        rec = re.sub(r'([a-fA-F0-9][a-fA-F0-9])',
            lambda x: chr(int(x.group[1],16)), rec)
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

    def handle_Maths(self, rec):
        """This is for mathematical variants on A-Z, not math symbols in general.
        """
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
        for mathRange in (self.mathStarts):
            if (n<mathRange or n>=mathRange+26): continue
            diff = n - mathRange
            theType = self.mathStarts[mathRange]
            if (theType == "UPPER"):
                return("ABCDEFGHIJKLMNOPQRSTUVWXYZ",diff[1:])
            elif (theType == "LOWER"):
                return("abcdefghijklmnopqrstuvwxyz",diff[1:])
            else:
                print("Bad math alphabet type '%s'." % (theType))
                exit(0)
        return(None)


    ###########################################################################
    # Following setupXxx() methods create lists of characters to map.
    #
    def setupDashes(self):
        dashChars = (
            # Leave out regular hyphen so doesn't mess up regex, and since it's
            # what we normalize *to*.
            #
            "\u00ad" + # soft hyphen
            "\u058a" + # armenian hyphen
            "\u1806" + # mongolian todo soft hyphen
            "\u1b60" + # balinese pameneng (line-breaking hyphen)
            "\u2010" + # 008208) + hyphen) +        '-',
            "\u2011" + # non-breaking hyphen,
            "\u2012" + # figure dash
            "\u2013" + # 008211) + ndash,         '-',
            "\u2014" + # 008212, mdash,         '--',
            "\u2015" + # 008213, horbar,        '--',
            "\u2027" + # hyphenation point
            "\u2043" + # hyphen bullet
            "\u2053" + # swung dash
            #"\u21E0" + # LEFTWARDS DASHED ARROW
            #"\u21E1" + # UPWARDS DASHED ARROW
            #"\u21E2" + # RIGHTWARDS DASHED ARROW
            #"\u21E3" + # DOWNWARDS DASHED ARROW
            "\u229d" + # circled dash
            "\u2448" + # ocr dash

            # Box-drawing dashes
            #
            #"\u2504" + # ... LIGHT TRIPLE DASH HORIZONTAL
            #"\u2505" + # ... HEAVY TRIPLE DASH HORIZONTAL
            #"\u2508" + # ... LIGHT QUADRUPLE DASH HORIZONTAL
            #"\u2509" + # ... HEAVY QUADRUPLE DASH HORIZONTAL
            #"\u254C" + # ... LIGHT DOUBLE DASH HORIZONTAL
            #"\u254D" + # ... HEAVY DOUBLE DASH HORIZONTAL

            "\u2e17" + # double oblique hyphen
            "\u2E1A" + # HYPHEN WITH DIAERESIS
            "\u301c" + # wave dash
            "\u3030" + # wavy dash
            "\u30a0" + # katakana-hiragana double hyphen
            "\uFE49" + # DASHED OVERLINE
            "\uFE4D" + # DASHED LOW LINE
            "\uFE58" + # small em dash
            "\ufe63" + # small hyphen-minus
            "\uff0d" + # fullwidth hyphen-minus
            "")
        return(dashChars)

    def setupDQuotes(self):
        dQuoteChars = (
            "\u00AB" +   # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK *
            "\u00BB" +   # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK *
            "\u201C" +   # LEFT DOUBLE QUOTATION MARK
            "\u201D" +   # RIGHT DOUBLE QUOTATION MARK
            "\u201E" +   # DOUBLE LOW-9 QUOTATION MARK
            "\u201F" +   # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
            "\u2358" +   # APL FUNCTIONAL SYMBOL QUOTE UNDERBAR
            "\u235E" +   # APL FUNCTIONAL SYMBOL QUOTE QUAD
            "\u275D" +   # HEAVY DOUBLE TURNED COMMA QUOTATION MARK ORNAMENT
            "\u275E" +   # HEAVY DOUBLE COMMA QUOTATION MARK ORNAMENT
            "\u301D" +   # REVERSED DOUBLE PRIME QUOTATION MARK
            "\u301E" +   # DOUBLE PRIME QUOTATION MARK
            "\u301F" +   # LOW DOUBLE PRIME QUOTATION MARK
        "")
        return(dQuoteChars)

    def setupSQuotes(self):
        sQuoteChars = (
            "\u2018" +   # LEFT SINGLE QUOTATION MARK
            "\u2019" +   # RIGHT SINGLE QUOTATION MARK
            "\u201A" +   # SINGLE LOW-9 QUOTATION MARK
            "\u201B" +   # SINGLE HIGH-REVERSED-9 QUOTATION MARK
            "\u2039" +   # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
            "\u203A" +   # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
            "\u275B" +   # HEAVY SINGLE TURNED COMMA QUOTATION MARK ORNAMENT
            "\u275C" +   # HEAVY SINGLE COMMA QUOTATION MARK ORNAMENT
            "\u276E" +   # HEAVY LEFT-POINTING ANGLE QUOTATION MARK ORNAMENT
            "\u276F" +   # HEAVY RIGHT-POINTING ANGLE QUOTATION MARK ORNAMENT
        "")
        return(sQuoteChars)

    def setupSpaces(self):
        spaceChars = (
            "\u0009" +    # TAB
            "\u000A" +    # LINE FEED
            "\u000B" +    # VERTICAL TAB
            "\u000C" +    # FORM FEED
            "\u000D" +    # CARRIAGE RETURN
            "\u0020" +    # SPACE
            "\u00A0" +    # NO-BREAK SPACE

            "\u1680" +    # OGHAM SPACE MARK

            "\u2002" +    # EN SPACE
            "\u2003" +    # EM SPACE
            "\u2004" +    # THREE-PER-EM SPACE
            "\u2005" +    # FOUR-PER-EM SPACE
            "\u2006" +    # SIX-PER-EM SPACE
            "\u2007" +    # FIGURE SPACE
            "\u2008" +    # PUNCTUATION SPACE
            "\u2009" +    # THIN SPACE
            "\u200A" +    # HAIR SPACE
            "\u200B" +    # ZERO WIDTH SPACE
            "\u202F" +    # NARROW NO-BREAK SPACE
            "\u205F" +    # MEDIUM MATHEMATICAL SPACE

            "\u2409" +    # SYMBOL FOR HORIZONTAL TABULATION
            "\u240B" +    # SYMBOL FOR VERTICAL TABULATION
            "\u2420" +    # SYMBOL FOR SPACE

            "\u3000" +    # IDEOGRAPHIC SPACE
            "\u303F" +    # IDEOGRAPHIC HALF FILL SPACE

            "\uFEFF" +    # ZERO WIDTH NO-BREAK SPACE (= byte-order mark)
        "")
        return(spaceChars)

    # Arabic ligatures are not here yet, because there are hundreds of them.
    #
    def setupLigatures(self):
        self.seq2ligBasic = {
            "\ufb00" : 'ff',  # 'LATIN SMALL LIGATURE FF'
            "\ufb01" : 'fi',  # 'LATIN SMALL LIGATURE FI'
            "\ufb02" : 'fl',  # 'LATIN SMALL LIGATURE FL'
            "\ufb03" : 'ffi', # 'LATIN SMALL LIGATURE FFI'
            "\ufb04" : 'ffl', # 'LATIN SMALL LIGATURE FFL'
        }

        self.seq2lig = {
            # Latin
            "\u0132" : 'IJ',  # 'LATIN CAPITAL LIGATURE IJ'
            "\u0133" : 'ij',  # 'LATIN SMALL LIGATURE IJ'
            "\u0152" : 'OE',  # 'LATIN CAPITAL LIGATURE OE'
            "\u0153" : 'oe',  # 'LATIN SMALL LIGATURE OE'
            "\ufb00" : 'ff',  # 'LATIN SMALL LIGATURE FF'
            "\ufb01" : 'fi',  # 'LATIN SMALL LIGATURE FI'
            "\ufb02" : 'fl',  # 'LATIN SMALL LIGATURE FL'
            "\ufb03" : 'ffi', # 'LATIN SMALL LIGATURE FFI'
            "\ufb04" : 'ffl', # 'LATIN SMALL LIGATURE FFL'
            "\ufb05" : 'st',  # 'LATIN SMALL LIGATURE LONG S T'
            "\ufb06" : 'st',  # 'LATIN SMALL LIGATURE ST'

            # Cyrillic
            "\u04a4" : "\u041d"+"\u0413",  # 'CAPITAL EN GHE'
            "\u04a5" : "\u043d"+"\u0433",  # 'SMALL EN GHE'
            "\u04b4" : "\u0422"+"\u0426",  # 'CAPITAL TE TSE'
            "\u04b5" : "\u0442"+"\u0446",  # 'SMALL TE TSE'
            "\u04d4" : "\u0410"+"\u0415",  # 'CAPITAL A IE'
            "\u04d5" : "\u0430"+"\u0435",  # 'SMALL A IE'

            # Other ### FIX
            "\u0587" : '',  # 'ARMENIAN SMALL LIGATURE ECH YIWN'
            "\u05f0" : '',  # 'HEBREW LIGATURE YIDDISH DOUBLE VAV'
            "\u05f1" : '',  # 'HEBREW LIGATURE YIDDISH VAV YOD'
            "\u05f2" : '',  # 'HEBREW LIGATURE YIDDISH DOUBLE YOD'
            "\ua7f9" : '',  # 'MODIFIER LETTER SMALL LIGATURE OE'
            "\ufb13" : '',  # 'ARMENIAN SMALL LIGATURE MEN NOW'
            "\ufb14" : '',  # 'ARMENIAN SMALL LIGATURE MEN ECH'
            "\ufb15" : '',  # 'ARMENIAN SMALL LIGATURE MEN INI'
            "\ufb16" : '',  # 'ARMENIAN SMALL LIGATURE VEW NOW'
            "\ufb17" : '',  # 'ARMENIAN SMALL LIGATURE MEN XEH'
            "\ufb1f" : '',  # 'HEBREW LIGATURE YIDDISH YOD YOD PATAH'
            "\ufb4f" : '',  # 'HEBREW LIGATURE ALEF LAMED'
            "\ufe20" : '',  # 'COMBINING LIGATURE LEFT HALF'
            "\ufe21" : '',  # 'COMBINING LIGATURE RIGHT HALF'
        }

        self.lig2seqBasic = {}
        self.lig2seq = {}

        # Add the basic to the main map
        for seq in (self.seq2ligBasic):
            self.seq2lig[seq] = self.seq2ligBasic[seq]

        # Make both reverse maps
        for seq in (self.seq2lig):
            lig = self.seq2lig[seq]
            self.lig2seq[lig] = seq
            if (seq in self.seq2ligBasic):
                self.lig2seqBasic[lig] = seq
        return

    def setupSupers(self):
        supers = {
            "\u2070" : '0',  # 'SUPERSCRIPT ZERO'
            "\u00b9" : '1',  # 'SUPERSCRIPT ONE'
            "\u00b2" : '2',  # 'SUPERSCRIPT TWO'
            "\u00b3" : '3',  # 'SUPERSCRIPT THREE'
            "\u2074" : '4',  # 'SUPERSCRIPT FOUR'
            "\u2075" : '5',  # 'SUPERSCRIPT FIVE'
            "\u2076" : '6',  # 'SUPERSCRIPT SIX'
            "\u2077" : '7',  # 'SUPERSCRIPT SEVEN'
            "\u2078" : '8',  # 'SUPERSCRIPT EIGHT'
            "\u2079" : '9',  # 'SUPERSCRIPT NINE'
            "\u2071" : 'i',  # 'SUPERSCRIPT LATIN SMALL LETTER I'
            "\u207f" : 'n',  # 'SUPERSCRIPT LATIN SMALL LETTER N'
            "\u207a" : '+',  # 'SUPERSCRIPT PLUS SIGN'
            "\u207b" : '-',  # 'SUPERSCRIPT MINUS'
            "\u207c" : '=',  # 'SUPERSCRIPT EQUALS SIGN'
            "\u207d" : '(',  # 'SUPERSCRIPT LEFT PARENTHESIS'
            "\u207e" : ')',  # 'SUPERSCRIPT RIGHT PARENTHESIS'
            "\u0670" : "\u0627", # 'ARABIC LETTER SUPERSCRIPT ALEF'
            "\u0711" : "\u0711", # 'SYRIAC LETTER SUPERSCRIPT ALAPH'
        }
        return(supers)

    def setupSubs(self):
        subs = {
            # Are the rest of the Latin letters hiding somewhere???
            #     Like: bcdfgqwyz ?
            "\u2090" : 'a',  # 'LATIN SUBSCRIPT SMALL LETTER A'
            "\u2091" : 'e',  # 'LATIN SUBSCRIPT SMALL LETTER E'
            "\u2095" : 'h',  # 'LATIN SUBSCRIPT SMALL LETTER H'
            "\u1d62" : 'i',  # 'LATIN SUBSCRIPT SMALL LETTER I'
            "\u2c7c" : 'j',  # 'LATIN SUBSCRIPT SMALL LETTER J'
            "\u2096" : 'k',  # 'LATIN SUBSCRIPT SMALL LETTER K'
            "\u2097" : 'l',  # 'LATIN SUBSCRIPT SMALL LETTER L'
            "\u2098" : 'm',  # 'LATIN SUBSCRIPT SMALL LETTER M'
            "\u2099" : 'n',  # 'LATIN SUBSCRIPT SMALL LETTER N'
            "\u2092" : 'o',  # 'LATIN SUBSCRIPT SMALL LETTER O'
            "\u209a" : 'p',  # 'LATIN SUBSCRIPT SMALL LETTER P'
            "\u1d63" : 'r',  # 'LATIN SUBSCRIPT SMALL LETTER R'
            "\u209b" : 's',  # 'LATIN SUBSCRIPT SMALL LETTER S'
            "\u209c" : 't',  # 'LATIN SUBSCRIPT SMALL LETTER T'
            "\u1d64" : 'u',  # "LATIN SUBSCRIPT SMALL LETTER U"
            "\u1d65" : 'v',  # 'LATIN SUBSCRIPT SMALL LETTER V'
            "\u2093" : 'x',  # 'LATIN SUBSCRIPT SMALL LETTER X'
            "\u2094" : "\u0259",  # 'LATIN SUBSCRIPT SMALL LETTER SCHWA'

            "\u0656" : "\u0627",  # 'ARABIC SUBSCRIPT ALEF'
            "\u1d66" : "\u1d66",  # 'GREEK SUBSCRIPT SMALL LETTER BETA'
            "\u1d67" : "\u1d67",  # 'GREEK SUBSCRIPT SMALL LETTER GAMMA'
            "\u1d68" : "\u1d68",  # 'GREEK SUBSCRIPT SMALL LETTER RHO'
            "\u1d69" : "\u1d69",  # 'GREEK SUBSCRIPT SMALL LETTER PHI'
            "\u1d6a" : "\u1d6a",  # 'GREEK SUBSCRIPT SMALL LETTER CHI'

            "\u2080" : '0',  # 'SUBSCRIPT ZERO'
            "\u2081" : '1',  # 'SUBSCRIPT ONE'
            "\u2082" : '2',  # 'SUBSCRIPT TWO'
            "\u2083" : '3',  # 'SUBSCRIPT THREE'
            "\u2084" : '4',  # 'SUBSCRIPT FOUR'
            "\u2085" : '5',  # 'SUBSCRIPT FIVE'
            "\u2086" : '6',  # 'SUBSCRIPT SIX'
            "\u2087" : '7',  # 'SUBSCRIPT SEVEN'
            "\u2088" : '8',  # 'SUBSCRIPT EIGHT'
            "\u2089" : '9',  # 'SUBSCRIPT NINE'

            "\u208a" : '+',  # 'SUBSCRIPT PLUS SIGN'
            # "\u2a27" : '',  # 'PLUS SIGN WITH SUBSCRIPT TWO'
            "\u208b" : '-',  # 'SUBSCRIPT MINUS'
            "\u208c" : '=',  # 'SUBSCRIPT EQUALS SIGN'
            "\u208d" : '(',  # 'SUBSCRIPT LEFT PARENTHESIS'
            "\u208e" : ')',  # 'SUBSCRIPT RIGHT PARENTHESIS'
        }
        return(subs)

    def setupListOfMathAlphabets(self):
        """List where each math-version of the Latin alphabet occurs, and
        what it is.
        """
        mathStarts = {
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
        for k, v in mathStarts.items():
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
            mathStarts[k].append(st + form + en)

        # FIX:
        #     U+ff41    FULLWIDTH LATIN SMALL LETTER A
        #
        #     U+1d6a4:  dotless i, j
        #     U+1d6a8   MATHEMATICAL BOLD CAPITAL ALPHA
        #     U+1d6c2   MATHEMATICAL BOLD SMALL ALPHA
        #     U+1d6e2   MATHEMATICAL ITALIC CAPITAL ALPHA
        #     U+1d6fc   MATHEMATICAL ITALIC SMALL ALPHA
        #     U+1d71c   MATHEMATICAL BOLD ITALIC CAPITAL ALPHA
        #     U+1d736   MATHEMATICAL BOLD ITALIC SMALL ALPHA
        #     U+1d756   MATHEMATICAL SANS-SERIF BOLD CAPITAL ALPHA
        #     U+1d770   MATHEMATICAL SANS-SERIF BOLD SMALL ALPHA
        #     U+1d790   MATHEMATICAL SANS-SERIF BOLD ITALIC CAPITAL ALPHA
        #     U+1d7aa   MATHEMATICAL SANS-SERIF BOLD ITALIC SMALL ALPHA
        #
        #     U+1d7ce   MATHEMATICAL BOLD DIGIT ZERO
        #     U+1d7d8   MATHEMATICAL DOUBLE-STRUCK DIGIT ZERO
        #     U+1d7e2   MATHEMATICAL SANS-SERIF DIGIT ZERO
        #     U+1d7ec   MATHEMATICAL SANS-SERIF BOLD DIGIT ZERO
        #     U+1d7f6   MATHEMATICAL MONOSPACE DIGIT ZERO
        #
        #     U+2460    CIRCLED DIGIT ONE
        #     U+2469    CIRCLED NUMBER TEN
        #     U+24ea    CIRCLED DIGIT ZERO
        #     U+24eb    NEGATIVE CIRCLED NUMBER ELEVEN
        #     U+24f5    DOUBLE CIRCLED DIGIT ONE
        #     U+2776    DINGBAT NEGATIVE CIRCLED DIGIT ONE
        #     U+2780    DINGBAT CIRCLED SANS-SERIF DIGIT ONE
        #     U+278a    DINGBAT NEGATIVE CIRCLED SANS-SERIF DIGIT ONE
        #     U+3248    CIRCLED NUMBER TEN ON BLACK SQUARE
        #     U+3251    CIRCLED NUMBER TWENTY ONE

        return mathStarts


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

