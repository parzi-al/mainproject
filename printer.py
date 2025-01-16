def print_wifi_data(wifi_data):
    """
    Function to print Wi-Fi data to the console.

    :param wifi_data: A list of dictionaries containing SSID and signal strength for Wi-Fi networks.
    """
    print("Received Wi-Fi data:")
    for device in wifi_data:
        ssid = device.get('SSID', 'Unknown SSID')
        signal_strength = device.get('Signal', 'Unknown Signal')
        print(f"SSID: {ssid}, Signal Strength: {signal_strength}")
