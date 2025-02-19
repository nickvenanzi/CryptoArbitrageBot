import json
from web3 import Web3
import math

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

with open('prices.json', 'r') as file:
    prices = json.load(file)

with open('edges.json', 'r') as file:
    data = json.load(file)

# Access the pools data
edge_data = data.get("edges", [])

volumes_usd = [10, 50, 100, 250, 500, 1000, 10000]
edges = {}
vertices = {}
for volume in volumes_usd:
    edges[volume] = []
    vertices[volume] = set()

################# UNISWAP_V3 CONTRACT CODE ####################
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
def get_uniswap_v3_weight(pool):
    token0 = pool["token0"]
    token1 = pool["token1"]
    try:
        prices[token0["id"]]
    except:
        print(token0["id"])
        return
    try:
        prices[token1["id"]]
    except:
        print(token1["id"])
        return
    for volume_usd in volumes_usd:
        amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
        amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t1) = t1
        try:  ## forward calculation
            params_fwd = {'tokenIn': token0["id"],'tokenOut': token1["id"],'amountIn': amount_in_fwd,'fee': round(pool["fee"]*1000000),'sqrtPriceLimitX96': 0}
            amount_out_fwd = quoter_contract.functions.quoteExactInputSingle(params_fwd).call()[0]
            price_fwd = amount_out_fwd / amount_in_fwd
            weight_fwd = -math.log10(price_fwd)
            edges[volume_usd].append({
                "start": token0,
                "end": token1,
                "weight": weight_fwd
            })
            if token0["id"] not in vertices[volume_usd]:
                vertices[volume_usd].add(token0["id"])
            if token1["id"] not in vertices[volume_usd]:
                vertices[volume_usd].add(token1["id"])
        except:
            pass
        try: ## backward calculation
            params_bwd = {'tokenIn': token1["id"],'tokenOut': token0["id"],'amountIn': amount_in_bwd,'fee': round(pool["fee"]*1000000),'sqrtPriceLimitX96': 0}
            amount_out_bwd = quoter_contract.functions.quoteExactInputSingle(params_bwd).call()[0]
            price_bwd = amount_out_bwd / amount_in_bwd
            weight_bwd = -math.log10(price_bwd)
            edges[volume_usd].append({
                "start": token1,
                "end": token0,
                "weight": weight_bwd
            })
            if token0["id"] not in vertices[volume_usd]:
                vertices[volume_usd].add(token0["id"])
            if token1["id"] not in vertices[volume_usd]:
                vertices[volume_usd].add(token1["id"])
        except:
            pass
################# UNISWAP_V3 CONTRACT CODE ####################

################# UNISWAP_V2 CONTRACT CODE ####################
UNISWAP_V2_FEE = 0.003
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
def get_uniswap_v2_weight(pair):
    pair_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['id']), abi=UNISWAP_V2_PAIR_ABI)
    reserve0, reserve1, _ = pair_contract.functions.getReserves().call()

    token0 = pair["token0"]
    token1 = pair["token1"]
    for volume_usd in volumes_usd:
        amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
        amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

        amount_in_fwd_w_fee = amount_in_fwd * (1.0 - UNISWAP_V2_FEE)
        amount_in_bwd_w_fee = amount_in_bwd * (1.0 - UNISWAP_V2_FEE)

        amount_output_fwd = (amount_in_fwd_w_fee * reserve1) / (reserve0 + amount_in_fwd)
        amount_output_bwd = (amount_in_bwd_w_fee * reserve0) / (reserve1 + amount_in_bwd)

        price_fwd = amount_output_fwd / amount_in_fwd
        price_bwd = amount_output_bwd / amount_in_bwd

        weight_fwd = -math.log10(price_fwd)
        weight_bwd = -math.log10(price_bwd)

        edges[volume_usd].append({
            "start": token0,
            "end": token1,
            "weight": weight_fwd
        })
        edges[volume_usd].append({
            "start": token1,
            "end": token0,
            "weight": weight_bwd
        })
        if token0["id"] not in vertices[volume_usd]:
            vertices[volume_usd].add(token0["id"])
        if token1["id"] not in vertices[volume_usd]:
            vertices[volume_usd].add(token1["id"])
################# UNISWAP_V2 CONTRACT CODE ####################

