#!/usr/bin/env python
#
# 2011-10-13: Written by Steven J. DeRose (in Perl)
# ...
# 2012-01-10 sjd: Start port to Python.
# 2012-01-18f sjd: Add setInputtext(), setStrict(), setKeySeparator().
#     Clean up text buffer handling. Debug. Drop lwarn() for sjdUtils.
#     Add HTML Entities support.
# 2012-02-24 sjd: Implement default values.
# 2012-03-12 sjd: Make Head a container, not an empty. Add multiHead.
# 2012-06-06 sjd: Drop strict, multiHead. Prep for sync w/ Perl version.
# 2012-12-10 sjd: Start getting it to actually work again. More sync.
#     Keep attribute order from Head, for use in output. Seems working.
# 2014-04-08: Switch from htmlentitydefs to HTMLParser.
# 2014-05-14: Sync w/ Perl version. Separate options into hash. Drop sjdUtils.
#    Make getLogicalLine() do almost all of parsing. Compile more regexes.
#    Options dict, and make some settable on constructor.
# 2014-09-03: Add encoding arg to constructor and to open; readline exceptions.
#     Drop setInputFile(). Use codecs.open().
# 2015-03-15: Drop all the 'text' stuff, let caller user StringIO if needed.
#     Better stack handling. Raise real exceptions, simplify error handling.
# 2015-04-11: Start on datatype validatin.
#
# To do:
#     Add validation support.
#     Possibly: move defaulting to a container element?
#     Possibly: option to recognize \xFF and similar?
#     Possibly: coerce items to type specified by #...#? including []?
#     Support table name, key field(s), blobs? in Head
#     Set attrOrder right (while parsing attrs)
#     Always at least default to "" (not None) -- why isn't it?
#     Re-sync with Perl version
#     Profile
#     Offer export to everything TabularFormats can do?
#
import sys, re
#import string
#import math
import codecs

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    import HTMLParser
    string_types = basestring
else:
    from html.parser import HTMLParser
    string_types = str
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): str(s, encoding, errors)

# Regexes for XSV syntax items (compiled in the constructor)
#
cex = {}
cex["eq"]        = r'='
cex["qlit"]      = r"('[^'<]*'|\"[^\"<]*\")"
cex["xname"]     = r'([_:\w][-_:.\w]*)'
cex["como"]      = r'<!--'
cex["comc"]      = r'-->'

cex["xdclo"]     = r'<\?xml '
cex["stago"]     = r'<'  + cex["xname"]
cex["etago"]     = r'</' + cex["xname"]

cex["attr"]      = cex["xname"]+r'\s*'+cex["eq"]+r'\s*'+cex["qlit"]
cex["xdcl"]      = r'<\?xml(\s+' + cex["attr"] + r')+\?>\s*$'

cex["stag"]      = cex["stago"] + r'(\s+' + cex["attr"] + r')*\s*/?>'
cex["etag"]      = cex["etago"] + r'\s*>'
cex["com"]       = cex["como"] + r'([^-]|-[^-])*' + cex["comc"]

cex["attrSpec"]  = r'^#.*?(#|$)'
cex["empty"]     = r'/>\s*$'
cex["spaces"]    = r'^\s*$'
cex["newline"]   = r'^([^\n\r]+)([\n\r]+)'

#cex["pi"]        = r'<\?(\w+)\s+([^?]|\?[^>])*' + r'\?>'
#cex["cdata"]     = r'<!\[CDATA\[' + '([^\]]|\][^\]]|\]\][^>])*' + r'\]\]>'
#cex["mdcl"]      = r'<!' + cex["xname"] + r'([^>]|'+cex["qlit"]+r')*>'
#cex["cref"]      = r'&#[xX][\dA-Fa-f]+;|&#\d+;|&\w+;'
#cex["text"]      = r'[^<&]*'

tagNameAttr = "#TAG" # Pseudo-attribute in which to return element type name

