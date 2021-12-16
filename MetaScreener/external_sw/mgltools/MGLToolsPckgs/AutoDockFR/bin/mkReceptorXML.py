#python27 mkReceptorXML.py 1HBV_1HBV_Lig/1HBV.pdbqt -rotSC "1HBV:A:ARG8;1HBV:B:ARG8;" -o testRecFlex.xml


import os, sys
##
## 
from MolKit import Read

def usage():
    print "*******************************************************************"
    print "*                                                                 *"
    print "* convert receptor PDBQT file to XML                              *"
    print "* Usage: mkReceptorXML pdbqtFile [-rotSC flexibleSideChains]      *"
    print "*            [-o output]                                          *"
    print "*                                                                 *"
    print "*  pdbqtFile: receptor pdbqt                                      *"
    print "*  flexibleSideChains: selection string for rotameric SC          *"
    print "*  output: output XML filename                                    *"
    print "*                                                                 *"
    print "*******************************************************************"

flexSC = None
output = None
try:
    filename = sys.argv[1]
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == "-rotSC":
            flexSC = sys.argv[i+1]
            i+=1
        elif sys.argv[i] == "-o":
            output=sys.argv[i+1]
            i+=1
        else:
            pass
            
except IndexError:
    usage()
    sys.exit(1)

mol = Read(filename)[0]
mol.buildBondsByDistance()

if output is None:
    output = os.path.basename(os.path.splitext(filename)[0])+'.xml'

if flexSC:
    from FlexTree.FTConstruction import FTParam, GenerateFT
    ftp = FTParam()
    ftp.kw['movingSidechains'] = flexSC
    gg = GenerateFT(ftp, mol=mol)
    tree = tree = gg.getTree()
else:
    from AutoDockFR.utils import rigidReceptor2XML
    tree = rigidReceptor2XML(mol)
    
tree.save(output)
