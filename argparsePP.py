#!/usr/bin/env python3
#
# argparsePP.py: An extended `argparse`.
# By Steven J. DeRose, started ~2014-06.
#
#pylint: disable=W0613, W0212, W0622, W0123
#
import sys
import os
import re
import argparse
import subprocess
from unicodedata import normalize

import Datatypes  # Support for XSD types

__metadata__ = {
    "title"        : "argParsePP",
    "description"  : "An extended `argparse`.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2014-06",
    "modified"     : "2020-10-22",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=ArgumentParserPP=

An improved ArgumentParser and argparse:

* Hooks up BlockFormatter for better help formatting
* Adds a `showDefaults` option
* Adds a `shortMetavars` option
* Supports alternative hyphen conventions (option to auto-alias "--long-form" vs. "--longform"
* Supports adding "toggle" attributes, with changeable "--no-" prefix (`add_toggle()`)
* Adds several attribute types, including ones useful with
Unicode, XSD, and other widely-used standards
* Can automatically expand "choices" values to one-hot separate attributes (`add_enum()`)
* Can ignore case for option names, choices values.
* Option to auto-shorten metavars


=Related Commands=

`argparse` [https://docs.python.org/3/library/argparse.html].


=Known bugs and limitations=

Unfinished.


=To do=

==Top==

* Option to pipe to $PAGER.
* Auto hyphen/underscore convention
* Auto shortening of metavars
* toggles
* Arg that takes 2 following values, or a name=value pair?

==Misc==

* Option to accept aliases that add/subtract internal hyphens/underscores
(maybe use my LooseDict.py).
* Option to suppress an argument(s) from having their help displayed
with default `-h`.
Esp. useful for imported args, like PowerWalk.py's.
Perhaps hide them under a secondary command, such as --help-all.
* Add an option to write out a zsh auto-completion file.

==More types==

* braced group? paren/brack/brace, goes to balance (mod \\)
* dict? works like append but add to a dict, with const value or serial num.
* tuples?
* XSD types via `Datatypes.py`
* type "type", that accepts defined type names.
* "globbable"?
* IEEE that accepts +/- inf, NaN.
* Comparison args?  -xattr whereFrom=~/foo.bar/ or -xattr foo<=12
Possibly allow .lt. etc; certainly allow Unicode symbols.
* Slice: take n:m where n>=0 and m>=n (or option with negatives)
* token accumulator: repeatable option, but you can either do `-x foo -x bar`,
or `-x "foo bar"`, or mix the two.
* string with \\-codes expanded
* -exec support: takes a command (test -x), and '{}' fill-in. Maybe adds a standard
arg to redefine the '{}' string?

==Types for files/paths==

===What is a sensible set of cases?===
    * File that exists (input)
    * Dir that exists (output)
    * Dir exists, but actual file doesn't yet exist there (maybe "!" to force?)
    * If file exists but is to be written:
        ** Append; inquire; append serial number; skip;
===Other factors===
    * Permission? Stdin/stdout? PAGER?
    * Plurals/globs?
    * Output file copy name (but not extension?) of current input file

==Expressions?==

Some (hopefully cleaner?) way to do logic, a bit like `find`. say,
parentheses, boolean ops, and comparisons, where identifiers get resolved
by a callback. But this really needs lazy evaluation -- you can only evaluate
`find`-like conditions on a file-by-file basis.

Issues:
    * case and regex comparison
    * case for `choices` values
    * support case-ignore and unique-abbrevs for enums (see `LooseDict.py`)
    * set operations
    * date/time facilities
    * check identifiers at parsetime, but eval later?
    * indicate which are per-file evals?
    * date differences like recency

    --include = "(type='d' and size>12E+6 and (ext in [ 'foo', 'bar' ]))"

    do this with just eval, after subbing in all the vars.
    usual question of how to signal interpolation.

    This probably also requires maintaining order of args.


==Other options==

* Way to make one shorthand option set 2 others, e.g. PowerWalk's --quote
to set --openQuote and --closeQuote.
* Option to group options into categories (so doc shows them in groups;
esp. useful for added groups like with PowerWalk.py).
* Ignore case
* append that does a split() then extend()?
* encoding (codecs.lookup(encoding))
* folded string
* See 'condition' type?
* Add way to limit range for int and float (-zorkRange [1:20])
* Document 'anyInt' type
* entailment? setting x also changes y and z
* exclusion: can't set both x and y
* support minimum unique truncations for "choices".
* "union" or "no dups but ordered", rather than "append"
* repeatable option, where instance can also be split, like -x "1 2 3" -x 4.

* method to add synonym to previously-defined option
* option for output to $PAGER (incl. links when possible? or should all
that go into BlockFormatter?). The printing in argparse goes through:

    def print_usage(self, file=None):
        if file is None:
            file = _sys.stdout
        self._print_message(self.format_usage(), file)

    def print_help(self, file=None):
        if file is None:
            file = _sys.stdout
        self._print_message(self.format_help(), file)

    def _print_message(self, message, file=None):
        if message:
            if file is None:
                file = _sys.stderr
            file.write(message)


=History=

* 2004-06 Written by Steven J. DeRose.
* 2020-08-28ff: Clean up doc. Start improving toggle attributes,
and make entailments automatic.
* 2020-10-22: Add types for class, type, exception, hInt, slice, datetime,
keyword, identifier.
Fix percentage.


=Rights=

Copyright 2004-06 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
# New types
# https://docs.python.org/3/library/argparse.html#type
#

genericMsg = "Value for option does not match type: '%s'."


###############################################################################
### Numerics
#
def t_anyInt(s:str):
    """Accept octal, decimal, or hex.
    Possibly also accept NaN, Inf, -Inf, -0...
    """
    try:
        return int(s, 0)
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_hInt(s:str):
    """Accept rank suffixes for Kilo, Mega, etc.
    """
    try:
        loc = "KMGTP".find(s[-1])
        if (loc < 0): factor = 1
        else: factor = 1000**(loc+1)
        return int(s[0:-1], 0) * factor
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_probability(s:str):
    """Floating point number between 0.0 and 1.0.
    Yeah, I know, roundoff error.
    """
    try:
        f = float(s)
        if (f>=0.0 and f<=1.0): return f
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_percentage(s:str):
    """This is for percentages of a tangible things, that cannot go negative
    or over 100, or probabilities. Some percentages, like in finance,
    % change, can go wider -- just use float for those.
    """
    try:
        f = float(s.strip("% "))
        if (f>=0.0 and f<=100.0): return f
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_slice(s:str):
    """A span of integer indexes.
    """
    try:
        mat = re.match(r"(\d+):(\d+)", s)
        if (mat):
            fr = int(mat.group(1))
            to = int(mat.group(2))
            if (fr>=0 and to>=fr): return (fr, to)
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))


###############################################################################
### Characters
# TODO: Sync with Python's set of islower() etc, plus length constraints
#
def t_char(s:str):
    """A single, literal Unicode character.
    """
    try:
        if (len(s) == 1): return s
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_ascii_char(s:str):
    """A single Unicode character, not including NUL.
    """
    try:
        assert len(s) == 1 and ord(s)>0 and ord(s)<256
        return s
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_uchar(s:str):
    """A single Unicode character, specified as any of:
        * a literal (a shell may already expand some \\-codes before we see them)
        * a hex/dec/oct code point
        * U+xxxx
        * TODO: an HTML entity name
    Ick. Single digit is ambiguous. Take it as literal.
    """
    if (len(s)==1): return s                        # Literal single char
    n = None
    mat = re.match(r"U\+([0-9a-fA-F]{1,5})$", s)    # U+xxxxx
    if (mat):
        n = int(mat.group(1), 16)
    if (mat is None):
        try:
            n = int(s, 0)
        except ValueError:
            pass
    n = ord(s[0])                                   # Int in whatever base
    try:
        c = chr(n)
        return c
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))              # Fail


