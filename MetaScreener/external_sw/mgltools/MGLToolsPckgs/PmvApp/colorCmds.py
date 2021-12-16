#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2014
#
#############################################################################

#
# $Header: /opt/cvs/PmvApp/colorCmds.py,v 1.8 2014/08/22 22:54:46 annao Exp $
#
# $Id: colorCmds.py,v 1.8 2014/08/22 22:54:46 annao Exp $
#
"""
This Module implements commands to color the current selection different ways.
for example:
    by atoms.
    by residues.
    by chains.
    etc ...
    
"""

import os, sys
from mglutil.util.colorUtil import ToHEX
from PmvApp.colorPalette import ColorPalette, ColorPaletteFunction
from PmvApp.Pmv import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent
from mglutil.events import Event

import numpy

from DejaVu2.colorTool import Map, RGBARamp, RedWhiteARamp, WhiteBlueARamp,\
     RedWhiteBlueARamp

from PmvApp.Pmv import MVCommand # MVAtomICOM

from MolKit.molecule import Molecule, Atom, AtomSet
from MolKit.protein import Protein, Residue, Chain, ProteinSet, ChainSet, ResidueSet
from DejaVu2.colorMap import ColorMap


class ColorAtomsEvent(Event):
    pass


class ColorCommand(MVCommand):
    """The ColorCommand class is the base class from which all the color commands implemented for PMV will derive.\n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorCommand \n
    Command : color \n
    Description:\n
    It implements the general functionalities to color the specified geometries
    representing the specified nodes with the given list of colors.\n
    Synopsis:\n
      None <--- color(nodes, colors[(1.,1.,1.),], geomsToColor=['all'])\n
    Required Arguments:\n 
      nodes --- any set of MolKit nodes describing molecular components\n
    Optional Arguments:\n  
      colors --- list of rgb tuple\n
      geomsToColor --- list of the name of geometries to color default is ['all']\n
      Keywords --- color\n
    """

    def __init__(self):
        MVCommand.__init__(self)


    def makeColorEvent(self, *args, **kw):
        event = ColorAtomsEvent(args, kw)
        self.app().eventHandler.dispatchEvent(event)
        
        
    def onAddCmdToApp(self):
        # this is done for sub classes to be able to change the undoCmdsString
        self.undoCmdsString = self.name

        
    #def onRemoveObjectFromViewer(self, object):
    #    self.cleanup()
    

    def onAddObjectToViewer(self, object):
        self.objectState[object] = {'onAddObjectCalled':True}
        

    def doit(self, nodes, colors=[(1.,1.,1.),], geomsToColor=['all',]):
        """None <--- color(nodes, colors=[(1.,1.,1.),], geomsToColor=['all'])"""
        # nodes are AtomSet
        
        #atms = nodes.findType(Atom)
        #if len(colors)==len(nodes) and not isinstance(nodes[0], Atom):
        #    #expand colors from nodes to atoms
        #    newcolors = []
        #    for n,c in map(None,nodes,colors):
        #        newcolors.extend( [c]*len(n.findType(Atom)) )
        #    colors = newcolors
        if "sticksAndBalls" in geomsToColor:
            geomsToColor.remove("sticksAndBalls")
            geomsToColor.extend(["sticks", "balls"])
        for g in geomsToColor:
            if len(colors)==1 or len(colors)!=len(nodes):
                for a in nodes:
                    #when a new geometry is created, the geometry's
                    #color dictianary is not added to  a.colors,
                    #so a.colors may not have the g key.  
                    #if not a.colors.has_key(g): continue
                    a.colors[g] = tuple( colors[0] )
            else:
                for a, c in map(None, nodes, colors):
                    #if not a.colors.has_key(g): continue
                    #a.colors[g] = tuple(c[:3])
                    a.colors[g] = tuple(c)

        
        for mol in self.molSet:
            updatedGeomsToColor = []
            try:
                for gName in geomsToColor:
                    if not mol.geomContainer.geoms.has_key(gName): continue
                    geom = mol.geomContainer.geoms[gName]
                    # turn off texturemapping:
                    if geom.texture is not None:
                        geom.texture.Set(enable=0, tagModified=False)
                        #updatedGeomsToColor.append(gName) # why is it done here if
                        # the gName is appended to the list 2 lines below (???)
                        geom.Set(inheritMaterial=0, redo=0, tagModified=False)

                    updatedGeomsToColor.append(gName)
                    geom.Set(inheritMaterial=0, redo=0, tagModified=False)

                    if geom.children != []:
                        # get geom Name:
                        childrenNames = [x.name for x in geom.children]
                        updatedGeomsToColor = updatedGeomsToColor + childrenNames
                        for childGeom in geom.children:
                            childGeom.Set(inheritMaterial=0, redo=0,
                                          tagModified=False)
                for gName in updatedGeomsToColor:
                    mol.geomContainer.updateColors([gName])
                self.app()._executionReport.addSuccess('%s: colored molecule %s successfully'% (self.name, mol.name))
            except:
                msg = 'Error while coloring %s for molecule %s'%(gName, mol.name,)
                self.app().errorMsg(sys.exc_info(), msg, obj=self.atmSet)
        #geomEditEvents
        if self.createEvents:
            event = EditGeomsEvent("color", [nodes,[geomsToColor, colors, self.name[5:11]]])
            self.app().eventHandler.dispatchEvent(event)
        self.makeColorEvent(nodes, colors=colors, geomsToColor=geomsToColor)
        

        
    def checkArguments(self, nodes, colors=[(1.,1.,1.),],
                       geomsToColor=['all',]):
        """
        nodes---TreeNodeSet holding the current selection \n
        colors---list of rgb tuple. \n
        geomsToColor---list of the name of geometries to color,default is ['all']
        """
        if isinstance (nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        mols, atms = self.getNodes(nodes)
        self.molSet = mols
        self.atmSet = atms
        assert isinstance(geomsToColor, (list, tuple))
        geomsToColor = [x for x in geomsToColor if x not in [' ', '']]
        if 'all' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols)
        if '*' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols, showUndisplay=1)
        assert  len(geomsToColor)
        assert isinstance(colors, (list, tuple, numpy.ndarray))
        assert len(colors)
        kw = {}
        kw['colors'] = colors
        kw['geomsToColor'] = geomsToColor
        return (atms,) , kw


    def getNodes(self, nodes, returnNodes=False):
        """Expand nodes argument into a list of atoms and a list of molecules. """
        nodes = self.app().expandNodes(nodes)
        assert len(nodes)
        if nodes == self.app().Mols:
            atoms = nodes.allAtoms
            molecules = nodes
        else:
            atoms = nodes.findType( Atom )
            if len(nodes) == 0:
                molecules = ProteinSet()
            else:
                molecules = nodes.top.uniq()
        if returnNodes:
            return molecules, atoms, nodes
        else:
            return molecules, atoms


    def undoCmdBefore(self, nodes, colors, geomsToColor):
        # nodes is an atom set
        for mol in self.molSet:
            if not self.objectState.has_key(mol):
                self.onAddObjectToViewer(mol)
        undoCmds = None
        if len(geomsToColor):
            undoCmds = ([], self.name)
        for g in geomsToColor:
            # all the atom don't have the entry g in their color dictionary.
            # Ca-trace, spline and secondary structure create the color
            # entry for their geometry when computed only
            #if not nodes.colors.has_key(g):
            #    continue
            # check if all colors are the same
            oldColors = nodes.colors.get(g, nodes.colors['lines'])
            cd = {}.fromkeys(['%f%f%f'%tuple(c) for c in oldColors])
            if len(cd)==1:
                oldColors = [oldColors[0]]
            kw = {"colors":oldColors, "geomsToColor":[g]}
            undoCmds[0].append ((self.app().color, (nodes,), kw))
        return undoCmds


    def getChildrenGeomsName(self, mol):
        geomC = mol.geomContainer
        # Get the name of the geometries that are child of another one
        # We only want the parent geometry i.e. 'secondarystructure'
        # We assume that the geometry name is the same than the key in
        # the geoms dictionary.
        childGeomsName = []
        for geomName in geomC.geoms.keys():
            if geomName in ['master','selectionSpheres']:continue
            if geomC.geoms[geomName].children != []:
                names = [x.name for x in geomC.geoms[geomName].children]
                childGeomsName = childGeomsName + names
        return childGeomsName


    def getAvailableGeoms(self, molecules, showUndisplay=0):
        """Method to build a dictionary containing all the geometries
        available in the scene."""
        geomsAvailable = []
        for mol in molecules:
            geomC = mol.geomContainer
            childGeomsName = self.getChildrenGeomsName(mol)
            
            # We only put the one we are interested in in the list
            # of geomsAvailable 
            for geomName in geomC.geoms.keys():
                if geomName in ['master'] :
                    continue
                if geomC.atoms.has_key(geomName):
                    if geomName in childGeomsName and geomC.geoms[geomName].children==[]:
                        continue
                    childgnames=[]
                    if geomC.geoms[geomName].children != []:
                        childnames = [x.name for x in geomC.geoms[geomName].children]
                        childgnames=childgnames+childnames
                        
                        for child in childgnames:
                            if geomC.atoms[geomName]==[] and geomC.atoms[child]!=[]:
                                if not geomName in geomsAvailable:
                                    geomsAvailable.append(geomName)
                    else:   
                        if geomC.atoms[geomName]!=[] or showUndisplay:
                           if not geomName in geomsAvailable:
                                geomsAvailable.append(geomName) 
                        
        return geomsAvailable   
        


