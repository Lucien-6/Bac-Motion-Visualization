"""
Object operation dialog.

Dialog for hiding/truncating object visualization at specific frames.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QButtonGroup, QPushButton,
    QFrame
)

from ..utils import get_app_icon


class ObjectDialog(QDialog):
    """
    Dialog for managing object visibility.
    
    Allows user to choose to hide an object before or after
    the current frame.
    """
    
    def __init__(
        self,
        obj_id: int,
        current_frame: int,
        parent=None
    ):
        """
        Initialize object dialog.
        
        Args:
            obj_id: Object ID being operated on.
            current_frame: Current frame index.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._obj_id = obj_id
        self._current_frame = current_frame
        self._selected_mode: str | None = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Object Operation")
        self.setWindowIcon(get_app_icon())
        self.setMinimumWidth(320)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        
        obj_label = QLabel(f"Object ID: <b>{self._obj_id}</b>")
        obj_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(obj_label)
        
        frame_label = QLabel(f"Current Frame: <b>{self._current_frame}</b>")
        frame_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(frame_label)
        
        layout.addWidget(info_frame)
        
        option_label = QLabel("Select operation:")
        option_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(option_label)
        
        self._button_group = QButtonGroup(self)
        
        self._before_radio = QRadioButton(
            f"Hide at frame ≤ {self._current_frame} (before and including current)"
        )
        self._before_radio.setStyleSheet("font-size: 13px;")
        self._button_group.addButton(self._before_radio, 1)
        layout.addWidget(self._before_radio)
        
        self._after_radio = QRadioButton(
            f"Hide at frame ≥ {self._current_frame} (current and after)"
        )
        self._after_radio.setStyleSheet("font-size: 13px;")
        self._button_group.addButton(self._after_radio, 2)
        layout.addWidget(self._after_radio)
        
        self._before_radio.setChecked(True)
        
        layout.addSpacing(16)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setObjectName("primaryButton")
        confirm_btn.setMinimumWidth(100)
        confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
    
    def _on_confirm(self):
        """Handle confirm button click."""
        if self._before_radio.isChecked():
            self._selected_mode = "before"
        elif self._after_radio.isChecked():
            self._selected_mode = "after"
        
        self.accept()
    
    def get_result(self) -> tuple[int, str, int] | None:
        """
        Get the dialog result.
        
        Returns:
            Tuple of (obj_id, mode, frame) or None if cancelled.
        """
        if self._selected_mode:
            return (self._obj_id, self._selected_mode, self._current_frame)
        return None
