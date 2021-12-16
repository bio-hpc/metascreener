## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2000
#
#############################################################################

# $Header: /opt/cvs/python/packages/share1.5/Pmv/moleculeViewer.py,v 1.296 2014/03/21 23:02:59 annao Exp $

#
# $Id: moleculeViewer.py,v 1.296 2014/03/21 23:02:59 annao Exp $
#
import shutil, tarfile

from MolKit.molecule import Atom, AtomSet, BondSet, Molecule , MoleculeSet
from MolKit.protein import Protein, ProteinSet, Residue, Chain, ResidueSet
from MolKit.stringSelector import CompoundStringSelector
from DejaVu.Geom import Geom
from ViewerFramework.VF import ViewerFramework, GeomContainer
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.Spheres import Spheres
from DejaVu.Points import CrossSet
from DejaVu.Cylinders import Cylinders
from Pmv.mvCommand import MVInteractiveCmdCaller
from mglutil.util.packageFilePath import getResourceFolderWithVersion, findFilePath
import thread
from types import StringType, ListType
import Pmw
import os, sys
from numpy.oldnumeric import array, fabs, maximum
from string import find, replace, split
from MolKit.tree import TreeNode, TreeNodeSet
import tkMessageBox
from mglutil.util.callback import CallbackFunction
from mglutil.util.packageFilePath import findFilePath
ICONPATH = findFilePath('Icons', 'Pmv')

from ViewerFramework.VF import VFEvent

class PickingEvent(VFEvent):
    pass

class DragSelectEvent(VFEvent):
    pass

class AddAtomsEvent(VFEvent):
    pass

class DeleteAtomsEvent(VFEvent):
    pass

class EditAtomsEvent(VFEvent):
    pass

class AddGeomsEvent(VFEvent):
    pass

class DeleteGeomsEvent(VFEvent):
    pass

class EditGeomsEvent(VFEvent):
    pass

class ShowMoleculesEvent(VFEvent):
    pass

class AddObjectEvent(VFEvent):
    def __init__(self, object):
        VFEvent.__init__(self)
        self.object = object


class MolGeomContainer(GeomContainer):
    """
    Class to hold geometries used to represent molecules in a viewer.
    An instance of such a class called geomContainer is added to each Molecule
    as it is loaded into a Viewer
    """
    def __init__(self, mol, viewerframework):
        """constructor of the geometry container"""

        GeomContainer.__init__(self)

        self.mol = mol
        mol.geomContainer = self

        ## Dictionary of AtomSets used to track which atoms are currently
        ## each mode
        self.atoms = {}

        ## Dictionary of function to be called to expand an atomic
        ## property to the corresponding vertices in a geometry
        ## The function has to accept 4 arguments: a geometry name,
        ## a list of atoms,  the name of the property and an optional argument
        ## the propIndex default is None, specifying the index of the property
        ## when needed.
        ## the key is the geometry name
        self.atomPropToVertices = {}

        
        ## Dictionary of function to be called to convert a vertex into an atom
        ## if no function is registered, used default (1vertex to 1atom)
        ## mapping
        ## if None is registered: this geometry cannot represent atoms
        ## else, call the function registered for this geometry
        self.geomPickToAtoms = {}

        ## Dictionary of function to be called when a part into a bond
        ## if no function is registered, used default (1vertex to 1bond)
        ## mapping
        ## if None is registered: this geometry cannot represent bonds
        ## else, call the function registered for this geometry
        self.geomPickToBonds = {}

        ## this set of coordinates should really be shared by all geometries
        self.allCoords = mol.allAtoms.coords

        if viewerframework:
            self.VIEWER = viewerframework.GUI.VIEWER
        else:
            self.VIEWER = None

        # master Geometry
        self.masterGeom = Geom(mol.name, shape=(0,0), 
                               pickable=0, protected=True)
        self.masterGeom.isScalable = 0
        self.geoms['master'] = self.masterGeom
        self.masterGeom.replace = True

        if self.VIEWER:
            self.VIEWER.AddObject( self.masterGeom )

        self.geoms['selectionSpheres'] = Spheres(
            'selectionSpheres', shape=(0,3), radii=0.3, quality = 3, 
            materials = ((1.0, 1.0, 0.),), inheritMaterial=0, protected=True,
            animatable=False)
        self.geoms['selectionSpheres'].pickable=0
        self.atoms['selectionSpheres']=AtomSet([])
        self.geoms['selectionCrosses'] = CrossSet(
            'selectionCrosses', shape=(0,3), materials=((1.0, 1.0, 0.),),
            lineWidth=2, inheritMaterial=0, protected=True,
            disableStencil=True, transparent=True,
            animatable=False)
        self.geoms['selectionCrosses'].pickable=0
        
        #sph = Spheres('selectionSpheres', shape=(0,3), radii=0.3, quality = 3, 
        #              materials = ((1.0, 1.0, 0.),), inheritMaterial=0,
        #              protected=True)
        #sph.pickable=0

        if self.VIEWER:
            self.VIEWER.AddObject(self.geoms['selectionSpheres'],
                                  parent=self.masterGeom, redo=0 )
            self.VIEWER.AddObject(self.geoms['selectionCrosses'],
                                  parent=self.masterGeom, redo=0 )


    def addGeom(self, geom, parent=None, redo=False):
        # add geometry to to geomContainer, create atom set and set pointer
        # from geom to molecule
        
        GeomContainer.addGeom(self, geom, parent, redo)
        if not self.atoms.has_key(geom.name):
            self.atoms[geom.name]=AtomSet([])
        # FIXME we should use a weakreference to mol here
        geom.mol = self.mol  #need for backtracking picking


    def getGeomColor(self, geomName):
        # build a list of colors for a geometry from the atom's colors
        if self.atomPropToVertices.has_key(geomName):
            func = self.atomPropToVertices[geomName]
            geom = self.geoms[geomName]
            atms = self.atoms[geomName]
            col = func(geom, atms, 'colors', propIndex=geomName)

        else:
            if geomName in self.atoms.keys():
                col = map(lambda x, geomName=geomName: x.colors[geomName],
                          self.atoms[geomName])
            else:
                return

        if col is not None:
            colarray = array(col, 'f')
            diff = colarray - colarray[0]
            maxi = maximum.reduce(fabs(diff.ravel()))
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
                self.geoms[name].Set( materials = col, redo=1,
                                      tagModified=False, transparent='implicit')
                opac = self.getGeomOpacity(name)
            else: opac = None
            
            if col is not None and opac is not None:
                self.geoms[name].Set( materials=col, opacity=opac, redo=1,
                                      tagModified=False, transparent='implicit')
            elif col is not None:
                self.geoms[name].Set( materials=col, redo=1, tagModified=False, transparent='implicit')
            elif opac is not None:
                self.geoms[name].Set( opacity=opac, redo=1, tagModified=False, transparent='implicit')


    def getGeomOpacity(self, geomName):
        if self.atomPropToVertices.has_key(geomName):
            func = self.atomPropToVertices[geomName]
            geom = self.geoms[geomName]
            atms = self.atoms[geomName]
            col = func(geom, atms, 'opacities', propIndex = geomName)
        else:
            if geomName in self.atoms.keys():
                col = map(lambda x, geomName=geomName: x.opacities[geomName],
                              self.atoms[geomName])
                
            else:
                return
        if col is not None:
            colarray = array(col, 'f')
            diff = colarray - colarray[0]
            maxi = maximum.reduce(fabs(diff.ravel()))
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
                col = array(col, 'f')
                self.geoms[name].Set( materials = col, redo=1,
                                      tagModified=False)


from MolKit.molecule import Molecule, MoleculeSet
from ViewerFramework.VFCommand import Command, CommandGUI
import Tkinter

from DejaVu import Viewer

class PMVViewer(Viewer):
    """
    package    : Pmv
    module     : moleculeViewer
    class      : PMVViewer
    description:
       Class derived from DejaVu.Viewer base class. It overrides
       _AddObject() method of the base class to set 'animatable' property
       of a Pmv geometry. 
    """


    def _AddObject(self, obj, parent, redo=False):
        Viewer._AddObject(self, obj, parent, redo=redo)
        if obj.LastParentBeforeRoot().name == 'misc':
            obj.Set(animatable = False)
        



