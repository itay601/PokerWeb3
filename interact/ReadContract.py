import os
from dotenv import load_dotenv


def read_contract():
    load_dotenv()
    contract_path = os.getenv('CONTRACT_PATH')
    try:
        with open(contract_path, 'r') as file:
            contract_contents = file.read()
            print(f'Contract file contents:\n{contract_contents}')
            return contract_contents
    except Exception as e:
        print(f'Error reading file: {e}')