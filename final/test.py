import requests
import time
import json
import random

BASE_URL = "http://127.0.0.1:5000"  # Change if running on a different server

def test_device(device_tag, wifi_devices):
    url = f"{BASE_URL}/"
    payload = {
        "device_tag": device_tag,
        "wifi_devices": wifi_devices
    }
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Device: {device_tag} - Response: {response.json()}\n")
    return response.json()

def get_result(device_tag):
    url = f"{BASE_URL}/result/{device_tag}"
    response = requests.get(url)
    print(f"Device: {device_tag} - Result: {response.json()}\n")
    return response.json()

def release_exit(device_tag):
    url = f"{BASE_URL}/exit/{device_tag}"
    response = requests.post(url)
    print(f"Device: {device_tag} - Exit Released: {response.json()}\n")
    return response.json()

if __name__ == "__main__":
    # Generate 100 device tags and corresponding WiFi device data
    device_tags = [f"device_{i}" for i in range(1, 101)]
    devices_data_list = [
        [
            {"name": random.choice(["CS_Lab", "bvn s22", "MITS_STAFF"]), "signalStrength": random.randint(-80, -50)},
            {"name": random.choice(["CS_Lab", "bvn s22", "MITS_STAFF"]), "signalStrength": random.randint(-150, -10)},
            {"name": random.choice(["CS_Lab", "bvn s22", "MITS_STAFF"]), "signalStrength": random.randint(-60, -20)}
        ]
        for _ in range(100)
    ]
    
    # Simulate multiple devices
    for tag, wifi_data in zip(device_tags, devices_data_list):
        test_device(tag, wifi_data)
        time.sleep(0.1)  # Small delay to simulate real-world scenario
    
    # Fetch results
    for tag in device_tags:
        get_result(tag)
        time.sleep(0.1)
    
    # Randomly select a subset of device tags to release exits
    subset_to_release = random.sample(device_tags, k=50)  # Release exits for 50 random devices
    
    # Release exits
    for tag in subset_to_release:
        release_exit(tag)
        time.sleep(0.1)