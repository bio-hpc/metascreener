#############################################################################
#
# Author: Michel F. SANNER, Anna Omelchenko
#
# Copyright: M. Sanner TSRI 2013
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/displayCmds.py,v 1.14 2014/08/22 22:56:06 annao Exp $
#
# $Id: displayCmds.py,v 1.14 2014/08/22 22:56:06 annao Exp $
#

import numpy, sys

from PmvApp.Pmv import MVCommand, formatName#MVAtomICOM
from PmvApp.Pmv import DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent,\
     ShowMoleculesEvent, DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent

from DejaVu2.Geom import Geom
from DejaVu2.Cylinders import Cylinders
from DejaVu2.IndexedPolylines import IndexedPolylines
from DejaVu2.IndexedGeom import IndexedGeom
from DejaVu2.Spheres import Spheres
from DejaVu2.Points import Points, CrossSet

from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet, BondSet
from MolKit.protein import Protein, Residue, Chain

class DisplayCommand(MVCommand): #, MVAtomICOM):
    """The DisplayCommand class is the base class from which all the display commands implemented for PMV will derive.It implements the general functionalities to display/undisplay parts of a geometry representing a molecule.
    \nPackage : PmvApp
    \nModule  : displayCmds
    \nClass   : DisplayCommand
    """

    def __init__(self):
        MVCommand.__init__(self)
        #MVAtomICOM.__init__(self)
        #self.flag = self.flag | self.objArgOnly
        #self.flag = self.flag | self.negateKw
    
    def onAddCmdToApp(self):
        self.app().eventHandler.registerListener(DeleteAtomsEvent, self.updateGeom)
        self.app().eventHandler.registerListener(AddAtomsEvent, self.updateGeom)
        self.app().eventHandler.registerListener(EditAtomsEvent, self.updateGeom)

    def updateGeom(self, event):
        """Function to update geometry objects created by this command
upon Modification events.  This function is called by the
the AppFramework.dispatchEvent command.
The function will compute  a set of atoms by combining
the atoms currently used to display the geometry (i.e.
adding or substracting event.objects for action =='add' or
'delete', then execute this command for the set of
atoms.
\nevent --- instance of an Event object
"""
        if isinstance(event, AddAtomsEvent):
            action='add'
        elif isinstance(event, DeleteAtomsEvent):
            action='delete'
        elif isinstance(event, EditAtomsEvent):
            action='edit'
        else:
            import warnings
            warnings.warn('Bad event %s for DisplayCommand.updateGeom'%event)
            return
        
        geomList = self.managedGeometries

        # split event.objects into atoms sets per molecule
        molecules, ats = self.app().getNodesByMolecule(event.objects)

        # build list of optional command arguments
        doitoptions = self.lastUsedValues['default']
        doitoptions['redraw']=1
        doitoptions['setupUndo']=False
        # allAts is the set of atoms for which we will invoke this command
        allAts = AtomSet([])

        # loop over molecules to update geometry objects
        for mol, atomSets in zip(molecules, ats):

            # loop over the geometry objects
            for geom in geomList:
                # get the list of atoms currently displayed with this geom
                atoms = mol.geomContainer.atoms[geom.name]
                if len(atoms)==0:
                    continue
                # handle event.action
                if action=='delete':
                    changed = atoms.inter(atomSets)
                    doitoptions['negate'] = 1
                    if len(changed):
                        #apply(self.doitWrapper,(changed,), doitoptions)
                        self(changed, **doitoptions)
                    doitoptions['negate'] = 0
                else:
                    if action == 'add':
                        allAts = allAts + atoms + atomSets
                    elif action == 'edit':
                        if len(allAts)==0:
                            allAts = atoms
                        else:
                            allAts = allAts.union(atoms)

        ## if there are atoms to be displayed in geoemtries created by this
        ## command, invoke the command
        if len(allAts):
            #apply(self.doitWrapper,(allAts,), doitoptions)
            self(allAts, **doitoptions)

    def cleanupUndoArgs(self):
        # remove the atoms from the nodes in the undoCommand for molecules for which
        # the command failed
        if self.undoCmds is None: return
        report = self.app()._executionReport
        sig, name = self.undoCmds
        func, args, kw = sig[0]
        nodes = args[0]
        for error in report.getErrors() + report.getExceptions():
            nodes = nodes - error.obj.findType(nodes[0].__class__)
        self.undoCmds = ( [ (func, (nodes,), kw) ], name )
            
    def getLastUsedValues(self, formName='default', **kw):
        """Return dictionary of last used values
"""
        return self.lastUsedValues[formName].copy() 



