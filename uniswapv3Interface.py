from web3 import Web3
import json

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

# Uniswap V3 Pool ABI (Minimal ABI for price fetching)
POOL_ABI = [
    {"constant": True, "inputs": [], "name": "slot0", "outputs": [
        {"name": "sqrtPriceX96", "type": "uint160"},
        {"name": "tick", "type": "int24"},
        {"name": "observationIndex", "type": "uint16"},
        {"name": "observationCardinality", "type": "uint16"},
        {"name": "observationCardinalityNext", "type": "uint16"},
        {"name": "feeProtocol", "type": "uint8"},
        {"name": "unlocked", "type": "bool"}
    ], "payable": False, "stateMutability": "view", "type": "function"}
]

# # Uniswap V3 QuoterV2 ABI (Minimal for quoteExactInputSingle)
QUOTER_V2_ABI = [
    {
        "inputs":[
            {"components":[
                {"internalType":"address","name":"tokenIn","type":"address"},
                {"internalType":"address","name":"tokenOut","type":"address"},
                {"internalType":"uint256","name":"amountIn","type":"uint256"},
                {"internalType":"uint24","name":"fee","type":"uint24"},
                {"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}
                ],
            "internalType":"struct IQuoterV2.QuoteExactInputSingleParams",
            "name":"params",
            "type":"tuple"
            }
        ],
        "name":"quoteExactInputSingle",
        "outputs":[
            {"internalType":"uint256","name":"amountOut","type":"uint256"},
            {"internalType":"uint160","name":"sqrtPriceX96After","type":"uint160"},
            {"internalType":"uint32","name":"initializedTicksCrossed","type":"uint32"},
            {"internalType":"uint256","name":"gasEstimate","type":"uint256"}
            ],
        "stateMutability":"nonpayable","type":"function"
    },
]

QUOTER_ABI = [
    {
    "inputs": [
      { "internalType": "address", "name": "tokenIn", "type": "address" },
      { "internalType": "address", "name": "tokenOut", "type": "address" },
      { "internalType": "uint24", "name": "fee", "type": "uint24" },
      { "internalType": "uint256", "name": "amountIn", "type": "uint256" },
      { "internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160" }
    ],
    "name": "quoteExactInputSingle",
    "outputs": [
      { "internalType": "uint256", "name": "amountOut", "type": "uint256" }
    ],
    "stateMutability": "nonpayable",
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

# Uniswap V3 QuoterV2 address (Mainnet)
QUOTER_ADDRESS = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
QUOTER_V2_ADDRESS = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"
USDC_ADDRESS = Web3.to_checksum_address("0xA0b86991c6218B36c1d19D4A2e9Eb0Ce3606eb48") #reference
WETH_ADDRESS = Web3.to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2") #reference
USDT_ADDRESS = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7") #reference
# Initialize the Quoter contract
quoter_contract = web3.eth.contract(address=QUOTER_V2_ADDRESS, abi=QUOTER_V2_ABI)
quoter_v1_contract = web3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)
# Function to fetch current price for each pool
def get_current_price(pool_id):
    pool_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_id), abi=POOL_ABI)
    slot0 = pool_contract.functions.slot0().call()
    
    # Extract the sqrtPriceX96 value
    sqrt_price_x96 = slot0[0]

    # Calculate the price
    return (sqrt_price_x96 ** 2) / (2 ** 192)  # Price formula from sqrtPriceX96

