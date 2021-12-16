#######################################################################
#
# Date: April 2006 Authors: Yong Zhao
#       November 2013 Major Revision Michel Sanner
#
#   sanner@scripps.edu
#
#   The Scripps Research Institute (TSRI)
#   Molecular Graphics Lab
#   La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################
"""
The is a simplified / modified version of SciPy Genetic Algorithm.

Genes are the most basic building block in this genetic algorithm library.
A gene represents a particular trait of an individual solution.  Mutliple
genes are combined together to form a Genome.  The entire genome represents
a solution to the problem being solved.

class hierarchy:
Variable
|__ Gene
     |__ Float_Gene
     |__ Int_Gene

UserList
     |__ Data_List
         |__ Genome     (list of Gene)
         |__ Population (list of Genome)
     
"""

import copy, time, sys, string, types, os
from math import tan, pi
import numpy
from random import random, gauss, uniform, randint, triangular


if sys.platform != 'win32': 
    import fcntl
    timer = time.clock	#clock behaves differently work on linux
else:
    timer = time.time
    
from AutoDockFR.ga_util import *

#import scipy.stats as stats
#rv = stats

import AutoDockFR.selection as selection
import AutoDockFR.scaling as scaling


def cauchy(location, scale):

    # Start with a uniform random sample from the open interval (0, 1).
    # But random() returns a sample from the half-open interval [0, 1).
    # In the unlikely event that random() returns 0, try again.
    
    p = random()
    while p == 0.0:
        p = random()
    return location + scale*tan(pi*(p - 0.5))

def cauchy0(scale):

    # Start with a uniform random sample from the open interval (0, 1).
    # But random() returns a sample from the half-open interval [0, 1).
    # In the unlikely event that random() returns 0, try again.
    
    p = random()
    while p == 0.0:
        p = random()
    return scale*tan(pi*(p - 0.5))


class float_gene_uniform_mutator:
    """ randomly choose a value within the float_gene's bounds"""
    def __call__(self, gene, cyclic=False):
        bounds = gene.bounds
        #new =rv.uniform(bounds[0], bounds[1]-bounds[0] )[0]

        #Return a random real number N such that a <= N < b.
        ## never equals b ?? BE CAREFUL !
        new = uniform(bounds[0],bounds[1] )
        return new


class float_gene_gaussian_mutator:
    """ 
    chooses a new value for a float_gene with gaussian 
    shaped distribution around the current value.  
    
    dev_width -- a value between 0 and 1.  It is the standard
    deviation for the gaussian distribution as a percentage
    of the float_gene's range.  For example:  If the genes bounds
    are (0,10) and dev_width is .1, then the standard deviation
    is 1.
    """
    def __init__(self, dev_width=.1):
        self.dev_width = dev_width
        return
    
    def __call__(self, gene, cyclic=False):
        print 'MUTATION', self.dev_width
        new = gauss(gene._value, self.dev_width)
        if new > gene.bounds[1]:
            if cyclic:
                #print 'Cyclic mutation1 value: %f ->%f'%(new, gene.bounds[0] + (new-gene.bounds[1]))
                new = gene.bounds[0] + (new-gene.bounds[1])%1.0
            else:
                new = gene.bounds[1]
                #raise
        elif new < gene.bounds[0]:
            if cyclic:
                #print 'Cyclic mutation2 value: %f ->%f'%(new, gene.bounds[1] + (new-gene.bounds[0]))
                new = gene.bounds[1] - (gene.bounds[0]-new)%1.0
            else:
                new = gene.bounds[0]
                #raise

        ## length = (gene.bounds[1] - gene.bounds[0])
        ## dev = length * self.dev_width
        ## #new = rv.norm(gene._value,dev)[0]
        ## new = gauss(gene._value, dev)
        ## if new > gene.bounds[1]:
        ##     if cyclic:
        ##         #print 'Cyclic mutation1 value: %f ->%f'%(new, gene.bounds[0] + (new-gene.bounds[1]))
        ##         new = gene.bounds[0] + (new-gene.bounds[1])%length
        ##     else:
        ##         new = gene.bounds[1]
        ##         #raise
        ## elif new < gene.bounds[0]:
        ##     if cyclic:
        ##         #print 'Cyclic mutation2 value: %f ->%f'%(new, gene.bounds[1] + (new-gene.bounds[0]))
        ##         new = gene.bounds[1] - (gene.bounds[0]-new)%length
        ##     else:
        ##         new = gene.bounds[0]
        ##         #raise
        if __debug__:
            if new < gene.bounds[0] or new > gene.bounds[1]:
                raise ValueError("gene value outside bounds %f (%f, %f)"%(
                    new, gene.bounds[0], gene.bounds[1]))
        return new


class Variable:
    """
    """
    def __init__(self, value=None,name=None):
        self.name = None
        self._value = value
        self.cyclic = False
        
    def set_value(self,x):
        """ No checking here. Don't assign an incompatible value.
        """ 
        self._value = x
        if x < self.bounds[0] or x > self.bounds[1]:
            import pdb
            pdb.set_trace()

    def get_value(self):
        return self._value

    #def __repr__(self):
    #    v = self._value
    #    if v is None: v = 'None'
    #    else: v = str(v)
    #    return v

    def value(self):
        """Return the current value of the gene. """ 
        try: 
            return self._value
        except AttributeError: 
            raise GAError, 'gene not initialized'
        return

    def __add__(self, other):
        try: return self.value() + other.value()
        except AttributeError: return self.value() + other
    __radd__ = __add__
    def __mul__(self, other):
        try: return self.value() * other.value()
        except AttributeError: return self.value() * other
    __rmul__ = __mul__
    def __sub__(self, other):
        try: return self.value() - other.value()
        except AttributeError: return self.value() - other
    def __rsub__(self, other):
        try: return other.value() - self.value()
        except AttributeError: return other - self.value()
    def __div__(self, other):
        try: return self.value() / other.value()
        except: return self.value() / other
    def __rdiv__(self, other):
        try: return other.value() / self.value()
        except AttributeError: return other / self.value()
    def __float__(self): return float(self.value())
    def __complex__(self): return float(self.value())	
    def __neg__(self): return -self.value()
    def __cmp__(self, other):
        try: 
            if self.__class__ == other.__class__ and self.__dict__ == other.__dict__: return 0
        except AttributeError: pass
        v1 = self.value()
        try: v2 = other.value()
        except AttributeError: v2 = other
        return cmp(v1,v2)
        

## ===


##     def __add__(self, other):
##         try: return self.value() + other.value()
##         except AttributeError: return self.value() + other
##     __radd__ = __add__


    
class Gene(Variable):

    initializer = float_gene_uniform_mutator()
    def __init__(self, value, name=None, min=None, max=None,
                 mutation_rate=0.0, mutation_func=None):
        Variable.__init__(self, value, name)
        self.bounds = [min,max]
        self.mutation_rate = 0.0
        ## if mutation_func != None:            
        ##     if callable(mutation_func):
        ##         self.mutation_func = mutation_func
        ##     elif type(mutation_func) is types.StringType:
        ##         if mutation_func == 'gaussian':
        ##             self.mutator = float_gene_gaussian_mutator(dev_width=.2)
	## 	elif mutation_func == 'uniform':
        ##             self.mutator = float_gene_uniform_mutator()
	## 	else:
        ##             print "Unknown mutator specified. Using gaussian mutator."
        ##             self.mutator = float_gene_gaussian_mutator()
        ## else:
        ##     # default mutator
        ##     self.mutator = float_gene_gaussian_mutator(dev_width=.2)
            
        ## return

    ## called a lot with good values so no check here
    ## def set_value(self, new):
    ##     """ set gene value and handle cyclic values
    ##     """
    ##     if new > self.bounds[1]:
    ##         if self.cyclic:
    ##             print 'Cyclic set1 value: %f ->%f'%(new, self.bounds[0] + (new-self.bounds[1]))
    ##             new = self.bounds[0] + (new-self.bounds[1])
    ##         else:
    ##             raise ValueError, "Setting gene to %g when bounds are %g-%g"%(
    ##                 new, self.bounds[0], self.bounds[1])
    ##     elif new < self.bounds[0]:
    ##         if self.cyclic:
    ##             print 'Cyclic set2 value: %f ->%f'%(new, self.bounds[1] + (new-self.bounds[0]))
    ##             new = self.bounds[1] + (new-self.bounds[0])
    ##         else:
    ##             raise ValueError, "Setting gene to %g when bounds are %g-%g"%(
    ##                 new, self.bounds[0], self.bounds[1])
    ##     self._value = new

    
    def set_mutation(self,mrate):
        """
        Set the mutation rate of the gene.
        Arguments:
        mrate -- can be one of the following:
        * a number between 0 and 1 - sets the mutation rate of the gene to a specific value.
        * "gene" - use the mutation rate set in the class definition for this gene.
        * "adapt" - the mutation rate for the gene is chosen randomly from the range mr_bounds
		"""
        
        if(mrate == 'gene'):   ## NEVER USED as of Apr.2006. .Yong
            try:
                #del self.mutation_rate #remove local mrates and use gene classes mrate
                if self.mutation_rate >= 0.0 and self.mutation_rate <= 1.0 :
                    pass
            except AttributeError: pass
        elif(mrate == 'adapt'): ## NEVER USED as of Apr.2006. .Yong
            #self.mutation_rate = rv.uniform(self.mr_bounds[0],self.mr_bounds[1])[0]
            print "NEVER USED as of Apr.2006. .Yong"
        else: 
            self.__class__.mutation_rate = mrate
        return

    def shallow_clone(self, item):
        new = self.__class__(self._value)
        new.__dict__.update(self.__dict__)
        return new

    def mutate(self):
        ## self.mutation_rate is GA_mutation  parameter
        if random() < self.mutation_rate:
            self.set_value(self.mutator(self, self.cyclic) )
            return 1
        return False

    def clone(self): 
        """Makes a shallow copy of the object.  override if you need more specialized behavior
        """
        return self.shallow_clone(self)
    
    def replicate(self,cnt): 
        """Returns a list with cnt copies of this object in it
        """
        return map(lambda x: x.clone(),[self]*cnt)
            
    def initialize(self):
        """Calls the initializer objects evaluate() function to initialize the gene 
        """
        raise RunTimeError, "Should not be called anymore"
        self._value = self.initializer(self)
        return self.value()



class Float_Gene(Gene):
    def __init__(self, value=None, name=None, **kw):
        Gene.__init__(self, value, name, **kw)
        return
        

class Int_Gene(Gene): ## never used?
    def __init__(self, value, name=None, **kw):
        Gene.__init__(self, value, name, **kw)
        return
    
    

class singlepoint_crossover:
    def __call__(self,parents):
        #assume mom and dad are the same length
        mom = parents[0]; dad = parents[1]
        size = len(mom)
        if(size > 1):
            if mom.cutPoints:
                crosspoint = mom.cutPoints[randint(0,len(mom.cutPoints)-1)]
            else:
                crosspoint = rv.randint(1,len(mom)-1)[0]
        else: 
            #crosspoint = rv.randint(0,len(mom))[0]
            crosspoint = randint(0,size)
        #we do not need this check anymore
        #if crosspoint==5 or crosspoint==6: raise ValueError, "cutting translation"

        brother = (mom[:crosspoint] + dad[crosspoint:]).clone()
        brother._score = None
        brother._fitness_score = None
        sister = (dad[:crosspoint] + mom[crosspoint:]).clone()
        sister._score = None
        sister._fitness_score = None
        return brother, sister


class doublepoint_crossover:

    def __call__(self, parents):
        #assume mom and dad are the same length
        parent1 = parents[0]
        parent2 = parents[1]
        size = len(parent1)
        child1 = parent1.clone()
        child2 = parent1.clone()
        child1._score = None
        child2._score = None
        if len(parent1.cutPoints)>2:
            point1 = parent1.cutPoints[randint(0,len(parent1.cutPoints)-1)]
            point2 = parent1.cutPoints[randint(0,len(parent1.cutPoints)-1)]
            if point1>point2:
                tmp = point1
                point1 = point2
                point2 = tmp
            if point1==5 or point1==6: raise ValueError, "cutting translation"
            if point2==5 or point2==6: raise ValueError, "cutting translation"
            child1.data = parent1.data[:point1]+parent2.data[point1:point2]+parent1.data[point2:]
            child2.data = parent2.data[:point1]+parent1.data[point1:point2]+parent2.data[point2:]
        elif len(parent1.cutPoints)==2:
            point1, point2 = parent1.cutPoints
            if point1==5 or point1==6: raise ValueError, "cutting translation"
            if point2==5 or point2==6: raise ValueError, "cutting translation"
            child1.data = parent1.data[:point1]+parent2.data[point1:point2]+parent1.data[point2:]
            child2.data = parent2.data[:point1]+parent1.data[point1:point2]+parent2.data[point2:]
        elif len(parent1.cutPoints)==1:
            point1 = parent1.cutPoints[0]
            if point1==5 or point1==6: raise ValueError, "cutting translation"
            child1.data = parent1.data[:point1]+parent2.data[point1:]
            child1.data = parent2.data[:point1]+parent1.data[point1:]
        else:
            child1.data = parent1.data[:]
            child2.data = parent2.data[:]
        return child1, child2


class default_evaluator: 
    """ This default evaluator class just reminds you to define your own. """
    ## OBSOLETE
    def evaluate(self,genome):
        #if a performance() method is available, use it!
        return genome.performance()

from UserList import UserList

class Data_List(UserList):
    """ a list of user defined data type.
In this case, it can be :
a list of Genes  ==>  a genome
a list of Genome ==>  a population
a list of Points ==>  a swarm (NOT AVAILABLE YET)

    """
    def __repr__(self):
        return "<%s with %d members>"%(str(self.__class__)[1:-1], len(self))
    
    def shallow_clone(self, item):
        raise RuntimeError, "Class %s does not implement shallow_clone" % self.__class__

    def data_clone(self):
        new = self.shallow_clone(self)
        new.data = map(lambda x: x.clone(),self.data)
        return new		

    def touch(self): pass

    def __setslice__(self, i, j, list):
        if type(list) == type(self.data): self.data[i:j] = list
        else: self.data[i:j] = list.data
        return
    
    def __getslice__(self, i, j):
        new = self.shallow_clone(self)
        new.data = self.data[i:j]
        new.touch()
        return new

    def __add__(self, list):
        new = self.shallow_clone(self)
        if type(list) == type(self.data):
            new.data = self.data + list			
        else: new.data = self.data + list.data			
        new.touch()
        return new

    def __radd__(self, list):
        new = self.shallow_clone(self)
        if type(list) == type(self.data):
            new.data = list + self.data		
        else:	new.data = list.data + self.data			
        new.touch()
        return new

    def __mul__(self, n):
        new = self.shallow_clone(self)
        new.data = self.data*n
        new.touch()
        return new
    
    __rmul__ = __mul__

    def __cmp__(self, other):
        return cmp(self.__dict__,other.__dict__)
	
    
class Genome(Data_List):
    crossover = singlepoint_crossover()
    evaluator = default_evaluator()    

    cutPoints = []

    def __init__(self, list):#, evaluator=None):
        Data_List.__init__(self, list)
        #self.evaluated = False
        self.evals = 0
        self.history = '' # history of operations on this individual
        self.nbLS = 0   # number of local search performed
        self._score = None # None means not evaluated
            
            
    def values(self):
        return [x._value for x in self]

    
    def initialize(self, settings=None):
        #self.evaluated = 0
        self.evals = 0
        #self.initializer.evaluate(self)
        # Initialize each gene
        for gene in self:
            gene.initialize()
            
        # Yong: added support of user defined mutation rate.
        if settings.has_key('GA_mutation'):
            mutation_rate = settings['GA_mutation']
            if mutation_rate >= 0.0 and mutation_rate <= 1.0 :
                for gene in self:
                    gene.mutation_rate = mutation_rate
        if settings and settings.has_key('p_mutate'):
            for g in self: g.set_mutation(settings['p_mutate'])            


    def clone(self):
        new = self.shallow_clone(self)
        new.data = map(lambda x: x.clone(),self.data)
        return new
    

    ## def touch(self): 
    ##     pass


    def evaluate(self, force=0):
        raise
        if (not self.evaluated) or force:
            #traceback.print_stack()
            self._score = self.evaluator.evaluate(self)
            ###self._score = self.scorer.score()
            self.evaluated = 1
            self.evals = self.evals + 1
            return self._score
        pass


    def score(self, RR_L=True, FR_L=True, L_L=True, 
              RR_RR=True, RR_FR=True, FR_FR=True):
        """get the score for this individual, set _score and return the score"""
        pass
        #return self._score
    

    def fitness(self,*val):
        if len(val): self._fitness = val[0]
        return self._fitness


    def set_values(self,x):
        """ Set the values of the genes
        """
        for i in range(len(self)):
            self[i].set_value(x[i])
            new = x[i]
            gene = self[i]
            if new < gene.bounds[0] or new > gene.bounds[1]:
                import pdb
                pdb.set_trace()
        return
    
    def get_values(self):
        """ Return the actual vlues of the genes as a list
        """
        return map(lambda x: x.value(),self)
    

    def mutateOLD(self):
        """mutate the genes in this genome
        """
        mutated = 0
        #for ct, gene in enumerate(self):
        #    mutated1 = gene.mutate()
        #    if ct>6 and mutated1:
        #        print 'mutated TOR %d to %f'%(ct-6, gene)
        #    mutated = mutated1 or mutated
        for gene in self:
            mutated += gene.mutate()
        if mutated:
            self._score = None
            self._fitness_score = None
        return mutated

    def mutate(self):
        """mutate the genes in this genome
        """
        mutated = False
        offset = 0
        values = self.values()
        for motion in self.motionObjs:
            nbg = motion.nbGenes
            #print 'mutaion offset', offset
            lmutated = motion.mutate(self[offset:offset+nbg], 0.05)
            if lmutated:
                mutated = True
            offset += nbg
        if mutated:
            self._score = None
            self._fitness_score = None
        return mutated


class empty_class: pass

def ftn_minimize(x,y): 
	"""Minimization comparator for fitness (scaled score)."""
	return cmp(x.fitness(),y.fitness())

def ftn_maximize(x,y): 
	"""Maximization comparator for fitness (scaled score)."""
	#return cmp(y.fitness(),x.fitness())
	return cmp(y._fitness,x._fitness)

def sc_minimize(x,y): 
	"""Minimization comparator for raw score."""
#	return cmp(x.score(),y.score())
	#removed one function call
	return cmp(x._fitness_score, y._fitness_score)

def sc_maximize(x,y): 
	"""Maximization comparator for raw score."""
	#return cmp(y.score(),x.score())
	#return cmp(y.evaluate(),x.evaluate())
	return cmp(y._fitness_score, x._fitness_score)


def shallow_clone(item):
    bases =  item.__class__.__bases__
    if object not in bases:
        bases = bases +(object,)
    new = type(item.__class__.__name__, bases, item.__dict__)
    return new
    # the vode below was no longer working starting with Python 2.6
    #new = empty_class()
    #new.__class__ = item.__class__
    #new.__dict__.update(item.__dict__)
    #return new


class default_pop_evaluator:
    """The **evaluate()** method simply calls the **evaluate()**
    method for all the genomes in the population
    """
##     def evaluate(self,pop,force = 0):
##         try:
##             evals = 0
##             if not pop.evaluated or force:
##                 for ind in pop:
##                     ind.evaluate(force)
##                     evals+=1
##         except:
##             #this makes where a pop evaluator can simply evaluate a list
##             #of genomes - might be useful to simplify remote evaluation
##             for ind in pop: ind.evaluate(force)

    def evaluate(self,pop,force=0):
        if not pop.evaluate or force:
            for ind in pop:
                ind.evaluate(force)
        return
    

