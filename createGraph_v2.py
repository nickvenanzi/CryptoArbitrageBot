import json
from web3 import Web3
import math
import time

start_time = time.time()
# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

with open('prices.json', 'r') as file:
    prices = json.load(file)

with open('edges.json', 'r') as file:
    data = json.load(file)

# Access the pools data
edge_data = data.get("edges", [])

volume_usd = 100

gas_used = 150_000  
gas_price_wei = web3.eth.gas_price  

# Calculate gas cost in ETH and USD
gas_cost_eth = gas_used * gas_price_wei / 10**18  # Convert WEI to ETH
gas_cost_usd = gas_cost_eth * prices["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"]  # Convert to USD
print(f"Gas per swap ~${gas_cost_usd:.2f}")
edges = []
vertices = set()

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
def get_uniswap_v3_weight(pool, result_fwd, result_bwd):
    token0 = pool["token0"]
    token1 = pool["token1"]

    token0["price"] = prices[token0["id"]]
    token1["price"] = prices[token1["id"]]

    amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
    amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

    amount_out_fwd = result_fwd[0]
    amount_out_bwd = result_bwd[0]

    if amount_out_fwd < 0.5:
        print(f"{amount_out_fwd} tokens outputted for pool: {pool["id"]}")
        return
    if amount_out_bwd < 0.5:
        print(f"{amount_out_bwd} tokens outputted for pool: {pool["id"]}")
        return
    
    price_fwd = amount_out_fwd / amount_in_fwd
    price_bwd = amount_out_bwd / amount_in_bwd
    weight_fwd = -math.log10(price_fwd)
    weight_bwd = -math.log10(price_bwd)

    edges.append({
        "start": token0,
        "end": token1,
        "weight": weight_fwd,
        "dex": pool["dex"],
        "fee": pool["fee"]
    })
    edges.append({
        "start": token1,
        "end": token0,
        "weight": weight_bwd,
        "dex": pool["dex"],
        "fee": pool["fee"]
    })
    if token0["id"] not in vertices:
        vertices.add(token0["id"])
    if token1["id"] not in vertices:
        vertices.add(token1["id"])
        
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
def get_uniswap_v2_weight(pair, result):
    reserve0, reserve1, _ = result

    token0 = pair["token0"]
    token1 = pair["token1"]

    amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
    amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

    gas_in_fwd = int(gas_cost_usd * 10**token0["decimals"] / prices[token0["id"]])
    gas_in_bwd = int(gas_cost_usd * 10**token1["decimals"] / prices[token1["id"]])

    amount_in_fwd_w_fee = amount_in_fwd * (1.0 - UNISWAP_V2_FEE) - gas_in_fwd
    amount_in_bwd_w_fee = amount_in_bwd * (1.0 - UNISWAP_V2_FEE) - gas_in_bwd

    amount_output_fwd = (amount_in_fwd_w_fee * reserve1) / (reserve0 + amount_in_fwd)
    amount_output_bwd = (amount_in_bwd_w_fee * reserve0) / (reserve1 + amount_in_bwd)

    price_fwd = amount_output_fwd / amount_in_fwd
    price_bwd = amount_output_bwd / amount_in_bwd

    weight_fwd = -math.log10(price_fwd)
    weight_bwd = -math.log10(price_bwd)

    token0["reserve"] = reserve0
    token1["reserve"] = reserve1

    token0["price"] = prices[token0["id"]]
    token1["price"] = prices[token1["id"]]

    edges.append({
        "start": token0,
        "end": token1,
        "weight": weight_fwd,
        "dex": pair["dex"],
        "fee": pair["fee"]
    })
    edges.append({
        "start": token1,
        "end": token0,
        "weight": weight_bwd,
        "dex": pair["dex"],
        "fee": pair["fee"]
    })
    if token0["id"] not in vertices:
        vertices.add(token0["id"])
    if token1["id"] not in vertices:
        vertices.add(token1["id"])
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
def get_sushiswap_weight(pair, result):
    reserve0, reserve1, _ = result

    token0 = pair["token0"]
    token1 = pair["token1"]

    amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
    amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

    gas_in_fwd = int(gas_cost_usd * 10**token0["decimals"] / prices[token0["id"]])
    gas_in_bwd = int(gas_cost_usd * 10**token1["decimals"] / prices[token1["id"]])

    amount_in_fwd_w_fee = amount_in_fwd * (1.0 - UNISWAP_V2_FEE) - gas_in_fwd
    amount_in_bwd_w_fee = amount_in_bwd * (1.0 - UNISWAP_V2_FEE) - gas_in_bwd

    amount_output_fwd = (amount_in_fwd_w_fee * reserve1) / (reserve0 + amount_in_fwd)
    amount_output_bwd = (amount_in_bwd_w_fee * reserve0) / (reserve1 + amount_in_bwd)

    price_fwd = amount_output_fwd / amount_in_fwd
    price_bwd = amount_output_bwd / amount_in_bwd

    weight_fwd = -math.log10(price_fwd)
    weight_bwd = -math.log10(price_bwd)

    token0["reserve"] = reserve0
    token1["reserve"] = reserve1

    token0["price"] = prices[token0["id"]]
    token1["price"] = prices[token1["id"]]

    edges.append({
        "start": token0,
        "end": token1,
        "weight": weight_fwd,
        "dex": pair["dex"],
        "fee": pair["fee"]
    })
    edges.append({
        "start": token1,
        "end": token0,
        "weight": weight_bwd,
        "dex": pair["dex"],
        "fee": pair["fee"]
    })
    if token0["id"] not in vertices:
        vertices.add(token0["id"])
    if token1["id"] not in vertices:
        vertices.add(token1["id"])
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
def get_balancer_weight(pool, result):
    token0 = edge["token0"]
    token1 = edge["token1"]
    tokens, balances, _ = result

    for index, token in enumerate(tokens):
        if token == token0["id"]:
            reserve0 = balances[index]
        if token == token1["id"]:
            reserve1 = balances[index]

    amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
    amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t0) = t0

    gas_in_fwd = int(gas_cost_usd * 10**token0["decimals"] / prices[token0["id"]])
    gas_in_bwd = int(gas_cost_usd * 10**token1["decimals"] / prices[token1["id"]])

    amount_in_fwd_w_fee = amount_in_fwd * (1.0 - pool["fee"]) - gas_in_fwd
    amount_in_bwd_w_fee = amount_in_bwd * (1.0 - pool["fee"]) - gas_in_bwd

    amount_output_fwd = float(reserve1) * (1.0 - (float(reserve0)/(float(reserve0) + amount_in_fwd_w_fee))**(token0["weight"]/token1["weight"]))
    amount_output_bwd = float(reserve0) * (1.0 - (float(reserve1)/(float(reserve1) + amount_in_bwd_w_fee))**(token1["weight"]/token0["weight"]))

    price_fwd = amount_output_fwd / amount_in_fwd
    price_bwd = amount_output_bwd / amount_in_bwd

    weight_fwd = -math.log10(price_fwd)
    weight_bwd = -math.log10(price_bwd)

    token0["reserve"] = reserve0
    token1["reserve"] = reserve1

    token0["price"] = prices[token0["id"]]
    token1["price"] = prices[token1["id"]]

    edges.append({
        "start": token0,
        "end": token1,
        "weight": weight_fwd,
        "dex": pool["dex"],
        "fee": pool["fee"]
    })
    edges.append({
        "start": token1,
        "end": token0,
        "weight": weight_bwd,
        "dex": pool["dex"],
        "fee": pool["fee"]
    })
    if token0["id"] not in vertices:
        vertices.add(token0["id"])
    if token1["id"] not in vertices:
        vertices.add(token1["id"])
