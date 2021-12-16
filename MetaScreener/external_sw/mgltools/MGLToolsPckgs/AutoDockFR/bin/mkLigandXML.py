# "1HBV:A:ARG8;1HBV:B:ARG8;"
#python27 -i mkLigandXML.py 1HBV_1HBV_Lig/1HBV_Lig.pdbqt -center 2.659 7.004 -7.047 -boxDim 8.0 8.0 14.0 -o test.xml

## FIXME use getopt to handl command line parameters

import sys
from MolKit import Read
from AutoDockFR.utils import pdbqt2XML
import numpy

def usage():
    print "*******************************************************************"
    print "*                                                                 *"
    print "* convert ligand PDBQT file to XML                                *"
    print "* Usage: mkLigandXML pdbqtFile -boxDim x y z [-center [percent] [angstrom] [x2 y2 z2]]   *"
    print "*                 -auto [-o output]                               *"
    print "*                                                                 *"
    print "*  boxDim: the dimension of docking box                           *"
    print "*  center: the center of docking box                              *"
    print "*  center options:                                                *"
    print "*       percent:  add this percentage of padding to the                                        *"
    print "*       angstrom: add this                                               *"
    print "*  auto  : the center of docking box is at the root of ligand     *"
    print "*  output: output XML filename                                    *"
    print "*                                                                 *"
    print "*******************************************************************"

dims = None
auto = True
output = None
percent = None
padding = None
center = None

try:
    filename = sys.argv[1]
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == "-boxDim":
	    if sys.argv[i+1] == "percent":
	        bbmol = sys.argv[i+2]
	        percent = float(sys.argv[i+3])
                i+=3
	    elif sys.argv[i+1] == "angstrom":
	        bbmol = sys.argv[i+2]
		padding = float(sys.argv[i+3])
                i+=3
            else:
	        dims = [0,0,0]
                dims[0] = float(sys.argv[i+1])
                dims[1] = float(sys.argv[i+2])
                dims[2] = float(sys.argv[i+3])
                i+=3
        elif sys.argv[i] == "-center":
	    center = [0,0,0]
            center[0] = float(sys.argv[i+1])
            center[1] = float(sys.argv[i+2])
            center[2] = float(sys.argv[i+3])
            auto = False
            i+=3
        elif sys.argv[i] == "-auto":
            bbmol = sys.argv[i+1]
            auto=True
            i+=1
        elif sys.argv[i] == "-o":
            output=sys.argv[i+1]
            i+=1
        else:
            pass
            
except IndexError:
    usage()
    sys.exit(1)

if output is None:
    xmlFilename=filename.split('.')[0]+".xml"
else:
    xmlFilename=output

ligand = Read(filename)[0]
ligand.buildBondsByDistance()

if percent is not None or padding is not None:
    bbmol = Read(bbmol)[0]
    coords = numpy.array(bbmol.allAtoms.coords, 'f')
    mini = numpy.min(coords, 0)
    maxi = numpy.max(coords, 0)
    print mini, maxi	    
    
    dims = maxi-mini

    if percent is not None:
       dims = dims*(1+percent/100.0)
    else:
        dims += padding

#center = numpy.sum(coords, 0)/len(coords)

if auto:  # docking box center at root of ligand torTree. (redocking?)
    bbmol = Read(bbmol)[0]
    print bbmol.ROOT, bbmol.ROOT.coords
    center = bbmol.ROOT.coords
    
pdbqt2XML(filename, xmlFilename, center, list(dims))



