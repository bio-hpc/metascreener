########################################################################
#
# Date: 2000 Authors: Michel Sanner, Matt Danielson
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
# $Header: /opt/cvs/AutoDockFR/evaluateEnergy.py,v 1.5 2012/06/21 22:23:02 mldaniel Exp $
#
# $Id: evaluateEnergy.py,v 1.5 2012/06/21 22:23:02 mldaniel Exp $
#

import numpy, os

class ADEnergyEvaluator:
    """
    This class allows calculating the energy of a complex
    """


    def __init__(self, receptor, ligand, forceFieldVersion='4', receptorFT=None, scorerOpts={}):
        """
        evaluator <- ADEnergyEvaluator(receptor, ligand, breakdown, forcefield='4')
        receptor - receptor molecule
        ligand   - 
        forcefield
        scorerOpts - dictionary of optinal parameter for scorer
        """
        if forceFieldVersion=='4':
            from AutoDockFR.ADCscorer import AD42ScoreC as ScorerClass
	    #  Weights from AD4.1_bound.dat
	    self.FE_coeff_vdW_42	= 0.1662 # van der waals
	    self.FE_coeff_hbond_42	= 0.1209 # hydrogen bonding
            self.FE_coeff_estat_42	= 0.1406 # electrostatics
            self.FE_coeff_desolv_42	= 0.1322 # desolvation
	    self.FE_coeff_tors_42	= 0.2983 # torsional 

        else:
            raise ValueError("bad forcefield version, expect '4' got %s" % forceFieldVersion)

        # ligand atoms
        self.ligand = ligand
        self.ligAtoms = ligand.allAtoms

        self.receptorFT = receptorFT

	# passed a Flexilbity tree
        if receptorFT:
            rigidRecAtoms = receptorFT.getRigidAtoms()
            flexRecAtoms = receptorFT.getMovingAtoms()
        else:
            rigidRecAtoms = receptor.allAtoms
            flexRecAtoms = []

        #print 'building scorer for %d rigid Rec %d ligand and %d flexible Rec atoms' % (
        #    len(rigidRecAtoms), len(self.ligAtoms), len(flexRecAtoms))
        
	# Create scorer
        self.scorer=ScorerClass(rigidRecAtoms, self.ligAtoms, self.ligand.torTree, self.ligand.TORSDOF,
                                flexRecAtoms=flexRecAtoms, **scorerOpts)

        # Method call to create a dictionary that stores all the scoring values
        self.data=self.scorer.getAllScoreTerms()

    def getProtLigScore(self, receptorFT=None):
        """
        None <- getProtLigScore(receptorFT)
        receptorFT - receptor flexiblity tree.  Used as a marker to print one or two scores

        Will print the protein-ligand interaction energy to the screen
        """

        # If you have receptor flexiblity, need 1. RigRec-Ligand score
        # & 2. FlexRec-Ligand score
        if receptorFT != None:
            print self.data['FlexProtLig'][1] + self.data['RigidProtLig'][1]
        else:
            print self.data['RigidProtLig'][1]
 
    def getProtLigScoreBreakdown(self):
        """
        None <- getProtLigScoreBreakdown()

        Will print the scoring breakdown to the screen
        """

        self.scorer.printAllScoreTerms(self.data)
 
    def getPerAtomBreakdown(self, molSyst):

	lines = []
        # Get the dictionary of terms
        d1 = self.scorer.getTerms(molSyst)
	perLigAtom = {}
        fmt = "\t%-20s "
	shortTermNames = ["Atmname"]
        termTotals = []
        # Assign each scoring term & associated array to the dictionary
        for name in d1['names']:
	    term, weight = d1['terms'][name]
	    array = numpy.array(term.get_score_array(), 'f')
	    perLigAtom[name] = array.sum(axis=0)*weight
	    fmt += "%-10s "
	    shortTermNames.append(name[:min(len(name),10)])
	    termTotals.append(0)
        print "**  per atom ligand breakdown"

	# create header line 
	line = fmt%tuple(shortTermNames)
        lines.append(line)

	# Using the shape attribute of numpy to return a tuple of the dimensions of the array
	nbAtR, nbAtL = array.shape

	# Score for each ligand atom
	#ligAtoms = molSyst.get_atoms(molSyst.atomSetIndices['set2'])
	ligAtoms = molSyst.get_atoms(1)
	for i in range(nbAtL):
            # List to store atom name and the scores
	    values = [ligAtoms[i].get_name()]
	    for j, name in enumerate(d1['names']):
		val = perLigAtom[name][i]
		values.append(val)
		termTotals[j] += val

            # Add the line to list
            line = fmt % tuple(values)
            lines.append(line)

	from math import fabs
	# Check to make sure the sum of the individual ligand atom scoring contributions add up to the toal value reported
	# We use the fabs because we are dealing with floats and rounding error.
	for j, name in enumerate(d1['names']):
	    term, weight = d1['terms'][name]
	    if fabs(termTotals[j] - term.get_score() * weight) > 0.01:
		print 'WARNING sum of per ligand atm %s interaction (%f) does not match term (%f)'%(name, termTotals[j], term.get_score() * weight)

	# Summary of values @ the end of Energy.txt
        line = "\t--------------------------------------------------------------------------"
        lines.append(line)
        line = fmt % (("Sum",)+tuple(termTotals)) 
        lines.append(line)
	return lines


    def getProtLigScorePerAtom(self):
        """
        None <- getProtLigScorePerAtom()

        Per atom energy analysis: breakdown of the scoring contribution: vdw, ele, hbond, delsolv
        """

        # return a per atom list of energetic contributions
        
	self.line_lst = []
        print "**  per atom ligand breakdown"
        line = "\t%-10s %-10s %-10s %-10s %-10s %-10s %-10s" % ("Atmname", "vdW+Hb+Ele", "vdW+Hbond", "Ele", "VDW", "Hbond", "Desolv") 
        print line
        self.line_lst.append(line)
   
	# vdw.get_score_array() returns a list of lists that stores the score for each ligand atom. 1D = each protein atom,  2D = each ligand atom
	vdw = self.scorer.vdw # instance of cAutoDock.scorer.VanDerWaals
	#Using numpy to create an array not a list of lists
	vdwArray = numpy.array(vdw.get_score_array())
	estat = self.scorer.estat
	estatArray = numpy.array(estat.get_score_array())
	hBond = self.scorer.hBond
	hBondArray = numpy.array(hBond.get_score_array())
	ds = self.scorer.ds
	dsArray = numpy.array(ds.get_score_array())

	# Using the shape attribute of numpy to return a tuple of the dimensions of the array
	nbAtR, nbAtL = vdwArray.shape

	# Array that contains the sum of all protein interactions with each ligand atom.  Scaled by the 4.2 prefactors
	perLigAtVdw  = vdwArray.sum(axis=0)   * self.FE_coeff_vdW_42
	perLigAtElec = estatArray.sum(axis=0) * self.FE_coeff_estat_42
	perLigAtds   = dsArray.sum(axis=0)    * self.FE_coeff_desolv_42
	perLigAthb   = hBondArray.sum(axis=0) * self.FE_coeff_hbond_42

	self.totalVDW = self.totalELE = self.totalHB = self.totalDS = 0.0
	# Print out the scores for each ligand atom
	for i in range(nbAtL):
	    # Needed to produce an output file that looks like AD4.2 .dlg file
	    vdwHbScore = perLigAtVdw[i] + perLigAthb[i]
	    vdwHbEleScore = vdwHbScore + perLigAtElec[i]
            line = "\t%-10s %-10f %-10f %-10f %-10f %-10f %-10f" % \
                (self.ligAtoms[i].name, vdwHbEleScore, vdwHbScore, perLigAtElec[i], perLigAtVdw[i], perLigAthb[i], perLigAtds[i])
            self.line_lst.append(line)
	    print line

	    # Keep track of the total score for Summary of Energy values
	    self.totalVDW += perLigAtVdw[i]
	    self.totalELE += perLigAtElec[i]
	    self.totalHB += perLigAthb[i]
	    self.totalDS += perLigAtds[i]

	from math import fabs
	# Check to make sure the sum of the indivual ligand atom scoring contributions add up to the toal value reported
	# We use the fabs because we are dealing with floats and rounding error.
	assert fabs(self.totalVDW - vdw.get_score() * self.FE_coeff_vdW_42) < 0.0001, \
            "sum of per ligand VDW interactions (%f) does not match VDW term (%f)"%(self.totalVDW, vdw.get_score() * VDW_WEIGHT_AUTODOCK)
	assert fabs(self.totalELE - estat.get_score() * self.FE_coeff_estat_42) < 0.0001, \
            "sum of per ligand ELE interactions (%f) does not match ELE term (%f)"%(self.totalELE, estat.get_score() * ESTAT_WEIGHT_AUTODOCK)
	assert fabs(self.totalHB - hBond.get_score() * self.FE_coeff_hbond_42) < 0.0001, \
            "sum of per ligand HB interactions (%f) does not match HB term (%f)"%(self.totalHB, hBond.get_score() * HBOND_WEIGHT_AUTODOCK)
	assert fabs(self.totalDS - ds.get_score() * self.FE_coeff_desolv_42) < 0.0001, \
            "sum of per ligand DS interactions (%f) does not match DS term (%f)"%(self.totalDS, ds.get_score() * DESOLV_WEIGHT_AUTODOCK)

	# Summary of values @ the end of Energy.txt
        line = "\t--------------------------------------------------------------------------"
        print line
        self.line_lst.append(line)
        line = "\t%-10s %-10.2f %-10.2f %-10.2f %-10.2f %-10.2f %-10.2f" % \
            ("Sum", self.totalVDW + self.totalELE + self.totalHB + self.totalDS, \
            self.totalVDW+self.totalHB, self.totalELE, self.totalVDW, self.totalHB, self.totalDS) 
        print line
        self.line_lst.append(line)

    def getProtLigScorePerAtomToFile(self):
        """
        None <- getProtLigScorePerAtomToFile()

        saves a file w/per atom energy analysis: breakdown of the scoring contribution: vdw, ele, hbond, delsolv
	output = cAD_Energy.txt
        """

        # Check to see if Energy.txt file already exists.  Remove if it does
	if os.path.isfile("cAD_Energy.txt"):
	    os.remove("cAD_Energy.txt")

	# Output file
	fo = open("cAD_Energy.txt", "w")
	fo.write("cAutoDock Intermolecular Energy Analysis\n\n")
        for line in self.line_lst:
           fo.write(line + "\n")

        #MLD: I think we need this for some other post-processing script....
	# Summary of values @ the end of Energy.txt
	fo.write("\n\n\tVDW Energy: %s\n" % (self.totalVDW))
	fo.write("\tELE Energy: %s\n" % (self.totalELE))
	fo.write("\tHB Energy: %s\n" % (self.totalHB))
	fo.write("\tDS Energy: %s\n" % (self.totalDS))
	fo.write("\tTotal Energy: %s\n" % (self.totalVDW + self.totalELE + self.totalHB + self.totalDS))
	fo.close()
           