class MoleculeViewer(ViewerFramework):
    """
    package    : Pmv
    module     : moleculeViewer
    class      : MoleculeViewer
    description:
       Class derived from the ViewerFramework base class. It provides a 3D
       molecular viewer.
    """
    

    def getSelLev(self):
        return self.selection.elementType


    def setSelLev(self, value):
        if value==Protein: value = Molecule
        assert value in [Molecule, Chain, Residue, Atom]
        self.setSelectionLevel(value)

    selectionLevel = property(getSelLev, setSelLev)


    ##
    ## Functions generating code for session
    ##

    def getStateCodeForSets(self):
        ##
        ## define all sets
        ##
        lines = """##\n## define all sets\n##\n"""
        dashboardTreeEntries = [x.object.name for x in self.dashboard.tree.root.children]
        for name, objs in self.sets.items():
            if name in dashboardTreeEntries: # add entry to dashboard
                lines += "self.addSelectionToDashboard('%s', '%s', topCommand=0)\n"%(name, objs.buildRepr())
            else: # regular set
                lines += """self.saveSet('%s', '%s', comments='%s')\n"""%(
                    objs.buildRepr(), name, objs.comments)
        return lines


    def getStateCodeForMeasureGeoms(self):
        "Returns source code needed to reproduce measure geomerties (measure distance, angle and torsion)."
        atomList = self.measureDistGUI.atomList
        lines = "" 
        for index, atom in enumerate(atomList[::2]):
            atom2 =  atomList[2*index+1]
            lines +="self.measureDistGUI('%s;%s')\n"%(atom.full_name(), atom2.full_name())

        atomList = self.measureAngleGC.atomList
        for index, atom in enumerate(atomList[::3]):
            atom2 =  atomList[3*index+1]
            atom3 =  atomList[3*index+2]            
            lines +="self.measureAngleGC('%s;%s;%s')\n"%(atom.full_name(), atom2.full_name(), atom3.full_name())

        atomList = self.measureTorsionGC.atomList
        for index, atom in enumerate(atomList[::4]):
            atom2 =  atomList[3*index+1]
            atom3 =  atomList[3*index+2]            
            atom4 =  atomList[3*index+3]            
            lines +="self.measureTorsionGC('%s;%s;%s;%s')\n"%(atom.full_name(), atom2.full_name(), atom3.full_name(), atom4.full_name())
            
        return lines
            
        
    def getStateCodeForMolecule(self, mol, mode="string"):
        # mode can be string or cmd. When it is string we get strings to be saved in a session file
        # when mode is cmds we get a list of python commands
        
        ##
        ## read in all molecules
        ##
        lines = """##\n## read in all molecules\n##\n"""

        ## generate Pmv commands to load the molecule
        molFile = os.path.basename(mol.getFilename())
        if mol.parser and mol.parser.model == True:
            if hasattr(mol, 'modelFilename'):
                molFile = mol.modelFilename
        molName = os.path.splitext(molFile)[0]
        ## check for multimodel file ("modelsAs") :
        if hasattr(mol.parser, 'modelsAs') and mol.parser.modelsAs != "molecules":
            # add "modelsAs" keyword to self.readMolecule:
            lines += """mols = self.Mols.get('%s')\nif len(mols)==0:\n\tmols = self.readMolecule('%s', addToRecent=False, modelsAs='%s')\n"""%(molName, molFile, mol.parser.modelsAs)
        else:
            lines += """mols = self.Mols.get('%s')\nif len(mols)==0:\n\tmols = self.readMolecule('%s', addToRecent=False)\n"""%(molName, molFile)
        lines += "self.undisplayLines(mols)\n"

        lines += "currentAtoms = mols.allAtoms\n"
        lines += "currentAtoms.sort()\n"
        currentAtoms = mol.allAtoms
        currentAtoms.sort()

        cmds = []
        ##
        ## create geometry
        ##   
        lines += """##\n## create geometry\n##\n"""
        ## generate Pmv commands to create geometry that are currently displayed
        gc = mol.geomContainer
        gca = gc.atoms
        gcg = gc.geoms

        ##
        ## molecular surfaces
        ##
        if hasattr(gc, "msms"):
            for name, srfa in gc.msms.items():
                srf = srfa[0]
                atoms = gca[name]
                if len(gca[name]): # This surface is displayed
                    lines += """self.computeMSMS('%s', hdensity=%f, hdset=%s, density=%f, pRadius=%f, perMol=%d, noHetatm=%d, display=False, surfName='%s')\n"""%(
                        atoms.buildRepr(), srf.hdensity, srf.hdset, srf.density,
                        srf.probeRadius, srf.perMol, srf.noHetatm, name)
                    cmds.append( (self.computeMSMS, (atoms,), {'hdensity':srf.hdensity, 'hdset':srf.hdset,
                                                               'density':srf.density, 'pRadius':srf.probeRadius,
                                                               'perMol':srf.perMol, 'noHetatm':srf.noHetatm,
                                                               'display':False, 'surfName':name}) )
                else:
                    lines += """self.computeMSMS('%s', hdensity=%f, hdset=%s, density=%f, pRadius=%f, perMol=%d, noHetatm=%d, display=False, surfName='%s')\n"""%(
                        currentAtoms.buildRepr(), srf.hdensity, srf.hdset, srf.density,
                        srf.probeRadius, srf.perMol, srf.noHetatm, name)
                    cmds.append((self.computeMSMS, (currentAtoms,), {'hdensity':srf.hdensity, 'hdset':srf.hdset,
                                                               'density':srf.density, 'pRadius':srf.probeRadius,
                                                               'perMol':srf.perMol, 'noHetatm':srf.noHetatm,
                                                               'display':False, 'surfName':name}) )

        ##
        ## Ribbons
        ##
        from MolKit.getsecondarystructure import \
             GetSecondaryStructureFromFile,\
             GetSecondaryStructureFromPross, \
             GetSecondaryStructureFromStride
             
        if hasattr(mol, 'builder'): # this molecule has SS
            # find which method was used and build the Ribbon
            kw = {}
            if isinstance(mol.builder, GetSecondaryStructureFromFile):
                molMode = "molModes={'%s':'From File'},"%mol.name
                kw['molModes'] = {mol.name:'From File'}
            elif isinstance(mol.builder, GetSecondaryStructureFromPross):
                molMode = "molModes={'%s':'From Pross'},"%mol.name
                kw['molModes'] = {mol.name:'From Pross'}
            if isinstance(mol.builder, GetSecondaryStructureFromStride):
                molMode = "molModes={'%s':'From Stride'},"%mol.name
                kw['molModes'] = {mol.name:'From Stride'}

            # compute secondary structure
            lines += "self.computeSecondaryStructure('%s', %s)\n"%(
                mol.name, molMode)
            cmds.append( (self.computeSecondaryStructure, (mol.name,), kw) )
        
            # for each chain extrude Secondary Structure
            for chain in mol.chains:
                if not hasattr(chain, 'ssExtrusionParams'): continue
                p = chain.ssExtrusionParams
                shape1 = p['shape1']
                if shape1 is not None:
                    shape1i, shape1t = shape1.returnStringRepr()
                    lines += shape1i+'\n' #import statment for shape 1
                else:
                    shape1t = 'None'

                shape2 = p['shape2']
                if shape2 is not None:
                    shape2i, shape2t = shape2.returnStringRepr()
                    lines += shape2i+'\n' #import statment for shape 2
                else:
                    shape2t = 'None'

                lines += """self.extrudeSecondaryStructure('%s:%s', nbchords=%d, gapBeg=%d, gapEnd=%d, frontcap=%d, endcap=%d, larrow=%d, arrow=%d, shape1=%s, shape2=%s, display=False)\n"""%(mol.name, chain.id, p['nbchords'], p['gapBeg'], p['gapEnd'], p['frontcap'], p['endcap'], p['larrow'], p['arrow'], shape1t, shape2t)
                cmds.append( (self.extrudeSecondaryStructure, ("%s:%s" %(mol.name, chain.id),),
                              {'nbchords':p['nbchords'], 'gapBeg':p['gapBeg'], 'gapEnd':p['gapEnd'],
                               'frontcap':p['frontcap'], 'endcap':p['endcap'], 'larrow':p['larrow'],
                               'arrow':p['arrow'], 'shape1':shape1, 'shape2':shape2, 'display':False}) )

        ##
        ## beaded Ribbons
        ##
        vi = self.GUI.VIEWER
        master = vi.FindObjectByName('root|%s|beadedRibbon'%(mol.name,))
        if master:
            # code to restore mol.strandVarValue
            d = {}
            for k,v in mol.strandVar.items():
                d[k] = v.get()
            lines += "mols[0].strandVarValue = %s\n"%str(d)
            cmds.append( (setattr, (mol, "strandVarValue", d), {}) )
            lines += "self.beadedRibbons('%s', **%s)\n"%(
                mol.name, str(mol.beadedRibbonParams))
            cmds.append((self.beadedRibbons, (mol.name,),  mol.beadedRibbonParams))
            
        ## compute coarse molecular surfaces
        if self.commands.has_key('coarseMolSurface'):
            for geomName in self.coarseMolSurface.surfNameList:
                geom = vi.FindObjectByName('root|%s|%s'%(mol.name, geomName))
                if geom:
                    p = self.coarseMolSurface.CSparams[geom.fullName]
                    if isinstance(p['nodes'], str):
                        nodesString = p['nodes']
                    else:
                        nodesString = p['nodes'].buildRepr()
                    lines += "self.coarseMolSurface(bindGeom=%d, gridSize=%d, surfName='%s', padding=%f, perMol=%d, nodes='%s', "%(
                        p['bindGeom'], p['gridSize'], geomName, p['padding'],
                        p['perMol'], nodesString)

                    if isinstance(p['isovalue'], str):
                        lines += "isovalue='%s', "%p['isovalue']
                    else:
                        lines += "isovalue=%f, "%p['isovalue']

                    if isinstance(p['resolution'], str):
                        lines += "resolution='%s')\n"%p['resolution']
                    else:
                        lines += "resolution=%f)\n"%p['resolution']
                    cmds.append((self.coarseMolSurface, (), p))
                    

        ## isocontour TODO

        ##
        ## atom colors
        ##
        colors={}
        lines += """##\n## atom colors\n##\n"""
        for an, a in enumerate(currentAtoms):
            for k,v in a.colors.items():
                if v!=(1.0, 1.0, 1.0) and len(v)==3:
                    lines += "currentAtoms[%d].colors['%s']=(%f, %f, %f)\n"%(
                        an, k, v[0], v[1], v[2])
                if not colors.has_key(an):
                    colors[an] = {}
                colors[an][k] = v
        cmds.append(("atomcolors", colors))
        ##
        ## display geometry
        ##
        lines += """\n#### display geometry\n##\n"""
        gc = mol.geomContainer
        gca = gc.atoms    
        allGeoms = gca.keys() # list of all geometries

        ##
        ## Lines
        ##
        if gca.has_key('bonded') and gca['bonded']:
            lw = gc.geoms['bonded'].lineWidth
            lines += """self.displayLines('%s', displayBO=False, lineWidth=%d)\n"""%(gca['bonded'].buildRepr(), lw)
            cmds.append((self.displayLines, (gca['bonded'],), {'displayBO':False, 'lineWidth':lw}) )
                        
        ##
        ## Sticks and Balls
        ##
        data={}
        if gca.has_key('sticks') and gca['sticks']:
            for i,a in enumerate(currentAtoms):
                if fabs(a.cRad-0.2)>0.01:
                    lines += "currentAtoms[%d].cRad = %f\n"%(i, a.cRad)
                    if not data.has_key(i):
                        data[i] = {}
                    data[i]['cRad'] = a.cRad
            for i,a in enumerate(currentAtoms):
                if fabs(a.ballRad-0.3)>0.01:
                    lines += "currentAtoms[%d].ballRad = %f\n"%(i, a.ballRad)
                    if not data.has_key(i):
                        data[i] = {}
                    data[i]['ballRad'] = a.ballRad
                if fabs(a.ballScale-0.0)>0.01:
                    lines += "currentAtoms[%d].ballScale = %f\n"%(i, a.ballScale)
                    if not data.has_key(i):
                        data[i] = {}
                    data[i]['ballScale'] = a.ballScale
            if len(data):
                cmds.append(("atomdata", data))

            sticksQuality = gc.geoms['sticks'].quality
            ballsQuality = gc.geoms['balls'].quality
            lines += """self.displaySticksAndBalls('%s', cquality=%d, sticksBallsLicorice='Sticks and Balls', bquality=%d, setScale=False)\n"""%(gca['sticks'].buildRepr(), sticksQuality, ballsQuality, )
            cmds.append((self.displaySticksAndBalls, (gca['sticks'],),
                         {'cquality':sticksQuality, 'sticksBallsLicorice':'Sticks and Balls',
                          'bquality':ballsQuality, 'setScale':False}))

        ##
        ## CPK and Balls
        ##
        if gca.has_key( 'cpk') and gca['cpk']:
            addtocmds = False
            if len(data) == 0:
                addtocmds = True
            # save atm.cpkScale unless == 1.0
            # and atm.cpkRad unless == 0.0
            for i,a in enumerate(currentAtoms):
                if a.cpkScale != 1.0:
                    lines += "currentAtoms[%d].cpkScale = %f\n"%(i, a.cpkScale)
                    if not data.has_key(i):
                        data[i] = {}
                    data[i]['cpkScale'] = a.cpkScale
                if a.cpkRad != 0.0:
                    lines += "currentAtoms[%d].cpkRad = %f\n"%(i, a.cpkRad)
                    if not data.has_key(i):
                        data[i] = {}
                    data[i]['cpkRad'] = a.cpkRad
            if addtocmds and len(data):
                cmds.append(("atomdata", data))
            # display CPK with setScale=False
            quality = gc.geoms['cpk'].quality
            atms = gca['cpk']
            reprstring = atms.buildRepr()
            lines += """self.displayCPK('%s', quality=%d, setScale=False)\n"""%(reprstring, quality)
            cmds.append((self.displayCPK, (atms,) , {'quality':quality, 'setScale':False}))

        ##
        ## Ribbons
        ##
        ribbonResidues = ResidueSet([], stringRepr='abc')
        for k, v in gca.items():
            if k[:4] in ['Heli', 'Stra', 'Turn', 'Coil'] and gca[k]:
                ribbonResidues += gca[k]
        if ribbonResidues:
            lines += """self.displayExtrudedSS('%s')\n"""%ribbonResidues.buildRepr()
            cmds.append((self.displayExtrudedSS, (ribbonResidues,), {}))

        ##
        ## Labels
        ##
        def numarr2str(val):
            import numpy
            threshold = numpy.get_printoptions()["threshold"]
            if val.size > threshold:
                numpy.set_printoptions(threshold=val.size)
            valstr = "array(%s ,'%s')" %(numpy.array2string(val, precision =4, separator =",") , val.dtype.char)
            numpy.set_printoptions(threshold=threshold)
            return valstr
        for kw in ('AtomLabels', 'ResidueLabels', 'ChainLabels', 'ProteinLabels'):
            if gca.has_key(kw) and gca[kw]:
                labelGeom = gc.geoms[kw]
                state = labelGeom.getState()
                verts = labelGeom.vertexSet.vertices.array
                lines += "state = %s\n"%str(str(state))
                lines += "from numpy import array\n"
                lines += "verts = %s\n" % numarr2str(verts)
                lines += "state['vertices']=verts\n"
                lines += "labelGeom = self.GUI.VIEWER.FindObjectByName('%s')\n"%(labelGeom.fullName)
                lines += "if labelGeom:\n"
                lines += "    labelGeom.Set(**state)\n\n"
        ## if gca.has_key('AtomLabels') and gca['AtomLabels']:
        ##     p = gc.geoms['AtomLabels'].params
        ##     if p.has_key('properties'):
        ##         lines += "self.labelByProperty('%s',font=%s, format='%s', location='%s', textcolor=%s, properties=%s)\n"%(
        ##             gca['AtomLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['properties']))
        ##         cmds.append((self.labelByProperty, (gca['AtomLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'properties':p['properties']}) )
        ##     elif p.has_key('function'):
        ##         lines += "self.labelByExpression('%s',font=%s, format='%s', location='%s', textcolor=%s, function=%s, lambdaFunc=%s)\n"%(
        ##             gca['AtomLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['function']), p["lambdaFunc"])
                
        ##         cmds.append((self.labelByExpression, (gca['AtomLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'function':['function'], 'lambdaFunc':p["lambdaFunc"]}) )
                
        ## if gca.has_key('ResidueLabels') and gca['ResidueLabels']:
        ##     p = gc.geoms['ResidueLabels'].params
        ##     if p.has_key('properties'):
        ##         lines += "self.labelByProperty('%s',font=%s, format='%s', location='%s', textcolor=%s, properties=%s)\n"%(
        ##             gca['ResidueLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['properties']))
        ##         cmds.append((self.labelByProperty, (gca['ResidueLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'properties':p['properties']}) )
            
        ##     elif p.has_key('function'):
        ##         lines += "self.labelByExpression('%s',font=%s, format='%s', location='%s', textcolor=%s, function=%s, lambdaFunc=%s)\n"%(
        ##             gca['ResidueLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['function']), p["lambdaFunc"])
        ##         cmds.append((self.labelByExpression, (gca['ResidueLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'function':['function'], 'lambdaFunc':p["lambdaFunc"]}) )
        ## if gca.has_key('ChainLabels') and gca['ChainLabels']:
        ##     p = gc.geoms['ChainLabels'].params
        ##     if p.has_key('properties'):
        ##         lines += "self.labelByProperty('%s',font=%s, format='%s', location='%s', textcolor=%s, properties=%s)\n"%(
        ##             gca['ChainLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['properties']))
        ##         cmds.append((self.labelByProperty, (gca['ChainLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'properties':p['properties']}) )
        ##     elif p.has_key('function'):
        ##         lines += "self.labelByExpression('%s',font=%s, format='%s', location='%s', textcolor=%s, function=%s, lambdaFunc=%s)\n"%(
        ##             gca['ChainLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['function']), p["lambdaFunc"])
        ##         cmds.append((self.labelByExpression, (gca['ChainLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'function':['function'], 'lambdaFunc':p["lambdaFunc"]}) )

        ## if gca.has_key( 'ProteinLabels') and gca['ProteinLabels']:
        ##     p = gc.geoms['ProteinLabels'].params
        ##     if p.has_key('properties'):
        ##         lines += "self.labelByProperty('%s',font=%s, format='%s', location='%s', textcolor=%s, properties=%s)\n"%(
        ##             gca['ProteinLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['properties']))
        ##         cmds.append((self.labelByProperty, (gca['ProteinLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'properties':p['properties']}) )
        ##     elif p.has_key('function'):
        ##         lines += "self.labelByExpression('%s',font=%s, format='%s', location='%s', textcolor=%s, function=%s, lambdaFunc=%s)\n"%(
        ##             gca['ProteinLabels'].buildRepr(), str(p['font']), p['format'],
        ##             p['location'], str(p['textcolor']), str(p['function']), p["lambdaFunc"])
        ##         cmds.append((self.labelByExpression, (gca['ProteinLabels'],),
        ##                      {'font':p['font'], 'format':p['format'], 'location':p['location'],
        ##                       'textcolor':p['textcolor'], 'function':['function'], 'lambdaFunc':p["lambdaFunc"]}) )
                
        if hasattr(gc, "msms"):   
            for name in gc.msms.keys():
                if gca[name]:
                    lines += """self.displayMSMS('%s', negate=False, only=False, surfName='%s', nbVert=1)\n"""%(gca[name].buildRepr(), name)
                    cmds.append((self.displayMSMS, (gca[name],),
                                 {'negate':False, 'only':False, 'surfName':name, 'nbVert':1}))

        ##
        ## display coarse molecular surfaces
        ##
        if self.commands.has_key('coarseMolSurface'):
            for geomName in self.coarseMolSurface.surfNameList:
                geom = vi.FindObjectByName('root|%s|%s'%(mol.name, geomName))
                if geom:
                    if gca.has_key(geomName) and gca[geomName]:
                        lines += "self.DisplayBoundGeom('%s', only=True, geomNames=['root|%s|%s'], nbVert=1)\n"%(gca[geomName].buildRepr(), mol.name, geomName)
                        cmds.append( (self.DisplayBoundGeom, (gca[geomName],),
                                      {'only':True, 'geomNames':['root|%s|%s' %(mol.name, geomName)], 'nbVert':1} ))
        ##                
        ## check if molecule is visible:
        ##    
        if not gc.geoms['master'].visible:
            lines += "self.showMolecules(['%s'], negate=1, redraw=1)\n" % (mol.name)
            cmds.append( (self.showMolecules, ([mol.name], ), {'negate':1, 'redraw':1}) )
            
        if mode == "string":
            return lines
        else:
            return cmds


    def getStateCodeForSelection(self):
        ##
        ## restore selection
        ##
        lines = """##n\## restore selection\n##\n"""
        if len(self.selection):
            lines = "self.select('%s')\n"%self.selection.buildRepr()

        return lines

 
    def getCodeForAnimation(self, numfiles, filename="animation"):
        ## Add lines to session.py that will load animation or/and snapshot
        ## sessions
        if numfiles == 0: return None
        lines = """##\n## restore animation\n##\n"""
        lines += """if hasattr(self, 'loadAniMol') and self.loadAniMol==False: pass\n"""
        lines += """else: self.customAnimation.animNB.loadAniMolSession('%s', %d)\n""" % (filename, numfiles)
        return lines


    def readFullSession(self, name):
        """
        read a session file

        None <- mv.readFullSession(self, name)

        name has to be the full path to a .tar.gz file as created by
        mv.saveSession 
        """
        # suspend redraw to save time and avoid flashing
        if self.hasGui:
            self.GUI.VIEWER.suspendRedraw = True
        #print 'restoring session', name

        bname = os.path.basename(name)+'_dir'  # i.e. mysession.psf
        import tempfile
        folder = tempfile.mktemp()
        #sessionFolder = os.path.join(folder, bname)
        #sessionFolder = os.path.join(folder, "*.psf_dir")
        #print 'creating folder', folder
        #os.mkdir(folder)

        # open tar file and extract into folder called name 
        tar = tarfile.open(name)
        #print 'extract to ',folder
        tar.extractall(path=folder)

        # save current directory
        cwd = os.getcwd()
        sessionFolder = os.path.join(folder, os.listdir(folder)[0])
        #print 'going to', sessionFolder
        # go to session folder
        os.chdir(sessionFolder)

        try:
            # execute session.py file inside untar'ed folder
            execfile('./session.py')
            os.chdir(cwd)
            
            # delete the untar'ed folder
            #print 'removing ', name+'_dir'
            self.openedSessions.append(folder)
            #shutil.rmtree(folder)

        finally:
            # allow viewer to redraw
            if self.hasGui :
                self.GUI.VIEWER.suspendRedraw = False


    def writeMoleculeToSessionFolder(self, mol):
        from MolKit.pdbParser import PdbParser, PQRParser, F2DParser, \
             PdbqParser, PdbqtParser, PdbqsParser
        from MolKit.mol2Parser import Mol2Parser
        from MolKit.mmcifParser import MMCIFParser
        from MolKit.groParser import groParser
        from MolKit.pdbWriter import PdbWriter, PdbqWriter, PdbqsWriter, \
             PdbqtWriter
        from MolKit.mmcifWriter import MMCIFWriter

        parser = mol.parser
        filename = mol.getFilename()
        # check if the molecule is a model:
        if parser.model == True:
            molName, ext = os.path.splitext(os.path.basename(filename))
            namel = mol.name.split("_model")
            if len(namel) == 2 and namel[0] == molName:
                filename = mol.name + ext
                mol.modelFilename = filename
        if isinstance(parser, PdbqtParser):
            writer = PdbqtWriter()
            records=['ATOM', 'HETATM', 'CONECT']
            writer.write(filename, mol, records=records)

        elif isinstance(parser, PdbqParser):
            writer = PdbqWriter()
            records=['ATOM', 'HETATM', 'CONECT']
            writer.write(filename, mol, records=records)

        elif isinstance(parser, PdbqsParser):
            writer = PdbqsWriter()
            records=['ATOM', 'HETATM', 'CONECT']
            writer.write(filename, mol, records=records)

        elif isinstance(parser, MMCIFParser):
            writer = MMCIFWriter()
            writer.write(filename, mol)

        else:
            if not isinstance(parser, PdbParser):
                print 'WARNING: no writer for molecule %s, read using %s parser'%\
                      (mol.name, parser.__class__)
                print '         defaulting to PDB format'
            writer = PdbWriter()
            records=['ATOM', 'HETATM', 'CONECT']
            if hasattr(mol, 'builder'):
                records.extend(['HELIX', 'SHEET', 'TURN'])
            #if hasattr(parser, 'PDBtags'):
            #    records = parser.PDBtags
            writer.write(filename, mol, records=records)
 


    def saveFullSession(self, name):
        """
        save a session file

        None <- mv.saveFullSession(self, name)

        create name.psf file. The extension is only added if it is not
        already in name
        """
        ##
        ## we create a file called name.psf. if name is /a/b/c.psf we call
        ## 'c' the basename. The name.psf file is a tar giz'ed directory
        ## containing the directory c.psf_dir in which we store molecules
        ## and a python script called session.py
        ##

        bname = os.path.basename(name)+'_dir'  # i.e. mysession.psf

        # create a temporary folder
        import tempfile
        folder = tempfile.mktemp()
        sessionFolder = os.path.join(folder, bname)
        #print 'creating folder', sessionFolder
        os.mkdir(folder)
        os.mkdir(sessionFolder)

        # create tar object in the location required by user
        #print 'mktar', name
        tar = tarfile.open(name, "w:gz")

        # goto folder 
        cwd = os.getcwd()
        #print 'goto folder', sessionFolder
        os.chdir(sessionFolder)

        try:
            #write all molecules into this file
            # FIXME .. we should use the same writer as the parser i.e. PQR etc
            from MolKit.pdbWriter import PdbWriter
            for mol in self.Mols:
                self.writeMoleculeToSessionFolder(mol)
                
            # write the session file in the folder
            lines = """"""
            for mol in self.Mols:
                lines += self.getStateCodeForMolecule(mol)

            lines += self.getStateCodeForMeasureGeoms()
            
            lines += self.getStateCodeForSets()
            lines += self.getStateCodeForSelection()
            
            if self.commands.has_key('sequenceViewer'):
                lines += self.sequenceViewer.getStateCodeForSeqViewer()
                
            vstate = self.GUI.VIEWER.getViewerStateDefinitionCode('self.GUI.VIEWER')
            ostate = self.GUI.VIEWER.getObjectsStateDefinitionCode('self.GUI.VIEWER')

            # write vision networks
            ed = self.vision.ed
            for name,net in ed.networks.items():
                if len(net.nodes):
                    net.saveToFile(os.path.join(sessionFolder,
                                                net.name+'_pmvnet.py'))
                    
            # add animation script file(animation.py). This file contains
            # Python code for restoring all actions and the Sequence Anim. animation
            # found in AniMol.
            animcode = None
            if self.commands.has_key('customAnimation'):
                #each animation action or snapshot is written in a separate file "animation#.py" 
                numfiles = self.customAnimation.animNB.saveAniMolSession("animation")
                #write code to load animation script and/or snapshots
                animcode = self.getCodeForAnimation(numfiles)

            f = open('session.py', 'w')
            [f.write(line) for line in lines]
            f.write("mode='both'\n")
            [f.write(line) for line in vstate]
            [f.write(line) for line in ostate]

            # add lines to session file to load vision networks
            f.write('ed = self.vision.ed\n')
            for name,net in ed.networks.items():
                if len(net.nodes):
                    f.write("ed.loadNetwork('%s')\n"%(net.name+'_pmvnet.py'))
            if animcode is not None:
                [f.write(line) for line in animcode]

            f.close()

           
            # go to parent folder
            os.chdir(folder)

            # add subdirectory with basename
            tar.add(bname)
            tar.close()
            
        finally:
            # restore original directory
            os.chdir(cwd)
            # delete the temporary folder
            #print 'removing ', folder
            shutil.rmtree(folder)


    def __init__(self, title="Molecule Viewer", logMode='no',
                 libraries=[], gui=1, resourceFile = '_pmvrc',
                 customizer = None, master=None, guiVisible=1,
                 withShell=1, verbose=True, trapExceptions=True):
        """
        * title:
          string used as a title. 
        * logMode:
          string specifying the mode of logging of mv.
            'no': for no loging of commands at all
            'overwrite': the log files overwrite the one from the previous
                         session the log files = mvAll.log.py
            'unique': the log file name include the date and time

        * libraries:
          list of the Python packages containing modules and commands
          that can be loaded in the application. Such a package needs the
          following files : cmdlib.py and modlib.py
        * gui :
          Flag specifying whether or not to run the application with a gui.
        * resourceFile:
          file sourced at startup and where userpreference  made as default
          are saved (default: '.pmvrc')
        * customizer :
          file when specified is sourced at startup instead of the resourceFile
        * master:
          can be specified to run PMV withing another GUI application.
        * guiVisible:
          Flag to specify whether or not to show the GUI.
        - trapExceptions should be set to False when creating a ViewerFramework
          for testing, such that exception are seen by the testing framework
        """
        libraries = ['Pmv', 'Volume','AutoDockTools'] + libraries
        _pmvrc, self.rcFolder = Find_pmvrc(resourceFile)
        if _pmvrc:
            resourceFile = _pmvrc
                    
        if withShell:
            from traceback import print_exception
            
            def print_exception_modified(etype, value, tb, limit=None, file=None):
                """
                Modified version of traceback.print_exception
                Deiconifies pyshell when Traceback is printed
                """
                print_exception(etype, value, tb, limit, file)
                if hasattr(self, 'GUI'):
                    self.GUI.pyshell.top.deiconify()
                if not 'Pmv' in tb.tb_frame.f_code.co_filename:
                    return
                if etype == ImportError:
                    if hasattr(value,'message'):
                        package = value.message.split()[-1]
                        print "Please install " +package + " to fix this problem."
                elif etype == AssertionError:
                    pass
                else:
                    print "\nPlease include this Traceback in your bug report.\n"
            import traceback 
        
            traceback.print_exception = print_exception_modified

        from time import time
        t0 = time()
        ViewerFramework.__init__(self, title, logMode, libraries, gui,
                                 resourceFile, master=master,
                                 guiVisible=guiVisible, withShell=withShell,
                                 verbose=verbose, viewerClass=PMVViewer,
                                 trapExceptions=trapExceptions)
        #print 'time to initialize ViewerFramework', time()-t0
        t0 = time()
        if gui:
            # add a page for Dashboard
            self.GUI.dockDashMaster = self.GUI.toolsNoteBook.insert(
                "DashBoard", 0)
            #button = self.GUI.toolsNoteBook.tab(0)
            button = Tkinter.Radiobutton(
                self.GUI.toolsButtonBarMaster, width=10,
                var=self.GUI.toolsButtonBarTabVar,
                value='Dashbord', indicatoron=False,
                text='Dashboard', font=('Helvetica', '', 10), padx=3, pady=0)
            
            button.pack(side='left', anchor='w')
            def adjustWidth():
                self.GUI.toolsNoteBook.selectpage(0)
                self.dashboard.setNaturalSize()
            button.configure(command=adjustWidth)
                        
        #print 'time to add dashboard page', time()-t0
        t0 = time()
        #if sys.platform == 'win32': #this needed to account for camera size
        #    geometry = '%dx%d+%d+%d' % (800,600, 30, 30)
        #else:
        #    geometry = '%dx%d+%d+%d' % (800,200, 30, 30)    
        #self.GUI.ROOT.geometry(geometry)

        # Establish interface to Visual Programming environment.
        if self.visionAPI is not None:
            # add Molecule, Pmv, Viewer to lookup table
            from Pmv.VisionInterface.PmvNodes import PmvMolecule, PmvNode, \
                 PmvViewer, PmvSetNode, PmvVolume
            self.visionAPI.addToLookup(Protein, PmvMolecule, "Molecules")
            self.visionAPI.addToLookup(MoleculeViewer, PmvNode, "PMV")
            from DejaVu import Viewer
            self.visionAPI.addToLookup(Viewer, PmvViewer, "PMV")
            self.visionAPI.addToLookup(TreeNodeSet, PmvSetNode, "Sets")

            # Note: Molecules are added to the interface in addMolecule() below
            
            # put Pmv instance into list of objects to be added to Vision
            self.visionAPI.add(self, "Pmv", kw={
                'vf':self,
                'constrkw':{'vf':'masterNet.editor.vf'} } )
            # put Pmv Viewer instance in list of objects to be added to Vision
            if self.hasGui:
                self.visionAPI.add(self.GUI.VIEWER, "Pmv Viewer", kw={
                'viewer':self.GUI.VIEWER,
                'constrkw':{'viewer':'masterNet.editor.vf.GUI.VIEWER'} } )

                # add flash spheres geom
                sph = Spheres('flashSphere', vertices=((0,0,0),), radii=(0.3,),
                              visible=0, materials=((0,1,1),))
                self.GUI.VIEWER.AddObject(sph, parent=self.GUI.miscGeom)
                self.flashSphere = sph

                # add flash labels geom
                from DejaVu.glfLabels import GlfLabels
                sca = 2.0
                lab = GlfLabels(
                    'flashLabel', fontStyle='solid3d', pickable=0,
                    fontTranslation=(0,0,3.), fontScales=(sca*.3,sca*.3, .1))
                self.GUI.VIEWER.AddObject(lab, parent=self.GUI.miscGeom)
                lab.applyStrokes()
                self.flashLabel = lab

        #print 'time to add vision', time()-t0
        t0 = time()

        self.openedSessions = []
        
        self.selection = MoleculeSet()  # store current selection
        # replace interactive command caller by MVInteractiveCmdCaller
        # we need the ICmdCaller even if there is no GUI because it has
        # the level variable used byu selection commands
        self.ICmdCaller = MVInteractiveCmdCaller( self )
        from mvCommand import MVSetIcomLevel
        self.addCommand( MVSetIcomLevel(), 'setIcomLevel', None )
        from mvCommand import MVSetSelectionLevel, MVSetSelectionLevelGUI
        self.addCommand( MVSetSelectionLevel(), 'setSelectionLevel',  MVSetSelectionLevelGUI)

        self.setSelectionLevel(Atom, topCommand = 0) #should this be Protein?
        self.setIcomLevel(Atom, topCommand = 0)

        from Pmv.displayCommands import BindGeomToMolecularFragment
        from Pmv.displayCommands import BindGeomToMolecularFragmentGUI
        
        self.addCommand( BindGeomToMolecularFragment(),
                         'bindGeomToMolecularFragment',
                         BindGeomToMolecularFragmentGUI )