# Function to parse Uniswap pool data
def parse_uniswap_pools(json_data):
    pools = json_data.get("pools", [])

    # Get rough $$ amount for input token
    dollars = 100
    dollarsInWei = dollars * 1_000_000
    ethAmount = get_uniswap_v3_quote(USDC_ADDRESS, WETH_ADDRESS, 500, dollarsInWei)

    for pool in pools:
        pool_id = pool["id"]
        fee_tier = int(pool["feeTier"])
        volume_usd = float(pool["volumeUSD"])
        tx_count = int(pool["txCount"])

        token0 = pool["token0"]
        token1 = pool["token1"]

        # Get current price from the pool contract
        current_price = get_current_price(pool_id) * 10**(int(token0['decimals']) - int(token1['decimals']))

        #get token0, token1 checksum address
        token0Address = Web3.to_checksum_address(token0["id"])
        token1Address = Web3.to_checksum_address(token1["id"])

        if pool["liquidity"] == "0":
            continue
        if token0["symbol"] == "WETH":
            token0Amount = ethAmount
        elif token1["symbol"] == "WETH":
            token0Amount = int(ethAmount / current_price)
        elif token0["symbol"] == "USDC" or token0["symbol"] == "USDT":
            token0Amount = dollarsInWei
        elif token1["symbol"] == "USDC" or token1["symbol"] == "USDT":
            token0Amount = int(dollarsInWei / current_price)
        else:
            try:
                token0Amount = get_uniswap_v3_quote(WETH_ADDRESS, token0Address, 3000, ethAmount)
            except:
                try:
                    tmp = get_uniswap_v3_quote(WETH_ADDRESS, token1Address, 3000, ethAmount)
                    token0Amount = int(tmp / current_price)
                except:
                    continue

        # Get slippage price based on trade volume
        try:
            token1Amount = get_uniswap_v3_quote(token0Address, token1Address, fee_tier, token0Amount)
        except Exception as e:
            print("issue")
            continue

        slippagePrice = (float(token1Amount)/float(token0Amount)) * 10**(int(token0['decimals']) - int(token1['decimals']))  
        # print(f"Pool ID: {pool_id}")
        # print(f"  Fee Tier: {(fee_tier / 1e6) * 100:.2f}%")
        # print(f"  Trade Volume (USD): ${volume_usd:,.2f}")
        # print(f"  Transactions Count: {tx_count}")
        # print(f"  Token 0: {token0['symbol']} ({token0['name']}) - Decimals: {token0['decimals']}")
        # print(f"  Token 1: {token1['symbol']} ({token1['name']}) - Decimals: {token1['decimals']}")
        # print(f"  Current Price: {current_price:.10f} {token1['symbol']} per {token0['symbol']}")
        # print(f"                 {(1/current_price):.10f} {token0['symbol']} per {token1['symbol']}")
        # print(f"${dollars} trade slippage:")
        # print(f"               : {slippagePrice:.10f} {token1['symbol']} per {token0['symbol']}")
        # print(f"     % slippage: {(current_price - slippagePrice)/current_price*100}%")
        # print("-" * 60)

def get_uniswap_v3_quote(token_in, token_out, fee_tier, amount_in):
    """
    Get a swap quote from Uniswap V3 using the QuoterV2 contract.
    
    Args:
        token_in (str): Address of input token.
        token_out (str): Address of output token.
        fee_tier (int): Fee tier (500, 3000, 10000 for 0.05%, 0.3%, 1%).
        amount_in (int): Amount of input token (in smallest unit, e.g., wei for ETH).
    
    Returns:
        int: Estimated output amount of token_out.
    """
    params = {
            'tokenIn': token_in,
            'tokenOut': token_out,
            'amountIn': amount_in,
            'fee': fee_tier,
            'sqrtPriceLimitX96': 0
        }
    # Call quoteExactInputSingle to get the estimated output amount
    return quoter_contract.functions.quoteExactInputSingle(params).call()[0]

# Read JSON data from file
def read_json_from_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# Path to your JSON file
json_file_path = "./archivePoolData/uniswapv3Pools.json"  # Replace with the path to your JSON file

# Read and parse the JSON data
json_data = read_json_from_file(json_file_path)
# # Call the function
parse_uniswap_pools(json_data)

# # Load the JSON file
# with open('uniswapv2Pools.json', 'r') as file:
#     data = json.load(file)