class Population(Data_List):

    default_selector = selection.srs_selector
    default_scaler = scaling.sigma_truncation_scaling
    scaler = default_scaler()

    def __init__(self, genome, size=0):
        """Arguments:
        
        genome -- a genome object.
        size -- number.  The population size.  The genome will be 
        replicated size times to fill the population.
        """
        self.model_genome = genome
        Data_List.__init__(self)
        self.ftn_comparator = ftn_maximize
        self.sc_comparator = sc_maximize		
        self._size(size)
        self.selector = Population.default_selector()
        self.stats = {}
        self.evaluator = default_pop_evaluator()


    def shallow_clone(self, item):
        new = self.__class__(self.model_genome, len(self))
        new.__dict__.update(self.__dict__)
        return new


    def initialize(self, settings=None, init_Population=None):
        b = time.clock()
	self.stats = {'current':{},'initial':{},'overall':{}}
        self.stats['ind_evals'] = 0
        #self.initializer.evaluate(self,settings)
        # initialize the population (all genes get assigned random value)
        for i, ind in enumerate(self):
            ind.initialize(settings)
            if init_Population is None:
                ind.randomize()
            else:
                for j in range(len(ind)):
                    ind[j]._value = init_Population[i][j]._value
        
                    
        ## if init_Population:
        ##     if len(init_Population) > len(self):
        ##         print "population size is too small:", len(self)
        ##         print "cannot be less than size of initial population:", len(init_Population)
        ##         raise ValueError
        ##     else:
        ##         for i in range(len(init_Population)):
        ##             assert len(init_Population[i]) == len(self[i])
        ##             for j in range(len(init_Population[i])):
        ##                 self[i][j].set_value(init_Population[i][j])
	## 			#raise
        e = time.clock()
        #print "finished initial population generation time (s): ", e-b	

        # Reset all the flags for the population
        self.touch(); 
        b = time.clock()
        
	#import pdb;pdb.set_trace()
        # Score/evaluate the population	
        for ind in self:
            if ind._score is None:
                ind.score()

        e = time.clock()
        #print "initial population evaluation time (s): ", e-b	

        # compute fitness for all individuals which is used by srs_select
        # to find individuals to cross and mutate
        self.scale()
        self.sort()
        
        # Update the population stats dictionary
        self.update_stats()
        self.stats['initial']['avg'] = self.stats['current']['avg']
        self.stats['initial']['max'] = self.stats['current']['max']
        self.stats['initial']['min'] = self.stats['current']['min']
        self.stats['initial']['dev'] = self.stats['current']['dev']
        return


    def data_clone(self):
        new = self.shallow_clone(self)
        new.data = map(lambda x: x.clone(),self.data)
        return new

    
    def clone(self): 
        """Returns a population that has a shallow copy the all the 
        attributes and clone of all the genomes in the original 
        object.  It also makes a deep copy of the stats dictionary.
        """	
        new = self.data_clone(self)
        new.stats = {}
        new.stats.update(self.stats)
        return new


    def touch(self):
        """Reset all the flags for the population."""
        self.evaluated = 0;
        self.scaled = 0;
        self.sorted = 0;
        self.select_ready = 0
        self.stated = 0
        return


    def _size(self, l):
        """Resize the population."""
        del self[l:len(self)]
        for i in range(len(self),l):
            self.append(self.model_genome.clone())
        return len(self)		


    def evaluate(self, force=0):
        """Call the **evaluator.evaluate()** method to evaluate
        the population.  The population is also sorted so that 
        it maintains the correct order.  The population is only 
        updated if *evaluated=0*.

        Arguments:
        force -- forces evaluation even if evaluated = 1
        """
        #b = time.clock()
        self.evaluator.evaluate(self,force)
        #e1 = time.clock()
        self.sort()
        #e2 = time.clock()
        #e3 = time.clock()
        self.touch()
        self.evaluated = 1


    def mutate(self):
        mutations = 0
        for ind in self:
            mutations  =  mutations + ind.mutate()
        return mutations


    def sort(self, type='raw', force=0):
        """Sort the population so they are ordered from best
        to worst.  This ordering is specified by the comparator
        operator used to sort the population.  The comparator
        is specified usign the **min_or_max()** function. 

        Arguments:

        type -- 'raw' or 'scaled'.  Determines wether the
        sorting is done based on raw scores or on
        fitness (scaled) scores.
        force -- forces the sort even if sorted = 1
        """
        #if not self.sorted or force: 
        if(type == 'scaled'):
            self.data.sort(self.ftn_comparator)
        elif(type == 'raw'):			
            self.data.sort(self.sc_comparator)	
        else:
            raise GAError, 'sort type must be "scaled" or "raw"'
        self.sorted = 1
        return
    

    def select(self, cnt=1):
        """Calls the selector and returns *cnt* individuals.
        Arguments:
        cnt -- The number of individuals to return.
        """
        if not self.select_ready:
            self.selector.update(self)
            self.select_ready = 1
        return self.selector.select(self,cnt)
        

    def scale(self, force=0):
        if not self.scaled or force:
            self.scaler.scale(self)			
        self.scaled = 1
        return


    def fitnesses(self): 
        """Returns the fitness (scaled score) of all the
        individuals in a population as a Numeric array.
        """		   
        return numpy.array(map(lambda x: x.fitness(),self))


    def scores(self):	
            """Returns the scores (raw) of all the
               individuals in a population as a Numeric array.
            """		   
            return numpy.array([x._fitness_score for x in self])


    def best(self, ith_best=1): 
        """Returns the best individual in the population.
        *It assumes the population has been sorted.*
        Arguments:            
        ith_best -- Useful if you want the second(2), third(3), etc.
        best individual in the population.
        """		   
        return self[ith_best - 1]


    def worst(self,ith_worst=1): 
        """Returns the worst individual in the population.
        *It assumes the population has been sorted.*
        Arguments:
        ith_worst -- Useful if you want the second(2), third(3), etc.
        worst individual in the population.
        """		   
        return self[-ith_worst]		

    def min_or_max(self,*which_one):
        """Returns or set 'min' or 'max' indicating whether the
        population is to be minimized or maximized.  
        *Minimization may require some special handling 
        in the scaling and selector routines.
        
        Arguments:
        which_one -- 'min' or 'max'(optional). Tells the population
        the problem is a minimization or maximizization
        problem.
        """
        if len(which_one): 
            if (re.match('min.*',which_one[0],re.I)):
                self.ftn_comparator = ftn_minimize
                self.sc_comparator = sc_minimize
            elif (re.match('max.*',which_one[0],re.I)):
                self.ftn_comparator = ftn_maximize
                self.sc_comparator = sc_maximize
            else:
                raise GaError, "min_or_max expects 'min' or 'max'"
        if self.ftn_comparator == ftn_minimize: return 'min'
        elif self.ftn_comparator == ftn_maximize: return 'max'


    def update_stats(self):
        """Update the statistics for all genomes in the population."""
        s = self.scores()
        self.stats['current']['max'] = max(s)
        self.stats['current']['avg'] = my_mean(s)
        self.stats['current']['min'] = min(s)
        if len(s) > 1: self.stats['current']['dev'] = my_std(s)
        else: self.stats['current']['dev'] = 0	
        try: self.stats['overall']['max'] = max(self.stats['overall']['max'],
                                                self.stats['current']['max'])
        except KeyError: self.stats['overall']['max'] = self.stats['current']['max']
        try: self.stats['overall']['min'] = min(self.stats['overall']['min'],
                                                self.stats['current']['min'])
        except KeyError: self.stats['overall']['min'] = self.stats['current']['min']
        return


        
