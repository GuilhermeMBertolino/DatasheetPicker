from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

class AxisPanel(QWidget):
    select_point = Signal(str)
    reset = Signal()
    mode_points = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        self.selection_label = QLabel("Selecting: X1")

        layout.addWidget(self.selection_label)

        x_group = QGroupBox("X Axis")
        x_layout = QFormLayout(x_group)

        self.x1_value = self._create_spinbox()
        self.x2_value = self._create_spinbox()

        x_layout.addRow("X1:", self.x1_value)

        x_layout.addRow("X2:", self.x2_value)

        self.x_logarithmic = QCheckBox("Logarithmic X Axis")

        x_layout.addRow(self.x_logarithmic)

        self.x1_button = QPushButton("Select X1")

        self.x2_button = QPushButton("Select X2")

        x_layout.addRow(self.x1_button)

        x_layout.addRow(self.x2_button)

        y_group = QGroupBox("Y Axis")
        y_layout = QFormLayout(y_group)

        self.y1_value = self._create_spinbox()
        self.y2_value = self._create_spinbox()

        y_layout.addRow("Y1:", self.y1_value)

        y_layout.addRow("Y2:", self.y2_value)

        self.y_logarithmic = QCheckBox("Logarithmic Y Axis")

        y_layout.addRow(self.y_logarithmic)

        self.y1_button = QPushButton("Select Y1")

        self.y2_button = QPushButton("Select Y2")

        y_layout.addRow(self.y1_button)

        y_layout.addRow(self.y2_button)

        self.reset_button = QPushButton("Reset Axis Selection")

        self.finish_button = QPushButton("Finish Calibration")

        self.finish_button.setEnabled(False)

        layout.addWidget(x_group)
        layout.addWidget(y_group)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.finish_button)

        layout.addStretch()

        self.x1_button.clicked.connect(lambda: self._select("X1"))

        self.x2_button.clicked.connect(lambda: self._select("X2"))

        self.y1_button.clicked.connect(lambda: self._select("Y1"))

        self.y2_button.clicked.connect(lambda: self._select("Y2"))

        self.reset_button.clicked.connect(self.reset.emit)

        self.finish_button.clicked.connect(self.mode_points.emit)

    def _create_spinbox(self):
        spinbox = QDoubleSpinBox()

        spinbox.setRange(-1e12, 1e12)

        spinbox.setDecimals(6)
        spinbox.setSingleStep(1.0)

        return spinbox

    def _select(self, name):
        self.set_current_selection(name)
        self.select_point.emit(name)

    def set_current_selection(self, name):
        self.selection_label.setText(
            f"Selecting: {name}"
        )

        buttons = {
            "X1": self.x1_button,
            "X2": self.x2_button,
            "Y1": self.y1_button,
            "Y2": self.y2_button,
        }

        for button in buttons.values():
            button.setChecked(False)
            button.setStyleSheet("")

        button = buttons[name]

        button.setCheckable(True)
        button.setChecked(True)

        button.setStyleSheet("font-weight: bold;")

    def get_values(self):
        return {
            "X1": self.x1_value.value(),
            "X2": self.x2_value.value(),
            "Y1": self.y1_value.value(),
            "Y2": self.y2_value.value(),
        }

    def is_x_logarithmic(self):
        return self.x_logarithmic.isChecked()

    def is_y_logarithmic(self):
        return self.y_logarithmic.isChecked()

    def set_calibration_complete(self):
        self.selection_label.setText("Axis calibration complete.")
        self.finish_button.setEnabled(True)

    def set_points_mode(self):
        self.selection_label.setText("Mode: Points")
        self.finish_button.setEnabled(False)