import numpy
from time import time
from Ingredient import SingleSphereIngr, MultiSphereIngr
from Organelle import Organelle
from Recipe import Recipe
from HistoVol import HistoVol

import sys
sys.path.insert(0, '/mgl/ms1/people/sanner/python/dev25')


from DejaVu.colors import red, aliceblue, antiquewhite, aqua, \
     aquamarine, azure, beige, bisque, black, blanchedalmond, \
     blue, blueviolet, brown, burlywood, cadetblue, \
     chartreuse, chocolate, coral, cornflowerblue, cornsilk, \
     crimson, cyan, darkblue, darkcyan, darkgoldenrod, \
     orange, purple, deeppink, lightcoral, \
     blue, cyan, mediumslateblue, steelblue, darkcyan, \
     limegreen, darkorchid, tomato, khaki, gold, magenta
# make recipes

# 1AON ingredient
GroelIngr1 = MultiSphereIngr( .0008, name='Groel+',
                              sphereFile='recipes/cyto/1AON_centered_8.sph',
                              color=red, packingPriority=1,
                              principalVector=(0,0,1) )
GroelIngr2 = MultiSphereIngr( .0008, name='Groel-',
                              sphereFile='recipes/cyto/1AON_centered_8.sph',
                              meshFile='recipes/cyto/1AON_centered.msh',
                              color=blue, packingPriority=1,
                              principalVector=(0,0,-11) )
# Surface:
rSurf1 = Recipe()
rSurf1.addIngredient( GroelIngr1 )
rSurf1.addIngredient( GroelIngr2 )

#rSurf1.addIngredient( MultiSphereIngr(
#    .0008, [60.,48.,48.], color=orange, packingPriority=2,
#    positions=([0,0,0], [-60.,0,0], [60,0,0])))
#rSurf1.addIngredient( MultiSphereIngr(
#    .0008, [40.,32.,32.,40], color=purple, packingPriority=3,
#    positions=([0,0,0], [-40.,0,0], [40,0,0], [60,30,0])))
rSurf1.addIngredient( MultiSphereIngr(
    .0015, [24.,30.,24.], color=deeppink, packingPriority=4,
    positions=([0,0,0], [-30.,0,0], [30,0,0])))
rSurf1.addIngredient( MultiSphereIngr(
    .001, [24.,30.,24.], color=lightcoral,  packingPriority=5,
    positions=([0,0,0], [-30.,0,0], [30,0,0]),
    principalVector=(-1,0,0)))
rSurf1.addIngredient( SingleSphereIngr( .08, 20., color=gold,
                      packingPriority=6) )

#Interior:
rInt1 = Recipe()
rInt1.addIngredient( SingleSphereIngr( .0001, 80., color=blue) )
rInt1.addIngredient( SingleSphereIngr( .0001, 60., color=cyan) )
rInt1.addIngredient( SingleSphereIngr( .0001, 50., color=mediumslateblue) )
rInt1.addIngredient( SingleSphereIngr( .0001, 40., color=steelblue) )
rInt1.addIngredient( SingleSphereIngr( .003,  30., color=darkcyan) )
rInt1.addIngredient( SingleSphereIngr( .003,  20., color=blue) )

# duplicate else recipeToCompNum in fill() will be wrong
# Surface:
# 1AON ingredient
GroelIngr3 = MultiSphereIngr( .0008, name='Groel+',
                              sphereFile='recipes/cyto/1AON_centered_8.sph',
                              meshFile='recipes/cyto/1AON_centered.msh',
                              color=red, packingPriority=1,
                              principalVector=(0,0,1) )
GroelIngr4 = MultiSphereIngr( .0008, name='Groel-',
                              sphereFile='recipes/cyto/1AON_centered_8.sph',
                              color=blue, packingPriority=1,
                              principalVector=(0,0,-11) )
