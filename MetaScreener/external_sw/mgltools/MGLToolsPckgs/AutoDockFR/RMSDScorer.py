########################################################################
#
# Date: 2014 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2014
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/RMSDScorer.py,v 1.1 2014/07/31 21:06:38 sanner Exp $
#
# $Id: RMSDScorer.py,v 1.1 2014/07/31 21:06:38 sanner Exp $
#

from AutoDockFR.ScoringFunction import ScoringFunction

from mglutil.math.rmsd import RMSDCalculator

class RMSDScorer(ScoringFunction): 

    def __init__(self, ligAtomRefCoords, flexRecAtomsRefCoords=None):
        self.ligAtomRefCoords = ligAtomRefCoords
        self.flexRecAtomsRefCoords = flexRecAtomsRefCoords
        self.ligandRmsdCalculators = RMSDCalculator(refCoords=ligAtomRefCoords)
        if flexRecAtomsRefCoords:
            self.flexRecRmsdCalculators = RMSDCalculator(refCoords=flexRecAtomsRefCoords)
        self.numEval = 0
        self.TORSDOF = 0
        
    def score(self, RR_coords, FR_coords, L_coords,
              RR_L=True, FR_L=True, L_L=True, 
              RR_RR=True, RR_FR=True, FR_FR=True):
     
        # returns fitness_score as the sum of RMSD of ligand atoms and
        # flexible receptor atoms
        
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


        rmsdL = self.ligandRmsdCalculators.computeRMSD(L_coords)
        self.scoreBreakdown['LL'] = rmsdL
        
        if self.flexRecAtomsRefCoords:
            rmsdFR = self.flexRecRmsdCalculators.computeRMSD(FR_coords)
            self.scoreBreakdown['FRFR'] = rmsdFR
        else:
            rmsdFR = 0.0
            
        return -rmsdL - rmsdFR, -rmsdL - rmsdFR 
