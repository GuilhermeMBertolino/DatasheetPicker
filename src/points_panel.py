from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

class PointsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.points_tree = QTreeWidget()
        self.points_tree.setHeaderLabels(["Pontos selecionados"])
        self.points_tree.setRootIsDecorated(True)

        self.points_root = QTreeWidgetItem(
            self.points_tree,
            ["Pontos"],
        )
        self.points_root.setExpanded(True)

        self.tabs.addTab(self.points_tree, "Pontos")
        layout.addWidget(self.tabs)

    def add_point(self, number, pixel_x, pixel_y, value_x, value_y):
        point_item = QTreeWidgetItem(
            self.points_root,
            [
                f"Ponto {number}: "
                f"x={value_x:.6g}, y={value_y:.6g} "
                f"(pixel: {pixel_x:.2f}, {pixel_y:.2f})"
            ],
        )
        point_item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {
                "pixel": (pixel_x, pixel_y),
                "value": (value_x, value_y),
            },
        )
        self.points_root.setExpanded(True)

    def clear_points(self):
        self.points_root.takeChildren()