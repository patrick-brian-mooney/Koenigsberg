#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cython: language_level=3
"""Quick test for how Cython handles bytearrays. This was intended to pare down
a problem with Cython's handling of the data type that turned out to be a bug
that was fixed by upgrading Cython to 0.29.32; see
https://www.reddit.com/r/Cython/comments/wep60b/trouble_with_bytearrays_during_cython_conversion/

Test was written for the Königsberg project. Copyright 2022 by Patrick Mooney.
No rights granted; this is a quick scratch test.
"""


def test() -> bytearray:
    b = bytearray(range(33, 65))
    print(b)
    print([w for w in b], f'\tlength: {len(b)}')
    print()
    return b



if __name__ == "__main__":
    pass
