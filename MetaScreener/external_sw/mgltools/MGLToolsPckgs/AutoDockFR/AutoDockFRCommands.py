## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#############################################################################
#
# Authors: Yong Zhao, Matt Danielson, Ruth Huey, Michel Sanner
#
# Copyright: Yong Zhao, Michel Sanner and TSRI
#
#############################################################################


from MolKit.molecule import Atom,AtomSet,MoleculeSet
from MolKit.protein import Protein,Residue, Chain, ProteinSet
from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.protein import Residue, ResidueSet
from MolKit import Read

from FlexTree.XMLParser import ReadXML
from FlexTree.FTMotions import FTMotionCombiner, FTMotion_BoxTranslation
from AutoDockFR.ADCscorer import AD42ScoreC
from Pmv.moleculeViewer import DeleteAtomsEvent, AddAtomsEvent, EditAtomsEvent
import os, glob, random

from Pmv.mvCommand import MVCommand

#from Pmv.selectionCommands import MVStringSelector
from ViewerFramework.VFCommand import CommandGUI

##  from ViewerFramework.gui import InputFormDescr
from mglutil.gui.InputForm.Tk.gui import InputFormDescr
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import ListChooser, \
     ExtendedSliderWidget,SaveButton, LoadButton
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from SimpleDialog import SimpleDialog

import Tkinter, types, string, Pmw, time
import numpy.oldnumeric as Numeric
N=Numeric

from DejaVu.bitPatterns import patternList
from opengltk.OpenGL import GL
from DejaVu.Box import Box
from DejaVu import viewerConst
face=((0,3,2,1),(3,7,6,2),(7,4,5,6),(0,1,5,4),(1,2,6,5),(0,4,7,3))
coords=((1,1,-1),(-1,1,-1),(-1,-1,-1),(1,-1,-1),(1,1,1),(-1,1,1),(-1,-1,1),(1,-1,1))
#new style RGB->
materials=((0,0,1),(0,1,0),(0,0,1),(0,1,0),(1,0,0),(1,0,0),)
box=Box('box', materials=materials, vertices=coords, faces=face, 
                    inheritMaterial=0, frontPolyMode=GL.GL_FILL)
box.inheritShading=0
box.shading=GL.GL_FLAT
box.Set(matBind=viewerConst.PER_PART)
box.Set(visible=0, inheritPolygonStipple=0)
box.polygonstipple.Set(pattern=patternList[0])
box.Set(stipplePolygons=1)
box.transparent=0
box.oldFPM = None
box.in_viewer = False

from DejaVu.Points import CrossSet
cenCross = CrossSet('BoxCenter', materials=((1.,1.,0),),
                    inheritMaterial=0,
                    offset=1.0,lineWidth=2, visible=0, pickable=0)
cenCross.in_viewer = False


foundFlexTree=False
try:
    import FlexTree
    foundFlexTree = True
    from AutoDockFR.utils import saveGA_Result, getResultsFromLogFile, saveGA, \
         geneToScore, validate, getCoordsAndScores, getSettingsFromLog
except ImportError:
    pass



def _tryLoadXML(xmlFileName, logFileName=None):
    reader = ReadXML()
    try:
        reader(xmlFileName, cmdLineOnly=True)
        tree=reader.get()[0]
        return tree
    except:
        if logFileName:
            try:
                aa=string.split(logFileName, '/')
                bb=string.join(aa[:-1], '/')
                xmlFileName=bb+'/' + xmlFileName
                reader(xmlFileName, cmdLineOnly=True)
                tree=reader.get()[0]
                return tree
            except:
                return None
        else:
            return None



class FlipDockCommand(MVCommand):

    def doit(self):
        if self.vf.GUI.menuBars.has_key('AutoDockFRBar'):
            return
        else:            
            #self.browseCommands('foo', commands = None, package = 'AutoDockFR')
            pass
            
    
    def hide(self, event=None):
        if self.root:
            self.root.withdraw()
        self.vf.GUI.toolbarCheckbuttons['flipdock']['Variable'].set(0)
        self.GUI.menuBars['AutoDockFRBar'].pack_forget()

    
    def guiCallback(self):
        if self.vf.GUI.toolbarCheckbuttons['flipdock']['Variable'].get():
            self.vf.GUI.menuBars['AutoDockFRBar'].pack(fill='x',expand=1)
        else:
            self.vf.GUI.menuBars['AutoDockFRBar'].pack_forget()
        self.doitWrapper()

    def __call__(self, **kw):
        """ """
        apply( self.doitWrapper, (), kw )

######## end of AutoDockFRCommands Class

class LoadLigXML(MVCommand):
    """ View the docking results saved in log file """
    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes = [('all', '*.xml')]        
        self.fileBrowserTitle ="Load XML file:"
        self.lastDir = "."
        return
        
    def updateViewer(self):
        vi=self.vf.GUI.VIEWER
        vi.ResetCurrentObject()
        vi.NormalizeCurrentObject()
        vi.CenterCurrentObject()

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        
    def doit(self, xmlFileName, **kw):
        """
        """
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        
        tree=_tryLoadXML(xmlFileName)
        if tree is None:
            print "Error in opening ligand XML file"
            return

        self.vf.flipdockSetting['ligandFT']=tree
        try:
            self.vf.readMolecule(tree.pdbfilename, log=0)
        except:
            print "Error in opening ligand file", tree.pdbfilename
            raise
        
        self.vf.color(tree.root.getAtoms().top.uniq()[0].name,\
                      [(0.0, 1.0, 0.0)], ['lines'], log=0)
        self.vf.flipdockSetting['ligand']=xmlFileName
        self.updateViewer()

    def guiCallback(self):
        #cmdmenuEntry = self.GUI.menu[4]['label']
        file = self.vf.askFileOpen(types=self.fileTypes,
                                   idir=self.lastDir,
                                   title=self.fileBrowserTitle)
        if file != None:
            self.lastDir = os.path.split(file)[0]
            apply( self.doitWrapper, (file, ) )
            
        return


class LoadLigPDBQ(LoadLigXML):
    """ load ligand from a pdbq file """
    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes = [('all', '*.pdbq')]        
        self.fileBrowserTitle ="Load PDBQ file:"
        self.lastDir = "."
        return

    def doit(self, pdbqFileName, **kw):
        """
        """        
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}

        from AutoDockFR.utils import pdbqt2XML
        xmlFileName=pdbqFileName.split(".pdbq")[0] + ".xml"
        pdbqt2XML(pdbqFileName, xmlFileName)
        self.vf.loadLigandXML(xmlFileName)
        msg="The torTree in %s is converted to FlexTree, saved in %s"\
             %(pdbqFileName, xmlFileName)
        d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                         buttons=['OK'], default=0, 
                         title='Attention')
        res=d.go()
        return


