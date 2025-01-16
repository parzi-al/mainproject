import json
import heapq
import math
from signaldistance import estimate_distance  # Import distance estimation function

# A* algorithm implementation
def a_star(graph, start, goal, unsafe_segments):
    open_set = [(0, start)]
    came_from = {}
    g_score = {node: float('inf') for node in graph['nodes']}
    f_score = {node: float('inf') for node in graph['nodes']}
    g_score[start] = 0
    f_score[start] = heuristic(graph['nodes'][start]['coords'], graph['nodes'][goal]['coords'])

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current), g_score[goal]

        for neighbor, distance in graph['nodes'][current]['connections'].items():
            if (current, neighbor) in unsafe_segments or (neighbor, current) in unsafe_segments:
                continue

            tentative_g_score = g_score[current] + distance
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(graph['nodes'][neighbor]['coords'], graph['nodes'][goal]['coords'])
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, float('inf')

# Heuristic function for A* (Euclidean distance)
def heuristic(coord1, coord2):
    return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2) ** 0.5

# Reconstruct the path from start to goal
def reconstruct_path(came_from, current):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.append(current)
    return path[::-1]

# Function to determine the user's location using trilateration
def determine_location(devices, distances, graph):
    min_distance = float('inf')
    nearest_room = None

    # Find the nearest room based on minimum distance
    for room, data in graph['nodes'].items():
        total_distance = sum(abs(distances[device] - heuristic(data['coords'], graph['nodes'][devices[device]]['coords']))
                             for device in distances)
        if total_distance < min_distance:
            min_distance = total_distance
            nearest_room = room

    return nearest_room

# Function to filter valid devices and calculate distances
def process_devices(wifi_data, graph):
    valid_devices = {}
    distances = {}

    for device in wifi_data:
        ssid = device.get('name', 'Unknown SSID')
        signal_strength = device.get('signalStrength', None)

        if ssid in graph['nodes'] and isinstance(signal_strength, (int, float)):
            distance, _, _ = estimate_distance(signal_strength)
            valid_devices[ssid] = graph['nodes'][ssid]['coords']
            distances[ssid] = distance

    return valid_devices, distances

# Main function
def main():
    # Input JSON for the building layout
    graph = json.loads('''{
        "nodes": {
            "Entrance": {"coords": [0, 0], "connections": {"Verandah": 2.5}},
            "Verandah": {"coords": [2.5, 0], "connections": {"Entrance": 2.5, "Living Room": 5.0, "Stair Hall": 3.5}},
            "Living Room": {"coords": [7.5, 0], "connections": {"Verandah": 5.0, "Dining Space": 3.0, "Toilet2": 1.5}},
            "Stair Hall": {"coords": [2.5, 3.5], "connections": {"Verandah": 3.5, "Dining Space": 3.0}},
            "Dining Space": {"coords": [5.5, 3.5], "connections": {"Living Room": 3.0, "Stair Hall": 3.0, "Kitchen": 2.5, "Master Bedroom": 3.0, "Bedroom": 3.0}},
            "Kitchen": {"coords": [8.0, 7.0], "connections": {"Dining Space": 2.5}},
            "Toilet2": {"coords": [8.0, 8.5], "connections": {"Living Room": 1.5}},
            "Bedroom": {"coords": [8.0, 10.0], "connections": {"Balcony2": 1.0, "Dining Space": 3.0}},
            "Master Bedroom": {"coords": [2.5, 7.0], "connections": {"Dining Space": 3.0, "Toilet": 1.5, "Balcony1": 1.0}},
            "Toilet": {"coords": [1.0, 7.0], "connections": {"Master Bedroom": 1.5}},
            "Balcony1": {"coords": [1.0, 9.0], "connections": {"Master Bedroom": 1.0}},
            "Balcony2": {"coords": [9.0, 10.0], "connections": {"Bedroom": 1.0}}
        }
    }''')

    # Sample Wi-Fi data input
    wifi_data = [
        {"name": "MITS_STAFF", "signalStrength": -50},
        {"name": "Placement_Cell", "signalStrength": -40},
        {"name": "Unknown_SSID", "signalStrength": -70}
    ]

    # Process valid devices
    devices, distances = process_devices(wifi_data, graph)

    # Determine the user's location
    user_location = determine_location(devices, distances, graph)
    print(f"User is located in: {user_location}")

    # Compute the shortest path to the Entrance
    unsafe_segments = set()
    start_node = user_location
    end_node = "Entrance"

    path, distance = a_star(graph, start_node, end_node, unsafe_segments)
    if path:
        print(f"Shortest safe path from {start_node} to {end_node}: {' -> '.join(path)}")
        print(f"Total distance: {distance:.2f} meters")
    else:
        print("No safe path found!")

if __name__ == "__main__":
    main()
