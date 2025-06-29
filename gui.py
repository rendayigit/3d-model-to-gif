"""
PySide6 GUI for 3d-model-to-gif
"""

import sys
import math
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
)
import run_me


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Model to GIF Converter")
        self.setMinimumWidth(400)
        self.ui_layout = QVBoxLayout()

        # Model file selection
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit(run_me.MESH_SOURCE)
        file_btn = QPushButton("Browse...")
        file_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(QLabel("3D Model (.glb):"))
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(file_btn)
        self.ui_layout.addLayout(file_layout)

        # Output GIF name and path (moved here)
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit(run_me.OUTPUT_GIF)
        output_btn = QPushButton("Browse...")
        output_layout.addWidget(QLabel("Output GIF:"))
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_btn)
        self.ui_layout.addLayout(output_layout)
        output_btn.clicked.connect(self.browse_output)

        # Camera zoom
        zoom_layout = QHBoxLayout()
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(-100, 100)
        self.zoom_spin.setValue(run_me.CAMERA_ZOOM)
        zoom_layout.addWidget(QLabel("Camera Zoom:"))
        zoom_layout.addWidget(self.zoom_spin)
        self.ui_layout.addLayout(zoom_layout)

        # Camera X/Y
        camxy_layout = QHBoxLayout()
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-100, 100)
        self.x_spin.setValue(run_me.CAMERA_X)
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-100, 100)
        self.y_spin.setValue(run_me.CAMERA_Y)
        camxy_layout.addWidget(QLabel("Camera X:"))
        camxy_layout.addWidget(self.x_spin)
        camxy_layout.addWidget(QLabel("Y:"))
        camxy_layout.addWidget(self.y_spin)
        self.ui_layout.addLayout(camxy_layout)

        # Lighting intensity
        light_layout = QHBoxLayout()
        self.light_spin = QDoubleSpinBox()
        self.light_spin.setRange(0, 100)
        self.light_spin.setValue(run_me.LIGHTING_INTENSITY)
        light_layout.addWidget(QLabel("Lighting Intensity:"))
        light_layout.addWidget(self.light_spin)
        self.ui_layout.addLayout(light_layout)

        # Rotate rate
        rotate_layout = QHBoxLayout()
        self.rotate_spin = QDoubleSpinBox()
        self.rotate_spin.setRange(0, 360)
        self.rotate_spin.setSuffix(" °/s")
        # Convert radians/sec to degrees/sec for display
        self.rotate_spin.setValue(run_me.ROTATE_RATE * 180 / math.pi)
        rotate_layout.addWidget(QLabel("Rotate Rate (deg/s):"))
        rotate_layout.addWidget(self.rotate_spin)
        self.ui_layout.addLayout(rotate_layout)

        # Refresh rate
        refresh_layout = QHBoxLayout()
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(1, 60)
        self.refresh_spin.setValue(run_me.REFRESH_RATE)
        refresh_layout.addWidget(QLabel("Refresh Rate (fps):"))
        refresh_layout.addWidget(self.refresh_spin)
        self.ui_layout.addLayout(refresh_layout)

        # Animation duration
        duration_layout = QHBoxLayout()
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 60)
        self.duration_spin.setValue(run_me.ANIMATION_DURATION)
        duration_layout.addWidget(QLabel("Animation Duration (s):"))
        duration_layout.addWidget(self.duration_spin)
        self.ui_layout.addLayout(duration_layout)


        # Run button
        self.run_btn = QPushButton("Create GIF")
        self.run_btn.clicked.connect(self.run_conversion)
        self.ui_layout.addWidget(self.run_btn)

        self.status_label = QLabel()
        self.ui_layout.addWidget(self.status_label)

        self.setLayout(self.ui_layout)

    def browse_output(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Select Output GIF", self.output_edit.text(), "GIF Files (*.gif)"
        )
        if file:
            if not file.lower().endswith(".gif"):
                file += ".gif"
            self.output_edit.setText(file)

    def browse_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select 3D Model", "", "3D Model Files (*.glb *.gltf)"
        )
        if file:
            self.file_edit.setText(file)
            self.output_edit.setText(file.rsplit(".", 1)[0] + ".gif")

    def run_conversion(self):
        # Set parameters in run_me
        run_me.MESH_SOURCE = self.file_edit.text()
        run_me.OUTPUT_GIF = self.output_edit.text()
        run_me.CAMERA_ZOOM = self.zoom_spin.value()
        run_me.CAMERA_X = self.x_spin.value()
        run_me.CAMERA_Y = self.y_spin.value()
        run_me.LIGHTING_INTENSITY = self.light_spin.value()
        # Convert degrees/sec from GUI to radians/sec for script
        run_me.ROTATE_RATE = self.rotate_spin.value() * math.pi / 180
        run_me.REFRESH_RATE = self.refresh_spin.value()
        run_me.ANIMATION_DURATION = self.duration_spin.value()
        try:
            run_me.main()
            self.status_label.setText(f"GIF saved as '{run_me.OUTPUT_GIF}'")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
