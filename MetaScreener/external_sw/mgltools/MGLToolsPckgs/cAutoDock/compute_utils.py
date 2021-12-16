##
## Copyright (C) The Scripps Research Institute 2006
##
## Authors: Alexandre Gillet <gillet@scripps.edu>
##  
## $Header: /opt/cvs/cAutoDockDIST/cAutoDock/compute_utils.py,v 1.1 2007/09/05 18:13:01 rhuey Exp $
## $Id: compute_utils.py,v 1.1 2007/09/05 18:13:01 rhuey Exp $
##  
##


## utils function use for computation during pattern detection


import Numeric,math
from MolKit.pdbWriter import PdbWriter
from MolKit.chargeCalculator import KollmanChargeCalculator,GasteigerChargeCalculator

import warnings
from cAutoDock import scorer as c_scorer
from memoryobject import memobject


class EnergyScorer:
    """ Base class for energy scorer """

    def __init__(self,atomset1,atomset2,func=None):

        self.atomset1 =atomset1
        self.atomset2 =atomset2
        
        # save molecule instance of parent molecule
        self.mol1 =  self.atomset1.top.uniq()[0]
        self.mol2 =  self.atomset2.top.uniq()[0]
        # dictionnary to save the state of each molecule when the
        # energy is calculated, will allow to retrieve the conformation
        # use for the energy calculation
        # keys are score,values is a list a 2 set of coords (mol1,mol2)
        self.confcoords = {}
        self.ms = ms = MolecularSystem()
        self.cutoff = 1.0
        self.score  = 0.0

                 
    def doit(self):

        self.update_coords()
        score,estat,hbond,vdw,ds= self.get_score()
        self.score = score
        self.saveCoords(score)
        self.atomset1.setConformation(0)
        self.atomset2.setConformation(0)
        return (score,estat,hbond,vdw,ds)

        
    def update_coords(self):
        """ update the coordinate of atomset """

        # use conformation set by dectected patterns
        if hasattr(self.mol1,'arconformationIndex'):
            self.atomset1.setConformation(self.mol1.arconformationIndex)
        if hasattr(self.mol2,'arconformationIndex'):
            self.atomset2.setConformation(self.mol2.arconformationIndex)
        # get the coords
        R_coords  = self.atomset1.coords
        L_coords =  self.atomset2.coords
        self.sharedMem[:] = Numeric.array(R_coords+L_coords, 'f')[:]
        c_updateCoords(self.proteinLen, self.msLen, self.ms,self.sharedMemPtr)


    def get_score(self):
        """ method to get the score """
        score = estat =  hbond = vdw = ds =  1000.
        return (score,estat,hbond,vdw,ds)


    def saveCoords(self,score):
        """methods to store each conformation coordinate.
         the score is use as the key of a dictionnary to store the different conformation.
         save the coords of the molecules to be use later to write out
         a pdb file
         We only save up 2 ten conformations per molecule. When 10 is reach we delete the one with the
         highest energy
         """
        score_int= int(score*100)
        # check number of conf save
        if len(self.confcoords.keys()) >= 50:
            # find highest energies
            val =max(self.confcoords.keys())
            del(self.confcoords[val])

        # add new conformation
        coords = [self.atomset1.coords[:],self.atomset2.coords[:]]
        self.confcoords[score_int] = coords


    def writeCoords(self,score=None,filename1=None,filename2=None,
                    sort=True, transformed=False,
                    pdbRec=['ATOM', 'HETATM', 'CONECT'],
                    bondOrigin='all', ssOrigin=None):
        """ write the coords of the molecules in pdb file
        pdb is file will have the molecule name follow by number of conformation
        """
        writer = PdbWriter()
        if score is None:
            score = min( self.confcoords.keys())
        if not self.confcoords.has_key(float(score)): return

        c1 = self.confcoords[score][0]
        c2 = self.confcoords[score][1]

        if filename1 is None:
            filename1 = self.mol1.name + '_1.pdb'
        prev_conf = self.setCoords(self.atomset1,c1)
        
        writer.write(filename1, self.atomset1, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)

        self.atomset1.setConformation(prev_conf)

        if filename2 is None:
            filename2 = self.mol2.name + '_1.pdb'
            
        prev_conf = self.setCoords(self.atomset2,c2)
        writer.write(filename2, self.atomset2, sort=sort, records=pdbRec,
                     bondOrigin=bondOrigin, ssOrigin=ssOrigin)
        self.atomset2.setConformation(prev_conf)
        

    def setCoords(self,atomset,coords):
        """ set the coords to a molecule """
        mol = atomset.top.uniq()[0]
        prev_conf = atomset.conformation[0]
        # number of conformations available
        confNum = len(atomset[0]._coords)
        if hasattr(mol, 'nrgCoordsIndex'):
            # uses the same conformation to store the transformed data
            atomset.updateCoords(coords, 
                                 mol.nrgCoordsIndex)
        else:
            # add new conformation to be written to file
            atomset.addConformation(coords)
            mol.nrgCoordsIndex = confNum
        atomset.setConformation( mol.nrgCoordsIndex )
        return prev_conf

        
    def pyMolToCAtomVect( self,mol):
        """convert Protein or AtomSet to AtomVector
        """
        from cAutoDock.scorer import AtomVector, Atom, Coords
        className = mol.__class__.__name__
        if className == 'Protein':
            pyAtoms = mol.getAtoms()
        elif className == 'AtomSet':
            pyAtoms = mol
        else:
            return None
        pyAtomVect = AtomVector()
        for atm in pyAtoms:
            a=Atom()
            a.set_name(atm.name)
            a.set_element(atm.autodock_element)# aromatic type 'A', vs 'C'
            coords=atm.coords
            a.set_coords( Coords(coords[0],coords[1],coords[2]))
            a.set_charge( atm.charge)
            try:
                a.set_atvol( atm.AtVol)
            except:
                pass
            try:
                 a.set_atsolpar( atm.AtSolPar)
            except:
                pass
            a.set_bond_ord_rad( atm.bondOrderRadius)
            a.set_charge( atm.charge)
            pyAtomVect.append(a)
        return pyAtomVect


    def free_memory(self):
        # free the shared memory
        memobject.free_shared_mem("SharedMemory")



