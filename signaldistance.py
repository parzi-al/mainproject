import numpy as np
import platform
import subprocess
from pywifi import PyWiFi, const

def estimate_distance(power_received, params=None):
    """
    Estimate the distance based on received signal strength (RSS).
    
    Parameters:
        power_received (float): RSS reading in dBm.
        params (4-tuple float): (d_ref, power_ref, path_loss_exp, stdev_power).
        
    Returns:
        tuple: (d_est, d_min, d_max) in meters, rounded to two decimal points.
    """
    if params is None:
        params = (1.0, -55.0, 2.0, 2.5)

    d_ref, power_ref, path_loss_exp, stdev_power = params
    uncertainty = 2 * stdev_power  # Approx. 95.45% confidence range

    d_est = d_ref * (10 ** (-(power_received - power_ref) / (10 * path_loss_exp)))
    d_min = d_ref * (10 ** (-(power_received - power_ref + uncertainty) / (10 * path_loss_exp)))
    d_max = d_ref * (10 ** (-(power_received - power_ref - uncertainty) / (10 * path_loss_exp)))

    return round(d_est, 2), round(d_min, 2), round(d_max, 2)

def get_wifi_networks():
    """
    Retrieve a list of available WiFi networks and their signal strengths.
    
    Returns:
        list: A list of dictionaries with SSID and signal strength in dBm.
    """
    networks = []
    if platform.system() == "Windows":
        cmd = "netsh wlan show networks mode=bssid"
        output = subprocess.check_output(cmd, shell=True, text=True)
        lines = output.splitlines()
        ssid = None
        for line in lines:
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":")[1].strip()
            elif "Signal" in line:
                signal_strength = line.split(":")[1].strip()
                signal = -100 + (int(signal_strength.rstrip('%')) / 2)
                if ssid:
                    networks.append({"SSID": ssid, "Signal": signal})
    elif platform.system() == "Linux":
        cmd = "nmcli -f SSID,SIGNAL dev wifi list"
        output = subprocess.check_output(cmd, shell=True, text=True)
        lines = output.splitlines()[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                ssid = " ".join(parts[:-1])
                signal_strength = int(parts[-1])
                signal = -100 + (signal_strength / 2)
                networks.append({"SSID": ssid, "Signal": signal})
    else:
        print("Unsupported platform. Only Windows and Linux are supported.")
    return networks

def display_network_distances():
    """
    Display available WiFi networks and their estimated distances.
    """
    print("Scanning for WiFi networks...")
    networks = get_wifi_networks()

    if not networks:
        print("No networks found.")
        return

    print("\nAvailable Networks:")
    for network in networks:
        ssid = network["SSID"]
        signal = network["Signal"]
        d_est, d_min, d_max = estimate_distance(signal)
        print(f"SSID: {ssid}, Signal: {signal} dBm")
        print(f"  Estimated Distance: {d_est} m")
        print(f"  Distance Range: {d_min} - {d_max} m\n")

if __name__ == '__main__':
    display_network_distances()
