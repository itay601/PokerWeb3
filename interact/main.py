import streamlit as st
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

    def connect_wallet(self):
        st.title("Blockchain Poker Game")
        
        if 'wallet_connected' not in st.session_state:
            st.session_state.wallet_connected = False
        
        if st.button("Connect Wallet"):
            try:
                accounts = self.w3.eth.accounts
                if accounts:
                    st.session_state.wallet_address = accounts[0]
                    st.session_state.wallet_connected = True
                    st.success(f"Wallet Connected: {self.w3.to_checksum_address(accounts[0])}")
                else:
                    st.warning("No accounts found.")
            except Exception as e:
                st.error(f"Connection Error: {e}")
        
        return st.session_state.wallet_connected

    def game_actions(self, wallet_address):
        st.header("Poker Game Actions")
        
        # Game Creation
        buy_in = st.number_input("Game Buy-in (ETH)", min_value=0.1, step=0.1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Game"):
                try:
                    buy_in_wei = self.w3.to_wei(buy_in, 'ether')
                    tx_params = {
                        'from': wallet_address,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('20', 'gwei')
                    }
                    tx_hash = self.contract.functions.createGame(buy_in_wei).transact(tx_params)
                    st.success(f"Game Created: {tx_hash.hex()}")
                except Exception as e:
                    st.error(f"Game Creation Failed: {e}")
        
        with col2:
            game_id = st.number_input("Game ID to Join", min_value=0, step=1)
            if st.button("Join Game"):
                try:
                    tx_params = {
                        'from': wallet_address,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('20', 'gwei'),
                        'value': self.w3.to_wei(buy_in, 'ether')
                    }
                    tx_hash = self.contract.functions.joinGame(game_id).transact(tx_params)
                    st.success(f"Joined Game: {tx_hash.hex()}")
                except Exception as e:
                    st.error(f"Game Joining Failed: {e}")

    def run(self):
        wallet_connected = self.connect_wallet()
        if wallet_connected:
            self.game_actions(st.session_state.wallet_address)

# Streamlit app initialization
if __name__ == "__main__":
    poker_app = PokerGameFrontend()
    poker_app.run()