# # Access the pairs data
# pairs = data['pairs']

# symbolsToPairs = {}

# # Loop through each v2 pool pair and extract relevant information
# for pair in pairs:
#     token0_symbol = pair['token0']['symbol']
#     token1_symbol = pair['token1']['symbol']
#     if token0_symbol not in symbolsToPairs.keys():
#         symbolsToPairs[token0_symbol] = 0
#     symbolsToPairs[token0_symbol] += 1

#     if token1_symbol not in symbolsToPairs.keys():
#         symbolsToPairs[token1_symbol] = 0
#     symbolsToPairs[token1_symbol] += 1

# # Loop through each v3 pool pair and extract relevant information
# pools = json_data.get("pools", [])
# for pool in pools:
#     token0 = pool["token0"]
#     token1 = pool["token1"]

#     if token0["symbol"] not in symbolsToPairs.keys():
#         symbolsToPairs[token0["symbol"]] = 0
#     symbolsToPairs[token0["symbol"]] += 1

#     if token1["symbol"] not in symbolsToPairs.keys():
#         symbolsToPairs[token1["symbol"]] = 0
#     symbolsToPairs[token1["symbol"]] += 1

# # Load the JSON file
# with open('sushiswapv2Pools.json', 'r') as file:
#     sushi_data = json.load(file)
# # Loop through each sushiswap pool pair and extract relevant information
# sushi_pools = sushi_data.get("pools", [])
# for pool in sushi_pools:
#     token0 = pool["token0"]
#     token1 = pool["token1"]

#     if token0["symbol"] not in symbolsToPairs.keys():
#         symbolsToPairs[token0["symbol"]] = 0
#     symbolsToPairs[token0["symbol"]] += 1

#     if token1["symbol"] not in symbolsToPairs.keys():
#         symbolsToPairs[token1["symbol"]] = 0
#     symbolsToPairs[token1["symbol"]] += 1

# # Load the JSON file
# with open('balancerv2Pools.json', 'r') as file:
#     bal_data = json.load(file)
# # Loop through each sushiswap pool pair and extract relevant information
# bal_pools = bal_data.get("pools", [])
# for pool in bal_pools:    
#     # Extract token data
#     tokens = pool['tokens']
#     symbols = [token["symbol"] for token in tokens]

#     for symbol in symbols:   
#         if symbol not in symbolsToPairs.keys():
#             symbolsToPairs[symbol] = 0
#         symbolsToPairs[symbol] += 1

# new_data = {
#     "edges": []
# }

# ## NOW GO THROUGH AND ADD TO NEW CONSOLIDATED FILE

# # Read and parse the JSON data
# uniswapv3_data = read_json_from_file("uniswapv3Pools.json")
# uniswapv2_data = read_json_from_file("uniswapv2Pools.json")
# sushiswapv2_data = read_json_from_file("sushiswapv2Pools.json")
# balancer_data = read_json_from_file("balancerv2Pools.json")

# # Access the pools data
# uniswapv3_pools = uniswapv3_data.get("pools", [])
# uniswapv2_pools = uniswapv2_data['pairs']
# sushiswap_pools = sushiswapv2_data.get("pools", [])
# balancer_pools = balancer_data.get("pools", [])

# # Loop through each v2 pool pair and extract relevant information
# for pair in uniswapv2_pools:
#     token0_symbol = pair['token0']['symbol']
#     token1_symbol = pair['token1']['symbol']
#     if symbolsToPairs[token0_symbol] < 2 or symbolsToPairs[token1_symbol] < 2:
#         continue
    
#     # Create ERC-20 contract instances for token0 and token1
#     token0_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['token0']['id']), abi=ERC20_ABI)
#     token1_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['token1']['id']), abi=ERC20_ABI)

