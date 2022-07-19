"""Sample data used in developing Patrick Mooney's Königsberg.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""

four_spot_square = {
    1: (2, 4),
    2: (1, 3),
    3: (2, 4),
    4: (1, 3),
}


hex_ring = {
    1: (2, 6),
    2: (1, 3),
    3: (2, 4),
    4: (3, 5),
    5: (4, 6),
    6: (1, 5)
}


ten_spot_hexagon = {
    1: (2, 4, 5),
    2: (1, 5, 6, 3),
    3: (2, 6, 7),
    4: (1, 5, 8),
    5: (4, 1, 2, 6, 9, 8),
    6: (5, 2, 3, 7, 10, 9),
    7: (6, 3, 10),
    8: (4, 5, 9),
    9: (8, 5, 6, 10),
    10: (9, 6, 7),
}


cealdhame = {
    1:  (2, 6),
    2:  (1, 6, 7, 3),
    3:  (2, 7, 8, 4),
    4:  (3, 8, 9, 5),
    5:  (4, 9),
    6:  (1, 2, 7, 11, 10),
    7:  (2, 3, 8, 12, 11, 6),
    8:  (7, 3, 4, 9, 13, 12),
    9:  (8, 4, 5, 14, 13),
    10: (6, 11, 15),
    11: (10, 6, 7, 12, 15, 16),
    12: (11, 7, 8, 13, 17, 16),
    13: (12, 8, 9, 14, 18, 17),
    14: (13, 9, 18),
    15: (10, 11, 16, 20, 19),
    16: (15, 11, 12, 17, 21, 20),
    17: (16, 12, 13, 18, 22, 21),
    18: (13, 14, 23, 22, 17),
    19: (15, 20),
    20: (19, 15, 16, 21),
    21: (20, 16, 17, 22),
    22: (21, 17, 18, 23),
    23: (18, 22),
}


# The tructure of the classic Königsberg seven-bridge problem:
# Region A in the middle, B down south, C up north, D in the east.
# 2 bridges (2, 3) connect A <-> C.
# 2 bridges (4, 5) connect A <-> B.
# 1 bridge (1) connects C <-> D.
# 1 bridge (6) connects A <-> D.
# 1 bridge (7) connects B <-> D.
Königsberg = {
    'nodes to paths': {             # Or, which bridges are accessible from which areas?
        'A': (2, 3, 4, 5, 6),
        'B': (4, 5, 7),
        'C': (2, 3, 1),
        'D': (1, 6, 7),
    },
    'paths to nodes': {             # Or, which areas does each bridge connect?
        1: ('C', 'D'),
        2: ('C', 'A'),
        3: ('C', 'A'),
        4: ('A', 'B'),
        5: ('A', 'B'),
        6: ('A', 'D'),
        7: ('B', 'D'),
    }
}