###############################################################################
### Normalized strings. This means that the string is normalized before storing,
# not that a non-normalized string from the user is rejected (they're named like
# the Python string-transformer functions to make that more intuitive).
#
def t_upper(s:str):
    return s.upper()

def t_lower(s:str):
    return s.lower()

def t_title(s:str):
    return s.title()

def t_NFC(s:str):
    return normalize("NFC", s)

def t_NFD(s:str):
    return normalize("NFD", s)

def t_NFKC(s:str):
    return normalize("NFKC", s)

def t_NFKD(s:str):
    return normalize("NFKD", s)

# TODO: Add case-folding PLUS canonicalization?



###############################################################################
### Regex-constrained text items
# Only do this if significantly easier than:
#     add_argument("--foo", type=lambda x: re.match(r"whatev(er|uh)", x)...)
# Perhaps:
#     add_argument("--foo", type=match, const=r"whatev(er|uh)")
# TODO: What of regex options, esp. IGNORECASE and UNICODE?
#
def checkRegex(expr, s:str):
    if (re.match(expr, s, flags=re.UNICODE)): return s
    raise ValueError(genericMsg % (s))

def isRegex(s:str):
    """Test for an arg which is itself a legit regular expression.
    """
    try:
        re.compile(s)
        return s
    except re.error:
        return None

# Following only allow complete date and/or time, not arbitrary shortenings.
# TODO: Add support for the ISO-allowed truncations.
#
dateX = re.compile(r"\d\d\d\d-[01]\d-[0-3]\d" + "$")
timeX = re.compile(r"[012]\d:[0-5]\d(:[0-5]\d(\.\d+)?)?(Z|[-+]\d\d:\d\d)?" + "$")

