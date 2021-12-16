import numpy
from time import time

import sys
if sys.platform=='win32':
    sys.path.insert(0, '..')
    sys.path.insert(0, 'C:\\Program Files\\MGLTools 1.5.6\\MGLToolsPckgs')
else:
    sys.path.insert(0, '/mgl/ms1/people/sanner/python/dev25')

from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr
from AutoFill.Organelle import Organelle
from AutoFill.Recipe import Recipe
from AutoFill.HistoVol import HistoVol

from DejaVu.colors import red, aliceblue, antiquewhite, aqua, \
     aquamarine, azure, beige, bisque, black, blanchedalmond, \
     blue, blueviolet, brown, burlywood, cadetblue, \
     chartreuse, chocolate, coral, cornflowerblue, cornsilk, \
     crimson, cyan, darkblue, darkcyan, darkgoldenrod, \
     orange, purple, deeppink, lightcoral, \
     blue, cyan, mediumslateblue, steelblue, darkcyan, \
     limegreen, darkorchid, tomato, khaki, gold, magenta, green

MSca = 18.0
# Surface:
rSurf1 = Recipe()

# outside
ingrOut = MultiSphereIngr( MSca*.001, color=gold, name='out outside',
                           sphereFile='recipes/anchor.sph',
                           packingPriority=1,
                           jitterMax=(0.2,1,1),
                           #perturbAxisAmplitude=.9,
                           principalVector=(1,0,0))
rSurf1.addIngredient(ingrOut)


#inside
ingrIn = MultiSphereIngr( MSca*.001, color=chartreuse, name='in  inside',
                           sphereFile='recipes/anchor.sph',
                           packingPriority=1,
                           jitterMax=(0.2,1,1),
                           nbJitter=20,
                           principalVector=(-1,0,0),)
#                           packingMode='close')
rSurf1.addIngredient(ingrIn)


#Cytoplasm:
rCyto1 = Recipe()
kinase0 = SingleSphereIngr( .02,  16., color=steelblue,
                            name='0ABL kinase0', nbJitter=20,
                            meshFile='recipes/cyto/1ABL_centered',
                            packingMode='close')
rCyto1.addIngredient( kinase0 )


# create HistoVol
h1 = HistoVol()

# create and add oganelles
from DejaVu.IndexedPolygons import IndexedPolygonsFromFile
geomS = IndexedPolygonsFromFile('organelles/vesicle_r20nm', 'vesicle')
faces = geomS.getFaces()
vertices = geomS.getVertices()
vnormals = geomS.getVNormals()
o1 = Organelle(vertices, faces, vnormals)
h1.addOrganelle(o1)

# set recipe
o1.setSurfaceRecipe(rSurf1)
o1.setInnerRecipe(rCyto1)

h1.setMinMaxProteinSize()
print 'Surf', rSurf1.getMinMaxProteinSize()
print 'Cyto', rCyto1.getMinMaxProteinSize()
print 'o1', o1.getMinMaxProteinSize()
print 'smallest', h1.smallestProteinSize
print 'largest', h1.largestProteinSize
print 'Bounding box', h1.boundingBox
# add padding
bb = h1.boundingBox
pad = 200.
x,y,z = bb[0]
bb[0] = [x-pad, y-pad, z-pad]
x,y,z = bb[1]
bb[1] = [x+pad, y+pad, z+pad]
print 'Bounding box with padding', h1.boundingBox

(x,y,z), maxi = h1.boundingBox
bb = [[0, y, z], maxi]

h1.buildGrid(boundingBox=bb)#, gridFileOut='1vesicle_new.grid' )
#h1.buildGrid(gridFileOut='1vesicle_new.grid' )

execfile('displayPreFill.py')

print 'gridSpacing', h1.gridSpacing
h1.printFillInfo()

raw_input('press enter to start')
t1 = time()
h1.fill3(seedNum=0)

print 'time to fill', time()-t1
h1.printFillInfo()


execfile('displayFill.py')


## for ingr, jitterList, collD1, collD2 in h1.successfullJitter:
##     print ingr.name[:4], len(ingr.positions), len(jitterList)

## len(h1.failedJitter)
## len(h1.successfullJitter)

## t1 = time()
## h1.fill3(seedNum=3.40)
## print 'time to fill', time()-t1
## h1.printFillInfo()
## execfile('displayFill.py')

## t1 = time()
## h1.fill3(seedNum=43420)
## print 'time to fill', time()-t1
## h1.printFillInfo()
## execfile('displayFill.py')
