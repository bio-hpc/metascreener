## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

######################################################################
#
# Date: Jan 2004 Author: Daniel Stoffler, Yong Zhao
#
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler and TSRI
#
#########################################################################

import weakref, types
import numpy.oldnumeric as Numeric
N=Numeric
from NetworkEditor.items import NetworkNode
#from ViewerFramework.VFCommand import Command
from ViewerFramework.VF import ModificationEvent 
from Vision import UserLibBuild

from FlexTree.FT import FTNode, FlexTree
from FlexTree.FTMotions import FTMotion, FTMotion_Hinge 
from FlexTree.FTShapes import FTShape, FTLines, FTEllipsoid
from FlexTree.FTConvolutions import FTShapeMotionConvolve,FTConvolveIdentity,\
     FTConvolveApplyMatrix, FTConvolveApplyMatrixToCoords

from FlexTree.FTShapeCombiners import FTShapesCombiner
from FlexTree.XMLParser import ReadXML, WriteXML
from FlexTree.VisionInterface.utils import addTreeToVision
from FlexTree.VisionInterface.utils import TreeBuilder

#from FlexTree.FTRotamers import _chooseRotamerClass
from FlexTree.EssentialDynamics import EssentialDynamics
from FlexTree.FTMotions import FTMotion_Rotamer
from warnings import warn

import random # for debug.

def dist(self, a,b):
    from math import sqrt
    xx= (a[0]-b[0]) **2 + (a[1]-b[1]) **2 + (a[2]-b[2]) **2
    return sqrt(xx)


