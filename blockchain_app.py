import hashlib
import time
import numpy as np
from flask import Flask, jsonify, request
import mysql.connector

# MySQL Configuration
db_config = {
    "host": "localhost",
    "user": "root",  # Replace with your MySQL username
    "password": "",  # Replace with your MySQL password
    "database": "blockchain_db",  # Replace with your database name
}

# Initialize MySQL connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Create transactions table if it doesn't exist
def create_transactions_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender VARCHAR(255) NOT NULL,
            receiver VARCHAR(255) NOT NULL,
            amount FLOAT NOT NULL,
            block_index INT NOT NULL
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

# Blockchain class
class Blockchain:
    def __init__(self):
        self.chain = []  # Store all blocks
        self.transactions = []  # Current transactions
        self.difficulty = 1  # Start with a lower difficulty
        self.reward = 10  # Reward for solving ML tasks
        self.create_block(proof=0, previous_hash="0")  # Genesis block

    def create_block(self, proof, previous_hash):
        block = {
            "index": len(self.chain) + 1,  # Unique block index
            "timestamp": time.time(),
            "transactions": self.transactions + [{
                "sender": "Network",
                "receiver": "Miner",
                "amount": self.reward,
            }],
            "proof": proof,
            "previous_hash": previous_hash,
        }
        self.transactions = []  # Reset transactions
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def proof_of_useful_work(self, task_input):
        try:
            matrix_size = task_input["matrix_size"]
            seed = task_input["seed"]

            # Retry mining until a valid proof is found
            max_attempts = 15  # Limit the number of attempts
            for attempt in range(max_attempts):
                np.random.seed(seed + attempt)  # Change seed for each attempt
                A = np.random.rand(matrix_size, matrix_size)
                B = np.random.rand(matrix_size, matrix_size)

                # Simulate "useful work" by computing matrix multiplication
                start_time = time.time()
                result = np.dot(A, B)
                elapsed_time = time.time() - start_time

                # Verify work: Hash of result must start with N zeros (difficulty)
                result_hash = hashlib.sha256(str(result.sum()).encode()).hexdigest()
                if result_hash[:self.difficulty] == "0" * self.difficulty:
                    return {"proof": result_hash, "time": elapsed_time}

            return None  # No valid proof found after max attempts
        except Exception as e:
            print(f"Error in proof_of_useful_work: {e}")
            return None

    def add_transaction(self, sender, receiver, amount):
        transaction = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
        }
        self.transactions.append(transaction)

        # Store transaction in MySQL database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (sender, receiver, amount, block_index)
            VALUES (%s, %s, %s, %s)
            """,
            (sender, receiver, amount, len(self.chain) + 1),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return self.get_last_block()["index"] + 1

    def is_chain_valid(self, chain):
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            if current_block["previous_hash"] != self.hash(previous_block):
                return False
        return True

    @staticmethod
    def hash(block):
        encoded_block = str(block).encode()
        return hashlib.sha256(encoded_block).hexdigest()

# Flask App
app = Flask(__name__)
blockchain = Blockchain()

# Create transactions table on startup
create_transactions_table()

# Web Interface
@app.route("/")
def home():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blockchain Web Interface</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; }
        .card { margin-bottom: 20px; }
        table { width: 100%; margin-bottom: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .transaction-table { margin: 0; }
        .transaction-table td { padding: 5px; border: none; }
        .table-responsive { overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center">Blockchain Web Interface</h1>

        <!-- Mine Block Section -->
        <div class="card">
            <div class="card-body">
                <h2>Mine a Block</h2>
                <form id="mineForm">
                    <div class="mb-3">
                        <label for="matrix_size" class="form-label">Matrix Size</label>
                        <input type="number" class="form-control" id="matrix_size" name="matrix_size" value="105" required>
                    </div>
                    <div class="mb-3">
                        <label for="seed" class="form-label">Seed</label>
                        <input type="number" class="form-control" id="seed" name="seed" value="42" required>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="mineBlock()">Mine Block</button>
                </form>
            </div>
        </div>

        <!-- Add Transaction Section -->
        <div class="card">
            <div class="card-body">
                <h2>Add a Transaction</h2>
                <form id="transactionForm">
                    <div class="mb-3">
                        <label for="sender" class="form-label">Sender</label>
                        <input type="text" class="form-control" id="sender" name="sender" required>
                    </div>
                    <div class="mb-3">
                        <label for="receiver" class="form-label">Receiver</label>
                        <input type="text" class="form-control" id="receiver" name="receiver" required>
                    </div>
                    <div class="mb-3">
                        <label for="amount" class="form-label">Amount</label>
                        <input type="number" class="form-control" id="amount" name="amount" required>
                    </div>
                    <button type="button" class="btn btn-primary" onclick="addTransaction()">Add Transaction</button>
                </form>
            </div>
        </div>

        <!-- Blockchain Section -->
        <div class="card">
            <div class="card-body">
                <h2>Blockchain</h2>
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Index</th>
                                <th>Timestamp</th>
                                <th>Proof</th>
                                <th>Previous Hash</th>
                                <th>Transactions</th>
                            </tr>
                        </thead>
                        <tbody id="blockchainBody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Transactions Section -->
        <div class="card">
            <div class="card-body">
                <h2>Transactions</h2>
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Sender</th>
                                <th>Receiver</th>
                                <th>Amount</th>
                                <th>Block Index</th>
                            </tr>
                        </thead>
                        <tbody id="transactionsBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Function to mine a block
        async function mineBlock() {
            const form = document.getElementById('mineForm');
            const data = {
                matrix_size: parseInt(form.matrix_size.value),
                seed: parseInt(form.seed.value),
            };
            const response = await fetch('/mine_block', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            alert(result.message);
            updateBlockchain();
            updateTransactions();
        }

        // Function to add a transaction
        async function addTransaction() {
            const form = document.getElementById('transactionForm');
            const data = {
                sender: form.sender.value,
                receiver: form.receiver.value,
                amount: parseFloat(form.amount.value),
            };
            const response = await fetch('/add_transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            alert(result.message);
            updateBlockchain();
            updateTransactions();
        }

        // Function to update the blockchain table
        async function updateBlockchain() {
            const response = await fetch('/get_chain');
            const data = await response.json();
            const blockchainBody = document.getElementById('blockchainBody');
            blockchainBody.innerHTML = ''; // Clear existing rows

            data.chain.forEach(block => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${block.index}</td>
                    <td>${new Date(block.timestamp * 1000).toLocaleString()}</td>
                    <td>${block.proof}</td>
                    <td>${block.previous_hash}</td>
                    <td>
                        <table class="transaction-table">
                            ${block.transactions.map(tx => `
                                <tr>
                                    <td>${tx.sender} → ${tx.receiver}</td>
                                    <td>${tx.amount}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </td>
                `;
                blockchainBody.appendChild(row);
            });
        }

        // Function to update the transactions table
        async function updateTransactions() {
            const response = await fetch('/get_transactions');
            const data = await response.json();
            const transactionsBody = document.getElementById('transactionsBody');
            transactionsBody.innerHTML = ''; // Clear existing rows

            data.forEach(transaction => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${transaction.sender}</td>
                    <td>${transaction.receiver}</td>
                    <td>${transaction.amount}</td>
                    <td>${transaction.block_index}</td>
                `;
                transactionsBody.appendChild(row);
            });
        }

        // Initial load
        updateBlockchain();
        updateTransactions();
    </script>
</body>
</html>
    """