class SetDockingBox(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        self.xCen = Tkinter.StringVar()
        self.yCen = Tkinter.StringVar()
        self.zCen = Tkinter.StringVar()
        self.showBox=Tkinter.IntVar()
        self.showCenter=Tkinter.IntVar()
        self.gridcenter = [0.,0.,0.]
        self.dims=[10,10,10]
        self.oldx=0
        self.oldy=0
        self.oldz=0
        return

    def onAddCmdToViewer(self):
        if not cenCross.in_viewer:
            self.vf.GUI.VIEWER.AddObject(cenCross, redo=0)
            cenCross.in_viewer = True
        if not box.in_viewer:
            self.vf.GUI.VIEWER.AddObject(box, redo=0)
            box.in_viewer = True
        return

    def doit(self, center, dims, **kw):
        if not self.vf.flipdockSetting.has_key('ligandFT'):
            self.vf.flipdockSetting['box']={"center":center,
                                            'dims':dims}
            self.vf.flipdockSetting['boxSaved']=False
##             msg="Please load a ligand first."
##             d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
##                              buttons=['OK'], default=0, 
##                              title='Error')
##             useTorTree=d.go()
##             return
        
        else:
            ligFT=self.vf.flipdockSetting['ligandFT']
            from AutoDockFR.utils import addDockingBox
            addDockingBox(ligFT, center, dims)            
        return
    
    
    def buildForm(self):
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        if self.vf.flipdockSetting.has_key('ligandFT'):
            from AutoDockFR.utils import locateDockingBoxInfo
            c,d=locateDockingBoxInfo(self.vf.flipdockSetting['ligandFT'])
            if c is not None:
                self.gridcenter=c
            if d is not None:
                self.dims=d
        
        # called once to set up form        
        ifd = self.ifd = InputFormDescr(title = "Configure Docking Box")
        specfont = ('Times',14,'bold') #('Helvetical', 12, 'bold')
        ifd.append( {'name': 'xScaleLab',
                     'widgetType':Tkinter.Label,
                     'wcfg':{'text':'Box diminsion in X:', 
                             'font':specfont, 
                             },
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'dim_x',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'wcfg':{'text':None,
                            'showLabel':1, 'width':100,
                            'min':0,
                            'max':100,
                            'lockBMin':1,
                            'lockBIncrement':1,
                            'value':self.dims[0],
                            'oneTurn':10,
                            'type':'int',
                            'canvasCfg':{'bg':'red'},
                            'wheelLabCfg':{'font':specfont},
                            'callback':self.update_cb,
                            'continuous':1, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':Tkinter.E,
                               'row':-1, 'column':2,
                               'columnspan':2}})
        ifd.append( {'name': 'yScaleLab',
                     'widgetType':Tkinter.Label,
                     'wcfg':{'text':'Box diminsion in Y', 
                             'font':('Helvetica',12,'bold')},
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'dim_y',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    #'wcfg':{'text':'number of points in y-dimension',
                    'wcfg':{'text':None,
                            'showLabel':1, 'width':100,
                            'min':0,
                            'max':100,
                            'lockBMin':1,
                            'lockBMax':1,
                            'lockBIncrement':1,
                            'value':self.dims[1],
                            'oneTurn':10,
                            'type':'int',
                            'increment':1,
                            'canvasCfg':{'bg':'green'},
                            'wheelLabCfg':{'font':specfont},
                            'callback':self.update_cb,
                            'continuous':1, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'e','columnspan':2,
                               'row':-1, 'column':2,}})
        ifd.append( {'name': 'zScaleLab',
                     'widgetType':Tkinter.Label,
                     'wcfg':{'text':'Box diminsion in Z', 
                             'font':('Helvetica',12,'bold')},
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'dim_z',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    #'wcfg':{'text':'number of points in z',
                    'wcfg':{'text':None,
                            'showLabel':1, 'width':100,
                            'min':0,
                            'max':100,
                            'lockBMin':1,
                            'lockBMax':1,
                            'lockBIncrement':1,
                            'value':self.dims[2],
                            'type':'int',
                            'oneTurn':10,
                            'increment':1,
                            'canvasCfg':{'bg':'blue'},
                            #'canvascfg':{'bg':'blue'},
                            'wheelLabCfg':{'font':specfont},
                            'callback':self.update_cb,
                            'continuous':1, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'e','columnspan':4,
                               'row':-1, 'column':2}})
        ifd.append({ 'widgetType':Tkinter.Label,
                     'wcfg':{ 'text': '',},
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})

        ifd.append({ 'widgetType':Tkinter.Label,
                     'wcfg':{ 'text':'Box Center',
                              'font':('Helvetica',12,'bold')},
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':4}})
        ifd.append( {'name': 'xcenter',
                     'widgetType':Tkinter.Entry,
                     'wcfg': {
            'label': 'Center X',
            'width':7,
            'textvariable': self.xCen
            },
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'xoffset',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'wcfg':{'text':None,
                            'showLabel':2, 'width':100,
                            'precision':3,
                            'canvasCfg':{'bg':'red'},
                            'callback':self.set_xoffset,
                            'wheelLabCfg':{'font':specfont},
                            'continuous':1, 'oneTurn':10, 'wheelPad':2, 'height':20},
                    'gridcfg':{'sticky':'e','row':-1, 'column':2,'columnspan':2}})
        ifd.append( {'name': 'ycenter',
                     'widgetType':Tkinter.Entry,
                     'wcfg': {
            'label': 'Center Y',
            'width':7,
            'textvariable': self.yCen
            },
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'yoffset',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'wcfg':{'text':None,
                            'showLabel':2, 'width':100,
                            'precision':3,
                            'canvasCfg':{'bg':'green'},
                            'wheelLabCfg':{'font':specfont},
                            'continuous':1, 'oneTurn':10,
                            'callback':self.set_yoffset,
                            'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'e', 'row':-1, 'column':2,'columnspan':2}})
        ifd.append( {'name': 'zcenter',
                     'widgetType':Tkinter.Entry,
                     'wcfg': {
            'label': 'Center Z',
            'width':7,
            'textvariable': self.zCen
            },
                     'gridcfg':{'sticky':Tkinter.W, 'columnspan':2}})
        ifd.append({'name': 'zoffset',
                    'wtype':ThumbWheel,
                    'widgetType':ThumbWheel,
                    'wcfg':{'text':None,
                            'showLabel':2,  'width':100,
                            'precision':3,
                            'canvasCfg':{'bg':'blue'},
                            'wheelLabCfg':{'font':specfont},
                            'callback':self.set_zoffset,
                            'continuous':1, 'oneTurn':10, 'wheelPad':1, 'height':20},
                    'gridcfg':{'sticky':'e','row':-1,'column':2,
                               'columnspan':2}})
        ifd.append({'name':'showBox',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip':'Show the docking box?',
                    'variable':self.showBox,
                    'text':'Show Docking Box',                    
                    'command': self.showBoxAndCenter,
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name':'showCenter',
                    'widgetType':Tkinter.Checkbutton,
                    'tooltip':'Show the grid center?',
                    'variable':self.showCenter,
                    'command': self.showBoxAndCenter,
                    'text':'Show Box Center',
                    'gridcfg':{'sticky':'w'}})
        ifd.append({'name': 'playB',
                    'widgetType': Tkinter.Button,
                    'tooltip':'Set docking box using the current box',
                    'text':'Set the docking box',
                    'wcfg':{'bd':4},
                    'gridcfg':{'sticky':'ew','columnspan':1},
                    'command':self.setBox_cb})
        self.form = self.vf.getUserInput(self.ifd, scrolledFrame=1,
                                         width=330, height=400, modal=0, blocking=0)
        #self.form.root.protocol('WM_DELETE_WINDOW',self.Close_cb)
        
        # setup handles to widgets
        self.nxpts = self.ifd.entryByName['dim_x']['widget']
        self.nypts = self.ifd.entryByName['dim_y']['widget']
        self.nzpts = self.ifd.entryByName['dim_z']['widget']
        return

    def set_xoffset(self, val):
        # callback for xoffset Thumbwheel
        newval = float(val)
        _newval = round((newval-self.oldx)+float(self.xCen.get()), 3)
        self.oldx = newval
        self.xCen.set(str(_newval))
        #this changes center so call updateCoofds
        self.updateCoords()
        

    def set_yoffset(self, val):
        # callback for yoffset Thumbwheel
        newval = float(val)
        _newval = round((newval-self.oldy)+ float(self.yCen.get()), 3)
        self.oldy = newval
        self.yCen.set(str(_newval))
        #this changes center so call updateCoofds
        self.updateCoords()
        
    def set_zoffset(self, val):
        # callback for zoffset Thumbwheel
        newval = float(val)
        _newval = round((newval-self.oldz)+float(self.zCen.get()), 3)
        self.oldz = newval
        self.zCen.set(str(_newval))
        #this changes center so call updateCoofds
        self.updateCoords()

    def updateCoords(self, event=None):
        try:
            self.gridcenter = (round(float(self.xCen.get()),3), round(float(self.yCen.get()),3),round(float(self.zCen.get()),3))
##             #also make sure auto is turned off
##             self.gridCenterType = 'set'
            self.updateBox()
        except ValueError:
            pass

  
    def update_cb(self, event=None):
        self.updateBox()

    def setBox_cb(self, event=None):
        center= self.gridcenter
        dims=[ self.nxpts.get(), self.nypts.get(), self.nzpts.get()]
        apply ( self.doitWrapper, (center, dims), )


    def showBoxAndCenter(self, event=None):
        box.Set(visible=self.showBox.get())
        cenCross.Set(visible=self.showCenter.get())
        cenCross.Set(vertices=(tuple(self.gridcenter),))
        self.vf.GUI.VIEWER.Redraw()
            
    def updateValues(self):
        self.nxpts.set(self.dims[0])
        self.nypts.set(self.dims[1])
        self.nzpts.set(self.dims[2])
        #xCen,yCen and zCen are entries so must have strings
        self.xCen.set(str(self.gridcenter[0]))
        self.yCen.set(str(self.gridcenter[1]))
        self.zCen.set(str(self.gridcenter[2]))
        self.showBox.set(1)
        self.showCenter.set(1)
        #self.showGridBox()
        #self.ifd.entryByName['spacenumber']['widget'].val = spacing

    def updateBox(self, event=None):
        xnum = self.nxpts.get()
        ynum = self.nypts.get()
        znum = self.nzpts.get()
        spacing=1
        xlen = round(spacing*xnum, 4)
        ylen = round(spacing*ynum, 4)
        zlen = round(spacing*znum, 4)
        c = self.gridcenter
        pts = [ (c[0]+xlen*0.5, c[1]+ylen*0.5, c[2]-zlen*0.5),
                    (c[0]-xlen*0.5, c[1]+ylen*0.5, c[2]-zlen*0.5),
                    (c[0]-xlen*0.5, c[1]-ylen*0.5, c[2]-zlen*0.5),
                    (c[0]+xlen*0.5, c[1]-ylen*0.5, c[2]-zlen*0.5),
                    (c[0]+xlen*0.5, c[1]+ylen*0.5, c[2]+zlen*0.5),
                    (c[0]-xlen*0.5, c[1]+ylen*0.5, c[2]+zlen*0.5),
                    (c[0]-xlen*0.5, c[1]-ylen*0.5, c[2]+zlen*0.5),
                    (c[0]+xlen*0.5, c[1]-ylen*0.5, c[2]+zlen*0.5)
                    ]
        box.vertexSet.vertices.array[:] = pts
        box.RedoDisplayList()
        #box.Set(center=self.gridcenter, xside=xlen, yside=ylen, zside=zlen)
        cenCross.Set(vertices=(tuple(self.gridcenter),))
        self.vf.GUI.VIEWER.Redraw()

    def guiCallback(self):
        """called each time the menuText['SetGridMB'] button is pressed"""
        if not hasattr(self, 'form'):
            self.buildForm()
        else:
            self.form.deiconify()
        #make sure form entries reflect gpo data
        self.updateValues()
        self.updateCoords()
        self.showBoxAndCenter()
        return


class SaveLigXML(MVCommand):
    """ View the docking results saved in log file """
    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes = [('all', '*.xml')]        
        self.fileBrowserTitle ="Save XML file:"
        self.lastDir = "."
        return

    def doit(self, filename):
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        setting=self.vf.flipdockSetting
        if not setting.has_key('ligandFT'):
            msg="Please load a ligand first."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                             buttons=['OK'], default=0, 
                             title='Error')
            useTorTree=d.go()
            return

        if setting.has_key('boxSaved'):
           if not setting['boxSaved']:
               self.vf.setDockingBox(center=setting['box']['center'],
                                     dims=setting['box']['dims'])
               setting['boxSaved']=True
        tree=setting['ligandFT']
        from FlexTree.XMLParser import WriteXML        
        writor = WriteXML()
        writor([tree], filename)
        setting['ligand']=filename
        return 

    def guiCallback(self):
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        if not self.vf.flipdockSetting.has_key('ligandFT'):
            msg="Please load a ligand first."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                             buttons=['OK'], default=0, 
                             title='Error')
            useTorTree=d.go()
            return

        file = self.vf.askFileSave(types=self.fileTypes,
                                   idir=self.lastDir,
                                   title=self.fileBrowserTitle)
        if file != None:
            self.lastDir = os.path.split(file)[0]
            apply( self.doitWrapper, (file, ) )
        return
  

class LoadRecXML(LoadLigXML):
    """ load receptor XML file """
    def doit(self, xmlFileName, **kw):
        """
        """
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        
        tree=_tryLoadXML(xmlFileName)
        if tree is None:
            print "Error in opening receptor XML file"
            return        

        self.vf.flipdockSetting['receptorFT']=tree

        try:
            self.vf.readMolecule(tree.pdbfilename, log=0)
        except:
            print "Error in opening receptor file", tree.pdbfilename
            raise
        
        self.vf.color(tree.root.getAtoms().top.uniq()[0].name,\
                      [(0.0, 1.0, 1.0)], ['lines'], log=0)
        self.vf.flipdockSetting['receptor']=xmlFileName
        self.updateViewer()
        return


class SetupGA(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        from AutoDockFR.Param import Params
        self.param=Params(enableGUI=True)
        self.vars={}

    def onAddCmdToViewer(self):        
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}


    def doit(self, **kw):
        """
        configure the genetic algorithm
        """
        self.vf.flipdockSetting['Genetic Algorithm']=kw


    def buildForm(self):
        # called once to set up form
        specfont = ('Times',14,'bold') #('Helvetical', 12, 'bold')
        ifd = self.ifd = InputFormDescr(title = "Configure Genetic Algorithm")
        #opList=self.param.optList[1:]  ## ignore -h --help
        #for op in opList:
        for i in range(len(self.param.optList)):
            op = self.param.optList[i]
            #print "op:", i, op.dest
            if op.dest == "help": continue
            commonConfig={'name': op.dest,
                          'gridcfg':{'sticky':Tkinter.W, 'columnspan':2,
                                     'row':-1, 'column':2,},
                          }

            if hasattr(op, 'widgetDescr'):                    
                ifd.append( {'name': op.dest+"_label",
                             'widgetType':Tkinter.Label,
                             'wcfg':{'text':op.help, 
                                     'font':specfont, 
                                     },
                             'gridcfg':{'sticky':Tkinter.W,
                                        'columnspan':2}}
                            )

                if type(op.widgetDescr) is types.ListType:
                    self.vars[op.dest]=Tkinter.StringVar()
                    self.vars[op.dest].set(op.default)
                    for descr in op.widgetDescr:
                        d={'name': op.dest}
                        descr['wcfg'].update({'variable':self.vars[op.dest]})
                        d.update(descr)
                        ifd.append(d)
                else:
                    #self.vars[op.dest]=Tkinter.StringVar()
                    #self.vars[op.dest].set(op.default)
                    d=commonConfig.copy()
                    d.update(op.widgetDescr)
                    ifd.append(d)
                    
        ifd.append({'widgetType': Tkinter.Button,
                    'text':'save the parameters',
                    'wcfg':{'bd':6},
                    'gridcfg':{'sticky':'we'},
                    'command':self.saveCurrentSetting} )
        
        self.form = self.vf.getUserInput(self.ifd, scrolledFrame=1,
                                         width=800, height=400, modal=0,
                                         blocking=0)
        return
        

    def guiCallback(self):
        if not hasattr(self, 'form'):
            self.buildForm()
        else:
            self.form.deiconify()
        

    def saveCurrentSetting(self):
        setting={}
        tmpDict=self.ifd.entryByName

        for op in self.param.optList[1:]:
            if op.type=='float' or op.type=='int':
                setting[op.dest]=tmpDict[op.dest]['widget'].get()
            elif op.type=='choice':
                value=self.vars[op.dest].get()
                try:
                    value=eval(value)
                except:
                    pass
                setting[op.dest]=value
        apply( self.doitWrapper, ( ), setting ) 
        return 
            


class SetupAutoDockFR(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        self.lastDir = "."
        from AutoDockFR.Param import Params
        self.param=Params()
        self.vars={}
        for op in self.param.optList[1:]:
            self.vars[op.dest]=Tkinter.StringVar()
            self.vars[op.dest].set(op.default)
            
        self.scoringFunc=''
        self.searching=''
        self.mapping={'GA':"Genetic Algorithm",
                      'DACGA':'divide-and-conquer GA'}
        
        return

        
        
    def onAddCmdToViewer(self):        
        if not hasattr(self.vf, 'flipdockSetting'):
            self.vf.flipdockSetting={}
        setting=self.vf.flipdockSetting
        for op in self.param.optList[1:]:
            if not setting.has_key(op.dest):
                setting[op.dest]=op.default

    def doit(self, filename, scoringfunction, searching, **kw):
        """
        save the setting in a python-style file
        """
        setting=self.vf.flipdockSetting
        assert searching in self.mapping.keys()
        name=self.mapping[searching]
        if not setting.has_key(name):
            d = SimpleDialog(self.vf.GUI.ROOT,
                             text="please set the parameters for %s"%name, 
                             buttons=['OK'], default=0, 
                             title='Error')
            res=d.go()
            return
        else:
            GAsetting=self.vf.flipdockSetting[name]
        
        ligand=setting['ligand']
        receptor=setting['receptor']
        scoringFunc=scoringfunction  #setting['scoringFunction']
        search= searching #setting['search']
        f=open(filename, 'w')
        f.write("# AutoDockFR configuration file\n")
        f.write("LigandXML = "+ligand+"\n")
        f.write("ReceptorXML = "+receptor+"\n")
        f.write("scoringFunction = " + scoringFunc+"\n")
        f.write("search = " + search+"\n")
        f.write("\n\n")
        f.write("# %s parameters \n"%(name))

        for k,v in GAsetting.items():
            f.write("%s = %s\n" %(k,v))
        f.close()
        return
        

        

    #def buildForm(self):
    def buildFormDescr(self, formName):
        if formName=='Options':
##             opList=self.param.optList[1:]  ## ignore -h --help
##             for op in opList:
##                 commonConfig={'name': op.dest,
##                               'gridcfg':{'sticky':Tkinter.W, 'columnspan':2,
##                                          'row':-1, 'column':2,},
##                               }
##                 if hasattr(op, 'widgetDescr'):                    
##                     ifd.append( {'name': op.dest+"_label",
##                                  'widgetType':Tkinter.Label,
##                                  'wcfg':{'text':op.help, 
##                                          'font':specfont, 
##                                          },
##                                  'gridcfg':{'sticky':Tkinter.W,
##                                             'columnspan':2}}
##                                 )
##                     if type(op.widgetDescr) is types.ListType:
##                         self.vars[op.dest]=Tkinter.StringVar()
##                         self.vars[op.dest].set(op.default)
##                         for descr in op.widgetDescr:
##                             d={'name': op.dest}
##                             descr['wcfg'].update(\
##                                 {'variable':self.vars[op.dest]})
##                             d.update(descr)
##                             ifd.append(d)
##                     else:
##                         d=commonConfig.copy()
##                         d.update(op.widgetDescr)
##                         ifd.append(d)

            
            # called once to set up form        
            specfont = ('Times',14,'bold')            
            ifd =self.ifd=InputFormDescr(title = "Setup AutoDockFR Calculation")
            ifd.append({'name': 'loadLigand',
                        'widgetType': Tkinter.Button,
                        'tooltip':'Load a ligand from XML file',
                        'text':'Load ligand',
                        'gridcfg':{'sticky':'w','columnspan':1},
                        'command':self.loadLig_cb})
            ifd.append({'name': 'ligand_label',
                        'widgetType':Tkinter.Label,
                        'text':'XML file for ligand:',
                        'textvariable':self.vars['LigandXML'],
                        'gridcfg':{'sticky':'w', 'columnspan':3}})
             
            ifd.append({'name': 'loadReceptor',
                        'widgetType': Tkinter.Button,
                        'tooltip':'Load a receptor from XML file',
                        'text':'Load receptor',
                        'gridcfg':{'sticky':'w','columnspan':1},
                        'command':self.loadRec_cb})
            ifd.append({'name': 'receptor_label',
                        'widgetType':Tkinter.Label,
                        'text':'XML file for receptor:',
                        'textvariable':self.vars['ReceptorXML'],
                        'gridcfg':{'sticky':'w', 'columnspan':3}})
                
            ### scoring function
            op=self.param.getOptByName('scoringFunction')
            assert op != None
            self.scoringFunc=op.default
            ifd.append({'name':'scoringFunction',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'label_text':'scoring function:',
                                'entryfield_value':op.default,
                                'labelpos':'w',
                                'listheight':'80',
                                'scrolledlist_items': op.choices,
                                'selectioncommand':self.choose_sf,
                                },
                        'textvariable':self.vars['scoringFunction'],
                        'gridcfg':{'sticky':Tkinter.W,
                                   'columnspan':2}})
            # Search Methonds
            op=self.param.getOptByName('search')
            assert op != None
            self.searching=op.default
            ifd.append({'name':'search',
                        'widgetType':Pmw.ComboBox,
                        'wcfg':{'label_text':'searching method:',
                                'entryfield_value':op.default,
                                'labelpos':'w',
                                'listheight':'80',
                                'scrolledlist_items': op.choices,
                                'selectioncommand':self.choose_search,
                                },
                        'gridcfg':{'sticky':Tkinter.W,
                                   'columnspan':2}})
            # Search Methonds
##             #searchMethonds=['Genetic Algorithm', "divide and conquer GA"]
##             ifd.append({'widgetType':Pmw.ComboBox,
##                         'name':'search',
##                         'wcfg':{'label_text':'searching method:',
##                                 'entryfield_value':searchMethonds[0],
##                                 'labelpos':'w',
##                                 'listheight':'80',
##                                 'scrolledlist_items': searchMethonds,
##                                 },
##                         'gridcfg':{'sticky':Tkinter.W,
##                                    'columnspan':2},
##                         })
            ifd.append({'name': 'save',
                        'widgetType': Tkinter.Button,
                        'tooltip':'save the docking parameters in a file',
                        'text':'save the AutoDockFR configuration as file',
                        #'wcfg':{'bd':4},
                        'gridcfg':{'sticky':'w','columnspan':2},
                        'command':self.save_cb})
            return ifd
    

    def guiCallback(self):
        self.updateValues()
        val = self.showForm('Options', blocking=0, modal=0)
        ifd=self.ifd
        ctr=ifd.entryByName['search']['widget']
        ent = ctr.component('entryfield')
        ifd.ent = ent._entryFieldEntry


    def updateValues(self):
        setting= self.vf.flipdockSetting
        if not setting.has_key('ligand'):
            self.vars['LigandXML'].set('XML file for ligand:' )
        else:
            self.vars['LigandXML'].set('XML file for ligand: '+setting['ligand'])
        if not setting.has_key('receptor'):
            self.vars['ReceptorXML'].set('XML file for receptor: not loaded ')
        else:           
            self.vars['ReceptorXML'].set('XML file for receptor:'+setting['receptor'])

        return
    
    def choose_sf(self, choice):
        #self.vf.flipdockSetting['scoringFunction']=choice
        #print choice
        self.scoringFunc=choice
        return

    def choose_search(self, choice):
        #self.vf.flipdockSetting['search']=choice
        #print choice
        self.searching=choice
        return
        
    
    def save_cb(self, event=None):
        setting=self.vf.flipdockSetting
        if not setting.has_key('ligand'):
            d = SimpleDialog(self.vf.GUI.ROOT,
                             text="please load a ligand", 
                             buttons=['OK'], default=0, 
                             title='Error')
            res=d.go()
            return
        elif not setting.has_key('receptor'):
            d = SimpleDialog(self.vf.GUI.ROOT,
                             text="please load a receptor", 
                             buttons=['OK'], default=0, 
                             title='Error')
            res=d.go()
            return

        self.updateValues()
        file = self.vf.askFileSave(idir=self.lastDir,
                                   title="Save the AutoDockFR Configuration")
        if file != None:
            self.lastDir = os.path.split(file)[0]
            apply( self.doitWrapper, (file,self.scoringFunc,self.searching) )
            
        return

    def loadRec_cb(self, event=None):
        file = self.vf.askFileOpen(types=[('all', '*.xml')],
                                   idir=self.lastDir,
                                   title="Load receptor in XML format")
        if file != None:            
            self.lastDir = os.path.split(file)[0]
            self.vf.loadReceptorXML(file)
            self.updateValues()
        return

    def loadLig_cb(self, event=None):
        file = self.vf.askFileOpen(types= [('all', '*.xml')] ,
                                   idir=self.lastDir,
                                   title="Load ligand in XML format")
        if file != None:            
            self.lastDir = os.path.split(file)[0]
            self.vf.loadLigandXML(file)
            self.updateValues()
        return

########
class NotAvailableYet(MVCommand):
    def guiCallback(self):
        msg="Under construcntion"
        d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                         buttons=['OK'], default=0, 
                         title='Attention')
        res=d.go()
        return



########

class LoadDockingLog(MVCommand):
    """ View the docking results saved in a log file.
    Log file name can be specified in the docking
    parameter file(log_file='fileName') """

    def __init__(self):
        MVCommand.__init__(self)
        self.fileTypes = [('all', '*')]        
        self.fileBrowserTitle ="Read AutoDockFR log file:"
        self.lastDir = "."
        self.data=[]
        self.setting={}

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"

        if not hasattr(self.vf, 'dockingResult'):
            self.vf.dockingResult=None
        

    def _validate(self, setting):

        mustHaveKeys=['ReceptorXML','LigandXML' ]
        keys=setting.keys()
        for k in mustHaveKeys:
            if k not in keys:
                msg="setting for %s not found in logfile"%(k,)
                d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                                 buttons=['OK'], default=0, 
                                 title='Error')
                err=d.go()
                return False
        return True


    def doit(self, logFileName, GUI=False, **kw):
        """
        
        """
        #oldcursor = self.vf.GUI.setCursor('watch')
        self.data = getResultsFromLogFile(logFileName)
        setting = getSettingsFromLog(logFileName)
        if setting==None and self.data==None: # when error in loading file
            return
        if not self._validate(setting):
            return       
        
        self.setting=setting
        
        dockingResult={}
        dockingResult['filename']=logFileName
        dockingResult['data']=self.data
        dockingResult['setting']=self.setting
        dockingResult['resultNum']=len(self.data)

        R_tree=_tryLoadXML(self.setting['ReceptorXML'], logFileName)
        if R_tree is None:
            print "Error in opening receptor XML file:",\
                  self.setting['ReceptorXML']
            return
        else:
            print "FlexTree in ", self.setting['ReceptorXML'], "is loaded"

        L_tree=_tryLoadXML(self.setting['LigandXML'], logFileName )
        if R_tree is None:
            print "Error in opening ligand XML file:",\
                  self.setting['LigandXML']
            return
        else:
            print "FlexTree in ", self.setting['LigandXML'], "is loaded"


        MOL_found=True
        try:
            recMol=self.vf.readMolecule(R_tree.pdbfilename, log=0)[0]
        except:
            print "Error in opening receptor PDBQS file:",\
                  R_tree.pdbfilename
            MOL_found=False
        try:
            ligMol=self.vf.readMolecule(L_tree.pdbfilename, log=0)[0]
        except:
            print "Error in opening ligand PDBQ file:",\
                  L_tree.pdbfilename
            MOL_found=False

        if MOL_found:
            #oldcursor = self.vf.GUI.setCursor('watch')
            dockingResult['receptor']=recMol
            dockingResult['ligand']=ligMol
            self.vf.foo=L_tree.root.motion.motionList[0]
            ## fixme : what about same score from different genes
            receptorCoords, ligandCoords, scores=getCoordsAndScores(R_tree, L_tree, self.data,self.setting['calcLigIE'],self.setting['calcRecIE'] )
            dockingResult['receptorCoords']=receptorCoords
            dockingResult['ligandCoords']=ligandCoords
            dockingResult['scores']=scores
            dockingResult['RMSDs']=self._getRMSD(ligandCoords,\
                                        orig=ligMol.parser.filename)
        else:
            pass

        # display docking box
        assert isinstance(L_tree.root.motion, FTMotionCombiner)
        motions=L_tree.root.motion.motionList
        boxDim=motions[1].boxDim   # the box_translation motion
        center=motions[2].point2   # the translation motion
        from DejaVu.Box import Box
        vi=self.vf.GUI.VIEWER                
        bb=Box(name="DockingBox", center=center,
               xside=boxDim[0],
               yside=boxDim[1], zside=boxDim[2])
        vi.AddObject(bb)
        vi.Redraw()

        self.vf.colorByMolecules(self.vf.Mols, ['lines'], log=0)
        self.vf.dockingResult=dockingResult
        self.vf.Rec_tree=R_tree
        self.vf.Lig_tree=L_tree
        self.vf.currentShowingResult = -1 # the index of currently shown result
        self._sortAtoms(ligMol)
        self._sortAtoms(recMol)

        #self.vf.GUI.setCursor(oldcursor)
        ## continue to view results?
        if GUI:
            msg="Continue to view the logfile %s ?"%(
                logFileName)
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg,
                             buttons=["Yes","No"],
                             default=0, title="View the log file?")
            ok=d.go()
            if ok==0: #answer was yes
                self.vf.viewDockingLog(index=0, GUI=True, log=0)

        return True


    def _getRMSD(self, ligConfList, orig=None):
        from AutoDockFR.utils import getRMSD
        return getRMSD(self.setting, ligConfList, orig=orig)
        
        
    def _sortAtoms(self, mol):
        """ helper function to set the line geom in order of sorted atoms
        Do this because:
        1) all the ligand/receptor coords are gathered after atoms.sort()
        2) however the molecule read from PDB are not necessory sorted .
        """
        ## clone of Pmv/displayCommands.py  DisplayLines doit()
        
        ggeoms = mol.geomContainer.geoms
        gatoms = mol.geomContainer.atoms
        set = gatoms['bonded']
        set.sort()  ## SORT atoms here
        setnobnds = gatoms['nobnds']
        bonds, atnobnd = set.bonds
        indices = map(lambda x: (x.atom1._bndIndex_,
                                 x.atom2._bndIndex_), bonds)
        if len(indices)==0:
            ggeoms['bonded'].Set(visible=0, tagModified=False)
        else:
            colors = mol.geomContainer.getGeomColor('bonded')
            ggeoms['bonded'].Set( vertices=set.coords,
                                  faces=indices,#lineWidth=lineWidth,
                                  materials=colors, visible=1,
                                  tagModified=False)



    def __call__(self, logFileName, GUI=False, **kw):
        """
        command line version, call the doit
        """
        if GUI:
            res=apply ( self.doitWrapper, (logFileName,GUI), kw)
##             if res:
##                 msg="Continue to view the logfile %s ?"%(
##                     logFileName)
##                 d = SimpleDialog(self.vf.GUI.ROOT, text=msg,
##                                  buttons=["Yes","No"],
##                                  default=0, title="View the log file?")
##                 ok=d.go()
##                 if ok==0: #answer was yes
##                     self.vf.viewDockingLog(index=0, GUI=True, log=0)
        else:
            return apply ( self.doitWrapper, (logFileName,), kw)
        
       
    def guiCallback(self, event=None, *args, **kw):
        cmdmenuEntry = self.GUI.menu[4]['label']
        file = self.vf.askFileOpen(types=self.fileTypes,
                                   idir=self.lastDir,
                                   title=self.fileBrowserTitle)
        if file != None:
            self.lastDir = os.path.split(file)[0]
            mol = self.vf.tryto(self.doitWrapper, file, GUI=True )

        return file



class ViewDockingLog(MVCommand):
    """ View the docking results saved in log file """

    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}
        self.guiUp = 0
        self.form = None
        self.printRMSD=None
        self.printScore=None
        self._lock=False

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'dockingResult'):
            self.vf.dockingResult=None
        return
        

    def doit(self, index, showLigandRMSD=True, showScore=True, **kw):
        """
        
        """
        if self._lock:
            print "Please wait till the current update is done\n"
            return
        
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return

        if index ==0:            
            self.vf.showPDBConformation()
            return

        #oldcursor = self.vf.GUI.setCursor('watch')
        # the index of conformation is zero-based
        index=index-1          
        dockingResult = self.vf.dockingResult
        receptorCoords= dockingResult['receptorCoords'][index]
        ligandCoords  = dockingResult['ligandCoords'][index]
        score         = dockingResult['scores'][index]
        
        if showLigandRMSD:
            rmsd = dockingResult['RMSDs'][index]
            if showScore:
                print "Result # %d: score = %f, ligand RMSD = %f \n" \
                      %( index+1, score, rmsd)
            else:
                print "Result # %d: ligand RMSD = %f \n" \
                      %( index+1, rmsd)
        
        elif showScore:
            print "Result # %d: score = %f \n" %( index+1, score)
            
        recMol=dockingResult['receptor']
        ligMol=dockingResult['ligand']

