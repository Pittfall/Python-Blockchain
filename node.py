from uuid import uuid4

from blockchain import Blockchain
from verification import Verification


class Node:
    def __init__(self):
        # self.id = str(uuid4())
        self.id = "Andrew"
        self.blockchain = Blockchain(self.id)

    def get_transaction_value(self):
        tx_recipient = input("Enter the recipient of the transaction: ")
        tx_amount = float(input("Please enter a transaction amount: "))
        return (tx_recipient, tx_amount)

    def get_user_choice(self):
        return input("Your choice: ")

    def print_blockchain_elements(self):
        print("-" * 20)
        for block in self.blockchain.chain:
            print(block)
        else:
            print("-" * 20)

    def listen_for_input(self):
        waiting_for_input = True

        while waiting_for_input:
            print("Please choose")
            print("1. Add a new transaction value")
            print("2. Mine a new block")
            print("3. Output the blockchain blocks")
            print("4. Check transaction validity")
            print("q. Exit")
            user_choice = self.get_user_choice()

            if user_choice == "1":
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                if self.blockchain.add_transaction(recipient=recipient, sender=self.id, amount=amount):
                    print("Added transaction!!")
                else:
                    print("Transaction failed!!")
                print(self.blockchain.get_open_transactions())
            elif user_choice == "2":
                self.blockchain.mine_block()
            elif user_choice == "3":
                self.print_blockchain_elements()
            elif user_choice == "4":
                if Verification.verify_transactions(self.blockchain.get_open_transactions(),
                                                self.blockchain.get_balance):
                    print("All transactions are valid")
                else:
                    print("There are invalid transactions")
            elif user_choice == "q":
                waiting_for_input = False
            else:
                print("Invalid Choice, please try again")

            if not Verification.verify_chain(self.blockchain.chain):
                print("Invalid blockchain")
                break

            print("-" * 30)
            print('Balance of {}: {:6.2f}'.format(
                self.id, self.blockchain.get_balance()))
            print("-" * 30)
        else:
            print("goodbye")

node = Node()
node.listen_for_input()