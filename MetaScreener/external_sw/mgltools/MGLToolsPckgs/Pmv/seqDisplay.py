########################################################################
#
# Date: 2012 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2012
#
#########################################################################
#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/seqDisplay.py,v 1.40 2014/09/26 19:44:15 annao Exp $
#
# $Id: seqDisplay.py,v 1.40 2014/09/26 19:44:15 annao Exp $
#
from mglutil.util.callback import CallbackFunction

from MolKit.PDBresidueNames import RNAnames, AAnames, DNAnames, ionNames
from MolKit.molecule import Atom, Molecule
from MolKit.protein import Residue, ResidueSet, Chain

import cairo, ImageTk, Image, Pmw
import math, time, sys
import Tkinter

from mglutil.gui.BasicWidgets.Tk.colorWidgets import BackgroundColorChooser, ColorChooser
from DejaVu.colorTool import TkColor, ToHSV, ToRGB

allResidueNames = {}
allResidueNames.update(RNAnames)
allResidueNames.update(AAnames)
allResidueNames.update(DNAnames)

def buildLabels(mol, ignoreChains=[], userGaps={}):
    assert isinstance(mol, Molecule)
    labels = {}
    numl = [] # list of characters for the number line
    labl = [] # list of characters for the primary sequence
    obj = []  # list of object associated with each character. None for characters that are not
              # representing molecular entities such as residues or chains
    numPt = labPt = len(numl) - 1
    for chain in mol.chains:
        cid = chain.id
        if cid==' ': cid='?'
        labl.extend([' ','|',cid,'|'])
        numl.extend([' ',' ', ' ', ' '])
        obj.extend( [None, None, chain, None])
        numPt += 4
        labPt += 4
        forceFirst = True
        if chain in ignoreChains: continue
        for res in chain.residues:

            #print 'RESIDUE', res.name, labPt, numPt
            resNumL = res.number
            noResNum = False
            try:
                resNum = int(resNumL)
            except ValueError: # some dlg files have '*' as residue number
                resNumL= '?'
                noResNum = True

            if forceFirst:
                #print '  FF', res.name, labPt, numPt
                if labPt<numPt:
                    [labl.append(' ') for i in range(numPt-labPt)]
                    obj.extend([None]*((numPt-labPt)))
                    labPt += (numPt-labPt)            
                if labPt>numPt:
                    [numl.append(' ') for i in range(labPt-numPt)]
                    numPt += (labPt-numPt)

                #print '   FF1', res.name, labPt, numPt

                # first handle gaps
                if userGaps.has_key(res):
                    nb = userGaps[res]
                    labl.extend(['-']*nb)
                    numl.extend([' ']*nb)
                    obj.extend( [None]*nb)
                    #print "user gaps1: ", nb
                    
                OneLetter = allResidueNames.get(res.type.strip(), '?')
                if OneLetter=='?': # put a gap, write full res name
                    labl.append(' '+res.type.strip().lower())
                    obj.append(res)
                    labPt += len(res.type.strip())+1
                    for c in ' '+resNumL: numl.append(c)
                    numPt += len(resNumL)+1
                    forceFirst = True
                else:
                    labl.append(OneLetter)
                    labPt += 1
                    obj.append(res)
                    numl.append(resNumL)
                    numPt += len(resNumL)

                    #print '   FF2', res.name, labPt, numPt, labl
                    forceFirst = False

            else:
                if noResNum or resNum > lastNum+1: # gap
                    #print 'GAP', resNum, lastNum, labPt, numPt
                    labl.append(' ')
                    labPt +=1
                    obj.append(None)
                    if labPt<=numPt:
                        [labl.append(' ') for i in range((numPt-labPt)+1)]
                        obj.extend([None]*((numPt-labPt)+1))
                        labPt += (numPt-labPt)+1

                    # first handle gaps
                    if userGaps.has_key(res):
                        nb = userGaps[res]
                        labl.extend(['-']*nb)
                        numl.extend([' ']*nb)
                        obj.extend( [None]*nb)
                        #print "user gaps2: ", nb

                    OneLetter = allResidueNames.get(res.type.strip(), '?')
                    if OneLetter=='?': # put a gap, write full res name
                        labl.append(' '+res.type.strip().lower())
                        obj.append(res)
                        labPt += len(res.type.strip())+1
                        for c in ' '+resNumL: numl.append(c)
                        numPt += len(resNumL)+1
                        forceFirst = True
                    else:
                        labl.append(OneLetter)
                        obj.append(res)
                        labPt +=1
                        numl.append(' ')
                        numPt += 1
                        for c in resNumL: numl.append(c)
                        numPt += len(resNumL)

                else: # No gap in residue numbering
                    #print '  NO GAP', res.name, labPt, numPt
                    if labPt==numPt: # last used position in charater in the number lines
                                     # is the same as the kast position used in label line
                        # first handle gaps
                        if userGaps.has_key(res):
                            nb = userGaps[res]
                            labl.extend(['-']*nb)
                            numl.extend([' ']*nb)
                            obj.extend( [None]*nb)
                            #print "user gaps3: ", nb
                        OneLetter = allResidueNames.get(res.type.strip(), '?')
                        if OneLetter=='?': # put a gap, write full res name
                            labl.append(' '+res.type.strip().lower())
                            obj.append(res)
                            labPt += len(res.type.strip())+1
                            for c in ' '+resNumL: numl.append(c)
                            numPt += len(resNumL)+1
                            forceFirst = True
                        else:
                            labl.append(OneLetter)
                            obj.append(res)
                            labPt +=1
                            if resNum%5==0:
                                for c in resNumL: numl.append(c)
                                numPt += len(resNumL)
                            else:
                                numl.append(' ')
                                numPt += 1
                    elif labPt<numPt:
                        # first handle gaps
                        if userGaps.has_key(res):
                            nb = userGaps[res]
                            labl.extend(['-']*nb)
                            numl.extend([' ']*nb)
                            obj.extend( [None]*nb)
                            #print "user gaps4: ", nb
                        OneLetter = allResidueNames.get(res.type.strip(), '?')
                        if OneLetter=='?': # put a gap, write full res name
                            [labl.append(' ') for i in range(numPt-labPt)]
                            obj.extend([None]*((numPt-labPt)))
                            labPt += (numPt-labPt)            
                            labl.append(' '+res.type.strip().lower())
                            obj.append(res)
                            labPt += len(res.type.strip())+1
                            for c in ' '+resNumL: numl.append(c)
                            numPt += len(resNumL)+1
                            forceFirst = True
                        else:
                            labl.append(OneLetter)
                            obj.append(res)
                            labPt +=1
                    else: # labPt > numPt
                        [numl.append(' ') for i in range(labPt-numPt)]
                        numPt += (labPt-numPt)+1
                        # first handle gaps
                        if userGaps.has_key(res):
                            nb = userGaps[res]
                            labl.extend(['-']*nb)
                            numl.extend([' ']*nb)
                            obj.extend( [None]*nb)
                            #print "user gaps5: ", nb
                        OneLetter = allResidueNames.get(res.type.strip(), '?')
                        if OneLetter=='?': # put a gap, write full res name
                            labl.append(' '+res.type.strip().lower())
                            obj.append(res)
                            labPt += len(res.type.strip())+1
                            for c in ' '+resNumL: numl.append(c)
                            numPt += len(resNumL)+1
                            forceFirst = True
                        else:
                            labl.append(OneLetter)
                            obj.append(res)
                            labPt +=1
                            if resNum%5==0:
                                for c in resNumL: numl.append(c)
                                numPt += len(resNumL)
                            else:
                                numl.append(' ')
                                numPt += 1

                    #print '     NO GAP1', res.name, labPt, numPt, labl
            if not noResNum:
                lastNum = resNum

    return labl, numl, obj