class ColorFromPalette(ColorCommand):#, MVAtomICOM):
    """The ColorFromPalette class is the base class from which all the color commands using a colorPalette implemented for PMV will derive. \n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorFromPalette \n
    Description:\n
    It implements the general functionalities needed to retrieve the colors given a palette and a set of nodes.\n
     Synopsis:\n
     None <- colorFromPalette(nodes, geomsToColor=['all'])\n
     Required Arguments:\n      
     nodes---TreeNodeSet holding the current selection\n
     geomsToColor---list of names of geometries to color, default is ['all']\n
    
    """
    # THE USER SHOULD BE ABLE TO CREATE A COLORPALETTE AND USE IT TO COLOR THE
    # SELECTED NODES WITH IT.
    
    def __init__(self):
        ColorCommand.__init__(self)
        #MVAtomICOM.__init__(self)
        #self.flag = self.flag | self.objArgOnly

    
    def undoCmdBefore(self, nodes, geomsToColor=['all',]):
        # these commands do not require the color argument since colors are
        # gotten from a palette
        # we still can use the ColorCommand.undoCmdBefore method by simply
        # passing None for the color argument
        return ColorCommand.undoCmdBefore(self, nodes, None, geomsToColor)
        

    def doit(self, nodes, geomsToColor=['all',]):
        # these commands do not require the color argument since colors are
        # gotten from a palette
        # we still can use the ColorCommand.undoCmdBefore but first we get
        # the colors. This also insures that the colors are not put inside the
        # log string for these commands

        colors = self.getColors(nodes)
        ColorCommand.doit(self, nodes, colors=colors, geomsToColor=geomsToColor)

            
    def onAddCmdToApp(self):
        # these commands use a color command to undo their effect
        # so we make sure it is loaded and we place its name into
        # undoCmdsString
        from mglutil.util.defaultPalettes import ChooseColor, \
             ChooseColorSortedKeys
        self.palette = ColorPalette(
            'Color palette', ChooseColor, readonly=0, info='Color palette',
            sortedkeys=ChooseColorSortedKeys )
            
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        self.undoCmdsString= self.app().color.name
        
        
    def getColors(self, nodes):
        return self.palette.lookup( nodes )


    def checkArguments(self, nodes, geomsToColor=['all']):
        """
           nodes --- TreeNodeSet holding the current selection \n
           geomsToColor --- list of of geometry names to color,
                           default is ['all'] """
        #print "checkArguments:", self.name
        assert nodes
        if isinstance (nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        mols, atoms = self.getNodes(nodes)
        self.molSet = mols
        self.atmSet = atoms
        if not atoms:
            raise ValueError, '%s: No molecular fragment found for %s'%(self.name, str(nodes))
        assert isinstance(geomsToColor, (list, tuple))
        geomsToColor = [x for x in geomsToColor if x not in [' ', '']]
        if 'all' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols)
        elif '*' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols, showUndisplay=1)
        assert len(geomsToColor)
        #print "geoms to color", geomsToColor
        #print "atoms:", len(atoms)
        return (atoms,), {'geomsToColor':geomsToColor}



