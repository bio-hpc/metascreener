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
# $Header: /opt/cvs/AutoDockFR/bin/generatePopulation.py,v 1.3 2013/11/14 19:20:09 pradeep Exp $
#
# $Id: generatePopulation.py,v 1.3 2013/11/14 19:20:09 pradeep Exp $
#

#!/usr/bin/env pythonsh
import sys, pdb
from time import time
from bhtree import bhtreelib
import numpy

t0 =  time()                        # Stores the time (float) at the start of the program

if len(sys.argv)==1:  ## print help msg if no input is given
    sys.argv.append('-help')

from AutoDockFR.Docking import AutoDockFR
from AutoDockFR.Param import Params


input=Params(args=sys.argv[1:])
adfr = AutoDockFR(input)

from MolKit import Read

from AutoDockFR.orderRefAtoms import orderRefMolAtoms
maxTry = adfr.setting['constraintMaxTry']
gscorer=None
if adfr.setting['gridMaps']:
    gscorer = adfr.docking.scoreObject.gridScorer

#if gscorer:
#    goodc = gscorer.fixTranslation(adfr.docking)

pop = adfr.docking.pop
pop._size(adfr.setting['initPopSize'])
#maxTry = adfr.setting['constraintMaxTry']
for i, ind in enumerate(pop):
    ## having maxTry != 0 will contraint atoms
    t0 = time()
    attempts = ind.randomize(maxTry=maxTry)
    print 'individual %3d randomized in %4d attempts %.2f(s) %.3f'%(
        i, attempts, time()-t0, ind._score)
###fileName = 'init_maxtry_%d'%(maxTry)
###adfr.docking.search.savePopulation(fileName,0)

from AutoDockFR.GA import SolisWet
ls = SolisWet()
# FIXME (MS) this should also happen in AutoDockFR 
if adfr.setting['GAminimize']:
    minimize_param = adfr.setting['GAminimize']
    print "Minimizing using ",minimize_param
minimize = adfr.docking.search.minimize
t00 = time()

for i, ind in enumerate(pop):
    ind._score = ind.score()
    t0 = time()
    if adfr.setting['GAminimize']:
        new = minimize(ind, **minimize_param)
    dt = time()-t0
    new._score = new.score()
    print "minimized %3d %15.3f -> %15.3f in %5.2f"%(
        i, -ind._score , -new._score, dt)
    pop[i] = new
print 'mini Done in', time()-t00
fileName =  adfr.setting['popOutName']
adfr.docking.search.savePopulation(fileName,0)

print "Execution time runadfr: %.1f hours, %.1f minutes, %.1f seconds\n" % ((time() -  t0)/3600, (time() -  t0)/60, time() -  t0)
