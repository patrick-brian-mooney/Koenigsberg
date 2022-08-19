#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

"""A program to create map files that can be used with Koenigsberg.

This program was written by Patrick Mooney. It is copyright 2022. It is
released under the GNU GPL, either version 3 or (at your option) any later
version. See the file LICENSE.md for details.
"""


import collections
import json
import shutil
import sys
import textwrap

from pathlib import Path
from typing import Dict, Iterable, Mapping


def terminal_width(default: int = 80) -> None:
    """Do the best job possible of figuring out the width of the current terminal.
    Fall back on a default width if it cannot be determined.
    """
    try:
        width = shutil.get_terminal_size()[0]
    except BaseException:
        width = default
    if width == -1:
        width = default
    return width


def _get_wrapped_lines(paragraph: str, 
                       indent_width: int = 0,
                       enclosing_width = -1) -> None:
    """Function that splits the paragraph into lines. Mostly just wraps textwrap.wrap().

    Note: Strips leading and trailing spaces.
    """
    if enclosing_width == -1:
        enclosing_width = terminal_width()
    ret = textwrap.wrap(paragraph, width=enclosing_width - 2*indent_width, replace_whitespace=False, expand_tabs=False, drop_whitespace=False)
    return [ l.rstrip() for l in ret ]


def print_wrapped_lines(paragraph: str, 
                        indent_width: int = 0, 
                        enclosing_width = -1) -> None:
    """Convenience wrapper for that prints the result of _get_wrapped_lines() to
    stdout.
    """
    for l in _get_wrapped_lines(paragraph, indent_width, enclosing_width):
        print(l)                        
    

def menu_choice(choice_menu: Mapping,
                prompt: str) -> str:
    """Takes a menu description, passed in as CHOICE_MENU, and asks the user to
    choose between the options. It then passes back the user's choice to the caller.

    CHOICE_MENU is a mapping from a list of options to be typed (short strings, each
    of which is ideally a single letter) to a full description of what that option
    means (a longer string). If the mapping preserves order (e.g., OrderedDict, or
    any dictionary in Python 3.6+), it will be presented in the intended order. For
    example:

        OrderedDict([
                        ('a', 'always capitalize'),
                        ('y', 'yes'),
                        ('n', 'never')
                    ])

    As a special case, if both parts of an entry in the CHOICE_MENU are two hyphens,
    that entry is not a valid menu choice; it is printed as-is, as a visual
    separator, but is not a choosable option.

    PROMPT is the string printed as a direct request for input; printed after all of
    the menu options have been displayed.

    Returns a string, the response the user typed that was validated as an allowed
    choice.
    """
    max_menu_item_width = max(len(x) for x in choice_menu)
    menu_column_width = max_menu_item_width + len("  [ ") + len(" ]")
    spacing_column_width = 3
    options_column_width = terminal_width() - (menu_column_width + spacing_column_width + 1)

    # OK, let's print this menu.
    print()
    for option, text in choice_menu.items():
        if (option == '--') and (text == '--'):
            current_line = '  --  ' + ' ' * (max_menu_item_width - len('--')) + ' ' * spacing_column_width + '-----'
        else:
            current_line = '[ %s ]%s%s' % (option, ' ' * (max_menu_item_width - len(option)), ' ' * spacing_column_width)
            text_lines = _get_wrapped_lines(text, enclosing_width=options_column_width)
            if len(text_lines) == 1:
                current_line = current_line + text_lines[0]
            else:
                current_line = current_line + text_lines.pop(0)     # Finish the line with the first line of the description
                left_padding = '\n' + (' ' * (menu_column_width + spacing_column_width))
                current_line = current_line + left_padding + left_padding.join(text_lines)     # Add in the rest of the lines
        print(current_line)
    print()

    # Now, get the user's choice
    choice = 'not a legal option'
    legal_options = [ k.lower() for k, v in choice_menu.items() if ((k != '--') or (v != '--')) ]
    tried_yet = False
    while choice.lower() not in legal_options:
        if tried_yet:           # If the user has got it wrong at least once...
            prompt = prompt.strip() + " [ %s ] " % ('/'.join(legal_options))
        choice = input(prompt.strip() + " ").strip()
        tried_yet = True
    return choice


def yes_or_no(prompt: str) -> bool:
    """Convenience function: asks the user to respond to PROMPT with 'yes' or 'no'
    chosen from a menu. If the user chooses YES, returns True; if NO, returns False.
    """
    return menu_choice({'y': 'Yes', 'n': 'No'}, prompt) == 'y'


def get_map() -> Dict[str, Dict[str, Iterable[str]]]:
    return dict()                                               #FIXME!


