#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""A program intending to supply all possible paths that successfully traverse an
undirected graph while passing over each pathway exactly once. Paths are
considered "traversed" if they have been crossed in either direction. There is
no form of support for directed graphs.

The program name comes from "the Königsberg Bridge Problem," a specific example
of this type of problem, once which was solved by Leonard Euler in 1775; see
https://www.maa.org/press/periodicals/convergence/leonard-eulers-solution-to-the-konigsberg-bridge-problem.
This code brute-forces the solution rather than applying Euler's solution.

Exit codes:
    0 - No errors during run.
    1 - (currently unused)
    2 - Invalid command-line argument, or files that were expected to contain
        input data were unreadable or malformed.
    3 - Input data did not pass sanity checks.

Verbosity levels:
    0 - Only report fatal errors and successful paths
    1 - also report when progress data is saved
    2 - also report basic info about how friendly interfaces are progressing
    3 - also report when selected exhausted paths are abandoned
    4 - also report when any exhausted path is abandoned

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""

import argparse
import json

from pathlib import Path

import sys
import traceback

from typing import Callable, Dict, Generator, Hashable, Iterable, Tuple, Type, Union


import util


# Constants
__version__ = "alpha"

# First, verbosity levels. Make these ENUMs when we Cythonize?
VERBOSITY_MINIMAL = 0
VERBOSITY_REPORT_PROGRESS_ON_SAVE = 1
VERBOSITY_FRIENDLY_PROGRESS_CHATTER = 2
VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS = 3
VERBOSITY_REPORT_ALL_ABANDONED_PATHS = 4

# Having to do with how often abandonded paths are reported at the level VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS
abandoned_paths_report_interval = 40

# Having to do with saving
checkpoint_interval = 10


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

        paths_not_in_nodes = set(paths_to_nodes.keys()) - set(util.flatten_list(nodes_to_paths.values()))
        assert not paths_not_in_nodes, f"Dictionary mapping paths to nodes has paths {paths_not_in_nodes} not connected to any node!"
        nodes_not_in_paths = set(nodes_to_paths.keys()) - set(util.flatten_list(paths_to_nodes.values()))
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
    check, err = _sanity_check_dicts(paths_to_nodes, nodes_to_paths, raise_error)
    if not check:
        traceback.print_exception(err, chain=True)
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
    check, err = _sanity_check_graph(graph)
    if not check:
        traceback.print_exception(err, chain=True)
        sys.exit(3)

    all_paths = set()
    for node, dest_list in graph.items():
        for dest in dest_list:
            all_paths.add(tuple(sorted([dest, node])))

    nodes_to_paths = {key: tuple(sorted([tuple(sorted([key, v])) for v in value])) for key, value in graph.items()}
    paths_to_nodes = {path: (path[0], path[1]) for path in sorted(all_paths)}

    return (paths_to_nodes, nodes_to_paths)


def log_it(message: str,                        # inline me when we Cythonize
           minimum_verbosity: int,
           current_verbosity_level: int) -> None:
    """Prints MESSAGE, provided that the current verbosity level, specified by
    CURRENT_VERBOSITY_LEVEL, is at least the MINIMUM_VERBOSITY specified for this
    message.
    """
    if current_verbosity_level >= minimum_verbosity:
        print(message)


def do_save(current_verbosity: int) -> None:
    """Save our current status, so we can restart from this point later.
    """
    log_it("Skipping regularly mandated save of progress data! #FIXME!", VERBOSITY_REPORT_PROGRESS_ON_SAVE, current_verbosity)


def path_is_pruned(path: bytearray) -> bool:
    """Return True if this is a path that we have already explored, e.g. in a previous
    run.
    """
    return False            #FIXME!


