import sys
import struct
import os
import csv

# ==============================
# ====== Global Constants ======
# ==============================

BLOCK_SIZE = 512
MAGIC = b"4348PRJ3"

T = 10                      # minimal degree
MAX_KEY_COUNT = 2 * T - 1   # 19
MAX_CHILD_COUNT = 2 * T     # 20


# ==============================
# ===== File Block Helpers =====
# ==============================

def block_read(fh, blk):
    fh.seek(blk * BLOCK_SIZE)
    data = fh.read(BLOCK_SIZE)
    if len(data) != BLOCK_SIZE:
        raise ValueError(f"Incomplete block read at {blk}")
    return data


def block_write(fh, blk, buf):
    if len(buf) > BLOCK_SIZE:
        raise ValueError("Block overflow")
    fh.seek(blk * BLOCK_SIZE)
    fh.write(buf + b"\x00" * (BLOCK_SIZE - len(buf)))


# ==============================
# ========== Header ============
# ==============================

class Header:
    def __init__(self, root=0, next_id=1):
        self.root = root
        self.next_id = next_id

    def encode(self):
        return struct.pack(">8sQQ", MAGIC, self.root, self.next_id)

    @staticmethod
    def decode(raw):
        magic, r, nxt = struct.unpack(">8sQQ", raw[:24])
        if magic != MAGIC:
            raise ValueError("Invalid header magic")
        return Header(r, nxt)


# ==============================
# ============ Node ============
# ==============================

class Node:
    def __init__(self, blk, parent=0):
        self.id = blk
        self.parent = parent
        self.count = 0
        self.keys = [0] * MAX_KEY_COUNT
        self.vals = [0] * MAX_KEY_COUNT
        self.children = [0] * MAX_CHILD_COUNT

    def leaf(self):
        return self.children[0] == 0

    def encode(self):
        out = struct.pack(">QQQ", self.id, self.parent, self.count)
        out += struct.pack(f">{MAX_KEY_COUNT}Q", *self.keys)
        out += struct.pack(f">{MAX_KEY_COUNT}Q", *self.vals)
        out += struct.pack(f">{MAX_CHILD_COUNT}Q", *self.children)
        return out

    @staticmethod
    def decode(raw):
        blk, parent, ct = struct.unpack(">QQQ", raw[:24])
        n = Node(blk, parent)
        n.count = ct
        offset = 24
        n.keys = list(struct.unpack(f">{MAX_KEY_COUNT}Q", raw[offset: offset + MAX_KEY_COUNT * 8]))
        offset += MAX_KEY_COUNT * 8
        n.vals = list(struct.unpack(f">{MAX_KEY_COUNT}Q", raw[offset: offset + MAX_KEY_COUNT * 8]))
        offset += MAX_KEY_COUNT * 8
        n.children = list(struct.unpack(f">{MAX_CHILD_COUNT}Q", raw[offset: offset + MAX_CHILD_COUNT * 8]))
        return n


# ==============================
# ======= Tree Operations ======
# ==============================

# ---- Load or create root ----
def new_root_node(header, fh, key, val):
    root_id = header.next_id
    header.next_id += 1
    node = Node(root_id)
    node.count = 1
    node.keys[0] = key
    node.vals[0] = val
    header.root = root_id
    block_write(fh, root_id, node.encode())
    block_write(fh, 0, header.encode())


# ---- Insert operations ----

def split(fh, header, parent, idx, child):
    median = T - 1

    right_id = header.next_id
    header.next_id += 1
    right = Node(right_id, parent.id)

    # move upper half keys/vals
    right.count = T - 1
    for j in range(T - 1):
        right.keys[j] = child.keys[j + T]
        right.vals[j] = child.vals[j + T]
        child.keys[j + T] = 0
        child.vals[j + T] = 0

    # move children (if not leaf)
    if not child.leaf():
        for j in range(T):
            right.children[j] = child.children[j + T]
            child.children[j + T] = 0

    child.count = T - 1

    # shift parent children
    for j in range(parent.count, idx, -1):
        parent.children[j + 1] = parent.children[j]
    parent.children[idx + 1] = right_id

    # shift parent keys
    for j in range(parent.count, idx, -1):
        parent.keys[j] = parent.keys[j - 1]
        parent.vals[j] = parent.vals[j - 1]

    # move median up
    parent.keys[idx] = child.keys[median]
    parent.vals[idx] = child.vals[median]
    child.keys[median] = 0
    child.vals[median] = 0
    parent.count += 1

    # write changes
    block_write(fh, 0, header.encode())
    block_write(fh, child.id, child.encode())
    block_write(fh, right.id, right.encode())
    block_write(fh, parent.id, parent.encode())


def insert_nonfull(fh, header, node, k, v):
    i = node.count - 1

    if node.leaf():
        while i >= 0 and k < node.keys[i]:
            node.keys[i + 1] = node.keys[i]
            node.vals[i + 1] = node.vals[i]
            i -= 1
        node.keys[i + 1] = k
        node.vals[i + 1] = v
        node.count += 1
        block_write(fh, node.id, node.encode())
        return

    while i >= 0 and k < node.keys[i]:
        i -= 1
    i += 1

    child_id = node.children[i]
    child = Node.decode(block_read(fh, child_id))

    if child.count == MAX_KEY_COUNT:
        split(fh, header, node, i, child)
        if k > node.keys[i]:
            i += 1
        child = Node.decode(block_read(fh, node.children[i]))

    insert_nonfull(fh, header, child, k, v)


# ---- Search ----