class DisplayLines(DisplayCommand):
    """The displayLines allows the user to display/undisplay the selected nodes using a lines for bonded atoms, dots for non bonded atoms and doted lines for an aromatic ring. The number of lines when representing a bond will vary depending on the bondOrder.
    \nPackage : PmvApp
    \nModule  : displayCmds
    \nClass   : DisplayLines
    \nCommand : displayLines
    \nSynopsis:\n
    None <--- displayLines(self, nodes, lineWidth=2, displayBO = 1, only = 0,
                         negate = 0)\n
    \nRequired Arguments:\n
    nodes --- any set of MolKit nodes describing molecular components\n

    \nOptional Arguments:\n
    lineWidth --- int specifying the width of the lines, dots or doted lines
                 representing the selection. (default = 2)\n
    displayBO --- boolean flag specifying whether or not to display the
                 bond order (default = False)\n
    only   --- boolean flag specifying whether or not to display only the
                 current selection. (default = False)\n
    negate --- boolean flag  specifying whether or not to negate the current
                 selection. (default = False)\n
                 

    keywords: display wireframe, lines, bond order, non bonded atoms.
    """
    

    def onAddCmdToApp(self):
        DisplayCommand.onAddCmdToApp(self)
        if not self.app().commands.has_key('buildBondsByDistance'):
            self.app().lazyLoad('bondsCmds', commands=['buildBondsByDistance'], package='PmvApp')

    def onAddObjectToViewer(self, obj):
        """
        Creates the lines, the points , the dotted lines and the bond order
        lines geometries and add these new geometries to the
        geomContainer.geoms of the new molecule.
        New AtomSet are created as well and added to the geomContainer.atoms
        """
        self.objectState[obj] = {'onAddObjectCalled':True}
        if self.app().commands.has_key('dashboard'):
            self.app().dashboard.resetColPercent(obj, '_showLinesStatus')
        geomC = obj.geomContainer
        # lines representation needs 4 different geometries need to create
        # a master geometrie Geom.
        #wire = geomC.geoms['lines'] = Geom('lines',  shape=(0,0))
        if not geomC.geoms.has_key('lines'):
            wire = Geom('lines',
                        shape=(0,0),
                        inheritLighting=False,
                        lighting=False,
                        protected=True)
            
        else:
            wire = geomC.geoms['lines']
        geomC.addGeom(wire, parent=geomC.masterGeom, redo=0 )    

        geomC.atomPropToVertices["bonded"] = self.atomPropToVertices
        geomC.atomPropToVertices["nobnds"] = self.atomPropToVertices
        geomC.atomPropToVertices["bondorder"] = self.atomPropToVertices

        # lines: Bonded atoms are represented by IndexedPolyLines
        l = IndexedPolylines("bonded", 
                             vertices=geomC.allCoords, 
                             visible=0,
                             pickableVertices=1,
                             inheritMaterial=1,
                             protected=True,
                             disableStencil=True,
                             transparent=True
                             )
        geomC.addGeom(l, parent=wire, redo=0)
        self.managedGeometries.append(l)
               
        # nobnds : Non Bonded atoms are represented by Points
        p = Points( "nobnds", shape=(0,3), visible=0,
                    inheritMaterial=1, protected=True,
                    disableStencil=True,
                    transparent=True
                    )
        
        geomC.addGeom( p, parent=wire, redo=0)
        self.managedGeometries.append(p)
        b = IndexedPolylines('bondorder', visible=0,
                             inheritMaterial=1, protected=True,
                             disableStencil=True,
                             transparent=True
                             )
        
        geomC.addGeom( b, parent=wire, redo=0 )
        self.managedGeometries.append(b)
        
        # Create the entry 'lines' and 'nobnds' in the atom.colors dictionary
        for atm in obj.allAtoms:
            atm.colors['lines'] = (1.0, 1.0, 1.0)



    def atomPropToVertices(self, geom, atms, propName, propIndex=None):
        """Function called to compute the array of properties"""
        if atms is None or len(atms)==0 : return None
        prop = []
        if propIndex == 'bondorder':
            mol = geom.mol()
            atms = mol.geomContainer.atoms['bondorder']

        propIndex = 'lines'
        for a in atms:
            d = getattr(a, propName)
            prop.append( d[propIndex] )
        return prop


    def undoCmdBefore(self, nodes, only=False, negate=False, displayBO=False,
                        lineWidth=2, redraw=True):
        #print "undoCmdBefore", self.name, "negate:", negate, "kw", kw
        #kw['displayBO'] = displayBO
        kw = {}
        kw['lineWidth'] = self.lastUsedValues['default']['lineWidth']
        kw['redraw'] = redraw
        geomSet = []
        boSet = []
        for mol in self.app().Mols:
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            geomSet = geomSet + mol.geomContainer.atoms['bonded']
            boSet = boSet + mol.geomContainer.atoms['bondorder'].uniq()
        if len(boSet) == 0:
            kw['displayBO']=False
        else:
            kw['displayBO']=True
        if len(geomSet) == 0:
            # The undo of a display command is undisplay what you just
            # displayed if nothing was displayed before.
            kw['negate'] = True
            kw['displayBO'] = False
            return ([(self, (nodes,), kw)], self.name)
        else:
            # The undo of a display command is to display ONLY what was
            # displayed before, if something was already displayed
            kw['only'] = True
            return ([(self, (geomSet,), kw)], self.name)
        
    def checkArguments(self, nodes, lineWidth=2, displayBO=False,
                       only=False, negate=False, redraw=True):
        """
        \nRequired Arguments:\n
        nodes --- any set of MolKit nodes describing molecular components\n

        \nOptional Arguments:\n
        lineWidth --- int specifying the width of the lines, dots or doted lines
                     representing the selection. (default = 2)\n
        displayBO --- boolean flag specifying whether or not to display the
                     bond order (default = False)\n
        only --- boolean flag specifying whether or not to display only
                     the current selection. (default = False)\n
        negate --- boolean flag specifying whether or not to negate the
                     current selection. (default = False)\n
        """
        kw = {}
        assert isinstance(lineWidth, (int, float))
        assert lineWidth>0
        assert displayBO in [True, False, 0, 1]
        assert only in [True, False, 0, 1]
        assert negate in [True, False, 0, 1]        
        kw['lineWidth'] = lineWidth
        kw['displayBO'] = displayBO
        kw['only'] = only
        kw['negate'] = negate
        kw['redraw'] = redraw
        if isinstance(nodes, str):
            self.nodeLogString = "'" + nodes +"'"
        oldNodes = nodes
        nodes = self.app().expandNodes(nodes)

        return (nodes,), kw

        
    def doit(self, nodes, lineWidth=2, displayBO=False , only=False,
             negate=False, redraw=True):
        
        #print 'DISPLAY LINES'
        ###################################################################
        def drawAtoms(mol, atm, displayBO, lineWidth, only, negate):
            """ Function to represent the given atoms as lines if they are
            bonded and points otherwise"""
            gc = mol.geomContainer
            ggeoms = gc.geoms
            # DISPLAY BONDED ATOMS AND NOBNDS ATOMS

            # special case all atoms in the molecule for efficiency
            if len(atm) == len(mol.allAtoms): #atm is all atoms in mol
                if negate:
                    _set = AtomSet() # evrythign gets undisplayed
                    setOff = atm
                    setOn = None
                else:
                    _set = atm
                    setOff = None
                    setOn = atm

            else: # atm is a subset of mol's atoms
                _set = gc.atoms['bonded']
                setnobnds = gc.atoms['nobnds']
                if negate: #if negate, remove current atms from displayed _set
                    setOff = atm
                    setOn = None
                    _set = _set - atm

                else:     #if only, replace displayed _set with current atms 
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            # Update geoms lines and nobnds with new information.
            # If no lines then donnot display bondorder.
            if len(_set)==0:
                ggeoms['bonded'].Set(faces=[], vertices=[], tagModified=False)
                gc.setAtomsForGeom('bonded', _set)
                ggeoms['nobnds'].Set(vertices=[], tagModified=False)
                gc.setAtomsForGeom('nobnds', _set)
                return setOn, setOff
            # This is done only if _set contains some atoms.
            bonds, atnobnd = _set.bonds

            # 1st lines need to store the whole _set in the
            # mol.geomContainer.atoms['lines'] because of the picking.
            gc.setAtomsForGeom('bonded', _set)

            if len(bonds) == 0:
                ggeoms['bonded'].Set(faces=[], vertices=[], tagModified=False)
            else:
                # need the indices for the indexedPolylines
                indices = [ (x.atom1._bndIndex_, x.atom2._bndIndex_) for x in bonds]
                if len(indices)==0:
                    ggeoms['bonded'].Set(visible=0, tagModified=False)
                else:
                    colors = [x.colors['lines'] for x in _set]
                    ggeoms['bonded'].Set( vertices=_set.coords,
                                          faces=indices,
                                          materials = colors,
                                          lineWidth=lineWidth,
                                          inheritLineWidth=False,
                                          visible=1,
                                          tagModified=False,
                                          inheritMaterial=False)
            # the nobnds
            gc.setAtomsForGeom('nobnds', atnobnd)
            if len(atnobnd)==0:
                ggeoms['nobnds'].Set(vertices=[], tagModified=False)
            else:
                vertices = atnobnd.coords
                colors = [x.colors['lines'] for x in atnobnd]
                ggeoms['nobnds'].Set(vertices=vertices,
                                     pointWidth=lineWidth,
                                     materials = colors,
                                     visible=1, inheritMaterial=False, 
                                     tagModified=False)
                
            #DISPLAY BOND ORDER.
            if not displayBO:
                setBo = AtomSet()

            else:
                if len(atm) == len(mol.allAtoms):
                    if negate:
                        setBo = AtomSet()
                    else:
                        setBo = atm

                else:
                    setBo = gc.atoms['bondorder'].uniq()
                    if negate:
                        # if negate, remove current atms from displayed set
                        setBo = mol.allAtoms - atm
                    else:
                        # if only, replace displayed set with
                        # current atms 
                        if only:
                            setBo = atm
                        else: 
                            setBo = mol.allAtoms
            
            if len(setBo) == 0:
                ggeoms['bondorder'].Set(vertices=[], tagModified=False)
                gc.setAtomsForGeom('bondorder', setBo)
                return setOn, setOff
            
            bonds = setBo.bonds[0]

            # Get only the bonds with a bondOrder greater than 1
            bondsBO = [x for x in bonds if (not x.bondOrder is None and x.bondOrder>1)]
            
            if not bondsBO: return setOn, setOff
            withVec = [x for x in bondsBO if (not hasattr( x.atom1, 'dispVec') \
                             and not hasattr(x.atom2, 'dispVec')) ]

            if len(withVec):
                [x.computeDispVectors() for x in bondsBO]

            vertices = []
            indices = []
            col = []
            i = 0
            realSet  = AtomSet([])
            ar = numpy.array
            for b in bonds:
                bondOrder = b.bondOrder
                if bondOrder == 'aromatic' : bondOrder = 2
                if not bondOrder > 1: continue

                at1 = b.atom1
                at2 = b.atom2
                if (not hasattr(at1, 'dispVec') \
                    and not hasattr(at2, 'dispVec')):
                    continue
                realSet.append(at1)
                realSet.append(at2)

                nc1 = ar(at1.coords) + \
                      ar(at1.dispVec)
                nc2 = ar(at2.coords) + \
                      ar(at2.dispVec)
                vertices.append(list(nc1))
                vertices.append(list(nc2))
                indices.append( (i, i+1) )
                i = i+2
            gc.setAtomsForGeom('bondorder', realSet)
            #col = mol.geomContainer.getGeomColor('bondorder')
            ggeoms['bondorder'].Set( vertices=vertices, 
                                     faces=indices,
                                     visible=1,
                                     lineWidth=lineWidth,
                                     tagModified=False)
            return setOn, setOff
        
        ##################################################################
        molecules, atomSets = self.app().getNodesByMolecule(nodes, Atom)
        setOn = AtomSet([])
        setOff = AtomSet([])
        for mol, atms, in map(None, molecules, atomSets):
            try:
                if not self.objectState.has_key(mol):
                    self.onAddObjectToViewer(mol)
                # Get the set of atoms currently represented as wireframe
                geomC = mol.geomContainer
                if self._failForTesting:
                    a = 1/0.
                son, sof = drawAtoms(mol, atms, displayBO, lineWidth, only, negate)
                if son: setOn += son
                if sof: setOff += sof
                self.app()._executionReport.addSuccess('displayed lines for molecule %s successfully'%
                    mol.name, obj=atms)
            except:
                msg = 'Error while displaying lines for molecule %s'%mol.name
                self.app().errorMsg(sys.exc_info(), msg, obj=atms)

        if only and len(molecules) != len(self.app().Mols):
            # if only is True we need to undisplay lines for molecules
            # that are not included in nodes
            mols = self.app().Mols - molecules
            for mol in mols:
                try:
                    only=0
                    negate=1
                    drawAtoms(mol, mol.allAtoms, displayBO, lineWidth, only,
                              negate)
                except:
                    msg = 'Error while undisplaying lines for molecule %s to enforce only=True option'%mol.name
                    self.app().errorMsg(sys.exc_info(), msg, obj=mol)

        if self.createEvents:
            if len(setOn) or len(setOff):
                event = EditGeomsEvent(
                    'lines', [nodes,[lineWidth, only, negate,redraw]],
                    setOn=setOn, setOff=setOff)
                self.app().eventHandler.dispatchEvent(event)


    def getLastUsedValues(self, formName='default', **kw):
        """Return dictionary of last used values
"""
        values = self.lastUsedValues[formName].copy()
        return self.handleDisplayValue(values)
    

    def handleDisplayValue(self, val):
        # creates the only and negate keywords based on the 'display' entry
        if val.has_key('display'):
            if val['display']=='display':
                val['only']= False
                val['negate'] = False
                del val['display']
            elif val['display']=='display only':
                val['only']= True
                val['negate'] = False
                del val['display']
            elif val['display']== 'undisplay':
                val['negate'] = True
                val['only'] = False
                del val['display']
            val['redraw'] = True
        return val


    def onRemoveObjectFromViewer(self, mol):
       """Function to remove the sets able to reference a TreeNode created
       in this command : Here remove bbDisconnectedAfter created for each
       chains  and bonds created for each elements of each level in
       buildBondsByDistance."""
       if self.objectState.has_key(mol):
            self.objectState.pop(mol)
       try: # _undoable delete 
           levels = mol.levels
       except:
           return
       for l in levels:
           try:
               levelNodes = mol.findType(l)
               for n in levelNodes:
                   if hasattr(n, 'bbDisconnectedAfter'):
                       del n.bbDisconnectedAfter
                   if hasattr(n, 'bonds'):
                       del n.bonds
           except:
               msg= "exception in DisplayLines.onRemoveObjectFromViewer for molecule %s"% mol.name
               self.app().errorMsg(sys.exc_info(), msg, obj=mol)
       del levelNodes



class UndisplayLines(DisplayCommand):
    """The undisplayLines command is a picking command allowing the user to undisplay the lines geometry representing the picked nodes.This command can also be called from the Python shell with a set of nodes.
    \nPackage : PmvApp
    \nModule  : displayCmds
    \nClass   : UnDisplayLines
    \nCommand : undisplayLines
    \nSynopsis:\n
        None <- undisplayLines(nodes, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        keywords --- undisplay, lines\n
    """

    def onAddCmdToApp(self):
        DisplayCommand.onAddCmdToApp(self)
        if not self.app().commands.has_key('displayLines'):
            self.app().lazyLoad('displayCmds', commands=['displayLines'], package='PmvApp')

    def checkArguments(self, nodes, **kw):
        """None <- undisplayLines(nodes, **kw)
           nodes: TreeNodeSet holding the current selection"""

        kw['negate']=1
        return self.app().displayLines.checkArguments(nodes, **kw)


    def doit(self, nodes, **kw):
        return self.app().displayLines(nodes, **kw)
    


