#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cython: language_level=3
"""Utility code used in Patrick Mooney's Königsberg.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import functools

from typing import Any, Callable, Dict, Generator, Hashable, Iterable, Optional


def flatten_list(l: Iterable) -> Generator[Any, None, None]:
    """Yields the items from L, an iterable, one at a time, unless those items are
    themselves iterables, in which case their single elements are yielded one at a
    time. Strings and string-like objects count as non-iterables for this function.

    No matter how deeply nested the iterables are, only non-iterable atomic elements
    are yielded.
    """
    for item in l:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes, bytearray)):
            yield from item
        else:
            yield item


def _default_path_formatter(path: bytearray,
                            path_length: int,
                            path_translation_dict: Dict[int, Hashable],
                            start: Optional[Hashable],
                            node_translation_dict: Optional[Dict[int, Hashable]]) -> str:
    """Takes PATH, a bytearray, and uses PATH_TRANSLATION_DICT to turn it into a
    human-readable form. Optionally, also uses START and NODE_TRANSLATION_DICT to
    indicate which node begins the path.

    Ignores any zero bytes at the end of the array; those are steps not taken. Zero
    bytes must occur in a contiguous block at the end of the array; no non-zero
    bytes may follow them.

    If either of START or NODE_TRANSLATION_DICT is supplied, the other must also be
    supplied.

    Don't use this function directly; get a callable version from the no-leading-
    underscore default_path_formatter(), below.
    """
    # Cython apparently gets confused about the lengths of paths, making this trimming step necessary?
    # Maybe we should be using NumPy arrays in the first place.
    path = path[:path_length]

    if 0 in path:
        first_loc = path.find(0)
        for i, byte in enumerate(path, first_loc):
            assert byte != 0, f"Zero-bytes can only occur contiguously at the end of a path, not at the beginning or in the middle! The byte {byte} in position {i} in path {path}, however, breaks this rule!"

    if start:
        ret = node_translation_dict[start] + ': '
    else:
        ret = ''

    ret += ' -> '.join(str(path_translation_dict[p]) for p in path if p)
    return ret



def default_path_formatter(path_translation_dict: Dict[int, Hashable], *,
                           start: Optional[Hashable] = None,
                           node_translation_dict: Optional[Dict[int, Hashable]] = None) -> Callable:
    """'Fixes' the three relevant arguments into a version of
    _default_path_formatter() that can be called with just PATH. Useful for passing
    into functions in the main Königsberg code that expect to just take a function
    that can process a bytearray PATH.
    """
    assert all([start, node_translation_dict]) or all([not start, not node_translation_dict])
    return functools.partial(_default_path_formatter, path_translation_dict=path_translation_dict, start=start, node_translation_dict=node_translation_dict)


def maximally_dense_network_graph(num_nodes: int) -> Dict[int, Iterable[int]]:
    """Automatically constructs and returns a graph with NUM_NODES nodes, each of
    which is connected to every other node.
    """
    return {n: [d for d in range(1, 1 + num_nodes) if d != n] for n in range(1, 1 + num_nodes)}
