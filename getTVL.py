import json
from web3 import Web3
# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

################# UNISWAP_V3 CONTRACT CODE ####################
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]
POOL_ABI = [
    {"constant": True, "inputs": [], "name": "slot0", "outputs": [
        {"name": "sqrtPriceX96", "type": "uint160"},
        {"name": "tick", "type": "int24"},
        {"name": "observationIndex", "type": "uint16"},
        {"name": "observationCardinality", "type": "uint16"},
        {"name": "observationCardinalityNext", "type": "uint16"},
        {"name": "feeProtocol", "type": "uint8"},
        {"name": "unlocked", "type": "bool"}
    ], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "liquidity", "outputs": [
        {"name": "liquidity", "type": "uint128"}
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

with open('edges.json', 'r') as file:
    data = json.load(file)

with open('prices.json', 'r') as file:
    prices = json.load(file)

# Access the pools data
pool_data = data.get("edges", [])

tvl_data = {}

for pool in pool_data:
    address0 = pool["token0"]["id"]
    address1 = pool["token1"]["id"]

    pool_id = pool["id"]
    dex = pool["dex"]

    try:
        price0 = prices[address0]
    except:
        print(f"No price for {address0} ({pool["token0"]["symbol"]})")
        price0 = 0.0
    try:
        price1 = prices[address1]
    except:
        print(f"No price for {address1} ({pool["token1"]["symbol"]})")
        price1 = 0.0

    if dex == "UNISWAP_V3":
        token0_contract = web3.eth.contract(address=address0, abi=ERC20_ABI)
        token1_contract = web3.eth.contract(address=address1, abi=ERC20_ABI)

        balance0 = token0_contract.functions.balanceOf(Web3.to_checksum_address(pool_id)).call()
        balance1 = token1_contract.functions.balanceOf(Web3.to_checksum_address(pool_id)).call()

        reserve0 = balance0 / 10.0**pool["token0"]["decimals"]
        reserve1 = balance1 / 10.0**pool["token1"]["decimals"]
        tvl = price0*reserve0 + price1*reserve1
    elif dex == "UNISWAP_V2":
        pair_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_id), abi=UNISWAP_V2_PAIR_ABI)
        reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
        tvl = price0*(reserve0/10.0**pool["token0"]["decimals"]) + price1*(reserve1/10.0**pool["token1"]["decimals"])
    elif dex == "SUSHISWAP":
        pool_contract = web3.eth.contract(address=Web3.to_checksum_address(pool_id), abi=SUSHISWAP_PAIR_ABI)
        reserve0, reserve1, _ = pool_contract.functions.getReserves().call()
        tvl = price0*(reserve0/10.0**pool["token0"]["decimals"]) + price1*(reserve1/10.0**pool["token1"]["decimals"])
    elif dex == "BALANCER":
        tokens, balances, _ = vault_contract.functions.getPoolTokens(pool_id).call()
        for index, token in enumerate(tokens):
            if token == address0:
                reserve0 = balances[index]
            if token == address1:
                reserve1 = balances[index]
        tvl = price0*(reserve0/10.0**pool["token0"]["decimals"]) + price1*(reserve1/10.0**pool["token1"]["decimals"])

    tvl_data[pool_id] = tvl

# Write data to the JSON file
with open("./TVLs.json", "w") as file:
    json.dump(tvl_data, file, indent=4)
