#!/usr/bin/env python
#
# TabularFormats2.py
# More modern port of by TabularFormats classes, originally from Perl.
# 2018-07-19: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import codecs

import csv
from csv import DictWriter, DictReader  # , Dialect
from csv import QUOTE_MINIMAL, QUOTE_NONNUMERIC, QUOTE_ALL, QUOTE_NONE

__metadata__ = {
    'title'        : "TabularFormats2.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2018-07-19",
    'modified'     : "2020-08-20",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Load data from some CSV-like form, such as listed below. Use the same API
as Python C<csv> package.

    CSV,
    ARFF,
    XSV
    Fixed columns
    SQL
    Simplistic S-EXP, JSON, HTML tables, etc.
    Perl or Python declarations

=Related Commands=

=Known bugs and Limitations=

=History=

* 2018-07-19: Written. Copyright by Steven J. DeRose.


=To do=

* Cleaner way to set params....
* Finish CSV
* Make reader/writer inherit options from top object
* Add more formats


=Rights=

Copyright 2018-07-19 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].

=Options=
"""


###############################################################################
#
def processOptions():
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--commentDelim", type=str, metavar='S', default=None,
        help='Start line with this to treat as a comment.')
    parser.add_argument(
        "--delimiter", "-t", "-d", "--fieldSep",
        type=str, metavar='S', default=",",
        help='Field separator character.')
    parser.add_argument(
        "--escapeChar",       type=str, metavar='E', default=None,
        help='Use this character to escape quotes or other characters.')
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
        "--quoteChar",        type=str, metavar='C', default='"',
        help='Use this character to quote fields.')
    parser.add_argument(
        "--quoting",          type=str, metavar='C', default='nonnumeric',
        choices=['none', 'all', 'nonnumeric', 'minimal'],
        help='What kind of values actually get quoted.')
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
    if (args0.delimiter):
        args0.delimiter = args0.delimiter.decode('string_escape')
    if (args0.escapeChar):
        args0.escapeChar = args0.escapeChar.decode('string_escape')
    if (args0.quoteChar):
        args0.quoteChar = args0.quoteChar.decode('string_escape')

    return(args0)


def writecomment(self, txt):
    if (self.commandDelim):
        self.csvfile.write(self.commentDelim + txt)

###############################################################################
# More or less a "Dialect"....
#
class TFOptions:
    def __init__(self, options=None):
        self.options = {
            # csv's options, defaults:
            'delimiter'        : ",",
            'doublequote'      : True,
            'escapechar'       : None,
            'lineterminator'   : '\r\n',
            'quotechar'        : '"',
            'quoting'          : csv.QUOTE_MINIMAL,
            # QUOTE_MINIMAL, QUOTE_NONNUMERIC, QUOTE_ALL, QUOTE_NONE
            'skipinitialspace' :  False,
            'strict'           :  False,

            # Our defaults:
            'commentDelim'     : None,
            'fieldNameExpr' :  r'\w+',
            'commentDelim'  : None,
            'fieldCount'    : 0,
            'fieldNames'    : None,
            'fieldTypes'    : None,
        }

        if (options):
            for k, v in (options.items()):
                self.options[k] = v


###############################################################################
# https://docs.python.org/3/library/csv.html
#    Python's csv is not actually a class. So make it one.
#
# csv's have a "Dialect" with these features:
#
class TabularFormats:  # Make this a subclass of csv?
    """Subclass this for other formats
    """

    def __init__(self, lgParam=None, options=None):
        self.rdr = None
        self.wtr = None
        self.optionsObj = TFOptions(options)

        if (lgParam): self.lg = lgParam
        else: self.lg = ALogger(1)

        # Patch as needed so we look like csv
        #
        self.register_dialect   = csv.register_dialect
        self.unregister_dialect = csv.unregister_dialect
        self.get_dialect        = csv.get_dialect
        self.list_dialects      = csv.list_dialects
        self.field_size_limit   = csv.field_size_limit

        DictWriter.writecomment = writecomment

    def getReader(self, csvfile, **fmtparams):
        mergedParams = self.optionsObj.options
        if (fmtparams):
            for k in (fmtparams): mergedParams[k] = fmtparams[k]
        print("getReader mergedParams:\n%s" % (mergedParams))
        self.rdr = csv.reader(csvfile, mergedParams)
        return(self.rdr)

    def getWriter(self, csvfile, **fmtparams):
        self.wtr = csv.writer(csvfile, dialect, *fmtparams)
        return(self.wtr)

    def getDictReader(self, f, fieldnames=None,
        restkey=None, restval=None, *args, **kwds):
        self.rdr = DictReader(f, fieldnames,
            restkey, restval, dialect, *kwds)
        return self.rdr

    def getDictWriter(self, f, fieldnames,
        restval='', extrasaction='raise', *args, **kwds):
        self.wtr = DictWriter(f, fieldnames,
            restval, extrasaction, dialect, *kwds)
        return self.wtr

    def getSaxReader(self, tableTag='table', recTag='tr', fieldTag='td'):
        self.rdr = SaxReader(tableTag, recTag, fieldTag)
        return self.rdr

    def getSaxWriter(self):
        self.wtr = SaxWriter()
        return self.wtr


###############################################################################
#
class SaxReader:
    INIT      = 1
    START_TAG = 2
    END_TAG   = 3
    TEXT      = 4
    FINAL     = 5
    def __init__(self, tableTag='table', recTag='tr', fieldTag='td'):
        self.tableTag = tableTag
        self.recTag   = recTag
        self.fieldTag = fieldTag
        self.curFields = None
        self.reader = self.csv.reader()

    def __next__(self):
        yield(SaxReader.INIT, "")
        yield(SaxReader.START_TAG, self.tableTag)
        for rec in self.reader():
            if (self.commentDelim and
                rec[0].startswith(self.commentDelim)):
                continue
            yield(SaxReader.START_TAG, self.recTag)
            for fd in rec:
                yield(SaxReader.START_TAG, self.fieldTag)
                yield(SaxReader.TEXT, fd)
                yield(SaxReader.END_TAG, self.fieldTag)
            yield(SaxReader.END_TAG, self.recTag)
        yield(SaxReader.END_TAG, self.tableTag)
        yield(SaxReader.FINAL, "")


###############################################################################
###############################################################################
# Main
#
if (__name__ == "__main__"):
    from alogging import ALogger
    lg = ALogger(1)

    def doOneFile(path, fh, options):
        """Read and deal with one individual file.
        """
        recnum = 0
        rec = ""
        tf = TabularFormats(options)
        #print(tf.options)
        reader = tf.getReader(fh)
        #reader = csv.reader(fh, tf.options)
        for rec in reader:
            recnum += 1
            print("======= RECORD %4d:" % (recnum))
            for fd in (rec):
                print("    '%s'" % (fd))
                if (args.delimiter != "\t" and "\t" in fd ):
                    sys.stderr.write(
                        "Warning: Tab in record %d, but delim is '%s'." %
                        (recnum, args.delimiter))
        return(recnum)

    ###########################################################################
    #
    args = processOptions()
    if (len(args.delimiter) > 1):
        sys.stderr.write(
            "Delimiter '%s' too long (%d)." % (args.delimiter, len(args.delimiter)))
        sys.exit()

    optionsObj = TFOptions({
        'commentDelim' : args.commentDelim,
        'delimiter'    : args.delimiter,
        'escapechar'   : args.escapeChar,
        'quotechar'    : args.quoteChar,
        'quoting'      : args.quoting
    })
    print("Initial TFOptions: %s" % (optionsObj.options))
    if (len(args.files) == 0):
        print("No files specified, trying STDIN.")
        doOneFile("[STDIN]", sys.stdin, optionsObj.options)
    else:
        for fArg in (args.files):
            fh0 = codecs.open(fArg, "rb", encoding=args.iencoding)
            lg.bumpStat("Total Args")
            doOneFile(fArg, fh0, optionsObj.options)
            fh0.close()

    lg.vMsg(0,"Done.")
    lg.showStats()