#        if self.hasGui:
#            from Pmv.mvCommand import MVPrintNodeNames, MVCenterOnNodes
#            self.addCommand( MVPrintNodeNames(), 'printNodeNames ', None )
#            self.addCommand( MVCenterOnNodes(), 'centerOnNodes', None )

            # load out default interactive command which prints out object
            # names
            #self.ICmdCaller.setCommands( self.printNodeNames )
            

        self.ICmdCaller.go()
        if self.hasGui:    
            # add callback to create picking event
            self.GUI.VIEWER.AddPickingCallback(self.makePickingEvent)

        #print 'time to do stuff 1', time()-t0
        t0 = time()
        
        self.addMVBasicMenus()
        #print 'time to add basic menus', time()-t0
        t0 = time()

        # overwrite camera.actions['Object']['pivotOnPixel'] to call Pmv
        # command to center on picked pixel
        if self.hasGui:
            actions = self.GUI.VIEWER.cameras[0].actions
            actions['Object']['pivotOnPixel'] = self.centerSceneOnPickedPixel
            self.GUI.VIEWER.cameras[0].bindActionToMouseButton(
                'pivotOnPixel', 3, modifier='Control')
                                                                     
        # load out default interactive command
        self.ICmdCaller.setCommands( self.printNodeNames, modifier=None )
        #self.ICmdCaller.setCommands( self.printNodeNames, modifier='Shift_L',
        #                             mode='pick')
        self.ICmdCaller.setCommands( self.select, modifier='Shift_L',
                                     mode='pick')
        self.ICmdCaller.setCommands( self.select, modifier='Shift_L',
                                     mode='drag select')
        self.ICmdCaller.setCommands( self.deselect, modifier='Control_L',
                                     mode='pick')
        self.ICmdCaller.setCommands( self.deselect, modifier='Control_L',
                                     mode='drag select')
        #self.ICmdCaller.setCommands( self.centerOnNodes, modifier='Alt_L' )

        #print 'time to do stuff 2', time()-t0
        t0 = time()

        self.Mols = MoleculeSet() # store the molecules read in
        self.objects = self.Mols
        from MolKit.sets import Sets
        self.sets = Sets()  # store user-defined sets in this dict

        # lock needs to be acquired before volume can be added
        self.volumesLock = thread.allocate_lock()

        self.Vols = [] # list of Grid3D objects storing volumetric data
        if self.visionAPI is not None:
            from Volume.Grid3D import Grid3D
            self.visionAPI.addToLookup(Grid3D, PmvVolume, "Volumes")

        #print 'time to do stuff 3', time()-t0
        t0 = time()

        self.allAtoms = AtomSet() # set of all atoms (across molecules)

        #if self.hasGui:
        #    from Pmv.controlPanelCommands import ControlPanel,ControlPanel_GUI
        #    self.addCommand(ControlPanel(), "controlPanel",ControlPanel_GUI)

        #add choices for loadMolecule (pdbParser) : modelsAs: can be set to 'molecules', 'chains', 'conformations'
        #'chains' is not yet implemented (7/09)

        choices = ['molecules', 'chains',
                   'conformations']
        choice = 'molecules'
        self.userpref.add('Read molecules as', choice, validValues=choices,
                          category="Molecules",
                          doc = """for pdb file with nulti MODEL, can be read as 'molecules', 'chains', 'conformations'.chains' is not yet implemented (7/09)""")

        choices = ['caseSensitive', 'caseInsensitive',
                   'caseInsensWithEscapedChars']

        self.userpref.add('String Matching Mode', 'caseSensitive', validValues=choices,
                          doc = """When set to caseSensitive the string match
mode will be case sensitive the other possibility is to be case insensitive or
case insensitive with escaped characters.
""")
        choices = ["none", "crosses", "spheres"]
        self.userpref.add('Selection Object', "crosses", validValues=choices,
                          category="Molecules",
                          callbackFunc = [self.changeSelectionObject],
                          doc = """Specifies which object to use for selections. Possible values are none, spheres, crosses. 
If set to none, no changes are visible in the viewer when doing selection.""")
        choices = [1,0]
        self.userpref.add('Exception for Missing Key', 1, validValues=choices,
                          callbackFunc = [self.setRaiseException],
                          doc = """When set to 1 an exception will be raised
is a a key is not found in a dictionnary (MolKit).
""")
        
        choices = [1, 0]
        self.userpref.add('Expand Node Log String', 0, validValues=choices,
                          category="Molecules",
                          doc = """When set to 1 the log string representing
the node argument of a doit will be expanded to the full name of each element
of the TreeNodeSet, when set to 0 the log string representing the node argument
of a doit will be 'self.getSelection()'. In the last case the command log will
depend on the current selection.""")

        # overwrite firstObject only with firstMoleculeOnly
        self.userpref['Center Scene']['validValues'][0] = 'firstMoleculeOnly'
        self.userpref.set('Center Scene', 'always')
        
        choices = ['yes','no']
        choice = 'yes'
        if sys.platform == 'darwin':
            choice = 'no'
        self.userpref.add('Depth Cueing', choice, validValues=choices, category="DejaVu",
                          callbackFunc = [self.setDepthCueing],
                          doc = """ When set to 'yes' the depthCueing is
turned on by default""")

        doc = """When set to yes a warning message is displayed when an empty
selection is about to be expanded to all the  molecules loaded in the 
application"""
        self.userpref.add('Warn on Empty Selection', 'no', validValues=choices, doc=doc)

        #print 'time to do stuff 4', time()-t0
        t00 = t0 = time()

        if self.hasGui:
            self.GUI.VIEWER.suspendRedraw = True
    
            self.GUI.drop_cb = self.drop_cb
            self.GUI.pickLabel.bind("<Button-1>",self.setSelectionLevel.popup)
            if self.userpref['Depth Cueing']['value']=='yes':
                self.GUI.VIEWER.currentCamera.fog.Set(enabled=1, tagModified=False)
            else:
                self.GUI.VIEWER.currentCamera.fog.Set(enabled=0, tagModified=False)                

            if title != 'AutoDockTools':
                toolbarDict = {}
                toolbarDict['name'] = 'ADT'
                toolbarDict['type'] = 'Checkbutton'
                toolbarDict['icon1'] = 'adt.png'
                toolbarDict['balloonhelp'] = 'AutoDock Tools'
                toolbarDict['icon_dir'] = ICONPATH
                toolbarDict['index'] = 7
                toolbarDict['cmdcb'] = self.Add_ADT
                toolbarDict['variable'] = None
                self.GUI.toolbarList.append(toolbarDict)
            self.GUI.configureToolBar(self.GUI.iconsize)
            # overwrite unsollicited picking with a version that prints atom names
            #self.GUI.VIEWER.RemovePickingCallback("unsolicitedPick")
            #self.GUI.VIEWER.AddPickingCallback(self.unsolicitedPick)

            #print 'time to do stuff 5', time()-t0
            t0 = time()

            # check if  AutoDockFR package can be imported,
            # add a button to the toolbar to load AutoDockFRCommands
            foundADTFR = False
            try:
                import AutoDockFR
                foundADTFR = True
            except:
                pass
            if foundADTFR:
                # add the button:
                adFRtoolbarDict = {'name': "AutoDockFR", 'type':'Checkbutton',
                              'icon1':'ADFR.png','balloonhelp':'AutoDockFR',
                              'icon_dir':ICONPATH, 'index':15,
                              'cmdcb':self.Add_AutoDockFR,
                              'variable':None}
                self.GUI.toolbarList.append(adFRtoolbarDict)
                self.GUI.configureToolBar(self.GUI.iconsize)

            #from Pmv.updateCommands import Update, UpdateGUI
            #self.addCommand( Update(), 'update', UpdateGUI )
    
            from Pmv.aboutCommands import About, AboutGUI
            self.addCommand( About(), 'about', AboutGUI )
    
            #self.GUI.vwrCanvasFloating.bind('<Delete>', self.deleteAtomSet.guiCallback)
            # load clear selection command because dashboard buttton uses it
            self.browseCommands ('selectionCommands', package='Pmv',
                                 commands=['clearSelection'],
                                 topCommand=0)
            self.browseCommands ('dashboardCommands', package='Pmv', topCommand=0)
            #self.browseCommands ('stylesCommands', package='Pmv', topCommand=0)

        #print 'time to do stuff 6', time()-t0
        t0 = time()
        #self.browseCommands('seqViewerCommands',package='Pmv', topCommand=0)

        #if self.hasGui:
        #    self.GUI.ROOT.bind('<Delete>', self.deleteAtomSet.guiCallback)
        self.userpref.loadSettings()
        #print 'time to do stuff 7', time()-t0
        t0 = time()

        self.customize(customizer)
        #print 'time to do stuff 8', time()-t0
        t0 = time()
        #rcFile = getResourceFolderWithVersion()
        #if rcFile:
        #    rcFile += os.sep + 'Pmv' + os.sep + "recent.pkl"
            
        if self.hasGui:
            #fileMenu = self.GUI.menuBars['menuRoot'].menubuttons['File'].menu
            # 
            #self.recentFiles = RecentFiles(self, fileMenu, filePath=rcFile, 
            #                               menuLabel = 'Recent Files')
            try:
                from DejaVu.Camera import RecordableCamera
                if isinstance(self.GUI.VIEWER.cameras[0], RecordableCamera):
                    from Pmv.videoCommands import VideoCommand, VideoCommandGUI 
                    self.addCommand(VideoCommand(), 'videoCommand', VideoCommandGUI)
            except:
                pass
                #print "Recordable camera is not available"
            #print 'time to do stuff 2', time()-t0
            t0 = time()

            #if self.commands.has_key('dashboard') and \
            #       len(self.dashboard.tree.columns)==0:
                # this warning is wrong, it appears during test_pmvscript
                #print "WARNING: update your _pmvrc file to load the dashboard commands"
                #these are now loaded through _pmvrc
                #from Pmv.dashboard import loadAllColunms
                #loadAllColunms(self)

        
            #from Pmv.commander import PmvCommander
            #cmd = PmvCommander(self)
            #cmd.topFrame.pack(expand=1, fill='both')

        if self.hasGui and self.commands.has_key('dashboard'):
            from Pmv.dashboard import SelectionWithButtons, \
                 LigandAtomsWithButtons, WaterWithButtons, \
                 MoleculeSetNoSelection, IonsWithButtons, \
                 DNAWithButtons, RNAWithButtons, STDAAWithButtons
            
            from mglutil.gui.BasicWidgets.Tk.trees.TreeWithButtons import \
                 NodeWithoutButtons
            
            ## add line to dashboard for current selection
            ##
            selection = MoleculeSetNoSelection()
            ## give the MoleculeSet a name to be displayed in the Dashboard
            selection.setSetAttribute('name', 'Current Selection')
            selection.setSetAttribute('treeNodeClass', SelectionWithButtons)
            self.dashboard.onAddObjectToViewer(selection)

            ## ##
            ## ## add a line for special sets
            ## spSets = MoleculeSet()
            ## spSets.setSetAttribute('elementType', MoleculeSet)
            ## spSets.setSetAttribute('name', 'Special Sets')
            ## spSets.setSetAttribute('treeNodeClass', NodeWithoutButtons)
            ## # object needs to have .children attribute for expandable icon
            ## spSets.setSetAttribute('children', spSets.data)
            ## spSets.setSetAttribute('treeIconName', 'set.png')
            ## self.dashboard.onAddObjectToViewer(spSets)
            
            ## ##
            ## ## add a special set for water atoms
            ## waters = MoleculeSet()
            ## waters.setSetAttribute('name', 'Water')
            ## waters.setSetAttribute('treeNodeClass', WaterWithButtons)
            ## #self.dashboard.onAddObjectToViewer(water, parent=spSets)
            ## spSets.append(waters)

            ## ##
            ## ## add a special set for ions
            ## ions = MoleculeSet()
            ## ions.setSetAttribute('name', 'Ions')
            ## ions.setSetAttribute('treeNodeClass', IonsWithButtons)
            ## #self.dashboard.onAddObjectToViewer(water, parent=spSets)
            ## spSets.append(ions)

            ## ##
            ## ## add a special set for DNA
            ## dna = MoleculeSet()
            ## dna.setSetAttribute('name', 'DNA')
            ## dna.setSetAttribute('treeNodeClass', DNAWithButtons)
            ## #self.dashboard.onAddObjectToViewer(water, parent=spSets)
            ## spSets.append(dna)

            ## ##
            ## ## add a special set for RNA
            ## rna = MoleculeSet()
            ## rna.setSetAttribute('name', 'RNA')
            ## rna.setSetAttribute('treeNodeClass', RNAWithButtons)
            ## #self.dashboard.onAddObjectToViewer(water, parent=spSets)
            ## spSets.append(rna)

            ## ##
            ## ## add a special set for amino acids
            ## rna = MoleculeSet()
            ## rna.setSetAttribute('name', 'Amino Acids')
            ## rna.setSetAttribute('treeNodeClass', STDAAWithButtons)
            ## #self.dashboard.onAddObjectToViewer(water, parent=spSets)
            ## spSets.append(rna)

            ## ##
            ## ## add a special set for hetero atoms under special sets
            ## hetero = MoleculeSet()
            ## hetero.setSetAttribute('name', 'Ligand')
            ## hetero.setSetAttribute('treeNodeClass', LigandAtomsWithButtons)
            ## hetero.top = self.dashboard.system
            ## hetero.parent = spSets
            ## spSets.append(hetero)
            #print 'time to do stuff 10', time()-t0
            t0 = time()

            # add AniMol command:
            if self.hasGui:
                #g = CommandGUI()
                g = None
                from ViewerFramework.basicCommand import customAnimationCommand
                self.addCommand(customAnimationCommand(), 'customAnimation', g)

        #print 'time to do stuff 11', time()-t0
        t0 = time()

        # load tools such as measure and display thigns by picking
        self.browseCommands('measureCommands',package='Pmv', topCommand=0)
        self.browseCommands('pickingToolsCommands',package='Pmv', topCommand=0)
        if not self.commands.has_key('displayLines'):
            self.browseCommands('displayCommands', commands=['displayLines',],  package='Pmv', topCommand=0)
        #if not self.commands.has_key('sequenceViewer'):
        #    self.browseCommands('seqViewerCommands', package='Pmv', topCommand=0)
        if not self.commands.has_key('colorByMolecules'):
            self.browseCommands('colorCommands',package='Pmv', topCommand=0)
        self.cmdsWithOnAddObj.extend([
            self.dashboard, self.displayLines,
            #self.sequenceViewer,
            self.colorByMolecules,
            ]) 
        #print 'time to do stuff 12', time()-t0
        #print 'Total time', time()-t00
       
        def findPossibleWidth(width):
            # try to guess monitor width
            import sys
            knownWidth = [ 1024, 1152, 1280, 1366, 1440, 1600,
                           1680, 1920]
            if sys.platform=='darwin':
                knownWidth.extend( [2048, 2560] )

            widths = {}
            mini = width
            #check for same size monitors
            for w1 in knownWidth:
                if width%w1==0:
                    widths[width/w1] = [w1]
                    if w1<mini: mini = w1
            # check for 2 monitors with with different size
            for i, w1 in enumerate(knownWidth[:-1]):
                for w2 in knownWidth[i+1:]:
                    if width==w1+w2:
                        if widths.has_key(2):
                            widths[2].append( (w1,w2) )
                        else:
                            widths[2] = [ (w1,w2) ]
                        if w1<mini: mini = w1
            return widths, mini

        if self.hasGui:
            if self.userpref.has_key('Save Perspective on Exit'):
                if not self.restorePerspective() or \
                     self.userpref['Save Perspective on Exit']['value']=='no':
                    width = self.GUI.screenWidth
                    if self.GUI.screenWidth>2000: #2 screens
                        width = findPossibleWidth(self.GUI.screenWidth)[1]
                    height = min(1024, self.GUI.screenHeight)
                    #print width, height
                    self.GUI.ROOT.geometry("%dx%d+20+20"%(width*.9, height*.9))
