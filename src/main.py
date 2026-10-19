import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QToolBar,
    QWidget,
)

from axis_panel import AxisPanel
from graph_view import GraphView
from points_panel import PointsPanel
from utils import pixel_to_data_coordinates

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Datasheet Picker")
        self.resize(1400, 900)

        self.selection_sequence = ["X1", "X2", "Y1", "Y2"]

        self.selection_index = 0

        self.mode = "calibration"
        self.graphs = {}
        self.active_graph_id = None
        self.graph_colors = [
            "#2ecc71",
            "#e67e22",
            "#3498db",
            "#e84393",
            "#f1c40f",
        ]

        self._create_ui()
        self._connect_signals()

        self._create_graph("graph-1", "Graph 1", self.graph_colors[0])
        self._activate_graph("graph-1")

        self.axis_panel.set_current_selection("X1")
        self.graph_view.start_axis_selection("X1")

    def _create_ui(self):
        central = QWidget()
        layout = QHBoxLayout(central)

        self.axis_panel = AxisPanel()
        self.graph_view = GraphView()
        self.points_panel = PointsPanel()

        self.axis_panel.setMinimumWidth(260)
        self.axis_panel.setMaximumWidth(320)
        self.points_panel.setMinimumWidth(250)
        self.points_panel.setMaximumWidth(360)

        layout.addWidget(self.axis_panel)
        layout.addWidget(self.graph_view)
        layout.addWidget(self.points_panel)

        self.setCentralWidget(central)

        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)

        self.open_button = QPushButton("Open Image")

        self.reset_view_button = QPushButton("Reset View")

        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.reset_view_button)

        self.addToolBar(
            Qt.ToolBarArea.TopToolBarArea,
            toolbar,
        )

    def _connect_signals(self):
        self.open_button.clicked.connect(self.open_image)
        self.reset_view_button.clicked.connect(self.reset_view)

        self.axis_panel.select_point.connect(self.select_axis_point)
        self.axis_panel.reset.connect(self.reset_axis_selection)
        self.axis_panel.mode_points.connect(self.start_points_mode)
        self.axis_panel.mode_calibration.connect(self.start_calibration_mode)

        for spinbox in (
            self.axis_panel.x1_value,
            self.axis_panel.x2_value,
            self.axis_panel.y1_value,
            self.axis_panel.y2_value,
        ):
            spinbox.valueChanged.connect(self.update_calibrated_points)

        self.axis_panel.x_logarithmic.toggled.connect(
            self.update_calibrated_points
        )
        self.axis_panel.y_logarithmic.toggled.connect(
            self.update_calibrated_points
        )

        self.graph_view.clicked.connect(self.on_graph_clicked)
        self.graph_view.point_added.connect(self.add_point_to_tree)
        self.points_panel.graph_added.connect(self.add_graph)
        self.points_panel.graph_selected.connect(self.select_graph)
        self.points_panel.graph_removed.connect(self.remove_graph)
        self.points_panel.graph_visibility_changed.connect(
            self.set_graph_visibility
        )

    def _create_graph(self, graph_id, name, color):
        self.graphs[graph_id] = {"name": name}
        self.graph_view.add_graph(graph_id, color)
        self.points_panel.add_graph(graph_id, name)

    def _activate_graph(self, graph_id):
        if graph_id not in self.graphs:
            return

        self.active_graph_id = graph_id
        self.graph_view.set_active_graph(graph_id)
        self.points_panel.set_active_graph(graph_id)
        self.graph_view.set_mode(self.mode)
        self.update_calibrated_points()

    def add_graph(self, graph_id):
        graph_number = len(self.graphs) + 1
        color = self.graph_colors[(graph_number - 1) % len(self.graph_colors)]
        self._create_graph(graph_id, f"Graph {graph_number}", color)
        self._activate_graph(graph_id)
        self.start_points_mode()

    def select_graph(self, graph_id):
        self._activate_graph(graph_id)

    def remove_graph(self, graph_id):
        if len(self.graphs) <= 1 or graph_id not in self.graphs:
            return

        was_active = graph_id == self.active_graph_id
        self.graph_view.remove_graph(graph_id)
        self.points_panel.remove_graph(graph_id)
        del self.graphs[graph_id]

        if was_active:
            self._activate_graph(next(iter(self.graphs)))

    def set_graph_visibility(self, graph_id, visible):
        self.graph_view.set_graph_visible(graph_id, visible)


    def select_axis_point(self, name):
        self.axis_panel.set_current_selection(name)

        self.graph_view.start_axis_selection(name)

        self.selection_index = (
            self.selection_sequence.index(name)
        )

    def on_graph_clicked(self, x, y):
        self.update_calibrated_points()

        if self.selection_index >= len(self.selection_sequence):
            return

        current_point = self.selection_sequence[self.selection_index]

        print(
            f"{current_point}: "
            f"x={x:.2f}, y={y:.2f}"
        )

        self.selection_index += 1

        if self.selection_index >= len(self.selection_sequence):
            self.axis_panel.set_calibration_complete()
            return

        next_point = self.selection_sequence[self.selection_index]

        self.axis_panel.set_current_selection(next_point)

        self.graph_view.start_axis_selection(next_point)

    def reset_axis_selection(self):
        self.selection_index = 0

        self.graph_view.reset_axis_selection()
        self.graph_view.reset_all_data_points()
        for graph_id in self.graphs:
            self.points_panel.clear_points(graph_id)

        self.axis_panel.set_calibration_reset()

        self.axis_panel.set_current_selection("X1")
        self.graph_view.start_axis_selection("X1")

    def add_point_to_tree(self, number, x, y):
        value_x, value_y = self._convert_point(x, y)

        self.points_panel.add_point(
            self.active_graph_id,
            number,
            x,
            y,
            value_x,
            value_y,
        )

    def _convert_point(self, x, y):
        try:
            return pixel_to_data_coordinates(
                x,
                y,
                self.graph_view.axis_positions,
                self.axis_panel.get_values(),
                self.axis_panel.is_x_logarithmic(),
                self.axis_panel.is_y_logarithmic(),
            )
        except (KeyError, ValueError):
            return x, y

    def update_calibrated_points(self, *_args):
        for graph_id in self.graphs:
            self.points_panel.update_point_values(
                graph_id,
                self._convert_point,
            )

    def open_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open graph image",
            "",
            "PNG images (*.png);;"
            "JPEG images (*.jpg *.jpeg);;"
            "All images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )

        if not filename:
            return

        if self.graph_view.load_image(filename):
            for graph_id in self.graphs:
                self.points_panel.clear_points(graph_id)

    def reset_view(self):
        if self.graph_view.image_item is None:
            return

        self.graph_view.fitInView(
            self.graph_view.image_item,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

    def start_points_mode(self):
        self.mode = "points"

        self.graph_view.set_mode("points")

        self.axis_panel.set_points_mode()

    def start_calibration_mode(self):
        self.mode = "calibration"

        self.graph_view.set_mode("calibration")
        self.axis_panel.set_calibration_mode()
        self.update_calibrated_points()

        self.selection_index = 0
        self.axis_panel.set_current_selection("X1")
        self.graph_view.start_axis_selection("X1")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())