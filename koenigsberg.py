#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""A program intending to supply all possible paths that successfully traverse an
undirected graph while passing over each pathway exactly once. Paths are
considered "traversed" if they have been crossed in either direction. There is
no other form of support for directed graphs, either.

The name comes from "the Königsberg Bridge Problem," a specific example of this
type of problem, once which was solved by Leonard Euler in 1775; see
https://www.maa.org/press/periodicals/convergence/leonard-eulers-solution-to-the-konigsberg-bridge-problem.
This code brute-forces the solution rather than applying Euler's solution.

Exit codes:
    0 - No errors during run.
    1 - Input data did not pass sanity checks.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import sys
import traceback

from typing import Any, Dict, Generator, Hashable, Iterable, Mapping, Tuple, Type, Union


import util


def _sanity_check_graph(graph: Dict[Hashable, Iterable[Hashable]],
                        raise_error: bool = True,
                        ) -> Tuple[bool, Union[Type[BaseException], None]]:
    """Perform basic sanity checks on the dictionaries PATHS_TO_NODES and
    NODES_TO_PATHS. If RAISE_ERROR is True, failing a sanity check raises a
    ValueError (and execution terminates); if it is False, the function returns
    False instead of crashing.
    """
    try:
        for node, dest_list in graph.items():
            assert isinstance(node, Hashable), f"Node {node} in the supplied graph is not a hashable value, and cannot be used as a node label!"
            assert isinstance(dest_list, Iterable), f"The destination list for node {node} in the supplied graph is not a list-like object!"
            assert not isinstance(dest_list, (str, bytes, bytearray)), f"The destination list for node {node} is a string or string-like object of type {type(dest_list)}, and these cannot be used as destination lists for graphs!"
            for dest in dest_list:
                assert isinstance(dest, Hashable), f"The destination node {dest} given in the destination list for the node {node} in the supplied graph is not a hashable value, and cannot be used as the label for a node!"
                assert dest in graph, f"The node {node} in the supplied graph is marked as going to the node {dest}, but that second node does not have any outbound paths listed!"
                assert node in graph[dest], f"The node {node} in the supplied graph is marked as going to the node {dest}, but that second node is not marked as leading back to {node}! (All pathways between nodes must explicitly be bidirectional.)"

        #FIXME! More tests?
        return True, None
    except BaseException as errrr:
        if raise_error:
            raise ValueError("Unable to validate supplied input data!") from errrr
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
            raise ValueError("Unable to validate supplied input data!") from errrr
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
        sys.exit(1)

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
        sys.exit(1)

    all_paths = set()
    for node, dest_list in graph.items():
        for dest in dest_list:
            all_paths.add(tuple(sorted([dest, node])))

    nodes_to_paths = {key: tuple(sorted([tuple(sorted([key, v])) for v in value])) for key, value in graph.items()}
    paths_to_nodes = {path: (path[0], path[1]) for path in sorted(all_paths)}

    return (paths_to_nodes, nodes_to_paths)



def solve_from(paths_to_nodes: Dict[int, Tuple[int]],
               nodes_to_paths: Dict[int, Tuple[int]],
               start_from: int,
               steps_taken: bytearray,
               num_steps_taken: int) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Recursively calls itself to solve the map described by PATHS_TO_NODES and
    NODES_TO_PATHS, starting from START_FROM, having already taken NUM_STEPS_TAKEN
    steps, which are recorded in the STEPS_TAKEN array. STEPS_TAKEN must be
    preallocated (and filled with zeroes) and is shared by each recursive invocation
    of this function; it's a scratch space that gets passed around, and copies of it
    are yielded when they turn into successful results.

    Yields nothing if there are no successful results.

    Makes no attempts to verify that the data is sane -- call _sanity_check_dicts()
    for that.

    #FIXME! Does not save progress or emit status data of any kind.
    """
    if len(tuple(b for b in steps_taken if b)) == len(paths_to_nodes):     # if we've hit every path ...
        yield bytes(steps_taken)                        # emit a copy of the current path: it's a solution!
    else:
        for next_path in [p for p in nodes_to_paths[start_from] if p not in steps_taken]:
            next_loc = [p for p in paths_to_nodes[next_path] if p != start_from][0]
            steps_taken[num_steps_taken] = next_path        # The step we're taking right now.
            yield from solve_from(paths_to_nodes, nodes_to_paths, next_loc, steps_taken, 1+num_steps_taken)
            steps_taken[num_steps_taken] = 0                # Free up the space for the step we just took


def solve_from_multiple(paths_to_nodes: Dict[int, Tuple[int]],
                        nodes_to_paths: Dict[int, Tuple[int]],
                        starts_from: Iterable[int],
                        steps_taken: bytearray) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Convenience function: repeatedly solve the map described by PATHS_TO_NODES and
    by NODES_TO_PATHS by starting from all of the paths in STARTS_FROM, an iterable
    of starting locations.

    It is unlikely, but possible in theory, that this function may emit "the same
    solution" more than once if it's possible to follow the same sequence of paths
    from different starting points.
    """
    for start in starts_from:
        yield from solve_from(paths_to_nodes, nodes_to_paths, start, steps_taken, 0)


def solve_from_all(paths_to_nodes: Dict[int, Tuple[int]],
                   nodes_to_paths: Dict[int, Tuple[int]],
                   steps_taken: bytearray) -> Generator[Iterable[Tuple[Hashable]], None, None]:
    """Convenience function: solves the PATHS_TO_NODES/NODES_TO_PATHS maps passed in,
    in the same way as solve_from_multiple(), but from every possible starting
    point, not just selected ones.
    """
    yield from solve_from_multiple(paths_to_nodes, nodes_to_paths, nodes_to_paths.keys(), steps_taken)


def koenigsberg_sample_test() -> None:
    import sample_data as sd
    p, n, p_trans, n_trans, p_trans_rev, n_trans_rev = normalize_dicts(sd.Königsberg['paths to nodes'], sd.Königsberg['nodes to paths'])

    path = bytearray([0] * 7)

    sol_found = False
    for i, path in enumerate(solve_from(p, n, n_trans_rev['A'], path, 0), 1):
        print(f"Solution #{i}: \t {path}")
        sol_found = True

    print("All paths examined!")
    if not sol_found:
        print("    No solutions found!")


if __name__ == "__main__":
    import sample_data as sd

    hexagon = sd.hex_ring
    p_to_n, n_to_p = graph_to_dicts(hexagon)

    p, n, p_trans, n_trans, p_trans_rev, n_trans_rev = normalize_dicts(p_to_n, n_to_p)
    path = bytearray([0] * len(p_to_n))

    sol_found = False
    for i, path in enumerate(solve_from(p, n, 1, path, 0), 1):
        print(f"Solution #{i}: \t {path}")
        sol_found = True

    print("All paths examined!")
    if not sol_found:
        print("    No solutions found!")

