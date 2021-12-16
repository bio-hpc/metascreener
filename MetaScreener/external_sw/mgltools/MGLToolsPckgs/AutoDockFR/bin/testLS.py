#!/usr/bin/env pythonsh
import sys, pdb
from time import time
#sys.path.insert(0,'/mgl/ms4/yongzhao/dev24')
#sys.path.insert(0, '.')
from bhtree import bhtreelib
import numpy

## import psyco
## psyco.log()
## psyco.profile()

t0 =  time()                        # Stores the time (float) at the start of the program
repeat=1

if len(sys.argv)==1:  ## print help msg if no input is given
    sys.argv.append('-help')

from AutoDockFR.Docking import AutoDockFR
from AutoDockFR.Param import Params


input=Params(args=sys.argv[1:])
#MLDprint input.optList.setting

#pdb.run("adfr=AutoDockFR(input)")
adfr = AutoDockFR(input)

from MolKit import Read

def foo(dockingObject, score_flag=False):
    print 'AAAAAA', dockingObject

from AutoDockFR.orderRefAtoms import orderRefMolAtoms

## if adfr.setting['gridRRL']:
##     # Add the gscorer to the ADCScorer as gridScorer
##     # Will then use grid to calculate RRL score
## 	##
## 	## setup grid-based scorer for ligand
## 	##
## 	# set of ligand atoms ordered according to FT

## 	ligAts = adfr.docking.ligandSet
##         #FIXME THIS IS NOT HOW YOU SHOULD GET THE MAP NAMES
##         import os
## 	system = os.path.basename(adfr.setting['Receptor'])[:4]
## 	###system = (adfr.setting['mapName'])#[:4]

## 	from AutoDockFR.gridScorer import GridScorer
## 	gscorer = GridScorer(ligAts, system)

## 	adfr.docking.scoreObject.gridScorer = gscorer
## 	#adfr.docking.scoreObject.RRLmolSyst.scorer = gscorer


###        import pdb
###        pdb.set_trace()

## hack bias torsion for 1ppc bond
## means = [[67.,187], [43.,163], [270.,70], [17.,137], [336.,96], [29.,149], [80.,200], [53.,173]]

## for i, torMotion in enumerate(adfr.docking.gnm.motionObjs[2:]):
##     normMean = [m/360. for m in means[i]]
##     torMotion.setGoodGenes(normMean, [20./360.]*len(normMean))

# Sets a callback to do RMSD calc after each GA generation
###########newly added################
gscorer=None
if adfr.setting['gridMaps']:
    gscorer = adfr.docking.scoreObject.gridScorer
  
if gscorer:
    goodc = gscorer.fixTranslation(adfr.docking)
    #print goodc

def writePopulation(adfr, prefix):
    # write population
    ligmol = adfr.docking.ligandSet[0].top
    ligFile = adfr.docking.ligandFile
    from MolKit import Read
    movMol = Read(ligFile)[0]
    # order movAtoms to match order in tree
    treeOrderedLigAtoms = orderRefMolAtoms(movMol.allAtoms, adfr.docking.ligandSet)

    for ni, ind in enumerate(pop):
        a, b, newCoords = ind.toPhenotype(ind)

        # assing coordinates from tree to ligand atoms ordered according to tree
        treeOrderedLigAtoms.updateCoords(newCoords)

        ligFilename = "%s%d.pdbqt"%(prefix, ni)
        # write with ligand with newCoords sorted to match order in ligand file
        ligmol.parser.write_with_new_coords( movMol.allAtoms.coords, filename=ligFilename)


    ## for i, ind in enumerate(pop):
    ##     origScore = ind.scorer.score(ind, RR_L=False, L_L=True)
    ##     new, nbSteps = ls.search(ind, max_steps=1000, MAX_FAIL=4, MIN_VAR=0.001,
    ##                              absMinVar=None, search_rate=1.0, mode='conformation')
    ##     #a, b, newCoords = new.toPhenotype(new)
    ##     #print 'anchor %d %s'%(i, str(newCoords[0]))

    ##     newScore = new.scorer.score(new, RR_L=False, L_L=True)
    ##     pop[i] = new
    ##     print "ind %d IE went from %9.3f to %9.3f in %d"%(i, origScore, newScore, nbSteps)

    ## print 'conf mini Done in', time()-t0
    ## ## writePopulation(adfr, 'cmini')

    ## t0 = time()
    ## for i, ind in enumerate(pop):
    ##     origScore = ind.scorer.score(ind)
    ##     new, nbSteps = ls.search(ind, max_steps=1000, MAX_FAIL=30, MIN_VAR=0.001,
    ##                              absMinVar=None, search_rate=1.0, mode='all')

    ##     newScore = new.scorer.score(new)
    ##     pop[i] = new
    ##     print "ind %d E went from %9.3f to %9.3f in %d"%(i, origScore, newScore, nbSteps)

    ## print 'glob mini Done in', time()-t0
    ## writePopulation(adfr, 'mini')



