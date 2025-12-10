import sys, struct, os, csv

BLOCK_SIZE = 512
MAGIC_NUMBER = b'4348PRJ3'

def read_bytes(f, block_id):
    f.seek(block_id * BLOCK_SIZE)
    data = f.read(BLOCK_SIZE)
    if len(data) < BLOCK_SIZE:
        raise ValueError("Block read incomplete")
    return data

def write_bytes(f, block_id, data):
    if len(data) > BLOCK_SIZE:
        raise ValueError("Too large block write")
    f.seek(block_id * BLOCK_SIZE)
    f.write(data + b'\x00' * (BLOCK_SIZE - len(data)))

class Header:
    def __init__(self, root_id=0, next_block_id=1):
        self.root_id = root_id
        self.next_block_id = next_block_id

    def to_bytes(self):
        return struct.pack(">8sQQ", MAGIC_NUMBER, self.root_id, self.next_block_id)

    @classmethod
    def from_bytes(cls, data):
        magic, r, n = struct.unpack(">8sQQ", data[:24])
        if magic != MAGIC_NUMBER:
            raise ValueError("Invalid magic")
        return cls(r, n)



DEGREE = 10
MAX_KEYS = 19
MAX_CHILDREN = 20

class Node:
    def __init__(self, block_id, parent_id=0):
        self.block_id = block_id
        self.parent_id = parent_id
        self.num_keys = 0
        self.keys = [0]*MAX_KEYS
        self.values = [0]*MAX_KEYS
        self.children = [0]*MAX_CHILDREN

    def is_leaf(self):
        return self.children[0] == 0

    def to_bytes(self):
        buf = struct.pack(">QQQ", self.block_id, self.parent_id, self.num_keys)
        buf += struct.pack(f">{MAX_KEYS}Q", *self.keys)
        buf += struct.pack(f">{MAX_KEYS}Q", *self.values)
        buf += struct.pack(f">{MAX_CHILDREN}Q", *self.children)
        return buf

    @classmethod
    def from_bytes(cls, data):
        bid, pid, nk = struct.unpack(">QQQ", data[:24])
        node = cls(bid, pid)
        node.num_keys = nk
        off = 24
        node.keys = list(struct.unpack(f">{MAX_KEYS}Q", data[off:off+MAX_KEYS*8]))
        off += MAX_KEYS*8
        node.values = list(struct.unpack(f">{MAX_KEYS}Q", data[off:off+MAX_KEYS*8]))
        off += MAX_KEYS*8
        node.children = list(struct.unpack(f">{MAX_CHILDREN}Q", data[off:off+MAX_CHILDREN*8]))
        return node

    # (previous code unchanged above)

    def cmd_create(filename):
        if os.path.exists(filename):
            print("Error: File exists.")
            sys.exit(1)
        with open(filename, "wb") as f:
            h = Header()
            write_bytes(f, 0, h.to_bytes())

    def cmd_insert(filename, key, value):
        if not os.path.exists(filename):
            print("Error: File missing.")
            sys.exit(1)

        with open(filename, "r+b") as f:
            h = Header.from_bytes(read_bytes(f, 0))

            # empty tree
            if h.root_id == 0:
                rid = h.next_block_id
                root = Node(rid)
                root.num_keys = 1
                root.keys[0] = key
                root.values[0] = value
                h.root_id = rid
                h.next_block_id += 1
                write_bytes(f, rid, root.to_bytes())
                write_bytes(f, 0, h.to_bytes())
                return

    

    def split_child(f, header, parent, i, child):
        z_id = header.next_block_id
        header.next_block_id += 1
        z = Node(z_id, parent.block_id)

        median = DEGREE - 1  # index 9

        # move keys
        z.num_keys = DEGREE - 1
        for j in range(DEGREE-1):
            z.keys[j] = child.keys[j+DEGREE]
            z.values[j] = child.values[j+DEGREE]
            child.keys[j+DEGREE] = 0
            child.values[j+DEGREE] = 0

        # move children
        if not child.is_leaf():
            for j in range(DEGREE):
                z.children[j] = child.children[j+DEGREE]
                child.children[j+DEGREE] = 0

        child.num_keys = DEGREE - 1

        # shift parent children
        for j in range(parent.num_keys, i, -1):
            parent.children[j+1] = parent.children[j]
        parent.children[i+1] = z_id

        # shift parent keys
        for j in range(parent.num_keys, i, -1):
            parent.keys[j] = parent.keys[j-1]
            parent.values[j] = parent.values[j-1]

        parent.keys[i] = child.keys[median]
        parent.values[i] = child.values[median]
        parent.num_keys += 1

        child.keys[median] = 0
        child.values[median] = 0

        write_bytes(f, 0, header.to_bytes())
        write_bytes(f, child.block_id, child.to_bytes())
        write_bytes(f, z.block_id, z.to_bytes())
        write_bytes(f, parent.block_id, parent.to_bytes())

    def insert_non_full(f, header, node, key, value):
        i = node.num_keys - 1

        if node.is_leaf():
            while i >= 0 and key < node.keys[i]:
                node.keys[i+1] = node.keys[i]
                node.values[i+1] = node.values[i]
                i -= 1
            node.keys[i+1] = key
            node.values[i+1] = value
            node.num_keys += 1
            write_bytes(f, node.block_id, node.to_bytes())
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            cid = node.children[i]
            child = Node.from_bytes(read_bytes(f, cid))

            if child.num_keys == MAX_KEYS:
                split_child(f, header, node, i, child)
                if key > node.keys[i]:
                    i += 1
                cid = node.children[i]
                child = Node.from_bytes(read_bytes(f, cid))

            insert_non_full(f, header, child, key, value)

            

    def cmd_insert(filename, key, value):
        if not os.path.exists(filename):
            print("Error: File missing.")
            sys.exit(1)

        with open(filename, "r+b") as f:
            header = Header.from_bytes(read_bytes(f, 0))

            if header.root_id == 0:
                rid = header.next_block_id
                header.next_block_id += 1
                root = Node(rid)
                root.num_keys = 1
                root.keys[0] = key
                root.values[0] = value
                header.root_id = rid
                write_bytes(f, rid, root.to_bytes())
                write_bytes(f, 0, header.to_bytes())
                return

            root = Node.from_bytes(read_bytes(f, header.root_id))

            if root.num_keys == MAX_KEYS:
                new_root_id = header.next_block_id
                header.next_block_id += 1
                new_root = Node(new_root_id)
                new_root.children[0] = root.block_id
                root.parent_id = new_root_id
                header.root_id = new_root_id

                write_bytes(f, 0, header.to_bytes())
                write_bytes(f, new_root_id, new_root.to_bytes())

                split_child(f, header, new_root, 0, root)
                insert_non_full(f, header, new_root, key, value)
            else:
                insert_non_full(f, header, root, key, value)
                def cmd_search(filename, key):
    if not os.path.exists(filename):
        print("Error: File not found.")
        sys.exit(1)

    with open(filename, "rb") as f:
        h = Header.from_bytes(read_bytes(f, 0))
        if h.root_id == 0:
            print("Error: Key not found.")
            return

        cid = h.root_id
        while True:
            node = Node.from_bytes(read_bytes(f, cid))
            i = 0
            while i < node.num_keys and key > node.keys[i]:
                i += 1
            if i < node.num_keys and node.keys[i] == key:
                print(f"{node.keys[i]}: {node.values[i]}")
                return
            if node.is_leaf():
                print("Error: Key not found.")
                return
            cid = node.children[i]

    def traversal_helper(f, block_id, out=None):
        if block_id == 0:
            return
        node = Node.from_bytes(read_bytes(f, block_id))

        keys = node.keys[:node.num_keys]
        values = node.values[:node.num_keys]
        children = node.children[:node.num_keys+1]
        leaf = node.is_leaf()

        for i in range(len(keys)):
            if not leaf:
                traversal_helper(f, children[i], out)
            if out is None:
                print(f"{keys[i]}: {values[i]}")
            else:
                out.append((keys[i], values[i]))
        if not leaf:
            traversal_helper(f, children[len(keys)], out)





