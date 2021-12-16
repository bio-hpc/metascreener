"""
Authors M Sanner

March 2010

copyright TSRI

usage: python mkMesh PDBFile
"""
""" Graham Modified the mesh settings 8/30/10 to make the thin proteins show up and the proteins in general very light weight.  Proteins with details like glycosylation or lipids fare best with 
isovalue = ~3, resolution = -0.3, and gridspacing between 16 and 24
Long thin proteins need higher resolution
most globular proteins work well at 
isovalue = 15, resolution = -0.1, and gridspacing between 16
if they are long and thin, reduce the isovalue to 10 or lower"""


##  Author: Michel Sanner

##  This script makes a course mesh from a PDB file and outputs vertex and face files
##    for use in AutoFill

##
## python mkMesh.py vesicleDimer1.pdb  # if in the same folder
##
## otherwise you need to cd to the alignVectMacG.py file and run with the path to the file you want to mesh:
##   python mkMesh.py /Users/grahamc4d/Desktop/AutoFillVesicleModel/CellPDBfiles/vesicleDimer1.pdb 

##  I need to set up the Python Path using Ludo's code
MGL_ROOT="/Library/MGLTools/1.5.6/"
#PLUGDIR="/Applications/MAXON/CINEMA 4D R11.5/plugins/Py4D/plugins/epmv"

#setup the python Path
import sys
import os
sys.path[0]=(MGL_ROOT+'lib/python2.5/site-packages')
sys.path.insert(0,MGL_ROOT+'/lib/python2.5/site-packages/PIL')
sys.path.append(MGL_ROOT+'/MGLToolsPckgs')
#########End Mac specific file paths

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



def coarseMolSurface(coords, radii, XYZd, isovalue=10.0, resolution=-0.1,
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


def computeMesh(coords, radii, resolution=-0.1, gridSize=16, name='NoName'):

    # get atomic coordinates
    isovalue = isoValueFromResolution(resolution)
    coarseMesh = coarseMolSurface(coords, radii, [gridSize,gridSize,gridSize],
                                  isovalue=10, resolution=resolution,
                                  padding=0.0, name=name+'_CoarseSurface')

    return coarseMesh

if __name__=='__main__':
    import sys, os
    import numpy
    from MolKit import Read
    from MolKit.molecule import Atom
    filename= sys.argv[1]
    if len(sys.argv)>2:
        ca = int(sys.argv[2])
    else:
        ca = False
    mols = Read(filename)

    from time import time
    t1 = time()

    atoms = mols.findType(Atom)
    coords = atoms.coords
    if ca:
        radii = [6]*len(atoms)
    else:
        radii = atoms.vdwRadius

    #import pdb
    #pdb.set_trace()
    coarseMesh = computeMesh(coords, radii, gridSize=20, name=mols[0].name)

    # center mesh
    verts = coarseMesh.getVertices()
    meshCenter = numpy.sum(verts, 0)/len(verts)
    print 'meshCenter %.2f %.2f %.2f'%tuple(meshCenter)

    #vertsCentered = verts-meshCenter
    #coarseMesh.Set(vertices=vertsCentered)

    fname, ext = os.path.splitext(filename)
    
    coarseMesh.writeToFile(fname)
    writeObj(fname+'.obj', coarseMesh)
    t_0 = time()-t1
    
