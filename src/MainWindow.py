from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QToolBar,
    QWidget,
)

from AxisPanel import AxisPanel
from calibration import pixel_to_data_coordinates
from ExportService import ExportService
from graph_models import DataPoint, GraphCollection
from GraphView import GraphView
from PointsPanel import PointsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Datasheet Picker")
        self.resize(1400, 900)

        self.selection_sequence = ["X1", "X2", "Y1", "Y2"]
        self.selection_index = 0
        self.mode = "calibration"
        self.graphs = GraphCollection()
        self.active_graph_id = None
        self.export_service = ExportService()
        self.graph_colors = [
            "#2ecc71",
            "#e67e22",
            "#3498db",
            "#e84393",
            "#f1c40f",
        ]

        self._create_ui()
        self._connect_signals()

        graph = self.graphs.add("Graph 1", self.graph_colors[0])
        self.graph_view.add_graph(graph.graph_id, graph.color)
        self.points_panel.add_graph(graph.graph_id, graph.name)
        self._activate_graph(graph.graph_id)
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
        self.export_active_button = QPushButton("Export Active")
        self.export_all_button = QPushButton("Export All")
        self.export_active_button.setMenu(self._create_export_menu(False))
        self.export_all_button.setMenu(self._create_export_menu(True))

        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.reset_view_button)
        toolbar.addWidget(self.export_active_button)
        toolbar.addWidget(self.export_all_button)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

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
        self.graph_view.point_added.connect(self.add_point)
        self.points_panel.graph_added.connect(self.add_graph)
        self.points_panel.graph_selected.connect(self.select_graph)
        self.points_panel.graph_removed.connect(self.remove_graph)
        self.points_panel.graph_visibility_changed.connect(
            self.set_graph_visibility
        )

    def _create_export_menu(self, export_all):
        menu = QMenu(self)
        formats = (
            ("CSV", "csv"),
            ("Excel (XLSX)", "xlsx"),
            ("JSON", "json"),
            ("Numpy (NPY)", "npy"),
            ("MATLAB (MAT)", "mat"),
            ("TXT", "txt"),
        )
        for label, file_format in formats:
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, selected_format=file_format:
                self.export_graphs(selected_format, export_all)
            )
        return menu

    def _activate_graph(self, graph_id):
        if graph_id not in self.graphs:
            return
        self.active_graph_id = graph_id
        self.graph_view.set_active_graph(graph_id)
        self.points_panel.set_active_graph(graph_id)
        self.graph_view.set_mode(self.mode)
        self.update_calibrated_points()

    def add_graph(self, _graph_id):
        graph_number = len(self.graphs) + 1
        color = self.graph_colors[(graph_number - 1) % len(self.graph_colors)]
        graph = self.graphs.add(f"Graph {graph_number}", color)
        self.graph_view.add_graph(graph.graph_id, graph.color)
        self.points_panel.add_graph(graph.graph_id, graph.name)
        self._activate_graph(graph.graph_id)
        self.start_points_mode()

    def select_graph(self, graph_id):
        self._activate_graph(graph_id)

    def remove_graph(self, graph_id):
        if len(self.graphs) <= 1 or graph_id not in self.graphs:
            return
        was_active = graph_id == self.active_graph_id
        self.graph_view.remove_graph(graph_id)
        self.points_panel.remove_graph(graph_id)
        self.graphs.remove(graph_id)
        if was_active:
            self._activate_graph(next(iter(self.graphs)))

    def set_graph_visibility(self, graph_id, visible):
        graph = self.graphs.get(graph_id)
        graph.visible = visible
        self.graph_view.set_graph_visible(graph_id, visible)

    def select_axis_point(self, name):
        self.axis_panel.set_current_selection(name)
        self.graph_view.start_axis_selection(name)
        self.selection_index = self.selection_sequence.index(name)

    def on_graph_clicked(self, _x, _y):
        self.update_calibrated_points()
        if self.selection_index >= len(self.selection_sequence):
            return
        self.selection_index += 1
        if self.selection_index >= len(self.selection_sequence):
            self.axis_panel.set_calibration_complete()
            return
        next_point = self.selection_sequence[self.selection_index]
        self.axis_panel.set_current_selection(next_point)
        self.graph_view.start_axis_selection(next_point)

    def add_point(self, _number, pixel_x, pixel_y):
        if self.active_graph_id is None:
            return
        value_x, value_y = self._convert_point(pixel_x, pixel_y)
        graph = self.graphs.get(self.active_graph_id)
        graph.points.append(DataPoint(pixel_x, pixel_y, value_x, value_y))
        self._refresh_graph(graph)

    def _convert_point(self, pixel_x, pixel_y):
        try:
            return pixel_to_data_coordinates(
                pixel_x,
                pixel_y,
                self.graph_view.axis_positions,
                self.axis_panel.get_values(),
                self.axis_panel.is_x_logarithmic(),
                self.axis_panel.is_y_logarithmic(),
            )
        except (KeyError, ValueError):
            return pixel_x, pixel_y

    def update_calibrated_points(self, *_args):
        for graph in self.graphs.values():
            for point in graph.points:
                point.value_x, point.value_y = self._convert_point(
                    point.pixel_x,
                    point.pixel_y,
                )
            self._refresh_graph(graph)

    def _refresh_graph(self, graph):
        self.points_panel.set_points(
            graph.graph_id,
            [(point.value_x, point.value_y) for point in graph.points],
        )

    def reset_axis_selection(self):
        self.selection_index = 0
        self.graph_view.reset_axis_selection()
        self.graph_view.reset_all_data_points()
        for graph in self.graphs.values():
            graph.points.clear()
            self._refresh_graph(graph)
        self.axis_panel.set_calibration_reset()
        self.axis_panel.set_current_selection("X1")
        self.graph_view.start_axis_selection("X1")

    def open_image(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open graph image",
            "",
            "PNG images (*.png);;JPEG images (*.jpg *.jpeg);;"
            "All images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not filename or not self.graph_view.load_image(filename):
            return
        for graph in self.graphs.values():
            graph.points.clear()
            self._refresh_graph(graph)

    def reset_view(self):
        if self.graph_view.image_item is not None:
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

    def export_graphs(self, file_format, export_all):
        if not export_all and self.active_graph_id is None:
            return

        delimiter = ","
        if file_format == "txt":
            delimiter, accepted = QInputDialog.getText(
                self, "TXT delimiter", "Enter the delimiter:", text="\t"
            )
            if not accepted or not delimiter:
                return
            if delimiter == r"\t":
                delimiter = "\t"

        graph_ids = list(self.graphs) if export_all else [self.active_graph_id]
        default_name = "graphs" if export_all else self.graphs.get(
            self.active_graph_id
        ).name
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export data",
            f"{default_name}.{file_format}",
            f"{file_format.upper()} files (*.{file_format})",
        )
        if not filename:
            return

        try:
            self.export_service.export(
                filename,
                file_format,
                self.graphs,
                graph_ids,
                delimiter,
            )
        except (ImportError, OSError, ValueError) as error:
            QMessageBox.critical(self, "Export failed", str(error))
