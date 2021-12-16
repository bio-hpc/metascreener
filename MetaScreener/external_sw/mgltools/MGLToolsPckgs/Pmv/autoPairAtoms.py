import numpy
import TkTreectrl
import Tkinter, Pmw
from MolKit.molecule import Atom, AtomSet, Molecule, MoleculeSet
import weakref
from mglutil.math.rigidFit import RigidfitBodyAligner
from mglutil.math.rmsd import RMSDCalculator
from mglutil.util.callback import CallbackFunction
from MolKit.PDBresidueNames import RNAnames, AAnames, DNAnames, ionNames

from Pmv.dashboard import SelectionWithButtons, SetWithButtons
from MolKit.protein import Residue, ResidueSet
from Pmv.residuePairsSelector import ResSelector
from Pmv.pairEditor import PairEditor

allResidueNames = {}
allResidueNames.update(RNAnames)
allResidueNames.update(AAnames)
allResidueNames.update(DNAnames)

def matchAtomSets(at1, at2, options):
    # build hash table for at1
    at1Dict = {}
    l1 = []
    l2 = []
    formatStr = "%s_" * (len(options)-1) + "%s"
    for a in at1:
        res = a.parent
        names = [{'AtomName':a.name, 'ResName':res.name, 'ChainID':res.parent.id, 'ResType':res.type}.get(n) for n in options]
        key = formatStr % tuple(names)
        if at1Dict.has_key(key):
            #print "matchAtomSets, options:", options, "at1Dict.haskey:", key , "returning []"
            return [l1, l2]
        at1Dict[key] = a

    # loop over atom set 2 and find match
    #pairs = []
    for a in at2:
        res = a.parent
        names = [{'AtomName':a.name, 'ResName':res.name, 'ChainID':res.parent.id, 'ResType':res.type}.get(n) for n in options]
        key = formatStr % tuple(names)
        if at1Dict.has_key(key):
            pa = at1Dict[key]
            if pa is not None:
                #print 'MATCH', i, a, pa, key
                #pairs.append( (pa,a) )
                l1.append(pa)
                l2.append(a)
                at1Dict[key] = None
    return [l1, l2]


def matchResSetsByAtomName(rset1, rset2):
    # return matching atoms of the two residue sets
    # (that have been aligned by the sequence alignment algorithm from biopython)
    
    #t1 = time()
    if len(rset1.atoms) == len(rset2.atoms):
        # assume the resudue sets match
        return rset1.atoms, rset2.atoms
    atset1 = AtomSet()
    atset2 = AtomSet()
    for res1,res2 in zip(rset1, rset2):
        atms1 = res1.atoms
        atms2 = res2.atoms
        # if atomsets of the two residues have the same length- assume they match 
        if len(atms1) == len(atms2):
            atset1.extend(atms1)
            atset2.extend(atms2)
        else:
            #compare atom names of two residues:
            d1 = dict(zip(atms1.name, atms1))
            for at in atms2:
                if d1.has_key(at.name):
                    atset1.append(d1[at.name])
                    atset2.append(at)
    #print "time:", time()-t1
    return atset1, atset2


def isDNA(allres):
    # all atoms in residues with name in the DNA names list
    res = [a for a in allres if DNAnames.has_key(a.type.strip())]
    return ResidueSet(res)


def isRNA(allres):
    # all atoms in residues with name in the RNA names list
    res = [a for a in allres if RNAnames.has_key(a.type.strip())]
    return ResidueSet(res)


def isProtein(allres):
    # all atoms in residues with name in the amino acids names list
    res = [a for a in allres if AAnames.has_key(a.type.strip())]
    return ResidueSet(res)


def isLigand(allres):
    res = [a for a in allres if not allResidueNames.has_key(a.type.strip())]
    return ResidueSet(res)

def isWater(allres):
    res = [a for a in allres if a.type=='WAT' or a.type=='HOH']
    return ResidueSet(res)

def isIons(allres):
    res = [a for a in allres if ionNames.has_key(a.type.strip())]
    return ResidueSet(res)



