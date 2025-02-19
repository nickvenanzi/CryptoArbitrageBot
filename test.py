import json

with open('graph.json', 'r') as file:
    data = json.load(file)

# Access the pools data
pool_data = data.get("500", [])
edges = pool_data["edges"]

print(edges[3055])
print(edges[650])
print(edges[2062])
