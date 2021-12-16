import sys
f = open(sys.argv[1])
data = f.readlines()
f.close()

vertices = []
faces = []
vnormals = []
for l in data:
    w = l.split()
    if len(w)==0: continue
    if w[0]=='v':
        vertices.append( map(float, w[1:4]) )
    elif w[0]=='f':
        faces.append( (float(w[1])-1, float(w[2])-1, float(w[3])-1) )

from DejaVu.IndexedPolygons import IndexedPolygons
pol = IndexedPolygons('foo', vertices = vertices, faces=faces)
pol.writeToFile(sys.argv[2])
