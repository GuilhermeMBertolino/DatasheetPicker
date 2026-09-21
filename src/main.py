import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from graph_view import GraphView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Datasheet Picker")
        self.resize(1400, 900)

        self._create_central_widget()
        self._create_toolbar()
        self._connect_signals()

    def _create_central_widget(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.graph_view = GraphView()

        self.status_label = QLabel(
            "Open an image to begin."
        )

        layout.addWidget(self.graph_view)
        layout.addWidget(self.status_label)

        self.setCentralWidget(central_widget)

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)

        self.open_button = QPushButton("Open Image")
        self.reset_button = QPushButton("Reset View")

        toolbar.addWidget(self.open_button)
        toolbar.addWidget(self.reset_button)

        self.addToolBar(
            Qt.ToolBarArea.TopToolBarArea,
            toolbar,
        )

    def _connect_signals(self):
        self.open_button.clicked.connect(
            self.open_image
        )

        self.reset_button.clicked.connect(
            self.reset_view
        )

        self.graph_view.clicked.connect(
            self.on_graph_clicked
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

        success = self.graph_view.load_image(
            filename
        )

        if success:
            self.status_label.setText(
                f"Loaded: {filename}"
            )
        else:
            self.status_label.setText(
                "Failed to load image."
            )

    def reset_view(self):
        if self.graph_view.image_item is None:
            return

        self.graph_view.fitInView(
            self.graph_view.image_item,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

        self.status_label.setText(
            "View reset."
        )

    def on_graph_clicked(self, x, y):
        self.status_label.setText(
            f"Pixel coordinates: "
            f"x = {x:.1f}, y = {y:.1f}"
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())