class DisplayCPK(DisplayCommand):
    """ The displayCPK command allows the user to display/undisplay the given nodes using a CPK representation, where each atom is represented with a sphere. A scale factor and the quality of the spheres are user
    defined parameters.
    \nPackage : PmvApp
    \nModule  : displayCommands
    \nClass   : DisplayCPK
    \nCommand : displayCPK
    \nSynopsis:\n
        None <- displayCPK(nodes, only=False, negate=False, 
                           scaleFactor=None, quality=None)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        only --- Boolean flag specifying whether or not to only display
                     the current selection\n
        negate --- Boolean flag specifying whether or not to undisplay
                     the current selection\n
        scaleFactor --- specifies a scale factor that will be applied to the atom
                     radii to compute the spheres radii. (default is 1.0)\n
        quality  --- specifies the quality of the spheres. (default 10)\n
        cpkRad  --- offset , used to comute spheres radii
        propertyName --- if specified,  the property is used to compute the spheres \n
                        radii (Sphere Radii = cpkRad + property * scaleFactor), \n
        propertyLevel --- can be one of the following: 'Atom', 'Residue', 'Chain', 'Molecule'.
        keywords --- display, CPK, space filling, undisplay.\n
    """

        
    def onAddCmdToApp(self,):
        DisplayCommand.onAddCmdToApp(self)

        if not self.app().commands.has_key('assignAtomsRadii'):
            self.app().lazyLoad('editCmds', commands=['assignAtomsRadii'], package='PmvApp')

        from mglutil.util.colorUtil import ToHEX
        self.molDict = {'Molecule':Molecule,
                        'Atom':Atom, 'Residue':Residue, 'Chain':Chain}
        self.nameDict = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}

        self.leveloption={}
        for name in ['Atom', 'Residue', 'Molecule', 'Chain']:
            col = self.app().levelColors[name]
            bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
            ag = ToHEX(col)
            self.leveloption[name]={#'bg':bg,
                                    'activebackground':bg, 'selectcolor':ag ,
                                    'borderwidth':3 , 'width':15}
        self.propValues = None
        self.getVal = 0
        self.propertyLevel = self.nameDict[self.app().selectionLevel]

        

    def onAddObjectToViewer(self, obj):
        """Adds the cpk geometry and the cpk Atomset to the object's
        geometry container
        """
        self.objectState[obj] = {'onAddObjectCalled':True}
        if self.app().commands.has_key('dashboard'):
            self.app().dashboard.resetColPercent(obj, '_showCPKStatus')

        obj.allAtoms.cpkScale = 1.0
        obj.allAtoms.cpkRad = 0.0
        geomC = obj.geomContainer
        # CPK spheres
        g = Spheres( "cpk", quality=0 ,visible=0, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['cpk'] = None
        for atm in obj.allAtoms:
            #atm.colors['cpk'] = (1.0, 1.0, 1.0)
            atm.opacities['cpk'] = 1.0


    def onRemoveObjectFromViewer(self, obj):
        if self.objectState.has_key(obj):
            self.objectState.pop(obj)    


    def undoCmdBefore(self, nodes, only=False, negate=False, scaleFactor=1.0,
                        cpkRad=0.0, quality=0, byproperty = False,
                        propertyName=None, propertyLevel='Molecule',
                        setScale=True, unitedRadii=True, redraw=True ):

        #print "in undoCmdBefore: only= ", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property = ", propertyName, "propertyLevel = ", propertyLevel

        kw = self.getLastUsedValues()
        geomSet = []
        for mol in self.app().Mols:
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            geomSet = geomSet + mol.geomContainer.atoms['cpk']
        #print "geomset:", len(geomSet)
        if len(geomSet) == 0:
            # If nothing was displayed before, the undo of a display
            # command is to undisplay what you just displayed 
            kw['negate'] = True
            #print "kw:", kw
            return ( [(self, (nodes,), kw)], self.name)
        else:
            # If the current was already displayed and only is False and negate
            # is False then the undo is to display this set using the last used
            # values.
            
            # If something was already displayed, the undo of a display
            # command is to display ONLY what was displayed before.
            #kw['only'] = True
            #print "kw:", kw
            return ( [(self, (geomSet,), kw)], self.name)


    def doit(self, nodes, only=False, negate=False, scaleFactor=1.0,
             cpkRad=0.0, quality=0,  byproperty = False, propertyName=None,
             propertyLevel='Molecule', setScale=True, unitedRadii=True, redraw=True):

        #print "in  doit: only=", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property=", propertyName, "propertyLevel = ", propertyLevel

        ##############################################################
        def drawAtoms( mol, atms, only, negate, scaleFactor, cpkRad, quality,
                       propertyName = None, propertyLevel="Molecule",
                       setScale=True):
            """
            handle all the atoms in one molecule
            """
            if setScale:
                atms.cpkScale = scaleFactor
                atms.cpkRad = cpkRad
            _set = mol.geomContainer.atoms['cpk']
            if len(atms) == len(mol.allAtoms):
                if negate:
                    setOff = atms
                    setOn = None
                    _set = AtomSet()
                else:
                    _set = atms
                    setOff = None
                    setOn = atms
            else:
                ##if negate, remove current atms from displayed _set
                if negate:
                    setOff = atms
                    setOn = None
                    _set = _set - atms

                ##if only, replace displayed _set with current atms 
                else:
                    if only:
                        setOff = _set - atms
                        setOn = atms
                        _set = atms
                    else: 
                        _set = atms + _set
                        setOff = None
                        setOn = _set

            # at this point _set is what will still be displayed as CPK after this cmd
            mol.geomContainer.setAtomsForGeom('cpk', _set)

            g = mol.geomContainer.geoms['cpk']
            if len(_set)==0: # nothing is diplayed as CPK anymore for this molecule
                g.Set(visible=0, tagModified=False) # hide the geom
            else: # CPK is still displayed for this molecule
                #_set.sort()   # EXPENSIVE...
                # The following assumes that the lines geometry has been added:
                colors = [x.colors.get('cpk', x.colors['lines']) for x in _set]
                # check if all colors are the same
                cd = {}.fromkeys(['%f%f%f'%tuple(c) for c in colors])
                if len(cd)==1:
                    colors = [colors[0]]

                cpkSF = numpy.array(_set.cpkScale)
                rad = _set.radius
                if propertyName:
                    propvals = self.getPropValues(_set, propertyName, propertyLevel)
                    rad = propvals
                cpkRad = numpy.array(_set.cpkRad)                
                sphRad = cpkRad + cpkSF*numpy.array(rad)
                sphRad = sphRad.tolist()

                g.Set(vertices=_set.coords, inheritMaterial=False, 
                      materials=colors, radii=sphRad, visible=1,
                      quality=quality, tagModified=False)
                
                # highlight selection
                selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get())
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
                if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['cpk']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)
            return setOn, setOff
        
        ##################################################################
                
        #molecules, atmSets = self.getNodes(nodes)
        molecules, atmSets = self.app().getNodesByMolecule(nodes, Atom)
        setOn = AtomSet([])
        setOff = AtomSet([])
        for mol in molecules:
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            hasRadii = False
            try:
                radii = mol.allAtoms.radius
                hasRadii = True
            except:
                pass
            #print "united:", unitedRadii, "mol.unitedRadii:", mol.unitedRadii
            if not hasRadii or mol.unitedRadii != unitedRadii:
                #print "defaultRadii"
                mol.unitedRadii = unitedRadii
                mol.defaultRadii(united=unitedRadii, overwrite=True)

        for mol, atms in map(None, molecules, atmSets):
            try:
                if self._failForTesting:
                    a = 1/0.
                if byproperty:
                    son, sof = drawAtoms(
                        mol, atms, only, negate, scaleFactor, cpkRad,
                        quality, propertyName, propertyLevel,setScale=setScale)
                else:
                    son, sof = drawAtoms(mol, atms, only, negate, 
                                         scaleFactor, cpkRad, quality,
                                         setScale=setScale)
                if son: setOn += son
                if sof: setOff += sof
                self.app()._executionReport.addSuccess('displayed CPK for molecule %s successfully'%
                    mol.name, obj=atms)
            except:
                msg = 'Error while displaying CPK for molecule %s'%mol.name
                self.app().errorMsg(sys.exc_info(), msg, obj=atms)
        if only and len(molecules)!=len(self.app().Mols):
            # if only is True we need to undisplay lines for molecules
            # that are not included in nodes
            mols = self.app().Mols - molecules
            for mol in mols:
                try:
                    only = False
                    negate = True
                    if byproperty:
                        son, sof = drawAtoms(
                            mol, mol.allAtoms, only, negate, scaleFactor, cpkRad,
                            quality, propertyName, propertyLevel, setScale)
                    else:
                        son, sof = drawAtoms(mol, mol.allAtoms, only, negate, 
                                             scaleFactor, cpkRad, quality,
                                             setScale=setScale)
                    if son: setOn += son
                    if sof: setOff += sof
                except:
                    msg = 'Error while undisplaying CPK for molecule %s to enforce only=True option'%mol.name
                    self.app().errorMsg(sys.exc_info(), msg, obj=mol)
                
        if self.createEvents:
            event = EditGeomsEvent(
            'cpk', [nodes,[only, negate,scaleFactor,cpkRad,quality,
                           byproperty,propertyName, propertyLevel,redraw]],
                                    setOn=setOn, setOff=setOff)
            self.app().eventHandler.dispatchEvent(event)

        
    def checkArguments(self, nodes, only=False, negate=False, 
                 scaleFactor=1.0,  cpkRad=0.0, quality=0,  byproperty=False,
                 propertyName=None, propertyLevel='Molecule',
                 setScale=True, unitedRadii=True, redraw=True):
        """
           nodes --- TreeNodeSet holding the current selection
           \nonly --- Boolean flag: when True only the current selection will be
                    displayed
           \nnegate --- Boolean flag: when True undisplay the current selection
           \nscaleFactor --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default is 1.0)
           \ncpkRad --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default 0.0). This arg
           \ncorresponds to the 'Offset' on the gui input form.
           \nquality --- sphere quality default value is 10
           \npropertyName --- if specified,  the property is used to compute the sphere radii (Sphere Radii = cpkRad + property * scaleFactor),
           \npropertyLevel --- can be one of the following: 'Atom', 'Residue', 'Chain', 'Molecule'.
           \nsetScale --- when true atm.scaleFactor and atm.cpkRad are set"""

        #print "in  checkArguments: only= ", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property=", propertyName, "propertyLevel = ", propertyLevel
        kw = {}
        assert isinstance(scaleFactor, (int , float, long))
        assert isinstance(cpkRad, (int , float, long))
        assert isinstance(quality, int)
        assert (quality>=0)
        assert only in [True, False, 0, 1]
        assert negate in [True, False, 0, 1]
        assert byproperty in [True, False, 0, 1]
        assert setScale in [True, False, 0, 1]
        assert unitedRadii in [True, False, 0, 1]        
        assert propertyLevel in ['Atom', 'Residue', 'Chain', 'Molecule']
        if propertyName is not None:
            if not isinstance(propertyName, str):
                assert isinstance (propertyName, (list, tuple))
                propertyName = propertyName[0]
                assert isinstance(propertyName, str)
            byproperty = True
        if isinstance (nodes, str):
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.app().expandNodes(nodes)

        kw['only'] = only
        kw['negate'] = negate
        kw['scaleFactor'] = scaleFactor
        kw['cpkRad'] = cpkRad
        kw['quality'] = quality
        kw['setScale']= setScale
        kw['unitedRadii'] = unitedRadii
        kw['propertyName'] = propertyName
        kw['propertyLevel']= propertyLevel
        kw['byproperty'] = byproperty

        #self.lastUsedValues['default']['byproperty'] = byproperty
        #self.lastUsedValues['default']['propertyName'] = propertyName
        #self.lastUsedValues['default']['unitedRadii'] = unitedRadii
        kw['redraw'] = redraw
        return (nodes,), kw


    def getPropValues(self, nodes, prop, propertyLevel=None):
        try:
            if propertyLevel is not None:
                #lNodesInLevel = self.app().activeSelection.get().findType(self.molDict[propertyLevel])
                lNodesInLevel = nodes.findType(self.molDict[propertyLevel])     
                num = len(lNodesInLevel.findType(Atom))
                propValues = getattr(lNodesInLevel, prop)
            else:
                propValues = getattr(nodes, prop)
        except:
            msg= "DisplayCPK.getPropValues: nodes do not have the selected property %s" % prop
            raise RuntimeError(msg)

        return propValues

    def getProperties(self, selection):

        properties = [x[0] for x in selection[0].__dict__.items() if (
            x[0][0]!='_' and isinstance(x[1], (int, float)))]
        #print "getProperties:", properties
        return properties


        