class ColorByAtomType(ColorFromPalette):
    """The colorByAtomType command allows the user to color the given geometry representing the given nodes using the atomtype coloring scheme where:N :Blue ; C :Gray ; O : Red ; S : Yellow ; H : Cyan; P: Magenta;UNK:green.
    \nPackage : PmvApp
    \nModule  : colorCmds
    \nClass   :  ColorByAtomType
    \nCommand : colorbyAtomType
    \nDescription:\n
    This coloring scheme gives some information on the atomic composition of
    the given nodes.\n
    \nSynopsis:\n
    None <- colorByAtomType(nodes, geomsToColor=['all'])\n
    nodes       : any set of MolKit nodes describing molecular components\n
    geomsToColor: list of the name of geometries to color default is 'all'\n
    Keywords: color, atom type\n
    """
    def __init__(self):
        ColorFromPalette.__init__(self)


    def onAddCmdToApp(self):
        c = 'Color palette for atom type'
        from PmvApp.pmvPalettes import AtomElements
        self.palette = ColorPalette('Atom Elements', colorDict=AtomElements,
                                    readonly=0, info=c,
                                    lookupMember='element')
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        self.undoCmdsString = self.app().color.name



class ColorByDG(ColorFromPalette):
    """The colorByDG command allows the user to color the given geometries representing the given nodes using David Goodsell's coloring
    scheme. \n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorByDG \n
    Command : colorAtomsUsingDG\n
    Synopsis:\n
    None <--- colorByDG(nodes, geomsToColor=['all'])\n
    Arguments:\n
    nodes --- any set of MolKit nodes describing molecular components\n
    geomsToColor --- list of the name of geometries to color default is 'all'\n
    Keywords --- color, David Goodsell's coloring scheme\n
    """
    
    def __init__(self):
        ColorFromPalette.__init__(self)

        self.DGatomIds=['ASPOD1','ASPOD2','GLUOE1','GLUOE2', 'SERHG',
                        'THRHG1','TYROH','TYRHH',
                        'LYSNZ','LYSHZ1','LYSHZ2','LYSHZ3','ARGNE','ARGNH1','ARGNH2',
                        'ARGHH11','ARGHH12','ARGHH21','ARGHH22','ARGHE','GLNHE21',
                        'GLNHE22','GLNHE2',
                        'ASNHD2','ASNHD21', 'ASNHD22','HISHD1','HISHE2' ,
                        'CYSHG', 'HN']

        
    def onAddCmdToApp(self):
        from PmvApp.pmvPalettes import DavidGoodsell, DavidGoodsellSortedKeys
        c = 'Color palette for coloring using David Goodsells colors'

        self.palette = ColorPaletteFunction(
            'DavidGoodsell', DavidGoodsell, readonly=0, info=c,
            sortedkeys=DavidGoodsellSortedKeys, lookupFunction=self.lookupFunc)
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        self.undoCmdsString = self.app().color.name


    def lookupFunc(self, atom):
        assert isinstance(atom, Atom)
        if atom.name in ['HN']:
            atom.atomId = atom.name
        else:
            atom.atomId=atom.parent.type+atom.name
        if atom.atomId not in self.DGatomIds: 
            atom.atomId=atom.element
        return atom.atomId



class ColorByResidueType(ColorFromPalette):
    """The colorByResidueType command allows the user to color the given geometries representing the given nodes using the Rasmol coloring scheme. \n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorByResidueType \n
    Command : colorByResidueType \n
    where:\n
    ASP, GLU    bright red       CYS, MET       yellow\n
    LYS, ARG    blue             SER, THR       orange\n
    PHE, TYR    mid blue         ASN, GLN       cyan\n
    GLY         light grey       LEU, VAL, ILE  green\n
    ALA         dark grey        TRP            pink\n
    HIS         pale blue        PRO            flesh\n
    Synopsis:\n
      None <- colorByResidueType(nodes, geomsToColor=['all'])\n
      nodes --- any set of MolKit nodes describing molecular components.\n
      geomsToColor --- list of the name of geometries to color default is 'all'\n
    Keywords --- color, Rasmol, residue type\n
    """
    
    def onAddCmdToApp(self):
        from PmvApp.pmvPalettes import RasmolAmino, RasmolAminoSortedKeys
        c = 'Color palette for Rasmol like residues types'
        self.palette = ColorPalette(
            'RasmolAmino', RasmolAmino, readonly=0, info=c,
            sortedkeys = RasmolAminoSortedKeys, lookupMember='type')
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        self.undoCmdsString = self.app().color.name


    def getColors(self, nodes):
        return self.palette.lookup( nodes.findType(Residue) )
    


