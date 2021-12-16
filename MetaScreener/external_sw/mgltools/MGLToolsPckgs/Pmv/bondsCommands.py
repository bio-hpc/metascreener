## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER, Sophie COON
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/bondsCommands.py,v 1.61 2011/11/01 23:46:42 annao Exp $
#
# $Id: bondsCommands.py,v 1.61 2011/11/01 23:46:42 annao Exp $
#
#
import numpy.oldnumeric as Numeric
from opengltk.OpenGL import GL

from Pmv.moleculeViewer import EditAtomsEvent
from Pmv.mvCommand import MVCommand, MVAtomICOM, MVBondICOM
from DejaVu.Geom import Geom
from DejaVu.Spheres import Spheres
#from DejaVu.Labels import Labels
from DejaVu.IndexedPolylines import IndexedPolylines
from ViewerFramework.VFCommand import CommandGUI
from MolKit.molecule import Atom, AtomSet, Bond, BondSet
from MolKit.protein import Chain
from types import StringType
var=0
"""
Package: Pmv
Module : bondsCommands
This module provides a set of commands:
- BuildBondsByDistance (buildBondsByDistance) to compute the bonds between
  atoms of the given nodes and connect the residues when necessary.
- AddBondsCommands (addBonds) to create a bond instance between two given atoms.
    -no gui
- AddBondsGUICCommands (addBondsGC) to create a bond between two picked
  atoms. If a group of atoms is selected by dragging, it will
  buildBondsByDistance between them.  
  This is an interactive command (ICOM) and the GUI version of addBonds.
- RemoveBondsCommands (removeBonds) to delete an existing bonds between the
  two given atoms.
    -no gui
- RemoveBondsGUICCommands (removeBondsGC) to delete the picked bond. If a
  groups of atoms is selected by dragging, it will remove all the bonds
  between them. 
  This is the GUI command of the removeBonds and it is an ICOM.

The menubuttons for BondsCommands are located under the 'Bonds' entry in the 'Edit' menu.
"""