def get_graph() -> Dict[str, Iterable[str]]:
    """Repeatedly prompt the user for the information needed to consult a graph-type
    map to be used with Koenigsberg, then return it to the calling function.
    """
    done, ret = False, collections.defaultdict(list)                                               
    while not done:
        node_name = input("What is the name of this node? ").strip()
        if not node_name: continue
        connections_entered = False
        while not connections_entered:
            print("Enter the names of other nodes that this node is connected to, separated by semicolons:")
            connections = input("  ")
            if not connections: continue
            cons_list = sorted(set([i.strip() for i in connections.split(';')]))
            connections_entered = True
        
        ret[node_name].extend(cons_list)
        if not yes_or_no("Input data for another node and its connections?"):
            done = True
            print('\n\n')
    
    # now make sure that every x -> y connection has a corresponding y -> x connection
    massaged = collections.defaultdict(list)
    for node in ret:
        for conn in ret[node]:
            if conn not in massaged[node]:
                massaged[node].append(conn)
            if node not in massaged[conn]:
                massaged[conn].append(node)

    return dict(massaged)
    

def do_choose_for_me() -> str:
    if not yes_or_no("Is your map made of nodes connected by pathsways?"):
        raise SystemExit("Sorry! Koenigsberg is not a suitable tool for your problem.")
    print('\n')
    if yes_or_no("Do you need to be able to name the pathways connecting the nodes?"):
        print("Creating .map file ...")
        return 'm'
    print('\n')
    if yes_or_no("In your problem, can the same pair of nodes be connected by more than one path?"):
        print("Creating .map file ...")
        return 'm'
    print('\nCreating .graph file ...')
    return 'm'                       


def do_print_explanation() -> None:
    """Print some explanatory text about the types of files this program can create,
    then return.
    """
    print_wrapped_lines("This wizard can create either of two types of data files used by Koenigsberg: .graph files or .map files. .graph files are "
    "simpler and faster to create: they consist of nodes information about which nodes each node connects to. They do not allow for the paths between "
    " nodes to have names, nor do they allow for a pair of nodes to be connected by more than a single path. This type of structured data is appropriate "
    "for many, but not all, of the problems that Koenisberg can solve. Data in this format is relatively quick to enter from a keyboard because "
    "Koenigsberg can infer some of the needed information about the topological structure of the graph.")
    print()
    print_wrapped_lines(".map files, like .graph files, consist of nodes connected to each other by pathways, but there can be multiple pathways connecting "
    "each pair of nodes, and the pathways between nodes can have names. This data can take longer to enter at a keyboard, because Koenigsberg makes no attempt "
    "to infer information about the topological structure of the graph being described.")
    print()
    print_wrapped_lines("In either case, you will almost certainly find it helpful to sketch out the structure of your map in advance, and to have the sketch "
    "sitting in front of you while you input its structure into this program.")
    print()
    print_wrapped_lines("It is also possible to hand-write either .graph or .map files if that is easier for you to do; see the manual for more information.")
    print('\n')


def get_save_file_name(default_ext: str,
                       file_type_name: str) -> Path:
    """Get a filename to use for the map being output. Use Tkinter if possible,
    otherwise just use Python's input(). Check to make sure it's an appropriate
    filename, then return it.
    """
    if not default_ext.strip().startswith('.'):
        default_ext = '.' + default_ext.strip()
    filename = None

    while not filename:
        try:                                # Use TKinter if possible
            import tkinter
            import tkinter.filedialog
            tkinter.Tk().withdraw()         # No root window
            filename = tkinter.filedialog.asksaveasfilename(title=f"Save {file_type_name} as ...", defaultextension=default_ext)
        except BaseException:                             # If all else fails, ask the user to type it.
            filename = input('Under what name would you like to save the file? ').strip()

        if not filename:
            ans = menu_choice({'y': "Yes", 'n': "No"}, "Really cancel save and discard all data?")
            if ans == "y":
                print("Map creation canceled!\n\n")
                sys.exit(0)
    
    ret = Path(filename)
    if not ret.suffix:
        ret = ret
        print(f"Adding file extension {default_ext} to make filename {ret}.\n")
    return ret


def do_make_map() -> None:
    """Ask the user to choose what kind of data file to create, then create it.
    """
    decided = False
    choices = {
        'm': '.map file',
        'g': '.graph file',
        '--': '--',
        '?': 'provide an explanation of differences, then ask again',
        'p': 'have the program decide for you after asking a series of questions',
    }
    while not decided:
        choice = menu_choice(choices, 'What kind of data file to you want to create?')
        if choice == "?":
            do_print_explanation()
        else:
            decided = True
            if choice == 'p':
                choice = do_choose_for_me()
    
    if choice == 'm':
        default_ext, file_type_name, the_data = '.map', 'map file', get_map()
    else:
        default_ext, file_type_name, the_data = '.graph', 'graph file', get_graph()

    file_name = get_save_file_name(default_ext, file_type_name)
    file_name.write_text(json.dumps(the_data, ensure_ascii=False, indent=2), encoding='utf-8')
        

if __name__ == "__main__":
    if len(sys.argv) > 1:
        raise SystemExit(f"Sorry! {sys.argv[0]} does not take any command-line arguments!")
    
    do_make_map()
