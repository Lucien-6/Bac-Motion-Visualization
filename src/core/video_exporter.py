"""
Video and image sequence exporter.

Handles exporting visualization to video files and image sequences
with progress tracking and cancellation support.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import cv2
import imageio
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from .frame_renderer import FrameRenderer
from ..utils import get_logger, ensure_directory

logger = get_logger(__name__)


class VideoExporter(QThread):
    """
    Exports visualization to video and/or image sequence.
    
    Runs in a separate thread with progress reporting
    and cancellation support.
    
    Signals:
        progress_updated(int, str): Progress percentage and remaining time.
        frame_exported(int): Current frame number exported.
        export_finished(bool, str): Success status and message.
    """
    
    progress_updated = pyqtSignal(int, str)
    frame_exported = pyqtSignal(int)
    export_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        """Initialize video exporter."""
        super().__init__(parent)
        
        self._renderer: FrameRenderer | None = None
        self._frame_count: int = 0
        self._output_fps: float = 30.0
        
        self._export_video: bool = True
        self._video_path: str = ""
        self._video_format: str = "mp4"
        
        self._export_images: bool = True
        self._image_dir: str = ""
        self._image_prefix: str = "frame_"
        
        self._cancelled: bool = False
    
    def set_renderer(self, renderer: FrameRenderer):
        """Set the frame renderer."""
        self._renderer = renderer
    
    def set_frame_count(self, count: int):
        """Set total number of frames."""
        self._frame_count = count
    
    def set_output_fps(self, fps: float):
        """Set output video frame rate."""
        self._output_fps = fps
    
    def set_video_export(
        self,
        enabled: bool,
        path: str = "",
        format: str = "mp4"
    ):
        """Configure video export."""
        self._export_video = enabled
        self._video_path = path
        self._video_format = format
    
    def set_image_export(
        self,
        enabled: bool,
        directory: str = "",
        prefix: str = "frame_"
    ):
        """Configure image sequence export."""
        self._export_images = enabled
        self._image_dir = directory
        self._image_prefix = prefix
    
    def cancel(self):
        """Request cancellation of export."""
        self._cancelled = True
        logger.info("Export cancellation requested")
    
    def run(self):
        """Execute the export process."""
        self._cancelled = False
        
        if self._renderer is None:
            self.export_finished.emit(False, "Renderer not set")
            return
        
        if self._frame_count <= 0:
            self.export_finished.emit(False, "No frames to export")
            return
        
        try:
            start_time = time.time()
            
            video_writer = None
            if self._export_video and self._video_path:
                video_writer = self._create_video_writer()
                if video_writer is None:
                    self.export_finished.emit(False, "Failed to create video writer")
                    return
            
            if self._export_images and self._image_dir:
                ensure_directory(self._image_dir)
            
            image_save_executor = ThreadPoolExecutor(max_workers=4)
            pending_saves = []
            
            for frame_idx in range(self._frame_count):
                if self._cancelled:
                    break
                
                # Render frame with labels and colorbar area for both video and images
                frame = self._renderer.render_frame(
                    frame_idx,
                    draw_labels=True,
                    include_colorbar_area=True
                )
                
                if video_writer is not None:
                    if self._video_format == 'gif':
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        video_writer.append_data(rgb_frame)
                    else:
                        video_writer.write(frame)
                
                if self._export_images and self._image_dir:
                    future = image_save_executor.submit(
                        self._save_frame_image,
                        frame, frame_idx
                    )
                    pending_saves.append(future)
                
                progress = int((frame_idx + 1) / self._frame_count * 100)
                elapsed = time.time() - start_time
                
                if frame_idx > 0:
                    avg_time_per_frame = elapsed / (frame_idx + 1)
                    remaining_frames = self._frame_count - frame_idx - 1
                    remaining_time = avg_time_per_frame * remaining_frames
                    remaining_str = self._format_time(remaining_time)
                else:
                    remaining_str = "Calculating..."
                
                self.progress_updated.emit(progress, remaining_str)
                self.frame_exported.emit(frame_idx + 1)
            
            for future in pending_saves:
                future.result()
            
            image_save_executor.shutdown(wait=True)
            
            if video_writer is not None:
                if self._video_format == 'gif':
                    video_writer.close()
                else:
                    video_writer.release()
            
            if self._cancelled:
                self.export_finished.emit(False, "Export cancelled by user")
            else:
                total_time = time.time() - start_time
                msg = f"Export completed in {self._format_time(total_time)}"
                logger.info(msg)
                self.export_finished.emit(True, msg)
                
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            logger.error(error_msg)
            self.export_finished.emit(False, error_msg)
    
    def _create_video_writer(self):
        """Create appropriate video writer based on format."""
        # Get first frame with all labels and colorbar area
        first_frame = self._renderer.render_frame(
            0, draw_labels=True, include_colorbar_area=True
        )
        height, width = first_frame.shape[:2]
        
        if self._video_format == 'mp4':
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            return cv2.VideoWriter(
                self._video_path, fourcc, self._output_fps, (width, height)
            )
        
        elif self._video_format == 'avi':
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            return cv2.VideoWriter(
                self._video_path, fourcc, self._output_fps, (width, height)
            )
        
        elif self._video_format == 'gif':
            return imageio.get_writer(
                self._video_path,
                mode='I',
                fps=self._output_fps,
                loop=0
            )
        
        return None
    
    def _save_frame_image(self, frame: np.ndarray, frame_idx: int):
        """Save a single frame as PNG image."""
        filename = f"{self._image_prefix}{frame_idx + 1:06d}.png"
        filepath = Path(self._image_dir) / filename
        cv2.imwrite(str(filepath), frame)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time in seconds to human readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}:{minutes:02d}:{secs:02d}"
