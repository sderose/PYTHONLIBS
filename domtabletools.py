#!/usr/bin/env python3
#
# domtabletools.py: Do fancy table stuff with *ML tables.
# 2022-01-30: Written by Steven J. DeRose.
#
#pylint: disable=E1101
#
import sys
import codecs
from enum import Enum
from typing import List, Union, Dict, Callable  #, IO
import logging
import re

from xml.dom.minidom import Node  # , Element, Document
from xml.dom import minidom

from fsplit import fsplit
from domextensions import DomExtensions, XmlStrings

DomExtensions.patchDom()

lg = logging.getLogger()

sys.stderr.write("Node.selectAncestor is %s." % (Node.selectAncestor))

__metadata__ = {
    "title"        : "domtabletools",
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
UNFINISHED

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

Can also convert to and from several other formats, such as CSV, JSON, Python
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
    (except perhaps a head row, which is special)
    ** each column typically has a meaningful name and often a datatype.
    ** nested tables don't make sense (except perhaps in a case described below).

Normalized tables can be used in many ways that non-normalized tables can't
(or at least, can't without extra work, added conventions, etc).

Normalized tables are specifically designed to be a compromise between RDB
tables and HTML tables, for the "kind" of data they have in common.
Thus, it requires:
    * no colspans or rowspans
    * exactly one head row, with a name for each column, unique within the table
    * all rows have to have the same number of columns, and if their cells
specify their own names (which can be awfully useful for readability and
regex-matching), they must match the corresponding head hame
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
int, float, string, date, and time; and a few special cases such as enums
URLs -- this is mainly so it can do display better (such as integer vs. string justification);
treat URLs as links; offer appropriate editing such as checkboxes for
booleans, menus for enums, or perhaps calendars for dates. But it doesn't know about
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

    domtabletools.py [options] [files]

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

Although we use patchDOM to attach a bunch of methods to Node and
to NormTable, pylint doesn't seem to realize it, so it still reports
issues like E1101: NormTable has no 'xxx' member.


=To do=

Find a way to get pylint to see DomExtensions when subclassing Node to NormTable.
See [https://stackoverflow.com/questions/60560093/monkey-patching-class-with-inherited-classes-in-python].

* Add way to get applicable alignment for a table cell or column
    ** @align or @style on the cell
    ** <col>?
    ** CSS (at least if explicit in an HTML header)
    ** scan column, if all numeric (except header) use right, else left; header center?
    ** Pull in table and style features from html2latex.py.

* Possibly extend support for proper matrices?
    ** Ensure datatypes
    ** Convert to/from numpy (let it do the math!)


=History=

* 2022-01-30: Written by Steven J. DeRose (draft, really).
* 2023-04-28: Move in table stuff from domextensions. Split out TableOptions class.
Make main class a wrapper that owns a table Node and a TableOptions.
Organize methods by components of a table. Decide to require clean (no nesting,
always has thead/tbody, one thead/tr, no spans, co-indexed column members.
Decided to number rows and columns from 1 (that's how everybody talks with
tables, and these really aren't array indexes since there can be
text nodes and PIs and stuff in there).


=Rights=

Copyright 2022-01-30 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
ELEM = Node.ELEMENT_NODE
ATTR = Node.ATTRIBUTE_NODE

def getChildByName(node:Node, name:str, ns:str="", case:bool=True):
    """Return the first child of the given node, which is an element of
    the given type.
        If 'case' is set to False, the nodeName is matched ignoring case.
        If 'ns' is not set, only the localName (not the namespace) is checked.
        If 'ns' is set, whether it test the prefix or URL may depend on the
        underlying DOM implementation.... though it shouldn't.
    """
    assert node.nodeType == Node.ELEMENT_NODE
    name = re.sub("^.*:", "", name)
    for ch in node.childNodes:
        if (ch.nodeType != node.ELEMENT_NODE): continue
        if (ns):
            nsPart = re.sub(r":.*", "", ch.nodeName)
            if strcmp(nsPart, ns,case) != 0: continue
        if strcmp(ch.localName, name, case) == 0: return ch
    return None

def strcmp(s1:str, s2:str, case:bool=True):
    """Compare the strings, ignoring case unless 'case' is Trueish.
    """
    if (not case):
        s1 = s1.lower()
        s2 = s2.lower()
    if s1 < s2: return -1
    if s1 > s2: return 1
    return 0


###############################################################################
#
class CellDataTypes(Enum):
    """A list of common data types in cells, mainly to help formats them.
    """
    NONE        = 0

    BOOL        = 1
    INT         = 2
    FLOAT       = 3
    CURRENCY    = 4

    YEAR        = 10
    DATE        = 11
    TIME        = 12
    DATETIME    = 13
    TIMESTAMP   = 14

    CHAR        = 20
    NMTOKEN     = 21  # (-> SQL Enum?)
    NMTOKENS    = 22  # (-> SQL SET?)
    URL         = 23
    GUID        = 24
    STR         = 25

    FKEY        = 30
    RASTER      = 31
    VECTOR      = 32
    VIDEO       = 33
    APPDATA     = 34

    XML         = 50

    BLOB        = 99

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
class TableOptions:
    """Define how each meaningful component is named and mapped to XML/HTML,
    and provide a method to turn CSV-ish stuff into it.
    TODO: Support swapping things between element/attribute?
    """
    def __init__(self):
        self.setDefaults()

    def setDefaults(self):
        # Table elements
        self.TABLE    = "table"
        self.THEAD    = "thead"
        self.TBODY    = "tbody"
        self.TFOOT    = "tfoot"
        self.TR       = "tr"
        self.TD       = "td"
        self.TH       = "th"

        # Attributes
        self.CLASS    = "class"
        self.COLSPAN  = "colspan"
        self.ROWSPAN  = "rowspan"

        self.TYPE     = "dtype"    # On header, datatype of column entries (?)

        # Constants
        self.ROW_0    = "row0"  # @CLASS token for rowspan dummy
        self.COL_0    = "col0"  # @CLASS token for rowspan dummy
        self.SORT     = "sortable"

        # Places to put special data
        # TODO: Abstract following; caller changes the values above.
        self.COLIDENTUSE = "class"  # Use of column ident
        self.COLIDENTDEF = "class"  # Definition of column ident
        #self.ISKEY       = "iskey"  # ???


###############################################################################
#
#
def CreateTableFromMatrix(self, theMatrix:List[List], hasHeader:bool=True):
    """Construct from list of lists. First row can be header if desired.
    """
    if (not self.topt): self.topt = TableOptions()

    nCols = len(theMatrix[0])
    colIds = []
    if (hasHeader):
        colIds = [ str(theMatrix[0][x]) for x in nCols ]
    else:
        colIds = [ ("col_%02d" % (i+1)) for i in range(nCols) ]

    self.tbl = NormTable(colIds)
    for i in range(1, len(theMatrix)):
        row = theMatrix[i]
        rowLen = len(row)
        if (rowLen != nCols):
            lg.warning("Row %d has %d items, expecting %d.", i, rowLen, nCols)
        self.tbl.appendRow()
        for colNum in range(rowLen):
            self.tbl.setField(i, colNum, row[colNum])
    return self.tbl


###############################################################################
# Construct from CSV
#
def CreateTableFromCSV(self, path:str, hasHeader:bool=True, fsplitArgs:Dict=None) -> Node:
    """Load a CSV file and create a NormTable out of it.
    First record better be field names; each name may also
    have a colon and a datatype name appended.
    """
    if (not fsplitArgs):
        fsplitArgs = { "quote":'"', "delim":"," }

    ifh = codecs.open(path, "rb", encoding="utf-8")


    # Process the head
    colIds = None
    if (hasHeader):
        colIds, _colTypes = self.doCSVHeader(ifh, fsplitArgs)

    # Process the data
    recNum = 1
    for rec in ifh.readlines():
        recNum += 1
        fds = fsplit(rec, fsplitArgs)
        dataRow = self.ownerDocument.createElement(self.topt.TR)
        self.tbl.appendChild(dataRow)
        for i, fd in enumerate(fds):
            colElem = self.ownerDocument.createElement(self.topt.TD)
            colElem.setAttribute(self.topt.CLASS, colIds[i])
            colElem.innerHtml = XmlStrings.escapeText(fd)
    return self.tbl

def doCSVHeader(self, ifh, fsplitArgs):
    colIds = []
    colTypes = []
    headRec = ifh.readline()
    colIds = []
    headFds = fsplit(headRec, fsplitArgs)
    for headFd in headFds:
        if (":" in headFd):
            nm, typ = headFd.split(sep=":")
        else:
            nm = headFd
            typ = None
        colIds.append(nm)
        colTypes.append(typ)
        colElem = self.ownerDocument.createElement(self.topt.TH)
        colElem.setAttribute(self.topt.CLASS, nm)
        if (typ): colElem.setAttribute("typeName", typ)
        self.appendColumn(colElem)
    return colIds, colTypes


###############################################################################
#
def checkNorm(tbl:Node, topt:TableOptions=None):
    if (not topt): topt = TableOptions()

    errCount = 0

    trHead = tbl.getElementsByTagName(topt.TR)
    if (not trHead):
        errCount += 1
        lg.warning("    no rows found.")
        return errCount

    colIds = []
    colTypes = []
    for headCell in trHead.childNodes:
        if (headCell.nodeType != Node.ELEMENT_NODE): continue
        if (headCell.nodeName != topt.TH):
            errCount += 1
            lg.warning("    Non-head cell '%s' found in heading row",
                headCell.nodeName)
        if (not headCell.hasAttribute(topt.CLASS)):
            errCount += 1
            lg.warning("    Head cell lacks @class.")
            colIds.append(None)
        else:
            colIds.append(headCell.getAttribute(topt.CLASS))
        if (not headCell.hasAttribute("typeName")):
            errCount += 1
            lg.warning("    Head cell lacks @typeName.")
            colTypes.append(None)
        elif (headCell.getAttribute("typeName") not in CellDataTypes):
            errCount += 1
            lg.warning("    Head cell @typeName '%s' not known.",
                headCell.getAttribute("typeName"))
            colTypes.append(None)
        else:
            colTypes.append(headCell.getAttribute("typeName"))

    for e in tbl.eachElement():
        if (e.hasAttribute("rowspan")):
            errCount += 1
            lg.warning("    rowspan attribute found")
        if (e.hasAttribute("colspan")):
            errCount += 1
            lg.warning("    colspan attribute found")
        if (not e.hasAttribute(topt.CLASS)):
            errCount += 1
            lg.warning("    class attribute missing")
        if (e.nodeType == topt.TH and
            e.selectAncestor(topt.TR) != trHead):
            errCount += 1
            lg.warning("    th found outside first (heading row)")

    # Check for nesting
    errCount +=  tbl.checkNesting()

    return errCount


###############################################################################
# Normalizers
#
def unspan(self, attrValue:str="td-nil") -> None:
    """Expand colspans and rowspans by adding empty cells as needed.
    If 'attrName' is not empty, 'attrValue' is added as a class token
    to that attribute on all the new empty cells.
    """
    for tr in self.getRows():
        for cell in tr.childNodes:
            if (cell.nodeName not in [ self.topt.TD, self.topt.TH ]): continue
            try:
                cspan = cell.getAttribute(self.topt.COLSPAN)
                cspan = int(cspan.strip()) if cspan else 1
                while cspan > 1:
                    cell.insertDummyCell(self.topt.TD, attrValue)
                    cspan -= 1
            except TypeError:
                pass
    return

def insertDummyCell(self, node:Node, colName:str="td-nil") -> Node:
    """Create a dummy cell (generally to take the place of a moribund span),
    and insert it after the given cell.
    """
    dum = self.ownerDocument.createElement(self.topt.TD)
    dum.setAttribute(self.topt.CLASS, colName)
    fsib = self.followingSibling
    if (fsib):
        node.parentNode.insertBefore(fsib, dum)
    else:
        node.parentNode.appendChild(fsib)
    return dum

def eliminateSpans(self):
    """Insert extra cells (empty, or copies of 'filler'), to obviate
    spans within the table.
    """
    theDoc = self.tbl.getDocument()

    # The colspans
    for node in self.tbl.eachElement():
        cs = node.getAttribute(self.topt.COLSPAN)
        if (cs and int(cs) > 1):
            cs = int(cs)
            node.setAttribute(self.topt.COLSPAN, 1)
            nn = node.nodeName
            #row = node.parentNode
            for _i in range(int(cs)):
                newNode = theDoc.createElement(nn)
                node.insertFollowingSibling(newNode)

    # The rowspans
    for node in self.generateRows():
        rs = node.getAttribute(self.topt.ROWSPAN)
        if (rs and int(rs) > 1):
            rs = int(rs)
            node.setAttribute(self.topt.ROWSPAN, 1)
            nn = node.nodeName
            while (rs > 1):
                newNode = theDoc.createElement(nn)
                node.insertFollowingSibling(newNode)
                rs -= 1

def unnest(self):
    nRemoved = 0
    for subtable in self.tbl.eachNode(self.topt.TABLE):
        if (subtable == self.tbl): continue
        subtable.parentNode.removeChild(subtable)
        nRemoved += 1
    return nRemoved

def hasSubTable(self):
    """Is there a table within this table?
    """
    st = self.tbl.getDescendant(self.topt.TABLE)
    return (st is not None)

def ensureOuters(self):
    th = self.getHead()
    if (not th): self.addHead()
    tb = self.getBody()
    if (not tb): self.addBody()

def ensureAllColumnIdents(self) -> int:
    nFailedColumns = 0
    for colNum, col in enumerate(self.generateColumns()):
        nFailedCells = self.ensureColumnIdents(colNum, col)
        if (nFailedCells): nFailedColumns += 1
    return nFailedColumns

def ensureColumnIdents(self:TableOptions, colNum:int, ) -> list:
    """Scan the table by column, and return a list of all the cell
    (row, col) coordinates where there's a column-id problem. If the
    returned list is empty, everything's ok.
    For purposes of this call, the hea row is considered to be row 0.
    """
    badCoords = ()

    theIDs = ()
    for row in self.getHeadRow():
        thisColId = theIDs.append(self.getAttribute(row, self.topt.CLASS))
        if (not thisColId): badCoords.append( (0, colNum) )

    for colNum, _col in enumerate(self.generateColumns()):
        for rowNum in range(1, self.getNumRows()):
            cell = self.getCellByRowColumn(rowNum, colNum=colNum)
            thisColId = cell.getAttribute(self.topt.CLASS)
            if (thisColId != theIDs[colNum]):
                badCoords.append( (rowNum, colNum) )
    return badCoords


###############################################################################
# Tabular structure support (TODO: Integrate)
#
def getColumn(self:Node, onlyChild:str="tbody", colNum:int=1, colSpanAttr:str=None) -> list:
    """Called on the root of table-like structure, return a list of
    the colNum-th child element of each child element. That should amount
    to the colNum-th column.
    @param onlyChild: If not "", look for a child of self of that type,
    and treat it as the container-of-rows.
    @param colSpanAttr: If set, treat that attribute name like HTML "colspan".
    """
    if (onlyChild):
        base = self.selectChild(onlyChild)
    else:
        base = self
    if (not base or base.nodeType != Node.ELEMENT_NODE): return None
    cells = []
    for row in base.childNodes:
        if (row.nodeType != Node.ELEMENT_NODE): continue
        cells.append(row.getCellOfRow(colNum=colNum, colSpanAttr=colSpanAttr))
    return cells

#def generateColumn(self):  # TODO: Implement
#    assert False

def getCellOfRow(self:TableOptions, row:Node, colNum:int=1, colSpanAttr:str=None) -> Node:
    """Pretty much like getElementChild(), but can account for horizontal
    spans (this does not yet adjust for vertical/row spans!).
    """
    found = 0
    for ch in row.childNodes:
        if (ch.nodeType != Node.ELEMENT_NODE): continue
        found += 1
        if (found == colNum): return ch
        if (colSpanAttr):
            cspan = int(ch.getAttribute(colSpanAttr))
            if (cspan > 1): found += cspan-1
    return None


###############################################################################
#
class SORTTYPE(Enum):
    """Basic ways to sort by a given column. Far from complete...
    Perhaps add: whitespace or unicode norm; dictionary style; human-numeric;
    date/time/datetime; version numbers; Mac auto-split. Cf *nix 'sort'.
    """
    STR = 0
    CASELESS = 1
    TOKENS = 2     # Tokenize at \W+, then sort tokenwise
    MACFILE = 3    # Tokenize by alpha vs. numeric
    INT = 10
    FLOAT = 11
    CASH = 12      # Strip whitespace and currency chars, then as float.


###############################################################################
#
class NormTable:
    """Manage a DOM table, with a wrapper and a ton of operations.
    Typically, we assume the table has been normalized:
        No rowspans or colspans
        No nested tables
        Always THEAD and TBODY
        One row in THEAD
        All cells have a column-name set in @CLASS, unique per column.
    On the other hand, actual tag names are always indirected through an
    instance of TableOptions.
    """
    def __init__(self, topt:TableOptions=None, fromTable:Node=None):
        if (topt): self.topt = topt
        else: self.topt = TableOptions()

        if (fromTable is None):
            self.tbl = self.makeDOMTable()
        else:
            self.tbl = fromTable
            if (fromTable.nodeName != topt.TABLE):
                lg.critical("Table node is named '%s', not '%s'.",
                    fromTable.nodeName, self.topt.TABLE)
            self.tbl.unspan()
            self.tbl.unnest()
            self.tbl.ensureOuters()
            self.tbl.ensureColumnIdents()

    def makeDOMTable(self):
        """Make an empty starter table.
        """
        doc = minidom.Document()
        tbl = doc.createElement(self.topt.TABLE)
        doc.appendChild(tbl)
        headRow = doc.createElement(self.topt.TR)
        thead = doc.createElement(self.topt.THEAD)
        thead.appendChild(headRow)
        tbl.appendChild(thead)
        tbody = doc.createElement(self.topt.TBODY)
        tbl.appendChild(tbody)
        return tbl

    def makeElement(self, name:str, attrs:Dict=None, text:str=None):
        doc = self.tbl.ownerDocument
        el = doc.createElement(name)
        if (attrs):
            for k, v in attrs:
                el.setAttribute(k, v)
        if (text):
            el.appendChild(doc.createTextNode(text))
        return el


    ##################################################### TABLE OPERATIONS
    #
    def getShape(self):
        return self.countRows(), self.countColumns()

    def ownerTable(self, node:Node):
        """Return the containing table (if any) given any node.
        Could also just return self.tbl....
        """
        anc = node.tbl
        while (anc):
            if (anc.nodeName == self.topt.TABLE): return anc
            anc = anc.parentNode
        return None

    def clearTable(self):
        # Should this leave same as makeDOMTable?
        while (self.tbl.childNodes):
            self.removeChild(self.tbl.firstChild)
        return self

#    def sortBy(self, keyCols:List):
#        """Sort the rows by some column(s)
#        TODO: Implement. How best to specify keys?
#            [ (colNum|colName, SORTTYPE, reverse)+ ]
#        """
#        assert False

    def transpose(self, replace:bool=False):
        """This makes a transposed copy of the table.
        TODO Ewww, what to do with the header?
        If 'replace' is True, it is spliced in to replace the original.
        In any case, the root of the new transposed thing is returned.
        """
        self.unspan()  # Just in case...

        # Make a destination table
        doc = self.ownerDocument
        t2 = doc.createElement(self.topt.TABLE)
        b2 = doc.createElement(self.topt.TBODY)
        t2.appendChild(b2)

        # Make as many new rows, as the starting table has columns
        nCols = self.getRow(0).countColumns()
        for _i in range(nCols):
            tr2 = doc.createElement(self.topt.TR)
            b2.appendChild(tr2)

        for tr in self.getRows():
            cNum = 0
            for cell in tr.childNodes:
                if (cell.nodeName not in [ self.topt.TD, self.topt.TH ]):
                    continue
                cell2 = cell.cloneNode()()
                b2.childNodes[cNum].appendChild(cell2)
                cNum += 1

        if (replace):
            self.parentNode.replaceChild(t2, self)
        return t2


    ##################################################### HEAD/BODY/FOOT OPS

    def getHead(self):
        return getChildByName(self.tbl, self.nc.THEAD)

    def getHeadRow(self):
        h = getChildByName(self.tbl, self.nc.THEAD)
        if (h): return getChildByName(h, self.nc.TR)
        return None

    def addHead(self, labels:List=None,
        numbered:str=None, moveRow:bool=False) -> None:
        """Add a table head and head row, and hopefully column labels.
        If there's already a thead, do nothing.
        Labels can be sourced from:
            * labels: A list of strings
            * numbered: This string plus a number
            * moveRow: moving the first row into the new THEAD
            * [otherwise]: Fail.
        TODO: Labels vs. contents vs. @CLASS; may want to set all.
        """
        if (self.getHead()): return None
        thead = self.tbl.ownerDocument.createElement(self.topt.THEAD)
        self.tbl.insertBefore(self.tbl.childNodes[0], thead)
        if (labels):
            for lab in labels:
                newCell = self.makeElement(self.topt.TH, text=lab)
                newCell.setAttribute("label", lab)
                thead.appendChild(newCell)
        elif (numbered):
            for i, in range(self.tbl.countColumns()):
                newCell = self.makeElement(self.topt.TH, text=lab)
                newCell.setAttribute("label", numbered+str(i))
                thead.appendChild(newCell)
        elif moveRow:
            theRow = self.tbl.getRow(0)
            thead.appendChild(theRow)
        else:
            assert False, "None of labels, numbers, or moveRow was given."

    def getcolIds(self:Node) -> List:
        colIds = []
        for th in self.getHeadRow().childNodes:
            colIds.append(th.getAttribute(self.topt.CLASS))
        return colIds

    ####### TODO Distinguish column IDENT from column LABEL.
    ####### TODO Support HTML5-ish LABELs.

    def setcolIds(self, colIds:list, alone:bool=True):
        """Given a list of names, assign them by setting an attribute
        on each instance. If 'alone' is True, the attribute is assigned
        that name only; otherwise, the name is appended as a space-separated
        token if not already there, and any prior tokens remain.
        """
        raise NotImplementedError

    def setColName(self, col:Union[int, str], name:str, alone:bool=True):
        """Setting the assigned attribute (typically "CLASS") on the column
        header and all cells in the column.
        If 'alone' is True, the attribute is assigned
        that name only; otherwise, the name is added as a space-separated
        token if not already there, and any prior tokens remain.
        """
        theCol = self.getColumn(col)
        if (alone):
            theCol.setAttribute(self.topt.CLASS, name)
        else:
            buf = theCol.setAttribute(self.topt.CLASS)
            if (buf): buf += " "
            buf += name
            theCol.setAttribute(self.topt.CLASS, buf)

    def getBody(self):
        return getChildByName(self.tbl, self.topt.TBODY)

    def getFoot(self):
        return getChildByName(self.tbl, self.topt.TFOOT)



    ##################################################### ROW OPERATIONS

    def countRows(self) -> int:
        """Find out how many rows there are.
        """
        nFound = 0
        for _tr in self.tbl.getRows(): nFound += 1
        return nFound

    def getRows(self) -> Node:
        """Get all (body) row elements of this (but not of nested) table.
        """
        rows = []
        for row in self.generateRows():
            rows.append(row)
        return rows

    def generateRows(self) -> Node:
        bod = self.tbl.getBody()
        for ch in bod.childNodes:
            if (ch.nodeName == self.topt.TR): yield ch
        return

    def getRow(self, n:int) -> Node:
        """Get the n-th row (counting from 1 -- is that best for this or not?).
        TODO Provide a get-by-key?
        """
        assert n != 0
        if (n < 0):
            rows = self.getRows()
            tgtRow = len(rows) + n
            if (tgtRow < 0): return None
            return rows[tgtRow]
        else:
            nFound = 0
            for row in self.generateRows():
                nFound += 1
                if (nFound >= n): return row
        return None


    ##################################################### COLUMN OPERATIONS
    # These actually operate on whole columns -- not just one cell in a column.
    #
    def getColHeader(self, n:Union[int, str]) -> Node:
        """Can find by name or number.
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
                if (th.getAttribute(self.topt.CLASS) == n): return th
            return None
        else:
            raise TypeError("getColHeader: must be string or int.")

    def insertColBefore(self, colNum:int, ident:str, label:str=None, theCells:List=None):
        """Insert an entire column. If theCells is a list of cells, use them;
        otherwise construct empty ones (plus a header one containing label).
        """
        thead = self.getHead()
        if (theCells):
            newCell = theCells[0]
        else:
            newCell = self.makeElement(self.topt.TH, { self.topt.CLASS:ident }, text=label)
        refCell = self.getCellOfRow(row=thead, colNum=colNum)
        thead.insertBefore(newCell, refCell)
        for rowNum, row in enumerate(self.generateRows()):
            if (theCells):
                newCell = theCells[rowNum+1]
            else:
                newCell = self.makeElement(self.topt.TD, text=label)
            newCell.setAttribute("label", ident)
            refCell = self.getCellOfRow(row=rowNum, colNum=colNum)
            row.insertBefore(newCell, refCell)

    def appendCol(self, ident:str, label:str=None, theCells:List=None):
        thead = self.getHead()
        if (theCells):
            newCell = theCells[0]
        else:
            newCell = self.makeElement(
             self.topt.TH, { self.topt.CLASS:ident }, text=label)  # TODO ???
        thead.appendChild(newCell)

        for rowNum, row in enumerate(self.generateRows()):
            if (theCells):
                newCell = theCells[rowNum+1]
            else:
                newCell = self.makeElement(
                    self.topt.TD, { self.topt.CLASS:ident}, text=label )
            row.appendChild(newCell)
        return

    # TODO: Add copyCol()

    def deleteCol(self, colNum:int) -> List:
        """Delete an entire column.
        Returns the list of deleted cells.
        Better not be any spans, this only covers normalized tables.
        """
        # TODO: Add test for normalized tableness.
        deletedCells = []
        thead = self.getHead()
        theCell = self.getCellOfRow(row=thead, colNum=colNum)
        deletedCells.append(thead.removeChild(theCell))
        for rowNum, row in enumerate(self.generateRows()):
            theCell = self.getCellOfRow(row=rowNum, colNum=colNum)
            deletedCells.append(row.removeChild(theCell))
        return deletedCells

    def moveColBefore(self, fromCol:Union[int, str], toCol:Union[int, str]):
        """Move a column to another location in the column order.
        fromCol is the current column position; toCol is where it will be
        once done (considering the column deletion, which matters).
        TODO: For the moment, this doesn't take column names, only numbers.
        """
        theCells = self.deleteCol(fromCol)
        self.insertColBefore(toCol, theCells)

    def swapCol(self, fromCol:Union[int, str], toCol:Union[int, str]):
        if (fromCol == toCol): return
        if (fromCol > toCol):
            tmp = toCol; toCol = fromCol; fromCol = tmp
        originalRightCells = self.deleteCol(toCol)
        originalLeftCells = self.deleteCol(fromCol)
        self.insertColBefore(fromCol, originalRightCells)
        self.insertColBefore(toCol, originalLeftCells)

    def setColIdent(self:Node, colNum:int, newColId:str, alone:bool=True):
        """Given a list of names, assign them by setting the given attribute
        on each instance. If 'alone' is True, the attribute is assigned
        that name only; otherwise, the name is added as a space-separated
        token if not already there, and any prior tokens remain.
        TODO: Generalize to allow setting any attribute on all cells of column.
        TODO: Way to remove an old ID token.
        """
        if (not attrName): attrName = self.topt.CLASS
        for cell in self.generateCellsOfCol(colNum):
            if (alone):
                cell.setAttribute(self.topt.CLASS, newColId)
            else:
                cell.setAttributeToken(self.topt.CLASS, newColId)
        raise NotImplementedError


    ##################################################### CELL OPERATIONS

    def countCells(self, row:Node) -> int:
        """Return the number of column in a given row.
        This accounts for colspans.
        """
        assert self.nodeName == self.topt.TR
        nCols = 0
        for cell in row.childNodes:
            if (cell.nodeName not in [ self.topt.TD, self.topt.TH ]): continue
            try:
                cspan = cell.getAttribute(self.topt.COLSPAN)
                cspan = int(cspan.strip()) if cspan else 1
                nCols += cspan
            except TypeError:
                pass
        return nCols


    def getCells(self) -> Node:
        assert False

    def generateCells(self) -> Node:
        """Generate the cells in a given row.
        """
        assert self.nodeName == self.topt.TR
        for cell in self.childNodes:
            if (cell.nodeName in [ self.topt.TD, self.topt.TH ]): yield cell
        return

    def _insertCellBefore(self, row:int, col:Union[int, str], colData:any):
        refCell = self.getCellByRowCol(row, col)
        assert refCell
        newCell = self.tbl.ownerDocument.createElement(self.topt.TD)
        newCell.innerText = colData
        refCell.parentNode.insertBefore(newCell, refCell)  # TODO: Arg order?
        return refCell

    # TODO: col num<>name > dtype <cell
    def getColHeaderForCell(self, node:Node) -> Node:
        assert node.nodeName == self.topt.TD
        colNum = self.getColNum()
        # Or node.getAttribute(self.topt.CLASS)...
        return self.getColHeader(colNum)

    def getColNumOfCell(self:Node) -> int:
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


    ###########################################################################
    #
    def checkNesting(self:Node) -> int:
        """Check whether nested tables, if any, obey NormTable restrictions.
        @return Number of errors found.
        """
        errCount = 0
        nestedTables = self.getElementsByTagName("table")
        if (not nestedTables): return 0
        if (not self.nestedOk):
            errCount += 1
            lg.warning("    %d nested tables found.", len(nestedTables))
        else:
            for nt in nestedTables:
                # TODO: Allow WSN
                if (nt.previousSibling or nt.nextSibling):
                    errCount += 1
                    lg.warning("    nested table is not alone.")
        return errCount

    def checkKeys(self:Node):
        raise NotImplementedError


    ###########################################################################
    # Manipulate existing tables toward norm
    #
    def removeThead(self:Node, _promote:bool=True):
        """TODO: Support 'promote' to move any thead rows into tbody.
        Then remove the thead itself.
        """
        for thead in self.table.getElementsByTagName(self.topt.THEAD):
            thead.parent.removeElement(thead)

    def removeTfoot(self:Node, _promote:bool=True):
        for tfoot in self.table.getElementsByTagName(self.topt.TFOOT):
            tfoot.parent.removeElement(tfoot)

    def attrToCol(self:Node, colNum:int, attrName:str, ident:str, label:str=None):
        """Promote one attribute of cells in a column, to form a new column.
        TODO: Add way to put it on target attribute vs. content (see addToCell()).
        """
        theCells = []
        for cell in self.generateCellsOfCol(colNum):
            attrVal = cell.getAttribute(attrName)
            newCell = self.makeElement(self.topt.TH, text=attrVal)
            if (ident): newCell.setAttribute(self.topt.CLASS, ident)
            theCells.append(newCell)
        self.insertColBefore(colNum=colNum, ident=ident, label=label, theCells=theCells)

    #def colToAttr(self:Node, attrName:str, ident:str, label=label):
        """Remove a column, and move something from into into another column.
        Take: Text Content or an attribute(s) (see DomExtensions choices)
        Put: Before/after/as Content or an attribute.
        TODO: Implement using addToCell().
        """

    def addToCell(self, cell:Node, text:str, locus:str="#text",
        disp:str="REPLACE", sep:str=" "):
        """Attach the given 'text' to the given 'cell', in a certain place:
            locus: If #text, in content, otherwise on the named attribute.
            disp: One of
                REPLACE -- replace all of the existing text or attrvalue (if any)
                BEFORE -- prepend
                AFTER -- append
                UNION -- only for tokenized attributes like HTML @CLASS; this
                    appends if the same token isn't there, else does nothing.
            Except for #text or REPLACE, put 'sep' in as a separator.
        """
        # TODO: This may create adjacent text nodes.
        if (locus == "#text"):
            newCell = self.makeTextNode(text)
            if (disp == "REPLACE"):
                while (cell.childNodes): cell.delete(cell.childNodes[-1])
                cell.appendChild(newCell)
            elif (disp == "BEFORE"):
                cell.insertChildBefore(newCell, cell.childNodes[0])
            elif (disp == "AFTER"):
                cell.appendChild(newCell)
            else:
                assert False, "DISP must be one of REPLACE, BEFORE, AFTER."
            cell.appendChild(newCell)
        elif (DomExtensions.isXmlName(locus)):
            val = cell.getAttribute(locus) or ""
            if (disp == "REPLACE"): val = text
            elif (disp == "BEFORE"): val = text + sep + val
            elif (disp == "AFTER"): val = val + sep + text
            elif (disp == "UNION"):
                if (not cell.hasAttributeToken(text)): return
                val = val + sep + text
            else:
                assert False, "DISP must be one of REPLACE, BEFORE, AFTER, UNION."
            cell.setAttribute(val)
        else:
            assert False, "locus must be #text or an attribute name"


    ###########################################################################
    # Format support
    #
    def reorderCols(self:Node, sortSpec:list):
        """ways to sort:
            by a list of names
            by value in col (using explicit datatype?)
            like bbedit, by regex caps from value
            by attribute(s)
            asc/desc
            empties to start or end
        """
        raise NotImplementedError

    def clearCellsByContent(self:Node, expr:str=None, nbIsSpace:bool=True):
        """Clear content of cells
        """
        raise NotImplementedError

    def deleteRow(self:'NormTable', rowNum:int):     # By number
        theRow = self.getRow(rowNum)
        assert theRow
        self.table.removeChild(theRow)  # TODO: Mr. tbody?

    def createTable(self, nRows:int, nCols:int, cellClasses:list=None):
        """Make an entire n*m table.
        If cellClasses is given it must be a list of length nCols, and its values
        must be strings to be put into @CLASS of the respective cell elements.
        """
        if (cellClasses): assert len(cellClasses) == nCols

        doc = self.ownerDocument
        t2 = doc.createElement(self.topt.TABLE)

        h2 = doc.createElement(self.topt.THEAD)
        t2.appendChild(h2)
        h2.appendChild(self.CreateRow(nCols, th=True, cellClasses=cellClasses))

        b2 = doc.createElement(self.topt.TBODY)
        t2.appendChild(b2)
        for _i in range(nRows):
            b2.appendChild(self.CreateRow(
                nCols, th=False, cellClasses=cellClasses))

        f2 = doc.createElement(self.topt.TFOOT)
        t2.appendChild(f2)
        f2.appendChild(self.CreateRow(nCols, th=True, cellClasses=cellClasses))

        self.tbl = t2
        return t2

    def insertRowBefore(self, before:Union[Node, int]) -> Node:
        """Create a row with nCols cells, all empty, and insert it before
        the given row (specified by reference or rowNum).
        """
        cellIds = self.getcolIds()
        nCols = len(cellIds)
        doc = self.ownerDocument
        newRow = doc.createElement(self.topt.TR)
        for i in range(nCols):
            cell = doc.createElement(self.topt.TD)
            cell.setAttribute(self.topt.CLASS, cellIds[i])
            newRow.appendChild(cell)
        if (isinstance(before, int)):
            refRow = self.getRow(before)
        else:
            refRow = before
        self.tbl.insertBefore(newRow, refRow)  # TODO: Check order vs. DOM
        return newRow

    def listList2Table(self, data:list) -> Node:
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

    def deleteTable(self:'NormTable'):  # TODO: Drop?
        raise NotImplementedError

    def setCol(self:'NormTable'):  # TODO: Drop? Or change to SetColDatatype?
        raise NotImplementedError

    def renameTable(self:'NormTable'):  # TODO: Drop?
        raise NotImplementedError

    def renameCol(self:'NormTable'):  # TODO: Drop?
        raise NotImplementedError


###########################################################################
# Do SQL on these
#
class JoinTypes(Enum):
    INNER = 1
    OUTER = 2
    LEFT  = 3
    RIGHT = 4

class SQLTable(NormTable):
    """Add basic RDB operations.
    See various other methods above, like sortBy, transpose, insertCol...
    """
    def project(self:'NormTable', cols:List):
        """Extract the given columns, in the given order.
        """
        raise NotImplementedError

    def select(self:'NormTable', rowChecker:Callable):
        """Iterates over the row, and extracts the cell values from each.
        They are copied into a dict, keyed by column name. Then the
        rowChecker is called with the NormTable object and the dict.
        If it returns Truish, the row will be copied to the output table.
        """
        raise NotImplementedError

    def join(
        self:'NormTable', other:'NormTable',
        selfCols:list, otherCols:list, joinType:int=JoinTypes.INNER):
        """Given two tables, generate the result of joining them....
        What's the easiest way to pass a join condition?
        Probably start with a list of field-name pairs, and compare ops?
        Then add an eval-able or callback that can generate temp-fields (and
        let the temp fields be named in the join, too)?
        """
        raise NotImplementedError

    # Set ops, too?
    #
    def union(self:'NormTable'):
        raise NotImplementedError

    def intersection(self:'NormTable'):
        raise NotImplementedError

    def diff(self:'NormTable'):
        raise NotImplementedError

    def symdiff(self:'NormTable'):
        raise NotImplementedError


###############################################################################
#
class Condition:
    """A condition such as used by SQL select, join, where-clauses in general.
    """
    def __init__(self, expr:str):
        """Create an interpretable AST from some syntax.
        """
        raise NotImplementedError



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
    tags = TableOptions()

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
