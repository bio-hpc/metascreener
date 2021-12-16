
#############################################################################
#
# Author: Ruth Huey, Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/deleteCmds.py,v 1.8 2014/07/11 05:59:37 sanner Exp $
#
# $Id: deleteCmds.py,v 1.8 2014/07/11 05:59:37 sanner Exp $
#

"""
This Module implements commands to delete items from the MoleculeViewer:
for examples:
    Delete Molecule
"""
from PmvApp.Pmv import Event, AfterDeleteAtomsEvent, DeleteAtomsEvent, \
     BeforeDeleteMoleculeEvent, AfterDeleteMoleculeEvent
from PmvApp.Pmv import BeforeDeleteMoleculeEvent, AfterDeleteMoleculeEvent
from PmvApp.selectionCmds import SelectionEvent
from PmvApp.Pmv import MVCommand

from AppFramework.App import DeleteObjectEvent
from MolKit.protein import Coil, Helix, Strand, Turn
from MolKit.molecule import MoleculeSet, AtomSet, Atom

class DeleteMolecules(MVCommand):
    """Command to delete molecules from the MoleculeViewer \n
    Package : PmvApp \n
    Module  : \n
    deleteCmds \n
    Class   : DeleteMolecules \n
    Command : deleteMolecules \n
    Synopsis:\n
        None<---deleteMol(nodes, **kw) \n
    Required Arguments:\n
        nodes --- TreeNodeSet holding the current selection \n
    It resets the undo stack automatically.\n
    """
    
    def onAddCmdToApp(self):
        self.app()._deletedLevels = []
        self.app().lazyLoad("selectionCmds",
                         commands=["select", "clearSelection"],
                         package="PmvApp")

        if  not self.app().commands.has_key('restoreMol'):
            self.app().lazyLoad("deleteCmds", commands=["restoreMol"],
                             package="PmvApp")
            

    def deleteMol(self, mol, undoable=False):
        """ Function to delete all the references to each elements of a
        molecule and then these elements and the molecule to free the
        memory space."""

        #  Call the removeObject function for all the command having an
        # onRemoveMol function
        self.app().removeObject(mol, "Molecule")
        event = DeleteObjectEvent(object=mol, objectType='Molecule')
        self.app().eventHandler.dispatchEvent(event)
        nodes = self.app().activeSelection.get()
        mol.__class__._numberOfDeletedNodes = 0
        node = mol
        while len(node.children):
            node = node.children

        # Initialize the variable _numberOfDeletedNodes at 0
        node[0].__class__._numberOfDeletedNodes = 0
        sslevels = [Coil, Helix, Strand, Turn]
        # Initialize the variable _numberOfDeletedNodes for each secondary
        # structure to 0.
        for sl in sslevels:
            # Initialize the variable _numberOfDeletedNodes at 0
            sl._numberOfDeletedNodes = 0

        # but only change selection if there is any
        if nodes is not None and len(nodes)>0:
            setClass = nodes.__class__
            thisMolNodes = setClass(nodes.get(lambda x, mol=mol: x.top==mol))
            #only change selection if this molecule has any nodes in it
            if len(thisMolNodes)>0:
                nodes = nodes-thisMolNodes
                self.app().clearSelection()
                if nodes is not None:
                    self.app().select(nodes)
        
        #check for any possible reference in self.app().GUI.VIEWER.lastPick
        ### FIX THIS :
        #if self.app().hasGui and self.app().GUI.VIEWER.lastPick:
        #    for key in self.app().GUI.VIEWER.lastPick.hits.keys():
        #        if hasattr(key,'mol'):
        #            if mol==key.mol():
        #                del self.app().GUI.VIEWER.lastPick.hits[key]

        # Remove the atoms of the molecule you are deleting from the
        # the AtomSet self.app().allAtoms
        self.app().allAtoms = self.app().allAtoms - mol.allAtoms
        seqViewer = self.app().commands.get("sequenceViewer", None)
        if seqViewer: seqViewer.deleteObject(mol)
        if not undoable:
            # Delete all the reference to the atoms you want to delete
            if hasattr(mol.allAtoms, 'bonds'):
                bnds = mol.allAtoms.bonds[0]
                for b in bnds:
                    b.__dict__.clear()
                    del(b)
            
            mol.allAtoms.__dict__.clear()
            del mol.allAtoms
            if hasattr(mol, 'geomContainer'):
                for g in mol.geomContainer.geoms.values():
                    if hasattr(g, 'mol'):
                        delattr(g, 'mol')
    
                mol.geomContainer.geoms.clear()
                mol.geomContainer.atoms.clear()
                delattr(mol.geomContainer, 'mol')
                del mol.geomContainer
    
            if hasattr(mol, 'atmNum'):
                mol.atmNum.clear()
                del mol.atmNum
    
            if hasattr(mol, 'childByName'):
                mol.childByName.clear()
                del mol.childByName
    
            if hasattr(mol, 'parser') and hasattr(mol.parser, 'mol'):
                delattr(mol.parser,'mol')
                del mol.parser

        # delete molecule from Vision, if Vision is running
        if hasattr(self.app(), "visionAPI") and self.app().visionAPI:
            self.app().visionAPI.remove(mol)

        if not undoable:
            if len(mol.children):
                deletedLevels = mol.deleteSubTree()
            else:
                deletedLevels = []
            # then delete all the refences to the molecule
            del mol.top
            # Then delete the molecule
            deletedLevels.insert(0, mol.__class__)
    
            mol.__dict__.clear()
            del mol
        
            self.app()._deletedLevels = deletedLevels


    def getFreeMemoryInformation(self):
        """Store how many TreeNodes have been actually free'ed during the
        last delete operation in a dictionary"""

        memoryInformation = {}
        #print 'self.app()._deletedLevels=', self.app()._deletedLevels
        for d in self.app()._deletedLevels:
            #print 'checking ', d, ' for deletedNodes'
            memoryInformation[d.__name__] = d._numberOfDeletedNodes
        sslevels = [Coil, Helix, Strand, Turn]