class UndisplayCPK(DisplayCommand):
    """ The undisplayCPK command is a picking command allowing the user to undisplay the CPK geometry representing the picked nodes when used as a picking command or the given nodes when called from the Python shell.
    \nPackage : PmvApp
    \nModule  : displayCmds
    \nClass   : UndisplayCPK
    \nCommand : undisplayCPK
    \nSynopsis:\n
        None <- undisplayCPK(nodes, **kw)\n
        nodes : any set of MolKit nodes describing molecular components\n
        keywords: undisplay, CPK\n
    """

    def onAddCmdToApp(self):
        DisplayCommand.onAddCmdToApp(self)
        if not self.app().commands.has_key('displayCPK'):
            self.app().lazyLoad('displayCmds', commands=['displayCPK'], package='PmvApp')


    def checkArguments(self, nodes, **kw):
        kw['negate' ] = True
        return self.app().displayCPK.checkArguments(nodes, **kw)


    def doit(self, nodes, **kw):
        return self.app().displayCPK(nodes, **kw)


class DisplaySticksAndBalls(DisplayCommand):
    """The displaySticksAndBalls command allows the user to display/undisplay
the given nodes using the sticks and balls representation, where the bonds are
represented by cylinders and the atoms by balls.The radii of the cylinders and
the balls, and the quality of the spheres are user defined. The user can chose
to display 'Licorice', 'Sticks only' or 'Sticks and Balls'.
Package : PmvApp
Module  : displayCmds
Class   : DisplaySticksAndBalls
Command : displaySticksAndBalls
Synopsis:
    None <--- displaySticksAndBalls(nodes,  only=0, negate=0,
                                    sticksBallsLicorice='Sticks and Balls',
                                    bradii=0.4, bquality=0, cradius=0.2,
                                    absolute=1)
    nodes --- any set of MolKit nodes describing molecular components
    only  --- Boolean flag specifying whether or not to only display
              the current selection\n
    negate --- Boolean flag specifying whether or not to undisplay
               the current selection\n
    sticksBallsLicorice --- string specifying the type of rendering
    cradius --- cylinder radius\n
    bradii ---  radius of the balls (if balls are displayed)
    bquality --- quality of the balls (if balls are displayed)
    keywords --- display sticks and balls representation
"""

    def onRemoveObjectFromViewer(self, mol):
        if self.objectState.has_key(mol):
            self.objectState.pop(mol)
            

    def onAddCmdToApp(self):
        DisplayCommand.onAddCmdToApp(self)
        if not self.app().commands.has_key('assignAtomsRadii'):
            self.app().lazyLoad('editCmds', commands=['assignAtomsRadii'], package='PmvApp')


    def onAddObjectToViewer(self, obj):
        self.objectState[obj] = {'onAddObjectCalled':True}
        if self.app().commands.has_key('dashboard'):
            self.app().dashboard.resetColPercent(obj, '_showS&BStatus')
        defaultValues = self.lastUsedValues['default']
        obj.allAtoms.ballRad = defaultValues['bRad']
        obj.allAtoms.ballScale = defaultValues['bScale']
        obj.allAtoms.cRad = defaultValues['cradius']

        geomC = obj.geomContainer

        # Cylinders (sticks)
        g = Cylinders( "sticks", visible=0, vertices=geomC.allCoords, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)

        # Spheres at atomic positions (used for stick and balls)
        g = Spheres( "balls", vertices = geomC.allCoords,
                     radii = 0.4, quality = 4 ,visible=0, protected=True)
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['balls'] = None

        for atm in obj.allAtoms:
            #atm.colors['sticks'] = (1.0, 1.0, 1.0)
            atm.opacities['sticks'] = 1.0
            #atm.colors['balls'] = (1.0, 1.0, 1.0)
            atm.opacities['balls'] = 1.0


 

    def undoCmdBefore(self, nodes, only=False, negate=False,
                        bRad=0.3, bScale=0.0,
                        bquality=0, cradius=0.2, cquality=0, absolute=True,
                        sticksBallsLicorice='Licorice', setScale=True, redraw=True):
        
        kw={}
        defaultValues = self.lastUsedValues['default']
        
        kw['bRad'] = defaultValues['bRad']
        kw['bScale'] = defaultValues['bScale']
        kw['bquality'] = defaultValues['bquality']
        kw['cradius'] = defaultValues['cradius']
        kw['cquality'] = defaultValues['cquality']
        kw['sticksBallsLicorice'] = defaultValues['sticksBallsLicorice']
        
        ballset = AtomSet()
        stickset = AtomSet()
        for mol in self.app().Mols:
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            ballset = ballset + mol.geomContainer.atoms['balls']
            stickset = stickset + mol.geomContainer.atoms['sticks']

        if len(ballset)==0:
            # no balls displayed
            if len(stickset) == 0: # negate
                # no stick displayed 
                kw['negate'] = True
                kw['redraw'] = True
                return ( [(self, (nodes,), kw)], self.name)
            else:
                # noballs was on
                kw['negate'] = False
                kw['redraw'] = True
                kw['only'] = True
                return ( [(self, (stickset,), kw)], self.name)
        else:

            kw['redraw'] = True
            kw['only'] = True
            return ( [(self, (stickset,), kw)], self.name)


    def doit(self, nodes, only=False, negate=False, bRad=0.3,
             bScale=0.0, bquality=0, cradius=0.2, cquality=0,
             sticksBallsLicorice='Licorice', setScale=True, redraw=True):
        #import pdb;pdb.set_trace()

        ########################################################

        def drawBalls(mol, atm, only, noBalls, negate, bRad, bScale,
                      bquality, setScale):
            if setScale:
                atm.ballRad = bRad
                atm.ballScale = bScale
            _set = mol.geomContainer.atoms['balls']
            if len(_set)>mol.allAtoms:
                _set = mol.allAtoms
                mol.geomContainer.setAtomsForGeom('balls', _set)
            if len(mol.geomContainer.atoms['balls']) > mol.allAtoms:
                mol.geomContainer.setAtomsForGeom('balls', mol.allAtoms)

             ## case noballs:
            if noBalls:
                 if only:
                     if len(atm) == len(mol.allAtoms):
                         _set = atm
                     else:
                         _set = atm.union(_set)
                     mol.geomContainer.geoms['balls'].Set(visible=0,
                                                          tagModified=False)
                     mol.geomContainer.setAtomsForGeom('balls', _set)
                     return None, atm
                 else:
                     negate = True
            
            ## Then handle only and negate    
            ##if negate, remove current atms from displayed _set
            if len(atm) == len(mol.allAtoms):
                if negate:
                    _set = AtomSet([])
                    setOff = atm
                    setOn = None
                else: 
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                if negate:
                    _set = _set - atm
                    setOff = atm
                    setOn = None
                else:
                    ##if only, replace displayed _set with current atms
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            if len(_set) == 0:
                mol.geomContainer.geoms['balls'].Set(visible=0,
                                                     tagModified=False)
                mol.geomContainer.setAtomsForGeom('balls', _set)
                return setOn, setOff
            
            mol.geomContainer.setAtomsForGeom('balls', _set)
            #_set.sort()
            bScale = numpy.array(_set.ballScale)
            bRad = numpy.array(_set.ballRad)
            aRad = numpy.array(_set.radius)
            
            ballRadii = bRad + bScale * aRad
            ballRadii = ballRadii.tolist()
            
            geom = mol.geomContainer.geoms['balls']
            bcolors = [x.colors.get('balls', x.colors['lines']) for x in _set]
            geom.Set(vertices=_set.coords, radii=ballRadii,
                  materials=bcolors, inheritMaterial=False, 
                  visible=1, tagModified=False)
            
            geom.Set(quality=bquality, tagModified=False)

            # highlight selection
            selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get())
            lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
            lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
            if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['balls']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        geom.Set(highlight=highlight)

            return setOn, setOff

 
        def drawSticks(mol, atm, only, negate, cradius, cquality,
                       setScale):
            if setScale:
                atm.cRad = cradius
            _set = mol.geomContainer.atoms['sticks']
            ##if negate, remove current atms from displayed _set
            if len(atm) == len(mol.allAtoms):
                if negate:
                    _set = AtomSet()
                    setOff = atm
                    setOn = None
                else:
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                if negate:
                    setOff = atm
                    setOn = None
                    _set = _set - atm
                else:
                    ## if only, replace displayed _set with current atms
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm.union(_set)
                        setOff = None
                        setOn = _set

            if len(_set) == 0:
                mol.geomContainer.geoms['sticks'].Set(visible=0,
                                                      tagModified=False)
                mol.geomContainer.setAtomsForGeom('sticks', _set)
                return setOn, setOff

            bonds, atnobnd = _set.bonds
            mol.geomContainer.setAtomsForGeom('sticks', _set)
            indices = [(x.atom1._bndIndex_, x.atom2._bndIndex_) for x in bonds]
            g = mol.geomContainer.geoms['sticks']
            if len(indices) == 0:
                g.Set(visible=0, tagModified=False, redo=False)
            else:
                cRad = _set.cRad
                scolors = [x.colors.get('sticks', x.colors['lines']) for x in _set]
                g.Set( vertices=_set.coords, faces=indices, radii=cRad,
                       materials=scolors, visible=1, quality=cquality,
                       tagModified=False, inheritMaterial=False)

            # highlight selection
            selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get())
            lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
            lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
            if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['sticks']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)
            return setOn, setOff

        ###########################################################

        molecules, atomSets = self.app().getNodesByMolecule(nodes, Atom)
        setOn = AtomSet([])
        setOff = AtomSet([])
       
        try:
            radii = molecules.allAtoms.radius
        except:
            self.app().assignAtomsRadii(molecules, 
                                     overwrite=False,
                                     united=False)

        for mol, atm in map(None, molecules, atomSets):
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            try:
                if sticksBallsLicorice == 'Licorice':
                    son, sof = drawBalls(mol, atm, only, 0, negate, cradius,
                                      0.0, cquality, setScale)
                elif sticksBallsLicorice == 'Sticks only':
                    son, sof = drawBalls(mol, atm, only, 1, negate, bRad,
                                      bScale, bquality, setScale)
                else:
                    son, sof = drawBalls(mol, atm, only, 0, negate, bRad,
                                      bScale, bquality, setScale)

                if son: setOn += son
                if sof: setOff += sof

                son, sof = drawSticks(mol, atm, only, negate, cradius,
                                   cquality, setScale)
                if son: setOn += son
                if sof: setOff += sof
                self.app()._executionReport.addSuccess('displayed sticks and balls for molecule %s successfully'%
                    mol.name, obj=atm)
            except:
                msg = 'Error while displaying sticks and balls (%s) for molecule %s' %\
                      (sticksBallsLicorice, mol.name)
                self.app().errorMsg(sys.exc_info(), msg, obj=atm)

        if only and len(self.app().Mols) != len(molecules):
            # if only is True we need to undisplay S&B for molecules
            # that are not included in nodes
            mols = self.app().Mols - molecules
            for mol in mols:
                try:
                    negate = True
                    only=False
                    if sticksBallsLicorice == 'Licorice':
                        son, sof = drawBalls(mol, mol.allAtoms, only, 0, negate,
                                             cradius, 0, cquality, setScale)
                    elif sticksBallsLicorice == 'Sticks only':
                        son, sof = drawBalls(mol, mol.allAtoms, only, 1, negate,
                                             bRad, bScale, bquality, setScale)
                    else:
                        son, sof = drawBalls(mol, mol.allAtoms, only, 0, negate,
                                             bRad, bScale, bquality, setScale)
                    if son: setOn += son
                    if sof: setOff += sof
                    son, sof = drawSticks(mol, mol.allAtoms, only, negate,
                                          cradius, cquality, setScale)
                    if son: setOn += son
                    if sof: setOff += sof
                except:
                    msg = 'Error while undisplaying S&B for molecule %s to enforce only=True option'%mol.name
                    self.app().errorMsg(sys.exc_info(), msg, obj=mol)

        if self.createEvents:
            event = EditGeomsEvent('bs', [nodes,[only, negate, bRad,
                                bScale, bquality, cradius, cquality,
                                sticksBallsLicorice,redraw]],
                                setOn=setOn, setOff=setOff)
            self.app().eventHandler.dispatchEvent(event)



    def checkArguments(self, nodes, only=False, negate=False,
                 bRad=0.3, bScale=0.0, bquality=0, cradius=0.2, cquality=0,
                 sticksBallsLicorice='Licorice', setScale=True, redraw=True):

        """
        nodes --- any set of MolKit nodes describing molecular components \n
        only  --- flag to only display the current selection \n
        negate  --- flag to undisplay the current selection \n
        bRad  --- defines the radius of the balls \n
        bScale --- defines the scale factor to be applied to the atom radius to
               compute the sphere radius (bRad + atom.radius *bScale)\n
        bquality --- defines the quality of the balls \n
        cradius --- defines the cylinder radius \n
        cquality --- defines the quality of the cylinders \n
        setScale --- when True atm.ballRad, atm.ballScale and atm.cRad are set;\n
                     if set to False, atm.ballRad, atm.ballScale and atm.cRad are used \n
                     instead of bRad, bScale, and cradius. 
        sticksBallsLicorice --- string specifying the type of rendering,
                     can be 'Licorice', 'Sticks only' or 'Sticks and Balls'
        """

        assert only in [True, False, 0, 1]
        assert negate in [True, False, 0, 1]
        assert isinstance(bRad, (int , float, long))
        assert isinstance(bScale, (int , float, long))
        assert isinstance(bquality, int)
        assert (bquality>=0)
        assert isinstance(cradius, (int , float, long))
        assert isinstance(cquality, (int , float, long))
        assert sticksBallsLicorice in ('Licorice', 'Sticks only','Sticks and Balls')
        assert setScale in [True, False, 0, 1]
        if isinstance (nodes, str):
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.app().expandNodes(nodes)

        kw = {'only':only, 'negate':negate , 'bRad':bRad , 'bScale':bScale ,
              'bquality':bquality , 'cradius':cradius , 'cquality':cquality ,
              'sticksBallsLicorice':sticksBallsLicorice , 'setScale':setScale ,
              'redraw':redraw}
        return (nodes,), kw



