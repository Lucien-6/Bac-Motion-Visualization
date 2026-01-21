"""
Frame rendering engine.

Renders individual frames with all visualization elements:
masks, contours, trajectories, labels, scale bar, and colorbar.
"""

import os
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtGui import QFont, QFontMetrics

from ..models import (
    VisualizationConfig,
    DataManager,
    TrajectoryCalculator,
    ObjectManager,
)
from .color_mapper import ColorMapper
from ..utils import get_logger

logger = get_logger(__name__)

# Color name to BGR mapping
COLOR_NAME_TO_BGR = {
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'yellow': (0, 255, 255),
}

# Windows system font directory
WINDOWS_FONT_DIR = "C:/Windows/Fonts"

# Font file mapping: (family, bold) -> filename
FONT_FILES = {
    ('Arial', False): 'arial.ttf',
    ('Arial', True): 'arialbd.ttf',
    ('Times New Roman', False): 'times.ttf',
    ('Times New Roman', True): 'timesbd.ttf',
}


class FrameRenderer:
    """
    Renders complete visualization frames.
    
    Combines original images with masks, contours, trajectories,
    and annotation elements based on configuration.
    """
    
    def __init__(
        self,
        data_manager: DataManager,
        trajectory_calculator: TrajectoryCalculator,
        object_manager: ObjectManager,
        color_mapper: ColorMapper,
        config: VisualizationConfig,
    ):
        """
        Initialize frame renderer.
        
        Args:
            data_manager: Data manager with loaded sequences.
            trajectory_calculator: Calculated trajectories.
            object_manager: Object visibility manager.
            color_mapper: Color assignment manager.
            config: Visualization configuration.
        """
        self.data_manager = data_manager
        self.trajectory_calculator = trajectory_calculator
        self.object_manager = object_manager
        self.color_mapper = color_mapper
        self.config = config
        
        self._label_positions: dict[str, tuple[float, float]] = {}
        
        # Font cache for PIL rendering
        self._font_cache: dict[tuple, ImageFont.FreeTypeFont] = {}
        self._pil_available = self._check_pil_fonts()
    
    def _check_pil_fonts(self) -> bool:
        """
        Check if PIL fonts are available on the system.
        
        Returns:
            True if TrueType fonts can be loaded, False otherwise.
        """
        try:
            test_font_path = os.path.join(WINDOWS_FONT_DIR, 'arial.ttf')
            if os.path.exists(test_font_path):
                ImageFont.truetype(test_font_path, 12)
                logger.info("PIL font rendering enabled")
                return True
        except Exception as e:
            logger.warning(f"PIL font loading failed: {e}")
        return False
    
    def _get_font(
        self,
        family: str,
        size: int,
        bold: bool
    ) -> ImageFont.FreeTypeFont:
        """
        Get or create a PIL font from cache.
        
        Args:
            family: Font family name ('Arial' or 'Times New Roman').
            size: Font size in pixels.
            bold: Whether to use bold variant.
            
        Returns:
            PIL ImageFont object.
        """
        key = (family, size, bold)
        
        if key in self._font_cache:
            return self._font_cache[key]
        
        font_file = FONT_FILES.get((family, bold))
        if font_file is None:
            font_file = FONT_FILES.get((family, False), 'arial.ttf')
        
        font_path = os.path.join(WINDOWS_FONT_DIR, font_file)
        
        try:
            font = ImageFont.truetype(font_path, size)
        except Exception as e:
            logger.warning(f"Failed to load font {font_path}: {e}")
            # Fallback: try arial.ttf
            try:
                font = ImageFont.truetype(
                    os.path.join(WINDOWS_FONT_DIR, 'arial.ttf'),
                    size
                )
            except Exception:
                # Last resort: default font (not ideal but functional)
                font = ImageFont.load_default()
        
        self._font_cache[key] = font
        return font
    
    def _estimate_text_width(
        self,
        text: str,
        font_size: int,
        bold: bool
    ) -> int:
        """
        Estimate text width using PIL for accurate measurement.
        
        Args:
            text: Text to measure.
            font_size: Font size in pixels.
            bold: Whether font is bold.
            
        Returns:
            Estimated width in pixels.
        """
        if self._pil_available:
            font = self._get_font('Arial', font_size, bold)
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        else:
            # Fallback estimation using OpenCV
            scale = font_size / 30
            thickness = max(2, int(font_size / 10)) if bold else max(1, int(font_size / 15))
            (w, _), _ = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness
            )
            return w
    
    def set_label_position(self, label_name: str, position: tuple[float, float]):
        """
        Set custom position for a label (from drag operation).
        
        Args:
            label_name: Name of the label ('time', 'scale_bar', 'speed', 'colorbar').
            position: Relative position (x, y) as fractions of image size.
        """
        self._label_positions[label_name] = position
    
    def get_label_position(self, label_name: str) -> tuple[float, float]:
        """Get current label position."""
        if label_name in self._label_positions:
            return self._label_positions[label_name]
        
        defaults = {
            'time': self.config.time_label.position,
            'scale_bar': self.config.scale_bar.position,
            'speed': self.config.speed_label.position,
            'colorbar': self.config.colorbar.position,
        }
        pos = defaults.get(label_name, [0.0, 0.0])
        return (pos[0], pos[1])
    
    def render_frame(
        self,
        frame_index: int,
        include_colorbar_area: bool = False,
        draw_labels: bool = True
    ) -> np.ndarray:
        """
        Render a complete visualization frame.
        
        Args:
            frame_index: Frame index to render.
            include_colorbar_area: If True, extend image to include colorbar area.
            draw_labels: If True, draw labels on image. Set False for preview
                        (labels shown as draggable overlays instead).
            
        Returns:
            Rendered frame as BGR numpy array.
        """
        base_image = self.data_manager.get_frame(frame_index)
        if base_image is None:
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        result = base_image.copy()
        
        # Record original image dimensions before any extension
        # All label positions (except colorbar) are relative to this size
        original_height, original_width = result.shape[:2]
        
        mask = self.data_manager.get_mask(frame_index)
        
        if mask is not None and self.config.mask.enabled:
            result = self._overlay_mask(result, mask, frame_index)
        
        if mask is not None and self.config.contour.enabled:
            result = self._draw_contours(result, mask, frame_index)
        
        if mask is not None and (
            self.config.ellipse_axes.show_major_axis or
            self.config.ellipse_axes.show_minor_axis
        ):
            result = self._draw_ellipse_axes(result, mask, frame_index)
        
        if self.config.trajectory.enabled:
            result = self._draw_trajectories(result, frame_index)
        
        # Draw centroids on top layer
        if mask is not None and self.config.centroid.enabled:
            result = self._draw_centroids(result, mask, frame_index)
        
        # Extend image if colorbar exceeds boundaries
        if include_colorbar_area and self.config.colorbar.enabled and \
           self.config.trajectory.color_mode == 'velocity':
            result = self._extend_for_colorbar(result)
            # Log extension for debugging
            if result.shape[:2] != (original_height, original_width):
                logger.debug(
                    f"Image extended from {original_width}x{original_height} "
                    f"to {result.shape[1]}x{result.shape[0]} for colorbar"
                )
        
        # Only draw labels when exporting (draw_labels=True)
        # For preview, labels are shown as draggable overlays
        # Note: All labels except colorbar use original dimensions to maintain
        # consistent positioning between edit and final preview modes
        if draw_labels:
            if self.config.time_label.enabled:
                result = self._draw_time_label(
                    result, frame_index, original_width, original_height
                )
            
            if self.config.scale_bar.enabled:
                result = self._draw_scale_bar(
                    result, original_width, original_height
                )
            
            if self.config.speed_label.enabled:
                result = self._draw_speed_label(
                    result, original_width, original_height
                )
            
            if self.config.colorbar.enabled and \
               self.config.trajectory.color_mode == 'velocity':
                result = self._draw_colorbar(result, original_width, original_height)
        
        return result
    
    def _overlay_mask(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        frame_index: int
    ) -> np.ndarray:
        """Overlay colored mask on image."""
        result = image.copy()
        opacity = self.config.mask.opacity
        
        colored_mask = np.zeros_like(image)
        
        for obj_id in self.data_manager.object_ids:
            if not self.object_manager.is_visible(obj_id, frame_index):
                continue
            
            obj_mask = mask == obj_id
            if not np.any(obj_mask):
                continue
            
            color = self.color_mapper.get_object_color_bgr(obj_id)
            colored_mask[obj_mask] = color
        
        mask_region = mask > 0
        result[mask_region] = cv2.addWeighted(
            image[mask_region], 1 - opacity,
            colored_mask[mask_region], opacity,
            0
        )
        
        return result
    
    def _draw_contours(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        frame_index: int
    ) -> np.ndarray:
        """Draw object contours on image."""
        result = image.copy()
        thickness = self.config.contour.thickness
        
        for obj_id in self.data_manager.object_ids:
            if not self.object_manager.is_visible(obj_id, frame_index):
                continue
            
            obj_mask = (mask == obj_id).astype(np.uint8)
            if not np.any(obj_mask):
                continue
            
            contours, _ = cv2.findContours(
                obj_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            color = self.color_mapper.get_object_color_bgr(obj_id)
            cv2.drawContours(result, contours, -1, color, thickness)
        
        return result
    
    def _draw_centroids(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        frame_index: int
    ) -> np.ndarray:
        """Draw object centroids on image."""
        result = image.copy()
        cfg = self.config.centroid
        
        for obj_id in self.data_manager.object_ids:
            if not self.object_manager.is_visible(obj_id, frame_index):
                continue
            
            centroid = self.trajectory_calculator.get_centroid(obj_id, frame_index)
            if centroid is None:
                continue
            
            cx, cy = int(centroid[0]), int(centroid[1])
            color = self.color_mapper.get_object_color_bgr(obj_id)
            size = cfg.marker_size
            
            if cfg.marker_shape == 'circle':
                cv2.circle(result, (cx, cy), size, color, -1)
            elif cfg.marker_shape == 'triangle':
                pts = np.array([
                    [cx, cy - size],
                    [cx - size, cy + size],
                    [cx + size, cy + size]
                ], np.int32)
                cv2.fillPoly(result, [pts], color)
            elif cfg.marker_shape == 'star':
                self._draw_star(result, cx, cy, size, color)
        
        return result
    
    def _draw_star(
        self,
        image: np.ndarray,
        cx: int,
        cy: int,
        size: int,
        color: tuple
    ):
        """Draw a 5-pointed star filled with color."""
        import math
        
        outer_radius = size
        inner_radius = size * 0.4
        
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            if i % 2 == 0:
                r = outer_radius
            else:
                r = inner_radius
            x = cx + int(r * math.cos(angle))
            y = cy - int(r * math.sin(angle))
            points.append([x, y])
        
        pts = np.array(points, np.int32)
        cv2.fillPoly(image, [pts], color)
    
    def _draw_ellipse_axes(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        frame_index: int
    ) -> np.ndarray:
        """Draw fitted ellipse major/minor axes on image."""
        result = image.copy()
        cfg = self.config.ellipse_axes
        
        # Get independent colors and thicknesses for major and minor axes
        major_color = COLOR_NAME_TO_BGR.get(cfg.major_color, (255, 255, 255))
        minor_color = COLOR_NAME_TO_BGR.get(cfg.minor_color, (255, 255, 255))
        major_thickness = cfg.major_thickness
        minor_thickness = cfg.minor_thickness
        
        for obj_id in self.data_manager.object_ids:
            if not self.object_manager.is_visible(obj_id, frame_index):
                continue
            
            obj_mask = (mask == obj_id).astype(np.uint8)
            if not np.any(obj_mask):
                continue
            
            contours, _ = cv2.findContours(
                obj_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                continue
            
            # Get largest contour
            contour = max(contours, key=cv2.contourArea)
            
            # Need at least 5 points to fit ellipse
            if len(contour) < 5:
                continue
            
            try:
                ellipse = cv2.fitEllipse(contour)
                (cx, cy), (ma, MA), angle = ellipse
                
                # Convert to integers
                cx, cy = int(cx), int(cy)
                
                # Major axis length and minor axis length
                major_len = int(MA / 2)
                minor_len = int(ma / 2)
                
                # Calculate axis endpoints
                angle_rad = np.radians(angle)
                cos_a = np.cos(angle_rad)
                sin_a = np.sin(angle_rad)
                
                # Major axis endpoints (perpendicular to angle)
                major_dx = int(major_len * sin_a)
                major_dy = int(major_len * cos_a)
                major_pt1 = (cx - major_dx, cy + major_dy)
                major_pt2 = (cx + major_dx, cy - major_dy)
                
                # Minor axis endpoints
                minor_dx = int(minor_len * cos_a)
                minor_dy = int(minor_len * sin_a)
                minor_pt1 = (cx - minor_dx, cy - minor_dy)
                minor_pt2 = (cx + minor_dx, cy + minor_dy)
                
                # Draw axes with solid lines
                if cfg.show_major_axis:
                    cv2.line(result, major_pt1, major_pt2, major_color, major_thickness, cv2.LINE_AA)
                if cfg.show_minor_axis:
                    cv2.line(result, minor_pt1, minor_pt2, minor_color, minor_thickness, cv2.LINE_AA)
                        
            except cv2.error:
                continue
        
        return result
    
    def _draw_trajectories(
        self,
        image: np.ndarray,
        frame_index: int
    ) -> np.ndarray:
        """Draw object trajectories on image."""
        result = image.copy()
        thickness = self.config.trajectory.thickness
        mode = self.config.trajectory.mode
        color_mode = self.config.trajectory.color_mode
        
        fps = self.config.global_config.original_fps
        delay_frames = int(self.config.trajectory.delay_time * fps)
        
        for obj_id in self.data_manager.object_ids:
            trajectory = self._get_trajectory_segment_for_mode(
                obj_id, frame_index, mode, delay_frames
            )
            
            if len(trajectory) < 2:
                continue
            
            visible_traj = [
                (f, x, y) for f, x, y in trajectory
                if self.object_manager.is_visible(obj_id, f)
            ]
            
            if len(visible_traj) < 2:
                continue
            
            if color_mode == 'object':
                color = self.color_mapper.get_object_color_bgr(obj_id)
                points = [(int(x), int(y)) for _, x, y in visible_traj]
                
                for i in range(len(points) - 1):
                    cv2.line(result, points[i], points[i + 1], color, thickness)
            else:
                vmin = self.config.colorbar.vmin
                vmax = self.config.colorbar.vmax
                colormap = self.config.colorbar.colormap
                
                for i in range(len(visible_traj) - 1):
                    f1, x1, y1 = visible_traj[i]
                    f2, x2, y2 = visible_traj[i + 1]
                    
                    velocity = self.trajectory_calculator.get_velocity(obj_id, f2)
                    if velocity is None:
                        velocity = 0.0
                    
                    color = self.color_mapper.get_velocity_color_bgr(
                        velocity, vmin, vmax, colormap
                    )
                    
                    pt1 = (int(x1), int(y1))
                    pt2 = (int(x2), int(y2))
                    cv2.line(result, pt1, pt2, color, thickness)
        
        return result
    
    def _get_trajectory_segment_for_mode(
        self,
        obj_id: int,
        frame_index: int,
        mode: str,
        delay_frames: int
    ) -> list[tuple[int, float, float]]:
        """Get trajectory segment based on display mode."""
        full_traj = self.trajectory_calculator.get_trajectory(obj_id)
        
        if not full_traj:
            return []
        
        if mode == 'full':
            return full_traj
        
        elif mode == 'start_to_current':
            return [(f, x, y) for f, x, y in full_traj if f <= frame_index]
        
        elif mode == 'delay_before':
            start_frame = max(0, frame_index - delay_frames)
            return [(f, x, y) for f, x, y in full_traj 
                    if start_frame <= f <= frame_index]
        
        elif mode == 'delay_after':
            end_frame = frame_index + delay_frames
            return [(f, x, y) for f, x, y in full_traj 
                    if frame_index <= f <= end_frame]
        
        return full_traj
    
    def _draw_time_label(
        self,
        image: np.ndarray,
        frame_index: int,
        original_width: int,
        original_height: int
    ) -> np.ndarray:
        """
        Draw time label on image with high quality rendering.
        
        Args:
            image: Input BGR image (possibly extended).
            frame_index: Current frame index.
            original_width: Original image width before extension.
            original_height: Original image height before extension.
            
        Returns:
            Image with time label drawn.
        """
        cfg = self.config.time_label
        
        fps = self.config.global_config.original_fps
        time_seconds = frame_index / fps if fps > 0 else 0
        
        # Format time text based on unit
        unit = cfg.unit
        if unit == 'ms':
            time_value = time_seconds * 1000
            text = f"{time_value:.1f} ms"
        elif unit == 's':
            text = f"{time_seconds:.2f} s"
        elif unit == 'min':
            time_value = time_seconds / 60
            text = f"{time_value:.2f} min"
        elif unit == 'h':
            time_value = time_seconds / 3600
            text = f"{time_value:.3f} h"
        else:
            text = f"{time_seconds:.2f} s"
        
        pos = self.get_label_position('time')
        # Use original dimensions to maintain consistent positioning
        x = int(pos[0] * original_width)
        y = int(pos[1] * original_height)
        
        color = COLOR_NAME_TO_BGR.get(cfg.color, (255, 255, 255))
        
        # Calculate Qt font metrics for accurate alignment
        qt_font = QFont(cfg.font_family)
        qt_font.setPixelSize(cfg.font_size)
        qt_font.setBold(cfg.font_bold)
        qt_fm = QFontMetrics(qt_font)
        qt_text_rect = qt_fm.boundingRect(text)
        
        return self._draw_text(
            image, text, (x, y),
            cfg.font_family, cfg.font_size, cfg.font_bold, color,
            qt_text_width=qt_text_rect.width(),
            qt_text_height=qt_text_rect.height()
        )
    
    def _draw_scale_bar(
        self,
        image: np.ndarray,
        original_width: int,
        original_height: int
    ) -> np.ndarray:
        """
        Draw scale bar with high quality text rendering.
        
        Args:
            image: Input BGR image (possibly extended).
            original_width: Original image width before extension.
            original_height: Original image height before extension.
            
        Returns:
            Image with scale bar drawn.
        """
        result = image.copy()
        cfg = self.config.scale_bar
        
        um_per_pixel = self.config.global_config.um_per_pixel
        if um_per_pixel <= 0:
            return result
        
        bar_length_px = int(cfg.length_um / um_per_pixel)
        
        pos = self.get_label_position('scale_bar')
        # (x, y) is top-left of bounding box (matching Qt setPos)
        # Use original dimensions to maintain consistent positioning
        x = int(pos[0] * original_width)
        y = int(pos[1] * original_height)
        
        bar_color = COLOR_NAME_TO_BGR.get(cfg.bar_color, (255, 255, 255))
        
        # Bar position within bounding box (matching Qt bar_x = 10)
        bar_x_offset = 10
        bar_x = x + bar_x_offset
        
        # Calculate bar Y position (matching Qt's layout logic)
        half_thickness = cfg.thickness // 2
        if cfg.text_position == 'below':
            # Bar at top, text below (matching Qt bar_y = 8 + half_thickness)
            bar_y = y + 8 + half_thickness
        else:
            # Text at top, bar below
            # Need to account for text height to match Qt layout
            bar_y = y + cfg.font_size + 2 + cfg.text_gap + half_thickness
        
        # Draw scale bar as filled rectangle (square ends)
        # Match Qt's drawRect behavior exactly
        # cv2.rectangle fills [pt1, pt2] (closed interval), Qt fills [y, y+h)
        # So pt2 coordinates must be -1 to match Qt's open interval
        bar_top = bar_y - half_thickness
        bar_height = cfg.thickness
        pt1 = (bar_x, bar_top)
        pt2 = (bar_x + bar_length_px - 1, bar_top + bar_height - 1)
        cv2.rectangle(result, pt1, pt2, bar_color, -1)  # -1 = filled
        
        if cfg.text_enabled:
            text = f"{cfg.length_um:.0f} μm"
            # Text centered horizontally over the bar
            text_x = bar_x + bar_length_px // 2
            
            # Calculate text baseline position (matching Qt logic exactly)
            # Use Qt font metrics to get accurate ascent
            qt_font = QFont(cfg.font_family)
            qt_font.setPixelSize(cfg.font_size)
            qt_font.setBold(cfg.font_bold)
            qt_fm = QFontMetrics(qt_font)
            ascent = qt_fm.ascent()
            
            if cfg.text_position == 'above':
                # Text above bar (matching Qt logic)
                bar_top = bar_y - half_thickness
                text_baseline_y = bar_top - cfg.text_gap
            else:
                # Text below bar (matching Qt: bar_bottom + text_gap + ascent)
                bar_bottom = bar_y + half_thickness
                text_baseline_y = bar_bottom + cfg.text_gap + ascent
            
            text_color = COLOR_NAME_TO_BGR.get(cfg.text_color, (255, 255, 255))
            
            # Use special method for baseline-positioned text
            result = self._draw_text_baseline(
                result, text, (text_x, text_baseline_y),
                cfg.font_family, cfg.font_size, cfg.font_bold, text_color,
                qt_ascent=ascent
            )
        
        return result
    
    def _draw_speed_label(
        self,
        image: np.ndarray,
        original_width: int,
        original_height: int
    ) -> np.ndarray:
        """
        Draw playback speed label with high quality rendering.
        
        Args:
            image: Input BGR image (possibly extended).
            original_width: Original image width before extension.
            original_height: Original image height before extension.
            
        Returns:
            Image with speed label drawn.
        """
        cfg = self.config.speed_label
        
        speed_text = self.config.get_speed_ratio_text()
        
        pos = self.get_label_position('speed')
        # Use original dimensions to maintain consistent positioning
        x = int(pos[0] * original_width)
        y = int(pos[1] * original_height)
        
        color = COLOR_NAME_TO_BGR.get(cfg.color, (255, 255, 255))
        
        # Calculate Qt font metrics for accurate alignment
        qt_font = QFont(cfg.font_family)
        qt_font.setPixelSize(cfg.font_size)
        qt_font.setBold(cfg.font_bold)
        qt_fm = QFontMetrics(qt_font)
        qt_text_rect = qt_fm.boundingRect(speed_text)
        
        return self._draw_text(
            image, speed_text, (x, y),
            cfg.font_family, cfg.font_size, cfg.font_bold, color,
            qt_text_width=qt_text_rect.width(),
            qt_text_height=qt_text_rect.height()
        )
    
    def _calculate_colorbar_bounds(
        self,
        image_width: int,
        image_height: int
    ) -> tuple[int, int, int, int]:
        """
        Calculate the actual bounding box of colorbar including all elements.
        
        Args:
            image_width: Original image width.
            image_height: Original image height.
            
        Returns:
            (left, top, right, bottom) - The bounding box coordinates.
        """
        cfg = self.config.colorbar
        pos = self.get_label_position('colorbar')
        
        # Colorbar anchor position (top-left of bounding box)
        x = int(pos[0] * image_width)
        y = int(pos[1] * image_height)
        
        # 1. Bar dimensions
        bar_width = cfg.bar_width
        bar_height = cfg.bar_height
        
        # 2. Use Qt font metrics for accurate calculations
        qt_title_font = QFont(cfg.title_font_family)
        qt_title_font.setPixelSize(cfg.title_font_size)
        qt_title_font.setBold(cfg.title_font_bold)
        qt_title_fm = QFontMetrics(qt_title_font)
        
        qt_tick_font = QFont(cfg.tick_font_family)
        qt_tick_font.setPixelSize(cfg.tick_font_size)
        qt_tick_font.setBold(cfg.tick_font_bold)
        qt_tick_fm = QFontMetrics(qt_tick_font)
        
        # Bar offset within bounding box (matching drawing logic with dynamic padding)
        bar_x_base = 5
        if cfg.title_position == 'top':
            # If title would extend left, bar shifts right
            title_width_val = qt_title_fm.horizontalAdvance(cfg.title) if cfg.title else 0
            title_center = bar_x_base + bar_width // 2
            title_left = title_center - title_width_val // 2
            left_padding = max(0, -title_left)
            bar_x_offset = bar_x_base + left_padding
        else:
            bar_x_offset = bar_x_base
        
        # 3. Calculate tick label width (based on max value digits)
        max_tick_text = f"{cfg.vmax:.2f}"
        max_tick_width = qt_tick_fm.horizontalAdvance(max_tick_text)
        
        # 4. Calculate title area
        title_width = 0
        title_height = 0
        if cfg.title:
            if cfg.title_position == 'top':
                # Title at top: ascent + 2 + descent + gap
                title_height = qt_title_fm.ascent() + 2 + qt_title_fm.descent() + cfg.title_gap
            else:  # right
                # Title on right (vertical text)
                # The rotated text image has width = font_height + 20 (with padding)
                # Text center is offset by descent/2 from translate point
                # So total width needed from tick labels edge:
                #   title_gap + font_height (translate offset) + rotated_width/2
                font_height = qt_title_fm.height()
                descent = font_height - qt_title_fm.ascent()
                rotated_width = font_height + 20
                # Right edge of title relative to title_x_base:
                #   font_height - descent//2 + rotated_width//2
                title_width = cfg.title_gap + font_height - descent // 2 + rotated_width // 2
        
        # 5. Determine bounds based on title position
        if cfg.title_position == 'top':
            left = x
            top = y
            
            # Calculate content width (bar + ticks)
            content_width = bar_x_offset + bar_width + cfg.tick_length + 3 + max_tick_width + 10
            
            # Calculate title width if present
            if cfg.title:
                title_width_total = qt_title_fm.horizontalAdvance(cfg.title) + bar_x_offset + 10
                # Right boundary should accommodate the wider of the two
                right = x + max(content_width, title_width_total)
            else:
                right = x + content_width
            
            bottom = y + title_height + bar_height + 10
        else:
            left = x
            top = y
            right = x + bar_x_offset + bar_width + cfg.tick_length + 3 + max_tick_width + title_width + 10
            bottom = y + 5 + bar_height + 10
        
        return (left, top, right, bottom)
    
    def _extend_for_colorbar(self, image: np.ndarray) -> np.ndarray:
        """
        Intelligently extend image for colorbar if needed.
        
        Only extends if colorbar elements exceed image boundaries.
        Extension amount is calculated precisely based on actual content.
        
        Args:
            image: Input BGR image.
            
        Returns:
            Original image or extended image with white background.
        """
        cfg = self.config.colorbar
        
        # Skip if colorbar is disabled or not in velocity mode
        if not cfg.enabled or self.config.trajectory.color_mode != 'velocity':
            return image
        
        h, w = image.shape[:2]
        
        # Calculate actual colorbar bounds
        left, top, right, bottom = self._calculate_colorbar_bounds(w, h)
        
        # Warn if colorbar is positioned outside top-left boundary
        if left < 0 or top < 0:
            logger.warning(
                f"Colorbar positioned outside top-left boundary "
                f"(left={left}, top={top}). Colorbar may be clipped."
            )
        
        # Calculate required extensions (with padding)
        extend_right = max(0, right - w + 15)  # +15 for padding
        extend_bottom = max(0, bottom - h + 10)
        
        # No extension needed - colorbar fits within image
        if extend_right == 0 and extend_bottom == 0:
            return image
        
        # Create extended image with white background
        new_w = w + extend_right
        new_h = h + extend_bottom
        
        extended = np.ones((new_h, new_w, 3), dtype=np.uint8) * 255
        extended[:h, :w] = image
        
        logger.debug(
            f"Extended image from {w}x{h} to {new_w}x{new_h} for colorbar"
        )
        
        return extended
    
    def _draw_text_baseline_simple(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_family: str,
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """
        Draw text using baseline positioning (matching Qt drawText behavior).
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) where x is left edge, y is baseline.
            font_family: Font family name.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            
        Returns:
            Image with text drawn.
        """
        if not self._pil_available:
            # Fallback to OpenCV
            result = image.copy()
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = font_size / 30
            thickness = max(1, int(font_size / 15))
            if font_bold:
                thickness = max(2, int(font_size / 10))
            
            x, y = position
            cv2.putText(
                result, text, (x, y), font, scale, color,
                thickness, cv2.LINE_AA
            )
            return result
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Get font
        font = self._get_font(font_family, font_size, font_bold)
        
        # Calculate text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        
        # Get Qt font metrics for accurate ascent
        qt_font = QFont(font_family)
        qt_font.setPixelSize(font_size)
        qt_font.setBold(font_bold)
        qt_fm = QFontMetrics(qt_font)
        ascent = qt_fm.ascent()
        
        x, y = position
        # y is baseline, convert to top-left for PIL
        draw_x = x - bbox[0]
        draw_y = y - ascent
        
        # Convert BGR color to RGB for PIL
        rgb_color = (color[2], color[1], color[0])
        
        # Draw text with antialiasing
        draw.text((draw_x, draw_y), text, font=font, fill=rgb_color)
        
        # Convert back to BGR numpy array
        result = np.array(pil_image)
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    
    def _draw_text_baseline_centered(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_family: str,
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """
        Draw text using baseline positioning with horizontal centering.
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) where x is horizontal center, y is baseline.
            font_family: Font family name.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            
        Returns:
            Image with text drawn.
        """
        if not self._pil_available:
            # Fallback to OpenCV
            result = image.copy()
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = font_size / 30
            thickness = max(1, int(font_size / 15))
            if font_bold:
                thickness = max(2, int(font_size / 10))
            
            (text_w, text_h), baseline = cv2.getTextSize(
                text, font, scale, thickness
            )
            
            x, y = position
            draw_x = x - text_w // 2
            draw_y = y  # OpenCV uses baseline
            
            cv2.putText(
                result, text, (draw_x, draw_y), font, scale, color,
                thickness, cv2.LINE_AA
            )
            return result
        
        # Use PIL with Qt metrics for accurate centering
        qt_font = QFont(font_family)
        qt_font.setPixelSize(font_size)
        qt_font.setBold(font_bold)
        qt_fm = QFontMetrics(qt_font)
        
        text_width = qt_fm.horizontalAdvance(text)
        ascent = qt_fm.ascent()
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Get font
        font = self._get_font(font_family, font_size, font_bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        
        x, y = position
        # x is horizontal center, y is baseline
        draw_x = x - text_width // 2 - bbox[0]
        draw_y = y - ascent
        
        # Convert BGR color to RGB for PIL
        rgb_color = (color[2], color[1], color[0])
        
        # Draw text with antialiasing
        draw.text((draw_x, draw_y), text, font=font, fill=rgb_color)
        
        # Convert back to BGR numpy array
        result = np.array(pil_image)
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    
    def _draw_vertical_text(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_family: str,
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """
        Draw vertical text (rotated 90 degrees counterclockwise) using PIL.
        
        Matches Qt's rotate(-90) behavior for vertical text rendering.
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) where x is left edge, y is vertical center.
            font_family: Font family name.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            
        Returns:
            Image with vertical text drawn.
        """
        if not self._pil_available:
            # Fallback: draw horizontal text if PIL unavailable
            return self._draw_text_internal(
                image, text, position, font_family, font_size, font_bold, color
            )
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # Get font and Qt metrics
        font = self._get_font(font_family, font_size, font_bold)
        qt_font = QFont(font_family)
        qt_font.setPixelSize(font_size)
        qt_font.setBold(font_bold)
        qt_fm = QFontMetrics(qt_font)
        
        # Get text dimensions
        text_width = qt_fm.horizontalAdvance(text)
        text_height = qt_fm.height()
        ascent = qt_fm.ascent()
        
        # Create text image (horizontal) with extra padding
        temp_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Convert BGR to RGB for PIL
        rgb_color = (color[2], color[1], color[0])
        
        # Draw text horizontally, centered in temp image
        temp_draw.text((10, 10), text, font=font, fill=rgb_color)
        
        # Rotate text 90 degrees counterclockwise (matching Qt rotate(-90))
        rotated_text = temp_img.rotate(90, expand=True)
        
        # Calculate paste position to match Qt's behavior:
        # Qt: painter.translate(tx, ty) then rotate(-90) then drawText(-text_width//2, ascent//2)
        # 
        # Qt's rotate(-90) is counter-clockwise 90 degrees.
        # After this rotation, coordinate transformation is: (x, y) -> (-y, x)
        # So drawText(-title_width//2, ascent//2) in rotated coords becomes:
        #   original_x = -ascent//2 (relative to translate point)
        #   original_y = -title_width//2 (relative to translate point)
        #
        # Text bounding box in original coords (relative to translate point):
        #   left:   -ascent//2 - descent
        #   right:  +ascent//2
        #   top:    -title_width//2
        #   bottom: +title_width//2
        #
        # Text horizontal center: (-ascent//2 - descent + ascent//2) / 2 = -descent/2
        # So text center is at (translate_x - descent/2, translate_y)
        
        x, y = position  # (translate_x, translate_y) in Qt terms
        descent = text_height - ascent
        
        # Rotated image dimensions
        rotated_width = text_height + 20
        rotated_height = text_width + 20
        
        # In PIL rotated image, text content is offset by padding (10px)
        # We want the text's horizontal center to align with (x - descent//2)
        # The rotated image center is at paste_x + rotated_width//2
        # So: paste_x + rotated_width//2 = x - descent//2
        # Therefore: paste_x = x - descent//2 - rotated_width//2
        paste_x = x - descent // 2 - rotated_width // 2
        
        # Text's vertical center should align with y
        # The rotated image center is at paste_y + rotated_height//2
        # So: paste_y + rotated_height//2 = y
        paste_y = y - rotated_height // 2
        
        # Paste rotated text onto main image
        pil_image.paste(rotated_text, (paste_x, paste_y), rotated_text)
        
        # Convert back to BGR numpy array
        result = np.array(pil_image.convert('RGB'))
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    
    def _draw_colorbar(
        self,
        image: np.ndarray,
        original_width: int,
        original_height: int
    ) -> np.ndarray:
        """
        Draw colorbar with high quality text rendering.
        
        Args:
            image: Input BGR image (possibly extended).
            original_width: Original image width before extension.
            original_height: Original image height before extension.
            
        Returns:
            Image with colorbar drawn.
        """
        result = image.copy()
        cfg = self.config.colorbar
        
        title_color = COLOR_NAME_TO_BGR.get(cfg.title_color, (0, 0, 0))
        tick_color = COLOR_NAME_TO_BGR.get(cfg.tick_color, (0, 0, 0))
        
        pos = self.get_label_position('colorbar')
        
        bar_width = cfg.bar_width
        bar_height = cfg.bar_height
        
        # Use original dimensions to maintain consistent positioning
        x = int(pos[0] * original_width)
        y = int(pos[1] * original_height)
        
        logger.debug(
            f"Drawing colorbar: rel_pos=({pos[0]:.3f}, {pos[1]:.3f}), "
            f"abs_pos=({x}, {y}), original=({original_width}x{original_height}), "
            f"extended=({image.shape[1]}x{image.shape[0]})"
        )
        
        # Get colormap image
        colorbar_img = self.color_mapper.get_colormap_image(
            cfg.colormap, bar_width, bar_height, 'vertical'
        )
        
        # Adjust bar_y based on title position
        # Use Qt font metrics to match editing mode exactly
        qt_title_font = QFont(cfg.title_font_family)
        qt_title_font.setPixelSize(cfg.title_font_size)
        qt_title_font.setBold(cfg.title_font_bold)
        qt_title_fm = QFontMetrics(qt_title_font)
        
        qt_tick_font = QFont(cfg.tick_font_family)
        qt_tick_font.setPixelSize(cfg.tick_font_size)
        qt_tick_font.setBold(cfg.tick_font_bold)
        qt_tick_fm = QFontMetrics(qt_tick_font)
        
        # Calculate bar_x with potential left padding for wide titles (matching editing mode)
        bar_x_base = 5
        if cfg.title_position == 'top':
            # If title would extend left of bounding rect, shift bar right
            title_width = qt_title_fm.horizontalAdvance(cfg.title) if cfg.title else 0
            title_center = bar_x_base + bar_width // 2
            title_left = title_center - title_width // 2
            left_padding = max(0, -title_left)
            bar_x = x + bar_x_base + left_padding
            
            if left_padding > 0:
                logger.debug(
                    f"Colorbar top title requires left padding: {left_padding}px "
                    f"(title_width={title_width}, bar_width={bar_width})"
                )
        else:
            bar_x = x + bar_x_base
        
        if cfg.title_position == 'top':
            # Match editing mode: title_y = ascent + 2, bar_y = title_y + descent + gap
            title_baseline_y = y + qt_title_fm.ascent() + 2
            bar_y = title_baseline_y + qt_title_fm.descent() + cfg.title_gap
        else:
            bar_y = y + 5  # Match editing mode bar_y = 5 offset
        
        # Draw colorbar image (allow drawing outside original bounds)
        end_y = bar_y + bar_height
        end_x = bar_x + bar_width
        
        # Ensure we don't exceed image dimensions (clamp to valid range)
        if bar_y >= 0 and bar_x >= 0 and end_y <= image.shape[0] and end_x <= image.shape[1]:
            result[bar_y:end_y, bar_x:end_x] = colorbar_img
        elif bar_y < image.shape[0] and bar_x < image.shape[1]:
            # Partial overlap - draw what we can
            clip_y_start = max(0, bar_y)
            clip_x_start = max(0, bar_x)
            clip_y_end = min(end_y, image.shape[0])
            clip_x_end = min(end_x, image.shape[1])
            
            src_y_start = clip_y_start - bar_y
            src_x_start = clip_x_start - bar_x
            src_y_end = src_y_start + (clip_y_end - clip_y_start)
            src_x_end = src_x_start + (clip_x_end - clip_x_start)
            
            if src_y_end > src_y_start and src_x_end > src_x_start:
                result[clip_y_start:clip_y_end, clip_x_start:clip_x_end] = \
                    colorbar_img[src_y_start:src_y_end, src_x_start:src_x_end]
        
        # Draw border with antialiasing
        cv2.rectangle(
            result, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
            tick_color, cfg.border_thickness, cv2.LINE_AA
        )
        
        # Draw title
        if cfg.title:
            if cfg.title_position == 'top':
                # Match editing mode: draw title centered over bar
                title_x = bar_x + bar_width // 2
                result = self._draw_text_baseline_centered(
                    result, cfg.title, (title_x, title_baseline_y),
                    cfg.title_font_family, cfg.title_font_size,
                    cfg.title_font_bold, title_color
                )
            else:
                # Title on right side - draw vertical text (rotated -90 degrees)
                # Match editing mode: title_x base position + height offset for Qt translate
                max_tick_width = qt_tick_fm.horizontalAdvance(f"{cfg.vmax:.2f}")
                title_x_base = bar_x + bar_width + cfg.tick_length + 3 + max_tick_width + cfg.title_gap
                # Qt translate uses title_x + font_height as anchor point
                title_x = title_x_base + qt_title_fm.height()
                title_y_center = bar_y + bar_height // 2
                
                result = self._draw_vertical_text(
                    result, cfg.title, (title_x, title_y_center),
                    cfg.title_font_family, cfg.title_font_size,
                    cfg.title_font_bold, title_color
                )
        
        # Draw tick marks and labels
        if cfg.vmax != cfg.vmin and cfg.tick_interval > 0:
            num_ticks = int((cfg.vmax - cfg.vmin) / cfg.tick_interval) + 1
            for i in range(num_ticks):
                value = cfg.vmax - i * cfg.tick_interval
                if value < cfg.vmin - 0.001:  # Small tolerance for float comparison
                    break
                
                # Calculate tick position
                ratio = (cfg.vmax - value) / (cfg.vmax - cfg.vmin)
                tick_y = bar_y + int(ratio * bar_height)
                
                # Draw tick line with antialiasing
                cv2.line(
                    result, (bar_x + bar_width, tick_y), (bar_x + bar_width + cfg.tick_length, tick_y),
                    tick_color, cfg.tick_thickness, cv2.LINE_AA
                )
                
                # Draw tick label - match editing mode: tick_y + ascent() // 2
                tick_text = f"{value:.2f}"
                tick_label_y = tick_y + qt_tick_fm.ascent() // 2
                result = self._draw_text_baseline_simple(
                    result, tick_text, (bar_x + bar_width + cfg.tick_length + 3, tick_label_y),
                    cfg.tick_font_family, cfg.tick_font_size,
                    cfg.tick_font_bold, tick_color
                )
        
        return result
    
    def _draw_text(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_family: str,
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (255, 255, 255),
        center: bool = False,
        qt_text_width: Optional[int] = None,
        qt_text_height: Optional[int] = None
    ) -> np.ndarray:
        """
        Draw high-quality text using PIL for journal-standard rendering.
        
        Uses Qt font metrics when provided to ensure visual alignment with
        draggable overlays in edit mode.
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) position.
            font_family: Font family name.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            center: If True, x is horizontal center position.
            qt_text_width: Qt-calculated text width (for alignment).
            qt_text_height: Qt-calculated text height (for alignment).
            
        Returns:
            Image with text drawn.
        """
        if not self._pil_available:
            return self._draw_text_opencv(
                image, text, position, font_size, font_bold, color, center,
                qt_text_width, qt_text_height
            )
        
        # Padding to match Qt DraggableTextLabel._padding
        padding = 6
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Get font
        font = self._get_font(font_family, font_size, font_bold)
        
        # Calculate text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        
        # Use Qt metrics if provided, otherwise use PIL metrics
        if qt_text_width is not None and qt_text_height is not None:
            text_width = qt_text_width
            text_height = qt_text_height
        else:
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        # Calculate bounding box size (text + padding on all sides)
        box_width = text_width + padding * 2
        box_height = text_height + padding * 2
        
        x, y = position
        
        if center:
            # x is horizontal center, y is top of text area (not bounding box)
            # Text is horizontally centered at x
            draw_x = x - text_width // 2 - bbox[0]
            draw_y = y - bbox[1]
        else:
            # (x, y) is top-left of bounding box (Qt uses this anchor)
            # Center text within the box to match Qt's AlignCenter behavior
            box_center_x = x + box_width // 2
            box_center_y = y + box_height // 2
            pil_text_width = bbox[2] - bbox[0]
            pil_text_height = bbox[3] - bbox[1]
            draw_x = box_center_x - pil_text_width // 2 - bbox[0]
            draw_y = box_center_y - pil_text_height // 2 - bbox[1]
        
        # Convert BGR color to RGB for PIL
        rgb_color = (color[2], color[1], color[0])
        
        # Draw text with antialiasing (PIL default)
        draw.text((draw_x, draw_y), text, font=font, fill=rgb_color)
        
        # Convert back to BGR numpy array
        result = np.array(pil_image)
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    
    def _draw_text_baseline(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_family: str,
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (255, 255, 255),
        qt_ascent: Optional[int] = None
    ) -> np.ndarray:
        """
        Draw text with baseline positioning (for scale bar).
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) where x is horizontal center, y is baseline.
            font_family: Font family name.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            
        Returns:
            Image with text drawn.
        """
        if not self._pil_available:
            # Fallback to OpenCV
            result = image.copy()
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = font_size / 30
            thickness = max(1, int(font_size / 15))
            if font_bold:
                thickness = max(2, int(font_size / 10))
            
            (text_w, text_h), baseline = cv2.getTextSize(
                text, font, scale, thickness
            )
            
            x, y = position
            draw_x = x - text_w // 2
            draw_y = y  # OpenCV uses baseline
            
            cv2.putText(
                result, text, (draw_x, draw_y), font, scale, color,
                thickness, cv2.LINE_AA
            )
            return result
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Get font
        font = self._get_font(font_family, font_size, font_bold)
        
        # Calculate text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Use Qt ascent if provided, otherwise estimate
        if qt_ascent is not None:
            ascent = qt_ascent
        else:
            # Fallback estimation (not accurate)
            ascent = int(font_size * 0.8)
        
        x, y = position
        # x is horizontal center, y is baseline
        draw_x = x - text_width // 2 - bbox[0]
        draw_y = y - ascent  # Convert baseline to top-left
        
        # Convert BGR color to RGB for PIL
        rgb_color = (color[2], color[1], color[0])
        
        # Draw text with antialiasing
        draw.text((draw_x, draw_y), text, font=font, fill=rgb_color)
        
        # Convert back to BGR numpy array
        result = np.array(pil_image)
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    
    def _draw_text_opencv(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_size: int,
        font_bold: bool,
        color: tuple[int, int, int],
        center: bool,
        qt_text_width: Optional[int] = None,
        qt_text_height: Optional[int] = None
    ) -> np.ndarray:
        """
        Fallback text drawing using OpenCV (when PIL fonts unavailable).
        
        Position semantics match Qt DraggableTextLabel:
        - Non-centered: (x, y) is top-left of bounding box, text centered inside
        - Centered: x is horizontal center, y is top of bounding box
        - Bounding box has padding=6 on all sides (matching Qt)
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) position.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            center: If True, x is horizontal center position.
            
        Returns:
            Image with text drawn.
        """
        padding = 6
        
        result = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = font_size / 30
        thickness = max(1, int(font_size / 15))
        if font_bold:
            thickness = max(2, int(font_size / 10))
        
        (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
        
        # Use Qt metrics if provided
        if qt_text_width is not None and qt_text_height is not None:
            box_text_width = qt_text_width
            box_text_height = qt_text_height
        else:
            box_text_width = text_w
            box_text_height = text_h
        
        # Calculate bounding box size
        box_width = box_text_width + padding * 2
        box_height = box_text_height + padding * 2
        
        x, y = position
        if center:
            # x is horizontal center, y is top of text area (not bounding box)
            # Text is horizontally centered at x
            draw_x = x - text_w // 2
            # OpenCV putText uses baseline position
            draw_y = y + text_h
        else:
            # (x, y) is top-left of bounding box
            # Center text within the box to match Qt's AlignCenter behavior
            box_center_x = x + box_width // 2
            box_center_y = y + box_height // 2
            draw_x = box_center_x - text_w // 2
            # OpenCV putText uses baseline position
            draw_y = box_center_y + text_h // 2
        
        cv2.putText(
            result, text, (draw_x, draw_y), font, scale, color, thickness, cv2.LINE_AA
        )
        return result
    
    def _draw_text_simple(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """
        Draw simple text using PIL for colorbar tick labels.
        
        This method draws text directly at the specified position without
        padding, suitable for internal component text like colorbar labels.
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) position where y is the vertical center.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            
        Returns:
            Image with text drawn.
        """
        return self._draw_text_internal(
            image, text, position,
            'Arial', font_size, font_bold, color, center=False
        )
    
    def _draw_text_internal(
        self,
        image: np.ndarray,
        text: str,
        position: tuple[int, int],
        font_family: str,
        font_size: int,
        font_bold: bool = False,
        color: tuple[int, int, int] = (255, 255, 255),
        center: bool = False
    ) -> np.ndarray:
        """
        Internal text drawing without padding, for component internals.
        
        Position (x, y) where y is the vertical center of the text.
        
        Args:
            image: Input BGR image.
            text: Text to draw.
            position: (x, y) where y is vertical center.
            font_family: Font family name.
            font_size: Font size in pixels.
            font_bold: Whether to use bold font.
            color: BGR color tuple.
            center: If True, center text horizontally at position.
            
        Returns:
            Image with text drawn.
        """
        if not self._pil_available:
            # Fallback to OpenCV
            result = image.copy()
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = font_size / 30
            thickness = max(1, int(font_size / 15))
            if font_bold:
                thickness = max(2, int(font_size / 10))
            
            (text_w, text_h), baseline = cv2.getTextSize(
                text, font, scale, thickness
            )
            
            x, y = position
            if center:
                x = x - text_w // 2
            draw_y = y + text_h // 2
            
            cv2.putText(
                result, text, (x, draw_y), font, scale, color,
                thickness, cv2.LINE_AA
            )
            return result
        
        # Convert BGR to RGB for PIL
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        draw = ImageDraw.Draw(pil_image)
        
        # Get font
        font = self._get_font(font_family, font_size, font_bold)
        
        # Calculate text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x, y = position
        if center:
            draw_x = x - text_width // 2
        else:
            draw_x = x - bbox[0]
        
        # y is vertical center, so adjust to top-left
        draw_y = y - text_height // 2 - bbox[1]
        
        # Convert BGR color to RGB for PIL
        rgb_color = (color[2], color[1], color[0])
        
        # Draw text with antialiasing
        draw.text((draw_x, draw_y), text, font=font, fill=rgb_color)
        
        # Convert back to BGR numpy array
        result = np.array(pil_image)
        return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)