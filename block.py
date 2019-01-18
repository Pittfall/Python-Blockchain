from time import time
from utility.printable import Printable


class Block(Printable):
    def __init__(self, index, previous_hash, transactions, proof, time=time()):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = time
        self.proof = proof

    def to_dict(self):
        block_copy = self.__dict__.copy()
        block_copy['transactions'] = [tx.__dict__ for tx in block_copy['transactions']]
        return block_copy
