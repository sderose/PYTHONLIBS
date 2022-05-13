#!/usr/bin/env python3
#
# DOMTableTools.py: Do fancy table stuff with *ML tables.
# 2022-01-30: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
#import os
import codecs
#import string
#import math
#import subprocess
#from collections import defaultdict, namedtuple
from enum import Enum
#from typing import List, Union  #, IO, Dict
import logging
lg = logging.getLogger()

from xml.dom.minidom import Node  # , Element, Document
from xml.dom import minidom

from fsplit import fsplit
from DomExtensions import DomExtensions, XMLStrings
DomExtensions.patchDom()

sys.stderr.write("Node.selectAncestor is %s." % (Node.selectAncestor))

__metadata__ = {
    "title"        : "DOMTableTools",
    "description"  : "Do fancy table stuff with *ML tables.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2022-01-30",
    "modified"     : "2022-01-30",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

This add-on for DOM provides many tools to make it easier to deal with
"tables" in HTML or XML.
It provides many basic operations for navigating and modifying tables,
including:
* creating them from CSV
* normalizing into what some call "data" tables, which are much more
regular (so easier to code for) than HTML tables in general.
* Do "bulk" operations on tables, such as:
** reordering columns
** sorting rows
** shifting data between attributes and content

These are the main things it does as a command. It can also be used as
a library that extends DOM with many table-specific operations and tests:
* all the above manipulations
* transposition
* basic relational algebra
* joins that produce either the usual flat result, or placing the joined table's
columns into a nested table.
* addressing rows or cells by sequence number (handling colspans
and rowspans if they haven't been normalized away)
* ignoring or removing whitespace nodes between rows and cells

One goal of the "normalized table" definition, is for data to be round-trippable
without loss.

This can also convert to and from several other formats, such as CSV, JSON, Python
init code, Python data structures. This is all pretty easy once you've
normalized.


* It distinguishes and supports a subset of tables I call "normalized".
These are in one sense "true" tables: 2-d collections of items, where the
rows and columns mean something consistent. Contrast these with "layout"
tables, commonly used on the Web to force various parts to display in different
areas or arrangements. Some differences are:
    ** It makes sense to sort (at least) columns
    ** Rowspans and colspans don't make sense
    ** all rows should have the same number and sequence of columns
    (except perhaps a header row, which is special)
    ** each column typically has a meaningful name and often a datatype.
    ** nested tables don't make sense (except perhaps in a case described below).

Normalized tables can be used in many ways that non-normalized tables can't
(or at least, can't without extra work, added conventions, etc).

Normalized tables are specifically designed to be a compromise between RDB
tables and HTML tables, for the "kind" of data they have in common. Thus, it requires:
    * no colspans or rowspans
    * exactly one header row, which defines a name for each column, unique within that table
    * all rows have to have the same number of columns, and if their cells
specify their own names (which can be awfully useful for readability and
regex-matching), they must match the corresponding header hame
    * nested tables are prohibited, *except* for one special case that maps
directly to a common RDB and statistics scenario for which it can be kept
clean (more on that below).

Normalized tables are thus very close analogs to database "relations". A couple
key remaining differences are:
    * They have to "be" in some row and column order -- actually, underneath
an RDB may be, too -- it's just that the order isn't considered meaningful.
    * RDBs have additional constraints, such as every row of a table being
unique, which tables in documents may not always need to satisfy.
    * RDBs have a notion of "keys", similar to
XML IDs, but considerably more powerful. Normalized tables allow one column
to declare itself the primary key, which can be useful for Javascript code
or for fine-grained hypertext linking in general.
    * Cells in normalized tables still allow internal markup, such as to
break a string cell into paragraphs, add emphasis, footnotes, etc.

Databases of course have many parts besides the data itself. However,
the normalized tables
defined and implemented here, should be able to
round-trip between (say) SQL and HTML without loss.

* The Normalized Table knows about semantic types of fields, such as bool,
int, float, string, date, and time; and a few special cases such as enums URLs -- this is mainly so it can do display better (such as integer vs. string justification);
treat URLs as links; offer appropriate editing such as checkboxes for booleans, menus for enums, or perhaps calendars for dates. But it doesn't know about
integer or string sizes, unisgned vs. signed, etc. Wouldn't be that hard to
upgrade my implementation for that, I just don't think it's that useful ''in
this context''.
* On the flip side, Normalized tables know about XML special-character handling,
and are reliably Unicode (at least for XML and XHTML).
while string fields in

* There are methods implemented here for checking some constraints such as
uniqueness, datatype, etc., but there's nothing in HTML itself for that, so
if you edit the HTML of a normalized table it might no longer be fully
normalized.

==Nested tables==

HTML tables allow arbitrary nesting, which RDBs simply do not. This has led
to some astonishingly bizarre results in the wild. Along with rowspans,
colspans, and the difficulty of being sure what's a heading row and
what's now, this makes tables far harder to deal with.

However, one case of table nesting seems to me less problematic, because
it corresponds to a well-define conceptual case that is common in DBs,
in statistical datasets, and in documents.

Consider census data. Data for a given person may include information on
their children. If there's only one, this is easy (I'm leaving out child
surnames to save space):

    ID SURNAME GIVEN DOB        Ch_GIVEN CH_DOB
    87 Smith   Joan  1990-01-01 Bill     2015-07-30

But when there's more than one, it gets messy, as many know. You see things like

    ID SURNAME GIVEN DOB        Ch_GIVEN1 CH_DOB1    Ch_GIVEN2 CH_DOB2    ...
    87 Smith   Joan  1990-01-01 Bill      2015-07-30 Cindy     2016-10-10

There are well-known problems with this, and a more effective DB solution
is to segregate all the "child information" into a second table, connected to
the first by an ID:

    ID   PARENT_ID GIVEN    DOB
    1020 87        Bill     2015-07-30
    1021 87        Cindy    2016-10-10

Several regularities obtain here:
    * The "parent" record connects to entire "child" records, not just to
parts of them.
    * There are no circularities.
    * Commonly, a specific "child" record can be "assigned" to only one
"parent" record.

Actually, in many cases it would make sense to connect a child to two
other records (in this case, both parents). That is often done by having
three tables: one of "parent" records, one of "child" (in the case of literal
children these could be merged into a single
"person" table), and a third table that has the connections, and perhaps
some data about the particular connection:
    PARENT_ID  CHILD_ID  FAVORITE
    87         1020      1
    87         1021      0

My "normalized" tables permit cases like this to pull in the "child" records,
by selecting the ones connected to the "parent" record and making them a
nested table in a colu n devoted to that action. DB practitioners will see
how this corresponds closely to a left join, and can be "unjoined" to get
back, or "rotated" (as some call it) to get either of the forms commonly used
in statistical datasets.

Of course, if a specific "child" record is attached to multiple "parent" records,
there will be duplicates across the nested tables. These can reliably be
dropped when "un-joining" back out, if needed.

Nested normalized tables are designed to permit this kind of "rotation", by
imposing these requirements:
    * If one cell in a column is a nested table, all must be (or be empty).
    * Nothing other than the nested table (and whitespace) may occur
in those cells.
    * All nested tables in the same column, must have the same sequence of
    column names, same schema name, and (if present) datatypes.
    * The datatype of the column with nested tables is "_JOIN".


==Usage==

    DOMTableTools.py [options] [files]

XML:sexp::SQL:CSV

Key normalizations vs. general HTML tables:
    * No colspans or rowspans
    * Columns are all named
    * Headings are always and only the first row, and all/only 'th's
    * Col heads are unique to one column, and always on all children.
    * Nested table only allowed with join-like restrictions
    * Optionally, can pre-calculate and save column widths.

=Issues=

    Mixture of goals:
        * Separate out data-ish HTML tables
        * Standardize a SQL transfer format
        * Round-trippability with HTML
        * Make it easy to put SQL into HTML (say, for nice display)
        * Support a little DB editing
        * Nesting to make things like stat rotations easy.

    Each table should have a schema name (for nested, must match across all
    in given col; for non-nested, must be unique in doc).

    keys? one col can claim primary key

    what to do with empty cells?

    should it support compound foreign key checking?

    mech to calculate cell on the fly, like spreadsheet?

    editable? fill in, menu, type?

    add equiv of groupby that makes spanning heads?


=Related Commands=


=Known bugs and Limitations=


=To do=

Find a way to get pylint to see DomExtensions when subclassing Node to NormTable.
See [https://stackoverflow.com/questions/60560093/monkey-patching-class-with-inherited-classes-in-python].

=History=

* 2022-01-30: Written by Steven J. DeRose.


=Rights=

Copyright 2022-01-30 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl:int, msg:str) -> None:
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def info0(msg:str) -> None: log(0, msg)
def info1(msg:str) -> None: log(1, msg)
def info2(msg:str) -> None: log(2, msg)
def error(msg:str) -> None: log(0, msg)
def fatal(msg:str) -> None: log(0, msg); sys.exit()

class UnimplementedError(Exception):
    pass
    
    
###############################################################################
#
ELEM = Node.ELEMENT_NODE
ATTR = Node.ATTRIBUTE_NODE


###############################################################################
#
class CellDataTypes(Enum):
    NONE        = 0

    BOOL        = 1
    INT         = 2
    FLOAT       = 3
    CURRENCY    = 4

    YEAR        = 10
    DATE        = 11
    TIME        = 12
    DATIME      = 13
    TIMESTAMP   = 14

    CHAR        = 20
    NMTOKEN     = 21  # (= SQL Enum?)
    NMTOKENS    = 22  # (= SQL SET)
    URL         = 23
    GUID        = 24
    STR         = 25

    FKEY        = 30
    RASTER      = 31
    VECTOR      = 32
    VIDEO       = 33
    APPDATA     = 34

    @staticmethod
    def isKnown(s:str) -> bool:
        su = s.upper()
        try:
            _foo = CellDataTypes.__getitem__(su)
            return True
        except KeyError:
            return False


###############################################################################
#
class NormComponents:
    """Define how each meaningful component is mapped to XML/HTML. As in,
    is it represented as an element, an attribute OF an element, or a value
    within element content or attribute value?
    """
    def __init__(self):
        #               (element attr val)
        self.TABLE    = "table"
        self.THEAD    = "thead"
        self.TBODY    = "tbody"
        self.TFOOT    = "tfoot"
        self.TR       = "tr"
        self.TD       = "td"
        self.TH       = "th"

        self.CLASS    = "class"
        self.COLSPAN  = "colspan"
        self.ROWSPAN  = "rowspan"

        # TODO: Change following; caller changes the values above.
        self.COLNAME    = ("td", "class", "")
        self.COLNAMEDEF = ("th", "class", "")
        self.ISKEY      = ("th", "iskey", "")
        self.SORTFLAG   = ("th", "class", "SORTABLE")

    def csv2norm(self, path:str, hasHeader:bool=True):
        """Load a CSV file and create a normTable out of it.
        First record better be field names; each name may also
        have a colon and a datatype name appended.
        """
        fsplitArgs = { "quote":'"', "delim":"," }
        doc = minidom.Document()
        tbl = doc.createElement("table")
        doc.appendChild(tbl)    
        headRow = doc.createElement(nc.TR)
        tbl.appendChild(headRow)

        ifh = codecs.open(path, "rb", encoding="utf-8")

        # Process the header
        colNames = []
        colTypes = []
        if (hasHeader):
            headRec = ifh.readline()
            colNames = []
            headFds = fsplit(headRec, fsplitArgs)
            for headFd in headFds:
                if (":" in headFd):
                    nm, typ = headFd.split(sep=":")
                else:
                    nm = headFd
                    typ = None
                colNames.append(nm)
                colTypes.append(typ)
                colElem = doc.createElement(nc.TH)
                colElem.setAttribute(nc.CLASS, nm)
                if (typ): colElem.setAttribute("typeName", typ)
                headRow.appendChild(colElem)

        # Process the data
        recnum = 1
        for rec in ifh.readlines():
            recnum += 1
            fds = fsplit(rec, fsplitArgs)
            dataRow = doc.createElement(nc.TR)
            tbl.appendChild(dataRow)
            for i, fd in enumerate(fds):
                colElem = doc.createElement(nc.TD)
                colElem.setAttribute(nc.CLASS, colNames[i])
                colElem.innerHtml = XMLStrings.escapeText(fd)

nc = NormComponents()


###############################################################################
#
class Condition:
    """A condition such as used by select, join, where-clauses in general.
    """
    def __init__(self, expr:str):
        """Create an interpretable AST from some syntax.
        """
        raise UnimplementedError


###############################################################################
#
class NormTable(Node):
    """This doesn't see the monkey-patched methods from DomExtensions....
    """
    def __init__(self, *args1, **kwargs):
        self.nestedOk = False
        super(NormTable, self).__init__(*args1, **kwargs)
        
    @staticmethod
    def warn(msg):
        if (args.quiet): return
        lg.warning(msg)

    def checkNorm(self, nestedOk:bool=False):
        self.nestedOk = nestedOk
        errCount = 0

        trHead = self.getElementsByTagName(nc.TR)
        if (not trHead):
            errCount += 1
            self.warn("    no rows found.")
            return errCount

        colNames = []
        colTypes = []
        for headCell in trHead.childNodes:
            if (headCell.nodeType != Node.ELEMENT_NODE): continue
            if (headCell.nodeName != nc.TH):
                errCount += 1
                self.warn("    Non-head cell '%s' found in heading row" %
                    (headCell.nodeName))
            if (not headCell.hasAttribute(nc.CLASS)):
                errCount += 1
                self.warn("    Head cell lacks @class.")
                colNames.append(None)
            else:
                colNames.append(headCell.getAttribute(nc.CLASS))
            if (not headCell.hasAttribute("typeName")):
                errCount += 1
                self.warn("    Head cell lacks @typeName.")
                colTypes.append(None)
            elif (headCell.getAttribute("typeName") not in CellDataTypes):
                errCount += 1
                self.warn("    Head cell @typeName '%s' not known." %
                    (headCell.getAttribute("typeName")))
                colTypes.append(None)
            else:
                colTypes.append(headCell.getAttribute("typeName"))

        for e in self.eachElement():
            if (e.hasAttribute("rowspan")):
                errCount += 1
                self.warn("    rowspan attribute found")
            if (e.hasAttribute("colspan")):
                errCount += 1
                self.warn("    colspan attribute found")
            if (not e.hasAttribute(nc.CLASS)):
                errCount += 1
                self.warn("    class attribute missing")
            if (e.nodeType == nc.TH and
                e.selectAncestor(nc.TR) != trHead):
                errCount += 1
                self.warn("    th found outside first (heading row)")

        # Check for nesting
        errCount +=  self.checkNesting()

        return errCount

    def getRow(self:Node, n:int) -> Node:
        """Get the n-th row.
        Cannot do negatives.
        """
        nFound = 0
        for ch in self.childNodes:
            if (ch.nodeName == nc.TR):
                nFound += 1
                if (nFound >= n): return ch2
            elif (ch.nodeName in [ nc.THEAD, nc.TBODY, nc.TFOOT ]):
                for ch2 in ch.childNodes:
                    if (ch2.nodeName == nc.TR):
                        nFound += 1
                        if (nFound >= n): return ch2
        return None
    
    def countRows(self:Node) -> int:
        """Find out how many rows there are.
        """
        nFound = 0
        for _tr in self.getRows(): nFound += 1
        return nFound
        
    def getRows(self:Node) -> Node:
        """Generate all row elements of this (but not of nested) table.
        They may be at top level, or inside thead/tbody/tfoot, but no deeper.
        Or, you can pass it a tbody etc. to just get the locals (though if 
        there were to be a directly nested thead/tbody/tfoot in that tbody,
        its rows would also get counted.... Let's assume that doesn't happen.
        """
        for ch in self.childNodes:
            if (ch.nodeName == nc.TR):
                yield ch
            elif (ch.nodeName in [ nc.THEAD, nc.TBODY, nc.TFOOT ]):
                for ch2 in ch.childNodes:
                    if (ch2.nodeName == nc.TR): yield ch
        return
                
    def getHeadRow(self:Node) -> Node:
        """Given any node in a table, return the header tr.
        """
        tbl = self.selectAncestorOrSelf("table")
        return tbl.getElementsByTagName(nc.TR)[0]

    def getColumns(self:Node) -> Node:
        """Generate the columns in a given row.
        """
        assert self.nodeName == nc.TR
        for cell in self.childNodes:
            if (cell.nodeName in [ nc.TD, nc.TH ]): yield cell
        return
                
    # TODO: col num<>name > dtype <cell
    def getColumnHeaderForCell(self:Node) -> Node:
        assert self.nodeName == nc.TD
        cnum = self.getColumnNum()
        return self.getColumnHeaderByNumber(cnum)

    def getColumnHeaderByNumber(self:Node, n) -> Node:
        """Needs some node of the table so it can find the head row...
        Can find by name or number.
        """
        # TODO Add methods to get from
        if (isinstance(n, int)):
            i = 0
            for th in self.getHeadRow().childNodes:
                if (th.nodeType != Node.ELEMENT_NODE): continue
                i += 1
                if (i==n): return th
            return None
        elif (isinstance(n, str)):
            for th in self.getHeadRow().childNodes:
                if (th.nodeType != Node.ELEMENT_NODE): continue
                if (th.getAttribute(nc.CLASS) == n): return th
            return None
        else:
            raise TypeError("getColumnHeaderByNumber: must be string or int.")

    def getColumnNum(self:Node) -> int:
        # TODO: rowspans
        n = 1
        cur = self
        while (cur):
            cur = cur.previousSibling
            if (cur.nodeType != Node.ELEMENT_NODE): continue
            if (cur.hasAttribute("colspan")):
                cspan = cur.getAttribute("colspan").strip()
                try:
                    n += int(cspan)
                except ValueError:
                    n += 1
        return n

    def countColumns(self:Node) -> int:
        """Return the number of column in a given row. 
        This accounts for colspans.
        """
        assert self.nodeName == nc.TR
        nColumns = 0
        for cell in self.childNodes:
            if (cell.nodeName not in [ nc.TD, nc.TH ]): continue
            try:
                cspan = cell.getAttribute(nc.COLSPAN)
                cspan = int(cspan.strip()) if cspan else 1
                nColumns += cspan
            except TypeError:
                pass
        return nColumns
        
    def getColumnNames(self:Node) -> list:
        colNames = []
        for th in self.getHeadRow().childNodes:
            colNames.append(th.getAttribute(nc.CLASS))
        return colNames

    def getColumnTypes(self:Node) -> list:
        colTypes = []
        for th in self.getHeadRow().childNodes:
            colTypes.append(th.getAttribute("typeName"))
        return colTypes

    def getSchemaName(self:Node) -> str:
        raise UnimplementedError

    def checkNesting(self:Node) -> int:
        """Check whether nested tables, if any, obey NormTable restrictions.
        @return Number of errors found.
        """
        errCount = 0
        nestedTables = self.getElementsByTagName("table")
        if (not nestedTables): return 0
        if (not self.nestedOk):
            errCount += 1
            self.warn("    %d nested tables found." % (len(nestedTables)))
        else:
            for nt in nestedTables:
                # TODO: Allow WSN
                if (nt.previousSibling or nt.nextSibling):
                    errCount += 1
                    self.warn("    nested table is not alone.")
        return errCount

    def checkKeys(self:Node):
        raise UnimplementedError


    ###########################################################################
    # Manipulate existing tables toward norm
    #
    def unspan(self:Node, attrName:str=nc.CLASS, attrValue:str="td-nil") -> None:
        """Expand colspans and rowspans by adding empty cells as needed.
        If 'attrName' is not empty, 'attrValue' is added as a class token
        to that attribute on all the new empty cells.
        """
        for tr in self.getRows():
            for cell in tr.childNodes:
                if (cell.nodeName not in [ nc.TD, nc.TH ]): continue
                try:
                    cspan = cell.getAttribute(nc.COLSPAN)
                    cspan = int(cspan.strip()) if cspan else 1
                    while cspan > 1:
                        cell.insertDummyCell(attrName, attrValue)
                        cspan -= 1
                except TypeError:
                    pass
        return

    def insertDummyCell(self:Node, attrName:str=nc.CLASS, attrValue:str="td-nil") -> Node:
        """Create a dummy cell (generally to take the place of a moribund span),
        and insert it after the given cell.
        """
        dum = self.ownerDocument.createElement(nc.TD)
        if (attrName): dum.setAttribute(attrName, attrValue)
        fsib = self.followingSibling
        if (fsib):
            self.parentNode.insertBefore(fsib, dum)
        else:
            self.parentNode.appendChild(fsib)
        return dum
        
    def nukeThead(self:Node, promote:bool=True):
        """If 'promote' is True, move any thead row into tbody.
        Otherwise, delete them.
        Then remove the thead itself.
        """
        raise UnimplementedError

    def nukeTfoot(self:Node, promote:bool=True):
        raise UnimplementedError

    def setColumnNames(self:Node, names:list, attrName:str=nc.CLASS, alone:bool=True):
        """Given a list of names, assign them by setting the given attribute
        on each instance. If 'alone' is True, the attribute is assigned
        that name only; otherwise, the name is added as a space-separated
        token if not already there, and any prior tokens remain.
        """
        raise UnimplementedError

    def unjoin(self:Node):
        raise UnimplementedError

    def attrToColumn(self:Node, attrName:str, colName:str, colNum:int):
        raise UnimplementedError

    def columnToAttr(self:Node, colName:str, attrName:str):
        raise UnimplementedError


    ###########################################################################
    # Format support
    #
    def strftime(self:Node, ifmtString:str, ofmtString:str):
        """Convert a string from one date/time format to another.
        Strictly speaking, this has no necessary connection to tables.
        TODO: doesn't need a Node or Document, so move to XMLStrings?
        """
        from datetime import datetime
        origText = self.collectText()
        tstr = datetime.strptime(origText, ifmtString)
        newText = datetime.strftime(tstr, ofmtString)
        self.innerHTML = newText

    def reorderColumns(self:Node, sortSpec:list):
        """ways to sort:
            by a list of names
            by value in col (using explicit datatype?)
            like bbedit, by regex caps from value
            by attribute(s)
            asc/desc
            empties to start or end
        """
        raise UnimplementedError

    def moveColumn(self:Node, columnToMove, target):
        """Move a column, identified by number or @class name, to a new place.
        """
        raise UnimplementedError

    def clearCellsByContent(self:Node, expr:str=None, nbIsSpace:bool=True):
        """Clear content of cells
        """
        raise UnimplementedError


    ###########################################################################
    # Edit tables (These should be available as bbedit tools)
    #
    def transposed(self:'NormTable', replace:bool=False):
        """This makes a transposed copy of everything under the passed node.
        So if only the tbody counts, pass *it*, not the table itself.
        If 'replace' is True, it is spliced in to replace the original.
        In any case, the root of the new transposed thing is returned.
        """
        self.unspan()

        # Make a destination table
        doc = self.ownerDocument
        t2 = doc.createElement(nc.TABLE)
        b2 = doc.createElement(nc.TBODY)
        t2.appendChild(b2)
        
        # Make as many new rows, as the starting table has columns
        nCols = self.getRow(0).countColumns()
        for _i in range(nCols):
            tr2 = doc.createElement(nc.TR)
            b2.appendChild(tr2)
            
        for tr in self.getRows():
            cNum = 0
            for cell in tr.childNodes:
                if (cell.nodeName not in [ nc.TD, nc.TH ]): continue
                cell2 = cell.cloneNode()()
                b2.childNodes[cNum].appendChild(cell2)
                cNum += 1
        
        if (replace):
            self.parentNode.replaceChild(t2, self)
        return t2
        
    def InsertColumn(self:'NormTable'):  # As number N, or before/after name?
        raise UnimplementedError
        
    def DeleteColumn(self:'NormTable'):  # By number or name
        raise UnimplementedError

    def DeleteRow(self:'NormTable'):     # By number
        raise UnimplementedError

    def InsertRow(self:'NormTable'):     # As number N
        raise UnimplementedError

    def CreateTable(self:Node, nRows:int, nCols:int, thead:bool=True, tfoot:bool=True, cellClasses:list=None):
        """Make an entire n*m table, optionally with thead and tfoot.
        If cellClasses is given it must be a list of length nCols, and its values
        must be strings to be put into @CLASS of the respective cell elements.
        TODO: Perhaps add a callback to provide content to insert?
        """
        if (cellClasses): assert len(cellClasses) == nCols
        
        doc = self.ownerDocument
        t2 = doc.createElement(nc.TABLE)
        if (thead):
            h2 = doc.createElement(nc.THEAD)
            t2.appendChild(h2)
            h2.appendChild(self.CreateRow(nCols, th=True, cellClasses=cellClasses))
                
        b2 = doc.createElement(nc.TBODY)
        t2.appendChild(b2)
        for _i in range(nRows):
            b2.appendChild(self.CreateRow(nCols, th=False, cellClasses=cellClasses))

        if (tfoot):
            f2 = doc.createElement(nc.TFOOT)
            t2.appendChild(f2)
            f2.appendChild(self.CreateRow(nCols, th=True, cellClasses=cellClasses))
            
        return t2
        
    def CreateRow(self:Node, nCols:int, th:bool=False, cellClasses:list=None) -> Node:
        """Create a row with nCols cells, all empty.
        TODO: Perhaps add a callback to provide content to insert?
        """
        doc = self.ownerDocument
        cellNodeName = nc.TH if th else nc.TD
        tr = doc.createElement(nc.TR)
        for i in range(nCols):
            cell = doc.createElement(cellNodeName)
            if (cellClasses): cell.setAttribute(nc.CLASS, cellClasses[i])
            tr.appendChild(cell)
        return tr
        
    def ListList2Table(self:Node, data:list) -> Node:
        """Make a new table from a list of lists of data. Better be rectangular.
        """
        nCols=len(data[0])
        t2 = self.CreateTable(nRows=len(data), nCols=nCols)
        for i, row in enumerate(t2.getRows()):
            rowData = data[i]
            assert len(rowData) == nCols
            for j, cell in row.childNodes:
                cell.innerHTML = str(rowData[j])
        return t2
        
    def DeleteTable(self:'NormTable'):  # TODO: Drop?
        raise UnimplementedError

    def SetColumn(self:'NormTable'):  # TODO: Drop? Or change to SetColumnDatatype?
        raise UnimplementedError

    def RenameTable(self:'NormTable'):  # TODO: Drop?
        raise UnimplementedError

    def RenameColumn(self:'NormTable'):  # TODO: Drop?
        raise UnimplementedError


    ###########################################################################
    # Do SQL on these
    #
    def project(self:'NormTable', columns:list):
        raise UnimplementedError
        
    def select(self:'NormTable'):
        raise UnimplementedError
        
    def union(self:'NormTable'):
        raise UnimplementedError
        
    def intersection(self:'NormTable'):
        raise UnimplementedError
        
    def diff(self:'NormTable'):
        raise UnimplementedError
        
    def symdiff(self:'NormTable'):
        raise UnimplementedError
        
    def join(self:'NormTable', other:'NormTable', selfColumns:list, otherColumns:list, where:Condition):
        raise UnimplementedError

# Make sure the right methods get monkey-patched onto our subclass?? TODO: Check
#
DomExtensions.patchDom(NormTable)


###############################################################################
# Main
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
            "--color",  # Don't default. See below.
            help="Colorize the output.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "files", type=str, nargs=1,
            help="Path to input HTML file.")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    tags = NormComponents()

    DomExtensions.patchDom(NormTable)

    for file in args.files:
        dom = minidom.parse(file)
        for tid in args.ids:
            tbl0 = dom.documentElement.getElementById(tid)
            if (not tbl0):
                lg.error("ID not found: '%s'.", tid)
                continue
            if (tbl0.nodeType != tags.TABLE[0]):
                lg.error("ID '%s' is on a %s, not a %s",
                    id, tbl0.nodeType, tags.TABLE[0])
                continue
            if (args.normalize and not tbl0.normalize()):
                lg.error("Culd not normalize table with ID '%s'.", tid)
                continue

