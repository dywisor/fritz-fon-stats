# fritz-fon-stats -- fonlist stats entry
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = []

import enum


@enum.unique
class CallType(enum.IntEnum):
    INCOMING          = 1
    INCOMING_MISSED   = 2
    INCOMING_DENIED   = 3
    OUTGOING          = 4
    INCOMING_ONGOING  = 5
    OUTGOING_ONGOING  = 6

    def is_outgoing(self):
        return self.value in {self.OUTGOING, self.OUTGOING_ONGOING}
    # ---

    def is_incoming(self):
        return self.value in {
            self.INCOMING, self.INCOMING_MISSED,
            self.INCOMING_DENIED, self.INCOMING_ONGOING
        }
    # ---

# --- end of CallType ---


class GespraechsDauer(object):
    __slots__ = ["dauer"]

    def __init__(self, dauer):
        super().__init__()
        self.dauer = dauer

    def __str__(self):
        return "{0:d}:{1:02d}".format((self.dauer // 60), (self.dauer % 60))
    # ---
# --- end of GespraechsDauer ---


class AVMRufnummer(object):
    __slots__ = ['nr']

    def __hash__(self):
        return hash(self.nr)

    def __eq__(self, other):
        if isinstance(other, AVMRufnummer):
            return self.nr == other.nr
        else:
            return NotImplemented
    # ---

    def __init__(self, nr):
        super().__init__()
        self.nr = nr
    # --- end of __init__ (...) ---

    def __str__(self):
        return "{nr}".format(nr=self.nr)

    def __repr__(self):
        return "{cls.__name__}({nr!r})".format(cls=self.__class__, nr=self.nr)

# --- end of AVMRufnummer ---


class AVMCaller(AVMRufnummer):
    __slots__ = []
# --- end of AVMCaller ---


class AVMNamedCaller(AVMCaller):
    __slots__ = ['name']

    def __hash__(self):
        return hash((self.nr, self.name))

    def __init__(self, nr, name):
        super().__init__(nr)
        self.name = name

    def __str__(self):
        return "{name}<{nr}>".format(name=self.name, nr=self.nr)
# --- end of AVMNamedCaller ---


class AVMNebenstelle(AVMRufnummer):
    __slots__ = ["desc", "nebenstelle"]

    def __hash__(self):
        return hash((self.nr, self.nebenstelle))

    def __init__(self, nr, desc, nebenstelle):
        super().__init__(nr)
        self.desc = desc
        self.nebenstelle = nebenstelle
    # ---
# --- end of AVMNebenstelle ---


class AVMPhoneStatsEntry(object):
    __slots__ = ["me", "them", "dauer", "datum", "call_type"]

    def __hash__(self):
        return hash((self.me, self.them, self.dauer, self.datum, self.call_type))

    def __init__(self, *, me, them, dauer, datum, call_type):
        super().__init__()
        self.me = me
        self.them = them
        self.dauer = dauer
        self.datum = datum
        self.call_type = call_type
    # --- end of __init__ (...) ---

    def __str__(self):
        call_type = self.call_type

        if call_type.is_incoming():
            fmt_str = "{call_type.name} {me} <-- {them} {datum} : {dauer}"
        else:
            fmt_str = "{call_type.name} {me} --> {them} {datum} : {dauer}"

        return fmt_str.format(
            me=self.me, them=self.them, call_type=call_type,
            datum=self.datum, dauer=self.dauer
        )
    # --- end of __str__ (...) ---

# --- end of AVMPhoneStatsEntry ---
