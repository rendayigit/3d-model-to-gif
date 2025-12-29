"""
Core rendering module for 3D model preview generation.

This module provides functions for loading 3D models and rendering them
to images and GIFs with transparent backgrounds.
"""

import math
import os
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import trimesh
from PIL import Image
from pyrender import (
    DirectionalLight,
    Mesh,
    Node,
    OffscreenRenderer,
    OrthographicCamera,
    RenderFlags,
    Scene,
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
class GifSettings:
    """Settings for GIF generation."""

    duration: float = 4.0  # seconds
    fps: int = 15
    rotate_speed: float = 90.0  # degrees per second
    lighting_intensity: float = 5.0
    width: int = 512
    height: int = 512


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


def load_model(filepath: str) -> trimesh.Trimesh:
    """
    Load a 3D model from file.

    Args:
        filepath: Path to the 3D model file (GLB, GLTF, OBJ, etc.).

    Returns:
        Loaded trimesh object.

    Raises:
        FileNotFoundError: If the model file doesn't exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")

    return trimesh.load(filepath)


# =============================================================================
# Scene Creation
# =============================================================================


def create_scene_with_model(
    mesh: trimesh.Trimesh,
    rotation_angle: float = 0,
    wireframe: bool = False,
) -> Scene:
    """
    Create a pyrender scene with the loaded model and transparent background.

    Args:
        mesh: Loaded trimesh model.
        rotation_angle: Angle to rotate the model (degrees).
        wireframe: Whether to render in wireframe mode.

    Returns:
        Configured pyrender Scene.
    """
    # Transparent background
    scene = Scene(bg_color=[0, 0, 0, 0], ambient_light=[0.3, 0.3, 0.3])

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


# =============================================================================
# Rendering Functions
# =============================================================================


def render_single_frame(
    mesh: trimesh.Trimesh,
    camera: CameraSettings,
    lighting: LightingPreset,
    width: int,
    height: int,
    angle: float = 0,
    wireframe: bool = False,
) -> np.ndarray:
    """
    Render a single frame of the model with transparent background.

    Args:
        mesh: Loaded trimesh model.
        camera: Camera settings.
        lighting: Lighting preset.
        width: Image width.
        height: Image height.
        angle: Rotation angle in degrees.
        wireframe: Whether to render in wireframe mode.

    Returns:
        RGBA image as numpy array.
    """
    scene = create_scene_with_model(mesh, angle, wireframe)
    add_camera_to_scene(scene, camera)
    add_lighting_to_scene(scene, lighting)

    renderer = OffscreenRenderer(width, height)
    try:
        # Render with RGBA flag for transparency
        color, _ = renderer.render(scene, flags=RenderFlags.RGBA)
    finally:
        renderer.delete()

    return color


def render_image(
    model_path: str,
    output_path: str,
    camera: CameraSettings,
    lighting: LightingPreset,
    image_settings: ImageSettings,
    angle: float = 0,
    wireframe: bool = False,
) -> str:
    """
    Render a single image of the 3D model with transparent background.

    Args:
        model_path: Path to the 3D model file.
        output_path: Path to save the rendered image (PNG).
        camera: Camera settings.
        lighting: Lighting preset.
        image_settings: Image dimensions and settings.
        angle: Rotation angle in degrees.
        wireframe: Whether to render in wireframe mode.

    Returns:
        Path to the saved image.
    """
    mesh = load_model(model_path)

    color = render_single_frame(
        mesh, camera, lighting, image_settings.width, image_settings.height, angle, wireframe
    )

    # Save image with transparency
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    Image.fromarray(color).save(output_path, "PNG")

    return output_path


def render_preview_set(
    model_path: str,
    output_dir: str,
    camera: CameraSettings,
    lighting_key: str,
    image_settings: ImageSettings,
    wireframe: bool = False,
    progress_callback: Optional[callable] = None,
) -> list[str]:
    """
    Render a set of preview images from multiple angles with transparent background.

    Args:
        model_path: Path to the 3D model file.
        output_dir: Directory to save rendered images.
        camera: Camera settings.
        lighting_key: Key for the lighting preset.
        image_settings: Image settings including angles.
        wireframe: Whether to render in wireframe mode.
        progress_callback: Optional callback for progress updates.

    Returns:
        List of paths to saved images.
    """
    lighting = LightingPreset.get_presets().get(lighting_key)
    if not lighting:
        raise ValueError(f"Unknown lighting preset: {lighting_key}")

    os.makedirs(output_dir, exist_ok=True)
    saved_paths = []
    mesh = load_model(model_path)

    total = len(image_settings.angles)
    for i, angle in enumerate(image_settings.angles):
        # Build filename
        mode_suffix = "_wireframe" if wireframe else ""
        light_suffix = f"_{lighting_key}" if lighting_key != "default" else ""
        filename = f"preview_{angle:03d}deg{mode_suffix}{light_suffix}.png"
        output_path = os.path.join(output_dir, filename)

        try:
            color = render_single_frame(
                mesh,
                camera,
                lighting,
                image_settings.width,
                image_settings.height,
                angle,
                wireframe,
            )
            Image.fromarray(color).save(output_path, "PNG")
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
    image_settings: ImageSettings,
    include_wireframe: bool = True,
    progress_callback: Optional[callable] = None,
) -> dict[str, list[str]]:
    """
    Render preview sets with multiple lighting options and transparent background.

    Args:
        model_path: Path to the 3D model file.
        output_dir: Base directory for output.
        camera: Camera settings.
        lighting_keys: List of lighting preset keys to use.
        image_settings: Image settings.
        include_wireframe: Whether to include wireframe renders.
        progress_callback: Optional callback for progress updates.

    Returns:
        Dictionary mapping category names to lists of saved paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    all_paths = {}

    # Calculate total renders for progress
    total_sets = len(lighting_keys)
    if include_wireframe:
        total_sets += 1

    current_set = 0

    # Standard renders with different lighting
    for light_key in lighting_keys:
        subdir = os.path.join(output_dir, light_key)

        if progress_callback:
            progress_callback(current_set, total_sets, f"Rendering {light_key} lighting...")

        paths = render_preview_set(
            model_path, subdir, camera, light_key, image_settings, wireframe=False
        )
        all_paths[light_key] = paths
        current_set += 1

    # Wireframe renders
    if include_wireframe:
        if progress_callback:
            progress_callback(current_set, total_sets, "Rendering wireframes...")

        wireframe_dir = os.path.join(output_dir, "wireframe")
        wireframe_paths = render_preview_set(
            model_path, wireframe_dir, camera, "default", image_settings, wireframe=True
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
    Render an animated GIF of the rotating model with transparent background.

    Uses offscreen rendering (no window opens).

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

    # Calculate frames needed
    total_frames = int(gif_settings.duration * gif_settings.fps)
    degrees_per_frame = gif_settings.rotate_speed / gif_settings.fps

    # Create lighting preset from intensity
    lighting = LightingPreset("GIF", gif_settings.lighting_intensity, (1.0, 1.0, 1.0))

    frames = []

    if progress_callback:
        progress_callback(0, total_frames, "Rendering frames...")

    for i in range(total_frames):
        angle = i * degrees_per_frame

        # Render frame with transparency
        color = render_single_frame(
            mesh, camera, lighting, gif_settings.width, gif_settings.height, angle, wireframe=False
        )
        frames.append(color)

        if progress_callback:
            progress_callback(i + 1, total_frames, f"Rendering frame {i + 1}/{total_frames}")

    if progress_callback:
        progress_callback(total_frames, total_frames, "Saving GIF...")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Save as GIF with transparency
    # Convert RGBA frames to PIL Images for proper GIF transparency handling
    pil_frames = [Image.fromarray(frame) for frame in frames]

    # Save with transparency - GIF uses palette-based transparency
    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=int(1000 / gif_settings.fps),  # milliseconds per frame
        loop=0,
        transparency=0,
        disposal=2,  # Restore to background between frames
    )

    if progress_callback:
        progress_callback(total_frames, total_frames, f"GIF saved: {output_path}")

    return output_path
