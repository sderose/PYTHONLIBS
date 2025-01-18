#!/usr/bin/env python3
#
# TextTree.py
# 2020-09-24: Written by Steven J. DeRose.
#
import sys
import os
import codecs
from collections import defaultdict

__metadata__ = {
    "title"        : "TextTree",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2020-09-24",
    "modified"     : "2023-01-20",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

[in progress]

TextTree provides the basic operations needed to create a tree over a bunch
of text, as done in many NLP systems. It can load formats like:

* s-expressions, including Penn TreeBank files
* Raw text, making sentence and paragraph breaks.
* Simple XML or JSON.
* Icky BIOEXMNWERIOTGKlgjqlk files.

This is a bit like DOM, but very, very minimal:

* All the text lives in an array of lines.
* There is only one Node type, which is a subclass of `list`, containing the
node's children.
* Each node has a dict named `props`, on which you can store any properties
you want, named with Python identifiers.
* A node can have children or not (leaves are empty lists).
* All nodes have references to where the text they contain (if any) is.
Thus, if you keep walking down the left branch from a tree, the _textBeg will
not change (even for empty nodes, which simply have _textBeg==_textEnd).
Likewise, if you walk down the right bracnh, the _textEnd will not change.

* These properties are reserved:
** _nodeID is a numeric identifier for the node. These are generated on load,
so change if the input changes. For persistent IDs, you can opt to save these
on export, or create another property of your own.
** _type is a name for the node's particular type.
** _textBeg is the line number and offset to the first text "in" the node
** _textEnd is the line number and offset to the first text past the node
** _cnum is the position of the node among its siblings
** _depth is the number of up (parent) steps to reach the root.
** _parent, _lSib, and _rSib point to the neighbors.

Only leaves may have text; but even they do not have to have any. You can have
a perfectly fine TTree with no text at all, only Node and their properties.

You can walk down the tree just as nested lists:
    someNode = myTree[12][0][0][3]

Once at a node, you can get its type as either of:
    someNode._type

The text is available as "allText", and includes all text covered by the
node, including all its descendant nodes. It can be accessed like:

    allText[lineNum]
    allText[lineNum][begOffset:endOffset]
    allText.range(begLine, begOffset, endLine, endOffset)
    allText.tostring(begLine, begOffset, endLine, endOffset) is the same as
        range(), but removes extra space such as before ".", "'s", etc.

You can walk around the tree like:
    newLoc = someNode.up()
    newLoc = someNode.down() -- this gets a childNode, by default the first.
    newLoc = someNode.left()
    newLoc = someNode.right()

These methods take optional arguments, including:
    n:   an integer number of steps. Negatives work back from the end.
    typ: only count steps of this type (can be a regex or a list of names, too)
    cb:  a callback that is handed each candidate node, and returns
True for nodes to be counted.

?? Add ups(), downs() etc. to return all, not just a single, match? Or do that
all the time and let them index into it. In latter case, return an orphan TTree
(no up/left/right) that's created on the fly?

There are a few other navigation methods:
    leftBranch: gets the furthest node reachable by successive [0]
    rightBranch: gets the furthest node reachable by successive [-1]
    compare(otherNode): Returns one of PRECEDES, FOLLOWS, CONTAINS, or OCCUPIES.
    text: Returns the full range of text covered by the node

Caveat: If you do myNode[1:3] or myNode.up[0:-1], you'll get back
a normal list, not a TTree. ??

The class provides assurances, such as that:
* TTrees only have TTrees as children
* the text ranges nest properly
* type names are identifiers
* navigation connections are consistent.


=Related Commands=


=Known bugs and Limitations=


=History=

* 2020-09-24: Written by Steven J. DeRose.
* 2023-01-20: Lint, drop Py2 support.


=To do=


=Rights=

Copyright 2020-09-24 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

dirCount = 0
fileCount = 0
stats = defaultdict(int)


###############################################################################
#
def warning(msg):
    sys.stderr.write(msg + "\n")

def doAllFiles(pathlist):
    global dirCount, fileCount
    for path in pathlist:
        if (os.path.isdir(path)):
            dirCount += 1
            if (not args.recursive): continue
            children = os.listdir(path)
            for ch in children:
                doAllFiles(ch)
        else:
            fileCount += 1
            doOneFile(path)


def doOneFile(path):
    """Read and deal with one individual file.
    """
    if (not path):
        if (sys.stdin.isatty() and not args.quiet): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = codecs.open(path, "rb", encoding=args.iencoding)
        except IOError as e:
            sys.stderr.write("Cannot open '%s':\n    %s" %
                (e)); stats["readError"] += 1
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        if (args.tickInterval and (recnum % args.tickInterval==0)):
            sys.stderr.write("Processing record %s." % (recnum))
        rec = rec.rstrip()
        if (rec == ''): continue  # Blank record
        print(rec)
    return(recnum)

def doOneXmlFile(path):
    """Parse and load
    """
    from xml.dom import minidom
    from domextensions import DomExtensions
    DomExtensions.patchDom(minidom)
    xdoc = minidom.parse(path)
    docEl = xdoc.documentElement
    paras = docEl.getElementsByTagName('P')
    for para in paras:
        print(para.textValue)
    return(0)


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def anyInt(x):
        return int(x, 0)

    def processOptions():
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
            "--iencoding", type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--ignoreCase", "-i", action='store_true',
            help='Disregard case distinctions.')
        parser.add_argument(
            "--oencoding", type=str, metavar='E',
            help='Use this character set for output files.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--recursive", action='store_true',
            help='Descend into subdirectories.')
        parser.add_argument(
            "--tickInterval", type=anyInt, metavar='N', default=10000,
            help='Report progress every n records.')
        parser.add_argument(
            "--unicode", action='store_const',  dest='iencoding',
            const='utf8', help='Assume utf-8 for input files.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files', type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

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

    if (len(args.files) == 0):
        warning("No files specified....")
        doOneFile(None)
    else:
        doAllFiles(args.files)

    if (not args.quiet):
        warning("Done, %d files.\n" % (fileCount))
