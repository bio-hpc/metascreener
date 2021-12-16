# -*- coding: utf-8 -*-
"""
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010 
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input 
#   from Arthur Olson's Molecular Graphics Lab
#
# HistoVol.py Authors: Graham Johnson & Michel Sanner with editing/enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# Copyright: Graham Johnson ©2010
#
# This file "HistoVol.py" is part of autoPACK, cellPACK, and AutoFill.
#    
#    autoPACK is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    autoPACK is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with autoPACK (See "CopyingGNUGPL" in the installation.
#    If not, see <http://www.gnu.org/licenses/>.
#
#
###############################################################################
@author: Graham Johnson, Ludovic Autin, & Michel Sanner

# Hybrid version merged from Graham's Sept 2011 and Ludo's April 2012 version on May 16, 2012
# Updated with final thesis HistoVol.py file from Sept 25, 2012 on July 5, 2012 with correct analysis tools

# TODO: fix the save/restore grid
"""
print ('histovol is on***********************************')

import os

from math import floor, ceil, fabs, sqrt,exp,cos
import time
from time import time

from random import randint, random, uniform, gauss, seed
import pdb
import bisect

import numpy, pickle, weakref

print ('AF import')
from AutoFill.Organelle import OrganelleList
from AutoFill.Recipe import Recipe
from AutoFill.Ingredient import GrowIngrediant,ActinIngrediant
from AutoFill.ray import vlen, vdiff, vcross
#from mglutil.math.rotax import rotVectToVect
import math
import sys

if sys.version > "3.0.0":
    xrange = range
try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib

#theses were alternative for the point list handling
#we actually dont use it
#from collections import deque
#try:
#    from blist import blist
#except:
#    blist = list
#from ctypes import *

#from AutoFill.cGrid import c_grid
from operator import itemgetter, attrgetter

import AutoFill
try :
    helper = AutoFill.helper
except :
    helper = None
print ("HistoVol helper is "+str(helper))

LOG = False
verbose = 0



try :
    import panda3d
    print ("got Panda3D raw")
except :    
    p="/Developer/Panda3D/lib"#sys.path.append("/Developer/Panda3D/lib/")
    sys.path.append(p)
    print ("Trying Panda3D Except")
try :
    import panda3d
    
    from panda3d.core import Mat4,Vec3,Point3
    from panda3d.core import TransformState
    from panda3d.core import BitMask32
    from panda3d.bullet import BulletSphereShape,BulletBoxShape,BulletCylinderShape
    #        from panda3d.bullet import BulletUpAxis
    from panda3d.bullet import BulletRigidBodyNode
    from panda3d.core import NodePath
    print ("Got Panda3D Except")
except :
    panda3d = None
    print ("Failed to get Panda")

import json


LISTPLACEMETHOD = AutoFill.LISTPLACEMETHOD
    
def linearDecayProb():
    """ return a number from 0 (higest probability) to 1 (lowest probability)
    with a linear fall off of probability
    """
    r1 = uniform(-0.25,0.25)
    r2 = uniform(-0.25,0.25)
    return abs(r1+r2)
    #r3 = uniform(-0.25,0.25)
    #r4 = uniform(-0.25,0.25)
    #return abs(r1+r2+r3+r4)  # Gaussian decay



