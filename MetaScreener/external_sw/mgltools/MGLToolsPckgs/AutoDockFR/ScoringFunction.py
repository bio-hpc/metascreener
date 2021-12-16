########################################################################
#
# Date: May 2012 Authors: Michel Sanner, Matt Danielson
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
# $Header: /opt/cvs/AutoDockFR/ScoringFunction.py,v 1.31 2014/07/31 18:20:49 pradeep Exp $
#
# $Id: ScoringFunction.py,v 1.31 2014/07/31 18:20:49 pradeep Exp $
#

import numpy
from cAutoDock.scorer import isNAN
from cAutoDock.scorer import MolecularSystem

#  Weights from AD4.1_bound.dat
FE_coeff_vdW_42		= 0.1662 # van der waals
FE_coeff_hbond_42	= 0.1209 # hydrogen bonding
FE_coeff_estat_42	= 0.1406 # electrostatics
FE_coeff_desolv_42	= 0.1322 # desolvation
FE_coeff_tors_42	= 0.2983 # torsional 


class ScoringFunction:
    def __init__(self):
        self.numEval = 0

        # list of molecualr systems that will be used to score interactions
        # between various parts (e.g. RRL, FRL, LL, RRFR, FRFR, RRRR)
        self.molecularSystems = []



    def createMolecularSystem(self):
        return MolecularSystem()

    def addMolecularSystem(self, description, internal=None):
        """
        create a new molecular system with a user given description (text)
        and whether it is an internal energy or not. If the MS is for internal
        energy then molSyst.factor will be set to 0.5 else it is set to 1.0
        """
        molSyst = self.createMolecularSystem()
        molSyst.description = description
        assert internal in (True, False, 0, 1)
        if internal:
            molSyst.factor = 0.5
        else:
            molSyst.factor = 1.0
            
        self.molecularSystems.append(molSyst)
        return molSyst

    # Each Scoring Function (ADCscorer, RMSDscorer, ect) should subclass score()        
    def score(self, candidate):
        pass


    def printAllScoreTerms(self, individual=None):
        ###
        ### None <- printAllScoreTerms()

        ### data is a dictionary that contains description of scoring terms, values, then breakdown.
        ### This function can also call getAllScoringTerms() to print the Summary of scoring terms 
        ###

        def _printTable(tmpData):
            # Print the dictionary of scoring terms

            name, value, detail = tmpData
            # If RecIE scoring, breakdown RecIE & indent everything
            if key == 'FlexReceptor' or key == 'FlexRigidReceptor' or key == 'RigidReceptor' \
			or key == 'RigidProtLig' or key == 'FlexProtLig':
                print "\t**\t%20s: %f" % (name, value)
                # Print the individual contributions (Hbonds, estat, VdW, ds)
                for k in detail.keys():
                    print "\t\t\t- %20s:\t\t%f" % (k, detail[k])
            else:
                print "%s: %f" % (name, value)
                # Print the individual contributions (Hbonds, estat, VdW, ds)
                for k in detail.keys():
                    print "\t- %20s:\t\t%f" % (k, detail[k])
            print

        # make sure scorer object are configures for thsi individual
        #if not individual == None:
        #    individual.score(individual)
 
       
        data = self.getAllScoreTerms(individual)
        ##data = self.getAllScoreTerms()
        if len(data) == 0:
	    print "Error in getAllScoreTerms...."
            return

        print "************************  Summary  ************************"
	# We need to use this instead of:
	# for key in data.keys()
	# To have the breakdown in a particular order
        for key in ['ProtLig', 'RigidProtLig', 'FlexProtLig', 'Ligand', 'Receptor', 'FlexReceptor', \
                   'FlexRigidReceptor', 'RigidReceptor','Tor', 'Overall']:
	    # If the key doesn't exits in the data dictionary, continue the for loop
            if not data.has_key(key):
                continue
            _printTable(data[key])

        return 

    def printEnergyBreakdownForInteraction(self, molSyst):
        scorer = molSyst.scorer
        totalEnergy = scorer.get_score() * molSyst.factor
        print "** energy of the %s: %f"%(molSyst.description, totalEnergy)
        

    def printEnergyBreakdownForTerm(self):
        for molSyst in self.molecularSystems:
            self.printEnergyBreakdownForInteraction(molSyst)


    def getTerms(self, molSyst):
	"""
	return a dictionary containing the various terms of the scorer used for
	the given molecular system

	dict <- getTerms(molSyst

	dict has the following keys:
	names: a list of term names
	terms: a dictionary of name:term items
        weights: a dictionary of name:weight items
	"""

	d = {}
	# Name of the scorer
	d['scorer'] = scorer = molSyst.scorer
	# Names of the terms making up the total score of the molSyst
	d['names'] = names = molSyst.scorer.names
	td = {}
	# Actual terms of the scorer
        terms = molSyst.scorer.get_terms()
	# Weights associtaed with each term
        weights = molSyst.scorer.get_weights()
	for name, term, weight in zip(names, terms, weights):
	    td[name] = (term, weight)
	d['terms'] = td
	return d


    def getAllScoreTermsDictionary(self, molSyst):
        """
	This function ...

        breakdown <- getScoreBreakdown(self, molSyst)

        molSyst   - a molecular system that contains a scorer (and molSyst.factor)
        breakdown - is a dict holding the Total score & term breakdown.
                    will contian a name, value, details
			name = string
			value = float
			details = {}

        ex: {'': ['Sum', -2.181810051144073, 
	{'hBonds': -0.07926812351745408, 'ds': 1.7603351532549212, 'vdw': -4.346005490067211, 'electrostatics': 0.48312840918567057}]}

        """

        breakdown = {}
        terms = molSyst.scorer.get_terms() # Method returns a cAutoDock.scorer.TermVect object (can not see the value)
        weights = molSyst.scorer.get_weights()
        names = molSyst.scorer.names
        tmp = {}
	 
        for t, w, n in zip(terms, weights, names):
           tmp[n] = t.get_score()*w * molSyst.factor

        score = molSyst.scorer.get_score() * molSyst.factor
        breakdown[''] = ["Sum", score, tmp]

        return breakdown
    

    def getAllScoreTerms(self, individual=None):
        ###
        ### data <- getAllScoreTerms()
	#import pdb
	#pdb.set_trace()
        if individual:
            individual.score()#self.score(individual)
            #print individual._score
        data = {}
        bindingScore = 0.0
        recligBE = 0.0
        recIE = 0.0
        counter = 1
        for k,v in self.scoreBreakdown.items():
            if v==999999.9: continue
            if k =='RRL':
                description = "interaction energy between rigid rec & lig"
                if self.gridScorer:
                    if individual:
                        RR_coords, FR_coords, L_coords = individual.phenotype #toPhenotype(individual)
                    else:
                        L_coords = self.ligAtoms.coords
                    terms,values,evalxChg, dvalxChg = self.gridScorer.scoreBreakDown(L_coords, k)
                    MLD = {}
                    total = terms.pop('total')
                    MLD['RigidProtLig'] = [description, total, terms] 
                else:
                    # get the dictionary containing scoring breakdown
                    MLD = self.getAllScoreTermsDictionary(self.RRLmolSyst)
                    # Update generic key to store the specific one that printAllScoreTerms uses
                    MLD['RigidProtLig'] = MLD.pop('')
                    MLD['RigidProtLig'][0] = description

                    # Update the data dictionary to hold the Rigid Rec-ligand information
                data.update(MLD)    
                score = MLD['RigidProtLig'][1]
                bindingScore += score
                recligBE = score

            elif k =='FRL':
                # get the dictionary containing scoring breakdown
                MLD = self.getAllScoreTermsDictionary(self.FRLmolSyst)
                # Update generic key to store the specific one that printAllScoreTerms uses
	        MLD['FlexProtLig'] = MLD.pop('')
                description = "interaction energy between the flex rec & lig"
                MLD['FlexProtLig'][0] = description

                # Update the data dictionary to hold the Flex Rec-ligand information
                data.update(MLD)

                score = MLD['FlexProtLig'][1]
                bindingScore += score
                recligBE +=score

            elif k =='LL':
		MLD = {}
            	description = "internal energy of the ligand (%d)" % counter
                MLD['Ligand'] = [description, 0.0, {}]

            	# Update the data dictionary to hold the Prot-ligand information
            	data.update(MLD)
            	ligIE_counter = counter

                # get the dictionary containing scoring breakdown
                # internal energy scores /2. While the energy for pair (i,j) is only computed once it is stored
                # twice in the score array once at (i,j) and once at (j,i)
                MLD = self.getAllScoreTermsDictionary(self.LLmolSyst)
                MLD['Ligand'] = MLD.pop('')
                description = "(%d) internal energy of the ligand" % counter
                MLD['Ligand'][0] = description

                # Update the data dictionary to hold the Prot-ligand information
                data.update(MLD)

                score = MLD['Ligand'][1]
                # MLD: We are not including the LigandIE in the dG prediction.  Matches what AD4.2 does
                #bindingScore += score
                ligIE_counter = counter
                counter += 1

            elif k =='FRFR':
                                #Pradeep
                # get the dictionary containing scoring breakdown
	        MLD = self.getAllScoreTermsDictionary(self.FRFRmolSyst)
	        # Update generic key to store the specific one that printAllScoreTerms uses
	        MLD['FlexReceptor'] = MLD.pop('')
                description = "interaction energy between the flex-flex rec"
	        MLD['FlexReceptor'][0] = description

	        # Update the data dictionary to hold the Prot-ligand information
	        data.update(MLD)

                recIE += MLD['FlexReceptor'][1]
                ##bindingScore -= MLD['FlexReceptor'][1]
    	        #bindingScore += recIE


                pass

            elif k =='RRFR':
                description = "interaction energy between rigid-flex rec"
                if self.gridScorer:
                    if individual:
                        RR_coords, FR_coords, L_coords = individual.phenotype #toPhenotype(individual)
                    else:
                        FR_coords = self.flexRecAtoms.coords
                    terms,values,evalxChg, dvalxChg = self.gridScorer.scoreBreakDown(FR_coords, k)
                    MLD = {}
                    total = terms.pop('total')
                    MLD['FlexRigidReceptor'] = [description, total, terms] 
                else:
                    # get the dictionary containing scoring breakdown
                    MLD = self.getAllScoreTermsDictionary(self.RRFRmolSyst)
                    # Update generic key to store the specific one that printAllScoreTerms uses
                    MLD['FlexRigidReceptor'] = MLD.pop('')
                    description = "interaction energy between the rigid-flex rec"
                    MLD['FlexRigidReceptor'][0] = description

	        # Update the data dictionary to hold the Prot-ligand information
	        data.update(MLD)

                recIE += MLD['FlexRigidReceptor'][1]
    	        #bindingScore += recIE

            elif k =='RRRR':
                pass
            
        ### data is a dictionary that contains description of scoring terms, values, then breakdown.
        ### Method retrieves all the previously calculated scores

        ## data = {}
        ## bindingScore = 0.0
	## ###########################################
	## # Protein- Ligand Interaction Energy term #
	## ###########################################
	## # 1. Rigid Rec-Ligand Interaction Energy term #
        ## if self.RR_L_Fitness and self.RR_L:

        ##     # if distances are > cutoff, NAN is return.
        ##     # else: the offending distance is returned. 
	##     # The distance matrice might only be partially populated as we 
	##     # break out as soon as a distance smaller than cutoff is seen. 
	##     # Scoring should not occur in this case as the clash is too severe
        ##     mini = self.RRLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
        ##     nan = isNAN(mini)
        ##     if not nan:
        ##         score = min(9999999.9, 9999.9/mini)
        ##         description = "interaction energy between rigid rec & lig"
        ##         data['RigidProtLig'] = [description, score, {}]
	##         # Return a large postive value (not favorable interaction)
	##         # This is Summary statement.  Dont need to make it negative to satisfy the GA fitness/performance looking for a maximum
        ##         bindingScore += score
        ##     else:
        ##         # get the dictionary containing scoring breakdown
        ##         MLD = self.getAllScoreTermsDictionary(self.RRLmolSyst)
        ##         # Update generic key to store the specific one that printAllScoreTerms uses
	##         MLD['RigidProtLig'] = MLD.pop('')
        ##         description = "interaction energy between rigid rec & lig"
        ##         MLD['RigidProtLig'][0] = description

        ##         # Update the data dictionary to hold the Rigid Rec-ligand information
        ##         data.update(MLD)

        ##         score = MLD['RigidProtLig'][1]
        ##         bindingScore += score

        ## # 2. Flex Rec-Ligand Interaction Energy term #
        ## if self.FR_L_Fitness and self.FR_L:

        ##     # if distances are > cutoff, NAN is return.
        ##     # else: the offending distance is returned. 
	##     # The distance matrice might only be partially populated as we 
	##     # break out as soon as a distance smaller than cutoff is seen. 
	##     # Scoring should not occur in this case as the clash is too severe
        ##     mini = self.FRLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
        ##     nan = isNAN(mini)
        ##     if not nan:
        ##         score = min(9999999.9, 9999.9/mini)
        ##         description = "interaction energy between the flex rec & lig"
        ##         data['FlexProtLig'] = [description, score, {}]
	##         # Return a large postive value (not favorable interaction)
	##         # This is Summary statement.  Dont need to make it negative to satisfy the GA fitness/performance looking for a maximum
        ##         bindingScore += score
        ##     else:
        ##         # get the dictionary containing scoring breakdown
        ##         MLD = self.getAllScoreTermsDictionary(self.FRLmolSyst)
        ##         # Update generic key to store the specific one that printAllScoreTerms uses
	##         MLD['FlexProtLig'] = MLD.pop('')
        ##         description = "interaction energy between the flex rec & lig"
        ##         MLD['FlexProtLig'][0] = description

        ##         # Update the data dictionary to hold the Flex Rec-ligand information
        ##         data.update(MLD)

        ##         score = MLD['FlexProtLig'][1]
        ##         bindingScore += score


	# Sum up the protein-ligand interaction energy
        if self.RR_L_Fitness or self.FR_L_Fitness:
            description = "(%d) interaction energy between the ligand & receptor" % counter
            #data['ProtLig'] = [description, bindingScore, {}]
            data['ProtLig'] = [description, recligBE, {}]
            counter += 1

	## ###############################
	## # Ligand Internal Energy term #
	## ###############################
        ## if self.L_L_Fitness and self.L_L:
        ##     # Rigid ligand, so score will always be 0.0.  Dont want a term breakdown
	##     if self.ligandTorTree.get_depth() == 0: #MLD: HACK to get # of torsions.  FIXME
	## 	MLD = {}
        ##     	description = "internal energy of the ligand (%d)" % counter
        ##         MLD['Ligand'] = [description, 0.0, {}]

        ##     	# Update the data dictionary to hold the Prot-ligand information
        ##     	data.update(MLD)

        ##     	ligIE_counter = counter

        ##     else:
        ##     	# if distances are > cutoff, NAN is return.
        ##     	# else: the offending distance is returned. 
	##     	# The distance matrice might only be partially populated as we 
	##     	# break out as soon as a distance smaller than cutoff is seen. 
	##     	# Scoring should not occur in this case as the clash is too severe
        ##     	mini = self.LLmolSyst.check_distance_cutoff(0, 1, self.cutoff)
        ##     	nan = isNAN(mini)
        ##     	if not nan:
        ##             score = min(9999999.9, 9999.9/mini)
        ##     	    description = "(%d) internal energy of the ligand" % counter
        ##             data['Ligand'] = [description, score, {}]
	##             # Return a large postive value (not favorable interaction)
	##             # This is Summary statement.  Dont need to make it negative to satisfy the GA fitness/performance looking for a maximum
        ##             bindingScore += score
	## 	else:
        ##             # get the dictionary containing scoring breakdown
        ##             # internal energy scores /2. While the energy for pair (i,j) is only computed once it is stored
        ##             # twice in the score array once at (i,j) and once at (j,i)
        ##             MLD = self.getAllScoreTermsDictionary(self.LLmolSyst)
	##             MLD['Ligand'] = MLD.pop('')
        ##     	    description = "(%d) internal energy of the ligand" % counter
        ##     	    MLD['Ligand'][0] = description

        ##     	    # Update the data dictionary to hold the Prot-ligand information
        ##     	    data.update(MLD)

        ##     	    score = MLD['Ligand'][1]
	## 	    # MLD: We are not including the LigandIE in the dG prediction.  Matches what AD4.2 does
        ##     	    #bindingScore += score
        ##     	    ligIE_counter = counter
        ##     	    counter += 1



	## #################################
	## # Receptor Internal Energy term #
	## #################################
        ## # 1: Internal energy among Flexible atoms #
        ## recIE = 0.0
        ## if self.FR_FR_Fitness and self.FR_FR:
        ##     # if distances are > cutoff, NAN is return.
        ##     # else: the offending distance is returned. 
	##     # The distance matrice might only be partially populated as we 
	##     # break out as soon as a distance smaller than cutoff is seen. 
	##     # Scoring should not occur in this case as the clash is too severe
	##     mini = self.FRFRmolSyst.check_distance_cutoff(0, 1, self.cutoff)
	##     nan = isNAN(mini)
	##     if not nan:
	##         score = min(9999999.9, 9999.9/mini)
        ##     	description = "internal energy of the flex-flex rec"
	##         data['FlexReceptor'] = [description, score, {}]
        ##         bindingScore += score
	##     else:
        ##     	# get the dictionary containing scoring breakdown
        ##     	# internal energy scores /2. While the energy for pair (i,j) is only computed once it is stored
        ##     	# twice in the score array once at (i,j) and once at (j,i)
        ##     	MLD = self.getAllScoreTermsDictionary(self.FRFRmolSyst)
        ##     	MLD['FlexReceptor'] = MLD.pop('')
        ##     	description = "internal energy of the flex-flex rec"
        ##     	MLD['FlexReceptor'][0] = description

        ##     	# Update the data dictionary to hold the Prot-ligand information
        ##     	data.update(MLD)

        ##     	recIE = MLD['FlexReceptor'][1]
    	##     	bindingScore += recIE

        ## # 2 : E between Rigid & Flex domains in receptor #
        ## if self.RR_FR_Fitness and self.RR_FR:
        ##     # if distances are > cutoff, NAN is return.
        ##     # else: the offending distance is returned. 
	##     # The distance matrice might only be partially populated as we 
	##     # break out as soon as a distance smaller than cutoff is seen. 
	##     # Scoring should not occur in this case as the clash is too severe
	##     mini = self.RRFRmolSyst.check_distance_cutoff(0, 1, self.cutoff)
	##     nan = isNAN(mini)
	##     if not nan:
	##         score = min(9999999.9, 9999.9/mini)
        ##         description = "interaction energy between rigid-flex rec"
	##         data['FlexRigidReceptor'] = [description, score, {}]
        ##         bindingScore += score
	##     else:
	##         # get the dictionary containing scoring breakdown
	##         MLD = self.getAllScoreTermsDictionary(self.RRFRmolSyst)
	##         # Update generic key to store the specific one that printAllScoreTerms uses
	##         MLD['FlexRigidReceptor'] = MLD.pop('')
        ##         description = "interaction energy between the rigid-flex rec"
	##         MLD['FlexRigidReceptor'][0] = description

	##         # Update the data dictionary to hold the Prot-ligand information
	##         data.update(MLD)

        ##         recIE += MLD['FlexRigidReceptor'][1]
    	##         bindingScore += recIE

        ## # 3: IE of Rigid domain in receptor #
        ## if self.RR_RR_Fitness and self.RR_RR:
        ##     # if distances are > cutoff, NAN is return.
        ##     # else: the offending distance is returned. 
	##     # The distance matrice might only be partially populated as we 
	##     # break out as soon as a distance smaller than cutoff is seen. 
	##     # Scoring should not occur in this case as the clash is too severe
	##     mini = self.RRRRmolSyst.check_distance_cutoff(0, 1, self.cutoff)
	##     nan = isNAN(mini)
	##     if not nan:
	##         score = min(9999999.9, 9999.9/mini)
        ##     	description = "internal energy of the rigid-rigid rec"
	##         data['RigidReceptor'] = [description, score, {}]
        ##         bindingScore += score
	##     else:
	##     	# get the dictionary containing scoring breakdown
	##     	MLD = self.getAllScoreTermsDictionary(self.RRRRmolSyst)
	##     	# Update generic key to store the specific one that printAllScoreTerms uses
	##     	MLD['RigidReceptor'] = MLD.pop('')
        ##     	description = "internal energy of the rigid-rigid rec"
	##     	MLD['RigidReceptor'][0] = description

	##     	# Update the data dictionary to hold the Prot-ligand information
	##     	data.update(MLD)

        ##     	recIE += MLD['RigidReceptor'][1]
    	##     	bindingScore += recIE

	# Sum up the rec-rec interaction energy
        if self.RR_RR_Fitness or self.RR_FR_Fitness or self.FR_FR_Fitness:
            #description = "internal energy of the receptor (%d)" % counter
            description = "(%d) internal energy of the receptor" % counter
            data['Receptor'] = [description, recIE, {}]
            recIE_counter = counter
            counter +=1
        else:
            description = "(%d) internal energy of the receptor" % counter
            MLD['Receptor'] = [description, 0.0, {}]

            # Update the data dictionary to hold the Prot-ligand information
            data.update(MLD) 
            recIE_counter = counter
            counter +=1

        ##########################################################
        # Torsional free energy term: wt * TORSDOF of the ligand #
        ##########################################################
        Torsional_score = self.TORSDOF * FE_coeff_tors_42
        description = "(%d) lig torsional free energy" % counter
        data['Tor'] = [description, Torsional_score, {}]
        bindingScore += Torsional_score

        ##############################################################
        # Sum of all scoring terms that contribute to binding energy #
        ##############################################################
        description = "************************  Total  ************************\nFree energy of binding in kcal/mol"
        if self.scoreBreakdown.has_key('LL') and \
           self.scoreBreakdown['LL']!=999999.9:
            for x in range(1, counter+1):
                if x == 1:
                    if ((x != ligIE_counter) and (x != recIE_counter)):
                        description = description + " [=(" + str(x) + ")"
                    elif (x != recIE_counter):
                        description = description + " [=(" + str(x) + ")+(-" + str(x) + ")"
                elif x == counter:
                    if ((x != ligIE_counter) and (x != recIE_counter)):
                        description = description + "+(" + str(x) + ")]"
                    else:
                        description = description + "+(" + str(x) + ")+(-" + str(x) + ")]"
                else:
                    if ((x != ligIE_counter) and (x != recIE_counter)):
                        description = description + "+(" + str(x) + ")"
                    elif (x != recIE_counter):
                        description = description + "+(" + str(x) + ")+(-" + str(x) + ")"


        data['Overall'] = [description, bindingScore, {}]
            
        return data     

 
    def getPerAtomBreakdown(self, molSyst):
	"""
        list <- getPerAtomBreakdown(molSyst)

        molSyst - MolecularSystem that includes a scorer within it

        Function returns a list of per atom energies for a molSyst.
	Useful when trying to compare the per atom energies with AD4.2
	or debugging when you dont trust the energy is correct  
	"""


	lines = []
        # Get the dictionary that contains keys: terms (dictionary of:term, weight), names, scorer
        d1 = self.getTerms(molSyst)
	perLigAtom = {}

	# Formatting string
        fmt =  "%5d  %2s  "
        fmt1 = "Sum:      "
	# create header line 
	header = " Num  Type "
        termTotals = []
        # Assign each scoring term & associated array to the dictionary
	# For each scoring term
        for name in d1['names']:
	    term, weight = d1['terms'][name]
            print term, weight
	    # Get the scoring array
	    array = numpy.array(term.get_score_array(), 'f')
	    # Add the name a the key, numpy array as the value
	    perLigAtom[name] = array.sum(axis=0) * weight * molSyst.factor
	    fmt += "%9.4f "
	    fmt1 += "%9.4f "
	    header += "%9s "%name[:9]
	    # Place holder for now
	    termTotals.append(0.0)
        print "**  per atom ligand breakdown"

        lines.append(header)

	# Using the shape attribute of numpy to return dimensions of the array
	nbAtR, nbAtL = array.shape

	# Score for each ligand atom
	ligAtoms = molSyst.get_atoms(1)
	for i in range(nbAtL):
            # List to store atom name and the scores
	    #values = [ligAtoms[i].get_name()]
            values = [i+1, ligAtoms[i].get_element()]
	    # Get the value for each atom, all terms
	    for j, name in enumerate(d1['names']):
		val = perLigAtom[name][i]
		values.append(val)
	        # Update the term summation
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
        line = fmt1 % tuple(termTotals) 
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