#if adfr.setting['constraint'] or adfr.setting['constraint_ls']:
pop = adfr.docking.pop
pop._size(adfr.setting['GA_pop_size'])
## for i, ind in enumerate(pop):
##     ind.randomize()
##     ie = ind.scorer.score(ind, L_L=True, RR_L=False)
##     e = ind.scorer.score(ind, L_L=False, RR_L=True)
##     print 'orig %d %9.3f %15.3f %15.3f'%(i, ie, e, ind.evaluate(force=1))
    #writePopulation(adfr, 'orig')

if adfr.setting['constraint']:
    #print 'randomizing ind until ok'
    #t0 = time()
    #for ni, ind in enumerate(pop):
    #    ind.randomize(1000)
    import os
    print 'reading population from constrained500pop.py'
    if os.path.exists('constrained500pop.py'):
        gl = {}
        execfile('constrained500pop.py', gl)
        population = gl['population']
        for ii, ind in enumerate(pop):
            for gi in range(len(ind)):
                pop[ii][gi]._value = population[ii][gi]
            print 'orig %d %15.3f'%(ii,ind.evaluate(force=1))
            #ie = ind.scorer.score(ind, L_L=True, RR_L=False)
            #e = ind.scorer.score(ind, L_L=False, RR_L=True)
            #print 'orig %d %9.3f %15.3f %15.3f'%(ii, ie, e, ind.evaluate(force=1))

    ## goodPointsBHT = bhtreelib.BHtree(goodc, None, 10)
    ## result = numpy.zeros( (5000,), 'i' )
    ## dist2 = numpy.zeros( (5000,), 'f' )
    ## bht = goodPointsBHT
    ## t0 = time()
    ## emap = gscorer.maps['e']
    ## ox, oy, oz = emap.origin
    ## sx, sy, sz =  emap.stepSize
    ## nbptx, nbpty, nbptz = emap.data.shape
    ## sizeX, sizeY, sizeZ = boxDim = ((nbptx-1)*sx, (nbpty-1)*sy, (nbptz-1)*sz)
    ## ex = ox + sizeX
    ## ey = oy + sizeY
    ## ez = oz + sizeZ
    ## ctsum = 0
    ## for ni, ind in enumerate(pop):
    ##     maxCt = 1000
    ##     minClash = None
    ##     done = False
    ##     maxnb = 0
    ##     ct = 0
        
    ##     while not done:
    ##         ind.randomize()
    ##         RR_coords, FR_coords, L_coords = ind.toPhenotype(ind)
    ##         minx, miny, minz = numpy.min(L_coords, 0)
    ##         if minx <= ox:
    ##             ct += 1
    ##             continue
    ##         if miny <= oy:
    ##             ct += 1
    ##             continue
    ##         if minz <= oz:
    ##             ct += 1
    ##             continue

    ##         maxx, maxy, maxz = numpy.max(L_coords, 0)
    ##         if maxx >= ex:
    ##             ct += 1
    ##             continue
    ##         if maxy >= ey:
    ##             ct += 1
    ##             continue
    ##         if maxz >= ez:
    ##             ct += 1
    ##             continue
            
    ##         noClash = True
    ##         minnb = 1000000
    ##         for c in L_coords: # loop over ligand atoms
    ##             #nb = bht.closePointsDist2(tuple(c), 2.0, result, dist2)
    ##             #rc = 0
    ##             #for i in range(nb):
    ##             #    if dist2[i] < 4.0:
    ##             #        rc +=1
    ##             #if rc != nb: print rc, nb
    ##             #nb = rc
    ##             nb = bht.closePoints(tuple(c), 2.0, result)
    ##             if nb < minnb: # keep track of worst clash
    ##                 minnb = nb
    ##         if minnb > 0:
    ##             done = True  
    ##             print 'individual %d %d attempts'%(ni, ct)
    ##         else:
    ##             if minnb > maxnb:
    ##                 maxnb = minnb
    ##                 minClash = ind.clone()
    ##             ct += 1
    ##             if ct>maxCt:
    ##                 for i in range(len(ind)):
    ##                     ind[i]._value = minClash._value

    ##                 done = True
    ##                 print
    ##                 print 'individual %d %d attempts %d/200'%(ni, ct, maxnb)
    ##         ## 	if nb<300:
    ##         ## 	    if nb > maxnb:
    ##         ## 	        maxnb = nb
    ##         ## 		minClash = ind.clone()
    ##         ## 		print 'individual %d %d/300'%(ni, nb)
    ##         ## 	    ct += 1
    ##         ## 	    if ct>maxCt:
    ##         ## 	        noClash = True
    ##         ## 		for i in range(len(ind)):
    ##         ## 		    ind[i]._value = minClash[i]._value
    ##         ## 	    else:
    ##         ## 	        noClash = False
    ##         ## 		break
    ##         ## if noClash:
    ##         ##     print 'individual %d %d attempts'%(ni, ct)
    ##         ## 	done = True
    ##     ctsum+=ct
    ## print 'Done in', time()-t0
    ## print 'avg', float(ctsum)/len(pop)

    ## f = open('constrained500pop.py', 'w')
    ## f.write("population = [\n")
    ## for ind in pop:
    ##     f.write("%s,\n"%str(ind.values()))

    ## f.write("]\n")
    ## f.close()
                
                       