class PairWiseEnergyScorer(EnergyScorer):
    """For each atom in one AtomSet, determine the electrostatics eneregy vs all the atoms in a second
    AtomSet using the C implementation of the autodock scorer.
    When using the autodock3 scorer, the receptor need to be loaded as a pdbqs file, the ligand as pdbqt.
    """

    
    def __init__(self,atomset1,atomset2,scorer_ad_type='305'):
        
        EnergyScorer.__init__(self,atomset1,atomset2)
        self.prop = 'ad305_energy'
        self.ms = ms = c_scorer.MolecularSystem()
        self.receptor= self.pyMolToCAtomVect(atomset1)
        self.ligand  = self.pyMolToCAtomVect(atomset2)
        
        self.r = ms.add_entities(self.receptor)
        self.l = ms.add_entities(self.ligand)
        
        ms.build_bonds( self.r )
        ms.build_bonds( self.l )
        # Notice: keep references to the terms !
        # or they will be garbage collected.
        self.scorer_ad_type = scorer_ad_type
        if self.scorer_ad_type == '305':
            self.ESTAT_WEIGHT_AUTODOCK = 0.1146 # electrostatics
            self.HBOND_WEIGHT_AUTODOCK = 0.0656 # hydrogen bonding
            self.VDW_WEIGHT_AUTODOCK   = 0.1485 # van der waals
            self.DESOLV_WEIGHT_AUTODOCK= 0.1711 # desolvation

        ## !!! Make sure that all the terms are saved and not freed after init is done
        ## keep them by making them attributes of  self.
        self.estat = c_scorer.Electrostatics(ms)
        self.hbond = c_scorer.HydrogenBonding(ms)
        self.vdw   = c_scorer.VanDerWaals(ms)
        self.ds    = c_scorer.Desolvation(ms)            
        self.scorer = c_scorer.WeightedMultiTerm(ms)
        self.scorer.add_term(self.estat, self.ESTAT_WEIGHT_AUTODOCK)
        self.scorer.add_term(self.hbond, self.HBOND_WEIGHT_AUTODOCK)
        self.scorer.add_term(self.vdw,   self.VDW_WEIGHT_AUTODOCK)
        self.scorer.add_term(self.ds,    self.DESOLV_WEIGHT_AUTODOCK)
        # shared memory, used by C++ functions
        self.proteinLen = len(atomset1)
        self.ligLen = len(atomset2)
        self.msLen =  self.proteinLen + self.ligLen
        self.sharedMem = memobject.allocate_shared_mem([self.msLen, 3],
                                                       'SharedMemory', memobject.FLOAT)
        self.sharedMemPtr = memobject.return_share_mem_ptr('SharedMemory')[0]
        #print "Shared memory allocated.."


    def get_score(self):
        """ return the score """
        
        mini = self.ms.check_distance_cutoff(0, 1, self.cutoff)

        # when number return should not do get_score ( proteins too close)
        # flag = (mini==1.0 and mini==2.0)
        flag =  (mini == mini)

        # for each of the terms and the score, we cap their max value to 100
        # so if anything is greater than 100 we assign 100
        # If their is bad contact score = 1000.
        
        if flag: # if any distance < cutoff : no scoring
            #self.score = min(9999999.9, 9999.9/mini)
            self.score = 1000.
            estat =  hbond = vdw = ds =  1000.
        else:
            self.score = min(self.scorer.get_score(),100.)
                
            estat = min(round(self.estat.get_score() * self.ESTAT_WEIGHT_AUTODOCK,2),1000.)
            hbond = min(round(self.hbond.get_score() * self.HBOND_WEIGHT_AUTODOCK,2),1000.)
            vdw   = min(round(self.vdw.get_score()   * self.VDW_WEIGHT_AUTODOCK,2),1000.)
            ds    = min(round(self.ds.get_score()    * self.DESOLV_WEIGHT_AUTODOCK,2),1000.)
            #print "--",estat,hbond,vdw,ds

        return (self.score,estat,hbond,vdw,ds)



