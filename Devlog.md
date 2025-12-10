# SESSION 1 — DEC 9, 11:00 PM
Thoughts

I looked through the project requirements and confirmed that one Python file is enough.
I think starting with block I/O and the header layout makes the most sense.

Plan
Creating a new file called project_3.py
Implement block read/write helpers and the header structure.
Keep everything minimal and clean so later code integrates easily.

# Session 2 - DEC 10, 12:15 AM

Thoughts

It took me almost an hour to implement the whole structure and  read/write helpers.

Now that the header works, the node format must follow the exact 512-byte spec.
It seems straightforward but long due to many fields.

Plan

Implement the Node class with full binary serialization.
Match the exact offsets for keys, values, and children.


# Session 3 - DEC 10, 1:15 AM

Thoughts

With node storage defined, the next step is initializing an empty tree.
I need to support create and the very first insert.

Plan

Write the create command and implement inserting into an empty index.
Ensure header updates correctly when root is created.


# Session 4 - DEC 10, 1:35 AM

Thoughts

A full B-tree insert requires splitting, so complexity increases now.
I feel this is the most difficult and most technical part of the project.
This will be my last commit for tonight, will continue tomorrow now.

Plan

Write split_child and insert_non_full functions.
Handle key shifting, child shifting, and writing updated blocks.

# Session 5 - DEC 10, 3:00 PM

Thoughts

Insertion works in parts, but root splits still need their logic.
This step will complete the core insert implementation.

Plan

Add code for splitting the root and creating a new root node.
Connect everything so insert_non_full can be used normally.