def _solve_from(paths_to_nodes: Dict[int, Tuple[int]],
               nodes_to_paths: Dict[int, Tuple[int]],
               start_from: int,
               steps_taken: bytearray,
               num_steps_taken: int,
               output_func: Callable,
               verbosity: int=1) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Recursively calls itself to solve the map described by PATHS_TO_NODES and
    NODES_TO_PATHS, starting from START_FROM, having already taken NUM_STEPS_TAKEN
    steps, which are recorded in the STEPS_TAKEN array. STEPS_TAKEN must be
    preallocated (and filled with zeroes) and is shared by each recursive invocation
    of this function; it's a scratch space that gets passed around, and copies of it
    are yielded when they turn into successful results.

    Yields nothing if there are no successful results.

    OUTPUT_FUNC must be a callable function that takes one parameter -- a bytearray
    that is the STEPS_TAKEN array -- and transforms it into a printed string. Use,
    e.g., util.default_path_formatter.

    VERBOSITY is the current verbosity level.

    Makes no attempts to verify that the data is sane -- call _sanity_check_dicts()
    for that.

    #FIXME! Does not save progress or emit status data of any kind.
    """
    if len(tuple(b for b in steps_taken if b)) == len(paths_to_nodes):     # if we've hit every path ...
        yield bytes(steps_taken)                        # emit a copy of the current path: it's a solution!
    else:
        next_steps = [p for p in nodes_to_paths[start_from] if p not in steps_taken]
        if next_steps:
            for next_path in next_steps:
                next_loc = [p for p in paths_to_nodes[next_path] if p != start_from][0]
                steps_taken[num_steps_taken] = next_path        # The step we're taking right now.
                yield from _solve_from(paths_to_nodes, nodes_to_paths, next_loc, steps_taken, 1+num_steps_taken, output_func, verbosity)
                steps_taken[num_steps_taken] = 0                # Free up the space for the step we just took
        else:
            if (len([b for b in steps_taken if b]) % abandoned_paths_report_interval) == 0:
                log_it(f"{' ' * len([b for b in steps_taken if b])} abandoned path {output_func(steps_taken)}.", VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS, verbosity)
            else:
                log_it(f"{' ' * len([b for b in steps_taken if b])} abandoned path {output_func(steps_taken)}.", VERBOSITY_REPORT_ALL_ABANDONED_PATHS, verbosity)
            if (num_steps_taken % checkpoint_interval) == 0:
                do_save(verbosity)


def solve_from(paths_to_nodes: Dict[int, Tuple[int]],
               nodes_to_paths: Dict[int, Tuple[int]],
               start_from: int,
               output_func: Callable,
               verbosity: int=1) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Friendly interface to _solve_from(), above. It does not require pre-allocation
    of a bytearray and it takes fewer parameters because it does not call itself
    recursively.
    """
    steps_taken = bytearray([0] * len(paths_to_nodes))
    yield from _solve_from(paths_to_nodes, nodes_to_paths, start_from, steps_taken, 0, output_func, verbosity)


def solve_from_multiple(paths_to_nodes: Dict[int, Tuple[int]],
                        nodes_to_paths: Dict[int, Tuple[int]],
                        starts_from: Iterable[int],
                        output_func: Callable,
                        verbosity: int=1) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Convenience function: repeatedly solve the map described by PATHS_TO_NODES and
    by NODES_TO_PATHS by starting from all of the paths in STARTS_FROM, an iterable
    of starting locations.

    It is unlikely, but possible in theory, that this function may emit "the same
    solution" more than once if it's possible to follow the same sequence of paths
    from different starting points.
    """
    steps_taken = bytearray([0] * len(paths_to_nodes))
    for start in starts_from:
        yield from _solve_from(paths_to_nodes, nodes_to_paths, start, steps_taken, 0, output_func, verbosity)


def solve_from_all(paths_to_nodes: Dict[int, Tuple[int]],
                   nodes_to_paths: Dict[int, Tuple[int]],
                   output_func: Callable,
                   verbosity: int=1) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Convenience function: solves the PATHS_TO_NODES/NODES_TO_PATHS maps passed in,
    in the same way as solve_from_multiple(), but from every possible starting
    point, not just selected ones.
    """
    yield from solve_from_multiple(paths_to_nodes, nodes_to_paths, nodes_to_paths.keys(), output_func, verbosity)


def print_all_dict_solutions(single_dict: dict,
                             verbosity: int=1) -> None:
    """Friendly interface that bundles together all of the various components of a
    generic solution that works fine for many purposes much of the time. It takes
    SINGLE_DICT, a parameter that bundles together both dictionaries describing a
    map into a single dictionary with the following format:
    {
        'nodes to paths': {  [ a valid nodes_to_paths dictionary ]  },
        'paths to nodes': {  [ a valid paths_to_nodes dictionary ]  }
    }

    It also allows the caller to specify a VERBOSITY level.

    Given those parameters, it normalizes the dictionaries, finds all solutions, and
    prints them using the default solution formatter.
    """
    p, n, p_trans, n_trans, p_trans_rev, n_trans_rev = normalize_dicts(single_dict['paths to nodes'], single_dict['nodes to paths'])
    formatter = util.default_path_formatter(p_trans)

    sol_found = False
    for i, path in enumerate(solve_from_all(p, n, formatter, verbosity), 1):
        print(f"Solution #{i}: \t {formatter(path)}")
        sol_found = True

    print("All paths examined!")
    if not sol_found:
        print("    No solutions found!")


