import functools
from collections import OrderedDict
import json

import hash_util

MINING_REWARD = 10
genesis_block = {"previous_hash": "",
                 "index": 0, "transactions": [], 'proof': 100}
blockchain = [genesis_block]
open_transactions = []
owner = "Andrew"
participants = {owner}


def load_data():
    with open('blockchain.txt', 'r') as f:
        file_content = f.readlines()
        global blockchain
        global open_transactions
        blockchain = json.loads(file_content[0].strip())
        updated_blockchain = []
        for block in blockchain:
            updated_block = {
                'previous_hash': block['previous_hash'],
                'index': block['index'],
                'proof': block['proof'],
                'transactions': [OrderedDict([
                                    ('sender', tx['sender']),
                                    ('recipient', tx['recipient']),
                                    ('amount', tx['amount'])
                                ]) for tx in block['transactions']]
            }
            updated_blockchain.append(updated_block)
        blockchain = updated_blockchain
        open_transactions = json.loads(file_content[1].strip())
        updated_transactions = []
        for tx in open_transactions:
            updated_transaction = OrderedDict([
                ('sender', tx['sender']),
                ('recipient', tx['recipient']),
                ('amount', tx['amount'])
            ])
            updated_transactions.append(updated_transaction)
        open_transactions = updated_transactions

load_data()


def save_data():
    with open('blockchain.txt', 'w') as f:
        f.write(json.dumps(blockchain))
        f.write("\n")
        f.write(json.dumps(open_transactions))


def valid_proof(transactions, last_hash, proof_number):
    guess = (str(transactions) + str(last_hash) + str(proof_number)).encode()
    guess_hash = hash_util.hash_string_256(guess)
    print(guess_hash)
    return guess_hash[0:2] == "00"


def proof_of_work():
    last_block = blockchain[-1]
    last_hash = hash_util.hash_block(last_block)
    proof = 0
    while not valid_proof(open_transactions, last_hash, proof):
        proof += 1
    return proof


def get_balance(participant):
    tx_sender = [[tx['amount'] for tx in block['transactions']
                  if tx['sender'] == participant] for block in blockchain]
    open_tx_sender = [tx['amount']
                      for tx in open_transactions if tx['sender'] == participant]
    tx_sender.append(open_tx_sender)
    amount_sent = functools.reduce(
        lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

    tx_recipient = [[tx['amount'] for tx in block['transactions']
                     if tx['recipient'] == participant] for block in blockchain]
    amount_received = functools.reduce(
        lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)

    return amount_received - amount_sent


def get_last_blockchain_value():
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def add_transaction(recipient, sender=owner, amount=1.0):
    """ Add a new transaction to the open transactions.

    Arguments:
        :sender: The sender of the coins.
        :recipient: The recipient of the coins.
        :amount: The amount of coins sent with the transaction (default = 1.0).
    """
    transaction = OrderedDict([
        ("sender", sender),
        ("recipient", recipient),
        ("amount", amount)
    ])

    if verify_transaction(transaction):
        open_transactions.append(transaction)
        participants.add(sender)
        participants.add(recipient)
        save_data()
        return True

    return False


def verify_transaction(transaction):
    sender_balance = get_balance(transaction['sender'])
    return sender_balance >= transaction['amount']


def mine_block():
    last_block = blockchain[-1]
    hashed_block = hash_util.hash_block(last_block)
    proof = proof_of_work()
    reward_transaction = OrderedDict([
        ('sender', 'MINING'),
        ('recipient', owner),
        ('amount', MINING_REWARD)
    ])
    copied_transactions = open_transactions[:]
    copied_transactions.append(reward_transaction)
    block = {
        "previous_hash": hashed_block,
        "index": len(blockchain),
        "transactions": copied_transactions,
        'proof': proof
    }
    blockchain.append(block)
    return True


def get_transaction_value():
    tx_recipient = input("Enter the recipient of the transaction: ")
    tx_amount = float(input("Please enter a transaction amount: "))
    return (tx_recipient, tx_amount)


def get_user_choice():
    return input("Your choice: ")


def print_blockchain_elements():
    print("-" * 20)
    for block in blockchain:
        print(block)
    else:
        print("-" * 20)


def verify_chain():
    for (index, block) in enumerate(blockchain):
        if index == 0:
            continue
        if block["previous_hash"] != hash_util.hash_block(blockchain[index - 1]):
            return False
        # Omit the reward transaction which is the last one since we calculate the proof of work before
        # adding the reward transaction.
        if not valid_proof(block['transactions'][:-1], block['previous_hash'], block['proof']):
            print("Proof of work is invalid")
            return False
    return True


def verify_transactions():
    return all([verify_transaction(tx) for tx in open_transactions])


waiting_for_input = True

while waiting_for_input:
    print("Please choose")
    print("1. Add a new transaction value")
    print("2. Mine a new block")
    print("3. Output the blockchain blocks")
    print("4. Output participants")
    print("5. Check transaction validity")
    print("h. Manipulate the chain")
    print("q. Exit")
    user_choice = get_user_choice()

    if user_choice == "1":
        tx_data = get_transaction_value()
        recipient, amount = tx_data
        if add_transaction(recipient=recipient, amount=amount):
            print("Added transaction!!")
        else:
            print("Transaction failed!!")
        print(open_transactions)
    elif user_choice == "2":
        if mine_block():
            open_transactions = []
        save_data()
    elif user_choice == "3":
        print_blockchain_elements()
    elif user_choice == "4":
        print(participants)
    elif user_choice == "5":
        if verify_transactions():
            print("All transactions are valid")
        else:
            print("There are invalid transactions")
    elif user_choice == "h":
        if len(blockchain) >= 1:
            blockchain[0] = {
                "previous_hash": "",
                "index": 0,
                "transactions": [{'sender': 'Hacker', 'recipient': 'me', 'amount': 100}]
            }
    elif user_choice == "q":
        waiting_for_input = False
    else:
        print("Invalid Choice, please try again")

    if not verify_chain():
        print("Invalid blockchain")
        break

    print("-" * 30)
    print('Balance of {}: {:6.2f}'.format("Andrew", get_balance("Andrew")))
    print("-" * 30)
else:
    print("goodbye")
