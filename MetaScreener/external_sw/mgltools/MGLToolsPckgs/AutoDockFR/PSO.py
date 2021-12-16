import random, sys, types
from math import sqrt, log

neval=0
debug=0

#  Rewrite the fitness function as your wish
def fitness(x,  dim):
    s = 0 
    t1=0
    t2=0
    for i in range(dim-1):
        tmp=x[i]
        t1 = x[i+1] - tmp*tmp
        t2 = tmp-1.0 
        s = s + 100 * t1*t1 + t2*t2 
        
    global neval
    neval +=1
    #print 'evals =',neval
    return s 


def ranf():
    return random.random()

def granf(sigma):
    stop=False
    #/* choose x,y in uniform square (-1,-1) to (+1,+1) */
    while not stop:
        x = -1 + 2 * ranf();
        y = -1 + 2 * ranf();

        #/* see if it is in the unit circle */
        r2 = x * x + y * y;
        
        if (r2 < 1.0 and r2 != 0):
            stop=True

    #/* Box-Muller transform */
    return (sigma * y * sqrt (-2.0 * log (r2) / r2));

    



class Particle:

    def __init__( self,d, _xmax, _xmin, _vmax, evalFunc, genome):        
        self.dim=d
        self.xmax=_xmax
        self.xmin=_xmin
        self.vmax=_vmax

        #self.x = genome.clone() 

        self.x = []  ## position
        self.v = []  ## velocity
        self.score =9999   #  fitness (score) of current position
        
        self.p = []  ## keep a copy of my best position explored
        self.p_score=9999  #  my personal best score

        self.evalFunc=evalFunc
        assert evalFunc is not None
        self.genome=genome
        assert genome is not None
        return
    

    def evaluate(self, actual=None):
        #self.score = fitness(self.x, self.dim)
        if actual:
            return -self.evalFunc.score(self.genome, actual=actual)
        else:
            self.score = -self.evalFunc.score(self.genome, actual=self.x)
            if debug:
                for i in self.x:
                    print "%8.4f , "%i,
                print " score=%10.7f"%self.score
            return self.score
        # end of evlaluate

    def initialize(self) :
        self.x = []
        self.v = []
        for i in range(self.dim):
            # randomize position between (xmin, xmax)
            self.x.append((self.xmax[i]-self.xmin[i])*ranf() + self.xmin[i] )
            # randomize velocity between ( -vmax, +vmax)
            self.v.append(self.vmax[i] * (ranf()*2.0 - 1.0) )
        return

class Swarm:

    def __init__(self, dim, xmax, xmin, vmax, size, \
                 evalFunc=None, genome=None ):
        self.popsize=size
        self.pop = []
        for i in range(self.popsize):
            particle = Particle(dim, xmax, xmin, vmax, evalFunc, genome) 
            self.pop.append(particle)
        return


    def best(self):
        return self.pop[self.bestIndex()] 
    
    def bestp(self):
        return self.pop[self.bestpIndex()]  


    def bestIndex(self):
        b = 0 
        for i in range(self.popsize):
            if(self.pop[i].score < self.pop[b].score):
                b = i 
        return b 


    def bestpIndex(self):
        b = 0 
        for i in range(self.popsize):
            if(self.pop[i].p_score < self.pop[b].p_score):
                b = i 
        return b 



