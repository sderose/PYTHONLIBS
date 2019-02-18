#!/usr/bin/env python
#
# sjdUtils: ANSI color utilities.
#
# 2011-12-09: sjdUtils Port from Perl to Python by Steven J. DeRose.
# 2016-10-31: Split ColorManager.py out of sjdUtils.py.
# 2018-09-04: Make basic tables accessible. Simplify string construction.
#     Add test feature as main.
# 2018-10-22: Catch KeyError on color names.
#
# To do:
#     Resync Perl version.
#     Make localizable.
#
from __future__ import print_function
import sys
import os
import re
import argparse

__version__ = "2018-11-19"


###############################################################################
###############################################################################
# Color management
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
    colorNumbers = {
        u"black"   : 0,
        u"red"     : 1,
        u"green"   : 2,
        u"yellow"  : 3,
        u"blue"    : 4,
        u"magenta" : 5,
        u"cyan"    : 6,
        u"white"   : 7,
        u"default" : 9,
    }

    effectNumbers = {
        u"bold"       : 1,
        u"faint"      : 2,
        u"italic"     : 3,
        u"underline"  : 4,
        #u"blink"      : 5,
        #u"fblink"      :6,
        u"reverse"    : 7,
        u"concealed"  : 8,
        u"strike"     : 9,
    }

    offNumbers = {
        u"default"    : 0,
        u"off"        : 0,
    }

    def __init__(self, effects=None):
        self.colorizeXmlContentExpr = re.compile(r'>(.*?)<')
        self.colorRegex = re.compile(r'\x1b\[\d+(;\d+)*m')
        self.offColor = chr(27) + "[m"  # ANSI to turn off colors
        self.setupColors(effects=effects)

    def setupColors(self, effects=None):
        """Work out all known color, effect, and combination names, and
        put them in a hash that maps them to their escape sequences.
        If 'effects' is not None, it must be either True (to enable all
        known effect names), or a list of the effect names
        to include, as defined in 'effectNumbers' below.
        """
        #nc = os.popen("tput colors").read()
        #if ((not nc) or int(nc) < 8):
        #    self.lg.warning("Color not supported? 'tput colors' says '%s'." % (nc))
        self.colorStrings = {}

        # Be nice to blink-sensitive folks
        if ('NOBLINK' not in os.environ):
            ColorManager.effectNumbers[u"blink"] = 5
            ColorManager.effectNumbers[u"fblink"] = 6

        if (isinstance(effects, list) and len(effects)):
            for k in ColorManager.effectNumbers.keys():
                if (k not in effects): del ColorManager.effectNumbers[k]

        eb = chr(27) + "["
        fmt2 = "%s%d;%dm"

        try:

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
                    self.colorStrings[    e+"/"+c]  = fmt2 % (eb, en, 30+cn)
                    self.colorStrings[    e+"//"+c] = fmt2 % (eb, en, 40+cn)
                    self.colorStrings["!"+e+"/"+c]  = fmt2 % (eb, 20+en, 30+cn)
                    self.colorStrings["!"+e+"//"+c] = fmt2 % (eb, 20+en, 40+cn)

                for c2 in ColorManager.colorNumbers:
                    c2n = ColorManager.colorNumbers[c2]
                    self.colorStrings[c+u"/"+c2] = (
                        fmt2 % (eb, 30+cn, 40+c2n))
                    for e in ColorManager.effectNumbers:
                        en = ColorManager.effectNumbers[e]
                        self.colorStrings[e+"/"+c+"/"+c2] = (
                            "%s%d;%d;%dm" % (eb, en, 30+cn, 40+c2n))
        except KeyError as err:
            sys.stderr.write(
                "KeyError in color setup: %s\n" % (err))
        return()

    def addColor(self, newName, oldName):
        """Add I<newName> to the color table, so it can be passed to I<vMsg>.
        It becomes a synonym for I<oldName> (any previous meaning of I<newName>
        is replaced, but I<oldName> remains).
        """
        try:
            self.colorStrings[newName] = self.colorStrings[oldName]
        except KeyError:
            return(False)
        return(True)

    def isColorName(self, name):
        return(bool(name in self.colorStrings))

    def getColorString(self, name):
        """Return the ANSI escape sequence to obtain the named color.
        Raises KeyError if color name is not known.
        """
        try:
            return(self.colorStrings[name])
        except KeyError as e:
            sys.stderr.write("ColorManager: Unknown name '%s':\n    %s" %
                (name, e))
            return ""

    def getColorStrings(self):
        """Return the dict of all known color names and escape strings.
        """
        return(self.colorStrings)

    def tostring(self, sampleText='sample', filterRegex=None):
        buf = ""
        for k in sorted(self.colorStrings.keys()):
            if (filterRegex and not re.match(filterRegex, k)): continue
            buf += "    %s  %s\n" % (self.colorize(k, sampleText), k)
        return(buf)

    def colorize(self, argColor='red', s="", endAs="off"):
        """If color is enabled, surround I<string> with the escape sequences
        needed to put it in the specified color (assuming the name is known).
        I<endAs> is the color that will be changed to at the end.
        """
        if (argColor not in self.colorStrings):
            return("<%s>%s</%s>" % (argColor, s, argColor))
        buf = self.colorStrings[argColor] + s + self.colorStrings[endAs]
        return(buf)

    def uncolorize(self, s):
        """Remove any ANSI terminal color escapes from a string.
        """
        t = re.sub(self.colorRegex,    '', s)
        return(t)

    def uncoloredLen(self, s):
        return(len(self.uncolorize(s)))


