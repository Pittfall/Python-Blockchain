from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from wallet import Wallet
from blockchain import Blockchain

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods=['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


@app.route('/wallet', methods=['POST'])
def create_keys():
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        return jsonify({
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }), 201
        return jsonify({
            'message': 'Saving the keys failed.',
        }), 500


@app.route('/wallet', methods=['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key, port)
        print(blockchain)
        return jsonify({
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }), 201
    return jsonify({
        'message': 'Loading the keys failed.',
    }), 500


@app.route('/balance', methods=['GET'])
def get_balance():
    balance = blockchain.get_balance()

    if balance == None:
        return jsonify({
            'message': 'Loading balance failed.',
            'wallet_set_up': wallet.public_key != None,
        }), 500

    return jsonify({
        'message': 'Fetched balance successfully.',
        'funds': balance
    }), 201


@app.route('/broadcast-transaction', methods=['POST'])
def boradcast_transaction():
    values = request.get_json()

    if not values:
        return jsonify({
            'message': 'No data found.',
        }), 400
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(key in values for key in required):
        return jsonify({
            'message': 'Some data is missing.',
        }), 400
    success = blockchain.add_transaction(
        values['recipient'], values['sender'], values['signature'], values['amount'], is_receiving=True)
    if not success:
        return jsonify({
            'message': 'Creating a transaction failed.',
        }), 400

    return jsonify({
        'message': 'Successfully added transaction.',
        'transaction': {
            'sender': values['sender'],
            'recipient': values['recipient'],
            'amount': values['amount'],
            'signature': values['signature']
        }
    }), 201


@app.route('/broadcast-block', methods=['POST'])
def boradcast_block():
    values = request.get_json()

    if not values:
        return jsonify({
            'message': 'No data found.',
        }), 400
    if 'block' not in values:
        return jsonify({
            'message': 'Some data is missing.',
        }), 400
    block = values['block']
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            return jsonify({
                'message': 'Block added',
            }), 201
        else:
            return jsonify({
                'message': 'Block seems invalid',
            }), 409
    elif block['index'] > blockchain.chain[-1].index:
        blockchain.resolve_conflicts = True
        return jsonify({
            'message': 'Blockchain seems to differ from local blockchain',
        }), 200
    else:
        return jsonify({
            'message': 'Blockchain seems to be shorter.  Block not added',
        }), 409


@app.route('/transaction', methods=['POST'])
def add_transaction():
    if wallet.public_key == None:
        return jsonify({
            'message': 'No wallet set up.',
        }), 400

    values = request.get_json()
    if not values:
        return jsonify({
            'message': 'No data found.',
        }), 400

    required_fields = ['recipient', 'amount']
    if not all(field in values for field in required_fields):
        return jsonify({
            'message': 'Required data is missing.',
        }), 400

    recipient = values['recipient']
    amount = values['amount']
    signature = wallet.sign_transaction(wallet.public_key, recipient, amount)
    success = blockchain.add_transaction(
        recipient, wallet.public_key, signature, amount)

    if not success:
        return jsonify({
            'message': 'Creating a transaction failed.',
        }), 400

    return jsonify({
        'message': 'Successfully added transaction.',
        'transaction': {
            'sender': wallet.public_key,
            'recipient': recipient,
            'amount': amount,
            'signature': signature
        },
        'funds': blockchain.get_balance()
    }), 201


@app.route('/mine', methods=['POST'])
def mine():
    if blockchain.resolve_conflicts:
        return jsonify({
            'message': 'Resolve conflicts first, block not added!'
        }), 409

    block = blockchain.mine_block()
    if block != None:
        return jsonify({
            'message': 'Block added successfully',
            'block': block.to_dict(),
            'funds': blockchain.get_balance()
        }), 201

    return jsonify({
        'message': 'Adding a block failed.',
        'wallet_set_up': wallet.public_key != None,
    }), 500


@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    if replaced:
        return jsonify({
            'message': 'Chain was replaced!'
        }), 200
    else:
        return jsonify({
            'message': 'Local chain kept!'
        }), 200


@app.route('/transactions', methods=['GET'])
def get_open_transaction():
    transactions = blockchain.get_open_transactions()
    dict_transactions = [tx.to_dict() for tx in transactions]
    return jsonify(dict_transactions), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    dict_chain = [block.to_dict() for block in chain_snapshot]
    return jsonify(dict_chain), 200


@app.route('/node', methods=['POST'])
def add_node():
    values = request.get_json()
    if not values:
        return jsonify({
            'message': 'No data attached.'
        }), 400

    if 'node' not in values:
        return jsonify({
            'message': 'No node data found.'
        }), 400

    node = values['node']
    blockchain.add_peer_node(node)

    return jsonify({
        'message': 'Node added successfully.',
        'all_nodes': blockchain.get_peer_nodes()
    }), 201


@app.route('/node/<node_url>', methods=['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url == None:
        return jsonify({
            'message': 'No node found.'
        }), 400

    blockchain.remove_peer_node(node_url)

    return jsonify({
        'message': 'Node removed successfully.',
        'all_nodes': blockchain.get_peer_nodes()
    }), 200


@app.route('/node', methods=['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    return jsonify({
        'all_nodes': nodes
    }), 200


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=5000)
    args = parser.parse_args()
    port = args.port
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)
    app.run(host='0.0.0.0', port=port)
