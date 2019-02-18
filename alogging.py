#!/usr/bin/env python
#
# alogging: messaging, logging, and statistics features from sjdUtils.py.
# Fairly compatible with Python's Logging package.
#
# 2011-12-09: Port from Perl to Python by Steven J. DeRose.
# (... see sjdUtils.py)
# 2015-10-13: Split messaging features from sjdUtils to new ALogger.
#     Integrate with Python 'logging' package.
# 2015-12-31ff: Improve doc.
# 2018-04-02: Add 'direct' option to make Anaconda Nav happier.
# 2018-07-29: Add showSize option to formatRec.
# 2018-08-07: Add quoteKey and keyWidth options to formatRec().
# 2018-08-17: Add maxItems option to formatRec().
#
# To do:
#     Protect formatRec() against circular structures.
#     Change all callers away from eMsg(), then delete method.
#     Option to get rid of "INFO:root:" prefix from logging package.
#     Allow %(name) references to caller's variables??
#     hMsg not printing? should info/warn/error use indent?
#
from __future__ import print_function
import sys
import os
import re
import logging
import inspect
from collections import defaultdict
#import time
#import string
#import argparse

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring
else:
    string_types = str
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): return str(s, encoding, errors)

____version____ = "2018-07-29"

try:
    x = unichr(0x0a)
except NameError:
    def unichr(n): return chr(n)

