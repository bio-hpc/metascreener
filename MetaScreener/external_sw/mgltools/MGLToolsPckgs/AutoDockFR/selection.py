#genetic algorithm selection routines
#based on galib. 
#exception - these classes only work on the scaled fitness

#from ga_util import *
from ga_util import choice

import pdb
from numpy.oldnumeric import *

from random import random
rand=random
from math import floor

class selector:
    def update(self,pop):
	pass
    def select(self,pop):
	raise GAError, 'selector.select() must be overridden'
    def clear(self):
		pass

class uniform_selector(selector):
    def select(self,pop,cnt = 1):
	if cnt == 1:
	    return choice(pop)
	res = []
	for i in range(cnt):
	    res.append(choice(pop))
	return res

class rank_selector(selector):
    def select(self,pop,cnt = 1):
	pop.sort()
	studliest = pop[0].fitness()
	tied_for_first = filter(lambda x,y=studliest: x.fitness()==y,pop)
	if cnt == 1:
	    return choice(tied_for_first)
	res = []
	for i in range(cnt):
	    res.append(choice(tied_for_first))
	return res

#scores must all be positive		
class roulette_selector(selector):
    def update(self,pop):
	self.pop = pop[:]
	sz = len(pop)
	if not sz:
	    raise GAError, 'srs_selector - the pop size is 0!'
	f =self.pop.fitnesses()
	f_max = max(f); f_min = min(f)
	if not ( (f_max >= 0 and f_min >= 0) or \
		 (f_max <= 0 and f_min <= 0)):
	    raise GAError, 'srs_selector requires all fitnesses values to be either strictly positive or strictly negative'
	if f_max == f_min: f = ones(shape(f),typecode = Float32)
	self.dart_board = add.accumulate(f / sum(f))
	
    def select(self,pop,cnt = 1):
	returns = []
	for i in range(cnt):
	    dart = rand()
	    idx = 0
	    while dart > self.dart_board[idx]:
		idx += 1
	    returns.append(self.pop[idx])
	if cnt == 1:
	    return returns[0]
	else:
	    return returns
	
    def clear(self): 
	del self.pop

from bisect import bisect

#scores must all be positive		
class srs_selector(selector):


    def update(self,pop):
        # build self.choices, a list of indices in the population used to select for cross and mutations
	sz = len(pop)
	if not sz:
	    raise GAError, 'srs_selector - the pop size is 0!'
        
	f = pop.fitnesses()
	f_max = max(f); f_min = min(f)
	if not ( (f_max >= 0. and f_min >= 0.) or 
		 (f_max <= 0. and f_min <= 0.)):
	    raise GAError, 'srs_selector requires all fitnesses values to be either strictly positive or strictly negative - min %f, max %f' %(f_min,f_max)

	f_avg = sum(f)/sz
	if abs(f_avg) < 1.e-10:
	    e = ones(shape(f),typecode = Float32)
	else:
	    if pop.min_or_max() == 'max': e = f/f_avg
	    else: e = (-f+f_max+f_min)/f_avg
	self.expected_value = e
	garauntee, chance = divmod(e,1.)
	choices = []
        choiceDict = {}
	for i in xrange(sz):
	    choices = choices + [i] * int(garauntee[i])
            if choiceDict.has_key(i):
                choiceDict[i] += int(garauntee[i])
            else:
                choiceDict[i] = int(garauntee[i])
                
	# now deal with the remainder
        # create a cumulative probability distribution (dart_board)
        # Then generate a random number between 0 and 1 and do a binary search
	sum_tmp = sum(chance)
	if sum_tmp !=0.0: 
	    for i in range(len(choices),sz):
                cdf = add.accumulate(chance / sum_tmp)
                idx = bisect(cdf,rand())
	    ## dart_board = add.accumulate(chance / sum_tmp)
	    ## for i in range(len(choices),sz):
	    ## 	dart = rand()
	    ## 	idx = 0
	    ##     while dart > dart_board[idx]: idx = idx + 1
	    ##     choices.append(idx)
                if choiceDict.has_key(idx):
                    choiceDict[idx] += 1
                else:
                    choiceDict[idx] = 1
                
        #if len(choiceDict) < 4:
        #    import pdb
        #    pdb.set_trace()
	self.choices = choices
        #print '  MAX CHOICE', choiceDict


    def select(self, pop, cnt=1):
        """
        Pick cnt individuals out of pop by randomly picking indices in self.choice
        """
        ## MS new implementation
        self._selected = []
        res = []
        lenChoices = len(self.choices)
        for i in range(cnt):
            ind = self.choices[int(floor(random()*lenChoices))]
            # once selected it is removed from the list
            #ind = self.choices.pop([int(floor(random()*lenChoices))])
            self._selected.append(ind)
            res.append(pop[ind])
        if cnt == 1:return res[0]
        else: return res
       
        ## res = []
        ## inds = []
        ## for i in range(cnt):
        ##     ind = choice(self.choices)
        ##     inds.append(ind)
        ##     res.append(pop[ind])

        ## #print "SELECTED", inds
        ## if cnt == 1:
        ##     return res[0]
        ## else:
        ##     return res


    def clear(self): 
        if hasattr(self,'choices'):
            del self.choices		
