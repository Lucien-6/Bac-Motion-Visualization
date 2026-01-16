"""
File operation utilities.

Provides functions for file dialogs, path handling, and file operations.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QWidget, QMessageBox
from PyQt6.QtGui import QIcon

from .natural_sort import natural_sort_paths


SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}


def get_app_icon() -> QIcon:
    """
    Load and return the application icon.
    
    Returns:
        QIcon: Application icon loaded from SVG file.
    """
    icon_path = Path(__file__).parent.parent.parent / "resources" / "icons" / "app_icon.svg"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def select_directory(
    parent: QWidget | None = None,
    title: str = "Select Directory",
    start_dir: str = ""
) -> str | None:
    """
    Open a directory selection dialog.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog window title.
        start_dir: Starting directory path.

    Returns:
        Selected directory path or None if cancelled.
    """
    directory = QFileDialog.getExistingDirectory(
        parent,
        title,
        start_dir,
        QFileDialog.Option.ShowDirsOnly
    )
    
    return directory if directory else None


def select_save_file(
    parent: QWidget | None = None,
    title: str = "Save File",
    start_dir: str = "",
    filters: str = "All Files (*)"
) -> str | None:
    """
    Open a file save dialog.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog window title.
        start_dir: Starting directory or file path.
        filters: File type filters (e.g., "Videos (*.mp4 *.avi)").

    Returns:
        Selected file path or None if cancelled.
    """
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        title,
        start_dir,
        filters
    )
    
    return file_path if file_path else None


def select_open_file(
    parent: QWidget | None = None,
    title: str = "Open File",
    start_dir: str = "",
    filters: str = "All Files (*)"
) -> str | None:
    """
    Open a file open dialog.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog window title.
        start_dir: Starting directory path.
        filters: File type filters.

    Returns:
        Selected file path or None if cancelled.
    """
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        title,
        start_dir,
        filters
    )
    
    return file_path if file_path else None


def get_image_files(directory: str) -> list[Path]:
    """
    Get all image files in a directory, naturally sorted.

    Args:
        directory: Directory path to scan.

    Returns:
        List of image file paths, naturally sorted.
    """
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    image_files = [
        f for f in dir_path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]
    
    return natural_sort_paths(image_files)


def ensure_directory(path: str | Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        Path object for the directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def file_exists(path: str | Path) -> bool:
    """
    Check if a file exists.

    Args:
        path: File path to check.

    Returns:
        True if file exists, False otherwise.
    """
    return Path(path).exists()


def confirm_overwrite(
    parent: QWidget | None,
    file_path: str
) -> bool:
    """
    Show a confirmation dialog for file overwrite.

    Args:
        parent: Parent widget for the dialog.
        file_path: Path of the file to be overwritten.

    Returns:
        True if user confirms overwrite, False otherwise.
    """
    result = QMessageBox.question(
        parent,
        "Confirm Overwrite",
        f"File already exists:\n{file_path}\n\nDo you want to overwrite it?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    
    return result == QMessageBox.StandardButton.Yes


def get_file_size_mb(path: str | Path) -> float:
    """
    Get file size in megabytes.

    Args:
        path: File path.

    Returns:
        File size in MB.
    """
    return Path(path).stat().st_size / (1024 * 1024)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size to human readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
