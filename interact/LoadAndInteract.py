from web3 import Web3
import json
from ContractReadCompile import compile_Contarct  # Fixed typo in import

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
assert w3.is_connected(), "Failed to connect to Ethereum network"

# Load the contract ABI and bytecode
compiled_contract = compile_Contarct()  # Fixed function name
contract_abi = compiled_contract['contracts']['PokerContract.sol']['Poker']['abi']
contract_bytecode = compiled_contract['contracts']['PokerContract.sol']['Poker']['evm']['bytecode']['object']

#print(contract_abi)

# Contract address (make sure this is the correct deployed address)
contract_address = Web3.to_checksum_address('0x5fbdb2315678afecb367f032d93f642f64180aa3')
poker_contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Set the default account
w3.eth.default_account = w3.eth.accounts[1]

def get_gas_price():
    return w3.eth.gas_price

def handle_transaction(func, *args, account=None):
    try:
        if account:
            tx = func(*args).build_transaction({
                'from': account,
                'nonce': w3.eth.get_transaction_count(account),
                'gas': 2000000,
                'gasPrice': get_gas_price()
            })
            signed_tx = w3.eth.account.sign_transaction(tx, private_key='your_private_key_here')
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        else:
            tx_hash = func(*args).transact()
        
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash
    except Exception as e:
        print(f"An error occurred: {e}")

def create_game(buy_in):
    handle_transaction(poker_contract.functions.createGame, buy_in)
    print("Game created!")

def join_game(game_id):
    buy_in = poker_contract.functions.games(game_id).call()[2]
    handle_transaction(poker_contract.functions.joinGame, game_id, {'value': buy_in})
    print("Joined game!")

def start_game(game_id):
    handle_transaction(poker_contract.functions.startGame, game_id)
    print("Game started!")

def bet(game_id, amount):
    handle_transaction(poker_contract.functions.bet, game_id, amount)
    print(f"Bet placed: {amount}")

def call(game_id):
    handle_transaction(poker_contract.functions.call, game_id)
    print("Called the bet!")

def raise_bet(game_id, amount):
    account = w3.eth.accounts[0]
    handle_transaction(poker_contract.functions.Raise, game_id, amount, account=account)  
    print(f"Raised the bet to: {amount}")

def fold(game_id):
    handle_transaction(poker_contract.functions.fold, game_id)
    print("Folded!")

def end_game(game_id, winner_address):
    handle_transaction(poker_contract.functions.endGame, game_id, winner_address)
    print("Game ended!")

# Example usage
if __name__ == "__main__":
    buy_in_amount = w3.to_wei(0.1, 'ether')
    create_game(buy_in_amount)
    
    game_id = 1  # Replace with the actual game ID

    # Assume game ID is 1 for demonstration
    join_game(game_id)
    start_game(game_id)
    bet(game_id, w3.to_wei(0.1, 'ether'))  # Changed initial bet amount
    call(game_id)
    raise_bet(game_id, w3.to_wei(0.2, 'ether'))
    fold(game_id)
    end_game(game_id, w3.eth.accounts[1])  # Replace with actual winner's address