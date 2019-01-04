genesis_block = {"previous_hash": "", "index": 0, "transactions": []}
blockchain = [genesis_block]
open_transactions = []
owner = "Andrew"
participants = {owner}


def hash_block(block):
    return "-".join([str(block[key]) for key in block])


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
    transaction = {"sender": sender, "recipient": recipient, "amount": amount}
    open_transactions.append(transaction)
    participants.add(sender)
    participants.add(recipient)


def mine_block():
    last_block = blockchain[-1]
    block_hash = hash_block(last_block)
    block = {
        "previous_hash": block_hash,
        "index": len(blockchain),
        "transactions": open_transactions,
    }
    blockchain.append(block)


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
        if block["previous_hash"] != hash_block(blockchain[index - 1]):
            return False
    return True


waiting_for_input = True

while waiting_for_input:
    print("Please choose")
    print("1. Add a new transaction value")
    print("2. Mine a new block")
    print("3. Output the blockchain blocks")
    print("4. Output participants")
    print("5. Manipulate the chain")
    print("6. Exit")
    user_choice = get_user_choice()

    if user_choice == "1":
        tx_data = get_transaction_value()
        recipient, amount = tx_data
        add_transaction(recipient=recipient, amount=amount)
        print(open_transactions)
    elif user_choice == "2":
        mine_block()
    elif user_choice == "3":
        print_blockchain_elements()
    elif user_choice == '4':
        print(participants)
    elif user_choice == "5":
        if len(blockchain) >= 1:
            blockchain[0] = {
                "previous_hash": "", 
                "index": 0,
                "transactions": [{'sender': 'Hacker', 'recipient': 'me', 'amount': 100}]
            }
    elif user_choice == "6":
        waiting_for_input = False
    else:
        print("Invalid Choice, please try again")

    if not verify_chain():
        print("Invalid blockchain")
        break

    print("-" * 30)
else:
    print("goodbye")