##                     top = self.GUI.ROOT.winfo_toplevel()
##                     geom = top.geometry()
##                     print 'GOGO1', geom
##                     geom = geom.split('x')
##                     self.GUI.menuBars['Toolbar']._frame.update_idletasks()
##                     winfo_width = self.GUI.menuBars['Toolbar']._frame.winfo_width()        
##                     if int(geom[0]) < winfo_width + 10:
##                         geom[0] = str(winfo_width + 10)
##                     print 'fogo', geom[0]+'x'+geom[1]
##                     top.geometry(geom[0]+'x'+geom[1])   
##                     if not trapExceptions and customizer == './.empty':
##                         top.update_idletasks()
##                         top.deiconify()  
##                         #self.GUI.vwrCanvasFloating.deiconify()
##                     self.GUI.naturalSize()
##                     print 'GOGO1', geom, self.GUI.ROOT.geometry()


        if self.hasGui:
            self.GUI.VIEWER.suspendRedraw = False


    def cleanCmdStack(self, command, molecule):
        # 'command' is either self.vf.NEWundo or self.vf.redo
        # when a molecule is deleted in an not undoable way we need to
        # remove references to this molecule from the undo/redo cmd stack

        #go over the stored commands (commmand.cmdStack) and remove the ones that 
        # contain given molecule in their argument tuples.
        removedEntries = [] # will contain indices of entries that need to be
                            # removed from command.cmdStack
        #print "cleaning up %s  cmdStack" % command.name
        from MolKit.tree import TreeNode, TreeNodeSet

        # loop over undo/redo comand stack
        for i, cmdEntry in enumerate(command.cmdStack):
            cmdList = cmdEntry[0] # get a handle to (cmd *args, **kw)
            remove = False
            # loop over commands in this undo block
            for j, cmd in enumerate(cmdList):
                if remove: break
                for arg in cmd[1]: # FIXME this loop might not be necessary
                                   # if the only place for molecular fragments
                                   # is the first argument

                    #if the arg is a molecular fragment
                    if isinstance(arg, TreeNode):
                        if arg.top==molecule:
                            removedEntries.append(i)
                            remove = True
                            break
                        
                    elif isinstance(arg, TreeNodeSet):
                        deleted = molecule.findType(arg.elementType)
                        new = arg - deleted
                        if len(new)==0:
                            removedEntries.append(i)
                            remove = True
                            break
                        #else:
                            # replace arg that contains reference to this molecule and some other
                            # molecule(s) by new.  
                            #cmdList[j] = (cmdList[j][0], (new,), cmdList[j][2])
                            # FIXME: this is not sufficient , we need to find a way to
                            # check all kw of the command to see if they contain vectors of colors, etc
                            # for this molecule.
                            #for now we remove all cmdStack entries containig reference to this molecule.
                        elif new == arg:
                            remove = False
                            break
                        else:
                            removedEntries.append(i)
                            remove = True
                            break
                    else: #not  TreNodeSet , not TreNode
                        #FIX ME (ex: AddBondsCommand takes a list of atom pairs ....
                        # maybe there are more cases like this one)
                        # remove it - for now
                        removedEntries.append(i)
                        remove = True
                        break
        # remove selected entries
        n = 0
        for i in removedEntries:
            command.cmdStack.pop(i-n)
            n = n+1
        
        command.setLabel()


    def focusCameraNodes(self, nodes, scale=1, name="", vector=None):
        molecules, atomSets = self.getNodesByMolecule(nodes, Atom)
        coords= []
        for mol,atoms in zip(molecules, atomSets):
            coords.extend( self.getTransformedCoords(mol, atoms.coords))
        self.focusCameraCoords(coords, scale=scale, name=name, vector=vector)


    def focusCameraCoords(self, coords, scale=1, name="", vector=None):
        # this method is also used in Pmv/seqDisplay.py
        mini = numpy.min( coords, 0)
        maxi = numpy.max( coords, 0)
        vi = self.GUI.VIEWER

        vi.FocusOnBox(vi.rootObject, mini-6, maxi+6, vector=vector)

        # add flash spheres
        from DejaVu.Spheres import Spheres
        sph = Spheres('highlightFocus', vertices=coords, radii=(0.2,),
                      opacity=0.99, transparent=1, inheritMaterial=0,
                      materials=[(0,1,1),], visible=0)
        vi.AddObject(sph)
        sph.applyStrokes()

        # add flash label
        if name:
            lab = GlfLabels(
                'flashLabel', fontStyle='solid3d', fontTranslation=(0,0,3.),
                fontScales=(scale*.3,scale*.3, .1), pickable=0, labels=[name],
                vertices=[numpy.sum(coords, 0)/len(coords)], visible=0)
            vi.AddObject(lab)
            lab.applyStrokes()

            #sph.fadeOut()
            cb = CallbackFunction(self.afterFlash_cb, sph)
            sph.flashT(interval=20, after_cb=cb)
            cb = CallbackFunction(self.afterFlash_cb, lab)
            lab.flashT(interval=20, after_cb=cb)


    def afterFlash_cb(self, geom):
        self.GUI.VIEWER.RemoveObject(geom)


    def makePickingEvent(self, pick):
        if pick.mode=='pick':
            event = PickingEvent(pick)
        elif pick.mode=='drag select':
            event = DragSelectEvent(pick)
        self.dispatchEvent(event)


    def drop_cb(self, files):
        for file in files:
            self.readMolecule(file)
        
    #def getSelectionLevel(self):
    #    return self.selection.elementType
            

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
            mol = filter(lambda x: x.name in name, self.Mols)
        else : 
            mols = filter(lambda x: x.name == name, self.Mols)
            if len(mols):
                mol = mols[0]
            else:
                mol = None
        return mol

    def setRaiseException(self, name, oldval, val):
        import MolKit.molecule
        MolKit.molecule.raiseExceptionForMissingKey = val


    def unsolicitedPick(self, pick):
        """treat an unsollicited picking event"""
        
        if pick is None: return
        vi = self.GUI.VIEWER
        if vi.isShift() or vi.isControl():
            vi.unsolicitedPick(pick)
        else:
            atom = self.findPickedAtoms(pick)
            if atom:
                level = self.ICmdCaller.level.value
                if level == Molecule: level = Protein
                node = atom.findType(level)
                for n in node:
                    self.message( n.full_name() )


    def loadMoleculeIfNeeded(self, filename):
        """load a molecule only if it doesn't exist yet in Pmv, else it
        aborts silent"""

        if not os.path.exists(filename):
            print 'Error! %s not found!'%filename
            return
        
        # find what name would be
        name = os.path.split(filename)[-1]
        try:
            spl = split(name, '.')
        except:
            spl = [name]
        name = spl[0]

        # ask if name already used
        if self.Mols:
            for mol in self.Mols.data:
                if name == mol.name:
                    # break and return mol
                    return mol
        
        # else load molecule
        if not hasattr(self, 'readMolecule'):
            self.browseCommands(
                'fileCommands',
                commands=['readMolecule'], package='Pmv', topCommand=0)

        mol = self.readMolecule(filename)
        return mol
        
        
    def addMolecule(self, newmol, ask=1):
        """
        Add a molecule to this viewer
        """
        #IN ANY CASE: change any special characters in name to '-'
        from MolKit.molecule import Molecule
        if self.hasGui:
            Molecule.configureProgressBar = self.GUI.progressBarConf
            Molecule.updateProgressBar = self.GUI.progressBarUpd
        
        spChar=['?','*','.','$','#',':','-',',']        