##         # the next 5 lines updates only the line geometry.
##         ggeoms=recMol.geomContainer.geoms
##         ggeoms['bonded'].Set(vertices = receptorCoords)
##         ggeoms=ligMol.geomContainer.geoms
##         ggeoms['bonded'].Set(vertices = ligandCoords)        
##         ligMol.geomContainer.masterGeom.viewer.Redraw()
        
        self.vf.currentShowingResult=index

        # the following code updates all the geoms by ModificationEvent
        vi = self.vf.GUI.VIEWER
        vi.stopAutoRedraw()
        self._lock=True

        tmp=recMol.allAtoms
        tmp.sort()
        if tmp[0].conformation ==0 and len(tmp[0]._coords)==1:
            tmp.addConformation(receptorCoords)
        else:
            tmp.updateCoords(receptorCoords, 1)
        tmp.setConformation(1)
        modEvent_R = EditAtomsEvent('coords', tmp)
        self.vf.dispatchEvent(modEvent_R)

        tmp=ligMol.allAtoms
        tmp.sort()
        if tmp[0].conformation ==0 and len(tmp[0]._coords)==1:
            tmp.addConformation(ligandCoords)
        else:
            tmp.updateCoords(ligandCoords, 1)
        tmp.setConformation(1)

        modEvent_L = EditAtomsEvent('coords', tmp)
        self.vf.dispatchEvent(modEvent_L)
        
        vi.OneRedraw()
        vi.startAutoRedraw()
        self._lock=False
        
        #self.vf.GUI.setCursor(oldcursor)
        return
        

    def __call__(self,index,showLigandRMSD=True,showScore=True,GUI=False,**kw):
        """
        command line version, call doit()
        """
        if GUI:
            self.displayForm()            
        else:
            return apply ( self.doitWrapper, (index,showLigandRMSD,showScore)
                           , kw)
       
    def guiCallback(self):
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return

        self.displayForm()
        

    def displayForm(self):
        self.printRMSD=Tkinter.IntVar()
        self.printScore=Tkinter.IntVar()
        
        resultNum=self.vf.dockingResult['resultNum']
        filename=self.vf.dockingResult['filename']
        self.ifd=ifd=InputFormDescr(title = 'Docking Result in '+ filename)


        ifd.append({'name':'index',
                    'widgetType':ThumbWheel,
                    'tooltip':'Left Arrow: previous\nRight Arrow: next\nUp Arrow: first (original PDB structure)\nDown Arrow: last\n',
                    'wcfg':{ 'labCfg':{'text':
                          'Docking Result #:\n0: Original Conformation', 
                                       'font':('Helvetica',12,'bold')},
                             'showLabel':1, 'width':100,
                             'min':0, 'max':resultNum,
                             'type':int, 'precision':1,
                             'immediate':1,
                             'value':0,'continuous':1,
                             'callback':self.setIndex_cb, 
                             'oneTurn':10, 'wheelPad':2, 'height':30},
                    'gridcfg':{'sticky':'we'}})
        ifd.append({'name':'printRMSD',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text': 'print ligand RMSD',
                            'variable': self.printRMSD, 
                            },
                    'gridcfg':{'sticky':'w'}})

        ifd.append({'name':'printScore',
                    'widgetType':Tkinter.Checkbutton,
                    'wcfg':{'text': 'print score',
                            'variable': self.printScore, 
                            },
                    'gridcfg':{'sticky':'w'}})


        self.form = self.vf.getUserInput(self.ifd, modal=0, blocking=0)
        self.index = self.ifd.entryByName['index']['widget']
        self.index.canvas.bind('<Enter>', self.Enter_cb)
        self.index.canvas.bind('<KeyPress>', self.keyDown)
        self.index.valueLabel.bind('<Enter>', self.Enter_cb)
        return ifd
        

    def setIndex_cb(self, event=None):
        index = int(self.index.get())
        printScore=self.printScore.get()
        printRMSD=self.printRMSD.get()        
        apply(self.doitWrapper, (index, printRMSD, printScore), )


    def keyDown(self, event):
        ## NOTE: self.index.set will trigger setIndex_cb()
        index = int(self.index.get())
        if event.keysym == "Up":
            self.index.set(0)            
        elif event.keysym == "Down":
            resultNum=self.vf.dockingResult['resultNum']
            self.index.set(resultNum)            
        elif event.keysym == "Right":
            self.index.set(index+1)
        elif event.keysym == "Left":
            self.index.set(index-1)
        else:
            pass # print event.keysym


    def Enter_cb(self, event):
	"""Call back function trigger when the mouse enters the cavas """
        #print 'entering tree'
	self.index.canvas.focus_set()
        #atFocus = self.canvas.focus()

      

