=PYTHONLIBS=

This repository includes a bunch of Python libraries used by my other repos,
or generally useful (or at least, I think so).

==Short descriptions==

* BlockFormatter.py -- a drop-in replacement for the `argparse` formatters.
Python's default one wraps everything into one massive blob of text; and its
"Raw" one does no wrapping at all. BlockFormatter handles rudimentary but
very common conventions:

** blank lines are retained (say, between paragraphs)
** indented lines, or lines starting with *, #, =, etc. keep
the newline and whitespace before them.
** unindented lines get wrapped together with the preceding line,
and the whole block is indented to match the first line's indent (if any).
** by default, a 2-column hanging indent is adde to non-first lines of
indented blocks (beyond the indentation expressed by their first line). This
is so that list items flagged by "*" etc have clearer boundaries.
** The whole thing is wrapped to the current window width.

Try it, it makes argparse help much better. Also try MarkupHelpFormatter,
which works basically the same way, but has much better formatting.

* CharDisplay.py -- given a character code as 999, 0xFFFF, 0177, etc., show a
ton of information about that Unicode code point.

* ColorManager.py -- provides ANSI color control, interfaced via simple names
like red/white/bold (for bold red text on a white background).

* DictTuple.py -- A subclass of dict that provides a number of features from defaultdict
    and namedtuple as well. It can even enforce types for members, allow or
    prohibit None for members, etc.

* DomExtensions.py -- Everything you always wanted to have in DOM, but were afraid
to ask for. Has a method to monkey-patch it all onto a DOM implementation.

* ElementManager.py -- Manage an XML schema (very basic)

* EntityManager.py -- Manage XML data sources, catalogs, etc.

* Homogeneous.py -- Defines 'hlist' and 'hdict', subclasses of list and dict
that let you constrain values (and/or keys for hdict) to certain types and/or
values. Whether subclasses are ok, and whether None is ok, also controllable.

* LooseDict.py -- A subclass of dict, that lets you attach a "normalization"
function for keys. For example, specifying lower() gives you a case-ignoring
dictionary. Each entry stores both the normalized and (last-set) unnormalized key.

* MarkupHelpFormatter.py -- a limited text-formatter that can be attached to
Python argparse, so you can use MarkDown, MediaWiki, POD, etc. to get
formatted help. Makes heavy use of ANSI color and
Unicode variations for pretty formatting (you want bold italic sans serif,
or bold Fraktur, on your terminal? You got it. See also `ord --math`).

* PowerWalk.py -- A more flexible version of `os.walk`, that knows about
tar and zip files, filtering files by various criteria, etc.

* ReadAny.py -- meh

* RealDOM.py -- an implementation of DOM for Python. Renamed `BaseDom.py`, and
now moved to the XML/BINARY repo.

* SimplifyUnicode.py -- meh

* TabularFormats.py -- supports several "tabular" data formats, including many
variants of CSV. This started out as a port from Perl, but needs to be updated
so it sits on top of exiting Python libs where practical. See also `fsplit.py`.

* TabularFormats2.py -- in progress

* Tokenizer.py -- a very Unicode-aware word tokenizer for NLP work.

* TokensEN.py -- includable by Tokenizer.py to support English-specific stuff
like contractions.

* XMLConstructs.py

* XmlNlpLoad.py

* XmlOutput.py -- helps write well-formed XML with simple calls like
openElement(name, attrs), closeThroughElement(), escaping, queueAttribute(),
and so forth. Maintains a stack so you know if you break things.

* XmlTuples.py -- Supports a very simple, XML-conforming 3-element schema for
CSV-like data. Easily interconvertible with most any other such format.

* alogging.py -- a logging package, mostly upwardly compatible with the usual
Python one, but handy for managing color, -v style message levels,
auto-indentation, etc.

* argParsePP.py -- half-done upgrade to argparse, for easier support of
-x vs. --x, --no-x, and other conventions.

* fsplit.py -- a variation of Python's string `split()` method.
In brief, it supports all the options of
Python's `csv` package and string `split()` itself:
(escaping, quoting, doubling, lstrip, etc), as well as these options and more:

** Multi-character delimiters (split() but not csv offers those)
** More than one allowed quotechar (for example, single and double)
** Unicode quote characters (curly, angle, etc)
** Special character escapes like \xFF, \uFFFF, &#xFFFFF;, &bull;, etc.
** Option to ignore repeated delimiters
** Type-checking, auto-typing (field "3.14" returned as float, etc.)

* improvements.py -- notes and tweaks to split(), join(), listdir(). meh.

* markdownToXML.py -- what it says.

* mathAlphanumerics.py -- provides somewhat easier access to the very many alternate
Latin and Greek alphabets in Unicode, such as sans-serif bold. Many of these
are in the "Mathematical Alphanumeric Symbols" area, but other sets are
supported as well.

* sjdUtils.py -- very generally-applicable stuff, like indenting and escaping
and unescaping XML, JSON; making Unicode and control characters printable, etc.

