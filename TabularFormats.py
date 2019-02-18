#!/usr/bin/env python
#
# TabularFormats.py
#
# Written 2010-03-23 by Steven J. DeRose (in Perl).
#
# 2012-01-09f sjd: Start Python port, get to compile.
# 2012-01-20 sjd: Debugging. Integrate sjdUtils.
# 2012-05-07 sjd: Move out Datatypes stuff to separate class.
# 2013-05-29 sjd: Start syncing up w/ Perl version. Add option-handling.
#     Introduce DataCurrent, DataOptions, DataSchema packages.
# 2014-09-06: Drop DataCurrent package, syncing w/ Perl verions.
# 2015-06-04: Get back to porting.... Start real subclasses.
#
# To do:
#     Re-port/sync from much-changed Perl version.
#     Split out format-specific stuff to TFormatSupport.py.
#
#  Packages to use:?
#     CVS       csv, reaader/writer/dialects/sniffer
#     JSON      json
#     ARFF      https://pypi.python.org/pypi/liac-arff
#     COLUMNS
#     MIME      https://docs.python.org/2/library/mimetools.html
#     XSV       *
#     MANCH
#     OWL/XML   https://pypi.python.org/pypi/Owlready
#
#     HTML      bsoup
#     SEXP      https://sexpdata.readthedocs.io/en/latest/
#     PERL
#     PYTHON
#     XML       bsoup?
#
#     (xdr, config, plist,...)
#
from __future__ import print_function
import sys
#import os
#import string
#import math
import re

from sjdUtils import sjdUtils
from alogging import ALogger
from XmlTuples import XmlTuples
#from TFormatSupport import TFormatSupport
# from Datatypes import Datatypes


###############################################################################
###############################################################################
###############################################################################
#
def tfWarn(self, lvl, m1, m2):
    if (self.options[TFverbose]>=lvl):
        sys.stderr.write(m1+m2+"\n")
    return

def tfError(self, lvl, m1, m2):
    if (self.options[TFverbose]>=lvl):
        sys.stderr.write("******* ERROR: "+m1+m2+"\n")
    return

def getLastMessage(self):
    return(self.lastMessage)



###############################################################################
###############################################################################
###############################################################################
#
class FieldDef:
    def __init__(self, name = None, ersatz = 0):
        # Where to find the field (not all always used)
        self.fName       = name            # Field name
        self.fErsatz     = ersatz          # Is it created as error recovery?
        self.fStart      = 0               # Starting column (optional)
        self.fWidth      = 0               # Column width

        # Input processing and cleanup
        self.fDefault    = None           # Value to load if missing (?)
        self.fCharset    = "utf-8"         # Character encoding
        self.fNilValueIn = ""              # Reserved "nil" value
        self.fCallback   = None           # Last-minute callback

        self.fSplitter   = None           # Regex to split() sub-fields
        self.fJoiner     = None           # String to join() sub-fields

        self.fDatatype   = ""              # Datatypes.pm name for checking

        # Output possibilities (see align() below)
        self.fAlign      = ""              # l/c/r/d/a
        self.fNilValueOut= ""              # Write this for None
        return

    # Mainly for COLUMNS, but anybody can use it.
    # Left, Center, Right, Dot, Auto, or "".
    #
    def align(self):
        return



###############################################################################
###############################################################################
###############################################################################
#
class DataSchema:
    def __init__(self):
        return

    def reset(self):
        return

    def setRecover(self):
        return
 # Allow auto-creation of fields?
    def addField(self):
        return
 # All params optional
    def getFieldDef(self):
        return

    def getFieldDefByName(self):
        return

    def getFieldDefByNumber(self):
        return

    def setFieldName(self):
        return

    def getFieldName(self):
        return

    def setFieldDatatype(self):
        return

    def getFieldDatatype(self):
        return

    def setFieldDefault(self):
        return

    def getFieldDefault(self):
        return

    def setFieldSplitter(self):
        return

    def setFieldCallback(self):
        return

    def setNFields(self):
        return

    def getNSchemaFields(self):
        return

    def setFieldNumber(self):
        return

    def getFieldNumber(self):
        return

    def setFieldNamesFromArray(self):
        return

    def getFieldNamesArray(self):
        return

    def setFieldPositions(self):
        return

    def setFieldPosition(self):
        return

    def getFieldPosition(self):
        return

    def setFieldNumbersByPosition(self):
        return

    def getAvailableWidth(self):
        return

    def getNearestFollowingFieldDef(self):
        return




###############################################################################
###############################################################################
###############################################################################
#
class DataSource:
    def __init__(self):
        return

    def open(self):
        return

    def setEncoding(self):
        return

    def attach(self):
        return

    def close(self):
        return

    def rewind(self):
        return

    def seek(self):
        return

    def tell(self):
        return

    def add_text(self):
        return

    def pushback(self):
        return

    def readLine(self):
        return

    def readRealLine(self):
        return

    def readBalanced(self):
        return

    def findCloser(self):
        return

    def readToUnquotedDelim(self):
        return



