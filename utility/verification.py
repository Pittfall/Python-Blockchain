import utility.hash_util as hash_util
from wallet import Wallet

class Verification:
    @staticmethod
    def valid_proof(transactions, last_hash, proof_number):
        guess = (str([tx.to_ordered_dict() for tx in transactions])
                + str(last_hash)
                + str(proof_number)).encode()
        guess_hash = hash_util.hash_string_256(guess)
        print(guess_hash)
        return guess_hash[0:2] == "00"

    @classmethod
    def verify_chain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_util.hash_block(blockchain[index - 1]):
                return False
            # Omit the reward transaction which is the last one since we calculate the proof of work before
            # adding the reward transaction.
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("Proof of work is invalid")
                return False
        return True

    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)

        return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])