def ingredient_compare1(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    """
    p1 = x.packingPriority
    p2 = y.packingPriority
    if p1 < p2: # p1 > p2
        return 1
    elif p1==p2: # p1 == p1
       r1 = x.minRadius
       r2 = y.minRadius
       if r1 > r2: # r1 < r2
           return 1
       elif r1==r2: # r1 == r2
           c1 = x.completion
           c2 = y.completion
           if c1 > c2: # c1 > c2
               return 1
           elif c1 == c2:
               return 0
           else:
               return -1
       else:
           return -1
    else:
       return -1

def ingredient_compare0(x, y):
    """
    sort ingredients using decreasing priority and decreasing radii for
    priority ties and decreasing completion for radii ties
    """
    p1 = x.packingPriority
    p2 = y.packingPriority
    if p1 > p2: # p1 > p2
        return 1
    elif p1==p2: # p1 == p1
       r1 = x.minRadius
       r2 = y.minRadius
       if r1 > r2: # r1 < r2
           return 1
       elif r1==r2: # r1 == r2
           c1 = x.completion
           c2 = y.completion
           if c1 > c2: # c1 > c2
               return 1
           elif c1 == c2:
               return 0
           else:
               return -1
       else:
           return -1
    else:
       return -1


def ingredient_compare2(x, y):
    """
    sort ingredients using decreasing radii and decresing completion
    for radii matches
    """
    c1 = x.minRadius
    c2 = y.minRadius
    if c1 < c2:
        return 1
    elif c1==c2:
       r1 = x.completion
       r2 = y.completion
       if r1 > r2:
          return 1
       elif r1 == r2:
          return 0
       else:
          return -1
    else:  #x < y
       return -1
       
def cmp2key(mycmp):
    "Converts a cmp= function into a key= function"
    class K:
        def __init__(self, obj, *args):
            self.obj = obj
        def __cmp__(self, other):
            return mycmp(self.obj, other.obj)
    return K       

from .randomRot import RandomRot

def vector_norm(data, axis=None, out=None):
    data = numpy.array(data, dtype=numpy.float64, copy=True)
    if out is None:
        if data.ndim == 1:
            return math.sqrt(numpy.dot(data, data))
        data *= data
        out = numpy.atleast_1d(numpy.sum(data, axis=axis))
        numpy.sqrt(out, out)
        return out
    else:
        data *= data
        numpy.sum(data, axis=axis, out=out)
        numpy.sqrt(out, out)
        
def angleVector(v0,v1, directed=True, axis=0):
    v0 = numpy.array(v0, dtype=numpy.float64, copy=False)
    v1 = numpy.array(v1, dtype=numpy.float64, copy=False)
    dot = numpy.sum(v0 * v1, axis=axis)
    dot /= vector_norm(v0, axis=axis) * vector_norm(v1, axis=axis)
    return numpy.arccos(dot if directed else numpy.fabs(dot))

def vdistance(c0,c1):
    d = numpy.array(c1) - numpy.array(c0)
    s = numpy.sum(d*d)
    return math.sqrt(s)

class Gradient:
    def __init__(self,name,mode="X",description="",direction=None,bb=None,**kw):
        self.name=name
        self.description=description
        self.start=[]
        self.end=[]
        self.bb=[[],[]]
        if bb is not None:
            self.computeStartEnd()
        self.function=self.defaultFunction #lambda ? 
        self.weight = None
        self.liste_mode = ["X","Y","Z","-X","-Y","-Z","direction","radial"]
        self.mode = mode #can X,Y,Z,-X,-Y,-Z,"direction" custom vector 
        self.weight_mode = "gauss"#"linear" #linear mode for weight generation linearpos linearneg
        if "weight_mode" in kw :
            self.weight_mode = kw["weight_mode"]
        self.pick_mode = "rnd"
        if "pick_mode" in kw :
            self.pick_mode = kw["pick_mode"]
        self.axes = {"X":0,"-X":0,"Y":1,"-Y":1,"Z":2,"-Z":2}
        self.directions = {"X":[1,0,0],"-X":[-1,0,0],"Y":[0,1,0],"-Y":[0,-1,0],"Z":[0,0,1],"-Z":[0,0,-1]}
        self.radius=10.0
        if "radius" in kw :
            self.radius=kw["radius"]
        self.weight_threshold = 0.0
        if direction is None :
            self.direction = self.directions[self.mode]
        else :
#            self.mode = "direction"
            self.direction=direction#from direction should get start and end point of the gradient
        self.distance=0.0
        #Note : theses functions could also be used to pick an ingredient
        self.pick_functions = {"max":self.getMaxWeight,
                               "min":self.getMinWeight,
                               "rnd":self.getRndWeighted,
                               "linear":self.getLinearWeighted,
                               "binary":self.getBinaryWeighted,
                               "sub":self.getSubWeighted,
                               }    
        self.liste_weigth_mode = self.pick_functions.keys()
        self.liste_options = ["mode","weight_mode","pick_mode","direction","radius"]
        self.OPTIONS = {
                    "mode":{"name":"mode","values":self.liste_mode,"default":"X",
                                           "type":"liste","description":"gradient direction",
                                           "min":0,"max":0},
                    "weight_mode":{"name":"weight_mode","values":["linear","gauss"],"default":"linear","type":"liste",
                                           "description":"calcul of the weight method","min":0,"max":0},
                    "pick_mode":{"name":"weight_mode","values":self.liste_weigth_mode,"default":"linear","type":"liste",
                                           "description":"picking random weighted method","min":0,"max":0},
                    "direction":{"name":"direction","value":[0.5,0.5,0.5],"default":[0.5,0.5,0.5],
                                 "type":"vector","description":"gradient custom direction","min":-2000.0,"max":2000.0},
                    "description":{"name":"description","value":self.description,"default":"a gradient",
                                 "type":"label","description":None,"min":0,"max":0}, 
                    "radius":{"name":"radius","value":self.radius,"default":100.0,
                                 "type":"float","description":"radius for the radial mode","min":0,"max":2000.0}, 
                                 
                    }

    def getCenter(self):
        center=[0.,0.,0.]
        for i in range(3):
            center[i]=(self.bb[0][i]+self.bb[1][i])/2.
        return center
                
    def computeStartEnd(self):
        #using bb and direction
        self.start=numpy.array(self.bb[0])
        self.end = numpy.array(self.bb[1])*numpy.array(self.direction)
        self.vgradient = self.end - self.start
        #self.distance = math.sqrt(numpy.sum(d*d))
        
    def defaultFunction(self,xyz):
        #linear function 0->0.1
        #project xyz on direction
        x = numpy.dot(xyz,self.direction)
        v = (x * 1.0) / (self.distance)
        return v

    def pickPoint(self,listPts):
        return self.pick_functions[self.pick_mode](listPts)
                
    def buildWeigthMap(self,bb,MasterPosition):
        print ("gradient ",self.name,self.mode)
        if self.mode in self.axes :
            self.buildWeigthMapAxe(bb,MasterPosition)
        elif self.mode == "direction":
            self.buildWeigthMapDirection(bb,MasterPosition)
        elif  self.mode == "radial":
            self.buildWeigthMapRadial(bb,MasterPosition)
    
    def get_gauss_weights(self,N,degree=5):
        degree = N/2
        window=N#degree*2#-1  
        weight=numpy.array([1.0]*window)          
        weightGauss=[]  
        for i in range(window):  
            i=i-degree+1  
            frac=i/float(window)  
            gauss=1/(numpy.exp((4*(frac))**2))  
            weightGauss.append(gauss) 
        return numpy.array(weightGauss)*weight  

        
    def getDirectionLength(self,bb=None,direction=None):
        if direction is None :
            direction = self.direction
        if bb is None :
            bb = self.bb
        print (bb)    
        #assume grid orthogonal
        maxinmini=[]
        a=[]
        axes = ["X","Y","Z"]
        for i,ax in enumerate( axes ):
            angle=angleVector(self.directions[ax],direction)
            a.append(angle)
            maxi=max(bb[1][i],bb[0][i])
            mini=min(bb[1][i],bb[0][i])
            maxinmini.append([mini,maxi])
        m = min(a)
        axi = a.index(m)
        L = maxinmini[axi][1]-maxinmini[axi][0]
        vdot = numpy.dot(numpy.array(self.directions[axes[axi]]),numpy.array(direction))#cos a * |A|*|B|
        Ld = (1.0/vdot)*(cos(m)*L)
        return Ld,maxinmini
        
    def get_gauss_weights1(self,N):
        support_points = [(float(3 * i)/float(N))**2.0 for i in range(-N,N + 1)]
        gii_factors = [exp(-(i/2.0)) for i in support_points]
        ki = float(sum(gii_factors))
        return [giin/ki for giin in gii_factors]
 
    def buildWeigthMapRadial(self,bb,MasterPosition):
        N = len(MasterPosition)
        self.bb= bb
        radial_point = self.direction
        NW=N/3
        self.weight =[]
        center = self.getCenter()
        xl,yl,zl = bb[0]
        xr,yr,zr = bb[1]

        if self.weight_mode == "gauss" :
            d = self.get_gauss_weights(NW)#numpy.random.normal(0.5, 0.1, NW) #one dimension 
        print (self.name,self.radius)
        for ptid in range(N) :
            dist=vdistance(MasterPosition[ptid],radial_point)
            if self.weight_mode == "linear" :
                w = (1.0-(abs(dist)/self.radius)) if abs(dist) < self.radius else 0.0
                self.weight.append( w )#
            elif self.weight_mode == "gauss" :
                w = abs(dist)/self.radius if abs(dist) < self.radius else 1.0
                i = int(w*N/3) if int(w*N/3) < len(d) else len(d)-1
#                print i,vax,(vax*N/3),int(vax*N/3),len(d)
                self.weight.append( d[i] )
       
    def buildWeigthMapDirection(self,bb,MasterPosition):
        #need BB, max and min
        #grid usually orthonorme
        N = len(MasterPosition)
        self.bb= bb
        axe = self.direction
        NW=N/3
        self.weight =[]
        center = self.getCenter()
        L,maxinmini = self.getDirectionLength(bb)
        if self.weight_mode == "gauss" :
            d = self.get_gauss_weights(NW)#numpy.random.normal(0.5, 0.1, NW) #one dimension 
        for ptid in range(N) :
            pt = numpy.array(MasterPosition[ptid])-numpy.array(center)#[maxinmini[0][0],maxinmini[1][0],maxinmini[2][0]])
            vdot = numpy.dot(pt,numpy.array(axe))
            p = ((L/2.0)+vdot)/L
            if self.weight_mode == "linear" :
                self.weight.append( p )#-0.5->0.5 axe value normalized?
            elif self.weight_mode == "gauss" :
#                p goes from 0.0 to 1.0
#                if p < 0.1 : p = 0.0
#                i = int(p*NW) if int(p*NW) < len(d) else len(d)-1
#                w = d[i] if d[i] > 0.9 else 0.0
                self.weight.append(1.0)# d[i] )

    def buildWeigthMapAxe(self,bb,MasterPosition,Axe="X"):
        #need BB, max and min
        #grid usually orthonorme
#        print MasterPosition
        N = len(MasterPosition)
        self.bb= bb
        ind = self.axes[self.mode]
        maxi=max(bb[1][ind],bb[0][ind])
        mini=min(bb[1][ind],bb[0][ind])
        maxix=max(bb[1][0],bb[0][0])
        minix=min(bb[1][0],bb[0][0])
        self.weight =[]
        if self.weight_mode == "gauss" :
            d = self.get_gauss_weights(N/3)#d = numpy.random.normal(0.5, 0.1, N/3) #one dimension 
#        print (N,N/3,len(d))
        for ptid in range(N) :
            if self.weight_mode == "linear" :
                self.weight.append( (MasterPosition[ptid][ind]-mini)/(maxi-mini) )#-0.5->0.5 axe value normalized?
            elif self.weight_mode == "gauss" :
#                x = (MasterPosition[ptid][0]-minix)/(maxix-minix) 
#                if x < 0.5 :
#                    self.weight.append( 0.0)
#                else :
                #compare dot product to that
#                vdot = numpy.array()
                vax=(MasterPosition[ptid][ind]-mini)/(maxi-mini) #0-1 on the axes
                i = int(vax*N/3) if int(vax*N/3) < len(d) else len(d)-1
#                print i,vax,(vax*N/3),int(vax*N/3),len(d)
                self.weight.append( d[i] )
                
    def getMaxWeight(self,listPts):
        ptInd = listPts[0]
        m=0.0                
        for pi in listPts :
            if self.weight[pi] > m :
                m=self.weight[pi]
                ptInd = pi
        if self.weight[ptInd] < self.weight_threshold:
            ptInd= None
        #print "picked",self.weight[ptInd]
        return ptInd
        
    def getMinWeight(self,listPts):   
        ptInd = listPts[0]
        m=1.1         
        for pi in  listPts :
            if self.weight[pi] < m :
                m=self.weight[pi]
                ptInd = pi
        if self.weight[ptInd] < self.weight_threshold:
            return None
        return ptInd
        

        
    def getRndWeighted(self,listPts):
        """
        From http://glowingpython.blogspot.com/2012/09/weighted-random-choice.html
        Weighted random selection
        returns n_picks random indexes.
        the chance to pick the index i 
        is give by the weight weights[i].
        """
        weight = numpy.take(self.weight,listPts)
        t = numpy.cumsum(weight)
        s = numpy.sum(weight)
        i = numpy.searchsorted(t,numpy.random.rand(1)*s)[0]
        return listPts[i]

    def getLinearWeighted(self,listPts):
        """
        From http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        The following is a simple function to implement weighted random selection in Python. 
        Given a list of weights, it returns an index randomly, according to these weights [2].
        For example, given [2, 3, 5] it returns 0 (the index of the first element) with probability 0.2, 
        1 with probability 0.3 and 2 with probability 0.5. 
        The weights need not sum up to anything in particular, 
        and can actually be arbitrary Python floating point numbers.
        """
        totals = []
        running_total = 0
        weights = numpy.take(self.weight,listPts)
        for w in weights:
            running_total += w
            totals.append(running_total)
    
        rnd = random() * running_total
        for i, total in enumerate(totals):
            if rnd < total:
                return listPts[i]

    def getBinaryWeighted(self,listPts):
        """
        From http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        Note that the loop in the end of the function is simply looking 
        for a place to insert rnd in a sorted list. Therefore, it can be 
        speed up by employing binary search. Python comes with one built-in, 
        just use the bisect module.
        """
        totals = []
        running_total = 0
        
        weights = numpy.take(self.weight,listPts)
        for w in weights:
            running_total += w
            totals.append(running_total)
    
        rnd = random() * running_total
        i = bisect.bisect_right(totals, rnd)
        return listPts[i]

    def getSubWeighted(self,listPts):
        """
        From http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python/
        This method is about twice as fast as the binary-search technique, 
        although it has the same complexity overall. Building the temporary 
        list of totals turns out to be a major part of the functions runtime.
        This approach has another interesting property. If we manage to sort 
        the weights in descending order before passing them to 
        weighted_choice_sub, it will run even faster since the random 
        call returns a uniformly distributed value and larger chunks of 
        the total weight will be skipped in the beginning.
        """
        
        weights = numpy.take(self.weight,listPts)
        rnd = random() * sum(weights)
        for i, w in enumerate(weights):
            rnd -= w
            if rnd < 0:
                return listPts[i]
                
class Grid:
    def __init__(self):
        #a grid is attached to an environement
        self.boundingBox=([0,0,0], [.1,.1,.1])
        # this list provides the id of the component this grid points belongs
        # to. The id is an integer where 0 is the Histological Volume, and +i is
        # the surface of organelle i and -i is the interior of organelle i
        # in the list self. organelles
        self.gridPtId = []
        # will be a list of indices into 3D of histovol
        # of points that have not yet been used by the fill algorithm
        # entries are removed from this list as grid points are used up
        # during hte fill. This list is used to pick points randomly during
        # the fill
        self.freePoints = []#blist()#[]#deque()
        self.nbFreePoints = 0
        # this list evolves in parallel with self.freePoints and provides
        # the distance to the closest surface (either an already placed
        # object (or an organelle surface NOT IMPLEMENTED)
        self.distToClosestSurf = []
        self.diag=None
        self.gridSpacing = None
        self.nbGridPoints = None
        self.nbSurfacePoints = 0
        self.gridVolume = 0 # will be the toatl number of grid points
        # list of (x,y,z) for each grid point (x index moving fastest)
        self.masterGridPositions = []
        
        #this are specific for each organelle
        self.aInteriorGrids = []
        self.aSurfaceGrids = []
        #bhtree
        self.surfPtsBht=None
        self.ijkPtIndice = []
        self.filename=None#used for storing before fillso no need rebuild
        self.result_filename=None#used after fill to store result

        self.encapsulatingGrid = 1
        
    def removeFreePoint(self,pti):
        tmp = self.freePoints[self.nbFreePoints] #last one
        self.freePoints[self.nbFreePoints] = pti
        self.freePoints[pti] = tmp
        self.nbFreePoints -= 1        

# Very dangerous to manipulate the grids... lets solve this problem much earlier in the setup with the new PseudoCode
#    def updateDistances(self, histoVol ,insidePoints, freePoints,
#                        nbFreePoints ):
#        verbose = histoVol.verbose
#        nbPts = len(insidePoints)
#        for pt in insidePoints:  #Reversing is not necessary if you use the correct Swapping GJ Aug 17,2012
#            try :
#                # New system replaced by Graham on Aug 18, 2012
#                nbFreePoints -= 1  
#                vKill = freePoints[pt]
#                vLastFree = freePoints[nbFreePoints]
#                freePoints[vKill] = vLastFree
#                freePoints[vLastFree] = vKill
#            except :
#                pass 
#            
#        return nbFreePoints,freePoints
    

    def removeFreePointdeque(self,pti):
        self.freePoints.remove(pti)

    def create3DPointLookup(self, boundingBox=None):
        #pFinalNumberOfPoints, pGridSpacing, pArrayOfTwoTotalCorners):
        # Fill the orthogonal bounding box described by two global corners
        # with an array of points spaces pGridSpacing apart.
        if boundingBox is None :
            boundingBox= self.boundingBox
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]

        nx,ny,nz = self.nbGridPoints
        pointArrayRaw = numpy.zeros( (nx*ny*nz, 3), 'f')
        self.ijkPtIndice = numpy.zeros( (nx*ny*nz, 3), 'i')
        space = self.gridSpacing
        # Vector for lower left broken into real of only the z coord.
        i = 0
        for zi in range(nz):
            for yi in range(ny):
                for xi in range(nx):
                    pointArrayRaw[i] = (xl+xi*space, yl+yi*space, zl+zi*space)
                    self.ijkPtIndice[i] = (xi,yi,zi)
                    i+=1
        self.masterGridPositions = pointArrayRaw

    def getPointFrom3D(self, pt3d):
        """
        get point number from 3d coordinates
        """
        x, y, z = pt3d  # Continuous 3D point to be discretized
        spacing1 = 1./self.gridSpacing  # Grid spacing = diagonal of the voxel determined by smalled packing radius
        NX, NY, NZ = self.nbGridPoints  # vector = [length, height, depth] of grid, units = gridPoints
        OX, OY, OZ = self.boundingBox[0] # origin of fill grid
        # Algebra gives nearest gridPoint ID to pt3D
        i = min( NX-1, max( 0, round((x-OX)*spacing1)))
        j = min( NY-1, max( 0, round((y-OY)*spacing1)))
        k = min( NZ-1, max( 0, round((z-OZ)*spacing1)))
        return int(k*NX*NY + j*NX + i)

    def getIJK(self,ptInd):
        #ptInd = k*(sizex)*(sizey)+j*(sizex)+i;#want i,j,k
        return self.ijkPtIndice[ptInd]

#    def getWindows(self,ptInd,size=1):
#        #get all point around ptInd
#        listePtind = []
#        ix,iy,iz = self.ijkPtIndice[ptInd]
#        for i in range(size):
            
        

    def checkPointInside(self,pt3d,dist=None):
        O = numpy.array(self.boundingBox[0])
        E = numpy.array(self.boundingBox[1])
        P = numpy.array(pt3d)
        test1 = P < O 
        test2 =  P > E
        if True in test1 or True in test2:
            #outside
            return False
        else :
            if dist is not None:
                d1 = P - O
                s1 = numpy.sum(d1*d1)
                d2 = E - P
                s2 = numpy.sum(d2*d2)
                if s1 <= dist or s2 <=dist:
                   return False 
            return True
        
    def getCenter(self):
        center=[0.,0.,0.]
        for i in range(3):
            center[i]=(self.boundingBox[0][i]+self.boundingBox[1][i])/2.
        return center
        
    def getRadius(self):
        d = numpy.array(self.boundingBox[0]) - numpy.array(self.boundingBox[1])
        s = numpy.sum(d*d)
#        s=0.
#        for i in range(3):
#            s += (self.boundingBox[0][i] - self.boundingBox[1][i])^2
        return math.sqrt(s)
        
    def getPointsInCube(self, bb, pt, radius,addSP=True,info=False):
        #return the PtId
        spacing1 = 1./self.gridSpacing
        NX, NY, NZ = self.nbGridPoints
        OX, OY, OZ = self.boundingBox[0] # origin of fill grid-> bottom lef corner not origin
        ox, oy, oz = bb[0]
        ex, ey, ez = bb[1]
#        print("getPointsInCube bb[0] = ",bb[0])
#        print("getPointsInCube bb[1] = ",bb[1])
        #        i0 = max(0, int((ox-OX)*spacing1)+1)
        i0 = int(max(0, floor((ox-OX)*spacing1)))
        i1 = int(min(NX, int((ex-OX)*spacing1)+1))
        #        j0 = max(0, int((oy-OY)*spacing1)+1)
        j0 = int(max(0, floor((oy-OY)*spacing1)))
        j1 = int(min(NY, int((ey-OY)*spacing1)+1))
        #        k0 = max(0, int((oz-OZ)*spacing1)+1)
        k0 = int(max(0, floor((oz-OZ)*spacing1)))
        k1 = int(min(NZ, int((ez-OZ)*spacing1)+1))
#        print("oz-OZ = ", oz-OZ)
#        print("((oz-OZ)*spacing1) = ", ((oz-OZ)*spacing1))
#        print("int((oz-OZ)*spacing1)) = ", int((oz-OZ)*spacing1))
#        print("int((oz-OZ)*spacing1)+1 = ", int((oz-OZ)*spacing1)+1)
#        print("floor(oz-OZ)*spacing1) = ", floor((oz-OZ)*spacing1))
#        print("i0= ", i0, ", i1= ", i1,", j0= ", j0,", j1= ",j1,", k0= ", k0, ", k1= ", k1)

        zPlaneLength = NX*NY
#        print ("zPlaneLength = ", zPlaneLength)

        ptIndices = []
        for z in range(k0,k1):
            offz = z*zPlaneLength
            for y in range(j0,j1):
                off = y*NX + offz
                #ptIndices.extend(numpy.arange(i0,i1)+off)
                for x in range(i0,i1):
                    ptIndices.append( x + off)
#                    print("position of point ",x+off," = ", self.masterGridPositions[x+off])

        # add surface points,but what if surface point not in the box
        if addSP and self.nbSurfacePoints != 0:
            result = numpy.zeros( (self.nbSurfacePoints,), 'i')
            nb = self.surfPtsBht.closePoints(tuple(pt), radius, result )
            dimx, dimy, dimz = self.nbGridPoints
            ptIndices.extend(list(map(lambda x, length=self.gridVolume:x+length,
                             result[:nb])) )
            #print("getPointsInCube ptIndices with sp = ",nb,ptIndices[-nb:])
#            if info :
#                return ptIndices,nb
        return ptIndices

    def computeGridNumberOfPoint(self,boundingBox,space):
#        print('bounding box = ', boundingBox)
#        print('space = ', space)
        # compute number of points
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]

        encapsulatingGrid = self.encapsulatingGrid  #Graham Added on Oct17 to allow for truly 2D grid for test fills... may break everything!
        
        from math import ceil
        nx = int(ceil((xr-xl)/space))+encapsulatingGrid
        ny = int(ceil((yr-yl)/space))+encapsulatingGrid
        nz = int(ceil((zr-zl)/space))+encapsulatingGrid
#        print("nx = ", nx)
#        print("ny = ", ny)
#        print("nz = ", nz)
#        print("$$$$$$$$$$$$$   Encapsulating Grid = ", encapsulatingGrid)
        return nx*ny*nz,(nx,ny,nz)

    def save(self):
        pass
    def restore(self):
        pass
        
class Environment(OrganelleList):

    def __init__(self,name="H"):
        OrganelleList.__init__(self)
        self.verbose = verbose  #Graham added to try to make universal "global variable Verbose" on Aug 28
        self.timeUpDistLoopTotal = 0 #Graham added to try to make universal "global variable Verbose" on Aug 28
        self.name = name        
        self.exteriorRecipe = None
        self.hgrid=[]
        self.world = None
        self.grid = Grid()
        self.encapsulatingGrid = 1  # Only override this with 0 for 2D fills- otherwise its very unsafe!
        self.nbOrganelles = 1 # 0 is the exterior, 1 is organelle 1 surface, -1 is organelle 1 interior, etc.
        self.name = "out"
        self.organelles = [] # list of all organelles in thei sHistoVol
        self.order={}#give the order of drop ingredient by ptInd from molecules
        self.lastrank=0
        # smallest and largest protein radii acroos all recipes
        self.smallestProteinSize = 99999999
        self.largestProteinSize = 0
        self.computeGridParams = True
        self.EnviroOnly = False
        self.EnviroOnlyCompartiment  =  -1
        # bounding box of the HistoVol

        self.boundingBox = [[0,0,0], [.1,.1,.1]]
        self.fbox_bb = None #used for estimating the volume
        
        self.fbox = None #Oct 20, 2012 Graham wonders if this is part of the problem
        self.fillBB = None # bounding box for a given fill
        self.fillbb_insidepoint =None #Oct 20, 2012 Graham wonders if this is part of the problem
        self.freePointMask =None
        self.molecules = [] # list of ( (x,y,z), rotation, ingredient) triplet generated by fill 
        self.ingr_result = {}
        self.ingr_added = {}
        t1=time()
        self.randomRot = RandomRot()
#        print ("random rot",time()-t1)
        self.activeIngr= [] 
        self.activeIngre_saved = []
        self.host = None
        self.afviewer = None
        
        self.version = "1.0"
        #option for filling using host dynamics capability
        self.windowsSize = 100
        self.windowsSize_overwrite = False

        self.simulationTimes = 2.0
        self.runTimeDisplay = False
        self.placeMethod="jitter"
        self.innerGridMethod = "bhtree" #or sdf
        self.orthogonalBoxType = 0
        self.overwritePlaceMethod = False
        self.springOptions={}
        self.dynamicOptions={}
        self.setupRBOptions()
        
        #saving/pickle option
        self.saveResult = False
        self.resultfile = "fillResult"
        self.setupfile = ""
        self.grid_filename =None#
        self.grid_result_filename = None#str(gridn.getAttribute("grid_result"))

        #cancel dialog
        self.cancelDialog = False
        
        #
        self.nFill = 0
        self.cFill = 0
        self.FillName=[]
        
        ##do we sort the ingrediant or not see  getSortedActiveIngredients
        self.pickWeightedIngr = True 
        self.pickRandPt = True       ##point pick randomly or one after the other?
        self.currtId = 0
        
        #gradient
        self.gradients={}
        self.use_gradient=False #gradient control is per ingredient
        
        self.ingrLookForNeighbours = True
        
        #debug with timer function
        self._timer = False
        self._hackFreepts = False
        self._useblist = True
        self.freePtsUpdateThrehod = 0.15
        
        self.listPlaceMethod = LISTPLACEMETHOD
        #should be part of an independant module        
        self.rb_func_dic={
        "SingleSphere":self.addSingleSphereRB,
        "SingleCube":self.addSingleCubeRB,
        "MultiSphere":self.addMultiSphereRB,
        "MultiCylinder":self.addMultiCylinderRB,
        "Mesh":self.addMeshRB,
        }
        self.OPTIONS = {
                    "smallestProteinSize":{"name":"smallestProteinSize","value":15,"default":15,
                                           "type":"int","description":"Smallest ingredient packing radius override (low=accurate | high=fast)",
                                           "mini":1.0,"maxi":100.0,
                                           "width":30},
                    "largestProteinSize":{"name":"largestProteinSize","value":0,"default":0,"type":"int","description":"largest Protein Size","width":30},
                    "computeGridParams":{"name":"computeGridParams","value":True,"default":True,"type":"bool","description":"compute Grid Params","width":100},
                    "EnviroOnly":{"name":"EnviroOnly","value":False,"default":False,"type":"bool","description":"Histo volume Only","width":30},
#                    "EnviroOnlyCompartiment":{"name":"EnviroOnlyCompartiment","value":-1,"default":-1,"type":"int","description":"Histo volume Only compartiment"},
                    "windowsSize":{"name":"windowsSize","value":100,"default":100,"type":"int","description":"windows Size","width":30},
#                    "simulationTimes":{"name":"simulationTimes","value":90,"default":90,"type":"int","description":"simulation Times"},
                    "runTimeDisplay":{"name":"runTimeDisplay","value":False,"default":False,"type":"bool","description":"Display packing in realtime (slow)","width":150},
                    "placeMethod": {"name":"placeMethod","value":"jitter","values":self.listPlaceMethod,"default":"placeMethod","type":"liste","description":"     Overriding Packing Method = ","width":30},
                    "use_gradient":{"name":"use_gradient","value":False,"default":False,"type":"bool","description":"Use gradients if defined","width":150},
                    "gradients":{"name":"gradients","value":"","values":[],"default":"","type":"liste","description":"Gradients available","width":150},
                    "innerGridMethod": {"name":"innerGridMethod","value":"bhtree","values":["bhtree","sdf","jordan","jordan3"],"default":"innerGridMethod","type":"liste","description":"     Method to calculate the inner grid:","width":30},
                    "overwritePlaceMethod":{"name":"overwritePlaceMethod","value":False,"default":False,"type":"bool","description":"Overwrite per-ingredient packing method with Overriding Packing Method:","width":300},
                    "saveResult": {"name":"saveResult","value":False,"default":False,"type":"bool","description":"Save packing result to .apr file (enter full path below):","width":200},
                    "resultfile": {"name":"resultfile","value":"fillResult","default":"fillResult","type":"filename","description":"result filename","width":200},
                    #cancel dialog
                    "cancelDialog": {"name":"cancelDialog","value":False,"default":False,"type":"bool","description":"compute Grid Params","width":30},
                    ##do we sort the ingrediant or not see  getSortedActiveIngredients
                    "pickWeightedIngr":{"name":"pickWeightedIngr","value":True,"default":True,"type":"bool","description":"Prioritize ingredient selection by packingWeight","width":200},
                    "pickRandPt":{"name":"pickRandPt","value":True,"default":True,"type":"bool","description":"Pick drop position point randomly","width":200},
                    #gradient
                    "ingrLookForNeighbours":{"name":"pickWeightedIngr","value":True,"default":True,"type":"bool","description":"compute Grid Params","width":30},
                    #debug with timer function
                    "_timer": {"name":"_timer","value":False,"default":False,"type":"bool","description":"evaluate time per function","width":30},
                    "_hackFreepts": {"name":"_hackFreepts","value":False,"default":False,"type":"bool","description":"no free point update","width":30},
                    "freePtsUpdateThrehod":{"name":"freePtsUpdateThrehod","value":0.15,"default":0.15,"type":"float","description":"Mask grid while packing (0=always | 1=never)","mini":0.0,"maxi":1.0,"width":30},
                        }

    def Setup(self,setupfile):
        #parse the given fill for
        #1-fillin option
        #2-recipe
        #use XML with tag description of the setup:
        #filling name root
        #histoVol option
        #cytoplasme recipe if any and its ingredient
        #organelle name= mesh ?
        #orga surfaceingr#file or direct
        #orga interioringr#file or direct
        #etc...
        pass

    def makeIngredient(self,**kw):
        from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr,SingleCubeIngr
        from AutoFill.Ingredient import MultiCylindersIngr, GrowIngrediant
        ingr = None

        if kw["Type"]=="SingleSphere":
            kw["position"] = kw["positions"][0][0]
            kw["radius"]=kw["radii"][0][0]
            del kw["positions"]
            del kw["radii"]
            ingr = SingleSphereIngr(**kw)
        elif kw["Type"]=="MultiSphere":
            ingr = MultiSphereIngr(**kw)                    
        elif kw["Type"]=="MultiCylinder":
            ingr = MultiCylindersIngr(**kw)                    
        elif kw["Type"]=="SingleCube":
            kw["positions"]=[[[0,0,0],[0,0,0],[0,0,0],]]
            kw["positions2"]=None
            ingr = SingleCubeIngr(**kw)                    
        elif kw["Type"]=="Grow":
            ingr = GrowIngrediant(**kw)                    
        elif kw["Type"]=="Actine":
            ingr = ActineIngrediant(**kw)       
        if "gradient" in kw and kw["gradient"] != "" and kw["gradient"]!= "None":
            ingr.gradient = kw["gradient"]           
        return ingr
        
    def load_XML(self,setupfile):
        self.setupfile = setupfile
        from AutoFill import Ingredient as ingr
        from AutoFill.Ingredient import IOingredientTool
        io_ingr = IOingredientTool()
        from xml.dom.minidom import parse
        self.xmldoc = parse(setupfile) # parse an XML file by name
        root = self.xmldoc.documentElement
        self.name = str(root.getAttribute("name"))
        options=root.getElementsByTagName("options")
        if len(options) :
            options=options[0]
            for k in self.OPTIONS:
                if k == "gradients": 
                    continue
                v=self.getValueToXMLNode(self.OPTIONS[k]["type"],options,k)
                if v is not None :
                    setattr(self,k,v)
            v=self.getValueToXMLNode("vector",options,"boundingBox")
            self.boundingBox = v
            v=self.getValueToXMLNode("string",options,"version")
            self.version = v
            
        gradientsnode=root.getElementsByTagName("gradients")
        if len(gradientsnode) :
            gradientnode=gradientsnode[0]
            grnodes = gradientnode.getElementsByTagName("gradient")
            for grnode in grnodes:
                name = str(grnode.getAttribute("name"))
                mode = str(grnode.getAttribute("mode"))
                weight_mode = str(grnode.getAttribute("weight_mode"))
                pick_mode = str(grnode.getAttribute("pick_mode"))
                direction = str(grnode.getAttribute("direction"))#vector
                description=str(grnode.getAttribute("description"))
#                print "weight_mode",weight_mode
                self.setGradient(name=name,mode=mode, direction=eval(direction),
                            weight_mode=weight_mode,description=description,
                            pick_mode=pick_mode)

        gridnode=root.getElementsByTagName("grid")
        if len(gridnode) :
            gridn=gridnode[0]
            self.grid_filename = str(gridn.getAttribute("grid_storage"))
            self.grid_result_filename = str(gridn.getAttribute("grid_result"))

        rnode=root.getElementsByTagName("cytoplasme")
        if len(rnode) :
            rCyto = Recipe()
            rnode=rnode[0]
            ingrnodes = rnode.getElementsByTagName("ingredient")
            for ingrnode in ingrnodes:
                ingre = io_ingr.makeIngredientFromXml(inode = ingrnode , recipe=self.name)
#                name = str(ingrnode.getAttribute("name"))
#                kw = {}
#                for k in ingr.KWDS:
#                    v=self.getValueToXMLNode(ingr.KWDS[k]["type"],ingrnode,k)
#                    if v is not None :
#                        kw[k]=v                   
                #create the ingredient according the type
#                ingre = self.makeIngredient(**kw)                    
                rCyto.addIngredient(ingre) 
            #check for includes 
            ingrnodes_include = rnode.getElementsByTagName("include")
            for inclnode in ingrnodes_include:
                xmlfile = str(inclnode.getAttribute("filename"))
                ingre = io_ingr.makeIngredientFromXml(filename = xmlfile, recipe=self.name)
                rCyto.addIngredient(ingre)
            #setup recipe
            self.setExteriorRecipe(rCyto)
            
        onodes = root.getElementsByTagName("organelle")
        from AutoFill.Organelle import Organelle
        for onode in onodes:
            name = str(onode.getAttribute("name"))
            geom = str(onode.getAttribute("geom"))
            rep =  str(onode.getAttribute("rep"))
            rep_file=str(onode.getAttribute("rep_file"))
            if rep != "None" :
                rname =  rep_file.split("/")[-1]
                fileName, fileExtension = os.path.splitext(rname)
                if fileExtension == "" :
                    fileExtension = AutoFill.helper.hext
                    if fileExtension == "" :
                        rep_file = rep_file+fileExtension
                    else :
                        rep_file = rep_file+"."+fileExtension   
            else :
                rep=None
                rep_file=None
            o = Organelle(name,None, None, None,filename=geom,object_name=rep,object_filename=rep_file)
            self.addOrganelle(o)
            rsnodes = onode.getElementsByTagName("surface")
            if len(rsnodes) :
                rSurf = Recipe()
                rsnodes=rsnodes[0]
                ingrnodes = rsnodes.getElementsByTagName("ingredient")
                for ingrnode in ingrnodes:
                    ingre = io_ingr.makeIngredientFromXml(inode = ingrnode , recipe=self.name)
#                    name = str(ingrnode.getAttribute("name"))
#                    kw = {}
#                    for k in ingr.KWDS:
#                        v=self.getValueToXMLNode(ingr.KWDS[k]["type"],ingrnode,k)
#                        if v is not None :
#                            kw[k]=v                   
                    #create the ingredient according the type
#                    ingre = self.makeIngredient(**kw)                    
                    rSurf.addIngredient(ingre) 
                ingrnodes_include = rsnodes.getElementsByTagName("include")
                for inclnode in ingrnodes_include:
                    xmlfile = str(inclnode.getAttribute("filename"))
                    ingre = io_ingr.makeIngredientFromXml(filename = xmlfile , recipe=self.name)
                    rSurf.addIngredient(ingre)
                o.setSurfaceRecipe(rSurf)                
            rinodes = onode.getElementsByTagName("interior")
            if len(rinodes) :
                rMatrix = Recipe()
                rinodes=rinodes[0]
                ingrnodes = rinodes.getElementsByTagName("ingredient")
                for ingrnode in ingrnodes:
                    ingre = io_ingr.makeIngredientFromXml(inode = ingrnode , recipe=self.name)
#                    name = str(ingrnode.getAttribute("name"))
#                    kw = {}
#                    for k in ingr.KWDS:
#                        v=self.getValueToXMLNode(ingr.KWDS[k]["type"],ingrnode,k)
#                        if v is not None :
#                            kw[k]=v                   
#                   create the ingredient according the type
#                    ingre = self.makeIngredient(**kw)                    
                    rMatrix.addIngredient(ingre) 
                ingrnodes_include = rinodes.getElementsByTagName("include")
                for inclnode in ingrnodes_include:
                    xmlfile = str(inclnode.getAttribute("filename"))
                    ingre = io_ingr.makeIngredientFromXml(filename = xmlfile , recipe=self.name)
                    rMatrix.addIngredient(ingre)
                o.setInnerRecipe(rMatrix)
     
    def getValueToXMLNode(self,vtype,node,attrname):
#        print "getValueToXMLNode ",attrname
        value = node.getAttribute(attrname)
#        print "value " , value
        value = str(value)
        if not len(value):
            return None
        if vtype not in ["liste","filename","string"] :
            value=eval(value)
        else :
            value=str(value)
        return value
               
    def setValueToXMLNode(self,value,node,attrname):
        if value is None:
            return
        if attrname == "color" :
            if type(value) != list and type(value) != tuple :
                if AutoFill.helper is not None : 
                    value=helper.getMaterialProperty(value,["color"])[0]
                else :
                    value = [1.,0.,0.]
        if type (value) == numpy.ndarray :
            value = value.tolist()
        elif type(value) == list :
            for i,v in enumerate(value) :
                if type(v) == numpy.ndarray :
                    value[i] = v.tolist()
                elif type(v) == list :
                    for j,va in enumerate(v) :
                        if type(va) == numpy.ndarray :
                            v[j] = va.tolist()                        
#        print ("setValueToXMLNode ",attrname,value,str(value))  
        node.setAttribute(attrname,str(value))
            
    def save_asXML(self,setupfile,useXref=True):
        from AutoFill.Ingredient import IOingredientTool
        io_ingr = IOingredientTool()
        self.setupfile = setupfile
        pathout=os.path.dirname(os.path.abspath(self.setupfile))
        #export all information as xml
        #histovol is a tag, option are attribute of the tag
        from xml.dom.minidom import getDOMImplementation
        impl = getDOMImplementation()
        #what about afviewer
        self.xmldoc = impl.createDocument(None, "AutoFillSetup", None)
        root = self.xmldoc.documentElement
        root.setAttribute("name",str(self.name))
        options=self.xmldoc.createElement("options")
        for k in self.OPTIONS:
            v = getattr(self,k)
            if k == "gradients" :
                v = self.gradients.keys()
#            elif k == "runTimeDisplay"
            self.setValueToXMLNode(v,options,k)
        #add the boundin box
        self.setValueToXMLNode(self.boundingBox,options,"boundingBox")
        self.setValueToXMLNode(self.version,options,"version")#version?
        root.appendChild(options)
        
        if len(self.gradients):
            gradientsnode=self.xmldoc.createElement("gradients")
            root.appendChild(gradientsnode)
            for gname in self.gradients:
                g = self.gradients[gname]
                grnode = self.xmldoc.createElement("gradient")
                gradientsnode.appendChild(grnode)
                grnode.setAttribute("name",str(g.name))
                for k in g.OPTIONS:
                    v = getattr(g,k)
                    self.setValueToXMLNode(v,grnode,k)      

        #grid path information
        if self.grid.filename is not None or self.grid.result_filename is not None:
            gridnode=self.xmldoc.createElement("grid")
            root.appendChild(gridnode)
            gridnode.setAttribute("grid_storage",str(self.grid.filename))
            gridnode.setAttribute("grid_result",str(self.grid.result_filename))
        
        r =  self.exteriorRecipe
        if r :
            rnode=self.xmldoc.createElement("cytoplasme")
            root.appendChild(rnode)
            for ingr in r.ingredients:                
                if useXref :
                    io_ingr.write(ingr,pathout+os.sep+ingr.name,ingr_format="xml")
                    ingrnode = self.xmldoc.createElement("ingredient")
                    rnode.appendChild(ingrnode)
                    ingrnode.setAttribute("include",str(pathout+os.sep+ingr.name+".xml"))                    
                else :
                    ingrnode = self.xmldoc.createElement("ingredient")
                    rnode.appendChild(ingrnode)
                    ingrnode.setAttribute("name",str(ingr.name))
                    for k in ingr.KWDS:
                        v = getattr(ingr,k)
    #                    print ingr.name+" keyword ",k,v
                        self.setValueToXMLNode(v,ingrnode,k)
        for o in self.organelles:
            onode=self.xmldoc.createElement("organelle")
            root.appendChild(onode)
            onode.setAttribute("name",str(o.name))
            onode.setAttribute("geom",str(o.filename))#should point to the used filename
            onode.setAttribute("rep",str(o.representation))#None
            if o.representation is not None :
                fileName, fileExtension = os.path.splitext(o.representation_file)
            else :
                fileName = None
            onode.setAttribute("rep_file",str(fileName))#None
            rs = o.surfaceRecipe
            if rs :
                onodesurface=self.xmldoc.createElement("surface")
                onode.appendChild(onodesurface)
                for ingr in rs.ingredients: 
                    if useXref :
                        io_ingr.write(ingr,pathout+os.sep+ingr.name,ingr_format="xml")
                        ingrnode = self.xmldoc.createElement("ingredient")
                        onodesurface.appendChild(ingrnode)
                        ingrnode.setAttribute("include",str(pathout+os.sep+ingr.name+".xml")) 
                    else :
                        ingrnode = self.xmldoc.createElement("ingredient")
                        onodesurface.appendChild(ingrnode)
                        ingrnode.setAttribute("name",str(ingr.name))                       
                        for k in ingr.KWDS:
                            v = getattr(ingr,k)
                            self.setValueToXMLNode(v,ingrnode,k)
            ri = o.innerRecipe
            if ri :
                onodeinterior=self.xmldoc.createElement("interior")
                onode.appendChild(onodeinterior)             
                for ingr in ri.ingredients: 
                    if useXref :
                        io_ingr.write(ingr,pathout+os.sep+ingr.name,ingr_format="xml")
                        ingrnode = self.xmldoc.createElement("ingredient")
                        onodeinterior.appendChild(ingrnode)
                        ingrnode.setAttribute("include",str(pathout+os.sep+ingr.name+".xml")) 
                    else :
                        ingrnode = self.xmldoc.createElement("ingredient")
                        onodeinterior.appendChild(ingrnode)
                        ingrnode.setAttribute("name",str(ingr.name))                       
                        for k in ingr.KWDS:
                            v = getattr(ingr,k)
                            self.setValueToXMLNode(v,ingrnode,k)
        f = open(setupfile,"w")        
        self.xmldoc.writexml(f, indent="\t", addindent="", newl="\n")
        f.close()

    def includeIngrRecipes(self,ingrname, include):
        r =  self.exteriorRecipe
        if (self.includeIngrRecipe(ingrname, include,r)) :
            return
        for o in self.organelles:
            rs =  o.surfaceRecipe
            if (self.includeIngrRecipe(ingrname, include,rs)) :
                return
            ri =  o.innerRecipe
            if (self.includeIngrRecipe(ingrname, include,ri)) :
                return
                
    def includeIngrRecipe(self,ingrname, include,rs):
        for ingr in rs.exclude :
            if ingr.name==ingrname:
                if not include :
                    return True
                else :
                    rs.addIngredient(ingr)
                    return True
        for ingr in rs.ingredients:
            if ingrname == ingr.name:
                if not include :
                    rs.delIngredients(ingr)
                    return True
                else :
                    return True

    def includeIngredientRecipe(self,ingr, include):
        r=ingr.recipe()
#        print r
        if include :
            r.addIngredient(ingr)
        else :
            r.delIngredient(ingr)
    
    def setGradient(self,**kw):
        #create a grdaient
        #assign weight to point
        #listorganelle influenced
        #listingredient influenced
        if "name" not in kw :
            print ("name kw is required")
            return
        gradient = Gradient(**kw) 
        #default gradient 1-linear Decoy X
        self.gradients[kw["name"]] = gradient
        
    def setDefaultOptions(self):
        for options in self.OPTIONS:
            setattr(self,options,self.OPTIONS[options]["default"])
        
    def callFunction(self,function,args=[],kw={}):
        if self._timer:
            res = self.timeFunction(function,args,kw)
        else :
            if len(kw):
                res = function(*args,**kw)
            else :
                res = function(*args)
        return res
        
    def timeFunction(self,function,args,kw):
        """
        Mesure the time for performing the provided function. 
    
        @type  function: function
        @param function: the function to execute
        @type  args: liste
        @param args: the liste of arguments for the function
        
    
        @rtype:   list/array
        @return:  the center of mass of the coordinates
        """
         
        t1=time()
        if len(kw):
            res = function(*args,**kw)
        else :
            res = function(*args)
        print(("time "+function.__name__, time()-t1))
        return res

    def SetRBOptions(self,obj="moving",**kw):
        key = ["shape","child",
                    "dynamicsBody", "dynamicsLinearDamp", 
                    "dynamicsAngularDamp", 
                    "massClamp","rotMassClamp"]
        for k in key :
            val = kw.pop( k, None)
            if val is not None:  
                self.dynamicOptions[obj][k]
                
    def SetSpringOptions(self,**kw):
        key = ["stifness","rlength","damping"]
        for k in key :
            val = kw.pop( k, None)
            if val is not None:
                self.springOptions[k] = val
        
    def setupRBOptions(self):
        self.springOptions["stifness"] = 1.
        self.springOptions["rlength"] = 0.
        self.springOptions["damping"] = 1.
        self.dynamicOptions["spring"]={}
        self.dynamicOptions["spring"]["child"] = True
        self.dynamicOptions["spring"]["shape"] = "auto"
        self.dynamicOptions["spring"]["dynamicsBody"] = "on"
        self.dynamicOptions["spring"]["dynamicsLinearDamp"] = 0.0
        self.dynamicOptions["spring"]["dynamicsAngularDamp"] = 0.0
        self.dynamicOptions["spring"]["massClamp"] = 1.
        self.dynamicOptions["spring"]["rotMassClamp"] = 1.        
        self.dynamicOptions["moving"]={}
        self.dynamicOptions["moving"]["child"] = True
        self.dynamicOptions["moving"]["shape"] = "auto"
        self.dynamicOptions["moving"]["dynamicsBody"] = "on"
        self.dynamicOptions["moving"]["dynamicsLinearDamp"] = 1.0
        self.dynamicOptions["moving"]["dynamicsAngularDamp"] = 1.0
        self.dynamicOptions["moving"]["massClamp"] = .001
        self.dynamicOptions["moving"]["rotMassClamp"] = .1        
        self.dynamicOptions["static"]={}
        self.dynamicOptions["static"]["child"] = True
        self.dynamicOptions["static"]["shape"] = "auto"
        self.dynamicOptions["static"]["dynamicsBody"] = "off"
        self.dynamicOptions["static"]["dynamicsLinearDamp"] = 0.0
        self.dynamicOptions["static"]["dynamicsAngularDamp"] = 0.0
        self.dynamicOptions["static"]["massClamp"] = 100.
        self.dynamicOptions["static"]["rotMassClamp"] = 1
        self.dynamicOptions["surface"]={}
        self.dynamicOptions["surface"]["child"] = True
        self.dynamicOptions["surface"]["shape"] = "auto"
        self.dynamicOptions["surface"]["dynamicsBody"] = "off"
        self.dynamicOptions["surface"]["dynamicsLinearDamp"] = 0.0
        self.dynamicOptions["surface"]["dynamicsAngularDamp"] = 0.0
        self.dynamicOptions["surface"]["massClamp"] = 100.
        self.dynamicOptions["surface"]["rotMassClamp"] = 1
                    
    def writeArraysToFile(self, f):
        "write self.gridPtId and self.distToClosestSurf to file"
        pickle.dump(self.grid.gridPtId, f)
        pickle.dump(self.grid.distToClosestSurf, f)

    def readArraysFromFile(self, f):
        "write self.gridPtId and self.distToClosestSurf to file"
        id = pickle.load(f)
        #assert len(id)==len(self.gridPtId)
        self.grid.gridPtId = id

        dist = pickle.load(f)
        #assert len(dist)==len(self.distToClosestSurf)
        self.grid.distToClosestSurf = dist#grid+organelle+surf


    def saveGridToFile(self,gridFileOut):
        f = open(gridFileOut, 'wb')#'w'
        self.writeArraysToFile(f) #save self.gridPtId and self.distToClosestSurf
        
        for organelle in self.organelles:
            organelle.saveGridToFile(f)
        f.close()

    def restoreGridFromFile(self, gridFileName):
        aInteriorGrids = []
        aSurfaceGrids = []
        f = open(gridFileName,'rb')
        self.readArraysFromFile(f) #read gridPtId and distToClosestSurf
        self.BuildGrids()        
#        for organelle in self.organelles:
#            
#            #surfacePoints, insidePoints, normals, srfPtsCoords = organelle.readGridFromFile(f)
#            surfacePoints, insidePoints, normals,surfacePointsCoords = organelle.readGridFromFile(f)
#            aInteriorGrids.append( insidePoints)
#            aSurfaceGrids.append( surfacePoints )
#            
#            srfPts = organelle.ogsurfacePoints = surfacePoints
#            ogNormals = organelle.ogsurfacePointsNormals = normals
#            nbGridPoints = len(self.grid.masterGridPositions)
#
#            length = len(srfPts)
#            
#            pointArrayRaw = numpy.zeros( (nbGridPoints + length, 3), 'f')
#            pointArrayRaw[:nbGridPoints] = self.grid.masterGridPositions
#            pointArrayRaw[nbGridPoints:] = srfPts
#            
#            organelle.surfacePointscoords = srfPts
#            self.grid.nbSurfacePoints += length
#            self.grid.masterGridPositions = pointArrayRaw
#            self.grid.distToClosestSurf.extend( [self.grid.diag]*length )
#            
#            self.grid.gridPtId.extend( [organelle.number]*length )
#            surfacePoints = range(nbGridPoints, nbGridPoints+length)
#            self.grid.freePoints.extend(surfacePoints)
#            
#            organelle.surfacePointsNormals = normals
#            organelle.surfacePoints = surfacePoints
#            organelle.insidePoints = insidePoints
#            organelle.surfacePointsCoords = surfacePointsCoords
#            
#            organelle.computeVolumeAndSetNbMol(self, surfacePoints, insidePoints)
#            print '%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
#                len(organelle.surfacePoints), len(organelle.insidePoints),
#                nbGridPoints, len(self.grid.masterGridPositions))

#        self.grid.aInteriorGrids = aInteriorGrids
#        self.grid.aSurfaceGrids = aSurfaceGrids



##     def getSmallestProteinSize(self, smallest):
##         for organelle in self.organelles:
##             size = organelle.getSmallestProteinSize(smallest)
##             if size < smallest:
##                 smallest = size
##         return smallest

    
##     def getLargestProteinSize(self, largest):
##         for organelle in self.organelles:
##             size = organelle.getLargestProteinSize(largest)
##             if size > largest:
##                 largest = size
##         return largest


    def setMinMaxProteinSize(self):
        for organelle in self.organelles:
            mini, maxi = organelle.getMinMaxProteinSize()
            if mini < self.smallestProteinSize:
                self.computeGridParams = True
                self.smallestProteinSize = mini

            if maxi > self.largestProteinSize:
                self.computeGridParams = True
                self.largestProteinSize = maxi

        if self.exteriorRecipe:
            smallest, largest = self.exteriorRecipe.getMinMaxProteinSize()

            if smallest < self.smallestProteinSize:
                self.smallestProteinSize = smallest

            if largest > self.largestProteinSize:
                self.largestProteinSize = largest

    def extractMeshComponent(self, obj):
        print ("extractMeshComponent",helper.getType(obj))
        if helper is None : 
            print ("no Helper found")            
            return None,None,None
        if helper.getType(obj) == helper.EMPTY: #Organelle master parent?
            childs = helper.getChilds(obj)
            for ch in childs:
                name = helper.getName(ch)
#                print ("childs ",name)
                if helper.getType(ch) == helper.EMPTY:
                    c = helper.getChilds(ch)
                    #should be all polygon
                    faces=[]
                    vertices=[]
                    vnormals=[]
                    for pc in c :
                        f,v,vn = helper.DecomposeMesh(pc,edit=False,
                                                copy=False,tri=True,transform=True)
                        faces.extend(f)
                        vertices.extend(v)
                        vnormals.extend(vn)
                    return vertices, faces, vnormals
                elif helper.getType(ch) == helper.POLYGON :
                    faces,vertices,vnormals = helper.DecomposeMesh(ch,
                                    edit=False,copy=False,tri=True,transform=True)
                    return vertices, faces, vnormals
                else :
                    continue
        elif helper.getType(obj) == helper.POLYGON :
            name = helper.getName(obj)
            #helper.triangulate(c4dorganlle)
#            print ("polygon ",name)
            faces,vertices,vnormals = helper.DecomposeMesh(obj,
                                    edit=False,copy=False,tri=True,transform=True)
#            print ("returning v,f,n",len(vertices))
            return vertices, faces, vnormals
        else :
            print ("extractMeshComponent",helper.getType(obj),helper.POLYGON,
                   helper.getType(obj)==helper.POLYGON)
            return None,None,None
            
    def setOrganelleMesh(self, organelle, ref_obj):
        if organelle.ref_obj == ref_obj : return
        if os.path.isfile(ref_obj):
            fileName, fileExtension = os.path.splitext(ref_obj)            
            if helper is not None:#neeed the helper
#                print ("read withHelper")
                helper.read(ref_obj)
                geom = helper.getObject(fileName)
                #reparent to the fill parent
                #rotate ?
                if helper.host != "c4d" and geom is not None:
                    #need to rotate the transform that carry the shape
                    helper.rotateObj(geom,[0.,-math.pi/2.0,0.0])
        else :
            geom = helper.getObject(ref_obj)
        if geom is not None :
            vertices, faces, vnormals = self.extractMeshComponent(geom)
            organelle.setMesh(filename=ref_obj,vertices=vertices, faces=faces, vnormals=vnormals )
                
    def addOrganelle(self, organelle):
        organelle.setNumber(self.nbOrganelles)
        self.nbOrganelles += 1

        fits, bb = organelle.inBox(self.boundingBox)
        
        if not fits:
            self.boundingBox = bb
        OrganelleList.addOrganelle(self, organelle)

    def longestIngrdientName(self):
        M=20        
        r = self.exteriorRecipe
        if r :
            for ingr in r.ingredients:
                if len(ingr.name) > M :
                    M = len(ingr.name)
        for o in self.organelles:
            rs = o.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    if len(ingr.name) > M :
                        M = len(ingr.name)  
            ri = o.innerRecipe
            if ri :
                for ingr in ri.ingredients:
                    if len(ingr.name) > M :
                        M = len(ingr.name)
        return M

    def loopThroughIngr(self,cb_function):
        r = self.exteriorRecipe
        if r :
            for ingr in r.ingredients:
                cb_function(ingr)
        for o in self.organelles:
            rs = o.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    cb_function(ingr)  
            ri = o.innerRecipe
            if ri :
                for ingr in ri.ingredients:
                    cb_function(ingr)
                    
    def getIngrFromNameInRecipe(self,name,r):
        if r :
            for ingr in r.ingredients:
                if name == ingr.name :
                    return ingr
            for ingr in r.exclude:
                if name == ingr.name :
                    return ingr        
        return None
        
    def getIngrFromName(self,name,compNum=None):
        if compNum == None :
            r = self.exteriorRecipe
            ingr = self.getIngrFromNameInRecipe(name,r)
            if ingr is not None : return ingr
            for o in self.organelles :            
                rs = o.surfaceRecipe
                ingr = self.getIngrFromNameInRecipe(name,rs)
                if ingr is not None : return ingr
                ri = o.innerRecipe
                ingr = self.getIngrFromNameInRecipe(name,ri)
                if ingr is not None : return ingr            
        elif compNum == 0 :
            r = self.exteriorRecipe
            ingr = self.getIngrFromNameInRecipe(name,r)
            if ingr is not None : return ingr
            else : return None
        elif compNum > 0 :
            o=self.organelles[compNum-1]
            rs = o.surfaceRecipe
            ingr = self.getIngrFromNameInRecipe(name,rs)
            if ingr is not None : return ingr
            else : return None
        else : #<0
            o=self.organelles[(compNum*-1)-1]
            ri = o.innerRecipe
            ingr = self.getIngrFromNameInRecipe(name,ri)
            if ingr is not None : return ingr
            else : return None
            
    def setExteriorRecipe(self, recipe):
        assert isinstance(recipe, Recipe)
        self.exteriorRecipe = recipe
        recipe.organelle = weakref.ref(self)
        for ingr in recipe.ingredients:
            ingr.compNum = 0

    def BuildGridsOld(self):
    # FIXME make recursive?
        aInteriorGrids = []
        aSurfaceGrids = []
        if self.EnviroOnly:
           v = self.EnviroOnlyCompartiment #the compartiment number
           if v < 0 and len(self.organelles):
              organelle = self.organelles[abs(v)-1]
              aInteriorGrids, aSurfaceGrids = organelle.BuildGridEnviroOnly(self,v)
           elif  len(self.organelles) :
              organelle = self.organelles[0]
              aInteriorGrids, aSurfaceGrids = organelle.BuildGridEnviroOnly(self,1)
              #aInteriorGrids =[]
              #aSurfaceGrids =[]    
        else :
            for organelle in self.organelles:
                if self.innerGridMethod =="sdf" :
                       a, b = organelle.BuildGrid_utsdf(self)
                elif self.innerGridMethod == "bhtree":
                       a, b = organelle.BuildGrid(self)                
                aInteriorGrids.append( a)
                aSurfaceGrids.append( b )
                
        self.grid.aInteriorGrids = aInteriorGrids
        self.grid.aSurfaceGrids = aSurfaceGrids
        print ("build Grids",self.innerGridMethod,len(self.grid.aSurfaceGrids))

    def BuildGrids(self):  #New version allows for orthogonal box to be used as an organelle requireing no expensive InsidePoints test
        # FIXME make recursive?
        aInteriorGrids = []
        aSurfaceGrids = []
        #    if self.EnviroOnly:
        #        v = self.EnviroOnlyCompartiment #the compartiment number
        #        if v < 0 and len(self.organelles):
        #            organelle = self.organelles[abs(v)-1]
        #            aInteriorGrids, aSurfaceGrids = organelle.BuildGridEnviroOnly(self,v)
        #        elif  len(self.organelles) :
        #            organelle = self.organelles[0]
        #            aInteriorGrids, aSurfaceGrids = organelle.BuildGridEnviroOnly(self,1)
        #    #aInteriorGrids =[]
        #    #aSurfaceGrids =[]
        #    else :
        for organelle in self.organelles:
            print("in HistoVol, organelle.isOrthogonalBoudingBox =", organelle.isOrthogonalBoudingBox)
            b = []
            if organelle.isOrthogonalBoudingBox==1:
                self.EnviroOnly = True
                print(">>>>>>>>>>>>>>>>>>>>>>>>> Not building a grid because I'm an Orthogonal Bounding Box")
                a =self.grid.getPointsInCube(organelle.bb, None, None) #This is the highspeed shortcut for inside points! and no surface! that gets used if the fillSelection is an orthogonal box and there are no other organelles.
                self.grid.gridPtId[a] = -organelle.number
                organelle.surfacePointsCoords = None
                bb0x, bb0y, bb0z = organelle.bb[0]
                bb1x, bb1y, bb1z = organelle.bb[1]
                AreaXplane = (bb1y-bb0y)*(bb1z-bb0z)
                AreaYplane = (bb1x-bb0x)*(bb1z-bb0z)
                AreaZplane = (bb1y-bb0y)*(bb1x-bb0x)
                vSurfaceArea = abs(AreaXplane)*2+abs(AreaYplane)*2+abs(AreaZplane)*2
                print("vSurfaceArea = ", vSurfaceArea)
                organelle.insidePoints = a
                organelle.surfacePoints = b
                organelle.surfacePointsCoords = []
                organelle.surfacePointsNormals = []
                print(' %d inside pts, %d tot grid pts, %d master grid'%( len(a),len(a), len(self.grid.masterGridPositions)))
                organelle.computeVolumeAndSetNbMol(self, b, a,areas=vSurfaceArea)               
                #print("I've built a grid in the organelle test with no surface", a)
                print("The size of the grid I build = ", len(a))

            if self.innerGridMethod =="sdf" and organelle.isOrthogonalBoudingBox!=1: # A fillSelection can now be a mesh too... it can use either of these methods
                a, b = organelle.BuildGrid_utsdf(self) # to make the outer most selection from the master and then the organelle
            elif self.innerGridMethod == "bhtree" and organelle.isOrthogonalBoudingBox!=1:  # surfaces and interiors will be subtracted from it as normal!
                a, b = organelle.BuildGrid(self)
            elif self.innerGridMethod == "jordan" and organelle.isOrthogonalBoudingBox!=1:  # surfaces and interiors will be subtracted from it as normal!
                a, b = organelle.BuildGridJordan(self)
            elif self.innerGridMethod == "jordan3" and organelle.isOrthogonalBoudingBox!=1:  # surfaces and interiors will be subtracted from it as normal!
                a, b = organelle.BuildGridJordan(self,ray=3)
            aInteriorGrids.append(a)
            print("I'm ruther in the loop")
            aSurfaceGrids.append(b)
    
        self.grid.aInteriorGrids = aInteriorGrids
        print("I'm out of the loop and have build my grid with inside points")
        self.grid.aSurfaceGrids = aSurfaceGrids
        print ("build Grids",self.innerGridMethod,len(self.grid.aSurfaceGrids))

    def getPointFrom3D(self, pt3d,bb,spacing,nb):
        """
        get point number from 3d coordinates
        """
        x, y, z = pt3d
        spacing1 = 1./spacing
        NX, NY, NZ = nb
        OX, OY, OZ = bb[0] # origin of fill grid
        i = min( NX-1, max( 0, round((x-OX)*spacing1)))
        j = min( NY-1, max( 0, round((y-OY)*spacing1)))
        k = min( NZ-1, max( 0, round((z-OZ)*spacing1)))
        return int(k*NX*NY + j*NX + i)


    def computeGridNumberOfPoint(self,boundingBox,space):
#        print('bounding box = ', boundingBox)
#        print('space = ', space)
        # compute number of points
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        
        encapsulatingGrid = self.encapsulatingGrid  #Graham Added on Oct17 to allow for truly 2D grid for test fills... may break everything!
        print("If having problems with grids, turn on prints below to make sure encapsulatingGrid is set to 1 unless doing the special 2D test fills!")
        
        from math import ceil
        nx = int(ceil((xr-xl)/space))+encapsulatingGrid
        ny = int(ceil((yr-yl)/space))+encapsulatingGrid
        nz = int(ceil((zr-zl)/space))+encapsulatingGrid
#        print("nx = ", nx)
#        print("ny = ", ny)
#        print("nz = ", nz)
#        print("$$$$$$$$$$$$$   Encapsulating Grid = ", encapsulatingGrid)
        return nx*ny*nz,(nx,ny,nz)
        
#        
#
#        from math import ceil
#        nx = int(ceil((xr-xl)/space))+1
#        ny = int(ceil((yr-yl)/space))+1
#        nz = int(ceil((zr-zl)/space))+1
#        return nx*ny*nz,(nx,ny,nz)

    def buildGrid(self, boundingBox=None, gridFileIn=None, rebuild=True,
                  gridFileOut=None, previousFill=False,previousfreePoint=None):
        
        if hasattr(self,"afviewer") :
            if self.afviewer is not None and hasattr(self.afviewer,"vi"):
                self.afviewer.vi.progressBar(label="Building the Master Grid")
        if boundingBox is None:
            boundingBox = self.boundingBox
        else:
            assert len(boundingBox)==2
            assert len(boundingBox[0])==3
            assert len(boundingBox[1])==3
        # make sure all recipes are sorted from large to small radius
        if self.exteriorRecipe:
            self.exteriorRecipe.sort()

        for o in self.organelles:
            if o.innerRecipe:
                o.innerRecipe.sort()
            if o.surfaceRecipe:
                o.surfaceRecipe.sort()

        if hasattr(self,"afviewer"):
            if self.afviewer is not None and hasattr(self.afviewer,"vi"):
                self.afviewer.vi.progressBar(label="Computing the number of grid points")
        if rebuild :
            # save bb for current fill
            self.fillBB = boundingBox
            grid = Grid()
            self.grid = grid
            grid.boundingBox = boundingBox
            # compute grid spacing
            grid.gridSpacing = space = self.smallestProteinSize*1.1547  # 2/sqrt(3)
            print ("$$$$$$$$  ",boundingBox,space,self.smallestProteinSize)
            grid.gridVolume,grid.nbGridPoints = self.callFunction(self.computeGridNumberOfPoint,(boundingBox,space))
        grid =self.grid
        nbPoints = self.grid.gridVolume
        print("$$$$$$$$  gridVolume = nbPoints = ", nbPoints, " grid.nbGridPoints = ", self.grid.nbGridPoints)
        # compute 3D point coordiantes for all grid points
        if rebuild :
            self.callFunction(grid.create3DPointLookup) #generate grid.masterGridPositions 
#            print('grid size', grid.nbGridPoints)
            grid.nbSurfacePoints = 0
            #self.isFree = numpy.ones( (nbPoints,), 'i') # Will never shrink
#            print('nb freePoints', nbPoints)#-1)
            # Id is set set to None initially
            grid.gridPtId = numpy.zeros(nbPoints)#[0]*nbPoints

        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
        self.grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
        self.grid.distToClosestSurf = [diag]*nbPoints#surface point too?
        self.grid.freePoints = list(range(nbPoints))
        #print 'DIAG', diag
        
#        if gridFileIn is None :
#            gridFileIn = self.grid_filename
#        if gridFileOut is None :
#            gridFileOut= self.grid_filename
#        if self.grid_filename is not None and not os.path.isfile(self.grid_filename):
#            gridFileIn = None

#        if rebuild :
            #this restore/store the grid information of the organelle.
        if gridFileIn is not None :
            self.grid.filename = gridFileIn
            self.restoreGridFromFile(gridFileIn)
        else:
            # assign ids to grid points
            self.BuildGrids()
        if gridFileOut is not None:
            self.saveGridToFile(gridFileOut)
            self.grid.filename = gridFileOut
        # get new set of freePoints which includes surface points
 #       nbPoints = nbPoints-1			#Graham Turned off this redundant nbPoints-1 call on 8/27/11
 #       nbPoints = nbPoints-1          #Graham Turned this one off on 5/16/12 to match August repair in Hybrid
        grid.nbFreePoints = nbPoints#-1
        grdPts = grid.masterGridPositions
        # build BHTree for surface points (off grid)
        if rebuild :
            verts = []            
            for orga in self.organelles:
                if orga.surfacePointsCoords:
                    for pt3d in orga.surfacePointsCoords:
                        verts.append( pt3d )
    
            from bhtree import bhtreelib
            grid.surfPtsBht = None
            if verts :
               grid.surfPtsBht = bhtreelib.BHtree( verts, None, 10)
           
        # build list of compartments without a recipe
        noRecipe = []
        if self.exteriorRecipe is None:
            noRecipe.append( 0 )
        for o in self.organelles:
            if o.surfaceRecipe is None:
                noRecipe.append( o.number )
            if o.innerRecipe is None:
                noRecipe.append( -o.number )

        # compute exterior volume 
        unitVol = grid.gridSpacing**3
        totalVolume = grid.gridVolume*unitVol
        if self.fbox_bb is not None :
                V,nbG = self.callFunction(self.computeGridNumberOfPoint,(self.fbox_bb,space))
                totalVolume = V*unitVol
        for o in self.organelles:
            #totalVolume -= o.surfaceVolume
            totalVolume -= o.interiorVolume
        self.exteriorVolume = totalVolume

        r = self.exteriorRecipe
        if r:
            r.setCount(totalVolume)#should actually use the fillBB
            
        if self.use_gradient and len(self.gradients):
            for g in self.gradients:
                self.gradients[g].buildWeigthMap(boundingBox,grid.masterGridPositions)
            
        #we should be able here to update the number of free point using a previous grid 
        #overlap
#        print("previousFill",previousFill)
        if previousFill:#actually if there is a previous fill
            #get the intersecting point and update freePoints from this one if they are not free
            #previousfreePoint
            #compute the intersection bounding box and get ptindice for both grid 
            #by getPointsInCube
            #check which one are in freePoints from previous, and update the current one
            #update the curentpass
#            #how to update the distance for each prest ingr ?
            distance = self.grid.distToClosestSurf#[:]
#            nbFreePoints = nbPoints-1				#This already comes from the Point Volume- no subtraction needed (Graham turned off on 8/27/11)
            nbFreePoints = nbPoints#-1              #Graham turned this off on 5/16/12 to match August Repair for May Hybrid
            molecules=self.molecules
#            print("molecules",molecules)
            for organelle in self.organelles:
                molecules.extend(organelle.molecules)
            for i,mingrs in enumerate(molecules) :#( jtrans, rotMatj, self, ptInd )
                jtrans, rotMatj, ingr, ptInd = mingrs
#                print ("OK",jtrans, rotMatj, ingr, ptInd)
                centT = ingr.transformPoints(jtrans, rotMatj, ingr.positions[-1])
                insidePoints = {}
                newDistPoints = {}
                mr = self.get_dpad(ingr.compNum)
                spacing = self.smallestProteinSize
                jitter = ingr.getMaxJitter(spacing)
                dpad = ingr.minRadius + mr + jitter
                insidePoints,newDistPoints = ingr.getInsidePoints(self.grid,
                                    self.grid.masterGridPositions,dpad,distance,
                                    centT=centT,
                                    jtrans=jtrans, 
                                    rotMatj=rotMatj)
                # update free points
                if len(insidePoints) and self.placeMethod.find("panda") != -1:
                	   print (ingr.name," is inside")
                	   self.checkPtIndIngr(ingr,insidePoints,i,ptInd)
                	   #ingr.inside_current_grid = True
                else  :
                    #not in the grid
                    print (ingr.name," is outside")
                    rbnode = ingr.rbnode[ptInd]
                    ingr.rbnode.pop(ptInd)
                    self.molecules[i][3]=-1
                    ingr.rbnode[-1] = rbnode
                #(self, histoVol,insidePoints, newDistPoints, freePoints,
                #        nbFreePoints, distance, masterGridPositions, verbose)
                nbFreePoints = ingr.updateDistances(self,insidePoints, newDistPoints, 
                            self.grid.freePoints, nbFreePoints, distance, 
                            self.grid.masterGridPositions,0)
            self.grid.nbFreePoints = nbFreePoints
        #self.hgrid.append(self.grid)
        self.setCompatibility()

    def checkPtIndIngr(self,ingr,insidePoints,i,ptInd):
    	#change key for rbnode too
    	rbnode = ingr.rbnode[ptInd]
    	ingr.rbnode.pop(ptInd)
        if i < len(self.molecules):
            self.molecules[i][3]=insidePoints.keys()[0]
            ingr.rbnode[insidePoints.keys()[0]] = rbnode
        else :
            nmol = len(self.molecules)
            for j,organelle in enumerate(self.organelles):
            	print (i,nmol+len(organelle.molecules))
                if i < nmol+len(organelle.molecules):
                    organelle.molecules[i-nmol][3]=insidePoints.keys()[0]
                    ingr.rbnode[insidePoints.keys()[0]] = rbnode
                else :
                    nmol+=len(organelle.molecules)
			
    def setCompatibility(self):
        self.getPointsInCube = self.grid.getPointsInCube
        self.boundingBox=self.grid.boundingBox
        self.gridPtId = self.grid.gridPtId
        self.freePoints = self.grid.freePoints
        self.diag=self.grid.diag
        self.gridSpacing = self.grid.gridSpacing
        self.nbGridPoints = self.grid.nbGridPoints
        self.nbSurfacePoints = self.grid.nbSurfacePoints
        self.gridVolume = self.grid.gridVolume # will be the toatl number of grid points
        self.masterGridPositions = self.grid.masterGridPositions
        self.aInteriorGrids = self.grid.aInteriorGrids
        self.aSurfaceGrids = self.grid.aSurfaceGrids
        self.surfPtsBht=self.grid.surfPtsBht
        self.gridPtId = self.grid.gridPtId = numpy.array(self.grid.gridPtId,int)
        
    def getSortedActiveIngredients(self, allIngredients, verbose=0):
        # first get the ones with a packing priority
        # Graham- This now works in concert with ingredient picking
        
        # Graham here- In the new setup, priority is infinite with abs[priority] increasing (+)
        # An ingredients with (-) priority will pack from greatest abs[-priority] one at a time
        #     to lease abs[-priority]... each ingredient will attempt to reach its molarity
        #     before moving on to the next ingredient, and all (-) ingredients will try to
        #     deposit before other ingredients are tested.
        # An ingredient with (+) priority will recieve a weighted value based on its abs[priority]
        #     e.g. an ingredient with a priority=10 will be 10x more likely to be picked than
        #     an ingredient with a priority=1.
        # An ingredient with the default priority=0 will recieve a weighted value based on its
        #     complexity. (currently complexity = minRadius), thus a more 'complex' ingredient
        #     will more likely try to pack before a less 'complex' ingredient.
        #     IMPORTANT: the +priority list does not fully mix with the priority=0 list, but this
        #     should be an option... currently, the priority=0 list is normalized against a range
        #     up to the smallest +priority ingredient and appended to the (+) list
        # TODO: Add an option to allow + ingredients to be weighted by assigned priority AND complexity
        #     Add an option to allow priority=0 ingredients to fit into the (+) ingredient list
        #       rather than appending to the end.
        #     Even better, add an option to set the max priority for the 0list and then plug the results
        #       into the (+) ingredient list.
        #     Get rid of the (-), 0, (+) system and recreate this as a new flag and a class function
        #        so we can add multiple styles of sorting and weighting systems.
        #     Make normalizedPriorities and thresholdPriorities members of Ingredient class to avoid
        #        building these arrays.
           
        ingr1 = []  # given priorities
        priorities1 = []
        ingr2 = []  # priority = 0 or none and will be assigned based on complexity
        priorities2 = []
        ingr0 = []  # negative values will pack first in order of abs[packingPriority]
        priorities0 = []
        for ing in allIngredients:
            if ing.completion >= 1.0: continue # ignore completed ingredients
            if ing.packingPriority is None or ing.packingPriority == 0 :
                ingr2.append(ing)
                priorities2.append(ing.packingPriority)
            elif ing.packingPriority > 0 :
                ingr1.append(ing)
                priorities1.append(ing.packingPriority)
            else:
                #ing.packingPriority    = -ing.packingPriority    
                ingr0.append(ing)
                priorities0.append(ing.packingPriority)

        if self.pickWeightedIngr:            
    #Graham here on 5/16/12. Double check that this new version is correct- it uses a very different function than the working September version from 2011
            #sorted(ingr1, key=attrgetter('packingPriority', 'minRadius','completion'), reverse=True)
            #ingr1.sort(key=ingredient_compare1)  #Fails 5/21/12
            if sys.version < "3.0.0" :
                ingr1.sort(ingredient_compare1)
                # sort ingredients with no priority based on radius and completion
                #sorted(ingr2, key=attrgetter('packingPriority', 'minRadius','completion'), reverse=True)
                #ingr2.sort(key=ingredient_compare2)  #Fails 5/21/12
                ingr2.sort(ingredient_compare2)
                #sorted(ingr0, key=attrgetter('packingPriority', 'minRadius','completion'), reverse=True)
                #ingr0.sort(key=ingredient_compare0)
                ingr0.sort(ingredient_compare0)  #Fails 5/21/12
    #            ingr0.sort()
            else :
                try :
                    ingr1.sort(key=ingredient_compare1)
                    ingr2.sort(key=ingredient_compare2)
                    ingr0.sort(key=ingredient_compare0)
                except :
                    print ("ATTENTION INGR NOT SORTED")
        #for ing in ingr3 : ing.packingPriority    = -ing.packingPriority
        #GrahamAdded this stuff in summer 2011, beware!
        if len(ingr1) != 0:
            lowestIng = ingr1[len(ingr1)-1]
            self.lowestPriority = lowestIng.packingPriority
        else :
            self.lowestPriority = 1.
        if verbose:
            print('self.lowestPriority for Ing1 = ', self.lowestPriority)
        self.totalRadii = 0
        for radii in ingr2:
            if radii.modelType=='Cylinders':
                r = max(radii.length/2.,radii.minRadius)
            elif radii.modelType=='Spheres':
                r = radii.minRadius
            elif radii.modelType=='Cube':
                r = radii.minRadius
            self.totalRadii = self.totalRadii + r
            if verbose:
                print('self.totalRadii += ', r, "=",self.totalRadii)
            if r==0 : 
                print (radii,radii.name)
                #safety 
                self.totalRadii = self.totalRadii + 1.0
            
        self.normalizedPriorities0 = []
        for priors2 in ingr2:
            if priors2.modelType=='Cylinders':
                r = max(priors2.length/2.,priors2.minRadius)
            elif priors2.modelType=='Spheres':
                r = priors2.minRadius            
            np = float(r)/float(self.totalRadii) * self.lowestPriority
            self.normalizedPriorities0.append(np)
            priors2.packingPriority = np
            if verbose:
                print('self.normalizedPriorities0 = ', self.normalizedPriorities0)
        activeIngr0 = ingr0#+ingr1+ingr2  #cropped to 0 on 7/20/10
        
        if verbose:
            print('len(activeIngr0)', len(activeIngr0))
        activeIngr12 = ingr1+ingr2
        if verbose:
            print('len(activeIngr12)', len(activeIngr12))
        packingPriorities = priorities0+priorities1+priorities2
        if verbose:
            print('priorities0 is ', priorities0)
            print('priorities1 is ', priorities1)
            print('priorities2 is ', priorities2)
            print('packingPriorities', packingPriorities)

#        if verbose>0:
#            print 'Ingredients:'
#            for i, ingr in enumerate(activeIngr):
#                packPri = ingr.packingPriority
#                if packPri is None:
#                    packPri = -1
#                print '  comp:%2d #:%3d pri:%3d compl:%.2f mRad:%5.1f t:%4d n:%4d '%(
#                    ingr.compNum, i, packPri, ingr.completion, ingr.minRadius,
#                    ingr.nbMol, ingr.counter)
#            raw_input("hit enter")

        return activeIngr0, activeIngr12

#    import fill3isolated # Graham cut the outdated fill3 from this document and put it in a separate file. turn on here if you want to use it.
            
    def updateIngr(self,ingr,completion=0.0,nbMol=0,counter=0):
        ingr.counter = counter
        ingr.nbMol = nbMol
        ingr.completion = completion

    def reset(self):
        self.fbox_bb = None
        self.totnbJitter = 0
        self.jitterLength = 0.0
        r =  self.exteriorRecipe
        self.resetIngrRecip(r)
        self.molecules=[]
        for orga in self.organelles:
            orga.reset()
            rs =  orga.surfaceRecipe
            self.resetIngrRecip(rs)
            ri =  orga.innerRecipe
            self.resetIngrRecip(ri)
#            print "ok reset"
#        from bhtree import bhtreelib    
#        bhtreelib.freeBHtree(self.grid.surfPtsBht)
#        self.hgrid.pop(self.hgrid.index(self.grid))
#        del self.grid

        self.ingr_result = {}
        if self.world is not None :
            #need to clear all node
            nodes = self.rb_panda[:]
            for node in nodes:
                self.delRB(node)
            self.static = []
            self.moving = None
        #the reset doesnt touch the grid...
            
    def resetIngrRecip(self,recip):
        if recip:            
            for ingr in recip.ingredients:
                ingr.results=[]
                ingr.firstTimeUpdate = True
                ingr.counter = 0
                ingr.rejectionCounter = 0
                ingr.completion= 0.0
                if hasattr(ingr,"allIngrPts"):  #Graham here on 5/16/12 are these two lines safe?
                    del ingr.allIngrPts         #Graham here on 5/16/12 are these two lines safe?
                if hasattr(ingr,"isph"):  
                    ingr.isph = None
                if hasattr(ingr,"icyl"):  
                    ingr.icyl = None
                if hasattr(ingr,"allIngrPts"):
                    delattr(ingr, "allIngrPts")
            for ingr in recip.exclude:
                ingr.results=[]
                ingr.firstTimeUpdate = True
                ingr.counter = 0
                ingr.rejectionCounter = 0
                ingr.completion= 0.0
                if hasattr(ingr,"allIngrPts"):  #Graham here on 5/16/12 are these two lines safe?
                    del ingr.allIngrPts           
                if hasattr(ingr,"isph"):  
                    ingr.isph = None    
                if hasattr(ingr,"icyl"):  
                    ingr.icyl = None
                if hasattr(ingr,"allIngrPts"):
                    delattr(ingr, "allIngrPts")
                    
    def resetIngr(self,ingr):
        ingr.counter = 0
        ingr.nbMol = 0
        ingr.completion = 0.0

    def getActiveIng(self):
        allIngredients = []
        r = self.exteriorRecipe
        if r is not None:
            if not hasattr(r,"molecules") :
                r.molecules = []
        if r:
            for ingr in r.ingredients:
                ingr.counter = 0 # counter of placed molecules
                if  ingr.nbMol > 0:
                    ingr.completion = 0.0
                    allIngredients.append(ingr)
                else:
                    ingr.completion = 1.0
            
        for o in self.organelles:
            if not hasattr(o,"molecules") :
                o.molecules = []
            r = o.surfaceRecipe
            if r:
                for ingr in r.ingredients:
                    ingr.counter = 0 # counter of placed molecules
                    if  ingr.nbMol > 0:
                        ingr.completion = 0.0
                        allIngredients.append(ingr)
                    else:
                        ingr.completion = 1.0

            r = o.innerRecipe
            if r:
                for ingr in r.ingredients:
                    ingr.counter = 0 # counter of placed molecules
#                    print "nbMol",ingr.nbMol
                    if  ingr.nbMol > 0:
                        ingr.completion = 0.0
                        allIngredients.append(ingr)
                    else:
                        ingr.completion = 1.0
        return allIngredients

    def pickIngredient(self,vThreshStart, verbose=0):
        #if verbose:
        #    print "unsorted",self.pickWeightedIngr,not self.pickWeightedIngr
        if self.pickWeightedIngr : 
            if self.thresholdPriorities[0] == 2 :
                # Graham here: Walk through -priorities first
                ingr = self.activeIngr[0]
            else:
                #prob = uniform(vRangeStart,1.0)  #Graham 9/21/11 This is wrong...vRangeStart is the point index, need active list i.e. thresholdPriority to be limited
                prob = uniform(0,1.0)
                ingrInd = 0
                for threshProb in self.thresholdPriorities:
                    if prob <= threshProb:
                        break
                    ingrInd = ingrInd + 1
                if ingrInd <  len(self.activeIngr):
                    ingr = self.activeIngr[ingrInd]
                else :
                    print("error in histoVol pick Ingredient",ingrInd)
                    ingr = self.activeIngr[0]
                if verbose:
                    print ('weighted',prob, vThreshStart, ingrInd,ingr.name)
        else :
            #if verbose:
            #    print "random in activeIngr"
            r = random()#randint(0, len(self.activeIngr)-1)#random()
            #n=int(r*(len(self.activeIngr)-1))
            n=int(r*len(self.activeIngr))
            ingr = self.activeIngr[n]
#            print (r,n,ingr.name,len(self.activeIngr)) #Graham turned back on 5/16/12, but may be costly
        return ingr

    def get_dpad(self,compNum):
        mr = 0.0
        if compNum==0: # cytoplasm -> use cyto and all surfaces
            for ingr1 in self.activeIngr:
                if ingr1.compNum>=0:
                    r = ingr1.encapsulatingRadius
                    if r>mr:
                        mr = r
        else:
            for ingr1 in self.activeIngr:
                if ingr1.compNum==compNum or ingr1.compNum==-compNum:
                    r = ingr1.encapsulatingRadius
                    if r>mr:
                        mr = r
        return mr

    def checkIfUpdate(self,ingr,nbFreePoints,verbose=False):
        #compare size of ingrediant related to nbFreePts
        if hasattr(ingr,"nbPts"):
            if hasattr(ingr,"firstTimeUpdate") and not ingr.firstTimeUpdate:
                ratio = float(ingr.nbPts)/float(nbFreePoints)
#                print('freePtsUpdateThrehod = ', self.freePtsUpdateThrehod)
                if verbose:
                    print("checkIfUpdate: ratio = ",ratio,"nbFreePoints = ", nbFreePoints, "ingr.nbPts = ",ingr.nbPts)
                if ratio > self.freePtsUpdateThrehod :
                    return True
                else :
                    if ingr.haveBeenRejected and ingr.rejectionCounter > 5:
                        ingr.haveBeenRejected = False
                        return True
                    #do we check to total freepts? or crowded state ?
                    else :
                        return False
            else :
                ingr.firstTimeUpdate = False
                return True
        else :
            return True


    def getPointToDrop(self,ingr,radius,jitter,freePoints,nbFreePoints,distance,
                       compId,compNum,vRangeStart,vThreshStart, verbose=False):
        #should we take in account a layer? cuttof_boundary and cutoff_surface?
        verbose = False
        if ingr.packingMode=='close':
            t1 = time()
            allIngrPts = []
            allIngrDist = []
            if ingr.modelType=='Cylinders' and ingr.useLength :
                cut = ingr.length-jitter
#            if ingr.modelType=='Cube' : #radius iactually the size
#                cut = min(self.radii[0]/2.)-jitter
            elif ingr.cutoff_boundary is not None :
                cut  = radius+ingr.cutoff_boundary-jitter
            else :
                cut  = radius-jitter
            for pt in freePoints:#[:nbFreePoints]:
                d = distance[pt]#look up the distance
                if compId[pt]==compNum and d>=cut:
                    allIngrPts.append(pt)
                    allIngrDist.append(d)
            if verbose:
                print("time to filter using for loop ", time()-t1)
        else:
            t1 = time()
            allIngrPts = []
#            print("allIngrPts = ", allIngrPts)
#            print("len (allIngrPts) = ", len(allIngrPts))
            if ingr.modelType=='Cylinders' and ingr.useLength :
                cut = ingr.length-jitter
            elif ingr.cutoff_boundary is not None :
                cut  = radius+ingr.cutoff_boundary-jitter                
            else :
                cut  = radius-jitter
            #for pt in freePoints[:nbFreePoints]:
            if hasattr(ingr,"allIngrPts") and self._hackFreepts:
                allIngrPts = ingr.allIngrPts
#                print("hasattr(ingr,allIngrPts)")
#                print ("Running nofreepoint HACK")
            else :
                #use periodic update according size ration grid
                update = self.checkIfUpdate(ingr,nbFreePoints)
#                print("in update else")
#                print "update ", update,nbFreePoints,hasattr(ingr,"allIngrPts"),cut
                if update :
#                    print("in update loop")
                    for i in range(nbFreePoints):
#                        print("in i range of update loop")
                        pt = freePoints[i]
                        d = distance[pt]
                        if compId[pt]==compNum and d>=cut:
#                            print("in update for/if")
#                            print pt,compId[pt], d,cut,compNum
                            allIngrPts.append(pt)
                    #allIngrDist.append(d)
                    ingr.allIngrPts = allIngrPts
                    ingr.cut = cut
#                    if verbose:
#                    print("getPointToDrop len(allIngrPts) = ", len(allIngrPts))
                else :
                    if hasattr(ingr,"allIngrPts"):
#                        print("allIngrPts = ingr.allIngrPts two elses deep")
                        allIngrPts = ingr.allIngrPts
                    else :    #Graham Here on 5/16/12, double check that this is safe as its not in the September version
                        allIngrPts = freePoints[:nbFreePoints]
                        ingr.allIngrPts = allIngrPts
#                        print("in the last else")
#                        print('freepoint routine here may be unsafe, not in old version, so doublecheck')
                        #compltly unsafe due to surface points !!!
#        print(("time to filter ",nbFreePoints," using lambda ", time()-t1))
        # no point left capable of accomodating this ingredient
#        print("allIngrPts = ", allIngrPts)
#        print("len (allIngrPts) = ", len(allIngrPts))
        if len(allIngrPts)==0:
            t=time()
#            print('No point left for ingredient %s %f minRad %.2f jitter %.3f in component %d'%(
#                ingr.name, ingr.molarity, radius, jitter, compNum))
            ingr.completion = 1.0
            ind = self.activeIngr.index(ingr)
            #if ind == 0:
            vRangeStart = vRangeStart + self.normalizedPriorities[0]
            if ind > 0:
                #j = 0
                for j in range(ind):                
                    self.thresholdPriorities[j] = self.thresholdPriorities[j] + self.normalizedPriorities[ind]
            self.activeIngr.pop(ind)
# Start of massive overruling section from corrected thesis file of Sept. 25, 2012
            #this function also depend on the ingr.completiion that can be restored ?
            self.activeIngr0, self.activeIngr12 = self.callFunction(self.getSortedActiveIngredients, (self.activeIngr,False))
            if verbose:
                print ('len(allIngredients', len(self.activeIngr))
                print ('len(self.activeIngr0)', len(self.activeIngr0))
                print ('len(self.activeIngr12)', len(self.activeIngr12))
            self.activeIngre_saved = self.activeIngr[:]

            self.totalPriorities = 0 # 0.00001
            for priors in self.activeIngr12:
                pp = priors.packingPriority
                self.totalPriorities = self.totalPriorities + pp
                if verbose :
                    print ('totalPriorities = ', self.totalPriorities)
            previousThresh = 0
            self.normalizedPriorities = []
            self.thresholdPriorities = [] 
            # Graham- Once negatives are used, if picked random# 
            # is below a number in this list, that item becomes 
            #the active ingredient in the while loop below
            for priors in self.activeIngr0:
                self.normalizedPriorities.append(0)
                if self.pickWeightedIngr :
                    self.thresholdPriorities.append(2)
            for priors in self.activeIngr12:
                #pp1 = 0
                pp = priors.packingPriority
                if self.totalPriorities != 0:
                    np = float(pp)/float(self.totalPriorities)
                else:
                    np=0.
                self.normalizedPriorities.append(np)
                if verbose :
                    print ('np is ', np, ' pp is ', pp, ' tp is ', np + previousThresh)
                self.thresholdPriorities.append(np + previousThresh)
                previousThresh = np + float(previousThresh)
            self.activeIngr = self.activeIngr0 + self.activeIngr12
            
            nls=0
            totalNumMols = 0
            for threshProb in self.thresholdPriorities:
                nameMe = self.activeIngr[nls]
                if verbose:
                    print ('threshprop is %f for ingredient: %s %s %d'%(threshProb, nameMe,nameMe.name,nameMe.nbMol))
                totalNumMols += nameMe.nbMol
                if verbose:
                    print ('totalNumMols = ', totalNumMols)
                nls+=1

            #print 'vThreshStart before = ', vThreshStart
            #vThreshStart = self.thresholdPriorities[0]
            #print 'vThreshStart after = ', vThreshStart
            #print 'because vself.thresholdPriorities[0] = ', self.thresholdPriorities[0]

            #self.thresholdPriorities.pop(ind)
            #self.normalizedPriorities.pop(ind)
            if verbose:
                print ("time to reject the picking", time()-t)
# End of massive overruling section from corrected thesis file of Sept. 25, 2011
# this chunk overwrites the next three lines from July version. July 5, 2012
#            self.thresholdPriorities.pop(ind)					
#            self.normalizedPriorities.pop(ind)
#            print(("time to reject the picking", time()-t))
            return False,vRangeStart
#        ptInd = allIngrPts[0]       #turned this off when I imported the large overrulling 
# code from Sept 25 2011 thesis version on July 5, 2012
        if self.pickRandPt:
            t2=time()
            if ingr.packingMode=='close':
                order = numpy.argsort(allIngrDist)
                # pick point with closest distance
                ptInd = allIngrPts[order[0]]
            elif ingr.packingMode=='gradient' and self.use_gradient:  
                #get the most probable point using the gradient                
                #use the gradient weighted map and get mot probabl point
                ptInd = self.gradients[ingr.gradient].pickPoint(allIngrPts) 
            else:
                # pick a point randomly among free points
                ptIndr = int(random()*len(allIngrPts))
                ptInd = allIngrPts[ptIndr]            
            if ptInd is None :
                t=time()
                if verbose:
                    print('No point left for ingredient %s %f minRad %.2f jitter %.3f in component %d'%(
                    ingr.name, ingr.molarity, radius, jitter, compNum))
                ingr.completion = 1.0
                ind = self.activeIngr.index(ingr)
                #if ind == 0:
                vRangeStart = vRangeStart + self.normalizedPriorities[0]
                if ind > 0:
                    #j = 0
                    for j in range(ind):                
                        self.thresholdPriorities[j] = self.thresholdPriorities[j] + self.normalizedPriorities[ind]
                self.activeIngr.pop(ind)
                if verbose:
                    print('popping this gradient ingredient array must be redone using Sept 25, 2011 thesis version as above for nongraient ingredients, TODO: July 5, 2012')
                self.thresholdPriorities.pop(ind)
                self.normalizedPriorities.pop(ind)
                if verbose:
                        print(("time to reject the picking", time()-t))
                return False,vRangeStart                    

#            print(("time to random pick a point", time()-t2))
        else :
            t3=time()
            allIngrPts.sort()
            ptInd = allIngrPts[0]
#            print(("time to sort and pick a point", time()-t3))
        return True,ptInd

#    import fill4isolated # Graham cut the outdated fill4 from this document and put it in a separate file. turn on here if you want to use it.
    def removeOnePoint(self, pt,freePoints,nbFreePoints):
        try :
                # New system replaced by Graham on Aug 18, 2012
                nbFreePoints -= 1  
                vKill = freePoints[pt]
                vLastFree = freePoints[nbFreePoints]
                freePoints[vKill] = vLastFree
                freePoints[vLastFree] = vKill
                # End New replaced by Graham on Aug 18, 2012
        except:
				pass
        return nbFreePoints
    
    def fill5(self, seedNum=14, stepByStep=False, verbose=False, sphGeom=None,
              labDistGeom=None, debugFunc=None,name = None, vTestid = 3,vAnalysis = 0,**kw):
        ## Fill the grid by picking an ingredient first and then
        ## this filling should be able to continue from a previous one
        ## find a suitable point suing hte ingredient's placer object
        import time
        t1=time.time()
        self.timeUpDistLoopTotal = 0 #Graham added to try to make universal "global variable Verbose" on Aug 28

        if self.grid is None:
            print("no grid setup")
            return
        # create a list of active ingredients indices in all recipes to allow
        # removing inactive ingredients when molarity is reached
        allIngredients = self.callFunction(self.getActiveIng)

        nbIngredients = len(allIngredients)
        self.cFill = self.nFill
        if name == None :
            name = "F"+str(self.nFill)
        self.FillName.append(name)
        self.nFill+=1
        # seed random number generator
        seed(seedNum)
        self.randomRot.setSeed(seed=seedNum)
        # create copies of the distance array as they change when molecules
        # are added, theses array can be restored/saved before feeling
        freePoints = self.grid.freePoints[:]
        nbFreePoints = len(freePoints)#-1
#        self.freePointMask = numpy.ones(nbFreePoints,dtype="int32")
        if "fbox" in kw :  # Oct 20, 2012  This is part of the code that is breaking the grids for all meshless organelle fills
            self.fbox = kw["fbox"]
        if self.fbox is not None and not self.EnviroOnly :
            self.freePointMask = numpy.ones(nbFreePoints,dtype="int32")
            bb_insidepoint = self.grid.getPointsInCube(self.fbox, [0,0,0], 1.0)[:]#center and radius ?3,runTime=self.runTimeDisplay
            self.freePointMask[bb_insidepoint]=0
            bb_outside = numpy.nonzero(self.freePointMask)
            self.grid.gridPtId[bb_outside] = 99999
        compId = self.grid.gridPtId
        #why a copy? --> can we split ?
        distance = self.grid.distToClosestSurf[:]

        spacing = self.smallestProteinSize

        # DEBUG stuff, should be removed later
        self.jitterVectors = []
        self.jitterLength = 0.0
        self.totnbJitter = 0
        self.maxColl = 0.0
        self.successfullJitter = []
        self.failedJitter = []
        
        #this function also depend on the ingr.completiion that can be restored ?
        self.activeIngr0, self.activeIngr12 = self.callFunction(self.getSortedActiveIngredients, (allIngredients,verbose))

        print('len(allIngredients', len(allIngredients))
        print('len(self.activeIngr0)', len(self.activeIngr0))
        print('len(self.activeIngr12)', len(self.activeIngr12))
        self.activeIngre_saved = self.activeIngr[:]

        self.totalPriorities = 0 # 0.00001
        for priors in self.activeIngr12:
            pp = priors.packingPriority
            self.totalPriorities = self.totalPriorities + pp
            print('totalPriorities = ', self.totalPriorities)
        previousThresh = 0
        self.normalizedPriorities = []
        self.thresholdPriorities = [] 
        # Graham- Once negatives are used, if picked random# 
        # is below a number in this list, that item becomes 
        # the active ingredient in the while loop below
        for priors in self.activeIngr0:
            self.normalizedPriorities.append(0)
            if self.pickWeightedIngr :#why ?
                self.thresholdPriorities.append(2)
        for priors in self.activeIngr12:
            #pp1 = 0
            pp = priors.packingPriority
            if self.totalPriorities != 0:
                np = float(pp)/float(self.totalPriorities)
            else:
                np=0.
            self.normalizedPriorities.append(np)
            print('np is ', np, ' pp is ', pp, ' tp is ', np + previousThresh)
            self.thresholdPriorities.append(np + previousThresh)
            previousThresh = np + float(previousThresh)
        self.activeIngr = self.activeIngr0 + self.activeIngr12

        nls=0
        totalNumMols = 0
        if len(self.thresholdPriorities ) == 0:
            for ingr in allIngredients:
                totalNumMols += ingr.nbMol
            print('totalNumMols = ', totalNumMols)
        else :                
            for threshProb in self.thresholdPriorities:
                nameMe = self.activeIngr[nls]
                print('threshprop is %f for ingredient: %s %s %d'%(threshProb, nameMe,nameMe.name,nameMe.nbMol))
                totalNumMols += nameMe.nbMol
                print('totalNumMols = ', totalNumMols)
                nls+=1
            
        vRangeStart = 0.0
        tCancelPrev=time.time()
        test = True
        kk=0
        ptInd = 0

        PlacedMols = 0
        vThreshStart = 0.0   # Added back by Graham on July 5, 2012 from Sept 25, 2011 thesis version
#==============================================================================
#         #the big loop
#==============================================================================
        while nbFreePoints:
#            print (".........At start of while loop, with vRangeStart = ", vRangeStart)
#            for o in self.organelles:
#                print ("organelles = ", o.name)
#            print("freePoints = ", freePoints, "nbFreePoints = ", nbFreePoints)
            if verbose > 1:
                print('Points Remaining', nbFreePoints, id(freePoints))
                print('len(self.activeIngr)', len(self.activeIngr))                
            
            #breakin test
            if len(self.activeIngr)==0:
                print('broken by len****')
                if hasattr(self,"afviewer"):
                    if self.afviewer is not None and hasattr(self.afviewer,"vi"):
                        self.afviewer.vi.resetProgressBar()
                        self.afviewer.vi.progressBar(label="Filling Complete")       
                break
            if vRangeStart>1:
                print('broken by vRange and hence Done!!!****')
                break   
            if self.cancelDialog :
                tCancel = time.time()
                if tCancel-tCancelPrev > 10.:
                    cancel=self.displayCancelDialog()
                    if cancel:
                        print("canceled by user: we'll fill with current objects up to time", tCancel)
                        break
                    #if OK, do nothing, i.e., continue loop (but not the function continue)
                    tCancelPrev= time.time()
            ## pick an ingredient
            
            ingr =  self.callFunction(self.pickIngredient,(vThreshStart,))
            #if ingr.completion >= 1.0 or ingr.is_previous:
            #    continue
#            ingr =  self.callFunction(self.pickIngredient,(vRangeStart,))   # Replaced this with previous line from Sept 25, 2011 thesis version on July 5, 2012
            if hasattr(self,"afviewer"):
                # C4D safety check added by Graham on July 10, 2012 until we can fix the uPy status bar for C4D
                #if self.host == 'c4d':
                    try :
                        import c4d
        #               Start working chunk pasted in by Graham from Sept 2011 on 5/16/12- Resorting to this because it fixes the status bar- must be a uPy problem?
        #               -Ludo: we need to use the helpr for that
        #               -Graham: The helper progressBar is broken at least for C4D
        #                   The self.afviewer.vi.progressBar(progress=int(p),label=ingr.name) functions shows zero progress until everything is ended, so using C4D for now
                        p = float(PlacedMols)/float(totalNumMols)*100.
                        c4d.StatusSetBar(int(p))
                        c4d.StatusSetText(ingr.name) 
        #               End working chunk pasted in by Graham from Sept 2011 on 5/16/12.
#                        print ("using c4d override for Status Bar")
                    except :
        #               p = ((float(t)-float(len(self.activeIngr)))/float(t))*100.
                        p = ((float(PlacedMols))/float(totalNumMols))#*100.    #This code shows 100% of ingredients all the time
                        if self.afviewer is not None and hasattr(self.afviewer,"vi"):
                            self.afviewer.vi.progressBar(progress=int(p),label=ingr.name)
                            if self.afviewer.renderDistance:
                                self.afviewer.vi.displayParticleVolumeDistance(distance,self)
                        #pass
                # End C4D safety check for Status bar added July 10, 2012
            compNum = ingr.compNum
            radius = ingr.minRadius
            jitter = self.callFunction(ingr.getMaxJitter,(spacing,))

            # compute dpad which is the distance at which we need to update
            # distances after the drop is successfull
            mr = self.get_dpad(compNum)
            dpad = ingr.minRadius + mr + jitter

            if verbose > 2:
                print('picked Ingr radius compNum dpad',ingr.name,radius,compNum,dpad)
            
            ## find the points that can be used for this ingredients
            ##
            res=self.callFunction(self.getPointToDrop,(ingr,radius,jitter,
                                        freePoints,nbFreePoints,
                                        distance,compId,compNum,vRangeStart,vThreshStart))
#                                        distance,compId,compNum,vRangeStart))   # Replaced this with Sept 25, 2011 thesis version on July 5, 2012
            if res[0] :
                ptInd = res[1]
                if ptInd > len(distance):
                    print ("problem ",ptInd)
                    continue
            else :
                vRangeStart = res[1]
                continue
#            print ("picked ",ptInd)
            #place the ingrediant
            if self.overwritePlaceMethod :
                ingr.placeType = self.placeMethod
            success, nbFreePoints = self.callFunction(ingr.place,(self, ptInd, 
                                freePoints, nbFreePoints, distance, dpad,
                                stepByStep, verbose),
                                {"debugFunc":debugFunc})
#            print("nbFreePoints after PLACE ",nbFreePoints)
            if success:
                PlacedMols+=1
#                nbFreePoints=self.removeOnePoint(ptInd,freePoints,nbFreePoints)  #Hidden by Graham on March 1, 2013 until we can test.
            if ingr.completion >= 1.0 :
                print('completed***************', ingr.name)
                print('PlacedMols = ', PlacedMols)
                ind = self.activeIngr.index(ingr)
#                vRangeStart = vRangeStart + self.normalizedPriorities[0]
                if ind > 0:
                    #j = 0
                    for j in range(ind):                
                        self.thresholdPriorities[j] = self.thresholdPriorities[j] + self.normalizedPriorities[ind]
                self.activeIngr.pop(ind)
#                self.thresholdPriorities.pop(ind)  # Replaced these from July SVN version with large chunk of code from thesis Sept 25, 2011 version on July 5, 2012
#                self.normalizedPriorities.pop(ind) # Replaced these from July SVN version with large chunk of code on next lines from thesis Sept 25, 2011 version on July 5, 2012                
# BEGIN large chunk of code from proper thesis Sept 25, 2011 version to correctly replace simple pop above on July 5, 2012
                #this function also depend on the ingr.completiion that can be restored ?
                self.activeIngr0, self.activeIngr12 = self.callFunction(self.getSortedActiveIngredients, (self.activeIngr,verbose))
                if verbose > 2:
                    print ('len(self.activeIngr', len(self.activeIngr))
                    print ('len(self.activeIngr0)', len(self.activeIngr0))
                    print ('len(self.activeIngr12)', len(self.activeIngr12))
                self.activeIngre_saved = self.activeIngr[:]

                self.totalPriorities = 0 # 0.00001
                for priors in self.activeIngr12:
                    pp = priors.packingPriority
                    self.totalPriorities = self.totalPriorities + pp
#                    print ('totalPriorities = ', self.totalPriorities)
                previousThresh = 0
                self.normalizedPriorities = []
                self.thresholdPriorities = [] 
                # Graham- Once negatives are used, if picked random# 
                # is below a number in this list, that item becomes 
                #the active ingredient in the while loop below
                for priors in self.activeIngr0:
                    self.normalizedPriorities.append(0)
                    if self.pickWeightedIngr :
                        self.thresholdPriorities.append(2)
                for priors in self.activeIngr12:
                    #pp1 = 0
                    pp = priors.packingPriority
                    if self.totalPriorities != 0:
                        np = float(pp)/float(self.totalPriorities)
                    else:
                        np=0.
                    self.normalizedPriorities.append(np)
#                    print ('np is ', np, ' pp is ', pp, ' tp is ', np + previousThresh)
                    self.thresholdPriorities.append(np + previousThresh)
                    previousThresh = np + float(previousThresh)
                self.activeIngr = self.activeIngr0 + self.activeIngr12
                
                nls=0
                totalNumMols = 0
                for threshProb in self.thresholdPriorities:
                    nameMe = self.activeIngr[nls]
                    totalNumMols += nameMe.nbMol
                    if verbose > 2:
                        print ('totalNumMols = ', totalNumMols)
                        print ('threshprop is %f for ingredient: %s %s %d'%(threshProb, nameMe,nameMe.name,nameMe.nbMol))
                    nls+=1
                
                #print 'vThreshStart before = ', vThreshStart
                #vThreshStart = self.thresholdPriorities[0]
                #print 'vThreshStart after = ', vThreshStart
                #print 'because vself.thresholdPriorities[0] = ', self.thresholdPriorities[0]
                #self.thresholdPriorities.pop(ind)
                #self.normalizedPriorities.pop(ind)
# END large chunk of code from proper thesis Sept 25, 2011 version to correctly replace simple pop above on July 5, 2012
#            if nbFreePoints == 0 :
#                break
        #0.8938
        # for debugging purposes
        #whats the difference with distancetosurface which is stored
        self.distancesAfterFill = distance
        self.freePointsAfterFill = freePoints
        self.nbFreePointsAfterFill = nbFreePoints
        self.distanceAfterFill = distance
        #self.rejectionCount = rejectionCount
#        c4d.documents.RunAnimation(doc, True)
        print ("get time")        
        t2 = time.time()
        print('time to fill', t2-t1)
            
        if self.saveResult:
            self.grid.freePoints = freePoints[:]
            self.grid.distToClosestSurf = distance[:]
            #shoul check extension filename for type of saved file
            self.saveGridToFile(self.resultfile+"grid")
            self.grid.result_filename = self.resultfile+"grid"
            self.store()
            self.store_asTxt()
            self.store_asJson()            
            #self.saveGridToFile_asTxt(self.resultfile+"grid")freePointsAfterFill
            #should we save to text as well
            print('time to save in fil5', time.time()-t2)
#            vAnalysis = 0
            if vAnalysis == 1 :
    #    START Analysis Tools: Graham added back this big chunk of code for analysis tools and graphic on 5/16/12 Needs to be cleaned up into a function and proper uPy code            
                unitVol = self.grid.gridSpacing**3
                #totalVolume = self.grid.gridVolume*unitVol
                wrkDirRes= self.resultfile+"_analyze_"
                print('TODO: overwrite wrkDirRes with specific user directory for each run or each script or put in a cache and offer a chance to save it')
                print("self.organelles = ", self.organelles)
                for o in self.organelles: #only for organelle ?
                    #totalVolume -= o.surfaceVolume
                    #totalVolume -= o.interiorVolume
                    innerPointNum = len(o.insidePoints)-1
                    print ('  .  .  .  . ')
                    print ('for Organelle o = ', o.name)
                    print ('inner Point Count = ', innerPointNum)
                    print ('inner Volume = ', o.interiorVolume)
                    print ('innerVolume temp Confirm = ', innerPointNum*unitVol)
                    usedPts = 0
                    unUsedPts = 0
                    #fpts = self.freePointsAfterFill
                    vDistanceString = ""
                    insidepointindce = numpy.nonzero(numpy.equal(self.grid.gridPtId,-o.number))[0]
                    for i in insidepointindce:#xrange(innerPointNum):
#                        pt = o.insidePoints[i] #fpts[i]
#                        print (pt,type(pt))
                        #for pt in self.histo.freePointsAfterFill:#[:self.histo.nbFreePointsAfterFill]:
                        d = self.distancesAfterFill[i]
                        vDistanceString += str(d)+"\n"
                        if d <= 0 :  #>self.smallestProteinSize-0.001:
                            usedPts += 1
                        else:
                            unUsedPts +=1
                    filename = wrkDirRes+"vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_dists.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
        #            filename = wrkDirRes+"/vDistances1.txt"
                    f = open(filename,"w")
                    vMyString = "I am on" + "\nThis is a new line."
                    f.write(vDistanceString)
                    f.close()
                    
                    #result is [pos,rot,ingr.name,ingr.compNum,ptInd]
                    #if resultfilename == None:
                    #resultfilename = self.resultfile
                    resultfilenameT = wrkDirRes+"vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_Trans.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
                    resultfilenameR = wrkDirRes+"vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_Rot.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
        #            resultfilenameT = wrkDirRes+"/vResultMatrix1" + o.name + "_Trans.txt"
        #            resultfilenameR = wrkDirRes+"/vResultMatrix1" + o.name + "_Rot.txt"
                    #pickle.dump(self.molecules, rfile)
                    #OR 
                    vTranslationString = ""
                    vRotationString = ""
                    result=[]
                    matCount = 0
                    # Add safety check for C4D until we can get uPy working for this matrix to hbp rotation function?
        #            from c4d import utils   # Removed by Graham on July 10, 2012 because replaced with more recent Thesis code on July 5, 2012 below
                    #what do you save everthing inleft hand ? and you actually dont use it ??
                    # Note July 4, 2012: the results are saved as right handed (see 2, 1, 0 for h, p, b) and used for analysis tools
                    # Note July 5, 2012: I found the better version we made and added it below to override the C4D version!
                    for pos, rot, ingr, ptInd in o.molecules:
                        #vMatrixString += str(result([pos]))+"\n"
        # BEGIN: newer code from Theis version added July 5, 2012
                        if hasattr(self,"afviewer"):        
                            mat = rot.copy()
                            mat[:3, 3] = pos
                            import math
                            from ePMV import comput_util as c
                            r  = c.matrixToEuler(mat)
                            h1 = math.degrees(math.pi + r[0])
                            p1 = math.degrees(r[1])
                            b1 = math.degrees(-math.pi + r[2])
                            #angles[0] = 180.0+angles[0]
                            #angles[2] = 180.0-angles[2] 
                            #hmat = self.afviewer.vi.FromMat(mat,transpose=True)
                            #rot = utils.MatrixToHPB(hmat)
                            print ('rot from matrix = ', r,h1,p1,b1)
        # END: newer code from Theis version added July 5, 2012
                        result.append([pos,rot])
                        pt3d = result[matCount][0]
                        x, y, z = pt3d #  ADDDED this line back from newer code from Theis version added July 5, 2012
        # BEGIN: retired SVN version, retired July 5, 2012
        #                x, y, z = pt3d
        #                rot3d = result[matCount][1][2]
        #                h1 = rot3d[2]
        #                p1 = rot3d[1]
        #                b1 = rot3d[0]
        #                rot3d = result[matCount][1][1]
        #                h2 = rot3d[2]
        #                p2 = rot3d[1]
        #                b2 = rot3d[0]
        #                rot3d = result[matCount][1][0]
        #                h3 = rot3d[2]
        #                p3 = rot3d[1]
        #                b3 = rot3d[0]
        # can we test for C4D for these last 6 lines until we can get same functionality from uPy?
        #                off = c4d.Vector(0)
        #                vec = c4d.Matrix(off, c4d.Vector(h1, p1, b1), c4d.Vector(h2,p2,b2), c4d.Vector(h3,p3,b3) )
        #                print vec  
        #                #m = rot3d #obj.GetMg()
        #                rot = utils.MatrixToHPB(vec)
        #                print 'rot from matrix = ', rot
        # END: retired SVN version, retired July 5, 2012                
                        vTranslationString += str(x)+ ",\t" + str(y) + ",\t" + str(z) + "\n"
                        #vRotationString += str(rot3d) #str(h)+ ",\t" + str(p) + ",\t" + str(b) + "\n"
                        vRotationString += str(h1)+ ",\t" + str(p1) + ",\t" + str(b1) + ",\t" + ingr.name +"\n"  #  ADDDED this line back from newer code from Theis version added July 5, 2012 to replace next line from SVN
        #                vRotationString += str(h1)+ ",\t" + str(p1) + ",\t" + str(b1) + ingr.name +"\n"
                        #vRotationString += str( (result[matCount][1]).x )+"\n"
                        matCount += 1
                    
                    
                    #result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
                    #d = self.distancesAfterFill[pt]
                    #vDistanceString += str(d)+"\n"
                    #pickle.dump(result, rfile)
                    rfile = open(resultfilenameT, 'w')
                    rfile.write( vTranslationString )
                    rfile.close()
                    
                    rfile = open(resultfilenameR, 'w')
                    rfile.write( vRotationString )
                    rfile.close()
                    print ('len(result) = ', len(result))
                    print ('len(self.molecules) = ', len(self.molecules))
                    ### Graham Note:  There is overused disk space- the rotation matrix is 4x4 with an offset of 0,0,0 and we have a separate translation vector in the results and molecules arrays.  Get rid of the translation vector and move it to the rotation matrix to save space... will that slow the time it takes to extract the vector from the matrix when we need to call it?       
                    print ('*************************************************** vDistance String Should be on')
                    print ('unitVolume2 = ', unitVol)
                    print ('Number of Points Unused = ', unUsedPts)
                    print ('Number of Points Used   = ', usedPts)
                    print ('Volume Used   = ', usedPts*unitVol)
                    print ('Volume Unused = ', unUsedPts*unitVol)
                    print ('vTestid = ', vTestid)
                    print ('self.nbGridPoints = ', self.nbGridPoints)
                    print ('self.gridVolume = ', self.gridVolume)
    #        self.exteriorVolume = totalVolume
                        
            print("self.organelles In HistoVol = ", len(self.organelles))
            if self.organelles == [] :
                #o = self.histoVol
#                o = self.exteriorRecipe
                unitVol = self.grid.gridSpacing**3
                innerPointNum = len(freePoints)
                print ('  .  .  .  . ')
#                print ('for Organelle o = ', o.name)
                print ('inner Point Count = ', innerPointNum)
#                print ('inner Volume = ', o.interiorVolume)
                print ('innerVolume temp Confirm = ', innerPointNum*unitVol)
                usedPts = 0
                unUsedPts = 0
                #fpts = self.freePointsAfterFill
                vDistanceString = ""
                for i in xrange(innerPointNum):
                    pt = freePoints[i] #fpts[i]
                    #for pt in self.histo.freePointsAfterFill:#[:self.histo.nbFreePointsAfterFill]:
                    d = self.distancesAfterFill[pt]
                    vDistanceString += str(d)+"\n"
                    if d <= 0 :  #>self.smallestProteinSize-0.001:
                        usedPts += 1
                    else:
                        unUsedPts +=1
#                filename = wrkDirRes+"/vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_dists.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
#                #            filename = wrkDirRes+"/vDistances1.txt"
#                f = open(filename,"w")
#                vMyString = "I am on" + "\nThis is a new line."
#                f.write(vDistanceString)
#                f.close()
#                resultfilenameT = wrkDirRes+"/vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_Trans.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
#                resultfilenameR = wrkDirRes+"/vResultMatrix1" + o.name + "_Testid" + str(vTestid) + "_Seed" + str(seedNum) + "_Rot.txt" # Used this from thesis to overwrite less informative SVN version on next line on July 5, 2012
#                vTranslationString = ""
#                vRotationString = ""
#                result=[]
#                matCount = 0
#                # Add safety check for C4D until we can get uPy working for this matrix to hbp rotation function?
#                #            from c4d import utils   # Removed by Graham on July 10, 2012 because replaced with more recent Thesis code on July 5, 2012 below
#                #what do you save everthing inleft hand ? and you actually dont use it ??
#                # Note July 4, 2012: the results are saved as right handed (see 2, 1, 0 for h, p, b) and used for analysis tools
#                # Note July 5, 2012: I found the better version we made and added it below to override the C4D version!
#                for pos, rot, ingr, ptInd in o.molecules:
#                    #vMatrixString += str(result([pos]))+"\n"
#                    # BEGIN: newer code from Theis version added July 5, 2012
#                    if hasattr(self,"afviewer"):        
#                        mat = rot.copy()
#                        mat[:3, 3] = pos
#                        import math
#                        from ePMV import comput_util as c
#                        r  = c.matrixToEuler(mat)
#                        h1 = math.degrees(math.pi + r[0])
#                        p1 = math.degrees(r[1])
#                        b1 = math.degrees(-math.pi + r[2])
#                        #angles[0] = 180.0+angles[0]
#                        #angles[2] = 180.0-angles[2] 
#                        #hmat = self.afviewer.vi.FromMat(mat,transpose=True)
#                        #rot = utils.MatrixToHPB(hmat)
#                        print 'rot from matrix = ', r,h1,p1,b1
#                    # END: newer code from Theis version added July 5, 2012
#                    result.append([pos,rot])
#                    pt3d = result[matCount][0]
#                    x, y, z = pt3d #  ADDDED this line back from newer code from Theis version added July 5, 2012             
#                    vTranslationString += str(x)+ ",\t" + str(y) + ",\t" + str(z) + "\n"
#                    vRotationString += str(h1)+ ",\t" + str(p1) + ",\t" + str(b1) + ",\t" + ingr.name +"\n"  #  ADDDED this line back from newer code from Theis version 
#                    matCount += 1
#                rfile = open(resultfilenameT, 'w')
#                rfile.write( vTranslationString )
#                rfile.close()
#                
#                rfile = open(resultfilenameR, 'w')
#                rfile.write( vRotationString )
#                rfile.close()
#                print ('len(result) = ', len(result))
#                print ('len(self.molecules) = ', len(self.molecules))
                ### Graham Note:  There is overused disk space- the rotation matrix is 4x4 with an offset of 0,0,0 and we have a separate translation vector in the results and molecules arrays.  Get rid of the translation vector and move it to the rotation matrix to save space... will that slow the time it takes to extract the vector from the matrix when we need to call it?       
                print ('*************************************************** vDistance String Should be on')
                print ('unitVolume2 = ', unitVol)
                print ('Number of Points Unused = ', unUsedPts)
                print ('Number of Points Used   = ', usedPts)
                print ('Volume Used   = ', usedPts*unitVol)
                print ('Volume Unused = ', unUsedPts*unitVol)
                print ('vTestid = ', vTestid)
                print ('self.nbGridPoints = ', self.nbGridPoints)
                print ('self.gridVolume = ', self.gridVolume)    
                print ('histoVol.timeUpDistLoopTotal = ', self.timeUpDistLoopTotal)

                            
            #totalVolume = self.grid.gridVolume*unitVol
            #fpts = self.nbFreePointsAfterFill
    #        print 'self.freePointsAfterFill = ', self.freePointsAfterFill
            #print 'nnbFreePointsAfterFill = ', self.nbFreePointsAfterFill
            #print 'Total Points = ', self.grid.gridVolume
            #print 'Total Volume = ', totalVolume
    #    END Analysis Tools: Graham added back this big chunk of code for analysis tools and graphic on 5/16/12 Needs to be cleaned up into a function and proper uPy code   
        print("getTime") 
        print('time to save end', time.time()-t2)            
        if self.afviewer is not None and hasattr(self.afviewer,"vi"):
            self.afviewer.vi.progressBar(label="Filling Complete")
            self.afviewer.vi.resetProgressBar()
        ingredients ={}
        for pos, rot, ingr, ptInd in self.molecules:
            if ingr.name not  in ingredients :
                ingredients[ingr.name]=[ingr,[],[],[]]
            mat = rot.copy()
            mat[:3, 3] = pos
            ingredients[ingr.name][1].append(pos)
            ingredients[ingr.name][2].append(rot)
            ingredients[ingr.name][3].append(numpy.array(mat))
        for o in self.organelles:
            for pos, rot, ingr, ptInd in o.molecules:
                if ingr.name not  in ingredients :
                    ingredients[ingr.name]=[ingr,[],[],[]]
                mat = rot.copy()
                mat[:3, 3] = pos
                ingredients[ingr.name][1].append(pos)
                ingredients[ingr.name][2].append(rot)
                ingredients[ingr.name][3].append(numpy.array(mat)) 
        self.ingr_result = ingredients
                            
    def displayCancelDialog(self):
        print('Popup CancelBox: if Cancel Box is up for more than 10 sec, close box and continue loop from here')
#        from pyubic.cinema4d.c4dUI import TimerDialog
#        dialog = TimerDialog()
#        dialog.init()
#        dialog.Open(async=True, pluginid=25555589, width=120, height=100)
#        tt=time.time()
        #while dialog.IsOpen():
        #    if time.time()-tt > 5.:
        #        print "time.time()-tt = ", time.time()-tt
        #        dialog.Close()
#        cancel = dialog._cancel
#        cancel=c4d.gui.QuestionDialog('WannaCancel?') # Removed by Graham on July 10, 2012 because it may no longer be needed, but test it TODO
#        return cancel

    def restore(self,result,orgaresult,freePoint):
        #should we used the grid ? the freePoint can be computed
        #result is [pos,rot,ingr.name,ingr.compNum,ptInd]
        #orgaresult is [[pos,rot,ingr.name,ingr.compNum,ptInd],[pos,rot,ingr.name,ingr.compNum,ptInd]...]
        #after restore we can build the grid and fill!
        #ingredient based dictionary
        ingredients={}
        molecules=[]
        for elem in result :
            pos,rot,name,compNum,ptInd = elem
            ingr = self.getIngrFromName(name,compNum)
            if ingr is not None:
                molecules.append([pos, rot, ingr, ptInd])
                if name not  in ingredients :
                    ingredients[name]=[ingr,[],[],[]]
                mat = rot.copy()
                mat[:3, 3] = pos
                ingredients[name][1].append(pos)
                ingredients[name][2].append(rot)
                ingredients[name][3].append(numpy.array(mat))
        self.molecules = molecules
        if self.exteriorRecipe:
            self.exteriorRecipe.molecules = molecules
        if len(orgaresult) == len(self.organelles):
            for i,o in enumerate(self.organelles):
                molecules=[]
                for elem in orgaresult[i] :
                    pos,rot,name,compNum,ptInd = elem
                    ingr = self.getIngrFromName(name,compNum)
                    if ingr is not None:
                        molecules.append([pos, rot, ingr, ptInd])
                        if name not in ingredients :
                            ingredients[name]=[ingr,[],[],[]]
                        mat = rot.copy()
                        mat[:3, 3] = pos                            
                        ingredients[name][1].append(pos)
                        ingredients[name][2].append(rot)
                        ingredients[name][3].append(numpy.array(mat))
                o.molecules = molecules
        #consider that one filling have occured
        self.cFill = self.nFill
        #if name == None :
        name = "F"+str(self.nFill)
        self.FillName.append(name)
        self.nFill+=1
        self.ingr_result = ingredients
        self.restoreFreePoints(freePoint)
        return ingredients

    def restoreFreePoints(self,freePoint):
        self.freePoints = self.freePointsAfterFill = freePoint
        self.nbFreePointsAfterFill = len(freePoint)   
        self.distanceAfterFill = self.grid.distToClosestSurf
        self.distancesAfterFill= self.grid.distToClosestSurf
        
            
    def load(self,resultfilename=None,restore_grid=True):
        if resultfilename == None:
            resultfilename = self.resultfile
        #check the extension of the filename none, txt or json
        fileName, fileExtension = os.path.splitext(resultfilename)
        if fileExtension == '':
            try :
                result= pickle.load( open(resultfilename,'rb'))
            except :
                print  ("can't read "+resultfilename)
                return [],[],[]
        elif fileExtension == '.apr':     
            try :
                result= pickle.load( open(resultfilename,'rb'))
            except :
                 return self.load_asTxt(resultfilename=resultfilename)
        elif fileExtension == '.txt':     
            return self.load_asTxt(resultfilename=resultfilename)
        elif fileExtension == '.json':
            return self.load_asJson(resultfilename=resultfilename)  
        else :
            print  ("can't read or recognize "+resultfilename)
            return [],[],[]
        #OR 
        #pos, rot, ingr, ptInd = self.molecules
        #pos,rot,ingr.name,ingr.compNum,ptInd
        orgaresult=[]
        freePoint=[]
        for i, orga in enumerate(self.organelles):
            orfile = open(resultfilename+"ogra"+str(i),'rb')
            orgaresult.append(pickle.load(orfile))
            orfile.close()
        if restore_grid :
            freePoint = self.loadFreePoint(resultfilename)
            self.restoreGridFromFile(resultfilename+"grid")#restore grid distance and ptId
        return result,orgaresult,freePoint
    
    def loadFreePoint(self,resultfilename):
        rfile = open(resultfilename+"freePoints",'rb')
        freePoint = pickle.load(rfile)
        rfile.close()
        return freePoint       
    
    def store(self,resultfilename=None):
        if resultfilename == None:
            resultfilename = self.resultfile
        rfile = open(resultfilename, 'wb')
        #pickle.dump(self.molecules, rfile)
        #OR 
        result=[]
        for pos, rot, ingr, ptInd in self.molecules:
            result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        pickle.dump(result, rfile)
        rfile.close()
        for i, orga in enumerate(self.organelles):
            orfile = open(resultfilename+"ogra"+str(i), 'wb')
            result=[]
            for pos, rot, ingr, ptInd in orga.molecules:
                result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
            pickle.dump(result, orfile)
#            pickle.dump(orga.molecules, orfile)
            orfile.close()
        rfile = open(resultfilename+"freePoints", 'wb')
        pickle.dump(self.freePoints, rfile)
        rfile.close()

    @classmethod
    def dropOneIngr(self,pos,rot, ingrname,ingrcompNum,ptInd,rad=1.0):
        line=""
        line+=("<%f,%f,%f>,")% (pos[0],pos[1],pos[2])
        r=rot.reshape(16,)   
        line+=("<")
        for i in range(15):            
            line+=("%f,")% (r[i])
        line+=("%f>,")% (r[15])
        line+="<%f>,<%s>,<%d>,<%d>\n" % (rad,ingrname,ingrcompNum,ptInd)
        return line
   
    @classmethod
    def getOneIngr(self,line):
        elem = line.split("<")
        pos = eval(elem[1][:-2])
        rot = eval(elem[2][:-2])
        rad = eval(elem[3][:-2])
        ingrname = elem[4][:-2]
        ingrcompNum = eval(elem[5][:-2])
        ptInd = eval(elem[6].split(">")[0])
        return pos,rot, ingrname,ingrcompNum,ptInd,rad

#    @classmethod
    def getOneIngrJson(self,ingr,ingrdic):
        for r in ingr.results:  
            ingrdic[ingr.name]["results"].append([r[0]],r[1],)
        if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
            ingr.nbCurve = ingrdic["nbCurve"]
            ingr.listePtLinear = []
            for i in range(ingr.nbCurve):
                ingr.listePtLinear.append( ingrdic["curve"+str(i)] )
        return ingrdic["results"], ingr.name,ingrdic["compNum"],1,ingrdic["encapsulatingRadius"]

    def load_asTxt(self,resultfilename=None):
#        from upy.hostHelper import Helper as helper 
        if resultfilename == None:
            resultfilename = self.resultfile
        rfile = open(resultfilename,'r')
        #needto parse
        result=[]
        orgaresult=[[],]*len(self.organelles)
#        mry90 = helper.rotation_matrix(-math.pi/2.0, [0.0,1.0,0.0])
#        numpy.array([[0.0, 1.0, 0.0, 0.0], 
#                 [-1., 0.0, 0.0, 0.0], 
#                 [0.0, 0.0, 1.0, 0.0], 
#                 [0.0, 0.0, 0.0, 1.0]])
        lines = rfile.readlines()        
        for l in lines :
            if not len(l) or len(l) < 6 : continue
            pos,rot, ingrname,ingrcompNum,ptInd,rad = self.getOneIngr(l)
            #should I multiply here
            r = numpy.array(rot).reshape(4,4)#numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
            if ingrcompNum == 0 :
                result.append([numpy.array(pos),numpy.array(r),ingrname,ingrcompNum,ptInd])
            else :
                orgaresult[abs(ingrcompNum)-1].append([numpy.array(pos),numpy.array(r),ingrname,ingrcompNum,ptInd])
#        for i, orga in enumerate(self.organelles):
#            orfile = open(resultfilename+"ogra"+str(i),'rb')
#            orgaresult.append(pickle.load(orfile))
#            orfile.close()
#        rfile.close()
#        rfile = open(resultfilename+"freePoints",'rb')
        freePoint = []# pickle.load(rfile)
        try :
            rfile = open(resultfilename+"freePoints",'rb')
            freePoint = pickle.load(rfile)
            rfile.close()
        except :
            pass
        return result,orgaresult,freePoint

    def collectResultPerIngredient(self):
        for pos, rot, ingr, ptInd in self.molecules:
            if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
                pass#already store
            else :
                ingr.results.append([pos,rot])
        for i, orga in enumerate(self.organelles):
            for pos, rot, ingr, ptInd in orga.molecules:
                if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
                    pass#already store
                else :
                    ingr.results.append([pos,rot])                                

    def load_asJson(self,resultfilename=None):
#        from upy.hostHelper import Helper as helper 
        if resultfilename == None:
            resultfilename = self.resultfile
        with open(resultfilename, 'r') as fp :#doesnt work with symbol link ?
            self.result_json=json.load(fp)#,indent=4, separators=(',', ': ')
        #needto parse
        result=[]
        orgaresult=[[],]*len(self.organelles)
        r =  self.exteriorRecipe
        if r :
            for ingr in r.ingredients:                
                iresults, ingrname,ingrcompNum,ptInd,rad = self.getOneIngrJson(ingr,self.result_json["exteriorRecipe"][ingr.name])
                for r in iresults:
                    rot = numpy.array(r[1]).reshape(4,4)#numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
                    result.append([numpy.array(r[0]),rot,ingrname,ingrcompNum,1])
        #organelle ingr
        for orga in self.organelles:
            #organelle surface ingr
            rs =  orga.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    iresults, ingrname,ingrcompNum,ptInd,rad = self.getOneIngrJson(ingr,self.result_json[orga.name+"_surfaceRecipe"][ingr.name])
                    for r in iresults:
                        rot = numpy.array(r[1]).reshape(4,4)#numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
                        orgaresult[abs(ingrcompNum)-1].append([numpy.array(r[0]),rot,ingrname,ingrcompNum,1])
            #organelle matrix ingr
            ri =  orga.innerRecipe
            if ri :
                for ingr in ri.ingredients:                    
                    iresults, ingrname,ingrcompNum,ptInd,rad = self.getOneIngrJson(ingr,self.result_json[orga.name+"_innerRecipe"][ingr.name])
                    for r in iresults:
                        rot = numpy.array(r[1]).reshape(4,4)#numpy.matrix(mry90)*numpy.matrix(numpy.array(rot).reshape(4,4))
                        orgaresult[abs(ingrcompNum)-1].append([numpy.array(r[0]),rot,ingrname,ingrcompNum,1])
        freePoint = []# pickle.load(rfile)
        try :
            rfile = open(resultfilename+"freePoints",'rb')
            freePoint = pickle.load(rfile)
            rfile.close()
        except :
            pass
        return result,orgaresult,freePoint
        
    def dropOneIngrJson(self,ingr,rdic):
        rdic[ingr.name]={}
        rdic[ingr.name]["compNum"]= ingr.compNum
        rdic[ingr.name]["encapsulatingRadius"]= ingr.encapsulatingRadius
        rdic[ingr.name]["results"]=[] 
        for r in ingr.results:  
            if hasattr(r[0],"tolist"):
                r[0]=r[0].tolist()
            if hasattr(r[1],"tolist"):
                r[1]=r[1].tolist()
            rdic[ingr.name]["results"].append([r[0],r[1]])
        if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
            rdic[ingr.name]["nbCurve"]=ingr.nbCurve
            for i in range(ingr.nbCurve):
                lp = numpy.array(ingr.listePtLinear[i])
                ingr.listePtLinear[i]=lp.tolist()                 
                rdic[ingr.name]["curve"+str(i)] = ingr.listePtLinear[i]
       
    def store_asJson(self,resultfilename=None):
        if resultfilename == None:
            resultfilename = self.resultfile
        self.collectResultPerIngredient()
        self.result_json={}
        r =  self.exteriorRecipe
        if r :
            self.result_json["exteriorRecipe"]={}
            for ingr in r.ingredients:
                self.dropOneIngrJson(ingr,self.result_json["exteriorRecipe"])

        #organelle ingr
        for orga in self.organelles:
            #organelle surface ingr
            rs =  orga.surfaceRecipe
            if rs :
                self.result_json[orga.name+"_surfaceRecipe"]={}
                for ingr in rs.ingredients:
                    self.dropOneIngrJson(ingr,self.result_json[orga.name+"_surfaceRecipe"])
            #organelle matrix ingr
            ri =  orga.innerRecipe
            if ri :
                self.result_json[orga.name+"_innerRecipe"]={}
                for ingr in ri.ingredients:
                    self.dropOneIngrJson(ingr,self.result_json["_innerRecipe"])
        with open(resultfilename+".json", 'w') as fp :#doesnt work with symbol link ?
            json.dump(self.result_json,fp,indent=4, separators=(',', ': '))#,indent=4, separators=(',', ': ')
        
    def store_asTxt(self,resultfilename=None):
        if resultfilename == None:
            resultfilename = self.resultfile
        rfile = open(resultfilename+".txt", 'w')#doesnt work with symbol link ?
        #pickle.dump(self.molecules, rfile)
        #OR 
        result=[]
        line=""
        for pos, rot, ingr, ptInd in self.molecules:
            line+=self.dropOneIngr(pos,rot,ingr.name,ingr.compNum,ptInd,rad=ingr.encapsulatingRadius)
            #result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        rfile.write(line)
        #write the curve point 

        rfile.close()
        for i, orga in enumerate(self.organelles):
            orfile = open(resultfilename+"ogra"+str(i)+".txt", 'w')
            result=[]
            line=""
            for pos, rot, ingr, ptInd in orga.molecules:
                line+=self.dropOneIngr(pos,rot,ingr.name,ingr.compNum,ptInd,rad=ingr.encapsulatingRadius)
            orfile.write(line)
#            pickle.dump(orga.molecules, orfile)
            orfile.close()
#        rfile = open(resultfilename+"freePoints", 'w')
#        pickle.dump(self.freePoints, rfile)
#        rfile.close()

    @classmethod
    def convertPickleToText(self,resultfilename=None,norga=0):
        if resultfilename == None:
            resultfilename = self.resultfile
        rfile = open(resultfilename)
        result= pickle.load( rfile)
        orgaresult=[]
        for i in range(norga):
            orfile = open(resultfilename+"ogra"+str(i))
            orgaresult.append(pickle.load(orfile))
            orfile.close()
        rfile.close()
        rfile = open(resultfilename+"freePoints")
        freePoint = pickle.load(rfile)
        rfile.close()
        rfile = open(resultfilename+".txt", 'w')
        line=""
        for pos, rot, ingrName,compNum, ptInd in result:
            line+=self.dropOneIngr(pos,rot,ingrName,compNum,ptInd)
            #result.append([pos,rot,ingr.name,ingr.compNum,ptInd])
        rfile.write(line)
        rfile.close()
        for i in range(norga):
            orfile = open(resultfilename+"ogra"+str(i)+".txt", 'w')
            result=[]
            line=""
            for pos, rot, ingrName,compNum, ptInd in orgaresult[i]:
                line+=self.dropOneIngr(pos,rot,ingrName,compNum,ptInd)
            orfile.write(line)
#            pickle.dump(orga.molecules, orfile)
            orfile.close()
         #freepoint
         
    def printFillInfo(self):
        r = self.exteriorRecipe
        if r is not None:
            print('    histoVol exterior recipe:')
            r.printFillInfo('        ')
            
        for o in self.organelles:
            o.printFillInfo()

    def finishWithWater(self,freePoints=None,nbFreePoints=None):
        #self.freePointsAfterFill[:self.nbFreePointsAfterFill]
        water = [ ( 0.000, 0.000, 0.0), #0
                  ( 0.757, 0.586, 0.0), #H
                  (-0.757, 0.586, 0.0)] #H
        #object?
        #sphere sphere of 2.9A
        waterDiam = 2.9
        if freePoints is None :
            freePoints = self.freePointsAfterFill
        if nbFreePoints is None :
            nbFreePoints = self.nbFreePointsAfterFill
        #a freepoint is a voxel, how many water in the voxel
        voxelsize = self.grid.gridSpacing
        nbWaterPerVoxel = voxelsize / waterDiam
        #coords masterGridPositions

    def estimateVolume(self,boundingBox, spacing):
        #need to box N point and coordinaePoint
#        xl,yl,zl = boundingBox[0]
#        xr,yr,zr = boundingBox[1]
#        realTotalVol = (xr-xl)*(yr-yl)*(zr-zl)
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        grid.gridVolume,grid.nbGridPoints = self.callFunction(self.computeGridNumberOfPoint,(boundingBox,spacing))
        unitVol = spacing**3
        realTotalVol = grid.gridVolume*unitVol

        r = self.exteriorRecipe
        if r :
            r.setCount(realTotalVol,reset=False)
        for o in self.organelles:
            o.estimateVolume(hBB=grid.boundingBox)
            rs = o.surfaceRecipe
            if rs :
                realTotalVol = o.surfaceVolume
                rs.setCount(realTotalVol,reset=False)
            ri = o.innerRecipe
            if ri :
                realTotalVol = o.interiorVolume
                ri.setCount(realTotalVol,reset=False)

    def estimateVolume_old(self,boundingBox, spacing):
        #need to box N point and coordinaePoint
        pad = 10.0
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        grid.gridVolume,grid.nbGridPoints = self.callFunction(self.computeGridNumberOfPoint,(boundingBox,spacing))
        nbPoints = grid.gridVolume            
        # compute 3D point coordiantes for all grid points
        self.callFunction(grid.create3DPointLookup) 
        grid.gridPtId = [0]*nbPoints
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        realTotalVol = (xr-xl)*(yr-yl)*(zr-zl)
        print ("totalVolume %f for %d points" % (realTotalVol,nbPoints))
        # distToClosestSurf is set to self.diag initially
        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
        distance  = grid.distToClosestSurf = [diag]*nbPoints
        #foreach ingredient get estimation of insidepoint and report the percantage of total point in Volume
        r = self.exteriorRecipe
        if r :
            for ingr in r.ingredients:
                insidePoints,newDistPoints=ingr.getInsidePoints(grid,grid.masterGridPositions,pad,distance,
                       centT=ingr.positions[-1],jtrans=[0.,0.,0.], rotMatj=numpy.identity(4))
                ingr.nbPts = len(insidePoints)
                onemol = (realTotalVol* float(ingr.nbPts) )/ float(nbPoints)
                ingr.vol_nbmol = int(ingr.molarity * onemol)
                print ("ingr %s has %d points representing %f for one mol thus %d mol" %(ingr.name, ingr.nbPts, onemol, ingr.vol_nbmol))
#                ingr.vol_nbmol = ?
        for o in self.organelles:
            rs = o.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    insidePoints,newDistPoints=ingr.getInsidePoints(grid,grid.masterGridPositions,pad,distance,
                           centT=ingr.positions[-1],jtrans=[0.,0.,0.], rotMatj=numpy.identity(4))
                    ingr.nbPts = len(insidePoints)
                    onemol = (realTotalVol* float(ingr.nbPts) )/ float(nbPoints)
                    ingr.vol_nbmol = int(ingr.molarity * onemol)
            ri = o.innerRecipe
            if ri :
                for ingr in ri.ingredients:
                    insidePoints,newDistPoints=ingr.getInsidePoints(grid,grid.masterGridPositions,pad,distance,
                           centT=ingr.positions[-1],jtrans=[0.,0.,0.], rotMatj=numpy.identity(4))
                    ingr.nbPts = len(insidePoints)
                    onemol = (realTotalVol* float(ingr.nbPts) )/ float(nbPoints)
                    ingr.vol_nbmol = int(ingr.molarity * onemol)
    
    def setupPanda(self,):
        if self.world is None :
            if panda3d is None :
                return
            from panda3d.core import loadPrcFileData
            
            loadPrcFileData("", "window-type none" ) 
            # Make sure we don't need a graphics engine 
            #(Will also prevent X errors / Display errors when starting on linux without X server)
            loadPrcFileData("", "audio-library-name null" ) # Prevent ALSA errors 
#            loadPrcFileData('', 'bullet-enable-contact-events true')
            loadPrcFileData('', 'bullet-max-objects 10240')
            
            import direct.directbase.DirectStart 
            from panda3d.bullet import BulletWorld
            from panda3d.core import Vec3
#            bullet.bullet-max-objects = 1024 * 10#sum of all predicted n Ingredient ?
            self.worldNP = render.attachNewNode('World')            
            self.world = BulletWorld()
            self.world.setGravity(Vec3(0, 0, 0))
            self.static=[]
            self.moving = None
            self.rb_panda = []

    def delRB(self, node):
        if panda3d is None :
                return
        self.world.removeRigidBody(node)
        if node in self.rb_panda: self.rb_panda.pop(self.rb_panda.index(node))
        if node in self.static: self.static.pop(self.static.index(node))
        if node == self.moving: self.moving = None
        np = NodePath(node)
        np.removeNode()

    def addSingleSphereRB(self,ingr,pMat,jtrans,rotMat):
        shape = BulletSphereShape(ingr.encapsulatingRadius)
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
#        inodenp.node().addShape(shape)
        inodenp.node().addShape(shape,TransformState.makePos(Point3(0, 0, 0)))#rotation ?
#        spherenp.setPos(-2, 0, 4)
        return inodenp
        
    def addMultiSphereRB(self,ingr,pMat,jtrans,rotMat):
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        centT = ingr.positions[0]#ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        for radc, posc in zip(ingr.radii[0], centT):
            shape = BulletSphereShape(radc)
            inodenp.node().addShape(shape, TransformState.makePos(Point3(posc[0],posc[1],posc[2])))#
        return inodenp
        
    def addSingleCubeRB(self,ingr,pMat,jtrans,rotMat):
        rt = "Box"
        halfextents= ingr.bb[1]
        print (halfextents)
        shape = BulletBoxShape(Vec3(halfextents[0], halfextents[1], halfextents[2]))#halfExtents
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
#        inodenp.node().addShape(shape)
        inodenp.node().addShape(shape,TransformState.makePos(Point3(0, 0, 0)))#, pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
#        spherenp.setPos(-2, 0, 4)
        return inodenp
        
    def addMultiCylinderRB(self,ingr,pMat,jtrans,rotMat):   
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        centT1 = ingr.positions[0]#ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        centT2 = ingr.positions2[0]#ingr.transformPoints(jtrans, rotMat, ingr.positions2[0])
        for radc, p1, p2 in zip(ingr.radii[0], centT1, centT2):
            length, mat = helper.getTubePropertiesMatrix(p1,p2)
            pMat = self.pandaMatrice(mat)
#            d = numpy.array(p1) - numpy.array(p2)
#            s = numpy.sum(d*d)
            shape = BulletCylinderShape(radc, length,1)#math.sqrt(s), 1)# { XUp = 0, YUp = 1, ZUp = 2 } or LVector3f const half_extents
            inodenp.node().addShape(shape, TransformState.makeMat(pMat))#
        return inodenp

    def addMeshRBOld(self,ingr,pMat,jtrans,rotMat):
        helper = AutoFill.helper
        if ingr.mesh is None:
            return
        faces,vertices,vnormals = helper.DecomposeMesh(ingr.mesh,
                                edit=False,copy=False,tri=True,transform=True)        
        from panda3d.bullet import BulletTriangleMesh,BulletTriangleMeshShape
        p0 = Point3(-10, -10, 0)
        p1 = Point3(-10, 10, 0)
        p2 = Point3(10, -10, 0)
        p3 = Point3(10, 10, 0)
        mesh = BulletTriangleMesh()
        points3d = [Point3(v[0],v[1],v[2]) for v in vertices]
        for f in faces:
            mesh.addTriangle(points3d[f[0]],points3d[f[1]],points3d[f[2]])
            
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        inodenp.node().addShape(shape,TransformState.makePos(Point3(0, 0, 0)))#, pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
        return inodenp

    def setGeomFaces(self,tris,face):                
        #have to add vertices one by one since they are not in order
        if len(face) == 2 :
            face = numpy.array([face[0],face[1],face[1],face[1]],dtype='int')
        for i in face :        
            tris.addVertex(i)
        tris.closePrimitive()


    def addMeshRB(self,ingr,pMat,jtrans,rotMat):
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        inodenp.node().setMass(1.0)
        helper = AutoFill.helper
        if ingr.mesh is None:
            return
        faces,vertices,vnormals = helper.DecomposeMesh(ingr.mesh,
                               edit=False,copy=False,tri=True,transform=True)        
        from panda3d.core import GeomVertexFormat,GeomVertexWriter,GeomVertexData,Geom,GeomTriangles
        from panda3d.core import GeomVertexReader
        from panda3d.bullet import BulletTriangleMesh,BulletTriangleMeshShape,BulletConvexHullShape
        #step 1) create GeomVertexData and add vertex information
        format=GeomVertexFormat.getV3()
        vdata=GeomVertexData("vertices", format, Geom.UHStatic)        
        vertexWriter=GeomVertexWriter(vdata, "vertex")
        [vertexWriter.addData3f(v[0],v[1],v[2]) for v in vertices]

        #step 2) make primitives and assign vertices to them
        tris=GeomTriangles(Geom.UHStatic)
        [self.setGeomFaces(tris,face) for face in faces]

        #step 3) make a Geom object to hold the primitives
        geom=Geom(vdata)
        geom.addPrimitive(tris)
        #step 4) create the bullet mesh and node
        mesh = BulletTriangleMesh()
        mesh.addGeom(geom)    
        shape = BulletTriangleMeshShape(mesh, dynamic=False)#BulletConvexHullShape
        #or
        #shape = BulletConvexHullShape()
        #shape.add_geom(geom)
        print "shape ok",shape
        #inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(ingr.name))
        #inodenp.node().setMass(1.0)
        inodenp.node().addShape(shape)#,TransformState.makePos(Point3(0, 0, 0)))#, pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
        return inodenp


    def pandaMatrice(self,mat):
        mat = mat.transpose().reshape((16,))
#        print mat,len(mat),mat.shape
        pMat = Mat4(mat[0],mat[1],mat[2],mat[3],
                   mat[4],mat[5],mat[6],mat[7],
                   mat[8],mat[9],mat[10],mat[11],
                   mat[12],mat[13],mat[14],mat[15],)
        return pMat
        
    
    def addRB(self,ingr, trans, rotMat, rtype="SingleSphere",static=False):
        # Sphere
        if panda3d is None :
            return None
        mat = rotMat.copy()
#        mat[:3, 3] = trans
#        mat = mat.transpose()
        mat = mat.transpose().reshape((16,))
#        print mat,len(mat),mat.shape
        pMat = TransformState.makeMat(Mat4(mat[0],mat[1],mat[2],mat[3],
                                           mat[4],mat[5],mat[6],mat[7],
                                           mat[8],mat[9],mat[10],mat[11],
                                           trans[0],trans[1],trans[2],mat[15],))
        
        shape = None
        inodenp = None
#        print (pMat) 		
        if ingr.use_mesh_rb:
            rtype = "Mesh"
            print "#######RBNode Mesh ####", ingr.name, ingr.rbnode,self.rb_func_dic[rtype]
        inodenp = self.rb_func_dic[rtype](ingr,pMat,trans,rotMat)
        inodenp.setCollideMask(BitMask32.allOn())
        inodenp.node().setAngularDamping(1.0)
        inodenp.node().setLinearDamping(1.0)
        
        self.world.attachRigidBody(inodenp.node())
        if static :
            self.static.append(inodenp.node())
        else :
            self.moving = inodenp.node()
        self.rb_panda.append(inodenp.node())
        return inodenp.node()
    
    def moveRBnode(self,node, trans, rotMat):
        mat = rotMat.copy()
#        mat[:3, 3] = trans
#        mat = mat.transpose()
        mat = mat.transpose().reshape((16,))
#        print mat,len(mat),mat.shape
        pMat = Mat4(mat[0],mat[1],mat[2],mat[3],
                   mat[4],mat[5],mat[6],mat[7],
                   mat[8],mat[9],mat[10],mat[11],
                   trans[0],trans[1],trans[2],mat[15],)
        pTrans = TransformState.makeMat(pMat)
        nodenp = NodePath(node)
        nodenp.setMat(pMat)
#        nodenp.setPos(trans[0],trans[1],trans[2])
#        print nodenp.getPos()
    
    def getRotTransRB(self,node ):
        nodenp = NodePath(node)
        m=nodenp.getMat()
        M = numpy.array(m)
        rRot = numpy.identity(4)
        rRot[:3,:3] = M[:3,:3]
        rTrans = M[3,:3]
        return rTrans,rRot
        
    def runBullet(self,ingr,simulationTimes, runTimeDisplay):
        done = False
        t1=time()
        simulationTimes = 5.0
        while not done:
            #should do it after a jitter run
#        for i in xrange(10):
            dt = globalClock.getDt()
            self.world.doPhysics(dt, 100,1.0/500.0)#world.doPhysics(dt, 10, 1.0/180.0)100, 1./500.#2, 1.0/120.0
            #check number of contact betwee currrent and rest ?
            r=[ (self.world.contactTestPair(self.moving, n).getNumContacts() > 0 ) for n in self.static]
            done=not ( True in r)
            print (done,dt,time()-t1)
            if runTimeDisplay :
                #move self.moving and update
                nodenp = NodePath(self.moving)
                ma=nodenp.getMat()
                self.afviewer.vi.setObjectMatrix(ingr.moving_geom,numpy.array(ma),transpose=False)#transpose ?
                self.afviewer.vi.update()
            if (time()-t1) > simulationTimes :
                done = True
                break
            
        