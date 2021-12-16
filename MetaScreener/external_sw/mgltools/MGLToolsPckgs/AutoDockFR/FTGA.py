# Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

from FlexTree.FT import VERBOSE
import time, types, numpy
from math import sqrt
from random import uniform, random, gauss

## # check if SciPy is installed
## try:
##     foundScipy = False    
##     import scipy
##     foundScipy = True

## except ImportError:
##     #import traceback, sys
##     #type, value, tb = sys.exc_info()
##     #traceback.print_exception(type, value, tb)
##     #import traceback
##     #traceback.print_exc()
##     foundScipy = False

from FlexTree.FTMotions import FTMotion_BoxTranslation, \
     FTMotion_Translation, FTMotion_RotationAboutPointQuat, \
     FTMotion_RotationAboutAxis, FTMotion_Rotamer, FTMotion_SoftRotamer

##
## subclass FTMotion objects to adapt them for GA
## the motion object needs to implement:
##
##  self.getGenes() to return
##    a list of genes corresponding to the currenttransformation
##
##  self.getParam() to return a dictionary ....
##
##  the configure method has to set and handle a gene representation
##
##  setValueFromGenes(self, *args): is a fast of method called by toPhenotype
##  to configure motion objects with minimal overhead as it is doen often
##

class GAFTMotion:
    """
    Base class used to define methods for operating the set of genes assoceated
    with motion a motion object
    """

    def __init__(self, nbGenes=0):
        self.nbGenes = nbGenes # number of genes used by this motion object

        self.cyclicGenes = None  # set to a list of True/False for each genes

        self.hasGoodGenes = False

        
    def perturb(self, genes, amplitude=0.01):
        """
        This method is used to create a smal local perturbation, It is used
        the the SolisWets local search algorithm
        """
        pass
    

    def jitter(self, genes, search_rate, var=None):
        ct = 0
        d = []
        for i in range(len(genes)):
            if search_rate==1.0 or random() < search_rate:
                d.append( gauss(0., var[i]) )
                ct += 1
            else:
                d.append(0)
        return ct, d

        
    def randomize(self, genes):
        """
        default method for randomizing a set of genes corresponding to a motion
        object. By default we generate uniform random values between 0 and 1
        for the gene and set the vale from the gene
        """
        #values = []
        for gene in genes:
            v = uniform(0., 1.)
            #values.append(v)
            gene._value = v
        #self.setValueFromGenes( *values )
    

    def mutate(self, genes, mutation_rate, dev=0.2):
        """
        default method for mutating a set of genes corresponding to a motion object
        By default we call the mutation operator in each gene
        """
        mutated = False
        #import pdb
        #pdb.set_trace()
        for gene in genes:
            if random() < mutation_rate:
                mutated = True
                new = gauss(gene._value, dev)
                length = gene.bounds[1] - gene.bounds[0]
                if new > gene.bounds[1]:
                    if gene.cyclic:
                        #print 'Cyclic mutation1 value: %f ->%f'%(
                        #    new, gene.bounds[0] + (new-gene.bounds[1])%length)
                        new = gene.bounds[0] + (new-gene.bounds[1]%length)
                    else:
                        new = gene.bounds[1]
                elif new < gene.bounds[0]:
                    if gene.cyclic:
                        #print 'Cyclic mutation2 value: %f ->%f'%(
                        #    new, gene.bounds[1] + (new-gene.bounds[0])%length)
                        new = gene.bounds[1] - (gene.bounds[0]-new)%length
                    else:
                        new = gene.bounds[0]
                gene._value = new

        return mutated


    def setValueFromGenes(self, *args):
        raise RuntimeError('ERROR: setValueFromGenes not implemented for %s'%\
                           self.__class__.__name__)

    
class GAFTMotion_Translation(GAFTMotion, FTMotion_Translation):

    def __init__(self, axis=None, points=None, magnitude=None, 
                 name='translation', percent=None, tolerance=None, \
                 beginPoint=None, endPoint=None):

        GAFTMotion.__init__(self, nbGenes=3)
        FTMotion_Translation.__init__(
            self, axis=axis, points=points, magnitude=magnitude, 
                 name=name, beginPoint=beginPoint, endPoint=endPoint)



class GAFTMotion_Rotamer(GAFTMotion, FTMotion_Rotamer):

    def __init__(self, name='discrete_rotamer_motion',
                 sideChainAtoms=None,
                 anchorAtomNames=['CB','CA','C'],
                 index=-1,
                 exclude=[]):

        GAFTMotion.__init__(self, nbGenes=1)
        FTMotion_Rotamer.__init__(
            self, name=name, sideChainAtoms=sideChainAtoms,
                 anchorAtomNames=anchorAtomNames,
                 index=index, exclude=exclude)


    def setValueFromGenes(self, gene):
        #print gene, self.confNB
        #print '************** FUGU', gene.value(), int(gene.value()*self.confNB)
        ##self.configure(index=int(gene.value()*self.confNB))
        #print int(gene*self.confNB)

        self.configure(index=int(gene*self.confNB))

        #print self.configure(index=int(gene*self.confNB))