class ColorShapely(ColorFromPalette):
    """The colorByShapely command allows the user to color the given geometries representing the given nodes using the Shapely coloring scheme where each residue has a different color. (For more information please refer to the pmv tutorial). \n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorShapely \n
    Command : colorResiduesUsingShapely\n
    Synopsis:\n
      None <- colorResiduesUsingShapely(nodes, geomsToColor=['all'])\n
      nodes --- any set of MolKit nodes describing molecular components\n
      geomsToColor --- list of the name of geometries to color default is ['all']\n
      Keywords --- color, shapely, residue type\n
    """
    def onAddCmdToApp(self):
        from PmvApp.pmvPalettes import Shapely

        self.palette = ColorPalette('Shapely', Shapely, readonly=0,
            info='Color palette for shapely residues types',
                                    lookupMember='type')
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp',
                                   )
            #colorCmd = self.app().color(loadOnly=True)
        self.undoCmdsString = self.app().color.name


    def getColors(self, nodes):
        if not nodes:
            raise ValueError, "%s: Missing molecular fragment to color" % self.name
        return self.palette.lookup( nodes.findType(Residue) )



##
## FIXME ramp should be a colorMap object with editor and stuff
## it should be possible to pass it as an argument. if none is given a default
## a colorMap object with a default RGBRamp would be used
## This is also true for Palettes.
##
from DejaVu2.colorTool import Map

class ColorFromRamp(ColorFromPalette):
    """The colorFromRamp class implements the functionality to color the given geometries representing the given nodes using a colorMap created from the Ramp.
    \nPackage : PmvApp
    \nModule  : colorCmds
    \nClass   : ColorFromRamp
    \nSynopsis:\n
      None <- colorFromRamp(nodes, geomsToColor=['all'])\n
      nodes --- any set of MolKit nodes describing molecular components\n
      geomsToColor --- list of the name of geometries to color default is ['all']\n
      Keywords --- color, ramp\n
    """
 
    def __init__(self):
        ColorFromPalette.__init__(self)
        #self.flag = self.flag | self.objArgOnly
        from DejaVu2.colorTool import RGBRamp, Map
        self.ramp = RGBRamp()


class ColorByChain(ColorFromPalette):
    """The colorByChain command allows the user to color the given geometries representing the given nodes by chain. A different color is assigned to each chain.
    \nPackage : PmvApp
    \nModule  : colorCmds
    \nClass   : ColorByChain
    \nCommand : colorByChains
    \nSynopsis:\n
      None <- colorByChains(nodes, geomsToColor=['all'], carbonsOnly=False)\n
      nodes --- any set of MolKit nodes describing molecular components\n
      geomsToColor --- list of the name of geometries to color default is 'all'\n
      Keywords --- color, chain\n
    """
    def onAddCmdToApp(self):
        from mglutil.util.defaultPalettes import MolColors, Rainbow, RainbowSortedKey
        self.palette = ColorPaletteFunction(
            'MolColors', MolColors, readonly=0, info='Color palette chain number',
            lookupFunction = lambda x, length = len(RainbowSortedKey):\
            x.number%length, sortedkeys = RainbowSortedKey)
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
            #colorCmd = self.app().color(loadOnly=True)
        self.undoCmdsString= self.app().color.name

        
    def getColors(self, nodes):
        if not nodes: return
        colors = self.palette.lookup(nodes.findType(Chain))
        return colors


    def checkArguments(self, nodes, geomsToColor=['all',], carbonsOnly=False):
        """
        nodes---TreeNodeSet holding the current selection \n
        colors---list of rgb tuple. \n
        geomsToColor---list of the name of geometries to color,default is ['all'],
        carbonsOnly --- flag (True, False) 
                        When this flag is set to True only carbon atoms \n
                        will be assigned color.
        """
        args, kw = ColorFromPalette.checkArguments(self, nodes,
                                                   geomsToColor=geomsToColor)
        assert carbonsOnly in (True, False)
        kw['carbonsOnly'] = carbonsOnly 
        return args, kw

    
    def doit(self, nodes, geomsToColor=['all',], carbonsOnly=False):
        # nodes are atom set
        if carbonsOnly:
            nodes= AtomSet([x for x in nodes if x.element=='C'])
        ColorFromPalette.doit(self, nodes, geomsToColor=geomsToColor)


    def undoCmdBefore(self, nodes, geomsToColor=['all',], carbonsOnly=False):
        #nodes is an atom set
        if carbonsOnly:
            nodes= AtomSet([x for x in nodes if x.element=='C'])
        return ColorCommand.undoCmdBefore(self, nodes, colors=None, geomsToColor=geomsToColor)
    


