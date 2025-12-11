CS 4348 – Project 3
B-Tree Index File Manager
Fall 2025

Overview

This program implements a disk-based B-Tree index file using fixed-size 512-byte blocks as required by the project description. The B-Tree uses minimal degree 10 (so each node holds up to 19 keys and 20 children). The application is a command-line tool that allows creating index files, inserting key/value pairs, searching for keys, printing all pairs in sorted order, extracting the tree to a CSV file, and loading entries from a CSV file.

All integers are stored in the file in 8-byte big-endian format, and the program never loads more than three nodes at a time, following the memory-restriction rule.

Everything is implemented in a single Python file named project3.py.

Files Included

project3.py
This is the main (and only) source file. It contains:

Block I/O helpers for reading/writing 512-byte blocks

Header structure handling (magic number, root id, next free block id)

Node structure for B-Tree nodes

All B-Tree logic (searching, splitting, inserting, printing, extracting)

The command-line interface and argument parsing

CSV load and extract functions

devlog.txt
My development log documenting each session I worked on this project.

How to Run

You can run the project using Python 3.
All commands follow this format:

python3 project3.py <command> [arguments]

Commands
create

Creates a new index file.

python3 project3.py create test.idx

insert

Inserts a single key/value pair.

python3 project3.py insert test.idx 15 100

search

Searches for a key in the tree.

python3 project3.py search test.idx 15

print

Prints all key/value pairs in sorted order.

python3 project3.py print test.idx

extract

Exports the entire B-Tree to a CSV.

python3 project3.py extract test.idx output.csv

load

Loads key/value pairs from a CSV file, inserting them one at a time.

python3 project3.py load test.idx input.csv

Notes

The B-Tree is implemented exactly as described in the project instructions.

All block operations are strictly 512 bytes, and unused portions are zero-padded.

The "3 nodes in memory" rule is followed by never storing more than the active parent, child, and optionally split node at one time.

The code uses only Python's built-in libraries struct, csv, os, sys.

The devlog contains all work sessions, commits and reflections.
