#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cython: language_level=3
"""Utility code used in Patrick Mooney's Königsberg.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import functools
import sys
import traceback

from typing import Any, Callable, Dict, Generator, Hashable, Iterable, Optional, Tuple, Union, Type


# First, verbosity levels.
VERBOSITY_MINIMAL = 0
VERBOSITY_REPORT_PROGRESS_ON_SAVE = 1
VERBOSITY_FRIENDLY_PROGRESS_CHATTER = 2
VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS = 3
VERBOSITY_REPORT_ALL_ABANDONED_PATHS = 4
VERBOSITY_REPORT_EVERYTHING = 5


# Global variables that control message printing
cdef long verbosity = 1


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
                            path_translation_dict: dict,
                            start: Hashable, 
                            node_translation_dict: dict) -> str:
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
    if start: assert node_translation_dict, f"ERROR! If START is specified, NODE_TRANSLATION_DICT must also be specified!"
    if node_translation_dict: assert start, f"ERROR! If NODE_TRANSLATION_DICT is specified, START must also be specified!"
    
    if 0 in path:
        first_loc = path.find(0)
        for i, byte in enumerate(path[first_loc:], first_loc):
            assert byte == 0, f"Zero-bytes can only occur contiguously at the end of a path, not at the beginning or in the middle! The byte {byte} in position {i} in path {path}, however, breaks this rule!"

    if start:
        ret = node_translation_dict[start] + ': '
    else:
        ret = ''

    ret += ' -> '.join(str(path_translation_dict[p]) for p in path if p)
    return ret


def default_path_formatter(path_translation_dict: Dict[int, Hashable], *,
                           start: Optional[Hashable] = "",
                           node_translation_dict: Optional[Dict[int, Hashable]] = dict()) -> Callable:
    """'Fixes' the three relevant arguments into a version of the above
    _default_path_formatter() that can be called with just PATH and PATH_LENGTH.
    Useful for passing into functions in the main Königsberg code that expect to
    just take a function that can process a bytearray PATH and its length.
    """
    assert all([start, node_translation_dict]) or all([not start, not node_translation_dict])
    return functools.partial(_default_path_formatter, path_translation_dict=path_translation_dict,
                             start=start, node_translation_dict=node_translation_dict)


def maximally_dense_network_graph(num_nodes: int) -> Dict[int, Iterable[int]]:
    """Automatically constructs and returns a graph with NUM_NODES nodes, each of
    which is connected to every other node.
    """
    return {n: [d for d in range(1, 1 + num_nodes) if d != n] for n in range(1, 1 + num_nodes)}


def _sanity_check_graph(graph: Dict[Hashable, Iterable[Hashable]],
                        raise_error: bool = True,
                        ) -> Tuple[bool, Union[Type[BaseException], None]]:
    """Perform basic sanity checks on the dictionaries PATHS_TO_NODES and
    NODES_TO_PATHS. If RAISE_ERROR is True, failing a sanity check raises a
    ValueError (and execution terminates); if it is False, the function returns
    False instead of crashing.
    """
    try:
        assert isinstance(graph, dict), f"The supplied graph {graph} is not a dictionary representing a node-to-node graph!"
        for node, dest_list in graph.items():
            assert isinstance(node, Hashable), f"Node {node} in the supplied graph is not a hashable value, and cannot be used as a node label!"
            assert isinstance(dest_list, Iterable), f"The destination list for node {node} in the supplied graph is not a list-like object!"
            assert not isinstance(dest_list, (str, bytes, bytearray)), f"The destination list for node {node} is a string or string-like object of type {type(dest_list)}, and these cannot be used as destination lists for graphs!"
            for dest in dest_list:
                assert isinstance(dest, Hashable), f"The destination node {dest} given in the destination list for the node {node} in the supplied graph is not a hashable value, and cannot be used as the label for a node!"
                assert dest in graph, f"The node '{node}' in the supplied graph is marked as going to the node '{dest}', but that second node does not have any outbound paths listed!"
                assert node in graph[dest], f"The node {node} in the supplied graph is marked as going to the node {dest}, but that second node is not marked as leading back to {node}! (All pathways between nodes must explicitly be bidirectional.)"

        #FIXME! More tests?
        return True, None
    except BaseException as errrr:
        if raise_error:
            raise ValueError(f"Unable to validate supplied input data: {str(errrr)}") from errrr
        else:
            return False, errrr


def _sanity_check_dicts(paths_to_nodes: Dict[Hashable, Iterable[Hashable]],
                        nodes_to_paths: Dict[Hashable, Iterable[Hashable]],
                        raise_error: bool = True,
                        ) -> Tuple[bool, Union[Type[BaseException], None]]:
    """Perform basic sanity checks on the dictionaries PATHS_TO_NODES and
    NODES_TO_PATHS. If RAISE_ERROR is True, failing a sanity check raises a
    ValueError (and execution terminates); if it is False, the function returns
    False instead of crashing.
    """
    try:
        assert isinstance(paths_to_nodes, Dict), f"The PATHS_TO_NODES parameter passed to _sanity_check_dicts() must be a dictionary, but is instead an instance of {type(paths_to_nodes)}!"
        assert isinstance(nodes_to_paths, Dict), f"The NODES_TO_PATHS parameter passed to _sanity_check_dicts() must be a dictionary, but is instead an instance of {type(nodes_to_paths)}!"
        assert len(paths_to_nodes.keys()) <= 255, f"Königsberg can only handle maps with up to 255 paths, but the supplied data has {len(paths_to_nodes.keys())} paths!"

        paths_not_in_nodes = set(paths_to_nodes.keys()) - set(flatten_list(nodes_to_paths.values()))
        assert not paths_not_in_nodes, f"Dictionary mapping paths to nodes has paths {paths_not_in_nodes} not connected to any node!"
        nodes_not_in_paths = set(nodes_to_paths.keys()) - set(flatten_list(paths_to_nodes.values()))
        assert not nodes_not_in_paths, f"Dictionary mapping nodes to paths has nodes {nodes_not_in_paths} not connected to any path!"

        for path, node_list in paths_to_nodes.items():
            assert isinstance(node_list, Iterable), f"The node list for path {path} in the dictionary mapping paths to nodes is not a list-like object, but instead is a {type(node_list)}!"
            assert len(node_list) == 2, f"Path {path} should connect exactly two nodes, but instead it connects {len(node_list)}!"
            for node in node_list:
                assert node in nodes_to_paths, f"Node {node} appears in the node list for path {path}, but does not appear in the dictionary mapping nodes to paths!"
        for node, path_list in nodes_to_paths.items():
            assert isinstance(path_list, Iterable), f"The path list for node {node} in the dictionary mapping nodes to paths is not a list-like object, but instead is a {type(path_list)}!"
            for path in path_list:
                assert path in paths_to_nodes, f"Path {path} appears in the path list for node {node}, but does not appear in the dictionary mapping paths to nodes!"

        # FIXME! More checks?
        return True, None
    except BaseException as errrr:
        if raise_error:
            raise ValueError(f"Unable to validate supplied input data: {str(errrr)}") from errrr
        else:
            return False, errrr


def normalize_dicts(paths_to_nodes: Dict[Hashable, Iterable[Hashable]],
                    nodes_to_paths: Dict[Hashable, Iterable[Hashable]],
                    raise_error: bool = True,
                    ) -> Tuple[Dict[int, Tuple[int]], Dict[int, Tuple[int]],
                               Dict[int, Hashable], Dict[int, Hashable],
                               Dict[Hashable, int], Dict[Hashable, int]]:
    """Takes the PATHS_TO_NODES dict and the NODES_TO_PATHs dict and fits them into
    the format that's easiest for solve_from() to work with: all path and node names
    are assigned integer IDs, regardless of how the human creating the description
    described them in that description.

    Returns a 6-tuple:
     1. a normalized PATHS_TO_NODES dictionary that uses integer IDs;
     2. a normalized NODES_TO_PATHS dictionary that uses integer IDS;
     3. a dictionary mapping path IDs to the human-supplied path descriptions;
     4. a dictionary mapping node IDs to the human-supplied node descriptions;
     5. a dictionary mapping human-supplied path descriptions to path IDs;
     6. a dictionary mapping human-supplied node descriptions to node IDs.

    Performs some basic sanity checks on the supplied data before doing all of this.

    #FIXME: optimization (later): return None for items 3 and/or 4 if the human-
    supplied descriptions were already integers.
    """
    check, errrr = _sanity_check_dicts(paths_to_nodes, nodes_to_paths, raise_error)
    if not check:
        traceback.print_exception(type(errrr), errrr, errrr.__traceback__, chain=True)
        sys.exit(3)

    # First, set up the translation tables that we're going to return so that our int-based dictionaries can be decoded later for the user
    paths_x = dict(zip(range(1, 256), sorted(paths_to_nodes.keys())))
    nodes_x = dict(zip(range(1, 256), sorted(nodes_to_paths.keys())))

    # And the opposite-direction translation tables so we can translate the user-supplied dicts in the first place.
    paths_x_rev = {value: key for key, value in paths_x.items()}
    nodes_x_rev = {value: key for key, value in nodes_x.items()}

    paths_ret, nodes_ret = dict(), dict()
    for path, node_list in paths_to_nodes.items():
        paths_ret[paths_x_rev[path]] = tuple(sorted(nodes_x_rev[i] for i in node_list))
    for node, path_list in nodes_to_paths.items():
        nodes_ret[nodes_x_rev[node]] = tuple(sorted(paths_x_rev[i] for i in path_list))

    return (paths_ret, nodes_ret, paths_x, nodes_x, paths_x_rev, nodes_x_rev)


def graph_to_dicts(graph: Dict[Hashable, Iterable[Hashable]]
                   ) -> Tuple[Dict[Hashable, Iterable[Hashable]], Dict[Hashable, Iterable[Hashable]]]:
    """Turns the graph GRAPH into a pair of dictionaries, the first of which maps
    paths to nodes, the second of which maps nodes to paths. A "graph" is a
    dictionary that indicates which nodes are connected to which other nodes, but
    without providing any direct information about paths. It is a more constrained
    way to indicate the connections in a graph -- it does not allow for paths to be
    named, and there cannot be more than one path between nodes -- but it is also
    less verbose and perhaps easier to construct. This route, of necessity,
    automatically names paths with boring names of the form "(Los Angeles, Oxnard)"
    for a route connecting the 'Los Angeles' node to the 'Oxnard' node.

    Performs basic sanity checks on the input data -- basically:
      1. whether it conforms to the expected format (i.e., that it is a dict mapping
         a hashable, taken to be a node label, to an iterable of other hashables,
         which are also taken to be node labels); and
      2. That if A -> B is represented in the graph, then B -> A must also be
         represented in the graph -- this is a guard intended to help detect data
         entry errors.

    You will presumably want to call normalize_dicts() on this pair, or at least
    _sanity_check_dicts(), but this function does not do so for you.
    """
    check, errrr = _sanity_check_graph(graph)
    if not check:
        traceback.print_exception(type(errrr), errrr, errrr.__traceback__, chain=True)
        sys.exit(3)

    all_paths = set()
    for node, dest_list in graph.items():
        for dest in dest_list:
            all_paths.add(tuple(sorted([dest, node])))

    nodes_to_paths = {key: tuple(sorted([tuple(sorted([key, v])) for v in value])) for key, value in graph.items()}
    paths_to_nodes = {path: (path[0], path[1]) for path in sorted(all_paths)}

    return (paths_to_nodes, nodes_to_paths)


cpdef inline void log_it(str message, int minimum_verbosity) except *:
    """Prints MESSAGE, provided that the current verbosity level, specified by
    CURRENT_VERBOSITY_LEVEL, is at least the MINIMUM_VERBOSITY specified for this
    message.

    We're not using the LOGGING module in the stdlib because we're trying to keep
    this as lightweight as possible, as well as inlining it. It's called a lot.
    """
    if verbosity >= minimum_verbosity:
        print(message)


def quick_test_harness() -> None:
    """Simple quick harness for testing something that's not going to get formally
    written up in tests.py
    """
    import tests.tests as t
    t.dense_polygon_sample_test(8)
    import sys
    sys.exit()


if __name__ == "__main__":
    # quick_test_harness()              # Comment me out when not using
    print("Sorry, no self-test code here!")