class ColorByMolecule(ColorFromPalette):
    """The colorByMolecules command allows the user to color the given geometries representing the given nodes by molecules. A different color is assigned to each molecule. \n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorByMolecule \n
    Command : colorByMolecules \n
    Synopsis:\n
      None <- colorByMolecules(nodes, geomsToColor=['all'], carbonsOnly=False)\n
      nodes --- any set of MolKit nodes describing molecular components\n
      geomsToColor --- list of the name of geometries to color default is ['all']\n
      carbonsOnly --- flag (True, False) 
                        When this flag is set to True only carbon atoms \n
                        will be assigned color.
      Keywords --- color, chain\n
    """

    
    def onAddCmdToApp(self):
        from mglutil.util.defaultPalettes import MolColors, Rainbow, RainbowSortedKey
        c = 'Color palette molecule number'
        self.palette = ColorPaletteFunction(
            'MolColors', MolColors, readonly=0, info=c,
            lookupFunction = lambda x, length=len(RainbowSortedKey): \
            x.number%length, sortedkeys=RainbowSortedKey)

        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        self.undoCmdsString= self.app().color.name


    def onAddObjectToViewer(self, obj):
        self.objectState[obj] = {'onAddObjectCalled':True}
        obj.number = self.app().Mols.index(obj)
        
        
    def getColors(self, nodes):
        if not nodes: return
        colors = self.palette.lookup(nodes.top)
        return colors


    def checkArguments(self, nodes, geomsToColor=['all',], carbonsOnly=False):
        """
        nodes---TreeNodeSet holding the current selection \n
        colors---list of rgb tuple. \n
        geomsToColor---list of the name of geometries to color,default is ['all'],
        carbonsOnly --- flag (True, False) Color by molecule assigns \n
                        a different color to each molecule.\n
                        When this flag is set to True only carbon atoms \n
                        will be assigned that color.
        """
        args, kw = ColorFromPalette.checkArguments(self, nodes,
                                                   geomsToColor=geomsToColor)
        assert carbonsOnly in (True, False)
        kw['carbonsOnly'] = carbonsOnly 
        return args, kw

    
    def doit(self, nodes, geomsToColor=['all',], carbonsOnly=False):
        # nodes is an atom set
        if carbonsOnly:
            nodes= AtomSet([x for x in nodes if x.element=='C'])

        ColorFromPalette.doit(self, nodes, geomsToColor=geomsToColor)


    def undoCmdBefore(self, nodes, geomsToColor=['all',], carbonsOnly=False):
        # nodes is an atom set
        if carbonsOnly:
            nodes= AtomSet([x for x in nodes if x.element=='C'])
        return ColorCommand.undoCmdBefore(self, nodes, colors=None, geomsToColor=geomsToColor)
            


class ColorByInstance(ColorFromPalette):
    """Command to color the current selection by instance using a Rainbow palette.
    \nPackage : PmvApp
    \nModule  : colorCmds
    \nClass   : ColorByInstance
    \nCommand : colorByInstance
    \nSynopsis:\n
      None <- colorByInstance(nodes, geomsToColor=['all'])\n
      nodes --- any set of MolKit nodes describing molecular components\n
      geomsToColor --- list of the name of geometries to color default is ['all']\n
    """

    def onAddCmdToApp(self):
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        self.undoCmdsString= self.app().color.name
        from mglutil.util.defaultPalettes import Rainbow, RainbowSortedKey
        c = 'Color palette molecule number'
        c = ""
        self.palette = ColorPaletteFunction(
            'Rainbow', Rainbow, readonly=0, info=c,
            lookupFunction = lambda x, length=len(RainbowSortedKey): \
            x%length, sortedkeys=RainbowSortedKey)


    def onAddObjectToViewer(self, obj):
        self.objectState[obj] = {'onAddObjectCalled':True}
        obj.number = self.app().Mols.index(obj)


    def doit(self, nodes, geomsToColor=['all']):
        # nodes is an atom set
        for m in self.molSet:
            geomc = m.geomContainer
            #moreGeoms = []
            #if 'lines' in geomsToColor:
            #    moreGeoms = ['bonded', 'bondorder','nobnds']
            #for g in geomsToColor+moreGeoms:
            for g in geomsToColor:
                try:
                    ge = geomc.geoms[g]
                    colors = self.palette.lookup(range(len(ge.instanceMatricesFortran)))
                    ge.Set(materials=colors, inheritMaterial=0, tagModified=False)
                    ge.SetForChildren(inheritMaterial=True, recursive=True)
                except:
                    msg = '%s: Error while coloring %s for molecule %s'%(self.name, g, m.name,)
                    self.app().errorMsg(sys.exc_info(), msg, obj=self.atmSet)
                #ColorCommand.doit(self, m, colors, geomsToColor)
            self.app()._executionReport.addSuccess('%s for molecule %s success'% (self.name, m.name))