# API Endpoints
@app.route("/mine_block", methods=["POST"])
def mine_block():
    try:
        data = request.get_json()
        if not data or "matrix_size" not in data or "seed" not in data:
            return jsonify({"message": "Invalid task input!"}), 400

        # Perform useful work
        task_input = {"matrix_size": data["matrix_size"], "seed": data["seed"]}
        work_result = blockchain.proof_of_useful_work(task_input)

        if work_result:
            last_block = blockchain.get_last_block()
            proof = work_result["proof"]
            previous_hash = blockchain.hash(last_block)
            block = blockchain.create_block(proof, previous_hash)
            response = {
                "message": "Block mined successfully!",
                "block": block,
                "work_time": work_result["time"],
            }
            return jsonify(response), 200
        return jsonify({"message": "Useful work failed to meet difficulty after multiple attempts!"}), 400
    except Exception as e:
        print(f"Error in mine_block: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    try:
        data = request.get_json()
        required_fields = ["sender", "receiver", "amount"]
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Missing transaction data"}), 400
        index = blockchain.add_transaction(data["sender"], data["receiver"], data["amount"])
        return jsonify({"message": f"Transaction added to Block {index}"}), 201
    except Exception as e:
        print(f"Error in add_transaction: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route("/get_chain", methods=["GET"])
def get_chain():
    try:
        response = {"chain": blockchain.chain, "length": len(blockchain.chain)}
        return jsonify(response), 200
    except Exception as e:
        print(f"Error in get_chain: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route("/get_transactions", methods=["GET"])
def get_transactions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(transactions), 200
    except Exception as e:
        print(f"Error in get_transactions: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route("/is_valid", methods=["GET"])
def is_valid():
    try:
        valid = blockchain.is_chain_valid(blockchain.chain)
        return jsonify({"message": "Blockchain is valid!" if valid else "Blockchain is not valid!"}), 200
    except Exception as e:
        print(f"Error in is_valid: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)