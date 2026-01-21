"""
Preview controller.

Manages preview rendering, playback, and frame navigation.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from ..models import (
    DataManager, TrajectoryCalculator, ObjectManager, VisualizationConfig
)
from ..core import FrameRenderer, ColorMapper
from ..views import PreviewWidget
from ..utils import get_logger, numpy_to_qpixmap

logger = get_logger(__name__)


class PreviewController(QObject):
    """
    Controls preview rendering and playback.
    
    Signals:
        frame_rendered(int): Frame index rendered.
        object_clicked(int, int, int): Frame, object ID, and click position.
    """
    
    frame_rendered = pyqtSignal(int)
    object_clicked = pyqtSignal(int, int, int)
    
    def __init__(
        self,
        preview_widget: PreviewWidget,
        data_manager: DataManager,
        trajectory_calculator: TrajectoryCalculator,
        object_manager: ObjectManager,
        color_mapper: ColorMapper,
        parent=None
    ):
        """
        Initialize preview controller.
        
        Args:
            preview_widget: Preview widget to control.
            data_manager: Data manager instance.
            trajectory_calculator: Trajectory calculator instance.
            object_manager: Object manager instance.
            color_mapper: Color mapper instance.
            parent: Parent QObject.
        """
        super().__init__(parent)
        
        self._preview = preview_widget
        self._data_manager = data_manager
        self._trajectory_calculator = trajectory_calculator
        self._object_manager = object_manager
        self._color_mapper = color_mapper
        
        self._config = VisualizationConfig()
        self._renderer: FrameRenderer | None = None
        
        self._current_frame = 0
        self._is_playing = False
        
        # Preview mode: 'edit' for draggable overlays, 'final' for export preview
        self._preview_mode = 'edit'
        
        self._playback_timer = QTimer(self)
        self._playback_timer.timeout.connect(self._on_playback_tick)
        
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect preview widget signals."""
        self._preview.play_requested.connect(self.play)
        self._preview.pause_requested.connect(self.pause)
        self._preview.frame_changed.connect(self.seek)
        self._preview.object_double_clicked.connect(self._on_object_double_click)
        self._preview.label_position_changed.connect(self._on_label_position_changed)
    
    def set_config(self, config: VisualizationConfig):
        """Update configuration and refresh preview."""
        self._config = config
        
        if self._renderer:
            self._renderer.config = config
        
        self._update_playback_timer()
        self.update_preview()
    
    def set_preview_mode(self, mode: str):
        """
        Set preview mode.
        
        Args:
            mode: 'edit' for draggable overlays, 'final' for export preview.
        """
        if mode not in ['edit', 'final']:
            logger.warning(f"Invalid preview mode: {mode}")
            return
        
        self._preview_mode = mode
        self._preview.set_overlay_visibility(mode == 'edit')
        self.update_preview()
        
        logger.info(f"Preview mode changed to: {mode}")
    
    def get_preview_mode(self) -> str:
        """
        Get current preview mode.
        
        Returns:
            Current mode: 'edit' or 'final'.
        """
        return self._preview_mode
    
    def initialize_renderer(self):
        """Initialize the frame renderer."""
        if not self._data_manager.is_loaded:
            logger.warning("Cannot initialize renderer: data not loaded")
            return
        
        self._renderer = FrameRenderer(
            self._data_manager,
            self._trajectory_calculator,
            self._object_manager,
            self._color_mapper,
            self._config
        )
        
        self._preview.set_frame_count(self._data_manager.frame_count)
        
        # Set default label positions from config
        cfg = self._config
        self._preview.set_label_position(
            "time", cfg.time_label.position[0], cfg.time_label.position[1]
        )
        self._preview.set_label_position(
            "scale_bar", cfg.scale_bar.position[0], cfg.scale_bar.position[1]
        )
        self._preview.set_label_position(
            "speed", cfg.speed_label.position[0], cfg.speed_label.position[1]
        )
        self._preview.set_label_position(
            "colorbar", cfg.colorbar.position[0], cfg.colorbar.position[1]
        )
        
        logger.info("Renderer initialized")
    
    def update_preview(self):
        """Render and display current frame based on preview mode."""
        if self._renderer is None:
            return
        
        if self._preview_mode == 'edit':
            # Edit mode: draggable overlays, no labels on image
            frame = self._renderer.render_frame(
                self._current_frame,
                draw_labels=False,
                include_colorbar_area=False
            )
            pixmap = numpy_to_qpixmap(frame)
            self._preview.set_image(pixmap)
            self._update_overlay_items()
        else:
            # Final mode: exact export preview with all labels drawn
            frame = self._renderer.render_frame(
                self._current_frame,
                draw_labels=True,
                include_colorbar_area=True
            )
            pixmap = numpy_to_qpixmap(frame)
            self._preview.set_image(pixmap)
        
        self.frame_rendered.emit(self._current_frame)
    
    def _update_overlay_items(self):
        """Update overlay item appearances based on config."""
        cfg = self._config
        fps = cfg.global_config.original_fps
        
        time_seconds = self._current_frame / fps if fps > 0 else 0
        unit = cfg.time_label.unit
        if unit == 'ms':
            time_text = f"{time_seconds * 1000:.1f} ms"
        elif unit == 's':
            time_text = f"{time_seconds:.2f} s"
        elif unit == 'min':
            time_text = f"{time_seconds / 60:.2f} min"
        else:
            time_text = f"{time_seconds / 3600:.3f} h"
        
        self._preview.update_time_label(
            time_text,
            cfg.time_label.enabled,
            cfg.time_label.font_family,
            cfg.time_label.font_size,
            cfg.time_label.font_bold,
            cfg.time_label.color
        )
        
        um_per_pixel = cfg.global_config.um_per_pixel
        length_px = int(cfg.scale_bar.length_um / um_per_pixel) if um_per_pixel > 0 else 100
        scale_text = f"{cfg.scale_bar.length_um:.0f} μm"
        
        self._preview.update_scale_bar(
            cfg.scale_bar.enabled,
            length_px,
            cfg.scale_bar.thickness,
            cfg.scale_bar.bar_color,
            scale_text,
            cfg.scale_bar.text_enabled,
            cfg.scale_bar.text_position,
            cfg.scale_bar.text_gap,
            cfg.scale_bar.font_family,
            cfg.scale_bar.font_size,
            cfg.scale_bar.font_bold,
            cfg.scale_bar.text_color
        )
        
        speed_text = cfg.get_speed_ratio_text()
        self._preview.update_speed_label(
            speed_text,
            cfg.speed_label.enabled,
            cfg.speed_label.font_family,
            cfg.speed_label.font_size,
            cfg.speed_label.font_bold,
            cfg.speed_label.color
        )
        
        show_colorbar = (
            cfg.colorbar.enabled and
            cfg.trajectory.enabled and
            cfg.trajectory.color_mode == 'velocity'
        )
        
        if show_colorbar:
            colormap_img = self._color_mapper.get_colormap_image(
                cfg.colorbar.colormap,
                cfg.colorbar.bar_width,
                cfg.colorbar.bar_height,
                'vertical'
            )
        else:
            colormap_img = None
        
        self._preview.update_colorbar(
            show_colorbar,
            colormap_img,
            cfg.colorbar.bar_height,
            cfg.colorbar.bar_width,
            cfg.colorbar.title,
            cfg.colorbar.title_position,
            cfg.colorbar.title_gap,
            cfg.colorbar.vmin,
            cfg.colorbar.vmax,
            cfg.colorbar.tick_interval,
            cfg.colorbar.title_font_family,
            cfg.colorbar.title_font_size,
            cfg.colorbar.title_font_bold,
            cfg.colorbar.title_color,
            cfg.colorbar.tick_font_family,
            cfg.colorbar.tick_font_size,
            cfg.colorbar.tick_font_bold,
            cfg.colorbar.tick_color,
            cfg.colorbar.border_thickness,
            cfg.colorbar.tick_thickness,
            cfg.colorbar.tick_length
        )
    
    def _update_playback_timer(self):
        """Update playback timer interval based on FPS."""
        fps = self._config.global_config.output_fps
        if fps > 0:
            interval = int(1000 / fps)
            self._playback_timer.setInterval(max(10, interval))
    
    def play(self):
        """Start playback."""
        if not self._data_manager.is_loaded:
            return
        
        self._is_playing = True
        self._preview.set_playing(True)
        self._playback_timer.start()
        
        logger.info("Playback started")
    
    def pause(self):
        """Pause playback."""
        self._is_playing = False
        self._preview.set_playing(False)
        self._playback_timer.stop()
        
        logger.info("Playback paused")
    
    def seek(self, frame_index: int):
        """
        Seek to specific frame.
        
        Args:
            frame_index: Target frame index.
        """
        if not self._data_manager.is_loaded:
            return
        
        frame_count = self._data_manager.frame_count
        self._current_frame = max(0, min(frame_index, frame_count - 1))
        self._preview.set_current_frame(self._current_frame)
        self.update_preview()
    
    def next_frame(self):
        """Go to next frame."""
        self.seek(self._current_frame + 1)
    
    def prev_frame(self):
        """Go to previous frame."""
        self.seek(self._current_frame - 1)
    
    def _on_playback_tick(self):
        """Handle playback timer tick."""
        if not self._data_manager.is_loaded:
            self.pause()
            return
        
        next_frame = self._current_frame + 1
        
        if next_frame >= self._data_manager.frame_count:
            next_frame = 0
        
        self.seek(next_frame)
    
    def _on_object_double_click(self, frame: int, x: int, y: int):
        """Handle double-click on preview."""
        obj_id = self._data_manager.get_object_at_position(frame, x, y)
        
        if obj_id is not None:
            self.object_clicked.emit(frame, obj_id, self._current_frame)
            logger.info(f"Object {obj_id} clicked at frame {frame}")
    
    def _on_label_position_changed(self, name: str, rel_x: float, rel_y: float):
        """Handle label position change from dragging."""
        if self._renderer:
            self._renderer.set_label_position(name, (rel_x, rel_y))
            
            if name == 'time':
                self._config.time_label.position = [rel_x, rel_y]
            elif name == 'scale_bar':
                self._config.scale_bar.position = [rel_x, rel_y]
            elif name == 'speed':
                self._config.speed_label.position = [rel_x, rel_y]
            elif name == 'colorbar':
                self._config.colorbar.position = [rel_x, rel_y]
    
    @property
    def current_frame(self) -> int:
        """Get current frame index."""
        return self._current_frame
    
    @property
    def is_playing(self) -> bool:
        """Check if playback is active."""
        return self._is_playing
    
    @property
    def renderer(self) -> FrameRenderer | None:
        """Get the frame renderer."""
        return self._renderer