rSurf2 = Recipe()
rSurf2.addIngredient( GroelIngr3 )
rSurf2.addIngredient( GroelIngr4 )
#rSurf2.addIngredient( MultiSphereIngr(
#    .0008, [60.,48.,48.], color=orange, packingPriority=2,
#    positions=([0,0,0], [-60.,0,0], [60,0,0])))
#rSurf2.addIngredient( MultiSphereIngr(
#    .0008, [40.,32.,32.,40], color=purple, packingPriority=3,
#    positions=([0,0,0], [-40.,0,0], [40,0,0], [60,30,0])))
rSurf2.addIngredient( MultiSphereIngr(
    .0015, [24.,30.,24.], color=deeppink, packingPriority=4,
    positions=([0,0,0], [-30.,0,0], [30,0,0])))
rSurf2.addIngredient( MultiSphereIngr(
    .001, [24.,30.,24.], color=lightcoral, packingPriority=5,
    positions=([0,0,0], [-30.,0,0], [30,0,0]),
    principalVector=(-1,0,0)))
rSurf2.addIngredient( SingleSphereIngr( .08, 20., color=gold,
                                        packingPriority=6) )

#Interior:
rInt2 = Recipe()
rInt2.addIngredient( SingleSphereIngr( .0001, 80., color=blue) )
rInt2.addIngredient( SingleSphereIngr( .0001, 60., color=cyan) )
rInt2.addIngredient( SingleSphereIngr( .0001, 50., color=mediumslateblue) )
rInt2.addIngredient( SingleSphereIngr( .0001, 40., color=steelblue) )
rInt2.addIngredient( SingleSphereIngr( .003,  30., color=darkcyan) )
rInt2.addIngredient( SingleSphereIngr( .003,  20., color=blue) )

# Cytoplasm:
GroelIngr5 = MultiSphereIngr( .00081, name='Groel+',
                              sphereFile='recipes/cyto/1AON_centered_8.sph',
                              meshFile='recipes/cyto/1AON_centered.msh',
                              color=magenta, packingPriority=1,
                              principalVector=(0,0,1) )
rCyto = Recipe()
rCyto.addIngredient( GroelIngr5 )
#rCyto.addIngredient( SingleSphereIngr( .0001, 125., color=blueviolet,
#                                       packingPriority=1) )
rCyto.addIngredient( SingleSphereIngr( .0001,  80., color=brown) )
rCyto.addIngredient( SingleSphereIngr( .0005,  60., color=burlywood) )
rCyto.addIngredient( SingleSphereIngr( .0006,  40., color=limegreen) )
rCyto.addIngredient( SingleSphereIngr( .0001,  35., color=darkorchid) ) 
rCyto.addIngredient( SingleSphereIngr( .0002,  30., color=tomato) )
rCyto.addIngredient( SingleSphereIngr( .0006,  28., color=khaki) )
rCyto.addIngredient( SingleSphereIngr( .0001,  25., color=cornflowerblue) ) 
rCyto.addIngredient( SingleSphereIngr(  .001,  22., color=cornsilk) ) 
rCyto.addIngredient( SingleSphereIngr(   .01,  20., color=crimson) )

from DejaVu.IndexedPolygons import IndexedPolygonsFromFile

#assert o1.getMinMaxProteinSize() == (10, 45)

# create HistoVol
h1 = HistoVol()

# create and add oganelles
geomS = IndexedPolygonsFromFile('SphOrganelle', 'sphOrga')
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()
o1 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o1)

geomT = IndexedPolygonsFromFile('TubeOrganelle', 'tubeOrga')
faces = geomT.getFaces()
vertices = geomT.getVertices()
vnormals = geomT.getVNormals()

o2 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o2)

# set recipes
h1.setExteriorRecipe(rCyto)

o1.setSurfaceRecipe(rSurf1)
o1.setInnerRecipe(rInt1)

o2.setSurfaceRecipe(rSurf2)
o2.setInnerRecipe(rInt2)


print 'Bounding box', h1.boundingBox
#assert h1.smallestProteinSize == 10
#assert h1.largestProteinSize == 45

print h1.nbGridPoints

# create a Viewer
from DejaVu import Viewer
vi = Viewer()
from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
from DejaVu.Box import Box
from DejaVu.Points import Points
from DejaVu.glfLabels import GlfLabels
from DejaVu.IndexedPolygons import IndexedPolygons
from DejaVu.Polylines import Polylines

