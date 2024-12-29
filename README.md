# WiFi Signal Strength Distance Estimator

This Python script scans available WiFi networks, retrieves their signal strengths (in dBm), and estimates the distances between your device and the access points based on the received signal strength (RSS). The script provides a list of all detected networks with their estimated distances and uncertainty ranges.

---

## Features

1. **WiFi Network Scanning**:
   - Retrieves available WiFi networks (SSID) and their signal strengths (RSS in dBm).
   - Supports both Windows and Linux platforms.

2. **Distance Estimation**:
   - Uses a simplified radio propagation model to estimate distance based on RSS.
   - Accounts for signal uncertainty using a confidence interval.

3. **Multi-Network Support**:
   - Scans and processes all nearby WiFi networks.

4. **Customizable Parameters**:
   - Adjustable parameters for distance estimation (e.g., reference distance, path loss exponent).

---

## Prerequisites

### Libraries Required:
- `numpy`: For numerical calculations.
- `pywifi`: For WiFi interface management.
- Standard libraries: `platform`, `subprocess`.

To install the `pywifi` library:
```bash
pip install pywifi
```
##  Shortest and Safest path using A* algorithm


This Python script implements the A* algorithm to find the shortest path between two nodes in a graph. The graph represents a building layout with nodes as rooms and edges as connections between them. The script allows dynamic checking of path safety and updates the graph to avoid unsafe segments.

---

## Features

1. **A* Pathfinding Algorithm**:
   - Calculates the shortest path from a start node to a goal node using the A* algorithm.
   - Incorporates a heuristic function based on Euclidean distance.

2. **Dynamic Path Safety Checks**:
   - Allows users to dynamically mark path segments as unsafe.
   - Updates the graph to exclude unsafe segments and recalculates the path.

3. **Building Layout Graph**:
   - Represents a building as a JSON input with nodes (rooms) and edges (connections with distances).
   - Includes coordinates for each node to support heuristic calculations.

4. **Interactive User Input**:
   - Users can verify the safety of path segments during execution.
   - Provides feedback on the availability of safe paths.

---

## Prerequisites

### Libraries Required

- `json`: For parsing and handling JSON input.
- `heapq`: For managing the priority queue in the A* algorithm.

These libraries are part of Python's standard library and do not require additional installation.

---

## How It Works
### A* Algorithm

The A* algorithm combines the actual cost from the start node to the current node (`g_score`) with an estimated cost to the goal node (`f_score`) to efficiently find the shortest path.
The A* algorithm combines the actual cost from the start node to the current node (`g_score`) with an estimated cost to the goal node (`f_score`) to efficiently find the shortest path.

**Heuristic Function**:
### Dynamic Path Safety

- Users are prompted to verify the safety of each segment in the path.
- Unsafe segments are added to a set and excluded from subsequent path calculations.
- Users are prompted to verify the safety of each segment in the path.
- Unsafe segments are added to a set and excluded from subsequent path calculations.

---
### Key Functions

#### 1. `a_star(graph, start, goal, unsafe_segments)`

- Implements the A* algorithm to find the shortest path.
- Skips segments marked as unsafe.
#### 1. `a_star(graph, start, goal, unsafe_segments)`:
- Implements the A* algorithm to find the shortest path.
- Skips segments marked as unsafe.
- **Parameters**:
  - `graph`: The building layout graph as a dictionary.
  - `start`: The start node.
  - `goal`: The goal node.
  - `unsafe_segments`: A set of unsafe segments to avoid.
#### 2. `heuristic(coord1, coord2)`

- Calculates the Euclidean distance between two coordinates.
#### 3. `reconstruct_path(came_from, current)`

- Reconstructs the path from the `came_from` dictionary.
#### 4. `check_path_safety(graph, path, unsafe_segments)`

- Prompts the user to verify the safety of each segment in the path.

#### 3. `reconstruct_path(came_from, current)`:
- Reconstructs the path from the `came_from` dictionary.

#### 4. `check_path_safety(graph, path, unsafe_segments)`:
- Prompts the user to verify the safety of each segment in the path.
- Adds unsafe segments to the `unsafe_segments` set.

---

## Input

### JSON Graph Format:
The building layout is represented as a JSON object:
```json
{
  "nodes": {
    "Entrance": {
      "coords": [0, 0],
      "connections": {"Verandah": 2.5}
    },
    "Verandah": {
      "coords": [2.5, 0],
      "connections": {"Entrance": 2.5, "Living Room": 5.0}
    }
    ...
  }
}
