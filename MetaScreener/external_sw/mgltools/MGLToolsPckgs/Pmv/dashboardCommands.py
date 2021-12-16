import Tkinter, Pmw, numpy
from Pmv.mvCommand import MVCommand, MVCommandGUI
from Pmv.moleculeViewer import DeleteGeomsEvent, AddGeomsEvent, EditGeomsEvent

# TODO
# add spline command column
# adding the columns should be commands

from Pmv.dashboard import MolFragTreeWithButtons, MolFragNodeWithButtons, \
     moveTreeToWidget
from mglutil.gui.BasicWidgets.Tk.trees.TreeWithButtons import \
     ColumnDescriptor
from mglutil.gui.BasicWidgets.Tk.trees.tree import IconsManager
from mglutil.gui.InputForm.Tk.gui import InputForm

from MolKit.molecule import MoleculeSet
from MolKit.protein import ResidueSet, Chain


class AddSelectionToDashboardCommand(MVCommand):
    """if there is a selection ask for a name and add a line to the dashboard
    \nPackage : Pmv
    \nModule : dashboardCommands
    \nClass : AddSelectionToDashboardCommand
    \nCommand : addSelectionToDashboard
    \nSynopsis:\n
        None <--- addSelectionToDashboard(name, set)
    """

    def doit(self, name, _set):
        self.vf.dashboard.addSetLine(name, _set)
        self.vf.saveSet(_set, name, comments=name+' created in dashboard')
        self.vf.clearSelection(log=0)


    def guiCallback(self, evt=None):
        if len(self.vf.selection)==0:
            from tkMessageBox import showwarning
            showwarning("Warning", "select something first")
        else:
            from tkSimpleDialog import askstring
            l = len(self.vf.dashboard.tree.root.children)
            name = askstring("set name in dashboard", "name:",
                             initialvalue="set_%d"%l)
            if name is None:
                return
            sel = self.vf.selection
            _set = sel.__class__(sel.data)
            
            self.doitWrapper( name, _set )
    

    def __call__(self, name, _set, **kw):
        """None <- addSelectionToDashboard( self, **kw)
        add a line to the dashboard to represent current selection
        """
        _set = self.vf.expandNodes(_set)
        if len(_set)==0:
            return
        self.doitWrapper( *(name, _set), **kw )

addSelectionToDashboardCommandGUI = MVCommandGUI()
addSelectionToDashboardCommandGUI.addMenuCommand('menuRoot', 'Select',
                                                 'Add selection To Dashboard')

addSelectionToDashboardGUI = MVCommandGUI()
addSetToDashboardmsg = 'Add the current selection to the dashboard'
from Pmv.moleculeViewer import ICONPATH
addSelectionToDashboardGUI.addToolBar(
    'addSetToDashboard', icon1='AddToDashboard.gif',index=15., 
    balloonhelp=addSetToDashboardmsg, type='ToolBarButton', icon_dir=ICONPATH)


class FloatDashboard(MVCommand):
    """Command to move the dashboard widget into its own toplevel widget"""

    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return

        self.vf.browseCommands('dashboardCommands', package='Pmv', log=0)


    def doit(self):
        # get handle to old tree
        oldtree = self.vf.dashboard.tree

        if isinstance(oldtree.master, Tkinter.Toplevel):
            return

        # create window for new tree
        master = Tkinter.Toplevel()
        #master.withdraw()
        #master.protocol('WM_DELETE_WINDOW',self.vf.dashboard.hide)
        master.protocol('WM_DELETE_WINDOW',self.vf.dockDashboard)

        tree = moveTreeToWidget(oldtree, master, self.vf)

        tree.configure(hull_height=300, hull_width=600)
        # update tree eight to force vertical scroll bar to appear if needed
        tree.updateTreeHeight()
        self.vf.dashboard.tree = tree
        tree.sets = self.vf.sets

    def destroy(self, event=None):
        self.vf.GUI.toolbarCheckbuttons['Dashboard']['Variable'].set(0)
        self.vf.dockDashboard(topCommand=0)
        