# These allow optional parts
#datePX = re.compile(r"(\d\d\d\d)(-[01]\d)?(-[0-3]\d)?" + "$")
#timePX = re.compile(r"([012]\d)(:[0-5]\d)?((:[0-5]\d)(\.\d+))?)?(Z|[-+]\d\d:\d\d)?" + "$")
def t_date_8601(s:str):
    return checkRegex(dateX, s)

def t_time_8601(s:str):
    return checkRegex(timeX, s)

def t_datetime_8601(s:str):
    return checkRegex(dateX[0:-1]+"T"+timeX, s)


###############################################################################
### XML and XSD stuff
#
NMSTART = r"[_.A-Z]"
NMCHAR  = r"[-_.:\w]"
NAME = NMSTART + NMCHAR + "*"   # Add Unicode! Cf. XML/PARSERS/XmlRegexes.py.

def t_xml_lang(s:str):
    return checkRegex(r"\w{2,3}(\.\w{2,3})?$", s)

def x_NMTOKEN(s:str):
    if (s[0].isdigit()): raise ValueError(genericMsg % (s))
    return checkRegex(r"[.\w][-_.:\w]*$", s)

def x_QNAME(s:str):
    if (s[0].isdigit()): raise ValueError(genericMsg % (s))
    return checkRegex(r"[.\w][-_.:\w]*$", s)


###############################################################################
### Python stuff
#
def p_encoding(s:str):
    try:
        import codecs
        codecs.decode("", encoding=s)
        return s
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

pythonReservedWords = frozenset([
    "and", "as", "assert", "async", "await", "break", "class",
    "continue", "def", "del", "elif", "else", "except", "False",
    "finally", "for", "from", "global", "if", "import", "in",
    "is", "lambda", "None", "nonlocal", "not", "or", "pass",
    "raise", "return", "True", "try", "while", "with", "yield",
])

def p_keyword(s:str):
    import keyword
    if (keyword.iskeyword(s)): return s
    #if (s in pythonReservedWords): return s
    raise ValueError(genericMsg % (s))

def p_identifier(s:str):
    if (s.isidentifier()): return s
    raise ValueError(genericMsg % (s))

def p_exception(s:str):
    if (s.isidentifier()):
        if (eval("issubclass(%s, Exception)")): return s
    raise ValueError(genericMsg % (s))

def p_class(s:str):
    if (s.isidentifier()):
        if (eval("type(%s) == type(str)")): return s
    raise ValueError(genericMsg % (s))

def p_type(s:str):
    if (s.isidentifier()):
        if (eval("isinstance(%s, type)")): return s
    raise ValueError(genericMsg % (s))


### XSD types (cf Datatypes.py)
#
dt = Datatypes.Datatypes()

dt.checkValueForType("int", "12")


### File-system stuff
#
# Nonextant but writable
# extant file (poss. with various properties or test callback)
# extant dir
# basename
# extension (no .)