##          geomslevels = [IndexedPolylines, IndexedPolygons]
        # Have to loop on the known secondarystructure because our
        # Data structure doesn't support multiple children and parents.
        for sl in sslevels:
            if sl._numberOfDeletedNodes!=0:
                memoryInformation[sl.__name__] = sl._numberOfDeletedNodes

##          for sg in geomslevels:
##              if sl._numberOfDeletedNodes!=0:
##                  memoryInformation[sl.__name__] = sl._numberOfDeletedNodes
                
        return memoryInformation


    def doit(self, nodes,  undoable=False, cleanRedo=True):
        #if called with no selection, just return
        molecules, nodeSets = self.app().getNodesByMolecule(nodes)

        # MS. NO need here because this is done autmatically in App.removeObject
        #event = BeforeDeleteMoleculeEvent(objects=molecules)
        #self.app().eventHandler.dispatchEvent(event)

        # MS if we do not make a copy of the set of molecules only the first
        # molecule gets deleted. Not sure why !
        for mol in MoleculeSet(molecules):
            if not undoable:
                #print "cleaning the undo CmdStack"
                self.app().undo.cleanCmdStack( mol)
                self.app().redo.cleanCmdStack( mol)
            else:
                if cleanRedo:
                    self.app().redo.cleanCmdStack(mol)
            self.deleteMol(mol, undoable)

        # MS. NO need here because this is done autmatically in App.removeObject
        #event = AfterDeleteMoleculeEvent(objects=molecules)
        #self.app().eventHandler.dispatchEvent(event)

        # The following  should be done in the method of AfterDeleteMoleculesEvent listener:
        # self.app().GUI.VIEWER.SetCurrentObject(self.app().GUI.VIEWER.rootObject)

        # ?????
        #if not undoable:
        #    self.app().resetUndo()

            
    def checkArguments(self, nodes, undoable=False, cleanRedo=True):
        """None <- deleteMolecules(nodes, **kw) \n
        nodes: TreeNodeSet holding the current selection.
        """
        if isinstance(nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        assert nodes
        assert undoable in [True, False, 1, 0]
        assert cleanRedo in [True, False, 1, 0]
        kw = {'undoable':undoable, 'cleanRedo':cleanRedo}
        return (nodes,), kw 


    def undoCmdBefore(self, molecule, undoable=False,  cleanRedo=True):
        #print "deleteMol, undoCmdBefore(), undoable", undoable
        if undoable:
            if isinstance(molecule, str):
                molecules, nodeSets = self.app().getNodesByMolecule(molecule)
                if not len(molecules):return
                molecule = molecules[0]
            
            code = self.app().getStateCodeForMolecule(molecule, mode="commands")
            return ([(self.app().restoreMol, (molecule,), {'cmds':code})], self.name+" %s"%molecule.name)
            


class RestoreMolecule(MVCommand):
    """Command to restore a molecule that had been deleted with \n
    deleteMol command (when 'undoable' of the delete command is set to True) \n
    Package : PmvApp \n
    Module  : deleteCmds \n
    Class   : RestoreMolecule \n
    Command : restoreMol \n
    Synopsis:\n
        None<---restoreMolecules(molecule, cmds=None) \n
        cmds - a list of commands to execute to restore the molecule's state
        """
    
    def doit(self, molecule, cmds=None):
        
        self.app().addMolecule(molecule)
        if not cmds: return
        if not len(self.app().Mols): return 
        mol = self.app().Mols[-1]
        if not mol.name == molecule.name:
            return
        currentAtoms = mol.allAtoms
        currentAtoms.sort()
        from AppFramework.AppCommands import AppCommand
        for entry in cmds:
            if isinstance(entry[0], AppCommand):
                cmd, args, kw = entry
                kw['setupUndo'] = 0
                cmd(*args, **kw)
            elif callable(entry[0]):
                cmd, args, kw = entry
                cmd(*args, **kw)
            elif entry[0] == "atomcolors":
                for ind, colors in entry[1].items():
                    for att, col in colors.items():
                        currentAtoms[ind].colors[att] = col
            elif entry[0] == "atomdata":
                for ind, data in entry[1].items():
                    for att, val in data.items():
                        setattr(currentAtoms[ind], att, val)

                         
    def checkArguments(self, molecule, cmds=None):
        """None <- restoreMol(molecule, **kw)
        \nmolecule: molecule that had beed deleted with deleteMol command.
        """
        kw = {'cmds':cmds}
        return (molecule,), kw 
             

    def undoCmdAfter(self, result, molecule, cmds=None):
        #this is called in VFCmd.afterDoit().
        #result is a returned value of the doit()--None for this command.
        #print "undoCmdAfter", self.name
        return ([(self.app().deleteMol, (molecule,), {'undoable':1, 'cleanRedo':False})],
                self.name+ " %s"%molecule.name)


    def handleForgetUndo(self, mol, cmds=None, **kw):
        if mol in self.app().Mols: return
        print self.name, "handleForgetUndo"
        # Delete all the reference to the atoms you want to delete
        if hasattr(mol.allAtoms, 'bonds'):
            bnds = mol.allAtoms.bonds[0]
            for b in bnds:
                b.__dict__.clear()
                del(b)

        mol.allAtoms.__dict__.clear()
        del mol.allAtoms

        if hasattr(mol, 'geomContainer'):
            for g in mol.geomContainer.geoms.values():
                if hasattr(g, 'mol'):
                    delattr(g, 'mol')

            mol.geomContainer.geoms.clear()
            mol.geomContainer.atoms.clear()
            delattr(mol.geomContainer, 'mol')
            del mol.geomContainer

        if hasattr(mol, 'atmNum'):
            mol.atmNum.clear()
            del mol.atmNum

        if hasattr(mol, 'childByName'):
            mol.childByName.clear()
            del mol.childByName

        if hasattr(mol, 'parser') and hasattr(mol.parser, 'mol'):
            delattr(mol.parser,'mol')
            del mol.parser

        if len(mol.children):
            deletedLevels = mol.deleteSubTree()
        else:
            deletedLevels = []
        # then delete all the refences to the molecule
        del mol.top
        # Then delete the molecule
        deletedLevels.insert(0, mol.__class__)

        mol.__dict__.clear()
        del mol

        self.app()._deletedLevels = deletedLevels


class DeleteAllMolecules(DeleteMolecules):
    """Command to delete all molecules from the MoleculeViewer \n
    Package : PmvApp \n
    Module  : deleteCmds \n
    Class   : DeleteAllMolecules \n
    Command : deleteAllMolecules \n
    Synopsis:\n
        None<---deleteAllMolecules( **kw) \n
    Required Arguments:\n
         It resets the undo stack automatically.\n
    """
            
    def onAddCmdToApp(self):
        self.app()._deletedLevels = [] 
           

    def getFreeMemoryInformation(self):
        """Store how many TreeNodes have been actually free'ed during the
        last delete operation in a dictionary"""

        memoryInformation = {}
        #print 'self.app()._deletedLevels=', self.app()._deletedLevels
        for d in self.app()._deletedLevels:
            #print 'checking ', d, ' for deletedNodes'
            memoryInformation[d.__name__] = d._numberOfDeletedNodes
        sslevels = [Coil, Helix, Strand, Turn]
##          geomslevels = [IndexedPolylines, IndexedPolygons]
        # Have to loop on the known secondarystructure because our
        # Data structure doesn't support multiple children and parents.
        for sl in sslevels:
            if sl._numberOfDeletedNodes!=0:
                memoryInformation[sl.__name__] = sl._numberOfDeletedNodes
##          for sg in geomslevels:
##              if sl._numberOfDeletedNodes!=0:
##                  memoryInformation[sl.__name__] = sl._numberOfDeletedNodes
        return memoryInformation


    def doit(self):
        for i in range(len(self.app().Mols)):
            self.deleteMol(self.app().Mols[-1])
        self.app().undo.resetCmdStack()
        self.app().redo.resetCmdStack()
        event = AfterDeleteMoleculeEvent(objects=molecules)
        self.app().eventHandler.dispatchEvent(event)
        #if self.app().hasGui:
        #    self.app().GUI.VIEWER.SetCurrentObject(self.app().GUI.VIEWER.rootObject)
        #     self.app().GUI.VIEWER.Redraw()


    def checkArguments(self, **kw):
        """ None<---deleteAllMolecules( **kw)
        \nRemove all molecules in the viewer
        \nIt resets the undo stack automatically.
        """
        return (), kw


    def undoCmdBefore(self):
        "DeleteALLMolecules is undoable"
        return

    

class DeleteAtomSet(MVCommand):
    """ Command to remove an AtomSet from the MoleculeViewer  \n
    Package : PmvApp \n
    Module  : deleteCmds \n
    Class   : DeleteAtomSet \n
    Command : deleteAtomSet \n
    Synopsis:\n
        None<---deleteAtomSet(atoms)\n
    Required Arguments:\n
        atoms --- AtomSet to be deleted.\n
    """
    
    def __init__(self):
        MVCommand.__init__(self)
        #self.flag = self.flag | self.objArgOnly


    def onAddCmdToApp(self):
        self.app()._deletedLevels = []
        if not self.app().commands.has_key('deleteMol'):
            self.app().lazyLoad("deleteCmds", commands=["deleteMol"], package="PmvApp")
        self.app().lazyLoad("selectionCmds", commands=[
            "select", "clearSelection"], package="PmvApp")


    def checkArguments(self, atoms):
        """None <- deleteAtomSet(atoms) \n
        atoms: AtomSet to be deleted."""
        if isinstance(atoms, str):
            self.nodeLogString = "'"+atoms+"'"
        ats = self.app().expandNodes(atoms)
        assert ats
        # MS here we create a copy of what findType returns
        ats = ats.findType(Atom)
        return (ats,), {}


    def doit(self, ats):
        """ Function to delete all the references to each atom  of a
        AtomSet."""

        # Remove the atoms of the molecule you are deleting from the
        # the AtomSet self.app().allAtoms
        self.app().allAtoms = self.app().allAtoms - ats
        event = DeleteAtomsEvent(objects=ats)
        self.app().eventHandler.dispatchEvent(event)
        #  Call the updateGeoms function for all the command having an
        # updateGeom function
        done = 0
        allAtoms = AtomSet([])
        app = self.app()
        molecules, atomSets = self.app().getNodesByMolecule(ats)

        selectedAtoms = app.curSelection.get()
        for mol, atSet in map(None, molecules, atomSets):

            # remove atoms from the names selections if necessary
            if app.curSelection.isAnySelected(atSet):
                app.curSelection.remove(atSet)
                event = SelectionEvent(
                    app.activeSelection, new=app.curSelection.get(), old=selectedAtoms,
                    setOn=app.curSelection.get()-selectedAtoms,
                    setOff=selectedAtoms-app.curSelection.get())
                app.eventHandler.dispatchEvent(event)
               
            for name, sel in app.namedSelections.items():
                if sel.isAnySelected(atSet):
                    sel.remove(atSet)
                    event = SelectionEvent(
                        app.activeSelection, new=app.curSelection.get(), old=selectedAtoms,
                        setOn=sel.get()-selectedAtoms, setOff=selectedAtoms-sel.get())
                    app.eventHandler.dispatchEvent(event)

            # delete the atoms
            if len(atSet)==len(mol.allAtoms):
                #have to add atoms back to allAtoms for deleteMol to work
                app.allAtoms = app.allAtoms + atSet
                app.undo.cleanCmdStack(mol)
                app.redo.cleanCmdStack(mol)
                if hasattr(app.deleteMol, 'loadCommand'):
                    app.deleteMol.loadCommand()
                app.deleteMol.deleteMol(mol)
                #if this is the last atom, quit the loop
                if mol==molecules[-1]:
                    done=1
                    break
                continue

            mol.allAtoms = mol.allAtoms - atSet
            allAtoms = allAtoms + atSet
            #FIRST remove any possible hbonds
            hbondAts = atSet.get(lambda x: hasattr(x, 'hbonds'))
            if hbondAts is not None:
                #for each atom with hbonds
                for at in hbondAts:
                    if not hasattr(at, 'hbonds'):
                        continue
                    #remove each of its hbonds 
                    for b in at.hbonds:
                        self.removeHBond(b)
        
            atSetCopy = atSet.copy() #fixed bug#:       1143
            for at in atSetCopy:
                for b in at.bonds:
                    at2 = b.atom1
                    if at2 == at: at2 = b.atom2
                    at2.bonds.remove(b)
                if at.parent.children:
                    at.parent.remove(at, cleanup=1)

        ## atmsInSel = app.selection.get()
        ## atmsInSel.sort()
        ## ats.sort()
        ## if len(atmsInSel):
        ##     if atmsInSel == ats:
        ##         # the current selection was deleted 
        ##         #app.clearSelection(createEvents=False)
        ##         app.clearSelection()
        ##     else:
        ##         nodes = app.selection
        ##         lenSel = len(nodes)
        ##         setClass = nodes.__class__
        ##         elementClass = nodes.elementType
        ##         if lenSel>0:
        ##             # this breaks if selectionlevel is Molecule, for instance
        ##             # setClass = nodes.__class__
        ##             # newSel = setClass(nodes.findType(Atom) - ats)
        ##             # newSel2 = setClass([])
        ##             newSel = atmsInSel-ats
        ##             newSel2 = AtomSet([])
        ##             # may have ats which have been deleted everywhere else
        ##             for at in newSel:
        ##                 if at in at.top.allAtoms:
        ##                     newSel2.append(at)
        ##             if len(newSel2)!=lenSel:
        ##                 app.clearSelection()
        ##                 if len(newSel2):
        ##                     newSel2 = newSel2.findType(elementClass).uniq()
        ##                     app.select(newSel2)

        # this fixes an exception that occured when the last chain was split
        # out of a protein
        if not done:
            event = AfterDeleteAtomsEvent(objects=ats)
            app.eventHandler.dispatchEvent(event)
        
        #this fixed a bug which occured when only 1 molecule present
        #and cmd invoked with mv.deleteAtomSet(mv.Mols[0].allAtoms)
        if not done:
            for at in ats: del at
        #app.resetUndo()
                    
    def removeHBond(self, b):
        atList = [b.donAt, b.accAt]
        if b.hAt is not None:
            atList.append(b.hAt)
        for at in atList:
            #hbonds might already be gone
            if not hasattr(at, 'hbonds'):
                continue
            okhbnds = []
            for hb in at.hbonds:
                if hb!=b:
                    okhbnds.append(hb)
            if len(okhbnds):
                at.hbonds = okhbnds
            else:
                delattr(at, 'hbonds')
        return 



class DeleteCurrentSelection(DeleteAtomSet):
    """ Command to remove an AtomSet from the MoleculeViewer \n
    Package : PmvApp \n
    Module  : deleteCmds \n
    Class   : DeleteCurrentSelection \n
    Command : deleteCurrentSelection \n
    Synopsis:\n
        None<---deleteCurrentSelection()\n
    Required Arguments:\n
        None
    """
    
    def checkArguments(self):
        """None <- deleteCurrentSelection()
        """
        return (), {}


    def doit(self):
        """ Function to delete all the references to each atom of a
        the currentSelection."""

        atoms = old = self.app().activeSelection.get()[:] # make copy of selection
        ats = self.app().expandNodes(atoms)
        if not len(ats):
            return
        ats = ats.findType(Atom)

        self.app().clearSelection(log=0)
        DeleteAtomSet.doit(self, ats)



class DeleteHydrogens(DeleteAtomSet):
    """ Command to remove hydrogen atoms from the MoleculeViewer  \n
    Package : PmvApp
    Module  : deleteCmds  \n
    Class   : DeleteHydrogens  \n
    Command : deleteHydrogens  \n
    Synopsis:\n
        None<---deleteHydrogens(atoms)\n
    Required Arguments:\n 
        atoms --- Hydrogens found in this atom set are deleted.\n
    """

    def checkArguments(self, atoms):
        """None <- deleteHydrogents(atoms) \n
        atoms: set of atoms, from which hydrogens are to be deleted."""
        if isinstance(atoms, str):
            self.nodeLogString = "'"+atoms+"'"
        
        ats = self.app().expandNodes(atoms)
        assert ats
        return (ats,), {}


    def doit(self, ats):
        hatoms = ats.get(lambda x: x.element=='H')
        if not len(hatoms):
            self.app().warningMsg("No hydrogens to delete.")
            return
        DeleteAtomSet.doit(self, hatoms)


# use for backwards compat with old cmd name deleteMol
class DeleteMoleculeOLD(DeleteMolecules):

    def checkArguments(self, *args, **kw):
        print 'deleteMol is depreacted use deleteMolecules'
        return DeleteMolecules.checkArguments(self, *args, **kw)
        
        
commandClassFromName = {
    'deleteMol' : [DeleteMoleculeOLD,  None],
    'deleteMolecules' : [DeleteMolecules,  None],
    'deleteAllMolecules' : [DeleteAllMolecules, None],
    'deleteAtomSet' : [DeleteAtomSet,  None ],
    'deleteCurrentSelection' : [DeleteCurrentSelection, None ],
    'deleteHydrogens' : [DeleteHydrogens,  None],
    'restoreMol' : [RestoreMolecule,  None],
}


def initModule(viewer, gui=True):
    for cmdName, values in commandClassFromName.items():
        cmdClass, guiInstance = values
        if gui:
            viewer.addCommand(cmdClass(), cmdName, guiInstance)
        else:
            viewer.addCommand(cmdClass(), cmdName, None)

