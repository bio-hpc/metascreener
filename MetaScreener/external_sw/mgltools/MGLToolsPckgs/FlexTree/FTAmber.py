## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: Nov 2006 Author: Yong Zhao
#
#    yongzhao@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Yong Zhao and TSRI
#
#########################################################################

### Yong's code for minimization.. based on SFF.
## 1) use protonate in Amber to add Hs
## 2) add charge

import pdb, numpy.oldnumeric as Numeric, random, types
from MolKit.stringSelector import CompoundStringSelector


from MolKit.molecule import Atom, AtomSet, Bond, Molecule, MoleculeSet
from MolKit.protein import Protein, ProteinSet, Chain, Residue, ResidueSet
from MolKit import Read
#mol=Read('1crn.pdb')[0]

from string import letters

from Pmv.qkollua import q
from MolKit import WritePDB


from MolKit.tree import TreeNode, TreeNodeSet
from MolKit.protein import Protein

from sff.amber import Amber94, AmberParm


class FTAmber94:
    def __init__(self, mol, movingAtoms=None, offset=1):
        """ setup amber calculaton  """
        self.offset=offset
        if type(mol) is types.StringType:
            try:
                mol=Read(mol)[0] ## assume Hs are properly added..
                mol.buildBondsByDistance()
            except:
                print 'error in opening', mol
                raise IOError
        else:
            assert isinstance( mol, Protein)
                
        self.mol=mol
        self.atoms=mol.allAtoms        
        self.AddKollmanCharges()
        self.FixAmberHAtomNames()
        if movingAtoms ==None:
            self.movingAtoms=AtomSet()  
        else:
            if type(movingAtoms) is types.StringType:
                css = CompoundStringSelector()
                tmp=MoleculeSet()
                tmp.append(self.mol)
                result = css.select(tmp, movingAtoms)[0]
                self.movingAtoms=result.findType(Atom)
            elif isinstance( movingAtoms, TreeNodeSet):
                self.movingAtoms=movingAtoms.findType(Atom)
            else:
                print "error in movingAtoms"
                return

        self.SetupAmber94()
        self.frozenAtoms=self.mol.allAtoms-self.movingAtoms
        if len(self.movingAtoms)!=0:
            print "number of frozen atoms:", len(self.frozenAtoms)
            self.freezeAtoms(self.amber, self.frozenAtoms)
       
        return
            
        
    ### add charge, clone from AddKollmanChargesCommand in Pmv/editCommands.py
    def AddKollmanCharges(self):
        mol=self.mol
        nodes = mol.allAtoms
        if len(nodes)==0: return 'ERROR'

        self.FixHydrogenAtomNames()

        allRes = nodes.findType(Residue).uniq()
        allAtoms = allRes.atoms
        allChains = allRes.parent.uniq()

        total = 0.0
        for a in allAtoms:
            if not q.has_key(a.parent.type):
                a._charges['Kollman'] = 0.0
            else:
                dict = q[a.parent.type]
                if dict.has_key(a.name):
                    a._charges['Kollman'] = dict[a.name]
                    total = total + a._charges['Kollman']
                else:
                    a._charges['Kollman'] = 0.0

        #fix histidines
        hisRes = allRes.get(lambda x:x.name[:3]=='HIS')
        if hisRes is not None and len(hisRes)!=0:
            for hres in hisRes:
                total = self.fixHisRes(hres, total)

        #fix cys's
        cysRes = allRes.get(lambda x:x.name[:3]=='CYS')
        if cysRes is not None and len(cysRes)!=0:
            for cres in cysRes:
                total = self.fixCysRes(cres, total)

        #check for termini:
        for ch in allChains:
            if ch.residues[0] in allRes:
                ##fix the charge on Hs 
                total = self.fixNterminus(ch.residues[0],total)
            if ch.residues[-1] in allRes:
                self.fixCterminus(ch.residues[-1], total)

        #make Kollman the current charge
        allAtoms.chargeSet = 'Kollman'
        return total
    

    def FixHydrogenAtomNames(self):
        nodes = self.mol.allAtoms
        if not len(nodes): return 'ERROR'

        allAtoms = nodes.findType(Atom)
        allHs = allAtoms.get('H*')
        if allHs is None or len(allHs)==0: return 'ERROR'
        ct = 0
        for a in allHs:
            if not len(a.bonds): continue
            b=a.bonds[0]
            a2=b.atom1
            if a2==a: a2=b.atom2
            if a2.name=='N':
                hlist = a2.findHydrogens()
                if len(hlist) == 1:
                    if a.name!='HN':
                        #print 'fixing atom ', a.full_name()
                        a.name = 'HN'
                        ct = ct + 1
                else:
                    for i in range(len(hlist)):
                        if hlist[i].name[:2]!='HN' or len(hlist[i].name)<3:
                            #print 'fixing atom ', hlist[i].full_name()
                            ct = ct + 1
                            hlist[i].name = 'HN'+str(i+1)
            if len(a2.name)>1:
                remote=a2.name[1]
                if remote in letters:
                    if remote!=a.name[1]:
                        #print 'fixing remote atom', a.full_name()
                        ct = ct + 1
                        a.name = a.name[0]+a2.name[1]
                        if len(a.name)>2:
                            a.name=a.name+a.name[2:]
                else:
                    newname = a.name + remote
                    if len(a.name)>1:
                        newname=newname+a.name[1:]

        return
        ## end of FixHydrogenAtomNames



    def fixNterminus(self, nres, total):
        """newTotal<-fixNterminu(nres, total)
           \nnres is the N-terminal residue
           \ntotal is previous charge total on residueSet
           \nnewTotal is adjusted total after changes to nres.charges
        """
        nresSet =  nres.atoms.get('N')
        if nresSet is None or len(nresSet)==0:
            if q.has_key(nres.type):
                for at in nres.atoms:
                    try:
                        at._charges['Kollman'] = q[at.parent.type][at.name]
                    except:
                        at._charges['Kollman'] = 0.0
            else:
                print  nres.name, ' not in qkollua; charges set to 0.0'
                for at in nres.atoms:
                    at._charges['Kollman'] = 0.0
            return total
        Natom = nres.atoms.get('N')[0]
        caresSet = nres.atoms.get('CA')
        if caresSet is None or len(caresSet)==0:
            if q.has_key(nres.type):
                for at in nres.atoms:
                    at._charges['Kollman'] = q[at.parent.type][at.name]
            else:
                print  nres.name, ' not in qkollua; charges set to 0.0'
                for at in nres.atoms:
                    at._charges['Kollman'] = 0.0
            return total
        CAatom = nres.atoms.get('CA')
        if CAatom is not None and len(CAatom)!=0:
            CAatom = nres.atoms.get('CA')[0]
            hlist = Natom.findHydrogens()
            #5/5:assert len(hlist), 'polar hydrogens missing from n-terminus'
            if not len(hlist): 
                print 'polar hydrogens missing from n-terminus of chain ' + nres.parent.name
                #warningMsg('polar hydrogens missing from n-terminus')
            if nres.type == 'PRO':
                #divide .059 additional charge between CA + CD
                #FIX THIS what if no CD?
                #CDatom = nres.atoms.get('CD')[0]
                CDatom = nres.atoms.get('CD')
                if CDatom is not None and len(CDatom)!=0:
                    CDatom = CDatom[0]
                    CDatom._charges['Kollman'] = CDatom._charges['Kollman'] + .029
                else:
                    print 'WARNING: no CD atom in ', nres.name
                Natom._charges['Kollman'] = Natom._charges['Kollman'] + .274
                CAatom._charges['Kollman'] = CAatom._charges['Kollman'] + .030
                for ha in hlist:
                    ha._charges['Kollman'] = .333
            else:
                Natom._charges['Kollman'] = Natom._charges['Kollman'] + .257
                CAatom._charges['Kollman'] = CAatom._charges['Kollman'] + .055
                for ha in hlist:
                    ha._charges['Kollman'] = .312

            return total + 1
        else:
            print 'WARNING: no CA atom in ', nres.name
            return total


    def fixCterminus(self, cres, total):
        """newTotal<-fixCterminu(cres, total)
            \ncres is the C-terminal residue
            \ntotal is previous charge total on residueSet
            \nnewTotal is adjusted total after changes to cres.charges
        """
        OXYatomSet = cres.atoms.get('OXT')
        if OXYatomSet is not None and len(OXYatomSet)!=0:
            OXYatom = OXYatomSet[0]
            OXYatom._charges['Kollman'] = -.706
            #CAUTION!
            CAatom = cres.atoms.get('CA')
            if CAatom is not None and len(CAatom)!=0:
                CAatom = cres.atoms.get('CA')[0]
                CAatom._charges['Kollman'] = CAatom._charges['Kollman'] - .006
                #CAUTION!
                Catom = cres.atoms.get('C')
                if Catom is not None and len(Catom)!=0:
                    Catom = cres.atoms.get('C')[0]
                    Catom._charges['Kollman'] = Catom._charges['Kollman'] - .082
                    Oatom = cres.atoms.get('O')
                    if Oatom is not None and len(Oatom)!=0:
                        #CAUTION!
                        Oatom = cres.atoms.get('O')[0]
                        Oatom._charges['Kollman'] = Oatom._charges['Kollman'] - .206
                        return total - 1


        else: 
            #if there is no OXT don't change charges
            return total


    def fixHisRes(self, his, total):
        """newTotal<-fixHisRes(his, total)
           \nhis is a HISTIDINE residue
           \ntotal is previous charge total on residueSet
           \nnewTotal is adjusted total after changes to his.charges
        """
        hisAtomNames = his.atoms.name
        #oldcharge = Numeric.sum(his.atoms._charges['Kollman'])
        oldcharge = 0
        for at in his.atoms:
            oldcharge = oldcharge + at._charges['Kollman']
        assertStr = his.name + ' is lacking polar hydrogens'
        assert 'HD1' or 'HE2' in hisAtomNames, assertStr
        #get the appropriate dictionary
        if 'HD1' in hisAtomNames and 'HE2' in hisAtomNames:
            d = q['HIS+']
        elif 'HD1' in  hisAtomNames:
            d = q['HISD']
        elif 'HE2' in hisAtomNames:
            d = q['HIS']
        else:
            msgStr = his.full_name() + ' missing both hydrogens!'
            print msgStr
            return total

        #assign charges
        for a in his.atoms:
            if d.has_key(a.name):
                a._charges['Kollman'] = d[a.name]
            else:
                a._charges['Kollman'] = 0.0

        #correct total
        #newcharge = Numeric.sum(his.atoms._charges['Kollman'])
        newcharge = 0
        for at in his.atoms:
            newcharge = newcharge + at._charges['Kollman']
        total = total - oldcharge + newcharge
        return total


    def fixCysRes(self, cys, total):
        cysAtomNames = cys.atoms.name
        #oldcharge = Numeric.sum(cys.atoms._charges['Kollman'])
        oldcharge = 0
        for at in cys.atoms:
            oldcharge = oldcharge + at._charges['Kollman']
        #get the appropriate dictionary
        if 'HG' in cysAtomNames:
            d = q['CYSH']
        else:
            #cystine
            d = q['CYS']

        #assign charges
        for a in cys.atoms:
            if d.has_key(a.name):
                a._charges['Kollman'] = d[a.name]
            else:
                a._charges['Kollman'] = 0.0

        #correct total
        #newcharge = Numeric.sum(cys.atoms._charges['Kollman'])
        newcharge = 0
        for at in cys.atoms:
            newcharge = newcharge + at._charges['Kollman']
        total = total - oldcharge + newcharge
        return total


    def FixAmberHAtomNames(self):
        all = self.mol.allAtoms
        allHs = all.get('H.*')
        if not allHs: return 'ERROR'
        # use _ct to only process each hydrogen once
        allHs._ct = 0

        #this leaves out hydrogens whose bonded atom isn't in nodes
        #hasHAtoms = AtomSet(filter(lambda x, all=all: x.findHydrogens(), all))
        #for a in hasHAtoms:
        for h in allHs:
            if h._ct: continue
            if not len(h.bonds): continue
            b = h.bonds[0]
            a = b.atom1
            if a==h: a = b.atom2

            if len(a.name)==1:
                astem = ''
            else:
                astem = a.name[1:]

            hlist = AtomSet(a.findHydrogens())
            #try to preserve order of H's if there is any
            hlist.sort()
            hlen = len(hlist)

            #SPECIAL TREATMENT for CYSTEINES:
            parType = h.parent.type
            sibNames = a.parent.atoms.name
            #NB CYS with no HG is CYM
            if parType=='CYS' or parType=='CYM':
                #check for nterminus + for cterminus + for disulfide bond:
                isTerminus = 'OXT' in sibNames or hlen==3
                # must have BOND S-S  and no HG atom for treatment as CYX 
                sAt = h.parent.atoms.get(lambda x: x.name=='SG')[0]
                hasDisulfide = len(sAt.bonds)==2 
                #problem1: in non-terminal CYM, H bonded to N is 'HN'
                if a.name=='N' and 'HG' not in sibNames \
                    and not isTerminus and not hasDisulfide:
                    #distinguish between cystine + neg charged cys:
                    #CYX v. CYM
                    astem = 'N'
                #problem2: in n- or c-terminal CYS, H bonded to SG is 'HSG'
                elif isTerminus and a.name=='SG':
                    astem = 'SG'

            if hlen == 1:
                hlist[0].name = 'H' + astem
            elif hlen == 2:
                #N-terminus PRO has H2+H3
                if len(a.name)>1 and a.name[0]=='N':
                    rl = [1,2]
                else:
                    rl = [2,3]

