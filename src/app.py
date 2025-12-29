"""
GUI Application for 3D Model Preview Generator.

This module provides the main application window and UI components
for generating preview images and GIFs from 3D models.
"""

import os
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .renderer import (
    CameraSettings,
    GifSettings,
    ImageSettings,
    LightingPreset,
    render_all_previews,
    render_gif,
)

# =============================================================================
# Multi-Selection List Widget
# =============================================================================


class MultiSelectList(QWidget):
    """A widget for selecting multiple items from a list."""

    def __init__(self, title: str, items: dict[str, str]):
        """
        Initialize the multi-select list.

        Args:
            title: Title for the group box.
            items: Dictionary mapping keys to display names.
        """
        super().__init__()
        self.items = items

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)

        self.list_widget = QListWidget()
        for key, display_name in items.items():
            item = QListWidgetItem(display_name)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(256, key)  # Store key in user data
            self.list_widget.addItem(item)

        group_layout.addWidget(self.list_widget)
        layout.addWidget(group)

    def get_selected_keys(self) -> list[str]:
        """Get list of selected item keys."""
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(256))
        return selected

    def select_first(self) -> None:
        """Select the first item in the list."""
        if self.list_widget.count() > 0:
            self.list_widget.item(0).setCheckState(Qt.CheckState.Checked)


# =============================================================================
# Worker Threads
# =============================================================================


class GifExportWorker(QThread):
    """Worker thread for GIF export."""

    progress = Signal(int, int, str)  # current, total, message
    finished_export = Signal(str)  # output path
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
            self.finished_export.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class PreviewExportWorker(QThread):
    """Worker thread for preview image export."""

    progress = Signal(int, int, str)  # current, total, message
    finished_export = Signal(dict)  # paths dict
    error = Signal(str)

    def __init__(
        self,
        model_path: str,
        output_dir: str,
        camera: CameraSettings,
        lighting_keys: list[str],
        image_settings: ImageSettings,
        include_wireframe: bool,
    ):
        super().__init__()
        self.model_path = model_path
        self.output_dir = output_dir
        self.camera = camera
        self.lighting_keys = lighting_keys
        self.image_settings = image_settings
        self.include_wireframe = include_wireframe

    def run(self):
        try:
            result = render_all_previews(
                self.model_path,
                self.output_dir,
                self.camera,
                self.lighting_keys,
                self.image_settings,
                self.include_wireframe,
                progress_callback=lambda c, t, m: self.progress.emit(c, t, m),
            )
            self.finished_export.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# =============================================================================
# GIF Export Tab
# =============================================================================


