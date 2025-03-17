from web3 import Web3
import json
# Connect to your local Ethereum node
web3 = Web3(Web3.HTTPProvider('http://10.0.0.49:8545'))

# Pool router addresses (update with actual contract addresses)
ROUTERS = {
    "uniswap_v2": Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"),  # Uniswap V2 Router
    "uniswap_v3": Web3.to_checksum_address("0xe592427a0aece92de3edee1f18e0157c05861564"),  # Uniswap V3 Router
    "sushiswap_v2": Web3.to_checksum_address("0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f"),  # Sushiswap V2 Router
    "balancer": Web3.to_checksum_address("0xBA12222222228d8Ba445958a75a0704d566BF2C8"),  # Balancer Vault
}

# ABI snippets for swap functions
UNISWAP_V2_ABI = [
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "path", "type": "address[]"},
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "uint256[]"}],
    }
]
UNISWAP_V3_ABI = [
    {
        "name": "exactInputSingle",
        "type": "function",
        "inputs": [
            {
                "name": "params",
                "type": "tuple",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
            }
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    }
]
BALANCER_ABI = [
    {
        "name": "swap",
        "type": "function",
        "inputs": [
            {
                "name": "singleSwap",
                "type": "tuple",
                "components": [
                    {"name": "poolId", "type": "bytes32"},
                    {"name": "kind", "type": "uint8"},
                    {"name": "assetIn", "type": "address"},
                    {"name": "assetOut", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "userData", "type": "bytes"},
                ],
            },
            {
                "name": "funds",
                "type": "tuple",
                "components": [
                    {"name": "sender", "type": "address"},
                    {"name": "recipient", "type": "address"},
                    {"name": "fromInternalBalance", "type": "bool"},
                    {"name": "toInternalBalance", "type": "bool"},
                ],
            },
            {"name": "limit", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
        "outputs": [{"name": "amountOut", "type": "uint256"}],
    }
]

TOKEN_ABI = [{
  "constant": False,
  "inputs": [
    {"name": "_spender","type": "address"},
    {"name": "_value","type": "uint256"}
  ],
  "name": "approve",
  "outputs": [
    {"name": "","type": "bool"}
  ],
  "payable": False,
  "stateMutability": "nonpayable",
  "type": "function"
}]

# Example usage
account = "0xebcbc40F25643F8430e1575882987aC2D2D96034"

amount_in = int(0.01 * 1e18) ## 0.01 WETH

router_address = ROUTERS.get("uniswap_v2")
# contract = web3.eth.contract(address=router_address, abi=UNISWAP_V2_ABI)

token_in = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
token_out = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

# path = [token_in, token_out]
# amount_out = contract.functions.swapExactTokensForTokens(
#     amount_in, 0, path, account, deadline
# ).call()
# amount_in = amount_out[-1]
# print(f"Simulated swap: {Web3.fromWei(amount_in, 'ether')} {token_out}")

with open("./private_key.json", 'r') as file:
    data = json.load(file)
    
# Extract the private key
private_key = data.get('key')

# Create contract instances
router_contract = web3.eth.contract(address=router_address, abi=UNISWAP_V2_ABI)
token_in_contract = web3.eth.contract(address=token_in, abi=TOKEN_ABI)

latest_block = web3.eth.get_block('latest')
deadline = latest_block["timestamp"] + 600
base_fee_per_gas = latest_block['baseFeePerGas']
buffer = 1 * 10**9  # 1 Gwei buffer
max_fee_per_gas = base_fee_per_gas + buffer

# # Approve the Uniswap Router to spend your WETH
# approve_txn = token_in_contract.functions.approve(
#     router_address,
#     amount_in
# ).build_transaction({
#     'from': account,
#     'nonce': web3.eth.get_transaction_count(account),
#     'gas': 100000,
#     'gasPrice': max_fee_per_gas
# })

# # Sign and send the approval transaction
# signed_approve_txn = web3.eth.account.sign_transaction(approve_txn, private_key=private_key)
# approve_txn_hash = web3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
# web3.eth.wait_for_transaction_receipt(approve_txn_hash)
# print(f"Approval transaction hash: {approve_txn_hash.hex()}")

# Define the swap path
path = [token_in, token_out]

# Build the swap transaction
swap_txn = router_contract.functions.swapExactTokensForTokens(
    amount_in,
    0,
    path,
    account,
    deadline
).call({'from': account})

print(f"Output: {swap_txn}")

print(ROUTERS)