class GA:
    """ genetic algorithm """
    default_settings = {'GA_pop_size':150,'GA_replace':.8,
                        'GA_crossover': .8, 'p_mutate':'gene',
                        'GA_deviation': 0.,'GA_gens':50,
                        'rand_seed': "time", 
                        'update_rate': 10000,'dbase':''}
    default_verbose = 1
    def __init__(self, pop, setting=None):
        self.verbose = self.default_verbose
        self.settings = GA.default_settings.copy()
        self.pop = pop
        self.gen = 0
        self.callbacks = {
            'preGeneration': (None, (), {}),
            'postGeneration': (None, (), {}),
            }
        self.use_stop_score = False
        self.enableLocalSearch = False

        if setting != None:
            self.updateSetting(setting)
        self.rmsdCalculators = [] # list of RMSD calculators
        self.rmsdCalc = None # rmsd calculator used by GA to cluster population
        
    
    def updateSetting(self, setting):
	"""
	None <- updateSetting(setting)

	where setting is a dictionary from settings file
	"""
        # update the default settings
        self.settings.update(setting)
        if self.settings.has_key('GA_enableLocalSearch'):
            self.enableLocalSearch = self.settings['GA_enableLocalSearch']
        else:
            self.enableLocalSearch = False ## default
        return
    

    def addCallback(self, where, cb, *args, **kw):
	"""
	None <- addCallback(where, cb)

	where can be 'preGeneration' or 'postGeneration'
	cb is either a callable or None, if cb is a callable it will be called at the begining
	of the evolution loop for each generation. The callable cb takes 1 argument which is an
	instance of GA.
	If cb returns 'end' the evolution loop will abort
	"""
        # set or reset callbacks
	
        assert where in self.callbacks.keys()
        assert callable(cb) or cb is None
        self.callbacks[where] = (cb, args, kw)
        return


    ## def savePopulation(self, filename, gen, rmsd_lst=None, pop=None):
    ##     if pop is None:
    ##         pop = self.pop
    ##     if rmsd_lst is None:
    ##         rmsd_lst = [-1.0]*len(pop)
    ##         for j in (self.settings['savePopulationGenes']):
    ##             if j == -1:
    ##                 j =  self.settings['GA_gens']
    ##             if gen == j:
    ##         	    f = open(filename+'_%04d.py' % gen, 'w')
    ##                 #f1 = open('Hist_'+filename+'_%04d.py' % gen, 'w')
    ##                 f.write("ligandTree = '%s.xml'\n" % self.settings['Ligand'].rsplit('.')[0])
    ##                 f.write("receptorTree = '%s.xml'\n" % self.settings['Receptor'].rsplit('.')[0])
    ##                 f.write("pop = [\n")
    ##                 for i, ind in enumerate(pop):
    ##             	#print i, ind, -ind._score
    ##          	        f.write("    [%s, %f, %f],\n" % (str(ind.values()), rmsd_lst[i], -ind._score))
    ##            	    f.write("      ]\n")
    ##         	    f.close()
    ##     if self.settings['savePopulationHist']:
    ##         for j in (self.settings['savePopulationHist']):
    ##             if j == -1:
    ##                 j =  self.settings['GA_gens']
    ##             if gen == j:
    ##                 f1 = open('Hist_'+filename+'_%04d.py' % gen, 'w')
    ##         	    for i, ind in enumerate(pop):
    ##            	        f1.write("%4d %12.3f %5.2f %s\n" % (i, -ind._score, rmsd_lst[i], ind.history))
    ##         	    f1.close()
    ##     if self.settings['savePopulationMols']:
    ##         for j in (self.settings['savePopulationMols']):
    ##             if j == -1:
    ##                 j =  self.settings['GA_gens']
    ##             if gen == j:
    ##                 from AutoDockFR.orderRefAtoms import orderRefMolAtoms
    ##     	    # write population
    ##         	    #ligmol = self.docking.ligand
    ##         	    for ni, ind in enumerate(pop):
    ##                     ligFilename = "%s_%04d_%d.pdbqt"%(filename,gen, ni)
    ##                     self.saveIndividualPDBQT(ind, ligFilename)


    def savePopulationGenes(self, filename, genStr, rmsd_lst=None, pop=None):
        if pop is None:
            pop = self.pop 
        if rmsd_lst is None:
            rmsd_lst = [-1.0]*len(pop)
        f = open(filename+'_%s.py' % genStr, 'w')
        f.write("ligandTree = '%s.xml'\n" % self.settings['Ligand'].rsplit('.')[0])
        f.write("receptorTree = '%s.xml'\n" % self.settings['Receptor'].rsplit('.')[0])
        f.write("pop = [\n")
        for i, ind in enumerate(pop):
            #print i, ind, -ind._score
            f.write("    [%s, %f, %f],\n" % (str(ind.values()), rmsd_lst[i], -ind._score))
        f.write("      ]\n")
        f.close()

    def savePopulationGenesBest(self, filename, genStr, rmsd_lst=None, pop=None):
        if pop is None:
            pop = self.pop 
        if rmsd_lst is None:
            rmsd_lst = [-1.0]*len(pop)
        f = open(filename+'_%s-bestInd.py' % genStr, 'w')
        f.write("ligandTree = '%s.xml'\n" % self.settings['Ligand'].rsplit('.')[0])
        f.write("receptorTree = '%s.xml'\n" % self.settings['Receptor'].rsplit('.')[0])
        f.write("pop = [\n")
        #for i, ind in enumerate(pop):
            #print i, ind, -ind._score
        f.write("    [%s, %f, %f],\n" % (str(pop[0].values()), rmsd_lst[0], -pop[0]._score))
        f.write("      ]\n")
        f.close()


    def savePopulationPDBQT(self, filename, genStr, recFilename=None, pop=None):
        if pop is None:
            pop = self.pop
        for ni, ind in enumerate(pop):
            ligandFilename = "%s_%s_%04d.pdbqt"%(filename, genStr, ni)
            if recFilename:
                receptorFilename = "%s_%s_%04d.pdbqt"%(recFilename, genStr, ni)
            comments=['*********************************************************']
            comments.append('Solution %d'%ni)
            comments.append('gene: ')
            #import pdb
            #pdb.set_trace()
            nbginit = 0
            #geneswnames=''
            #print ind.values()
	    val = []
            for motion in ind.motionObjs:
                nbg = motion.nbGenes
		comments.append("%s #%s,"%(ind.values()[nbginit:nbg+nbginit],motion.name))
		nbginit = nbg+nbginit
		#comments.extend(list(val))
		#comments.extend(list("#"+motion.name+",\n"))
                #geneswnames+= '%s #%s,\n'%(ind.values()[nbginit:nbg+nbginit][:nbg],motion.name)
                #nbginit = nbg+nbginit
		#comments.extend"#"+motion.name+",\n"))
            #comments.append(geneswnames)
            self.saveIndividualPDBQT(ind, ligandFilename, ni, comments=comments,
                                     recFilename=receptorFilename)

        
    def saveIndividualPDBQT(self, ind, ligFilename, num, comments=[], recFilename=None):
        ligmol = self.docking.ligand
        recmol = self.docking.receptor
        treeOrderedLigAtoms = self.docking.sortedMovAts
        a, b, newCoords = ind.phenotype
        # assing coordinates from tree to ligand atoms ordered according to tree
        treeOrderedLigAtoms.updateCoords(newCoords)

        ind.score()
        scorer = self.docking.scoreObject
        RecLigEnergy = scorer.scoreBreakdown['RRL']
        InternalLigEnergy = scorer.scoreBreakdown.get('LL', 999999999)
        from AutoDockFR.ScoringFunction import FE_coeff_tors_42
        tor = scorer.TORSDOF * FE_coeff_tors_42
        ene = RecLigEnergy + tor
        # write ligand part of solution
        ligComments = []
        ligComments.append('FINAL SOLUTION: %3d FEB: %9.3f R-L: %9.3f L: %9.3f Tor: %9.3f Score: %9.3f'%(
            num, ene, RecLigEnergy, InternalLigEnergy, tor, -ind._fitness_score))
        line = 'rmsdsL: '
        if len(self.rmsdCalculators):
            for rmsdc in self.rmsdCalculators:
                rmsd = rmsdc.computeRMSD(newCoords)
                line += " %6.2f"%rmsd
        comments.append(line)   
        comments.append('*********************************************************')
        # write with ligand with newCoords sorted to match order in ligand file
        ligmol.parser.write_with_new_coords(ligmol.allAtoms.coords, filename=ligFilename,
                                            comments=comments+ligComments,withBondsFor=ligmol)

        # write receptor if flexible
        if self.settings.has_key("movingSC") and recFilename:
            RecLigEnergy = scorer.scoreBreakdown['RRL']+scorer.scoreBreakdown['FRL']

            recComments = []
            recComments.append('FINAL SOLUTION: %3d FEB: %9.3f R-L: %9.3f L: %9.3f Tor: %9.3f Score: %9.3f'%(
            num, ene, RecLigEnergy, InternalLigEnergy, tor, -ind._fitness_score))
            line = 'rmsdsR: '
            if len(self.rmsdCalculatorsRec):
                for rmsdc in self.rmsdCalculatorsRec:
                    rmsd = rmsdc.computeRMSD(b)
                    line += " %6.2f"%rmsd
            comments.append(line)   

            comments.append('*********************************************************')
            self.docking.flexRecAtoms.updateCoords(b)
            recmol.parser.write_with_new_coords(recmol.allAtoms.coords, filename=recFilename,
                                                comments=comments+recComments,withBondsFor=recmol)

        
    def initialize(self, reseed=0, init_Population=None): 
        #import pdb
        #pdb.set_trace()
        b = timer()
        self.gen = 0
        sd = self.settings['rand_seed'];

        if reseed:
            print "+++++++++++  random seed changing +++++++++++++++"
            t=type(sd)
            if sd == "time" or sd == -1:
                currentTime = time.time()
                seed(currentTime)
                print 'Using system time as random seed :',currentTime
            else:
                if (t == types.FloatType or t == types.IntType):
                    print 'Using ',sd,' as random seed '
                    seed(sd)
                else:
                    print "Warning: Wrong random seed", sd
                    print "Warning: Using system time as seed"
                    seed(time.time())
                
        #self.settings['seed_used'] = rv.initial_seed()

        # Instance of GA.singlepoint_crossover.  Gets the crossover op from the 1st genome (Yong)
        self.crossover = self.pop.model_genome.crossover
        self.pop.settings = self.settings 

        # Expand the pop to contain more than one gene
        self.pop._size(self.settings['GA_pop_size'])
        #self.size_pop(self.settings['GA_pop_size'])
        
        # Adding new terms to self.settings dictionary
        self.settings['crossover'] = string.split(str(self.crossover))[0][1:]
        self.settings['selector'] = string.split(str(self.pop.selector))[0][1:]
        self.settings['scaler'] = string.split(str(self.pop.scaler))[0][1:]
        self.settings['genome_type'] = string.split(str(self.pop.model_genome))[0][1:]
        
        # Intialize the population (all genes with random values)
        self.pop.initialize(self.settings, init_Population=init_Population)

        # Population stats, then add the genome stats to it	
        self.stats = {'selections':0,'crossovers':0,'mutations':0,
                      'replacements':0,'pop_evals':1,'ind_evals':0}
        self.stats.update(self.pop.stats)

        self.step_time = timer() - b

        # Create a top-level dictionary. Stores stats of GA, settings, & system info
        self.init_dbase()
        return
    
    """
    def size_pop(self,s):
        #MLD_4_12_12: I think this is extra code we dont need.  Why not just call self.pop._size(self.settings['GA_pop_size'])
        #self.settings['GA_pop_size'] = s
        self.pop._size(s)
        return
    """
    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """
        sz = len(self.pop)

        p_crossover = self.settings['GA_crossover']

        b = timer()

        # compute the number of individuals to be replaced by crossover
        replace = int(self.settings['GA_replace'] * len(self.pop))

        # Iterates by two (replace the mom & dad in a pair)
        for i in range(0,replace,2):
            mom,dad = self.pop[:sz].select(2)
            self.stats['selections'] = self.stats['selections'] + 2
            # Returns true or false.  Random number < p_crossover, then true
            if flip_coin(p_crossover):
                try: 
                    bro,sis = self.crossover((mom,dad))
                    bro.evaluate(force=1)
                    sis.evaluate(force=1)
                    self.stats['crossovers'] = self.stats['crossovers'] + 2
                    self.pop.append(bro);
                    self.pop.append(sis)
                except ValueError: 
                    #crossover failed
                    #- just act as if this iteration never happened
                    i = i - 2 
                    #print 'crossover failure - ignoring and continuing'

            else: 
                self.pop.append(mom.clone());
                self.pop.append(dad.clone());
        # If there is a remainder, too many individuals are replace in the population
        # Remove the last individual            
        if replace % 2:
            ###pradeep- Should a population sort be done here?
            ###self.pop.sort()
            #we did one to many - remove the last individual
            del self.pop[-1]
            self.stats['crossovers'] = self.stats['crossovers'] - 1

        e1 = timer();
        # Mutation
        self.stats['mutations'] = self.stats['mutations'] +\
                                  self.pop[sz:].mutate()
        e2 = timer();
        self.pop.touch()
        self.pop.evaluator.evaluate(self.pop[sz:],force=1)
        self.pop.sort()
        e3 = timer();
        del self.pop[sz:] #touch removed from del
        #self.pop.scale()

        # Local Search step
        if self.enableLocalSearch:
            p_localsearch = self.search_rate#self.settings['GA_localsearchrate']
            # Returns true or false.  Random number < p_crossover, then true
            #if self.LocalSearchFlipCoin.flip_coin(p_localsearch):
            if True:
                # Every member of the population has local search performed on it
                print "\tLocal Search on every member of the population"

                ## optimize the whole population
                #for i, ind in enumerate(self.pop):
                #    neighbor, nbSteps = self.localSearch.search(ind)
                #    self.pop[i] = neighbor

                ## try to only lcoal search good scores
                ## BAD after a while the whoel population is good and no gain
                ## in speed
                ## for i, ind in enumerate(self.pop):
                ##     if ind._score > -100.:
                ##         print '  optimizing individual', i, ind._score
                ##         neighbor, nbSteps = self.localSearch.search(ind)
                ##         self.pop[i] = neighbor

                ## try to optimiaze only half the population
                #for i, ind in enumerate(self.pop[:len(self.pop)/2]):
                for i, ind in enumerate(self.pop[:10]):
                    neighbor, nbSteps = self.localSearch.search(ind)
                    #print '  optimizing individual %d %f -> %f'%(i, ind._score, neighbor._score)
                    self.pop[i] = neighbor
                # Sort the population to have the best score in postion 0

                ## mini = self.pop[0]._score
                ## mini_ind = 0
                ## for i, ind in enumerate(self.pop[:10]):
                ##     if ind._score > mini:
                ##         mini = ind._score
                ##         mini_ind = i
                ## print 'local search made individual %d the best with %f'%(mini_ind, mini)
                ## self.pop.sort()

        # Update the population stats
        self.pop.update_stats()
        self.stats['pop_evals'] = self.stats['pop_evals'] + 1
        self.gen = self.gen + 1
        e = timer(); self.step_time = e - b
            
        # Update the top-level dictionary        
        self.stats.update(self.pop.stats)	
        self.db_entry['best_scores'].append(self.stats['current']['max'])
        return

    def moreGenerations(self, nb):
        for i in range(nb):
            self.step()
            self.p_dev = self.pop_deviation()
            self.iteration_output()
            f, args, kw = self.callbacks['postGeneration']
            if f:
                val = f(*args, **kw)

           
    def evolve(self, init_Population=None):
        self.beginTime = time.time()
        startTime = timer()

        #import pdb
        #pdb.set_trace()
        
        # Sets up the GA & several dictionaries to track the results of the GA
        # and randomize individuals
        self.initialize(init_Population=init_Population)
        # write population

        # mark individuals as originals
        if self.settings['savePopulationHist']:
            for ind in self.pop:
                ind.history = 'O %.2f '%ind._score

        #for ind in self.pop:
        #    ind.randomize()

	# Initial energy cutoff used to cluster members of the population
        self.clusterEcut = 3.0

        # used by GA2
	# Initial energy cutoff used to cluster members of the population
        self.clusterEnergyCut = 2.0
        self.nbClusters = -1
        self.nbGenWithCstClusters = 0
        self.clustersBestE = [] # list of best energy in cluster in previous
                                # generation
        self.nbNoClusterEimprovement = 0
        
        # If Local Search enabled, creates instance of SolisWet class
        self.pre_evolve()

        ## if self.enableLocalSearch:
        ##     for i, ind in enumerate(self.pop):
        ##         neighbor, nbSteps = self.localSearch.search(ind)
        ##         #print '\toptimizing top individual %d %f -> %f'%(i, ind._score, neighbor._score)
        ##         self.pop[i] = neighbor

        # Coefficient of variation (CV): SD/mean
        self.p_dev = self.pop_deviation()
        self.iteration_output()

        # print out stats for Gen 0
        val = self.genStatsOutput()
        self.firstIndToLS = 0
        
        p_stdev = self.settings['GA_deviation']
        maxEvals = self.settings['GA_max_eval']
        score = self.stats['current']['max'] * -1

        # While you havent completed all generations or population hasn't converged
        status = 'searching'
        self.gen = 0
        self.saveGenOutput(val)
        ## if self.gen in self.settings['savePopulationGenes']:
        ##     filename = "%s_%s_job%s"%(
        ##         os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
        ##         os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
        ##         self.settings['jobID'])
        ##     self.savePopulationGenes(filename, '%04d'%self.gen, rmsd_lst)

        ## if self.gen in self.settings['savePopulationMols']:
        ##     filename = "%s_%s_job%s"%(
        ##         os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
        ##         os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
        ##         self.settings['jobID'])
        ##     if self.settings['movingSC']:
        ##         recfilename = "%s_%s_job%s_flexrec"%(
        ##             os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
        ##             os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
        ##             self.settings['jobID'])
        ##         self.savePopulationPDBQT(filename, '%04d'%self.gen,recFilename= recfilename)  
        ##     else:
        ##         self.savePopulationPDBQT(filename, '%04d'%self.gen)

        ## if self.gen in self.settings['savePopulationGenesBest']:
        ##     filename = "%s_%s_job%s"%(
        ##         os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
        ##         os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
        ##         self.settings['jobID'])
        ##     self.savePopulationGenesBest(filename, '%04d'%self.gen, rmsd_lst)
        self.gen = 1
        while (self.gen <= self.settings['GA_gens'] and self.scoreObject.numEval<=maxEvals) \
                  and status=='searching':
            self.lastGenBest = self.pop[0]._fitness_score
            # GA step where crossover, mutation, replacement, local search can occur
            status = self.step()

            self.firstIndToLS = (self.firstIndToLS+1)%3
            
            # Population Coefficient of variation (CV): SD/mean
            self.p_dev = self.pop_deviation()

            # Write out the generation information
            self.iteration_output()
            if(self.gen % self.settings['update_rate'] == 0):
                print "MLD"
                self.update_dbase()

            # print out stats for this Gen
            rmsd_lst = self.genStatsOutput()

            # save stuff for this generation
            #if self.minRMSDInd:
            #    fileName = "%s_%s_job%s_%d.pdbqt"%(self.settings['Receptor'].rsplit('.')[0],
            #                           self.settings['Ligand'].rsplit('.')[0],self.settings['jobID'], self.gen)
            #    self.saveIndividualPDBQT(self.minRMSDInd, fileName)

            self.saveGenOutput(rmsd_lst)
            ## if self.gen in self.settings['savePopulationGenes']:
	    ##     filename = "%s_%s_job%s"%(
            ##         os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
            ##         os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
            ##         self.settings['jobID'])
            ##     self.savePopulationGenes(filename, '%04d'%self.gen, rmsd_lst)

            ## if self.gen in self.settings['savePopulationMols']:
	    ##     filename = "%s_%s_job%s"%(
            ##         os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
            ##         os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
            ##         self.settings['jobID'])
            ##     if self.settings['movingSC']:
            ##         recfilename = "%s_%s_job%s_flexrec"%(
            ##             os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
            ##             os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
            ##             self.settings['jobID'])
            ##         self.savePopulationPDBQT(filename, '%04d'%self.gen,recFilename= recfilename)  
            ##     else:
            ##         self.savePopulationPDBQT(filename, '%04d'%self.gen)

            ## if self.gen in self.settings['savePopulationGenesBest']:
	    ##     filename = "%s_%s_job%s"%(
            ##         os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
            ##         os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
            ##         self.settings['jobID'])
            ##     self.savePopulationGenesBest(filename, '%04d'%self.gen, rmsd_lst)


            if self.use_stop_score:
                score = self.stats['current']['max'] * -1
                if score < self.stop_score:
                    break
            self.gen += 1
            
            if self.p_dev<p_stdev:
                status='population deviation is %f'%p_stdev
                break
            
        # end of evolution
        
        if -1 in self.settings['savePopulationGenes']:
            filename = "%s_%s_job%s"%(
                os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                self.settings['jobID'])
            if self.gen != 0:
                self.savePopulationGenes(filename, 'last_%d'%self.gen, rmsd_lst)
            else:
                self.savePopulationGenes(filename, 'last_%d'%self.gen)

        if -1 in self.settings['savePopulationMols']:
            filename = "%s_%s_job%s"%(
                os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                self.settings['jobID'])
            if self.settings['movingSC']:
                recfilename = "%s_%s_job%s_flexrec"%(
                    os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                    os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                    self.settings['jobID'])
                self.savePopulationPDBQT(filename, 'last_%d'%self.gen,recFilename= recfilename)  
            else:
                self.savePopulationPDBQT(filename, 'last_%d'%self.gen)

        # Update the top-level dictionary        
        print 'EVOLUTION ENDED with status:', status
        self.update_dbase() #enter status prior to post_evolve in dbase
        self.post_evolve()
        self.db_entry['run_time'] = timer() - startTime
        # Windows command
        self.write_dbase()
        return

    def saveGenOutput(self,rmsd_lst):
        if self.gen in self.settings['savePopulationGenes']:
            filename = "%s_%s_job%s"%(
                os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                self.settings['jobID'])
            self.savePopulationGenes(filename, '%04d'%self.gen, rmsd_lst)

        if self.gen in self.settings['savePopulationMols']:
            filename = "%s_%s_job%s"%(
                os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                self.settings['jobID'])
            if self.settings['movingSC']:
                recfilename = "%s_%s_job%s_flexrec"%(
                    os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                    os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                    self.settings['jobID'])
                self.savePopulationPDBQT(filename, '%04d'%self.gen,recFilename= recfilename)  
            else:
                self.savePopulationPDBQT(filename, '%04d'%self.gen)

        if self.gen in self.settings['savePopulationGenesBest']:
            filename = "%s_%s_job%s"%(
                os.path.splitext(os.path.basename(self.settings['Receptor']))[0],
                os.path.splitext(os.path.basename(self.settings['Ligand']))[0],
                self.settings['jobID'])
            self.savePopulationGenesBest(filename, '%04d'%self.gen, rmsd_lst)

        
    def genStatsOutput(self):
        """
        None <- GenStatsOutput()

        This function will take a genome (collection of individual
        genes that make up the population) and determine the rmsd and 
        score of each gene. Used to track the minimum RMSD of the 
        population after each step of the GA.
        """
        # Handle to GA instance

        # loop over all RMSD calculators
        print "        minRMSD L R    index  (     RL  ,     RR  ,       IE   ,     FEB     ) |     maxRMSD   | best: RMSD L R   (     RRL  ,   FRL  ,    FRFR   ,    RRFR  ,    LL   ,     score,     FEB     ) | evals"
        if len(self.rmsdCalculators):
            rmsdcl = self.rmsdCalculators[0]
            rmsd_lst = []
            for i, gene in enumerate(self.pop):
                RR_coords, FR_coords, L_coords = gene.phenotype
                ##print "\n",FR_coords,"\n","\n"
                rmsd = rmsdcl.computeRMSD(L_coords)
                rmsd_lst.append(rmsd)
            minRMSD = min(rmsd_lst)
            minInd = rmsd_lst.index(minRMSD)
            maxRMSD = max(rmsd_lst)
            maxInd = rmsd_lst.index(maxRMSD)
        else:
            rmsdcl = None
            minRMSD = -1
            minInd = -1
            maxRMSD = -1
            maxInd = -1
            rmsd_lst = [-1]
            
        if len(self.rmsdCalculatorsRec):
            rmsdcr = self.rmsdCalculatorsRec[0]
            rmsd_lstr = []
            for i, gene in enumerate(self.pop):
                RR_coords, FR_coords, L_coords = gene.phenotype
                rmsd = rmsdcr.computeRMSD(FR_coords)
                rmsd_lstr.append(rmsd)
            minRMSDR = min(rmsd_lstr)
            minIndR = rmsd_lstr.index(minRMSDR)
            maxRMSDR = max(rmsd_lstr)
            maxIndR = rmsd_lstr.index(maxRMSDR)
        else:
            rmsdcr = None
            minRMSDR = -1
            minIndR = -1
            maxRMSDR = -1
            maxIndR = -1
            rmsd_lstr = [-1]
            
        ## FIXME This constant (0.2983) is hardwired from AD42
        cst = self.pop[minInd].scorer.TORSDOF * 0.2983
        indMin = self.pop[minInd]
        bestInd = self.pop[0]
        print " _Gen%03d  %5.2f %5.2f   %3d   ( %9.3f %9.3f %9.3f %9.3f ) |  %5.2f %5.2f  |      %5.2f %5.2f ( %9.3f %9.3f %9.3f %9.3f %9.3f  %9.3f %9.3f ) | %d"%(
            self.gen, minRMSD, minRMSDR, minInd,
            indMin.RRL+indMin.FRL, indMin.FRFR+indMin.RRFR, indMin.LL, indMin.RRL+indMin.FRL+cst,
            maxRMSD, maxRMSDR, rmsd_lst[0], rmsd_lstr[0],
            bestInd.RRL, bestInd.FRL, bestInd.FRFR, bestInd.RRFR, bestInd.LL, -bestInd._fitness_score, bestInd.RRL+bestInd.FRL+cst,
            bestInd.scorer.numEval)

        for rmsdc in self.rmsdCalculators[1:]:
            pass
        for rmsdc in self.rmsdCalculatorsRec[1:]:
            pass
        
        return rmsd_lst


    def iteration_output(self):
        # Yong's hack for minimum energy
        from time import time
        # Return the (-) of the score.  Indicating more negative, now more favorable
        score = self.stats['current']['max'] * -1

        output = ('\ngen: ' + `self.gen` + ' ' 
                  #+ 'max: ' + `self.stats['current']['max']`  + ' '
                  ## Yong: need min for energy
                  + 'min: ' + str(score)  + ' ' 
                  + 'pop: %d'%len(self.pop) + ' ' 
                  + 'dev: %.4e'%self.p_dev + ' ' 
                  + '#evals: %7d '%(self.scoreObject.numEval)
                  #+ 'eval time: %7.2f'%(self.step_time) + ' sec '
                  + 'Total Time:  %7.2f'%(time()-self.startTime))
        self._print( output )
        if self.gen%10 == 0:
            sys.stdout.flush()

        return

    def pop_deviation(self):
        #compute the coefficient of variation (CV): STDV/mean
        scores = self.pop.scores()
        denom = my_mean(scores)
        if denom == 0.: denom = .0001  # what should I do here?
        return abs(my_std(scores) / denom)
    

    def pre_evolve(self):
	"""
	None <- pre_evolve()

        Creates an instance of SolisWet local search if specfied in settings file
	"""

        if self.settings.has_key('stop_score'):
            self.use_stop_score = True
            self.stop_score = self.settings['stop_score']
        return
    
            
    def post_evolve(self):
        return


    def _print(self,val, level = 1):
        if(self.verbose >= level):
            if type(val) == types.StringType: print val
            else:
                pp = pprint.PrettyPrinter(indent=4)
                pp.pprint(val)
        return

    
    def init_dbase(self):
        """
        None <- init_dbase()

        creates a dictionary that stores GA results, GA Settings, & system settings
        """

        self.db_entry = {}
        self.db_entry['settings'] = self.settings
        t=time.time()
        self.db_entry['raw_time'] = t
        self.db_entry['time'] = time.ctime(t)
        self.db_entry['best_scores'] = [self.stats['current']['max']]
        #self.db_entry['best_scores'] = [self.stats['current']['min']]
        self.db_entry['stats'] = [copy.deepcopy(self.stats)]
        self.db_entry['step_time'] = [self.step_time]
        #MLD_should_be: self.db_entry['optimization_type'] = string.split(str(self.__class__))[0]
        self.db_entry['optimization_type'] = string.split(str(self.__class__))[0][1:]
	return
    
    def update_dbase(self):
        #self.db_entry['best_scores'].append(self.pop.best().score())
        self.db_entry['stats'].append(copy.deepcopy(self.stats))
        self.db_entry['step_time'].append(self.step_time)
        return



    def write_dbase(self):	
        """This does not do file locking on NT - which isn't that big
        a deal because at the most, two runs are going at a time, and
        they are unlikely going to write at the same time (but could).
        On NT, hopefully we're using the gdbm module which does automatic
        file locking.
        """
        if(self.settings['dbase'] != ''):
            fname = self.settings['dbase']
            try: 
                if sys.platform == 'win32': pass
                else:
                    f = open(fname +'.lock','a')
                    fcntl.flock(f.fileno(),fcntl.LOCK_EX)
                try:
                    try: db = my_shelve.open(fname,'w')
                    except dberror: db = my_shelve.open(fname,'c')	
                    keys = db.keys()
                    if(len(keys) == 0):
                        self.dbkey = `1`
                    else:
                        gkeys = []
                        for k in keys:
                            try: gkeys.append(string.atoi(k))
                            except ValueError: pass
                        self.dbkey = `max(gkeys)+1`
                    print 'DB NAME: ', self.settings['dbase'], 'KEY: ', self.dbkey
                    db[self.dbkey] = self.db_entry 
                    db.close()
                except: pass #if an error occured, we still need to unlock the db	
                if sys.platform == 'win32': pass
                else:
                    fcntl.flock(f.fileno(),fcntl.LOCK_UN)
                    f.close()
            except: 	
                if sys.platform == 'win32': pass
                else:
                    f = open('error.lock','a')
                    f.write(os.environ['HOST'])
                    f.close()

        else:  "no dbase specified"
        return


    def best(self):
        vars = self.pop.best()
        bestScore =-1 * max(self.db_entry['best_scores'])
        return vars, bestScore


    def cluster(self, remainder):
        clusters = []
        seedInd = remainder[0]
        pop = self.pop
        RMSDcalc = self.rmsdCalc
        while len(remainder):
            #print '%d left to cluster seed=%d'%(len(remainder), seedInd), remainder
            ref = pop[seedInd]
            dum1, dum2, L_coordsRef = ref.phenotype
            RMSDcalc.setRefCoords(L_coordsRef)
            cluster = [seedInd]
            bestScore = -1000000.0
            notSelected = []
            seed = seedInd # seed will not change in the for loop but seedInd will
            for i in remainder:
                if i==seed:
                    continue
                dum1, dum2, L_coords = pop[i].phenotype
                # RMSD calc
                rmsd = RMSDcalc.computeRMSD(L_coords)
                if rmsd<=2.0:
                    cluster.append(i)
                else:
                    notSelected.append(i)
                    if pop[i]._fitness_score > bestScore:
                        seedInd = i
                        bestScore = pop[i]._fitness_score
            #print 'found cluster', cluster, seedInd
            clusters.append( cluster )
            remainder = notSelected
        return clusters


    def getTopSolutions(self, cut=2.0):
        print 'getting solutions'
        #import pdb
        #pdb.set_trace()
        self.pop.data.sort(sc_maximize)
        ref = self.pop[0]
        remainder = [0]
        refScore = ref._fitness_score
        for i, ind in enumerate(self.pop[1:]):
            if refScore-ind._fitness_score>cut:
                break
            remainder.append(i+1)
        clusters = self.cluster(remainder) 
        print '  found %d clusters out of %d'%(len(clusters), len(remainder))
        best = []
        for c in clusters:
            # find lowest scored individual in cluster
            mini = 999999.9
            rep = None
            for ind in c:
                if -self.pop[ind]._fitness_score < mini:
                    mini = -self.pop[ind]._fitness_score
                    rep = ind
            # optimize lowest score indidual in cluster
            if self.localSearch and self.settings['AnnealSteps']>0:
                neighbor = self.anneal(self.pop[rep], self.localSearch, self.settings['AnnealSteps'])
            else:
                neighbor = self.pop[rep] 

            print "    LSC %d %f -> %f"%(rep, -self.pop[rep]._fitness_score, -neighbor._fitness_score),
            if len(self.rmsdCalculators):
                a, b, L_coords = neighbor.phenotype #self.pop[rep].phenotype
                for rmsdc in self.rmsdCalculators:
                    rmsdL = rmsdc.computeRMSD(L_coords)
                    print "    rmsdL: %6.2f"%rmsdL,
            if len(self.rmsdCalculatorsRec):
                a, b, L_coords = neighbor.phenotype #self.pop[rep].phenotype
                for rmsdc in self.rmsdCalculatorsRec:
                    rmsdR = rmsdc.computeRMSD(b)
                    print "    rmsdR: %6.2f"%rmsdR,

            if len(self.rmsdCalculators) and not len(self.rmsdCalculatorsRec): rmsdR = -1.
            if not len(self.rmsdCalculators) and not len(self.rmsdCalculatorsRec):
                rmsdL = -1.
                rmsdR = -1.
            print len(c), c,
            print
            self.pop[rep] = neighbor
            best.append( (neighbor,[rmsdL],[rmsdR],rep) )
        return best
    

class GA1(GA):
    """ genetic algorithm """


    def jitter(self, ind, dtx, dty, dtz):
        # rotation
        #rdx = 0.005
        #ind[0]._value += uniform(-rdx, rdx)
        #ind[1]._value += uniform(-rdx, rdx)
        #ind[2]._value += uniform(-rdx, rdx)
        #ind[3]._value += uniform(-rdx, rdx)

        # translation
        ind[4]._value += uniform(-dtx, dtx)
        ind[5]._value += uniform(-dty, dty)
        ind[6]._value += uniform(-dtz, dtz)

        # conformation
        #adx = 0.33 # +/- 120 degrees i.e. 120./360
        adx = 0.16 # +/- 60 degrees i.e. 60./360
        #adx = 0.08 # +/- 30 degrees i.e. 30./360

        for i in range(7,len(ind)):
            mini, maxi = ind[i].bounds
            length = maxi-mini
            deltaAngle = uniform(-adx, adx)
            #print deltaAngle,
            tmp = ind[i]._value + deltaAngle
            if tmp > maxi:
                tmp = mini + (tmp - maxi)%length
            elif tmp < mini:
                tmp = maxi - (mini - tmp)%length
            if __debug__:
                if tmp < mini or tmp > maxi:
                    raise ValueError("gene value outside bounds %f (%f, %f)"%(
                        tmp, mini, maxi))
            ind[i]._value = tmp
        #print

        ## torsChains = [ [7,8], [9,10,11] ]
        ## for tc in torsChains:
        ##     if len(tc)==1:
        ##         ind[i]._value += uniform(-adx, adx)
        ##     elif len(tc)==2:
        ##         i1, i2 = tc
        ##     else:
        ##         tcc = tc[:]
        ##         i1 = int(uniform(0, len(tcc)))
        ##         i1 = tcc.pop(i1)
        ##         i2 = int(uniform(0, len(tcc)))
        ##         i2 = tcc[i2]
        ##     deltaAngle = uniform(-adx, adx)
        ##     print i1, i2, deltaAngle
        ##     ind[i1]._value += deltaAngle
        ##     ind[i2]._value -= deltaAngle
        ind.score()
        #ind.evaluate(force=1)


    def anneal(self, ind, solisWets, nbRounds=50, roundFails=10, dx=1.0, absVar=None, verbose=True):    
        """
        Simulated annealing of an individuals. Custom for AutoDockFR rigid receptor
        """
        t0 = time.time()
        rfail = 0  # round failure counter
        #dxMult = 0

        # find dimension of the dockign search box
        # MS: might be better to use settings
        from FTGA import GAFTMotion_BoxTranslation
        for motion in ind.motionObjs:
            if isinstance(motion, GAFTMotion_BoxTranslation):
                break
        bx, by, bz = motion.boxDim

        winner = ind.clone()
        mini = ind.clone()
        
        maxFail = len(ind) # maximum number of such failures

		# iterate the process n times (i.e. rounds)
        for i in range(nbRounds):
		    if __debug__:
		        if verbose:
		            print "round: %d ene:%f in %.2f(s) dx:%f"%(i, -winner._fitness_score, time.time()-t0, dx)
		    fail = 0           # count the number of times SolisWets does not improve
		    ct = 0             # counter 

		    while fail<maxFail: # as long as we do not fail nbGenes time in a row
		        # do one local search with lots of steps and allwo to fail 2*nbGenes
		        first = True
			kw={'max_steps':1000, 'MAX_FAIL':maxFail*2, 'MIN_VAR':0.001, 'absMinVar':absVar, 'search_rate':1.0}
		        new, nbSteps = solisWets.search(mini, **kw) #, max_steps=1000, MAX_FAIL=maxFail*2, MIN_VAR=0.001,
		                                        #absMinVar=absVar, search_rate=1.0)
		        # if the results is better it will be minimized again and reset fail counter

		        # I noticed that the result will only get better than winner if the
		        # result of the first SolisWets takes up back to within 2% of the best
		        # if it is not the case it is not useful to iterated SolisWets
		        if first and new._fitness_score < winner._fitness_score*0.98:
		            break

		        if new._fitness_score > mini._fitness_score:
		            if __debug__:
		                if verbose:
		                    print '  ',fail, nbSteps, mini._fitness_score, new._fitness_score, new._fitness_score- mini._fitness_score
		            fail = 0
		            mini = new
		        else: # increment failure count
		            fail += 1

		        ct += 1
		        # if we reach 10 iterations and score is not better we stop minimizing
		        if ct > 10: break

		    # if the minimized ind is better he becomes the winner
		    if mini._fitness_score > winner._fitness_score:
		        winner = mini.clone()
		        rfail = 0
		        ## if dxMult > 0:
		        ##     dx -= 1.0 # if dx was increased, decrease it
		        ##     dxMult -= 1
		    else:
		        # we start from the last winner
		        mini = winner.clone()
		        rfail += 1
		        if rfail==roundFails: # if the winner did not improve in 5 round increase dx
		            break
		            ## dx += 1.0
		            ## dxMult += 1
		            ## rfail = 0

		    # we randomly move the individual using a Gaussian with dev dx
		    self.jitter(mini, dx/bx, dx/by, dx/bz)

        if __debug__:
            if verbose:
                print 'AFTER search', winner._fitness_score, time.time()-t0
	kw = {'max_steps':1000, 'MAX_FAIL':maxFail*2, 'MIN_VAR':0.0005}
        new, nbSteps = solisWets.search(winner, **kw)
        if new._fitness_score > winner._fitness_score:
            winner = new
        if __debug__:
            if verbose:
                print 'AFTER final mini', new._fitness_score

        return winner
        

    def minimize(self, individual, nbSteps=5, noImproveStop=2, **kw):
        #minimize_param = self.configure_minimize
        last_score = individual.score()
        noImprovement = 0
        totalSteps = 0
        solisWets = self.localSearch

        for i in range(nbSteps):
            neighbor, nbSteps = solisWets.search(individual, **kw)
            totalSteps += nbSteps
            if neighbor.score() > last_score:
                #print 'round %d: %f -> %f %4d %f'%(i, -individual._score, -neighbor._score, nbSteps, kw['MIN_VAR'])
                last_score = neighbor.score()
                individual = neighbor
            else:
                noImprovement += 1
                if noImprovement > noImproveStop:
                    break

        self._totalStepInLastMinimize = totalSteps
        return individual

    
    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        t0 = time.time()
        # count similar individuals (within clusterEcut of the top scored ind)
        ref = self.pop[0]
        remainder = [0]
        refScore = ref._fitness_score
        if refScore > 0.0:
            for i, ind in enumerate(self.pop[1:]):
                if refScore-ind._fitness_score > self.clusterEcut:
                    break
                remainder.append(i+1)

            print '\n  CLUSTERING %d individual(s) Within %.2f Kcal of %f'%(
                len(remainder), self.clusterEcut, -refScore)

        gen = self.gen
        
        #if refScore>0.0 and len(remainder)<10: # slower and does not seem to help on 1HBV
        #    remainder = range(10)

        ## # sanity check
        ## for ind in remainder:
        ##     individual = self.pop.model_genome.clone()
        ##     individual.initialize(self.settings)
        ##     for i,v in enumerate( self.pop[ind] ):
        ##         individual[i].set_value(v)
        ##     assert individual.evaluate()==self.pop[ind]._fitness_score
            
	    # If there are more than 10 individuals that are similar
	    # reduce the clusteringEnergy by 0.5 (cluster less individuals)
        fromClusters = []
        if len(remainder)>10:
            #remainder = remainder[:10]
            self.clusterEcut = max(2.0, self.clusterEcut-0.5)
        elif len(remainder)==2:
            self.clusterEcut += 0.5
            
        p_crossover = self.settings['GA_crossover']
        toRemove = []
        bestInCluster = []
        if len(remainder)>2:
            nbRemoved = 0
            clusters = self.cluster(remainder)
            for c in clusters:
                #import pdb
                #pdb.set_trace()
                # find lowest score individual in cluster
                mini = 99999999999.9
                rep = None
                for ind in c:
                    if -self.pop[ind]._fitness_score < mini:
                        mini = -self.pop[ind]._fitness_score
                        rep = ind
                # optimize lowest score individual in cluster
                ind = self.pop[rep]
                bestInCluster.append(ind.clone())
                ##
                ## NO MIMIMIZATION OF BEST IN CLUSTER
                #neighbor = self.minimize(ind, nbSteps=50, max_steps=100, noImproveStop=10,)
                neighbor = ind
                #print "   LSC %2d %9.3f -> %9.3f gen:%d evals:%d"%(
                #    rep, -self.pop[rep]._fitness_score, -neighbor._fitness_score, self.gen, self.scoreObject.numEval),
                if len(self.rmsdCalculators):
                    a, b, L_coords = self.pop[rep].phenotype
                    for rmsdc in self.rmsdCalculators:
                        print "    rmsd: %6.2f"%rmsdc.computeRMSD(L_coords),
                print " #inClust", len(c), "ClustMemb", c, rep, -self.pop[rep]._fitness_score
                #MLDprint ' origin:%s'%neighbor.history.split()[0]

                #neighbor.history = ind.history+'LSC(%d) %.2f '%(gen,neighbor._fitness_score)
                self.pop[rep] = neighbor
                
                # If cluster has more than one member, remove individuals from population
                nbRemoved += len(c)-1
                for index in c:
                    if index==rep: continue
                    toRemove.append(self.pop[index])
                    #self.pop[index]._fitness_score = -999999999.9 # will remove it (if we sort)

            ##
            ## The code below tried to add offsprings from members that will be removed from the cluster
            ##
            bestEmut = -999999.
            bestEcross = -999999.
            ## # create offspring for cluster members that will be removed
            ## if len(clusters)==1: # mutate all the ones that will be removed
            ##     for c in clusters:
            ##         for ind in c:
            ##             self.stats['mutations'] = self.stats['mutations'] + self.pop[ind].mutate()
            ##             self.pop[ind].evaluate(force=1)
            ##             e = self.pop[ind]._fitness_score
            ##             if e > bestEmut:
            ##                 bestEmut = e
            ##             fromClusters.append(self.pop[ind])
            ## else:
            ##     # randomly pick 2 individuals and either cross them or mutate them
            ##     parents = toRemove[:]
            ##     while len(parents) >= 2:
            ##         i = int(uniform(0, len(parents)))
            ##         mom = parents.pop(i)
            ##         j = int(uniform(0, len(parents)))
            ##         dad = parents.pop(j)
            ##         if flip_coin(p_crossover):
            ##             bro,sis = self.crossover((mom,dad))
            ##             bro.evaluate(force=1)
            ##             sis.evaluate(force=1)
            ##             fromClusters.append(bro)
            ##             fromClusters.append(sis)
            ##             e = sis._fitness_score
            ##             if e > bestEcross:
            ##                 bestEcross = e
            ##             e = bro._fitness_score
            ##             if e > bestEcross:
            ##                 bestEcross = e
            ##         else:
            ##             self.stats['mutations'] = self.stats['mutations'] + mom.mutate()
            ##             self.stats['mutations'] = self.stats['mutations'] + dad.mutate()
            ##             mom.evaluate(force=1)
            ##             dad.evaluate(force=1)
            ##             fromClusters.append(mom)
            ##             fromClusters.append(dad)
            ##             e = dad._fitness_score
            ##             if e > bestEmut:
            ##                 bestEmut = e
            ##             e = mom._fitness_score
            ##             if e > bestEmut:
            ##                 bestEmut = e
                        
            # remove individuals now else indiced in cluster would change
            #for ind in toRemove:
            #    self.pop.remove(ind)
            if __debug__:
                #print "  %d clusters found and optimzed in %f (removed %d created %d (bestEM %f, bestEC%f))"%(len(clusters), time.time()-t0, nbRemoved, len(fromClusters), bestEmut, bestEcross)
                print "  %d clusters found in %f (removed %d)"%(len(clusters), time.time()-t0, nbRemoved)
        
        # Size of the population
        sz = len(self.pop)

        b = timer()

        # Number of individuals to be replaced (settings file)
        # This concept does not exist in the AD4.2 GA implementation
        replace = int(self.settings['GA_replace'] * sz)
	    # Number of new members in inject into the population (settings file)
        # This concept does not exist in the AD4.2 GA implementation
        nbNew = int(self.settings['GA_injectRandomInd'] * sz)
        # Also add the number of clustered individuals removed
        nbNew2 = nbNew + len(toRemove)

        #import pdb;pdb.set_trace()
        self.pop.touch() # this will reset selector_ready

        nbCross = nbGood1 = nbGood2 = 0
        fromCrossOver = []
	    # The energy (cutE) will be the most unfavorable individual
	    # that is not automatically replaced by crossover or random_injection
        #MLDcutE = -self.pop[len(self.pop)-nbNew-replace/2-1]._fitness_score
        cutE = -self.pop[len(self.pop)-nbNew-replace -1]._fitness_score
        e1 = time.time()

        # reduce number of steps minimizing mutations and cross overs
        # else time to create them increases and not better results
        #nbsteps = max(10, 50-6*self.gen)

        # Iterates by two (replace the mom & dad in a pair)
        for i in range(0,replace,2):
            #mom,dad = self.pop[:sz].select(2)
            #ts = time.time()
            mom, dad = self.pop.select(2)
            #print 'select', i, time.time()-ts
            self.stats['selections'] = self.stats['selections'] + 2
            # Returns true or false.  Random number < p_crossover, then true
	        # Either do crossover
            if flip_coin(p_crossover):
                try: 
                    bro,sis = self.crossover((mom,dad))
                    bro.score()
                    sis.score()
                    self.stats['crossovers'] = self.stats['crossovers'] + 2
                    if self.enableLocalSearch:
                        bron = self.minimize(bro, **self.settings['GAminimize'])
                        nbSteps1 = self._totalStepInLastMinimize
                        sisn = self.minimize(sis, **self.settings['GAminimize'])
                        nbSteps2 = self._totalStepInLastMinimize
                        o1star = o2star = ''
                        if bron._fitness_score>refScore:
                            o1star = '*'
                            refScore = bron._fitness_score
                        elif sisn._fitness_score>refScore:
                            refScore = sisn._fitness_score
                            o2star = "*"
                        #sisn, nbSteps =  self.localSearch.search(sis, max_steps=300, MAX_SUCCESS=4, MAX_FAIL=6)
                        print '  CRO A: %3d %12.3f B: %3d %12.3f O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                            self.pop.selector._selected[0], -mom._fitness_score,
                            self.pop.selector._selected[1], -dad._fitness_score,
                            -bro._fitness_score, -bron._fitness_score, o1star, nbSteps1,
                            -sis._fitness_score, -sisn._fitness_score, o2star, nbSteps2)
                        #print '  CROSS  BRO %12.3f -> %12.3f (%4d) SIS %12.3f -> %12.3f (%4d)'%(
                        #    -bro._fitness_score, -bron._fitness_score, nbSteps1, -sis._fitness_score, -sisn._fitness_score, nbSteps2)
                        #print 'CRO SIS %f -> %f %d'%(-sis._fitness_score, -sisn._fitness_score, nbSteps)
                    else:
                        bron = bro
                        sisn = sis

                    fromCrossOver.append(bron)
                    fromCrossOver.append(sisn)
                    if self.settings['savePopulationHist']:
                        dadOrigin = dad.history.split()[0]
                        momOrigin = mom.history.split()[0]
                        bron.history = 'C(%d_%s|%s) %.2f '% (gen, momOrigin, dadOrigin, bro._fitness_score)
                        sisn.history = 'C(%d_%s|%s) %.2f '% (gen, momOrigin, dadOrigin, sis._fitness_score)
                    nbCross += 2
                    if -bron._fitness_score < cutE: nbGood1 +=1
                    if -sisn._fitness_score < cutE: nbGood1 +=1
                except ValueError: 
                    print "ERROR: crossover failed"
                    #- just act as if this iteration never happened
                    i = i - 2 
                    #print 'crossover failure - ignoring and continuing'
	        # Or do mutation
            else:
                #import pdb
                #pdb.set_trace()
                momc = mom.clone()
                self.stats['mutations'] = self.stats['mutations'] + momc.mutate()
                dadc = dad.clone()
                self.stats['mutations'] = self.stats['mutations'] + dadc.mutate()
                
                if self.enableLocalSearch:
                    #ndadc, nbSteps =  self.localSearch.search(dadc, max_steps=300, MAX_SUCCESS=4, MAX_FAIL=6)
                    ndadc = self.minimize(dadc, **self.settings['GAminimize'])
                    nbSteps1 = self._totalStepInLastMinimize
                    nmomc = self.minimize(momc, **self.settings['GAminimize'])
                    nbSteps2 = self._totalStepInLastMinimize
                    o1star = o2star = ''
                    if ndadc._fitness_score>refScore:
                        o1star = '*'
                        refScore = ndadc._fitness_score
                    elif nmomc._fitness_score>refScore:
                        refScore = nmomc._fitness_score
                        o2star = "*"
                    print '  MUT A: %3d %12.3f B: %3d %12.3f O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                        self.pop.selector._selected[0], -mom._fitness_score,
                        self.pop.selector._selected[1], -dad._fitness_score,
                        -momc._fitness_score, -nmomc._fitness_score, o2star, nbSteps2,
                        -dadc._fitness_score, -ndadc._fitness_score, o1star, nbSteps1)
                    dadc = ndadc
                    momc = nmomc
                else:
                    momc.evaluate(force=1)
                    dadc.evaluate(force=1)
                    print '  MUTATE BRO %12.3f -> %12.3f (%4d) SIS %12.3f -> %12.3f (%4d)'%(
                        -dad._fitness_score, -dadc._fitness_score, nbSteps1, -mom._fitness_score, -momc._fitness_score, nbSteps2)
                
                if -momc._fitness_score < cutE: nbGood2 +=1
                if -dadc._fitness_score < cutE: nbGood2 +=1
                fromCrossOver.append(momc)
                fromCrossOver.append(dadc)
                if self.settings['savePopulationHist']:
                    momc.history += 'M(%d) %.2f '%(gen, momc._fitness_score)
                    dadc.history += 'M(%d) %.2f '%(gen, dadc._fitness_score)

        if __debug__:
            print '  CROSSOVER/MUT created %d individuals (cross=%d good, mut=%d good) in %f'%(
                len(fromCrossOver), nbGood1, nbGood2, time.time()-e1)

        # remove the clustered individuals now else indiced in cluster would change
        if len(remainder)>2 and len(remainder)<100:
            for ind in toRemove:
                self.pop.remove(ind)

        #print "Population sz after cross & removal %s.  Should be %s " % (len(self.pop), sz)

        ## inject new individuals in the population
        template = self.pop.model_genome
        newIndiv = []
        off = self.transOff
        ligRoot = self.ligRoot
        ax,ay,az = self.origAnchor
        result = numpy.zeros( (500,), 'i' )
        dist2 = numpy.zeros( (500,), 'f' )
        #print 'searching ...', cutE
        nbGood3 = 0
        e1 = time.time()
        lowestE = -99999.0
        while len(newIndiv) < nbNew2:
            ind = template.clone() # create an individual
            ind.initialize(self.settings)
            attempts = ind.randomize(maxTry=self.settings['constraintMaxTry'])
            before = ind._fitness_score
            #ind._fitness_score = ind.score()
            if self.enableLocalSearch:
                nind = self.minimize(ind, **self.settings['GAminimize'])
            else:
                nind = ind

            o1star = ''
            if nind._fitness_score>refScore:
                o1star = '*'
            print "      NEW: %4d attempts %12.3f -> %12.3f%1s (%4d)"%(
                attempts, -before, -nind._fitness_score, o1star, self._totalStepInLastMinimize)

            newIndiv.append(nind)
            if self.settings['savePopulationHist']:
                nind.history = 'N(%d) %.2f '%(gen, nind._fitness_score)
            if nind._fitness_score>lowestE:
                lowestE=nind._fitness_score
            if -nind._fitness_score < cutE:
                nbGood3 +=1
            
        self.pop.extend(newIndiv)
        self.pop.extend(fromCrossOver)
        self.pop.sort()
        self.pop.data = bestInCluster + self.pop[:sz-len(bestInCluster)].data
        #print "Population sz after extension and trunc: ", len(self.pop)

        ## nbls = 0
        ## index = 0
        ## while nbls<5 and index < len(self.pop): # FIXME 15
        ##     if self.pop[index].nbLS > 5:
        ##         index += 1
        ##         continue
        ##     print "LS ind %d"%index
        ##     neighbor = self.minimize(self.pop[index], nbSteps=10, max_steps=100, noImproveStop=3)
        ##     neighbor.history = ind.history + 'LS2(%d) %.2f '%(gen, neighbor._fitness_score)
        ##     self.pop[index] = neighbor
        ##     index += 1
        ##     nbls += 1

        # Local Search step
        if self.enableLocalSearch:
            p_localsearch = self.settings['GA_localsearchfreq']
            # Returns true or false.  Random number < p_crossover, then true
            if self.localSearchFlipCoin.flip_coin(p_localsearch):
                print "  Local Search on all members of the population"
                tls = time.time()
                oldScores = []
                lsc = 0
                mini = self.pop[0]._fitness_score
                bestInd = 0
                for i, ind in enumerate(self.pop[1:]):
                    oldScores.append(ind._fitness_score)
                    neighbor = self.minimize(ind, nbSteps=10, noImproveStop=2, max_steps=1000,
                                             MAX_FAIL=15, MIN_VAR=0.01)
                    if self.settings['savePopulationHist']:
                        neighbor.history = ind.history + 'LS(%d) %.2f '%(gen, neighbor._fitness_score)
                    if neighbor._fitness_score > mini:
                        mini = neighbor._fitness_score
                        bestInd = i
                    self.pop[i] = neighbor
                    lsc += 1
                print "  local search minimized %d individuals in %f"%(lsc, time.time()-tls)
                print "    best individual %d %12.3f -> %12.3f"%(bestInd, -oldScores[bestInd], -mini)

        ##         ## optimize the whole population
        ##         #for i, ind in enumerate(self.pop):
        ##         #    neighbor, nbSteps = self.localSearch.search(ind)
        ##         #    self.pop[i] = neighbor

        ##         ## try to only lcoal search good scores
        ##         ## BAD after a while the whole population is good and no gain
        ##         ## in speed
        ##         ## for i, ind in enumerate(self.pop):
        ##         ##     if ind._fitness_score > -100.:
        ##         ##         print '  optimizing individual', i, ind._fitness_score
        ##         ##         neighbor , nbSteps= self.localSearch.search(ind)
        ##         ##         self.pop[i] = neighbor

        ##         ## for i in xrange(self.firstIndToLS,sz,3):
        ##         ##     ind = self.pop[i]
        ##         ##     neighbor, nbSteps = self.localSearch.search(ind)
        ##         ##     #print 'optimizing top individual %d %f -> %f'%(i, ind._fitness_score, neighbor._fitness_score)
        ##         ##     self.pop[i] = neighbor
        ##         # Sort the population to have the best score in postion 0

            ##     tls = time.time()
            ##     oldScores = []
            ##     for ind in self.pop:
            ##         oldScores.append(ind._fitness_score)
            ##     ## SCHEME 1
            ##     ## Optimize top individuals
            ##     #for i, ind in enumerate(self.pop[:len(self.pop)/2]):
            ##     lsc = 0
            ##     e_cut = 0.0 
            ##     for i in range(len(self.pop)/2):
            ##         if self.pop[i]._fitness_score <= 0.0:
            ##             #e_cut = self.pop[100]._fitness_score
            ##             e_cut = self.pop[min(100, len(self.pop)/2)]._fitness_score
            ##             break
                    
            ##     for i, ind in enumerate(self.pop[:maxp]):
            ##         if ind._fitness_score >= e_cut:
            ##             #neighbor, nbSteps = self.localSearch.search(ind, max_steps=, MIN_VAR=varMin)
            ##             neighbor = self.minimize(ind, nbSteps=10, noImproveStop=2,
            ##                                      max_steps=200, MAX_FAIL=15, MIN_VAR=0.01)
            ##             #neighbor, nbSteps = self.localSearch.search(ind, max_steps=, MIN_VAR=varMin)
            ##             #print 'optimizing top individual %d %f -> %f'%(i, -ind._fitness_score, -neighbor._fitness_score)
            ##             neighbor.history = ind.history + 'LS2(%d) %.2f '%(gen, neighbor._fitness_score)
            ##             self.pop[i] = neighbor
            ##             lsc += 1
            ##     # Sort the population to have the best score in postion 0
            ##     print "local search minimized %d individuals in %f"%(lsc, time.time()-tls)

            ##     ## Optimize random individuals with decreasing probability according to ranking
            ##     tls = time.time()
            ##     maxr = self.settings['GA_localsearchRandPopSize']
            ##     #print "Local Search on %d random members of the population"%maxr
            ##     n = sz-maxp
            ##     lsc = 0
            ##     for i in xrange(maxr):
            ##         index = maxp + int(triangular(0,1.,0.)*n)
            ##         ind = self.pop[index]
            ##         #neighbor, nbSteps = self.localSearch.search(self.pop[index], )
            ##         neighbor = self.minimize(ind, nbSteps=1, max_steps=50, noImproveStop=3, MIN_VAR=0.01)
                    
            ##         #print ' optimizing random individual %d %f -> %f'%(index, -self.pop[index]._fitness_score, -neighbor._fitness_score)
            ##         neighbor.history = ind.history + 'LS3(%d) %.2f '%(gen, neighbor._fitness_score)
            ##         self.pop[index] = neighbor
            ##         lsc += 1

            ##     print "local search minimized %d random individuals in %f"%(lsc, time.time()-tls)

            ##     mini = self.pop[0]._fitness_score
            ##     mini_ind = 0
            ##     for i, ind in enumerate(self.pop[:maxp]):
            ##         if ind._fitness_score > mini:
            ##             mini = ind._fitness_score
            ##             mini_ind = i
            ##     if mini_ind != 0:
            ##         print ' *** LS made individual %d the best with %f->%f'%(mini_ind, oldScores[mini_ind], mini)
            ##     ## SCHEME 1
            ##     #elif mini_ind >= maxp:
            ##     #    print ' ***'
            ##     #    print ' *** LS made individual %d the best with %f->%f'%(mini_ind, oldScores[mini_ind], mini)
            ## else: # local search probability said no local search
            ##     # we still optimize top one and 10 random ones in top maxp
            ##     t0 = time.time()
            ##     for i in range(10):
            ##         neighbor = self.minimize(self.pop[i], 3, 20, 1, MIN_VAR=0.01)
            ##         #neighbor, nbSteps = self.localSearch.search(self.pop[i], max_steps=300, MAX_FAIL=20, MIN_VAR=0.001)
            ##         #print 'LS1 ', i, -self.pop[i]._fitness_score, -neighbor._fitness_score
            ##         neighbor.history = self.pop[i].history + 'LS1(%d) %.2f '%(gen, neighbor._fitness_score)
            ##         self.pop[i] = neighbor
            ##     print "LS for top 10 in:", time.time()-t0
                ## neighbor = self.minimize(self.pop[0], 6, 50, 2)
                ## print 'LS 0', -self.pop[0]._fitness_score, -neighbor._fitness_score
                ## self.pop[0] = neighbor

                ## t0 = time.time()
                ## maxi = len(pop)-10
                ## for i in range(maxi/4):
                ##     index = 10 + int(uniform(10,maxi))
                ##     neighbor = self.minimize(self.pop[index], 1, 4, 1)
                ##     #print 'LS2', index, -self.pop[index]._fitness_score, -neighbor._fitness_score
                ##     self.pop[index] = neighbor
                ## print "LS2 for top 20 in:", time.time()-t0

                ## t0 = time.time()
                ## for i in range(20):
                ##     index = 10 + int(triangular(0,1.,0.)*maxp)
                ##     neighbor = self.minimize(self.pop[index], 3, 20, 1)
                ##     #print 'LS2', index, -self.pop[index]._fitness_score, -neighbor._fitness_score
                ##     self.pop[index] = neighbor
                ## print "LS2 for top 20 in:", time.time()-t0

                #for i, ind in enumerate(self.pop[:10]):
                #    neighbor, nbSteps = self.localSearch.search(ind)
                #    self.pop[i] = neighbor

        self.pop.touch()
        self.pop.scale()
        self.pop.sort()

        # Update the population stats
        self.pop.update_stats()
        self.stats['pop_evals'] = self.stats['pop_evals'] + 1
        #chk for saving
        #fileName = "%s_%s_%d"%(self.settings['Receptor'].rsplit('.')[0],self.settings['Ligand'].rsplit('.')[0],self.settings['constraintMaxTry'])
        #self.checkSavePopulation(fileName)

        e = timer(); self.step_time = e - b

        if __debug__:
            # print out rmsd to all reference structures for all individuals within 2 kcal/mol
            # of the lowest energy
            # used for statictics
            gene = self.pop[0]
            Eref = gene._fitness_score
            i = 0
            print "  LowE_RMSDs gen:%d" % self.gen,
            while gene._fitness_score > Eref-2.0 and i < len(self.pop)-1:
                print " | %d:"%i,
                adum, bdum, L_coords = gene.phenotype
                for RMSDcalc in self.rmsdCalculators:
                    rmsd = RMSDcalc.computeRMSD(L_coords)
                    print " %5.2f"%rmsd,
                i += 1
                gene = self.pop[i]
            print

        # Update the top-level dictionary
        self.stats.update(self.pop.stats)	
        self.db_entry['best_scores'].append(self.stats['current']['max'])
        return 'searching'



class GA2(GA1):

    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        #for  num, x in enumerate(self.pop):
        #    assert x.cutPoints[1]==7

        #import resource, gc
        #gc.collect()
        history = False

        t0 = time.time()

        # count similar individuals (within clusterEcut of the top scored ind)
        ref = self.pop[0]
        for i, ind in enumerate(self.pop):
            assert ind._fitness_score == ind.score()
        
        refScore = ref._fitness_score # lowest score in pop al all times
        remainder = []
        for i,x in enumerate(self.pop):
            #if x._fitness_score > 0.0:
            if refScore-x._fitness_score > self.clusterEnergyCut:
                break
            remainder.append(i)

        gen = self.gen
        popSize = len(self.pop)
        for ind in self.pop:
            before = ind._fitness_score
            assert ind._fitness_score == ind.score()
        if gen==6:
            import pdb
            pdb.set_trace()
        # build the population from which we will select
        selectionPopulation = []
        selectionPopulationd = {}

        incluster = {}
        tokeep = []
        cst = self.pop[0].scorer.TORSDOF * 0.2983
        if len(remainder)>2:
            print '\n  CLUSTERING %d individual(s) with %.2f'%(len(remainder), self.clusterEnergyCut)
            clusters = self.cluster(remainder)

            print "   CNUM  len best  Rmsd        Score         FEB        <Score>  stdev cluster"    
            for cnum, c in enumerate(clusters):
                # find lowest score individual in cluster
                maxi = self.pop[c[0]]._fitness_score
                rep = c[0]
                scores = [-self.pop[c[0]]._fitness_score]
                incluster[c[0]] = True
                for ind in c[1:]:
                    scores.append(-self.pop[ind]._fitness_score)
                    incluster[ind] = True
                    if self.pop[ind]._fitness_score > maxi:
                        maxi = self.pop[ind]._fitness_score
                        rep = ind

                tokeep.append(self.pop[rep].clone())
                oldScore = tokeep[-1]._fitness_score
                newScore = tokeep[-1].score()
                if abs(oldScore-newScore)>1.:
                    import pdb
                    pdb.set_trace()
                # every best in cluster get best score to guarantee offsprings
                self.pop[rep]._real_score = self.pop[rep]._fitness_score
                self.pop[rep]._fitness_score = refScore
                # add best in cluster to new pop
                selectionPopulation.append(self.pop[rep])
                selectionPopulationd[rep] = True
                
                # compute RMSD
                print "   %3d  %3d  %3d"%(cnum, len(c), rep),
                if len(self.rmsdCalculators):
                    a, b, L_coords = self.pop[rep].phenotype
                    for rmsdc in self.rmsdCalculators:
                        print "%6.2f"%rmsdc.computeRMSD(L_coords),

                print " %12.3f %12.3f %12.3f %6.3f %s"%(-self.pop[rep]._real_score,\
                      -self.pop[rep]._real_score-self.pop[rep].ie+cst, numpy.mean(scores), numpy.std(scores), c)


            if len(clusters)==self.nbClusters:
                self.nbGenWithCstClusters += 1
                if self.nbGenWithCstClusters > 5:
                    self.clusterEnergyCut = self.clusterEnergyCut-0.1
                    if self.clusterEnergyCut < 1.0:
                        return "Clustering Energy reached %.2f"%self.clusterEnergyCut
                    #return "5 generations with %d clusters"%self.nbClusters
            else:
                self.nbClusters = len(clusters)
                self.nbGenWithCstClusters = 0

        ## inject new individuals in the population
        nbNew = int(self.settings['GA_injectRandomInd'] * popSize)
        newIndiv = []
        negEInd = 0
        for ind in self.pop:
            if ind._fitness_score >= 0.0:
                negEInd += 1
        if nbNew and len(remainder)>2:
            while len(newIndiv) < nbNew:
                for k in range(5):
                    indIndex = int(random()*negEInd)
                    ind = self.pop[indIndex].clone() # create an individual
                    j = 0
                    while True:
                        before = ind._fitness_score
                        # randomize genome with 20% chance on each gene
                        attempts = ind.randomize(maxTry=100+100*k+10*j,
                                                 perGenProbabilty=0.3)
                        after = ind._fitness_score
                        nind = self.minimize(ind, **self.settings['GAminimize'])
                        print 'NEW:, %12.3f -> %12.3f (%4d) -> %12.3f rmsd:'%(
                            -before, -after, attempts, -nind._fitness_score),
                        if nind._fitness_score > refScore-self.clusterEnergyCut:
                            a, b, L_coords = nind.phenotype
                            a, b, L_coords_orig = self.pop[indIndex].phenotype
                            for rmsdc in self.rmsdCalculators:
                                print "%6.2f -> %6.2f"%(
                                    rmsdc.computeRMSD(L_coords_orig), rmsdc.computeRMSD(L_coords))
                            break
                        else:
                            print
                        j += 1
                        if j==5:
                            nind = None
                            print 'UNABLE to create good new individual'
                            break
                    if nind:
                        break
                if nind:
                    newIndiv.append(nind)
                    selectionPopulation.append(nind)

        
        # fill selectionPopulation using current population and skipping ones in cluster
        for num, ind in enumerate(self.pop):
            if incluster.get(num, None): continue # skip individuals in clusters
            selectionPopulation.append(ind)
            selectionPopulationd[num] = True
            if len(selectionPopulation)==popSize: break


        while len(selectionPopulation) < popSize-len(tokeep): # only best in clusters are in selection population
            for cnum, c in enumerate(clusters):
                if len(c)==1:
                    for i in range(3):
                        ind = self.pop[c[0]].clone()
                        ind.mutate()
                        if ind._fitness_score is None:
                            indn = self.minimize(ind, nbSteps=5, noImproveStop=2,
                                                 max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                        else:
                            indn = ind
                            indn.score()
                        selectionPopulation.append(indn)
                elif len(c)==2:
                    ind1 = self.pop[c[0]]
                    ind2 = self.pop[c[1]]
                    if ind1._fitness_score > ind2._fitness_score:
                        selectionPopulation.append(ind2)
                    else:
                        selectionPopulation.append(ind1)
                    a,b = self.crossover([ind1, ind2])
                    a.score()
                    an = self.minimize(a, nbSteps=5, noImproveStop=2,
                                       max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                    b.score()
                    bn = self.minimize(b, nbSteps=5, noImproveStop=2,
                                       max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                    selectionPopulation.append(an)
                    selectionPopulation.append(bn)
                elif len(c)==3:
                    ind1 = self.pop[c[0]]
                    ind2 = self.pop[c[1]]
                    ind3 = self.pop[c[2]]
                    if ind1._fitness_score > ind2._fitness_score:
                        if ind1._fitness_score > ind3._fitness_score: # 1 is best
                            selectionPopulation.append(ind2)
                            selectionPopulation.append(ind3)
                            best = ind1
                        else: # 3 is largest
                            selectionPopulation.append(ind1)
                            selectionPopulation.append(ind2)
                            best = ind3
                    else: # 2 is better than 1
                        if ind2._fitness_score > ind3._fitness_score: # 2 is best
                            selectionPopulation.append(ind1)
                            selectionPopulation.append(ind3)
                            best = ind2
                        else: # 3 is largest
                            selectionPopulation.append(ind1)
                            selectionPopulation.append(ind2)
                            best = ind3
                    best.mutate()
                    if best._fitness_score is None:
                        bestn = self.minimize(best, nbSteps=5, noImproveStop=2,
                                              max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                    else:
                        bestn = best
                        bestn.score()
                    selectionPopulation.append(bestn)
                else:
                    j = 0
                    for i in range(len(c)):
                        if selectionPopulationd.get(c[i], None) is None:
                            selectionPopulation.append(self.pop[c[i]])
                            j+=1
                        if j==3: break
                        
        selectionPopulation.sort(sc_maximize) # so that printing our choices makes sense
        self.pop.data = selectionPopulation
        # prepare the population for selection
        self.pop.touch()
        self.pop.scale()

        # restore real score for best in cluster
        for ind in self.pop:
            if hasattr(ind, '_real_score'):
                ind._fitness_score = ind._real_score
                delattr(ind, '_real_score')
        # create crossover and mutate
        gaind = []
        replace = int(self.settings['GA_replace'] * popSize)
        p_crossover = self.settings['GA_crossover']
        print ' ',
        if gen==7:
            import pdb
            pdb.set_trace()
            # 112, 101
        for i in range(0,replace,2):
            mom, dad = self.pop.select(2)
            # indices of selected individuals
            p1Index, p2Index = self.pop.selector._selected
            alreadyAdded = []
            ##
            ## version where we minimize cross and mutate
            ## in this version the lowest score found after cross
            ## might get lost if we mutate later and it does not get better
            ## yet it seems to work the best
            ##
            o1star = o2star = o1star1 = o2star1 = ''
            if flip_coin(p_crossover):
                bro, sis = self.crossover((mom,dad))
                bro.score()
                sis.score()

                bron = self.minimize(bro, nbSteps=5, noImproveStop=2,
                                     max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                nbSteps1 = self._totalStepInLastMinimize
                sisn = self.minimize(sis, nbSteps=5, noImproveStop=2,
                                     max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                nbSteps2 = self._totalStepInLastMinimize
                if bron._fitness_score>refScore:
                    o1star = '*'
                    refScore = bron._fitness_score
                    gaind.append(bron)
                    alreadyAdded.append(bron)
                    oldScore = bron._fitness_score
                    newScore = bron.score()
                    if abs(oldScore-newScore)>1.:
                        import pdb
                        pdb.set_trace()
                if sisn._fitness_score>refScore:
                    refScore = sisn._fitness_score
                    o2star = "*"
                    gaind.append(sisn)
                    oldScore = sisn._fitness_score
                    newScore = sisn.score()
                    if abs(oldScore-newScore)>1.:
                        import pdb
                        pdb.set_trace()
                    alreadyAdded.append(sisn)
                if o1star or o2star:
                    print '\n  (%3d, %3d) CRO O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                        p1Index, p2Index,
                        -bro._fitness_score, -bron._fitness_score, o1star, nbSteps1,
                        -sis._fitness_score, -sisn._fitness_score, o2star, nbSteps2),
                bro = bron
                sis = sisn
                
            else:
                bro = dad
                sis = mom

            a1 = bro._fitness_score
            broc = bro.clone()
            mutated1 = broc.mutate()
            if mutated1:
                c = broc.score()
                bron = self.minimize(broc, nbSteps=5, noImproveStop=2,
                                     max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                if bron._fitness_score>refScore:
                    o1star1 = '*'
                    refScore = bron._fitness_score
                if o1star1:
                    if not (o1star or o2star):
                        print '\n  (%3d, %3d)'%(p1Index, p2Index),
                    print ' MUT O1: %12.3f -> %12.3f -> %12.3f%1s (%4d)'%(
                        -a1, -c, -bron._fitness_score, o1star1, self._totalStepInLastMinimize),
                #if bron._fitness_score > bro._fitness_score:
                bro = bron
                
            a = sis._fitness_score
            sisc = sis.clone()
            mutated = sisc.mutate()
            if mutated:
                c = sisc.score()
                sisn = self.minimize(sisc, nbSteps=5, noImproveStop=2,
                                     max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                if sisn._fitness_score>refScore:
                    o2star1 = '*'
                    refScore = sisn._fitness_score
                if o2star1:
                    if not (o1star or o2star or o1star1):
                        print '\n  (%3d, %3d)'%(p1Index, p2Index),
                    print ' MUT O2: %12.3f -> %12.3f -> %12.3f%1s (%4d)'%(
                        -a, -c, -sisn._fitness_score, o2star1, self._totalStepInLastMinimize),
                #if sisn._fitness_score > sis._fitness_score:
                sis = sisn
                
            if not (o1star or o2star or o1star1 or o2star1):
                print '(%3d, %3d)'%(p1Index, p2Index),
            else:
                print '\n ',
                
            if bro not in alreadyAdded:
                gaind.append(bro)
                oldScore = bro._fitness_score
                newScore = bro.score()
                if abs(oldScore-newScore)>1.:
                    import pdb
                    pdb.set_trace()
            if sis not in alreadyAdded:
                gaind.append(sis)
                oldScore = sis._fitness_score
                newScore = sis.score()
                if abs(oldScore-newScore)>1.:
                    import pdb
                    pdb.set_trace()

        print
        
        tokeep.sort(sc_maximize) #MS not sure we need this

        # keep only clusters with e< bestE+2kcal
        i = len(tokeep)
        while i>0 and tokeep[i-1]._fitness_score<(refScore-2.0):
            i -= 1
        print 'keeping %d clusters out of %d'%(i, len(tokeep))
        tokeep1 = tokeep[:i]
        gaind += tokeep[i:] # other clusters compete with gaind

        for ind in tokeep1:
            oldScore = ind._fitness_score
            newScore = ind.score()
            if abs(oldScore-newScore)>1.:
                import pdb
                pdb.set_trace()
            
        if len(newIndiv):
            tokeep1 += newIndiv
        for j, ind in enumerate(tokeep[i:]):
            print 'Cluster %d has to compete with gaind'%(i+j)

        # sort the population using _fitness_score
        if len(tokeep1)+len(gaind)>popSize:
            gaind.sort(sc_maximize)
            pop = tokeep1 + gaind[:popSize-len(tokeep1)]
        else:
            pop = tokeep1 + gaind
            for ind in self.pop.data[:popSize-len(tokeep1)-len(gaind)]:
                pop.append( ind.clone() )
            for ind in self.pop.data[:popSize-len(tokeep1)-len(gaind)]:
                oldScore = ind._fitness_score
                newScore = ind.score()
                if abs(oldScore-newScore)>1.:
                    import pdb
                    pdb.set_trace()

        pop.sort(sc_maximize)

        #if len(tokeep)>popSize8.5:
        #    print 'annealing'
        #    self.anneal(self, ind, solisWets, nbRounds=50, roundFails=10, dx=1.0, absVar=None, verbose=True):    
        assert self.lastGenBest < pop[0]._fitness_score
        
        # now rebuild the population by keeping the to tokeep ones and
        #for i, ind in enumerate(tokeep):
        #    if ind._fitness_score > gaind[i]._fitness_score:
        #        gaind[len(gaind)-1-i] = ind

        #assert pop[0]._fitness_score==refScore
        assert len(pop)==popSize
        self.pop.data = pop
        
        return 'searching'



class GA2_1(GA1):

    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        sanityCheck = True
        GAminimize = self.settings['GAminimize']
        self._nbMut = 0
        
        # SANITY CHECK
        ## if sanityCheck:
        ##     for i, ind in enumerate(self.pop):
        ##         before = ind._fitness_score
        ##         assert ind._fitness_score == ind.score()
        
        # count similar individuals (within clusterEcut of the top scored ind)
        ref = self.pop[0]
        refScore = ref._fitness_score # lowest score in pop al all times
        remainder = []
        for i,x in enumerate(self.pop):
            #if x._fitness_score > 0.0:
            if refScore-x._fitness_score > self.clusterEnergyCut:
                break
            remainder.append(i)

        gen = self.gen
        popSize = len(self.pop)

        # build the population from which we will select
        selectionPopulation = []
        selectionPopulationd = {}

        incluster = {} # keep track who is in a cluster
        tokeep = [] # clones of best in cluster
        cst = self.pop[0].scorer.TORSDOF * 0.2983
        if len(remainder)>2:
            print '\n  CLUSTERING %d individual(s) with %.2f'%(len(remainder), self.clusterEnergyCut)
            clusters = self.cluster(remainder)

            print "   CNUM  len best  Rmsd        Score         FEB        <Score>  stdev cluster"
            bestEinClust = []
            ediffCluster = 0.0
            for cnum, c in enumerate(clusters):
                # find lowest score individual in cluster
                maxi = self.pop[c[0]]._fitness_score
                rep = c[0]
                scores = [-self.pop[c[0]]._fitness_score]
                incluster[c[0]] = True
                for ind in c[1:]:
                    scores.append(-self.pop[ind]._fitness_score)
                    incluster[ind] = True
                    if self.pop[ind]._fitness_score > maxi:
                        maxi = self.pop[ind]._fitness_score
                        rep = ind
                bestEinClust.append(self.pop[rep]._fitness_score)
                if cnum < len(self.clustersBestE):
                    ediffCluster += self.pop[rep]._fitness_score - self.clustersBestE[cnum]
                tokeep.append(self.pop[rep].clone())
                ## if sanityCheck:
                ##     oldScore = tokeep[-1]._fitness_score
                ##     newScore = tokeep[-1].score()
                ##     assert oldScore==newScore

                # every best in cluster get best score to guarantee offsprings
                self.pop[rep]._real_score = self.pop[rep]._fitness_score
                self.pop[rep]._fitness_score = refScore

                # add best in cluster to selection pop
                selectionPopulation.append(self.pop[rep])
                selectionPopulationd[rep] = True
                
                # compute RMSD
                print "   %3d  %3d  %3d"%(cnum, len(c), rep),
                if len(self.rmsdCalculators):
                    a, b, L_coords = self.pop[rep].phenotype
                    for rmsdc in self.rmsdCalculators:
                        print "%6.2f"%rmsdc.computeRMSD(L_coords),

                print " %12.3f %12.3f %12.3f %6.3f %s"%(-self.pop[rep]._real_score,\
                      -self.pop[rep]._real_score-self.pop[rep].LL+cst, numpy.mean(scores), numpy.std(scores), c)

            self.clustersBestE = bestEinClust

            if len(clusters) and ediffCluster==0.0:
                self.nbNoClusterEimprovement += 1
                if self.nbNoClusterEimprovement==5:
                    return "No improvement in best in %d clusters for 5 generations"%len(clusters)

            if len(clusters)==self.nbClusters and ediffCluster==0.0:
                self.nbGenWithCstClusters += 1
                if self.nbGenWithCstClusters > 5:
                    if self.clusterEnergyCut >= 1.0:
                        self.clusterEnergyCut = self.clusterEnergyCut-0.1
#                    self.clusterEnergyCut = self.clusterEnergyCut-0.1
#                    if self.clusterEnergyCut < 1.0:
#                        return "Clustering Energy reached %.2f"%self.clusterEnergyCut
                    #return "5 generations with %d clusters"%self.nbClusters
            else:
                self.nbClusters = len(clusters)
                self.nbGenWithCstClusters = 0
        else: # nothing to cluster -> keep best
            tokeep.append(self.pop[0].clone())
            incluster[0] = True
           

        # fill selectionPopulation using current population and skipping ones in cluster
        for num, ind in enumerate(self.pop):
            if incluster.get(num, None): continue # skip individuals in clusters
            selectionPopulation.append(ind)
            selectionPopulationd[num] = True
            if len(selectionPopulation)==popSize: break

        if len(selectionPopulation) == len(tokeep): # only best in clusters are in selection population
            if len(selectionPopulation) <= 2:
                return '1 or 2 clusters left'
                        
        #selectionPopulation.sort(sc_maximize) # so that printing our choices makes sense
        self.pop.data = selectionPopulation

        # prepare the population for selection
        self.pop.touch()
        self.pop.scale()
        # restore real score for best in cluster
        for ind in self.pop:
            if hasattr(ind, '_real_score'):
                ind._fitness_score = ind._real_score
                delattr(ind, '_real_score')

        print ' ',

        #if gen==7:
        #    import pdb
        #    pdb.set_trace()

        # create crossover and mutate
        replace = int(self.settings['GA_replace'] * popSize)
        p_crossover = self.settings['GA_crossover']
        gaind = []
        gaindSize = popSize - len(tokeep)
        while len(gaind) < gaindSize:
            mom, dad = self.pop.select(2)
            # indices of selected individuals
            p1Index, p2Index = self.pop.selector._selected
            if mom._fitness_score > dad._fitness_score:
                best2 = [mom, dad] # keep track of best individuals for this parents
            else:
                best2 = [dad, mom] # keep track of best individuals for this parents
            ##
            ## version where we minimize cross and mutate
            ## in this version the lowest score found after cross
            ## might get lost if we mutate later and it does not get better
            ## yet it seems to work the best
            ##
            o1star = o2star = o1star1 = o2star1 = ''
            if flip_coin(p_crossover):
                bro, sis = self.crossover((mom,dad))
                bro.score()
                sis.score()
                bron = self.minimize(bro, **GAminimize)
                if bron._fitness_score > best2[0]._fitness_score:
                    best2 = [bron, best2[0]]
                elif bron._fitness_score > best2[1]._fitness_score:
                    best2 = [best2[0], bron]
                nbSteps1 = self._totalStepInLastMinimize
                sisn = self.minimize(sis, **GAminimize)
                if sisn._fitness_score > best2[0]._fitness_score:
                    best2 = [sisn, best2[0]]
                elif sisn._fitness_score > best2[1]._fitness_score:
                    best2 = [best2[0], sisn]
                nbSteps2 = self._totalStepInLastMinimize
                if bron._fitness_score>refScore:
                    o1star = '*'
                    refScore = bron._fitness_score
                    #gaind.append(bron)
                    ## if sanityCheck:
                    ##     oldScore = bron._fitness_score
                    ##     newScore = bron.score()
                    ##     assert oldScore== newScore
                if sisn._fitness_score>refScore:
                    refScore = sisn._fitness_score
                    o2star = "*"
                    #gaind.append(sisn)
                    ## if sanityCheck:
                    ##     oldScore = sisn._fitness_score
                    ##     newScore = sisn.score()
                    ##     assert oldScore== newScore
                if o1star or o2star:
                    print '\n  (%3d, %3d) CRO O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                        p1Index, p2Index,
                        -bro._fitness_score, -bron._fitness_score, o1star, nbSteps1,
                        -sis._fitness_score, -sisn._fitness_score, o2star, nbSteps2),
                bro = bron
                sis = sisn
                
            else:
                bro = dad
                sis = mom

            a1 = bro._fitness_score
            broc = bro.clone()
            mutated1 = broc.mutate()
            self._nbMut += mutated1
            if mutated1:
                c = broc.score()
                bron = self.minimize(broc, **GAminimize)
                if bron._fitness_score > best2[0]._fitness_score:
                    best2 = [bron, best2[0]]
                elif bron._fitness_score > best2[1]._fitness_score:
                    best2 = [best2[0], bron]
                if bron._fitness_score>refScore:
                    o1star1 = '*'
                    refScore = bron._fitness_score
                if o1star1:
                    if not (o1star or o2star):
                        print '\n  (%3d, %3d)'%(p1Index, p2Index),
                    print ' MUT O1: %12.3f -> %12.3f -> %12.3f%1s (%4d)'%(
                        -a1, -c, -bron._fitness_score, o1star1, self._totalStepInLastMinimize),
                
            a = sis._fitness_score
            sisc = sis.clone()
            mutated = sisc.mutate()
            self._nbMut += mutated
            if mutated:
                c = sisc.score()
                sisn = self.minimize(sisc, **GAminimize)
                if sisn._fitness_score > best2[0]._fitness_score:
                    best2 = [sisn, best2[0]]
                elif sisn._fitness_score > best2[1]._fitness_score:
                    best2 = [best2[0], sisn]
                if sisn._fitness_score>refScore:
                    o2star1 = '*'
                    refScore = sisn._fitness_score
                if o2star1:
                    if not (o1star or o2star or o1star1):
                        print '\n  (%3d, %3d)'%(p1Index, p2Index),
                    print ' MUT O2: %12.3f -> %12.3f -> %12.3f%1s (%4d)'%(
                        -a, -c, -sisn._fitness_score, o2star1, self._totalStepInLastMinimize),
                
            if not (o1star or o2star or o1star1 or o2star1):
                print '(%3d, %3d)'%(p1Index, p2Index),
            else:
                print '\n ',
                
            gaind.append(best2[0])
            gaind.append(best2[1])
            ## if sanityCheck:
            ##     oldScore = best2[0]._fitness_score
            ##     newScore = best2[0].score()
            ##     assert oldScore== newScore
            ##     oldScore = best2[1]._fitness_score
            ##     newScore = best2[1].score()
            ##     assert oldScore== newScore

        print

        self.pop.data.sort(sc_maximize)

        pop = tokeep + gaind 
        pop.sort(sc_maximize)
        if sanityCheck:
            assert self.lastGenBest <= pop[0]._fitness_score, "ERROR: lost best score %f -> %f"%(
                self.lastGenBest, pop[0]._fitness_score)
        self.pop.data = pop[:popSize]

        print 'Mutation Rate %.4f'%(float(self._nbMut) / (popSize*len(self.pop[0])))

        return 'searching'


class GA2_2(GA1):
    """
    GA for local search withn 2 angstrom RMSD of a given result
    """
    
    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        sanityCheck = True
        GAminimize = self.settings['GAminimize']
        self._nbMut = 0
        popSize = len(self.pop)
        
        cst = self.pop[0].scorer.TORSDOF * 0.2983
                        
        # prepare the population for selection
        self.pop.touch()
        self.pop.scale()

        print ' ',

        # create crossover and mutate
        replace = int(self.settings['GA_replace'] * popSize)
        p_crossover = self.settings['GA_crossover']
        gaind = []
        gaindSize = popSize
        rmsdCalc = self.rmsdCalculators[0]
        refScore = self.pop[0]._fitness_score
        
        while len(gaind) < gaindSize:
            mom, dad = self.pop.select(2)
            # indices of selected individuals
            p1Index, p2Index = self.pop.selector._selected
            if mom._fitness_score > dad._fitness_score:
                best2 = [mom, dad] # keep track of best individuals for this parents
            else:
                best2 = [dad, mom] # keep track of best individuals for this parents
            ##
            ## version where we minimize cross and mutate
            ## in this version the lowest score found after cross
            ## might get lost if we mutate later and it does not get better
            ## yet it seems to work the best
            ##
            o1star = o2star = o1star1 = o2star1 = ''
            if flip_coin(p_crossover):
                bro, sis = self.crossover((mom,dad))

                bro.score()
                rmsd1 = rmsdCalc.computeRMSD(bro.phenotype[2])
                if rmsd1 <= 2.0:
                    bron = self.minimize(bro, **GAminimize)
                    rmsd11 = rmsdCalc.computeRMSD(bron.phenotype[2])
                    if rmsd11 <= 2.0:
                        if bron._fitness_score > best2[0]._fitness_score:
                            best2 = [bron, best2[0]]
                        elif bron._fitness_score > best2[1]._fitness_score:
                            best2 = [best2[0], bron]
                        nbSteps1 = self._totalStepInLastMinimize

                        if bron._fitness_score>refScore:
                            o1star = '*'
                            refScore = bron._fitness_score
                            gaind.append(bron)
                    else:
                        bron = bro
                else:
                    bron = dad

                sis.score()
                rmsd2 = rmsdCalc.computeRMSD(bro.phenotype[2])
                if rmsd2 <= 2.0:
                    sisn = self.minimize(sis, **GAminimize)
                    rmsd21 = rmsdCalc.computeRMSD(sisn.phenotype[2])
                    if rmsd21 <= 2.0:
                        if sisn._fitness_score > best2[0]._fitness_score:
                            best2 = [sisn, best2[0]]
                        elif sisn._fitness_score > best2[1]._fitness_score:
                            best2 = [best2[0], sisn]
                        nbSteps2 = self._totalStepInLastMinimize

                        if sisn._fitness_score>refScore:
                            refScore = sisn._fitness_score
                            o2star = "*"
                            gaind.append(sisn)
                    else:
                        sisn = sis
                else:
                    sisn = mom

                if o1star or o2star:
                    print '\n  (%3d, %3d) CRO O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                        p1Index, p2Index,
                        -bro._fitness_score, -bron._fitness_score, o1star, nbSteps1,
                        -sis._fitness_score, -sisn._fitness_score, o2star, nbSteps2),
                bro = bron
                sis = sisn
                
            else:
                bro = dad
                sis = mom

            a1 = bro._fitness_score
            broc = bro.clone()
            mutated1 = broc.mutate()
            self._nbMut += mutated1
            if mutated1:
                c = broc.score()
                rmsd31 = rmsdCalc.computeRMSD(broc.phenotype[2])
                if rmsd31 <= 2.0:
                    bron = self.minimize(broc, **GAminimize)
                    rmsd32 = rmsdCalc.computeRMSD(bron.phenotype[2])
                    if rmsd32 <= 2.0:
                        if bron._fitness_score > best2[0]._fitness_score:
                            best2 = [bron, best2[0]]
                        elif bron._fitness_score > best2[1]._fitness_score:
                            best2 = [best2[0], bron]

                        if bron._fitness_score>refScore:
                            o1star1 = '*'
                            refScore = bron._fitness_score
                        if o1star1:
                            if not (o1star or o2star):
                                print '\n  (%3d, %3d)'%(p1Index, p2Index),
                                print ' MUT O1: %12.3f -> %12.3f -> %12.3f%1s (%4d)'%(
                                    -a1, -c, -bron._fitness_score, o1star1, self._totalStepInLastMinimize),
                
            a = sis._fitness_score
            sisc = sis.clone()
            mutated = sisc.mutate()
            self._nbMut += mutated
            if mutated:
                c = sisc.score()
                rmsd41 = rmsdCalc.computeRMSD(sisc.phenotype[2])
                if rmsd41 <= 2.0:
                    sisn = self.minimize(sisc, **GAminimize)
                    rmsd42 = rmsdCalc.computeRMSD(sisn.phenotype[2])
                    if rmsd42 <= 2.0:
                        if sisn._fitness_score > best2[0]._fitness_score:
                            best2 = [sisn, best2[0]]
                        elif sisn._fitness_score > best2[1]._fitness_score:
                            best2 = [best2[0], sisn]
                        if sisn._fitness_score>refScore:
                            o2star1 = '*'
                            refScore = sisn._fitness_score
                        if o2star1:
                            if not (o1star or o2star or o1star1):
                                print '\n  (%3d, %3d)'%(p1Index, p2Index),
                            print ' MUT O2: %12.3f -> %12.3f -> %12.3f%1s (%4d)'%(
                                -a, -c, -sisn._fitness_score, o2star1, self._totalStepInLastMinimize),
                
            if not (o1star or o2star or o1star1 or o2star1):
                print '(%3d, %3d)'%(p1Index, p2Index),
            else:
                print '\n ',

            gaind.append(best2[0])
            gaind.append(best2[1])

        print

        #self.pop.data.sort(sc_maximize)

        self.pop.extend(gaind)
        self.pop.sort()
        if sanityCheck:
            assert self.lastGenBest <= self.pop[0]._fitness_score, "ERROR: lost best score %f -> %f"%(
                self.lastGenBest, self.pop[0]._fitness_score)
        self.pop.data = self.pop.data[:popSize]

        print 'Mutation Rate %.4f'%(float(self._nbMut) / (popSize*len(self.pop[0])))

        return 'searching'



class GA3(GA1):

    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        #for  num, x in enumerate(self.pop):
        #    assert x.cutPoints[1]==7

        #import resource, gc
        #gc.collect()
        history = False

        t0 = time.time()

        # count similar individuals (within clusterEcut of the top scored ind)
        ref = self.pop[0]
        refScore = ref._fitness_score # lowest score in pop al all times
        remainder = []
        for i,x in enumerate(self.pop):
            if x._fitness_score > 0.0:
                remainder.append(i)

        gen = self.gen
        popSize = len(self.pop)
        tokeep = []
        #if gen==2:
        #    import pdb
        #    pdb.set_trace()
        # build the population from which we will select
        selectionPopulation = []

        incluster = {}
        if len(remainder)>2:
            print '\n  CLUSTERING %d individual(s)'%(len(remainder))
            clusters = self.cluster(remainder)
            for c in clusters:
                # find lowest score individual in cluster
                maxi = self.pop[c[0]]._fitness_score
                rep = c[0]
                incluster[c[0]] = True
                for ind in c[1:]:
                    incluster[ind] = True
                    if self.pop[ind]._fitness_score > maxi:
                        maxi = self.pop[ind]._fitness_score
                        rep = ind

                # add best in cluster to new pop
                selectionPopulation.append(self.pop[rep])
                tokeep.append(self.pop[rep])
                
                # compute RMSD
                if len(self.rmsdCalculators):
                    a, b, L_coords = self.pop[rep].phenotype
                    for rmsdc in self.rmsdCalculators:
                        print "    rmsd: %6.2f"%rmsdc.computeRMSD(L_coords),

                print " #inClust", len(c), "ClustMemb", c, rep, -self.pop[rep]._fitness_score

        ## inject new individuals in the population
        nbNew = int(self.settings['GA_injectRandomInd'] * popSize)
        if nbNew:
            template = self.pop.model_genome
            e1 = time.time()
            while len(newIndiv) < nbNew2:
                ind = template.clone() # create an individual
                ind.initialize(self.settings)
                attempts = ind.randomize(maxTry=self.settings['constraintMaxTry'])
                before = ind._fitness_score
                if self.enableLocalSearch:
                    nind = self.minimize(ind, **self.settings['GAminimize'])
                else:
                    nind = ind

                o1star = ''
                if nind._fitness_score>refScore:
                    o1star = '*'
                print "      NEW: %4d attempts %12.3f -> %12.3f%1s (%4d)"%(
                    attempts, -before, -nind._fitness_score, o1star, self._totalStepInLastMinimize)

                selectionPopulation.append(nind)
                if self.settings['savePopulationHist']:
                    nind.history = 'N(%d) %.2f '%(gen, nind._fitness_score)
        
        # fill selectionPopulation using current population and skipping ones in cluster
        for num, ind in enumerate(self.pop):
            if incluster.get(num, None): continue # skip individuals in clusters
            selectionPopulation.append(ind)
            if len(selectionPopulation)==popSize: break

        self.pop.data = selectionPopulation
        # prepare the population for selection
        self.pop.touch()
        self.pop.scale()

        # create crossover and mutate
        gaind = []
        replace = int(self.settings['GA_replace'] * popSize)
        p_crossover = self.settings['GA_crossover']
        for i in range(0,replace,2):
            mom, dad = self.pop.select(2)
            # indices of selected individuals
            p1Index, p2Index = self.pop.selector._selected
            alreadyAdded = []

            ##
            ## version where we we cross and mutate without minimizing
            ##
            if flip_coin(p_crossover):
                bro,sis = self.crossover((mom,dad))
            else:
                bro = dad
                sis = mom

            a = bro._fitness_score
            broc = bro.clone()
            mutated = broc.mutate()

            a = sis._fitness_score
            sisc = sis.clone()
            mutated = sisc.mutate()

            if broc._score is None:
                broc.score()
                bron = self.minimize(broc, nbSteps=5, noImproveStop=2,
                                     max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                bro = bron
            else:
                bro = broc
                
            if sisc._score is None:
                sisc.score()
                sisn = self.minimize(sisc, nbSteps=5, noImproveStop=2,
                                     max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                sis = sisn
            else:
                sis = sisc

            o1star = o2star = ''
            if bro._fitness_score>refScore:
                o1star = '*'
                refScore = bro._fitness_score
            if sis._fitness_score>refScore:
                o2star = '*'
                refScore = sis._fitness_score
            print '  A: %3d %12.3f   B: %3d %12.3f   O1: %12.3f%1s   O2: %12.3f%1s'%(
                p1Index, -mom._fitness_score, p2Index, -dad._fitness_score,
                -bro._fitness_score, o1star, -sis._fitness_score, o2star)
            ##    
            ## END version where we we cross and mutate without minimizing
            ##
            gaind.append(bro)
            gaind.append(sis)

        tokeep.sort(sc_maximize) #MS notsure we need this

        # keep only clusters with e< bestE+2kcal
        i = len(tokeep)-1
        while i>=0 and tokeep[i]._fitness_score<(refScore-2.0):
            i -= 1
        tokeep = tokeep[:i]

        gaind += tokeep[i:] # other clusters compete with gaind
        print 'keeping %d clusters'%(len(tokeep))

        # sort the population using _fitness_score
        if len(tokeep)+len(gaind)>popSize:
            gaind.sort(sc_maximize)
            pop = tokeep + gaind[:popSize-len(tokeep)]
        else:
            pop = tokeep + gaind + self.pop.data[:popSize-len(tokeep)-len(gaind)]

        pop.sort(sc_maximize)

        #if len(tokeep)>popSize8.5:
        #    print 'annealing'
        #    self.anneal(self, ind, solisWets, nbRounds=50, roundFails=10, dx=1.0, absVar=None, verbose=True):    
        assert self.lastGenBest < pop[0]._fitness_score
        
        # now rebuild the population by keeping the to tokeep ones and
        #for i, ind in enumerate(tokeep):
        #    if ind._fitness_score > gaind[i]._fitness_score:
        #        gaind[len(gaind)-1-i] = ind

        #assert pop[0]._fitness_score==refScore
        assert len(pop)==popSize
        self.pop.data = pop

        return 'searching'


class GA4(GA1):
    """ no clustering"""
    
    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        #for  num, x in enumerate(self.pop):
        #    assert x.cutPoints[1]==7

        #import resource, gc
        #gc.collect()
        history = False

        t0 = time.time()

        # count similar individuals (within clusterEcut of the top scored ind)
        ref = self.pop[0]
        refScore = ref._fitness_score # lowest score in pop al all times
        gen = self.gen
        popSize = len(self.pop)

        # copy elite
        tokeep = []
        for i in range(3):
            tokeep.append(self.pop[i].clone())

        # prepare the population for selection
        self.pop.touch()
        self.pop.scale()

        # create crossover and mutate
        gaind = []
        replace = int(self.settings['GA_replace'] * popSize)
        p_crossover = self.settings['GA_crossover']
        for i in range(0,replace,2):
            mom, dad = self.pop.select(2)
            # indices of selected individuals
            p1Index, p2Index = self.pop.selector._selected
            alreadyAdded = []

            if flip_coin(p_crossover):
                bro,sis = self.crossover((mom,dad))
            else:
                bro = dad.clone()
                sis = mom.clone()

            a = bro._fitness_score
            mutated = bro.mutate()

            a = sis._fitness_score
            mutated = sis.mutate()

            if bro._score is None:
                bro.score()
                bro = self.minimize(bro, nbSteps=5, noImproveStop=2,
                                    max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                
            if sis._score is None:
                sis.score()
                sis = self.minimize(sis, nbSteps=5, noImproveStop=2,
                                    max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)

            o1star = o2star = ''
            if bro._fitness_score>refScore:
                o1star = '*'
                refScore = bro._fitness_score
            if sis._fitness_score>refScore:
                o2star = '*'
                refScore = sis._fitness_score
            print '  A: %3d %12.3f   B: %3d %12.3f   O1: %12.3f%1s   O2: %12.3f%1s'%(
                p1Index, -mom._fitness_score, p2Index, -dad._fitness_score,
                -bro._fitness_score, o1star, -sis._fitness_score, o2star)
            ##    
            ## END version where we we cross and mutate without minimizing
            ##
            gaind.append(bro)
            gaind.append(sis)

        # elitism
        for i, ind in enumerate(tokeep):
            if ind._fitness_score > gaind[len(gaind)-1-i]._fitness_score:
                gaind[len(gaind)-1-i] = ind

        # fill population with old members
        i += 1
        while len(gaind)<popSize:
            gaind.append(self.pop[i])
            i += 1
        gaind = gaind[:popSize]
        gaind.sort(sc_maximize)

        #if len(tokeep)>popSize8.5:
        #    print 'annealing'
        #    self.anneal(self, ind, solisWets, nbRounds=50, roundFails=10, dx=1.0, absVar=None, verbose=True):    
        assert self.lastGenBest < gaind[0]._fitness_score
        
        # now rebuild the population by keeping the to tokeep ones and
        #for i, ind in enumerate(tokeep):
        #    if ind._fitness_score > gaind[i]._fitness_score:
        #        gaind[len(gaind)-1-i] = ind

        #assert pop[0]._fitness_score==refScore
        assert len(gaind)==popSize
        self.pop.data = gain

        return 'searching'



class GA5(GA1):
    """ like 4 but old pop and new pop compete"""
    
    def step(self):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        #for  num, x in enumerate(self.pop):
        #    assert x.cutPoints[1]==7

        #import resource, gc
        #gc.collect()
        history = False

        t0 = time.time()

        # count similar individuals (within clusterEcut of the top scored ind)
        ref = self.pop[0]
        refScore = ref._fitness_score # lowest score in pop al all times
        gen = self.gen
        popSize = len(self.pop)

        # copy elite
        tokeep = []
        for i in range(3):
            tokeep.append(self.pop[i].clone())

        # prepare the population for selection
        self.pop.touch()
        self.pop.scale()

        # create crossover and mutate
        gaind = []
        replace = int(self.settings['GA_replace'] * popSize)
        p_crossover = self.settings['GA_crossover']
        for i in range(0,replace,2):
            mom, dad = self.pop.select(2)
            # indices of selected individuals
            p1Index, p2Index = self.pop.selector._selected
            alreadyAdded = []

            if flip_coin(p_crossover):
                bro,sis = self.crossover((mom,dad))
            else:
                bro = dad.clone()
                sis = mom.clone()

            a = bro._fitness_score
            mutated = bro.mutate()

            a = sis._fitness_score
            mutated = sis.mutate()

            if bro._score is None:
                bro.score()
                bro = self.minimize(bro, nbSteps=5, noImproveStop=2,
                                    max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)
                
            if sis._score is None:
                sis.score()
                sis = self.minimize(sis, nbSteps=5, noImproveStop=2,
                                    max_steps=200, MAX_FAIL=8, MIN_VAR=0.01)

            o1star = o2star = ''
            if bro._fitness_score>refScore:
                o1star = '*'
                refScore = bro._fitness_score
            if sis._fitness_score>refScore:
                o2star = '*'
                refScore = sis._fitness_score
            print '  A: %3d %12.3f   B: %3d %12.3f   O1: %12.3f%1s   O2: %12.3f%1s'%(
                p1Index, -mom._fitness_score, p2Index, -dad._fitness_score,
                -bro._fitness_score, o1star, -sis._fitness_score, o2star)
            ##    
            ## END version where we we cross and mutate without minimizing
            ##
            gaind.append(bro)
            gaind.append(sis)

        # elitism
        newpop = gaind + self.pop.data[len(tokeep):]
        newpop.sort(sc_maximize)
        newpop = tokeep+newpop
        newpop = newpop[:popSize]
        newpop.sort(sc_maximize)

        assert self.lastGenBest < newpop[0]._fitness_score
        assert len(newpop)==popSize
        self.pop.data = newpop

        return 'searching'


class GA6(GA1):
    """
    like GA1 but
       cluster at 2.Kcal fixed
       if all population in clusters stop
    """
    
    def post_evolve(self):
        solutions = []
        
        # copy population
        finalPop = []
        for ind in self.pop:
            finalPop.append(ind.clone())

        # find clusters
        remainder = range(len(self.pop))
        clusters = self.cluster(remainder)

        #import pdb
        #pdb.set_trace()

        # no mutation
        self.settings['GA_crossover'] = 1.0
        
        refScore = self.pop[0]._fitness_score
        # do GA on clusters
        from random import random
        for cnum, c in enumerate(clusters):
            bestScore = -100000
            clusterPop = []
            for num in c:
                clusterPop.append(finalPop[num])
                if finalPop[num]._fitness_score > bestScore:
                    bestScore = finalPop[num]._fitness_score
                    best = num
                
            if bestScore < refScore-2.0: continue
            print "#######################################################################"
            print 'Optimizing cluster %d, best %f'%(cnum, -finalPop[best]._fitness_score)
            # create population from cluster
            self.pop.data = clusterPop
            while 1:
                mom = self.pop[int(random()*len(self.pop))]
                dad = self.pop[int(random()*len(self.pop))]
                bro, sis = self.crossover([mom, dad])
                bro.score()
                clusterPop.append(bro)
                if len(self.pop)==len(finalPop): break
                sis.score()
                clusterPop.append(sis)
                if len(self.pop)==len(finalPop): break
                momc = mom.clone()
                momc.mutate()
                momc.score()
                clusterPop.append(momc)
                if len(self.pop)==len(finalPop): break
                dadc = dad.clone()
                dadc.mutate()
                dadc.score()
                clusterPop.append(dadc)
                if len(self.pop)==len(finalPop): break
                
            status = 'searching'
            coarse_gen = self.gen
            self.gen = 0
            self.pop.touch()
            self.pop.scale()
            self.pop.sort()
            p_dev = self.pop_deviation()
            f, args, kw = self.callbacks['postGeneration']
            f(*args, **kw)
            #while(self.gen < 10 and p_dev>0.001 and status=='searching'):
            while(p_dev>0.001 and status=='searching'):
                # GA step where crossover, mutation, replacement, local search can occur
                status = self.step(mode='optimizeCluster')
            
                # Population Coefficient of variation (CV): SD/mean
                p_dev = self.pop_deviation()
                print 'POP std', self.p_dev
                # Write out the generation information
                self.iteration_output()
                f, args, kw = self.callbacks['postGeneration']
                if f:
                    val = f(*args, **kw)
                    if val=='end':
                        print 'GA is terminated by', 
                        print f.function.im_func.__name__
            print '  cluster %d optimized, best %f'%(cnum, -self.pop[0]._fitness_score)
            #import pdb
            #pdb.set_trace()
            solutions.append(self.pop[0].clone())

        # save solutions
        for cnum, ind in enumerate(solutions):
            comments = ['Solution %d'%cnum]
            comments.append('gene: %s'%ind.values())
            ind.score()
            scorer = self.docking.scoreObject
            RecLigEnergy = scorer.scoreBreakdown['RRL']
            InternalLigEnergy = scorer.scoreBreakdown.get('LL', 999999999)
            from AutoDockFR.ScoringFunction import FE_coeff_tors_42
            tor = scorer.TORSDOF * FE_coeff_tors_42
            ene = RecLigEnergy + tor
            comments.append('FINAL SOLUTION: %3d FEB: %9.3f R-L: %9.3f L: %9.3f Tor: %9.3f Score: %9.3f'%(
                cnum, ene, RecLigEnergy, InternalLigEnergy, tor, -ind._fitness_score))
            line = 'rmsds: '
            if len(self.rmsdCalculators):
                a, b, L_coords = ind.phenotype
                for rmsdc in self.rmsdCalculators:
                    rmsd = rmsdc.computeRMSD(L_coords)
                    line += " %6.2f"%rmsd
            comments.append(line)
            self.saveIndividualPDBQT(ind, "cluster%d_solution.pdbqt"%cnum, cnum, comments=comments)

    
    def step(self, mode='coarse search'):
        """
	None <- step(steps)

        Function takes the current population and does the GA step.
        Mutation, crossover, replacement, local search all done here.
        """

        t0 = time.time()
        # count similar individuals (with in clusterEcut of the top scored ind)
        ref = self.pop[0]
        remainder = [0]
        refScore = ref._fitness_score
        # Size of the population
        sz = len(self.pop)
        gen = self.gen
        
        if mode=='coarse search':
            if refScore > 0.0:
                for i, ind in enumerate(self.pop[1:]):
                    if refScore-ind._fitness_score > 2.0:#self.clusterEcut:
                        break
                    remainder.append(i+1)

            print '\n  CLUSTERING %d individual(s) Within %.2f Kcal of %f'%(
                len(remainder), 2.0, -refScore)#self.clusterEcut, -refScore)

            # If there are more than 10 individuals that are similar
            # reduce the clusteringEnergy by 0.5 (cluster less individuals)
            fromClusters = []
            if len(remainder)>10:
                #remainder = remainder[:10]
                self.clusterEcut = max(2.0, self.clusterEcut-0.5)
            elif len(remainder)==2:
                self.clusterEcut += 0.5

            toRemove = []
            if len(remainder)>2:
                nbRemoved = 0
                clusters = self.cluster(remainder)
                for c in clusters:
                    # find lowest score individual in cluster
                    mini = 99999999999.9
                    rep = None
                    scores = []
                    clustLen = len(c)
                    for ind in c:
                        scores.append(-self.pop[ind]._fitness_score)
                        if -self.pop[ind]._fitness_score < mini:
                            mini = -self.pop[ind]._fitness_score
                            rep = ind

                    best = self.pop[rep]

                    if len(self.rmsdCalculators):
                        a, b, L_coords = self.pop[rep].phenotype
                        for rmsdc in self.rmsdCalculators:
                            print "    rmsd: %6.2f"%rmsdc.computeRMSD(L_coords),

                    print " #inClust", len(c), "ClustMemb", c, 'best:', rep, -self.pop[rep]._fitness_score,\
                          numpy.mean(scores), numpy.std(scores)

                    # If cluster has more than one member, remove individuals from population
                    nbRemoved += len(c)-1
                    for index in c:
                        if index==rep: continue
                        toRemove.append(self.pop[index])

                ##
                ## The code below tried to add offsprings from members that will be removed from the cluster
                ##

                if __debug__:
                    #print "  %d clusters found and optimzed in %f (removed %d created %d (bestEM %f, bestEC%f))"%(len(clusters), time.time()-t0, nbRemoved, len(fromClusters), bestEmut, bestEcross)
                    print "  %d clusters found in %f (removed %d)"%(len(clusters), time.time()-t0, nbRemoved)
        
        bestEmut = -999999.
        bestEcross = -999999.

        if len(remainder)==sz and mode=='coarse search':
               return 'population clustered'
               
        b = timer()

        # Number of individuals to be replaced (settings file)
        # This concept does not exist in the AD4.2 GA implementation
        replace = int(self.settings['GA_replace'] * sz)
	    # Number of new members in inject into the population (settings file)
        # This concept does not exist in the AD4.2 GA implementation

        
        #import pdb;pdb.set_trace()
        self.pop.touch() # this will reset selector_ready

        nbCross = nbGood1 = nbGood2 = 0
        fromCrossOver = []
	    # The energy (cutE) will be the most unfavorable individual
	    # that is not automatically replaced by crossover or random_injection
        #MLDcutE = -self.pop[len(self.pop)-nbNew-replace/2-1]._fitness_score
        cutE = -self.pop[len(self.pop)-replace -1]._fitness_score
        e1 = time.time()

        # reduce number of steps minimizing mutations and cross overs
        # else time to create them increases and not better results
        #nbsteps = max(10, 50-6*self.gen)

        # Iterates by two (replace the mom & dad in a pair) 
        p_crossover = self.settings['GA_crossover']
        for i in range(0,replace,2):
            #mom,dad = self.pop[:sz].select(2)
            #ts = time.time()
            mom, dad = self.pop.select(2)
            #print 'select', i, time.time()-ts
            self.stats['selections'] = self.stats['selections'] + 2
            # Returns true or false.  Random number < p_crossover, then true
	        # Either do crossover
            if flip_coin(p_crossover):
                try: 
                    bro,sis = self.crossover((mom,dad))
                    bro.score()
                    sis.score()
                    self.stats['crossovers'] = self.stats['crossovers'] + 2
                    if self.enableLocalSearch:
                        bron = self.minimize(bro, **self.settings['GAminimize'])
                        nbSteps1 = self._totalStepInLastMinimize
                        sisn = self.minimize(sis, **self.settings['GAminimize'])
                        nbSteps2 = self._totalStepInLastMinimize
                        o1star = o2star = ''
                        if bron._fitness_score>refScore:
                            o1star = '*'
                            refScore = bron._fitness_score
                        elif sisn._fitness_score>refScore:
                            refScore = sisn._fitness_score
                            o2star = "*"
                        #sisn, nbSteps =  self.localSearch.search(sis, max_steps=300, MAX_SUCCESS=4, MAX_FAIL=6)
                        print '  CRO A: %3d %12.3f B: %3d %12.3f O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                            self.pop.selector._selected[0], -mom._fitness_score,
                            self.pop.selector._selected[1], -dad._fitness_score,
                            -bro._fitness_score, -bron._fitness_score, o1star, nbSteps1,
                            -sis._fitness_score, -sisn._fitness_score, o2star, nbSteps2)
                        #print '  CROSS  BRO %12.3f -> %12.3f (%4d) SIS %12.3f -> %12.3f (%4d)'%(
                        #    -bro._fitness_score, -bron._fitness_score, nbSteps1, -sis._fitness_score, -sisn._fitness_score, nbSteps2)
                        #print 'CRO SIS %f -> %f %d'%(-sis._fitness_score, -sisn._fitness_score, nbSteps)
                    else:
                        bron = bro
                        sisn = sis

                    fromCrossOver.append(bron)
                    fromCrossOver.append(sisn)
                    if self.settings['savePopulationHist']:
                        dadOrigin = dad.history.split()[0]
                        momOrigin = mom.history.split()[0]
                        bron.history = 'C(%d_%s|%s) %.2f '% (gen, momOrigin, dadOrigin, bro._fitness_score)
                        sisn.history = 'C(%d_%s|%s) %.2f '% (gen, momOrigin, dadOrigin, sis._fitness_score)
                    nbCross += 2
                    if -bron._fitness_score < cutE: nbGood1 +=1
                    if -sisn._fitness_score < cutE: nbGood1 +=1
                except ValueError: 
                    print "ERROR: crossover failed"
                    #- just act as if this iteration never happened
                    i = i - 2 
                    #print 'crossover failure - ignoring and continuing'
	        # Or do mutation
            else:
                #import pdb
                #pdb.set_trace()
                momc = mom.clone()
                self.stats['mutations'] = self.stats['mutations'] + momc.mutate()
                dadc = dad.clone()
                self.stats['mutations'] = self.stats['mutations'] + dadc.mutate()
                
                if self.enableLocalSearch:
                    #ndadc, nbSteps =  self.localSearch.search(dadc, max_steps=300, MAX_SUCCESS=4, MAX_FAIL=6)
                    ndadc = self.minimize(dadc, **self.settings['GAminimize'])
                    nbSteps1 = self._totalStepInLastMinimize
                    nmomc = self.minimize(momc, **self.settings['GAminimize'])
                    nbSteps2 = self._totalStepInLastMinimize
                    o1star = o2star = ''
                    if ndadc._fitness_score>refScore:
                        o1star = '*'
                        refScore = ndadc._fitness_score
                    elif nmomc._fitness_score>refScore:
                        refScore = nmomc._fitness_score
                        o2star = "*"
                    print '  MUT A: %3d %12.3f B: %3d %12.3f O1: %12.3f -> %12.3f%1s (%4d) O2: %12.3f -> %12.3f%1s (%4d)'%(
                        self.pop.selector._selected[0], -mom._fitness_score,
                        self.pop.selector._selected[1], -dad._fitness_score,
                        -momc._fitness_score, -nmomc._fitness_score, o2star, nbSteps2,
                        -dadc._fitness_score, -ndadc._fitness_score, o1star, nbSteps1)
                    dadc = ndadc
                    momc = nmomc
                else:
                    momc.evaluate(force=1)
                    dadc.evaluate(force=1)
                    print '  MUTATE BRO %12.3f -> %12.3f (%4d) SIS %12.3f -> %12.3f (%4d)'%(
                        -dad._fitness_score, -dadc._fitness_score, nbSteps1, -mom._fitness_score, -momc._fitness_score, nbSteps2)
                
                if -momc._fitness_score < cutE: nbGood2 +=1
                if -dadc._fitness_score < cutE: nbGood2 +=1
                fromCrossOver.append(momc)
                fromCrossOver.append(dadc)
                if self.settings['savePopulationHist']:
                    momc.history += 'M(%d) %.2f '%(gen, momc._fitness_score)
                    dadc.history += 'M(%d) %.2f '%(gen, dadc._fitness_score)

        if __debug__:
            print '  CROSSOVER/MUT created %d individuals (cross=%d good, mut=%d good) in %f'%(
                len(fromCrossOver), nbGood1, nbGood2, time.time()-e1)

        # remove the clustered individuals now else indiced in cluster would change
        if len(remainder)>2 and len(remainder)<100:
            for ind in toRemove:
                self.pop.remove(ind)

        #print "Population sz after cross & removal %s.  Should be %s " % (len(self.pop), sz)

        self.pop.extend(fromCrossOver)
        self.pop.sort()
        self.pop = self.pop[:sz]

        # Local Search step
        if self.enableLocalSearch:
            p_localsearch = self.settings['GA_localsearchfreq']
            # Returns true or false.  Random number < p_crossover, then true
            if self.localSearchFlipCoin.flip_coin(p_localsearch):
                print "  Local Search on all members of the population"
                tls = time.time()
                oldScores = []
                lsc = 0
                mini = self.pop[0]._fitness_score
                bestInd = 0
                for i, ind in enumerate(self.pop[1:]):
                    oldScores.append(ind._fitness_score)
                    neighbor = self.minimize(ind, nbSteps=10, noImproveStop=2, max_steps=1000,
                                             MAX_FAIL=15, MIN_VAR=0.01)
                    if self.settings['savePopulationHist']:
                        neighbor.history = ind.history + 'LS(%d) %.2f '%(gen, neighbor._fitness_score)
                    if neighbor._fitness_score > mini:
                        mini = neighbor._fitness_score
                        bestInd = i
                    self.pop[i] = neighbor
                    lsc += 1
                print "  local search minimized %d individuals in %f"%(lsc, time.time()-tls)
                print "    best individual %d %12.3f -> %12.3f"%(bestInd, -oldScores[bestInd], -mini)

        self.pop.touch()
        self.pop.scale()
        self.pop.sort()

        # Update the population stats
        self.pop.update_stats()
        self.stats['pop_evals'] = self.stats['pop_evals'] + 1
        #chk for saving
        #fileName = "%s_%s_%d"%(self.settings['Receptor'].rsplit('.')[0],self.settings['Ligand'].rsplit('.')[0],self.settings['constraintMaxTry'])
        #self.checkSavePopulation(fileName)
        e = timer(); self.step_time = e - b

        if __debug__:
            # print out rmsd to all reference structures for all individuals within 2 kcal/mol
			# of the lowest energy
            # used for statictics
            gene = self.pop[0]
            Eref = gene._fitness_score
            i = 0
            print "  LowE_RMSDs gen:%d" % self.gen,
            while gene._fitness_score > Eref-2.0 and i < len(self.pop)-1:
                print " | %d:"%i,
                adum, bdum, L_coords = gene.phenotype
                for RMSDcalc in self.rmsdCalculators:
                    rmsd = RMSDcalc.computeRMSD(L_coords)
                    print " %5.2f"%rmsd,
                i += 1
                gene = self.pop[i]
            print

        # Update the top-level dictionary
        self.stats.update(self.pop.stats)	
        self.db_entry['best_scores'].append(self.stats['current']['max'])
        return 'searching'


    
## end of GA class
#from AutoDockFR.PSO import ranf, granf ## bad.. fixme.

## from math import sqrt, log

## def granf(sigma):
##     stop = False
##     #/* choose x,y in uniform square (-1,-1) to (+1,+1) */
##     while not stop:
##         r1 = random() #Random number in [0., 1.[
##         r2 = random() #Random number in [0., 1.[
##         x = -1 + 2 * r1 # map x into [-1, 1[
##         y = -1 + 2 * r2 # map y into [-1, 1[

##         #/* see if it is in the unit circle */
##         r2 = x * x + y * y;
        
##         if (r2 < 1.0 and r2 != 0):
##             stop=True

##     #/* Box-Muller transform */
##     return (sigma * y * sqrt (-2.0 * log (r2) / r2));


## class SolisWet_ORIG:
##     """ local searching
##     mutate an individual from a population. see if the score can be improved.
##     """
##     def __init__(self, GA_LocalSearchRate, GA_LocalSearchMaxFail, GA_LocalSearchMaxSucess,\
##                  GA_LocalSearchMinVar, GA_LocalSearchFactorContraction,\
##                  GA_LocalSearchFactorExpansion, GA_LocalSearchMaxIts):

