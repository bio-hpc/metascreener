## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

############################################################################
#
# Author: Yong Zhao
#
# Copyright: Yong Zhao, TSRI
#
#############################################################################


from MolKit.molecule import Atom,AtomSet,MoleculeSet
from MolKit.protein import Protein,Residue, Chain, ProteinSet
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.protein import Residue, ResidueSet
from MolKit import Read

from FlexTree.XMLParser import ReadXML
from FlexTree.FTMotions import FTMotionCombiner, FTMotion_BoxTranslation
from AutoDockFR.ScoringFunction import AD305ScoreC
from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent
import os, glob

from Pmv.mvCommand import MVCommand

#from Pmv.selectionCommands import MVStringSelector
from ViewerFramework.VFCommand import CommandGUI

##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     ExtendedSliderWidget,SaveButton, LoadButton
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.misc import ensureFontCase
from SimpleDialog import SimpleDialog

import Tkinter, types, string, Pmw, time
import numpy.oldnumeric as Numeric
N=Numeric

foundFlexTree=False
try:
    import FlexTree
    foundFlexTree = True
    from AutoDockFR.utils import saveGA_Result, findBestGenes, saveGA, \
         geneToScore, validate, getCoordsAndScores
except ImportError:
    pass

       

###############################  Essential Dynamics related #############

class LoadEssentialDynamics(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}
        self.inputFileName=""
        self.modeNum="1"

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'essentialDynamics'):
            self.vf.essentialDynamics=None

        
    def doit(self, filename, modeNum, **kw):
        """
        
        """
        from FlexTree.EssentialDynamics import EssentialDynamics
        ed=EssentialDynamics()
        ok=ed.load(filename)
        if ok:
            ed.chooseModes(modeNum)
            # fixme
            # ask if loading ed.pdbFile or apply it to some other mols(pdbqs?)
            mol=self.vf.readMolecule(ed.pdbFile, log=0)
                
