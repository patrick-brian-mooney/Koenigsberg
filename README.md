# Koenigsberg (alpha version)

Graph analysis tool by <a rel="author" href="https://patrickbrianmooney.nfshost.com/~patrick/">Patrick Mooney</a>

## Overview

Koenigsberg brute-forces certain problems in graph theory that are analogous to "the Königsberg Bridge Problem," which was solved without brute-forcing it by by Leonard Euler in 1775; see Teo Paoletti's [writeup](
https://www.maa.org/press/periodicals/convergence/leonard-eulers-solution-to-the-konigsberg-bridge-problem) for an overview of this problem and Euler's solution.

"Königsberg problems," as this program calls them, are problems that consist of (a) a map in which nodes are connected by pathways; and (b) the problem is to attempt to find a pathway through the network that traverses each connection exactly once. Königsberg provides a set of tools to help solve these problems by brute force: it is a command-line program that operates on pre-created files describing the connections between nodes and networks, and also a set of Python libraries that allow these pre-defined libraries to be scripted using the Python programming language.

## Quick reference

<code><pre>
  -h, --help
                        show this help message and exit

  --graph GRAPH, -g GRAPH
                        An appropriately formatted .graph file to solve exhaustively

  --map MAP, -m MAP
                        An appropriately formatted .map file to solve exhaustively

  --checkpoint-file CHECKPOINT_FILE, --check CHECKPOINT_FILE, -c CHECKPOINT_FILE
                        Path to save and restore checkpointing data to. If unspecified, no checkpoints will be created.

  --checkpoint-length CHECKPOINT_LENGTH, --check-len CHECKPOINT_LENGTH, -e CHECKPOINT_LENGTH
                        Lengths of paths that cause a checkpoint to be created; larger numbers lead to less frequent saves. This number must not be changed during a run, even if the run is stopped and resumed.

  --min-save-interval MIN_SAVE_INTERVAL, --min-save MIN_SAVE_INTERVAL, -n MIN_SAVE_INTERVAL
                        Minimum amount of time, in seconds, between checkpointing saves. Increasing this makes the program slightly faster but means you'll lose more progress if it's interrupted.

  --abandoned-report-length-interval ABANDONED_REPORT_LENGTH_INTERVAL, --abandoned-length ABANDONED_REPORT_LENGTH_INTERVAL, -a ABANDONED_REPORT_LENGTH_INTERVAL
                        Length of paths that cause a status message to be emitted when the path is abandoned at verbosity level 3.

  --abandoned-report-number-interval ABANDONED_REPORT_NUMBER_INTERVAL, --abandoned-number ABANDONED_REPORT_NUMBER_INTERVAL, -r ABANDONED_REPORT_NUMBER_INTERVAL
                        Length of paths that cause a status message to be emitted when the path is abandoned at verbosity level 3.

  --prune-exhausted-interval PRUNE_EXHAUSTED_INTERVAL, -p PRUNE_EXHAUSTED_INTERVAL
                        Threshold for cleaning up the list of paths we've exhausted; doing this more often will make the program run faster when it's not cleaning this list but will make the list-cleaning action happen more often.

  --verbose, -v
                        Increase how chatty the program is about the progress it makes. May be specified multiple times.

  --version, --vers, --ver
                        Display version information and exit.
</pre></code>

## More information

See [the file docs/manual.md](docs/manual.md) for more information.

## License

Königsberg is licensed under the GPL, either version 3 or (at your option) any later version. See [the LICENSE.md file](LICENSE.md) for a copy of this license.
