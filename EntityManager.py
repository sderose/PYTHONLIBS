#!/usr/bin/env python
#
# EntityManager.py
#
# Broken out from multiXML.py, 2013-02-25.
# multiXml written 2011-03-11 by Steven J. DeRose.
# 2015-09-19: Close to real, syntax ok, talks to multiXML.py.
#
# To do:
#     Get it running.
#     Get rid of sys.stderr.write()s.
#
import sys
import os
#import string
import re

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    import HTMLParser
    string_types = basestring
else:
    from html.parser import HTMLParser
    string_types = str
    def unichr(n): return chr(n)

from sjdUtils import sjdUtils  # Only uses lg and isXmlChar
#from alogging import ALogger


###############################################################################
###############################################################################
#
class EntityManager:
    """Manage an entity dictionary, and a stack of open entities.
    This is used for entities
    that map to file or URI objects; entities that are just declared as
    strings, and character references, are handled inline rather than here (?).
    """
    builtins = {
      'lt':   '<',
      'gt':   '>',
      'amp':  '&',
      'apos': "'",
      'quot': '"',
    }
    htmlparser = HTMLParser.HTMLParser() # For entity decoding


    def __init__(self, su=None):
        self.su = su or sjdUtils()
        self.entPath    = []    # dirs to look in
        self.entDefs    = {}    # internal and external
        self.entStack   = []    # open entities
        self.totLine    = 0     # overall lines processed
        self.totChar    = 0     # overall chars processed
        self.eventQueue = []    # Pending events

    def appendEntityPath(self,path):
        if (not os.path.isdir(path)):
            sys.stderr.write("appendEntityPath: path 'path' not a directory.")
        self.entPath += path

    def addEntity(self,ename,isParam,aType,value,pubid,sydid,notation):
        mat = re.search("^(LITERALPUBLICSYSTEM)",type)
        if (not mat):
            print("Bad entity type '"+aType+"' in addEntity!")
            exit(0)
        if (not notation):
            notation = ""
        if (isParam):
            ename = "%ename"
        self.entDefs[ename] = (aType, value, pubid, sydid, notation)

    def getDepth(self):
        return(len(self.entStack))

    def pushEvent(self, typ, msg):
        self.eventQueue.append((type, msg))


    # Only SYSTEM ids are presently used, and there's no catalog support.
    #
    def openParameterEntity(self, ename):
        self.openEntity("ename")


    def openEntity(self, ename):
        self.su.lg.vMsg(0,"Opening entity 'ename'.")
        entSpecsRef = self.entDefs[ename]
        if (not entSpecsRef):
            self.pushEvent("ERROR","WF: Entity '"+ename+"' is unknown.")
            return(0)
        (aType, value, pubid, sysid, notation) = entSpecsRef
        for i in (range(0, self.getDepth())):
            if (self.entStack[i].oeName == ename):
                self.pushEvent(
                     "ERROR","WF: Recursive reference to entity '"+ename+"'.")
                return(0)
        gotit = 0
        mat = re.search("^(https?|ftp|file|local):",sysid)
        if (mat):
            print("URIs are not yet supported.")
            exit(0)
        for d in (range(0, len(self.entPath))):
            candidate = os.path.join(self.entPath[d], sysid)
            if (os.path.isfile(candidate)):
                gotit = 1
                break
        if (not gotit):
            sys.stderr.write("Entity '"+ename+"' not found, referenced from:")
            print(self.wholeLoc())
            return(0)
        FILE = open(candidate,"r")
        if (not FILE):
            self.pushEvent(
                "ERROR", "Failed to open file '%s' for entity '%s'." %
                (candidate, ename))
            return(0)

        newFrame             = EntityFrame()
        newFrame.oeHandle   = FILE
        newFrame.oeName     = ename
        newFrame.oeFilename = sysid
        newFrame.oeTagDepth = self.getDepth()
        newFrame.l          = ""
        newFrame.cursor     = -1
        newFrame.oeLinenum  =  0
        return(self.getDepth())

    def closeEntity(self):
        self.su.lg.vMsg(0,"Closing entity '%s'." % self.entStack[-1].oeName)
        self.entStack[-1].oeHandle.close()
        self.entStack.pop()
        return(self.getDepth())

    def entDepth(self):
        return(len(self.entStack))

    def wholeLoc(self):
        buf = ""
        for i in (range(self.entDepth()-1, 0, -1)):
            buf += ("    %2d: Entity %-12s line %6d, file '%s'" %
                (i,
                self.entStack[i].oeName,
                self.entStack[i].oeLinenum,
                self.entStack[i].oeFilename))
        return(buf)

    def entLoc(self):
        return(self.entStack[-1].oeName + " + " + self.entStack[-1].oeLineNum)

    def entName(self):
        return(self.entStack[-1].oeName)

    def entLine(self):
        return(self.entStack[-1].oeLineNum)

    def entChar(self):
        return(self.entStack[-1].oeCharNum)

    def fillBuf(self):
        self.su.lg.vMsg(0,"In fillBuf, entity stack depth " + self.getDepth())
        while ((self.getDepth() > 0)):
            CURFILE = self.entStack[-1].oeHandle
            rec = CURFILE.readline()
            if (rec):
                self.su.lg.vMsg(0,"Read line: rec")
                self.entStack[-1].oeCharNum += len(rec)
                self.entStack[-1].oeLineNum += 1
                self.entStack[-1].cursor = 0
                rec = re.sub("\r\n\r","\n",rec)
                self.entStack[-1].curBuf += rec
                return self.entStack[-1].curBuf
            self.closeEntity()
        return(None) # EOF


    def curChar(self):
        """Return the character the cursor is on, without consuming it
        """
        if (self.getDepth() < 1):
            # warn "Nothing on open entity stack!";
            return("")
        if (self.entStack[-1].cursor >= len(self.entStack[-1].curBuf)):
            if (not self.fillBuf()):
                return(None)
        return(self.entStack[-1].curBuf[self.entStack[-1].cursor])

    def consumeChar(self):
        """Return the character the cursor is on, AND consume it.
        """
        c = self.curChar()
        self.nextChar()
        return(c)

    def nextChar(self):
        """Move to and return, the continue character.
        """
        self.entStack[-1].cursor += 1
        return(self.curChar())



