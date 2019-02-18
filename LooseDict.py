#!/usr/bin/env python
#
# LooseDict.py: enhance dict to handle case-ignorant or similar lookups.
#
# 2018-09-04: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#     Implement __cmp__
#     Provie functions that do Unicode normalizations.
#
from __future__ import print_function
import sys
import argparse
import unicodedata

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-09-04",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-09-04",
}
__version__ = __metadata__['version_date']

class LooseDict(dict):
    """A dict also indexable by *normalized* keys (but it keeps the exact keys,
    too). See also "Emulating container types":
    https://docs.python.org/2/reference/datamodel.html#emulating-container-types
    """
    def __init__(self, key=None):
        super(LooseDict, self).__init__()
        if (key): self.keyFunction = key
        else: self.keyFunction = str.lower
        self.normKeys = {}  # Map from normalized to real keys

    def __setitem__(self, someKey, value):
        normKey = self.getNormKey(someKey)
        print("in setitem for '%s', norm='%s', val='%s'." % (someKey, normKey, value))
        if (normKey in self.normKeys):
            oldRealKey = self.normKeys[normKey]
            super(LooseDict, self).__delitem__(oldRealKey)
        self.normKeys[normKey] = someKey
        super(LooseDict, self).__setitem__(someKey, value)
        return

    def __getitem__(self, someKey):
        normKey = self.getNormKey(someKey)
        realKey = self.normKeys[normKey]
        return super(LooseDict, self).__getitem__(realKey)

    def getRealKey(self, someKey):
        normKey = self.keyFunction(someKey)
        if (normKey not in self.normKeys): return None
        return self.normKeys[normKey]

    def getNormKey(self, someKey):
        return(self.keyFunction(someKey))

    def __has_key__(self, someKey):
        normKey = self.getNormKey(someKey)
        return (normKey in self.normKeys)

    def clear(self):
        self.normKeys.clear()
        return super(LooseDict, self).clear()

    def copy(self):
        newld = LooseDict(key=self.keyFunction)
        for kk in self.keys():
            newld[kk] = self[kk]
        return newld

    def __iteritems__(self, sortNorm=False, reverse=False):
        """Make Python 2 users happy....
        """
        if (sortNorm):
            skeys = self.keys()
        else:
            skeys = sorted(self.keys(), key=self.getNormKey, reverse=reverse)
        for kk in skeys:  yield kk, self[kk]
        return None

    #def __cmp__(self, dict_):
    #    return self.__cmp__(self.__dict__, dict_)

    @staticmethod
    def nfkd(s):
        return LooseDict.unormalize(s, 'NFKD', ignoreCase=False)

    @staticmethod
    def nfkdi(s):
        return LooseDict.unormalize(s, 'NFKD', ignoreCase=True)

    @staticmethod
    def nfc():
        return LooseDict.unormalize(s, 'NFC', ignoreCase=False)

    @staticmethod
    def nfci(s):
        return LooseDict.unormalize(s, 'NFC', ignoreCase=True)

    @staticmethod
    def unormalize(s, form="NFC", ignoreCase=True
        s2 = unicodedata.normalize('NFKD', s)
        if (case=='I'): s2 = s2..lower()
        return s2


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    descr = """
=head1 Description

A subclass of C<dict> that stores keys and values exactly as passed,
but indexes them under a normalized form, such as folded to lowercase.
For example:

    myDict = LooseDict(key=lower)
    myDict['fooBar'] = 12
    print(myDict['FOOBAR'])

prints "12". C<lower> was specified here, so keys are normalized by
passing them to C<lower>(). This is also the default.
You can specify some other function as needed.
In particular, LooseDict.nfkd(), LooseDict.nfkdi(),
 LooseDict.nfc(), LooseDict.nfci() are provided, to do the eponymous
 Unicode normalizations, plus forcing to lower case for the "i" variants
(see L<https://www.unicode.org/faq/normalization.html>).

There are a few extra methods.
For example, you can get the normalized form of a key:

    print(myDict.getNormKey('FooBaR'))

would print 'foobar'.

For any non-normalized key, you can find what (possibly different)
key was last used to store data under the same B<normalized> key. For example:

    myDict['fooBar'] = 2
    myDict['FoobaR'] = 4
    print(myDict.getRealKey('fOOBAr'))

would print 'FoobaR', since all these arguments normalized to the same
normKey ('foobar').

Note that entries must still be unique with respect to their I<normalized>
form. If you do:

    myDict = LooseDict()
    myDict['fooBar'] = 12
    myDict['foobar'] = 10
    myDict['FOOBAR'] = 8

The dict will have just one entry, whose normkey is 'foobar', realKey is 'FOOBAR'
(because it was the last one explicitly set), and value is 8.

    for k, y in myDict.items()
        or
    keylist = myDict.keys()

will get you the real (not normalized) keys. You can of course normalize
individually using C<getNormKey()>. I<iteritems>() is a Python 2 thing; the
underlying I<__iteritems__>() is implemented directly in this class,
however, so is available even in Python 3.

C<__cmp__> uses the regular C<dict> method, so compares on the basis of real
(not normalized) keys. This should perhaps change, at least to allow a choice.

Other dict operations are all intended to work normally. For example:

=over

=item * Setting or getting items with C<[]> should work fine.

=item * 'in' normalizes the key passed, and returns True iff there is an item whose
real key normalizes to that same normalized value.

=item * 'clear' and 'copy' have no notable differences.

=item * 'keys' and 'iteritems' should also work fine.
Both return the I<real> keys,
not the normalized form (of course, you can convert using 'getNormKey').
C<iteritems>() also can be passed C<sortNorm=True> to get
pairs in order of normalized keys (or reversed order if you also pass
C<reverse=True>).


=back


=head1 Related Commands

=head1 Known bugs and Limitations

Changing the key-normalizing function on an existing instance is not supported.

The normalizer function must be idempotent. That is, after being applied once,
additional applications should make no further changes. Or in other words,
normalizing an already-normalized key should not denormalize it.

=head1 Licensing

Copyright 2018-09-04 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

=head1 Options
"""
    def processOptions():
        try:
            from MarkupHelpFormatter import MarkupHelpFormatter
            formatter = MarkupHelpFormatter
        except ImportError:
            formatter = None
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=formatter)

        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    print("Testing...")

    ld = LooseDict()
    ld['foobar'] = 12
    ld['FOOBar'] = 10
    ld['FoObAr'] = 8

    for k, v in ld.__iteritems__():
        print("    '%s': %s" % (k, v))

    if (not args.quiet):
        sys.stderr.write("Done.\n")
