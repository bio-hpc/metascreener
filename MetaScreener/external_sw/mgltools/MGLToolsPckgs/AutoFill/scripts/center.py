##  Author: Michel Sanner

## centers the molecule and writes a pdb file called file_centerd.pdb
##computes the bounding sphere and saves its radius it in file_bb.sph

##
## python center.py vesicleDimer1.pdb  # if in the same folder
##
## otherwise you need to cd to the alignVectMacG.py file and run with the path to the file you want to mesh:
##   python center.py /Users/grahamc4d/Desktop/AutoFillVesicleModel/CellPDBfiles/vesicleDimer1.pdb 

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

"""
Authors M Sanner

March 2010

copyright TSRI

usage: python center.py file.pdb

centers the molecule and writes a pdb file called file_centerd.pdb
computes the bounding sphere and saves its radius it in file_bb.sph
"""
from math import sqrt
import sys, os
import numpy

if len(sys.argv)<2:
    print "Usage: pytyhon %s PDBfile [x y z]"%sys.argv[0]
    sys.exit(1)

filename = sys.argv[1]
if len(sys.argv)==5:
    x = float(sys.argv[2])
    y = float(sys.argv[3])
    z = float(sys.argv[4])
    
from MolKit import Read
mols = Read(filename)

c = mols[0].allAtoms.coords
g = numpy.sum(c, 0)/len(c)
print 'center %.2f %.2f %.2f'%tuple(g)
c1 = c - g
mols[0].allAtoms.updateCoords(c1)

fname, ext = os.path.splitext(filename)

# compute bounding sphere radius
delta = c-g
delta *= delta
d2 = max(numpy.sum(delta, 1))
f = open(fname+'_bb.sph', 'w')
f.write('%.2f\n'%sqrt(d2))
f.close()

from MolKit.pdbWriter import PdbWriter
writer = PdbWriter()
writer.write(fname+'_centered.pdb', mols[0], records=['ATOM', 'HETATM'])