## 	self.GA_LocalSearchRate = GA_LocalSearchRate
##         self.GA_LocalSearchMaxFail = GA_LocalSearchMaxFail
##         self.GA_LocalSearchMaxSuccess = GA_LocalSearchMaxSucess
##         self.GA_LocalSearchMinVar = GA_LocalSearchMinVar
##         self.GA_LocalSearchFactorContraction = GA_LocalSearchFactorContraction
##         self.GA_LocalSearchFactorExpansion = GA_LocalSearchFactorExpansion
##         self.GA_LocalSearchMaxIts = GA_LocalSearchMaxIts

##         """
## 	self.settings = settings
##         if 'GA_localsearchrate' in self.settings:
##             self.GA_LocalSearchRate = self.settings['GA_localsearchrate']
##         else:
##             self.GA_LocalSearchRate = 0.3

##         self.GA_LocalSearchMaxFail = self.settings['GA_LocalSearchMaxFail']
##         self.GA_LocalSearchMaxSuccess = self.settings['GA_LocalSearchMaxSuccess']
##         self.GA_LocalSearchMinVar = self.settings['GA_LocalSearchMinVar']
##         self.GA_LocalSearchFactorContraction = self.settings['GA_LocalSearchFactorContraction']
##         self.GA_LocalSearchFactorExpansion = self.settings['GA_LocalSearchFactorExpansion']
##         self.GA_LocalSearchMaxIts = self.settings['GA_LocalSearchMaxIts']
##         """
        
