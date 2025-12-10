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