#     # Get decimals for token0 and token1
#     token0_decimals = token0_contract.functions.decimals().call()
#     token1_decimals = token1_contract.functions.decimals().call()
#     new_data["edges"].append({
#         "id": pair["id"],
#         "token0": {
#             "id": pair['token0']['id'],
#             "symbol": token0_symbol,
#             "decimals": token0_decimals
#         },
#         "token1": {
#             "id": pair['token1']['id'],
#             "symbol": token1_symbol,
#             "decimals": token1_decimals
#         },
#         "dex": "UNISWAP_V2",
#         "fee": 0.003,
#     })

# # Loop through each v3 pool pair and extract relevant information
# for pool in uniswapv3_pools:
#     token0 = pool["token0"]
#     token1 = pool["token1"]

#     token0_symbol = token0["symbol"]
#     token1_symbol = token1["symbol"]

#     if symbolsToPairs[token0_symbol] < 2 or symbolsToPairs[token1_symbol] < 2:
#         continue

#     token0_decimals = int(token0["decimals"])
#     token1_decimals = int(token1["decimals"])

#     fee = int(pool["feeTier"])/1000000.0

#     new_data["edges"].append({
#         "id": pool["id"],
#         "token0": {
#             "id": token0['id'],
#             "symbol": token0_symbol,
#             "decimals": token0_decimals
#         },
#         "token1": {
#             "id": token1['id'],
#             "symbol": token1_symbol,
#             "decimals": token1_decimals
#         },
#         "dex": "UNISWAP_V3",
#         "fee": fee,
#     })

# for pool in sushiswap_pools:
#     token0_symbol = pool['token0']['symbol']
#     token1_symbol = pool['token1']['symbol']
#     if symbolsToPairs[token0_symbol] < 2 or symbolsToPairs[token1_symbol] < 2:
#         continue

#     # Get decimals for token0 and token1
#     token0_decimals = pool["token0"]["decimals"]
#     token1_decimals = pool["token1"]["decimals"]

#     new_data["edges"].append({
#         "id": pool["id"],
#         "token0": {
#             "id": pool['token0']['id'],
#             "symbol": token0_symbol,
#             "decimals": token0_decimals
#         },
#         "token1": {
#             "id": pool['token1']['id'],
#             "symbol": token1_symbol,
#             "decimals": token1_decimals
#         },
#         "dex": "SUSHISWAP",
#         "fee": 0.003,
#     })

# for pool in balancer_pools:    
#     pool_id = pool['id']
#     swap_fee = float(pool["swapFee"])

#     # Extract token data
#     tokens = pool['tokens']
#     addresses = [token["address"] for token in tokens]
#     weights = [float(token['weight']) for token in tokens]
#     symbols = [token["symbol"] for token in tokens]
#     decimals = [token["decimals"] for token in tokens]

#     for start in range(len(tokens)-1): ## 0, 1, 2
#         for end in range(start+1, len(tokens)): ## 1, 2, 3
#             token0_symbol = symbols[start]
#             token1_symbol = symbols[end]
#             if symbolsToPairs[token0_symbol] < 2 or symbolsToPairs[token1_symbol] < 2:
#                 continue

#             token0_decimals = decimals[start]
#             token1_decimals = decimals[end]

#             token0_address = addresses[start]
#             token1_address = addresses[end]

#             token0_weight = weights[start]
#             token1_weight = weights[end]

#             new_data["edges"].append({
#                 "id": pool_id,
#                 "token0": {
#                     "id": token0_address,
#                     "symbol": token0_symbol,
#                     "decimals": token0_decimals,
#                     "weight": token0_weight
#                 },
#                 "token1": {
#                     "id": token1_address,
#                     "symbol": token1_symbol,
#                     "decimals": token1_decimals,
#                     "weight": token1_weight
#                 },
#                 "dex": "BALANCER",
#                 "fee": swap_fee,
#             })

# # Specify the filename
# filename = "./edges.json"

# # Write data to the JSON file
# with open(filename, "w") as file:
#     json.dump(new_data, file, indent=4)

