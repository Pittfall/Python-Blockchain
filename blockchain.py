import functools
import json
import requests

from utility import hash_util
from utility.verification import Verification

from block import Block
from transaction import Transaction
from wallet import Wallet

MINING_REWARD = 10


class Blockchain:
    def __init__(self, public_key, node_id):
        genesis_block = Block(0, "", [], 100, 0)
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        return self.__open_transactions

    def load_data(self):
        try:
            with open('data/blockchain-{}.txt'.format(self.node_id), 'r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0].strip())
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                                    for tx in block['transactions']]
                    updated_block = Block(block['index'], block['previous_hash'],
                                          converted_tx, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                open_transactions = json.loads(file_content[1].strip())
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2].strip())
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            print("Handled Exception")
        finally:
            print("Cleanup")

    def save_data(self):
        try:
            with open('data/blockchain-{}.txt'.format(self.node_id), 'w') as f:
                saveable_chain = []
                for block in self.__chain:
                    block_current_transactions = [
                        tx.__dict__ for tx in block.transactions]
                    block_current = Block(block.index, block.previous_hash, block_current_transactions,
                                          block.proof, block.timestamp).__dict__
                    saveable_chain.append(block_current)
                f.write(json.dumps(saveable_chain))
                f.write("\n")
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write("\n")
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print("Saving failed!!")

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_util.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        if sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key
        else:
            participant = sender

        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == participant] for block in self.__chain]
        open_tx_sender = [tx.amount
                          for tx in self.__open_transactions if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = functools.reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

        tx_recipient = [[tx.amount for tx in block.transactions
                         if tx.recipient == participant] for block in self.__chain]
        amount_received = functools.reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)

        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """ Add a new transaction to the open transactions.

        Arguments:
            :sender: The sender of the coins.
            :recipient: The recipient of the coins.
            :amount: The amount of coins sent with the transaction (default = 1.0).
        """
        transaction = Transaction(sender, recipient, signature, amount)

        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json={
                            'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self):
        if self.public_key == None:
            return None

        last_block = self.__chain[-1]
        hashed_block = hash_util.hash_block(last_block)
        proof = self.proof_of_work()
        reward_transaction = Transaction(
            "MINING", self.public_key, "", MINING_REWARD)
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block,
                      copied_transactions, proof)

        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.to_dict()
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue

        return block

    def add_block(self, block):
        transactions = [Transaction(
            tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_util.hash_block(
            self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(
            block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions = self.__open_transactions[:]
        for itx in block['transactions']:
            for opentx in stored_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed')
        self.save_data()
        return True

    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'],
                                    [Transaction(tx['sender'], tx['recipient'],
                                                 tx['signature'], tx['amount']) for tx in block['transactions']], block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        return list(self.__peer_nodes)