class UndisplaySticksAndBalls(DisplayCommand):
    """ The UndisplaySticksAndBalls command is an interactive command to undisplay part of the molecule when represented as sticks and balls.
    \nPackage : PmvApp
    \nModule  : displayCmds
    \nClass   : UnDisplaySticksAndBalls
    \nCommand : undisplaySticksAndBalls
    \nSynopsis:\n
        None <- undisplaySticksAndBalls(nodes, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        keywords --- undisplay, SticksAndBalls\n
    """

    def onAddCmdToApp(self):
        DisplayCommand.onAddCmdToApp(self)
        if not self.app().commands.has_key('displaySticksAndBalls'):
            self.app().lazyLoad('displayCommands', commands=['displaySticksAndBalls'],
                             package='PmvApp')


    def checkArguments(self, nodes, **kw):
        """ nodes: TreeNodeSet holding the current selection"""
        kw['negate']= 1
        return self.app().displaySticksAndBalls.checkArguments(nodes, **kw)

    def doit(self,  nodes, **kw):
        self.app().displaySticksAndBalls(nodes, **kw)



class DisplayBackboneTrace(DisplaySticksAndBalls):
    """The displayBackboneTrace command allows the user to display/undisplay the given nodes using the sticks and balls representation, where the bonds are represented by cylinders and the atoms by balls.The radii of the cylinders and the balls, and the quality of the spheres are user defined.The user can chose to display 'Licorice', 'Sticks only' or 'Sticks and Balls'.
    \nPackage : PmvApp
    \nModule  : displayCommands
    \nClass   : DisplayBackboneTrace
    \nCommand : displayBackboneTrace
    \nSynopsis:\n
        None <- displayBackboneTrace(nodes,  only=0, negate=0, noballs=0,
                                      bradii=0.4, bquality=4, cradius=0.2,
                                      absolute=1, **kw)\n
        nodes   : any set of MolKit nodes describing molecular components\n
        only    : Boolean flag specifying whether or not to only display
                  the current selection\n
        negate  : Boolean flag specifying whether or not to undisplay
                  the current selection\n
        cradius : specifies the cylinder radius\n
        bradii  : specifies the radius of the balls if displayed.\n
        bquality: specifies the quality of the balls if displayed.\n
        setScale --- when True atm.caballRad, atm.caballScale and atm.cacRad are set;\n
                     if set to False, atm.caballRad, atm.caballScale and atm.cacRad \n
                     are used  instead of bRad, bScale, and cradius. 
        sticksBallsLicorice --- string specifying the type of rendering,
                     can be 'Licorice', 'Sticks only' or 'Sticks and Balls'
        keywords: display BackboneTrace representation\n
    """

    def onAddObjectToViewer(self, obj):
        self.objectState[obj] = {'onAddObjectCalled':True}
        self.objectState[obj] = {'onAddObjectCalled':True}
        defaultValues = self.lastUsedValues['default']
        obj.allAtoms.caballRad = defaultValues['bRad']
        obj.allAtoms.caballScale = defaultValues['bScale']
        obj.allAtoms.cacRad = defaultValues['cradius']

        geomC = obj.geomContainer

        # Cylinders (sticks)
        g = Cylinders( "CAsticks", visible=0, vertices = geomC.allCoords, protected=True)
        geomC.addGeom(g)
        self.managedGeometries.append(g)

        # Spheres at atomic positions (used for stick and balls)
        g = Spheres( "CAballs", vertices = geomC.allCoords,
                     radii = 0.4, quality = 4 ,visible=0, protected=True)
        geomC.addGeom(g)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['CAballs'] = None

        for atm in obj.allAtoms:
            #atm.colors['CAsticks'] = (1.0, 1.0, 1.0)
            atm.opacities['CAsticks'] = 1.0
            #atm.colors['CAballs'] = (1.0, 1.0, 1.0)
            atm.opacities['CAballs'] = 1.0


    def undoCmdBefore(self, nodes, only=False, negate=False,
                        bRad=0.3, bScale=0.0, bquality=0,
                        cradius=0.2, cquality=0, setScale=True, 
                        sticksBallsLicorice='Sticks and Balls',
                        redraw=True):
        
        kw={}
        defaultValues = self.lastUsedValues['default']

        kw['bRad'] = defaultValues['bRad']
        kw['bScale'] = defaultValues['bScale']
        kw['bquality'] = defaultValues['bquality']
        kw['cradius'] = defaultValues['cradius']
        kw['cquality'] = defaultValues['cquality']
        kw['sticksBallsLicorice'] = defaultValues['sticksBallsLicorice']
        
        caballset = AtomSet()
        castickset = AtomSet()
        for mol in self.app().Mols:
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            caballset =  caballset+mol.geomContainer.atoms['CAballs']
            castickset = castickset+mol.geomContainer.atoms['CAsticks']
           
        if len(caballset)==0:
            # no balls displayed
            if len(castickset) == 0: # negate
                # no stick displayed 
                kw['negate'] = True
                kw['redraw'] = True
                return ( [(self, (nodes,), kw)], self.name)
            else:
                # noballs was on
                kw['negate'] = False
                kw['redraw'] = True
                kw['only'] = True
                return ([(self, (castickset,), kw)], self.name)
        else:

            kw['redraw'] = True
            kw['only'] = True
            return ([(self, (castickset,), kw)], self.name)



    def doit(self, nodes, only=False, negate=False, bRad=0.3,
             bScale=0.0, bquality=0, cradius=0.2, cquality=0, 
             sticksBallsLicorice='Sticks and Balls', setScale=True, redraw=True):

        ########################################################
            
        def drawCABalls(mol, atm, only, noBalls, negate, bRad, bScale,
                      bquality, setScale):
            if setScale:
                atm.caballRad = bRad
                atm.caballScale = bScale
            
            _set = mol.geomContainer.atoms['CAballs']
            ## case noballs:
            if noBalls:
                if only:
                    if len(atm) == len(mol.allAtoms):
                        _set = atm
                    else:
                        _set = atm.union(_set)
                    mol.geomContainer.geoms['CAballs'].Set(visible=0,
                                                         tagModified=False)
                    mol.geomContainer.setAtomsForGeom('CAballs', _set)
                    return
                else:
                    negate = True
            
            ## Then handle only and negate    
            ##if negate, remove current atms from displayed _set
            if len(atm) == len(mol.allAtoms):
                if negate: _set = AtomSet([])
                else: _set = atm
            else:
                if negate:
                    _set = _set - atm
                else:
                    ##if only, replace displayed _set with current atms
                    if only:
                        _set = atm
                    else: 
                        _set = atm.union(_set)
            if len(_set) == 0:
                mol.geomContainer.geoms['CAballs'].Set(visible=0,
                                                     tagModified=False)
                mol.geomContainer.setAtomsForGeom('CAballs', _set)
                return
            
            mol.geomContainer.setAtomsForGeom('CAballs', _set)
            #_set.sort()
            bScale = numpy.array(_set.caballScale)
            bRad = numpy.array(_set.caballRad)
            aRad = numpy.array(_set.radius)
            ballRadii = bRad + bScale * aRad
            ballRadii = ballRadii.tolist()

            b = mol.geomContainer.geoms['CAballs']
            # this assumes that the lines geometry has been added
            bcolors = [x.colors.get('CAballs', x.colors['lines']) for x in _set]
            b.Set(vertices=_set.coords, radii=ballRadii,
                  materials=bcolors, inheritMaterial=False, 
                  visible=1, quality=bquality, tagModified=False)

            # highlight selection
            selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get())
            lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
            lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
            if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['CAballs']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        b.Set(highlight=highlight)


        def drawCASticks(mol, atm, only, negate, cradius, cquality, setScale):

                atm.sort()
                if setScale:
                    atm.cacRad = cradius
                _set = mol.geomContainer.atoms['CAsticks']
                 
                if negate:
                    _set = mol.geomContainer.atoms['CAsticks']
                    _set = _set - atm
                         
                else:                       
                     if only: 
                            _set = atm                            
                     else: 
                            _set = atm.union(_set)
                            
                if len(_set) == 0:
                    mol.geomContainer.geoms['CAsticks'].Set(visible=0,
                                                      tagModified=False)
                    mol.geomContainer.setAtomsForGeom('CAsticks', _set)
                    return

                mol.geomContainer.setAtomsForGeom('CAsticks', _set)
             
                indices =[]
                                   
                for i in range(0,len(_set)):
                        if i+1 <=len(_set)-1:
                            indices.append((i,i+1))
                                     
                for ch in range(0,len(mol.chains)-1):
                      list =[]
                    
                      if len(mol.chains)>1: 
                        a=mol.chains[ch].getAtoms().get(lambda x: x.name=='CA')
                        a.sort()
                        for l in _set:
                            for k in a:
                                if l==k:            
                                    list.append(l)
                        i =len(list)
                        if _set !=list:
                            if (i-1,i) in indices:
                                ind=indices.index((i-1,i))
                                del indices[ind]

                for ch in range(0,len(mol.chains)):    
                    #finding tranformed coordsd to pass in to FindGap
                    chatoms=_set
                    mats=[]
                    for ca in chatoms:
                        c = self.app().transformedCoordinatesWithInstances(AtomSet([ca]))
                        mat = numpy.array(c[0], 'f')
                        mats.append(mat)
                        
                    from MolKit.GapFinder import FindGap
                    #calling Find Gap such that chains with residues not connected will 
                    #have an attribute 'hasGap' and CA atoms have "gap" attribute
                    
                    if len(_set)!=0:
                         _set.sort()
                         mygap = FindGap(mats,mol.chains[ch],_set)
                         if hasattr(mol.chains[ch],'hasGap'):
                             for i in range(0,len(chatoms)):
                                 if hasattr(chatoms[i],"gap"):
                                     if i+1<=len(chatoms)-1:
                                         if chatoms[i].gap=='start':
                                             #indi=chatoms.index(chatoms[i])
                                             for at in _set:
                                                 if chatoms[i]==at:
                                                     indi =_set.index(at)
                                             if (indi,indi+1) in indices:
                                                 ind=indices.index((indi,indi+1))    
                                                 del indices[ind] 
                                            
                mol.geomContainer.setAtomsForGeom('CAsticks', _set)
                g = mol.geomContainer.geoms['CAsticks'] 
                if len(indices) == 0:
                    g.Set(visible=0, tagModified=False)
                else:
                    cRad = _set.cacRad
                    scolors = [x.colors.get('CAsticks', x.colors['lines']) for x in _set]
                    g.Set( vertices=_set.coords, faces=indices, radii=cRad,
                           materials=scolors, visible=1, quality=cquality,
                           tagModified=False,  inheritMaterial=False)

                # highlight selection
                selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get())
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
                if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['CAsticks']
                    if len(lVertexClosestAtomSet) > 0:
                        lVertexClosestAtomSetDict = dict(zip(lVertexClosestAtomSet,
                                                             range(len(lVertexClosestAtomSet))))
                        highlight = [0] * len(lVertexClosestAtomSet)
                        for i in range(len(lSelectedAtoms)):
                            lIndex = lVertexClosestAtomSetDict.get(lSelectedAtoms[i], None)
                            if lIndex is not None:
                                highlight[lIndex] = 1
                        g.Set(highlight=highlight)


        ########################################################
        
        molecules, atmSets = self.app().getNodesByMolecule(nodes, Atom)
        try:
            radii = molecules.allAtoms.radius
        except:
            self.app().assignAtomsRadii(molecules, 
                                     overwrite=False,
                                     united=False)

        for mol, atom in map(None, molecules, atmSets):
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            #for chain in mol.chains:
            try:
                if self._failForTesting:
                    a = 1/0.
                atm = atom.get(lambda x:x.name =='CA')
                if len(atm)==0:
                    raise RuntimeError("No CA atoms in %s"%mol.name) 
                if sticksBallsLicorice == 'Licorice':
                    drawCABalls(mol, atm, only, 0, negate, cradius, 0,
                                cquality, setScale)
                elif sticksBallsLicorice == 'Sticks only':
                    drawCABalls(mol, atm, only, 1, negate, bRad, bScale,
                                bquality, setScale)
                else:
                    drawCABalls(mol, atm, only, 0, negate, bRad, bScale,
                           bquality, setScale)
                drawCASticks(mol, atm, only, negate, cradius, cquality, setScale)
                self.app()._executionReport.addSuccess('displayed backbone trace for molecule %s successfully'%
                    mol.name, obj=atm)
            except:
                msg = 'Error while displaying backbone trace(%s) for molecule %s' %\
                      (sticksBallsLicorice, mol.name)
                self.app().errorMsg(sys.exc_info(), msg, obj=atm)
            
        if only and len(self.app().Mols) != len(molecules):
            # if only is True we need to undisplay back bone for molecules
            # that are not included in nodes
            mols = self.app().Mols - molecules
            for mol in mols:
                try:
                    negate = True
                    only=0
                    if sticksBallsLicorice == 'Licorice':
                        drawCABalls(mol, mol.allAtoms, only, 0, negate, cradius,
                              0, cquality, setScale)
                    elif sticksBallsLicorice == 'Sticks only':
                        drawCABalls(mol, mol.allAtoms, only, 1, negate, bRad,
                              bScale, bquality, setScale)
                    else:
                        drawCABalls(mol, mol.allAtoms, only, 0, negate, bRad,
                              bScale, bquality, setScale)
                    drawCASticks(mol, mol.allAtoms, only, negate, cradius, cquality, setScale)
                except:
                    msg = 'Error while undisplaying backbone trace for molecule %s to enforce only=True option'%mol.name
                    self.app().errorMsg(sys.exc_info(), msg, obj=mol) 
        if self.createEvents:
            event = EditGeomsEvent('trace', [nodes,[only, negate, bRad,bScale, bquality, 
						cradius, cquality,sticksBallsLicorice]])
            self.app().eventHandler.dispatchEvent(event)