class ALogger:
    def __init__(self,
        verbose      = None,       # Level of detail for 'info' messages.
        color        = None,
        filename     = None,
        encoding     = 'utf-8',
        level        = None,
        direct       = True,
        ):

        if (color is None):
            color = ('USE_COLOR' in os.environ)

        self.options = {
            'verbose'        : verbose or 1,# Verbosity level
            'color'          : color,       # Using terminal color?
            'filename'       : filename,    # For logging pkg
            'encoding'       : encoding,    # Assumed char set
            # Set a level that doesn't hide too much:
            # CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0
            'level'          : level or 20, # For logging filtering
            'direct'         : direct,      # stderr, not Logger package.

            'badChar'        : "?",         # Substitute for undecodables
            'controlPix'     : True,        # Show U+24xx for control chars?
            'indentString'   : "  ",        # For pretty-printing
            'noMoreStats'    : False,       # Warn on new stat names
            'plineWidth'     : 30,          # Columns for label for pline()
        }
        if (filename):
            logging.basicConfig(level=self.options['level'],
                                filename=self.options['filename'],
                                format='%(message)s')
        else:
            logging.basicConfig(level=self.options['level'],
                                format='%(message)s')
        self.lg             = logging.getLogger()

        # msgType: color, nLevels, func, prefix, infix, suffix, escape, indent.
        self.msgTypes       = {}
        self.msgFormats     = {}
        self.msgStats       = {}

        self.msgIndentLevel = 0   # How far are we indenting infos?
        self.errorCount     = 0   # Total number of errors logged
        self.plineCount     = 1   # pline() uses, for colorizing

        self.unescapeExpr   = re.compile(r'_[0-9a-f][0-9a-f]')

        # Also available via ColorManager.uncolorizer()
        self.colorRegex     = re.compile(r'\x1b\[\d+(;\d+)*m')

        if (self.options['color']): self.setupColor()
        self.defineMsgTypes()

        # Can instead set to generate tags...
        self.openDict = "{"; self.closeDict = "}"
        self.openList = "["; self.closeList = "]"
        self.openObject = "{{"; self.closeObject = "}}"


        return(None)

    def setColors(self, activate=True):
        """Obsolete but kept for backward compatibilit
        """
        if (activate): self.setupColor()

    def setupColor(self):
        try:
            import ColorManager
            self.colorManager = ColorManager.ColorManager()
            self.colorManager.setupColors()
            self.colorStrings = self.colorManager.getColorStrings()
            #print("Color count: %d" % (len(self.colorStrings)))
        except ImportError as e:
            sys.stderr.write("Cannot import ColorManager:\n    %s" % (e))
            self.colorStrings = { 'bold': '*', 'off':'*' }


    ###########################################################################
    ###########################################################################
    # Options
    #
    def setALoggerOption(self, name, value=1):
        return(self.setOption(name, value))
    def setOption(self, name, value=1):
        """Set option I<name> to I<value>.
        """
        if (name not in self.options):
            return(None)
        self.options[name] = value
        return(1)

    def getALoggerOption(self, name):
        return(self.getOption(name))

    def getOption(self, name):
        """Return the current value of an option (see setOption()).
        """
        return(self.options[name])

    def setVerbose(self, v):
        """Set the degree of verbosity for messages to be reported.
        This is NOT the same as the logging package 'level'!
        """
        if (v>0 and not self.lg.isEnabledFor(20)):
            self.lg.setLevel(20)
        return(self.setALoggerOption('verbose', v))

    def getVerbose(self):
        """Return the verbosity threshold.
        """
        return(self.getALoggerOption('verbose'))

    def showInvisibles(self, s):
        """Return 's' with non-ASCII and control characters replaced by
        hexadecimal escapes such as \\uFFFF.
        """
        cp = self.options['controlPix']
        try:
            s = re.sub(r'([%[:ascii:]]|[[:cntrl:]])',
                lambda x: (
                    chr(0x2400+ord(x.group(1))) if (cp and ord(x.group(1))<32)
                    else (u"\\u%04x;" % (ord(x.group(1))))),
                s)
        except sre_costant.error as e:
            sys.stderr.write("Regex error processing '%s'." % (x.group(1)))
        return(s)

    ###########################################################################
    # Set default options for predefined message-types v, e, h, x.
    #
    def defineMsgTypes(self):
        """
        Define the set of built-in message types.
        """
        # Try to figure out what the background color is?
        bgType = 'light'
        if ('TERM_BG' in os.environ):
            if (os.environ('TERM_BG') in [u'black',u'blue',u'red',u'magenta']):
                bgType = 'dark'
        elif (0 and 'COLORTERM' in os.environ):
            if (os.environ('COLORTERM') == "gnome-terminal"):
                xtc = "FIX THIS" # which xtermcontrol
                if (0 and os.path.exists(xtc)):
                    # xtermbg = xtc --get-bg
                    # ...
                    pass

        if (bgType == 'light'):
            self.defineMsgType(u'v',
              u'blue',             escape=0, indent=1)
            self.defineMsgType(u'e',
              u"bold/white/red",   escape=1, indent=1,  prefix=u"ERROR: ")
            self.defineMsgType(u'h',
              u'magenta/white',    escape=0, indent=1,  prefix=u"\n******* ")
            self.defineMsgType(u'x',
              u'blue',             escape=0, indent=0)
        else:
            self.defineMsgType(u'v',
              u"/blue",            escape=0, indent=1)
            self.defineMsgType(u'e',
              u"/red", func=1,     escape=1, indent=1,  prefix=u"ERROR: ")
            self.defineMsgType(u'h',
              u"/magenta/white",   escape=0, indent=1,  prefix=u"\n******* ")
            self.defineMsgType(u'x',
              u"/blue",            escape=0, indent=0)


    def defineMsgType(self, msgType, color=None, nLevels=0, func=None,
        prefix=None, infix=None, suffix=None, escape=None, indent=None):
        """Create a new named message type, for use with 'Msg()'.
        Each type owns a bunch of formatting information.
        Arguments default to None, so user can leave items unchanged
        if the type is already defined.
        """
        if (not msgType): return(0)
        if (msgType not in self.msgTypes):
            #sys.stderr.write("defining new message type '%s'.\n" % (msgType))
            self.msgTypes[msgType] = {
            'color'     : color or u"/yellow",
            'nLevels'   : 0,
            'func'      : 0,
            'prefix'    : u"",
            'infix'     : u"",
            'suffix'    : u"",
            'escape'    : 1,
            'indent'    : 1,
        }
        theType = self.msgTypes[msgType]
        if (color  is not None): theType['color']   = color
        if (nLevels is not None): theType['nLevels'] = nLevels
        if (func   is not None): theType['func']    = func
        if (prefix is not None): theType['prefix']  = prefix
        if (infix  is not None): theType['infix']   = infix
        if (suffix is not None): theType['suffix']  = suffix
        if (escape is not None): theType['escape']  = escape
        if (indent is not None): theType['indent']  = indent
        return(1)

    def getMsgDefs(self):
        """
        """
        buf = ("******* Message Type Definitions (indentString = '%s'):\n" %
            (self.options['indentString']))
        for k, v in (self.msgTypes.items()):
            buf += '  ' + k + ': '
            for a in v.keys():
                buf += "%s:'%s', " % (a, v[a])
            buf += "\n"
        return(buf)

    def getPickedColorString(self, argColor, msgType):
        """Return color escape codes (not name!) -- the requested color if any,
        else the default color for the message type.
        """
        if (not self.options['color']):
            return("","")

        if (argColor and argColor in self.colorStrings):
            return(self.colorStrings[argColor],self.colorStrings['off'])

        mt = msgType.lower()
        if (mt and mt in self.msgTypes and
            self.msgTypes[mt]['color'] in self.colorStrings):
            #print("getPickedColorString: msgType color '%s'." % (self.msgTypes[mt]['color']))

            return(self.colorStrings[self.msgTypes[mt]['color']],
                   self.colorStrings[u'off'])
        return("","")

    ###########################################################################
    # Manage persistent indentation of xMsg calls.
    #
    def MsgPush(self):
        """Increment the message indent level, causing indentation for messages
        displayed via I<vMsg>. This is mainly useful for messages that reflect
        successive tiers of processing on input data (e.g., notices about
        each file, record, and field). The string to repeat to make indentation
        can be set with I<setOption('indentString', string)>.
        """
        self.msgIndentLevel += 1

    def MsgPop(self):
        """Decrement the message-nesting level (see I<MsgPush>).
        """
        if (self.msgIndentLevel>0): self.msgIndentLevel -= 1

    def MsgSet(self, n):
        """Force the message-nesting level to I<n> (see I<MsgPush>).
        """
        self.msgIndentLevel = n

    def MsgGet(self):
        """Return the message-nesting level (see I<MsgPush>).
        """
        return(self.msgIndentLevel)


    ###########################################################################
    # Python 'Logger'-compatible calls:
    #
    def log(self, level, msg, stat=None, **kwargs):    # TAKES LEVEL ARG
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.log(level, msg, *kwargs)
    def debug(self, msg, stat=None, **kwargs):         # level = 10
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.debug(msg, *kwargs)
    def info(self, msg, stat=None, **kwargs):          # level = 20
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.info(msg, *kwargs)
    def warning(self, msg, stat=None, **kwargs):       # level = 30
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.warning(msg, *kwargs)
    def error(self, msg, stat=None, **kwargs):         # level = 40
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.error(msg, *kwargs)
    def exception(self, msg, stat=None, **kwargs):     # level = 40
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.exception(msg, *kwargs)
    def critical(self, msg, stat=None, **kwargs):      # level = 50
        if (stat): self.bumpStat(stat)
        if (self.options['direct']): self.directMsg(msg)
        else: self.lg.critical(msg, *kwargs)

    def directMsg(self, msg):
        if (not msg.endswith("\n")): msg += "\n"
        sys.stderr.write(msg)


    # Pass through a few useful methods?
    def setLevel(self, lvl):
        self.lg.setLevel(lvl)
    #def disable(self, lvl):
    #    self.lg.disable(lvl)
    #def addLevelName(self, lvl, lvlName):
    #    self.lg.addLevelName(lvl, lvlName)
    #def getLevelName(self, lvl):
    #    self.lg.getLevelName(lvl)
    #def shutdown(self):
    #    self.lg.logging.shutdown()

    # Add fatal(): level 60, and raise exception after.
    #
    def fatal(self, msg, stat=None, **kwargs):         # level = 60
        if (stat): self.bumpStat(stat)
        self.log(60, msg, *kwargs)
        raise Exception("*** Logged message is fatal ***")

    # The following message methods and types are treated
    #     as subtypes of info() messages. So they only appear if you
    #     set logging level to a value <= 20.
    # IN ADDITION, they take a 'verbose' argument, which is a value
    #     from 0 to n, and is the number of '-v' flags (or equivalent)
    #     needed to make the message appare. So 0 will show up any time
    #     info() messages do; 1 must also have at least -v; two -v -v,....
    #
    def MsgRule(self, verbose=0, color=None, width=79):
        """Obsolete, deprecated. Use rMsg().
        """
        self.rMsg(verbose=verbose, color=color, width=width)

    def rMsg(self, verbose, color=None, width=79, char=None):
        """Draw a (possibly colored) line I<n> columns wide. Default n: 80.
        """
        if (not char): char = '='
        if (self.options['verbose']<verbose): return
        (on,off) = self.getPickedColorString(color, None)
        m = on + (char * width/len(char)) + off
        self.info(m+"\n")

    def vMsg(self, verbose, m1="", m2="", color=None, stat=""):
        """A variant of I<Msg>(), to issue a 'verbose' (msgType 'v') message.
        """
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose']<verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, msgType='v')
        self.info(m+"\n")

    # Change called over to call error() directly, then delete eMsg().
    def eMsg(self, verbose, m1="", m2="", color=None, stat=""):
        """A variant of I<Msg>(), to issue an 'error' (msgType 'e') message.
        """
        self.errorCount += 1
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose']<verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, msgType='e')
        self.info(m+"\n")
        if (verbose<0):
            raise AssertionError("alogging:eMsg with level %d." % (verbose))

    def hMsg(self, verbose, m1="", m2="", color=None, stat=""):
        """A variant of I<Msg>(), to issue a 'heading' (msgType 'h') message.
        """
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose']<verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, msgType='h')
        self.info(m+"\n")

    # Messages of various kinds (sync with Perl version)
    def Msg(self,msgType,m1="",m2="",color=None,escape=None,stat=None,verbose=0):
        """Issue a message of the given I<msgType> (define via I<defineMsgType).
        See also the wrappers I<hMsg>(), I<vMsg>(), and I<hMsg>().

        Checks I<verbose> against the value of the 'verbose' option; if that
        option has actually been set, B<and> is lower, return without display.
        Otherwise, call Logger's I<info>() to actually issue the message.

        * I<msgType> Mnemonic 'type' of the message, per defineMsgType>().

        * I<message1> The text to display, in the color specified by the I<color>
        argument, or the color for the message type.

        * I<message2> (optional) additional message, to display uncolored.
        If I<text> is true, it will undergo I<showInvisibles>() and be bracketed.
        A newline appears after I<message2>.

        * I<color> the color in which to display I<message1>.
        For backward compatibility, I<color> may be a literal ANSI color
        escape sequence, such as I<\\e[31m>, etc.

        * I<text> Send I<m1> through I<showInvisibles>().

        * I<stat> Increment the named statistic, even if the message will not
        appear.
        The counts reside in a dictionary in C<msgStats>.
        See I<showStats>() for displaying a list of all the collected counts.
        Also see I<bumpStat>, I<setStat>, I<appendStat>, and I<getStat>.
        """
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose']<verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, msgType=msgType, color=color, escape=escape)
        self.lg.info(m)
        return

    def assembleMsg(self, m1="", m2="",
             color=None, escape=False, indent=None, nLevels=0, msgType='v'):
        """Assemble the components of a message to be printed.
        bumpStat also happens there.
        Parameters corresponding to definedMsgType() ones, are overrides.
        """
        if (msgType not in self.msgTypes):
            sys.stderr.write("Unknown message type '%s'.\n" % (msgType))
            msgType = 'v'
        msgDef = self.msgTypes[msgType]
        locMsg = ""; nLevels = max(nLevels, msgDef['nLevels'])
        if (nLevels>0):
            locMsg = "TRACEBACK:\n" + self.getLoc(3, 3+nLevels) + "\n"
        if (escape or msgDef['escape']):
            m1 = self.showInvisibles(m1)
            m2 = self.showInvisibles(m2)

        if (indent or msgDef['indent']):
            ind = (self.options['indentString'] * self.msgIndentLevel)
            pre = ind + re.sub(r'\n', r'\n'+ind, msgDef['prefix'])
            inf = re.sub(r'\n', r'\n'+ind, msgDef['infix'])
            suf = re.sub(r'\n', r'\n'+ind, msgDef['suffix'])
        else:
            pre = msgDef['prefix']
            suf = msgDef['suffix']

        caller = ""
        if (msgDef['func']): caller = self.getCaller() + ": "

        (on,off) = self.getPickedColorString(color, msgType)

        if (PY3 or isinstance(m1, unicode)):
            um1 = m1
        else:
            try:
                um1 = unicode(m1, encoding='latin-1')
            except UnicodeDecodeError:
                um1 = re.sub(r'[\x80-\xFF]', self.options['badChar'], m1)
        if (PY3 or isinstance(m2, unicode)):
            um2 = m2
        else:
            try:
                um2 = unicode(m2, encoding='latin-1')
            except UnicodeDecodeError:
                um2 = re.sub(r'[\x80-\xFF]', self.options['badChar'], m2)

        m = u""
        m += on + pre + caller + um1 + off + inf + um2 + suf + "\n" + locMsg
        return(m)


    def getLoc(self, startLevel=0, endLevel=0):
        """Return a line(s) showing where we were invoked from.
        frameItems = [ 'frameObj', 'file', 'lineno',
                       'function', "[codeLines]", 'indexOfLine' ]
        """
        if (startLevel<=0): return("")
        buf = ""
        if (endLevel==0): endLevel = len(inspect.stack())
        for level in range(startLevel, endLevel):
            fr = inspect.stack()[level]
            buf += ("%-20s %4d in %s(): %s" %
                (fr[1], fr[2], fr[3], fr[4][fr[5]]))
        return(buf)

    def findCaller(self):
        return(self.getCaller())

    def getCaller(self):
        fr = inspect.stack()[2]
        return(fr[3])


    ###########################################################################
    # Statistic-keeping
    #
    def defineStat(self, stat):
        """Create a new statistic. Optional, because stats are quietly created
        as needed. However, I<setOption('noMoreStats', True) prevents this.
        """
        self.msgStats[stat] = 0

    def bumpStat(self, stat, amount=1):
        """Increment the named statistic, by I<amount> (default: 1).
        If the name contains "/", it splits there. The first part is
        the overall stat name, which will be stored as a dict, with
        entries made and counted for each value of the second part.
        """
        if (stat in self.msgStats):
            self.msgStats[stat] += amount
        elif (self.options['noMoreStats']):
            self.Msg(0, "alogging.bumpStat: unknown stat '%s'." % stat)
        else:
            self.msgStats[stat] = amount

    def appendStat(self, stat, datum):
        """Append to the named statistic (converting to a list first if needed)
        """
        if (stat in self.msgStats):
            self.msgStats[stat].append(datum)
        elif (self.options['noMoreStats']):
            self.Msg(0, "alogging.appendStat: unknown stat '%s'." % stat)
        else:
            self.msgStats[stat] = [ datum ]

    def setStat(self, stat, value):
        """Force the named statistic to the given value.
        """
        if (stat in self.msgStats):
            self.msgStats[stat] = value
        elif (self.options['noMoreStats']):
            self.Msg(0, "alogging.setStat: unknown stat '%s'." % stat)
        else:
            self.msgStats[stat] = value

    def getStat(self, stat):
        """Return the current value of the named statistic.
        """
        if (stat in self.msgStats): return(self.msgStats[stat])
        return(0)

    def showStats(self, zeros=False, descriptions=None,
                  dotfill=0, fillchar='.', onlyMatching='', lists='len'):
        """Display all the stat values, via I<pline>()
        @param I<zeros>: if not True, statistics with a count of 0 are excluded.
        @param I<descriptions>: map from names to a I<label> argument to
            have I<pline>() display. Unmapped names use the name as label.
        @param I<dotfill>: Use dot-fills for readability (@see pline()).
        @param I<fillchar>: Use this char as the "dot" for dotfill.
        @param I<onlyMatching>: a regex, only stats that match it appear.
        @param I<lists>: For 'appendStat' stats, how to show the vectors:
          - omit: do not report at all
          - len: just show the list length
          - uniq: uniqify and sort, then show the list
          - uniqc: uniqify with count, sort, then show the list
          - otherwise: show the whole list
        """
        # If any stats contain "/", accumulate into groups.
        statGroups = defaultdict(int)
        for k in self.msgStats.keys():
            if ('/' not in k): continue
            parts = '/'.split(k)
            statGroups[parts[0]] += self.msgStats[k]
        for statGroup, n in statGroups.items():
            if (statGroup in self.msgStats):
                statGroup += " [group]"
            self.msgStats[statGroup] = n

        # Generate the report
        self.lg.info("Summary of message statistics:")
        nPrinted = 0
        for k in sorted(self.msgStats.keys()):
            if (onlyMatching and not re.search(onlyMatching, k)):
                continue
            if (descriptions!=None and k in descriptions):
                label = descriptions[k]
            else:
                label = k
            v = self.msgStats[k]
            if (isinstance(v, list)):
                if (lists == 'omit'): continue
                elif (lists == 'len'): self.pline("  "+label, len(v))
                elif (lists == 'uniq'):
                    uv = sorted(list(set(v)))
                    self.pline("  "+label, uv)
                elif (lists == 'uniqc'):
                    uv = defaultdict(int)
                    for item in v: uv[item] += 1
                    disp = ""
                    for k in sorted(dict(uv).keys()): disp += "%s:%d, " % (k, uv[k])
                    self.pline("  "+label, disp)
                else: self.pline("  %s%s" % (label, v))
            elif (v!=0 or zeros):
                nPrinted += 1
                pLabel = "  "+label
                if ('/' in k): pLabel = "    " + pLabel
                self.pline(pLabel, v, dotfill=dotfill, fillchar=fillchar)
        if (nPrinted==0):
            self.lg.info("    (no stats logged)")

    def pline(self, label, n, denom=None, dotfill=0, fillchar='.',
        width=None, quiet=False):
        """Display via I<vMsg>(), with I<label> padded to I<width> columns,
        (default: C<plineWidth> option). I<n> is justified according to type.
            With I<dotfill>, every I<dotfill>'th line will pad I<label>
        with I<fillchar> for readability (using I<ljust>).
            If I<denom> ('denominator') is non-zero, and I<n> is an int or
        float, then an additional field showing n/denom appears (or 'NaN').
        """
        self.plineCount += 1
        if (isinstance(n, int)):
            valueField = "%12d" % n
        elif (isinstance(n, float)):
            valueField = "%12.6f" % n
            if (denom): valueField += "   %12.6f" % (n/denom)
        elif (isinstance(n, bool)):
            valueField = "%10s" % (n)
        else:
            try:
                valueField = unicode(n)
            except UnicodeDecodeError:
                valueField = self.showInvisibles(n)

        if (denom):
            try:
                ratio = "%12.6f" % (n*1.0/denom)
            except (ValueError, ZeroDivisionError):
                ratio = "%12s" % ('NaN')
            valueField += "   " + ratio

        wid = width or self.options['plineWidth']
        if (not dotfill or self.plineCount % dotfill != 0):
            uncolorized = re.sub(self.colorRegex, '', label)
            padlen = wid - len(uncolorized)
            msg = label + (" " * padlen) + valueField
        else:
            msg = label + (fillchar * padlen) + valueField
        if (not quiet): self.lg.info(msg)
        return(msg)

    def clearStats(self):
        self.msgStats = {}

    # dir() can be wrong, e.g., if the object has a custom __getattr__.
    # Does not seem to work for Cython objects such as in Spacy.
    #
    def dirMain(self, obj, includeCallables=False):
        tdict = {}
        for k in dir(obj):
            if (k.startswith("__") or k == "_"): continue
            try:
                if (not includeCallables and callable(getattr(dir, k))):
                    continue
                val = getattr(dir, k)
            except AttributeError:
                val = "###MISSING ATTRIBUTE###"
            tdict[k] = val
        return tdict

    # Or  inspect.getmembers(object[, predicate])
    # Add summarizable classes/types (e.g. Node)
    #
    from xml.dom.minidom import Node, Document
    import xml.dom.minidom

    def formatRec(self, obj, depth=0, showSpecials=False,
        maxDepth=3, maxItems=0, showSize=True, quoteKeys=False, keyWidth=14):
        """NOTE: This is not protected against circular structures, except
        by 'maxDepth'.
        """
        if (depth > maxDepth): return
        #ty = type(obj)
        ind = "    " * depth
        #buf += (ind + "*** Dumping a '%s'." % (type(obj)))
        buf = ""

        if (obj is None):
            buf += ind + "*NONE*"

        #elif (isinstance(obj, ( Node, Document ))):
        #    buf += "%s%s%s" % (unichr(0x227A), type(obj), unichr(0x227B))

        elif (callable(obj)):
            #buf += (ind + "callable '%s'\n" % (nm))
            nm = getattr(obj, '__name__', "[UNNAMED]")
            buf += ind + "Function '%s()'" % (nm)

        # If a scalar is in some aggregates, the aggregate add ind and \n.
        elif (type(obj) in [ int, float, long, complex, str, unicode ] or
            isinstance(obj, (int, float, long, complex, basestring))):
            buf += self.formatScalar(obj)

        elif (isinstance(obj, dict)):  # namedtuple, defaultdict?
            buf += ind
            if (showSize): buf += "dict |%d|:" % (len(obj))
            if (len(obj)):
                buf += ind + " %s\n" % (self.openDict)
                dfmt = ind + "  %-" + ("%d" % (keyWidth)) + "s: %s,\n"
                inum = 0
                for n, v in (obj.items()):
                    inum += 1
                    if (maxItems and inum > maxItems): break
                    buf += dfmt % (
                        self.quote(n, quoteKeys),
                        self.formatRec(v, depth+1, showSize=showSize, quoteKeys=quoteKeys))
                buf += ind + self.closeDict

        elif (isinstance(obj, (tuple, set, frozenset))):
            buf += ind
            if (showSize): buf += "set-ish |%d|" % (len(obj))
            if (len(obj)):
                buf += ": %s\n" % (self.openList)
                for n, v in enumerate(obj):
                    if (maxItems and n > maxItems): break
                    buf += ("%s%s,\n" %
                    (ind, self.formatRec(v, depth+1, showSize=showSize, quoteKeys=quoteKeys)))
                buf += ind + self.closeList

        elif (isinstance(obj, list)):
            buf += ind
            if (showSize): buf += "list |%d|" % (len(obj))
            if (len(obj)):
                buf += ": %s\n" % (self.openList)
                for n, v in enumerate(obj):
                    if (maxItems and n > maxItems): break
                    buf += "%s %3d %s,\n" % (ind, n, self.formatRec(v, depth+1, showSize=showSize, quoteKeys=quoteKeys))
                buf += ind + self.closeList

        elif (isinstance(obj, object)):
            stuff = dir(obj)
            buf += ind
            if (showSize): buf += "obj %s |%d|" % (type(obj), len(stuff))
            buf += ": %s\n" % (self.openObject)
            #skipped = 0
            for nm in (stuff):
                thing = getattr(obj, nm, "[NONE]")
                if ((nm.startswith('__') or callable(thing))
                    and not showSpecials):
                    #skipped += 1
                    continue
                #buf += (ind + "  .%s (%s): " % (nm, type(thing)))
                buf += "%s    %-24s = %s,\n" % (
                    ind, "'" + self.quote(nm, quoteKeys) + "'",
                    self.formatRec(thing, depth+1, showSize=showSize, quoteKeys=quoteKeys))
            buf += ind + self.closeObject

        else:
            buf += ("something else")
            buf += self.formatScalar(obj)
        return buf
        # end formatRec

    def quote(self, s, addQuotes=False):
        if (not addQuotes): return s
        return '"' + re.sub(r'"', '\\"', s) + '"'

    # Scalars don't add their own newline.
    def formatScalar(self, obj):
        ty = type(obj)
        if (obj is None):
            return "*None*"
        elif (isinstance(obj, str) or
            isinstance(obj, basestring)):
            return '"%s"' % (obj)
        elif (isinstance(obj, unicode)):
            return 'u"%s"' % (obj)
        elif (isinstance(obj, bytearray)):
            return 'b"%s"' % (obj)
        elif (isinstance(obj, buffer)):
            return '"%s"' % (obj)
        #elif (isinstance(obj, storage)):
        #    return "%s" % (obj)

        elif (isinstance(obj, bool)):
            if (obj): return "True"
            return "False"

        elif (isinstance(obj, int)):
            return "%8d" % (obj)
        elif (isinstance(obj, float)):
            return "%12.4f" % (obj)
        elif (isinstance(obj, long)):
            return "%12d" % (obj)
        elif (isinstance(obj, complex)):
            return "%s" % (obj)

        elif (isinstance(obj, dict)):
            return "{|%d|}" % (len(obj))
        elif (isinstance(obj, list)):
            return "[|%d|]" % (len(obj))
        elif (isinstance(obj, tuple)):
            return "(|%d|)" % (len(obj))
        elif (isinstance(obj, set)):
            return "[set |%d|]" % (len(obj))
        elif (isinstance(obj, frozenset)):
            return "[frset |%d|]" % (len(obj))

        elif (isinstance(obj, object)):
            return "[%s |%d|]" % (ty, len(obj))
        return "[???] %s" % (obj)
        # end formatScalar


