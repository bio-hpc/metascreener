###########################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2012
#
#############################################################################

#
# $Header: /opt/cvs/python/packages/share1.5/Pmv/pairEditor.py,v 1.4 2012/12/12 23:07:16 annao Exp $
# 
# $Id: pairEditor.py,v 1.4 2012/12/12 23:07:16 annao Exp $
#
import Tkinter, Pmw, numpy
from math import sqrt

class PairEditor:
    """
    create an GUI with a Viewer and 2 cameras to display 2 molecules as lines
    and labels and allowing users to pick atoms to create a list of atoms pairs
    """

    def __init__(self, mol1, mol2, master=None, onClose=None):
        """
        the molecules are Pmv moelcule that have all atoms displayed as lines
        and are colored by atom types
        """
        self.mol1 = mol1
        self.mol2 = mol2
        self.master = None
        self.ownsMaster = False

        self.state = 'New Pair' # used by handlePick to decide what to do
        self.nbPairs = 0        # number of defined pairs
        self.pairs = []         # pairs of atoms
        self.saveAtomNames1 = [] # used to restore atom names
        self.saveAtomNames2 = [] #used to restore atom names

        self.callback = None
        
        if onClose:
            assert callable(onClose)
        self.onClose = onClose
        
        self.createGUI(master)

        #get molecule lines geometry info
        lineGeom = mol1.geomContainer.geoms['bonded']
        v1 = lineGeom.getVertices()
        center1, rad1 = self.computeMolBBSphere(v1)
        self.mol1V = v1-center1
        self.mol1F = lineGeom.getFaces()
        self.mol1C = lineGeom.materials[1028].prop[1].copy()

        lineGeom = mol2.geomContainer.geoms['bonded']
        v2 = lineGeom.getVertices()
        center2, rad2 = self.computeMolBBSphere(v2)
        self.mol2V = v2-center2
        self.mol2F = lineGeom.getFaces()
        self.mol2C = lineGeom.materials[1028].prop[1].copy()

        # setup picking to identify atoms
        self.atoms1FromIndex = mol1.allAtoms
        self.atoms2FromIndex = mol2.allAtoms

        from DejaVu.IndexedPolylines import IndexedPolylines
        self.lines1 = IndexedPolylines(
            'mol1', vertices=self.mol1V, faces=self.mol1F,
            materials=self.mol1C, inheritMaterial=False)
        self.vi.AddObject(self.lines1)
        self.lines1.hiddenInCamera[self.vi.cameras[1]] = True

        self.lines2 = IndexedPolylines(
            'mol2', vertices=self.mol2V, faces=self.mol2F,
            materials=self.mol2C, inheritMaterial=False)
        self.vi.AddObject(self.lines2)
        self.lines2.hiddenInCamera[self.vi.cameras[0]] = True

        # add labels
        from DejaVu.glfLabels import GlfLabels

        colors = ([0,1,1],)*len(v1)
        self.atomNames1 = GlfLabels(
            name='AtomNames1', vertices=self.mol1V, labels=mol1.allAtoms.name,
            font='arial1.glf', fontStyle='solid3d', fontScales=(.3, .3, .3),
            inheritMaterial=0, materials=colors, billboard=1, pickable=False)
        self.vi.AddObject(self.atomNames1)
        self.atomNames1.hiddenInCamera[self.vi.cameras[1]] = True

        colors = ([1,1,0],)*len(v2)
        self.atomNames2 = GlfLabels(
            name='AtomNames2', vertices=self.mol2V, labels=mol2.allAtoms.name,
            font='arial1.glf', fontStyle='solid3d', fontScales=(.3, .3, .3),
            inheritMaterial=0, materials=colors, billboard=1, pickable=False)
        self.atomNames2.hiddenInCamera[self.vi.cameras[0]] = True
        self.vi.AddObject(self.atomNames2)


    def handlePick(self, pick):
        if pick.mode=='drag select': return # only accept picks

        object, items = pick.hits.items()[0]
        atNum = items[0][0]
        atom1 = atom2 = None

        if object==self.lines1: #picked atom in first molecule
            atom1 = self.atoms1FromIndex[atNum]
            if self.isInPairs(atom1): return
        elif object==self.lines2: #picked atom in second molecule
            atom2 = self.atoms2FromIndex[atNum]
            if self.isInPairs(atom2, 1): return
        #print "state:", self.state, atNum
        if self.state=='New Pair':
            if atom1 is not None:
                self.pairs.append( [atom1, None] )
                self.state = 'Got First Atom'
                self.pairsBox.insert('end', '[%d] %s - '%(self.nbPairs+1, atom1.name))
                lab = self.atomNames1.labels
                self.saveAtomNames1.append((atNum,lab[atNum]))
                lab[atNum] = '[%d]'%(self.nbPairs+1)
                self.atomNames1.materials[1028].prop[1][atNum][:3] = [1,0,0]
                self.atomNames1.Set(labels=lab)
            elif atom2 is not None:
                self.pairs.append( [None, atom2] )
                self.state = 'Got Second Atom'
                self.pairsBox.insert('end', '[%d] - %s'%(self.nbPairs+1, atom2.name))
                lab = self.atomNames2.labels
                self.saveAtomNames2.append((atNum,lab[atNum]))
                lab[atNum] = '[%d]'%(self.nbPairs+1)
                self.atomNames2.materials[1028].prop[1][atNum][:3] = [1,0,0]
                self.atomNames2.Set(labels=lab)

        elif self.state=='Got First Atom':
            if atom1 is not None: # overwrite first atom
                self.pairs[-1][0] = atom1
                self.pairsBox.delete('end')
                self.pairsBox.insert('end', '[%d] %s - '%(self.nbPairs+1, atom1.name))
                lab = self.atomNames1.labels
                oldatNum, label = self.saveAtomNames1.pop()
                self.saveAtomNames1.append((atNum,lab[atNum]))
                lab[atNum] = '[%d]'%(self.nbPairs+1)
                lab[oldatNum] = label
                self.atomNames1.materials[1028].prop[1][oldatNum][:3] = [0,1,1]
                self.atomNames1.materials[1028].prop[1][atNum][:3] = [1,0,0]

            elif atom2 is not None: # create pair
                self.pairs[-1][1] = atom2
                atom1 = self.pairs[-1][0]            
                self.pairsBox.delete('end')
                self.pairsBox.insert('end', '[%d] %s - %s'%(self.nbPairs+1, atom1.name,
                                                      atom2.name))
                lab = self.atomNames2.labels
                self.saveAtomNames2.append((atNum,lab[atNum]))
                lab[atNum] = '[%d]'%(self.nbPairs+1)
                self.atomNames2.materials[1028].prop[1][atNum][:3] = [1,0,0]
                self.state='New Pair'
                self.nbPairs += 1
                

        elif self.state=='Got Second Atom':
            if atom1 is not None: # create pair
                self.pairs[-1][0] = atom1
                atom2 = self.pairs[-1][1]
                self.pairsBox.delete('end')
                self.pairsBox.insert('end', '[%d] %s - %s'%(self.nbPairs+1, atom1.name,
                                                      atom2.name))
                lab = self.atomNames1.labels
                self.saveAtomNames1.append((atNum,lab[atNum]))
                self.atomNames1.materials[1028].prop[1][atNum][:3] = [1,0,0]
                lab[atNum] = '[%d]'%(self.nbPairs+1)
                self.atomNames1.Set(labels=lab)
                self.nbPairs += 1
                self.state='New Pair'

            elif atom2 is not None:# overwrite second atom
                self.pairs[-1][1] = atom2
                self.pairsBox.delete('end')            
                self.pairsBox.insert('end', '[%d] - %s'%(self.nbPairs+1, atom2.name))
                lab = self.atomNames2.labels
                oldatNum, label = self.saveAtomNames2.pop()
                self.saveAtomNames2.append((atNum,lab[atNum]))
                lab[atNum] = '[%d]'%(self.nbPairs+1)
                lab[oldatNum] = label
                self.atomNames2.materials[1028].prop[1][oldatNum][:3] = [1,1,0]
                self.atomNames2.materials[1028].prop[1][atNum][:3] = [1,0,0]

    def isInPairs(self, atom, ind=0):
        """Returns True if the specified atom is in the self.pairs list.
        - ind - can be 0 or 1 ,is the molecule index to which the atom belongs."""
        name = atom.name
        for pair in self.pairs:
            at = pair[ind]
            if at is not None and at.name == name:
                return True
        return False


    def deletePair(self):
        """removes selected pair of atoms from the 'Atom Pairs' ScrolledListBox """
        pairNames = self.pairsBox.getcurselection()
        col1 = self.atomNames1.materials[1028].prop[1]
        col2 = self.atomNames2.materials[1028].prop[1]
        allat1 = self.mol1.allAtoms
        a1Names = allat1.name
        allat2 = self.mol2.allAtoms
        a2Names = allat2.name
        for pairName in pairNames:
            pairNum = int(pairName.split()[0][1:-1])-1
            atom1, atom2 = self.pairs.pop(pairNum)
            if self.state == 'Got First Atom':
                a1Ind = allat1.index(atom1)
                col1[a1Ind][:3] = [0,1,1]
            elif self.state == 'Got Second Atom':
                a2Ind = allat2.index(atom2)
                col2[a2Ind][:3] = [1,1,0]
            else:
                self.nbPairs -= 1
                a1Ind = allat1.index(atom1)
                col1[a1Ind][:3] = [0,1,1]
                a2Ind = allat2.index(atom2)
                col2[a2Ind][:3] = [1,1,0]
        self.state = "New Pair"

        self.pairsBox.delete(0, 'end')

        i = 1
        for a1, a2 in self.pairs:
            if a1 == None: name1 = ""
            else: name1 = a1.name
            if a2 == None: name2 = ""
            else: name2 = a2.name
            self.pairsBox.insert('end', '[%d] %s - %s'%(i, name1, name2))
            if a1 is not None:
                a1Ind = allat1.index(a1)
                a1Names[a1Ind] = '[%d]'%i
            if a2 is not None:
                a2Ind = allat2.index(a2)
                a2Names[a2Ind] = '[%d]'%i
            i += 1
        self.atomNames1.Set(labels=a1Names)
        self.atomNames2.Set(labels=a2Names)


    def clearAllPairs(self):
        """removes all pairs of atoms from the 'Atom Pairs' ScrolledListBox """
        if len(self.pairs) != 0:
            self.pairs = []
            self.pairsBox.delete(0, 'end')
            n1 = len(self.mol1.geomContainer.geoms['bonded'].getVertices())
            n2 = len(self.mol2.geomContainer.geoms['bonded'].getVertices())
            colors1 = ([0,1,1],)*n1
            colors2 = ([1,1,0],)*n2
            self.atomNames1.Set(labels=self.mol1.allAtoms.name, materials=colors1)
            self.atomNames2.Set(labels=self.mol2.allAtoms.name, materials=colors2)
            self.nbPairs = 0
            self.saveAtomNames1 = []
            self.saveAtomNames2 = []


    def pairByAtomName(self):
        self.clearAllPairs()
        atms1 = self.atoms1FromIndex
        atms2 = self.atoms2FromIndex
        natms1 = len(atms1)
        latms1 = zip(atms1, range(natms1))
        d1 = dict(zip(atms1.name, latms1))
        self.pairs = []
        lab1 = self.atomNames1.labels
        lab2 = self.atomNames2.labels
        for atNum2, at2 in enumerate(atms2):
            if d1.has_key(at2.name):
                self.nbPairs += 1
                at1, atNum1 = d1.pop(at2.name)  
                self.pairs.append([at1, at2])
                self.pairsBox.insert('end', '[%d] %s - %s'%(self.nbPairs, at1.name, at2.name))
                lab1[atNum1] = '[%d]'%(self.nbPairs)
                self.atomNames1.materials[1028].prop[1][atNum1][:3] = [1,0,0]
                lab2[atNum2] = '[%d]'%(self.nbPairs)
                self.atomNames2.materials[1028].prop[1][atNum2][:3] = [1,0,0]
        if self.nbPairs > 0:
            self.state='New Pair'
            self.atomNames1.Set(labels=lab1)
            self.atomNames2.Set(labels=lab2)


    def closeEditor(self, event=None):
        if self.ownsMaster:
            self.master.destroy()
        else:
            self.topFrame.destroy()
        if self.onClose:
            self.onClose()
        if self.callback:
            func, args = self.callback
            atset1 = []
            atset2 = []
            if self.state != 'New Pair' and len(self.pairs):
                self.pairs.pop(-1)
            if len(self.pairs):                    
                atset1, atset2 = zip(*self.pairs)
            func(atset1, atset2, *args)
            

    def forgetMainForm(self, event=None):
        if self.ownsMaster:
            self.master.destroy()
        else:
            self.topFrame.forget()


    def packMainForm(self):
        if not self.ownsMaster:
            self.topFrame.pack(expand=1, fill='both')


    def createGUI(self, master):
        if master is None:
            master = Tkinter.Tk()
            master.title('Pair Editor')
            self.ownsMaster = True
            master.protocol("WM_DELETE_WINDOW", self.closeEditor)

        self.master = master

        # create the top Frame
        self.topFrame = Tkinter.Frame(master)

        # create a horizontal paned widget
        self.paned = Pmw.PanedWidget(self.topFrame, orient='horizontal')

        ## create the left frame for scrolledlist of pairs
        self.leftFrame = self.paned.add('left')#Tkinter.Frame(paned, bg='green')
        frame1 = Tkinter.Frame(self.leftFrame)
        frame1.pack(fill='x')
        self.pairAtomsMenu = Tkinter.Menubutton(frame1, text='Pair Atoms by...',
                                                underline=0,relief='raised' )
        self.pairAtomsMenu.pack(fill='x')
        self.pairAtomsMenu.menu = Tkinter.Menu(self.pairAtomsMenu)
        self.pairAtomsMenu.menu.add_command(label="atom name", underline=0,
                                               command = self.pairByAtomName)
        self.pairAtomsMenu['menu'] = self.pairAtomsMenu.menu
        
        # create scrolled list for pairs
        self.pairsBox = Pmw.ScrolledListBox(
            self.leftFrame, labelpos='n', label_text='Atom Pairs',
            #selectioncommand=self.selectionCommand,
            #dblclickcommand=self.defCmd,
        )
        self.pairsBox.pack(expand=1, fill='both')

        # create delete pairs button
        self.deleteButton = Tkinter.Button(self.leftFrame, text='Delete Pair',
                                           command=self.deletePair)
        self.deleteButton.pack(fill='x')

        # create Delete All Pairs button
        self.deleateAllButton = Tkinter.Button(self.leftFrame, text='Delete All Pairs',
                                           command=self.clearAllPairs)
        self.deleateAllButton.pack(fill='x')
        
        ## create the right frame for 3D Viewer
        self.rightFrame = self.paned.add('right')

        # create 3D Viewer
        from DejaVu import Viewer
        self.lviewerFrame = Tkinter.Frame(self.rightFrame)
        self.vi = Viewer(self.lviewerFrame, showViewerGUI=0, cnf={'width': 300, 'height': 300})
        vi = self.vi
        vi.TransformRootOnly(1)
        #vi.GUI.root.withdraw() # hide ViewerGUI
        self.rviewerFrame = Tkinter.Frame(self.rightFrame)
        vi.AddCamera(self.rviewerFrame, cnf={'width': 300, 'height': 300})
        vi.cameras[0].Set(color=(1,1,1))
        vi.cameras[1].Set(color=(1,1,1))

        # change callback for scaling to scale both cameras together
        def scaleAllCameras(event):
            curcam = vi.currentCamera
            for c in vi.cameras:
                vi.currentCamera = c
                Viewer.scaleCurrentCameraMouseWheel(vi, event)
            vi.currentCamera = curcam

        for c in vi.cameras:
            c.eventManager.RemoveCallback("<Button-4>",
                                          vi.scaleCurrentCameraMouseWheel)
            c.eventManager.RemoveCallback("<Button-5>",
                                          vi.scaleCurrentCameraMouseWheel)
            c.eventManager.AddCallback("<Button-4>", scaleAllCameras)
            c.eventManager.AddCallback("<Button-5>", scaleAllCameras)

        vi.scaleCurrentCameraMouseWheel = scaleAllCameras

        # replace default callback for picking
        vi.SetPickingCallback(self.handlePick)

        # create close button
        self.closeButton = Tkinter.Button(self.topFrame, text='Close',
                                          command=self.closeEditor)

        # pack frames
        self.closeButton.pack(side='bottom', fill='x')
        self.leftFrame.pack(side='left', fill='y')
        self.rightFrame.pack(expand=1, side='left', fill='both')
        self.lviewerFrame.pack(expand=1, side='left', fill='both')
        self.rviewerFrame.pack(expand=1, side='left', fill='both')
        self.paned.pack(fill='both', expand=1)
        self.topFrame.pack(expand=1, fill='both')


    def computeMolBBSphere(self, vertices):
        # compute bounding sphere
        center = numpy.sum(vertices, 0)/len(vertices)
        delta = vertices-center
        dist2 = numpy.sum(delta*delta, 1)
        # max distance from center to atom 
        radius = sqrt(max(dist2))
        return center, radius+3


if __name__=="__main__":
    previousUser = self.GUI.mainAreaUser
    if previousUser:
        previousUser.forgetMainForm()
        if hasattr(previousUser, 'packMainForm'):
            onClose = previousUser.packMainForm
        else:
            onClose = None

    from Pmv.pairEditor import PairEditor
    master = self.GUI.mainAreaMaster
    pe = PairEditor(self.Mols[0], self.Mols[1], master, onClose=onClose)

#self.GUI.mainNoteBook.selectpage('Manual Pairing')
## from mglutil.util.callback import CallbackFunction

## cb = CallbackFunction(self.GUI.mainNoteBook.selectpage, 'Manual Pairing')
## import Tkinter
## button = Tkinter.Radiobutton(
##     self.GUI.mainButtonBarMaster,
##     command=cb,
##     var=self.GUI.mainButtonBarTabVar,
##     value='Manual Pairing', indicatoron=False,
##     text='Manual Pairing', font=('Helvetica', '', 10), padx=3, pady=0)
## button.pack(side='left', anchor='w')
