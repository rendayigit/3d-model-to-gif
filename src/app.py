"""
Model Preview Generator - Main GUI Application

A user-friendly application for generating preview images and animated GIFs
from 3D models for publishing on the web.
"""

import math
import os
import sys
from pathlib import Path

# Set Qt platform to offscreen if XCB fails (fallback for headless/WSL environments)
if sys.platform == "linux":
    # Try to use xcb, fall back to offscreen if not available
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.renderer import (
    BackgroundPreset,
    CameraSettings,
    GifSettings,
    ImageSettings,
    LightingPreset,
    render_all_previews,
    render_gif,
)

# =============================================================================
# Constants
# =============================================================================

APP_NAME = "Model Preview Generator"
APP_VERSION = "1.0.0"
SUPPORTED_FORMATS = "3D Model Files (*.glb *.gltf *.obj *.stl *.ply *.fbx)"


# =============================================================================
# Worker Threads
# =============================================================================


class PreviewExportWorker(QThread):
    """Worker thread for exporting image previews."""

    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        model_path: str,
        output_dir: str,
        camera: CameraSettings,
        lighting_keys: list[str],
        background_keys: list[str],
        image_settings: ImageSettings,
        include_wireframe: bool,
    ):
        super().__init__()
        self.model_path = model_path
        self.output_dir = output_dir
        self.camera = camera
        self.lighting_keys = lighting_keys
        self.background_keys = background_keys
        self.image_settings = image_settings
        self.include_wireframe = include_wireframe

    def run(self):
        try:
            result = render_all_previews(
                self.model_path,
                self.output_dir,
                self.camera,
                self.lighting_keys,
                self.background_keys,
                self.image_settings,
                self.include_wireframe,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class GifExportWorker(QThread):
    """Worker thread for exporting GIF animations."""

    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        model_path: str,
        output_path: str,
        camera: CameraSettings,
        gif_settings: GifSettings,
    ):
        super().__init__()
        self.model_path = model_path
        self.output_path = output_path
        self.camera = camera
        self.gif_settings = gif_settings

    def run(self):
        try:
            result = render_gif(
                self.model_path,
                self.output_path,
                self.camera,
                self.gif_settings,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# Custom Widgets
# =============================================================================


class FileSelector(QWidget):
    """Widget for selecting a file with browse button."""

    fileChanged = Signal(str)

    def __init__(
        self,
        label: str,
        filter_str: str = "",
        save_mode: bool = False,
        directory_mode: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.filter_str = filter_str
        self.save_mode = save_mode
        self.directory_mode = directory_mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label)
        self.label.setMinimumWidth(100)
        self.edit = QLineEdit()
        self.edit.textChanged.connect(self.fileChanged.emit)
        self.button = QPushButton("Browse...")
        self.button.clicked.connect(self._browse)

        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.button)

    def _browse(self):
        if self.directory_mode:
            path = QFileDialog.getExistingDirectory(self, "Select Directory", self.edit.text())
        elif self.save_mode:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save File", self.edit.text(), self.filter_str
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select File", self.edit.text(), self.filter_str
            )

        if path:
            self.edit.setText(path)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, text: str):
        self.edit.setText(text)


class CameraSettingsWidget(QGroupBox):
    """Widget for camera settings configuration."""

    def __init__(self, title: str = "Camera Settings", parent=None):
        super().__init__(title, parent)

        layout = QVBoxLayout(self)

        # Zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(0.1, 100)
        self.zoom_spin.setValue(2.0)
        self.zoom_spin.setSingleStep(0.1)
        self.zoom_spin.setToolTip("Distance from camera to model (higher = further)")
        zoom_layout.addWidget(self.zoom_spin)
        layout.addLayout(zoom_layout)

        # Offset X/Y
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("Offset X:"))
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-100, 100)
        self.x_spin.setValue(0.0)
        self.x_spin.setSingleStep(0.1)
        offset_layout.addWidget(self.x_spin)

        offset_layout.addWidget(QLabel("Y:"))
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-100, 100)
        self.y_spin.setValue(0.0)
        self.y_spin.setSingleStep(0.1)
        offset_layout.addWidget(self.y_spin)
        layout.addLayout(offset_layout)

    def get_settings(self) -> CameraSettings:
        return CameraSettings(
            zoom=self.zoom_spin.value(),
            offset_x=self.x_spin.value(),
            offset_y=self.y_spin.value(),
        )

    def set_settings(self, settings: CameraSettings):
        self.zoom_spin.setValue(settings.zoom)
        self.x_spin.setValue(settings.offset_x)
        self.y_spin.setValue(settings.offset_y)


