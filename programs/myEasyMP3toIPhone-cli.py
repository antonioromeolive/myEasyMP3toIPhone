# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""myEasyMP3toIPhone-cli.exe: la console (--env, --scan, --version, --selftest), nella build (myEasyMP3toIPhone.spec)."""

import sys

from myeasymp3toiphone.app import cli_main

sys.exit(cli_main())