##     def search(self, individual):
##         x = individual.clone()
##         bestResult = individual.clone()
##         dim = len(x)
##         s = individual._score
##         i = 0
##         success = 0 
##         fail = 0 
##         steps = 0 
##         t_score =0
##         t = []
##         d = []
##         bias = []
##         var = dim*[self.GA_LocalSearchMinVar]
##         max_steps = self.GA_LocalSearchMaxIts
##         terminate = False 
## 	MAX_SUCCESS = self.GA_LocalSearchMaxSuccess
## 	MAX_FAIL   = self.GA_LocalSearchMaxFail
## 	FACTOR_EXPANSION =   self.GA_LocalSearchFactorExpansion
## 	FACTOR_CONTRACTION = self.GA_LocalSearchFactorContraction
## 	MIN_VAR = self.GA_LocalSearchMinVar

##         # Initialize the bias to 0.0
##         for i in range(dim):
##             bias.append(0.0)

##         #  generate new position
##         while (steps < max_steps and not terminate):
##             d = x.clone()
##             # Replace the values of the current population member
##             for i in range(dim):
##                 r = ranf()
##                 if (r < self.GA_LocalSearchRate):
##                     d[i].set_value( granf(var[i]) + bias[i]  )
##                 else:
##                     d[i].set_value( 0.0 )

