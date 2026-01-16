"""
Export controller.

Manages the export process for videos and image sequences.
"""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from ..models import VisualizationConfig, DataManager
from ..core import VideoExporter, FrameRenderer
from ..views import ExportDialog, ProgressDialog
from ..utils import get_logger, file_exists, confirm_overwrite, ensure_directory

logger = get_logger(__name__)


class ExportController(QObject):
    """
    Controls the export workflow.
    
    Signals:
        export_started: Export process started.
        export_finished(bool, str): Export finished with success status and message.
    """
    
    export_started = pyqtSignal()
    export_finished = pyqtSignal(bool, str)
    
    def __init__(
        self,
        data_manager: DataManager,
        config: VisualizationConfig,
        parent=None
    ):
        """
        Initialize export controller.
        
        Args:
            data_manager: Data manager instance.
            config: Visualization configuration.
            parent: Parent QObject.
        """
        super().__init__(parent)
        
        self._data_manager = data_manager
        self._config = config
        self._renderer: FrameRenderer | None = None
        
        self._exporter: VideoExporter | None = None
        self._progress_dialog: ProgressDialog | None = None
    
    def set_renderer(self, renderer: FrameRenderer):
        """Set the frame renderer to use for export."""
        self._renderer = renderer
    
    def set_config(self, config: VisualizationConfig):
        """Update configuration."""
        self._config = config
    
    def start_export(self, parent_widget=None) -> bool:
        """
        Start the export process.
        
        Shows export dialog, then progress dialog, and starts export.
        
        Args:
            parent_widget: Parent widget for dialogs.
            
        Returns:
            True if export started, False if cancelled.
        """
        if not self._data_manager.is_loaded:
            logger.error("Cannot export: data not loaded")
            return False
        
        if self._renderer is None:
            logger.error("Cannot export: renderer not set")
            return False
        
        export_dialog = ExportDialog(parent_widget)
        export_dialog.set_defaults(
            video_format=self._config.output.video_format,
            image_prefix=self._config.output.image_prefix,
            subfolder_name=self._config.output.subfolder_name,
            original_fps=self._config.global_config.original_fps,
            output_fps=self._config.global_config.output_fps
        )
        
        if export_dialog.exec() != ExportDialog.DialogCode.Accepted:
            logger.info("Export cancelled by user")
            return False
        
        settings = export_dialog.get_export_settings()
        
        if settings['export_video'] and settings['video_path']:
            if file_exists(settings['video_path']):
                if not confirm_overwrite(parent_widget, settings['video_path']):
                    return False
        
        if settings['export_images'] and settings['image_dir']:
            image_dir = Path(settings['image_dir'])
            if image_dir.exists():
                existing_images = list(image_dir.glob("*.png"))
                if existing_images:
                    if not confirm_overwrite(
                        parent_widget,
                        f"Images in {settings['image_dir']}"
                    ):
                        return False
        
        self._start_export_process(settings, parent_widget)
        return True
    
    def _start_export_process(self, settings: dict, parent_widget):
        """Start the actual export process."""
        self._progress_dialog = ProgressDialog("Exporting...", parent_widget)
        
        self._exporter = VideoExporter()
        self._exporter.set_renderer(self._renderer)
        self._exporter.set_frame_count(self._data_manager.frame_count)
        # Use output_fps from export settings (set in dialog)
        output_fps = settings.get('output_fps', self._config.global_config.output_fps)
        self._exporter.set_output_fps(output_fps)
        # Update config with the chosen output_fps
        self._config.global_config.output_fps = output_fps
        
        self._exporter.set_video_export(
            settings['export_video'],
            settings['video_path'],
            settings['video_format']
        )
        
        if settings['export_images']:
            ensure_directory(settings['image_dir'])
        
        self._exporter.set_image_export(
            settings['export_images'],
            settings['image_dir'],
            settings['image_prefix']
        )
        
        self._exporter.progress_updated.connect(self._on_progress_updated)
        self._exporter.frame_exported.connect(self._on_frame_exported)
        self._exporter.export_finished.connect(self._on_export_finished)
        
        self._progress_dialog.show()
        
        self.export_started.emit()
        self._exporter.start()
        
        logger.info("Export process started")
    
    def _on_progress_updated(self, percent: int, remaining_time: str):
        """Handle progress update from exporter."""
        if self._progress_dialog:
            self._progress_dialog.update_progress(percent, remaining_time)
            
            if self._progress_dialog.is_cancelled():
                self._exporter.cancel()
    
    def _on_frame_exported(self, frame_num: int):
        """Handle frame exported notification."""
        if self._progress_dialog:
            self._progress_dialog.set_frame_progress(
                frame_num, self._data_manager.frame_count
            )
    
    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        if self._progress_dialog:
            self._progress_dialog.finish(success, message)
        
        self.export_finished.emit(success, message)
        
        if success:
            logger.info(f"Export completed: {message}")
        else:
            logger.error(f"Export failed: {message}")
    
    def cancel_export(self):
        """Cancel ongoing export."""
        if self._exporter:
            self._exporter.cancel()
            logger.info("Export cancellation requested")
