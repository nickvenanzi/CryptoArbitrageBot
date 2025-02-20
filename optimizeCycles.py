import json
from web3 import Web3
import math

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

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
def get_uniswap_v3_weight(edge, amount_in):
    token0 = edge["start"]
    token1 = edge["end"]
    try:  ## forward calculation
        params_fwd = {'tokenIn': token0["id"],'tokenOut': token1["id"],'amountIn': int(amount_in),'fee': round(edge["fee"]*1000000),'sqrtPriceLimitX96': 0}
        amount_out = quoter_contract.functions.quoteExactInputSingle(params_fwd).call()[0]
        return amount_out
    except:
        return -1
################# UNISWAP_V3 CONTRACT CODE ####################

################# UNISWAP_V2 CONTRACT CODE ####################
def get_uniswap_v2_weight(edge, amount_in):
    token0 = edge["start"]
    token1 = edge["end"]
    amount_in_w_fee = amount_in * (1.0 - edge["fee"])
    amount_output = (amount_in_w_fee * token1["reserve"]) / (token0["reserve"] + amount_in)
    return amount_output
################# UNISWAP_V2 CONTRACT CODE ####################

################# SUSHISWAP CONTRACT CODE ####################
def get_sushiswap_weight(edge, amount_in):    
    token0 = edge["start"]
    token1 = edge["end"]
    amount_in_w_fee = amount_in * (1.0 - edge["fee"])
    amount_output = (amount_in_w_fee * token1["reserve"]) / (token0["reserve"] + amount_in)
    return amount_output
################# SUSHISWAP CONTRACT CODE ####################

################# BALANCER CONTRACT CODE ####################
def get_balancer_weight(edge, amount_in):
    token0 = edge["start"]
    token1 = edge["end"]
    amount_in_w_fee = amount_in * (1.0 - edge["fee"])
    amount_output = float(token1["reserve"]) * (1.0 - (float(token0["reserve"])/(float(token0["reserve"]) + amount_in_w_fee))**(token0["weight"]/token1["weight"]))
    return amount_output
################# BALANCER CONTRACT CODE ####################

def computeProfit(path, start_volume):
    startNode = path[0]["start"]
    amount_in = int(start_volume * 10**startNode["decimals"] / startNode["price"]) # $ / ($/t0) = t0

    for edge in path:
        dex = edge["dex"]
        if dex == "UNISWAP_V3":
            amount_in = get_uniswap_v3_weight(edge, amount_in)
            if amount_in < 0:
                return -1
        elif dex == "UNISWAP_V2":
            amount_in = get_uniswap_v2_weight(edge, amount_in)
        elif dex == "SUSHISWAP":
            amount_in = get_sushiswap_weight(edge, amount_in)
        elif dex == "BALANCER":
            amount_in = get_balancer_weight(edge, amount_in)
    end_volume = amount_in * startNode["price"] / 10**startNode["decimals"]
    return end_volume - start_volume


def optimize(path):
    previous_volume = 0.0
    current_volume = 10.0

    previous_profit = 0
    current_profit = 0

    alpha = 10
    for i in range(10):
        previous_profit = current_profit
        current_profit = computeProfit(path, current_volume)
        grad = (current_profit - previous_profit)#/(current_volume - previous_volume)  # Approximate gradient using finite difference
        tmp = current_volume + alpha * grad  # Update x
        # tmp = max(tmp, 1)
        previous_volume = current_volume
        current_volume = tmp
        print(f"{i}: Volume: {previous_volume}, Profit: ${current_profit}")
        # if current_volume == 1:
        #     previous_volume = 0 ## direct the algorithm to go up from 1
    return previous_volume, current_profit

def ternarySearch(path):
    min_val = 1.0
    max_val = 100.0
    while min_val + 0.1 < max_val:
        m = (min_val + max_val)/2
        left_profit = computeProfit(path, m - 1)
        mid_profit = computeProfit(path, m)
        right_profit = computeProfit(path, m + 1)
        print(f"(min={round(min_val, 1)},max={round(max_val, 1)}): ({m}) -> (${round(mid_profit, 2)})")
        if right_profit > mid_profit: ## move right
            min_val = m + 1
        elif left_profit > mid_profit: ## move left
            max_val = m - 1
        else:
            return m, mid_profit
    return m, mid_profit

with open('cycles.json', 'r') as file:
    cycles_data = json.load(file)

# Access the pools data
cycles = cycles_data.get("cycles", [])

for i, cycle in enumerate(cycles):
    path = cycle["edgePath"]
    volume, profit = ternarySearch(path)
    cycles[i]["volume"] = volume
    cycles[i]["optimized_profit"] = profit
    print(f"{"-"*40}")

# Specify the filename
filename = f"./cyclesOptimized.json"

# Write data to the JSON file
with open(filename, "w") as file:
    json.dump({"cycles": cycles}, file, indent=4)