def SolisWet(particle, init_var,  max_steps, mutation_rate):
    x=particle.x
    dim=len(x)
    s=particle.score
    
    MAX_SUCCESS= 4
    MAX_FAIL   = 4
    FACTOR_EXPENSION =   2.0
    FACTOR_CONSTRACTION=0.5
    MIN_VAR    =0.01

    i=0
    success = 0 
    fail = 0 
    steps = 0 
    t_score =0
    t = []
    d = []
    bias = []
    var = []
    terminate = False 

    var=init_var[:]
    
    for i in range(dim):
        bias.append(0.0)

    while (steps < max_steps and not terminate):
        #  generate new position
        d=[]
        for i in range(dim):
            if (ranf()<mutation_rate): 
                d.append( granf(var[i]) + bias[i]  )
            else:
                d.append(0.0)                
            if debug:
                print "  d[%d]=%f"%(i,d[i])

        #  try t = x + d
        t=[]
        for i in range(dim):
            tmp= x[i] + d[i]
            mini, maxi=particle.genome[i].bounds
            if tmp>maxi:
                tmp=maxi
            elif tmp<mini:
                tmp=mini
            t.append( tmp)
            
        #t_score = fitness(t, dim)
        t_score=particle.evaluate(t)
        if(t_score < s):
            #print "t_score=%f, old score=%f"%(t_score, s)
            x=t[:]
            particle.x= t[:]
            s = t_score 
            for i in range(dim):
                bias[i] = 0.4 * d[i] + 0.2 * bias[i] 
            success+=1 
            fail = 0 
        
        else:        
            #  try t = x - d
            t=[]
            for i in range(dim):
                tmp= x[i] - d[i]
                mini, maxi=particle.genome[i].bounds
                if tmp>maxi:
                    tmp=maxi
                elif tmp<mini:
                    tmp=mini
                t.append( tmp)
                            
            #t_score = fitness(t, dim)
            t_score=particle.evaluate(t)            
            if(t_score < s):
                #print "t_score=%f, old score=%f"%(t_score, s)
                x=t[:]
                particle.x= t[:]
                s = t_score 
                for i in range(dim):
                    bias[i] = bias[i] - 0.4 * d[i] 
                success +=1 
                fail = 0 
            
            else: #  fail
                for i in range(dim):
                    bias[i] *= 0.5 
                fail +=1 
                success = 0 
            
        

        if(success >= MAX_SUCCESS):        
            for i in range(dim):
                var[i] *= FACTOR_EXPENSION 
            success = 0 
            #  enlarge step size
        
        elif(fail >= MAX_FAIL):
            for i in range(dim):            
                var[i] *= FACTOR_CONSTRACTION 
                if(var[i] < MIN_VAR):                
                    terminate = True 
                    break 
            
        
        steps+=1 
    
    particle.score= s
    if debug:
        print "##  local search  -->[%d] steps"%steps 
    return particle



