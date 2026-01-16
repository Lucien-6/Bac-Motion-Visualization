"""
Main application controller.

Coordinates all components and handles user interactions.
"""

from pathlib import Path

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication

from ..models import (
    DataManager, TrajectoryCalculator, ObjectManager, VisualizationConfig,
    TrajectoryDataLoader
)
from ..core import ColorMapper
from ..views import MainWindow, ObjectDialog, DataLoadDialog
from ..utils import (
    get_logger, select_open_file, select_save_file
)
from .preview_controller import PreviewController
from .export_controller import ExportController

logger = get_logger(__name__)


class MainController(QObject):
    """
    Main application controller.
    
    Coordinates data loading, configuration management,
    preview rendering, and export operations.
    """
    
    def __init__(self):
        """Initialize main controller."""
        super().__init__()
        
        self._data_manager = DataManager()
        self._trajectory_calculator = TrajectoryCalculator()
        self._object_manager = ObjectManager()
        self._color_mapper = ColorMapper()
        self._config = VisualizationConfig()
        
        self._main_window = MainWindow()
        
        self._preview_controller = PreviewController(
            self._main_window.preview_widget,
            self._data_manager,
            self._trajectory_calculator,
            self._object_manager,
            self._color_mapper
        )
        
        self._export_controller = ExportController(
            self._data_manager,
            self._config
        )
        
        self._connect_signals()
        
        self._load_default_config()
    
    def _connect_signals(self):
        """Connect all signals."""
        window = self._main_window
        window.load_data_requested.connect(self._show_data_load_dialog)
        window.save_config_requested.connect(self._save_config)
        window.load_config_requested.connect(self._load_config)
        window.export_requested.connect(self._export)
        window.preview_mode_changed.connect(self._on_preview_mode_changed)
        
        panel = window.parameter_panel
        panel.config_changed.connect(self._on_config_changed)
        panel.restore_object_requested.connect(self._restore_object)
        panel.restore_all_requested.connect(self._restore_all_objects)
        
        self._preview_controller.object_clicked.connect(self._on_object_clicked)
        
        self._object_manager.records_changed.connect(self._on_hidden_records_changed)
        
        self._export_controller.export_finished.connect(self._on_export_finished)
    
    def _load_default_config(self):
        """Load default configuration."""
        default_path = Path(__file__).parent.parent.parent / "config" / "default_config.json"
        
        if default_path.exists():
            config = VisualizationConfig.load_from_file(default_path)
            if config:
                self._config = config
                self._main_window.parameter_panel.set_config(config)
                logger.info("Default configuration loaded")
    
    def _show_data_load_dialog(self):
        """Show the data loading dialog."""
        dialog = DataLoadDialog(self._main_window)
        
        # Set defaults from current config
        dialog.set_defaults(
            original_fps=self._config.global_config.original_fps,
            um_per_pixel=self._config.global_config.um_per_pixel
        )
        
        if dialog.exec() != DataLoadDialog.DialogCode.Accepted:
            return
        
        settings = dialog.get_load_settings()
        self._load_and_analyze_data(settings)
    
    def _load_and_analyze_data(self, settings: dict):
        """
        Load and analyze data based on dialog settings.
        
        Args:
            settings: Dictionary from DataLoadDialog.get_load_settings().
        """
        # Load original images
        self._main_window.set_status("Loading original images...")
        QApplication.processEvents()
        
        success, message = self._data_manager.load_original_sequence(
            settings['original_dir']
        )
        if not success:
            self._main_window.show_error("Load Error", message)
            self._main_window.set_status("Ready")
            return
        
        # Load mask images
        self._main_window.set_status("Loading mask images...")
        QApplication.processEvents()
        
        success, message = self._data_manager.load_mask_sequence(
            settings['mask_dir']
        )
        if not success:
            self._main_window.show_error("Load Error", message)
            self._main_window.set_status("Ready")
            return
        
        # Validate sequences
        valid, message = self._data_manager.validate_sequences()
        if not valid:
            self._main_window.show_error("Validation Error", message)
            self._main_window.set_status("Ready")
            return
        
        # Update config with new parameters
        self._config.global_config.original_fps = settings['original_fps']
        self._config.global_config.um_per_pixel = settings['um_per_pixel']
        
        # Update parameter panel with original_fps for speed ratio calculation
        self._main_window.parameter_panel.set_original_fps(settings['original_fps'])
        
        # Handle trajectory data if provided
        if settings.get('has_trajectory', False):
            self._main_window.set_status("Loading trajectory data...")
            QApplication.processEvents()
            
            loader = TrajectoryDataLoader()
            loader.set_parameters(
                file_path=settings['trajectory_file'],
                file_type=settings['file_type'],
                time_column=settings['time_column'],
                x_column=settings['x_column'],
                y_column=settings['y_column'],
                data_start_row=settings['data_start_row'],
                time_unit=settings['time_unit'],
                space_unit=settings['space_unit'],
                original_fps=settings['original_fps'],
                um_per_pixel=settings['um_per_pixel'],
                id_column=settings.get('id_column', '')
            )
            
            # Load file
            success, message = loader.load_file()
            if not success:
                self._main_window.show_error("Trajectory Load Error", message)
                self._main_window.set_status("Ready")
                return
            
            # Convert trajectories
            success, message = loader.convert_trajectories()
            if not success:
                self._main_window.show_error("Trajectory Conversion Error", message)
                self._main_window.set_status("Ready")
                return
            
            # Validate trajectory data
            valid, message = loader.validate_data(
                self._data_manager.frame_count,
                self._data_manager.frame_width,
                self._data_manager.frame_height
            )
            if not valid:
                self._main_window.show_error("Trajectory Validation Error", message)
                self._main_window.set_status("Ready")
                return
            
            # Set trajectory loader in data manager
            self._data_manager.set_trajectory_loader(loader)
            
            # Calculate trajectories from external data
            self._main_window.set_status("Processing trajectory data...")
            QApplication.processEvents()
            
            success, message = self._trajectory_calculator.set_from_external_data(
                loader.get_trajectories(),
                self._data_manager,
                settings['original_fps'],
                settings['um_per_pixel']
            )
            if not success:
                self._main_window.show_error("Trajectory Processing Error", message)
                self._main_window.set_status("Ready")
                return
            
            # Use new object IDs from trajectory calculator
            object_ids = self._trajectory_calculator.get_new_object_ids()
        else:
            # Clear any previous external trajectory
            self._data_manager.clear_external_trajectory()
            
            # Calculate trajectories from mask data
            self._main_window.set_status("Calculating trajectories...")
            QApplication.processEvents()
            
            object_ids = self._data_manager.object_ids
            
            self._trajectory_calculator.calculate_all_trajectories(
                self._data_manager,
                settings['original_fps'],
                settings['um_per_pixel']
            )
        
        # Continue with visualization initialization
        self._initialize_visualization(object_ids)
    
    def _initialize_visualization(self, object_ids: list[int]):
        """
        Initialize visualization after data loading.
        
        Args:
            object_ids: List of object IDs to visualize.
        """
        self._color_mapper.assign_colors(object_ids)
        
        # Auto-set colorbar size based on image dimensions
        img_height = self._data_manager.frame_height
        bar_height = int(img_height * 2 / 3)
        bar_width = max(5, int(bar_height / 15))
        self._config.colorbar.bar_height = bar_height
        self._config.colorbar.bar_width = bar_width
        
        # Auto-set colorbar vmin/vmax to velocity range
        vmin, vmax = self._trajectory_calculator.get_velocity_range()
        if vmax > vmin:
            self._config.colorbar.vmin = round(vmin, 2)
            self._config.colorbar.vmax = round(vmax, 2)
            self._config.colorbar.tick_interval = round((vmax - vmin) / 5, 2)
        
        self._main_window.parameter_panel.set_config(self._config)
        
        self._preview_controller.set_config(self._config)
        self._preview_controller.initialize_renderer()
        self._preview_controller.update_preview()
        
        self._export_controller.set_config(self._config)
        self._export_controller.set_renderer(self._preview_controller.renderer)
        
        self._main_window.set_status(
            f"Ready - {self._data_manager.frame_count} frames, "
            f"{len(object_ids)} objects"
        )
        
        logger.info("Visualization initialized")
    
    def _check_and_initialize(self):
        """Check if data is ready and initialize visualization."""
        if not self._data_manager.is_loaded:
            return
        
        valid, message = self._data_manager.validate_sequences()
        
        if not valid:
            self._main_window.show_error("Validation Error", message)
            return
        
        self._main_window.set_status("Calculating trajectories...")
        QApplication.processEvents()
        
        self._color_mapper.assign_colors(self._data_manager.object_ids)
        
        self._config = self._main_window.parameter_panel.get_config()
        
        self._trajectory_calculator.calculate_all_trajectories(
            self._data_manager,
            self._config.global_config.original_fps,
            self._config.global_config.um_per_pixel
        )
        
        # Auto-set colorbar size based on image dimensions
        # Default: height = image_height * 2/3, width = height / 15
        img_height = self._data_manager.frame_height
        bar_height = int(img_height * 2 / 3)
        bar_width = max(5, int(bar_height / 15))
        self._config.colorbar.bar_height = bar_height
        self._config.colorbar.bar_width = bar_width
        
        # Auto-set colorbar vmin/vmax to velocity range
        vmin, vmax = self._trajectory_calculator.get_velocity_range()
        if vmax > vmin:
            self._config.colorbar.vmin = round(vmin, 2)
            self._config.colorbar.vmax = round(vmax, 2)
            self._config.colorbar.tick_interval = round((vmax - vmin) / 5, 2)
        
        self._main_window.parameter_panel.set_config(self._config)
        
        self._preview_controller.set_config(self._config)
        self._preview_controller.initialize_renderer()
        self._preview_controller.update_preview()
        
        self._export_controller.set_config(self._config)
        self._export_controller.set_renderer(self._preview_controller.renderer)
        
        self._main_window.set_status(
            f"Ready - {self._data_manager.frame_count} frames, "
            f"{len(self._data_manager.object_ids)} objects"
        )
        
        logger.info("Visualization initialized")
    
    def _on_config_changed(self):
        """Handle configuration change from parameter panel."""
        # Preserve original_fps and um_per_pixel (managed by DataLoadDialog)
        saved_original_fps = self._config.global_config.original_fps
        saved_um_per_pixel = self._config.global_config.um_per_pixel
        
        # Get new config from parameter panel (includes output_fps)
        self._config = self._main_window.parameter_panel.get_config()
        
        # Restore original_fps and um_per_pixel
        self._config.global_config.original_fps = saved_original_fps
        self._config.global_config.um_per_pixel = saved_um_per_pixel
        
        self._preview_controller.set_config(self._config)
        self._export_controller.set_config(self._config)
    
    def _on_object_clicked(self, frame: int, obj_id: int, current_frame: int):
        """Handle object double-click."""
        dialog = ObjectDialog(obj_id, current_frame, self._main_window)
        
        if dialog.exec() == ObjectDialog.DialogCode.Accepted:
            result = dialog.get_result()
            if result:
                obj_id, mode, frame = result
                
                if mode == "before":
                    self._object_manager.hide_object_before(obj_id, frame)
                else:
                    self._object_manager.hide_object_after(obj_id, frame)
                
                self._preview_controller.update_preview()
    
    def _restore_object(self, obj_id: int):
        """Restore a hidden object."""
        self._object_manager.restore_object(obj_id)
        self._preview_controller.update_preview()
    
    def _restore_all_objects(self):
        """Restore all hidden objects."""
        self._object_manager.restore_all()
        self._preview_controller.update_preview()
    
    def _on_hidden_records_changed(self):
        """Handle hidden records change."""
        records = self._object_manager.get_hidden_records()
        self._main_window.parameter_panel.update_hidden_objects(records)
    
    def _save_config(self):
        """Handle save configuration request."""
        file_path = select_save_file(
            self._main_window,
            "Save Configuration",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        if not file_path.endswith('.json'):
            file_path += '.json'
        
        # Preserve original_fps and um_per_pixel (managed by DataLoadDialog)
        saved_original_fps = self._config.global_config.original_fps
        saved_um_per_pixel = self._config.global_config.um_per_pixel
        self._config = self._main_window.parameter_panel.get_config()
        self._config.global_config.original_fps = saved_original_fps
        self._config.global_config.um_per_pixel = saved_um_per_pixel
        
        if self._config.save_to_file(file_path):
            self._main_window.show_info(
                "Configuration Saved",
                f"Configuration saved to:\n{file_path}"
            )
        else:
            self._main_window.show_error(
                "Save Error",
                "Failed to save configuration."
            )
    
    def _load_config(self):
        """Handle load configuration request."""
        file_path = select_open_file(
            self._main_window,
            "Load Configuration",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        config = VisualizationConfig.load_from_file(file_path)
        
        if config:
            # Preserve current original_fps and um_per_pixel (from data loading)
            # Only use output_fps from loaded config
            config.global_config.original_fps = self._config.global_config.original_fps
            config.global_config.um_per_pixel = self._config.global_config.um_per_pixel
            
            self._config = config
            self._main_window.parameter_panel.set_config(config)
            self._preview_controller.set_config(self._config)
            self._export_controller.set_config(self._config)
            
            self._main_window.show_info(
                "Configuration Loaded",
                f"Configuration loaded from:\n{file_path}"
            )
        else:
            self._main_window.show_error(
                "Load Error",
                "Failed to load configuration."
            )
    
    def _export(self):
        """Handle export request."""
        if not self._data_manager.is_loaded:
            self._main_window.show_warning(
                "No Data",
                "Please load image sequences before exporting."
            )
            return
        
        self._export_controller.start_export(self._main_window)
    
    def _on_export_finished(self, success: bool, message: str):
        """Handle export completion."""
        if success:
            self._main_window.show_info("Export Complete", message)
        else:
            if "cancelled" not in message.lower():
                self._main_window.show_error("Export Failed", message)
    
    def _on_preview_mode_changed(self, mode: str):
        """Handle preview mode change from main window."""
        self._preview_controller.set_preview_mode(mode)
    
    def show(self):
        """Show the main window."""
        self._main_window.show()
    
    @property
    def main_window(self) -> MainWindow:
        """Get the main window."""
        return self._main_window
