import hashlib
import time
import json

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def is_valid(self):
        # Перевірка, чи є відправник і одержувач різними особами
        if self.sender == self.receiver:
            return False

        # Перевірка, чи є кількість коштів додатнім числом
        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            return False

        return True

    def calculate_hash(self):
        transaction_content = f"{self.sender}{self.receiver}{self.amount}".encode()
        return hashlib.sha256(transaction_content).hexdigest()
class Block:
    def __init__(self, transactions, previous_hash):
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.time = time.time()
        self.nonce = 0
        self.merkle_tree = MerkleTree([t.calculate_hash() for t in transactions])
        self.merkle_tree.create_tree()
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        transaction_hashes = "".join(transaction.calculate_hash() for transaction in self.transactions)
        block_content = f"{transaction_hashes}{self.previous_hash}{self.time}{self.nonce}".encode()
        return hashlib.sha256(block_content).hexdigest()

    def add_transaction(self, transaction):
        if transaction.is_valid():
            self.transactions.append(transaction)
        else:
            raise Exception("Invalid transaction")

    def is_valid(self):
        for transaction in self.transactions:
            if not transaction.is_valid():
                return False

        if self.calculate_hash() != self.hash:
            return False

        return True

    def mine(self, difficulty):
        target = "0" * difficulty

        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

class MerkleTree:
    def __init__(self, transactions=None):
        self.transactions = transactions
        self.merkle_tree = []

    def create_tree(self):
        transactions = self.transactions
        temp_transactions = []

        for transaction in transactions:
            transaction_hash = hashlib.sha256(transaction.encode()).hexdigest()
            self.merkle_tree.append(transaction_hash)
            temp_transactions.append(transaction_hash)

        while len(temp_transactions) > 1:
            temp_transactions = self.create_parent(temp_transactions)

    def create_parent(self, transactions):
        temp_transactions = []

        for i in range(0, len(transactions)-1, 2):
            transaction_hash = hashlib.sha256((transactions[i] + transactions[i+1]).encode()).hexdigest()
            self.merkle_tree.append(transaction_hash)
            temp_transactions.append(transaction_hash)

        if len(transactions) % 2 == 1:
            transaction_hash = hashlib.sha256(transactions[-1].encode()).hexdigest()
            self.merkle_tree.append(transaction_hash)
            temp_transactions.append(transaction_hash)

        return temp_transactions

    def get_root(self):
        return self.merkle_tree[-1]

class Blockchain:
    def __init__(self):
        self.chain = []
        self.merkle_tree = MerkleTree([])
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block([], "0")
        self.chain.append(genesis_block)
        self.merkle_tree.transactions.append(genesis_block.hash)
        self.merkle_tree.create_tree()

    def add_block(self, new_block, difficulty):
        new_block.mine(difficulty)
        self.chain.append(new_block)
        self.merkle_tree.transactions.append(new_block.hash)
        self.merkle_tree.create_tree()
    def get_latest_block(self):
        return self.chain[-1]

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if not current_block.is_valid():
                return False

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def get_balance(self, person):
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == person:
                    balance -= transaction.amount
                if transaction.receiver == person:
                    balance += transaction.amount

        return balance

    def save_to_file(self, file_name):
        chain_data = json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        with open(file_name, 'w') as file:
            file.write(chain_data)

    @classmethod
    def load_from_file(cls, file_name):
        with open(file_name, 'r') as file:
            chain_data = file.read()
        chain_data = json.loads(chain_data)

        blockchain = cls()
        blockchain.chain = []

        for block_data in chain_data['chain']:
            block = Block([Transaction(t['sender'], t['receiver'], t['amount']) for t in block_data['transactions']],
                          block_data['previous_hash'])
            block.time = float(block_data['time'])  # конвертуємо часову мітку назад в число з плаваючою комою
            block.hash = block_data['hash']
            block.nonce = block_data['nonce']
            blockchain.chain.append(block)

        return blockchain

    def get_all_persons(self):
        persons = set()
        for block in self.chain:
            for transaction in block.transactions:
                persons.add(transaction.sender)
                persons.add(transaction.receiver)
        return persons

    def get_min_max_balance(self, person):
        balance = 0
        min_balance = float('inf')
        max_balance = float('-inf')
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == person:
                    balance -= transaction.amount
                if transaction.receiver == person:
                    balance += transaction.amount
                min_balance = min(min_balance, balance)
                max_balance = max(max_balance, balance)
        return min_balance, max_balance

def main():
    # Створюємо новий блокчейн
    blockchain = Blockchain()

    # Створюємо декілька транзакцій
    transaction1 = Transaction("Alice", "Bob", 50)
    transaction2 = Transaction("Bob", "Charlie", 20)
    transaction3 = Transaction("Charlie", "Alice", 30)

    # Додаємо транзакції до блоку
    block = Block([transaction1, transaction2, transaction3], blockchain.get_latest_block().hash)

    # Додаємо блок до блокчейну
    blockchain.add_block(block, 2)

    print("Blockchain is valid?")

    # Перевіряємо валідність блокчейну
    print(blockchain.is_chain_valid())

    # Виводимо баланси осіб
    print("Balances")
    print(blockchain.get_balance("Alice"))
    print(blockchain.get_balance("Bob"))
    print(blockchain.get_balance("Charlie"))

    # Зберігаємо блокчейн в файл
    blockchain.save_to_file("blockchain.txt")

    # Завантажуємо блокчейн з файлу
    loaded_blockchain = Blockchain.load_from_file("blockchain.txt")

    print("Blockchain is valid?")
    # Перевіряємо валідність завантаженого блокчейну
    print(loaded_blockchain.is_chain_valid())
    print("Balances")
    # Виводимо баланси осіб у завантаженому блокчейну
    print(loaded_blockchain.get_balance("Alice"))
    print(loaded_blockchain.get_balance("Bob"))
    print(loaded_blockchain.get_balance("Charlie"))

    print("All people")

    print(blockchain.get_all_persons())

    print("Min max balance")
    print(blockchain.get_min_max_balance("Alice"))

    # Виводимо корінь дерева Merkle для кожного блоку
    for i, block in enumerate(blockchain.chain):
        if block.merkle_tree.transactions:
            print(f"Merkle root for block {i}: {block.merkle_tree.get_root()}")
        else:
            print(f"Block {i} has no transactions")

    # Виводимо корінь дерева Merkle для всього блокчейну
    if blockchain.merkle_tree.transactions:
        print(f"Merkle root for entire blockchain: {blockchain.merkle_tree.get_root()}")
    else:
        print("Blockchain has no blocks")

if __name__ == "__main__":
    main()