"""
Export settings dialog.

Dialog for configuring video and image sequence export options.
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QFileDialog, QMessageBox,
    QDoubleSpinBox
)

from ..utils import get_app_icon


class ExportDialog(QDialog):
    """
    Dialog for configuring export settings.
    
    Allows user to set output directory, video settings,
    and image sequence settings.
    """
    
    def __init__(self, parent=None):
        """Initialize export dialog."""
        super().__init__(parent)
        
        self._output_dir = ""
        self._export_video = True
        self._video_filename = "output"
        self._video_format = "mp4"
        self._export_images = True
        self._subfolder_name = "frames"
        self._image_prefix = "frame_"
        self._output_fps: float = 30.0
        self._original_fps: float = 1.0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Export Settings")
        self.setWindowIcon(get_app_icon())
        self.setMinimumWidth(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        dir_layout = QHBoxLayout()
        
        dir_label = QLabel("Output Directory:")
        dir_label.setStyleSheet("font-weight: 600;")
        dir_layout.addWidget(dir_label)
        
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Select output directory...")
        self._dir_edit.setReadOnly(True)
        dir_layout.addWidget(self._dir_edit, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_btn)
        
        layout.addLayout(dir_layout)
        
        video_group = QGroupBox("Video Output")
        video_layout = QVBoxLayout(video_group)
        
        self._video_check = QCheckBox("Export Video")
        self._video_check.setChecked(True)
        self._video_check.toggled.connect(self._on_video_toggled)
        video_layout.addWidget(self._video_check)
        
        video_form = QFormLayout()
        video_form.setSpacing(12)
        
        self._video_name_edit = QLineEdit("output")
        video_form.addRow("Filename:", self._video_name_edit)
        
        self._format_combo = QComboBox()
        self._format_combo.addItems(["mp4", "avi", "gif"])
        video_form.addRow("Format:", self._format_combo)
        
        # Output FPS is set in parameter panel, display here for reference
        self._output_fps_label = QLabel("30.0 fps")
        self._output_fps_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        video_form.addRow("Output FPS:", self._output_fps_label)
        
        self._speed_ratio_label = QLabel("30.0×")
        self._speed_ratio_label.setStyleSheet("color: #666; font-style: italic;")
        video_form.addRow("Speed Ratio:", self._speed_ratio_label)
        
        video_layout.addLayout(video_form)
        layout.addWidget(video_group)
        
        image_group = QGroupBox("Image Sequence Output")
        image_layout = QVBoxLayout(image_group)
        
        self._image_check = QCheckBox("Export Image Sequence")
        self._image_check.setChecked(True)
        self._image_check.toggled.connect(self._on_image_toggled)
        image_layout.addWidget(self._image_check)
        
        image_form = QFormLayout()
        image_form.setSpacing(12)
        
        self._subfolder_edit = QLineEdit("frames")
        image_form.addRow("Subfolder:", self._subfolder_edit)
        
        self._prefix_edit = QLineEdit("frame_")
        image_form.addRow("Filename Prefix:", self._prefix_edit)
        
        preview_label = QLabel()
        preview_label.setStyleSheet("color: #666; font-style: italic;")
        self._preview_label = preview_label
        self._update_preview()
        image_form.addRow("Preview:", preview_label)
        
        self._prefix_edit.textChanged.connect(self._update_preview)
        
        image_layout.addLayout(image_form)
        layout.addWidget(image_group)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        export_btn = QPushButton("Export")
        export_btn.setObjectName("primaryButton")
        export_btn.setMinimumWidth(100)
        export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_directory(self):
        """Open directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self._output_dir or "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self._output_dir = directory
            self._dir_edit.setText(directory)
    
    def _on_video_toggled(self, checked: bool):
        """Handle video export checkbox toggle."""
        self._video_name_edit.setEnabled(checked)
        self._format_combo.setEnabled(checked)
    
    def _update_speed_ratio(self):
        """Update speed ratio display based on output and original FPS."""
        if self._original_fps <= 0:
            self._speed_ratio_label.setText("N/A")
            return
        
        ratio = self._output_fps / self._original_fps
        if ratio >= 1:
            if ratio == int(ratio):
                text = f"{int(ratio)}×"
            else:
                text = f"{ratio:.1f}×"
        else:
            text = f"{ratio:.2f}×"
        
        self._speed_ratio_label.setText(text)
    
    def _on_image_toggled(self, checked: bool):
        """Handle image export checkbox toggle."""
        self._subfolder_edit.setEnabled(checked)
        self._prefix_edit.setEnabled(checked)
    
    def _update_preview(self):
        """Update filename preview."""
        prefix = self._prefix_edit.text() or "frame_"
        self._preview_label.setText(f"{prefix}000001.png, {prefix}000002.png, ...")
    
    def _on_export(self):
        """Handle export button click."""
        if not self._output_dir:
            QMessageBox.warning(
                self,
                "No Output Directory",
                "Please select an output directory."
            )
            return
        
        if not self._video_check.isChecked() and not self._image_check.isChecked():
            QMessageBox.warning(
                self,
                "No Export Selected",
                "Please select at least one export option."
            )
            return
        
        self._export_video = self._video_check.isChecked()
        self._video_filename = self._video_name_edit.text() or "output"
        self._video_format = self._format_combo.currentText()
        # output_fps is already set via set_defaults from config
        
        self._export_images = self._image_check.isChecked()
        self._subfolder_name = self._subfolder_edit.text() or "frames"
        self._image_prefix = self._prefix_edit.text() or "frame_"
        
        self.accept()
    
    def get_export_settings(self) -> dict:
        """
        Get export settings.
        
        Returns:
            Dictionary with export settings.
        """
        video_path = ""
        if self._export_video:
            video_path = str(
                Path(self._output_dir) / f"{self._video_filename}.{self._video_format}"
            )
        
        image_dir = ""
        if self._export_images:
            image_dir = str(Path(self._output_dir) / self._subfolder_name)
        
        return {
            'output_dir': self._output_dir,
            'export_video': self._export_video,
            'video_path': video_path,
            'video_format': self._video_format,
            'output_fps': self._output_fps,
            'export_images': self._export_images,
            'image_dir': image_dir,
            'image_prefix': self._image_prefix,
        }
    
    def set_defaults(
        self,
        output_dir: str = "",
        video_format: str = "mp4",
        image_prefix: str = "frame_",
        subfolder_name: str = "frames",
        original_fps: float = 1.0,
        output_fps: float = 30.0
    ):
        """Set default values."""
        if output_dir:
            self._output_dir = output_dir
            self._dir_edit.setText(output_dir)
        
        index = self._format_combo.findText(video_format)
        if index >= 0:
            self._format_combo.setCurrentIndex(index)
        
        self._prefix_edit.setText(image_prefix)
        self._subfolder_edit.setText(subfolder_name)
        self._update_preview()
        
        self._original_fps = original_fps
        self._output_fps = output_fps
        self._output_fps_label.setText(f"{output_fps:.1f} fps")
        self._update_speed_ratio()