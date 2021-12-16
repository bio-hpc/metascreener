#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2010
#
#
#############################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/seqViewerCommands.py,v 1.20 2013/10/10 22:56:17 sanner Exp $
# 
# $Id: seqViewerCommands.py,v 1.20 2013/10/10 22:56:17 sanner Exp $
#

import Pmw

from Pmv.mvCommand import MVCommand, MVCommandGUI
from Pmv.seqDisplay import SeqViewGUI, buildLabels
from Pmv.moleculeViewer import ShowMoleculesEvent
from MolKit.protein import Residue

class SeqViewerSuspendRedraw(MVCommand):
    """Command to suspend and un-suspend the tree redrawing"""

    def onAddCmdToViewer(self):
        if not self.vf.hasGui: return
        self.vf.browseCommands('seqViewerCommands', package='Pmv', log=0)


    def doit(self, val):
        assert val in [True, False, 0, 1]
        self.vf.sequenceViewer.suspendRedraw = val


class SequenceViewerCommand(MVCommand):
    """
    The SequenceViewerCommand adds the Sequence Viewer widget
    of the GUI
    \nPackage : Pmv
    \nModule  : seqViewerCommands
    \nClass   : LoadSequenceViewerCommand
    \nName    : loadSequenceViewer
    """

    def __init__(self, func=None):
        MVCommand.__init__(self, func)
        self.suspendRedraw = False

    def onSelect(self, residues, deselect=False):
        #print "SV suspendRedraw in onSelect", self.suspendRedraw
        if self.suspendRedraw: return
        if deselect:
            self.vf.deselect(residues)
        else:
            self.vf.select(residues)


    def handleColorAtomsEvent(self, event):
        #print "SV suspendRedraw in handleColorAtomsEvent", self.suspendRedraw
        if self.suspendRedraw: return
        sel = event.arg[0]
        self.colorSequenceString(sel)


    def colorSequenceString(self, sel):
        #print "SV suspendRedraw in colorSequenceString", self.suspendRedraw
        if self.suspendRedraw: return
        #This method is also used in script that restores Pmv session (session.py)  
        if type(sel) == str:
            sel = self.vf.expandNodes(sel)
        canvas = self.seqViewer.canvas
        bcanvas = self.seqViewer.bcan
        sqv = self.seqViewer
        tkColFormat = '#%02X%02X%02X'
        for res in sel.findType(Residue):
            if res.CAatom is not None:
                col = res.CAatom.colors['lines']
            elif res.C1atom is not None:
                col = res.C1atom.colors['lines']
            else:
                col = (.5, .5, .5)
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
            ##         col = (.5, .5, .5)

            tkcol = tkColFormat%(col[0]*255,col[1]*255, col[2]*255)
            tid = sqv.resToTkid.get(res, None)
            if tid:
                if sqv.selected.has_key(res): # this residue is selected
                    canvas.itemconfigure(tid, fill='black')
                else:
                    canvas.itemconfigure(tid, fill=tkcol)

                canvas.itemconfigure(sqv.scids[tid], fill=tkcol)
                bcanvas.itemconfigure(sqv.orientId[tid], fill=tkcol)
            
    
    def handleSelectionEvent(self, event):
        #print "SV suspendRedraw in handleSelectionEvent", self.suspendRedraw
        if self.suspendRedraw: return
        sqv = self.seqViewer
        if sqv._makingSelection:
            return # we originated this event

        # deselect current selection
        items = []
        for res in sqv.selected:
            item = sqv.resToTkid.get(res, None)
            if item: items.append(item)
        #items = [sqv.resToTkid[res] for res in sqv.selected]
        sqv.deselectItems(items)
        
        residues = self.vf.selection.findType(Residue)
        sqv.selected = {}.fromkeys(residues)
        sqv.selection = residues

        # select new selection
        items = []
        for res in sqv.selected:
            item = sqv.resToTkid.get(res, None)
            if item: items.append(item)
            
        #items = [sqv.resToTkid[res] for res in residues]
        sqv.selectItems(items)


    def handleShowMoleculesEvent(self, event):
        #print "SV suspendRedraw in handleShowMoleculesEvent", self.suspendRedraw
        if self.suspendRedraw: return
        # event.arg is the first argument to Event object constructor
        # event.objects is second argument to Event object constructor
        sv = self.seqViewer
        if event.kw['visible']:
            for mol in event.arg:
                if sv.selectForSuperimpose and not mol in sv.alignmentMols:
                    continue
                sv.showSequence(mol)
        else:
            for mol in event.arg:
                if sv.selectForSuperimpose and not mol in sv.alignmentMols:
                    continue
                sv.hideSequence(mol)


    def isShown(self, mol):
        if self.seqViewer.isVisible.has_key(mol):
            return self.seqViewer.isVisible[mol]
        else: return False

    
    def handleDeleteAtomsEvents(self, event):
        #print "SV suspendRedraw in handleDeleteAtomsEvents", self.suspendRedraw
        if self.suspendRedraw: return
        atoms = event.objects
        self.seqViewer.handleDeleteAtoms(atoms)


    def onAddCmdToViewer(self):
        
        from Pmv.selectionCommands import SelectionEvent
        from Pmv.colorCommands import ColorAtomsEvent
        from Pmv.deleteCommands import AfterDeleteAtomsEvent
        self.vf.registerListener(ColorAtomsEvent, self.handleColorAtomsEvent)
        self.vf.registerListener(SelectionEvent, self.handleSelectionEvent)
        self.vf.registerListener(ShowMoleculesEvent,
                                 self.handleShowMoleculesEvent)
        self.vf.registerListener(AfterDeleteAtomsEvent, self.handleDeleteAtomsEvents)
        if self.vf.hasGui:
            gui = self.vf.GUI

            #master = gui.workspace.pane('DockedCamera')
            master = gui.mainNoteBook.page('3D View')
            self.seqViewer = SeqViewGUI(master, onSelection = self.onSelect, vf=self.vf)
            self.viewerVisible = True
            ## for mol in self.vf.Mols:
            ##     labels = buildLabels(mol)
            ##     mol.sequenceLabels = labels
            ##     self.seqViewer.addMolecule(mol)


    def reparent(self, master):
        self.seqViewer.topFrame.destroy()
        self.seqViewer = SeqViewGUI(master, onSelection=self.onSelect, vf=self.vf)
        self.viewerVisible = True
        for mol in self.vf.Mols:
            labels = buildLabels(mol)
            mol.sequenceLabels = labels
            self.seqViewer.addMolecule(mol)


    ## def onAddObjectToViewer(self, obj):
    ##     """
    ##     update list of molecules in sequence viewer
    ##     """
    ##     print 'SEQVIEW onAddObjectToViewer'
    ##     if self.suspendRedraw: return
    ##     if self.vf.hasGui:
    ##         labels = buildLabels(obj)
    ##         obj.sequenceLabels = labels
    ##         self.seqViewer.addMolecule(obj)

        ## for res in obj.chains.residues:
        ##     if res.CAatom:
                
        ##     if res.hasCA:
        ##         ca = res.get('CA')
        ##         if len(ca)==0: # can happen when alternate position are available
        ##             ca = res.get('CA@.')
        ##             if len(ca)==0: # no CA found !
        ##                 res.seqViewAt = ca
        ##             else:
        ##                 res.seqViewAt = None
        ##         else:
        ##             res.seqViewAt = ca
        ##     else:
        ##         at = res.get('C1*')
        ##         if at:
        ##             res.seqViewAt = at
        ##         else:
        ##             res.seqViewAt = None


    def deleteObject(self, obj):
        """
        remove specified molecule from sequence viewer
        """
        if self.suspendRedraw: return
        if self.vf.hasGui: 
            self.seqViewer.removeMolecule(obj)

    def showHideGUI(self, visible = None):
        topFrame = self.seqViewer.topFrame
        ismapped = topFrame.winfo_ismapped()
        if visible == None:
            # toggles the "visible" state of the viewer
            if ismapped:
                # hide the Gui
                topFrame.forget()
                self.viewerVisible = False
            else:
                topFrame.pack(fill='both', expand=0)
                self.viewerVisible = True
        elif visible == True:
            if not ismapped:
                topFrame.pack(fill='both', expand=0)
                self.viewerVisible = True
        elif visible == False:
            if ismapped:
               topFrame.forget()
               self.viewerVisible = False 
            

    def getStateCodeForSeqViewer(self):
        """Returns a string with code that restores
        the configuration of the sequenceViewer """
        seqViewer = self.seqViewer
        lines = """# configure the Sequence Viewer\n"""
        for mol in seqViewer.sequenceOrder:
            lines += """self.sequenceViewer.colorSequenceString('%s')\n""" % mol.name
        stateDict = {}
        stateDict["viewerVisible"] = self.viewerVisible
        # ignoreChains dictionary
        ignoreChains = {}
        for mol, chlist in seqViewer.ignoreChains.items():
            newchlist = []
            for ch in chlist:
                newchlist.append(ch.full_name())
            ignoreChains[mol.name] = newchlist
        if len(ignoreChains):
            stateDict["ignoreChains"] = ignoreChains

        #userGaps
        userGaps = {}
        for mol, resgaps in seqViewer.userGaps.items():
            newresgaps = {}
            for res, ngaps in resgaps.items():
                newresgaps[res.full_name()] = ngaps
            userGaps[mol.name] = newresgaps
        if len(userGaps):
            stateDict["userGaps"] = userGaps

        lines += """svStateDict = %s \n""" % stateDict
        lines += """self.sequenceViewer.configureSeqViewer(svStateDict)\n"""
        # set colors for seq.viewer's background and Text
        bgColor = seqViewer.backcol
        lines += """self.sequenceViewer.seqViewer.colorTarget = 'background'\n"""
        lines += """self.sequenceViewer.seqViewer.setAColor(%s)\n"""%(bgColor,)
        atColor = seqViewer.activeTextColor
        lines += """self.sequenceViewer.seqViewer.colorTarget = 'activeText'\n"""
        lines += """self.sequenceViewer.seqViewer.setAColor('%s')\n"""%(atColor)
        itColor =  seqViewer.inactiveTextColor
        lines += """self.sequenceViewer.seqViewer.colorTarget = 'inactiveText'\n"""
        lines += """self.sequenceViewer.seqViewer.setAColor('%s')\n"""%(itColor)
        return lines


    def configureSeqViewer(self, stateDict=None):
        """ Configure the Sequence Viewer.
        stateDict - a dictionary containig:
        'viewerVisible' : True or False ;
        'ignoreChains'  : {mol : [list of chains to be ignored/hidden]} ;
        'userGaps'      : {mol: {residue : numOfGaps}};
        """
        if not stateDict:
            return
        viewerVisible = stateDict.get("viewerVisible", None)
        if viewerVisible is not None:
            self.showHideGUI(visible = viewerVisible)
        ignoreChains_ = stateDict.get("ignoreChains", None)
        ignoreChains = {}
        if ignoreChains_:
            for molname, chnames in ignoreChains_.items():
                mols = self.vf.Mols.get(molname)
                if not len(mols): continue
                mol = mols[0]
                ignoreChains[mol] = []
                for chname in chnames:
                    ignoreChains[mol].append(self.vf.expandNodes(chname)[0])
                    
        userGaps_ = stateDict.get("userGaps", None)
        userGaps = {}
        if userGaps_:
            for molname, resgaps in userGaps_.items():
                mols = self.vf.Mols.get(molname)
                if not len(mols): continue
                mol = mols[0]
                userGaps[mol] = {}
                for resname , resnum in resgaps.items():
                    res = self.vf.expandNodes(resname)[0]
                    userGaps[mol][res] = resnum

        self.seqViewer.configure(ignoreChains, userGaps)
            

                    

## class RefreshSeqViewerCommand(MVCommand):
##     """
##     The SequenceViewerCommand adds the Sequence Viewer widget
##     of the GUI
##     \nPackage : Pmv
##     \nModule  : seqViewerCommands
##     \nClass   : LoadSequenceViewerCommand
##     \nName    : loadSequenceViewer
##     """

##     def __init__(self, func=None):
##         MVCommand.__init__(self, func)

##     def __call__(self):
##         sqv = self.vf.sequenceViewer.seqViewer
##         sqv.clear()
##         for mol in self.vf.Mols:
##             sqv.draw(mol, resize=False)

               
commandList = [
    {'name':'sequenceViewer', 'cmd':SequenceViewerCommand(),
     'gui':None},
    {'name':'seqViewerSuspendRedraw', 'cmd':SeqViewerSuspendRedraw(),
     'gui':None},
##     {'name':'refreshSeqViewer', 'cmd':RefreshSeqViewerCommand(),
##      'gui':None},
]

def initModule(viewer):
    for dict in commandList:
        viewer.addCommand(dict['cmd'], dict['name'], dict['gui'])
