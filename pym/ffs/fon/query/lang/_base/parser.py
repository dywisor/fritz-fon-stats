# fritz-fon-stats -- parser base class
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["ParserBase"]

import io
import ply.yacc

import ffs.fon.exc.lang


class ParserBase(object):

    def p_start(self, p):
        '''start : lang'''
        p[0] = p[1]

    @classmethod
    def dict_composition_partial(cls, da, db):
        # d :: k -> u, d = da o db | da :: k -> v, db :: v' -> u
        #
        # map keys from da to values from db:
        #   da :: key -> intermediate_key
        #   db :: intermediate_key -> value
        # intermediate keys that do not exist in db are ignored.
        return {k: db[v] for k, v in da.items() if v in db}

    def build_precedence(self):
        return ()
    # --- end of build_precedence (...) ---

    def __init__(self, lexer):
        super().__init__()

        self.lexer = lexer
        self.precedence = self.build_precedence()

        self.tokens = self.lexer.tokens  # ref

        self.parser = None
        self.parse_error = 0
        self.infile = None
        self.filename = None
    # --- end of __init__ (...) ---

    def reset(self):
        self.lexer.reset()
        self.parse_error = 0
        self.infile = None
        self.filename = None
    # --- end of reset (...) ---

    def build(self, **kwargs):
        kwargs.setdefault("debug", False)
        kwargs.setdefault("write_tables", False)

        self.lexer.build_if_needed(debug=kwargs["debug"])
        self.parser = ply.yacc.yacc(module=self, **kwargs)
    # --- end of build (...) ---

    def build_if_needed(self, **kwargs):
        if self.parser is None:
            self.build(**kwargs)
    # --- end of build_if_needed (...) ---

    def check_error(self):
        return bool(self.parse_error)
    # ---

    def _parse(self, data, **kwargs):
        try:
            parse_ret = self.parser.parse(
                data, lexer=self.lexer.lexer, **kwargs
            )
        except ffs.fon.exc.lang.QueryLangLexError: # as lex_err:
            # self.logger.error(
            #     "{infile}: line {lineno:d}: {msg}".format(
            #         infile=(self.filename or self.infile or "<input>"),
            #         lineno=lex_err.lineno, msg=lex_err.args[0]
            #     )
            # )
            return None
        # --

        if self.parse_error:
            return None
        else:
            return parse_ret
    # --- end of _parse (...) ---

    def parse(self, data, **kwargs):
        self.reset()
        return self._parse(data, **kwargs)
    # --- end of parse (...) ---

    def parse_file(self, infile, filename=None, encoding="utf-8", **kwargs):
        self.reset()
        self.infile = infile
        self.filename = filename or infile

        with io.open(infile, "rt", encoding=encoding) as fh:
            ret = self._parse(fh.read(), **kwargs)

        return ret
    # --- end of parse_file (...) ---

    def handle_parse_error(self, p, tok_idx, message):
        # self.logger.error(
        #     "{infile}: line {lineno:d}: col {col:d}: {msg}".format(
        #         infile=(self.filename or self.infile or "<input>"),
        #         lineno=p.lineno(tok_idx), col=p.lexpos(tok_idx), msg=message
        #     )
        # )

        self.parse_error = 1  # redundant
        p[0] = None
    # --- end of handle_parse_error (...) ---

    def p_error(self, p):
        self.parse_error = 1
        # if not p:
        #     self.logger.error("Unexpected end of input file")
    # ---

# --- end of _ParserBase ---
