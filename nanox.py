#!/usr/bin/env python
#
# By Steven J. DeRose, written 2019-08-10.
#
# This work by Steven J. DeRose is licensed under a Creative Commons
# Attribution-Share Alike 3.0 Unported License. For further information on
# this license, see http://creativecommons.org/licenses/by-sa/3.0/.
# For the most recent version, see http://www.derose.net/steve/utilities/.
#
# Based on alogging.formatRec, in turn on sjd Logging PHP package for ccel.org.
# Rename 'paexano'?
#
import sys
import re
from collections import defaultdict, OrderedDict, namedtuple, deque

class nanox:
    """Make an XML equivalent of JSON i/o for Python, to make it equally trivial to
    make slightly better data.

    To do:
        Lost separate <item> element in dicts, move @n onto sub's @k.
        Use ol and ul or dl for list and dict?
        NaN, Inf, -0?
        Special list types for numpy vector and tensor?
        Sparse lists (via repeat of prior list item?)
        Write list indexes?
        Circularity protection
        Know how to dump XML objects, too? As-is or mapto JEX...
        ChainMap?
        namedtuple.
        tuple can't be iterated, so can't just treat as list.
        Option to write as HTML w/ link to stylesheet.
        <i n="1"/> or <i>1</i> or <i/1/
        Write homogeneous numeric arrays as just numbers or NUMTOKENS?
    """
    buf = ""

    @staticmethod
    def encode(obj, indentString='  ', indent=True, maxDepth=3,
        xmlDecl=True,
        doctype="https://www.derose.net/namespaces/schemas/nanox.xsd",
        sparseLists=False, sortDict=False, ignoreCase=True
        ):
        """NOTE: This is not protected against circular structures, except
        by 'maxDepth'.
        """
        options = {
            'version'       : "0.1",
            'indentString'  : indentString,
            'indent'		: indent,
            'maxDepth'    	: maxDepth,
            'xmlDecl'    	: xmlDecl,
            'doctype'    	: doctype,
            'sparseLists'	: sparseLists,
            'sortDict'    	: sortDict,
            'ignoreCase'	: ignoreCase,
        }

        nanox.buf = ''
        if (xmlDecl):
            nanox.buf += '<?xml version="1.0" encoding="utf-8"?>'
        if (doctype):
            nanox.buf += '<DOCTYPE nanox SYSTEM "%s">' % (options['doctype'])
        nanox.buf += '<nanox version="%s">' % (options['version'])
        nanox.encode_r(obj, options=options)
        nanox.buf += '</nanox>'
        return nanox.buf

    @staticmethod
    def encode_r(obj, options, depth=0):
        if (options['maxDepth'] and depth > options['maxDepth']): return
        btype = nanox.getBasicType(obj)
        if (btype is None):                                # NONE
            nanox.gen(depth, options, "<null/>")

        elif (btype == bool):                              # BOOLEAN
            nanox.gen(depth, options, '<b n="%d"/>' % (1 if (obj) else 0))

        elif (btype == int):                               # INT
            nanox.gen(depth, options, '<i n="%d"/>' % (obj))

        elif (btype == float):                             # FLOAT
            nanox.gen(depth, options, '<f n="%f"/>' % (obj))

        elif (btype == complex):                           # COMPLEX
            nanox.gen(depth, options, '<c r="%f" j="%f"/>' % (obj.real, obj.imag))

        elif (btype == str):                               # STRING
            nanox.gen(depth, options, '<s>%s</s>' % (nanox.escContent(obj)))

        elif (btype == list):                              # LIST
            subclass = ""
            if (type(obj) != type([])):
                subclass = ' class="%s"' % (nanox.className(obj))
            hFlag = ""
            if (nanox.isHomogeneous(obj)): hFlag = ' hom="1"'
            nanox.gen(depth, options, '<list%s%s>' % (subclass, hFlag))
            for n, v in enumerate(obj):
                nanox.encode_r(v, options, depth=depth+1)
            nanox.gen(depth, options, '</list>')

        elif (btype == dict):                              # DICT
            subclass = ""
            if (type(obj) != type({})):
                subclass = ' class="%s"' % (nanox.className(obj))
            hFlag = ""
            if (nanox.isHomogeneous(obj)): hFlag = ' hom="1"'
            nanox.gen(depth, options, "<dict%s%s>" % (subclass, hFlag))
            try:
                theKeys = list(obj.keys())
            except TypeError as e:
                sys.stderr.write("TypeError on a '%s':\n%s\n%s" %
                    (type(obj), repr(obj), e))
                sys.exit()
            if (options['sortDict']):
                if (options['ignoreCase']): theKeys.sort(key=str.lower)
                else: theKeys.sort()
            for n in (theKeys):
                nanox.gen(depth, options, '<item n="%s">' % (n))
                nanox.encode_r(obj[n], options, depth=depth+1)
                nanox.gen(depth, options, '</item>')
            nanox.gen(depth, options, '</dict>')

        elif (isinstance(obj, object)):                    # OBJECT
            theKeys = dir(obj)
            if (options['sortDict']):
                if (options['ignoreCase']): theKeys.sort(key=str.lower)
                else: theKeys.sort()
            nanox.gen(depth, options, '<obj id="_%s" class="%s">' %
                (id(obj), nanox.className(obj)))
            for n in (theKeys):
                thing = getattr(obj, n, "[NONE]")
                if ((n.startswith('__') or callable(thing))):
                    continue
                nanox.gen(depth, options, '<item n="%s">' % (n))
                if (isinstance(thing, object)):                # SHALLOW
                    nanox.gen(depth, options, '<objref rid="_%s" />' % (id(thing)))
                else:
                    nanox.encode_r(thing, options, depth+1)
            nanox.gen(depth, options, '</obj>')

        else:
            nanox.gen(depth, options, ("<!-- PROBLEM -->"))
        return nanox.buf
        # end encode


    @staticmethod
    def gen(depth, options, s):
        if (options['indent']): nanox.buf += "\n" + (options['indentString'] * depth)
        nanox.buf += s

    @staticmethod
    def className(obj):
        c = "%s" % (type(obj))
        c = re.sub(r".*'(.*)'.*", "\\1", c)
        return c

    @staticmethod
    def escContent(s):
        s = s.replace(r'&', '&amp;')
        s = s.replace(r'<', '&lt;')
        s = s.replace(r']]>', ']]&gt;')
        return s

    @staticmethod
    def escQuote(s):
        s = s.replace(r'&', '&amp;')
        s = s.replace(r'"', '&quot;')
        return s

    @staticmethod
    def isHomogeneous(coll):
        seenAnything = False
        for x in coll:
            if (not seenAnything):
                theType = type(x)
                seenAnything = True
            elif (type(x) != theType): return False
        return True

    @staticmethod
    def isBasicallyHomogeneous(coll):
        seenAnything = False
        for x in coll:
            if (not seenAnything):
                theType = nanox.getBasicType(x)
                seenAnything = True
            elif (nanox.getBasicType(x) != theType): return False
        return True

    @staticmethod
    def getBasicType(v):
        if (v is None):
            return None
        if (v is True or v is False):
            return bool
        if (isinstance(v, int)):
            return int
        if (isinstance(v, float)):
            return float
        if (isinstance(v, complex)):
            return complex
        if (isinstance(v, str)):
            return str
        if (isinstance(v, object)):
            #vt = type(v)
            if (isinstance(v, (list, set, frozenset, tuple, deque))):
                return list
            if (isinstance(v, (dict, defaultdict, OrderedDict))):
                return dict
            # namedtuple is not exactly a class.....
            return object
        return "UNSUPPORTED"

if  __name__ == "__main__":
    a = {
        'a': None,
        'b': False,
        'c': True,
        'd': 32767,
        'e': 3.1415926,
        'f': 1.0+2.4j,
        'g': [ 10, 20, 30, 40 ],
        'h': { 'aardvark':1, 'basilisk':2, 'catoblepas':None },
        'i': [ [ 1, 2, 3 ], [ 4, 5, 6 ], [ 7, 8, 9 ], [ 10, 11, 12 ] ],
        'j': ( 'tuple1', 'tuple2', 'tuple3', 'tuple4' ),
    }

    print(nanox.encode(a))

    d = defaultdict(int)
    d['cat'] = 'mouse'
    d['dog'] = 'cat'

    print(nanox.encode(d))

