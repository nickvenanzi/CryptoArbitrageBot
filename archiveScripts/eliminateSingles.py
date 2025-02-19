import json
from web3 import Web3
# Connect to Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

with open('edges.json', 'r') as file:
    data = json.load(file)

# Access the pools data
pool_data = data.get("edges", [])

with open('prices.json', 'r') as file:
    prices = json.load(file)

with open('TVLs.json', 'r') as file:
    tvls = json.load(file)

addressCheck = {}

for pool in pool_data:
    address0 = pool["token0"]["id"]
    address1 = pool["token1"]["id"]
    pool_id = pool["id"]

    if address0 not in prices.keys() or address1 not in prices.keys():
        continue  # no price data

    if tvls[pool_id] < 100.0:
        continue # not enough liquidity to have useful arbitrage
    
    if address0 not in addressCheck.keys():
        addressCheck[address0] = 0
    if address1 not in addressCheck.keys():
        addressCheck[address1] = 0
    
    addressCheck[address0] += 1
    addressCheck[address1] += 1

# Specify the filename
filename = "./newestEdges.json"

new_data = {
    "edges": []
}

print(len(pool_data))
for pool in pool_data:
    address0 = pool["token0"]["id"]
    address1 = pool["token1"]["id"]
    pool_id = pool["id"]

    if address0 not in addressCheck.keys():
        continue
    if address1 not in addressCheck.keys():
        continue

    if tvls[pool_id] < 100.0:
        continue # not enough liquidity to have useful arbitrage

    if addressCheck[address0] < 2 or addressCheck[address1] < 2:
        continue  ## no arbitrage when there's one path

    new_data["edges"].append(pool)

print(len(new_data["edges"]))
# Write data to the JSON file
with open(filename, "w") as file:
    json.dump(new_data, file, indent=4)