###############################################################################
#
class ArgumentParserPP(argparse.ArgumentParser):
    """Improved argparse. But main diffs:
        * A bunch of pre-defined types, including boolean toggles
        * Better help, incl. formatter, short metavars, exclude-from-summary
        * Auto-aliasing to cover Gnu vs. Posix hyphenation, etc.
        * 'choices' can be case-insensitive
    """
    def __init__(self,
        # argparse's usual options
        prog                    = None,
        usage                   = None,
        description             = None,
        epilog                  = None,
        parents                 = None,
        formatter_class         = None,
        prefix_chars:str        = "-",
        fromfile_prefix_chars   = None,
        argument_default        = None,
        conflict_handler        = "error",
        add_help                = True,

        # Additions (see the --help)
        ignoreCase              = True,
        hyphenConvention:str    = "gnu",  # cf prefix_chars
        negationPrefix:str      = "no-",
        showDefaults:bool       = True,
        shortMetavars           = True,
        pager                   = None,
        gnuStyle                = True,
        entailments             = None
        ):

        if (formatter_class is None):
            try:
                from BlockFormatter import BlockFormatter
                self.formatter_class = BlockFormatter
            except ImportError:
                pass

        self.ignoreCase         = ignoreCase
        self.hyphenConvention   = hyphenConvention
        self.negationPrefix     = negationPrefix
        self.showDefaults       = showDefaults
        self.shortMetavars      = shortMetavars
        self.pager              = {}
        self.gnuStyle           = False
        self.entailments        = {}

        super(ArgumentParserPP, self).__init__(
            prog                = prog,
            usage               = usage,
            description         = description,
            epilog              = epilog,
            parents             = parents,
            formatter_class     = formatter_class,
            prefix_chars        = prefix_chars,
            fromfile_prefix_chars = fromfile_prefix_chars,
            argument_default    = argument_default,
            conflict_handler    = conflict_handler,
            add_help            = add_help
        )

    def add_argument(
        self,
        *theArgs,              # TODO Finish...
        **kwargs
        ):
        """
        action      = None,
        nargs       = None,
        const       = None,
        default     = None,
        type        = None,
        choices     = None,
        required    = None,
        help        = None,
        metavar     = None,
        dest        = None
        """
        basename = theArgs[0].strip(" \t-_")
        if (self.showDefaults and kwargs["default"] is not None):
            if (kwargs["help"] is None): help=""
            help += " Default: " + str(kwargs["default"])
        if (kwargs["metavar"] is None):
            kwargs["metavar"] = basename.upper()
            if (self.shortMetavars):
                kwargs["metavar"] = kwargs["metavar"][0:1]
        if (kwargs["dest"] is None):
            kwargs["dest"] = re.sub("-", "_", basename)

        # For gnu style, always add "-" synonym for "--" form
        if (theArgs[0].startswith("--") and self.gnuStyle):
            super().add_argument(theArgs, kwargs)
        return super().add_argument(theArgs, kwargs)

    def showSettings(self):
        """Display the args with types and values.
        """
        print("Args:\n%s")
        argDict = self.__dict__  # TODO: Check
        for k0 in sorted(argDict.keys()):
            print("    %-20s %-12s %s" %
                (k0, type(argDict[k0]).__name__, argDict[k0]))
        return

    def add_toggle(
        self,
        name:str    = None,  # name without "no-" or similar part
        default     = None,
        help:str    = None,
        metavar:str = None,
        dest:str    = None
        ):
        """Add both sides of an invertible boolean option. This method:
            Adds the named option with action="store_true"
            Adds the opposite option with action="store_true":
                Uses negationPrefix to name it, such as "--no-" + name
                Makes up as cross-reference as help.
                Applies the same default, dest, and metavar.
        """
        if (not name.startswith("--")):
            sys.stderr.write("add_toggle: option doesn't start with '--'.")
            return
        basename = name.strip(" \t-_")
        pos = self.add_argument(
            name,
            action="store_true",
            dest=name[2:],
            metavar=metavar,
            default=default,
            help=help
        )
        self.add_argument(
            self.negationPrefix+basename,
            action="store_false",
            dest=dest or basename,
            metavar=metavar,
            default=default,
            help="See '"+name+"'."
        )
        return pos

    def add_enum(
        self,
        basename:str = "",
        type         = str,
        default      = None,
        help         = None,
        metavar      = None,
        dest         = None,
        choices      = None
        ):
        """Add the given argument, with a set of `choices`. In addition, add each
        choice as a separate argumnt of its own, that just sets this one.

        This has the side-effect that you can give them regardless of case,
        and/or as minimum-unique abbreviations.
        The caller is responsible for avoiding conflicts.
        """
        self.add_argument(
            "--"+basename,
            type=type,
            default=default,
            help=help,
            metavar=metavar,
            dest=dest or basename,
            choices=choices
        )
        for c in choices:
            self.add_argument(
                "--"+c,
                action="store_const",
                const=c,
                help=("Shorthand for '--%s %s'." % (basename, c)),
                dest=dest or basename
            )

    def add_entailment(self, name1:str, name2:str, value2):
        """Store the fact that setting one option, forces another one.
        The actual forcing has to be done via parser_arguments().
        """
        if (name1 not in self.entailments):
            self.entailments[name1] = []
        self.entailments[name1] = (name2, value2)

    #    Rfile = argparse.FileType("r")
    #    Wfile = argparse.FileType("w")

    def print_help(self, file=None):
        """Override argparse version, to respond to "pager" option.
        """
        if (self.pager == "less"):
            subprocess.run(
                [ "/usr/bin/less" ],
                input=self.format_help(),
                check=True
            )
        else:
            super().print_help(file=file)


###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        """I'm so meta, even this acronym...
        """
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--color", # Don't default. See below.
            help="Colorize the output.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character set for input files. Default: utf-8.")
        parser.add_argument(
            "--ignoreCase", "-i", action="store_true",
            help="Disregard case distinctions.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E",
            help="Use this character set for output files.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--recursive", action="store_true",
            help="Descend into subdirectories.")
        parser.add_argument(
            "--tickInterval", type=t_anyInt, metavar="N", default=10000,
            help="Report progress every n records.")
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
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        if (args0.color is None):
            args0.color = ("CLI_COLOR" in os.environ and sys.stderr.isatty())
        #lg.setColors(args0.color)
        #if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)

    ###########################################################################
    #
    fileCount = 0
    args = processOptions()

    print("Driver not yet implemented.")
