"""
Preview widget for visualization.

Displays rendered frames with playback controls and
draggable overlay items.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QPushButton,
    QSlider, QLabel, QFrame, QSizePolicy
)

from .graphics_items import (
    DraggableTextLabel, DraggableScaleBar, DraggableColorbar
)


class PreviewGraphicsView(QGraphicsView):
    """
    Custom graphics view with double-click detection.
    
    Signals:
        double_clicked(float, float): Double-click position in scene coordinates.
    """
    
    double_clicked = pyqtSignal(float, float)
    
    def __init__(self, parent=None):
        """Initialize preview graphics view."""
        super().__init__(parent)
        
        self.setRenderHints(
            self.renderHints() |
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click events."""
        scene_pos = self.mapToScene(event.pos())
        self.double_clicked.emit(scene_pos.x(), scene_pos.y())
        super().mouseDoubleClickEvent(event)
    
    def resizeEvent(self, event):
        """Handle resize to fit content."""
        super().resizeEvent(event)
        self.fit_in_view()
    
    def fit_in_view(self):
        """Fit scene content in view while maintaining aspect ratio."""
        if self.scene() and self.scene().sceneRect().isValid():
            self.fitInView(
                self.scene().sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )


class PlaybackControls(QFrame):
    """
    Playback control bar with play/pause, step, and seek functionality.
    
    Signals:
        play_clicked: Play button clicked.
        pause_clicked: Pause button clicked.
        prev_clicked: Previous frame button clicked.
        next_clicked: Next frame button clicked.
        seek_requested(int): Slider position changed.
    """
    
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """Initialize playback controls."""
        super().__init__(parent)
        
        self._is_playing = False
        self._frame_count = 0
        self._current_frame = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the control bar UI."""
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f7;
                border-top: 1px solid #e5e5ea;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFixedSize(24, 32)
        self._prev_btn.setToolTip("Previous Frame")
        self._prev_btn.clicked.connect(self.prev_clicked.emit)
        layout.addWidget(self._prev_btn)
        
        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(24, 32)
        self._play_btn.setToolTip("Play")
        self._play_btn.clicked.connect(self._on_play_pause)
        layout.addWidget(self._play_btn)
        
        self._next_btn = QPushButton("▶")
        self._next_btn.setFixedSize(24, 32)
        self._next_btn.setToolTip("Next Frame")
        self._next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self._next_btn)
        
        layout.addSpacing(8)
        
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.setValue(0)
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider, 1)
        
        layout.addSpacing(8)
        
        self._frame_label = QLabel("0 / 0")
        self._frame_label.setMinimumWidth(75)
        self._frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._frame_label)
    
    def _on_play_pause(self):
        """Handle play/pause button click."""
        if self._is_playing:
            self._is_playing = False
            self._play_btn.setText("▶")
            self._play_btn.setToolTip("Play")
            self.pause_clicked.emit()
        else:
            self._is_playing = True
            self._play_btn.setText("⏸")
            self._play_btn.setToolTip("Pause")
            self.play_clicked.emit()
    
    def _on_slider_changed(self, value: int):
        """Handle slider value change."""
        self.seek_requested.emit(value)
    
    def set_frame_count(self, count: int):
        """Set total frame count."""
        self._frame_count = count
        self._slider.setMaximum(max(0, count - 1))
        self._update_label()
    
    def set_current_frame(self, frame: int):
        """Set current frame without emitting signal."""
        self._current_frame = frame
        self._slider.blockSignals(True)
        self._slider.setValue(frame)
        self._slider.blockSignals(False)
        self._update_label()
    
    def _update_label(self):
        """Update frame label."""
        self._frame_label.setText(
            f"{self._current_frame + 1} / {self._frame_count}"
        )
    
    def set_playing(self, playing: bool):
        """Set playing state."""
        self._is_playing = playing
        if playing:
            self._play_btn.setText("⏸")
            self._play_btn.setToolTip("Pause")
        else:
            self._play_btn.setText("▶")
            self._play_btn.setToolTip("Play")


class PreviewWidget(QWidget):
    """
    Main preview widget containing graphics view and playback controls.
    
    Signals:
        object_double_clicked(int, int, int): Object ID, X, Y at double-click.
        label_position_changed(str, float, float): Label name and new position.
        play_requested: Play animation requested.
        pause_requested: Pause animation requested.
        frame_changed(int): Frame index changed via controls.
    """
    
    object_double_clicked = pyqtSignal(int, int, int)
    label_position_changed = pyqtSignal(str, float, float)
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    frame_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """Initialize preview widget."""
        super().__init__(parent)
        
        self._image_width = 0
        self._image_height = 0
        self._current_frame = 0
        
        # Store overlay enabled states for visibility control
        self._overlay_enabled_states = {
            'time': False,
            'scale_bar': False,
            'speed': False,
            'colorbar': False
        }
        self._overlay_visible = True  # Master visibility control
        
        self._setup_ui()
        self._setup_overlay_items()
    
    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._scene = QGraphicsScene(self)
        self._view = PreviewGraphicsView()
        self._view.setScene(self._scene)
        self._view.double_clicked.connect(self._on_double_click)
        
        # Set white background for preview area
        self._view.setStyleSheet("background-color: white;")
        self._scene.setBackgroundBrush(Qt.GlobalColor.white)
        
        layout.addWidget(self._view, 1)
        
        self._controls = PlaybackControls()
        self._controls.play_clicked.connect(self.play_requested.emit)
        self._controls.pause_clicked.connect(self.pause_requested.emit)
        self._controls.prev_clicked.connect(self._on_prev_frame)
        self._controls.next_clicked.connect(self._on_next_frame)
        self._controls.seek_requested.connect(self._on_seek)
        
        layout.addWidget(self._controls)
        
        self._image_item = QGraphicsPixmapItem()
        self._scene.addItem(self._image_item)
    
    def _setup_overlay_items(self):
        """Set up draggable overlay items."""
        self._time_label = DraggableTextLabel("time", "0.00 s")
        self._time_label.position_changed.connect(self._on_label_moved)
        self._time_label.setVisible(False)
        self._scene.addItem(self._time_label)
        
        self._scale_bar = DraggableScaleBar("scale_bar")
        self._scale_bar.position_changed.connect(self._on_label_moved)
        self._scale_bar.setVisible(False)
        self._scene.addItem(self._scale_bar)
        
        self._speed_label = DraggableTextLabel("speed", "1×")
        self._speed_label.position_changed.connect(self._on_label_moved)
        self._speed_label.setVisible(False)
        self._scene.addItem(self._speed_label)
        
        self._colorbar = DraggableColorbar("colorbar")
        self._colorbar.position_changed.connect(self._on_label_moved)
        self._colorbar.setVisible(False)
        self._scene.addItem(self._colorbar)
    
    def _on_double_click(self, x: float, y: float):
        """Handle double-click on scene."""
        int_x = int(x)
        int_y = int(y)
        
        if 0 <= int_x < self._image_width and 0 <= int_y < self._image_height:
            self.object_double_clicked.emit(self._current_frame, int_x, int_y)
    
    def _on_label_moved(self, name: str, rel_x: float, rel_y: float):
        """Handle label position change."""
        self.label_position_changed.emit(name, rel_x, rel_y)
    
    def _on_prev_frame(self):
        """Go to previous frame."""
        if self._current_frame > 0:
            self.frame_changed.emit(self._current_frame - 1)
    
    def _on_next_frame(self):
        """Go to next frame."""
        self.frame_changed.emit(self._current_frame + 1)
    
    def _on_seek(self, frame: int):
        """Seek to specific frame."""
        self.frame_changed.emit(frame)
    
    def set_image(self, pixmap: QPixmap):
        """Set the preview image."""
        self._image_item.setPixmap(pixmap)
        
        if pixmap.width() != self._image_width or pixmap.height() != self._image_height:
            self._image_width = pixmap.width()
            self._image_height = pixmap.height()
            
            self._scene.setSceneRect(0, 0, self._image_width, self._image_height)
            
            self._update_overlay_sizes()
            
            self._view.fit_in_view()
    
    def _update_overlay_sizes(self):
        """Update overlay item sizes for new image dimensions."""
        self._time_label.set_image_size(self._image_width, self._image_height)
        self._scale_bar.set_image_size(self._image_width, self._image_height)
        self._speed_label.set_image_size(self._image_width, self._image_height)
        self._colorbar.set_image_size(self._image_width, self._image_height)
    
    def set_frame_count(self, count: int):
        """Set total frame count."""
        self._controls.set_frame_count(count)
    
    def set_current_frame(self, frame: int):
        """Set current frame index."""
        self._current_frame = frame
        self._controls.set_current_frame(frame)
    
    def set_playing(self, playing: bool):
        """Set playing state."""
        self._controls.set_playing(playing)
    
    def update_time_label(
        self, text: str, visible: bool, font: str, size: int,
        bold: bool = False, color: str = 'white'
    ):
        """Update time label appearance."""
        self._time_label.set_text(text)
        self._time_label.set_font(font, size, bold)
        self._time_label.set_color(color)
        
        # Store enabled state and apply visibility
        self._overlay_enabled_states['time'] = visible
        self._time_label.setVisible(visible and self._overlay_visible)
    
    def update_scale_bar(
        self,
        visible: bool,
        length_px: int,
        thickness: int,
        bar_color: str,
        text: str,
        text_enabled: bool,
        text_position: str,
        text_gap: int,
        font: str,
        size: int,
        font_bold: bool = False,
        text_color: str = 'white'
    ):
        """Update scale bar appearance."""
        self._scale_bar.set_bar_length(length_px)
        self._scale_bar.set_bar_thickness(thickness)
        self._scale_bar.set_bar_color(bar_color)
        self._scale_bar.set_text(text)
        self._scale_bar.set_text_enabled(text_enabled)
        self._scale_bar.set_text_position(text_position)
        self._scale_bar.set_text_gap(text_gap)
        self._scale_bar.set_font(font, size, font_bold)
        self._scale_bar.set_text_color(text_color)
        
        # Store enabled state and apply visibility
        self._overlay_enabled_states['scale_bar'] = visible
        self._scale_bar.setVisible(visible and self._overlay_visible)
    
    def update_speed_label(
        self, text: str, visible: bool, font: str, size: int,
        bold: bool = False, color: str = 'white'
    ):
        """Update speed label appearance."""
        self._speed_label.set_text(text)
        self._speed_label.set_font(font, size, bold)
        self._speed_label.set_color(color)
        
        # Store enabled state and apply visibility
        self._overlay_enabled_states['speed'] = visible
        self._speed_label.setVisible(visible and self._overlay_visible)
    
    def update_colorbar(
        self,
        visible: bool,
        colormap_image,
        bar_height: int,
        bar_width: int,
        title: str,
        title_position: str,
        title_gap: int,
        vmin: float,
        vmax: float,
        tick_interval: float,
        title_font: str,
        title_size: int,
        title_bold: bool,
        title_color: str,
        tick_font: str,
        tick_size: int,
        tick_bold: bool,
        tick_color: str
    ):
        """Update colorbar appearance."""
        self._colorbar.set_bar_size(bar_width, bar_height)
        self._colorbar.set_colormap_image(colormap_image)
        self._colorbar.set_title(title)
        self._colorbar.set_title_position(title_position)
        self._colorbar.set_title_gap(title_gap)
        self._colorbar.set_range(vmin, vmax, tick_interval)
        self._colorbar.set_fonts(
            title_font, title_size, title_bold,
            tick_font, tick_size, tick_bold
        )
        self._colorbar.set_title_color(title_color)
        self._colorbar.set_tick_color(tick_color)
        
        # Store enabled state and apply visibility
        self._overlay_enabled_states['colorbar'] = visible
        self._colorbar.setVisible(visible and self._overlay_visible)
    
    def set_label_position(self, name: str, rel_x: float, rel_y: float):
        """Set label position."""
        if name == "time":
            self._time_label.set_relative_position(rel_x, rel_y)
        elif name == "scale_bar":
            self._scale_bar.set_relative_position(rel_x, rel_y)
        elif name == "speed":
            self._speed_label.set_relative_position(rel_x, rel_y)
        elif name == "colorbar":
            self._colorbar.set_relative_position(rel_x, rel_y)
    
    def get_label_position(self, name: str) -> tuple[float, float]:
        """Get label position."""
        if name == "time":
            return self._time_label.get_relative_position()
        elif name == "scale_bar":
            return self._scale_bar.get_relative_position()
        elif name == "speed":
            return self._speed_label.get_relative_position()
        elif name == "colorbar":
            return self._colorbar.get_relative_position()
        return (0.0, 0.0)
    
    def set_overlay_visibility(self, visible: bool):
        """
        Set master visibility of all overlay items.
        
        When visible is False, all overlays are hidden (for final preview mode).
        When visible is True, overlays are shown based on their enabled states.
        
        Args:
            visible: Whether overlays should be visible.
        """
        self._overlay_visible = visible
        
        if visible:
            # Restore visibility based on enabled states
            self._time_label.setVisible(self._overlay_enabled_states['time'])
            self._scale_bar.setVisible(self._overlay_enabled_states['scale_bar'])
            self._speed_label.setVisible(self._overlay_enabled_states['speed'])
            self._colorbar.setVisible(self._overlay_enabled_states['colorbar'])
        else:
            # Hide all overlays
            self._time_label.setVisible(False)
            self._scale_bar.setVisible(False)
            self._speed_label.setVisible(False)
            self._colorbar.setVisible(False)