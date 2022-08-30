# Koenigsberg (alpha version)

A graph analysis tool by <a rel="author" href="https://patrickbrianmooney.nfshost.com/~patrick/">Patrick Mooney</a>.The most recent version can be found <a rel="me author" href="https://github.com/patrick-brian-mooney/Koenigsberg">on GitHub</a>.

## Requirements

Koenigsberg requires Python 3.9 or above and Cython (at least version 0.32), and a working C compiler that is set up to work with Cython. 

## Installation

First, be sure that a C compiler is installed in a location and manner that allows Cython to find it. Under Debian, Ubuntu, and related Linuxes, `sudo apt install build-essential` will install everything needed at the system level and allow Cython to be installed with `pip`, as described below. Users of other operating systems should look at the instructions on the [installing Cython](https://cython.readthedocs.io/en/latest/src/quickstart/install.html) webpage.

    git clone patrick-brian-mooney/Koenigsberg
    cd Koenigsberg
    pip install -r requirements.txt

`pip` will then install Cython, a recent version of which is currently the only requirement. (Older versions of Cython may not work; recent versions are required because they fix a problem with correctly determining the length of bytearrays.) If `pip` is not already installed properly on your system, you may need to [install pip](https://pip.pypa.io/en/stable/installation/) first.

Installing Cython manually and separately is not generally necessary, but this may not be true for your particular setup; see [installing Cython](https://cython.readthedocs.io/en/latest/src/quickstart/install.html) for instructions if `pip` does not automatically set up Cython for you.

## Overview

Koenigsberg brute-forces certain problems in graph theory that are analogous to "the Königsberg Bridge Problem," which was solved without brute-forcing it by by Leonard Euler in 1775; see Teo Paoletti's [writeup](
https://www.maa.org/press/periodicals/convergence/leonard-eulers-solution-to-the-konigsberg-bridge-problem) for an overview of this problem and Euler's solution.

"Königsberg problems," as this program calls them, are problems that consist of (a) a map in which nodes are connected by pathways; and (b) the problem is to attempt to find a pathway through the network that traverses each connection exactly once. Königsberg provides a set of tools to help solve these problems by brute force: it is a command-line program that operates on pre-created files describing the connections between nodes and networks, and also a set of Python libraries that allow these pre-defined libraries to be scripted using the Python programming language.

## Quick start

*note:* Windows users may need to adapt the commands in this section by replacing forward slashes (`/`) used as path separators with back slashes (`\`). MacOS users and users of other Unix-based operating systems may need to prefix the program nam `koenigsberg.py` with a dot and a slash (so that it becomes `./koenigsberg.py`) if they are running the program from the current directory. Users of any operating system may find that explicitly specifying the full path to the executable is the easiest way to work around problems in this area. If your system is not detecting properly that `koenigsberg.py` should be run using the Python interpreter, you may need to specify that explicitly on the command line by prefixing the command with the name of and/or full path to the Python interpreter, which may be called `python`, `python3`, `python.exe`, `python3.exe`, or something else on your system. Check your own installation for details.

To start: try

    koenigsberg.py --help
    
to see a list of comand-line options, or 

    koenigsberg.py --version
    
to print out the current version of Koenigsberg (and the version of Python it is running under).

The first time you run `koenigsberg`, it will build its extension modules; please be patient as this may take a minute or two on slower systems.

### First run

To analyze a simple (trivial, even) graph structure provided in a sample data file, try

    koenigsberg.py --graph sample_data/hex_ring.graph

You should see output that looks like this:

    ('1', '2') -> ('2', '3') -> ('3', '4') -> ('4', '5') -> ('5', '6') -> ('1', '6')
    ('1', '6') -> ('5', '6') -> ('4', '5') -> ('3', '4') -> ('2', '3') -> ('1', '2')
    ('1', '2') -> ('1', '6') -> ('5', '6') -> ('4', '5') -> ('3', '4') -> ('2', '3')
    ('2', '3') -> ('3', '4') -> ('4', '5') -> ('5', '6') -> ('1', '6') -> ('1', '2')
    ('2', '3') -> ('1', '2') -> ('1', '6') -> ('5', '6') -> ('4', '5') -> ('3', '4')
    ('3', '4') -> ('4', '5') -> ('5', '6') -> ('1', '6') -> ('1', '2') -> ('2', '3')
    ('3', '4') -> ('2', '3') -> ('1', '2') -> ('1', '6') -> ('5', '6') -> ('4', '5')
    ('4', '5') -> ('5', '6') -> ('1', '6') -> ('1', '2') -> ('2', '3') -> ('3', '4')
    ('4', '5') -> ('3', '4') -> ('2', '3') -> ('1', '2') -> ('1', '6') -> ('5', '6')
    ('5', '6') -> ('1', '6') -> ('1', '2') -> ('2', '3') -> ('3', '4') -> ('4', '5')
    ('1', '6') -> ('1', '2') -> ('2', '3') -> ('3', '4') -> ('4', '5') -> ('5', '6')
    ('5', '6') -> ('4', '5') -> ('3', '4') -> ('2', '3') -> ('1', '2') -> ('1', '6')

Koenigsberg is examining the graph in the `hex_ring.graph` file and seeking all paths through it that cross each pathway between nodes exactly once, and printing the list of pathways that so ao.

The graph in that file looks like this:

![A node map in the shape of a hexagon, where each node is connected to the two nodes adjacent to it on the outside of the hexagon, and the nodes are numbered one through six.](img/hex_ring.png "Optional title")

Each node in the network above is given a name -- in this case, a number, using the numbers one through six. There are (unnamed) pathways between the numbers; when `koenigsberg` loads the .graph file, it automatically names those pathways: `('1', '2')` is the name given to the pathway that connects node `'1'` with node `'2'`; `('2', '3')` is the name of the pathway connecting node `'2'` to node `'3'`; and so forth. Nodes need not be named using numbers; any textual string can be used to name them. So a .graph file can contain nodes named, for instance, `'Berlin'` and `'Munich'`; in this case, if there is a pathway connecting them, it will be automatically named `('Berlin', 'Munich')`, with the node names in alphabetical order. (It is not possible to override the automatic names given to pathways in a .graph file, nor is it possible in a .graph file for two nodes to be connected by more than a single pathway. Both of these restrictions are lifted in .map files, which support a more complex file format &mdash; also a file format that is more tedious to create.)

Having loaded the map data and named the pathways, Koenigsberg then attempts to find all possible ways to traverse the map, starting from any node, in which each pathway is traversed exactly once. When it finds such a pathway, it prints it out. So the first line in the sample output above means that one way to traverse the map that meets the "pass through each pathway exactly once" constraint is:

* Move down the pathway `('1', '2')`; then
* Move down the pathway `('2', '3')`; then
* Move down the pathway `('3', '4')`; then
* Move down the pathway `('4', '5')`; then
* Move down the pathway `('6', '1')`; and every pathway has been traversed.
