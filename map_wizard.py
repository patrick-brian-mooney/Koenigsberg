#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

"""A program to create map files that can be used with Koenigsberg.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import sys

try:
    import pyximport; pyximport.install()
except ImportError:
    print("Cython not completely imported! Running in pure-Python mode. This may crash if files are named improperly!")

import wizard_lib


if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(f"Sorry! {sys.argv[0]} does not take any command-line arguments!")

    wizard_lib.do_make_map()
