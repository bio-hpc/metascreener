########################################################################
#
# Date: 2014 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
#
# $Header: /opt/cvs/PmvApp/GUI/Qt/PmvGUI.py,v 1.59 2014/09/05 22:31:24 annao Exp $
#
# $Id: PmvGUI.py,v 1.59 2014/09/05 22:31:24 annao Exp $
#
import os, sys, weakref

from PySide import QtGui, QtCore

from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet, MoleculeGroup
from MolKit.protein import Protein, Residue
from MolKit.tree import TreeNode

from mglutil.util.callback import CallbackFunction
from mglutil.util.uniq import uniq
from mglutil.util.packageFilePath import findFilePath
PMVICONPATH = findFilePath('Icons', 'PmvApp.GUI')

from DejaVu2.Spheres import Spheres
from DejaVu2.Cylinders import Cylinders
from DejaVu2.IndexedPolygons import IndexedPolygons

from PmvApp.Pmv import Selection, numOfSelectedVerticesToSelectTriangle

use_ipython_shell=False

try:
    from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
    from IPython.qt.inprocess import QtInProcessKernelManager
    from IPython.lib import guisupport
    use_ipython_shell=True
except ImportError:
    print "Warning: failed to import IPython.qt module. Cannot use IPython shell widget,\nusing PyShell instead." 


class GetNewName(QtGui.QInputDialog):
    # dialog to get one or more new names for dashboard entries
    
    # class to get unique class names
    def __init__(self, objItems, pmvGUI):
	self.pmvGUI = pmvGUI
        self.objItems = objItems
	QtGui.QInputDialog.__init__(self, pmvGUI)
	self.setInputMode(QtGui.QInputDialog.TextInput)
        if len(objItems)==1:
            obj0, item0 = objItems[0]
            if item0 is None:
                name = obj0.name
            else:
                name = item0.text(0)
            self.setLabelText('New name for %s'%name)
	else:
            itemNames = ''
            for obj, item in objItems:
                if item:
                    itemNames += item.text(0)
                else:
                    itemNames += obj.name
                itemNames += ', '
            itemNames = itemNames[:-2]
            if len(itemNames)>63:
                itemNames = itemNames[:30] + "..." + itemNames[-30:]
            self.setLabelText('New names for %s'%itemNames)
            
    def done(self, result):
        # validate names
	if result==QtGui.QDialog.Accepted:
	    names = self.textValue().encode('ascii', 'ignore').split(',')
            if len(names)==1:
                names = names*len(self.objItems)
            elif len(names)!=len(self.objItems):
		self.pmvGUI.statusBar().showMessage(self.tr(
			"for %d items to be renames provide 1 or %d comma separated names.try again..."))
                return
            else:
                # make sure the name is unique
                if len(names)!=len(uniq(names)):
                    self.pmvGUI.statusBar().showMessage(self.tr(
			"Selection names have to be unique.try again..."))
                    return

            # at this point we should have good names
            object0, item0 = self.objItems[0]
            if isinstance(object0, Selection):
                # makes sure the names do not exist yet in selections
                for name in names:
                    # FIXME: we could check against names in list of children of invisible root ?
                    if name in self.pmvGUI.pmv.namedSelections.keys() or name=='Current Selection' or \
                           name in self.pmvGUI.pmv.Mols.name:
                        self.pmvGUI.statusBar().showMessage(self.tr(
                            "Invalid name. Selection names must be unique (%s) ..try again..."%name))
                QtGui.QInputDialog.done(self, result)
	    else:
		QtGui.QInputDialog.done(self, result)
	else:
	    QtGui.QInputDialog.done(self, result)

def contentFont():
        font = QtGui.QFont()
        font.setStyleStrategy(QtGui.QFont.PreferAntialias)
 
        #if sys.platform == 'darwin':
        #    font.setPixelSize(9)
        #    font.setFamily('Arial')
        #else:
        #    font.setPixelSize(11)
        #    font.setFamily('Arial')
        font.setPixelSize(11)
        font.setFamily('Arial')
 
        return font

class GridGroup:

    def __init__(self, name, children=None):
        self.name = name
        if children is None:
            children= []
        self.children = children
    