##         spChar=['?','*','.','$','#',':','_',',']        
        for item in spChar:
            newmol.name = replace(newmol.name,item,'_')
##             newmol.name = replace(newmol.name,item,'-')
        if len(self.Mols) > 0:
            if newmol.name in self.Mols.name:
                if ask==1: 
                    from mglutil.gui.InputForm.Tk.gui import InputFormDescr
                    idf = self.ifd = InputFormDescr(title = '')
                    idf.append({'widgetType':Pmw.EntryField,
                                'name':'newmol',
                                'required':1,
                                'wcfg':{'labelpos':'w',
                                        'label_text':'New Name: ',
                                        'validate':None,
                                        'value':'%s-%d'%(newmol.name,
                                                         len(self.Mols))},
                                'gridcfg':{'sticky':'we'}})

                    vals = self.getUserInput(idf)
                    if len(vals)>0:
                        assert not vals['newmol'] in self.Mols.name
                        newmol.name = vals['newmol']
                    else:
                        return None
                else:
                    newmol.name='%s_%d'%(newmol.name,len(self.Mols))

        newmol.allAtoms.setStringRepr(newmol.full_name()+':::')
        
        # provide hook for progress bar
        # old code: newmol.allAtoms._bndIndex_ = range(len(newmol.allAtoms))

        allAtomsLen = len(newmol.allAtoms)
        if allAtomsLen == 0:
            tkMessageBox.showwarning("Empty molecule",  "No atom record found for %s\nSee Python Shell for more info." % newmol.name)
            return None
        if self.hasGui:
            self.GUI.configureProgressBar(init=1, mode='increment',
                                      max=allAtomsLen,
                                      labeltext='add molecule to viewer')
        i = 0
        for a in newmol.allAtoms:
            a._bndIndex_ = i
            if self.hasGui:
                self.GUI.updateProgressBar()
            i = i + 1

        g = None
        if self.hasGui:
            g = MolGeomContainer( newmol, self )
        else:
            g = MolGeomContainer( newmol, None)

        if hasattr(newmol, 'spaceGroup'):
            self.browseCommands ('crystalCommands', package='Pmv', topCommand=0)
        newmol.unitedRadii = None # set to None to force initial radii assignment
        nchains = len(self.Mols.chains)
        for i, c in enumerate(newmol.chains):
            c.number = nchains+i
            
        # addObject calls updateProgressBar on its own
        self.addObject('mol%s'%len(self.Mols), newmol, g)

        self.Mols.setStringRepr(self.Mols.full_name())

        # add object to visionAPI (to add them as nodes to Vision library)
        if self.visionAPI:
            self.visionAPI.add(newmol, newmol.name, kw={
                'molecule':newmol,
                'constrkw':{
                    'molecule':
                    'masterNet.editor.vf.expandNodes("%s")[0]'%newmol.name} } )

        self.allAtoms = self.allAtoms + newmol.allAtoms
        self.allAtoms.setStringRepr(self.Mols.full_name()+':::')
        
        #used by cpk command to decide whether or not to compute radii
        event = AddObjectEvent(newmol)
        self.dispatchEvent(event)
        return newmol


    def addVolume(self, name, grid):
        # FIXME we need to check for name unicity and have a repalcement policy

        #self.volumesLock.acquire()
        self.Vols.append(grid)
        grid.name = name
        #self.volumesLock.release()

        if self.visionAPI:
            self.visionAPI.add(grid, name, kw={
                'grid':grid,
                'constrkw':{
                    'grid':
                    'masterNet.editor.vf.gridFromName("%s")[0]'%grid.name} } )

    
    def getSelection(self):
        # FIXME why not return self.Mols always on empty selection ??
        # this should speed thing up
        #ICmdCallerLevel = self.ICmdCaller.level.value
        selLevel = self.selectionLevel

        if len(self.selection)==0:
            # empty selection
            if self.userpref['Warn on Empty Selection']['value']=='yes':
                if self.askOkCancelMsg('expand empty selection to all molecules?'):
                    #selection = self.Mols.findType(selLevel)#, uniq=1)
                    return self.Mols.copy()
                    #try:
                    #    selection = self.Mols.findType(selLevel)#, uniq=1)
                    #except:
                    #    if selLevel==Molecule:
                    #        selection = self.Mols.findType(Protein)
                    #return selection
                else:
                    #selection = self.Mols.findType(selLevel)#, uniq=1)
                    return self.Mols.copy()
                    #try:
                    #    selection = self.Mols.findType(selLevel)#, uniq=1)
                    #except:
                    #    if selLevel==Molecule:
                    #        selection = self.Mols.findType(Protein)
                    #return selection
            else:
                #selection = self.Mols.findType(selLevel)#, uniq=1)
                return self.Mols.copy()
                #try:
                #    selection = self.Mols.findType(selLevel)#, uniq=1)
                #except:
                #    if selLevel==Molecule:
                #        selection = self.Mols.findType(Protein)
                #return selection
                
        else:
            # not empty select
            #try:
            #    selection = self.selection.findType(selLevel, uniq=1)
            #except:
            #    if selLevel==Molecule:
            #        selection = self.selection.findType(Protein)
            return self.selection.copy()
            #selection = self.selection.findType(selLevel, uniq=1)
            #return selection