# display organelle mesh
orgaToMasterGeom = {}
for orga in h1.organelles:
    g = Geom('organelle_%d'%orga.number)
    vi.AddObject(g)
    orgaToMasterGeom[orga] = g

    tet = IndexedPolygons('surfaceMesh', vertices=orga.vertices,
                          faces=orga.faces, normals=orga.vnormals,
                          inheritFrontPolyMode=False,
                          frontPolyMode='line',
                          inheritCulling=0, culling='none',
                          inheritShading=0, shading='flat')
    vi.AddObject(tet, parent=g)

# display histo BB 
hbb = Box('histoVolBB', cornerPoints=h1.boundingBox)
vi.AddObject(hbb)

#debug Spheres
#spbgdebug = Spheres('debug', vertices=[[ 392.10198975,  304.03399658, -287.62399292]],
#                    radii=10)
#vi.AddObject(spbgdebug)

def displaySubGrid((x,y,z), radius, rad, bb, pointsInCube, h1):
    # display sphere at drop location
    sph = Spheres('dropPoint', centers=((x,y,z),(x,y,z),(x,y,z)),
                  radii=[1.0, radius,rad],
                  materials=[(1,0.5,0)], inheritMaterial=False,
                  inheritFrontPolyMode=False, frontPolyMode='line',
                  culling='none', inheritCulling=0)
    vi.AddObject(sph)

    # display BB 
    hbb = Box('dropBB', cornerPoints=bb, visible=0)
    vi.AddObject(hbb)

    # display histoVol.distToClosestSurf
    vertices = []
    for i in pointsInCube:
        vertices.append( h1.masterGridPositions[i] )

    s = Points('dropBBPoints', vertices=vertices, visible=1,
               materials=[(0,0.5,1)], inheritMaterial=False)
    vi.AddObject(s)

## uncomment to save grids
#h1.buildGrid(gridFileOut='tetra1.grid') #for radii 20 to 75

## uncomment to read grid instead of computing them
#h1.buildGrid(gridFileIn='tetra1.grid')

#h1.buildGrid(gridFileOut='tetra2.grid') #for radii 10 to 45
#h1.buildGrid(gridFileIn='tetra2.grid')

# try to specify smaller BB
mini, maxi = h1.boundingBox
#dx = maxi[0]-mini[0]
#dy = maxi[1]-mini[1]
#dz = maxi[2]-mini[2]
#bb = ( mini, (mini[0]+dx*.6, mini[1]+dy*.6, mini[2]+dz*.6) )
bb = [[-370, 50, -380], [370, 950, 0]]
print 'fill BB', bb
h1.buildGrid(boundingBox=bb, gridFileOut='2organelles_new.grid' )
#h1.buildGrid(boundingBox=bb, gridFileIn='2organelles_new.grid' )
#h1.buildGrid(boundingBox=bb, gridFileOut='2organelles_isp.grid', ) #for radii 10 to 45
#h1.buildGrid(boundingBox=bb, gridFileIn='2organelles_isp.grid', ) #for radii 10 to 45
#h1.buildGrid(boundingBox=bb, gridFileOut='2organelles_LRS_5skin.grid', ) #for radii 10 to 45
#h1.buildGrid(boundingBox=bb, gridFileIn='2organelles_LRS_5skin.grid')

#display fill box
fbb = Box('fillpBB', cornerPoints=bb, visible=1)
vi.AddObject(fbb)
from math import fabs
    
##     # display SDF field for all organelles
##     for orga in h1.organelles:
##         master = orgaToMasterGeom[orga]
##         vertsI = []
##         vertsO = []
##         vertsS = []
##         surfaceCutOff = h1.gridSpacing*0.5
##         dimx, dimy, dimz = orga.sdfDims
##         ox, oy, oz = orga.sdfOrigin
##         sx, sy, sz = orga.sdfGridSpacing
##         data = orga.sdfData
    