###############################################################################
###############################################################################
# Main (doc, example and smoke-test)
#
if __name__ == "__main__":
    descr = """
=pod
=head1 Description

A logging facility, largely compatible with Python 'logging.Logger'.
Derived from sjdUtils.py's messaging methods.

=head1 Extra features compared to logging.Logger:

=over

=item * Strong support for ANSI terminal color

=item * Controllable indentation levels for messages

=item * Defined named message types, with their own layouts

=item * Traditional *nix-style C<-v> verbosity levels

=item * Better Unicode and non-printable char handling

=item * Option to bump a counter for any/all messages, making it easy
to keep and report error statistics

=back

=head2 Notes on speed

With either this package or Python C<logging>,
calling a logging/messaging method does cost
time even if the message doesn't end up getting displayed or saved.
This can be very significant for messages in inner loops.
It can also be significant if evaluating the I<parameters> being passed
is expensive, since that is done before the logging function is actually
called (so even if the logging function returns instantly the setup time
is still taken).

You can get reduce such overhead by:

=over

=item (a) removing or commenting out the calls, especially in inner loops.
You may want to use a profiler to be sure which ones actually matter.

=item (b) putting code under an "if", for example "if (False)", "if (args.verbose)", or even better,
"if (__debug__)" (which makes them go away when Python is run with the C<-O>
option.

=item (c) Use a preprocesser to remove some/all logging statements
for production. See the discussion at
L<http://stackoverflow.com/questions/482014>.

=back



=for nobody ===================================================================

=head1 General Methods

=over

=item * B<setVerbose(v)>

The initial verbosity level can be set as a parameter to the constructor.
This method lets you reset it later.
Otherwise, messages whose first argument's magnitude
is greater than I<v> are discarded (verbosity levels are perhaps best
thought of as priorities). This means that verbosity runs like C<-v> flags in
many *nix programs, but opposite from Python C<logging> levels.

I<setVerbose(v)> is just shorthand for B<setOption("verbose", v)>.

=item * B<getVerbose>()

Return the current verbosity level (see I<setVerbose>).
This is just shorthand for B<getOption("verbose")>.

=item B<findCaller(self)

Returns the name of the function or method that called I<findCaller>().

=item * B<pline(label, n, width=None, dotfill=0, fillchar='.', denom=None)>

Display a line consisting of I<label> (padded to I<width>),
and then the data (I<n>).
I<width> defaults to the value of the I<plinewidth> option.
The data is displayed in a type-appropriate way after that.

If I<dotfill> is greater than 0, then every I<dotfill>'th line will use
I<fillchar> instead of space for padding I<label>. For example,
I<dotfill=3> makes every third line be dot-filled.

If I<denom> is greater than 0, another column is displayed, showing I<n/denom>.

=back


=head2 'logging'-like messaging methods

=The following methods are largely compatible with methods in the Python
C<logging> package. However, there is no tree of instances, just
an I<ALogger> object. The format string for each type is kept in
C<msg.formats{typename}>, and defaults to I<%(msg}\\n>.
These methods are still experimental.

I<kwargs> can be used to provide a dictionary of names whose
values are filled in to such format strings via I<%(name)>.
This is only useful if you also set a format
string that includes references to them. These names are defined by default:

=over

=item B<info(self, msg, *args, **kwargs)

Issues an informational message, like Python C<logging>.

=item B<warning(self, msg, *args, **kwargs)

Issues a warning message, like Python C<logging>.

=item B<error(self, msg, *args, **kwargs)

Issues an error message, like Python C<logging>.

=item B<critical(self, msg, *args, **kwargs)

Issues an critical error message, like Python C<logging>.

=item B<debug(self, msg, *args, **kwargs)

Issues a debugging message, like Python C<logging>.

=item B<log(self, level, msg, *args, **kwargs)

Issues an otherwise unspecified log message, like Python C<logging>.

=item B<exception(self, msg, *args, **kwargs)

Issues an exception message, like Python C<logging>.

=back


=head2 Additional messaging methods

=over

=item * B<eMsg> I<(level, message1, message2, color, text, stat)>

Shorthand for I<Msg('e'...)>, meant for error messages.
Specifying a I<level> less than 0 is fatal.
B<Deprecated>, replaced by I<warning>(), I<error>(), and I<fatal>().

=item * B<hMsg> I<(level, message1, message2, color, text, stat)>

Shorthand for I<Msg('h'...)>, meant for headings, which are displayed
more prominantly. By default, with a blank line and several asterisks in front.

=item * B<vMsg> I<(level, message1, message2, color, text, stat)>

Shorthand for I<Msg('v'...)>, meant for debugging/tracing messages.
The levels of messages here, are separate from Logger's implicit
levels for I<warning>, I<error>, etc.

=item * B<rMsg(self, color=None, width=n, char='=')>

Draw a (possibly colored) line ("rule") of width I<n> characters.
Default I<n>: 80.

=item * B<Msg> I<(msgType, message1, message2, color, text, stat)>

Issue a message (normally to STDOUT), using the formatting and options defined
for the given I<msgType>. Types 'e' (error), 'w' (warning),
and 'h' (header) are provided, and have
shorthand calls (see following); additional
types can be defined using I<defineMsgType>().

=back


=head3 Treatment of message with C<eMsg>, C<vMsg>, C<hMsg>, etc.

The C<ALogger>-specific messaging methods do the following:

=over

=item - If the message is not high enough priority compared
to the I<verbose> setting, the method simply returns.

B<Important Note>: All I<vMsg> messages are
I<information>-level as far as I<Logger> is concerned, and so I<none>
of them will show up unless you're showing such messages. The I<level>
argument to I<vMsg> is a further filter, to support verbosity levels
as are very common for *nix utilities.

=item - Converts the message to UTF-8.

=item - Adds I<prefix> before I<m1>,
I<infix> between I<m1> and I<m2>, and/or I<suffix> after I<m2>.

=item - If I<indent> is True, creates an indent string for
the level set by I<MsgPush>(), etc., and inserts it:

=over

=item * before the prefix, and

=item * after each newline in the prefix, infix, and suffix

=back

=item - If I<func> is True, inserts the name of the calling function
before I<m1>.

=item - Colorizes the prefix (including any applicable preprefix, infix,
and indentation whitespace) and I<m1>.

=item - If I<escape> is True, passes I<m1> and I<m2> through I<showInvisibles>,
which turns control characters, whitespace, etc. to visible representations.

=item - If I<nLevels> > 0, appends that many levels of stack-trace information.

=item - Displays the resulting message. It goes to STDERR by default,
but to STDOUT if the I<stdout> option is set.

=back

These items can be filled in by a message format:

=over

=item 'function'

=item 'filename'

=item 'index'

=item 'lineno'

=item 'asctime'

=item 'type'

=item 'msg'

=back


=head2 Custom message types

=item * B<defineMsgType>(type, color=None, nLevels=None, func=None,
prefix=None, infix=None, suffix=None, escape=None, indent=None)

Create or modify a named "type" of message.
Types "v", "e", and "h" are predefined but may be modified.
Type "x" is reserved.

The parameters other than I<type> are all optional and default to C<None>.
When a parameter is C<None>, the property is left
unchanged for an already-existing message type.
However, for an entirely new message type the property is set to
the corresponding default value shown below:

=over

=item * I<type>: a name for the type of message, to identify it to I<Msg>().
Required.

=item * I<color>: What color to display the message in (if color is enabled).
Default: C</yellow>.
Note that the C<_Msg> methods can take a C<color> argument to override this for
particular messages.

=item * I<nLevels>: Number of levels of stack-trace to display
(not yet supported). Default: C<0>.

=item * I<func>: If True, display the calling function's name.
Default: C<False>.

=item * I<prefix>: A string to display before the start of each message.
For example, "h"
messages prefix "\\n******* ", to make them stand out like headings.
Default: "".

=item * I<infix>: A string to display between the parts (I<m1> and I<m2>)
of each message. For example, one might want I<m2> always on a separate line,
and therefore set I<infix> to C<\\n>.
Default: "".

=item * I<suffix>: A string to display after the end of each message.
Default: "".

=item * I<escape>: Turn non-printable characters in the message to printable.
This is done using I<showInvisibles>() (q.v.).
Default: C<True>.
Note that the C<Msg> methods accept an C<escape> parameter to override this for
particular messages.

=item * I<indent>: Whether to indent messages according to the level set
using I<vPush>(), I<vPop>(), etc.
Default: C<True>.

=back


=head2 Statistics-keeping methods

This package maintains a list of named "statistics". Typically, each
one has just a counter, which you increment by passing the static name
to the C<stat"> parameter of any of the messaging calls described in the
next section. You do not need to declare or initialize such statistics
(although you can set them all and then set the C<noMoreStats> option
to prevent creating any more).

The statistics can all be printed out (for example, just before your
main program ends). For example:

    recnum = 0
    for rec in open(foo, 'r').readline():
        recnum += 1
        if (len(rec) > 999):
            lg.eMsg("Line %d too long (%d characters)." % (recnum, len(rec)),
                    stat="Too long")
    lg.setOption('plineWidth', 45)  # Allow space for long stat names
    lg.showStats()

An B<experimental> feature allows you to use "/" in a stat name, in
order to group statistics for reporting. If used, such statistics will
be grouped (well, they would be anyway by alphabetization),
and indented under the common (pre-/) part, which will be printed
with the total counts for all stats in the group. This is especially useful
for defining subtypes of errers, or attaching small data to them. The
example above could be modified to keep count of all the specific
excessive record-lengths, by changing the I<eMsg> call to:

    lg.eMsg("Line %d too long (%d characters)." % (recnum, len(rec)),
            stat="Too long/%d" % (len(rec))

In addition to the C<stat> parameter on various messaging methods, there
are methods for manipulating the stats independently of messages:

=over

=item * B<defineStat(self, stat)>

Initialize the given stat (to 0). This is optional (that is, you can just
mention a stat and it will be created if necessary).

=item * B<bumpStat(self, stat, amount=1)>

Increment the given stat by the specified I<amount> (default: 1).

=item * B<appendStat(self, stat, datum)>

Convert the given stat to a list if it is not one already, and I<append>
the I<datum> to the list.

=item * B<setStat(self, stat, value)>

Set the given stat to the given I<value>.

=item * B<getStat(self, stat)>

Return the value of the given stat.

=item * B<showStats(self, zeros=False, descriptions=None, dotfill=0, fillchar='.', onlyMatching='', lists='len')

Display all the accumulated statistics,
each with its name and then its value.
Each statistic is printed used I<pline>(), so is subject to the formatting
described there.

Stats with a value of 0 are not shown unless
the I<zeros> parameter is set to True.

If I<descriptions> is specified, it must be a dict that maps (some or all) of
the stat names to strings to be printed in place of the name. This is useful
if you want short/compact names to pass to I<bumpStat>, messaging, or other
methods that take a stat name; and yet want long, more user-readable
error descriptions for the report.

B<Note>: See above re. the (experimental) use of "/" in statistic names,
to group and accumulate more detailed statistics.

I<dotfill>: Use dot-fills for readability (@see pline()).

I<fillchar>: Use this char as the "dot" for dotfill.

I<onlyMatching>: a regex. Only stats whose names match it are displayed.

I<lists>: For stats that are lists (see I<appendStat>()), specifies
how to show those lists:

=over

=item * 'omit': do not show at all

=item * 'len': just show the list name and length

=item * 'uniq': sort and uniqify, then show the list

=item * 'uniqc': sort and uniqify with count, then show the list

=item * otherwise: show the whole list

=back

=item * B<clearStats(self)>

Remove all statistics.

=back


=head2 Additional messaging methods

This package adds several more calls. The first is simply I<fatal>,
which issues a I<log>() message with level 60, and then raises an
exception (if uncaught, this will lead to a stack trace and termination).

The following calls issue their messages via I<info>(),
and so will not produce visible message if the I<Logger> level is over 20.

These are mainly for developers or power users, and support
messages of the kind common for *nix command-line programs, where the
amount of messaging is increased by using one or more I<-v> options.
Thus, the I<verbose> argument for the following calls ranges from 0
(for a message that should appear any time the I<Logger> message allows
any 'info' messages through); to 1 (for messages that also require at least
I<-v> on the command line); to 2 (for messages that also require at least
I<-v -v> on the command line); and so on.

To set the degree of verbosity, use B<setVerbose(n)>. Calling this with n>0
will test that Logger.isEnabledFor(20) is True; if not, it will call
Logger.setLevel(20) so that these messages have a chance to get through.
This means that getting such messages also forces you to get warnings,
error, and criticals. This seems sensible to the author.

=over

=item * B<Msg(self, level, msgType='v', color=None, width=79)>

Issues such a message. The I<msgType> parameter specifies a message I<type>
either from the predefined list (e, v, h, or x),
or added using I<defineMsgType>(). A message type can specify:

=over

=item * a format-string to use for the message (unlike with I<Logger>,
this can be different for each type);

=item * a color (for when the C<color> option is set);

=item * whether the messages should be indented according to the current persistent-indentation level (see below);

=item * whether unprintable characters should be escaped;

=item * whether a full or partial stack-trace should be shown;

=item * text to go before or after the message,
(or between the parts when 2 are present).

=back

=item * B<vMsg(self, level, msg1, msg2, color=None)>

Shorthand to issue such a message, with I<msgType> 'v' (verbose).

=item * B<hMsg(self, level, msg1, msg2, color=None, width=79)>

Shorthand to issue such a message, with I<msgType> 'h' ('heading').
Such messages get a blank line before, and a distinctive color or prefix.

=item * B<eMsg(self, level, msg1, msg2, color=None)>

Shorthand to issue such a message, with I<msgType> 'e' (error).
Error messages with a negative level cause termination.

=item * B<rMsg(self, level, color=None, width=79)

Produces a (possibly colored) horizontal rule of the given I<width>.

=back


=head2 Indentation control methods

=over

=item * B<MsgPush(self)>

Increment the message-nesting depth, causing indentation for messages
displayed via I<Msg>(). This is mainly useful for messages that reflect
successive tiers of processing on input data (e.g., notices about
each file, record, and field). The string to repeat to make indentation
can be set with I<setOption('indentString', string)>.

=item * B<MsgPop(self)>

Decrement the message indentation depth (see I<MsgPush>).

=item * B<MsgSet(self, n)>

Force the message indentation depth to I<n> (see I<MsgPush>).

=item * B<MsgGet(self)>

Return the current message indentation depth (see I<MsgPush>).

=back


=head2 Option control methods

=over

=item * B<setOption(name, value)

Sets the named option (see below) to the specified value.

=item * B<getOption(name)>

Returns the current value of the named option.

=back

=head3 List of available options

These are stored in instances of C<ALogger>, as .options['name'].

=over

* Option: I<badChar>

Print this character in place of control or other unprintables.
Default: '?'.

=item * B<Option>:I<color>

Use ANSI terminal colors? If not passed to the constructor,
this defaults to True if environment variable C<USE_COLOR> is set,
otherwise False. When set, the script tries to load my ColorManager package.
Failing that, it issues a message and falls back to using "*" before and
after colorized items.

=item * B<Option>:I<controlPix>

When set, displays U+24xx for control characters. Those Unicode characters
should show up as tiny mnemonics for the corresponding control characters.

=item * B<Option>:I<encoding>

Sets the name of the character encoding to be used (default C<utf-8>).

=item * B<Option>:I<direct>

If set, messages will be sent directly to C<stderr>.
Otherwise they go through C<logging.Logger>, which currently
means that no messages are issued if verbosity is not set higher than 0
(I prefer to have 0-level messages unconditionally displayed).

=item * B<Option>:I<filename>

This is just passed along to the like-named argument of the
Python I<logging.basicConfig>() method, and controls where messages go.
It defaults to C<sys.stderr>.

=item * B<Option>:I<indentString> (string)

The string used by I<Msg>() to build indentation according to the
I<indentation depth>
set by I<MsgPush>(), I<MsgPop>, etc. Default: "  " (two spaces).
Indentation is inserted before the message-type prefix (though after the
Logger prefix), and after each newline in the prefix, infix, and suffix
for the message (see I<defineMsgType>()).

=item * B<Option>:I<noMoreStats>

When set, trying to increment a I<msgStats> counter that is not already
known, results in an error message instead of the counter being quietly
created.

=item * B<Option>:I<verbose> (int)

I<vMsg>, I<hMsg>, and I<Msg> issue I<logging.info()> messages.
Thus, they are at I<logging> level B<20>, and so calling I<setVerbose>()
not only sets this option, but also force the I<logging> level to 20.
The I<Msg> calls take a first argument which is the minimum verbosity
required for the message to be shown.
This typically equals the number of times the I<-v> option
was specified on the command line.
This is completely separate from I<logging>'s own 0-50 'levels'.

If the I<verbose> option is not set at all,
then all such messages are displayed, regardless of their verbosity-level
(assuming that I<logging>'s message level is at most 20.

=back


=head1 Known bugs and limitations

If you don't call the constructor (or C<setVerbose()>) with a non-zero argument,
nothing will be printed.

This package is not integrated with the Python I<logging>
package's hierarchical loggers model.

There is not yet an option to remove the default text that I<logging>
prefixes to messages (such as "INFO:root:").


=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see L<http://creativecommons.org/licenses/by-sa/3.0/>.

For the most recent version, see L<http://www.derose.net/steve/utilities/>.

This script was derived (almost entirely by extraction)
in Oct. 2015 from C<sjdUtils.py>,
which in turn was ported from C<sjdUtils.pm> in Dec. 2011,
which was assembled from pieces in other of my scripts in Mar. 2011.
All those works are by the same author and are licensed under the same license
(CCLI Attribution-Sharealike 3.0 unported).


=head1 Options

=cut
    """
    if (len(sys.argv) > 1):
        print(descr)
        sys.exit()

    lg = ALogger(1)

    lg.info("sjd alogging.ALogger library.", stat='infoStat')
    lg.warning("A warning message")
    lg.error("An error message")

    lg.hMsg(0, "An hMsg message")
    lg.vMsg(0, "A vMsg message.")
    lg.MsgPush()
    lg.vMsg(0, "A vMsg message, indented.")
    lg.MsgPop()
    lg.vMsg(0, "A vMsg message.")
    lg.eMsg(0, "An eMsg message")

    lg.bumpStat('infoStat', 100)
    lg.showStats()