###############################################################################
###############################################################################
###############################################################################
#
class DataOptions:
    def __init__(self):
        self.optionData = self.defineOptions()
        self.options    = {}
        return

    def defineOptions(self):
        opDefData = [
            # NAME            DATATYPE   DEFAULT   HELP
            ("basicType",   "Name",    "CSV",    'What format to use?' ),
            ("header",      "boolean",  0,       'Is first record a header?'),
            ("xTable",      "Name",    "table",  'Tag to use for HTML table'),
            ("xGroup",       "Name",    "tgroup", 'Tag to use for HTML tgroup'),
            ("xRecord",      "Name",    "tr",     'Tag to use for HTML tr'),
            ("xFNameTo",   r"X-Regex\t\\\class","",'' ),
            ("xField",       "Name",    "td",    'Tag to use for HTML td'),
            ("xHeader",      "Name",    "th",    'Tag to use for HTML th'),
            ("xSubfield",    "Name",    "",      '' ),
            ("xEntWidth",    "int",      5,      'Min digits for char refs.'),
            ("xEntBase",     "int",     16,      'Base 10/16 for char refs.'),
            ("xEntRsv",      "Name",    "",      '' ),
            ("xASCII",       "boolean",  0,      'Escape all non-ASCII.'),
            ("xHtmlNames",   "boolean",  0,      '' ),
            ("xAsElements",  "boolean",  0,      '' ),
            ("tableSep",     "string",   "",     '' ),
            ("groupCount",   "int",      0,      '' ),
            ("groupSep",     "string",   "",     '' ),
            ("recordSep",    "string",   "",     '' ),
            ("fieldSep",     "string",   "\t",   'Field separator/delimiter'),
            ("subfieldSep",  "string",   "",     '' ),
            ("quote",        "string",   "\"",   'What char to use as quote.'),
            ("nlInQuotes",   "boolean",  0,      'Quoted fields may have \\n.'),
            ("qdouble",      "boolean",  0,      'Escape quotes by doubling.'),
            ("escape",       "string",   "",     'Char to use as escape.'),
            ("escape2hex",   "string",   "",     ''),
            ("comment",      "X-Regex",  "#",    'What marks comment lines?'),
            ("stripFields",  "boolean",  0,   'Strip whitespace from fields.'),
            ("stripRecords", "boolean",  0,   'Strip whitespace from records.'),
        ]
        for op in opDefData:
            self.defineOption(op)
        # End defineOptions

    def defineOption(self, name, typ, dft, doc):
        self.options[name] = [ typ, dft, doc ]
        return

    def setOptionsFromHash(self, aHash):
        for opt in (aHash.keys()):
            self.setOption(opt, aHash[opt])
        return(1)

    def getOptionsHash(self):
        return(self.options)

    def getOptionHelps(self):
        helps = {}
        for opt in (self.options.keys()):
            helps[opt] = self.options[opt][2]
        return(helps)

    def readyCheck(self):
        return(True)

    def addOptions(self, ap, prefix=""):
        for opt, typ in (self.optionData.keys().items()):
            if (typ == "boolean"):
                ap.add_argument("-"+opt, action='store_true')
            elif (typ == "Name" or
                typ == "string" or
                typ.startswith("X-Regex")):
                ap.add_argument("-"+opt, type=str, default="")
            elif (typ.startswith("X-Enum")):
                ap.add_argument("-"+opt, type=str, default="")
            elif (typ == "int"):
                ap.add_argument("-"+opt, type=int, default=0)
        # End addTFOptions

    def setOptions(self, argDict): # FIX
        self.setOption("basicType",    argDict.basicType)
        self.setOption("comment",      argDict.comment)
        self.setOption("escape",       argDict.escape)
        self.setOption("fieldSep",     argDict.fieldSep)
        self.setOption("header",       argDict.header)
        self.setOption("nlInQuotes",   argDict.nlInQuotes)
        self.setOption("qdouble",      argDict.qdouble)
        self.setOption("quote",        argDict.quote)
        self.setOption("stripFields",  argDict.stripFields)
        self.setOption("stripRecords", argDict.stripRecords)

    def setOption(self, name, value):
        self.options[name] = value
        return(self.options[name])

    def getOption(self, name):
        return(self.options[name])

    def getOptionType(self, name):
        return(self.optionsInfo[name][0])

    def fixOptionName(self, name):
        if (name == "delim"): return("fieldSep")
        else: return(name)

    def displayOptions(self):
        buf = ""
        for opt in (keys(self.options)):
            buf += opt + ":\t" + self.options[opt]
        return(buf)


    ###########################################################################
    def normalizeBoolean(self, value):
        mat = re.match("(0+|false)",value,"i")
        if (mat): value = 0
        else: value = 1
        return(value)

    def normalizeNumber(self, value):
        return(float(value))

    def normalizeBaseInt(self, value):
        if (re.match(r"0",value)): value = oct(value)
        return(value)

    def normalizeString(self, value):
        value = re.sub(r"\s+"," ",value.strip())
        return(value)