##         for k in range(dimz):
##             z = oz + k*sz
##             for j in range(dimy):
##                 y = oy + j*sy
##                 for i in range(dimx):
##                     d = data[i][j][k]
##                     x = ox+ i*sx
##                     if d < -surfaceCutOff:
##                         vertsI.append( (x,y,z) )
##                     elif d > surfaceCutOff:
##                         vertsO.append( (x,y,z) )
##                     else:
##                         vertsS.append( (x,y,z) )

##         pt1g = Points('sdf inside Points', vertices=vertsI, visible=0,
##                       inheritMaterial=0, materials=[(1,0,0)])
##         vi.AddObject(pt1g, parent=master)

##         pt2g = Points('sdf outside Points', vertices=vertsO, visible=0,
##                       inheritMaterial=0, materials=[(0,0,1)])
##         vi.AddObject(pt2g, parent=master)

##         pt3g = Points('sdf surface Points', vertices=vertsS, visible=0,
##                       inheritMaterial=0, materials=[(0,1,0)])
##         vi.AddObject(pt3g, parent=master)
    
##     # display distance field as points
##     vertsI = []
##     vertsO = []
##     vertsS = []
##     labels = []
##     vlab = []
##     surfaceCutOff = h1.gridSpacing*0.5
##     for i, p in enumerate(h1.masterGridPositions):
##         pt = h1.masterGridPositions[i]
##         d = h1.distToClosestSurf[i]
##         if fabs(d)< 6*h1.gridSpacing:
##             vlab.append( p)
##             labels.append( '%.2f'%d)
##         if d < -surfaceCutOff:
##             vertsI.append( p )
##         elif d > surfaceCutOff:
##             vertsO.append( p )
##         else:
##             vertsS.append( p )

##     pt1g = Points('inside Points', vertices=vertsI, visible=1,
##                   inheritMaterial=0, materials=[(1,0,0)])
##     vi.AddObject(pt1g)

##     pt2g = Points('outside Points', vertices=vertsO, visible=0,
##                   inheritMaterial=0, materials=[(0,0,1)])
##     vi.AddObject(pt2g)

##     pt3g = Points('surface Points', vertices=vertsS, visible=1,
##                   inheritMaterial=0, materials=[(0,1,0)],
##                   inheritPointWidth=0, pointWidth=4)
##     vi.AddObject(pt3g)

##     lab = GlfLabels('distanceLabs', vertices=vlab, labels=labels, visible=1)
##     vi.AddObject(lab)

#raise
# display organelle surface normals
for orga in h1.organelles:
    verts = []
    for i, p in enumerate(o1.surfacePoints):
        pt = h1.masterGridPositions[p]
        norm = o1.surfacePointsNormals[p]
        verts.append( (pt, (pt[0]+norm[0]*10, pt[1]+norm[1]*10, pt[2]+norm[2]*10) ) )

    n = Polylines('normals', vertices=verts, visible=0)
    vi.AddObject(n, parent=orgaToMasterGeom[orga])

    if hasattr(o1, 'ogsurfacePoints'):
        # display off grid surface grid points
        verts = []
        labels = []
        for i,pt in enumerate(orga.ogsurfacePoints):
            verts.append( pt )
            labels.append("%d"%i)

        s = Points('OGsurfacePts', vertices=verts, materials=[[1,1,0]],
                   inheritMaterial=0, pointWidth=3, inheritPointWidth=0,
                   visible=0)
        vi.AddObject(s, parent=orgaToMasterGeom[orga])
        labDistg = GlfLabels('OGsurfacePtLab', vertices=verts, labels=labels,
                             visible=0)
        vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])


    # display surface grid points
    verts = []
    colors = [(1,0,0)]
    labels = []
    for ptInd in orga.surfacePoints:
        verts.append( h1.masterGridPositions[ptInd])
        labels.append("%d"%ptInd)
