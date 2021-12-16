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
# $Header: /opt/cvs/PmvApp/GUI/Qt/dashboard.py,v 1.25 2014/07/23 00:34:44 sanner Exp $
#
# $Id: dashboard.py,v 1.25 2014/07/23 00:34:44 sanner Exp $
#

## Selections:
##   when nothing is selected, selecting somethign add current selection to to the tree
##   only one selection can be active at any time.
##   selected items are added to the current selection
##   the active selection has a yellow background in the Tree widget
##   clicking on the active selection (i.e. with yellow background) make the active selection None
##   There is no range or complex combinations of selections (i.e. multiple selections can not be
##     made blue and operated on as one can do with molecular fragments and groups
##

import weakref, os
from PySide import QtCore, QtGui

from MolKit.molecule import Atom, Molecule, MoleculeSet, MoleculeGroup
from MolKit.protein import Residue, Chain, Protein

from mglutil.util.callback import CallbackFunction
from mglutil.util.packageFilePath import findFilePath
PMVICONPATH = findFilePath('Icons', 'PmvApp.GUI')

from PmvGUI import GridGroup
from PmvApp.Pmv import Selection

class ResTreeWidgetItem(QtGui.QTreeWidgetItem):

    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        key1 = self.text(column)
        key2 = other.text(column)
        return int(key1[3:]) < int(key2[3:])
        
