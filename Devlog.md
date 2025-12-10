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