##             if self.userpref['warnOnEmptySelection']['value']=='yes':
##                 if self.askOkCancelMsg('expand empty selection to all molecules?'):
##                     selection = self.Mols.findType(selLevel)#, uniq=1)
##                     #try:
##                     #    selection = self.Mols.findType(selLevel)#, uniq=1)
##                     #except:
##                     #    if selLevel==Molecule:
##                     #        selection = self.Mols.findType(Protein)
##                     return selection
##                 else:
##                     selection = self.Mols.findType(selLevel)#, uniq=1)
##                     #try:
##                     #    selection = self.Mols.findType(selLevel)#, uniq=1)
##                     #except:
##                     #    if selLevel==Molecule:
##                     #        selection = self.Mols.findType(Protein)
##                     return selection
##             else:
##                 selection = self.Mols.findType(selLevel)#, uniq=1)
##                 #try:
##                 #    selection = self.Mols.findType(selLevel)#, uniq=1)
##                 #except:
##                 #    if selLevel==Molecule:
##                 #        selection = self.Mols.findType(Protein)
##                 return selection
                
##         else:
##             # not empty select
##             #try:
##             #    selection = self.selection.findType(selLevel, uniq=1)
##             #except:
##             #    if selLevel==Molecule:
##             #        selection = self.selection.findType(Protein)
##             selection = self.selection.findType(selLevel, uniq=1)
##             return selection
            

    def getItems(self, selString=""):
        """Takes a string and returns a TreeNodeSet
The string  can contain a series of set descriptors with operators
separated by / characters.  There is always a first set, followed by pairs of
operators and sets.  All sets have to describe nodes of the same level.
example:
    '1crn:::CA*/+/1crn:::O*' describes the union of all CA ans all O in 1crn
    '1crn:::CA*/+/1crn:::O*/-/1crn::TYR29:' 
"""
        assert type(selString)==StringType
        return self.expandNodes(selString)
            
        
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

        elif type(nodes)==StringType:
            stringRepr = nodes
            css = CompoundStringSelector()
            result = css.select(self.Mols, stringRepr)[0]
