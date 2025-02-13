from web3 import Web3
import json

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

POOL_ABI = [
  {
    "constant": True,
    "inputs": [],
    "name": "getPoolTokens",
    "outputs": [
      {
        "name": "tokens",
        "type": "address[]"
      },
      {
        "name": "balances",
        "type": "uint256[]"
      },
      {
        "name": "lastChangeBlock",
        "type": "uint256"
      }
    ],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
  }
]

VAULT_ABI = [
    {
        "inputs":[
            {"internalType":"bytes32","name":"poolId","type":"bytes32"}
        ],
        "name":"getPoolTokens",
        "outputs":[
            {"internalType":"address[]","name":"tokens","type":"address[]"},
            {"internalType":"uint256[]","name":"balances","type":"uint256[]"},
            {"internalType":"uint256","name":"lastChangeBlock","type":"uint256"}
        ],
        "stateMutability":"view",
        "type":"function"
    }
]

VAULT_ADDRESS = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"

vault_contract = web3.eth.contract(address=VAULT_ADDRESS, abi=VAULT_ABI)

# Load the JSON file
with open('balancerv2Pools.json', 'r') as file:
    data = json.load(file)

# Access the pairs data
pools = data['pools']

# Loop through each pool pair and extract relevant information
for pool in pools:
    pool_id = pool['id']
    swap_fee = float(pool['swapFee'])
    
    # Extract token data
    tokens = pool['tokens']
    addresses = [token["address"] for token in tokens]
    weights = [float(token['weight']) for token in tokens]
    symbols = [token["symbol"] for token in tokens]
    decimals = [token["decimals"] for token in tokens]

    try:
        # Initialize the contract
        tokens, balances, _ = vault_contract.functions.getPoolTokens(pool_id).call()
    except:
        continue
    # Trade size (amount of token0 being traded)
    amount_input = 100000.0  # Example: 100,000 token0
    inputMinusFee = amount_input * (1.0 - swap_fee)
    
    # Calculate current price (token1 per token0)
    spot_price = (balances[1] * weights[0]) / (balances[0] * weights[1])

    # Calculate amount of token1 received in the trade
    # Use the Uniswap constant product formula: x * y = k
    amount_output = float(balances[1]) * (1.0 - (float(balances[0])/(float(balances[0]) + inputMinusFee))**(weights[0]/weights[1]))
    # New reserves after the trade
    new_reserve0 = balances[0] + amount_input
    new_reserve1 = balances[1] - amount_output

    # Calculate new price after the trade
    new_price = (new_reserve1 * weights[0]) / (new_reserve0 * weights[1])

    # Calculate price slippage as percentage difference
    slippage = ((amount_output / amount_input) - spot_price) / spot_price * 100

    # calculate readable price
    real_price = new_price * 10**(decimals[0] - decimals[1])
    # Print the extracted information
    print(f"Reserve USD: {pool["totalLiquidity"]}")
    print(f"Swap fee: {swap_fee*100}%")
    for i in range(len(addresses)):
        print(f"Token {i}: {symbols[i]}, address: {addresses[i]}, weight: {weights[i]}, decimals: {decimals[i]}")
    print()
    for j in range(len(tokens)):
        print(f"Token {j}: {tokens[j]}, balance: {balances[j]}")

    print(f"Current price: {spot_price}")
    print(f"My price: {amount_output / amount_input}")
    print(f"New price: {new_price}")
    print(f"Price slippage: {slippage}%")
    print(f"Real price: {real_price} {symbols[1]} per {symbols[0]}")
    print(f"            {1/real_price} {symbols[0]} per {symbols[1]}")

    print('-' * 40)
