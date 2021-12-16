import sys

prot = sys.argv[1]

from DejaVu import Viewer
vi = Viewer()

from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Spheres import Spheres
from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

geomS = IndexedPolygonsFromFile(prot)
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()
mesh = IndexedPolygons(prot+'mesh', vertices=vertices,
                      faces=faces, vnormals=vnormals,
                      inheritFrontPolyMode=False,
                      frontPolyMode='line',
                      inheritCulling=0, culling='none',
                      inheritShading=0, shading='flat')
vi.AddObject(mesh)

def getSpheres(prot, branch, nblevel):
    f = open('1TWT_%d_%d.sph'%(branch, nblevel))
    data = f.readlines()
    f.close()

    w = data[0].split()
    mod, sph = float(w[0]), float(w[1])
    x, y, z,r = map(float, w[2:])
    spheres = [ [(x,y,z)] ]
    radii = [ [r] ]
    linenum = 1

    for level in range(1, nblevel):
        cen = []
        rad = []
        for ln in range(branch**(level)):
            x, y, z,r = map(float, data[linenum].split()[2:])
            cen.append( (x,y,z) )
            rad.append( r)
            linenum +=1
        spheres.append(cen)
        radii.append( rad )
    return spheres, radii

spheres, radii = getSpheres('1qo1', 4, 3)

i = 1
from DejaVu.colors import green, orange, red, magenta, gold, blue, pink
colors = [ green, orange, red, magenta, gold, blue, pink ]
for c,r in zip(spheres, radii):
    sph = Spheres('level%d'%i, centers=c, radii=r,
                  frontPolyMode='line',
                  inheritMaterial=0, materials=[colors[i]],
                  inheritCulling=0, culling='none',
                  inheritShading=0, shading='flat')
    vi.AddObject(sph)
    i += 1
