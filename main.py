"""
Bac-Motion Visualization Application Entry Point.

A professional bacterial motion visualization application that overlays
segmentation and tracking masks onto original image sequences.

Author: Lucien (lucien-6@qq.com)
License: MIT License
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path.parent))

from src.controllers import MainController
from src.utils import setup_root_logger, get_logger, get_app_icon


def main():
    """Main entry point for the application."""
    log_dir = Path(__file__).parent / "logs"
    setup_root_logger(str(log_dir))
    
    logger = get_logger(__name__)
    logger.info("Starting Bac-Motion Visualization application")
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Bac-Motion Visualization")
    app.setOrganizationName("Lucien")
    app.setApplicationVersion("1.1.0")
    app.setWindowIcon(get_app_icon())
    
    controller = MainController()
    controller.show()
    
    logger.info("Application window displayed")
    
    exit_code = app.exec()
    
    logger.info(f"Application exiting with code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
