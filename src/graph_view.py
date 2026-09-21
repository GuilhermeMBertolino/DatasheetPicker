from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsItemGroup,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
)

class GraphView(QGraphicsView):
    clicked = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.image_item = None

        self.selection_mode = None
        self.axis_markers = {}

        self.setDragMode(
            QGraphicsView.DragMode.ScrollHandDrag
        )

        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )

        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )

    def load_image(self, filename):
        pixmap = QPixmap(filename)

        if pixmap.isNull():
            return False

        self.scene.clear()

        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)

        self.axis_markers.clear()

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
            self.scale(
                zoom_factor,
                zoom_factor,
            )
        else:
            self.scale(
                1 / zoom_factor,
                1 / zoom_factor,
            )

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.selection_mode is not None
        ):
            scene_pos = self.mapToScene(
                event.position().toPoint()
            )

            if self._inside_image(scene_pos):
                self.set_axis_marker(
                    self.selection_mode,
                    scene_pos.x(),
                    scene_pos.y(),
                )

                self.clicked.emit(
                    scene_pos.x(),
                    scene_pos.y(),
                )

                self.selection_mode = None

                return

        super().mousePressEvent(event)

    def start_axis_selection(self, name):
        self.selection_mode = name

    def set_axis_marker(self, name, x, y):
        # Remove previous marker
        if name in self.axis_markers:
            self.scene.removeItem(
                self.axis_markers[name]
            )

        if name in ("X1", "X2"):
            color = Qt.GlobalColor.red
        else:
            color = Qt.GlobalColor.blue

        if name in ("X1", "Y1"):
            marker = self._create_cross(
                x,
                y,
                color,
            )
        else:
            marker = self._create_circle(
                x,
                y,
                color,
            )

        self.scene.addItem(marker)

        marker.setZValue(10)

        self.axis_markers[name] = marker

    def reset_axis_selection(self):
        for marker in self.axis_markers.values():
            self.scene.removeItem(marker)

        self.axis_markers.clear()
        self.selection_mode = None

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

        local_pos = self.image_item.mapFromScene(
            scene_pos
        )

        return self.image_item.contains(
            local_pos
        )