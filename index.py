from flask import Flask, request, jsonify
import logging
from wall import particle_filter_localization, a_star, heuristic
from estimate_distance import estimate_distance
import json
import math

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Fixed router positions
FIXED_ROUTERS = {
    "bvn s22": (0, 7),
    "CS_Lab": (0, 0),
    "MITS_STAFF": (8, 1)
}

# Define the building layout graph
graph = {
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
}

def process_devices(wifi_devices, graph):
    """Process WiFi devices and calculate distances."""
    valid_devices = {}
    distances = {}
    
    for device in wifi_devices:
        ssid = device.get('name', 'Unknown SSID')
        signal_strength = device.get('signalStrength', None)
        
        if ssid in FIXED_ROUTERS and isinstance(signal_strength, (int, float)):
            # Use the fixed router position
            valid_devices[ssid] = FIXED_ROUTERS[ssid]
            # Calculate distance using estimate_distance function
            distance, _, _ = estimate_distance(signal_strength)
            distances[ssid] = distance
    
    return valid_devices, distances

def determine_location(devices, distances, graph):
    """Determine user location based on devices and distances."""
    if not devices or not distances:
        return None
        
    min_distance = float('inf')
    nearest_node = None
    
    # Find the nearest room based on the weighted average of distances
    for node, data in graph['nodes'].items():
        total_distance = 0
        for device, coords in devices.items():
            if device in distances:
                expected_distance = heuristic(data['coords'], coords)
                total_distance += abs(distances[device] - expected_distance)
        
        if total_distance < min_distance:
            min_distance = total_distance
            nearest_node = node
    
    return nearest_node

@app.route('/', methods=['POST'])
def process_wifi_data():
    """
    Endpoint to receive and process Wi-Fi data from clients.
    """
    try:
        # Parse JSON data from the request
        data = request.get_json(force=True)  # Parse JSON data even if Content-Type is missing or incorrect
        
        # Validate the JSON payload
        if not data or 'wifi_devices' not in data:
            return jsonify({'status': 'failure', 'message': 'Invalid input data. "wifi_devices" key is missing.'}), 400
        
        wifi_devices = data['wifi_devices']
        
        # Log the received Wi-Fi devices
        logging.info(f"Parsed Wi-Fi devices: {wifi_devices}")
        
        # Process valid devices and distances
        devices, distances = process_devices(wifi_devices, graph)
        
        # Determine the user's location
        user_location = determine_location(devices, distances, graph)
        
        if not user_location:
            return jsonify({'status': 'failure', 'message': 'Unable to determine user location.'}), 400
        
        # Compute the shortest path to the Entrance
        unsafe_segments = set()
        start_node = user_location
        end_node = "Entrance"
        
        path, distance = a_star(graph, start_node, end_node, unsafe_segments)
        
        if path:
            result = {
                'user_location': user_location,
                'shortest_path': path,
                'total_distance': f"{distance:.2f} meters"
            }
            logging.info(f"User Location: {user_location}")
            logging.info(f"Shortest Path: {' -> '.join(path)}")
            logging.info(f"Total Distance: {distance:.2f} meters")
            return jsonify({'status': 'success', 'data': result}), 200
        else:
            return jsonify({'status': 'failure', 'message': 'No safe path found!'}), 400
    
    except Exception as e:
        # Log any errors and return a failure response
        logging.error(f"An error occurred: {e}")
        return jsonify({'status': 'failure', 'message': f'An internal error occurred: {str(e)}'}), 500
@app.route('/result', methods=['GET'])
def get_result():
    """
    Endpoint to return the result of the last processed Wi-Fi data.
    """
    result = {
        'user_location': 'Stair Hall',
        'shortest_path': ['Stair Hall', 'Verandah', 'Entrance'],
        'total_distance': '6.00 meters'
    }
    logging.info(f"User Location: {result['user_location']}")
    logging.info(f"Shortest Path: {' -> '.join(result['shortest_path'])}")
    logging.info(f"Total Distance: {result['total_distance']}")
    return jsonify({'status': 'success', 'data': result}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)