##             #  try t = x + d.  t = orginal + small change
##             t = x.clone()
##             # check that vals in t[] are not > the max or min of current val
##             for i in range(dim):
##                 tmp = x[i] + d[i]
##                 mini, maxi=individual[i].bounds
##                 if tmp > maxi:
##                     tmp = maxi
##                 elif tmp < mini:
##                     tmp = mini
##                 t[i].set_value(tmp)

##             #t_score = fitness(t, dim)
##             #print t[:2],
##             #print individual[:2]
##             #print individual.evaluated
##             #print
##             #t_score=Genome.evaluate(t,force=1)
##             # Evaluate the score of the new individual
##             t_score = t.evaluate(force=1)
##             #print s, "after:",t_score
##             # More favorable (negative) score
##             if(-t_score < -s):
##                 #print " +   t_score=%f, old score=%f"%(t_score, s)
##                 x = t[:]
##                 individual.x= t[:]
##                 s = t_score 
##                 # Update the bias list based on the new population member, keep moving in this direction
##                 for i in range(dim):
##                     bias[i] = 0.4 * d[i] + 0.2 * bias[i] 
##                 success += 1 
##                 fail = 0 
##             # score not more favorable (more negative)
##             else:        
##                 #  try t = x - d, move in the opposite direction
##                 t = x.clone()
##                 for i in range(dim):
##                     tmp = x[i] - d[i]
##                     mini, maxi=individual[i].bounds
##                     if tmp > maxi:
##                         tmp = maxi
##                     elif tmp < mini:
##                         tmp = mini
##                     t[i].set_value(tmp)

