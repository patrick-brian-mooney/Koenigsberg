#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# cython: language_level=3
"""A program intending to supply all possible paths that successfully traverse an
undirected graph while passing over each pathway exactly once. Paths are
considered "traversed" if they have been crossed in either direction. There is
no form of support for directed graphs.

The program name comes from "the Königsberg Bridge Problem," a specific example
of this type of problem, one which was solved by Leonard Euler in 1775; see
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
import sys
import traceback

from pathlib import Path
from typing import Union, Optional

try:
    import pyximport; pyximport.install()
except ImportError:
    print("Cython not completely imported! Running in pure-Python mode. This may crash if files are named improperly!")

import util

import koenigsberg_lib as kl


def read_graph_file(which_file: Union[str, Path]) -> dict:
    """Reads a JSON file containing graph-type data, as described in graph_to_dicts(),
    above. Performs some basic sanity checking.

    Graph files must be UTF-8 encoded JSON files. By convention, they have a .graph
    extension.
    """
    try:
        if not isinstance(which_file, Path):
            which_file = Path(which_file)
        util.log_it(f"Opening graph file {which_file.name} ...", util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)
        if which_file.suffix.lower() != ".graph":
            util.log_it("    Warning! File does not have a .graph suffix. Trying anyway.\n",
                        util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)

        with open(which_file, mode='rt', encoding='utf-8') as graph_file:
            graph = json.load(graph_file)
        util.log_it("File opened, performing sanity checks ...", util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)
        util._sanity_check_graph(graph)
        util.log_it("    ... sanity checks passed!\n", util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)

        return graph
    except (IOError, json.JSONDecodeError) as errrr:
        traceback.print_exception(type(errrr), errrr, errrr.__traceback__, chain=True)
        sys.exit(2)


def read_map_file(which_file: Union[str, Path]) -> dict:
    """Reads a JSON file containing a dictionary that encapsulates both a
    nodes- paths dict and a paths->nodes dict under the names expected by
    print_all_dict_solutions(), above. Performs some basic sanity checks.

    These map files must be UTF-8 encoded JSON files. By convention, they have a
    .map extension.
    """
    try:
        if not isinstance(which_file, Path):
            which_file = Path(which_file)
        util.log_it(f"Opening map file {which_file.name} ...", util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)
        if which_file.suffix.lower() != ".map":
            util.log_it("    Warning! File does not have a .map suffix. Trying anyway.\n",
                        util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)

        with open(which_file, mode='rt', encoding='utf-8') as graph_file:
            map = json.load(graph_file)

        util.log_it("File opened, performing sanity checks ...", util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)
        assert 'nodes to paths' in map, "File {which_file.name} does not have a 'nodes to paths' key!"
        assert 'paths to nodes' in map, "File {which_file.name} does not have a 'paths to nodes' key!"
        util._sanity_check_dicts(map['paths to nodes'], map['nodes to paths'])
        util.log_it("    ... sanity checks passed!\n", util.VERBOSITY_FRIENDLY_PROGRESS_CHATTER)

        return map
    except (IOError, json.JSONDecodeError) as errrr:
        traceback.print_exception(type(errrr), errrr, errrr.__traceback__, chain=True)
        sys.exit(2)


def parse_args(args) -> None:
    """Parse the arguments passed on the command line. Set any global parameters that
    need to be set, then perform the analysis indicated.
    """
    class ErrorCatchingArgumentParser(argparse.ArgumentParser):
        """More or less stolen outright from the Python docs.
        """
        def exit(self, status: int = 0, message: Optional[str] = None):
            if status:
                raise Exception(f'Exiting with status {status} because of a fatal error:\n{message}')
            exit(status)

    parser = ErrorCatchingArgumentParser(description=__doc__, prog="Königsberg", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--graph', '-g', type=Path, help="An appropriately formatted .graph file to solve exhaustively")
    parser.add_argument('--map', '-m', type=Path, help="An appropriately formatted .map file to solve exhaustively")

    parser.add_argument('--checkpoint-file', '--check', '-c', type=Path, help="Path to save and restore checkpointing data to. If unspecified, no checkpoints will be created.")
    parser.add_argument('--checkpoint-length', '--check-len', '-e', type=int, help="Lengths of paths that cause a checkpoint to be created; larger numbers lead to less frequent saves. This number must not be changed during a run, even if the run is stoppoed and resumed.")
    parser.add_argument('--min-save-interval', '--min-save', '-n', type=int, help="Minimum amount of time, in seconds, between checkpointing saves. Increasing this makes the program slightly faster but means you'll lose more progress if it's interrupted.")
    parser.add_argument('--abandoned-report-length-interval', '--abandoned-length', '-a', type=int, help=f"Length of paths that cause a status message to be emitted when the path is abandoned at verbosity level {util.VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS}.")
    parser.add_argument('--abandoned-report-number-interval', '--abandoned-number', '-r', type=int, help=f"Length of paths that cause a status message to be emitted when the path is abandoned at verbosity level {util.VERBOSITY_REPORT_SELECTED_ABANDONED_PATHS}.")
    parser.add_argument('--prune-exhausted-interval', '-p', type=int, help="Threshold for cleaning up the list of paths we've exhausted; doing this more often will make the program run faster when it's not cleaning this list but will make the list-cleaning action happen more often.")

    parser.add_argument('--verbose', '-v', action='count', default=1, help="Increase how chatty the program is about the progress it makes. May be specified multiple times.")
    parser.add_argument('--version', '--vers', '--ver', action='store_true', help="Display version information and exit.")
    args = parser.parse_args(args)

    util.verbosity = args.verbose
    if args.version:
        print(f'\n\nKönigsberg, version {kl.__version__}, by Patrick Mooney')
        print(f"Use {Path(__file__).resolve().name} --help for more help.\n\n")
        sys.exit(0)

    if args.checkpoint_file:
        kl.checkpoint_path = args.checkpoint_file
        kl.exhausted_paths = set()                      # Set up an empty set to be used to check progress.
        kl.do_load_progress()
    if args.checkpoint_length:
        kl.checkpoint_interval = args.checkpoint_length
    if args.min_save_interval:
        kl.min_save_interval = args.min_save_interval
    if args.abandoned_report_length_interval:
        kl.abandoned_paths_length_report_interval = args.abandoned_report_length_interval
    if args.abandoned_report_number_interval:
        kl.abandoned_paths_number_report_interval = args.abandoned_report_number_interval
    if args.prune_exhausted_interval:
        kl.exhausted_paths_prune_threshold = args.prune_exhausted_interval

    assert not (args.graph and args.map), "ERROR! Only one of --graph or --map may be specified."
    assert args.graph or args.map, "ERROR! One of --graph or --map must be specified."
    if args.graph:
        graph = read_graph_file(args.graph)
        kl.print_all_graph_solutions(graph)
    elif args.map:
        map = read_map_file(args.map)
        kl.print_single_dict_solutions(map)
    else:
        print("You must specify either --map or --graph!")
        sys.exit(2)


if __name__ == "__main__":
    #parse_args(["--map", "sample_data/Königsberg.map", "-r", "200", "-vvvvvvv"])
    # parse_args(sys.argv[1:])
    import cProfile
    cProfile.run("""parse_args(["--graph", "sample_data/ten_spot_hexlike.graph", '-v'])""", sort='time')
