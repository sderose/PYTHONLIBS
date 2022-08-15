#!/usr/bin/env python3
#
# alogging: messaging, logging, and statistics features from sjdUtils.py.
# Fairly close to Python's Logging package, but adds color and -v stacking.
# Written 2011-12-09 by Steven J. DeRose
#
# pylint: disable=W1406
#
import sys
import os
import re
import logging
import inspect
from collections import defaultdict
from typing import Iterable, Dict, Any

# Need this to do formatRec() right for it:
try:
    from xml.dom.minidom import NamedNodeMap
except ImportError:
    class NamedNodeMap(list): pass  # Just get it out of the way...

# "PYunicode" is a type that we can use in either Python 2 or 3.
#
PY3 = sys.version_info[0] == 3
if PY3:
    PYunicode = str
else:
    PYunicode = unicode  # noqa: F821  #pylint: disable=E0602

__metadata__ = {
    'title'        : "alogging",
    'description'  : "logging additions, for -v levels, stats, formatting, traceback,...",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2011-12-09",
    'modified'     : "2022-02-17",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

A logging facility, largely compatible with Python 'logging.Logger'.
Derived from `sjdUtils.py`'s messaging methods.

=Extra features compared to `logging.Logger`=

* Traditional *nix-style `-v` verbosity levels

* Better Unicode and non-printable char handling

* Definable named message types, with their own layouts

* Support for ANSI terminal color

* Controllable indentation levels

* Option to bump counters for any/all messages, making it easy
to keep and report error statistics

* `formatRec()` for nice layout of nested data structures.


=Usage=

    import alogging
    lg = alogging.ALogger()

    lg.warn(msg)
    lg.vMsg(2, msg1, msg2, color='red', stat='Input too long')

    print(lg.formatRec(myBigDataThing))

`warn`, `info`, `error`, `fatal`, `exception`, and `critical` work
like in Python `logging.warn()`, except that there is only one context,
and they accept an optional `stat` parameter (see below).

==vMsg() and its kin==

`vMsg()` takes an integer verbosity level, and only displays a message if the
current verbosity level is at least that high. This is typically controlled
by passing 0 or more `-v` options on a command line. It also allows a 2nd
message parameter, just for flexibility (probably should change to allow any
number).

`vMsg()` is meant for
verbose or informational messages `eMsg()` (now deprecated, use `error()`) is for errors,
while `hMsg` is for headings. They have different formatting
characteristics, which can be changed independently.

The `stat` option may be used to provide the name of a counter to increment.
This can be handy for tracking how many times various messages occur. Separate
messages may increment the same-named stat counter.
The named stats are created as needed.
Other `stat` methods include (see also the more detailed discussion below):

* `getStat('name')`
* `bumpStat('name')`
* `bumpStat('name', incrementAmount)`
* `setStat('name', newCounterValue)`
* `appendStat(self, stat, datum)` -- converts the stat to a list if it isn't
already, and appends `datum` to the list.
* `showStats()`
* `setOption('noMoreStats', True)` -- this will prevent any new stat names
from being accepted (causing an exception on any such attempt).

You can control the indentation level of messages with `MsgPush()` and `MsgPop()`.

Verbosity can be set with `setOption("verbose", n)` or `setVerbose(n)`.

==formatRec(self, obj, options=None)==

This will fairly nicely format any (?) Python object as an annotated outline.
It knows about the basic
scalar and collection datatypes, as well as basic numpy and PyTorch vector types.
For objects, it knows to show their non-callable properties.

`options` should be a dict, which may include:
* `obj`       -- The data to be displayed.
* `keyWidth`  -- Allow this much room for dict keys, in trying to line things up. Default: 14.
* `maxDepth`  -- Limit how far down nested collections will be displayed. Default: 3.
* `maxItems`  -- Limit how many items of lists will be displayed.
* `maxString` -- Limit number of characters to show for strings.
* `propWidth` -- Allow this much room for object property names.
* `quoteKeys` -- Put quotes around the keys of dicts. Default: False
* `showSize`  -- Display len() for collection objects.
* `specials`  -- Display callable and "__"-initial members of objects.
* `stopTypes`  -- A dict of types or typenames, which are to be displayed
as just present, without all their (non-callable) properties. At the moment,
these are checked by == on the type and the typename, so subclasses must be
explicitly listed to be affected.

==formatPickle(self, path)==

This loads a pickle file, and then runs `formatRec()` on it and returns the
result.

===Layout conventions===

Lists and dictionaries get a header line indicating their type and length,
and the usual delimiters then enclose their members, each on a separate line.
Members that are themselves collections, do the same thing but indented one
more level. List items are prefixed by their index (like "#0:"), and dict
items by their keys (in quotes). Values in dicts and objects are aligned
vertically by padding their keys/names to `keyWidth` or `propWidth` columns.

Object are displayed pretty much like dicts, but using "<<" and ">>" to surround
their members, and putting "." before property names, unlike quoted dict keys.
Callables, and properties beginning with "__", are omitted unless the 'specials'
option is set.

numpy and PyTorch vectors are not shown in their entirety, but do display their
dimensionality, length, and item datatype.

==getLoc(startLevel=0, endLevel=0)==

gets a decently-formatted partial or complete stack trace
(not counting internals of `alogging` itself).

==getCaller(self)==

Just returns the name of the (direct) caller of `alogging`, using Python `inspect`.


==Notes on speed==

With either this package or Python `logging`,
calling a logging/messaging method does cost
time even if the message doesn't end up getting displayed or saved.
This can be very significant for messages in inner loops.
It can also be significant if evaluating the ''parameters'' being passed
is expensive, since that is done before the logging function is actually
called (so even if the logging function returns instantly the setup time
is still taken).

You can get reduce such overhead by:

* (a) removing or commenting out the calls when no longer needed,
especially in inner loops.
You may want to use a profiler to be sure which ones actually matter.

* (b) putting code under an "if", for example "if (False)",
"if (args.verbose)", or (even better)
"if (__debug__)" (which makes them go away when Python is run with the `-O`
option.

* (c) Use a preprocesser to remove some/all logging statements
for production. See the discussion at
[http://stackoverflow.com/questions/482014].


=General Methods=

* ''setVerbose(v)''

The initial verbosity level can be set as a parameter to the constructor.
This method lets you reset it later.
Otherwise, messages whose first argument's magnitude
is greater than ''v'' are discarded (verbosity levels are perhaps best
thought of as priorities). This means that verbosity runs like `-v` flags in
many *nix programs, but opposite from Python `logging` levels.

''setVerbose(v)'' is just shorthand for ''setOption("verbose", v)''.

* ''getVerbose''()

Return the current verbosity level (see ''setVerbose'').
This is just shorthand for ''getOption("verbose")''.

* '''findCaller(self)

Returns the name of the function or method that called ''findCaller''().

* ''pline(label, n, width=None, dotfill=0, fillchar='.', denom=None)''

Display a line consisting of ''label'' (padded to ''width''),
and then the data (''n'').
''width'' defaults to the value of the ''plinewidth'' option.
The data is displayed in a type-appropriate way after that.

If ''dotfill'' is greater than 0, then every ''dotfill'''th line will use
''fillchar'' instead of space for padding ''label''. For example,
''dotfill=3'' makes every third line be dot-filled.

If ''denom'' is greater than 0, another column is displayed, showing ''n/denom''.

=='logging'-like messaging methods==

=The following methods are largely compatible with methods in the Python
`logging` package. However, there is no tree of instances, just
an ''ALogger'' object. The format string for each type is kept in
`msg.formats{typename}`, and defaults to ''%(msg}\\n''.
These methods are still experimental.

''kwargs'' can be used to provide a dictionary of names whose
values are filled in to such format strings via ''%(name)''.
This is only useful if you also set a format
string that includes references to them. These names are defined by default:

* '''info(self, msg, *args, **kwargs)'''

Issues an informational message, like Python `logging`.

* '''warning(self, msg, *args, **kwargs)'''

Issues a warning message, like Python `logging`.

* '''error(self, msg, *args, **kwargs)'''

Issues an error message, like Python `logging`.

* '''critical(self, msg, *args, **kwargs)'''

Issues an critical error message, like Python `logging`.

* '''debug(self, msg, *args, **kwargs)'''

Issues a debugging message, like Python `logging`.

* '''log(self, level, msg, *args, **kwargs)'''

Issues an otherwise unspecified log message, like Python `logging`.

* '''exception(self, msg, *args, **kwargs)'''

Issues an exception message, like Python `logging`.

==Additional messaging methods==

* ''eMsg'' ''(level, message1, message2, color, text, stat)''

Specifying a ''level'' less than 0 is fatal.
''Deprecated'', replaced by ''warning''(), ''error''(), and ''fatal''().

* ''hMsg'' ''(level, message1, message2, color, text, stat)''

''Deprecated''. Instead, start another kind of message with "====", which will
generate whitespace and a separator line.

* ''vMsg'' ''(level, message1, message2, color, text, stat)''

The levels of messages here are separate from Logger's implicit
levels for ''warning'', ''error'', etc.

===Treatment of message with `eMsg`, `vMsg`, `hMsg`, etc.===

The `ALogger`-specific messaging methods do the following:

** If the message is not high enough priority compared
to the ''verbose'' setting, the method simply returns.

''Important Note'': All ''vMsg'' messages are
''information''-level as far as ''Logger'' is concerned, and so ''none''
of them will show up unless you're showing such messages. The ''level''
argument to ''vMsg'' is a further filter, to support verbosity levels
as are very common for *nix utilities.

** Converts the message to UTF-8.

** Adds ''prefix'' before ''m1'',
''infix'' between ''m1'' and ''m2'', and/or ''suffix'' after ''m2''.

** If ''indent'' is True, creates an indent string for
the level set by ''MsgPush''(), etc., and inserts it
before the prefix and after each newline in the prefix, infix, and suffix.

** If ''func'' is True, inserts the name of the calling function
before ''m1''.

** Colorizes the prefix (including any applicable preprefix, infix,
and indentation whitespace) and ''m1''.

** If ''escape'' is True, passes ''m1'' and ''m2'' through ''showInvisibles'',
which turns control characters, whitespace, etc. to visible representations.

** If ''nLevels'' ''' 0, appends that many levels of stack-trace information.

** Displays the resulting message. It goes to STDERR by default,
but to STDOUT if the ''stdout'' option is set.

These items can be filled in by a message format:

* 'function'

* 'filename'

* 'index'

* 'lineno'

* 'asctime'

* 'type'

* 'msg'

==Message types==

* ''defineMsgType''(type, color=None, nLevels=None, func=None,
prefix=None, infix=None, suffix=None, escape=None, indent=None)

DEPRECATED

Create or modify a named "type" of message.
Types "v", "e", and "h" are predefined but may be modified.
Type "x" is reserved.

The parameters other than ''type'' are all optional and default to `None`.
When a parameter is `None`, the property is left
unchanged for an already-existing message type.
However, for an entirely new message type the property is set to
the corresponding default value shown below:

* ''type'': a name for the type of message, to identify it to ''Msg''().
Required.

* ''color'': What color to display the message in (if color is enabled).
Default: `/yellow`.
Note that the `_Msg` methods can take a `color` argument to override this for
particular messages.

* ''nLevels'': Number of levels of stack-trace to display
(not yet supported). Default: `0`.

* ''func'': If True, display the calling function's name.
Default: `False`.

* ''prefix'': A string to display before the start of each message.
For example, "h"
messages prefix "\\n******* ", to make them stand out like headings.
Default: "".

* ''infix'': A string to display between the parts (''m1'' and ''m2'')
of each message. For example, one might want ''m2'' always on a separate line,
and therefore set ''infix'' to `\\n`.
Default: "".

* ''suffix'': A string to display after the end of each message.
Default: "".

* ''escape'': Turn non-printable characters in the message to printable.
This is done using ''showInvisibles''() (q.v.).
Default: `True`.
Note that the `Msg` methods accept an `escape` parameter to override this for
particular messages.

* ''indent'': Whether to indent messages according to the level set
using ''vPush''(), ''vPop''(), etc.
Default: `True`.

==Statistics-keeping methods==

This package maintains a list of named "statistics". Typically, each
one has just a counter, which you increment by passing the static name
to the `stat"` parameter of any of the messaging calls described in the
next section. You do not need to declare or initialize such statistics
(although you can set them all and then set the `noMoreStats` option
to prevent creating any more).

The statistics can all be printed out (for example, just before your
main program ends). For example:

    recnum = 0
    for rec in open(foo, 'r').readline():
        recnum += 1
        if (len(rec) > 999):
            lg.error("Line %d too long (%d characters)." % (recnum, len(rec)),
                    stat="Too long")
    lg.setOption('plineWidth', 45)  # Allow space for long stat names
    lg.showStats()

An ''experimental'' feature allows you to use "/" in a stat name, in
order to group statistics for reporting. If used, such statistics will
be grouped (well, they would be anyway by alphabetization),
and indented under the common (pre-/) part, which will be printed
with the total counts for all stats in the group. This is especially useful
for defining subtypes of errers, or attaching small data to them. The
example above could be modified to keep count of all the specific
excessive record-lengths, by changing the ''eMsg'' call to:

    lg.error("Line %d too long (%d characters)." % (recnum, len(rec)),
            stat="Too long/%d" % (len(rec))

In addition to the `stat` parameter on various messaging methods, there
are methods for manipulating the stats independently of messages:

* ''defineStat(self, stat)''

Initialize the given stat (to 0). This is optional (that is, you can just
mention a stat and it will be created if necessary).

* ''bumpStat(self, stat, amount=1)''

Increment the given stat by the specified ''amount'' (default: 1).

* ''appendStat(self, stat, datum)''

Convert the given stat to a list if it is not one already, and ''append''
the ''datum'' to the list.

* ''setStat(self, stat, value)''

Set the given stat to the given ''value''.

* ''getStat(self, stat)''

Return the value of the given stat.

* '''showStats(self, zeros=False, descriptions=None, dotfill=0, fillchar='.', onlyMatching='', lists='len')

Display all the accumulated statistics,
each with its name and then its value.
Each statistic is printed used ''pline''(), so is subject to the formatting
described there.

Stats with a value of 0 are not shown unless
the ''zeros'' parameter is set to True.

If ''descriptions'' is specified, it must be a dict that maps (some or all) of
the stat names to strings to be printed in place of the name. This is useful
if you want short/compact names to pass to ''bumpStat'', messaging, or other
methods that take a stat name; and yet want long, more user-readable
error descriptions for the report.

''Note'': See above re. the (experimental) use of "/" in statistic names,
to group and accumulate more detailed statistics.

''dotfill'': Use dot-fills for readability (@see pline()).

''fillchar'': Use this char as the "dot" for dotfill.

''onlyMatching'': a regex. Only stats whose names match it are displayed.

''lists'': For stats that are lists (see ''appendStat''()), specifies
how to show those lists:

* 'omit': do not show at all

* 'len': just show the list name and length

* 'uniq': sort and uniqify, then show the list

* 'uniqc': sort and uniqify with count, then show the list

* otherwise: show the whole list

* ''clearStats(self)''

Remove all statistics.

==Additional messaging methods==

This package adds several more calls. The first is simply ''fatal'',
which issues a ''log''() message with level 60 and then raises an
exception (if uncaught, this will lead to a stack trace and termination).

The numbers message methods, such as ''info1'' check the verbosity level 
(set via ''setVerbose()''), and discard the message if it is not at least
as high as the number at the end of the method name.
This supports the common *nix command-line usage, where the
amount of messaging is increased by using one or more ''-v'' options.

==Indentation control methods==

* ''MsgPush(self)''

Increment the message-nesting depth, causing indentation for messages
displayed via ''Msg''(). This is mainly useful for messages that reflect
successive tiers of processing on input data (e.g., notices about
each file, record, and field). The string to repeat to make indentation
can be set with ''setOption('indentString', string)''.

* ''MsgPop(self)''

Decrement the message indentation depth (see ''MsgPush'').

* ''MsgSet(self, n)''

Force the message indentation depth to ''n'' (see ''MsgPush'').

* ''MsgGet(self)''

Return the current message indentation depth (see ''MsgPush'').


==Option control methods==

* '''setOption(name, value)'''

Sets the named option (see below) to the specified value.

* ''getOption(name)''

Returns the current value of the named option.

===List of available options===

These are stored in instances of `ALogger`, as .options['name'].

* Option: ''badChar''

Print this character in place of control or other unprintables.
Default: '?'.

* ''Option'':''color''

Use ANSI terminal colors? If not passed to the constructor,
this defaults to True if environment variable `CLI_COLOR` is set,
otherwise False. When set, the script tries to load my ColorManager package.
Failing that, it issues a message and falls back to using "*" before and
after colorized items.

* ''Option'':''controlPix''

When set, displays U+24xx for control characters. Those Unicode characters
should show up as tiny mnemonics for the corresponding control characters.

* ''Option'':''encoding''

Sets the name of the character encoding to be used (default `utf-8`).

* ''Option'':''filename''

This is just passed along to the like-named argument of the
Python ''logging.basicConfig''() method, and controls where messages go.
It defaults to `sys.stderr`.

* ''Option'':''indentString'' (string)

The string used by ''Msg''() to build indentation according to the
''indentation depth''
set by ''MsgPush''(), ''MsgPop'', etc. Default: "  " (two spaces).
Indentation is inserted before the message and after each newline.

* ''Option'':''noMoreStats''

When set, trying to increment a ''msgStats'' counter that is not already
known, results in an error message instead of the counter being quietly
created.

* ''Option'':''verbose'' (int)

''vMsg'', ''hMsg'', and ''Msg'' issue ''logging.info()'' messages.
Thus, they are at ''logging'' level ''20'', and so calling ''setVerbose''()
not only sets this option, but also force the ''logging'' level to 20.
The ''Msg'' calls take a first argument which is the minimum verbosity
required for the message to be shown.
This typically equals the number of times the ''-v'' option
was specified on the command line.
This is completely separate from ''logging'''s own 0-50 'levels'.

If the ''verbose'' option is not set at all,
then all such messages are displayed, regardless of their verbosity-level
(assuming that ''logging'''s message level is at most 20.


=Related commands=

My `ColorManager.py`: provides color support when requested.


=Known bugs and limitations=

If you don't call the constructor (or `setVerbose()`) with a non-zero argument,
nothing will be printed.

This package is not integrated with the Python ''logging''
package's hierarchical loggers model.

There is not yet an option to remove the default text that ''logging''
prefixes to messages (such as "INFO:root:").

Seems to be a problem with `maxItems`, and with suppressing callables in `formatRec()`.

`formatRec()` could use more options to shorten long displays, such as:

* suppress all object properties with value None
* suppress a given list of properties
* don't descend into certain object types
* use a caller-supplied displayer method


=To do=

* I don't really like that "stats" part, discard it.

* Sync to Py logger:
    rename file to aLogger
    drop 'direct' option
    drop defineMsgType (globalchange, colorManager, lessData, ...)
    drop versions of this package from `Volsunga
    drop any redundant code from sjdUtils
    drop prefix/infix/suffix
    warn(0 -'''w0...), etc.
    drop stat arg
    vMsg->i...
    eMsg->e...
    hMsg??

* Maybe do a level-transform from -v**n to logger levels?
    Py name   Py lvl  
    CRITICAL      50
    ERROR         40
    WARNING       30
    INFO          20
    DEBUG         10
    NOTSET        0

So if I get
    mylog(0, msg) it should show unconditionally, so 29 (and setLevel that)
    mylog(1, msg) it should show if they said -v, so level is 28
    mylog(2, msg) is level 27
    ...

So argparse and setVerbose do:
    lg.setLevel(29-args.verbose)

Then we can do:
    def vlog(lvl, msg):
        lg.log(29-lvl, msg)

* Option to get rid of "INFO:root:" prefix from logging package.

* Consider switching to "logv = lambda lvl, msg: info(msg) if lvl<=args.verbose else None"


* formatRec():
** Move out to be a separate library?
** Support more numpy, PyTorch classes (and have a way to extend? maybe just tostring()?)
Or have a dict of types, mapping to their formatter functions.
** Protect against circular structures (started 2022-02-17 via 'noDups' option).
** Option to only show first N of each class/type.
** Perhaps accept maxItems as a dict, mapping types to limits?
** For collections of length 1, put on same line.
** Coalesce short lists (and matrices?) of numbers.
** Option to make strings visible and/or ASCII.
** Implement key and property sorting options.
** Option to re-display item name after closing ">>".
** Let stopNames option take list, not just dict. When a dict, allow value to
say which sub-item to use as the key, and only show that.


=History=

* 2011-12-09: Port from Perl to Python by Steven J. DeRose.
(... see `sjdUtils.py`)
* 2015-10-13: Split messaging features from `sjdUtils` to new `ALogger`.
Integrate with Python `logging` package.
* 2015-12-31ff: Improve doc.
* 2018-04-02: Add `direct` option to make Anaconda Nav happier.
* 2018-07-29: Add `showSize` option to `formatRec`.
* 2018-08-07: Add `quoteKey` and `keyWidth` options to `formatRec()`.
* 2018-08-17: Add `maxItems` option to `formatRec()`.
* 2020-03-02: New layout, doc to MarkDown, document `formatRec()` better. Lint.
* 2020-03-06: Add `formatRec()` support for numpy and Torch vectors.
Move `formatRec()` options to a dict instead of individual parameters, and make
them inherit right. Add `propWidth`, `noExpand`, `disp_None`.
Improve formatting.
* 2020-08-19: Cleanup, lint, add some type-hinting. Improve messaging when
Linux command `dircolors` is not available. POD to MarkDown.
* 2020-09-23: Add forward for `colorize()`, and a fallback. lint.
* 2020-10-07: Add formatPickle().
* 2020-12-10ff: Drop 'direct' option, start dropping defineMsgType
and [evh]Msg() forms, in favor of warningN(), etc. Add verboseDefault. lint.
* 2021-07-09: formatRec(): Fix maxDepth limiting, clean up option handling.
Rename `noExpand` to `stopTypes`, add `stopNames`.
* 2022-02-17: formatRec: Fix numpy ndarray shape reporting. Make depth limit
message report type of next thing, and still report scalars. Add 'maxString'.
Drop headingN() methods, and make log() insert separator space and line if the
message starts with "====". Planning to lose hMsg(), defined msg types, etc.
Add 'noDups'. Drop rMsg(), MsgRule, defineMsgType(), Msg().
* 2022-07-27: Add indent option to pline. More type-hints.

=Rights=

Copyright 2019 by Steven J. DeRose. This work is licensed under a Creative
Commons Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].

This script was derived (almost entirely by extraction)
in Oct. 2015 from `sjdUtils.py`,
which in turn was ported from `sjdUtils.pm` in Dec. 2011,
which was assembled from pieces in others of my scripts in Mar. 2011.
All those works are by the same author and are licensed under the same license
(CCLI Attribution-Sharealike 3.0 unported).


=Options=
"""


###############################################################################
#
class ALogger:
    """A default verbosity level.
    """
    verboseDefault = 0

    def __init__(self,
        verbose:int  = None,       # Level of detail for 'info' messages.
        color        = None,
        filename:str = None,
        encoding:str = 'utf-8',
        level:int    = None,
        options:dict = None
        ):

        if (color is None):
            color = ('CLI_COLOR' in os.environ)

        if (verbose is None):
            verbose = ALogger.verboseDefault

        self.options = {
            'verbose'        : verbose,     # Verbosity level
            'color'          : color,       # Using terminal color?
            'filename'       : filename,    # For logging pkg
            'encoding'       : encoding,    # Assumed char set
            # Set a level that doesn't hide too much:
            # CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0
            'level'          : level or 20, # For logging filtering

            'badChar'        : "?",         # Substitute for undecodables
            'controlPix'     : True,        # Show U+24xx for control chars?
            'indentString'   : "  ",        # For pretty-printing
            'noMoreStats'    : False,       # Warn on new stat names
            'plineWidth'     : 30,          # Columns for label for pline()
            'displayForm'    : "SIMPLE",    # UNICODE, HTML, or SIMPLE
        }

        self.optionTypes = {
            'verbose'        : int,
            'color'          : bool,
            'filename'       : str,
            'encoding'       : str,
            'level'          : int,
            'direct'         : bool,

            'badChar'        : str,
            'controlPix'     : bool,
            'indentString'   : str,
            'noMoreStats'    : bool,
            'plineWidth'     : int,
            'displayForm'    : str,
        }

        if (options is not None):
            for k, v in options.items():
                if (k not in self.options):
                    raise KeyError("Unrecognized option '%s'." % (k))
                self.options[k] = self.optionTypes[k](v)

        if (filename):
            logging.basicConfig(level=self.options['level'],
                                filename=self.options['filename'],
                                format='%(message)s')
        else:
            logging.basicConfig(level=self.options['level'],
                                format='%(message)s')
        self.lg             = logging.getLogger()

        self.msgStats       = {}
        self.msgIndentLevel = 0   # How far are we indenting infos?
        self.errorCount     = 0   # Total number of errors logged
        self.plineCount     = 1   # pline() uses for colorizing

        self.unescapeExpr   = re.compile(r'_[0-9a-f][0-9a-f]')

        # Also available via ColorManager.uncolorizer()
        self.colorRegex     = re.compile(r'\x1b\[\d+(;\d+)*m')
        self.colorManager   = None
        if (self.options['color']): self.setupColor()

        # String to display to delimit types of objects
        # Factor out string-quoting too, to make it distinctive.
        if (self.options['displayForm'] == "UNICODE"):
            self.openDict = "{"; self.closeDict = "}"
            self.openList = "["; self.closeList = "]"
            self.openObject = "\u00ab"; self.closeObject = "\u00bb"  # ANGLE BKT
            self.disp_None = "\u2205"  # NULL SET
        elif (self.options['displayForm'] == "HTML"):
            self.openDict = "<DL>"; self.closeDict = "</DL>"
            self.openList = "<OL>"; self.closeList = "</OL>"
            self.openObject = "<UL>"; self.closeObject = "</UL>"
            self.disp_None = "&#x2205;"  # NULL SET
        else:  # (self.options['displayForm'] == "SIMPLE"):
            self.openDict = "{"; self.closeDict = "}"
            self.openList = "["; self.closeList = "]"
            self.openObject = "<<"; self.closeObject = ">>"
            self.disp_None = "*NONE*"

        self.aggregatesSeen = None  # For formatRec()
        
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

    def colorize(self, argColor='red', s="", endAs="off",
        fg='', bg='', effect=''):
        if (self.colorManager):
            return self.colorManager.colorize(argColor=argColor, msg=s,
                endAs=endAs, fg=fg, bg=bg, effect=effect)
        return "*" + s + "*"


    ###########################################################################
    # Options
    #
    def setALoggerOption(self, name, value=1):
        return(self.setOption(name, value))

    def setOption(self, name, value=1):
        """Set option ''name'' to ''value''.
        """
        if (name not in self.options):
            return(None)
        self.options[name] = self.optionTypes[name](value)
        return(1)

    def getALoggerOption(self, name):
        return(self.getOption(name))

    def getOption(self, name):
        """Return the current value of an option (see setOption()).
        """
        return(self.options[name])

    def setVerbose(self, v:int):
        """Set the degree of verbosity for messages to be reported.
        This is NOT the same as the logging package 'level'!
        """
        v = int(v)
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
        except re.error as e:
            sys.stderr.write("Regex error: %s\n" % (e))
        return(s)


    ###########################################################################
    # Set default options for predefined message-types v, e, h, x.
    #
    def defineMsgTypes(self):
        """
        Define the set of built-in message types.
        """
        assert False

    def defineMsgType(self, *_args, **_kwargs):
        """Create a new named message type, for use with 'Msg()'.
        Each type owns a bunch of formatting information.
        Arguments default to None, so user can leave items unchanged
        if the type is already defined.
        """
        assert False, "defineMsgType has been dropped."

    def getMsgDefs(self):
        """
        """
        assert False

    def getPickedColorString(self, argColor:str, msgType:str=None):
        """Return color escape codes (not name!) -- the requested color if any,
        else the default color for the message type.
        """
        assert not msgType
        if (not self.options['color']):
            return("","")
        if (argColor and argColor in self.colorStrings):
            return(self.colorStrings[argColor], self.colorStrings['off'])
        return("","")


    ###########################################################################
    # Manage persistent indentation of xMsg calls.
    #
    def MsgPush(self):
        """Increment the message indent level, causing indentation for messages
        displayed via ''vMsg''. This is mainly useful for messages that reflect
        successive tiers of processing on input data (e.g., notices about
        each file, record, and field). The string to repeat to make indentation
        can be set with ''setOption('indentString', string)''.
        """
        self.msgIndentLevel += 1

    def MsgPop(self):
        """Decrement the message-nesting level (see ''MsgPush'').
        """
        if (self.msgIndentLevel>0): self.msgIndentLevel -= 1

    def MsgSet(self, n):
        """Force the message-nesting level to ''n'' (see ''MsgPush'').
        """
        self.msgIndentLevel = n

    def MsgGet(self):
        """Return the message-nesting level (see ''MsgPush'').
        """
        return(self.msgIndentLevel)


    ###########################################################################
    # Python 'Logger'-compatible calls:
    #
    # The type-specific calls handles statistic-updating, because that should
    # happen whether or not the level filters out actual display.
    #
    def log(self, level, msg, stat=None, **kwargs):  # ARGS!
        if (stat): self.bumpStat(stat)
        if (self.options['verbose'] < level): return
        self.directMsg(msg, **kwargs)
    def debug(self, msg, stat=None, **kwargs):         # level = 10
        if (stat): self.bumpStat(stat)
        self.directMsg(msg, **kwargs)
    def info(self, msg, stat=None, **kwargs):          # level = 20
        if (stat): self.bumpStat(stat)
        self.directMsg(msg, **kwargs)
    def warning(self, msg, stat=None, **kwargs):       # level = 30
        if (stat): self.bumpStat(stat)
        self.directMsg(msg, **kwargs)
    def error(self, msg, stat=None, **kwargs):         # level = 40
        if (stat): self.bumpStat(stat)
        self.directMsg(msg, **kwargs)
    def exception(self, msg, stat=None, **kwargs):     # level = 40
        if (stat): self.bumpStat(stat)
        self.directMsg(msg, **kwargs)
    def critical(self, msg, stat=None, **kwargs):      # level = 50
        if (stat): self.bumpStat(stat)
        self.directMsg(msg, **kwargs)


    ###########################################################################
    # Level-specific shorthand (replacing old log-style level param).
    #
    def info0(self, msg, **kwargs): self.log(0, msg, **kwargs)
    def info1(self, msg, **kwargs): self.log(1, msg, **kwargs)
    def info2(self, msg, **kwargs): self.log(2, msg, **kwargs)
    def info3(self, msg, **kwargs): self.log(3, msg, **kwargs)
    def info4(self, msg, **kwargs): self.log(4, msg, **kwargs)

    def warning0(self, msg, **kwargs): self.log(0, msg, **kwargs)
    def warning1(self, msg, **kwargs): self.log(1, msg, **kwargs)
    def warning2(self, msg, **kwargs): self.log(2, msg, **kwargs)
    def warning3(self, msg, **kwargs): self.log(3, msg, **kwargs)
    def warning4(self, msg, **kwargs): self.log(4, msg, **kwargs)

    def directMsg(self, msg, **kwargs) -> None:
        """Pretty much everything ends up here.
        'stat' are should have been handled and removed by caller.
        """
        #assert ('stat' not in kwargs)
        if (msg.startswith("====")):
            msg = "\n%s\n%s" % ("=" * 79, msg.lstrip('='))
        ender = kwargs['end'] if 'end' in kwargs else "\n"
        if (not msg.endswith(ender)): msg += ender
        #msg2 = re.sub(r'\n', '*', msg)
        if ('color' in kwargs):
            if (not self.colorManager): msg += " (color not enabled)"
            else: msg = self.colorManager.colorize(kwargs['color'])
        sys.stderr.write(msg)

    # Pass through a few useful methods?
    def setLevel(self, lvl) -> None:
        self.lg.setLevel(lvl)

    # Add fatal(): level 60, and raise exception after.
    #
    def fatal(self, msg, stat=None, **kwargs) -> None:
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
    def vMsg(
        self, 
        verbose:int, 
        m1:str, 
        m2:str="", 
        color:str=None, 
        indent:bool=True, 
        stat:str=""
        ) -> None:
        """Issue a 'verbose' (msgType 'v') info message.
        """
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose'] < verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, indent=indent)
        self.info(m)

    # Change called over to call error() directly, then delete eMsg().
    def eMsg(
        self, 
        verbose:int, 
        m1:str, 
        m2:str="", 
        color:str=None, 
        indent:bool=True, 
        stat:str=""
        ) -> None:
        """Issue an error message.
        """
        self.errorCount += 1
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose'] < verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, indent=indent)
        self.info(m)
        if (verbose<0):
            raise AssertionError("alogging:eMsg with level %d." % (verbose))

    def hMsg(
        self, 
        verbose:int, 
        m1:str, 
        m2:str="", 
        color:str=None, 
        indent:bool=True, 
        stat:str=""
        ) -> None:
        """Issue a 'heading' (msgType 'h') message.
        DEPRECATED in favor of prefixing "====" to other messages.
        """
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose'] < verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, indent=indent)
        self.info(m)

    # Messages of various kinds (sync with Perl version)
    def Msg(
        self,
        level:int,  # vs. defined type
        m1:str,
        m2:str="",
        color:str=None,
        escape:str=None,
        stat:str=None,
        verbose:int=0
        ) -> None:
        """Issue a message of the given ''msgType'' (see ''defineMsgType).
        See also the wrappers ''hMsg''(), ''vMsg''(), and ''hMsg''().

        Checks ''verbose'' against the value of the 'verbose' option; if that
        option has actually been set, ''and'' is lower, return without display.
        Otherwise, call Logger's ''info''() to actually issue the message.

        * ''msgType'' Mnemonic 'type' of the message, per defineMsgType''().

        * ''message1'' Text to display, in the color specified by ''color''
        or for the message type.

        * ''message2'' (optional) additional message, to display uncolored.
        If ''text'' is true, ''showInvisibles'' and bracketing apply.
        A newline appears after ''message2''.

        * ''color'' the color in which to display ''message1''.
        For backward compatibility, ''color'' may be a literal ANSI color
        escape sequence, such as ''\\e[31m'', etc.

        * ''text'' Send ''m1'' through ''showInvisibles''().

        * ''stat'' Increment the named statistic, even if the message will not
        appear.
        The counts reside in a dictionary in `msgStats`.
        See ''showStats''() for displaying a list of all the collected counts.
        Also see ''bumpStat'', ''setStat'', ''appendStat'', and ''getStat''.
        """
        assert False, "Don't use Msg() any more!"
        if (stat!=""): self.bumpStat(stat)
        if (self.options['verbose']<verbose): return
        m = self.assembleMsg(m1=m1, m2=m2, color=color, escape=escape)
        self.lg.info(m)
        return

    def assembleMsg(
        self,
        m1:str,
        m2:str="",
        color:str=None,
        escape:bool=False,  # Make chars all visible?
        indent=None,        # Indent by msgLevel?
        nLevels:int=0,      # Show some stack trace?
        msgType:str=None,
        func:bool=False     # Show calling function name
        ) -> str:
        """Assemble the components of a message to be printed.
        bumpStat also happens there.
        Parameters corresponding to definedMsgType() ones, are overrides.
        """
        assert msgType is None

        locMsg = ""
        if (nLevels>0):
            locMsg = "TRACEBACK:\n" + self.getLoc(3, 3+nLevels) + "\n"
        if (escape):
            m1 = self.showInvisibles(m1)
            m2 = self.showInvisibles(m2)
        pre = ""
        if (indent): pre = (self.options['indentString'] * self.msgIndentLevel)
        caller = ""
        if (func): caller = self.getCaller() + ": "
        (on, off) = self.getPickedColorString(color, msgType)
        m = on + pre + caller + self.insureUnicode(m1) + off + self.insureUnicode(m2)
        if (locMsg): m += "\n" + locMsg
        return(m)

    def getLoc(self, startLevel:int=0, endLevel:int=0) -> str:
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

    def insureUnicode(self, s:str):
        if (not s): return ""
        if (isinstance(s, str)): return s
        try:
            s2 = s.decode(encoding='latin-1')
        except UnicodeDecodeError:
            s2 = re.sub(r'[\x80-\xFF]', self.options['badChar'], s)
        return s2
        
        
    ###########################################################################
    # Statistic-keeping
    #
    def defineStat(self, stat:str) -> None:
        """Create a new statistic. Optional, because stats are quietly created
        as needed. However, ''setOption('noMoreStats', True) prevents this.
        """
        self.msgStats[stat] = 0

    def bumpStat(self, stat:str, amount:int=1) -> None:
        """Increment the named statistic, by ''amount'' (default: 1).
        If the name contains "/", it splits there. The first part is
        the overall stat name, which will be stored as a dict, with
        entries made and counted for each value of the second part.
        """
        if (stat in self.msgStats):
            self.msgStats[stat] += amount
        elif (self.options['noMoreStats']):
            self.error(0, "alogging.bumpStat: unknown stat '%s'." % stat)
        else:
            self.msgStats[stat] = amount

    def appendStat(self, stat:str, datum:Any) -> None:
        """Append to the named statistic (converting to a list first if needed)
        """
        if (stat in self.msgStats):
            self.msgStats[stat].append(datum)
        elif (self.options['noMoreStats']):
            self.error(0, "alogging.appendStat: unknown stat '%s'." % stat)
        else:
            self.msgStats[stat] = [ datum ]

    def setStat(self, stat:str, value:Any) -> None:
        """Force the named statistic to the given value.
        """
        if (stat in self.msgStats):
            self.msgStats[stat] = value
        elif (self.options['noMoreStats']):
            self.error(0, "alogging.setStat: unknown stat '%s'." % stat)
        else:
            self.msgStats[stat] = value

    def getStat(self, stat:str) -> Any:
        """Return the current value of the named statistic.
        """
        if (stat in self.msgStats): return(self.msgStats[stat])
        return(0)

    def showStats(
        self,
        zeros:bool=False,
        descriptions:dict=None,
        dotfill:bool=0,
        fillchar:str='.',
        onlyMatching:str='',
        lists:str='len'
        ):
        """Display all the stat values, via ''pline''()
        @param ''zeros'': if not True, statistics counts of 0 are excluded.
        @param ''descriptions'': map from names to a ''label'' argument to
            have ''pline''() display. Unmapped names use the name as label.
        @param ''dotfill'': Use dot-fills for readability (@see pline()).
        @param ''fillchar'': Use this char as the "dot" for dotfill.
        @param ''onlyMatching'': a regex, only stats that match it appear.
        @param ''lists'': For 'appendStat' stats, how to show the vectors:
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
            parts = k.split(sep='/')
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
            if (descriptions and k in descriptions):
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
                    for k2 in sorted(dict(uv).keys()):
                        disp += "%s:%d, " % (k2, uv[k2])
                    self.pline("  "+label, disp)
                else: self.pline("  "+label, v)
            elif (v!=0 or zeros):
                nPrinted += 1
                pLabel = "  "+label
                if ('/' in k): pLabel = "    " + pLabel
                self.pline(pLabel, v, dotfill=dotfill, fillchar=fillchar)
        if (nPrinted==0):
            self.lg.info("    (no stats logged)")

    def pline(
        self, 
        label:str,          # label, in 'width' columns
        n:Any,              # value, in 2nd area(type-dependent alignment)
        denom:float=None,   # if present, also display n/denom
        dotfill:int=0,      # if set to D, dot-fill every D-th line
        fillchar:str='.',   # the dot fill character
        width:int=None,     # width of the label area
        quiet:bool=False,   # if set, return it but don't display
        indent:int=0,       # Add this many leading spaces
        ) -> str:
        """Display a pair of a label and an aligned value.
        'widt´h' defaults to the `plineWidth` option).
        If ''denom'' ('denominator') is non-zero, and ''n'' is an int or
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
                valueField = chr(n)
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
        if (indent): msg = (" " * indent) + msg
        if (not quiet): self.lg.info(msg)
        return(msg)

    def clearStats(self) -> None:
        self.msgStats = {}

    # dir() can be wrong, e.g., if the object has a custom __getattr__.
    # Does not seem to work for Cython objects such as in Spacy.
    #
    def dirMain(self, obj:Any, includeCallables:bool=False) -> Dict:
        tdict = {}
        for k in dir(obj):
            if (k.startswith("__") or k == "_"): continue
            try:
                if (not includeCallables and callable(getattr(dir, k))):  # TODO dir? -> obj?
                    continue
                val = getattr(dir, k)
            except AttributeError:
                val = "###MISSING ATTRIBUTE###"
            tdict[k] = val
        return tdict


    ###########################################################################
    # Data formatters
    #
    def formatPickle(self, path:str) -> str:
        import pickle
        with open(path, "rb") as ifh:
            stuff = pickle.load(ifh)
        return self.formatRec(stuff)

    def getFROptionDefaults(self) -> Dict:
        """Initial/default values for all the formatRec() options.
        """
        options = {
            "depthMessage": "deeper",   # Show in place of deeper objects
            "indentSize":   4,          # Spaces per indent level
            "keyWidth":     14,         # Columns to leave for dict keys
            "maxDepth":     3,          # Limit recursion levels
            "maxItems":     0,          # Limit items to show from lists
            "maxString":    0,          # Limit string length to show
            "noDups":       0,          # Don't print same aggregate twice.
            "propWidth":    16,         # Columns to leave for object prop names
            "quoteKeys":    False,      # Put quotation marks around dict keys?
            "showSize":     True,       # Display len() of aggregates
            "sortKeys":     True,       # Dicts shown in key order?
            "specials":     False,      # Show callables and __xxx__ items
            "stopNames":    {},         # Names/keys *not* to expand
            "stopTypes":    {},         # Types *not* to expand
        }
        return options

    def formatRec(
        self,
        obj:Any,         # Data to format
        **kwargs         # Options
        ) -> str:
        """Format a pretty wide range of data structures for pretty-printing.
        Based on a similar PHP tool I built with ccel.org.

        Options are set on the initial call; internal recursion is via
        formatRec_R, so we don't have to reprocess them all the way down.

        @return: A printable string.

        NOTE: This is protected against circular structures only by 'maxDepth' and
        the (still experimental) 'noDups' option if set.
        """
        options = self.getFROptionDefaults()
        for k, v in kwargs.items():
            if (k not in options):
                raise KeyError("Bad formatRec() option '%s'. Known options: %s." %
                    (k, ", ".join(sorted(options.keys()))))
            if (not isinstance(v, type(options[k]))):
                raise ValueError("Expected type %s, not %s, for formatRec option '%s'." %
                    (type(options[k]), type(v), k))
            options[k] = v

        # Keep a list of non-scalars so we don't re-print same one.
        self.aggregatesSeen = {}

        return self.formatRec_R(obj, options=options, depth=0)

    scalarTypes = [ int, str, bool, float, complex, str, bytearray ]
    
    def formatRec_R(self, obj:Any, options:Dict, depth:int) -> str:
        """The real (recursive) formatter.
        """
        #print("In formatRec_R, depth %d, maxDepth %d." % (depth, options['maxDepth']))
        isScalar = type(obj) in self.scalarTypes
        if (depth > options['maxDepth']):
            if (isScalar): return self.formatScalar(obj, options['maxString'])
            return "(%s %s)" % (options['depthMessage'], type(obj).__name__)

        ind = ' ' * (options['indentSize'] * depth)
        buf = ""
        #buf += (ind + "*** Dumping a '%s'." % (type(obj)))

        try:
            typeName = type(obj).__name__
        except AttributeError:
            typeName = "???"
            
        # Avoid re-printing same non-scalar object (also prevents circular traverse).
        if (not isScalar):
            if (id(obj) in self.aggregatesSeen):
                # TODO: Also print obj pointers on aggregates...
                buf += ind + "(repeated %s, at 0x%x)" % (typeName, id(obj))
                return buf
            else:
                self.aggregatesSeen[id(obj)] = True
                
        if (obj is None):                                           # NONE
            buf += ind + self.disp_None

        #elif (typeName in [ Node, Document ]):
        #    buf += "%s%s%s" % (chr(0x227A), type(obj), chr(0x227B))

        elif (callable(obj)):                                       # CALLABLE
            #buf += (ind + "callable '%s'\n" % (nm))
            nm = getattr(obj, '__name__', "[UNNAMED]")
            buf += ind + "Callable '%s()'" % (nm)

        # If a scalar is in some aggregates, the aggregate adds ind and \n.
        elif (isinstance(obj, (bool, int, float, complex, str))):   # SCALARS
            buf += self.formatScalar(obj, options['maxString'])

        elif (isinstance(obj, dict)):                               # DICT
            # namedtuple, defaultdict?
            buf += ind
            if (options['showSize']): buf += "dict |%d|:" % (len(obj))
            if (len(obj)):
                buf += ind + " %s\n" % (self.openDict)
                dfmt = ind + "  %-" + str(options['keyWidth']) + "s: %s,\n"
                inum = 0

                if (options['sortKeys']):
                    try:
                        keyList = sorted(obj.keys())
                    except TypeError:
                        keyList = obj.keys()
                else: keyList = obj.keys()
                for n in keyList:
                    v = obj[n]
                    inum += 1
                    if (self.skipIt(v, n, options)): continue
                    if (options['maxItems'] > 0 and inum > options['maxItems']):
                        buf += "*** maxItems reached ***"
                        break
                    buf += dfmt % (
                        self.quote(n, options['quoteKeys']),
                        self.formatRec_R(v, options=options, depth=depth+1))
                buf += ind + self.closeDict

        elif (isinstance(obj, (tuple, set, frozenset))):            # TUPLE, SET
            buf += ind
            if (options['showSize']): buf += "%s |%d|" % (typeName, len(obj))
            if (len(obj)):
                buf += ": %s\n" % (self.openList)
                for n, v in enumerate(obj):
                    if (options['maxItems'] > 0 and n > options['maxItems']): break
                    buf += ("%s%s,\n" %
                    (ind, self.formatRec_R(v, options=options, depth=depth+1)))
                buf += ind + self.closeList

        elif (isinstance(obj, list)):                               # LIST
            buf += ind
            if (options['showSize']): buf += "%s |%d|" % (typeName, len(obj))
            if (len(obj)):
                buf += ": %s\n" % (self.openList)
                for n, v in enumerate(obj):
                    if (options['maxItems'] > 0 and n > options['maxItems']): break
                    buf += "%s #%d: %s,\n" % (
                        ind, n, self.formatRec_R(v, options=options, depth=depth+1))
                buf += ind + self.closeList

        elif (typeName == "Tensor"):                      # torch Tensor
            # Ignore most props
            if (obj.is_cuda): cFlag = " (cuda)"
            else: cFlag = ""
            buf += "%4d-D %s of |%d| %s%s" % (
                obj.dim(), typeName, len(obj), obj.dtype, cFlag)

        elif (typeName == 'ndarray'):                     # numpy array
            buf += "ndarray |%s|" % (", ".join(str(x) for x in obj.shape))

        elif isinstance(obj, NamedNodeMap):                         # NamedNodeMap
            # This is weird, dir() won't touch it. Just map it to a dict
            # and print it that way. Geez. TODO: Support sortKeys.
            eqDict = {}
            for k, v in obj.items():
                eqDict[k] = v
            return self.formatRec_R(eqDict, options=options, depth=depth)

        #elif (isinstance(obj, type)):                               # TYPE
        #    buf += "(type)"

        elif (isinstance(obj, object)):                             # OBJECT
            if (type(obj) in options['stopTypes'] or
                typeName in options['stopTypes']):
                buf += ind + "(object of type %s)" % (typeName)
            else:
                try:
                    stuff = dir(obj)
                    #buf += ind
                    if (isinstance(obj, Iterable)): iFlag = " (Iterable)"
                    else: iFlag = ""
                    if (options['showSize']):
                        buf += "obj %s |%d|%s" % (typeName, len(stuff), iFlag)
                    buf += ": %s\n" % (self.openObject)
                    #skipped = 0
                    if (options['sortKeys']): stuff = sorted(stuff)
                    for nm in (stuff):
                        try:
                            thing = getattr(obj, nm, "[NONE]")
                        except (ValueError, IndexError) as e:
                            buf += "*** Could not get attr '%s': %s" % (nm, e)
                            continue
                        if (self.skipIt(thing, nm, options)): continue
                        #buf += (ind + "  .%s (%s): " % (nm, type(thing)))
                        ofmt = ind + "  .%-" + str(options['propWidth']) + "s = %s,\n"
                        buf += ofmt % (
                            nm, self.formatRec_R(thing, options=options, depth=depth+1))
                    buf += ind + self.closeObject
                except AttributeError:
                    # xml.dom.minidom.NamedNodeMap lands here, dir can't deal....
                    buf += "(dir() failed for %s)" % (type(obj))

        else:                                                       # UNKNOWN
            buf += ("something else")
            buf += self.formatScalar(obj, options['maxString'])
        return buf
        # end formatRec_R

    def skipIt(self, thing:Any, nm:str, options:Dict) -> bool:
        """Called for members of objects (and dicts?). Return True if we
        should skip this member due to name, being callable, etc.
        If the 'specials' option is set, we keep callable and __s; but
        that can be overridden for names listed specifically in `stopName`.
        TODO: Upgrade to allow skipping entirely, or just showing name, type, size, (keyField?).
        """
        if (nm in options['stopNames']): return True
        if (options['specials']): return False
        if (callable(thing)): return True
        if (isinstance(nm, str) and nm.startswith('__')): return True
        return False

    def quote(self, s:str, addQuotes:bool=False) -> str:
        if (not addQuotes): return s
        return '"' + re.sub(r'"', '\\"', s) + '"'

    def formatScalar(self, obj:Any, maxString:int=0) -> str:
        """Return a formatted version of a scalar variable (or at least not a aggregate).
        If passed an aggregate, format its length instead.
        """
        ty = type(obj)
        if (obj is None):
            return self.disp_None
        elif (isinstance(obj, (str, PYunicode))):
            if (maxString > 0 and len(obj) > maxString):
                return '"%s"' % (obj[0:maxString])
            return '"%s"' % (obj)
        elif (isinstance(obj, bytearray)):
            return 'b"%s"' % (obj)
        #elif (isinstance(obj, buffer)):
        #    return '"%s"' % (obj)
        #elif (isinstance(obj, storage)):
        #    return "%s" % (obj)

        elif (isinstance(obj, bool)):
            return "True" if (obj) else "False"
        elif (isinstance(obj, int)):
            return "%12d" % (obj)
        elif (isinstance(obj, float)):
            return "%12s" % (obj)
        elif (isinstance(obj, complex)):
            return "%s" % (obj)

        elif (isinstance(obj, type)):
            return "%12s" % (ty.__name__)

        elif (isinstance(obj, dict)):
            return "{|%d|}" % (len(obj))
        elif (isinstance(obj, list)):
            return "[|%d|]" % (len(obj))
        elif (isinstance(obj, tuple)):
            return "(|%d|)" % (len(obj))
        elif (isinstance(obj, set)):
            return "\u2282|%d|\u2283" % (len(obj))
            #return "[set |%d|]" % (len(obj))
        elif (isinstance(obj, frozenset)):
            #return "\u2acf|%d|\u2ad0" % (len(obj))
            return "\u2282frset |%d|\u2283" % (len(obj))

        elif (isinstance(obj, object)):
            return "[%s |%d|]" % (ty, len(obj))
        return "[???] %s" % (obj)
        # end formatScalar


    ###########################################################################
    # Get install state
    #
    def gatherLibraryReport(
        self, 
        dunder:bool=False, 
        sunder:bool=False, 
        builts:bool=False, 
        dotted:bool=False
        ) -> str:
        """Create a printable report of all the imported libraries.
        """
        buf = ""
        libDict = self.gatherLibraryVersions(
            dunder=dunder, sunder=sunder, builts=builts, dotted=dotted)
        for m, pair in libDict.items():
            buf += "%-30s %20s %s" % (m, pair[0], pair[1])
        return buf

    def gatherLibraryVersions(
        self, 
        dunder:bool=False, 
        sunder:bool=False, 
        builts:bool=False, 
        dotted:bool=False
        ) -> Dict:
        """Collect all imported modules, with their version and path (if
        available), and display them.
        From: getLibraryVersions.py (it also has a builtin list)
        """
        theDict = {}
        mlist = sorted(list(sys.modules.keys()))
        for m in mlist:
            if (not dunder and m.startswith("__")): continue
            if (not sunder and m.startswith("_") and m[1]!="_"): continue
            if (not builts and "__builtins__" in dir(m)): continue
            if (not dotted and "." in m): continue
            ver = filename = "???"
            try:
                ver = sys.modules[m].__version__
            except AttributeError:
                pass
            try:
                filename = sys.modules[m].__file__
            except AttributeError:
                pass
            theDict[m] = (ver, filename)
        return theDict
                
    
###############################################################################
# Main (doc, example and smoke-test)
# Run some simple tests if invoked as its own command.
#
if __name__ == "__main__":
    print("Running smoke tests on alogging.py")

    if (len(sys.argv) > 1):
        print(descr)
        sys.exit()

    lg = ALogger(1)

    lg.info("sjd alogging.ALogger library.", stat='infoStat')
    lg.warning("A warning message")
    lg.error("An error message")

    lg.info("====A header message")
    lg.vMsg(0, "A vMsg message.")
    lg.MsgPush()
    lg.vMsg(0, "A vMsg message, indented.")
    lg.MsgPop()
    lg.vMsg(0, "A vMsg message, back to no indent.")
    lg.error("An eMsg message")

    foo = {
        "key1": 3,
        "key2": -2.0E-12,
        "key3": 3.14+1j,
        "key4": True,
        "key5": [ 0, 1, 2, { "z":26, "y":25, "x":24 } ],
        "key6": ( "a", "b", "c" ),
        "key7": set([ 99, 98, 97 ]),
        "key8": None,
        "hello": "world\u203d",
        "aType": int,
        "aFunc": lg.formatRec,
        "aClass": ALogger,
    }
    print(lg.formatRec(foo))
    lg.bumpStat('infoStat', 100)
    lg.showStats()