class XmlTuples:
    def __init__(self, srcFile=None, encoding='utf-8', verbose=0):
        self.inFile     = None         # Path to input file/source
        self.encoding   = encoding     # Char set encoding to assume?
        self.inFH       = None         # Handle to input file
        self.lineNum    = 0            # Physical line we're on

        self.tagStack   = []           # Parser state
        self.inHead     = 0            # Are we inside a Head element?

        self.headNames  = []           # List of field names (set by Head)
        self.defaults   = {}           # Default values from <Head>
        self.typespecs  = {}           # Datatype prefixes from <Head>
        self.typespecsP = {}           # And as parsed
        self.errorCode  = ""
        self.errorMsg   = ""

        self.options = {
            "typeCheck"     : 0,
            "verbose"       : verbose,
            "breakAttrs"    : 0,       # For output, each attribute new line?
            "njustify"      : 1,       # Output width for numeric fields
            "dt"            : 0,
            "validate"      : False,   # Check datatypes declared on <Head>?

            "reservedChar"  : '#',     # Not yet used
            "assignChar"    : '=',     # Separates attr name and value
            "keySep"        : "#",     # Separator for parts of compound key
            "loose"         : 0,       # Allow variant delimiters?
            "xsvName"       : "Xsv",   # Tag for root recognize
            "headName"      : "Head",  # Tag for header record
            "recName"       : "Rec",   # Tag for data records
        }

        self.typespecExpr = re.compile(r'^(#)(\w+)(\(.*?\))?([!?*+])?(.*)')
        self.dtObject     = None

        # Gathered data
        self.dcInfo       = {},        # Dublin Core attrs from Xsv (optional)
        self.attrNames    = {},        # Hash of attr names and default values
        self.attrOrder    = [],        # Attr names in order on <Head>
        self.ids          = {},        # ID attribute values seen
        self.idrefs       = {},        # IDREF attr values (and tokens) seen

        self.errorCode    = "",        # last error code
        self.errorMsg     = "",        # last error message text

        self.setStackSequence()

        self.theHTMLParser = HTMLParser() # For expanding entities
        if (srcFile):
            self.open(srcFile, encoding=encoding)

        if (self.options["verbose"]>2):
            self.xWarn(0, "\nCompiling parsing expressions:")
            for k, v in (cex.items()):
                self.xWarn(0, "    %-10s  /%s/" % (k, v))
                cex[k] = re.compile(v)


    def reset(self):
        """Re-initialize everything except options, so we can parse more.
        """
        self.attrNames  = None
        self.inFile     = None
        if (self.inFH):
            self.inFH.close()
            self.inFH   = None
        self.lineNum    = 0
        self.ids        = {}
        self.idrefs     = {}
        self.tagStack   = []


    ###########################################################################
    #
    def setOption(self, name, value):
        """Set the value of the named option.
        """
        if (name not in self.options):
            self.xWarn(0, "XSV::setOption: Unknown option '%s'." % (name))
            return(None)
        self.options[name] = value
        self.setStackSequence()
        #self.setupRegexes() # in case we changed a delimiter, etc.
        return(value)

    def getOption(self, name):
        """Return the value of the named option.
        """
        if (name not in self.options):
            self.xWarn(0, "XSV::getOption: Unknown option '%s'." % (name))
            return(None)
        return(self.options[name])


    ###########################################################################
    # Error reporting
    #
    def getError(self):
        return(self.errorCode)

    def clrError(self):
        self.errorCode = ""
        self.errorMsg = ""

    def setError(self, code, msg, msg2=""):
        self.errorCode = code
        self.errorMsg = msg+msg2
        print(msg+msg2)

    def xWarn(self, level, msg, context=""):
        if (self.options["verbose"] < level): return
        msg = msg.strip()
        if (context): msg += "\n" + context
        sys.stderr.write("XSV: at line %d: %s.\n" % (self.lineNum, msg))


    ###########################################################################
    # (meta-) data access
    #
    def getLineNumber(self):
        return(self.lineNum)

    def getFieldNamesArray(self):
        return(self.attrOrder) # an array

    # Dublin Core data from <Xsv> element (optional).
    def getDCInfo(self):
        return(self.dcInfo)

    def isXsv(self, hashRef):
        if (tagNameAttr in hashRef and
            hashRef[tagNameAttr] == self.options["xsvName"]): return(1)
        return(0)

    def isHead(self, hashRef):
        if (tagNameAttr in hashRef and
            hashRef[tagNameAttr] == self.options["headName"]): return(1)
        return(0)

    def isRecord(self, hashRef):
        if (tagNameAttr in hashRef and
            hashRef[tagNameAttr] == self.options["recName"]): return(1)
        return(0)


    ###########################################################################
    # Reconstruct XSV for output.
    #
    def makeXSVRecord(self, dictOfFields):
        buf = ""
        for k in (self.attrOrder):
            if (self.options["breakAttrs"]): buf += "\n    "
            else: buf += " "
            try:
                f = float(dictOfFields[k])
                v = '"%s"' % (dictOfFields[k])
                if (self.options["njustify"]):
                    v = v.rjust(self.options["njustify"])
            except ValueError:
                v = dictOfFields[k]
                v = re.sub(r'&', "&amp;",  v)
                v = re.sub(r'<', "&lt;",   v)
                v = re.sub(r'"', "&quot;", v)
                v = '"%s"' % (dictOfFields[k])
            buf += ('%s=%s' % (k, v))
        return("<Rec " + buf + "/>\n")


    ###########################################################################
    # Line/record input
    #
    def open(self, path, encoding='utf-8'):
        self.encoding = encoding
        self.inFH = codecs.open(path, mode="r", encoding=encoding)
        if (not self.inFH): return(0)
        self.inFile  = path
        self.lineNum = 0
        return(1)

    def attach(self, fh):
        if (self.inFH): inFH.close()
        self.inFile  = None
        self.inFH    = fh
        self.lineNum = 0
        return(1)


    def getLogicalLine (self):
        """This has taken over nearly all of the parsing work.
        Returns: more-or-less a SAX event:
            buf, typ, nam, ats, empty
        """
        buf = ""
        typ = None
        nam = None
        ats = {}
        empty = False
        inWhat = ""
        startingLineNum = self.lineNum
        while ((1)):
            if (not self.inFH): return(None)
            line = self.inFH.readline()
            if (not line):
                if (buf == ""): return(buf,"EOF",nam,ats)       # EOF
                break
            self.lineNum = self.lineNum + 1

            if (buf=="" and re.match(cex["spaces"],line)):      # Whitespace
                continue

            buf += line

            if (not inWhat):                      # Nothing yet -start?
                buf = buf.lstrip()
                # Check what construct is opening
                for x in (["como", "stago", "etago", "xdclo"]):
                    mat = re.search(cex[x], buf)
                    if (mat):
                        inWhat = x
                        if (x=="stago" or x=="etago"):
                            #mat = re.sub(cex[x], buf)
                            nam = mat.group(1)
                        break
                if (not inWhat):
                    self.xWarn(1, "Bad syntax near '%s'" % (buf))
                    buf = ""
                    continue
                else:
                    self.xWarn(1, "Started a '%s' at '%s'." % (inWhat, buf))

            # We've got a start, read til complete.
            #
            if (inWhat == "como"):                # Continue comment
                if (re.search(cex["com"], buf)):
                    typ = "COM"
                    break
                elif (re.search('--', buf[4:]) > 0):
                    self.xWarn(0, "Bad comment near '%s'" % (buf))
                    typ = "ERROR"
                    break

            elif (inWhat == "stago"):             # Continue start-tag
                if (re.search(cex["stag"], buf)):
                    typ = "STAG"
                    ats[tagNameAttr] = nam
                    if (re.search(cex["empty"], buf)): empty = True
                    for mat in (re.finditer(cex["attr"],buf)):
                        val = self.theHTMLParser.unescape(mat.group(2))
                        ats[mat.group(1)] = val[1:-1]
                    break
                elif ('>' in buf):
                    self.xWarn(0, "Bad start-tag near '%s'" % (buf))
                    typ = "ERROR"
                    break

            elif (inWhat == "etago"):             # Continue end-tag
                if (re.search(cex["etag"], buf)):
                    typ = "ETAG"
                    break
                elif ('>' in buf):
                    self.xWarn(0, "Bad end-tag near '%s'" % (buf))
                    typ = "ERROR"
                    break

            elif (inWhat == "xdclo"):             # Continue XML decl
                if (re.search(cex["xdcl"], buf)):
                    typ = "XDCL"
                    break
                elif ('?>' in buf):
                    self.xWarn(0, "Bad XML declaration near '%s'" % (buf))
                    typ = "ERROR"
                    break
            # Go around for continuation lines...

        #self.xWarn(4, "Logical line: //%s//" % (buf))
        return(buf, typ, nam, ats, empty)


    ###########################################################################
    # Actual parsing
    #
    def getHeader(self):
        """Read the XSV <Head> start-tag, collecting the known attribute
        names and default values.
        """
        while (1):
            aHash = self.getNext()
            if (not aHash): break
            #self.xWarn(0, "getHeader: type %s (%s): %s" %
            #    (type(aHash), aHash[tagNameAttr], ", ".join(aHash.keys())))
            if (self.isHead(aHash)):
                nameArray = self.getFieldNamesArray()
                return(nameArray)
            if (self.isRecord(aHash)):
                return([])
        return([])

    def getAllAsArray(self):
        """Read all the records, each one as a hash of fields,
        and put them all into an array in the order read.
        """
        theArray = []
        while (1):
            aRecord = self.getNext()
            if (not aRecord and self.getError()=="EOF"): break
            theArray.append(aRecord)
        return(theArray)

    def getAllAsHash(self, theKeys):
        """Read all the records, each one as a hash of fields,
        and put them all into a hash, keyed by the key fields named in theKeys.
        """
        if (isinstance(theKeys, basestring)):
            theKeys = [ theKeys ]
        elif (not isinstance(theKeys, list)):
            return(None)
        nKeyAttributes = len(theKeys)
        if (nKeyAttributes < 1):
            return(None)
        theHash = {}
        nTuples = 0
        while (1):
            aRecord = self.getNext()
            if (not aRecord): break
            nTuples = nTuples + 1
            key = ""
            for i in (range(0,nKeyAttributes)):
                if (theKeys[i] in aRecord):
                    key += aRecord[theKeys[i]]
                key = key + self.options["keySep"]
            if (key.lstrip(self.options["keySep"]) == ""):
                self.xWarn(0,"No key (%s) in record %d, theKeys were: %s" %
                           (key, nTuples, str(aRecord)))
            elif (key in theHash):
                self.xWarn(0,"Duplicate key '%s' in record #%d" %
                           (key, nTuples))
            else:
                theHash[key] = aRecord
        return(theHash)


    def getNext(self):
        """Read the next XML event, discarding anything except start-tags,
        which in XSV have all the data. For start-tags, apply any defaults
        and then return the hash of fields we got.
        """
        self.clrError()
        tline     = ""
        eventType = "COM"
        name      = ""
        attrs     = None
        isEmpty   = False

        while (eventType in ["COM", "XDCL"]):
            tline, eventType, name, attrs, isEmpty = self.getLogicalLine()
            if (not tline):                                # EOF
                self.errorCode = "EOF"
                return(None)

        if (eventType == "STAG"):                          # Start-tag
            attrs = self.applyDefaults(attrs, tline)
            if (not isEmpty):
                self.openElement(name)
            if (name == self.options["headName"]):
                self.handleHeader(attrs)
            elif (self.options["validate"]):
                self.checkDatatypes(attrs)
            return(attrs)

        elif (eventType == "ETAG"):                        # End-tag
            self.closeElement(name)
            return(None)

        elif (eventType == "ERROR"):                       # ERROR
            return(None)

        raise AssertionError("Unknown eventType '%s'" % (eventType))


    def handleHeader(self, attrs):
        """Save the declared fields (attributes) found on <Head>,
        including any default values, and any #...# prefixes, which
        can specify a datatype constraint for the field.
        """
        fieldCount = 0
        self.attrOrder = sorted(attrs.keys())           ####### FIX
        self.typespecs = {}
        self.defaults = {}
        for k, v in attrs.items():
            fieldCount += 1
            mat = re.match(r'#([^#]*)#(.*)$', v)
            if (not mat):
                self.typespecs[k] = None
                self.defaults[k] = attrs
            else:
                ts = mat.group(1)
                mat = re.match(self.parseTypespec, ts)
                if (not mat):
                    self.setError("ValueError",
                        "Type spec '%s' for field '%s' is not valid." % (ts, k))
                else:
                    self.typespecsP[k] = {
                        # Don't store the leading RNI ("#")
                        "typename":	mat.group(2),
                        "arg":	    mat.group(3),
                        "rep":		mat.group(4),
                        "dft":	    mat.group(5),
                    }
                self.typespecs[k] = ts
                self.defaults[k] = mat.group(2)

        return(fieldCount)

    def checkDatatypes(self, attrs):
        """Check each field for which we have a datatype specification
        (from <Head>), and return the number of violations.
        Lack of "#REQUIRED" attributes is check separately in applyDefaults().
        """
        nErrs = 0
        for k, v in self.typespecsP.items():
            if (not self.checkOneDatatype(attrs[k], v)):
                self.setError("ValueError",
                    "Value '%s' for field '%s' does not match datatype '%s'." %
                    (attrs[k], k, v))
                nErrs += 1
        return(nErrs)


    def checkOneDatatype(self, value, tsp):
        """Check one attribute value against its defined datatype spec, which is:
            { rep:x, typename:x, arg:x, dft:x }
        """
        # Not finished; cf XmlTuples.pm, Datatypes.py
        if (not self.dtObject):
            from Datatypes import Datatypes
            self.dtObject = Datatypes()

        rep = tsp["rep"]
        if (value == "" and (not rep or rep=="!" or rep=="+")):  # Required!
            self.setError(
                "REQATTR",
                "Attribute '%s' required but missing." % (value))
            return(False)
        return(self.dtObject.checkValueForType(value, tsp))


    def applyDefaults(self, attrs, tline):
        """Go through all the declared fields (learned from <Head>), and
        for any that weren't found in the input record (<Rec>), apply any
        default that we know for them.
        """
        for aname in (self.headNames):
            if (aname in attrs): continue
            if (self.defaults[aname]=="#REQUIRED"):
                self.setError("REQATTR",
                    "#REQUIRED attribute '%s' missing in:\n    %s" %
                    (aname, tline))
                raise AttributeError("Missing #REQUIRED XSV attribute '%s'" %
                    (aname))
            attrs[aname] = re.sub(cex["attrSpec"],'',self.defaults[aname])
        return(attrs)


    ###########################################################################
    # Maintain a stack of open elements, like a real XML parser.
    #
    def setStackSequence(self):
        """Collect the chosen tag names, in the order they are permitted
        to nest (used by openElement() for validation).
        Called by constructor and setOption.
        """
        self.stackSequence = [
            self.options["xsvName"],
            self.options["headName"],
            self.options["recName"],
            "???"
        ]
        return

    def openElement(self, tag):
        depth = len(self.tagStack)
        if (tag != self.stackSequence[depth]):
            raise SyntaxError("XSV: Bad start tag '%s', stack is %s." %
                              (tag, self.tagStack))
        self.tagStack.append(tag)
        return(len(self.tagStack))

    def closeElement(self, tag):
        if (tag==self.tagStack[-1]):
            self.tagStack.pop()
        else:
            raise SyntaxError("XSV: Bad end tag '%s'." % (tag))
        return(len(self.tagStack))