#if adfr.setting['constraint'] or adfr.setting['constraint_ls']:
#    for i, ind in enumerate(pop):
#        ie = ind.scorer.score(ind, L_L=True, RR_L=False)
#        e = ind.scorer.score(ind, L_L=False, RR_L=True)
#        print 'const %d %9.3f %9.3f'%(i, ie, e)

    #writePopulation(adfr, 'b4mini')

def minimizePop(mode, **LSkw):
    #pop = adfr.docking.pop
    #pop._size(size)
    #for ind in pop:
    #    ind.randomize()

    t0 = time()
    from AutoDockFR.GA import SolisWet
    ls = SolisWet(adfr.setting['GA_localsearchrate'],
                  adfr.setting['GA_LocalSearchMaxFail'],
                  adfr.setting['GA_LocalSearchMaxSuccess'],
                  adfr.setting['GA_LocalSearchMinVar'],
                  adfr.setting['GA_LocalSearchFactorContraction'],
                  adfr.setting['GA_LocalSearchFactorExpansion'],
                  adfr.setting['GA_LocalSearchMaxIts'])
    minimize = adfr.docking.search.minimize
    adfr.docking.search.localSearch = ls
    result = {}
    result['old_ie'] = []
    result['old_e'] = []
    result['new_ie'] = []
    result['new_e'] = []
    result['steps'] = []
    result['time'] = []
    
    kw = {'max_steps':1000, 'MAX_FAIL':len(pop[0])*2,
          'MIN_VAR':0.001, 'absMinVar':None, 'search_rate':1.0}
    kw.update(LSkw)

    if mode == 'simple':
        for i, ind in enumerate(pop):
            old_ie = ind.scorer.score(ind, RR_L=False, L_L=True)
            old_e = ind.scorer.score(ind, RR_L=True, L_L=False)
            t0 = time()
            #new, nbSteps = ls.search(ind, **kw)
            new = minimize(ind, nbSteps=10, noImproveStop=2, max_steps=200, MAX_FAIL=15)
            dt = time()-t0
            new_ie = ind.scorer.score(new, RR_L=False, L_L=True)
            new_e = ind.scorer.score(new, RR_L=True, L_L=False)
            print "%3d %4d %15.3f %15.3f %15.3f %15.3f %15.3f %f"%(
                i, -1, -old_ie, -new_ie, -old_e, -new_e, -new.score(), dt)
            result['old_ie'].append(-old_ie)
            result['old_e'].append(-old_e)
            result['new_ie'].append(-new_ie)
            result['new_e'].append(-new_e)
            result['steps'].append(-1)
            result['time'].append(dt)
        return result

    if mode == 'conf+all':
        for i, ind in enumerate(pop):
            old_ie = ind.scorer.score(ind, RR_L=False, L_L=True)
            old_e = ind.scorer.score(ind, RR_L=True, L_L=False)
            t0 = time()
            new, nbSteps = ls.search(ind, mode='conformation', **kw)
            new, nbSteps = ls.search(ind, mode='all', **kw)
            dt = time()-t0
            new_ie = ind.scorer.score(new, RR_L=False, L_L=True)
            new_e = ind.scorer.score(new, RR_L=True, L_L=False)
            print "%3d %4d %15.3f %15.3f %15.3f %15.3f %f"%(
                i, nbSteps, -old_ie, -new_ie, -old_e, -new_e, dt)
            result['old_ie'].append(-old_ie)
            result['old_e'].append(-old_e)
            result['new_ie'].append(-new_ie)
            result['new_e'].append(-new_e)
            result['steps'].append(nbSteps)
            result['time'].append(dt)
        return result

