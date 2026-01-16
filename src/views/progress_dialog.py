"""
Progress dialog for export operations.

Shows export progress with estimated remaining time and cancel option.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton
)

from ..utils import get_app_icon


class ProgressDialog(QDialog):
    """
    Progress dialog for long-running operations.
    
    Shows progress bar, current status, and cancel button.
    """
    
    def __init__(self, title: str = "Processing...", parent=None):
        """
        Initialize progress dialog.
        
        Args:
            title: Dialog title.
            parent: Parent widget.
        """
        super().__init__(parent)
        
        self._cancelled = False
        
        self._setup_ui(title)
    
    def _setup_ui(self, title: str):
        """Set up the dialog UI."""
        self.setWindowTitle(title)
        self.setWindowIcon(get_app_icon())
        self.setMinimumWidth(450)
        self.setModal(True)
        
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1d1d1f;
        """)
        layout.addWidget(self._title_label)
        
        progress_layout = QHBoxLayout()
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e5e5ea;
                border-radius: 6px;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #0071e3;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self._progress_bar)
        
        self._percent_label = QLabel("0%")
        self._percent_label.setMinimumWidth(50)
        self._percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._percent_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        progress_layout.addWidget(self._percent_label)
        
        layout.addLayout(progress_layout)
        
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)
        
        self._status_label = QLabel("Preparing...")
        self._status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self._status_label)
        
        self._time_label = QLabel("Estimated time remaining: Calculating...")
        self._time_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self._time_label)
        
        layout.addLayout(status_layout)
        
        layout.addSpacing(8)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self._cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self._cancelled = True
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("Cancelling...")
        self._status_label.setText("Cancelling operation...")
    
    def update_progress(self, percent: int, remaining_time: str = ""):
        """
        Update progress display.
        
        Args:
            percent: Progress percentage (0-100).
            remaining_time: Formatted remaining time string.
        """
        self._progress_bar.setValue(percent)
        self._percent_label.setText(f"{percent}%")
        
        if remaining_time:
            self._time_label.setText(f"Estimated time remaining: {remaining_time}")
    
    def update_status(self, status: str):
        """
        Update status message.
        
        Args:
            status: Status message to display.
        """
        self._status_label.setText(status)
    
    def set_frame_progress(self, current: int, total: int):
        """
        Update frame progress display.
        
        Args:
            current: Current frame number.
            total: Total frame count.
        """
        self._status_label.setText(f"Processing frame {current} / {total}")
    
    def is_cancelled(self) -> bool:
        """Check if cancel was requested."""
        return self._cancelled
    
    def finish(self, success: bool, message: str = ""):
        """
        Complete the progress dialog.
        
        Args:
            success: Whether operation completed successfully.
            message: Completion message.
        """
        if success:
            self._progress_bar.setValue(100)
            self._percent_label.setText("100%")
            self._status_label.setText("Complete!")
            self._time_label.setText(message or "Export finished successfully.")
        else:
            self._status_label.setText("Failed")
            self._time_label.setText(message or "Operation failed.")
        
        self._cancel_btn.setText("Close")
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.clicked.disconnect()
        self._cancel_btn.clicked.connect(self.accept)
