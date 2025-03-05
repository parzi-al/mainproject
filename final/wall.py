import json
import heapq
import math
import random
from safety_check import is_safe

NUM_PARTICLES = 1000

def heuristic(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def is_line_of_sight_clear(start, end, walls):
    for wall in walls:
        x1, y1, x2, y2 = wall
        if do_lines_intersect(start, end, (x1, y1), (x2, y2)):
            return False
    return True

def do_lines_intersect(p1, p2, p3, p4):
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def particle_filter_localization(routers, distances, walls):
    particles = [(random.uniform(0, 10), random.uniform(0, 10)) for _ in range(NUM_PARTICLES)]
    
    for _ in range(5):
        weights = []
        for p in particles:
            error = sum(
                abs(heuristic(p, routers[r]) - d) if is_line_of_sight_clear(p, routers[r], walls) else float('inf')
                for r, d in distances.items()
            )
            weights.append(1 / (error + 1e-6))
        
        total_weight = sum(weights)
        if total_weight == 0:
            continue
        weights = [w / total_weight for w in weights]
        particles = random.choices(particles, weights, k=NUM_PARTICLES)

    avg_x = sum(p[0] for p in particles) / len(particles)
    avg_y = sum(p[1] for p in particles) / len(particles)
    return (avg_x, avg_y)

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
            if not is_safe(neighbor) or (current, neighbor) in unsafe_segments:
                continue

            tentative_g_score = g_score[current] + distance
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(graph['nodes'][neighbor]['coords'], graph['nodes'][goal]['coords'])
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None, float('inf')

def reconstruct_path(came_from, current):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.append(current)
    return path[::-1]

def main():
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

    routers = {"Router1": (7.5, 2.0), "Router2": (5.5, 3.5), "Router3": (7.5, 9.0)}
    distances = {"Router1": 5, "Router2": 2.5, "Router3": 0}
    walls = [(2.0, 2.0, 4.0, 4.0), (5.0, 5.0, 7.0, 7.7)]
    user_location = particle_filter_localization(routers, distances, walls)
    print(f"User is most likely at: {user_location}")
    start_node = min(graph['nodes'], key=lambda node: heuristic(graph['nodes'][node]['coords'], user_location))
    end_node = "Entrance"
    unsafe_segments = set()
    path, distance = a_star(graph, start_node, end_node, unsafe_segments)
    if path:
        print(f"Shortest safe path from {start_node} to {end_node}: {' -> '.join(path)}")
        print(f"Total distance: {distance:.2f} meters")
    else:
        print("No safe path found!")

if __name__ == "__main__":
    main()
