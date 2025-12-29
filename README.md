# Model Preview Generator

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg" alt="Platform">
</p>

A user-friendly desktop application for generating professional preview images and animated GIFs from 3D models. Perfect for showcasing your 3D assets on websites, portfolios, online stores, and social media.

![Screenshot](docs/screenshot.png)

## ✨ Features

- **🎬 Animated GIFs** - Create smooth rotating animations of your 3D models
- **📸 Multi-angle Previews** - Generate static images from any angle (0°, 45°, 90°, etc.)
- **🎨 Multiple Backgrounds** - Choose from black, white, gray, transparent, gradient, and more
- **💡 Lighting Presets** - Default, warm, cool, bright, dim, and dramatic lighting options
- **🔲 Wireframe Mode** - Generate technical wireframe renders
- **📐 Customizable Camera** - Adjust zoom and position for perfect framing
- **🖼️ High Resolution** - Export images up to 4K resolution

## 📦 Supported Formats

- **GLB** / **GLTF** (recommended)
- **OBJ**
- **STL**
- **PLY**
- **FBX**

## 🚀 Quick Start

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/renda/3d-model-to-gif.git
   cd 3d-model-to-gif
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   ```bash
   python main.py
   ```

### Linux Users (Additional Setup)

If you encounter Qt platform plugin errors on Linux, install the required system packages:

```bash
# Ubuntu/Debian
sudo apt-get install libxcb-cursor0 libxcb-xinerama0

# Fedora
sudo dnf install xcb-util-cursor xcb-util-wm

# Arch Linux
sudo pacman -S xcb-util-cursor xcb-util-wm
```

## 📖 Usage

### Creating an Animated GIF

1. Click **Browse** and select your 3D model file
2. Go to the **🎬 GIF Animation** tab
3. Adjust camera settings (zoom, position)
4. Configure animation settings:
   - **Duration**: Length of the animation (1-30 seconds)
   - **Frame Rate**: Smoothness (5-30 fps)
   - **Rotation Speed**: How fast the model rotates
   - **Lighting**: Brightness of the scene
5. Click **Create GIF**

### Exporting Image Previews

1. Click **Browse** and select your 3D model file
2. Go to the **📸 Image Previews** tab
3. Configure output settings:
   - **Image Size**: Resolution of output images
   - **Preview Angles**: Select which angles to render
   - **Backgrounds**: Choose background styles
   - **Lighting**: Select lighting presets
4. Enable **Include wireframe previews** if needed
5. Click **Export Previews**

## ⚙️ Configuration Options

### Camera Settings

| Setting | Description | Range |
|---------|-------------|-------|
| Zoom | Distance from model | 0.1 - 100 |
| Offset X | Horizontal position | -100 - 100 |
| Offset Y | Vertical position | -100 - 100 |

### GIF Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Duration | Animation length | 4 seconds |
| Frame Rate | Frames per second | 15 fps |
| Rotation Speed | Degrees per second | 90°/s |
| Lighting | Scene brightness | 5.0 |

### Image Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Width | Image width in pixels | 800 |
| Height | Image height in pixels | 800 |
| Angles | Rotation angles to render | 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315° |

### Background Options

- **Black** - Classic dark background
- **White** - Clean light background
- **Gray** - Neutral gray background
- **Transparent** - PNG with alpha channel
- **Blue** - Professional blue tone
- **Gradient** - Smooth vertical gradient

### Lighting Presets

- **Default** - Balanced neutral lighting
- **Warm** - Orange/yellow tones
- **Cool** - Blue tones
- **Bright** - High intensity
- **Dim** - Low intensity
- **Dramatic** - High contrast

## 🛠️ Development

### Project Structure

```
3d-model-to-gif/
├── main.py              # Application entry point
├── src/
│   ├── __init__.py      # Package initialization
│   ├── app.py           # GUI application
│   └── renderer.py      # 3D rendering engine
├── tests/               # Unit tests
├── docs/                # Documentation
├── requirements.txt     # Dependencies
├── pyproject.toml       # Project configuration
└── README.md
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Style

This project uses:

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
black src/
ruff check src/
mypy src/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [pyrender](https://github.com/mmatl/pyrender) - 3D rendering library
- [trimesh](https://github.com/mikedh/trimesh) - 3D mesh loading
- [PySide6](https://www.qt.io/qt-for-python) - Qt GUI framework

## 📬 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/renda/3d-model-to-gif/issues) page
2. Create a new issue with:
   - Your operating system
   - Python version
   - Steps to reproduce the problem
   - Error messages (if any)

---

<p align="center">
  Made with ❤️ for the 3D community
</p>