class SuperimposeGUI:

    def __init__(self, node, master=None):
        self.node = node
        self.vf =  node.tree().vf
        if master is None:
            master = self.vf.dashboard.master3
        self.master = master
        self.rmsdMols = {}
        self.rmsdPairs = {}
        self.typefunc = None
        self.object =  node.object
        # options for the matcher combobox
        #self.matchPairsOptions =  ['AtomName', 'AtomName_ResName', 'AtomName_ResName_ChainID', 'AtomName_ResType_ChainID', "SequenceAlignment", "ManualAlignment"]
        self.matchPairsOptions =  ['AtomName', 'AtomName_ResName', 'AtomName_ResName_ChainID', "SequenceAlignment", "ManualAlignment"]
        if isinstance(self.node , SetWithButtons):
            self.refAtmSet = self.object._set
            self.refResSet = self.refAtmSet.findType(Residue).uniq()
            self.refMolName = self.refAtmSet.top.uniq()[0].name
        elif isinstance(self.node , SelectionWithButtons):
            self.refAtmSet = self.vf.getSelection()
            self.refResSet = self.refAtmSet.findType(Residue).uniq()
            self.refMolName = self.refAtmSet.top.uniq()[0].name
        else:
            self.refAtmSet =  self.object.allAtoms
            self.refResSet = self.object.chains.residues
            self.refMolName = self.object.name
        self.molSequences = {}
        paramsNB = self.vf.dashboard.paramsNB
        self.paramsNBconfig = {'rendtab':  paramsNB.tab('Rendering'),
                               'tabName': 'Rendering',
                               'raisecommand': paramsNB.configure()['raisecommand'][-1]}
        paramsNB.configure(raisecommand=self.selectSeqalignParams_cb)

        self.movewithMols = {}
        self.atpairedbox = None
        self.showForm()
        # the following will be widgets for selecting pairs of residues or atoms
        self.residueChoser = None
        self.atomPairEditor = None
        
        self.applyButtonName = self.vf.dashboard.applyButton.configure("text")[-1]
        self.vf.dashboard.applyButton.configure(text = "Superimpose", state = Tkinter.DISABLED)
        self.vf.dashboard.expandParams(self.form)
        self.vf.dashboard.columnShowingForm = self
        self.vf.dashboard.applyButton.bind('<1>', self.Apply_cb)
        self.vf.dashboard.closeButton.bind('<1>', self.Close_cb)

        
    def Close_cb(self, event=None):
        #for w in self.widgets: w.destroy()
        self.form.destroy()
        self.form2.destroy()
        self.vf.dashboard.applyButton.unbind('<1>')
        self.vf.dashboard.applyButton.configure(text = self.applyButtonName, state = Tkinter.NORMAL)
        self.vf.dashboard.closeButton.unbind('<1>')
        self.vf.dashboard.collapseParams()
        self.vf.dashboard.columnShowingForm = None
        rendtab = self.paramsNBconfig['rendtab']
        name = self.paramsNBconfig['tabName']
        command = self.paramsNBconfig['raisecommand']
        rendtab.configure(text=name,  state="normal")
        self.vf.dashboard.paramsNB.configure(raisecommand=command)
        self.seqalParams.topFrame.destroy()
        self.vf.dashboard.geomAppearanceWidget.groupw.pack(side='top', anchor='nw', padx=2, pady=2)
        #self.moveAlongButton.destroy()
        if hasattr(self.vf, 'sequenceViewer'):
            sqv = self.vf.sequenceViewer.seqViewer
            if sqv.selectForSuperimpose: sqv.removeAlignment()
        
        
    def Apply_cb(self, event=None):
        ## find all molecules with checked checkboxes and
        ## fit them
        #print "Apply_cb"
        from MolKit.molecule import AtomSet

        lbox = self.RMSDmlb.listbox
        length = len(lbox.get(0, 'end'))
        nchecked = 0 
        for i, entry in enumerate(lbox.get(0, 'end')):
            state = lbox.itemstate_forcolumn(i+1, lbox.column(0))
            #print i, state
            if state is not None:
                nchecked = nchecked + 1
                # get name of reference molecule from table
                molname = entry[1]
                mol = self.rmsdMols[molname]
                        
                if not self.rmsdPairs.has_key(molname): continue
                if hasattr(self.vf, "sequenceViewer"):
                    sv = self.vf.sequenceViewer.seqViewer
                    if self.matcherbox.get() == "SequenceAlignment" and sv.selectForSuperimpose:
                        # find pairs selected in the sequence Viewer
                        set1, set2 = sv.selectedAlignmentPairs(self.refMolName, molname)
                        if len(set1): self.rmsdPairs[molname]= [set1, set2]
                set1, set2 = self.rmsdPairs[molname]    
                #print "in Apply_cb:", "set1:", len(set1), "set2:", len(set2)
                if not len(set1): continue
                # get corrdiantes from pairs for superimpose
                atomtype = None
                if self.atpairedbox and self.atpairedbox.winfo_ismapped():
                    atomtype = self.atpairedbox.get()
                refAtoms, mobAtoms = self.getAtomTypePairs(molname, atomtype)
                refcoords = refAtoms.coords
                mobcoords = mobAtoms.coords
                refmol = refAtoms.top.uniq()[0]
                trefcoords = self.vf.getTransformedCoords(refmol, refcoords)
                #tmobcoords = self.vf.getTransformedCoords(mol, mobcoords)
                #tmobcoords = mobcoords
                #print "refmol:", refmol.name
                #print "refcoords:" , len(refcoords)
                #print trefcoords
                #print "mob mol:", mol.name
                #print "tmobcoords", len(tmobcoords)
                #print tmobcoords

                # calcualte superimpose Xform
                rigidfitAligner = RigidfitBodyAligner()
                rigidfitAligner.setRefCoords(trefcoords)                
                res = rigidfitAligner.rigidFit(mobcoords)
                #print "res:", res
                if res: continue
                mGeom = mobAtoms[0].top.geomContainer.masterGeom  
                rotMat =  numpy.identity(4).astype('d')
                rotMat[:3,:3] = rigidfitAligner.rotationMatrix               
                transMat = numpy.array(rigidfitAligner.translationMatrix)
                rotMat[3,:3] = transMat
                      
                #mGeom.SetRotation(numpy.reshape(rotMat, (16,)).astype('f'))
                mGeom.SetTransformation(numpy.reshape(rotMat, (16,)).astype('f'))
                #update in the listbox :
                #print "mgeom:", mGeom, "rotMatrix:"
                #print rotMat
                #print "------------------"
                #print mGeom.GetMatrix(mGeom)
                tmobCoords = self.vf.getTransformedCoords(mol, mobcoords)
                rmsd = self.computeRMSD(trefcoords, tmobCoords)
                #print "rmsd:", rmsd
                #rmsd = rigidfitAligner.rmsdAfterSuperimposition(tmobcoords)
                
                self.updatePairsRMSDTable(i+1, rmsd, len(trefcoords))
                #lbox.itemstate_forcolumn(i+1, lbox.column(0), '~Checked')
        if nchecked == 1: 
            movemols = self.movewithMols.get(molname, None)
            if movemols is not None:
                for mmol in movemols:
                    mg = mmol.geomContainer.masterGeom
                    #mg.SetRotation(numpy.reshape(rotMat, (16,)).astype('f'))
                    mg.SetTransformation(numpy.reshape(rotMat, (16,)).astype('f'))
        
        self.vf.GUI.VIEWER.Redraw()
        # the above code can "Uncheck" some of the entries in the table,
        # find if we still have "checked" ones
        if not len(self.findCheckedInTable()): 
            self.vf.dashboard.applyButton.configure(state=Tkinter.DISABLED)
            self.moveWithButton.configure(state=Tkinter.DISABLED)

        
    def getAtomSets(self, allmols):
        sets = []
        refatset= self.refAtmSet
        if isinstance(self.node , SetWithButtons) or isinstance(self.node , SelectionWithButtons):
            refmol = refatset.top.uniq()[0]
        else :
            refmol = self.object
        for mol in allmols:
            if mol == refmol: continue
            sets.append((mol, mol.allAtoms))
        return refatset, sets
            

    def showForm(self, event=None):
        # create GUI for selecting matching pairs of atoms, computing RMSD and Superimposition
        vf = self.vf
        dashboard = vf.dashboard
        vf.sGUI = self
        master = self.master

        # create the main frame in the basic tab
        self.form = form = Tkinter.Frame(master)
        
        # update the top label in Basic Panel
        name = "Reference (fixed): %s" % (self.object.name)
        dashboard.objectLabelWidget.configure(text=name)
        # rename "Rendering" tab , create sequence alignment option panel
        nbtab = self.paramsNBconfig['rendtab']
        nbtab.configure(text="Options", state="disable")
        dashboard.geomAppearanceWidget.groupw.forget()
        self.seqalParams = SequenceAlignmentParams(dashboard.geomAppearanceWidget.master, self. alignSequences_cb)
        
        # create a group for matchers
        self.optGroup = group = Pmw.Group(form, tag_text='Options')
        group.pack(side='top', anchor='nw', padx=4, pady=4)#, fill='both', expand=1)
        options = self.matchPairsOptions[:] 
        #('AtomName', 'AtomName_ResName', 'AtomName_ResName_ChainID',  "SequenceAlignment", "ManualAlignment")
        opt = options[1] #'AtomName_ResName'
        allres = []
        objres = self.refResSet

        # Find object type: Protein, DNA, RNA, Ligand
        if len(isProtein(objres)):
            opt = options[3] # "SequenceAlignment"
            allres = isProtein(self.vf.Mols.chains.residues)
            self.typefunc = isProtein
            nbtab.configure(state="normal")
            self.molSequences[self.refMolName] = self.sequenceString(objres)
        elif len(isDNA(objres)):
            opt = options[1] #'AtomName_ResName'
            allres = isDNA(self.vf.Mols.chains.residues)
            self.typefunc = isDNA
        elif len(isRNA(objres)):
            opt = options[1] #'AtomName_ResName'
            allres = isRNA(self.vf.Mols.chains.residues)
            self.typefunc = isRNA
        elif len(isLigand(objres)):
            if len(objres) == 1:
                opt = options[0] # 'AtomName'
            else:
                opt = options[1] #'AtomName_ResName'
            allres = isLigand(self.vf.Mols.chains.residues)
            self.typefunc= isLigand
            options.pop(3)

            
        # create combobox for matchmaker algorithm
        self.matcherbox = w = Pmw.ComboBox(group.interior(),
            label_text = 'matcher:', labelpos = 'w',
            selectioncommand = self.fillTable_cb,
            scrolledlist_items = options,
            #scrolledlist_height = 10,
            entryfield_entry_width = 25,
            scrolledlist_usehullsize = 1,
            scrolledlist_hull_height = 100,)
        
        w.selectitem(opt)
        w.pack(side = 'top', anchor = 'n',
          fill = 'x', padx = 4, pady = 4) # fill = 'x', expand = 1,
        if self.typefunc == isProtein:
            # Create "atoms paired" comboBox.
            # Pack it on the form if matcher option is "SequenceAlignment"  :
            atomtypes = ["C-alpha", "Backbone", "All"]
            self.atpairedbox = w = Pmw.ComboBox(group.interior(),
                 label_text = 'atoms paired:', labelpos = 'w',
                 selectioncommand = self.selectAtomPaired_cb,
                 scrolledlist_items = atomtypes, entryfield_entry_width = 25,
                 scrolledlist_usehullsize = 1, scrolledlist_hull_height = 100)
            w.selectitem(atomtypes[0])
            if  opt == "SequenceAlignment":
                w.pack(side = 'top', anchor = 'n', fill = 'x', padx = 4, pady = 4)

        # create table of system parameters
        self.frameMLB = frame1 = Tkinter.Frame(form)
        frame1.pack(expand=1, fill='both')
        mlb = self.RMSDmlb = TkTreectrl.ScrolledMultiListbox(frame1, height=200)
        mlb.pack(fill='both', expand=1)
        lbox = mlb.listbox
        lbox.config(columns=('fit', 'Molecule', '#pairs', 'RMSD', 'score'))
        lbox.state_define('Checked')
        lbox.icons = {}

        checkedIcon = lbox.icons['checkedIcon'] = \
            Tkinter.PhotoImage(master=frame1, data='R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39////8CJ4yPNgHtLxYYtNbIbJ146jZ0gzeCIuhQ53NJVNpmryZqsYDnemT3BQA7')
        unCheckedIcon = lbox.icons['unCheckedIcon'] = \
            Tkinter.PhotoImage(master=frame1, data='R0lGODlhDQANABEAACwAAAAADQANAIEAAAB/f3/f39////8CIYyPNgHtLxYYtNbIrMZTX+l9WThwZAmSppqGmADHcnRaBQA7')

        # style for check buttons
        el_image = lbox.element_create(type='image', image=(
            checkedIcon, 'Checked', unCheckedIcon, ()))
        styleCheckbox = lbox.style_create()
        lbox.style_elements(styleCheckbox, lbox.element('select'),
                            el_image, lbox.element('text'))
        lbox.style_layout(styleCheckbox, el_image, padx=3, pady=2)
        lbox.style(lbox.column(0), styleCheckbox)

        colors = ('white', '#ddeeff')
        for col in range(5):
            lbox.column_configure(lbox.column(col), itembackground=colors)
        lbox.bind('<1>', self.on_button1)
        lbox['selectbackground'] = 'white'
        lbox['selectforeground'] = 'black'
        if len(allres):
            allmols = allres.top.uniq()
            self.fillTable(opt.split("_"), allmols)
        self.form2 = form2 = Tkinter.Frame(master)
        form2.pack(side = 'bottom', expand=1, fill="both")
        self.moveWithButton = Tkinter.Button(form2, text="Move with 0 mols",
                                              command=self.moveWith_cb, state='disable')
        self.moveWithButton.pack(side='bottom', anchor='w', fill='x', expand=1)
        
        self.form.pack(expand=1, fill="both")


    def on_button1(self, event):
        # callback of the checkbuttons in the table
        lbox = self.RMSDmlb.listbox
        identify = lbox.identify(event.x, event.y)
        # identify might be None or look like:
        # ('item', '2', 'column', '0') or ('item', '3', 'column', '0', 'elem', 'pyelement3')
        item = None
        if identify:
            #print "identify", identify
            try:
                item, column, element = identify[1], identify[3], identify[5]
            except IndexError:
                # we did not hit the image, never mind
                pass
        if item == None: return
       
        if int(item)%2 == 1:
            selcolor = 'white'
        else:
            selcolor = '#ddeeff'
        matcher = self.matcherbox.get()
        molname = lbox.get(lbox.index(item=item))[0][1]
        if int(column)==0: # Compute Checkbutton was pressed
            if matcher == "SequenceAlignment":
                # check if clicked on "checked" box:
                if lbox.itemstate_forcolumn(item, column) is not None: # it is checked
                    lbox.itemstate_forcolumn(item, column, '~Checked') # uncheck it
                    lbox.update_idletasks()
                    # 'enable' all other checkboxes and remove alignment strings from sequence viewer(restore the original ones)
                    lbox['selectbackground'] = selcolor
                    colors = ('white', '#ddeeff')
                    for i, entry in enumerate(lbox.get(0, 'end')):
                        it = lbox.item(i)
                        lbox.item_enabled(it, enabled=True)
                    for col in range(5):
                        lbox.column_configure(lbox.column(col), itembackground=colors)
                    if hasattr(self.vf, 'sequenceViewer'):
                        self.vf.sequenceViewer.seqViewer.removeAlignment()
                else:
                    
                    # find if other boxes are checked:
                    if len(self.findCheckedInTable()): # there are checked boxes
                        return
                    else:
                        lbox['selectbackground'] = selcolor
                        lbox.itemstate_forcolumn(item, column, '~Checked') # check the box
                        lbox.update_idletasks()
                        #'disable' all other checkboxes and display alignment
                        colors = []
                        for i, entry in enumerate(lbox.get(0, 'end')):
                            colors = []
                            it = lbox.item(i)
                            if it==item:
                                colors.append(selcolor)
                                lbox.item_enabled(it, enabled=True)
                            else:
                                colors.append('light grey')
                                for cl in range(1, lbox.column_count()):
                                    lbox.itemelement_config(it, lbox.column(cl), lbox.element('text'), fill=('light grey',))
                                lbox.item_enabled(it, enabled=False)
                        #for col in range(5):
                        #    lbox.column_configure(lbox.column(col), itembackground=colors)
                        set1, set2 = self.alignSequences(molname, item)
            else:
                lbox['selectbackground'] = selcolor
                lbox.itemstate_forcolumn(item, column, '~Checked')
                lbox.update_idletasks()
                if lbox.itemstate_forcolumn(item, column) is not None:
                    if  matcher == "ManualAlignment":
                        if self.typefunc == isLigand:
                            previousUser = self.vf.GUI.mainAreaUser
                            if previousUser:
                                previousUser.forgetMainForm()
                                if hasattr(previousUser, 'packMainForm'):
                                    onClose = previousUser.packMainForm
                                else:
                                    onClose = None
                            master = self.vf.GUI.mainAreaMaster
                            mol1= self.object
                            mol2 = self.rmsdMols[molname]
                            self.atomPairEditor = PairEditor(mol1, mol2, master, onClose=onClose)
                            self.atomPairEditor.callback = (self.setManualAtomPairs_cb, (item,))

                        else: # "replace the list table with the "pair residues" widget  
                            #self.vf.dashboard.master4.forget() # forget param notebook
                            self.vf.dashboard.paramsNB.pack_forget()
                            self.vf.dashboard.applyButton.master.forget()

                            #create form with 3 listboxes
                            mol = self.rmsdMols[molname]
                            self.residueChooser =  ResSelector(
                                self.refResSet, mol.chains.residues,
                                self.vf.dashboard.master4)
                                #self.vf.dashboard.dashboardPanedWidget.pane('cmdParams'))
                            self.residueChooser.setCallback(self.setManualResiduePairs_cb, (item,))

        nchecked = len(self.findCheckedInTable())
        if nchecked:
            # if there are "checked" items in the table - enable the "Superimpose"
            # button
            self.vf.dashboard.applyButton.configure(state=Tkinter.NORMAL)
        else:
            self.vf.dashboard.applyButton.configure(state=Tkinter.DISABLED)
        if nchecked == 1:
            if len(self.vf.Mols)-2 < 1 :
                # there is no mols to move with --> disable the button:
                self.moveWithButton.configure(state='disable', text="Move with 0 mols")
            else:
                mmols = self.movewithMols.get(molname, [])
                self.moveWithButton.configure(state='normal', text="Move with %d mols"%len(mmols))
        else:
            self.moveWithButton.configure(state='disable', text="Move with 0 mols")

            
    def fillTable_cb(self, matcherName):
        # callback of the matcher combobox
        allres = self.typefunc(self.vf.Mols.chains.residues)
        if len(allres):
            allmolls = allres.top.uniq()
            self.fillTable(matcherName.split("_"), allmolls)
        if self.atpairedbox:
            ismapped = self.atpairedbox.winfo_ismapped()
            if matcherName.split("_")[0] == "AtomName":
                if ismapped:
                    self.atpairedbox.forget()
            else:
                if not ismapped:
                    self.atpairedbox.pack(side = 'top', anchor = 'n', fill = 'x', padx = 4, pady = 4)

        rendtab = self.paramsNBconfig['rendtab']

        if matcherName == "SequenceAlignment":
            rendtab.configure(state="normal")
        else:
            rendtab.configure(state="disable")
            if hasattr(self.vf, "sequenceViewer"):
                sv = self.vf.sequenceViewer.seqViewer
                if sv.selectForSuperimpose: sv.removeAlignment()

    def fillTable(self, options, allmols):
        # fill the Molecule - #pairs - RMSD table
        lbox = self.RMSDmlb.listbox
        lbox.delete(0, 'end')
        if options[0] == "AtomName" : # fast algorithm for atom pair matching-
                                      # find the pairs and compute RMSD
            at1, atsets = self.getAtomSets(allmols)
            for item in atsets:
                mol = item[0]
                at2 = item[1]
                name = mol.name
                #pairs = self.autoPairAtoms().matchAtomSets_Aname_Rname(at1, at2)
                set1, set2 = matchAtomSets(at1, at2, options)
                #print "AtomName:", len(set1), len(set2)
                if len(set1):
                    set1 = AtomSet(set1)
                    set2 = AtomSet(set2)
                    refmol = set1.top.uniq()[0]
                    refcoords = self.vf.getTransformedCoords(refmol, set1.coords)
                    mobcoords = self.vf.getTransformedCoords(mol, set2.coords)
                    rmsd = self.computeRMSD(refcoords, mobcoords)
                    lbox.insert( 'end', '', name, len(set1), "%.3f"%rmsd, "" )
                    lbox.itemelement_config(
                        'end', lbox.column(1), lbox.element('text'),
                        text=name, datatype=TkTreectrl.STRING, data=name)
                    self.rmsdMols[name] = mol
                    self.rmsdPairs[name] = [set1, set2]
        elif options[0] =="SequenceAlignment":
              #either "SequenceAlignment" (could be slow) or "ManualAlignment".
              # List all available for this algorithm molecules in the table- do not
              # look for pairs.
              refname = self.refMolName
              refmol = self.refAtmSet.top.uniq()[0]
              refseq, refres = self.molSequences.get(refname, (None, None))
              if not refseq:
                  refseq, refres = self.sequenceString(self.refResSet)
                  self.molSequences[refname] = (refseq, refres)
              for mol in allmols:
                  name = mol.name
                  if name == refname:
                      continue
                  molseq, molres = self.molSequences.get(name, (None, None))
                  if not molseq:
                      molseq, molres = self.sequenceString(mol.chains.residues)
                      self.molSequences[name] = (molseq, molres)
                  set1 = []
                  if refseq == molseq and len(refres.atoms) == len(molres.atoms):
                      set1, set2 = matchAtomSets(refres.atoms,  molres.atoms, ['AtomName', 'ResName', 'ChainID'])
                      if len(set1):
                          set1 = AtomSet(set1)
                          set2 = AtomSet(set2)
                          self.rmsdPairs[name] = [set1, set2]
                          if self.atpairedbox:
                              self.atpairedbox.selectitem("All")
                          refcoords = self.vf.getTransformedCoords(refmol, set1.coords)
                          mobcoords = self.vf.getTransformedCoords(mol, set2.coords)
                          rmsd = self.computeRMSD(refcoords, mobcoords)
                          lbox.insert( 'end', '', name, len(set1), "%.3f"%rmsd, "identical" )
                          lbox.itemelement_config(
                              'end', lbox.column(1), lbox.element('text'),
                              text=name, datatype=TkTreectrl.STRING, data=name)
                          
                  if not len(set1):
                      lbox.insert( 'end', '', name, "", "","" )
                      lbox.itemelement_config(
                          'end', lbox.column(1), lbox.element('text'),
                          text=name, datatype=TkTreectrl.STRING, data=name)
                  self.rmsdMols[name] = mol
                  
                  colors = ('white', '#ddeeff')
                  for col in range(5):
                      lbox.column_configure(lbox.column(col), itembackground=colors)
                  lbox['selectbackground'] = 'white'
                  lbox['selectforeground'] = 'black' 
        else:
            refname = self.refMolName
            for mol in allmols:
                name = mol.name
                if name == refname:
                    continue
                lbox.insert( 'end', '', name, "", "","" )
                lbox.itemelement_config(
                        'end', lbox.column(1), lbox.element('text'),
                        text=name, datatype=TkTreectrl.STRING, data=name)
                self.rmsdMols[name] = mol
        self.vf.dashboard.expandParams(self.master)
        # disable the "Superimpose" button:
        self.vf.dashboard.applyButton.configure(state=Tkinter.DISABLED)


    def sequenceViewerSelect_cb(self, set1, set2):
        if not len(set1):return
        sqv = self.vf.sequenceViewer.seqViewer
        refMol, mvMol = sqv.alignmentMols
        self.rmsdPairs[mvMol.name] = [set1, set2]        

        atomtype = None
        if self.atpairedbox:
            atomtype = self.atpairedbox.get()
        refAtoms, mobAtoms = self.getAtomTypePairs(mvMol.name, atomtype)
        refcoords = refAtoms.coords
        mobcoords = mobAtoms.coords
        trefcoords = self.vf.getTransformedCoords(refMol, refcoords)
        tmobcoords = self.vf.getTransformedCoords(mvMol, mobcoords)
        rmsd = self.computeRMSD(trefcoords, tmobcoords)
        lbox = self.RMSDmlb.listbox
        for i, entry in enumerate(lbox.get(0, 'end')):
            if entry[1] == mvMol.name:
                self.updatePairsRMSDTable(i+1, rmsd, len(refcoords))
                break

    def selectAtomPaired_cb(self, atomtype):
        # callback of the "atoms paired" comboBox.
        #print "selectAtomPaired_cb, atomtype:", atomtype
        # go over all mols in the table and compute RMSD for "checked" lines.
        lbox = self.RMSDmlb.listbox
        for i, entry in enumerate(lbox.get(0, 'end')):
            state = lbox.itemstate_forcolumn(i+1, lbox.column(0))
            if state != None: # the checkbutton is checked
                molname = entry[1]
                if self.rmsdPairs.has_key(molname):
                    mol = self.rmsdMols[molname]
                    set1, set2 = self.rmsdPairs[molname]
                    if len(set1):
                        refAtoms, mobAtoms = self.getAtomTypePairs(molname, atomtype)
                        refmol = refAtoms.top.uniq()[0]
                        refcoords = refAtoms.coords
                        mobcoords = mobAtoms.coords
                        trefcoords = self.vf.getTransformedCoords(refmol, refcoords) 
                        tmobcoords = self.vf.getTransformedCoords(mol, mobcoords)
                        rmsd = self.computeRMSD(trefcoords, tmobcoords)
                        # update rmsd value in the table
                        self.updatePairsRMSDTable(i+1, rmsd, len(refcoords))


    def alignSequences_cb(self, event=None):
        lbox = self.RMSDmlb.listbox
        for i, entry in enumerate(lbox.get(0, 'end')):
            state = lbox.itemstate_forcolumn(i+1, lbox.column(0))
            if state != None: # the checkbutton is checked
               molname = entry[1]
               self.alignSequences(molname, i+1)
               
        self.vf.dashboard.paramsNB.selectpage("Basic") 
               

    def alignSequences(self, molname, item):
        # use Biopython pairwise module to align selected molecule and
        # the reference structure
        #print "alignSequences"

        selMols, selRes = self.vf.getNodesByMolecule(self.vf.selection, Residue)
        # get sequence string for the reference mol (check if the molecule has a selection, take only selected residues)
        if self.refMolName in selMols.name:
            ind = selMols.name.index(self.refMolName)
            seq1, resList1 = self.sequenceString(selRes[ind])
        else:
            seq1, resList1 = self.molSequences.get(self.refMolName, (None, None))
            if not seq1:
                seq1, resList1 = self.sequenceString(self.refResSet)
                self.molSequences[self.refMolName] = (seq1, resList1)
        # get sequence string for the selected in the table mol
        # (check if the molecule has a selection, take only selected residues)
        if molname in  selMols.name:
            ind = selMols.name.index(molname)
            seq2, resList2 = self.sequenceString(selRes[ind])
        else:
            seq2, resList2 = self.molSequences.get(molname, (None, None))
            if not seq2:
                seq2, resList2 = self.sequenceString(self.rmsdMols[molname].chains.residues)
                self.molSequences[molname] = seq2
        #print '###############'
        #print seq1
        #print seq2
        #print resList1.name
        #print resList2.name    
        useBio = True
        if seq1 == seq2 and len(resList1.atoms) == len(resList2.atoms):
            set1, set2 = matchAtomSets(resList1.atoms,  resList2.atoms,
                                       ['AtomName', 'ResName', 'ChainID'])
            if len(set1):
                set1 = AtomSet(set1)
                set2 = AtomSet(set2)
                useBio = False
                score = "identical"
        if useBio:
            from Bio.SubsMat import MatrixInfo as matlist
            from Bio import pairwise2
            matrix, gap_open, gap_extend = self.seqalParams.getParams()
            if gap_open > 0: gap_open = -gap_open
            if gap_extend > 0: gap_extend = -gap_extend
            #print "gap_open:",  gap_open,  "gap_extend:", gap_extend, "matrix:", matrix
            matrix = getattr(matlist, matrix)
            #matrix = matlist.blosum62
            #gap_open = -10
            #gap_extend = -0.5
            alns = pairwise2.align.globalds(seq1, seq2, matrix, gap_open, gap_extend)
            score = alns[0][2]
            set1, set2 = self.getResPairsFromAlignment(alns[0], resList1, resList2)
            #print len(set1), len(set2), score
        self.rmsdPairs[molname] = [set1, set2]
        atomtype = None
        if self.atpairedbox:
            atomtype = self.atpairedbox.get()
            refAtoms, mobAtoms = self.getAtomTypePairs(molname, atomtype)
        mol = self.rmsdMols[molname]
        refmol = refAtoms.top.uniq()[0]
        refcoords = self.vf.getTransformedCoords(refmol, refAtoms.coords)
        mobcoords = self.vf.getTransformedCoords(mol, mobAtoms.coords)
        rmsd = self.computeRMSD(refcoords, mobcoords)
        self.updatePairsRMSDTable(item, rmsd, len(refAtoms), score)
        
        if useBio:
            if not hasattr(self.vf, 'sequenceViewer'):
                self.vf.browseCommands('seqViewerCommands', package='Pmv',
                                       topCommand=0)
            svcmd = self.vf.sequenceViewer
            if not svcmd.viewerVisible: svcmd.showHideGUI(visible=True)
            sv = svcmd.seqViewer
            sv.showAlignment([refmol, alns[0][0], resList1], [mol, alns[0][1], resList2])
            sv.selectForSuperimpose_cb = self.sequenceViewerSelect_cb
        return set1, set2


    def sequenceString(self, frag):
        # create residue sequence string 
        residues = frag.findType(Residue)
        #seqFmt = "%c"*len(residues)
        #seq = seqFmt%tuple([AAnames[x] for x in residues.type])
        seq = ""
        #for restype in residues.type:
        rset = ResidueSet()
        for res in residues:
            restype = res.type
            s = allResidueNames.get(restype.strip(), None)
            if s is None:
                print "sequenceString, residue not in seq.string:", restype, res.name  
                continue
            if s != '?':
                seq += s
                rset.append(res)
        #return seq, residues
        return seq, rset


    def getResPairsFromAlignment(self, aln, resList1, resList2):
        # return two aligned residue sets
        ind1 = 0
        ind2 = 0
        l1 = []
        l2 = []
        for c1,c2 in zip(aln[0], aln[1]):
            if c1=='-': ind2 += 1
            elif c2=='-': ind1 += 1
            else: # we have a pair
                l1.append(resList1[ind1])
                l2.append(resList2[ind2])
                ind1 += 1
                ind2 += 1
        return ResidueSet(l1),ResidueSet(l2)


    def getAtomTypePairs(self, molname, atomtype=None):
        # return atom pairs (based on the specified atom type) from the two aligned residue sets 
        set1, set2 = self.rmsdPairs[molname]
        atomtype = {"C-alpha": "CA", "Backbone": "backbone"}.get(atomtype, "All")
        if isinstance(set1, ResidueSet):
            if atomtype != "All":
                from time import time
                refAtoms = set1.atoms.get(atomtype)
                mobAtoms = set2.atoms.get(atomtype)
                if len(refAtoms) != len(mobAtoms):
                    refAtoms = AtomSet()
                    mobAtoms = AtomSet()
                    for res1, res2 in zip(set1, set2):
                        atms1 = res1.atoms.get(atomtype)
                        atms2 = res2.atoms.get(atomtype)
                        if len(atms1) == len(atms2):
                            refAtoms.extend(atms1)
                            mobAtoms.extend(atms2)
            else: # "All"
                refAtoms,mobAtoms = matchResSetsByAtomName(set1, set2)          
        else:
            set1 = AtomSet(set1)
            set2 = AtomSet(set2)
            if atomtype != "All":
                refAtoms = set1.get(atomtype)
                mobAtoms = set2.get(atomtype)
            else: # "All"
                refAtoms = set1
                mobAtoms = set2
        return refAtoms, mobAtoms


    def computeRMSD(self, refcoords, mobcoords):
        rmsdCalc = RMSDCalculator(refcoords)
        rmsd = rmsdCalc.computeRMSD(mobcoords)
        return rmsd


    def setManualResiduePairs_cb(self, set1, set2, item):
        if len(set1):
            atomtype = None
            if self.atpairedbox:
                atomtype = self.atpairedbox.get()
            mol = set2.top.uniq()[0]
            molname = mol.name
            self.rmsdPairs[molname] = [set1, set2]
            refAtoms, mobAtoms = self.getAtomTypePairs(molname, atomtype)
            refcoords = refAtoms.coords
            mobcoords = mobAtoms.coords
            refmol = refAtoms.top.uniq()[0]
            trefcoords = self.vf.getTransformedCoords(refmol, refcoords)
            tmobcoords = self.vf.getTransformedCoords(mol, mobcoords)
            rmsd = self.computeRMSD(trefcoords, tmobcoords)
            self.updatePairsRMSDTable(item, rmsd, len(refcoords))
        # destroy the residue chooser widget and restore the RMSD/Pair form
        self.residueChooser.topFrame.destroy()
        #self.vf.dashboard.master3.forget()
        #self.vf.dashboard.applyButton.master.forget()
        #self.vf.dashboard.master3.pack(expand=1, fill='both')
        #self.vf.dashboard.applyButton.master.pack(fill='x', expand=0)
        #self.vf.dashboard.master4.pack(expand=0, fill='x')
        self.vf.dashboard.paramsNB.pack(fill='both', expand=1)
        self.vf.dashboard.applyButton.master.pack(fill='x', expand=0)
        # the notebook tabs look somewhat distorted at this point,
        # the following code fixes this 
        #nb=self.vf.dashboard.paramsNB
        #curpage = nb.getcurselection()
        #nb._topPageName=None
        #nb.selectpage(curpage)


    def setManualAtomPairs_cb(self, set1, set2, item):
        if len(set1):
            refAtoms = AtomSet(set1)
            mobAtoms = AtomSet(set2)
            mol = mobAtoms.top.uniq()[0]
            molname = mol.name
            self.rmsdPairs[molname] = [refAtoms, mobAtoms]
            refcoords = refAtoms.coords
            mobcoords = mobAtoms.coords
            refmol = refAtoms.top.uniq()[0]
            trefcoords = self.vf.getTransformedCoords(refmol, refcoords)
            tmobcoords = self.vf.getTransformedCoords(mol, mobcoords)
            rmsd = self.computeRMSD(trefcoords, tmobcoords)
            #print "rmsd:", rmsd
            self.updatePairsRMSDTable(item, rmsd, len(refcoords))


    def updatePairsRMSDTable(self, item, rmsd, npairs, score=None):
        #print "updatePairsRMSDTable", item, rmsd,  npairs, score
        lbox = self.RMSDmlb.listbox
        lbox.itemelement_config(item, lbox.column(3),
                                lbox.element('text'), text="%.3f"%rmsd,
                                datatype=TkTreectrl.DOUBLE, data=rmsd)
        lbox.itemelement_config(item, lbox.column(2),
                                lbox.element('text'), text=str(npairs),
                                datatype=TkTreectrl.INTEGER, data=npairs)
        if score is not None:
            if type(score) == str:
                lbox.itemelement_config(item, lbox.column(4),
                                lbox.element('text'), text=score,
                                datatype=TkTreectrl.STRING, data=score)
            else:
                lbox.itemelement_config(item, lbox.column(4),
                                        lbox.element('text'), text="%.3f"%score,
                                        datatype=TkTreectrl.DOUBLE, data=score)


    def findCheckedInTable(self):
        # return list of items in the Molecule-#pairs-RMSD table
        # that have "fit" checkbutton checked.
        lbox = self.RMSDmlb.listbox
        items = []
        for i, entry in enumerate(lbox.get(0, 'end')):
            state = lbox.itemstate_forcolumn(i+1,  lbox.column(0))
            if state is not None: # checked
                items.append([i+1, entry])
        return items
    

    def selectSeqalignParams_cb(self, pagename):
        # callback of the paramsNB , when a page is selected
        #print "pagename:", pagename
        selectedItems = self.findCheckedInTable()
        selected = len(selectedItems)
        if pagename == "Rendering":
            if not selected:
                self.seqalParams.button.configure(state='disable')
            else:
                identical = 0
                for item in selectedItems:
                    if item[1][-1] == 'identical':
                        identical += 1
                if identical == selected:
                    self.seqalParams.button.configure(state='disable')
                else:
                    self.seqalParams.button.configure(state='normal')
                
            self.vf.dashboard.applyButton.configure(state='disable')
            self.vf.dashboard.closeButton.configure(state='disable')
        elif pagename == "Basic":
            if not selected:
                self.vf.dashboard.applyButton.configure(state='disable')
            else:
                self.vf.dashboard.applyButton.configure(state='normal')
            self.vf.dashboard.closeButton.configure(state='normal')


    def moveWith_cb(self, event=None):
        items = self.findCheckedInTable()
        if not len(items):
            self.moveWithButton.configure(text="Move with 0 mols")
            return
        entry = items[0][1]
        molname = entry[1]
        movemols = self.movewithMols.get(molname, [])
        refatset, sets = self.getAtomSets(self.vf.Mols)
        mols = []
        var = []
        dialog = Pmw.Dialog(self.form, buttons = ('OK','Cancel'),
                            defaultbutton = 'OK', title='Select mols')
        dialog.withdraw()
        parent = dialog.interior()
        for item in sets:
            mol = item[0]
            name = mol.name
            if name != molname:
                mols.append(mol)
                v = Tkinter.IntVar()
                var.append(v)
                if mol in movemols:
                    v.set(1)
                w = Tkinter.Checkbutton(parent, text=name, variable=v)
                w.pack(side='top', expand=1, fill='x')
        ans = dialog.activate(geometry = '+%d+%d' % (self.vf.master.winfo_x(),
                                      self.vf.master.winfo_y()+self.vf.master.winfo_height()/2) )
        #ans = dialog.activate()
        if ans == "OK":
            movemols=[]
            for i, v in enumerate(var):
                if v.get():
                    movemols.append(mols[i])
            self.movewithMols[molname] = movemols
        nmols = len(movemols)
        #print "move with:", molname, movemols
        self.moveWithButton.configure(text="Move with %d mols"%nmols)
        