def saveResult(filename, resultDict):
    import pickle
    pkl_file = open(filename, 'wb')
    pkl_file.write(pickle.dumps(resultDict))
    pkl_file.close()

def loadResult(filename):
    import pickle
    pkl_file = open(filename, 'rb')
    result = pickle.load(pkl_file)
    pkl_file.close()
    return result

const = adfr.setting['constraint']
fixed = adfr.setting['fixMaps']
result = minimizePop('simple')
saveResult('mini500Fixed%dconst%d_10_2_200_15.pkl'%(int(fixed), int(const)), result)
#result = minimizePop('simple', MAX_FAIL=30)
#saveResult('simple500Fixed%dconst%d.pkl'%(int(fixed), int(const)), result)
#result = minimizePop('conf+all', MAX_FAIL=30)
#saveResult('confAll500Fixed%dconst%d.pkl'%(int(fixed), int(const)), result)
print 'FIXED MAPS%dCONST%d'%(int(fixed), int(const))
raise

#for i, ind in enumerate(pop):
#    a, b, newCoords = ind.toPhenotype(ind)
#    print 'anchor %d %s'%(i, str(newCoords[0]))
#    ind.scorer.score()
#    ind.scorer.printAllScoreTerms(ind)
#    print "-------------------------------------------------------------------"
    
