"""
Image processing utilities.

Provides functions for image format conversion, bit depth handling,
and Qt image conversion.
"""

import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap


def load_image(path: str) -> np.ndarray | None:
    """
    Load an image file with automatic format detection.

    Supports 8/12/16-bit grayscale and 24-bit RGB images.
    Output is always BGR format for OpenCV compatibility.

    Args:
        path: Path to the image file.

    Returns:
        Image as numpy array (BGR format) or None if loading fails.
    """
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    
    if image is None:
        return None
    
    if len(image.shape) == 2:
        if image.dtype == np.uint16:
            image = normalize_to_8bit(image)
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif len(image.shape) == 3:
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        if image.dtype == np.uint16:
            image = normalize_to_8bit(image)
    
    return image


def load_mask(path: str) -> np.ndarray | None:
    """
    Load a mask image file.

    Preserves original values as object IDs.
    Supports 8/12/16-bit grayscale images.

    Args:
        path: Path to the mask image file.

    Returns:
        Mask as numpy array (uint16 or uint8) or None if loading fails.
    """
    mask = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    
    if mask is None:
        return None
    
    if len(mask.shape) == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    
    return mask


def normalize_to_8bit(image: np.ndarray) -> np.ndarray:
    """
    Normalize image to 8-bit range.

    Args:
        image: Input image (any bit depth).

    Returns:
        8-bit normalized image.
    """
    if image.dtype == np.uint8:
        return image
    
    img_min = image.min()
    img_max = image.max()
    
    if img_max == img_min:
        return np.zeros(image.shape, dtype=np.uint8)
    
    normalized = ((image.astype(np.float64) - img_min) / 
                  (img_max - img_min) * 255).astype(np.uint8)
    
    return normalized


def numpy_to_qimage(image: np.ndarray) -> QImage:
    """
    Convert numpy array to QImage.

    Args:
        image: Input image (BGR or RGB format).

    Returns:
        QImage object.
    """
    if len(image.shape) == 2:
        height, width = image.shape
        bytes_per_line = width
        return QImage(
            image.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8
        )
    
    height, width, channels = image.shape
    
    if channels == 3:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * width
        return QImage(
            rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888
        ).copy()
    elif channels == 4:
        rgba_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
        bytes_per_line = 4 * width
        return QImage(
            rgba_image.data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888
        ).copy()
    
    return QImage()


def numpy_to_qpixmap(image: np.ndarray) -> QPixmap:
    """
    Convert numpy array to QPixmap.

    Args:
        image: Input image (BGR or RGB format).

    Returns:
        QPixmap object.
    """
    qimage = numpy_to_qimage(image)
    return QPixmap.fromImage(qimage)


def ensure_bgr(image: np.ndarray) -> np.ndarray:
    """
    Ensure image is in BGR format.

    Args:
        image: Input image.

    Returns:
        Image in BGR format.
    """
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    
    return image


def get_image_info(image: np.ndarray) -> dict:
    """
    Get information about an image.

    Args:
        image: Input image.

    Returns:
        Dictionary with image information.
    """
    info = {
        'height': image.shape[0],
        'width': image.shape[1],
        'channels': image.shape[2] if len(image.shape) == 3 else 1,
        'dtype': str(image.dtype),
        'min_value': int(image.min()),
        'max_value': int(image.max()),
    }
    return info
