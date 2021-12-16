from mglutil.gui.BasicWidgets.Tk.trees.TreeWithButtons import \
     ColumnDescriptor ,TreeWithButtons, NodeWithButtons
from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from mglutil.util.packageFilePath import getResourceFolderWithVersion
from mglutil.util.callback import CallbackFunction

from MolKit.molecule import MolecularSystem
import Pmw, Tkinter, os, sys, string

from MolKit.stringSelector import CompoundStringSelector
from MolKit.molecule import MoleculeSet, Molecule
from MolKit.listSet import ListSet

from Pmv.moleculeViewer import ICONPATH as iconPath
from Pmv.selectionCommands import MVSelectCommand
from Pmv.seqDisplay import buildLabels
from pyglf import glf


class MolFragTreeWithButtons(TreeWithButtons):
    """Each node in the tree has an object associated in the node's .object
attribute.  The objects are expected to have a .parent and a .children
attribute describing the hierarchy."""

    def enterDivider_cb(self, event):
        TreeWithButtons.enterDivider_cb(self, event)
        self.headerCanvas.config(cursor='sb_h_double_arrow')
    
    def leaveDivider_cb(self, event):
        TreeWithButtons.leaveDivider_cb(self, event)
        self.headerCanvas.config(cursor='')

    def dividePress_cb(self, event):
        TreeWithButtons.dividePress_cb(self, event)
        self.headerCanvas.bind("<Motion>", self.moveDivider_cb)

    def divideRelease_cb(self, event):
        TreeWithButtons.divideRelease_cb(self, event)
        self.headerCanvas.unbind("<Motion>")
        
    def setTreeWidth(self, width):
        width = min(width, self.canvas.winfo_width())
        off = width-self.treeWidth
        TreeWithButtons.setTreeWidth(self, width)
        self.headerCanvas.move(self.dividerCanvasId2, off, 0)
        self.headerCanvas.move('ColHeaders', off, 0)
        self.headerCanvas.move('backgroundStripes', off, 0)

    def enter_cb(self, event=None):
        TreeWithButtons.enter_cb(self, event=None)
        # create a line in header canvas
        self.crosshairTk2 = self.headerCanvas.create_line(
            0,0,0,0, fill='#35A8FF', width=2)

    def leave_cb(self, event=None):
        TreeWithButtons.leave_cb(self, event=None)
        #print 'deleting crosshair2'
        self.headerCanvas.delete(self.crosshairTk2)
        self.crosshairTk2 = None

    def move_cb(self,event):
        TreeWithButtons.move_cb(self,event)
        if self.crosshairTk2 is None:
            return
        x = self.headerCanvas.canvasx(event.x)
        if isinstance(event.widget, Tkinter.Label):
            x = x + event.widget.winfo_x()
        self.headerCanvas.coords( self.crosshairTk2, x, 0, x, 100)


    def setColumnWidth(self, cw):
        self.colWidth = cw
        self.canvas.delete('backgroundStripes')
        self.canvas.delete('ColHeaders')
        self.headerCanvas.delete('backgroundStripes')
        self.headerCanvas.delete( 'ColHeaders')
        for i, col in enumerate(self.columns):
            self.createColHeader(col, i)
            
        self.redraw()


    def createColHeader(self, columnDescr, number):
        cw = self.colWidth
        x = self.treeWidth + (0.5*self.colWidth)
        canvas = self.canvas
        # add column background
        if number%2:
            _id = canvas.create_rectangle(
                x+number*cw-cw/2, 0, x+number*cw+cw/2, 10000,
                tags=('backgroundStripes',), fill='#DDDDDD', outline='#DDDDDD')
            
        canvas = self.headerCanvas
        # add column background
        if number%2:
            _id = canvas.create_rectangle(
                x+number*cw-cw/2, 0, x+number*cw+cw/2, 10000,
                tags=('backgroundStripes',), fill='#DDDDDD', outline='#DDDDDD')

        # add title and icon
        _id = canvas.create_text(
            x+number*cw, 7, text=columnDescr.title, justify='center',
            tags=('ColHeaders',), fill=columnDescr.color, font=self.font)
        cb = CallbackFunction(self.rightButtonClick, columnDescr)
        canvas.tag_bind(_id, "<Button-3>", cb)
        self.colLabIds.append(_id)

        # add column header icons
        if columnDescr.iconfile:
            if columnDescr.icon is None:
                columnDescr.getIcon(columnDescr.iconfile)
            _id = canvas.create_image(
                x+number*cw, 19,tags=('ColHeaders',),
                    image=columnDescr.icon)
        self.colLabIds.append(_id)


    def toggleShowMolColBar(self, event=None):
        #val = self.showMolColBarVar.get()
        #print 'toggleShowMolColBar', val
        self.redraw(force=True)


        
    def __init__(self, master, root, vf=None, iconsManager=None,
                 idleRedraw=True, nodeHeight=18, **kw):
        # add a compound selector entry
        self.vf = vf
        kw['iconsManager'] = iconsManager
        kw['idleRedraw'] = idleRedraw
        kw['nodeHeight'] = nodeHeight
        TreeWithButtons.__init__( *(self, master, root), **kw )

        # add backbone only widget
        self.bbmodevar = Tkinter.StringVar()
        self.bbmodevar.set("CMD")

        self.showMolColBarVar = Tkinter.IntVar()
        self.showMolColBarVar.set(False)

        # master1 is master for selection box
        self.master1 = self.createSelectionBox(master)
        self.master4 = self.createHeaderCanvas(master)
        w = self.treeWidth
        canvas = self.headerCanvas
        id_ = canvas.create_line(w-6, 0, w-6, 100, fill='grey75', width=3)
        self.dividerCanvasId2 = id_
        canvas.tag_bind(id_,"<Enter>", self.enterDivider_cb)
        canvas.tag_bind(id_,"<Leave>", self.leaveDivider_cb)
        canvas.tag_bind(id_,"<Button-1>", self.dividePress_cb)
        canvas.tag_bind(id_,"<ButtonRelease-1>", self.divideRelease_cb)

        self.menus = [] # list of posted menus to cancel if focus is lost

        ##
        ## create buttons at the top fo the dashboard
        ##

        ##
        ## add a button to save selection as a set
        filename = os.path.join(iconPath, 'AddToDashboard.gif')
        self.addSelIcon = ImageTk.PhotoImage(file=filename)
        width = self.addSelIcon.width()
        height = self.addSelIcon.height()
        button = Tkinter.Button(canvas, width=width, height=height,
                                command=self.addSel_cb, image=self.addSelIcon)
        self.addSelButton = canvas.create_window(
            2+width/2.0, 2+height/2.0, window=button, tags=('dashButtons',))
        
        x = width + 4
        #self.addSelButton = canvas.create_image(
        #    width/2.0, height/2.0, image=self.addSelIcon,
        #    tags=('dashButtons',))
        #canvas.tag_bind(self.addSelButton, '<ButtonRelease-1>', self.addSel_cb)

        from Pmv.dashboardCommands import addSetToDashboardmsg
        self.balloon.tagbind(canvas, self.addSelButton, addSetToDashboardmsg)

        ##
        ## add a button to clear the current selection
        def clearSel(event=None):
            self.vf.clearSelection()
            
        filename = os.path.join(iconPath, 'eraser.gif')
        self.clearSelectionIcon = ImageTk.PhotoImage(file=filename)
        width = self.clearSelectionIcon.width()
        #height = self.clearSelectionIcon.height()
        button = Tkinter.Button(
            canvas, width=width, height=height,
            command=clearSel, image=self.clearSelectionIcon)
        self.clearSelectionButton = canvas.create_window(
            x+4+width/2.0, 2+height/2.0, window=button, tags=('dashButtons',))
        #self.clearSelectionButton = canvas.create_image(
        #    x + width/2.0, height/2.0, image=self.clearSelectionIcon,
        #    tags=('dashButtons',))
        x += width + 6
        #canvas.tag_bind(self.clearSelectionButton, '<ButtonRelease-1>',
        #                clearSel)

        from Pmv.dashboardCommands import addSetToDashboardmsg
        self.balloon.tagbind(canvas, self.clearSelectionButton,
                             "Clear current selection")

        ##
        ## add a button with selection level
        filename = os.path.join(iconPath, 'AtomLevel.png')
        self.atomSelectionLevelIcon = ImageTk.PhotoImage(file=filename)
        filename = os.path.join(iconPath, 'ResidueLevel.png')
        self.residueSelectionLevelIcon = ImageTk.PhotoImage(file=filename)
        filename = os.path.join(iconPath, 'ChainLevel.png')
        self.chainSelectionLevelIcon = ImageTk.PhotoImage(file=filename)
        filename = os.path.join(iconPath, 'MoleculeLevel.png')
        self.moleculeSelectionLevelIcon = ImageTk.PhotoImage(file=filename)
        button = Tkinter.Button( canvas, width=20, height=height,
                                 image=self.atomSelectionLevelIcon,
                                 command=self.setLevel_cb)
        self.selLevelButtonWidget = button
        self.setLevelButton = canvas.create_window(
            x+4+width/2.0, 2+height/2.0, window=button, tags=('dashButtons',))

        x += width + 6


        ##
        ## add a button for settings
        filename = os.path.join(iconPath, 'dashboardSetting.png')
        self.dashboardSettingIcon = ImageTk.PhotoImage(file=filename)
        width = self.dashboardSettingIcon.width()
        button = Tkinter.Button(
            canvas, width=width, height=height,
            command=self.settingMenu_cb, image=self.dashboardSettingIcon)
        self.settingButton = canvas.create_window(
            x+4+width/2.0, 2+height/2.0, window=button, tags=('dashButtons',))

        x += width + 6

        ##
        ## add a button to set dashboard natural size
        filename = os.path.join(iconPath, 'autosizeY.gif')
        self.autoWidthIcon = ImageTk.PhotoImage(file=filename)
        #width = self.autoWidthIcon.width()
        #height = self.autoWidthIcon.height()
        #self.autoSizeButton = canvas.create_image(
        #    x + width/2.0, height/2.0, image=self.autoWidthIcon,
        #    tags=('dashButtons',))
        #x += width + 4
        #canvas.tag_bind(self.autoSizeButton, '<ButtonRelease-1>', 
        #                self.vf.dashboard.setNaturalSize)
        #naturalSizeballoon = "Sets the dashboard width to show all columns"
        #self.balloon.tagbind(canvas, self.autoSizeButton,
        #                     naturalSizeballoon)

        ##
        ## add a button to increase column width
        #id_  = self.sizeUpButton = canvas.create_text(
        #    x+12, height/2.0, justify='center', text="Z", font='Arial 20',
        #    tags=('dashButtons',))
        #x += 14
        #canvas.tag_bind(id_, "<ButtonRelease-1>", self.vf.dashboard.
        #                increaseColumnWidth)
        #colWidthUpBalloon = "Increase column width and scale buttons down"
        #self.balloon.tagbind(canvas, id_, colWidthUpBalloon)
        
        ##
        ## add a button to decrease column widtg
        #id_  = self.autoSizeButton = canvas.create_text(
        #    x+18, height/2.0, justify='center', text="Z", font='Arial 12',
        #    tags=('dashButtons',))
        #x += 36
        #canvas.tag_bind(id_, "<ButtonRelease-1>",
        #                self.vf.dashboard.decreaseColumnWidth)
        #colWidthDownBalloon = "Decrease column width and scale buttons down"
        #elf.balloon.tagbind(canvas, id_, colWidthDownBalloon)

        def showHideSequenceViewer(event=None):
            if hasattr(self.vf, 'sequenceViewer'):
                self.vf.sequenceViewer.showHideGUI()
            else:
                self.vf.browseCommands('seqViewerCommands', package='Pmv',
                                       topCommand=0)
        # add a button to show/hide the sequenceViewer
        filename = os.path.join(iconPath, 'seq.png')
        self.sequenceViewerIcon = ImageTk.PhotoImage(file=filename)
        width = self.sequenceViewerIcon.width()
        button = Tkinter.Button(
            canvas, width=width, height=height,
            command=showHideSequenceViewer, image=self.sequenceViewerIcon)
        self.sequenceViewerButton = canvas.create_window(
            x+4+width/2.0, 2+height/2.0, window=button, tags=('dashButtons',))
        #height = self.sequenceViewerIcon.height()
        #self.sequenceViewerButton = canvas.create_image(
        #    x + width/2.0, height/2.0, image=self.sequenceViewerIcon,
        #    tags=('dashButtons',))
        #x += width + 4
        #canvas.tag_bind(self.sequenceViewerButton, '<ButtonRelease-1>',
        #                showHideSequenceViewer)
        self.balloon.tagbind(canvas, self.sequenceViewerButton,
                             "show/hide sequenceViewer")

        #self.headerLine = canvas.create_line(0, 27, 100, 27, fill='black', tags=('dashButtons',))
        bb = canvas.bbox('dashButtons')
        self.minTreeWidth = bb[2]-bb[0]


    def setLevel(self, klass):
        if klass==Atom:
            self.selLevelButtonWidget.configure(
                image=self.atomSelectionLevelIcon)
        elif klass==Residue:
            self.selLevelButtonWidget.configure(
                image=self.residueSelectionLevelIcon)
        elif klass==Chain:
            self.selLevelButtonWidget.configure(
                image=self.chainSelectionLevelIcon)
        elif klass==Molecule:
            self.selLevelButtonWidget.configure(
                image=self.moleculeSelectionLevelIcon)
            

    def setLevel_cb(self, event=None):
        # post menu with the 3 missing buttons
        #bb = self.canvas.bbox(self.setLevelButton)
        #print bb
        x = self.canvas.winfo_rootx() + 58 # 48 is 2 buttons of width 24
        y = self.canvas.winfo_rooty()
        self.vf.setSelectionLevel.bottomMenu.post(x,y)
        self.menus.append(self.vf.setSelectionLevel.bottomMenu)
        

    def settingMenu_cb(self, event=None):
        x = self.canvas.winfo_rootx() + 86 # 48 is 2 buttons of width 24
        y = self.canvas.winfo_rooty()
        menu = Tkinter.Menu(self.canvas, tearoff=0)
        menu.add_command(
            label='set natural Width', command=self.vf.dashboard.setNaturalSize)
        menu.add_command(label='increase column width',
                         command=self.vf.dashboard.increaseColumnWidth)
        menu.add_command(label='decrease column width',
                         command=self.vf.dashboard.decreaseColumnWidth)
        menu.post(x,y)
        self.menus.append(menu)
        

    def cancelMenu(self, event=None):
        for menu in self.menus:
            #print 'unposting', menu
            menu.unpost()
        self.menus = []
        

    def addSel_cb(self, event=None):
        self.vf.addSelectionToDashboard.guiCallback()
        
        
    def createHeaderCanvas(self, master):
        master1 = Tkinter.Frame(master)
        self.headerCanvas = Tkinter.Canvas(master1, bg='#EEEEEE', height=30,
                                           highlightthickness=0)
        self.headerCanvas.pack(side='top', fill='x')
        master1.pack(side='top', fill='x')
        return master1

    
    def createSelectionBox(self, master):
        master1 = Tkinter.Frame(master)

        # add selector entry
        self.selector = CompoundStringSelector()
        #self.selectorEntry = Pmw.EntryField(
        #    w, labelpos='w', label_text='Sel.:',
        #    entry_width=12, validate=None, command=self.selectFromString)
        self.selectorEntry = Pmw.ComboBox(
            master1, labelpos='w', label_text='Sel.:', entry_width=12,
            ##scrolledlist_items = self.vf.sets.keys(),
            selectioncommand=self.selectFromString, fliparrow=1)
        self.selectorEntry.pack(side='left', expand=1, fill='x')

        # add selection tree expansion checkbox
        #var = self.expandTreeOnSelection = Tkinter.IntVar(0)
        #c = self.expandTreeOnSelectionTk = Tkinter.Checkbutton(
        #    master1, text="Expand", variable=var)
        #c.pack(side='left')
        
        # add backbone only widget
        self.bbmode_menu = Pmw.ComboBox(
            master1, selectioncommand= self.bbmodevar.set,
            scrolledlist_items = ['CMD', 'BB', 'SC', 'SC+CA', 'ALL'],
            entryfield_entry_width=4, fliparrow=1)
        self.bbmode_menu.selectitem('CMD')
        self.bbmode_menu.pack(side='right', expand=0)
        master1.pack(side='top', fill='x')

        self.selectorHelp = """This entry is used to select entities in the dashboard tree. 
Nodes selected in the dashboard tree are outlined by a yellow background.
When a command button is clicked for a selected node, the command is applied to all selected nodes.
The syntax for selection is a ';' separated list of expressions.
Each expression is a ':' separated list of selectors applying at the various levels of the Tree.
For instance:
    :::CA selects all alpha carbon atoms and sets the selection level to Atom
    :A::CA selects all CA in chain A
    ::CYS* selects all cysteines and sets the selection level to Residue
    
special names such as water, ions, DNA, RNA Amino Acids and lignad can be used at the residue level
special names such as sidechain, backbone, backbone+h, hetatm can be used at the atom level
"""
        self.balloon.bind(self.selectorEntry, self.selectorHelp)

        self.bbmodeHelp = """This option menu is used to specify whether commands should be applied to the
backbone atoms only (BB), the side chain atoms only (SC), the sidechain atoms
and CA atoms (SC+CA) or the full molecular fragment (ALL).
This setting can be overridden by each column (CMD)"""
        self.balloon.bind(self.bbmode_menu, self.bbmodeHelp)

##         expandHelp = """Check in order to expand the dashboard tree upon selection and select nodes in tree.
## Uncheck to perform PMV selection add"""
##         self.balloon.bind(self.expandTreeOnSelectionTk, expandHelp)

        return master1


    def addColumnDescriptor(self, columnDescr):
        vf = columnDescr.vf
        # load Pmv commands
        for cmd, module, package in columnDescr.pmvCmdsToLoad:
            #print 'loading', cmd, module, package
            vf.browseCommands(module, commands=(cmd,), package='Pmv', log=0)

        # register interest in Pmv commands
        dashboardCmd = vf.dashboard
        for cmd in columnDescr.pmvCmdsToHandle:
            #print 'register', cmd, columnDescr.title
            vf.cmdsWithOnRun[vf.commands[cmd]] = [dashboardCmd]

        cmd = columnDescr.cmd

        if isinstance(cmd[0], str):
            cmd[2]['callListener']=False
            columnDescr.cmd = (vf.commands[cmd[0]], cmd[1], cmd[2])
            #cmd[2]['callListener'] = False # prevents dashboard issues commands
                                            # from calling dashboard.onCmdRun
        if columnDescr.title is None:
            columnDescr.title = name  ### FIX THIS: name -?

        TreeWithButtons.addColumnDescriptor(self, columnDescr)


    def expandParents(self, object):
        """Expand all parents of the node"""
        p = object.parent
        if not self.objectToNode.has_key(p):
            self.expandParents(p)
            
        self.objectToNode[p].expand()


    def selectFromString(self, value):
        #value = self.selectorEntry.getvalue()
        from MolKit.molecule import MoleculeSet
        molecules = MoleculeSet(
            [x for x in self.root.object.children if not isinstance(
                x, MoleculeSet)] )
        molFrag = self.selector.select(molecules, value, sets=self.vf.sets)

##         if self.expandTreeOnSelection.get():
##             for obj in molFrag[0]:
##                 try:
##                     node = self.objectToNode[obj]
##                 except KeyError:
##                     self.expandParents(obj)
##                     node = self.objectToNode[obj]
##                 node.select(only=False)
##         else:
##             self.vf.select(molFrag[0])
        self.vf.select(molFrag[0])


    def rightButtonClick(self, columnDescr, event):
        columnDescr.bbmodeOptMenu(event)



from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet
from MolKit.protein import Chain, ChainSet, Residue, ResidueSet, Protein, ProteinSet
import numpy
from DejaVu.glfLabels import GlfLabels

