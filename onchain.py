import hashlib
import json
import time
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect("blockchain.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS blocks (
                index INTEGER PRIMARY KEY, 
                timestamp TEXT, 
                transactions TEXT, 
                previous_hash TEXT, 
                nonce INTEGER, 
                hash TEXT)
            ""
            )
    conn.commit()
    conn.close()

init_db()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.load_chain()
        if not self.chain:
            self.create_genesis_block()
    
    def load_chain(self):
        conn = sqlite3.connect("blockchain.db")
        c = conn.cursor()
        c.execute("SELECT * FROM blocks")
        rows = c.fetchall()
        self.chain = [self.convert_row_to_block(row) for row in rows]
        conn.close()
    
    def convert_row_to_block(self, row):
        return {
            'index': row[0],
            'timestamp': row[1],
            'transactions': json.loads(row[2]),
            'previous_hash': row[3],
            'nonce': row[4],
            'hash': row[5]
        }
    
    def create_genesis_block(self):
        genesis_block = self.create_block(nonce=0, previous_hash='0')
        self.chain.append(genesis_block)
        self.save_block(genesis_block)
    
    def create_block(self, nonce, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(time.time()),
            'transactions': self.pending_transactions,
            'previous_hash': previous_hash,
            'nonce': nonce,
            'hash': ''
        }
        block['hash'] = self.hash_block(block)
        self.pending_transactions = []
        return block
    
    def hash_block(self, block):
        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()
    
    def proof_of_work(self, previous_hash):
        nonce = 0
        while True:
            block = self.create_block(nonce, previous_hash)
            if block['hash'][:4] == '0000':
                return block
            nonce += 1
    
    def add_transaction(self, sender, receiver, amount):
        self.pending_transactions.append({'sender': sender, 'receiver': receiver, 'amount': amount})
    
    def mine_block(self):
        last_block = self.chain[-1]
        new_block = self.proof_of_work(last_block['hash'])
        self.chain.append(new_block)
        self.save_block(new_block)
        return new_block
    
    def save_block(self, block):
        conn = sqlite3.connect("blockchain.db")
        c = conn.cursor()
        c.execute("INSERT INTO blocks VALUES (?, ?, ?, ?, ?, ?)",
                  (block['index'], block['timestamp'], json.dumps(block['transactions']), block['previous_hash'], block['nonce'], block['hash']))
        conn.commit()
        conn.close()

blockchain = Blockchain()

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required_fields = ['sender', 'receiver', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing values'}), 400
    blockchain.add_transaction(data['sender'], data['receiver'], data['amount'])
    return jsonify({'message': 'Transaction added!'}), 201

@app.route('/mine', methods=['GET'])
def mine():
    new_block = blockchain.mine_block()
    return jsonify(new_block), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify(blockchain.chain), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
