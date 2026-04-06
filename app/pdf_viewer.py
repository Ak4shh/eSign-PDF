from __future__ import annotations
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QColor, QCursor, QFont, QPainter, QPainterPath, QPen, QPixmap,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsView, QGraphicsSimpleTextItem,
)

from app.models import OverlayItem, OverlayType, PdfRect
from app.tools import PendingPlacement
from app.utils import (
    color_name_to_qcolor, normalize_rect, pdf_rect_to_qrectf, fit_font_size,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HANDLE_SIZE = 8.0        # screen-space pixels worth of handle — scaled by zoom in viewer
_HANDLE_HALF = _HANDLE_SIZE / 2.0
_MIN_RECT = 10.0           # minimum width/height in PDF points

_HANDLE_CURSORS = [
    Qt.CursorShape.SizeFDiagCursor,  # 0 TL
    Qt.CursorShape.SizeVerCursor,    # 1 T
    Qt.CursorShape.SizeBDiagCursor,  # 2 TR
    Qt.CursorShape.SizeHorCursor,    # 3 R
    Qt.CursorShape.SizeFDiagCursor,  # 4 BR
    Qt.CursorShape.SizeVerCursor,    # 5 B
    Qt.CursorShape.SizeBDiagCursor,  # 6 BL
    Qt.CursorShape.SizeHorCursor,    # 7 L
]

# Which edges each handle index moves:
#   bit 0 = left, bit 1 = right, bit 2 = top, bit 3 = bottom
_HANDLE_EDGES = [
    0b0101,  # 0 TL  left+top
    0b0100,  # 1 T   top
    0b0110,  # 2 TR  right+top
    0b0010,  # 3 R   right
    0b1010,  # 4 BR  right+bottom
    0b1000,  # 5 B   bottom
    0b1001,  # 6 BL  left+bottom
    0b0001,  # 7 L   left
]


# ---------------------------------------------------------------------------
# Overlay graphics item
# ---------------------------------------------------------------------------

class OverlayGraphicsItem(QGraphicsRectItem):
    """
    Movable, resizable, selectable rectangle for one OverlayItem.
    Movement and resizing are handled manually so the item position stays
    at (0,0) in scene; all coordinates live in the rect itself (== PDF points).
    """

    SEL_COLOR = QColor(0, 120, 215, 60)
    HANDLE_COLOR = QColor(0, 120, 215)
    BORDER_COLOR = QColor(0, 120, 215)

    def __init__(self, overlay: OverlayItem, zoom: float = 1.0,
                 on_resized=None,
                 parent: QGraphicsItem | None = None):
        r = pdf_rect_to_qrectf(overlay.rect_pdf)
        super().__init__(r, parent)
        self.overlay = overlay
        self._zoom = zoom
        self._on_resized = on_resized  # callable(OverlayItem) or None
        self._label: Optional[QGraphicsSimpleTextItem] = None

        # drag state
        self._drag_mode: int | str | None = None   # None | 'move' | handle-int
        self._drag_start_scene = QPointF()
        self._drag_start_rect = QRectF()

        self._setup()

    def _setup(self) -> None:
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setAcceptHoverEvents(True)
        pen = QPen(self.BORDER_COLOR, 1.5, Qt.PenStyle.DashLine)
        self.setPen(pen)
        self._refresh_label()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _hs(self) -> float:
        """Handle half-size in scene/PDF coordinates (constant screen size)."""
        return _HANDLE_HALF / max(self._zoom, 0.1)

    def _handle_rects(self) -> list[QRectF]:
        r = self.rect()
        hs = self._hs()
        s = hs * 2
        cx = r.x() + r.width() / 2
        cy = r.y() + r.height() / 2
        return [
            QRectF(r.left()  - hs, r.top()    - hs, s, s),  # 0 TL
            QRectF(cx        - hs, r.top()    - hs, s, s),  # 1 T
            QRectF(r.right() - hs, r.top()    - hs, s, s),  # 2 TR
            QRectF(r.right() - hs, cy         - hs, s, s),  # 3 R
            QRectF(r.right() - hs, r.bottom() - hs, s, s),  # 4 BR
            QRectF(cx        - hs, r.bottom() - hs, s, s),  # 5 B
            QRectF(r.left()  - hs, r.bottom() - hs, s, s),  # 6 BL
            QRectF(r.left()  - hs, cy         - hs, s, s),  # 7 L
        ]

    def _hit_handle(self, pos: QPointF) -> int:
        for i, hr in enumerate(self._handle_rects()):
            if hr.contains(pos):
                return i
        return -1

    def boundingRect(self) -> QRectF:
        hs = self._hs()
        return self.rect().adjusted(-hs, -hs, hs, hs)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    # ------------------------------------------------------------------
    # Label / display
    # ------------------------------------------------------------------

    @staticmethod
    def _screen_dpi_for_item(item: "OverlayGraphicsItem") -> float:
        scene = item.scene()
        if scene:
            views = scene.views()
            if views:
                return max(views[0].logicalDpiY(), 1.0)
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        return max(screen.logicalDotsPerInch(), 1.0) if screen else 96.0

    def _pdf_pt_to_qt_pt(self, pdf_pt: float) -> float:
        """
        Convert a font size in PDF points to Qt logical points so that the
        rendered height in scene units (= PDF points) matches visually.
        Qt renders a font of size s pts at height ≈ s × DPI/72 logical pixels
        (= scene units). To get height = pdf_pt scene units we need:
            qt_pt = pdf_pt × 72 / DPI
        """
        return pdf_pt * 72.0 / self._screen_dpi_for_item(self)

    def _refresh_label(self) -> None:
        ov = self.overlay
        r = self.rect()
        text = ov.text or ""

        if ov.type == OverlayType.signature_image or not text:
            if self._label is not None:
                self._label.setVisible(False)
            return

        if self._label is None:
            self._label = QGraphicsSimpleTextItem(self)
            self._label.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        self._label.setVisible(True)
        self._label.setText(text)

        color = color_name_to_qcolor(ov.color or "black")
        self._label.setBrush(color)

        font = QFont()
        if ov.type == OverlayType.typed_signature and ov.font_name:
            font.setFamily(ov.font_name)

        if ov.font_size and ov.font_size > 0:
            # Use the PyMuPDF-computed size, converted to Qt logical points
            qt_pt = self._pdf_pt_to_qt_pt(ov.font_size)
        else:
            # Fallback heuristic until compute_font_size runs after placement
            qt_pt = self._pdf_pt_to_qt_pt(
                fit_font_size(text, ov.font_name or "", r.width(), r.height())
            )

        font.setPointSizeF(max(qt_pt, 1.0))
        self._label.setFont(font)

        lb = self._label.boundingRect()
        lx = r.x() + (r.width() - lb.width()) / 2
        ly = r.y() + (r.height() - lb.height()) / 2
        self._label.setPos(lx, ly)

    def refresh(self) -> None:
        """Re-sync display from self.overlay after an external model change."""
        self.prepareGeometryChange()
        self.setRect(pdf_rect_to_qrectf(self.overlay.rect_pdf))
        pen = QPen(self.BORDER_COLOR, 1.5, Qt.PenStyle.DashLine)
        self.setPen(pen)
        self._refresh_label()
        self.update()

    def set_zoom(self, zoom: float) -> None:
        self._zoom = zoom
        self.prepareGeometryChange()
        self.update()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paint(self, painter: QPainter, option, widget=None) -> None:
        if self.isSelected():
            painter.fillRect(self.rect(), self.SEL_COLOR)
        super().paint(painter, option, widget)

        # Draw resize handles only when selected
        if self.isSelected():
            hs = self._hs()
            s = hs * 2
            painter.setPen(QPen(self.HANDLE_COLOR, 1.0))
            painter.setBrush(QColor(255, 255, 255))
            for hr in self._handle_rects():
                painter.drawRect(hr)

    # ------------------------------------------------------------------
    # Hover / cursor
    # ------------------------------------------------------------------

    def hoverMoveEvent(self, event) -> None:
        i = self._hit_handle(event.pos())
        if i >= 0:
            self.setCursor(QCursor(_HANDLE_CURSORS[i]))
        else:
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def hoverLeaveEvent(self, event) -> None:
        self.unsetCursor()

    # ------------------------------------------------------------------
    # Mouse press / move / release
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            self._drag_start_scene = event.scenePos()
            self._drag_start_rect = QRectF(self.rect())

            i = self._hit_handle(pos)
            if i >= 0:
                self._drag_mode = i
                # Manually handle selection so handle drag also selects
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    sc = self.scene()
                    if sc:
                        sc.clearSelection()
                self.setSelected(True)
                event.accept()
                return

            self._drag_mode = 'move'

        super().mousePressEvent(event)  # handles ItemIsSelectable

    def mouseMoveEvent(self, event) -> None:
        if self._drag_mode is None:
            super().mouseMoveEvent(event)
            return

        delta = event.scenePos() - self._drag_start_scene
        r = QRectF(self._drag_start_rect)

        if self._drag_mode == 'move':
            r.translate(delta)
        else:
            edges = _HANDLE_EDGES[self._drag_mode]
            if edges & 0b0001:  # left
                r.setLeft(min(r.left() + delta.x(), r.right() - _MIN_RECT))
            if edges & 0b0010:  # right
                r.setRight(max(r.right() + delta.x(), r.left() + _MIN_RECT))
            if edges & 0b0100:  # top
                r.setTop(min(r.top() + delta.y(), r.bottom() - _MIN_RECT))
            if edges & 0b1000:  # bottom
                r.setBottom(max(r.bottom() + delta.y(), r.top() + _MIN_RECT))

        self.prepareGeometryChange()
        self.setRect(r)
        self.overlay.rect_pdf = PdfRect(r.x(), r.y(), r.width(), r.height())
        self._refresh_label()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        mode = self._drag_mode
        self._drag_mode = None
        super().mouseReleaseEvent(event)
        # Notify after a resize so the main window can recompute font_size
        if mode is not None and mode != 'move' and self._on_resized:
            self._on_resized(self.overlay)


# ---------------------------------------------------------------------------
# Main viewer widget
# ---------------------------------------------------------------------------

class PdfViewer(QGraphicsView):
    """
    Displays a single PDF page. Scene coordinates == PDF coordinates (points).
    Zoom is applied via the view transform only; stored geometry is unaffected.
    """

    overlay_placed = Signal(OverlayItem)
    overlay_deleted = Signal(str)          # overlay id
    overlay_edit_requested = Signal(OverlayItem)
    overlay_resized = Signal(OverlayItem)  # fired after a resize drag completes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._zoom: float = 1.0
        self._page_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._pending: Optional[PendingPlacement] = None
        self._drag_start: Optional[QPointF] = None
        self._rubber_item: Optional[QGraphicsRectItem] = None
        self._overlay_items: Dict[str, OverlayGraphicsItem] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_page(
        self,
        pixmap: QPixmap,
        overlays: List[OverlayItem],
        zoom: float,
    ) -> None:
        self._scene.clear()
        self._overlay_items.clear()
        self._rubber_item = None
        self._drag_start = None
        self._zoom = zoom

        if pixmap.isNull():
            return

        inv_zoom = 1.0 / zoom
        self._page_pixmap_item = QGraphicsPixmapItem(pixmap)
        self._page_pixmap_item.setScale(inv_zoom)
        self._page_pixmap_item.setZValue(0)
        self._scene.addItem(self._page_pixmap_item)

        pdf_w = pixmap.width() * inv_zoom
        pdf_h = pixmap.height() * inv_zoom
        self._scene.setSceneRect(0, 0, pdf_w, pdf_h)

        for ov in overlays:
            self._add_overlay_item(ov)

        self._apply_zoom(zoom)

    def set_zoom(self, zoom: float) -> None:
        self._zoom = zoom
        for item in self._overlay_items.values():
            item.set_zoom(zoom)
        self._apply_zoom(zoom)

    def set_pending(self, pending: Optional[PendingPlacement]) -> None:
        self._pending = pending
        if pending is not None:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def add_overlay(self, overlay: OverlayItem) -> None:
        self._add_overlay_item(overlay)

    def remove_overlay(self, overlay_id: str) -> None:
        item = self._overlay_items.pop(overlay_id, None)
        if item is not None:
            self._scene.removeItem(item)

    def refresh_overlay(self, overlay_id: str) -> None:
        item = self._overlay_items.get(overlay_id)
        if item:
            item.refresh()

    def delete_selected(self) -> None:
        for item in list(self._scene.selectedItems()):
            if isinstance(item, OverlayGraphicsItem):
                ov_id = item.overlay.id
                self._scene.removeItem(item)
                self._overlay_items.pop(ov_id, None)
                self.overlay_deleted.emit(ov_id)

    def clear_overlays(self) -> None:
        for item in list(self._overlay_items.values()):
            self._scene.removeItem(item)
        self._overlay_items.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_zoom(self, zoom: float) -> None:
        self.resetTransform()
        self.scale(zoom, zoom)

    def _add_overlay_item(self, overlay: OverlayItem) -> OverlayGraphicsItem:
        item = OverlayGraphicsItem(
            overlay,
            zoom=self._zoom,
            on_resized=lambda ov: self.overlay_resized.emit(ov),
        )
        item.setZValue(1)
        self._scene.addItem(item)
        self._overlay_items[overlay.id] = item
        return item

    # ------------------------------------------------------------------
    # Mouse events for draw mode
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if self._pending is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = self.mapToScene(event.position().toPoint())
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            self._rubber_item = self._scene.addRect(
                QRectF(self._drag_start, self._drag_start), pen
            )
            self._rubber_item.setZValue(10)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._pending is not None and self._drag_start is not None:
            current = self.mapToScene(event.position().toPoint())
            r = QRectF(self._drag_start, current).normalized()
            if self._rubber_item:
                self._rubber_item.setRect(r)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._pending is not None and self._drag_start is not None:
            end = self.mapToScene(event.position().toPoint())
            rect = normalize_rect(
                self._drag_start.x(), self._drag_start.y(),
                end.x(), end.y(),
            )

            if self._rubber_item:
                self._scene.removeItem(self._rubber_item)
                self._rubber_item = None
            self._drag_start = None

            if rect.width < 4 or rect.height < 4:
                return

            pending = self._pending
            self._pending = None
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

            overlay = OverlayItem(
                page_index=-1,
                type=pending.overlay_type,
                rect_pdf=rect,
                text=pending.text,
                font_name=pending.font_name,
                color=pending.color,
                image_path=pending.image_path,
            )
            self._add_overlay_item(overlay)
            self.overlay_placed.emit(overlay)
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if self._pending is not None:
            super().mouseDoubleClickEvent(event)
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        for item in self._scene.items(scene_pos):
            if isinstance(item, OverlayGraphicsItem):
                self.overlay_edit_requested.emit(item.overlay)
                event.accept()
                return
            # handle clicks on child label items
            parent = item.parentItem() if isinstance(item, QGraphicsItem) else None
            if isinstance(parent, OverlayGraphicsItem):
                self.overlay_edit_requested.emit(parent.overlay)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
            return
        if event.key() == Qt.Key.Key_Escape:
            if self._pending is not None:
                if self._rubber_item:
                    self._scene.removeItem(self._rubber_item)
                    self._rubber_item = None
                self._drag_start = None
                self._pending = None
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return
        super().keyPressEvent(event)