###############################################################################
###############################################################################
#
if __name__ == "__main__":
    doc = u"""
=head1 Description

See colorNames.pod for information re. the colors supported by this package.

This is a separate class for managing ANSI terminal colors.
However, if using C<sjdUtils.py>, the C<ColorManager.py> methods
are patched in to C<sjdUtils.py>, so when color is enabled you can just
call them as if they were methods of C<sjdUtils.py> itself.

The color names available are defined in F<bingit/SHELL/colorNames.pod>,
which supercedes anything in specific scripts (they I<should> match).


=head1 Usage

    from ColorManager import ColorManager
    cm = ColorManager()
    ...
    print(cm.colorize('red/white', myMessage)


=head1 Methods

=over

=item * B<__init__(effects=None)>

Set up the color manager. I<effects> is merely passed down to
I<setupColors()>.

=item * B<setupColors(effects=None)>

(iternal) Work out all known color, effect, and combination names, and
put them in a hash that maps them to their escape sequences.
If 'effects' is not None, it must be a list of the effect names
to include. That list may be empty.

=item * B<addColor(newName, oldName)>

Adds a synonym for an existing color.

=item * B<isColorName(name)>

Returns True iff I<name> is a known color name.

=item * B<getColorString(name)>

Returns the ANSI terminal escape string to switch to the named color.

=item * B<getColorStrings(paramColor, defaultColor)>

Returns a dict mapping color names (such as "red/white") to
the escape strings needed to get them.

=item * B<tostring(sampleText='sample', filter=None)>

Obsolete.

Return a printable buffer with one line for each defined color name.
Each line consist of colorized I<sampleText> and then the color name.

If I<filter> is supplied, it is treated as a regular expression, and any
color names that do not match it are excluded. This is useful because
there are about 1000 combinations available.

=item * B<colorize(argColor='red', s="", endAs="off")>

Return the string I<s>, but with
the ANSI terminal escape sequences to display it in the specified
I<argColor> added at the start, and the escape to switch to color I<endAs>
added at the end.

=item * B<uncolorize>I<(s)>

Remove any ANSI terminal color escapes from I<s>.

=item * B<uncoloredLen>I<(s)>

Return the length of I<s>, but ignoring any ANSI terminal color strings.
This is just shorthand for C<len(uncolorize(s))>.

=back


=head1 Known bugs and limitations

If you I<colorize>() a string, it resets the color to default at the end.
Thus, if you insert colorized string A within colorized string B, the portion
of B following A will I<not> be colorized; if B was already colorized, the
trailing portion will likewise not be colorized.
You can specify the I<endAs> option when colorizing A to avoid this.

ColorManager has no support for 256-color terminals.


=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see http://www.derose.net/steve/utilities/.


=head1 Options

=cut
"""
    from MarkupHelpFormatter import MarkupHelpFormatter
    parser = argparse.ArgumentParser(
        description=doc,
        formatter_class=MarkupHelpFormatter)
    parser.add_argument(
        "--bold",             action='store_true',
        help='Show samples with bold foreground colors.')
    parser.add_argument(
        "--effects",           type=str, default=None,
        #choices=ColorManager.effectNumbers.keys(),
        help="Show sample only for the given effect(s).")
    parser.add_argument(
        "--pack",             action='store_true',
        help='Pack samples, instead of showing one per line.')
    parser.add_argument(
        "--version",          action='version', version=__version__,
        help='Display version information, then exit.')
    args = parser.parse_args()

    effects = []
    if (args.effects):
        effects = re.split(r'\s+', args.effects.strip())
    effects = set(effects)

    ender = "\n"
    if (args.pack): ender = " "
    cm = ColorManager(effects=True)
    ctable = cm.getColorStrings()
    tot = 0
    for ct in (sorted(ctable.keys())):
        if (args.effects):
            keywords = set(re.split('/', ct))
            if (not effects.intersection(keywords)): continue
        print(ctable[ct] + ct + ctable['off'], end=ender)
        tot += 1
    print("\nDone, %d combinations." % (tot))
    sys.exit()