###############################################################################
###############################################################################
###############################################################################
#
class TabularFormats:
    def __init__(self, su=None):
        self.version    = "2015-06-04"
        self.verbose    = 0
        self.quiet      = 0
        self.typeCheck  = 0
        self.expect     = 0        # Enforce # of fields per record?
        self.expectWarn = 0        # Give warning if wrong number of fields?
        self.fieldInfo  = []       # Specifics per field
        self.su         = su or sjdUtils()
        self.options    = {}
        self.defineOptions()

        #self.dtObj      = Datatypes()
        #oFieldsInfo = fieldInfo() # Also used in setOption().
        for o in optionData:
            v = optionData[o]
            if (re.match(r'(X-Enum|X-Regex)\t',v)):
                continue
            if  (0): #dtObj.isKnownDatatype(v)):
                self.su.lg.vMsg(0,"TabularFormats: Unknown datatype '" + v +
                              "' for '" + o + "'.")
        return

    def reset(self):
        return

    def hashToArray(self):
        return
    def parseRecordFromString(self):
        return

    def parsestringtoDOM(self):
        return
    def setHandlers(self):
        return

    def isHandlerName(self):
        return

    def parsefile(self):
        return
    def parsestring(self):
        return

    def parse(self):
        return

    def parse_run(self):
        return

    def saxEvent(self):
        return

    def parse_start(self):
        return

    def pull_start(self):
        return

    def getDataSource(self):
        return

    def open(self):
        return

    def attach(self):
        return

    def close(self):
        return

    def rewind(self):
        return

    def seek(self):
        return

    def tell(self):
        return

    def getDataSchema(self):
        return

    def setRecover(self):
        return

    def getNSchemaFields(self):
        return

    def getFieldNamesArray(self):
        return

    def setFieldNamesFromArray(self):
        return

    def clearFieldValues(self):
        return

    def getNCurrentFields(self):
        return

    def setFieldValue(self):
        return

    def getFieldValue(self):
        return

    def addOptionsToGetoptLongArg(self):
        return

    def isOkFieldName(self):
        return

    def cleanFieldName(self):
        return

    def readAndParseHeader(self):
        return

    def readRecord(self):
        return

    def postProcessFields(self):
        return

    def assembleRecordFromArray(self):
        return

    def assembleField(self, fieldInfoRef, field):
        return

    def assembleComment(self):
        return

    def assembleRecordFromHash(self):
        return

    def assembleHeader(self):
        return

    def assembleTrailer(self):
        return


    def setVerbose(self, n):
        self.verbose = n

    def setQuiet(self, n):
        self.quiet = n


    def setExpectedFields(self, n):
        self.expect = n
        curFields = self.getNFields()
        if (n < curFields):
            self.fieldInfo = self.fieldInfo[0:n+1]
        else:
            for i in (range(curFields,n)):
                fi = fieldInfo()
                self.fieldInfo.append(fi)

    def getExpectedFields(self, n):
        return(self.expect)

    def getNFields(self):
        return(len(self.fieldInfo)-1)


    def addFieldDefinition(self, name):
        newf = FieldInfo()
        newf[fName] = name
        self.fieldInfo.append(newf)
        return(len(self.fieldInfo))


    def setFieldName(self, num, name):
        if (self.checkFieldNumber(num)):
            return(None)
        self.fieldInfo[num].fName = name
        return(len(self.fieldInfo))

    def getFieldName(self, num):
        if (self.checkFieldNumber(num)):
            return(None)
        return(self.fieldInfo[num].fName)


    def setFieldType(self, num, type):
        if (self.checkFieldNumber(num)):
            return(None)
        self.fieldInfo[num].types = type

    def getFieldType(self, num):
        if (self.checkFieldNumber(num)):
            return(None)
        return(self.fieldInfo[num].types)


    def getFieldNumber(self, name):
        if  (not name):
            self.su.lg.vMsg(0,"getFieldNumber: Noneined name returned.")
            return(None)
        num = 1
        while (num<=self.getNFields()):
            theFInfo = self.fieldInfo[num]
            if (not (theFInfo)):
                continue
            if (theFInfo[fName] and theFInfo[fName] == name):
                return(num)
            num = num+1
        return(-1)

    def checkFieldNumber(self, num):
        if (num<=0):
            self.su.lg.vMsg(0,"getFieldType: fields count from 1, not " + num)
            return(0)
        if (num>=len(self.fieldInfo)):
            self.su.lg.vMsg(0,"getFieldName: field " + num + " does not exist.")
            return(0)
        return(1)


    ###########################################################################
    # Option support
    #
    def setOption(self, name, value):
        if (self.verbose):
            self.su.lg.vMsg(0,"setOption: '" + name + "' -> '" + value + "'")
        if (name == "delim"):
            name = "fieldSep"
        theType = self.dataOptions.getOptionType(name)
        if  (not theType):
            self.su.lg.fatal("cvFormat.setOption: Bad option name '" + name + "'")
        if  (not self.dtObj.checkValueForType(theType,value)):
            self.su.lg.fatal("cvFormat.setOption: Bad value '" + value +
                "' for option " +
                "'" + name + "' (type '" + theType)
        self.options[name] = value
        return(value)


    def getOption(self, name):
        if (not self.options[name]):
            self.su.lg.fatal("cvFormat.getOption: Bad option name '" + name + "'")
        return(self.options[name])


    def displayOptions(self):
        return(self.displayOptions())

    # If the caller is using argparse, provide a simple way to add our
    # many options.
    #
    def addOptions(self, ap, prefix=""):
        self.options.addOptions(ap, prefix)

    def setOptions(self, argDict):
        self.options.setOptions(argDict)


    #############################################################################
    #

    # Copy fields from an array to a new array, retrieving them by their 'from'
    # names, and putting them in the order of the 'to' names.
    #
    def copyFieldArrayByName(self, fromData, fromNames, toNames):
        if (fromNames[0] or toNames[0]):
            self.su.lg.fatal("cvFormat.copyFieldArrayByName: Non-empty name[0].")
        toData = ("")
        for f in (range(1,len(toNames))):
            for t in (range(1,len(fromNames))):
                if (fromNames[f] == toNames[t]):
                    toData[t] = fromData[f]
                    break
        return(toData)

    def copyFieldHashToArray(self, fromData, toNames):
        if (toNames[0]):
            self.su.lg.fatal("cvFormat.copyFieldArrayByName: Non-empty name[0].")
        toData = [ "", ]
        for f in (range(1,(len(toNames)-1))):
            x = ""
            if (fromData[toNames[f]]): x = fromData[toNames[f]]
            toData.append(x)
        return(toData)


    ###########################################################################
    #
    def parseHeader(self, raw):
        fieldsRef = self.parseRecord(raw)
        nf = len(fieldsRef)
        self.setExpectedFields(nf)
        if (fieldsRef[0]):
            self.su.lg.fatal("cvFormat.parseHeader: parseRecord returned [0]: '" +
                fieldsRef[0] + "'.")
        arr = [""]
        for i in (range(1,(nf-1))):
            self.setFieldName(i,fieldsRef[i])
            arr.append, fieldsRef[i]
        return(arr)

    def parseHeaderToHash(self, raw):
        fs = self.parseHeader(raw)
        fhash = {}
        for i in (range(1,len(fs)-1)):
            fhash[fs[i]] = i
        return(fhash)


    def setFieldNames(self,nameArray):
        nf = len(nameArray)
        for i in (range(1,(nf-1))):
            self.setFieldName(i,nameArray[i])



    ###########################################################################
    #
    def readRecordToHash(self, fh):
        rec = self.readRecordAndDoNothing(fh)
        if (not (rec)):
            return(None)
        fields = self.parseRecordToHash(rec)
        return(fields)

    def readRecordToArray(self, fh):
        rec = self.readRecordAndDoNothing(fh)
        if (not (rec)):
            return(None)
        fields = self.parseRecordToArray(rec)
        return(fields)


    # Need to use this iff nlInQuotes or groupCount or groupSep is on,
    # because then a logical record may consist of multiple physical records.
    # How to signal the error if we get imbalance without nlInQuotes?
    #
    def readRecordAndDoNothing(self, fh):
        fullRec = ""
        rec = self.readToBalancedQuotes(fh)
        if  (not (rec)):
            return(None)
        # If we're doing record-groups (unusual), read some more...
        if (self.options["groupCount"]>1): # ?
            nPhysical=1
            while ((nPhysical<self.options["groupCount"])):
                fullRec = fullRec + self.options["fieldSep"] + rec
                rec = self.readToBalancedQuotes(fh)
                nPhysical = nPhysical + 1
        elif (self.options["groupSep"] != ""):
            nPhysical = 1
            while (not re.match(self.options["groupSep"], rec)):
                fullRec += self.options["fieldSep"] + rec
                nPhysical = nPhysical + 1
                rec = self.readToBalancedQuotes(fh)
        else:
            fullRec = rec
        return(fullRec)


    def readToBalancedQuotes(self, fh):
        rec = fh.readline()
        if  (not rec):
            return(None)
        nextPart = ""
        nParts = 1
        while (not self.areQuotesUnbalanced(rec)):
            nParts = nParts + 1
            if  (not self.options["nlInQuotes"]):
                self.su.lg.vMsg(0,"Unbalanced quotes, and nlInQuotes is off: " +
                    self.su.showControls(rec))
                #return(rec)
            nextPart = fh.readline()
            if (not nextPart):
                self.su.lg.vMsg(0,"Unbalanced quotes at EOF.")
            rec += nextPart
        rec = rec.strip("\r")
        if (self.options["stripRecords"]):
            rec = rec.lstrip().rstrip()
        return(rec)

    # Check whether a buffer has an even number of unescaped quotes. This gives
    # the generous interpretation that a field like ||"abc\""def"ghi"|| is ok.
    #
    def areQuotesUnbalanced(self, rec):
        if (not (rec)):
            return(1)
        copy = rec
        e = self.options["escape"]
        q = self.options["quote"]
        if (self.options["qdouble"]):
            copy = re.sub(q+q,"",copy)
        if (e):
            copy = re.sub(e+q,"",copy)
        copy = re.sub(r'[^' + q + r']', "", copy)
        #self.su.lg.vMsg(0,length(copy) + " quotes(q) from : 'rec' => 'copy'")
        if (len(copy) % 2):
            return(0)
        return(1)


    ###########################################################################
    # Given a string (generally a record), parse it according to the input spec
    # in effect, and hand back a hash, or an array of fields ([0] is always "").
    #
    def parseRecordToHash(self, raw):
        aRef = self.parseRecord(raw)
        theHash = {}
        for i in (range(1,len(aRef)-1)):
            theHash[self.getFieldName(i)] = aRef[i]
        return(theHash)


    def parseRecordToArray(self, raw):
        return(self.parseRecord(raw))


    def parseRecord(self, raw):
        aRef = None
        if  (not raw or raw.lstrip() == ""):
            return(None)
        if (self.options["comment"] and re.search(self.options["comment"],raw)):
            return(None)
        raw = re.sub("[\n\r]+", " ", raw)
        if (self.options["stripStart"]):
            raw = raw.lstrip()
        bt = self.options["basicType"]
        if (bt == "CSV"):
            if ((self.options["quote"]  and re.search(self.options["quote"],raw)) or
                (self.options["escape"] and re.search(self.options["escape"],raw))):
                aRef = self.parseCsvRecord2(raw)
            else: # Trivial, so use faster method
                fields = re.split(self.options["fieldSep"],raw)
                fields.insert(0,"")
                aRef = fields
        elif (bt == "XML"):
            aRef = self.parseXmlRecord(raw)
        elif (bt == "ARFF"):
            aRef = self.parseArffRecord(raw)
        else:
            self.su.lg.fatal(
                "cvFormat.parseRecord: unknown basic input type '" + bt + "'.")

            # Strip whitespace from all fields if requested
            #
            if (self.options["stripFields"]):
                for i in (range(1,(len(aRef)-1))):
                    aRef[i] = aRef[i].lstrip().rstrip()

            # Save fields, and verify number of fields
            #
            ex = self.expect
            if (ex>0 and self.getNCurrentFields() != ex):
                if (self.expectWarn):
                    self.su.lg.vMsg(
                        0,"\nparseRecord: Expected " + ex + " fields, but found " +
                        self.getNCurrentFields() + " from:\n    " + raw)
            return(aRef)