class DockDashboard(MVCommand):
    """Command to move the dashboard widget into the PMV GUI"""

    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return

        self.vf.browseCommands('dashboardCommands', package='Pmv', log=0)


    def doit(self):

        self.vf.GUI.toolbarCheckbuttons['Dashboard']['Variable'].set(0)
        # get handle to old tree
        oldtree = self.vf.dashboard.tree

        # get master
        if oldtree.master==self.vf.dashboard.master2:
            return

        oldmaster = oldtree.master
        tree = moveTreeToWidget(oldtree, self.vf.dashboard.master2, self.vf)
        tree.pack(side='top', expand=1, fill='both')
        oldmaster.destroy()
        tree.vf = self.vf
        self.vf.dashboard.tree = tree
        tree.sets = self.vf.sets



class DashboardSuspendRedraw(MVCommand):
    """Command to suspend and un-suspend the tree redrawing"""

    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return

        self.vf.browseCommands('dashboardCommands', package='Pmv', log=0)


    def doit(self, val):
        assert val in [True, False, 0, 1]
        self.vf.dashboard.tree.suspendRedraw = val



class ShowDashboard(MVCommand):
    """Command to show or hide the dashboard, can be added to _pmvrc"""
    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return

        self.vf.browseCommands('dashboardCommands', package='Pmv', log=0)


    def doit(self, val):
        #print "ShowDashboard.doit", val
        tree = self.vf.dashboard.tree
        if val:
            self.vf.GUI.toolbarCheckbuttons['Dashboard']['Variable'].set(1)
            if isinstance(tree.master, Tkinter.Toplevel):
                self.vf.dashboard.tree.master.deiconify()
            else:
                self.vf.dashboard.tree.pack(side='bottom', expand=0, fill='x')
        else:
            self.vf.GUI.toolbarCheckbuttons['Dashboard']['Variable'].set(0)
            if isinstance(tree.master, Tkinter.Toplevel):
                self.vf.dashboard.tree.master.withdraw()
            else:
                self.vf.dashboard.tree.forget()



class AddDashboardCmd(MVCommand):
    """Command to add a command in a nwe column"""

    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return

        self.vf.browseCommands('dashboardCommands', package='Pmv', log=0)


    def doit(self, descr):
        self.vf.dashboard.addColumnDescriptor(descr)

from Pmv.selectionCommands import SelectionEvent
from Pmv.dashboard import SetWithButtons

