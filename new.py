from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import logging
import math
from wall import particle_filter_localization, a_star, heuristic
from estimate_distance import estimate_distance


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable WebSockets

logging.basicConfig(level=logging.INFO)

latest_results = {}
active_exits = {
    "Entrance": [],
    "Balcony1": [],
    "Balcony2": []
}

EXIT_CAPACITY = {
    "Entrance": 10,
    "Balcony1": 15,
    "Balcony2": 8
}

# Fixed router positions (ensure these keys match the WiFi device names provided by your Flutter app)
FIXED_ROUTERS = {
    "CS_Lab": (4, 11),
    "bvn s22": (1, 8),
    "MITS_STAFF": (8, 5)
}

# Define the building layout graph
graph = {
    "nodes": {
        "Entrance": {"coords": [0, 0], "connections": {"Verandah": 2.5}},
        "Verandah": {"coords": [2.5, 0], "connections": {"Entrance": 2.5, "Living Room": 5.0, "Stair Hall": 4.5}},
        "Living Room": {"coords": [7.5, 0], "connections": {"Verandah": 5.0, "Dining Space": 3.0, "Toilet2": 1.5}},
        "Stair Hall": {"coords": [8.5, 3.5], "connections": {"Verandah": 3.5, "Dining Space": 3.0}},
        "Dining Space": {"coords": [5.5, 3.5], "connections": {"Living Room": 3.0, "Stair Hall": 9.0, "Kitchen": 2.5, "Master Bedroom": 3.0, "Bedroom": 3.0}},
        "Kitchen": {"coords": [8.0, 7.0], "connections": {"Dining Space": 2.5}},
        "Toilet2": {"coords": [8.0, 8.5], "connections": {"Living Room": 1.5}},
        "Bedroom": {"coords": [8.0, 10.0], "connections": {"Balcony2": 1.0, "Dining Space": 3.0}},
        "Master Bedroom": {"coords": [2.5, 7.0], "connections": {"Dining Space": 3.0, "Toilet": 1.5, "Balcony1": 1.0}},
        "Toilet": {"coords": [1.0, 7.0], "connections": {"Master Bedroom": 1.5}},
        "Balcony1": {"coords": [1.0, 9.0], "connections": {"Master Bedroom": 1.0}},
        "Balcony2": {"coords": [9.0, 10.0], "connections": {"Bedroom": 1.0}}
    }
}

def send_update():
    socketio.emit("update", {
        "devices": list(latest_results.values()),
        "exits": active_exits
    })

def find_nearest_available_exit(user_node):
    # Get exits sorted by distance from the user
    exit_distances = {
        exit: math.sqrt((graph['nodes'][exit]['coords'][0] - graph['nodes'][user_node]['coords'][0])**2 +
                        (graph['nodes'][exit]['coords'][1] - graph['nodes'][user_node]['coords'][1])**2)
        for exit in active_exits.keys()
    }
    
    sorted_exits = sorted(exit_distances.items(), key=lambda x: x[1])  # Sort exits by distance
    
    for exit, _ in sorted_exits:
        if len(active_exits[exit]) < EXIT_CAPACITY[exit]:  # Check if the exit is free
            return exit
    
    return None  # No exit available

def calculate_signal_strength_weight(signal_strength):
    """Convert signal strength (dBm) to a weight value."""
    # Normalize signal strength to a 0-1 scale (-100 dBm -> 0, -50 dBm -> 1)
    normalized = (signal_strength + 100) / 50
    return max(0, min(1, normalized))

def process_devices(wifi_devices):
    valid_devices = {}
    distances = {}
    weights = {}
    
    logging.info("Processing WiFi devices:")
    for device in wifi_devices:
        ssid = device.get('name', 'Unknown SSID')
        signal_strength = device.get('signalStrength', None)
        
        if ssid in FIXED_ROUTERS and isinstance(signal_strength, (int, float)):
            valid_devices[ssid] = FIXED_ROUTERS[ssid]
            distance, confidence, _ = estimate_distance(signal_strength)
            weight = calculate_signal_strength_weight(signal_strength)
            
            distances[ssid] = distance
            weights[ssid] = weight
            
            logging.info(f"Router: {ssid}")
            logging.info(f"  Position: {FIXED_ROUTERS[ssid]}")
            logging.info(f"  Signal Strength: {signal_strength} dBm")
            logging.info(f"  Estimated Distance: {distance:.2f} meters")
            logging.info(f"  Weight: {weight:.4f}")
    
    return valid_devices, distances, weights