##            setsStrings = stringRepr.split('/')
##            getSet = self.Mols.NodesFromName
##            result = getSet(setsStrings[0])
##            for i in range(1, len(setsStrings), 2):
##                op = setsStrings[i]
##                arg = setsStrings[i+1]
##                if op=='|': # or
##                    result += getSet(arg)
##                elif op=='-': # subtract
##                    result -= getSet(arg)
##                elif op=='&': # intersection
##                    result &= getSet(arg)
##                elif op=='^': # xor
##                    result ^= getSet(arg)
##                elif op=='s': # sub select (i.e. select from previous result)
##                    result = result.get(arg)
##                else:
##                    raise ValueError, '%s bad operation in selection string'%op
##            result.setStringRepr(stringRepr)

        elif isinstance(nodes,TreeNodeSet):
            result = nodes
        else:
            raise ValueError, 'Could not expand nodes %s\n'%str(nodes)
        
        return result

        
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
        if isinstance(nodes, MoleculeSet) or isinstance(nodes, ProteinSet):
            if nodeType is Atom:
                atms = []
                for mol in nodes:
                    atms.append(mol.allAtoms)
                return nodes, atms
            elif (nodeType is Protein) or (nodeType is Molecule):
                return nodes, nodes
        
        # if it is a string, get a bunch of nodes from the string
        if type(nodes)==StringType:
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

            #stringRepr = nodes.getStringRepr()
            #if stringRepr:
            #    if ':' in stringRepr:
            #        mol_nodes.setStringRepr(
            #            mol.name+stringRepr[stringRepr.index(':'):])
            #    else:
            #        mol_nodes.setStringRepr(stringRepr)

            nodeSets.append( mol_nodes )

        return molecules, nodeSets


    def addMVBasicMenus(self):
        from Pmv.selectionCommands import MVSelectCommand, MVDeSelectCommand
        from Pmv.mvCommand import MVPrintNodeNames, MVCenterOnNodes
        self.addCommand( MVPrintNodeNames(), 'printNodeNames' )
        self.addCommand( MVSelectCommand(), 'select' )
        self.addCommand( MVDeSelectCommand(), 'deselect' )
        self.addCommand( MVCenterOnNodes(), 'centerOnNodes' )


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
            instances = map(lambda x: x[1], values)
            vertInds = map(lambda x: x[0], values)

            # only geometry bound to molecules is packable in PMV
            if not hasattr(obj, 'mol') or len(vertInds)<1:
                continue

            # only vertices of geometry have a mapping to atoms
            # for other types we return an empty atom set
            if pick.type!='vertices':
                return allatoms

            g = obj.mol.geomContainer

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
        
    def Add_ADT(self):
        """Adds AutoToolsBar"""
        if self.GUI.toolbarCheckbuttons['ADT']['Variable'].get():
            #if self.GUI.menuBars.has_key('AutoTools4Bar'):
            #    self.GUI.menuBars['AutoTools4Bar'].pack(fill='x',expand=1)
            if hasattr(self.GUI, 'currentADTBar'):
                self.GUI.menuBars[self.GUI.currentADTBar].pack(fill='x',expand=1)
            else:
                self.browseCommands('autotors41Commands', commands = None, 
                                        package = 'AutoDockTools')
                self.browseCommands('autoflex41Commands', commands = None, 
                                     package = 'AutoDockTools')
                self.browseCommands('autogpf41Commands', commands = None, 
                                        package = 'AutoDockTools')
                self.browseCommands('autodpf41Commands', commands = None, 
                                        package = 'AutoDockTools')
                self.browseCommands('autostart41Commands', commands = None, 
                                        package = 'AutoDockTools')
                self.browseCommands('autoanalyze41Commands', commands = None, 
                                        package = 'AutoDockTools')
                self.GUI.currentADTBar = 'AutoTools41Bar'
                from AutoDockTools import setADTmode
                setADTmode('AD4.2', self)
                self.GUI.adt41ModeLabel.bind("<Double-Button-1>", self.ADTSetMode.guiCallback)
                self.GUI.menuBars[self.GUI.currentADTBar]._frame.master.config({'bg':'tan', 'relief':'flat', 'height':24})
                self.GUI.menuBars[self.GUI.currentADTBar]._frame.config({'bg':'tan','height':24})
                #setADTmode('AD4.2', self)
                #setADTmode('AD4.1', self)
                self.ADTSetMode.Close_cb()
        else:
            #self.GUI.menuBars['AutoToolsBar'].pack_forget()
            self.GUI.menuBars[self.GUI.currentADTBar].pack_forget()


    def Add_AutoDockFR(self):
        if self.GUI.toolbarCheckbuttons["AutoDockFR"]["Variable"].get():
            if self.GUI.menuBars.has_key("AutoDockFRBar"):
                self.GUI.menuBars["AutoDockFRBar"].pack(fill='x',expand=1)
            else:
                self.browseCommands("AutoDockFRCommands", commands = None, 
                                        package = "AutoDockFR")
        else:
            if self.GUI.menuBars.has_key("AutoDockFRBar"):
                self.GUI.menuBars["AutoDockFRBar"].pack_forget()

            
    def changeSelectionObject(self, name, oldval, newval):
        """Callback for userpref 'Selection Object'"""
        if oldval != newval:
            if len(self.selection) !=0:
                self.userpref['Selection Object']['value'] = oldval
                nodes = self.selection.copy()
                self.clearSelection()
                self.userpref['Selection Object']['value'] = newval
                self.select(nodes)


    def setDepthCueing(self, name, oldval, newval):
        """Callback for userpref 'Depth Cueing'"""
        if not hasattr(self, 'GUI'): return
        if newval == 'yes':
            self.GUI.VIEWER.currentCamera.fog.Set(enabled=1, tagModified=False)
        else:
            self.GUI.VIEWER.currentCamera.fog.Set(enabled=0, tagModified=False)
        self.GUI.VIEWER.OneRedraw()


    def  getTransformedCoords(self, mol, coords):
        """ Get transformation matrix of the molecule and apply it to
        coords"""
        import numpy
        # get a handle on the master geometry
        mg = mol.geomContainer.masterGeom
        matrix = mg.GetMatrix(mg)
        # Transpose the transformation matrix.
        trMatrix = numpy.transpose(matrix)
        # Transform coords into homogeneous coords.
        hCoords = numpy.concatenate((coords, numpy.ones( (len(coords), 1), 'd')), 1)
        tCoords = numpy.dot(hCoords, trMatrix)
        return tCoords[:,:3]

                
