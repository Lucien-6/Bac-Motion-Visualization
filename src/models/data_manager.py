"""
Image sequence data manager.

Handles loading and managing original image sequences and mask sequences
with LRU caching for memory efficiency.
"""

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from ..utils import get_logger, get_image_files, load_image, load_mask

logger = get_logger(__name__)


# Forward declaration for type hints
TrajectoryDataLoader = None


class DataManager:
    """
    Manages image sequences for visualization.
    
    Handles loading, validation, and cached access to original images
    and mask sequences.
    """
    
    def __init__(self, cache_size: int = 100):
        """
        Initialize data manager.
        
        Args:
            cache_size: Maximum number of frames to cache in memory.
        """
        self._original_paths: list[Path] = []
        self._mask_paths: list[Path] = []
        self._frame_count: int = 0
        self._frame_width: int = 0
        self._frame_height: int = 0
        self._object_ids: list[int] = []
        self._cache_size = cache_size
        
        # External trajectory data support
        self._trajectory_loader = None
        self._use_external_trajectory: bool = False
        
        self._setup_cache()
    
    def _setup_cache(self):
        """Set up LRU cached methods."""
        self._get_frame_cached = lru_cache(maxsize=self._cache_size)(
            self._load_frame_uncached
        )
        self._get_mask_cached = lru_cache(maxsize=self._cache_size)(
            self._load_mask_uncached
        )
    
    def clear_cache(self):
        """Clear all cached frames."""
        self._get_frame_cached.cache_clear()
        self._get_mask_cached.cache_clear()
        logger.info("Frame cache cleared")
    
    def load_original_sequence(self, folder: str) -> tuple[bool, str]:
        """
        Load original image sequence from folder.
        
        Args:
            folder: Path to folder containing image files.
            
        Returns:
            Tuple of (success, message).
        """
        paths = get_image_files(folder)
        
        if not paths:
            msg = f"No image files found in {folder}"
            logger.error(msg)
            return False, msg
        
        first_image = load_image(str(paths[0]))
        if first_image is None:
            msg = f"Failed to load first image: {paths[0]}"
            logger.error(msg)
            return False, msg
        
        self._original_paths = paths
        self._frame_count = len(paths)
        self._frame_height, self._frame_width = first_image.shape[:2]
        
        self.clear_cache()
        
        msg = f"Loaded {self._frame_count} original images ({self._frame_width}x{self._frame_height})"
        logger.info(msg)
        return True, msg
    
    def load_mask_sequence(self, folder: str) -> tuple[bool, str]:
        """
        Load mask image sequence from folder.
        
        Args:
            folder: Path to folder containing mask files.
            
        Returns:
            Tuple of (success, message).
        """
        paths = get_image_files(folder)
        
        if not paths:
            msg = f"No image files found in {folder}"
            logger.error(msg)
            return False, msg
        
        self._mask_paths = paths
        
        self.clear_cache()
        
        self._extract_object_ids()
        
        msg = f"Loaded {len(paths)} mask images with {len(self._object_ids)} objects"
        logger.info(msg)
        return True, msg
    
    def _extract_object_ids(self):
        """Extract all unique object IDs from mask sequence."""
        all_ids = set()
        
        sample_indices = list(range(0, len(self._mask_paths), 
                                    max(1, len(self._mask_paths) // 10)))
        if len(self._mask_paths) - 1 not in sample_indices:
            sample_indices.append(len(self._mask_paths) - 1)
        
        for idx in sample_indices:
            mask = self._load_mask_uncached(idx)
            if mask is not None:
                unique_ids = np.unique(mask)
                all_ids.update(unique_ids.tolist())
        
        all_ids.discard(0)
        self._object_ids = sorted(list(all_ids))
        
        logger.info(f"Found {len(self._object_ids)} unique object IDs")
    
    def validate_sequences(self) -> tuple[bool, str]:
        """
        Validate that original and mask sequences are compatible.
        
        Returns:
            Tuple of (valid, message).
        """
        if not self._original_paths:
            return False, "Original image sequence not loaded"
        
        if not self._mask_paths:
            return False, "Mask image sequence not loaded"
        
        if len(self._original_paths) != len(self._mask_paths):
            return False, (
                f"Sequence length mismatch: {len(self._original_paths)} original images "
                f"vs {len(self._mask_paths)} mask images"
            )
        
        first_mask = self._load_mask_uncached(0)
        if first_mask is None:
            return False, "Failed to load first mask image"
        
        mask_h, mask_w = first_mask.shape[:2]
        
        if mask_w != self._frame_width or mask_h != self._frame_height:
            return False, (
                f"Size mismatch: original {self._frame_width}x{self._frame_height} "
                f"vs mask {mask_w}x{mask_h}"
            )
        
        return True, "Sequences validated successfully"
    
    def _load_frame_uncached(self, index: int) -> np.ndarray | None:
        """Load a frame without caching."""
        if index < 0 or index >= len(self._original_paths):
            return None
        return load_image(str(self._original_paths[index]))
    
    def _load_mask_uncached(self, index: int) -> np.ndarray | None:
        """Load a mask without caching."""
        if index < 0 or index >= len(self._mask_paths):
            return None
        return load_mask(str(self._mask_paths[index]))
    
    def get_frame(self, index: int) -> np.ndarray | None:
        """
        Get an original image frame (cached).
        
        Args:
            index: Frame index (0-based).
            
        Returns:
            Image as numpy array (BGR format) or None.
        """
        return self._get_frame_cached(index)
    
    def get_mask(self, index: int) -> np.ndarray | None:
        """
        Get a mask frame (cached).
        
        Args:
            index: Frame index (0-based).
            
        Returns:
            Mask as numpy array or None.
        """
        return self._get_mask_cached(index)
    
    @property
    def frame_count(self) -> int:
        """Get total number of frames."""
        return self._frame_count
    
    @property
    def frame_width(self) -> int:
        """Get frame width in pixels."""
        return self._frame_width
    
    @property
    def frame_height(self) -> int:
        """Get frame height in pixels."""
        return self._frame_height
    
    @property
    def frame_size(self) -> tuple[int, int]:
        """Get frame size as (width, height)."""
        return (self._frame_width, self._frame_height)
    
    @property
    def object_ids(self) -> list[int]:
        """Get list of all object IDs."""
        return self._object_ids.copy()
    
    @property
    def is_loaded(self) -> bool:
        """Check if both sequences are loaded and validated."""
        return bool(self._original_paths and self._mask_paths)
    
    def get_object_at_position(
        self, 
        frame_index: int, 
        x: int, 
        y: int
    ) -> int | None:
        """
        Get object ID at a specific position in a frame.
        
        Args:
            frame_index: Frame index.
            x: X coordinate.
            y: Y coordinate.
            
        Returns:
            Object ID or None if background or out of bounds.
        """
        mask = self.get_mask(frame_index)
        if mask is None:
            return None
        
        if x < 0 or x >= mask.shape[1] or y < 0 or y >= mask.shape[0]:
            return None
        
        obj_id = int(mask[y, x])
        return obj_id if obj_id != 0 else None
    
    def set_trajectory_loader(self, loader) -> None:
        """
        Set external trajectory data loader.
        
        Args:
            loader: TrajectoryDataLoader instance.
        """
        self._trajectory_loader = loader
        self._use_external_trajectory = loader is not None
        logger.info(
            f"External trajectory loader {'set' if loader else 'cleared'}"
        )
    
    def has_external_trajectory(self) -> bool:
        """
        Check if external trajectory data is available.
        
        Returns:
            True if external trajectory data is loaded.
        """
        return self._use_external_trajectory and self._trajectory_loader is not None
    
    def get_external_trajectories(self) -> dict[int, list[tuple[int, float, float]]]:
        """
        Get external trajectory data.
        
        Returns:
            Dictionary mapping object ID to list of (frame, x, y) tuples.
        """
        if not self.has_external_trajectory():
            return {}
        return self._trajectory_loader.get_trajectories()
    
    def get_external_object_ids(self) -> list[int]:
        """
        Get object IDs from external trajectory data.
        
        Returns:
            List of object IDs in order of first appearance.
        """
        if not self.has_external_trajectory():
            return []
        return self._trajectory_loader.get_object_ids()
    
    def validate_trajectory_with_masks(self) -> tuple[bool, str]:
        """
        Validate that each trajectory point has a corresponding mask.
        
        For each (frame, x, y) in trajectory data, checks that
        mask[y, x] != 0 at that frame.
        
        Returns:
            Tuple of (valid, error_message).
        """
        if not self.has_external_trajectory():
            return True, "No external trajectory to validate"
        
        trajectories = self._trajectory_loader.get_trajectories()
        
        for obj_id, points in trajectories.items():
            for frame, x, y in points:
                mask = self.get_mask(frame)
                if mask is None:
                    return False, (
                        f"Object {obj_id}: Failed to load mask for frame {frame}"
                    )
                
                # Convert float coordinates to integer pixel positions
                px = int(round(x))
                py = int(round(y))
                
                # Check bounds
                if px < 0 or px >= mask.shape[1] or py < 0 or py >= mask.shape[0]:
                    return False, (
                        f"Object {obj_id} at frame {frame}: "
                        f"Position ({px}, {py}) is out of image bounds"
                    )
                
                # Check if there's a mask at this position
                mask_value = int(mask[py, px])
                if mask_value == 0:
                    return False, (
                        f"Object {obj_id} at frame {frame}: "
                        f"No mask found at trajectory position ({px}, {py})"
                    )
        
        logger.info("Trajectory-mask validation passed")
        return True, "Validation passed"
    
    def clear_external_trajectory(self) -> None:
        """Clear external trajectory data."""
        self._trajectory_loader = None
        self._use_external_trajectory = False
        logger.info("External trajectory data cleared")