class ShowPDBConformation(MVCommand):
    """ show the conformation from PDB file"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}
        self._lock=False
        return
    

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        if not hasattr(self.vf, 'dockingResult'):
            self.vf.dockingResult=None
        return
    
        
    def doit(self, **kw):
        """show the conformation from PDB file """
        if self._lock:
            return
        #oldcursor = self.vf.GUI.setCursor('watch')
        vi = self.vf.GUI.VIEWER
        vi.stopAutoRedraw()
        self._lock=True        
        dockingResult = self.vf.dockingResult
        recMol=dockingResult['receptor']
        ligMol=dockingResult['ligand']

        tmp=recMol.allAtoms
        tmp.setConformation(0)    
        #recMol.allAtoms.updateCoords(receptorCoords)        
        modEvent_R = EditAtomsEvent('coords', tmp)
        self.vf.dispatchEvent(modEvent_R)
        #self.updateGeom(modEvent_R)
        #recMol.geomContainer.updateGeoms(modEvent_R)

        tmp=ligMol.allAtoms
        tmp.setConformation(0)
        #ligMol.allAtoms.updateCoords(ligandCoords)        
        modEvent_L = EditAtomsEvent('coords', tmp)
        self.vf.dispatchEvent(modEvent_L)
        #ligMol.geomContainer.updateGeoms(modEvent_L)
        #self.updateGeom(modEvent_L)

        vi.OneRedraw()
        vi.startAutoRedraw()
        self._lock=False
        
        #self.vf.GUI.setCursor(oldcursor)
        

##         ggeoms=recMol.geomContainer.geoms
##         tmp=recMol.allAtoms
##         tmp.setConformation(0)        
##         ggeoms['bonded'].Set(vertices = tmp.coords)
        
##         ggeoms=ligMol.geomContainer.geoms
##         tmp=ligMol.allAtoms
##         tmp.setConformation(0)        
##         ggeoms['bonded'].Set(vertices = tmp.coords)

##         mGeom = ligMol.geomContainer.masterGeom.viewer.Redraw()
        #print "Now showing the original conformation before docking"
        

    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
        
       
    def guiCallback(self):
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        apply( self.doitWrapper, )  
        
##     def updateGeom(self, event): ## ShowPDBConformation
##         assert isinstance(event, EditAtomsEvent)
##         action='edit'


class ConsolidateLogs(MVCommand):
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}
        self.inputFiles=""
        self.outputFileName="dockLog.txt"

    def onAddCmdToViewer(self):        
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        
    def doit(self, logFiles, outputFileName, **kw):
        """
        
        """
        if logFiles=='':
            return
        from AutoDockFR.utils import consolidateLogs
        msg=consolidateLogs(fileNames=logFiles, outputFileName=outputFileName)
        if len(msg):
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                             buttons=['OK'], default=0, 
                             title='Warning')
            err=d.go()    
        else:
            self.outputFileName=outputFileName
            self.inputFiles=logFiles

    def __call__(self, logFiles, outputFileName, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (logFiles, outputFileName), kw)
        
       
    def guiCallback(self):
        val = self.showForm('Options')
        if val:
            if val.has_key('filename') and val.has_key('logFiles'):
                apply( self.doitWrapper, (val['logFiles'],val['filename'],))
                
                msg="Continue to load the consolidated logfile %s ?"%(
                    self.outputFileName)
                d = SimpleDialog(self.vf.GUI.ROOT, text=msg,
                                 buttons=["Yes","No"],
                                 default=0, title="Load the log file?")
                ok=d.go()
                if ok==0: #answer was yes
                    self.vf.loadDockingLog(self.outputFileName, GUI=True,log=0)

                
    def buildFormDescr(self, formName):
        #from mglutil.util.misc import uniq
        if formName=='Options':
            ifd = InputFormDescr(
                title='Consolidate all log files into a single file')

            ###  define input Directory
            ifd.append({'name':'fileGroup',
                        'widgetType':Pmw.Group,
                        'container':{'fileGroup':"w.interior()"},
                        'wcfg':{},
                        'gridcfg':{'sticky':'wnse', 'columnspan':4}})

            ifd.append({'name':'logFiles',
                        'widgetType':Pmw.EntryField,
                        'parent':'fileGroup',
                        'tooltip':'Enter a directory name',
                        'wcfg':{'label_text':'Log Files:',
                                'labelpos':'w', 'value':self.inputFiles},
                        'gridcfg':{'sticky':'we'},
                        })
            ifd.append({'name':'dirbrowse',
                        'widgetType':Tkinter.Button,
                        'tooltip':'Choose a directory with log files',
                        'wcfg':{'text':'BROWSE',
                                'command':self.chooseDIR_cb},
                        'parent':'fileGroup',
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            ### define output filename
            ifd.append({'name':'filename',
                        'widgetType':Pmw.EntryField,
                        'parent':'fileGroup',
                        'tooltip':'Enter a filename',
                        'wcfg':{'label_text':'Save as file:',
                                'labelpos':'w', 'value':self.outputFileName},
                        'gridcfg':{'sticky':'we'},
                        })
            ifd.append({'widgetType':SaveButton,
                        'name':'filebrowse',
                        'parent':'fileGroup',
                        'tooltip':'Enter a file name',
                        'wcfg':{'buttonType':Tkinter.Button,
                                'title':"Choose output filename",
                                'types':[('all file', '*.*')],
                                'callback':self.setEntry_cb,
                                'widgetwcfg':{'text':'BROWSE'}},
                        'gridcfg':{'row':-1, 'sticky':'we'}})

            
            return ifd
           
    def setEntry_cb(self, filename ):
        ebn = self.cmdForms['Options'].descr.entryByName
        entry = ebn['filename']['widget']
        entry.setentry(filename)

    def chooseDIR_cb(self ):
        #from ViewerFramework.VFGUI import dirChoose
        from mglutil.gui.BasicWidgets.Tk.dirDialog import askdirectory
        dirpath = askdirectory( initialdir='/export/people/yongzhao/dev',
                                title='title')
        if dirpath=='': dirpath = None
        if dirpath:
            ebn = self.cmdForms['Options'].descr.entryByName
            entry = ebn['logFiles']['widget']
            entry.setentry(dirpath)

        
class CloseLogFile(MVCommand):
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
        close the logfile and cleaning up
        """
        dockingResult=self.vf.dockingResult
        ligMol=dockingResult['ligand']
        viewer=ligMol.geomContainer.masterGeom.viewer
        self.vf.deleteMol(dockingResult['receptor'].name, log=0)
        self.vf.deleteMol(ligMol.name, log=0)

        box=viewer.FindObjectByName('root|DockingBox')
        viewer.RemoveObject(box)
        viewer.Redraw()
        self.vf.dockingResult=None

        # close the "view docking result" dialog, if any
        viewResultForm=self.vf.viewDockingLog.form
        if viewResultForm:
            if viewResultForm.f.winfo_ismapped():
                viewResultForm.Cancel_cb()
                

    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
        
       
    def guiCallback(self):
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        apply( self.doitWrapper, )  
        



