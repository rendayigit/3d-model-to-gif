"""
Core rendering module for 3D model preview generation.

This module provides functions for loading 3D models and rendering them
to images and GIFs with various camera, lighting, and background options.
"""

import math
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import imageio
import numpy as np
import trimesh
from PIL import Image
from pyrender import (
    DirectionalLight,
    Mesh,
    Node,
    OffscreenRenderer,
    OrthographicCamera,
    Scene,
    Viewer,
)

# Fix for numpy compatibility
np.infty = np.inf


# =============================================================================
# Configuration Data Classes
# =============================================================================


@dataclass
class CameraSettings:
    """Camera configuration for rendering."""

    zoom: float = 2.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    def get_pose_matrix(self) -> np.ndarray:
        """Generate the camera pose matrix."""
        return np.array(
            [
                [1.0, 0.0, 0.0, self.offset_x],
                [0.0, 1.0, 0.0, self.offset_y],
                [0.0, 0.0, 1.0, self.zoom],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )


@dataclass
class LightingPreset:
    """Lighting configuration preset."""

    name: str
    intensity: float
    color: tuple[float, float, float]

    @classmethod
    def get_presets(cls) -> dict[str, "LightingPreset"]:
        """Get all available lighting presets."""
        return {
            "default": cls("Default", 5.0, (1.0, 1.0, 1.0)),
            "warm": cls("Warm", 6.0, (1.0, 0.9, 0.8)),
            "cool": cls("Cool", 6.0, (0.8, 0.9, 1.0)),
            "bright": cls("Bright", 10.0, (1.0, 1.0, 1.0)),
            "dim": cls("Dim", 2.0, (1.0, 1.0, 1.0)),
            "dramatic": cls("Dramatic", 8.0, (1.0, 0.95, 0.9)),
        }


@dataclass
class BackgroundPreset:
    """Background configuration preset."""

    name: str
    color: tuple[int, int, int, int]  # RGBA
    is_transparent: bool = False
    is_gradient: bool = False
    gradient_top: tuple[int, int, int] = (50, 50, 80)
    gradient_bottom: tuple[int, int, int] = (20, 20, 40)

    @classmethod
    def get_presets(cls) -> dict[str, "BackgroundPreset"]:
        """Get all available background presets."""
        return {
            "black": cls("Black", (0, 0, 0, 255)),
            "white": cls("White", (255, 255, 255, 255)),
            "gray": cls("Gray", (128, 128, 128, 255)),
            "dark_gray": cls("Dark Gray", (64, 64, 64, 255)),
            "transparent": cls("Transparent", (0, 0, 0, 0), is_transparent=True),
            "blue": cls("Blue", (30, 60, 114, 255)),
            "gradient": cls("Gradient", (0, 0, 0, 0), is_gradient=True),
        }


@dataclass
class GifSettings:
    """Settings for GIF generation."""

    duration: float = 4.0  # seconds
    fps: int = 15
    rotate_speed: float = 90.0  # degrees per second
    lighting_intensity: float = 5.0


@dataclass
class ImageSettings:
    """Settings for static image generation."""

    width: int = 800
    height: int = 800
    angles: list[int] = field(default_factory=lambda: [0, 45, 90, 135, 180, 225, 270, 315])


# =============================================================================
# Utility Functions
# =============================================================================


def create_rotation_matrix(angle_deg: float, axis: str = "y") -> np.ndarray:
    """
    Create a 4x4 rotation matrix for the given angle around the specified axis.

    Args:
        angle_deg: Rotation angle in degrees.
        axis: Axis to rotate around ('x', 'y', or 'z').

    Returns:
        4x4 numpy array representing the rotation matrix.
    """
    angle_rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

    matrices = {
        "y": np.array([[cos_a, 0, sin_a, 0], [0, 1, 0, 0], [-sin_a, 0, cos_a, 0], [0, 0, 0, 1]]),
        "x": np.array([[1, 0, 0, 0], [0, cos_a, -sin_a, 0], [0, sin_a, cos_a, 0], [0, 0, 0, 1]]),
        "z": np.array([[cos_a, -sin_a, 0, 0], [sin_a, cos_a, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
    }
    return matrices.get(axis, np.eye(4))


def apply_gradient_background(
    image: np.ndarray,
    top_color: tuple[int, int, int] = (50, 50, 80),
    bottom_color: tuple[int, int, int] = (20, 20, 40),
) -> np.ndarray:
    """
    Apply a vertical gradient background to an image with transparency.

    Args:
        image: Input image as numpy array (with alpha channel).
        top_color: RGB color for the top of the gradient.
        bottom_color: RGB color for the bottom of the gradient.

    Returns:
        Image with gradient background applied.
    """
    height, width = image.shape[:2]
    gradient = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        ratio = y / height
        color = tuple(int(top_color[i] * (1 - ratio) + bottom_color[i] * ratio) for i in range(3))
        gradient[y, :] = color

    if image.shape[2] == 4:
        alpha = image[:, :, 3:4] / 255.0
        rgb = image[:, :, :3]
        result = (rgb * alpha + gradient * (1 - alpha)).astype(np.uint8)
        return np.concatenate([result, np.full((height, width, 1), 255, dtype=np.uint8)], axis=2)
    return image


def load_model(filepath: str) -> trimesh.Trimesh:
    """
    Load a 3D model from file.

    Args:
        filepath: Path to the 3D model file (GLB, GLTF, OBJ, etc.).

    Returns:
        Loaded trimesh object.

    Raises:
        FileNotFoundError: If the model file doesn't exist.
        ValueError: If the file format is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")

    return trimesh.load(filepath)


# =============================================================================
# Rendering Functions
# =============================================================================


def create_scene_with_model(
    mesh: trimesh.Trimesh,
    background: BackgroundPreset,
    rotation_angle: float = 0,
    wireframe: bool = False,
) -> Scene:
    """
    Create a pyrender scene with the loaded model.

    Args:
        mesh: Loaded trimesh model.
        background: Background preset to use.
        rotation_angle: Angle to rotate the model (degrees).
        wireframe: Whether to render in wireframe mode.

    Returns:
        Configured pyrender Scene.
    """
    # Determine background color for scene
    if background.is_transparent or background.is_gradient:
        bg_color = [0, 0, 0, 0]
    else:
        bg_color = [c / 255.0 for c in background.color[:3]]

    scene = Scene(bg_color=bg_color, ambient_light=[0.3, 0.3, 0.3])

    # Calculate rotation matrix
    rotation = create_rotation_matrix(rotation_angle, "y")

    # Add geometries to scene
    if hasattr(mesh, "geometry"):
        for geom in mesh.geometry.values():
            mesh_instance = Mesh.from_trimesh(geom, wireframe=wireframe)
            scene.add_node(Node(mesh=mesh_instance, matrix=rotation))
    else:
        mesh_instance = Mesh.from_trimesh(mesh, wireframe=wireframe)
        scene.add_node(Node(mesh=mesh_instance, matrix=rotation))

    return scene


def add_camera_to_scene(scene: Scene, camera_settings: CameraSettings) -> None:
    """
    Add an orthographic camera to the scene.

    Args:
        scene: The pyrender scene.
        camera_settings: Camera configuration.
    """
    camera = OrthographicCamera(xmag=1.0, ymag=1.0, znear=0.1, zfar=1000.0)
    camera_node = Node(camera=camera, matrix=camera_settings.get_pose_matrix())
    scene.add_node(camera_node)


def add_lighting_to_scene(scene: Scene, lighting: LightingPreset) -> None:
    """
    Add directional lights to the scene.

    Args:
        scene: The pyrender scene.
        lighting: Lighting preset to use.
    """
    light_directions = [
        [1, 1, 1],
        [-1, 1, 1],
        [0, -1, 1],
    ]

    for direction in light_directions:
        light = DirectionalLight(
            color=lighting.color,
            intensity=lighting.intensity,
        )
        light_pose = np.eye(4)
        light_pose[:3, 2] = np.array(direction) / np.linalg.norm(direction)
        scene.add_node(Node(light=light, matrix=light_pose))


def render_image(
    model_path: str,
    output_path: str,
    camera: CameraSettings,
    lighting: LightingPreset,
    background: BackgroundPreset,
    image_settings: ImageSettings,
    angle: float = 0,
    wireframe: bool = False,
) -> str:
    """
    Render a single image of the 3D model.

    Args:
        model_path: Path to the 3D model file.
        output_path: Path to save the rendered image.
        camera: Camera settings.
        lighting: Lighting preset.
        background: Background preset.
        image_settings: Image dimensions and settings.
        angle: Rotation angle in degrees.
        wireframe: Whether to render in wireframe mode.

    Returns:
        Path to the saved image.
    """
    mesh = load_model(model_path)

    scene = create_scene_with_model(mesh, background, angle, wireframe)
    add_camera_to_scene(scene, camera)
    add_lighting_to_scene(scene, lighting)

    # Render
    renderer = OffscreenRenderer(image_settings.width, image_settings.height)
    try:
        flags = 4 if (background.is_transparent or background.is_gradient) else 0
        color, _ = renderer.render(scene, flags=flags)
    finally:
        renderer.delete()

    # Apply gradient if needed
    if background.is_gradient:
        color = apply_gradient_background(
            color, background.gradient_top, background.gradient_bottom
        )

    # Save image
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if background.is_transparent:
        Image.fromarray(color).save(output_path, "PNG")
    else:
        imageio.imwrite(output_path, color)

    return output_path


def render_preview_set(
    model_path: str,
    output_dir: str,
    camera: CameraSettings,
    lighting_key: str,
    background_key: str,
    image_settings: ImageSettings,
    wireframe: bool = False,
    progress_callback: Optional[callable] = None,
) -> list[str]:
    """
    Render a set of preview images from multiple angles.

    Args:
        model_path: Path to the 3D model file.
        output_dir: Directory to save rendered images.
        camera: Camera settings.
        lighting_key: Key for the lighting preset.
        background_key: Key for the background preset.
        image_settings: Image settings including angles.
        wireframe: Whether to render in wireframe mode.
        progress_callback: Optional callback for progress updates.

    Returns:
        List of paths to saved images.
    """
    lighting = LightingPreset.get_presets().get(lighting_key)
    background = BackgroundPreset.get_presets().get(background_key)

    if not lighting:
        raise ValueError(f"Unknown lighting preset: {lighting_key}")
    if not background:
        raise ValueError(f"Unknown background preset: {background_key}")

    os.makedirs(output_dir, exist_ok=True)
    saved_paths = []

    total = len(image_settings.angles)
    for i, angle in enumerate(image_settings.angles):
        # Build filename
        mode_suffix = "_wireframe" if wireframe else ""
        bg_suffix = f"_{background_key}" if background_key != "black" else ""
        light_suffix = f"_{lighting_key}" if lighting_key != "default" else ""
        filename = f"preview_{angle:03d}deg{mode_suffix}{bg_suffix}{light_suffix}.png"
        output_path = os.path.join(output_dir, filename)

        try:
            render_image(
                model_path,
                output_path,
                camera,
                lighting,
                background,
                image_settings,
                angle,
                wireframe,
            )
            saved_paths.append(output_path)
        except Exception as e:
            print(f"Error rendering angle {angle}: {e}")
            continue

        if progress_callback:
            progress_callback(i + 1, total, output_path)

    return saved_paths


def render_all_previews(
    model_path: str,
    output_dir: str,
    camera: CameraSettings,
    lighting_keys: list[str],
    background_keys: list[str],
    image_settings: ImageSettings,
    include_wireframe: bool = True,
    progress_callback: Optional[callable] = None,
) -> dict[str, list[str]]:
    """
    Render comprehensive preview sets with multiple options.

    Args:
        model_path: Path to the 3D model file.
        output_dir: Base directory for output.
        camera: Camera settings.
        lighting_keys: List of lighting preset keys to use.
        background_keys: List of background preset keys to use.
        image_settings: Image settings.
        include_wireframe: Whether to include wireframe renders.
        progress_callback: Optional callback for progress updates.

    Returns:
        Dictionary mapping category names to lists of saved paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    all_paths = {}

    # Calculate total renders for progress
    total_sets = len(background_keys) * len(lighting_keys)
    if include_wireframe:
        total_sets += 1

    current_set = 0

    # Standard renders
    for bg_key in background_keys:
        for light_key in lighting_keys:
            category = f"{bg_key}_{light_key}"
            subdir = os.path.join(output_dir, category)

            if progress_callback:
                progress_callback(current_set, total_sets, f"Rendering {category}...")

            paths = render_preview_set(
                model_path, subdir, camera, light_key, bg_key, image_settings, wireframe=False
            )
            all_paths[category] = paths
            current_set += 1

    # Wireframe renders
    if include_wireframe:
        if progress_callback:
            progress_callback(current_set, total_sets, "Rendering wireframes...")

        wireframe_dir = os.path.join(output_dir, "wireframe")
        wireframe_paths = render_preview_set(
            model_path, wireframe_dir, camera, "default", "white", image_settings, wireframe=True
        )
        all_paths["wireframe"] = wireframe_paths

    return all_paths


def render_gif(
    model_path: str,
    output_path: str,
    camera: CameraSettings,
    gif_settings: GifSettings,
    progress_callback: Optional[callable] = None,
) -> str:
    """
    Render an animated GIF of the rotating model.

    Args:
        model_path: Path to the 3D model file.
        output_path: Path to save the GIF.
        camera: Camera settings.
        gif_settings: GIF animation settings.
        progress_callback: Optional callback for progress updates.

    Returns:
        Path to the saved GIF.
    """
    mesh = load_model(model_path)

    # Create scene with black background
    scene = Scene(bg_color=[0, 0, 0])

    # Add geometries
    if hasattr(mesh, "geometry"):
        for geom in mesh.geometry.values():
            mesh_instance = Mesh.from_trimesh(geom)
            scene.add_node(Node(mesh=mesh_instance, matrix=np.eye(4)))
    else:
        mesh_instance = Mesh.from_trimesh(mesh)
        scene.add_node(Node(mesh=mesh_instance, matrix=np.eye(4)))

    # Add camera
    camera_obj = OrthographicCamera(xmag=1.0, ymag=1.0, znear=0.1, zfar=1000.0)
    camera_node = Node(camera=camera_obj, matrix=camera.get_pose_matrix())
    scene.add_node(camera_node)

    # Create viewer and record
    if progress_callback:
        progress_callback(0, 100, "Starting GIF recording...")

    viewer = Viewer(
        scene,
        run_in_thread=True,
        record=True,
        rotate=True,
        use_raymond_lighting=True,
        use_direct_lighting=True,
        rotate_rate=math.radians(gif_settings.rotate_speed),
        refresh_rate=gif_settings.fps,
        lighting_intensity=gif_settings.lighting_intensity,
        rotate_axis=[0, 1, 0],
    )

    # Let the viewer run
    time.sleep(gif_settings.duration)

    if progress_callback:
        progress_callback(50, 100, "Saving GIF...")

    # Close and save
    viewer.close_external()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Save the GIF
    # Access internal frames (this is the documented way for pyrender)
    frames = viewer._saved_frames
    imageio.mimsave(output_path, frames, fps=gif_settings.fps, loop=0)

    if progress_callback:
        progress_callback(100, 100, f"GIF saved: {output_path}")

    return output_path