class Dashboard(MVCommand):

    """Display a widget showing a tree representation of the molecules in the Viewer and check buttons allowing to carry out command on parts of molecules directly.
    Certain commands such as coloring or displaying lines, CPK and S&B are implmented as mutually exclusive (i.e. like radio buttons).
"""

    def onExitFromViewer(self):
        for col in self.tree.columns:
            col.icon = None


    def setColumnWidth(self, cw):
        self.tree.setColumnWidth(cw)
        self.setNaturalSize()

    def increaseColumnWidth(self, event=None):
        self.setColumnWidth(self.tree.colWidth+1)
        
    def decreaseColumnWidth(self, event=None):
        self.setColumnWidth(self.tree.colWidth-1)
        

    def setNaturalSize(self, event=None):
        if not self.vf.GUI.workspace.winfo_ismapped():
            self.vf.GUI.ROOT.after(500, self.setNaturalSize)
            
        # get width of tree
        x1, dum, x2, dum = self.tree.headerCanvas.bbox('ColHeaders')
        dwidth = x2#-x1

        # add space for vertical scroll bar if visible
        vb = self.tree.component('vertscrollbar')
        #if vb.winfo_ismapped():
        dwidth += int(vb.configure('width')[-1]) + 5

        dwidth += 24 #to account for padding and separator

        #print 'setNaturalSize', x1, x2, dwidth
        #camwidth = self.GUI.workspace.winfo_width() - dwidth
        #self.GUI.workspace.configurepane('DockedCamera',size=camwidth)
        self.vf.GUI.workspace.configurepane('ToolsNoteBook',size=dwidth)


    def hide(self):
        self.vf.showDashboard(False)


    def show(self):
        self.vf.showDashboard(True)


    def addColumnDescriptor(self, colDescr):
        # adds self.vf to colDescr
        assert isinstance(colDescr,ColumnDescriptor)

        colDescr.vf = self.vf
        
        self.tree.addColumnDescriptor(colDescr)


    def addSetLine(self, name, set):
        """
        add a line to the dashboard with a given  molecular fragment
        """
        from MolKit.molecule import MoleculeSet
        node = MoleculeSet()
        node.setSetAttribute('_set', set)
        node.setSetAttribute('name', name)
        node.setSetAttribute('treeNodeClass', SetWithButtons)
        self.onAddObjectToViewer(node)
        

    def onAddCmdToViewer(self):
        vf = self.vf
        
        if not vf.hasGui: return

        vf.browseCommands('dashboardCommands', package='Pmv', log=0)
        #self.hasMSMS = True
        #try:
        #    import mslib
        #    vf.browseCommands('msmsCommands', package='Pmv', log=0)
        #except:
        #    self.hasMSMS = False

        from Pmv.moleculeViewer import AddAtomsEvent, DeleteAtomsEvent
        from Pmv.deleteCommands import AfterDeleteAtomsEvent, \
             BeforeDeleteMoleculesEvent
        from Pmv.colorCommands import ColorAtomsEvent
        vf.registerListener(BeforeDeleteMoleculesEvent,
                            self.handleBeforeDeleteMoleculesEvents)
        vf.registerListener(DeleteAtomsEvent, self.handleDeleteAtomsEvents)
        vf.registerListener(AfterDeleteAtomsEvent, self.handleAfterDeleteEvents)
        vf.registerListener(AddAtomsEvent, self.handleAddEvents)
        vf.registerListener(SelectionEvent, self.handleSelection)
        vf.registerListener(EditGeomsEvent, self.handleEditGeom)
        vf.registerListener(ColorAtomsEvent, self.handleColorAtomsEvent)
        #vf.registerListener(ClearSelectionEvent, self.handleClearSelection)

        # build the tree
        #master = Tkinter.Toplevel()
        #master.withdraw()
        #master.protocol('WM_DELETE_WINDOW',self.hide)

        from MolKit.molecule import MolecularSystem
        self.system = syst = MolecularSystem ('All Molecules')
        
        # override elementType in order to allow adoption of selection
        syst.children.elementType = None

        # create a frame for dashboard and params widget
        pw = Tkinter.Frame(self.vf.GUI.dockDashMaster)
        pw.pack_propagate(0)
        # create frame containing the dashboard
        self.master2 = master2 = Tkinter.Frame(pw)
        self.master4 = Tkinter.Frame(pw)
        #master4.pack(anchor='s', expand=0, fill='both')
        #master4.forget()
        
##         # create a vertical panned widget
##         pw = self.dashboardPanedWidget = Pmw.PanedWidget(
##             self.vf.GUI.dockDashMaster,
##             orient='vertical',
##             hull_borderwidth = 1,
##             hull_relief = 'sunken')

##         # add pane for dashboard
##         master2 = pw.add('dashboard')
        
##         # add pane for cmdparams
##         pane2 = pw.add('cmdParams', size=1)
##         pane2.bind('<Configure>', self.configure_cb)

        ## MS if I create the scrolled farm the notebook inside will
        ## not expand :(
        #self.paramsSF = Pmw.ScrolledFrame(
        #    pane2, vertscrollbar_width=8, horizscrollbar_width=8)
        #self.paramsSF.pack(fill='both', expand=1)

        # create notebook inside scroleld frame
        #notebook = self.paramsNB = Pmw.NoteBook(self.paramsSF.interior())
        #self.master4 = Tkinter.Frame(pane2)

        self.objectLabelWidget = Tkinter.Label(self.master4, text='For: ')
        self.objectLabelWidget.pack(side='top', anchor='w')
        
        notebook = self.paramsNB = Pmw.NoteBook(self.master4)
        notebook.pack(fill='both', expand=1)
        self.paramsNoteBook = notebook
        
        # put OK and close buttons
        ApplyCloseFrame = Tkinter.Frame(self.master4)
        self.applyButton = Tkinter.Button(ApplyCloseFrame, text='Apply')
        self.applyButton.pack(side='left', fill='x', expand=1)
        self.closeButton = Tkinter.Button(ApplyCloseFrame, text='Close')
        self.closeButton.pack(side='left', fill='x', expand=1)
        ApplyCloseFrame.pack(fill='x', expand=0)

        #self.master4.pack(fill='both', expand=1)
        
        self.master3 = master3 = notebook.add("Basic")
        advanced = notebook.add("Rendering")
        from Pmv.appearancePanel import GeomAppearanceWidget
        self.geomAppearanceWidget = GeomAppearanceWidget(advanced, self.vf)
        