##                 #t_score = fitness(t, dim)
##                 #t_score=individual.evaluate(t)
##                 t_score = t.evaluate(force=1)
##                 # Score is more favorable
##                 if(-t_score < -s):
##                     #print " -   t_score=%f, old score=%f"%(t_score, s)
##                     x = t.clone()
##                     #individual.x= t[:]
##                     s = t_score 
##                     for i in range(dim):
##                         bias[i] = bias[i] - 0.4 * d[i] 
##                     success += 1 
##                     fail = 0 
##                 else: #  Score still isn't favorable = fail
##                     for i in range(dim):
##                         bias[i] *= 0.5 
##                     fail +=1 
##                     success = 0 

##             # If you have made a X steps in a row that are favorable, take a bigger step
##             if(success >= MAX_SUCCESS):        
##                 for i in range(dim):
##                     var[i] *= FACTOR_EXPANSION 
##                 success = 0 
##             # If you have made a X steps in a row that are unfavorable, take a smaller step
##             elif(fail >= MAX_FAIL):
##                 for i in range(dim):            
##                     var[i] *= FACTOR_CONTRACTION 
##                     if(var[i] < MIN_VAR):                
##                         terminate = True 
##                         break 


##             steps+=1 
##         # end of while (steps < max_steps and not terminate)
##         #individual._score= s
##         return x