################# SUSHISWAP CONTRACT CODE ####################
SUSHISWAP_FEE = 0.003
SUSHISWAP_PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "reserve0", "type": "uint112"},
        {"name": "reserve1", "type": "uint112"},
        {"name": "blockTimestampLast", "type": "uint32"}
    ], "payable": False, "stateMutability": "view", "type": "function"}
]
def get_sushiswap_weight(pair):
    pair_contract = web3.eth.contract(address=Web3.to_checksum_address(pair['id']), abi=SUSHISWAP_PAIR_ABI)
    reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
    
    token0 = pair["token0"]
    token1 = pair["token1"]
    for volume_usd in volumes_usd:
        amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
        amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

        amount_in_fwd_w_fee = amount_in_fwd * (1.0 - UNISWAP_V2_FEE)
        amount_in_bwd_w_fee = amount_in_bwd * (1.0 - UNISWAP_V2_FEE)

        amount_output_fwd = (amount_in_fwd_w_fee * reserve1) / (reserve0 + amount_in_fwd)
        amount_output_bwd = (amount_in_bwd_w_fee * reserve0) / (reserve1 + amount_in_bwd)

        price_fwd = amount_output_fwd / amount_in_fwd
        price_bwd = amount_output_bwd / amount_in_bwd

        weight_fwd = -math.log10(price_fwd)
        weight_bwd = -math.log10(price_bwd)

        edges[volume_usd].append({
            "start": token0,
            "end": token1,
            "weight": weight_fwd
        })
        edges[volume_usd].append({
            "start": token1,
            "end": token0,
            "weight": weight_bwd
        })
        if token0["id"] not in vertices[volume_usd]:
            vertices[volume_usd].add(token0["id"])
        if token1["id"] not in vertices[volume_usd]:
            vertices[volume_usd].add(token1["id"])
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
def get_balancer_weight(pool):
    token0 = pool["token0"]
    token1 = pool["token1"]
    tokens, balances, _ = vault_contract.functions.getPoolTokens(pool["id"]).call()
    for index, token in enumerate(tokens):
        if token == token0["id"]:
            reserve0 = balances[index]
        if token == token1["id"]:
            reserve1 = balances[index]

    for volume_usd in volumes_usd:
        amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
        amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

        amount_in_fwd_w_fee = amount_in_fwd * (1.0 - pool["fee"])
        amount_in_bwd_w_fee = amount_in_bwd * (1.0 - pool["fee"])

        amount_output_fwd = float(reserve1) * (1.0 - (float(reserve0)/(float(reserve0) + amount_in_fwd_w_fee))**(token0["weight"]/token1["weight"]))
        amount_output_bwd = float(reserve0) * (1.0 - (float(reserve1)/(float(reserve1) + amount_in_bwd_w_fee))**(token1["weight"]/token0["weight"]))

        price_fwd = amount_output_fwd / amount_in_fwd
        price_bwd = amount_output_bwd / amount_in_bwd

        weight_fwd = -math.log10(price_fwd)
        weight_bwd = -math.log10(price_bwd)

        edges[volume_usd].append({
            "start": token0,
            "end": token1,
            "weight": weight_fwd
        })
        edges[volume_usd].append({
            "start": token1,
            "end": token0,
            "weight": weight_bwd
        })
        if token0["id"] not in vertices[volume_usd]:
            vertices[volume_usd].add(token0["id"])
        if token1["id"] not in vertices[volume_usd]:
            vertices[volume_usd].add(token1["id"])
################# BALANCER CONTRACT CODE ####################

# Loop through each v2 pool pair and extract relevant information
counter = 0
for edge in edge_data:
    dex = edge["dex"]
    if dex == "UNISWAP_V3":
        get_uniswap_v3_weight(edge)
    elif dex == "UNISWAP_V2":
        get_uniswap_v2_weight(edge)
    elif dex == "SUSHISWAP":
        get_sushiswap_weight(edge)
    elif dex == "BALANCER":
        get_balancer_weight(edge)
    
    counter+=1
    if counter % 100 == 0:
        print(f"{round(counter / len(edge_data)*100, 2)}%")

# Specify the filename
filename = "./graph.json"

graph = {
    "volumes": volumes_usd
}
for volume in volumes_usd:
    graph[volume] = {
        "edges": edges[volume],
        "vertices": list(vertices[volume])
    }
# Write data to the JSON file
with open(filename, "w") as file:
    json.dump(graph, file, indent=4)