#        master3 = self.paramsSF.interior()
        
        rootnode = MolFragNodeWithButtons(syst, None)#, buttonType='OnOffButtons')
        # no + icon before All Molecules
        rootnode.hasExpandIcon = False
        # no identation for children of All Molecules
        rootnode.generation = -1
        
        # master2 is master for tree
        #master2 = Tkinter.Frame(self.vf.GUI.dockDashMaster)
        iconsManager = IconsManager(['Icons'], 'Pmv')
        tree = MolFragTreeWithButtons(
            self.master2, rootnode, self.vf, iconsManager=iconsManager,
            selectionMode='multiple')
        
        # make All Molecule text bold
        font = tree.font.split()
        rootnode.font = (font[0], font[1], 'bold')

        #self.master2.pack(anchor='n', expand=1, fill='both')
        self.master2.grid(row=0, column=0, sticky='nesw')

        # needed to have dashboard expand when params are hidden
        pw.grid_columnconfigure(0, weight=1)
        pw.grid_rowconfigure(0, weight=1)
        
        rootnode.expand()
        tree.pack(side='top', expand=1, fill='both')
        self.tree = tree
        self.tree.sets = vf.sets

        pw.pack(expand=1, fill='both')

        #self.vf.GUI.setCmdsParamsMaster(master3)
        #self.vf.GUI.setAfterCreatingFormFunc(self.expandParams)
        #self.vf.GUI.setAfterUsingFormFunc(self.collapseParams)
        self.columnShowingForm = None
        self.columnShowingFormValues = {}
        
        #self.vf.GUI.dockDashMaster.after(500, self. hideParamsPane)
        #master3.pack(expand=0, fill='both')
        #master3.forget()

    def hideApplyButton(self):
        self.applyButton.forget()

    def showApplyButton(self):
        self.closeButton.forget()
        self.applyButton.pack(side='left', fill='x', expand=1)
        self.closeButton.pack(side='left', fill='x', expand=1)
        
##     def hideParamsPane(self, event=None):
##         self.dashboardPanedWidget.pane('cmdParams').unbind('<Configure>')
##         height = self.vf.GUI.dockDashMaster.winfo_height()
##         if height==1:
##             self.vf.GUI.dockDashMaster.after(100, self. hideParamsPane)
##         self.dashboardPanedWidget.configurepane(0, size=height)
##         self.vf.master.after(100, self.dashboardPanedWidget.pane('cmdParams').bind,  '<Configure>', self.configure_cb)


    def collapseParams(self, form=None):
##         self.dashboardPanedWidget.pane('cmdParams').unbind('<Configure>')
        form = self.columnShowingForm.form
        self.columnShowingForm = None
        self.master4.place_forget()
        if form is None: return
##        panedW = self.dashboardPanedWidget 
        #self.master4.grid_forget()

##         # get current height
##         curHeight = panedW.pane('dashboard').winfo_height()
##         # get target height
##         height = self.vf.GUI.dockDashMaster.winfo_height()
##         # compute dy
##         nbSteps = 20
##         dy = ((height-curHeight))/(nbSteps-1)
##         for i in range(nbSteps):
##             h = curHeight + i*dy
##             #print "  going to   ",h
##             panedW.configurepane('dashboard', size=int(h))
##         self.columnShowingForm = None
##         self.vf.master.after(100, self.dashboardPanedWidget.pane('cmdParams').bind,  '<Configure>', self.configure_cb)

        
    def expandParams(self, frame):
        frame.update()
        frameheight = frame.winfo_reqheight()
        nbheight = self.paramsNB.component('hull').winfo_reqheight()
        if nbheight > frameheight:
            self.paramsNB.setnaturalsize()
            # this shrinks the notebook to the size of its widgets (frame),
            # otherwise the "Apply" and "Cancel" buttons may not be visible
        height = frameheight + 100
        #print "expandParams:", self, frameheight, nbheight
        self.master4.place(relx=0, rely=1, height=height, relwidth=1., anchor='sw')
        
        #height = frame.winfo_reqheight()
        #self.master4.configure(height=height)
        #self.master4.pack(anchor='s', expand=1, fill='x')
        #self.master4.grid_propagate(0)
        #self.master4.grid(row=1, column=0, sticky='esw')
        #self.master4.grid_columnconfigure(0, weight=40, minsize=500)
        #self.master4.grid_rowconfigure(1, weight=40, minsize=500)
        #dashHeight = self.vf.GUI.dockDashMaster.winfo_height()
        #print 'MASTER4 req', self.master4.winfo_reqheight()
        #print 'MASTER4', self.master4.winfo_height()
        #print 'frame', frame.winfo_reqheight()
        #height = self.master4.winfo_reqheight()
        #self.master4.configure(height=height)
        #return
    
