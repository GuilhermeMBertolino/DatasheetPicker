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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Datasheet Picker")
        self.resize(1400, 900)

        self.selection_sequence = ["X1", "X2", "Y1", "Y2"]

        self.selection_index = 0

        self._create_ui()
        self._connect_signals()

        # Start calibration at X1
        self.axis_panel.set_current_selection("X1")
        self.graph_view.start_axis_selection("X1")

    def _create_ui(self):
        central = QWidget()
        layout = QHBoxLayout(central)

        self.axis_panel = AxisPanel()
        self.graph_view = GraphView()

        self.axis_panel.setMinimumWidth(260)
        self.axis_panel.setMaximumWidth(320)

        layout.addWidget(self.axis_panel)
        layout.addWidget(self.graph_view)

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

        self.axis_panel.select_point.connect(self.graph_view.start_axis_selection)

        self.axis_panel.reset.connect(self.reset_axis_selection)

        self.graph_view.clicked.connect(self.on_graph_clicked)

    def on_graph_clicked(self, x, y):
        if self.selection_index >= len(self.selection_sequence):
            return

        current_point = self.selection_sequence[self.selection_index]

        print(
            f"{current_point}: "
            f"x={x:.2f}, y={y:.2f}"
        )

        # Avança para o próximo ponto
        self.selection_index += 1

        if self.selection_index >= len(self.selection_sequence):
            self.axis_panel.set_selection_complete()
            return

        next_point = self.selection_sequence[self.selection_index]

        self.axis_panel.set_current_selection(next_point)

        self.graph_view.start_axis_selection(next_point)

    def reset_axis_selection(self):
        self.selection_index = 0

        self.graph_view.reset_axis_selection()

        self.axis_panel.set_current_selection("X1")

        self.graph_view.start_axis_selection("X1")

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

        self.graph_view.load_image(
            filename
        )

    def reset_view(self):
        if self.graph_view.image_item is None:
            return

        self.graph_view.fitInView(
            self.graph_view.image_item,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())