#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2013
#
#########################################################################
#
# $Header: /opt/cvs/PmvApp/Pmv.py,v 1.34 2014/07/16 23:45:08 annao Exp $
#
# $Id: Pmv.py,v 1.34 2014/07/16 23:45:08 annao Exp $
#

"""
define a class for a molecular viewer
"""
import os, weakref
from AppFramework.App import AppFramework, GeomContainer, AddGeometryEvent
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet, MoleculeGroup
from MolKit.protein import Protein, ProteinSet, Chain, ChainSet, Residue, ResidueSet
from MolKit.sets import Sets
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.stringSelector import CompoundStringSelector
from mglutil.events import Event
import numpy

def reduceName(name, length):
    """ turn the string name into 'start of name ... end of name' if length of name
is greater than length
"""
    if len(name) < length: return name
    return name[:length/2]+'...'+name[-length/2:]

def formatName(repStr, maxLength):
    """format the string name so that no line exceeds maxLength characters
    """
    if len(repStr)>maxLength:
        pt = 0
        frepStr = ""
        while pt < len(repStr):
            frepStr += repStr[pt:min(pt+maxLength, len(repStr))]+'\n'
            pt += maxLength
        frepStr = frepStr[:-1]
    else:
        frepStr = repStr
    return frepStr
    
numOfSelectedVerticesToSelectTriangle = 1 # 1 , 2 or 3

class RenameSelectionEvent(Event):
    # event.item item associate with event.selection
    # event.selection selection that was renamed
    # event.setCurrent True if curSelection was renamed and was active
    pass

class RenameGroupEvent(Event):
    # event.item item associate with event.object
    # event.object group that was renamed
    pass
    
class RenameTreeNodeEvent(Event):
    # event.object TreeNodeE that was renamed
    pass
    
class AddGroupEvent(Event):
    # event is created when group is added to Pmv
    # event.group is the group that was added
    pass

class DeleteGroupsEvent(Event):
    # event is created when group is added to Pmv
    # event.group is the group that was deleted
    pass

class ReparentGroupObject(Event):
    # event is created when a group or a molecule is move to a new parent
    # event.newGroup is the group which is the new parent of event.object
    # event.oldGroup is the group which was the old parent of event.object
    # event.object is the object reparented
    pass

class ActiveSelectionChangedEvent(Event):
    # event is created when pmv's active selection object is replaced by a new one
    # event.current is the new Selection object
    # event.previous is the old Selection object
    pass

class DeleteNamedSelectionEvent(Event):
    # event is created when a named selection is deleted
    # event.selection the deleted Selection object
    pass


class StartAddMoleculeEvent(Event):
    # event is created at the begging of the addition of an molecule
    #
    # event.name is the name of the molecule added
    # event.object is the molecule being added
    pass

class AddMoleculeCmdEvent(Event):
    # event is created each time we call a command to be carried out on
    #  an molecule that is added
    #
    # event.number number of command currently called
    # event.total total number of commands to be called
    # event.cmdName name of the command currently called
    pass


class EndAddMoleculeEvent(Event):
    # event is created after the molecule has been added
    # 
    # event.object is the molecule that has been added
    pass


class BeforeDeleteMoleculeEvent(Event):
    # event is created before the molecule is deleted
    # 
    # event.object is the molecule that is being deleted
    pass

class AfterDeleteMoleculeEvent(Event):
    # event is created after the molecule is deleted
    # 
    # event.object the molecule that has been deleted
    pass


class EditAtomsEvent(Event):
    # event is created when atom properties are modified
    # event.objects - AtomSet
    def __init__(self, name=None, objects=[], *args, **kw):
        Event.__init__(self, *args, **kw)
        self.objects = objects
        self.name = name

class DeleteAtomsEvent(Event):
    pass

class AfterDeleteAtomsEvent(Event):
    pass

class AddAtomsEvent(Event):
    pass

class ShowMoleculesEvent(Event):
    pass

class AddGeomsEvent(Event):
    pass

class DeleteGeomsEvent(Event):
    pass

class EditGeomsEvent(Event):
     def __init__(self, name=None, objects=[], *args, **kw):
        Event.__init__(self, *args, **kw)
        self.objects = objects
        self.name = name


moleculeEvents = {
    'startAddObject' : StartAddMoleculeEvent,
    'addObjectCmd' : AddMoleculeCmdEvent,
    'endAddObject' : EndAddMoleculeEvent,
    'beforeDeleteObject' : BeforeDeleteMoleculeEvent,
    'afterDeleteObject' : AfterDeleteMoleculeEvent
    }