###############################################################################
###############################################################################
# Used by EntityManager package, just to store the tuple needed for one
# currently-open entity.
#
class EntityFrame:
    def __init__(self):
        self.oeName     = ""       # Name of the entity
        self.oeFilename = ""       # Corresponding file name
        self.oeHandle   = ""       # File handle
        self.oeLinenum  = ""       # Current line-number in the entity
        self.oeCharnum  = ""       # Current chare-number in the entity
        self.oeTagDepth = ""       # How deeply nested are we at start of ent?
        self.l          = ""       # Current record of input file
        self.cursor     = ""       # Current loc in the input record



###############################################################################
###############################################################################
#
class NotationDcl:
    def __init__(self, nname, pubid, sysid):
        self.nname      = nname   # Name of the notation
        self.pubid      = pubid   #
        self.sysid      = sysid   #



###############################################################################
###############################################################################
#
class EntityDoStuff:
    """FIX"""
    def __init__(self, su=None):
        self.foo = True
        self.textEntities = {}
        self.fileEntities = {}
        self.ecount = 0
        self.useHtmlEntities = True
        self.useXmlEntities  = True
        self.su = su or sjdUtils()

    def expandEntities(self, s):
        s = re.sub(r"^&(#\d+#x[\da-f]+xname);", self.eeRHS, s)
        return(s)

    def eeRHS(self, mat):
        return(self.expandEntity(mat.group(1)))

    def expandEntity(self, raw):
        buf = ""
        mat = re.sub(r"^&#x([0-9a-f]+)","",raw)        # Hexadecimal Char Ref
        if (mat):
            c = unichr(int(mat.group(1)),16)
            if (not c or not self.su.isXmlChar(c)):
                self.pushEvent(
                    "ERROR", "WF: Character reference to non-XML Char 0x%s" %
                    (mat.group(1)))
            return(c)

        mat = re.sub(r"^&#([0-9]+)","",raw)            # Decimal Char Ref
        if (mat):
            c = unichr(int(mat.group(1)))
            if (not c or  not self.su.isXmlChar(c)):
                self.pushEvent(
                    "ERROR", "WF: Character reference to non-XML Char 0d%s" %
                    (mat.group(1)))
            return(c)

        mat = re.sub(r"^&(xname);","",raw)             # Named Entity Ref
        if (mat):
            buf = self.lookupEntityName(mat.group(1))
            return(buf)

        self.su.lg.vMsg(0,"WF: Bad entity reference syntax: 'raw'.")
        return(raw)

    def lookupEntityName(self, ename):
        """Find a definition for a given entity name. Try predefined XML
        ones first, then any the caller defined, then HTML if enabled.
        """
        if (self.useXmlEntities and ename in EntityManager.builtins):
            return(EntityManager.builtins[ename])
        if (ename in self.textEntities):
            return(self.textEntities[ename])
        if (ename in self.fileEntities):
            sys.stderr.write("File (system) entities are not yet supported.")
            return("&ename;")
        if (self.useHtmlEntities):
            evalue = EntityManager.htmlparser.unescape("&"+ename+";")
            if (evalue != "&"+ename+";"): return(evalue)
        self.su.lg.vMsg(0,"Unrecognized entity name '"+ename+"'.")
        return("<!-- Unrecognized entity name '"+ename+"' -->")

    def setXmlEntities(self, flag):
        self.useXmlEntities = bool(flag)

    def addTextEntity(self, aName, value):
        """Could also prevent redefinition of HTML entities.
        """
        if (aName in self.textEntities or
            aName in self.fileEntities or
            aName in EntityManager.builtins):
            sys.stderr.write("Entity 'aName' redefined.")
        self.textEntities[aName] = value
        self.ecount += 1

    def setHtmlEntities(self,flag):
        self.useHtmlEntities = bool(flag)