##         self.dashboardPanedWidget.pane('cmdParams').unbind('<Configure>')
##         # expand the [ane containing the parameter form
##         frame.update() # give the form time to be built
##         height = frame.winfo_reqheight()
##         #print 'KKKK', height, self.master4.winfo_reqheight(), self.master4.winfo_height(), self.paramsNoteBook.component('hull').winfo_reqheight(), self.paramsNoteBook.component('hull').winfo_height()
##         #print 'form height', height, self.paramsNB.winfo_reqheight(), self.paramsNB.winfo_height()
##         #print 'self.dashboard.master3.winfo_reqheight()'
##         if height is None:
##             frame.after(100, self.dashboardPanedWidget.pane('cmdParams').bind,  '<Configure>', self.configure_cb)
##             return
##         nbSteps = 20
##         dy = (height+90)/(nbSteps-1)
##         panedW = self.dashboardPanedWidget
##         dashHeight = self.vf.GUI.dockDashMaster.winfo_height()
##         for i in range(nbSteps):
##             h = dashHeight - (i*dy)
##             #print "  going to   ",h, dy
##             # for some reason setting the size does not change anything
##             panedW.configurepane('dashboard', size=int(h))

##         #print 'master3 height', self.master3.winfo_height()
##         #print 'pane height', self.dashboardPanedWidget.pane('cmdParams').winfo_height()
##         #print 
##         frame.after(100, self.dashboardPanedWidget.pane('cmdParams').bind,  '<Configure>', self.configure_cb)


##     def configure_cb(self, event):
##         self.dashboardPanedWidget.pane('cmdParams').unbind('<Configure>')
##         panedW = self.dashboardPanedWidget
##         dashHeight = self.vf.GUI.dockDashMaster.winfo_height()
##         if self.columnShowingForm is not None:
##             # if a form is shown we need to configure the dashboard pane
##             # to ocupy the height of the dockDashMaster-height(form)

##             # height dockDashMaster
##             if isinstance(self.columnShowingForm.form, InputForm):
##                 frame = self.columnShowingForm.form.root
##             else:
##                 frame = self.columnShowingForm.form
##             frame.update() # give the form time to be built
##             # height needed for parameter panel
##             height = frame.winfo_reqheight()+90
##             panedW.configurepane('dashboard', size=int(dashHeight-height))
##         else:
##             panedW.configurepane('dashboard', size=int(dashHeight))
##         self.vf.master.after(100, self.dashboardPanedWidget.pane('cmdParams').bind,  '<Configure>', self.configure_cb)


    def handleSelection(self, event):
        self.setColPercent(event.setOn, event.setOff, '_selectionStatus')
        self.tree.redraw(force=True)
        
    ## def handleClearSelection(self, event):
    ##     for mol in self.vf.Mols:
    ##         self.resetColPercent(mol, '_selectionsStatus')
        
    def handleEditGeom(self, event):
        #print 'handle edit geoms', event.arg
        if event.arg=='lines':
            nodes = event.objects[0]
            for mol in self.vf.Mols:#nodes.top.uniq():
                #ats = mol.geomContainer.atoms['bonded']
                self.setColPercent(event.setOn, event.setOff,
                                   '_showLinesStatus')
                
        elif event.arg=='cpk':
            nodes = event.objects[0]
            for mol in self.vf.Mols:#nodes.top.uniq():
                #ats = mol.geomContainer.atoms['cpk']
                self.setColPercent(event.setOn, event.setOff, '_showCPKStatus')

        elif event.arg=='bs':
            nodes = event.objects[0]
            for mol in self.vf.Mols:#nodes.top.uniq():
                #ats = mol.geomContainer.atoms['sticks']
                self.setColPercent(event.setOn, event.setOff,
                                   '_showS&BStatus')
                #ats = mol.geomContainer.atoms['balls']
                self.setColPercent(event.setOn, event.setOff,
                                   '_showS&BStatus')

        elif event.arg=='msms_ds':
            nodes = event.objects[0]
            surfName = event.objects[1][0][0]
            #if surfName=='MSMS-MOL':
            for mol in self.vf.Mols:#nodes.top.uniq():
                if mol.geomContainer.atoms.has_key(surfName):
                    #ats = mol.geomContainer.atoms[surfName]
                    self.setColPercent(event.setOn, event.setOff,
                                       '_showMSMSStatus_%s'%surfName)

        elif event.arg=='SSdisplay':
            nodes = event.objects[0]
            for mol in self.vf.Mols:#nodes.top.uniq():
                geoms = mol.geomContainer.atoms
                res = ResidueSet([])
                for k,v in geoms.items():
                    if k[:4] in ['Turn', 'Coil', 'Heli', 'Stra']:
                        res += v
                self.setColPercent(event.setOn, event.setOff,
                                   '_showRibbonStatus')