class SaveLigand(MVCommand):
    """ cleaning up FlexTree related"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        return

    
    def doit(self, **kw):
        """
        """        
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        assert self.vf.dockingResult.has_key("ligand")
        ligand=self.vf.dockingResult["ligand"]
        if not hasattr(self,'mol'):
            self.mol=Read(ligand.parser.filename)[0]

        #mol=self.vf.dockingResult["ligand"]
        index=self.vf.currentShowingResult
        name=self.mol.name + "_%d.pdb"%index
        dockingResult = self.vf.dockingResult
        ligandCoords  = dockingResult['ligandCoords'][index]
        nodes=self.mol.allAtoms
        nodes.sort()
        nodes.updateCoords(ligandCoords, 0)
        print 'foo',nodes[0].conformation
        self.vf.writePDB(nodes,filename= name, pdbRec=['ATOM', 'HETATM'],\
                         log=0)
        return


    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
        
       
    def guiCallback(self):
        apply( self.doitWrapper, ( ),  )  




class SaveReceptor(MVCommand):
    """ cleaning up FlexTree related"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        return
        
    def doit(self, **kw):
        """
        """
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        assert self.vf.dockingResult.has_key("receptor")
        receptor=self.vf.dockingResult["receptor"]
        if not hasattr(self,'mol'):
            self.mol=Read(receptor.parser.filename)[0]

        index=self.vf.currentShowingResult
        name=self.mol.name + "_%d.pdb"%index
        dockingResult = self.vf.dockingResult
        receptorCoords  = dockingResult['receptorCoords'][index]
        nodes=self.mol.allAtoms
        nodes.updateCoords(receptorCoords) 
        self.vf.writePDB(nodes,filename= name, pdbRec=['ATOM', 'HETATM'],\
                         log=0)
        return


    def __call__(self, **kw):
        """
        command line version, call doit()
        """
        return apply ( self.doitWrapper, (), kw)
          

    def guiCallback(self):
        apply( self.doitWrapper, (),  )  




