#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# cython: language_level=3
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
    3 - also report when selected exhausted paths are abandoned, and give total abandoned paths at that time.
    4 - also report when any exhausted path is abandoned, and give total examined paths at that time.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import bz2
import pickle
import time

from pathlib import Path
from typing import Callable, Dict, Generator, Hashable, Iterable, Tuple

import util


# Constants
__version__ = "alpha"

# File system locations
script_home = Path(__file__).parent.resolve()
sample_data = script_home / 'sample_data'

# Global variables tracking the list of paths that have been explored exhaustively.
exhausted_paths = None              # or a set(), if we're tracking progress
cdef long paths_length_at_last_prune = 0
cdef long total_paths_exhausted_num = 0

# Global variables tracking solutions found.
cdef set solutions = set()

# Global variables that can be set with command_line parameters follow

# Having to do with saving
checkpoint_interval = 10              # save occurs when length of path being abandoned is a multiple of this number
min_save_interval = 15 * 60           # seconds
last_save = time.monotonic()
checkpoint_path = None                          # or a Path

# Having to do with how often abandoned paths are reported at the level VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS
abandoned_paths_length_report_interval = 8
abandoned_paths_number_report_interval = 100000

# Having to do with how often the list of exhausted paths is pruned.
exhausted_paths_prune_threshold = 1000      #FIXME! Experiment with this value

# The function used to convert a bytearray into a printed output path
output_func = lambda the_bytes, *args: ''.join(chr(o) for o in the_bytes)

# Other globals
run_start = time.monotonic()


cpdef void reset_data(bint confirm=False):
    """Reset the variables used to track progress to their initial values.
    """
    global exhausted_paths, solutions, paths_length_at_last_prune, total_paths_exhausted_num, run_start
    if not confirm: 
        print("ERROR! reset_data() called without confirm=True. To avoid accidentally scuttling progres data, reset_data() must be called while manually passing confirm=True.")
        return

    exhausted_paths = None
    solutions = set()
    paths_length_at_last_prune = 0
    total_paths_exhausted_num = 0
    run_start = time.monotonic()


cdef void do_prune_exhausted_paths_list() except *:
    """Prune the list of exhausted paths so that it consists only of the shortest paths
    that represents the path, in which each bytestring is a list of intersections
    that have been exhaustively traversed and in which having 0x010x020x030x04 in
    addition to 0x010x020x03 is redundant: the second includes enough information to
    show that the first is redundant.

    Pruning takes time, but speeds up the "can we skip this path" test, so it helps
    overall ... up to a point. How often pruning happens can be adjusted with the
    --prune-exhausted-interval switch, which adjusts the threshold of how many new
    paths can be added to the list before the list is pruned.
    """
    cdef bytes p
    cdef set pruned_paths_list
    cdef long length

    global exhausted_paths, paths_length_at_last_prune

    if not exhausted_paths:
        return

    pruned_paths_list = set()
    for p in sorted(exhausted_paths, key=len):
        for length in range(1+len(p)):
            if bytes(p[:length]) in pruned_paths_list:
                break
        else:
            pruned_paths_list.add(p)

    exhausted_paths = pruned_paths_list
    paths_length_at_last_prune = len(pruned_paths_list)


def do_save(even_if_not_time: bool = False,
            suppress_prune: bool = False) -> None:
    """Save our current status, so we can restart from this point later.
    """
    global solutions, exhausted_paths, total_paths_exhausted_num, run_start, last_save

    if not checkpoint_path:         # no checkpoint file defined? We're not saving!
        return
    if (not even_if_not_time) and ((time.monotonic() - last_save) < min_save_interval):
        return
    if not suppress_prune:
        do_prune_exhausted_paths_list()

    data = {
        'solutions': solutions,
        'exhausted_paths': exhausted_paths,
        'num_exhausted': total_paths_exhausted_num,
        'total_time': time.monotonic() - run_start,
    }

    if checkpoint_path.exists():
        checkpoint_path.rename(checkpoint_path.with_suffix(checkpoint_path.resolve().suffix + '.bak'))
    with bz2.open(checkpoint_path, mode='wb') as checkpoint_file:
        pickle.dump(data, checkpoint_file, protocol=-1)

    util.log_it(f"Progress saved to {checkpoint_path.name}! {len(solutions)} solutions found and {total_paths_exhausted_num} paths exhaused in {data['total_time'] / 60:.10} minutes.",
                util.VERBOSITY_REPORT_PROGRESS_ON_SAVE)
    last_save = time.monotonic()


