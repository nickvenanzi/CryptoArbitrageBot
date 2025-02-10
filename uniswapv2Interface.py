from web3 import Web3
import json

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

# ABI for Uniswap V2 Pair contract (just the `getReserves` function)
PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "reserve0", "type": "uint112"},
            {"name": "reserve1", "type": "uint112"},
            {"name": "blockTimestampLast", "type": "uint32"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

# Define ERC-20 contract ABI (simplified)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

UNISWAP_V2_FEE = 0.003
# Load the JSON file
with open('uniswapv2Pools.json', 'r') as file:
    data = json.load(file)

# Access the pairs data
pairs = data['pairs']

i = 0
# Loop through each pool pair and extract relevant information
for pair in pairs:
    reserve_usd = pair['reserveUSD']
    token0_symbol = pair['token0']['symbol']
    token1_symbol = pair['token1']['symbol']
    
    # Create contract instance
    pair_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['id']), abi=PAIR_ABI)

    # Create ERC-20 contract instances for token0 and token1
    token0_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['token0']['id']), abi=ERC20_ABI)
    token1_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['token1']['id']), abi=ERC20_ABI)

    # Get decimals for token0 and token1
    token0_decimals = token0_contract.functions.decimals().call()
    token1_decimals = token1_contract.functions.decimals().call()

    # Get reserves from the pair contract
    reserve0, reserve1, _ = pair_contract.functions.getReserves().call()

    # Trade size (amount of token0 being traded)
    amount_input = 10000000  # Example: 10,000 token0
    inputMinusFee = amount_input * (1.0 - UNISWAP_V2_FEE)
    
    # Calculate current price (token1 per token0)
    current_price = reserve1 / reserve0

    # Calculate amount of token1 received in the trade
    # Use the Uniswap constant product formula: x * y = k
    amount_output = (inputMinusFee * reserve1) / (reserve0 + amount_input)

    # New reserves after the trade
    new_reserve0 = reserve0 + amount_input
    new_reserve1 = reserve1 - amount_output

    # Calculate new price after the trade
    new_price = new_reserve1 / new_reserve0

    # Calculate price slippage as percentage difference
    slippage = ((amount_output / amount_input) - current_price) / current_price * 100

    # calculate readable price
    real_price = new_price * 10**(token0_decimals - token1_decimals)
    # Print the extracted information
    print(f"Reserve USD: {reserve_usd}")
    print(f"Token 0: {token0_symbol}, reserves: {reserve0}")
    print(f"Token 1: {token1_symbol}, reserves: {reserve1}")
    print(f"Current price: {current_price}")
    print(f"My price: {amount_output / amount_input}")
    print(f"New price: {new_price}")
    print(f"Price slippage: {slippage}%")
    print(f"Real price: {real_price} {token1_symbol} per {token0_symbol}")
    print(f"            {1/real_price} {token0_symbol} per {token1_symbol}")

    print('-' * 40)
    i+=1
    if i > 2:
        break