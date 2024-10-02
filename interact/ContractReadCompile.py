from solcx import compile_standard, install_solc  
import json
import os
from dotenv import load_dotenv


def compile_Contract():
    install_solc('0.8.27')
    
    contract_code = read_contract()
    compile_solidity = compile_standard({
        "language": "Solidity",
        "sources": {"PokerContract.sol": {
            "content": contract_code
        }},
        "settings": {
            "outputSelection": {
                "*": {"*":
                    ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        }
    },solc_version = "0.8.27")
    #print(compile_solidity)
    return compile_solidity



def convert_contract_to_json():
    with open("compiled_code.json", "w") as file:
         json.dump(compile_Contract(), file)
                    


def read_contract():
    load_dotenv()
    contract_path = os.getenv("CONTRACT_PATH")
    try:
        with open(contract_path, 'r') as file:
            contract_contents = file.read()
            #print(contract_contents)
            return contract_contents
    except Exception as e:
        print(f'Error reading file: {e}')   



#a = convert_contract_to_json()
#print(a)        