def do_load_progress() -> None:
    """Restore progress from the file at the global CHECKPOINT_PATH variable, if it
    exists; if it doesn't, report that it doesn't, and that we're restarting from
    scratch.
    """
    global solutions, exhausted_paths, total_paths_exhausted_num, run_start

    util.log_it(f"  ... opening progress file {checkpoint_path.name} ...", util.VERBOSITY_REPORT_PROGRESS_ON_SAVE)
    try:
        with bz2.open(checkpoint_path, mode='rb') as checkpoint_file:
            data = pickle.load(checkpoint_file)
        solutions = data['solutions']
        exhausted_paths = data['exhausted_paths']
        total_paths_exhausted_num = data['num_exhausted']
        run_start = time.monotonic() - data['total_time']
        print(f"  ... data loaded from {checkpoint_path.name}!")
    except (IOError, pickle.PickleError) as errrr:
        print(f"Warning! Cannot load progress data from {checkpoint_path.name}; the system said: {errrr}")
        print("Starting from scratch.")


cdef bint path_is_pruned(bytearray path) except? 127:        # 127 should never be a value that the function returns
    """Return True if this is a path that we have already explored, e.g. in a previous
    run.
    """
    global exhausted_paths

    if not exhausted_paths: return False

    for length in range(1, 1 + len([node for node in path if node])):
        if bytes(path[:length]) in exhausted_paths:
            return True
    return False


cdef void _solve_from(dict paths_to_nodes,       # Dict[int, Tuple[int]]
                      dict nodes_to_paths,       # Dict[int, Tuple[int]]
                      int start_from,
                      bytearray steps_taken,
                      int num_steps_taken) except *:
    """Recursively calls itself to solve the map described by PATHS_TO_NODES and
    NODES_TO_PATHS, starting from START_FROM, having already taken NUM_STEPS_TAKEN
    steps, which are recorded in the STEPS_TAKEN array. STEPS_TAKEN must be
    preallocated (and filled with zeroes) and is shared by each recursive invocation
    of this function; it's a scratch space that gets passed around, and copies of it
    are formatted and printed when they turn into successful results.

    Prints nothing if there are no successful results.
    Makes no attempts to verify that the data is sane -- call _sanity_check_dicts()
    before beginning for that.

    This function is not meant to be end-user accessible; use a friendly front-end,
    below, to get the ball rolling. Rather than friendly and accessible from outside
    this module, this function is intended to be *fast*.
    """
    global output_func
    global exhausted_paths, solutions
    global exhausted_paths_prune_threshold, paths_length_at_last_prune, total_paths_exhausted_num

    if num_steps_taken == len(paths_to_nodes):                  # if we've hit every path ... we have a solution!
        sol = bytes([s for s in steps_taken if s])              # create a copy of the current path
        solutions.add(sol)                                      # add it to the set of solutions
        print(output_func(steps_taken, num_steps_taken))        # print it

    else:                                                       # We have not explored every possible path on this journey.
        next_steps = [p for p in nodes_to_paths[start_from] if p not in steps_taken]
        if next_steps:
            for next_path in sorted(next_steps):
                next_loc = [p for p in paths_to_nodes[next_path] if p != start_from][0]
                steps_taken[num_steps_taken] = next_path        # The step we're taking right now.
                if (not exhausted_paths) or (not path_is_pruned(steps_taken)):
                    _solve_from(paths_to_nodes, nodes_to_paths, next_loc, steps_taken, 1+num_steps_taken)
                steps_taken[num_steps_taken] = 0                # Free up the space for the step we just took

        else:
            total_paths_exhausted_num += 1
            if exhausted_paths is not None:
                exhausted_paths.add(bytes((s for s in steps_taken if s)))
                if len(exhausted_paths) > (exhausted_paths_prune_threshold + paths_length_at_last_prune):
                    do_prune_exhausted_paths_list()

            if (total_paths_exhausted_num % abandoned_paths_number_report_interval) == 0:
                util.log_it(f"  {total_paths_exhausted_num / 1000000:.6f} million exhausted paths",
                            util.VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS)

            if (num_steps_taken % abandoned_paths_length_report_interval) == 0:
                util.log_it(f"{' ' * len([b for b in steps_taken if b])} abandoned path {output_func(steps_taken, num_steps_taken)}.",
                            util.VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS)
            # Calculating a textual representation of a path is time-consuming, so we pre-test the verbosity level
            # before dispatching to a function that calls the path-formatting function
            elif util.verbosity >= util.VERBOSITY_REPORT_ALL_ABANDONED_PATHS:
                util.log_it(f"{' ' * len([b for b in steps_taken if b])} abandoned path {output_func(steps_taken, num_steps_taken)}.",
                            util.VERBOSITY_REPORT_ALL_ABANDONED_PATHS)
            if exhausted_paths and ((num_steps_taken % checkpoint_interval) == 0):
                do_save()