class GifExportTab(QWidget):
    """Tab for GIF export settings and execution."""

    def __init__(self):
        super().__init__()
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Model file selection
        model_group = QGroupBox("Model")
        model_layout = QHBoxLayout(model_group)

        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("Select a 3D model file...")
        model_layout.addWidget(self.model_path)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_model)
        model_layout.addWidget(browse_btn)

        layout.addWidget(model_group)

        # Output file selection
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout(output_group)

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output GIF path...")
        output_layout.addWidget(self.output_path)

        output_btn = QPushButton("Browse...")
        output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(output_btn)

        layout.addWidget(output_group)

        # Camera settings
        camera_group = QGroupBox("Camera")
        camera_layout = QVBoxLayout(camera_group)

        # Zoom slider
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider()
        self.zoom_slider.setOrientation(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 100)
        self.zoom_slider.setValue(20)
        zoom_row.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("2.0")
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f"{v / 10:.1f}"))
        zoom_row.addWidget(self.zoom_label)
        camera_layout.addLayout(zoom_row)

        layout.addWidget(camera_group)

        # GIF settings
        gif_group = QGroupBox("Animation Settings")
        gif_layout = QVBoxLayout(gif_group)

        # Duration
        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("Duration (sec):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 30)
        self.duration_spin.setValue(4)
        duration_row.addWidget(self.duration_spin)
        gif_layout.addLayout(duration_row)

        # FPS
        fps_row = QHBoxLayout()
        fps_row.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(5, 60)
        self.fps_spin.setValue(15)
        fps_row.addWidget(self.fps_spin)
        gif_layout.addLayout(fps_row)

        # Rotation speed
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Rotation (deg/sec):"))
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(10, 360)
        self.speed_spin.setValue(90)
        speed_row.addWidget(self.speed_spin)
        gif_layout.addLayout(speed_row)

        # Lighting intensity
        light_row = QHBoxLayout()
        light_row.addWidget(QLabel("Lighting:"))
        self.light_slider = QSlider()
        self.light_slider.setOrientation(Qt.Orientation.Horizontal)
        self.light_slider.setRange(1, 20)
        self.light_slider.setValue(5)
        light_row.addWidget(self.light_slider)
        self.light_label = QLabel("5.0")
        self.light_slider.valueChanged.connect(lambda v: self.light_label.setText(f"{v:.1f}"))
        light_row.addWidget(self.light_label)
        gif_layout.addLayout(light_row)

        # Resolution
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Resolution:"))
        self.res_spin = QSpinBox()
        self.res_spin.setRange(128, 1024)
        self.res_spin.setValue(512)
        self.res_spin.setSingleStep(64)
        res_row.addWidget(self.res_spin)
        gif_layout.addLayout(res_row)

        layout.addWidget(gif_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Export button
        self.export_btn = QPushButton("Export GIF")
        self.export_btn.clicked.connect(self._export_gif)
        layout.addWidget(self.export_btn)

        layout.addStretch()

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Model",
            "",
            "3D Models (*.glb *.gltf *.obj *.stl *.ply *.fbx);;All Files (*)",
        )
        if path:
            self.model_path.setText(path)
            # Auto-fill output path
            base = os.path.splitext(path)[0]
            self.output_path.setText(f"{base}.gif")

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "", "GIF Files (*.gif);;All Files (*)"
        )
        if path:
            self.output_path.setText(path)

    def _export_gif(self):
        if not self.model_path.text():
            QMessageBox.warning(self, "Error", "Please select a model file.")
            return

        if not self.output_path.text():
            QMessageBox.warning(self, "Error", "Please select an output path.")
            return

        # Gather settings
        camera = CameraSettings(zoom=self.zoom_slider.value() / 10)
        gif_settings = GifSettings(
            duration=self.duration_spin.value(),
            fps=self.fps_spin.value(),
            rotate_speed=self.speed_spin.value(),
            lighting_intensity=self.light_slider.value(),
            width=self.res_spin.value(),
            height=self.res_spin.value(),
        )

        # Start worker thread
        self.worker = GifExportWorker(
            self.model_path.text(),
            self.output_path.text(),
            camera,
            gif_settings,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_export.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting export...")

        self.worker.start()

    def _on_progress(self, current: int, total: int, message: str):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)

    def _on_finished(self, path: str):
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"GIF saved: {path}")
        QMessageBox.information(self, "Success", f"GIF exported successfully!\n\n{path}")

    def _on_error(self, error: str):
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Error", f"Export failed:\n\n{error}")


# =============================================================================
# Image Preview Tab
# =============================================================================