class UndisplayBackboneTrace(DisplayCommand):
    """ The UndisplayBackboneTrace command is an interactive command to undisplay part of the molecule when represented as sticks and balls.
    \nPackage : PmvApp
    \nModule  : displayCmds
    \nClass   : UnDisplayBackboneTrace
    \nCommand : undisplayBackboneTrace
    \nSynopsis:\n
        None <- undisplayBackboneTrace(nodes, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        keywords --- undisplay, lines\n 
    """

    def onAddCmdToApp(self):
        DisplayCommand.onAddCmdToApp(self)
        if not self.app().commands.has_key('displayBackboneTrace'):
            self.app().lazyLoad('displayCmds', commands=['displayBackboneTrace'],
                                package='PmvApp')


    def checkArguments(self, nodes, **kw):
        """None <- undisplayBackboneTrace(nodes, **kw)
        nodes: TreeNodeSet holding the current selection"""
        
        kw['negate']=1
        return self.app().displayBackboneTrace.checkArguments(nodes, **kw)
 

    def doit(self, nodes, **kw):
        self.app().displayBackboneTrace(nodes, **kw)


BHTree_CUT = 40.0

class BindGeomToMolecularFragmentBase( MVCommand):
    data = {}   # data will be shared between all instances of the class



class BindGeomToMolecularFragment(BindGeomToMolecularFragmentBase):
    """Command to bind an Indexed Geometry to a molecule."""    

    def __init__(self):
        MVCommand.__init__(self)
        self.isDisplayed=0
        self.objects = {}

    def checkDependencies(self, vf):
        from bhtree import bhtreelib
        

    def doit(self, g, nodes, cutoff_from=3.5, cutoff_to=BHTree_CUT,
             instanceMatrices=None):
        mols = nodes.top.uniq()
        mol = mols[0]
        cl_atoms = []
        geomC = mol.geomContainer

        reparent = True
        # check if geom g is already under the molecule's hierarchy of
        # DejaVu2 Objects

        obj = g
        while obj.parent:
            if g.parent==geomC.masterGeom:
                reparent=False
                break
            obj = obj.parent

        try:
            atoms = nodes.findType(Atom)
            gname = g.name
            vs = g.vertexSet.vertices.array
            if isinstance(g, IndexedGeom):
                fs = g.faceSet.faces.array
                fns = g.getFNormals()
            else:
                fs = fns = None
            #print "in doit: lenvs:", len(vs)
            cl_atoms = self.findClosestAtoms(vs, atoms, cutoff_from, cutoff_to, instanceMatrices)
            if len(cl_atoms):
                if hasattr(g, 'mol') and g.mol()==mol:
                    # we are binding to a new molecule
                    for a in g.mol().allAtoms:
                        del a.colors[gname]
                        del a.opacities[gname]
                if g.parent==None:   #add geometry to Viewer:
                    geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
                    reparent = False
                if reparent: # need to reparent geometry
                    vi= geomC.VIEWER
                    if vi:
                        vi.ReparentObject(g, geomC.masterGeom)
                    else:
                        oldparent = g.parent
                        oldparent.children.remove(g)
                        geomC.masterGeom.children.append(g)
                        g.parent = geomC.masterGeom
                    g.fullName = g.parent.fullName+'|'+gname
                geomC.atomPropToVertices[gname] = self.atomPropToVertices
                geomC.geomPickToAtoms[gname] = self.pickedVerticesToAtoms
                geomC.geomPickToBonds[gname] = None
                
                for a in mol.allAtoms:
                    a.colors[gname] = (1.,1.,1.)
                    a.opacities[gname] = 1.0

                g.userName = gname
                geomC.geoms[gname] = g
                import weakref
                g.mol = weakref.ref(mol)
                u_atoms = self.findUniqueAtomSet(cl_atoms, atoms )
                geomC.setAtomsForGeom(gname, u_atoms)
                #self.cl_atoms[gname] = cl_atoms
                #create a unique identifier for all atoms
                ids = [x.name+str(i) for i,x in enumerate(atoms)]
                atoms.sl_id = ids
                mol_lookup = dict(zip(ids, range(len(ids))))

                # highlight selection
                lAtomVerticesDict = {}
                for lIndex in range(len(cl_atoms)):
                    lAtomVerticesDict[atoms[cl_atoms[lIndex]]]=[]
                for lIndex in range(len(cl_atoms)):
                    lAtomVerticesDict[atoms[cl_atoms[lIndex]]].append(lIndex)

                self.data[g.fullName]={'cl_atoms':cl_atoms, 'fs':fs, 'fns':fns,
                                       'mol_lookup':mol_lookup, 'atoms':atoms,
                                       'atomVertices':lAtomVerticesDict}
                #print self.data[g.fullName]['atoms']
                self.app()._executionReport.addSuccess('displayed lines for molecule %s successfully'% mol.name, obj=atoms)
            else:
                raise RuntimeError("%s: no close atoms found for geometry: %s" % (self.name, g.name))
        
        except:
            msg = 'Error in binding geometry %s to molecule %s'%(g.name, mol.name)
            self.app().errorMsg(sys.exc_info(), msg, obj=atoms)                       

        return cl_atoms

            
    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert picked vertices into atoms"""
        
        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet
        mol = geom.mol()
        l = []
        #atom_inds = self.cl_atoms[geom.name]
        atom_inds = self.data[geom.fullName]['cl_atoms']
        #atoms = mol.allAtoms
        atoms  = self.data[geom.fullName]['atoms']
        for ind in vertInd:
            l.append(atoms[atom_inds[ind]])
        return AtomSet( AtomSet( l ) )


    def findUniqueAtomSet(self, atomIndices, atoms ):
        #atoms - array of indices of closest atoms
        #print "findUniqueAtomSet", "atomIndices", len(atomIndices), "atoms:", len(atoms)
        l = []

        natoms = len(atoms)
        maxind = max(atomIndices)
        #print "maxind:", maxind
        seen = {}
#        for i in range(maxind+1):
#            if i in atomIndices:
        for i in atomIndices:
            if not seen.has_key(i):
                l.append(atoms[i])
                seen[i] = 1
        atomset = AtomSet( l )
        #print len(atomset)
        return atomset


    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        """Function called to map atomic properties to the vertices of the
        geometry"""
        
        if len(atoms)==0: return None
        #print "len atoms:", len(atoms)
        #print "propIndex:", propIndex
        #for a in atoms.data:
        #    print a.__dict__['number'],
        #print 
        # array of propperties of all atoms for the geometry.
        prop = []
        atoms = self.data[geom.fullName]['atoms']
        if propIndex is not None:
            for a in atoms:
                d = getattr(a, propName)
                prop.append( d[propIndex] )
        else:
            for a in atoms:
                prop.append( getattr(a, propName) )
        #atind = self.cl_atoms[geom.name]
        atind = self.data[geom.fullName]['cl_atoms']

        # get lookup col using closest atom indicies
        mappedProp = numpy.take(prop, atind, axis=0 ).astype('f')
        import numpy.oldnumeric as Numeric
        mappedProp1 = Numeric.take(prop, atind).astype('f')
        print mappedProp.shape, mappedProp1.shape
        return mappedProp


    def checkArguments(self, geom, nodes, cutoff_from=3.5, cutoff_to=BHTree_CUT,
                       instanceMatrices=None):
       
        """
        Finds the closest atom to each vertex of a given indexed geometry.
        Binds the geometry to the molecule.
        geom --- an input Geom object;
        molname --- the name of an input molecule;
        cutoff_from --- the initial distance from vertices in which the search\n
                        for the closest atoms is performed. If no atoms are found,\n
                        the search distance is gradually increased untill it reaches\n
                        the 'cutoff_to' value."""
        
        nodes = self.app().expandNodes(nodes)

        mols = nodes.top.uniq()
        if len(mols) > 1:
            raise RuntimeError("bindGeomToMolecularFragment: ERROR: atoms belong to more than one molecule")
        #if isinstance(geom , str):
        #    geom = self.app().GUI.VIEWER.FindObjectByName(geom)
        assert isinstance (geom, Geom)
        assert isinstance(cutoff_from, (int, float))
        assert isinstance(cutoff_to, (int, float))
        kw = {"cutoff_from":cutoff_from, "cutoff_to":cutoff_to,
              "instanceMatrices": instanceMatrices}
        
        return (geom, nodes), kw
        

        
    def findClosestAtoms(self, obj_verts,  atoms,
                         cutoff_from=3.5, cutoff_to=BHTree_CUT,instanceMatrices=None ):
        """For every vertex in a given set of vertices finds the closest atom.
        Returns an array of corresponding atom indices. Based on bhtree
        library. """
        if not len(obj_verts):
            return []
        from bhtree import bhtreelib
        atom_coords = atoms.coords
        natoms = len(atom_coords)
        if instanceMatrices:
            coordv = numpy.ones(natoms *4, "f")
            coordv.shape = (natoms, 4)
            coordv[:,:3] = atom_coords[:]
            new_coords = []
            for m in instanceMatrices:
                new_coords.append(numpy.dot(coordv, \
                                   numpy.transpose(m))[:, :3])
            atom_coords = numpy.concatenate(new_coords)
        print "len atom_coords: ", len(atom_coords)
        bht = bhtreelib.BHtree( atom_coords, None, 10)
        cl_atoms = []
        mdist = cutoff_from
        print "** Bind Geometry to Molecule Info: **"
        print "** looking for closest atoms (cutoff range: %2f-%2f)...   **"%(cutoff_from, cutoff_to)
        cl_atoms = bht.closestPointsArray(obj_verts, mdist)
        while len(cl_atoms) == 0 and mdist <cutoff_to:
            print "** ... no closest atoms found for cutoff = %2f; continue looking ... **"%mdist
            mdist=mdist+0.2
            cl_atoms = bht.closestPointsArray(obj_verts, mdist)
            #print "mdist: ", mdist, "  len cl_atoms: ", len(cl_atoms)
        print "**... done. %d closest atoms found within distance: %2f **"%(len(cl_atoms) , mdist)
        if instanceMatrices:
            if cl_atoms:
                return [x%natoms for x in cl_atoms]
        return cl_atoms


    
from PmvApp.Pmv import numOfSelectedVerticesToSelectTriangle

class DisplayBoundGeom(DisplayCommand, BindGeomToMolecularFragmentBase):
    """Command to display/undisplay geometries that were bound to molecules with
    'bindGeomToMolecularFragment' command. """
    
    def checkDependencies(self, vf):
        from bhtree import bhtreelib


    def doit(self, nodes, geomNames=None, only=0, negate=0, nbVert=3, redraw=True):
        #print "nbVert: ", nbVert
        #print "geomNames:", geomNames
        if not geomNames:
            return
        molecules, atomSets = self.app().getNodesByMolecule(nodes, Atom)
        if not molecules: return
        # get all objects(geometries) that were bound with  'bindGeomToMolecularFragment' command:
        for mol, atm  in map(None,molecules,atomSets):
            try:
                # find geoms that were bound to molecule mol:
                allatoms = mol.allAtoms
                for obj in geomNames:
                    oname = obj.split('|')[-1]
                    # get the set of atoms for the geometry
                    _set = mol.geomContainer.atoms[oname]

                    #if negate, remove current atms from displayed _set
                    if negate: _set = _set - atm

                    #if only, replace displayed _set with current atms 
                    else:
                        if only: _set = atm
                        else: 
                            _set = atm.union(_set)
                    mol.geomContainer.setAtomsForGeom(oname, _set)
                    g = mol.geomContainer.geoms[oname]
                    if len(_set) == 0:
                        g.Set(visible=0, tagModified=False)
                        return
                    # get the atom indices
                    atomindices = []
                    cl_atoms = self.data[obj]['cl_atoms']
                    vs = []
                    mol_lookup = self.data[obj]['mol_lookup']
                    for a in _set:
                        if hasattr(a, "sl_id"):
                            ind = mol_lookup[a.sl_id]
                            atomindices.append(ind)
                    cond = [x in atomindices for x in cl_atoms]
                    #a new subset of vertex indices:
                    nvs = numpy.nonzero(cond)[0] #returns indices of cond,
                                                #where its elements != 0

                    #print "atom inds to display: " , nvs
                    faces = self.data[obj]['fs']
                    norms = self.data[obj]['fns']
                    s = faces.shape
                    ####################################
##                      fs_lookup = numpy.zeros(s, 'i')
##                      for i in range(s[0]):
##                          for j in range(s[1]):
##                              f=faces[i][j]
##                              if f != -1:
##                                  if f in nvs:
##                                      fs_lookup[i][j] = 1
##                      vs_per_face = numpy.sum(fs_lookup, 1)
##                      cond = numpy.greater_equal(vs_per_face, nbVert)
##                      nfs_ind = numpy.nonzero(cond)
##                      print "len(nfs_ind):", len(nfs_ind)
##                      nfs = numpy.take(faces, nfs_ind)
                    #####################
                    # find a subset of faces and face normals:
                    from bhtree import bhtreelib
                    from time import time
                    t1=time()
                    nvs = nvs.astype('i')
                    nfs_ind = bhtreelib.findFaceSubset(nvs, faces, nbVert)#indices of
                                                                          #subset of faces
                    nfs = numpy.take(faces, nfs_ind, axis=0)
                    nfns = numpy.take(norms, nfs_ind, axis=0)
                    t2=time()
                    #print "time to loop: ", t2-t1
                    #print "nfs.shape: ", nfs.shape
                    if len(atomindices)==0:
                        g.Set(visible=0, tagModified=False)
                    else:
                        col = mol.geomContainer.getGeomColor(oname)
                        g.Set(faces=nfs, fnormals = nfns, materials=col,
                              inheritMaterial=False, visible=1, tagModified=False)
                        if g.transparent:
                            opac = mol.geomContainer.getGeomOpacity(oname)
                            g.Set( opacity=opac, redo=0, tagModified=False)

                        # update texture coordinate if needed
                        if g.texture and g.texture.enabled and g.texture.auto==0:
                            mol.geomContainer.updateTexCoords[o](mol)
                
                self.app()._executionReport.addSuccess('displayed bound geometry for molecule %s successfully'%
                    mol.name, obj=atm)
            except:
                msg = 'Error while displaying bound geometry for molecule %s'%mol.name
                self.app().errorMsg(sys.exc_info(), msg, obj=atm)


    def checkArguments(self, nodes, only=0, negate=0, geomNames=None,
                       nbVert=numOfSelectedVerticesToSelectTriangle, redraw=True):
        """
           nodes  : TreeNodeSet holding the current selection
           only   : flag when set to 1 only the current selection will be
                    displayed
           negate : flag when set to 1 undisplay the current selection
           nbVert : number of vertices per triangle needed to select a triangle"""

        if isinstance (nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.app().expandNodes(nodes)

        assert only in [True, False, 0, 1]
        assert negate in [True, False, 0, 1]
        assert isinstance(nbVert, int)
        if geomNames is not None:
            assert isinstance (geomNames, (list, tuple))
        kw = {}
        kw['only'] = only
        kw['negate'] = negate
        kw['nbVert'] = nbVert
        kw['geomNames'] = geomNames
        kw['redraw'] = redraw 
        return (nodes,), kw



class UndisplayBoundGeom(DisplayBoundGeom):
    
    def checkArguments(self, nodes, **kw):
        """None <- undisplayBoundGeom(nodes, **kw)
           nodes  : TreeNodeSet holding the current selection (mv.activeSelection.get())
           """
        kw['negate']= 1
        return self.app().displayBoundGeom.checkArguments(nodes, **kw)

    
    def doit(self, nodes, **kw):
        kw['negate']= 1
        return self.app().displayBoundGeom(nodes, **kw)



class ShowMolecules(MVCommand):
    """The showMolecules command allows the user to show or hide chosen molecules. \n
    Package : PmvApp \n
    Module  : displayCmds \n
    Class   : ShowMolecules \n
    Command : showMolecules \n
    Synopsis:\n
        None <--- showMolecules(molName, negate = 0, **kw)\n
        molName --- list of the string representing the name of the molecules to be hidden or shown\n
        negate --- Boolean Flag when True the molecules corresponding to the given names are hidden, when set to 0 they will be shown\n
        keywords --- show hide molecules\n
    Events: generates ShowMoleculesEvent
    """

    def __init__(self):
        MVCommand.__init__(self)

        #self.flag = self.flag | self.negateKw
        self.callbacks=[]


    def addCallback(self, f, event=None):
        """add a callback function to be called when the visibility 
        flag of a molecule is toggled. The function is called after the flag
        has been toggled and takes one argument which is the molecule"""
        assert callable(f)
        self.callbacks.append(f)


    def removeCallback(self, f, event=None):
        """remove a callback function called when the visibility 
        flag of a molecule is toggled. """
        self.callbacks.remove(f)


    def onRemoveObjectFromViewer(self, obj):
        if hasattr(obj, 'displayMode'):
            delattr(obj, 'displayMode')


    def onAddObjectToViewer(self, obj):
        self.objectState[obj] = {'onAddObjectCalled':True}


    def doit(self, molName, negate=False):
        if not isinstance(molName ,(tuple, list)):
            return
        mols = []
        for name in molName:
            mol = self.app().Mols.NodesFromName(name)[0]
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            mol.geomContainer.geoms['master'].Set(visible = not negate,
                                                  tagModified=False)
            mols.append(mol)
            # ????
            for f in self.callbacks:
                f(mol)
        if self.createEvents and len(mols):
            event = ShowMoleculesEvent( mols, visible = not negate)
            self.app().eventHandler.dispatchEvent(event)


    def checkArguments(self, molName, negate=False):
        """None <- showMolecules(molName, negate=0) \n
           molName : list of string name of molecules (mol.name) \n
           negate  : flag when set to 1 hide the given molecule
        """
        from MolKit.tree import TreeNode, TreeNodeSet
        if molName == 'all':
            molName = self.app().Mols.name
        elif isinstance(molName, TreeNode):
            molName = [molName.top.name]
        elif isinstance(molName, TreeNodeSet):
            molName = molName.top.uniq().name
        # can not do "assert molName"  here,
        # it will fail when molName is  <MoleculeSetNoSelection instance> empty
        # (show molecule from "All Molecules" menu in the dashboard)  
        # In this case doit has to return 
        assert negate in [True, False, 1, 0]
        kw = {'negate':negate}
        return (molName,), kw



commandClassFromName = {
    'displayLines' : [DisplayLines, None],
    'undisplayLines' : [UndisplayLines,  None],
    'displayCPK': [DisplayCPK, None],
    'undisplayCPK' : [UndisplayCPK,  None],
    'displaySticksAndBalls': [DisplaySticksAndBalls, None],
    'undisplaySticksAndBalls' : [UndisplaySticksAndBalls, None],
    
    'displayBackboneTrace' : [DisplayBackboneTrace, None],
    'undisplayBackboneTrace': [UndisplayBackboneTrace, None],
    'displayBoundGeom': [DisplayBoundGeom, None],
    'undisplayBoundGeom': [UndisplayBoundGeom, None],
    'bindGeomToMolecularFragment': [BindGeomToMolecularFragment, None],
    'showMolecules' : [ShowMolecules, None],
    }


def initModule(viewer, gui=True):
    for cmdName, values in commandClassFromName.items():
        cmdClass, guiInstance = values
        viewer.addCommand(cmdClass(), cmdName, guiInstance)

