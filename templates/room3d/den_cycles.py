"""The den, path-traced: Blender Cycles with Poly Haven CC0 models and textures (11 Oct 2026).
   python den_cycles.py <out.png> [scale=1] [samples=128] [pass=all|lamp|tv|moon]
Assets come from /root/den-assets/dl (fetched by fetch.py / tex.py from api.polyhaven.com, CC0).
Writes the frame and <out>.quad.json (the screen's corners in 1080x1920 frame pixels)."""
import bpy, sys, json, math, mathutils, os
from bpy_extras.object_utils import world_to_camera_view
A = '/root/den-assets/dl'
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUT = argv[0]; SCALE = float(argv[1]) if len(argv) > 1 else 1; SAMPLES = int(argv[2]) if len(argv) > 2 else 128
PASS = argv[3] if len(argv) > 3 else 'all'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def model(aid, loc, rot=0, s=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f'{A}/{aid}/{aid}.gltf')
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(aid, None); sc.collection.objects.link(root)
    for o in new:
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, math.radians(rot)); root.scale = (s, s, s)
    return root

def pbr(name, tex, tile=1.0, tint=None, bump=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links
    b = n['Principled BSDF']; d = f'{A}/tex/{tex}'
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (tile, tile, tile)
    l.new(tc.outputs['UV'], mp.inputs['Vector'])
    def img(f, col):
        t = n.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(f'{d}/{f}')
        if not col: t.image.colorspace_settings.name = 'Non-Color'
        l.new(mp.outputs['Vector'], t.inputs['Vector']); return t
    c = img('Diffuse.jpg', True)
    if tint:
        mx = n.new('ShaderNodeMixRGB'); mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1
        mx.inputs[2].default_value = (*tint, 1); l.new(c.outputs['Color'], mx.inputs[1]); l.new(mx.outputs[0], b.inputs['Base Color'])
    else: l.new(c.outputs['Color'], b.inputs['Base Color'])
    l.new(img('Rough.jpg', False).outputs['Color'], b.inputs['Roughness'])
    nm = n.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = bump
    l.new(img('nor_gl.jpg', False).outputs['Color'], nm.inputs['Color']); l.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m

def plain(name, col, rough=0.5, metal=0.0, emit=None, strength=0.0, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = strength
    if trans: b.inputs['Transmission Weight'].default_value = trans
    return m

def box(name, size, loc, mat, rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name
    o.scale = size; o.rotation_euler = (0, 0, math.radians(rot)); bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(mat); return o

def plane(name, size, loc, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name
    o.scale = (*size, 1); bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1); bpy.ops.object.mode_set(mode='OBJECT')
    o.data.materials.append(mat); return o

# ---- room: back wall at y=1.0, left wall x=-1.9, floor z=0 ----
wall = pbr('wall', 'dark_paneled_wood', 1.0, tint=(0.85, 0.72, 0.6))
plane('floor', (6, 6), (0, -1, 0), (0, 0, 0), pbr('floor', 'herringbone_parquet', 1.2, tint=(0.75, 0.6, 0.48)))
plane('back', (6, 3.2), (0, 1.0, 1.6), (math.radians(90), 0, 0), wall)
plane('left', (6, 3.2), (-2.2, -1, 1.6), (math.radians(90), 0, math.radians(90)), wall)
plane('ceiling', (6, 6), (0, -1, 2.6), (math.radians(180), 0, 0), plain('ceil', (0.5, 0.45, 0.4), 0.9))
rug = plane('rug', (1.6, 1.1), (0.05, 0.05, 0.004), (0, 0, 0), pbr('rug', 'floral_jacquard', 1.5, tint=(0.42, 0.20, 0.08), bump=0.6))

# ---- furniture: a vertical slice around the set (the frame is about 1 m wide at the set) ----
TVX, TVY, TVZ = 0.0, 0.74, 0.374
oak = pbr('oak', 'dark_paneled_wood', 3.0, tint=(0.55, 0.38, 0.25), bump=0.3)
model('modern_wooden_cabinet', (0, 0.80, 0), 0, 0.55)           # credenza, 1.34 x 0.29 x 0.37
model('Television_01', (TVX, TVY, TVZ), 0, 1.0)
model('portable_cassette_player', (-0.40, 0.70, TVZ + 0.056), 18, 1.0)
model('potted_plant_02', (0.60, 0.45, 0), -30, 0.85)
box('shelf', (1.0, 0.22, 0.03), (0.18, 0.89, 1.40), oak)
model('book_encyclopedia_set_01', (-0.28, 0.90, 1.415), 0, 1.0)
model('boombox', (0.48, 0.90, 1.415), 0, 0.42)

# floor lamp of our own: brass pole, linen shade, left of the set
brass = plain('brass', (0.75, 0.55, 0.3), 0.3, 1.0)
LX, LY, LZ = -0.50, 0.86, 1.22
bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.02, location=(LX, LY, 0.01)); bpy.context.object.data.materials.append(brass)
bpy.ops.mesh.primitive_cylinder_add(radius=0.011, depth=LZ, location=(LX, LY, LZ / 2)); bpy.context.object.data.materials.append(brass)
bpy.ops.mesh.primitive_cone_add(radius1=0.21, radius2=0.13, depth=0.27, end_fill_type='NOTHING', location=(LX, LY, LZ + 0.02))
shade = bpy.context.object; mod = shade.modifiers.new('s', 'SOLIDIFY'); mod.thickness = 0.004
sm = plain('shade', (0.93, 0.80, 0.60), 0.8); shade.data.materials.append(sm)
nt = sm.node_tree; sb = nt.nodes['Principled BSDF']; tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (0.55, 0.34, 0.16, 1)
mx = nt.nodes.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.5
nt.links.new(sb.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface'])

# ---- TV screen: our own emissive plane over the tube; its corners become quad.json ----
scr = plane('screen', (0.40, 0.335), (TVX - 0.06, TVY - 0.24, TVZ + 0.2575), (math.radians(90), 0, 0),
            plain('scr', (0.02, 0.02, 0.02), 0.15, emit=(0.55, 0.7, 1.0), strength=2.5))

# ---- lights ----
def light(name, kind, loc, energy, col, size=0.1, rot=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = col
    if kind == 'AREA': d.size = size
    else: d.shadow_soft_size = size
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc
    if rot: o.rotation_euler = rot
    return o
lamp = light('lamp', 'POINT', (LX, LY, LZ), 30, (1.0, 0.64, 0.34), 0.04)
tvl = light('tvlight', 'AREA', (TVX - 0.06, TVY - 0.30, TVZ + 0.24), 6, (0.6, 0.75, 1.0), 0.4, (math.radians(-90), 0, 0))   # faces the room (-Y)
tvl.data.shape = 'RECTANGLE'; tvl.data.size = 0.40; tvl.data.size_y = 0.30
# moonlight through a venetian blind out of frame on the left: a spot with real slats in front of it
MP = mathutils.Vector((-1.5, -0.2, 2.0)); MT = mathutils.Vector((0.55, 1.0, 1.0)); md = (MT - MP).normalized()
q = md.to_track_quat('-Z', 'Y')
moon = light('moon', 'SPOT', MP, 500, (0.50, 0.64, 1.0), 0.004); moon.rotation_euler = q.to_euler(); moon.data.spot_size = math.radians(26); moon.data.spot_blend = 0.3
slat = plain('slat', (0.1, 0.1, 0.1), 0.8)
up = q @ mathutils.Vector((0, 1, 0)); side = q @ mathutils.Vector((1, 0, 0))
for i in range(-16, 17):
    c = MP + md * 1.0 + up * (i * 0.032)
    o = box('slat', (1.2, 0.016, 0.002), (0, 0, 0), slat); o.location = c
    o.rotation_euler = (q @ mathutils.Quaternion((1, 0, 0), math.radians(-25))).to_euler()
    o.visible_camera = False
# the shade glows from inside; the blind's stripes on it read wrong, so the moon does not reach it (light linking)
lc = bpy.data.collections.new('moon_receivers'); lc.objects.link(shade)
moon.light_linking.receiver_collection = lc
lc.collection_objects[0].light_linking.link_state = 'EXCLUDE'   # the only member is the shade
fill = light('fill', 'AREA', (-0.9, -1.2, 1.4), 14, (1.0, 0.70, 0.45), 1.5)   # faint warm fill, as if the lamp bounced off the room
fill.rotation_euler = (mathutils.Vector((0, 0.7, 0.4)) - fill.location).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.01, 0.012, 0.02, 1)

# ---- camera: 9:16, the set's screen in the band between the title and the sheet ----
cd = bpy.data.cameras.new('cam'); cd.lens = 45; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 36
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (0.0, -1.95, 0.98)
target = mathutils.Vector((0.0, 0.7, 0.52))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.dof.use_dof = True; cd.dof.focus_distance = (mathutils.Vector((TVX, TVY - 0.24, TVZ + 0.24)) - cam.location).length; cd.dof.aperture_fstop = 4.0

# ---- render ----
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x = int(1080 * SCALE); sc.render.resolution_y = int(1920 * SCALE); sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = OUT
if PASS != 'all':
    keep = {'lamp': lamp, 'tv': tvl, 'moon': moon, 'fill': fill}[PASS]
    for o in (lamp, tvl, moon, fill):
        if o is not keep: o.data.energy = 0
    if PASS != 'tv': scr.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0
bpy.context.view_layer.update()
quad = []
v = scr.data.vertices; ws = [scr.matrix_world @ x.co for x in v]
ws.sort(key=lambda p: -p.z); top = sorted(ws[:2], key=lambda p: p.x); bot = sorted(ws[2:], key=lambda p: p.x)
for p in [top[0], top[1], bot[1], bot[0]]:
    q = world_to_camera_view(sc, cam, p); quad.append([round(q.x * 1080, 1), round((1 - q.y) * 1920, 1)])
json.dump({'quad': quad}, open(OUT.rsplit('.', 1)[0] + '.quad.json', 'w')); print('quad', quad)
bpy.ops.render.render(write_still=True)