class ImagePreviewTab(QWidget):
    """Tab for image preview export settings and execution."""

    def __init__(self):
        super().__init__()
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Model file selection
        model_group = QGroupBox("Model")
        model_layout = QHBoxLayout(model_group)

        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("Select a 3D model file...")
        model_layout.addWidget(self.model_path)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_model)
        model_layout.addWidget(browse_btn)

        layout.addWidget(model_group)

        # Output directory selection
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Select output directory...")
        output_layout.addWidget(self.output_dir)

        output_btn = QPushButton("Browse...")
        output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(output_btn)

        layout.addWidget(output_group)

        # Options row
        options_layout = QHBoxLayout()

        # Lighting selection
        lighting_presets = {k: v.name for k, v in LightingPreset.get_presets().items()}
        self.lighting_selector = MultiSelectList("Lighting Presets", lighting_presets)
        self.lighting_selector.select_first()
        options_layout.addWidget(self.lighting_selector)

        layout.addLayout(options_layout)

        # Additional options
        additional_group = QGroupBox("Options")
        additional_layout = QVBoxLayout(additional_group)

        self.wireframe_check = QCheckBox("Include wireframe renders")
        self.wireframe_check.setChecked(True)
        additional_layout.addWidget(self.wireframe_check)

        # Resolution
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Resolution:"))
        self.res_spin = QSpinBox()
        self.res_spin.setRange(256, 2048)
        self.res_spin.setValue(800)
        self.res_spin.setSingleStep(100)
        res_row.addWidget(self.res_spin)
        res_row.addStretch()
        additional_layout.addLayout(res_row)

        # Camera zoom
        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Camera Zoom:"))
        self.zoom_slider = QSlider()
        self.zoom_slider.setOrientation(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 100)
        self.zoom_slider.setValue(20)
        zoom_row.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("2.0")
        self.zoom_slider.valueChanged.connect(lambda v: self.zoom_label.setText(f"{v / 10:.1f}"))
        zoom_row.addWidget(self.zoom_label)
        additional_layout.addLayout(zoom_row)

        layout.addWidget(additional_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Export button
        self.export_btn = QPushButton("Export Previews")
        self.export_btn.clicked.connect(self._export_previews)
        layout.addWidget(self.export_btn)

        layout.addStretch()

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Model",
            "",
            "3D Models (*.glb *.gltf *.obj *.stl *.ply *.fbx);;All Files (*)",
        )
        if path:
            self.model_path.setText(path)
            # Auto-fill output directory
            model_dir = os.path.dirname(path)
            model_name = os.path.splitext(os.path.basename(path))[0]
            self.output_dir.setText(os.path.join(model_dir, f"{model_name}_previews"))

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_dir.setText(path)

    def _export_previews(self):
        if not self.model_path.text():
            QMessageBox.warning(self, "Error", "Please select a model file.")
            return

        if not self.output_dir.text():
            QMessageBox.warning(self, "Error", "Please select an output directory.")
            return

        lighting_keys = self.lighting_selector.get_selected_keys()
        if not lighting_keys:
            QMessageBox.warning(self, "Error", "Please select at least one lighting preset.")
            return

        # Gather settings
        camera = CameraSettings(zoom=self.zoom_slider.value() / 10)
        image_settings = ImageSettings(
            width=self.res_spin.value(),
            height=self.res_spin.value(),
        )

        # Start worker thread
        self.worker = PreviewExportWorker(
            self.model_path.text(),
            self.output_dir.text(),
            camera,
            lighting_keys,
            image_settings,
            self.wireframe_check.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_export.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting export...")

        self.worker.start()

    def _on_progress(self, current: int, total: int, message: str):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)

    def _on_finished(self, paths: dict):
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        total_images = sum(len(p) for p in paths.values())
        self.status_label.setText(f"Exported {total_images} images")
        QMessageBox.information(
            self,
            "Success",
            f"Preview export complete!\n\n"
            f"Exported {total_images} images to:\n{self.output_dir.text()}",
        )

    def _on_error(self, error: str):
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Error", f"Export failed:\n\n{error}")


# =============================================================================
# Main Window
# =============================================================================


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Model Preview Generator")
        self.setMinimumSize(500, 600)
        self._setup_ui()

    def _setup_ui(self):
        # Central widget with tabs
        tabs = QTabWidget()
        tabs.addTab(GifExportTab(), "GIF Export")
        tabs.addTab(ImagePreviewTab(), "Image Previews")

        self.setCentralWidget(tabs)


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("3D Model Preview Generator")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