# Used by regexes below
def hexFunction(mat):
    return(int(mat.group(),16))
def octalFunction(mat):
    return(int(mat.group(),8))
def unescape(self, f):
    iFmt = self.options
    e = iFmt["escape"]
    f = re.sub(e+"n", "\n", f)
    f = re.sub(e+"r", "\r", f)
    f = re.sub(e+"t", "\t", f)
    f = re.sub(e+"f", "\f", f)
    if (iFmt["escape2hex"]):
        f = re.sub(r'e([0-9a-fA-F][0-9a-fA-F])', hexFunction, f)
    if (iFmt["escapeOctal"]):
        f = re.sub(e+r'([0-7][0-7][0-7])', octalFunction, f)
    f = re.sub(e+e, e, f)
    if (iFmt["stripFields"]):
        f = f.lstrip().rstrip()
    return(f)


###########################################################################
###########################################################################
#
class TabularXML(TabularFormats):
    """XML (tabular)
    #
    # Very rudimentary so far. Makes a new field every time it sees an end tag.
    # Probably should do so on start or end, but not twice if it sees end/start.
    # Should learn about HTML entities, and maybe learn to stop at the record-tag.
    # (just switch to a real parser....)
    """
    def __init__(self, **kwargs):
        TabularFormats.__init__(self, **kwargs)

    def parseXmlRecord(self, raw):
        fields = ("")
        fbuf = ""
        inQuote = 0
        i = 0

        while ((raw)):
            if (i > self.expect):
                self.su.lg.vMsg(0,"\nparseXmlRecord: too many fields -- ignored.")
                break

            if (re.match(r'<?',raw)):             # PI
                raw = re.sub(r'<\?.*?\?>',"",raw)
            elif (re.match(r'<!--',raw)):         # COMMENT
                raw = re.sub(r'<!--.*?-->',"",raw)
            elif (re.match(r'<!\[CDATA\[',raw)):  # MS
                raw = re.sub(r'^<!\[CDATA\[.*?]]>',"",raw)
            elif (re.match(r'<!',raw)):           # DCL
                raw = re.sub(r'^<!.*?>',"",raw)
            elif (re.match(r'&#',raw)):           # Ent Ref
                mat = re.match(r'^&#(x?)([0-9a-f]+);',raw)
                code = 26 # ASCII SUB
                if (mat.group(2)):
                    code = mat.group(2)
                if (mat.group(1)):
                    code = fromhex(code)
                fbuf = fbuf + unichr(code)
                raw = raw[len(mat.group(2)+mat.group(1))]
            elif (re.match(r'</',raw)):             # End tag
                mat = re.match(r'^</(\w+)\s*>',raw)
                if (mat.group(1) and mat.group(1) == self.options["recordSep"]):
                    break
                fields.append(fbuf)
                raw = raw[len(mat.group(1))]
                fbuf = ""
            elif (re.match(r'<',raw)):              # Start tag
                raw = re.sub(r'^<(.*)/?>',"",raw)
            else:                                   # Text
                raw = re.sub(r'^([^<&]+)',"",raw)
                fbuf = fbuf + mat.group(1)

        if (fbuf):
            fields.append(fbuf)
            fbuf = ""

        ex = self.expect
        if (ex>0 and self.getNCurrentFields() != ex):
            if (self.expectWarn):
                self.su.lg.vMsg(
                    0,"\nparseXmlRecord: Expected " + ex + " fields, not " +
                    self.getNCurrentFields() + " in:\n    " + raw)
        return(fields)


    ###########################################################################
    #
    def assembleHeader(self):
        fields = []
        if (self.verbose):
            self.su.lg.vMsg(0,"In assembleHeader")

        for i in (range(1,(len(self.fieldInfo)))):
            name = self.fieldInfo[i].fName
            if (not name):
                name = "Field_" + str(i)
            fields.append(name)
        if (self.verbose):
            self.su.lg.vMsg(0, "Header:\n    '" + "'\n    '".join(fields) + "'")
        self.su.lg.vMsg(0,"TabularFormats: calling assembleRecord (returning " +
            fields + "):")
        buf = self.assembleRecord(fields)
        return(buf)

    def assembleRecordFromHash(self, fieldHashRef):
        fieldData = []
        for fi in self.fieldInfo:
            fieldData.append(fieldHashRef.fName)
        return(self.assembleRecord(fieldData))

    def assembleRecord(self, fields):
        self.su.lg.error("Virtual method")
        return(None)

    def assembleField(self, fieldInfoRef, field):
        self.su.lg.error("Virtual method")
        return(None)