class GAFTMotion_SoftRotamer(GAFTMotion, FTMotion_SoftRotamer):

    dev = [2, 4, 6, 8] # deviations for jitter

    def __init__(self, residue, anchorAtoms, name=None):

        if name is None:
            name = 'SoftRotamerMotion_%s'%residue.name
        GAFTMotion.__init__(self)
        FTMotion_SoftRotamer.__init__(
            self, residue, anchorAtoms, name=name)
        self.nbGenes = len(self.angDef)
        self.cyclicGenes = [True]*len(self.angDef)


    def jitter(self, genes, search_rate, var=None):
        ct = 0
        d = []
        l = len(genes)
        # compute v such that the deviation depends on the # of CHI
        # we want dev=self.dev[-1] for the last CHI angle and self.dev[-2]
        # for the CHI angle before the last one
        v = 4-l 
        for i in range(l):
            if search_rate==1.0 or random() < search_rate:
                angle = gauss(self.angles[i], self.dev[v+i])
                if angle < 0: angle += 360.
                elif angle > 360: angle -= 360.
                d.append( angle )
                ct += 1
            else:
                d.append(0)
        return ct, d


    def getParam(self):
        """
        returns the GA related parameters
        """
        validParamName =[]
        validParam = []
        for i, val in enumerate(self.angles):
            validParam.append({'type': 'continuous', 'dataType':'float',
                               'mutator': 'gaussian',
                               'min': 0.0, 'max':360.0})
            validParamName.append('devChi%d'%i) 
        return validParamName, validParam


    def getCurrentSetting(self):
        d = {}
        for name, value in self.getParam():
            d[name] = value
        return d

    def getGenes(self):
        return self.angles[:]


    def randomize(self, genes):
        """
        default method for randomizing a set of genes corresponding to a motion
        object. By default we generate uniform random values between 0 and 1
        for the gene and set the vale from the gene
        """
        #values = []
        #genes[0]._value = uniform(0., 0.999999)
        #index = int(genes[0]*self.confNB)
        index = int(uniform(0., 0.999999)*self.confNB)
        dev = self.angDev[index]
        angles = self.angleList[index]
        for i, gene in enumerate(genes):
            #gene._value = 0.0
            angle = gauss(angles[i], dev[i])
            if angle < 0: angle += 360.
            elif angle > 360: angle -= 360.
            gene._value = angle
        #print 'RANDOMIZEDDDD', self.name, index, genes.values()


    def mutate(self, genes, mutation_rate, dev=0.2):
        """
        Method for mutating a setrotameric side chain
        """
        mutated = False
        if random() < mutation_rate:
            self.randomize(genes)
            mutated = True
        return mutated
    

    def setValueFromGenes(self, *genes):
        #print 'SOFTROT genes', genes
        #self.setAngles(genes)
        self.angles[:] = genes[:]
        

## class GAFTMotion_SoftRotamer1(GAFTMotion, FTMotion_SoftRotamer):
##     # first soft rotamer with index and deviations from rotamer
    
##     dev = [2, 4, 6, 8] # deviations for jitter

##     def __init__(
##         self, residue, anchorAtoms, name='discrete_rotamer_motion',
##         sideChainAtoms=None,
##         anchorAtomNames=['CB','CA','C'], index=0, exclude=[]):

##         GAFTMotion.__init__(self, nbGenes=1)
##         FTMotion_SoftRotamer.__init__(
##             self, residue, anchorAtoms, name=name,
##             sideChainAtoms=sideChainAtoms,
##             anchorAtomNames=anchorAtomNames,
##             index=index, exclude=exclude)
##         self.nbGenes = 1 + len(self.angDef)
##         self.cyclicGenes = [False] + [True]*len(self.angDef)


##     def jitter(self, genes, search_rate, var=None):
##         ct = 0
##         d = [0.0]
##         l = len(genes)-1
##         # compute v such that the deviation depends on the # of CHI
##         # we want dev=self.dev[-1] for the last CHI angle and self.dev[-2]
##         # for the CHI angle before the last one
##         v = 3-l 
##         for i in range(1, l+1):
##             if search_rate==1.0 or random() < search_rate:
##                 d.append( gauss(0., self.dev[v+i]) ) # 4-l+i-1
##                 ct += 1
##             else:
##                 d.append(0)
##         return ct, d


