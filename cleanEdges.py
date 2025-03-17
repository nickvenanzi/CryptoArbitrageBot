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
new_edge_data = []
volume_usd = 100

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
    amount_in_fwd = int(volume_usd * 10**token0["decimals"] / prices[token0["id"]]) # $ / ($/t0) = t0
    amount_in_bwd = int(volume_usd * 10**token1["decimals"] / prices[token1["id"]]) # $ / ($/t1) = t1
    try:  ## forward calculation
        params_fwd = {'tokenIn': token0["id"],'tokenOut': token1["id"],'amountIn': amount_in_fwd,'fee': round(pool["fee"]*1000000),'sqrtPriceLimitX96': 0}
        quoter_contract.functions.quoteExactInputSingle(params_fwd).call()[0]
        params_bwd = {'tokenIn': token1["id"],'tokenOut': token0["id"],'amountIn': amount_in_bwd,'fee': round(pool["fee"]*1000000),'sqrtPriceLimitX96': 0}
        quoter_contract.functions.quoteExactInputSingle(params_bwd).call()[0]
    except:
        return
    new_edge_data.append(pool)
################# UNISWAP_V3 CONTRACT CODE ####################

################# UNISWAP_V2 CONTRACT CODE ####################
def get_uniswap_v2_weight(pair):
    new_edge_data.append(pair)
################# UNISWAP_V2 CONTRACT CODE ####################

################# SUSHISWAP CONTRACT CODE ####################
def get_sushiswap_weight(pair):
    new_edge_data.append(pair)
################# SUSHISWAP CONTRACT CODE ####################

################# BALANCER CONTRACT CODE ####################
def get_balancer_weight(pool):
    new_edge_data.append(pool)
################# BALANCER CONTRACT CODE ####################

# Loop through each pool pair and extract relevant information
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

addressCheck = {}

for pool in new_edge_data:
    address0 = pool["token0"]["id"]
    address1 = pool["token1"]["id"]

    if address0 not in addressCheck.keys():
        addressCheck[address0] = 0
    if address1 not in addressCheck.keys():
        addressCheck[address1] = 0
    
    addressCheck[address0] += 1
    addressCheck[address1] += 1

pruned_data = []

for pool in new_edge_data:
    address0 = pool["token0"]["id"]
    address1 = pool["token1"]["id"]
    pool_id = pool["id"]

    if address0 not in addressCheck.keys():
        continue
    if address1 not in addressCheck.keys():
        continue

    if addressCheck[address0] < 2 or addressCheck[address1] < 2:
        continue  ## no arbitrage when there's one path

    pruned_data.append(pool)

# Specify the filename
filename = "./edges.json"

# Write data to the JSON file
with open(filename, "w") as file:
    json.dump({"edges": pruned_data}, file, indent=4)

print(f"Removed {len(edge_data) - len(pruned_data)} edges")