##             if orga.insideSide[ptInd]==1:
##                 colors.append( (1,0,0) )
##             else:
##                 colors.append( (0,0,1) )
    s = Points('surfacePts', vertices=verts, materials=colors,
               inheritMaterial=0, pointWidth=4, inheritPointWidth=0,
               visible=0)
    vi.AddObject(s, parent=orgaToMasterGeom[orga])
    labDistg = GlfLabels('surfacePtLab', vertices=verts, labels=labels,
                         visible=0)
    vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])

    # display interior grid points
    verts = []
    labels = []
    for ptInd in orga.insidePoints:
        verts.append( h1.masterGridPositions[ptInd])
        labels.append("%d"%ptInd)

    s = Points('insidePts', vertices=verts, materials=[[0,1,0]],
               inheritMaterial=0, pointWidth=4, inheritPointWidth=0,
               visible=0)
    vi.AddObject(s, parent=orgaToMasterGeom[orga])

    labDistg = GlfLabels('insidePtLab', vertices=verts, labels=labels,
                         visible=0)
    vi.AddObject(labDistg, parent=orgaToMasterGeom[orga])

# display cyto grid points
# for i, grid in enumerate(h1.aSurfaceGrids):
#     verts = []
#     for vindex in grid:
#         verts.append( h1.masterGridPositions[vindex] )

# s = Points('cytoPts', vertices=verts, visible=0)
# vi.AddObject(s)

##     display interior grid points
##     labels = []
##     for i, grid in enumerate(h1.aInteriorGrids):
##         verts = []
##         for vindex in grid:
##             verts.append( h1.masterGridPositions[vindex] )
##             #labels.append("%2f"%h1.distToClosestSurf[vindex])
##             labels.append("%d"%vindex)
##     s = Points('interior%d'%i, vertices=verts,materials=((0,1,0),), inheritMaterial=False, visible=0)
##     vi.AddObject(s)

##     labDistg = GlfLabels('distanceLab', vertices=verts, labels=labels,
##                          visible=0)
##     vi.AddObject(labDistg)


vi.Reset_cb()
vi.Normalize_cb()
vi.Center_cb()
cam = vi.currentCamera
cam.master.master.geometry('%dx%d+%d+%d'%(400,400, 92, 73))
vi.update()
cam.fog.Set(enabled=1)
##
## FILL
##
raw_input('press enter to start')
t1 = time()
sph = Spheres('debugSph', inheritMaterial=False)
vi.AddObject(sph)
#h1.fill(seedNum=10, stepByStep=True, sphGeom=sph, verbose=3)
#h1.fill(seedNum=10)
#h1.fill2(seedNum=10, stepByStep=True, sphGeom=sph, verbose=2,
#         debugFunc=displaySubGrid, labDistGeom=labDistg)
#h1.fill2(seedNum=10)

#h1.fill3(seedNum=10, stepByStep=True, sphGeom=sph, verbose=2,
#         debugFunc=displaySubGrid, labDistGeom=labDistg)
h1.fill3(seedNum=10)

print 'time to fill', time()-t1
#print 'rejections:', h1.rejectionCount
h1.printFillInfo()

##     import cProfile, pstats
##     prof = cProfile.Profile()
##     prof = prof.runctx("h1.fill(seedNum=10)", globals(), locals())
##     stats = pstats.Stats(prof)
##     stats.sort_stats("time")
##     stats.print_stats(80)
##     h1.printFillInfo()

# display cytoplasm spheres
verts1 = []
radii1 = []
colors1 =[]

verts2 = [] # with mesh
radii2 = []
colors2 =[]

for pos, rot, ingr, ptInd in h1.molecules:
    if ingr.mesh:
        verts2.append( pos )
        radii2.append( ingr.minRadius)
        colors2.append( ingr.color)
    else:
        verts1.append( pos )
        radii1.append( ingr.minRadius)
        colors1.append( ingr.color)

sph = Spheres('cytoNoMeshSph', inheritMaterial=False, centers=verts1,
              materials=colors1, radii=radii1, visible=0)
vi.AddObject(sph)
sph = Spheres('cytoMeshSph', inheritMaterial=False, centers=verts2,
              materials=colors2, radii=radii2, visible=0)
vi.AddObject(sph)