##     def getParam(self):
##         """
##         returns the GA related parameters
##         """
##         validParamName =[]
##         validParam = []
##         validParamName.append('percent')
##         validParam.append({'type': 'continuous','dataType':'float',
##                            'mutator': 'gaussian',
##                            'min': 0.0, 'max':1.0})
##         for i, val in enumerate(self.deviations):
##             validParam.append({'type': 'continuous', 'dataType':'float',
##                                'mutator': 'gaussian',
##                                'min': 0.0, 'max':360.0})
##             validParamName.append('devChi%d'%i) 
##         return validParamName, validParam


##     def getGenes(self):
##         return [self.percent] + self.deviations[:]


##     def randomize(self, genes):
##         """
##         default method for randomizing a set of genes corresponding to a motion
##         object. By default we generate uniform random values between 0 and 1
##         for the gene and set the vale from the gene
##         """
##         #values = []
##         genes[0]._value = uniform(0., 0.999999)
##         index=int(genes[0]*self.confNB)
##         dev = self.angDev
##         for i, gene in enumerate(genes[1:]):
##             #gene._value = 0.0
##             gene._value = gauss(0.0, dev[index][i])
##         #print 'RANDOMIZEDDDD', genes.values()
        
##     def setValueFromGenes(self, *genes):
##         #print 'SOFTROT genes', genes
##         self.setRotamer(int(genes[0]*self.confNB), deviations=genes[1:])
        

class GAFTMotion_RotationAboutPointQuat(GAFTMotion,
                                        FTMotion_RotationAboutPointQuat):

    def __init__(self, point=None, quat=None,
                 name='rotation about a point(Quat)', tolerance=None):

        GAFTMotion.__init__(self, nbGenes=4)
        FTMotion_RotationAboutPointQuat.__init__(self, point=point, quat=quat,
                                        name=name, tolerance=tolerance)
        self.qx = 0.5
        self.qy = 0.5
        self.qz = 0.5
        self.qw = 1.


    def getParam(self):
        """
        returns the GA related parameters
        """
        validParamName =[]
        validParam = []
        validParamName.append('qx')
        validParam.append({'type': 'continuous','dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        validParamName.append('qy')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        validParamName.append('qz') 
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        validParamName.append('qw')  
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        return validParamName, validParam
        

    def setValueFromGenes(self, qx, qy, qz, qw):
        # fast method for setting values without going through configure

        # compute quaternion values and normalize it
        a = 2*qx - 1.0
        b = 2*qy - 1.0
        c = 2*qz - 1.0
        d = 2*qw - 1.0
        n1 = 1./sqrt(a*a +b*b +c*c +d*d)
        self.quat[0] = a*n1
        self.quat[1] = b*n1
        self.quat[2] = c*n1
        self.quat[3] = d*n1
        self.qx = qx
        self.qy = qy
        self.qz = qz
        self.qw = qw
        self.updateTransformation()


    def configure(self, qx=None, qy=None, qz=None, qw=None, **kw):

        kw['update'] = False
        if len(kw): FTMotion_RotationAboutPointQuat.configure(self, **kw)

        # handle new qx, qy, qz and qw attributes
        if qx is not None:
            self.quat[0] = 2*qx - 1.0
            
        if qy is not None:
            self.quat[1] = 2*qy - 1.0
            
        if qz is not None:
            self.quat[2] = 2*qz - 1.0
            
        if qw is not None:
            self.quat[3] = 2*qw - 1.0

        # update qx, qy, qz and qw if quat is set
        quat = kw.get('quat', None)
        if quat:
            x,y,z,w = quat
            self.qx = (x+1.0) * 0.5
            self.qy = (y+1.0) * 0.5
            self.qz = (z+1.0) * 0.5
            self.qw = (w+1.0) * 0.5

        self.updateTransformation()


    def getGenes(self):
        return [self.qx, self.qy, self.qz, self.qw] 



class GAFTMotion_RotationAboutAxis(GAFTMotion, FTMotion_RotationAboutAxis):
    
    def __init__(self, axis=None, points=None,
                 angle=0.0, name='rotation about an axis',
                 type='FTMotion_RotationAboutAxis',
                 tolerance=None):
        GAFTMotion.__init__(self, nbGenes=1)
        FTMotion_RotationAboutAxis.__init__(
            self, axis=axis, points=points, angle=angle, name=name,
            type=type, tolerance=tolerance)
        

    def configure(self, angleGene=None, **kw):

        kw['update'] = False
        if len(kw): FTMotion_RotationAboutAxis.configure(self, **kw)

        if angleGene is not None:
            self.angle =  angleGene * 360.0           
            self.angleGene = angleGene

        angle = kw.get('angle')
        if angle:
            self.angleGene = angle/360.

        self.updateTransformation()

        self.means = []
        self.devs = []

        
    def setGoodGenes(self, means, devs):
        # HACK to bias torsions using a list of Gaussians
        self.hasGoodGenes = True
        self.means = means
        self.devs = devs


    def randomize(self, genes):
        """
        default method for randomizing a set of genes corresponding to a motion
        object. We pick one of the gaussians and generated a value fom it
        """
        nb = len(self.means)
        if nb:
            v = int(uniform(0, nb)) # pick a gaussian
            val = gauss(self.means[v], self.devs[v])
            if val < 0:
                val = (val - 1.0)%1.0 # mini + (tmp - maxi)%length
            elif val > 1.0:
                val = 1.0 - (-val)%1.0    # maxi - (mini - tmp)%length
            genes[0]._value = val
        else: # no bias .. flat distribution
            genes[0]._value = uniform(0., 1.)


    def setValueFromGenes(self, angleGene):
        # fast method for setting values without going through configure
        self.angle =  angleGene * 360.0           
        self.angleGene = angleGene
        self.updateTransformation()


    def getGenes(self):
        return [self.angleGene]


    def getParam(self):
        """
        returns the GA related parameters
        """
        validParamName =[]
        validParam = []

        validParamName.append('angleGene')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min':0.0, 'max':1.0
                           })
        
        return validParamName, validParam



