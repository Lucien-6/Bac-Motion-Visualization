"""
Parameter panel widget.

Left side panel containing all visualization settings organized
in collapsible groups.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QGroupBox, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox,
    QSlider, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QSizePolicy
)

from ..models import VisualizationConfig, HiddenRecord
from ..core import ColorMapper

# Standard label width for form alignment
LABEL_WIDTH = 80
# Standard input widget max width (reduced by 1/3 from default)
INPUT_MAX_WIDTH = 160


def create_form_row(label_text: str, widget: QWidget) -> QHBoxLayout:
    """Create a form row with aligned label and widget."""
    layout = QHBoxLayout()
    layout.setSpacing(4)
    label = QLabel(label_text)
    label.setFixedWidth(LABEL_WIDTH)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label)
    widget.setMaximumWidth(INPUT_MAX_WIDTH)
    layout.addWidget(widget)
    layout.addStretch()
    return layout


class CollapsibleGroup(QGroupBox):
    """Collapsible group box with toggle functionality."""
    
    def __init__(self, title: str, parent=None):
        """Initialize collapsible group."""
        super().__init__(title, parent)
        
        # Style the group title: larger font and bold
        self.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                max-width: 310px;
            }
        """)
        
        self._is_collapsed = False
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.addWidget(self._content_widget)
        
        self.setCheckable(False)
    
    def content_layout(self) -> QVBoxLayout:
        """Get the content layout for adding widgets."""
        return self._content_layout


