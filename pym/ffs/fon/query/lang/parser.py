# fritz-fon-stats -- query lang parser
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["FilterLangParser"]

import datetime
import operator
import re

try:
    import dateutil.parser
except ImportError:
    HAVE_DATEUTIL_PARSER = False
else:
    HAVE_DATEUTIL_PARSER = True

import ffs.fon.query.lang._base.parser

import ffs.util.objcache

import ffs.fon.stats.entry
from ffs.fon.stats.entry import CallType

import ffs.fon.query.filters
from ffs.fon.query.filters import (
    FilterNOT, FilterAND, FilterOR,
    FilterTrue, FilterFalse,
    FilterCallIncoming, FilterCallOutgoing,
    FilterHasAttr, FilterAttrRegexp,
    FilterAttrCmpFunc, FilterAttrCaseEq
)


class FilterLangParser(ffs.fon.query.lang._base.parser.ParserBase):

    def build_precedence(self):
        precedence = (
            (
                "nonassoc",
                "NE", "GE", "LE", "GT", "LT", "EQ_CMP", "EQ"
            ),
            ("right", "NOT"),
            ("left", "AND"),
            ("left", "OR"),
        )

        return (super().build_precedence() + precedence)
    # --- end of build_precedence (...) ---

    def __init__(self, lexer, *args, **kwargs):
        super().__init__(lexer, *args, **kwargs)

        self.regexp_telnummer = re.compile(r'^(?P<nr>\d+)$')
        self.obj_cache = ffs.util.objcache.ObjectCache()

        self.date_today = (
            datetime.datetime.combine(
                datetime.date.today(),
                datetime.time.min
            )
        )

        self.date_op_map = self.dict_composition_partial(
            self.lexer.reserved,
            {
                "KW_TODAY":         None,
                "KW_YESTERDAY":     datetime.timedelta(days=-1),
                "KW_WEEK":          datetime.timedelta(days=-7),
            }
        )

        self.cmp_op_map = self.dict_composition_partial(
            self.lexer.reserved,
            {
                "NE":       operator.__ne__,
                "GE":       operator.__ge__,
                "LE":       operator.__le__,
                "GT":       operator.__gt__,
                "LT":       operator.__lt__,
                "EQ":       operator.__eq__,
                "EQ_CMP":   operator.__eq__,
            }
        )
    # --- end of __init__ (...) ---

    def get_date(self, date_shift=None):
        date_today = self.date_today
        return (date_today + date_shift) if date_shift else date_today
    # ---

    if HAVE_DATEUTIL_PARSER:
        def convert_date(self, arg):
            return dateutil.parser.parse(arg, ignoretz=True, yearfirst=True)
        # --- end of convert_date (...) ---
    else:
        def convert_date(self, arg):
            format_string = "%Y-%m-%d"
            return datetime.datetime.strptime(arg, format_string)
        # --- end of convert_date (...) ---
    # -- end if

    def p_lang(self, p):
        '''lang : expr'''
        p[0] = p[1]

    def p_expr_simple_list(self, p):
        '''expr : sexpr_list'''
        if p[1] is None:
            p[0] = None
        elif len(p[1]) == 1:
            p[0] = p[1][0]
        else:
            p[0] = FilterAND(p[1])
    # ---

    def p_expr_in_parens(self, p):
        '''expr : LPAREN expr RPAREN'''
        p[0] = p[2]

    def p_expr_not(self, p):
        '''expr : NOT expr'''
        p[0] = (FilterNOT(p[2]) if p[2] is not None else None)

    def p_expr_and(self, p):
        '''expr : expr AND expr'''
        if p[1] is not None and p[3] is not None:
            p[0] = FilterAND(p[1], p[3])
        else:
            p[0] = None

    def p_expr_or(self, p):
        '''expr : expr OR expr'''
        if p[1] is not None and p[3] is not None:
            p[0] = FilterOR(p[1], p[3])
        else:
            p[0] = None

    def p_expr_bad(self, p):
        '''expr : error'''
        self.handle_parse_error(p, 1, "unknown error")

    # list of simple expressions
    def p_sexpr_list_one(self, p):
        '''sexpr_list : sexpr'''
        p[0] = ([p[1]] if p[1] is not None else None)

    def p_sexpr_list_many(self, p):
        '''sexpr_list : sexpr sexpr_list'''
        if p[1] is not None and p[2] is not None:
            p[0] = [p[1]] + p[2]
        else:
            p[0] = None

    # simple expressions
    def p_sexpr_true(self, p):
        '''sexpr : KW_TRUE'''
        p[0] = self.obj_cache(FilterTrue)

    def p_sexpr_false(self, p):
        '''sexpr : KW_FALSE'''
        p[0] = self.obj_cache(FilterFalse)

    def p_sexpr_known(self, p):
        '''sexpr : KW_KNOWN'''
        p[0] = self.obj_cache(FilterHasAttr, "them.name")

    def p_sexpr_unknown(self, p):
        '''sexpr : KW_UNKNOWN'''
        p[0] = FilterNOT(self.obj_cache(FilterHasAttr, "them.name"))

    def p_sexpr_foreign(self, p):
        '''sexpr : KW_FOREIGN'''
        # hardcoded country code
        p[0] = self.obj_cache(FilterAttrRegexp, "them.nr", r'^(:?\+|00)(?!49)')

    def p_sexpr_mobile(self, p):
        '''sexpr : KW_MOBILE'''
        # hardcoded codes
        p[0] = self.obj_cache(
            FilterAttrRegexp, "them.nr",
            r'^(?:\+49|0)'
            r'(?:'
                r'(?:151[124567]|160|17[015])'          # Deutsche Telekom
                r'|(?:152[0235]|162|17[234])'           # Vodafone
                r'|(?:157[03578]|163|17[78])'           # E-Plus
                r'|(?:1590|017[69])'                    # O2
            r')'
        )

    def p_sexpr_incoming(self, p):
        '''sexpr : KW_INCOMING'''
        p[0] = self.obj_cache(FilterCallIncoming)

    def p_sexpr_outgoing(self, p):
        '''sexpr : KW_OUTGOING'''
        p[0] = self.obj_cache(FilterCallOutgoing)

    def p_sexpr_missed(self, p):
        '''sexpr : KW_MISSED'''
        p[0] = self.obj_cache(
            FilterAttrCmpFunc,
            "call_type", operator.is_, CallType.INCOMING_MISSED
        )

    def p_sexpr_denied(self, p):
        '''sexpr : KW_DENIED'''
        p[0] = self.obj_cache(
            FilterAttrCmpFunc,
            "call_type", operator.is_, CallType.INCOMING_DENIED
        )

    def p_sexpr_dev(self, p):
        '''sexpr : KW_DEV STR'''
        p[0] = FilterAttrRegexp("me.nebenstelle", p[2], flags=re.I)

    def p_sexpr_me(self, p):
        '''sexpr : KW_ME STR'''
        m = self.regexp_telnummer.match(p[2])
        if m:
            p[0] = self.obj_cache(
                FilterAttrCmpFunc, "me.nr", operator.__eq__, m.group("nr")
            )
        else:
            self.handle_parse_error(p, 2, "invalid telno")

    def p_sexpr_me_any(self, p):
        '''sexpr : KW_ME KW_ANY'''
        p[0] = self.obj_cache(FilterTrue)

    def p_sexpr_them(self, p):
        '''sexpr : KW_THEM STR'''
        if not p[2]:
            self.handle_parse_error(p, 2, "empty 'them' identifier")
        else:
            m = self.regexp_telnummer.match(p[2])
            if m:
                p[0] = self.obj_cache(
                    FilterAttrCmpFunc, "them.nr", operator.__eq__, m.group("nr")
                )
            else:
                p[0] = FilterAttrCaseEq("them.name", p[2], weak=True)
            # --
        # --
    # ---

    def p_sexpr_them_like(self, p):
        '''sexpr : KW_THEM APPROX STR'''
        p[0] = FilterAttrRegexp("them.nr", p[3], flags=re.I)
    # ---

    def p_sexpr_them_any(self, p):
        '''sexpr : KW_THEM KW_ANY'''
        p[0] = self.obj_cache(FilterTrue)

    def p_sexpr_them_name_eq(self, p):
        '''sexpr : KW_NAME EQ     STR
                 | KW_NAME EQ_CMP STR'''
        p[0] = FilterAttrCaseEq("them.name", p[3], weak=True)

    def p_sexpr_them_name_like(self, p):
        '''sexpr : KW_NAME APPROX STR'''
        p[0] = FilterAttrRegexp("them.name", p[3], flags=re.I, weak=True)

    def _create_time_cmp_date(self, op_func, p):
        try:
            date_arg = self.convert_date(p[2])
        except ValueError:
            self.handle_parse_error(p, 2, "invalid date")
        else:
            p[0] = self.obj_cache(
                FilterAttrCmpFunc, "datum", op_func, date_arg
            )
    # ---

    def _create_time_cmp_kw(self, op_func, p):
        p[0] = self.obj_cache(
            FilterAttrCmpFunc, "datum", op_func,
            self.get_date(self.date_op_map[p[2]])
        )
    # ---

    def _create_time_cmp_between(self, p, low, high):
        filter_low = self.obj_cache(
            FilterAttrCmpFunc, "datum", operator.__ge__, low
        )
        filter_high = self.obj_cache(
            FilterAttrCmpFunc, "datum", operator.__lt__, high
        )
        p[0] = FilterAND(filter_low, filter_high)
    # ---

    def p_sexpr_date_since(self, p):
        '''sexpr : KW_SINCE STR'''
        self._create_time_cmp_date(operator.__ge__, p)

    def p_sexpr_date_for_n_days(self, p):
        '''sexpr : KW_FOR   STR KW_DAYS
                 | KW_SINCE STR KW_DAYS'''
        try:
            num_days = int(p[2], 10)
        except ValueError:
            p[0] = None
        else:
            self._create_time_cmp_between(
                p,
                self.get_date(datetime.timedelta(days=-num_days)),
                self.get_date(datetime.timedelta(days=1))
            )
        # --

    def p_sexpr_date_since_kw(self, p):
        '''sexpr : KW_SINCE KW_TODAY
                 | KW_SINCE KW_YESTERDAY
                 | KW_SINCE KW_WEEK'''
        self._create_time_cmp_kw(operator.__ge__, p)

    def p_sexpr_date_before(self, p):
        '''sexpr : KW_BEFORE STR'''
        self._create_time_cmp_date(operator.__lt__, p)
    # ---

    def p_sexpr_date_before_kw(self, p):
        '''sexpr : KW_BEFORE KW_TODAY
                 | KW_BEFORE KW_YESTERDAY
                 | KW_BEFORE KW_WEEK'''
        self._create_time_cmp_kw(operator.__lt__, p)

    def p_sexpr_today(self, p):
        '''sexpr : KW_TODAY'''
        self._create_time_cmp_between(
            p,
            self.get_date(),
            self.get_date(datetime.timedelta(days=1))  # should be redundant
        )

    def p_sexpr_yesterday(self, p):
        '''sexpr : KW_YESTERDAY'''
        self._create_time_cmp_between(
            p,
            self.get_date(datetime.timedelta(days=-1)),
            self.get_date()
        )

    def p_sexpr_week(self, p):
        '''sexpr : KW_WEEK'''
        self._create_time_cmp_between(
            p,
            self.get_date(datetime.timedelta(days=-6)),
            self.get_date(datetime.timedelta(days=1))
        )

    def p_sexpr_date_between(self, p):
        '''sexpr : KW_BETWEEN STR STR'''
        try:
            low_date_arg = self.convert_date(p[2])
        except ValueError:
            self.handle_parse_error(p, 2, "invalid from date")
            low_date_arg = None
        # --

        try:
            high_date_arg = self.convert_date(p[3])
        except ValueError:
            self.handle_parse_error(p, 3, "invalid to date")
            high_date_arg = None
        # --

        if low_date_arg is not None and high_date_arg is not None:
            self._create_time_cmp_between(p, low_date_arg, high_date_arg)
    # ---

    def p_sexpr_duration(self, p):
        '''sexpr : KW_DURATION NE     STR
                 | KW_DURATION GE     STR
                 | KW_DURATION LE     STR
                 | KW_DURATION GT     STR
                 | KW_DURATION LT     STR
                 | KW_DURATION EQ_CMP STR
                 | KW_DURATION EQ     STR
        '''
        cmp_op = self.cmp_op_map[p[2]]

        try:
            duration_arg = int(p[3], 10)
        except ValueError:
            self.handle_parse_error(p, 3, "invalid duration")
        else:
            p[0] = self.obj_cache(
                FilterAttrCmpFunc, "dauer.dauer", cmp_op, duration_arg
            )
    # ---

# --- end of FilterLangParser ---
