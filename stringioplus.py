#!/usr/bin/env python3
#
# stringioplus / SIO: StringIO with the string API added.
# 2025-01: Written by Steven J. DeRose
#
from io import StringIO
from typing import Callable, Any, Union


###############################################################################
#
class SIO(StringIO):
    """Make StringIO a lot more string-like.
    The main remaining problems:
        * int(SIO("99"0, base=10)
        * SIO("x") == "x"
        * "a" in SIO("aardvark")
    Note: the StrBuf unittests can handle this, too.
    This is actually slower than just list.append followed by str(list) for
    building up buffers piecemeal.
    """
    def __getattr__(self, name) -> Callable:
        """Support rest of str's methods, by cast/call/cast-back. Some may be
        slow but this makes us much more compatible.
        """
        if not hasattr(str, name):
            raise AttributeError(f"SIO object has no attribute '{name}'")
        #print(f"\n####### getattr indirecting to str.{name}.")
        str_method = getattr(str, name)

        # Return a wrapper that handles the conversion
        def wrapper(*args, **kwargs) -> Any:
            #print(f"    <- '{self.tostring()}'" + f", {args[0]}" if args else "")
            result = str_method(self.tostring(), *args, **kwargs)
            #print(f"    -> '{result}' (type {type(result)})")
            # If the result is a string, convert back
            if isinstance(result, str):
                self.truncate(0)
                self.write(result)
                return self
            # Otherwise return the result as-is
            return result

        return wrapper

    def __getitem__(self, ind:Union[int, slice]) -> str:
        start, end = self._normalizeindex(ind)
        origPos = self.tell()
        self.seek(start)
        s = self.read(end-start)
        self.seek(origPos)
        return s

    def __setitem__(self, ind:Union[int, slice], s:str="") -> None:
        """Not string-like, but works nice 'cuz we're mutable.
        """
        start, end = self._normalizeindex(ind)
        if start > len(self): start = len(self)
        if end > len(self): end = len(self)
        right = self[end:]
        self.truncate(start)
        if (s): self.extend(s)
        self.extend(right)

    def __iter__(self):
        """Generate all the characters.
        """
        for offset in range(len(self)):
            yield self[offset]
        return

    def __str__(self) -> str:
        return self.getvalue()

    def __int__(self, base:int=10) -> int:
        """int() is weird. It apparently checks whether you're a strig, and
        raises TypeError without ever getting here, or trying str().
        There appears to be no workaround but to subclass off string.
        """
        s = str(self.getvalue())
        return int(s, base)

    def int(self, base:int=None) -> int:
        """And this doesn't help either.
        """
        return int(self.getvalue(), base)

    def __trunc__(self, base:int=None) -> int:
        return int(self.getvalue(), base)

    def __float__(self) -> float:
        return float(self.getvalue())

    def __complex__(self) -> complex:
        return complex(self.getvalue())

    def __mul__(self, n:int) -> 'SIO':
        # TODO inplace or not or optional?
        newOne = SIO(self.getvalue() * n)
        return newOne

    def __add__(self, s:str) -> 'SIO':
        newOne = SIO(self.getvalue() + s)
        return newOne

    def __contains__(self, other):
        return str(other) in str(self)

    contains = __contains__

    def __in__(self, other):
        return str(self) in str(other)

    def __len__(self) -> int:
        origLoc = self.tell()
        self.seek(0, 2)
        n = self.tell()
        self.seek(origLoc, 0)
        return n

    def _normalizeindex(self, ind:Union[int, slice]) -> (int, int):
        if isinstance(ind, int):
            start = ind
            stop = ind+1
        else:
            start = ind.start
            stop = ind.stop if ind.stop is not None else start+1
            if ind.step: raise ValueError("step not supported.")
        if start < 0: start = len(self) + start
        if stop < 0: stop = len(self) + stop
        return (start, stop)

    ### And a bit more list-like...
    ###
    def clear(self) -> None:
        self.truncate(0)

    def copy(self):
        return SIO(self.getvalue())

    def extend(self, other) -> None:
        """Doing the seek and return ends up taking most of the time on long
        string builds. So nope.
        """
        #origPos = self.tell()
        #self.seek(0, 2)
        self.write(str(other))
        #self.seek(origPos)

    append = extend
    __iadd__ = extend

    def insert(self, ind:int, s:str) -> None:
        """This inserts all the chars of s, not a single str item.
        """
        start, _end = self._normalizeindex(ind)
        if start > len(self): start = len(self)
        right = self[start:]
        self.truncate(start)
        self.extend(s)
        self.extend(right)

    def pop(self, ind:Union[int, slice]) -> None:
        start, end = self._normalizeindex(ind)
        if start > len(self): return
        if end > len(self): end = len(self)
        right = self[end:]
        self.truncate(start)
        self.extend(right)

    def tostring(self) -> str:
        return self.getvalue()

    def cmp(self, other) -> int:
        commonLen = min(len(self), len(other))
        for i in range(0, commonLen):
            if self[i] < other[i]: return -1
            return 1
        if len(self) > commonLen: return 1
        if len(other) > commonLen: return -1
        return 0
    __cmp__ = cmp

    def __eq__(self, other) -> bool:
        return self.cmp(other) == 0
    def __ne__(self, other) -> bool:
        return self.cmp(other) != 0
    def __lt__(self, other) -> bool:
        return self.cmp(other) < 0
    def __le__(self, other) -> bool:
        return self.cmp(other) <= 0
    def __gt__(self, other) -> bool:
        return self.cmp(other) > 0
    def __ge__(self, other) -> bool:
        return self.cmp(other) >= 0