def print_all_graph_solutions(graph: dict,
                              verbosity: int=1) -> None:
    """Friendly interfact that takes a graph, as defined in graph_to_dicts(), above,
    and finds, then prints, all solutions from any point, just as
    print_all_dict_solutions(), above, does for maps represented by dicts.
    """
    p_to_n, n_to_p = graph_to_dicts(graph)
    print_all_dict_solutions(graph, verbosity)


def read_graph_file(which_file: Union[str, Path],
                    verbosity: int=1) -> dict:
    """Reads a JSON file containing graph-type data, as described in graph_to_dicts(),
    above. Performs some basic sanity checking.

    Graph files must be UTF-8 encoded JSON files. By convention, they have a .graph
    extension.
    """
    try:
        if not isinstance(which_file, Path):
            which_file = Path(which_file)
        log_it(f"Opening graph file {which_file.name} ...", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)
        if which_file.suffix.lower() != ".graph":
            log_it("    Warning! File does not have a .graph suffix. Trying anyway.\n", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)

        with open(which_file, mode='rt', encoding='utf-8') as graph_file:
            graph = json.load(graph_file)
        log_it("File opened, performing sanity checks ...", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)
        _sanity_check_graph(graph)
        log_it("    ... sanity checks passed!\n", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)

        return graph
    except (IOError, json.JSONDecodeError) as errrr:
        traceback.print_exception(errrr, chain=True)
        sys.exit(2)


def read_map_file(which_file: Union[str, Path],
                  verbosity: int = 1) -> dict:
    """Reads a JSON file containing a dictionary that encapsulates both a
    nodes- paths dict and a paths->nodes dict under the names expected by
    print_all_dict_solutions(), above. Performs some basic sanity checks.

    These map files must be UTF-8 encoded JSON files. By convention, they have a
    .map extension.
    """
    try:
        if not isinstance(which_file, Path):
            which_file = Path(which_file)
        log_it(f"Opening map file {which_file.name} ...", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)
        if which_file.suffix.lower() != ".map":
            log_it("    Warning! File does not have a .map suffix. Trying anyway.\n", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)

        with open(which_file, mode='rt', encoding='utf-8') as graph_file:
            map = json.load(graph_file)

        log_it("File opened, performing sanity checks ...", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)
        assert 'nodes to paths' in map, "File {which_file.name} does not have a 'nodes to paths' key!"
        assert 'paths to nodes' in map, "File {which_file.name} does not have a 'paths to nodes' key!"
        _sanity_check_dicts(map['paths to nodes'], map['nodes to paths'])
        log_it("    ... sanity checks passed!\n", VERBOSITY_FRIENDLY_PROGRESS_CHATTER, verbosity)

        return map
    except (IOError, json.JSONDecodeError) as errrr:
        traceback.print_exception(errrr, chain=True)
        sys.exit(2)


def parse_args(args) -> None:
    parser = argparse.ArgumentParser(description=__doc__, prog="Königsberg")
    parser.add_argument('--graph', '-g', type=Path)
    parser.add_argument('--map', '-m', type=Path)
    parser.add_argument('--verbose', '-v', action='count', default=1)
    parser.add_argument('--version', action='version', version=f'Königsberg {__version__}, by Patrick Mooney')
    args = parser.parse_args(args)
    assert not (args.graph and args.map), "ERROR! Only one of --graph or --map must be specified."
    if args.graph:
        graph = read_map_file(args.graph)
        print_all_graph_solutions(graph, args.verbose)
    elif args.map:
        map = read_map_file(args.map)
        print_all_dict_solutions(map, args.verbose)
    else:
        print("You must specify either --map or --graph!")
        sys.exit(1)



if __name__ == "__main__":
    # parse_args(sys.argv[1:])
    parse_args(['--graph', '/tmp/hello.json', '-v', '-v', '-v', '-v'])

