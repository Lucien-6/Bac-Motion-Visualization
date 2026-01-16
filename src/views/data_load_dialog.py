"""
Data loading dialog.

Dialog for selecting and loading image sequences and trajectory data.
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QDoubleSpinBox, QSpinBox, QFrame
)

from ..utils import get_image_files, get_logger, get_app_icon
from ..models import TrajectoryDataLoader

logger = get_logger(__name__)

# Standard label width for form alignment
LABEL_WIDTH = 100


class DataLoadDialog(QDialog):
    """
    Dialog for loading image sequences and trajectory data.
    
    Allows user to select original image sequence folder,
    mask image sequence folder, set parameters, and optionally
    load trajectory data from Excel/CSV files.
    """
    
    def __init__(self, parent=None):
        """Initialize data load dialog."""
        super().__init__(parent)
        
        # Image sequence paths
        self._original_dir: str = ""
        self._mask_dir: str = ""
        self._original_count: int = 0
        self._original_format: str = ""
        self._mask_count: int = 0
        self._mask_format: str = ""
        
        # Parameters
        self._original_fps: float = 1.0
        self._um_per_pixel: float = 1.0
        
        # Trajectory data
        self._trajectory_file: str = ""
        self._trajectory_columns: list[str] = []
        self._file_type: str = "csv"  # "excel" or "csv"
        self._id_column: str = ""
        self._time_column: str = ""
        self._x_column: str = ""
        self._y_column: str = ""
        self._data_start_row: int = 1
        self._time_unit: str = "frame"
        self._space_unit: str = "pixel"
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Load Data")
        self.setWindowIcon(get_app_icon())
        self.setMinimumWidth(600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Section 1: Required Data
        required_group = QGroupBox("Required Data")
        required_layout = QVBoxLayout(required_group)
        required_layout.setSpacing(12)
        
        # Original images
        orig_layout = QHBoxLayout()
        orig_label = QLabel("Original Images:")
        orig_label.setFixedWidth(LABEL_WIDTH)
        orig_layout.addWidget(orig_label)
        
        self._original_dir_edit = QLineEdit()
        self._original_dir_edit.setPlaceholderText("Select folder...")
        self._original_dir_edit.setReadOnly(True)
        orig_layout.addWidget(self._original_dir_edit, 1)
        
        self._original_browse_btn = QPushButton("Browse...")
        self._original_browse_btn.setFixedWidth(80)
        orig_layout.addWidget(self._original_browse_btn)
        
        required_layout.addLayout(orig_layout)
        
        # Original info label
        self._original_info_label = QLabel("")
        self._original_info_label.setStyleSheet("color: #666; font-style: italic; margin-left: 105px;")
        required_layout.addWidget(self._original_info_label)
        
        # Mask images
        mask_layout = QHBoxLayout()
        mask_label = QLabel("Mask Images:")
        mask_label.setFixedWidth(LABEL_WIDTH)
        mask_layout.addWidget(mask_label)
        
        self._mask_dir_edit = QLineEdit()
        self._mask_dir_edit.setPlaceholderText("Select folder...")
        self._mask_dir_edit.setReadOnly(True)
        mask_layout.addWidget(self._mask_dir_edit, 1)
        
        self._mask_browse_btn = QPushButton("Browse...")
        self._mask_browse_btn.setFixedWidth(80)
        mask_layout.addWidget(self._mask_browse_btn)
        
        required_layout.addLayout(mask_layout)
        
        # Mask info label
        self._mask_info_label = QLabel("")
        self._mask_info_label.setStyleSheet("color: #666; font-style: italic; margin-left: 105px;")
        required_layout.addWidget(self._mask_info_label)
        
        layout.addWidget(required_group)
        
        # Section 2: Parameters
        param_group = QGroupBox("Parameters")
        param_layout = QFormLayout(param_group)
        param_layout.setSpacing(12)
        
        self._fps_spin = QDoubleSpinBox()
        self._fps_spin.setRange(0.001, 10000)
        self._fps_spin.setValue(1.0)
        self._fps_spin.setDecimals(3)
        self._fps_spin.setSuffix(" fps")
        param_layout.addRow("Original FPS:", self._fps_spin)
        
        self._um_spin = QDoubleSpinBox()
        self._um_spin.setRange(0.001, 10000)
        self._um_spin.setValue(1.0)
        self._um_spin.setDecimals(3)
        self._um_spin.setSuffix(" μm/pixel")
        param_layout.addRow("μm/pixel:", self._um_spin)
        
        layout.addWidget(param_group)
        
        # Section 3: Optional Trajectory Data
        traj_group = QGroupBox("Trajectory Data (Optional)")
        traj_layout = QVBoxLayout(traj_group)
        traj_layout.setSpacing(12)
        
        # Trajectory file selection
        file_layout = QHBoxLayout()
        file_label = QLabel("Trajectory File:")
        file_label.setFixedWidth(LABEL_WIDTH)
        file_layout.addWidget(file_label)
        
        self._traj_file_edit = QLineEdit()
        self._traj_file_edit.setPlaceholderText("Select Excel or CSV file...")
        self._traj_file_edit.setReadOnly(True)
        file_layout.addWidget(self._traj_file_edit, 1)
        
        self._traj_browse_btn = QPushButton("Browse...")
        self._traj_browse_btn.setFixedWidth(80)
        file_layout.addWidget(self._traj_browse_btn)
        
        self._traj_clear_btn = QPushButton("Clear")
        self._traj_clear_btn.setFixedWidth(60)
        file_layout.addWidget(self._traj_clear_btn)
        
        traj_layout.addLayout(file_layout)
        
        # Column mapping (initially disabled)
        self._column_frame = QFrame()
        column_layout = QFormLayout(self._column_frame)
        column_layout.setSpacing(8)
        
        # ID Column row (only for CSV, hidden for Excel)
        self._id_combo = QComboBox()
        self._id_combo.setMinimumWidth(150)
        self._id_label = QLabel("ID Column:")
        column_layout.addRow(self._id_label, self._id_combo)
        
        self._time_combo = QComboBox()
        self._time_combo.setMinimumWidth(150)
        column_layout.addRow("Time Column:", self._time_combo)
        
        self._x_combo = QComboBox()
        self._x_combo.setMinimumWidth(150)
        column_layout.addRow("X Column:", self._x_combo)
        
        self._y_combo = QComboBox()
        self._y_combo.setMinimumWidth(150)
        column_layout.addRow("Y Column:", self._y_combo)
        
        # File type info label
        self._file_type_label = QLabel("")
        self._file_type_label.setStyleSheet("color: #666; font-style: italic;")
        column_layout.addRow("", self._file_type_label)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        column_layout.addRow(sep)
        
        self._start_row_spin = QSpinBox()
        self._start_row_spin.setRange(1, 10000)
        self._start_row_spin.setValue(1)
        self._start_row_spin.setToolTip("Row number where data starts (1 = immediately after header)")
        column_layout.addRow("Data Start Row:", self._start_row_spin)
        
        self._time_unit_combo = QComboBox()
        self._time_unit_combo.addItems(["frame", "ms", "s", "min", "h"])
        column_layout.addRow("Time Unit:", self._time_unit_combo)
        
        self._space_unit_combo = QComboBox()
        self._space_unit_combo.addItems(["pixel", "μm"])
        column_layout.addRow("Space Unit:", self._space_unit_combo)
        
        self._column_frame.setEnabled(False)
        traj_layout.addWidget(self._column_frame)
        
        layout.addWidget(traj_group)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        self._load_btn = QPushButton("Load && Analyze")
        self._load_btn.setObjectName("primaryButton")
        self._load_btn.setMinimumWidth(120)
        self._load_btn.clicked.connect(self._on_load_analyze)
        button_layout.addWidget(self._load_btn)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect widget signals."""
        self._original_browse_btn.clicked.connect(self._browse_original_dir)
        self._mask_browse_btn.clicked.connect(self._browse_mask_dir)
        self._traj_browse_btn.clicked.connect(self._browse_trajectory_file)
        self._traj_clear_btn.clicked.connect(self._clear_trajectory_file)
    
    def _browse_original_dir(self):
        """Browse for original image sequence folder."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Original Image Sequence Folder",
            self._original_dir or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self._original_dir = directory
            self._original_dir_edit.setText(directory)
            self._update_original_info()
    
    def _browse_mask_dir(self):
        """Browse for mask image sequence folder."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Mask Image Sequence Folder",
            self._mask_dir or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self._mask_dir = directory
            self._mask_dir_edit.setText(directory)
            self._update_mask_info()
    
    def _browse_trajectory_file(self):
        """Browse for trajectory data file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Trajectory Data File",
            "",
            "Trajectory Files (*.xlsx *.xls *.csv);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if file_path:
            self._trajectory_file = file_path
            self._traj_file_edit.setText(file_path)
            self._load_trajectory_columns()
    
    def _clear_trajectory_file(self):
        """Clear trajectory file selection."""
        self._trajectory_file = ""
        self._file_type = "csv"
        self._traj_file_edit.setText("")
        self._trajectory_columns = []
        self._id_combo.clear()
        self._time_combo.clear()
        self._x_combo.clear()
        self._y_combo.clear()
        self._file_type_label.setText("")
        self._column_frame.setEnabled(False)
        # Reset ID column visibility
        self._id_label.setVisible(True)
        self._id_combo.setVisible(True)
    
    def _update_original_info(self):
        """Update original image sequence info display."""
        if not self._original_dir:
            self._original_info_label.setText("")
            return
        
        files = get_image_files(self._original_dir)
        self._original_count = len(files)
        
        if files:
            formats = set(f.suffix.lower() for f in files)
            self._original_format = ", ".join(sorted(formats))
            self._original_info_label.setText(
                f"{self._original_count} images ({self._original_format})"
            )
        else:
            self._original_format = ""
            self._original_info_label.setText("No images found")
    
    def _update_mask_info(self):
        """Update mask image sequence info display."""
        if not self._mask_dir:
            self._mask_info_label.setText("")
            return
        
        files = get_image_files(self._mask_dir)
        self._mask_count = len(files)
        
        if files:
            formats = set(f.suffix.lower() for f in files)
            self._mask_format = ", ".join(sorted(formats))
            self._mask_info_label.setText(
                f"{self._mask_count} images ({self._mask_format})"
            )
        else:
            self._mask_format = ""
            self._mask_info_label.setText("No images found")
    
    def _load_trajectory_columns(self):
        """Load column headers from trajectory file."""
        if not self._trajectory_file:
            return
        
        columns, file_type, error = TrajectoryDataLoader.get_columns(
            self._trajectory_file
        )
        
        if error:
            QMessageBox.warning(
                self,
                "Error Reading File",
                f"Failed to read trajectory file:\n{error}"
            )
            self._clear_trajectory_file()
            return
        
        if not columns:
            QMessageBox.warning(
                self,
                "No Columns Found",
                "The trajectory file appears to have no column headers."
            )
            self._clear_trajectory_file()
            return
        
        self._trajectory_columns = columns
        self._file_type = file_type
        
        # Populate combo boxes
        self._id_combo.clear()
        self._time_combo.clear()
        self._x_combo.clear()
        self._y_combo.clear()
        
        self._id_combo.addItems(columns)
        self._time_combo.addItems(columns)
        self._x_combo.addItems(columns)
        self._y_combo.addItems(columns)
        
        # Try to auto-select columns based on common names
        self._auto_select_columns(columns)
        
        # Show/hide ID column based on file type
        if file_type == "excel":
            self._id_label.setVisible(False)
            self._id_combo.setVisible(False)
            self._file_type_label.setText(
                "Excel file: each sheet = one object (ID assigned by sheet order)"
            )
        else:
            self._id_label.setVisible(True)
            self._id_combo.setVisible(True)
            self._file_type_label.setText(
                "CSV file: objects grouped by ID column"
            )
        
        self._column_frame.setEnabled(True)
        
        logger.info(
            f"Loaded {len(columns)} columns from {file_type} trajectory file"
        )
    
    def _auto_select_columns(self, columns: list[str]):
        """Try to auto-select columns based on common naming patterns."""
        columns_lower = [c.lower() for c in columns]
        
        # ID column patterns
        for i, col in enumerate(columns_lower):
            if col in ('id', 'object_id', 'objectid', 'obj_id', 'track_id', 'trackid'):
                self._id_combo.setCurrentIndex(i)
                break
        
        # Time column patterns
        for i, col in enumerate(columns_lower):
            if col in ('t', 'time', 'frame', 'timepoint', 'time_point'):
                self._time_combo.setCurrentIndex(i)
                break
        
        # X column patterns
        for i, col in enumerate(columns_lower):
            if col in ('x', 'x_pos', 'x_position', 'xpos', 'position_x', 'centroid_x'):
                self._x_combo.setCurrentIndex(i)
                break
        
        # Y column patterns
        for i, col in enumerate(columns_lower):
            if col in ('y', 'y_pos', 'y_position', 'ypos', 'position_y', 'centroid_y'):
                self._y_combo.setCurrentIndex(i)
                break
    
    def _validate_inputs(self) -> tuple[bool, str]:
        """
        Validate required inputs.
        
        Returns:
            Tuple of (valid, error_message).
        """
        if not self._original_dir:
            return False, "Please select an original image sequence folder."
        
        if self._original_count == 0:
            return False, "No images found in the original image folder."
        
        if not self._mask_dir:
            return False, "Please select a mask image sequence folder."
        
        if self._mask_count == 0:
            return False, "No images found in the mask image folder."
        
        # Validate trajectory data if selected
        if self._trajectory_file:
            if not self._trajectory_columns:
                return False, "Failed to read trajectory file columns."
            
            time_col = self._time_combo.currentText()
            x_col = self._x_combo.currentText()
            y_col = self._y_combo.currentText()
            
            if self._file_type == "excel":
                # Excel: only check T, X, Y are different
                selected = [time_col, x_col, y_col]
                if len(set(selected)) != 3:
                    return False, "Please select different columns for Time, X, and Y."
            else:
                # CSV: check ID, T, X, Y are different
                id_col = self._id_combo.currentText()
                selected = [id_col, time_col, x_col, y_col]
                if len(set(selected)) != 4:
                    return False, "Please select different columns for ID, Time, X, and Y."
        
        return True, ""
    
    def _on_load_analyze(self):
        """Handle load and analyze button click."""
        valid, error = self._validate_inputs()
        
        if not valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        # Store values
        self._original_fps = self._fps_spin.value()
        self._um_per_pixel = self._um_spin.value()
        
        if self._trajectory_file:
            self._time_column = self._time_combo.currentText()
            self._x_column = self._x_combo.currentText()
            self._y_column = self._y_combo.currentText()
            self._data_start_row = self._start_row_spin.value()
            self._time_unit = self._time_unit_combo.currentText()
            self._space_unit = self._space_unit_combo.currentText()
            # ID column only relevant for CSV
            if self._file_type == "csv":
                self._id_column = self._id_combo.currentText()
            else:
                self._id_column = ""
        
        self.accept()
    
    def get_load_settings(self) -> dict:
        """
        Get all loading settings.
        
        Returns:
            Dictionary containing all settings.
        """
        settings = {
            'original_dir': self._original_dir,
            'mask_dir': self._mask_dir,
            'original_fps': self._original_fps,
            'um_per_pixel': self._um_per_pixel,
            'has_trajectory': bool(self._trajectory_file),
        }
        
        if self._trajectory_file:
            settings.update({
                'trajectory_file': self._trajectory_file,
                'file_type': self._file_type,
                'id_column': self._id_column,
                'time_column': self._time_column,
                'x_column': self._x_column,
                'y_column': self._y_column,
                'data_start_row': self._data_start_row,
                'time_unit': self._time_unit,
                'space_unit': self._space_unit,
            })
        
        return settings
    
    def set_defaults(self, original_fps: float = 1.0, um_per_pixel: float = 1.0):
        """
        Set default parameter values.
        
        Args:
            original_fps: Default original FPS value.
            um_per_pixel: Default μm/pixel value.
        """
        self._fps_spin.setValue(original_fps)
        self._um_spin.setValue(um_per_pixel)