def buildSeqAlignmentLabels(aln, resList):
    labels = {}
    numl = [] # list of characters for the number line
    labl = [] # list of characters for the primary sequence
    obj = []  # list of objects associated with each character. None for characters that are not
              # representing residues ("-") 
    numPt = labPt = len(numl) - 1
    forceFirst = True
    ind = 0
    for OneLetter in aln:
        if not OneLetter.isalpha():  # "-"
            labl.append('-')
            numl.append(' ')
            obj.append(None)
            continue
        else:
            res = resList[ind]
            ind +=1
            resNumL = res.number
            noResNum = False
        try:
            resNum = int(resNumL)
        except ValueError: # some dlg files have '*' as residue number
            resNumL= '?'
            noResNum = True
        if forceFirst:
            #print '  FF', res.name, labPt, numPt
            labl.append(OneLetter)
            labPt += 1
            obj.append(res)
            numl.append(resNumL)
            numPt += len(resNumL)
            #print '   FF1', res.name, labPt, numPt, labl
            forceFirst = False
        else:
            if noResNum or resNum > lastNum+1: # gap
                #print 'GAP', resNum, lastNum, labPt, numPt, OneLetter, len(numl), numl[-5:]
                if labPt<=numPt:
                    n = numPt-labPt
                    # we remove the last number in the numl (replace it with " ")
                    #and put the resnumber of the "gap" residue 
                    if n>0:
                         numl=numl[:-n]
                         numPt -= n
                    for i in range(len(numl)-1, -1, -1):
                         if numl[i] != " ":  numl[i]=" "
                         else: break
                labl.append(OneLetter)
                obj.append(res)
                labPt +=1
                for c in resNumL: numl.append(c)
                numPt += len(resNumL)

            else: # No gap in residue numbering
                #print '  NO GAP', res.name, labPt, numPt
                if labPt==numPt: # last used position in charater in the number lines
                                 # is the same as the last position used in label line
                    labl.append(OneLetter)
                    obj.append(res)
                    labPt +=1
                    if resNum%5==0:
                        for c in resNumL: numl.append(c)
                        numPt += len(resNumL)
                    else:
                        numl.append(' ')
                        numPt += 1
                elif labPt<numPt:
                    labl.append(OneLetter)
                    obj.append(res)
                    labPt +=1
                else: # labPt > numPt
                    [numl.append(' ') for i in range(labPt-numPt)]
                    numPt += (labPt-numPt)+1
                    labl.append(OneLetter)
                    obj.append(res)
                    labPt +=1
                    if resNum%5==0:
                        for c in resNumL: numl.append(c)
                        numPt += len(resNumL)
                    else:
                        numl.append(' ')
                        numPt += 1
                #print '     NO GAP1', res.name, labPt, numPt, labl
        if not noResNum:
            lastNum = resNum

    return labl, numl, obj


