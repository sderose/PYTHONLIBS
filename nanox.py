#!/usr/bin/env python
#
# nanox.py: JSON-like encode/decode.
#
#pylint: disable=W0613, W0212, W0603
#
import sys
import re
from collections import defaultdict, OrderedDict, deque, Counter

__metadata__ = {
    'title'        : "nanox.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2019-08-10",
    'modified'     : "2020-02-27",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Make an XML equivalent of JSON i/o for Python,
to make it equally trivial to make slightly better data.

Modelled on [https://docs.python.org/3/library/json.html].

''Not thoroughly tested yet''

=Classes and Methods=


==Output==

nanox.dump(obj, fp, *, cls=None, xmlDecl=True, doctype="...",
sparseLists=False, sortDict=False, ignoreCase=True, **kw)

nanox.dumps(obj, *, cls=None, xmlDecl=True, doctype="...,
sparseLists=False, sortDict=False, ignoreCase=True, **kw)

class nanox.NANOXEncoder(*, xmlDecl=True, doctype="...",
sparseLists=False, sortDict=False, ignoreCase=True)

The following keyword arguments are common to all of the above calls,
and are only in Nanox, not JSON:

* xmlDecl: Write an XML declaration at the beginning.
* doctype: Write this as the SYSTEM identifier for the doctype declaration.
* sparseLists: Compress sparse lists and repetitions
* sortDict: Write dicts in sorted order of their keys.
* ignoreCase: With `sortDict`, ignore case for string sorting.

The following keyword arguments are common to all of the above calls (but not
shown above, for brevity). They have the same meaning in nanox:

* skipkeys=False -- Skips dict keys that are not str, int, float, bool, or None.

* ensure_ascii=True -- Hex-code all non-ASCII characters.

* check_circular=True -- Test for circularity (not yet supported here).

* allow_nan=True -- If false, do not output NaN, -inf, or +inf.

* indent=None --

* separators=None -- For JSON, this indicates whether to use (', ', ': ') or something else, such as (',', ':') as key and item separators. In Nanox,

* default=None --

* sort_keys=False --


==Input==

''(unfinished)''

nanox.load(fp, *, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, object_pairs_hook=None, **kw)

nanox.loads(s, *, cls=None, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, object_pairs_hook=None, **kw)

class nanox.NANOXEncoder(*, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, strict=True, object_pairs_hook=None)


=Why?=

* Can distinguish more precise datatypes than JSON (int, float, complex,....),
while still allowing fallback for naive importers.
* Can retain subclass information.
* Can export instances of classes and rebuild them on import.
* Can be post-processed with a far wider range of tools (validators, XSLT, etc. etc.)
* Much more human-readable.
* Has room to attach metadata, such as list homogeneity, subclasses, etc.
* Far more compact for sparse or repetitive lists.
* Better support for IEEE floating-point things like NaN and -inf.
* Can support actual inter-object references.

=Related commands=

`DomBuilder.py` is quite similar to NANOXDecode().

=Mapping=

    Python     NANOX              JSON
    -----      ------             ----
    dict       <dict>...</dict>   {...}
    list       <list>...</list>   [...]
    str        <s>...</s>         "..."
    int        <i n="9"/>         9
    float      <f n="9.9"/>       9.9
    True       <T/>               true
    False      <F/>               false
    None       <NULL/>            null

The XML tag and attributes names used are defined in class `TagName` and `AttrName`.
as the values of variables
named as '_' plus the names above (mostly Python type names),
and whose values are the tag names to use, as shown above.
An option will probably be added to enable changing them.

These correspond closely to what the JSON Encoder supports. However,
because Python items are here mapped to full-fledged XML elements, there is room
for more information. Thus:

* homogeneous lists and dicts get attributes saying what types they use.
On import, such cases could
be mapped into special classes if desired (such as my `Homogeneous.hlist`
and  `Homogeneous.hdict`.

* Python's subclasses of list or dict are mapped as above, but with the correct
subclass name also expressed on a 'subclass' attribute. The correct subclass
should be instantiated when decoding (this only applies to classes defined in
Python's `collections` library).

In addition, NANOX supports:

    Python        NANOX
    ------        -----
    complex       <c r="%f" j="%f"/>
    object        <object class="foo" id="xyz" flag="1"...>
                      <item n="fname"><s>Smith</s></item>...</object>
    reference     <objref rid="xyz"/>

objects have their actual class identified by the `subclass` attribute. On export,
their `dir` is traversed and exported as if the objects were a `dict`. However,
entries are not exported if they begin with '__' or are callable.

And coming eventually:
    sparse arrays and repeated items:
        <list>
            <skip to="99">...</skip>
            <repeat n="99"/>
        </list>

=Known bugs, limitations, and to-do items=

* Haven't really thought through non-string dict keys (like arbitrary hashables).
Seems excessive in most cases, to promote them to whole elements. Option?
* Circularity protection
* Object references don't get re-attached when loading. Still TODO.
* NaN, Inf, -0? Support those and other options known to JSON lib.
* ChainMap? compiled regex undo? Exception classes?
* namedtuples and frozensets are not yet decoded to the exact right type.

Compactness:
* Sparse lists support
* Repeated-item support
* Special list types for numpy vector and tensor?
* Might want fixed-dim vectors as a special thing, too (NUMTOKENS-ish?)

Layout:
* Option for newline before collection close
* There is no control of numeric formats, such as number of post-decimal digits.
* Option to write list indexes?
* Option to write as HTML, or to change tag names in general?
* Option to write homogeneous numeric arrays as just numbers or NUMTOKENS?
* Option to repeat key/index value as a comment at the end of very long substrucs.
* Might want option to write complex numbers "1+2j" instead of as separate parts.
* Should there be more compact forms for homogeneous lists?
* Should *scalar* item values in dict, move onto an attribute (essentially #CONREF)?

==Mapping issues/questions==

* Should True and False become <b v="1"/> and <b v="0"/> like other scalars?
* Should the text of strings move from content to v=""?
* Should the value attribute have a different name per type?
* Should this use UL, OL, LI for dict, list, and item?

=History=

* 2019-08-10: Written.
Based on `alogging.formatRec`, in turn on sjd Logging PHP package for ccel.org.

* 2020-02-19: New layout. Lint. Start decoding. Improve collections support.

* 2020-02-27: Factor out tag and attribute names. Testing.

=Rights=

Copyright 2019 by Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].

=Options=
"""


###############################################################################
#
class TagName:
    """Map internal categories, to XML tags used to serialize them.
    """
    _root     = 'nanox'
    _dict     = 'dict'       # or ul?
    _list     = 'list'       # or ol?
    _object   = 'object'
    _str      = 's'
    _int      = 'i'
    _float    = 'f'          # Avoid due to F for False?
    _complex  = 'c'
    _objref   = 'objref'
    _True     = 'T'          # Maybe <b v="[01]"/> instead?
    _False    = 'F'
    _None     = 'NULL'
    _item     = 'item'

    nameIndex = {}

    @staticmethod
    def getOurName(aTagName):
        if (len(TagName.nameIndex) == 0):
            for k, v in TagName.__dict__.items():
                if (k[0] != '_' or k[1] == '_'): continue
                TagName.nameIndex[v] = k
        if (aTagName in TagName.nameIndex): return TagName.nameIndex[aTagName]
        return None


###############################################################################
#
class TagGroup:
    _root     = 'COLLECTION'
    _dict     = 'COLLECTION'  # or ul?
    _list     = 'COLLECTION'  # or ol?
    _object   = 'COLLECTION'
    _str      = 'SCALAR'      # But oddly, not an empty element.
    _int      = 'SCALAR'
    _float    = 'SCALAR'      # Avoid due to F for False?
    _complex  = 'SCALAR'
    _objref   = 'SCALAR'
    _True     = 'CONST'
    _False    = 'CONST'
    _None     = 'CONST'
    _item     = 'DICTITEM'    # A named member of a dict (contains value)

    def __init__(self):
        self.placeHolder = 1

    @staticmethod
    def getOurGroup(aTagName):
        ourName = TagName.getOurName(aTagName)
        #print("getOurName for '%s' got '%s'." % (aTagName, ourName))
        #print(TagGroup.__dict__)
        #grp = TagGroup.__getattribute__(ourName)
        grp = TagGroup.__dict__[ourName]
        return grp


###############################################################################
#
class AttrName:
    _id       = 'id'
    _rid      = 'rid'             # for objrefs
    _key      = 'k'               # for dict item keys
    _value    = 'v'               # scalar values that fit in attributes
    _realPart = 'r'               # of complex numbers
    _imagPart = 'j'               # of complex numbers
    _subclass = 'subclass'
    _dftType  = 'type'            # for defaultdict
    _homKeys  = 'keyType'         # keys of a dict are homogeneous of this type
    _homValues = 'valueType'      # values of a collection are homogeneous of this type


###############################################################################
#
def xmlDcl(encoding="utf-8"):
    return '<?xml version="1.0" encoding="%s"?>' % (encoding)

def startTag(s:str, attrs:dict=None):
    attList = ""
    if (attrs):
        for k, v in attrs.items():
            attList += ' %s="%s"' % (k, NANOXEncoder.escQuote(str(v)))
    return '<%s%s>' % (s, attList)

def emptyTag(s:str, attrs:dict=None):
    attList = ""
    if (attrs):
        for k, v in attrs.items():
            attList += ' %s="%s"' % (k, NANOXEncoder.escQuote(str(v)))
    return '<%s%s />' % (s, attList)

def endTag(s:str):
    return '</%s>' % (s)


###############################################################################
#
class nanox:
    @staticmethod
    def dump(obj, *, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None,
        separators=None, default=None, sort_keys=False,
        xmlDecl=True, doctype=None,
        sparseLists=False, sortDict=False, ignoreCase=True, **kw
        ):
        if (cls is None): cls = NANOXEncoder
        obj.write(cls.encode(obj, skipkeys=skipkeys,
        ensure_ascii=ensure_ascii, check_circular=check_circular,
        allow_nan=allow_nan, cls=cls, indent=indent,
        separators=separators, default=default, sort_keys=sort_keys,
        xmlDecl=xmlDecl, doctype=doctype,
        sparseLists=sparseLists, sortDict=sortDict, ignoreCase=ignoreCase, **kw))

    @staticmethod
    def dumps(obj, *, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None,
        separators=None, default=None, sort_keys=False,
        xmlDecl=True, doctype=None,
        sparseLists=False, sortDict=False, ignoreCase=True, **kw
        ):
        if (cls is None): cls = NANOXEncoder
        return cls.encode(obj, skipkeys=skipkeys,
        ensure_ascii=ensure_ascii, check_circular=check_circular,
        allow_nan=allow_nan, cls=cls, indent=indent,
        separators=separators, default=default, sort_keys=sort_keys,
        xmlDecl=xmlDecl, doctype=doctype,
        sparseLists=sparseLists, sortDict=sortDict, ignoreCase=ignoreCase, **kw)


###############################################################################
#
class NANOXEncoder:
    buf = ""

    @staticmethod
    def encode(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, sort_keys=False, indent=4,
        separators=None, default=None,
        xmlDecl=True, doctype=None,
        sparseLists=False, sortDict=False, ignoreCase=True, **kw
        ):
        """NOTE: This is not protected against circular structures, except
        by 'maxDepth'.
        """
        if (doctype is None):
            doctype = "https://www.derose.net/namespaces/schemas/nanox.xsd"

        if (indent is None): indent = 0
        options = {
            # JSON-like options
            'skipkeys'      : skipkeys,
            'ensure_ascii'  : ensure_ascii,
            'check_circular': check_circular,
            'allow_nan'     : allow_nan,
            'sort_keys'     : sort_keys,
            'indent'        : indent,
            'separators'    : separators,
            'default'       : default,

            # Nanox-specific options
            'version'       : "0.1",
            'maxDepth'      : 10,
            'xmlDecl'       : xmlDecl,
            'doctype'       : doctype,
            'sparseLists'   : sparseLists,
            'sortDict'      : sortDict,
            'ignoreCase'    : ignoreCase,
        }

        NANOXEncoder.buf = ''
        if (xmlDecl):
            NANOXEncoder.buf += xmlDcl()
        if (doctype):
            brk = "\n" if (options['indent'] > 0) else ""
            NANOXEncoder.buf += '%s<!DOCTYPE nanox PUBLIC "" "%s">%s' % (
                brk, options['doctype'], brk)
        NANOXEncoder.buf += '<%s version="%s">' % (TagName._root, options['version'])
        NANOXEncoder.encode_r(obj, options=options)
        NANOXEncoder.buf += endTag(TagName._root)
        return NANOXEncoder.buf

    @staticmethod
    def encode_r(obj, options, depth=0):
        if (options['maxDepth'] and depth > options['maxDepth']): return
        btype = NANOXEncoder.getBasicType(obj)

        ### CONST cases
        #
        if (btype is None):                                # NONE
            NANOXEncoder.gen(depth, options, emptyTag(TagName._None))

        elif (btype == bool):                              # BOOLEAN
            if (obj): tName = TagName._True
            else: tName = TagName._False
            NANOXEncoder.gen(depth, options, emptyTag(tName))

        ### Scalars that fit on an attributes
        #
        elif (btype == int):                               # INT
            NANOXEncoder.gen(depth, options,
                emptyTag(TagName._int, attrs={ AttrName._value: obj }))

        elif (btype == float):                             # FLOAT
            NANOXEncoder.gen(depth, options,
                emptyTag(TagName._float, attrs={ AttrName._value: obj }))

        elif (btype == complex):                           # COMPLEX
            NANOXEncoder.gen(depth, options, emptyTag(TagName._complex, attrs= {
                AttrName._realPart: obj.real, AttrName._imagPart: obj.imag }))

        ### Scalars that go in content (move to attr?)
        #
        elif (btype == str):                               # STRING
            NANOXEncoder.gen(depth, options, '<%s>%s</%s>' %
                (TagName._str, NANOXEncoder.escContent(obj), TagName._str))

        ### Collections
        #
        elif (btype == list):                              # LIST
            attrs = {}
            if (type(obj) != type([])):
                attrs[AttrName._subclass] = NANOXEncoder.className(obj)
            hType = NANOXEncoder.hasHomogeneousValues(obj)
            if (hType):
                attrs[AttrName._homValues] = hType
            NANOXEncoder.gen(depth, options, startTag(TagName._list, attrs=attrs))
            for n, v in enumerate(obj):
                NANOXEncoder.encode_r(v, options, depth=depth+1)
            NANOXEncoder.gen(depth, options, endTag(TagName._list))

        elif (btype == dict):                              # DICT
            attrs = {}
            if (type(obj) != type({})):
                attrs[AttrName._subclass] = NANOXEncoder.className(obj)
            hType = NANOXEncoder.hasHomogeneousKeys(obj)
            if (hType):
                attrs[AttrName._homKeys] = hType
            hType = NANOXEncoder.hasHomogeneousValues(obj)
            if (hType):
                attrs[AttrName._homValues] = hType
            NANOXEncoder.gen(depth, options, startTag(TagName._dict, attrs=attrs))
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
                NANOXEncoder.gen(depth, options,
                    startTag(TagName._item, attrs={ AttrName._key: n }))
                NANOXEncoder.encode_r(obj[n], options, depth=depth+1)
                NANOXEncoder.gen(depth, options, endTag(TagName._item))
            NANOXEncoder.gen(depth, options, endTag(TagName._dict))

        elif (isinstance(obj, object)):                    # OBJECT
            theKeys = dir(obj)
            if (options['sortDict']):
                if (options['ignoreCase']): theKeys.sort(key=str.lower)
                else: theKeys.sort()
            NANOXEncoder.gen(depth, options, startTag(TagName._object, attrs={
                AttrName._id, id(obj),
                AttrName._subclass, NANOXEncoder.className(obj) }))
            for n in (theKeys):
                thing = getattr(obj, n, "[NONE]")
                if ((n.startswith('__') or callable(thing))):
                    continue
                NANOXEncoder.gen(depth, options,
                    startTag(TagName._item, attrs={ AttrName._key: n }))
                if (isinstance(thing, object)):                # SHALLOW
                    NANOXEncoder.gen(depth, options,
                     emptyTag(TagName._objref, attrs={ AttrName._rid: id(thing) }))
                else:
                    NANOXEncoder.encode_r(thing, options, depth+1)
            NANOXEncoder.gen(depth, options, endTag(TagName._object))

        else:
            NANOXEncoder.gen(depth, options, ("<!-- PROBLEM -->"))
        return NANOXEncoder.buf
        # end encode


    @staticmethod
    def gen(depth:int, options:dict, s:str):
        if (options['indent'] > 0):
            NANOXEncoder.buf += "\n" + (' ' * (options['indent'] * depth))
        NANOXEncoder.buf += s

    @staticmethod
    def className(obj):
        c = "%s" % (type(obj))
        c = re.sub(r".*'(.*)'.*", "\\1", c)
        return c

    @staticmethod
    def escContent(s:str):
        s = s.replace(r'&', '&amp;')
        s = s.replace(r'<', '&lt;')
        s = s.replace(r']]>', ']]&gt;')
        return s

    @staticmethod
    def escQuote(s:str):
        s = s.replace(r'&', '&amp;')
        s = s.replace(r'"', '&quot;')
        return s

    @staticmethod
    def hasHomogeneousKeys(coll):
        seenAnything = False
        for x in coll.keys():
            if (not seenAnything):
                theType = type(x)
                seenAnything = True
            elif (type(x) != theType): return False
        return True

    @staticmethod
    def hasHomogeneousValues(coll, allowNone=False):
        seenAnything = False
        if (isinstance(coll, (list, tuple, set))):
            for x in coll:
                if (not seenAnything):
                    theType = type(x)
                    seenAnything = True
                elif (type(x) != theType): return False
        elif (isinstance(coll, dict)):
            for x in coll.values():
                if (not seenAnything):
                    theType = type(x)
                    seenAnything = True
                elif (type(x) != theType): return False
        else:
            raise TypeError("Must be a dict/list/tuple, not %s." % (type(coll)))
        return True

    @staticmethod
    def isBasicallyHomogeneous(coll, allowNone=False):
        seenAnything = False
        for x in coll:
            if (not seenAnything):
                theType = NANOXEncoder.getBasicType(x)
                seenAnything = True
            elif (NANOXEncoder.getBasicType(x) != theType): return False
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


###############################################################################
#
class NANOXDecoder:
    @staticmethod
    def decode(s:str):
        from xml.parsers import expat
        p = expat.ParserCreate(
            encoding=args.iencoding, namespace_separator=':')

        global theParser, theObject # For getting at location and error info
        theParser = p
        theObject = None
        p.StartElementHandler          = StartElementHandler
        p.EndElementHandler            = EndElementHandler
        p.CharacterDataHandler         = CharacterDataHandler
        #p.ProcessingInstructionHandler = ProcessingInstructionHandler
        #p.CommentHandler               = CommentHandler
        p.Parse(s)
        trace(0, "After parse, nodeStack len is %d, type of theObject %s." %
            (len(nodeStack), type(theObject)))
        return theObject


### Handlers ##############################################################
# (from DomBuilder.py)
#
theObject = None
theParser = None
nodeStack = []
idToCurrentPointer = {}
pendingName = None

def trace(lvl:int, msg:str):
    if (args.verbose>lvl): sys.stderr.write(msg+"\n")

def StartElementHandler(name:str, attributes=None):
    global pendingName, theObject
    trace(1, "StartElement: '%s' (depth was %d)" % (name, len(nodeStack)))
    if (len(nodeStack) == 0):
        nodeStack.append([])
        theObject = nodeStack[0]

    if (name == TagName._None):
        insertAtStackTop(None)
    elif (name == TagName._True):
        insertAtStackTop(True)
    elif (name == TagName._False):
        insertAtStackTop(False)
    elif (name == TagName._float):
        insertAtStackTop(float(attributes[AttrName._value]))
    elif (name == TagName._int):
        insertAtStackTop(int(attributes[AttrName._value]))
    elif (name == TagName._complex):
        insertAtStackTop(complex(
            float(attributes[AttrName._realPart]),
            float(attributes[AttrName._imagPart])))
    ####
    elif (name == TagName._str):
        trace(0, "STRING FAIL")
    elif (name == TagName._item):
        pendingName = attributes[AttrName._key]
    elif (name == TagName._objref):
        trace(0, "OBJREF FAIL")

    # If this is an aggregate, we push instead of insert.
    #
    elif (name == TagName._list):
        subclass = ''
        if (AttrName._subclass in attributes):
            subclass = attributes[AttrName._subclass]
        if (subclass == 'deque'):
            theNewList = deque()
        elif (subclass == 'tuple'):
            theNewList = []  # TODO: convert at the end
        else:
            theNewList = []
        insertAtStackTop(theNewList)
        nodeStack.append(theNewList)
    elif (name == TagName._dict):
        subclass = ''
        if (AttrName._subclass in attributes):
            subclass = attributes[AttrName._subclass]
        if (subclass == 'defaultdict'):
            theNewDict = defaultdict(attributes[AttrName._dftType])
        elif (subclass == 'set'):
            theNewDict = set()
        elif (subclass == 'frozenset'):
            theNewDict = set()  # TODO: freeze at the end
        elif (subclass == 'OrderedDict'):
            theNewDict = OrderedDict()
        elif (subclass == 'Counter'):
            theNewDict = Counter()
        elif (subclass == 'namedtuple'):
            theNewDict = {}  # TODO: convert at the end
        else:
            theNewDict = {}
        insertAtStackTop(theNewDict)
        nodeStack.append(theNewDict)
    elif (name == TagName._object):  # TODO: add props and vars
        subclass = ''
        if ('subclass' in attributes): subclass = attributes['subclass']
        theNewObj = object()
        theNewObj.myClassName = subclass
        insertAtStackTop(theNewObj)
        nodeStack.append(theNewObj)

    else:
        trace(0, "Unknown incoming element: '%s'." % (name))
    return

def insertAtStackTop(value):
    """Add the given value to the innermost open COLLECTION (that
    should be the stack top). If the stack is empty, we push the new thing
    if it's an aggregate, otherwise push a generic list?
    """
    global pendingName
    if (not nodeStack): return  # Should be only at very beginning
    if (isinstance(nodeStack[-1], list)):
        nodeStack[-1].append(value)
    elif (isinstance(nodeStack[-1], dict)):
        nodeStack[-1][pendingName] = value
        pendingName = None
    else:
        raise ValueError("stack top is a %s, not list of dict, inserting '%s'." %
            (type(nodeStack[-1]), value))

def EndElementHandler(name):
    group = TagGroup.getOurGroup(name)
    if (group == 'COLLECTION'):
        nodeStack.pop()
    elif (group == 'DICTITEM'):
        pass
    elif (group == 'SCALAR'):
        pass
    else:
        pass  # empty elements
    return

def CharacterDataHandler(data):
    if (not re.match(r'\S', data)):  # whitespace-only
        return
    else:
        if (not nodeStack):
            raise("Found data outside any element: '%s'." % (data))
    #trace(1, "CharacterData: got '%s'" % (data))
    insertAtStackTop(data)
    return


###############################################################################
#
if  __name__ == "__main__":
    import argparse

    def processOptions():
        parser = argparse.ArgumentParser(
            description=descr,
            #formatter_class=MarkupHelpFormatter
        )
        parser.add_argument(
            "--iencoding",         type=str, default='utf-8',
            help='Assume this input character encoding.')
        parser.add_argument(
            "--quiet", "-q",       action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v",     action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version",           action='version',
            version="%s (Python %s)" % (__version__, sys.version_info[0]),
            help='Display version information, then exit.')

        parser.add_argument(
            'charSpecs',           type=str,
            nargs=argparse.REMAINDER,
            help='...')

        args0 = parser.parse_args()

        return(args0)

    ###########################################################################
    # Main
    #
    args = processOptions()

    a = {
        'a': None,
        'b': False,
        'c': True,
        'd': 32767,
        'e': 3.1415926,
        'f': 1.0+2.4j,
        'g': [ 10, 20, 30, 40 ],
        'g2': [ 1, True, 3 ],
        'h': { 'aardvark':1, 'basilisk':2, 'catoblepas':None,
               'dictWithin': { 'aa': 11, 'bb': 22 },
             },
        'i': [ [ 1, 2, 3 ], [ 4, 5, 6 ], [ 7, 8, 9 ], [ 10, 11, 12 ] ],
        'j': ( 'tuple1', 'tuple2', 'tuple3', 'tuple4' ),
        'k': defaultdict(int),
        'l': set([99, 98, 97]),
    }

    print("\n******* encoding some data *******")
    theXML = NANOXEncoder.encode(a)
    print(theXML)

    print("\n\n%s\n" % ('#' *79))
    d = defaultdict(int)
    d['cat'] = 'mouse'
    d['dog'] = 'cat'

    print("\n******* encoding some other data *******")
    print(NANOXEncoder.encode(d))

    print("\n\n%s\n" % ('#' *79))
    print("\n******* decoding some data *******")
    thePythonThing = NANOXDecoder.decode(theXML)
    print(thePythonThing)

    print("\n******* pretty-printing the decoded thing *******")
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(thePythonThing)
