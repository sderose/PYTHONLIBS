#!/usr/bin/env python3
#
# ReadAny.py: Read plain/zip/gzip files, directories, etc.
# 2013-03-22: Written by Steven J. DeRose.
#
import sys
import re
import os
import codecs
import zipfile
import gzip
import tarfile
#import magic

from sjdUtils import sjdUtils

__metadata__ = {
    'title'        : "ReadAny",
    'description'  : "Read plain/zip/gzip files, directories, etc.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2013-03-22",
    'modified'     : "2020-08-23",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Usage=

ReadAny.py [options] [files]

'''UNFINISHED'''

Transparently read files whether they are zip, gzip, or plain.
Can do recursive directory traversal, and include/exclude
backups, hidden files, links, and/or binary files.

Caller can either request each file or record as needed, or run everything
and get callbacks per file or record.

Also maintains counts of records and of each category of file-system item.


=Methods=

The usual File methods are also supported: ''open''() (a no-op), ''close''(),
''seek''(), ''tell''(), ''isatty''(), ''read''(), ''readline''().

* '''ReadAny(files, recursive=0, binaries=0, halt="ALL", backups=0, hiddens=0, links=0, verbose=0)'''

Constructor.

** ''files'' is an array of paths, such as from a typical command line.
If the array is empty, STDIN is used (but will not be uncompressed!)

** ''recursive'' makes the read proceed down through sub-directories.

** ''binaries'' includes binary files other than zips and gzips (those two
kinds are transparently opened and their contents decompressed, regardless
of this setting).
UNFINISHED

** ''hiddens'' includes files whose names, or any of whose ancestor
directories names, start with ".".

** ''halt'' determines whether a user interrupt (^C) should
stop nothing (`IGNORE`),
stop just the current file (`FILE`), or
stop everything (`ALL`).
`ALL` is the default.
UNFINISHED

** ''backups'' determines whether to include files which appear to
be backups: namely, with names ending "~" or ".bak" or "#".

** ''verbose'' specifies the messaging level (default: 0).

* nextItem

Returns an `OpenItem` object representing the next file-system item,
whether it is something you want or not. That is, this stops at all
readable files,
directories even if you aren't going to recurse into them,
binary files even if you aren't going to read them,
backups even if you aren't going to read them, etc.
Seldom needed (though if you're cloning a whole directory tree or something,
you may want to stop at all the directories as you go.

* nextFile

Open the next file, and pass back a file-handle to it.
Collections are transparently opened; such as directories,
zip, gzip, and eventually tar files, etc.
All the "leaf" files support `readline`() directly
(see the Python `zipfile` and `gzip` packages).
''nextFile'' will force any current ''readable'' file to be closed,
whether or not they have been completely read (or course, it won't force
a directory to close until all its descendants have been handled, if
you're recursing.

Returns `None` when there are no more files to get to.

* readline

* readAll(openCB, recordCB, closeCB)

Do all the reading, but via callbacks instead of pulling a file or record
at a time. The callbacks are:

* ''openCB(path, fh, type)''

If provided, called when each file it opened (not including directories
or files that are missing or skipped, such as backups).

** ''recordCB(string, path, recnum, totalRecords)''

If this callback is not defined, the file will not even be read by this
package. If this callback is defined, it will be called for each record
of each input file; if it returns -1 the file will be closed (see
''closeCB'') and the next file started; if -2, all files will be closed.

** ''closeCB(path, fh, type, totalRecordsInFile, totalRecords)''

If provided, called just before the item is closed.


=Related Commands=

`zcat` -- unzips and cats a file.

`less` -- clever enough to unzip things by itself.

This package ised by `selectNgrams.py` and `calculateMI.py`.


=Known bugs and limitations=


=To do=

* Add uudecode, mscompress, etc.?
* Add grep-like --include/--exclude?
* Add option to control link/alias handling.
* Other backup conventions (see `copyExprs`)
* Integrate into PowerWalk?
* Integrate into: selectNGrams.py, calculateMI.py, findExamples.py,
* Twitter.py, deriveData.py, disaggregate.py, extractNgrams.py.
* Integrate into: grepData, lessData, uniqData,
countData, alignData, deriveData, countChars, vocab, ngrams,
globalChange, body, randomRecords.


=History=

* 2013-03-22: Written by Steven J. DeRose.
* 2013-04-03: Split out from selectNgrams.py.
* 2013-06-20: Rough out rest of usual File methods.
* 2018-06-01: Attach codecs.
* 2020-08-27: New layout.
* 2021-09-17: Doc cleanup.


=Rights=

Copyright 2013-03-22 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
# Filename patterns indicating copies or backups
#
copyExprs = {
    "emacs1": r'(~\d+)?~$',
    "emacs2": r'^#.*#$',
    "user1":  r'\.bak$',
    "mac1":   r' copy( \d+)?\.\w+$',    # (before extension)
    "win1":   r'^Copy (\d+ )of ',
    "win2":   r'^(Copy of )+',
    "patch":  r'\.orig$',
    "linux1": r'\(\w* *copy\)\.\w+$',  # (copy) (another copy) (3rd copy)...
}

typeNames = { # Determined by OpenItem
    "MISSING": "ERROR",
    "BAD":     "ERROR",
    "DIR":     "COLLECTION",
    "ZIP":     "COLLECTION",
    "GZIP":    "COLLECTION",
    "TAR":     "COLLECTION",
    "TEXT":    "READABLE",
    "STDIN":   "READABLE",
    "LINK":    "LINK",
    }


###############################################################################
# Returns type: MISSING DIR ZIP GZIP FILE STDIN BAD
# (If you pass 'pathList' instead of 'path', it pretends it's a DIR)
#
class OpenItem:
    def __init__(self, path, pathList=None, encoding="utf-8"):
        self.path     = path
        self.encoding = encoding
        self.pathList = pathList
        self.type     = None
        self.subList  = []
        self.fh       = None
        self.recnum   = 0

        ###
        ### if we're IN a collection, have to do something special to open...
        ###
        if (pathList):
            self.type    = "DIR"
            self.subList = pathList
        elif (path is None):
            self.type = "STDIN"
            self.fh = sys.stdin
        elif (not os.path.exists(path)):
            self.type = "MISSING"
        elif (os.path.isdir(path)):
            self.type = "DIR"
            self.subList = os.listdir(path)
        elif (os.path.islink(path)):
            self.type = "LINK"
        elif (re.search(r'\.tar(\.gz|\.bz2)?$',path)):
            self.type = "TAR"
            self.fh = tarfile.TarFile.open(path)
            self.subList = self.fh.getnames()
        elif (zipfile.is_zipfile(path)):
            self.type = "ZIP"
            z = zipfile.ZipFile(path, 'r')
            self.subList = z.namelist()
            z.close()
        elif (re.search(r'\.gz$',path)):
            self.type = "GZIP"
            self.fh = gzip.GzipFile(path, 'r')     # Aggregates????
        elif (os.path.isfile(path)):
            self.type = "FILE"
            self.fh = codecs.open(path, "r", encoding=self.encoding)
        else:
            self.type = "BAD"

    def isCollectionType(self):
        if (self.type in typeNames and
            typeNames[self.type] == "COLLECTION"): return(1)
        return(0)

    def isReadableType(self):
        if (self.type in typeNames and
            typeNames[self.type] == "READABLE"): return(1)
        return(0)

    def openNextChild(self):
        if (not self.isCollectionType):
            return(None)
        #print("openNextChild: in %s, childNum = %d of %d" %
        #    (self.type, self.recnum, len(self.subList)))
        if (self.recnum >= len(self.subList)-1):
            return(None)
        self.recnum += 1

        if (self.path):
            chName = self.path + "/" + self.subList[self.recnum]
        else:
            chName = self.subList[self.recnum]
        #print("    chName is " + chName)
        if (self.type == "DIR"):
            chHandle = OpenItem(chName)
        elif (self.type == "ZIP"):
            chHandle = OpenItem(chName)
        elif (self.type == "GZIP"):
            chHandle = OpenItem(chName)
        elif (self.type == "TAR"):
            chHandle = self.fh.extract(chName)
        else:
            print("Unknown collection type '"+self.type+"'.")
            sys.exit(0)
        return(chHandle)

    def close(self):
        if (self.fh): self.fh.close()


###############################################################################
#
class ReadAny:
    def __init__(self, files,
                 recursive=0, binaries=0, backups=0, hiddens=0, links=0,
                 halt="ALL", verbose=0):
        self.files          = files
        self.recursive      = recursive
        self.binaries       = binaries
        self.backups        = backups
        self.hiddens        = hiddens
        self.links          = links
        self.halt           = halt
        self.verbose        = verbose
        self.su             = sjdUtils()
        self.su.setVerbose(verbose)

        self.openItems      = []
        self.halted         = 0

        # Stats
        self.started        = 0
        self.totalRecords   = 0
        self.nItems         = 0
        self.itemCounts = {}
        for tn in (typeNames):
            self.itemCounts[tn] = 0

    def depth(self):
        return(len(self.openItems))

    def curPath(self):
        if (self.depth() > 0):
            return(self.openItems[-1].path)
        return(None)

    def closeCurrentItem(self):
        if (self.depth() > 0):
            self.openItems[-1].close()
            self.openItems.pop()
        if (self.depth() <= 0):
            return(None)
        return(self.openItems[-1])


    def start(self):
        if (self.started):
            print("start() called when already started.")
            sys.exit()
        self.started = 1

        if (len(self.files)==0):                  # STDIN
            self.openItems.append(OpenItem(None))
            self.nItems = 1
            return(sys.stdin)
        newItem = OpenItem(None,pathList=self.files)
        self.openItems.append(newItem)
        return(self.nextItem())


    # Advance to the next item of whatever type -- even things we don't want!
    def nextItem(self):
        while(1):
            try:
                if (not self.started):
                    print("Call start() before nextItem.")
                    sys.exit()

                if (len(self.openItems)<=0):
                    return(None)

                # Close a NON-COLLECTION if currently open
                curItem = self.openItems[-1]
                if (not curItem.isCollectionType()):
                    curItem = self.closeCurrentItem()

                # Try to open next child; if done, pop and go on to aunts...
                # (this doesn't recurse down collections; caller may)
                while (curItem):
                    ch = curItem.openNextChild()
                    if (ch):
                        self.openItems.append(ch)
                        return(ch)
                    curItem = self.closeCurrentItem()
                break # FAIL(nothing left)
            except KeyboardInterrupt:
                sys.stderr.write(
                    "KeyboardInterrupt receive, halt = " + self.halt)
                if (self.halt=="FILE" or self.halt=="ALL"):
                    if (self.halt=="ALL"): self.halted = 1

        # We've closed all the way and there's nobody.
        return(None)


    # Advance to the next desired, non-collection item
    def nextFile(self):
        while(1):
            curItem = self.nextItem()
            if (curItem is None):                 # The END
                break
            elif (curItem.isCollectionType):      # Recurse or skip?
                if (not self.recursive):
                    self.closeCurrentItem()
            elif (curItem.isReadableType):        # Some file; do we want it?
                if ((not self.backups) and            # undesired backup
                    re.match(r'(~|#|\.bak)$', curItem.path)): continue
                if ((not self.hiddens) and            # undesired .xyz
                    re.match(r'(^\.|/\.)', curItem.path)): continue
                #if ((not self.binaries) and           # undesired binary
                #    (magic.from_file(curItem.path)).index("text")<0): continue
                break                             # Ahhhh! Got something
        return(curItem)

    def readAll(self, openCB, recordCB, closeCB):
        if (len(self.openItems)<=0):
            return(None)
        totalRecords = 0
        while (1):
            f = self.nextFile()
            if (f is None): return(None)
            curItem = self.openItems[-1]
            if (openCB): openCB(curItem.path, f, curItem.type)
            if (recordCB is None): continue
            while(1):
                rec = f.readline()
                if (len(rec) == 0): break
                rc = recordCB(rec, curItem.path, curItem.recnum,
                         totalRecords+curItem.recnum)
                if (rc == -1): break
                elif (rc == -2): return(None)
            totalRecords += curItem.recnum
            if (closeCB): closeCB(curItem.path, f, curItem.type)
        return(None)


    ###########################################################################
    # Standard calls, so we look like a File.
    #
    def open(self, path, mode):
        pass

    def seek(self, n, whence):
        if (len(self.openItems)<=0):
            return(None)
        curItem = self.openItems[-1]
        return(curItem.fh.seek(n, whence))


    def tell(self):
        if (len(self.openItems)<=0):
            return(None)
        curItem = self.openItems[-1]
        return(curItem.fh.tell())

    def isatty(self, size):
        if (len(self.openItems)<=0):
            return(None)
        curItem = self.openItems[-1]
        return(curItem.fh.isatty(size))

    def close(self):
        pass

    def read(self, size):
        if (len(self.openItems)<=0):
            return(None)
        curItem = self.openItems[-1]
        return(curItem.fh.read(size))

    def readline(self):
        if (len(self.openItems)<=0):
            return(None)
        curItem = self.openItems[-1]
        curItem.recnum += 1
        return(curItem.fh.readline())
