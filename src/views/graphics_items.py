"""
Draggable graphics items for preview overlay.

Provides draggable label items for time, scale bar, speed label,
and colorbar that can be positioned by the user.
"""

from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QFont, QColor, QPen, QBrush
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QGraphicsRectItem,
    QStyleOptionGraphicsItem, QWidget
)


class DraggableItem(QGraphicsObject):
    """
    Base class for draggable overlay items.
    
    Stores position as relative coordinates (0-1) for
    resolution-independent positioning.
    
    Signals:
        position_changed(str, float, float): Item name, relative x, relative y.
    """
    
    position_changed = pyqtSignal(str, float, float)
    
    def __init__(self, name: str, parent=None):
        """
        Initialize draggable item.
        
        Args:
            name: Identifier for this item.
            parent: Parent graphics item.
        """
        super().__init__(parent)
        
        self._name = name
        self._image_width = 100
        self._image_height = 100
        self._relative_x = 0.0
        self._relative_y = 0.0
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setAcceptHoverEvents(True)
        
        self._is_hovered = False
    
    @property
    def name(self) -> str:
        """Get item name."""
        return self._name
    
    def set_image_size(self, width: int, height: int):
        """Set reference image size for relative positioning."""
        self._image_width = width
        self._image_height = height
        
        # Recalculate absolute position based on stored relative position
        abs_x = self._relative_x * self._image_width
        abs_y = self._relative_y * self._image_height
        self.setPos(abs_x, abs_y)
    
    def set_relative_position(self, rel_x: float, rel_y: float):
        """
        Set position using relative coordinates.
        
        Args:
            rel_x: Relative X position (0-1).
            rel_y: Relative Y position (0-1).
        """
        self._relative_x = rel_x
        self._relative_y = rel_y
        
        abs_x = rel_x * self._image_width
        abs_y = rel_y * self._image_height
        self.setPos(abs_x, abs_y)
    
    def get_relative_position(self) -> tuple[float, float]:
        """Get current relative position."""
        return (self._relative_x, self._relative_y)
    
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = value
            
            if self._image_width > 0 and self._image_height > 0:
                self._relative_x = pos.x() / self._image_width
                self._relative_y = pos.y() / self._image_height
                
                # Allow items to be placed outside image boundaries
                # to support colorbar placement outside original image area
                # The image will be extended in final preview mode
                # Limit to reasonable range (-0.5 to 2.0) to prevent
                # items from being dragged too far off-screen
                self._relative_x = max(-0.5, min(2.0, self._relative_x))
                self._relative_y = max(-0.5, min(2.0, self._relative_y))
                
                self.position_changed.emit(
                    self._name, self._relative_x, self._relative_y
                )
        
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter."""
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave."""
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)


COLOR_MAP = {
    'white': QColor(255, 255, 255),
    'black': QColor(0, 0, 0),
    'red': QColor(255, 0, 0),
    'blue': QColor(0, 0, 255),
    'green': QColor(0, 255, 0),
    'yellow': QColor(255, 255, 0),
}