class GAFTMotion_BoxTranslation(GAFTMotion, FTMotion_BoxTranslation):

    def __init__(self,  name='translation within a box',
                 boxDim=None, point=None, 
                 percent=None, tolerance=None):

        GAFTMotion.__init__(self, nbGenes=3)
        FTMotion_BoxTranslation.__init__(
            self,  name=name, boxDim=boxDim, point=point, 
            tolerance=tolerance)

        # these represent the point exrpressed in gene values (i.e 0.-1.)
        self.dxGene = 0.5
        self.dyGene = 0.5
        self.dzGene = 0.5
        self.goodGenes = None
        self.nbGoodGenes = 0
        self.geneBounds = [0.0, 1.0]


    def setGoodGenes(self, genes):
        self.hasGoodGenes = True
        mini, maxi = self.geneBounds
        for x,y,z in genes:
            assert mini-x<0.00001 and x-maxi<0.00001 and \
                   mini-y<0.00001 and y-maxi<0.00001 and \
                   mini-z<0.00001 and z-maxi<0.00001 
        self.goodGenes = genes
        self.nbGoodGenes = len(genes)
        

    def randomize(self, genes):
        """
        default method for randomizing a set of genes corresponding to a motion
        object. By default we generate uniform random values between 0 and 1
        for the gene and set the vale from the gene
        """
        nb = self.nbGoodGenes
        if nb:
            v = int(uniform(0, nb))
            for gene, value in zip(genes, self.goodGenes[v]):
                gene._value = value
        else:
            values = []
            for gene in genes:
                v = uniform(0., 1.)
                values.append(v)
                gene._value = v


    def getParam(self):
        """
        get GA-related parametersd sescription
        """
        validParamName =[]
        validParam = []

        validParamName.append('dxGene')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min':  self.geneBounds[0],
                           'max':  self.geneBounds[1]})
        validParamName.append('dyGene')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min':  self.geneBounds[0],
                           'max':  self.geneBounds[1] })
        validParamName.append('dzGene')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min':  self.geneBounds[0],
                           'max':  self.geneBounds[1] })
        return validParamName, validParam


    def setValueFromGenes(self, dxGene, dyGene, dzGene):
        # fast method for setting values without going through configure
        # and updating the FT motion
        self.dxGene = dxGene
        self.point[0] = (dxGene - 0.5) * self.boxDim[0]
        self.dyGene = dyGene
        self.point[1] = (dyGene - 0.5) * self.boxDim[1]
        self.dzGene = dzGene
        self.point[2] = (dzGene - 0.5) * self.boxDim[2]
        self.updateTransformation()


    def configure(self, dxGene=None, dyGene=None, dzGene=None, **kw):

        kw['update'] = False
        if len(kw): FTMotion_BoxTranslation.configure(self, **kw)

        if dxGene:
            self.dxGene = dxGene
            self.point[0] = (dxGene - 0.5) * self.boxDim[0]

        if dyGene:
            self.dyGene = dyGene
            self.point[1] = (dyGene - 0.5) * self.boxDim[1]

        if dzGene:
            self.dzGene = dzGene
            self.point[2] = (dzGene - 0.5) * self.boxDim[2]

        point = kw.get('point', None)
        if point:
            x, y, z = point
            dx, dy, dz = self.boxDim
            self.dxGene  = (x/dx) + 0.5
            self.dyGene  = (y/dy) + 0.5
            self.dzGene  = (z/dz) + 0.5

        self.updateTransformation()


    def getGenes(self):
        return [self.dxGene, self.dyGene, self.dzGene]


    