class SolisWet:
    """ local searching
    mutate an individual from a population. see if the score can be improved.
    """
    def __init__(self, search_rate=0.3, max_steps=500, mode=all,
                 MAX_FAIL=4, MAX_SUCCESS=4, MIN_VAR=0.01,
                 FACTOR_EXPANSION=2.0, FACTOR_CONTRACTION=0.5, absMinVar=None):
        """
        SolisWets <- SolisWet( ...)

        ... 
        """
        self.max_steps = max_steps
	self.search_rate = search_rate  # probability for a gene to be perturbed
        self.MAX_FAIL = MAX_FAIL       # maximum number of ...
        self.MAX_SUCCESS = MAX_SUCCESS
        self.MIN_VAR = MIN_VAR
        self.FACTOR_EXPANSION = FACTOR_EXPANSION
        self.FACTOR_CONTRACTION = FACTOR_CONTRACTION
        self.mode = mode
        self.absMinVar = absMinVar    # find out what it is used for
        
        self.configure( search_rate=search_rate, max_steps=max_steps, mode=mode,
                 MAX_FAIL=MAX_FAIL, MAX_SUCCESS=MAX_SUCCESS, MIN_VAR=MIN_VAR,
                 FACTOR_EXPANSION=FACTOR_EXPANSION, FACTOR_CONTRACTION=FACTOR_CONTRACTION)


    def configure(self, search_rate=None, max_steps=None, mode=None,
                 MAX_FAIL=None, MAX_SUCCESS=None, MIN_VAR=None,
                 FACTOR_EXPANSION=None, FACTOR_CONTRACTION=None, absMinVar=None):
        # set default values for LS parameters

        if max_steps:
            self.max_steps = max_steps
            
        if search_rate:
            assert isinstance(search_rate, float)
            assert search_rate>0.0
            assert search_rate<=1.0
            self.search_rate = search_rate

        if MAX_FAIL:
            self.MAX_FAIL = MAX_FAIL       # maximum number of ...

        if MAX_SUCCESS:    
            self.MAX_SUCCESS = MAX_SUCCESS

        if MIN_VAR:
            self.MIN_VAR = MIN_VAR

        if FACTOR_EXPANSION:
            self.FACTOR_EXPANSION = FACTOR_EXPANSION

        if FACTOR_CONTRACTION:
            self.FACTOR_CONTRACTION = FACTOR_CONTRACTION

        if mode:
            self.mode = mode

        if absMinVar:
            self.absMinVar = absMinVar    # find out what it is used for


    def search(self, individual, **kw):
        """
        documnent !
        """
        
        max_steps = kw.get('max_steps', self.max_steps)
	search_rate = kw.get('search_rate', self.search_rate )
        MAX_FAIL = kw.get('MAX_FAIL', self.MAX_FAIL )
        MAX_SUCCESS = kw.get('MAX_SUCCESS', self.MAX_SUCCESS )
        MIN_VAR = kw.get('MIN_VAR', self.MIN_VAR )
        FACTOR_EXPANSION = kw.get('FACTOR_EXPANSION', self.FACTOR_EXPANSION )
        FACTOR_CONTRACTION = kw.get('FACTOR_CONTRACTION', self.FACTOR_CONTRACTION )
        mode = kw.get('mode', self.mode )
        absMinVar = kw.get('absMinVar', self.absMinVar )
        
        individual.nbLS += 1
        x = individual.clone()
        nbGenes = len(x)
        success = 0 
        fail = 0 
        steps = 0 
        terminate = False 
        if mode=='conformation':
            begin = 7
            end = nbGenes
            scorekw = {'L_L':True, 'RR_L':False}
            #scorer = individual.scorer
            #old = scorer.configure(RR_L=False, FR_L=False, L_L=True, 
            #                       RR_RR=False, RR_FR=False, FR_FR=False)
        elif mode=='pose':
            begin = 0
            end = 7
            scorekw = {'L_L':False, 'RR_L':True}
            #scorer = individual.scorer
            #old = scorer.configure(RR_L=True, FR_L=False, L_L=False, 
            #                       RR_RR=False, RR_FR=False, FR_FR=False)
        elif mode=='trans':
            begin = 0
            end = 3
            scorekw = {'L_L':True, 'RR_L':True}

        else:
            begin = 0
            end = nbGenes
            scorekw = {}

        
        s = individual.score(**scorekw)

        # make step absolute displacement
        if absMinVar:
            # absMinVar is a number between 0. and -1. which when scaled
            # to the range of real values for this gene provides the deviation
            # of the Gaussian used to compute the displacement
            var = absMinVar[:]
        else:
            # vector of deviation
            var = nbGenes*[MIN_VAR]
        #print var
        # Initialize the bias to 0.0
        bias = [0.0]*nbGenes

        #  generate new position
        while (steps < max_steps and not terminate):

            # create a vector of displacements d making sure
            # at least one gene will be modified
            d = [0]*nbGenes
            ct  = 0 # count how many genes will be modified

            # MS Oct 2012: for bad individuals search rate has to be low to improve score
            #              i.e. 0.1 for score > 1000.
            #  for anneal when solution are good search_rate
            #while ct == 0:
            #    for i in range(begin,end):
            #        if search_rate==1.0 or random() < search_rate:
            #            d[i] =  gauss(0., var[i]) + bias[i]
            #            ct += 1

            while ct == 0:
                delta = []
                offset = 0
                for motion in x.motionObjs:
                    nbg = motion.nbGenes
                    ct1, devs = motion.jitter(
                        x[offset:offset+nbg],
                        search_rate, var[offset:offset+nbg])
                    delta.extend(devs)
                    ct += ct1
                    offset += nbg

                for i in range(begin,end):
                    d[i] =  delta[i] + bias[i]
                
            #print 'deviation', d
            #  try t = x + d.  t = orginal + small change
            t = x.clone()
            # check that vals in t[] are not > the max or min of current val
            # and handle cyclic genes
            for i in range(begin,end):
                tmp = x[i] + d[i]
                mini, maxi = individual[i].bounds
                length = maxi-mini
                if tmp > maxi:
                    if x[i].cyclic: tmp = mini + (tmp - maxi)%length
                    else: tmp = maxi
                elif tmp < mini:
                    if x[i].cyclic: tmp = maxi - (mini - tmp)%length
                    else: tmp = mini
                if __debug__:
                    if tmp < mini or tmp > maxi:
                        raise ValueError("gene value outside bounds %f (%f, %f)"%(tmp, mini, maxi))
                t[i]._value = tmp

            # Evaluate the score of the new individual
            t_score = t.score(**scorekw)

            if t_score > s: # More favorable
                x = t[:]
                s = t_score 
                # Update the bias list based on the new population member,
                # keep moving in this direction
                for i in range(begin,end): bias[i] = 0.4 * d[i] + 0.2 * bias[i] 
                success += 1 
                fail = 0 
                #print ' success 1', steps, success, fail

            else: # Unfavorable 
                #  try t = x - d, move in the opposite direction
                t = x.clone()
                for i in range(begin,end):
                    tmp = x[i] - d[i]
                    mini, maxi = individual[i].bounds
                    length = maxi-mini
                    if tmp > maxi:
                        if x[i].cyclic: tmp = mini + (tmp - maxi)%length
                        else: tmp = maxi
                    elif tmp < mini:
                        if x[i].cyclic: tmp = maxi - (mini - tmp)%length
                        else: tmp = mini
                    if __debug__:
                        if tmp < mini or tmp > maxi:
                            raise ValueError("gene value outside bounds %f (%f, %f)"%(tmp, mini, maxi))
                    t[i]._value = tmp

                t_score = t.score(**scorekw)
                
                if t_score > s: # More favorable
                    x = t[:]
                    s = t_score 
                    for i in range(begin,end): bias[i] = bias[i] - 0.4 * d[i] 
                    success += 1
                    fail = 0
                    #print '  success 2', steps, success, fail

                else: #  Score still isn't favorable = fail
                    for i in range(begin,end): bias[i] *= 0.5 
                    fail += 1
                    success = 0 
                    #print '  fail', steps, success, fail

            # If you have made a X steps in a row that are favorable,
            #take a bigger step
            if(success >= MAX_SUCCESS):        
                for i in range(begin,end): var[i] *= FACTOR_EXPANSION 
                success = 0 

            # If you have made a X steps in a row that are unfavorable,
            #take a smaller step
            elif(fail >= MAX_FAIL):
                for i in range(begin,end):
                    var[i] *= FACTOR_CONTRACTION 
                    if(var[i] < MIN_VAR):
                        terminate = True 
                        break 

            steps+=1 
        # end of while (steps < max_steps and not terminate)
        #individual._score= s
        #print 'AAA', steps, -individual._score, -x._score
        x._score= s
        return x, steps

            
    ## def search(self, individual, max_steps=None,search_rate=None,
    ##               MAX_SUCCESS=None, MAX_FAIL=None,
    ##               FACTOR_EXPANSION=None, FACTOR_CONTRACTION=None,
    ##               MIN_VAR=None, absMinVar=False, mode='all'):
    ##     """
    ##     max_steps: how many attemps to minimize
    ##     MAX_SUCCESS: if the energy goes down this many times increase step size
    ##                  by multiplying by FACTOR_EXPANSION
    ##     MAX_FAIL: if the energy goes up that many times decresae step size
    ##                  by multiplying by FACTOR_CONTRACTION
    ##     """
    ##     individual.nbLS += 1
    ##     x = individual.clone()
    ##     nbGenes = len(x)
    ##     success = 0 
    ##     fail = 0 
    ##     steps = 0 
    ##     terminate = False 

    ##     # FIXME we shoudl have a searchConf method to avoid testing this here
    ##     if mode=='conformation':
    ##         begin = 7
    ##         end = nbGenes
    ##         scorekw = {'L_L':True, 'RR_L':False}
    ##         #scorer = individual.scorer
    ##         #old = scorer.configure(RR_L=False, FR_L=False, L_L=True, 
    ##         #                       RR_RR=False, RR_FR=False, FR_FR=False)
    ##     elif mode=='pose':
    ##         begin = 0
    ##         end = 7
    ##         scorekw = {'L_L':False, 'RR_L':True}
    ##         #scorer = individual.scorer
    ##         #old = scorer.configure(RR_L=True, FR_L=False, L_L=False, 
    ##         #                       RR_RR=False, RR_FR=False, FR_FR=False)
    ##     else:
    ##         begin = 0
    ##         end = nbGenes
    ##         scorekw = {}
            
    ##     s = individual._score

    ##     # FIXME we should not always test this here
    ##     if max_steps is None: max_steps = self.GA_localSearchMaxIts
    ##     if MAX_SUCCESS is None: MAX_SUCCESS = self.GA_localSearchMaxSuccess
    ##     if MAX_FAIL is None: MAX_FAIL = self.GA_localSearchMaxFail
    ##     if FACTOR_EXPANSION is None: FACTOR_EXPANSION = self.GA_localSearchFactorExpansion
    ##     if FACTOR_CONTRACTION is None: FACTOR_CONTRACTION = self.GA_localSearchFactorContraction
    ##     if MIN_VAR is None: MIN_VAR = self.GA_localSearchMinVar
    ##     if search_rate is None: search_rate = self.GA_localSearchRate

    ##     # make step absolute displacement
    ##     if absMinVar:
    ##         # absMinVar os a number between 0. and -1. which when scaled
    ##         # to the range of real values for this gene provides the deviation
    ##         # of the Gaussian used to compute the displacement
    ##         var = absMinVar[:]
    ##     else:
    ##         # vector of deviation
    ##         var = nbGenes*[MIN_VAR]
    ##     #print var
    ##     # Initialize the bias to 0.0
    ##     bias = [0.0]*nbGenes

    ##     #  generate new position
    ##     while (steps < max_steps and not terminate):

    ##         # create a vector of displacements d making sure
    ##         # at least one gene will be modified
    ##         d = [0]*nbGenes
    ##         ct  = 0 # count how many genes will be modified

    ##         # MS Oct 2012: for bad individuals search rate has to be low to improve score
    ##         #              i.e. 0.1 for score > 1000.
    ##         #  for anneal when solution are good search_rate

    ##         # compute a deviation until at least one gene will change
    ##         # for very small values of search_rate d[i] could be 0.0 for all i
    ##         while (ct==0):
    ##             for i in range(begin,end):
    ##                 if search_rate==1.0 or random() < search_rate:
    ##                     d[i] =  gauss(0., var[i]) + bias[i]
    ##                     ct += 1

    ##         #print 'deviation', d
    ##         #  try t = x + d.  t = orginal + small change
    ##         t = x.clone()
    ##         # check that vals in t[] are not > the max or min of current val
    ##         # and handle cyclic genes
    ##         for i in range(begin,end):
    ##             tmp = x[i] + d[i]
    ##             mini, maxi = individual[i].bounds
    ##             length = maxi-mini
    ##             if tmp > maxi:
    ##                 if x[i].cyclic: tmp = mini + (tmp - maxi)%length
    ##                 else: tmp = maxi
    ##             elif tmp < mini:
    ##                 if x[i].cyclic: tmp = maxi - (mini - tmp)%length
    ##                 else: tmp = mini
    ##             if __debug__:
    ##                 if tmp < mini or tmp > maxi:
    ##                     raise ValueError("gene value outside bounds %f (%f, %f)"%(tmp, mini, maxi))
    ##             t[i]._value = tmp

    ##         # Evaluate the score of the new individual
    ##         t_score = t.score(t, **scorekw)

    ##         if t_score > s: # More favorable
    ##             x = t[:]
    ##             s = t_score 
    ##             # Update the bias list based on the new population member,
    ##             # keep moving in this direction
    ##             for i in range(begin,end): bias[i] = 0.4 * d[i] + 0.2 * bias[i] 
    ##             success += 1 
    ##             fail = 0 
    ##             #print ' success 1', steps, success, fail

    ##         else: # Unfavorable 
    ##             #  try t = x - d, move in the opposite direction
    ##             t = x.clone()
    ##             for i in range(begin,end):
    ##                 tmp = x[i] - d[i]
    ##                 mini, maxi = individual[i].bounds
    ##                 length = maxi-mini
    ##                 if tmp > maxi:
    ##                     if x[i].cyclic: tmp = mini + (tmp - maxi)%length
    ##                     else: tmp = maxi
    ##                 elif tmp < mini:
    ##                     if x[i].cyclic: tmp = maxi - (mini - tmp)%length
    ##                     else: tmp = mini
    ##                 if __debug__:
    ##                     if tmp < mini or tmp > maxi:
    ##                         raise ValueError("gene value outside bounds %f (%f, %f)"%(tmp, mini, maxi))
    ##                 t[i]._value = tmp

    ##             t_score = t.score(t, **scorekw)
                
    ##             if t_score > s: # More favorable
    ##                 x = t[:]
    ##                 s = t_score 
    ##                 for i in range(begin,end): bias[i] = bias[i] - 0.4 * d[i] 
    ##                 success += 1
    ##                 fail = 0
    ##                 #print '  success 2', steps, success, fail

    ##             else: #  Score still isn't favorable = fail
    ##                 for i in range(begin,end): bias[i] *= 0.5 
    ##                 fail += 1
    ##                 success = 0 
    ##                 #print '  fail', steps, success, fail

    ##         # If you have made a X steps in a row that are favorable,
    ##         #take a bigger step
    ##         if(success >= MAX_SUCCESS):        
    ##             for i in range(begin,end): var[i] *= FACTOR_EXPANSION 
    ##             success = 0 

    ##         # If you have made a X steps in a row that are unfavorable,
    ##         #take a smaller step
    ##         elif(fail >= MAX_FAIL):
    ##             for i in range(begin,end):
    ##                 var[i] *= FACTOR_CONTRACTION 
    ##                 if(var[i] < MIN_VAR):
    ##                     terminate = True 
    ##                     break 

    ##         steps+=1 
    ##     # end of while (steps < max_steps and not terminate)
    ##     #individual._score= s
    ##     #print 'AAA', steps, -individual._score, -x._score
    ##     #print 'MINI', ['%.2f '%v for v in x.values()], float(ctSum)/steps
    ##     x._score= s
    ##     return x, steps
