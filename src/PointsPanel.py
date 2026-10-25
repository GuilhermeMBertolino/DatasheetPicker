from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PointsTree(QTreeWidget):
    points_reordered = Signal(str, list)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            super().mouseMoveEvent(event)
            return

        previous_current = self.currentItem()
        previous_selected = list(self.selectedItems())
        super().mouseMoveEvent(event)

        self.blockSignals(True)
        self.clearSelection()
        for item in previous_selected:
            item.setSelected(True)
        self.setCurrentItem(previous_current)
        self.blockSignals(False)

    def dropEvent(self, event):
        dragged_item = self.currentItem()
        if dragged_item is None or dragged_item.parent() is None:
            event.ignore()
            return

        graph_item = dragged_item.parent()
        target_item = self.itemAt(event.position().toPoint())
        target_graph = (
            target_item.parent()
            if target_item and target_item.parent()
            else target_item
        )
        if target_graph is not graph_item:
            event.ignore()
            return

        graph_id = graph_item.data(2, Qt.ItemDataRole.UserRole)
        super().dropEvent(event)

        if dragged_item.parent() is not graph_item:
            return

        order = [
            graph_item.child(index).data(0, Qt.ItemDataRole.UserRole)
            for index in range(graph_item.childCount())
        ]
        self.points_reordered.emit(graph_id, order)


class PointsPanel(QWidget):
    graph_added = Signal(str)
    graph_selected = Signal(str)
    graph_removed = Signal(str)
    graph_visibility_changed = Signal(str, bool)
    point_removed = Signal(str, int)
    points_reordered = Signal(str, list)
    graph_color_changed = Signal(str, str)
    graph_renamed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph_items = {}
        self.color_buttons = {}
        self.next_graph_number = 2

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.points_tree = PointsTree()
        self.points_tree.setColumnCount(3)
        self.points_tree.setHeaderLabels(["", "Color", "Graphs and points"])
        self.points_tree.header().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.points_tree.header().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.points_tree.header().setStretchLastSection(True)
        self.points_tree.setRootIsDecorated(True)
        self.points_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.tabs.addTab(self.points_tree, "Points")
        layout.addWidget(self.tabs)

        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add graph")
        self.remove_button = QPushButton("Remove graph")
        self.remove_point_button = QPushButton("Remove point")
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addWidget(self.remove_point_button)
        layout.addLayout(buttons_layout)

        self.add_button.clicked.connect(self._add_graph)
        self.remove_button.clicked.connect(self._remove_selected_graph)
        self.remove_point_button.clicked.connect(self._remove_selected_point)
        self.points_tree.itemClicked.connect(self._handle_item_clicked)
        self.points_tree.itemChanged.connect(self._handle_item_changed)
        self.points_tree.points_reordered.connect(self.points_reordered)

    def add_graph(self, graph_id, name, color):
        graph_item = QTreeWidgetItem(
            self.points_tree,
            ["", "", name],
        )
        graph_item.setData(2, Qt.ItemDataRole.UserRole, graph_id)
        graph_item.setFlags(
            graph_item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
        graph_item.setCheckState(0, Qt.CheckState.Checked)
        graph_item.setExpanded(True)
        self.graph_items[graph_id] = graph_item

        color_button = QPushButton()
        color_button.setFixedSize(18, 14)
        color_button.setCursor(Qt.CursorShape.PointingHandCursor)
        color_button.clicked.connect(
            lambda: self._choose_graph_color(graph_id)
        )
        self.color_buttons[graph_id] = color_button
        self._set_color_button(color_button, color)
        self.points_tree.setItemWidget(graph_item, 1, color_button)
        self.points_tree.setCurrentItem(graph_item)

    def remove_graph(self, graph_id):
        graph_item = self.graph_items.pop(graph_id, None)
        if graph_item is None:
            return
        index = self.points_tree.indexOfTopLevelItem(graph_item)
        self.points_tree.takeTopLevelItem(index)
        self.color_buttons.pop(graph_id, None)

    def set_active_graph(self, graph_id):
        graph_item = self.graph_items.get(graph_id)
        if graph_item is not None:
            self.points_tree.setCurrentItem(graph_item)

    def set_points(self, graph_id, points):
        graph_item = self.graph_items[graph_id]
        while graph_item.childCount():
            graph_item.takeChild(0)

        for index, (value_x, value_y) in enumerate(points, start=1):
            point_item = QTreeWidgetItem(
                graph_item,
                [
                    "",
                    "",
                    f"Point {index}: x={value_x:.6g}, y={value_y:.6g}",
                ],
            )
            point_item.setFlags(
                point_item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled
            )
            point_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                index - 1,
            )
        graph_item.setExpanded(True)

    def update_point(self, graph_id, index, value_x, value_y):
        point_item = self.graph_items[graph_id].child(index)
        point_item.setText(
            2,
            f"Point {index + 1}: x={value_x:.6g}, y={value_y:.6g}",
        )

    def refresh_point_indices(self, graph_id):
        graph_item = self.graph_items[graph_id]
        for index in range(graph_item.childCount()):
            graph_item.child(index).setData(
                0,
                Qt.ItemDataRole.UserRole,
                index,
            )

    def set_graph_name(self, graph_id, name):
        self.graph_items[graph_id].setText(2, name)

    def _set_color_button(self, button, color):
        button.setProperty("color", color)
        button.setStyleSheet(
            f"background-color: {color}; border: 1px solid #333;"
        )

    def _choose_graph_color(self, graph_id):
        button = self.color_buttons[graph_id]
        color = QColorDialog.getColor(
            QColor(button.property("color")),
            self,
            "Select graph color",
        )
        if not color.isValid():
            return

        color_name = color.name()
        self._set_color_button(button, color_name)
        self.graph_color_changed.emit(graph_id, color_name)

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
        graph_id = graph_item.data(2, Qt.ItemDataRole.UserRole)
        self.graph_removed.emit(graph_id)

    def _remove_selected_point(self):
        point_item = self.points_tree.currentItem()
        if point_item is None or point_item.parent() is None:
            return
        graph_item = point_item.parent()
        graph_id = graph_item.data(2, Qt.ItemDataRole.UserRole)
        point_index = point_item.data(0, Qt.ItemDataRole.UserRole)
        self.point_removed.emit(graph_id, point_index)

    def _handle_item_clicked(self, item, _column):
        if item.parent() is not None:
            return
        graph_id = item.data(2, Qt.ItemDataRole.UserRole)
        if graph_id in self.graph_items:
            self.graph_selected.emit(graph_id)

    def _handle_item_changed(self, item, column):
        if item.parent() is not None:
            return
        graph_id = item.data(2, Qt.ItemDataRole.UserRole)
        if graph_id not in self.graph_items:
            return
        if column == 2:
            self.graph_renamed.emit(graph_id, item.text(2).strip())
        visible = item.checkState(0) == Qt.CheckState.Checked
        self.graph_visibility_changed.emit(graph_id, visible)