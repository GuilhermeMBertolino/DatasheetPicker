from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PointsPanel(QWidget):
    graph_added = Signal(str)
    graph_selected = Signal(str)
    graph_removed = Signal(str)
    graph_visibility_changed = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph_items = {}
        self.next_graph_number = 2

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.points_tree = QTreeWidget()
        self.points_tree.setHeaderLabels(["Graphs and points"])
        self.points_tree.setRootIsDecorated(True)
        self.tabs.addTab(self.points_tree, "Points")
        layout.addWidget(self.tabs)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add graph")
        self.remove_button = QPushButton("Remove graph")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        layout.addLayout(buttons_layout)

        self.add_button.clicked.connect(self._add_graph)
        self.remove_button.clicked.connect(self._remove_selected_graph)
        self.points_tree.itemClicked.connect(self._handle_item_clicked)
        self.points_tree.itemChanged.connect(self._handle_item_changed)

    def add_graph(self, graph_id, name):
        graph_item = QTreeWidgetItem(self.points_tree, [name])
        graph_item.setData(0, Qt.ItemDataRole.UserRole, graph_id)
        graph_item.setFlags(
            graph_item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsSelectable
        )
        graph_item.setCheckState(0, Qt.CheckState.Checked)
        graph_item.setExpanded(True)
        self.graph_items[graph_id] = graph_item
        self.points_tree.setCurrentItem(graph_item)

    def remove_graph(self, graph_id):
        graph_item = self.graph_items.pop(graph_id, None)
        if graph_item is None:
            return
        index = self.points_tree.indexOfTopLevelItem(graph_item)
        self.points_tree.takeTopLevelItem(index)

    def set_active_graph(self, graph_id):
        graph_item = self.graph_items.get(graph_id)
        if graph_item is not None:
            self.points_tree.setCurrentItem(graph_item)

    def add_point(self, graph_id, number, pixel_x, pixel_y, value_x, value_y):
        graph_item = self.graph_items[graph_id]
        point_item = QTreeWidgetItem(
            graph_item,
            [
                f"Point {number}: "
                f"x={value_x:.6g}, y={value_y:.6g}"
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
        graph_item.setExpanded(True)

    def clear_points(self, graph_id):
        graph_item = self.graph_items[graph_id]
        while graph_item.childCount():
            graph_item.takeChild(0)

    def update_point_values(self, graph_id, value_converter):
        graph_item = self.graph_items[graph_id]
        for index in range(graph_item.childCount()):
            point_item = graph_item.child(index)
            point_data = point_item.data(0, Qt.ItemDataRole.UserRole)
            pixel_x, pixel_y = point_data["pixel"]
            value_x, value_y = value_converter(pixel_x, pixel_y)
            point_data["value"] = (value_x, value_y)
            point_item.setData(0, Qt.ItemDataRole.UserRole, point_data)
            point_item.setText(
                0,
                f"Point {index + 1}: "
                f"x={value_x:.6g}, y={value_y:.6g}",
            )

    def get_points(self, graph_id):
        graph_item = self.graph_items[graph_id]
        points = []

        for index in range(graph_item.childCount()):
            point_item = graph_item.child(index)
            point_data = point_item.data(0, Qt.ItemDataRole.UserRole)
            points.append(point_data["value"])

        return points

    def get_graph_name(self, graph_id):
        return self.graph_items[graph_id].text(0)

    def _add_graph(self):
        graph_id = f"graph-{self.next_graph_number}"
        self.next_graph_number += 1
        self.graph_added.emit(graph_id)

    def _remove_selected_graph(self):
        graph_item = self.points_tree.currentItem()
        if graph_item is None:
            return

        if graph_item.parent() is not None:
            graph_item = graph_item.parent()

        graph_id = graph_item.data(0, Qt.ItemDataRole.UserRole)
        self.graph_removed.emit(graph_id)

    def _handle_item_clicked(self, item, _column):
        if item.parent() is not None:
            item = item.parent()
        graph_id = item.data(0, Qt.ItemDataRole.UserRole)
        if graph_id in self.graph_items:
            self.graph_selected.emit(graph_id)

    def _handle_item_changed(self, item, _column):
        if item.parent() is not None:
            return
        graph_id = item.data(0, Qt.ItemDataRole.UserRole)
        if graph_id in self.graph_items:
            visible = item.checkState(0) == Qt.CheckState.Checked
            self.graph_visibility_changed.emit(graph_id, visible)