class MolFragNodeWithButtons(NodeWithButtons):

    # self.getNodes()
    #  for a node that is from a molecule it returns a dict with key
    #    nodeName (i.e. name in dashboard) and value a set of Protein Chain
    #    Residue or Atom

    # self.getObjects() returns dict with keys the nodeNames of all nodes that
    #    are selected in the dashboard and keys a list of 4 sets (Atom, Residue,
    #    Chain and Molecule)
    #
    def __init__(self, object, parent, buttonType=None):
        NodeWithButtons.__init__(self, object, parent, buttonType)

        if isinstance(object, Molecule) and hasattr(self.object, 'chains'):
            font = self.tree().font.split()
            self.font = (font[0], font[1], 'bold')

           
    def _getCol(self,res):
        col = (0, 0, 0)
        if res.CAatom is not None:
            col = res.CAatom.colors['lines']
        elif res.C1atom is not None:
            col = res.C1atom.colors['lines']
        ## if res.hasCA:
        ##     ca = res.get('CA')
        ##     if len(ca)==0: # can happen when alternate position are available
        ##         ca = res.get('CA@.')
        ##         if len(ca)==0: # no CA found !
        ##             col = (.5, .5, .5)
        ##         else:
        ##             col = ca.colors['lines'][0]
        ##     else:
        ##         col = ca.colors['lines'][0]

        ## else:
        ##     at = res.get('C1*')
        ##     if at:
        ##         col = at[0].colors['lines']
        ##     else:
        ##         col = (0, 0, 0)
        return col

    
    def getMolColor(self, mol):
        res = mol.chains[0].residues[0]
        from DejaVu.colorTool import TkColor
        return TkColor(self._getCol(res))


    def getMolColors(self, mol):
        from DejaVu.colorTool import TkColor
        colors = []
        for res in mol.chains.residues:
            colors.append(TkColor(self._getCol(res)))
        return colors

   
    def drawNodeCustomization(self, x, y):
        """Draw additional things on the canvas"""
        if self.tree().showMolColBarVar.get() and \
               isinstance(self.object, Molecule) and \
               hasattr(self.object, 'chains'):
            #from time import time
            #t1 = time()
            tree = self.tree()
            canvas = tree.canvas
            colors = self.getMolColors(self.object)
            nbRes = len(colors)
            lineLength=80
            if nbRes>lineLength: # more residues than pixels
                stepSize = int(float(nbRes)/lineLength)
                width = 1
            else:
                stepSize = 1
                width = float(lineLength)/nbRes
                
            bb = canvas.bbox(self.labelTkid)

            for i, col in enumerate(colors[::stepSize]):
                glyphTkid =  canvas.create_rectangle(
                    bb[0]+i*width, bb[3]+1, bb[0]+(i+1)*width, bb[3]+3,
                    fill=col, outline=col, tags=(self.nodeTkTag,))
                #canvas.lower(glyphTkid)
            #print 'time to draw colbar for %s'%self.object.name, time()-t1
        else:
            self.glyphTkid = None

        x = NodeWithButtons.drawNodeCustomization(self, x, y)
        return x
 
    def setRotationCenter(self):
        vf = self.tree().vf
        obj = self.object
        vf.centerOnNodes(obj.setClass([obj]))


    def makeSetsForChains(self, event=None):
        vf = self.tree().vf
        for chain in self.object.children:
            name = chain.parent.name + '_' + chain.name
            vf.addSelectionToDashboard(name, chain)


    def deleteMolecule(self, event=None):
        self.tree().vf.deleteMol(self.object, undoable=True)


    def postMoleculeMenu(self,event):
        menu = Tkinter.Menu(tearoff=False)
        obj = self.object
        #isroot = False

        if isinstance(obj, MolecularSystem):
            cb = self.tree().vf.readMolecule.guiCallback
            menu.add_command(label='Read molecule', command=cb)
            menu.add_separator()
            cb = CallbackFunction(self.showHideAll, show=1)
            menu.add_command(label='Hide all molecules', command=cb)
            cb = CallbackFunction(self.showHideAll, show=0)
            menu.add_command(label='Show all molecules', command=cb)
            menu.add_checkbutton(label='Show molecules color ID',
                                 #onvalue=True, offvalue=False,
                                 var=self.tree().showMolColBarVar,
                                 command=self.tree().toggleShowMolColBar)
        else:
            #if isinstance(obj, Protein) or isinstance(obj, Molecule) and \
            #   not isinstance(obj, Chain) and not isinstance(obj, Residue):
            if isinstance(self.object, Molecule) and \
                   hasattr(self.object, 'chains'):
                isMol = True
            else:
                isMol = False

            if isMol:
                gcg = self.object.geomContainer.geoms
                if gcg['master'].visible:
                    menu.add_command(label='Hide molecule',
                                     command=self.showHide)
                else:
                    cb = CallbackFunction(self.showHide, show=0)
                    menu.add_command(label='Show molecule', command=cb)

                if hasattr(self.tree().vf, 'sequenceViewer'):
                    if self.tree().vf.sequenceViewer.isShown(self.object):
                        cb = CallbackFunction(self.showHideSeq, show=0)
                        menu.add_command(label='Hide Sequence',
                                         command=cb)
                    else:
                        cb = CallbackFunction(self.showHideSeq, show=1)
                        menu.add_command(label='Show Sequence', command=cb)
                else:
                    cb = CallbackFunction(self.showHideSeq, show=1)
                    menu.add_command(label='Show Sequence',
                                     command=cb)
                    
                menu.add_command(label='View text file',
                                 command=self.viewSource)
                menu.add_separator()

            menu.add_command(label='Show in 3D Viewer',
                             command=self.focusCamera)
            menu.add_command(label='Set rotation center',
                             command=self.setRotationCenter)

            if isMol:
                menu.add_separator()
            
                menu.add_command(label='RMSD/Superimpose', command=self.superimpose)

                menu.add_separator()
                if len(obj.children)>1:
                    menu.add_command(label='Make sets for chains',
                                     command=self.makeSetsForChains)
                menu.add_command(label='Delete', command=self.deleteMolecule)
                menu.add_separator()
                menu.add_command(label='Add Hydrogen', command=self.protonate)
                cb = CallbackFunction(self.protonate, polar=1)
                menu.add_command(label='Add Polar Hydrogens', command=cb)

                menu.add_command(label='Show Hydrogens',
                                 command=self.showHideHydrogens)
                cb = CallbackFunction(self.showHideHydrogens, negate=True)
                menu.add_command(label='Hide Hydrogens', command=cb)

        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.tree().menus.append(menu)
        canvas = self.tree().canvas
        canvas.bind('<FocusOut>', self.tree().cancelMenu)
        return menu


    def superimpose(self, event=None):
        dashboard = self.tree().vf.dashboard
        if dashboard.columnShowingForm:
            dashboard.columnShowingForm.Close_cb()

        from autoPairAtoms import SuperimposeGUI
        rmsdPanel = SuperimposeGUI(self)

        #values = dashboard.columnShowingFormValues.get('superimpose', None)
        #if values:
        #    pass # configure the values = 

    def showHideSeq(self, show=1):
        if not hasattr(self.tree().vf, 'sequenceViewer'):
            self.tree().vf.browseCommands('seqViewerCommands', package='Pmv',
                                          topCommand=0)
        svcmd = self.tree().vf.sequenceViewer
        if show and not svcmd.viewerVisible:
            svcmd.showHideGUI(visible=True)
        sv = svcmd.seqViewer
        
        mol = self.object
        if sv.isVisible.has_key(mol):
            if show:
                sv.showSequence(mol)
            else:
                sv.hideSequence(mol)
        else:
            if show:
                labels = buildLabels(mol)
                mol.sequenceLabels = labels
                sv.addMolecule(mol)
            else:
                sv.hideSequence(mol)
        if not show and max(sv.isVisible.values()) == False:
            # no visible molecules in the sequence viewer-->hide the viewer
            svcmd.showHideGUI(visible=False)
            
        
    def showHideAll(self, show=1):
        tree = self.tree()
        vi = tree.vf.GUI.VIEWER
        old = vi.suspendRedraw
        vi.suspendRedraw = True
        tree = self.tree()
        canvas = tree.canvas
        showMol = tree.vf.showMolecules
        for child in tree.root.children:
            if isinstance(child, MolFragNodeWithButtons):
                showMol(child.object, show)
                if show:
                    canvas.itemconfig(child.labelTkid, fill='gray50')
                else:
                    canvas.itemconfig(child.labelTkid, fill='black')
                    
        if show:
            canvas.itemconfig(self.labelTkid, fill='gray50')
        else:
            canvas.itemconfig(self.labelTkid, fill='black')
        vi.suspendRedraw = old

            
    def showHide(self, show=1, node=None):
        if node is None:
            node = self

        mol = node.object

        tree = self.tree()
        vi = tree.vf.GUI.VIEWER
        old = vi.suspendRedraw
        vi.suspendRedraw = True
        tree = self.tree()
        canvas = tree.canvas
        showMol = tree.vf.showMolecules

        # get all lines selected in the dashboard
        # we get a dict with key is molecule node (i.e. line in dashboard)
        # the values is a list of things of 4 sets (mol. chain, res atoms)
        for node, sets in self.getObjects(0).items():
            molset = sets[0]
            mol = molset[0]
            showMol(mol, show)
            if show:
                canvas.itemconfig(node.labelTkid, fill='gray50')
            else:
                canvas.itemconfig(node.labelTkid, fill='black')
        vi.suspendRedraw = old

        
    def showHideHydrogens(self, negate=0):
        hydrogens = self.object.findType(Atom).get('H*')
        if len(hydrogens):
            vf = self.tree().vf
            gca = self.object.geomContainer.atoms
            hat = {}.fromkeys(hydrogens)

            hydat = [] # list of H atoms bound to atoms visible as lines
            atoms = gca['bonded']
            if len(atoms):
                for a in atoms:
                    for b in a.bonds:
                        a2 = b.atom1
                        if a2==a: a2 = b.atom2
                        if hat.has_key(a2):
                            hydat.append(a2)
                vf.displayLines(AtomSet(hydat), negate=negate)

            hydat = [] # list of H atoms bound to atoms visible as sticks
            if not gca.has_key('sticks'):
                atoms = []
            else:
                atoms = gca['sticks']
            if len(atoms):
                for a in atoms:
                    for b in a.bonds:
                        a2 = b.atom1
                        if a2==a: a2 = b.atom2
                        if hat.has_key(a2):
                            hydat.append(a2)
                vf.displaySticksAndBalls(AtomSet(hydat), negate=negate)

            hydat = [] # list of H atoms bound to atoms visible as cpk
            if not gca.has_key('cpk'):
                atoms = []
            else:
                atoms = gca['cpk']
            if len(atoms):
                for a in atoms:
                    for b in a.bonds:
                        a2 = b.atom1
                        if a2==a: a2 = b.atom2
                        if hat.has_key(a2):
                            hydat.append(a2)
                vf.displayCPK(AtomSet(hydat), negate=negate)


    def protonate(self, polar=0):
        self.tree().vf.add_hGC(self.object, redraw=1, renumber=1,
                               polarOnly=polar,  method='noBondOrder')


    def viewSource(self, event=None):
        self.object.parser.viewSource()


    def focusCamera(self, event=None):
        vf = self.tree().vf
        if isinstance(self, SelectionWithButtons):
            #obj = self.getNodes(0)[0]
            obj = self.object._set
            if isinstance(obj[0], Atom): sca = 1
            elif isinstance(obj[0], Residue): sca = 2
            elif isinstance(obj[0], Chain): sca = 3
            elif isinstance(obj[0], Molecule): sca = 4
            name = self.object.name
            coords = vf.getTransformedCoords(obj.top[0], obj.findType(Atom).coords)
        else:
            if isinstance(self.object, Atom): sca = 1
            elif isinstance(self.object, Residue): sca = 2
            elif isinstance(self.object, Chain): sca = 3
            elif isinstance(self.object, Molecule): sca = 4
            name = self.object.full_name()
            if sca == 1:
                coords = [self.object.coords]
            else:
                coords = self.object.getAtoms().coords
            coords = vf.getTransformedCoords(self.object.top, coords)
        self.focusCamera_(coords, sca, name)


    def focusCamera_(self, coords, sca, name):
        # this method is also used in Pmv/seqDisplay.py
        mini = numpy.min( coords, 0)
        maxi = numpy.max( coords, 0)
        #self.currentCamera.AutoDepthCue(object=object)
        gui = self.tree().vf.GUI
        vi = gui.VIEWER

        vi.FocusOnBox(vi.rootObject, mini-6, maxi+6)

        # add flash spheres
        from DejaVu.Spheres import Spheres
        sph = Spheres('highlightFocus', vertices=coords, radii=(0.2,),
                      opacity=0.99, transparent=1, inheritMaterial=0,
                      materials=[(0,1,1),], visible=0)
        vi.AddObject(sph)
        sph.applyStrokes()

        # add flash label
        lab = GlfLabels(
            'flashLabel', fontStyle='solid3d', fontTranslation=(0,0,3.),
            fontScales=(sca*.3,sca*.3, .1), pickable=0, labels=[name],
            vertices=[numpy.sum(coords, 0)/len(coords)], visible=0)
        vi.AddObject(lab)
        lab.applyStrokes()

        #sph.fadeOut()
        cb = CallbackFunction(self.afterFlash_cb, sph)
        sph.flashT(interval=20, after_cb=cb)
        cb = CallbackFunction(self.afterFlash_cb, lab)
        lab.flashT(interval=20, after_cb=cb)


    def afterFlash_cb(self, geom):
        self.tree().vf.GUI.VIEWER.RemoveObject(geom)
        
        
    def drawNodeLabel(self, x, y):
        result = NodeWithButtons.drawNodeLabel(self, x, y)
        obj = self.object
        if isinstance(obj, Protein) or isinstance(obj, Molecule) and \
           not isinstance(obj, Chain) and not isinstance(obj, Residue):
            isMol = True
        else:
            isMol = False

        if isMol:
            tree = self.tree()
            canvas = tree.canvas
            gcg = self.object.geomContainer.geoms
            if gcg['master'].visible:
                canvas.itemconfig(self.labelTkid, fill='black')
            else:
                canvas.itemconfig(self.labelTkid, fill='gray50')
        return result
    

    def doubleLabel1(self, event=None):
        # override double click on label
        self.deselect() # undo yellow back ground that migh be created by first
                        # click in double click serie
        obj = self.object

        if isinstance(obj, Protein) or isinstance(obj, Molecule) and \
           not isinstance(obj, Chain) and not isinstance(obj, Residue):
            isMol = True
        else:
            isMol = False

        if isMol:
            gcg = self.object.geomContainer.geoms
            if gcg['master'].visible:
                self.showHide(show=1)
            else:
                self.showHide(show=0)

        
    def button3OnLabel(self, event=None):
        self.postMoleculeMenu(event)


    def getIcon(self):
        """return node's icons"""
        iconsManager = self.tree().iconsManager
        object = self.object
        if isinstance(object, Atom):
            icon = iconsManager.get("atom.png", self.tree().master)
        elif isinstance(object, Residue):
            #icon = iconsManager.get("residue.png", self.tree().master)
            icon = iconsManager.get("sidechain.png", self.tree().master)
        elif isinstance(object, Chain):
            icon = iconsManager.get("chain.png", self.tree().master)
        elif isinstance(object, Molecule):
            #icon = iconsManager.get("ms.png", self.tree().master)
            icon = iconsManager.get("molecule.png", self.tree().master)
        else:
            icon = None

        if icon:
            self.iconWidth = icon.width()
        else:
            self.iconWidth = 0
        return icon


    def getNodes(self, column):
        #print 'MolFragNodeWithButtons.getNodes'
        tree = self.tree()
        # return the objects associated with this node
        # handle the backbone, sidechain and both value for the command
        result = molFrag = self.object
        children = []
        from Pmv.moleculeIterator import MoleculeIterator
        for i, c in enumerate(result.children):
            if isinstance(c, MoleculeIterator):
                c = c.object
            children.append(c)
        if isinstance(result, MolecularSystem):
            result = MoleculeSet([x for x in children if \
                                  isinstance(x, Molecule)])
        bbmode = tree.bbmodevar.get()

        if bbmode=='CMD':
            #print 'Cmd setting found'
            bbmode = tree.columns[column].bbmode

        #print 'bbmode in getNode', column, bbmode
        if bbmode!='ALL':
            if result.findType(Chain)[0].isProteic():
                atoms = result.findType(Atom)
                if bbmode=='BB':
                    result = atoms.get('backbone')
                elif bbmode=='SC+CA':
                    result = atoms.get('sidechain')+atoms.get('CA')
                else:
                    result = atoms.get('sidechain')
                try:
                    return result.setClass([result])
                except KeyError:
                    return {self: [result]}

        if hasattr(result,'setClass') and result.setClass:
            return {self: [result.setClass([result])]}
        else:
            return {self: [result]}
        

    def getObjects(self, column):
        # return a list of objects associated with this node and possibly
        # other selected nodes.  For selection we return a list for each type
        # ( i.e. Atom, Residue, etc..)
        # if the node is selected, collect object from all other selected nodes
        tree = self.tree()
        if not self.isSelected:
            return self.getNodes(column)

        else:
            buttonValue = self.chkbtval[column]
            fill = tree.columns[column].buttonColors
            # loop over selected nodes
            results = {}
            for node in tree.selectedNodes:
                if node.parent is None: # 'All Molecules' is selected 
                    continue

                topNode = node  # find molecule or set level
                while topNode.parent.parent!=None:
                    topNode = topNode.parent

                if results.has_key(topNode):
                    resultAtoms = results[topNode][3]
                    resultResidues = results[topNode][2]
                    resultChains = results[topNode][1]
                    resultMolecules = results[topNode][0]
                else:
                    resultAtoms = AtomSet([])
                    resultResidues = ResidueSet([])
                    resultChains = ChainSet([])
                    resultMolecules = MoleculeSet([])
                    
                    results[topNode] = [ resultMolecules, resultChains,
                                         resultResidues, resultAtoms ]

                    
                if node.buttonType is None: # None for percent buttons
                    if node in tree.displayedNodes:
                        tree.canvas.itemconfigure(node.chkbtid[column],
                                                  fill=fill[buttonValue])
                    node.chkbtval[column] = buttonValue
                result = node.getNodes(column)
                #result.append(node.getNodes(column))
                obj = result.values()[0][0]
                #print 'HHHHH', node, result, obj
                if isinstance(obj, AtomSet):
                    resultAtoms += obj
                elif isinstance(obj, ResidueSet):
                    resultResidues += obj
                elif isinstance(obj, ChainSet):
                        resultChains += obj
                elif isinstance(obj, MoleculeSet) or isinstance(obj, ProteinSet):
                    resultMolecules += obj

            #print 'HAHA', results
            return results
                

class MolFragIteratorNodeWithButtons(MolFragNodeWithButtons):

     def __init__(self, obj, parent):
         self.molIterator = None
         self.numMols = 0
         self.currentMolInd = 0
         if hasattr(obj, 'molIteratorNodeClass'): 
             self.molIterator = obj
             obj = self.molIterator.object
             self.numMols = self.molIterator.numMols
             self.currentMolInd = self.molIterator.currentMolInd
         MolFragNodeWithButtons.__init__(self, obj, parent)
         #print "MolFragIteratorNodeWithButtons:", obj, self.object, parent
         self.loadingMol = False

     def showMolIterator(self, event):
         # place the counter below the node in the dashboard
     	 counter = self.molIterator.counter
         canvas = self.tree().canvas
         canvx = canvas.winfo_rootx()
         canvy = canvas.winfo_rooty()
         x1, y1, x2, y2  = canvas.bbox(self.iconTkid)
	 if counter:
	    try:
		root = counter._hull.master
             	#root.geometry("+%d+%d"%(event.x_root,event.y_root+self.iconWidth/2) )
                root.geometry("+%d+%d"%(canvx+x1 ,canvy+y2) )
             	return
	    except: pass
         
         canvas.unbind('<FocusOut>')
         root = Tkinter.Toplevel()
         root.transient(canvas.master)
         #print "event:", event.x_root, event.y_root, root.winfo_pointerxy()
         #root.geometry("+%d+%d"%root.winfo_pointerxy())
         #root.geometry("+%d+%d"%(event.x_root,event.y_root+self.iconWidth/2) )
         root.geometry("+%d+%d"%(canvx+x1 ,canvy+y2) )
         root.overrideredirect(True)
         molind = self.currentMolInd
         
         c = Pmw.Counter(
            root, #label_text = '', labelpos = 'w',
            orient = 'horizontal', #label_justify = 'left',
            entry_width = 5,
            entryfield_value = molind+1,  
            entryfield_validate = {'validator' : 'integer',
                        'min' : 1, 'max' : self.numMols},
            entryfield_command = self.counterReturn_cb,
            increment = 1)
         
         c.grid(row=0, column=0)
         self.molIterator.counter = c
         c._upArrowBtn.unbind('<Any-ButtonRelease-1>')
         c._upArrowBtn.bind('<Any-ButtonRelease-1>', self.counterArrowRelease_cb)
         c._downArrowBtn.unbind('<Any-ButtonRelease-1>')
         c._downArrowBtn.bind('<Any-ButtonRelease-1>', self.counterArrowRelease_cb)
         im = ImageTk.PhotoImage(file=os.path.join(iconPath,'ok20.png'))
         #b = Tkinter.Button(root, image=im, command=self.counterReturn_cb)
         #b.im = im
         #b.grid(row=0, column=1)
         
         im = ImageTk.PhotoImage(file=os.path.join(iconPath,'cancel20.png'))
         b = Tkinter.Button(root, image=im, command=self.counterCancel_cb)
         b.im = im
         b.grid(row=0, column=2)
         #c._hull.wait_visibility(root)
         #root.grab_set()


     def counterValidate(self, text):
         pass

     def counterArrowRelease_cb(self, event=None):
     	 counter = self.molIterator.counter
         counter._stopCounting(event)
         self.counterReturn_cb()

     def counterReturn_cb(self):
     	 counter = self.molIterator.counter
         val = counter.get()
         molind = int(val)-1
         if molind == self.currentMolInd: return
         if self.loadingMol:
             counter._counterEntry.setentry(self.currentMolInd)
             return
         self.loadNextMol(molind)


     def getIcon(self):
        """return node's icons"""
        #print  "Iterator, getIcon", self.object, self.molIterator 
        iconsManager = self.tree().iconsManager
        object = self.object
        icon = None
        if isinstance(object, Atom):
            return MolFragNodeWithButtons.getIcon(self)
        elif isinstance(object, Residue):
            return MolFragNodeWithButtons.getIcon(self)
        elif isinstance(object, Chain):
            return MolFragNodeWithButtons.getIcon(self)
        elif isinstance(object, Molecule):
            icon = iconsManager.get("molecule1.png", self.tree().master)
            if icon:
                self.iconWidth = icon.width()
            else:
                self.iconWidth = 0
            return icon

     def drawNodeIcon(self, x, y):
         """Draw the node's icon"""
         iconWidth = MolFragNodeWithButtons.drawNodeIcon(self, x,y)
         if self.molIterator:
             tree = self.tree()
             canvas = tree.canvas
             if self.iconTkid:
                 canvas.unbind("<Button-1>")
                 canvas.tag_bind(self.iconTkid, "<Button-1>", self.showMolIterator)
         return iconWidth
     
     def counterCancel_cb(self):
         if self.loadingMol: return
         #self._counter._hull.grab_release()
     	 counter = self.molIterator.counter
	 root = counter._hull.master
	 root.destroy()
         self.molIterator.counter = None


     def loadNextMol(self, molind):
         self.loadingMol = True
         oldmolind = self.currentMolInd
         oldmol = self.object
         mol = self.molIterator.getNextMolecule(molind)
         #print "loadNextMol, newmol:", molind, mol.name, "oldmol:", oldmolind, oldmol.name
         vf = self.tree().vf
         onAddCmd = vf.dashboard.onAddObjectToViewer
         onRemoveCmd = vf.dashboard.onRemoveObjectFromViewer
         def tmpCmd(obj):
             #print "tmpCmd:", obj
             return
         vf.dashboard.onAddObjectToViewer = tmpCmd
         vf.dashboard.onRemoveObjectFromViewer = tmpCmd
         # remove current mol and add new one
         vf.cleanCmdStack(vf.NEWundo, oldmol)
         vf.cleanCmdStack(vf.redo, oldmol)
         #suspend redraw of the sequence viewer, so it does not remove
         #the old molecule's sequence or add the new molecule (yet)
         sv = None
         if hasattr(vf, "sequenceViewer") and vf.sequenceViewer.viewerVisible:
             vf.sequenceViewer.suspendRedraw = True
             sv = vf.sequenceViewer.seqViewer
             # get the index of the old molecule in the sv: 
             svMolInd = sv.sequenceOrder.index(oldmol)
         
         vf.deleteMol.deleteMol(oldmol, undoable=True)
         self.molIterator.addToMolCache(oldmolind, oldmol)
         #mol._fastLoad = True
         # remove the old sequence from the sv , do not resize it or rearrange
         # the other sequences:
         if sv is not None:
             sv.removeMolecule(oldmol, False)
         vf.addMolecule(mol, True)
         if sv is not None:
             vf.sequenceViewer.suspendRedraw = False
             # add new molecule to the sv (at the old molecule's location):
             sv.addMolecule(mol, molInd=svMolInd)
         
         self.object = mol
         root = self.tree().root
         self.currentMolInd = molind
         self.tree().root.refreshChildren()
         
         vf.dashboard.onAddObjectToViewer = onAddCmd
         vf.dashboard.onRemoveObjectFromViewer = onRemoveCmd
         self.loadingMol = False
         #del mol._fastLoad