# check if AutoDock Scorer (C++) is installed
try:
    from cAutoDock.scorer import CoordsVector, Coords, MolecularSystem,\
         updateCoords #, MolKitMolecularSystem
    foundAutoDockC = True
except ImportError:
    foundAutoDockC = False

from AutoDockFR.GA import Genome, Float_Gene

#import numpy.oldnumeric as Numeric
import numpy as Numeric
N=Numeric
from mglutil.math.rigidFit import RigidfitBodyAligner
from mglutil.math.rmsd import RMSDCalculator

class GaRepr(Genome):
    pass
    
from AutoDockFR.ScoringFunction import ScoringFunction
from FlexTree.FTMotions import FTMotionCombiner, FTMotion_Identity 

class FTtreeGaRepr(GaRepr):
    """Implement support for representing a Flexibility Tree for a GA
    search """

    def shallow_clone(self, item):
        # make a shallow copy of self
        new = self.__class__(self.receptorTree, self.ligandTree, self.scorer)
        new.__dict__.update(self.__dict__)
        return new


    def _randomize(self, perGenProbabilty=1.0):
        """
        randomize genome. For each motion object call motion.randomize with
        the set of genes associated with that motion object
        All genes are always modified
        """

        offset = 0
        if perGenProbabilty==1.0:
            for motion in self.motionObjs:
                nbg = motion.nbGenes
                # self[offset:offset+nbg] would create a new gene object
                # self.data[offset:offset+nbg] will randomize the exiting genes
                motion.randomize(self[offset:offset+nbg])
                offset += nbg
        else:
            for motion in self.motionObjs:
                nbg = motion.nbGenes
                if random() < perGenProbabilty:
                    motion.randomize(self[offset:offset+nbg])
                offset += nbg
            
        self.evaluated = 0


    def randomize(self, maxTry=0, perGenProbabilty=1.0):
        if maxTry==0:
            self._randomize()
            self.score()
            ##print self.score()
            return 1
        else:
            gridScorer = self.scorer.gridScorer
            #bht = gridScorer.goodPointsBHT
            #result = gridScorer.result
            #dist2 = gridScorer.dist2
            #ox, oy, oz = gridScorer.gridOrigin
            #ex, ey, ez =  gridScorer.gridEnd

            minClash = None
            done = False
            maxnb = 0
            bestScore = -99999999999
            perAtomMaxPenalty = 0 #
            nbLigAt = len(self.ligRoot.getCurrentConformation())
            iterMax = maxTry/10.

            for k in range(10): # loop with increasing per atom penalty
                maxAllowedPenalty = -nbLigAt*perAtomMaxPenalty
                ct = 0
                done = False
                while not done:
                    self._randomize(perGenProbabilty)

                    self.score()#, RR_L=True, L_L=False)
                    if self._fitness_score > maxAllowedPenalty:
                        return ct+k*iterMax
                    else:
                        if self._fitness_score > bestScore:
                            bestScore = self._fitness_score
                            minClash = self.clone()
                        ct += 1
                        if ct>iterMax:
                            perAtomMaxPenalty += 50
                            done = True

            # if we get here we did not find anyone with a good energy
            # we use the minClash individual
            for i in range(len(self)):
                self[i]._value = minClash[i]._value
            self._fitness_score = minClash._fitness_score
            self._score = minClash._score
            return maxTry
                ## noClash = True
                ## minnb = 1000000
                ## for c in L_coords: # loop over ligand atoms
                ##     nb = bht.closePoints(tuple(c), 2.0, result)
                ##     if nb < minnb: # keep track of worst clash
                ##         minnb = nb
                ## if minnb > 0:
                ##     return ct
                ## else:
                ##     if minnb > maxnb:
                ##         maxnb = minnb
                ##         minClash = self.clone()
                ##     ct += 1
                ##     if ct>maxTry:
                ##         for i in range(len(self)):
                ##             self[i]._value = minClash._value
                ##             print 'individual %d attempts %d'%(ct, maxnb)
                ##         return maxTry



    def configureMotionObjects(self):
        """
        configure genome. For each motion object call motion.setValueFromGenes
        with the set of genes associated with that motion object
        """
        offset = 0
        values = self.values()
        ##import pdb
        ##pdb.set_trace()
        for motion in self.motionObjs:
            nbg = motion.nbGenes
            #if motion.active:
            motion.setValueFromGenes(*values[offset:offset+nbg])
            offset += nbg

        # update all combiners
        for m in self.combinerList: m.updateTransformation()

        # put modified values in genome
        #for i in range(len(genes)):
        #    self[i]._value = genes[i]._value


    def perturb(self, amplitude):
        """
        perturb genome. For each motion object call motion.perturb with
        the set of genes associated with that motion object.
        Modified genes are picked randomly and only affected combiner are
        updated
        """
        offset = 0
        combiners = {}
        for motion in self.motionObjs:
            nbg = motion.nbGenes
            motion.perturb(self[offset:offset+nbg])
            offset += nbg
            m = self.combinerMotions[motion]
            if m: combiners[m] = 1
        self.evaluated = 0
        # update combiners
        for m in combiners.keys(): m.updateTransformation()


    ## def mutate(self, mProb=0.1, dev=0.1):
    ##     """
    ##     mutate genome. For each motion object call motion.mutate with
    ##     the set of genes associated with that motion object
    ##     Modified genes are picked randomly and only affected combiner are
    ##     updated
    ##     """
    ##     offset = 0
    ##     combiners = {}
    ##     mutated = False
    ##     for motion in self.motionObjs:
    ##         nbg = motion.nbGenes
    ##         mutated = mutated or motion.mutate(
    ##             self[offset:offset+nbg], mProb, dev)
    ##         offset += nbg
    ##         m = self.combinerMotions[motion]
    ##         if m: combiners[m] = 1
    ##     self.evaluated = 0
    ##     # update combiners
    ##     for m in combiners.keys(): m.updateTransformation()
    ##     return mutated


    def initialize(self, settings=None):
        #self.evaluated = 0
        self.evals = 0

        if settings.has_key('GA_mutation'):
            mutation_rate = settings['GA_mutation']
            if mutation_rate >= 0.0 and mutation_rate <= 1.0 :
                for gene in self:
                    gene.mutation_rate = mutation_rate


    def __init__(self, receptorTree, ligTree,
                 scoringObj, beforePerf_cb=None,
                 afterPerf_cb=None, optFEB=False):
        # loop over tree and find list of ftNodes with motion objects
        R_MotionObjs = receptorTree.getAllMotion() # receptor motions
        L_MotionObjs = ligTree.getAllMotion() # ligand motions

        self.receptorTree = receptorTree
        self.ligandTree = ligTree
	self.optFEB = optFEB
        self.receptorRoot= receptorTree.root
        self.ligRoot     = ligTree.root

        if len(receptorTree.getMovingAtoms())==0:
            self.rigidReceptor=True
        else:
            self.rigidReceptor=False

        self.beforePerf_cb = beforePerf_cb
        self.afterPerf_cb = afterPerf_cb

        ## build lists of motion objects
        ##
        #  build a dict with key motion object and value the combiner to which
        #  the motion belongs to
        self.combinerMotions={}  # key motion: value combiner or None
        self.combinerList=[]     # list of all combiners

        # will hold a list of all motion objects that can be modified
        self.motionObjs=[]

        # build a list of motion objects that can be modified
        for m in R_MotionObjs:
            if isinstance(m, FTMotionCombiner):
                for motion in m.motionList:
                    if motion.can_be_modified:
                        self.motionObjs.append(motion)
                    self.combinerMotions[motion] = m
                self.combinerList.append(m)
            elif isinstance(m, FTMotion_Identity):
                pass
            else:
                if m.can_be_modified:
                    self.motionObjs.append(m)
                    self.combinerMotions[m] = None

        for m in L_MotionObjs:
            if isinstance(m, FTMotionCombiner):
                for motion in m.motionList:
                    if motion.can_be_modified:
                        self.motionObjs.append(motion)
                        self.combinerMotions[motion] = m
                self.combinerList.append(m)
            elif isinstance(m, FTMotion_Identity):
                pass
            else:
                if m.can_be_modified:
                    self.motionObjs.append(m)
                    self.combinerMotions[m] = None

        # save scoring object
        assert isinstance(scoringObj, ScoringFunction)
        self.scorer = scoringObj

        # generate a genome of float going from 0.0 to 1.0
        all_genes = []

        self.totalGeneNum=0    # number of genes in this genome.
        cutPoints = []    # list of indices at which cross over can occur
                          # a value of 4 means parent1[:4]+parent2[4:] is legal
        cnb = 0

        #print
        #print
        
        for m in self.motionObjs:
            #if not m.can_be_modified:
            #    continue
            if isinstance(m, GAFTMotion_RotationAboutPointQuat):
                #print 'ligand genes starts at', self.totalGeneNum
                self.firstLigandGeneIndex = self.totalGeneNum

            kList, vList = m.getParam()
            nb = len(kList)

            #print 'NBGenes', m.name, nb

            # if divide_and_conquer strategy
            if hasattr(m, 'divide_and_conquar'):
                self.box_start= self.totalGeneNum
                self.box_end  = self.box_start+nb

            if m.cyclicGenes:
                assert len(m.cyclicGenes)==nb
                cyclic = m.cyclicGenes
            else:
                cyclic = [True]*nb

            #if isinstance(m, GAFTMotion_BoxTranslation) and 
            if m.cutPoints:
                for p in m.cutPoints:
                    cutPoints.append(cnb+p)
                cnb = cutPoints[-1]
            else:
                cnb += nb
                cutPoints.append(cnb)

            self.totalGeneNum += nb
            for n in range(nb):
                k=kList[n]
                v=vList[n]
                if v['type'] == 'continuous':
                    #gene=(v['min'], v['max'])
                    if v['dataType'] == 'float':
                        all_genes.append(Float_Gene(min=v['min'], max=v['max'], mutation_func=v['mutator']) )
                    elif v['dataType'] == 'int':
                        all_genes.append(Int_Gene(min=v['min'], max=v['max'], mutation_func=v['mutator']))
                    else:
                        print "Only float/integer gene type is supported"
                        print "Error in type", v['dataType']
                        raise ValueError
                    all_genes[-1].cyclic = cyclic[n]

                elif v['type'] == 'discrete':
                    try:
                        if v['data']:  # if discrete list is defiend
                            gene = v['data']
                    except:
                        gene=range(v['min'], v['max']+1)
                    #all_genes.append( ga.gene.list_gene( gene ) )
                    all_genes.append( Float_Gene( gene ) )
                    all_genes[-1].cyclic = cyclic[n]
                else:
                    raise ValueError('Wrong type in motion parameter list')

        #print 'CUT POINT', cutPoints
        # set the cutPoints
        self.cutPoints = cutPoints[:-1]

        # for debugging
        self.allGenes = all_genes

        self.phenotype = None # will the phenotype when constructure by score to evaluate

        #self.extend(self.allGenes)
        GaRepr.__init__(self, all_genes)


    def toPhenotype(self, sort=False):

        if VERBOSE:
            print "----------  toPhenotype"

        #from time import time
        #t0 = time()
        self.configureMotionObjects()
        #print '    configureMotionObjectsAAA', time()-t0

        # update coords of receptor   
        R_Root=self.receptorRoot
        # Flexible receptor
        #t00 = time()
        if not self.rigidReceptor:
            R_Root.newMotion=True
            if VERBOSE:
                print "\t---", "update receptor coords"
            #t0 = time()
            #import pdb
            #pdb.set_trace()
            R_Root.updateCurrentConformation()#
            #print '        updateCurrentConformationAAA', time()-t0
            #t0 = time()
            if sort:
                FR_coords = R_Root.getCurrentSortedConformation2()
            else:
                #R_coords = R_Root.getCurrentConformation()
                tree=R_Root.tree()
                FR_coords=tree.getMovingAtomCoords()[:]
                #print '        getMovingAtomCoordsAAA', time()-t0
        else:
            FR_coords = None
        #print '    getFRCOORDSAAA', time()-t00

        ## a rigid receptor ..
        ## FIXME .. maybe we could use the rigidRecAtoms directly without calling
        ## R_Root.getCurrentSortedConformation2()
        #RR_coords = R_Root.tree().getRigidAtoms().coords
        RR_coords = None
        #if sort:
        #    if not hasattr(self, 'rigidRecCoordsSorted'):
        #        self.rigidRecCoordsSorted=R_Root.getCurrentSortedConformation2()
        #    RR_coords=self.rigidRecCoordsSorted
        #else:  ## no sorting
        #    if not hasattr(self, 'rigidRecCoords'):
        #        self.rigidRecCoords=R_Root.getCurrentSortedConformation2()
        #    RR_coords=self.rigidRecCoords                    

        # update coords of ligand
        L_Root=self.ligRoot
        L_Root.newMotion=True
        if VERBOSE:
            print "\t---", "update ligand coords"
        #import pdb
        #pdb.set_trace()
        #t0 = time()
        L_Root.updateCurrentConformation()#updateAtom=True)
        #print '    L_Root.updateCurrentConformation', time()-t0
        #t0 = time()
        if sort:
            L_coords = L_Root.getCurrentSortedConformation2()
            #print '    L_Root.getCurrentSortedConformation2', time()-t0
        else:
            L_coords = L_Root.getCurrentConformation()
            #print '    L_Root.getCurrentConformation', time()-t0

        return RR_coords, FR_coords, L_coords  # list type


    def score(self, RR_L=True, FR_L=True, L_L=True, 
              RR_RR=True, RR_FR=True, FR_FR=True):
        """get the score (when no val specified) or set the score to val """
        assert isinstance(RR_L, bool)
        assert isinstance(FR_L, bool)
        assert isinstance(L_L, bool)
        assert isinstance(RR_RR, bool)
        assert isinstance(RR_FR, bool)
        assert isinstance(FR_FR, bool)

        #from time import time
        #t0 = time()
        self.phenotype = RR_coords, FR_coords, L_coords = self.toPhenotype()
        #print 'TOPHENOTYPEAAA', time()-t0
        #t0 = time()
        fscore, score = self.scorer.score(RR_coords, FR_coords, L_coords,
                                          RR_L=RR_L, FR_L=FR_L, L_L=L_L, 
                                          RR_RR=RR_RR, RR_FR=RR_FR, FR_FR=FR_FR)
        self.FRFR = self.scorer.scoreBreakdown['FRFR']
        self.RRL = self.scorer.scoreBreakdown['RRL']
        self.FRL = self.scorer.scoreBreakdown['FRL']        
        self.LL = self.scorer.scoreBreakdown['LL']
        self.RRFR = self.scorer.scoreBreakdown['RRFR']

        #print 'SCOREAAA', time()-t0
	#self.ie = -score+fscore
	if self.optFEB:
            # once the score gets negative and the internal energy is negative
            # we only use the interaction energy 
            if score > 0 and self.ie < 0.0:
                self._fitness_score = fscore 
                self._score = score
            else:
                self._fitness_score = score
                self._score = score
	else:
            self._fitness_score = score
            self._score = score
            #self.ie = -score+fscore
        # once the score gets negative and the internal energy is less than 1.0
        # we only use the interaction energy 
        #if score > 0 and score-fscore > -1.0:
        #    self._fitness_score = fscore 
        #    self._score = score
        #else:
        #    self._fitness_score = score
        #    self._score = score
        return self._fitness_score


    # create fitness calculation function
    ## def performance(self):
    ##         """The GA will call this function to evaluate EACH gene"""
    ##         if VERBOSE:
    ##             print "\n-- FTGA performance()"
    ##         if self.beforePerf_cb:
    ##             self.beforePerf_cb()

    ##         score = self.score(self)
            
    ##         if self.afterPerf_cb:
    ##             self.afterPerf_cb()

    ##         # GA appears to be maximizing the score
    ##         if score > self.scorer.bestScore:
    ##             self.scorer.bestScore=score

    ##         ## print number of evals and score
    ##         ## for GA tuning..                
    ##         ## if self.scorer.numEval%100==0:
    ##         ##     print "LGA:", self.scorer.numEval, -self.scorer.bestScore
            
    ##         return score


