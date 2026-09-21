from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
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

        # Pan com botão esquerdo arrastando
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Zoom acontece em torno do mouse
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

        # Limpa a cena anterior
        self.scene.clear()

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
            self.scale(
                1 / zoom_factor,
                1 / zoom_factor,
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:

            scene_pos = self.mapToScene(
                event.position().toPoint()
            )

            # Só registra cliques dentro da imagem
            if (
                self.image_item is not None
                and self.image_item.contains(
                    self.image_item.mapFromScene(scene_pos)
                )
            ):
                print(
                    f"Clicked: "
                    f"x={scene_pos.x():.2f}, "
                    f"y={scene_pos.y():.2f}"
                )

                self.clicked.emit(
                    scene_pos.x(),
                    scene_pos.y(),
                )

                self.add_marker(
                    scene_pos.x(),
                    scene_pos.y(),
                )

        super().mousePressEvent(event)

    def add_marker(self, x, y, radius=5):
        marker = QGraphicsEllipseItem(
            x - radius,
            y - radius,
            2 * radius,
            2 * radius,
        )

        marker.setBrush(
            QBrush(Qt.GlobalColor.red)
        )

        marker.setPen(
            QPen(Qt.GlobalColor.red)
        )

        marker.setZValue(10)

        self.scene.addItem(marker)

        return marker