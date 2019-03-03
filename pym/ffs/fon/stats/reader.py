# fritz-fon-stats -- fonlist csv reader
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["AVMPhoneStatsReader"]

import csv
import datetime
import re

import ffs.util.objcache

import ffs.fon.stats.entry
from ffs.fon.stats.entry import (
    CallType,
    AVMCaller, AVMNamedCaller, AVMNebenstelle,
    GespraechsDauer,
    AVMPhoneStatsEntry
)


class AVMPhoneStatsReader(object):
    RE_HEADER_SEP = re.compile(r'^sep=(?P<sep>\S)\s*$')
    RE_DAUER = re.compile(r'^(?P<H>\d+)[:](?P<M>\d+)$')
    # Eigene Rufnummer:
    #    sequence of non-empty,non-colon chars  --> %desc
    #    followed by colon and whitespace       --> IGNORE
    #    and a number                           --> %nr
    RE_EIGENE_RUFNUMMER = re.compile(r'^(?P<desc>[^\s:]+)[:]\s+(?P<nr>\d+)$')

    DATUM_FMT = r'%d.%m.%y %H:%M'

    def __init__(self):
        super().__init__()
        self.obj_cache = ffs.util.objcache.ObjectCache()
    # --- end of __init__ (...) ---

    def _create_stats_entry(self, data):
        obj_cache = self.obj_cache  # ref
        data = {k: v.strip() for k, v in data.items()}  # overwrite param

        entry_data = {}

        # me (Nebenstelle/Rufnummer fritz box)
        me_match = self.RE_EIGENE_RUFNUMMER.match(data['Eigene Rufnummer'])
        if me_match is not None:
            entry_data["me"] = obj_cache(
                AVMNebenstelle, me_match.group('nr'), me_match.group('desc'), data['Nebenstelle']
            )
        else:
            raise ValueError("Eigene Rufnummer", data['Eigene Rufnummer'])
        # --


        # them (Name/Rufnummer Gegenstelle)
        if data['Name']:
            entry_data["them"] = obj_cache(
                AVMNamedCaller, data['Rufnummer'], data['Name']
            )
        else:
            entry_data["them"] = obj_cache(AVMCaller, data['Rufnummer'])
        # --

        # call_type
        entry_data["call_type"] = CallType(int(data['Typ'].strip(), 10))

        # dauer
        dauer_match = self.RE_DAUER.match(data['Dauer'])
        if dauer_match is not None:
            entry_data["dauer"] = obj_cache(
                GespraechsDauer,
                (
                    (60 * int(dauer_match.group('H'), 10))
                    + int(dauer_match.group('M'), 10)
                )
            )
        else:
            #entry_data["dauer"] = None
            raise ValueError("Dauer", data['Dauer'])
        # --

        # datum
        entry_data["datum"] = datetime.datetime.strptime(data['Datum'], self.DATUM_FMT)

        # pylint: disable=missing-kwoa
        return AVMPhoneStatsEntry(**entry_data)
    # --- end of _create_stats_entry (...) ---

    def _gen_read_csv_file(self, fh):
        try:
            header_line = next(fh)
        except StopIteration:
            # empty file?
            return
        # --

        sep = None
        header_match = self.RE_HEADER_SEP.match(header_line)
        if header_match is not None:
            sep = header_match.group("sep")
        else:
            raise AssertionError("unexpected file format, missing sep= line")
        # -- get separator

        reader = csv.DictReader(fh, delimiter=sep)
        for row in reader:
            yield self._create_stats_entry(row)
    # --- end of _gen_read_csv_file (...) ---

    def read_csv_file(self, fh):
        for row in self._gen_read_csv_file(fh):
            yield row
    # --- end of read_csv_file (...) ---

# --- end of AVMPhoneStatsReader ---
