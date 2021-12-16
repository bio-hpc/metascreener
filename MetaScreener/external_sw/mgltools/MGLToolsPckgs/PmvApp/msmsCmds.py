#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/msmsCmds.py,v 1.7 2014/07/18 22:59:06 annao Exp $
# 
# $Id: msmsCmds.py,v 1.7 2014/07/18 22:59:06 annao Exp $
#

import numpy
import os, sys
from MolKit.molecule import Atom, AtomSet

from DejaVu2.IndexedPolygons import IndexedPolygons

from PmvApp.displayCmds import DisplayCommand
from PmvApp.Pmv import MVCommand  #MVAtomICOM
from PmvApp.msmsParser import MSMSParser

from PmvApp.Pmv import DeleteGeomsEvent, AddGeomsEvent,\
     EditGeomsEvent, DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent,\
     AfterDeleteAtomsEvent
from PmvApp import Pmv

if not  hasattr( Pmv, 'numOfSelectedVerticesToSelectTriangle'):
    Pmv.numOfSelectedVerticesToSelectTriangle = 1
    Pmv.app().userpref.add('Sharp Color Boundaries for MSMS', 'yes', ('yes','no'),
                  doc="""specifie color boundaries for msms surface (blur or sharp)""",
                 )


class ComputeMSMS(MVCommand): #, MVAtomICOM):
    """The computeMSMS command will compute a triangulated solvent excluded surface for the current selection.\n
    Package : PmvApp\n
    Module  : msmsCmds\n
    Class   : ComputeMSMS\n
    Command name : computeMSMS\n
    \nSynopsis :\n
    None <--- mv.computeMSMS(nodes, surfName=None, pRadius=1.5,
                           density=1.0, perMol=True, noHetatm=False,
                           display=1)\n
    \nRequired Arguments :\n
        nodes --- current selection\n
    \nOptional Arguments:\n
    surfName --- name of the surfname which will be used as the key in
                mol.geomContainer.msms dictionary. If the surfName is
                already a key of the msms dictionary the surface is
                recreated. By default mol.name is MSMS\n
    pRadius  --- probe radius (1.5)\n
    density --- triangle density to represent the surface (1.0)\n
    perMol  --- when this flag is True a surface is computed for each molecule
                having at least one node in the current selection,
                else the surface is computed for the current selection.
                (default True)\n
    noHetatm --- when this flag is True hetero atoms are ignored, unless
                 all atoms are HETATM\n
    display ---  when set to True the displayMSMS will be executed to
                display the new msms surface.\n
                    
    """

    ###
    ###COMMAND METHODS
    ###
    def __init__(self):
        MVCommand.__init__(self)
        #MVAtomICOM.__init__(self)
        #self.flag = self.flag | self.objArgOnly


    def checkDependencies(self, vf):
        import mslib


    def onAddCmdToApp(self):
        if not self.app().commands.has_key('assignAtomsRadii'):
            self.app().lazyLoad('editCmds', commands=['assignAtomsRadii',],
                             package='PmvApp')

    def onAddObjectToViewer(self, obj):
        """
        """
        self.objectState[obj] = {'onAddObjectCalled':True}
        geomC = obj.geomContainer
        geomC.nbSurf = 0
        geomC.msms = {}
        geomC.msmsAtoms = {} # AtomSets used to compute the surfaces
        geomC.msmsCurrentDisplay = {} # Dictionary whose keys are 'surfaceNames'
                                      # and whose values are strings
                                      # to be used to undo either 'displayMSMS'
                                      # or 'displayBuriedTriangles', restoring
                                      # the geometry 'surfaceName' to its
                                      # previous state. This dictionary is 
                                      # necessary because these two different commands 
                                      # can effect changes to the same geometry,
                                      # thus making the undo dependent on the
                                      # command sequence....
                                      # 1. displayMSMS followed by displayMSMS is
                                      # simplest to undo: invoke the second displayMSMS 
                                      # cmd with negate flag on
                                      # 2. displayMSMS followed by displayBuriedTriangles
                                      # requires displayMSMS with
                                      # geomContainer.atoms['surfaceName']
                                      # 3. displayBuriedTriangles followed by displayMSMS 
                                      #  AND
                                      # 4. displayBuriedTriangles followed by displayBuriedTriangles
                                      # requires geom.Set(faces=currentFaces) 
                                      # NOTE: correctly updating msmsCurrentDisplay needs testing

    def onRemoveObjectFromViewer(self, obj):
        if self.objectState.has_key(obj):
            self.objectState.pop(obj)

    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        """Function called to map atomic properties to the vertices of the
        geometry"""
        if len(atoms)==0: return None
        mol = geom.mol()
        geomC = mol.geomContainer
        surfName = geom.userName
        surf = geomC.msms[surfName][0]
        surfNum = geomC.msms[surfName][1]
        # array of colors of all atoms for the msms.
        prop = []
        if propIndex is not None:
            for a in geomC.msmsAtoms[surfName].data:
                d = getattr(a, propName) # a is an atom, propName is colors
                # d is atom.colors from which we get the entry surfName
                prop.append( d.get(surfName, d['lines']) )
                #if not d.has_key(surfName): d[surfName] = d['lines']
        else:
            for a in geomC.msmsAtoms[surfName].data:
                prop.append( getattr(a, propName) )
        # find indices of atoms with surface displayed
        atomIndices = []
        indName = '__surfIndex%d__'%surfNum
        for a in atoms.data:
            atomIndices.append(getattr(a, indName))
        # get the indices of closest atoms
        dum1, vi, dum2 = surf.getTriangles(atomIndices, keepOriginalIndices=1)
        # get lookup col using closest atom indicies
        mappedProp = numpy.take(prop, vi[:, 1]-1, axis=0).astype('f')
        if hasattr(geom,'apbs_colors'):
            colors = []
            for i in range(len(geom.apbs_dum1)):
                ch = geom.apbs_dum1[i] == dum1[0]
                if not 0 in ch:
                    tmp_prop = mappedProp[0]
                    mappedProp = mappedProp[1:]
                    dum1 = dum1[1:]
                    if    (tmp_prop[0] == [1.5]) \
                      and (tmp_prop[1] == [1.5]) \
                      and (tmp_prop[2] == [1.5]):
                        colors.append(geom.apbs_colors[i][:3])
                    else:
                        colors.append(tmp_prop)
                    if dum1 is None:
                        break
            mappedProp = colors            
        return mappedProp


    def pickedVerticesToBonds(self, geom, parts, vertex):
        return None


    def pickedVerticesToAtoms(self, geom, vertInd):
        """Function called to convert picked vertices into atoms"""

        # this function gets called when a picking or drag select event has
        # happened. It gets called with a geometry and the list of vertex
        # indices of that geometry that have been selected.
        # This function is in charge of turning these indices into an AtomSet

        surfName = geom.userName
        mol = geom.mol()
        geomC = mol.geomContainer
        surfNum = geomC.msms[surfName][1]
        indName = '__surfIndex%d__'%surfNum
       
        #FIXME: building atomindices is done in DisplayMSMS
        # should re-use it

        atomindices = []
        indName = '__surfIndex%d__'%surfNum
        al = mol.geomContainer.atoms[surfName]
        for a in al:
            atomindices.append(getattr(a, indName))

        surf = geomC.msms[surfName][0]
        dum1, vi, dum2 = surf.getTriangles(atomindices, keepOriginalIndices=1)

        l = []
        allAt = geomC.msmsAtoms[surfName]
        for i in vertInd:
            l.append(allAt[vi[i][1]-1])
        return AtomSet( AtomSet( l ) )


    def checkArguments(self, nodes, surfName='MSMS-MOL', pRadius=1.5,
                 density=3.0, perMol=True, noHetatm=False, display=True,
                 hdset=None, hdensity=6.0, redraw=True):
        """
        Required Arguments :\n
        nodes ---  atomic fragment (string or objects)\n
        Optional Arguments :\n
        surfName --- name of the surfname which will be used as the key in
                     mol.geomContainer.msms dictionary. If the surfName is
                     already a key of the msms dictionary the surface is
                     recomputed. (default MSMS-MOL)\n
        pRadius  --- probe radius (1.5)\n
        density  --- triangle density to represent the surface. (1.0)\n
        perMol   --- when this flag is True a surface is computed for each 
                     molecule having at least one node in the current selection
                     else the surface is computed for the current selection.
                     (True)\n
        noHetatm --- when this flag is True hetero atoms are ignored, unless
                     all atoms are HETATM.\n
        display  --- flag when set to 1 the displayMSMS will be executed with
                     the surfName else not.\n
        hdset    --- Atom set (or name) for which high density triangualtion will
                     be generated
        hdensity --- vertex density for high density
        """
        nodes = self.app().expandNodes(nodes)

        assert isinstance(surfName, str)
        assert isinstance(pRadius, (int, float))
        assert pRadius > 0
        assert isinstance(density, (int, float))
        assert isinstance(hdensity, (int, float))
        assert display in [True, False, 1, 0]
        assert perMol in [True, False, 1, 0]
        assert noHetatm in [True, False, 1, 0]
        if hdset != None:
            #print "hdset:", hdset
            if isinstance(hdset, (tuple, list)):
                hdset = hdset[0]
            assert isinstance(hdset, str)
        kw = {}
        kw['surfName'] = surfName
        kw['pRadius'] = pRadius
        kw['density'] = density
        kw['perMol'] = perMol
        kw['noHetatm'] = noHetatm
        kw['display'] = display
        kw['hdset'] = hdset
        kw['hdensity'] = hdensity
        kw['redraw'] = redraw
        if isinstance (nodes, str):
            self.nodeLogString = "'" + nodes +"'"
        return (nodes,), kw
            

    def doit(self, nodes, surfName='MSMS-MOL', pRadius=1.5, density=1.0,
             perMol=True, noHetatm=False, display=True, hdset=None,
	     hdensity=6.0, redraw=True):
        """Required Arguments:\n        
        nodes   ---  current selection\n
        surfName --- name of the surfname which will be used as the key in
                    mol.geomContainer.msms dictionary.\n
        \nOptional Arguments:  \n      
        pRadius  --- probe radius (1.5)\n
        density  --- triangle density to represent the surface. (1.0)\n
        perMol   --- when this flag is True a surface is computed for each 
                    molecule having at least one node in the current selection
                    else the surface is computed for the current selection.
                    (True)\n
        noHetatm --- when this flag is True hetero atoms are ignored, unless
                 all atoms are HETATM.\n
        display  --- flag when set to True the displayMSMS will be executed with
                    the surfName else not.\n
        hdset    --- Atom set for which high density triangualtion 
                     will be generated
        hdensity --- vertex density for high density
        """
        from mslib import MSMS
        if hdset:
            if self.app().sets.has_key(hdset):
                hdset = self.app().sets[hdset].findType(Atom)
                for a in hdset:
                    a.highDensity = True
            else:
                self.app().warningMsg("set %s not found"%hdset)
                hdset = None

        # get the set of molecules and the set of atoms per molecule in the
        # current selection
        if perMol:
            molecules = nodes.top.uniq()
            atmSets = [x.allAtoms for x in molecules]
        else:
            molecules, atmSets = self.app().getNodesByMolecule(nodes, Atom)

        for mol, atms in map(None, molecules, atmSets):
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
            if self.app().commands.has_key('dashboard'):
                self.app().dashboard.resetColPercent(
                    mol, '_showMSMSStatus_%s'%surfName)
            try:  
                if noHetatm:
                    ats = [x for x in atms if not x.hetatm]
                    if len(ats)==0:
                        ats = atms
                    atms = AtomSet(ats)

                if not surfName:
                    surfName = mol.name + '-MSMS'
                geomC = mol.geomContainer

                if not geomC.msms.has_key(surfName):
                    # Create a new geometry
                    # be stored.
                    g = IndexedPolygons(surfName, pickableVertices=1, protected=True,)
                    if self.app().userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                        g.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False,)
                    g.userName = surfName
                    geomC.addGeom(g)
                    self.managedGeometries.append(g)
                    geomC.geomPickToAtoms[surfName] = self.pickedVerticesToAtoms
                    geomC.geomPickToBonds[surfName] = None
                    # This needs to be replaced by string to not have a direct
                    # dependency between PMV and OPENGL...
                    #g.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
                    #g.Set(frontPolyMode=GL.GL_FILL, redo=0)
                    # g.RenderMode('GL_FILL', face='GL_FRONT', redo=0)
                    geomC.atomPropToVertices[surfName] = self.atomPropToVertices
                    # Create the key for this msms for each a.colors dictionary.
                    #for a in mol.allAtoms:
                    #    a.colors[surfName] = (1.,1.,1.)
                    #    a.opacities[surfName] = 1.0
                    # Created a new geometry needs to update the form if exists.
                    #if self.cmdForms.has_key('default'):
                    #    self.updateForm(surfName)

                # update the existing geometry
                geomC.msmsAtoms[surfName] = atms[:]
                geomC.setAtomsForGeom(surfName, AtomSet([]))

                i=0  # atom indices are 1-based in msms
                indName = '__surfIndex%d__'%geomC.nbSurf
                hd = []
                surf = []
                for a in atms:
                    setattr(a, indName, i)
                    i = i + 1
                    surf.append(1)
                    if hasattr(a, 'highDensity'):
                        hd.append(1)
                    else:
                        hd.append(0)

                # get atm radii if necessary
                try:
                    atmRadii = atms.radius
                except AttributeError:
                    self.app().assignAtomsRadii(mol, united=0)
                    atmRadii = atms.radius

                # build an MSMS object and compute the surface
                srf = MSMS(coords=atms.coords, radii=atmRadii, surfflags=surf,
                           hdflags=hd)
                srf.compute(probe_radius=pRadius, density=density,
                            hdensity=hdensity)

                # save computation parameters inside srf
                srf.probeRadius = pRadius
                srf.density = density
                srf.perMol = perMol
                srf.surfName = surfName
                srf.noHetatm = noHetatm
                srf.hdset = hdset
                srf.hdensity = hdensity

                if mol.geomContainer.msms.has_key(surfName):
                    #print "freeing MSMSC %s"%surfName
                    oldsrf = mol.geomContainer.msms[surfName][0]
                    del oldsrf

                # save a pointer to the MSMS object
                mol.geomContainer.msms[surfName] = (srf, geomC.nbSurf)
                # Increment the nbSurf counter
                geomC.nbSurf += 1
                self.app()._executionReport.addSuccess('computed surface for molecule %s successfully'%
                    mol.name, obj=atms)
            except:
                msg = 'Error while computing surface for molecule %s'%mol.name
                self.app().errorMsg(sys.exc_info(), msg, obj=mol)

        if hdset:
            for a in hdset:
                del a.highDensity

        if display:
            if not self.app().commands.has_key('displayMSMS'):
                self.app().lazyLoad("msmsCmds", commands=['displayMSMS',],
                                 package='PmvApp')
            if nodes.stringRepr is not None:
                geomC.msmsCurrentDisplay[surfName] = \
                    "self.displayMSMS('%s', surfName=['%s'], negate=0, only=0, nbVert=%d)" %(nodes.stringRepr, surfName, Pmv.numOfSelectedVerticesToSelectTriangle) 
            else:
                geomC.msmsCurrentDisplay[surfName] = \
                    "self.displayMSMS('%s', surfName=['%s'], negate=0, only=0, nbVert=%d)" %(nodes.full_name(), surfName, Pmv.numOfSelectedVerticesToSelectTriangle)            

            self.app().displayMSMS(nodes, surfName=[surfName,], negate=0, only=1,
                                      nbVert=Pmv.numOfSelectedVerticesToSelectTriangle)
                
            
        event = EditGeomsEvent('msms_c', [nodes,[surfName, pRadius, density,
						perMol, display, hdset, hdensity]])
        self.app().eventHandler.dispatchEvent(event)



    ###
    ### HELPER METHODS
    ###
    def setTexCoords(self, mol, values):
        srf = mol.geomContainer.msms
        lookup = mol.geomContainer.texCoordsLookup["msms"]
        g = mol.geomContainer.geoms['msms']
        if g.texture:
            g.texture.auto=0
        if srf:
            vf, vi, f = srf.getTriangles()
            values.shape = (-1,1)
            assert len(values)==len(vf)
            i = 0
            for v in vf:
                lookup[str(v[0])+str(v[1])+str(v[2])] = values[i]
                i = i + 1
        self.updateTexCoords(mol)
        
                
    def updateTexCoords(self, mol):
        lookup = mol.geomContainer.texCoordsLookup["msms"]
        g = mol.geomContainer.geoms['msms']
        tx = [lookup[str(v[0])+str(v[1])+str(v[2])] for v in g.vertexSet.vertices.array]
        tx = numpy.array(tx)
        tx.shape = (-1,1)
        g.Set( textureCoords=tx, tagModified=False )


    def fixValues(self, val):
        if val['hdset'] is None:
            return val
        if val['hdset'] == 'None':
            val['hdset'] = None
            return val
        hdsetName = val['hdset'][0]
        if hdsetName=='None' or hdsetName=='':
            val['hdset'] = None
        return val



