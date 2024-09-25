from solcx import compile_standard, install_solc 
from ReadContract import read_contract 


def compile_Contarct():
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
    return compile_solidity



def convert_contract_to_json():
    with open("compiled_code.json", "w") as file:
        json.dump(compile_Contarct(), file)