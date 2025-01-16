import json
import heapq
import math
from signaldistance import estimate_distance  # Import distance estimation function
import numpy as np

# Existing A* algorithm and helpers
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

def heuristic(coord1, coord2):
    return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2) ** 0.5

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
def find_closest_node(user_location, graph):
    """Find the closest graph node to the given user location."""
    min_distance = float('inf')
    closest_node = None
    for node, data in graph['nodes'].items():
        distance = heuristic(user_location, data['coords'])
        if distance < min_distance:
            min_distance = distance
            closest_node = node
    return closest_node

def estimate_user_location(device_locs, distances):
    points = []
    radii = []
    for device, location in device_locs.items():
        if device in distances:
            points.append(location)
            radii.append(distances[device])
    if len(points) < 3:
        raise ValueError("At least three points are required for trilateration.")
    A = []
    B = []
    for i in range(1, len(points)):
        x1, y1 = points[0]
        x2, y2 = points[i]
        r1, r2 = radii[0], radii[i]
        A.append([2 * (x2 - x1), 2 * (y2 - y1)])
        B.append(r1**2 - r2**2 - x1**2 - y1**2 + x2**2 + y2**2)
    A = np.array(A)
    B = np.array(B)
    estimated_position = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(estimated_position)

def main():
    # Floor plan device locations
    device_locations = {
        "Device 1": (8.0, 10.0),  # Bedroom
        "Device 2": (2.5, 7.0),   # Master Bedroom
        "Device 3": (5.5, 3.5),   # Dining Hall
        "Device 4": (7.5, 0.0)    # Living Room
    }

    # Workflow output distances
    device_distances = {
        "Device 1": 14.83,
        "Device 2": 43.36,
        "Device 3": 48.33,
        "Device 4": 48.33
    }

    # Estimate user location
    user_location = estimate_user_location(device_locations, device_distances)
    print(f"Estimated user location: {user_location}")

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
    json_input = '''
    {
      "nodes": {
        "Entrance": {"coords": [0, 0], "connections": {"Verandah": 2.5}},
        "Verandah": {"coords": [2.5, 0], "connections": {"Entrance": 2.5, "Living Room": 5.0, "Stair Hall": 3.5}},
        "Living Room": {"coords": [7.5, 0], "connections": {"Verandah": 5.0, "Dining Space": 3.0}},
        "Stair Hall": {"coords": [2.5, 3.5], "connections": {"Verandah": 3.5, "Dining Space": 3.0}},
        "Dining Space": {"coords": [5.5, 3.5], "connections": {"Living Room": 3.0, "Stair Hall": 3.0, "Bedroom": 3.0, "Master Bedroom": 3.0}},
        "Bedroom": {"coords": [8.0, 10.0], "connections": {"Dining Space": 3.0}},
        "Master Bedroom": {"coords": [2.5, 7.0], "connections": {"Dining Space": 3.0}}
      }
    }
    '''

    graph = json.loads(json_input)

    # Determine the closest node
    start_node = find_closest_node(user_location, graph)
    print(f"Closest node to user location: {start_node}")

    # Define the goal node
    end_node = "Entrance"

    # Find the shortest path
    unsafe_segments = set()
    path, distance = a_star(graph, start_node, end_node, unsafe_segments)

    if path:
        print(f"Shortest path from {start_node} to {end_node}: {' -> '.join(path)}")
        print(f"Total distance: {distance:.2f} meters")
    else:
        print(f"No path found from {start_node} to {end_node}.")

if __name__ == "__main__":
    main()