###############################################################################
###############################################################################
#
perldoc = """

=pod

=head1 Usage

EntityManager.py (Python)

Manages Entity and Notation definitions for an XML parser.

B<(unfinished)>



=head1 Methods

=over

=item * B<new>()

=item * B<setOption>(I<name, value>)

Options available include:

=over

I<expandEntities> -- (Boolean) if turned off, entities will be returned as
I<unparsed> events with a single argument, which is the original form
of the entity (or numeric character) reference.

I<entitiesInPIs> -- (Boolean) if set, the content of PIs (but not the
I<target>) will be parsed in search of entity and character references,
which will be expanded.

=back


=item * B<appendEntityPath>(path)

Add I<path> to the end of the list of directories, in which to search
for external entities. First added, is first searched.

=item * $s = B<getText>()

Return the current contents of the buffer to be parsed (that is, any pending
text that has not yet been parsed). This does not clear the buffer; to do that
use I<clearText>().

=item * B<clearText>()

Remove any remaining text in the parse buffer (the text is returned);


=item * B<addTextEntity>(I<name, value>)

Define the entity I<name> to the given (string) value. If I<setHtmlEntities>()
is in effect, defining an entity via <addEntity> overrides any HTML entity
of the same name.
Entities that refer to files, URIs, etc. are not yet supported.

=item * B<setHtmlEntities>(I<flag>)

Determine whether to recognize the standard HTML named character entities.
They are off by default; this calls turns them on unless I<flag> is present
and has the value 0 (if I<flag> is entirely absent, they are turned I<on>!)
Individual entities can be overridden via I<addEntity>().

=item * B<setXmlEntities>(I<flag>)

Determine whether to recognize the five XML built-in entities.
They are on by default; this calls turns them on unless I<flag> is present
and has the value 0 (if I<flag> is entirely absent, they are turned I<on>!)
These entities cannot be overridden when on.

=item * B<getDepth>()

Returns the number of open entities.

...



=head1 Known bugs and limitations



=head1 Related commands

C<EntityManager.pm> -- Perl equivalent.



=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License, with one additional restriction:

For further information on
the CCLI license, see L<http://creativecommons.org/licenses/by-sa/3.0/>.

For the most recent version, see L<http://www.derose.net/steve/utilities/>.

=cut
"""