##                 ## Yong tried to fix this..
##                 if len(a.name)>1:
##                     rl = [1,2]
##                 elif a.parent.name[:3]=='PRO'and (a.name[0]=='N'):
##                     rl = [2,3]
##                 else:
##                     print a.parent.name, a.name
##                     rl = [2,3]
##                     #if a.parent.name=='PRO19':
##                     #    raise

                for i in rl:
                    hat = hlist[i-2]
                    hat.name = 'H' +  astem + str(i)
                    hat._ct = 1
            elif hlen == 3:
                for i in range(3):
                    hat = hlist[i]
                    hat.name = 'H' + astem + str(i+1)
                    hat._ct = 1
        delattr(allHs, '_ct')
        return


    

    def SetupAmber94(self, key='test'):
        atoms = self.mol.allAtoms
        dataDict ={}
        #dataDict = kw.get('dataDict', {})
        #print 'calling Amber94 init with dataDict=', dataDict
        amb_ins = Amber94(atoms, dataDict = dataDict)
        #amb_ins.key = key
        #Amber94Config[key] = [amb_ins]
        #self.CurrentAmber94 = amb_ins
        #print 'set CurrentAmber94 to', self.CurrentAmber94
        self.amber=amb_ins
        return amb_ins


    def freezeAtoms(self, amb_ins, atsToFreeze):
        #amb_ins = Amber94Config[key][0]
        #self.CurrentAmber94 = amb_ins

        #check that all the atsToFreeze are in amber instances' atoms
        chain_ids = {}
        for c in amb_ins.atoms.parent.uniq().parent.uniq():
            chain_ids[id(c)] = 0

        for c in atsToFreeze.parent.uniq().parent.uniq():
            assert chain_ids.has_key(id(c)), 'atoms to freeze not in Amber94 instance.atoms'

        atsToFreezeIDS = {}
        for at in atsToFreeze:
            atsToFreezeIDS[id(at)] = 0
        atomIndices = map(lambda x, d=atsToFreezeIDS: d.has_key(id(x)), amb_ins.atoms)
        #FIX THIS: it has to be put into the correct c-structure
        #print 'setting ', key, ' frozen to ', atomIndices
        #amb_ins.frozen = atomIndices
        apply(amb_ins.freezeAtoms, (atomIndices,), {})
        numFrozen = Numeric.add.reduce(Numeric.array(amb_ins.frozen))
        #print 'numFrozen=', numFrozen
        return numFrozen

    def minimize(self):        
        #res=self.amber.minimize(drms=1e-06, dfpred=10., maxIter=10000)
        res=self.amber.minimize() #drms=0.1, dfpred=10., maxIter=500)
        print res, 
        #print "E=", self.amber.energies[8]
        print "E=", self.amber.energies[0]
        #print self.amber.energies


