import eventlet
eventlet.monkey_patch()  #
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import logging
import math
from wall import particle_filter_localization, a_star, heuristic
from estimate_distance import estimate_distance

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')  # Ensure 'index.html' is in 'templates' folder

logging.basicConfig(level=logging.INFO)

latest_results = {}
active_exits = {
    "Staircase 1": [],
    "Staircase 2": [],
    "Elevator 1": []
}
node_congestion = {}  # Will be initialized with graph nodes
fire_nodes = set()  # Track nodes affected by fire

EXIT_CAPACITY = {
    "Staircase 1": 10,
    "Staircase 2": 15,
    "Elevator 1": 8
}
CONGESTION_THRESHOLD = 5  # Maximum allowed users per node

FIXED_ROUTERS = {
    "GNXS-2.4G-095C60": (4, 11),
    "GNXS-5G-095C60": (1, 8),
    "MITS_STAFF": (8, 5)
}

graph = {
        "nodes": {
        "Staircase 1": {"coords": [0, 0], "connections": {"Passage 1": 5}},
        "Passage 1": {"coords": [5, 0], "connections": {"Staircase 1": 5, "Elevator 1": 3, "Turing Lab": 2, "Grace Hopper Lab": 2, "Staircase 2": 5}},
        "Elevator 1": {"coords": [2, 0], "connections": {"Passage 1": 3}},
        "Turing Lab": {"coords": [5, 2], "connections": {"Passage 1": 2, "Electrical & Electronics Department": 3}},
        "Grace Hopper Lab": {"coords": [5, -2], "connections": {"Passage 1": 2, "Language Lab": 2}},
        "Language Lab": {"coords": [7, -2], "connections": {"Grace Hopper Lab": 2, "CAD Lab (CE)": 2}},
        "CAD Lab (CE)": {"coords": [9, -2], "connections": {"Language Lab": 2, "Staircase 2": 3}},
        "Staircase 2": {"coords": [10, 0], "connections": {"Passage 1": 5, "Dijkstra Lab": 2}},
        "Elevator 2": {"coords": [8, 0], "connections": {"Passage 1": 3}},
        "Dijkstra Lab": {"coords": [10, 2], "connections": {"Staircase 2": 2, "Codd Base Lab": 2}},
        "Codd Base Lab": {"coords": [12, 2], "connections": {"Dijkstra Lab": 2, "Boy's Common Room": 2, "Fire Exit": 2}},
        "Boy's Common Room": {"coords": [12, 4], "connections": {"Codd Base Lab": 2, "Steve Jobs Hall": 2}},
        "Steve Jobs Hall": {"coords": [10, 4], "connections": {"Boy's Common Room": 2, "Measurements Lab": 2}},
        "Measurements Lab": {"coords": [8, 4], "connections": {"Steve Jobs Hall": 2, "Michael Faraday Hall": 2}},
        "Michael Faraday Hall": {"coords": [6, 4], "connections": {"Measurements Lab": 2, "Departmental Library": 2}},
        "Departmental Library": {"coords": [4, 4], "connections": {"Michael Faraday Hall": 2, "Ladies Toilet": 2}},
        "Ladies Toilet": {"coords": [2, 4], "connections": {"Departmental Library": 2}},
        "Fire Exit": {"coords": [12, 0], "connections": {"Codd Base Lab": 2}},
        "Electrical Room": {"coords": [12, 6], "connections": {"Codd Base Lab": 4}},
        "Gent's Toilet": {"coords": [0, 2], "connections": {"Staircase 1": 2}}
    }

}

# Initialize node congestion
node_congestion = {node: 0 for node in graph['nodes']}

def send_update():
    socketio.emit("update", {
        "devices": list(latest_results.values()),
        "exits": active_exits,
        "congestion": node_congestion,
        "fire_nodes": list(fire_nodes),
        "exit_capacity": EXIT_CAPACITY
    })

