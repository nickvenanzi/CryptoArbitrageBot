import math
import json
import time

start_time = time.time()
def findArbitrage(edges, vertices):
    cycles = []
    distance = {}
    nodePath = {}
    edgePath = {}
    count = 0
    for startNode in vertices:
        count += 1
        cycleDistance = math.inf ## defaul value just needs to be >= 0
        for node in vertices:
            distance[node] = math.inf
            nodePath[node] = []
            edgePath[node] = []
        distance[startNode] = 0
        
        for _ in range(len(vertices) - 1):
            updated = False
            for edgeIndex, edge in enumerate(edges):
                start = edge["start"]["id"]
                end = edge["end"]["id"]
                weight = edge["weight"]
                newDistance = distance[start] + weight
                if newDistance < distance[end] and (end == startNode or end not in nodePath[start]):
                    if end == startNode:
                        cycleEdges = edgePath[start] + [edgeIndex]
                        cycleDistance = newDistance
                    else:
                        distance[end] = newDistance
                        nodePath[end] = nodePath[start] + [start]
                        edgePath[end] = edgePath[start] + [edgeIndex]
                        updated = True
            if not updated:
                break
        if cycleDistance < 0:
            cycles.append({"edgePath": cycleEdges, "gain": 10**-cycleDistance})
    return cycles

with open('graph.json', 'r') as file:
    graph = json.load(file)

volume_usd = graph.get("volume", 0)

edges = graph["edges"]
vertices = graph["vertices"]
cycles = findArbitrage(edges, vertices)

blufs = []
for i, cycle in enumerate(cycles):
    edgeData = [edges[edgeIndex] for edgeIndex in cycle["edgePath"]]
    bluf = "->".join([f"{edge["start"]["symbol"]} ({edge["dex"]})" for edge in edgeData + [edgeData[0]]])
    blufs.append(f"{round((cycle["gain"]-1)*100, 2)}%: {bluf}")
    cycles[i]["edgePath"] = edgeData

# Specify the filename
filename = f"./cycles.json"

# Write data to the JSON file
with open(filename, "w") as file:
    json.dump({"BLUF": blufs, "cycles": cycles}, file, indent=4)

end_time = time.time()
elapsed_time = end_time - start_time

print(f"Execution time: {elapsed_time:.6f} seconds")