## 1) load molecule
mol=Read('mol.pdb')[0]  ## 1crn with Hs
#mol=Read('link1H.pdb')[0]
mol.buildBondsByDistance()
atoms=mol.allAtoms
#atoms.sort()
atoms.addConformation(atoms.coords[:])

    
## ## 2.1) add charge
## AddKollmanCharges(mol)

## ## 2.2) fix H names
## ## ignore this if input is generated by protonate of Amber.. 
## FixAmberHAtomNames(mol)

## ## 3) setup amber 
## amber=SetupAmber94(mol)

## ## 4) freeze the rigid part
## movingAtoms=mol.chains.residues.get('PRO19-THR21').atoms
## movingAtoms.sort()
## #print movingAtoms.name
## #print 'before minimization. atom names:\n',movingAtoms.name



## atsToFreeze=mol.allAtoms - movingAtoms
## atsToFreeze.sort()
## freezeAtoms(amber, atsToFreeze)




## ## possible return codes:\n
## ##         >0    converged, final iteration number\n
## ##         -1    bad line search, probably an error in the relation
## ##                 of the funtion to its gradient (perhaps from
## ##                 round-off if you push too hard on the minimization).\n
## ##         -2    search direction was uphill\n
## ##         -3    exceeded the maximum number of iterations\n
## ##         -4    could not further reduce function value\n
## ##         -5    stopped via signal   (bsd)\n


