import sys

print sys.argv
if len(sys.argv)<3:
    print 'Usage:  python %s InMeshFile OutMeshFile'
    sys.exit(1)

from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

geomS = IndexedPolygonsFromFile(sys.argv[1], 'shape')
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()

f = open(sys.argv[2], 'w')
f.write('##\n')
f.write('## Wavefront OBJ file\n')
f.write('## Created by MeshToObj 0.1\n')
f.write('## Author Michel Sanner\n')
f.write('##\n')
f.write('g Object\n')

for v in vertices:
    f.write('v %f %f %f\n'%tuple(v))

for v in vertices:
    f.write('vt 0.0 0.0\n')

for n in vnormals:
    f.write('vn %f %f %f\n'%tuple(n))

f.write('usemtl Material\n')
for fa in faces:
    i,j,k = fa
    i+=1
    j+=1
    k+=1
    f.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n'%(i,i,i,j,j,j,k,k,k))
f.close()
