#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""Code that's been removed from the Königsberg project.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


from typing import *


labeled_paths = dict()


def sanity_check(data: Mapping[Hashable, Iterable[Hashable]],
                 raise_error: bool = True) -> bool:
    """Perform some basic sanity checks on DATA, a node dictionary (or other
    hashmap) that maps nodes, by (hashable) name or label, to an iterable of
    nodes, identified in the same way as they appear as keys in the hashmap.

    If RAISE_ERROR is True (the default), failing a sanity check raises an
    AssertionError (and crashes). If False, the function returns False instead of
    crashing if any sanity checks are missed.
    """
    try:
        for start, destlist in data.items():
            # First: check for sensible data types, and assert that each node is connected to at least one other node.
            assert isinstance(destlist, Iterable), f"ERROR! {destlist} appears as the destination list for the node {start}, but it is not a list-like object!"
            assert len(destlist) > 0, f"ERROR! The destination list for node {start} is empty!"

            for dest in destlist:
                # Next: check that for each known A->B path, B->A is also a known path.
                assert start in data[dest], f"ERROR! {start} -> {dest} appears in the data, but {dest} -> {start} does not!"
    except AssertionError:
        if raise_error:
            raise
        else:
            return False


def expand_paths(data: Mapping[Hashable, Iterable[Hashable]]) -> Dict[Hashable, Tuple[Hashable, ...]]:
    """Expand PATHS_FROM_NODE into the """
    all_paths = set()

    for node, destlist in paths_from_node.items():
        for dest in destlist:
            all_paths.add(tuple(sorted([node, dest])))

    assert len(all_paths) < 256, f"ERROR! There are {len(all_paths)} unique paths in the data! Königsberg can only handle 255 paths."
    return dict(zip(range(1, 256), sorted(all_paths)))


if __name__ == "__main__":
    sanity_check(paths_from_node)
    labeled_paths = expand_paths(paths_from_node)

    from pprint import pprint
    pprint(labeled_paths)