class DisplayMSMS(DisplayCommand):
    """The displayMSMS command allows the user to display/undisplay or display only the given MSMS surface corresponding to the current selection.\n
    Package : PmvApp\n
    Module  : msmsCmds\n
    Class   : DisplayMSMS\n
    Command name : displayMSMS\n
    Required Arguments:\n
    nodes  --- TreeNodeSet holding the current selection\n
    Optional Arguments:\n
    only     --- flag when set to 1 only the current selection will be
              displayed\n
    negate   --- flag when set to 1 undisplay the current selection\n
    surfName --- name of the selection, default = 'all'\n
    nbVert  ---  number of vertices per triangle needed to select a triangle.\n
    
    """

    def onAddCmdToApp(self):
        self.app().eventHandler.registerListener(AfterDeleteAtomsEvent, self.handleDeleteAtoms)
        self.app().eventHandler.registerListener(EditAtomsEvent, self.handleEditEvent)
        #self.app().eventHandler.registerListener(AddAtomsEvent, self.updateGeom)


    def handleDeleteAtoms(self, event):
        """Function to update geometry objects created by this command
        upon atom deletion.\n
        event --- instance of a VFEvent object
"""
        # split event.objects into atoms sets per molecule
        molecules, ats = self.app().getNodesByMolecule(event.objects)

        # loop over molecules to update geometry objects
        for mol, atomSet in zip(molecules, ats):
            geomC = mol.geomContainer
            if not hasattr(geomC, "msms"): continue
            for srfName, srfc in geomC.msms.items():
                ats = geomC.atoms[srfName]
                srf = srfc[0]
                if len(ats & atomSet): #deleted atoms are in this surface
                    
                    newAts = ats-atomSet
                    kw = {}
                    kw['surfName'] = srfName
                    kw['pRadius'] = srf.probeRadius
                    kw['density'] = srf.density
                    kw['perMol'] = srf.perMol
                    kw['noHetatm'] = srf.noHetatm
                    kw['hdset'] = srf.hdset
                    kw['hdensity'] = srf.hdensity
                    kw['display'] = 1
                    
                    del srf # free old C structure
                    #print 'recompute MSMS', len(newAts), kw
                    self.app().computeMSMS( newAts, **kw)


    def handleEditEvent(self, event):
        from mslib import msms

        # build list of optional command arguments
        doitoptions = self.lastUsedValues['default']
        doitoptions['redraw']=1

        molecules, atomSets = self.app().getNodesByMolecule(event.objects, Atom)
        for mol, atoms in zip(molecules, atomSets):
            geomC = mol.geomContainer
            if not hasattr(geomC, 'msms'): continue
            # loop over all surfaces
            for name in geomC.msms.keys():
                g = geomC.geoms[name]

                # get the atom indices
                surfc = geomC.msms[name][0]
                surfNum = geomC.msms[name][1]
                indName = '__surfIndex%d__'%surfNum
                atomindices = []
                coords = []
                for a in atoms:
                    atomindices.append(a.__dict__[indName])
                    coords.append( list(a.coords)+[a.radius] )
                        
                msms.MS_reset_atom_update_flag(surfc)
                i = msms.MS_updateSpheres(surfc, len(atoms), atomindices,
                                          coords)
                rs = surfc.rsr.fst
                # this would only be needed once initially
                msms.MS_tagCloseProbes(surfc, rs, 15.0)
                mode = 0
                density = surfc.density
                updateNum = 1
                i = msms.MS_update_surface(surfc, rs, mode, density, updateNum)
                if i==msms.MS_ERR:
                    print "ERROR while updating RS %d %s\n"%(updateNum, "Error")#msms.MS_err_msg) MS_err_msg not exposed
                    return
                #msms.MS_update_SES_area(surfc, rs.ses)
                vf, vi, f = surfc.getTriangles()
                col = mol.geomContainer.getGeomColor(name)

                g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6],
                       faces=f[:,:3], materials=col, inheritMaterial=False, 
                       tagModified=False )