class Selection:
    # class to store a selection in Pmv

    def __init__(self, app, name='selection', nodes=None):
        self.app = app
        self.name = name
        self.children = []
        self.atomsDict = {}
        if nodes:
            self.set(nodes)
        else:
            self.atoms = AtomSet([])
        self.setClass = SelectionSet

    def __len__(self):
        return len(self.atoms)
    
    def __sub__(self, other):
        sel = self.copy()
        if isinstance(obj, Selection):
            sel.atoms -= other.atoms
        else:
            sel.atoms -= other.findType(Atom)
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel
    
    def __add__(self, other):
        sel = self.copy()
        if isinstance(obj, Selection):
            sel.atoms += other.atoms
        else:
            sel.atoms += other.findType(Atom)
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel
    
    def __or__(self, other):
        sel = self.copy()
        if isinstance(obj, Selection):
            sel.atoms = sel.atoms | other.atoms
        else:
            sel.atoms = sel.atoms | other.findType(Atom)
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel
    
    def __inter__(self, other):
        sel = self.copy()
        if isinstance(obj, Selection):
            sel.atoms = sel.atoms.__inter__(other.atoms)
        else:
            sel.atoms = sel.atoms.__inter__(other.findType(Atom))
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel
    
    def __xor__(self, other):
        sel = self.copy()
        if isinstance(obj, Selection):
            sel.atoms = sel.atoms.__xor__(other.atoms)
        else:
            sel.atoms = sel.atoms.__xor__(other.findType(Atom))
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel
    
    def __and__(self, other):
        sel = self.copy()
        if isinstance(obj, Selection):
            sel.atoms = sel.atoms & other.atoms
        else:
            sel.atoms = sel.atoms & other.findType(Atom)
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel

    def copy(self):
        sel = Selection(self.app, self.name)
        sel.atoms = self.atoms.copy()
        sel.children = self.atoms.top.uniq()
        sel.update()
        #print 'asda', self.children, len(self.children)
        return sel
    
    def empty(self):
        if len(self.atoms): return False
        return True

    def get(self, klass=Atom):
        if klass==Atom:
            return self.atoms.copy()
        elif klass==Residue:
            return self.atoms.parent.uniq()
        elif klass==Chain:
            return self.atoms.parent.parent.uniq()
        elif klass==Molecule or klass==Protein:
            return self.atoms.top.uniq()
        
    def set(self, obj):
        #print 'setting selection', self.name, str(obj)
        if isinstance(obj, AtomSet):
            self.atoms = obj
        else:
            self.atoms = obj.findType(Atom)
        self.atoms = self.atoms.uniq()
        #print 'asda', self.children, len(self.children)
        self.update()

    def isSelected(self, obj):
        # returns True if all atoms in obj are selected
        #         False is all atoms in obj are deselected
        #         'partial' else
        if not isinstance(obj, AtomSet):
            atoms = obj.findType(Atom)
        else:
            atoms = obj

        if len(self.atoms)==0: return False
        
        # selection status of first atom
        sel0 = self.atomsDict.has_key(atoms[0])
        for a in atoms[1:]:
            sel = self.atomsDict.has_key(a)
            if sel!=sel0:
                return 'partial'
        return sel0

    def isNotSelected(self, obj, mode='fast'):
        if not isinstance(obj, AtomSet):
            atoms = obj.findType(Atom)
        else:
            atoms = obj
        if mode=='fast':
            for a in atoms:
                d = self.atomsDict.get(a, None)
                if d is None:
                    return True
            return False
        elif mode=='complete':
            raise
        else:
            raise RuntimeError("Bad mode %s, expected 'fast' or 'complete'"%mode)

    def isAnySelected(self, obj, mode='fast'):
        if not isinstance(obj, AtomSet):
            atoms = obj.findType(Atom)
        else:
            atoms = obj
        if mode=='fast':
            for a in atoms:
                d = self.atomsDict.get(a, None)
                if d is not None:
                    return True
            return False
        elif mode=='complete':
            raise
        else:
            raise RuntimeError("Bad mode %s, expected 'fast' or 'complete'"%mode)

    def add(self, obj):
        #print 'setting selection', self.name, str(obj)
        if isinstance(obj, Selection):
            self.atoms += obj.atoms
        else:
            self.atoms += obj.findType(Atom)
        self.atoms = self.atoms.uniq()
        #print 'asda', self.children, len(self.children)
        self.update()

    def remove(self, obj):
        #print 'setting selection', self.name, str(obj)
        if isinstance(obj, Selection):
            self.atoms -= obj.atoms
        else:
            self.atoms -= obj.findType(Atom)
        #print 'asda', self.children, len(self.children)
        self.update()

    def xor(self, obj):
        #print 'setting selection', self.name, str(obj)
        if isinstance(obj, Selection):
            self.atoms = self.atoms ^ obj.atoms
        else:
            self.atoms = self.atoms ^ obj.findType(Atom)
        #print 'asda', self.children, len(self.children)
        self.update()

    def inter(self, obj):
        #print 'setting selection', self.name, str(obj)
        if isinstance(obj, Selection):
            self.atoms = self.atoms & obj.atoms
        else:
            self.atoms = self.atoms & obj.findType(Atom)
        #print 'asda', self.children, len(self.children)
        self.update()
        
    def update(self):
        # compute self.children and self.atomsDict
        self.children = self.atoms.top.uniq()
        self.atomsDict = {}.fromkeys(self.atoms, True)
        
    def clear(self):
        self.atoms.data = []
        self.atomsDict = {}

from MolKit.listSet import ListSet
class SelectionSet(ListSet):

    def __init__(self, data=None, elementType=Selection, **kw):
        ListSet. __init__(self, data=data, elementType=Selection)

        
