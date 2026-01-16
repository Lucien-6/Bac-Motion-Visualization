"""
Trajectory and velocity calculator.

Computes object centroids, trajectories, and instantaneous velocities
from mask sequences using vectorized operations for performance.
"""

import numpy as np
from scipy import ndimage

from ..utils import get_logger

logger = get_logger(__name__)


class TrajectoryCalculator:
    """
    Calculates and stores trajectory data for all objects.
    
    Uses scipy.ndimage for efficient centroid calculation
    across all objects simultaneously.
    """
    
    def __init__(self):
        """Initialize trajectory calculator."""
        self._trajectories: dict[int, dict] = {}
        self._is_calculated: bool = False
        self._last_fps: float = 0.0
        self._last_um_per_pixel: float = 0.0
    
    def calculate_all_trajectories(
        self,
        data_manager,
        original_fps: float,
        um_per_pixel: float,
        progress_callback=None
    ) -> bool:
        """
        Calculate trajectories for all objects in the sequence.
        
        Args:
            data_manager: DataManager instance with loaded sequences.
            original_fps: Original video frame rate (fps).
            um_per_pixel: Micrometers per pixel conversion factor.
            progress_callback: Optional callback(current, total) for progress.
            
        Returns:
            True if successful, False otherwise.
        """
        if not data_manager.is_loaded:
            logger.error("Data not loaded")
            return False
        
        self._trajectories.clear()
        
        object_ids = data_manager.object_ids
        for obj_id in object_ids:
            self._trajectories[obj_id] = {
                'centroids': [],
                'velocities': [],
            }
        
        frame_count = data_manager.frame_count
        frame_interval = 1.0 / original_fps if original_fps > 0 else 1.0
        
        logger.info(f"Calculating trajectories for {len(object_ids)} objects "
                    f"across {frame_count} frames")
        
        prev_centroids: dict[int, tuple[float, float]] = {}
        
        for frame_idx in range(frame_count):
            mask = data_manager.get_mask(frame_idx)
            if mask is None:
                continue
            
            current_centroids = self._calculate_frame_centroids(mask, object_ids)
            
            for obj_id, centroid in current_centroids.items():
                if centroid is not None:
                    self._trajectories[obj_id]['centroids'].append(
                        (frame_idx, centroid[0], centroid[1])
                    )
                    
                    if obj_id in prev_centroids and prev_centroids[obj_id] is not None:
                        prev_x, prev_y = prev_centroids[obj_id]
                        curr_x, curr_y = centroid
                        
                        dx = (curr_x - prev_x) * um_per_pixel
                        dy = (curr_y - prev_y) * um_per_pixel
                        distance = np.sqrt(dx**2 + dy**2)
                        velocity = distance / frame_interval
                        
                        self._trajectories[obj_id]['velocities'].append(
                            (frame_idx, velocity)
                        )
            
            prev_centroids = current_centroids
            
            if progress_callback and frame_idx % 100 == 0:
                progress_callback(frame_idx + 1, frame_count)
        
        self._is_calculated = True
        self._last_fps = original_fps
        self._last_um_per_pixel = um_per_pixel
        logger.info("Trajectory calculation completed")
        
        return True
    
    def _calculate_frame_centroids(
        self,
        mask: np.ndarray,
        object_ids: list[int]
    ) -> dict[int, tuple[float, float] | None]:
        """
        Calculate centroids for all objects in a single frame.
        
        Uses scipy.ndimage.center_of_mass for vectorized computation.
        
        Args:
            mask: Mask image.
            object_ids: List of object IDs to find.
            
        Returns:
            Dictionary mapping object ID to (x, y) centroid or None.
        """
        result = {}
        
        present_ids = [oid for oid in object_ids if oid in np.unique(mask)]
        
        if present_ids:
            centroids = ndimage.center_of_mass(
                mask > 0,
                labels=mask,
                index=present_ids
            )
            
            for obj_id, centroid in zip(present_ids, centroids):
                if not np.isnan(centroid[0]) and not np.isnan(centroid[1]):
                    result[obj_id] = (centroid[1], centroid[0])
        
        for obj_id in object_ids:
            if obj_id not in result:
                result[obj_id] = None
        
        return result
    
    def get_centroid(
        self,
        obj_id: int,
        frame: int
    ) -> tuple[float, float] | None:
        """
        Get centroid position of an object at a specific frame.
        
        Args:
            obj_id: Object ID.
            frame: Frame index.
            
        Returns:
            (x, y) centroid or None if not present.
        """
        if obj_id not in self._trajectories:
            return None
        
        centroids = self._trajectories[obj_id]['centroids']
        for f, x, y in centroids:
            if f == frame:
                return (x, y)
        
        return None
    
    def get_trajectory(self, obj_id: int) -> list[tuple[int, float, float]]:
        """
        Get complete trajectory for an object.
        
        Args:
            obj_id: Object ID.
            
        Returns:
            List of (frame, x, y) tuples.
        """
        if obj_id not in self._trajectories:
            return []
        return self._trajectories[obj_id]['centroids'].copy()
    
    def get_trajectory_segment(
        self,
        obj_id: int,
        start_frame: int,
        end_frame: int
    ) -> list[tuple[int, float, float]]:
        """
        Get trajectory segment for an object within frame range.
        
        Args:
            obj_id: Object ID.
            start_frame: Start frame index (inclusive).
            end_frame: End frame index (inclusive).
            
        Returns:
            List of (frame, x, y) tuples within range.
        """
        trajectory = self.get_trajectory(obj_id)
        return [
            (f, x, y) for f, x, y in trajectory
            if start_frame <= f <= end_frame
        ]
    
    def get_velocity(self, obj_id: int, frame: int) -> float | None:
        """
        Get instantaneous velocity of an object at a specific frame.
        
        Args:
            obj_id: Object ID.
            frame: Frame index.
            
        Returns:
            Velocity in μm/s or None if not available.
        """
        if obj_id not in self._trajectories:
            return None
        
        velocities = self._trajectories[obj_id]['velocities']
        for f, v in velocities:
            if f == frame:
                return v
        
        return None
    
    def get_velocity_range(self) -> tuple[float, float]:
        """
        Get minimum and maximum velocities across all objects and frames.
        
        Returns:
            (min_velocity, max_velocity) tuple.
        """
        all_velocities = []
        
        for obj_data in self._trajectories.values():
            for _, v in obj_data['velocities']:
                all_velocities.append(v)
        
        if not all_velocities:
            return (0.0, 100.0)
        
        return (min(all_velocities), max(all_velocities))
    
    def get_object_frame_range(self, obj_id: int) -> tuple[int, int] | None:
        """
        Get the frame range where an object appears.
        
        Args:
            obj_id: Object ID.
            
        Returns:
            (first_frame, last_frame) tuple or None if object not found.
        """
        if obj_id not in self._trajectories:
            return None
        
        centroids = self._trajectories[obj_id]['centroids']
        if not centroids:
            return None
        
        frames = [f for f, _, _ in centroids]
        return (min(frames), max(frames))
    
    def rescale_velocities(
        self,
        new_fps: float,
        new_um_per_pixel: float
    ) -> bool:
        """
        Rescale all velocities based on new parameters.
        
        This is much faster than recalculating from scratch since
        centroids don't change - only the velocity scaling factors do.
        
        velocity = (displacement_px * um_per_pixel) / frame_interval
        new_velocity = old_velocity * (new_um / old_um) * (new_fps / old_fps)
        
        Args:
            new_fps: New frame rate (fps).
            new_um_per_pixel: New micrometers per pixel factor.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self._is_calculated:
            logger.warning("Cannot rescale: trajectories not calculated")
            return False
        
        if self._last_fps <= 0 or self._last_um_per_pixel <= 0:
            logger.warning("Cannot rescale: invalid previous parameters")
            return False
        
        # Calculate scale factor
        um_scale = new_um_per_pixel / self._last_um_per_pixel
        fps_scale = new_fps / self._last_fps
        total_scale = um_scale * fps_scale
        
        # Skip if no change
        if abs(total_scale - 1.0) < 1e-9:
            return True
        
        # Rescale all velocities
        for obj_data in self._trajectories.values():
            obj_data['velocities'] = [
                (frame, velocity * total_scale)
                for frame, velocity in obj_data['velocities']
            ]
        
        # Update stored parameters
        self._last_fps = new_fps
        self._last_um_per_pixel = new_um_per_pixel
        
        logger.info(f"Velocities rescaled by factor {total_scale:.4f}")
        return True
    
    @property
    def last_fps(self) -> float:
        """Get the FPS used in last calculation."""
        return self._last_fps
    
    @property
    def last_um_per_pixel(self) -> float:
        """Get the um/pixel used in last calculation."""
        return self._last_um_per_pixel
    
    @property
    def is_calculated(self) -> bool:
        """Check if trajectories have been calculated."""
        return self._is_calculated
    
    @property
    def object_count(self) -> int:
        """Get number of tracked objects."""
        return len(self._trajectories)
    
    def set_from_external_data(
        self,
        external_trajectories: dict[int, list[tuple[int, float, float]]],
        data_manager,
        original_fps: float,
        um_per_pixel: float
    ) -> tuple[bool, str]:
        """
        Initialize trajectories from external trajectory data.
        
        Validates that each trajectory point has a corresponding mask,
        reassigns object IDs in order of first appearance, and
        calculates velocities.
        
        Args:
            external_trajectories: Dict mapping original ID to list of
                                   (frame, x, y) tuples.
            data_manager: DataManager instance for mask validation.
            original_fps: Original video frame rate.
            um_per_pixel: Micrometers per pixel conversion factor.
            
        Returns:
            Tuple of (success, error_message).
        """
        self._trajectories.clear()
        
        frame_interval = 1.0 / original_fps if original_fps > 0 else 1.0
        
        # Process each object's trajectory
        new_id = 1
        id_mapping = {}
        
        # Get object IDs in order of first appearance
        object_order = []
        first_frame = {}
        for orig_id, points in external_trajectories.items():
            if points:
                min_frame = min(p[0] for p in points)
                first_frame[orig_id] = min_frame
                object_order.append(orig_id)
        
        # Sort by first appearance frame, then by original ID for stability
        object_order.sort(key=lambda oid: (first_frame[oid], oid))
        
        for orig_id in object_order:
            points = external_trajectories[orig_id]
            if not points:
                continue
            
            # Assign new ID
            id_mapping[orig_id] = new_id
            
            # Validate each point against mask
            for frame, x, y in points:
                mask = data_manager.get_mask(frame)
                if mask is None:
                    return False, (
                        f"Object {orig_id}: Failed to load mask for frame {frame}"
                    )
                
                px = int(round(x))
                py = int(round(y))
                
                if px < 0 or px >= mask.shape[1] or py < 0 or py >= mask.shape[0]:
                    return False, (
                        f"Object {orig_id} at frame {frame}: "
                        f"Position ({px}, {py}) is out of image bounds"
                    )
                
                mask_value = int(mask[py, px])
                if mask_value == 0:
                    return False, (
                        f"Object {orig_id} at frame {frame}: "
                        f"No mask found at trajectory position ({px}, {py})"
                    )
            
            # Sort points by frame
            sorted_points = sorted(points, key=lambda p: p[0])
            
            # Build trajectory data
            self._trajectories[new_id] = {
                'centroids': [(f, x, y) for f, x, y in sorted_points],
                'velocities': [],
                'original_id': orig_id,
            }
            
            # Calculate velocities
            for i in range(1, len(sorted_points)):
                prev_f, prev_x, prev_y = sorted_points[i - 1]
                curr_f, curr_x, curr_y = sorted_points[i]
                
                dx = (curr_x - prev_x) * um_per_pixel
                dy = (curr_y - prev_y) * um_per_pixel
                distance = np.sqrt(dx**2 + dy**2)
                
                # Time elapsed (in seconds)
                time_elapsed = (curr_f - prev_f) * frame_interval
                if time_elapsed > 0:
                    velocity = distance / time_elapsed
                else:
                    velocity = 0.0
                
                self._trajectories[new_id]['velocities'].append(
                    (curr_f, velocity)
                )
            
            new_id += 1
        
        self._is_calculated = True
        self._last_fps = original_fps
        self._last_um_per_pixel = um_per_pixel
        
        logger.info(
            f"Loaded {len(self._trajectories)} trajectories from external data"
        )
        
        return True, f"Loaded {len(self._trajectories)} object trajectories"
    
    def get_new_object_ids(self) -> list[int]:
        """
        Get list of new object IDs (after reassignment).
        
        Returns:
            List of object IDs.
        """
        return sorted(self._trajectories.keys())
    
    def get_original_id(self, new_id: int) -> int | None:
        """
        Get original object ID for a reassigned ID.
        
        Args:
            new_id: New (reassigned) object ID.
            
        Returns:
            Original object ID or None if not found.
        """
        if new_id not in self._trajectories:
            return None
        return self._trajectories[new_id].get('original_id', new_id)