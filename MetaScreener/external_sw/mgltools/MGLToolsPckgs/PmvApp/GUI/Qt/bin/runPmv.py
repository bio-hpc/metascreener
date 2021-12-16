# $Header: /opt/cvs/PmvApp/GUI/Qt/bin/runPmv.py,v 1.10 2014/07/22 23:51:52 autin Exp $
# $Id: runPmv.py,v 1.10 2014/07/22 23:51:52 autin Exp $

import os, sys
sys.path.insert(0,'.')
args = sys.argv
# remove -i from the argv list:
ind = None
debug = False
for i, arg in enumerate(args):
    if arg == "-i":
        ind = i
    elif arg == "-d":
        debug = True

if ind is not None:
    args.pop(ind)
    
from PySide import QtGui, QtCore
app = QtGui.QApplication(args)

from PmvApp.GUI.Qt.PmvGUI import PmvGUI,use_ipython_shell
from PmvApp.Pmv import MolApp

pmv = MolApp()
if debug:
    pmv._stopOnError = True
    
pmv.lazyLoad('bondsCmds', package='PmvApp')
pmv.lazyLoad('fileCmds', package='PmvApp')
pmv.lazyLoad('displayCmds', package='PmvApp')
pmv.lazyLoad("colorCmds", package="PmvApp")
pmv.lazyLoad("selectionCmds", package="PmvApp")
pmv.lazyLoad('msmsCmds', package='PmvApp')
pmv.lazyLoad('deleteCmds', package='PmvApp')
pmv.lazyLoad('secondaryStructureCmds', package='PmvApp')
pmv.lazyLoad('displayHyperBallsCmds', package='PmvApp')

pmvgui = PmvGUI(pmv)
pmvgui.resize(800,600)

molNames = []
for arg in sys.argv[1:]:
    if os.path.splitext(arg)[1] in ['.pdb','.mol2','.pdbqt','.pqr','.pdbq']:
	molNames.append(arg)

mols = pmv.readMolecules(molNames)
for mol in mols:
    pmv.buildBondsByDistance(mol)

pmv.displayLines(mols)
#pmv.displayHyperBalls(pmv.Mols[0],shrink=0.01, scaleFactor = 0.26, bScale = 0.26,cpkRad=0.0)
#shrink=0.01, scaleFactor = 0.0, bScale = 1.0,cpkRad=0.3) LIC ?

#pmv.colorByAtoms(mols)
if use_ipython_shell :
    from IPython.lib import guisupport
    guisupport.start_event_loop_qt4(app)
    #pylab?
else :
    sys.exit(app.exec_())
