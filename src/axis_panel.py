from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
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

    def __init__(self, parent=None):
        super().__init__(parent)

        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        x_group = QGroupBox("X Axis")
        x_layout = QFormLayout(x_group)

        self.x1_value = self._create_spinbox()
        self.x2_value = self._create_spinbox()

        x_layout.addRow("X1:", self.x1_value)
        x_layout.addRow("X2:", self.x2_value)

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

        self.y1_button = QPushButton("Select Y1")
        self.y2_button = QPushButton("Select Y2")

        y_layout.addRow(self.y1_button)
        y_layout.addRow(self.y2_button)

        self.status_label = QLabel(
            "Enter the axis values and select their positions."
        )

        self.reset_button = QPushButton(
            "Reset Axis Selection"
        )

        layout.addWidget(self.status_label)
        layout.addWidget(x_group)
        layout.addWidget(y_group)
        layout.addWidget(self.reset_button)

        layout.addStretch()

        self.x1_button.clicked.connect(lambda: self._select("X1"))

        self.x2_button.clicked.connect(lambda: self._select("X2"))

        self.y1_button.clicked.connect(lambda: self._select("Y1"))

        self.y2_button.clicked.connect(lambda: self._select("Y2"))

        self.reset_button.clicked.connect(self.reset.emit)

    def _create_spinbox(self):
        spinbox = QDoubleSpinBox()

        spinbox.setRange(-1e12, 1e12)

        spinbox.setDecimals(6)
        spinbox.setSingleStep(1.0)

        return spinbox

    def _select(self, name):
        self.status_label.setText(f"Click on the graph to select {name}.")

        self.select_point.emit(name)

    def get_values(self):
        return {
            "X1": self.x1_value.value(),
            "X2": self.x2_value.value(),
            "Y1": self.y1_value.value(),
            "Y2": self.y2_value.value(),
        }