from web3 import Web3
import json

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

# SushiSwap V2 Pair Contract ABI (Only needed functions)
PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "reserve0", "type": "uint112"},
        {"name": "reserve1", "type": "uint112"},
        {"name": "blockTimestampLast", "type": "uint32"}
    ], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [
        {"name": "", "type": "address"}
    ], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [
        {"name": "", "type": "address"}
    ], "payable": False, "stateMutability": "view", "type": "function"}
]

TOKEN_ABI = [
    {
        "constant": True, 
        "inputs": [], 
        "name": "decimals", 
        "outputs": [{"name": "", "type": "uint8"}], 
        "payable": False, 
        "stateMutability": "view", 
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Load the JSON file
with open('sushiswapv2Pools.json', 'r') as file:
    data = json.load(file)

new_data = {
    "pools": []
}

# Access the pairs data
pools = data['pools']

i = 0
# Loop through each pool pair and extract relevant information
for pool in pools:
    pool_id = pool['id']
    try:
        # Instantiate the contract
        pool_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_id), abi=PAIR_ABI)

        # Fetch reserves
        reserve0, reserve1, _ = pool_contract.functions.getReserves().call()

        # Fetch token addresses
        token0_addr = pool_contract.functions.token0().call()
        token1_addr = pool_contract.functions.token1().call()

        token0_contract = web3.eth.contract(address=token0_addr, abi=TOKEN_ABI)
        token1_contract = web3.eth.contract(address=token1_addr, abi=TOKEN_ABI)

        # Fetch token addresses
        token0_sym = token0_contract.functions.symbol().call()
        token1_sym = token1_contract.functions.symbol().call()

        # Instantiate token contracts
        token0_contract = web3.eth.contract(address=token0_addr, abi=TOKEN_ABI)
        token1_contract = web3.eth.contract(address=token1_addr, abi=TOKEN_ABI)

        # Fetch token decimals
        decimals0 = token0_contract.functions.decimals().call()
        decimals1 = token1_contract.functions.decimals().call()
    except:
        continue
    # Normalize reserves to get proper token prices
    adjusted_reserve0 = reserve0 / (10 ** decimals0)
    adjusted_reserve1 = reserve1 / (10 ** decimals1)

    # Compute token prices
    token0_price = adjusted_reserve1 / adjusted_reserve0
    token1_price = adjusted_reserve0 / adjusted_reserve1

    if token0_sym == "WETH":
        tvl = 2 * adjusted_reserve0 * 2611
    elif token1_sym == "WETH":
        tvl = 2 * adjusted_reserve1 * 2611
    elif token0_sym == "USDC" or token0_sym == "USDT":
        tvl = 2 * adjusted_reserve0
    elif token1_sym == "USDC" or token1_sym == "USDT":
        tvl = 2 * adjusted_reserve1
    else:
        continue

    if tvl > 100000:
        new_data["pools"].append({
            "id": pool_id,
            "token0": {
                "id": token0_addr,
                "symbol": token0_sym,
                "decimals": decimals0
            },
            "token1": {
                "id": token1_addr,
                "symbol": token1_sym,
                "decimals": decimals1
            }
        })
    print(f"Token0 Address: {token0_addr}")
    print(f"Token1 Address: {token1_addr}")
    print(f"Reserve0: {adjusted_reserve0}")
    print(f"Reserve1: {adjusted_reserve1}")
    print(f"Price of {token0_sym} in terms of {token1_sym}: {token0_price}")
    print(f"Price of {token1_sym} in terms of {token0_sym}: {token1_price}")
    print(f"Total Volume USD: {tvl}\n")

# Specify the filename
filename = "./output.json"

# Write data to the JSON file
with open(filename, "w") as file:
    json.dump(new_data, file, indent=4)

