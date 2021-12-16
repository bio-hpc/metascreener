#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2014
#
#########################################################################
#
# $Header: /opt/cvs/PmvApp/GUI/Qt/bin/__init__.py,v 1.2 2014/06/19 20:52:37 sanner Exp $
#
# $Id: __init__.py,v 1.2 2014/06/19 20:52:37 sanner Exp $
#
import sys

def runPmv2():
    from PySide import QtGui, QtCore
    app = QtGui.QApplication(sys.argv)

    from PmvApp.GUI.Qt.PmvGUI import PmvGUI
    from PmvApp.Pmv import MolApp

    pmv = MolApp()
    pmv.lazyLoad('bondsCmds', commands=[
        'buildBondsByDistance',],
                 package='PmvApp')
    pmv.lazyLoad('fileCmds', commands=[
        'readMolecules', 'readPmvSession', 'fetch', 'readAny', 'writePDB'],
                 package='PmvApp')
    pmv.lazyLoad('displayCmds', commands=[
        'displayLines', 'undisplayLines', 'displayCPK', 'undisplayCPK',
        'displaySticksAndBalls', 'undisplaySticksAndBalls',
        'displayBackboneTrace', 'undisplayBackboneTrace',
        'displayBoundGeom', 'undisplayBoundGeom','bindGeomToMolecularFragment',
        'showMolecules'],
                 package='PmvApp')

    cmds = ['color', 'colorByAtomType', 'colorByResidueType',
            'colorAtomsUsingDG', 'colorResiduesUsingShapely',
            'colorByChains', 'colorByMolecules', 'colorByInstance',
            'colorByProperty', 'colorRainbow', 'colorRainbowByChain',
            'colorByExpression', 'colorByLinesColor']
    pmv.lazyLoad("colorCmds", commands=cmds, package="PmvApp")
    pmv.lazyLoad("selectionCmds", package="PmvApp")


    pmv.lazyLoad('msmsCmds', package='PmvApp')

    pmvgui = PmvGUI(pmv)
    pmvgui.resize(800,600)

    ## cam = pmvgui.viewer.cameras[0]
    ## cam.Set(color=(.7,.7,.7))

    ## cursor_px = QtGui.QPixmap('/mgl/ms1/people/sanner/python/lazy/PmvApp/GUI/Icons/selectionAdd.png')
    ## #cursor_px = QtGui.QPixmap('/mgl/ms1/people/sanner/python/lazy/PmvApp/GUI/Icons/colorChooser32.png')
    ## cursor_px.setMask(cursor_px.mask())
    ## cursor = QtGui.QCursor(cursor_px)
    ## cam.setCursor(cursor)



    for arg in sys.argv[1:]:
        mols = pmv.readMolecule(arg)
        for mol in mols:
            pmv.buildBondsByDistance(mol)
        pmv.displayLines(mols)

    ## print 'DDDD', len(pmv.Mols[0].allAtoms[:-18])

    ## from time import time
    ## t0 = time()
    ## pmv.selection.set(pmv.Mols[0].allAtoms[:-18])
    ## print 'FASFD', time()-t0

    #pmvgui.createNewGroup('Group 1')
    #pmvgui.createNewGroup('Group 2')
    #pmvgui.createNewGroup('Group 3')
    #pmvgui.createNewGroup('Group 4')
    #pmvgui.createNewGroup('Group 5')
    sys.exit(app.exec_())
