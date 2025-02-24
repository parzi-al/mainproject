import json
import heapq
import math
import random

# Number of particles for Monte Carlo Localization
NUM_PARTICLES = 1000

# Heuristic function (Euclidean distance)
def heuristic(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

# Check if a line between two points intersects any walls (obstructions)
def is_line_of_sight_clear(start, end, walls):
    for wall in walls:
        # Check if the line between 'start' and 'end' intersects the wall
        # Assuming walls are represented as line segments (x1, y1, x2, y2)
        x1, y1, x2, y2 = wall
        if do_lines_intersect(start, end, (x1, y1), (x2, y2)):
            return False
    return True

# Check if two line segments intersect
def do_lines_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

# Particle Filter Localization (Monte Carlo Localization - MCL)
def particle_filter_localization(routers, distances, walls):
    particles = []
    
    # Initialize particles randomly across the map
    for _ in range(NUM_PARTICLES):
        x = random.uniform(0, 10)
        y = random.uniform(0, 10)
        particles.append((x, y))

    for _ in range(5):  # Iteratively refine particles
        weights = []
        for p in particles:
            error = 0
            for router, true_distance in distances.items():
                expected_distance = heuristic(p, routers[router])

                # Check for obstruction
                if not is_line_of_sight_clear(p, routers[router], walls):
                    expected_distance = float('inf')  # Invalidate this distance if blocked by a wall

                error += abs(expected_distance - true_distance)
            weights.append(1 / (error + 1e-6))  # Avoid division by zero
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            continue
        weights = [w / total_weight for w in weights]

        # Resampling: pick particles based on weight
        new_particles = random.choices(particles, weights, k=NUM_PARTICLES)
        particles = new_particles

    # Return the most probable location (mean of best particles)
    avg_x = sum(p[0] for p in particles) / len(particles)
    avg_y = sum(p[1] for p in particles) / len(particles)
    return (avg_x, avg_y)

# A* Pathfinding Algorithm
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

# Reconstruct the shortest path
def reconstruct_path(came_from, current):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.append(current)
    return path[::-1]

# Main function
def main():
    # Building Layout (Graph)
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

    # Wi-Fi routers placed at exact coordinates
    routers = {
        "Router1": (7.5, 2.0),
        "Router2": (5.5, 3.5),
        "Router3": (7.5, 9.0)
    }

    # Measured distances from Wi-Fi signals
    distances = {
        "Router1": 5,
        "Router2": 2.5,
        "Router3": 0
    }

    # Walls in the map (represented as line segments with start and end coordinates)
    walls = [
        (2.0, 2.0, 4.0, 4.0),  # Example wall from (2,2) to (4,4)
        (5.0, 5.0, 7.0, 7.0)   # Example wall from (5,5) to (7,7)
    ]

    # Find user location using Particle Filter
    user_location = particle_filter_localization(routers, distances, walls)
    print(f"User is most likely at: {user_location}")

    # Find nearest room
    start_node = min(graph['nodes'], key=lambda node: heuristic(graph['nodes'][node]['coords'], user_location))
    end_node = "Entrance"

    # Compute the shortest path to the Entrance
    unsafe_segments = set()
    path, distance = a_star(graph, start_node, end_node, unsafe_segments)

    if path:
        print(f"Shortest safe path from {start_node} to {end_node}: {' -> '.join(path)}")
        print(f"Total distance: {distance:.2f} meters")
    else:
        print("No safe path found!")

if __name__ == "__main__":
    main()
