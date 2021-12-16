##
## python alignVect.py vesicleDimer1.pdbt
##

import sys
from MolKit import Read
from MolKit.molecule import AtomSet
from math import fabs

molname = sys.argv[1]
mols = Read(molname)

radius = 200.0
radius2 = radius**2
eps = 64.0

allAtoms = mols.allAtoms
inDisc = AtomSet()
for atom in allAtoms:
    x,y,z = atom.coords
    d2 = x*x + y*y + z*z
    if fabs(d2 - radius2) < eps:
        print d2
        inDisc.append(atom)

print len(inDisc)

coordsInDics = inDisc.coords
import numpy
cx, cy, cz = center = numpy.sum( coordsInDics, 0) / len(coordsInDics)

# find max distance to center
minR = 0.
for x,y,z in coordsInDics:
    d2 = (x-cx)*(x-cx) + (y-cy)*(y-cy) + (z-cz)*(z-cz)
    if d2 > minR:
        minR = d2

from math import sqrt
print 'center of membrane', center, 'min Radius:', sqrt(minR)

from mglutil.math.rotax import rotVectToVect

# compute rotation matrix to rotate vector center to X axis
mat = rotVectToVect( center, (1,0,0) )

# add translation of -center
#mat[0][3] = -center[0]
#mat[1][3] = -center[1]
#mat[2][3] = -center[2]

## apply transformation to coordinates 

# get atomic coordinates
allCoords = numpy.ones( (len(allAtoms),4), 'f')

# translate them to ogigin
allCoords[:, :3] = allAtoms.coords - center

# apply rotation
tcoords = numpy.dot( allCoords, numpy.transpose(numpy.array( mat)))

# set the transformed atom coordinates
allAtoms.updateCoords(tcoords)

# write PDB file
from MolKit.pdbWriter import PdbWriter
writer = PdbWriter()
from os.path import splitext
a,b = splitext(molname)
writer.write(a+'Aligned'+'.pdb', mols)

f = open(a+'Aligned'+'.pdb', 'a')
f.write('REMARK Rmin %6.2f\n'%sqrt(minR))
f.close()
