import csv
import importlib
import json
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QInputDialog,
    QMenu,
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
        self.export_active_button = QPushButton("Export Active")
        self.export_all_button = QPushButton("Export All")
        self.export_active_button.setMenu(self._create_export_menu(False))
        self.export_all_button.setMenu(self._create_export_menu(True))

        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.reset_view_button)
        toolbar.addWidget(self.export_active_button)
        toolbar.addWidget(self.export_all_button)

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

    def export_graphs(self, file_format, export_all):
        if not export_all and self.active_graph_id is None:
            return

        delimiter = ","
        if file_format == "txt":
            delimiter, accepted = QInputDialog.getText(
                self,
                "TXT delimiter",
                "Enter the delimiter:",
                text="\t",
            )
            if not accepted or not delimiter:
                return
            if delimiter == r"\t":
                delimiter = "\t"

        default_name = "graphs" if export_all else self.points_panel.get_graph_name(
            self.active_graph_id
        )
        extensions = {
            "csv": "CSV files (*.csv)",
            "xlsx": "Excel files (*.xlsx)",
            "json": "JSON files (*.json)",
            "npy": "Numpy files (*.npy)",
            "mat": "MATLAB files (*.mat)",
            "txt": "Text files (*.txt)",
        }
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export data",
            f"{default_name}.{file_format}",
            extensions[file_format],
        )

        if not filename:
            return

        try:
            rows = self._export_rows(export_all)
            if file_format in ("csv", "txt"):
                self._write_delimited(
                    filename,
                    rows,
                    delimiter,
                    export_all,
                    file_format,
                )
            elif file_format == "json":
                self._write_json(filename, rows, export_all)
            elif file_format == "xlsx":
                self._write_xlsx(filename, rows, export_all)
            elif file_format == "npy":
                self._write_npy(filename, rows, export_all)
            elif file_format == "mat":
                self._write_mat(filename, rows, export_all)
        except (ImportError, OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Export failed",
                str(error),
            )

    def _export_rows(self, export_all):
        rows = []
        graph_ids = self.graphs if export_all else [self.active_graph_id]
        for graph_id in graph_ids:
            graph_name = self.points_panel.get_graph_name(graph_id)
            for value_x, value_y in self.points_panel.get_points(graph_id):
                rows.append((graph_name, value_x, value_y))
        return rows

    def _write_delimited(
        self,
        filename,
        rows,
        delimiter,
        export_all,
        file_format,
    ):
        extension = ".txt" if file_format == "txt" else ".csv"
        if not filename.lower().endswith(extension):
            filename += extension

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=delimiter)
            writer.writerow(["graph", "x", "y"] if export_all else ["x", "y"])
            if export_all:
                writer.writerows(rows)
            else:
                writer.writerows(
                    [(value_x, value_y) for _name, value_x, value_y in rows]
                )

    def _write_json(self, filename, rows, export_all):
        if not filename.lower().endswith(".json"):
            filename += ".json"

        if export_all:
            data = [
                {"graph": graph_name, "x": value_x, "y": value_y}
                for graph_name, value_x, value_y in rows
            ]
        else:
            data = [
                {"x": value_x, "y": value_y}
                for _graph_name, value_x, value_y in rows
            ]

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def _write_xlsx(self, filename, rows, export_all):
        try:
            workbook_module = importlib.import_module("openpyxl")
        except ImportError as error:
            raise ImportError(
                "XLSX export requires the openpyxl package."
            ) from error

        workbook_class = workbook_module.Workbook

        if not filename.lower().endswith(".xlsx"):
            filename += ".xlsx"

        workbook = workbook_class()
        sheet = workbook.active
        sheet.append(["graph", "x", "y"] if export_all else ["x", "y"])
        for graph_name, value_x, value_y in rows:
            sheet.append(
                [graph_name, value_x, value_y]
                if export_all
                else [value_x, value_y]
            )
        workbook.save(filename)

    def _write_npy(self, filename, rows, export_all):
        try:
            numpy = importlib.import_module("numpy")
        except ImportError as error:
            raise ImportError(
                "Numpy export requires the numpy package."
            ) from error

        if not filename.lower().endswith(".npy"):
            filename += ".npy"

        if export_all:
            data = numpy.array(rows, dtype=object)
        else:
            data = numpy.array(
                [(value_x, value_y) for _name, value_x, value_y in rows],
                dtype=float,
            )
        numpy.save(filename, data, allow_pickle=True)

    def _write_mat(self, filename, rows, export_all):
        try:
            numpy = importlib.import_module("numpy")
            scipy_io = importlib.import_module("scipy.io")
        except ImportError as error:
            raise ImportError(
                "MATLAB export requires the numpy and scipy packages."
            ) from error

        if not filename.lower().endswith(".mat"):
            filename += ".mat"

        data = {
            "x": numpy.array([value_x for _name, value_x, _value_y in rows]),
            "y": numpy.array([value_y for _name, _value_x, value_y in rows]),
        }
        if export_all:
            data["graph"] = numpy.array(
                [graph_name for graph_name, _x, _y in rows],
                dtype=object,
            )
        scipy_io.savemat(filename, data)

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