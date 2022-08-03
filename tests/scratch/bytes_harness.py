#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple harness for running bytes_test.pyx.

Test was written for the Königsberg project. Copyright 2022 by Patrick Mooney.
No rights granted; this is a quick scratch test.
"""


import pyximport; pyximport.install()
import bytes_test as bt


if __name__ == "__main__":
    b = bt.test()
    print([w for w in b], f'\tlength: {len(b)}')
    print(b)
