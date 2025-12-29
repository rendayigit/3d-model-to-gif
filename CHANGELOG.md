# Changelog

All notable changes to Model Preview Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-29

### Added

- Initial release of Model Preview Generator
- GUI application with PySide6
- GIF animation export with customizable settings
  - Adjustable duration, frame rate, and rotation speed
  - Configurable lighting intensity
- Multi-angle image preview export
  - Support for 8 preset angles (0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°)
  - Custom angle input
- Multiple background options
  - Black, white, gray, dark gray
  - Transparent (PNG with alpha)
  - Blue tone
  - Vertical gradient
- Lighting presets
  - Default, warm, cool, bright, dim, dramatic
- Wireframe rendering mode
- Camera controls (zoom, X/Y offset)
- Support for multiple 3D formats (GLB, GLTF, OBJ, STL, PLY, FBX)
- Cross-platform support (Linux, Windows, macOS)

### Technical

- Modular architecture with separate renderer and GUI modules
- Type hints throughout the codebase
- Dataclasses for configuration management
- Worker threads for non-blocking export operations
- Progress tracking for export operations