from cAutoDock.AutoDockScorer import AutoDock305Scorer as c_AutoDock305Scorer
from cAutoDock.scorer import MolecularSystem as c_MolecularSystem 
from cAutoDock.scorer import updateCoords as c_updateCoords

class cADCalcAD3Energies(EnergyScorer):
    """For each atom in one AtomSet, determine the electrostatics eneregy vs all the atoms in a second
    AtomSet using the C implementation of the autodock scorer.
    When using the autodock3 scorer, the receptor need to be loaded as a pdbqs file, the ligand as pdbqt.
    """

    def __init__(self,atomset1,atomset2):

        
        EnergyScorer.__init__(self,atomset1,atomset2)
        self.weight = None
        self.weightLabel = None

        bothAts = atomset1 + atomset2
        self.ms = c_MolecularSystem()
        self.receptor= self.pyMolToCAtomVect(atomset1)
        self.ligand  = self.pyMolToCAtomVect(atomset2)
        self.r = self.ms.add_entities(self.receptor)
        self.l = self.ms.add_entities(self.ligand)
        self.ms.build_bonds( self.r )
        self.ms.build_bonds( self.l )

        self.scorer = c_AutoDock305Scorer(ms=self.ms,
                                          pyatomset1=atomset1,
                                          pyatomset2=atomset2)
        self.prop = self.scorer.prop

        # shared memory, used by C++ functions
        self.proteinLen = len(atomset1)
        self.ligLen = len(atomset2)
        self.msLen =  self.proteinLen + self.ligLen
        self.sharedMem = memobject.allocate_shared_mem([self.msLen, 3],
                                                       'SharedMemory', memobject.FLOAT)
        self.sharedMemPtr = memobject.return_share_mem_ptr('SharedMemory')[0]
        #print "Shared memory allocated.."


    def get_score(self):
        """ return the score """
        
        mini = self.ms.check_distance_cutoff(0, 1, self.cutoff)

        # when number return should not do get_score ( proteins too close)
        # flag = (mini==1.0 and mini==2.0)
        flag =  (mini == mini)

        # for each of the terms and the score, we cap their max value to 100
        # so if anything is greater than 100 we assign 100
        # If their is bad contact score = 1000.
        
        if flag: # if any distance < cutoff : no scoring
            #self.score = min(9999999.9, 9999.9/mini)
            self.score = 1000.
            estat =  hbond = vdw = ds =  1000.
        else:
            self.score = min(self.scorer.get_score(),100.)

            
            terms_score = self.scorer.get_score_per_term()
            estat = min(round(terms_score[0],2),1000.)
            hbond = min(round(terms_score[1],2),1000.)
            vdw   = min(round(terms_score[2],2),1000.)
            ds    = min(round(terms_score[3],2),1000.)
            #print "--",estat,hbond,vdw,ds

        # labels atoms
        score_array = self.scorer.get_score_array()
        self.scorer.labels_atoms_w_nrg(score_array)

        return (self.score,estat,hbond,vdw,ds)
        

#############################################################################################################
