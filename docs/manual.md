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

![A node map in the shape of a hexagon, where each node is connected to the two nodes adjacent to it on the outside of the hexagon, and the nodes are numbered one through six.](img/hex_ring.png)

Each node in the network above is given a name -- in this case, a number, using the numbers one through six. There are (unnamed) pathways between the numbers; when `koenigsberg` loads the .graph file, it automatically names those pathways: `('1', '2')` is the name given to the pathway that connects node `'1'` with node `'2'`; `('2', '3')` is the name of the pathway connecting node `'2'` to node `'3'`; and so forth. Nodes need not be named using numbers; any textual string can be used to name them. So a .graph file can contain nodes named, for instance, `'Paris'` and `'Rouen'`; in this case, if there is a pathway connecting them, it will be automatically named `('Paris', 'Rouen')`, with the node names in alphabetical order. (It is not possible to override the automatic names given to pathways in a .graph file, nor is it possible in a .graph file for two nodes to be connected by more than a single pathway. Both of these restrictions are lifted in .map files, which support a more complex file format &mdash; also a file format that is more tedious to create.)

Having loaded the map data and named the pathways, Koenigsberg then attempts to find all possible ways to traverse the map, starting from any node, in which each pathway is traversed exactly once. When it finds such a pathway, it prints it out. So the first line in the sample output above means that one way to traverse the map that meets the "pass through each pathway exactly once" constraint is:

* Move down the pathway `('1', '2')`; then
* move down the pathway `('2', '3')`; then
* move down the pathway `('3', '4')`; then
* move down the pathway `('4', '5')`; then
* move down the pathway `('5', '6')`; then
* move down the pathway `('1', '6')`; and every pathway has been traversed.

There are of course eleven other possible solutions to this map meeting the given constraint; they are also printed.


### Another example

Imagine a pentagon in which each vertex is a node in a graph and each node is connected to every other node by a pathway:

![A node map in the shape of a pentagon, where each node is connected to the every other node, and the nodes are numbered one through five.](img/pentagon.png)

How many possible paths are there through this network that pass through each connecting pathway exactly once? Let's find out:

    koenigsberg.py --graph sample_data/pentagon.graph

Koenigsberg prints out every valid answer; the answer list ends with

        [...]
    
    ('4', '5') -> ('3', '4') -> ('3', '5') -> ('2', '5') -> ('1', '2') -> ('1', '4') -> ('2', '4') -> ('2', '3') -> ('1', '3') -> ('1', '5')
    ('4', '5') -> ('3', '4') -> ('3', '5') -> ('2', '5') -> ('2', '3') -> ('1', '3') -> ('1', '2') -> ('2', '4') -> ('1', '4') -> ('1', '5')
    ('4', '5') -> ('3', '4') -> ('3', '5') -> ('2', '5') -> ('2', '3') -> ('1', '3') -> ('1', '4') -> ('2', '4') -> ('1', '2') -> ('1', '5')
    ('4', '5') -> ('3', '4') -> ('3', '5') -> ('2', '5') -> ('2', '4') -> ('1', '4') -> ('1', '2') -> ('2', '3') -> ('1', '3') -> ('1', '5')
    ('4', '5') -> ('3', '4') -> ('3', '5') -> ('2', '5') -> ('2', '4') -> ('1', '4') -> ('1', '3') -> ('2', '3') -> ('1', '2') -> ('1', '5')
    All paths examined!
        2640 solutions found!

and there's the answer: there are 2640 valid pathways through the network that traverse each connection exactly once.

### The original Königsberg bridges problem

The basic structure of the Königsberg bridges problem looks like this:

![A node map of the Königsberg bridges problem. Area A is connected to Area B by bridges a and b, to Area C by bridges c and d, and to Area D by bridge e; Area B is also connected to Area D by bridge f; Area C is also connected to Area D by bridge g.](img/Königsberg.png)

Note that some pairs of nodes in this network are connected by multiple bridges, which is why the data is represented by a .map, rather than a .graph, file; .map files have additional information that allows for multiple paths to exist connecting any pair of nodes (and for paths to be named).

To brute-force this graph, try:

    koenigsberg.py --map sample_data/Königsberg.map 
    
(If your keyboard does not have an **ö** key, you may find it helpful to use your terminal's tab-completion feature, or to cut and paste the file name or the letter.) Note that the command-line interface requires the use of the `--map` switch, instead of the `--graph` switch, to load a map file. (Conversely, the `--map` switch will only load .map, not .graph, files.)

This produces:

    All paths examined!
        No solutions found!

This matches up with Euler's 1735 proof, which he performed deductively rather than by brute-forcing the problem. (But he didn't have a computer, either.)


## Creating .map and .graph files

The easiest way to create a .map or a .graph file to use the (included) `map_wizard` program, which will prompt the user for information repeatedly until the entire map (or graph) is created, then write the relevant data out to disk in a file of the appropriate format.

To get started, type:

    map_wizard.py
    
and answer the questions.

### Creating .graph files by hand (or programmatically)

A .graph file is just a JSON file that encodes a Python dictionary following these rules:

1. Each key is a node name.
2. The value that each key indexes is a list of node names indicating which nodes the node mentioned in the key is connected to.

Here is a sample:

    {
      "1": [
        "2",
        "4"
      ],
      "2": [
        "1",
        "3"
      ],
      "3": [
        "2",
        "4"
      ],
      "4": [
        "1",
        "3"
      ]
    }

This file describes a network with four nodes: `'1'`, `'2'`, `'3'`, and `'4'`. Node 1 is connected to nodes 2 and 4 (but not to node 3); node 2 is connected to nodes 1 and 3 (but not to node 4); node 3 is connected to nodes 2 and 4 (but not to node 1), and node 4 is connected to nodes 1 and 3 (but not to node 2).

Any valid JSON file that encodes such a dictionary is a valid .map file for Koenigsberg. "Valid" includes not only strictly-valid files under the original, strict version of the JSON standard, but any JSON file that [Python's `json` module](https://docs.python.org/3.9/library/json.html) can read. 


### Creating .map files by hand (or programmatically)

## Saving the progress of an exploration run

## Other command-line options  

## Bugs

There are probably bugs. Please [report them](https://github.com/patrick-brian-mooney/Koenigsberg/issues) at the project's page [on GitHub](https://github.com/patrick-brian-mooney/Koenigsberg).

Questions, offers to collaborate, inquiries about where to send large sums of money, etc., should also be directed through GitHub. 