def triangulate_position(devices, distances, weights):
    if not devices or not distances:
        return None
    
    total_weight_x = 0.0
    total_weight_y = 0.0
    total_weights = 0.0
    
    logging.info("\nTriangulation Calculation:")
    for device, coords in devices.items():
        distance = distances.get(device, 0)
        weight = weights.get(device, 0)
        
        if distance <= 0 or weight <= 0:
            continue
            
        # Calculate weighted contribution
        weighted_x = coords[0] * weight
        weighted_y = coords[1] * weight
        
        total_weight_x += weighted_x
        total_weight_y += weighted_y
        total_weights += weight
        
        logging.info(f"Router: {device}")
        logging.info(f"  Contribution X: {weighted_x:.2f}")
        logging.info(f"  Contribution Y: {weighted_y:.2f}") 
    
    if total_weights == 0:
        return None
    
    estimated_x = total_weight_x / total_weights
    estimated_y = total_weight_y / total_weights
    
    logging.info(f"\nFinal Position:")
    logging.info(f"  X: {estimated_x:.2f}")
    logging.info(f"  Y: {estimated_y:.2f}")
    
    return (estimated_x, estimated_y)

def determine_nearest_node(coordinate, graph):
    min_dist = float('inf')
    nearest_node = None
    
    logging.info("\nNearest Node Calculation:")
    for node, data in graph['nodes'].items():
        node_coord = data['coords']
        dist = math.sqrt((coordinate[0] - node_coord[0])**2 + 
                        (coordinate[1] - node_coord[1])**2)
        
        logging.info(f"Node: {node}")
        logging.info(f"  Distance to user: {dist:.2f} meters")
        
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    
    logging.info(f"\nSelected Nearest Node: {nearest_node}")
    logging.info(f"  Distance: {min_dist:.2f} meters")
    
    return nearest_node

@app.route("/", methods=["POST"])
def process_wifi_data():
    global latest_results, active_exits
    try:
        data = request.get_json(force=True)
        if not data or 'wifi_devices' not in data or 'device_tag' not in data:
            return jsonify({'status': 'failure', 'message': 'Invalid input data'}), 400

        wifi_devices = data['wifi_devices']
        device_tag = data['device_tag']

        # Process WiFi devices
        devices, distances, weights = process_devices(wifi_devices)
        if len(devices) < 2:
            return jsonify({'status': 'failure', 'message': 'Need at least 2 known routers'}), 400

        # Estimate position
        estimated_coord = triangulate_position(devices, distances, weights)
        if not estimated_coord:
            return jsonify({'status': 'failure', 'message': 'Triangulation failed'}), 400

        # Find nearest node
        user_node = determine_nearest_node(estimated_coord, graph)

        # Find the nearest available exit
        assigned_exit = find_nearest_available_exit(user_node)

        if not assigned_exit:
            return jsonify({'status': 'failure', 'message': 'No available exits'}), 400

        # Calculate path to assigned exit
        path, total_distance = a_star(graph, user_node, assigned_exit, set())

        if path:
            result = {
                'device_tag': device_tag,
                'user_location': user_node,
                'coordinates': {'x': estimated_coord[0], 'y': estimated_coord[1]},
                'assigned_exit': assigned_exit,
                'shortest_path': path,
                'total_distance': f"{total_distance:.2f} meters"
            }
            latest_results[device_tag] = result
            active_exits[assigned_exit].append(device_tag)  # Mark exit as occupied
            
            send_update()  # Emit real-time update
            
            return jsonify({'status': 'success', 'data': result}), 200
        else:
            return jsonify({'status': 'failure', 'message': 'No path found'}), 400

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'status': 'failure', 'message': f'Internal error: {str(e)}'}), 500

@app.route('/result/<device_tag>', methods=['GET'])
def get_result(device_tag):
    global latest_results
    result = latest_results.get(device_tag)
    if result:
        return jsonify({'status': 'success', 'data': result}), 200
    return jsonify({
        'status': 'failure',
        'message': 'No result available for the given device tag'
    }), 400

@app.route('/exit/<device_tag>', methods=['POST'])
def free_exit(device_tag):
    global latest_results, active_exits

    if device_tag in latest_results:
        assigned_exit = latest_results[device_tag]['assigned_exit']
        if assigned_exit in active_exits and device_tag in active_exits[assigned_exit]:
            active_exits[assigned_exit].remove(device_tag)  # Free up the exit

        del latest_results[device_tag]
        return jsonify({'status': 'success', 'message': f'Exit {assigned_exit} is now free'}), 200
    
    return jsonify({'status': 'failure', 'message': 'Device tag not found'}), 400

@socketio.on("connect")
def handle_connect():
    logging.info("Client connected")
    send_update()  # Send initial data on connection
    
@socketio.on('disconnect')
def handle_disconnect():
    logging.info("Client disconnected")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)