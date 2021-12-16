#f = open('models/lamp600-spawn.sph')
f = open('2plv-medial.sph')
data = f.readlines()
f.close()

nbs = [1,8,43,203]
nbs = [1,8,64,504]
x,y,z,r = map(float, data[1].split()[:4])
spheres = [ [(x,y,z)], ]
radii = [ [r] ]
sphCount = 0
modelCount = 1
lc = []
lr = []
for line in data[2:]:
    if line[:26]=='0.000000 0.000000 0.000000':
        continue
    x,y,z,r = map(float, line.split()[:4])
    lc.append( (x,y,z) )
    lr.append( r )
    sphCount += 1
    if sphCount==nbs[modelCount]:
        print modelCount, sphCount
        spheres.append( lc )
        radii.append( lr )
        lc = []
        lr = []
        sphCount = 0
        modelCount += 1
    if modelCount==4:
        print 'DONE', modelCount
        break

from DejaVu import Viewer
vi = Viewer()

from DejaVu.Spheres import Spheres
for i in range(len(nbs)):
    sph = Spheres('level%d'%i, centers = spheres[i], radii=radii[i])
    vi.AddObject(sph)

from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

geomS = IndexedPolygonsFromFile('2plv', 'shape')
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()

from DejaVu.IndexedPolygons import IndexedPolgons
pol = IndexedPolygons('coarse', vertices=vertices, faces=faces)
vi.AddObject(pol)