class SelectionWithButtons(MolFragNodeWithButtons):
    ## this is used to show the current selection in the dashboard
    ## the molecular fragment is returned by self.getNodes()

    def __init__(self, object, parent):

        MolFragNodeWithButtons.__init__(self, object, parent)
#                                        buttonType='OnOffButtons')
        self.nbSplits = 0
        font = self.tree().font.split()
        self.font = (font[0], font[1], 'italic')

    def getNodes(self, column):
        return {self: [self.tree().vf.getSelection().copy()]}

    def setRotationCenter(self):
        vf = self.tree().vf
        sel = vf.getSelection()
        obj = sel[0]
        vf.centerOnNodes(obj.setClass(sel))

    def postSetMenu(self,event):
        menu = Tkinter.Menu(tearoff=False)
        menu.add_command(label='Split', command=self.splitSelection)
        menu.add_command(label='Clone', command=self.cloneSelection)
        menu.add_separator()            
        atset = self.tree().vf.selection
        if not len(atset) or len(atset.top.uniq()) != 1:
            menu.add_command(label='RMSD/Superimpose', command=self.superimpose, state='disable')
        else:
            menu.add_command(label='RMSD/Superimpose', command=self.superimpose)
        menu.add_separator()
        menu.add_command(label='Show in 3D Viewer', command=self.focusCamera)
        menu.add_command(label='Set rotation center',
                         command=self.setRotationCenter)
        menu.add_separator()
        menu.add_command(label='Delete selected Atoms',
                         command=self.tree().vf.deleteCurrentSelection)
        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.tree().menus.append(menu)
        canvas = self.tree().canvas
        canvas.bind('<FocusOut>', self.tree().cancelMenu)


    def button3OnLabel(self, event=None):
        self.postSetMenu(event)


    def cloneSelection(self):
        self.splitSelection(cmdName='clone', deleteAfterCopy=False)

        
    def splitSelection(self, cmdName='split', deleteAfterCopy=True):

        nodes = self.getNodes(1)
        if nodes == self.tree().vf.Mols:
            from tkMessageBox import showwarning
            showwarning("Warning", "select something first")
        else:
            nodes = self.getNodes(0) # does not use dashboard selection
            if len(nodes)==0:
                return
            self.nodes = nodes
            cb = CallbackFunction( self.executeSplit,
                                   deleteAfterCopy=deleteAfterCopy)
            w = self.nameSelectionDialog = Pmw.PromptDialog(
                self.tree().vf.master, title = 'Split name', 
                label_text = "Enter the name of the molecule to %s"%cmdName,
                entryfield_labelpos = 'n',
                buttons = ('OK', 'Cancel'), command=cb)
            #w.insertentry(0, nodes.buildRepr()[:30].replace(';', ''))
            w.insertentry(0, "%s_%d"%(cmdName,self.nbSplits))
            self.nbSplits += 1
            w.component('entry').selection_range(0, Tkinter.END) 
            w.component('entry').focus_set()
            w.component('entry').bind('<Return>', cb)
            self.nameSelectionDialog.geometry(
                '+%d+%d' % (self.tree().vf.master.winfo_x()+200,
                            self.tree().vf.master.winfo_y()+200))             


    def executeSplit(self, result, deleteAfterCopy=True):
        self.nameSelectionDialog.withdraw()
        if result == 'OK'  or hasattr(result, "widget"):
            name = self.nameSelectionDialog.get()   
            if not name: return  
            vf = self.tree().vf
            vf.clearSelection()
            self._splitSet(self.nodes, name=name,
                           deleteAfterCopy=deleteAfterCopy)
        

    def _splitSet(self, nodes, name=None, deleteAfterCopy=True):
        if name is None:
            name = nodes.buildRepr()[:30]
        name = name.replace(" ", "_")
        name = name.replace(";", "")
        vf = self.tree().vf

        # make one AtomSet out of all objects
        atoms = AtomSet([])
        for node,objlist in nodes.items():
            for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(obj)==0: continue
                # get all atoms for this node
                atoms += obj.findType(Atom)
        from MolKit import makeMoleculeFromAtoms
        mol = makeMoleculeFromAtoms(name, atoms)
        vf.addMolecule(mol)
        
        if deleteAfterCopy:
            vf.deleteAtomSet(atoms)

        

class SetWithButtons(SelectionWithButtons):
    ## these are user sets
    ## the obejcts are in a ListSet in self.object._set
    
    def setRotationCenter(self):
        vf = self.tree().vf
        sel = vf.getSelection()
        obj = sel[0]
        vf.centerOnNodes(self.object._set)

    def getNodes(self, column):
        return {self: [self.object._set]}


    def splitSet(self):
        
        self._splitSet(self.getNodes(0), name=self.object.name,
                       deleteAfterCopy=True)
        
    def copySet(self):
        self._splitSet(self.getNodes(0), name=self.object.name,
                       deleteAfterCopy=False)
        
    def postSetMenu(self,event):
        menu = Tkinter.Menu(tearoff=False)
        menu.add_command(label='Rename', command=self.renameSet)
        menu.add_command(label='Split', command=self.splitSet)
        menu.add_command(label='Clone', command=self.copySet)
        menu.add_command(label='Remove', command=self.removeSet)
        menu.add_separator()
        atset = self.object._set
        if len(atset.top.uniq()) != 1:
            menu.add_command(label='RMSD/Superimpose', command=self.superimpose, state='disable')
        else:
            menu.add_command(label='RMSD/Superimpose', command=self.superimpose)
        menu.add_separator()            
        menu.add_command(label='Set rotation center',
                         command=self.setRotationCenter)
        menu.add_command(label='Show in 3D Viewer', command=self.focusCamera)
        menu.add_separator()
        menu.add_command(label='Dismiss')
        menu.post(event.x_root, event.y_root)
        self.tree().menus.append(menu)
        canvas = self.tree().canvas
        canvas.bind('<FocusOut>', self.tree().cancelMenu)


    def removeSet(self):
        vf = self.tree().vf
        vf.dashboard.onRemoveObjectFromViewer(self.object)
        
        # remove molecular surface for this set if it exists
        name = 'surface_%s'% str(self).replace(' ', '_')
        name = name.replace('_','-')

        vi = vf.GUI.VIEWER
        for node,objlist in self.getNodes(0).items():
            # find molecules
            atoms = AtomSet([]) # collect atoms from objlist
            for obj in objlist:
                atoms += obj.findType(Atom)
            mols = atoms.top.uniq()
            for mol in mols:
                gc = mol.geomContainer
                if gc.geoms.has_key(name):
                    geom = gc.geoms[name]
                    del gc.geoms[name]
                    del gc.atoms[name]
                    swigsrf = gc.msms[name][0]
                    del swigsrf
                    del gc.msms[name]
                    geom.protected = 0 
                    vi.RemoveObject(geom)

        # remove set from list of sets:
        del vf.sets[str(self)]
        
        vi.Redraw()


    def renameSet(self):
        from tkSimpleDialog import askstring
        oldname = self.object.name
        name = askstring("rename set", "new name:", initialvalue=oldname)
        if name is None:
            name = self.object.name
        self.object.setSetAttribute('name', name)
        self.tree().root.refreshChildren()

        # name set in vf.sets
        sets = self.tree().vf.sets
        sets[name] = sets[oldname]
        del sets[oldname]


class WaterWithButtons(SetWithButtons):

    # all atoms in residues with name HOH or WAT
    def getNodes(self, column):
        allres = self.tree().vf.allAtoms.parent.uniq()
        res = [a for a in allres if a.type=='WAT' or a.type=='HOH']
        return {self: [ResidueSet(res)]}


from MolKit.PDBresidueNames import RNAnames, AAnames, DNAnames, ionNames, \
     allResidueNames

class IonsWithButtons(SetWithButtons):
    
    # all atoms in residues with name in the ion names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if ionNames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class DNAWithButtons(SetWithButtons):
    
    # all atoms in residues with name in the DNA names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if DNAnames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class RNAWithButtons(SetWithButtons):

    # all atoms in residues with name in the RNA names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if RNAnames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class STDAAWithButtons(SetWithButtons):
    
    # all atoms in residues with name in the amino acids names list
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if AAnames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}


class LigandAtomsWithButtons(SetWithButtons):
    
    def getNodes(self, column):
        allres = self.tree().vf.Mols.chains.residues
        res = [a for a in allres if not allResidueNames.has_key(a.type.strip())]
        return {self: [ResidueSet(res)]}



#####################################################################
#
#  Column Descriptors for common PMV commands
#
#####################################################################
ColumnDescriptors = []

import Pmv, os, ImageTk

class MVColumnDescriptor(ColumnDescriptor):         

    def __init__(self, name, cmd, btype='checkbutton', 
                 buttonShape='circle', buttonColors = ['white', 'green'],
                 inherited=True, title=None, color='black',
                 objClassHasNoButton=None,
                 pmvCmdsToLoad=[], pmvCmdsToHandle=[],
                 showPercent=False, getNodeLevel=None, iconfile=None,
                 buttonBalloon=None, onButtonBalloon=None,
                 offButtonBalloon=None, geomNames=None):

        ColumnDescriptor.__init__(
            self, name, cmd, btype=btype, 
            buttonShape=buttonShape, buttonColors=buttonColors,
            inherited=inherited, title=title, color=color,
            objClassHasNoButton=objClassHasNoButton, showPercent=showPercent,
            buttonBalloon=buttonBalloon, onButtonBalloon=onButtonBalloon,
            offButtonBalloon=offButtonBalloon)

        self.getNodeLevel = getNodeLevel
        
        self.pmvCmdsToHandle = pmvCmdsToHandle #list of Pmv commands that
           # this column wants to know about

        self.pmvCmdsToLoad = pmvCmdsToLoad #list of Pmv commands that
           # need to be loaded. Each one is (command, module, package)

        self.bbmode = 'ALL'
        self.bbmodeWidgetcid = None

        self.iconfile = iconfile
        self.icon = None

        if iconfile: self.getIcon(iconfile)

        if geomNames is None:
            self.geomNames = []
        else:
            self.geomNames = geomNames


    def getGeoms(self, node, colIndex):
        #objects = node.getObjects(colIndex) # this uses the dashboard selection
        objects = node.getNodes(colIndex) # while this only returns the the dashboard
                                          # entry we clciked on
        # objects is a list of pairs (node, objList) where objlist is a list of
        # molecular fragments for Molecules, Chains, Residues, Atoms for this node
        # in the dashboard tree

        # FIXME we take the first object, which might be any of the selected
        #  nodes in the dashboard tree I think (MS)
        node, objlist = objects.items()[0]
        for obj in objlist:
            if len(obj)!=0: break
        if len(obj)==0: return []
        mol = obj.top[0]
        geoms = [x for x in mol.geomContainer.geoms['master'].children if
                 x.name in self.geomNames]
        return geoms


    def setForLabel(self, node):
        self.currentSelection = False
        if isinstance(node, SetWithButtons):
            self.vf.dashboard.objectLabelWidget.configure(
                text='For: '+node.object.name)
        elif isinstance(node, SelectionWithButtons):
            self.vf.dashboard.objectLabelWidget.configure(
                text='For: Current Selection')
            self.currentSelection = True
        else:
            self.vf.dashboard.objectLabelWidget.configure(
                text='For: '+node.object.full_name())

        
    def optMenu_cb(self, node, column, event=None):
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()

        cmd, args, kw = self.cmd
        self.setForLabel(node)
        
        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, column))
        
        #from Pmv.displayCommands import DisplayCommand
        #cmd.setLastUsedValues('default')
        # force display radio button
        if self.tree.vf.dashboard.columnShowingForm is not None:
            return
        
        if  cmd.cmdForms.has_key('default'): # if form exists change widget
            dispW = cmd.cmdForms['default'].descr.entryByName['display']['widget']
            dispW.component('display').invoke() # set radio to 'display'
            #print 'INVOKING DISPLAY'
        else:
            # change default values so when form is created it will use display
            cmd.lastUsedValues['default']['negate'] = False
            cmd.lastUsedValues['default']['only'] = False
            #print 'SETTING NEGATE AND ONLY TO FALSE'

        master = self.vf.dashboard.master3        
        self.form = ColumnDescriptor.optMenu_cb(
            self, node, column, event, master,
            postCreationFunc=self.vf.dashboard.expandParams)

        self.vf.dashboard.columnShowingForm = self
        
        cb = CallbackFunction(self.Apply_cb, cmd, node, column)
        self.vf.dashboard.applyButton.bind('<1>', cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)


    def Apply_cb(self, cmd, node, column, event=None):
        values = self.form.checkValues()
        if values=={}:
            return # Cancel was pressed
        val = 1
        if values.has_key('display'):
            if values['display']=='undisplay':
                val = 0

        cmd.lastUsedValues['default'].update(values)
        node.buttonClick(column, val=val) # always call with button on


    def Close_cb(self, event=None):
        if self.form:
        #    if sys.platform != "win32" or sys.platform: 
        #        self.form.root.quit() # this line seems to cause
                                      # Python interpreter crash on Windows
            self.form.withdraw()
        self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()


    def getIcon(self, iconfile):
        filename = os.path.join(iconPath, iconfile)
        self.icon = ImageTk.PhotoImage(file=filename)


    def _getNodes(self, node, colInd):
        #print 'MVColumnDescriptor _getNodes'
        return node.getObjects(colInd)

##         # added so that MVColumnDescriptor can override
##         objects = node.getObjects(colInd)
##         #print 'KKKK', objects, colInd
##         #print objects.__class__, len(objects), repr(objects)
##         if self.getNodeLevel:
##             if isinstance(objects, list): # special and user sets
##                 objects = [x.findType(self.getNodeLevel) for x in objects]
##             else: # MolKit node set
##                 objects = [objects.findType(self.getNodeLevel)]

##         return {self: [objects]}


    def execute(self, node, colInd):
        objects = self._getNodes(node, colInd)
        val = node.chkbtval[colInd]
        cmd, args, kw = self.cmd
        defaultValues = cmd.getLastUsedValues()
        defaultValues.update( kw )
        
        if  self.commandType == 'checkbutton':
            if defaultValues.has_key('negate'):
                defaultValues['negate'] = not val
            elif not val:
                return
        # when lines in dashboard are selected objects has one entry per line
        for node,objlist in objects.items():
            for objs in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(objs)==0: continue
                
                #print 'ColumnDescriptor execute GGGG', cmd, repr(objs), objs.__class__, args, defaultValues
                if isinstance(cmd, MVSelectCommand):
                    # if the command is select we need to be careful about
                    # the selection level. If objs is smaller than selection
                    # level (e.g. atoms vs residues) we set the selection level
                    # to objs else we turn objs into the selection level.
                    selection = self.tree.vf.selection
                    orderedList = [ProteinSet, ChainSet, ResidueSet, AtomSet]
                    orderedList1 = [MoleculeSet, ChainSet, ResidueSet, AtomSet]
                    try:
                        objInd = orderedList.index(objs.__class__)
                    except ValueError:
                        objInd = orderedList1.index(objs.__class__)
                    try:
                        selInd = orderedList.index(selection.__class__)
                    except ValueError:
                        selInd = orderedList1.index(selection.__class__)
                    if objInd > selInd: # obj is smaller than selection
                        self.tree.vf.setSelectionLevel(objs.elementType)
                    else: # selection is smaller so we make obj smaller
                        objs = objs.findType(selection.elementType)
                cmd ( *((objs,)+args), **defaultValues)

    ## def onPmvCmd(self, command, column, *args, **kw):
    ##     pass


    def setBBmode(self, value):
        assert value in ['BB', 'SC', 'SC+CA', 'ALL']
        self.bbmode = value
        if self.bbmodeWidgetcid:
            self.tree.delete(self.bbmodeWidgetcid)
        self.bbmodeWidgetcid = None
        

    def bbmodeOptMenu(self, event):
        self.bbmodeWidget = Pmw.ComboBox(
            self.tree.interior(), selectioncommand=self.setBBmode,
            scrolledlist_items=['BB', 'SC', 'SC+CA', 'ALL'],
            entryfield_entry_width=4)#, dropdown=0)
        self.bbmodeWidget.selectitem(self.bbmode)

        self.bbmodeWidgetcid = self.tree.create_window(event.x, event.y,
                                         window=self.bbmodeWidget, anchor='nw')

        
from MolKit.molecule import Molecule, MolecularSystem
from MolKit.protein import Residue, Chain


class MVvisibilityColumnDescriptor(MVColumnDescriptor):         

    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        self.cbOn = self.onShowMoleculesCmd
        self.cbOff = self.onShowMoleculesCmd
            

    def onShowMoleculesCmd(self, node, colInd, val, event=None):
        tree = self.tree
        # FIXME
        obj = node.getObjects(colInd) # what the cmd will apply to
        if isinstance(obj, list): # for sets
            obj = obj[0]

            self.vf.showMolecules(obj, not val)
            for mol in obj: # loop over molecules
                node = tree.objectToNode[mol]
                node.set(colInd, val)
        else:
            self.vf.showMolecules(obj, node.chkbtval[colInd])
            node.toggle(colInd)
        tree.redraw()


    def isOn(self, node):
        try:
            return node.geomContainer.masterGeom.visible
        except AttributeError:
            return 1 # at first the master geom is not there yet

visibilityColDescr = MVvisibilityColumnDescriptor(
    'showMolecules', ('showMolecules', (), {}), title='V', 
    buttonColors=['white', 'grey75'], inherited=False,
    buttonShape='rectangle', color='black',
    objClassHasNoButton = [Atom, Residue, Chain, MoleculeSet, MolecularSystem],
    pmvCmdsToHandle = [],#'showMolecules'],
    pmvCmdsToLoad = [('showMolecules', 'displayCommands', 'Pmv'),],
    iconfile='dashboardeyeballIcon.jpg',
    buttonBalloon='show/hide %s',
    onButtonBalloon='show molecules in %s',
    offButtonBalloon='hide molecules in %s')
ColumnDescriptors.append(visibilityColDescr)


class MoleculeSetNoSelection(MoleculeSet):
    pass


