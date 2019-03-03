# fritz-fon-stats -- query lang lexer
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["FilterLangLexer"]

import ffs.fon.query.lang._base.lexer


class FilterLangLexer(ffs.fon.query.lang._base.lexer.LexerBase):

    t_ignore = ' \t'

    def build_reserved(self):
        reserved = super().build_reserved()

        reserved.update({
            "true":             "KW_TRUE",
            "false":            "KW_FALSE",

            '!=':               "NE",
            '>=':               "GE",
            '<=':               "LE",
            '>':                "GT",
            '<':                "LT",
            '==':               "EQ_CMP",
            '=':                "EQ",
            '~':                "APPROX",

            '&&':               "AND",
            "and":              "AND",
            '||':               "OR",
            "or":               "OR",
            '!':                "NOT",
            "not":              "NOT",
        })

        reserved.update({
            "incoming":         "KW_INCOMING",
            "outgoing":         "KW_OUTGOING",

            "missed":           "KW_MISSED",
            "denied":           "KW_DENIED",

            "dev":              "KW_DEV",
            "on":               "KW_ME",
            "nr":               "KW_THEM",
            "name":             "KW_NAME",

            "duration":         "KW_DURATION",

            "since":            "KW_SINCE",
            "before":           "KW_BEFORE",
            "between":          "KW_BETWEEN",

            "for":              "KW_FOR",
            "days":             "KW_DAYS",

            "today":            "KW_TODAY",
            "yesterday":        "KW_YESTERDAY",
            "week":             "KW_WEEK",

            "any":              "KW_ANY",

            "known":            "KW_KNOWN",
            "unknown":          "KW_UNKNOWN",
            "foreign":          "KW_FOREIGN",
            "mobile":           "KW_MOBILE",
            "mobil":            "KW_MOBILE",
            "cell":             "KW_MOBILE",
        })

        return reserved
    # --- end of build_reserved (...) ---

    def build_tokens(self):
        tokens = super().build_tokens()

        tokens.extend([
            "LPAREN",
            "RPAREN"
        ])

        return tokens
    # --- end of build_tokens (...) ---

    def t_LPAREN(self, t):
        r'\('
        return self.emit_reset_cmd_end(t)

    def t_RPAREN(self, t):
        r'\)'
        return self.emit_reset_cmd_end(t)

    def t_op_twochars_eq(self, t):
        r'[\<\>\=\!][\=]'
        t.type = self.reserved[t.value]
        return self.emit_reset_cmd_end(t)

    def t_op_onechar(self, t):
        r'[\<\>\=\!\~]'
        t.type = self.reserved[t.value]
        return self.emit_reset_cmd_end(t)

    def t_op_and(self, t):
        r'\&\&'
        t.type = self.reserved[t.value]
        return self.emit_reset_cmd_end(t)

    def t_op_or(self, t):
        r'\|\|'
        t.type = self.reserved[t.value]
        return self.emit_reset_cmd_end(t)

# --- end of FilterLangLexer ---
