"""
Application styles and themes.

Defines macOS-inspired light theme stylesheet for PyQt6.
"""

MACOS_LIGHT_STYLE = """
/* Main Window */
QMainWindow {
    background-color: #f5f5f7;
}

/* General Widget */
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #1d1d1f;
}

/* Menu Bar */
QMenuBar {
    background-color: #f5f5f7;
    border-bottom: 1px solid #d2d2d7;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #e8e8ed;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0071e3;
    color: #ffffff;
}

/* Scroll Area */
QScrollArea {
    background-color: #f5f5f7;
    border: none;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #c7c7cc;
    border-radius: 5px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a8a8ad;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #c7c7cc;
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a8a8ad;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Group Box */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 10px;
    margin-top: 16px;
    padding: 16px;
    padding-top: 24px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    color: #1d1d1f;
    font-weight: 600;
    font-size: 14px;
}

/* Labels */
QLabel {
    color: #1d1d1f;
    background-color: transparent;
}

/* Line Edit */
QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #0071e3;
}

QLineEdit:focus {
    border: 2px solid #0071e3;
    padding: 5px 9px;
}

QLineEdit:disabled {
    background-color: #f5f5f7;
    color: #8e8e93;
}

/* Spin Box */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 80px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #0071e3;
    padding: 5px 9px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 20px;
    border: none;
    background-color: transparent;
}

/* Combo Box */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 100px;
}

QComboBox:focus {
    border: 2px solid #0071e3;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    selection-background-color: #0071e3;
    selection-color: #ffffff;
}

/* Check Box */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #d2d2d7;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0071e3;
    border-color: #0071e3;
}

QCheckBox::indicator:hover {
    border-color: #0071e3;
}

/* Radio Button */
QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid #d2d2d7;
    background-color: #ffffff;
}

QRadioButton::indicator:checked {
    background-color: #0071e3;
    border: 5px solid #ffffff;
    outline: 1px solid #0071e3;
}

/* Push Button */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #f5f5f7;
}

QPushButton:pressed {
    background-color: #e8e8ed;
}

QPushButton:disabled {
    background-color: #f5f5f7;
    color: #8e8e93;
}

QPushButton#primaryButton {
    background-color: #0071e3;
    border-color: #0071e3;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #0077ed;
}

QPushButton#primaryButton:pressed {
    background-color: #006edb;
}

/* Slider */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #e5e5ea;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 12px;
    height: 12px;
    margin: -4px 0;
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
}

QSlider::handle:horizontal:hover {
    border-color: #0071e3;
}

QSlider::sub-page:horizontal {
    background-color: #0071e3;
    border-radius: 2px;
}

/* Progress Bar */
QProgressBar {
    background-color: #e5e5ea;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #0071e3;
    border-radius: 4px;
}

/* Tab Widget */
QTabWidget::pane {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
}

QTabBar::tab {
    background-color: transparent;
    padding: 8px 16px;
    margin-right: 4px;
    border-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
}

QTabBar::tab:hover:!selected {
    background-color: #f5f5f7;
}

/* List Widget */
QListWidget {
    background-color: #ffffff;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #0071e3;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f5f5f7;
}

/* Splitter */
QSplitter::handle {
    background-color: #e5e5ea;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* Status Bar */
QStatusBar {
    background-color: #f5f5f7;
    border-top: 1px solid #e5e5ea;
    padding: 4px;
}

/* Dialog */
QDialog {
    background-color: #f5f5f7;
}

/* Tool Tip */
QToolTip {
    background-color: #1d1d1f;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
}

/* Graphics View */
QGraphicsView {
    background-color: #2c2c2e;
    border: 1px solid #e5e5ea;
    border-radius: 8px;
}
"""


def get_application_style() -> str:
    """
    Get the application stylesheet.
    
    Returns:
        CSS stylesheet string.
    """
    return MACOS_LIGHT_STYLE