class MVSelectColumnDescriptor(MVColumnDescriptor):         
    """
    class for selection column in dashboard
    """

    def __init__(self, name, cmd, btype='checkbutton', 
                 buttonShape='circle', buttonColors = ['white', 'green'],
                 inherited=True, title=None, color='black',
                 objClassHasNoButton=[MoleculeSetNoSelection],
                 pmvCmdsToLoad=[], pmvCmdsToHandle=[],
                 buttonBalloon=None, onButtonBalloon=None,
                 offButtonBalloon=None):

        MVColumnDescriptor.__init__(
            self, name, cmd, btype=btype, 
            buttonShape=buttonShape, buttonColors=buttonColors,
            inherited=inherited, title=title, color=color,
            objClassHasNoButton=objClassHasNoButton,
            pmvCmdsToLoad=pmvCmdsToLoad, pmvCmdsToHandle=pmvCmdsToHandle,
            showPercent='_selectionStatus',
            iconfile='dashboardSelectionIcon.jpg',
            buttonBalloon=buttonBalloon, onButtonBalloon=onButtonBalloon,
            offButtonBalloon=offButtonBalloon)

        self.selectionDict = {}
        self.getNodeLevel = Atom
        self.deselectVar = Tkinter.IntVar()
        self.distanceVar = Tkinter.DoubleVar()
        self.distanceVar.set(5.0)
        

    def makeNames(self, obj, selector, selLevel='atom'):
        names = ''
        for ob in obj:
            if selLevel=='atom':
                if isinstance(ob, Atom):
                    pass
                elif isinstance(ob, Residue):
                    names += '%s:%s;'%(ob.full_name(), selector) 
                elif isinstance(ob, Chain):
                    names += '%s::%s;'%(ob.full_name(), selector)
                elif isinstance(ob, Molecule):
                    names += '%s:::%s;'%(ob.full_name(), selector)
            elif selLevel=='residue':
                if isinstance(ob, Atom):
                    pass
                elif isinstance(ob, Residue):
                    pass
                elif isinstance(ob, Chain):
                    names += '%s:%s;'%(ob.full_name(), selector)
                elif isinstance(ob, Molecule):
                    names += '%s::%s;'%(ob.full_name(), selector)
        return names


    def select_cb(self, names):
        self.vf.select(names, negate=self.deselectVar.get())
        
        
    def optMenu_cb(self, node, column, event=None):
        tree = self.tree
        if len(tree.selectedNodes)>0:
            tree.clearSelection()
            
        # called upon right click
        obj = node.getObjects(column) # what to cmd will apply to
        obj = obj[node][0]

        # reset deselection button
        self.deselectVar.set(0)
        
        menu = Tkinter.Menu(tearoff=False)
        
        cb = CallbackFunction( self.vf.deselect, "*" )
        menu.add_command(label='Clear selection', command=cb)

        cb = CallbackFunction( self.vf.invertSelection, subset=obj)
        menu.add_command(label='Invert selection', command=cb)

        cb = CallbackFunction( menu.post, event.x_root, event.y_root )
        menu.add_checkbutton(label='Deselect', variable=self.deselectVar,
                             command=cb)
       
        if not isinstance(obj, AtomSet) or len(obj)>1:

            menu.add_separator()
            menu.add_command(label='Subsets', command=None, state='disable',
                             font=('Helvetica', 12, 'bold'))

            names = self.makeNames(obj, 'backbone')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Backbone', command=cb)

            names = self.makeNames(obj, 'backbone+h')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Backbone+H', command=cb)

            names = self.makeNames(obj, 'sidechain')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Sidechains', command=cb)

            #names = self.makeNames(obj, 'hetero')
            # MS '1jff:::hetero' does not select anything :(
            cb = CallbackFunction( self.vf.selectHeteroAtoms, obj )
            menu.add_command(label='Hetero Atoms', command=cb)

            names = self.makeNames(obj, 'H*')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Hydrogens', command=cb)

            names = self.makeNames(obj, 'C*')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Carbons', command=cb)

        if not isinstance(obj, AtomSet) and \
               (not isinstance(obj, ResidueSet) or len(obj)>1):

            menu.add_separator()
            menu.add_command(label='Special', command=None, state='disable',
                             font=('Helvetica', 12, 'bold'))

            names = self.makeNames(obj, 'Water', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Water', command=cb)

            names = self.makeNames(obj, 'ions', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Ions', command=cb)

            names = self.makeNames(obj, 'dna', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='DNA', command=cb)

            names = self.makeNames(obj, 'rna', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='RNA', command=cb)

            names = self.makeNames(obj, 'aminoacids', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Amino Acids', command=cb)

            names = self.makeNames(obj, 'ligand', selLevel='residue')
            cb = CallbackFunction( self.select_cb, names )
            menu.add_command(label='Ligand', command=cb)

        menu.add_separator()

        menu.add_command(label='Displayed as', command=None,
                         state='disable', font=('Helvetica', 12, 'bold'))
        alines = AtomSet()
        acpk = AtomSet()
        asticks = AtomSet()
        aribbon = ResidueSet()
        asurface = AtomSet()
        aalab = AtomSet()
        arlab = ResidueSet()

        for ob in obj:
            mol = ob.top
            gca = mol.geomContainer.atoms
            if gca.has_key('bonded') and gca['bonded']:
                alines += gca['bonded']
            if gca.has_key('cpk') and gca['cpk']:
                acpk += gca['cpk']
            if gca.has_key('sticks') and gca['sticks']:
                asticks += gca['sticks']
            msmsAtoms = {}
            if hasattr(mol.geomContainer, 'msms'):
                for msmsName in mol.geomContainer.msms.keys():
                    if gca.has_key(msmsName) and gca[msmsName]:
                        msmsAtoms[msmsName] = gca[msmsName]
            if gca.has_key('AtomLabels') and gca['AtomLabels']:
                aalab += gca['AtomLabels']
            if gca.has_key('ResidueLabels') and gca['ResidueLabels']:
                arlab += gca['ResidueLabels']
            for k, v in gca.items():
                if k[:4] in ['Heli', 'Stra', 'Turn', 'Coil']:
                    aribbon += gca[k]

        if alines:
            cb = CallbackFunction( self.vf.select, alines.copy())
            menu.add_command(label='Lines', command=cb)
        if acpk:
            cb = CallbackFunction( self.vf.select, acpk.copy())
            menu.add_command(label='Spheres', command=cb)
        if asticks:
            cb = CallbackFunction( self.vf.select, asticks.copy())
            menu.add_command(label='Balls & Sticks', command=cb)
        if aribbon:
            cb = CallbackFunction( self.vf.select, aribbon.copy())
            menu.add_command(label='Ribbon', command=cb)
        if msmsAtoms:
            for name, atoms in msmsAtoms.items():
                cb = CallbackFunction( self.vf.select, atoms.copy())
                menu.add_command(label='Surface %s'%name,
                                 command=cb)
        if aalab:
            cb = CallbackFunction( self.vf.select, aalab.copy())
            menu.add_command(label='With atom labels', command=cb)
        if arlab:
            cb = CallbackFunction( self.vf.select, arlab.copy())
            menu.add_command(label='With residue labels',
                             command=cb)
                
        if len(self.vf.selection):
            menu.add_separator()
            menu.add_command(label='Edit current', command=None,
                             state='disable', font=('Helvetica', 12, 'bold'))
            self.menuPosition = (event.x_root, event.y_root)


            cb = CallbackFunction( self.setCutOff, self.expand, obj, node)
            menu.add_command(label='Expand selection', command=cb)

            cb = CallbackFunction( self.setCutOff, self.selectAround, obj, node)
            menu.add_command(label='Select around', command=cb)

        menu.add_separator()
        menu.add_command(label='Dismiss', command=self.cancelCB)

        menu.post(event.x_root, event.y_root)
        self.menu = menu


    def setCutOff(self, cmd, obj, node):
        self.menu.post( *self.menuPosition )
        self._tmproot = root = Tkinter.Toplevel()
        root.transient()
        root.geometry("+%d+%d"%root.winfo_pointerxy())
        root.overrideredirect(True)

        # add geometry to show what would be selected with this cut off
        from DejaVu.Spheres import Spheres
        self.showCutoffSph = Spheres(
            'cutOffFeedBack', inheritMaterial=0, radii=(0.3,),
            materials=((0,1,1, 0.5),), transparent=1)
        self.vf.GUI.VIEWER.AddObject(self.showCutoffSph)

        cb = CallbackFunction( self.returnCB, cmd, obj, node)
        vcb = CallbackFunction( self._custom_validate, obj, node)
        c = Pmw.Counter(
            root, #label_text = 'distance cuttoff', labelpos = 'w',
            orient = 'horizontal', #label_justify = 'left',
            entryfield_value = '%5.1f'%self.distanceVar.get(),
            entry_width = 5,
            datatype = {'counter' : 'real', 'separator' : '.'},
            entryfield_validate = vcb,
            entryfield_command = cb,
            increment = 0.5)

        c.grid(row=0, column=0)
        self._counter = c

        im = ImageTk.PhotoImage(file=os.path.join(iconPath,'ok20.png'))
        b = Tkinter.Button(root, image=im, command=cb)
        b.im = im
        b.grid(row=0, column=1)

        im = ImageTk.PhotoImage(file=os.path.join(iconPath,'cancel20.png'))
        b = Tkinter.Button(root, image=im, command=self.cancelCB)
        b.im = im
        b.grid(row=0, column=2)


    def getContextProteinNames(self, node):
        if isinstance(node, SetWithButtons):
            names = [node.object.name]
        elif node==self.tree.root: # replace 'All Molecules' by a list of names
            names = [x.name for x in node.object.children[1:]] # skip selection
        else:
            names = [node.object.full_name()]
        return names

        
    def showCutOffSelection(self, val, obj, node):
        # show what this cutoff will select
        
        centers = self.vf.selection.findType(Atom).coords
        names = self.getContextProteinNames(node)
        ats = self.vf.selectInSphere.getAtoms(centers, val, names)
        self.showCutoffSph.Set(vertices=ats.coords)

        
    def _custom_validate(self, obj, node, text):
        try:
            val = float(text)
            if val > 0.0:
                ok = True
            else:
                ok = False
        except:
            ok = False
        if ok:
            self.showCutOffSelection(val, obj, node)
            return 1
        else:
            return -1

    def cancelCB(self, event=None):
        if hasattr(self, '_tmproot'):
            self._tmproot.destroy()
            del self._tmproot
            self.vf.GUI.VIEWER.RemoveObject(self.showCutoffSph)
            del self.showCutoffSph
        self.menu.unpost()


    def returnCB(self, cmd, obj, node, event=None):
        value = self._counter.get()
        self.distanceVar.set(value)
        self.cancelCB(event)
        cmd(obj, node)
        
    
    def expand(self, obj, node):
        dist = self.distanceVar.get()
        molNames = self.getContextProteinNames(node)
        d = {}.fromkeys(molNames)
        centers = self.vf.selection.findType(Atom).coords
        oldSel = self.vf.getSelection().findType(Atom)[:]
        self.vf.expandSelection(oldSel, centers, dist, d.keys(), )



    def selectAround(self, obj, node):
        dist = self.distanceVar.get()
        molNames = self.getContextProteinNames(node)
        oldSel = self.vf.getSelection().findType(Atom)[:]
        centers = oldSel.coords
        self.vf.selectAround(oldSel, centers, dist, molNames)



selectColDescr = MVSelectColumnDescriptor(
    'select', ('select', (), {}), title='S', #title='Sel.',
    buttonColors=['white', '#FFCC05'], inherited=False,
    buttonShape='circle', color='magenta',
    pmvCmdsToHandle = [],#'select', 'clearSelection', 'selectFromString',
                       #'invertSelection', 'selectInSphere',
                       #'setSelectionLevel'],
    pmvCmdsToLoad = [('select', 'selectionCommands', 'Pmv'),
                     ('clearSelection', 'selectionCommands', 'Pmv'),
                     ('selectFromString', 'selectionCommands', 'Pmv'),
                     ('invertSelection', 'selectionCommands', 'Pmv'),
                     ('selectInSphere', 'selectionCommands', 'Pmv'),
                     ('expandSelection', 'selectionCommands', 'Pmv'),
                     ('selectAround', 'selectionCommands', 'Pmv'),                                          
                     ],
    buttonBalloon='select/deselect %s',
    onButtonBalloon='select %s',
    offButtonBalloon='deselect %s'
    )

ColumnDescriptors.append(selectColDescr)


displayLinesColDescr = MVColumnDescriptor(
    'display lines', ('displayLines', (), {}),
    buttonColors=['white', '#FF4F44'], title='L',
    color='#5B49BF', pmvCmdsToHandle = [],#'displayLines'],
    pmvCmdsToLoad = [('displayLines', 'displayCommands', 'Pmv')],
    showPercent='_showLinesStatus', iconfile='dashboardLineIcon.jpg',
    buttonBalloon='display/undisplay lines for %s',
    onButtonBalloon='display lines for %s',
    offButtonBalloon='undisplay lines for %s',
    geomNames=['bonded', 'nobnds', 'bondorder']
)
ColumnDescriptors.append(displayLinesColDescr)



class CPKColumnDescriptor(MVColumnDescriptor):
    """
    Column with a menu when I click on a button
    """
    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        #self.onOnly = self.execute
        #self.cbOn = self.execute
        #self.cbOff = None
        self.widgets = []
        self.form = None
        self.unitedButtonVar = Tkinter.IntVar()
        self.unitedButtonVar.set(0)
        self.bypropButtonVar = Tkinter.IntVar()
        self.bypropButtonVar.set(0)
        self.leveloptions=None
        

    def setAllGeomButtons(self, event=None):
        # copy the state of the allGeomsVar variable to all variable
        # used for the list of visible geoemtries 
        value = self.allGeomsVar.get()
        for var in self.geomsVar.values():
            var.set(value)

            
    def optMenu_cb(self, node, colInd, event=None):
        #print "optMenu", node, colInd
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()
        if self.form:
            return 

        self.setForLabel(node)
        obj = node.getObjects(colInd) # what to cmd will apply to
        self.objects = obj
        
        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, colInd))
        cmd, args, kw = self.cmd
        values = cmd.lastUsedValues['default']
        master = self.vf.dashboard.master3
        self.form = Tkinter.Frame(master)
        balloon = Pmw.Balloon(self.form, yoffset=15)
        #self.radiiGroup =  Pmw.Group(self.form, ring_borderwidth=3)
        #parent = self.radiiGroup.interior()
        parent = self.form
        w = Tkinter.Checkbutton(parent, text='By property',
                                variable=self.bypropButtonVar, command=self.byProperty_cb)
        w.grid(row=0, column=0, sticky='w', pady=5)
        w = Tkinter.Checkbutton(parent, text='United Radii',
                                variable=self.unitedButtonVar)
        balloon.bind(w, "allows the user to use United radii vs Regular radii.\nThe button is checked for United radii")
        #w.pack(side='top')
        w.grid(row=1, column=0, sticky='w', pady=5)
        w = self.offsetRadiusTw = ThumbWheel(parent,
             labCfg={'text':'offset radius:', 'side':'left'},
             showLabel=1,  width=100, height=20, min=0.0, type=float,
             precision=1, value=values['cpkRad'],
             continuous=True, oneTurn=2, wheelPad=2)
        balloon.bind(w,"The radius of the sphere for any atom = Offset Radius + Atomic Radius * Scale Factor")
        #w.pack(side='top')
        w.grid(row=2, column=0, sticky='e', pady=2)
        
        w = self.scaleFactorTw = ThumbWheel(parent,
             labCfg={'text':'scale factor:', 'side':'left'},
             showLabel=1, width=100,
             min=0.0, max=100, increment=0.01, type=float,
             precision=1, value=values['scaleFactor'],
             continuous=1, oneTurn=2, wheelPad=2, height=20)
        balloon.bind(w, 'The radius of the sphere for any atom = Offset Radius + Atomic Radius * Scale Factor')
        #w.pack(side='top')
        w.grid(row=3, column=0, sticky='e', pady=2)
        w = self.qualityTw = ThumbWheel(parent,
             labCfg={'text':'sphere quality:', 'side':'left'},
             showLabel=1, width=100, height=20, min=0,
             max=5, lockMin=1, type=int, precision=1,
             value=values['quality'], continuous=1,
             oneTurn=10, wheelPad=2)
        #w.pack(side='top')
        w.grid(row=4, column=0, sticky='e', pady=2)
        balloon.bind(w, 'if quality==0, a default value will be determined\nbased on the number of atoms involved in the command')
        
        #self.radiiGroup.pack(side='top', fill='x', expand=1 )
        self.form.pack(expand=1, fill='both')

        # By property panel:
        byProperty = self.vf.dashboard.paramsNB.insert('By property', before=1)
        self.form1 = f1 = Tkinter.Frame(byProperty)
        self.form1.pack(expand=1, fill='both')
        self.leftFrame = Tkinter.Frame(f1)#(byProperty)
        self.leftFrame.pack(side='left', expand=1, fill='both', anchor='nw')
        self.rightFrame = Tkinter.Frame(f1)#(byProperty)
        self.rightFrame.pack(side='left', expand=1, fill='both', anchor='ne')
        
        
        # Set of thumbwheels for the property panel:
        wd = 60
        ht = 12
        ## w = self.offsetRadiusTw1 = ThumbWheel(self.leftFrame,
        ##      labCfg={'text':'offset rad:', 'side':'left'},
        ##      showLabel=1,  width=wd, height=ht, min=0.0, type=float,
        ##      precision=1, value=values['cpkRad'],
        ##      continuous=True, oneTurn=2, wheelPad=2)
        ## balloon.bind(w,"The radius of the sphere for any atom = Offset Radius + Atomic Radius * Scale Factor")
        ## w.pack(side='top', anchor='e')
       
        ## w = self.scaleFactorTw1 = ThumbWheel(self.leftFrame,
        ##      labCfg={'text':'scale:', 'side':'left'},
        ##      showLabel=1, width=wd, height=ht,
        ##      min=0.0, max=100, increment=0.01, type=float,
        ##      precision=1, value=values['scaleFactor'],
        ##      continuous=1, oneTurn=2, wheelPad=2)
        ## balloon.bind(w, 'The radius of the sphere for any atom = Offset Radius + Atomic Radius * Scale Factor')
        ## w.pack(side='top', anchor='e')
        ## w = self.qualityTw1 = ThumbWheel(self.leftFrame,
        ##      labCfg={'text':'quality:', 'side':'left'},
        ##      showLabel=1, width=wd, height=ht, min=0,
        ##      max=5, lockMin=1, type=int, precision=1,
        ##      value=values['quality'], continuous=1,
        ##      oneTurn=10, wheelPad=2)
        ## w.pack(side='top', anchor='e')
        ## balloon.bind(w, 'if quality==0, a default value will be determined\nbased on the number of atoms involved in the command')
        
        self.levelGroup = Pmw.Group(self.leftFrame, tag_text='Level')
        #self.levelGroup.pack(expand=1, fill='x')
        self.levelGroup.pack(expand=1, fill='both')
        parent1 = self.levelGroup.interior()
        level = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}[self.vf.selectionLevel]
        self.levelRB = w = Pmw.RadioSelect(parent1, orient = 'vertical', #'horizontal'
                                           buttontype = 'radiobutton',
                                           command=self.setLevel, pady=1)
        if not self.leveloptions:
            self.leveloptions = {}
            from mglutil.util.colorUtil import ToHEX
            for name in  ['Atom', 'Residue', 'Chain', 'Molecule']:
                col = self.vf.ICmdCaller.levelColors[name]
                bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
                ag = ToHEX(col)
                self.leveloptions[name]= {'activebackground':bg, 'selectcolor':ag,
                                          'borderwidth':3}#1}
        for name  in ['Atom', 'Residue', 'Chain', 'Molecule']:
            w.add(name, **self.leveloptions[name])
        w.setvalue(level)
        self.levelRB.pack(side='top')
        
        self.propList = Pmw.ScrolledListBox(self.rightFrame,
            label_text = 'Select property', labelpos = 'nw',
            #selectioncommand = self.updateValMinMax,
            usehullsize = 1, hull_width = 150, hull_height = 200,
            horizscrollbar_width=7, vertscrollbar_width=7)
        self.setLevel(level)
        self.propList.pack(padx=3, pady=3,  expand=1, fill='both', )
        
        cb = CallbackFunction(self.Apply_cb, node, colInd)
        
        self.vf.dashboard.applyButton.bind('<1>', cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)

        #self.vf.dashboard.expandParams(self.form)
        self.vf.dashboard.expandParams(self.form1)
        self.vf.dashboard.columnShowingForm = self


    def byProperty_cb(self):
        var = self.bypropButtonVar.get()
        if var:
            #open "By Property" panel
            self.vf.dashboard.paramsNB.selectpage('By property')

    def setLevel(self, level='Atom'):
        self.level=level
        #print level
        levelDict =  {'Atom':(Atom, AtomSet) , 'Residue':(Residue,ResidueSet), 'Chain':(Chain , ChainSet),
                      'Molecule': (Molecule, MoleculeSet)}
        levelClass = levelDict[level][0]
        levelSetClass = levelDict[level][1]
        elements = levelSetClass([])
        for node, sets in self.objects.items():
            for obj in sets:
                elements += obj.findType(levelClass).uniq()
        #print "in dashboard CPK, elements:", elements
        props = [x[0] for x in elements[0].__dict__.items() if (
            x[0][0]!='_' and isinstance(x[1], (int, float)))]
        props.sort()
        self.propList.setlist(props)
   

    def Close_cb(self, event=None):
        self.vf.dashboard.paramsNB.delete('By property')
        for w in self.widgets: w.destroy()
        self.form.destroy()
        self.form = None
        self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()


    def Apply_cb(self, node, colInd, event=None):
        values = self.checkFormValues()
        if not len(values):
            return
        cmd, args, kw = self.cmd
        cmd.lastUsedValues['default'].update(values)
        node.buttonClick(colInd, val=1) # always call with button on


    def checkFormValues(self):
        values = {}
        #curpage = self.vf.dashboard.paramsNB.getcurselection()
        #if curpage == 'Basic':
        values['cpkRad'] = self.offsetRadiusTw.get()
        values['quality'] =  self.qualityTw.get()
        values['scaleFactor'] = self.scaleFactorTw.get()
        values['unitedRadii'] = self.unitedButtonVar.get()
        values['setScale'] = True
        #elif curpage == 'By property':
        byprop = self.bypropButtonVar.get()
        values['byproperty']=byprop
                    
        if byprop:
            prop = self.propList.getcurselection()
            if not len(prop):
                print "No property cpecified"
                return {}
            values['propertyName']= prop
            #values['cpkRad'] = self.offsetRadiusTw1.get()
            #values['quality'] =  self.qualityTw1.get()
            #values['scaleFactor'] = self.scaleFactorTw1.get()
            values['setScale'] = True
            values['propertyLevel']=self.level
        #print "cpk form values:", values
        return values

        
# we always use 'setScale':True because when a session is saved and restored
# this keyword gets set to False during restore and because the default value
# used by the dashboard

displayCPKColDescr = CPKColumnDescriptor(
    'display CPK', ('displayCPK', (), {'setScale':True}),
    buttonColors=['white', '#FF4F44'], title='C',
    color='#BF7C66', pmvCmdsToHandle = [],#'displayCPK'],
    pmvCmdsToLoad = [('displayCPK', 'displayCommands', 'Pmv')],
    showPercent='_showCPKStatus', iconfile='dashboardAtomIcon.jpg',
    buttonBalloon='display/undisplay atomic spheres for %s',
    onButtonBalloon='display atomic spheres for %s',
    offButtonBalloon='undisplay atomic spheres for %s',
    geomNames=['cpk']
)

## displayCPKColDescr = MVColumnDescriptor(
##     'display CPK', ('displayCPK', (), {'setScale':True}),
##     buttonColors=['white', '#FF4F44'], title='C',
##     color='#BF7C66', pmvCmdsToHandle = [], #'displayCPK'],
##     pmvCmdsToLoad = [('displayCPK', 'displayCommands', 'Pmv')],
##     showPercent='_showCPKStatus', iconfile='dashboardAtomIcon.jpg',
##     buttonBalloon='display/undisplay atomic spheres for %s',
##     onButtonBalloon='display atomic spheres for %s',
##     offButtonBalloon='undisplay atomic spheres for %s',
##     geomNames=['cpk']
## )
ColumnDescriptors.append(displayCPKColDescr)


