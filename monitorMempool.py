from web3 import Web3
import pandas as pd
import time
import json
import re
# Connect to local Ethereum node
w3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

ROUTERS = {
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": "uniswap_v2",  # Uniswap V2 Router
    "0xE592427A0AEce92De3Edee1F18E0157C05861564": "uniswap_v3",  # Uniswap V3 Router
    "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F": "sushiswap_v2",  # Sushiswap V2 Router
    "0xBA12222222228d8Ba445958a75a0704d566BF2C8": "balancer",  # Balancer Vault
}

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]

with open("./abi/ABI.json", 'r') as file:
    abis = json.load(file)

# Excel file setup
EXCEL_FILE = "./dex_log.xlsx"
COLUMNS = ["Block Number", "Tx Hash", "From", "To", "Gas Price (Gwei)", "Time in Pool", "Function"] + [f"Param {i+1}" for i in range(15)]

transactionCount = {}
# Initialize DataFrame or load existing one
try:
    df = pd.read_excel(EXCEL_FILE)
except FileNotFoundError:
    df = pd.DataFrame(columns=COLUMNS)

def save_to_excel(transaction_data):
    """Save transaction data to an Excel spreadsheet."""
    global df
    df = pd.concat([df, pd.DataFrame(transaction_data, columns=COLUMNS)], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    print(f"Saved {len(transaction_data)} transactions to {EXCEL_FILE}")

def replaceSymbol(match):
    hex_value = match.group(0)  # Extract the full match (e.g., "0xabc123")
    try:
        token_contract = w3.eth.contract(address=hex_value, abi=ERC20_ABI)
        token_symbol = token_contract.functions.symbol().call()
        return f"{token_symbol} ({hex_value[:6]}...)"
    except:
        return hex_value  # Return the modified value to replace in the string

def monitor_mempool():
    """Monitor the mempool and log transactions."""
    latest_block = w3.eth.block_number
    print(f"Monitoring mempool... (Starting from block {latest_block})")

    while True:
        current_block = w3.eth.block_number

        if current_block > latest_block:
            print(f"New block detected: {current_block}")
            pending_txs = w3.eth.get_block("pending", full_transactions=True).transactions
            transaction_data = []

            for tx in pending_txs:
                try:
                    ## tracker
                    if tx.hash.hex() not in transactionCount.keys():
                        transactionCount[tx.hash.hex()] = 0
                    transactionCount[tx.hash.hex()] += 1

                    if tx.to in ROUTERS: ## DEX interaction found
                        contract = w3.eth.contract(address=tx.to, abi=abis[tx.to])
                        decoded = contract.decode_function_input(tx.input)

                        # Print the decoded function name and parameters
                        print(f"Function: {decoded[0]}")
                        print(f"Parameters: {decoded[1]}")

                        tx_data = [
                            current_block,  # Block Number
                            tx.hash.hex(),  # Transaction Hash
                            tx["from"],  # From Address
                            ROUTERS[tx.to],  # To Address
                            w3.from_wei(tx.gasPrice, 'gwei'),  # Gas Price in Gwei
                            transactionCount[tx.hash.hex()],
                            f"{decoded[0]}", ## function name
                        ]
                        params = decoded[1].items()
                        if ROUTERS[tx.to] == "uniswap_v3":
                            params = decoded[1]["params"].items()
                        for key, val in params:
                            if "0x" in str(val):
                                val = re.sub(r'0x[a-fA-F0-9]+', replaceSymbol, str(val))
                            tx_data.append(f"{key}: {val}")
                        delta = len(COLUMNS) - len(tx_data)
                        if delta > 0:
                            tx_data += ["" for _ in range(delta)]
                        transaction_data.append(tx_data)

                except Exception as e:
                    print(f"Error processing transaction {tx.hash.hex()}: {e}")

            if transaction_data:
                save_to_excel(transaction_data)

            latest_block = current_block  # Update block reference
        
        time.sleep(5)  # Poll every 5 seconds

if __name__ == "__main__":
    monitor_mempool()