def importVizLib(net):
    try:
        from DejaVu.VisionInterface.DejaVuNodes import vizlib
        net.editor.addLibraryInstance(
            vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
    except:
        import traceback
        traceback.print_exc()
        warn(
            'Warning! Could not import vizlib from DejaVu/VisionInterface')



## class FlexTreeLibraryNode(NetworkNode, TreeBuilder):

##     """This node builds a Vision FlexTree network once the node has been
## dragged to the canvas. This node will then delete itself"""

##     def __init__(self, flexTree=None, name='FlexTree Dummy Node', **kw):
##         #print "!!!", flexTree
##         #assert isinstance(flexTree, FlexTree)
##         self.flexTree = flexTree
##         kw['name'] = name
##         apply( NetworkNode.__init__, (self,), kw )
##         TreeBuilder.__init__(self)        
##         self.lastX = 0
## 	code = """def doit(self):
##     pass
## """
##         if code: self.setFunction(code)


##     def afterAddingToNetwork(self):
##         NetworkNode.afterAddingToNetwork(self)
##         posx = self.posx
##         posy = self.posy
##         # build tree with Vision FlexTree nodes
##         self.buildTree(self.flexTree, posx, posy)
##         # finally, delete myself
##         self.editor.currentNetwork.deleteNodes([self])


# check if AutoDockFR is installed

try:
    import AutoDockFR
    foundAutoDockFR = True
except ImportError:
    #import traceback, sys
    #type, value, tb = sys.exc_info()
    #traceback.print_exception(type, value, tb)
    #import traceback
    #traceback.print_exc()
    foundAutoDockFR = False    

# check if AutoDock Scorer (C++) is installed
try:
    from cAutoDock.scorer import CoordsVector, Coords, MolecularSystem,\
         updateCoords #, MolKitMolecularSystem
    foundAutoDockC = True
except ImportError:
    foundAutoDockC = False


if foundAutoDockFR:

    from AutoDockFR.FTGA import  FTtreeGaRepr, OneFT_GaRepr
    from AutoDockFR.ScoringFunction import AD305Scoring, RMSDScoring

    class RMSDScoringNode(NetworkNode):
        """Output a scoring object for GA.
    The score will be the RMDS between the candidate conformation and the
    reference set of coordinates

    Input:
        refCoords: reference set of coordinates
    Output:
        scoringObject: RMSD scoring object
    """

        def __init__(self, name='RMSD score', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )
            
            self.RMSDscorer = RMSDScoring()

            self.widgetDescr['selection'] = {
                'class':'NEComboBox', 'master':'node',
                'choices':['All',
                           'Backbone',
                           'C-alpha' ],
                'fixedChoices':True,
                'initialValue':'All',
                'entryfield_entry_width':25,
                'labelGridCfg':{'sticky':'w'},
                'widgetGridCfg':{'sticky':'w', 'columnspan':2},
                'labelCfg':{'text':'Select Atoms'},
            }
            self.widgetDescr['superimpose'] = {
            'class':'NECheckButton', 'master':'node',
            'type':'boolean',
            'initialValue':True,
            'labelCfg':{'text':'Superimpose'},
            'widgetGridCfg':{'sticky':'w', 'sticky':'w', 'columnspan':2},
            }


            ip = self.inputPortsDescr
            #ip.append(datatype='coordinates3D', name='currentConf')
            #ip.append(datatype='FlexTree', name='tree')
            ip.append(datatype='AtomSet', name='mobAtomset')
            #ip.append(datatype='coordinates3D', name='refCoords')
            ip.append(datatype='AtomSet', name='refAtomset')

            ip.append(datatype='string', required=False, name='selection')
            ip.append(datatype='boolean', required=False, name='superimpose')
 

            op =self.outputPortsDescr 
            op.append(datatype='scoreObject', name='scoringObject')

            code = """def doit(self, mobAtomset, refAtomset, selection, superimpose):
        self.RMSDscorer.configure(mobAtomset=mobAtomset,refAtomset=refAtomset,\
                                  selection=selection, superimpose=superimpose)
        self.outputData(scoringObject=self.RMSDscorer)
"""

            self.setFunction(code)


        def beforeAddingToNetwork(self, net):
            try:
                from MolKit.VisionInterface.MolKitNodes import molkitlib
                net.editor.addLibraryInstance(molkitlib,
                    'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
            except:
                warn('Warning! Could not import molkitlib from MolKit/Vision')



    class AD305ScoringNode(NetworkNode):
        """Output a scoring object for GA.
    The score will be the AutoDock energy

    Input:
        atomset1: receptor
        atomset2: ligand
    Output:
        scoringObject: AutoDock305 scoring object
    """

        def __init__(self, name='AD305 score', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )

            ip = self.inputPortsDescr
            ip.append(datatype='AtomSet', name='atomset1')
            ip.append(datatype='AtomSet', name='atomset2')

            op =self.outputPortsDescr 
            op.append(datatype='scoreObject', name='scoringObject')

            code = """def doit(self, atomset1, atomset2):
    self.scorer = AD305Scoring(atomset1, atomset2)
    self.outputData(scoringObject=self.scorer)
"""

            self.setFunction(code)

        
        def beforeAddingToNetwork(self, net):
            try:
                from MolKit.VisionInterface.MolKitNodes import molkitlib
                net.editor.addLibraryInstance(molkitlib,
                    'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
            except:
                warn('Warning! Could not import molkitlib from MolKit/Vision')


                
    class FTGA(NetworkNode):
        """perform a GA search on a Flexibility Tree

Input:
    GaRepr: Object representing a Genome for GA search
    scoreObject: object used to score a conformations
    nbGenerations: number of generations
    popSize: population size
Output:
    genome:  FTtreeGaRepr instance
"""
# demo of how to use scipy GA package can be found in
# ..../i86Linux2/lib/python2.3/site-packages/scipy/ga/examples.py
        def __init__(self, name='FTGA', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )

            self.scoreObject = None
            self.motionObjs = None
            self.counter=0

            self.widgetDescr['p_replace'] = {
                'class':'NEDial', 'master':'ParamPanel', 'size':40,
                'oneTurn':1.0, 'type':'float',
                'initialValue':0.80,
                'labelCfg':{'text':'Probability of replacement'},
                'widgetGridCfg':{'labelSide':'left'},
                }

            self.widgetDescr['p_cross'] = {
                'class':'NEDial', 'master':'ParamPanel', 'size':40,
                'oneTurn':1.0, 'type':'float',
                'initialValue':0.80,
                'labelCfg':{'text':'Probability of crossover'},
                'widgetGridCfg':{'labelSide':'left'},
                }

            self.widgetDescr['capture_Frame'] = {
                'class':'NEComboBox', 'master':'node',
                'choices':['Capture Every Frame',
                           'Redraw Viewer'],
                'fixedChoices':True,
                'initialValue':'Redraw Viewer',
                'entryfield_entry_width':25,
                'labelGridCfg':{'sticky':'w'},
                'widgetGridCfg':{'sticky':'w', 'columnspan':2},
                'labelCfg':{'text':'Select Callback for each GA run'},
            }
            
            ip = self.inputPortsDescr
            ip.append(datatype='FlexTree', name='receptorFlexTree')
            ip.append(datatype='FlexTree', required=False,
                      name='ligandFlexTree')
            ip.append(datatype='scoreObject', name='scoreObject')
            ip.append(datatype='int', name='nbGenerations')
            ip.append(datatype='int', name='popSize')
            ip.append(datatype='viewer', required=False, name='viewer')
            ip.append(datatype='float', name='p_replace')
            ip.append(datatype='float', name='p_cross')
            ip.append(datatype='boolean', name='capture_Frame')

            op = self.outputPortsDescr
            op.append(datatype='list', name='best')
            op.append(datatype='None', name='genome')
            op.append(datatype='None', name='trigger')

            code = """def doit(self, receptorFlexTree, ligandFlexTree,scoreObject, nbGenerations, popSize, viewer, p_replace, p_cross,capture_Frame):
    self.viewer = viewer
    if capture_Frame=='Capture Every Frame':
        self.counter = 0
        beforePerf_cb = self.captureScreen_cb
    else: # the default callback 'Redraw Viewer'
        beforePerf_cb = self.redraw_cb

    if scoreObject.__class__=='RMSDScoring':
        self.gnm = gnm = OneFT_GaRepr(receptorFlexTree,
                                  scoreObject,
                                  beforePerf_cb=beforePerf_cb) 
    else:
        self.gnm = gnm = FTtreeGaRepr(receptorFlexTree,
                                  ligandFlexTree,scoreObject,
                                  beforePerf_cb=beforePerf_cb)    
    # Create a population of the genomes.
    pop = ga.population.population(gnm)
    pop.min_or_max('min')
    # Now use the basic genetic algorithm to evolve the population
    self.galg = galg = ga.algorithm.galg(pop)
  

    # change a few settings
    if p_replace >1.0 or p_replace <0.0 or p_cross>1.0 or p_cross>1.0:
        return 
    settings = {'pop_size':popSize,
                'p_replace':p_replace,'p_cross': p_cross, 'p_mutate':'gene',
                'p_deviation': 0.000001,'gens':nbGenerations,
                'rand_seed':0,'rand_alg':'CMRG'}
    galg.settings.update(settings)
##     print "********"
##     print galg.settings
##     print "********"
    from mglutil.util.callback import CallBackFunction
    cb = CallBackFunction(self.postGeneration_cb)
    galg.addCallback('postGeneration', cb)
#    cb = CallBackFunction(self.postStep_cb)
#    galg.addCallback('postStep', cb)
    galg.evolve()
    print " ***  evolution finished ***"
    print
    best=galg.pop.best()
    bestList=[]
    for b in best:
        bestList.append( float(b) )
    self.outputData(best=bestList, genome=gnm)
"""
            if code: self.setFunction(code)

        def checkStatus(self):
            self.network.canvas.update()
            stop = self.network.checkExecStatus()
            if stop:
                return 'end'
            
        def redraw_cb(self):
            self.network.canvas.update()
            galg = self.galg
            if self.viewer:
                node=self.gnm.motionObjs[0].node
                if node:
                    #root = node().tree().root
                    #root.newMotion=True
                    #root.updateConvolution()
                    rRoot=self.gnm.receptorRoot
                    rRoot.newMotion=True
                    rRoot.updateConvolution()
                    
                    lRoot=self.gnm.ligRoot
                    lRoot.newMotion=True
                    lRoot.updateConvolution()
                    self.viewer.Redraw()

        def captureScreen_cb(self):
            self.network.canvas.update()
            galg = self.galg
            if self.viewer:
                node=self.gnm.motionObjs[0].node
                if node:
##                     root = node().tree().root
##                     root.newMotion=True
##                     root.updateConvolution()
                    rRoot=self.gnm.receptorRoot
                    rRoot.newMotion=True
                    rRoot.updateConvolution()
                    
                    lRoot=self.gnm.ligRoot
                    lRoot.newMotion=True
                    lRoot.updateConvolution()                    
                    self.viewer.Redraw()
                    camera = self.viewer.cameras[0]
                    camera.Activate()
                    image = camera.GrabFrontBuffer()
                    filename='file%08d.png'%self.counter
                    image.save(filename)
                    self.counter +=1

                
        def postGeneration_cb(self):
            if self.network:
                stat = self.checkStatus()
                galg = self.galg
                if stat == 'end':
                    galg.gen = galg.settings['gens']
                    
            best = galg.pop.best()
            print "Best Gene:",best
            print "++++++++++++++++++++++++++++++++++"
        
            if self.viewer:
                print '__________________________________'
                print
                print
                coords = self.gnm.toPhenotype(best)
                node=self.gnm.motionObjs[0].node
                if node:
                    root = node().tree().root
                    #root.updateCurrentConformation()
                    root.updateConvolution()
                    self.viewer.Redraw()


        def postStep_cb(self):
            print 'postReplace'
            self.network.canvas.update()
            stop = self.network.checkExecStatus()
            galg = self.galg
            if stop:
                return 'end'
##             if self.viewer:
##                 best = galg.pop.best()
##                 coords = self.gnm.toPhenotype(best)
##                 root = self.gnm.motionObjs[0].node().tree().root
##                 root.updateCurrentConformation()
##                 root.updateShape
##                 self.viewer.Redraw()


        def beforeAddingToNetwork(self, net):
            try:
                from DejaVu.VisionInterface.DejaVuNodes import vizlib
                net.editor.addLibraryInstance(
                    vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
            except:
                warn('Warning! Could not import vizlib from DejaVu/VisionInterface')




    class ConfigureTreeFromGene(NetworkNode):
        """Update the conformation with gene.
    This node takes a tree instance and a genome (setting of motion objects),
    configure the tree with the genome

    Input: FlexTree: a FlexTree Object
           gene: a list of values

"""

        def __init__(self, name='ConfigureTreeFromGene', **kw):
            kw['name'] = name
            apply(NetworkNode.__init__, (self,), kw )

            ip = self.inputPortsDescr #instanceMatrices
            ip.append(datatype='FlexTree', name='R_tree')
            ip.append(datatype='FlexTree', name='L_tree')
            ip.append(datatype='None', name='genome')
            ip.append(datatype='list', name='best')
            
            op = self.outputPortsDescr
            op.append(datatype='coordinates3D', name='coords')
            
            code = """def doit(self, R_tree,L_tree , genome, best):
        # configure the conformaton with best score
        coords = genome.toPhenotype(genome=best, sort=True)
        R_tree.root.updateConvolution()
        L_tree.root.updateConvolution()        
        self.outputData(coords = coords )
        
"""
            if code: self.setFunction(code)


    class PrintScoreNode(NetworkNode):
        """Output a score of given scoring object
    The score will be the AutoDock energy.

    Input:
        scoringObject: AutoDock305 scoring object
    Output:
        None, the score from scoringObject is printed
    """

        def __init__(self, name='AD305 score', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )
            self.bestScore = 99999

            ip = self.inputPortsDescr
            ip.append({'name':'scoringObject', 'datatype':'scoreObject'})

            code = """def doit(self, scoringObject):
    ADscore = scoringObject.scorer.get_score()
    print 'score =%10.3f'%(ADscore,),
    if hasattr(scoringObject, 'calcInternalEnergy'):
        if scoringObject.calcInternalEnergy:
            IE = scoringObject.internal_E.get_score()
            print "Internal E =%10.3f,Total Score =%10.3f "%(IE, ADscore + IE),

    print
"""
            self.setFunction(code)


    class ScoreContributionFromAtomsNode(NetworkNode):
        """Find out the AutoDock energy contribution from each atom and assign
it as an attribute of Atom 

    Input:
        scoringObject: AutoDock305 scoring object
    Output:
        list of energy contribution from each atom.
    """

        def __init__(self, name='AD305 score', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )

            ip = self.inputPortsDescr
            ip.append({'name':'scoringObject', 'datatype':'scoreObject'})

            op = self.outputPortsDescr
            op.append(datatype='list', name='contrib')

            code = """def doit(self, scoringObject):
    if hasattr(scoringObject, 'sharedMem'): # no appliable for C++ version
        print "no appliable for C++ scorer"
        return
    ADScoreArray = scoringObject.scorer.get_score_array()
    atoms=scoringObject.molSyst.get_entities()
    contrib=[]
    assert len(atoms) == len(ADScoreArray)
    for i in range(len(ADScoreArray)):
        e = Numeric.add.reduce(ADScoreArray[i])
        if i == 0:
            e=0.0 # quick hack to solve the problem of desovation.py (line 113)
        atoms[i].energyContribution =  e
        contrib.append(e)   

    print 
    self.outputData(contrib=contrib)
"""

            self.setFunction(code)

    

if foundAutoDockFR and foundAutoDockC:

    from AutoDockFR.ScoringFunction import AD305ScoreC
    
    class AD305ScoringNodeC(NetworkNode):
        """Output a scoring object for GA.
    The score will be the AutoDock energy, C++ version.

    Input:
        atomset1: receptor
        atomset2: ligand
    Output:
        scoringObject: AutoDock305 scoring object
    """

        def __init__(self, name='AD305 score', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )

            ip = self.inputPortsDescr
            ip.append({'name':'atomset1', 'datatype':'AtomSet'})
            ip.append({'name':'atomset2', 'datatype':'AtomSet'})

            op =self.outputPortsDescr 
            op.append({'name':'scoringObject', 'datatype':'scoreObject'})

            code = """def doit(self, atomset1, atomset2):
    self.scorer = AD305ScoreC(atomset1, atomset2)
    self.outputData(scoringObject=self.scorer)
"""

            self.setFunction(code)

        
        def beforeAddingToNetwork(self, net):
            try:
                from MolKit.VisionInterface.MolKitNodes import molkitlib
                net.editor.addLibraryInstance(molkitlib,
                    'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
            except:
                warn('Warning! Could not import molkitlib from MolKit/Vision')


    class AD305SPENodeC(NetworkNode):
        """Output a scoring object for GA.
    The score will be the Single Point Energy of the receptor, based on
AutoDock energy, C++ version.

    Input:
        atomset1: receptor
        atomset2: ligand
    Output:
        scoringObject:  scoring object
    """

        def __init__(self, name='SPE score', **kw):
            kw['name'] = name
            apply( NetworkNode.__init__, (self,), kw )

            ip = self.inputPortsDescr
            ip.append({'name':'atomset1', 'datatype':'AtomSet'})
            #ip.append({'name':'atomset2', 'datatype':'AtomSet'})

            op =self.outputPortsDescr 
            op.append({'name':'scoringObject', 'datatype':'scoreObject'})

            code = """def doit(self, atomset1):
    self.scorer = ADSinglePoint(atomset1)
    self.outputData(scoringObject=self.scorer)
"""

            self.setFunction(code)

        
        def beforeAddingToNetwork(self, net):
            try:
                from MolKit.VisionInterface.MolKitNodes import molkitlib
                net.editor.addLibraryInstance(molkitlib,
                    'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
            except:
                warn('Warning! Could not import molkitlib from MolKit/Vision')







######

class SelectAtomsNode(NetworkNode):
    """Select the molecular fragment of a paticular type of atoms that are
associated with a FT tree node
e.g. find all the C-alpha atoms of chain_A.
or   find all the backbone atoms of ABC node.. etc.

this node will recursively go traverse all the children FTNodes

Input:
    FTNode: the FTNode to select from
    selection: selection criterion. (All, backbone, C-alpha only..etc.)
Output:
    atomSet: the selected AtomSet
"""

    def __init__(self, name='Select Atoms', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.widgetDescr['selection'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['All',
                       'Backbone',
                       'C-alpha' ],
            'fixedChoices':True,
            'initialValue':'All',
            'entryfield_entry_width':25,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Select Atoms'},
        }

        self.widgetDescr['sort'] = {
            'class':'NECheckButton', 'master':'node',
            'type':'boolean',
            'initialValue':True,
            'labelCfg':{'text':'Sort the Atoms'},
            'widgetGridCfg':{'sticky':'w', 'sticky':'w', 'columnspan':2},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='FlexTreeNode', name='ftNode')
        ip.append(datatype='string', name='selection')
        ip.append(datatype='boolean', required=False, name='sort')

        op =self.outputPortsDescr 
        op.append(datatype='AtomSet', name='selected')

        code = """def doit(self, ftNode, selection, sort):
    atoms=None
    if selection == 'All':
        atoms=ftNode.getAtoms()
    elif selection == 'Backbone':
        atoms=ftNode.getAtoms().get('C,N,CA,O')
    elif selection == 'Backbone':
        atoms=ftNode.get('CA')
    else:
        atoms=ftNode.get(selection) # user defined selection
    if sort :
        atoms.sort()
    self.outputData(selected=atoms)
"""

        self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        try:
            from MolKit.VisionInterface.MolKitNodes import molkitlib
            net.editor.addLibraryInstance(molkitlib,
                'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
        except:
            warn('Warning! Could not import molkitlib from MolKit/Vision')



class WritePDBNode(NetworkNode):

    """This node writes current conformation of the FlexTree to PDB file
Input:
    FTNode:   a FlexTree object
    filename: filename of XML file"""

    def __init__(self, name='Write XML', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.writer = WriteXML()

        fileTypes=[('pdb', '*.pdb'), ('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node',
            'filetypes':fileTypes, 'title':'save file', 'width':16,
            'labelCfg':{'text':'file:'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='FlexTree', name='FlexTree')
        ip.append(datatype='string', name='filename')

	code = """def doit(self, FlexTree, filename):
    if FlexTree and filename:
        nodes=FlexTree.root.getAtoms()
        mol = nodes.top.uniq()
        assert len(mol)==1
        recType = 'all'  
        nodes.sort()
        from MolKit import WritePDB
        WritePDB(filename, nodes)
        #mol[0].write(filename, nodes, PdbWriter(),  recType )

"""
        if code: self.setFunction(code)



class WriteXMLNode(NetworkNode):

    """This node writes XML code of a FlexTree object.
Please note: any shape, motion, etc. node connected to a FlexTree node will
incorporated into the FTNode the next time the XML file is loaded. Any widgets
of shape, motion, ect. nodes will be added to the param. panel of the FTNode

Input:
    FTNode:   a FlexTree object
    filename: filename of XML file"""

    def __init__(self, name='Write XML', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.writer = WriteXML()

        fileTypes=[('xml', '*.xml'), ('all', '*')]

        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node',
            'filetypes':fileTypes, 'title':'save file', 'width':16,
            'labelCfg':{'text':'file:'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='FlexTree', name='FlexTree')
        ip.append(datatype='string', name='filename')

	code = """def doit(self, FlexTree, filename):
    if FlexTree and filename:
        if FlexTree.pdbfilename=='' or FlexTree.pdbfilename==None:
            mol=FlexTree.root.getAtoms().top.uniq()[0]
            FlexTree.pdbfilename=mol.parser.filename
        self.writer([FlexTree], filename)
"""
        if code: self.setFunction(code)


class ReadXMLNode(NetworkNode, TreeBuilder):

    """This node reads XML code describing a FlexTree object.
A FlexTree Vision network will be built, and this node will then delete itself.

Input:
    filename: filename of XML file"""

    def __init__(self, name='Read XML', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        self.reader = ReadXML()

        fileTypes=[('xml', '*.xml'), ('all', '*')]
        
        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'save file', 'width':16,
            'labelCfg':{'text':'file:'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='filename')

	code = """def doit(self, filename):
    if filename:
        self.reader(filename)
        trees = self.reader.get()
        posx = self.posx
        posy = self.posy
        for tree in trees:
            # add tree to Library
            addTreeToVision(self.editor, tree)
            # build tree with Vision FlexTree nodes
            self.buildTree(tree, posx, posy)
            posx = posx + 400
            # do this because rotamer conformation are not anchored.
            tree.root.updateCurrentConformation()
            
        # finally, delete myself
        self.editor.currentNetwork.deleteNodes([self])
"""
        if code: self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        importVizLib(net)


class FlexTreeNode(NetworkNode):

    def __init__(self, ftNode=None, name='FlexTree Node', **kw):
        if ftNode is not None:
            assert isinstance(ftNode, FTNode)
#        self.ftNode = ftNode
        if ftNode is not None:
            self.ftNode = ftNode
        else:
            self.ftNode = FTNode()

        self.tree = None

        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='FlexTreeNode', required=False, name='FlexTreeNode')
        ip.append(datatype='FTShape', required=False, name='shape')
        ip.append(datatype='FTMotion', required=False, name='motion')
        #ip.append(datatype='string', required=False, name='shape')
        #ip.append(datatype='string', required=False, name='motion')
        
        ip.append(datatype='FTConvolution', required=False, name='convolution')
        ip.append(datatype='FTCombiner', required=False, name='combiner')
        ip.append(datatype='FlexTreeNode', required=False, name='refNode')
        ip.append(datatype='boolean', required=False, name='updateConf')
        ip.append(datatype='boolean', required=False, name='updateShape')

        self.widgetDescr['updateConf'] = {
            'class':'NECheckButton', 'master':'node',
            'type':'boolean',
            'initialValue':True,
            'labelCfg':{'text':'UpdateConf'},
            'widgetGridCfg':{'sticky':'w', 'sticky':'w', 'columnspan':2},
            }

        self.widgetDescr['updateShape'] = {
            'class':'NECheckButton', 'master':'node',
            'type':'boolean',
            'initialValue':True,
            'labelCfg':{'text':'UpdateShape'},
            'widgetGridCfg':{'sticky':'w', 'sticky':'w', 'columnspan':2},
            }
        
        self.widgetDescr['convolution'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['FTConvolveIdentity',
                       'FTConvolveApplyMatrix',
                       'FTConvolveApplyMatrixToCoords' ,
                       'FTConvolveAppendInstanceMatrix' ,
                       'FTConvolveAppend'
                       ],
            'fixedChoices':True,
            'initialValue':'FTConvolveApplyMatrixToCoords',
            'entryfield_entry_width':25,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Convolution'},
            'widgetGridCfg':{'labelSide':'left'},
            'selectioncommand':self.rename,
            }

        self.widgetDescr['combiner'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['Not implemented yet',
                       'Not implemented yet',
                       'Not implemented yet' ],
            'fixedChoices':True,
            'initialValue':'Not implemented yet',
            'entryfield_entry_width':25,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Shape Combiner'},
            'widgetGridCfg':{'labelSide':'left'},
            'selectioncommand':self.rename,
            }

        self.widgetDescr['motion'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['FTMotion_Hinge',
                       'Unbind',
                       'Generic' ],
            'fixedChoices':True,
            'initialValue':'FTMotion_Hinge',
            'entryfield_entry_width':25,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Motion'},
            #'selectioncommand':self.rename,
            }

##         inputPort = self.getPortbyName('shape')
##         if inputPort != -1:
##             codeAfterConnect="""def afterConnect(self, conn):
##     # self refers to the port
##     # conn is the connection that has been created
##     currentNode = self.node.ftNode
##     name=currentNode.name
##     self.data[0].name="FTLines_" + name
##     return 
## """
##             ip[inputPort]['afterConnect']= codeAfterConnect



        op = self.outputPortsDescr
        op.append(datatype='FlexTreeNode', name='OutFTNode')
        op.append(datatype='geom', name='geoms')

	code ="""def doit(self,FlexTreeNode, shape, motion,
        convolution, combiner, refNode, updateConf,
        updateShape):

    ftNode=self.ftNode
    #print '*** ->', id(ftNode), ftNode.name
    if updateConf is None:
        updateConf=True
    if updateShape is None:
        updateShape=False

    conv=self.getConvolution(convolution)
    comb=self.getCombiner(combiner)

    m = self.getMotion(motion)
    if isinstance(motion, FTMotion):
        m=motion
    elif m == 'Unbind':
        m=ftNode.motion
        self.unbindMotion()
    else:
        m=None


    ftNode.configure(autoUpdateConf=updateConf, autoUpdateShape=updateShape,\
                     motion=m,    convolution=conv, \
                     shapeCombiner=comb, refNode=refNode,\
                     )

    if shape is not None:        
        if shape is not ftNode.shape:
            print 'new shape'
            ftNode.configure(shape=shape)
            geoms = ftNode.shape.getGeoms()
            if len(geoms)==1:
                geoms[0].name = self.name
            if len(geoms):
                self.outputData(geoms=geoms)
    elif ftNode.shape is not None:
        if ftNode.shape.__class__.__name__ == "FTLines":
            ftNode.shape.updateCrossSetGeoms()
        geoms = ftNode.shape.getGeoms()
        if len(geoms)==1:
            geoms[0].name = self.name
        if len(geoms):
            self.outputData(geoms=geoms)           
##     else:
##         # update the shape of root.. if available
##         root = ftNode.tree().root
##         if root.shape:
##             root.updateCurrentConformation()
##             root.shape.updateGeoms()
##             redrawGeom=None
##             shape=root.shape
##             for g in shape.geoms:
##                 if g.viewer is None:
##                     continue
##                 redrawGeom=g
##             if redrawGeom:
##                 redrawGeom.viewer.Redraw()



    self.outputData(OutFTNode=self.ftNode)
"""
        if code: self.setFunction(code)


    def getPortbyName(self, name):
        """return index of the port with name ='name' """
        ip = self.inputPortsDescr
        for i in range(len(ip)):
            if ip[i]['name'] == name: return i
        return -1


    def unbindMotion(self):
        """if 'Unbind' is chosen as motion, unbinds the widget, add the corresponding motion parameter panel into the network"""

        inputPort = self.getPortbyName('motion')
        motionPortDesr={'name':'motion','datatype':'FTMotion','required':False}
        self.inputPorts[inputPort].unbindWidget()
        p=self.inputPorts[inputPort]
        apply(p.configure, (1,), motionPortDesr)
        
        m=self.ftNode.motion
        if m is None : return

        # FIXME ... create motionobject using __class__
        if m.name == 'hinge':
            node = FTMotionHinge()
            self.tmpMotionNode = node
            self.network.addNode(node, self.posx + 10 , self.posy - 40.)
            ip= node.inputPorts
            
            motion = self.ftNode.motion
            node.rename(self.name+'_'+motion.name)
            setting = motion.getCurrentSetting()

            for k, v in setting.items():
                portID = node.getPortbyName(k)
                if portID == -1 :
                    #print k, 'is not a valid param as widget'
                    pass
                else:
                    node.inputPorts[portID].widget.set(v)
        else:
            # fixme : more motion other than hinge should be supported
            pass


    def getConvolution(self, convolution):
        """convolution can be an instance of a FTShapeMotionConvolve object
or the name of a subclass of FTShapeMotionConvolve."""
        if convolution==None :
            return None
        if self.ftNode == None:
            return None
        if type(convolution)==types.StringType:
            import FlexTree.FTConvolutions
            klass = getattr(FlexTree.FTConvolutions, convolution)
            assert issubclass(klass, FTShapeMotionConvolve)
            return klass(self.ftNode)
        else:
            assert isinstance(convolution, FTShapeMotionConvolve)
            convolution.setNode(self.ftNode)
            return convolution

    def getMotion(self, motion):
        """ if motion is a string, return the corresponding motion object
returns string 'Unbind', if motion == 'Unbind'.. """
        if motion==None :
            return None
        if self.ftNode.motion.__class__.__name__ != motion:
            if motion == 'FTHinge':
                return FTMotion_Hinge()
            if motion == 'FTConvolveApplyMatrix': # fixme...not motion
                return FTConvolveApplyMatrix(self.ftNode)
            if motion == 'Unbind':
                return 'Unbind'

        return None


    def getCombiner(self, combiner):
        # fixme: not implemented yet
        return None


    def beforeAddingToNetwork(self, net):
            try:
                from DejaVu.VisionInterface.DejaVuNodes import vizlib
                net.editor.addLibraryInstance(
                    vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
            except:
                warn('Warning! Could not import vizlib from DejaVu/VisionInterface')

#    def afterAddingToNetwork(self):
#        if self.ftNode is not None:
#            NetworkNode.afterAddingToNetwork(self)
#            self.schedule_cb()


    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        lines = []
        txt = NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent, ignoreOriginal)
        lines.extend(txt)
        nodeName = self.getUniqueNodeName()
        lines.append(indent+"RT.assignFlexTreeNode("+nodeName+")\n")
        return lines
    

class FlexTreeRootNode(FlexTreeNode):

    def __init__(self, ftNode=None, name='FlexTree Root Node', **kw):
        kw['name'] = name
        kw['ftNode'] = ftNode
        
        apply( FlexTreeNode.__init__, (self,), kw )
        ip = self.inputPortsDescr
        #del ip[0] # root node does not need a FlexTree input port

        op = self.outputPortsDescr
        op.append(datatype='FlexTree', name='FlexTree')
        op.append(datatype='AtomSet', name='allAtoms')
        
        
	code = """def doit(self, FlexTreeNode, shape, motion,
        convolution, combiner, refNode,
        updateConf, updateShape ):

    ftNode = self.ftNode
    if updateConf is None:
        updateConf=True
    if updateShape is None:
        updateShape=False

    conv=self.getConvolution(convolution)
    comb=self.getCombiner(combiner)
    m = self.getMotion(motion)   
    if isinstance(motion, FTMotion):
        m=motion
    elif m == 'Unbind':
        m=ftNode.motion
        self.unbindMotion()
    else:
        m=None

    ftNode.configure(autoUpdateConf=updateConf, autoUpdateShape=updateShape,\
                     motion=m   ,convolution=conv, \
                     shapeCombiner=comb,
                     #refNode=refNode,
                     shape=shape,\
                     #molFrag=molFrag
                     )

    if shape is not None or ftNode.shape is not None:
        ftNode.configure(shape=shape)
        geoms = ftNode.shape.getGeoms()
        if len(geoms):
            self.outputData(geoms=geoms)

    if ftNode.tree is not None:
        tree = ftNode.tree()
        allAtoms=tree.root.getAtoms()
    else:
        tree = None
        allAtoms=None
    self.outputData(OutFTNode=self.ftNode, FlexTree=tree,
                    allAtoms=allAtoms )
"""
        if code: self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        try:
            from MolKit.VisionInterface.MolKitNodes import molkitlib
            net.editor.addLibraryInstance(molkitlib,
                 'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
        except:
            warn('Warning! Could not import molkitlib from MolKit/Vision')




    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        lines = []
        xml = self.ftNode.tree().xmlfilename
        t1 = "### This code restores and builds a FlexTree object ###\n"
        t2 = "from FlexTree.VisionInterface.utils import RestoreTree\n"
        t3 = "RT = RestoreTree('"+xml+"')\n"
        t4 = "#######################################################\n"
        lines.append(indent+t1)
        lines.append(indent+t2)
        lines.append(indent+t3)
        lines.append(indent+t4)
        txt = NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent, ignoreOriginal)
        lines.extend(txt)
        nodeName = self.getUniqueNodeName()
        lines.append(indent+"RT.assignFlexTreeNode("+nodeName+")\n")
        return lines

##      def beforeRemovingFromNetwork(self):
##          """delete corresponding entry in category"""
##          lib = self.library
##          lib.deleteNodeFromCategoryFrame("FlexTrees", self.ftNode.tree().name)
##          lib.resizeCategories()
##          NetworkNode.beforeRemovingFromNetwork(self)



class BuildFTNode(FlexTreeNode):
    """provide the vision-interface to build a FT node on canvas"""
    def __init__(self, ftNode=None, name='FlexTree Node', **kw):
        kw['name'] = name
        apply(FlexTreeNode.__init__, (self,), kw )
        self.ftNode = FTNode()
        
        self.widgetDescr['name'] = {
            'class':'NEEntry', 'master':'node',
            'initialValue':'Flex Tree Node',
            'labelCfg':{'text':'Name'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr

        inputPort = self.getPortbyName('molFrag')
        if inputPort != -1:
            ip[inputPort]['required'] = True

        self.widgetDescr['motion'] = {
            'class':'NEComboBox', 'master':'node',
            'choices':['FTMotion_Hinge',
                       'Unbind',
                       'Generic' ],
            'fixedChoices':True,
            'initialValue':'FTMotion_Hinge',
            'entryfield_entry_width':25,
            'labelGridCfg':{'sticky':'w'},
            'widgetGridCfg':{'sticky':'w', 'columnspan':2},
            'labelCfg':{'text':'Motion'},
            #'selectioncommand':self.rename,
            }

        inputPort = self.getPortbyName('motion')
        if inputPort != -1:
            ip[inputPort] ={'name':'motion',\
                                      'datatype':'string', 'required':False}
               

        # Build the tree 
        inputPort = self.getPortbyName('FlexTreeNode')
        if inputPort != -1:
            codeAfterConnect="""def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    currentNode = self.node.ftNode
    parentNode= conn.port1.node.ftNode
    parentNode.addChildren( [self.node.ftNode] )
    #currentNode.tree = weakref.ref(parentNode._tree)
    currentNode.tree = parentNode.tree
    currentNode.tree().createUniqNumber(currentNode)
    return 
"""
            ip[inputPort]['afterConnect']= codeAfterConnect

        ip.append(datatype='string', required=False, name='name')
        ip.append(datatype='TreeNodeSet', required=False, name='molFrag')

        # set the selectionString for ftNode
        ftInputPort = self.getPortbyName('molFrag')
        if ftInputPort != -1:
            codeAfterConnect="""def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    currentNode = self.node.ftNode
    molFrag = conn.port1.data
    currentNode.selectionString = molFrag.full_name()
    return 
"""
            ip[ftInputPort]['afterConnect']= codeAfterConnect

           

        code ="""def doit(self,FlexTreeNode, shape, motion,
        convolution, combiner, refNode, 
        updateConf, updateShape, name, molFrag):
        
    ftNode=self.ftNode
    
    if updateConf is None:
        updateConf=True
    if updateShape is None:
        updateShape=False
    
    # fixme: add name to ftNode.configure
    if name is not None:
        ftNode.name=name
        self.rename(name)

    conv=self.getConvolution(convolution)
    comb=self.getCombiner(combiner)
    m = self.getMotion(motion)
    if isinstance(motion, FTMotion):
        m=motion
    elif m == 'Unbind':
        m=ftNode.motion
        self.unbindMotion()
    else:
        m=None

    if shape is not ftNode.shape:
        newShape=True
    else:
        newShape=False

    ftNode.configure(autoUpdateConf=updateConf, autoUpdateShape=updateShape,\
                     motion=m,convolution=conv, \
                     shapeCombiner=comb, refNode=refNode, shape=shape,
                     molFrag=molFrag)

    if shape is not None:
        if shape is not ftNode.shape:
            ftNode.configure(shape=shape)
            geoms = ftNode.shape.getGeoms()
            if len(geoms)==1:
                geoms[0].name = self.name
            if len(geoms):
                self.outputData(geoms=geoms)
        else:
            self.outputData(geoms=ftNode.shape.getGeoms())  
    elif ftNode.shape is not None:
        geoms = ftNode.shape.getGeoms()
        if len(geoms)==1:
            geoms[0].name = self.name
        if len(geoms):
            self.outputData(geoms=geoms)           

    self.outputData(OutFTNode=self.ftNode)
"""
        if code: self.setFunction(code)




    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):
        lines = []
        txt = NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent)
        lines.extend(txt)
        nodeName = self.getUniqueNodeName()
#        lines.append(indent+"RT.assignFlexTreeNode("+nodeName+")\n")
        return lines

    def beforeAddingToNetwork(self, net):
        FlexTreeNode.beforeAddingToNetwork(self, net)
        try:
            from MolKit.VisionInterface.MolKitNodes import molkitlib
            net.editor.addLibraryInstance(molkitlib,
                                          'MolKit.VisionInterface.MolKitNodes',
                                          'molkitlib')
        except:
            warn('Warning! Could not import molkitlib from MolKit/Vision')



class BuildFTRoot(BuildFTNode):
    """provide the vision-interface to build a FT root node on canvas"""
    def __init__(self, ftNode=None, name='Root Node', **kw):
        kw['name'] = name
        apply(BuildFTNode.__init__, (self,), kw )
        self.widgetDescr['name'] = {
            'class':'NEEntry', 'master':'node',
            'initialValue': 'Root Node',
            'labelCfg':{'text':'Name'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        del ip[0] # root node does not need a FlexTree input port
        del ip[4] # root node does not need a refNode input port

        ftInputPort = self.getPortbyName('molFrag')
        if ftInputPort != -1:
            codeAfterConnect="""def afterConnect(self, conn):
    # self refers to the port
    # conn is the connection that has been created
    currentFTNode=self.node.ftNode
    tree = currentFTNode.tree()
    molFrag = conn.port1.data
    tree.pdbfilename = molFrag.top.uniq().parser[0].filename
    currentFTNode.selectionString = molFrag.full_name()
    tree.pdbfilename=molFrag[0].top.parser.filename 
    return 
"""
            ip[ftInputPort]['afterConnect']= codeAfterConnect
            
        self.tree = FlexTree(name=name)
        tree = self.tree
        self.ftNode = FTNode()
        ftNode = self.ftNode
        tree.root = ftNode
        ftNode._tree = tree
        ftNode.tree = weakref.ref(ftNode._tree)
        ftNode.selectionString=''
        tree.createUniqNumber(ftNode)
        op = self.outputPortsDescr
        op.append(datatype='FlexTree', name='FlexTree')

        # add tree information for XML
        tree.pdbfilename=''
        tree.xmlfilename=''        
        tree.name='no name'


        code = """def doit(self, shape, motion,
        convolution, combiner,# refNode, 
        updateConf, updateShape, name, molFrag):        
    ftNode = self.ftNode
    if updateConf is None:
        updateConf=True
    if updateShape is None:
        updateShape=False
    if name is not None:
        ftNode.name=name
        self.rename(name)

    conv=self.getConvolution(convolution)
    comb=self.getCombiner(combiner)
    if isinstance(motion, FTMotion):
        m=motion
    else:
        m = self.getMotion(motion)    
        if m == 'Unbind':
            m=ftNode.motion
            self.unbindMotion()    

    ftNode.configure(autoUpdateConf=updateConf, autoUpdateShape=updateShape,\
                     motion=m,convolution=conv, \
                     shapeCombiner=comb, #refNode=refNode,
                     shape=shape,\
                     molFrag=molFrag)
                     
    if shape is not None:
        if shape is not ftNode.shape:
            ftNode.configure(shape=shape)
            geoms = ftNode.shape.getGeoms()
            if len(geoms)==1:
                geoms[0].name = self.name
            if len(geoms):
                self.outputData(geoms=geoms)
    elif ftNode.shape is not None:
        geoms = ftNode.shape.getGeoms()
        if len(geoms)==1:
            geoms[0].name = self.name
        if len(geoms):
            self.outputData(geoms=geoms)           

    self.outputData(OutFTNode=self.ftNode,FlexTree=self.ftNode.tree() )
"""
        if code: self.setFunction(code)

    def getNodeDefinitionSourceCode(self, networkName, indent="",
                                    ignoreOriginal=False):        
        lines = []
        #xml = self.ftNode.tree().xmlfilename
#        xml = 'xxxx'
#        t1 = "### This code restores and builds a FlexTree object ###\n"
#        t2 = "from FlexTree.VisionInterface.utils import RestoreTree\n"
#        t3 = "RT = RestoreTree('"+xml+"')\n"
        t4 = "#######################################################\n"
#        lines.append(indent+t1)
#        lines.append(indent+t2)
#        lines.append(indent+t3)
        lines.append(indent+t4)
        txt = NetworkNode.getNodeDefinitionSourceCode(
            self, networkName, indent)
        lines.extend(txt)
        lines
        #nodeName = self.getUniqueNodeName()
#        lines.append(indent+"RT.assignFlexTreeNode("+nodeName+")\n")
        return lines

   
        

class FTMotionBase(NetworkNode):

    def __init__(self, name='Undefined Motion', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.motion = None
        # since the motion is usually defined by two atoms in space,
        # axis is defined by two points.. from point1 to point2
        # instead of point + vector
        # 2004-12-9
        self.widgetDescr['point1'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Point1'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[1.0, 0., 0.]
            }
        
        self.widgetDescr['point2'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Point2'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0., 0., 0.]
            }

        ip = self.inputPortsDescr
        ip.append(datatype='dict', required=False, name='point1')
        ip.append(datatype='list', required=False, name='point2')

        self.outputPortsDescr.append(datatype='FTMotion', name='motion')

	code = """def doit(self, point1, point2):
    axis = self.buildAxis(vector, point)
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'axis':axis})
    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


    def buildAxis(self, point1, point2):
        vector = [0,0,0.]
        vector[0] = point2[0] - point1[0]
        vector[1] = point2[1] - point1[1]
        vector[2] = point2[2] - point1[2]        
        return {'vector':vector, 'point':point1}


#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        self.schedule_cb()

    def getPortbyName(self, name):
        """return index of the port with name ='name' """
        ip = self.inputPortsDescr
        for i in range(len(ip)):
            if ip[i]['name'] == name: return i
        return -1



class FTMotionRotation(FTMotionBase):
    """FlexTree Rotation About Axis motion object

Defines a rotation about an arbitrary axis.
The axis can either be specified using the point and a vector or by providing
two points."""

    def __init__(self, name='Axis Rotation', **kw):
        kw['name'] = name
        apply( FTMotionBase.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_RotationAboutAxis
        self.motion = FTMotion_RotationAboutAxis()

        self.widgetDescr['angle'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10.0, 'type':'float',
            'initialValue':0.0,
            'labelCfg':{'text':'angle'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='angle')

	code = """def doit(self, vector, point, angle):
    axis = self.buildAxis(vector, point)
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'axis':axis,
        'angle':angle})
    else:
        self.motion.configure(axis = axis, angle=angle)

    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


class FTMotionHinge(FTMotionRotation):
    """FlexTree Hinge motion object

Defines a hinge rotation about an arbitrary axis.
The axis can either be specified using the point and a vector or by providing
two points. The motion is limited to the min and max angles."""

    def __init__(self, name='Hinge', **kw):
        kw['name'] = name
        apply( FTMotionRotation.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_Hinge
        self.motion = FTMotion_Hinge()

        self.widgetDescr['min_angle'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':360, 'type':'float',
            'initialValue':0.0,
            'labelCfg':{'text':'min_angle'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        self.widgetDescr['max_angle'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':360, 'type':'float',
            'initialValue':360.0,
            'labelCfg':{'text':'max_angle'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='min_angle')
        ip.append(datatype='float', required=False, name='max_angle')

	code = """def doit(self, vector, point, angle, min_angle, max_angle):
    axis = self.buildAxis(vector, point)
    if min_angle is not None:
        # set minimum for angle dial
        w=self.getInputPortByName('angle').widget
        if w: w.configure(min=min_angle)
        # also set minimum for max_angle dial
        w=self.getInputPortByName('max_angle').widget
        if w: w.configure(min=min_angle)
        
    if max_angle is not None:
        # set maximum for angle dial
        w=self.getInputPortByName('angle').widget
        if w: w.configure(max=max_angle)
        # set also maximum for min_angle dial
        w=self.getInputPortByName('min_angle').widget
        if w: w.configure(max=max_angle)
        
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'axis':axis,
        'angle':angle, 'min_angle':min_angle, 'max_angle':max_angle})
    else:
        self.motion.configure(axis = axis, angle=angle, min_angle=min_angle,
                              max_angle=max_angle)
    
    self.outputData(motion=self.motion)
"""
        self.setFunction(code)


class FTMotionTranslation(FTMotionBase):
    """FlexTree Translation motion object
    
The parameters are an axis which is specified by a point and a vector, and
a translation"""

    def __init__(self, name='Translation', **kw):
        kw['name'] = name
        apply( FTMotionBase.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_Translation
        self.motion = FTMotion_Translation()

        
        self.widgetDescr['translation'] = {
            'class':'NEThumbWheel', 'master':'ParamPanel', 'width':80,
            'height':21, 'wheelPad':2, 'oneTurn':360, 'type':'float',
            'initialValue':0.0,
            'labelCfg':{'text':'translation'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='translation')

	code = """def doit(self, vector, point, translation):
    axis = self.buildAxis(vector, point)
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'axis':axis,
        'magnitude':translation})
    else:
        self.motion.configure(axis = axis, magnitude=translation)
        
     
    self.outputData(motion=self.motion)
"""
        self.setFunction(code)
        

class FTMotionGeneric4x4(NetworkNode):
    """FlexTree Generic Transformation motion object

The parameters are a list of transformation matrix, a list of position and a
percentage parameter 'percent'
for example, transformList has T1, T2 and T3, positionList is[0.25,0.75]
if percent = 0.25, T1 will be applied.
if percent = 0.75, T1 applied then T2 will be applied.
if percent = 1.0, T1 is applied then T2 is applied, at last, T3 will be applied
if percent = 0.50, T1 applied then 50% of the rotaton and translation in T2                        will be applied. ( 0.5 is in the middle of 0.25 and 0.75)

The node outputs the 4x4 transformation matrix
"""

    def __init__(self, name='Generic4x4', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_Generic
        self.motion = FTMotion_Generic(); 

        self.widgetDescr['percent'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':1.0, 'type':'float',
            'lockOneTurn':True,'lockMin':True,'lockMax':True,
            'min':0.0, 'max':1.0,
            'initialValue':0.0,
            'labelCfg':{'text':'percent'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr #instanceMatrices
        ip.append(datatype='list', name='matrixList')
        ip.append(datatype='list', name='indexList')
        ip.append(datatype='float', name='percent')
       
        self.outputPortsDescr.append(datatype='FTMotion', name='motion')
        
	code = """def doit(self,matrixList, indexList, percent):
    #axis = self.buildAxis(vector, point)
    if self.motion.node is not None:
        if type(matrixList) is types.ListType:
            matrixList = Numeric.array(matrixList, 'f')
        if type(indexList) is types.ListType:
            indexList = Numeric.array(indexList, 'f')        
        self.motion.node().configure(motionParams={'matrixList':matrixList,
        'indexList':indexList, 'percent':percent}, autoUpdateConf=True, autoUpdateShape=True)
    else:
        self.motion.configure(matrixList=matrixList, indexList=indexList,\
                              percent=percent)
    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)



class FTMotionPointRotationDiscrete(NetworkNode):
    """FlexTree motion object, rotate around a point
with discrete rotaton matrix read from 3x3 matrices list file
"""

    def __init__(self,name='Rotation about a point', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_DiscreteRotAboutPoint
        self.motion = FTMotion_DiscreteRotAboutPoint(); 

        self.widgetDescr['index'] = {
            'class':'NEThumbWheel', 'master':'node', 'width':80,
            'height':21, 'wheelPad':2, 'oneTurn':360, 'type':'int',
            'initialValue':0.0,
            'labelCfg':{'text':'index'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        self.widgetDescr['point'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Rotation about this point'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0.0, 0.0, 0.0]
            }

        ip = self.inputPortsDescr #instanceMatrices
        ip.append(datatype='int', required=False, name='index')
        ip.append(datatype='list', required=False, name='point')
       
        self.outputPortsDescr.append(datatype='FTMotion', name='motion')
        
	code = """def doit(self, index, point):
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'point':point,
        'index':index}, autoUpdateConf=True, autoUpdateShape=True)
    else:
        self.motion.configure(index=index, point=point)
    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        self.schedule_cb()

        

class FTMotionPointRotation(NetworkNode):
    """FlexTree motion object, rotate around a point
"""

    def __init__(self,name='Rotation about a point', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_RotationAboutPoint
        self.motion = FTMotion_RotationAboutPoint(); 

        self.widgetDescr['point'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Rotation about this point'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0.0, 0.0, 0.0],
            }
        
        self.widgetDescr['vector'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Rotation Vector'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[1.0, 0.0, 0.0], 
            }
        
        self.widgetDescr['angle'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':360.0, 'type':'float', 'initialValue':0.0,
            'labelCfg':{'text':'angle'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr #instanceMatrices
        ip.append(datatype='list', required=False, name='point')
        ip.append(datatype='list', required=False, name='vector')
        ip.append(datatype='float', required=False, name='angle')
       
        self.outputPortsDescr.append(datatype='FTMotion', name='motion')
        
	code = """def doit(self, point, vector, angle):
    
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'point':point,
        'vector':vector, 'angle':angle})
    else:
        self.motion.configure(angle=angle, vector=vector, point=point)
    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        self.schedule_cb()


class FTMotionConeRotation(NetworkNode):
    """FlexTree motion object, rotate around a point
"""

    def __init__(self,name='Rotation within a cone', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_ConeRotation
        self.motion = FTMotion_ConeRotation(); 
 
        self.widgetDescr['point'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Rotation about this point'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0.0, 0.0, 0.0],
            }        
        self.widgetDescr['vector'] = {
            'class':'NEVectEntry', 'master':'node', 'width':12,
            'labelCfg':{'text':'Rotation Unit Vector'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[1.0, 0.0, 0.0], 
            }        
        self.widgetDescr['alpha'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10.0, 'type':'float', 'initialValue':0.0,
            'labelCfg':{'text':'alpha'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        self.widgetDescr['beta'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10.0, 'type':'float', 'initialValue':0.0,
            'labelCfg':{'text':'beta'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        self.widgetDescr['delta'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10.0, 'type':'float', 'initialValue':0.0,
            'labelCfg':{'text':'delta'},
            'widgetGridCfg':{'labelSide':'top'},
            } 
        self.widgetDescr['maxDelta'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10.0, 'type':'float', 'initialValue':10.0,
            'labelCfg':{'text':'maxDelta'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        self.widgetDescr['maxAlpha'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10.0, 'type':'float', 'initialValue':90.0,
            'labelCfg':{'text':'maxAlpha'},
            'widgetGridCfg':{'labelSide':'top'},
            }
 

        ip = self.inputPortsDescr #instanceMatrices
        ip.append(datatype='list', required=False, name='point')
        ip.append(datatype='list', required=False, name='vector')
        ip.append(datatype='float', required=False, name='maxAlpha')
        ip.append(datatype='float', required=False, name='alpha')
        ip.append(datatype='float', required=False, name='beta')
        ip.append(datatype='float', required=False, name='maxDelta')
        ip.append(datatype='float', required=False, name='delta')
       
        self.outputPortsDescr.append(datatype='FTMotion', name='motion')
        
	code = """def doit(self, point, vector, maxAlpha, alpha, beta, maxDelta,
delta):
    
    if self.motion.node is not None:
        self.motion.node().configure(motionParams={'point':point,
        'vector':vector, 'alpha':alpha, 'beta':beta, 'delta':delta,\
        #'maxDelta':maxDelta, 'maxAlpha':maxAlpha
        })
    else:
        self.motion.configure(vector=vector, point=point,alpha=alpha, beta=beta, delta=delta, maxAlpha=maxAlpha, maxDelta=maxDelta)
        
    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        self.schedule_cb()



class FTMotionCombiner(NetworkNode):
    """FlexTree motion object, combination of a rotation object and a
translation object.
The node outputs the 4x4 transformation matrix
"""
    
    def __init__(self, name='Combined Motion', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotionCombiner 
        self.motion = FTMotionCombiner(); 

        ip = self.inputPortsDescr #instanceMatrices
        ip.append(datatype='FTMotion', name='motion1')
        ip.append(datatype='FTMotion', name='motion2')
       
        self.outputPortsDescr.append(datatype='FTMotion', name='motion')
        
	code = """def doit(self,motion1, motion2):
    motionList=[motion1, motion2]
    dictList=[]
##     print id(motion1), id(motion2)
##     for i in range(len(motionList)):
##         dictList.append(motionList[i].getDescr())
##     if self.motion.node is not None:
##         self.motion.node().configure(
##         motionParams={'motionParamDictList':dictList},
##         autoUpdateConf=True, autoUpdateShape=True)
##     else:
##         self.motion.configure(motionParamDictList =dictList)

    if self.motion.node is not None:
        self.motion.node().configure(
            motionParams={'motionList':motionList},
            autoUpdateConf=True, autoUpdateShape=True)
    else:
        self.motion.configure(motionList =motionList)


    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


class FTMotionBoxTranslation(NetworkNode):
    """FlexTree motion object
"""
    
    def __init__(self, name='Combined Motion', **kw):
        kw['name'] = name
        apply(NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_BoxTranslation 
        self.motion = FTMotion_BoxTranslation(); 

        self.widgetDescr['gridCenter'] = {
            'class':'NEVectEntry', 'master':'ParamPanel', 'width':12,
            'labelCfg':{'text':'Center of Box'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0.0, 0.0, 0.0],
            }
        
        self.widgetDescr['boxDim'] = {
            'class':'NEVectEntry', 'master':'ParamPanel', 'width':12,
            'labelCfg':{'text':'Dimension of Box'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0.0, 0.0, 0.0],
            }

        self.widgetDescr['point'] = {
            'class':'NEVectEntry', 'master':'ParamPanel', 'width':12,
            'labelCfg':{'text':'point in the box'},
            'widgetGridCfg':{'labelSide':'top'},
            'initialValue':[0.0, 0.0, 0.0],
            }

        ip = self.inputPortsDescr #instanceMatrices
        ip.append(datatype='list', required=True, name='gridCenter')
        ip.append(datatype='list', required=True, name='boxDim')
        ip.append(datatype='list', required=True, name='point')
       
        self.outputPortsDescr.append(datatype='FTMotion', name='motion')
        
	code = """def doit(self, gridCenter, boxDim, point):
    if self.motion.node is not None:
        self.motion.node().configure(
                 motionParams={'gridCenter':gridCenter, 'boxDim':boxDim,
                 'point':point}, autoUpdateConf=True, autoUpdateShape=True)
    else:
        self.motion.configure(gridCenter=gridCenter, boxDim=boxDim,point=point)
    self.outputData(motion=self.motion)
"""
        if code: self.setFunction(code)


class FTShapeBase(NetworkNode):
    """Base node which most shape nodes will inherit from."""

    def __init__(self, name='Undefined Shape', **kw):

        # shape.node gets assigned in configure of FlexTree.FT.FTNode
        
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        self.shape = None

        # this code will added to port.callbacks.
        # disconnecting a shape node will delete the object in the FlexTree
        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    childNode = c.port2.node

    from FlexTreeTypes import FlexTreeShapeType

    if not isinstance(c.port2.datatypeObject, FlexTreeShapeType):
        # if we connect to any other port by accident, we want to be
        # able to disconnect here
        return

    from DejaVu.Geom import Geom
    geoms = c.port2.node.ftNode.shape.getGeoms()
    if len(geoms) and c.port2.node.ftNode.shape.ownsGeom:
        # geoms can be packed in a list or not
        if type(geoms) == types.ListType:
            for g in geoms:
                if isinstance(g, Geom):
                    if hasattr(g, 'viewer') and g.viewer is not None:
                        g.viewer.RemoveObject(g)
        else: # not list
            g=geoms
            if isinstance(g, Geom):
                if hasattr(g, 'viewer') and g.viewer is not None:
                    g.viewer.RemoveObject(g)

    # and delete shape object in FTNode
    c.port2.node.ftNode.configure(shape=None, shapeParams=None)
"""


        self.outputPortsDescr.append(name='shape', datatype='FTShape',
                                     beforeDisconnect=codeBeforeDisconnect)

	code = """def doit(self):
    if self.shape.node is not None:
        self.shape.node().configure(shapeParams=None)
             
    self.outputData(shape=self.shape)
"""
        if code: self.setFunction(code)


#    def afterAddingToNetwork(self):
#        NetworkNode.afterAddingToNetwork(self)
#        self.schedule_cb()



class FTShapeGeom(FTShapeBase):
    """FlexTree DejaVu Geom shape object"""
    
    def __init__(self, name='FTGeom', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        ip = self.inputPortsDescr
        ip.append(datatype='geom', name='geom')
        
        from FlexTree.FTShapes import FTGeom
        self.shape = FTGeom()

	code = """def doit(self, geom):
    self.shape.geoms = [geom]
    self.outputData(shape=self.shape)
"""
        if code: self.setFunction(code)


class FTShapeSphere(FTShapeBase):
    """FlexTree Gyration Sphere shape object"""
    
    def __init__(self, name='Sphere', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        from FlexTree.FTShapes import FTSphere
        self.shape = FTSphere()


class FTShapeEllipsoid(FTShapeBase):
    """FlexTree Ellipsoid shape object"""

    def __init__(self, name='Ellipsoid', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        from FlexTree.FTShapes import FTEllipsoid
        self.shape = FTEllipsoid()


class FTShapeConvexHull(FTShapeBase):
    """FlexTree Convex Hull shape object"""

    def __init__(self, name='ConvexHull', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        from FlexTree.FTShapes import FTConvexHull
        self.shape = FTConvexHull()


class FTShapeLines(FTShapeBase):
    """FlexTree Lines shape object"""

    def __init__(self, name='Lines', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        from FlexTree.FTShapes import FTLines
        self.shape = FTLines()

        self.widgetDescr['cutoff'] = {
            'class':'NEDial', 'master':'ParamPanel', 'size':50,
            'oneTurn':1, 'type':'float',
            'initialValue':1.85,
            'labelCfg':{'text':'cutoff'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='cutoff')

	code = """def doit(self, cutoff):
    if cutoff is not None:
        if self.shape.node is not None:
            self.shape.node().configure(shapeParams={'cutoff':cutoff})
        
    self.outputData(shape=self.shape)
"""
        if code: self.setFunction(code)


class FTShapeCPK(FTShapeBase):
    """FlexTree CPK shape object"""

    def __init__(self, name='CPK', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        from FlexTree.FTShapes import FTCPK
        self.shape = FTCPK()

        self.widgetDescr['quality'] = {
            'class':'NEDial', 'master':'ParamPanel', 'size':50,
            'oneTurn':4, 'type':'int',
            'initialValue':10,
            'min':3,
            'labelCfg':{'text':'quality'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        self.widgetDescr['united'] = {
            'class':'NECheckButton', 'master':'ParamPanel',
            'type':'boolean',
            'initialValue':False,
            'labelCfg':{'text':'united'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        
        ip = self.inputPortsDescr
        ip.append(datatype='int', required=False, name='quality', defaultValue=10)
        ip.append(datatype='boolean', required=False, name='united', defaultValue=False)

	code = """def doit(self, quality, united):
    if quality is not None or united is not None:
        if self.shape.node is not None:
            self.shape.node().configure(shapeParams={'quality':quality,
            'united':united})
        
    self.outputData(shape=self.shape)
"""
        if code: self.setFunction(code)

        

class FTShapeMSMS(FTShapeBase):
    """FlexTree Lines shape object"""

    def __init__(self, name='MSMS', **kw):
        kw['name'] = name
        apply( FTShapeBase.__init__, (self,), kw )
        from FlexTree.FTShapes import FTMsms
        self.shape = FTMsms()

        self.widgetDescr['pRadius'] = {
            'class':'NEDial', 'master':'ParamPanel', 'size':50,
            'oneTurn':1, 'type':'float',
            'initialValue':1.5,
            'labelCfg':{'text':'Radius'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        self.widgetDescr['density'] = {
            'class':'NEDial', 'master':'ParamPanel', 'size':50,
            'oneTurn':1, 'type':'float',
            'initialValue':1.0,
            'labelCfg':{'text':'Density'},
            'widgetGridCfg':{'labelSide':'top'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='float', required=False, name='pRadius')
        ip.append(datatype='float', required=False, name='density')

	code = """def doit(self, pRadius, density):
    if pRadius is not None:
        if self.shape.node is not None:
            self.shape.node().configure(shapeParams={'pRadius':pRadius})
    if density is not None:
        if self.shape.node is not None:
            self.shape.node().configure(shapeParams={'density':density})
        
    self.outputData(shape=self.shape)
"""
        if code: self.setFunction(code)



class RigidBodyFit(NetworkNode):
    """input the two AtomSet instances and use the rigidBodyFit to output the
4x4 transformation matrix """
    
    def __init__(self, name='RigidBodyFit', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='AtomSet', required=True, name='RefAtomSet')
        ip.append(datatype='AtomSet', required=True, name='MobileAtomSet')
        self.outputPortsDescr.append(name='transform', datatype='NumericArray')
      
        code = """def doit(self, RefAtomSet, MobileAtomSet, united):
    if RefAtomSet is not None and MobileAtomSet is not None and len(MobileAtomSet)==len(RefAtomSet):
        RefAtomSet.sort()
        MobileAtomSet.sort()
        from mglutil.math.rigidFit import RigidfitBodyAligner
        aligner = RigidfitBodyAligner(refCoords = RefAtomSet.coords )
        aligner.rigidFit(mobileCoords =MobileAtomSet.coords)
        #import numpy.oldnumeric as Numeric
        rotMat =  Numeric.identity(4).astype('d')
        rotMat[:3,:3] = aligner.rotationMatrix               
        transMat = Numeric.array(aligner.translationMatrix)
        rotMat[3,:3] = transMat     
        print aligner.rmsdAfterSuperimposition(setCoords = MobileAtomSet.coords)
    self.outputData(transform=rotMat)
"""
        if code: self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        try:
            from MolKit.VisionInterface.MolKitNodes import molkitlib
            net.editor.addLibraryInstance(
                molkitlib, 'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
        except:
            warn("Warning! Could not import molkitlib from "+\
                  "MolKit.VisionInterface.MolKitNodesr")


class RandomMotion(NetworkNode):
    """Trigges a FlexTree object to assume random conformation, then outputs
the updated coordinates.

Input: FlexTree: a FlexTree Object
       next: a signal to run again (any data will do)
       repeat : times to repeat (the last conformation as output)

Output: coords: FlexTree 3-D coordinates of its current conformation"""

    def __init__(self, name='Random Motion', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='FlexTree', name='FlexTree')
        ip.append(datatype='None', required=False, name='next')

        self.outputPortsDescr.append(datatype='coordinates3D', name='coords')
                 
	code = """def doit(self, FlexTree, next):
    if FlexTree:
        FlexTree.adoptRandomConformation()
        root = FlexTree.root
        #root.updateShape()  # fixeme: obsolete function
        root.updateCurrentConformation()
        root.updateConvolution()
        newCoords = root.getCurrentSortedConformation2()
        self.outputData(coords=newCoords)
"""
        if code: self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        try:
            from DejaVu.VisionInterface.DejaVuNodes import vizlib
            net.editor.addLibraryInstance(
                vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
        except:
            warn('Warning! Could not import vizlib from DejaVu/VisionInterface')


class PDBQ2XML(NetworkNode):
    """Read a pdbq file (ligand) and convert the torTree information into XML
file..
Input: PDBQ file 
Output: XML file """

    def __init__(self, name='pdbq to XML', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        fileTypes=[('xml', '*.xml'), ('all', '*')]        
        self.widgetDescr['xmlFilename'] = {
            'class':'NEEntryWithFileSaver', 'master':'node',
            'filetypes':fileTypes, 'title':'save file', 'width':16,
            'labelCfg':{'text':'file:'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='MoleculeSet', name='MolSets')
        ip.append(datatype='string', name='xmlFilename')
      
	code = """def doit(self, mol, xmlFilename):
    from MolKit.protein import ProteinSet, Protein
    if isinstance(mol, ProteinSet):
        mol=mol[0]
    if mol and xmlFilename:
        if mol.torTree is None:
            print "Not torTree info found"
        else:
            s=mol.torTree.printXmlTree(mol.allAtoms, 1000)
            file=open(xmlFilename,'w')
            file.write(s)
            file.close()
        
"""
        if code: self.setFunction(code)


    def beforeAddingToNetwork(self, net):
        try:
            from DejaVu.VisionInterface.DejaVuNodes import vizlib
            net.editor.addLibraryInstance(
                vizlib, 'DejaVu.VisionInterface.DejaVuNodes', 'vizlib')
        except:
            warn('Warning! Could not import vizlib from DejaVu/VisionInterface')

#################
class FlexLinker(NetworkNode):
    """Read a ResidueSet, assuming all psi, phi angle are freely rotatable,
convert the linker information into XML

Input: ResidueSet
Output: XML file """

    def __init__(self, name='pdbq to XML', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        fileTypes=[('xml', '*.xml'), ('all', '*')]        
        self.widgetDescr['xmlFilename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'save file', 'width':16,
            'labelCfg':{'text':'file:'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='ResidueSet', name='residueSet')
        ip.append(datatype='string', name='xmlFilename')
      
	code = """def doit(self, residueSet, xmlFilename):
    if not self.validLinker(residueSet):
        print "Not a valid linker"
        return

            else:
            s=mol.torTree.printXmlTree(mol.allAtoms, 0)
            file=open(xmlFilename,'w')
            file.write(s)
            file.close()
        
"""
        if code: self.setFunction(code)




    def beforeAddingToNetwork(self, net):
        try:
            from MolKit.VisionInterface.MolKitNodes import molkitlib
            net.editor.addLibraryInstance(molkitlib,
                    'MolKit.VisionInterface.MolKitNodes', 'molkitlib')
        except:
            warn('Warning! Could not import molkitlib from MolKit/Vision')




class FlexibleResidue(NetworkNode):
    """ add rotamer to the flexible sidechain of a residue"""

    def createPortsForPositionalArgs(self, args):
        # add ports for positional arguments
        self.posArgNames = []
        self.posArgNamesDict = {} # used for fast lookup

        for arg in args:
            ipdescr = {'name':arg}
            ip = apply( self.addInputPort, (), ipdescr )


    def buildPortsForNameList(self, nameList):
        """add ports (dial) for each hinge angle"""
        for name in nameList:
            self.widgetDescr[name] = {
                'master':'node',  #'master':'ParamPanel',
                'class': 'NEDial', 'size':50,
                'showLabel':1, 'oneTurn':360., 'type':'float',
                'min':0.0, 'max':360,
                'initialValue':0,
                'labelGridCfg':{'sticky':'w'},
                'labelCfg':{'text':name},
                }
                
            ipdescr = {'name':name, 'required':False, 'datatype': 'float',
                       'balloon':'Defaults to'+str(name),
                       'singleConnection':True}
            # create port
            ip = apply( self.addInputPort, (), ipdescr )
            # create widget if necessary
            ip.createWidget(descr=self.widgetDescr[name])

        return 


##     def _chooseRotamerClass(self, resName):
##         """ private function, import different FTRotamer class accordingly."""
##         name =  'FT_'+resName[:3]
##         ftR =__import__('FlexTree.FTRotamers', globals(), locals(),[name])
##         self.ftRotamer=getattr(ftR, name)

        
    
    def __init__(self, residue=None, posArgsNames=[], namedArgs={},
                 sortedArgNames=[], name='Add rotamer to sideChain', **kw):
        kw['name'] = name

        apply( NetworkNode.__init__, (self,), kw )

        self.residue = residue  
        self.geomContainer = None
        self.hingeNames = []


        # fixme: do we need this? copied from PmvRunCommand
        self.posArgsNames = posArgsNames
        self.namedArgs = namedArgs # dict:  key: arg name, value: arg default
        self.sortedArgNames = sortedArgNames
        self.defaultNamedArgs = ['log', 'redraw', 'topCommand', 'setupUndo']
        self.defaultNamedArgsdefaults = [ True, True, True, True]
        
        ip = self.inputPortsDescr
        codeBeforeDisconnect = """def beforeDisconnect(self, c):
    # upon disconnecting we want to set the attribute command to None
    c.port2.node.command = None
"""
            
        ip.append(name='ftnode', required=True, datatype='FlexTreeNode',
                  beforeDisconnect=codeBeforeDisconnect)
        ip.append(name='residues', required=True, datatype='ResidueSet',
                  beforeDisconnect=codeBeforeDisconnect)
        self.ftNodeList=[]
        self.motionList=[]
        self.refNode=None
        self.refMolFrag=None
	code = """def doit(self, ftnode, residues, *args):
    self.refNode=ftnode
    if not hasattr(self.refNode, 'origMolFrag'):
        self.refNode.origMolFrag=self.refNode.molecularFragment[:]
    self.refMolFrag=self.refNode.origMolFrag
    tree=self.refNode.tree()            
    if len(self.ftNodeList)>0:
        cList=tree.root.children
        for ftn in self.ftNodeList:
            index=cList.index(ftn)
            del cList[index]
        self.ftNodeList=[]
        self.motionList=[]
        ## restore molFrag in refNode
        self.refNode.configure(molFrag=self.refMolFrag)

    from MolKit.molecule import Atom, AtomSet

    for res in residues:
        motion=FTMotion_Rotamer()
        resAtoms=res.atoms
        sidechain=resAtoms.get('sidechain')-resAtoms.get('CB')
        anchor=[]
        for name in ['CB','CA','C']:
            anchor.append(res.get(name)[0])
        anchor=AtomSet(anchor)
        motion.configure(residueName=res.name, sideChainAtomNames=sidechain.name, anchorAtoms=anchor)
        self.motionList.append(motion)
        ftn= FTNode(refNode=ftnode, discreteMotion=motion, name=res.name, molFrag=sidechain)
        ftn.anchorAtoms=anchor
        self.ftNodeList.append(ftn)
        tree.root.children.append(ftn)
        tree.createUniqNumber(ftn)
        motion._buildConfList()
        self.refMolFrag=self.refMolFrag.findType(Atom)-sidechain

    self.refNode.configure(molFrag=self.refMolFrag)
    #self.outputData(result=self.tree)
    
"""
        if code: self.setFunction(code)



class DiscreteRotamer(NetworkNode):
    """ use rotamer library to describe a flexible sidechain 
Input: index of conformation in the rotamer library
Note: The rotamer is available only after connected to a FTNode (FTN). And the
      molecularFragment associated with the FTN has to be a Residue object.

"""

    def __init__(self, name='Discrete Rotomer', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_Rotamer
        self.motion = FTMotion_Rotamer()
        
        self.widgetDescr['index'] = {
            'class':'NEDial', 'master':'node', 'size':50,
            'oneTurn':10, 'type':'int',
            'initialValue':0,
            'labelCfg':{'text':'Index'},
            'widgetGridCfg':{'labelSide':'top'},
            }
        
        ip = self.inputPortsDescr
        ip.append(datatype='Residue', name='residue')
        ip.append(datatype='int', required=False, name='index')
        op=self.outputPortsDescr
        op.append(datatype='FTMotion', name='motion')
        op.append(datatype='AtomSet', name='sidechainAtoms')
	code = """def doit(self, residue, index):
    if residue:
        resAtoms=residue.atoms
        sidechain=resAtoms.get('sidechain')-resAtoms.get('CB')
        self.motion.configure(residueName=residue.name, sideChainAtomNames=sidechain.name) 
    if index is not None:
        if self.motion.node is not None:
            self.motion.node().configure(motionParams={'index':index},
            autoUpdateConf=True, autoUpdateShape=True)
        else:
            self.motion.configure(index=index)

    self.outputData(motion=self.motion, sidechainAtoms=sidechain)
"""
        if code: self.setFunction(code)


class ExcludeBackboneCB(NetworkNode):
    """ this node excludes backbone atoms and CBs of input 2 from input 1
"""

    def __init__(self, name='exclude rotamer', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        from FlexTree.FTMotions import FTMotion_Rotamer
        self.motion = FTMotion_Rotamer()
                
        ip = self.inputPortsDescr
        ip.append(datatype='TreeNodeSet', name='source')
        ip.append(datatype='Residue',name='data',singleConnection=False)
        op=self.outputPortsDescr
        op.append(datatype='AtomSet', name='result')
	code = """def doit(self, source, data):
    from MolKit.molecule import Atom, AtomSet
    from MolKit.protein import Residue
    result=source.findType(Atom)
    if isinstance(data,Residue):
        result=result-data.get('sidechain') + data.get('CB')
    else:
        for res in data:
            tmp=res.findType(Atom)
            result=result-tmp.get('sidechain') + tmp.get('CB')
    self.outputData(result=result)
"""
        if code: self.setFunction(code)
        return


         
class UpdateGeomInPMV(NetworkNode):
    """ 
"""
    from ViewerFramework.VF import ModificationEvent 
    def __init__(self, name='Discrete Rotomer', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
       
        ip = self.inputPortsDescr
        ip.append(datatype= 'coordinates3D',required=True, name='FTCoords')
        ip.append(name='pmvAtoms', required=True, datatype='AtomSet')
        self.outputPortsDescr.append(name='trigger')

        
	code = """def doit(self, FTCoords, pmvAtoms):
    in0=FTCoords
    in1=pmvAtoms
    pmvAtoms=in1.allAtoms
    pmvAtoms.sort()
    pmvAtoms.updateCoords(in0, 0)
    modEvent = ModificationEvent('edit', 'coords', pmvAtoms)
    in1[0].geomContainer.updateGeoms(modEvent)
    self.outputData(trigger='trigger')  #to trigger 'one redraw',if necessory.

  
"""
        if code: self.setFunction(code)


  
# define MacroNode here
from NetworkEditor.macros import MacroNode

if foundAutoDockFR:
    class DockingBoxMacro(MacroNode):
        """Display the docking box. Information extracted from a ligand flextree """
        def __init__(self, constrkw={}, name='Docking Box', **kw):
            kw['name'] = name
            apply( MacroNode.__init__, (self,), kw)

        def beforeAddingToNetwork(self, net):
            MacroNode.beforeAddingToNetwork(self, net)
            importVizLib(net)
            # loading library stdlib
            from Vision.StandardNodes import stdlib
            net.editor.addLibraryInstance(stdlib, 'Vision.StandardNodes',
                                          'stdlib')
        def afterAddingToNetwork(self):
            from DejaVu.VisionInterface.DejaVuNodes import vizlib
            from Vision.StandardNodes import stdlib
            MacroNode.afterAddingToNetwork(self)
            Docking_Box_0 = self
            from Vision.StandardNodes import Generic
            from DejaVu.VisionInterface.GeometryNodes import BoxNE
            Box_3 = BoxNE(constrkw = {}, name='Box', library=vizlib)
            Docking_Box_0.macroNetwork.addNode(Box_3,125,217)
            Box_3.inputPortByName['centerx'].unbindWidget()
            Box_3.inputPortByName['centery'].unbindWidget()
            Box_3.inputPortByName['centerz'].unbindWidget()
            Box_3.inputPortByName['lengthx'].unbindWidget()
            Box_3.inputPortByName['lengthy'].unbindWidget()
            Box_3.inputPortByName['lengthz'].unbindWidget()

            Locate_Docking_Box_4 = Generic(constrkw = {}, name='Locate Docking Box', library=stdlib)
            Docking_Box_0.macroNetwork.addNode(Locate_Docking_Box_4,125,116)
            apply(Locate_Docking_Box_4.addInputPort, (), {'datatype': 'FlexTree', 'width': 8, 'name': 'flextree', 'height': 8})
            apply(Locate_Docking_Box_4.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out0', 'height': 8})
            apply(Locate_Docking_Box_4.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out1', 'height': 8})
            apply(Locate_Docking_Box_4.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out2', 'height': 8})
            apply(Locate_Docking_Box_4.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out3', 'height': 8})
            apply(Locate_Docking_Box_4.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out4', 'height': 8})
            apply(Locate_Docking_Box_4.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out5', 'height': 8})
            code = """def doit(self, flextree):
    from AutoDockFR.utils import locateDockingBoxInfo
    out0,out1=locateDockingBoxInfo(flextree)
    self.outputData(out0=out0[0],out1=out0[1],out2=out0[2],\
                    out3=out1[0],out4=out1[1],out5=out1[2])
"""
            Locate_Docking_Box_4.configure(function=code)
            ## saving connections for network Docking Box ##
            Docking_Box_0.macroNetwork.freeze()
            output_Ports_2 = Docking_Box_0.macroNetwork.opNode
            if Box_3 is not None and output_Ports_2 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Box_3, output_Ports_2, "box", "new", blocking=True)
            input_Ports_1 = Docking_Box_0.macroNetwork.ipNode
            if input_Ports_1 is not None and Locate_Docking_Box_4 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    input_Ports_1, Locate_Docking_Box_4, "new", "flextree", blocking=True)
            if Locate_Docking_Box_4 is not None and Box_3 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Locate_Docking_Box_4, Box_3, "out0", "centerx", blocking=True)
            if Locate_Docking_Box_4 is not None and Box_3 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Locate_Docking_Box_4, Box_3, "out1", "centery", blocking=True)
            if Locate_Docking_Box_4 is not None and Box_3 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Locate_Docking_Box_4, Box_3, "out2", "centerz", blocking=True)
            if Locate_Docking_Box_4 is not None and Box_3 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Locate_Docking_Box_4, Box_3, "out3", "lengthx", blocking=True)
            if Locate_Docking_Box_4 is not None and Box_3 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Locate_Docking_Box_4, Box_3, "out4", "lengthy", blocking=True)
            if Locate_Docking_Box_4 is not None and Box_3 is not None:
                Docking_Box_0.macroNetwork.connectNodes(
                    Locate_Docking_Box_4, Box_3, "out5", "lengthz", blocking=True)
            Docking_Box_0.macroNetwork.unfreeze()
            Docking_Box_0.shrink()



class RandomTransform(MacroNode):

    def __init__(self, constrkw={}, name='RandomTransform', **kw):
        kw['name'] = name
        apply( MacroNode.__init__, (self,), kw)

    def beforeAddingToNetwork(self, net):
        MacroNode.beforeAddingToNetwork(self, net)
        ## loading libraries ##
        from symserv.VisionInterface.SymservNodes import symlib
        net.editor.addLibraryInstance(
            symlib,"symserv.VisionInterface.SymservNodes", "symlib")
        from FlexTree.VisionInterface.FlexTreeNodes import flextreelib
        net.editor.addLibraryInstance(
            symlib,"FlexTree.VisionInterface.FlexTreeNodes", "flextreelib")

        importVizLib(net)

        

    def afterAddingToNetwork(self):
        from NetworkEditor.macros import MacroNode
        MacroNode.afterAddingToNetwork(self)
        
        from FlexTree.VisionInterface.FlexTreeNodes import flextreelib
        from Vision.StandardNodes import stdlib
#        node10 = MacroNode(name='AppendInstanceMatrices')
#        masterNet.addNode(node10, 251, 200)
        node10= self
        node11 = node10.macroNetwork.ipNode
        node11.move(87, 27)
        node12 = node10.macroNetwork.opNode
        node12.move(87, 371)
        from FlexTree.VisionInterface.FlexTreeNodes import FTMotionBoxTranslation
        node13 = FTMotionBoxTranslation(constrkw = {}, name='BoxTranslation', library=flextreelib)
        node10.macroNetwork.addNode(node13,258,99)
        apply(node13.inputPorts[0].widget.configure, (), {'widgetGridCfg': {'column': 0, 'row': 2}})
        apply(node13.inputPorts[1].widget.configure, (), {'widgetGridCfg': {'column': 0, 'row': 5}})
        node13.inputPorts[1].widget.set([60.0, 60.0, 60.0],0)
        apply(node13.inputPorts[2].widget.configure, (), {'widgetGridCfg': {'column': 0, 'row': 8}})
        apply(node13.configure, (), {'specialPortsVisible': True})
        from FlexTree.VisionInterface.FlexTreeNodes import FTMotionPointRotation
        node14 = FTMotionPointRotation(constrkw = {}, name='Point Rotation', library=flextreelib)
        node10.macroNetwork.addNode(node14,418,78)
        apply(node14.inputPorts[0].widget.configure, (), {'widgetGridCfg': {'column': 0, 'row': 2}})
        apply(node14.inputPorts[1].widget.configure, (), {'widgetGridCfg': {'column': 0, 'row': 5}})
        apply(node14.inputPorts[2].widget.configure, (), {'widgetGridCfg': {'column': 0, 'row': 8}})
        node14.inputPorts[2].widget.set(6.0090059575,0)
        apply(node14.configure, (), {'specialPortsVisible': True})
        from FlexTree.VisionInterface.FlexTreeNodes import FTMotionCombiner
        node15 = FTMotionCombiner(constrkw = {}, name='Combined Motion', library=flextreelib)
        node10.macroNetwork.addNode(node15,345,181)
        from Vision.StandardNodes import CallMethod
        node16 = CallMethod(constrkw = {}, name='Random Motion', library=stdlib)
        node10.macroNetwork.addNode(node16,345,243)
        apply(node16.inputPorts[0].configure, (), {'datatype': 'FTMotion'})
        apply(node16.inputPorts[1].widget.configure, (), {'widgetGridCfg': {'row': 1}})
        node16.inputPorts[1].widget.set("randomize",0)
        code = """def doit(self, objects, signature):
    if signature and signature != self.oldSignature:
        self.oldSignature = signature
        words = signature.split()
        for word in words:
            if word[0] == '%':
                match = self.allowedFirstChar.match(word[1:])
            else:
                match = self.allowedFirstChar.match(word)
            if not match:
                return

        self.createPortsFromDescr( words )

    results = []

    if self.inputPorts[0].singleConnection:
        if not hasattr(objects, self.method):
            return
        else:
            #self.rename(objects.fullName+' '+self.oldSignature)
            method = eval('objects.'+self.method)
            posArgs = []
            namedArgs = {}
            #print 'POS',self.posArgNames
            for arg in self.posArgNames:
                posArgs.append(eval(arg[0]))
            #print 'NAMED',self.namedArgNames
            for arg in self.namedArgNames:
                namedArgs[arg[1]] = eval(arg[0])
            results = [apply( method, posArgs, namedArgs )]

    elif objects:
        for g in objects:
            #import types
            #if not type(g)==types.InstanceType:
            from mglutil.util.misc import isInstance
            if isInstance(g) is False:
                continue
            if not hasattr(g, self.method):
                continue
            #method = getattr(g, self.method)
            method = eval('g.'+self.method)
            posArgs = []
            namedArgs = {}
            #print 'POS',self.posArgNames
            for arg in self.posArgNames:
                posArgs.append(eval(arg[0]))
            #print 'NAMED',self.namedArgNames
            for arg in self.namedArgNames:
                namedArgs[arg[1]] = eval(arg[0])

            results.append( apply( method, posArgs, namedArgs ) )

    self.outputData(objects=objects, results=results)
"""
        node16.configure(function=code)
        apply(node16.configure, (), {'specialPortsVisible': True})
        from Vision.StandardNodes import CallMethod
        node17 = CallMethod(constrkw = {}, name='GetMatrix', library=stdlib)
        node10.macroNetwork.addNode(node17,197,296)
        apply(node17.inputPorts[1].widget.configure, (), {'widgetGridCfg': {'row': 1}})
        node17.inputPorts[1].widget.set("getMatrix",0)
        code = """def doit(self, objects, signature):
    if signature and signature != self.oldSignature:
        self.oldSignature = signature
        words = signature.split()
        for word in words:
            if word[0] == '%':
                match = self.allowedFirstChar.match(word[1:])
            else:
                match = self.allowedFirstChar.match(word)
            if not match:
                return

        self.createPortsFromDescr( words )

    results = []

    if self.inputPorts[0].singleConnection:
        if not hasattr(objects, self.method):
            return
        else:
            #self.rename(objects.fullName+' '+self.oldSignature)
            method = eval('objects.'+self.method)
            posArgs = []
            namedArgs = {}
            #print 'POS',self.posArgNames
            for arg in self.posArgNames:
                posArgs.append(eval(arg[0]))
            #print 'NAMED',self.namedArgNames
            for arg in self.namedArgNames:
                namedArgs[arg[1]] = eval(arg[0])
            results = [apply( method, posArgs, namedArgs )]

    elif objects:
        for g in objects:
            import types
            if not type(g)==types.InstanceType:
                continue
            if not hasattr(g, self.method):
                continue
            #method = getattr(g, self.method)
            method = eval('g.'+self.method)
            posArgs = []
            namedArgs = {}
            #print 'POS',self.posArgNames
            for arg in self.posArgNames:
                posArgs.append(eval(arg[0]))
            #print 'NAMED',self.namedArgNames
            for arg in self.namedArgNames:
                namedArgs[arg[1]] = eval(arg[0])

            results.append( apply( method, posArgs, namedArgs ) )

    self.outputData(objects=objects, results=results)
"""
        node17.configure(function=code)
        from Vision.StandardNodes import Generic
        node18 = Generic(constrkw = {}, name='AppendMatirx', library=stdlib)
        node10.macroNetwork.addNode(node18,104,243)
        apply(node18.addInputPort, (), {'datatype': 'geom', 'width': 12, 'name': 'in0', 'height': 8})
        apply(node18.addInputPort, (), {'datatype': 'None', 'width': 12, 'name': 'in1', 'height': 8})
        apply(node18.addOutputPort, (), {'datatype': 'None', 'width': 12, 'name': 'out0', 'height': 8})
        code = """def doit(self, in0, in1):
    oldMats = in0.instanceMatricesFortran
    #print oldMats
    N=Numeric
    newMat = N.array(in1[0])
    newMat = newMat.astype('f')
    newMat = N.transpose(newMat)
    newMat = N.reshape(newMat, (16,))

    mats=[]
    for m in oldMats:
        m=N.reshape(m, (4,4))
        mm= N.transpose(m)
        mm = N.reshape(mm, (16,))
        mats.append(mm)
    mats.append(newMat)
    #print len(mats)
    in0.Set(instanceMatrices = mats)
    data = 1
    self.outputData(out0=data)

"""
        node18.configure(function=code)
        from Vision.StandardNodes import Pass
        node19 = Pass(constrkw = {}, name='Pass', library=stdlib)
        node10.macroNetwork.addNode(node19,36,151)
        apply(node19.configure, (), {'specialPortsVisible': True})

        ## saving connections for network AppendInstanceMatrices ##
        if node13 is not None and node15 is not None:
            node10.macroNetwork.connectNodes(
                node13, node15, "motion", "motion1", blocking=True)
        if node14 is not None and node15 is not None:
            node10.macroNetwork.connectNodes(
                node14, node15, "motion", "motion2", blocking=True)
        if node15 is not None and node16 is not None:
            node10.macroNetwork.connectNodes(
                node15, node16, "motion", "objects", blocking=True)
        if node16 is not None and node17 is not None:
            node10.macroNetwork.connectNodes(
                node16, node17, "objects", "objects", blocking=True)
        if node17 is not None and node18 is not None:
            node10.macroNetwork.connectNodes(
                node17, node18, "results", "in1", blocking=True)
        if node11 is not None and node19 is not None:
            node10.macroNetwork.connectNodes(
                node11, node19, "new", "in1", blocking=True)
        if node18 is not None and node12 is not None:
            node10.macroNetwork.connectNodes(
                node18, node12, "out0", "new", blocking=True)
        if node11 is not None and node18 is not None:
            node10.macroNetwork.connectNodes(
                node11, node18, "Pass_in1", "in0", blocking=True)
        node10.shrink()





# end of NetworkNodes / MacroNode definition  #



class LoadEssentialDynamics(NetworkNode):

    """This node load EssentialDynamics files.
Input:
    FTNode:   file name
    format of input file:
    first line: PDB file name
    all other lines: eigen value, eigen vector
Output:
    EssentialDynamics object
"""

    def __init__(self, name='EssentialDynamics', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )
        fileTypes=[('all', '*')]
        self.widgetDescr['filename'] = {
            'class':'NEEntryWithFileBrowser', 'master':'node',
            'filetypes':fileTypes, 'title':'load file', 'width':16,
            'labelCfg':{'text':'file:'},
            'widgetGridCfg':{'labelSide':'left'},
            }

        ip = self.inputPortsDescr
        ip.append(datatype='string', name='filename')

        op =self.outputPortsDescr 
        op.append(datatype='None', name='ed')

	code = """def doit(self, filename):
    if filename:
        ed = EssentialDynamics()
        ed.load(filename)
        self.outputData(ed=ed)
        return

"""
        if code: self.setFunction(code)



class ViewEssentialDynamics(NetworkNode):

    """This node load EssentialDynamics files.
Input:
    FTNode:   file name
    format of input file:
    first line: PDB file name
    all other lines: eigen value, eigen vector
Output:
    EssentialDynamics object
"""

    def __init__(self, name='EssentialDynamics', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='Molecule', required=True, name='molecule')
        ip.append(datatype='None', name='ed')
        ip.append(datatype='int', required=True, name='index')
        ip.append(datatype='float', required=True, name='amplitude')
        ip.append(datatype='viewer', required=False, name='viewer')
        ip.append(datatype='geom', name='geom')
        op =self.outputPortsDescr 
        op.append(datatype='coordinates3D', name='coords')
        op.append(datatype='None', name='ed')

	code = """def doit(self, mol, ed, index, amplitude, viewer, geom):
    if mol.parser.filename !=ed.pdbFile or amplitude > 1.0 or amplitude < -1.0:
        return
    else:
        newCoords = ed.getCoords(index, amplitude)
        geom.Set(vertices = newCoords)
        viewer.Redraw()
        self.outputData(coords = newCoords , ed = ed)

"""
        if code: self.setFunction(code)



class LoopList(NetworkNode):

    """This node generate a looping list
Input:
    number of steps.
Output:
    a list of amplicudes between [-1, 1]

e.g. [0, -.1, -.2, -.3, -.4, -.5, -.6, -.7, -.8, -.9, -10., -10., -.9, -.8, -.7, -.6, -.5, -.4, -.3, -.2, -.1, 0.0, .1, .2, .3, .4, .5, .6, .7, .8, .9, .9, .8, .7, .6, .5, .4, .3, .2, .1, 0.0 ]

"""

    def __init__(self, name='Loop List', **kw):
        kw['name'] = name
        apply( NetworkNode.__init__, (self,), kw )

        ip = self.inputPortsDescr
        ip.append(datatype='int', required=True, name='steps')
        op =self.outputPortsDescr 
        op.append(datatype='list', name='loop')

	code = """def doit(self, steps):
    result=[]
    all=range(-1*steps, steps)
    half=steps/2
    tmp= all[:steps][:]
    tmp.reverse()
    result.extend(tmp)
    result.extend(all)
    tmp= all[steps:][:]
    tmp.reverse()
    result.extend(tmp)
    result = N.array(result,'f')/steps
    self.outputData(loop=result.tolist())

    
"""
        if code: self.setFunction(code)



## create library ##
from Vision.VPE import NodeLibrary
flextreelib = NodeLibrary('FlexTree', '#5B91FF')

## add nodes ##
flextreelib.addNode(FTMotionRotation, 'Axis Rotation', 'Motions')
flextreelib.addNode(FTMotionPointRotationDiscrete, 'Discrete Point Rotation',
                    'Motions')
flextreelib.addNode(FTMotionPointRotation, 'Point Rotation', 'Motions')
flextreelib.addNode(FTMotionCombiner, 'Combined Motion', 'Motions')
flextreelib.addNode(FTMotionHinge, 'Hinge', 'Motions')
flextreelib.addNode(FTMotionTranslation, 'Translation', 'Motions')
flextreelib.addNode(FTMotionGeneric4x4, 'Generic4x4', 'Motions')
flextreelib.addNode(FTMotionBoxTranslation, 'BoxTranslation', 'Motions')
flextreelib.addNode(FTMotionConeRotation, 'ConeRotation', 'Motions')
flextreelib.addNode(DiscreteRotamer, 'Rotamer sidechain', 'Motions')

flextreelib.addNode(FTShapeSphere, 'Sphere', 'Shapes')
try:
    #from pyefit import efit # for ellipsoids
    from geomutils import efitlib
    flextreelib.addNode(FTShapeEllipsoid, 'Ellipsoid', 'Shapes')
except:
    print 'Ellipsoid shape node is not loaded (could not import geomutils.efitlib module)'
    
flextreelib.addNode(FTShapeConvexHull, 'ConvexHull', 'Shapes')
flextreelib.addNode(FTShapeLines, 'Lines', 'Shapes')
flextreelib.addNode(FTShapeCPK, 'CPK', 'Shapes')
flextreelib.addNode(FTShapeMSMS, 'MSMS', 'Shapes')
flextreelib.addNode(FTShapeGeom, 'Geom', 'Shapes')

flextreelib.addNode(WriteXMLNode, 'Write XML', 'Output')
flextreelib.addNode(RandomMotion, 'Random Motion', 'Output')
flextreelib.addNode(WritePDBNode, 'SaveAs PDB', 'Output')
flextreelib.addNode(UpdateGeomInPMV, 'Update Geom in Pmv', 'Output')

flextreelib.addNode(ReadXMLNode, 'Read XML', 'Input')
flextreelib.addNode(RigidBodyFit, 'RigidBodyFit', 'Input')
flextreelib.addNode(BuildFTNode, 'FTNode', 'Input')
flextreelib.addNode(BuildFTRoot, 'FTRootNode', 'Input')
flextreelib.addNode(PDBQ2XML, 'PDBQ to XML', 'Input')
flextreelib.addNode(FlexibleResidue, 'Add Rotamer', 'Input')
flextreelib.addNode(ExcludeBackboneCB, 'Exclude sidechain', 'Input')
flextreelib.addNode(SelectAtomsNode, 'Select Atoms', 'Input')

flextreelib.addNode(LoadEssentialDynamics, 'Load Essential Dynamics', 'Input')
flextreelib.addNode(LoopList, 'LoopList for Essential Dynamics', 'Input')
LoopList
flextreelib.addNode(ViewEssentialDynamics, 'Choose Essential Dynamics', 'Output')

flextreelib.addNode(FlexTreeNode, 'FlexTreeNode', 'FT')
flextreelib.addNode(FlexTreeRootNode,'FlexTreeRootNode','FT')
flextreelib.addNode(BuildFTNode,'BuildFTNode','FT')
flextreelib.addNode(BuildFTRoot,'BuildFTRoot','FT')


if foundAutoDockFR:
    flextreelib.addNode(RMSDScoringNode, 'RMSDScoringNode', 'GA')
    flextreelib.addNode(AD305ScoringNode, 'AD305ScoringNode', 'GA')
    flextreelib.addNode(FTGA, 'FT GA', 'GA')
    flextreelib.addNode(ConfigureTreeFromGene, 'ConfigureTree', 'GA')
    flextreelib.addNode(PrintScoreNode, 'PrintScore', 'Output')
    flextreelib.addNode(ScoreContributionFromAtomsNode, 'Score->Atoms', 'Output')
    flextreelib.addNode(DockingBoxMacro, 'Docking Box', 'Macro')

    if foundAutoDockC:
        flextreelib.addNode(AD305ScoringNodeC, 'ADScoring,C++', 'GA')
        flextreelib.addNode(AD305SPENodeC, 'Single Point Energy', 'GA')


UserLibBuild.addTypes(flextreelib, 'FlexTree.VisionInterface.FlexTreeTypes')

try:
    UserLibBuild.addTypes(flextreelib, 'DejaVu.VisionInterface.DejaVuTypes')
except:
    pass

try:
    UserLibBuild.addTypes(flextreelib, 'MolKit.VisionInterface.MolKitTypes')
except:
    pass