import time, random
class PSO:

    ## FIXME: GENOME is a bad hack to get "toPhenoType"
    def __init__(self,evalFunc, genome, neval_max=2000,
                 enable_local_search=True, ls_max_steps=None, \
                 neighborhood_size=None, number_of_particles=None, \
                 w_max=None, w_min=None, freq=10, max_gens=None, \
                 mutation_rate=None, seed=None):
        """constructor """
        self.xmax = [] 
        self.xmin = []
        self.neval_max=neval_max #  maximal number of function evaluations
        
        for gene in genome:
            bd=gene.bounds
            self.xmin.append(bd[0])
            self.xmax.append(bd[1])       

        if enable_local_search in [True, False]:
            self.enable_local_search = enable_local_search

        # max steps for local search
        if ls_max_steps is not None:
            self.ls_max_steps = ls_max_steps 

        #  size of neighborhood
        if neighborhood_size is not None:
            self.neighborhood_size = neighborhood_size

        #  number of particles
        if number_of_particles is not None:
            self.number_of_particles = number_of_particles
        
        #  maximal inertia weight
        if w_max is not None:
            self.w_max = w_max

        #  minimal inertia weight    
        if w_min is not None:
            self.w_min = w_min

        # output frequency (every n generation)
        if freq is not None:
            self.freq = freq

        # maximum generations..
        if max_gens is not None:
            self.max_gens = max_gens

        # mutation rate..
        if mutation_rate is not None:
            self.mutation_rate=mutation_rate

        ## seed of random number generator
        if seed=="time" or seed==-1:
            currentTime=time.time()
            random.seed(currentTime)
            print 'Using system time as random seed :',currentTime
        else:
            t=type(seed)
            if (t==types.FloatType or t== types.IntType):
                print 'Using ',seed,' as random seed '
                random.seed(seed)
            else:
                print "Warning: Wrong random seed", seed
                print "Warning: Using system time as seed"
                random.seed(time.time())


        self.evalFunc = evalFunc
        self.genome=genome
        self.dim = len(genome)
        return

    def go(self):
        """ do the searching now """
        #  PSO settings
        dim=self.dim
        xmax=self.xmax
        xmin=self.xmin       
        self.gens =0        
        Np = self.number_of_particles 
        K  = self.neighborhood_size 

        ## hack... 10% as neighbor size
        ##K  = int( max(self.number_of_particles/10, 1) )  

        neval_max = self.neval_max    
        w=0.0 
        c1 = 2.0 
        c2 = 2.0 
        vmax = []     #  maximal velocity
        for i in range(dim):
            #vmax.append( (xmax[i]-xmin[i]) * 0.1 ) ## why 0.1
            vmax.append( (xmax[i]-xmin[i]) * 1 ) 
        
        self.swarm=Swarm(dim, xmax, xmin, vmax, Np, \
                     evalFunc=self.evalFunc, genome=self.genome) 
        self.neval = 0   #  number of evaluation
 
        #t_start=time.time()
        #print "PSO start at %s" % time.ctime()  

        S=self.swarm
        ## initialize the swarm
        for i in range(Np):
            S.pop[i].initialize() 
            S.pop[i].evaluate() 
            S.pop[i].p_score = S.pop[i].score 
            S.pop[i].p= S.pop[i].x[:]

        self.gens = 0 
        print "%-10s%-10s%-20s%10s"%("gens","neval","score","index")
        print "%-40s"%("_"*50)
       
        neval=0

        while neval < neval_max and self.gens<self.max_gens :
            ### WHY ????
            w = (self.w_max - self.w_min) / neval_max * (neval_max - neval)  \
                + self.w_min
            
            for i in range(Np):
                #  find Pg , the position from neighbors with lowest score 
                Pg = S.pop[i] 
                for j in range(i+1 ,i+K):
                    if(S.pop[j%Np].p_score < Pg.p_score):
                        Pg = S.pop[j%Np] 

                #  generate new velocity
                #  local method, weight declining
                ptr = S.pop[i] 
                for j in range(dim):
                    #  generate new velocity
                    ptr.v[j] = w  * ptr.v[j] \
                               + c1 * ranf() * (ptr.p[j] - ptr.x[j]) \
                               + c2 * ranf() * (Pg.p[j] - ptr.x[j]) 

                    #  repair velocity if it out of range [-vmax, vmax].
                    if ptr.v[j] > vmax[j] :
                        ptr.v[j] = vmax[j] 
                    elif(ptr.v[j] < -vmax[j]):
                        ptr.v[j] = -vmax[j] 

                    #  move to the new position
                    ptr.x[j] += ptr.v[j] 

                    # repair the particle
                    # if the position out of range [xmin, xmax].
                    if ptr.x[j] > xmax[j]:
                        ptr.x[j] = xmax[j] 
                    elif(ptr.x[j] < xmin[j]):
                        ptr.x[j] = xmin[j] 

                 #  end j (dim)
            
                ptr.evaluate() #  evaluate particle
                if ptr.score < ptr.p_score:
                    # if the particle is at a "better" place, save it.
                    ptr.p_score = ptr.score 
                    ptr.p= ptr.x[:]

            #  end i (popsize)
            
            #print "before best p_score=%f"%(S.bestp().p_score)
            if(self.enable_local_search):
                #  find the best particle
                ptr = S.best()
                #if debug:
                #print "b4 SW: ", ptr.x
                p_score=ptr.p_score
                ptr=SolisWet(ptr, vmax, self.ls_max_steps, self.mutation_rate)
                if(ptr.score < p_score):
                    #if debug:
                    #print "after SW: ", ptr.x
                    #print "local search:", p_score, "==>",ptr.score
                    ptr.p_score = ptr.score
                    foo=S.bestp().p_score
                    ptr.p=ptr.x[:]

            # end of local search
            self.gens+=1
            neval=self.genome.scorer.numEval
            if  (self.gens % self.freq)==0:
                print "%-10d%-10d%-20f%10d" %(self.gens, neval,
                                         S.bestp().p_score, S.bestpIndex())
                sys.stdout.flush()

           

        ## neval_max reached..
        #ptr = S.bestp()
        #t_end=time.time()
        #print "PSO finished at %s", time.ctime()
        #print "execution time: %7.2f mins."% ((t_end-t_start)/60.)

##         #  print final results
##         print "\n******************************************" 
##         print "Total number of generations: %d\n"% self.gens 
##         print "Total number of function evaluations: %d\n"% neval
##         print "\nINFO: best_gene=", ptr.p
##         print "\nINFO: best_score=", ptr.p_score 
##         print "******************************************\n" 

        return


    def best(self):
        """return optimized variable list and best score"""
        ptr = self.swarm.bestp()
        return ptr.p, ptr.p_score 

# end of class PSO

## EOF