class OneFT_GaRepr(FTtreeGaRepr): #e.g. for RMSD based scoring
    def __init__(self, receptorTree, 
                 scoringObj, beforePerf_cb=None,
                 afterPerf_cb=None):
        # loop over tree and find list of ftNodes with motion objects
        R_MotionObjs = receptorTree.getAllMotion() # receptor motions

        #self.receptorRoot= R_MotionObjs[0].node().tree().root
        self.receptorRoot=receptorTree.root
        self.beforePerf_cb = beforePerf_cb
        self.afterPerf_cb = afterPerf_cb

        # store how many genes needed per motion.
        self.genesPerMotion = []
        # expand all combiner motion objs. 
        self.combinerList=[]
        self.motionObjs=[]
        from FlexTree.FTMotions import FTMotionCombiner, FTMotion_Identity 
        for m in R_MotionObjs:
            if isinstance(m, FTMotionCombiner):
                self.motionObjs.extend(m.motionList)
                self.combinerList.append(m)
            elif isinstance(m, FTMotion_Identity):
                pass
            else:
                self.motionObjs.append(m)

        # save scoring object
        assert isinstance(scoringObj, ScoringFunction)
        self.scorer = scoringObj

        # generate a genome of float going from 0.0 to 1.0
        all_genes = []

        self.totalGeneNum=0       # number of genes in this genome.
        for m in self.motionObjs:
            if not m.can_be_modified:
                continue
            kList,vList = m.getParam()
            nb=len(kList)
            self.genesPerMotion.append((nb, kList))
            self.totalGeneNum += nb
            for n in range(nb):
                k=kList[n]
                v=vList[n]
                if v['type'] == 'continuous':
                    gene=(v['min'], v['max'])
                    if v['dataType'] == 'float':
                        #all_genes.append( ga.gene.float_gene(gene) )
                        all_genes.append(Float_Gene(min=v['min'], \
                                                    max=v['max'], \
                                          mutation_func=v['mutator']) )
                    elif v['dataType'] == 'int':
                        #all_genes.append( ga.gene.int_gene(gene) )
                        all_genes.append(Int_Gene(min=v['min'], \
                                                  max=v['max'], \
                                           mutation_func=v['mutator']))

                    else:
                        print "Only float/integer gene type is supported"
                        print "Error in type", v['dataType']
                        raise

                elif v['type'] == 'discrete':
                    try:
                        if v['data']:  # if discrete list is defiend
                            gene = v['data']
                    except:
                        gene=range(v['min'], v['max']+1)
                    all_genes.append( ga.gene.list_gene( gene ) )
                else:
                    raise ValueError('Wrong type in motion parameter list')
