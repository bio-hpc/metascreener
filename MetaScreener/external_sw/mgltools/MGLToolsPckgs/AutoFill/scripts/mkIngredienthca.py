def coarseMolSurface(coords, radii, XYZd, isovalue=7.0, resolution=-0.3,
                     padding=0.0, name='CoarseMolSurface'):
    """
    coarseMolSurface compute a coarse molecular surface for a specified set of
    spheres
    molFrag is the molecule nodes from which the surface will be computed
    isovalue, resolution, padding are the options for the computation
    name is the name of the indexedGeom
    XYZd is the grid dimension
    """

    # blur atoms on grid
    from UTpackages.UTblur import blur
    import numpy.oldnumeric as Numeric
    volarr, origin, span = blur.generateBlurmap(
        coords, radii, XYZd,resolution, padding = padding)
    volarr.shape = (XYZd[0],XYZd[1],XYZd[2])
    volarr = Numeric.ascontiguousarray(Numeric.transpose(volarr), 'f')

    weights =  Numeric.ones(len(radii), typecode = "f")
    h = {}
    from Volume.Grid3D import Grid3DF
    maskGrid = Grid3DF( volarr, origin, span , h)
    h['amin'], h['amax'],h['amean'],h['arms']= maskGrid.stats()

    #(self, grid3D, isovalue=None, calculatesignatures=None, verbosity=None)
    from UTpackages.UTisocontour import isocontour
    isocontour.setVerboseLevel(0)

    data = maskGrid.data

    origin = Numeric.array(maskGrid.origin).astype('f')
    stepsize = Numeric.array(maskGrid.stepSize).astype('f')
    # add 1 dimension for time steps amd 1 for multiple variables
    if data.dtype.char!=Numeric.Float32:
        print 'converting from ', data.dtype.char
        data = data.astype('f')#Numeric.Float32)

    newgrid3D = Numeric.ascontiguousarray(
        Numeric.reshape( Numeric.transpose(data),
                         (1, 1)+tuple(data.shape) ), data.dtype.char)
    
    ndata = isocontour.newDatasetRegFloat3D(newgrid3D, origin, stepsize)

 
    isoc = isocontour.getContour3d(ndata, 0, 0, isovalue,
                                   isocontour.NO_COLOR_VARIABLE)
    vert = Numeric.zeros((isoc.nvert,3)).astype('f')
    norm = Numeric.zeros((isoc.nvert,3)).astype('f')
    col = Numeric.zeros((isoc.nvert)).astype('f')
    tri = Numeric.zeros((isoc.ntri,3)).astype('i')
    isocontour.getContour3dData(isoc, vert, norm, col, tri, 0)
    #print vert

    if maskGrid.crystal:
        vert = maskGrid.crystal.toCartesian(vert)
	
    from DejaVu.IndexedGeom import IndexedGeom
    from DejaVu.IndexedPolygons import IndexedPolygons
    g=IndexedPolygons(name=name)
    #print g
    inheritMaterial = None
    g.Set(vertices=vert, faces=tri, materials=None, 
          tagModified=False, 
          vnormals=norm, inheritMaterial=inheritMaterial )

    return g


def isoValueFromResolution(resolution):
    """
    Piecewise linear interpretation on isovalue that is a function of blobbyness.
    """
    X = [-3.0, -2.5, -2.0, -1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1]
    Y = [0.6565, 0.8000, 1.0018, 1.3345, 1.5703, 1.8554, 2.2705, 2.9382, 4.1485, 7.1852, 26.5335]
    if resolution<X[0] or resolution>X[-1]:
        print "WARNING: Fast approximation :blobbyness is out of range [-3.0, -0.1]"
        return None
    i = 0
    while resolution > X[i]:
        i +=1
    x1 = X[i-1]
    x2 = X[i]
    dx = x2-x1
    y1 = Y[i-1]
    y2 = Y[i]
    dy = y2-y1
    return y1 + ((resolution-x1)/dx)*dy


def writeObj(filename, coarseMesh):

    vertices = coarseMesh.getVertices()
    vnormals = coarseMesh.getVNormals()
    faces = coarseMesh.getFaces()

    f = open(filename, 'w')
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


def getSpheres(filename):
    f = open(filename)
    data = f.readlines()
    f.close()

    depth, branch = map(int, data[0].split())

    # get level 1 sphere
    x,y,z,r = map(float, data[1].split()[:4])
    spheres = [ [(x,y,z)], ]
    radii = [ [r] ]

    sphCount = 0
    modelCount = 1
    lc = []
    lr = []
    for line in data[2:]:
        if line[:26]=='0.000000 0.000000 0.000000': # skip invalid spheres
            continue
        x,y,z,r = map(float, line.split()[:4])
        lc.append( (x,y,z) )
        lr.append( r )
        sphCount += 1
        if sphCount==branch**modelCount:
            print modelCount, sphCount
            spheres.append( lc )
            radii.append( lr )
            lc = []
            lr = []
            sphCount = 0
            modelCount += 1
        if modelCount==depth:
            print 'DONE', modelCount
            break
    return spheres, radii


