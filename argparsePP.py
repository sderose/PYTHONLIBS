#!/usr/bin/env python
#
# argparsePP.py: A slightly extended `argparse`.
# By Steven J. DeRose, started ~2014-06.
#
#pylint: disable=W0613, W0212, W0622
#
#from __future__ import print_function
import sys, os
import re
import argparse
import subprocess
import unicodedata

__metadata__ = {
    'title'        : "argParsePP.py",
    'description'  : "A slightly extended `argparse`.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2014-06",
    'modified'     : "2020-10-22",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=ArgumentParserPP=

An improved ArgumentParser and argparse:

* Hooks up BlockFormatter for better help formatting
* Adds a `showDefaults` option
* Adds a `shortMetavars` option
* Supports alternative hyphen conventions
* Supports adding 'toggle' attributes, with changeable '--no-' prefix (`add_toggle()`)
* Adds several useful attribute types, including ones useful with
Unicode, XSD, and other widely-used standards.
* Can automatically expand "choices" values to one-hot separate attributes
(`add_enum()`)
* Can ignore case for option names.


=Related Commands=

`argparse` [https://docs.python.org/3/library/argparse.html].


=Known bugs and limitations=

Unfinished.


=To do=

==More types==

* dict? works like append but add to a dict, with const value or serial num.
* tuples?
* XSD types via `Datatypes.py`
* type "type", that accepts defined type names.
* 'globbable'?
* IEEE that accepts +/- inf, NaN.
* Comparison args?  -xattr whereFrom=~/foo.bar/ or -xattr foo<=12
* Slice: take n:m where n>=0 and m>=n (or option with negatives)

==Other options==

* Option to group options into categories (so doc shows them in groups;
esp. useful for added groups like with PowerWalk.py).
* Ignore case
* append that does a split() then extend()?
* encoding (how to test if known?)
* folded string
* See 'condition' type?
* Add way to limit range for int and float (-zorkRange [1:20])
* Document 'anyInt' type
* entailment? setting x also changes y and z
* exclusion: can't set both x and y
* support minimum unique truncations for 'choices'.

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


### Numerics
#
def t_anyInt(s):
    """Accept octal, decimal, or hex.
    """
    try:
        return int(s, 0)
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_hInt(s):
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

def t_probability(s):
    try:
        f = float(s)
        if (f>=0.0 and f<=1.0): return f
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_percentage(s):
    """This is for percentages of a tangible things, that cannot go negative
    or over 100, or probabilities. Some percentages, like in finance,
    % change, can go wider -- just use float for those.
    """
    try:
        f = float(s.strip('% '))
        if (f>=0.0 and f<=100.0): return f
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_slice(s):
    """A span of integer indexes.
    """
    try:
        mat = re.match(r'(\d+):(\d+)', s)
        if (mat):
            fr = int(mat.group(1))
            to = int(mat.group(2))
            if (fr>=0 and to>=fr): return (fr, to)
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))


### Characters
#
def t_char(s):
    try:
        if (len(s) == 1): return s
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_ascii_char(s):
    try:
        assert len(s) == 1 and ord(s)>0 and ord(s)<256
        return s
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

def t_uchar(s):
    n = None
    mat = re.match(r'U\+([0-9a-fA-F]{1,5})$', s)
    if (mat):
        n = int(mat.group(1), 16)
    if (mat is None):
        try:
            n = int(s,0)
        except ValueError:
            pass
    n = ord(s[0])
    try:
        c = chr(n)
        return c
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))


### Normalized strings
#
def t_ustring(s):
    return s.upper()

def t_lstring(s):
    return s.lower()

def t_NFC(s):
    return unicodedata.normalize('NFC', s)

def t_NFD(s):
    return unicodedata.normalize('NFD', s)

def t_NFKC(s):
    return unicodedata.normalize('NFKC', s)

def t_NFKD(s):
    return unicodedata.normalize('NFKD', s)

# TODO: Add case-folding PLUS canonicalization?