class PmvGUI(QtGui.QMainWindow):
    
    levelLabels = [ 'M:', 'C:', 'R:', 'A:']
    _NoERROR = 0
    _WARNING = 1
    _ERROR = 2
    _EXCEPTION = 3
    
    def __init__(self, pmv, parent=None, classCamera=None, autoRedraw=True):
 	"""PmvGui constructor
"""
        self.pmv = pmv
        pmv.gui = weakref.ref(self)
        
        # if None no selection is active in the GUI
        # else is points to the active Pmv Selection object
        self.activeSelection = None
        
        QtGui.QMainWindow.__init__(self, parent)
        sb = self.statusBar()
        #b = self.execStatusWidget = QtGui.QToolButton()
        b = self.execStatusWidget = QtGui.QPushButton()
        b.setStyleSheet("QPushButton { border: none; background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #a6a6a6, stop: 0.08 #7f7f7f, stop: 0.39999 #717171, stop: 0.4 #626262, stop: 0.9 #4c4c4c, stop: 1 #333333);}")
        #b.setContentsMargins(0,0,0,0)
        #b.setFlat(True)
        #b.setIcon(QtGui.QIcon(os.path.join(PMVICONPATH, 'logWindow.png')))
        #b.setIconSize(QtCore.QSize(16,16))
        #b.resize(16, 16)
        sb.addPermanentWidget ( self.execStatusWidget, stretch = 0 )

        self.setFont(contentFont())
        self.groups = {}
        self.setWindowTitle('PMV2_Qt')
        self.createDockedtWidgets()
        self.createActions()
        b.released.connect(self.displayReports)
        self.createMenus()
        self.createToolBar()
        self.createStatusBar()
        self.registerListerners()
        self.show()

        # create a crossSet geom for showing selections
        from DejaVu2.Points import CrossSet
        self.selectionCrosses = g = CrossSet(
            'selectionCrosses', shape=(0,3), materials=((1.0, 1.0, 0.),), lineWidth=2,
            inheritMaterial=0, protected=True, disableStencil=True,
            transparent=True, animatable=False)
        g.pickable = 0
        self.viewer.AddObject(g)
        self.selectionCrosses = g

        self.unseenReports = [] # list of execution reports not yet seen by the user
        self._worstError = self._NoERROR
        
    def createStatusBar(self):
        self.statusBar().showMessage(self.tr("Ready"))

    def createActions(self):
        # open file action
        open = self.openAct = QtGui.QAction(
            QtGui.QIcon(os.path.join(PMVICONPATH, 'open.png')),
            'Open', self)
        open.setShortcut('Ctrl+O')
        open.setStatusTip('Open File')
        self.connect(open, QtCore.SIGNAL('triggered()'), self.openFile)

        # undo Action
        undo = self.undoAct = QtGui.QAction(
            QtGui.QIcon(os.path.join(PMVICONPATH, 'undo.png')),
            'Undo', self)
        undo.setShortcut('Ctrl+Z')
        undo.setStatusTip('Undo last command')
        cb = CallbackFunction(self.pmv.undo)
        self.connect(undo, QtCore.SIGNAL('triggered()'), cb)

        # redo Action
        redo = self.redoAct = QtGui.QAction(
            QtGui.QIcon(os.path.join(PMVICONPATH, 'redo.png')),
           'Redo', self)
        redo.setShortcut('Ctrl+Shift+Z')
        redo.setStatusTip('Redo last command')
        cb = CallbackFunction(self.pmv.redo)
        self.connect(redo, QtCore.SIGNAL('triggered()'), cb)

        # clearSelection Action
        clearSel = self.clearSelAct = QtGui.QAction(
            QtGui.QIcon(os.path.join(PMVICONPATH, 'eraser.png')),
            'Clear selection', self)
        #redo.setShortcut('Ctrl+Shift+Z')
        clearSel.setStatusTip('Clear Selection')
        cb = CallbackFunction(self.pmv.clearSelection)
        self.connect(clearSel, QtCore.SIGNAL('triggered()'), cb)

        # report action
        exit = self.reportAct = QtGui.QAction(
            QtGui.QIcon(os.path.join(PMVICONPATH, 'report.png')),
            'Execution Report', self)
        exit.setStatusTip('Display Execution Report')
        self.connect(exit, QtCore.SIGNAL('triggered()'), self.displayReports)

        # exit action
        exit = self.exitAct = QtGui.QAction(
            QtGui.QIcon(os.path.join(PMVICONPATH, 'quit.png')),
            'Exit', self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip('Exit application')
        self.connect(exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

        ## # select action
        ## select = self.selectAct = QtGui.QAction(QtGui.QIcon('icons/config.png'),
        ##                                       'Select ...', self)
        ## select.setShortcut('Ctrl+S')
        ## select.setStatusTip('Select')
        ## self.connect(select, QtCore.SIGNAL('triggered()'), self.selectionPanel)

    def selectionPanel(self):
        print 'DISPLAY SELECTION WINDOW'
        # windows visiblity actions
        #self.toggleLogViewAct = QtGui.QAction('showHide_Log', self)
        #connect(openAct, QtCore.SIGNAL("triggered()"),
        #        self.logWidget, SLOT("setVisible(bool)"))

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.undoAct)
        self.editMenu.addAction(self.redoAct)
        self.editMenu.addAction(self.clearSelAct)
        
        self.newGrpAct = self.editMenu.addAction('Create New Group')
        self.connect(self.newGrpAct, QtCore.SIGNAL('triggered()'),
                     self.createNewGroup)

        self.windowsMenu = self.menuBar().addMenu(self.tr("&Windows"))
        self.windowsMenu.addAction(self.toggleShellViewAct)
        self.windowsMenu.addAction(self.toggleLogViewAct)
#        self.windowsMenu.addAction(self.toggleCmdlineViewAct)
        self.windowsMenu.addAction(self.toggleDashboardViewAct)
        self.windowsMenu.addAction(self.toggle3DViewViewAct)
        self.windowsMenu.addAction(self.reportAct)
        #self.windowsMenu.addAction(self.togglePyShellViewAct)

        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))

    def createNewGroup(self, name=None, parent=None):
        if name is None:
            name, ok = QtGui.QInputDialog.getText(
                self, 'Group Name', 'Group name:')
            name = name.encode('ascii', 'ignore')
        else:
            ok = True
            
        if ok and name:
            self.pmv.addGroup(name)

    def createToolBar(self):
        self.toolBar = self.addToolBar(self.tr("PmvToolBar"))
        self.toolBar.addAction(self.openAct)
        self.toolBar.addAction(self.undoAct)
        self.toolBar.addAction(self.redoAct)
        self.toolBar.addAction(self.clearSelAct)
        self.toolBar.addAction(self.reportAct)        
        self.toolBar.addAction(self.exitAct)
        self.toolBar.setStyleSheet("QToolBar { background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #a6a6a6, stop: 0.08 #7f7f7f, stop: 0.39999 #717171, stop: 0.4 #626262, stop: 0.9 #4c4c4c, stop: 1 #333333);}")

    def createDockedtWidgets(self):
        # create a viewer and make it the central widget
        dock = QtGui.QDockWidget('3DViewer', self)
        dock.setMinimumSize(600, 400)
        from DejaVu2.Qt.Viewer import Viewer
        self.viewer = vi = Viewer(master=dock)
        dock.setWidget(vi.cameras[0])
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        #self.setCentralWidget(vi.cameras[0])
        self.toggle3DViewViewAct = dock.toggleViewAction()

        # override picking

        # the Viewer.processPicking is called with the pick object
        self.viewer.processPicking = self.processPicking

        # self.processPicking will turn the pick into atoms and call self.setDragSelectCommand
        self.setDragSelectCommand(self.pmv.select)

        # this allows to specify what should happen when we pick on nothing, Set to None
        # if no action is wanted
        self.setEmptyPickCommand(None)
        
        # override picking
        ## vi.cameras[0]._mouseReleaseNoMotionActions[
        ##     int(QtCore.Qt.LeftButton)][
        ##     int(QtCore.Qt.NoModifier)] = self.processPicking

        ## vi.cameras[0]._mouseReleaseWithMotionActions[
        ##     int(QtCore.Qt.LeftButton)][
        ##     int(QtCore.Qt.ShiftModifier)] = self.pick

        vi.cameras[0]._mouseReleaseNoMotionActions[
            int(QtCore.Qt.RightButton)][
            int(QtCore.Qt.NoModifier)] = self.pickMenu

        # create the dashboard widget
        dock = QtGui.QDockWidget('Dashboard', self)
        from dashboard import Dashboard
        self.objTree = Dashboard(self, parent=dock)
        dock.setWidget(self.objTree)
        dock.setMinimumSize(200, 600)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.toggleDashboardViewAct = dock.toggleViewAction()
        
        dock = QtGui.QDockWidget(self.tr("Python Shell"), self)
        if not use_ipython_shell:        
            # create the PyShell widget
            from pyshell import PyShell
            self.pyShellWidget = PyShell(dock)
        else :
            #create ipython embeded shell
            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel()
            kernel = kernel_manager.kernel
            kernel.gui = 'qt4'
            #other variable to pass to the context ?
            kernel.shell.push({'pmv':self.pmv,'pmvgui': self})
            #do you want pylab ?
            #kernel.shell.run_cell("import matplotlib")
            #kernel.shell.run_cell("matplotlib.rcParams['backend.qt4']='PySide'")
            #kernel.shell.run_cell("%pylab")