# display cytoplasm meshes
meshGeoms = {}
for pos, rot, ingr, ptInd in h1.molecules:
    if ingr.mesh: # display mesh
        geom = ingr.mesh
        mat = rot.copy()
        mat[:3, 3] = pos
        if not meshGeoms.has_key(geom):
            meshGeoms[geom] = [mat]
            geom.Set(materials = [ingr.color], inheritMaterial=0)
        else:
            meshGeoms[geom].append(mat)

for geom, mats in meshGeoms.items():
    geom.Set(instanceMatrices=mats)
    vi.AddObject(geom)

#from pdb import set_trace
#raise
#pdb.set_trace()

# display organelle spheres and meshes
for orga in h1.organelles:
    g = orgaToMasterGeom[orga]
    vertsIn = []
    radiiIn = []
    colorsIn =[]
    vertsSurf = []
    radiiSurf = []
    colorsSurf =[]
    for pos, rot, ingr, ptInd in orga.molecules:
        px, ro = ingr.getXformedPositions(pos, rot, randomRot=False)
        if ingr.singleSphere:
            if ingr.compNum > 0:
                vertsSurf.append(px[0])
                radiiSurf.append(ingr.radius)
                colorsSurf.append(ingr.color)
            else:
                vertsIn.append(px[0])
                radiiIn.append(ingr.radius)
                colorsIn.append(ingr.color)

        else:
            for ii in range(len(ingr.radii)):
                if ingr.compNum > 0:
                    vertsSurf.append( px[ii] )
                    radiiSurf.append( ingr.radii[ii] )
                    colorsSurf.append( ingr.color)
                else:
                    vertsIn.append( px[ii] )
                    radiiIn.append( ingr.radii[ii] )
                    colorsIn.append( ingr.color)

    sph = Spheres('SrfSph', inheritMaterial=False, centers=vertsSurf,
                  materials=colorsSurf, radii=radiiSurf)
    vi.AddObject(sph, parent=g)
    sph = Spheres('IntSph', inheritMaterial=False, centers=vertsIn,
                  materials=colorsIn, radii=radiiIn)
    vi.AddObject(sph, parent=g)

    #from DejaVu.Ellipsoids import Ellipsoids
    #el1 = Ellipsoids('Surface', centers=ellcent, scaling = ellsca,
    #                 orientation = ellrot, materials = ellcol,
    #                 inheritMaterial=0, quality=20)
    #vi.AddObject(el1, parent=g)

for orga in h1.organelles:
    g = orgaToMasterGeom[orga]
    meshGeoms = {}
    for pos, rot, ingr, ptInd in orga.molecules:
        if ingr.mesh: # display mesh
            geom = ingr.mesh
            mat = rot.copy()
            mat[:3, 3] = pos
            if not meshGeoms.has_key(geom):
                meshGeoms[geom] = [mat]
                geom.Set(materials = [ingr.color], inheritMaterial=0)
            else:
                meshGeoms[geom].append(mat)

    for geom, mats in meshGeoms.items():
        geom.Set(instanceMatrices=mats)
        vi.AddObject(geom, parent=g)

# display histoVol.distToClosestSurf
from DejaVu.colorTool import RGBRamp, Map
verts = []
labels = []
for i, value in enumerate(h1.distToClosestSurf):
    if h1.gridPtId[i]==1:
        verts.append( h1.masterGridPositions[i] )
        labels.append("%.2f"%value)
lab = GlfLabels('distanceLab', vertices=verts, labels=labels, visible=0)
vi.AddObject(lab)

# display grid points with positive distances left
verts = []
rads = []
for pt in h1.freePointsAfterFill:
    d = h1.distancesAfterFill[pt]
    if d>19.999:
        verts.append(h1.masterGridPositions[pt])
        rads.append(d)

sph1 = Spheres('unused', centers=verts, radii=rads, inheritFrontPolyMode=0,
               frontPolyMode='line', visible=0)
vi.AddObject(sph1)
    
##     # display cytoplasm grid points
##     vertices = []
##     for vindex in h1.exteriorPoints:
##         vertices.append( h1.masterGridPositions[vindex] )

##     s = Points('exterior', vertices=vertices,materials=((0,1,1),), inheritMaterial=False)
##     vi.AddObject(s)