class testDocking(MVCommand):
    """ cleaning up FlexTree related"""
    def __init__(self):
        MVCommand.__init__(self)
        self.setting={}
        reader = ReadXML()
        self.paramList=[]
        self._locked=False
        self.updateInRealTime=Tkinter.IntVar()

    def onAddCmdToViewer(self):
        if not foundFlexTree:
            print "Warning: FlexTree package not found"
        return
        

    def __call__(self, paramList=None,**kw):
        """
        command line version, call doit()
        """
        #if self.vf.Rec_tree is None or self.vf.Lig_tree is None:
        #    return        
        #self.vf.Lig_tree=self.tree
        if paramList is None:
            val=self.showForm('parameterForm', blocking=0, modal=0)
        else:
            return apply ( self.doitWrapper, (paramList,), kw)
          
       
    def buildFormDescr(self, formName):
        if formName == 'parameterForm':
            if self.vf.Rec_tree == None or self.vf.Lig_tree ==None:
                return
            
            self.ifd=InputFormDescr(title = 'Test Docking')
            # the following checkbutton is commented out since there is no code
            # to update geoms in real time ...
            #self.ifd.append({'name':'printRMSD',
            #                 'widgetType':Tkinter.Checkbutton,
            #                 'wcfg':{'text':
            #                         'update line geometries in real time',
            #                         'variable': self.updateInRealTime, 
            #                         },
            #                 'gridcfg':{'sticky':'w'}})
            self.ifd.append({'widgetType': Tkinter.Button,
                             'text':'reset values',
                             'wcfg':{'bd':6},
                             'gridcfg':{'sticky':'we'},
                             'command':self.resetValues_cb} )            

            self.counter=0
            self.paramNameList=[]
            
            # first result in log file
            self.data=self.vf.dockingResult['data'][0]
            
            tree= self.vf.Rec_tree
            self._my_buildFormDescr(tree)
            tree= self.vf.Lig_tree
            self._my_buildFormDescr(tree)
            self.counter=0
            self.ifd.append({'widgetType': Tkinter.Button,
                             'text':'compute score',
                             'wcfg':{'bd':6},
                             'gridcfg':{'sticky':'we'},
                             'command':self.getCurrentScore_cb} )
            return self.ifd
        else:
            return None


    def _my_buildFormDescr(self, tree):
        allMotions=tree.getAllMotion()
        ifd=self.ifd
        for i in range(len(allMotions)):
            motion=allMotions[i]
            if isinstance(motion, FTMotionCombiner):                
                # not modifiable.
                names=[]
                param=[]
                for m in motion.motionList:
                    if  m.can_be_modified:                            
                        n,p=m.getParam()
                        names.extend(n)
                        param.extend(p)                            
            else:
                names,param=motion.getParam()

            ftNodeName=motion.node().name
            ## NOTE: all motion parameters are <float> type !
            for j in range(len(param)):
                mini=param[j]['min']
                maxi=param[j]['max']
                paramName='param_%d'%self.counter
                self.paramNameList.append(paramName)
                ifd.append({'name':paramName,
                            'widgetType':ThumbWheel,
                            'wcfg':{ 'labCfg':{'text':ftNodeName+" :" +
                                               names[j],
                                               'font':('Helvetica',12,
                                                       'bold')},
                                     'showLabel':1, 'width':100,
                                     'min':mini, 'max':maxi,
                                     'type':float, 'precision':4,
                                     'immediate':1, #??
                                     'value':self.data[self.counter],
                                     #'variable':tempVar,
                                     'continuous':True,
                                     'callback':self.update_cb,
                                     'oneTurn':0.1, 'wheelPad':2,
                                     'height':20},
                            'gridcfg':{'sticky':'we'}})

                self.counter +=1
        return
        
    def update_cb(self, event=None):
        if self._locked :            
            return
        if not self.updateInRealTime.get():
            return
        #self._locked=True        
        #paramList=self._getParams()
        #self.updateLineGeoms(paramList)  # This method is not implemented (!)
        #self._locked=False
        #return

    def _getParams(self):
        """ returns all the parameters (current values of ThumbWheel) """
        paramList=[]
        for item in self.ifd:
            if isinstance (item['widget'] , ThumbWheel):
                paramList.append(item['widget'].value)
        return paramList


    def guiCallback(self):
        if self.vf.dockingResult is None:
            msg="Log file not loaded."
            d = SimpleDialog(self.vf.GUI.ROOT, text=msg, 
                buttons=['OK'], default=0, 
                title='Error')
            useTorTree=d.go()
            return
        
        val = self.showForm('parameterForm', blocking=0, modal=0)
        if not val:
            return
        return


    def doit(self, geneList):
        if self._locked:
            return
        self._locked=True
        
        if not hasattr(self, "genome"):
            R_tree=self.vf.Rec_tree
            L_tree=self.vf.Lig_tree
            if not hasattr(self, "scoreObject"):
                dockingResult=self.vf.dockingResult
                setting=dockingResult['setting']
                calcLigandIE=setting['calcLigIE']
                calcReceptorIE=setting['calcRecIE']
                R_tree=self.vf.Rec_tree
                R_root=R_tree.root
                L_tree=self.vf.Lig_tree
                L_root=L_tree.root
                rec = R_root.getAtoms()[:]
                lig = L_root.getAtoms()[:]
                self.scoreObject = AD42ScoreC(rec, lig,
                                               calcLigIE=calcLigandIE, \
                                               calcRecIE=calcReceptorIE,
                                               receptorFT=R_tree)
            from AutoDockFR.FTGA import FTtreeGaRepr
            self.genome= FTtreeGaRepr(R_tree, L_tree, self.scoreObject)
            
        gnm=self.genome
        R_coords, L_coords=gnm.toPhenotype(geneList, sort=True)
        dockingResult=self.vf.dockingResult
        setting=dockingResult['setting']
        recMol=dockingResult['receptor']
        ligMol=dockingResult['ligand']

        # update receptor coords
        tmp=recMol.allAtoms
        print 
        if len(tmp[0]._coords)==1:
            tmp.addConformation(R_coords)            
        else:
            tmp.updateCoords(R_coords, 1)
        modEvent_R = EditAtomsEvent('coords', tmp)
        self.vf.dispatchEvent(modEvent_R)
        
        # update ligand coords
        tmp=ligMol.allAtoms
        if len(tmp[0]._coords)==1:
            tmp.addConformation(L_coords)
        else:
            tmp.updateCoords(L_coords, 1)
        modEvent_L = EditAtomsEvent('coords', tmp)
        self.vf.dispatchEvent(modEvent_L)

        gnm=self.genome
        score= 0.0 - self.scoreObject.score(gnm, geneList)
        print "this score =",score
        self._locked=False
        return score
        

    def getCurrentScore_cb(self, event=None):
        """ return score of current set of parameters."""
        geneList=self._getParams()
        self.doit(geneList)
        return
    
