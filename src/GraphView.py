import math

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
    point_moved = Signal(int, float, float)
    axis_moved = Signal(str, float, float)

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
        self.dragging_point_index = None
        self.dragging_axis_name = None

        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self._set_canvas_cursor(Qt.CursorShape.CrossCursor)

        self.magnifier_enabled = False
        self.magnifier_size = 180
        self.magnifier_zoom = 4.0
        self.last_scene_pos = None
        self.last_viewport_pos = None
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
        self._update_cursor_for_position(self.last_scene_pos)

    def _set_canvas_cursor(self, cursor_shape):
        self.setCursor(cursor_shape)
        self.viewport().setCursor(cursor_shape)

    def _update_cursor_for_position(self, scene_pos):
        if scene_pos is None or not self._inside_image(scene_pos):
            self._set_canvas_cursor(Qt.CursorShape.CrossCursor)
            return

        if self.mode == "calibration":
            over_axis = self._find_axis_name(scene_pos) is not None
        else:
            over_axis = False
        over_point = (
            self.mode == "points"
            and self._find_point_index(scene_pos) is not None
        )

        if self.dragging_axis_name is not None:
            cursor_shape = Qt.CursorShape.ClosedHandCursor
        elif self.dragging_point_index is not None and over_point:
            cursor_shape = Qt.CursorShape.ClosedHandCursor
        elif over_axis or over_point:
            cursor_shape = Qt.CursorShape.PointingHandCursor
        elif self.magnifier_enabled:
            cursor_shape = Qt.CursorShape.BlankCursor
        else:
            cursor_shape = Qt.CursorShape.CrossCursor
        self._set_canvas_cursor(cursor_shape)

    def mouseMoveEvent(self, event):
        viewport_pos = event.position().toPoint()
        self.last_viewport_pos = viewport_pos
        self.last_scene_pos = self.mapToScene(viewport_pos)
        if self.dragging_axis_name is not None:
            self._move_axis_marker(
                self.dragging_axis_name,
                self.last_scene_pos.x(),
                self.last_scene_pos.y(),
            )
        elif self.dragging_point_index is not None:
            self._move_data_point(
                self.dragging_point_index,
                self.last_scene_pos.x(),
                self.last_scene_pos.y(),
            )
        else:
            self._refresh_magnifier()

        super().mouseMoveEvent(event)
        QTimer.singleShot(0, self._restore_cursor)

    def _refresh_magnifier(self):
        if (
            not self.magnifier_enabled
            or self.last_scene_pos is None
            or self.last_viewport_pos is None
            or not self._inside_image(self.last_scene_pos)
        ):
            self.magnifier_label.hide()
            self._update_cursor_for_position(self.last_scene_pos)
            return

        self._update_magnifier(
            self.last_scene_pos,
            self.last_viewport_pos,
        )

    def leaveEvent(self, event):
        self.magnifier_label.hide()
        self._set_canvas_cursor(Qt.CursorShape.CrossCursor)
        super().leaveEvent(event)

    def _update_magnifier(self, scene_pos, viewport_pos):
        self._update_cursor_for_position(scene_pos)
        source_radius = self._magnifier_source_radius()
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

    def _magnifier_source_radius(self):
        current_zoom = abs(self.transform().m11())
        current_zoom = max(current_zoom, 0.01)
        return (self.magnifier_size - 8) / (
            2 * current_zoom * self.magnifier_zoom
        )

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

    def set_graph_color(self, graph_id, color):
        layer = self.graph_layers.get(graph_id)
        if layer is None:
            return

        layer["color"] = QColor(color)
        for marker in layer["data_markers"]:
            marker.setBrush(QBrush(layer["color"]))
            marker.setPen(QPen(layer["color"]))
        for line in layer["data_lines"]:
            pen = QPen(layer["color"])
            pen.setWidth(2)
            line.setPen(pen)
        self._refresh_magnifier()

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
        viewport_pos = event.position().toPoint()
        self.last_viewport_pos = viewport_pos

        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

        self.last_scene_pos = self.mapToScene(viewport_pos)
        self._refresh_magnifier()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            QTimer.singleShot(0, self._restore_cursor)
            return

        scene_pos = self.mapToScene(event.position().toPoint())
        self.last_viewport_pos = event.position().toPoint()
        self.last_scene_pos = scene_pos

        if not self._inside_image(scene_pos):
            super().mousePressEvent(event)
            QTimer.singleShot(0, self._restore_cursor)
            return

        if self.mode == "calibration":
            axis_name = self._find_axis_name(scene_pos)
            if axis_name is not None:
                self.dragging_axis_name = axis_name
                self._move_axis_marker(
                    axis_name,
                    scene_pos.x(),
                    scene_pos.y(),
                )
                self._set_canvas_cursor(Qt.CursorShape.ClosedHandCursor)
                return
            self._handle_calibration_click(scene_pos)

        elif self.mode == "points":
            point_index = self._find_point_index(scene_pos)
            if point_index is not None:
                self.dragging_point_index = point_index
                self._move_data_point(
                    point_index,
                    scene_pos.x(),
                    scene_pos.y(),
                )
                return
            self._handle_point_click(scene_pos)
            QTimer.singleShot(0, self._restore_cursor)
            return

        super().mousePressEvent(event)
        QTimer.singleShot(0, self._restore_cursor)

    def mouseReleaseEvent(self, event):
        self.dragging_point_index = None
        self.dragging_axis_name = None
        super().mouseReleaseEvent(event)
        QTimer.singleShot(0, self._restore_cursor)

    def _restore_cursor(self):
        self._update_cursor_for_position(self.last_scene_pos)

    def _find_point_index(self, scene_pos):
        if not self.data_points:
            return None

        threshold = 8 / max(abs(self.transform().m11()), 0.01)
        closest_index = None
        closest_distance = threshold
        for index, (point_x, point_y) in enumerate(self.data_points):
            distance = math.hypot(
                scene_pos.x() - point_x,
                scene_pos.y() - point_y,
            )
            if distance <= closest_distance:
                closest_index = index
                closest_distance = distance
        return closest_index

    def _find_axis_name(self, scene_pos):
        if not self.axis_positions:
            return None

        threshold = 8 / max(abs(self.transform().m11()), 0.01)
        closest_name = None
        closest_distance = threshold
        for name, (point_x, point_y) in self.axis_positions.items():
            distance = math.hypot(
                scene_pos.x() - point_x,
                scene_pos.y() - point_y,
            )
            if distance <= closest_distance:
                closest_name = name
                closest_distance = distance
        return closest_name

    def _move_axis_marker(self, name, x, y):
        self.set_axis_marker(name, x, y)
        self.axis_moved.emit(name, x, y)

    def _move_data_point(self, index, x, y):
        self.data_points[index] = (x, y)
        marker = self.data_markers[index]
        rect = marker.rect()
        marker.setRect(
            x - rect.width() / 2,
            y - rect.height() / 2,
            rect.width(),
            rect.height(),
        )
        self._rebuild_data_lines()
        self.point_moved.emit(index, x, y)
        self._refresh_magnifier()

    def _rebuild_data_lines(self):
        for line in self.data_lines:
            self.scene.removeItem(line)
        self.data_lines.clear()

        color = self.graph_layers[self.active_graph_id]["color"]
        for index in range(1, len(self.data_points)):
            x1, y1 = self.data_points[index - 1]
            x2, y2 = self.data_points[index]
            line = QGraphicsLineItem(x1, y1, x2, y2)
            pen = QPen(color)
            pen.setWidth(2)
            line.setPen(pen)
            line.setZValue(15)
            self.scene.addItem(line)
            self.data_lines.append(line)

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

    def remove_data_point(self, index):
        if index < 0 or index >= len(self.data_points):
            return False

        marker = self.data_markers.pop(index)
        self.scene.removeItem(marker)
        self.data_points.pop(index)
        self._rebuild_data_lines()
        self._refresh_magnifier()
        return True

    def reorder_data_points(self, order):
        if sorted(order) != list(range(len(self.data_points))):
            return False

        self.data_points[:] = [self.data_points[index] for index in order]
        self.data_markers[:] = [self.data_markers[index] for index in order]
        self._rebuild_data_lines()
        self._refresh_magnifier()
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

        self.add_data_point(x, y)

        self.point_added.emit(
            len(self.data_points),
            x,
            y,
        )

    def add_data_point(self, x, y):
        """Add a point programmatically without emitting a click signal."""

        self.data_points.append((x, y))

        color = self.graph_layers[self.active_graph_id]["color"]
        marker = self._create_data_marker(x, y, color)

        self.scene.addItem(marker)
        marker.setZValue(20)

        self.data_markers.append(marker)

        if len(self.data_points) >= 2:
            x1, y1 = self.data_points[-2]

            line = QGraphicsLineItem(x1, y1, x, y)

            pen = QPen(color)
            pen.setWidth(2)

            line.setPen(pen)
            line.setZValue(15)

            self.scene.addItem(line)

            self.data_lines.append(line)

        self._refresh_magnifier()

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