#!/usr/bin/env python3
#
# ColorManager.py: ANSI color utilities for Python, by Steven J. DeRose.
# 2011-12-09: sjdUtils Ported to Python; 2016-10-31 ColorManager separated.
#
import sys
import os
import re
from typing import Union

__metadata__ = {
    'title'        : "ColorManager",
    'description'  : "ANSI terminal color utilities.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2011-12-09",
    'modified'     : "2021-07-01",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

Provide relatively easy access to ANSI terminal colors. For example,
colorize a string using a color name such as "blue/white/bold", remove
all color escapes, change ANSI color to represent via HTML,
measure the character length of a string while
disregarding color escapes, etc.

==Color names==

Color names are of the form ''foreground/background/effect'', with all
items optional. For example:

    red/italic produces red italic text on default background
    /blue/bold produces default foreground color but bold, on blue background (broken)
    yellow/black/underline produces underscored yellow text on black background

The colors are: "black", "red", "green", "yellow",
"blue", "magenta", "cyan", "white", "default".

The effect names are as shown below, but support varies widely from one
terminal program to another:
    "bold" (aka 'bright'),
    "faint",
    "italic" (rare),
    "underline",
    "blink",
    "fblink" (aka 'fastblink' (rare)),
    "reverse" (aka 'inverse'),
    "concealed" (aka 'invisible' or 'hidden'),
    "strike" (aka 'strikethru' or 'strikethrough'),
    "plain" (no special effect)

Prefix "!" to an effect name to turn it off, but some terminals may not support that.

Names passed as arguments are forced to lower-case before lookup.

For detailed information on the color-name conventions, see `colorNames.md`.
For information on the ANSI codes, see for example
[https://en.wikipedia.org/wiki/ANSI_escape_code].

==Usage from Python==

    from ColorManager import ColorManager
    cm = ColorManager()
    ...
    print(cm.colorize(myMessage, "red/white")

==Usage from shell==

* ColorManager.py --color 'red/blue' --text 'Spam, spam, eggs, and spam.'

Display the `text` in the specified `color`.

* ColorManager.py --showAll

Display a list of all the available color names.

* ColorManager.py --uncolorize

Copy stdin to stdout, but removing any color escapes.

* ColorManager.py --testEffects

Show samples with the supported effects, which is a good way to see which ones
your terminal programs supports (currently has problems...)


=Methods=

* '''__init__(effects=None)'''

Set up the color manager.
See ''setupColors()'' re. how to use ''effects''.

* '''setupColors(effects=None)'''

(iternal) Work out all known color, effect, and combination names, and
put them in a hash that maps them to their escape sequences.
If 'effects' is not None, it must be a list of the effect names
to include. That list may be empty.

* '''addColor(newName, oldName)'''

Adds a synonym for an existing color.

* '''isColorName(name)'''

Returns True iff ''name'' is a known color name (fg/bg/ef)

* '''getColorString(name)'''

Returns the ANSI terminal escape string to switch to the named color.

* '''getColorStrings(paramColor, defaultColor)'''

Returns a dict mapping color names (such as "red/white") to
the ANSI terminal escape strings needed to achieve them.

* '''tostring(sampleText='sample', filter=None)'''

Obsolete.

Return a printable buffer with one line for each defined color name.
Each line consist of colorized ''sampleText'' and then the color name.

If ''filter'' is supplied, it is treated as a regular expression, and any
color names that do not match it are excluded. This is useful because
there are about 1000 combinations available.

* '''colorize(msg="", argColor='red', endAs="off")'''

Return the string ''msg'', but with
the ANSI terminal escape sequences to display it in the specified
''argColor'' added at the start, and the escape to switch to color ''endAs''
added at the end.

* '''uncolorize(s)'''

Remove any ANSI terminal color escapes from ''s''.

* '''uncoloredLen(s)'''

Return the length of ''s'', but ignoring any ANSI terminal color strings.
This is just shorthand for `len(uncolorize(s))`.

* '''color2Html(s)'''

(experimental) Map color escapes to HTML. This should work fine for simple
cases, but it might come out odd if you have multiple color-changes in a row.
That's because ANSI color just switches (possibly to 'default', but that's just
another change), while HTML components push and pop the state.


=Known bugs and limitations=

If you ''colorize''() a string, it resets the color to default at the end.
Thus, if you insert colorized string A within colorized string B, the portion
of B following A will ''not'' be colorized; if B was already colorized, the
trailing portion will likewise not be colorized.
You can specify the ''endAs'' option when colorizing A to avoid this.

ColorManager has no support (yet) for 256-color terminals.


=To do=

* Resync Perl version.

* Make color names localizable.

* Consider additional ANSI codes
([https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters]):

* Primary and alternate fonts (see `mathAlphanumerics.py`).

* Perhaps allow RGB colors like CSS?
    0 black   -- #000
    1 red     -- #F00
    2 green   -- #0F0
    3 yellow  -- #FF0
    4 blue    -- #00F
    5 magenta -- #F0F
    6 cyan    -- #0FF
    7 white   -- #FFF


=Related commands=

There is a Perl version in `ColorManager.pm`,
and there are command-line wrappers in `uncolorize` and `colorstring`.

My `hilite` uses that Perl version, and lets you specify any number of regexes
with colors to highlight their matches in.

There is some similar functionality for zsh and bash in my `ShellSetup/setupColors`,
and very basic shell functions such as `echoc` and `makeColorEscape`
in `ShellSteup/-setupTracing`.

My [https://github.com/sderose/Color.git/blob/master/uncolorize] is a wrapper
for some `ColorManager.py` functionality.

Pypi has an `ansicolors` package (by Jonathan Eunice) at
[https://pypi.org/project/ansicolors/] which is similar to this.

See [https://stackoverflow.com/questions/287871] on "How to print colored text
in terminal in python." It references Python modules ''termcolor'' (apparently
no longer maintained?), ''chromalog'', ''Colorama'', and others.

For information on the codes themselves, see for example
[https://en.wikipedia.org/wiki/ANSI_escape_code].


=History=

* 2011-12-09: `sjdUtils` port from Perl to Python by Steven J. DeRose.
* 2016-10-31: Split `ColorManager.py` out of `sjdUtils.py`.
* 2018-09-04: Make basic tables accessible. Simplify string construction.
Add test feature as main.
* 2018-10-22: Catch `KeyError` on color names.
* 2020-09-16ff: Add separate fg, bg, effect args for `colorize()`.
Clean up doc. Move effects to end, not beginning per ColorNames.md.
* 2020-11-24: Clean up and describe command-line usage. Add `--uncolorize` and
`--testEffects`. Make `--text` and stdin work the same way.
* 2020-12-14: Start support for HTML output.
* 2021-07-01: Sync args to `colorize()` with `colorstring.py`.
* 2023-05-16: Factor out color-name parsing. Not used yet.

=Rights=

Copyright 2011-12-09 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].


=Options=
"""

def warning(msg: str) -> None:
    sys.stderr.write(msg+"\n")


###############################################################################
#
class ColorManager:
    """This class provides access to a wide range of ANSI terminal control
    strings for setting colors. It knows about foreground and background
    colors, combinations, and the addition of many effects. It follows
    a simple naming convention to get all available combinations.
    Notes:
        Few terminals support all of the effects, and this doesn't check.
        There is no support for 256 color terminals.
    """
    numbers2Names = {}  # Set up only if needed

    colorNumbers = {  # +30 for foreground, +40 for background
        "black"   : 0,
        "red"     : 1,
        "green"   : 2,
        "yellow"  : 3,
        "blue"    : 4,
        "magenta" : 5,
        "cyan"    : 6,
        "white"   : 7,
        "default" : 9,
    }

    effectNumbers = {  # +0 to turn on, +20 to turn off
        "bold"       : 1,
        "faint"      : 2,
        "italic"     : 3,
        "underline"  : 4,
        #"blink"      : 5,
        #"fblink"      :6,
        "reverse"    : 7,
        "concealed"  : 8,
        "strike"     : 9,
    }

    offNumbers = {
        #"default"    : 0,
        "off"        : 0,
    }

    def __init__(self, effects=None):
        self.colorizeXmlContentExpr = re.compile(r'>(.*?)<')
        self.colorRegex = re.compile(r'\x1b\[\d+(;\d+)*m')
        self.offColor = chr(27) + "[m"  # ANSI to turn off colors
        self.setupColors(effects=effects)

    def parseColorName(self, name:str) -> (str, str, str):  # TODO: Integrate this
        """Parse up a long color name such as "red/blue/!italic".
        Return the normalized (lowe-case) names, in a tuple of (fg, bg, ef).
        The effect (only) may have a prefixed "!" for negation (which stays).
        """
        tokens = name.lower().split("/")
        if (len(tokens) > 3): return (None, None, None)
        fg = bg = ef = None
        for token in tokens:
            # Assign to right item of (fg, bg, ef)
            if (token in self.effectNumbers or
                (token.startswith("!") and token[1:] in self.effectNumbers)):
                if (ef is not None):
                    warning("Too many effects: '%s' and '%s'." % (ef, token))
                    return (None, None, None)
                ef = token
            elif (token in self.colorNumbers):
                if (bg is not None):
                    warning("Too many colors: '%s', '%s', '%s'." % (fg, bg, token))
                    return (None, None, None)
                elif (fg is not None):
                    bg = token
                else:
                    fg = token
            elif (token == ""):
                if (fg is not None):
                    warning("Unexpected empty token.")
                    return (None, None, None)
                fg = ""
            else:
                warning("Unrecognized color or effect name: '%s'." % (token))
                return (None, None, None)
        return (fg, bg, ef)

    def setupColors(self, effects: Union[bool, list] = None):
        """Work out all known color, effect, and combination names, and
        put them in a hash that maps them to their escape sequences.
        If 'effects' is not None, it must be either True (to enable all
        known effect names), or a list of the effect names
        to include, as defined in 'effectNumbers' below.
        """
        #nc = os.popen("tput colors").read()
        #if ((not nc) or int(nc) < 8):
        #    warning("Color not supported? 'tput colors' says '%s'." % (nc))
        self.colorStrings = {}


        # Be nice to blink-sensitive folks
        if ('NOBLINK' not in os.environ):
            ColorManager.effectNumbers["blink"] = 5
            ColorManager.effectNumbers["fblink"] = 6

        if (isinstance(effects, list) and len(effects)):
            for k in ColorManager.effectNumbers.keys():
                if (k not in effects): del ColorManager.effectNumbers[k]

        eb = chr(27) + "["
        fmt2 = "%s%d;%dm"

        try:
            self.colorStrings["default"] = eb + "m"  # TODO: Check

            for c in ColorManager.offNumbers:
                cn = ColorManager.offNumbers[c]
                self.colorStrings[c] = eb + str(0 +cn) + "m"

            for e in ColorManager.effectNumbers:
                en = ColorManager.effectNumbers[e]
                self.colorStrings[e]     = eb + str(0 +en) + "m"
                self.colorStrings["!"+e] = eb + str(20+en) + "m"

            for c in ColorManager.colorNumbers:
                cn = ColorManager.colorNumbers[c]
                self.colorStrings[c]     = "%s%dm" % (eb, 30+cn)
                self.colorStrings["/"+c] = "%s%dm" % (eb, 40+cn)
                for e in ColorManager.effectNumbers:
                    en = ColorManager.effectNumbers[e]
                    self.colorStrings[c+"/"+e]   = fmt2 % (eb, en,    30+cn)
                    self.colorStrings[c+"//"+e]  = fmt2 % (eb, en,    40+cn)
                    self.colorStrings[c+"/!"+e]  = fmt2 % (eb, 20+en, 30+cn)
                    self.colorStrings[c+"//!"+e] = fmt2 % (eb, 20+en, 40+cn)

                for c2 in ColorManager.colorNumbers:
                    c2n = ColorManager.colorNumbers[c2]
                    self.colorStrings[c+"/"+c2] = (
                        fmt2 % (eb, 30+cn, 40+c2n))
                    for e in ColorManager.effectNumbers:
                        en = ColorManager.effectNumbers[e]
                        self.colorStrings[c+"/"+c2+"/"+e] = (
                            "%s%d;%d;%dm" % (eb, en, 30+cn, 40+c2n))
        except KeyError as err:
            warning("KeyError in color setup: %s\n" % (err))
        return

    def addColor(self, newName: str, oldName: str) -> bool:
        """Add `newName` to the color table, so it can be passed to ''vMsg''.
        It becomes a synonym for ''oldName'' (any previous ''newName''
        is replaced, but ''oldName'' remains).
        """
        newName = newName.lower()
        oldName = oldName.lower()
        try:
            self.colorStrings[newName] = self.colorStrings[oldName]
        except KeyError:
            return(False)
        return(True)

    def isColorName(self, name: str) -> bool:
        name = name.lower()
        return(bool(name in self.colorStrings))

    def getColorString(self, name: str) -> str:
        """Return the ANSI escape sequence to obtain the named color.
        Raises KeyError if color name is not known.
        """
        name = name.lower()
        try:
            return(self.colorStrings[name])
        except KeyError as e:
            warning("ColorManager: Unknown name '%s':\n    %s" %
                (name, e))
            return ""

    def getColorStrings(self) -> dict:
        """Return the dict of all known color names and escape strings.
        """
        return(self.colorStrings)

    def tostring(self, sampleText: str = 'sample', filterRegex: str = None) -> str:
        buf = ""
        for k in sorted(self.colorStrings.keys()):
            if (filterRegex and not re.match(filterRegex, k)): continue
            buf += "    %s  %s\n" % (self.colorize(sampleText, k), k)
        return(buf)

    def colorize(self, msg: str = "", argColor: str = None, endAs: str = "off",
        fg:str='', bg:str='', effect:str='') -> str:
        """If color is enabled, surround `string` with the escape sequences
        needed to put it in the specified color (assuming the name is known).
        The color may be specified either by;
            argColor: A full name, such as "red" or "red/blue/bold", or
            fg="red", bg="blue", effect="bold"
        `endAs` is the color that will be changed to at the end.
        """
        endAs = endAs.lower()
        if (endAs in self.colorStrings):
            endEsc = self.colorStrings[endAs]
        else:
            endEsc = ""  # TODO: Warn or assert or something....
        if (not argColor):
            argColor = fg
            if (bg): argColor += "/" + bg
            if (effect): argColor += "/" + effect
        argColor = argColor.lower()
        if (argColor in self.colorStrings):
            buf = self.colorStrings[argColor] + msg + endEsc
        else:
            warning("Unknown color name '%s'." % (argColor))
            buf = "<%s>%s</%s>" % (argColor, msg, argColor)
        return(buf)

    def uncolorize(self, msg: str) -> str:
        """Remove any ANSI terminal color escapes from a string.
        """
        t = re.sub(self.colorRegex,    '', msg)
        return(t)

    def uncoloredLen(self, msg: str) -> int:
        """Return the length of a string in characters, not counting any ANSI
        terminal color escapes or any trailing whitespace.
        """
        return(len(self.uncolorize(msg)))

    def color2Html(self, msg: str) -> str:  # TODO: Finish
        """Convert colors escapes to HTML <spans>.
        TODO: This is dumb about overlapping/nested/serial colors, because
        ANSI terminal color does not use a stack discipline.
        """
        t = re.sub(self.colorRegex, self.htmlMapper, msg)
        return(t)

    @staticmethod
    def htmlMapper(_mat):
        assert(False)

    def esc2css(self, e: str) -> str:
        parts = [ code for code in re.split(r"\D+", e) if code.isnum() ]
        return ";".join(parts)

    def toName(self, num) -> str:
        if (ColorManager.numbers2Names is None):
            for nam, num in self.colorStrings.items():
                ColorManager.numbers2Names[num] = nam
        return ColorManager.numbers2Names[num] or None


###############################################################################
#
if __name__ == "__main__":
    import argparse

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--bold", action='store_true',
            help='Show samples with bold foreground colors.')
        parser.add_argument(
            "--colorize", type=str, default=None,
            help="Apply the given color to --text or stdin.")
        parser.add_argument(
            "--effects", type=str, default=None,
            #choices=ColorManager.effectNumbers.keys(),
            help="Show sample only for the given effect(s).")
        parser.add_argument(
            "--pack", action='store_true',
            help='Pack samples, instead of showing one per line.')
        parser.add_argument(
            "--showAll", action='store_true',
            help='Show samples of all combinations.')
        parser.add_argument(
            "--testEffects", action='store_true',
            help='Show samples of all known effects.')
        parser.add_argument(
            "--uncolorize", action='store_true',
            help='Remove ANSI terminal color escapes from the input.')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            "text", type=str, nargs=argparse.REMAINDER,
            help="Rest of args are a message for --colorize if used.")

        args0 = parser.parse_args()
        if (args0.text): args0.text = " ".join(args0.text)
        return args0


    ###########################################################################
    #
    args = processOptions()

    theEffects = []
    if (args.effects):
        theEffects = re.split(r'\s+', args.effects.strip())
    theEffects = set(theEffects)

    ender = "\n"
    if (args.pack): ender = " "

    cm = ColorManager(effects=True)
    ctable = cm.getColorStrings()

    if (args.colorize):
        try:
            onSeq = ctable[args.colorize]
        except KeyError:
            print("\nCan't find color '%s'. See colorNames.md." % (args.color))
            sys.exit()
        offSeq = ctable['off']
        if (args.text):
            print(onSeq + args.text + offSeq, end=ender)
        else:
            for rec in sys.stdin.readlines():
                print(onSeq + cm.uncolorize(rec) + offSeq)

    elif (args.uncolorize):
        if (args.text):
            print(cm.uncolorize(args.text), end=ender)
        else:
            for rec in sys.stdin.readlines():
                print(cm.uncolorize(rec))

    elif (args.testEffects):
        theText = "(Sample Text)"
        if (args.text): theText = args.text
        for eName, eNumber in ColorManager.effectNumbers.items():
            print(" %d %-10s  '%s'" %
                (eNumber, eName, cm.colorize(theText, effect=eName)))

    elif (args.showAll):
        tot = 0
        for ct in (sorted(ctable.keys())):
            if (args.effects):
                keywords = set(re.split('/', ct))
                if (not theEffects.intersection(keywords)): continue
            print(ctable[ct] + ct + ctable['off'], end=ender)
            tot += 1
        print("\nDone, %d combinations." % (tot))

    else:
        print("No action requested. See -h.")
