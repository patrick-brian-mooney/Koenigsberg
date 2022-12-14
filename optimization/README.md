# `Optimization/`

Output of various versions of the script, including timing information, as the script is converted from pure-Python to Cython. These occur in both plain-text format and <a rel="muse" href="https://asciinema.org/">ASCIInema</a> JSON (as `.cast` files). ASCIInama `.cast` files are recorded with a terminal size of 100&nbsp;x&nbsp;25.

All timing runs were performed on the same computer using Python 3.9 under x64 Linux Mint 20.1, with a similar load of background processes running at the time.

The standard invocation of the script for timing purposes is something very close to `./koenigsberg.py 2>&1 | tee timing/pre-optimization/pre-optimization.txt`, with the filenames adjusted as necessary. The internal call to `cProfile` looks like `cProfile.run("""parse_args(["--graph", "sample_data/ten_spot_hexlike.graph", '-v'])""", sort='time')`.

## `pre-optimization/`
The pure-Python version of the program<!--, as it occurs in [commit 0a329421d5675de3606f9079cf0e9e32102074d7](https://github.com/patrick-brian-mooney/IF-utils/commit/0a329421d5675de3606f9079cf0e9e32102074d7)-->. Took 24.846 seconds to run the sample problem.

## `simply-compiled/`
The pure-Python version of the program, using Cython to compile `koenigsberg_lib` and `util` as-is, with no other changes. Ran the same test in 7.622 seconds, reducing the time required by the previous test by nearly 70%.

## `minimal-cdef/`
First steps toward converting some pure-Python functions to C-style `cdef`- and `cpdef`-defined functions.  Ran the same test in 2.296 seconds, shaving off 70% of the remaining time required for the test.

## `further-cdef/`
Defining data types for additional global and local variables. Ran the same test in 1.847 seconds, shaving off nearly another 20% from the running time. 

## `removing-yields/`
Refactoring to eliminate the code's structural dependence on the Python `yield` statement, which cannot be compiled by Cython because it does not correspond to a C statement. Ran the same test in 1.277 seconds, shaving off nearly another 31% from the running time on the test. The program is now nearly 20x faster than it was at the beginning.



<p>&nbsp;</p>
<footer>This file last updated 15 Aug 2022.</footer>

