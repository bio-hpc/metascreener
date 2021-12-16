########################################################################
#
# Date: 2012 Authors: Michel Sanner, Matt Danielson
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
# $Header: /opt/cvs/AutoDockFR/ADCscorer.py,v 1.32 2014/03/19 02:01:54 pradeep Exp $
#
# $Id: ADCscorer.py,v 1.32 2014/03/19 02:01:54 pradeep Exp $
#

#  Weights from AD4.1_bound.dat
FE_coeff_vdW_42		= 0.1662 # van der waals
FE_coeff_hbond_42	= 0.1209 # hydrogen bonding
FE_coeff_estat_42	= 0.1406 # electrostatics
FE_coeff_desolv_42	= 0.1322 # desolvation
FE_coeff_tors_42	= 0.2983 # torsional 

DEBUG = 0
VERBOSE = 0

import numpy
import sys, pdb
from MolKit.molecule import AtomSet
from AutoDockFR.ScoringFunction import ScoringFunction

# Try to import the cAutoDock package
from cAutoDock.scorer import CoordsVector, Coords, MolecularSystem,\
     isNAN, AtomVector, Atom, Coords, InternalEnergy

from cAutoDock._scorer import updateCoords

from memoryobject.memobject import return_share_mem_ptr, allocate_shared_mem, FLOAT
from cAutoDock.scorer import  Electrostatics, \
     HydrogenBonding, VanDerWaals, Desolvation4, WeightedMultiTerm

class NamedWeightedMultiTerm(WeightedMultiTerm):
    """
    subclass WeightedMultiTerm in order to keep track of scoring componet names

    """

    def __init__(self,*args):
        WeightedMultiTerm.__init__(self, *args)
        self.names = []

    def add_term(self, term, weight, name):
        self.names.append(name)
        WeightedMultiTerm.add_term(self, term, weight)


##
## there are 6 possible scorers to score interactions betweem a Ligand and a
## receptor that has a flexible and a rigid part
##
## let FR be the Flexible receptor part, RR the rigid receptor part and L the ligand
##
## each the these parts has interactions with itself:
##  L - L: internal energy of ligand    (1)
##  RR-RR: internal energy of Rigid-rec (2)
##  FR-FR: internal energy of Flex-rec  (3)
##
## in addition each of these parts can interact with the 2 other parts
##  L -FR: interaction energy between ligand-flex-rec    (4)
##  L -RR: interaction energy between ligand-rigid-rec   (5)
##  RR-FR: interaction energy between rigid-rec-flex-rec (6)
##
## for each of these 6 interactions we can build a molecular system and
## the associated scorer. By default all 6 scorers are created
##
## Any of these scorers can be suppressed by passing constructor options
## L_L, FR_FR, RR_RR, L_FR, L_RR, FR_RR to be False
##
## Sanity checks are perform to make sure that if a given scorer is required
## a set of atoms correspnds to this scorer (e.g. if FR_FR is True there needs
## to be a set of moving receptor atoms
##
        
class AD42ScoreC(ScoringFunction): 


    def createMolecularSystem(self):
        return MolecularSystem()


    def __init__(self, rigidRecAtoms, ligAtoms, ligandTorTree, TORSDOF,
                 flexRecAtoms=None, interfaceAtoms=None,
                 cutoff=1.0, RR_L=True, FR_L=True, L_L=True, RR_RR=True, RR_FR=True, FR_FR=True,
                 RR_L_Fitness=True, FR_L_Fitness=True, L_L_Fitness=True, RR_RR_Fitness=True, 
                 RR_FR_Fitness=True, FR_FR_Fitness=True, gridScorer=None, include_1_4_interactions=True):
    