class ColorByProperties(ColorCommand):
    """
    Command to color the current selection according to the integer
    or float properties, or by defining a function.
    \nPackage : PmvApp
    \nModule  : colorCmds
    \nClass   : ColorByProperties
    \nCommand : colorByProperty
    \nSynopsis:\n
      None <- colorByProperty(nodes, geomsToColor, property,colormap='rgb256')\n
      nodes --- any set of MolKit nodes describing molecular components\n
      geomsToColor --- list of the name of geometries to color default is 'all'\n
      property ---  property name of type integer or float or property defined by a function returning a list of float or int.\n
      colormap ---  either a string representing a colormap or a DejaVu2.ColorMap instance.\n
    """

    levelOrder = {'Atom':0 , 
                  'Residue':1,
                  'Chain':2,
                  'Molecule':3 }

    def __init__(self):
        ColorCommand.__init__(self)
        #self.flag = self.flag & 0
        self.level = Atom  # class at this level (i.e. Molecule, Residue, Atom)
        

    def onAddCmdToApp(self):
        # the following commands use a color command to undo their effect
        # so we make sure it is loaded and we place its name into
        # undoCmdsString
        if not self.app().commands.has_key('color'):
            self.app().lazyLoad('colorCmds', commands=['color'], package='PmvApp')
        if not self.app().commands.has_key('saveSet'):
            self.app().lazyLoad('selectionCmds', commands=['saveSet'], package='PmvApp')
            #colorCmd = self.app().color(loadOnly=True)
        self.app().loadColormap()
        self.undoCmdsString = self.app().color.name
        self.molDict = {'Molecule':Molecule,
                        'Atom':Atom, 'Residue':Residue, 'Chain':Chain}

        self.leveloption={}
        for name in ['Atom', 'Residue', 'Molecule', 'Chain']:
            col = self.app().levelColors[name]
            bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
            ag = ToHEX(col)
            self.leveloption[name]={'bg':bg,'activebackground':ag,
                                    'borderwidth':3}
        self.propValues = None
        self.level = "Molecule"
        self.propertyLevel = self.level


    def getPropValues(self, nodes, prop, propertyLevel=None):
        #print "getPropValues", self, nodes, prop, propertyLevel
        try:
            if propertyLevel is not None:
                lNodesInLevel = nodes.findType(self.molDict[propertyLevel])
                self.propValues = getattr(lNodesInLevel, prop)
            else:
                self.propValues = getattr(nodes, prop)
        except:
            from Pmv import formatName
            msg= "%s.getPropValues: nodes(%s) do not have property %s" % (self.name, formatName(nodes.buildRepr(), 60), prop)
            raise RuntimeError(msg)


    def undoCmdBefore(self, nodes, geomsToColor,  property,
                        propertyLevel=None, colormap='rgb256',
                        mini=None, maxi=None, carbonsOnly=False):
        # nodes is an atom set
        if carbonsOnly:
            nodes= AtomSet([x for x in nodes if x.element=='C'])
        return ColorCommand.undoCmdBefore(self, nodes, colors=None, geomsToColor=geomsToColor)


    def doit(self, nodes, geomsToColor, property, propertyLevel=None,
             colormap='rgb256', mini=None, maxi=None, carbonsOnly=False):

        #print 'VVVV', len(nodes), property, propertyLevel
        #nodes = nodes.findType(self.app().selectionLevel)
        #print 'CCCCCC', len(nodes)
        if "sticksAndBalls" in geomsToColor:
            geomsToColor.remove("sticksAndBalls")
            geomsToColor.extend(["sticks", "balls"])
        if isinstance (colormap, str):
            colormap = self.app().colorMaps[colormap]
        # Get the list of values corresponding the the chosen property
        # if not already done ?
        self.getPropValues(nodes, property, propertyLevel)
        # build the color ramp.
        selectioncol = colormap.Map(self.propValues, mini=mini, maxi=maxi)
        # Call the colorProp method
        self.colorProp(nodes, geomsToColor, selectioncol,
                       propertyLevel, carbonsOnly )
        
        ## insideIntervalnodes = []
        ## for i in range(len(nodes)):
        ##     if self.propValues[i] >= mini and self.propValues[i] <= maxi:
        ##         insideIntervalnodes.append(nodes[i])
        ## if nodes[0].__class__.__name__.endswith('Atom'):
        ##     lSet = AtomSet(insideIntervalnodes)
        ## elif nodes[0].__class__.__name__.endswith('Residue'):
        ##     lSet = ResidueSet(insideIntervalnodes)
        ## elif nodes[0].__class__.__name__.endswith('Chain'):
        ##     lSet = ChainSet(insideIntervalnodes)
        ## elif nodes[0].__class__.__name__.endswith('Molecule'):
        ##     lSet = MoleculeSet(insideIntervalnodes)
        ## elif nodes[0].__class__.__name__.endswith('Protein'):
        ##     lSet = ProteinSet(insideIntervalnodes)

##         if 'ColorByProperties' in self.app().sets.keys():
##             self.app().sets.pop('ColorByProperties')
##         self.app().saveSet(lSet, 'ColorByProperties', log=False,
##                 comments="""Last set created by colorByProperties,
## contains only nodes with chosen property between mini and maxi.
## This set is ovewritten each time ColorByProperties is called.
## """)
        #geomEditEventss
        
        event = EditGeomsEvent("color", [nodes,[geomsToColor, selectioncol, self.name[5:11]]])
        self.app().eventHandler.dispatchEvent(event)
        #return lSet


    def colorProp(self, nodes, geomsToColor, selectioncol, propertyLevel='Atom', carbonsOnly=False):
        # nodes is an atom set
        if (propertyLevel is not None) and \
           self.levelOrder[propertyLevel] < self.levelOrder[self.level]:
            nodes = nodes.findType(self.molDict[propertyLevel])     

        # loop over the node and assign the right color to the atoms.
        deltaOpac = 0.0
        for gName in geomsToColor:
            for i, n in enumerate(nodes):
                if not carbonsOnly or n.chemElem == "C":
                    #if n.colors.has_key(gName):
                    n.colors[gName] = tuple(selectioncol[i][:3])
                    if n.opacities.has_key(gName):
                        newOpac = selectioncol[i][3]
                        oldOpac = n.opacities[gName]
                        deltaOpac = deltaOpac + (oldOpac-newOpac)
                        n.opacities[gName] = newOpac
        for mol in self.molSet:
            try:
                updatedGeomsToColor = []
                for gName in geomsToColor:
                    if not mol.geomContainer.geoms.has_key(gName): continue
                    geom = mol.geomContainer.geoms[gName]
                    if geom.children != []:
                        # get geom Name:
                        childrenNames = [x.name for x in geom.children]
                        updatedGeomsToColor = updatedGeomsToColor + childrenNames
                        for childGeom in geom.children:
                            childGeom.Set(inheritMaterial=0, redo=0, tagModified=False)
                    else:
                        updatedGeomsToColor.append(gName)
                        geom.Set(inheritMaterial=0, redo=0, tagModified=False)

                updateOpac = (deltaOpac!=0.0)
                mol.geomContainer.updateColors(updatedGeomsToColor,
                                               updateOpacity=updateOpac)
                self.app()._executionReport.addSuccess('%s: colored molecule %s successfully'% (self.name, mol.name))
            except:
                msg = '%s: Error in colorProp() for molecule %s'%(self.name, mol.name)
                self.app().errorMsg(sys.exc_info(), msg, obj=self.atmSet)
            

    def checkArguments(self, nodes, geomsToColor, property,
                       propertyLevel='Atom', colormap='rgb256',
                       mini=None, maxi=None, carbonsOnly=False):
        """None <- colorByProperty(nodes, geomsToColor, property,colormap='rgb256', **kw)
        \nnode --- TreeNodeSet holding the current selection
        \ngeomsToColor --- the list of the name geometries to be colored
        \nproperty ---   property name of type integer or float or property defined by a function returning a list of float or int.
        \ncolormap--- either a string representing a colormap or a DejaVu2.ColorMap instance.
        """
        assert nodes
        if isinstance (nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        mols, atms = self.getNodes(nodes)
        self.molSet = mols
        self.atmSet = atms
        assert isinstance(geomsToColor, (list, tuple))
        geomsToColor = [x for x in  geomsToColor if x not in [' ', '']]
        if 'all' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols)
        if '*' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols, showUndisplay=1)
        assert len(geomsToColor)
        assert propertyLevel in ['Atom', 'Residue', 'Molecule', 'Chain']
        assert isinstance(property, str)
        if mini is not None:
            assert isinstance (mini, (int, float))
        if maxi is not None:
            assert isinstance (maxi, (int, float))
            assert maxi >= mini
        if isinstance (colormap, str):
            assert self.app().colorMaps.has_key(colormap)
        else:
            assert isinstance(colormap, ColorMap)

        kw= {}
        kw['colormap'] = colormap
        kw['mini'] = mini
        kw['maxi'] = maxi
        kw['propertyLevel'] = propertyLevel
        return (atms, geomsToColor, property), kw