class SeqViewGUI:

    def __init__(self, master=None, onSelection=None, vf=None):
        if master is None:
            master = Tkinter.Toplevel()

        self.master = master
        self.vf = vf
        # create a top Frame
        self.topFrame = Tkinter.Frame(master, bg='darkblue')
        self.tkbackcol = 'black'
        self.tkbackcolComp = 'white'
        self.backcolComp = (1.,1.,1.)
        self.backcol = (0.,0.,0.)

        self.rowScale = 1.6
        
        # create a paned widget inside the Frame
        pw = self.panew = Pmw.PanedWidget(self.topFrame, orient='horizontal')

        # add pane for molecule names canvas
        master2 = pw.add('molNames')
        master2.forget()
        master2.pack(fill='x', expand=0)
        master2.configure(bg=self.tkbackcol)#bg='green')
        master2.bind("<ButtonRelease-3>", self.postMainMenu)
        master2.bind("<FocusOut>", self.cancelMainMenu)
        
        master1 = pw.add('sequences')
        master1.forget()
        master1.pack(fill='x', expand=0)

        #create a canvas for molecule names
        self.molNamesCanvas = Tkinter.Canvas( 
            master2, bg=self.tkbackcol, highlightthickness=0, width=100, height=1)
        self.molNamesCanvas.pack(fill='x', expand=0)
        self.molNamesCanvas.bind("<ButtonRelease-3>", self.postMainMenu)
        self.molNamesCanvas.bind('<FocusOut>', self.cancelMainMenu)
        
        self.tkIdToObj = {} # lookup for canvas id to residue
        self.resToTkid = {}

        master = self.seqTop = Tkinter.Frame(master1)
        master.pack(fill='x', expand=0)
        
        self.selection  = [] # list of res
        self.canvas = Tkinter.Canvas(master, bg=self.tkbackcol,
                                     highlightthickness=0, height=1)
        self.canvas.pack(fill='x', expand=0)

        self.canvas.bind("<ButtonPress-1>", self.mouseButton1cb)

        size = self.fontSize = 12

        tid = self.canvas.create_text(0, 0, text='A', font=(('courier'), size, 'bold'))
        bb = self.canvas.bbox(tid)
        self.characterWidth = bb[2]-bb[0]
        self.characterHeight = bb[3]-bb[1]
        self.canvas.delete(tid)
        self.lasty = 0

        self.ratio = 1.0
        self.windowWidth = 1
        self.totalWidth = 1

        # make the canvas heigh enough for 1 molecule (i.e. 2 lines)
        self.canvas.configure(height=2*self.characterHeight)
        self.nbSequences = 0
        self.nbVisibleSequences = 0
        self.sequenceIndex = {} # index is a molecule name, value is a 1 based index
        self.sequenceOrder = [] # list of molecule in the order they are displayed from top to bottom
        self.isVisible = {} # index is a molecule name, value is True False
        self.seqLength = {} # index is a molecule name, value is a largest x values to draw sequence
        self.chainItems = {} # key is a chain, value is canvas is of chain label in sequence
        self.ignoreChains = {} # key is molecule value is list of chains to not show
        self.userGaps = {} # keys is molecule value is a dict {resAfterGap:number of gaps}
        # create canvas for bar
        self.barHeight = 1
        bcan = Tkinter.Canvas(master, height=1, bg='black', highlightthickness=0)
        bcan.pack(side='bottom', fill='x')
        self.bcan = bcan

        bcan.bind("<ButtonRelease-3>", self.postMainMenu)
        bcan.bind('<FocusOut>', self.cancelMainMenu)

        pw.pack(fill='x', expand=0)
        self.topFrame.pack(fill='both', expand=0)
        
        self.barPosX = 0
        self.barLength = 0

        # use a dummy image. It will be overwritten later
        self.imagetk = Tkinter.PhotoImage(data='R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53NJVNpmryZqsYDnemT3BQA7')
        self.imwidth = self.imagetk.width()
        self.imheight = self.imagetk.height()
        self.barid = bcan.create_image(
            -1000, 0, anchor=Tkinter.NW, image=self.imagetk, tags=('bar',))
        #self.barid = bcan.create_rectangle(0, 0, 1, self.barHeight, outline='white', width=3)#fill='gray75', outline='')
        bcan.tag_bind(self.barid, '<Button-1>', self.mouseDown)
        bcan.bind('<Configure>', self.expose_cb) # when window is resized we update things

        # draw selection
        self.scids = {}  # key is canvas item (i.e. letter), value canvas polygon item
        self.selection = ResidueSet([]) # list of residues
        self.selected = {} # keys are residues
        self.orientId = {} # keys are canvas ids of residue letters, value is canvas id of box in
                           # scroll bar
        self.currentSelectionBox = None
        
        self.onSelection = onSelection # call back when selection is made

        self.pady = 1

        self._makingSelection = False # used to avoid endless loops on selectione events
        self.mainMenu = None
        self.resMenu = None
        self.activeTextColor = 'white'
        self.inactiveTextColor = '#808080'

        self.colorFormWidgets = []
        self.selectedFrame = None
        self.colorTarget = 'background'

        self.selectForSuperimpose = False
        self.alignmentMols = []
        self.iCmd = {}
        self.selectForSuperimpose_cb = None


    def postMainMenu(self, event=None):
        if self.mainMenu:
            self.cancelMainMenu()
            return
        # this menu also pops up whith a right-click on a chain letter - try to avoid that:
        items = self.molNamesCanvas.find_overlapping(event.x-1, event.y-1, event.x+1, event.y+1)
        for it in items:
            tags = self.molNamesCanvas.gettags(it)
            if len(tags) >=3:
                for mol in self.sequenceOrder:
                    if tags[0] == mol.molTag:
                        if tags[1] == '?' or tags[1] in mol.chains.id : return
        menu = Tkinter.Menu(tearoff=False)
        menu.add_command(label='Set Color ...', command=self.setColors_cb)
        menu.post(event.x_root, event.y_root)
        self.mainMenu = menu

        
    ## uncomment to put this form in dashboard
    ##
    #def Close_cb(self, event=None):
    #    for w in self.colorFormWidgets: w.destroy()
    #    self.form.destroy()
    #    self.vf.dashboard.applyButton.unbind('<1>')
    #    self.vf.dashboard.closeButton.unbind('<1>')
    #    self.vf.dashboard.collapseParams()
    ##
    ## END uncomment to put this form in dashboard

    def Close_cb(self, event=None):
        for w in self.colorFormWidgets:
            w.destroy()
        #self.form.destroy()


    def executeSetColor(self, result):
        self.dialog.deactivate(result)
        self.Close_cb()

    def setColors_cb(self, event=None):

        ## uncomment to put this form in dashboard
        ##
        #if self.vf.dashboard.columnShowingForm:
        #    self.vf.dashboard.columnShowingForm.Close_cb()

        #master = self.form = Tkinter.Frame(self.vf.dashboard.master3)
        ##
        ## END uncomment to put this form in dashboard

        #master = self.form  = Tkinter.Toplevel()
        #master.protocol('WM_DELETE_WINDOW',self.Close_cb)

	# Create the dialog.
	self.dialog = Pmw.Dialog(#master,
	    buttons = ('Close',),
	    defaultbutton = 'Close',
	    title = 'Set Seq View. Colors',
	    command = self.executeSetColor)

        master = self.dialog.interior()
        w = Tkinter.Label(master, text='Background Color')
        w.grid(column=0, row=0, sticky='ew')
        self.colorFormWidgets.append(w)
        if self.colorTarget=='background': relief = 'sunken'
        else: relief='raised'
        w = Tkinter.Frame(master, bg=self.tkbackcol, width=40, height=20, relief=relief,
                          borderwidth=3, pady=5)
        w.grid(column=1, row=0)
        if self.colorTarget=='background': self.selectedFrame = w
        cb = CallbackFunction(self.selectWhatTocolor, 'background', w)
        w.bind("<ButtonRelease-1>", cb)
        self.colorFormWidgets.append(w)

        w = Tkinter.Label(master, text='Active Text Color')
        w.grid(column=0, row=1, sticky='ew')
        self.colorFormWidgets.append(w)
        if self.colorTarget=='activeText': relief = 'sunken'
        else: relief='raised'
        w = Tkinter.Frame(master, bg=self.activeTextColor, width=40, height=20, relief=relief,
                          borderwidth=3, pady=5)
        cb = CallbackFunction(self.selectWhatTocolor, 'activeText', w)
        w.bind("<ButtonRelease-1>", cb)
        w.grid(column=1, row=1)
        if self.colorTarget=='activeText': self.selectedFrame = w
        self.colorFormWidgets.append(w)

        w = Tkinter.Label(master, text='Inactive Text Color')
        w.grid(column=0, row=2, sticky='ew')
        self.colorFormWidgets.append(w)
        if self.colorTarget=='inactiveText': relief = 'sunken'
        else: relief='raised'
        w = Tkinter.Frame(master, bg=self.inactiveTextColor, width=40, height=20, relief=relief,
                          borderwidth=3, pady=5)
        cb = CallbackFunction(self.selectWhatTocolor, 'inactiveText', w)
        w.bind("<ButtonRelease-1>", cb)
        w.grid(column=1, row=2)
        if self.colorTarget=='inactiveText': self.selectedFrame = w
        self.colorFormWidgets.append(w)

        cc = ColorChooser(master=master, immediate=1, commands=self.setAColor)
        cc.grid(column=0, row=3, columnspan=2, sticky='snew')
        # MS not sure if not destroying the cc creates a memory leak
        
        w = Tkinter.Button(master, text='Restore Default colors', command=self.setDefaultColors_cb)
        w.grid(column=0, row=4, columnspan=2, sticky='ew')
        self.colorFormWidgets.append(w)

        ## comment to put this form in dashboard
        ##
        #w = Tkinter.Button(master, text='Close', command=self.Close_cb)
        #w.grid(column=0, row=5, columnspan=2, sticky='ew')
        #self.colorFormWidgets.append(w)
        ##
        ## END comment to put this form in dashboard
       
        ## uncomment to put this form in dashboard
        ##
        #self.form.pack(expand=1, fill='both')
        #self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)
        #self.vf.dashboard.expandParams(self.form)
        #self.vf.dashboard.columnShowingForm = self
        ##
        ## END uncomment to put this form in dashboard
        self.dialog.activate(globalMode = False)
        self.mainMenu = None


    def selectWhatTocolor(self, what, frame, event=None):
        if self.selectedFrame:
            self.selectedFrame.configure(relief='raised')
        self.selectedFrame = frame
        frame.configure(relief='sunken')
        self.colorTarget = what

            
    def setAColor(self, color):
        if self.selectedFrame:
            self.selectedFrame.configure(bg=TkColor(color))
        if self.colorTarget=='background':
            self.setBackgroundColor(color)
        elif self.colorTarget=='activeText':
            if type(color) == str:
                self.activeTextColor = color
            else:
                self.activeTextColor = TkColor(color)
            self.canvas.itemconfig('activeText', fill=self.activeTextColor)
            self.molNamesCanvas.itemconfig('activeText', fill=self.activeTextColor)
        elif self.colorTarget=='inactiveText':
            if type(color) == str:
                self.inactiveTextColor = color
            else:
                self.inactiveTextColor = TkColor(color)
            self.canvas.itemconfig('inactiveText', fill=self.inactiveTextColor)
            self.molNamesCanvas.itemconfig('inactiveText', fill=self.inactiveTextColor)
            
        
    def setDefaultColors_cb(self, event=None):
        self.activeTextColor = 'white'
        self.inactiveTextColor = '#808080'
        self.canvas.itemconfig('activeText', fill=self.activeTextColor)
        self.molNamesCanvas.itemconfig('activeText', fill=self.activeTextColor)
        self.canvas.itemconfig('inactiveText', fill=self.activeTextColor)
        self.molNamesCanvas.itemconfig('inactiveText', fill=self.activeTextColor)
        self.setBackgroundColor((0,0,0))

        
    def cancelMainMenu(self, event=None):
        self.mainMenu.unpost()
        self.mainMenu = None

        
    def setBackgroundColor(self, color):
        self.backcol = color
        self.tkbackcol = tkcol = TkColor(color)

        if color[0] >.9 and color[1] >.9 and color[2] >.9:
            self.backcolComp = (0,0,0)
            self.tkbackcolComp = '#000000'
        else:
            self.backcolComp = (1,1,1)
            self.tkbackcolComp = '#FFFFFF'

        self.canvas.configure(bg=tkcol)
        self.bcan.configure(bg=tkcol)
        self.molNamesCanvas.configure(bg=tkcol)
        self.panew.pane('molNames').configure(bg=tkcol)
        self.updateScrollBar()
        
        
    def clear(self):
        self.canvas.delete('all')
        for mol in self.sequenceIndex.keys():
            self.bcan.delete(*self.orientId.values())
        self.lasty = 0
        self.scids = {}

        
    def mouseDown(self, event):
        # scroll bar mouse down
        self.barOffset = self.barPosX-event.x
        self.bcan.tag_bind(self.barid, '<Motion>', self.motion)
        self.bcan.tag_bind(self.barid, '<ButtonRelease-1>', self.release)


    def motion(self, event):
        # scroll bar mouse motion
        self.barPosX = event.x+self.barOffset
        if self.barPosX<0:
            self.barPosX = 0
        if self.barPosX+self.barLength>self.windowWidth:
            self.barPosX = self.windowWidth-self.barLength
        self.bcan.coords(self.barid, self.barPosX, 0)#, self.barPosX+self.barLength, self.barHeight)
        self.canvas.xview('moveto', float(self.barPosX)/self.windowWidth)
        

    def release(self, event):
        # scroll bar mouse button 1release
        self.bcan.tag_unbind(self.barid, '<Motion>')
        self.bcan.tag_unbind(self.barid, '<ButtonRelease-1>')


    def expose_cb(self, event):
        self.updateWindowWidth()
        self.updateScrollBar()

        
    def updateWindowWidth(self):
        self.master.update() # give the window tiem to appear
        #get the width of the window
        self.windowWidth = self.canvas.winfo_width()
        self.ratio = float(self.windowWidth)/self.totalWidth
        return self.windowWidth


    def updateTotalWidth(self):
        bb = self.canvas.bbox('all')
        if bb is None: return None
        self.totalWidth = bb[2]-bb[0]
        self.ratio = float(self.windowWidth)/self.totalWidth
        return self.totalWidth
    

    def ranksOfVisibleMolecules(self):
        # find rank of visible molecule in drawing order
        molInd = {}
        ind = 0
        for mol in self.sequenceOrder:
            if self.isVisible[mol]:
                molInd[mol] = ind
                ind += 1
        return molInd


    def updateScrollBar(self):
        canvas = self.canvas
        bcanvas = self.bcan

        # compute and configure the height of the scrolling bar
        self.barHeight = 4 + self.nbVisibleSequences*4 # 2 pixels above and below and 2 per sequence
                                                       # 1 pixels between sequences
        self.bcan.configure(height=self.barHeight+1) # 1 is for padding below the bar (between bar and canvas bottom)

        width = self.updateWindowWidth()
        totalWidth = self.updateTotalWidth()
        if totalWidth is None: return None
        self.barLength = (float(width)*width)/totalWidth
        if self.ratio >= 1.0:
            bcanvas.itemconfig(self.barid, state='hidden')
        else:
            # create a 10x10 image for scroll bar
            w = int(self.barLength)
            h = int(self.barHeight)
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            self.ctx = cairo.Context (self.surface)
            self.ctx.rectangle( 0, 0, w, h)

            red, green, blue = self.backcol
            if sys.platform=='win32':
                self.ctx.set_source_rgba(red, green, blue,0)
            else:
                self.ctx.set_source_rgba(red, green, blue,.2)
            self.ctx.fill()
            self.ctx.rectangle( 0, 0, w, h)
            self.ctx.set_source_rgb(*self.backcolComp)
            self.ctx.set_line_width(2)
            self.ctx.stroke()

            # turn cairo image into PIL image
            buf = self.surface.get_data()
            image = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'RGBA', 0, 1)
            self.imagetk = ImageTk.PhotoImage(image=image)
            bcanvas.itemconfig(self.barid, state='normal', image=self.imagetk)
            bcanvas.coords(self.barid, self.barPosX, 0)#, self.barPosX+self.barLength, self.barHeight)

        molInd = self.ranksOfVisibleMolecules()
    
        # resize boxes
        for mol, index in molInd.items():
            if not self.isVisible[mol]: continue
            y0 = 1 + index*4
            for tid in canvas.find_withtag(mol.molTag):
                bb = canvas.bbox(tid)
                bid = self.orientId.get(tid, None)
                if bid:
                    bcanvas.coords(bid, bb[0]*self.ratio, y0, bb[2]*self.ratio, y0+2)

        if self.ratio < 1.0:
            bcanvas.tag_raise(self.barid)


    def resizeCanvases(self):
        # make the canvas heigh enough for 1 molecule (i.e. 2 lines)
        height = self.rowScale*self.nbVisibleSequences*self.characterHeight+10
        #print "resizeCanvases:", height, self.nbVisibleSequences
        self.molNamesCanvas.configure(height=height)
        self.canvas.configure(height=height)
        self.configureScrollRegion()
        self.updateScrollBar()
        self.panew.setnaturalsize()


    def jumpToChain(self, chain, event):
        bb = self.bcan.bbox(self.barid)
        curRatio = float(bb[0])/self.windowWidth
        bb = self.canvas.bbox(self.chainItems[chain])
        newRatio = float(bb[0])/self.totalWidth
        nbSteps = 50
        delta = (newRatio-curRatio)
        incr = (newRatio-curRatio)/float(nbSteps)

        ratio = curRatio
        integral = 0.0
        t0 = time.time()
        animTime = 0.5 # (seconds)
        for i in range(nbSteps):
            lAtenuationFactor = math.sin(math.pi*i/nbSteps) / 31.8205 # 31 is the integral of lAtenuationFactor
            ratio += lAtenuationFactor*delta
            integral += lAtenuationFactor
            self.canvas.xview('moveto', ratio)
            self.canvas.update()
            self.bcan.move(self.barid, int(lAtenuationFactor*delta*self.windowWidth),0)
            t1 = time.time()
            dtime = t1-t0
            t0 = t1
            if dtime<(animTime/nbSteps):
                time.sleep((animTime/nbSteps)-dtime)

        self.barPosX = self.bcan.bbox(self.barid)[0]


    def drawSequenceforMol(self, mol, labels, numbers, objects):
        """
        this is used to display a row of numbers above a row of characters.
        Objects is used to identify molecular entities when we click on the labels. It is
        a list of objects and has None for characters such as spaces
        """
        if not self.sequenceIndex.has_key(mol):
            posy = None
        else:
            # delete all canvas items for that molecule
            if not self.isVisible[mol]:
                self.showSequence(mol)
            self.canvas.delete(mol.molTag)

            # compute y position for that molecule on canvas
            molInd = self.ranksOfVisibleMolecules()
            posy = molInd[mol]*self.rowScale*self.characterHeight

        # set the 3 tuple used to draw this molecule
        mol.sequenceLabels = [labels, numbers, objects]

        self.addMolecule(mol, posy)

        
    def showHideChain(self, chain, event):
        mol = chain.top
        cid = chain.id
        if cid==' ': cid='?'        
        item = self.molNamesCanvas.find_withtag("%s&&%s"%(mol.molTag, cid))
        if chain in self.ignoreChains[mol]:
            self.ignoreChains[mol].remove(chain)
            self.molNamesCanvas.itemconfig(item, fill=self.activeTextColor)
            show = True
        else:
            self.ignoreChains[mol].append(chain)
            self.molNamesCanvas.itemconfig(item, fill=self.inactiveTextColor)
            show = False

        # rebuild labels
        mol.sequenceLabels = buildLabels(mol, self.ignoreChains[mol], self.userGaps[mol])

        # delete items for this molecule
        self.canvas.delete(mol.molTag)

        # rebuild Tk items
        molInd = self.ranksOfVisibleMolecules()
        posy = molInd[mol]*self.rowScale*self.characterHeight
        self.addMolecule(mol, posy=posy)

        if show:
            canvas = self.canvas
            bcan = self.bcan
            # redo selection
            items = []
            for res in chain.residues:
                if self.selected.has_key(res):
                    items.append(self.resToTkid[res])
            self.selectItems(items)


    def handleDeleteAtoms(self, atoms):
        for mol in atoms.top.uniq():
            if not hasattr(mol, 'sequenceLabels'): continue
            labl, numl, obj=  mol.sequenceLabels
            #print numl
            #print labl
            labl1, numl1, obj1 = buildLabels(mol , self.ignoreChains[mol], self.userGaps[mol])
            #print "--------------------------"
            #print numl1
            #print labl1
            if labl != labl1:
                #rebuild the seq.string for this molecule in the viewer
                self.canvas.delete(mol.molTag)
                mol.sequenceLabels = (labl1, numl1, obj1)

                # rebuild Tk items
                molInd = self.ranksOfVisibleMolecules()
                posy = molInd[mol]*self.rowScale*self.characterHeight
                self.addMolecule(mol, posy=posy)
                
        
    def addMolecule(self, molecule, posy=None, molInd=None):
        if posy is None:
            # when we add the molecule we create all items on the canvas but hid some
            if self.sequenceIndex.has_key(molecule):
                return # the molecule was already added

            # add the molecule and increment the number of sequences
            self.nbSequences += 1
            if molInd is not None:
                self.sequenceIndex[molecule] = molInd+1
                self.sequenceOrder.insert(molInd, molecule)
                self.lasty =  molInd*self.rowScale*self.characterHeight
            else:
                self.sequenceIndex[molecule] =  self.nbSequences
                self.sequenceOrder.append(molecule)
            self.ignoreChains[molecule] = []
            self.isVisible[molecule] = True
            self.userGaps[molecule] = {}# no gaps to start with
            self.nbVisibleSequences += 1
            posy1 = self.lasty
        else:
            posy1 = posy
        if not hasattr(molecule, "sequenceLabels"):
            labels = buildLabels(molecule)
            molecule.sequenceLabels = labels
        else:
            labels = molecule.sequenceLabels
        canvas = self.canvas
        bcan = self.bcan

        ## now create all the canvas items
        ## we create letter(s) for each character in labels[1]. This is the numbers line
        ## we create letter(s) for each character in labels[0]. This is the sequence line
        size = self.fontSize
        posy2 = posy1 + self.characterHeight*.8
        width = self.characterWidth
        tkColFormat = '#%02X%02X%02X'
        scids = self.scids

        # we add '_' in front in case the moelcule name looks like an int which is not a legal tag
        molName = molecule.molTag = '_'+molecule.name

        if posy is None:
            # create the molecule name
            mcan = self.molNamesCanvas
            cid = mcan.create_text( 10, posy1+2, text=molecule.name, anchor='nw',
                                    font=(('courier'), size, 'bold'), fill=self.activeTextColor,
                                    tags=(molName,'activeText'))
            # add chain names
            posx = 20

            for c in molecule.chains:
                if c in self.ignoreChains[molecule]:
                    color = self.inactiveTextColor
                    tag = 'inactiveText'
                else:
                    color = self.activeTextColor
                    tag = 'activeText'
                chainid = c.id
                if chainid==' ': chainid='?'
                cid = mcan.create_text( posx, posy2+3, text=chainid, anchor='nw',
                                        font=(('courier'), size-2, ''), fill=color,
                                        tags=(molName ,chainid, tag))

                cb1 = CallbackFunction(self.jumpToChain, c)
                mcan.tag_bind(cid, "<Button-1>", cb1)
                cb3 = CallbackFunction(self.showHideChain, c)
                mcan.tag_bind(cid, "<Button-3>", cb3)
                posx += width

        # create the letter for the number line
        labs, numList, obj = labels
        posx = 0
        for num in numList:
            tid = canvas.create_text(posx, posy1, text=num, anchor='nw',
                                     font=(('courier'), size-2, 'bold'), fill=self.activeTextColor,
                                     tags=(molName,'number', 'activeText'))
            posx += len(num)*width

        # create the letters for the sequence line
        posx = 0
        pady = self.pady
        scids = self.scids
        tkIdToObj = self.tkIdToObj
        resToTkid = self.resToTkid
        orientId = self.orientId

        for lab, res in zip(labs, obj):

            # find color or residue.
            if res is None or isinstance(res, Chain): # non pickable charaters, i.e. mol name etc
                textcol = self.activeTextColor
                tag = 'activeText'
                if lab=='-' or (isinstance(res, Chain) and res in self.ignoreChains[molecule]):
                    textcol = self.inactiveTextColor
                    tag = 'inactiveText'
            else:
                # For amino acids we take color of lines of CA atom
                # if there is no CA we use gray50
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
                if res.CAatom is not None:
                    col = res.CAatom.colors['lines']
                elif res.C1atom is not None:
                    col = res.C1atom.colors['lines']
                else:
                    col = (.5, .5, .5)
                # create Tkcolors
                # if the residue is selected, we color the letter black and create a box behind it
                #    with residue color
                # else:
                #    we color the letter the same as the residue
                textcol = tkColFormat%(col[0]*255,col[1]*255, col[2]*255)
                backCol = tkColFormat%(col[0]*255,col[1]*255, col[2]*255)
                tag = ''
                
            # draw residue letter
            tid = canvas.create_text(posx, posy2, text=lab, anchor='nw', tags=('letter',molName,tag),
                                     font=(('courier'), size, 'bold'), fill=textcol)

            # build lookup allowing us to get a residue from the letter canvas id
            tkIdToObj[tid] = res
            # build lookup allowing us to the letter's canvas id from for a residue
            resToTkid[res] = tid

            if isinstance(res, Residue):
                # draw selection polygon, but hide it until the residue is selected
                bb = canvas.bbox(tid)
                scid = canvas.create_rectangle( bb[0], bb[1]+pady, bb[2], bb[3]-pady, fill=backCol,
                                                outline='', tags=('bg', molName), state='hidden')
                cbres = CallbackFunction(self.postResidueMenu, res, lab)
                canvas.tag_bind(tid, "<Button-3>", cbres)
                scids[tid] = scid

                # draw box on scroll bar canvas
                y0 = 4 + (self.sequenceIndex[molecule]-1)*6
                oid = bcan.create_rectangle( bb[0]*self.ratio, y0, bb[2]*self.ratio, y0+4,
                                             fill=backCol, outline='', tags=(molName, 'feedback'),
                                             state='hidden')
                orientId[tid] = oid
            elif isinstance(res, Chain):
                self.chainItems[res] = tid
                #cb1 = CallbackFunction(self.jumpToChain, res)
                #canvas.tag_bind(tid, "<Button-1>", cb1)
                cb3 = CallbackFunction(self.showHideChain, res)
                canvas.tag_bind(tid, "<Button-3>", cb3)
                
            # increment the x position
            posx += width*len(lab)

        self.seqLength[molecule] = canvas.bbox(molName)[2]

        # lower all boxes below the labels
        canvas.tag_lower('bg')

        self.updateTotalWidth()
        self.resizeCanvases()

        # configure scroll area
        #self.configureScrollRegion()

        # configure scroll bar
        #self.updateScrollBar()

        # resize paned widget
        #self.panew.setnaturalsize()


    def configureScrollRegion(self):
        canvas = self.canvas
        self.lasty = self.nbVisibleSequences*self.rowScale*self.characterHeight
        # configure the scrolling area
        bb = self.canvas.bbox('all')
        if bb is None: return
        maxx = bb[2]
        canvas.configure(scrollregion=(0,0,maxx,self.lasty))
       

    def selectItems(self, items):
        canvas = self.canvas
        bcan = self.bcan
        scids = self.scids
        orientId = self.orientId
        residues = []

        for tid in items:
            if tid == self.currentSelectionBox:
                continue # selection box
            res = self.tkIdToObj.get(tid)
            if res is None:
                continue # not a residue
            residues.append(res)

            # change letter color to black
            self.canvas.itemconfig(tid, fill='black')

            # make polygons behind letters visible
            canvas.itemconfig(scids[tid], state='normal')

            # add 'selected' tag
            canvas.addtag_withtag('selected', tid)
            canvas.addtag_withtag('selected', scids[tid])
            bcan.addtag_withtag('selected', orientId[tid])
            
            # make polygons in scroll bar visible
            bcan.itemconfig(orientId[tid], state='normal')

        self.updateScrollBar()
        return residues
       

    def deselectItems(self, items):
        canvas = self.canvas
        bcan = self.bcan
        scids = self.scids
        orientId = self.orientId
        tkColFormat = '#%02X%02X%02X'
        residues = []

        for tid in items:
            if tid == self.currentSelectionBox:
                continue # selection box
            res = self.tkIdToObj.get(tid)
            if res is None:
                continue # not a residue
            residues.append(res)

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
            if res.CAatom is not None:
                col = res.CAatom.colors['lines']
            elif res.C1atom is not None:
                col = res.C1atom.colors['lines']
            else:
                col = (.5, .5, .5)
            tkcol = tkColFormat%(col[0]*255,col[1]*255, col[2]*255)
            # change letter color to residue color
            canvas.itemconfig(tid, fill=tkcol)

            # make polygons behind letters visible
            canvas.itemconfig(scids[tid], state='hidden')

            # make polygons in scroll bar visible
            bcan.itemconfig(orientId[tid], state='hidden')

            # remove 'selected' tag
            canvas.dtag(tid, 'selected')
            canvas.dtag(scids[tid], 'selected')
            bcan.dtag(orientId[tid], 'selected')

        self.updateScrollBar()

        return residues

                
    def _showSequence(self, mol):
        self.isVisible[mol] = True
        self.nbVisibleSequences += 1
        # show sequence and numbers (i.e. tag molecule but not bg
        self.canvas.itemconfig("%s&&!bg"%mol.molTag, state='normal')
        # show selected background poly and scroll bar items
        self.canvas.itemconfig("%s&&selected"%mol.molTag, state='normal')
        self.bcan.itemconfig("%s&&selected"%mol.molTag, state='normal')
        # show molecule name
        self.molNamesCanvas.itemconfig(mol.molTag, state='normal')

        
    def _hideSequence(self, mol):
        self.isVisible[mol] = False
        self.nbVisibleSequences = max(0, self.nbVisibleSequences-1)
        self.canvas.itemconfig(mol.molTag, state='hidden')
        self.molNamesCanvas.itemconfig(mol.molTag, state='hidden')
        self.bcan.itemconfig(mol.molTag, state='hidden')


    def moveUp(self, mol):
        self.canvas.move(mol.molTag, 0, -self.characterHeight*self.rowScale)
        self.molNamesCanvas.move(mol.molTag, 0, -self.characterHeight*self.rowScale)
        self.bcan.move(mol.molTag, 0, -4)
    

    def moveDown(self, mol):
        self.canvas.move(mol.molTag, 0, self.characterHeight*self.rowScale)
        self.molNamesCanvas.move(mol.molTag, 0, self.characterHeight*self.rowScale)
        self.bcan.move(mol.molTag, 0, 4)


    def hideSequence(self, mol):
        if not self.isVisible.has_key(mol):
            return
        self._hideSequence(mol)
        ind = self.sequenceIndex[mol]
        for molec, index in self.sequenceIndex.items():
            if index > ind:
                self.moveUp(molec)
        #self.configureScrollRegion()
        #self.updateScrollBar()
        self.resizeCanvases()
        #self.panew.setnaturalsize()
        

    def showSequence(self, mol):
        #print "showSequence", mol.name,
        if not self.isVisible.has_key(mol):
            return
        self._showSequence(mol)
        ind = self.sequenceIndex[mol]
        for molec, index in self.sequenceIndex.items():
            if index > ind:
                #print "moveDown:", molec, index
                self.moveDown(molec)
        #self.configureScrollRegion()
        #self.updateScrollBar()
        self.resizeCanvases()
        #self.panew.setnaturalsize()
                

    def mouseButton1cb(self, event):
        self.x0 = self.canvas.canvasx(event.x)
        self.y0 = self.canvas.canvasy(event.y)
        # tag items items to the right
        shift = ctrl = caps = numlock = leftAlt = rightAlt = mb1 = mb2 = mb3 = False
        if event.state & 1: shift = True
        if event.state & 2: caps = True
        if event.state & 4: ctrl = True
        if event.state & 8: leftAlt = True
        if event.state & 16: numlock = True
        if event.state & 128: rightAlt = True
        if event.state & 256: mb1 = True
        if event.state & 512: mb2 = True
        if event.state & 1024: mb3 = True

        #print 'FUGU', shift, caps, ctrl, numlock, leftAlt, rightAlt, mb1, mb2, mb3
        if shift and ctrl:#event.state==5:
            self.canvas.addtag(
                'toRight', 'overlapping',
                self.x0, self.y0-self.characterHeight*.6,
                self.x0+self.updateTotalWidth(), self.y0)
            # since selection polygons might be hidden
            # we need to tag them too
            for cid in self.canvas.find_withtag('toRight&&letter'):
                scid = self.scids.get(cid, None)
                if scid: # chain labels are selected by _withtag but have no polygon
                    self.canvas.addtag_withtag('toRight', scid)

        if not shift and not ctrl: # no modifier:
            self.startSelectionBox(event)
        elif shift and ctrl: # Shift-Ctrl
            self.openCloseGap(event)

    ##
    ## insert gaps or close gaps
    ##
    def openCloseGap(self, event):
        items = self.canvas.find_withtag('current')
        if len(items)==0: return
        res = self.tkIdToObj.get(items[0], None)
        if res is None or isinstance(res, Chain):
            return
        self.gapMol = res.top
        self.gapRes = res
        # compute posy for picked residue
        bb = self.canvas.bbox(items[0])
        self.cposx = bb[0]
        self.cposy = bb[1]
        
        self.canvas.bind("<Button1-Motion>",self.gapMotion)
        self.canvas.bind("<Button1-ButtonRelease>",self.gapEnd)


    def gapMotion(self, event):
        self.x1 = self.canvas.canvasx(event.x)
        self.y1 = self.canvas.canvasy(event.y)

        #dragging to left closes a gap. Can't be done if there is no gap.
        #print 'gapMotion', resLeft, self.x1, self.x0, self.characterWidth
        if self.x1 < self.x0-self.characterWidth:
            toLeft = self.canvas.find_overlapping(
                self.x0-self.characterWidth-1, self.y0-1,
                self.x0-self.characterWidth+1, self.y0+1)
            if self.canvas.itemcget(toLeft, 'text')=='-':
                self.closeGap(toLeft)
                self.x0 -= self.characterWidth
                self.cposx -= self.characterWidth

        #dragging to right opens a gap. Can always be done.
        if self.x1 > self.x0+self.characterWidth:
            self.openGap()
            self.x0 += self.characterWidth
            self.cposx += self.characterWidth


    def openGap(self):
        # shift all canvas items to the right
        self.canvas.move('toRight', self.characterWidth, 0)

        # put an '-' in the sequence
        mol = self.gapMol
        res = self.gapRes
        self.canvas.create_text(self.cposx, self.cposy, text='-', anchor='nw', tags=('letter', mol.molTag, 'usergap'),
                                font=(('courier'), self.fontSize, 'bold'), fill=self.inactiveTextColor)

        # remember this gap
        if self.userGaps[mol].has_key(res):
            self.userGaps[mol][res] += 1
        else:
            self.userGaps[mol][res] = 1
        

    def closeGap(self, cid):
        # cid is the canvas item tot he left of what was clicked on (normally '-' when we get here)
        if cid:
            self.canvas.delete(cid)

        # shift all canvas items to the left
        self.canvas.move('toRight', -self.characterWidth, 0)

        # remove this gap
        self.userGaps[self.gapMol][self.gapRes] -= 1


    def gapEnd(self, event):
        self.resizeCanvases()
        self.canvas.unbind("<Button1-Motion>")
        self.canvas.unbind("<Button1-ButtonRelease>")
        self.canvas.dtag('toRight', 'toRight')
        del self.gapMol
        del self.gapRes
        del self.cposx
        del self.cposy
        del self.x0
        del self.y0
        del self.x1
        del self.y1

    ##
    ## select/deselect residues
    ##
    def startSelectionBox(self, event=None):
        items = self.canvas.find_withtag('current')
        if len(items)==0: return
        res = self.tkIdToObj.get(items[0], None)
        if res is None or isinstance(res, Chain):
            return
        if self.selected.has_key(res):
            self._mode='deselect'
        else:
            self._mode='select'
        canvas = self.canvas
        bb = canvas.bbox(*items)
        self.x0 = bb[0]
        self.y0 = bb[1]
        self.x1 = self.x0+1
        self.y1 = self.y0+1
        self.thisColors = {}
        pady = self.pady
        y1 = bb[3]
        y0 = bb[1]
        if self.selectForSuperimpose:
            mol = res.top
            molind = self.ranksOfVisibleMolecules()[mol]
            if molind == 0:
                y1 = 2*self.rowScale*self.characterHeight
            else:
                y0 = self.characterHeight
            self.y1 = y1
            self.y0 = y0


        self.currentSelectionBox = canvas.create_rectangle( bb[0], y0+pady, bb[2], y1-pady,
                                                            fill='', outline='white')
        canvas.tag_raise(self.currentSelectionBox)
        self.canvas.bind("<Button1-Motion>",self.continueSelectionBox)
        self.canvas.bind("<Button1-ButtonRelease>",self.endSelectionBox)
        

    def continueSelectionBox(self, event=None):
        self.x1 = self.canvas.canvasx(event.x)
        if not self.selectForSuperimpose:
            self.y1 = self.canvas.canvasy(event.y)
        pady = self.pady
        if self.y0 < self.y1:
            mvdown = True
            y0 = self.y0+pady
            y1 = self.y1-pady
        else: # moving up
            mvdown = False
            y0 = self.y1-pady
            y1 = self.y0+pady
        items = self.canvas.find_overlapping(self.x0, y0,self.x1, y1)
        bid = self.currentSelectionBox
        items = [x for x in items if x!=bid]
        canvas = self.canvas
        if len(items):
            bb = canvas.bbox(*items)
            if not mvdown: y0 = bb[1]+pady
            y1 = bb[3]-pady
            canvas.coords(self.currentSelectionBox, bb[0], y0, bb[2], y1)


    def endSelectionBox(self, event=None):
        canvas = self.canvas
        items = canvas.find_overlapping(self.x0,self.y0,self.x1,self.y1)
        self.canvas.unbind("<Button1-Motion>")
        self.canvas.unbind("<Button1-ButtonRelease>")
        self.canvas.delete(self.currentSelectionBox)
        self._makingSelection = True
        if hasattr(self, '_mode'): # for some reason we sometime get here with _mode ! (MS July 2012)
            #print "MODE:", self._mode, len(self.selected), len(self.selection)
            if self._mode=='select':
                residues = self.selectItems(items)
                thisSelection = ResidueSet(residues)
                self.selection += thisSelection
                deselect = False
            else:
                residues = self.deselectItems(items)
                thisSelection = ResidueSet(residues)
                self.selection -= thisSelection
                deselect = True
            self.selected = {}.fromkeys(self.selection)
            self.selection = ResidueSet(self.selected.keys())
            #print "selected:" , len(self.selected)
            if self.onSelection:
                self.onSelection(thisSelection, deselect)
            if self.selectForSuperimpose and self.selectForSuperimpose_cb:
                refMolName = self.alignmentMols[0].name
                mvMolName = self.alignmentMols[1].name
                set1, set2 = self.selectedAlignmentPairs(refMolName, mvMolName)
                self.selectForSuperimpose_cb(set1, set2)
            del self._mode
        self._makingSelection = False


    def showAlignment(self, refMol, moveMol):
        # refMol and moveMol lists [mol, letterSequense, residueSet]
        if  self.selectForSuperimpose or len(self.alignmentMols): return
        self.selectForSuperimpose = True
        # clear previous selection:
        if len(self.selected):
            self.vf.deselect(self.vf.selection)
        self.alignmentMols = [refMol[0], moveMol[0]]
        # disable "picking command" selection in the Viewer
        for k, v in self.vf.ICmdCaller.commands.value.items():
            if v == self.vf.select or v == self.vf.deselect:
                self.iCmd[k] = v
                self.vf.ICmdCaller.commands.value[k] = None
        for mol, index in self.sequenceIndex.items():
            if not mol in  self.alignmentMols:
                self.hideSequence(mol)
        for mol, sequence, resSet in (refMol, moveMol):
            labels, numbers, objects = buildSeqAlignmentLabels(sequence, resSet)
            self.drawSequenceforMol(mol, labels, numbers, objects)
            # remove chain names from molNamesCanvas
            for chain in mol.chains:
                cid = chain.id
                if cid==' ': cid='?'        
                item = self.molNamesCanvas.find_withtag("%s&&%s"%(mol.molTag, cid))
                if len(item):
                    self.molNamesCanvas.itemconfig(item, state='hidden')


    def removeAlignment(self):
        if not self.selectForSuperimpose or len(self.alignmentMols) == 0: return
        self.selectForSuperimpose = False
        # clear previous selection:
        if len(self.selected):
            self.vf.deselect(self.vf.selection)
        for mol, index in self.sequenceIndex.items():
            if mol in self.alignmentMols:
                labl, numl, obj = buildLabels(mol, self.ignoreChains[mol],
                                              self.userGaps[mol])
                self.drawSequenceforMol(mol, labl, numl, obj)
            else:
                self.showSequence(mol)
                # show chain ids
                for chain in mol.chains:
                    cid = chain.id
                    if cid==' ': cid='?'        
                    item = self.molNamesCanvas.find_withtag("%s&&%s"%(mol.molTag, cid))
                    if len(item):
                        self.molNamesCanvas.itemconfig(item, state='normal')
        for k, v in self.iCmd.items():
            self.vf.ICmdCaller.commands.value[k] = v
        self.iCmd = {}
        self.alignmentMols = []

    def selectedAlignmentPairs(self, refMolName, mvMolName):
        assert refMolName == self.alignmentMols[0].name
        assert mvMolName == self.alignmentMols[1].name
        set1 = []
        set2 = []
        selMols, selRes = self.vf.getNodesByMolecule(self.selection, Residue)
        if len(selMols) != 2 : return set1, set2
        for mol, rset in zip (selMols, selRes):
            if mol.name == refMolName:
                refMol = mol
                refSeq = refMol.sequenceLabels[2]
                refSet = rset
            elif mol.name == mvMolName:
                mvMol = mol
                mvSeq = mvMol.sequenceLabels[2]
                mvSet = rset
            else:
                print "mol names mismatch (%s, %s), %s" % (refMolName, mvMolName, mol.name)
                return set1, set2
        refDict = dict(zip(refSeq, range(len(refSeq))))
        for res in refSet:
            ind = refDict[res]
            if mvSeq[ind]:
                set1.append(res)
                set2.append(mvSeq[ind])
        return ResidueSet(set1), ResidueSet(set2)


    def removeMolecule(self, molecule, resize = True):
        if not self.sequenceIndex.has_key(molecule):
            return # the molecule is not there
        # remove the molecule and decrement the number of sequences
        if not self.isVisible.has_key(molecule):
            return
        bcan = self.bcan
        canvas = self.canvas
        scids = self.scids
        molname = molecule.molTag
        canvas.delete(molname)
        for tid in canvas.find_withtag(molname):
            if self.orientId.has_key(tid):
                bid = self.orientId.pop(key)
                self.bcan.delete(bid)
            if self.scids.has_key(tid):
                self.scids.pop(tid)
            if self.tkIdToObj.has_key(tid):
                res = self.tkIdToObj.pop(tid)
                self.resToTkid.pop(res)
        self.molNamesCanvas.delete(molname)
        sind = self.sequenceIndex.pop(molecule)
        self.nbSequences -= 1
        self.sequenceOrder.remove(molecule)
        self.ignoreChains.pop(molecule)
        self.isVisible.pop(molecule)
        self.nbVisibleSequences = max(0, self.nbVisibleSequences-1)
        self.seqLength.pop(molecule)
        if resize:
            if self.nbSequences:
                for n in range(sind-1 , self.nbSequences):
                    mol = self.sequenceOrder[n]
                    self.moveUp(mol)
                    self.sequenceIndex[mol] = n+1
            self.resizeCanvases()


    def postResidueMenu(self, res, lab, event=None):
        """right-click on residue letter posts menu with
        'Show in 3D Viewer' and 'Set rotation center' commands
        """
        #print "postResidue menu", res.name, lab
        canvas = self.canvas
        canvas.focus_set()
        menu = Tkinter.Menu(tearoff=False)
        cb1 = CallbackFunction(self.vf.focusCamera, res)
        menu.add_command(label='Show in 3D Viewer',
                             command=cb1)
        cb2 = CallbackFunction(self.setRotationCenter, res, 2, res.name)
        menu.add_command(label='Set rotation center',
                             command=cb2)
        menu.post(event.x_root, event.y_root)
        self.resMenu = menu
        canvas.bind('<FocusOut>', self.cancelResMenu)


    ## def focusCamera(self, res, molecule, event=None):
    ##     # this copied (and modified) from dashboard.py
    ##     sca = 2
    ##     name = res.name
    ##     import numpy
    ##     #coords = numpy.array(res.findType(Atom).coords)
    ##     #print "focusCamera: coords1", coords
    ##     coords = numpy.array(self.vf.getTransformedCoords(molecule, res.findType(Atom).coords))
    ##     #print "focusCamera: coords2", coords
    ##     self.vf.dashboard.tree.root.focusCamera_(coords, sca, name)

    def cancelResMenu(self, event=None):
        self.resMenu.unpost()


    def setRotationCenter(self, res):
        vf = self.vf
        if vf:
            obj = res
            vf.centerOnNodes(obj.setClass([obj]))


    def configure(self, ignoreChains={}, userGaps={}):
        stateDict = {}
        if len(ignoreChains):
            for mol, chains in ignoreChains.items():
                if not stateDict.has_key(mol):
                    stateDict[mol] = {"ignoreChains": chains}
                else:
                    stateDict[mol]["ignoreChains"] = chains

        if len(userGaps):
            for mol, gaps in userGaps.items():
                if not stateDict.has_key(mol):
                    stateDict[mol] = {"userGaps":gaps}
                else:
                    stateDict[mol]["userGaps"] = gaps
        if len(stateDict):
            for mol, kw in stateDict.items():
                ic = kw.get("ignoreChains", [])
                ug = kw.get("userGaps", {})
                if len(ic) or len(ug):
                    visible = self.isVisible[mol]
                    if not visible:
                        self.showSequence(mol)
                        
                    labl, numl, obj = buildLabels(mol , ignoreChains=ic, userGaps=ug)
                    self.canvas.delete(mol.molTag)
                    sel = []
                    for res in self.selected.keys():
                        if res.top == mol:
                            sel.append(res)
                    if len(sel):
                        for tid in self.canvas.find_withtag(mol.molTag):
                            b = sv.orientId.get(tid, None)
                            if b: 
                                bcan.itemconfig(b, state='hidden')
                                bcan.dtag(b, 'selected')
                    # rebuild Tk items
                    mol.sequenceLabels = (labl, numl, obj)
                    molInd = self.ranksOfVisibleMolecules()
                    posy = molInd[mol]*self.rowScale*self.characterHeight
                    self.addMolecule(mol, posy=posy)
                    if len(ug):
                        self.userGaps[mol] = ug
                    if len(ic):
                        self.ignoreChains[mol] = []
                        for chain in ic:
                            self.showHideChain(chain, None)
                    #redo selection
                    if len(sel):
                        items = []
                        for res in sel:
                            items.append(self.resToTkid[res])
                        self.selectItems(items)
                    if not visible:
                        self.hideSequence(mol)
                        



if __name__=='__main__':
    from time import time
    t0 = time()
    from MolKit import Read
    mol1 = Read('../dev25/1crn.pdb')[0]
    #mol = Read('../dev25/1jff.pdb')[0]
    mol2 = Read('../dev25/1jff.pdb')[0]
    
    import Tkinter
    root = Tkinter.Tk()
    sv = SeqViewGUI(root)
    labels1 = buildLabels(mol1)
    sv.draw(labels1)
    #labels2 = buildLabels(mol2)
    #sv.draw(labels2)

    print time()-t0