class BuildBondsByDistance(MVCommand, MVAtomICOM):
    """This command creates the bonds between atoms of the given set of nodes and connect the residues when necessary. The cut_off distance is based on the bond order radius of the two atoms to be bound. The command will use the bhtree functionality to find the pairs of atoms to be found when available.This command can be applied on a current selection or used interactively when bound to the mouse event.
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : BuildBondsByDistance
   \nCommand : buildBondsByDistance
   \nSynopsis:\n
        None<---buildBondsByDistance( nodes, display = True, **kw)\n
   \nRequired Arguments:\n     
        nodes --- any set for MolKit nodes describing molecular components\n
        display --- when set to 1 the displayLines command is called and th
                 bonds are displayed as lines.\n
   \nOptional Arguments:\n        
        kw --- any of the additional optional keywords supported by commands
               (see ViewerFramework.VFCommands.Command documentation).\n
    \nRequired Commands:\n
      displayLines 
    \nKnown bugs:\n
      None\n
    \nExamples:\n
      mol = mv.Mols[ 0 ]\n
      mv.buildBondsByDistance(mol, display=1)\n
    """

    def __init__(self, func = None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.flag = self.flag | self.objArgOnly
        

    def negateCmdAfter(self, *args, **kw):
        if self.createdBonds:
            return ([(self.vf.removeBonds, (self.createdBonds,), {'topCommand':0})],
                    self.vf.removeBonds.name)
        

    def onAddCmdToViewer(self):
        # this command when called interactively triggers the display of
        # the newly built bonds using lines.
        #if self.vf.hasGui and not self.vf.commands.has_key('displayLines'):
        self.vf.loadCommand('displayCommands', 'displayLines', 'Pmv',
                            topCommand=0)
        # try to import bhtree package and set the command flag hasBhtree
        # to the proper value.
        try:
            import bhtree
            self.hasBhtree = 1
        except:
            self.hasBhtree = 0


    def doit(self, nodes, display=False):
        self.createdBonds = None
        # Get the molecules and the atomSets per molecules in the set of nodes.
        molecules, atomSets = self.vf.getNodesByMolecule(nodes, Atom)
        # Loop over the molecules and the sets of atoms
        bonds = []
        for mol, atm in map(None, molecules, atomSets):
            if self.hasBhtree:
                bond = None
                if len(atm)==len(mol.allAtoms):
                    bond = mol.buildBondsByDistance()
                    
                else:
                    bond = mol.buildBondsByDistanceOnAtoms(atm)
                if bond:
                    bonds.extend(bond)

            else:
                # Need to build the bonds in a chain so loop over the chains.
                for chain in mol.chains:
                    atmInChain = AtomSet(filter(lambda x, name = chain.id:
                                                x.parent.parent.id == name , atm))
                    if not len(atmInChain):
                        continue
                    residues = atmInChain.parent.uniq()
                    residues.sort()
                    bond = residues[0].buildBondsByDistance()
                    if bond:
                        r.extend(bond)
                    for ind in xrange(len(residues)-1):
                        res1 = residues[ind]
                        res2 = residues[ind+1]
                        res2.buildBondsByDistance()
                        chain.connectResidues(res1, res2)
                        
        if display:
            # when we call it from the GUI we want the result to be displayed
            self.vf.displayLines(nodes, topCommand=0, setupNegate=0)
        self.createdBonds = bonds
        return bonds


    def __call__(self, nodes, display=False, **kw):
        """None <- buildBondsByDistance(nodes, display=1,**kw)
        \nnodes   : TreeNodeSet holding the current selection
        \ndisplay : Boolean flag if set to True the displayLines 
                  commands are called.
        \nThe buildBondsByDistance commands connects atoms and residues in the
        given set of nodes based on the covalent radius of each atoms to be
        connected.
        """
        if not kw.has_key('redraw'):
            kw['redraw']=1
        kw['display']=display
        if type(nodes) is StringType:
            self.nodeLogString = "'"+nodes+"'"

        return self.doitWrapper( nodes, **kw)

        
    def guiCallback(self, event=None):
        """Default callback function called by the gui"""
        if self.vf.userpref['Expand Node Log String']['value'] == 0:
            self.nodeLogString = "self.getSelection()"
        self.doitWrapper( self.vf.getSelection(), display = 1, redraw=0)
        

from Pmv.bondsCommandsGUI import BuildBondsByDistanceGUI


class AddBondsGUICommand(MVCommand, MVAtomICOM):
    """
    The AddBondGUICommand provides an interactive way of creating bonds between two given atoms by picking on them. To use this command you need first to load it into PMV. Then you can find the entry 'addBonds' under the Edit menu. To add bonds  you just need to pick on the 2 atoms you want to bind. If you drag select  a bunch of atoms, the command will buildBondsByDistance between them.This command is undoable.
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : AddBondsGUICommand
   \nCommand : addBondsGC
   \nSynopsis:\n
        None<-addBondsGC(atoms)\n
    \nRequired Arguments:\n    
        atoms  : atom(s)\n
    """
    
    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        MVAtomICOM.__init__(self)
        self.atomList = AtomSet([])
        self.labelStrs = []
        self.createdBonds = [] # this list will store created bonds used to create
                               # negation of command

            
    def onRemoveObjectFromViewer(self, obj):
        removeAts = AtomSet([])
        for at in self.atomList:
            if at in obj.allAtoms:
                removeAts.append(at)
        self.atomList = self.atomList - removeAts
        removeAts = AtomSet([])
        self.update()

       
    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('setICOM'):
            self.vf.loadCommand('interactiveCommands', 'setICOM', 'Pmv',
                                topCommand=0) 
        if not self.vf.commands.has_key('addBonds'):
            self.vf.loadCommand('bondsCommands', 'addBonds', 'Pmv',
                                topCommand=0) 
        if not self.vf.commands.has_key('removeBondsGC'):
            self.vf.loadCommand('bondsCommands', 'removeBondsGC', 'Pmv',
                                topCommand=0) 
        self.masterGeom = Geom('addBondsGeom',shape=(0,0), 
                               pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.spheres = Spheres(name='addBondsSpheres', shape=(0,3),
                               inheritMaterial=0,
                               radii=0.2, quality=15,
                               materials = ((1.,1.,0.),), protected=True) 
        if not self.vf.commands.has_key('labelByExpression'):
            self.vf.loadCommand('labelCommands', 
                                ['labelByExpression',], 'Pmv', topCommand=0)
        if self.vf.hasGui:
            miscGeom = self.vf.GUI.miscGeom
            self.vf.GUI.VIEWER.AddObject(self.masterGeom, parent=miscGeom)
            self.vf.GUI.VIEWER.AddObject(self.spheres, parent=self.masterGeom)


    def __call__(self, atoms, **kw):
        """None<-addBondsGC(atoms)
           \natoms  : atom(s)"""
        if type(atoms) is StringType:
            self.nodeLogString = "'"+atoms+"'"
        ats = self.vf.expandNodes(atoms)
        if not len(ats): return 'ERROR'
        return apply(self.doitWrapper, (ats,), kw)


    def doit(self, ats):
        if len(ats)>2:
            if len(self.atomList):
                atSet = ats + self.atomList
            else: atSet = ats
            parent = atSet[0].parent
            #parent.buildBondsByDistanceOnAtoms(atSet)
            self.vf.buildBondsByDistance(atSet, topCommand=0)
            self.update(True)
            self.atomList = AtomSet([])
            self.vf.displayLines(atSet, topCommand=0, setupNegate=0)
        else:
            lenAts = len(self.atomList)
            last = None
            if lenAts:
                last = self.atomList[-1]
                top = self.atomList[0].top
            for at in ats:
                #check for repeats of same atom
                if lenAts and at==last:
                    continue
                #lenAts = len(self.atomList)
                #if lenAts and at==self.atomList[-1]:
                #    continue
                if lenAts and at.top!=self.atomList[-1].top:
                    msg = "intermolecular bond to %s disallowed"%(at.full_name())
                    self.warningMsg(msg)
                self.atomList.append(at)
                lenAts = len(self.atomList)
            self.update(True)
            #if only have one atom, there is nothing else to do
            if lenAts<2: return
            #now build bonds between pairs of atoms
            atSet = self.atomList
            if lenAts%2!=0:
                atSet = atSet[:-1]
                #all pairs of atoms will be bonded
                #so keep only the last one
                self.atomList = atSet[-1:]
                lenAts = lenAts -1
            else:
                self.vf.labelByExpression(self.atomList, negate=1, topCommand=0, setupNegate=0)
                self.atomList = AtomSet([])
            for i in range(0, lenAts, 2):
                at1 = atSet[i]
                at2 = atSet[i+1]
                self.vf.addBonds( [(at1, at2)], bondOrder=[1], origin='UserDefined',log=0, topCommand=0)
        self.update(True)


    def applyTransformation(self, pt, mat):
        pth = [pt[0], pt[1], pt[2], 1.0]
        return Numeric.dot(mat, pth)[:3]


    def getTransformedCoords(self, atom):
        if not atom.top.geomContainer:
            return atom.coords
        g = atom.top.geomContainer.geoms['master']
        c = self.applyTransformation(atom.coords, g.GetMatrix(g))
        return  c.astype('f')


    def update(self, event=None):
        if not len(self.atomList):
            self.spheres.Set(vertices=[], tagModified=False)
            self.vf.labelByExpression(self.atomList, negate=1, topCommand=0, setupNegate=False)
            if self.vf.hasGui:
                self.vf.GUI.VIEWER.Redraw()
            return
        self.lineVertices=[]
        #each time have to recalculate lineVertices
        for at in self.atomList:
            c1 = self.getTransformedCoords(at)
            self.lineVertices.append(tuple(c1))
            
        if event:
            self.spheres.Set(vertices=self.lineVertices, tagModified=False)
            self.vf.labelByExpression(self.atomList,
                                      function = 'lambda x: x.full_name()',
                                      lambdaFunc = 1,
                                      textcolor = 'yellow',
                                      format = '', negate = 0,
                                      location = 'Last', log = 0,
                                      font = 'arial1.glf', only = 1,
                                      topCommand=0,setupNegate=False )
        #setting spheres doesn't trigger redraw so do it explicitly
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.Redraw()


    def guiCallback(self, event=None):
        self.save = self.vf.ICmdCaller.commands.value["Shift_L"]
        self.vf.setICOM(self, modifier="Shift_L", topCommand=0, setupNegate=False)

        
    def startICOM(self):
        self.vf.setIcomLevel( Atom, topCommand=0)

    def stopICOM(self):
        if len(self.atomList)!=0:
            self.vf.labelByExpression(self.atomList, negate=1, topCommand = 0,setupNegate=False )
        del self.atomList[:]
        self.labelStrs = []
        self.spheres.Set(vertices=[], tagModified=False)
        self.vf.GUI.VIEWER.Redraw()
        self.save = None


from Pmv.bondsCommandsGUI import AddBondsGUICommandGUI

class AddBondsCommand(MVCommand):
    """
    The AddBondsCommand is a command to connect two given atoms.This command will not allow the creation inter-molecular bonds.This command doesn't have a GUI interface and can only be called through the pyShell.
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : AddBondsCommand
   \nCommand : addBonds
   \nSynopsis:\n
        None<-addBonds(atom1,atom2)\n
   \nRequired Arguments:\n    
     atom1  : first atom\n
     atom2  : second atom \n
   \nOptional Arguments:\n  
     bondOrder : Integer specifying the bondOrder of the bond that is going to be created between atom1 and atom2.The bondOrder by default is 1.\n
     origin  : string describing how bond was specified \n 
    """

    def onAddCmdToViewer(self):
        if not self.vf.commands.has_key('removeBonds'):
            self.vf.loadCommand('bondsCommands', 'removeBonds', 'Pmv',
                                topCommand=0) 


    def negateCmdAfter(self, *args, **kw):
        if self.createdBonds:
            return ([(self.vf.removeBonds, (self.createdBonds,), {'topCommand':0})],
                    self.vf.removeBonds.name)
        

    def __call__(self, bondAtomPairs, bondOrder=None, origin='UserDefined', **kw):
        """None<-addBonds(bondAtomPairs)
           \nbondAtomPairs  : list of pair of atoms forming bonds
           \nbondOrder : list of integer specifying the bondOrder of the bonds that is going to be created between. The bondOrder by default is 1.
           \norigin  : string describing how bond was specified"""

        if bondOrder is None:
            bondOrder = [1]*len(bondAtomPairs)
        else:
            assert len(bondOrder)==len(bondAtomPairs)

        return self.doitWrapper( bondAtomPairs, bondOrder, origin, **kw)


    def doit(self, bondAtomPairs, bondOrder, origin, **kw):
        bonds = self.createdBonds = []
        for atoms, bo in zip(bondAtomPairs, bondOrder):
            ats = self.vf.expandNodes(atoms[0])
            if not len(ats): return 'ERROR'
            atom1 = ats[0]
            ats = self.vf.expandNodes(atoms[1])
            if not len(ats): return 'ERROR'
            atom2 = ats[0]
            # check for inter molecular bonds
            if atom1.top!=atom2.top:
               msg = "intermolecular bond between %s and %s \
                      disallowed"%(atom1.full_name(), atom2.full_name())
               self.warningMsg(msg)

            # do not duplicate existing bonds
            bnds = AtomSet([atom1, atom2]).bonds[0]
            if len(bnds): 
               msg = "bond between %s and %s already \
                      exists"%(atom1.full_name(), atom2.full_name())

            bonds.append( Bond( atom1, atom2, origin=origin, bondOrder=bo) )

            event = EditAtomsEvent('coords', AtomSet([atom1, atom2]))
            self.vf.dispatchEvent(event)
        return bonds
    

class RemoveBondsGUICommand(MVCommand, MVBondICOM):
    """ The RemoveBondsGUICommands provides an interactive way of deleting picked bonds. To use this command you need to first load it in the application. Once loaded you will find an entry called 'delete bonds' under the bonds entry in the Edit menu. You can then pick on the bonds you wish to delete. This command is undoable.
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : RemoveBondsGUICommand
   \nCommand : removeBondsGC
   \nSynopsis:\n
        None<---removeBondsGC(bonds)\n
   \nRequired Arguments:\n    
        bonds  : bond(s)\n
    """

    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'addBondsGC'):
            self.vf.loadCommand("bondsCommands", "addBondsGC", "Pmv")

        if not self.vf.commands.has_key('removeBonds'):
            self.vf.loadCommand('bondsCommands', 'removeBonds', 'Pmv',
                                topCommand=0) 


    def __init__(self, func = None):
        MVCommand.__init__(self, func)
        MVBondICOM.__init__(self)
        self.pickLevel = 'parts'
        self.undoBondList = []


    def guiCallback(self):
        self.save = self.vf.ICmdCaller.commands.value["Shift_L"]
        self.vf.setICOM(self, modifier="Shift_L", topCommand=0, setupNegate=False)
        self.vf.setIcomLevel( Atom )


    def stop(self):
        self.done_cb()


    def getObjects(self, pick):
        for o, val in pick.hits.items(): #loop over geometries
            primInd = map(lambda x: x[0], val)
            g = o.mol.geomContainer
            if g.geomPickToBonds.has_key(o.name):
                func = g.geomPickToBonds[o.name]
                if func: return func(o, primInd)
            else:
                l = []
                bonds = g.atoms[o.name].bonds[0]
                if not len(bonds): return BondSet()
                for i in range(len(primInd)):
                    l.append(bonds[int(primInd[i])])
                return BondSet(l)


    def dismiss(self):
        self.vf.setICOM(self.save, modifier="Shift_L", topCommand=0, setupNegate=False)
        self.save = None
        self.done_cb()


    def done_cb(self):
        pass

    
    def __call__(self, bonds, **kw):
        """None <- removeBondsGC(bonds, **kw)
           \nbonds: bonds
           """
        kw['log'] = 0
        if not len(bonds):
            return 'ERROR'
        apply(self.doitWrapper, (bonds,), kw)



    def doit(self, bonds):
        global var
        var=1 
        ats = AtomSet([])
        for bond in bonds:
            ats.append(bond.atom1)
            ats.append(bond.atom2)
            self.vf.removeBonds( [bond] )
        var=0
        if self.vf.hasGui:
            self.vf.GUI.VIEWER.Redraw()
        

    def negateCmdBefore(self, bonds):
        cmds =([], self.vf.addBondsGC.name)
        for b in bonds:
            nameStr = AtomSet([b.atom1, b.atom2]).full_name()
            cmds[0].append((self.vf.addBondsGC, (nameStr,),{}) )
        return cmds

    

from Pmv.bondsCommandsGUI import RemoveBondsGUICommandGUI


class RemoveBondsCommand(MVCommand):
    """ 
    The RemoveBondsCommand allows the user to remove the bond existing between two given atoms (atom1 and atom2). This command doesn't have a gui and therefore can only be called through the pyShell.
   \nPackage : Pmv
   \nModule  : bondsCommands
   \nClass   : RemoveBondsCommand
   \nCommand : removeBonds
   \nSynopsis:\n
        None<---removeBonds(bondList)\n
    \nRequired Arguments:\n    
        bondList  : list of bonds to remove\n
    """

    def onAddCmdToViewer(self):
        if not hasattr(self.vf, 'addBonds'):
            self.vf.loadCommand("bondsCommands", "addBonds", "Pmv")


    def negateCmdBefore(self, bondList):
        # The undo is to recreate the bond you just deleted.when
        # removebondsCommand called
        bondAtomPairs = []
        for bond in bondList:
            bondAtomPairs.append( (bond.atom1, bond.atom2) )
            
        return ( [(self.vf.addBonds, (bondAtomPairs,), {})], self.vf.addBonds.name)


    def __call__(self, bondList, **kw):
        """None<-removeBonds(bondList)
        
           \nabondList  : list of bonds to remove"""
        #ats = self.vf.expandNodes(atom1)
        #if not len(ats): return 'ERROR'
        #at1 = ats[0]
        #ats = self.vf.expandNodes(atom2)
        #if not len(ats): return 'ERROR'
        #at2 = ats[0]
        self.doitWrapper( bondList, **kw)
        

    def doit(self, bondList):
        #Have to find the bond first
        
        for theBond in bondList:
            atom1 = theBond.atom1
            atom2 = theBond.atom2
            #remove this bond
            atom2.bonds.remove(theBond)
            #this may not be possible
            atom1.bonds.remove(theBond)
##             atom1.parent.hasBonds=0
##             if atom2.parent!=atom1.parent:
##                 atom2.parent.hasBonds = 0
##                 if atom1.parent.parent:
##                     atom1.parent.parent.hasBonds = 0
##                 if atom2.parent.parent:
##                     atom2.parent.parent.hasBonds = 0
##                 break

##         if not theBond:
##             from warnings import warn
##             warn('bond not found %s-%s'%(atom1, atom2))
##             return 'ERROR'
##         else:
        event = EditAtomsEvent('coords', AtomSet([atom1, atom2]))
        self.vf.dispatchEvent(event)


commandList = [
    {'name':'buildBondsByDistance', 'cmd':BuildBondsByDistance(),
     'gui':BuildBondsByDistanceGUI},
    {'name':'addBonds', 'cmd':AddBondsCommand(), 'gui':None},
    {'name':'addBondsGC','cmd':AddBondsGUICommand(),
     'gui':AddBondsGUICommandGUI},
    {'name':'removeBonds', 'cmd':RemoveBondsCommand(), 'gui':None}, # ackward compat
    {'name':'removeBondsGC','cmd':RemoveBondsGUICommand(),
     'gui':RemoveBondsGUICommandGUI}
    
    ]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])

