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
# $Header: /opt/cvs/AutoDockFR/bin/runadfr.py,v 1.9 2014/07/31 18:29:45 pradeep Exp $
#
# $Id: runadfr.py,v 1.9 2014/07/31 18:29:45 pradeep Exp $
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
#MLDprint input.optList.setting

#pdb.run("adfr=AutoDockFR(input)")
adfr = AutoDockFR(input)

from MolKit import Read

from AutoDockFR.orderRefAtoms import orderRefMolAtoms
maxTry = adfr.setting['constraintMaxTry']
## gscorer=None
## if adfr.setting['gridMaps']:
##     gscorer = adfr.docking.scoreObject.gridScorer

## if gscorer:
##     gscorer.fixTranslation(adfr.docking)

pop = adfr.docking.pop
pop._size(adfr.setting['GA_pop_size'])
## pop._size(1)

## transToCenter = adfr.docking.ligRoot.motion.motionList[2]
## t = numpy.array(transToCenter.point1)- numpy.array(transToCenter.point2)
## boxDim = adfr.docking.LigandTree.getAllMotion()[0].motionList[1].boxDim
## tpercent = 0.5+t[0]/boxDim[0], 0.5+t[1]/boxDim[1], 0.5+t[2]/boxDim[2]
## refGenes = [0.5, 0.5, 0.5, 1.,
##             tpercent[0], tpercent[1], tpercent[2]] + \
##             [0.]*8
## values = [7./9., 0,0] + refGenes
## for i,v in enumerate(values):
##     pop[0][i]._value = v

## import pdb
## #pdb.run("a,b,c = pop[0].toPhenotype()")
## pop[0].score()
## adfr.docking.search.savePopulationPDBQT('test_lig', 0,
##                                         pop=pop, recFilename='test_rec')

## raise
## values = [0.062, 0,0,0,0] + refGenes
## for i,v in enumerate(values):
##     pop[0][i]._value = v


#import pdb
#pdb.run("pop[0].toPhenotype()")

if adfr.setting['search']=='GA2_2':
    # perform local search either around:
    # - rmsdRef[0] structure with genes for this structure given in refGenes
    # - input ligand with refGenes ='identity'
    from random import uniform, gauss
    genes = adfr.setting['refGenes']
    if genes=='identity':
        transToCenter = adfr.docking.ligRoot.motion.motionList[2]
        t = numpy.array(transToCenter.point1)- numpy.array(transToCenter.point2)
        boxDim = adfr.docking.LigandTree.getAllMotion()[0].motionList[1].boxDim
        tpercent = 0.5+t[0]/boxDim[0], 0.5+t[1]/boxDim[1], 0.5+t[2]/boxDim[2]
        refGenes = [0.5, 0.5, 0.5, 1.,
                    tpercent[0], tpercent[1], tpercent[2]] + \
                    [0.]*(len(pop[0])-7)
        adfr.setting['refGenes'] = refGenes

    ind = pop[0].clone()
    for i,v in enumerate(adfr.setting['refGenes']):
        ind[i]._value = v
    score = ind.score()
    rmsd = adfr.docking.search.rmsdCalculators[0].computeRMSD(ind.phenotype[2])
    print 'REFERENCE SCORE: %f RMSD %f'%(score, rmsd)

    # create individuals from pop[1] t0 pop[-1] that are within 2 angstroms
    # RMSD of pop[0]
    pop = adfr.initialPopulationForLocalSearch(
        adfr.setting['GA_pop_size'], ind)

    #adfr.docking.search.savePopulationPDBQT('rmsd2Min', 'initial')

# FIXME (MS) This should happen in AutoDockFR
# we should also be able to specify a population file to strat with
elif not adfr.setting['usePop']:
    print "Generating initial population of size %d and contraintMaxTry of %d"%(
        adfr.setting['GA_pop_size'],adfr.setting['constraintMaxTry'])
    for i, ind in enumerate(pop):
        ## having maxTry != 0 will contraint atoms
        t0 = time()
        attempts = ind.randomize(maxTry=maxTry)
        print 'individual %3d randomized in %4d attempts %.5f(s) %.3f'%(
            i, attempts, time()-t0, -ind._fitness_score)
    ###fileName = 'init_maxtry_%d'%(maxTry)
    ###adfr.docking.search.savePopulation(fileName,0)

    ## from AutoDockFR.GA import SolisWet
    ## ls = SolisWet() 
    ## # FIXME (MS) this should also happen in AutoDockFR 
    ## if adfr.setting['minimize']:
    ##     minimize_param = adfr.setting['minimize']
    ##     print "Minimizing using ",minimize_param
    ## minimize = adfr.docking.search.minimize
    ## t00 = time()

    ## for i, ind in enumerate(pop):
    ##     #old_ie = ind.score(ind, RR_L=False, L_L=True)
    ##     #old_e = ind.score(ind, RR_L=True, L_L=False)
    ##     ind._score = ind.score()
    ##     t0 = time()
    ##     #new, nbSteps = ls.search(ind, **kw)
    ##     # FIXME: it would be nice if minimize returned the number of steps info
    ##     # or at least kept it si that we can use it to understand behavior
    ##     if adfr.setting['minimize']:
    ##         configure=adfr.docking.search.configure_minimize
    ##         #configure(minimize_param)
    ##         ls = SolisWet(configure(minimize_param))
    ##     adfr.docking.search.localSearch=ls 
    ##     new = minimize(ind) # nbSteps=nbSteps, noImproveStop=noImproveStop, max_steps=max_steps,
    ##                    #MAX_FAIL=MAX_FAIL, MIN_VAR= MIN_VAR)
    ##     dt = time()-t0
    ##     new._score = new.score()
    ##     #new_ie = ind.score(new, RR_L=False, L_L=True)
    ##     #new_e = ind.score(new, RR_L=True, L_L=False)
    ##     print "minimized %3d %15.3f -> %15.3f in %5.2f"%(
    ##         i, -ind._score , -new._score, dt)
    ##     pop[i] = new
    ## print 'mini Done in', time()-t00
    ## ###fileName = 'init_maxtry_%d_minimize'%(maxTry)
    ## ###adfr.docking.search.savePopulation(fileName,0)
