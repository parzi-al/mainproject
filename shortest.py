import json
import math

# Heuristic function (Euclidean distance)
def heuristic(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

# A* algorithm for shortest path
def a_star(graph, start, end, unsafe_segments):
    open_set = set([start])
    came_from = {}
    g_score = {node: float('inf') for node in graph['nodes']}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph['nodes']}
    f_score[start] = heuristic(graph['nodes'][start]['coords'], graph['nodes'][end]['coords'])

    while open_set:
        current = min(open_set, key=lambda node: f_score[node])

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1], g_score[end]

        open_set.remove(current)
        for neighbor, distance in graph['nodes'][current]['connections'].items():
            if (current, neighbor) in unsafe_segments or (neighbor, current) in unsafe_segments:
                continue
            tentative_g_score = g_score[current] + distance
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(graph['nodes'][neighbor]['coords'], graph['nodes'][end]['coords'])
                if neighbor not in open_set:
                    open_set.add(neighbor)

    return None, None

# Determine user location using device coordinates and distances
def determine_location(devices, distances, graph):
    min_error = float('inf')
    best_room = None

    for room, room_data in graph['nodes'].items():
        total_error = 0

        for device, device_coords in devices.items():
            room_coords = room_data['coords']

            # Calculated distance and user input
            actual_distance = heuristic(device_coords, room_coords)
            user_distance = distances.get(device, float('inf'))

            # Accumulate error
            total_error += abs(user_distance - actual_distance)

        # Find room with minimum error
        if total_error < min_error:
            min_error = total_error
            best_room = room

    return best_room

def main():
    # Updated JSON for the building layout (accurate coordinates)
    graph = {
        "nodes": {
            "Entrance": {"coords": [0, 0], "connections": {"Verandah": 2.5}},
            "Verandah": {"coords": [2.5, 0], "connections": {"Entrance": 2.5, "Living Room": 2.5, "Stair Hall": 3.5}},
            "Living Room": {"coords": [6.5, 1.0], "connections": {"Verandah": 2.5, "Dining Space": 3.0, "Toilet2": 1.5}},
            "Stair Hall": {"coords": [2.5, 3.5], "connections": {"Verandah": 3.5, "Dining Space": 3.0}},
            "Dining Space": {"coords": [5.5, 4.0], "connections": {"Living Room": 3.0, "Stair Hall": 3.0, "Kitchen": 2.5, "Master Bedroom": 3.0, "Bedroom": 3.0}},
            "Kitchen": {"coords": [8.0, 7.0], "connections": {"Dining Space": 2.5}},
            "Toilet2": {"coords": [6.5, 2.5], "connections": {"Living Room": 1.5}},
            "Bedroom": {"coords": [8.5, 9.0], "connections": {"Balcony2": 1.0, "Dining Space": 3.0}},
            "Master Bedroom": {"coords": [2.5, 7.0], "connections": {"Dining Space": 3.0, "Toilet": 1.5, "Balcony1": 1.0}},
            "Toilet": {"coords": [1.0, 7.0], "connections": {"Master Bedroom": 1.5}},
            "Balcony1": {"coords": [1.0, 9.0], "connections": {"Master Bedroom": 1.0}},
            "Balcony2": {"coords": [9.0, 10.0], "connections": {"Bedroom": 1.0}}
        }
    }

    # Explicit device coordinates
    devices = {
        "Device1": [8.5, 9.0],  # Device1 in Bedroom
        "Device2": [5.5, 4.0],  # Device2 in Dining Space
        "Device3": [6.5, 1.0]   # Device3 in Living Room
    }

    # Input distances from the user
    distances = {}
    print("Enter distances to devices (in meters):")
    for device in devices.keys():
        while True:
            try:
                distance = float(input(f"  - Distance to {device}: "))
                distances[device] = distance
                break
            except ValueError:
                print("Please enter a valid number.")

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
