#!/usr/bin/env python
#
# By Steven J. DeRose, started ~2014-06.
#
#pylint: disable=W0613, W0212, W0622
#
from __future__ import print_function
import sys
import re
import argparse
#import os
#import string

from MarkupHelpFormatter import MarkupHelpFormatter

__metadata__ = {
    'title'        : "argParsePP.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2004-06",
    'modified'     : "2020-01-09",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=ArgumentParserPP=

An improved ArgumentParser and argparse:

    Hooks up MarkupHelpFormatter
    Adds a showDefaults option
    Adds a shortMetavars option
    Supports alternative hyphen conventions
    Supports adding 'toggle' attributes, without changeable 'no-' prefix

=Related Commands=

=Known bugs and limitations=

Unfinished.

=To do=

* argparsePP: way to add "choices" values as independent options !
* entailment
* set options for MarkupFormatter etc.
* method to 'add' synonym to previously-defined option
* option for output to $PAGER (incl. links when possible?)

=Ownership=

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [http://github.com/sderose].

=Options=
    """

class ArgumentParserPP(argparse.ArgumentParser):
    def __init__(self,
        prog=None,
        usage=None,
        description=None,
        epilog=None,
        parents=None,
        formatter_class=MarkupHelpFormatter,
        prefix_chars='-',
        fromfile_prefix_chars=None,
        argument_default=None,
        conflict_handler='error',
        add_help=True,

        hyphenConvention="gnu",
        negationPrefix="no-",
        showDefaults=True,
        shortMetavars=True,
        pager = None,
        gnuStyle = True
        ):
        """Improved argparse. Mostly just like the regular one, however,
        adds a notion of 'toggles', automatic metavar shortening, and
        defaulting to use of MarkupHelpFormatter.
        """
        self.hyphenConvention = hyphenConvention
        self.negationPrefix   = negationPrefix
        self.showDefaults     = showDefaults
        self.shortMetavars    = shortMetavars
        self.entailments      = {}
        self.gnuStyle         = False

        super(ArgumentParserPP, self).__init__(
            prog=prog,
            usage=usage,
            description=description,
            epilog=epilog,
            parents=parents,
            formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler,
            add_help=add_help,
            )


    def add_argument(
        self,
        name,               # How do you add multiple names?
        action=None,
        nargs=None,
        const=None,
        default=None,
        typ=None,
        choices=None,
        required=None,
        help=None,
        metavar=None,
        dest=None
        ):
        basename = name.strip(' \t-_')
        if (self.showDefaults and default!=None):
            if (help==None): help=""
            help += " Default: " + str(default)
        if (metavar==None):
            metavar = basename.upper()
            if (self.shortMetavars):  metavar = metavar[0:1]
        if (dest==None): dest = re.sub('-', '_', basename)

        if (name.startswith("--") and self.gnuStyle):
            super.add_argument(
                 name=name[1:],
                 action=action,
                 nargs=nargs,
                 const=const,
                 default=default,
                 type=typ,
                 choices=choices,
                 required=required,
                 help=help,
                 metavar=metavar,
                 dest=dest)

        return(super.add_argument(
            name=name,
            action=action,
            nargs=nargs,
            const=const,
            default=default,
            type=typ,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar,
            dest=dest)
        )

    def showSettings(self):
        return

    def add_toggle(
        self,
        name=None,
        default=None,
        help=None,
        metavar=None,
        dest=None
        ):
        """An invertible flag as a special-case. This method:
            Adds the named option with action='store_true'
            Adds the opposite option with action='store_true':
                Uses a standard 'prefix' to name it
                Makes up as cross-reference as help.
        """
        if (not name.startswith("--")):
            sys.stderr.write("add_toggle: option doesn't start with '--'.")
            return
        basename = name.strip(' \t-_')
        self.add_argument(
            name, action='store_true', dest=name[2:],
            default=default, help=help)
        return(self.add_argument(
            '--'+self.negationPrefix+basename, action='store_false',
            default=default,
            help="See '"+name+"'.",
            metavar=metavar,
            dest=dest or basename
            )
        )


    def add_enum(
        self,
        basename="",
        typ=str,
        default=None,
        help=None,
        metavar=None,
        dest=None,
        choices=None
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
        self.entailments[name1].append( (name2, value2) )

#    Rfile = argparse.FileType('r')
#    Wfile = argparse.FileType('w')