##         elif event.arg=='trace':
##             nodes = event.objects[0]
##             for mol in nodes.top.uniq():
##                 ats = mol.geomContainer.atoms['CAsticks']
##                 self.setColPercent(ats, '_showCAtraceStatus')
##                 ats = mol.geomContainer.atoms['CAballs']
##                 self.setColPercent(ats, '_showCAtraceStatus')
        self.tree.redraw(force=True)
        #if "color" widget is displayed in the dashboard to update its
        # list of representations:
        if self.columnShowingForm is not None:
            if hasattr(self.columnShowingForm, 'name') and \
                   self.columnShowingForm.name == "color":
                self.columnShowingForm.updateRepresentations()


    def guiCallback(self):
        if self.vf.GUI.toolbarCheckbuttons['Dashboard']['Variable'].get():
            #self.show()
            self.vf.floatDashboard()
        else:
            #self.hide()
            self.vf.dockDashboard()

            
    def resetColPercent(self, mol, attribute):
        attribute = attribute.replace('-', '_') # 'MSMS-MOL' cannot be used
        setattr(mol, attribute, 0.0)
        if not hasattr(mol, "allAtoms"): return 
        setattr(mol.allAtoms, attribute, 0.0)
        for chain in mol.chains:
            setattr(mol.chains, attribute, 0.0)
            for res in chain.residues:
                setattr(res, attribute, 0.0)


    def getSSResidues(self, chain):
        res = [x for x in chain.children if hasattr(x,'secondarystructure')]
        return ResidueSet(res)
    

    def setColPercent(self, setOn, setOff, attribute):
        #print 'SETCOLPERCENT ON', repr(setOn)
        #print 'SETCOLPERCENT OFF', repr(setOff)
        #from time import time
        #t1 = time()

        attribute = attribute.replace('-', '_') # 'MSMS-MOL' cannot be used
        
        # set attribute to 0 for all elements in setOff and their children
        if setOff:
            for n in setOff:
                setattr(n, attribute, 0.0)
            # all children are selected as well
            children = setOff.children
            while len(children):
                setattr(children, attribute, 0.0)
                children = children.children

        # set attribute to 1 for all elements in setOn and their children
        if setOn:
            for n in setOn:
                setattr(n, attribute, 1.0)
            # all children are selected as well
            children = setOn.children
            while len(children):
                setattr(children, attribute, 1.0)
                children = children.children

        # update parents of setOff
        if setOff:
            parents = setOff.parent
            while parents[0]!=None:
                for p in parents.uniq():
                    if isinstance(p, Chain) and attribute=='_showRibbonStatus':
                        children = self.getSSResidues(p)
                    else:
                        children = p.children
                    l = len(children)
                    if l:
                        try:
                            # if atoms have been added this might fail
                            childSum = numpy.sum(getattr(children, attribute))
                        except:
                            # for each child that does nto have the attribute
                            # create it and set it to 0.0
                            for c in children:
                                setattr(c, attribute, 0.0)
                            childSum = numpy.sum(getattr(children, attribute))
                        setattr(p, attribute, childSum/float(l))
                if isinstance(parents, MoleculeSet):
                    break
                else:
                    parents = parents.parent.uniq()
                
        # update parents of setOn
        if setOn:
            parents = setOn.parent
            while parents[0]!=None:
                for p in parents.uniq():
                    if isinstance(p, Chain) and attribute=='_showRibbonStatus':
                        children = self.getSSResidues(p)
                    else:
                        children = p.children
                    l = len(children)
                    if l:
                        try:
                            # if atoms have been added this maight fail
                            childSum = numpy.sum(getattr(children, attribute))
                        except: #KeyError:
                            # for each child that does nto have the attribute
                            # create it and set it to 0.0
                            for c in children:
                                setattr(c, attribute, 0.0)
                            childSum = numpy.sum(getattr(children, attribute))
                        setattr(p, attribute, childSum/float(l))
                if isinstance(parents, MoleculeSet):
                    break
                else:
                    parents = parents.parent.uniq()

        #print 'time to set %s'%attribute, time()-t1, repr(setOn), repr(setOff)


    
    def onAddObjectToViewer(self, obj):
        """
        Add the new molecule to the tree
        """
        # we have to save .top and .parent else they become syst
        # and it brakes Pmv
        top = obj.top
        parent = obj.parent

        self.system.adopt(obj)
        # restore .top and .parent
        obj.top = top
        obj.parent = parent
        
        rootNode = self.tree.root
        length = len(self.system.children)
        if length==1:
            rootNode.refresh()
            
        rootNode.refreshChildren()

        if length==1:
            rootNode.expand()

        self.resetColPercent(obj, '_selectionStatus')
        # make scroll bar appear if needed
        self.tree.updateTreeHeight()
        

    def onRemoveObjectFromViewer(self, obj):    
        ## MoleculeSet object are ultimately UserList objects\
        ## for which __eq__ tests self.data == self.__cast(other)
        ## hence we need to find the righ object  using id()
        from Pmv.moleculeIterator import MoleculeIterator
        for i, _object in enumerate(self.system.children):
            if isinstance(_object, MoleculeIterator):
                _object = _object.object
            if id(_object)==id(obj):
                break

        if i<len(self.system.children):
            self.system.children.pop(i)

        self.tree.root.refreshChildren()


    def handleColorAtomsEvent(self, event):
        sel = event.arg[0]
        if type(sel) == str:
            sel = self.vf.expandNodes(sel)
        from MolKit.molecule import Molecule
        from MolKit.tree import TreeNode
        if issubclass(sel.__class__, TreeNode):
            sel = sel.setClass([sel])
        for mol in sel.top.uniq():
            for child in self.tree.root.children:
                if isinstance(child.object, Molecule) and \
                       hasattr(child.object, 'chains'):
                    child.nodeRedraw()
                
            
    def handleBeforeDeleteMoleculesEvents(self, event):

        deletedMolecules = event.arg
        for child in self.tree.root.children:
            if isinstance(child, SetWithButtons):
                obj = child.getNodes(0).values()[0][0]
                mols = obj.top.uniq()
                for m in mols:
                    if m in deletedMolecules:
                        child.removeSet()

        ## FIXME to make this undoable we shoudl add re-creatign the sets
        ## to the undostack


    def handleDeleteAtomsEvents(self, event):
        """Function to update tree when molecular fragments are deleted.
"""
        atoms = event.objects

        ## remove atoms from user defined sets in dashboard
        from MolKit.molecule import Atom
        for child in self.tree.root.children:
            if isinstance(child, SetWithButtons):
                _set = child.object._set.findType(Atom)
                newSet = _set-atoms
                if len(newSet):
                    child.object.setSetAttribute('_set', newSet)
                else:
                   child.removeSet()
                   
        parents = atoms.parent.uniq()
        allParents = []
        tree = self.tree
        while True:
            for p in parents:
                try:
                    ptnode = tree.objectToNode[p]
                    ptnode.children = []
                    allParents.append(ptnode)
                    if len(p.children)==0:
                        del tree.objectToNode[p]
                except KeyError: # the node was not created in the tree yet
                    pass
            parents = parents.parent
            if parents[0]==None: break
            else: parents = parents.uniq()
        self.allParentsToResfresh = allParents
                    

    def handleAfterDeleteEvents(self, event):
        """Function to update tree when molecular fragments are deleted.
"""
        for p in self.allParentsToResfresh:
            # p.object can be missing after splitting all chains of a protein
            if hasattr(p.object, 'children'):
                p.refreshChildren()
        self.resetAllPercents()
        return


    def resetAllPercents(self):
        for mol in self.vf.Mols:
            gca = mol.geomContainer.atoms
            ats = gca['bonded']
            self.resetColPercent(mol, '_showLinesStatus')
            self.setColPercent(ats, [], '_showLinesStatus')

            if gca.has_key('cpk'):
                ats = gca['cpk']
                self.resetColPercent(mol, '_showCPKStatus')
                self.setColPercent(ats, [], '_showCPKStatus')
            
            if gca.has_key('sticks'):
                ats = gca['sticks']
                self.resetColPercent(mol, '_showS&BStatus')
                self.setColPercent(ats, [], '_showS&BStatus')
            
            if gca.has_key('balls'):
                ats = gca['balls']
                self.setColPercent(ats, [], '_showS&BStatus')

            # MSMS is handle automatically because
            # displayMSMS.handleDeleteAtoms will trigger a recalculation
    

    def handleAddEvents(self, event):
        """Function to update tree when molecular fragments are added.
"""
        tree = self.tree
        for obj in event.objects:
            try:
                parentNode = tree.objectToNode[obj.parent]
                if len(obj.parent.children)==1:
                    parentNode.refresh()
                parentNode.refreshChildren(redraw=False)
            except KeyError:
                pass
        tree.redraw()
            
                
    def onCmdRun(self, command, *args, **kw):
        #import traceback
        #print '#############################################################'
        #traceback.print_stack()
        #print 'OnRun', command, args, kw
        # called when a Pmv command is run

        # find the column for this command
        for i,col in enumerate(self.tree.columns):
            if command.name in col.pmvCmdsToHandle:
                try:
                    col.onPmvCmd(command, *((i,)+args), **kw)
                except AttributeError:
                    pass
        return

