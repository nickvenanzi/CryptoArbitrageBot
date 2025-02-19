import math
import json

def findArbitrage(edges, vertices):
    cycles = []
    distance = {}
    nodePath = {}
    edgePath = {}
    count = 0
    for startNode in vertices:
        count += 1
        if count % 10 == 0:
            print(f"{round(count / len(vertices)*100, 2)}% done iterations")
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

volumes_usd = graph.get("volumes", [])

for volume in volumes_usd:
    edges = graph[f"{volume}"]["edges"]
    vertices = graph[f"{volume}"]["vertices"]
    cycles = findArbitrage(edges, vertices)

    # Specify the filename
    filename = f"./cycles/{volume}.json"

    # Write data to the JSON file
    with open(filename, "w") as file:
        json.dump({"cycles": cycles}, file, indent=4)

