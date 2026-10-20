from PySide6.QtCore import QPoint, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsItemGroup,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
)

class GraphView(QGraphicsView):
    clicked = Signal(float, float)
    point_added = Signal(int, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.image_item = None

        self.selection_mode = None
        self.graph_layers = {}
        self.active_graph_id = None
        self.axis_markers = {}
        self.axis_positions = {}
        self.axis_lines = {}

        self.mode = "calibration"

        self.data_points = []
        self.data_markers = []
        self.data_lines = []

        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._set_canvas_cursor(Qt.CursorShape.CrossCursor)

        self.magnifier_enabled = False
        self.magnifier_size = 180
        self.magnifier_label = QLabel(self.viewport())
        self.magnifier_label.setFixedSize(
            self.magnifier_size,
            self.magnifier_size,
        )
        self.magnifier_label.setStyleSheet(
            "background: white; border: 2px solid #333;"
        )
        self.magnifier_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.magnifier_label.hide()

    def set_magnifier_enabled(self, enabled):
        self.magnifier_enabled = enabled
        if not enabled:
            self.magnifier_label.hide()
            self._set_canvas_cursor(Qt.CursorShape.CrossCursor)

    def _set_canvas_cursor(self, cursor_shape):
        self.setCursor(cursor_shape)
        self.viewport().setCursor(cursor_shape)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.position().toPoint())
        if self.magnifier_enabled and self._inside_image(scene_pos):
            self._update_magnifier(
                scene_pos,
                event.position().toPoint(),
            )
        else:
            self.magnifier_label.hide()
            self._set_canvas_cursor(Qt.CursorShape.CrossCursor)

        super().mouseMoveEvent(event)
        QTimer.singleShot(0, self._restore_cursor)

    def leaveEvent(self, event):
        self.magnifier_label.hide()
        self._set_canvas_cursor(Qt.CursorShape.CrossCursor)
        super().leaveEvent(event)

    def _update_magnifier(self, scene_pos, viewport_pos):
        self._set_canvas_cursor(Qt.CursorShape.BlankCursor)
        source_radius = 25
        source_rect = QRectF(
            scene_pos.x() - source_radius,
            scene_pos.y() - source_radius,
            source_radius * 2,
            source_radius * 2,
        )

        display = QPixmap(self.magnifier_label.size())
        display.fill(Qt.GlobalColor.white)
        painter = QPainter(display)
        target_rect = QRectF(
            4,
            4,
            self.magnifier_size - 8,
            self.magnifier_size - 8,
        )
        self.scene.render(painter, target_rect, source_rect)
        painter.setPen(QPen(Qt.GlobalColor.red, 1))
        center_x = display.width() // 2
        center_y = display.height() // 2
        painter.drawLine(center_x - 10, center_y, center_x + 10, center_y)
        painter.drawLine(center_x, center_y - 10, center_x, center_y + 10)
        painter.end()

        self.magnifier_label.setPixmap(display)
        self._move_magnifier(viewport_pos)
        self.magnifier_label.show()

    def _move_magnifier(self, cursor_pos):
        viewport_rect = self.viewport().rect()
        position = cursor_pos - QPoint(
            self.magnifier_size // 2,
            self.magnifier_size // 2,
        )
        position.setX(max(0, position.x()))
        position.setY(max(0, position.y()))
        position.setX(
            min(position.x(), viewport_rect.width() - self.magnifier_size)
        )
        position.setY(
            min(position.y(), viewport_rect.height() - self.magnifier_size)
        )
        self.magnifier_label.move(position)

    def add_graph(self, graph_id, color=None):
        self.graph_layers[graph_id] = {
            "data_points": [],
            "data_markers": [],
            "data_lines": [],
            "visible": True,
            "color": QColor(color) if color else QColor("#2ecc71"),
        }
        if self.active_graph_id is None:
            self.set_active_graph(graph_id)

    def set_active_graph(self, graph_id):
        if graph_id not in self.graph_layers:
            return

        self.active_graph_id = graph_id
        layer = self.graph_layers[graph_id]
        self.data_points = layer["data_points"]
        self.data_markers = layer["data_markers"]
        self.data_lines = layer["data_lines"]
        self._bind_layer_visibility(layer)

    def remove_graph(self, graph_id):
        layer = self.graph_layers.pop(graph_id, None)
        if layer is None:
            return

        for item in self._layer_items(layer):
            self.scene.removeItem(item)

        if self.active_graph_id == graph_id:
            self.active_graph_id = None
            if self.graph_layers:
                self.set_active_graph(next(iter(self.graph_layers)))

    def set_graph_visible(self, graph_id, visible):
        layer = self.graph_layers.get(graph_id)
        if layer is None:
            return

        layer["visible"] = visible
        self._bind_layer_visibility(layer)

    def _layer_items(self, layer):
        return (
            layer["data_markers"]
            + layer["data_lines"]
        )

    def _bind_layer_visibility(self, layer):
        for item in self._layer_items(layer):
            item.setVisible(layer["visible"])

    def load_image(self, filename):
        pixmap = QPixmap(filename)

        if pixmap.isNull():
            return False

        self.scene.clear()

        self.axis_markers.clear()
        self.axis_positions.clear()
        self.axis_lines.clear()

        for layer in self.graph_layers.values():
            layer["data_points"].clear()
            layer["data_markers"].clear()
            layer["data_lines"].clear()

        if self.active_graph_id is not None:
            self.set_active_graph(self.active_graph_id)

        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)

        self.scene.setSceneRect(
            self.image_item.boundingRect()
        )

        self.fitInView(
            self.image_item,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

        return True

    def wheelEvent(self, event):
        zoom_factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            QTimer.singleShot(0, self._restore_cursor)
            return

        scene_pos = self.mapToScene(event.position().toPoint())

        if not self._inside_image(scene_pos):
            super().mousePressEvent(event)
            QTimer.singleShot(0, self._restore_cursor)
            return

        if self.mode == "calibration":
            self._handle_calibration_click(scene_pos)

        elif self.mode == "points":
            self._handle_point_click(scene_pos)
            if self.magnifier_enabled:
                self._set_canvas_cursor(Qt.CursorShape.BlankCursor)
            else:
                QTimer.singleShot(0, self._restore_cursor)
            return

        super().mousePressEvent(event)
        QTimer.singleShot(0, self._restore_cursor)

    def _restore_cursor(self):
        if not self.magnifier_enabled:
            self._set_canvas_cursor(Qt.CursorShape.CrossCursor)

    def start_axis_selection(self, name):
        self.selection_mode = name

    def set_axis_marker(self, name, x, y):
        if self.active_graph_id is None:
            return

        if name in self.axis_markers:
            self.scene.removeItem(self.axis_markers[name])

        self.axis_positions[name] = (x, y)

        if name in ("X1", "X2"):
            color = Qt.GlobalColor.red
        else:
            color = Qt.GlobalColor.blue

        if name in ("X1", "Y1"):
            marker = self._create_cross(x, y, color)
        else:
            marker = self._create_circle(x, y, color)

        self.scene.addItem(marker)

        marker.setZValue(10)

        self.axis_markers[name] = marker

        self._update_axis_line(name)

    def _update_axis_line(self, name):
        if name in ("X1", "X2"):
            point1_name = "X1"
            point2_name = "X2"
            color = Qt.GlobalColor.red
        else:
            point1_name = "Y1"
            point2_name = "Y2"
            color = Qt.GlobalColor.blue

        if (point1_name not in self.axis_positions
            or point2_name not in self.axis_positions):
            return

        x1, y1 = self.axis_positions[point1_name]
        x2, y2 = self.axis_positions[point2_name]

        axis_name = point1_name[0]

        if axis_name in self.axis_lines:
            self.scene.removeItem(self.axis_lines[axis_name])

        line = QGraphicsLineItem(x1, y1, x2, y2,)

        pen = QPen(color)
        pen.setWidth(2)

        line.setPen(pen)

        line.setZValue(5)

        self.scene.addItem(line)

        self.axis_lines[axis_name] = line

    def set_mode(self, mode):
        self.mode = mode

    def reset_axis_selection(self):
        for marker in self.axis_markers.values():
            self.scene.removeItem(marker)

        for line in self.axis_lines.values():
            self.scene.removeItem(line)

        self.axis_markers.clear()
        self.axis_positions.clear()
        self.axis_lines.clear()

        self.selection_mode = None

    def reset_data_points(self):
        for marker in self.data_markers:
            self.scene.removeItem(marker)

        for line in self.data_lines:
            self.scene.removeItem(line)

        self.data_points.clear()
        self.data_markers.clear()
        self.data_lines.clear()

    def reset_all_data_points(self):
        active_graph_id = self.active_graph_id
        for graph_id in self.graph_layers:
            self.set_active_graph(graph_id)
            self.reset_data_points()
        if active_graph_id is not None:
            self.set_active_graph(active_graph_id)

    def remove_last_data_point(self):
        if not self.data_points:
            return False

        marker = self.data_markers.pop()
        self.scene.removeItem(marker)
        self.data_points.pop()

        if self.data_lines:
            line = self.data_lines.pop()
            self.scene.removeItem(line)

        return True

    def _create_cross(self, x, y, color, size=2):
        pen = QPen(color)
        pen.setWidth(1)

        line1 = QGraphicsLineItem(
            x - size,
            y - size,
            x + size,
            y + size,
        )

        line2 = QGraphicsLineItem(
            x - size,
            y + size,
            x + size,
            y - size,
        )

        line1.setPen(pen)
        line2.setPen(pen)

        group = QGraphicsItemGroup()

        group.addToGroup(line1)
        group.addToGroup(line2)

        group.setZValue(10)

        return group

    def _create_circle(self, x, y, color, radius=2):
        marker = QGraphicsEllipseItem(
            x - radius,
            y - radius,
            2 * radius,
            2 * radius,
        )

        pen = QPen(color)
        pen.setWidth(2)

        marker.setPen(pen)

        marker.setBrush(QBrush(color))

        return marker

    def _inside_image(self, scene_pos):
        if self.image_item is None:
            return False

        local_pos = self.image_item.mapFromScene(scene_pos)

        return self.image_item.contains(local_pos)

    def _handle_calibration_click(self, scene_pos):
        if self.selection_mode is None:
            return

        self.set_axis_marker(
            self.selection_mode,
            scene_pos.x(),
            scene_pos.y(),
        )

        self.clicked.emit(
            scene_pos.x(),
            scene_pos.y(),
        )

    def _handle_point_click(self, scene_pos):
        x = scene_pos.x()
        y = scene_pos.y()

        self.data_points.append((x, y))

        color = self.graph_layers[self.active_graph_id]["color"]
        marker = self._create_data_marker(x, y, color)

        self.scene.addItem(marker)
        marker.setZValue(20)

        self.data_markers.append(marker)

        self.point_added.emit(
            len(self.data_points),
            x,
            y,
        )

        if len(self.data_points) >= 2:
            x1, y1 = self.data_points[-2]

            line = QGraphicsLineItem(x1, y1, x, y)

            pen = QPen(color)
            pen.setWidth(2)

            line.setPen(pen)
            line.setZValue(15)

            self.scene.addItem(line)

            self.data_lines.append(line)

    def _create_data_marker(self, x, y, color, radius=1):
        marker = QGraphicsEllipseItem(
            x - radius,
            y - radius,
            2 * radius,
            2 * radius,
        )

        marker.setBrush(QBrush(color))
        marker.setPen(QPen(color))

        return marker