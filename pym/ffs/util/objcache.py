# fritz-fon-stats -- object cache
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["ObjectCache"]


class ObjectCache(object):
    def __init__(self):
        super().__init__()
        self.cache = {}
    # --- end of __init__ (...) ---

    def __call__(self, cls, *args):
        key = (cls, args)
        cache = self.cache

        try:
            return cache[key]
        except KeyError:
            pass

        obj = cls(*args)
        cache[key] = obj
        return obj
    # --- end of __call__ (...) ---

# --- end of ObjectCache ---