#            kernel.shell
            #matplotlib.rcParams['backend.qt4']='PySide'
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            app = guisupport.get_app_qt4()
            def stop():
                kernel_client.stop_channels()
                kernel_manager.shutdown_kernel()
                app.exit()
    
            self.pyShellWidget = RichIPythonWidget()
            self.pyShellWidget.kernel_manager = kernel_manager
            self.pyShellWidget.kernel_client = kernel_client
            self.pyShellWidget.exit_requested.connect(stop)
        
        dock.setWidget(self.pyShellWidget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.toggleShellViewAct = dock.toggleViewAction()

        # create the Log widget
        dock = QtGui.QDockWidget(self.tr("Log"), self)
        #dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        # prevent widget from being closeable
        #dock.setFeatures(QtGui.QDockWidget.DockWidgetMovable |
        #                 QtGui.QDockWidget.DockWidgetFloatable)
        self.logWidget = QtGui.QListWidget(dock)
        self.logWidget.addItems(["## Welcome to PMV",
                                 "## commands issues in PMV will log themselves here"])
        dock.setWidget(self.logWidget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.toggleLogViewAct = dock.toggleViewAction()
        
        # create cmd line widget
        ## dock = QtGui.QDockWidget(self.tr("cmdline"), self)
        ## self.cmdLineWidget = QtGui.QLineEdit(dock)
        ## self.cmdLineWidget.setFocus()
        ## dock.setWidget(self.cmdLineWidget)
        ## self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        ## self.toggleCmdlineViewAct = dock.toggleViewAction()

        ## dock = QtGui.QDockWidget(self.tr("Python Shell"), self)
        ## self.PyShellWidget =PyShell(dock)
        ## self.PyShellWidget.setFocus()
        ## dock.setWidget(self.PyShellWidget)
        ## self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        ## self.togglePyShellViewAct = dock.toggleViewAction()
        

    def findPickedAtoms(self, pick):
        """
given a PickObject this function finds all corresponding atoms.
Each atom in the returned set has its attribute pickedInstances set to a list
of 2-tuples [(geom, instance),...].
"""

        allatoms = AtomSet( [] )
        # loop over object, i.e. geometry objects
        for obj, values in pick.hits.items():
            # build a list of vertices and list of instances
            vertInds, instances = zip(*values)

            # only geometry bound to molecules is packable in PMV
            if not hasattr(obj, 'mol') or len(vertInds)<1:
                continue

            # only vertices of geometry have a mapping to atoms
            # for other types we return an empty atom set
            if pick.type!='vertices':
                return allatoms

            g = obj.mol().geomContainer

            # convert vertex indices into atoms
            if g.geomPickToAtoms.has_key(obj.name):
                # the geometry obj has a function to convert to atoms
                # specified it he geomContainer[obj], e.g. MSMS surface
                func = g.geomPickToAtoms[obj.name]
                if func:
                    atList = func(obj, vertInds)
                else:
                    atlist = []
            else:
                # we assume a 1 to 1 mapping of vertices with atoms
                # e.g. the lines geometry
                atList = []
                allAtoms = g.atoms[obj.name]
                for i in vertInds:
                    atList.append(allAtoms[int(i)])

            # build a dict of atoms used to set the pickedAtomInstance
            # attribute for the last picking operation
            pickedAtoms = {}

            # update the pickedAtoms dict
            for i, atom in enumerate(atList):
                atomInstList = pickedAtoms.get(atom, None)
                if atomInstList:
                    atomInstList.append( (obj, instances[i]) )
                else:
                    pickedAtoms[atom] = [ (obj, instances[i]) ]

            # FIXME atoms might appear multiple times because they were picked
            # in several geometries OR be cause they correspond to different
            # instances.  In the first case (i.e. multiple geometries)
            # duplicates should be removed, in the latter (multiple instances)
            # duplicate should be kept
            #
            # Apparently we do not get duplication for multiple geoemtry objects!
            allatoms = allatoms + AtomSet( atList )

            # loop over picked atoms and write the instance list into the atom
            for atom, instances in pickedAtoms.items():
                atom.pickedInstances = instances

        #print allAtoms
        return allatoms


    def findPickedBonds(self, pick):
        """do a pick operation and return a 2-tuple holding (the picked bond,
        the picked geometry)"""

        allbonds = BondSet( [] )
        for o, val in pick.hits.items(): #loop over geometries
            # loop over list of (vertices, instance) (e.g. (45, [0,0,2,0]))
            for instvert in val:
                primInd = instvert[0]
                if not hasattr(o, 'mol'): continue
                g = o.mol.geomContainer
                if g.geomPickToBonds.has_key(o.name):
                    func = g.geomPickToBonds[o.name]
                    if func: allbonds = allbonds + func(o, primInd)
                else:
                    l = []
                    bonds = g.atoms[o.name].bonds[0]
                    for i in range(len(primInd)):
                        l.append(bonds[int(primInd[i])])
                    allbonds = allbonds + BondSet(l)

        return allbonds

    def setDragSelectCommand(self, cmd):
        # force loading the selection command
        try:
            cmd = cmd.loadCommand()
        except AttributeError:
            pass
        # set the selection command to be the command
        self.dragSelectFunc = cmd

    def setEmptyPickCommand(self, cmd):
        # force loading the selection command
        if cmd is not None:
            try:
                cmd = cmd.loadCommand()
            except AttributeError:
                pass
        # set the selection command to be the command
        self.emptyPickFunc = cmd

    def processPicking(self, pick):
        cam = self.viewer.currentCamera
        objects = []
        if len(pick.hits):
            atoms = self.findPickedAtoms(pick)
            if len(atoms):
                if pick.operation=='add': negate = False
                else: negate = True
                self.dragSelectFunc(atoms, negate=negate)
        else:
            if self.emptyPickFunc:
                self.emptyPickFunc()

    def buildMenuForCamera(self, camera, parent=None):

        def askCamColor():
            def setCamCol(color):
                camera.Set(color=color.getRgb())
                camera.viewer.OneRedraw()
            oldCol = camera.backgroundColor
            w = QtGui.QColorDialog(parent)
            w.setCurrentColor(QtGui.QColor(*oldCol))
            w.currentColorChanged.connect(setCamCol)
            value = w.exec_()
            if value==0:
                camera.Set(color=oldCol)
        
        menu = QtGui.QMenu(self.tr('Camera'), parent)
        action = menu.addAction("background Color ...")
        self.connect(action, QtCore.SIGNAL('triggered()'), askCamColor)
        menu.popup(QtGui.QCursor.pos())
        
    def pickMenu(self, x, y, dx, dy, e):
        #import pdb
        #pdb.set_trace()
        cam = self.viewer.currentCamera
        pick = cam.DoPick(x, y, event=e)
        objects = []
        if len(pick.hits):
            atoms = self.findPickedAtoms(pick)
            if len(atoms):
                obj = atoms[0]
                rootItem = obj.top._treeItems.keys()[0]
                try:
                    item = obj._treeItems[rootItem]
                except AttributeError:
                    item = None
                objItems = [ (obj, item) ]
                while obj.parent:
                    try:
                        item = obj.parent._treeItems[rootItem]
                    except AttributeError: # obj.parent has never been expanded
                        item = None
                    except KeyError: # obj.parent has been expanded but not under the molecule
                        item = None
                    objItems.append( (obj.parent, item) )
                    obj = obj.parent
                # now check for groups
                ob = objItems[-1][0]
                while ob._group:
                    objItems.append( (ob._group, ob._group._treeItems.keys()[0]) )
                    ob = ob._group
                objItems.reverse()
                self.buildMenuForObjects(objItems, parent=self)
                #print 'pick object', atom, pick.hits.keys()[0].name
        else:
            self.buildMenuForCamera(self.viewer.currentCamera, parent=self)

    def getVisibleGeoms(self, obj):
        geoms = {}
        molecules, atomSets = self.pmv.getNodesByMolecule(obj, Atom)
        for mol, atoms in zip(molecules, atomSets):
            gc = mol.geomContainer
            #import pdb
            #pdb.set_trace()
            for name, ats in gc.atoms.items():
                if gc.geoms.has_key(name) and gc.geoms[name].visible:
                    if name[:4] in ['Heli', 'Stra', 'Turn', 'Coil']:
                        if not geoms.has_key('secondarystructure'):
                            if gc.displayedAs([name], atoms.parent.uniq(), 'fast'):
                                geoms['secondarystructure'] = gc.geoms[name]
                    elif gc.displayedAs([name], atoms, 'fast'):
                        if name in ['balls', 'sticks']:
                            geoms['sticksAndBalls'] = gc.geoms[name]
                        elif name in ['bonded', 'nobnds', 'bondorder']:
                            geoms['lines'] = gc.geoms[name]
                        else:
                            geoms[name] = gc.geoms[name]
        return geoms

    ## def remove_cb(self, obj, root):
    ##     if isinstance(obj, (Molecule, Atom)):
    ##         if root:
    ##             if isinstance(root._pmvObject, Molecule):
    ##                 print 'Delete Molecular fragment', obj.full_name()
    ##             elif isinstance(root._pmvObject, Selection):
    ##                 print 'Deselect %s under %s'%(obj.full_name(), root.text(0))
    ##             elif isinstance(root._pmvObject, MoleculeGroup):
    ##                 item = obj._treeItems[root]
    ##                 print 'Remove %s from group %s'%(obj.full_name(), item.parent().text(0))
    ##         else:
    ##             print 'Delete Molecular fragment', obj.full_name()
                
    ##     elif isinstance(obj, Selection):
    ##         print 'Delete selectino', obj.name
    ##     elif isinstance(obj, MoleculeGroup):
    ##         if obj == root._pmvObject:
    ##             print 'Delete group %s'%(obj.name)
    ##         else:
    ##             print 'Delete group %s under %s'%(obj.name, root.text(0))
        #self.objTree.removeItem(items)

    def deleteSelection_cb(self, objItems):
        # items is a list of items from the dashboard
        # the items all correspond to object of the same type
        rstr = ""
        for ob, it in objItems:
            rstr += ob.name+', '
        rstr = rstr[:-2]
        reply = QtGui.QMessageBox.question(self, "Delete Selection",
                                           "do you want want to delete the selection(s)\n%s?"%rstr,
                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            for ob, it in objItems:
                self.pmv.deleteNamedSelection(ob)

    def deleteObjects_cb(self, objItems):
        # items is a list of items from the dashboard
        # the items all correspond to object of the same type
        rstr = ""
        obj0, it0 = objItems[-1]
        if isinstance(obj0, (Protein, Selection, MoleculeGroup)):
            for obj, it in objItems:
                rstr += obj.name+', '
        else:
            molObj = []
            for obj, it in objItems:
                molObj.append(obj)
            molObj = obj0.setClass(molObj)
            rstr = molObj.buildRepr()
            
        reply = QtGui.QMessageBox.question(self, "Delete",
                                           "do you want to delete %s ?"%rstr,
                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.delete(objItems)

    def delete(self, objItems):
        app = self.pmv
        allObjects = [x[0] for x in objItems]
        allObjects = allObjects[0].setClass(allObjects)

        if isinstance(allObjects[0], Protein):
            self.pmv.deleteMolecules(MoleculeSet(allObjects))
        elif isinstance(allObjects[0], Selection):
            atoms = allObjects[0].atoms
            for obj in allObjects[1:]:
                atoms += obj.atoms
            self.pmv.deleteAtomSet(atoms)
        elif isinstance(allObjects[0], MoleculeGroup):
            self.pmv.deleteGroups(allObjects)
        else:
            atoms = allObjects.findType(Atom)
            self.pmv.deleteAtomSet(atoms)

    def rename_cb(self, objItems):
        # items is a list of items from the dashboard
        # the items all correspond to object of the same type

        w = GetNewName(objItems, self)
            
        ok = w.exec_()
	if ok==QtGui.QDialog.Accepted:
	    name = w.textValue()
	    name = name.encode('ascii', 'ignore')
            names = name.split(',')
            if len(names)==1:
                names = names*len(objItems)            
            # remove leading and ending spaces
            names = [n.strip() for n in names]
	else:
            names = None
	# this version does not allow me to overwrite done()
        #name, ok = GetSelectionName.getText(self, 'Name', 'Selection name:')
        if ok and names:
            self.rename(names, objItems)

    def rename(self, names, objItems):
        app = self.pmv
        for name, objItem in zip(names, objItems):
            obj, item = objItem
            self.pmv.rename(obj, name, item)

    def buildMenuForObjects(self, objItems, parent=None):
        # thsi function is call deom processPick with a list of 4 (obj,item)
        # for Molecule, Chain, Residue, Atom that was picked
        # We build a menu that will cascade the dashboard menu for each of these objects
        # assuming the the item picked was the Molecule object in the dashboard
        # We also build menu entries for the current selection if the picked atom is selected
        # and antries for each names selection the picked atom belings to
        menu = QtGui.QMenu(self.tr('Levels'), parent)

        # Current Selection Entry
        ob, it = objItems[-1]
        if self.pmv.activeSelection.isAnySelected(ob):
            submenu = menu.addMenu('Current Selection')
            item = self.pmv.activeSelection._treeItems.keys()[0]
            ob = self.pmv.activeSelection
            self.buildMenuForObject( [(ob, item)], parent=parent, parentMenu=submenu)

        # Named Selections Entries
        for name, sel in self.pmv.namedSelections.items():
            if sel.atomsDict.has_key(ob):
                submenu = menu.addMenu(name)
                item = sel._treeItems.keys()[0]
                self.buildMenuForObject( [(sel, item)], parent=parent, parentMenu=submenu)

        # build dashboard menu for Molecule, Chain, Residue and Atom
        for num, objIt in enumerate(objItems):
            obj, item = objIt
            if num < 4:
                label = self.levelLabels[num]
            else:
                label = 'G:'
            submenu = menu.addMenu('%s %s'%(label, getattr(obj, 'name')))
            self.buildMenuForObject( [(obj, item)], parent=parent, parentMenu=submenu )

        menu.popup(QtGui.QCursor.pos())
        return menu
            
    def getMoleculesInGroups(self, items):
        # gets all the molecule in the subtrees rooted at items
        # items are supposed to be for groups / molecules
        molecules = MoleculeSet([])
        for item in items:
            molecules.extend( self.getMoleculesInGroup(item) )
        return molecules
            
    def getMoleculesInGroup(self, item):
        molecules = MoleculeSet([])
        obj = item._pmvObject
        if isinstance(obj, Protein):
            molecules.append(obj)
        elif isinstance(obj, MoleculeGroup):
            # for groups return all molecules in subtree
            for n in range(item.childCount()):
                child = item.child(n)
                molecules.extend( self.getMoleculesInGroup(child) )
        return molecules

    def repostMenus(self, menu):
        ## to repost a menu we need to repost all parent menus at
        ## their respective locations and register a callback which
        ## will remove all reposted menus once a menu entry that does
        ## not trigger a repost is triggered

        ## create a list of all menus
        parent = menu
        parents = []
        while isinstance(parent, QtGui.QMenu):
            parents.append(parent)
            parent = parent.parent()

        # reverse the list to post them in the order the user posted
        # the menus (as they overlap slightly
        parents.reverse()

        # post the menus
        for parent in parents:
            parent.popup(parent.pos())

        # define a function that will unpost them all
        def hideAll(menu):
            parent = menu
            while isinstance(parent, QtGui.QMenu):
                parent.setVisible(False)
                parent = parent.parent()

        # assign the function to hide all menus
        cb = CallbackFunction(hideAll, menu)
        menu.aboutToHide.connect(cb)

        ## menu.popup(menu.pos()) # this reposts the menu at its position but not parent menus

    def buildMenuForObject(self, objItems, parent=None, parentMenu=None):
        # objItems is a list of (obj, item) pairs. item can be None when this is called
        # the 3D Viewer pick as the item might not exist for a residue for instance when
        # the molecule was not yet expanded.
        # The list can be of length one (e.g. right click on single entry)
        # or have N items if right click on entry that is part of dashboard selection
        # parent menu is used to decide if we post the menu or it will be a cascade of the
        # the parent menu (used by context menu in 3D viewer)
        
        if parentMenu is None:
            menu = QtGui.QMenu(parent)
        else:
            menu = parentMenu

        curSel = self.pmv.curSelection

        object0, item0 = objItems[0]
        if item0 is None:
            rootItem = object0.top._treeItems.keys()[0]
        else:
            rootItem = self.objTree.getRootItem(item0)

        isSelection = False
        if isinstance(object0, Selection):
            isSelection = True
            atoms = object0.atoms.copy()
            for obj, it in objItems[1:]:
                atoms.data += obj.atoms
        elif isinstance(object0, MoleculeGroup):
            items = [ob[0]._treeItems.keys()[0] for ob in objItems]
            molecules = self.getMoleculesInGroups(items)
            atoms = molecules.allAtoms
        else:
            atoms = AtomSet([])
            for ob, it in objItems:
                atoms += ob.findType(Atom)

        # if the item is in a selection, restrict atoms to selection
        allAtoms = atoms
        if isinstance(rootItem._pmvObject, Selection):
            atoms = atoms & rootItem._pmvObject.atoms
        ##
        ## Select/Deselect menu entry
        if len(atoms):
            selected = self.pmv.activeSelection.isSelected(allAtoms)
            if selected is True:
                action = menu.addAction("Deselect")
                cb = CallbackFunction(self.select, curSel, allAtoms, negate=1)
            else:
                if isinstance(rootItem._pmvObject, Selection):
                    action = menu.addAction("Complete Partial Selection")
                    only = False # objects in selection add to the selection.e.g. complete a residue
                else:
                    action = menu.addAction("Set as Selection")
                    only = True # objects in molecules or groups set the selection
                cb = CallbackFunction(self.select, curSel, allAtoms, negate=0, only=only)

            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        ##
        ## add to selections menu entry
        seleCount = len(self.pmv.namedSelections)
        curSelInTree = hasattr(self.pmv.curSelection, '_treeItems')
        if len(atoms) and (seleCount or curSelInTree):
            submenu = menu.addMenu('Add to Selection')
            if curSelInTree:
                action = submenu.addAction(self.tr('Current Selection'))
                cb = CallbackFunction(self.select, curSel, atoms, negate=0, only=False)
                self.connect(action, QtCore.SIGNAL('triggered()'), cb)
                
            for name, sel in self.pmv.namedSelections.items():
                action = submenu.addAction(self.tr(name))
                cb = CallbackFunction(self.select, sel, atoms, negate=0, only=False)
                self.connect(action, QtCore.SIGNAL('triggered()'), cb)
                
        menu.addSeparator()

        ##
        ## Name menu entry
        action = menu.addAction("Name ...")
        cb = CallbackFunction(self.rename_cb, objItems)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        ##
        ## Delete menu entry
        action = menu.addAction("Delete ...")
        cb = CallbackFunction(self.deleteObjects_cb, objItems)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        ##
        ## Delete Selection menu entry
        if isSelection:
            namedSelections = [x for x in objItems if x[0]!=curSel]
            if len(namedSelections):
                action = menu.addAction("Delete Selection")
                cb = CallbackFunction(self.deleteSelection_cb, namedSelections)
                self.connect(action, QtCore.SIGNAL('triggered()'), cb)
            
        menu.addSeparator()
        ## add all visible geometries
        ##
        geomsDict = self.getVisibleGeoms(atoms)
        geomNames = geomsDict.keys()
        geomNames.sort()
        hasSS = geomsDict.has_key('secondarystructure')
        for gname in geomNames:
            geom = geomsDict[gname]

            submenu = menu.addMenu(gname)
            action = submenu.addAction(self.tr('Remove'))
            if hasattr(geom, '_msmsType'):
                cb = CallbackFunction(self.pmv.displayMSMS, atoms, surfName=gname, negate=True)
            else:
                cb = CallbackFunction(self.displayfor, atoms, gname, negate=1)
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            # add color submenu
            colorSubMenu = submenu.addMenu(self.tr('Color by'))

            # Ca only for coloring action
            COnly = self.COnly = colorSubMenu.addAction(self.tr('Carbon only'))
            COnly.setStatusTip('Apply coloring to Carbon atoms only')
            COnly.setCheckable(True)
            COnly.setChecked(True)
            colorSubMenu.addSeparator()

            # FIXME how to repost menu 
            #cb = CallbackFunction(colorSubMenu.popup, QtGui.QCursor.pos())
            cb = CallbackFunction(self.repostMenus, colorSubMenu)
            self.connect(COnly, QtCore.SIGNAL('triggered()'), cb)
            
            action = colorSubMenu.addAction(self.tr('Atom Type'))
            cb = CallbackFunction(self.color, atoms, [gname], 'atomType')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Rasmol Residue Colors'))
            cb = CallbackFunction(self.color, atoms, [gname], 'rasmol')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Shapely Residues Colors'))
            cb = CallbackFunction(self.color, atoms, [gname], 'shapely')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Polarity'))
            cb = CallbackFunction(self.color, atoms, [gname], 'polarity')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Chain'))
            cb = CallbackFunction(self.color, atoms, [gname], 'chain')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Molecule'))
            cb = CallbackFunction(self.color, atoms, [gname], 'molecule')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Rainbow'))
            cb = CallbackFunction(self.color, atoms, [gname], 'rainbow')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('Rainbow By Chain'))
            cb = CallbackFunction(self.color, atoms, [gname], 'rainbowChain')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            if hasSS:
                action = colorSubMenu.addAction(self.tr('By secondary structure'))
                cb = CallbackFunction(self.color, atoms, [gname], 'secondaryStructure')
                self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = colorSubMenu.addAction(self.tr('custom colors'))
            cb = CallbackFunction(self.color, atoms, [gname], 'color')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)
                
            action = colorSubMenu.addAction(self.tr('Line colors'))
            cb = CallbackFunction(self.color, atoms, [gname], 'lineColors')
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

            action = submenu.addAction(self.tr('Customize'))

        # add submenu to add representation
        submenu = menu.addMenu(self.tr('Add Representation'))

        action = submenu.addAction(self.tr('lines'))
        cb = CallbackFunction(self.displayfor, atoms, 'lines', negate=0)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        action = submenu.addAction(self.tr('Sticks And Balls'))
        cb = CallbackFunction(self.displayfor, atoms, 'sticksAndBalls',
                              negate=0)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        action = submenu.addAction(self.tr('CPK'))
        cb = CallbackFunction(self.displayfor, atoms, 'cpk', negate=0)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        subsubmenu = submenu.addMenu('HyperBalls')
        for name, kw in {"S&B":{'shrink':0.01, 'scaleFactor':0.0 ,  'bScale':0.5, 'cpkRad':0.5 },
                         "CPK":{'shrink':0.01, 'scaleFactor':1   ,  'bScale':0.01, 'cpkRad':0.0},
                         "LIC":{'shrink':0.01, 'scaleFactor':0.0,  'bScale':1.0, 'cpkRad':0.3},
                         "HBL":{'shrink':0.3,  'scaleFactor':0.0 ,  'bScale':1.0, 'cpkRad':0.6 }}.items():
            action = subsubmenu.addAction(self.tr(name))
            cb = CallbackFunction(self.displayfor, atoms, 'hpballs', negate=0, **kw)
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        # FIXME only add of atoms is suitable for ribbon (see old dashboard)
        action = submenu.addAction(self.tr('ribbon'))
        cb = CallbackFunction(self.displayfor, atoms, 'ribbon', negate=0)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        action = submenu.addAction(self.tr('surface'))
        cb = CallbackFunction(self.displayMSMSfor, objItems, atoms, negate=0)
        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        if parentMenu is None:
            menu.popup(QtGui.QCursor.pos())
        return menu
    
    def select(self, selection, objects, negate=False, only=False):
        #print "SELEDCT:", selection.name, str(objects), negate, only
        old = selection.atoms[:]
        if only is True:
            setOn = objects.findType(Atom)
            setOff = []
            selection.set(setOn)
        elif negate:
            setOff = objects.findType(Atom)
            setOn = []
            selection.remove(setOff)
        else:
            setOn = objects.findType(Atom)
            setOff = []
            selection.add(setOn)

        if selection == self.pmv.activeSelection:
            self.objTree._selectionEventHandler(setOn, setOff, selection.atoms, old)
            self.updateSelectionIcons()
            self.highlightSelection()
            
    
    def buildMenuForObject1(self, obj, parent=None, parentMenu=None, target=None, rootItem=None):
        # obj is an atom, residue, chain or molecule for which to build the menu
        # target is what commands should apply to. This can be different from obj
        #        when target is a selection or a group
        # rootItem is the root node in the tree for obj. This is only set when we click on
        #     tree nodes in the dashboard. When the me is built for objects picked in the 3D
        #     camera rootItem will be None

        if parentMenu is None:
            menu = QtGui.QMenu(parent)
        else:
            menu = parentMenu

        
        originalObject = obj

        if isinstance(obj, Selection):
            isSelection = True
            obj = obj.atoms
        else:
            isSelection = False
            
        if target is None:
            target = obj

        ## Select menu entries
        ##
        if self.pmv.isNotSelected(target):
            name = str(taget.name)
            if len(name) > 20:
                name = name[:10]+'...'+name[-10:]
            action = menu.addAction("Make %s Current Selection"%name)
            cb = CallbackFunction(self.pmv.select, target, negate=0)
        else:
            action = menu.addAction("Deselect")
            cb = CallbackFunction(self.pmv.select, target, negate=1)

        self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        if isSelection:
            action = menu.addAction("Rename ...")
            cb = CallbackFunction(self.renameSelection_cb)
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        if not (isinstance(originalObject, Selection) and originalObject.name==u'Current Selection'):
            action = menu.addAction("Remove")
            cb = CallbackFunction(self.remove_cb, originalObject, rootItem)
            self.connect(action, QtCore.SIGNAL('triggered()'), cb)

        menu.addSeparator()
            


        menu.addSeparator()
        submenu = menu.addMenu('Styles')
        submenu = menu.addMenu('Label')
        submenu = menu.addMenu('Compute')
        if parentMenu is None:
            menu.popup(QtGui.QCursor.pos())

    def color(self, obj, gnames, mode):
        if isinstance(obj, MoleculeGroup):
            objects = obj.findType(Protein)
        else:
            objects = [obj]
            
        for obj in objects:
            if mode=='atomType':
                self.pmv.colorByAtomType(obj, geomsToColor=gnames)
            elif mode=='rasmol':
                self.pmv.colorByResidueType(obj, geomsToColor=gnames)
            elif mode=='shapely':
                self.pmv.colorResiduesUsingShapely(obj, geomsToColor=gnames)
            elif mode=='polarity':
                self.pmv.colorAtomsUsingDG(obj, geomsToColor=gnames)
            elif mode=='molecule':
                self.pmv.colorByMolecules(obj, geomsToColor=gnames)
            elif mode=='chain':
                self.pmv.colorByChains(obj, geomsToColor=gnames)
            elif mode=='rainbow':
                self.pmv.colorRainbow(obj, geomsToColor=gnames)
            elif mode=='rainbowChain':
                self.pmv.colorRainbowByChain(obj, geomsToColor=gnames)
            elif mode=='secondaryStructure':
                self.pmv.colorBySecondaryStructure(obj, geomsToColor=gnames)
            #elif mode=='customColor':
            #    self.pmv.(obj, geomsToColor=gnames)
            #elif mode=='lineColors':
            #    self.pmv.(obj, geomsToColor=gnames)
        
    def displayfor(self, obj, geomName, negate=0, **kw):
        if isinstance(obj, MoleculeGroup):
            objects = obj.findType(Protein)
        else:
            objects = [obj]

        for obj in objects:
            if geomName=='lines':
                self.pmv.displayLines(obj, negate=negate)
            elif geomName=='sticksAndBalls':
                self.pmv.displaySticksAndBalls(obj, negate=negate)
            elif geomName=='cpk':
                self.pmv.displayCPK(obj, negate=negate)            
            elif geomName=='hpballs':
                self.pmv.displayHyperBalls(obj, negate=negate, **kw)
                self.viewer.Redraw()
            elif geomName=='ribbon':
                self.pmv.ribbon(obj, negate=negate)
                #self.pmv.displayExtrudedSS(obj, negate=negate)

    def _displayMSMS(self, atoms, mol, surfName, negate=None, perMol=True):
        # here all atoms are in mol
        app = self.pmv
        gc = mol.geomContainer
        if not gc.geoms.has_key(surfName) or (
            hasattr(gc, 'msmsAtoms') and perMol==False and len(atoms)!=len(gc.msmsAtoms[surfName])):
            app.computeMSMS(atoms, surfName=surfName, perMol=perMol)
            mol.geomContainer.geoms[surfName]._msmsType = True
            app.displayMSMS(atoms, surfName=surfName, only=True, negate=False)
        else:
            if negate is None:
                negate = gc.displayedAs([surfName], atoms, 'fast')
            app.displayMSMS(atoms, surfName=surfName, negate=negate)
        
    def displayMSMSfor(self, objItems, atoms, negate=None):
        """Display (and compute if needed) molecular surfaces.
        """
        app = self.pmv
        obj0, item0 = objItems[0]
        rootItem = item0
        while rootItem.parent() is not None: rootItem = rootItem.parent()

        mols, atms = self.pmv.getNodesByMolecule(atoms)

        # for Selections, there can only be one selection we are operating on
        if isinstance(rootItem._pmvObject, Selection):
            sele = rootItem._pmvObject
            # if it is the current selection we operate on 'surface-%s'%mol.name
            if sele is self.pmv.curSelection:
                for mol, ats in zip(mols, atms):
                    self._displayMSMS(ats, mol, 'surface-%s'%mol.name, negate=negate, perMol=True)
            else:
                for mol, ats in zip(mols, atms):
                    self._displayMSMS(ats, mol, 'surface-%s'%sele.name, negate=negate, perMol=False)
        else:
            # if it is the current selection we operate on 'surface-%s'%mol.name
            for mol, ats in zip(mols, atms):
                self._displayMSMS(ats, mol, 'surface-%s'%mol.name, negate=negate, perMol=True)

    def openFile(self):
        filename, filter = QtGui.QFileDialog.getOpenFileName(
            self, self.tr("Read molecule or session"),
            '',
            self.tr("Molecule Files (*.pdb *.mol2);; Session Files (*.psf)"))

        if filename:
            # FIXME .. how to handle unicode names ?
            filename = filename.encode('ascii', 'ignore')
            #filename = filename.encode('ascii', 'replace')
            mols = self.pmv.readMolecules([filename])#)
            for mol in mols:
                self.pmv.buildBondsByDistance(mol)
            # FIXME we hardwire the the commands used upon loading
            if mols:
                self.pmv.displayLines(mols)
                self.pmv.colorByAtomType(mols, geomsToColor=['lines'])
   
    def registerListerners(self):
        ##
        evh = self.pmv.eventHandler

        from AppFramework.App import AddGeometryEvent, RemoveGeometryEvent, \
             RedrawEvent
        evh.registerListener(AddGeometryEvent, self.addGeometryEventHandler)
        evh.registerListener(RemoveGeometryEvent,
                             self.removeGeometryEventHandler)
        evh.registerListener(RedrawEvent, self.redrawEventHandler)

        from AppFramework.notOptionalCommands import NewUndoEvent, \
             AfterUndoEvent
        evh.registerListener(NewUndoEvent, self.undoEventHandler)
        evh.registerListener(AfterUndoEvent, self.undoEventHandler)

        ## reports
        from AppFramework.AppCommands import ExecutionReportEvent
        evh.registerListener(ExecutionReportEvent,
                             self.executionReportEventHandler)
        #from execReport import RemoveReportsEvent
        #evh.registerListener(RemoveReportsEvent,
        #                     self.removeReportsEventHandler)
        
        ##
        ## Selection Events        
        from PmvApp.selectionCmds import SelectionEvent

        from PmvApp.Pmv import StartAddMoleculeEvent, \
             ActiveSelectionChangedEvent, DeleteNamedSelectionEvent, \
             RenameSelectionEvent, RenameGroupEvent, RenameTreeNodeEvent

        evh.registerListener(StartAddMoleculeEvent,
                             self.addMoleculeEventHandler)

        evh.registerListener(SelectionEvent, self.selectionEventHandler)
        evh.registerListener(ActiveSelectionChangedEvent,
                             self.activeSelectionChangedEventHandler)
        evh.registerListener(DeleteNamedSelectionEvent,
                             self.deleteNamedSelectionEventHandler)
        evh.registerListener(RenameSelectionEvent,
                             self.renameSelectionEventHandler)
        evh.registerListener(RenameGroupEvent,
                             self.renameGroupEventHandler)
        evh.registerListener(RenameTreeNodeEvent,
                             self.renameTreeNodeEventHandler)

        ##
        ## groups
        from PmvApp.Pmv import AddGroupEvent, DeleteGroupsEvent, ReparentGroupObject
        evh.registerListener(AddGroupEvent, self.addGroupEventHandler)
        evh.registerListener(DeleteGroupsEvent, self.deleteGroupsEventHandler)
        evh.registerListener(ReparentGroupObject, self.reparentGroupObjectHandler)

        ##
        ## Delete Events
        from PmvApp.deleteCmds import BeforeDeleteMoleculeEvent
        from PmvApp.Pmv import AfterDeleteAtomsEvent

        evh.registerListener(BeforeDeleteMoleculeEvent,
                             self.beforeDeleteMoleculeEventHandler)

        evh.registerListener(AfterDeleteAtomsEvent,
                             self.afterDeleteAtomsEventHandler)

    def executionReportEventHandler(self, event):
        report = event.report
        self.updateReportIcon(report)
        
    def updateReportIcon(self, report):
        if report.numberOf['exceptions'] or report._requestUserConfirmation:
            self.unseenReports.append(report)
            self.reportAct.setIcon(QtGui.QIcon(os.path.join(
                PMVICONPATH, 'reportException.png')))
            self._worstError = self._EXCEPTION

        elif report.numberOf['errors']:
            if self._worstError < self._ERROR:
                self._worstError = self._ERROR
                self.reportAct.setIcon(QtGui.QIcon(os.path.join(
                    PMVICONPATH, 'reportError.png')))
            self.unseenReports.append(report)
            
        elif report.numberOf['warnings'] > 1:
            if self._worstError < self._WARNING:
                self._worstError = self._WARNING
                self.reportAct.setIcon(QtGui.QIcon(os.path.join(
                    PMVICONPATH, 'reportWarning.png')))
            self.unseenReports.append(report)

    def displayReports(self):
        # reset icons and state
        self._worstError = self._NoERROR
        self.reportAct.setIcon(QtGui.QIcon(os.path.join(PMVICONPATH,
                                                        'report.png')))
        
        if len(self.unseenReports)==0: return
        from execReport import ExecutionReports
        w = ExecutionReports(self.pmv, self.unseenReports)
        ## w.setModal(False)
        ## w.show()
        ## w.raise_()
        ## w.activateWindow()
        ok = w.exec_()
        #report.printReport()

    ## def removeReportsEventHandler(self, event):
    ##     self._worstError = self._NoERROR
    ##     self.reportAct.setIcon(QtGui.QIcon(os.path.join(PMVICONPATH,
    ##                                                     'report.png')))
    ##     for report in self.unseenReports:
    ##         self.updateReportIcon(report)
            
    def addGroupEventHandler(self, event):
        self.objTree.addObject(event.group, None, event.group.name)

    def deleteGroupsEventHandler(self, event):
        for group in event.groups:
            groupItem = group._treeItems.keys()[0]
            if groupItem.parent() is None:
                self.objTree.invisibleRootItem().removeChild(groupItem)
            else:
                groupItem.parent().removeChild(groupItem)
            
    def reparentGroupObjectHandler(self, event):
        # remove object's item from old group
        obj = event.object
        if hasattr(obj, '_treeItems'):
            objItem = obj._treeItems.keys()[0]
            parent = objItem.parent()
            if parent is None:
                self.objTree.invisibleRootItem().removeChild(objItem)
            else:
                parent.removeChild(objItem)

        # add object's item to new group
        newGroup = event.newGroup
        if newGroup is None:
            self.objTree.invisibleRootItem().addChild(objItem)
            self.objTree.setItemsExpandable(True)
        elif hasattr(newGroup, '_treeItems'):
            newGroupItem = newGroup._treeItems.keys()[0]
            collapse = False
            if not newGroupItem.isExpanded():
                collapse = True
            newGroupItem.addChild(objItem)
            if collapse:
                newGroupItem.setExpanded(False)
                
    def renameTreeNodeEventHandler(self, event):
        obj = event.object
        if obj.alias:
            newName = "%s (%s)"%(obj.alias, obj.name)
        else:
            newName = obj.name
        if hasattr(obj, '_treeItems'):
            for root, it in obj._treeItems.items():
                it.setText(0, newName)
                
    def renameGroupEventHandler(self, event):
        obj = event.object
        item = event.item
        if item is None:
            item = obj._treeItems.keys()[0]
        item.setText(0, obj.name)

    def renameSelectionEventHandler(self, event):
        item = event.item
        obj =  event.selection
        if item is None:
            item = obj._treeItems.keys()[0]

        item.setText(0, obj.name)
        if hasattr(event, 'setCurrent'): # we renamed the curSelection
            if event.setCurrent:
                self.pmv.setCurrentSelection(obj)
            
    def deleteNamedSelectionEventHandler(self, event):
        sele = event.selection
        if self.activeSelection == sele:
            self.activeSelection = None
        if hasattr(sele, '_treeItems'):
            self.objTree.invisibleRootItem().removeChild(sele._treeItems.keys()[0])
            
    def activeSelectionChangedEventHandler(self, event):
        old = event.old
        new = event.new
        self.activeSelection = new
        if hasattr(new, '_treeItems'):
            self.objTree.setCurrentSelection(new._treeItems.keys()[0])
        
    def afterDeleteAtomsEventHandler(self, event):
        roots = {}
        for atom in event.objects:
            if hasattr(atom, '_treeItems'):
                for rootItem, item in atom._treeItems.items():
                    parentItem = item.parent()
                    parentItem.removeChild(item)
                    while parentItem is not None:
                        if parentItem.childCount()==0:
                            newparentItem = parentItem.parent()
                            newparentItem.removeChild(parentItem)
                            parentItem = newparentItem
            else:
                # this happens if we delete all the atoms in a bunch of residues
                # for instance. The atoms are not in the dahsboard, but the residues might be
                # and need to be removed
                
                # go up the tree until we find an parent in the Dashboard
                parent = atom.parent
                while not hasattr(parent, '_treeItems'):
                    parent = parent.parent
                roots[parent] = True
                
        # now traverse all molecules and delete all entries with no children
        nodes = roots.keys()
        parentItems = {}
        for node in roots.keys():
            if len(node.children)==0:
                for it in node._treeItems.values():
                    parent = it.parent()
                    if parent:
                        parent.removeChild(it)
                        parentItems[parent] = True

        # node clean up all parent in the tree
        items = parentItems.keys()
        while len(items):
            parentItems = {}
            for item in items:
                if item.childCount()==0:
                    parent = item.parent()
                    if parent:
                        parent.removeChild(item)
                        parentItems[parent] = True
                    elif isinstance(item._pmvObject, (Protein, MoleculeGroup)):
                        self.objTree.invisibleRoot().removeChild(item)
                    elif isinstance(item._pmvObject, (Selection)):
                        if item._pmvObject==self.pmv.curSelection:
                            self.objTree.invisibleRoot().removeChild(item)
                            self.activeSelection = None
            items = parentItems.keys()
                
    def undoEventHandler(self, event):
        # set the button tool tip and the status bar message to the
        # the name of the next action undo(redo) could trigger
        cmd = event.command
        if len(event.objects):
            if cmd.name == "undo":
            #if event.objects == self.pmv.undo.cmdStack:
                self.undoAct.setStatusTip('Undo '+event.objects[-1][1])
                self.undoAct.setToolTip('Undo '+event.objects[-1][1])
            #elif event.objects == self.pmv.redo.cmdStack:
            elif cmd.name == "redo":
                self.redoAct.setStatusTip('Redo '+event.objects[-1][1])
                self.redoAct.setToolTip('Redo '+event.objects[-1][1])
            else:
                raise # FIXME
        else:
            if cmd.name == "undo":
                self.undoAct.setStatusTip('Undo (empty stack)')
                self.undoAct.setToolTip('Undo (empty stack)')
            elif cmd.name == "redo":
                self.redoAct.setStatusTip('Redo (empty stack)')
                self.redoAct.setToolTip('Redo (empty stack)')
            #print 'Undo event on empty stack'

            
    def beforeDeleteMoleculeEventHandler(self, event):
        mol = event.object
        # remove the molecule form the tree
        item = mol._treeItems.keys()[0]
        if item.parent() is None:
            self.objTree.invisibleRootItem().removeChild(item)
        else:
            item.parent().removeChild(item)
        # remove item's ._pmvObject attribute to break cyclic reference
        def delPmvObject(item):
            del item._pmvObject
            for n in range(item.childCount()):
                child = item.child(n)
                if hasattr(child, '_pmvObject'): # dummy child of unexpanded node does not have _pmvObject
                    delPmvObject(child)
        delPmvObject(item)
                
    def addMoleculeEventHandler(self, event):
        mol = event.kw['object']
        name = event.kw['name']
        self.objTree.addObject(mol, None, name)
        
    def addGeometryEventHandler(self, event):
        #obj, parent=None, redo=False):
        #print 'Handling add geom event for', event.object.name
        self.viewer.AddObject(event.object, parent=event.parent, redo=event.redo)
        
    def removeGeometryEventHandler(self, event):
        #obj, parent=None, redo=False):
        #print 'Handling add geom event for', event.object.name
        self.viewer.RemoveObject(event.object)

    def redrawEventHandler(self, event):
        #print 'Handling redraw event'
        self.viewer.redraw()

    def selectionEventHandler(self, event=None):
        self.updateSelectionIcons()
        self.highlightSelection()

    def updateSelectionIcons(self):
        """update selection icons"""
        #if SelectionSpheres is currently turned on: 
        app = self.pmv
        if self.activeSelection is None or app.activeSelection.empty():
            self.selectionCrosses.Set(visible=0, tagModified=False)
        else:
            atoms = self.pmv.activeSelection.get(Atom)
            self.selectionCrosses.Set(vertices=atoms.coords, visible=1, tagModified=False)
                    
        self.viewer.Redraw()

    def highlightSelection(self):
        # highlight selection
        app = self.pmv
        if self.activeSelection is None or self.pmv.activeSelection.empty():
            selMols = selAtms = []
        else:
            selMols, selAtms = app.getNodesByMolecule(self.pmv.activeSelection.get())
        allMols = set( app.Mols[:] )
        unselectedMols = allMols.difference(selMols)
        boundGeoms = []
        if app.commands.has_key('DisplayBoundGeom'):
            if isinstance(app.DisplayBoundGeom, MVCommand):
                boundGeoms = app.DisplayBoundGeom.getBoundGeomNames()
        for mol in unselectedMols:
            for geomName, lGeom in mol.geomContainer.geoms.items():
                if isinstance(lGeom, Spheres) \
                  or isinstance(lGeom, Cylinders) \
                  or (    isinstance(lGeom, IndexedPolygons) \
                      and hasattr(mol.geomContainer,'msmsAtoms') and mol.geomContainer.msmsAtoms.has_key(geomName) ):
                    lGeom.Set(highlight=[])
                elif isinstance(lGeom, IndexedPolygons) \
                  and lGeom.parent.name == 'secondarystructure':
                    lGeom.Set(highlight=[])
                elif isinstance(lGeom, IndexedPolygons) \
                  and lGeom.fullName in boundGeoms:
                    lGeom.Set(highlight=[])

        if self.activeSelection is None or self.pmv.activeSelection.empty():
            selMols2 = selResidueSets = []
        else:
            selMols2, selResidueSets = app.getNodesByMolecule(self.pmv.activeSelection.get(Residue))
        molSelectedResiduesDict = dict( zip( selMols2, selResidueSets) )
        for mol, selectedResidueSet in molSelectedResiduesDict.items():
            for lGeom in mol.geomContainer.geoms.values():
                if isinstance(lGeom, IndexedPolygons) and lGeom.parent.name == 'secondarystructure':
                    highlight = [0] * len(lGeom.vertexSet.vertices.array)
                    for selectedResidue in selectedResidueSet:
                        if hasattr(lGeom, 'resfacesDict') and lGeom.resfacesDict.has_key(selectedResidue):
                            for lFace in lGeom.resfacesDict[selectedResidue]:
                                for lVertexIndex in lFace:
                                    highlight[int(lVertexIndex)] = 1
                    lGeom.Set(highlight=highlight)

        for mol, atoms in map(None, selMols, selAtms):
            for geomName, lGeom in mol.geomContainer.geoms.items():
                if   isinstance(lGeom, Spheres) \
                  or isinstance(lGeom, Cylinders):
                    lAtomSet = mol.geomContainer.atoms[geomName]
                    if len(lAtomSet) > 0:
                        lAtomSetDict = dict(zip(lAtomSet, range(len(lAtomSet))))
                        highlight = [0] * len(lAtomSet)
                        for i in range(len(atoms)):
                            lIndex = lAtomSetDict.get(atoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        lGeom.Set(highlight=highlight)
                elif isinstance(lGeom, IndexedPolygons):
                  if hasattr(mol.geomContainer,'msmsAtoms') and mol.geomContainer.msmsAtoms.has_key(geomName):
                    lAtomSet = mol.geomContainer.msmsAtoms[geomName]
                    if len(lAtomSet) > 0:
                        lAtomSetDict = dict(zip(lAtomSet, range(len(lAtomSet))))
                        lAtomIndices = []
                        for i in range(len(atoms)):
                            lIndex = lAtomSetDict.get(atoms[i], None)
                            if lIndex is not None:
                                lAtomIndices.append(lIndex)
                        lSrfMsms = mol.geomContainer.msms[geomName][0]
                        lvf, lvint, lTri = lSrfMsms.getTriangles(
                            lAtomIndices, 
                            selnum=numOfSelectedVerticesToSelectTriangle,
                            keepOriginalIndices=1)
                        highlight = [0] * len(lGeom.vertexSet.vertices)
                        for lThreeIndices in lTri:
                            highlight[int(lThreeIndices[0])] = 1
                            highlight[int(lThreeIndices[1])] = 1
                            highlight[int(lThreeIndices[2])] = 1
                        lGeom.Set(highlight=highlight)
                  elif app.bindGeomToMolecularFragment.data.has_key(lGeom.fullName) \
                    and app.bindGeomToMolecularFragment.data[lGeom.fullName].has_key('atomVertices'):
                      bindcmd = app.bindGeomToMolecularFragment
                      lSelectedAtoms = atoms
                      if len(lSelectedAtoms) > 0:
                        lAtomVerticesDict = bindcmd.data[lGeom.fullName]['atomVertices']
                        highlight = [0] * len(lGeom.vertexSet.vertices)
                        for lSelectedAtom in lSelectedAtoms:
                            lVertexIndices = lAtomVerticesDict.get(lSelectedAtom, [])
                            for lVertexIndex in lVertexIndices:
                                highlight[lVertexIndex] = 1
                        lGeom.Set(highlight=highlight)

