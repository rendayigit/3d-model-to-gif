from pyrender import Mesh, Scene, Viewer, Node, OrthographicCamera
from io import BytesIO
import numpy as np
import trimesh, requests, time, math

scene = Scene(bg_color = [0, 0, 0])

mesh_source = "https://github.com/zekihub/3dmodels/raw/master/models/3d/bin/heart.glb"
mesh = trimesh.load(BytesIO(requests.get(mesh_source).content), file_type = 'glb')
meshInstance = Mesh.from_trimesh(list(mesh.geometry.values())[0])
meshNode = Node(mesh = meshInstance, matrix = np.eye(4))
scene.add_node(meshNode)

camera = OrthographicCamera(xmag = 1.0, ymag = 1.0)
cameraNode = Node(camera = camera, matrix = np.eye(4))
scene.add_node(cameraNode)

zoom = 2.5
x = 0.0
y = 0.3
cam_pose = np.array([
    [1.0, 0.0, 0.0, x],
    [0.0, 1.0, 0.0, y],
    [0.0, 0.0, 1.0, zoom],
    [0.0, 0.0, 0.0, 1.0]
])
scene.set_pose(cameraNode, pose = cam_pose)

viewer = Viewer(scene,
                run_in_thread = True,
                record = True,
                rotate = True,
                use_raymond_lighting = True,
                use_direct_lighting = True,
                rotate_rate = math.pi / 2.0,
                refresh_rate = 10,
                lighting_intensity = 5.0,
                rotate_axis = [0, 1, 0])

time.sleep(4)

viewer.close_external()

viewer.save_gif("out.gif")
