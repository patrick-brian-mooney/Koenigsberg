#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests and other testing code for Patrick Mooney's Königsberg.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import unittest

import koenigsberg
import koenigsberg_lib as kl
import util


def limited_koenigsberg_sample_test() -> None:
    sd = koenigsberg.read_map_file('sample_data/Königsberg.map')
    p, n, p_trans, n_trans, p_trans_rev, n_trans_rev = kl.normalize_dicts(sd['paths to nodes'], sd['nodes to paths'])
    formatter = util.default_path_formatter(p_trans)

    sol_found = False
    for i, path in enumerate(kl.solve_from(p, n, n_trans_rev['A'], formatter), 1):
        print(f"Solution #{i}: \t {p_trans(path)}")
        sol_found = True

    print("All paths examined!")
    if not sol_found:
        print("    No solutions found!")


def full_koenigsberg_sample_test() -> None:
    map = koenigsberg.read_map_file('sample_data/Königsberg.map')
    kl.print_all_dict_solutions(map['paths to nodes'], map['nodes to paths'])


def hex_ring_sample_test() -> None:
    kl.print_all_graph_solutions(koenigsberg.read_graph_file('sample_data/hex_ring.graph'))


def dense_polygon_sample_test(sides: int = 6) -> None:
    # FIXME: this fails to operate properly when sides = 5. Why?
    p_to_n, n_to_p = kl.graph_to_dicts(util.maximally_dense_network_graph(sides))
    kl.print_all_dict_solutions(paths_to_nodes=p_to_n, nodes_to_paths=n_to_p)


class TestDataSanityChecks(unittest.TestCase):
    @unittest.skip("Command-line parsing tests don't work yet.")
    def test_command_line(self) -> None:
        with self.assertRaises(Exception):
            # FIXME! Doesn't currently work!
            koenigsberg.parse_args(['--graph', '/tmp/hello.json', '--map', '/tmp/hello.json'])

    def test_graph_sanity(self) -> None:
        with self.assertRaises(ValueError):
            # GRAPH must be a dict
            koenigsberg._sanity_check_graph(graph=[1, 2, 3, 4])
            # GRAPH values must be an iterable
            koenigsberg._sanity_check_graph(graph={1: 2})
            # GRAPH values must not be strings or similar, even though those are iterable too
            koenigsberg._sanity_check_graph(graph={1: "ABC"})
            # values in GRAPH destination lists must contain hashable objects
            koenigsberg._sanity_check_graph(graph={1: (1, 2, 3, [4, 5, 6]), 2: (1, 3), 3: (1, 2)})
            # values in GRAPH destination list must also be nodes that occur in the keys of the same graph dictionary
            koenigsberg._sanity_check_graph(graph={1: (2, 3, 4), 2: (1, 3), 3: (1, 2)})
            # graphs that map A -> B must also map B -> A
            koenigsberg._sanity_check_graph(graph={1: (2, 3, 4), 2: (3, 4), 3: (1, 2), 4: (1, 2)})

    def test_dict_pair_sanity(self) -> None:
        with self.assertRaises(ValueError):
            # PATHS_TO_NODES and NODES_TO_PATHS must be dicts
            koenigsberg._sanity_check_dicts(paths_to_nodes=True, nodes_to_paths=dict())
            koenigsberg._sanity_check_dicts(paths_to_nodes=dict(), nodes_to_paths=True)
            # max possible paths is 255
            koenigsberg._sanity_check_dicts(paths_to_nodes={k: True for k in range(1000)}, nodes_to_paths={})
            # all nodes mentioned as part of paths must be mentioned in keys of nodes dict
            koenigsberg._sanity_check_dicts(paths_to_nodes={(1, 2): (1, 2), (1, 4): (1, 4), (2, 3): (2, 3), (3, 4): (3, 4)},
                                            nodes_to_paths={1: ((1, 2), (1, 4)), 2: ((1, 2), (2, 3)), 4: ((1, 4), (3, 4))})
            # all nodes mentioned in keys of nodes dict must be mentioned in lists in path dict
            koenigsberg._sanity_check_dicts(paths_to_nodes={(2, 3): (2, 3), (3, 4): (3, 4)},
                                            nodes_to_paths={1: ((1, 2), (1, 4)), 2: ((1, 2), (2, 3)), 3: ((2, 3), (3, 4)), 4: ((1, 4), (3, 4))})
            # node lists in paths_to_nodes must be iterable -- probably inevitably caught by previous rules, but check explicitly
            koenigsberg._sanity_check_dicts(paths_to_nodes={'hello': True, 'there': (1, 2)}, nodes_to_paths={True: (1, 2, 'hello'), (1, 2, 3): False})
            # paths in path-to-node node lists must connect exactly two nodes
            koenigsberg._sanity_check_dicts(paths_to_nodes={'hello': (1, 2), 'there': (1, 2, 3)}, nodes_to_paths={1: ('hello'), 2: ('hello', 'there'), 3: ('there')})
            # nodes mentioned in PATHS_TO_NODES list must also appear as keys in NODES_TO_PATHS
            koenigsberg._sanity_check_dicts(paths_to_nodes={'hello': (1, 2), 'there': (2, 3), 'young': (3, 4), 'fellow': (1, 3)},
                                            nodes_to_paths={1: ('hello', 'fellow'), 2: ('hello', 'there'), 3: ('there', 'young', 'fellow')})
            # path lists that occur in the values of NODES_TO_PATHS must be iterable.
            koenigsberg._sanity_check_dicts(paths_to_nodes={'hello': (1, 2), 'there': (2, 3), 'young': (3, 4), 'fellow': (1, 3)},
                                            nodes_to_paths={1: ('hello', 'fellow'), 2: ('hello', 'there'), 3: ('there', 'young', 'fellow'), 4: None})
            # paths appearing in the values of NODES_TO_PATHS must only contain paths that appear as keys in paths_to_nodes
            koenigsberg._sanity_check_dicts(paths_to_nodes={(1, 2): (1, 2), (1, 4): (1, 4), (2, 3): (2, 3)},
                                            nodes_to_paths={1: ((1, 2), (1, 4)), 2: ((1, 2), (2, 3)), 3: ((2, 3), (3, 4)), 4: ((1, 4), (3, 4))})


if __name__ == "__main__":
    unittest.main()

