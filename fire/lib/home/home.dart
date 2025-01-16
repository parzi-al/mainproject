import 'package:flutter/material.dart';
import 'package:wifi_iot/wifi_iot.dart';
import 'package:shimmer/shimmer.dart'; // Ensure this package is installed

class WiFiScanPage extends StatefulWidget {
  const WiFiScanPage({Key? key}) : super(key: key);

  @override
  State<WiFiScanPage> createState() => _WiFiScanPageState();
}

class _WiFiScanPageState extends State<WiFiScanPage> {
  List<WifiNetwork> _wifiNetworks = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _scanWiFiNetworks();
  }

  Future<void> _scanWiFiNetworks() async {
    setState(() {
      _isLoading = true;
    });
    await Future.delayed(const Duration(seconds: 2)); // Simulate loading delay
    final networks = await WiFiForIoTPlugin.loadWifiList();
    setState(() {
      _wifiNetworks = networks;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Wi-Fi Networks"),
        centerTitle: true,
        backgroundColor: Colors.blueAccent,
      ),
      body: _isLoading
          ? _buildShimmerEffect()
          : _wifiNetworks.isEmpty
              ? const Center(child: Text("No Wi-Fi networks found"))
              : ListView.builder(
                  itemCount: _wifiNetworks.length,
                  itemBuilder: (context, index) {
                    final network = _wifiNetworks[index];
                    return _buildAnimatedListItem(network, index);
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: _scanWiFiNetworks,
        backgroundColor: Colors.blueAccent,
        child: const Icon(Icons.refresh),
      ),
    );
  }

  Widget _buildShimmerEffect() {
    return ListView.builder(
      itemCount: 8,
      itemBuilder: (context, index) {
        return Shimmer.fromColors(
          baseColor: Colors.grey[300]!,
          highlightColor: Colors.grey[100]!,
          child: ListTile(
            leading: const Icon(Icons.wifi, size: 40, color: Colors.grey),
            title: Container(height: 15, color: Colors.grey[300]),
            subtitle: Container(height: 10, color: Colors.grey[300]),
          ),
        );
      },
    );
  }

  Widget _buildAnimatedListItem(WifiNetwork network, int index) {
    return TweenAnimationBuilder<double>(
      duration: const Duration(milliseconds: 500),
      tween: Tween<double>(begin: 0.0, end: 1.0),
      curve: Curves.easeInOut,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, (1 - value) * 20),
            child: child,
          ),
        );
      },
      child: Card(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        elevation: 3,
        child: ListTile(
          leading: const Icon(Icons.wifi, color: Colors.blueAccent),
          title: Text(network.ssid ?? 'Unknown SSID', style: const TextStyle(fontWeight: FontWeight.bold)),
          subtitle: Text('Signal Strength: ${network.level} dBm'),
          trailing: _getSignalIcon(network.level),
        ),
      ),
    );
  }

  Icon _getSignalIcon(int? level) {
    if (level == null) return const Icon(Icons.signal_wifi_0_bar_sharp, color: Colors.redAccent);
    if (level > -50) return const Icon(Icons.signal_wifi_4_bar, color: Colors.green);
    if (level > -70) return const Icon(Icons.signal_wifi_4_bar_sharp, color: Colors.orange);
    return const Icon(Icons.signal_wifi_bad, color: Colors.redAccent);
  }
}