class SticksAndBallsColumnDescriptor(MVColumnDescriptor):
    """
    Column with a menu when I click on a button
    """
    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        #self.onOnly = self.execute
        #self.cbOn = self.execute
        #self.cbOff = None
        self.widgets = []
        self.form = None
        self.checkButtonVar = Tkinter.IntVar()
        self.checkButtonVar.set(0)

    def setAllGeomButtons(self, event=None):
        # copy the state of the allGeomsVar variable to all variable
        # used for the list of visible geoemtries 
        value = self.allGeomsVar.get()
        for var in self.geomsVar.values():
            var.set(value)

            
    def optMenu_cb(self, node, colInd, event=None):
        #print "optMenu", node, colInd
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()
        if self.form:
            return 

        self.setForLabel(node)

        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, colInd))
        cmd, args, kw = self.cmd
        values = cmd.lastUsedValues['default']
        master = self.vf.dashboard.master3
        self.form = Tkinter.Frame(master)
        balloon = Pmw.Balloon(self.form, yoffset=15)
        self.sticksGroup =  Pmw.Group(self.form, tag_text='Sticks')
        parent = self.sticksGroup.interior()
        w = self.sticksRadiusTw = ThumbWheel(parent,
             labCfg={'text':'radius:', 'side':'left'},
             showLabel=1,  width=70, height=15, min=0.1, type=float,
             max=10.0, precision=2, value=values['cradius'],
             continuous=True, oneTurn=2, wheelPad=2)
        w.pack(side='left')

        w = self.sticksQualityTw = ThumbWheel(parent,
             labCfg={'text':'quality:', 'side':'left'},
             showLabel=1, width=70, height=15, min=0,
             max=5, lockMin=1, type=int,
             precision=1, value=values['cquality'],
             continuous=True, oneTurn=10, wheelPad=2)
        w.pack(side='left')
        self.sticksGroup.pack(side='top', fill='x', expand=1 )
        

        self.ballsGroup = Pmw.Group(self.form, tag_pyclass = Tkinter.Checkbutton,
             tag_text='Balls',
             tag_command = self.setBallsWidgets,
             tag_variable=self.checkButtonVar)
        parent = self.ballsGroup.interior()
        w = self.ballRadiusTw = ThumbWheel(parent,
                labCfg={'text':'radii:',  'side':'left'}, 
                showLabel=1, width=70, min=0.0, type=float,
                precision=1, value=values['bRad'],
                continuous=1, oneTurn=2, wheelPad=2, height=15)
        w.grid(column=0, row=0, sticky='w')
        balloon.bind(w, 'The Radii of the sphere geom representing the atom will be equal to (Ball Radii + Atom Radii * Scale Factor)')
        
        w = self.ballQualityTw = ThumbWheel(parent,
                       labCfg={'text':'quality:'}, 
                       showLabel=1, width=70,
                       min=0, max=5, lockMin=1, type=int,
                       precision=1, value=values['bquality'],
                       continuous=1, oneTurn=10, wheelPad=2, height=15)
        w.grid(column=1, row=0, sticky='w')
        balloon.bind(w, 'if quality = 0 a default value will be determined based on the number of atoms involved in the command')
        
        w = self.scaleFactorTw = ThumbWheel(parent,
                labCfg={'text':'scale factor:','side':'left'}, 
                showLabel=1, width=70,
                min=0.0, max=10.0, type=float,
                precision=2, value=values['bScale'],
                continuous=1, oneTurn=2, wheelPad=2, height=15)
        w.grid(column=0, row=1, columnspan=2, sticky='w')
        balloon.bind(w, 'The Radii of the sphere geom representing the atom will be equal to (Ball Radii + Atom Radii * Scale Factor)')

        self.ballsGroup.pack(side='top', fill='x', expand=1 )
        self.form.pack(expand=0, fill='both')
        self.setBallsWidgets()        
        obj = node.getObjects(colInd) # what to cmd will apply to
        self.objects = obj
        cb = CallbackFunction(self.Apply_cb, node, colInd)
        self.vf.dashboard.applyButton.bind('<1>', cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)

        self.vf.dashboard.expandParams(self.form)
        self.vf.dashboard.columnShowingForm = self


    def Close_cb(self, event=None):
        for w in self.widgets: w.destroy()
        self.form.destroy()
        self.form = None
        self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()


    def Apply_cb(self, node, colInd, event=None):
        values = self.checkFormValues()
        cmd, args, kw = self.cmd
        cmd.lastUsedValues['default'].update(values)
        node.buttonClick(colInd, val=1) # always call with button on


    def checkFormValues(self):
        values = {}
        values['cradius'] = self.sticksRadiusTw.get()
        values['cquality'] =  self.sticksQualityTw.get()
        values['bRad'] = self.ballRadiusTw.get()
        values['bquality'] = self.ballQualityTw.get()
        values['bScale'] = self.scaleFactorTw.get()
        val = self.checkButtonVar.get()
        if val:
            values['sticksBallsLicorice']='Sticks and Balls'
        else:
            values['sticksBallsLicorice'] = 'Licorice'
        return values



    def setBallsWidgets(self):
        val = self.checkButtonVar.get()
        tw = [self.ballRadiusTw, self.ballQualityTw, self.scaleFactorTw]
        if val:
            for w in tw:
                self.enableThumbWheel(w)
        else:
            for w in tw:
                self.disableThumbWheel(w)


    def displayOptions(self, cmd, obj, event):
        values = cmd.showForm(posx=event.x_root, posy=event.y_root,
                              master=self.tree.master)
        if values and len(values)==0: return # Cancel was pressed
        cmd.lastUsedValues['default'].update(values)
        cmd( *(obj,), **values)


    def disableThumbWheel(self, tw):
        """disables a thumbwheel widgets"""
        def foo(val):
            pass
        tw.configure(showLabel=0)
        tw.canvas.bind("<ButtonPress-1>", foo)
	tw.canvas.bind("<ButtonRelease-1>", foo)
	tw.canvas.bind("<B1-Motion>", foo)
        tw.canvas.bind("<Button-3>", foo)
        
        
    def enableThumbWheel(self, tw, val =None):
        """enables a thumbwheel widgets """
        tw.canvas.bind("<ButtonPress-1>", tw.mouseDown)
	tw.canvas.bind("<ButtonRelease-1>", tw.mouseUp)
	tw.canvas.bind("<B1-Motion>", tw.mouseMove)
        tw.canvas.bind("<Button-3>", tw.toggleOptPanel)
        tw.configure(showLabel=1)
        if val:
            tw.set(val, update=0)


## displaySandBColDescr = MVColumnDescriptor(
##     'display S&B', ('displaySticksAndBalls', (), {'setScale':True}),
##     buttonColors=['white', '#FF4F44'], title='B',
##     color='purple', pmvCmdsToHandle = [],#'displaySticksAndBalls'],
##     pmvCmdsToLoad = [('displaySticksAndBalls', 'displayCommands', 'Pmv')],
##     showPercent='_showS&BStatus', iconfile='dashboardBondIcon.jpg',
##     buttonBalloon='display/undisplay Sticks and Balls for %s',
##     onButtonBalloon='display sticks and balls for %s',
##     offButtonBalloon='undisplay sticks and balls for %s',
##     geomNames=['sticks','balls'])

displaySandBColDescr = SticksAndBallsColumnDescriptor(
    'display S&B', ('displaySticksAndBalls', (), {'setScale':True}),
     buttonColors=['white', '#FF4F44'],
    color='purple', title='B', pmvCmdsToHandle = [],#'displaySticksAndBalls'],
    pmvCmdsToLoad = [('displaySticksAndBalls', 'displayCommands', 'Pmv')],
    showPercent='_showS&BStatus', iconfile='dashboardBondIcon.jpg',
    buttonBalloon='display/undisplay Sticks and Balls for %s',
    onButtonBalloon='display sticks and balls for %s',
    offButtonBalloon='undisplay sticks and balls for %s',
    geomNames=['sticks','balls'])
ColumnDescriptors.append(displaySandBColDescr)



class RibbonColumnDescriptor(MVColumnDescriptor):


    # override Ribbon.optMenu_cb to display panel of extrude SS
    def optMenu_cb(self, node, column, event=None):
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()

        self.setForLabel(node)

        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, column))

        # find out type of chains
        hasAA = hasNA = False
        for node,objlist in node.getObjects(column).items():
            for obj in objlist:
                for chain in obj.findType(Chain):
                    ctype = chain.ribbonType()
                    if ctype=='NA': hasNA = True
                    if ctype=='AA': hasAA = True
                    if hasAA and hasNA: break
        
        master = self.vf.dashboard.master3
        self.form = None
        self.widgets = []
        #notebook = self.vf.dashboard.paramsNoteBook
        if hasAA:
            self.form = Tkinter.Frame(master)
            
            row = 0
            shapeList = ['default', 'rectangle', 'circle', 'ellipse', 'square',
                         'triangle']
            # shape chooser
            w = Pmw.ComboBox(
                self.form, label_text = 'Shape:', labelpos = 'nw',
                entryfield_value='default', entryfield_entry_width=3,
                selectioncommand = self.shapeParameters, listbox_height = 6,
                scrolledlist_items = shapeList)
            w.grid(row=row, column=0, sticky='ew')

            self.widgets.append(w)
            # put quality widget
            w = Pmw.Counter(
                self.form, labelpos = 'nw', label_text = 'Quality:',
                entry_width = 2, entryfield_value = 8,
                entryfield_validate = {'validator' : 'integer', 'min' : 2, 'max' : 99}
                )
            w.grid(row=row, column=1, sticky='ew')
            self.widgets.append(w)
            row += 1

            # width and height widget
            w = Pmw.Counter(
                self.form, labelpos = 'nw', label_text = 'Width:',
                entry_width=5, entryfield_value=1.2, increment=0.1,
                entryfield_validate = {'validator':'real', 'min':0.1 },
                datatype = {'counter' : 'real'},
                )
            w.grid(row=row, column=0, sticky='ew')
            self.widgets.append(w)

            w = Pmw.Counter(
                self.form, labelpos = 'nw', label_text = 'Height:',
                entry_width = 5, entryfield_value = 0.2, increment=0.1,
                entryfield_validate = {'validator' : 'real', 'min' : 0.1},
                datatype = {'counter' : 'real'},
                )
            w.grid(row=row, column=1, sticky='ew')
            self.widgets.append(w)
            row += 1

            # radius and arrow length
            w = Pmw.Counter(
                self.form, labelpos = 'nw', label_text = 'Radius:',
                entry_width = 5, entryfield_value = 0.1, increment=0.1,
                entryfield_validate = {'validator' : 'real', 'min' : 0.1},
                datatype = {'counter' : 'real'},
                )
            w.grid(row=row, column=0, sticky='ew')
            self.widgets.append(w)

            w = Pmw.Counter(
                self.form, labelpos = 'nw', label_text = 'Arrow Length:',
                entry_width = 5, entryfield_value = 2,
                entryfield_validate = {'validator' : 'integer', 'min' : 1},
                datatype = {'counter' : 'real'},
                )
            w.grid(row=row, column=1, sticky='ew')
            self.widgets.append(w)
            row += 1

            # caps check buttons
            var = self.fcapsVar = Tkinter.IntVar()
            self.fcapsVar.set(1)
            w = Tkinter.Checkbutton(self.form, text='Front cap', variable=var)
            w.grid(row=row, column=0, sticky='ew')
            self.widgets.append(w)
            
            var = self.bcapsVar = Tkinter.IntVar()
            self.bcapsVar.set(1)
            w = Tkinter.Checkbutton(self.form, text='Back cap', variable=var)
            w.grid(row=row, column=1, sticky='ew')
            self.widgets.append(w)

            self.form.pack(fill='both')
            
        # Add Nucleic Acids tab
        if hasNA:
            naPage = notebook.insert('Nucleic Acids', before=2)
            naPage.pack(expand=0, fill='both')
            self.vf.Nucleic_Acids_properties.showForm(
                'Display', root=naPage,
                okcancel=0, help=0, modal=0, blocking=0)

        self.hasAA= hasAA
        self.hasNA= hasNA
        cmd, args, kw = self.cmd
        cb = CallbackFunction(self.Apply_cb, cmd, node, column)
        self.vf.dashboard.applyButton.bind('<1>', cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)
        self.vf.dashboard.columnShowingForm = self
        if self.form is not None:
            self.vf.dashboard.expandParams(self.form)


    def shapeParameters(self, shape):
        if shape=='default':
            for widget in self.widgets[2:-2]:
                widget.component('entryfield').component('entry').configure(
                    state='normal')
            #set default values:
            self.widgets[2].setvalue(1.2)
            self.widgets[3].setvalue(0.2)
            self.widgets[4].setvalue(0.1)
            self.widgets[5].setvalue(2)
        elif shape=='rectangle' or shape=='ellipse':
            # enable width and heigth
            for widget in self.widgets[2:4]: # width and height
                widget.component('entryfield').component('entry').configure(
                    state='normal')
            # disable radius and arrow
            for widget in self.widgets[4:6]: # width and height
                widget.component('entryfield').component('entry').configure(
                    state='disabled')
            if shape=='rectangle':
                self.widgets[2].setvalue(1.2)
                self.widgets[3].setvalue(.2)
            else: #Ellipse
                self.widgets[2].setvalue(0.5)
                self.widgets[3].setvalue(0.2)

        elif shape=='square' or shape=='triangle':
            # enable width
            self.widgets[2].component('entryfield').component('entry').configure(
                state='normal')
            # disable height and radius
            for widget in self.widgets[3:5]: # width and height
                widget.component('entryfield').component('entry').configure(
                    state='disabled')
            # enable arrow length for square
            if shape=='square':
                self.widgets[5].component('entryfield').component('entry').configure(
                    state='normal')
            else:
                self.widgets[5].component('entryfield').component('entry').configure(
                    state='disabled')
                
        elif shape=='circle':
            # enable readius only
            for widget in self.widgets[2:-2]:
                widget.component('entryfield').component('entry').configure(
                    state='disabled')
            self.widgets[4].component('entryfield').component('entry').configure(
                state='normal')

        
    def Close_cb(self, event=None):
        for w in self.widgets: w.destroy()
        if self.form is not None:
            self.form.destroy()
        self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()


    def Apply_cb(self, cmd, node, column, event=None):
        from DejaVu.Shapes import Shape2D, Triangle2D, Circle2D, Rectangle2D,\
             Square2D, Ellipse2D
        shape = self.widgets[0].get()
        val = {}
        val['nbchords'] = int(self.widgets[1].getvalue())
        val['width'] = float(self.widgets[2].getvalue())
        val['height'] = float(self.widgets[3].getvalue())
        val['radius'] = float(self.widgets[4].getvalue())
        val['larrow'] = int(self.widgets[5].getvalue())
        #val['gapBeg'] = self.fcapsVar.get()
        #val['gapEnd'] = self.bcapsVar.get()
        val['frontcap'] = self.fcapsVar.get()
        val['endcap'] = self.bcapsVar.get()
        val['shape2'] = None
        if shape=='default':
            val['shape1'] = Rectangle2D(val['width'],val['height'], vertDup=1)
            val['shape2'] = Circle2D(radius=val['radius'])
        elif shape=='rectangle':
            val['shape1'] = Rectangle2D(val['width'],val['height'], vertDup=1)
        elif shape=='circle':
            val['shape1'] = Circle2D(radius=val['radius'])
        elif shape=='ellipse':
            val['shape1'] = Ellipse2D(demiGrandAxis= val['width'],
                                      demiSmallAxis=val['height'])
        elif shape=='square':
            val['shape1'] = Square2D(side=val['width'], vertDup=1)
        elif shape=='triangle':
            val['shape1'] = Triangle2D(side=val['width'], vertDup=1)
            
        # get a dict for all selected nodes in dashboard
        nodedict = node.getObjects(column) # what to cmd will apply to
        for node, lists in nodedict.items():
            for _set in lists:
                if len(_set):
                    cmd.doitWrapper( _set, **val)

        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, column))


    def getGeoms(self, node, colIndex):
        objects = node.getObjects(colIndex)
        node, objlist = objects.items()[0]
        if len(objlist[0])==0: return []
        mol = objlist[0].top[0]
        ssgeom = mol.geomContainer.geoms.get('secondarystructure', None)
        if ssgeom:
            return ssgeom.children
        else:
            return []

 
displaySSColDescr = RibbonColumnDescriptor(
    'display Second.Struct.', ('ribbon', (), {}),
    buttonColors=['white', '#FF4F44'], title='R', 
    color='#333333', pmvCmdsToHandle = [],#'displayExtrudedSS'],
    pmvCmdsToLoad = [('displayExtrudedSS', 'secondaryStructureCommands', 'Pmv')],
    showPercent='_showRibbonStatus', iconfile='dashboardRibbonIcon.jpg',
    buttonBalloon='Display/Undisplay ribbon for %s',
    onButtonBalloon='display ribbon for %s',
    offButtonBalloon='undisplay ribbon for %s',
    geomNames=['secondaryStructure'])


ColumnDescriptors.append(displaySSColDescr)


import types
class MSMSColumnDescriptor(MVColumnDescriptor):

    def __init__(self, name, cmd, btype='checkbutton', 
                 buttonShape='circle', buttonColors = ['white', 'green'],
                 inherited=True, title=None, color='black',
                 pmvCmdsToLoad=[], pmvCmdsToHandle=[],
                 buttonBalloon=None, onButtonBalloon=None,
                 offButtonBalloon=None, geomNames=None):

        MVColumnDescriptor.__init__(
            self, name, cmd, btype=btype, 
            buttonShape=buttonShape, buttonColors=buttonColors,
            inherited=inherited, title=title, color=color,
            pmvCmdsToLoad=pmvCmdsToLoad, pmvCmdsToHandle=pmvCmdsToHandle,
            showPercent='_showMSMSStatus_MSMS_MOL',
            iconfile='dashboardSurfaceIcon.jpg',
            buttonBalloon=buttonBalloon, onButtonBalloon=onButtonBalloon,
            offButtonBalloon=offButtonBalloon, geomNames=geomNames)

        #self.getNodeLevel = Atom


    def execute(self, node, colInd):
        # get status of clicked button (1:full, 0:empty or partial)
        val = node.chkbtval[colInd]

        # get parameter from MSMS command input form
        cmd = self.vf.computeMSMS
        formValues = cmd.getLastUsedValues()
        formValues = cmd.fixValues(formValues)

        for node,objlist in node.getObjects(colInd).items():

            # collect atoms from the 4 lists in objList
            atoms = AtomSet([]) # collect atoms from objlist
            for obj in objlist:
                atoms += obj.findType(Atom)
            if len(atoms)==0: continue
            # find molecule
            #mol = atoms[0].top

            if len(atoms)==1:
                # this does not compute a surface in MSMS :(. For now we
                # simply display CPK instead
                self.vf.displayCPK(atoms, topCommand=False)
                continue
            
            #from mglutil.util import misc
            #MB = float(1040*1024)
            #mem0 = mem1 = mem2 = misc.memory()
            
            # generate surface name and force perMol based on node type
            if isinstance(node, SetWithButtons):# or \
                   #isinstance(node, SelectionWithButtons):
                # MS Sept 2013: made selection not compute a separate surface
                # if we cant a separate surface make a set from the selection
                # this way we can display an opened surface for the selection
                formValues['perMol']=0
                name = 'surface_%s'% str(node).replace(' ', '_')
                name = name.replace('_','-')
            else:
                formValues['perMol']=1
                name = 'MSMS-MOL'

            #print 'AAAAA perMol',  formValues['perMol']
            mols  = self.vf.getNodesByMolecule(atoms, Molecule)[0]
            recompute = False
            for mol in mols:
                if not cmd.objectState.has_key(mol):
                    cmd.onAddObjectToViewer(mol)
                # find last parameters used to compute this surface
                try:
                    srf = mol.geomContainer.msms[name][0]
                    lastValues = {
                        'pRadius': srf.probeRadius,
                        'density': srf.density,
                        'perMol': srf.perMol,
                        'surfName': srf.surfName,
                                'noHetatm': srf.noHetatm,
                        'hdset': srf.hdset,
                        'hdensity': srf.hdensity,
                        }
                except KeyError:
                    lastValues = {}

                if val: # if button is on we might have to re-compute
                    recompute = False
                    if len(lastValues)==0: # surface was not computed yet
                        recompute=True
                        break
                    elif isinstance(node, SelectionWithButtons):
                        # if the node is the current selection, the selection might
                        # have changed and we have to recompute the surface
                        recompute=True
                        break
                    else: # compare last parameters with ones in form
                        for k,v in lastValues.items():
                            nv = formValues.get(k, None)
                            if nv!=v:
                                #print 'MSMS recompute: new param', k, nv, v
                                recompute=True
                                break
            if recompute:
                formValues['surfName']=name
                formValues['display']=False
                #print 'computing MSMS surface', formValues
                self.vf.computeMSMS( *(atoms,), **formValues)
                #srf = mol.geomContainer.msms[name][0]
            #mem1 = misc.memory()
            # endif val

            # display/undisplay
            pmvcmd = self.vf.displayMSMS
            # MS sept 2011: calling doit reduces memory leak and speeds up
            # but we lose undo capability
            #pmvcmd.doit(atoms, negate=not val, surfName=name)
            pmvcmd(atoms, negate=not val, callListener=False, surfName=name)

            #mem2 = misc.memory()
            #print "MSMS %4.2f %4.2f %4.2f %4.2f %4.2f"%(
            #    (mem1-mem0)/MB, (mem2-mem1)/MB, mem0/MB, mem1/MB, mem2/MB)


    # override MSMScol.optMenu_cb
    def optMenu_cb(self, node, column, event=None):
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()

        # get status of clicked button (1:full, 0:empty or partial)
        #val = node.chkbtval[column]
        #if val==1: # button is on --> right click does nothing
        #    return
        
        cmd = self.vf.computeMSMS
        self.setForLabel(node)

        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, column))

        if isinstance(node, SelectionWithButtons):
            # not a molecule but a set
            name = 'surface_%s'% str(node).replace(' ', '_')
            name = name.replace('_','-')
        else:
            name = 'MSMS-MOL'
        
        master = self.vf.dashboard.master3

        self.form = cmd.showForm(
            posx=event.x_root, posy=event.y_root, root=master,
            okcancel=0, help=0, modal=0, blocking=0,
            postCreationFunc=self.vf.dashboard.expandParams)
        
        cb = CallbackFunction(self.Apply_cb, cmd, node, column)
        self.vf.dashboard.applyButton.bind('<1>', cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)
        self.vf.dashboard.columnShowingForm = self


    def Apply_cb(self, cmd, node, column, event=None):
        values = self.form.checkValues()
        values = cmd.fixValues(values)
        cmd.lastUsedValues['default'].update(values)
        node.buttonClick(column, val=1) # always call with button on
        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, column))

 