### Constrained text items
#
def checkX(expr, s):  ### Regex checking feature
    if (re.match(expr, s, flags=re.UNICODE)): return s
    raise ValueError(genericMsg % (s))

def t_identifier(s):
    return checkX(r'[.\w][-_.:\w]*$', s)

dateX = r'\d\d\d\d-[01]\d-[0-3]\d$'
timeX = r'[012]\d:[0-5]\d(:[0-5]\d(\.\d+)?)?(Z|[-+]\d\d:\d\d)?$'

def t_date_8601(s):
    return checkX(dateX, s)

def t_time_8601(s):
    return checkX(timeX, s)

def t_datetime_8601(s):
    return checkX(dateX[0:-1]+'T' + timeX, s)


### XML and XSD stuff
#
NMSTART = r'[_.A-Z]'
NMCHAR  = r'[-_.:\w]'
NAME = NMSTART + NMCHAR + "*"   # Add Unicode!

def t_xml_lang(s):
    return checkX(r'\w{2,3}(\.\w{2,3})?$', s)

def x_NMTOKEN(s):
    if (s[0].isdigit()): raise ValueError(genericMsg % (s))
    return checkX(r'[.\w][-_.:\w]*$', s)


### Python stuff
#
def p_encoding(s):
    try:
        import codecs
        codecs.decode("", encoding=s)
        return s
    except ValueError:
        pass
    raise ValueError(genericMsg % (s))

pythonReservedWords = frozenset([
    'and', 'as', 'assert', 'async', 'await', 'break', 'class',
    'continue', 'def', 'del', 'elif', 'else', 'except', 'False',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in',
    'is', 'lambda', 'None', 'nonlocal', 'not', 'or', 'pass',
    'raise', 'return', 'True', 'try', 'while', 'with', 'yield',
])

def p_keyword(s):
    if (s in pythonReservedWords): return s
    raise ValueError(genericMsg % (s))

def p_identifier(s):
    if (s.isidentifier()): return s
    raise ValueError(genericMsg % (s))

def p_exception(s):
    if (s.isidentifier()):
        if (eval("issubclass(%s, Exception)")): return s
    raise ValueError(genericMsg % (s))

def p_class(s):
    if (s.isidentifier()):
        if (eval("type(%s) == type(str)")): return s
    raise ValueError(genericMsg % (s))

def p_type(s):
    if (s.isidentifier()):
        if (eval("isinstance(%s, type)")): return s
    raise ValueError(genericMsg % (s))


### XSD types (cf Datatypes.py)
#
import Datatypes
dt = Datatypes.Datatypes()

dt.checkValueForType("int", "12")


### Comparison types
# These let the user specify a condition for the code to apply.
# For example, `find` wants to check sizes, times, etc against some limit.
#     --mtime '<2020-03-12'
#     maybe append tolerance: ~3d
#     strings want regex compare: --name '/.txt$' (prefix '~', or just *do*?)
# Ones like -xattr need a name to compare:
#     -xattr 'whereFrom=~/example.com/' (too Perlish? =r''? ~=? ~?
#
def condition(s):
    pass


