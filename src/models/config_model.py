"""
Configuration data models.

Defines dataclasses for all visualization settings with JSON serialization support.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

from ..utils import get_logger

logger = get_logger(__name__)


@dataclass
class GlobalConfig:
    """Global settings."""
    original_fps: float = 1.0
    um_per_pixel: float = 1.0
    output_fps: float = 30.0


@dataclass
class MaskConfig:
    """Mask overlay settings."""
    enabled: bool = True
    opacity: float = 0.5


@dataclass
class ContourConfig:
    """Object contour settings."""
    enabled: bool = True
    thickness: int = 2


@dataclass
class CentroidConfig:
    """Object centroid marker settings."""
    enabled: bool = False
    marker_shape: Literal['circle', 'triangle', 'star'] = 'circle'
    marker_size: int = 5


@dataclass
class EllipseAxesConfig:
    """Object fitted ellipse axes settings."""
    show_major_axis: bool = False
    show_minor_axis: bool = False
    major_thickness: int = 1
    major_color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'white'
    minor_thickness: int = 1
    minor_color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'white'


@dataclass
class TrajectoryConfig:
    """Trajectory display settings."""
    enabled: bool = True
    mode: Literal['full', 'start_to_current', 'delay_before', 'delay_after'] = 'full'
    delay_time: float = 1.0
    thickness: int = 1
    color_mode: Literal['object', 'velocity'] = 'object'


@dataclass
class TimeLabelConfig:
    """Time label settings."""
    enabled: bool = True
    unit: Literal['ms', 's', 'min', 'h'] = 's'
    font_family: Literal['Arial', 'Times New Roman'] = 'Arial'
    font_size: int = 24
    font_bold: bool = False
    color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'white'
    position: list[float] = field(default_factory=lambda: [0.02, 0.02])


@dataclass
class ScaleBarConfig:
    """Scale bar settings."""
    enabled: bool = True
    thickness: int = 3
    length_um: float = 50.0
    bar_color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'white'
    text_enabled: bool = True
    text_position: Literal['above', 'below'] = 'below'
    text_gap: int = 5
    font_family: Literal['Arial', 'Times New Roman'] = 'Arial'
    font_size: int = 18
    font_bold: bool = False
    text_color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'white'
    position: list[float] = field(default_factory=lambda: [0.85, 0.92])


@dataclass
class SpeedLabelConfig:
    """Playback speed label settings."""
    enabled: bool = True
    font_family: Literal['Arial', 'Times New Roman'] = 'Arial'
    font_size: int = 20
    font_bold: bool = False
    color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'white'
    position: list[float] = field(default_factory=lambda: [0.02, 0.92])


@dataclass
class ColorbarConfig:
    """Colorbar settings for velocity coloring mode."""
    enabled: bool = True
    colormap: str = 'viridis'
    bar_height: int = 200
    bar_width: int = 14
    title: str = 'Speed (μm/s)'
    title_font_family: Literal['Arial', 'Times New Roman'] = 'Arial'
    title_font_size: int = 14
    title_font_bold: bool = False
    title_color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'black'
    title_position: Literal['top', 'right'] = 'top'
    title_gap: int = 5
    vmin: float = 0.0
    vmax: float = 100.0
    tick_interval: float = 20.0
    tick_font_family: Literal['Arial', 'Times New Roman'] = 'Arial'
    tick_font_size: int = 12
    tick_font_bold: bool = False
    tick_color: Literal['white', 'black', 'red', 'blue', 'green', 'yellow'] = 'black'
    border_thickness: int = 1
    tick_thickness: int = 1
    tick_length: int = 5
    position: list[float] = field(default_factory=lambda: [1.02, 0.1])


@dataclass
class OutputConfig:
    """Output settings."""
    video_format: Literal['mp4', 'avi', 'gif'] = 'mp4'
    image_prefix: str = 'frame_'
    subfolder_name: str = 'frames'


@dataclass
class VisualizationConfig:
    """Main configuration containing all visualization settings."""
    global_config: GlobalConfig = field(default_factory=GlobalConfig)
    mask: MaskConfig = field(default_factory=MaskConfig)
    contour: ContourConfig = field(default_factory=ContourConfig)
    centroid: CentroidConfig = field(default_factory=CentroidConfig)
    ellipse_axes: EllipseAxesConfig = field(default_factory=EllipseAxesConfig)
    trajectory: TrajectoryConfig = field(default_factory=TrajectoryConfig)
    time_label: TimeLabelConfig = field(default_factory=TimeLabelConfig)
    scale_bar: ScaleBarConfig = field(default_factory=ScaleBarConfig)
    speed_label: SpeedLabelConfig = field(default_factory=SpeedLabelConfig)
    colorbar: ColorbarConfig = field(default_factory=ColorbarConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'global': asdict(self.global_config),
            'mask': asdict(self.mask),
            'contour': asdict(self.contour),
            'centroid': asdict(self.centroid),
            'ellipse_axes': asdict(self.ellipse_axes),
            'trajectory': asdict(self.trajectory),
            'time_label': asdict(self.time_label),
            'scale_bar': asdict(self.scale_bar),
            'speed_label': asdict(self.speed_label),
            'colorbar': asdict(self.colorbar),
            'output': asdict(self.output),
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VisualizationConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        if 'global' in data:
            config.global_config = GlobalConfig(**data['global'])
        if 'mask' in data:
            config.mask = MaskConfig(**data['mask'])
        if 'contour' in data:
            config.contour = ContourConfig(**data['contour'])
        if 'centroid' in data:
            config.centroid = CentroidConfig(**data['centroid'])
        if 'ellipse_axes' in data:
            config.ellipse_axes = EllipseAxesConfig(**data['ellipse_axes'])
        if 'trajectory' in data:
            config.trajectory = TrajectoryConfig(**data['trajectory'])
        if 'time_label' in data:
            config.time_label = TimeLabelConfig(**data['time_label'])
        if 'scale_bar' in data:
            config.scale_bar = ScaleBarConfig(**data['scale_bar'])
        if 'speed_label' in data:
            config.speed_label = SpeedLabelConfig(**data['speed_label'])
        if 'colorbar' in data:
            config.colorbar = ColorbarConfig(**data['colorbar'])
        if 'output' in data:
            config.output = OutputConfig(**data['output'])
        
        return config
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VisualizationConfig':
        """Deserialize configuration from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, path: str | Path) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            path: File path to save to.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            
            logger.info(f"Configuration saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, path: str | Path) -> 'VisualizationConfig | None':
        """
        Load configuration from JSON file.
        
        Args:
            path: File path to load from.
            
        Returns:
            VisualizationConfig instance or None if loading fails.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json_str = f.read()
            
            config = cls.from_json(json_str)
            logger.info(f"Configuration loaded from {path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return None
    
    def get_speed_ratio(self) -> float:
        """Calculate playback speed ratio."""
        if self.global_config.original_fps <= 0:
            return 1.0
        return self.global_config.output_fps / self.global_config.original_fps
    
    def get_speed_ratio_text(self) -> str:
        """Get formatted playback speed ratio text."""
        ratio = self.get_speed_ratio()
        if ratio >= 1:
            if ratio == int(ratio):
                return f"{int(ratio)}×"
            else:
                return f"{ratio:.1f}×"
        else:
            return f"{ratio:.2f}×"
