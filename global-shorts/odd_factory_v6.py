import bpy, math, os
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
s=bpy.context.scene
s.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version >= (4,2,0) else 'BLENDER_EEVEE'
s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=30
# 32 Eevee samples preserve the approved scene while fitting the hosted-runner render budget.
s.eevee.taa_render_samples=32
s.frame_start=1;s.frame_end=300
s.world.color=(0.025,0.025,0.03)
def material(name,rgb,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
steel=material('Steel',(.4,.47,.52),.8,.27)
brass=material('Brass',(.65,.38,.13),.85,.24)
black=material('Graphite',(.025,.035,.05),.4,.42)
def cyl(name,loc,r,d,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=d,location=loc)
 o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 mod=o.modifiers.new('Bevel','BEVEL');mod.width=.012;mod.segments=2
 o.data.use_auto_smooth=True if hasattr(o.data,'use_auto_smooth') else None
 # Weighted normals are optional for these flat mechanical surfaces.
 return o
def gear(name,x,y,mat):
 n=16;pts=[]
 for i in range(n):
  center=2*math.pi*i/n
  for offset,r in [(-.49,.285),(-.28,.285),(-.19,.355),(.19,.355),(.28,.285),(.49,.285)]:
   a=center+offset*2*math.pi/n;pts.append((r*math.cos(a),r*math.sin(a)))
 N=len(pts)
 vertices=[(a,b,z) for z in (-.07,.07) for a,b in pts]
 faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]
 faces.extend((i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);s.collection.objects.link(ob);ob.location=(x,y,.06);ob.data.materials.append(mat)
 bev=ob.modifiers.new('Bevel','BEVEL');bev.width=.006;bev.segments=2
 # Keep bevel, avoid unsupported weighted-normal modifier.
 cyl(name+' axle',(x,y,.20),.06,.17,black)
 return ob
for row in range(3):
 for col in range(3):
  idx=row*3+col;x=(col-1)*1.65;y=(1-row)*1.7
  cyl('Mount'+str(idx),(x,y,-.16),.82,.12,black)
  a=gear('GearA'+str(idx),x-.325,y,steel)
  b=gear('GearB'+str(idx),x+.325,y,brass)
  for frame in (1,300):
   t=(frame-1)/30*1.3
   a.rotation_euler.z=t;b.rotation_euler.z=math.pi/16+(t if idx==4 else -t)
   a.keyframe_insert(data_path='rotation_euler',index=2,frame=frame)
   b.keyframe_insert(data_path='rotation_euler',index=2,frame=frame)
bpy.ops.object.camera_add(location=(0,-10,13))
cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=7.4;s.camera=cam
for name,loc,power,size in [('Key',(1,-3,8),1600,5),('Fill',(-5,0,5),950,5),('Rim',(3,5,7),2100,4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size
 o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
os.makedirs('output',exist_ok=True)
# Keep the diagnostic and animation in the same canonical scene.
for obj in s.objects:
 if obj.type=='MESH' and obj.name.startswith('Gear'):
  assert len(obj.data.vertices)>0, 'Empty gear mesh'
assert s.frame_end-s.frame_start+1==300
s.render.image_settings.file_format='PNG'
s.frame_set(30)
if os.environ.get('ODD_FACTORY_SMOKE') == '1':
 s.render.resolution_percentage=25
 s.render.filepath=os.path.abspath('output/smoke.png')
 bpy.ops.render.render(write_still=True)
 print('SMOKE_RENDER_OK')
 raise SystemExit(0)
s.render.filepath=os.path.abspath('output/diagnostic.png')
bpy.ops.render.render(write_still=True)
s.render.resolution_percentage=100
s.render.image_settings.color_mode='RGB'
s.render.image_settings.color_depth='8'
s.render.filepath=os.path.abspath('output/frame_')
bpy.ops.render.render(animation=True)