class DraggableTextLabel(DraggableItem):
    """
    Draggable text label for time label, speed label, etc.
    """
    
    def __init__(self, name: str, text: str = "", parent=None):
        """
        Initialize text label.
        
        Args:
            name: Item identifier.
            text: Display text.
            parent: Parent item.
        """
        super().__init__(name, parent)
        
        self._text = text
        self._font = QFont("Arial")
        self._font.setPixelSize(16)  # Use pixel size for DPI independence
        self._font_bold = False
        self._text_color = QColor(255, 255, 255)
        self._padding = 6
        
        self._width = 100
        self._height = 30
        self._update_size()
    
    def set_text(self, text: str):
        """Set display text."""
        self._text = text
        self._update_size()
        self.update()
    
    def set_font(self, family: str, size: int, bold: bool = False):
        """Set text font using pixel size for DPI independence."""
        self._font = QFont(family)
        self._font.setPixelSize(size)  # Use pixel size instead of point size
        self._font_bold = bold
        self._font.setBold(bold)
        self._update_size()
        self.update()
    
    def set_color(self, color: str):
        """Set text color by name."""
        self._text_color = COLOR_MAP.get(color, QColor(255, 255, 255))
    
    def _update_size(self):
        """Update bounding rect based on text size."""
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(self._font)
        text_rect = fm.boundingRect(self._text)
        self._width = text_rect.width() + self._padding * 2
        self._height = text_rect.height() + self._padding * 2
        self.prepareGeometryChange()
    
    def boundingRect(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(0, 0, self._width, self._height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the text label."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw selection/hover indicator
        if self.isSelected() or self._is_hovered:
            painter.setPen(QPen(QColor(0, 113, 227), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.boundingRect(), 4, 4)
        
        # Draw text directly (no background, no outline)
        painter.setFont(self._font)
        painter.setPen(self._text_color)
        painter.drawText(
            self.boundingRect(),
            Qt.AlignmentFlag.AlignCenter,
            self._text
        )


class DraggableScaleBar(DraggableItem):
    """
    Draggable scale bar with line and optional text.
    """
    
    def __init__(self, name: str = "scale_bar", parent=None):
        """Initialize scale bar."""
        super().__init__(name, parent)
        
        self._bar_length = 100
        self._bar_thickness = 3
        self._bar_color = QColor(255, 255, 255)
        self._text = "50 μm"
        self._text_enabled = True
        self._text_position = "below"
        self._text_gap = 5
        self._font = QFont("Arial")
        self._font.setPixelSize(14)  # Use pixel size for DPI independence
        self._font_bold = False
        self._text_color = QColor(255, 255, 255)
        
        self._update_size()  # Dynamically calculate width and height
    
    def set_bar_length(self, length: int):
        """Set bar length in pixels."""
        self._bar_length = length
        self._update_size()
        self.update()
    
    def set_bar_thickness(self, thickness: int):
        """Set bar thickness."""
        self._bar_thickness = thickness
        self._update_size()
        self.update()
    
    def set_bar_color(self, color: str):
        """Set bar color by name."""
        self._bar_color = COLOR_MAP.get(color, QColor(255, 255, 255))
        self.update()
    
    def set_text(self, text: str):
        """Set scale text."""
        self._text = text
        self._update_size()
        self.update()
    
    def set_text_enabled(self, enabled: bool):
        """Enable or disable text."""
        self._text_enabled = enabled
        self._update_size()
        self.update()
    
    def set_text_position(self, position: str):
        """Set text position ('above' or 'below')."""
        self._text_position = position
        self._update_size()
        self.update()
    
    def set_text_gap(self, gap: int):
        """Set gap between bar and text in pixels."""
        self._text_gap = gap
        self._update_size()
        self.update()
    
    def set_font(self, family: str, size: int, bold: bool = False):
        """Set text font using pixel size for DPI independence."""
        self._font = QFont(family)
        self._font.setPixelSize(size)  # Use pixel size instead of point size
        self._font_bold = bold
        self._font.setBold(bold)
        self._update_size()
        self.update()
    
    def set_text_color(self, color: str):
        """Set text color by name."""
        self._text_color = COLOR_MAP.get(color, QColor(255, 255, 255))
        self.update()
    
    def _update_size(self):
        """Update bounding rect based on bar and text dimensions."""
        from PyQt6.QtGui import QFontMetrics
        
        # Calculate width: max of bar length and text width
        bar_with_margin = self._bar_length + 20  # 10px left + 10px right
        
        if self._text_enabled:
            fm = QFontMetrics(self._font)
            text_width = fm.horizontalAdvance(self._text)
            text_with_margin = text_width + 20  # 10px left + 10px right
            self._width = max(bar_with_margin, text_with_margin)
            
            # Calculate height based on text position
            text_height = fm.height()
            
            if self._text_position == "below":
                # Bar at top, text below
                # 8 (top margin) + bar_thickness + text_gap + text_height + 2 (bottom margin)
                self._height = 8 + self._bar_thickness + self._text_gap + text_height + 2
            else:
                # Text at top, bar below
                # 2 (top margin) + text_height + text_gap + bar_thickness + 2 (bottom margin)
                self._height = 2 + text_height + self._text_gap + self._bar_thickness + 2
        else:
            # No text, just bar
            self._width = bar_with_margin
            # 8 (top margin) + bar_thickness + 8 (bottom margin)
            self._height = 8 + self._bar_thickness + 8
        
        self.prepareGeometryChange()
    
    def boundingRect(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(0, 0, self._width, self._height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the scale bar."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)  # Disable for sharp edges
        
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(self._font)
        text_height = fm.height()
        ascent = fm.ascent()
        
        bar_x = 10
        half_thickness = self._bar_thickness // 2
        
        if self._text_position == "below":
            # Bar at top, text below
            bar_y = 8 + half_thickness
            bar_bottom = bar_y + half_thickness
            text_baseline_y = bar_bottom + self._text_gap + ascent
        else:
            # Text at top, bar below
            text_baseline_y = ascent + 2
            text_bottom = text_baseline_y + fm.descent()
            bar_y = text_bottom + self._text_gap + half_thickness
        
        # Draw scale bar as filled rectangle (square ends, not rounded)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._bar_color))
        bar_top = int(bar_y - half_thickness)
        bar_rect_height = self._bar_thickness
        painter.drawRect(bar_x, bar_top, self._bar_length, bar_rect_height)
        
        if self._text_enabled:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)  # Re-enable for text
            painter.setFont(self._font)
            
            text_width = fm.horizontalAdvance(self._text)
            text_x = bar_x + (self._bar_length - text_width) // 2
            
            painter.setPen(self._text_color)
            painter.drawText(text_x, int(text_baseline_y), self._text)
        
        if self.isSelected() or self._is_hovered:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(QColor(0, 113, 227), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())


class DraggableColorbar(DraggableItem):
    """
    Draggable colorbar for velocity visualization.
    """
    
    def __init__(self, name: str = "colorbar", parent=None):
        """Initialize colorbar."""
        super().__init__(name, parent)
        
        self._colormap_image = None
        self._title = "Speed (μm/s)"
        self._vmin = 0.0
        self._vmax = 100.0
        self._tick_interval = 20.0
        
        self._bar_width = 14
        self._bar_height = 200
        self._title_position = "top"
        self._title_gap = 5
        self._title_font = QFont("Arial")
        self._title_font.setPixelSize(12)  # Use pixel size for DPI independence
        self._title_bold = False
        self._title_color = QColor(0, 0, 0)
        self._tick_font = QFont("Arial")
        self._tick_font.setPixelSize(10)  # Use pixel size for DPI independence
        self._tick_bold = False
        self._tick_color = QColor(0, 0, 0)
        self._border_thickness = 1
        self._tick_thickness = 1
        self._tick_length = 5
        
        self._update_total_size()
        
        # Set cache mode to prevent drag trails
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)
    
    def _update_total_size(self):
        """Recalculate total bounding rect size."""
        from PyQt6.QtGui import QFontMetrics
        
        title_fm = QFontMetrics(self._title_font)
        tick_fm = QFontMetrics(self._tick_font)
        
        # Calculate tick label width (estimate with max value)
        max_tick_width = tick_fm.horizontalAdvance(f"{self._vmax:.2f}")
        
        # Calculate dimensions based on title position
        if self._title_position == "top":
            title_width = title_fm.horizontalAdvance(self._title)
            bar_x = 5
            
            # Content (bar + ticks) width from left edge of bounding rect
            content_width = bar_x + self._bar_width + self._tick_length + 3 + max_tick_width + 10
            
            # Title is centered at bar_x + bar_width/2
            # Calculate how much width the centered title needs
            title_center = bar_x + self._bar_width // 2
            title_left = title_center - title_width // 2
            title_right = title_center + title_width // 2
            
            # If title extends left of x=0, we need extra width
            left_extend = max(0, -title_left)
            title_needs_width = title_right + left_extend + 10
            
            # Total width must accommodate both title and content
            self._total_width = max(content_width, title_needs_width)
            self._total_height = title_fm.height() + self._title_gap + self._bar_height + 10
        else:
            # Title on right, vertical text
            title_height = title_fm.horizontalAdvance(self._title)
            self._total_width = self._bar_width + self._tick_length + 3 + max_tick_width + self._title_gap + title_fm.height() + 20
            self._total_height = max(self._bar_height, title_height) + 20
        
        self.prepareGeometryChange()
    
    def set_colormap_image(self, image):
        """Set colormap image (numpy array BGR)."""
        if image is not None:
            from ..utils import numpy_to_qpixmap
            self._colormap_image = numpy_to_qpixmap(image)
        self._update_total_size()
        self.update()
    
    def set_bar_size(self, width: int, height: int):
        """Set bar dimensions."""
        self._bar_width = width
        self._bar_height = height
        self._update_total_size()
        self.update()
    
    def set_title(self, title: str):
        """Set colorbar title."""
        self._title = title
        self._update_total_size()
        self.update()
    
    def set_title_position(self, position: str):
        """Set title position ('top' or 'right')."""
        self._title_position = position.lower()
        self._update_total_size()
        self.update()
    
    def set_title_gap(self, gap: int):
        """Set gap between title and colorbar."""
        self._title_gap = gap
        self._update_total_size()
        self.update()
    
    def set_range(self, vmin: float, vmax: float, tick_interval: float):
        """Set value range and tick interval."""
        self._vmin = vmin
        self._vmax = vmax
        self._tick_interval = tick_interval
        self._update_total_size()
        self.update()
    
    def set_fonts(
        self, title_family: str, title_size: int, title_bold: bool,
        tick_family: str, tick_size: int, tick_bold: bool
    ):
        """Set fonts for title and tick labels using pixel size."""
        self._title_font = QFont(title_family)
        self._title_font.setPixelSize(title_size)  # Use pixel size
        self._title_bold = title_bold
        self._title_font.setBold(title_bold)
        self._tick_font = QFont(tick_family)
        self._tick_font.setPixelSize(tick_size)  # Use pixel size
        self._tick_bold = tick_bold
        self._tick_font.setBold(tick_bold)
        self._update_total_size()
        self.update()
    
    def set_title_color(self, color: str):
        """Set title color by name."""
        self._title_color = COLOR_MAP.get(color, QColor(0, 0, 0))
        self.update()
    
    def set_tick_color(self, color: str):
        """Set tick label color by name."""
        self._tick_color = COLOR_MAP.get(color, QColor(0, 0, 0))
        self.update()
    
    def set_border_thickness(self, thickness: int):
        """Set border line thickness."""
        self._border_thickness = thickness
        self.update()
    
    def set_tick_style(self, thickness: int, length: int):
        """Set tick mark thickness and length."""
        self._tick_thickness = thickness
        self._tick_length = length
        self._update_total_size()
        self.update()
    
    def boundingRect(self) -> QRectF:
        """Return bounding rectangle."""
        return QRectF(0, 0, self._total_width, self._total_height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Paint the colorbar."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        from PyQt6.QtGui import QFontMetrics
        title_fm = QFontMetrics(self._title_font)
        tick_fm = QFontMetrics(self._tick_font)
        
        # Calculate bar_x with potential left padding for wide titles
        bar_x_base = 5
        if self._title_position == "top":
            # If title would extend left of bounding rect, shift bar right
            title_width = title_fm.horizontalAdvance(self._title)
            title_center = bar_x_base + self._bar_width // 2
            title_left = title_center - title_width // 2
            left_padding = max(0, -title_left)
            bar_x = bar_x_base + left_padding
        else:
            bar_x = bar_x_base
        
        if self._title_position == "top":
            # Title at top, horizontal, centered over bar
            title_y = title_fm.ascent() + 2
            bar_y = title_y + title_fm.descent() + self._title_gap
            
            painter.setFont(self._title_font)
            painter.setPen(self._title_color)
            
            # Center title horizontally over the bar
            title_width = title_fm.horizontalAdvance(self._title)
            title_x = bar_x + (self._bar_width - title_width) // 2
            painter.drawText(title_x, int(title_y), self._title)
        else:
            # Title on right, vertical
            bar_y = 5
        
        # Draw colormap image
        if self._colormap_image:
            scaled_pixmap = self._colormap_image.scaled(
                self._bar_width, self._bar_height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(bar_x, int(bar_y), scaled_pixmap)
        
        # Draw bar border
        painter.setPen(QPen(self._tick_color, self._border_thickness))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(bar_x, int(bar_y), self._bar_width, self._bar_height)
        
        # Draw tick marks and labels
        painter.setFont(self._tick_font)
        painter.setPen(QPen(self._tick_color, self._tick_thickness))
        if self._vmax > self._vmin and self._tick_interval > 0:
            num_ticks = int((self._vmax - self._vmin) / self._tick_interval) + 1
            
            for i in range(num_ticks):
                value = self._vmax - i * self._tick_interval
                if value < self._vmin:
                    break
                
                tick_y = bar_y + int(
                    (self._vmax - value) / (self._vmax - self._vmin) * self._bar_height
                )
                
                painter.drawLine(
                    bar_x + self._bar_width, int(tick_y),
                    bar_x + self._bar_width + self._tick_length, int(tick_y)
                )
                
                painter.drawText(
                    bar_x + self._bar_width + self._tick_length + 3, int(tick_y) + tick_fm.ascent() // 2,
                    f"{value:.2f}"
                )
        
        # Draw title on right side (vertical text)
        if self._title_position == "right":
            painter.setFont(self._title_font)
            painter.setPen(self._title_color)
            
            max_tick_width = tick_fm.horizontalAdvance(f"{self._vmax:.2f}")
            title_x = bar_x + self._bar_width + 8 + max_tick_width + self._title_gap
            
            # Draw vertical text (rotated 90 degrees, facing left = -90)
            painter.save()
            title_center_y = bar_y + self._bar_height // 2
            painter.translate(title_x + title_fm.height(), title_center_y)
            painter.rotate(-90)
            
            title_width = title_fm.horizontalAdvance(self._title)
            painter.drawText(-title_width // 2, title_fm.ascent() // 2, self._title)
            painter.restore()
        
        # Draw selection/hover indicator
        if self.isSelected() or self._is_hovered:
            painter.setPen(QPen(QColor(0, 113, 227), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
