# fritz-fon-stats -- ffs-query main script
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["FFSQuery"]

import argparse
import io
import sys


import ffs.scripts._base

import ffs.fon.stats.reader
import ffs.fon.stats.stats

import ffs.fon.query.lang.lexer
import ffs.fon.query.lang.parser


class FFSQuery(ffs.scripts._base.MainScriptBase):

    def build_argument_parser(self):
        parser = argparse.ArgumentParser(prog=self.prog_name)

        parser.add_argument(
            "-f", "--csv-file", metavar="<file>", default=None,
            help="path to csv file (default: stdin)"
        )

        parser.add_argument(
            "-F", "--filter",
            dest="filter_exprv", metavar="<expr>", default=[], action="append",
            help="filter expressions"
        )

        parser.add_argument(
            "-v", "--invert-filter",
            dest="invert_filter", default=False, action="store_true",
            help="invert final filter"
        )

        output_mode_group = parser.add_argument_group(title="output mode")
        output_mode_group_mut = output_mode_group.add_mutually_exclusive_group()

        output_mode_group.add_argument(
            "-n", "--no-names",
            dest="resolve_names", default=True, action="store_false",
            help="do not include names in output"
        )

        output_mode_group_mut.add_argument(
            "--output-mode",
            dest="output_mode", default=None,
            choices=[
                "print", "count", "ratio",
                "list-me", "list-them", "list-dev",
                "describe-filter"
            ],
            help="set output mode"
        )

        output_mode_group_mut.add_argument(
            "-c", "--count",
            dest="output_mode", default=argparse.SUPPRESS,
            action="store_const", const="count",
            help="show number of matching entries"
        )

        output_mode_group_mut.add_argument(
            "-r", "--ratio",
            dest="output_mode", default=argparse.SUPPRESS,
            action="store_const", const="ratio",
            help="show number of matching entries, compared to previous filters or all entries"
        )

        output_mode_group_mut.add_argument(
            "-M", "--list-me",
            dest="output_mode", default=argparse.SUPPRESS,
            action="store_const", const="list_me",
            help="list local numbers (Eigene Rufnummer) from matched entries"
        )

        output_mode_group_mut.add_argument(
            "-T", "--list-them",
            dest="output_mode", default=argparse.SUPPRESS,
            action="store_const", const="list_them",
            help="list remote numbers (Rufnummer) from matched entries"
        )

        output_mode_group_mut.add_argument(
            "-D", "--list-dev",
            dest="output_mode", default=argparse.SUPPRESS,
            action="store_const", const="list_dev",
            help="list devices (Nebenstelle) from matched entries"
        )

        output_mode_group_mut.add_argument(
            "-X", "--describe-filter",
            dest="output_mode", default=argparse.SUPPRESS,
            action="store_const", const="describe_filter",
            help="show compiled filters"
        )

        return parser
    # --- end of build_argument_parser (...) ---

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arg_parser = self.build_argument_parser()
    # --- end of __init__ (...) ---

    def parse_args(self, argv):
        return self.arg_parser.parse_args(argv)
    # --- end of parse_args (...) ---

    def get_query_parser(self):
        parser = ffs.fon.query.lang.parser.FilterLangParser(
            ffs.fon.query.lang.lexer.FilterLangLexer()
        )
        parser.build()
        return parser
    # --- end of get_query_parser (...) ---

    def compile_filters(self, filter_exprv, flatten=True):
        if not filter_exprv:
            return None

        parser = self.get_query_parser()

        filter_funcv = [
            parser.parse(filter_expr) for filter_expr in filter_exprv
        ]

        if any((f is None for f in filter_funcv)):
            raise RuntimeError("Failed to compile filters!\n")
        # --

        if flatten:
            return [f.flatten() for f in filter_funcv]
        else:
            return filter_funcv
    # ---

    def get_stats_reader(self):
        return ffs.fon.stats.reader.AVMPhoneStatsReader()
    # --- end of get_stats_reader (...) ---

    def read_phone_stats(self, csv_file):
        stats = ffs.fon.stats.stats.AVMPhoneStats()
        stats_reader = self.get_stats_reader()

        if csv_file is None or csv_file == "-":
            stats.update(stats_reader.read_csv_file(sys.stdin))
        else:
            with io.open(csv_file, "rt", encoding="utf-8") as fh:
                stats.update(stats_reader.read_csv_file(fh))
        # --

        return stats
    # --- end of read_phone_stats (...) ---

    def get_phone_stats(self, arg_config):
        return self.read_phone_stats(arg_config.csv_file)
    # ---

    def filter_stats(self, stats, filter_funcv, invert_filter):
        prev_matched = stats.get_entries()
        matched = prev_matched

        if filter_funcv:
            # initially, match all entries
            #  each filter_func then reduces the amount
            #  of the previously matched entries
            for filter_func in filter_funcv:
                prev_matched = matched
                if prev_matched:
                    matched, others = stats.filter_split(
                        filter_func, entries=prev_matched
                    )
                else:
                    matched = []
                    others = []
                    break
                # --

            # --

            if invert_filter:
                matched = others
            # --
        # --

        return (prev_matched, matched)
    # --- end of filter_stats (...) ---

    def __call__(self, argv):
        arg_config = self.parse_args(argv)
        filter_funcv = self.compile_filters(arg_config.filter_exprv)

        stats = self.get_phone_stats(arg_config)
        output_mode = (arg_config.output_mode or "print")

        if output_mode == "describe_filter":
            if not filter_funcv:
                pass
            elif len(filter_funcv) == 1:
                print(filter_funcv[0].describe())
            else:
                print(
                    "\n".join((f.describe() for f in filter_funcv))
                )
            # --

        elif output_mode in {
            "print", "ratio", "count", "list_me", "list_them", "list_dev"
        }:
            prev_matched, matched = self.filter_stats(
                stats, filter_funcv, arg_config.invert_filter
            )

            if not output_mode or output_mode == "print":
                print("\n".join(map(str, matched)))

            elif output_mode == "count":
                print(len(matched))

            elif output_mode == "ratio":
                num_matched = len(matched)
                num_prev_matched = len(prev_matched)

                print(
                    "{p:.00%} ({a} / {b})".format(
                        a=num_matched, b=num_prev_matched,
                        p=num_matched / (num_prev_matched or 1)
                    )
                )

            elif output_mode == "list_me":
                print(
                    "\n".join(sorted(set((obj.me.nr for obj in matched))))
                )

            elif output_mode == "list_them":
                if arg_config.resolve_names:
                    lines_gen = map(
                        str,
                        sorted(
                            set((obj.them for obj in matched)),
                            key=lambda o: o.nr
                        )
                    )
                else:
                    lines_gen = sorted(set((obj.them.nr for obj in matched)))
                # --

                print("\n".join(lines_gen))

            elif output_mode == "list_dev":
                print(
                    "\n".join(sorted(set((obj.me.nebenstelle for obj in matched))))
                )

            else:
                raise NotImplementedError("unhandled output mode: {}".format(output_mode))
            # --
        else:
            raise NotImplementedError("unknown output mode: {}".format(output_mode))
    # ---

# --- end of FFSQuery ---


if __name__ == "__main__":
    FFSQuery.run()