###############################################################################
###############################################################################
###############################################################################
#

poddoc = """

=pod

=head1 Usage

XmlTuples.py

Parses a tiny subset of XML, known as XSV.
XSV is comparable to CSV files in terms of structure, but is
more human-readable, checkable, and consistent.
The information is well-formed XML, so works with any XML parser.

XSV data may be larger or smaller than the same data in other simple formats.
For example:

    JSON:  { "FN":"John", "LN":"Doe", "DOB":"1900-01-01", "N":99 }
    XSV:   <Rec FN="John" LN="Doe" DOB="1900-01-01" N="99"/>
    JSON:  [ "John", "Doe", "1900-01-01", 99 ]
    CSV:   John, Doe, 1900-01-01, 99

CSV can be very space-efficient.
The costs are that fields must always be in the same order, that long or
complex records are difficult to proofread or correct (and in many kinds
of CSV, cannot be broken into shorter lines). CSV files
come in countless variations with unpredictable support for quoting,
quoted fields containing newlines or quotes, Unicode, headers, etc.

JSON avoids some of these problems (especially that of inconsistent syntax rules).
JSON which uses field-names consistently avoids even more of the problems,
but suffers some space cost instead. The space cost will often be more with JSON
than with XSV (or, for that matter, competent XML); but not always.
In XSV, any field instances
whose values are the default can be entirely omitted. So files with many
defaultable fields (for example, many 0s in statistical datasets),
can be vastly more space-efficient:

    XSV: <Rec Name="MysteryPerson" Age="31"/>
    CSV: MysteryPerson,,,,,,,,,,,,,,,,,,,,,,,,31,,,,,,,,,,,,,,,,,/>

XSV also:
    Allows multiple tables within a single file
    Is much easier to be sure you've got right
    Supports comments throughout the file
    Supports Dublin Core Metadata describing your file
    Can be parsed with any off-the-shelf XML parser


XSV is especially good for:
    readability (especially with long records)
    non-ASCII data
    portability across programming languages
    avoiding problems with quotes, commas, tabs, etc.
    datasets with many default or empty fields.

In programming terms, each logical record in XSV amounts to
a dictionary (or hash) of (fieldName: value) pairs.

Some test data is in:
    ~/bin/SAMPLE_DATA/xsvSample.xsv

This is the Python version; XmlTuples is also available in Perl.
Additional ports, bug reports, etc. may be sent to the author.



==Example==

  myXsvData = ('
  <!-- A collection of really great data. -->
  <Xsv creator="G. Washington" data="1776-07-04">
  <Head Hex="" Unicode="" EntName="" Descr=""/>
  <Rec Hex="80" Unicode="00C4" EntName="Auml"  Descr="A with diaeresis"
       Literal="&#x00c4;"/>
  <Rec Hex="81" Unicode="00C5" EntName="Aring" Descr="A with ring"/>
  ...
  </Head>
  </Xsv>
  ')

=head3 Parsing using this package

  from XmlTuples import *

  foo = XmlTuples(myXsvData, verbose=1)
  headerDict = foo.getNext() # Reads the header
  while (True):
      recordDict = foo.getNext()
      if (not recordDict): break
      if (recordDict["#TAG"] == "Rec"):
          print "Another record:"
          for k in (sorted recordDict):
              print(k + ": " + recordDict[k])
      if (recordDict["#TAG"] == "Head"):
          print("\nNEW TABLE STARTING")


=head3 Parsing using a generic XML parser

This example does not do XSV datatype validation, though of course
you get XML Well-Formedness checking from the parser (and you could write
and apply an XSD, Relax-NG, DTD, or Schematron schema if desired). It does,
however, remember and apply the declared defaults (an XML parser, by itself,
does not).

  import xml.etree.ElementTree as ET
  tree = ET.parse("/tmp/mystuff.xsv")
  root = tree.getroot()

  # Collect default values and datatypes from the <Head>
  head = root[1]
  if (head.tag != "Head"): sys.exit(99)
  datatypes = {}
  defaults = {}
  for k, v in head.attrib
      mat = re.match(r'^#([^#]*)(#|$)(.*)$', v)
      if (mat):
          datatypes[k] = mat.group(1)
          defaults[k] = mat.group(2)
      else:
          datatypes[k] = None
          defaults[k] = v

  tuplesRef = {}
  for (i=1; i<len(head); i++):
      rec = head[i]
      if (rec.tag == "Rec"):
          for aname (keys headAttrs): # Apply defaults
              if (rec.attrib[aname] is None):
                   rec.attrib[aname] = defaults[aname] or None
          tuplesRef[rec.attrib["EntName"]] = rec.attrib
          yield tuplesRef # Or whatever you want to do with the record...
      if (rec.tag == "Head"):
          yield "New table starting"


==Formal identification==

If you want a formal way to refer to this specific subset and
application of XML, I prefer "XSV" for the name, ".xsv" for
the file extension, a MIME type of "text/xsv+xml" (see L<RFC3023>),
and a namespace URI of L<http://derose.net/namespaces/XSV-1.0>.



=head1 Methods

=over

=item * B<xt = new XmlTuples(file=None, encoding='utf-8', verbose=0)>

Set up the XSV parser, with an (optional) file or file-like object to parse.
You can use I<open(path, encoding='utf-8')> of I<attach(handle)
to add data later (I<open> uses Python's codecs.open()).
To parse from a string, use the I<StringIO> package.
You may also specify a setting for the I<verbose> option, to enable
more detailed tracing if desired.


=item * B<xsv.reset>()

Reset everything except options.

=item * B<xsv.setOption(name, value)>

Set the specified option. Available options are:

=over

=item I<verbose> (default 0): More messages.

=item I<breakAttrs> (default 0): For output, put each attribute on a new line.

=item I<njustify> (default 1): When using I<makeXSVRecord>(),
right-justify numeric values in this width for output.

=item I<dt> (default 0):

=item I<typeCheck> (default 0): Do type-checking for attributes that
specify a datatype prefix in Head.

=back

The following additional options change the syntax allowed, such
as the reserved delimiter characters and element type names.

=over

=item I<keySep> (default "#"): Separator for parts of compound key

=item I<reservedChar> (default '#'): Used to separate the type-declaration
from the default value in Head attributes.

=item I<assignChar> (default '='): Separates attribute name and value

=item I<loose> (default 0):

Allow some variant delimiters. This can be used to read very similar formats,
such as that of the Unicode databases.

=item I<xsvName> (default "Xsv"): Tag for outermost element.

=item I<headName> (default "Head"): Tag for header record

=item I<recName> (default "Rec"): Tag for data records.

=back

=item * B<xsv.getOption(name)>

Return the value of the specified option.

=item * B<xsv.open(path, encoding='utf-8')>

Set up to take input from the file at I<path>, via codecs.open().
Any file and line number are cleared. Returns success flag.

=item * B<xsv.attach(handle)>

Provide a reference to a file or file-like object to parse.
Returns success flag.

=item * B<array = xsv.getHeader>()

Read to the C<Head> start-tag, and return an array of the attribute names
that occurred on it, in the order they appear in the input.

=item * B<array = xsv.getAllAsArray>()

Use I<getNext>() to parse all the records available.
Return an array of the data,
in the same order as found in the input. Each entry in that array is
a hash of the attributes (including defaults) found for that record.

=item * B<hash = xsv.getAllAsHash([names])>

Use I<getNext>() to parse all the records available. Return a hash table that
contains an entry for each record. The attributes (fields) specified in the
I<names> argument (an array), are concatenated in order, separated by '#'
(but see I<setKeySeparator(char)>), to create the hash key (some but not all
of the key fields may be empty). The corresponding value is, as with
I<getAllAsArray>(), a hash of the attributes from the record. Null and
duplicate keys result in an error message, and their records are not added.

B<Note>: A single name may be passed as a string, instead of passing
an array containing one string.

=item * B<hash = xsv.getNext>()

Parse the next record and return a hash of its
named attributes, plus an entry for "#TAG" with the element type of the
tuple. The first one must be I<Head>, and the rest I<Rec>.

=back


==XSV Construction method==

=over

=item * B<xsv.makeXSVRecord(hash)>

Take a hash and make it into an XSV Rec (escaping as needed).
(specifically, as readable by this script).
Attributes are written in the order defined by the C<Head> element.

=back


=for nobody ===================================================================

=head1 Syntax Rules

Except as stated here, XML is implemented unchanged.
All exceptions are by way of I<subsetting>,
so that all Well-Formed XSV is also Well-Formed XML
(thus, you can parse XSV with any full-fledged XML parser; but you can
also parse it with trivial code such as a handful of regular expressions).

An XSV-aware processer will, however, also perform two extra tasks that
a generic XML processer does not include. 1: applying default values
(this could instead be achieved via an XML schema in a schema
language that supports defaults); and
2: checking field values on the enclosed I<Rec> elements
for comformity to a given datatype (on which see below).

=over

=item * A document is not correct XSV unless it is well-formed XML.

=item * The character encoding I<must> be UTF8, and non-XML characters
I<must not> occur.

=item * Only XML declarations,
XML comments, and elements of types "Xsv", "Head", and "Rec" are allowed.
No PIs, markup declarations,
non-whitespace text content (not even entities that resolve to whitespace),
CDATA marked sections, etc.

=item * Each XML declaration, tag, and comment I<must> start on a new line
(leading white space is allowed),
but may be continued onto following lines (line-breaks within tags
may occur exactly where they could in XML).
In other words, a tag or comment may take multiple lines, but
a single line cannot contain part or all of more than one tag or comment.
For example, this in incorrect:

    <Rec a="b" c="d"> <!-- hello -->

but this is correct:

    <Rec a="b" c
    ="d">

    <!-- hello
      -->

Whitespace outside of attribute values is not considered
part of the XSV data content.

Breaking lines within an attribute value is permitted but not recommended.
XSV applications I<may> normalize whitespace in such values,
but are not required to.

B<Note>: This implementation presently fails on encountering ">" at the end of a
line within an attribute value; the workaround for now is to remove the
line-break or use "&gt;".

=item * Within attribute values (only), XML numeric character references,
XML predefined named entity references, and HTML 4 named entity references
may be used. No other entity references are permitted.

=item * Blank lines (containing only whitespace) and comments may occur
anywhere they can occur in XML, except that each comment I<must>
start a new line.
Comments I<may> be discarded or passed to an application.
They do not otherwise affect XSV processing.

=item * XSV data I<should> begin with a comment
whose first line is (a single space after the "<!--" and then) "XSV".

=item * An XSV document I<should> have an outermost element of type "Xsv",
which I<should> have attributes giving information about the nature, author,
version, and source of the XSV data.

The attributes allowed on "Xsv" are:
I<contributor>, I<coverage>, I<creator>, I<date>, I<description>, I<format>,
I<identifier>, I<language>, I<publisher>, I<relation>, I<rights>, I<source>,
I<subject>, I<title>, and I<type>.

These names are from the Dublin Core C</elements/1.1> properties,
and must be used in accordance with the corresponding
definitions (on which see
L<http://dublincore.org/documents/2012/06/14/dcmi-terms/?v=elements#H3>).
No other attributes may be specified on the "Xsv" element.

=item * All child elements of the "Xsv" element I<must> be of type "Head".
A Head is analogous to a single relational table, a CSV file, etc.

=item * A "Head" element I<must> have start and end tags (it may not be
an XML "empty element"),
and I<must> have at least one attribute.
Its attributes serve as declarations for what attributes are permitted
on contained "Rec" elements.

=item * A "Head" element's child elements (if any)
I<must> all be "Rec" elements.

=item * A "Rec" element I<must> use XML empty element form, and must have only
attributes whose names appear as attribute names on the immediately
containing "Head" element. As in XML, the order of attributes is irrelevant.

=item * Attributes on a "Head" I<must> have a value (possibly "").
If such a value begins with "#", then the value up to the next "#" is
a I<datatype specification>. If there is no second "#", the entire value
is taken as the I<datatype specification>.
Any data after the second "#", or the whole value if the value does not
begin with "#", specifies the I<default value> for the like-named attribute.

If a "#" is required with a I<datatype specification>, it can be represented
via a numeric or named character reference such as I<&#x23;>. Thus, XSV
parsers must logically separate the I<datatype specification> from the
I<default value> B<before> expanding character references.

I<All> XSV applications I<must> notice and separate a datatype specification
from a I<default value> in "Head" attribute values whenever it is present.

XSV applications I<may> discard I<datatype specification>s, but
I<should> instead use them to check values for the given attribute name
as defined in the next section.
It is strongly recommended that all XSV implementations at least support
the semantics of the B<BASE> datatype specification; XSV implementations
that do not support BASE, I<must> at least issue a message or warning if
they encounter one.

XSV applications I<must> must return the default value as specified on <Head>,
as the value of the like-named attribute for any and all directly-contained
<Rec> elements which do not specify the like-named attribute at all.
This is true whether or not the default value conforms to the applicable
datatype specification (if any).

B<Note>: If an attribute is specified on a given C<Rec>, with the value
"", then it counts as specified and the default value I<must not> be applied.
Whether the empty string is an allowed value for that attribute is
determined by the applicable datatype prefix (if there is none, then the
value "" is allowed).

=back


=for nobody ===================================================================

==Datatype Specifications==

When "Head" provides a I<datatype specification> for a particular
attribute (as just defined),
it never affects what data is actually expressed by the XSV, except in
the case of "BASE" (see below). Rather, it is for datatype checking
(analogous to XML schemas). For example, the following declaration
ensures that each "Foo" attribute on each contained <Rec> element
contains one or more whitespace-separated integers (cf XSD),
and defines the default value to be "1":

    <Head Foo="#integer+#1">

The next example ensures that "Lunch" attributes contain a single token
either "Spam" or "Eggs", or default to "Spam" if empty. It also
sets a default of "1" for the "NVikings" attribute, without placing any
restrictions on what values may be explicitly specified for "NVikings":

    <Head Lunch="#ENUM(Spam Eggs)#Spam" NVikings="1">

A I<datatype specification> includes, in the order shown:

=over

=item B<< # >> -- the starting delimiter (required)

=item B<< typename >> -- the type name, which I<must> be one of these (see
additional discussion below):

    the XSD built-in datatype names
    ENUM, STRING, ASCII, REGEX, BASEINT
    BASE
    REQUIRED

=item B<< (arg) >> -- an optional argument, enclosed in parentheses.
A few of the datatypes require an argument (BASE, ENUM, and STRING).
Empty parentheses may, however, be specified with any typename.
The argument may never contain "#", even via a numeric character reference
or entity.

=item B<< repetition >> -- an optional single character indicating how
many repetitions of the named datatype I<must> occur (separated by white-space).
Requiring one or more repetitions, however, does not preclude omitting
the attribute so that a default value (if provided) is used.

    "!" or "" (no character) indicates the attribute I<must> have one match.
    "?" indicates the attribute may be empty, or have one match.
    "*" indicates the attribute may be empty, or have any number of matches.
    "+" indicates the attribute I<must> have at least one match.

=item B<< # >> -- the ending delimiter, separating the datatype specification
from the default value.

=item B<< default >> -- the XSV default value (possibly empty).
Defaults I<must not> be applied when an attribute is present and explicitly
set to "".

=back

To specify a default value that begins with "#", put a (possibly empty)
datatype specification in front of it, as in I<myAttr="###FOO">. An
empty datatype specification allows any value.

Permitted "#"-initial values match this (PCRE-style) regex, in which
the last capture group is the default value:

    /^(#)([-\\w]+)(\\([^#]*?\\))([!?*+])?#(.*)$/

All XSV applications I<must> find and apply I<default> values from "Head",
whether they are preceded by a datatype specification or not.

XSV applications I<may> also support datatype checking; if they do then they
I<must> also apply the validation checks defined below
when evaluating the like-named attribute on subsequent <Rec> elements.

The specific behavior upon finding an attribute value (including a default)
that does not match the applicable datatype specification,
is not defined by XSV, but is left to the individual implementation.

XSV applications that do not support datatype checking I<may> ignore, report,
or discard the datatype specifications, so long as they still handle
default values properly.


=for nobody ===================================================================

=head3 Description of supported datatypes

Nearly all the XSV datatypes are taken exactly from C<XSD>
(L<http://www.w3.org/TR/xmlschema-2/>).
Others are named in all caps (see below).

=over

=item * Logical types:
boolean (true, false, 1, or 0, the first two being canonical).

=item * Real number types:
decimal, double, float.

=item * Integer types:
byte, int, short, integer, long,
nonPositiveInteger, negativeInteger, nonNegativeInteger, positiveInteger,
unsignedByte, unsignedShort, unsignedInt, unsignedLong.

=item * Dates and times:
date, dateTime, time, duration, gDay, gMonth, gMonthDay, gYear, gYearMonth.

=item * Strings:
language, normalizedString, string, token.

=item * XML constructs:
NMTOKEN, NMTOKENS, Name, NCName, ENTITY, ENTITIES, QName,
ID, IDREF, IDREFS.
Because XSV supports repetition operators, NMTOKENS, ENTITIES, and
IDREFS are partially redundant (you may specify repeatability either way).

Because XSV does not support DTDs, the types
ENTITY, ENTITIES, ID, IDREF, and IDREFS
are not necessarily distinct from NCName(s).
However, an XSV implementation I<may>
check ID attributes for uniqueness and IDREF/IDREFS for resolvability.

=item * Net constructs:
anyURI, base64Binary, hexBinary.

=back


=head4 Extension datatypes (that is, ones not defined by XSD):

=over

=item * ENUM(I<arg>) -- any member of the whitespace-separated list of tokens
listed (space-separated) in I<arg>. All of the tokens I<must> be XML NAMEs,
and there I<must> be no duplicates in a single ENUM datatype specification.
As with other types, a following repetition indicator I<may> be used.

If the datatype specification allows repetition, then a single attribute value
may even have the I<same> particular token more than once; this has
no special meaning to XSV (though of course it may to callers).

=item * STRING(I<regex>) -- any string conforming to the (PCRE) regular
expression given as I<regex>.
I<regex> I<must not> contain parentheses or "#".
Those character I<may> be included via named or numeric character references.
Of course, the string also I<must not> contain non-XML control characters.

=item * ASCII(I<regex>) -- an ASCII string conforming to the (PCRE) I<regex>.
This works just like I<STRING>, except that only ASCII characters are allowed
in the I<regex> and in a successfully-matching attribute value.

=item * REGEX -- a regular expression (this does I<not> take an
argument, because it means that the values checked must
I<be> (PCRE) regexes, not I<match> a certain regex (see also STRING[regex]).

=item * BASEINT -- an integer in decimal (no leading zeros),
hex (0xF...), or octal (07...) form.
Binary (0b1...) is I<not> allowed. This declaration only affects validation;
the value is I<not> normalized or converted by XSV implementations.

=back

The final datatype is quite special:

BASE(I<string>) -- The I<string> argument must be prefixed to all
non-empty values of the attribute. This is a special case
inspired by the HTML "base" attribute. However, "BASE" can be used whether
the values are URIs, STRINGs, or whatever.
It simply causes a string concatenation (this might be odd with some types,
such as boolean or numeric types, but it is not illegal).
Because this type, like other types, is specified on the declaration for
a particular named attribute, you can have different BASE values for
different named attributes.

"BASE" still allows a normal default value following the argument (thus, the
final value of an attribute whose declaration on Head uses "BASE", and which
is not specified on a given Rec element, is the concatenation of the "BASE"
value with the default (not including the delimiting "#"s).
However, since BASE uses the syntactic position of a datatype name,
one cannot also specify a datatype name, and although one may specify a
repetition character it is not used for anything.



=for nobody ===================================================================

=head1 Related commands

C<testXsv> -- a simple driver that uses this package to parse an XSV file,
and displays the records, record numbers, and fields.

C<XmlTuples.pm> -- Perl version.



=for nobody ===================================================================

=head1 Known bugs and limitations

=over

=item * XSV datatype checking (specified by attributes on <Head>
whose values begin with "#"), is not supported yet.
Such definitions are detected, but do not result in any actual datatype
validation, other than the value "#REQUIRED".

=item * You can't just dive in with C<getAllAsHash>() or  C<getAllAsHash>() yet.
You have to call C<getNext>() first to parse the C<Head> element.

=item * Does not catch all XML well-formedness errors.
For example, a numeric character reference
to a non-XML character such as C<&#5;> or C<&#xDEADBEEF;>.

=item * Slightly too leniant on XML NAMES (such as attribute names).
It accepts all regex C<\\w> characters anywhere in a NAME.

=back



=head1 Related commands

C<XmlTuples.pm> -- Perl version of the same thing.
Almost the same API.

C<StringIO> -- Python package you can use to create a file-like object
from a string (pass one to I<attach>() to use with this package).


=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see L<http://creativecommons.org/licenses/by-sa/3.0/>.

For the most recent version, see L<http://www.derose.net/steve/utilities/>.

=cut
"""
