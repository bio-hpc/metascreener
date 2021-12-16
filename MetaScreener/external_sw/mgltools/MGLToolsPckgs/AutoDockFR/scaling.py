#############################################################################
#
# Author: Michel F. SANNER
#
# Copyright: M. Sanner TSRI 2009
#
# adapted from scipy.ga
#
#############################################################################

from ga_util import my_std, my_mean, GAError
from numpy import less_equal, choose

# if a score is less the 2 standard deviations below, the average, its score
# is arbitrarily set to zero
class sigma_truncation_scaling:

    def __init__(self,scaling = 2):
	self.scaling = scaling

    def scale(self, pop):
	sc = pop.scores()
	avg = my_mean(sc)
	if len(sc) > 1:
	    dev = my_std(sc)
	else: dev = 0
	#print 'SCALING mean %f std %f'%(avg, dev) 
	f = sc - avg + self.scaling * dev
	# document of choose function
	# http://numeric.scipy.org/numpydoc/numpy-9.html#pgfId-36498
	f=choose(less_equal(f,0.),(f,0.))
	# set the fitness
	#print 'FITNESSES',
	for i in range(len(pop)):
	    pop[i].fitness(f[i])
	    #print '%.3f'%f[i],
	#print
	#print 'fitness for best score', f
	return pop	


class no_scaling:

    def scale(self,pop): 
	for ind in pop:
            ind.fitness(ind._fitness_score)
	return pop	


class linear_scaling:

    def __init__(self,mult = 1.2):
	self.mult = mult

    def scale(self,pop):
	sc = pop.scores()
	pmin = min(sc)
	if pmin < 0: raise GAError, 'linear scaling does not work with objective scores < 0'
	pmax = max(sc)
	pavg = my_mean(sc)
	if(pavg == pmax): 
	    a = 1.
	    b = 0.
	elif pmin > (self.mult * pavg - pmax)/(self.mult - 1.):
	    delta = pmax - pavg
	    a = (self.mult - 1.) * pavg / delta
	    b = pavg * (pmax - self.mult * pavg) / delta
	else:
	    delta = pavg - pmin
	    a = pavg / delta
	    b = -pmin * pavg / delta
	f = sc * a + b
	f=choose(less_equal(f,0.),(f,0.))
	for i in range(len(pop)):
            pop[i].fitness(f[i])