###########################################################################
###########################################################################
#
# Implementations of specific formats follow.
#
###########################################################################
###########################################################################


###############################################################################
###############################################################################
#
class TabularARFF(TabularFormats):
    """ARFF (used for input to WEKA NLP system)
    # See http://www.cs.waikato.ac.nz/~ml/weka/arff.html
    # Doc says carriage returns, but I think WEKA really doesn't care.
    # Doc doesn't say what happens if a comma or CR is needed.
    """
    def __init__(self, **kwargs):
        TabularFormats.__init__(self, **kwargs)

    def parseRecord(self):
        self.su.lg.fatal("cvFormat.parseArffRecord: ARFF not yet supported.")

    def assembleArffRelation(self, relationName):
        cr = "\r"
        self.su.lg.vMsg(0,"assembleArffRelation is unfinished.")
        buf = "\\RELATION relationNamecr"
        for i in (range(1,len(self.fieldInfo))):
            fiRef = self.fieldInfo[i]
            f = fiRef.fName
            if (re.search(r'\s',f)):
                f = '"' + f + '"'
            buf += "\\ATTRIBUTE %-24s %s"+cr.format(fiRef.fName, fiRef[fDataType])
        return(buf+cr)

    def assembleRecord(self):
        self.su.lg.vMsg(0,"assembleArffRecord is unfinished.")
        buf = ""
        for i in (range(1,len(self.fieldInfo))):
            fiRef = self.fieldInfo[i]
            f = fiRef.fName
            if (re.search(r'\s',f)):
                f = '"' + f + '"'
            buf += self.assembleField(fiRef,self.fieldInfo[i]) + ","
        buf = re.sub(",", "", buf)
        return(buf)

    def assembleField(self, fieldInfoRef, fieldValue):
        if (not fieldValue):
            return("?") # Reserved 'missing value'
        if (re.search(r'[,\s]',fieldValue)):
            fieldValue = "'" + fieldValue + "'"
        return(fieldValue)



