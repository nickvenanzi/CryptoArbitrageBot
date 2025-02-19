import json
from web3 import Web3
# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

################# UNISWAP_V3 CONTRACT CODE ####################
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
QUOTER_V2_ADDRESS = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"
quoter_contract = web3.eth.contract(address=QUOTER_V2_ADDRESS, abi=QUOTER_V2_ABI)
def get_uniswap_v3_quote(token_in, token_out, fee_tier, amount_in):
    params = {'tokenIn': token_in,'tokenOut': token_out,'amountIn': amount_in,'fee': fee_tier,'sqrtPriceLimitX96': 0}
    # Call quoteExactInputSingle to get the estimated output amount
    return quoter_contract.functions.quoteExactInputSingle(params).call()[0]
################# UNISWAP_V3 CONTRACT CODE ####################

################# UNISWAP_V2 CONTRACT CODE ####################
UNISWAP_V2_PAIR_ABI = [
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
################# UNISWAP_V2 CONTRACT CODE ####################

################# SUSHISWAP CONTRACT CODE ####################
SUSHISWAP_PAIR_ABI = [
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
################# SUSHISWAP CONTRACT CODE ####################

################# BALANCER CONTRACT CODE ####################
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
################# BALANCER CONTRACT CODE ####################

USDC_ADDRESS = Web3.to_checksum_address("0xA0b86991c6218B36c1d19D4A2e9Eb0Ce3606eb48") #reference
WETH_ADDRESS = Web3.to_checksum_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2") #reference
USDT_ADDRESS = Web3.to_checksum_address("0xdac17f958d2ee523a2206206994597c13d831ec7") #reference
DAI_ADDRESS = Web3.to_checksum_address("0x6b175474e89094c44da98b954eedeac495271d0f") #reference

references = set(["USDC", "USDT", "DAI", "WETH"])

usdAmount = 100 * 10**6
daiAmount = usdAmount * 10**(18-6)
ethAmount = get_uniswap_v3_quote(USDC_ADDRESS, WETH_ADDRESS, 500, usdAmount)

prices = {
    USDC_ADDRESS: 1.0,
    USDT_ADDRESS: 1.0,
    DAI_ADDRESS: 1.0,
    WETH_ADDRESS: usdAmount/ethAmount * 10.0**(18-6)
}

symbols = {
    USDC_ADDRESS: "USDC",
    USDT_ADDRESS: "USDT",
    DAI_ADDRESS: "DAI",
    WETH_ADDRESS: "WETH"
}

with open('edges.json', 'r') as file:
    data = json.load(file)

# Access the pools data
pool_data = data.get("edges", [])

queue = [i for i in range(len(pool_data))]
# Loop through each v2 pool pair and extract relevant information
iterations = 0
while len(queue) > 0:
    iterations += 1
    if iterations % 100 == 0:
        print(len(queue))
    i = queue.pop(0)
    pool = pool_data[i]
    pool_id = pool["id"]
    dex = pool["dex"]
    fee = pool["fee"]

    token0 = pool["token0"]
    token1 = pool["token1"]

    address0 = Web3.to_checksum_address(token0["id"])
    address1 = Web3.to_checksum_address(token1["id"])

    if address0 not in symbols.keys():
        symbols[address0] = token0["symbol"]

    if address1 not in symbols.keys():
        symbols[address1] = token1["symbol"]

    if address0 in prices.keys() and address1 in prices.keys():
        continue
    elif address0 not in prices.keys() and address1 not in prices.keys():
        queue.append(i)
        continue

    if address0 in prices.keys():
        ## use token0 as reference for token1
        startSymbol = symbols[address0]
        endSymbol = symbols[address1]

        startDecimals = token0["decimals"]
        endDecimals = token1["decimals"]

        startAddress = address0
        endAddress = address1
    else:
        ## use token1 as reference for token0
        startSymbol = symbols[address1]
        endSymbol = symbols[address0]

        startDecimals = token1["decimals"]
        endDecimals = token0["decimals"]

        startAddress = address1
        endAddress = address0

    dollarsPerT0 = prices[startAddress] ## $ per 1 startToken

    if dex == "UNISWAP_V3":
        dollars = 10.0
        amountIn = int(dollars * 10**startDecimals / prices[startAddress]) # $ / ($/t0) = t0
        params = {'tokenIn': startAddress,'tokenOut': endAddress,'amountIn': amountIn,'fee': round(fee*1000000),'sqrtPriceLimitX96': 0}
        try:
            amountOut = quoter_contract.functions.quoteExactInputSingle(params).call()[0]
            price = amountOut / amountIn
        except:
            continue
        T1perT0 = float(price) * 10.0**(startDecimals - endDecimals)
    elif dex == "UNISWAP_V2":
        pair_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_id), abi=UNISWAP_V2_PAIR_ABI)
        reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
        spot_price = reserve1 / reserve0 if startAddress == address0 else reserve0 / reserve1
        T1perT0 = spot_price * 10**(startDecimals - endDecimals)
    elif dex == "SUSHISWAP":
        pool_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_id), abi=SUSHISWAP_PAIR_ABI)
        reserve0, reserve1, _ = pool_contract.functions.getReserves().call()
        spot_price = reserve1 / reserve0 if startAddress == address0 else reserve0 / reserve1
        T1perT0 = spot_price * 10**(startDecimals - endDecimals)
    elif dex == "BALANCER":
        tokens, balances, _ = vault_contract.functions.getPoolTokens(pool_id).call()
        for index, token in enumerate(tokens):
            if token == startAddress:
                startBalance = balances[index]
            if token == endAddress:
                endBalance = balances[index]
        if address0 == startAddress:
            startWeight = token0["weight"]
            endWeight = token1["weight"]
        else:
            startWeight = token1["weight"]
            endWeight = token0["weight"]
        T1perT0 = (endBalance * startWeight) / (startBalance * endWeight) * 10**(startDecimals - endDecimals)
    if T1perT0 < 1e-15:
        print(f"Divide by zero: {pool_id}")
        continue
    prices[endAddress] = dollarsPerT0 / T1perT0 ## ($/t0) / (t1/t0) = ($/t1)

# Specify the filename
filename = "./prices.json"

# Write data to the JSON file
with open(filename, "w") as file:
    json.dump(prices, file, indent=4)