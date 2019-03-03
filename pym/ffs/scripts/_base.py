# fritz-fon-stats -- base class for main scripts
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["MainScriptBase"]

import os.path
import sys


class MainScriptBase(object):
    EX_OK = getattr(os, 'EX_OK', 0)
    EX_ERR = EX_OK ^ 1
    EX_KEYBOARD_INTERRUPT = EX_OK ^ 130

    @classmethod
    def run(cls, prog=None, argv=None, **kwargs):
        main_script = cls(prog=prog, **kwargs)
        exit_code = main_script.run_main(argv)
        sys.exit(exit_code)
    # ---

    @property
    def prog_name(self):
        return os.path.basename(self.prog)

    def __init__(self, prog=None):
        super().__init__()
        self.prog = (sys.argv[0] if prog is None else prog)

    def run_main(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]

        try:
            exit_code = self(argv)
        except KeyboardInterrupt:
            exit_code = self.EX_KEYBOARD_INTERRUPT
        else:
            if exit_code is None or exit_code is True:
                exit_code = self.EX_OK
            elif exit_code is False:
                exit_code = self.EX_ERR
            # --
        # --

        return exit_code
    # ---

    def write_error(self, text):
        sys.stderr.write(text + '\n')

    def __call__(self, argv):
        pass
    # --- end of __call__ (...) ---

# --- end of MainScriptBase ---
