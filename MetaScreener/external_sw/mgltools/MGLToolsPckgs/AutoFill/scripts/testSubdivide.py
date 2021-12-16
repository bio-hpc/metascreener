from DejaVu.IndexedPolygons import IndexedPolygonsFromFile
from DejaVu.IndexedPolygons import IndexedPolygons

geomT = IndexedPolygonsFromFile('TubeOrganelle', 'tubeOrga')
faces = geomT.getFaces()
vertices = geomT.getVertices()
vnormals = geomT.getVNormals()

from DejaVu import Viewer
vi = Viewer()

srf = IndexedPolygons('surfaceMesh', vertices=vertices,
                      faces=faces, vnormals=vnormals,
                      inheritFrontPolyMode=False,
                      frontPolyMode='line',
                      inheritCulling=0, culling='none',
                      inheritShading=0, shading='flat')
vi.AddObject(srf)

lverts = []
labels = []
for fnum,t in enumerate(faces):
    p1 = vertices[t[0]]
    p2 = vertices[t[1]]
    p3 = vertices[t[2]]
    lverts.append( ( (p1[0]+p2[0]+p3[0])/3., (p1[1]+p2[1]+p3[1])/3.,
                     (p1[2]+p2[2]+p3[2])/3. ) )
    labels.append( str(fnum) )

from DejaVu.glfLabels import GlfLabels
lab = GlfLabels('facenum', vertices=lverts, labels=labels, visible=0)
vi.AddObject(lab)

from ray import vdiff, vlen, vcross
import pdb

def createSurfacePoints( vertices, faces, vnormals, maxl=20):
    """
    create points inside edges and faces with max distance between then maxl
    return a list of of tuples wher each tuple provides the following info
    for a surface point:
        surface point coordinates
        surface point normal
    """

    points = list(vertices)[:]
    normals = list(vnormals)[:]
    
    # create points in edges
    edges = {}
    for fn, tri in enumerate(faces):
        s1,s2 = tri[0],tri[1]
        if edges.has_key( (s2, s1) ):
            edges[(s2,s1)].append(fn)
        else:
            edges[(s1,s2)] = [fn]

        s1,s2 = tri[1],tri[2]
        if edges.has_key( (s2, s1) ):
            edges[(s2,s1)].append(fn)
        else:
            edges[(s1,s2)] = [fn]

        s1,s2 = tri[2],tri[0]
        if edges.has_key( (s2, s1) ):
            edges[(s2,s1)].append(fn)
        else:
            edges[(s1,s2)] = [fn]

    lengths = map(len, edges.values())
    assert max(lengths)==2
    assert min(lengths)==2

    for edge, faceInd in edges.items():
        s1, s2 = edge
        p1 = vertices[s1]
        p2 = vertices[s2]
        v1 = vdiff(p2, p1) # p1->p2
        l1 = vlen(v1)
        if l1 <= maxl: continue

        # compute number of points
        nbp1 = int(l1 / maxl)
        if nbp1<1: continue

        # compute interval size to spread the points
        dl1 = l1/(nbp1+1)

        # compute interval vector
        dx1 = dl1*v1[0]/l1
        dy1 = dl1*v1[1]/l1
        dz1 = dl1*v1[2]/l1
        x, y, z = p1
        nx1, ny1, nz1 = vnormals[s1]
        nx2, ny2, nz2 = vnormals[s2]
        edgeNorm = ( (nx1+nx2)*.5,  (ny1+ny2)*.5,  (nz1+nz2)*.5 )
        for i in range(1, nbp1+1):
            points.append( (x + i*dx1, y + i*dy1, z + i*dz1) )
            normals.append( edgeNorm )
            
    for fn,t in enumerate(faces):
        #if t[0]==16 and t[1]==6 and t[2]==11:
        #    pdb.set_trace()
        pa = vertices[t[0]]
        pb = vertices[t[1]]
        pc = vertices[t[2]]

        va = vdiff(pb, pa) # p1->p2
        la = vlen(va)
        if la <= maxl: continue

        vb = vdiff(pc, pb) # p2->p3
        lb = vlen(vb)
        if lb <= maxl: continue

        vc = vdiff(pa, pc) # p3->p1
        lc = vlen(vc)
        if lc <= maxl: continue

        #if fn==0:
        #    pdb.set_trace()
        # pick shortest edge to be second vector
        if la<=lb and la<=lc:
            p1 = pc
            p2 = pa
            p3 = pb
            v1 = vc
            l1 = lc
            v2 = va
            l2 = la
            v3 = vb

        if lb<=la and lb<=lc:
            p1 = pa
            p2 = pb
            p3 = pc
            v1 = va
            l1 = la
            v2 = vb
            l2 = lb
            v3 = vc
            
        if lc<=lb and lc<=la:
            p1 = pb
            p2 = pc
            p3 = pa
            v1 = vb
            l1 = lb
            v2 = vc
            l2 = lc
            v3 = va
            
        lengthRatio = l2/l1

        nbp1 = int(l1 / maxl)
        if nbp1<1: continue

        dl1 = l1/(nbp1+1)
        #if dl1<15:
        #    pdb.set_trace()
        #print l1, nbp1, dl1, lengthRatio
        dx1 = dl1*v1[0]/l1
        dy1 = dl1*v1[1]/l1
        dz1 = dl1*v1[2]/l1
        x,y,z = p1
        fn = vcross(v1, (-v3[0], -v3[1], -v3[2]) )
        fnl = 1.0/vlen(fn)
        faceNorm = ( (fn[0]*fnl, fn[1]*fnl, fn[2]*fnl) )
        
        for i in range(1, nbp1+1):
            l2c = (i*dl1)*lengthRatio
            nbp2 = int(l2c/maxl)
            percentage = (i*dl1)/l1
            #nbp2 = int(l2*lengthRatio*percentage/maxl)
            if nbp2<1: continue
            #dl2 = l2*percentage/(nbp2+1)
            dl2 = l2c/(nbp2+1)
            #print '   ',i, percentage, dl1, l2c, dl2, nbp2, l2
            #if dl2<15:
            #    pdb.set_trace()

            dx2 = dl2*v2[0]/l2
            dy2 = dl2*v2[1]/l2
            dz2 = dl2*v2[2]/l2
            for j in range(1, nbp2+1):
                points.append( (
                    x + i*dx1 + j*dx2, y + i*dy1 + j*dy2, z + i*dz1 + j*dz2) )
                normals.append(faceNorm)

    return points, normals

points, normals = createSurfacePoints( vertices, faces, vnormals, maxl=20)

from DejaVu.Points import Points
pts = Points('facePts', vertices=points, pointWidth=4, inheritPointWidth=0,
              materials=( (1,0,0),), inheritMaterial=0)
vi.AddObject(pts)

from DejaVu.Polylines import Polylines
v = []
for p, n in zip(points, normals):
    x, y, z = p
    nx, ny, nz = n
    v.append( ( (x,y,z), (x+20*nx, y+20*ny, z+20*nz) ) )
    
normg = Polylines('normals', vertices=v)
vi.AddObject(normg)

## fpts = Points('facePts', vertices=facePoints, pointsize=4, inheritPointsize=0,
##               materials=( (1,0,0),), inheritMaterial=0)
## vi.AddObject(fpts)
## epts = Points('edgePts', vertices=edgePoints, pointsize=4, inheritPointsize=0,
##               materials=( (0,1,0),), inheritMaterial=0)
## vi.AddObject(epts)
    