##     def computeScore(self, genomeValues):
##         geneList=genomeValues        
##         self.updateLineGeoms(geneList) # update line Geom first

##         dockingResult=self.vf.dockingResult
##         setting=dockingResult['setting']
##         calcLigandIE=setting['calcLigIE']
##         calcReceptorIE=setting['calcRecIE']
##         R_tree=self.vf.Rec_tree
##         R_root=R_tree.root
##         L_tree=self.vf.Lig_tree
##         L_root=L_tree.root        
##         recAtms = R_root.getAtoms()[:]
##         ligAtms = L_root.getAtoms()[:]

##         if not hasattr(self, "scoreObject"):
##             rec=recAtms[:]
##             lig=ligAtms[:]
##             self.scoreObject = AD305ScoreC(rec, lig, calcLigIE=calcLigandIE, \
##                                            calcRecIE=calcReceptorIE,
##                                            receptorFT=R_root.tree())
##         scoreObject=self.scoreObject
##         gnm=self.genome
##         score= 0.0 - scoreObject.score(gnm, geneList)
##         print "score =",score
##         self._locked=False
##         return  score


##     def updateLines_cb(self, event=None):
##         """ update line geometries in viewer"""        
##         if self._locked:
##             return
##         self._locked=True
##         geneList=self._getParams()
##         self.updateLineGeoms(geneList) # update line Geom first
##         self._locked=False
##         return


    def resetValues_cb(self, event=None):
        """ update line geometries in viewer"""        
        if self._locked:
            return
        self._locked=True
        paramList=[]
        counter=0
        for item in self.ifd:
            widget=item['widget'] 
            if isinstance (widget, ThumbWheel):
                widget.setValue(self.data[counter])
                counter +=1
        paramList=self._getParams()

        self.doit(paramList)
        #self.updateLineGeoms(paramList)
        self._locked=False
        return
        
