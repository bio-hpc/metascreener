import sys

if len(sys.argv)<3:
    print "Usage: python %s infile scale"%sys.argv[0]
    sys.exit(1)

infile = sys.argv[1]
scale = float(sys.argv[2])

# Vertices
f = open(infile+'.vert')
data = f.readlines()
f.close()

if data[0][0]=='#':
    startLine = 3
else:
    startLine = 0

f = open(infile+'.indpolvert', 'w')
vertices = []
for line in data[startLine:]:
    x,y,z,nx,ny,nz = map(float, line.split()[:6])
    f.write("%f %f %f %f %f %f\n"%(x*scale, y*scale, z*scale, nx,ny,nz))
    vertices.append( (x,y,z) )
f.close()

# Faces
from ray import vlen, vcross
def faceNormal(vertices, face):
    x1,y1,z1 = vertices[face[0]]
    x2,y2,z2 = vertices[face[1]]
    x3,y3,z3 = vertices[face[2]]
    v1 = (x2-x1, y2-y1, z2-z1)
    v2 = (x3-x1, y3-y1, z3-z1)
    normal = vcross(v1,v2)
    n1 = 1./vlen(normal)
    return  (normal[0]*n1, normal[1]*n1, normal[2]*n1)

f = open(infile+'.face')
data = f.readlines()
f.close()

f = open(infile+'.indpolface', 'w')
for line in data[startLine:]:
    i,j,k = map(int, line.split()[:3])
    nx, ny, nz = faceNormal(vertices, (i-1,j-1,k-1))
    f.write("%d %d %d %f %f %f\n"%(i-1, j-1, k-1, nx,ny,nz))
f.close()

