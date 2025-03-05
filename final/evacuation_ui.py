import sys
import json
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QTimer
# Flask Server URL
FLASK_SERVER_URL = "http://127.0.0.1:5000"

# Define colors
PATH_COLOR = QColor(0, 0, 255)  # Blue for paths
EXIT_COLOR = QColor(0, 255, 0)  # Green for exits
FIRE_COLOR = QColor(255, 0, 0)  # Red for fire
USER_COLOR = QColor(255, 165, 0)  # Orange for user location

class EvacuationMap(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Evacuation Route Visualization")
        self.setGeometry(100, 100, 800, 600)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.setCentralWidget(self.view)

        self.nodes = {}
        self.paths = []

        self.fetch_and_draw_map()

        # Timer to fetch updates every 3 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.fetch_and_draw_map)
        self.timer.start(3000)

    def fetch_and_draw_map(self):
        """Fetch data from Flask and update the visualization"""
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/update")
            if response.status_code == 200:
                data = response.json()
                self.draw_map(data)
        except Exception as e:
            print("Error fetching data:", e)

    def draw_map(self, data):
        """Clear and redraw the map based on the latest data."""
        self.scene.clear()

        graph = data.get("graph", {})
        devices = data.get("devices", [])
        fire_nodes = set(data.get("fire_nodes", []))

        # Draw nodes
        self.nodes = {}
        for node, details in graph["nodes"].items():
            x, y = details["coords"]
            self.draw_node(node, x * 50, y * 50, fire_nodes)

        # Draw safe paths for each user
        for device in devices:
            path = device.get("shortest_path", [])
            self.draw_path(path)

    def draw_node(self, name, x, y, fire_nodes):
        """Draw a node with a label, applying different colors for exits and fire areas."""
        node_color = EXIT_COLOR if "Balcony" in name or name == "Entrance" else Qt.white
        if name in fire_nodes:
            node_color = FIRE_COLOR

        # Create node circle
        node_item = QGraphicsEllipseItem(x, y, 20, 20)
        node_item.setBrush(node_color)
        self.scene.addItem(node_item)

        # Add node label
        text_item = QGraphicsTextItem(name)
        text_item.setDefaultTextColor(Qt.black)
        text_item.setPos(x, y - 20)
        self.scene.addItem(text_item)

        # Store the node position
        self.nodes[name] = (x + 10, y + 10)

    def draw_path(self, path):
        """Draw the evacuation route using blue lines."""
        pen = QPen(PATH_COLOR, 3)
        for i in range(len(path) - 1):
            start_node, end_node = path[i], path[i + 1]
            if start_node in self.nodes and end_node in self.nodes:
                x1, y1 = self.nodes[start_node]
                x2, y2 = self.nodes[end_node]
                line = QGraphicsLineItem(x1, y1, x2, y2)
                line.setPen(pen)
                self.scene.addItem(line)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EvacuationMap()
    window.show()
    sys.exit(app.exec_())