displayMSMSColDescr = MSMSColumnDescriptor(
    'compute/display Molecular Surface', ('displayMSMS', (), {}),
    buttonColors=['white', '#FF4F44'], title='MS',
    color='#333333', pmvCmdsToHandle = [],#'displayMSMS', 'computeMSMS'],
    pmvCmdsToLoad = [('displayMSMS', 'msmsCommands', 'Pmv'),
                     ('computeMSMS', 'msmsCommands', 'Pmv')],
    buttonBalloon='Display/Undisplay molecular surface for %s',
    onButtonBalloon='display molecular surface for %s',
    offButtonBalloon='undisplay molecular surface for %s',
    geomNames=['MSMS-MOL'],
    )
ColumnDescriptors.append(displayMSMSColDescr)
   

from mglutil.gui.BasicWidgets.Tk.colorWidgets import ColorChooser

class ColorColumnDescriptor(MVColumnDescriptor):
    """
    Column with a menu when I click on a button
    """
    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        self.onOnly = self.execute
        self.cbOn = self.execute
        self.cbOff = None
        self.carbonOnly = Tkinter.IntVar()
        self.widgets = []
        self.form = None
        self.leveloptions = None
        self.node = None
        self.colInd = None
        

    def setAllGeomButtons(self, event=None):
        # copy the state of the allGeomsVar variable to all variable
        # used for the list of visible geoemtries 
        value = self.allGeomsVar.get()
        for var in self.geomsVar.values():
            var.set(value)

            
    def execute(self, node, colInd, val, event=None):
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()
        if self.form:
            #print "FORM EXISTS -returning", "columnShowingForm:",  self.vf.dashboard.columnShowingForm
            # this is odd:looks like some of the "left mouse clicks" are interpreted as two clicks and
            #this method is called twice simultaneously. The 'columnShowingForm' at this point for the second
            # call is None - the function creates a form that is not working  
            return 

        self.setForLabel(node)
        master = self.vf.dashboard.master3
        self.form = Tkinter.Frame(master)
        self.leftFrame = Tkinter.Frame(self.form)
        self.leftFrame.pack(side='left', expand=1, fill='both', anchor='nw')
        self.rightFrame = Tkinter.Frame(self.form)
        self.rightFrame.pack(side='left', expand=1, fill='both', anchor='ne')
        self.form.pack(expand=1, fill='both')
        obj = node.getObjects(colInd) # what to cmd will apply to
        self.objects = obj
        # get geometries that can be colored
        visibleGeoms = self.getVisibleGeoms(obj)
        
        # handle sticks and balls as a single geom
        if len(visibleGeoms)==1:
            varVal = 1
        elif len(visibleGeoms)==2 and 'sticks' in visibleGeoms.keys() and \
             'balls' in visibleGeoms.keys():
            varVal = 1
        else:
            varVal = 0
            
        self.allGeomsVar = Tkinter.IntVar()
        self.allGeomsVar.set(varVal==1)
        self.geomsVar = {}

        b = Tkinter.Checkbutton(self.leftFrame, text='All Representations',
                                variable=self.allGeomsVar,
                                command=self.setAllGeomButtons)
        #b.grid(column=0, row=0, sticky='w')
        b.pack(side='top', anchor='w')
        self.widgets.append(b)
        
        self.carbonOnly = Tkinter.IntVar()
        caOnlyWidget = Tkinter.Checkbutton(self.leftFrame, text='Carbon only',
                                           variable=self.carbonOnly,
                                           command=self.handleFilterButtons)
        caOnlyWidget.pack(side='top', anchor='w')
        self.widgets.append(caOnlyWidget)
        
        w = self.geomsWidget = Pmw.ScrolledFrame(
            self.leftFrame, labelpos = 'nw', label_text = 'Representations',
            usehullsize = 1,
            hull_width = 150,
            hull_height = 220,
            )
        w.pack(side='top', fill='x', anchor='w')
        for name, geom in visibleGeoms.items():
            v = self.geomsVar[name] = Tkinter.IntVar()
            v.set(varVal)
            cb = CallbackFunction(self.handleCheckButtons, name, geom)
            b = Tkinter.Checkbutton(w.interior(), text=name, variable=v, command=cb)
            b.pack(anchor='w')
            self.widgets.append(b)
            
        colorCommands = [
            'By atom type', 'By polarity (David Goodsell)', 'By molecule', 'By chain',
            'By residue type (Rasmol)', 'By residues type (Shapely)', 'By instance',
            'By rainbow']

        added = False
        for ob in obj.values():
            for o in ob:
                if isinstance(o, MoleculeSet) or isinstance(ob, ProteinSet):
                    colorCommands.append('By rainbow (per chain)')
                    added = True
                    break
            if added is True:
                break
        
        mols = {}
        for ob in obj.values():
            mols.update( {}.fromkeys([o.top for o in ob]) )
            
        for m in mols.keys():
            if hasattr(m, 'builder'): # there is a ribbon
                colorCommands.append('By secondary structure')
                break
        self.vf.dashboard.geomAppearanceWidget.setGeoms(self.getGeoms( node, colInd))
        # add color command that work with carbon only
        colorCommands.append('Custom color')
        colorCommands.append('By property')
        cb = CallbackFunction(self.Apply_cb, node, colInd)
        self.colorSchemesWidget = Pmw.ComboBox(
            self.rightFrame,
            label_text = 'Coloring schemes:',
            labelpos = 'nw',
            #selectioncommand = self.changeText,
            scrolledlist_items = colorCommands,
            dropdown=0,
            selectioncommand=cb
            )
        self.colorSchemesWidget.pack(side='top', expand=1, fill='both', anchor='w')
        #self.colorSchemesWidget.grid(column=1, row=0, rowspan=3, sticky='nesw')
        #self.widgets.append(self.colorSchemesWidget)

        #cb = CallbackFunction(self.Apply_cb, node, colInd)
        # forget the apply button since the applky_cb is called when we click on color scheme
        self.vf.dashboard.applyButton.forget()
        #self.vf.dashboard.applyButton.bind('<1>', cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)

        self.vf.dashboard.expandParams(self.form)
        self.vf.dashboard.columnShowingForm = self

        
    def Close_cb(self, event=None):
        if 'By property' in self.vf.dashboard.paramsNB.pagenames():
            self.vf.dashboard.paramsNB.delete('By property')
            self.vf.dashboard.paramsNB.selectpage('Basic')
        for w in self.widgets: w.destroy()
        self.form.destroy()
        self.form = None
        self.vf.dashboard.closeButton.forget()
        self.vf.dashboard.applyButton.pack(side='left', fill='x', expand=1)
        self.vf.dashboard.closeButton.pack(side='left', fill='x', expand=1)
        #self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()


    def Apply_cb(self, node, colInd, event=None):
        if not node:
            node = self.node
            colInd = self.colInd
        else:
            self.node = node
            self.colInd = colInd
            
        obj = node.getObjects(colInd) # what to cmd will apply to
        colorScheme = self.colorSchemesWidget.get()
        if colorScheme=='By atom type':
            self.color_cb(self.vf.colorByAtomType, obj)
        elif colorScheme=='By polarity (David Goodsell)':
            self.color_cb(self.vf.colorAtomsUsingDG, obj)
        elif colorScheme=='By molecule':
            self.color_cb(self.vf.colorByMolecules, obj)
        elif colorScheme=='By chain':
            self.color_cb(self.vf.colorByChains, obj)
        elif colorScheme=='By residue type (Rasmol)':
            self.color_cb(self.vf.colorByResidueType, obj)
        elif colorScheme=='By residues type (Shapely)':
            self.color_cb(self.vf.colorResiduesUsingShapely, obj)            
        elif colorScheme=='By instance':
            self.color_cb(self.vf.colorByInstance, obj)            
        elif colorScheme=='By rainbow':
            self.color_cb(self.vf.colorRainbow, obj)
        elif colorScheme=='By rainbow (per chain)':
            self.color_cb(self.colorChainsByRainbow, obj)
        elif colorScheme=='Custom color':
            self.colorChooser_cb(node, colInd)
        elif colorScheme=='By secondary structure':
            self.color_cb(self.vf.colorBySecondaryStructure, obj)
        elif colorScheme=='By property':
            if 'By property' not in self.vf.dashboard.paramsNB.pagenames():
                self.addByPropertyPage(obj)
            self.vf.dashboard.paramsNB.selectpage('By property')

        # redraw node in dashboard to reflect coloring
        ypos = node.nodeRedraw()
        
    def handleFilterButtons(self):
        conly = self.carbonOnly.get()
        if conly:
            clist = []
        else:
            clist = ['By atom type', 'By polarity (David Goodsell)']
        clist.extend( ['By molecule', 'By chain',
                       'By residue type (Rasmol)',
                       'By residues type (Shapely)',
                       'By instance', 'By rainbow',
                       'By rainbow (per chain)',
                       'By secondary structure',
                       'Custom color'] )
        self.colorSchemesWidget.component('scrolledlist').setlist(clist)


    def handleCheckButtons(self, name, geom):
        #geoms= self.getGeoms( node, colInd)
        checked = self.geomsVar[name].get()
        geoms = self.vf.dashboard.geomAppearanceWidget.geoms
        if geom not in geoms:
            if checked:
                geoms.append(geom)
        else:
            if not checked:
                geoms.remove(geom)
        self.vf.dashboard.geomAppearanceWidget.setGeoms(geoms)
        colorScheme = self.colorSchemesWidget.get()
        # if there is a selection in colorChemes list and the geom button is checked,
        # execute the color command
        if colorScheme and checked:
            self.Apply_cb(None, None)
        #print "geoms:", geoms, colorScheme
        
        

    def colorChooser_cb(self, node, colInd):
        objects = node.getObjects(colInd) # what to cmd will apply to
        geomsToColor=[k for k,v in self.geomsVar.items() if v.get()]
        if len(geomsToColor)==0:
            # repost menu in same location
            #self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())
            return

        def cb(color, node=node, colInd=colInd):
            objects = node.getObjects(colInd) # what to cmd will apply to
            #if objects=='selection':
            #    objects = self.vf.getSelection()
            for node, objlist in objects.items():
                for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                    if len(obj)==0: continue
                    if self.carbonOnly.get():
                        #obj = obj.findType(Atom).get('C*')
                        obj = AtomSet(
                            [x for x in obj.findType(Atom) if x.element=='C'])
                    self.vf.color(obj, [color], geomsToColor)

        name = str([str(o) for o in objects.keys()])
        cc = ColorChooser(immediate=1, commands=cb,
                          title='Color %s for %s'%(str(geomsToColor), name))

        cc.pack(expand=1, fill='both')


    def color_cb(self, cmd, objects):
        geomsToColor=[k for k,v in self.geomsVar.items() if v.get()]
        if len(geomsToColor)==0:
            # repost menu in same location
            #self.menu.post(self.menu.winfo_x(), self.menu.winfo_y())
            return
        for node, objlist in objects.items():
            for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(obj)==0: continue

                if cmd not in [self.vf.colorByAtomType,
                               self.vf.colorAtomsUsingDG,
                               self.vf.colorBySecondaryStructure] and \
                               self.carbonOnly.get():
                    #obj = obj.findType(Atom).get('C*')
                    obj = AtomSet(
                        [x for x in obj.findType(Atom) if x.element=='C'])
                    
                if cmd == self.vf.colorByProperty:
                    vals = self.checkFormValues()

                    prop = vals['property']
                    if not len(prop):return
                    prop = prop[0]
                    
                    propLevel = vals['propertyLevel']
                    obj = obj.findType(self.vf.selectionLevel)
                    cmd(obj, geomsToColor, prop, propertyLevel=propLevel,
                        mini=vals['mini'], maxi=vals['maxi'])
                    # Show the colormapeditor
                    if vals['edit']:
                        self.vf.showCMGUI(cmap='rgb256', topCommand=0)
                        cmg = self.vf.showCMGUI.cmg
                        cm =  self.vf.colorMaps['rgb256']
                        cm.configure(mini=vals['mini'], maxi=vals['maxi']) 
                        func =  CallbackFunction(cmd.cmGUI_cb, geomsToColor,
                                    prop, propertyLevel=propLevel, nodes=obj)
                        #cmg.addCallback(func)
                        if not len(cmg.callbacks):
                            cmg.addCallback(func)
                        else:
                            cmg.callbacks=[func]
                        
                else:
                    cmd(obj, geomsToColor=geomsToColor)
        

    def colorChainsByRainbow(self, obj, geomsToColor=None):
        if hasattr(obj, 'chains'):
            for chain in obj.chains:
                self.vf.colorRainbow(chain, geomsToColor=geomsToColor)
        else:
            chains = obj.findType(Chain).uniq()
            for c in chains:
               atms = c.findType(Atom) & obj.findType(Atom)
               self.vf.colorRainbow(atms, geomsToColor=geomsToColor)
            

    def getVisibleGeoms(self, objects):
        geoms = {}
        for node, objlist in objects.items():
            for objs in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(objs)==0: continue

                for ob in objs:
                    gc = ob.top.geomContainer
                    for name, ats in gc.atoms.items():
                        if gc.geoms.has_key(name) and gc.geoms[name].visible \
                               and len(ats):
                            if name[:4] in ['Heli', 'Stra', 'Turn', 'Coil']:
                                #geoms['secondarystructure'] = True
                                geoms['secondarystructure'] = gc.geoms[name]
                            elif name in ['bonded', 'nobnds', 'bondorder']:
                                #geoms['lines'] = True
                                geoms['lines'] = gc.geoms[name]
                            else:
                                #geoms[name] = True
                                geoms[name] = gc.geoms[name]
        return geoms

    def updateRepresentations(self):
        # this is called by dashboardCommand.handleEditGeom() (when a geometry is displayed/undisplayed)
        #print "objects:", self.objects
        obj = self.objects
        visibleGeoms = self.getVisibleGeoms(obj)
        if len(visibleGeoms) != len(self.geomsVar):
            buttons = self.geomsWidget.interior().children.values()
            for b in buttons:
                if b in self.widgets:
                    self.widgets.remove(b)
                    b.destroy()
            self.geomsVar = {}
            if len(visibleGeoms)==1:
                varVal = 1
            elif len(visibleGeoms)==2 and 'sticks' in visibleGeoms.keys() and \
                     'balls' in visibleGeoms.keys():
                varVal = 1
            else:
                varVal = 0
            for name, geom in visibleGeoms.items():
                #print geom
                if name == "secondarystructure":
                    colorBy = list(self.colorSchemesWidget.get(0, "end"))
                    if "By secondary structure" not in colorBy:
                        colorBy.append('By secondary structure')
                        #print colorBy
                        self.colorSchemesWidget.component('scrolledlist').setlist(colorBy)
                v = self.geomsVar[name] = Tkinter.IntVar()
                v.set(varVal)
                cb = CallbackFunction(self.handleCheckButtons, name,  geom)
                b = Tkinter.Checkbutton(self.geomsWidget.interior(), text=name, variable=v,
                                        command=cb)
                b.pack(anchor='w')
                self.widgets.append(b)


    def addByPropertyPage(self, obj):
        byProperty = self.vf.dashboard.paramsNB.insert('By property', before=1)
        self.form1 = f1 = Tkinter.Frame(byProperty)
        self.form1.pack(expand=1, fill='both')
        self.leftFrame = Tkinter.Frame(f1)#(byProperty)
        self.leftFrame.pack(side='left', expand=1, fill='both', anchor='nw')
        self.rightFrame = Tkinter.Frame(f1)#(byProperty)
        self.rightFrame.pack(side='left', expand=1, fill='both', anchor='ne')
        #add level radio buttons
        self.levelGroup = Pmw.Group(self.leftFrame, tag_text='Level')
        #self.levelGroup.pack(expand=1, fill='x')
        self.levelGroup.pack(expand=1, fill='both')
        level = {Molecule:'Molecule', Atom:'Atom', Residue:'Residue',
                         Chain:'Chain'}[self.vf.selectionLevel]
        self.levelRB = w = Pmw.RadioSelect(self.levelGroup.interior(),
                                           orient = 'vertical', #'horizontal'
                                           buttontype = 'radiobutton',
                                           command=self.setLevel, pady=1)
        if not self.leveloptions:
            self.leveloptions = {}
            from mglutil.util.colorUtil import ToHEX
            for name in  ['Atom', 'Residue', 'Chain', 'Molecule']:
                col = self.vf.ICmdCaller.levelColors[name]
                bg = ToHEX((col[0]/1.5,col[1]/1.5,col[2]/1.5))
                ag = ToHEX(col)
                self.leveloptions[name]= {'activebackground':bg, 'selectcolor':ag,
                                          'borderwidth':1}
        for name  in ['Atom', 'Residue', 'Chain', 'Molecule']:
            w.add(name, **self.leveloptions[name])
        w.setvalue(level)
        self.levelRB.pack(side='top')
        self.mini = 0.0
        self.maxi = 0.0
        self.minEntry = w = Pmw.EntryField(self.leftFrame, entry_width=10,
                            labelpos='w', label_text='0.0 Min',
                            validate={'validator':'real'}, value=0.0,
                            )
                            #validate=self.minMaxValidate,  )
        w.pack(side='top', anchor='e')
        self.maxEntry = w = Pmw.EntryField(self.leftFrame, entry_width=10,
                             labelpos='w', label_text='0.0 Max',
                             validate={'validator':'real'}, value=0.0,
                             )
                             #validate=self.minMaxValidate)
        w.pack(side='top', anchor='e')
        
        self.editVar = Tkinter.IntVar()
        self.editVar.set(0)
        b = Tkinter.Checkbutton(self.leftFrame, text='Edit', variable=self.editVar)
        b.pack(side='top', anchor='e')
        
        cmd = self.tree.vf.colorByProperty
        cb =  CallbackFunction(self.color_cb, cmd, obj)
        b = Tkinter.Button(self.leftFrame, text='Apply', command=cb)
        b.pack(side = 'top', fill = 'x', padx = 3, pady = 3)
        cb = CallbackFunction(self.updateValMinMax_cb, obj, cmd)
        self.propList = Pmw.ScrolledListBox(self.rightFrame,
            label_text = 'Select property', labelpos = 'nw',
            selectioncommand = cb,
            usehullsize = 1, hull_width = 150, hull_height = 200,
            horizscrollbar_width=7, vertscrollbar_width=7)
        self.setLevel(level)
        self.propList.pack(padx=3, pady=3,  expand=1, fill='both', )
        

    def setLevel(self, level='Atom'):
        self.level=level
        #print level
        levelDict =  {'Atom':(Atom, AtomSet) , 'Residue':(Residue,ResidueSet), 'Chain':(Chain , ChainSet),
                      'Molecule': (Molecule, MoleculeSet)}
        levelClass = levelDict[level][0]
        levelSetClass = levelDict[level][1]
        elements = levelSetClass([])
        for node, sets in self.objects.items():
            for obj in sets:
                elements += obj.findType(levelClass).uniq()
        props = [x[0] for x in elements[0].__dict__.items() if (
            x[0][0]!='_' and isinstance(x[1], (int, float)))]

        if hasattr(elements[0], 'chargeSet') and elements[0].chargeSet:
            props.append('charge')
            
        props.sort()
        self.propList.setlist(props)


    def getGeoms(self, node, colInd):
        objects = node.getObjects(colInd)
        visgeoms = self.getVisibleGeoms(objects)
        geomNames = [k for k,v in self.geomsVar.items() if v.get()]
        geoms = []
        for name, geom in visgeoms.items():
            if name in geomNames:
                geoms.append(geom)
        return geoms


    def checkFormValues(self):
        values = {}
        values['propertyLevel'] = self.levelRB.getvalue()
        values['property'] = self.propList.getcurselection()
        try:
            values['mini'] = float(self.minEntry.getvalue())
        except:
            values['mini'] = None
        try:
            values['maxi'] = float(self.maxEntry.getvalue())
        except:
            values['maxi'] = None
        values['edit'] = self.editVar.get()
        return values

        
    def updateValMinMax_cb(self, objects, cmd):
        prop = self.propList.getcurselection()
        if not len(prop):
            return
        propValues = None
        mini = 0
        maxi = 0
        for node, objlist in objects.items():
            for obj in objlist: # each node has [AtomSet, ResidueSet, ...]
                if len(obj)==0:continue
                level = self.levelRB.getvalue()
                #print "LEVEL:", level
                cmd.getPropValues(obj, prop[0], level)
                propValues = cmd.propValues
                if propValues is not None:
                    mini = min(propValues)
                    maxi = max(propValues)
                self.mini = mini
                self.maxi = maxi
                self.minEntry.setvalue(mini)
                self.maxEntry.setvalue(maxi)
                #labels:
                if type(mini) == int:
                    self.minEntry.configure(label_text='%d Min'% mini)
                elif type(mini) == float:
                    self.minEntry.configure(label_text='%.2f Min'% mini)
                if type(maxi) == int:
                    self.maxEntry.configure(label_text='%d Max'% maxi)
                elif type(maxi) == float:
                    self.maxEntry.configure(label_text='%.2f Max'% maxi)


    def minMaxValidate(self, text):
        print "validate:", text, "min, max:" , self.mini, self.maxi
        if not text:
            return -1
        try:
            val = string.atof(text)
        except ValueError:
            return 0
        print "value:", val,
        if val<=self.maxi and val>=self.mini:
            print "1"
            return 1
        else:
            print "0"
            return 0
        
