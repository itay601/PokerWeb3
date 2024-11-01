from web3 import Web3
from web3.logs import DISCARD
import json
from ContractReadCompile import compile_Contract 
from dotenv import load_dotenv
import os
import time
from web3.exceptions import ContractLogicError

# Initialize Web3
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
assert w3.is_connected(), "Failed to connect to Ethereum network"

# Load the contract ABI and bytecode
compiled_contract = compile_Contract()
contract_abi = compiled_contract['contracts']['PokerContract.sol']['Poker']['abi']
contract_bytecode = compiled_contract['contracts']['PokerContract.sol']['Poker']['evm']['bytecode']['object']

# Contract address (make sure this is the correct deployed address)
contract_address = Web3.to_checksum_address('0x5FbDB2315678afecb367f032d93F642f64180aa3')
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Accounts
dealer_account = w3.eth.accounts[0]
player_accounts = [w3.eth.accounts[1], w3.eth.accounts[2], w3.eth.accounts[3]]

# Set up transaction parameters
def get_tx_params(account):
    return {
        'from': account,
        'gas': 2000000,
        'gasPrice': w3.to_wei('20', 'gwei')
    }

# Create a game
def create_game(buy_in_ether):
    buy_in_wei = w3.to_wei(buy_in_ether, 'ether')
    tx_hash = contract.functions.createGame(buy_in_wei).transact(get_tx_params(dealer_account))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Game created: {receipt.transactionHash.hex()}")
    return receipt.transactionHash

# Join a game
def join_game(game_id, buy_in_ether, player_account):
    buy_in_wei = w3.to_wei(buy_in_ether, 'ether')
    tx_params = get_tx_params(player_account)
    tx_params['value'] = buy_in_wei
    tx_hash = contract.functions.joinGame(game_id).transact(tx_params)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Player {player_account} joined game: {receipt.transactionHash.hex()}")

# Start a game
def start_game(game_id):
    tx_hash = contract.functions.startGame(game_id).transact(get_tx_params(dealer_account))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Game started: {receipt.transactionHash.hex()}")

# Player actions
def bet(game_id, amount, player_account):
    tx_hash = contract.functions.bet(game_id, amount).transact(get_tx_params(player_account))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Player {player_account} bet {w3.from_wei(amount, 'ether')} ETH: {receipt.transactionHash.hex()}")

def call(game_id, player_account):
    tx_hash = contract.functions.call(game_id).transact(get_tx_params(player_account))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Player {player_account} called: {receipt.transactionHash.hex()}")

def fold(game_id, player_account):
    tx_hash = contract.functions.fold(game_id).transact(get_tx_params(player_account))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Player {player_account} folded: {receipt.transactionHash.hex()}")

def dict_cards_of_the_game():
    suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    return {i: f"{ranks[i % 13]} of {suits[i // 13]}" for i in range(52)}

# Reveal community cards
def reveal_community_cards(game_id):
    try:
        cards = contract.functions.getCommunityCards(game_id).call()
        card_dict = dict_cards_of_the_game()
        revealed_cards = [card_dict[card] for card in cards if card != 0]
        print(f"Community cards: {', '.join(revealed_cards)}")
    except Exception as e:
        print(f"Error revealing community cards: {e}")

# Reveal player cards
def reveal_player_cards(game_id, player_account):
    try:
        cards = contract.functions.getPlayerCards(game_id, player_account).call()
        card_dict = dict_cards_of_the_game()
        revealed_cards = [card_dict[card] for card in cards if card != 0]
        print(f"Player {player_account} cards: {', '.join(revealed_cards)}")
    except Exception as e:
        print(f"Error revealing player cards: {e}")

def get_game_ended_event(contract, game_id):
    game_ended_filter = contract.events.GameEnded.create_filter(from_block=0, to_block='latest')
    for i in range(60):  # Wait up to 60 seconds
        events = game_ended_filter.get_new_entries()
        for event in events:
            if event['args']['gameId'] == game_id:
                return event
        time.sleep(1)
    return None

# Simulate a full game
def simulate_full_game():
    game_id = 3
    buy_in = 1.0 # 1 Ether

    # Create and join game
    create_game(buy_in)
    time.sleep(1)
    for player in player_accounts:
        join_game(game_id, buy_in, player)
        time.sleep(1)

    start_game(game_id)
    time.sleep(1)

    for player in player_accounts:
        reveal_player_cards(game_id, player)
        time.sleep(1)

    # Simulate betting rounds
    stages = ["PreFlop", "Flop", "Turn", "River"]
    for stage in stages:
        print(f"\n--- {stage} ---")
        for i, player in enumerate(player_accounts):
            time.sleep(1)
            action = i % 3  # 0: bet, 1: call, 2: fold
            if action == 0:
                bet(game_id, w3.to_wei(0.1, 'ether'), player)
            elif action == 1:
                call(game_id, player)
            else:
                call(game_id, player)
                #player_accounts.remove(player)
                
        time.sleep(1)
        reveal_community_cards(game_id)
        time.sleep(1)

    print("\nGame ended")
    game_ended_event = get_game_ended_event(contract, game_id)
    if game_ended_event:
        winner = game_ended_event['args']['winner']
        winnings = game_ended_event['args']['winningAmount']
        print(f"Game ended. Winner: {winner}, Winnings: {w3.from_wei(winnings, 'ether')} ETH")
    else:
        print("Game ended event not found")

simulate_full_game()