if adfr.setting['constraint_ls']:
    t0 = time()
    anneal = adfr.docking.search.anneal
    from AutoDockFR.GA import SolisWet
    ls = SolisWet(adfr.setting['GA_localsearchrate'], adfr.setting['GA_LocalSearchMaxFail'],\
                  adfr.setting['GA_LocalSearchMaxSuccess'], adfr.setting['GA_LocalSearchMinVar'],
                  adfr.setting['GA_LocalSearchFactorContraction'],\
                  adfr.setting['GA_LocalSearchFactorExpansion'],adfr.setting['GA_LocalSearchMaxIts'])

    #for ind in pop:
    #    print ind.score(),
    #    new, nbSteps = ls.search(ind, max_steps=1000, MAX_FAIL=len(ind)*2, MIN_VAR=0.001,
    #			     absMinVar=None, search_rate=1.0)
    #    print new.score()

    for i, ind in enumerate(pop):
        origScore = ind.scorer.score(ind, RR_L=False, L_L=True)
        new, nbSteps = ls.search(ind, max_steps=1000, MAX_FAIL=4, MIN_VAR=0.001,
                                 absMinVar=None, search_rate=1.0, mode='conformation')
        #a, b, newCoords = new.toPhenotype(new)
        #print 'anchor %d %s'%(i, str(newCoords[0]))

        newScore = new.scorer.score(new, RR_L=False, L_L=True)
        pop[i] = new
        print "ind %d IE went from %9.3f to %9.3f in %d"%(i, origScore, newScore, nbSteps)

    print 'conf mini Done in', time()-t0
    ## writePopulation(adfr, 'cmini')

    t0 = time()
    for i, ind in enumerate(pop):
        origScore = ind.scorer.score(ind)
        new, nbSteps = ls.search(ind, max_steps=1000, MAX_FAIL=30, MIN_VAR=0.001,
                                 absMinVar=None, search_rate=1.0, mode='all')

        newScore = new.scorer.score(new)
        pop[i] = new
        print "ind %d E went from %9.3f to %9.3f in %d"%(i, origScore, newScore, nbSteps)

    print 'glob mini Done in', time()-t0
    writePopulation(adfr, 'mini')

    # print population
    #for ind in pop:
    #    print ['%8.3f'%v for v in ind.get_values()]

    ## # write population
    ## ligmol = adfr.docking.ligandSet[0].top
    ## ligFile = adfr.docking.ligandFile
    ## from MolKit import Read
    ## movMol = Read(ligFile)[0]
    ## for ni, ind in enumerate(pop):
    ##     a, b, newCoords = ind.toPhenotype(ind)

    ##     # order movAtoms to match order in tree
    ##     treeOrderedLigAtoms = orderRefMolAtoms(movMol.allAtoms, adfr.docking.ligandSet)
    ##     # assing coordinates from tree to ligand atoms ordered according to tree
    ##     treeOrderedLigAtoms.updateCoords(newCoords)

    ##     ligFilename = "initPop%d.pdbqt"%(ni)
    ##     print ligFilename
    ##     # write with ligand with newCoords sorted to match order in ligand file
    ##     ligmol.parser.write_with_new_coords( movMol.allAtoms.coords, filename=ligFilename)
######################## ############

from mglutil.math.rmsd import RMSDCalculator
for ref in adfr.setting['rmsdRef']:
    refMol=Read(ref)[0]
    refAts=refMol.getAtoms()

    ligAts = adfr.docking.ligandSet
    # Make sure the reference atoms match the order of the atoms in the FT
    sortedRefAts = orderRefMolAtoms(refAts, ligAts)

    adfr.docking.search.addCallback('postGeneration', adfr.docking.GA_PopScoreRMSD_cb, sortedRefAts.coords, score_flag=True, popFile='generation_job%s' % adfr.setting['jobID'])
    RMSDcalc = RMSDCalculator(refCoords = sortedRefAts.coords)
    adfr.docking.search.rmsdCalculators.append(RMSDcalc)

print 'search box size', adfr.docking.LigandTree.getAllMotion()[0].motionList[1].boxDim
print 'search box center', adfr.docking.LigandTree.getAllMotion()[0].motionList[2].point2

# start docking
#pdb.run("adfr.dock()")
if adfr.setting['constraint'] or adfr.setting['constraint_ls']:
    for ind in pop:
        ind.evaluate(force=1)
        #ind.scorer.printAllScoreTerms(ind)

if adfr.setting['constraint'] or adfr.setting['constraint_ls']:
    adfr.dock(pop)
else:
    adfr.dock()


#adfr.docking.GA_PopScoreRMSD_cb(sortedRefAts.coords, score_flag=True, popFile='lastGenration.py')

print "Execution time runadfr: %.1f hours, %.1f minutes, %.1f seconds\n" % ((time() -  t0)/3600, (time() -  t0)/60, time() -  t0)
