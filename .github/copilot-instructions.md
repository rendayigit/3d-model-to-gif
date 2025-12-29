# Model Preview Generator - GitHub Copilot Instructions

## Project Overview

This is a Python desktop application for generating preview images and animated GIFs from 3D models. It's designed to help 3D artists and developers create professional previews of their models for publishing on websites, portfolios, and online stores.

## Technology Stack

- **Python 3.10+** - Core language
- **PySide6** - Qt-based GUI framework
- **pyrender** - 3D rendering engine
- **trimesh** - 3D mesh loading and manipulation
- **imageio** - Image and GIF writing
- **Pillow** - Image processing
- **NumPy** - Numerical operations

## Project Structure

```
main.py              # Entry point - run this to start the app
src/
├── __init__.py      # Package metadata and version
├── app.py           # GUI application (PySide6 widgets and windows)
└── renderer.py      # 3D rendering engine (scene setup, rendering)
tests/
└── test_renderer.py # Unit tests for renderer module
```

## Key Components

### renderer.py

- `CameraSettings` - Dataclass for camera configuration
- `LightingPreset` - Dataclass for lighting configuration
- `GifSettings` - Dataclass for GIF animation settings
- `ImageSettings` - Dataclass for static image settings
- `render_single_frame()` - Render a single frame with transparent background
- `render_image()` - Render a single preview image
- `render_preview_set()` - Render multiple angles with same settings
- `render_all_previews()` - Comprehensive export with multiple options
- `render_gif()` - Create animated GIF (offscreen, no window)

### app.py

- `MainWindow` - Main application window
- `GifExportTab` - Tab for GIF export settings
- `ImagePreviewTab` - Tab for image preview export
- Worker threads for non-blocking export operations

## Code Style

- Use type hints for all function signatures
- Use dataclasses for configuration objects
- Google-style docstrings
- Black formatter with 100 char line length
- Ruff for linting

## Common Tasks

### Adding a new lighting preset

1. Add entry to `LightingPreset.get_presets()` in renderer.py
2. The GUI will automatically pick it up

### Adding a new export option

1. Add the setting to the appropriate dataclass
2. Update the GUI widget to include the control
3. Pass the setting through the worker thread to the render function

## Testing

Run tests with: `pytest -v`

## Dependencies

Core rendering requires OpenGL support. On Linux, the xcb platform plugin needs `libxcb-cursor0`.
