# fritz-fon-stats -- lexer base class
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["LexerBase"]


import ply.lex
import re

import ffs.fon.exc.lang


class LexerBase(object):

    def build_reserved(self):
        reserved = {}

        return reserved
    # --- end of build_reserved (...) ---

    def build_tokens(self):
        tokens = ["STR"]
        tokens.extend(set(self.reserved.values()))

        return tokens
    # --- end of build_tokens (...) ---

    def __init__(self):
        super().__init__()

        self.regexp_escape_seq = re.compile(r'[\\]([.])')

        self.reserved = self.build_reserved()
        self.tokens = self.build_tokens()

        self.lexer = None
    # ---

    def reset(self):
        pass
    # --- end of reset (...) ---

    def build(self, **kwargs):
        kwargs.setdefault("debug", False)
        self.lexer = ply.lex.lex(module=self, **kwargs)
    # --- end of build (...) ---

    def build_if_needed(self, **kwargs):
        if self.lexer is None:
            self.build(**kwargs)
    # --- end of build_if_needed (...) ---

    def input(self, *args, **kwargs):
        self.reset()
        self.lexer.input(*args, **kwargs)
    # --- end of input (...) ---

    def token(self):
        return self.lexer.token()
    # --- end of token (...) ---

    def unescape_quoted_str(self, s):
        """This method replaces escape sequences in a str with their
        unescaped value.

        @param s:  input str
        @type  s:  C{str}

        @return:   output str
        @rtype:    C{str}
        """
        return self.regexp_escape_seq.sub(r'\1', s[1:-1])

    def unquote_tok(self, t):
        """
        This method unquotes the value of a token and sets its type to "STR".

        @param t:  token
        @type  t:  LexToken

        @return:   input token, modified
        @rtype:    LexToken
        """
        t.value = self.unescape_quoted_str(t.value)
        t.type = "STR"
        return t

    def emit_reset_cmd_end(self, t):
        return t

    def t_DQSTR(self, t):
        r'"([\\].|[^"\\])*"'
        return self.emit_reset_cmd_end(self.unquote_tok(t))

    def t_SQSTR(self, t):
        r"'([\\].|[^'\\])*'"
        return self.emit_reset_cmd_end(self.unquote_tok(t))

    def t_STR(self, t):
        r'[a-zA-Z0-9\_\-\+\.\/\*]+'
        slow = t.value.lower()
        try:
            stype = self.reserved[slow]
        except KeyError:
            pass
        else:
            t.value = slow
            t.type = stype
        # --
        return self.emit_reset_cmd_end(t)

    def t_error(self, t):
        raise ffs.fon.exc.lang.LexInvalidCharError(
            t.lineno, t.lexpos, t.value[0]
        )

# --- end of LexerBase ---