class ParameterPanel(QScrollArea):
    """
    Left panel containing all visualization parameters.
    
    Signals:
        config_changed: Emitted when any configuration value changes.
        restore_object_requested(int): Request to restore an object.
        restore_all_requested: Request to restore all objects.
    """
    
    config_changed = pyqtSignal()
    restore_object_requested = pyqtSignal(int)
    restore_all_requested = pyqtSignal()
    
    PANEL_WIDTH = 380
    
    def __init__(self, parent=None):
        """Initialize parameter panel."""
        super().__init__(parent)
        
        self._config = VisualizationConfig()
        self._updating = False
        self._original_fps: float = 1.0  # For speed ratio calculation
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the panel UI."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(self.PANEL_WIDTH)
        self.setMaximumWidth(self.PANEL_WIDTH)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        layout.addWidget(self._create_mask_group())
        layout.addWidget(self._create_contour_group())
        layout.addWidget(self._create_centroid_group())
        layout.addWidget(self._create_ellipse_axes_group())
        layout.addWidget(self._create_trajectory_group())
        layout.addWidget(self._create_time_label_group())
        layout.addWidget(self._create_scale_bar_group())
        layout.addWidget(self._create_speed_label_group())
        layout.addWidget(self._create_colorbar_group())
        layout.addWidget(self._create_object_operations_group())
        
        layout.addStretch()
        
        self.setWidget(container)
    
    def _create_mask_group(self) -> QGroupBox:
        """Create mask overlay group."""
        group = CollapsibleGroup("Mask Overlay")
        layout = group.content_layout()
        
        self._mask_enabled_check = QCheckBox("Enable")
        self._mask_enabled_check.setChecked(True)
        layout.addWidget(self._mask_enabled_check)
        
        opacity_layout = QHBoxLayout()
        opacity_layout.setSpacing(4)
        opacity_label = QLabel("Opacity:")
        opacity_label.setFixedWidth(LABEL_WIDTH)
        opacity_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        opacity_layout.addWidget(opacity_label)
        
        self._mask_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._mask_opacity_slider.setRange(0, 100)
        self._mask_opacity_slider.setValue(50)
        self._mask_opacity_slider.setMinimumWidth(150)
        opacity_layout.addWidget(self._mask_opacity_slider)
        
        self._mask_opacity_label = QLabel("50%")
        self._mask_opacity_label.setMinimumWidth(40)
        opacity_layout.addWidget(self._mask_opacity_label)
        opacity_layout.addStretch()
        
        layout.addLayout(opacity_layout)
        
        self._mask_opacity_slider.valueChanged.connect(
            lambda v: self._mask_opacity_label.setText(f"{v}%")
        )
        
        return group
    
    def _create_contour_group(self) -> QGroupBox:
        """Create object contour group."""
        group = CollapsibleGroup("Object Contour")
        layout = group.content_layout()
        
        self._contour_enabled_check = QCheckBox("Enable")
        self._contour_enabled_check.setChecked(True)
        layout.addWidget(self._contour_enabled_check)
        
        thickness_layout = QHBoxLayout()
        thickness_layout.setSpacing(4)
        thickness_label = QLabel("Thickness:")
        thickness_label.setFixedWidth(LABEL_WIDTH)
        thickness_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        thickness_layout.addWidget(thickness_label)
        self._contour_thickness_spin = QSpinBox()
        self._contour_thickness_spin.setRange(1, 99)
        self._contour_thickness_spin.setValue(2)
        self._contour_thickness_spin.setSuffix(" px")
        self._contour_thickness_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        thickness_layout.addWidget(self._contour_thickness_spin)
        thickness_layout.addStretch()
        layout.addLayout(thickness_layout)
        
        return group
    
    def _create_centroid_group(self) -> QGroupBox:
        """Create centroid marker group."""
        group = CollapsibleGroup("Centroid Marker")
        layout = group.content_layout()
        
        self._centroid_enabled_check = QCheckBox("Enable")
        layout.addWidget(self._centroid_enabled_check)
        
        shape_layout = QHBoxLayout()
        shape_layout.setSpacing(4)
        shape_label = QLabel("Shape:")
        shape_label.setFixedWidth(LABEL_WIDTH)
        shape_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        shape_layout.addWidget(shape_label)
        self._centroid_shape_combo = QComboBox()
        self._centroid_shape_combo.addItems(["Circle", "Triangle", "Star"])
        self._centroid_shape_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        shape_layout.addWidget(self._centroid_shape_combo)
        shape_layout.addStretch()
        layout.addLayout(shape_layout)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        size_label = QLabel("Size:")
        size_label.setFixedWidth(LABEL_WIDTH)
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        size_layout.addWidget(size_label)
        self._centroid_size_spin = QSpinBox()
        self._centroid_size_spin.setRange(1, 50)
        self._centroid_size_spin.setValue(5)
        self._centroid_size_spin.setSuffix(" px")
        self._centroid_size_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        size_layout.addWidget(self._centroid_size_spin)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        return group
    
    def _create_ellipse_axes_group(self) -> QGroupBox:
        """Create ellipse axes group."""
        group = CollapsibleGroup("Ellipse Axes")
        layout = group.content_layout()
        
        # Major axis settings
        layout.addWidget(QLabel("Major Axis:"))
        self._ellipse_major_check = QCheckBox("Show Major Axis")
        layout.addWidget(self._ellipse_major_check)
        
        major_thickness_layout = QHBoxLayout()
        major_thickness_layout.setSpacing(4)
        major_thickness_label = QLabel("Thickness:")
        major_thickness_label.setFixedWidth(LABEL_WIDTH)
        major_thickness_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        major_thickness_layout.addWidget(major_thickness_label)
        self._ellipse_major_thickness_spin = QSpinBox()
        self._ellipse_major_thickness_spin.setRange(1, 99)
        self._ellipse_major_thickness_spin.setValue(1)
        self._ellipse_major_thickness_spin.setSuffix(" px")
        self._ellipse_major_thickness_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        major_thickness_layout.addWidget(self._ellipse_major_thickness_spin)
        major_thickness_layout.addStretch()
        layout.addLayout(major_thickness_layout)
        
        major_color_layout = QHBoxLayout()
        major_color_layout.setSpacing(4)
        major_color_label = QLabel("Color:")
        major_color_label.setFixedWidth(LABEL_WIDTH)
        major_color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        major_color_layout.addWidget(major_color_label)
        self._ellipse_major_color_combo = QComboBox()
        self._ellipse_major_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._ellipse_major_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        major_color_layout.addWidget(self._ellipse_major_color_combo)
        major_color_layout.addStretch()
        layout.addLayout(major_color_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Minor axis settings
        layout.addWidget(QLabel("Minor Axis:"))
        self._ellipse_minor_check = QCheckBox("Show Minor Axis")
        layout.addWidget(self._ellipse_minor_check)
        
        minor_thickness_layout = QHBoxLayout()
        minor_thickness_layout.setSpacing(4)
        minor_thickness_label = QLabel("Thickness:")
        minor_thickness_label.setFixedWidth(LABEL_WIDTH)
        minor_thickness_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        minor_thickness_layout.addWidget(minor_thickness_label)
        self._ellipse_minor_thickness_spin = QSpinBox()
        self._ellipse_minor_thickness_spin.setRange(1, 99)
        self._ellipse_minor_thickness_spin.setValue(1)
        self._ellipse_minor_thickness_spin.setSuffix(" px")
        self._ellipse_minor_thickness_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        minor_thickness_layout.addWidget(self._ellipse_minor_thickness_spin)
        minor_thickness_layout.addStretch()
        layout.addLayout(minor_thickness_layout)
        
        minor_color_layout = QHBoxLayout()
        minor_color_layout.setSpacing(4)
        minor_color_label = QLabel("Color:")
        minor_color_label.setFixedWidth(LABEL_WIDTH)
        minor_color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        minor_color_layout.addWidget(minor_color_label)
        self._ellipse_minor_color_combo = QComboBox()
        self._ellipse_minor_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._ellipse_minor_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        minor_color_layout.addWidget(self._ellipse_minor_color_combo)
        minor_color_layout.addStretch()
        layout.addLayout(minor_color_layout)
        
        return group
    
    def _create_trajectory_group(self) -> QGroupBox:
        """Create trajectory group."""
        group = CollapsibleGroup("Trajectory")
        layout = group.content_layout()
        
        self._traj_enabled_check = QCheckBox("Enable")
        self._traj_enabled_check.setChecked(True)
        layout.addWidget(self._traj_enabled_check)
        
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(4)
        mode_label = QLabel("Mode:")
        mode_label.setFixedWidth(LABEL_WIDTH)
        mode_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        mode_layout.addWidget(mode_label)
        self._traj_mode_combo = QComboBox()
        self._traj_mode_combo.addItems([
            "Full Trajectory",
            "Start to Current",
            "Delay Before",
            "Delay After"
        ])
        self._traj_mode_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        mode_layout.addWidget(self._traj_mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        delay_layout = QHBoxLayout()
        delay_layout.setSpacing(4)
        delay_label = QLabel("Delay Time:")
        delay_label.setFixedWidth(LABEL_WIDTH)
        delay_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        delay_layout.addWidget(delay_label)
        self._traj_delay_spin = QDoubleSpinBox()
        self._traj_delay_spin.setRange(0.1, 100)
        self._traj_delay_spin.setValue(1.0)
        self._traj_delay_spin.setSuffix(" s")
        self._traj_delay_spin.setDecimals(1)
        self._traj_delay_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        delay_layout.addWidget(self._traj_delay_spin)
        delay_layout.addStretch()
        layout.addLayout(delay_layout)
        
        thickness_layout = QHBoxLayout()
        thickness_layout.setSpacing(4)
        thickness_label = QLabel("Thickness:")
        thickness_label.setFixedWidth(LABEL_WIDTH)
        thickness_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        thickness_layout.addWidget(thickness_label)
        self._traj_thickness_spin = QSpinBox()
        self._traj_thickness_spin.setRange(1, 99)
        self._traj_thickness_spin.setValue(1)
        self._traj_thickness_spin.setSuffix(" px")
        self._traj_thickness_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        thickness_layout.addWidget(self._traj_thickness_spin)
        thickness_layout.addStretch()
        layout.addLayout(thickness_layout)
        
        color_mode_layout = QHBoxLayout()
        color_mode_layout.setSpacing(4)
        color_mode_label = QLabel("Color Mode:")
        color_mode_label.setFixedWidth(LABEL_WIDTH)
        color_mode_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        color_mode_layout.addWidget(color_mode_label)
        self._traj_color_mode_combo = QComboBox()
        self._traj_color_mode_combo.addItems(["Object Color", "Velocity Color"])
        self._traj_color_mode_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        color_mode_layout.addWidget(self._traj_color_mode_combo)
        color_mode_layout.addStretch()
        layout.addLayout(color_mode_layout)
        
        return group
    
    def _create_time_label_group(self) -> QGroupBox:
        """Create time label group."""
        group = CollapsibleGroup("Time Label")
        layout = group.content_layout()
        
        self._time_enabled_check = QCheckBox("Enable")
        self._time_enabled_check.setChecked(True)
        layout.addWidget(self._time_enabled_check)
        
        unit_layout = QHBoxLayout()
        unit_layout.setSpacing(4)
        unit_label = QLabel("Unit:")
        unit_label.setFixedWidth(LABEL_WIDTH)
        unit_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        unit_layout.addWidget(unit_label)
        self._time_unit_combo = QComboBox()
        self._time_unit_combo.addItems(["ms", "s", "min", "h"])
        self._time_unit_combo.setCurrentText("s")
        self._time_unit_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        unit_layout.addWidget(self._time_unit_combo)
        unit_layout.addStretch()
        layout.addLayout(unit_layout)
        
        font_layout = QHBoxLayout()
        font_layout.setSpacing(4)
        font_label = QLabel("Font:")
        font_label.setFixedWidth(LABEL_WIDTH)
        font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font_layout.addWidget(font_label)
        self._time_font_combo = QComboBox()
        self._time_font_combo.addItems(["Arial", "Times New Roman"])
        self._time_font_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        font_layout.addWidget(self._time_font_combo)
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        size_label = QLabel("Size:")
        size_label.setFixedWidth(LABEL_WIDTH)
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        size_layout.addWidget(size_label)
        self._time_size_spin = QSpinBox()
        self._time_size_spin.setRange(8, 99)
        self._time_size_spin.setValue(24)
        self._time_size_spin.setSuffix(" pt")
        self._time_size_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        size_layout.addWidget(self._time_size_spin)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        bold_layout = QHBoxLayout()
        bold_layout.setSpacing(4)
        bold_label = QLabel("")
        bold_label.setFixedWidth(LABEL_WIDTH)
        bold_layout.addWidget(bold_label)
        self._time_bold_check = QCheckBox("Bold")
        self._time_bold_check.setMaximumWidth(INPUT_MAX_WIDTH)
        bold_layout.addWidget(self._time_bold_check)
        bold_layout.addStretch()
        layout.addLayout(bold_layout)
        
        color_layout = QHBoxLayout()
        color_layout.setSpacing(4)
        color_label = QLabel("Color:")
        color_label.setFixedWidth(LABEL_WIDTH)
        color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        color_layout.addWidget(color_label)
        self._time_color_combo = QComboBox()
        self._time_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._time_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        color_layout.addWidget(self._time_color_combo)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        return group
    
    def _create_scale_bar_group(self) -> QGroupBox:
        """Create scale bar group."""
        group = CollapsibleGroup("Scale Bar")
        layout = group.content_layout()
        
        self._scale_enabled_check = QCheckBox("Enable")
        self._scale_enabled_check.setChecked(True)
        layout.addWidget(self._scale_enabled_check)
        
        thickness_layout = QHBoxLayout()
        thickness_layout.setSpacing(4)
        thickness_label = QLabel("Thickness:")
        thickness_label.setFixedWidth(LABEL_WIDTH)
        thickness_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        thickness_layout.addWidget(thickness_label)
        self._scale_thickness_spin = QSpinBox()
        self._scale_thickness_spin.setRange(1, 99)
        self._scale_thickness_spin.setValue(3)
        self._scale_thickness_spin.setSuffix(" px")
        self._scale_thickness_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        thickness_layout.addWidget(self._scale_thickness_spin)
        thickness_layout.addStretch()
        layout.addLayout(thickness_layout)
        
        length_layout = QHBoxLayout()
        length_layout.setSpacing(4)
        length_label = QLabel("Length:")
        length_label.setFixedWidth(LABEL_WIDTH)
        length_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        length_layout.addWidget(length_label)
        self._scale_length_spin = QDoubleSpinBox()
        self._scale_length_spin.setRange(1, 10000)
        self._scale_length_spin.setValue(50)
        self._scale_length_spin.setSuffix(" μm")
        self._scale_length_spin.setDecimals(1)
        self._scale_length_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        length_layout.addWidget(self._scale_length_spin)
        length_layout.addStretch()
        layout.addLayout(length_layout)
        
        bar_color_layout = QHBoxLayout()
        bar_color_layout.setSpacing(4)
        bar_color_label = QLabel("Bar Color:")
        bar_color_label.setFixedWidth(LABEL_WIDTH)
        bar_color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bar_color_layout.addWidget(bar_color_label)
        self._scale_bar_color_combo = QComboBox()
        self._scale_bar_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._scale_bar_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        bar_color_layout.addWidget(self._scale_bar_color_combo)
        bar_color_layout.addStretch()
        layout.addLayout(bar_color_layout)
        
        self._scale_text_check = QCheckBox("Show Text")
        self._scale_text_check.setChecked(True)
        layout.addWidget(self._scale_text_check)
        
        pos_layout = QHBoxLayout()
        pos_layout.setSpacing(4)
        pos_label = QLabel("Text Position:")
        pos_label.setFixedWidth(LABEL_WIDTH)
        pos_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pos_layout.addWidget(pos_label)
        self._scale_text_pos_combo = QComboBox()
        self._scale_text_pos_combo.addItems(["Above", "Below"])
        self._scale_text_pos_combo.setCurrentText("Below")
        self._scale_text_pos_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        pos_layout.addWidget(self._scale_text_pos_combo)
        pos_layout.addStretch()
        layout.addLayout(pos_layout)
        
        gap_layout = QHBoxLayout()
        gap_layout.setSpacing(4)
        gap_label = QLabel("Text Gap:")
        gap_label.setFixedWidth(LABEL_WIDTH)
        gap_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        gap_layout.addWidget(gap_label)
        self._scale_text_gap_spin = QSpinBox()
        self._scale_text_gap_spin.setRange(0, 99)
        self._scale_text_gap_spin.setValue(5)
        self._scale_text_gap_spin.setSuffix(" px")
        self._scale_text_gap_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        gap_layout.addWidget(self._scale_text_gap_spin)
        gap_layout.addStretch()
        layout.addLayout(gap_layout)
        
        font_layout = QHBoxLayout()
        font_layout.setSpacing(4)
        font_label = QLabel("Font:")
        font_label.setFixedWidth(LABEL_WIDTH)
        font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font_layout.addWidget(font_label)
        self._scale_font_combo = QComboBox()
        self._scale_font_combo.addItems(["Arial", "Times New Roman"])
        self._scale_font_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        font_layout.addWidget(self._scale_font_combo)
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        size_label = QLabel("Size:")
        size_label.setFixedWidth(LABEL_WIDTH)
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        size_layout.addWidget(size_label)
        self._scale_size_spin = QSpinBox()
        self._scale_size_spin.setRange(8, 99)
        self._scale_size_spin.setValue(18)
        self._scale_size_spin.setSuffix(" pt")
        self._scale_size_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        size_layout.addWidget(self._scale_size_spin)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        bold_layout = QHBoxLayout()
        bold_layout.setSpacing(4)
        bold_label = QLabel("")
        bold_label.setFixedWidth(LABEL_WIDTH)
        bold_layout.addWidget(bold_label)
        self._scale_bold_check = QCheckBox("Bold")
        self._scale_bold_check.setMaximumWidth(INPUT_MAX_WIDTH)
        bold_layout.addWidget(self._scale_bold_check)
        bold_layout.addStretch()
        layout.addLayout(bold_layout)
        
        text_color_layout = QHBoxLayout()
        text_color_layout.setSpacing(4)
        text_color_label = QLabel("Text Color:")
        text_color_label.setFixedWidth(LABEL_WIDTH)
        text_color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        text_color_layout.addWidget(text_color_label)
        self._scale_text_color_combo = QComboBox()
        self._scale_text_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._scale_text_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        text_color_layout.addWidget(self._scale_text_color_combo)
        text_color_layout.addStretch()
        layout.addLayout(text_color_layout)
        
        return group
    
    def _create_speed_label_group(self) -> QGroupBox:
        """Create speed label group."""
        group = CollapsibleGroup("Speed Label")
        layout = group.content_layout()
        
        self._speed_enabled_check = QCheckBox("Enable")
        self._speed_enabled_check.setChecked(True)
        layout.addWidget(self._speed_enabled_check)
        
        # Output FPS setting (for speed ratio calculation)
        fps_layout = QHBoxLayout()
        fps_layout.setSpacing(4)
        fps_label = QLabel("Output FPS:")
        fps_label.setFixedWidth(LABEL_WIDTH)
        fps_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        fps_layout.addWidget(fps_label)
        self._output_fps_spin = QDoubleSpinBox()
        self._output_fps_spin.setRange(0.1, 1000)
        self._output_fps_spin.setValue(30.0)
        self._output_fps_spin.setDecimals(1)
        self._output_fps_spin.setSuffix(" fps")
        self._output_fps_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        self._output_fps_spin.valueChanged.connect(self._update_speed_ratio)
        fps_layout.addWidget(self._output_fps_spin)
        fps_layout.addStretch()
        layout.addLayout(fps_layout)
        
        # Speed ratio display (auto-calculated)
        ratio_layout = QHBoxLayout()
        ratio_layout.setSpacing(4)
        ratio_label = QLabel("Speed Ratio:")
        ratio_label.setFixedWidth(LABEL_WIDTH)
        ratio_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ratio_layout.addWidget(ratio_label)
        self._speed_ratio_label = QLabel("30.0×")
        self._speed_ratio_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        self._speed_ratio_label.setMaximumWidth(INPUT_MAX_WIDTH)
        ratio_layout.addWidget(self._speed_ratio_label)
        ratio_layout.addStretch()
        layout.addLayout(ratio_layout)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)
        
        font_layout = QHBoxLayout()
        font_layout.setSpacing(4)
        font_label = QLabel("Font:")
        font_label.setFixedWidth(LABEL_WIDTH)
        font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font_layout.addWidget(font_label)
        self._speed_font_combo = QComboBox()
        self._speed_font_combo.addItems(["Arial", "Times New Roman"])
        self._speed_font_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        font_layout.addWidget(self._speed_font_combo)
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        size_layout = QHBoxLayout()
        size_layout.setSpacing(4)
        size_label = QLabel("Size:")
        size_label.setFixedWidth(LABEL_WIDTH)
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        size_layout.addWidget(size_label)
        self._speed_size_spin = QSpinBox()
        self._speed_size_spin.setRange(8, 99)
        self._speed_size_spin.setValue(20)
        self._speed_size_spin.setSuffix(" pt")
        self._speed_size_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        size_layout.addWidget(self._speed_size_spin)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        bold_layout = QHBoxLayout()
        bold_layout.setSpacing(4)
        bold_label = QLabel("")
        bold_label.setFixedWidth(LABEL_WIDTH)
        bold_layout.addWidget(bold_label)
        self._speed_bold_check = QCheckBox("Bold")
        self._speed_bold_check.setMaximumWidth(INPUT_MAX_WIDTH)
        bold_layout.addWidget(self._speed_bold_check)
        bold_layout.addStretch()
        layout.addLayout(bold_layout)
        
        color_layout = QHBoxLayout()
        color_layout.setSpacing(4)
        color_label = QLabel("Color:")
        color_label.setFixedWidth(LABEL_WIDTH)
        color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        color_layout.addWidget(color_label)
        self._speed_color_combo = QComboBox()
        self._speed_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._speed_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        color_layout.addWidget(self._speed_color_combo)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        return group
    
    def _update_speed_ratio(self):
        """Update speed ratio display based on output and original FPS."""
        if self._original_fps <= 0:
            self._speed_ratio_label.setText("N/A")
            return
        
        ratio = self._output_fps_spin.value() / self._original_fps
        if ratio >= 1:
            if ratio == int(ratio):
                text = f"{int(ratio)}×"
            else:
                text = f"{ratio:.1f}×"
        else:
            text = f"{ratio:.2f}×"
        
        self._speed_ratio_label.setText(text)
    
    def _create_colorbar_group(self) -> QGroupBox:
        """Create colorbar group."""
        group = CollapsibleGroup("Colorbar (Velocity Mode)")
        layout = group.content_layout()
        
        self._colorbar_enabled_check = QCheckBox("Enable")
        self._colorbar_enabled_check.setChecked(True)
        layout.addWidget(self._colorbar_enabled_check)
        
        cmap_layout = QHBoxLayout()
        cmap_layout.setSpacing(4)
        cmap_label = QLabel("Colormap:")
        cmap_label.setFixedWidth(LABEL_WIDTH)
        cmap_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        cmap_layout.addWidget(cmap_label)
        self._colorbar_cmap_combo = QComboBox()
        self._colorbar_cmap_combo.addItems(ColorMapper.get_available_colormaps())
        self._colorbar_cmap_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        cmap_layout.addWidget(self._colorbar_cmap_combo)
        cmap_layout.addStretch()
        layout.addLayout(cmap_layout)
        
        height_layout = QHBoxLayout()
        height_layout.setSpacing(4)
        height_label = QLabel("Height:")
        height_label.setFixedWidth(LABEL_WIDTH)
        height_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        height_layout.addWidget(height_label)
        self._colorbar_height_spin = QSpinBox()
        self._colorbar_height_spin.setRange(50, 2000)
        self._colorbar_height_spin.setValue(200)
        self._colorbar_height_spin.setSuffix(" px")
        self._colorbar_height_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        height_layout.addWidget(self._colorbar_height_spin)
        height_layout.addStretch()
        layout.addLayout(height_layout)
        
        width_layout = QHBoxLayout()
        width_layout.setSpacing(4)
        width_label = QLabel("Width:")
        width_label.setFixedWidth(LABEL_WIDTH)
        width_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        width_layout.addWidget(width_label)
        self._colorbar_width_spin = QSpinBox()
        self._colorbar_width_spin.setRange(5, 200)
        self._colorbar_width_spin.setValue(14)
        self._colorbar_width_spin.setSuffix(" px")
        self._colorbar_width_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        width_layout.addWidget(self._colorbar_width_spin)
        width_layout.addStretch()
        layout.addLayout(width_layout)
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(4)
        title_label = QLabel("Title:")
        title_label.setFixedWidth(LABEL_WIDTH)
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_layout.addWidget(title_label)
        self._colorbar_title_edit = QLineEdit("Speed (μm/s)")
        self._colorbar_title_edit.setMaximumWidth(INPUT_MAX_WIDTH)
        title_layout.addWidget(self._colorbar_title_edit)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        title_pos_layout = QHBoxLayout()
        title_pos_layout.setSpacing(4)
        title_pos_label = QLabel("Title Position:")
        title_pos_label.setFixedWidth(LABEL_WIDTH)
        title_pos_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_pos_layout.addWidget(title_pos_label)
        self._colorbar_title_pos_combo = QComboBox()
        self._colorbar_title_pos_combo.addItems(["Top", "Right"])
        self._colorbar_title_pos_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        title_pos_layout.addWidget(self._colorbar_title_pos_combo)
        title_pos_layout.addStretch()
        layout.addLayout(title_pos_layout)
        
        title_gap_layout = QHBoxLayout()
        title_gap_layout.setSpacing(4)
        title_gap_label = QLabel("Title Gap:")
        title_gap_label.setFixedWidth(LABEL_WIDTH)
        title_gap_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_gap_layout.addWidget(title_gap_label)
        self._colorbar_title_gap_spin = QSpinBox()
        self._colorbar_title_gap_spin.setRange(0, 99)
        self._colorbar_title_gap_spin.setValue(5)
        self._colorbar_title_gap_spin.setSuffix(" px")
        self._colorbar_title_gap_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        title_gap_layout.addWidget(self._colorbar_title_gap_spin)
        title_gap_layout.addStretch()
        layout.addLayout(title_gap_layout)
        
        title_font_layout = QHBoxLayout()
        title_font_layout.setSpacing(4)
        title_font_label = QLabel("Title Font:")
        title_font_label.setFixedWidth(LABEL_WIDTH)
        title_font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_font_layout.addWidget(title_font_label)
        self._colorbar_title_font_combo = QComboBox()
        self._colorbar_title_font_combo.addItems(["Arial", "Times New Roman"])
        self._colorbar_title_font_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        title_font_layout.addWidget(self._colorbar_title_font_combo)
        title_font_layout.addStretch()
        layout.addLayout(title_font_layout)
        
        title_size_layout = QHBoxLayout()
        title_size_layout.setSpacing(4)
        title_size_label = QLabel("Title Size:")
        title_size_label.setFixedWidth(LABEL_WIDTH)
        title_size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_size_layout.addWidget(title_size_label)
        self._colorbar_title_size_spin = QSpinBox()
        self._colorbar_title_size_spin.setRange(8, 99)
        self._colorbar_title_size_spin.setValue(14)
        self._colorbar_title_size_spin.setSuffix(" pt")
        self._colorbar_title_size_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        title_size_layout.addWidget(self._colorbar_title_size_spin)
        title_size_layout.addStretch()
        layout.addLayout(title_size_layout)
        
        title_style_layout = QHBoxLayout()
        title_style_layout.setSpacing(4)
        title_bold_label = QLabel("")
        title_bold_label.setFixedWidth(LABEL_WIDTH)
        title_style_layout.addWidget(title_bold_label)
        self._colorbar_title_bold_check = QCheckBox("Title Bold")
        self._colorbar_title_bold_check.setMaximumWidth(INPUT_MAX_WIDTH)
        title_style_layout.addWidget(self._colorbar_title_bold_check)
        title_style_layout.addStretch()
        layout.addLayout(title_style_layout)
        
        title_color_layout = QHBoxLayout()
        title_color_layout.setSpacing(4)
        title_color_label = QLabel("Title Color:")
        title_color_label.setFixedWidth(LABEL_WIDTH)
        title_color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_color_layout.addWidget(title_color_label)
        self._colorbar_title_color_combo = QComboBox()
        self._colorbar_title_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._colorbar_title_color_combo.setCurrentText("black")
        self._colorbar_title_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        title_color_layout.addWidget(self._colorbar_title_color_combo)
        title_color_layout.addStretch()
        layout.addLayout(title_color_layout)
        
        min_layout = QHBoxLayout()
        min_layout.setSpacing(4)
        min_label = QLabel("Min:")
        min_label.setFixedWidth(LABEL_WIDTH)
        min_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        min_layout.addWidget(min_label)
        self._colorbar_min_spin = QDoubleSpinBox()
        self._colorbar_min_spin.setRange(0, 100000)
        self._colorbar_min_spin.setValue(0)
        self._colorbar_min_spin.setDecimals(2)
        self._colorbar_min_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        min_layout.addWidget(self._colorbar_min_spin)
        min_layout.addStretch()
        layout.addLayout(min_layout)
        
        max_layout = QHBoxLayout()
        max_layout.setSpacing(4)
        max_label = QLabel("Max:")
        max_label.setFixedWidth(LABEL_WIDTH)
        max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        max_layout.addWidget(max_label)
        self._colorbar_max_spin = QDoubleSpinBox()
        self._colorbar_max_spin.setRange(0, 100000)
        self._colorbar_max_spin.setValue(100)
        self._colorbar_max_spin.setDecimals(2)
        self._colorbar_max_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        max_layout.addWidget(self._colorbar_max_spin)
        max_layout.addStretch()
        layout.addLayout(max_layout)
        
        tick_layout = QHBoxLayout()
        tick_layout.setSpacing(4)
        tick_label = QLabel("Tick Interval:")
        tick_label.setFixedWidth(LABEL_WIDTH)
        tick_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tick_layout.addWidget(tick_label)
        self._colorbar_tick_spin = QDoubleSpinBox()
        self._colorbar_tick_spin.setRange(0.01, 10000)
        self._colorbar_tick_spin.setValue(20)
        self._colorbar_tick_spin.setDecimals(2)
        self._colorbar_tick_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        tick_layout.addWidget(self._colorbar_tick_spin)
        tick_layout.addStretch()
        layout.addLayout(tick_layout)
        
        tick_font_layout = QHBoxLayout()
        tick_font_layout.setSpacing(4)
        tick_font_label = QLabel("Tick Font:")
        tick_font_label.setFixedWidth(LABEL_WIDTH)
        tick_font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tick_font_layout.addWidget(tick_font_label)
        self._colorbar_tick_font_combo = QComboBox()
        self._colorbar_tick_font_combo.addItems(["Arial", "Times New Roman"])
        self._colorbar_tick_font_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        tick_font_layout.addWidget(self._colorbar_tick_font_combo)
        tick_font_layout.addStretch()
        layout.addLayout(tick_font_layout)
        
        tick_size_layout = QHBoxLayout()
        tick_size_layout.setSpacing(4)
        tick_size_label = QLabel("Tick Size:")
        tick_size_label.setFixedWidth(LABEL_WIDTH)
        tick_size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tick_size_layout.addWidget(tick_size_label)
        self._colorbar_tick_size_spin = QSpinBox()
        self._colorbar_tick_size_spin.setRange(8, 99)
        self._colorbar_tick_size_spin.setValue(12)
        self._colorbar_tick_size_spin.setSuffix(" pt")
        self._colorbar_tick_size_spin.setMaximumWidth(INPUT_MAX_WIDTH)
        tick_size_layout.addWidget(self._colorbar_tick_size_spin)
        tick_size_layout.addStretch()
        layout.addLayout(tick_size_layout)
        
        tick_style_layout = QHBoxLayout()
        tick_style_layout.setSpacing(4)
        tick_bold_label = QLabel("")
        tick_bold_label.setFixedWidth(LABEL_WIDTH)
        tick_style_layout.addWidget(tick_bold_label)
        self._colorbar_tick_bold_check = QCheckBox("Tick Bold")
        self._colorbar_tick_bold_check.setMaximumWidth(INPUT_MAX_WIDTH)
        tick_style_layout.addWidget(self._colorbar_tick_bold_check)
        tick_style_layout.addStretch()
        layout.addLayout(tick_style_layout)
        
        tick_color_layout = QHBoxLayout()
        tick_color_layout.setSpacing(4)
        tick_color_label = QLabel("Tick Color:")
        tick_color_label.setFixedWidth(LABEL_WIDTH)
        tick_color_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tick_color_layout.addWidget(tick_color_label)
        self._colorbar_tick_color_combo = QComboBox()
        self._colorbar_tick_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        self._colorbar_tick_color_combo.setCurrentText("black")
        self._colorbar_tick_color_combo.setMaximumWidth(INPUT_MAX_WIDTH)
        tick_color_layout.addWidget(self._colorbar_tick_color_combo)
        tick_color_layout.addStretch()
        layout.addLayout(tick_color_layout)
        
        return group
    
    def _create_object_operations_group(self) -> QGroupBox:
        """Create object operations group."""
        group = CollapsibleGroup("Object Operations")
        layout = group.content_layout()
        
        info_label = QLabel("Double-click objects in preview to hide them.")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self._object_list = QListWidget()
        self._object_list.setMaximumHeight(150)
        self._object_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self._object_list)
        
        btn_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._on_remove_selected)
        btn_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_all)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def _connect_signals(self):
        """Connect all widget signals to config_changed."""
        spin_boxes = [
            self._contour_thickness_spin, self._centroid_size_spin,
            self._ellipse_major_thickness_spin, self._ellipse_minor_thickness_spin,
            self._traj_delay_spin, self._traj_thickness_spin,
            self._time_size_spin, self._scale_thickness_spin, self._scale_length_spin,
            self._scale_text_gap_spin, self._scale_size_spin, self._speed_size_spin,
            self._colorbar_height_spin, self._colorbar_width_spin, self._colorbar_title_gap_spin,
            self._colorbar_title_size_spin, self._colorbar_tick_size_spin,
            self._colorbar_min_spin, self._colorbar_max_spin, self._colorbar_tick_spin,
            self._output_fps_spin,
        ]
        
        check_boxes = [
            self._mask_enabled_check, self._contour_enabled_check, self._centroid_enabled_check,
            self._ellipse_major_check, self._ellipse_minor_check,
            self._traj_enabled_check, self._time_enabled_check, self._time_bold_check,
            self._scale_enabled_check, self._scale_text_check, self._scale_bold_check,
            self._speed_enabled_check, self._speed_bold_check,
            self._colorbar_enabled_check, self._colorbar_title_bold_check,
            self._colorbar_tick_bold_check,
        ]
        
        combo_boxes = [
            self._centroid_shape_combo, self._ellipse_major_color_combo, self._ellipse_minor_color_combo,
            self._traj_mode_combo, self._traj_color_mode_combo,
            self._time_unit_combo, self._time_font_combo,
            self._time_color_combo, self._scale_bar_color_combo, self._scale_text_pos_combo,
            self._scale_font_combo, self._scale_text_color_combo,
            self._speed_font_combo, self._speed_color_combo,
            self._colorbar_cmap_combo, self._colorbar_title_pos_combo,
            self._colorbar_title_font_combo, self._colorbar_title_color_combo,
            self._colorbar_tick_font_combo, self._colorbar_tick_color_combo,
        ]
        
        line_edits = [self._colorbar_title_edit]
        
        for widget in spin_boxes:
            widget.editingFinished.connect(self._emit_config_changed)
        
        for widget in check_boxes:
            widget.toggled.connect(self._emit_config_changed)
        
        for widget in combo_boxes:
            widget.currentTextChanged.connect(self._emit_config_changed)
        
        self._mask_opacity_slider.valueChanged.connect(self._emit_config_changed)
        
        for widget in line_edits:
            widget.editingFinished.connect(self._emit_config_changed)
    
    def _emit_config_changed(self):
        """Emit config_changed signal if not updating."""
        if not self._updating:
            self.config_changed.emit()
    
    def _on_remove_selected(self):
        """Remove selected items from object list."""
        for item in self._object_list.selectedItems():
            obj_id = item.data(Qt.ItemDataRole.UserRole)
            self.restore_object_requested.emit(obj_id)
    
    def _on_clear_all(self):
        """Clear all items from object list."""
        self.restore_all_requested.emit()
    
    def get_config(self) -> VisualizationConfig:
        """Get current configuration from UI values."""
        config = VisualizationConfig()
        
        # output_fps is managed here; original_fps and um_per_pixel by DataLoadDialog
        config.global_config.output_fps = self._output_fps_spin.value()
        
        config.mask.enabled = self._mask_enabled_check.isChecked()
        config.mask.opacity = self._mask_opacity_slider.value() / 100.0
        
        config.contour.enabled = self._contour_enabled_check.isChecked()
        config.contour.thickness = self._contour_thickness_spin.value()
        
        config.centroid.enabled = self._centroid_enabled_check.isChecked()
        shape_map = {"Circle": "circle", "Triangle": "triangle", "Star": "star"}
        config.centroid.marker_shape = shape_map.get(
            self._centroid_shape_combo.currentText(), "circle"
        )
        config.centroid.marker_size = self._centroid_size_spin.value()
        
        config.ellipse_axes.show_major_axis = self._ellipse_major_check.isChecked()
        config.ellipse_axes.show_minor_axis = self._ellipse_minor_check.isChecked()
        config.ellipse_axes.major_thickness = self._ellipse_major_thickness_spin.value()
        config.ellipse_axes.major_color = self._ellipse_major_color_combo.currentText()
        config.ellipse_axes.minor_thickness = self._ellipse_minor_thickness_spin.value()
        config.ellipse_axes.minor_color = self._ellipse_minor_color_combo.currentText()
        
        config.trajectory.enabled = self._traj_enabled_check.isChecked()
        mode_map = {
            "Full Trajectory": "full",
            "Start to Current": "start_to_current",
            "Delay Before": "delay_before",
            "Delay After": "delay_after",
        }
        config.trajectory.mode = mode_map.get(
            self._traj_mode_combo.currentText(), "full"
        )
        config.trajectory.delay_time = self._traj_delay_spin.value()
        config.trajectory.thickness = self._traj_thickness_spin.value()
        config.trajectory.color_mode = "velocity" if self._traj_color_mode_combo.currentIndex() == 1 else "object"
        
        config.time_label.enabled = self._time_enabled_check.isChecked()
        config.time_label.unit = self._time_unit_combo.currentText()
        config.time_label.font_family = self._time_font_combo.currentText()
        config.time_label.font_size = self._time_size_spin.value()
        config.time_label.font_bold = self._time_bold_check.isChecked()
        config.time_label.color = self._time_color_combo.currentText()
        
        config.scale_bar.enabled = self._scale_enabled_check.isChecked()
        config.scale_bar.thickness = self._scale_thickness_spin.value()
        config.scale_bar.length_um = self._scale_length_spin.value()
        config.scale_bar.bar_color = self._scale_bar_color_combo.currentText()
        config.scale_bar.text_enabled = self._scale_text_check.isChecked()
        config.scale_bar.text_position = self._scale_text_pos_combo.currentText().lower()
        config.scale_bar.text_gap = self._scale_text_gap_spin.value()
        config.scale_bar.font_family = self._scale_font_combo.currentText()
        config.scale_bar.font_size = self._scale_size_spin.value()
        config.scale_bar.font_bold = self._scale_bold_check.isChecked()
        config.scale_bar.text_color = self._scale_text_color_combo.currentText()
        
        config.speed_label.enabled = self._speed_enabled_check.isChecked()
        config.speed_label.font_family = self._speed_font_combo.currentText()
        config.speed_label.font_size = self._speed_size_spin.value()
        config.speed_label.font_bold = self._speed_bold_check.isChecked()
        config.speed_label.color = self._speed_color_combo.currentText()
        
        config.colorbar.enabled = self._colorbar_enabled_check.isChecked()
        config.colorbar.colormap = self._colorbar_cmap_combo.currentText()
        config.colorbar.bar_height = self._colorbar_height_spin.value()
        config.colorbar.bar_width = self._colorbar_width_spin.value()
        config.colorbar.title = self._colorbar_title_edit.text()
        config.colorbar.title_position = self._colorbar_title_pos_combo.currentText().lower()
        config.colorbar.title_gap = self._colorbar_title_gap_spin.value()
        config.colorbar.title_font_family = self._colorbar_title_font_combo.currentText()
        config.colorbar.title_font_size = self._colorbar_title_size_spin.value()
        config.colorbar.title_font_bold = self._colorbar_title_bold_check.isChecked()
        config.colorbar.title_color = self._colorbar_title_color_combo.currentText()
        config.colorbar.vmin = self._colorbar_min_spin.value()
        config.colorbar.vmax = self._colorbar_max_spin.value()
        config.colorbar.tick_interval = self._colorbar_tick_spin.value()
        config.colorbar.tick_font_family = self._colorbar_tick_font_combo.currentText()
        config.colorbar.tick_font_size = self._colorbar_tick_size_spin.value()
        config.colorbar.tick_font_bold = self._colorbar_tick_bold_check.isChecked()
        config.colorbar.tick_color = self._colorbar_tick_color_combo.currentText()
        
        return config
    
    def set_config(self, config: VisualizationConfig):
        """Set UI values from configuration."""
        self._updating = True
        
        try:
            # Set output_fps and original_fps for speed ratio calculation
            self._original_fps = config.global_config.original_fps
            self._output_fps_spin.setValue(config.global_config.output_fps)
            self._update_speed_ratio()
            
            self._mask_enabled_check.setChecked(config.mask.enabled)
            self._mask_opacity_slider.setValue(int(config.mask.opacity * 100))
            
            self._contour_enabled_check.setChecked(config.contour.enabled)
            self._contour_thickness_spin.setValue(config.contour.thickness)
            
            self._centroid_enabled_check.setChecked(config.centroid.enabled)
            shape_map = {"circle": "Circle", "triangle": "Triangle", "star": "Star"}
            self._centroid_shape_combo.setCurrentText(
                shape_map.get(config.centroid.marker_shape, "Circle")
            )
            self._centroid_size_spin.setValue(config.centroid.marker_size)
            
            self._ellipse_major_check.setChecked(config.ellipse_axes.show_major_axis)
            self._ellipse_minor_check.setChecked(config.ellipse_axes.show_minor_axis)
            self._ellipse_major_thickness_spin.setValue(config.ellipse_axes.major_thickness)
            self._ellipse_major_color_combo.setCurrentText(config.ellipse_axes.major_color)
            self._ellipse_minor_thickness_spin.setValue(config.ellipse_axes.minor_thickness)
            self._ellipse_minor_color_combo.setCurrentText(config.ellipse_axes.minor_color)
            
            self._traj_enabled_check.setChecked(config.trajectory.enabled)
            mode_map = {
                "full": "Full Trajectory",
                "start_to_current": "Start to Current",
                "delay_before": "Delay Before",
                "delay_after": "Delay After",
            }
            self._traj_mode_combo.setCurrentText(
                mode_map.get(config.trajectory.mode, "Full Trajectory")
            )
            self._traj_delay_spin.setValue(config.trajectory.delay_time)
            self._traj_thickness_spin.setValue(config.trajectory.thickness)
            self._traj_color_mode_combo.setCurrentIndex(
                1 if config.trajectory.color_mode == "velocity" else 0
            )
            
            self._time_enabled_check.setChecked(config.time_label.enabled)
            self._time_unit_combo.setCurrentText(config.time_label.unit)
            self._time_font_combo.setCurrentText(config.time_label.font_family)
            self._time_size_spin.setValue(config.time_label.font_size)
            self._time_bold_check.setChecked(config.time_label.font_bold)
            self._time_color_combo.setCurrentText(config.time_label.color)
            
            self._scale_enabled_check.setChecked(config.scale_bar.enabled)
            self._scale_thickness_spin.setValue(config.scale_bar.thickness)
            self._scale_length_spin.setValue(config.scale_bar.length_um)
            self._scale_bar_color_combo.setCurrentText(config.scale_bar.bar_color)
            self._scale_text_check.setChecked(config.scale_bar.text_enabled)
            self._scale_text_pos_combo.setCurrentText(
                config.scale_bar.text_position.capitalize()
            )
            self._scale_text_gap_spin.setValue(config.scale_bar.text_gap)
            self._scale_font_combo.setCurrentText(config.scale_bar.font_family)
            self._scale_size_spin.setValue(config.scale_bar.font_size)
            self._scale_bold_check.setChecked(config.scale_bar.font_bold)
            self._scale_text_color_combo.setCurrentText(config.scale_bar.text_color)
            
            self._speed_enabled_check.setChecked(config.speed_label.enabled)
            self._speed_font_combo.setCurrentText(config.speed_label.font_family)
            self._speed_size_spin.setValue(config.speed_label.font_size)
            self._speed_bold_check.setChecked(config.speed_label.font_bold)
            self._speed_color_combo.setCurrentText(config.speed_label.color)
            
            self._colorbar_enabled_check.setChecked(config.colorbar.enabled)
            self._colorbar_cmap_combo.setCurrentText(config.colorbar.colormap)
            self._colorbar_height_spin.setValue(config.colorbar.bar_height)
            self._colorbar_width_spin.setValue(config.colorbar.bar_width)
            self._colorbar_title_edit.setText(config.colorbar.title)
            self._colorbar_title_pos_combo.setCurrentText(
                config.colorbar.title_position.capitalize()
            )
            self._colorbar_title_gap_spin.setValue(config.colorbar.title_gap)
            self._colorbar_title_font_combo.setCurrentText(
                config.colorbar.title_font_family
            )
            self._colorbar_title_size_spin.setValue(config.colorbar.title_font_size)
            self._colorbar_title_bold_check.setChecked(config.colorbar.title_font_bold)
            self._colorbar_title_color_combo.setCurrentText(config.colorbar.title_color)
            self._colorbar_min_spin.setValue(config.colorbar.vmin)
            self._colorbar_max_spin.setValue(config.colorbar.vmax)
            self._colorbar_tick_spin.setValue(config.colorbar.tick_interval)
            self._colorbar_tick_font_combo.setCurrentText(
                config.colorbar.tick_font_family
            )
            self._colorbar_tick_size_spin.setValue(config.colorbar.tick_font_size)
            self._colorbar_tick_bold_check.setChecked(config.colorbar.tick_font_bold)
            self._colorbar_tick_color_combo.setCurrentText(config.colorbar.tick_color)
            
        finally:
            self._updating = False
    
    def set_original_fps(self, fps: float):
        """
        Set original FPS for speed ratio calculation.
        
        Args:
            fps: Original FPS value from data loading.
        """
        self._original_fps = fps
        self._update_speed_ratio()
    
    def update_hidden_objects(self, records: list[HiddenRecord]):
        """Update the hidden objects list."""
        self._object_list.clear()
        
        for record in records:
            item = QListWidgetItem(record.get_description())
            item.setData(Qt.ItemDataRole.UserRole, record.obj_id)
            self._object_list.addItem(item)
