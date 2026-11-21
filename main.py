# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Avvio dai sorgenti: python main.py (la finestra) o python main.py --cli [opzioni] (la console)."""

import sys

from myeasymp3toiphone.app import cli_main, main

if __name__ == "__main__":
    if "--cli" in sys.argv[1:]:
        sys.argv.remove("--cli")
        sys.exit(cli_main())
    sys.exit(main())