def find_nearest_available_exit(user_node, blocked_nodes):
    exit_distances = {}
    for exit in active_exits.keys():
        if exit in blocked_nodes:
            continue
        user_coords = graph['nodes'][user_node]['coords']
        exit_coords = graph['nodes'][exit]['coords']
        distance = math.sqrt((exit_coords[0] - user_coords[0])**2 + 
                            (exit_coords[1] - user_coords[1])**2)
        exit_distances[exit] = distance
    logging.info(f"Exit distances before sorting: {exit_distances}")  # Debugging log

    sorted_exits = sorted(exit_distances.items(), key=lambda x: x[1])
    logging.info(f"Sorted exits: {sorted_exits}")  # Debugging log

    for exit, _ in sorted_exits:
        if len(active_exits[exit]) < EXIT_CAPACITY[exit]:
            path, _ = a_star(graph, user_node, exit, blocked_nodes)
            if path:
                return exit
    return None

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

@app.route("/fire", methods=["POST"])
def update_fire():
    global fire_nodes
    data = request.get_json()
    if 'nodes' in data and isinstance(data['nodes'], list):
        fire_nodes = set(data['nodes'])
        logging.info(f"Fire nodes updated: {fire_nodes}")
        send_update()
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "failure"}), 400

@app.route("/", methods=["POST"])
def process_wifi_data():
    global latest_results, active_exits, node_congestion
    try:
        data = request.get_json()
        logging.info(f"Received data: {data}")  # <-- Add this debug log

        if not data or 'wifi_devices' not in data or 'device_tag' not in data:
            return jsonify({'status': 'failure', 'message': 'Invalid input'}), 400

        wifi_devices = data['wifi_devices']
        device_tag = data['device_tag']

        # Process devices and calculate position
        devices, distances, weights = process_devices(wifi_devices)
        if len(devices) < 2:
            return jsonify({'status': 'failure', 'message': 'Need 2+ routers'}), 400

        estimated_coord = triangulate_position(devices, distances, weights)
        if not estimated_coord:
            return jsonify({'status': 'failure', 'message': 'Triangulation failed'}), 400

        user_node = determine_nearest_node(estimated_coord, graph)

        # Calculate blocked nodes (fire + congestion)
        blocked_nodes = fire_nodes.union(
            {node for node, count in node_congestion.items() if count >= CONGESTION_THRESHOLD}
        )

        assigned_exit = find_nearest_available_exit(user_node, blocked_nodes)
        if not assigned_exit:
            return jsonify({'status': 'failure', 'message': 'No exits available'}), 400

        # Calculate path with congestion and fire avoidance
        path, total_distance = a_star(graph, user_node, assigned_exit, blocked_nodes)
        if not path:
            return jsonify({'status': 'failure', 'message': 'No safe path'}), 400

        # Update congestion counters
        for node in path:
            node_congestion[node] += 1

        result = {
            'device_tag': device_tag,
            'user_location': user_node,
            'coordinates': {'x': estimated_coord[0], 'y': estimated_coord[1]},
            'assigned_exit': assigned_exit,
            'shortest_path': path,
            'total_distance': f"{total_distance:.2f} meters"
        }
        latest_results[device_tag] = result
        active_exits[assigned_exit].append(device_tag)
        send_update()

        return jsonify({'status': 'success', 'data': result}), 200

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'status': 'failure', 'message': str(e)}), 500

@app.route('/exit/<device_tag>', methods=['POST'])
def free_exit(device_tag):
    global latest_results, active_exits, node_congestion
    if device_tag in latest_results:
        result = latest_results[device_tag]
        exit_node = result['assigned_exit']
        path = result['shortest_path']

        if exit_node in active_exits and device_tag in active_exits[exit_node]:
            active_exits[exit_node].remove(device_tag)

        for node in path:
            if node in node_congestion:
                node_congestion[node] -= 1

        del latest_results[device_tag]
        send_update()
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'failure'}), 400

@socketio.on("connect")
def handle_connect():
    send_update()

@app.route("/update", methods=["GET"])
def send_map_update():
    return jsonify({
        "graph": graph,
        "devices": list(latest_results.values()),
        "fire_nodes": list(fire_nodes),
    })

@app.route('/get_updates', methods=['GET'])
def get_updates():
    return jsonify({
        "devices": list(latest_results.values()),
        "fire_nodes": list(fire_nodes),
        "graph": graph
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
