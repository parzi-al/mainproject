import json
import heapq
import math
from signaldistance import get_wifi_networks, estimate_distance
from shortest import a_star, determine_location

def integrate_workflow(graph, known_devices):
    # Scan for WiFi networks
    networks = get_wifi_networks()
    distances = {}
    
    # Estimate distances for known devices
    for network in networks:
        ssid = network["SSID"]
        signal = network["Signal"]
        if ssid in known_devices:
            d_est, _, _ = estimate_distance(signal)
            distances[ssid] = d_est

    # Determine user's location based on WiFi distances
    user_location = determine_location(known_devices, distances, graph)
    print(f"User is located in: {user_location}")

    # Compute shortest path to Entrance
    start_node = user_location
    end_node = "Entrance"
    unsafe_segments = set()  # Add any unsafe segments if needed

    path, distance = a_star(graph, start_node, end_node, unsafe_segments)
    if path:
        print(f"Shortest safe path from {start_node} to {end_node}: {' -> '.join(path)}")
        print(f"Total distance: {distance:.2f} meters")
    else:
        print("No safe path found!")

if __name__ == "__main__":
    # Define the graph structure
    graph = {
        "nodes": {
            # (Sample data, replace with actual graph)
            "Entrance": {"coords": [0, 0], "connections": {"Verandah": 2.5}},
            # Add the rest of the graph nodes here
        }
    }

    # Define known WiFi devices and their corresponding graph nodes
    known_devices = {
        "Device1": "Bedroom",
        "Device2": "Dining Space",
        "Device3": "Kitchen"
    }

    # Run the integrated workflow
    integrate_workflow(graph, known_devices)