##         tree = self.tree
##         column = None
##         for i,col in enumerate(tree.columns):
##             cmd, arg, opt = col.cmd
##             if cmd==command:
##                 column=i
##                 break

##         if column is None:
##             return # the command is not one in the dashboard

##         if col.commandType=='button':
##             return  # only check buttons not managed upon PMV command

##         molFrag = args[0]
##         negate = kw['negate']
##         if column<6:#command==self.vf.displayLines:
##             for o in molFrag:
##                 try:
##                     node = self.tree.objectToNode[o]
##                     if node.chkbtval[column]==negate:
##                         #only call if button needs to be checked
##                         node.set(column, negate==False)
##                 except KeyError:
##                     #print 'Failed to find object in tree', o
##                     pass
                    
                
Dashboard_GUI = MVCommandGUI()
#from Pmv.moleculeViewer import ICONPATH
#Dashboard_GUI.addToolBar('Dashboard', icon1='dashboard.png', 
#                         icon_dir=ICONPATH,
#                         balloonhelp='Float Dashboard Widget', index=9)
            
commandList = [
    {'name':'dashboard', 'cmd':Dashboard(), 'gui':Dashboard_GUI},
    #{'name':'showDashboard', 'cmd':ShowDashboard(), 'gui':None},
    {'name':'floatDashboard', 'cmd':FloatDashboard(), 'gui':None},
    {'name':'dockDashboard', 'cmd':DockDashboard(), 'gui':None},
    {'name':'addDashboardCmd', 'cmd':AddDashboardCmd(), 'gui':None},
    {'name':'dashboardSuspendRedraw', 'cmd':DashboardSuspendRedraw(),
     'gui':None},
    {'name':'addSelectionToDashboard', 'cmd':AddSelectionToDashboardCommand(),
     'gui':addSelectionToDashboardCommandGUI},
    {'name':'addSelectionToDashboardButton', 'cmd':AddSelectionToDashboardCommand(),
     'gui':addSelectionToDashboardGUI},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