def search_file(filename, k):
    if not os.path.exists(filename):
        print("Error: File not found.")
        return

    with open(filename, "rb") as fh:
        try:
            header = Header.decode(block_read(fh, 0))
        except:
            print("Error: Invalid index file.")
            return

        if header.root == 0:
            print("Error: Key not found.")
            return

        cur = header.root
        while True:
            node = Node.decode(block_read(fh, cur))
            i = 0
            while i < node.count and k > node.keys[i]:
                i += 1

            if i < node.count and k == node.keys[i]:
                print(f"{node.keys[i]}: {node.vals[i]}")
                return

            if node.leaf():
                print("Error: Key not found.")
                return

            cur = node.children[i]


# ---- Traversal ----

def traverse(fh, blk, out_list=None):
    if blk == 0:
        return
    n = Node.decode(block_read(fh, blk))
    keys = n.keys[:n.count]
    vals = n.vals[:n.count]
    kids = n.children[:n.count + 1]
    lf = n.leaf()

    for i in range(len(keys)):
        if not lf:
            traverse(fh, kids[i], out_list)
        if out_list is None:
            print(f"{keys[i]}: {vals[i]}")
        else:
            out_list.append((keys[i], vals[i]))

    if not lf:
        traverse(fh, kids[len(keys)], out_list)


# ==============================
# ======= Commands =============
# ==============================

def cmd_create(path):
    if os.path.exists(path):
        print(f"Error: File {path} already exists.")
        return
    with open(path, "wb") as fh:
        hdr = Header()
        block_write(fh, 0, hdr.encode())


def cmd_insert(path, k, v):
    if not os.path.exists(path):
        print("Error: File does not exist.")
        return

    with open(path, "r+b") as fh:
        try:
            header = Header.decode(block_read(fh, 0))
        except:
            print("Error: Invalid index file.")
            return

        # empty tree
        if header.root == 0:
            new_root_node(header, fh, k, v)
            return

        root = Node.decode(block_read(fh, header.root))

        if root.count == MAX_KEY_COUNT:
            new_root_id = header.next_id
            header.next_id += 1

            nr = Node(new_root_id)
            nr.children[0] = root.id
            root.parent = new_root_id
            header.root = new_root_id

            block_write(fh, 0, header.encode())
            block_write(fh, new_root_id, nr.encode())
            block_write(fh, root.id, root.encode())

            split(fh, header, nr, 0, root)
            insert_nonfull(fh, header, nr, k, v)
        else:
            insert_nonfull(fh, header, root, k, v)


def cmd_print(path):
    if not os.path.exists(path):
        print("Error: File not found.")
        return

    with open(path, "rb") as fh:
        try:
            header = Header.decode(block_read(fh, 0))
        except:
            print("Error: Invalid index file.")
            return

        if header.root != 0:
            traverse(fh, header.root, None)


def cmd_extract(path, out_csv):
    if not os.path.exists(path):
        print("Error: File not found.")
        return
    if os.path.exists(out_csv):
        print(f"Error: File {out_csv} already exists.")
        return

    out = []
    with open(path, "rb") as fh:
        header = Header.decode(block_read(fh, 0))
        if header.root != 0:
            traverse(fh, header.root, out)

    with open(out_csv, "w", newline="") as c:
        w = csv.writer(c)
        for k, v in out:
            w.writerow([k, v])


def cmd_load(path, csvfile):
    if not os.path.exists(path):
        print("Error: File not found.")
        return
    if not os.path.exists(csvfile):
        print("Error: CSV file not found.")
        return

    pairs = []
    with open(csvfile) as f:
        for row in csv.reader(f):
            if row:
                pairs.append((int(row[0]), int(row[1])))

    with open(path, "r+b") as fh:
        header = Header.decode(block_read(fh, 0))

        for k, v in pairs:
            if header.root == 0:
                new_root_node(header, fh, k, v)
                header = Header.decode(block_read(fh, 0))
            else:
                root = Node.decode(block_read(fh, header.root))
                if root.count == MAX_KEY_COUNT:
                    new_root_id = header.next_id
                    header.next_id += 1
                    nr = Node(new_root_id)
                    nr.children[0] = root.id
                    root.parent = new_root_id
                    header.root = new_root_id
                    block_write(fh, 0, header.encode())
                    block_write(fh, new_root_id, nr.encode())
                    block_write(fh, root.id, root.encode())
                    split(fh, header, nr, 0, root)
                    insert_nonfull(fh, header, nr, k, v)
                else:
                    insert_nonfull(fh, header, root, k, v)

            # refresh header in case root changed
            header = Header.decode(block_read(fh, 0))


def cmd_search(path, k):
    search_file(path, k)


# ==============================
# ============ Main ============
# ==============================

def main():
    if len(sys.argv) < 2:
        print("Usage: project3 <command> ...")
        return

    cmd = sys.argv[1]

    if cmd == "create":
        if len(sys.argv) != 3:
            print("Usage: project3 create <index>")
            return
        cmd_create(sys.argv[2])

    elif cmd == "insert":
        if len(sys.argv) != 5:
            print("Usage: project3 insert <file> <key> <value>")
            return
        cmd_insert(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))

    elif cmd == "search":
        if len(sys.argv) != 4:
            print("Usage: project3 search <file> <key>")
            return
        cmd_search(sys.argv[2], int(sys.argv[3]))

    elif cmd == "print":
        if len(sys.argv) != 3:
            print("Usage: project3 print <file>")
            return
        cmd_print(sys.argv[2])

    elif cmd == "extract":
        if len(sys.argv) != 4:
            print("Usage: project3 extract <file> <csv>")
            return
        cmd_extract(sys.argv[2], sys.argv[3])

    elif cmd == "load":
        if len(sys.argv) != 4:
            print("Usage: project3 load <file> <csv>")
            return
        cmd_load(sys.argv[2], sys.argv[3])

    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()