#    def __init__(self, rigidRecAtoms, ligAtoms, ligandTorTree, TORSDOF, flexRecAtoms=None,
#                 calcLigIE=True, calcRecIE=False, ReceptorIE=None, cutoff=1.0):

        """
        cutoff: non-bonded distance cutoff b/t prot-lig
                if any distance < this cutoff, complex wont be scored.
                Useful defaults: the H-H covalent bond length is 0.76A
        """
        # Initialize the parent class
        ScoringFunction.__init__(self)

        self.TORSDOF = TORSDOF # Total number of rotatable bonds in the ligand.  Used for Torsional scoring term
        self.ligAtoms = ligAtoms  # ligand atom set
        self.rigidRecAtoms = rigidRecAtoms # rigid receptor atom set
        self.flexRecAtoms = flexRecAtoms # flexible receptor atom set            
        self.interfaceAtoms = interfaceAtoms # CA and CB of flexible residues
        if interfaceAtoms:
            self.interfaceCoords = interfaceAtoms.coords
            
        # grid maps are computed without side chain plus CA removed for flexible residues
        # when we use grid maps
        #    FR-L scorer interface atoms should be included in the list of receptor atoms
        #    FR-FR scorer interface atoms should be included in the list of receptor atoms
        #    FR-RR scorer interface atoms should NOT be included in the list of receptor atoms
        #          because they would be 1-2 an 1-3 interactions
        # when using pairwise scorers, we also include CA and CB in FR for FR-L and FR-FR but not
        # for FR-RR
        
        self.interfaceAtoms = interfaceAtoms # CA and CB atoms of flexible residues
        
        self.ligandTorTree = ligandTorTree # ligand torsional tree
        self.gridScorer = None
        self.cutoff = cutoff # Cutoff used to check for clashes between molecular systems
        self.RR_L = RR_L   # Create Rigid-Rec - Ligand Molecular system
        self.FR_L = FR_L   # Create Flex-Rec - Ligand Molecular system
        self.L_L = L_L     # Create Ligand - Ligand Molecular system
        self.RR_RR = RR_RR # Create Rigid-Rec - Rigid-Rec Molecular system
        self.RR_FR = RR_FR # Create Rigid-Rec - Flex-Rec Molecular system
        self.FR_FR = FR_FR # Create Flex-Rec - Flex-Rec Molecular system
        self.RR_L_Fitness = RR_L_Fitness   # Include Rigid-Rec - Ligand score in GA Fitness
        self.FR_L_Fitness = FR_L_Fitness   # Include Flex-Rec - Ligand score in GA Fitness
        self.L_L_Fitness = L_L_Fitness     # Include Ligand - Ligand score in GA Fitness
        self.RR_RR_Fitness = RR_RR_Fitness # Include Rigid-Rec - Rigid-Rec score in GA Fitness
        self.RR_FR_Fitness = RR_FR_Fitness # Include Rigid-Rec - Flex-Rec score in GA Fitness
        self.FR_FR_Fitness = FR_FR_Fitness # Include Flex-Rec - Flex-Rec score in GA Fitness


        self.bestScore = -1e9 # variable to store the best score
        self.RRLmolSyst =  None # this will be RigidReceptor-Ligand molecular system
        self.FRLmolSyst =  None # this will be FlexRec-Ligand molecular system
        self.LLmolSyst =  None # this will be Ligand-Ligand molecular system
        self.FRFRmolSyst =  None # this will be FlexReceptor-FlexReceptor molecular system
        self.RRFRmolSyst =  None # this will be RigidReceptor-FlexReceptor molecular system
        self.RRRRmolSyst =  None # this will be RigidReceptor-RigidReceptor molecular system
        self.include_1_4_interactions = include_1_4_interactions
	self.scoreBreakdown = {}
        
        # Initial sanity check on the scorer
        if ((FR_L or RR_FR or FR_FR) and (FR_L_Fitness or RR_FR_Fitness or FR_FR_Fitness)) and flexRecAtoms == None:
            print 'ERROR: can not calculate flexible receptor energy without specifing flexible atoms in receptor'
            sys.exit(1)


        # define function from cAutoDock that knows how to update the coordinates
        #self.updateCoords = updateCoords

        # create vectors of cAutodock.Atoms for the 3 sets of atoms
        #rigidRecCatoms = self.pyMolToCAtomVect(self.rigidRecAtoms)
        #ligandCatoms  = self.pyMolToCAtomVect(self.ligAtoms)
        #ligandCatoms2 = self.pyMolToCAtomVect(self.ligAtoms)
        #if flexRecAtoms:
        #    flexRecCatoms = self.pyMolToCAtomVect(self.flexRecAtoms)
        #else:
        #    flexRecCatoms = None

        # Create scorer for Protein-Ligand interaction energy 
        self.createProtLigScorer(
            self.rigidRecAtoms, self.ligAtoms, self.flexRecAtoms, self.interfaceAtoms,
            self.RR_L, self.FR_L, gridScorer)

        # Create scorer for Ligand Internal Energy
        if self.L_L:    
            self.createLigLigScorer(self.ligAtoms, self.L_L)

        # Receptor Internal Energy Calculation
        if self.RR_RR or self.RR_FR or self.FR_FR:
            self.createRecRecScorer(
                self.rigidRecAtoms, self.flexRecAtoms, self.interfaceAtoms,
                self.RR_RR, self.RR_FR, self.FR_FR)     
                

                
    def createProtLigScorer(self, rigidRecAtoms, ligAtoms, flexRecAtoms, interfaceAtoms,
                            RR_L, FR_L, gridScorer):
        """
        None <- createProtLigScorer(rigidRecCatoms, ligCAtoms, flexRecCatoms, interfaceAtoms, RR_L, FR_L, gridScorer)

        rigidRecAtoms - molkit atomset for rigid receptor atoms
        ligAtoms - molkit atomset for  ligand atoms
        flexRecAtoms - molkit atomset for receptor atoms that move (can be None)
        interfaceAtoms - CA and CB atoms of flexible residues
	RR_L - True/False flag to control building the RigidRec-Ligand scorer
	FR_L - True/False flag to control building the FlexRec-Ligand IE scorer
        gridScorer - AutoDock gripmaps-based scorer
        
        this method will create 1 or 2 molecular systems and the corresponding
        scorers:
             1: rigid receptor-ligand
             2: flexible receptor-ligand (ONLY if flexRecAtoms is not None)
        """

        # This scorer RR_L should always be on
        if RR_L:
            if gridScorer is not None:
                self.gridScorer = gridScorer
            else:
                # create a molecular system and the associated scorer for rigid recptor-ligand
                molSyst = self.addMolecularSystem('rigid receptor-ligand',
                                              internal=False)
                self.RRLmolSyst = molSyst
                # create vectors of cAutodock.Atoms
                rigidRecCatoms = self.pyMolToCAtomVect(rigidRecAtoms)
                ligCatoms  = self.pyMolToCAtomVect(ligAtoms)
                # add the receptor atoms as first entity and ligand as second
                msEntity1 = molSyst.add_entities(rigidRecCatoms)
                msEntity2 = molSyst.add_entities(ligCatoms)
                molSyst.atomSetIndices = {'set1':msEntity1, 'set2':msEntity2}

                # terms to add to the NamedWeightedMultiTerm scorer
                estat = Electrostatics(molSyst)
                hBond = HydrogenBonding(molSyst)
                vdw = VanDerWaals(molSyst)
                #vdw.set_ad_version("4.0")	# force ad version to 4.0
                #print '1:USING force field version', vdw.get_ad_version()
                ds = Desolvation4(molSyst)            

                # build a NamedWeightedMultiTerm scorer for this molecular system
                RRLscorer = NamedWeightedMultiTerm(molSyst)
                RRLscorer.add_term(estat, FE_coeff_estat_42, 'electrostatics')
                RRLscorer.add_term(hBond, FE_coeff_hbond_42, 'hBonds')
                RRLscorer.add_term(vdw,   FE_coeff_vdW_42, 'vdw')
                RRLscorer.add_term(ds,    FE_coeff_desolv_42, 'ds')

                # put the scorer inside the molecualr system
                molSyst.scorer = RRLscorer

                # keep a reference to the terms to avoid them from being garbage collected
                molSyst.terms = [vdw, estat, hBond, ds]

                msLen =  len(rigidRecCatoms) + len(ligCatoms)
                # allocate shared memory for this scorer
                # shared memory, used by C++ functions
                #  | rigid receptor atoms | ligand atoms | 
                #  ^---begin              ^--- MemSplit  ^---end
                RRLscorer.sharedMem = allocate_shared_mem([msLen, 3],'RRLSharedMemory', FLOAT)
                RRLscorer.sharedMemPtr = return_share_mem_ptr('RRLSharedMemory')[0]
                RRLscorer.sharedMemLen = msLen
                lrigid = len(rigidRecCatoms)
                RRLscorer.sharedMemSplit = lrigid

                # Rigid atom coords never change: copy them into the shared mem here once
                # saves time in the score() function below
                if lrigid:
                    RRLscorer.sharedMem[:lrigid] = numpy.array(self.rigidRecAtoms.coords,'f')

                # The bonds have to be computed AFTER the pairwaise scorers are created
                # else the bond list in C++ is corrupted
                molSyst.build_bonds(msEntity1)
                molSyst.build_bonds(msEntity2)
        
        ### Flexible receptor atoms ### 
        if FR_L and flexRecAtoms:
            # create a molecular system and the associated scorer for FlexRecptor-ligand
            molSyst = self.addMolecularSystem('flexible receptor-ligand',
                                              internal=False)
            self.FRLmolSyst = molSyst
            # create vectors of cAutodock.Atoms
            flexRecCatoms = self.pyMolToCAtomVect(flexRecAtoms+interfaceAtoms)
            ligCatoms  = self.pyMolToCAtomVect(ligAtoms)
            # add the receptor atoms as first entity and ligand as second
	    msEntity1 = molSyst.add_entities(flexRecCatoms)
	    msEntity2 = molSyst.add_entities(ligCatoms)
	    molSyst.atomSetIndices = {'set1':msEntity1, 'set2':msEntity2}

            # terms to add to the NamedWeightedMultiTerm scorer
            estat = Electrostatics(molSyst)
            hBond = HydrogenBonding(molSyst)
            vdw = VanDerWaals(molSyst)
            ds = Desolvation4(molSyst)            

            # build a NamedWeightedMultiTerm scorer for this molecular system
            FRLscorer = NamedWeightedMultiTerm(molSyst)
            FRLscorer.add_term(estat, FE_coeff_estat_42, 'electrostatics')
            FRLscorer.add_term(hBond, FE_coeff_hbond_42, 'hBonds')
            FRLscorer.add_term(vdw,   FE_coeff_vdW_42, 'vdw')
            FRLscorer.add_term(ds,    FE_coeff_desolv_42, 'ds')

            # put the scorer inside the molecualr system
            self.FRLmolSyst.scorer = FRLscorer

            # keep a reference to the terms to avoid them from being garbage collected
            molSyst.terms = [vdw, estat, hBond, ds]

            msLen = len(flexRecCatoms) + len(ligCatoms)
            # allocate shared memory for this scorer
            #  | flex receptor atoms | ligand atoms | 
            #  ^---begin             ^--- MemSplit  ^---end
            FRLscorer.sharedMem = allocate_shared_mem([msLen, 3],'FRLSharedMemory', FLOAT)
            FRLscorer.sharedMemPtr = return_share_mem_ptr('FRLSharedMemory')[0]
            FRLscorer.sharedMemLen = msLen
            FRLscorer.sharedMemSplit = len(flexRecCatoms)

            # The bonds have to be computed AFTER the pairwaise scorers are created
            # else the bond list in C++ is corrupted
	    molSyst.build_bonds(msEntity1)
	    molSyst.build_bonds(msEntity2)


    def createLigLigScorer(self, ligAtoms, L_L):
        """
        None <- createLigLigScorer(ligCAtoms, ligandCAtoms2)

	ligAtoms - molkit atomset for ligand atoms       
	L_L - True/False flag to control building the Ligand IE scorer
        
        this method will create molecular system and the coreponding scorer:
            1: ligand-ligand
        """
        
        # This scorer should always be on
        if L_L:
            ## create a molecular system and the associate scorer for ligand-ligand
            molSyst = self.addMolecularSystem('ligand-ligand',
                                              internal=True)
            self.LLmolSyst = molSyst
            # create vectors of cAutodock.Atoms
            ligCatoms  = self.pyMolToCAtomVect(ligAtoms)
            ligCatoms2  = self.pyMolToCAtomVect(ligAtoms)
            # add the ligand atoms as first entity and ligand as second
            msEntity1 = molSyst.add_entities(ligCatoms)
	    ## we do not build the bonds in the C-code because they are only used
	    ## to mask bonded interactions and the code is has too many interactions (extra 1-4).
	    ##
	    ## we wrote getBondedInteractions(atoms) to mask out the  1-1, 1-2, 1-3 and 1-4 interactions
	    ## properly for sets of atoms
            msEntity2 = molSyst.add_entities(ligCatoms2)
	    molSyst.atomSetIndices = {'set1':msEntity1, 'set2':msEntity2}

            # terms to add to the NamedWeightedMultiTerm scorer
            vdw = VanDerWaals(molSyst)
            estat = Electrostatics(molSyst)
            hBond = HydrogenBonding(molSyst)
            ds = Desolvation4(molSyst)

            ## Allocate the mask and set all entries to 1 (i.e. valid interaction to be scored)
            molSyst.set_use_mask(1) # 1 for True

	    ## now get a list of bonded interactions and mask them
	    # mask the 1-1, 1-2, 1-3 and 1-4 interactions
	    bondedInter = self.getBondedInteractions(ligAtoms, self.ligandTorTree)
            #import pdb
            #pdb.set_trace()

            ## bondedInter.remove( (0,5))
            ## bondedInter.remove( (1,8))
            ## bondedInter.remove( (1,10))
            ## bondedInter.remove( (1,11))
            ## bondedInter.remove( (2,7))
            ## bondedInter.remove( (2,9))
            ## bondedInter.remove( (3,7))
            ## bondedInter.remove( (3,9))
            ## bondedInter.remove( (4,7))
            ## bondedInter.remove( (4,9))
            ## bondedInter.remove( (5,0))
            ## bondedInter.remove( (8,1))
            ## bondedInter.remove( (10,1))
            ## bondedInter.remove( (11,1))
            ## bondedInter.remove( (7,2))
            ## bondedInter.remove( (9,2))
            ## bondedInter.remove( (7,3))
            ## bondedInter.remove( (9,3))
            ## bondedInter.remove( (7,4))
            ## bondedInter.remove( (9,4))
            #import pdb
            #pdb.set_trace()
            
	    for i,j in bondedInter:
	        molSyst.set_mask( i, j, 0) # 0 means this interactions is ignored

            ## mask the 1-1, 1-2, 1-3, & 1-4 interactions
            ## this was done automatically by InternalEnergy(molSyst) in the C++
            ## code. Since we switched to NamedWeightedMultiTerm we have to call 
            ## this functin explicitly
            ##
            ## MLD: NO LONGER USED due to getBondedInteractions call above
            #MLDmolSyst.compute_bonded_matrix(msEntity1)


            ## the C++ code masks 1-1, 1-2, 1-3, & 1-4 interactions but does not mask 
            ## non-bonded interactions between rigid bodies (known as weed bonds in AutoDock).
            ## First find out Non-bonded interactions that need to be removed:
            removed = self.weedBonds(self.ligandTorTree)
            ## set the mask for these interactions
            ## k is a string 'a-b' and values is a tuple (a,b) where a and b are atom indices
            ## NOTE: removed contains both (a,b) and (b,a)
            for k, value in removed.items():
                i, j = value
                molSyst.set_mask( i, j, 0)


            # build a NamedWeightedMultiTerm scorer for this molecular system
            LLscorer = NamedWeightedMultiTerm(molSyst)
            # setting the term to symmetric only calcuates the score for half the matrix.
            # still assigns a score in (i,j) and (j,i).  Therefore, score/2.0 is needed.
            vdw.set_symmetric(True)
            #hBond.set_symmetric(False)
            hBond.set_directional(False)
            hBond.set_NA_HDfactor(False)
            estat.set_symmetric(True)
            ds.set_symmetric(True)
            LLscorer.add_term(estat, FE_coeff_estat_42, 'electrostatics')
            LLscorer.add_term(hBond, FE_coeff_hbond_42, 'hBonds')
            LLscorer.add_term(vdw,   FE_coeff_vdW_42, 'vdw')
            LLscorer.add_term(ds,    FE_coeff_desolv_42, 'ds')

            # put the scorer inside the molecualr system
            self.LLmolSyst.scorer = LLscorer

            # keep a reference to the terms to avoid them from being garbage collected
            molSyst.terms = [vdw, estat, hBond, ds]

            msLen =  2 * len(ligCatoms)
            # allocate shared memory for this scorer
            #  | ligand atoms | ligand atoms | 
            #  ^---begin      ^--- MemSplit  ^---end
            LLscorer.sharedMem = allocate_shared_mem([msLen, 3],'LLSharedMemory', FLOAT)
            LLscorer.sharedMemPtr = return_share_mem_ptr('LLSharedMemory')[0]
            LLscorer.sharedMemLen = msLen
            LLscorer.sharedMemSplit = len(ligCatoms)

            # The bonds have to be computed AFTER the pairwaise scorers are created
            # else the bond list in C++ is corrupted
            molSyst.build_bonds(msEntity1)
            molSyst.build_bonds(msEntity2)


    def createRecRecScorer(self, rigidRecAtoms, flexRecAtoms, interfaceAtoms, RR_RR, RR_FR, FR_FR):
        """
        None <- createRecRecScorer(rigidRecAtoms, flexRecAtoms, interfaceAtoms, RR_RR, RR_FR, FR_FR)

        rigidRecAtoms - python atom set for for rigid receptor atoms
        flexRecAtoms - python atom set for receptor atoms that move (can be None)
        interfaceAtoms = CA and CB atoms of flexible Residues
	RR_RR - True/False flag to control building the rigidRec-rigidRec IE scorer
	RR_FR - True/False flag to control building the rigidRec- flexRec interaction scorer
	FR_FR - True/False flag to control building the flexRec-flexRec IE scorer
        """

	if FR_FR:
            ###########################################
            # 1: Internal energy among flexible atoms #
            ###########################################
            ## create a molecular system and the associate scorer for FlexRec-FlexRec
            molSyst = self.addMolecularSystem('FlexReceptor-FlexReceptor',
                                          internal=True)
            self.FRFRmolSyst = molSyst
            # create vectors of cAutodock.Atoms
	    flexRecCatoms = self.pyMolToCAtomVect(flexRecAtoms+interfaceAtoms)
	    flexRecCatoms2 = self.pyMolToCAtomVect(flexRecAtoms+interfaceAtoms)
            # add the flexible receptor atoms to MolecularSystem
            msentity1 = molSyst.add_entities(flexRecCatoms)
            ## we do not build the bonds in the C-code because they are only used
            ## to mask bonded interactions and the code if failing on molSyst.compute_bonded_matrix.
            ## In addition, the bonds created in the C code are missing bonds between rigid and flexible
            ## atoms in the receptor. The C approach also required including interface atoms such as Cb
            ## in order to get the right list of 1-3 and 1-4 interactions masked out in the flexible
            ## receptor (for instance  THR & SER: the gamma-Oxygen would be a broken piece if CB is not
            ## included.
            ##
            ## we wrote getBondedInteractions(atoms) to mask out the  1-1, 1-2, 1-3 and 1-4 interactions
            ## properly for sets of atoms
            msentity2 = molSyst.add_entities(flexRecCatoms2)
	    molSyst.atomSetIndices = {'set1':msentity1, 'set2':msentity2}
          
            ## first allocate the mask and set all entries to 1 (i.e. all valid interaction)
            molSyst.set_use_mask(1) 

            ## now get a list of bonded interactions and mask them
            # mask the 1-1, 1-2, 1-3 and 1-4 interactions
            bondedInter = self.getBondedInteractions(flexRecAtoms+interfaceAtoms,
                                                     )
            for i,j in bondedInter:
                molSyst.set_mask( i, j, 0) # 0 means this interactions is ignored

	    #mask = molSyst.get_mask()
	    #print 'AAAAAAAAAAAAA', mask[0]

            # This code was used when the C code was building the bonds and the interfacce
            # atoms were added to the moving atoms (e.g. the CB on rotameric side chains)
            #assert molSyst.ignore_interface(msentity1) # set mask to 0 for interactions between ?
            #assert molSyst.ignore_interface(msentity2)
	    #mask = molSyst.get_mask()
	    #print 'AAAAAAABBBBBB', mask[0]

            # terms to add to the NamedWeightedMultiTerm scorer
            estat = Electrostatics(molSyst)
            hBond = HydrogenBonding(molSyst)
            vdw = VanDerWaals(molSyst)
            # force ad version to 4.0
            vdw.set_ad_version("4.0")
            ds = Desolvation4(molSyst)        

            # build a NamedWeightedMultiTerm scorer for this molecular system
            FRFRscorer = NamedWeightedMultiTerm(molSyst)
            vdw.set_symmetric(True)
            #hBond.set_symmetric(True)
            hBond.set_directional(False)
            hBond.set_NA_HDfactor(False)
            estat.set_symmetric(True)
            ds.set_symmetric(True)
            FRFRscorer.add_term(estat, FE_coeff_estat_42, 'electrostatics')
            FRFRscorer.add_term(hBond, FE_coeff_hbond_42, 'hBonds')
            # force H-bonding to be non-directional
            #MLD: do we need to do this?
            #FRFRscorer.set_directional(0)
            FRFRscorer.add_term(vdw,   FE_coeff_vdW_42, 'vdw')
            #MLD: DS was not present in the old 3.05 code                
            #FRFRscorer.add_term(ds,    FE_coeff_desolv_42, 'ds')

            # put the scorer inside the molecualr system
            self.FRFRmolSyst.scorer = FRFRscorer

            # keep a reference to the terms to avoid them from being garbage collected
            molSyst.terms = [vdw, estat, hBond, ds]

            msLen = 2 * len(flexRecCatoms)
            # allocate shared memory for this scorer
            #  | flex receptor atoms | flex receptor atoms | 
            #  ^---begin             ^--- MemSplit         ^---end
            FRFRscorer.sharedMem = allocate_shared_mem([msLen, 3],'FRFRSharedMemory', FLOAT)
            FRFRscorer.sharedMemPtr = return_share_mem_ptr('FRFRSharedMemory')[0]
            FRFRscorer.sharedMemLen = msLen
            FRFRscorer.sharedMemSplit = len(flexRecCatoms)

            # The bonds have to be computed AFTER the pairwaise scorers are created
            # else the bond list in C++ is corrupted
            molSyst.build_bonds(msentity1)
            molSyst.build_bonds(msentity2)

	if RR_FR:
            ##################################################
            # 2 : E between Rigid & Flex domains in receptor #
            ##################################################
            ## create a molecular system and the associate scorer for FlexRec-FlexRec
            molSyst = self.addMolecularSystem('RigidReceptor-FlexReceptor',
                                          internal=False)
            self.RRFRmolSyst = molSyst
            # create vectors of cAutodock.Atoms
	    rigidRecCatoms = self.pyMolToCAtomVect(rigidRecAtoms)
	    flexRecCatoms = self.pyMolToCAtomVect(flexRecAtoms)
            # add the rigid & flex receptor atoms to MolecularSystem
            msentity1 = molSyst.add_entities(rigidRecCatoms)
            msentity2 = molSyst.add_entities(flexRecCatoms)
	    molSyst.atomSetIndices = {'set1':msentity1, 'set2':msentity2}

            ## first allocate the mask and set all entries to 1 (i.e. all valid interaction)
            molSyst.set_use_mask(1) # 1 for True 

            # ignore the bonds between moving and fixed domains
            # as well as 1-3 and 1-4 interactions across interface between
            # rigid and moving
            molSyst.ignore_recptor_ligand_bonds(True)

            # terms to add to the NamedWeightedMultiTerm scorer
            estat = Electrostatics(molSyst)
            hBond = HydrogenBonding(molSyst)
            vdw = VanDerWaals(molSyst)
            # force ad version to 4.0
            vdw.set_ad_version("4.0")
            #ds = Desolvation4(molSyst)        

            # build a NamedWeightedMultiTerm scorer for this molecular system
            RRFRscorer = NamedWeightedMultiTerm(molSyst)
            RRFRscorer.add_term(estat, FE_coeff_estat_42, 'electrostatics')
            RRFRscorer.add_term(hBond, FE_coeff_hbond_42, 'hBonds')
            # force H-bonding to be non-directional
            #MLD: do we need to do this?
            #FRFRscorer.set_directional(0)
            RRFRscorer.add_term(vdw,   FE_coeff_vdW_42, 'vdw')
            #MLD: DS was not present in the old 3.05 code                
            #RRFRscorer.add_term(ds,    FE_coeff_desolv_42, 'ds')

            # put the scorer inside the molecualr system
            self.RRFRmolSyst.scorer = RRFRscorer

            # keep a reference to the terms to avoid them from being garbage collected
            #molSyst.terms = [vdw, estat, hBond, ds]
            molSyst.terms = [vdw, estat, hBond]

            msLen = len(rigidRecCatoms) + len(flexRecCatoms)
            # allocate shared memory for this scorer
            #  | rigid receptor atoms | flex receptor atoms | 
            #  ^---begin              ^--- MemSplit         ^---end
            RRFRscorer.sharedMem = allocate_shared_mem([msLen, 3],'RRFRSharedMemory', FLOAT)
            RRFRscorer.sharedMemPtr = return_share_mem_ptr('RRFRSharedMemory')[0]
            RRFRscorer.sharedMemLen = msLen
            RRFRscorer.sharedMemSplit = len(rigidRecCatoms)

            # The bonds have to be computed AFTER the pairwaise scorers are created
            # else the bond list in C++ is corrupted
            molSyst.build_bonds(msentity1)
            molSyst.build_bonds(msentity2)


	if RR_RR:
            ######################################
            # 3 : IE of Rigid domain in receptor #
            ######################################
            ## create a molecular system and the associate scorer for Rigid-Rigid
            molSyst = self.addMolecularSystem('RigidReceptor-RigidReceptor',
                                          internal=True)
            self.RRRRmolSyst = molSyst
            # create vectors of cAutodock.Atoms
	    rigidRecCatoms = self.pyMolToCAtomVect(rigidRecAtoms)
	    rigidRecCatoms2 = self.pyMolToCAtomVect(rigidRecAtoms)
            # add the rigid rec atoms as first & second entity
            msentity1 = molSyst.add_entities(rigidRecCatoms)
            msentity2 = molSyst.add_entities(rigidRecCatoms2)
	    molSyst.atomSetIndices = {'set1':msentity1, 'set2':msentity2}

            ## first allocate the mask and set all entries to 1 (i.e. all valid interaction)
            molSyst.set_use_mask(1) # 1 for True

            # terms to add to the NamedWeightedMultiTerm scorer
            vdw = VanDerWaals(molSyst)
            # force ad version to 4.0
            vdw.set_ad_version("4.0")
            estat = Electrostatics(molSyst)
            hBond = HydrogenBonding(molSyst)
            #ds = Desolvation4(molSyst)

            ## now get a list of bonded interactions and mask them
            # mask the 1-1, 1-2, 1-3 and 1-4 interactions
            bondedInter = self.getBondedInteractions(rigidRecAtoms)
            for i,j in bondedInter:
                molSyst.set_mask( i, j, 0) # 0 means this interactions is ignored


            ## mask the 1-1, 1-2, 1-3 and 1-4 interactions
            ## this was done automatically by InternalEnergy(molSyst) in 
            ## the C++ code but since
            ## we switched to NamedWeightedMultiTerm we have to call 
            ## this functin explicitly
            ## MLD:deprecated molSyst.compute_bonded_matrix(0)


            # build a NamedWeightedMultiTerm scorer for this molecular system
            RRRRscorer = NamedWeightedMultiTerm(molSyst)
            vdw.set_symmetric(True)
            hBond.set_symmetric(True)
            # force H-bonding to be non-directional
            #hBond.set_directional(0)
            estat.set_symmetric(True)
            #ds.set_symmetric(True)
            RRRRscorer.add_term(estat, FE_coeff_estat_42, 'electrostatics')
            RRRRscorer.add_term(hBond, FE_coeff_hbond_42, 'hBonds')
            RRRRscorer.add_term(vdw,   FE_coeff_vdW_42, 'vdw')
            #RRRRscorer.add_term(ds,    FE_coeff_desolv_42, 'ds')

            # put the scorer inside the molecualr system
            self.RRRRmolSyst.scorer = RRRRscorer

            # keep a reference to the terms to avoid them from being garbage collected
            molSyst.terms = [vdw, estat, hBond]

            msLen =  2 * len(rigidRecCatoms)
            # allocate shared memory for this scorer
            #  | rigid receptor atoms | rigid receptor atoms | 
            #  ^---begin              ^--- MemSplit          ^---end
            RRRRscorer.sharedMem = allocate_shared_mem([msLen, 3],'RRRRSharedMemory', FLOAT)
            RRRRscorer.sharedMemPtr = return_share_mem_ptr('RRRRSharedMemory')[0]
            RRRRscorer.sharedMemLen = msLen
            RRRRscorer.sharedMemSplit = len(rigidRecCatoms)

            # The bonds have to be computed AFTER the pairwaise scorers are created
            # else the bond list in C++ is corrupted
            molSyst.build_bonds(msentity1)
            molSyst.build_bonds(msentity2)


    def pyMolToCAtomVect(self, mol):
        """
        pyAtomVect <- pyMolToCAtomVect()

        convert Protein or AtomSet to AtomVector
        """

        className = mol.__class__.__name__
        if className == 'Protein':
            pyAtoms = mol.getAtoms()
        elif className == 'AtomSet':
            pyAtoms = mol
        else:
            print 'Warning: Need a AtomSet or Protein'
            raise ValueError
            return None
        pyAtomVect = AtomVector()

        confNB = pyAtoms[0].conformation
        pyAtoms.setConformation(0)
        for atm in pyAtoms:
            a = Atom()
            a.set_name(atm.full_name())
            #if atm.autodock_element == "Cl":
            #    print "Error: Cl should be c, as autodock_element"
            #    raise ValueError
            #if atm.autodock_element == "Br":
            #    print "Error: Br should be b, as autodock_element"
            #    raise ValueError                
            a.set_element(atm.autodock_element)# aromatic type 'A', vs 'C'
            coords = atm.coords
            a.set_coords( Coords(coords[0],coords[1],coords[2]))
            a.set_charge( atm.charge)
            if hasattr(atm, 'AtVol'):
                a.set_atvol( atm.AtVol)

            if hasattr(atm, 'AtSolPar'):
                a.set_atsolpar( atm.AtSolPar)

            if hasattr(atm, 'atInterface'): # an interface atom?
                a.set_atInterface(atm.atInterface)

            a.set_bond_ord_rad( atm.bondOrderRadius)
            a.set_atom_type( atm.autodock_element) # this is used for DS & setting vdw correctly in cAutoDockDist code
            #a.set_charge( atm.charge)
            pyAtomVect.append(a)

        if confNB != 0:
            pyAtoms.setConformation(confNB)

        return pyAtomVect


    def weedBonds(self, tree):
        """
        removed <- weedBonds(tree)

        tree - ligandTorTree

        the 1-3 and 1-4 intearctions have already been masked by the C++ code
        when the Molecular System was built. Here we identify non bonded interactions
        between rigid bodies and we mask them.  
        """
        
        # the keys of this dict are '%d-%d' where the 2 numbers are atom indices
        # the value is a tuple containign these 2 numbers
        self.removedPairs = {}

        # define a recursive function that will walk the tree
        # and remove add to removedPairs all pairs of atoms
        # located in the same rigid body (i.e. node in the troTree)
        # as well as any inteaction between atoms in the node and
        # the 2 atoms of the bond traversed to reach this node

        def _handleRigidBody(node):
            atomList = node.atomList#FT
            if node.bond[0] is not None:
                atomList.append(node.bond[0])
            if node.bond[1] is not None:
                atomList.append(node.bond[1])
            for ai in atomList:
                for bi in atomList:
                    key = '%d-%d'%(ai,bi)
                    self.removedPairs[key] = (ai,bi)
                    key = '%d-%d'%(bi,ai)
                    self.removedPairs[key] = (bi,ai)
            for c in node.children:
                _handleRigidBody(c)

        # call recursive fucntion to populate self.removedPairs
        _handleRigidBody(tree.rootNode)

        removed = self.removedPairs
        del self.removedPairs
        return removed


    def getBondedInteractions(self, atoms, tree=None):
        # build a list of 0-based indices of bonded interactions
        # 1-1, 1-2, 1-3, 1-4
        # bonds might point to atoms not in the set. but a 1-3 interaction
        # between atoms in the set can me mediated through an atom outside
        # the set. hence we can not stop when the bonded atom is outside the set
        # but we on only add pairs where both atoms in the pair belong to the set

        #MLD_8_16_12: Turning this off for single atom energy analysis
	#assert len(atoms.bonds[0]) > 0, "ERROR: atoms in molecule %s have no bonds"%atoms[0].top.name
        interactions = []

        if tree:
            # tage rotatable bonds
            bonds, noBonds = atoms.bonds
            bonds._rotatable = False

            def _traverse(atoms, node):
                if node.bond[0] is not None:
                    a1 = atoms[node.bond[0]]
                    a2 = atoms[node.bond[1]]
                    for b in a1.bonds:
                        if b.atom1==a2 or b.atom2==a2:
                            b._rotatable = True
                for c in node.children:
                    _traverse(atoms, c)

            _traverse(atoms, tree.rootNode)
        
        ## create a sequential number
        atoms.uniqInterNum = range(len(atoms))
        ## outer loop over atoms
        for a in atoms:
            # loop over the bonds of a
            n1 = a.uniqInterNum
            interactions.append( (n1,n1) ) # 1-1

            ## loop over atoms bonded to a
            for b in a.bonds:
                # find a2 which is bonded to a through b
                a2 = b.atom1
                if a2==a: a2=b.atom2
                if hasattr(a2, 'uniqInterNum'):
                    # only exlude pair if both atoms are in the set atoms
                    interactions.append( (n1,a2.uniqInterNum) ) # 1-2

                ## loop over bonds of at2 to find 1-3 interactions
                for b1 in a2.bonds:
                    # find a2 which is bonded to a2 through b1
                    a3 = b1.atom1
                    if a3==a2: a3=b1.atom2
                    if a3 == a : continue
                    if hasattr(a3, 'uniqInterNum'):
                        interactions.append( (n1,a3.uniqInterNum) ) # 1-3
                    
                    ## loop over bonds of at3 to find 1-3 interactions
                    if (self.include_1_4_interactions == True):
                        # we only remove the 1-4 if a2-a3 bond is not rotatable
                        if tree is None or not b1._rotatable:
                            for b2 in a3.bonds:
                                # find a4 which is bonded to a3 through b2
                                a4 = b2.atom1
                                if a4==a3: a4=b2.atom2
                                if a4 == a2 : continue
                                if hasattr(a4, 'uniqInterNum'):
                                    interactions.append( (n1,a4.uniqInterNum) ) # 1-4

                    else: # 1-4 interaction have to be removed, so we append them to the list
                        for b2 in a3.bonds:
                            # find a4 which is bonded to a3 through b2
                            a4 = b2.atom1
                            if a4==a3: a4=b2.atom2
                            if a4 == a2 : continue
                            if hasattr(a4, 'uniqInterNum'):
                                interactions.append( (n1,a4.uniqInterNum) ) # 1-4


        for a in atoms:
            del a.uniqInterNum
            
        return interactions


    def LigandIE(self, L_coords):
        ############################
        ## Ligand Internal energy ##
        ############################
        if self.LLmolSyst and self.L_L_Fitness:
            scorer = self.LLmolSyst.scorer
            #  memory of LLmolSyst
            #  | ligand atoms | ligand atoms | 
            #  ^---begin      ^--- MemSplit  ^---end
            # Copy the ligand coordinates into the shared memory
            scorer.sharedMem[:] = numpy.array(L_coords+L_coords , 'f')
            updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.LLmolSyst,\
                         scorer.sharedMemPtr)

            # if distances are > cutoff, NAN is return.
            # else: the offending distance is returned. 
	    # The distance matrice might only be partially populated as we 
	    # break out as soon as a distance smaller than cutoff is seen. 
	    # Scoring should not occur in this case as the clash is too severe
            mini = self.LLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
            nan = isNAN(mini)
            if not nan:
                if DEBUG:
                    print "Not scoring because Flexible receptor - ligand clash =", mini
                scoreLL = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
	        # Return a large negative value (not favorable interaction)
	        # This is due to the GA fitness/performance looking for a maximum
                return 0.0 - scoreLL
            else:
                # Get the score of Prot-ligand interaction
                scoreLL = scorer.get_score() * self.LLmolSyst.factor
            return scoreLL


    def score(self, RR_coords, FR_coords, L_coords,
              RR_L=True, FR_L=True, L_L=True, 
              RR_RR=True, RR_FR=True, FR_FR=True):

        # returns fitness_score, score where fiteness_score is the part of the score used
        # to calculate the fitness in the GA and score is all terms
        # Only Receptor-Ligand interactions are used for fitness.
        # The internal energy fo the flexible parts is onyl computed to avoid them from
        # collapsing onto themselves in order to interact multiple times with the receptor
        # in the same location
        self.numEval += 1

	scoreLL = scoreRRL = scoreFRL = scoreRRRR = scoreRRFR = scoreFRFR = 0.0
        fitness_score = 0.0 # only contains Receptor-Ligand actions
        score = 0.0 # contains all terms, including IE
        self.scoreBreakdown = {}
        self.scoreBreakdown['RRL']  = 999999.9
        self.scoreBreakdown['FRL']  = 999999.9
        self.scoreBreakdown['LL']   = 999999.9
        self.scoreBreakdown['FRFR'] = 999999.9
        self.scoreBreakdown['RRFR'] = 999999.9
        self.scoreBreakdown['RRRR'] = 999999.9
        ##################################################
        ## Compute the Protein-Ligand interaction score ##
        ##################################################
	## 1. Rigid Rec-Ligand ##
        if self.RR_L_Fitness is True and RR_L is True:
            #t0 = time()
            if self.gridScorer:

                # check if atoms ar inside the box
                minx, miny, minz = numpy.min(L_coords, 0)
                maxx, maxy, maxz = numpy.max(L_coords, 0)
                ox, oy, oz = self.gridScorer.gridOrigin
                ex, ey, ez = self.gridScorer.gridEnd
                maxVal = -len(L_coords)*self.gridScorer.maxGridVal
                for x,y,z in L_coords:
                    if minx <= ox: return maxVal, maxVal
                    if miny <= oy: return maxVal, maxVal
                    if minz <= oz: return maxVal, maxVal

                    if maxx >= ex: return maxVal, maxVal
                    if maxy >= ey: return maxVal, maxVal
                    if maxz >= ez: return maxVal, maxVal
                    
                # make good score large positive numbers
                scoreRRL = self.gridScorer.score(L_coords, 'RRL')
                fitness_score += scoreRRL
                score += scoreRRL
                
            elif self.RRLmolSyst:
                #score = self.RRLmolSyst.scorer.get_score(L_coords)
                scorer = self.RRLmolSyst.scorer
                #  memory of RRLmolSyst
                #  | rigid receptor atoms | ligand atoms | 
                #  ^---begin              ^--- MemSplit  ^---end
                # Copy the ligand coordinates into the shared memory
                scorer.sharedMem[scorer.sharedMemSplit:] = numpy.array(L_coords , 'f')
                updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.RRLmolSyst,\
                             scorer.sharedMemPtr)

                # if distances are > cutoff, NAN is return.
                # else: the offending distance is returned. 
                # The distance matrice might only be partially populated as we 
                # break out as soon as a distance smaller than cutoff is seen. 
                # Scoring should not occur in this case as the clash is too severe
                mini = self.RRLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
                nan = isNAN(mini)
                if not nan:
                    if DEBUG:
                        print "Not scoring because Rigid receptor-ligand clash =", mini
                    scoreRRL = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
                    # Return a large negative value (not favorable interaction)
                    # This is due to the GA fitness/performance looking for a maximum
                    self.scoreBreakdown['RRL'] = scoreRRL
                    score += scoreRRL
                    fitness_score += scoreRRL
                    return -fitness_score, -score
                else:
                    # Get the score of Prot-ligand interaction
                    scoreRRL = scorer.get_score() * self.RRLmolSyst.factor
                    score += scoreRRL
                    fitness_score += scoreRRL
            self.scoreBreakdown['RRL'] = scoreRRL
	    #print "RRL: ",scoreRRL, fitness_score, score
            #print 'time RRL', time()-t0
            
        ## 2. Flexible Rec-Ligand ##
        if self.FRLmolSyst and self.FR_L_Fitness is True and FR_L is True:
            #t0 = time()
            scorer = self.FRLmolSyst.scorer
            #  memory of FRLmolSyst
            #  | flex receptor atoms | ligand atoms | 
            #  ^---begin             ^--- MemSplit  ^---end
            # Copy the flex rec & lig coordinates into the shared memory
            scorer.sharedMem[:] = numpy.array(FR_coords+self.interfaceCoords+L_coords , 'f')
            updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.FRLmolSyst,\
                         scorer.sharedMemPtr)

            # if distances are > cutoff, NAN is return.
            # else: the offending distance is returned. 
	    # The distance matrice might only be partially populated as we 
	    # break out as soon as a distance smaller than cutoff is seen. 
	    # Scoring should not occur in this case as the clash is too severe
            mini = self.FRLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
            nan = isNAN(mini)
            if not nan:
                if DEBUG:
                    print "Not scoring because Flexible receptor-ligand clash =", mini
                scoreFRL = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
	        # Return a large negative value (not favorable interaction)
	        # This is due to the GA fitness/performance looking for a maximum
                self.scoreBreakdown['FRL'] = scoreFRL
                score += scoreFRL
                fitness_score += scoreFRL
		###print "nan FRL"
                return -fitness_score, -score
            else:
                # Get the score of Prot-ligand interaction
                scoreFRL = scorer.get_score() * self.FRLmolSyst.factor
                score += scoreFRL
                fitness_score += scoreFRL
            self.scoreBreakdown['FRL'] = scoreFRL
	    #print "FRL: ",scoreFRL, fitness_score, score
            #print 'time FRL', time()-t0


        ############################
        ## Ligand Internal energy ##
        ############################
        if self.LLmolSyst and self.L_L_Fitness is True and L_L is True:
            #t0 = time()
            #coords3d = []
            #for c in L_coords:
            #    coords3d.append(eval("%.3f, %.3f, %.3f, "%tuple(c)))
            scorer = self.LLmolSyst.scorer
            #  memory of LLmolSyst
            #  | ligand atoms | ligand atoms | 
            #  ^---begin      ^--- MemSplit  ^---end
            # Copy the ligand coordinates into the shared memory
            #scorer.sharedMem[:] = numpy.array(L_coords+L_coords , 'f')
            #scorer.sharedMem[:] = numpy.array(coords3d+coords3d , 'f')
            scorer.sharedMem[:] = numpy.array(L_coords+L_coords, 'f')
            updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.LLmolSyst,\
                         scorer.sharedMemPtr)

            # if distances are > cutoff, NAN is return.
            # else: the offending distance is returned. 
	    # The distance matrice might only be partially populated as we 
	    # break out as soon as a distance smaller than cutoff is seen. 
	    # Scoring should not occur in this case as the clash is too severe
            mini = self.LLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
            nan = isNAN(mini)
            if not nan:
                if DEBUG:
                    print "Not scoring because Flexible receptor - ligand clash =", mini
                scoreLL = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
	        # Return a large negative value (not favorable interaction)
	        # This is due to the GA fitness/performance looking for a maximum
                self.scoreBreakdown['LL'] = scoreLL
                score += scoreLL
		##print "nan LL"
                return -fitness_score, -score
            else:
                # Get the score of Prot-ligand interaction
                scoreLL = scorer.get_score() * self.LLmolSyst.factor
                score += scoreLL  
            self.scoreBreakdown['LL'] = scoreLL
	    #print "LL: ",scoreLL, fitness_score, score
            #print 'time LL', time()-t0


        ##############################
        ## Receptor Internal energy ##
        ##############################
	## 1. IE of Flex atoms ##
	if self.FRFRmolSyst and self.FR_FR_Fitness is True: 
            #t0 = time()
	    scorer = self.FRFRmolSyst.scorer
	    #  memory of FRFRmolSyst
	    #  | flex receptor atoms | flex rec atoms | 
	    #  ^---begin             ^--- MemSplit    ^---end
	    # Copy the flex-rec coordinates into the shared memory
	    scorer.sharedMem[:] = numpy.array(FR_coords+self.interfaceCoords+FR_coords+self.interfaceCoords, 'f')
	    updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.FRFRmolSyst,\
                         scorer.sharedMemPtr)

            # if distances are > cutoff, NAN is return.
            # else: the offending distance is returned. 
	    # The distance matrice might only be partially populated as we 
	    # break out as soon as a distance smaller than cutoff is seen. 
	    # Scoring should not occur in this case as the clash is too severe
	    mini = self.FRFRmolSyst.check_distance_cutoff(0, 1, self.cutoff)
	    nan = isNAN(mini)
	    if not nan:
	        if DEBUG:
		    print "Not scoring because Flex-Flex rec clash =", mini
	        scoreFRFR = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
	        # Return a large negative value (not favorable interaction)
	        # This is due to the GA fitness/performance looking for a maximum
                self.scoreBreakdown['FRFR'] = scoreFRFR
                score += scoreFRFR
                fitness_score += scoreFRFR
		
	        return -fitness_score, -score
	    else:
		scoreFRFR = scorer.get_score() * self.FRFRmolSyst.factor
                score += scoreFRFR
                fitness_score += scoreFRFR
            self.scoreBreakdown['FRFR'] = scoreFRFR
	    #print "FRFR: ",scoreFRFR, fitness_score, score
            #print 'time FRFR', time()-t0

        ## 2. Interaction energy bt rigid-flex atoms ##
	if self.RRFRmolSyst and self.RR_FR_Fitness is True:
            #t0 = time()
            if self.gridScorer:
                # check if atoms ar inside the box
                minx, miny, minz = numpy.min(FR_coords, 0)
                maxx, maxy, maxz = numpy.max(FR_coords, 0)
                ox, oy, oz = self.gridScorer.gridOrigin
                ex, ey, ez = self.gridScorer.gridEnd
                maxVal = -len(FR_coords)*self.gridScorer.maxGridVal
                for x,y,z in FR_coords:
                    if minx <= ox: return maxVal, maxVal
                    if miny <= oy: return maxVal, maxVal
                    if minz <= oz: return maxVal, maxVal

                    if maxx >= ex: return maxVal, maxVal
                    if maxy >= ey: return maxVal, maxVal
                    if maxz >= ez: return maxVal, maxVal
                    
                # make good score large positive numbers
                scoreRRFR = self.gridScorer.score(FR_coords, 'RRFR')
                fitness_score += scoreRRFR
                score += scoreRRFR
		#####self.scoreBreakdown['RRFR'] = scoreRRFR
            else:
                scorer = self.RRFRmolSyst.scorer
                #  memory of RRFRmolSyst
                #  | rigid receptor atoms | flex rec atoms | 
                #  ^---begin              ^--- MemSplit    ^---end
                # Copy the rigid & flex rec coordinates into the shared memory
                scorer.sharedMem[:] = numpy.array(RR_coords+FR_coords, 'f')
                updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.RRFRmolSyst,\
                             scorer.sharedMemPtr)

                # if distances are > cutoff, NAN is return.
                # else: the offending distance is returned. 
                # The distance matrice might only be partially populated as we 
                # break out as soon as a distance smaller than cutoff is seen. 
                # Scoring should not occur in this case as the clash is too severe
                mini = self.RRFRmolSyst.check_distance_cutoff(0, 1, self.cutoff)
                nan = isNAN(mini)
                if not nan:
                    if DEBUG:
                        print "Not scoring because Rigid-Flex rec clash =", mini
                    scoreRRFR = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
                    # Return a large negative value (not favorable interaction)
                    # This is due to the GA fitness/performance looking for a maximum
                    self.scoreBreakdown['RRFR'] = scoreRRFR
                    score += scoreRRFR

                    fitness_score += scoreRRFR
                    return -fitness_score, -score
                else:
                    # Get the score of Prot-ligand interaction
                    scoreRRFR = scorer.get_score() * self.RRFRmolSyst.factor
                    score += scoreRRFR
                    fitness_score += scoreRRFR
            self.scoreBreakdown['RRFR'] = scoreRRFR
	    #print "RRFR: ",scoreRRFR, fitness_score, score
            #print 'time RRFR', time()-t0

        ## 3 : IE of Rigid atoms ##
	if self.RRRRmolSyst and self.RR_RR_Fitness is True:
            #t0 = time()
            scorer = self.RRRRmolSyst.scorer
            #  memory of RRRRmolSyst
            #  | rigid receptor atoms | rigid rec atoms | 
            #  ^---begin              ^--- MemSplit     ^---end
            # Copy the rigid rec coordinates into the shared memory
            scorer.sharedMem[:] = numpy.array(RR_coords+RR_coords, 'f')
            updateCoords(scorer.sharedMemSplit, scorer.sharedMemLen, self.RRRRmolSyst,\
                         scorer.sharedMemPtr)

            # if distances are > cutoff, NAN is return.
            # else: the offending distance is returned. 
	    # The distance matrice might only be partially populated as we 
	    # break out as soon as a distance smaller than cutoff is seen. 
	    # Scoring should not occur in this case as the clash is too severe
            mini = self.RRRRmolSyst.check_distance_cutoff(0, 1, self.cutoff)
            nan = isNAN(mini)
            if not nan:
                if DEBUG:
                    print "Not scoring because Rigid-Rigid rec clash =", mini
                scoreRRRR = min(9999999.9, 9999.9/mini) #larger than 10K and smaller than 10M
	        # Return a large negative value (not favorable interaction)
	        # This is due to the GA fitness/performance looking for a maximum
                self.scoreBreakdown['RRRR'] = scoreRRRR
                score += scoreRRFR
                return -fitness_score, -score
            else:
                # Get the score of Prot-ligand interaction
                scoreRRRR = scorer.get_score() * self.RRRRmolSyst.factor
                score += scoreRRRR
            self.scoreBreakdown['RRRR'] = scoreRRRR
            #print 'time RRRR', time()-t0


        # Return the Score. Score should be positive
        return -fitness_score, -score