##             except:
##                 msg="Can't load PDB file %s \n This file is used to generate the essential file %s"% (ed.pdbFile, filename)
##                 d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
##                                  buttons=['OK'], default=0, 
##                                  title='Error')
##                 err=d.go()
##                 msg="kao"
##                 d = SimpleDialog(self.vf.GUI.ROOT, text=msg,
##                                  buttons=["Yes","No"],
##                                  default=0, title="Locate the file yourself?")
##                 ok=d.go()
##             if ok==0: #answer was yes
##                 file = self.vf.askFileOpen(types= [('all', '*')],
##                                    idir='.',
##                                    title="Loading PDB file:")
                

                
                
            self.vf.essentialDynamics=ed
            ed.mol=mol[0]
            self.inputFileName=filename
            #remember the inputfileName so that it could be written to XML file
            self.vf.essentialDynamics.inputFileName=self.inputFileName
        else:
            msg="%s is not a valid mode number. Need an integer"% \
                         val['modeNum']
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                             buttons=['OK'], default=0, 
                             title='Error')
            err=d.go()
            return


    def __call__(self, filename, modeNum, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (filename, modeNum), kw)
        
       
    def guiCallback(self):
        val = self.showForm('Options')
        if val:
            if val.has_key('filename') and val.has_key('modeNum'):
                try:
                    modeNum=eval(val['modeNum'])                    
                except:
                    ##
                    msg="%s is not a valid mode number. Need an integer"% \
                         val['modeNum']
                    d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                                     buttons=['OK'], default=0, 
                                     title='Error')
                    err=d.go()
                    return
                
                apply( self.doitWrapper, (val['filename'], modeNum), )

                
    def buildFormDescr(self, formName):
        #from mglutil.util.misc import uniq
        if formName=='Options':
            self.ifd= ifd= InputFormDescr(
                title='Consolidate all log files into a single file')

            ###  define input Directory
            ifd.append({'name':'fileGroup',
                        'widgetType':Pmw.Group,
                        'container':{'fileGroup':"w.interior()"},
                        'wcfg':{},
                        'gridcfg':{'sticky':'wnse', 'columnspan':4}})

            ifd.append({'name':'modeNum',
                        'widgetType':Pmw.EntryField,
                        'parent':'fileGroup',
                        'tooltip':'Enter number of modes',
                        'wcfg':{'label_text':'Number of Modes:',
                                'labelpos':'w','value':self.modeNum },
                        'gridcfg':{'sticky':'we'},
                        })

            ifd.append({'name':'filename',
                        'widgetType':Pmw.EntryField,
                        'parent':'fileGroup',
                        'tooltip':'Enter a filename',
                        'wcfg':{'label_text':'Load from file:',
                                'labelpos':'w', 'value':self.inputFileName},
                        'gridcfg':{'sticky':'we'},
                        })
            ifd.append({'widgetType':LoadButton,
                        'name':'filebrowse',
                        'parent':'fileGroup',
                        'tooltip':'Enter a file name',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':"Choose filename",
                                'types':[('all file', '*.*')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

      ## or use a thumbwheel?
            
##             ifd.append({'name':'modeNum',
##                         #'parent':'fileGroup',
##                         'widgetType':ThumbWheel,
##                         'tooltip':'Choose the top N modes..\n',
##                         'wcfg':{ 'labCfg':{'text':
##                                            'Number of modes:', 
##                                            'font':(ensureFontCase('helvetica'),12,'bold')},
##                                  'showLabel':1, 'width':100,
##                                  'min':0, 'max':100, #fixme
##                                  'type':int, 'precision':1,
##                                  'immediate':1,
##                                  'value':0,'continuous':1,
##                                  'callback':self.setIndex_cb, 
##                                  'oneTurn':10, 'wheelPad':2, 'height':30},
##                         'gridcfg':{'sticky':'we'}})
            return ifd

    def setEntry_cb(self, filename ):
        ebn = self.cmdForms['Options'].descr.entryByName
        entry = ebn['filename']['widget']
        entry.setentry(filename)

class BuildFlexTree_ED(MVCommand):
    """ add essential dynamics to FlexTree"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'essentialDynamics'):
            self.vf.essentialDynamics=None
        
    def doit(self, **kw):
        """

        """
        if self.vf.essentialDynamics is None:
            msg="Essential Dynamics file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return

        ## init FlexTree here
        ## see ttt008.py
        self._writeXML(self.vf.essentialDynamics)
        pass


    def _writeXML(self, ed):
        """ private function.."""
        lines1=['<?xml version="1.0" ?>',
                ' <root',
                '  name="Root" ',
                '  id="0"']
        lines2= '  discreteMotionParams="name: str Essentian_Dynamics, modeNum: int %d, edFile: str %s "'
        lines3=' selectionString="%s"'
        lines4=[' discreteMotion="FTMotion_EssentialDynamics"',
                ' convolve="FTConvolveApplyMatrix"']
        lines5=' file="%s">'
        lines6= ' </root>' 
        outXML=file('%s_ED.xml'%ed.mol.name, 'w')
        for line in lines1:
            outXML.write(line + '\n')
        outXML.write(lines2%(len(ed.vectors), ed.inputFileName) + " \n")
        outXML.write(lines3%(ed.mol.name) + '\n')
        for line in lines4:
            outXML.write(line + '\n')
        outXML.write(lines5%ed.pdbFile + '\n')
        outXML.write(lines6 + '\n')
        outXML.close()

        from FlexTree.XMLParser import ReadXML
        reader = ReadXML()
        reader('%s_ED.xml'%ed.mol.name)
        tree=reader.get()[0]
        root=tree.root
        tree.adoptRandomConformation()
        root.updateCurrentConformation()
        print '------------ done with ' , ed.mol.name

        x=os.system('rm -f %s_ED.xml'%ed.mol.name)
        self.vf.FT_ED=tree

    
    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
        
       
    def guiCallback(self):
        apply( self.doitWrapper, )  


class AddRotamerToED(MVCommand):
    """ add rotamer side chains to FlexTree"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'essentialDynamics'):
            self.vf.essentialDynamics=None
        
    def doit(self, nodes, **kw):
        """

        """
        tree=self.vf.FT_ED
        if tree is None:
            msg="Essential Dynamics file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return

        if isinstance(nodes, Residue):
            tree.addRotamerToRootNode(nodes)
        elif isinstance( nodes, ResidueSet):
            for node in nodes:
                tree.addRotamerToRootNode(node)
        else:
            msg="Need a Residue or ResideSet as input (nothing selected)"
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()

            
    def __call__(self, nodes, **kw):
        """
        command line version, call doit()
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return

        return apply ( self.doitWrapper, (nodes, ), kw)

    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes:
            print "Nothing selected."
            return 'Error' # to prevent logging
        else:
            apply(self.doitWrapper, (nodes,),)



class SaveFlexTree_ED(MVCommand):
    """ add essential dynamics to FlexTree"""
    def __init__(self):
        MVCommand.__init__(self)
        self.lastDir='.'

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'FT_ED'):
            self.vf.FT_ED=None
        
    def doit(self, outputFile, **kw):
        """

        """
        if self.vf.FT_ED is None:
            msg="FlexTree for Essential Dynamics not defined."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        from FlexTree.XMLParser import WriteXML
        tree=self.vf.FT_ED

        #print self.vf.FT_ED.root.children[0].molecularFragment
        
        writor = WriteXML(tree)
        writor([tree], outputFile)

    
    def __call__(self, outputFile,**kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (outputFile,), kw)
        
    def guiCallback(self, event=None, *args, **kw):
        cmdmenuEntry = self.GUI.menu[4]['label']
        file = self.vf.askFileSave(types=[('xml file', '*.xml')],
                                   idir=self.lastDir,
                                   title="Save as XML")
        if file != None:
            self.lastDir = os.path.split(file)[0]
            #self.vf.GUI.configMenuEntry(self.GUI.menuButton, cmdmenuEntry,
            #                            state='disabled')
            mol = self.vf.tryto(self.doitWrapper, file, GUI=True )
            #self.vf.GUI.configMenuEntry(self.GUI.menuButton,
            #                            cmdmenuEntry,state='normal')



class ShowRmsd_VS_Score(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'dockingResult'):
            self.vf.dockingResult=None
        
    def doit(self, **kw):
        """
        draw RMSD_Score figure
        """

        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return

        dockingResult=self.vf.dockingResult
        recMol=dockingResult['receptor']
        ligMol=dockingResult['ligand']
        RMSDs = self.vf.dockingResult['RMSDs']
        scores =self.vf.dockingResult['scores']

        for i in range(len(RMSDs)):
            print RMSDs[i], scores[i]

##         from matplotlib import matlab        
##         matlab.plot(RMSDs,scores, 'bo')
##         matlab.ylabel('Scores (kcal/mol)')
##         matlab.xlabel('RMSD (A)')
##         matlab.title('RMSD vs. Scores')       

##         #filename='%s_%s.png'%(recMol.name, ligMol.name)
##         #matlab.savefig(filename, dpi=120)
##         #print "figure saved as %s."%filename
##         matlab.show()
        

    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
        
       
    def guiCallback(self):
        
        apply( self.doitWrapper, )  
        



class CloseED_FT(MVCommand):
    """ This command clean up all the Essential Dynamics - FlexTree related properties."""
    def __init__(self):
        MVCommand.__init__(self)

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'FT_ED'):
            self.vf.FT_ED=None
   
        
    def doit(self, **kw):
        """
        cleaning up
        """
        if self.vf.essentialDynamics is None :
            msg="Essential Dynamics file not loaded"
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
        else:
            ed=self.vf.essentialDynamics         
            viewer=ed.mol.geomContainer.masterGeom.viewer
            self.vf.deleteMol(ed.mol.name, log=0)            
            viewer.Redraw()
            self.vf.essentialDynamics=None
            if self.vf.FT_ED is None:
                self.vf.FT_ED=None   
        

    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
        
       
    def guiCallback(self):
        apply( self.doitWrapper, )  
        


  
class ShowEssentialDynamics(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes = [('all', '*')]        
        self.fileBrowserTitle ="Read Essential Dynamics File:"
        self.lastDir = "."                
        self.vectors=[]
        self.amplitudes=[]
        self.initilized=False
        self._lock=False # lock for redraw
        

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'essentialDynamics'):
            self.vf.essentialDynamics=None
        
    def doit(self, index=None, scaling=1.0, **kw):
        """
        
        """
        ed=self.vf.essentialDynamics
        if ed is None :
            msg="Essential Dynamics file not loaded yet. Do you want to load the essential dynamics file now?"
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            ok=d.go()
            return
        if not self.initilized:
            self.vectors=ed.vectors
            self.amplitudes=ed.amplitudes
            self.pdbFile=ed.pdbFile
            self.coords=ed.coords[:] ## fixme? a must?
            self.atoms=ed.mol.allAtoms
            self.initilized=True

        # hack to show backbone only..
        filter=ed.filter
        if filter[-2:] =='CA' or filter=='backbone':
            self.vf.displayLines(ed.mol.name+":::backbone", negate=False, displayBO=False, only=False, log=0, lineWidth=2)
        elif filter.split('+')[0]=='CA':
            self.vf.displayLines(ed.mol.name+":::backbone;"+ed.mol.name+":"+ed.filter.split('+')[1], negate=False, displayBO=False, only=False, log=0, lineWidth=2)
        else:
            pass
        
        if index==None:
            self.displayForm()
        else:            
            self._vibrate(index, scale=scaling)
        

    def __call__(self, index=None, scaling=1.0, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (index,scaling ), kw)
        
       
    def guiCallback(self, event=None, *args, **kw):
        return apply ( self.doitWrapper, ( ), kw)
        
    def displayForm(self):
        self.showIt=Tkinter.IntVar()
        resultNum=len(self.vectors)
        self.ifd=ifd=InputFormDescr(title =\
                                    'Essential Dynamics in '+ self.pdbFile)
        ifd.append({'name':'index',
                    'widgetType':ThumbWheel,
                    'wcfg':{ 'labCfg':{'text':'View Vector:', 
                                       'font':(ensureFontCase('helvetica'),12,'bold')},
                             'showLabel':1, 'width':100,
                             'min':0, 'max':resultNum-1,
                             'type':int, 'precision':1,
                             'immediate':1,
                             'value':0,'continuous':1,
                             'callback':self.setIndex_cb, 
                             'oneTurn':10, 'wheelPad':2, 'height':20},
                    'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'scale',
                    'widgetType':ThumbWheel,
                    'wcfg':{ 'labCfg':{'text':'Scale factor:', 
                                       'font':(ensureFontCase('helvetica'),12,'bold')},
                             'showLabel':1, 'width':100,
                             'min':0.0, 'max':10.0, # fixme..
                             'type':float, 'precision':0.1,
                             'immediate':1,
                             'value':1.0,'continuous':1,
                             'callback':self.setScalingFactor_cb,
                             'oneTurn':1.0, 'wheelPad':2, 'height':20},
                    'gridcfg':{'sticky':'we'}})

        ifd.append({'name':'ShowIt',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text': 'Show the vibration',
                            'variable': self.showIt,
                            },
                    'command':self.showIt_cb, 
                    'gridcfg':{'sticky':'w'}})


        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.index = self.ifd.entryByName['index']['widget']
        self.scalingFactor = self.ifd.entryByName['scale']['widget']
        return ifd

    def setIndex_cb(self, event=None):
        show= self.showIt.get()
        if not show:
            return
        index = int(self.index.get())
        scale = self.scalingFactor.get()
        self._vibrate(index, scale=scale)

    def setScalingFactor_cb(self, event=None):
        pass

    def showIt_cb(self, event=None):
        show= self.showIt.get()
        if not show:
            return

        index = int(self.index.get())
        scale = self.scalingFactor.get()
        self._vibrate(index, scale=scale)

    def _vibrate(self, index, steps=10, scale=1.0):        
        if self._lock:
            print "Please wait till the current update is done"
            return
        ed=self.vf.essentialDynamics
        mol=self.vf.Mols.get(ed.mol.name)[0]
        movingAtoms=mol.NodesFromName(mol.name+ed.filter)
        movingAtoms=movingAtoms.parent.atoms
        
        modeNum=len(ed.vectors)
        if index >=modeNum:            
            print "Invalid index %d, index is up to %d"%(index, modeNum-1)
            return
        vi = self.vf.GUI.VIEWER        
##         mol=ed.mol
##         ggeoms = mol.geomContainer.geoms
        vi.stopAutoRedraw()
        self._lock=True
        wList=range(-1, -steps-1, -1) + \
               range(-steps+1, steps+1) +\
               range(steps-1, -1, -1)
        #wList=[-steps, 0, steps]
        for i in wList:
            i=i*1.0 # float
            weight=i/steps
            newCoords=ed.getCoords(index, weight, scale, allAtoms=False)
            movingAtoms.updateCoords(newCoords,0)
            #ed.mol.allAtoms.setConformation(1)
            modEvent = EditAtomsEvent('coords', movingAtoms)
            self.vf.dispatchEvent(modEvent)
            #self.atoms.updateCoords(newCoords.tolist())
            #modEvent = ModificationEvent('edit', 'coords', self.atoms)
            #mol.geomContainer.updateGeoms(modEvent)
            #if line geometry only
            #ggeoms['bonded'].Set(vertices = newCoords)            
            vi.OneRedraw()

        vi.startAutoRedraw()
        self._lock=False


###

class InitFlexTree(MVCommand):
    """ Initialize a FlexTree"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'flexTree'):
            self.vf.flexTree=None
        
    def doit(self, mol, **kw):
        """

        """
##         if self.vf.essentialDynamics is None:
##             msg="Essential Dynamics file not loaded."
##             d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
##                 buttons=['OK'], default=0, 
##                 title='Error')
##             useTorTree=d.go()
##             return

        ## init FlexTree here
        ## see ttt008.py

        if isinstance(mol, ProteinSet) or isinstance(mol, MoleculeSet) :
            if len(mol) == 0: return
            mol=mol[0]
        self._writeXML(mol)
        pass


    def _writeXML(self, mol):
        """ private function.."""
        lines1=['<?xml version="1.0" ?>',
                '   <root',
                '     name="Root" ',
                '     id="0"',
                '     convolve="FTConvolveApplyMatrix"']
        lines2= '     selectionString="%s"'
        lines3=' file="%s">'
        lines4= ' </root>' 
        outXML=file('%s_tmp.xml'%mol.name, 'w')
        for line in lines1:
            outXML.write(line + '\n')
        outXML.write(lines2%(mol.name) + '\n')
        outXML.write(lines3%mol.parser.filename + '\n')
        outXML.write(lines4 + '\n')
        outXML.close()

        from FlexTree.XMLParser import ReadXML
        reader = ReadXML()
        reader('%s_tmp.xml'%mol.name)
        tree=reader.get()[0]
        root=tree.root
        tree.adoptRandomConformation()
        root.updateCurrentConformation()
        x=os.system('rm -f %s_tmp.xml'%mol.name)
        self.vf.flexTree=tree

    
    def __call__(self, mol,  **kw):
        """
        command line version, call doit()
        """
        if type(mol) is types.StringType:
            self.nodeLogString = "'" + mol +"'"
        mol = self.vf.expandNodes(mol)
        if not mol: return
        return apply ( self.doitWrapper, (mol,), kw)
        
       
    def guiCallback(self):
        nodes = self.vf.getSelection()
        apply( self.doitWrapper, (nodes, ),  )  


InitFlexTreeGUI = CommandGUI()
InitFlexTreeGUI.addMenuCommand('menuRoot', 'FlexTree', 'Init FlexTree')


class AddRotamerToFlexTree(MVCommand):
    """ add rotamer side chains to FlexTree"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'essentialDynamics'):
            self.vf.essentialDynamics=None
        
    def doit(self, nodes, **kw):
        """

        """
        tree=self.vf.flexTree
        if tree is None:
            msg="Essential Dynamics file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return

        if isinstance(nodes, Residue):
            tree.addRotamerToRootNode(nodes)
        elif isinstance( nodes, ResidueSet):
            for node in nodes:
                tree.addRotamerToRootNode(node)
        else:
            msg="Need a Residue or ResideSet as input (nothing selected)"
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()

            
    def __call__(self, nodes, **kw):
        """
        command line version, call doit()
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes: return

        return apply ( self.doitWrapper, (nodes, ), kw)

    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes:
            print "Nothing selected."
            return 'Error' # to prevent logging
        else:
            apply(self.doitWrapper, (nodes,),)


AddRotamerToFlexTree_GUI = CommandGUI()
AddRotamerToFlexTree_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Add Rotamer')
       
class SaveFlexTree(MVCommand):
    """ add essential dynamics to FlexTree"""
    def __init__(self):
        MVCommand.__init__(self)
        self.lastDir='.'

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'flexTree'):
            self.vf.flexTree=None
        
    def doit(self, outputFile, **kw):
        """

        """
        if self.vf.flexTree is None:
            msg="FlexTree not defined (initialized)."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        from FlexTree.XMLParser import WriteXML
        tree=self.vf.flexTree
        writor = WriteXML(tree)
        writor([tree], outputFile)

    
    def __call__(self, outputFile,**kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (outputFile,), kw)
        
    def guiCallback(self, event=None, *args, **kw):
        cmdmenuEntry = self.GUI.menu[4]['label']
        file = self.vf.askFileSave(types=[('xml file', '*.xml')],
                                   idir=self.lastDir,
                                   title="Save as XML")
        if file != None:
            self.lastDir = os.path.split(file)[0]
            #self.vf.GUI.configMenuEntry(self.GUI.menuButton, cmdmenuEntry,
            #                            state='disabled')
            mol = self.vf.tryto(self.doitWrapper, file, GUI=True )
            #self.vf.GUI.configMenuEntry(self.GUI.menuButton,
            #                            cmdmenuEntry,state='normal')


SaveFlexTree_GUI = CommandGUI()
SaveFlexTree_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Save FlexTree to XML')


                                  
class CloseFlexTree(MVCommand):
    """ cleaning up FlexTree related"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        
    def doit(self, **kw):
        """

        """
        tree=self.vf.flexTree
        self.vf.deleteMol(tree.root.getAtoms().top.uniq()[0].name, log=0)
        tree=None
        self.vf.GUI.VIEWER.Redraw()
            
    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, ( ), kw)

    def guiCallback(self):
        apply(self.doitWrapper, (),)


CloseFlexTree_GUI = CommandGUI()
CloseFlexTree_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Close FlexTree')


        
### loop prediction related.
class showAlternativeLoop(MVCommand):
    """ """
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}
        from memoryobject.memobject import return_share_mem_ptr, \
             allocate_shared_mem, FLOAT

        residueLen=5
        self.inputMem = allocate_shared_mem([residueLen*3, 3],
                                        'InputMemory', FLOAT)
        self.inputMemPtr =return_share_mem_ptr('InputMemory')[0]

        self.MaxSolutionNum=16
        self.outputMem = allocate_shared_mem([residueLen*3*self.MaxSolutionNum,
                                              3],
                                             'OutputMemory', FLOAT)
        self.outputMemPtr =return_share_mem_ptr('OutputMemory')[0]
        from FlexTree.loop_closure import solve
        self.solve=solve
        
    def doit(self, nodes, **kw):
        """

        """
        inputMem=self.inputMem
        outputMem=self.outputMem
        atoms=nodes.atoms
        N=atoms.get('N')
        CA=atoms.get('CA')
        C=atoms.get('C')
        coords=N.coords+CA.coords+C.coords   # NOTE: has to be N-CA-C !!
        inputMem[:] = Numeric.array(coords, 'f')[:]
        solNB=self.solve(self.inputMemPtr,self.outputMemPtr )
        res=outputMem[:solNB*3*5]
        from MolKit import WritePDB
        for sol in range(solNB):
            n=N[:]
            ca=CA[:]
            c=C[:]
            n.updateCoords(res[sol*15:sol*15+5], 0)
            ca.updateCoords(res[sol*15+5:sol*15+10], 0)
            c.updateCoords(res[sol*15+10:sol*15+15], 0)
            nodes=n+ca+c
            nodes.sort()
            WritePDB("loop_%d.pdb"%sol, nodes)
            self.vf.readMolecule("loop_%d.pdb"%sol)

 ##            msg="Need a Residue or ResideSet as input (nothing selected)"
##             d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
##                 buttons=['OK'], default=0, 
##                 title='Error')
##             useTorTree=d.go()

            
    def __call__(self, nodes, **kw):
        """
        command line version, call doit()
        """
        if type(nodes) is types.StringType:
            self.nodeLogString = "'" + nodes +"'"
        nodes = self.vf.expandNodes(nodes)
        if not nodes:
            return
        elif isinstance(nodes, ResidueSet) and len(nodes)==5:
            return apply ( self.doitWrapper, (nodes, ), kw)
        else:
            return

    def guiCallback(self):
        nodes = self.vf.getSelection()
        if not nodes:
            print "Nothing selected."
            return 'Error' # to prevent logging
        else:
            # only works when 5 residues(in sequence) are selected
            if isinstance(nodes, ResidueSet) and len(nodes)==3:
                apply(self.doitWrapper, (nodes,),)
            else:
                print 'foo'
                return



  
######## GUI (includes menu, commandList. etc. ) ##########

## setup AutoDockFR
SetupAutoDockFRGUI = CommandGUI()
SetupAutoDockFRGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'Setup AutoDockFR')

 ##  AutoDockFR log related
ConsolidateLogsGUI = CommandGUI()
ConsolidateLogsGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'Consolidate Logs',
                                  cascadeName="AutoDockFR Log")
LoadDockingLogGUI = CommandGUI()
LoadDockingLogGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'Load Log file',
                                 cascadeName="AutoDockFR Log")
ViewDockingLogGUI = CommandGUI()
ViewDockingLogGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'ViewLog',
                                 cascadeName="AutoDockFR Log")
ShowPDBConf_GUI = CommandGUI()
ShowPDBConf_GUI.addMenuCommand('menuRoot', 'AutoDockFR', 'Show PDB Conformation',
                               cascadeName="AutoDockFR Log")
CloseLogFile_GUI = CommandGUI()
CloseLogFile_GUI.addMenuCommand('menuRoot', 'AutoDockFR', 'Close Log File',
                                cascadeName="AutoDockFR Log")

SaveLigandGUI = CommandGUI()
SaveLigandGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'save ligand',
                             cascadeName="Save current")
SaveReceptorGUI = CommandGUI()
SaveReceptorGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'save receptor',
                               cascadeName="Save current")
TestDockingGUI = CommandGUI()
TestDockingGUI.addMenuCommand('menuRoot', 'AutoDockFR', 'test docking')


 ##  essential dynamics related

LoadEssentialDynamics_GUI = CommandGUI()
LoadEssentialDynamics_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Load Essential Dynamics', cascadeName="Essential Dynamics")

BuildFlexTree_ED_GUI = CommandGUI()
BuildFlexTree_ED_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Add Essential Dynamics to FlexTree', cascadeName="Essential Dynamics")

AddRotamerToEssentialDynamics_GUI = CommandGUI()
AddRotamerToEssentialDynamics_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Add Rotamer', cascadeName="Essential Dynamics")

SaveFlexTree_ED_GUI = CommandGUI()
SaveFlexTree_ED_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Save FlexTree to XML', cascadeName="Essential Dynamics")

CloseED_FT_GUI = CommandGUI()
CloseED_FT_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Close All (FT,ED) ', cascadeName="Essential Dynamics")

ShowEssentialDynamics_GUI = CommandGUI()
ShowEssentialDynamics_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Show Essential Dynamics', cascadeName="Essential Dynamics")



## loop prediction
ShowAlternativeLoop = CommandGUI()
ShowAlternativeLoop.addMenuCommand('menuRoot', 'FlexTree', 'Show Alternative Loops')





## foundMatplotlib = False    
## try:
##     from matplotlib import matlab
##     foundMatplotlib = True
## except:
##     pass

foundMatplotlib=True

commandList = [
    {'name':'initFlexTree', 'cmd':InitFlexTree(),
     'gui':InitFlexTreeGUI},    
     {'name':'addRotamerToFlexTree', 'cmd':AddRotamerToFlexTree(),
     'gui':AddRotamerToFlexTree_GUI},        
    {'name':'saveFlexTree', 'cmd':SaveFlexTree(),
     'gui':SaveFlexTree_GUI},
    {'name':'closeFlexTree', 'cmd':CloseFlexTree(),
     'gui':CloseFlexTree_GUI},

##     {'name':'consolidateLogs', 'cmd':ConsolidateLogs(),
##      'gui':ConsolidateLogsGUI},
##     {'name':'setupDock', 'cmd':setupAutoDockFR(),
##      'gui':SetupAutoDockFRGUI},
##     {'name':'loadDockingLog', 'cmd':LoadDockingLog(),
##      'gui':LoadDockingLogGUI},
##     {'name':'viewDockingLog', 'cmd':ViewDockingLog(),
##      'gui':ViewDockingLogGUI},
##     {'name':'showPDBConformation', 'cmd':ShowPDBConformation(),
##      'gui':ShowPDBConf_GUI},    
##     {'name':'closeLogFile', 'cmd':CloseLogFile(),
##      'gui':CloseLogFile_GUI},
##     {'name':'saveLigand', 'cmd':SaveLigand(),
##      'gui':SaveLigandGUI},
##     {'name':'saveReceptor', 'cmd':SaveReceptor(),
##      'gui':SaveReceptorGUI},
##     {'name':'testDock', 'cmd':testDocking(),
##      'gui':TestDockingGUI},


    {'name':'loadED', 'cmd':LoadEssentialDynamics(),
     'gui':LoadEssentialDynamics_GUI},
    {'name':'buildFT_ED', 'cmd':BuildFlexTree_ED(),
     'gui':BuildFlexTree_ED_GUI},
    {'name':'addRotamerToED', 'cmd':AddRotamerToED(),
     'gui':AddRotamerToEssentialDynamics_GUI},
    {'name':'saveFT_ED', 'cmd':SaveFlexTree_ED(),
     'gui':SaveFlexTree_ED_GUI},
    {'name':'closeED_FT', 'cmd':CloseED_FT(),
     'gui':CloseED_FT_GUI},
    
    {'name':'showED', 'cmd':ShowEssentialDynamics(),
     'gui':ShowEssentialDynamics_GUI},

##     {'name':'showLoop', 'cmd':showAlternativeLoop(),
##      'gui':ShowAlternativeLoop},


]

## if foundMatplotlib:
##     ShowRMSD_SCORE_GUI = CommandGUI()
##     ShowRMSD_SCORE_GUI.addMenuCommand('menuRoot', 'AutoDockFR', 'RMSD vs. Score', cascadeName="AutoDockFR Log")
    
##     commandList.append(
##         {'name':'showRmsd_VS_Score', 'cmd':ShowRmsd_VS_Score(),
##      'gui':ShowRMSD_SCORE_GUI},
##         )

def initModule(viewer):
    """ initializes commands for secondary structure and extrusion.  """
    for dict in commandList:
	viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
