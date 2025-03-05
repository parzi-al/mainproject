import requests
import random
import time
import threading

# Configuration
BASE_URL = "http://localhost:5000"
NUM_DEVICES = 50
FIRE_UPDATE_INTERVAL = 10  # seconds

# List of valid router names from the server's configuration
ROUTERS = ["CS_Lab", "bvn s22", "MITS_STAFF"]
NODES = [
    "Entrance", "Verandah", "Living Room", "Stair Hall", "Dining Space",
    "Kitchen", "Toilet2", "Bedroom", "Master Bedroom", "Toilet",
    "Balcony1", "Balcony2"
]

def simulate_device(device_id):
    device_tag = f"device_{device_id:02d}"
    print(f"Starting device {device_tag}")
    
    try:
        # Simulate 5 location updates
        for _ in range(5):
            # Generate random signal strengths (-100 to -30 dBm)
            wifi_devices = [{
                "name": router,
                "signalStrength": random.randint(-90, -40)
            } for router in random.sample(ROUTERS, 2)]  # Always send 2 routers

            payload = {
                "wifi_devices": wifi_devices,
                "device_tag": device_tag
            }

            response = requests.post(f"{BASE_URL}/", json=payload)
            print(f"{device_tag} location update: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"{device_tag} path: {data['data']['shortest_path']}")
            
            time.sleep(random.uniform(2, 5))
            
        # Simulate exiting
        response = requests.post(f"{BASE_URL}/exit/{device_tag}")
        print(f"{device_tag} exit: {response.status_code}")
        
    except Exception as e:
        print(f"Error in {device_tag}: {str(e)}")

def simulate_fire_alerts():
    while True:
        # Randomly select 1-3 nodes to set on fire
        fire_nodes = random.sample(NODES, random.randint(1, 3))
        payload = {"nodes": fire_nodes}
        
        try:
            response = requests.post(f"{BASE_URL}/fire", json=payload)
            print(f"Fire update ({fire_nodes}): {response.status_code}")
        except Exception as e:
            print(f"Fire simulation error: {str(e)}")
        
        time.sleep(FIRE_UPDATE_INTERVAL)

def main():
    # Start fire simulation thread
    fire_thread = threading.Thread(target=simulate_fire_alerts)
    fire_thread.start()

    # Create device threads
    threads = []
    for device_id in range(1, NUM_DEVICES + 1):
        thread = threading.Thread(target=simulate_device, args=(device_id,))
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # Stagger device starts

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All devices completed their simulations")

if __name__ == "__main__":
    main()