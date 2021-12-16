import sys

fileBase = sys.argv[1]

from DejaVu import Viewer
vi = Viewer()

from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Spheres import Spheres

from AutoFill.Ingredient import getSpheres

rmin, rmax, centers, radii, children = getSpheres(fileBase+'.sph')

from DejaVu.colors import red, green, orange, magenta, gold, blue, pink
colors = [ green, orange, red, magenta, gold, blue, pink ]

sphMin = Spheres('Min', centers=[(0,0,0)], radii=[rmin],
              frontPolyMode='line',
              inheritMaterial=0, materials=[colors[0]],
              inheritCulling=0, culling='none',
              inheritShading=0, shading='flat')
vi.AddObject(sphMin)

sphMax = Spheres('Max', centers=[(0,0,0)], radii=[rmax],
              frontPolyMode='line',
              inheritMaterial=0, materials=[colors[1]],
              inheritCulling=0, culling='none',
              inheritShading=0, shading='flat')
vi.AddObject(sphMax)

i=0
sphGeoms = []
for cs, rs in zip(centers, radii):
    sph = Spheres('level_%d'%i, centers=cs, radii=rs,
                  frontPolyMode='line',
                  inheritMaterial=0, materials=[colors[i+2]],
                  inheritCulling=0, culling='none',
                  inheritShading=0, shading='flat')
    vi.AddObject(sph)
    i += 1
    sphGeoms.append(sph)


from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

try:
    geomS = IndexedPolygonsFromFile(fileBase)
    faces = geomS.getFaces()
    vertices = geomS.getVertices()
    vnormals = geomS.getVNormals()
    mesh = IndexedPolygons(fileBase, vertices=vertices,
                           faces=faces, vnormals=vnormals,
                           inheritFrontPolyMode=False,
                           frontPolyMode='line',
                           inheritCulling=0, culling='none',
                           inheritShading=0, shading='flat')
    vi.AddObject(mesh)
except IOError:
    print 'WARNING: mesfile %s not found'%fileBase

def scaleMin(value):
    #val = (int(value)-50)/50.
    #print val, rmin, rmin*val
    val = float(value)
    print val
    sphMin.Set(radii=[val])
    
def scaleMax(value):
    #val = (int(value)-50)/50.
    #print val, rmin, rmin*val
    val = float(value)
    print val
    sphMax.Set(radii=[val])
    
import Tkinter
master = Tkinter.Toplevel()
scaleMin = Tkinter.Scale(master, label='Min Rad', command=scaleMin,
                         from_= 15, to=rmax)
scaleMin.set(rmin)
scaleMin.pack(side='left')
scaleMax = Tkinter.Scale(master, label='Max Rad', command=scaleMax,
                         from_= 15, to=3*rmax)
scaleMax.set(rmax)
scaleMax.pack(side='left')
