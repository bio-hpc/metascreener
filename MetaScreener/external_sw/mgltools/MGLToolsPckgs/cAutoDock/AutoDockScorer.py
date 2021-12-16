## Automatically adapted for numpy.oldnumeric Jul 30, 2007 by 

##
## Copyright (C)2007 The Scripps Research Institute 
##
## Authors: Alexandre Gillet <gillet@scripps.edu>
##  
## For further information please contact:
##  Alexandre Gillet
##  <gillet@scripps.edu>
##  The Scripps Research Institute
##  10550 N Torrey Pines Rd 
##  La Jolla Ca 92037 USA
##  
##  
## $Header: /opt/cvs/cAutoDockDIST/cAutoDock/AutoDockScorer.py,v 1.3 2007/07/30 20:21:43 vareille Exp $
## $Id: AutoDockScorer.py,v 1.3 2007/07/30 20:21:43 vareille Exp $
##  
##

## This is python wrapper of the c implementation of AutoDockScorer
import cAutoDock
from cAutoDock import scorer
from cAutoDock.scorer import MolecularSystem
from cAutoDock.scorer import VanDerWaals
from cAutoDock.scorer import HydrogenBonding
from cAutoDock.scorer import Electrostatics
from cAutoDock.scorer import Desolvation
from cAutoDock.scorer import WeightedMultiTerm

from memoryobject import memobject
import numpy.oldnumeric as Numeric


class AutoDockTermWeights305:
    def __init__(self):
        self.name = 'asdf'

    estat_weight = 0.1146 # Autogrid3 weight
    dsolv_weight = 0.1711 # Autogrid3 weight
    hbond_weight = 0.0656 # Autogrid3 weight
    vdw_weight = 0.1485 # Autogrid3 weight
# AutoDockTermWeights305

class AutoDock305Scorer(AutoDockTermWeights305):

    def __init__(self,ms=None,pyatomset1=None,pyatomset2=None):

        # check that ms is of MolecularSystem
        if ms is None:
            print " You need to specify a molecular system when using the c scorer"
            return
        if type(ms) is not MolecularSystem:
            print "Molecular System not of type MolecularSystem "
            return
        self.ms = ms
        self.prop = 'ad305_energy'
        AutoDockTermWeights305.__init__(self)
        self.terms = []
        
        # might have to set the ms for each term
        self.scorer =  WeightedMultiTerm(self.ms)
        self.estat =   Electrostatics(self.ms)
        self.hbond =   HydrogenBonding(self.ms)
        self.vdw   =   VanDerWaals(self.ms)
        self.ds    =   Desolvation(self.ms)     
        self.add_term(self.estat,self.estat_weight)
        self.add_term(self.hbond, self.hbond_weight)
        self.add_term(self.vdw, self.vdw_weight)
        self.add_term(self.ds, self.dsolv_weight)

        self.pyatomset1 = pyatomset1
        self.pyatomset2 = pyatomset2
        
    def set_molecular_system(self, ms):
        """ ms, a MolecularSystem, manages which of its entity_sets is 'receptor'
        and which 'ligand' via its configuration tuple and 
        maintains the corresponding pairwise distance matrix. 
        
        'set_molecular_system' checks that the currently designated entity_sets have
        attributes required by this scorer class.
        """
        
        self.scorer.set_molecular_system(ms)
        for term in self.terms:
            term[0].set_molecular_system(ms)
        self.ms = ms
       
    def add_term(self, term, weight=1.0):
        """add the term and weight as a tuple to the list of terms.
        """
        if hasattr(self, 'ms'):
            term.set_molecular_system(self.ms)
        self.scorer.add_term(term,weight)
        self.terms.append( (term, weight) )
        
       
    def get_score(self):
        return self.scorer.get_score()
   
    def get_score_per_term(self):
        scorelist = []
        for term, weight in self.terms:
            scorelist.append( weight*term.get_score() )
        return scorelist

    def get_score_array(self):
        # add up vdw, estat and hbond
        t = self.terms[0]
        # do you really want the list of arrays ? or a list of number for each
        # scoring object?

        array = Numeric.array(t[0].get_score_array()) * t[1]
        for term, weight in self.terms[1:]:
            array = array + weight* Numeric.array(term.get_score_array())

        self.array = array
        
        return self.array

    def labels_atoms_w_nrg(self,score_array):
      """ will label each atoms with a nrg score """
      # label each first atom by sum of its ad3 interaction energies 
      if self.pyatomset1 is None or self.pyatomset2 is None: return
      firstAts = self.pyatomset1
      for i in range(len(firstAts)):
        a = firstAts[i]
        vdw_hb_estat_ds =Numeric.add.reduce(score_array[i])
        setattr(a, self.prop, vdw_hb_estat_ds)

      # label each second atom by sum of its vdw interaction energies
      secondAts = self.pyatomset2
      swap_result = Numeric.swapaxes(score_array,0,1)
      for i in range(len(swap_result)):
          a = secondAts[i]
          vdw_hb_estat_ds =Numeric.add.reduce(swap_result[i])
          setattr(a, self.prop, vdw_hb_estat_ds)
                      




##       for i in range(len(firstAts)):
##         a = firstAts[i]
##         vdw_hb_estat = Numeric.add.reduce(score_array[i])
##         if a.element=='O':
##           setattr(a, self.prop, .236+vdw_hb_estat)   #check this
##         elif a.element=='H':
##           setattr(a, self.prop, .118+vdw_hb_estat)   #check this
##         else:
##           setattr(a, self.prop, Numeric.add.reduce(self.dsolv_array[i])+vdw_hb_estat)

##       # label each second atom by sum of its vdw interaction energies
##       secondAts = self.pyatomset2
##       swap_result = Numeric.swapaxes(score_array,0,1)
##       swap_dsolv = Numeric.swapaxes(self.dsolv_array,0,1)
##       for i in range(len(swap_result)):
##         a = secondAts[i]
##         vdw_hb_estat = Numeric.add.reduce(swap_result[i])
##         if a.element=='O':
##           setattr(a, self.prop, .236+vdw_hb_estat)   #check this
##         elif a.element=='H':
##           setattr(a, self.prop, .118+vdw_hb_estat)   #check this
##         else:
##           setattr(a, self.prop, Numeric.add.reduce(swap_dsolv[i])+vdw_hb_estat)
    
    

# AutoDock305Scorer
