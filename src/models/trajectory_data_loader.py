"""
Trajectory data loader.

Loads and parses trajectory data from Excel or CSV files.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from ..utils import get_logger

logger = get_logger(__name__)


class TrajectoryDataLoader:
    """
    Loads and parses trajectory data from Excel or CSV files.
    
    Handles unit conversion for time and space coordinates,
    validates data integrity, and provides trajectory data
    in a format suitable for visualization.
    """
    
    def __init__(self):
        """Initialize trajectory data loader."""
        self._file_path: str = ""
        self._file_type: str = "csv"  # "excel" or "csv"
        self._id_column: str = ""  # Only used for CSV
        self._time_column: str = ""
        self._x_column: str = ""
        self._y_column: str = ""
        self._data_start_row: int = 1
        self._time_unit: str = "frame"
        self._space_unit: str = "pixel"
        self._original_fps: float = 1.0
        self._um_per_pixel: float = 1.0
        
        self._raw_data: pd.DataFrame | None = None
        self._sheet_data: dict[str, pd.DataFrame] = {}  # For Excel multi-sheet
        self._trajectories: dict[int, list[tuple[int, float, float]]] = {}
        self._object_ids: list[int] = []
    
    def set_parameters(
        self,
        file_path: str,
        file_type: str,
        time_column: str,
        x_column: str,
        y_column: str,
        data_start_row: int,
        time_unit: str,
        space_unit: str,
        original_fps: float,
        um_per_pixel: float,
        id_column: str = ""
    ):
        """
        Set loading parameters.
        
        Args:
            file_path: Path to trajectory data file.
            file_type: File type ("excel" or "csv").
            time_column: Name of time column.
            x_column: Name of X coordinate column.
            y_column: Name of Y coordinate column.
            data_start_row: Row number where data starts (1-based, after header).
            time_unit: Time unit ("frame", "ms", "s", "min", "h").
            space_unit: Space unit ("μm", "pixel").
            original_fps: Original video frame rate.
            um_per_pixel: Micrometers per pixel conversion factor.
            id_column: Name of ID column (required for CSV, ignored for Excel).
        """
        self._file_path = file_path
        self._file_type = file_type
        self._id_column = id_column
        self._time_column = time_column
        self._x_column = x_column
        self._y_column = y_column
        self._data_start_row = data_start_row
        self._time_unit = time_unit
        self._space_unit = space_unit
        self._original_fps = original_fps
        self._um_per_pixel = um_per_pixel
    
    @staticmethod
    def get_columns(file_path: str, header_row: int = 0) -> tuple[list[str], str, str]:
        """
        Read column headers from a trajectory file.
        
        Args:
            file_path: Path to the file.
            header_row: Row index of the header (0-based).
            
        Returns:
            Tuple of (column_names, file_type, error_message).
            file_type is "excel" or "csv".
            If successful, error_message is empty.
        """
        try:
            path = Path(file_path)
            suffix = path.suffix.lower()
            
            if suffix in ('.xlsx', '.xls'):
                file_type = "excel"
                # For Excel, read from the first sheet
                df = pd.read_excel(file_path, header=header_row, nrows=0)
            elif suffix == '.csv':
                file_type = "csv"
                df = pd.read_csv(file_path, header=header_row, nrows=0)
            else:
                return [], "", f"Unsupported file format: {suffix}"
            
            columns = df.columns.tolist()
            columns = [str(col) for col in columns]
            
            return columns, file_type, ""
            
        except Exception as e:
            logger.error(f"Failed to read columns: {e}")
            return [], "", str(e)
    
    def load_file(self) -> tuple[bool, str]:
        """
        Load and parse the trajectory file.
        
        For Excel files: each sheet contains one object's trajectory.
        For CSV files: all objects in one file with ID column.
        
        Returns:
            Tuple of (success, message).
        """
        try:
            # Calculate skiprows: skip rows before data_start_row (excluding header)
            skiprows_after_header = self._data_start_row - 1
            
            if self._file_type == "excel":
                return self._load_excel_file(skiprows_after_header)
            else:
                return self._load_csv_file(skiprows_after_header)
            
        except Exception as e:
            logger.error(f"Failed to load trajectory file: {e}")
            return False, str(e)
    
    def _load_excel_file(self, skiprows_after_header: int) -> tuple[bool, str]:
        """
        Load Excel file with each sheet as a separate object.
        
        Args:
            skiprows_after_header: Number of rows to skip after header.
            
        Returns:
            Tuple of (success, message).
        """
        # Read all sheet names
        excel_file = pd.ExcelFile(self._file_path)
        sheet_names = excel_file.sheet_names
        
        if not sheet_names:
            return False, "Excel file has no sheets"
        
        self._sheet_data = {}
        required_columns = [self._time_column, self._x_column, self._y_column]
        reference_columns = None
        
        for sheet_name in sheet_names:
            df = pd.read_excel(
                self._file_path,
                sheet_name=sheet_name,
                header=0,
                skiprows=range(1, 1 + skiprows_after_header) if skiprows_after_header > 0 else None
            )
            
            # Verify columns exist
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                return False, (
                    f"Sheet '{sheet_name}': Missing columns: {', '.join(missing)}"
                )
            
            # Verify all sheets have the same columns (header consistency)
            current_columns = set(df.columns.tolist())
            if reference_columns is None:
                reference_columns = current_columns
            elif current_columns != reference_columns:
                return False, (
                    f"Sheet '{sheet_name}' has different column headers than the first sheet. "
                    f"All sheets must have identical column headers."
                )
            
            self._sheet_data[sheet_name] = df
        
        total_points = sum(len(df) for df in self._sheet_data.values())
        logger.info(
            f"Loaded Excel file with {len(sheet_names)} sheets, "
            f"{total_points} total trajectory points"
        )
        return True, f"Loaded {len(sheet_names)} objects from {len(sheet_names)} sheets"
    
    def _load_csv_file(self, skiprows_after_header: int) -> tuple[bool, str]:
        """
        Load CSV file with ID column.
        
        Args:
            skiprows_after_header: Number of rows to skip after header.
            
        Returns:
            Tuple of (success, message).
        """
        df = pd.read_csv(
            self._file_path,
            header=0,
            skiprows=range(1, 1 + skiprows_after_header) if skiprows_after_header > 0 else None
        )
        
        # Verify required columns exist
        required_columns = [
            self._id_column, self._time_column,
            self._x_column, self._y_column
        ]
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return False, f"Missing columns: {', '.join(missing)}"
        
        self._raw_data = df
        
        logger.info(f"Loaded CSV file with {len(df)} rows")
        return True, f"Loaded {len(df)} trajectory points"
    
    def convert_trajectories(self) -> tuple[bool, str]:
        """
        Convert raw data to trajectory format with unit conversions.
        
        For Excel: each sheet becomes one object (ID assigned by sheet order).
        For CSV: objects grouped by ID column.
        
        Returns:
            Tuple of (success, message).
        """
        try:
            if self._file_type == "excel":
                return self._convert_excel_trajectories()
            else:
                return self._convert_csv_trajectories()
            
        except Exception as e:
            logger.error(f"Failed to convert trajectories: {e}")
            return False, str(e)
    
    def _convert_excel_trajectories(self) -> tuple[bool, str]:
        """
        Convert Excel multi-sheet data to trajectories.
        
        Each sheet becomes one object with ID assigned by sheet order (1, 2, 3...).
        
        Returns:
            Tuple of (success, message).
        """
        if not self._sheet_data:
            return False, "No Excel data loaded"
        
        self._trajectories = {}
        self._object_ids = []
        
        # Assign object IDs in sheet order (1, 2, 3, ...)
        for obj_id, (sheet_name, df) in enumerate(self._sheet_data.items(), start=1):
            times = df[self._time_column].values
            x_coords = df[self._x_column].values
            y_coords = df[self._y_column].values
            
            self._object_ids.append(obj_id)
            self._trajectories[obj_id] = []
            
            for i in range(len(times)):
                time_val = float(times[i])
                x_val = float(x_coords[i])
                y_val = float(y_coords[i])
                
                frame = self._convert_time_to_frame(time_val)
                x_pixel = self._convert_space_to_pixel(x_val)
                y_pixel = self._convert_space_to_pixel(y_val)
                
                self._trajectories[obj_id].append((frame, x_pixel, y_pixel))
            
            # Sort trajectory by frame
            self._trajectories[obj_id].sort(key=lambda x: x[0])
        
        total_points = sum(len(traj) for traj in self._trajectories.values())
        logger.info(
            f"Converted {total_points} trajectory points for "
            f"{len(self._object_ids)} objects from Excel sheets"
        )
        
        return True, f"Converted {len(self._object_ids)} object trajectories"
    
    def _convert_csv_trajectories(self) -> tuple[bool, str]:
        """
        Convert CSV data to trajectories.
        
        Objects are grouped by ID column value.
        
        Returns:
            Tuple of (success, message).
        """
        if self._raw_data is None:
            return False, "No CSV data loaded"
        
        df = self._raw_data.copy()
        
        # Extract required columns
        ids = df[self._id_column].values
        times = df[self._time_column].values
        x_coords = df[self._x_column].values
        y_coords = df[self._y_column].values
        
        # Build trajectories grouped by ID (preserving order of first appearance)
        self._trajectories = {}
        self._object_ids = []
        id_order_map = {}
        
        for i in range(len(ids)):
            obj_id = int(ids[i])
            time_val = float(times[i])
            x_val = float(x_coords[i])
            y_val = float(y_coords[i])
            
            # Convert time to frame index
            frame = self._convert_time_to_frame(time_val)
            
            # Convert space to pixels
            x_pixel = self._convert_space_to_pixel(x_val)
            y_pixel = self._convert_space_to_pixel(y_val)
            
            # Track order of first appearance
            if obj_id not in id_order_map:
                id_order_map[obj_id] = len(self._object_ids)
                self._object_ids.append(obj_id)
                self._trajectories[obj_id] = []
            
            self._trajectories[obj_id].append((frame, x_pixel, y_pixel))
        
        # Sort each trajectory by frame
        for obj_id in self._trajectories:
            self._trajectories[obj_id].sort(key=lambda x: x[0])
        
        total_points = sum(len(traj) for traj in self._trajectories.values())
        logger.info(
            f"Converted {total_points} trajectory points for "
            f"{len(self._object_ids)} objects from CSV"
        )
        
        return True, f"Converted {len(self._object_ids)} object trajectories"
    
    def validate_data(
        self,
        frame_count: int,
        frame_width: int,
        frame_height: int
    ) -> tuple[bool, str]:
        """
        Validate trajectory data against image sequence constraints.
        
        Args:
            frame_count: Total number of frames in the sequence.
            frame_width: Width of frames in pixels.
            frame_height: Height of frames in pixels.
            
        Returns:
            Tuple of (valid, error_message).
        """
        if not self._trajectories:
            return False, "No trajectory data to validate"
        
        # Check for duplicate IDs (already handled by grouping, but verify)
        # This check is inherently satisfied by our data structure
        
        # Check for duplicate time points within same object
        for obj_id, points in self._trajectories.items():
            frames_seen = set()
            for frame, x, y in points:
                if frame in frames_seen:
                    return False, (
                        f"Object {obj_id} has duplicate data at frame {frame}"
                    )
                frames_seen.add(frame)
        
        # Check frame range
        max_frame = self.get_max_frame()
        if max_frame >= frame_count:
            return False, (
                f"Trajectory data contains frame {max_frame}, "
                f"but sequence only has {frame_count} frames (0-{frame_count - 1})"
            )
        
        # Check coordinate range
        for obj_id, points in self._trajectories.items():
            for frame, x, y in points:
                if x < 0 or x >= frame_width:
                    return False, (
                        f"Object {obj_id} at frame {frame}: "
                        f"X coordinate {x:.1f} is out of range [0, {frame_width})"
                    )
                if y < 0 or y >= frame_height:
                    return False, (
                        f"Object {obj_id} at frame {frame}: "
                        f"Y coordinate {y:.1f} is out of range [0, {frame_height})"
                    )
        
        logger.info("Trajectory data validation passed")
        return True, "Validation passed"
    
    def get_trajectories(self) -> dict[int, list[tuple[int, float, float]]]:
        """
        Get converted trajectory data.
        
        Returns:
            Dictionary mapping object ID to list of (frame, x, y) tuples.
        """
        return self._trajectories.copy()
    
    def get_object_ids(self) -> list[int]:
        """
        Get object IDs in order of first appearance.
        
        Returns:
            List of object IDs.
        """
        return self._object_ids.copy()
    
    def get_max_frame(self) -> int:
        """
        Get the maximum frame index in the trajectory data.
        
        Returns:
            Maximum frame index.
        """
        max_frame = 0
        for points in self._trajectories.values():
            for frame, _, _ in points:
                max_frame = max(max_frame, frame)
        return max_frame
    
    def get_min_frame(self) -> int:
        """
        Get the minimum frame index in the trajectory data.
        
        Returns:
            Minimum frame index.
        """
        min_frame = float('inf')
        for points in self._trajectories.values():
            for frame, _, _ in points:
                min_frame = min(min_frame, frame)
        return int(min_frame) if min_frame != float('inf') else 0
    
    def _convert_time_to_frame(self, value: float) -> int:
        """
        Convert time value to frame index.
        
        Args:
            value: Time value in the specified unit.
            
        Returns:
            Frame index (0-based).
        """
        if self._time_unit == "frame":
            return int(value)
        elif self._time_unit == "ms":
            time_seconds = value / 1000.0
        elif self._time_unit == "s":
            time_seconds = value
        elif self._time_unit == "min":
            time_seconds = value * 60.0
        elif self._time_unit == "h":
            time_seconds = value * 3600.0
        else:
            return int(value)
        
        frame = int(round(time_seconds * self._original_fps))
        return frame
    
    def _convert_space_to_pixel(self, value: float) -> float:
        """
        Convert space coordinate to pixels.
        
        Args:
            value: Coordinate value in the specified unit.
            
        Returns:
            Coordinate in pixels.
        """
        if self._space_unit == "pixel":
            return value
        elif self._space_unit == "μm":
            return value / self._um_per_pixel
        else:
            return value
    
    @property
    def is_loaded(self) -> bool:
        """Check if trajectory data is loaded."""
        if self._file_type == "excel":
            return bool(self._sheet_data)
        else:
            return self._raw_data is not None
    
    @property
    def point_count(self) -> int:
        """Get total number of trajectory points."""
        return sum(len(traj) for traj in self._trajectories.values())
