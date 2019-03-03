# fritz-fon-stats -- filters
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = []

import abc
import operator
import re


class FilterFunc(object, metaclass=abc.ABCMeta):
    __slots__ = []

    @abc.abstractmethod
    def __call__(self, entry):
        raise NotImplementedError(self)

    def describe(self, *, level=0, indent_str="  "):
        return "\n".join(
            ((level * indent_str) + desc)
            for level, desc in self.gen_describe(level)
        )
    # ---

    @abc.abstractmethod
    def gen_describe(self, level):
        raise NotImplementedError(self)

    def flatten(self):
        return self

    def __repr__(self):
        return "{cls!r}".format(cls=self.__class__)

# ---

class FilterWrapperFunc(FilterFunc):
    __slots__ = ['func']

    def __init__(self, func):
        if not isinstance(func, FilterFunc):
            raise TypeError(func)

        super().__init__()
        self.func = func
    # --- end of __init__ (...) ---

    def __repr__(self):
        return "{cls!r}->{func!r}".format(cls=self.__class__, func=self.func)

    def flatten(self):
        flat_func = self.func.flatten()
        if flat_func is self.func:
            return self
        else:
            return self.__class__(self.func.flatten())
    # ---

# --- end of FilterWrapperFunc ---


class CompoundFilterFunc(FilterFunc):
    __slots__ = ['funcs']

    def __init__(self, *args):
        if not args:
            raise TypeError(self)
        elif len(args) == 1:
            if isinstance(args[0], (list, tuple, set)):
                funcs = list(args[0])
            else:
                raise TypeError(args, "at least 2 functions are required")
        else:
            funcs = list(args)

        items_bad_type = [f for f in funcs if not isinstance(f, FilterFunc)]
        if items_bad_type:
            raise TypeError(items_bad_type)

        super().__init__()
        self.funcs = funcs
    # --- end of __init__ (...) ---

    def flatten(self):
        my_cls = self.__class__

        flattened = False
        funcs = []

        for orig_func in self.funcs:
            func = orig_func.flatten()

            if func.__class__ is my_cls:
                funcs.extend(func.funcs)
                flattened = True
            else:
                funcs.append(func)
                if func is not orig_func:
                    flattened = True
                # --
            # --
        # --

        if len(funcs) == 1:
            return funcs[0]
        elif flattened:
            return my_cls(funcs)
        else:
            return self
    # ---

    def __repr__(self):
        return "{cls!r}<{funcs!r}>".format(cls=self.__class__, funcs=self.funcs)

# --- end of CompoundFilterFunc ---


class SimpleCompoundFilterFunc(CompoundFilterFunc):
    __slots__ = []
    # pylint: disable=no-self-argument

    @abc.abstractmethod
    def COND_DESC(cls):
        raise NotImplementedError(cls)

    @abc.abstractmethod
    def COND_FUNC(cls):
        raise NotImplementedError(cls)
    # ---

    def gen_describe(self, level):
        yield (level, "{}(".format(self.COND_DESC))
        for func in self.funcs:
            yield from func.gen_describe(level + 1)
        yield (level, ")")
    # ---

    def __call__(self, entry):
        # pylint: disable=too-many-function-args
        return self.COND_FUNC((f(entry) for f in self.funcs))
    # --- end of __call__ (...) ---

# --- end of SimpleCompoundFilterFunc ---


class FilterAttrCheckBase(FilterFunc):
    __slots__ = ['attr_name', 'attr_getter', 'weak']

    def quote_value(self, val):
        if isinstance(val, str):
            return "\"{}\"".format(val.replace("\"", ("\\" + "\"")))
        else:
            return val

    def __init__(self, attr_name, weak=False):
        super().__init__()
        self.attr_name = attr_name
        self.attr_getter = operator.attrgetter(self.attr_name)
        self.weak = weak
    # --- end of __init__ (...) ---

    def gen_describe(self, level):
        yield (level, "AttrCheck({0})".format(self.attr_name))

    @abc.abstractmethod
    def attr_check(self, value):
        raise NotImplementedError(self)
    # ---

    def __call__(self, entry):
        try:
            value = self.attr_getter(entry)
        except AttributeError:
            if self.weak:
                return False
            raise
        else:
            return self.attr_check(value)
    # --- end of __call__ (...) ---

# --- end of FilterAttrCheckBase ---


class FilterAttrCmpBase(FilterAttrCheckBase):
    __slots__ = ['expected_value']
    # pylint: disable=no-self-argument

    @abc.abstractmethod
    def CMP_DESC(cls):
        raise NotImplementedError(cls)
    # ---

    def gen_describe(self, level):
        yield (
            level,
            "{desc}(${name}, {val})".format(
                desc=self.CMP_DESC,
                name=self.attr_name,
                val=self.quote_value(self.expected_value)
            )
        )

    def __init__(self, attr_name, expected_value, **kwargs):
        super().__init__(attr_name, **kwargs)
        self.expected_value = expected_value

    @abc.abstractmethod
    def attr_cmp(self, a, b):
        raise NotImplementedError(self)

    def attr_check(self, value):
        return self.attr_cmp(value, self.expected_value)
    # ---