def Find_pmvrc(resourceFile):
    """
    This function tries to find resource file for Pmv in the User Home folder. 
    If it can't find one, it will copy it from Pmv._pmvrc
    """
    import mglutil
    try:            
        reload(mglutil) # this is needed for updates
    except RuntimeError, e:
        print "# this is needed for updates: unable to reload mglutil\n", e
    lResourceFolderWithVersion = getResourceFolderWithVersion()
    if lResourceFolderWithVersion is not None:
        pmvrcFolder = lResourceFolderWithVersion + os.sep + 'Pmv'
        if not os.path.exists(pmvrcFolder):
            os.mkdir(pmvrcFolder)
        pmvrcFile = pmvrcFolder + os.sep + resourceFile
        if not os.path.exists(pmvrcFile):
            file_out = open(pmvrcFile,'w')
            import Pmv
            file_in = open(Pmv.__path__[0] + os.sep + resourceFile )
            file_out.write(file_in.read())
        #print "Resource file used to customize PMV: "+pmvrcFile
        return pmvrcFile, pmvrcFolder
    else:
        lPath = os.path.dirname(__file__)
        return lPath+os.sep+'_pmvrc', lPath

if __name__ == '__main__':
    from Pmv.fileCommands import PDBQReader, PDBReader, PQRReader
    import pdb
    mv = MoleculeViewer(logMode='no')
    import pdb
