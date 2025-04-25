"""
Python script to load a 3D model, display it in a viewer, and save the output as a GIF.
"""

import time
import math
import trimesh
from pyrender import Mesh, Scene, Viewer, Node, OrthographicCamera
import imageio
import numpy as np

np.infty = np.inf

# Set the 3D model file path
MESH_SOURCE = "emoji.glb"

# Set the output GIF name based on the GLB file name
OUTPUT_GIF = f"{MESH_SOURCE.rsplit('.', 1)[0]}.gif"

# Adjust camera parameters to fit your model
CAMERA_ZOOM = -2
CAMERA_X = 0.0
CAMERA_Y = 0.0

# Other parameters
LIGHTING_INTENSITY = 5.0
ROTATE_RATE = math.pi / 2.0
REFRESH_RATE = 10
ANIMATION_DURATION = 4.3  # seconds

# Create the scene with a black background
scene = Scene(bg_color=[0, 0, 0])

# Load the 3D model
mesh = trimesh.load(MESH_SOURCE)

# Add all geometries from the mesh to the pyrender scene
for name, geom in mesh.geometry.items():
    mesh_instance = Mesh.from_trimesh(geom)
    mesh_node = Node(mesh=mesh_instance, matrix=np.eye(4))
    scene.add_node(mesh_node)

# Set up an orthographic camera
camera = OrthographicCamera(xmag=1.0, ymag=1.0)
camera_node = Node(camera=camera, matrix=np.eye(4))
scene.add_node(camera_node)

# Define the camera pose
cam_pose = np.array(
    [
        [1.0, 0.0, 0.0, CAMERA_X],
        [0.0, 1.0, 0.0, CAMERA_Y],
        [0.0, 0.0, 1.0, -CAMERA_ZOOM],
        [0.0, 0.0, 0.0, 1.0],
    ]
)
scene.set_pose(camera_node, pose=cam_pose)

# Initialize the viewer with updated parameters
viewer = Viewer(
    scene,
    run_in_thread=True,
    record=True,
    rotate=True,
    use_raymond_lighting=True,
    use_direct_lighting=True,
    rotate_rate=ROTATE_RATE,
    refresh_rate=REFRESH_RATE,
    lighting_intensity=LIGHTING_INTENSITY,
    rotate_axis=[0, 1, 0],
)

# Allow the viewer to run for a few seconds
time.sleep(ANIMATION_DURATION)

# Close the viewer and save the GIF
viewer.close_external()

# Save the GIF
imageio.mimsave(OUTPUT_GIF, viewer._saved_frames, fps=REFRESH_RATE, loop=0)
print(f"GIF saved as '{OUTPUT_GIF}'")