##     def postMenu(self, node, colInd, val, event=None):
## ##         tree = self.tree
## ##         if len(tree.selectedNodes)>0:
## ##             tree.clearSelection()
            
##         # called upon right click
##         obj = node.getObjects(colInd) # what to cmd will apply to
## ##         obj = obj[node][0]
## ##         if val==0:
## ##             return
## ##         obj = node.getObjects(colInd) # what to cmd will apply to

## ##         if isinstance(obj, list): # for sets
## ##             obj = obj[0]

##         menu = Tkinter.Menu(tearoff=False)

##         # put entries to select geometry to color
##         visibleGeoms = self.getVisibleGeoms(obj)

##         if len(visibleGeoms)==1:
##             varVal = 1
##         elif len(visibleGeoms)==2 and 'sticks' in visibleGeoms and \
##              'balls' in visibleGeoms:
##             varVal = 1
##         else:
##             varVal = 0
            
##         self.allGeomsVar = Tkinter.IntVar()
##         self.allGeomsVar.set(varVal==1)
##         self.geomsVar = {}

##         menu.add_command(label='Geometry', command=None, state='disable',
##                          font=('Helvetica', 12, 'bold'))
##         if len(visibleGeoms)>1:
##             cb = CallbackFunction( self.handleCheckButtons, 'all')
##             menu.add_checkbutton(label='All Representations',
##                                  variable=self.allGeomsVar,
##                                  command=cb)

##         for geom in visibleGeoms:
##             v = self.geomsVar[geom] = Tkinter.IntVar()
##             v.set(varVal)
##             cb = CallbackFunction( self.handleCheckButtons, geom)
##             menu.add_checkbutton(label=geom, variable=v, command=cb)

##         menu.add_separator()

##         menu.add_command(label='Filter', command=None, state='disable',
##                          font=('Helvetica', 12, 'bold'))
##         # add check button  for carbon only
##         #cb = CallbackFunction( menu.post, event.x_root, event.y_root)
##         menu.add_checkbutton(label='Carbon only', variable=self.carbonOnly,
##                              command=self.handleFilterButtons)

##         menu.add_separator()
##         # add color command unaffected by carbon only

##         menu.add_command(label='Color Scheme', command=None, state='disable',
##                          font=('Helvetica', 12, 'bold'))

##         cb = CallbackFunction( self.color_cb, self.vf.colorByAtomType, obj )
##         menu.add_command(label='By atom type', command=cb)

##         cb = CallbackFunction( self.color_cb, self.vf.colorAtomsUsingDG, obj )
##         menu.add_command(label='By polarity (David Goodsell)', command=cb)

##         cb = CallbackFunction( self.color_cb, self.vf.colorByMolecules, obj )
##         menu.add_command(label='By molecule', command=cb)

##         cb = CallbackFunction( self.color_cb, self.vf.colorByChains, obj )
##         menu.add_command(label='By chain', command=cb)

##         cb = CallbackFunction( self.color_cb, self.vf.colorByResidueType, obj )
##         menu.add_command(label='By residue type (Rasmol)', command=cb)

##         cb = CallbackFunction( self.color_cb, self.
##                                vf.colorResiduesUsingShapely, obj )
##         menu.add_command(label='By residues type (Shapely)', command=cb)

##         cb = CallbackFunction( self.color_cb, self.vf.colorByInstance, obj )
##         menu.add_command(label='By instance', command=cb)

##         cb = CallbackFunction( self.color_cb, self.vf.colorRainbow, obj)
##         menu.add_command(label='By rainbow', command=cb)

##         added = False
##         for ob in obj.values():
##             for o in ob:
##                 if isinstance(o, MoleculeSet) or isinstance(ob, ProteinSet):
##                     cb = CallbackFunction( self.color_cb,
##                                            self.colorChainsByRainbow, obj)
##                     menu.add_command(label='By rainbow (per chain)', command=cb)
##                     added = True
##                     break
##             if added is True:
##                 break

##         mols = {}
##         for ob in obj.values():
##             mols.update( {}.fromkeys([o.top for o in ob]) )
            
##         for m in mols.keys():
##             if hasattr(m, 'builder'): # there is a ribbon
##                 cb = CallbackFunction( self.color_cb,
##                                        self.vf.colorBySecondaryStructure, obj )
##                 menu.add_command(label='By secondary structure', command=cb)
##                 break
            
##         # add color command that work with carbon only
##         cb = CallbackFunction( self.colorChooser_cb, obj)
##         menu.add_command(label='Custom color', command=cb)


##         menu.add_separator()
        
##         menu.add_command(label='Dismiss')

##         menu.post(event.x_root, event.y_root)
##         self.menu = menu
##         self.enableDisableColorCmdEntries()


    def optMenu_cb(self, node, column, event=None):
        pass # to avoid traceback on color menu right click

    
    def displayOptions(self, cmd, obj, event):
        values = cmd.showForm(posx=event.x_root, posy=event.y_root,
                              master=self.tree.master)
        if values and len(values)==0: return # Cancel was pressed
        cmd.lastUsedValues['default'].update(values)
        cmd( *(obj,), **values)

         

colorMenuColDescr = ColorColumnDescriptor(
    'color', [None], buttonColors=['white', 'white'],
    buttonShape='downTriangle',
    inherited=False, title='Cl',
    iconfile='dashboardColorIcon.jpg',
    buttonBalloon="""display coloring menu for representations of %s""",
)
ColumnDescriptors.append(colorMenuColDescr)



