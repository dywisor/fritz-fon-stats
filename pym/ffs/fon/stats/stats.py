# fritz-fon-stats -- fonlist stats
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["AVMPhoneStats"]

class AVMPhoneStats(object):

    def __init__(self):
        super().__init__()
        self.entries = []
    # ---

    def update(self, reader_data):
        self.entries.extend(reader_data)
    # ---

    def filter(self, filter_func, entries=None):
        if entries is None:
            entries = self.entries

        return filter(filter_func, entries)
    # ---

    def filter_split(self, filter_func, entries=None):
        matched = []
        not_matched = []

        if entries is None:
            entries = self.entries
        # --

        if filter_func is None:
            matched.extend(entries)
        else:
            add_matched = matched.append
            add_not_matched = not_matched.append

            for entry in entries:
                if filter_func(entry):
                    add_matched(entry)
                else:
                    add_not_matched(entry)
                # --
            # --
        # --

        return (matched, not_matched)
    # --- end of filter_split (...) ---

    def get_entries(self):
        return list(self.entries)

# --- end of AVMPhoneStats ---