######## GUI (includes menu, commandList. etc. ) ##########
from Pmv.mvCommand import MVCommand, MVCommandGUI
#AutoDockFRCommandGUI = MVCommandGUI()
#msg = 'show/hide AutoDockFR GUI'
#from mglutil.util.packageFilePath import findFilePath
#path = findFilePath('Icons', 'Pmv')

#AutoDockFRCommandGUI.addToolBar('flipdock', icon_dir=path,
 #                             icon1='adt.png', balloonhelp=msg,
 #                             index=15)

## setup AutoDockFR
loadLigXMLGUI = CommandGUI()
loadLigXMLGUI.addMenuCommand('AutoDockFRBar', 'Ligand', 'Load from XML File')

loadLigPDBQGUI = CommandGUI()
loadLigPDBQGUI.addMenuCommand('AutoDockFRBar', 'Ligand', 'Load from PDBQ File')

saveLigandXMLGUI = CommandGUI()
saveLigandXMLGUI.addMenuCommand('AutoDockFRBar', 'Ligand', 'Save the ligand as XML')

loadRecXMLGUI = CommandGUI()
loadRecXMLGUI.addMenuCommand('AutoDockFRBar', 'Receptor', 'Load from XML File')
setDockingBoxGUI = CommandGUI()
setDockingBoxGUI.addMenuCommand('AutoDockFRBar','Receptor','Set the docking box')

setupGAGUI = CommandGUI()
setupGAGUI.addMenuCommand('AutoDockFRBar', 'Searching', 'Genetic Algorithm')

setupGA_DAC_GUI = CommandGUI()
setupGA_DAC_GUI.addMenuCommand('AutoDockFRBar', 'Searching', 'Divide and Conquer GA')

setupPSO_GUI = CommandGUI()
setupPSO_GUI.addMenuCommand('AutoDockFRBar', 'Searching', 'Partical Swamp Optimization')

setupAutoDockFR_GUI = CommandGUI()
setupAutoDockFR_GUI.addMenuCommand('AutoDockFRBar', 'Docking', 'Setup')

runAutoDockFR_GUI = CommandGUI()
runAutoDockFR_GUI.addMenuCommand('AutoDockFRBar', 'Docking', 'Run')


## setFLIPLigGUI = CommandGUI()
## setFLIPLigGUI.addMenuCommand('AutoDockFRBar', 'Ligand', 'Load from XML File')

 ##  AutoDockFR log related
ConsolidateLogsGUI = CommandGUI()
ConsolidateLogsGUI.addMenuCommand('AutoDockFRBar', 'Log Analysis', 'Consolidate Logs')

LoadDockingLogGUI = CommandGUI()
LoadDockingLogGUI.addMenuCommand('AutoDockFRBar', 'Log Analysis','Load Log file')

ViewDockingLogGUI = CommandGUI()
ViewDockingLogGUI.addMenuCommand('AutoDockFRBar', 'Log Analysis', 'ViewLog')

ShowPDBConf_GUI = CommandGUI()
ShowPDBConf_GUI.addMenuCommand('AutoDockFRBar', 'Log Analysis', 'Show PDB Conformation')

CloseLogFile_GUI = CommandGUI()
CloseLogFile_GUI.addMenuCommand('AutoDockFRBar','Log Analysis','Close Log File')

SaveLigandGUI = CommandGUI()
SaveLigandGUI.addMenuCommand('AutoDockFRBar', 'Log Analysis', 'save ligand',
                             cascadeName="Save current")
SaveReceptorGUI = CommandGUI()
SaveReceptorGUI.addMenuCommand('AutoDockFRBar', 'Log Analysis', 'save receptor',
                               cascadeName="Save current")
TestDockingGUI = CommandGUI()
TestDockingGUI.addMenuCommand('AutoDockFRBar', 'Log Analysis', 'test docking')
msg="test"
#TestDockingGUI.addToolBar('sdfVision', icon1='vision.png', balloonhelp=msg, )
                           

##  ##  essential dynamics related

## LoadEssentialDynamics_GUI = CommandGUI()
## LoadEssentialDynamics_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Load Essential Dynamics', cascadeName="Essential Dynamics")

## BuildFlexTree_ED_GUI = CommandGUI()
## BuildFlexTree_ED_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Add Essential Dynamics to FlexTree', cascadeName="Essential Dynamics")

## AddRotamerToEssentialDynamics_GUI = CommandGUI()
## AddRotamerToEssentialDynamics_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Add Rotamer', cascadeName="Essential Dynamics")

## SaveFlexTree_ED_GUI = CommandGUI()
## SaveFlexTree_ED_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Save FlexTree to XML', cascadeName="Essential Dynamics")

## CloseED_FT_GUI = CommandGUI()
## CloseED_FT_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Close All (FT,ED) ', cascadeName="Essential Dynamics")

## ShowEssentialDynamics_GUI = CommandGUI()
## ShowEssentialDynamics_GUI.addMenuCommand('menuRoot', 'FlexTree', 'Show Essential Dynamics', cascadeName="Essential Dynamics")



## ## loop prediction
## ShowAlternativeLoop = CommandGUI()
## ShowAlternativeLoop.addMenuCommand('menuRoot', 'FlexTree', 'Show Alternative Loops')





## foundMatplotlib = False    
## try:
##     from matplotlib import matlab
##     foundMatplotlib = True
## except:
##     pass

foundMatplotlib=True


commandList = [
    #{'name':'flipdock', 'cmd':FlipDockCommand(), 'gui':AutoDockFRCommandGUI},
    {'name':'loadReceptorXML', 'cmd':LoadRecXML(),
     'gui':loadRecXMLGUI},
    {'name':'setDockingBox', 'cmd':SetDockingBox(),
     'gui':setDockingBoxGUI},

    
    {'name':'loadLigandXML', 'cmd':LoadLigXML(),
     'gui':loadLigXMLGUI},
    {'name':'loadLigandPDBQ', 'cmd':LoadLigPDBQ(), 
     'gui':loadLigPDBQGUI},
    {'name':'saveLigandXML', 'cmd':SaveLigXML(),
     'gui':saveLigandXMLGUI},
    

    {'name':'setupGA', 'cmd':SetupGA(),
     'gui':setupGAGUI},
    {'name':'setupDACGA', 'cmd':NotAvailableYet(),
     'gui':setupGA_DAC_GUI},
    {'name':'setupPSO', 'cmd':NotAvailableYet(),
     'gui':setupPSO_GUI},
#    {'name':'setupAutoDockFR', 'cmd':SetupAutoDockFR(),
#     'gui':setupAutoDockFR_GUI},
    {'name':'runAutoDockFR', 'cmd':NotAvailableYet(),
     'gui':runAutoDockFR_GUI},

    {'name':'loadDockingLog', 'cmd':LoadDockingLog(),
     'gui':LoadDockingLogGUI},
    {'name':'viewDockingLog', 'cmd':ViewDockingLog(),
     'gui':ViewDockingLogGUI},
    {'name':'showPDBConformation', 'cmd':ShowPDBConformation(),
     'gui':ShowPDBConf_GUI},    
    {'name':'closeLogFile', 'cmd':CloseLogFile(),
     'gui':CloseLogFile_GUI},
    {'name':'saveLigand', 'cmd':SaveLigand(),
     'gui':SaveLigandGUI},
    {'name':'saveReceptor', 'cmd':SaveReceptor(),
     'gui':SaveReceptorGUI},
    {'name':'testDock', 'cmd':testDocking(),
     'gui':TestDockingGUI},
]

## if foundMatplotlib:
##     ShowRMSD_SCORE_GUI = CommandGUI()
##     ShowRMSD_SCORE_GUI.addMenuCommand('menuRoot', 'AutoDockFR', 'RMSD vs. Score', cascadeName="AutoDockFR Log")
    
##     commandList.append(
##         {'name':'showRmsd_VS_Score', 'cmd':ShowRmsd_VS_Score(),
##      'gui':ShowRMSD_SCORE_GUI},
##         )

def initModule(vf):
    """ initializes commands """
    bgcolor = "grey70"
    if vf.hasGui:
        if not vf.GUI.menuBars.has_key('AutoDockFRBar'):
            # create menuBar before adding menuCommands: 
            gui = loadRecXMLGUI.menu
            bar = vf.GUI.addMenuBar("AutoDockFRBar", gui[0], gui[1])
            frame = bar._frame
            frame.config( {'background':bgcolor, 'height':24})
            if hasattr(frame, "master"):
                frame.master.config( {'background':bgcolor, 'relief':'flat',
                                      'height':24})
            # add "AutoDockFR" label to the bar
            label = Tkinter.Label(frame, text="AutoDockFR", width=10,
                                  relief='sunken', borderwidth=1, fg='black',
                                  bg = 'ivory', anchor='w' )
            label.pack(side='left')
    # add the commands
    for dict in commandList:
	vf.addCommand(dict['cmd'], dict['name'], dict['gui'])
    if vf.hasGui and vf.GUI.menuBars.has_key('AutoDockFRBar'):
        menuBar = vf.GUI.menuBars['AutoDockFRBar']
        for item in menuBar.menubuttons.values():
            item.configure(background = bgcolor)