class MolApp(AppFramework):
    """
    Application that support lazy loading of commands
    """

    def exit(self):
        AppFramework.exit(self)

        
    def __init__(self, title="Molecule Viewer", eventHandler=None):

        AppFramework.__init__(self, name=title, eventHandler=eventHandler)

        self.molecules = MoleculeGroup('All Molecules')
        self.Mols = self.molecules.children # store the molecules read in
        self.lastMolNumer = 0 # used to give molecules unique numbers
        
        self.sets = Sets()  # store user-defined sets in this dict
        self.Vols = [] # list of Grid3D objects storing volumetric data
        self.allAtoms = AtomSet() # set of all atoms (across molecules)
        
        def moleculeValidator(mol):
            return isinstance(mol, Molecule)
          
        self.addObjectType("Molecule", moleculeValidator, moleculeEvents)
        self.objects["Molecule"] = self.Mols

        ## selections
        ##
        self.curSelection = Selection(self, u'Current Selection')
        # activeSelection always hold a Selection which is either
        # self.curSelection or a named selection
        self.activeSelection = self.curSelection
        self.namedSelections = {}
        self.selectionLevel = Atom

        ## groups
        ##
        self.groups = {} # name: MoleculeGroup Instance
        
        # this levelColors attribute used to be in ICmdCaller (???)
        # the level variable is used by selection commands
        self.levelColors = {
            'Atom':(1.,1.,0.),
            'Residue':(0.,1.,0.),
            'Chain':(0.,1.,1.),
            'Molecule':(1.,0.,0.),
            'Protein':(1.,0.,0.),
            }
        choices = ['molecules', 'chains', 'conformations']
        choice = 'molecules'
        self.userpref.add('Read molecules as', choice, validValues=choices,
                          category="Molecules",
                          doc = """for pdb file with multi MODEL, can be read as 'molecules', 'chains', 'conformations'.chains' is not yet implemented (7/09)""")

        choices = ['caseSensitive', 'caseInsensitive',
                   'caseInsensWithEscapedChars']

        self.userpref.add('String Matching Mode', 'caseSensitive', validValues=choices,
                          doc = """When set to caseSensitive the string match
mode will be case sensitive the other possibility is to be case insensitive or
case insensitive with escaped characters.
""")

    ##
    ## Renaming objects
    ##
    def rename(self, obj, name, item=None):
        """Rename Pmv objects
None <- pmv.rename(obj, item, name)
obj: object or name of an object (Objects can be selections, groups or molecular fragments
name: usesr defined name for the object
items: is the item associate with the object in the Dashboard, or None

For groups and selections the name will overwrite the old name. For molecular fragments
the name will become the alias for this object
"""
        inUndo = self.undo.inUndo
        inRedo = self.redo.inUndo
        if isinstance(obj, str):
            # turn the string into an object
            if obj == 'Current Selection':
                obj = self.curSelection
            elif obj in self.namedSelections.keys():
                obj = self.namedSelections[obj]
            elif obj in self.groups.keys():
                obj = self.groups[obj]
            else:
                objs = self.expandNodes(obj)
                if len(objs)==0:
                    raise ValueError, "%s is not a selection, group or molecular fragment"%obj
                obj = objs

        if isinstance(obj, Selection):
            # make sure the name is not already used
            if obj.name == name: return
            if name=='Current Selection' or name in self.namedSelections.keys():
                raise ValueError, "%s is alreday use for a selection"%name
            if obj == self.curSelection:
                obj.name = name
                # save it in named selections
                self.namedSelections[name] = obj
                self.curSelection = Selection(self, u'Current Selection')
                event = RenameSelectionEvent(item=item, selection=obj,
                                             setCurrent=(obj==self.activeSelection))
                self.eventHandler.dispatchEvent(event)
                def mkSelCurSel(selection, item=None):
                    self.curSelection = selection
                    old = selection.name
                    del self.namedSelections[selection.name]
                    selection.name = u'Current Selection'
                    if self.undo.inUndo>=0: # we are in undo mode 
                        self.undo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})]  )
                        if self.undo.inUndo==0:
                            self.redo.addUndoCall(*self.undo._cmdList )
                    event = RenameSelectionEvent(item=item, selection=selection,
                                                 setCurrent=(selection==self.activeSelection))
                    self.eventHandler.dispatchEvent(event)
                if inUndo==-1 and inRedo==-1: # not doing Undo or Redo
                    self.undo.addUndoCall( [(mkSelCurSel, (obj,), {'item':item})],
                                           'rename "Current Selection' )
                else:
                    if inRedo>=0: # we are in redo mode 
                        self.redo._cmdList[0].extend([(mkSelCurSel, (obj,), {'item':item})] )
                        if inRedo==0:
                            self.undo.addUndoCall( *self.redo._cmdList )
                    
            else:
                namedSelection = obj
                old = obj.name
                del self.namedSelections[namedSelection.name]
                namedSelection.name = name
                self.namedSelections[namedSelection.name] = namedSelection

                event = RenameSelectionEvent(item=item, selection=obj)
                self.eventHandler.dispatchEvent(event)
                if inUndo==-1 and inRedo==-1: # not doing Undo or Redo
                    self.undo.addUndoCall( [(self.rename, (obj, old), {'item':item})],
                                           'rename %s'%old )
                else:
                    if inUndo>=0: # we are in undo mode 
                        self.undo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})] )
                        if inUndo==0:
                            self.redo.addUndoCall(*self.undo._cmdList )
                    else: # redo mode
                        self.redo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})] )
                        if inRedo==0:
                            self.undo.addUndoCall( *self.redo._cmdList )

        elif isinstance(obj, MoleculeGroup):
            if obj.name == name: return
            if name in self.groups.keys():
                raise ValueError, "%s is alreday use for a group"%name
            old = obj.name
            self.groups[name] = obj
            del self.groups[obj.name]
            obj.name = name
            event = RenameGroupEvent(object=obj, item=item)
            self.eventHandler.dispatchEvent(event)
            if inUndo==-1 and inRedo==-1: # not doing Undo or Redo
                self.undo.addUndoCall( [(self.rename, (obj, old), {'item':item})],
                                       'rename %s'%old )
            else:
                if inUndo>=0: # we are in undo mode 
                    self.undo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})] )
                    if inUndo==0:
                        self.redo.addUndoCall(*self.undo._cmdList )
                else: # redo mode
                    self.redo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})] )
                    if inRedo==0:
                        self.undo.addUndoCall( *self.redo._cmdList ) 

        elif isinstance(obj, TreeNode):
            old = obj.alias
            obj.alias = name
            event = RenameTreeNodeEvent(object=obj)
            self.eventHandler.dispatchEvent(event)
            if inUndo==-1 and inRedo==-1: # not doing Undo or Redo
                self.undo.addUndoCall( [(self.rename, (obj, old), {'item':item})],
                                       'rename %s'%obj.name )
            else:
                if inUndo>=0: # we are in undo mode 
                    self.undo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})] )
                    if inUndo==0:
                        self.redo.addUndoCall(*self.undo._cmdList )
                else: # redo mode
                    self.redo._cmdList[0].extend([(self.rename, (obj, old), {'item':item})] )
                    if inRedo==0:
                        self.undo.addUndoCall( *self.redo._cmdList )             

        elif isinstance(obj, TreeNodeSet):
            undo = []
            undoName = ""
            for ob in obj:
                old = ob.alias
                ob.alias = name
                event = RenameTreeNodeEvent(object=ob)
                self.eventHandler.dispatchEvent(event)
                undo.append( (self.rename, (ob, old), {'item':item}) )
                undoName += ob.name+', '
            undoName = reduceName(undoName[:-2], 60)
            if self.undo.inUndo==-1 and self.redo.inUndo==-1: # not doing Undo or Redo
                self.undo.addUndoCall( undo, 'rename %s'%undoName) 
        else:
            print 'RENAMING %s not implemented', obj.__class__

    ##
    ## Groups
    ##
    def _deleteGroupTree(self, obj):
        if isinstance(obj, Protein):
            self.deleteMolecules(MoleculeSet([obj]))
        else:
            for ob in obj.children:
                self._deleteGroupTree(ob)
            del self.groups[obj.name]
        
    def deleteGroups(self, groups):
        for group in groups:
            self._deleteGroupTree(group)
        event = DeleteGroupsEvent(groups=groups)
        self.eventHandler.dispatchEvent(event)

    def addGroup(self, name, parentGroup=None):
        assert name not in self.groups.keys()
        grp = MoleculeGroup(name)
        if isinstance(parentGroup, str):
            parentGroup = self.groups[parentGroup]
        self.groups[name] = grp
        grp._group = None
        event = AddGroupEvent(group=grp)
        self.eventHandler.dispatchEvent(event)
        if parentGroup is not None:
            assert isinstance(parentGroup, MoleculeGroup)
            self.reparentObject(grp, parentGroup)
        return grp
    
    def reparentObject(self, obj, group):
        assert group is None or isinstance(group, MoleculeGroup)
        assert isinstance(obj, (Protein, MoleculeGroup))
        oldGroup = None
        if hasattr (obj, "_group"):
            oldGroup = obj._group
        if oldGroup:
            oldGroup.children.remove(obj)
        if group is not None:
            group.children.append(obj)
        obj._group = group
        event = ReparentGroupObject(newGroup=group, oldGroup=oldGroup, object=obj)
        self.eventHandler.dispatchEvent(event)
    
    ## def addObjectToGroup(self, group, obj):
    ##     assert isinstance(group, MoleculeGroup)
    ##     assert isinstance(obj, (Protein, MoleculeGroup))
    ##     group.children.append(obj)
    ##     obj._group = group
    ##     event = AddObjectToGroupEvent(group=group, object=obj)
    ##     self.eventHandler.dispatchEvent(event)
        
    ## def removeObjectFromGroup(self, group, obj):
    ##     assert isinstance(group, MoleculeGroup)
    ##     assert isinstance(obj, (Protein, MoleculeGroup))
    ##     group.children.remove(obj)
    ##     del obj._group
    ##     event = RemoveObjectFromGroupEvent(group=group, object=obj)
    ##     self.eventHandler.dispatchEvent(event)
        
    ##
    ## Selections
    ##
    def setCurrentSelection(self, sele):
        """Set the pmv's active selection which is the selection on which \
        pmv.select will operate
Events: ActiveSelectionChangedEvent(old=oldSelection, new=newSelection)
        """
        assert isinstance(sele, Selection)
        oldSele = self.activeSelection
        self.activeSelection = sele
        event = ActiveSelectionChangedEvent(old=oldSele, new=sele)
        self.eventHandler.dispatchEvent(event)

    def deleteNamedSelection(self, sele):
        del self.namedSelections[sele.name]
        if sele == self.activeSelection:
            self.clearSelection()
            self.activeSelection = self.curSelection
        event = DeleteNamedSelectionEvent(selection=sele)
        self.eventHandler.dispatchEvent(event)
        
    def setSelection(self, obj):
        """Set the content of the active selection to be alist of atoms
provided by obj
        """
        if isinstance(obj, Selection):
            self.activeSelection.atoms = obj.atoms[:]
            self.activeSelection.update()
        else:
            self.activeSelection.set(obj)

    def isNotSelected(self, obj, mode='fast'):
        self.activeSelection.isNotSelected( obj, mode=mode)


    def setSelLev(self, value):
        if value==Protein: value = Molecule
        assert value in [Molecule, Chain, Residue, Atom]
        self.setSelectionLevel(value)
      
    
    def readMolecule(self, filename, addToRecent=True, modelsAs='molecules', group=None):
        """Reads molecule in the following formats: pdb, ent, pdbq, \
         pqr, mol2, cif.
        Adds the molecule object to the application
        group is a MoleculeGroup instance or a name(string) of existing group, if not None , the molecule is addded
        to the specified group. 
        """
        fileExt = os.path.splitext(filename)[1]
        # Call the right method for reading the file:
        if fileExt == ".pdb" or fileExt == ".ent":
            mols = self.readPDB(filename, modelsAs=modelsAs, group=group)
        elif fileExt == ".pdbqt":
            mols = self.readPDBQT(filename, modelsAs=modelsAs, group=group)
        elif fileExt == ".pqr":
            mols = self.readPQR(filename, modelsAs=modelsAs, group=group)
        elif fileExt == ".mol2":
            mols = self.readMOL2(filename, modelsAs=modelsAs, group=group)
        elif fileExt == ".cif":
            mols = self.readMMCIF(filename, modelsAs=modelsAs, group=group)
        elif fileExt == ".pdbq":
            raise ValueError, "There is no parser for PDBQ files"
            #mols = self.readPDBQ(filename, ask=ask, modelsAs=modelsAs)
        elif fileExt == ".pdbqs":
            raise ValueError, "There is no parser for PDBQS files"
            #mols = self.readPDBQS(filename,ask=ask, modelsAs=modelsAs)
        elif fileExt == ".gro":
            raise ValueError, "There is no parser for GRO files"
            #mols = self.readGRO(filename, ask=ask)
        elif fileExt == ".f2d":
            raise ValueError, "There is no parser for F2D files"
            #mols = self.readF2D(filename, ask=ask)
        elif fileExt == ".sdf":
            raise ValueError, "There is no parser for SDF files"
            #mols = self.readSDF(filename, ask=ask)
        else:
            raise ValueError, "Extension %s not recognized"%fileExt
        if addToRecent and hasattr(self,'recentFiles'):
            self.recentFiles.add(filename, 'guiSafeLoadMolecule')
        return mols

        
    def readPDB(self, filename, modelsAs='molecules', group=None):
        if modelsAs is None:
            modelsAs = self.userpref['Read molecules as']['value']

        from MolKit.pdbParser import PdbParser
        newparser = PdbParser(filename, modelsAs=modelsAs)

        mols = newparser.parse()
        if mols is None:
            del newparser
            return 
        newmol = []
        for m in mols:
            mol = self.addMolecule(m, group=group)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def readPDBQT(self, filename, modelsAs='molecules', group=None):
        from MolKit.pdbParser import PdbqtParser
        newparser = PdbqtParser(filename, modelsAs=modelsAs)
        mols = newparser.parse()
        if mols is None:
            del newparser
            return 
        newmol = []
        for m in mols:
            mol = self.addMolecule(m, group=group)
            if mol is None:
                del newparser
                return 
            newmol.append(mol)
        return mols.__class__(newmol)


    def readPQR(self, filename, modelsAs='molecules', group=None):
        from MolKit.pdbParser import PQRParser
        newparser = PQRParser(filename, modelsAs=modelsAs)
        mols = newparser.parse()
        if mols is None :
            del newparser
            return
        newmol = []
        for m in mols:
            mol = self.addMolecule(m, group=group)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def readMMCIF(self, filename, modelsAs='molecules', group=None):
        from MolKit.mmcifParser import MMCIFParser
        newparser = MMCIFParser(filename)
        mols = newparser.parse()
        if mols is None: return
        newmol = []
        for m in mols:
            mol = self.addMolecule(m, group=group)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)


    def readMOL2(self, filename, modelsAs='molecules', group=None):
        from MolKit.mol2Parser import Mol2Parser
        newparser = Mol2Parser(filename)
        mols = newparser.parse()
        newmol = []
        if mols is None: return
        for m in mols:
            mol = self.addMolecule(m, group=group)
            if mol is None:
                del newparser
                return mols.__class__([])
            newmol.append(mol)
        return mols.__class__(newmol)

        
    def addMolecule(self, newmol, group=None):
        """
        Add a molecule to the application 
        """
        assert len(newmol.allAtoms) > 0, "Empty molecule. No atom record found for %s." % newmol.name
        #IN ANY CASE: change any special characters in name to '-'
        spChar=['?','*','.','$','#',':','-',',']        
        for item in spChar:
            newmol.name = newmol.name.replace(item, '_')
        if len(self.Mols) > 0:
            if newmol.name in self.Mols.name:
                newmol.name='%s_%d'%(newmol.name,len(self.Mols))

        newmol.allAtoms.setStringRepr(newmol.full_name()+':::')
        
        # provide hook for progress bar
        # old code: newmol.allAtoms._bndIndex_ = range(len(newmol.allAtoms))

        #if self.hasGui:
        #    self.GUI.configureProgressBar(init=1, mode='increment',
        #                              max=len(newmol.allAtoms),
        #                              labeltext='add molecule to viewer')
        i = 0
        for a in newmol.allAtoms:
            a._bndIndex_ = i
            #if self.hasGui:
            #    self.GUI.updateProgressBar()
            i = i + 1

        g = MolGeomContainer(newmol, self)
        #if hasattr(newmol, 'spaceGroup'):
        #    self.lazyLoadCommands ('crystalCommands', package='Pmv')
        newmol.unitedRadii = None # set to None to force initial radii assignment
        self.lastMolNumer += 1
        newmol.number = self.lastMolNumer
        
        nchains = len(self.Mols.chains)
        for i, c in enumerate(newmol.chains):
            c.number = nchains+i
            
        self.addObject(newmol.name, newmol, "Molecule", g)

        self.Mols.setStringRepr(self.Mols.full_name())

        self.allAtoms = self.allAtoms + newmol.allAtoms
        self.allAtoms.setStringRepr(self.Mols.full_name()+':::')
        
        #event = StartAddMoleculeEvent(newmol)
        #print 'DASDASDA', event, dir(event)
        #self.eventHandler.dispatchEvent(event)
        if group:
            if isinstance(group, str):
                group = self.groups[group]
            assert isinstance(group, MoleculeGroup)
            self.reparentObject(newmol, group)
        else:
            newmol._group = None
            
        return newmol


    def getNodesByMolecule(self, nodes, nodeType=None):
        """ moleculeSet, [nodeSet, nodeSet] <- getNodesByMolecule(nodes, nodeType=None)
        nodes can be either: a string, a TreeNode or a TreeNodeSet.
        This method returns a molecule set and for each molecule a TreeNodeSet
        of the nodes belonging to this molecule.
        'nodeType' enables a desired type of nodes to be returned for each
        molecule
        """

        # special case list of complete molecules to be expanded to atoms
        # this also covers the case where nothing is selected
        #if isinstance(nodes, MoleculeSet) or isinstance(nodes, ProteinSet):
        if isinstance(nodes, ProteinSet):
            if nodeType is Atom:
                atms = []
                for mol in nodes:
                    atms.append(mol.allAtoms)
                return nodes, atms
            elif (nodeType is Protein) or (nodeType is Molecule):
                return nodes, nodes
        
        # if it is a string, get a bunch of nodes from the string
        if isinstance(nodes, str):
            nodes = self.expandNodes(nodes)

        assert issubclass(nodes.__class__, TreeNode) or \
               issubclass(nodes.__class__, TreeNodeSet)

        # if nodes is a single TreeNode make it a singleton TreeNodeSet
        if issubclass(nodes.__class__, TreeNode):
            nodes = nodes.setClass([nodes])
            nodes.setStringRepr(nodes.full_name())

        if len(nodes)==0: return MoleculeSet([]), []

        # catch the case when nodes is already a MoleculeSet
        if nodes.elementType in [Molecule, Protein]:
            molecules = nodes
        else: # get the set of molecules
            molecules = nodes.top.uniq()

        # build the set of nodes for each molecule
        nodeSets = []

        # find out the type of the nodes we want to return
        searchType=0
        if nodeType is None:
            Klass = nodes.elementType # class of objects in that set
        else:
            assert issubclass(nodeType, TreeNode)
            Klass = nodeType
            if Klass != nodes.elementType:
                searchType=1

        for mol in molecules:
            # get set of nodes for this molecule
            mol_nodes = nodes.get(lambda x, mol=mol: x.top==mol)

            # get the required types of nodes
            if searchType:
                if Klass == Atom and hasattr(mol_nodes, 'allAtoms'):
                    mol_nodes = mol_nodes.allAtoms
                else:
                    mol_nodes = mol_nodes.findType( Klass ).uniq()

            nodeSets.append( mol_nodes )

        return molecules, nodeSets


    def expandNodes(self, nodes):
        """Takes nodes as string or TreeNode or TreeNodeSet and returns
a TreeNodeSet
If nodes is a string it can contain a series of set descriptors with operators
separated by / characters.  There is always a first set, followed by pairs of
operators and sets.  All sets ahve to describe nodes of the same level.

example:
    '1crn:::CA*/+/1crn:::O*' describes the union of all CA ans all O in 1crn
    '1crn:::CA*/+/1crn:::O*/-/1crn::TYR29:' 
"""
        if isinstance(nodes,TreeNode):
            result = nodes.setClass([nodes])
            result.setStringRepr(nodes.full_name())

        elif isinstance(nodes, str):
            stringRepr = nodes
            css = CompoundStringSelector()
            result = css.select(self.Mols, stringRepr)[0]
        elif isinstance(nodes,TreeNodeSet):
            result = nodes
        else:
            raise ValueError, 'Could not expand nodes %s\n'%str(nodes)
        return result


    def getMolFromName(self, name):
        """
        Return the molecule of a given name, or the list of molecules of given
        names.
    
        @type  name: string or list
        @param name: the name of the molecule, or a list of molecule name
        @rtype:   MolKit.protein or list
        @return:  the molecule or the list of molecules for the given name(s).
        """
        
        if type(name) is list :
            mol = [x for x in self.Mols if x.name in name]
        else : 
            mols = [x for x in self.Mols if x.name==name]
            if len(mols):
                mol = mols[0]
            else:
                mol = None
        return mol


    def transformedCoordinatesWithInstances(self, nodes):
        """ for a nodeset, this function returns transformed coordinates.
This function will use the pickedInstance attribute if found.
"""
        # nodes is a list of atoms, residues, chains, etc. where each member
        # has a pickedInstances attribute which is a list of 2-tuples
        # (object, [i,j,..])
        vt = []
        for node in nodes:
            #find all atoms and their coordinates
            coords = nodes.findType(Atom).coords
            if hasattr(node, 'pickedInstances'):
                # loop over the pickedInstances of this node
                for inst in node.pickedInstances:
                    geom, instance = inst # inst is a tuple (object, [i,j,..])
                    M = geom.GetMatrix(geom.LastParentBeforeRoot(), instance[1:])
                    for pt in coords:
                        ptx = M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3]
                        pty = M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3]
                        ptz = M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3]
                        vt.append( (ptx, pty, ptz) )
            else:
                # no picking ==> no list of instances ==> use [0,0,0,...] 
                g = nodes[0].top.geomContainer.geoms['master']
                M = g.GetMatrix(g.LastParentBeforeRoot())
                for pt in coords:
                    ptx = M[0][0]*pt[0]+M[0][1]*pt[1]+M[0][2]*pt[2]+M[0][3]
                    pty = M[1][0]*pt[0]+M[1][1]*pt[1]+M[1][2]*pt[2]+M[1][3]
                    ptz = M[2][0]*pt[0]+M[2][1]*pt[1]+M[2][2]*pt[2]+M[2][3]
                    vt.append( (ptx, pty, ptz) )
                
        return vt



    