class LabelColumnDescriptor(MVColumnDescriptor):
    """
    Column with a menu when I click on a button
    """
    def __init__(self, name, cmd, **kw):

        MVColumnDescriptor.__init__(self, name, cmd, **kw)
        self.onOnly = self.execute
        self.cbOn = self.execute
        self.cbOff = None # self.postMenu # nothing on right click 
        #self._propVars = {Atom:{}, Residue:{}, Chain:{}, Molecule:{}}
        self.propLevel = None
        self.widgets = []
        self.currentLevel = 'Residue'
        self.frequentProps = {
            Atom:['autodock_element', 'charge', 'coords', 'element', 'name',
                  'number', 'occupancy', 'temperatureFactor', 'type', 'custom'],
            Residue:['name', 'number', 'type', 'custom'],
            Chain:['id', 'number', 'custom'],
            Molecule:['name', 'number', 'custom']
            }
        
        self.fontList = [
            'arial1.glf', 'courier1.glf', 'crystal1.glf', 'techno0.glf',
            'techno1.glf', 'times_new1.glf', 'aksent1.glf', 'alpine1.glf',
            'broadway1.glf', 'chicago1.glf', 'compact1.glf', 'cricket1.glf',
            'garamond1.glf', 'gothic1.glf', 'penta1.glf', 'present_script1.glf']

        self.fontStyleDict = {
            'solid':   glf.glfDrawSolidString,
            'solid3d': glf.glfDraw3DSolidString,
            'wire':   glf.glfDrawWiredString,
            'wire3d': glf.glfDraw3DWiredString,
            }
        self.fontStyleList = self.fontStyleDict.keys()
        self.shiftLabelEditorDialog = None
        self.labelEditorDialog = None
        self.labelEditorDialogVisible = False

    
    def optMenu_cb(self, node, column, event=None):
        pass # to avoid traceback on color menu right click
    


    def execute(self, node, colInd, val, event=None):

        #self.postMenu(node, colInd, label=True)
        if self.vf.dashboard.columnShowingForm:
            self.vf.dashboard.columnShowingForm.Close_cb()

        self.setForLabel(node)

        self._propVars = {Atom:[], Residue:[], Chain:[], Molecule:[]}

        master = self.vf.dashboard.master3
        self.form = Tkinter.Frame(master)
        self.leftFrame = Tkinter.Frame(self.form)
        self.leftFrame.pack(side='left', expand=1, fill='both', anchor='nw')
        self.rightFrame = Tkinter.Frame(self.form)
        self.rightFrame.pack(side='left', expand=1, fill='both', anchor='ne')
        self.form.pack(expand=1, fill='both')

        obj = node.getObjects(colInd) # what to cmd will apply to
        self.objects = obj
        self.colInd = colInd
        self.node = node
        
        # Create and pack a vertical RadioSelect widget for the level
        self.levelW = Pmw.RadioSelect(
            self.leftFrame, orient = 'vertical', labelpos = 'nw',
            command = self.setLevel, label_text = 'Level',
            frame_borderwidth = 2, frame_relief = 'ridge'
        )
        self.levelW.pack(fill = 'x', padx = 10, pady = 10)
        for text in ('Atom', 'Residue', 'Chain', 'Molecule'):
            self.levelW.add(text)

        # create a button to clear label at the current level
        self.clearLabW = Tkinter.Button(self.leftFrame,
            text='Clear Labels', command=self.clearLabels)
        self.clearLabW.pack(fill = 'x', padx = 5, pady = 5)
        
        # create a checkbutton to show all properties
        v = self.showAllTk = Tkinter.IntVar()
        self.showAllTk.set(0)
        b = Tkinter.Checkbutton(self.rightFrame, text='Show all properties',
                                variable=v, command=self.toggleAllProp)
        b.pack(fill = 'x')#, padx = 5, pady = 5)

        # create a scrolled frame for properties with buttons
        self.propWidget = Pmw.ScrolledFrame(
            self.rightFrame, labelpos = 'nw', label_text = 'Properties',
            usehullsize = 1,
            hull_width = 150,
            hull_height = 220,
            )
        self.propWidget.pack(fill='both', expand=1, anchor='w')

        self.levelW.invoke(self.currentLevel)

        geoms = []
        for mol, elements in zip(self.molecules, self.sets):
            if isinstance(elements, ListSet):
                geomName = elements[0].__class__.__name__+'Labels'
            else:
                geomName = elements.__class__.__name__+'Labels'
            # find the geometry to use, for atoms, label, chains or protein
            labelGeom = mol.geomContainer.geoms[geomName]
            geoms.append(labelGeom)
            
        self.vf.dashboard.geomAppearanceWidget.setGeoms(geoms)

        ##
        ## now add a panel with label properties
        ##
        for mol, elements in zip(self.molecules, self.sets):
            if isinstance(elements, ListSet):
                geomName = elements[0].__class__.__name__+'Labels'
            else:
                geomName = elements.__class__.__name__+'Labels'
            # find the geometry to use, for atoms, label, chains or protein
            labelGeom = mol.geomContainer.geoms[geomName]
            break
        
        advanced = self.vf.dashboard.paramsNB.insert('Advanced', before=1)

        f = Tkinter.Frame(advanced)
        # billboard button
        self.billboardVar = Tkinter.IntVar()
        self.billboardVar.set(labelGeom.billboard)
        self.billboardTk = Tkinter.Checkbutton(
            f, text='billboard', variable=self.billboardVar,
            command=self.setFontOpts)
        self.billboardTk.grid(column=0, row=0, columnspan=2, sticky='w')

        # font and style combos
        # font
        self.guiFontComboBox = Pmw.ComboBox(
            f, #label_text='font', labelpos='w',
            entryfield_value=labelGeom.font,
            entryfield_entry_width=15, scrolledlist_items=self.fontList,
            selectioncommand=self.setFontOpts)
        self.guiFontComboBox.grid(column=0, row=1, columnspan=2, sticky='ew')

        # font style
        self.guiFontStyleComboBox = Pmw.ComboBox(
            f, #label_text='style', labelpos='w',
            entryfield_value=labelGeom.fontStyle, entryfield_entry_width=3,
            scrolledlist_items=self.fontStyleList,
            selectioncommand=self.setFontOpts)
        self.guiFontStyleComboBox.grid(column=2, row=1, columnspan=2, sticky='ew')
        
        # font spacing
        self.guiSpacing = ThumbWheel(
            f, labCfg={'text':'Spacing', 'side':'left'},
            showLabel=1,  width=70, height=20, min=0, type=float,
            value=labelGeom.fontSpacing, callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiSpacing.grid(column=0, row=2, columnspan=2, sticky='ew', pady=5)
        
        # font global scale
        self.guiGlobalScale = ThumbWheel(
            f, labCfg={'text':'Scale', 'side':'left'},
            showLabel=1, width=70, height=20, min=0, type=float,
            value=1.0, callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiGlobalScale.grid(column=2, row=2, columnspan=2, sticky='ew', pady=5)
        
        # font scale X
        Tkinter.Label(f, text='Stretch ').grid(column=0, row=3, sticky='w')
        self.guiScaleX = ThumbWheel(
            f, labCfg={'text':'X', 'side':'left'},
            showLabel=1, width=60, height=20, min=0, type=float,
            value=labelGeom.fontScales[0], callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiScaleX.grid(column=1, row=3, sticky='ew')

        # font scale Y
        self.guiScaleY = ThumbWheel(
            f, labCfg={'text':'Y', 'side':'left'},
            showLabel=1, width=60, height=20, min=0, type=float,
            value=labelGeom.fontScales[1], callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiScaleY.grid(column=2, row=3, sticky='ew')

        # font scale Z
        self.guiScaleZ = ThumbWheel(
            f, labCfg={'text':'Z', 'side':'left'},
            showLabel=1, width=60, height=20, min=0, type=float,
            value=labelGeom.fontScales[2], callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiScaleZ.grid(column=3, row=3, sticky='ew')
        
        ## SHIFT label
        Tkinter.Label(f, text='Shift ').grid(column=0, row=4, sticky='w')
        # font Translate X
        self.guiTranslateX = ThumbWheel(
            f, labCfg={'text':'X', 'side':'left'},
            showLabel=1, width=60, height=20, type=float,
            value=labelGeom.fontTranslation[0], callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiTranslateX.grid(column=1, row=4, sticky='ew')

        # font Translate Y
        self.guiTranslateY = ThumbWheel(
            f, labCfg={'text':'Y', 'side':'left'},
            showLabel=1, width=60, height=20, type=float,
            value=labelGeom.fontTranslation[1], callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiTranslateY.grid(column=2, row=4, sticky='ew')

        # font Translate Z
        self.guiTranslateZ = ThumbWheel(
            f, labCfg={'text':'Z', 'side':'left'},
            showLabel=1, width=60, height=20, type=float,
            value=labelGeom.fontTranslation[2], callback=self.setFontOpts,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiTranslateZ.grid(column=3, row=4, sticky='ew')

        ## Rotation label
        Tkinter.Label(f, text='Rotate ').grid(column=0, row=5, sticky='w')
        # font Rotate X
        self.guiRotateX = ThumbWheel(
            f, labCfg={'text':'X', 'side':'left'},
            showLabel=1, width=60, height=20, type=float, min=-180, max=180,
            value=labelGeom.fontRotateAngles[0], callback=self.setFontOpts,
            continuous=True, oneTurn=90, wheelPad=2)
        self.guiRotateX.grid(column=1, row=5, sticky='ew')

        # font Rotate Y
        self.guiRotateY = ThumbWheel(
            f, labCfg={'text':'Y', 'side':'left'},
            showLabel=1, width=60, height=20, type=float, min=-180, max=180,
            value=labelGeom.fontRotateAngles[1], callback=self.setFontOpts,
            continuous=True, oneTurn=90, wheelPad=2)
        self.guiRotateY.grid(column=2, row=5, sticky='ew')
        
        # font Rotate Z
        self.guiRotateZ = ThumbWheel(
            f, labCfg={'text':'Z', 'side':'left'},
            showLabel=1, width=60, height=20, type=float, min=-180, max=180,
            value=labelGeom.fontRotateAngles[2], callback=self.setFontOpts,
            continuous=True, oneTurn=90, wheelPad=2)
        self.guiRotateZ.grid(column=3, row=5, sticky='ew')

        f.pack(fill='x')

        # add button to shift individual labels
        self.shiftLabelsVar = Tkinter.IntVar()
        self.shiftLabelsVar.set(0)
        self.shiftLabelsTk = Tkinter.Checkbutton(
            advanced, text='Shift individual labels', variable=self.shiftLabelsVar,
            command=self.shiftLabelsPanel_cb)
        self.shiftLabelsTk.pack(side='left')
        
        self.vf.dashboard.hideApplyButton()
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)

        self.vf.dashboard.expandParams(self.form)
        self.vf.dashboard.columnShowingForm = self


    def setLabelGeom(self, obj, geomName):
        classNames = ['Atom','Residue','Chain','Protein']
        setClass = [AtomSet, ResidueSet, ChainSet, ProteinSet]
        geomC = obj.geomContainer
        for ind, className in enumerate(classNames):
            _geomName = className+'Labels'
            if _geomName == geomName:
                if not geomC.atoms.has_key(geomName):        
                    geomC.atoms[geomName] = setClass[ind]([])
                    geomC.atomPropToVertices[geomName] = self.atomPropToVertices
                    for atm in obj.allAtoms:
                        atm.colors[geomName] = (1.0, 1.0, 1.0)
                        atm.opacities[geomName] = 1.0
                if not geomC.geoms.has_key(geomName):
                    j = ind + 1
                    g = GlfLabels(geomName, fontStyle='solid3d',
                            fontTranslation=(0,0,3.), fontScales=(j*.3,j*.3, .1),
                            visible=0, pickable=0,
                                  )
                    geomC.addGeom(g, parent=geomC.masterGeom,redo=0)
                    g.applyStrokes()
                break


    def atomPropToVertices(self, geom, atoms, propName, propIndex=None):
        if len(atoms)==0: return None
        geomName = string.split(geom.name,'_')[0]
        prop = []
        if propIndex is not None:
            if not isinstance(atoms[0], Atom):
                 for x in atoms:
                     a = x.findType(Atom)[0]
                     d = getattr(a, propName)
                     prop.append(d[propIndex])
            else:
                for a in atoms:
                    d = getattr(a, propName)
                    prop.append(d[propIndex])

        else:
            if not isinstance(atoms[0], Atom):
                for x in atoms:
                    a = x.findType(Atom)[0]
                    prop.append( getattr(a, propName) )
            else:
                for a in atoms:
                    prop.append( getattr(a, propName) )
        return prop
    ##
    ## methods used to shift indvidual labels
    ##
    def endShiftDialog(self, result):
        self.shiftLabelsVar.set(0)
        if result=='Cancel':
            self.currentGeom.Set(labelTranslation=self.origOffset)
        self.shiftLabelEditorDialog.deactivate(result)
        self.shiftLabelEditorDialog.destroy()
        self.shiftLabelEditorDialog = None
        
        del self.origOffset
        del self.currentOffset
        del self.currentGeom

        
    def shiftLabelsPanel_cb(self,event=None):
        if self.currentSelection:
            # refresh self.molecules and self.sets
            self.setLevel(self.currentLevel)

        for mol, toshift in zip(self.molecules, self.sets):
            self.shiftLabelsPanel(mol, toshift)
           
    def setAll(self):
        val = self.selAllVar.get()
        for v in self.labelEntries:
            if v is not None:
                v.set(val)
        self.setCurrentOffset()

        
    def setCurrentOffset(self, event=None):
        self.currentOffest = self.currentGeom.labelTranslation.copy()
        self.guiTransLabX.set(0, update=0)
        self.guiTransLabY.set(0, update=0)
        self.guiTransLabZ.set(0, update=0)


    def resetOffset(self, atoms, adict):
        i = 0
        off = self.currentGeom.labelTranslation
        for v, at in zip(self.labelEntries, atoms):            
            if adict.has_key(at) and v and v.get(): #This atom is in the current set               
                off[i] = (0.2,0.2,0.2)
            i += 1
        self.currentGeom.Set(labelTranslation=off)
        self.setCurrentOffset()


    def shiftLabelsPanel(self, mol, toshift):

        if self.shiftLabelEditorDialog:
            self.endShiftDialog("Cancel")
        var = self.shiftLabelsVar.get()
        if var == 0:
            return
        if self.labelEditorDialogVisible:
            self.endDialog("Cancel")
        geomName = toshift[0].__class__.__name__+'Labels'
        geom = mol.geomContainer.geoms[geomName]
        if len(geom.getVertices())==0:
            level = toshift[0].__class__.__name__
            dialog = Pmw.MessageDialog(
                parent=self.vf.master,
                title = 'No label at the %s level'%level,
                defaultbutton = 0,
                buttons = ('OK',),
                message_text = 'No labels are currently displayed at the %s level\nUse the Basic panel to select a level with displayed labels'%level)
            dialog.iconname('No labels dialog')
            result = dialog.activate()
            self.shiftLabelsVar.set(0)
            return 
        labeled = mol.geomContainer.atoms[geomName]
        self.adict = adict = {}.fromkeys(toshift)
        # get original offset vector
        
        self.currentGeom = geom
        
        if geom.labelTranslation is None:
            off = numpy.zeros( (len(geom.labels), 3), 'f')
            geom.Set(labelTranslation = off.copy())
        else:
            off = geom.labelTranslation
        self.origOffset = off
        self.currentOffset = self.origOffset.copy()
        
        # build dialog
        
        self.shiftLabelEditorDialog = Pmw.Dialog(
	    buttons = ('OK', 'Cancel',), defaultbutton = 'OK',
	    title = 'Shift individual labels for %s'%geom.fullName, command=self.endShiftDialog)
        master1 = self.shiftLabelEditorDialog.interior()

        f = Tkinter.Frame(master1)
        # checkbutton to select/deselect all label
        self.selAllVar = Tkinter.IntVar()
        b = Tkinter.Checkbutton(f, text='Select all', command=self.setAll, highlightthickness=1,
                                highlightcolor='black',highlightbackground='black',variable=self.selAllVar)
        b.pack(side='left', padx=3,pady=1)

        # button to reset offset for selected label
        cb = CallbackFunction(self.resetOffset, labeled, adict)
        b = Tkinter.Button(f, text='Reset offset for selected label', command=cb, highlightthickness=1,
                           highlightcolor='black',highlightbackground='black')
        b.pack(side='left', padx=3,pady=1)
        
        f.pack(fill='x',pady=3)

	sf = Pmw.ScrolledFrame(
            master1, usehullsize = 1, hull_width = 250,  hull_height = 400)

        master = sf.interior()

        self.labelEntries = []
        for at, lab in zip(labeled, geom.labels):
            if adict.has_key(at): #This atom is in the current set               
                v = Tkinter.IntVar()
                v.set(0)
                w = Tkinter.Checkbutton(master, text=lab, variable=v,
                                        command = self.setCurrentOffset)
                w.pack(side='top', anchor='w')
                self.labelEntries.append(v)
            else:
                self.labelEntries.append(None)
                
        sf.pack(fill='both', expand=1, padx=3, pady=3)

        f = Tkinter.Frame(master1)
        # font Translate X
        self.guiTransLabX = ThumbWheel(
            f, labCfg={'text':'X', 'side':'left'},
            showLabel=1, width=60, height=20, type=float,
            value=0., callback=self.setShiftLabels,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiTransLabX.grid(column=0, row=0, sticky='ew')

        # font Translate Y
        self.guiTransLabY = ThumbWheel(
            f, labCfg={'text':'Y', 'side':'left'},
            showLabel=1, width=60, height=20, type=float,
            value=0., callback=self.setShiftLabels,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiTransLabY.grid(column=1, row=0, sticky='ew')

        # font Translate Z
        self.guiTransLabZ = ThumbWheel(
            f, labCfg={'text':'Z', 'side':'left'},
            showLabel=1, width=60, height=20, type=float,
            value=0., callback=self.setShiftLabels,
            continuous=True, oneTurn=1, wheelPad=2)
        self.guiTransLabZ.grid(column=2, row=0, sticky='ew')
        f.pack(fill='x', pady=3)
        self.shiftLabelEditorDialog.activate(globalMode = 'nograb')


    def setShiftLabels(self, event=None):
        geom = self.currentGeom
        if geom.labelTranslation is None:
            off = numpy.zeros( (len(geom.labels), 3), 'f')
        else:
            off = geom.labelTranslation

        dx = self.guiTransLabX.get()
        dy = self.guiTransLabY.get()
        dz = self.guiTransLabZ.get()
        for i, v in enumerate(self.labelEntries):
            if v:
                if v.get():
                    ox, oy, oz = self.currentOffset[i]
                    off[i][0] = ox + dx
                    off[i][1] = oy + dy
                    off[i][2] = oz + dz
                
        geom.Set(labelTranslation = off)
        
    ##
    ## methods used for advanced panel
    ##
    def setFontOpts(self, event=None):
        """
"""
        for mol, elements in zip(self.molecules, self.sets):
            if isinstance(elements, ListSet):
                geomName = elements[0].__class__.__name__+'Labels'
            else:
                geomName = elements.__class__.__name__+'Labels'
            # find the geometry to use, for atoms, label, chains or protein
            labelGeom = mol.geomContainer.geoms[geomName]
            lGlobalScale = self.guiGlobalScale.get()
            self.billboard = self.billboardVar.get()
            self.font = self.guiFontComboBox.get()
            self.fontStyle = self.guiFontStyleComboBox.get()
            labelGeom.Set(#labels=eval(self.labelsEnt.get()),
                billboard = self.billboard,
                #includeCameraRotationInBillboard=self.includeCameraRotationInBillboardVar.get(),
                #lighting=self.lightingVar.get(),
                font=self.font, fontStyle=self.fontStyle,
                fontSpacing=self.guiSpacing.get(),
                fontScales = ( lGlobalScale*self.guiScaleX.get(),
                               lGlobalScale*self.guiScaleY.get(),
                               lGlobalScale*self.guiScaleZ.get() ),
                fontTranslation = ( self.guiTranslateX.get(),
                                    self.guiTranslateY.get(),
                                    self.guiTranslateZ.get() ),
                fontRotateAngles = ( self.guiRotateX.get(),
                                     self.guiRotateY.get(),
                                     self.guiRotateZ.get() ),
                updateOwnGui=True)

        
    ##
    ## methods used for properties list
    ##
    def toggleAllProp(self, event=None):
        self.setLevel(self.currentLevel)

        
    def setLevel(self, level):
        if self.currentSelection:
            # refresh self.molecules and self.sets
            obj = self.node.getObjects(self.colInd) # what to cmd will apply to
            self.objects = obj

        self.currentLevel = level
        if level=='Atom':
            levelClass = Atom
            levelSetClass = AtomSet
        elif level=='Residue':
            levelClass = Residue
            levelSetClass = ResidueSet
        elif level=='Chain':
            levelClass = Chain
            levelSetClass = ChainSet
        else:
            levelClass = Molecule
            levelSetClass = MoleculeSet
        self.propLevel = levelClass

        elements = levelSetClass([])

        for node, sets in self.objects.items():
            for obj in sets:
                elements += obj.findType(levelClass).uniq()

        # clear the buttons
        for w in self.widgets:
            w.destroy()

        if len(elements)==0: return

        # populate the properties panel with the properties
        if self.showAllTk.get():
            properties = [x[0] for x in elements[0].__dict__.items() if (
                x[0][0]!='_' and isinstance(x[1], (int, float,str)))]
        else:
            properties = self.frequentProps[levelClass]
            
        self.propVars = self._propVars[levelClass]
        master = self.propWidget.interior()
        for prop in properties:
            f = Tkinter.Frame(master)
            cb = CallbackFunction(self.handleButton, prop, levelClass)
            b = Tkinter.Button(f, font=('arial', 1, 'normal'), command=cb,
                               borderwidth=3)
            b.pack(side='left', padx=0, pady=5, ipadx=0, ipady=0)
            self.widgets.append(b)

            b = Tkinter.Label(f, text=prop)
            b.pack(side='left', fill='x')
            self.widgets.append(b)
            f.pack(fill='x')
            self.widgets.append(f)
        self.molecules, self.sets = self.vf.getNodesByMolecule(
            elements, levelClass)
        geoms = []
        for mol, elements in zip(self.molecules, self.sets):
            if isinstance(elements, ListSet):
                geomName = elements[0].__class__.__name__+'Labels'
            else:
                geomName = elements.__class__.__name__+'Labels'
            # find the geometry to use
            if not mol.geomContainer.geoms.has_key(geomName):
                self.setLabelGeom(mol, geomName)
            labelGeom = mol.geomContainer.geoms[geomName]
            geoms.append(labelGeom)
        self.vf.dashboard.geomAppearanceWidget.setGeoms(geoms)


    def clearLabels(self):
        # remove labels selectively for current level and current mol frag
        if self.currentSelection:
            self.setLevel(self.currentLevel)

        for mol, elements in zip(self.molecules, self.sets):
            if not isinstance(elements, ListSet):
                elements = [elements]
            geomName = elements[0].__class__.__name__+'Labels'
            # find the geometry to use, for atoms, label, chains or protein
            labelGeom = mol.geomContainer.geoms[geomName]
            elems = mol.geomContainer.atoms[geomName]

            adict = {}.fromkeys(elements)
            labs = []
            pos = []
            atoms = []
            labels = labelGeom.labels
            vertices = labelGeom.getVertices()

            for i, at in enumerate(elems):
                if adict.has_key(at): continue
                labs.append(labels[i])
                pos.append(vertices[i])
                atoms.append(at)

            labelGeom.Set(vertices=pos, labels=labs, tagModified=False)
            mol.geomContainer.atoms[geomName].data = atoms
        
        levelClass = self.propLevel
        self._propVars[levelClass] = []
        self.propVars = self._propVars[levelClass]


    def endDialog(self, result):
        if result=='OK' or result=='Cancel':
            self.labelEditorDialog.deactivate(result)
            self.labelEditorDialogVisible=False
        elif result=='Apply':
            newlabels = []
            for w in self.labelEntries:
                newlabels.append(w.getvalue())
            self.labelitemsArgs[-2] = self.labelitemsArgs[-3]+newlabels
            self.labelItems(*self.labelitemsArgs)

        self._result = result

        
    def labelEditor(self, atoms, labels):
        def setAll(event=None):
            v = self.allValuesEntry.getvalue()
            for w in self.labelEntries:
                w.setvalue(v)
        if self.labelEditorDialogVisible:
            self.endDialog("Cancel")
        if self.shiftLabelEditorDialog:
            self.endShiftDialog("Cancel")
        self.labelEditorDialog = Pmw.Dialog(
	    buttons = ('OK', 'Apply', 'Cancel',), defaultbutton = 'Apply',
	    title = 'Set custom labels', command = self.endDialog)
        master = self.labelEditorDialog.interior()
        f = Tkinter.Frame(master)
        b = Tkinter.Button(f, text='Set all:', command=setAll,highlightthickness=1,
            highlightcolor='black',highlightbackground='black')
        b.pack(side='left', padx=3,pady=1)
        w = Pmw.EntryField(f, entry_width=20,#labelpos='w', label_text='Apply to All:',
                           command=setAll)
        self.allValuesEntry = w
        w.pack(fill='both',expand=1,padx=2,pady=1)
        f.pack(fill='x',pady=3)
        
	sf = Pmw.ScrolledFrame(
            master, usehullsize = 1, hull_width = 250,  hull_height = 400)
        master = sf.interior()
        self.labelEntries = []
        for at, lab in zip(atoms, labels):
            w = Pmw.EntryField( master, labelpos='e', label_text=at.full_name(),
                                value=lab, entry_width=20)
            w.pack(side='top', anchor='w')
            self.labelEntries.append(w)
        sf.pack(fill='both', expand=1,padx=3, pady=3)
        self.labelEditorDialogVisible = True
        self.labelEditorDialog.activate(globalMode = 'nograb')

        if self._result=='Cancel':
            return None

        newlabels = []
        for w in self.labelEntries:
            newlabels.append(w.getvalue())
        return newlabels
    
            
    def handleButton(self, prop, levelClass, event=None):
        if self.currentSelection:
            # refresh self.molecules and self.sets
            self.setLevel(self.currentLevel)

        if prop and prop not in self.propVars:
            self.propVars.append(prop)

        for mol, tolabel in zip(self.molecules, self.sets):
            # tolabel are atoms, residues chains or molecules for which this
            # labeling command is executed
            if not isinstance(tolabel, ListSet):
                geomName = tolabel.__class__.__name__+'Labels'
                tolabel = mol.geomContainer.atoms[geomName].__class__([tolabel])
            else:
                geomName = tolabel[0].__class__.__name__+'Labels'
            adict = {}.fromkeys(tolabel)

            # find the geometry to use, for atoms, label, chains or protein
            labelGeom = mol.geomContainer.geoms[geomName]
            labels = labelGeom.labels
            vertices = labelGeom.getVertices()

            # labeled are the atoms, residues chains or molecules that are
            # already labeled
            labeled = mol.geomContainer.atoms[geomName]

            # build a list of position for labels that will change
            posTolabel = []
            location = 'Center'
            for item in tolabel:
                z = item.findType(Atom)
                if location=='First':
                    z=z[0]
                    zcoords = numpy.array(z.coords)
                    zcoords = zcoords+0.2
                    zcoords = zcoords.tolist()
                    posTolabel.append(zcoords)
                elif location=='Center':
                    n = int(len(z)/2.)
                    z=z[n]                     
                    zcoords = numpy.array(z.coords)
                    zcoords = zcoords+0.2                    
                    zcoords = zcoords.tolist()
                    posTolabel.append(zcoords)
                if location=='Last':
                    z=z[-1]
                    zcoords = numpy.array(z.coords)
                    zcoords = zcoords+0.2
                    zcoords = zcoords.tolist()
                    posTolabel.append(zcoords)
            labs = []
            pos = []
            
            if prop=='custom':
                existingLabels = {}
                # loop over laready labeled things
                i = 0
                for a, l in zip(labeled, labels):
                    existingLabels[a] = l
                    # if this already labeled thing is in the list for which
                    # are labeleing now we do not need to position as it will
                    # be computed below
                    if not adict.has_key(a):
                        labs.append(labels[i])
                        pos.append(vertices[i])
                    i += 1

                pos = pos + posTolabel
                labelsToEdit = []
                for at in tolabel:
                    if existingLabels.has_key(at):
                        labelsToEdit.append(existingLabels[at])
                    else:
                        labelsToEdit.append('')
                self.labelitemsArgs = [ mol, labeled, tolabel, labelGeom,
                                        geomName, labs, labelsToEdit, pos]
                editedLabels = self.labelEditor(tolabel, labelsToEdit)
                if editedLabels: # edited labels are to be used
                    propLabels = labs + editedLabels
                    self.customLabels = editedLabels
                else: # label editing was cancelled
                    propLabels = labs + labelsToEdit
                    self.customLabels = labelsToEdit
                
            else:
                for i, at in enumerate(labeled):
                    # if this already labeled thing is in the list for which
                    # are labeleing now we do not need to position as it will
                    # be computed below
                    if adict.has_key(at): continue
                    labs.append(labels[i])
                    pos.append(vertices[i])

                pos = pos + posTolabel

                propLabels = labs
                for i, el in enumerate(tolabel):
                    lab = ""
                    for prop in self.propVars:
                        if hasattr(el, prop):
                            lab += str(getattr(el, prop))+' | '
                        elif prop=='custom':
                            if len(self.customLabels)==len(tolabel):
                                lab += '%s | '%self.customLabels[i]
                        else:
                            lab += '? | '
                    propLabels.append(lab[:-3])

            self.labelItems(mol, labeled, tolabel, labelGeom, geomName, labs,
                            propLabels, pos)


    def labelItems(self, mol, labeled, tolabel, labelGeom, geomName, labs,
                   propLabels, pos):
        #print 'ZZZZZ', len(propLabels), propLabels, repr(tolabel), len(pos)

        #print 'LABELLING', len(propLabels), len(propCenters)
        labelGeom.Set(
            labels=tuple(propLabels), vertices=tuple(pos),
            visible=1, tagModified=False,
            )

        labeled = labeled.union(tolabel)
        mol.geomContainer.atoms[geomName] = labeled
        
        
    def Close_cb(self, event=None):
        # put apply button back
        self.vf.dashboard.showApplyButton()

        # delete advanced panel
        self.vf.dashboard.paramsNB.delete('Advanced')

        # destroy widgets
        for w in self.widgets: w.destroy()
        self.form.destroy()
        self.form = None
        self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()


labelMenuColDescr = LabelColumnDescriptor(
    'label', [None], buttonColors=['white', 'white'],
    buttonShape='downTriangle',
    inherited=False, title='L',
    pmvCmdsToLoad = [('labelAtoms', 'labelCommands', 'Pmv'),                  
                     ('labelResidues', 'labelCommands', 'Pmv'),
                     ('labelChains', 'labelCommands', 'Pmv'),
                     ('labelMolecules', 'labelCommands', 'Pmv')],
    iconfile='dashboardLabelIcon.jpg',
    buttonBalloon="""display labeling menu for %s""",
    onButtonBalloon='display labeling menu for %s',
    offButtonBalloon='display unlabeling menu for %s'
    )
ColumnDescriptors.append(labelMenuColDescr)



colAtColDescr = MVColumnDescriptor(
    'color by atom types', ('colorByAtomType', (), {}),
    title='Atom', color='magenta',
    pmvCmdsToHandle = ['colorByAtomType'],
    pmvCmdsToLoad = [('colorByAtomType', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', )
ColumnDescriptors.append(colAtColDescr)


colMolColDescr = MVColumnDescriptor(
    'color by molecule', ('colorByMolecules', (), {}),
    title='Mol', color='#5B49BF',
    pmvCmdsToHandle = ['colorByMolecules'],
    pmvCmdsToLoad = [('colorByMolecules', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colMolColDescr)


colChainColDescr = MVColumnDescriptor(
    'color by chains', ('colorByChains', (), {}),
    title='Chain', color='#BF7C66',
    pmvCmdsToHandle = ['colorByChains'],
    pmvCmdsToLoad = [('colorByChains', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colChainColDescr)


colResRASColDescr = MVColumnDescriptor(
    'color by residue (RASMOL)', ('colorByResidueType', (), {}),
    title='RAS', color='purple',
    pmvCmdsToHandle = ['colorByResidueType'],
    pmvCmdsToLoad = [('colorByResidueType', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colResRASColDescr)


colResSHAColDescr = MVColumnDescriptor(
    'color by residue (SHAPELY)', ('colorResiduesUsingShapely', (), {}),
    title='SHA', color='#333333',
    pmvCmdsToHandle = ['colorResiduesUsingShapely'],
    pmvCmdsToLoad = [('colorResiduesUsingShapely', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colResSHAColDescr)


colDGColDescr = MVColumnDescriptor(
    'color by DG', ('colorAtomsUsingDG', (), {}),
    title='DG', color='#268E23',
    pmvCmdsToHandle = ['colorAtomsUsingDG'],
    pmvCmdsToLoad = [('colorAtomsUsingDG', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colDGColDescr)


colInstColDescr = MVColumnDescriptor(
    'color by instance', ('colorByInstance', (), {}),
    title='Inst.', color='black',
    pmvCmdsToHandle = ['colorByInstance'],
    pmvCmdsToLoad = [('colorByInstance', 'colorCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colInstColDescr)


colSSColDescr = MVColumnDescriptor(
    'color by second. struct.', ('colorBySecondaryStructure', (), {}),
    title='Sec.\nStr.', color='magenta',
    pmvCmdsToHandle = ['colorBySecondaryStructure'],
    pmvCmdsToLoad = [('colorBySecondaryStructure',
                      'secondaryStructureCommands', 'Pmv')],
    btype='button', buttonShape='diamond', 
)
ColumnDescriptors.append(colInstColDescr)


## ColDescr = MVColumnDescriptor(
##     '', ('', (), {}),
##     title='', color='',
##     pmvCmdsToHandle = [''],
##     pmvCmdsToLoad = [('', 'colorCommands', 'Pmv')],
##     btype='button', buttonShape='diamond', 
## )
## ColumnDescriptors.append(ColDescr)


## cmds = [
##     ('color by atom types', 'Atom', 'colorByAtomType', (), {},
##      'magenta', 'colorCommands'),
##     ('color by molecule', 'Mol', 'colorByMolecules', (), {},
##      '#5B49BF', 'colorCommands'),

##     ('color by chains', 'Chain', 'colorByChains', (), {},
##      '#BF7C66', 'colorCommands'),
##     ('color by residue (RASMOL)', 'RAS',
##      'colorByResidueType', (), {}, 'purple', 'colorCommands'), 

##     ('color by residue (SHAPELY)', 'SHA',
##      'colorResiduesUsingShapely', (), {}, '#333333', 'colorCommands'),
##     ('color by DG', 'DG', 'colorAtomsUsingDG',(), {}, '#268E23',
##      'colorCommands'),
##     ('color by instance', 'Inst.', 'colorByInstance', (), {},
##      'black', 'colorCommands'),
##     ('color by second. struct.', 'Sec.\nStr.',
##      'colorBySecondaryStructure', (), {}, 'magenta',
##      'secondaryStructureCommands'),
## ]

## for name, title, cmd, args, opt, color, mod in cmds:
##     descr = MVColumnDescriptor(
##         name, (cmd, args, opt), title=title, color=color,
##         btype='button', buttonShape='diamond', 
##         pmvCmdsToHandle = [cmd],
##         pmvCmdsToLoad = [(cmd, mod, 'Pmv')]
##         )
##     ColumnDescriptors.append(descr)

# MS I think this funciton is not OBSOLETE
def loadAllColunms(mv):
    print ' HUMM it actually gets called !'
    raise
    # adding columns to dashboard
    mv.dashboardSuspendRedraw(True)

    mv.addDashboardCmd(visibilityColDescr, log=0)
    mv.addDashboardCmd(selectColDescr, log=0)
    mv.addDashboardCmd(displayLinesColDescr, log=0)
    mv.addDashboardCmd(displaySandBColDescr, log=0)
    mv.addDashboardCmd(displayCPKColDescr, log=0)
    mv.addDashboardCmd(displaySSColDescr, log=0)
    mv.addDashboardCmd(displayMSMSColDescr, log=0)
    #mv.addDashboardCmd(labelColDescr, log=0)
    #mv.addDashboardCmd(colAtColDescr, log=0)
    #mv.addDashboardCmd(colMolColDescr, log=0)
    #mv.addDashboardCmd(colChainColDescr, log=0)
    #mv.addDashboardCmd(colResRASColDescr, log=0)
    #mv.addDashboardCmd(colResSHAColDescr, log=0)
    #mv.addDashboardCmd(colDGColDescr, log=0)
    #mv.addDashboardCmd(colSSColDescr, log=0)
    #mv.addDashboardCmd(colInstColDescr, log=0)
    mv.addDashboardCmd(colorMenuColDescr, log=0)
    mv.addDashboardCmd(labelMenuColDescr, log=0)
    
    mv.dashboardSuspendRedraw(False)
    mv.GUI.ROOT.update()
    # set dahboard size
    mv.dashboard.setNaturalSize()


def moveTreeToWidget(oldtree, master, vf):
    # save columns
    columns = oldtree.columns

    # get handle to root node
    rootnode = oldtree.root

    # get handle to tree's objectToNode dict
    objToNode = oldtree.objectToNode
    selectedNodes = oldtree.selectedNodes
    
    # destroy docked tree
    oldtree.undisplay()
    oldtree.destroy()

    # create new tree
    tree = oldtree.__class__(master, rootnode, vf=vf, selectionMode='multiple')

    # change all references to Tree
    oldtree.reparentNodes(tree)

    tree.selectedNodes = selectedNodes
    tree.objectToNode = objToNode
    
    # put the columns back. This needs to be done by hand
    # because addColumnDescriptor appends a chkbtval and resets nodes
    tree.columns = columns
    tree.nbCol = len(columns)
    for i,c in enumerate(columns):
        tree.createColHeader(c, i)
        c.tree = tree

    tree.pack(expand=1, fill="both")
    tree.updateTreeHeight()
    return tree