###############################################################################
###############################################################################
#
class TabularCSV(TabularFormats):
    """Parse a CSV record into an array of fields ([0] empty). However, if the
    # record has no quote or escape characters (including when none are defined),
    # the caller just does a split() instead.
    #
    # Probable bug: escape and qdouble together.
    """
    def __init__(self, **kwargs):
        self.basicType = "CSV"
        TabularFormats.__init__(self, **kwargs)


    def parseRecord2(self, raw):  # CSV
        fields   = [ "", ]
        iFmt     = self.options
        fieldSep = iFmt["fieldSep"]
        escape   = iFmt["escape"]
        quote    = iFmt["quote"]
        qdouble  = iFmt["qdouble"]

        # Matches a quoted value including embedded escaped quotes
        # (move this calculation into setOption to save time?)
        qexpr = "^" + quote + "(([^" + escape + quote + "]"
        if (qdouble):
            qexpr = qexpr + quote + quote
        if (escape):
            qexpr = qexpr + escape + quote
        qexpr = qexpr + ")+)" + quote + fieldSep
        raw = raw + fieldSep

        # Parse off a field on each iteration, including the following sep.
        while ((raw)):
            if (iFmt["stripFields"]):
                raw = raw.lstrip()
            f = ""
            if (re.match(fieldSep,raw)):                          # Empty field:
                pass
                #self.su.lg.vMsg(0,"  nil")
            elif (quote and re.match(                             # "" field
                   quote+quote+r'\s*'+fieldSep,raw)):
                pass
                #self.su.lg.vMsg(0,"  \"\"")
            elif (quote and re.match(quote,raw)):                 # quoted
                mat = re.match(qexpr,raw)
                if (mat):                                         # ok quote
                    f = mat.group(1)
                    raw = raw[len(f):]
                    if (qdouble): # ???
                        f = re.sub(quote+quote,quote,f)
                    #self.su.lg.vMsg(0,"  qouted(f)")
                else:                                             # Quote error
                    mat = re.match(quote+"(.*?)"+fieldSep,raw)
                    f = mat.group(1)
                    raw = raw[len(f):]
                    #self.su.lg.vMsg(0,"Quote error in field " + scalar(@fields) .
                    #    ": '" + self.su.showControls(raw) + "'.")   # quoted
            elif (escape):                                       # Unquoted field
                mat = re.match("(.*?[^"+escape+"])"+fieldSep,raw)
                f = mat.group(1)
                raw = raw[len(f):]
                #self.su.lg.vMsg(0,"  noEscape("+f+")")
            else:                                                 # simple
                mat = re.match(r'(.+?)'+fieldSep,raw)
                f = mat.group(1)
                raw = raw[len(f):]
                #self.su.lg.vMsg(0,"  plain(f)")
            if (escape):
                # ???
                f = unescape(f) # ???
            #self.su.lg.vMsg(0,"    Field " + scalar(@fields) + ": 'f'")
            fields.append(f)
        return(fields)

    def assembleRecord(self, fields):  # CSV
        #my @fields = @fieldsRef
        nFields = len(fields)
        of = self.options

        exp = self.expect
        if (exp>0 and nFields != exp):
            if (self.expectWarn):
                self.su.lg.vMsg(0,"assembleCsvRecord: Expected " + exp +
                     "fields, but found " + nFields + ".")
        fsep = of[fieldSep]
        rsep = of[recordSep]
        buf = ""
        if (self.fieldOrder): # reordered:
            self.su.lg.fatal("cvFormat.assembleCsvRecord: field ordering:.")
            nFields = len(self.fieldOrder)
            for i in (range(0,nFields)):
                i2 = self.fieldOrder[i]
                f = of.assembleCsvField(self.fieldInfo,fields[i2])
                buf += f + fsep
        else:                                               # normal order
            for i in (range(0,nFields)):
                f = of.assembleCsvField(self.fieldInfo,fields[i])
                if (self.verbose):
                    self.su.lg.vMsg(0,"  " + i + ": '" + f + "'")
                if (f):
                    buf += f + fsep
                elif (self.verbose):
                    self.su.lg.vMsg(0,"assembleCsvRecord->assembleCsvField, None.")
        buf = re.sub(fsep,rsep,buf)
        return(buf)

    def assembleField(self, fieldInfoRef, field):  # CSV
        if (not field):
            self.su.lg.vMsg(0,"Noneined field in assembleCsvField.")
            return
        esc = self.options["escape"]
        quo = self.options["quote"]
        if (self.verbose):
            self.su.lg.vMsg(0,
            "Escape 'esc' (" + ord(esc) + "), quote 'quo' (" + ord(quo) + ")")
        if (esc):
            field = re.sub(esc, esc+esc, field)
            field = re.sub(self.options["fieldSep"], esc+self.options["fieldSep"], field)
            field = re.sub(quo, esc+quo, field)
        elif (quo and self.options["qdouble"]):
            field = re.sub(quo, quo+quo, field)
        if (esc and not self.options["nlInQuotes"]):
            field = re.sub("(\r\n\r\n)", esc+'n', field)
        qChar = self.shouldQuote(field) # null if no need to quote
        return(qChar+field+qChar)

    def shouldQuote(self, field):
        nqExpr = self.noQuote
        if (re.search(nqExpr,field)):
            return("")
        return(self.quote)