def computeMesh(mol, resolution=-0.1, smooth=16):

    # get atomic coordinates
    from MolKit.molecule import Atom
    atoms = mols.findType(Atom)
    coords = atoms.coords
    radii = [6.0]*len(coords)

    isolvalue = isoValueFromResolution(resolution)
    coarseMesh = coarseMolSurface(coords, radii, [smooth,smooth,smooth],
                                  isovalue=isolvalue, resolution=resolution,
                                  padding=0.0, name='CoarseMolSurface')

    return coarseMesh


def computeSpheresRange(minNbSph=1, maxNbSph=4, resolution=-0.1, smooth=16):

    import os, sys
    spheres = []
    radii = []
    first = max(2, minNbSph)
    for i in range(first, maxNbSph):
        os.system('/mgl/ms1/people/sanner/src/spheretree-dist-1.0/src/makeTreeMedial -depth 2 -branch %d tmpCoarseMesh.obj'%(i))
        sph, rad = getSpheres('tmpCoarseMesh-medial.sph')
        if i==first:
            spheres.append(sph[0])
            radii.append(rad[0])
        spheres.append(sph[1])
        radii.append(rad[1])

    return spheres, radii


def saveSpheresRange(filename, spheres, radii):
    f = open(filename, 'w')
    modNum = 1
    for sphs, rads in zip(spheres, radii):
        sphNum = 1
        for center, rad in zip(sphs, rads):
            f.write("%d %d %f %f %f %f\n"%( modNum, sphNum, center[0],
                                            center[1], center[2], rad))
            sphNum += 1
        modNum += 1
    f.close()


def computeSpheres(nbSph=4, nbModels=3, resolution=-0.1, smooth=16):

    import os
    os.system('/mgl/ms1/people/sanner/src/spheretree-dist-1.0/src/makeTreeMedial -depth %d -branch %d tmpCoarseMesh.obj'%(nbModels, nbSph))
    sph, rad = getSpheres('tmpCoarseMesh-medial.sph')

    return sph, rad


def saveSpheres(filename, spheres, radii):
    f = open(filename, 'w')
    modNum = 1
    for sphs, rads in zip(spheres, radii):
        sphNum = 1
        for center, rad in zip(sphs, rads):
            f.write("%d %d %f %f %f %f\n"%( modNum, sphNum, center[0],
                                            center[1], center[2], rad))
            sphNum += 1
        modNum += 1
    f.close()


def showApprox(vi, spheres, radii, coarseMesh):
    from DejaVu.Spheres import Spheres
    from DejaVu.colors import green, orange, red, magenta, gold, blue, pink
    colors = [ green, orange, red, magenta, gold, blue, pink ]
    for i in range(len(spheres)):
        sph = Spheres('level_%d'%i, centers=spheres[i], radii=radii[i],
                      inheritMaterial=0, materials=[colors[i]],
                      inheritFrontPolyMode=0, frontPolyMode='line')
        vi.AddObject(sph)

    coarseMesh.Set(inheritShading=0, shading='flat')
    vi.AddObject(coarseMesh)
    
    
# cyto 1ABL resolution=-0.3, 

if __name__=='__main__':
    import sys, os
    import numpy
    from MolKit import Read
    mols = Read(sys.argv[1])
    nbSph = int(sys.argv[2])
    nbModels = int(sys.argv[3])
    #mini = int(sys.argv[2])
    #maxi = int(sys.argv[3])

    from time import time
    t1 = time()
    coarseMesh = computeMesh(mols[0], smooth=32)

    # center mesh
    verts = coarseMesh.getVertices()
    meshCenter = numpy.sum(verts, 0)/len(verts)
    vertsCentered = verts-meshCenter
    coarseMesh.Set(vertices=vertsCentered)
    
    writeObj('tmpCoarseMesh.obj', coarseMesh)
    t_0 = time()-t1
    
    #sph, rads = computeSpheresRange(minNbSph= mini, maxNbSph=maxi)
    #name = "%s_%d_%d"%(os.path.basename(sys.argv[1])[:-4], mini, maxi)
    #saveSpheresRange(name, sph, rads)

    t1 = time()
    sph, rads = computeSpheres(nbSph=nbSph, nbModels=nbModels)
    t_1 = time()-t1

    # restore mesh coords
    coarseMesh.Set(vertices=verts)

    # move spheres
    spheres = []
    dx, dy, dz  = meshCenter
    for sphs in sph:
        l = []
        for c in sphs:
            l.append( (c[0]+dx, c[1]+dy, c[2]+dz) )
        spheres.append(l)

    name = "%s_%d_%d.sph"%(os.path.basename(sys.argv[1])[:-4], nbSph, nbModels)
    saveSpheres(name, spheres, rads)

    print 'mk mesk', t_0
    print 'mk spheres', t_1

    from DejaVu import Viewer
    vi = Viewer()

    showApprox(vi, spheres, rads, coarseMesh)

# 1ABL: 1 sphere resolution=-0.1, smooth=16
# 1AON: 30 spheres