# setupUndoBefore is no longer used. Use negateCmdBefore() instead. 

##     def setupUndoBefore(self, nodes, surfName='all', negate=False, only=False, nbVert=1):
##         molecules, atomSets = self.app().getNodesByMolecule(nodes, Atom)
##         for mol, atoms in map(None, molecules, atomSets):
##             geomC = mol.geomContainer
##             surfNames = geomC.msms.keys()
##             if surfName == 'all':
##                 names = surfNames
##             elif not isinstance (surfName, (list, tuple)):
##                 if not surfName in surfNames:
##                     continue
##                 else:
##                     names = [surfName,]
##             else:
##                 names = surfName
##             for n in names: 
##                 # undo depends on whether current msms geometry resulted from
##                 # displayMSMS OR from displayBuriedTriangles
##                 # for each molecule, this is tracked in dictionary stored as
##                 # molecule.geomContainer.msmsCurrentDisplay[surfName]
##                 #possibly surface was previously computed but never displayed
##                 lastCmd = geomC.msmsCurrentDisplay.get(n, "")
##                 if lastCmd=="" or lastCmd.find('displayMSMS')>-1:
##                     #no previous geometry OR the geometry resulted from displayMSMS 
##                     not_negate =  not negate
##                     if not geomC.atoms.has_key(n):
##                         continue
##                     ats = geomC.atoms[n]
##                     if not len(ats):
##                         continue
##                     #FIX THIS SHOULD IT REALLY BE NOT-NEGATE???
##                     old_atoms_name = self.app().undo.saveUndoArg(ats)
##                     undoCmd = "self.displayMSMS(%s, surfName=['%s'], negate=%d, only=%d, nbVert=%d)" %(old_atoms_name, n, not_negate, only, nbVert)
##                     #undoCmd = "self.displayMSMS('%s', surfName=['%s'], negate=%d, only=%d, nbVert=%d)" %(old_atoms_name, n, not_negate, only, nbVert)
##                     self.app().undo.addEntry((undoCmd), (self.name))
##                 elif lastCmd.find('displayBuried')>-1:
##                     #the geometry resulted from displayBuriedTriangles 
##                     #get a handle to the IndexedPolygon geometry
##                     g = geomC.geoms[n]
##                     #save the current verts
##                     old_vertices_name = self.app().undo.saveUndoArg(g.getVertices())
##                     #save the current faces
##                     old_faces_name = self.app().undo.saveUndoArg(g.getFaces())
##                     #save the current vnormals
##                     old_vnormals_name = self.app().undo.saveUndoArg(g.getVNormals())
##                     #save the current front_colors
##                     front_colors = g.materials[GL.GL_FRONT].getState()
##                     old_front_name = self.app().undo.saveUndoArg(front_colors)
##                     #save the current back_colors
##                     back_colors = g.materials[GL.GL_BACK].getState()
##                     old_back_name = self.app().undo.saveUndoArg(back_colors)
##                     undoCmd = "from opengltk.OpenGL import GL;g = self.expandNodes('%s')[0].geomContainer.geoms['%s'];g.Set(vertices=%s, faces=%s, vnormals=%s);apply(g.materials[GL.GL_FRONT].Set, (), %s);apply(g.materials[GL.GL_BACK].Set, (), %s)" %(mol.name, n, old_vertices_name, old_faces_name, old_vnormals_name, old_front_name, old_back_name)
##                     geomC.msmsCurrentDisplay[n] = undoCmd
##                     self.app().undo.addEntry((undoCmd), (self.name))



    def doit(self, nodes, surfName='all', negate=False, only=False,
             nbVert=Pmv.numOfSelectedVerticesToSelectTriangle, redraw=True):
        #print "DisplayMSMS.doit",  "surfName:" , surfName
        molecules, atomSets = self.app().getNodesByMolecule(nodes, Atom)
        names = None

        rsetOn = AtomSet([])
        rsetOff = AtomSet([])

        for mol, atoms in zip(molecules, atomSets):
            try:
                geomC = mol.geomContainer
                if not hasattr(geomC, 'msms'):
                    continue
                surfNames = geomC.msms.keys()
                if surfName == 'all':
                    names = surfNames

                elif not isinstance (surfName, (list, tuple)):
                    if not surfName in surfNames:
                        raise RuntimeError, "Error in displaying MSMS for molecule %s: %s surface does not exist" %(mol.name, surfName)
                    else:
                        names = [surfName,]
                else:
                    names = surfName

                for sName in names:
                    # Make sure that the surface exists for this molecule.
                    if not sName in surfNames: continue
                    # first get the atoms for this molecule in set of atoms used
                    # for that surface
                    allAtms = geomC.msmsAtoms[sName]
                    atm = allAtms.inter(atoms)

                    # get the set of atoms with surface displayed
                    lSet = geomC.atoms[sName]

                    ##if negate, remove current atms from displayed set
                    if negate:
                        setOff = atm
                        setOn = None
                        lSet = lSet - atm

                    ##if only, replace displayed set with current atms 
                    else:
                        if only:
                            setOff = lSet - atm
                            setOn = atm
                            lSet = atm
                        else:
                            lSet = atm + lSet
                            setOff = None
                            setOn = lSet

                    if lSet is None:
                        print "skipping ", sName
                        continue
                    if setOn: rsetOn += setOn
                    if setOff: rsetOff += setOff

                    geomC.setAtomsForGeom(sName, lSet)

                    # get the msms surface object for that molecule
                    srf = geomC.msms[sName][0]

                    # get the atom indices
                    surfNum = geomC.msms[sName][1]
                    indName = '__surfIndex%d__'%surfNum
                    atomindices = []
                    for a in lSet:
                        atomindices.append(getattr(a, indName))

                    g = geomC.geoms[sName]
                    if lSet.stringRepr is not None:
                        geomC.msmsCurrentDisplay[sName] = "self.displayMSMS('%s', surfName=['%s'], negate=%d, only=%d, nbVert=%d)" %(lSet.stringRepr, sName, negate, only, nbVert)
                    else:
                        geomC.msmsCurrentDisplay[sName] = "self.displayMSMS('%s', surfName=['%s'], negate=%d, only=%d, nbVert=%d)" %(lSet.full_name(), sName, negate, only, nbVert)
                    if len(atomindices) == 0:
                        g.Set(visible=0, tagModified=False)
                    else:
                        # get the triangles corresponding to these atoms
                        vf, vi, f = srf.getTriangles(atomindices, selnum=nbVert, keepOriginalIndices=1)
                        col = mol.geomContainer.getGeomColor(sName)
                        g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6],
                               faces=f[:,:3], materials=col, visible=1,
                               tagModified=False, inheritMaterial=False)

                        if g.transparent:
                            opac = mol.geomContainer.getGeomOpacity(sName)
                            g.Set( opacity=opac, redo=0, tagModified=False)

                        # update texture coordinate if needed
                        if g.texture and g.texture.enabled and g.texture.auto==0:
                            mol.geomContainer.updateTexCoords[sName](mol)

                        # highlight selection
                        #vi = self.app().GUI.VIEWER
                        selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get(), Atom)
                        lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                        ats = lMolSelectedAtmsDict.get(mol, None)
                        if ats is not None:
                            lAtomSet = mol.geomContainer.msmsAtoms[sName]
                            if len(lAtomSet) > 0:
                                    lAtomSetDict = dict(zip(lAtomSet, range(len(lAtomSet))))
                                    lAtomIndices = []
                                    for i in range(len(ats)):
                                        lIndex = lAtomSetDict.get(ats[i], None)
                                        if lIndex is not None:
                                            lAtomIndices.append(lIndex)							
                                    lSrfMsms = mol.geomContainer.msms[sName][0]
                                    lvf, lvint, lTri = lSrfMsms.getTriangles(lAtomIndices, selnum=nbVert,
                                                                             keepOriginalIndices=1)
                                    highlight = [0] * len(g.vertexSet.vertices)
                                    for lThreeIndices in lTri:
                                        highlight[int(lThreeIndices[0])] = 1
                                        highlight[int(lThreeIndices[1])] = 1
                                        highlight[int(lThreeIndices[2])] = 1
                                    g.Set(highlight=highlight)

        
                self.app()._executionReport.addSuccess('displayed surface for molecule %s successfully'%
                    mol.name, obj=atoms)
            except:
                msg = 'Error while displaying surface for molecule %s'%mol.name
                self.app().errorMsg(sys.exc_info(), msg, obj=mol)
        redraw = False 
        if self.createEvents and len(rsetOn)+len(rsetOff):
            event = EditGeomsEvent('msms_ds',
                                   [nodes,[names, negate, only, nbVert]],
                                   setOn=rsetOn, setOff=rsetOff)
            self.app().eventHandler.dispatchEvent(event)


    def checkArguments(self, nodes, only=False, negate=False,
                       surfName='all', nbVert=1, redraw=True):
        """Required Arguments:\n
        nodes  --- TreeNodeSet holding the current selection\n
        Optional Arguments:\n
        only   --- Boolean flag when set to True only the current selection will be displayed (default=False)\n
        negate --- Boolean flag when set to True undisplay the current selection (default=False)\n
        surfName   --- name of the selection, default = 'all'\n
        nbVert --- Nb of vertices per triangle needed to select a triangle\n
        """
       
        if isinstance (nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        nodes = self.app().expandNodes(nodes)

        if surfName is None: surfName = 'all'
        assert isinstance(surfName, (str, list, tuple))
        assert only in [True, False, 0, 1]
        assert negate in [True, False, 0, 1]
        assert isinstance (nbVert, int)
        kw = {}
        kw['redraw'] = redraw
        kw['only'] = only
        kw['negate'] = negate
        kw['nbVert'] = nbVert
        kw['redraw'] = 1
        kw['surfName'] = surfName
        return (nodes,), kw



class UndisplayMSMS(DisplayCommand):
    """The undisplayMSMS command allows the user to undisplay displayedMSMS\n
    Package : PmvApp\n
    Module  : msmsCmds\n
    Class   : UndisplayMSMS\n
    Command name : undisplayMSMS\n
    \nRequired Arguments:\n
    nodes  --- TreeNodeSet holding the current selection\n.
    """
    
    def onAddCmdToApp(self):
        if not self.app().commands.has_key('displayMSMS'):
            self.app().lazyLoad('msmsCmds', commands=['displayMSMS'], package='PmvApp')


    def checkArguments(self, nodes, **kw):
        """ nodes ---TreeNodeSet holding the current selection
        (mv.activeSelection.get())"""
        kw['negate']= 1
        kw['redraw']=1
        if isinstance(nodes, str):
            self.nodeLogString = "'" + nodes +"'"
        return (nodes,),kw

    
    def doit(self, nodes, **kw):
        """None <- undisplayMSMS(nodes, **kw)\n
           nodes ---TreeNodeSet holding the current selection
                   (mv.activeSelection.get())"""
        
        self.displayMSMS(nodes, **kw)



class ComputeSESAndSASArea(MVCommand):
    """Compute Solvent Excluded Surface and Solvent Accessible Surface Areas\n
    Package : PmvApp\n
    Module  : msmsCmds\n
    Class   : ComputeSESAndSASArea\n
    Command name : computeSESAndSASArea\n
    \nSynopsis :\n
    None--->mv.computeSESAndSASArea(mol)\n    
    \nDescription:\n
    Computes Solvent Excluded Surface and Solvent Accessible Surface Areas. Stores numeric values per Atom,
    Residue, Chain, and Molecule in ses_area and sas_area attributes.
    """
    def onAddCmdToApp(self):
        if not self.app().commands.has_key('computeMSMS'):
            self.app().lazyLoad('msmsCmds', commands=['ComputeMSMS',], package='PmvApp')


    def doit(self, mol):
        try:
            allrads = mol.defaultRadii()
            allChains = mol.chains
            allResidues = mol.chains.residues
            allAtoms = mol.allAtoms
            import mslib
            # compute the surface
            srf = mslib.MSMS(coords=allAtoms.coords, radii = allrads)
            srf.compute()
            srf.compute_ses_area()        
            # get surface areas per atom
            ses_areas = []
            sas_areas = []
            for i in xrange(srf.nbat):
                atm = srf.get_atm(i)
                ses_areas.append(atm.get_ses_area(0))
                sas_areas.append(atm.get_sas_area(0))
            # get surface areas to each atom
            allAtoms.ses_area = ses_areas
            allAtoms.sas_area = sas_areas
            # sum up ses areas over resdiues
            for r in allResidues:
                r.ses_area = numpy.sum(r.atoms.ses_area)        
                r.sas_area = numpy.sum(r.atoms.sas_area)

            mol.ses_area = 0
            mol.sas_area = 0            
            for chain in allChains:
                chain.ses_area = 0
                chain.sas_area = 0
                for residue in chain.residues:
                    chain.ses_area += numpy.sum(residue.ses_area)
                    chain.sas_area += numpy.sum(residue.sas_area)
                mol.ses_area += chain.ses_area 
                mol.sas_area += chain.sas_area
            self.app()._executionReport.addSuccess('%s: computed surface for molecule %s successfully'%(self.name, mol.name), obj=allAtoms)
        except:
            msg = '%s: Error while computing surface for molecule %s'%(self.name, mol.name)
            self.app().errorMsg(sys.exc_info(), msg, obj=mol)            

            
    def checkArguments(self, molecule):
        """
    Computes Solvent Excluded Surface and Solvent Accessible Surface Areas. Stores numeric values per Atom,
    Residue, Chain, and Molecule in ses_area and sas_area attributes.               
        """
        nodes=self.app().expandNodes(molecule)

        return (nodes), kw


class SaveMSMS(MVCommand):
    """The SaveMSMS command allows the user to save a chosen MSMS surface (tri-angulated solvant excluded surface) in two files: .vert(vertex coordinates) and .face (vertex indices of the faces) .\n
    Package : PmvApp\n
    Module  : msmsCmds\n
    Class   : SaveMSMS\n
    Command name : saveMSMS\n
    Description:\n
    If the component number is 0, files called filename.vert and filename.face
    are created.
    For other components, the component number is appended in the file name,
    for example for the component number 3 the files are called
    filename_3.vert and filename_3.face.

    The face file contains three header lines followed by one triangle per
    line. The first header line provides a comment and the filename of the
    sphere set.
    The second header line holds comments about the content of the third line.
    The third header line provides the number of triangles, the number of
    spheres in the set, the triangulation density and the probe sphere radius.
    The first three numbers are (1 based) vertex indices. The next field
    can be: 1 for a triangle in a toric reentrant face, 2 for a triangle in
    a spheric reentrant face and 3 for a triangle in a contact face.
    The last number on the line is the (1 based) face number in the
    analytical description of the solvent excluded surface. These values
    are written in the following format ''%6d %6d %6d %2d %6d''.

    The vertex file contains three header lines (similar to the header
    in the .face file) followed by one vertex per line and provides the
    coordinates (x,y,z) and the normals (nx,ny,nz) followed by the number of
    the face (in the analytical description of the solvent excluded surface)
    to which the vertex belongs.
    The vertices of the analytical surface have a value 0 in that field and
    the vertices lying on edges of this surface have nega tive values.
    The next field holds the (1 based) index of the closest sphere.
    The next field is 1 for vertices which belong to toric reentrant faces
    (including vertices of the analytical surface), 2 for vertices inside
    reentrant faces and 3 for vertices inside contact faces.
    Finally, if atom names were present in the input file, the name of the
    closest atom is written for each vertex. These values are written in
    the following format
    ''%9.3f %9.3f %9.3f %9.3f %9.3f %9.3f %7d %7d %2d %s''.\n

    \nSynopsis:\n
    None <- saveMSMS(filename, mol, surfacename, withHeader=1, component=0,
                     format='MS_TSES_ASCII', **kw)\n
    filename : name of the output file\n
    mol      : molecule associated with the surface\n
    surfacename : name of the surface to save\n
    withHeader  : flag to either write the headers or not\n
    component   : specifies which component of the surface to write out\n
    format      : specifies in which format to save the surface. 
                  It can be one of the following ,\n
                  'MS_TSES_ASCII' Triangulated surface in ASCII format\n
                  'MS_ASES_ASCII' Analytical surface in ASCII format. This is
                  actually a discrete representation of the analytical model.\n
                  'MS_TSES_ASCII_AVS' Triangulated surface in ASCII with
                  AVS header\n
                  'MS_ASES_ASCII_AVS'  Analytical surface in ASCII format
                  with AVS header\n

    """

    def onAddCmdToApp(self):
        self.formats = ['MS_TSES_ASCII', 
                        'MS_ASES_ASCII', 
                        'MS_TSES_ASCII_AVS',
                        'MS_ASES_ASCII_AVS'
                        ]
        # MS_TSES_ASCII : Triangulated surface in ASCII format
        # MS_ASES_ASCII : Analytical surface in ASCII format, which is
        #                 a discrete representation of the analytical model
        # MS_TSES_ASCII_AVS : Triangulated surface in ASCII with AVS header
        # MS_ASES_ASCII_AVS : Analytical surface in ASCII format with AVS
        #                     header

    
    def doit(self, filename, molName, surfName, withHeader=True, component=0,
             format="MS_TSES_ASCII"):
        try:
            mol = self.app().getMolFromName(molName)
            if mol is None:
                raise RuntimeError, "saveMSMS: no molecule %s found"% molName
            gc = mol.geomContainer
            if not hasattr(gc, "msms") or not gc.msms.has_key(surfName):
                raise RuntimeError, "saveMSMS: no molecule surface %s"% surfName
            msmsSurf = gc.msms[surfName][0]
            msmsAtms = gc.msms[surfName]
            from mslib import msms
            if not format in self.formats:
                format = "MS_TSES_ASCII"
            format = getattr(msms, format)
            if component is None : component = 0
            elif not component in range( msmsSurf.rsr.nb ):
                raise RuntimeError, "%s error: %s is an invalid component"%(self.name, component)
            msmsSurf.write_triangulation(filename, no_header=not withHeader,
                                         component=component, format=format)
            self.app()._executionReport.addSuccess('saved surface for molecule %s successfully'%
                    molName, obj=mol)
        except:
            msg = 'Error while saving surface for molecule %s'%molName
            self.app().errorMsg(sys.exc_info(), msg, obj=mol)


    def checkArguments(self, filename, molName, surfName, withHeader=True,
                 component=None, format="MS_TSES_ASCII"):
        """None <--- mv.saveMSMS(filename, mol, surface, withHeader=True,component=None, format='MS_TSES_ASCII', **kw)\n
        Required Arguments:\n
        filename --- path to the output file without an extension two files will be created filename.face and a filename.vert\n 
        mol      --- Protein associated to the surface\n
        surface  --- surface name\n

        Optional Arguments:\n
        withHeader --- True Boolean flag to specify whether or not to write the headers in the .face and the .vert files\n
        component  --- msms component to save by default None\n
        format     --- format in which the surface will be saved. It can be,\n        
        MS_TSES_ASCII: Triangulated surface in ASCII format.\n
        MS_ASES_ASCII: Analytical surface in ASCII format.This is a discrete representation of the analytical model.MS_TSES_ASCII_AVS: Triangulated surface in ASCII with AVS header\n
        MS_ASES_ASCII_AVS: Analytical surface in ASCII format with AVS header\n
        
        """
        assert isinstance(filename, str)
        assert isinstance( molName, str)
        assert isinstance(surfName, str)
        assert withHeader in [True, False, 1, 0]
        assert format in self.formats
        kw = {}
        kw['withHeader'] = withHeader
        kw['component'] = component
        kw['format'] = format
        return (filename, molName, surfName), kw
        

class ReadMSMS(MVCommand):
    """Command reads .face and .vert file, creates the msms surface and links it to the selection if can\n
    Package : PmvApp\n
    Module  : msmsCmds\n
    Class   : ReadMSMS\n
    Command name : readMSMS\n
    nSynopsis :\n
    None--->self.readMSMS(vertFilename, faceFilename, molName=None)\n
    \nRequired Arguments :\n
    vertFilename---name of the .vert file\n 
    faceFilename---name of the .face file\n    
    """

    def __init__(self):
        MVCommand.__init__(self)
        self.msmsFromFile = {}
    
    
    def doit(self, vertFilename, faceFilename, molName=None):
        try:
            vertFName = os.path.split(vertFilename)[1]
            faceFName = os.path.split(faceFilename)[1]
            vertName = os.path.splitext(vertFName)[0]
            faceName = os.path.splitext(faceFName)[0]
            assert vertName == faceName
            msmsParser = MSMSParser()
            self.msmsFromFile[vertName] = msmsParser
            msmsParser.parse(vertFilename, faceFilename)
            self.surf  = IndexedPolygons(vertName+'_msms', visible=1, 
                                    pickableVertices=1, protected=True,)
            if self.app().userpref['Sharp Color Boundaries for MSMS']['value'] == 'blur':
                self.surf.Set(inheritSharpColorBoundaries=False, sharpColorBoundaries=False, )
            #self.surf.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
            #self.surf.Set(frontPolyMode=GL.GL_FILL, redo=0)
            self.surf.Set(vertices=msmsParser.vertices, faces=msmsParser.faces,
                          vnormals=msmsParser.normals, tagModified=False)
            # The AppGUI should register an AddGeometryEvent listener
            # that implements a method to add geometry to the application
            # self.app().GUI.VIEWER.AddObject(self.surf)

            from AppFramework.App import AddGeometryEvent
            event = AddGeometryEvent(self.surf)
            self.app().eventHandler.dispatchEvent(event)


            if not molName is None:
                if not hasattr(self.app(), "bindGeomToMolecularFragment"):
                    self.app().lazyLoad("displayCmds", commands=['bindGeomToMolecularFragment'],
                                        package="PmvApp")
                self.app().bindGeomToMolecularFragment(self.surf, molName)

                # highlight selection
                surf = self.surf
                bindcmd = self.app().bindGeomToMolecularFragment
                selMols, selAtms = self.app().getNodesByMolecule(self.app().activeSelection.get(), Atom)
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                print self.name, "doit", surf.mol
                if lMolSelectedAtmsDict.has_key(surf.mol()):
                    lSelectedAtoms = lMolSelectedAtmsDict[surf.mol()]
                    if len(lSelectedAtoms) > 0:
                        lAtomVerticesDict = bindcmd.data[surf.fullName]['atomVertices']
                        highlight = [0] * len(surf.vertexSet.vertices)
                        for lSelectedAtom in lSelectedAtoms:
                            lVertexIndices = lAtomVerticesDict.get(lSelectedAtom, [])
                            for lVertexIndex in lVertexIndices:
                                highlight[lVertexIndex] = 1
                        surf.Set(highlight=highlight)
            self.app()._executionReport.addSuccess('read surface from files %s, %s successfully'%(vertName, faceName ), obj=surf)
        except:
            msg = 'Error while reading surface for molecule %s'%vertFilename
            self.app().errorMsg(sys.exc_info(), msg, obj=None)

    def checkArguments(self, vertFilename, faceFilename, molName=None):
        """None--->mv.readMSMS(vertFilename,faceFilename,molName=None, **kw)
        """
        assert os.path.exists(vertFilename)
        assert os.path.exists(faceFilename)
        if molName:
            assert isinstance(molName, str)
        kw = {}
        kw['molName'] = molName
        #kw['redraw'] = 1
        return (vertFilename, faceFilename), kw
       


commandClassFromName = {
    'displayMSMS' : [DisplayMSMS, None],
    'undisplayMSMS' : [UndisplayMSMS, None],
    'computeMSMS' : [ComputeMSMS, None],
    'computeSESAndSASArea' : [ComputeSESAndSASArea, None],
    'readMSMS' : [ReadMSMS, None],
    'saveMSMS' : [SaveMSMS, None],
    #'computeMSMSApprox' : [ComputeMSMSApprox, None],
    #'identifyBuriedVertices' : [IdentifyBuriedVertices, None],
    #'displayBuriedTriangles' : [DisplayBuriedTriangles, None],
    #'displayIntermolecularBuriedTriangles' : [DisplayIntermolecularBuriedTriangles, None],
    #'assignBuriedAreas' : [AssignBuriedAreas, None],
    
}

def initModule(viewer, gui=True):
    for cmdName, values in commandClassFromName.items():
        cmdClass, guiInstance = values
        viewer.addCommand(cmdClass(), cmdName, guiInstance)