def solve_from(paths_to_nodes: Dict[int, Tuple[int]],
               nodes_to_paths: Dict[int, Tuple[int]],
               start_from: int) -> None:
    """Friendly interface to _solve_from(), above. It does not require pre-allocation
    of a bytearray and it takes fewer parameters because it does not call itself
    recursively.
    """
    steps_taken = bytearray([0] * len(paths_to_nodes))
    _solve_from(paths_to_nodes, nodes_to_paths, start_from, steps_taken, 0)


def solve_from_multiple(paths_to_nodes: Dict[int, Tuple[int]],
                        nodes_to_paths: Dict[int, Tuple[int]],
                        starts_from: Iterable[int]) -> None:
    """Convenience function: repeatedly solve the map described by PATHS_TO_NODES and
    by NODES_TO_PATHS by starting from all of the paths in STARTS_FROM, an iterable
    of starting locations.

    It is unlikely, but possible in theory, that this function may emit "the same
    solution" more than once if it's possible to follow the same sequence of paths
    from different starting points.
    """
    steps_taken = bytearray([0] * len(paths_to_nodes))
    for start in starts_from:
        _solve_from(paths_to_nodes, nodes_to_paths, start, steps_taken, 0)


def solve_from_all(paths_to_nodes: Dict[int, Tuple[int]],
                   nodes_to_paths: Dict[int, Tuple[int]]) -> None:
    """Convenience function: solves the PATHS_TO_NODES/NODES_TO_PATHS maps passed in,
    in the same way as solve_from_multiple(), but from every possible starting
    point, not just selected ones.
    """
    solve_from_multiple(paths_to_nodes, nodes_to_paths, nodes_to_paths.keys())


def print_all_dict_solutions(paths_to_nodes: dict, 
                             nodes_to_paths: dict,
                             path_formatter: typing.Optional[typing.Callable[[int], str]] = None) -> None:
    """Friendly interface that bundles together all of the various components of a
    generic solution that works fine for many purposes much of the time. It takes a
    PATHS_TO_NODES and a NODES_TO_PATHS dictionary.

    Given those parameters, it normalizes the dictionaries, finds all solutions, and
    prints them using the default solution formatter.
    """
    global output_func

    p, n, p_trans, n_trans, p_trans_rev, n_trans_rev = util.normalize_dicts(paths_to_nodes, nodes_to_paths)
    output_func = path_formatter or util.default_path_formatter(p_trans)

    solve_from_all(p, n)

    print("All paths examined!")
    if solutions:
        print(f"    {len(solutions)} solutions found!\n\n\n")
    else:
        print("    No solutions found!\n\n\n")


def print_single_dict_solutions(single_dict: dict,
                                path_formatter: typing.Optional[typing.Callable[[int], str]] = None) -> None:
    """Friendly, high-level interface to print_all_dict_solutions; a convenience
    function for command-line use that takes  SINGLE_DICT, a parameter that bundles
    together both dictionaries describing a map into a single dictionary with the
    following format:

    {
        'nodes to paths': {  [ a valid nodes_to_paths dictionary ]  },
        'paths to nodes': {  [ a valid paths_to_nodes dictionary ]  }
    }
    """
    print_all_dict_solutions(single_dict['paths to nodes'], single_dict['nodes to paths'], path_formatter)


def print_all_graph_solutions(graph: dict,
                              path_formatter: typing.Optional[typing.Callable[[int], str]] = None) -> None:
    """Friendly interface that takes a graph, as defined in graph_to_dicts(), and
    finds, then prints, all solutions from any point, just as
    print_all_dict_solutions(), above, does for maps represented by dicts.
    """
    p_to_n, n_to_p = util.graph_to_dicts(graph)
    print_all_dict_solutions(p_to_n, n_to_p, path_formatter)


if __name__ == "__main__":
    # test harness
    import koenigsberg
    koenigsberg.parse_args(['--graph', '/tmp/hello.json', '-v', '-v', '-v', '-v'])

