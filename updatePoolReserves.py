import json
from web3 import Web3

# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

with open('edges.json', 'r') as file:
    data = json.load(file)

# Access the pools data
pool_data = data.get("pools", [])

# Loop through each v2 pool pair and extract relevant information
for pool in pool_data:
    pool_id = pool["id"]
    dex = pool["dex"]
    fee = pool["fee"]

    token0 = pool["token0"]
    token1 = pool["token1"]

    if dex == "UNISWAP_V3":
        ##call uniswap v3 price function
        pass
    elif dex == "UNISWAP_V2":
        ## call uniswap v2 price function
        pass
    elif dex == "SUSHISWAP":
        ## call sushiswap price function
        pass
    elif dex == "BALANCER":
        ## call balancer price function
        pass
    