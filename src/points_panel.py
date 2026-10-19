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
                f"Point {number}: "
                f"x={value_x:.6g}, y={value_y:.6g} "
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

    def update_point_values(self, value_converter):
        for index in range(self.points_root.childCount()):
            point_item = self.points_root.child(index)
            point_data = point_item.data(0, Qt.ItemDataRole.UserRole)
            pixel_x, pixel_y = point_data["pixel"]
            value_x, value_y = value_converter(pixel_x, pixel_y)

            point_data["value"] = (value_x, value_y)
            point_item.setData(0, Qt.ItemDataRole.UserRole, point_data)
            point_item.setText(
                0,
                f"Point {index + 1}: "
                f"x={value_x:.6g}, y={value_y:.6g} "
            )