# --- end of FilterAttrCmpBase ---


class FilterHasAttr(FilterFunc):
    __slots__ = ["attr_name", "attr_getter"]

    def __init__(self, attr_name):
        super().__init__()
        self.attr_name = attr_name
        self.attr_getter = operator.attrgetter(self.attr_name)
    # ---

    def gen_describe(self, level):
        yield (level, "HAS(${})".format(self.attr_name))

    def __call__(self, entry):
        try:
            value = self.attr_getter(entry)
        except AttributeError:
            return False

        if value is None:
            return False
        elif isinstance(value, str):
            return bool(value)
        else:
            return True
    # ---
# --- end of FilterHasAttr ---


class FilterAttrCaseEq(FilterAttrCmpBase):
    __slots__ = []

    CMP_DESC = "AttrStrCaseEqual"

    def attr_cmp(self, a, b):
        return a.lower() == b.lower()
# ---

class FilterAttrRegexp(FilterAttrCheckBase):
    __slots__ = ['regexp']

    CMP_DESC = "AttrRegexpMatch"

    def gen_describe(self, level):
        yield (
            level,
            "{desc}(${name}, {val})".format(
                desc=self.CMP_DESC,
                name=self.attr_name,
                val=self.quote_value(self.regexp.pattern)
            )
        )

    def __init__(self, attr_name, regexp_str, flags=0, **kwargs):
        super().__init__(attr_name, **kwargs)
        self.regexp = re.compile(regexp_str, flags=flags)
    # ---

    def attr_check(self, value):
        return (self.regexp.search(value) is not None)
    # ---
# --- end of FilterAttrRegexp ---


class FilterAttrCmpFunc(FilterAttrCmpBase):
    __slots__ = ["cmp_func"]

    @property
    def CMP_DESC(self):
        return "Attr{}".format(self.cmp_func.__name__.upper())

    def attr_cmp(self, a, b):
        return self.cmp_func(a, b)

    def __init__(self, attr_name, cmp_func, expected_value, **kwargs):
        super().__init__(attr_name, expected_value, **kwargs)
        self.cmp_func = cmp_func
    # ---
# ---


class FilterAttrIn(FilterAttrCmpBase):
    __slots__ = []

    CMP_DESC = "AttrIn"

    def gen_describe(self, level):
        yield (
            level,
            "{desc}(${name}, {{{val}}})".format(
                desc=self.CMP_DESC,
                name=self.attr_name,
                val=", ".join(
                    self.quote_value(val) for val in sorted(self.expected_value)
                )
            )
        )

    def __init__(self, attr_name, expected_value, **kwargs):
        super().__init__(attr_name, set(expected_value), **kwargs)

    def attr_cmp(self, a, b):
        return a in b
    # ---
# --- end of FilterAttrIn ---


class FilterOR(SimpleCompoundFilterFunc):
    __slots__ = []
    COND_DESC = "OR"
    COND_FUNC = any
# --- end of FilterOR ---


class FilterAND(SimpleCompoundFilterFunc):
    __slots__ = []
    COND_DESC = "AND"
    COND_FUNC = all
# --- end of FilterAND ---


class FilterNOT(FilterWrapperFunc):
    __slots__ = []

    def flatten(self):
        my_cls = self.__class__

        func = self.func.flatten()

        # not not (x) <=> (x)
        if func.__class__ is my_cls:
            return func.func
        elif func is self.func:
            return self
        else:
            return my_cls(func)
    # ---

    def gen_describe(self, level):
        yield (level, "NOT(")
        yield from self.func.gen_describe(level + 1)
        yield (level, ")")

    def __call__(self, entry):
        return (not self.func(entry))
    # ---
# --- end of FilterNOT ---


class _FilterCallType(FilterAttrCheckBase):
    __slots__ = []

    def __init__(self):
        super().__init__("call_type", weak=False)

# --- end of _FilterCallType ---


class FilterCallIncoming(_FilterCallType):
    __slots__ = []

    def gen_describe(self, level):
        yield (level, "CallIncoming")

    def attr_check(self, call_type):
        return call_type.is_incoming()
# --- end of FilterCallIncoming ---


class FilterCallOutgoing(_FilterCallType):
    __slots__ = []

    def gen_describe(self, level):
        yield (level, "CallOutgoing")

    def attr_check(self, call_type):
        return call_type.is_outgoing()
# --- end of FilterCallOutgoing ---


class FilterTrue(FilterFunc):
    __slots__ = []

    def gen_describe(self, level):
        yield (level, "TRUE")

    def __call__(self, entry):
        return True
# --- end of FilterTrue ---


class FilterFalse(FilterFunc):
    __slots__ = []

    def gen_describe(self, level):
        yield (level, "FALSE")

    def __call__(self, entry):
        return False
# --- end of FilterFalse ---