###############################################################################
###############################################################################
#
class TabularFIXED(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "FIXED"
        TabularFormats.__init__(self, **kwargs)



###############################################################################
###############################################################################
#
class TabularJSON(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "JSON"
        TabularFormats.__init__(self, **kwargs)




###############################################################################
###############################################################################
#
class TabularMIME(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "MIME"
        TabularFormats.__init__(self, **kwargs)




###############################################################################
###############################################################################
#
class TabularMANCH(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "MANCH"
        TabularFormats.__init__(self, **kwargs)




###############################################################################
###############################################################################
#
class TabularSEXP(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "SEXP"
        TabularFormats.__init__(self, **kwargs)





###############################################################################
###############################################################################
#
class TabularXML(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "XML"
        TabularFormats.__init__(self, **kwargs)

    def assembleRecord(self, fields):  # XML
        #my @fields = @fieldsRef
        of = self.options
        nFields = len(fields)
        exp = self.expect
        if (exp>0 and nFields != exp):
            if (self.expectWarn):
                self.su.lg.vMsg(0,"assembleXmlRecord: Expected " + exp +
                     " fields, but found " + nFields + ".")
        tr = of["xRecord"]
        #td = of["xField"]
        buf = "<%s>" % (tr)
        for i in (1,range(nFields)):
            buf += of.assembleXmlField(fields[i])
        buf += "</%s>\n" % (tr)
        return(buf)

    def assembleField(self, fieldInfoRef, s):  # XML
        if (self.options["xAsElements"]):
            buf = "<%s>%s</%s>" % (self.options["xField"],
                self.su.escapeXml(s), self.options["xField"])
        else:
            buf = " %s=\"%s\"" % (self.options["xField"],
                self.su.escapeXmlAttribute(s))
        return(buf)



###############################################################################
###############################################################################
#
class TabularXSV(TabularFormats):
    def __init__(self, **kwargs):
        self.basicType = "XSV"
        TabularFormats.__init__(self, **kwargs)

    def assembleRecord(self, fields):  # XSV
        #my @fields = @fieldsRef
        of = self.options
        nFields = len(fields)
        exp = self.expect
        if (exp>0 and nFields != exp):
            if (self.expectWarn):
                self.su.lg.vMsg(0,
                "assembleXsvRecord: Expected "+exp+" fields, but found "+nFields)
        tr = of["xRecord"]
        td = of["xField"]
        buf = "<%s" % (tr)
        for i in (range(0,nFields)):
            buf += (" " + self.fieldInfo.fName +
                "=\"" + self.su.escapeXmlAttribute(fields[i]) + "\"")
        buf += " />\n"
        return(buf)




###############################################################################
###############################################################################
###############################################################################
# This package is just to help organize per-field type/layout information.
# No real methods, just access it directly.
#
class fieldInfo:
    def __init__(self, fName=""):
        # Field order is part of record, not field.
        self.fName      = fName
        self.fWidth     = 0
        self.fAlign     = "L"
        self.fNilValue  = ""
        self.fNormalize = 0
        self.fActive    = 1
        self.fDatatype  = ""
        self.fBase      = 10
        self.fMin       = None
        self.fMax       = None
        self.fExpr      = ""




###############################################################################
###############################################################################
###############################################################################
#

perldoc = """

=pod

=head1 Usage

import TabularFormats

B<***UNFINISHED***>

Provide parsing for record-oriented, delimited files
(tab- or comma-delimited files, tabular-style XML data, etc.

Much more flexible than typical *nix tools such as C<cut>, which can't
deal with quoted fields, quotes in quoted fields, XML, Unicode, etc.

You can instantiate one of these, set options for the input file's layout,
and use it to parse records, returning an array or hash of fields.

You can instead or in addition, instantiate one of these to turn arrays or
hashes of fields, into output records in some format.

For example, there are options to:

=over

=item * change the delimiters (including using regexes),

=item * determine when and how to quote fields,

=item * determine when and how to escape characters,

=item * manage Unicode and some other character encodings,

=item * allow line-breaks within quoted fields (like MS Office(tm)),

=item * learn field names from the first record,
and then refer to fields by name or number.

=item * input or output XML with one element per field (like HTML tables),
or one element per record and one attribute per field.

=item * input or output ARFF files as used by the WEKA machine-learning tool.

=back

It can not only parse a wide variety of formats, but also assemble a variety.
Thus it's easy to build useful converters on top of this.

It has some support for groups of records, and for delimited portions of
fields (such as punctuated keyword-lists in a field,
paragraphs within HTML table cells, etc.).

B<Note>: Fields always count from 1, not zero.
When arrays are handled, element [0] is always the empty string.
This is consistent with the way most *nix tools count fields.
Methods complain if you ask them to do something with field [0].

B<Note>: There is no support for fixed-width fields or for box-drawing.
See the C<align> utility for some help with those.



=head1 Example

    import TabularFormats

    tf = TabularFormats()
    tf.setOption("delim", ",")
    tf.setOption("quote", "\\"")
    tf.setOption("header", 1)
    tf.setOption("stripFields", 1)

    F = open("mypath")
    headerRecord = F.readline()
    fieldNamesRef = tf.parseHeader(headerRecord)

    rec = F.readline()
    while (rec):
        tf.parseRecord(rec)
        print sprintf("%-20s %-20s\\n",
                      tf.getField("name"),
                      tf.getField("id"))
        rec = F.readline()
    F.close()



=head1 Methods and Options

=head2 Methods for basic setup

=over

=item * B<setVerbose>()

Provide extra information messages.

=item * B<setQuiet>()

Supress various warning messages.

=item * B<setExpectedFields(n)>

Say how many fields should normally be present per record. This enables
various checks and warnings.

=item * B<getExpectedFields>()

Return the number of fields set by I<setExpectedFields(n)>.

=item * B<addFieldDefinition(name)>

Append a field to the list of known fields. Returns the number of fields
defined so far (including the new one).

=item * B<setFieldNames(@namesRef)>

Change the names of all the fields (just shorthand for I<setFieldName>() for
each name listed in I<@namesRef>.

=item * B<setFieldName(num, name)>

Change the name of field number I<num> (always counting from 1).

=item * B<getFieldName(num)>

Return the name of field number I<num> (always counting from 1).

=item * B<setFieldType(num)>

=item * B<getFieldType(num)>

=item * B<getFieldNumber(name)>

Return the field number corresponding to the given I<name>, or -1 if there
is no such field.

=item * B<getNCurrentFields>()

=item * B<getNSchemaFields>()

Distinct, but not yet implemented....

=back


=head2 Methods for changing input and output formats

=over

=item * B<setOption(name, value)>

(see next section for details)

=item * B<getOption(name)>

(see next section for details)

=back



=head3 Options for setOptions()

Using an unknown option name will fail,
but checking on the values assigned is incomplete.
The type for each option, is:
Boolean if the default value is shown as 1 or 0 below and the description
ends with "?",
an enum if several literal values are listed, and
string if a quoted string is shown.

=over

=item * B<basicType>

"CSV"
Depending on this setting, only some of the other settings will apply.
Known basic types are:

=over

B<ARFF> uses the form for the C<WEKA> tookit.

B<CSV> offers a huge variety of field separator, delimiter, and other options

B<XML> uses table markup (HTML-style by default)

B<XSV> uses the form of C<xmlTuples>. For example:

    <Rec Name="Joe" Age="21".../>\\n

B<MIME> uses MIME header form (but is not yet implemented),
with I<label:>-prefixed fields (with continuation lines indented), and
a blank line (only) before each entire record. For example:

    Name: Alexander
       the Great
    Nationality: Greek

=back

=item * B<verbose>      0       # Show more trace information?

=back


=head3 Options for CSV formats

=over

=item * B<recordSep>    "\\n"    # Record separator

=item * B<fieldSep>     "\\t"    # Field separator (also synonym "delim")

=item * B<delim>        "\\t"    # Synonym for I<fieldSep>

=item * B<header>     0,        # Is (record 1) a header with field names?

=item * B<escape>       "\\\\"    # Char used to escape other chars?

=item * B<quote>        "\\""    # Use to quote nonalphanumeric fields

=item * B<qdouble>      0       # Escape embedded quotes by doubling them?
This only applies to the I<quote> character. If I<escape> is also set,
it takes precedence over I<qdouble>.

=item * B<nlInQuotes>    0       # Allow newline in quotes?
B<Note>: With this option, you'll need to read records via one of the
I<read...> calls provided in this package (see below).
Using normal reads will of course not get
the multiple physical records that make up one logical record.
Mixing this option with groupCount or groupSep is not recommended.

=item * B<comment>      "^#"    # Ignore matching records as comments

=item * B<stripFields>  1       # Discard leading/trailing space on fields?

=item * B<stripRecords> 1       # Discard leading/trailing space on records?


=item * B<tableSep>     ""      # Start a whole new table on seeing this

=item * B<groupCount>    0      # Logical records include
a constant number of physical records.
(not yet supported).

=item * B<groupSep>     ""      # Logical records include multiple
physical records, separated by
regex-recognizable separator records (say, /^\\s+$/ or /^#/)
that do not include data (not yet supported).

=item * B<subfieldSep>  ""      # Sub-field separator (normally none).
Not yet supported. This will eventually support treating the
lines/paragraphs within an HTML or similar table cell, as separate fields.

=item * B<noQuote>  "^\\d+\\$"    # Do I<not> quote fields that
match this regex; quote all others.

=item * B<escape2hex>   ""      # Char used to mark hex-escapes,
such as "%" for URI-style escapes.

=item * B<escapeMap>            # What sequences are supported for
special characters (not currently settable). Default includes \\n, \\r, \\0,
\\f. (unfinished)

=back


=head3 Options for XML formats

=over

=item * B<xTable>     "table"   # Element types to use

=item * B<xGroup>     "tgroup"  # (unused)

=item * B<xRecord>

"tr"

=item * B<xFNameTo>   "@class"  # Where to put field names (@xyz or <>)

=item * B<xField>     "td"      # Element name for fields unless xFNameTo="<>"

=item * B<xHeader>    "th"      # (unused)

=item * B<xSubfield>  "p"       # (subfields are not yet supported)

=item * B<xEntWidth>  5         # Min width for numeric char references

=item * B<xEntBase>   16        # Base 10 or 16?

=item * B<xEntRsv>    "NAME"    # NAME: Use 5 builtin named entitites
or NUM: just numbers

=item * B<xASCII>     0         # Use character references for all chars > 127?

=item * B<xHtmlNames> 0         # Use HTML entity names when applicable?

=back



=head2 Methods for operating on actual records

=over

=item * B<copyFieldArrayByName>(I<fromData, fromNames, toNames>)

Copy field from the data array referenced by I<fromData>, to a string record
that is returned. The fields are copied in the order specified in
the array referenced by I<toNames>.
(unfinished; probably I<fromNames> is not needed, and I<toNames> should be
allowed to be just another TabularFormats object, which knows its names.


=item * B<parseHeader(s)>

This is essentially the same as
I<parseRecord>(), except that the values parsed out are also used to set up an
internal list of field-names, that can then be used to refer to fields more
mnemonically than using numbers. A reference to an array of the names is
returned. The 0th entry is not a field name (fields always count from 1).


=item * B<parseRecord>(s)

Take a string (with or without a record
separator on the end), and parse it into an array of fields.
Return a reference to the array, or None if the record return
passed is a comment.
Field [0] is set to the null string, because fields are conventionally
numbered from 1 and it's easier to avoid the off-by-one correction.
If subfields are in use, nothing happens to them, they just stay there
(embedded in their fields).

=item * B<parseRecordToArray>(s)

Synonym for I<parseRecord>(s).

=item * B<parseRecordToHash>(s)

Like I<parseRecord>(), but returns
a reference to a hash, where each field is stored under its name.

=item * B<readRecordAndDoNothing>(I<fh>)

Read a record from file I<fh> and return it.
This or another I<read...> call should be used if
the I<--nlInQuotes> option is in effect, because in such cases any number of
physical (newline-separated) records may have to be read, in order to
gather one complete logical record. If you do not use the I<read...> calls
provided for such cases, you must either code the equivalent functionality
in your application, or put up with erroneous interpretation of the input.

=item * B<readRecordToArray>(I<fh>)

Read a record from file I<fh> and parse it (according to the current format
options). Put the fields into a new array, and return a reference to it.

=item * B<readRecordToHash>(I<fh>)

Read a record from file I<fh> and parse it (according to the current format
options). Put the fields into a hash by name, and return a reference to it.


=item * B<assembleHeader(arrayRef)>

Like I<assembleRecord>.

=item * B<assembleRecordFromHash(hashRef)>

Like I<assembleRecord>, but goes through the known fields inorder (which
must each include a fieldName), and retrieves each field's value by name
from the hash at I<hashRef>, rather than getting them from an array.

=item * B<assembleRecord(arrayRef)>

Take an array of fields (for example as
produced by I<parseRecord>(), and assemble them into a string according to
the format specifications. This may assemble a CSV record, an XML element
for the record (with either sub-elements or attributes per field),
or an ARFF record.

=item * B<assembleRecordFromHash(hashRef)>

Like I<assembleRecord>, but gets the fields by name from a hash
instead of from an array. It puts them in the order learned
from parseHeader() or from calls to
I<addFieldDefinition()>, I<setFieldNames()>, and/or I<setFieldName()>.

=item * B<assembleArffRelation>(I<name>)

Put together the "@relation declaration" for an ARFF file (see
L<http://www.cs.waikato.ac.nz/~ml/weka/arff.html>).
This just lists each field and its datatype, in order.
The datatype names are not yet normalized.
The names known to ARFF are I<numeric>, I<{ val1, val2,...}>,
I<string>, I<date> (various forms).

=item * B<assembleArffRecord>()

Assemble the current data ito an ARFF data record (basically a comma-separated
record with quoting).

=item * B<assembleArffField>()

Return the data in the given field, quoted if there are any spaces.
Also quotes the field if there are any commas, although doc I've found re ARFF
doesn't specify what to do in that case.

=back



=head1 Related commands

C<TabularFormats> -- Original (Perl) version of this package.

=back



=head1 Known bugs and limitations

=over

=item * Unfinished.

=item * Not yet integrated with Datatypes.py.

=item * Little subfield or record-group support.

=item * Formats unfinished (cf Perl version):
ARFF (for C<WEKA>),
JSON,
MIME header,
Manchester OWL/RDF support (see I<xml2tab>),
SEXP.

=item * The behavior if using regexes rather than strings for I<delim>,
I<quote>, I<comment>, etc., is Noneined.
Most likely it will work ok for input, but not for output.


=back



=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see http://creativecommons.org/licenses/by-sa/3.0/.

For the most recent version, see http://www.derose.net/steve/utilities/.

=cut
"""
