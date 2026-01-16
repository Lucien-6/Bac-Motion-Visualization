"""
Main application window.

The main window containing parameter panel, preview widget,
menu bar, and status bar.
"""

import os
import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QKeySequence, QDesktopServices
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QMessageBox, QPushButton, QFrame
)

from .parameter_panel import ParameterPanel
from .preview_widget import PreviewWidget
from .styles import get_application_style
from ..utils import get_app_icon


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Signals:
        load_data_requested: Request to open data loading dialog.
        save_config_requested: Request to save configuration.
        load_config_requested: Request to load configuration.
        export_requested: Request to export visualization.
        preview_mode_changed(str): Preview mode changed ('edit' or 'final').
    """
    
    load_data_requested = pyqtSignal()
    save_config_requested = pyqtSignal()
    load_config_requested = pyqtSignal()
    export_requested = pyqtSignal()
    preview_mode_changed = pyqtSignal(str)
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        
        self.setStyleSheet(get_application_style())
    
    def _setup_window(self):
        """Configure window properties."""
        self.setWindowTitle("Bac-Motion Visualization")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(1000, 800)
        
        self.resize(1500, 1200)
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self._parameter_panel = ParameterPanel()
        self._splitter.addWidget(self._parameter_panel)
        
        # Create preview container with toolbar
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        # Preview toolbar
        self._preview_toolbar = QFrame()
        self._preview_toolbar.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-bottom: 1px solid #d0d0d0;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
                border-color: #0078d4;
            }
        """)
        toolbar_layout = QHBoxLayout(self._preview_toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)
        toolbar_layout.setSpacing(8)
        
        # Preview mode buttons (two separate buttons)
        self._edit_mode_btn = QPushButton("Edit Mode")
        self._edit_mode_btn.setCheckable(True)
        self._edit_mode_btn.setChecked(True)
        self._edit_mode_btn.setToolTip("Edit Mode: Drag labels to adjust positions")
        self._edit_mode_btn.clicked.connect(self._on_edit_mode_clicked)
        toolbar_layout.addWidget(self._edit_mode_btn)
        
        self._final_mode_btn = QPushButton("Final Preview")
        self._final_mode_btn.setCheckable(True)
        self._final_mode_btn.setChecked(False)
        self._final_mode_btn.setToolTip("Final Preview: Show exact export result")
        self._final_mode_btn.clicked.connect(self._on_final_mode_clicked)
        toolbar_layout.addWidget(self._final_mode_btn)
        
        toolbar_layout.addStretch()
        
        preview_layout.addWidget(self._preview_toolbar)
        
        self._preview_widget = PreviewWidget()
        preview_layout.addWidget(self._preview_widget, 1)
        
        self._splitter.addWidget(preview_container)
        
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        
        self._splitter.setSizes([380, 1020])
        
        layout.addWidget(self._splitter)
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        load_data_action = QAction("Load Data...", self)
        load_data_action.setShortcut(QKeySequence("Ctrl+L"))
        load_data_action.triggered.connect(self.load_data_requested.emit)
        file_menu.addAction(load_data_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_requested.emit)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        config_menu = menubar.addMenu("Config")
        
        save_config_action = QAction("Save Config...", self)
        save_config_action.setShortcut(QKeySequence("Ctrl+S"))
        save_config_action.triggered.connect(self.save_config_requested.emit)
        config_menu.addAction(save_config_action)
        
        load_config_action = QAction("Load Config...", self)
        load_config_action.setShortcut(QKeySequence("Ctrl+I"))
        load_config_action.triggered.connect(self.load_config_requested.emit)
        config_menu.addAction(load_config_action)
        
        help_menu = menubar.addMenu("Help")
        
        user_guide_action = QAction("User Guide", self)
        user_guide_action.setShortcut(QKeySequence("F1"))
        user_guide_action.triggered.connect(self._show_user_guide)
        help_menu.addAction(user_guide_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        
        self._status_bar.showMessage("Ready")
    
    def _show_user_guide(self):
        """Open the user guide in the default browser."""
        # Get the help guide path relative to this file
        help_path = Path(__file__).parent.parent.parent / "resources" / "help_guide.html"
        
        if help_path.exists():
            # Open in default browser
            url = QUrl.fromLocalFile(str(help_path.resolve()))
            QDesktopServices.openUrl(url)
        else:
            QMessageBox.warning(
                self,
                "Help Not Found",
                f"User guide file not found:\n{help_path}"
            )
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Bac-Motion Visualization",
            "<h3>Bac-Motion Visualization</h3>"
            "<p>Version 1.0.0</p>"
            "<p>A professional bacterial motion visualization application.</p>"
            "<p>Overlays segmentation and tracking masks onto original "
            "image sequences for intuitive visualization.</p>"
            "<hr>"
            "<p>Author: Lucien (lucien-6@qq.com)</p>"
            "<p>License: MIT License</p>"
        )
    
    @property
    def parameter_panel(self) -> ParameterPanel:
        """Get the parameter panel."""
        return self._parameter_panel
    
    @property
    def preview_widget(self) -> PreviewWidget:
        """Get the preview widget."""
        return self._preview_widget
    
    def set_status(self, message: str, timeout: int = 0):
        """
        Set status bar message.
        
        Args:
            message: Status message.
            timeout: Message timeout in milliseconds (0 = permanent).
        """
        self._status_bar.showMessage(message, timeout)
    
    def show_error(self, title: str, message: str):
        """Show error message box."""
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Show warning message box."""
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Show information message box."""
        QMessageBox.information(self, title, message)
    
    def _on_edit_mode_clicked(self):
        """Handle Edit Mode button click."""
        self._edit_mode_btn.setChecked(True)
        self._final_mode_btn.setChecked(False)
        self.preview_mode_changed.emit('edit')
    
    def _on_final_mode_clicked(self):
        """Handle Final Preview button click."""
        self._edit_mode_btn.setChecked(False)
        self._final_mode_btn.setChecked(True)
        self.preview_mode_changed.emit('final')