elif adfr.setting['usePop']:
    ###pop = adfr.docking.pop
    ###pop._size(adfr.setting['GA_pop_size'])

    d = {}
    ###fileName = 'init_maxtry_%d_minimize_0000'%(maxTry)
    fileName = adfr.setting['usePop']
    execfile(fileName, d)
    for i, ind in enumerate(pop):
        for j in range(len(ind)):
            ind[j]._value = d['pop'][i][0][j]
        print -ind.score()

## if adfr.setting['fixMaps']:
##     if adfr.setting['gridMaps'][0].find('fixed') == -1:
##         print "Use fixed maps!!!"
##         sys.exit(1)

## from mglutil.math.rmsd import RMSDCalculator
## for ref in adfr.setting['rmsdRef']:
##     refMol=Read(ref)[0]
##     refAts=refMol.getAtoms()

##     ligAts = adfr.docking.ligandSet
##     # Make sure the reference atoms match the order of the atoms in the FT
##     sortedRefAts = orderRefMolAtoms(refAts, ligAts)
##     RMSDcalc = RMSDCalculator(refCoords = sortedRefAts.coords)
##     adfr.docking.search.rmsdCalculators.append(RMSDcalc)


#adfr.docking.search.addCallback('postGeneration', adfr.docking.GA_PopScoreRMSD_cb)
#                                popFile='generation_job%s' % adfr.setting['jobID'])


print 'search box size', adfr.docking.LigandTree.getAllMotion()[0].motionList[1].boxDim
print 'search box center', adfr.docking.LigandTree.getAllMotion()[0].motionList[2].point2

# start docking
#pdb.run("adfr.dock()")
#if adfr.setting['constraintMaxTry']:
#for ind in pop:
#    if not hasattr(ind, '_score'):
#        ind.evaluate(force=1)
#    #ind.scorer.printAllScoreTerms(ind)

## ind = [0.15700297339390745, 0.7451602707462004, 0.11933272356620601, 0.5055953057315851, 0.22611740587340426, 0.5239786295807208, 0.5213937607767014, 0.7874872104163948, 0.9265792887321761, 0.6412214761592581, 0.9670963234779929, 0.5406061173754328, 0.8669863429112867, 0.05081628176550114, 0.6458833320922571, 0.8833884491993559]
## for i,v in enumerate(ind):
##     print adfr.docking.search.pop[0][i]._value, v
##     adfr.docking.search.pop[0][i]._value = v
## 
## scorer = adfr.docking.scoreObject
## 
## indi = adfr.docking.search.pop[0]
## indi.score()
## print adfr.docking.scoreObject.printAllScoreTerms(indi)
## 
## for l in scorer.getPerAtomBreakdown(adfr.docking.scoreObject.LLmolSyst): print l
## 
adfr.dock(pop)
## 
## terms = scorer.LLmolSyst.scorer.get_terms()
## names = scorer.LLmolSyst.scorer.names
## for n,t in zip(names, terms):
##   print n, t
## 
## import numpy; 
## array = numpy.array(terms[2].get_score_array(), 'f')
## for v,n in zip(array[1], adfr.docking.ligandSet.name):
##    print n, v
## 
## d = scorer.LLmolSyst.get_distance_matrix(1, 0)
## d[0]
## 
## for i in range(24):
##   print i, adfr.docking.ligandSet.name[i], scorer.LLmolSyst.is_masked(2,i)
## 
## dir(scorer.LLmolSyst)
## 
print "Execution time runadfr: %.1f hours, %.1f minutes, %.1f seconds\n" % ((time() -  t0)/3600, (time() -  t0)/60, time() -  t0)


