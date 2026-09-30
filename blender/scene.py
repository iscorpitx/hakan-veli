import bpy, math

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def mat(name, color, metallic=0.0, rough=0.4, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 6
    return m

# Zemin
bpy.ops.mesh.primitive_plane_add(size=40)
bpy.context.object.data.materials.append(mat("Zemin", (0.05, 0.05, 0.07), rough=0.25))

# Ortada altın küre (pürüzsüz)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=64, ring_count=32)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(mat("Altin", (1.0, 0.72, 0.3), metallic=1, rough=0.15))

# Etrafında dönen renkli küpler (bevel modifier ile yumuşak kenar)
colors = [(0.9, 0.15, 0.2), (0.1, 0.5, 0.95), (0.15, 0.8, 0.4), (0.95, 0.5, 0.1), (0.6, 0.2, 0.9)]
for i, c in enumerate(colors):
    a = i / len(colors) * 2 * math.pi
    bpy.ops.mesh.primitive_cube_add(size=0.7, location=(2.6 * math.cos(a), 2.6 * math.sin(a), 0.35),
                                    rotation=(0, 0, a + 0.4))
    o = bpy.context.object
    bev = o.modifiers.new("Bevel", "BEVEL"); bev.width = 0.08; bev.segments = 4
    o.data.materials.append(mat(f"Kup{i}", c, rough=0.3))

# Işıyan halka
bpy.ops.mesh.primitive_torus_add(major_radius=1.6, minor_radius=0.04, location=(0, 0, 1))
bpy.context.object.rotation_euler = (math.radians(70), 0, math.radians(20))
bpy.context.object.data.materials.append(mat("Neon", (0, 0, 0), emit=(0.2, 0.8, 1.0)))

# Işıklar
bpy.ops.object.light_add(type="AREA", location=(4, -4, 6))
l = bpy.context.object; l.data.energy = 900; l.data.size = 4
l.rotation_euler = (math.radians(45), 0, math.radians(45))
bpy.ops.object.light_add(type="AREA", location=(-5, 3, 3))
l = bpy.context.object; l.data.energy = 300; l.data.color = (0.5, 0.6, 1.0)
l.rotation_euler = (math.radians(70), 0, math.radians(-120))

# Dünya (hafif mavi ortam)
world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.025, 0.04, 1)

# Kamera
bpy.ops.object.camera_add(location=(0, -7.5, 3.4))
cam = bpy.context.object
cam.rotation_euler = (math.radians(74), 0, 0)
cam.data.lens = 40
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = 7.8
cam.data.dof.aperture_fstop = 2.8
scene.camera = cam

# Render ayarları
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.view_settings.view_transform = "AgX"
scene.render.filepath = "//blender_render.png"
bpy.ops.render.render(write_still=True)
print("OK")
