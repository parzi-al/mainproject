import json
import heapq

# A* algorithm implementation
def a_star(graph, start, goal, unsafe_segments):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {node: float('inf') for node in graph['nodes']}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph['nodes']}
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
                if neighbor not in [item[1] for item in open_set]:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, float('inf')

# Heuristic function for A* (Euclidean distance)
def heuristic(coord1, coord2):
    return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2) ** 0.5

# Reconstruct the path from start to goal
def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

# Function to check path safety dynamically
def check_path_safety(graph, path, unsafe_segments):
    for i in range(len(path) - 1):
        print(f"Is the path from {path[i]} to {path[i+1]} safe? (1 for Yes, 0 for No)")
        user_input = int(input("Enter your choice: "))
        if user_input == 0:
            # Mark the segment as unsafe and discard the path
            unsafe_segments.add((path[i], path[i+1]))
            return False
    return True

# Main function
def main():
    # Input JSON for the building layout
    json_input = '''
    {
      "nodes": {
        "Entrance": {
          "coords": [0, 0],
          "connections": {"Verandah": 2.5}
       
        },
        "Verandah": {
          "coords": [2.5, 0],
          "connections": {"Entrance": 2.5, "Living Room": 5.0, "Stair Hall": 3.5}
       
        },
        "Living Room": {
          "coords": [7.5, 0],
          "connections": {"Verandah": 5.0, "Dining Space": 3.0, "Toilet2": 1.5}
       
        },
        "Stair Hall": {
          "coords": [2.5, 3.5],
          "connections": {"Verandah": 3.5, "Dining Space": 3.0}
       
        },
        "Dining Space": {
          "coords": [5.5, 3.5],
          "connections": {
            "Living Room": 3.0,
            "Stair Hall": 3.0,
            "Kitchen": 2.5,
            "Master Bedroom": 3.0,
            "Bedroom": 3.0
          }
       
        },
        "Kitchen": {
          "coords": [8.0, 7.0],
          "connections": {"Dining Space": 2.5}
       
        },
        "Toilet2": {
          "coords": [8.0, 8.5],
          "connections": {"Living Room": 1.5}
       
        },
        "Bedroom": {
          "coords": [8.0, 10.0],
          "connections": {"Balcony2": 1.0, "Dining Space": 3.0}
       
        },
        "Master Bedroom": {
          "coords": [2.5, 7.0],
          "connections": {"Dining Space": 3.0, "Toilet": 1.5, "Balcony1": 1.0}
       
        },
        "Toilet": {
          "coords": [1.0, 7.0],
          "connections": {"Master Bedroom": 1.5}
       
        },
        "Balcony1": {
          "coords": [1.0, 9.0],
          "connections": {"Master Bedroom": 1.0}
       
        },
        "Balcony2": {
          "coords": [9.0, 10.0],
          "connections": {"Bedroom": 1.0}
        }
      }
    }
    '''
    
    # Parse JSON into Python dictionary
    graph = json.loads(json_input)
    
    # Input start and end points
    start_node = "Entrance"
    end_node = "Bedroom"
    
    unsafe_segments = set()
    
    while True:
        path, distance = a_star(graph, start_node, end_node, unsafe_segments)
        if path:
         
            is_safe = check_path_safety(graph, path, unsafe_segments)
            if is_safe:
                print("Safe path found!")
                print(f"Shortest path from {start_node} to {end_node}: {' -> '.join(path)}")
                print(f"Total distance: {distance:.2f} meters")
                
                break
        else:
            print(f"No safe path found from {start_node} to {end_node}.")
            break

if __name__ == "__main__":
    main()