class MultiSelectList(QGroupBox):
    """Widget for multi-selection list with checkable items."""

    selectionChanged = Signal()

    def __init__(
        self, title: str, items: dict[str, str], default_selected: list[str] = None, parent=None
    ):
        super().__init__(title, parent)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.list_widget.itemSelectionChanged.connect(self.selectionChanged.emit)

        for key, display_name in items.items():
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)
            if default_selected and key in default_selected:
                item.setSelected(True)

        self.list_widget.setMaximumHeight(120)
        layout.addWidget(self.list_widget)

    def get_selected_keys(self) -> list[str]:
        return [
            self.list_widget.item(i).data(Qt.UserRole)
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).isSelected()
        ]

    def select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(True)

    def select_none(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(False)


# =============================================================================
# Main Tabs
# =============================================================================


class GifExportTab(QWidget):
    """Tab for GIF export settings and execution."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.worker = None

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Output file
        self.output_selector = FileSelector("Output File:", "GIF Files (*.gif)", save_mode=True)
        layout.addWidget(self.output_selector)

        # Camera settings
        self.camera_widget = CameraSettingsWidget()
        layout.addWidget(self.camera_widget)

        # Animation settings
        anim_group = QGroupBox("Animation Settings")
        anim_layout = QVBoxLayout(anim_group)

        # Duration
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Duration:"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 30.0)
        self.duration_spin.setValue(4.0)
        self.duration_spin.setSuffix(" seconds")
        self.duration_spin.setToolTip("Length of the GIF animation")
        duration_layout.addWidget(self.duration_spin)
        anim_layout.addLayout(duration_layout)

        # FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Frame Rate:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(5, 30)
        self.fps_spin.setValue(15)
        self.fps_spin.setSuffix(" fps")
        self.fps_spin.setToolTip("Frames per second (higher = smoother but larger file)")
        fps_layout.addWidget(self.fps_spin)
        anim_layout.addLayout(fps_layout)

        # Rotation speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Rotation Speed:"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(10, 360)
        self.speed_spin.setValue(90)
        self.speed_spin.setSuffix(" °/s")
        self.speed_spin.setToolTip("Degrees per second rotation")
        speed_layout.addWidget(self.speed_spin)
        anim_layout.addLayout(speed_layout)

        # Lighting intensity
        light_layout = QHBoxLayout()
        light_layout.addWidget(QLabel("Lighting:"))
        self.light_spin = QDoubleSpinBox()
        self.light_spin.setRange(1.0, 20.0)
        self.light_spin.setValue(5.0)
        self.light_spin.setToolTip("Lighting intensity")
        light_layout.addWidget(self.light_spin)
        anim_layout.addLayout(light_layout)

        layout.addWidget(anim_group)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Export button
        self.export_btn = QPushButton("🎬 Create GIF")
        self.export_btn.setMinimumHeight(40)
        font = self.export_btn.font()
        font.setPointSize(11)
        font.setBold(True)
        self.export_btn.setFont(font)
        layout.addWidget(self.export_btn)

        layout.addStretch()

    def get_gif_settings(self) -> GifSettings:
        return GifSettings(
            duration=self.duration_spin.value(),
            fps=self.fps_spin.value(),
            rotate_speed=self.speed_spin.value(),
            lighting_intensity=self.light_spin.value(),
        )

    def set_output_from_model(self, model_path: str):
        if model_path:
            base = os.path.splitext(model_path)[0]
            self.output_selector.setText(f"{base}.gif")


class ImagePreviewTab(QWidget):
    """Tab for image preview export settings and execution."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.worker = None

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Output directory
        self.output_selector = FileSelector("Output Folder:", directory_mode=True)
        layout.addWidget(self.output_selector)

        # Image size
        size_group = QGroupBox("Image Settings")
        size_layout = QHBoxLayout(size_group)

        size_layout.addWidget(QLabel("Size:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(128, 4096)
        self.width_spin.setValue(800)
        self.width_spin.setSuffix(" px")
        size_layout.addWidget(self.width_spin)

        size_layout.addWidget(QLabel("×"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(128, 4096)
        self.height_spin.setValue(800)
        self.height_spin.setSuffix(" px")
        size_layout.addWidget(self.height_spin)

        size_layout.addStretch()
        layout.addWidget(size_group)

        # Camera settings
        self.camera_widget = CameraSettingsWidget()
        layout.addWidget(self.camera_widget)

        # Angles
        angles_group = QGroupBox("Preview Angles")
        angles_layout = QVBoxLayout(angles_group)

        self.angles_list = QListWidget()
        self.angles_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.angles_list.setMaximumHeight(80)

        default_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        for angle in default_angles:
            item = QListWidgetItem(f"{angle}°")
            item.setData(Qt.UserRole, angle)
            self.angles_list.addItem(item)
            item.setSelected(True)

        angles_layout.addWidget(self.angles_list)

        # Custom angle
        custom_layout = QHBoxLayout()
        self.custom_angle_spin = QSpinBox()
        self.custom_angle_spin.setRange(0, 359)
        self.custom_angle_spin.setSuffix("°")
        custom_layout.addWidget(QLabel("Add custom:"))
        custom_layout.addWidget(self.custom_angle_spin)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_custom_angle)
        custom_layout.addWidget(add_btn)
        custom_layout.addStretch()
        angles_layout.addLayout(custom_layout)

        layout.addWidget(angles_group)

        # Options side by side
        options_layout = QHBoxLayout()

        # Backgrounds
        bg_items = {k: v.name for k, v in BackgroundPreset.get_presets().items()}
        self.bg_selector = MultiSelectList(
            "Backgrounds", bg_items, default_selected=["black", "white", "transparent"]
        )
        options_layout.addWidget(self.bg_selector)

        # Lighting
        light_items = {k: v.name for k, v in LightingPreset.get_presets().items()}
        self.light_selector = MultiSelectList(
            "Lighting", light_items, default_selected=["default", "warm"]
        )
        options_layout.addWidget(self.light_selector)

        layout.addLayout(options_layout)

        # Wireframe option
        self.wireframe_check = QCheckBox("Include wireframe previews")
        self.wireframe_check.setChecked(True)
        self.wireframe_check.setToolTip("Generate additional wireframe renders")
        layout.addWidget(self.wireframe_check)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Export button
        self.export_btn = QPushButton("📸 Export Previews")
        self.export_btn.setMinimumHeight(40)
        font = self.export_btn.font()
        font.setPointSize(11)
        font.setBold(True)
        self.export_btn.setFont(font)
        layout.addWidget(self.export_btn)

        layout.addStretch()

    def _add_custom_angle(self):
        angle = self.custom_angle_spin.value()
        for i in range(self.angles_list.count()):
            if self.angles_list.item(i).data(Qt.UserRole) == angle:
                return  # Already exists

        item = QListWidgetItem(f"{angle}°")
        item.setData(Qt.UserRole, angle)
        self.angles_list.addItem(item)
        item.setSelected(True)

    def get_selected_angles(self) -> list[int]:
        return sorted(
            [
                self.angles_list.item(i).data(Qt.UserRole)
                for i in range(self.angles_list.count())
                if self.angles_list.item(i).isSelected()
            ]
        )

    def get_image_settings(self) -> ImageSettings:
        return ImageSettings(
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            angles=self.get_selected_angles(),
        )

    def set_output_from_model(self, model_path: str):
        if model_path:
            base = os.path.splitext(model_path)[0]
            self.output_selector.setText(f"{base}_previews")


# =============================================================================
# Main Window
# =============================================================================


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(600, 700)
        self.resize(650, 800)

        self._setup_menu()
        self._setup_ui()
        self._connect_signals()

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Model...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_model)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        github_action = QAction("&GitHub Repository", self)
        github_action.triggered.connect(
            lambda: QDesktopServices.openUrl("https://github.com/renda/3d-model-to-gif")
        )
        help_menu.addAction(github_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel(f"<h2>{APP_NAME}</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Generate preview images and GIFs from your 3D models")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # Model file selector
        model_group = QGroupBox("3D Model")
        model_layout = QVBoxLayout(model_group)

        self.model_selector = FileSelector("Model File:", SUPPORTED_FORMATS)
        model_layout.addWidget(self.model_selector)

        # Supported formats info
        formats_label = QLabel("<small>Supported: GLB, GLTF, OBJ, STL, PLY, FBX</small>")
        formats_label.setStyleSheet("color: gray;")
        model_layout.addWidget(formats_label)

        layout.addWidget(model_group)

        # Tabs
        self.tabs = QTabWidget()

        self.gif_tab = GifExportTab()
        self.tabs.addTab(self.gif_tab, "🎬 GIF Animation")

        self.preview_tab = ImagePreviewTab()
        self.tabs.addTab(self.preview_tab, "📸 Image Previews")

        layout.addWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Ready - Select a 3D model to begin")

    def _connect_signals(self):
        # Model selection updates output paths
        self.model_selector.fileChanged.connect(self._on_model_changed)

        # Export buttons
        self.gif_tab.export_btn.clicked.connect(self._export_gif)
        self.preview_tab.export_btn.clicked.connect(self._export_previews)

    def _on_model_changed(self, path: str):
        self.gif_tab.set_output_from_model(path)
        self.preview_tab.set_output_from_model(path)

        if path and os.path.exists(path):
            self.statusBar().showMessage(f"Model loaded: {os.path.basename(path)}")
        else:
            self.statusBar().showMessage("Ready - Select a 3D model to begin")

    def _open_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select 3D Model", "", SUPPORTED_FORMATS)
        if path:
            self.model_selector.setText(path)

    def _validate_model(self) -> bool:
        model_path = self.model_selector.text()
        if not model_path:
            QMessageBox.warning(self, "No Model Selected", "Please select a 3D model file first.")
            return False

        if not os.path.exists(model_path):
            QMessageBox.warning(
                self, "File Not Found", f"The selected model file does not exist:\n{model_path}"
            )
            return False

        return True

    def _export_gif(self):
        if not self._validate_model():
            return

        output_path = self.gif_tab.output_selector.text()
        if not output_path:
            QMessageBox.warning(
                self, "No Output Path", "Please specify an output file path for the GIF."
            )
            return

        if not output_path.lower().endswith(".gif"):
            output_path += ".gif"
            self.gif_tab.output_selector.setText(output_path)

        # Disable UI
        self.gif_tab.export_btn.setEnabled(False)
        self.gif_tab.progress_bar.setVisible(True)
        self.gif_tab.progress_bar.setRange(0, 100)
        self.gif_tab.progress_label.setVisible(True)

        # Create worker
        self.gif_tab.worker = GifExportWorker(
            self.model_selector.text(),
            output_path,
            self.gif_tab.camera_widget.get_settings(),
            self.gif_tab.get_gif_settings(),
        )
        self.gif_tab.worker.progress.connect(self._on_gif_progress)
        self.gif_tab.worker.finished.connect(self._on_gif_finished)
        self.gif_tab.worker.error.connect(self._on_gif_error)
        self.gif_tab.worker.start()

        self.statusBar().showMessage("Creating GIF animation...")

    def _on_gif_progress(self, current: int, total: int, message: str):
        self.gif_tab.progress_bar.setValue(current)
        self.gif_tab.progress_label.setText(message)

    def _on_gif_finished(self, output_path: str):
        self.gif_tab.export_btn.setEnabled(True)
        self.gif_tab.progress_bar.setVisible(False)
        self.gif_tab.progress_label.setVisible(False)

        self.statusBar().showMessage(f"GIF saved: {output_path}")

        QMessageBox.information(
            self, "Export Complete", f"GIF animation saved successfully!\n\n{output_path}"
        )

    def _on_gif_error(self, error: str):
        self.gif_tab.export_btn.setEnabled(True)
        self.gif_tab.progress_bar.setVisible(False)
        self.gif_tab.progress_label.setVisible(False)

        self.statusBar().showMessage("Error creating GIF")

        QMessageBox.critical(self, "Export Error", f"Failed to create GIF:\n\n{error}")

    def _export_previews(self):
        if not self._validate_model():
            return

        output_dir = self.preview_tab.output_selector.text()
        if not output_dir:
            QMessageBox.warning(
                self,
                "No Output Directory",
                "Please specify an output directory for the preview images.",
            )
            return

        # Validate selections
        backgrounds = self.preview_tab.bg_selector.get_selected_keys()
        if not backgrounds:
            QMessageBox.warning(
                self, "No Background Selected", "Please select at least one background option."
            )
            return

        lightings = self.preview_tab.light_selector.get_selected_keys()
        if not lightings:
            QMessageBox.warning(
                self, "No Lighting Selected", "Please select at least one lighting option."
            )
            return

        angles = self.preview_tab.get_selected_angles()
        if not angles:
            QMessageBox.warning(
                self, "No Angles Selected", "Please select at least one preview angle."
            )
            return

        # Disable UI
        self.preview_tab.export_btn.setEnabled(False)
        self.preview_tab.progress_bar.setVisible(True)
        self.preview_tab.progress_bar.setRange(0, 0)  # Indeterminate
        self.preview_tab.progress_label.setVisible(True)

        # Create worker
        self.preview_tab.worker = PreviewExportWorker(
            self.model_selector.text(),
            output_dir,
            self.preview_tab.camera_widget.get_settings(),
            lightings,
            backgrounds,
            self.preview_tab.get_image_settings(),
            self.preview_tab.wireframe_check.isChecked(),
        )
        self.preview_tab.worker.progress.connect(self._on_preview_progress)
        self.preview_tab.worker.finished.connect(self._on_preview_finished)
        self.preview_tab.worker.error.connect(self._on_preview_error)
        self.preview_tab.worker.start()

        self.statusBar().showMessage("Exporting preview images...")

    def _on_preview_progress(self, current: int, total: int, message: str):
        if total > 0:
            self.preview_tab.progress_bar.setRange(0, total)
            self.preview_tab.progress_bar.setValue(current)
        self.preview_tab.progress_label.setText(message)

    def _on_preview_finished(self, result: dict):
        self.preview_tab.export_btn.setEnabled(True)
        self.preview_tab.progress_bar.setVisible(False)
        self.preview_tab.progress_label.setVisible(False)

        total_images = sum(len(paths) for paths in result.values())
        output_dir = self.preview_tab.output_selector.text()

        self.statusBar().showMessage(f"Exported {total_images} preview images")

        QMessageBox.information(
            self,
            "Export Complete",
            f"Successfully exported {total_images} preview images!\n\n" f"Location: {output_dir}",
        )

    def _on_preview_error(self, error: str):
        self.preview_tab.export_btn.setEnabled(True)
        self.preview_tab.progress_bar.setVisible(False)
        self.preview_tab.progress_label.setVisible(False)

        self.statusBar().showMessage("Error exporting previews")

        QMessageBox.critical(self, "Export Error", f"Failed to export previews:\n\n{error}")

    def _show_about(self):
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>Generate professional preview images and animated GIFs "
            f"from 3D models for publishing on the web.</p>"
            f"<p>Supports GLB, GLTF, OBJ, STL, PLY, and FBX formats.</p>"
            f"<p><b>License:</b> MIT</p>"
            f"<p><a href='https://github.com/renda/3d-model-to-gif'>GitHub Repository</a></p>",
        )


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Main entry point for the application."""
    # Handle high DPI displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set style
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
