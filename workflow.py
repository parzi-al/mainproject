import numpy as np
import matplotlib.pyplot as plt
from estimate_distance import estimate_distance
from simulate_rss_matrix import simulate_rss_matrix
from estimate_distance_matrix import estimate_distance_matrix

# Parameters
num_devices = 5
area_side = 100

# Step 1: Simulate RSS data
node_locs, rss_matrix = simulate_rss_matrix(num_devices, area_side)

# Step 2: Compute distances from user (device 0)
user_device = 0
distances, _ = estimate_distance_matrix(
    rss_matrix, 
    use_model="rss_only", 
    reference_device=user_device
)

# Step 3: Print distance estimates
print(f"Distances from User (Device {user_device}):")
for i, dist in enumerate(distances):
    if i != user_device:  # Skip the user device itself
        print(f"Device {i}: {dist:.2f} m")

# Step 4: Visualize device locations
plt.scatter(node_locs[:, 0], node_locs[:, 1], label="Devices", c="blue")
plt.scatter(node_locs[user_device, 0], node_locs[user_device, 1], label="User", c="red")
for i, (x, y) in enumerate(node_locs):
    plt.text(x, y, f"Device {i}", fontsize=9)

plt.legend()
plt.title("Device Locations")
plt.xlabel("X-coordinate (m)")
plt.ylabel("Y-coordinate (m)")
plt.grid()
plt.show()
