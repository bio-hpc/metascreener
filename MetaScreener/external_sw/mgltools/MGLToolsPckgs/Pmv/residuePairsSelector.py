import Tkinter, Pmw
from mglutil.util.callback import CallbackFunction
from MolKit.protein import ResidueSet

class ResSelector:
    """A widget containing 3 scrolled listboxes:
    - first box lists names of residue set 1,
    - second box lists names of residue set 2,
    Clicking on the names in the first and the second boxes creates
    a pair of names in the third box.
    """
    def __init__(self, residues1, residues2, master=None):
        if not master: 
            master = Tkinter.Toplevel()
        self.master = master
        self.topFrame = Tkinter.Frame(self.master)
        self.residues1 = residues1
        self.residues2 = residues2
        objname1 = residues1.top.uniq()[0].name
        objname2 = residues2.top.uniq()[0].name
        self.state = 'New Pair'
        self.nbPairs = 0  
        self.pairs = []
        self.callback = None
        self.args = ()
        label = Tkinter.Label(self.topFrame, text="Pair up residues")
        label.pack(side='top', fill="x")

        # create Frame for 3 listboxes
        frame = Tkinter.Frame(self.topFrame)
        self.reslist1 = reslist1 = ["#%i, %s" % (i+1, res.name) for i, res in enumerate(residues1)]
        self.reslist2 = reslist2 = ["#%i, %s" % (i+1, res.name) for i, res in enumerate(residues2)]
        
        self.box1 = b1 = Pmw.ScrolledListBox(
            frame,
            label_text = objname1,
            labelpos = 'nw',
            selectioncommand = self.selectFirstRes_cb,
            items = reslist1,
            usehullsize = 1,
            hull_width = 100,
            hull_height = 200,
            horizscrollbar_width=7,
            vertscrollbar_width=7,)
        b1.pack(side = 'left', anchor = 'n',padx = 8, pady = 8, fill = 'both', expand = 1)
        self.box2 = b2 = Pmw.ScrolledListBox(frame,
                           label_text = objname2,
                           labelpos = 'nw',
                           selectioncommand = self.selectLastRes_cb,
                           items = reslist2,
                           usehullsize = 1,
                           hull_width = 100,
                           hull_height = 200,
                           horizscrollbar_width=7,
                           vertscrollbar_width=7,)
        b2.pack(side = 'left', anchor = 'n',padx = 8, pady = 8, fill = 'both', expand = 1)
        # box containing pairs:
        self.pairsBox = b3 = Pmw.ScrolledListBox(frame,
                           label_text = 'pairs:',
                           labelpos = 'nw',
                           usehullsize = 1,
                           hull_width = 200,
                           hull_height = 200,
                           horizscrollbar_width=7,
                           vertscrollbar_width=7)
        b3.pack(side = 'left', anchor = 'n',padx = 8, pady = 8, fill = 'both', expand = 1)

        frame.pack(side='top', expand=1, fill="both")

        frame2 = Tkinter.Frame(self.topFrame)

        self.applyButton = Tkinter.Button(frame2, text='OK',
                                          command=self.apply_cb)
        self.applyButton.pack(side='left', fill='x', expand=1)

        self.deleteButton = Tkinter.Button(frame2, text='Delete Pair',
                                           command=self.deletePair_cb)
        self.deleteButton.pack(side='left', fill='x', expand=1)
        
        frame2.pack(side='top', expand=0, fill="x")

        self.topFrame.pack(side='top', expand=1, fill="both")


    def selectFirstRes_cb(self, event=None):
        """callback of the first listbox"""
        sels = self.box1.getcurselection()
        if len(sels) == 0:
            #print 'No selection 1'
            return
        resname1 = sels[0]
        #print "select first", resname1, self.state,
        ind , name = resname1.split(", ")
        resind1 = int(ind[1:])-1
        if self.state=='New Pair':
            self.pairs.append( [ resind1, None] )
            # add the name of the first residue to the "pair" box
            self.pairsBox.insert('end', '[%d] %s - '%(self.nbPairs+1, resname1))
            self.state = 'Got First Res'
        elif self.state == 'Got First Res':
            # replace existing name of the first residue in the "pair" box with a new one
            self.pairs[-1][0] = resind1
            self.pairsBox.delete('end')
            self.pairsBox.insert('end', '[%d] %s - '%(self.nbPairs+1, resname1))
        elif self.state=='Got Second Res':
            # create pair
            self.pairs[-1][0] = resind1
            resind2 = self.pairs[-1][1]
            resname2 = "#%i, %s"%(resind2+1, self.residues2[resind2].name)
            self.pairsBox.delete('end')
            self.pairsBox.insert('end', '[%d] %s - %s'%(self.nbPairs+1, resname1,
                                                      resname2))
            self.nbPairs += 1
            # remove the names of the pair from box1 and box2
            #(since they cannot be selected for another pair)
            boxind1 = self.box1.get(0, 'end').index(resname1)
            self.box1.delete(boxind1)
            boxind2 = self.box2.get(0, 'end').index(resname2)
            self.box2.delete(boxind2)            
            self.state='New Pair'
        #print "new state:", self.state
        

    def selectLastRes_cb(self, event=None):
        """callback of the second listbox"""
        sels = self.box2.getcurselection()
        if len(sels) == 0:
            #print 'No selection 2'
            return
        resname2 = sels[0]
        ind , name = resname2.split(", ")
        resind2 = int(ind[1:])-1
        #print "select second", resname2, self.state,
        if self.state=='New Pair':
            # add the name of the second residue to the "pair" box
            self.pairs.append( [None, resind2] )
            self.state = 'Got Second Res'
            self.pairsBox.insert('end', '[%d] - %s'%(self.nbPairs+1, resname2))
        elif self.state=='Got First Res':
            # create pair
            self.pairs[-1][1] = resind2
            resind1 = self.pairs[-1][0]
            resname1 = "#%i, %s"%(resind1+1, self.residues1[resind1].name)
            self.pairsBox.delete('end')
            self.pairsBox.insert('end', '[%d] %s - %s'%(self.nbPairs+1, resname1,
                                                      resname2))

            # remove the names of the pair from box1 and box2 (since they cannot be selected for another pair)
            boxind1 = self.box1.get(0, 'end').index(resname1)
            self.box1.delete(boxind1)
            boxind2 = self.box2.get(0, 'end').index(resname2)
            self.box2.delete(boxind2)
            self.state='New Pair'
            self.nbPairs += 1
        elif self.state=='Got Second Res':
            # replace existing name of the second residue in the "pair" box with a new one
            self.pairs[-1][1] = resind2
            self.pairsBox.delete('end')            
            self.pairsBox.insert('end', '[%d] - %s'%(self.nbPairs+1, resname2))
        #print "new state:", self.state


    def deletePair_cb(self):
        """Callback of the Delete pair button"""
        sel = self.pairsBox.getcurselection()
        if not len(sel): return
        pairName = sel[0]          
        pairNum = int(pairName.split()[0][1:-1])-1
        resind1, resind2 = self.pairs.pop(pairNum)
        self.nbPairs -= 1
        self.pairsBox.delete(0, 'end')
        i = 1
        for i1, i2 in self.pairs:
            res1 = self.residues1[i1]
            res2 = self.residues2[i2]
            self.pairsBox.insert('end', '[%d] #%i, %s - #%i, %s'%(i, i1+1, res1.name, i2+1, res2.name))
            i = i+1
        if self.state == "Got Second Res" or self.state == "Got First Res":
            self.state = "New Pair"
            return
        #insert the deleted pair back to the residue lists in box1 and box2
        reslist1 = self.box1.get(0, 'end')
        resname1 = "#%i, %s"%(resind1+1, self.residues1[resind1].name)
        for i , entry in enumerate(reslist1):
            ind , name = entry.split(", ")
            ind = int(ind[1:])-1
            if ind > resind1: break
        self.box1.insert(i, resname1)
        
        reslist2 = self.box2.get(0, 'end')
        resname2 = "#%i, %s"%(resind2+1, self.residues2[resind2].name)
        for i , entry in enumerate(reslist2):
            ind , name = entry.split(", ")
            ind = int(ind[1:])-1
            if ind > resind2: break
        self.box2.insert(i, resname2)


    def getResiduePairs(self):
        """Returns two lists of residues from the pair box """
        if self.state != "New Pair":
            if len(self.pairs):
                self.pairs.pop(-1)
        respairs =  [[self.residues1[i1], self.residues2[i2]]  for i1,i2 in self.pairs]
        if not len(respairs):
            return [[], []]
        set1, set2 = zip(*respairs)
        return ResidueSet(set1), ResidueSet(set2)


    def apply_cb(self):
        l1, l2 = self.getResiduePairs()
        if self.callback:
            self.callback(l1, l2, *self.args)

    def setCallback(self, callback, args):
        assert callable(callback) 
        self.callback = callback
        self.args = args
        



## if __name__ == '__main__':
##     root = Tkinter.Tk()
##     from MolKit import Read 
##     refmol = Read("1crn.pdb")
##     mol = Read("1crn.pdb")
##     res1 =  refmol.chains.residues
##     res2 = mol.chains.residues
##     w = ResSelector(res1, res2)
