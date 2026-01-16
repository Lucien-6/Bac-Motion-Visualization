"""
Color mapping and assignment module.

Provides color assignment for objects using golden angle distribution
and velocity-based coloring using matplotlib colormaps.
"""

import colorsys

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Normalize

from ..utils import get_logger

logger = get_logger(__name__)


GOLDEN_ANGLE = 137.50776405003785


class ColorMapper:
    """
    Manages color assignment for objects and velocity coloring.
    
    Uses golden angle distribution for object colors to ensure
    good visual separation even for adjacent IDs.
    """
    
    def __init__(self):
        """Initialize color mapper."""
        self._object_colors: dict[int, tuple[int, int, int]] = {}
        self._colormap_cache: dict[str, np.ndarray] = {}
    
    def assign_colors(
        self,
        obj_ids: list[int],
        saturation: float = 0.75,
        value: float = 0.9
    ):
        """
        Assign unique colors to objects using golden angle distribution.
        
        Args:
            obj_ids: List of object IDs.
            saturation: Color saturation (0-1).
            value: Color value/brightness (0-1).
        """
        self._object_colors.clear()
        
        for i, obj_id in enumerate(obj_ids):
            hue = (i * GOLDEN_ANGLE) % 360 / 360
            
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            
            color = (int(r * 255), int(g * 255), int(b * 255))
            self._object_colors[obj_id] = color
        
        logger.info(f"Assigned colors to {len(obj_ids)} objects")
    
    def get_object_color(self, obj_id: int) -> tuple[int, int, int]:
        """
        Get RGB color for an object.
        
        Args:
            obj_id: Object ID.
            
        Returns:
            (R, G, B) tuple (0-255 range).
        """
        if obj_id in self._object_colors:
            return self._object_colors[obj_id]
        
        hue = (obj_id * GOLDEN_ANGLE) % 360 / 360
        r, g, b = colorsys.hsv_to_rgb(hue, 0.75, 0.9)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def get_object_color_bgr(self, obj_id: int) -> tuple[int, int, int]:
        """
        Get BGR color for an object (OpenCV format).
        
        Args:
            obj_id: Object ID.
            
        Returns:
            (B, G, R) tuple (0-255 range).
        """
        r, g, b = self.get_object_color(obj_id)
        return (b, g, r)
    
    def get_velocity_color(
        self,
        velocity: float,
        vmin: float,
        vmax: float,
        colormap: str = 'viridis'
    ) -> tuple[int, int, int]:
        """
        Get RGB color based on velocity value.
        
        Args:
            velocity: Velocity value.
            vmin: Minimum velocity for colormap.
            vmax: Maximum velocity for colormap.
            colormap: Matplotlib colormap name.
            
        Returns:
            (R, G, B) tuple (0-255 range).
        """
        norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
        normalized = norm(velocity)
        
        cmap = colormaps.get_cmap(colormap)
        rgba = cmap(normalized)
        
        r = int(rgba[0] * 255)
        g = int(rgba[1] * 255)
        b = int(rgba[2] * 255)
        
        return (r, g, b)
    
    def get_velocity_color_bgr(
        self,
        velocity: float,
        vmin: float,
        vmax: float,
        colormap: str = 'viridis'
    ) -> tuple[int, int, int]:
        """
        Get BGR color based on velocity value (OpenCV format).
        
        Args:
            velocity: Velocity value.
            vmin: Minimum velocity for colormap.
            vmax: Maximum velocity for colormap.
            colormap: Matplotlib colormap name.
            
        Returns:
            (B, G, R) tuple (0-255 range).
        """
        r, g, b = self.get_velocity_color(velocity, vmin, vmax, colormap)
        return (b, g, r)
    
    def get_colormap_lut(
        self,
        colormap: str,
        n: int = 256
    ) -> np.ndarray:
        """
        Get colormap lookup table.
        
        Args:
            colormap: Matplotlib colormap name.
            n: Number of colors in the LUT.
            
        Returns:
            Numpy array of shape (n, 3) with RGB values (0-255).
        """
        cache_key = f"{colormap}_{n}"
        
        if cache_key in self._colormap_cache:
            return self._colormap_cache[cache_key]
        
        cmap = colormaps.get_cmap(colormap)
        lut = np.zeros((n, 3), dtype=np.uint8)
        
        for i in range(n):
            rgba = cmap(i / (n - 1))
            lut[i] = [int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255)]
        
        self._colormap_cache[cache_key] = lut
        return lut
    
    def get_colormap_image(
        self,
        colormap: str,
        width: int,
        height: int,
        orientation: str = 'vertical'
    ) -> np.ndarray:
        """
        Generate a colormap image for visualization.
        
        Args:
            colormap: Matplotlib colormap name.
            width: Image width.
            height: Image height.
            orientation: 'vertical' or 'horizontal'.
            
        Returns:
            Numpy array (BGR format) of the colormap image.
        """
        lut = self.get_colormap_lut(colormap, 256)
        
        if orientation == 'vertical':
            gradient = np.linspace(255, 0, height, dtype=np.uint8)
            gradient = gradient.reshape(-1, 1)
            gradient = np.repeat(gradient, width, axis=1)
        else:
            gradient = np.linspace(0, 255, width, dtype=np.uint8)
            gradient = gradient.reshape(1, -1)
            gradient = np.repeat(gradient, height, axis=0)
        
        image = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(3):
            image[:, :, i] = lut[gradient, 2 - i]
        
        return image
    
    @staticmethod
    def get_available_colormaps() -> list[str]:
        """
        Get list of available matplotlib colormaps.
        
        Returns:
            List of colormap names.
        """
        recommended = [
            'viridis', 'plasma', 'inferno', 'magma', 'cividis',
            'jet', 'turbo', 'rainbow', 'coolwarm', 'RdYlBu',
            'hot', 'cool', 'spring', 'summer', 'autumn', 'winter',
        ]
        return recommended
