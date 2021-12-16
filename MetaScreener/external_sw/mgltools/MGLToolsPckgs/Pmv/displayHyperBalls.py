# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 18:08:00 2011

@author: -
"""
import warnings
import traceback, math
from types import ListType, TupleType, StringType, IntType, FloatType, LongType, StringType
import Tkinter, Pmw
import string
import numpy
import numpy as np
import numpy.oldnumeric as Numeric

from Pmv.mvCommand import MVCommand, MVAtomICOM
from Pmv.stringSelectorGUI import StringSelectorGUI

from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet, BondSet
from MolKit.protein import Protein, Residue, ResidueSet, Chain

from DejaVu.Cylinders import Cylinders
from DejaVu.IndexedPolylines import IndexedPolylines
from DejaVu.Spheres import Spheres
from DejaVu.Points import Points, CrossSet
from DejaVu.Geom import Geom

from ViewerFramework.VFCommand import CommandGUI
from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent, ShowMoleculesEvent
from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent

from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.misc import ensureFontCase

from mglutil.gui.InputForm.Tk.gui import InputFormDescr, evalString
from mglutil.util.callback import CallBackFunction
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ExtendedSliderWidget, ListChooser
import types


from Pmv.displayCommands import DisplayCommand

#// setup for the different standard representions

#SHRINK_CPK     =    0.01
#SCALE_BOND_CPK =    0.2
#SCALE_ATOM_CPK =    0.3
#
#SHRINK_VDW      =   0.01
#SCALE_BOND_VDW  =   0.01
#SCALE_ATOM_VDW  =   0.99
#
#SHRINK_LIC       =  0.01
#SCALE_BOND_LIC   =  0.26
#SCALE_ATOM_LIC   =  0.26
#
#SHRINK_HBL       =  0.3
#SCALE_BOND_HBL   =  0.4
#SCALE_ATOM_HBL   =  0.4


class DisplayHyperBalls(DisplayCommand):
    """ The displayCPK command allows the user to display/undisplay the given nodes using a CPK representation, where each atom is represented with a sphere. A scale factor and the quality of the spheres are user
    defined parameters.
    \nPackage : Pmv
    \nModule  : displayCommands
    \nClass   : DisplayCPK
    \nCommand : displayCPK
    \nSynopsis:\n
        None <- displayCPK(nodes, only=False, negate=False, 
                           scaleFactor=None, quality=None, **kw)\n
        nodes --- any set of MolKit nodes describing molecular components\n
        only --- Boolean flag specifying whether or not to only display
                     the current selection\n
        negate --- Boolean flag specifying whether or not to undisplay
                     the current selection\n
        scaleFactor --- specifies a scale factor that will be applied to the atom
                     radii to compute the spheres radii. (default is 1.0)\n
        quality  --- specifies the quality of the spheres. (default 10)\n
        keywords --- display, CPK, space filling, undisplay.\n
    """
    
    def __init__(self, func=None):
        DisplayCommand.__init__(self, func)
#        self.shaders = Qutemol.shaders
#        self.backup_camera_redraw = None
#        self.camera_initialized = False
        print "init"
        self.options={"CPK":[0.01,0.2,0.3],
                      "VDW":[0.01,0.01,0.99],
                      "LIC":[0.01,0.26,0.26],
                      "HBL":[0.3,0.4,0.4]}
        self.options_adv={"S&B":{'shrink':0.01, 'scaleFactor':0.0 ,  'bScale':0.5, 'cpkRad':0.5 },
                         "CPK":{'shrink':0.01, 'scaleFactor':1   ,  'bScale':0.01, 'cpkRad':0.0},
                         "LIC":{'shrink':0.01, 'scaleFactor':0.0,  'bScale':1.0, 'cpkRad':0.3},
                         "HBL":{'shrink':0.3,  'scaleFactor':0.0 ,  'bScale':1.0, 'cpkRad':0.6 }}        
#        for name, kw in {"S&B":{'shrink':0.01, 'scaleFactor':0.0 ,  'bScale':0.5, 'cpkRad':0.5 },
#                         "CPK":{'shrink':0.01, 'scaleFactor':1   ,  'bScale':0.01, 'cpkRad':0.0},
#                         "LIC":{'shrink':0.01, 'scaleFactor':0.0,  'bScale':1.0, 'cpkRad':0.3},
#                         "HBL":{'shrink':0.3,  'scaleFactor':0.0 ,  'bScale':1.0, 'cpkRad':0.6 }}.items():
        
    def onAddCmdToViewer(self,):
        DisplayCommand.onAddCmdToViewer(self)

        if self.vf.hasGui:
            self.showAtomProp = Tkinter.IntVar()
            self.showAtomProp.set(0)
            self.aScale_var = Tkinter.DoubleVar()
            self.aScale_var.set(0.0)
            self.bScale_var = Tkinter.DoubleVar()
            self.bScale_var.set(0.5)
            self.shrink_var = Tkinter.DoubleVar()
            self.shrink_var.set(0.01)
            self.cpkRad_var = Tkinter.DoubleVar()
            self.cpkRad_var.set(0.5)
            
#            self.shaderprop = Tkinter.IntVar()
#            self.shaderprop.set(0)
#            self.pmvproj = Tkinter.IntVar()
#            self.pmvproj.set(0)
#            self.pmvtransf = Tkinter.IntVar()
#            self.pmvtransf.set(0)
            
        if not self.vf.commands.has_key('assignAtomsRadii'):
            self.vf.loadCommand('editCommands', 'assignAtomsRadii', 'Pmv',
                                topCommand=0)
        from MolKit.molecule import Molecule, Atom
        from MolKit.protein import Protein, Residue, Chain
        from mglutil.util.colorUtil import ToHEX
        self.molDict = {'Molecule':Molecule,
                        'Atom':Atom, 'Residue':Residue, 'Chain':Chain}
        self.nameDict = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}

        self.leveloption={}
        for name in ['Atom', 'Residue', 'Molecule', 'Chain']:
            col = self.vf.ICmdCaller.levelColors[name]
            bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
            ag = ToHEX(col)
            self.leveloption[name]={#'bg':bg,
                                    'activebackground':bg, 'selectcolor':ag ,
                                    'borderwidth':3 , 'width':15}
        self.propValues = None
        self.getVal = 0
        self.propertyLevel = self.nameDict[self.vf.selectionLevel]

        

    def onAddObjectToViewer(self, obj):
        """Adds the cpk geometry and the cpk Atomset to the object's
        geometry container
        """
#        if self.vf.hasGui and self.vf.commands.has_key('dashboard'):
#            self.vf.dashboard.resetColPercent(obj, '_showCPKStatus')

        #if not self.vf.hasGui: return
        obj.allAtoms.cpkScale = 1.0
        obj.allAtoms.cpkRad = 0.0
        geomC = obj.geomContainer
        # CPK spheres
        from DejaVu.hpBalls import hyperBalls
        #from pyQutemol.qutemolSpheres import QuteMolSpheres
        g = hyperBalls("hpballs" ,visible=0, protected=True)
        #g = Spheres( "cpk", quality=0 ,visible=0, protected=True)
#        g.pmvmol =obj
        geomC.addGeom(g, parent=geomC.masterGeom, redo=0)
        self.managedGeometries.append(g)
        geomC.geomPickToBonds['hpballs'] = None
        for atm in obj.allAtoms:
            atm.colors['hpballs'] = (1.0, 1.0, 1.0)
            atm.opacities['hpballs'] = 1.0
#        geomC.masterGeom.isScalable =1 
#        g.initialiseCamera()
        self.vf.GUI.VIEWER.useMasterDpyList=0
        
    def setupUndoBefore(self, nodes, only=False, negate=False, scaleFactor=1.0,
                        cpkRad=0.0, quality=0, byproperty = False,
                        propertyName = None, propertyLevel = 'Molecule',
                        setScale=True):

        print "in setupUndoBefore: only= ", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property = ", propertyName, "propertyLevel = ", propertyLevel




    def getLastUsedValues(self, formName='default', **kw):
        vals = apply(DisplayCommand.getLastUsedValues, (self, formName), kw)
        if vals.has_key('byproperty'):
            if vals['byproperty']:
                if vals.has_key('quality1'):
                    vals['quality']= vals.pop('quality1')
                if vals.has_key('scaleFactor1'):
                    vals['scaleFactor'] = vals.pop('scaleFactor1')
                if vals.has_key('offset'):
                    vals['cpkRad'] = vals.pop('offset')
                vals['propertyLevel'] = self.propertyLevel
            else:
                if vals.has_key('quality1'):
                    vals.pop('quality1')
                if vals.has_key('scaleFactor1'):
                    vals.pop('scaleFactor1')
                if vals.has_key('propertyName'):
                    vals.pop('propertyName')
                if vals.has_key('propertyLevel'):
                    vals.pop('propertyLevel')
                if vals.has_key('offset'):
                    vals.pop('offset')
        return vals
    

    def doit(self, nodes, only=False, negate=False, scaleFactor=0.05,
             cpkRad=0.0, quality=0,  shrink=0.1, bScale=0.05, byproperty = False, propertyName=None,
             propertyLevel='Molecule', setScale=True, unitedRadii=True, redraw=True, **kw):

        ##############################################################
        print "in  DOIT: ", "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, 'bScale=', bScale, 'shrink=',shrink
        scaleFactor, "cpkRad=", cpkRad, "quality=", quality, 
        "shrink =" , shrink, "bScale ", bScale,"property=", propertyName, 
        "propertyLevel = ", propertyLevel
        def drawAtoms( mol, atm, only, negate, scaleFactor, cpkRad, quality,
                       shrink, bScale,
                       propertyName = None, propertyLevel="Molecule",
                       setScale=True):

            if setScale:
                atm.cpkScale = scaleFactor
                atm.cpkRad = cpkRad
            _set = mol.geomContainer.atoms['hpballs']
            if len(atm) == len(mol.allAtoms):
                if negate:
                    setOff = atm
                    setOn = None
                    _set = AtomSet()
                else:
                    _set = atm
                    setOff = None
                    setOn = atm
            else:
                ##if negate, remove current atms from displayed _set
                if negate:
                    setOff = atm
                    setOn = None
                    _set = _set - atm

                ##if only, replace displayed _set with current atms 
                else:
                    if only:
                        setOff = _set - atm
                        setOn = atm
                        _set = atm
                    else: 
                        _set = atm + _set
                        setOff = None
                        setOn = _set

            mol.geomContainer.atoms['hpballs']=_set

            g = mol.geomContainer.geoms['hpballs']
            print "tpoto",len(_set)
            if len(_set)==0: 
#                g.Set(visible=0, tagModified=False)
                g.Set(vertices=[(0.,0.,0.),], inheritMaterial=False, 
                      materials=[(0.,0.,0.),], radii=[0,])
            else:
                _set.sort()   # EXPENSIVE...
                colors = map(lambda x: x.colors['hpballs'], _set)
                cd = {}.fromkeys(['%f%f%f'%tuple(c) for c in colors])
                if len(cd)==1:
                    print 'ONE COLOR'
                    colors = [colors[0]]

                cpkSF = Numeric.array(_set.cpkScale)
                if propertyName:
                    atmRadOld = atm.radius[:]
                    propvals = Numeric.array(self.getPropValues(atm, propertyName, propertyLevel), "f")
                    atm.radius = propvals
                #this is done in the shader, should be removed
                atmRad = np.array(_set.radius)
                cpkRad = np.array(_set.cpkRad)
                sphRad = cpkRad + cpkSF*atmRad
#                sphRad = cpkRad + atmRad#cpkSF
                sphRad = (sphRad/10.0).tolist()

                if propertyName:
                    atm.radius = atmRadOld
                bonds, atnobnd = _set.bonds
                indices = map(lambda x: (x.atom1._bndIndex_,
                                         x.atom2._bndIndex_), bonds)
                g.Set(vertices=_set.coords,bonds=indices, inheritMaterial=False, 
                      materials=colors, radii=sphRad, visible=1,
                      quality=quality,aScale=scaleFactor, shrink=shrink, 
                      bScale=bScale,tagModified=False)
                
                # highlight selection
                selMols, selAtms = self.vf.getNodesByMolecule(self.vf.selection, Atom)
                lMolSelectedAtmsDict = dict( zip( selMols, selAtms) )
                lSelectedAtoms = lMolSelectedAtmsDict.get(mol, None)
                if lSelectedAtoms is not None:
                    lVertexClosestAtomSet = mol.geomContainer.atoms['hpballs']
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
                
        molecules, atmSets = self.getNodes(nodes)
        setOn = AtomSet([])
        setOff = AtomSet([])
        try:
            radii = molecules.allAtoms.radius
        except:
            self.vf.assignAtomsRadii(molecules, 
                                     overwrite=False, topCommand=False)

        for mol, atms in map(None, molecules, atmSets):
            if 'hpballs' not in mol.geomContainer.geoms:
                self.onAddObjectToViewer(mol)
            if byproperty:
                son, sof = drawAtoms(
                    mol, atms, only, negate, scaleFactor, cpkRad,
                    quality, shrink, bScale,propertyName, propertyLevel,setScale=setScale)
            else:
                son, sof = drawAtoms(mol, atms, only, negate, 
                                     scaleFactor, cpkRad, quality,
                                     shrink, bScale,setScale=setScale)
            if son: setOn += son
            if sof: setOff += sof

        if only and len(molecules)!=len(self.vf.Mols):
            mols = self.vf.Mols - molecules
            for mol in mols:
                only = False
                negate = True
                if byproperty:
                    son, sof = drawAtoms(
                        mol, mol.allAtoms, only, negate, scaleFactor, cpkRad,
                        quality, shrink, bScale,propertyName, propertyLevel, setScale)
                else:
                    son, sof = drawAtoms(mol, mol.allAtoms, only, negate, 
                                         scaleFactor, cpkRad, quality,shrink, bScale,
                                         setScale=setScale)
                if son: setOn += son
                if sof: setOff += sof
                
        redraw = False
        if kw.has_key("redraw") : redraw=True
#        if not self.camera_initialized :
#            g = molecules[0].geomContainer.geoms['hpballs']
##            g.initialiseCamera()
#            self.initialiseCamera(g,self.vf.GUI.VIEWER.cameras[0].width)
                             
        if self.createEvents:
            event = EditGeomsEvent(
            'hpballs', [nodes,[only, negate,scaleFactor,cpkRad,quality,shrink, bScale,
                           byproperty,propertyName, propertyLevel,redraw]],
                                    setOn=setOn, setOff=setOff)
            self.vf.dispatchEvent(event)

        
    def cleanup(self):
        if hasattr(self, 'expandedNodes____AtomSets'):
            del self.expandedNodes____AtomSets
        if hasattr(self, 'expandedNodes____Molecules'):
            del self.expandedNodes____Molecules


    def __call__(self, nodes, only=False, negate=False, 
                 scaleFactor=1.0,  cpkRad=0.0, quality=0,  shrink=0.1, bScale=0.05,
                 byproperty = False, propertyName = None,
                 propertyLevel = 'Molecule', setScale=True, **keywords):
        """None <- displayCPK(nodes, only=False, negate=False,scaleFactor=None, cpkRad=0.0, quality=None, propertyName = None, propertyLevel = 'Molecule', **kw)
           \nnodes --- TreeNodeSet holding the current selection
           \nonly --- Boolean flag when True only the current selection will be
                    displayed
           \nnegate --- Boolean flag when True undisplay the current selection
           \nscaleFactor --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default is 1.0)
           \ncpkRad --- value used to compute the radii of the sphere representing the atom (Sphere Radii = cpkRad + atom.radius * scaleFactor (default 0.0)
           \nquality --- sphere quality default value is 10
           \nshrink --- sphere quality default value is 10
           \nbScale --- sphere quality default value is 10
           \npropertyName --- if specified,  the property is used to compute the sphere radii (Sphere Radii = cpkRad + property * scaleFactor),
           \npropertyLevel --- can be one of the following: 'Atom', 'Residue', 'Chain', 'Molecule'.
           \nsetScale --- when true atm.scaleFactor and atm.cpkRad are set"""

        #print "in __call__: only= ", only, "negate=", negate, "scaleFactor=", scaleFactor, "cpkRad=", cpkRad, "quality=", quality, "property = ", propertyName, "propertyLevel = ", propertyLevel, "kw:", keywords, "nodes:", nodes
        kw = {}
        if not keywords.has_key('redraw'): kw['redraw'] = True
        if not type(scaleFactor) in [IntType, FloatType,
                                    LongType]: return 'ERROR'
        if not isinstance(quality, IntType) and quality>=0:
            return 'ERROR'
        kw['only'] = only
        kw['negate'] = negate
        kw['scaleFactor'] = scaleFactor
        kw['cpkRad'] = cpkRad
        kw['quality'] = quality
        kw['setScale']= setScale#atom scale
        kw['shrink']= shrink
        kw['bScale']= bScale
        #shrinks=0.1,bdScale=0.05
        if propertyName is not None:
            if type(propertyName) != types.StringType:
                propertyName = propertyName[0]
            kw['propertyName'] = propertyName
            kw['propertyLevel']= propertyLevel
            byproperty = True
            kw['byproperty'] = byproperty
        else:
            byproperty = False

        if type(nodes) is StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return
        kw.update(keywords)
        apply( self.doitWrapper, (nodes,), kw)
        
        #if self.showAtomProp.get() != byproperty:
        #   self.showAtomProp.set(byproperty)
        self.lastUsedValues['default']['byproperty'] = byproperty
        self.lastUsedValues['default']['propertyName'] = propertyName
  


    def updateLevel_cb(self, tag):
        if tag != self.propertyLevel:
            self.propertyLevel = tag
            
        #if self.molDict[tag]  != self.vf.ICmdCaller.level.value:
            #self.vf.setIcomLevel(self.molDict[tag])
            #force a change of selection level too in order to get
            #list of property values at 'tat' level
            #self.vf.setSelectionLevel(self.molDict[tag])

            lSelection = self.vf.getSelection().uniq().findType(
                self.molDict[tag]).uniq()
            lSelection.sort()
            self.updateChooser(lSelection)


    def buildFormDescr(self, formName='default'):
        # Need to create the InputFormDescr here if there is a gui.
        if formName == 'default':
            idf = DisplayCommand.buildFormDescr(
                self, formName, title ="Display QuteMol:")

            defaultValues = self.lastUsedValues['default']
            idf.append({'name': 'byproperty',
                        'widgetType': Tkinter.Checkbutton,
                        'tooltip': 'allows the user to specify a property used to display/undisplay selected nodes using CPK representation',
                        'wcfg': {'text': 'By property',
                                 'variable': self.showAtomProp,
                                 'command': self.toggleInputByProp},
                        'gridcfg':{'sticky':'w'}} )
            
            idf.append({'name':'radiiGroup', #'cpkradii',
                        'widgetType':Pmw.Group,
                        'container':{'radiiGroup':"w.interior()"},
                        'wcfg':{'ring_borderwidth':3,},
                        'gridcfg':{'sticky':'we', 'columnspan':1}})
            
            idf.append({'name':'cpkRad',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The radius of the sphere for any atom is computed as Offset Radius + Atomic Radius * Scale Factor', 
                        'wcfg':{ 'labCfg':{'text':'Offset Radius:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'type':float,
                                 'precision':1,
                                 'variable':self.cpkRad_var,
                                 'value': defaultValues['cpkRad'],
                                 'continuous':1,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'scaleFactor',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The radius of the sphere for any atom is computed as Offset Radius + Atomic Radius * Scale Factor',
                        'wcfg':{ 'labCfg':{'text':'Scale Factor:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'max':100,
                                 'increment':0.01, 'type':float,
                                 'precision':2,
                                 'variable':self.aScale_var,
                                 'value': 0.05,
                                 'continuous':0,
                                 'command':self.update,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'quality',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'if quality = 0 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Sphere Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5, 'type':int, 'precision':1,
                                 'value': defaultValues['quality'],
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'shrink',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The radius of the sphere for any atom is computed as Offset Radius + Atomic Radius * Scale Factor',
                        'wcfg':{ 'labCfg':{'text':'bonds Shrink:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'max':100,
                                 'increment':0.01, 'type':float,
                                 'precision':2,
                                 'value': 0.1,
                                 'variable':self.shrink_var,
                                 'continuous':0,
                                 'command':self.update,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})

            idf.append({'name':'bScale',
                        'parent':'radiiGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'The radius of the sphere for any atom is computed as Offset Radius + Atomic Radius * Scale Factor',
                        'wcfg':{ 'labCfg':{'text':'bonds Scale:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0.0, 'max':100,
                                 'increment':0.01, 'type':float,
                                 'precision':2,
                                 'value':0.05,
                                 'continuous':0,
                                 'variable':self.bScale_var,
                                 'command':self.update,
                                 'oneTurn':2, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})                        
            idf.append({'name':'shadersgroup', #'cpkradii',
                        'widgetType':Pmw.Group,
                        'container':{'shadersgroup':"w.interior()"},
                        'wcfg':{'ring_borderwidth':3,},
                        'gridcfg':{'sticky':'we', 'columnspan':1}})
            #for sh in self.shaders:
            #or radiobutton
            idf.append({'name': "shaders",
                        'parent':'shadersgroup',
                        'widgetType': Pmw.OptionMenu,
                        'tooltip': 'allows the user to specify a shader used to display/undisplay selected nodes using Qutemol representation',
                        'wcfg': {'label_text': "Choose options",
                                 #'variable': self.shaderprop,
                                 'command': self.toggleShader,
                                 'menubutton_width' : 10,
                                 'labelpos':'w',
                                 'items':self.options_adv.keys()},
                        'gridcfg':{'sticky':'w'}} )
            idf.append({'name': 'Update',
                        'widgetType': Tkinter.Button,
                        'parent':'radiiGroup',
                        'tooltip': 'allows the user to reset the AO',
                        'wcfg': {'text': 'Update',
                                 #'variable': self.showAtomProp,
                                 'command': self.update},
                        'gridcfg':{'sticky':'w'}} )
#            idf.append({'name': 'draw_axes',
#                        'widgetType': Tkinter.Checkbutton,
#                        'tooltip': 'draw axes and light direction',
#                        'wcfg': {'text': 'draw axes',
#                                 'variable': self.shaderprop,
#                                 'command': self.toggleDrawAxis},
#                        'gridcfg':{'sticky':'w'}} )
#            idf.append({'name': 'pmvTransf',
#                        'widgetType': Tkinter.Checkbutton,
#                        'tooltip': 'use dejavu transformation type',
#                        'wcfg': {'text': 'pmv transformation',
#                                 'variable': self.pmvtransf,
#                                 'command': self.togglepmvtransf},
#                        'gridcfg':{'sticky':'w'}} )
#            idf.append({'name': 'pmvProj',
#                        'widgetType': Tkinter.Checkbutton,
#                        'tooltip': 'use dejavu projection',
#                        'wcfg': {'text': 'pmv projection',
#                                 'variable': self.pmvproj,
#                                 'command': self.togglepmvproj},
#                        'gridcfg':{'sticky':'w'}} )
                        
            return idf

    def guiCallback(self):
        
        nodes = self.vf.getSelection()
        if not nodes:
            self.warningMsg("no nodes selected")
            return

        val = self.showForm()
        kw ={}

        if val:
            kw['redraw'] = True
            if val['display']=='display':
                kw['only']= False
                kw['negate'] = False

            elif val['display']=='display only':
                kw['only'] = True
                kw['negate'] = False

            elif val['display']== 'undisplay':
                kw['negate'] = True
                kw['only'] = False
                del val['display']
            bp = val.get("byproperty")
            if not bp:
                kw['quality'] = int(val['quality'])
                kw ['cpkRad'] = val['cpkRad']
                kw['scaleFactor']= val['scaleFactor']
                kw['bScale']= val['bScale']
                kw['shrink']= val['shrink']
            else:
                kw['byproperty'] = val['byproperty']
                kw['propertyName'] = val['propertyName'][0]
                kw ['cpkRad'] = val['offset']
                kw['quality'] = int(val['quality1'])
                kw['scaleFactor']= val['scaleFactor1']
                kw['propertyLevel'] = self.propertyLevel
            apply(self.doitWrapper, (nodes,), kw)


    def toggleShader(self,name):
        print name
#        geom = self.managedGeometries[0]
#        geom.setOption(name)
#        geom.Set(self.options_adv[name])
#        geom.shrink = self.options_adv[name]
#        geom.aScale = self.options_adv[name]
#        geom.bScale = self.options_adv[name]
#        geom.initialise()
        nodes = self.vf.getSelection()
        apply(self.doitWrapper, (nodes,), self.options_adv[name])
        self.vf.GUI.VIEWER.OneRedraw()

    def update(self,*args,**kw):
#        geom = self.managedGeometries[0]
#        geom.shrink =self.shrink_var.get() 
#        geom.bScale =self.aScale_var.get() 
#        geom.aScale =self.bScale_var.get()
#        print "update ",geom.aScale,geom.bScale,geom.shrink
#        geom.initialise()                
        kw = {'shrink':self.shrink_var.get() , 'scaleFactor':self.aScale_var.get()  ,  'bScale':self.bScale_var.get(), 'cpkRad':0.5 }
        nodes = self.vf.getSelection()
        apply(self.doitWrapper, (nodes,), kw)
        self.vf.GUI.VIEWER.OneRedraw()
       
#
#    def resetAO(self):
#        self.managedGeometries[0].ResetAO()
#        self.vf.GUI.VIEWER.OneRedraw()
#        
#    def toggleDrawAxis(self):
#        #print "toggleInputByProp",
#        val = self.showAtomProp.get()
#        self.managedGeometries[0].draw_axis = val
#    
#    def togglepmvtransf(self):
#        #print "toggleInputByProp",
#        val = self.pmvtransf.get()
#        self.managedGeometries[0].pmvTransf = val
#    
#    def togglepmvproj(self):
#        #print "toggleInputByProp",
#        val = self.pmvproj.get()
#        self.managedGeometries[0].pmvProj = val

    def toggleInputByProp(self):
        #print "toggleInputByProp",
        val = self.showAtomProp.get()
        form = self.cmdForms['default']
        
        if val:
            form.descr.entryByName['radiiGroup']['widget'].grid_forget()
            defaultValues = self.lastUsedValues['default']
            if not form.descr.entryByName.get('propsGroup'):
                lSelection = self.vf.getSelection().uniq().findType(
                self.molDict[self.propertyLevel]).uniq()
                lSelection.sort()
                #molecules, atmSet = self.getNodes(self.vf.getSelection())
                #properties = self.getProperties(atmSet[0])
                properties = self.getProperties(lSelection)
                propertyNames = map(lambda x: (x[0],None), properties)
                propertyNames.sort()
                descr = []
                descr.append ({'name':'propsGroup',
                        'widgetType':Pmw.Group,
                        'container':{'propsGroup':"w.interior()"},
                        
                        'wcfg':{'ring_borderwidth':3,},
                        'gridcfg':{'sticky':'we', 'columnspan':1}})
                
                descr.append({'widgetType':Pmw.RadioSelect,
                              'parent':'propsGroup',
                              'name':'propertyLevel',
                              'listtext':['Atom', 'Residue', 'Chain','Molecule'],
                              'defaultValue':self.propertyLevel,'listoption':self.leveloption,
                              'wcfg':{'label_text':'Change the property level:',
                                      'labelpos':'nw','orient': Tkinter.VERTICAL,
                                      'buttontype': "radiobutton",
                                      'command':self.updateLevel_cb,
                                      },
                            'gridcfg':{'sticky':'we','columnspan':2}})
                
                
                descr.append({'name':'propertyName',
                       'parent':'propsGroup',
                       'widgetType':ListChooser,
                       'required':1,
                       'wcfg':{'entries': propertyNames,
                               'title':'Choose property:',
                               'lbwcfg':{'exportselection':0},
                               'mode':'single','withComment':0,
                               'command':self.updateValMinMax
                               },
                       'gridcfg':{'sticky':'we', 'rowspan':4, 'padx':5}#, 'columnspan':2}
                              })
                descr.append({'name':'valueMiniMaxi',
                        'widgetType':Pmw.Group,
                        'parent':'propsGroup',
                        'container':{"valminimaxi":'w.interior()'},
                        'wcfg':{'tag_text':"Property Values:"},
                        'gridcfg':{'sticky':'wnse'}})
##                 descr.append({'name':"valMin",
##                             'widgetType':Pmw.EntryField,
##                             'parent':'valminimaxi',
##                             'wcfg':{'label_text':'Minimum',
##                                     'labelpos':'w'},
##                             })
##                 descr.append({'name':"valMax",
##                               'widgetType':Pmw.EntryField,
##                               'parent':'valminimaxi',
##                               'wcfg':{'label_text':'Maximum',
##                                       'labelpos':'w'},
##                               #'gridcfg':{'row': -1}
##                               })
                descr.append({'name':"valMin",
                              'widgetType': Tkinter.Label,
                              'parent':'valminimaxi',
                              'wcfg': {'text':"Minimum:"},
                              'gridcfg':{'sticky':'w', 'columnspan':2}
                              })
                descr.append({'name':"valMax",
                              'widgetType': Tkinter.Label,
                              'parent':'valminimaxi',
                              'wcfg': {'text':"Maximum:"},
                              'gridcfg':{'sticky':'w', 'columnspan':2}
                              })
                
                
                descr.append({'name':'offset',
                          'parent':'propsGroup',
                          'widgetType':ThumbWheel,
                          'tooltip':' Radii of the sphere geom representing the atom will be equal to ( PropertyValue * Scale Factor + Offset)', 
                          'wcfg':{ 'labCfg':{'text':'Offset:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                   'showLabel':1, 'width':100,
                                   'min':0.0, 'type':float,
                                   'precision':1,
                                   'value': defaultValues.get('cpkRad', 0.0),
                                   'continuous':1,
                                   'oneTurn':2, 'wheelPad':2, 'height':20},
                          'gridcfg':{'sticky':'e'}#, 'columnspan':2}
                              })

                descr.append({'name':'scaleFactor1',
                      'parent':'propsGroup',
                      'widgetType':ThumbWheel,
                      'tooltip':'The Radii of the sphere geom representing the atom will be equal to (CPK Radii + Atom Radii * Scale Factor)',
                      'wcfg':{ 'labCfg':{'text':'Scale Factor:', 
                                         'font':(ensureFontCase('helvetica'),12,'bold')},
                               'showLabel':1, 'width':100,
                               'min':0.1, 'max':100,
                               'increment':0.01, 'type':float,
                               'precision':1,
                               'value': defaultValues.get('scaleFactor', 1.0),
                               'continuous':1,
                               'oneTurn':2, 'wheelPad':2, 'height':20},# 'columnspan':2},
                      'gridcfg':{'sticky':'e'} })
                descr.append({'name':'quality1',
                        'parent':'propsGroup',
                        'widgetType':ThumbWheel,
                        'tooltip':'if quality = 0 a default value will be determined based on the number of atoms involved in the command',
                        'wcfg':{ 'labCfg':{'text':'Sphere Quality:', 
                                           'font':(ensureFontCase('helvetica'),12,'bold')},
                                 'showLabel':1, 'width':100,
                                 'min':0, 'max':5, 'type':int, 'precision':1,
                                 'value': defaultValues.get('quality', 2),
                                 'continuous':1,
                                 'oneTurn':10, 'wheelPad':2, 'height':20},
                        'gridcfg':{'sticky':'e'}})
                
                for entry in descr:
                    form.addEntry(entry)
                    form.descr.entryByName[entry['name']] = entry
                form.autoSize()
            else:
                w = form.descr.entryByName['propsGroup']
                apply( w['widget'].grid ,(),w['gridcfg'])
                form.autoSize()
        else:
            if form.descr.entryByName.get('propertyName').has_key('required'):
                form.descr.entryByName.get('propertyName').pop('required')
            if form.descr.entryByName.get('propsGroup'):
                form.descr.entryByName['propsGroup']['widget'].grid_forget()
            w = form.descr.entryByName['radiiGroup']
            apply( w['widget'].grid ,(),w['gridcfg'])
            form.autoSize()


    def updateValMinMax(self, event=None):
        #print "updateValMinMax"
        ebn = self.cmdForms['default'].descr.entryByName
        widget = ebn['propertyName']['widget']
        properties = widget.get()
        if len(properties)==0:
            propValues=None
        else:
            propValues = self.getPropValues(self.vf.getSelection(),
                                            properties[0], self.propertyLevel)
            #print "in update:", propValues
        minEntry = ebn['valMin']['widget']
        maxEntry = ebn['valMax']['widget']
        self.getVal = 1
        if propValues is None :
            mini = 0
            maxi = 0
        else:
            mini = min(propValues)
            maxi = max(propValues)
        minEntry.configure(text="Minimum: " + str(mini))
        maxEntry.configure(text="Maximum: " + str(maxi))
        #minEntry.setentry(mini)
        #maxEntry.setentry(maxi)


    def getPropValues(self, nodes, prop, propertyLevel=None):
        #import pdb;pdb.set_trace()
        try:
            if propertyLevel is not None:
                #lNodesInLevel = self.vf.getSelection().findType(self.molDict[propertyLevel])
                lNodesInLevel = nodes.findType(self.molDict[propertyLevel])     
                num = len(lNodesInLevel.findType(Atom))
                propValues = getattr(lNodesInLevel, prop)
            else:
                propValues = getattr(nodes, prop)
        except:
            msg= "Some nodes do not have the selected property, therefore the \
current selection cannot be colored using this function."
            self.warningMsg(msg)
            propValues=None
        return propValues

    def getProperties(self, selection):
        properties = filter(lambda x: type(x[1]) is types.IntType \
                                 or type(x[1]) is types.FloatType,
                                 selection[0].__dict__.items())

        # Filter out the private members starting by __.
        properties = filter(lambda x: x[0][:2]!='__', properties)
        return properties
        

    def updateChooser(self, selection):
        ## if not hasattr(self, 'properties'): self.properties = []
##         oldProp = self.properties
##         self.properties = filter(lambda x: isinstance(x[1], IntType) \
##                                  or isinstance(x[1], FloatType),
##                                  selection[0].__dict__.items())

##         # Filter out the private members starting by __.
##         self.properties = filter(lambda x: x[0][:2]!='__', self.properties)
        properties = self.getProperties(selection)
        
        if self.cmdForms.has_key('default'):
            # If the list of properties changed then need to update the listbox
            ebn = self.cmdForms['default'].descr.entryByName
            widget = ebn['propertyName']['widget']
            propertyNames = map(lambda x: (x[0],None),properties)
            propertyNames.sort()
            oldsel = widget.get()
            widget.setlist(propertyNames)
            if len(oldsel)>0 and (oldsel[0], None) in propertyNames:
                widget.set(oldsel[0])
            

displayHyperBallsGuiDescr = {'widgetType':'Menu', 'menuBarName':'menuRoot',
                     'menuButtonName':'Display', 'menuEntryLabel':
                     'HyperBalls' }

DisplayHyperBallsGUI = CommandGUI()
DisplayHyperBallsGUI.addMenuCommand('menuRoot', 'Display', 'HyperBalls')

commandList=[{'name':'displayHyperBalls','cmd': DisplayHyperBalls(), 'gui': DisplayHyperBallsGUI},]

def initModule(viewer):
    for dict in commandList[:-1]:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
#self.browseCommands('displayHyperBalls', commands=['displayHyperBalls'], package="Pmv", topCommand=0)