################# BALANCER CONTRACT CODE ####################

# Loop through each v2 pool pair and construct batch requests
counter = 0
total = 0
BATCH_SIZE = 880 ## must be less than 1000

# Prepare batch request array
batch = web3.batch_requests()
results = []
for i, edge in enumerate(edge_data):
    dex = edge["dex"]
    if dex == "UNISWAP_V3":
        token0 = edge["token0"]
        token1 = edge["token1"]
        amount_in_fwd = int((volume_usd - gas_cost_usd) * 10**token0["decimals"] / prices[token0["id"]])
        params_fwd = [token0["id"], token1["id"], amount_in_fwd, round(edge["fee"]*1000000), 0]
        batch.add(quoter_contract.functions.quoteExactInputSingle(params_fwd))
        amount_in_bwd = int((volume_usd - gas_cost_usd) * 10**token1["decimals"] / prices[token1["id"]])
        params_bwd = [token1["id"], token0["id"], amount_in_bwd, round(edge["fee"]*1000000), 0]
        batch.add(quoter_contract.functions.quoteExactInputSingle(params_bwd))
        edge_data[i]["request"] = (total, total + 1)
        counter += 1 ## duplicate adds since 2 requests made for uni_v3
        total += 1
    elif dex == "UNISWAP_V2":
        pair_contract = web3.eth.contract(address=Web3.to_checksum_address(edge['id']), abi=UNISWAP_V2_PAIR_ABI)
        batch.add(pair_contract.functions.getReserves())
        edge_data[i]["request"] = total
    elif dex == "SUSHISWAP":
        pair_contract = web3.eth.contract(address=Web3.to_checksum_address(edge['id']), abi=SUSHISWAP_PAIR_ABI)
        batch.add(pair_contract.functions.getReserves())
        edge_data[i]["request"] = total
    elif dex == "BALANCER":
        batch.add(vault_contract.functions.getPoolTokens(edge["id"]))
        edge_data[i]["request"] = total
    counter += 1
    total += 1
    if counter >= BATCH_SIZE:
        try:
            results += batch.execute()
        except Exception as e:
            print(e)
        batch = web3.batch_requests()
        print(f"Processed {counter} requests: {round(i / len(edge_data)*100, 2)}%")  
        counter = 0
if counter > 0:
    try:
        results += batch.execute()
    except Exception as e:
        print(e)
    batch = web3.batch_requests()
    print(f"Processed {counter} requests: {round(i / len(edge_data)*100, 2)}%")  
    counter = 0

for i, edge in enumerate(edge_data):
    dex = edge["dex"]
    resultIndex = edge["request"]
    if dex == "UNISWAP_V3":
        fwd, bwd = resultIndex
        get_uniswap_v3_weight(edge, results[fwd], results[bwd])
    elif dex == "UNISWAP_V2":
        get_uniswap_v2_weight(edge, results[resultIndex])
    elif dex == "SUSHISWAP":
        get_sushiswap_weight(edge, results[resultIndex])
    elif dex == "BALANCER":
        get_balancer_weight(edge, results[resultIndex])
 
    if i % 100 == 0:
        print(f"{round(i / len(edge_data)*100, 2)}%")

# Specify the filename
filename = "./graph.json"

graph = {
    "volume": volume_usd,
    "edges": edges,
    "vertices": list(vertices)
}
# Write data to the JSON file
with open(filename, "w") as file:
    json.dump(graph, file, indent=4)

end_time = time.time()
elapsed_time = end_time - start_time

print(f"Execution time: {elapsed_time:.6f} seconds")