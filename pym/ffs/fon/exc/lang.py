# fritz-fon-stats -- query lang exceptions
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = []


class QueryLangLexError(ValueError):
    pass


class LexInvalidCharError(QueryLangLexError):
    pass
