#!/usr/bin/env python3
#
# Tokenizer.pm: Port of my Perl tokenizer.
# 2012-08-22: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import regex as re  # Adds support for \p{}. See https://pypi.org/project/regex/
import codecs
import unicodedata
import urllib
import html
from html.parser import HTMLParser

def unicode(s, encoding="utf-8", errors="strict"):
    if (not isinstance(s, str)): return str(s, encoding, errors)
    return s

__metadata__ = {
    "title"        : "Tokenizer",
    "description"  : "An NLP tokenizer that knows about Unicode.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2012-08-22",
    "modified"     : "2022-03-11",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Divide strings into tokens, trying to be sensible about Unicode issues,
complicated numbers, dates and times, DNA, URLs, emails, contractions, etc.

This is a natural-language tokenizer, intended as a front-end to NLP
software, particularly lexico-statistical calculators. It's pretty
knowledgeable about Unicode, especially characters used in quality typography.
It can also be used to normalize text without tokenizing, or
as a preprocessor for more extensive NLP stacks.

If you run this package directly from the command line, it will tokenize
and display the specified input file(s) or STDIN. If you specify "*" instead
of a filename, it will use some text of its own as a test.

There are several tokenizers included:

* The ''SimpleTokenizer'' class is quick and should be adequate for
many uses. It drops soft/optional hyphens, normalizes Unicode (accents,
ligatures, etc.), then applyies a few regexes to insert
extra spaces (such as before the apostrophe of contractions, around emdashes, 
after opening punctuation, etc.), and then splits on space-runs.
It offers an option to use ''TokensEN.py'' for contractions, but
otherwise applies a simplified rule for them.

This is the easiest to use, for example:

  from Tokenizer import SimpleTokenizer
  myTok = SimpleTokenizer()
  for rec in fh.readline():
      tokens = myTok.tokenize(rec)
      print("\n".join(tokens))

It provides a few keyword options on the constructor:

**'''normalize''' -- What Unicode normalization to apply.

Default: 'NFKD' (others are 'NFC', 'NFD', and 'NFKC').

**'''breakHyphens''' -- Whether to split hyphenated words. Default: False.

**'''fancyContractions''' -- Whether to use the ''TokensEN'' package
to handle contractions, or just some local regexes. Default: False.

**'''verbose''' -- Whether to print steps of progress. Default: False.

* ''NLTKTokenizerPlus'' applies the NLTK tokenizer, then
makes a few adjustments. Usage is the same as just shown,
just substitute "NLTKTokenizerPlus".

* ''HeavyTokenizer'' provides a variety of useful but complex steps, and
can do a lot of manipulation to help when gathering lexicostatistics. 
Usage is the same as just shown, just substitute "HeavyTokenizer". However, you'll
probably want to use ''setOption''() to pick exactly what behaviors you want.

==Details on the HeavyTokenizer==

* Expand format-specific special characters like &lt; %42 \\uFFFF

* Normalize the character inventory (accents, ligatures, quotes,
dashes (soft, em, etc.), spaces (non-breaking, m-width, etc.), etc.

* Shorten long repetition sequences like 'argggggg'

* Deal with contractions (this part is English-only so far)

* Identify many specific types of non-word tokens (numbers, date, URIs, DNA, emoticons,...)

* Filter out or merge particular tokens (for example, sometimes you
might want only alphabetic tokens; or no punctuation; or want a "cover"
token such as "99" to represent ''all'' numbers; etc.) This is especially
useful when developing lexica from corpora.

* Generate the actual tokenized result.

HeavyTokenizer focuses on handling complex Unicode issues well (other than
word-division in space-less orthographies, which it doesn't attempt).

Some of the features in more detail:

* Character represented in special ways, such as %xx codes used in URIs,
character references like &quot; or &#65; in HTML and XML, and so on. These are
very often found in lexical databases, and are often handled incorrectly.

* Less-common characters such as ligatures, accents,
non-Latin digits, fractions, hyphens and dashes, quotes, and spaces, 
presentation variants, footnote markers, angstrom vs. a-with-ring, etc.

Very many of the NLP systems I've examined fail on quite common cases such as
hard spaces, ligatures, curly quotes, soft hyphens, and em-dashes.
This is intended not to.

* Many kinds of non-word tokens, such as URIs, Twitter hashtags and userids,
and jargon; numbers, dates, times, email addresses, etc. Imho, NLP systems
shouldn't break URIs at every "/" and then try to POS-tag the directory names.

* Contemporary conventions such as emphasis via special puntuations
(*word*), or via repeating letters (aaaarrrrrggggghhhhhh, hahahaha).

* Special cases such as contractions and possessives
(with and without explicit apostrophes), hyphenated words
(not the same thing as em-dash-separated clauses), etc.

* When collecting or measuring vocabulary,
options to filter out unwanted tokens are very useful.
For example, the non-word types already mentioned are important for some purposes, but
not for others. Words already listed in a given dictionary(s) can be discarded. Tokens
in all lower, all upper, title, camel, or other case patterns; numers
tokens containing special characters, long or short tokens, etc. There are many filtering
options, so you can easily winnow a list down to just what you want.

* Numerics are, I think, handled better than is typical. You don't need integers listed
in a lexicon, or to miss ones that aren't. Likewise for floating-point numbers,
currently, etc. Also decades such as 50's 60s '70s and '80's should just work.


=Usage=

==Example==

  from Tokenizer import HeavyTokenizer
  myTok = HeavyTokenizer("characters")
  myTok.setOption("Uppercase_Letter", "lower")
  for rec in fh.readline():
      tokens = myTok.tokenize(rec)
      for token in (tokens):
          counts[token] += 1

There are several steps to the process of tokenizing.
They are described in order below, with the options applicable to each.

Option names appear in '''BOLD''', and values in ''ITALIC'' below.
The type of value expected is shown in (parentheses): either (boolean), (int),
or (disp), unless otherwise described.


==1: Expand escaped characters==

These options all begin with "X_" and all take (boolean) values,
for whether to expand them to a literal character.

* '''X_BACKSLASH''' -- A lot of cases are covered.

* '''X_URI''' -- %-escapes as used in URIs.
Not to be confused with the '''T_URI''' option for tokenizing (see below).

* '''X_ENTITY''' -- Covers HTML and XML named entities and
numeric character references (assuming the caller didn't already parse and
expand them).


==2: Normalize the character set==

These options are distinguished by being named in Title_Case with underscores
(following the Perl convention for Unicode character class names).
 See [http://unicode.org/reports/tr44/tr44-4.html#General_Category_Values].

This all assumes that the data is already Unicode, so be careful of CP1252.

* '''Ascii_Only''' (boolean) -- a special case.
Discards all non-ASCII characters, and turns control characters (such as
CR, LF, FF, VT, and TAB) to space. If you specify this, you should not specify
other character set normalization options.

All other character set normalization options are of type (disp):

(disp) values that apply to any character category at all:
  "keep"      -- Don't change the characters
  "delete"    -- Delete the characters entirely
  "space"     -- Replace the characters with a space
  "unify"     -- Convert all matches to a single character (see below)

(disp) values only for Number and its subtypes:
  "value"     -- Replace with the value

(disp) values only for Letter and its subtypes:
  "upper"     -- Force to upper-case
  "lower"     -- Force to lower-case
  "strip"     -- Decompose (NFKD) and then strip any diacritics
  "decompose" -- Decompose (NFKD) into component characters

''Letter'' and its subcategories default to `keep`; all other
character categories default to `unify` (see below for the
meaning of "unify" for each case).

'''Note''': A character may have multiple decompositions, or may be
undecomposable. The resulting string will also be in Compatibility decomposition
(see [http://unicode.org/reports/tr15/]) and
Unicode's Canonical Ordering Behavior. Compatibility decomposition combines
stylistic variations such as font, breaking, cursive, circled, width,
rotation, superscript, squared, fractions, ''some'' ligatures
(for example ff but not oe), and pairs like angstrong vs. A with ring,
ohm vs omega, long s vs. s.

`#unify` changes each character of the given class
to one particular ASCII character to represent the class (this is useful for finding
interesting patterns of use):

  Letter                  unifies to "A"
  Cased_Letter            unifies to "A"
  Uppercase_Letter        unifies to "A"
  Lowercase_Letter        unifies to "a"
  Titlecase_Letter        unifies to "Fi"
  Modifier_Letter         unifies to "A"
  Other_Letter            unifies to "A"

  Mark                    unifies to " "
  Nonspacing_Mark         unifies to " "
  Spacing_Mark            unifies to " "
  Enclosing_Mark          unifies to " "

  Number                  unifies to "9"
  Decimal_Number          unifies to "9"
  Letter_Number           unifies to "9"
  Other_Number            unifies to "9"

  Punctuation             unifies to "."
  Connector_Punctuation   unifies to "_"
  Dash_Punctuation        unifies to "-"
  Open_Punctuation        unifies to "("
  Close_Punctuation       unifies to ")"
  Initial_Punctuation     unifies to "`"
  Final_Punctuation       unifies to "'"
  Other_Punctuation       unifies to "*"

  Symbol                  unifies to "#"
  Math_Symbol             unifies to "="
  Currency_Symbol         unifies to "\\$"
  Modifier_Symbol         unifies to "#"
  Other_Symbol            unifies to "#"

  Separator               unifies to " "
  Space_Separator         unifies to " "
  Line_Separator          unifies to " "
  Paragraph_Separator     unifies to " "

  Other                   unifies to "?"
  Control                 unifies to "?"
      (includes > 64 characters. For example, U+00A0.
  Format                  unifies to "?"
  Surrogate               unifies to "?"
  Private_Use             unifies to "?"
  Unassigned              unifies to "?"

`unify` can also be used for the Non-word token options (see below); in that
case, each option has a particular value to which matching ''tokens'' unify.

Setting the option for a cover category (such as ''Letter'') is merely shorthand for
setting all its subcategories to that value. Some or all subcategories can
still be reset afterward, but any ''earlier'' setting for a subcategory
is discarded when you set its cover category.

To get a list of the category options run `Tokenizer.pm -list`.

The following character set normalization options can also be used
(but are not Unicode General Categories):

* '''Accent''' --
These are related to Unicode '''Nonspacing_Mark''',
but that also would include vowel marks, which this doesn't.
''#decompose'' and ''strip'' are important value for this option:
the format splits a composed letter+diacritic or similar combination
into its component parts; the latter discards the diacritic instead.
''#delete'' discards the whole accent+letter combination (?).
'''Note''': There is a separate Unicode property called "Diacritic",
but it isn't available here yet.

* '''Control_0''' -- The C0 control characters.
That is, the usual ones from \\x00 to \\x1F.
This option only matters if ''Control'' is set to `keep`.

* '''Control_1''' -- The C1 control characters.
That is, the "upper half" ones from \\x80 to \\x9F.
'''Note''': These are graphical characters in the common Windows(r) character
set known as "CP1252", but not in Unicode or most other sets.
This option only matters if ''Control'' is set to `keep`.

* '''Digit''' -- characters 0-9 -- Cf Unicode '''Number''', which is broader.

* '''Ligature''' characters -- This also includes titlecase and digraph
characters. '''Note''': Some Unicode ligatures, particular in Greek, may also
be involved in accent normalization.
See also [http://en.wikipedia.org/wiki/Typographic_ligature]
'''(not yet supported)'''

* '''Fullwidth''' --
See [http://en.wikipedia.org/wiki/Halfwidth_and_fullwidth_forms]
'''(not yet supported)'''

* '''Math''' -- Unicode includes many variants of the entire Latin
alphabet, such as script, sans serif, and others.
These are in the Unicode '''Math''' general category.
'''(not yet supported)'''

* '''Nbsp''' -- The non-breaking space character, U+00A0. This
defaults to being changed to a regular space.

* '''Soft_Hyphen''' -- The soft (optional) hyphen characters,
U+00AD and U+1806. These default to being deleted.


==3: Shorten runs of the same character==

These options are all (boolean).

* '''N_CHAR''' Reduce runs of >= N of the same
word-character in a row, to just N occurrences. This is for things like
"aaaaaaaarrrrrrrrrgggggggghhhhhh". However, it does not yet cover things
like "hahahaha".

* '''N_SPACE''' Reduce runs of >= N white-space characters
(not necessarily all the same) to just N.


==4: Non-word tokens==

This step can tweak various kinds of non-word tokens, such as
numbers, URIs, etc. The options are of type (disp), but the
only meaningful settings are "keep", "delete", "space", and "unify".

* '''T_TIME''' tokens, such as "6:24 pm".

* '''T_DATE''' tokens, such as "2012-08-22" or "2012 BCE".
Month names and abbreviations are not yet supported.

* '''T_FRACTION''' (including Unicode fraction characters if they
were not already normalized).

* '''T_NUMBER''' tokens, including signed or unsigned integers, reals,
and exponential notation (however, fractions are dealt with separately).
This does not include spelled-out numbers such as "five hundred".
(not yet supported)

* '''T_CURRENCY''' tokens, consisting of a currency symbol and a number,
such as $1, $29.95, etc.

* '''T_EMOTICON''' items

* '''T_HASHTAG''' items as in Twitter (#ibm)

* '''T_USER''' items as in Twitter (@john)

* '''T_EMAIL''' addresses

* '''T_URI''' items (see also the '''X_URI''' unescaping option earlier)


==4: Split tokens==

As a first approximation, text can be broken at each white-space character(s),
at all individual `characters`, or `none` at all. The choice depends on the
''TOKENTYPE'' option. There is a host of other rules for various cases.

Then leading and trailing punctuation are broken off.
This prevents leaving parentheses, commas, quotes, etc. attached to words.
However, the script is not smart (at least, yet) about special cases such as:

  $12       ~5.2      #1        +12
  5'6"      5!        5%
  U.S.      p.m.
  ).        ."        +/-
  (a)       501(c)(3)
  @user     #topic    ~a        AT&T
  e'tre     D'Avaux   let's     y'all     and/or
  house(s)

This needs some adjustments re. which punctuation is allowed on which
end.  Harder problems include plural genitives: "The three ''dogs''' tails."
and abbreviations versus sentence-ends.

A few special cases are controlled by these ("S_") options, such as
re-mapping contractions and breaking up hyphenated words (by inserting
extra spaces).

* '''S_CONTRACTION''' can be set to "unify" in order to
expand most English contractions. For example:
won't, ain't, we'll, we'd, we're, we'll, somebody'd,
y'all, let's, gonna, cannot.
Not very useful for non-English cases like "dell'" or "c'est".
(see also POS/multitagTokens).

* '''S_HYPHENATED''' break at hyphens, making the hyphen a separate
token. (Doesn't deal with soft hyphens or other '''Format''' characters.

* '''S_GENITIVE''' break "'s" to a separate token. This does not actually
catch all genitives, even in English (and, many "'s" cases in English
can be either genitives or contractions of "is".
'''(not yet supported)'''


==6: Filter out unwanted tokens ("words" mode only)==

These options are all (boolean) except for '''F_MINLENGTH''' and '''F_MAXLENGTH'''.
For Boolean filter options, the default is off, which means the tokens
are not discarded.

* '''F_MINLENGTH''' (int) -- Discard all tokens shorter than this.

* '''F_MAXLENGTH''' (int) -- Discard all tokens longer than this.

* '''F_SPACE''' (boolean) -- can be used to delete all white-space items.

* Filter by case and special-character pattern
Each of the following (disjoint) categories
can be controlled separately (see also ''--ignoreCase'', ''--Letter'', etc.):

** '''F_UPPER''' (boolean) -- remove words with only capital or caseless letters

** '''F_LOWER''' (boolean) -- remove words with only lower case or caseless letters

** '''F_TITLE''' (boolean) -- remove words with only an initial capital or titlecase
letter, followed by only lower case or caseless letters.

** '''F_MIXED''' (boolean) -- remove words with at least two capital and/or
titlecase letters, along with any number of lower case or caseless letters.

** '''F_ALNUM''' (boolean) -- remove words that contain both digits and
letters.

** '''F_PUNCT''' (boolean) -- remove words that contain both punctuation and
letters. However, hyphens, apostrophes, and periods do no count.

* Tokens in any specified '''F_DICT''' list. '''F_MINLENGTH''' ''4''
(see above) can serve as a passable substitute for a dictionary of
function words.


=Outline of token types (unfinished)=

(see also earlier sections)

(is there a useful type for "nested syntax"? dates, times, formulae, phone numbers,
music,

    Numeric
        Int
            Dec, Oct, Bin, Hex, Roman
        Real
            Float, Exp, Frac, pct/pmil
        Ordinal
            1st, #1, first
        Complex
        Matrix
        Math forms, roman and frac unicode, circled,....
        Formula
            SPecial constants: pi, euler, c, angstrom, micro prefix

    Date/time (under numeric? unit?)

    Unit
        Currency
        Dimension, scale
        32F 100C 273.15K

    Punc
        Quote
            Left/right/plain, single/double/angle
        Dash
            em/en/fig/soft?
        Brace
            left/right/shape/balanced
        Grammatical
            period, ellipsis, colon, semi, comma
        Verbal
            &, &c

    Identifier
        URL
        domain name
        email (incl. mailto?)
        hashtag
        @user
        Phone
        PostCode
        element
        substance

    Lexeme
        simplex
            lower, title, mixed, caps, uncased
            abbrev
                single initial?
            mixed-script
            construct
                dimethyltrichloroacetate
                genome (incl. end indicators)
        multiplex
            hyphenated
            acronym
            contraction (vs. possessive)
                gonna, ima, afaik
            idiom
                as far as, so as to,

    Dingbat
        Bullet, arrow
        emoticon, emoji
        sepline

    Mixture
        (>1 of alpha, num, punc)

Oddball cases:
    4x4 1'2" AT&T and/or
    60's
    Ph.D. vs. PhD (treat like soft hyphen?
    > or | for email quoting
    Mg+2 H2O
    gender symbols
    footnote numbers, daggers, etc.
    dominos, cards, dice
    c/o
    +/-
    O'Donnell


=Some high-order problem cases (not including Unicode cases)=

    and/or b/c +/-
    JRR vs. J.R.R. vs. J. R. R. Tolkien. Mr. J. Smith is here.
    See section (II) (A) (3), and also part B. Or Part [C].
    A: Introduction--fer real-life use.
    1'2". She is 5' tall. Or so they "think."
    I'm gonna be a contraction that'd be the writer's bane.

=Differences from some other tokenizers=

Such as Stanford https://nlp.stanford.edu/software/tokenizer.shtml.

* This tokenizer knows a lot about Unicode, especially punctuation, such
as the many varieties of dash, space, and brackets. Stanford also has several
Unicode-related options, including the thoughtful:

    strictTreebank3: PTBTokenizer deliberately deviates from strict PTB3 WSJ tokenization in two cases. Setting this improves compatibility for those cases. They are: (i) When an acronym is followed by a sentence end, such as "U.K." at the end of a sentence, the PTB3 has tokens of "Corp" and ".", while by default PTBTokenizer duplicates the period returning tokens of "Corp." and ".", and (ii) PTBTokenizer will return numbers with a whole number and a fractional part like "5 7/8" as a single token, with a non-breaking space in the middle, while the PTB3 separates them into two tokens "5" and "7/8". (Exception: for only "U.S." the treebank does have the two tokens "U.S." and "." like our default; strictTreebank3 now does that too.) The default is false.

* Many only break, rather than expand contractions. This means your lexicon
has to know "tokens" like:
    ca n't ai gim gon na lem haf ta da whad dya t shan

Adding these to the lexicon typically means they are accepted as real words
even when they didn't come from expading a contraction (and most tokenizers
don't pass along any signal of where the contractions were).

* One ''advantage'' of merely splitting, is that a few cases are ambiguous:
"'s" can repreent either "is" or "was", while "'re" can represent either
"are" or "were" and
"'d" can represent "would", "had", or possibly "did".
If you expand, you have to choose.

* Contracted "not" sometimes re-uses the "n" from the base, as in "can't".
Tokenizers vary in getting can|'t, ca|n't, can|n't, can|not. The only reason
seems to be a desire to not insert another "n"; but why avoid that gnat
when swallowing the camel of adding all these fragments to your lexicon?
Stanford, for one, (I think wisely) duplicates "." with sentence-end abbreviations,
which seems to me essentially the same thing.

* Some cases, like "ima" for "i am going to" don't even have enough letters
to do the "split" approach, so it's not strictly possible to be consistent
without adding new characters (or new information in some form).

* Worse, some of those tokens collide with real words, adding lexical
ambiguity that just isn't there:  "coulda" means "a" can be "HAVE", while
"buncha" means "a" can be "OF" -- but only in those cases. If you build
probability for POS tagging from those tokens, you're worse off.

* I haven't yet seen a tokenizer that accurately keeps offsets into a source
text, so everyone already accepts that you can't easily map back to the user's
"ur" input (say, to highlight something). This is bad enough in the case of
whitespace runs, line-breaks, tabs, etc; many tokenizers also normalize
(some, but rarely all) Unicode Zs (white-space-ish) characters to ASCII " ".
This is appropriate for some characters, but the notion that tab, LF,
non-breaking space, and hair space are all the same is wrong; they mean
very different things to actual readers.

* A very few contractions start with an apostrophe, making it harder to know
when to split that off.

* Some tokenizers "normalize" double-quotes (including curly ones, but rarely
chevrons or others) into apostrophes. This loses information that
can be important for syntactic processing, and also raises edge cases where
single and double quotes co-occurs, which is very common "Walk the 'dog'", she said."

* Some other tokenizers also have never heard of clausal dashes, turning two
hyphens (or, if they thought of it, Unicode em dash) into a single hyphen.


=Methods=

* '''new'''(tokenType)

Instantiate the tokenizer, and set it up for the ''tokenTYpe'' to be
either '''characters''' or '''words'''.

* '''addOptionsToGetoptLongArg(hashRef,prefix)'''

Add the options for this package to ''hashRef'', in the form expected by
`argparse`. If ''prefix'' is provided, add it to the beginning of each
option name (to avoid name conflicts). All the options for this package
are distinct even ignoring case, so callers may ignore or regard case
for options as desired.

* '''setOption'''(name,value)

Change the value of the named option.
Option names are case-sensitive (but see previous method).

'''Note''': Setting the option for a Unicode cover category
(such as '''Letter''' rather than '''Uppercase_Letter'''), is merely shorthand for
setting all its subcategories to that value
(subcategories can still be reset afterward).

* '''getOption'''(name)

Return the present value of the named option.
Option names are case-sensitive.

* '''tokenize'''(string)

Break ''string'' into tokens according to the settings in effect, and return
a reference to an array of them. '''Note''': This method uses several other
internal methods; they can be invoked separately is desired, but are not
documented fully here; the methods are as shown below (`s` is a string to
handle):

    s = tkz.expand(s)
    s = tkz.normalize(s)
    s = tkz.shorten(s)
    s = tkz.nonWordTokens(s)
    tokens = tkz.splitTokens(s)
    tokens = tkz.filter(tokens)


=Known Bugs and Limitations=

==True tokenization issues==

* house(s) breaks funny.
* Can't break words in orthographies that lack spaces (e.g., Japanese).
* Too generous about expanding contractions (e.g. "Tom's")

==Other==
Not all options are finished. For example:
''Ligature, Math, Fullwidth, S_GENITIVE,'' etc.
''T_NUMBER'' is disabled for the moment.
Titlecase characters, etc.
Some of this can be done in a pre-pass with:

    iconv -f utf8 -t ascii//TRANSLIT

(disp) values upper, lower, and decompose do not restrict themselves
to just a single category, but affect all if set for any.

Can't distinguish single vs. double quotes while unifying variants.

Abbreviations, acronyms, and other cases with word-final punctuation
are a little wonky: "U.S." loses the final ".".
Acronyms with periods ''and'' spaces aren't caught at all.
Acronyms aren't allowed within Names Entity References.

W/ testTokenizer defaults, turns B&O into 9/9&O ... into \\.\\.\\. doesn't
separate }. Default unifies URIs, emails, and some (?) numerics.  Doesn't do @userid.
Probably should move Unification out of Tokenizer?

Processing XML/HTML with default options, ends up splitting the SGML delimiters
apart from their constructs. Use `dropXMLtags` is necessary first.


=Related commands and data=

This uses the "regex" library [https://pypi.org/project/regex] instead of 
the built-in Python "re". It adds support for \\p{}. 

This Python program is mostly a port of a much earlier Perl one, which is also
available.

The `TokensEN.py` package gives access to list of English tokens that are
especially useful in tokenizing, such as abbreviations (for splitting the "."),
contractions (for distinguishing them from possessives), personal titles,
week and month names
`vocab`, `ngrams`, `normalizeSpace`, `SimplifyUnicode`,
`volsunga`, `findNERcandidates`,....

There is some test data inline, and more extensive data at
[https://github.com/sderose/Data/NLPFormatSamples/blob/master/TokenizerTestData.txt].

See [https://github.com/sderose/Lexicon.git/blob/master/xsv/contractions.xsv],
[https://github.com/sderose/Lexicon.git/blob/master/python/abbreviations.py]


=Related Commands=

Tokenize.py, Tokenizer.pm, Volsunga tokenizer (qv).

The "smoke test" data included in the code, has a lot of nice cases.


=Known bugs and Limitations=

Ported from Tokenizer.pm (also) by Steven J. DeRose.


=To do=

    More testing.
    Add timer.
    Incorporate abbrev list.
    Add any options Stanford or others have that this doesn't, such as:
        [https://nlp.stanford.edu/software/tokenizer.shtml]
        -encoding charset The character set encoding. By default, it assumues utf-8, but you can tell it to use another character encoding.
        -preserveLines Keep the input line breaks vs. one token per line.
        -oneLinePerElement Print the tokens of an element space-separated on one line.
        -parseInside regex Only tokenize inside XML elements which match the regex.
        -filter regex Delete any token that matches() (in its entirety).
        -lowerCase Force lowercase.
        -dump Print out everything about each token.
        -options optionString (bunch more)
        -ioFileList file+ Treat files as lists of in\tout files.
        -fileList file+ Treat files as lists of input filenames, one per line.
        -untok Makes a best effort attempt at undoing PTB tokenization.

    Split each stage (expand, filter, etc.) into a separate class?
    Consider switching this to Antlr 4?
    "''" as double quote
    Emoticons
    Should ellipsis plus [.,;?!] count as one punc unit or two?


=History=

* 2012: Written by Steven J. DeRose, in Perl.
* ????: Ported to Python.
* 2020-03-04: Fixes.
* 2021-04-09: Clean up. Spell NKFD right. Re-sync versions.
Clean up handling of `dispTypes`, quotes and general lint.
* 2022-03-11: Drop Python2. Lint.


=Rights=

Copyright 2012 by Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].


=Options=
"""


# Unicode "general categories", available via unicodedata.category(c)
# https://stackoverflow.com/questions/1832893/
# regex also supports single-char cover categories, I think.
#
unicodeCategories = {
    "Cc":  "Other, Control",
    "Cf":  "Other, Format",
    "Cn":  "Other, Not Assigned",
    "Co":  "Other, Private Use",
    "Cs":  "Other, Surrogate",
    "LC":  "Letter, Cased",
    "Ll":  "Letter, Lowercase",
    "Lm":  "Letter, Modifier",
    "Lo":  "Letter, Other",
    "Lt":  "Letter, Titlecase",
    "Lu":  "Letter, Uppercase",
    "Mc":  "Mark, Spacing Combining",
    "Me":  "Mark, Enclosing",
    "Mn":  "Mark, Nonspacing",
    "Nd":  "Number, Decimal Digit",
    "Nl":  "Number, Letter",
    "No":  "Number, Other",
    "Pc":  "Punctuation, Connector",
    "Pd":  "Punctuation, Dash",
    "Pe":  "Punctuation, Close",
    "Pf":  "Punctuation, Final quote",
    "Pi":  "Punctuation, Initial quote",
    "Po":  "Punctuation, Other",
    "Ps":  "Punctuation, Open",
    "Sc":  "Symbol, Currency",
    "Sk":  "Symbol, Modifier",
    "Sm":  "Symbol, Math",
    "So":  "Symbol, Other",
    "Zl":  "Separator, Line",
    "Zp":  "Separator, Paragraph",
    "Zs":  "Separator, Space",
}

unicodeSpaces = [
    0x0009,  # "CHARACTER TABULATION",
    0x000A,  # "LINE FEED",
    0x000B,  # "LINE TABULATION",
    0x000C,  # "FORM FEED",
    0x000D,  # "CARRIAGE RETURN",
    0x0020,  # "SPACE",
    0x0089,  # "CHARACTER TABULATION WITH JUSTIFICATION",
    0x00A0,  # "NO-BREAK SPACE",
    0x2000,  # "EN QUAD",
    0x2001,  # "EM QUAD",
    0x2002,  # "EN SPACE",
    0x2003,  # "EM SPACE",
    0x2004,  # "THREE-PER-EM SPACE",
    0x2005,  # "FOUR-PER-EM SPACE",
    0x2006,  # "SIX-PER-EM SPACE",
    0x2007,  # "FIGURE SPACE",
    0x2008,  # "PUNCTUATION SPACE",
    0x2009,  # "THIN SPACE",
    0x200A,  # "HAIR SPACE",
    0x200B,  # "ZERO WIDTH SPACE",
    0x202F,  # "NARROW NO-BREAK SPACE",
    0x205F,  # "MEDIUM MATHEMATICAL SPACE",
    0x2420,  # "SYMBOL FOR SPACE",
    0x3000,  # "IDEOGRAPHIC SPACE",
    0x303F,  # "IDEOGRAPHIC HALF FILL SPACE",
]

unicodeDashes = [
    0x002D,  # "HYPHEN-MINUS",
    0x058A,  # "ARMENIAN HYPHEN",
    0x1B60,  # "BALINESE PAMENENG (line-breaking hyphen)",
    0x2010,  # "HYPHEN",
    0x2011,  # "NON-BREAKING HYPHEN",
    0x2012,  # "FIGURE DASH",
    0x2013,  # "EN DASH",
    0x2043,  # "HYPHEN BULLET",
    0x2212,  # "MINUS",
    0x2448,  # "OCR DASH",
    0xFE63,  # "SMALL HYPHEN-MINUS",
    0xFF0D,  # "FULLWIDTH HYPHEN-MINUS",
]

# What of primes U+2032...U+2037, U+2057
unicodeLQuotes = [
    0x00AB, # "LEFT-POINTING DOUBLE ANGLE QUOTATION MARK *",
    0x2018, # "LEFT SINGLE QUOTATION MARK",
    0x201A, # "SINGLE LOW-9 QUOTATION MARK",
    0x201C, # "LEFT DOUBLE QUOTATION MARK",
    0x201E, # "DOUBLE LOW-9 QUOTATION MARK",
    0x2039, # "SINGLE LEFT-POINTING ANGLE QUOTATION MARK",
    0x2E02, # "LEFT SUBSTITUTION BRACKET",
    0x2E04, # "LEFT DOTTED SUBSTITUTION BRACKET",
    0x2E09, # "LEFT TRANSPOSITION BRACKET",
    0x2E0C, # "LEFT RAISED OMISSION BRACKET",
    0x2E1C, # "LEFT LOW PARAPHRASE BRACKET",
    0x2E20, # "LEFT VERTICAL BAR WITH QUILL",
]

unicodeRQuotes = [
    0x00BB, # "RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK *",
    0x2019, # "RIGHT SINGLE QUOTATION MARK",
    0x201B, # "SINGLE HIGH-REVERSED-9 QUOTATION MARK",
    0x201D, # "RIGHT DOUBLE QUOTATION MARK",
    0x201F, # "DOUBLE HIGH-REVERSED-9 QUOTATION MARK",
    0x203A, # "SINGLE RIGHT-POINTING ANGLE QUOTATION MARK",
    0x2358, # "APL FUNCTIONAL SYMBOL QUOTE UNDERBAR",
    0x235E, # "APL FUNCTIONAL SYMBOL QUOTE QUAD",
    0x2E03, # "RIGHT SUBSTITUTION BRACKET",
    0x2E05, # "RIGHT DOTTED SUBSTITUTION BRACKET",
    0x2E0A, # "RIGHT TRANSPOSITION BRACKET",
    0x2E0D, # "RIGHT RAISED OMISSION BRACKET",
    0x2E1D, # "RIGHT LOW PARAPHRASE BRACKET",
    0x2E21, # "RIGHT VERTICAL BAR WITH QUILL",
]

unicodeEllipses = [
    0x0eaf, # LAO ELLIPSIS
    0x1801, # MONGOLIAN ELLIPSIS
    0x2026, # HORIZONTAL ELLIPSIS
    0x22ee, # VERTICAL ELLIPSIS
    0x22ef, # MIDLINE HORIZONTAL ELLIPSIS
]

unicodeToDelete = [
    0x00AD,  # "SOFT HYPHEN"
    0x1806,  # "MONGOLIAN TODO SOFT HYPHEN"
    0x2027,  # "HYPHENATION POINT"
 ]

unicodeDoubles = [
    0x2014,  # EM DASH
    0x30a0,  # KATAKANA-HIRAGANA DOUBLE HYPHEN
    0xfe58,  # SMALL EM DASH
]

# (Cyrillic, Armenian, Hebrew, and many, many Arabic ligatures omitted)
# Could do this instead with unicodedb "Decompose" feature.
unicodeLigatures = [
    0x0132,  #  "IJ",   #"LATIN CAPITAL LIGATURE IJ",
    0x0133,  #  "ij",   #"LATIN SMALL LIGATURE IJ",
    0x0152,  #  "OE",   #"LATIN CAPITAL LIGATURE OE",
    0x0153,  #  "oe",   #"LATIN SMALL LIGATURE OE",
    0xa7f9,  #  "oe",   #"MODIFIER LETTER SMALL LIGATURE OE",
    0xfb00,  #  "ff",   #"LATIN SMALL LIGATURE FF",
    0xfb01,  #  "fi",   #"LATIN SMALL LIGATURE FI",
    0xfb02,  #  "fl",   #"LATIN SMALL LIGATURE FL",
    0xfb03,  #  "ffi",  #"LATIN SMALL LIGATURE FFI",
    0xfb04,  #  "ffl",  #"LATIN SMALL LIGATURE FFL",
    0xfb05,  #  "st",   #"LATIN SMALL LIGATURE LONG S T",
    0xfb06,  #  "st",   #"LATIN SMALL LIGATURE ST",
]

if (False):
    elRegex  = "[" + "".join([ chr(x) for x in unicodeEllipses]) + "]"  # --
    spRegex  = "[" + "".join([ chr(x) for x in unicodeSpaces  ]) + "]"  # Zs
    hyRegex  = "[" + "".join([ chr(x) for x in unicodeDashes  ]) + "]"  # Pd
    lqRegex  = "[" + "".join([ chr(x) for x in unicodeLQuotes ]) + "]"  # Pi
    rqRegex  = "[" + "".join([ chr(x) for x in unicodeRQuotes ]) + "]"  # Pf
    delRegex = "[" + "".join([ chr(x) for x in unicodeToDelete]) + "]"  # --
    dblRegex = "[" + "".join([ chr(x) for x in unicodeDoubles ]) + "]"  # --
    ligRegex = "[" + "".join([ chr(x) for x in unicodeLigatures]) + "]"
    #print("ligRegex: '%s'." % (ligRegex))
else:
    elRegex  = "[" + "".join([ chr(x) for x in unicodeEllipses]) + "]"  # --
    spRegex  = r"\p{Zs}"
    hyRegex  = r"\p{Pd}"
    lqRegex  = r"\p{Pi}"
    rqRegex  = r"\p{Pf}"
    delRegex = "[" + "".join([ chr(x) for x in unicodeToDelete]) + "]"  # --
    dblRegex = "[" + "".join([ chr(x) for x in unicodeDoubles ]) + "]"  # --
    ligRegex = "[" + "".join([ chr(x) for x in unicodeLigatures]) + "]"
    #print("ligRegex: '%s'." % (ligRegex))


lexemeTypes = {
    "lower": [ "lower", r"[a-z]+" ],
    "upper": [ "upper", r"[A-Z]+" ],
    "title": [ "title", r"[A-Z][a-z]+" ],
    "mixed": [ "mixed", r"\w+" ],
}


# Reserved set of option values, to specify for how to map char classes.
# Use numbers for faster tests in map().
#
DT_KEEP             = "KEEP"
DT_UNIFY            = "UNIFY"
DT_DELETE           = "DELETE"
DT_SPACE            = "SPACE"
DT_STRIP            = "STRIP"
DT_VALUE            = "VALUE"
DT_UPPER            = "UPPER"
DT_LOWER            = "LOWER"
DT_DECOMPOSE        = "DECOMPOSE"

dispTypes = {
    # Keyword:       ( DT_NAME,      map?, whichClasses),
    DT_KEEP:         ( DT_KEEP,          False, "*" ),
    DT_UNIFY:        ( DT_UNIFY,         True,  "*" ),
    DT_DELETE:       ( DT_DELETE,        True,  "*" ),
    DT_SPACE:        ( DT_SPACE,         True,  "*" ),
    DT_STRIP:        ( DT_STRIP,         True,  "Letter" ),
    DT_VALUE:        ( DT_VALUE,         True,  "Number" ),
    DT_UPPER:        ( DT_UPPER,         False, "Letter" ),
    DT_LOWER:        ( DT_LOWER,         False, "Letter" ),
    DT_DECOMPOSE:    ( DT_DECOMPOSE, False, "Letter" ),
}

# Enumeration of token "types" and "subtypes".
#
# Not used yet, but a finer-grained set of possibilities is provided below,
# mostly based on my "Tokenizer" package.... Most can never contain spaces,
# except for DATIME and MATH.
#
tokenSubtypes = {
    "W": {
        "NUM":       "W: 1, 1.2E+08, 0xFF, 1/3, 12%, per-mil, 6'1\", phone, ip",
        "DATIME":    "W: Date and/or time string",
        "MATH":      "W: Math beyond just numbers",
        "CONTR":     "W: Separated contraction part, such as n't or na",
    },
    "S": {
        "LINE":      "S: Line boundary (put with prev or next, or separate?",
    },
    "P": {
        "CURRENCY":  "P: Currency indicator (if with it's number, -> NUM)",
        "EM":        "P: Clausal/em dash",
        "ELLIPSIS":  "P: Ellipsis, 3 or 4 dots, etc.",
        "QI":        "P: Initial/open quote (left in left-to-right writing systems",
        "QC":        "P: Final/close quote (right in left-to-right writing systems",
        "BI":        "P: Initial/open bracket (left in left-to-right writing systems",
        "BC":        "P: Final/close bracket (right in left-to-right writing systems",
        "EMOJI":     "P: Emoji or emoticon",
        "RULE":      "P: A rule (generally horizontal)",
        "DASH":      "P: Hyphens and dashes other than EM (soft get normalized away)",
        "DINGBAT":   "P: Any kind of typographic ornament",
    },
    "I": {
        "URL":       "I: A URL",
        "EMAIL":     "I: An email address",
        "HASHTAG":   "I: A Twitter-style hash-tag keyword",
        "IPADDR":    "I: 192.168.1.1",
    },
}


###############################################################################
#
def die(msg):
    sys.stderr.write(msg+"\n")
    raise AssertionError(msg)


###############################################################################
# Could be fancier. Based on Volsunga Python port.
#
# Issues:
#     "1920's"; many more date formats. +/-?
#     Does not always split multiple open/close punctuation apart.
#
class SimpleTokenizer:
    # Add spaces around em-dashes, ellipses
    splitDashes    = re.compile(r"(--+|\u2014|\uFE58|\.\.\.\.?|\u2026)")

    # Find leading punctuation marks (not apostrophe?)
    splitFromStart = re.compile(r"(?<=\s|^)([\"`\p{Pi}\p{Ps}]+)")

    # Find trailing punctuation marks (not apostrophe?)
    # Careful not to catch ":" in things like "2:30am", "http://".
    splitFromEnd   = re.compile(r"([\"`:;,.?!\p{Pf}\p{Pe}]+)(?=\s|$)")

    # Split up contractions and possessives. See also TokensEN.py.
    contracted     = re.compile(r"(?<=\w)('(s|d|t|ll|ve|re)?)(?=\s|$)")

    # Hyphenated words?
    hyphens        = re.compile(r"(\w)-(\w)")

    # Insert spaces between all characters, except inside emdash, ellipsis.
    #
    def spaceAll(self, mat):
        #print("spaceAll got: '%s'." % (mat.group(1)))
        return re.sub(r"([^.-]|\.+|-+)", " \\1", mat.group(1)) + " "

    def __init__(self,
        normalize = "NFKD",            # Unicode normalization (of "")
        breakHyphens = False,          # Split hyphenated words?
        fancyContractions = False,     # Use lg-specific token list
        verbose = False
        ):
        self.normalize = normalize
        self.breakHyphens = breakHyphens
        self.contractor = None
        if (fancyContractions):
            import TokensEN
            self.contractor = TokensEN.TokensEN()
        self.verbose = verbose
        return

    def tokenize(self, s1):
        # Normalize Unicode. NFKD default gets to decomposed form.
        # Punctuation may land next to diacritics (which are not \w).
        #
        if (self.normalize):
            s2 = unicodedata.normalize("NFKD", unicode(s1))
        else:
            s2 = s1

        # Soft (optional) hyphens just get in the way.
        #
        s2 = re.sub("\u00AD", "", s2)             # soft hyphen

        # Insert spaces to separate various punctuation from words.
        #
        if (self.verbose):
            s2 = re.sub(SimpleTokenizer.splitDashes,    r" \1 ",    s2)
            print("dashes: %s" % (s2))

            s2 = re.sub(SimpleTokenizer.splitFromStart, self.spaceAll, s2)
            print("starts: %s" % (s2))

            s2 = re.sub(SimpleTokenizer.splitFromEnd, self.spaceAll, s2)
            print("finals: %s" % (s2))

            if (self.contractor is None):
                s2 = re.sub(SimpleTokenizer.contracted, r" \1",     s2)
            else:
                s2 = self.contractor.doContractions(s2)
            print("contrs: %s" % (s2))

            if (self.breakHyphens):
                s2 = re.sub(SimpleTokenizer.hyphens,    r"\1 - \2", s2)
                print("hyphens: %s" % (s2))

            tokens = re.split(r"\p{Z}+", s2.strip())
            #print("tokens:\n    #%s#" % ("#\n    #".join(tokens)))

        else:
            s2 = re.sub(SimpleTokenizer.splitDashes,    r" \1 ",    s2)

            s2 = re.sub(SimpleTokenizer.splitFromStart, self.spaceAll, s2)

            s2 = re.sub(SimpleTokenizer.splitFromEnd, self.spaceAll, s2)

            if (self.contractor):
                s2 = self.contractor.doContractions(s2)
            else:
                s2 = re.sub(SimpleTokenizer.contracted, r" \1",     s2)

            if (self.breakHyphens):
                s2 = re.sub(SimpleTokenizer.hyphens,    r"\1 - \2", s2)

            tokens = re.split(r"\p{Z}+", s2.strip())

        return(tokens)


###############################################################################
#
class NLTKTokenizerPlus:
    """
    See also https://keras.io/preprocessing/text/
        keras.preprocessing.text.Tokenizer(
            num_words=None,          # drop low-freq words
            filters="...",           # drop these chars (default: v. all punc)
            lower=True,              # toLower
            split=" ",               # word-split on this
            char_level=False,        # true to split to individual chars
            oov_token=None)          # use for out-of-vocab words
        Which looks even lamer....

    Issues:
        Leaves final period on the last token of the text.
        Splits off contraction, etc (but not possessives?).
        Splits plus-or-minus after the slash
        Splits before hyphen (and comma?) in DNA and chemical names
        Splits after URL schem (and before most slashes, like in paths)
        Join https?: with next token.

    This fixes:
        Keep dot if there's another one (e.g., U.S.A., a.m.)
        So still drop dot for Mr., Dr., A., and sentence-final.
        Lots of Unicode punctuation issues.
    """
    def __init__(self):
        try:
            import nltk
        except ImportError:
            print("\n******* Cannot import nltk *******")

        self.nltk = nltk
        self.options = {}
        self.srcData = ""
        self.tokens = []

    def tokenize(self, txt):
        if (self.options["unicodePunct"]):
            txt = self.regularizeUnicode(txt)
        if (self.options["expandLigatures"]):
            txt = self.expandLigatures(txt)
        if (self.options["normalize"]):
            txt = unicodedata.normalize(self.options["normalize"], txt)

        tokens = self.nltk.word_tokenize(txt)
        for i, token in enumerate(tokens):
            if (len(token) == 1): continue
            if (token.endswith(".")):
                if (token.find(".") != len(token)-1): continue
                tokens[i] = token[0:-1]
        return tokens

    def regularizeUnicode(self, txt):
        """Deal with Unicode details. Specifically:
            - Reduce variant spaces, dashes, quotes
            - Scream on seeing unexpanded XML/HTML entities
        What of:
            brackets
            daggers, superscripts, subscripts, dot leaders
            math specials
            !! !? ?? ?! iquest interrobang
            emoji and dingbats
        """
        if (re.search(r"&[#\w]\w+;", txt)):
            die("Unexpected XML/HTML entity syntax in '%s'.")
        txt = re.sub(elRegex, ",", txt)    # -- Ellipses
        txt = re.sub(spRegex, " ", txt)    # Zs Spaces
        txt = re.sub(hyRegex, "-", txt)    # Pd dashes
        txt = re.sub(lqRegex, '"', txt)    # Pi Left Quotes
        txt = re.sub(rqRegex, '"', txt)    # Pf Right quotes
        txt = re.sub(delRegex, "", txt)    # -- Chars to delete
        txt = re.sub(dblRegex, "--", txt)  # -- em dashes
        return txt

    def expandLigatures(self,txt):
        return re.sub(ligRegex, ligRegexFunction, txt)


###############################################################################
# Functions used as RHS in regex changes
#
def ligRegexFunction(mat):
    try:
        return unicodeLigatures[mat.group(0)]
    except KeyError:
        return mat.group(0)

def strip_diacritics(mat):
    c = mat.group(1)
    de = unicodedata.normalize("NFKD", c)
    if (de is None or de == ""): return(c)
    # Ditch accents, but not ligature parts...
    de = re.sub(r"\p{Mn}", "", de)
    return de


def get_value(mat):
    """Unicode defines numeric values for many chars, such as fractions.
    """
    c = mat.group(1)
    v = unicodedata.numeric(c)
    if (v is None or v == ""): return(c)
    return(v)


###############################################################################
#
class HeavyTokenizer:
    """Based on my Perl Tokenizer.pm.
    """
    dispValues = {
        # Keyword     Value    Classes that can use it
        # No change needed:
        "keep"      :  1,     # "*"
        "unify"     : 11,     # "*"
        "delete"    : 12,     # "*"
        "space"     : 13,     # "*"
        "strip"     : 14,     # "Letter"
        "value"     : 15,     # "Number"
        # Not done via map()... probably should be....
        "upper"     :  6,     # "Letter"
        "lower"     :  7,     # "Letter"
        "decompose" :  8,     # "Letter"
        }

    def __init__(self, breakHyphens=False):
        self.options     = {}
        self.optionTypes = {}
        self.version     = __version__
        self.anyFilters  = 1
        self.srcData     = ""
        self.tokens      = []
        self.nNilTokens  = []   # by place in record
        self.regexes     = {}

        self.breakHyphens = breakHyphens

        self.defineOptions()
        self.preCompileRegexes()

    ###########################################################################
    # OPTIONS
    #
    def defineOptions(self):
        sdo = self.defineOption

        #   Name             Datatype   Default
        sdo("unicodePunct",      "boolean", True)    # Simplify Unicode punc
        sdo("expandLigatures",   "boolean", True)    # Simplify fi/fl etc.
        sdo("normalize",         ""       , True)    # NFC/NFKC/NFD/NFKD
        sdo("dropFinalDot",      "boolean", True)    # final-period handling
        sdo("splitContractions", "boolean", True)
        sdo("splitPossessives",  "boolean", True)
        sdo("caseHandling",      "keep"   , True)    # /keep/lower/upper
        sdo("assignTypes",       "boolean", False)   # TokenTypes

        sdo("TVERBOSE",      "boolean", 0)
        sdo("TOKENTYPE",     "string",  "words")

        # 1: Expand
        sdo("X_BACKSLASH",   "boolean", 0)
        sdo("X_URI",         "boolean", 0)
        sdo("X_ENTITY",      "boolean", 0)

        # 2: Normalize
        sdo("Ascii_Only",    "boolean", 0)
        sdo("Accent",        "disp",    "keep")
        sdo("Control_0",     "disp",    "keep")
        sdo("Control_1",     "disp",    "keep")
        sdo("Digit",         "disp",    "keep")
        sdo("Fullwidth",     "disp",    "keep")
        sdo("Ligature",      "disp",    "keep")
        sdo("Math",          "disp",    "keep")
        sdo("Nbsp",          "disp",    "space")
        sdo("Soft_Hyphen",   "disp",    "delete")
        for u in (unicodeCategories.keys()):  # The Unicode categories
            sdo(u,           "disp",    "keep")

        # 3: Shorten
        sdo("N_CHAR",        "int",     0)
        sdo("N_SPACE",       "int",     0)

        # 4: Non-word tokens
        sdo("T_TIME",        "disp",    "keep")
        sdo("T_DATE",        "disp",    "keep")
        sdo("T_FRACTION",    "disp",    "keep")
        sdo("T_NUMBER",      "disp",    "keep")
        sdo("T_CURRENCY",    "disp",    "keep")
        sdo("T_PERCENT",     "disp",    "keep")
        sdo("T_EMOTICON",    "disp",    "keep")
        sdo("T_HASHTAG",     "disp",    "keep")
        sdo("T_USER",        "disp",    "keep")
        sdo("T_EMAIL",       "disp",    "keep")
        sdo("T_URI",         "disp",    "keep")

        # 5: Special issues
        sdo("S_CONTRACTION", "disp",    "keep")
        sdo("S_HYPHENATED",  "disp",    "keep")
        sdo("S_GENITIVE",    "disp",    "keep")

        # 6: Filter (0 means keep, 1 means filter out)
        sdo("F_MINLENGTH",   "int",     0)
        sdo("F_MAXLENGTH",   "int",     0)
        sdo("F_DICT",        "string",  "")
        sdo("F_SPACE",       "boolean", 0) # OBS?
        sdo("F_UPPER",       "boolean", 0)
        sdo("F_LOWER",       "boolean", 0)
        sdo("F_TITLE",       "boolean", 0)
        sdo("F_MIXED",       "boolean", 0)
        sdo("F_ALNUM",       "boolean", 0)
        sdo("F_PUNCT",       "boolean", 0)

        return

    def defineOption(self, name, datatype, dft):
        if (name in self.options):
            die("Duplicate option def for '%s'\n" % (name))
        self.optionTypes[name] = datatype
        self.options[name] = dft
        return

    def setOption(self, name, value):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        self.options[name] = value

    def getOption(self, name):
        if (name not in self.options):
            raise ValueError("Unknown option '%s'." % (name))
        return self.options[name]


    ###########################################################################
    # REGEX
    #
    def preCompileRegexes(self):

        self.regexes["Ascii_Only"]  = r"[^[:ascii:]]"

        for ugcName in (unicodeCategories.keys()):
            self.regexes[ugcName]  = r'\p{'+ugcName+'}'

        self.regexes["Accent"]      = r"" ### FIX ###
        self.regexes["Control_0"]   = r"[\x00-\x1F]"
        self.regexes["Control_1"]   = r"[\x80-\x9F]"
        self.regexes["Digit"]       = r"[0-9]"
        #self.regexes["Fullwidth"]  = r"" ### FIX ###
        #self.regexes["Ligature"]   = r"" ### FIX ###
        #self.regexes["Math"]       = r"" ### FIX ###

        ###################################################### VERY SPECIAL CHARS
        self.regexes["Nbsp"]        = r"\xA0"
        self.regexes["Soft_Hyphen"] = r"\xAD\u1806"

        ###################################################### DATE/TIME
        # Doesn't deal with alphabetic times
        #
        yr       = r"\b[12]\d\d\d"                         # Year
        tim      = r"[012]?\d:[0-5]\d(:[0-5]\d)?"
        # Move following few to TokensEN?
        ampm     = r"(a\.?m\.?|p\.?m\.?)?"
        era      = r"(AD|BC|CE|BCE)"                       # Which half of hx
        zone     = r"\s?[ECMP][SD]T"                       # Time zone
        self.regexes["T_TIME"]      = r"\b%s\s*%s(%s)?\b" % (tim, ampm, zone)
        # Also '60s 60's 60s
        self.regexes["T_DATE"]      = r'\b('+yr+r'".\'[-\/][0-3]?\d[-\/][0-3]?\d)|('+yr+' ?'+era+r')\b'

        ###################################################### NUMERICS
        # Also float, exp, 1,234,567, 5'6", roman numerals, Europen punctuation
        #
        self.regexes["T_NUMBER"]    = r'\b[-+]?\d+\b'
        self.regexes["T_FLOAT"]     = r'\b[-+]?\d+(\.\d+)?([Ee][-+]?\d+)?\b'

        ###################################################### FRACTIONS
        # Doesn't deal with spelled out "one half" etc.
        # (sadly, Unicode lumps these into Number, other).
        fractionChars = "".join([
            "\u00BC",   # VULGAR FRACTION ONE QUARTER
            "\u00BD",   # VULGAR FRACTION ONE HALF
            "\u00BE",   # VULGAR FRACTION THREE QUARTERS
            "\u0B72",   # ORIYA FRACTION ONE QUARTER
            "\u0B73",   # ORIYA FRACTION ONE HALF
            "\u0B74",   # ORIYA FRACTION THREE QUARTERS
            "\u0B75",   # ORIYA FRACTION ONE SIXTEENTH
            "\u0B76",   # ORIYA FRACTION ONE EIGHTH
            "\u0B77",   # ORIYA FRACTION THREE SIXTEENTHS
            "\u0C78",   # TELUGU FRACTION DIGIT ZERO FOR ODD POWERS OF FOUR
            "\u0C79",   # TELUGU FRACTION DIGIT ONE FOR ODD POWERS OF FOUR
            "\u0C7A",   # TELUGU FRACTION DIGIT TWO FOR ODD POWERS OF FOUR
            "\u0C7B",   # TELUGU FRACTION DIGIT THREE FOR ODD POWERS OF FOUR
            "\u0C7C",   # TELUGU FRACTION DIGIT ONE FOR EVEN POWERS OF FOUR
            "\u0C7D",   # TELUGU FRACTION DIGIT TWO FOR EVEN POWERS OF FOUR
            "\u0C7E",   # TELUGU FRACTION DIGIT THREE FOR EVEN POWERS OF FOUR
            "\u0D73",   # MALAYALAM FRACTION ONE QUARTER
            "\u0D74",   # MALAYALAM FRACTION ONE HALF
            "\u0D75",   # MALAYALAM FRACTION THREE QUARTERS
            "\u2044",   # FRACTION SLASH Sm 0 CS     N
            "\u2150",   # VULGAR FRACTION ONE SEVENTH
            "\u2151",   # VULGAR FRACTION ONE NINTH
            "\u2152",   # VULGAR FRACTION ONE TENTH
            "\u2153",   # VULGAR FRACTION ONE THIRD
            "\u2154",   # VULGAR FRACTION TWO THIRDS
            "\u2155",   # VULGAR FRACTION ONE FIFTH
            "\u2156",   # VULGAR FRACTION TWO FIFTHS
            "\u2157",   # VULGAR FRACTION THREE FIFTHS
            "\u2158",   # VULGAR FRACTION FOUR FIFTHS
            "\u2159",   # VULGAR FRACTION ONE SIXTH
            "\u215A",   # VULGAR FRACTION FIVE SIXTHS
            "\u215B",   # VULGAR FRACTION ONE EIGHTH
            "\u215C",   # VULGAR FRACTION THREE EIGHTHS
            "\u215D",   # VULGAR FRACTION FIVE EIGHTHS
            "\u215E",   # VULGAR FRACTION SEVEN EIGHTHS
            "\u215F",   # FRACTION NUMERATOR ONE
            "\u2189",   # VULGAR FRACTION ZERO THIRDS
            "\u2CFD",   # COPTIC FRACTION ONE HALF
            "\uA830",   # NORTH INDIC FRACTION ONE QUARTER
            "\uA831",   # NORTH INDIC FRACTION ONE HALF
            "\uA832",   # NORTH INDIC FRACTION THREE QUARTERS
            "\uA833",   # NORTH INDIC FRACTION ONE SIXTEENTH
            "\uA834",   # NORTH INDIC FRACTION ONE EIGHTH
            "\uA835",   # NORTH INDIC FRACTION THREE SIXTEENTHS
            "\u10E7B",   # RUMI FRACTION ONE HALF
            "\u10E7C",   # RUMI FRACTION ONE QUARTER
            "\u10E7D",   # RUMI FRACTION ONE THIRD
            "\u10E7E",   # RUMI FRACTION TWO THIRDS
        ])

        self.regexes["T_FRACTION"]  = r"\b((\d+-)?\d+\/\d+|[%s])\b" % (fractionChars)

        ###################################################### CURRENCY
        currency = "".join([r"$",
            "\u00A3",   # pound sign
            "\u00A4",   # currency sign
            #"\u09F4",   # to U+09F9: Bengali currency numerators/denominator
            "\u0E3f",   # Thai bhat
            "\u17DB",   # Khmer riel
            "\u20A0",   # Euro sign ~~ U+20CF
            "\uFFE1",   # fullwidth pound sign
            "\uFE69",   # SMALL DOLLAR SIGN
            "\uFF04",   # FULLWIDTH DOLLAR SIGN
            #"\u1F4B2",  # HEAVY DOLLAR SIGN
        ])
        self.regexes["T_CURRENCY"]  = r"\b[%s]\d+(\.\d+)?[KMB]?\b" % (currency)

        ###################################################### PERCENT, etc.
        pct = "".join(["%",
            "\u2030",   # Per Mille Sign
            "\u2031",   # Per Ten Thousand Sign
            "\u0609",   # Arabic-indic Per Mille Sign
            "\u060a",   # Arabic-indic Per Ten Thousand Sign
            "\u066a",   # Arabic-indic Percent Sign
            "\uFE6A",   # Small Percent Sign
            "\uFF05",   # Fullwidth Percent Sign
        ])
        self.regexes["T_PERCENT"]   = r"\b\d+(\.\d+)[%s]\b" % (pct)

        uriChars = r"[-~?\\[\\]\\(\\)&@+\w.:\\/\\$\\#]"    # Chars ok in URIs
        schemes  = "(shttp|http|https|ftp|mailto)"        # URI scheme prefixes
        #tld      = "(com|org|edu|net|uk|ca)"              # top-level domains
        self.regexes["T_EMOTICON"]  = r"[-:;]+[(){}<>]\b"
        self.regexes["T_HASHTAG"]   = r"\b#\p{L}+\b"
        self.regexes["T_EMAIL"]     = r"\b\w+@\w+(\.\w+)+\b"
        self.regexes["T_USER"]      = r"\s@[.\w+]\b"
        self.regexes["T_URI"]       = r"\b%s:\/\/%s+\w\b" % (schemes, uriChars)

        ###################################################### Hyphenation
        self.regexes["S_HYPHENATED"]= r"(\w)-(\w)"

        self.regexes["N_CHAR"]      = r"(\w)\1{%s,}" % (self.options["N_CHAR"])
        self.regexes["N_SPACE"]     = r"\s{%s,}" % (self.options["N_SPACE"])


    ###########################################################################
    # MAIN TOKENIZER
    #
    def tokenize(self, s):
        if (self.options["TVERBOSE"]):
            s = self.expand(s)
            print("Expanded: %s" % (s))
            s = self.normalize(s)
            print("Normalized: %s" % (s))
            s = self.shorten(s)
            print("Shortened: %s" % (s))
            s = self.nonWordTokens(s)
            print("nonWords: %s" % (s))
            tokens = self.splitTokens(s)
            print("SplitTokens: %s" % (tokens))
            if (self.anyFilters): tokens = self.filter(tokens)
            print("Filtered: %s" % (tokens))
        else:
            s = self.expand(s)
            s = self.normalize(s)
            s = self.shorten(s)
            s = self.nonWordTokens(s)
            tokens = self.splitTokens(s)
            if (self.anyFilters): self.filter(tokens)
        self.srcData = s
        self.tokens = tokens
        return(tokens)

    def expand(self, s):
        """Decode various special-character representations for various
        file formats. These often get left around in NLP lexica....
        """
        if (self.options["X_BACKSLASH"]):        # \uFFFF, \xFF, \n, etc.
            if (sys.version_info[0] < 3):
                s = s.decode("string_escape")
            else:
                s = s.decode("unicode_escape")

        if (self.options["X_URI"]):              # %FF
            s = urllib.parse.unquote(s)

        if (self.options["X_ENTITY"]):           # &#xFF; &#255; &lt;
            s = html.unescape(s)

        return s

    def normalize(self, s):
        if (self.options["Ascii_Only"] ): # boolean
            s = re.sub(r"[^[:ascii:]]", "", s)

        else:
            for ugcName in (unicodeCategories.keys()):
                optValue = self.options[ugcName]
                if (dispTypes[optValue] == DT_KEEP): continue
                s = self.map(s, ugcName, unicodeCategories[ugcName])

            s = self.map(s, "Accent",            "???")
            s = self.map(s, "Control_0",         " ")
            s = self.map(s, "Control_1",         " ")
            # The digit normalization should be optional:
            #s = self.map(s, "Digit",             "9")
            #s = self.map(s, "Fullwidth"
            #s = self.map(s, "Ligature"
            #s = self.map(s, "Math"
            s = self.map(s, "Nbsp",              " ")
            s = self.map(s, "Soft_Hyphen",       "")
        return s

    def shorten(self, s):
        """Nuke tokens where char is heavily repeated, like argggggggg.
        """
        if (self.options["N_CHAR"] > 1):
            s = re.sub(self.regexes["N_CHAR"],"11",s)

        if (self.options["N_SPACE"] > 1):
            s = re.sub(self.regexes["N_SPACE"], " ", s)
        return s


    ###########################################################################
    #
    def nonWordTokens(self, s):
        """Special handling for special kinds of tokens.
        Don't need to tokenize these, they're normally already surrounded by
        spaces or other breaking punctuation. But, can unify/space/delete them.
        """
        s = self.map(s, "T_TIME",      r"09:09")
        s = self.map(s, "T_DATE",      r"2009-09-09")
        s = self.map(s, "T_FRACTION",  r"9/9")
        #s = self.map(s, "T_NUMBER",    r"9999")
        #s = self.map(s, "T_CURRENCY",  r"#99")
        s = self.map(s, "T_PERCENT",   r"99%")
        s = self.map(s, "T_EMOTICON",  r":)")
        s = self.map(s, "T_HASHTAG",   r"#nine")
        s = self.map(s, "T_EMAIL",     r"u\@nine.com")
        s = self.map(s, "T_USER",      r"\@nine")
        s = self.map(s, "T_URI",       r"http://www.nine.com")
        return s

    def splitTokens(self, s):
        # A few specials
        s = re.sub(r"--+", " -- ", s)  # em dash
        for c in ([ "\\.", "\\/", "\\*", "\\\\", "#", "=", "\\?", "\\!" ]):
            s = re.sub(r"(%s\s*){3,}" % (c), " %s " % (c*3), s)

        s = self.map(s, "S_HYPHENATED", "\\1 - \\2")

        #s = self.map(s, "S_GENITIVE", ...)

        if (self.options["S_CONTRACTION"] != "keep"):
            die("Contraction support is not included now")
            #... import TokensEN instantiate it in our constructor
            #self.doContractions()

        tokens = None
        bt = self.getOption("TOKENTYPE")
        if (not bt): bt = ""
        if (bt == "words"):                             # WORD/TOKEN SPLITTING
            # Break periods *not* for abbreviations
            try:
                #s = re.sub(r"(\w)\. (\p{PosixUpper})", "\\1 . \\2", s)
                #s = re.sub(
                #    r"(" + HeavyTokenizer.langSpec.titles +
                #    r") \.", "\\1.", s)
                s = re.sub(
                    r"\b(\w) \. (\w) \.\b", "\\1.\\2.", s)

                # Separate punct at start/end of words
                s = re.sub(
                    r"(\s+)([^\w\s#@]+)(\w)", " \\2 \\3", s)
                s = re.sub(
                    r"(\w)([^\w\s.]+)(\s|$)", "\\1 \\2 ", s) # Not periods!
            except re.error as e:
                die("regex core error: %s" % (e))
            # Finally, split on all spaces (maybe switch to do this first?
            tokens = re.split(r"\s+", s)

        elif (bt == "chars"):                          # CHARACTER SPLITTING
            tokens = re.split(r"", s)
            #warn "Split into: {" . join(" ",    tokens) . "}\n"

        elif (bt == "none"):                           # NO SPLITTING AT ALL
            tokens.push(s)

        else:
            die("Unknown TOKENTYPE '%s' (not words, chars, or none).\n" % (bt))

        return(tokens)

    def map(self, s, optName:str, norm: str=None) -> str:
        """Check a given option (for ones that take a `dispType`
        as their value). Apply a regex change (that was already compiled!),
        to do the right thing to matching data.
        """
        optValue = self.options[optName]
        if (optValue is None):
            die("No option value found for '%s'." % (optName))
            optValue = self.options[optName] = "keep"

        cregex = self.regexes[optName]
        if (not cregex):
            die("No compiled regex available for '%s'" % (optName))
            return

        #warn "Firing %s\t'%s': \t/%s/ on\n    %s\n" %
        # (optName, optValue, regex, s))
        dl = dispTypes[optValue]

        try:
            if (dl[0] == DT_KEEP):                  # keep
                return
            if (dl[0] == DT_UNIFY):                 # unify
                s = re.sub(cregex, norm, s)
            elif (dl[0] == DT_DELETE):              # delete
                s = re.sub(cregex, "", s)
            elif (dl[0] == DT_SPACE):               # space
                s = re.sub(cregex, " ", s)
            elif (dl[0] == DT_STRIP):               # strip
                s = re.sub(r"(%s)" % (cregex), strip_diacritics, s)
            elif (dl[0] == DT_VALUE):               # value
                s = re.sub(r"(%s)" % (cregex), get_value, s)
            elif (dl[0] == DT_UPPER):               # upper
                s = s.upper()
                # OR: s = re.sub(r"(%s)" % (cregex), "\U\\1\E", s)
            elif (dl[0] == DT_LOWER):               # lower
                s = s.lower()
                # OR: s = re.sub(r"(%s)" % (cregex), "\L\\1\E", s)
            elif (dl[0] == DT_DECOMPOSE):           # decompose
                s = unicodedata.normalize("NFKD", s)
            else:
                die("map: bad (disp) value '%d' (=%s)\n" % (optValue, dl))
        except TypeError as e:
            print("TypeError (cregex is %s):\n    %s" % (cregex, e))

        return s


    ###########################################################################
    # Discard unwanted kinds of tokens.
    # Faster to discard by nilling out, and dropping at the end.
    #
    def filter(self, tokens):
        #warn "filtering...\n"
        for i in (range(len(tokens))):
            nillable = 0
            t = tokens[i]
            if (len(t) < self.options["F_MINLENGTH"]): nillable = 1
            elif (self.options["F_MAXLENGTH"] > 0 and
                     len(t) > self.options["F_MAXLENGTH"]): nillable = 1
            #elif (self.options["F_DICT"]  and      # dictionaries
            #        self.dict[t]): nillable = 1
            elif (self.options["F_SPACE"] and      # boolean
                     re.search(r"^\s*$", t)): nillable = 1
            elif (self.options["F_UPPER"] and      # UPPER
                     re.search(r"^[[:upper:]]+$", t)): nillable = 1
            elif (self.options["F_LOWER"] and      # lower
                     re.search(r"^[[:lower:]]+$", t)): nillable = 1
            elif (self.options["F_TITLE"] and      # Title
                     re.search(r"^[[:upper:]][[:lower:]]*$", t)): nillable = 1
            elif (self.options["F_MIXED"] and      # mIxED
                     re.search(r"^[[:alpha:]]+$", t)): nillable = 1
            elif (self.options["F_ALNUM"] and      # 4x4
                     re.search(r"\d", t) and re.search(r"\w", t)): nillable = 1
            elif (self.options["F_PUNCT"] and      # AT&T /^[#@]/ ?
                     re.search(r"[^-'.\w]", t)): nillable = 1
            if (nillable): tokens[i] = ""

        return(tokens)


###############################################################################
# Main
#
if __name__ == "__main__":
    def doOneFile(path0, fhandle, tok0):
        if (not args.quiet): print("Starting %s" % (path0))
        for rec in (fhandle.readlines()):
            tokens = tok0.tokenize(rec)
            print(rec)
            print(" | ".join(tokens))
        return

    def doSmokeTest(tok0):
        print("Using smoke-test data... (mostly just ASCII, though!)")
        testData = """
A line of words, to help test 1-horse natural-language systems.
Contractions it's good-luck in 2021 CE, 'til we're gonna add 'em.
Foreign languages' words--like d'jour; c'est la vie -- they matter.
Possessives, OTOH (are Dr. Alice's dog's thing (it can't think)).
People do weird things... with punctuation, like [bracket] and {brace}.
And weirder (like "this")!? -- see John Q. Smith & JRR Tolkien in a 4x4 on B&O.
Back in the 1920s (aka '20s) there were "only 2 numbers", then we invented 3.14,
[(which cost DARPA $200), and/or maybe $200M +/-1M]. We got 12% back
on April 2nd, 2005 at 2:31am. Some would say 2005/04/02 instead, that's A#1!
There are 25.4mm per inch, even for 6'5" people dense enough to
weigh 0.2E-12 solar masses, +/- 1, or ~1Tg or 3 -1/2 tonne (see #twitter).
See http://bit.ly/840284028#xyz or email me at foo@example.com.
Emoticons like :) and :( and :P are a pain, especially at sen-
tence end :). You get an A+ if on M*A*S*H c/o J.R.R. Tolkien (see section 1(a).12).
DNA sequences look like CCAGTTGTGTATGTCCACCC-3', while at 2 o'clock, ma'am, I'd've
seen substance(s) 8-hydroxydeoxyguanosine and 2,3,4-dihydrogen-monoxide.
Visit Lake Chargoggagoggmanchauggagoggchaubunagungamaugg.
"""
        for rec in (testData.split()):
            tokens = tok0.tokenize(rec)
            print("\n======= %s" % (rec))
            print(" | ".join(tokens))

        return


    ###########################################################################
    #
    import argparse
    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--heavy", action="store_true",
            help="Use HeavyTokenizer instead of SimpleTokenizer.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character set for input files. Default: utf-8.")
        parser.add_argument(
            "--nltk", action="store_true",
            help="Use NLTKTokenizerPlus instead of SimpleTokenizer.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E",
            help="Use this character set for output files.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
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
            "files",             type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()
    print("Testing...")

    if (args.heavy):
        print("Running HeavyTokenizer")
        tok = HeavyTokenizer()
        if (args.verbose): tok.setOption("TVERBOSE", 1)
    elif (args.nltk):
        print("Running NLTKTokenizerPlus")
        tok = NLTKTokenizerPlus()
    else:
        print("Running SimpleTokenizer")
        tok = SimpleTokenizer(verbose=args.verbose)

    if (len(args.files) == 0 or args.files[0] == "*"):
        doSmokeTest(tok)
    else:
        for path in args.files:
            fh0 = codecs.open(path, "rb", encoding=args.iencoding)
            doOneFile(path, fh0, tok)
            fh0.close()

    if (not args.quiet):
        print("Done.")