## def go(amber):
##     maxFailNum=10
##     failed=0
##     converged=False
##     global counter
##     while failed < maxFailNum:
##         res=amber.minimize(drms=1e-06, dfpred=10., maxIter=100000)
##         E=amber.energies[8]
##         print res, E
##         if res>0:
##             converged=True
##             print "converged.. E =", E
##             break
##         else:
##             failed +=1

##     if converged:
##         atoms=amber.atoms
##         newcoords = Numeric.array(amber.coords[:])
##         newcoords.shape = (-1,3)
##         atoms.updateCoords(newcoords.tolist(), 1)

##         outputFileName="linker_%d.pdb"%counter
##         #movingAtoms.sort()
##         #WritePDB(outputFileName, movingAtoms)
##         #WritePDB(outputFileName, atoms)
##         writer.write(outputFileName, movingAtoms, \
##                      records=['ATOM', 'HETATM', 'CONECT'],\
##                      bondOrigin='all')
##         counter +=1

"""
"""

## OFFSET=5

## def sampling(movingAtoms, number=1):
##     coords=movingAtoms.coords  
##     newCoords=coords[:]
##     for i in range(len(coords)):
##         c=coords[i]
##         newCoords[i]=[c[0]+rand(OFFSET),c[1]+rand(OFFSET),c[2]+rand(OFFSET)]
##     movingAtoms.updateCoords(newCoords, 1)            
##     go(amber)

## sampling(movingAtoms)