class Dashboard(QtGui.QTreeWidget):

    def __init__(self, pmvGUI, parent=None):
        self.pmvGUI = pmvGUI
        #self.objToTreeitem = {}
        #self.treeitemToObj = {}
        QtGui.QTreeWidget.__init__(self, parent)
        self.setColumnCount(1)
        self.setHeaderLabels(['objects', ])
        self.currentItemChanged.connect(self.onSetCurrentItem)
        self.itemExpanded.connect(self.onItemExpanded)
        self.itemDoubleClicked.connect(self.showHide)
        ## self.itemClicked.connect(self.onItemClick)
        ## self.itemActivated.connect(self.onItemActivated)
        self.setAlternatingRowColors(True)
        self.setAutoScroll(True)
        
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        #self.setDropIndicatorShown(True) #is default

        # this will move the actual node
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

        self.currentSeleItem = None # will be a TreeWidgetItem when a selection is active
        from PmvApp.selectionCmds import SelectionEvent
        self.pmvGUI.pmv.eventHandler.registerListener(
            SelectionEvent, self.selectionEventHandler)

        from PmvApp.deleteCmds import DeleteObjectEvent
        self.pmvGUI.pmv.eventHandler.registerListener(
            DeleteObjectEvent, self.deleteObjectEventHandler)

        #root = self.invisibleRootItem()
        #root.setFlags(root.flags() & ~QtCore.Qt.ItemIsDropEnabled)
        self.colors = {
            'molecules':QtGui.QColor(255, 255, 255),
            'currentSelection':QtGui.QColor(253, 253, 150),
            'namedSelections':QtGui.QColor(119, 158, 203),
            'groups':QtGui.QColor(255, 105, 97),
            'grids':QtGui.QColor(255, 179, 71),
            'molecules':QtGui.QColor(255, 255, 255),
            'currentSelection':QtGui.QColor(253, 253, 150),
            'namedSelections':QtGui.QColor(255, 255, 255),
            'groups':QtGui.QColor(255, 255, 255),
            'grids':QtGui.QColor(255, 255, 255),
            'white':QtGui.QColor(255, 255, 255),
            }
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        #selModel = self.selectionModel()
        #.setSelectionFlag(QtGui.QAbstractItemView.ToggleCurrent)
        self.itemExpanded.connect(self.onItemExpanded)
        #selModel.selectionChanged.connect(self.onSelectionChange)
        self.itemSelectionChanged.connect(self.onItemSelectionChange)

    def mousePressEvent(self, e):
        ## only left mouse button press are handled as mouse press in the tree
        self._MouseBUtton = e.buttons()
        #print 'mousePress', int(e.buttons())
        if e.buttons()==QtCore.Qt.LeftButton:
            #item = self.itemAt(e.pos())
            #self.setCurrentItem(item)
            #item.setExpanded(not item.isExpanded())
            QtGui.QTreeWidget.mousePressEvent(self, e)

    def onItemSelectionChange(self):
        #
        # Here we enforce rules for extended selections
        # 1 - objects have to be of the same class
        # 2 - the roots can not be a selection and something else
        
        selectedItems = self.selectedItems()
        ## when first item is selected we remember class of selected object
        ## and the root of the item
        if len(selectedItems)==1:
            self._selectionClass = selectedItems[0]._pmvObject.__class__
            self._selectionRootObj = self.getRootItem(selectedItems[0])._pmvObject
            #print 'FIRST PICK', self._selectionClass, self._selectionRootObj.name
        else:
            if not hasattr(self, '_selectionClass'): # we got here with multiple selection before
                                                     # could set the class
                # deselect everythign and return
                selModel = self.selectionModel()
                for index in selModel.selection().indexes():
                    selModel.select(index, selModel.Deselect)
                return
            
        ## for all elements in the selection we verify that they are of the proper type
        ## and under the right root
        #print 'selected:'
        selModel = self.selectionModel()
        for index in selModel.selection().indexes():
            item = self.itemFromIndex(index)
            rootObj = self.getRootItem(item)._pmvObject

            # objects need to be of the same class
            if not isinstance(item._pmvObject, self._selectionClass):
                selModel.select(index, selModel.Deselect)
            elif isinstance(self._selectionRootObj, Selection):
                # if objects are f the same class they also nee to have compatible roots
                if not isinstance(rootObj, Selection):
                    selModel.select(index, selModel.Deselect)
            elif not isinstance(self._selectionRootObj, Selection):
                if isinstance(rootObj, Selection):
                    selModel.select(index, selModel.Deselect)
            #else:
            #    print 'keeping2', item.text(0)
        
    def deleteObjectEventHandler(self, event):
        mol = event.object
        print 'Handling delete', mol.name

    def removeItem(self, items):
        for k, item in items.items():
            print 'remove %s under %s'%(item.text(0), self.getRootItem(item).text(0))

    def removeEmptyBranches(self, item, selection, root):
        #print 'Entering', item.text(0), item, item.childCount()
        #import pdb
        #pdb.set_trace()
        for i in range(item.childCount()):
            child = item.child(i)
            if hasattr(child, '_pmvObject'): # dummyChild does not have it
                selectedAtoms = selection.inter(child._pmvObject.findType(Atom))
                if len(selectedAtoms)==0:
                    #try:
                    del child._pmvObject._treeItems[root]
                    #except KeyError:
                    #    import pdb
                    #    pdb.set_trace()
                    #print 'deleting2', child.text(0), child, child._pmvObject.name
                    child.parent().removeChild(child)
                        
                else:
                    self.removeEmptyBranches(child, selection, root)

    ## def onItemClick(self, item, column):
    ##     print 'mouse press intercepted', item, column
        
    ## def onItemActivated(self, item, column):
    ##     import pdb
    ##     pdb.set_trace()
    ##     print 'mouse activaed intercepted', item, column
        

    def selectionEventHandler(self, event):
        self._selectionEventHandler(event.setOn, event.setOff, event.new, event.old)

    def _selectionEventHandler(self, setOn, setOff, new, old):
        #print 'SELECTIONEVENT', setOn, setOff
        app = self.pmvGUI.pmv
        item = None
        #print 'DDDD', app.activeSelection, app.curSelection
        #import pdb
        #pdb.set_trace()
        if app.curSelection.empty():
            # the selection is empty and was shown in the tree => we remove it
            if hasattr(app.activeSelection,'_treeItems') and app.activeSelection is app.curSelection:
                item = app.activeSelection._treeItems.keys()[0]
                self.invisibleRootItem().removeChild(item)
                del self.pmvGUI.activeSelection._treeItems
                self.pmvGUI.activeSelection = None # remember that no selection is active
                return
        
        ##
        ## selection in PMV is empty
        if app.activeSelection.empty():
            if self.pmvGUI.activeSelection is None: # no selection is active in the dashboard
                return
            ##
            ##  named selection is active
            if app.activeSelection != app.curSelection:
                # we clear the sub tree to reflect empty selection
                # but keep this selection as active with top entry in dashboard
                item = app.activeSelection._treeItems.keys()[0]
                for i in range(item.childCount()):
                    item.removeChild(item.child(i))
                    item.dummyChild = QtGui.QTreeWidgetItem(item)
                    item.setExpanded(False)
                return
        ##
        ## selection is NOT empty
        else:
            ##
            ## not selection is active, i.e. the selection is in  app.curSelection
            if self.pmvGUI.activeSelection is None:
                # make curSelection the currently active selection
                app.activeSelection = app.curSelection
                self.pmvGUI.activeSelection = app.curSelection
                # add current selection to the tree if needed
                if hasattr(app.curSelection, '_treeItems'):
                    self.setCurrentSelection(app.curSelection._treeItems.keys()[0])
                else:
                    self.addObject(app.curSelection, None, 'Current Selection',
                                   color=self.colors['currentSelection'])
                return
            else:
                item = app.activeSelection._treeItems.keys()[0]
            
        if item:
            if self.isItemExpanded(item):
                # remove nodes of deselected atoms
                for atom in setOff:
                    root = item
                    if hasattr(atom, '_treeItems') and \
                           atom._treeItems.has_key(root):
                        #print 'FAGA', atom.name, atom._treeItems.keys()
                        item = atom._treeItems[root]
                        parent = item.parent()
                        parent.removeChild(item)
                        #print 'deleting1', item.text(0), item
                        del atom._treeItems[root]
                        while parent.childCount()==0:
                            grandParent = parent.parent()
                            print 'FUGU removing', parent.text(0)
                            grandParent.removeChild(parent)
                            del parent._pmvObject._treeItems[root]
                            parent = grandParent
                            
                if len(setOff):
                    self.removeEmptyBranches(item, self.pmvGUI.activeSelection.atoms, root)
                
                # add nodes of selected atoms
                parents = []
                for atom in setOn:
                    root = item
                    # find first ancestor that is shown in tree
                    if hasattr(atom, '_treeItems') and atom._treeItems.has_key(root):
                        #print 'FUGU12'
                        continue # already selected
                    obj = atom
                    while not hasattr(obj.parent, '_treeItems') or \
                              not obj.parent._treeItems.has_key(root):
                        if obj.parent is None:
                            break
                        else:
                            obj = obj.parent
                    #print 'FAGA', atom, obj, obj.parent, obj.parent._treeItems[root]._pmvObject.name
                    #print 'FAGAO', obj.name
                    if obj.parent is None:
                        parent = root
                    else:
                        parent = obj.parent._treeItems[root]
                    if parent.isExpanded():
                        newItem = self.addObject(obj, parent, obj.name.replace(' ', '_'))
                    parents.append(parent)

                # sort residues
                for parent in parents:
                    parent.sortChildren(0, QtCore.Qt.AscendingOrder)
                    
        
    def getObjectsForTreeItem(self, item):
        # gets all the objects in the subtree rooted at item
        # obj = self.treeitemToObj[item]
        obj = item._pmvObject
        root = self.getRootItem(item)

        if isinstance(root._pmvObject, Selection):
            # for selections return the intersection of the selection
            # with the atoms of the node corresponding to item
            return obj.atoms.findType(Atom).inter(root._pmvObject.atoms)

        elif isinstance(obj, MoleculeGroup):
            # for groups return all molecules in subtree
            objects = []
            for n in range(item.childCount()):
                child = item.child(n)
                if isinstance(child._pmvObject, MoleculeGroup):
                    objects.extend( self.getObjectsForTreeItem(child) )
                else:
                    objects.append( child._pmvObject )
            return MoleculeSet(objects)

        else:
            #print 'getObjectsForTreeItem', obj.__class__
            # for other nodes, i.e. Molecule, chains, Residues and Atoms
            klass = obj.setClass
            return klass([obj])
            #return obj

    def getIcon(self, obj):
        if isinstance(obj, Atom):
            icon = os.path.join(PMVICONPATH, "atom.png")
        elif isinstance(obj, Residue):
            icon = os.path.join(PMVICONPATH, "sidechain.png")
        elif isinstance(obj, Chain):
            icon = os.path.join(PMVICONPATH, "chain.png")
        elif isinstance(obj, Molecule):
            icon = os.path.join(PMVICONPATH, "molecule.png")
        elif isinstance(obj, MoleculeGroup):
            icon = os.path.join(PMVICONPATH, "group.png")
        elif isinstance(obj, Selection):
            icon = os.path.join(PMVICONPATH, "selection.png")
        else:
            icon = os.path.join(PMVICONPATH, "python.gif")

        return QtGui.QIcon(icon)

    def getColor(self, obj):
        if isinstance(obj, Protein):
            return self.colors['molecules']
        elif isinstance(obj, Selection):
            if obj.name==u'Current Selection':
                return self.colors['currentSelection']
            else:
                return self.colors['namedSelections']
        elif isinstance(obj, MoleculeGroup):
            return self.colors['groups']
        else:
            return None
                
    def addObject(self, obj, parent, name, color=None):
        # obj is a pmv object such as molecule or group
        # parent is a tree item
        #if name == 'OH':
        #    import pdb
        #    pdb.set_trace()

        #if color is None:
        #    color = self.getColor(obj)
        if parent is None: # add a root object (not draggable)
            root = item = QtGui.QTreeWidgetItem(self)
            #item.setFlags(item.flags() & ~QtCore.Qt.ItemIsDragEnabled)
            #self.objToTreeitem[root] = {}
        else:
            if isinstance(obj, Residue):
                item = ResTreeWidgetItem(parent)
            else:
                item = QtGui.QTreeWidgetItem(parent)
            root = self.getRootItem(item)

            if isinstance(obj, MoleculeGroup):
                pass
            elif isinstance(obj, Protein):
                # molecules inside selections cannot be dragged
                if isinstance(root._pmvObject, Selection):
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsDragEnabled)
                # disallow dropping on Proteins
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsDropEnabled)
                pass
            else: # chains, residues and atoms are not dragable or droppable
                item.setFlags(item.flags() & ~(QtCore.Qt.ItemIsDragEnabled |
                                               QtCore.Qt.ItemIsDropEnabled))

        if color:
            item.setBackground(0, color)
            
        if len(obj.children) or isinstance(obj, Selection):
            # create a dummy child and add it so that the item is expandable
            # that way we can make lazy expansion
            #print 'creating DUMMY child for', obj.name, name
            item.dummyChild = QtGui.QTreeWidgetItem(item)

        # add the icon
        icon = self.getIcon(obj)
        if icon:
            item.setIcon(0, icon)

        #self.objToTreeitem[root][obj] = item
        #self.treeitemToObj[item] = obj
        if hasattr(obj, 'alias') and obj.alias:
            name = '%s (%s)'%(obj.alias, name)

        item.setText(0, self.tr(name))
        if not hasattr(obj, '_treeItems'):
            obj._treeItems = {}

        obj._treeItems[root] = item
        #print '%%%%%%', obj.name, id(obj), obj.__class__, obj._treeItems
        item._pmvObject = obj
        #print 'ADDING1', item.text(0), item, name #, obj.name, obj.__class__, item, parent
        return item

    def getRootItem(self, item):
        root = item
        while root.parent() is not None:
            root = root.parent()
        return root                
        
    def onItemExpanded (self, item):
        #print 'Expanded', item, item._pmvObject
        #print 'Expand XXXXXX', item, obj, hasattr(item, 'dummyChild')
        if hasattr(item, 'dummyChild'):
            obj = item._pmvObject
            #print 'Expanding', obj.name 
            #import pdb
            #pdb.set_trace()
            root = self.getRootItem(item)
            if isinstance(root._pmvObject, Selection):
                selection = root._pmvObject.atoms
                if len(selection)==0:
                    item.setExpanded(False)
                    return
                item.removeChild(item.dummyChild)
                del item.dummyChild
                #print 'FAGO', len(selection)
                for c in obj.children:
                    selectedChildren = selection.inter(c.findType(Atom))
                    if len(selectedChildren):
                        newItem = self.addObject(c, item, c.name.replace(' ', '_'))
            else:
                item.removeChild(item.dummyChild)
                del item.dummyChild
                for c in obj.children:
                   # self.addObject(c, self.objToTreeitem[root][obj], c.name.replace(' ', '_'))
                   self.addObject(c, item, c.name.replace(' ', '_'))
        
    def startDrag(self, action):
        # save the object we are dragging
        self._draggedItems = self.selectedItems()#currentItem()
        QtGui.QTreeWidget.startDrag(self, action)

    def dragMoveEvent(self, event):
        ## to constrain dragging we have to monitor the motion and interactively decide
        ## whether the item we are on is suitable to be dropped on based on the type of
        ## the currently dragged object.
        ## in order to show the forbidden cursor icon we need to set the flags of all
        ## parent to non droppable.
        item = self.itemAt(event.pos()) # get item we are on now

        # Disallow dragging 
        if hasattr(item, '_pmvObject'): # the invisible root does not have it
            root = self.getRootItem(item)
            if isinstance(item._pmvObject, Protein) or \
                   isinstance(root._pmvObject, Selection):
                event.ignore()
                return

        if item is None:
            QtGui.QTreeWidget.dragMoveEvent(self, event)
            return

        obj = item._pmvObject # get object we are over
        items = []
        if isinstance(self._draggedItems[0]._pmvObject, Protein):
            if isinstance(obj, (Protein, GridGroup)): # make not droppable
                _obj = item
                for _obj in item, item.parent():
                    if _obj is not None:
                        flags = _obj.flags()
                        _obj.setFlags(_obj.flags() & ~QtCore.Qt.ItemIsDropEnabled)
                        items.append( (_obj, flags) )
                        #print 'resetting', _obj._pmvObject.name
                        _obj = _obj.parent()

        if len(items)==0:
            QtGui.QTreeWidget.dragMoveEvent(self, event)

        for item, flags in items:
            item.setFlags(flags)
        

    def dropEvent(self, e):
        #import pdb
        #pdb.set_trace()
        sourceItems = self._draggedItems
        destItem = self.itemAt(e.pos())

        for sourceItem in sourceItems:
            oldRoot = self.getRootItem(sourceItem)
            if destItem is not None:
                newRoot = self.getRootItem(destItem)
            try:
                #print 'dragged %s onto %s'%(sourceItem.text(0), destItem.text(0))
                if isinstance(destItem._pmvObject, Protein):
                    #print 'REFUSE, return'
                    return
            except AttributeError:
                pass

            if destItem is None:
                self.pmvGUI.pmv.reparentObject(sourceItem._pmvObject, None)
            else:
                self.pmvGUI.pmv.reparentObject(sourceItem._pmvObject, destItem._pmvObject)
        #QtGui.QTreeWidget.dropEvent(self, e)



    def unsolicitedPick(self, pick):
        """treat an unsollicited picking event"""
        print 'FFFFF unsolicitedPick'

    def showHide(self, item, column):
        if column==0:
            mols = self.getObjectsForTreeItem(item).top.uniq()
            for mol in mols:
                show = mol.geomContainer.masterGeom.visible
                self.pmvGUI.pmv.showMolecules(mol, negate=show)
                # redo expand/collapse that double click triggered
            if item.isExpanded():
                self.collapseItem(item)
            else:
                self.expandItem(item)

    def setCurrentSelection(self, item):
        app = self.pmvGUI.pmv
        if item:
            # make current selection background white
            if hasattr(app.activeSelection, '_treeItems'):
                app.activeSelection._treeItems.keys()[0].setBackground(0, self.colors['white'])

            # make background of new active selection yellow
            item.setBackground(0, self.colors['currentSelection'])

            # set the new selection to be active
            #self.pmvGUI.activeSelection = app.activeSelection = item._pmvObject
            #self.pmvGUI.activeSelection = item._pmvObject

            # call handler so that crosses and selectionFeedback is updated
            self.pmvGUI.selectionEventHandler()

        else: # item is None so no selection is activein the GUI
            if hasattr(self.pmvGUI.activeSelection, '_treeItems'):
                self.pmvGUI.activeSelection._treeItems.keys()[0].setBackground(0, self.colors['white'])
            self.pmvGUI.activeSelection = None
            # set the app's active Selection to current selection so that selection operations
            # operate on current selection
            #app.activeSelection = app.curSelection
            
        self.pmvGUI.updateSelectionIcons()
        self.pmvGUI.highlightSelection()

    def onSetCurrentItem(self, current, previous):
        # called when an item is left click on in the dashboard
        # print 'clicked on', current.text(0), previous.text(0)

        if current and isinstance(current._pmvObject, Selection):
            # clicked on a selection in the dashboard
            if current._pmvObject is self.pmvGUI.activeSelection:
                ## clicked on the the GUI's active selection selection ==>
                ##   hide the current selection and make pmv.curSelection the active selection
                self.setCurrentSelection(None)
                self.pmvGUI.pmv.setCurrentSelection(self.pmvGUI.pmv.curSelection)
                #self.setCurrentSelection(current._pmvObject._treeItems.keys()[0])
                self.setCurrentSelection(None)
            else:
                #self.setCurrentSelection(current)
                self.setCurrentSelection(None)
                self.pmvGUI.pmv.setCurrentSelection(current._pmvObject)
            # set the previous item to the the current tree ite to avoid blue background on active selection
            self.setCurrentItem(previous)
        else:
            msg = "toggle with keys: select l:lines, b:S&B, c:CPK, r:ribbon, m:surface"
            self.pmvGUI.statusBar().showMessage(self.tr(msg))
            
    def enterEvent(self, e):
        self.setFocus()
        self.pmvGUI.statusBar().showMessage(self.tr("Ready"))

    def leaveEvent(self, e):
        self.clearFocus()
        self.pmvGUI.statusBar().showMessage(self.tr("Ready"))

    def keyPressEvent(self, e):
        #print "key press", e.key(), e.text(), (e.modifiers() & QtCore.Qt.ControlModifier)== QtCore.Qt.ControlModifier
        items = self.selectedItems()#currentItem()
        objects = []
        for item in items:
            objects.extend(self.getObjectsForTreeItem(item).data)
        if len(objects)==0: return
        objects = objects[0].setClass(objects)
        app = self.pmvGUI.pmv
        mols, atomSets = app.getNodesByMolecule(objects, Atom)
        for mol, atms in zip(mols, atomSets):
            #print 'FAFAFA', mol, len(atms), atms
            gc = mol.geomContainer
            if hasattr(self, '_alt'):
                if e.text()=='c':
                    self._altC = True
                elif e.text()=='d':
                    self._altD = True
                del self._alt
            elif hasattr(self, '_altC'): # AltC color commands
                if e.text()=='a':
                    app.colorByAtomType(atms, geomsToColor=['all'])
                elif e.text()=='m':
                    app.colorByMolecules(atms, geomsToColor=['all'])
                elif e.text()=='p':
                    app.colorAtomsUsingDG(atms, geomsToColor=['all'])
                elif e.text()=='r':
                    app.colorRainbow(atms, geomsToColor=['all'])
                elif e.text()=='c':
                    app.colorRainbowByChain(atms, geomsToColor=['all'])
                del self._altC
            elif hasattr(self, '_altD'):
                if e.text()=='l':
                    print 'Sequnce alt + D + L'
                del self._altD
            else:
                if e.text()=='s':
                    if app.isNotSelected(atms):            
                        app.select(atms, negate=0)
                    else:
                        app.select(atms, negate=1)
                elif e.text()=='l':
                    negate = gc.displayedAs(['bonded', 'nobnds'], atms, 'fast')
                    app.displayLines(atms, negate=negate)
                elif e.text()=='b':
                    negate = gc.displayedAs(['sticks', 'balls'], atms, 'fast')
                    app.displaySticksAndBalls(atms, negate=negate)
                elif e.text()=='c':
                    negate = gc.displayedAs(['cpk'], atms, 'fast')
                    #print 'Display CPK', len(atms), negate
                    app.displayCPK(atms, negate=negate)
                elif e.text()=='r':
                    g = gc.geoms.get('secondarystructure', None)
                    if g is None:
                        negate = False
                    else:
                        geomNames = [x.name for x in g.children]
                        negate = gc.displayedAs(geomNames, atms.parent.uniq(), 'fast')
                    app.ribbon(atms, negate=negate)
                elif e.text()=='m':
                    objItems = [ (x._pmvObject, x) for x in items ]
                    atoms = objects.findType(Atom)
                    self.pmvGUI.displayMSMSfor(objItems, atoms)

                elif (e.modifiers() & QtCore.Qt.AltModifier) == QtCore.Qt.AltModifier:
                    self._alt = True
                
        ## elif e.text()=='r':
        ##     negate = gc.displayedAs(geoms, atoms, 'fast')
        ##     app.displaySecondaryStructure(atms, negate=negate)
        ## elif e.text()=='m':
        ##     negate = gc.displayedAs(['cpk'], atoms, 'fast')
        ##     app.displayCPK(atms, negate=negate)

    def contextMenuEvent(self, event, item=None):
        # find the item on which we clicked
        if item is None:
            item = self.itemAt(event.pos())

        if item is None: return
        
        # find the asscoiate Pmv object
        obj = item._pmvObject

        # if the item we clicked on is selected we want the operation to
        # occur for everything selected in the dashboard
        selectedItems = self.selectedItems()

        # check is clicked item is selected
        # for some reason item in selectedItems fails so we have to check manually
        itemInSel = False
        for it in selectedItems:
            if it is item:
                itemInSel = True
                break
        ## if the item is selected
        ## replace obj by a set of object for all selected items
        if itemInSel:
            items = selectedItems
        else:
            items = [item]

        objItems = [(it._pmvObject, it) for it in items]

        return self.pmvGUI.buildMenuForObject(objItems, parent=self, parentMenu=None)

        ## if itemInSel:
        ##     obj = [it._pmvObject for it in selectedItems]
        ##     obj = obj[0].setClass(obj)
            
        ## else:
        ##     obj = obj.setClass([item._pmvObject])

        ## at this point obj is always a set of potentially one object
        ## print 'OBJECTS', [o.name for o in obj]

        ## # for nodes under a selection, right click should not makes us loose the selection
        ## # so we force the current item to be the root
        ## root = self.getRootItem(item)
        ## #if isinstance(root._pmvObject, Selection):
        ## #    self.setCurrentItem(root)

        ## if isinstance(obj, MoleculeGroup):
        ##     self.pmvGUI.buildMenuForObject(obj, parent=self, parentMenu=None,
        ##                                    target=self.getObjectsForTreeItem(item),
        ##                                    rootItem=root)
        ## else:
        ##     self.pmvGUI.buildMenuForObject(obj, parent=self, parentMenu=None, rootItem=root)
            


    #def onItemPressed (self, item, column):
    #    print 'pressed', item, self.treeitemToObj.get(item, 'dummy')

    #def onExpandItem(self, item):
    #    print 'onExpandItem', item, self.treeitemToObj.get(item, 'dummy')
            

     ## def __init__(self, parent=None):

    ##     QtGui.QTreeWidget.__init__(self, parent)

    ##     self.pmv = None
    ##     self.rootRow = None
        
    ##     tree = self.tree = QtGui.QTreeWidget(parent)
    ##     self.headerLabels = ['geometry', 'info']
    ##     self.nbCol = len(self.headerLabels)
    ##     tree.setColumnCount(self.nbCol)
    ##     tree.setHeaderLabels(self.headerLabels)
            
    ##     mainLayout = QtGui.QVBoxLayout()   
    ##     mainLayout.addWidget(tree)

    ##     self.setLayout(mainLayout)
        
    ##     tree.show()

    ## def bind(self, pmv):
    ##     self.pmv = pmv
    ##     tree = self.tree
    ##     row = QtGui.QTreeWidgetItem(tree)
    ##     row.setText(0, 'All')
    ##     row.buttons = []
    ##     for i in range(1,self.nbCol):
    ##         b1 = QtGui.QCheckBox(tree)
    ##         self.connect(b1, QtCore.SIGNAL("stateChanged(int)"), self.box_cb)
    ##         b1.object = pmv.Molecules
    ##         b1.col = i
    ##         row.buttons.append(b1)
    ##         tree.setItemWidget(row, i, b1)
    ##     self.rootRow = row

    ##     for mol in pmv.Molecules:
    ##         self.addMolecule(mol)

        
    ## def addMolecule(self, mol):
    ##     def addRow(object, parent):
    ##         row = QtGui.QTreeWidgetItem(parent)
    ##         row.setText(0, object.name)
    ##         row.buttons = []
    ##         for i in range(1,self.nbCol):
    ##             b1 = QtGui.QCheckBox()
    ##             b1.object = object
    ##             b1.col = i
    ##             self.connect(b1, QtCore.SIGNAL("stateChanged(int)"), self.box_cb)
    ##             row.buttons.append(b1)
    ##             self.tree.setItemWidget(row, i, b1)
    ##         for child in object.children:
    ##             if isinstance(child, Atom):
    ##                 return
    ##             addRow(child, row)

    ##     addRow(mol, self.rootRow)


    ## def box_cb(self, i):
    ##     button = self.sender()
    ##     frag = button.object
    ##     mol = frag.top
    ##     geomC = mol.geomContainer
    ##     if button.col==3: # cpk
    ##         atmset = geomC.atoms['cpk']
    ##         if i:
    ##             atms = atmset + frag.findType(Atom)
    ##         else:
    ##             atms = atmset - frag.findType(Atom)

    ##         geom = geomC.geoms['cpk']
    ##         if len(atms)==0:
    ##             geom.Set(visible=0, tagModified=False)
    ##         else:
    ##             try:
    ##                 rads = atms.radius
    ##             except AttributeError:
    ##                 rads = mol.defaultRadii()
    ##             geom.Set(visible=1, vertices=atms.coords, radii=atms.radius)

    ##         geomC.atoms['cpk'] = atms
            
    ##         vi = geom.viewer
    ##         vi.Redraw()
    ##         vi.cameras[0].updateGL()
    ##     #print i, frag, self.headerLabels[button.col]
        

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)

    from MolKit import Read
    from time import time
    t1 = time()
    mol = Read(sys.argv[1])[0]
    print 'read mol in ', time()-t1

    class Pmv:
        def __init__(self):
            self.Molecules = []

    pmv = Pmv()
    pmv.Molecules.append(mol)
    
    t1 = time()
    db = Dashboard(pmv)
    print 'built tree in ', time()-t1

