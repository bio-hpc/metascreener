########################################################################
#
# Date: 2013 Authors: Pradeep Ravindranath, Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2013
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/bin/pdbqtFromGenes.py,v 1.1 2013/11/15 22:46:42 sanner Exp $
#
# $Id: pdbqtFromGenes.py,v 1.1 2013/11/15 22:46:42 sanner Exp $
#

#!/usr/bin/env pythonsh
import sys, pdb
from time import time
from bhtree import bhtreelib
import numpy

t0 =  time()                        # Stores the time (float) at the start of the program

#if len(sys.argv)==1:  ## print help msg if no input is given
#    sys.argv.append('-help')

from AutoDockFR.Docking import AutoDockFR
from AutoDockFR.Param import Params

input=Params(args=sys.argv[1:])
#MLDprint input.optList.setting


#pdb.run("adfr=AutoDockFR(input)")
adfr = AutoDockFR(input)

pop = adfr.docking.pop
pop._size(1)

genes = [0.13603212362497852, 0.9007457341791795, 0.23543403235539598, 0.61475642797471, 0.49233618465537876, 0.48810888616323156, 0.498047060440614, 0.16033415094870368, 0.5921503060633838, 0.4144667892899728, 0.07720952490316424, 0.048759239854327556, 0.023700881258877662, 0.5004399757546709, 0.018887344386127325, 0.22678723340162635, 0.7444179100810082, 0.5096166379005564, 0.04767568971573344, 0.34105411897393195, 0.8974919181550925, 0.9303271939853316, 0.9202649075049036, 0.6217615978620916, 0.978582479174044, 0.015184883206871867, 0.5956584257419131, 0.09439971446100225, 0.06620363269203487, 0.7728487513525669, 0.33229263563282113, 0.03242572911382919, 0.9153372835991459, 0.11917317894162514, 0.3942628872898461]
ind = pop[0]
for i in range(len(ind)):
    ind[i]._value = genes[i]

fscore = ind.score()
adfr.docking.search.saveIndividualPDBQT(ind, "result.pdbqt")