class ColorByExpression(ColorByProperties):
    """The colorByExpression command allows the user to color the given geometries representing the given nodes evaluated by  python function or lambda function. \n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorByExpression \n
    Command : colorByExpression \n
    Synopsis:\n
     None <- colorByExpression(nodes, geomsToColor, function, colormap='rgb256', min=None, max=None) \n
     nodes --- TreeNodeSet holding the current selection \n
     geomsToColor --- the list of the name geometries to be colored \n
     function --- python function or lambda function that will be evaluated with the given nodes \n
     colormap ---  can either be a string which is the name of a loaded colormap or a DejaVu2.colorMap.ColorMap instance.
  """  
    
    # comments for map function definition window
    mapLabel = """Define a function to be applied
on each node of the current selection: """

    # code example for map function definition window
    mapText = '\
#This is a demo function for this widget.\n\
def foo(object):\n\
\tif hasattr(object, "number"):\n\
\t\treturn object._uniqIndex\n\
\telse:\n\
\t\treturn 0\n\
\n'

    # comments for function to operate on selection
    funcLabel = """Define a function to be applied to
the current selection:"""
    
    # code example for function to operate on selection
    funcText ='#def foo(selection):\n#\tvalues = []\n#\t#loop on the current selection\n#\tfor i in xrange(len(selection)):\n#\t\t#build a list of values to color the current selection.\n#\t\tif selection[i].number > 20:\n#\t\t\tvalues.append(selection[i].number*2)\n#\t\telse:\n#\t\t\tvalues.append(selection[i].number)\n#\t# this list of values is then returned.\n#\treturn values\n'

    def __init__(self):
        ColorCommand.__init__(self)
        #self.flag = self.flag & 0

    def onAddCmdToApp(self):
        ColorByProperties.onAddCmdToApp(self)
        self.evalFlag = 0
        self.propValues=None
        

        
    def undoCmdBefore(self, nodes, geomsToColor,
                        function='lambda x: x._uniqIndex',
                        colormap='rgb256'):
        return ColorCommand.undoCmdBefore(self, nodes, colors=None, geomsToColor=geomsToColor)


    def checkArguments(self, nodes,  geomsToColor=['all'],
                 function='lambda x: x._uniqIndex',
                 colormap='rgb256'):
        """
        nodes --- TreeNodeSet holding the current selection \n
        geomsToColor --- the list of the name geometries to be colored \n
        function --- python function or lambda function that will be evaluated with the given nodes \n
        colormap ---  can either be a string which is the name of a loaded colormap or a DejaVu2.colorMap.ColorMap instance.
        """
        assert nodes
        if isinstance (nodes, str):
            self.nodeLogString = "'"+nodes+"'"
        mols, atms = self.getNodes(nodes)
        self.molSet = mols
        self.atmSet = atms
        assert isinstance(geomsToColor, (list, tuple))
        geomsToColor = [x for x in  geomsToColor if x not in [' ', '']]
        if 'all' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols)
        if '*' in geomsToColor:
            geomsToColor = self.getAvailableGeoms(mols, showUndisplay=1)
        assert len(geomsToColor)
        if isinstance (colormap, str):
            assert self.app().colorMaps.has_key(colormap)
        else:
            assert isinstance(colormap, ColorMap)
        assert isinstance (function, str)
        kw = {}
        kw['function'] = function
        kw['colormap'] = colormap
        return (atms, geomsToColor), kw
    

    def getPropValues(self, nodes, function):
        func = evalString(function)
        self.propValues = func(nodes)

        
    def doit(self, nodes,  geomsToColor,
             function='lambda x: x._uniqIndex', colormap='rgb256'):
        #nodes is an atom set
        if "sticksAndBalls" in geomsToColor:
            geomsToColor.remove("sticksAndBalls")
            geomsToColor.extend(["sticks", "balls"])
        if isinstance(colormap, str):
            colormap = self.app().colorMaps[colormap]
        # get the values
        self.getPropValues(nodes, function)

        # Get the color corresponding the values
        selectioncol = colormap.Map(self.propValues, colormap.mini,
                                    colormap.maxi)
        
        self.colorProp(nodes, geomsToColor, selectioncol)
        #geomEditEventss
        event = EditGeomsEvent("color", [nodes,[geomsToColor, selectioncol, self.name[5:11]]])
        self.app().eventHandler.dispatchEvent(event)



