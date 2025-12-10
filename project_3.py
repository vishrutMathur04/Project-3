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


