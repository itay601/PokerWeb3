import streamlit as st
import time
from web3 import Web3
from ContractReadCompile import compile_Contract

class PokerGameFrontend:
    def __init__(self):
        # Web3 Connection
        self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        
        # Load Contract
        compiled_contract = compile_Contract()
        self.contract_abi = compiled_contract['contracts']['PokerContract.sol']['Poker']['abi']
        self.contract_address = Web3.to_checksum_address('0x5FbDB2315678afecb367f032d93F642f64180aa3')
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)
        
        # Card mapping
        self.card_dict = self.dict_cards_of_the_game()

    def dict_cards_of_the_game(self):
        suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        return {i: f"{ranks[i % 13]} of {suits[i // 13]}" for i in range(52)}

    def get_game_ended_event(self, game_id):
        game_ended_filter = self.contract.events.GameEnded.create_filter(from_block=0, to_block='latest')
        for i in range(60):  # Wait up to 60 seconds
            events = game_ended_filter.get_new_entries()
            for event in events:
                if event['args']['gameId'] == game_id:
                    return event
            time.sleep(1)
        return None  

    def get_game_id(self):
        game_id = self.contract.functions.getLastID().call()
        return game_id      

    def connect_wallet(self):
        st.title("🃏 Blockchain Poker Game")
        
        if 'wallet_connected' not in st.session_state:
            st.session_state.wallet_connected = False
            st.session_state.game_id = None
        
        wallet_address = st.text_input("Enter your wallet address")

        if st.button("🔗 Connect Wallet"):
            try:
                if wallet_address and self.w3.is_address(wallet_address):
                    st.session_state.wallet_address = self.w3.to_checksum_address(wallet_address)
                    st.session_state.wallet_connected = True
                    st.success(f"Wallet Connected: {st.session_state.wallet_address}")
                else:
                    st.warning("Invalid wallet address.")
            except Exception as e:
                st.error(f"Connection Error: {e}")
        
        return st.session_state.wallet_connected

    def get_game_state(self, game_id):
        try:
            #need to be changed or ADD it
            game_state = self.contract.functions.getGameState(game_id).call()
            #################################################3
            st.write("Game State Details:")
            st.json({
                "Stage": ["PreFlop", "Flop", "Turn", "River","End"][game_state[0]],
                "Current Player": game_state[1],
                "Pot Size": f"{self.w3.from_wei(game_state[2], 'ether')} ETH",
                "Players": game_state[3]
            })
        except Exception as e:
            st.error(f"Error fetching game state: {e}")

    def game_actions(self, wallet_address):
        st.header("🃏 Poker Game Actions")
        
        # Game Creation
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Create Game")
            buy_in = st.number_input("Game Buy-in (ETH)", min_value=0.1, step=0.1, key="create_buy_in")
            
            if st.button("Create Game"):
                try:
                    buy_in_wei = self.w3.to_wei(buy_in, 'ether')
                    tx_params = {
                        'from': wallet_address,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('20', 'gwei')
                    }
                    tx_hash = self.contract.functions.createGame(buy_in_wei).transact(tx_params)
                    st.success(f"{tx_hash}")
                    st.session_state.game_id = self.get_game_id()
                    st.success(f"Game Created: ID {st.session_state.game_id}")
                except Exception as e:
                    st.error(f"Game Creation Failed: {e}")
        
        with col2:
            st.subheader("Join Game")
            game_id = st.number_input("Game ID to Join", min_value=0, step=1, key="join_game_id")
            join_buy_in = st.number_input("Buy-in (ETH)", min_value=0.1, step=0.1, key="join_buy_in")
            
            if st.button("Join Game"):
                try:
                    tx_params = {
                        'from': wallet_address,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('20', 'gwei'),
                        'value': self.w3.to_wei(join_buy_in, 'ether')
                    }
                    tx_hash = self.contract.functions.joinGame(game_id).transact(tx_params)
                    st.session_state.game_id = game_id
                    st.success(f"Joined Game: {game_id}")
                except Exception as e:
                    st.error(f"Game Joining Failed: {e}")

        # Game Interaction
        if st.session_state.game_id is not None:
            st.header(f"Game #{st.session_state.game_id} Actions")
            
            # Get Game State
            if st.button("Get Game State"):
                self.get_game_state(st.session_state.game_id)
            
            # Start Game
            if st.button("Start Game"):
                try:
                    tx_params = {
                        'from': wallet_address,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('20', 'gwei')
                    }
                    tx_hash = self.contract.functions.startGame(st.session_state.game_id).transact(tx_params)
                    st.success("Game Started!")
                except Exception as e:
                    st.error(f"Game Start Failed: {e}")
            
            # Player Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                bet_amount = st.number_input("Bet Amount (ETH)", min_value=0.01, step=0.01)
                if st.button("Bet"):
                    try:
                        tx_params = {
                            'from': wallet_address,
                            'gas': 2000000,
                            'gasPrice': self.w3.to_wei('20', 'gwei')
                        }
                        bet_wei = self.w3.to_wei(bet_amount, 'ether')
                        tx_hash = self.contract.functions.bet(st.session_state.game_id, bet_wei).transact(tx_params)
                        st.success("Bet Placed!")
                    except Exception as e:
                        st.error(f"Bet Failed: {e}")
            
            with col2:
                if st.button("Call"):
                    try:
                        tx_params = {
                            'from': wallet_address,
                            'gas': 2000000,
                            'gasPrice': self.w3.to_wei('20', 'gwei')
                        }
                        tx_hash = self.contract.functions.call(st.session_state.game_id).transact(tx_params)
                        st.success("Called!")
                    except Exception as e:
                        st.error(f"Call Failed: {e}")
            
            with col3:
                if st.button("Fold"):
                    try:
                        tx_params = {
                            'from': wallet_address,
                            'gas': 2000000,
                            'gasPrice': self.w3.to_wei('20', 'gwei')
                        }
                        tx_hash = self.contract.functions.fold(st.session_state.game_id).transact(tx_params)
                        st.success("Folded!")
                    except Exception as e:
                        st.error(f"Fold Failed: {e}")
            
            # View Cards
            st.subheader("Card Viewer")
            if st.button("View My Community Cards"):
                try:
                    cards = self.contract.functions.getCommunityCards(st.session_state.game_id).call()
                    revealed_cards = [self.card_dict[card] for card in cards if card != 0]
                    st.write("Community Cards:", revealed_cards)
                except Exception as e:
                    st.error(f"Error revealing community cards: {e}")
            
            if st.button("View My Cards"):
                try:
                    cards = self.contract.functions.getPlayerCards(st.session_state.game_id, wallet_address).call()
                    revealed_cards = [self.card_dict[card] for card in cards if card != 0]
                    st.write("Your Cards:", revealed_cards)
                except Exception as e:
                    st.error(f"Error revealing player cards: {e}")
            #End game
            st.subheader("Check End Game State")
            if st.button("Check State winning"):
                try:
                    st.write("\nGame ended\n")
                    game_ended_event = get_game_ended_event(game_id)
                    if game_ended_event:
                        winner = game_ended_event['args']['winner']
                        winnings = game_ended_event['args']['winningAmount']
                        st.write(f"Game ended. Winner: {winner}, Winnings: {w3.from_wei(winnings, 'ether')} ETH")
                    else:
                        st.write("Game ended event not found")   
                except Exception as e:
                    st.error(f"Error revealing player cards: {e}")         

    
    def run(self):
        wallet_connected = self.connect_wallet()
        if wallet_connected:
            self.game_actions(st.session_state.wallet_address)

# Streamlit app initialization
if __name__ == "__main__":
    poker_app = PokerGameFrontend()
    poker_app.run()