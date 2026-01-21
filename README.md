# Bac-Motion Visualization

<div align="center">

**A Professional Bacterial Motion Visualization Application**

_Overlay segmentation and tracking masks onto original image sequences for intuitive visualization of processing results_

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://pypi.org/project/PyQt6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()
[![Version](https://img.shields.io/badge/Version-1.1.0-brightgreen.svg)]()

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [What's New](#whats-new)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [User Interface](#user-interface)
- [Configuration Parameters](#configuration-parameters)
- [Export Options](#export-options)
- [File Format Support](#file-format-support)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Author](#author)

---

## What's New

### Version 1.1.0 (2026-01-21)

**New Features:**

- **Enhanced Colorbar Customization**
  - Border Thickness: Adjust the colorbar border line thickness (1-10 px)
  - Tick Thickness: Customize tick mark line thickness (1-10 px)
  - Tick Length: Control tick mark length from border (1-30 px)
  - Provides finer control over colorbar appearance for publication-quality figures

**Improvements:**

- Improved colorbar rendering precision with configurable line properties
- Enhanced UI parameter panel with new colorbar style controls
- Better consistency between preview and exported results

---

## Overview

**Bac-Motion Visualization** is a specialized desktop application designed for researchers in microbiology, cell biology, and biophysics who need to visualize and analyze bacterial motion and cell tracking data. The application combines original microscopy image sequences with segmentation masks and tracking data to produce publication-ready visualizations.

### Key Capabilities

- **Multi-layer Visualization**: Overlay masks, contours, trajectories, and annotations on original images
- **Real-time Preview**: Interactive preview with playback controls before export
- **Velocity Mapping**: Color-coded trajectories based on instantaneous velocity
- **Flexible Annotations**: Customizable time labels, scale bars, and colorbars
- **High-quality Export**: Generate videos (MP4, AVI, GIF) and image sequences suitable for publications

---

## Features

### Image Processing

| Feature                        | Description                                                        |
| ------------------------------ | ------------------------------------------------------------------ |
| **Multi-format Support**       | Load 8/12/16-bit grayscale or 24-bit RGB images (JPEG, PNG, TIFF)  |
| **Mask Overlay**               | Visualize segmentation masks with adjustable transparency (0-100%) |
| **Object Contours**            | Display object boundaries with customizable thickness and colors   |
| **Automatic Color Assignment** | Distinct colors automatically assigned to each tracked object      |

### Trajectory Visualization

| Feature               | Description                                                               |
| --------------------- | ------------------------------------------------------------------------- |
| **Display Modes**     | Full trajectory, Start-to-current, Delay-before, Delay-after              |
| **Velocity Coloring** | Color trajectories by instantaneous velocity using customizable colormaps |
| **Centroid Markers**  | Circle, Triangle, or Star markers at object centroids                     |
| **Ellipse Fitting**   | Display major and minor axes of fitted ellipses                           |

### Annotation System

| Feature              | Description                                                      |
| -------------------- | ---------------------------------------------------------------- |
| **Time Label**       | Display elapsed time with configurable units (ms, s, min, h)     |
| **Scale Bar**        | Physical scale reference with customizable length and appearance |
| **Speed Label**      | Playback speed indicator (e.g., "30×")                           |
| **Colorbar**         | Velocity scale legend with customizable range and tick marks     |
| **Drag-to-Position** | All annotation elements can be repositioned by dragging          |

### Data Import

| Feature              | Description                                               |
| -------------------- | --------------------------------------------------------- |
| **Image Sequences**  | Automatic detection and sorting of image files            |
| **Trajectory Data**  | Import from Excel (XLSX/XLS) or CSV files                 |
| **Flexible Mapping** | Map any columns to ID, Time, X, Y coordinates             |
| **Unit Conversion**  | Automatic conversion between pixels/μm and frames/seconds |

### Export Capabilities

| Feature               | Description                                        |
| --------------------- | -------------------------------------------------- |
| **Video Formats**     | MP4 (H.264), AVI, GIF                              |
| **Image Sequences**   | PNG with sequential numbering                      |
| **Configurable FPS**  | Set output frame rate independent of original data |
| **Quality Rendering** | High-quality text and graphics using PIL/Pillow    |

---

## System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.10 or higher
- **RAM**: 4 GB (8 GB recommended for large datasets)
- **Storage**: 500 MB for installation + space for data

### Dependencies

The application requires the following Python packages:

```
PyQt6>=6.6.0
numpy>=1.24.0
opencv-python>=4.8.0
Pillow>=10.0.0
pandas>=2.0.0
openpyxl>=3.1.0
```

---

## Installation

### Step 1: Create Virtual Environment

```bash
conda create -n motion_vis python=3.10
conda activate motion_vis
```

### Step 2: Clone or Download

```bash
git clone https://github.com/your-repo/motion-visualization.git
cd motion-visualization
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python main.py
```

The application window should appear if installation was successful.

---

## Quick Start

### Basic Workflow

1. **Launch Application**

   ```bash
   python main.py
   ```

2. **Load Data** (`Ctrl+L`)

   - Select original image sequence folder
   - Select mask image sequence folder
   - Set physical parameters (FPS, μm/pixel)
   - Optionally load trajectory data from Excel/CSV

3. **Adjust Parameters**

   - Configure visualization options in the left panel
   - Enable/disable overlay elements as needed
   - Customize appearance (colors, fonts, sizes)

4. **Preview**

   - Use playback controls to review the visualization
   - Switch between Edit Mode and Final Preview
   - Drag labels to desired positions

5. **Export** (`Ctrl+E`)
   - Select output directory
   - Choose export formats (video and/or images)
   - Start export process

---

## User Interface

### Main Window Layout

```
┌────────────────────────────────────────────────────────────┐
│  File  Config  Help                              Menu Bar  │
├─────────────────┬──────────────────────────────────────────┤
│                 │  [Edit Mode] [Final Preview]    Toolbar  │
│  Parameter      │ ┌──────────────────────────────────────┐ │
│  Panel          │ │                                      │ │
│                 │ │                                      │ │
│  - Mask Overlay │ │         Preview Area                 │ │
│  - Contour      │ │                                      │ │
│  - Centroid     │ │    (Rendered visualization          │ │
│  - Ellipse Axes │ │     with draggable labels)           │ │
│  - Trajectory   │ │                                      │ │
│  - Time Label   │ │                                      │ │
│  - Scale Bar    │ │                                      │ │
│  - Speed Label  │ └──────────────────────────────────────┘ │
│  - Colorbar     │ ┌──────────────────────────────────────┐ │
│  - Object Ops   │ │ ◀ ▶ ▶│ [====slider====] 1/100 │ │
│                 │ └──────────────────────────────────────┘ │
├─────────────────┴──────────────────────────────────────────┤
│  Ready - 100 frames, 5 objects               Status Bar    │
└────────────────────────────────────────────────────────────┘
```

### Preview Modes

- **Edit Mode**: Labels are displayed as draggable overlays for positioning
- **Final Preview**: Shows exact export result with labels rendered on image

---

## Configuration Parameters

### Global Parameters

| Parameter    | Description                      | Unit     |
| ------------ | -------------------------------- | -------- |
| Original FPS | Frame rate of original recording | fps      |
| μm/pixel     | Physical scale calibration       | μm/pixel |
| Output FPS   | Frame rate for exported video    | fps      |

### Mask Overlay

| Parameter | Range  | Default | Description                 |
| --------- | ------ | ------- | --------------------------- |
| Enabled   | On/Off | On      | Show/hide mask overlay      |
| Opacity   | 0-100% | 25%     | Transparency of mask colors |

### Object Contour

| Parameter | Range   | Default | Description             |
| --------- | ------- | ------- | ----------------------- |
| Enabled   | On/Off  | On      | Show/hide contour lines |
| Thickness | 1-99 px | 2 px    | Contour line width      |

### Centroid Marker

| Parameter | Options                | Default | Description                |
| --------- | ---------------------- | ------- | -------------------------- |
| Enabled   | On/Off                 | On      | Show/hide centroid markers |
| Shape     | Circle, Triangle, Star | Circle  | Marker shape               |
| Size      | 1-50 px                | 5 px    | Marker size                |

### Ellipse Axes

| Parameter       | Options    | Default | Description             |
| --------------- | ---------- | ------- | ----------------------- |
| Show Major Axis | On/Off     | On      | Display major axis line |
| Show Minor Axis | On/Off     | On      | Display minor axis line |
| Major Thickness | 1-99 px    | 1 px    | Major axis line width   |
| Minor Thickness | 1-99 px    | 1 px    | Minor axis line width   |
| Major Color     | Color list | White   | Major axis color        |
| Minor Color     | Color list | White   | Minor axis color        |

### Trajectory

| Parameter  | Options                                           | Default  | Description                 |
| ---------- | ------------------------------------------------- | -------- | --------------------------- |
| Enabled    | On/Off                                            | On       | Show/hide trajectories      |
| Mode       | Full, Start-to-Current, Delay Before, Delay After | Full     | Display mode                |
| Delay Time | 0.1-100 s                                         | 30 s     | Time window for delay modes |
| Thickness  | 1-99 px                                           | 2 px     | Trajectory line width       |
| Color Mode | Object Color, Velocity Color                      | Velocity | Coloring scheme             |

### Time Label

| Parameter | Options                | Default | Description          |
| --------- | ---------------------- | ------- | -------------------- |
| Enabled   | On/Off                 | On      | Show/hide time label |
| Unit      | ms, s, min, h          | s       | Time display unit    |
| Font      | Arial, Times New Roman | Arial   | Font family          |
| Size      | 8-99 pt                | 32 pt   | Font size            |
| Bold      | On/Off                 | On      | Bold text            |
| Color     | Color list             | White   | Text color           |

### Scale Bar

| Parameter     | Range/Options | Default | Description                |
| ------------- | ------------- | ------- | -------------------------- |
| Enabled       | On/Off        | On      | Show/hide scale bar        |
| Thickness     | 1-99 px       | 10 px   | Bar thickness              |
| Length        | 1-10000 μm    | 5 μm    | Physical length            |
| Bar Color     | Color list    | White   | Bar color                  |
| Show Text     | On/Off        | On      | Display length text        |
| Text Position | Above, Below  | Below   | Text placement             |
| Text Gap      | 0-99 px       | 5 px    | Space between bar and text |

### Colorbar (Velocity Mode)

| Parameter       | Range/Options         | Default        | Description                  |
| --------------- | --------------------- | -------------- | ---------------------------- |
| Enabled         | On/Off                | On             | Show/hide colorbar           |
| Colormap        | viridis, plasma, etc. | viridis        | Color scheme                 |
| Height          | 50-2000 px            | 800 px         | Bar height                   |
| Width           | 5-200 px              | 40 px          | Bar width                    |
| Title           | Text                  | "Speed (μm/s)" | Colorbar title               |
| Min/Max         | Numeric               | Auto           | Value range                  |
| Tick Interval   | Numeric               | Auto           | Spacing between ticks        |
| Border Thk      | 1-10 px               | 1 px           | Border line thickness        |
| Tick Thk        | 1-10 px               | 1 px           | Tick mark line thickness     |
| Tick Length     | 1-30 px               | 5 px           | Tick mark length from border |

---

## Export Options

### Video Export

| Format | Codec | Quality | File Size | Compatibility |
| ------ | ----- | ------- | --------- | ------------- |
| MP4    | H.264 | High    | Small     | Excellent     |
| AVI    | MJPEG | High    | Large     | Good          |
| GIF    | GIF   | Medium  | Medium    | Excellent     |

### Image Sequence Export

- **Format**: PNG (lossless)
- **Naming**: `{prefix}{number:06d}.png` (e.g., `frame_000001.png`)
- **Subfolder**: Customizable subfolder name

---

## File Format Support

### Image Formats

| Format | Extensions  | Bit Depth   | Color Modes          |
| ------ | ----------- | ----------- | -------------------- |
| JPEG   | .jpg, .jpeg | 8-bit       | Grayscale, RGB       |
| PNG    | .png        | 8/16-bit    | Grayscale, RGB, RGBA |
| TIFF   | .tif, .tiff | 8/12/16-bit | Grayscale, RGB       |

### Trajectory Data Formats

| Format | Extension   | ID Handling                |
| ------ | ----------- | -------------------------- |
| Excel  | .xlsx, .xls | Each sheet = one object    |
| CSV    | .csv        | ID column specifies object |

#### Excel File Structure

Each worksheet represents one tracked object. Required columns:

- Time (frame number or time value)
- X coordinate
- Y coordinate

#### CSV File Structure

All objects in single file. Required columns:

- ID (object identifier)
- Time
- X coordinate
- Y coordinate

---

## Keyboard Shortcuts

| Shortcut | Action               |
| -------- | -------------------- |
| `Ctrl+L` | Load Data            |
| `Ctrl+E` | Export               |
| `Ctrl+S` | Save Configuration   |
| `Ctrl+I` | Import Configuration |
| `Ctrl+Q` | Quit Application     |

---

## Troubleshooting

### Common Issues

**Q: Images not loading properly**

- Ensure all images in the sequence have the same dimensions
- Check that image format is supported (JPEG, PNG, TIFF)
- Verify file naming allows proper sorting

**Q: Trajectory data not recognized**

- Check column mapping in the load dialog
- Ensure data types are numeric (not text)
- Verify time and coordinate units are correct

**Q: Export is slow**

- Large images or many frames require more processing time
- Consider reducing output resolution or frame count
- Close other applications to free system resources

**Q: Labels not appearing in export**

- Ensure labels are enabled in parameter panel
- Check that labels are within image boundaries
- Verify font files are available (Windows Fonts folder)

**Q: Colorbar not showing**

- Colorbar only appears in Velocity Color mode
- Enable colorbar in the parameter panel
- Ensure trajectory visualization is enabled

---

## Project Structure

```
Bac-Motion Visualization/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── LICENSE                # MIT License
├── config/
│   └── default_config.json # Default configuration
├── logs/                  # Application logs
├── resources/
│   └── icons/             # UI icons
└── src/
    ├── controllers/       # Application logic
    │   ├── main_controller.py
    │   ├── preview_controller.py
    │   └── export_controller.py
    ├── core/              # Rendering engine
    │   ├── color_mapper.py
    │   ├── frame_renderer.py
    │   └── video_exporter.py
    ├── models/            # Data structures
    │   ├── config_model.py
    │   ├── data_manager.py
    │   ├── object_manager.py
    │   ├── trajectory_calculator.py
    │   └── trajectory_data_loader.py
    ├── utils/             # Utility functions
    │   ├── file_utils.py
    │   ├── image_utils.py
    │   ├── logger.py
    │   └── natural_sort.py
    └── views/             # User interface
        ├── main_window.py
        ├── parameter_panel.py
        ├── preview_widget.py
        ├── data_load_dialog.py
        ├── export_dialog.py
        ├── object_dialog.py
        ├── graphics_items.py
        ├── progress_dialog.py
        └── styles.py
```

---

## License

MIT License

Copyright (c) 2026 Lucien

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Author

**Lucien**

- Email: lucien-6@qq.com

---

<div align="center">

_Designed for researchers who need publication-quality motion visualization_

</div>
