blockchain = []


def get_last_blockchain_value():
    if len(blockchain) < 1:
        return None
    return blockchain[-1]


def add_transaction(transaction_amount, last_transaction):
    if last_transaction == None:
        last_transaction = [1.0]
    blockchain.append([last_transaction, transaction_amount])


def get_transaction_value():
    return float(input("Please enter a transaction amount: "))


def get_user_choice():
    return input("Your choice: ")


def print_blockchain_elements():
    print('-' * 20)
    for block in blockchain:
        print(block)
    else:
        print('-' * 20)


def verify_chain():
    block_index = 0
    for block_index in range(len(blockchain)):
        if block_index == 0:
            continue
        if blockchain[block_index][0] != blockchain[block_index - 1]:
            return False
    return True

waiting_for_input = True

while waiting_for_input:
    print("Please choose")
    print("1. Add a new transaction value")
    print("2. Output the blockchain blocks")
    print("3. Manipulate the chain")
    print("4. Exit")
    user_choice = get_user_choice()

    if user_choice == "1":
        tx_amount = get_transaction_value()
        add_transaction(tx_amount, get_last_blockchain_value())
    elif user_choice == "2":
        print_blockchain_elements()
    elif user_choice == "3":
        if len(blockchain) >= 1:
            blockchain[0] = [2.0]
    elif user_choice == "4":
        waiting_for_input = False
    else:
        print("Invalid Choice, please try again")

    if not verify_chain():
        print("Invalid blockchain")
        break
else:
    print("goodbye")
