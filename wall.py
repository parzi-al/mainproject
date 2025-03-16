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
    }''')
    routers = {"Router1": (7.5, 2.0), "Router2": (5.5, 3.5), "Router3": (7.5, 9.0)}
    distances = {"Router1": 5, "Router2": 2.5, "Router3": 0}
    walls = [(2.0, 2.0, 4.0, 4.0), (5.0, 5.0, 7.0, 7.7)]
    user_location = particle_filter_localization(routers, distances, walls)
    print(f"User is most likely at: {user_location}")
    start_node = min(graph['nodes'], key=lambda node: heuristic(graph['nodes'][node]['coords'], user_location))
    end_node = "Staircase 1"
    unsafe_segments = set()
    path, distance = a_star(graph, start_node, end_node, unsafe_segments)
    if path:
        print(f"Shortest safe path from {start_node} to {end_node}: {' -> '.join(path)}")
        print(f"Total distance: {distance:.2f} meters")
    else:
        print("No safe path found!")

if __name__ == "__main__":
    main()