class RainbowColor(ColorFromPalette):
    """The RainbowColor command colors molecules using a rainbow color map.\n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : RainbowColor \n
    Command : colorRainbow \n
    Synopsis:\n
    None <- colorRainbow(nodes, geomsToColor=['all']) \n
    nodes --- TreeNodeSet holding the current selection \n
    geomsToColor --- list of geometries (names) to be colored
    """  
    

    def doit(self, nodes, geomsToColor=['all']):
        # nodes is an atom set
        nodes._uniqNumber = range(1, len(nodes)+1)  
        self.app().colorByProperty(nodes, geomsToColor, '_uniqNumber',
                                propertyLevel='Atom', colormap='rgb256',
                                mini=1., maxi=len(nodes), 
                                setupUndo=False)
        


class RainbowColorByChain(ColorFromPalette):
    """The RainbowColor command colors molecule's chains using a rainbow color map.\n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : RainbowColor \n
    Command : colorRainbowByChain\n
    Synopsis:\n
     None <- colorRainbowByChain(nodes, geomsToColor=['all']) \n
     nodes --- TreeNodeSet holding the current selection \n
     geomsToColor --- list of geometries (names) to be colored
    """  
    def doit(self, nodes, geomsToColor=['all']):
        # nodes is an atomset
        #from time import time
        #t1 = time()
        chains = nodes.findType(Chain)
        if nodes == nodes.top.uniq().allAtoms:
            chains = chains.uniq()
            for chain in chains:
                atoms = chain.findType(Atom)
                atoms._uniqNumber = range(1, len(atoms)+1)
                self.app().colorByProperty(atoms, geomsToColor, '_uniqNumber',
                             propertyLevel='Atom', colormap='rgb256',
                             mini=1., maxi=len(atoms), 
                             setupUndo=False)
        else:
            dd = {}.fromkeys(chains.uniq(), AtomSet())
            for i, ch in enumerate(chains): dd[ch].append(nodes[i])
            for chain, atoms in dd.items():
                atoms._uniqNumber = range(1, len(atoms)+1)
                self.app().colorByProperty(atoms, geomsToColor, '_uniqNumber',
                                    propertyLevel='Atom', colormap='rgb256',
                                    mini=1., maxi=len(atoms), 
                                    setupUndo=False)
        #print "done RainbowColorByChain in :", time() -t1



class ColorByLineGeometryColor(ColorFromPalette):
    """ Colors selected geometries by the Lines color scheme.\n
    Package : PmvApp \n
    Module  : colorCmds \n
    Class   : ColorByLineGeometryColor \n
    Command : colorByLinesColor\n
    Synopsis:\n
     None <- colorByLinesColor(nodes, geomsToColor=['all']) \n
     nodes --- TreeNodeSet holding the current selection \n
     geomsToColor --- list of geometries (names) to be colored"""
            
    def doit (self, nodes, geomsToColor=['all']):
        # nodes is an atom set
        if 'lines' in geomsToColor:
            geomsToColor.remove('lines')
            if not len(geomsToColor): return
        if "sticksAndBalls" in geomsToColor:
            geomsToColor.remove("sticksAndBalls")
            geomsToColor.extend(["sticks", "balls"])
        for geom in geomsToColor:
            for a in nodes:
                if a.colors.has_key(geom):
                    del a.colors[geom]
            if geom == 'sticks' or geom == 'balls':
                self.app().displaySticksAndBalls(nodes)
            elif geom == 'cpk':
                self.app().displayCPK(nodes)
            elif geom == "MSMS-MOL":
                self.app().computeMSMS(nodes)
            #CAballs CAsticks
            elif geom == "CAballs" or geom == "CAsticks":
                self.app().displayBackboneTrace(nodes)
            elif geom == "secondarystructure":
                self.app().displayExtrudedSS(nodes)
            elif geom.find("Labels")>0:
                ColorFromPalette.doit(self, nodes, [geom,])
                

    def getColors(self, nodes):
        return nodes.colors.get('lines', [(1.,1.,1.),])
        

    
commandClassFromName = {
    'color' : [ColorCommand,  None],
    'colorByAtomType' : [ColorByAtomType, None],
    'colorByResidueType' : [ColorByResidueType, None],
    'colorAtomsUsingDG' : [ColorByDG, None],
    'colorResiduesUsingShapely' : [ColorShapely, None],
    'colorByChains' : [ColorByChain, None],
    'colorByMolecules' : [ColorByMolecule, None],
    'colorByInstance' : [ColorByInstance, None],
    'colorByProperty' : [ColorByProperties, None],
    'colorRainbow' : [RainbowColor, None],
    'colorRainbowByChain' : [RainbowColorByChain, None],
    'colorByExpression' : [ColorByExpression, None],
    'colorByLinesColor' :[ColorByLineGeometryColor, None]
    }


def initModule(viewer):
    for cmdName, values in commandClassFromName.items():
        cmdClass, guiInstance = values
        viewer.addCommand(cmdClass(), cmdName, guiInstance)

