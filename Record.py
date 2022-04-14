#!/usr/bin/env python3
#
# Record.py: A cross between namedtuple and dict.
# Written 2018-06-09 by Steven J. DeRose (nee `DictTuple`).
#
import re
from collections import namedtuple
from enum import Enum
from typing import Union, Any, Dict

__metadata__ = {
    'title'        : "Record",
    'description'  : "A cross between namedtuple and dict.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2018-06-09",
    'modified'     : "2020-10-21",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

''UNFINISHED''

The "Record" class is a collection of data items, that conform to certain
constraints. The contraints are specified by a RecordDef, which can
specify a lisst of field, and for each field (all optional except the name):

* a name,
* a datatype
* whether subclass of that datatype are ok
* a default value
* whether None is ok
* how to format() the value
* what order the field comes in (normally defaulted)

In addition, the RecordDef may specify that one or more fields constitute
a key, which should be used to uniquely identify each Record instance with
that RecordDef.

Having made a RecordDef, you can instantiate Records, simply naming the
applicable RecordDef as an argument to the constructor.

Record is a subclass of ''dict'', but adds properties of ordereddict,
namedtuple, defaultdict, and object:

* Like a regular ''dict'', Records are mutable, and the members are unordered.

* Somewhat like ''ordereddict', a reliable order of fields is available.
But it is the order of definition, not last set, so is consistent across all
Records with the same RecordDef.

* Like ''namedtuple'', it knows a specific
set of named fields, and ionstances can contain only those fields.

* Like ''defaultdict'', you can set a default, but for each field.

* Like none of these, you can (optionally) specify a datatype for each field,
and whether an assigned value must be exactly that type, a subclass,
or CAST (not yet finished).

* You can also specify whether None is an acceptable value.


==RecordDef==

To define a type of record, instantiate a RecordDef, passing a name and
a list of the specific
fields that can or must be stored in it. This is much like ''namedtuple''
except that each field may specify more than just
a name, and the result is an instance of RecordDef, not a new class.

For the list of specific fields, you can pass a `list` or a `dict`:

* For a list, each item can be:
** a string field name (all constraints default); or
** a (sub)list with constraints in order (see the `FieldInfo` namedtuple).

* If it's a dict, the keys are fieldNames, which will be added in
alphabetical order. Each value can be either:
** None
** a list as just described, or
** a dict mapping fieldnames to constraints named as follow
(see also the `FieldInfo` namedtuple):

Each field can have the following features (all but the first can be defaulted):

* `name`: a string that is the key used to identify this field
in instances of the Record. Required, and must be unique.

* `type`: an actual type to constrain the values that may be set for the
field of the given 'name'. if 'type' is omitted or 'None', any type is allowed.

* `subs`: one of three values (only meaningful is a type is specified;
the default is CAST):
** STRICT: only values of exactly the specified type are allowed
** SUB: values of subclasses are also allowed
** CAST: any value CAST to the speciied type are allowed

* `defaultValue`: if the field is missing, requests for it return this
value (which should be of an acceptable 'type'. If not specified,
requesting a missing field raises KeyError, just as with a dict or namedtuple.

* `nil`: If True, "None" is an acceptable value for the field.

* `fmt`: How to format the field for output (typically a %-code).

* `seq`: [internal] -- this is the generated sequence number for the field.
To change field order, see `RecordDef.setOrder()`.

For example, to define a Record type consisting of 5 fields, the first
four of specific types, and the last allowing anything, and with the
last three having default values:

    EmpRecord = RecordDef('EmpRecord', [
        [ 'fullName', str ],
        [ 'age'     , int ],
        [ 'gender'  , str,   SubsValues.STRICT, None ],
        [ 'salary'  , float, SubsValues.STRICT, 1.0 ],
        [ 'userdata', None,  SubsValues.CAST, None ]
    ])

==Record==

Once a RecordDef is created, you can make instances of the Record class,
which have the RecordDef attached and so enforce the constraints.
You can set all the values at once (in the order
they were given for the RecordDef constructor:

    employee1 = Record(EmpRecord, ['Pat Smith', 30, 'M', 100000])

or set them piecemeal:

    employee2 = Record(EmpRecord)
    employee2['fullName'] = 'Chris Jones'
    employee2['age'] = 40
    employee2['gender'] = 'F'
    employee2['salary'] = 100000

In order to allow piecemeal or even deferred setting of the fields, creating
a Record with some fields not set is not an error. The error would arise on
setting an impermissible field value, or deleting rather than
changing a required field. You can also check for validity with isValid(),
which will complain if any required fields have not (yet) been set.

Because Records are mutable, you can update particular fields:

    employee1['fullName'] = 'Pat Smith-Robinson'

or

    employee1.fullName = 'Pat Smith-Robinson'

==Key fields==

Being mutable means Record objects cannot be used as keys for dicts. You
cannot say:

    employees[employee1] = employee1

You could say:

    employees[employee1.fullName] = employee1

but in that case, you really don't want to change the 'fullName' field, lest
your employee list be keyed by an obsolete value. To protect against that, you
can declare that a certain field is considered a key, and may not be changed
(at least by normal assignment):

       employeeRecord = RecordDef('MyClass', [
        [ 'fullName', str],
        [ 'age'     , int ],
        [ 'gender'  , str,   None, True  ],
        [ 'salary'  , float,  1.0, True  ],
        [ 'userdata', None,  None, True  ]
    ], key = 'fullName')

The value given for 'key' when defining the Record subclass, must be one of
the defined field names, or a list containing one or more field names. In
the latter case, none of the listed fields may be changed, and getKey()
returns a tuple of them in the specified order.


    employees = Dict
    employees[


This 4-tuple of features for each permitted item is internally stored
as an instance of a named tuple called ''FieldInfo''.
You can make these ahead of time, or just pass in lists or tuples of the 4 features as shown above.


=Methods=


=Related Commands=

`Homogeneous.py`, `LooseDict.py`.


=Known bugs and limitations=

'''Unfinished'''

Need to be clear about the notion of constraining what keys are allowed in the
dict, and what the structure of the values is.


=To do=

* Do a similar class, but immutable, so basically just adding type-checking
to namedtuple?
* Hook up directly to `Datatypes.py`.
* Perhaps package with hookup to argparse to use for package option mgmt?


=History=

* 2018-06-09: Written by Steven J. DeRose.
* 2020-09-08: Add Strictness as Enum. Add 'format' to FieldInfo.
Add prettyPrint().
* 2020-10-21: Rename Strictness to SubsValues, shorten fieldInfo prop names.


=Rights=

Copyright 2018-06-09 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
# Where we store meta-info about each allowed Record entry.
#
FieldInfo = namedtuple('FieldInfo', [
    'name',         # String field name
    'type',         # Datatype expected (None for any)
    'subs',         # Are subclasses or castable values ok?
    'default',      # Default value if requested but not set
    'nil',          # Is None an acceptable value?
    'fmt',          # How to format it for output ("%12.6f" or similar)
    'seq',          # Was this field defined first or second or what?
    ])

class SubsValues(Enum):
    ONLY = 0
    SUBS = 1
    CAST = 2

def makeFieldInfo(
    name:str,
    typ:type = None,
    subs     = SubsValues.CAST,
    dft      = None,
    nil:bool = True,
    fmt      = None,
    seq      = None
    ):
    assert (name.isalnum)
    assert (isinstance(typ, type) or typ is None)
    sv = int(subs)
    assert (sv in [ 0, 1, 2 ])
    if (typ is not None):
        assert (isinstance(dft, type) or typ is None)
    assert (fmt is None or FormatField.isFormatSpec(fmt))
    return FieldInfo(name, typ, subs, dft, nil, fmt, seq)


###############################################################################
#
class FormatField:  #  cf FormatRec(). Move to Datatypes?
    """A format spec can include:
    * Minimum width (how to pad)
    * Maximum width (how to chop)
    * Absolute width (just set min/max?)
    * Justification (l/c/r/dec)
    * Char encoding?
    *
    * For None: string to use
    * For Bool: string to use
    * For numbers:
    *    Base
    *    Sign (none, negativeOnly, always)
    *    Flag negative via (), red, etc.
    *    Commas (or other seps)
    *    KMGTPX notation
    *    Unit suffix (and whether to scale units)
    * Reals:
    *    Exponential notation
    *    Post-decimal digits
    *    Round vs. truncate
    *    percent and permil
    * Complex
    *    i vs. j
    * For strings
    *    truncate/wrap
    *    quote
    *    escaping (showInvisible, entities, etc)
    * DatesTimes -- a la strftime?
    *    Named forms
    """
    @staticmethod
    def isFormatSpec(s):
        if (re.match(r'%-?\d+(\.\d+)[bcdefgx]', s)): return True


###############################################################################
#
class RecordDef():
    """A class representing the set of constraints on a given Record, such
    as the permitted field names, their types, defaults, etc.

    Define a certain set of entries/fields (by name and type),
    each represented as a FieldInfo that gives its properties. The
    definition object is attached to Record instances.

    @param name: Just a name for the record type.
    @param fields: specifies the fields allowed, and their constraints,
        as a list or a dict. See the help for details.
    @param keyFields is a list of field names, together defining a key.
        This lets the caller define something like the SQL notion of a compound
        key applicable to Records of the given record type.

    TODO: Add a way to use just parts of fields (esp. strings), or at
    least let user give a function to derive the key from the record.

    Should this be a subclass of list, dict, or tuple? Could be any.
    It doesn't want to be very mutable, so maybe tuple?
    But do people think of "fields" as ordered, so maybe list?
    But we want to encourage names, not numbers, so maybe dict?
    """
    def __init__(self, name: str, fields:list=None, keyFields=None):
        self.name = name
        self.fieldNames = []        # In order matching FieldInfo.seq
        self.fieldInfos = {}        # Index by field name
        self.keyFields = keyFields  # TODO: Allow multiple named keys
        self.locked = False

        if (fields is None):
            return

        if (isinstance(fields, list)):
            for i, fieldInfo in enumerate(fields):
                if (isinstance(fieldInfo, list)):
                    self.defineField(*fieldInfo)
                elif (isinstance(fieldInfo, str)):
                    self.defineField(fieldInfo)
                else:
                    raise ValueError("Field %d of RecordDef '%s' not list|str."
                        % (i, name))

        elif (isinstance(fields, dict)):
            for i, fieldName in enumerate(fields.keys()):
                fieldInfo = fields[fieldName]
                if (fieldInfo is None):
                    self.defineField(fieldName)
                elif (isinstance(fieldInfo, list)):
                    self.defineField(fieldName, *fieldInfo)
                elif (isinstance(fieldInfo, dict)):
                    if ('typ' not in fieldInfo): fieldInfo['typ'] = None
                    if ('subs' not in fieldInfo): fieldInfo['subs'] = None
                    if ('dft' not in fieldInfo): fieldInfo['dft'] = None
                    if ('nil' not in fieldInfo): fieldInfo['nil'] = None
                    if ('fmt' not in fieldInfo): fieldInfo['fmt'] = None
                    self.defineField(
                        fieldName,
                        typ         = fieldInfo['typ'],
                        subs  = fieldInfo['subs'],
                        dft         = fieldInfo['dft'],
                        nil    = fieldInfo['nil'],
                        fmt  = fieldInfo['fmt']
                    )
                else:
                    raise ValueError("Field %d of RecordDef '%s' not list|str."
                        % (i, name))
        else:
            raise ValueError("'fields' arg must be list or dict, not %s." %
                (type(fields)))

        if (self.keyFields):
            for f in self.keyFields:
                if (f not in self.fieldInfos):
                    raise ValueError("Key field '%s' does not exist." % (f))
        #self.locked = True

    def lock(self):
        """Once locked, no more fields can be added to the definition.
        """
        self.locked = True

    def setOrder(self, fieldNames:list):
        """Reset all the seq numbers of the fields, to a new sequence.
        @param fieldNames: The field names, in the order desired.
            If None, the fields are put in alphabetical order.
            Omitted fields go unlisted in the order, and callers may omit
            them, append them at the end, ban them, or whatever they like.
            This list must have exactly the same names already known.
            Add or delete fields first if desired.
        """
        # Make sure the names all exist, no dups.
        if (len(fieldNames) != len(self.fieldNames)):
            raise ValueError("%d fields named, but RecordDef has %d." %
                (len(fieldNames), len(self.fieldNames)))
        checkDict = {}
        for i, f in enumerate(fieldNames):
            if (f not in self.fieldNames):
                raise ValueError("field name '%s' does not exist." % (f))
            if (f in checkDict):
                raise ValueError("duplicate field name '%s'." % (f))
            checkDict[f] = True
        checkDict = None

        # Re-create the fieldInfos with the new Name, seq, and set our
        # ordered list of the names to match.
        self.fieldNames = []
        for i, f in enumerate(fieldNames):
            old = self.fieldInfos[f]
            self.fieldInfos[f] = FieldInfo(
                old.name, old.typ, old.subs,
                old.dft, old.nil, old.fmt, i)
            self.fieldNames[i] = old.name
        return

    def checkOrder(self):
        for i, f in enumerate(self.fieldNames):
            if (f not in self.fieldInfos):
                return False
            if (self.fieldInfos[f].seq != i):
                return False
        return True

    def defineField(self,
        name:str,
        typ:type = None,
        subs     = SubsValues.CAST,
        dft      = None,
        nil:bool = True,
        fmt      = None
        ):
        """Parameters passed should be the same as the items of a FieldInfo
        (except that seq is added automatically).
        """
        if (self.locked):
            raise ValueError("Can't defineField in a locked RecordDef.")
        if (name in self.fieldInfos):
            raise KeyError("item '%s' already defined." % (name))
        seq = len(self.fieldInfos)
        try:
            newFI = makeFieldInfo(name, typ, subs, dft, nil, fmt, seq)
        except ValueError:
            return None
        self.fieldNames.append(name)
        self.fieldInfos[name] = newFI
        return newFI

    def removeField(self, fieldName):
        """This doesn't update instances of this kind of record.
        """
        if (self.locked):
            raise ValueError("Can't removeField in a locked RecordDef.")
        if (fieldName not in self.fieldInfos):
            raise ValueError("Can't remove nonexistent field '%s'." %
                (fieldName))
        theSeq = self.fieldInfos[fieldName].seq
        del self.fieldNames[theSeq]
        del self.fieldInfos[fieldName]
        self.setOrder(self.fieldNames)

    def isValueOK(self, fieldName, value):
        """Test whether a value matches the constraints for the named field.
        """
        if (fieldName not in self.fieldInfos):
            raise KeyError("Field '%s' not defined for RecordDef '%s'." %
                (fieldName, self.name))
        fi = self.fieldInfos[fieldName]
        return self.isValueOfType(fi, value)

    def isValueOfType(self, fi, value):
        if (fi.typ is None):               # no type spec, so take any
            return True

        if (value is None):                # Vaue None, is that ok?
            return fi.nil
        if (fi.subs == SubsValues.CAST):
            try:
                _ = fi.typ(value)
            except ValueError:
                return False
        elif (fi.subs == SubsValues.SUBS):
            if (not isinstance(value, fi.typ)):
                return False
        elif (fi.subs == SubsValues.ONLY):
            if (type(value) != fi.typ):
                return False

        return True


###############################################################################
#
class Record(dict):
    """A subclass of dict that provides a number of features from defaultdict
    and namedtuple as well. It can enforce types for members, allow or
    prohibit None for members, etc.

    To construct and instance, give:
        * An instance of RecordDef, which determines what fields are allowed,
        * the data to fill in:
            * a list: checks and fills the fields in order
            * a dict: checks and fills the fields by name
            * None: check and fill the fields with default or None
    """
    def __init__(self, dfn:RecordDef, data:Union[list, dict, None]=None):
        super(Record, self).__init__()

        if (not isinstance(dfn, RecordDef)):
            raise TypeError("dfn is not a RecordDef.")

        # Initialize the fields with default values
        for fName, fInfo in dfn.fieldInfos.items:
            if (fInfo.dft): self[fName] = fInfo.dft
            else: self[fName] = None

        # If they gave us data, apply it
        self.dfn = dfn
        if (isinstance(data, list)):
            self.setFromList(data)
        elif (isinstance(data, dict)):
            self.setFromDict(data)
        elif (data is not None):
            raise TypeError("Record data must be list, dict, or None.")

    def setFromList(self, data):
        for i, d in enumerate(data):
            fieldName = self.dfn.fields[i]
            self[fieldName] = d

    def setFromDict(self, data:Dict):
        for k, v in enumerate(data):
            fieldName = self.dfn.fieldInfos[k]
            self[fieldName] = v

    def __setitem__(self, key: str, value:Any):
        """Actually store a value, type-checking it on the way.
        See https://stackoverflow.com/questions/2060972/
        """
        if (key not in self.dfn.fields):
            raise KeyError("item '%s' not defined." % (key))
        it = self.dfn.fields[key]
        if (it['type'] and not isinstance(value, it['type'])):
            raise TypeError("value for item '%s' is type %s (need %s)." %
                (key, type(value), it['type']))
        if (value is None and not it['nil']):
            raise TypeError("value for item '%s' may not be None." % (key))
        super(Record, self).__setitem__(key, value)

    def __getitem__(self, key):
        if ('defaultValue' in self.dfn[key]):
            return self.dfn[key]['defaultValue']
        return None

    def isValid(self):
        """Check that this Record is legit.
        TODO: Make sure check for all required/non-default fields.
        """
        for key, value in self.dfn.fields.fields():
            if (key not in self.dfn.fields):
                raise KeyError("item '%s' not defined." % (key))
            if (not self.dfn.isValueOK(key, value)): return False
        return True


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    class Whatev:
        def __init__(self):
            self.x = 1

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')
        parser.add_argument(
            'files', type=str, nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')
        args0 = parser.parse_args()
        return(args0)


    print("Testing Record.py...")
    print("Unfinished")

    args = processOptions()

    EmpRecord = RecordDef('EmpRecord', [
        [ 'fullName', str ],
        [ 'age'     , int ],
        [ 'gender'  , str,   SubsValues.ONLY, True, None ],
        [ 'salary'  , float, SubsValues.ONLY, True,  1.0 ],
        [ 'userdata', None,  SubsValues.CAST, True, None ]
    ])

    employeeRec = Record(EmpRecord, ['Pat Smith', 30, 'M', 100000])
    employee2 = Record(EmpRecord, ['Chris Jones', 40, 'F', 100000])