###############################################################################
#
class ArgumentParserPP(argparse.ArgumentParser):
    """Improved argparse. Mostly just like the regular one, however
    * adds a notion of boolean 'toggles'
    * automatic metavar shortening
    * default to use BlockFormatter.
    """
    def __init__(self,
        # argparse's usual options
        prog                    = None,
        usage                   = None,
        description             = None,
        epilog                  = None,
        parents                 = None,
        formatter_class         = None,
        prefix_chars            = '-',
        fromfile_prefix_chars   = None,
        argument_default        = None,
        conflict_handler        = 'error',
        add_help                = True,

        # Additions
        ignoreCase              = True,
        hyphenConvention        = "gnu",  # cf prefix_chars
        negationPrefix          = "no-",
        showDefaults            = True,
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
            prog                =    prog,
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
        name,
        *altNames,              # TODO implement
        action      = None,
        nargs       = None,
        const       = None,
        default     = None,
        typ         = None,
        choices     = None,
        required    = None,
        help        = None,
        metavar     = None,
        dest        = None
        ):
        basename = name.strip(' \t-_')
        if (self.showDefaults and default!=None):
            if (help==None): help=""
            help += " Default: " + str(default)
        if (metavar==None):
            metavar = basename.upper()
            if (self.shortMetavars):  metavar = metavar[0:1]
        if (dest==None): dest = re.sub('-', '_', basename)

        # For gnu style, always add '-' synonym for '--' form
        if (name.startswith("--") and self.gnuStyle):
            super.add_argument(
                 name           = name[1:],
                 action         = action,
                 nargs          = nargs,
                 const          = const,
                 default        = default,
                 type           = typ,
                 choices        = choices,
                 required       = required,
                 help           = help,
                 metavar        = metavar,
                 dest           = dest)

        return(super.add_argument(
            name            = name,
            action          = action,
            nargs           = nargs,
            const           = const,
            default         = default,
            type            = typ,
            choices         = choices,
            required        = required,
            help            = help,
            metavar         = metavar,
            dest            = dest)
        )

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
        name        = None,  # name without "no-" or similar part
        default     = None,
        help        = None,
        metavar     = None,
        dest        = None
        ):
        """Add both sides of an invertible boolean option. This method:
            Adds the named option with action='store_true'
            Adds the opposite option with action='store_true':
                Uses negationPrefix to name it, such as '--no-' + name
                Makes up as cross-reference as help.
                Applies the same default, dest, and metavar.
        """
        if (not name.startswith("--")):
            sys.stderr.write("add_toggle: option doesn't start with '--'.")
            return
        basename = name.strip(' \t-_')
        pos = self.add_argument(name,
            action='store_true', dest=name[2:], metavar=metavar,
            default=default, help=help)
        self.add_argument(self.negationPrefix+basename,
            action='store_false', dest=dest or basename, metavar=metavar,
            default=default, help="See '"+name+"'.")
        return pos

    def add_enum(
        self,
        basename    = "",
        typ         = str,
        default     = None,
        help        = None,
        metavar     = None,
        dest        = None,
        choices     = None
        ):
        self.add_argument(
            '--'+basename, typ=typ,
            default=default,
            help=help,
            metavar=metavar,
            dest=dest or basename,
            choices=choices
            )
        for c in choices:
            self.add_argument(
                '--'+c, action='store_const', const=c,
                help=("Shorthand for '--%s %s'." % (basename, c)),
                dest=dest or basename
                )


    def add_entailment(self, name1, name2, value2):
        """Store the fact that setting one option, forces another one.
        The actual forcing has to be done via parser_arguments().
        """
        if (name1 not in self.entailments):
            self.entailments[name1] = []
        self.entailments[name1] = (name2, value2)

    #    Rfile = argparse.FileType('r')
    #    Wfile = argparse.FileType('w')

    def print_help(self, file=None):
        """Override argparse version, to respond to 'pager' option.
        """
        if (self.pager == "less"):
            subprocess.run([ "/usr/bin/less" ],
            input=self.format_help(), check=True)
        else:
            super.print_help(file=file)


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
            "--color",  # Don't default. See below.
            help='Colorize the output.')
        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--ignoreCase", "-i", action='store_true',
            help='Disregard case distinctions.')
        parser.add_argument(
            "--oencoding",        type=str, metavar='E',
            help='Use this character set for output files.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--recursive",        action='store_true',
            help='Descend into subdirectories.')
        parser.add_argument(
            "--tickInterval",     type=t_anyInt, metavar='N', default=10000,
            help='Report progress every n records.')
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
        if (args0.color == None):
            args0.color = ("USE_COLOR" in os.environ and sys.stderr.isatty())
        #lg.setColors(args0.color)
        #if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)

    ###########################################################################
    #
    fileCount = 0
    args = processOptions()

    print("Driver not yet implemented.")