class MolGeomContainer(GeomContainer):
    """
    Class to hold geometries used to represent molecules in a viewer.
    An instance of this class called geomContainer is added to
    each loaded Molecule.
    """
    def __init__(self, mol, app):
        """constructor of the geometry container"""

        GeomContainer.__init__(self, app)
        self.mol = mol
        mol.geomContainer = self

        ## Dictionary of AtomSets used to hold atoms for each geometry in the container
        self.atoms = {}
        ## Dictionary of geoms: {atoms:None} used to find out if an atom has a certain representation
        self.atomGeoms = {}

        ## Dictionary {geometry name: function}. Function is used to expand an atomic
        ## property to the corresponding vertices in a geometry.
        ## The function has to accept 4 arguments: a geometry name,
        ## a list of atoms,  the name of the property and an optional argument--
        ## propIndex (default is None)-- specifying the index of the property
        ## when needed.
        self.atomPropToVertices = {}

        
        ##  Dictionary {geometry name: function}. Function is used to map a vertex to an atom.
        ## If no function is registered, default mapping is used (1vertex to 1atom).
        ## If None is registered -- this geometry cannot represent atoms
        self.geomPickToAtoms = {}

        ## Dictionary {geometry name: function}. Function is used to map vertices to bonds.
        ## If no function is registered, default mapping is used (1vertex to 1bond).
        ## If None is registered: this geometry cannot represent bonds.
        self.geomPickToBonds = {}

        ## this set of coordinates should really be shared by all geometries
        self.allCoords = mol.allAtoms.coords

        # master Geometry
        from DejaVu2.Geom import Geom
        g = self.masterGeom = Geom(mol.name, shape=(0,0), 
                                   pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.geoms['master'] = self.masterGeom
        self.masterGeom.replace = True

        event = AddGeometryEvent(g, parent=None, redo=False)
        self.app.eventHandler.dispatchEvent(event)

        from DejaVu2.Spheres import Spheres

    def displayedAs(self, geomNames, atoms, mode='fast'):
        # mode = 'fast' means return as soon as we find at least 1 atom
        # mode = 'complete' means after checking all atoms
        from time import time
        t0 = time()
        l = len(atoms)
        if mode == 'complete':
            counts = []
            count = 0
            for geomName in geomNames:
                d = self.atomGeoms.get(geomName, None)
                if d is None: continue
                for a in atoms:
                    if d.has_key(a): count +=1
                counts.append(count)
            #print 'DISPLAYED as', geomName, l, counts, time()-t0
            return counts
        
        elif mode == 'fast':
            for geomName in geomNames:
                d = self.atomGeoms.get(geomName, None)
                if d is None: continue
                for a in atoms:
                    if d.has_key(a):
                        #print 'DISPLAYED as', geomName, l, count, count/float(l), time()-t0
                        return 1
            return 0
            
    def setAtomsForGeom(self, geomName, atoms):
        self.atoms[geomName] = atoms
        self.atomGeoms[geomName] = {}.fromkeys(atoms, None)

        
    def addGeom(self, geom, parent=None, redo=False):
        """Add geometry to to geomContainer, create atom set and set pointer
        from geom to molecule"""
        
        GeomContainer.addGeom(self, geom, parent, redo)
        if not self.atoms.has_key(geom.name):
            self.setAtomsForGeom(geom.name, AtomSet([]))
        geom.mol = weakref.ref(self.mol)  #need for backtracking picking


    def getGeomColor(self, geomName):
        """Build a list of colors for a geometry from the atom's colors"""
        if self.atomPropToVertices.has_key(geomName):
            func = self.atomPropToVertices[geomName]
            geom = self.geoms[geomName]
            atms = self.atoms[geomName]
            col = func(geom, atms, 'colors', propIndex=geomName)

        else:
            if geomName in self.atoms.keys():
                col = [x.colors.get(geomName, x.colors['lines']) for x in self.atoms[geomName]]
            else:
                return

        if col is not None:
            colarray = numpy.array(col, 'f')
            diff = colarray - colarray[0]
            maxi = numpy.maximum.reduce(numpy.fabs(diff.ravel()))
            if maxi==0:
                return [colarray[0].tolist()]
            else:
                return col


    def updateColors(self, geomName=[], updateOpacity=0):
        for name in geomName:
            if geomName=='master': continue
            if geomName=='selectionSpheres': continue
            if self.atoms.has_key(name) and len(self.atoms[name])==0: continue 
            col = self.getGeomColor(name)

            if updateOpacity:
                self.geoms[name].Set(materials=col, redo=1,
                                     tagModified=False, transparent='implicit')
                opac = self.getGeomOpacity(name)
            else: opac = None
            
            if col is not None and opac is not None:
                self.geoms[name].Set(materials=col, opacity=opac, redo=1,
                                     tagModified=False, transparent='implicit')
            elif col is not None:
                self.geoms[name].Set(materials=col, redo=1, tagModified=False, transparent='implicit')
            elif opac is not None:
                self.geoms[name].Set(opacity=opac, redo=1, tagModified=False, transparent='implicit')


    def getGeomOpacity(self, geomName):
        if self.atomPropToVertices.has_key(geomName):
            func = self.atomPropToVertices[geomName]
            geom = self.geoms[geomName]
            atms = self.atoms[geomName]
            col = func(geom, atms, 'opacities', propIndex = geomName)
        else:
            if geomName in self.atoms.keys():
                col = [x.opacities[geomName] for x in self.atoms[geomName]]
            else:
                return
        if col is not None:
            colarray = numpy.array(col, 'f')
            diff = colarray - colarray[0]
            maxi = numpy.maximum.reduce(numpy.fabs(diff.ravel()))
            if maxi==0:
                return colarray[0]
            else:
                return col


    def updateOpacity(self, geomName=[]):
        for name in geomName:
            if geomName=='master': continue
            if geomName=='selectionSpheres': continue
            if len(self.atoms[name])==0: continue
            col = self.getGeomColor(name)
            if col:
                col = numpy.array(col, 'f')
                self.geoms[name].Set(materials=col, redo=1, tagModified=False)


from AppFramework.AppCommands import AppCommand

class MVCommand(AppCommand):

    def _strArg(self, arg):
        """
        Method to turn a command argument into a string for logging purposes
        Add support for TreeNodes and TreeNodeSets
        """
        #if type(arg)==types.InstanceType:
        from mglutil.util.misc import isInstance
        if isInstance(arg) is True:
            if issubclass(arg.__class__, TreeNode):
                return '"' + arg.full_name() + '", ', None
                
            if issubclass(arg.__class__, TreeNodeSet):
                stringRepr = arg.getStringRepr()
                if stringRepr:
                    return '"' + stringRepr + '", ', None
                else:
                    name = ""
                    mols, elems = self.app().getNodesByMolecule(arg)
                    for elem in elems:
                        name = name + elem.full_name() +';'
                    return '"' + name + '", ', None

        return AppCommand._strArg(self, arg)