class SequenceAlignmentParams:

    def __init__(self, master, callback=None):
        if not master: 
            master = Tkinter.Toplevel()
        self.master = master
        self.gapopen = 10.0
        self.gapext = 0.20
        self.matrix = "pam30"
        self.callback = callback
        self.topFrame = frame = Tkinter.Frame(self.master)
        items = [ 'blosum30', 'blosum35', 'blosum40', 'blosum45', 'blosum50', 'blosum55', 'blosum60', 'blosum62', 'blosum65', 'blosum70', 'blosum75', 'blosum80', 'blosum85', 'blosum90', 'blosum95', 'blosum100', 'gonnet', 'ident',  'pam30', 'pam60', 'pam90', 'pam120', 'pam180', 'pam250', 'pam300', 'pam60']
        self.matrixBox = b1 = Pmw.ComboBox(frame,
            label_text = "Matrix:",
            labelpos = 'w',
            scrolledlist_items = items,
            selectioncommand = self.selectMatrix_cb,)
        b1.selectitem(self.matrix)
        b1.pack(side='top', expand=1, fill="both")
        
        self.gapopenEntry = g1 = Pmw.EntryField(frame,
                labelpos = 'w',
                value = str(self.gapopen),
                label_text = 'Gap opening:',
                validate = {'validator' : 'real',
                        'min' : 1.0, 'max' : 100.0, },
                )
        g1.pack(side='top', expand=1, fill= "x")

        self.gapextEntry = g2 =  Pmw.EntryField(frame,
                labelpos = 'w',
                value = str(self.gapext),
                label_text = 'Gap extension:',
                validate = {'validator' : 'real',
                        'min' : 0.0, 'max' : 100.0, },
                )
        g2.pack(side='top', expand=1, fill= "x")

        self.button = Tkinter.Button(frame, text="Realign",
                                     command=self.align_cb,
                                     state="disable")
        self.button.pack(side='top', expand=1, fill= "x")
        frame.pack(expand=0, fill= "x")


    def selectMatrix_cb(self, matrix):
        self.matrix = matrix


    def getParams(self):
        self.gapopen = float(self.gapopenEntry.getvalue())
        self.gapext = float(self.gapextEntry.getvalue())
        return self.matrix, self.gapopen, self.gapext

    def align_cb(self):
         if self.callback:
             self.callback()

    


    
