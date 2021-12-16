# -*- coding: utf-8 -*-
"""
############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, 
#   and Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson 
#    between 2005 and 2010 
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input 
#   from Arthur Olson's Molecular Graphics Lab
#
# Ingredient.py Authors: Graham Johnson & Michel Sanner with 
#  editing/enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner 
#  with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# Copyright: Graham Johnson ©2010
#
# This file "Ingredient.py" is part of autoPACK, cellPACK, and AutoFill.
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
############################################################################
@author: Graham Johnson, Ludovic Autin, & Michel Sanner


# Hybrid version merged from Graham's Sept 2011 and Ludo's April 2012 
# version on May 16, 2012
# Updated with Correct Sept 25, 2011 thesis version on July 5, 2012

# TODO: Describe Ingredient class here at high level
"""

import numpy, weakref
from math import sqrt, pi,sin, cos, asin

from random import uniform, gauss,random
from time import time,sleep
import math
from .ray import vlen, vdiff, vcross

#init panda ?
#
import sys

try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib

import AutoFill
from AutoFill import checkURL

AFDIR = AutoFill.__path__[0]#working dir ?

try :
    helper = AutoFill.helper
except :
    helper = None
print ("helper in Ingredient is "+str(helper))
helper = AutoFill.helper
reporthook = None
if helper is not None:        
    reporthook=helper.reporthook

import numpy.oldnumeric as N
degtorad = pi/180.
KWDS = {   "molarity":{"type":"float"}, 
                        "radii":{"type":"float"}, 
                        "positions":{"type":"vector"}, "positions2":{"type":"vector"},
                        "sphereFile":{"type":"string"}, 
                        "packingPriority":{"type":"float"}, "name":{"type":"string"}, "pdb":{"type":"string"}, 
                        "color":{"type":"vector"},"principalVector":{"type":"vector"},
                        "meshFile":{"type":"string"},
                        "use_mesh_rb":{"name":"use_mesh_rb","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"use mesh for collision"},                             
                        "coordsystem":{"name":"coordsystem","type":"string","value":"right","default":"right","description":"coordinate system of the files"},
#                        "meshObject":{"type":"string"},
                        "nbMol":{"type":"int"},
                        "Type":{"type":"string"},
                        "jitterMax":{"name":"jitterMax","value":[1.,1.,1.],"default":[1.,1.,1.],"min":0,"max":1,"type":"vector","description":"jitterMax"},
                        "nbJitter":{"name":"nbJitter","value":5,"default":5,"type":"int","min":0,"max":50,"description":"nbJitter"},
                        "perturbAxisAmplitude":{"name":"perturbAxisAmplitude","value":0.1,"default":0.1,"min":0,"max":1,"type":"float","description":"perturbAxisAmplitude"},
                        "useRotAxis":{"name":"useRotAxis","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"useRotAxis"},                             
                        "rotAxis":{"name":"rotAxis","value":[0.,0.,0.],"default":[0.,0.,0.],"min":0,"max":1,"type":"vector","description":"rotAxis"},
                        "rotRange":{"name":"rotRange","value":6.2831,"default":6.2831,"min":0,"max":12,"type":"float","description":"rotRange"},
                        "principalVector":{"name":"principalVector","value":[0.,0.,0.],"default":[0.,0.,0.],"min":-1,"max":1,"type":"vector","description":"principalVector"},
                        "cutoff_boundary":{"name":"cutoff_boundary","value":1.0,"default":1.0,"min":0.,"max":50.,"type":"float","description":"cutoff_boundary"},
                        "cutoff_surface":{"name":"cutoff_surface","value":5.0,"default":5.0,"min":0.,"max":50.,"type":"float","description":"cutoff_surface"},
                        "placeType":{"name":"placeType","value":"jitter","values":AutoFill.LISTPLACEMETHOD,"min":0.,"max":0.,
                                        "default":"jitter","type":"liste","description":"placeType"},
                        "packingMode":{"type":"string"},                     
                        "useLength":{"type":"float"},
                        "length":{"type":"float"},
                        "closed":{"type":"bool"},
                        "biased":{"type":"float"},
                        "marge":{"type":"float"},
                        "orientation":{"type":"vector"},
                        "walkingMode":{"type":"string"},
                        "gradient":{"name":"gradient","value":"","values":[],"min":0.,"max":0.,
                                        "default":"jitter","type":"liste","description":"gradient name to use if histo.use_gradient"},
}
#from mglutil.math.rotax import rotax, rotVectToVect
def rotax( a, b, tau, transpose=1 ):
    """
    Build 4x4 matrix of clockwise rotation about axis a-->b
    by angle tau (radians).
    a and b are sequences of 3 floats each
    Result is a homogenous 4x4 transformation matrix.
    NOTE: This has been changed by Brian, 8/30/01: rotax now returns
    the rotation matrix, _not_ the transpose. This is to get
    consistency across rotax, mat_to_quat and the classes in
    transformation.py
    when transpose is 1 (default) a C-style rotation matrix is returned
    i.e. to be used is the following way Mx (opposite of OpenGL style which
    is using the FORTRAN style)
    """

    assert len(a) == 3
    assert len(b) == 3
    if tau <= -2*pi or tau >= 2*pi:
        tau = tau%(2*pi)

    ct = cos(tau)
    ct1 = 1.0 - ct
    st = sin(tau)

    # Compute unit vector v in the direction of a-->b. If a-->b has length
    # zero, assume v = (1,1,1)/sqrt(3).

    v = [b[0]-a[0], b[1]-a[1], b[2]-a[2]]
    s = v[0]*v[0]+v[1]*v[1]+v[2]*v[2]
    if s > 0.0:
        s = sqrt(s)
        v = [v[0]/s, v[1]/s, v[2]/s]
    else:
        val = sqrt(1.0/3.0)
        v = (val, val, val)

    rot = N.zeros( (4,4), 'f' )
    # Compute 3x3 rotation matrix

    v2 = [v[0]*v[0], v[1]*v[1], v[2]*v[2]]
    v3 = [(1.0-v2[0])*ct, (1.0-v2[1])*ct, (1.0-v2[2])*ct]
    rot[0][0]=v2[0]+v3[0]
    rot[1][1]=v2[1]+v3[1]
    rot[2][2]=v2[2]+v3[2]
    rot[3][3] = 1.0;

    v2 = [v[0]*st, v[1]*st, v[2]*st]
    rot[1][0]=v[0]*v[1] * ct1-v2[2]
    rot[2][1]=v[1]*v[2] * ct1-v2[0]
    rot[0][2]=v[2]*v[0] * ct1-v2[1]
    rot[0][1]=v[0]*v[1] * ct1+v2[2]
    rot[1][2]=v[1]*v[2] * ct1+v2[0]
    rot[2][0]=v[2]*v[0] * ct1+v2[1]

    # add translation
    for i in (0,1,2):
        rot[3][i] = a[i]
    for j in (0,1,2):
        rot[3][i] = rot[3][i]-rot[j][i]*a[j]
    rot[i][3]=0.0

    if transpose:
        return rot
    else:
        return N.transpose(rot)




def rotVectToVect(vect1, vect2, i=None):
    """returns a 4x4 transformation that will align vect1 with vect2
vect1 and vect2 can be any vector (non-normalized)
"""
    v1x, v1y, v1z = vect1
    v2x, v2y, v2z = vect2
    
    # normalize input vectors
    norm = 1.0/sqrt(v1x*v1x + v1y*v1y + v1z*v1z )
    v1x *= norm
    v1y *= norm
    v1z *= norm    
    norm = 1.0/sqrt(v2x*v2x + v2y*v2y + v2z*v2z )
    v2x *= norm
    v2y *= norm
    v2z *= norm
    
    # compute cross product and rotation axis
    cx = v1y*v2z - v1z*v2y
    cy = v1z*v2x - v1x*v2z
    cz = v1x*v2y - v1y*v2x

    # normalize
    nc = sqrt(cx*cx + cy*cy + cz*cz)
    if nc==0.0:
        return [ [1., 0., 0., 0.],
                 [0., 1., 0., 0.],
                 [0., 0., 1., 0.],
                 [0., 0., 0., 1.] ]

    cx /= nc
    cy /= nc
    cz /= nc
    
    # compute angle of rotation
    if nc<0.0:
        if i is not None:
            print ('truncating nc on step:', i, nc)
        nc=0.0
    elif nc>1.0:
        if i is not None:
            print ('truncating nc on step:', i, nc)
        nc=1.0
        
    alpha = asin(nc)
    if (v1x*v2x + v1y*v2y + v1z*v2z) < 0.0:
        alpha = pi - alpha

    # rotate about nc by alpha
    # Compute 3x3 rotation matrix

    ct = cos(alpha)
    ct1 = 1.0 - ct
    st = sin(alpha)
    
    rot = [ [0., 0., 0., 0.],
            [0., 0., 0., 0.],
            [0., 0., 0., 0.],
            [0., 0., 0., 0.] ]


    rv2x, rv2y, rv2z = cx*cx, cy*cy, cz*cz
    rv3x, rv3y, rv3z = (1.0-rv2x)*ct, (1.0-rv2y)*ct, (1.0-rv2z)*ct
    rot[0][0] = rv2x + rv3x
    rot[1][1] = rv2y + rv3y
    rot[2][2] = rv2z + rv3z
    rot[3][3] = 1.0;

    rv4x, rv4y, rv4z = cx*st, cy*st, cz*st
    rot[0][1] = cx * cy * ct1 - rv4z
    rot[1][2] = cy * cz * ct1 - rv4x
    rot[2][0] = cz * cx * ct1 - rv4y
    rot[1][0] = cx * cy * ct1 + rv4z
    rot[2][1] = cy * cz * ct1 + rv4x
    rot[0][2] = cz * cx * ct1 + rv4y

    return rot

def getSpheres(sphereFile):
    """
    get spherical approximation of shape
    """
    # file format is space separated
    # float:Rmin float:Rmax
    # int:number of levels
    # int: number of spheres in first level
    # x y z r i j k ...# first sphere in first level and 0-based indices
                       # of spheres in next level covererd by this sphere
    # ...
    # int: number of spheres in second level
    helper = AutoFill.helper
    reporthook = None
    if helper is not None:        
        reporthook=helper.reporthook
    print ("sphereFile ",sphereFile)
    if sphereFile.find("http") != -1 or sphereFile.find("ftp")!= -1 :
        name = sphereFile.split("/")[-1]
        tmpFileName = AFDIR+os.sep+"cache_ingredients"+os.sep+"sphereTree"+os.sep+name
        #check if exist first
        if not os.path.isfile(tmpFileName) or AutoFill.forceFetch :
            try :
                import urllib.request as urllib
            except :
                import urllib
            if checkURL(sphereFile):
                urllib.urlretrieve(sphereFile, tmpFileName,reporthook=reporthook)
            else :
                if not os.path.isfile(tmpFileName)  :
                    return  0, 0, [], [], []
        sphereFile = tmpFileName    
    f = open(sphereFile)
    datao = f.readlines()
    f.close()
    
    # strip comments
    data = [x for x in datao if x[0]!='#' and len(x)>1]

    rmin, rmax = list(map(float, data[0].split()))
    nblevels = int(data[1])
    radii = []
    centers = []
    children = []
    line = 2
    for level in range(nblevels):
        rl = []
        cl = []
        ch = []
        nbs = int(data[line])
        line += 1
        for n in range(nbs):
            w = data[line].split()
            x,y,z,r = list(map(float, w[:4]))
            if level<nblevels-1: # get sub spheres indices
                ch.append( list(map(int, w[4:])) )
            cl.append( (x,y,z) )
            rl.append( r )
            line += 1
        centers.append(cl)
        radii.append(rl)
        children.append(ch)

    # we ignore the hierarchy for now
    return rmin, rmax, centers, radii, children 


def ApplyMatrix(coords,mat):
    """
    Apply the 4x4 transformation matrix to the given list of 3d points.

    @type  coords: array
    @param coords: the list of point to transform.
    @type  mat: 4x4array
    @param mat: the matrix to apply to the 3d points

    @rtype:   array
    @return:  the transformed list of 3d points
    """

    #4x4matrix"
    mat = numpy.array(mat)
    coords = numpy.array(coords)
    one = numpy.ones( (coords.shape[0], 1), coords.dtype.char )
    c = numpy.concatenate( (coords, one), 1 )
    return numpy.dot(c, numpy.transpose(mat))[:, :3]


class Partner:
    def __init__(self,name,weight=0.0,properties=None):
        self.name = name
        self.weight = weight
        self.properties = {}
        if properties is not None:
            self.properties = properties
            
    def addProperties(self,name, value):
        self.properties[name] = value

    def getProperties(self,name):
        if name in self.properties:
            return self.properties[name]
        else :
            return None        

    def distanceFunction(self,d,expression=None,function=None):
        #default functino that can be overwrite or 
        #can provide an experssion which 1/d or 1/d^2 or d^2etc.w*expression
        #can provide directly a function that take as
        # arguments the w and the distance
        if expression is not None:
            val = self.weight * expression(d)
        elif function is not None :
            val = function(self.weight,d)
        else :
            val= self.weight*1/d
        return val
        
class Agent:
    def __init__(self, name, concentration, packingMode='close', 
                 placeType="jitter", **kw):
        self.name=name
        self.concentration = concentration
        self.partners={}
        self.excluded_partners={}
        assert packingMode in ['random', 'close', 'closePartner',
                               'randomPartner', 'gradient']
        self.packingMode = packingMode

        #assert placeType in ['jitter', 'spring','rigid-body']
        self.placeType = placeType
        self.isAttractor = False
        self.mesh_3d = None
        self.weight=0.2               #use for affinity ie partner.weight
        if "weight" in kw:
            self.weight=kw["weight"]
        self.proba_not_binding = 0.5  #chance to actually not bind
        if "proba_not_binding" in kw:
            self.proba_not_binding = kw["proba_not_binding"]
        self.force_random = False     #avoid any binding
        if "force_random" in kw:
            self.force_random = kw["force_random"]
        self.distFunction = None
        if "distFunction" in kw:
            self.distFunction = kw["distFunction"]
        self.distExpression = None
        if "distExpression" in kw:
            self.distExpression=kw["distExpression"]
        self.overwrite_distFunc = False     #overWrite
        if "overwrite_distFunc" in kw:
            self.overwrite_distFunc = kw["overwrite_distFunc"]        
        self.proba_binding = 0.5      
        #chance to actually bind to any partner
        self.gradient=""
        if "gradient" in kw :
           self.gradient=kw["gradient"] 
        self.cb = None
        self.radii = None
        self.recipe = None #weak ref to recipe
        
    def getProbaBinding(self,val =None):
        #get a value between 0.0 and 1.0and return the weight and success ?
        if val is None :
            val = random()
        if self.cb is not None :
            return self.cb(val)
        if val <= self.weight :
            return True,val
        else :
            return False,val

    def getPartnerweight(self,name):
        print("Deprecated use self.weight")
        partner = self.getPartner(name)
        w = partner.getProperties("weight")
        if w is not None :
            return w
            
    def getPartnersName(self):
        return list(self.partners.keys())
        
    def getPartner(self,name):
        if name in self.partners:
            return self.partners[name]
        else :
            return None
        
    def addPartner(self, name, weight=0.0, properties=None):
        self.partners[name] = Partner(name, weight=weight, 
                                properties=properties)
        return self.partners[name]
        
    def getExcludedPartnersName(self):
        return list(self.excluded_partners.keys())

    def getExcludedPartner(self, name):
        if name in self.excluded_partners:
            return self.excluded_partners[name]
        else :
            return None

    def addExcludedPartner(self, name, properties=None):
        self.excluded_partners[name] = Partner(name, properties=properties)
         

    def sortPartner(self, listeP=None):
        if listeP is None :
            listeP=[]
            for i,ingr in list(self.partners.keys()):
                listeP.append([i,ingr])
        #extract ing name unic
        listeIngrInstance={}
        for i,ingr in listeP:
            if ingr.name not in listeIngrInstance:
                listeIngrInstance[ingr.name]=[ingr.weight,[]]
            listeIngrInstance[ingr.name][1].append(i)
        #sort according ingrediant binding weight (proba to bind)
        sortedListe = sorted(list(listeIngrInstance.items()), 
                                 key=lambda elem: elem[1][0])   
        #sortedListe is [ingr,(weight,(instances indices))]
        # sort by weight/min->max
        #wIngrList = []
        #for i,ingr in listeP:
            #need to sort by ingr.weight
        #    wIngrList.append([i,ingr,ingr.weight])
        #sortedListe = sorted(wIngrList, key=lambda elem: elem[2])   # sort by weight/min->max
#        print sortedListe
        return sortedListe

    def weightListByDistance(self, listePartner):
        probaArray=[]
        w=0.
        for i,part,dist in listePartner:
            if self.overwrite_distFunc:
                wd = part.weight
            else:
                wd = part.distanceFunction(dist, 
                                           expression=part.distExpression)
#            print "calc ",dist, wd
            probaArray.append(wd)
            w = w+wd
        probaArray.append(self.proba_not_binding)
        w=w+self.proba_not_binding
        return probaArray,w

    def getProbaArray(self, weightD, total):
        probaArray=[]
        final=0.
        for w in weightD:
            p = w/total
#            print "norma ",w,total,p
            final = final + p
            probaArray.append(final)
        probaArray[-1]=1.0
        return probaArray
        
    def pickPartner(self, mingrs, listePartner, currentPos=[0,0,0]):
        #listePartner is (i,partner,d)
        #wieght using the distance function
#        print "len",len(listePartner)
        weightD,total = self.weightListByDistance(listePartner)
#        print "w", weightD,total
        probaArray = self.getProbaArray(weightD,total)
#        print "p",probaArray
        probaArray=numpy.array(probaArray)
        #where is random in probaArray->index->ingr
        b = random() 
        test = b < probaArray
        i = test.tolist().index(True)
#        print "proba",i,test,(len(probaArray)-1)    
        if i == (len(probaArray)-1) :
            #no binding due to proba not binding....
            return None,b
        ing = mingrs[i][2]
        targetPoint= mingrs[i][0]            
        if self.placeType == "rigid-body" or self.placeType == "jitter":
            #the new point is actually tPt -normalise(tPt-current)*radius
            print("tP",targetPoint,ing.radii[0][0])
            print("cP",currentPos)
            v=numpy.array(targetPoint) - numpy.array(currentPos)
            s = numpy.sum(v*v)
            factor = ((v/math.sqrt(s)) * (ing.radii[0][0]+self.radii[0][0]))
            targetPoint =  numpy.array(targetPoint) - factor    
            print("tPa",targetPoint)
        return targetPoint,b
        
    def pickPartner_old(self, mingrs,listePartner, currentPos=[0,0,0]):
        #pick the highest weighted partner
        #pick one instance of this ingrediant 
        #(distance or random or density nb of instance) 
        #roll a dice to decide if bind or not
        #problem where put the cb function
        #listePartner is (i,partner,d)
        sorted_listePartner=self.sortPartner(listePartner)
        #sortedListe is [ingrP,(weight,(instances indices))]
        binding = False
        targetPoint = None
        pickedIngr = None     
        found = False
        safetycutoff=10 #10 roll dice, save most prob
        #do we take the one with highest weight of binding, 
        #or do we choose with a dice
#        p = random()
#        for bindingIngr in sorted_listePartner:
#            if p < part[1][0] :
#                break
        bindingIngr = sorted_listePartner[0]
        #pick the instance random, or distance
        i = self.pickPartnerInstance(bindingIngr, mingrs, 
                                     currentPos=currentPos)
        #roll a dice to see if we bind
        b=random()
        if b < self.proba_binding:
            binding = True
        if binding:
            ing = mingrs[i][2]
            targetPoint= mingrs[i][0]            
            if self.placeType == "rigid-body":
                #the new point is actually 
                #tPt -normalise(tPt-current)*radius
                v=numpy.array(targetPoint) - numpy.array(currentPos)
                s = numpy.sum(v*v)
                factor = ((v/s)* ing.radii[0][0])
                targetPoint = numpy.array(targetPoint) - factor
        return targetPoint,b

    def pickPartnerInstance(self, bindingIngr, mingrs, currentPos=None):
        #bindingIngr is ingr,(weight,(instances indices))
#        print "bindingIngr ",bindingIngr,bindingIngr[1]
        if currentPos is None : #random mode
            picked_I = random()*len(bindingIngr[1][1])
            i = bindingIngr[1][1][picked_I]
        else : #pick closest one
            mind=99999999.9
            i=0
            for ind in bindingIngr[1][1]:
                v=numpy.array(mingrs[ind][0]) - numpy.array(currentPos)
                d = numpy.sum(v*v)
                if d < mind:
                    mind = d
                    i = ind
        return i
                

#the ingrediant should derive from a class of Agent
class Ingredient(Agent):
    """
    Base class for Ingredients that can be added to a Recipe.
    Ingredients provide:
        - a molarity used to compute how many to place
        - a generic density value
        - a unit associated with the density value
        - a jitter amplitude vector specifying by how much the jittering
        algorithm can move fro the grid position.
        - a number of jitter attempts
        - an optional color used to draw the ingredient default (white)
        - an optional name
        - an optional pdb ID
        - an optional packing priority. If omited the priority will be based
        on the radius with larger radii first
        ham here: (-)packingPriority object will pack from high to low one at a time
        (+)packingPriority will be weighted by assigned priority value
        (0)packignPriority will be weighted by complexity and appended to what is left
        of the (+) values
        - an optional princial vector used to align the ingredient
        - recipe will be a weakref to the Recipe this Ingredient belongs to
        - compNum is th compartment number (0 for cyto plasm, positive for organelle
        surface and negative organelle interior
        - Attributes used by the filling algorithm:
        - nbMol counts the number of palced ingredients during a fill
        - counter is the target numbr of ingredients to place
        - completion is the ratio of placxed/target
        - rejectionCounter is used to eliminate ingredients after too many failed
        attempts

    """
    def __init__(self, molarity=0.0, radii=None, positions=None, positions2=None,
                 sphereFile=None, packingPriority=0, name=None, pdb='????', 
                 color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1, principalVector=(1,0,0),
                 meshFile=None, packingMode='random',placeType="jitter",
                 meshObject=None,nbMol=0,Type="MultiSphere",**kw):
        Agent.__init__(self, name, molarity, packingMode=packingMode, 
                       placeType=placeType, **kw)
        self.molarity = molarity
        self.packingPriority = packingPriority
        print (packingPriority,self.packingPriority)
        if name == None:
            name = "%f"% molarity
        self.name = str(name)
        self.Type = Type
        self.pdb = pdb        #pmv ?
        self.color = color    # color used for sphere display
        self.modelType='Spheres'
        self.rRot=[]
        self.tTrans=[]
        self.htrans=[]
        self.moving = None
        self.moving_geom = None
        self.vi = None
        self.minRadius = 0
        self.encapsulatingRadius = 0
        self.maxLevel = 1
        self.is_previous = False
        #self._place = self.place
        children = []
        self.sphereFile = None
        if sphereFile is not None:
            self.sphereFile=sphereFile
            rm, rM, positions, radii, children = getSpheres(sphereFile)
            if not len(radii):
                self.minRadius = 1.0
                self.encapsulatingRadius = 1.0
            else :
                # minRadius is used to compute grid spacing. It represents the
                # smallest radius around the anchor point(i.e. 
                # the point where the
                # ingredient is dropped that needs to be free
                self.minRadius = rm
                # encapsulatingRadius is the radius of the sphere 
                # centered at 0,0,0
                # and encapsulate the ingredient
                self.encapsulatingRadius = rM
            
        elif positions is None or positions[0] is None or positions[0][0] is None:#[0][0]
            positions = [[[0,0,0]]]
            if radii is not None :    
                self.minRadius = [radii[0]]
                self.encapsulatingRadius = [radii[0]]
        else :
            if radii is not None :
                self.minRadius = min(radii[0])
                self.encapsulatingRadius = max(radii[0])
#        print "sphereFile",sphereFile
#        print "positions",positions,len(positions)
#        print "rad",radii,len(radii)
        if radii is not None and positions is not None:
            for r,c in zip(radii, positions):
                assert len(r)==len(c)
        
        if radii is not None :
            self.maxLevel = len(radii)-1
        
        self.radii = radii
        self.positions = positions
        self.positions2 = positions2
        self.children = children
        self.rbnode =  {} #keep the rbnode if any
        self.collisionLevel = self.maxLevel 
        # first level used for collision detection
        self.rejectionThreshold = 30
        self.jitterMax = jitterMax 
        # (1,1,1) means 1/2 grid spacing in all directions
        self.nbJitter = nbJitter 
        # number of jitter attemps for translation

        self.perturbAxisAmplitude = perturbAxisAmplitude
        
        self.principalVector = principalVector

        self.recipe = None # will be set when added to a recipe
        self.compNum = None 
        # will be set when recipe is added to HistoVol 
        #added to a compartment
        self.overwrite_nbMol = False
        self.overwrite_nbMol_value = nbMol
        self.nbMol =  nbMol
        self.vol_nbmol=0
        # used by fill() to count placed molecules,overwrite if !=0
#        if nbMol != 0:
#            self.overwrite_nbMol = True
#            self.overwrite_nbMol_value = nMol
#            self.nbMol = nMol
        self.counter = 0      # target number of molecules for a fill
        self.completion = 0.0 # ratio of counter/nbMol
        self.rejectionCounter = 0
        self.verts=None
        self.rad=None

        #TODO : geometry : 3d object or procedural from PDB
        #TODO : usekeyword resolution->options dictionary of res :
        #TODO : {"simple":{"cms":{"parameters":{"gridres":12}},
        #TODO :            "obj":{"parameters":{"name":"","filename":""}}
        #TODO :            }
        #TODO : "med":{"method":"cms","parameters":{"gridres":30}}
        #TODO : "high":{"method":"msms","parameters":{"gridres":30}}
        #TODO : etc...
        
        self.coordsystem="left"
        if "coordsystem" in kw:
            self.coordsystem = kw["coordsystem"]
        self.meshFile = None
        self.mesh = None
        self.meshObject= None
        if meshFile is not None:
            print ("OK, meshFile is not none, it is = ",meshFile,self.name)
            self.mesh = self.getMesh(meshFile, self.name)
            print ("OK got",self.mesh)
            if self.mesh is None :
                #display a message ?
                print ("no geometrie for ingredient " + self.name)
            #should we reparent it ?
            self.meshFile = meshFile
        elif meshObject is not None:
            self.mesh = meshObject
        self.use_mesh_rb = False
        self.current_resolution="Low"#should come from data
        self.available_resolution=["Low","Med","High"]#0,1,2
        self.resolution_dictionary = {"Low":"","Med":"","High":""}
        if "resolution_dictionary" in kw :
            if kw["resolution_dictionary"] is not None:
                self.resolution_dictionary = kw["resolution_dictionary"]
        self.useRotAxis = False    
        if "useRotAxis" in kw:
            self.useRotAxis = kw["useRotAxis"]
        self.rotAxis = None
        if "rotAxis" in kw:
            self.rotAxis = kw["rotAxis"]
        self.rotRange = 6.2831
        if "rotRange" in kw:
            self.rotRange = kw["rotRange"]
        #cutoff are used for picking point far from surface and boundary
        self.cutoff_boundary = 0
        self.cutoff_surface = 0
        if "cutoff_boundary" in kw:
            self.cutoff_boundary = kw["cutoff_boundary"]
        if "cutoff_surface" in kw:
            self.cutoff_surface = kw["cutoff_surface"]
        
        self.compareCompartment = False
        self.compareCompartmentTolerance = 0
        self.compareCompartmentThreshold = 0.0
        
        self.updateOwnFreePts = False #work for rer python not ??
        self.haveBeenRejected = False
        
        self.distances_temp=[]
        self.centT = None #transformed position

        self.results =[]
        self.KWDS = {   "molarity":{"type":"float"}, 
                        "radii":{"type":"float"}, 
                        "positions":{}, "positions2":{},
                        "sphereFile":{"type":"string"}, 
                        "packingPriority":{"type":"float"}, 
                        "name":{"type":"string"}, 
                        "pdb":{"type":"string"}, 
                        "color":{"type":"vector"},"principalVector":{"type":"vector"},
                        "meshFile":{"type":"string"}, 
                        "coordsystem":{"name":"coordsystem","type":"string","value":"right","default":"right","description":"coordinate system of the files"},
#                        "meshObject":{"type":"string"},
                        "principalVector":{"name":"principalVector","value":[0.,0.,0.],"default":[0.,0.,0.],"min":-1,"max":1,"type":"vector","description":"principalVector"},
                        "nbMol":{"type":"int"},
                        "Type":{"type":"string"},
                        "jitterMax":{"name":"jitterMax","value":[1.,1.,1.],"default":[1.,1.,1.],"min":0,"max":1,"type":"vector","description":"jitterMax"},
                        "nbJitter":{"name":"nbJitter","value":5,"default":5,"type":"int","min":0,"max":50,"description":"nbJitter"},
                        "perturbAxisAmplitude":{"name":"perturbAxisAmplitude","value":0.1,"default":0.1,"min":0,"max":1,"type":"float","description":"perturbAxisAmplitude"},
                        "useRotAxis":{"name":"useRotAxis","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"useRotAxis"},                             
                        "rotAxis":{"name":"rotAxis","value":[0.,0.,0.],"default":[0.,0.,0.],"min":0,"max":1,"type":"vector","description":"rotAxis"},
                        "rotRange":{"name":"rotRange","value":6.2831,"default":6.2831,"min":0,"max":12,"type":"float","description":"rotRange"},
                        "cutoff_boundary":{"name":"cutoff_boundary","value":1.0,"default":1.0,"min":0.,"max":50.,"type":"float","description":"cutoff_boundary"},
                        "cutoff_surface":{"name":"cutoff_surface","value":5.0,"default":5.0,"min":0.,"max":50.,"type":"float","description":"cutoff_surface"},
                        "placeType":{"name":"placeType","value":"jitter","values":AutoFill.LISTPLACEMETHOD,"min":0.,"max":0.,
                                        "default":"jitter","type":"liste","description":"placeType"},
                        "use_mesh_rb":{"name":"use_mesh_rb","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"use mesh for collision"},                             
                        
                        "packingMode":{"name":"packingMode","value":"random","values":['random', 'close', 'closePartner',
                               'randomPartner', 'gradient'],"min":0.,"max":0.,"default":'random',"type":"liste","description":"packingMode"},
                        "gradient":{"name":"gradient","value":"","values":[],"min":0.,"max":0.,
                                        "default":"jitter","type":"liste","description":"gradient name to use if histo.use_gradient"},
}
        self.OPTIONS = {
                        "molarity":{}, 
                        "radii":{}, 
                        "positions":{}, "positions2":{},
                        "sphereFile":{}, 
                        "packingPriority":{}, "name":{}, "pdb":{}, 
                        "color":{},
                        "principalVector":{"name":"principalVector","value":[0.,0.,0.],"default":[0.,0.,0.],"min":-1,"max":1,"type":"vector","description":"principalVector"},
                        "meshFile":{}, "meshObject":{},"nbMol":{},
                        "coordsystem":{"name":"coordsystem","type":"string","value":"right","default":"right","description":"coordinate system of the files"},
                        "use_mesh_rb":{"name":"use_mesh_rb","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"use mesh for collision"},                             
                        "rejectionThreshold":{"name":"rejectionThreshold","value":30,"default":30,"type":"int","min":0,"max":10000,"description":"rejectionThreshold"},
                        "jitterMax":{"name":"jitterMax","value":[1.,1.,1.],"default":[1.,1.,1.],"min":0,"max":1,"type":"vector","description":"jitterMax"},
                        "nbJitter":{"name":"nbJitter","value":5,"default":5,"type":"int","min":0,"max":50,"description":"nbJitter"},
                        "perturbAxisAmplitude":{"name":"perturbAxisAmplitude","value":0.1,"default":0.1,"min":0,"max":1,"type":"float","description":"perturbAxisAmplitude"},
#                         "principalVector":{"name":"principalVector","value":9999999,"default":99999999,"type":"vector_norm","description":"principalVector"},
                        "useRotAxis":{"name":"useRotAxis","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"useRotAxis"},                             
                        "rotAxis":{"name":"rotAxis","value":[0.,0.,0.],"default":[0.,0.,0.],"min":0,"max":1,"type":"vector","description":"rotAxis"},
                        "rotRange":{"name":"rotRange","value":6.2831,"default":6.2831,"min":0,"max":12,"type":"float","description":"rotRange"},
                        "packingMode":{"name":"packingMode","value":"random","values":['random', 'close', 'closePartner',
                               'randomPartner', 'gradient'],"min":0.,"max":0.,"default":'random',"type":"liste","description":"packingMode"},
                        "placeType":{"name":"placeType","value":"jitter","values":AutoFill.LISTPLACEMETHOD,"min":0.,"max":0.,
                                        "default":"jitter","type":"liste","description":"placeType"},
                        "gradient":{"name":"gradient","value":"","values":[],"min":0.,"max":0.,
                                        "default":"jitter","type":"liste","description":"gradient name to use if histo.use_gradient"},
                        "isAttractor":{"name":"isAttractor","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"isAttractor"},
                        "weight":{"name":"weight","value":0.2,"default":0.2,"min":0.,"max":50.,"type":"float","description":"weight"},
                        "proba_binding":{"name":"proba_binding","value":0.5,"default":0.5,"min":0.,"max":1.0,"type":"float","description":"proba_binding"},
                        "proba_not_binding":{"name":"proba_not_binding","value":0.5,"default":0.5,"min":0.0,"max":1.,"type":"float","description":"proba_not_binding"},
                        "cutoff_boundary":{"name":"cutoff_boundary","value":1.0,"default":1.0,"min":0.,"max":50.,"type":"float","description":"cutoff_boundary"},
                        "cutoff_surface":{"name":"cutoff_surface","value":5.0,"default":5.0,"min":0.,"max":50.,"type":"float","description":"cutoff_surface"},
                        "compareCompartment":{"name":"compareCompartment","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"compareCompartment"},
                        "compareCompartmentTolerance":{"name":"compareCompartmentTolerance","value":0.0,"default":0.0,"min":0.,"max":1.0,"type":"float","description":"compareCompartmentTolerance"},
                        "compareCompartmentThreshold":{"name":"compareCompartmentThreshold","value":0.0,"default":0.0,"min":0.,"max":1.0,"type":"float","description":"compareCompartmentThreshold"},
                        }

    
                        
    def Set(self,**kw):
        self.nbMol = 0   
        if "nbMol" in kw :
            nbMol = kw["nbMol"]
#            if nbMol != 0:
#                self.overwrite_nbMol = True
#                self.overwrite_nbMol_value = nbMol
#                self.nbMol = nbMol
#            else :
#                self.overwrite_nbMol =False
            self.overwrite_nbMol_value = nbMol
            self.nbMol = nbMol
        if "molarity" in kw :
            self.molarity  = kw["molarity"]  
        if "priority" in kw :
            self.packingPriority = kw["priority"]
        if "packingMode" in kw :
            self.packingMode = kw["packingMode"]
            
    def getMesh(self, filename, geomname):
        """
        Create a mesh representaton from a filename for the ingredient
    
        @type  filename: string
        @param filename: the name of the input file
        @type  geomname: string
        @param geomname: the name of the ouput geometry
    
        @rtype:   DejaVu.IndexedPolygons/HostObjec
        @return:  the created mesh  
        """
        #depending the extension of the filename, can be eitherdejaVu file, fbx or wavefront
        #no extension is DejaVu
        helper = AutoFill.helper
        reporthook = None
        if helper is not None:        
            reporthook=helper.reporthook
#        print('TODO: getMesh need safety check for no internet connection')
#        print ("helper in Ingredient is "+str(helper))
        #should wetry to see if it already exist inthescene 
        if helper is not None:
            o = helper.getObject(geomname)
            print ("retrieve ",geomname,o)
            if o is not None :
                return o
        if filename.find("http") != -1 or filename.find("ftp")!= -1 :
            try :
                import urllib.request as urllib# , urllib.parse, urllib.error
            except :
                import urllib
            name =   filename.split("/")[-1]
            fileName, fileExtension = os.path.splitext(name)
            tmpFileName = AFDIR+os.sep+"cache_ingredients"+os.sep+name
#            print("try to get from cache "+name+" "+fileExtension,fileExtension.find(".fbx"),fileExtension.find(".dae"))
            if fileExtension is '' :            
#            if fileExtension.find(".fbx") == -1 and fileExtension.find(".dae") == -1:
                #need to getboth file
                tmpFileName1 = AFDIR+os.sep+"cache_ingredients"+os.sep+name+".indpolface"
                tmpFileName2 = AFDIR+os.sep+"cache_ingredients"+os.sep+name+".indpolvert"
#                print("#check if exist first1",tmpFileName1)
                #check if exist first
                if not os.path.isfile(tmpFileName1) or AutoFill.forceFetch:
                    if checkURL(filename+".indpolface"):
                        try :
                            urllib.urlretrieve(filename+".indpolface", tmpFileName1,reporthook=reporthook)
                        except :
                            print ("problem downloading "+filename+".indpolface to"+tmpFileName1)
                    else : 
                        print ("problem downloading "+filename+".indpolface to"+tmpFileName1)
                        if not os.path.isfile(tmpFileName1): return
                if not os.path.isfile(tmpFileName2) or AutoFill.forceFetch:
                    if checkURL(filename+".indpolvert"):
                        try :
                            urllib.urlretrieve(filename+".indpolvert", tmpFileName2,reporthook=reporthook)
                        except :
                            print ("problem downloading "+filename+".indpolface to"+tmpFileName2)
                    else : 
                        print ("problem downloading "+filename+".indpolface to"+tmpFileName1)
                        if not os.path.isfile(tmpFileName2): return
            else :
                tmpFileName = AFDIR+os.sep+"cache_ingredients"+os.sep+name
#                print("#check if exist first",tmpFileName,os.path.isfile(tmpFileName))
                if not os.path.isfile(tmpFileName) or AutoFill.forceFetch:
#                    print("urlretrieve and fetch")
                    if checkURL(filename):
                        urllib.urlretrieve(filename, tmpFileName,reporthook=reporthook)#hook_cb ->progress bar TODO
                    else :
                        print ("problem downloading "+filename)
                        if not os.path.isfile(tmpFileName):
                            return
            filename = tmpFileName 
        fileName, fileExtension = os.path.splitext(filename)
        print('found fileName '+fileName+' fileExtension '+fileExtension)
        if fileExtension.lower() == ".fbx" :
#            print ("read fbx withHelper",filename,helper,AutoFill.helper)
            #use the host helper if any to read
            if helper is not None:#neeed the helper
#                print "read "+filename
                helper.read(filename)
#                print "try to get the object "+geomname
                geom = helper.getObject(geomname)
                print ("geom ",geom,geomname,helper.getName(geom))
                #reparent to the fill parent
                if helper.host == "3dsmax" :
                    helper.resetTransformation(geom)#remove rotation and scale from importing
                    #helper.rotateObj(geom,[0.0,0.0,-math.pi/2.0])
                    #m = geom.GetNodeTM()
                    #m.PreRotateY(-math.pi/2.0)
                    #geom.SetNodeTM(m)
                if helper.host != "c4d" and self.coordsystem == "left":
                    #need to rotate the transform that carry the shape
                    helper.rotateObj(geom,[0.,-math.pi/2.0,0.0])
                if helper.host =="softimage" and self.coordsystem == "left" and helper.host != "softimage":
                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0],primitive=True)#need to rotate the primitive                    
#                if helper.host == "c4d" and self.coordsystem == "left":
#
#                    oldv = self.principalVector[:]
#                    self.principalVector = [oldv[2],oldv[1],oldv[0]]
                p=helper.getObject("AutoFillHider")
                if p is None:
                    p = helper.newEmpty("AutoFillHider")
                    if helper.host.find("blender") == -1 :
                        helper.toggleDisplay(p,False)
                helper.reParent(geom,p)
                return geom
            return None
        elif fileExtension == ".dae":
            print ("read dae withHelper",filename,helper,AutoFill.helper)
            #use the host helper if any to read
            if helper is not None:#neeed the helper
                helper.read(filename)
                geom = helper.getObject(geomname)
                print ("should have read...",geomname,geom)
#                helper.update()
                #rotate ?
                if helper.host == "3dsmax" :
                    helper.resetTransformation(geom)#remove rotation and scale from importing??maybe not?
                if helper.host != "c4d"  and helper.host != "dejavu" and self.coordsystem == "left" and helper.host != "softimage":#and helper.host.find("blender") == -1:
                    #what about softimage
                    #need to rotate the transform that carry the shape, maya ? or not ?
                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0])#wayfront as well euler angle
                    #swicth the axe?
#                    oldv = self.principalVector[:]
#                    self.principalVector = [oldv[2],oldv[1],oldv[0]]
                if helper.host =="softimage" and self.coordsystem == "left" :
                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0],primitive=True)#need to rotate the primitive
                p=helper.getObject("AutoFillHider")
                if p is None:
                    p = helper.newEmpty("AutoFillHider")
                    if helper.host.find("blender") == -1 :
                        helper.toggleDisplay(p,False)
                helper.reParent(geom,p)            
                return geom
            return None
        elif fileExtension is '' :
            return self.getDejaVuMesh(filename, geomname)
        else :#host specific file
            if helper is not None:#neeed the helper
                helper.read(filename)
                geom = helper.getObject(geomname)
                print ("should have read...",geomname,geom)
                p=helper.getObject("AutoFillHider")
                if p is None:
                    p = helper.newEmpty("AutoFillHider")
                    if helper.host.find("blender") == -1 :helper.toggleDisplay(p,False)
                helper.reParent(geom,p)            
                return geom
            return None
            
        
    def getDejaVuMesh(self, filename, geomname):
        """
        Create a DejaVu polygon mesh object from a filename 
    
        @type  filename: string
        @param filename: the name of the input file
        @type  geomname: string
        @param geomname: the name of the ouput geometry
    
        @rtype:   DejaVu.IndexedPolygons
        @return:  the created dejavu mesh  
        """
        #filename or URL
        from DejaVu.IndexedPolygons import IndexedPolygonsFromFile
        #seems not ok...when they came from c4d ... some transformation are not occuring.
#        print ("dejavu mesh", filename)        
        geom = IndexedPolygonsFromFile(filename, 'mesh_%s'%self.pdb)
#        if helper is not None:
#            if helper.host != "maya" :
#                helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0])
        return geom


    def jitterPosition(self, position, spacing):
        """
        position are the 3d coordiantes of the grid point
        spacing is the grid spacing
        this will jitter gauss(0., 0.3) * Ingredient.jitterMax
        """
        jx, jy, jz = self.jitterMax
        dx = jx*gauss(0., 0.3)
        dy = jy*gauss(0., 0.3)
        dz = jz*gauss(0., 0.3)
        d2 = dx*dx + dy*dy + dz*dz
        position[0] += dx
        position[1] += dy
        position[2] += dz
        return position


    def getMaxJitter(self, spacing):
        return max(self.jitterMax)*spacing


##     def checkCollisions(self, pt, radius, pointsInCube, gridPointsCoords,
##                         distance, verbose):
##         insidePoints = {}
##         newDistPoints = {}
##         x, y, z = pt
##         for pt in pointsInCube:
##             x1,y1,z1 = gridPointsCoords[pt]
##             dist = sqrt((x1-x)*(x1-x) + (y1-y)*(y1-y) + (z1-z)*(z1-z))
##             d = dist-radius
##             if dist < radius:  # point is inside dropped sphere
##                 if distance[pt]<-0.0001:
##                     return None, None, pt
##                 else:
##                     if insidePoints.has_key(pt):
##                         if d < insidePoints[pt]:
##                             insidePoints[pt] = d
##                     else:
##                         insidePoints[pt] = d

##             else: # update distance is smaller that existing distance
##                 if d < distance[pt]:
##                     if newDistPoints.has_key(pt):
##                         if d < newDistPoints[pt]:
##                             newDistPoints[pt] = d
##                     else:
##                         newDistPoints[pt] = d

##                     if verbose > 5:
##                         print 'point ',pt, 'going from ', \
##                               distance[pt],'to', dist

##         return insidePoints, newDistPoints, None

    def swap(self,d, n):
        d.rotate(-n)
        d.popleft()
        d.rotate(n)

    def deleteblist(self,d, n):
        del d[n]

    def getDistancesCube(self,jtrans, rotMat,gridPointsCoords, distance, grid):
        radii = self.radii        
        insidePoints = {}
        newDistPoints = {}
        cent1T = self.transformPoints(jtrans, rotMat, self.positions[0])[0]#bb1
        cent2T = self.transformPoints(jtrans, rotMat, self.positions2[0])[0]#bb2
        center = self.transformPoints(jtrans, rotMat, [self.center,])[0]
        cylNum = 0
#        for radc, p1, p2 in zip(radii, cent1T, cent2T):
        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
        lengthsq = vx*vx + vy*vy + vz*vz
        l = sqrt( lengthsq )
        cx, cy, cz = posc = center#x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = l/2. + self.encapsulatingRadius
        
        bb = [cent2T,cent1T]#self.correctBB(p1,p2,radc)
        x,y,z = posc
        bb = ( [x-radt, y-radt, z-radt], [x+radt, y+radt, z+radt] )
#        print ("pointsInCube",bb,posc,radt)        
        pointsInGridCube = grid.getPointsInCube(bb, posc, radt)
        
        # check for collisions with cylinder    
        pd = numpy.take(gridPointsCoords,pointsInGridCube,0)-center
        
        delta = pd.copy()        
        delta *= delta
        distA = numpy.sqrt( delta.sum(1) )
        
        m = numpy.matrix(numpy.array(rotMat).reshape(4,4))#
        mat = m.I
        #need to apply inverse mat to pd
        rpd = ApplyMatrix(pd,mat)
        #need to check if these point are inside the cube using the dimension of the cube
        #numpy.fabs        
        res = numpy.less_equal(numpy.fabs(rpd),numpy.array(radii[0])/2.)
        if len(res) :
            c=numpy.average(res,1)#.astype(int)
            d=numpy.equal(c,1.)
            ptinsideCube = numpy.nonzero(d)[0]
        else :
            ptinsideCube = []
        for pti in range(len(pointsInGridCube)):#ptinsideCube:#inside point but have been already computed during the check collision...?
            pt = pointsInGridCube[pti]
            if pt in insidePoints: continue
            dist = distA[pti]
            d = dist-self.encapsulatingRadius #should be distance to the cube, but will use approximation
            if pti in ptinsideCube:# dist < radt:  # point is inside dropped sphere
                if pt in insidePoints:
                    if d < insidePoints[pt]:
                        insidePoints[pt] = d
                else:
                    insidePoints[pt] = d
            elif d < distance[pt]: # point in region of influence
                if pt in newDistPoints:
                    if d < newDistPoints[pt]:
                        newDistPoints[pt] = d
                else:
                    newDistPoints[pt] = d
        return insidePoints,newDistPoints

                
    def updateDistances(self, histoVol,insidePoints, newDistPoints, freePoints,
                        nbFreePoints, distance, masterGridPositions, verbose):
#        print("*************updating Distances")
        verbose = histoVol.verbose
        t1 = time()
        distChanges = {}
        self.nbPts = len(insidePoints)
#        print("nbPts = len(insidePoints) = ", self.nbPts)
#        print("nbFreePoints = ", nbFreePoints)
#        print("lenFreePoints = ", len(freePoints))
#        fptCount = 0
#        for val1 in freePoints:
#            print("FreePoint[",fptCount,"] = ", freePoints[fptCount]," = val1 = ", val1)
#            fptCount += 1
        for pt,dist in list(insidePoints.items()):  #Reversing is not necessary if you use the correct Swapping GJ Aug 17,2012
            #        for pt,dist in reversed(list(insidePoints.items()) ):  # GJ notes (August 17, 2012): Critical to reverse 
            # or points that need to get masked towards the end get used incorrectly as valid points during forward swap
            # Reversing the walk through the masked points cures this! 
            # swap reverse point at ptIndr with last free one
            # pt is the grid point indice not the freePt indice
#            try :
#                fi = freePoints.index(pt)#too slow
#            except :
#                pass
            try :
                # New system replaced by Graham on Aug 18, 2012
                nbFreePoints -= 1  
                vKill = freePoints[pt]
                vLastFree = freePoints[nbFreePoints]
                freePoints[vKill] = vLastFree
                freePoints[vLastFree] = vKill
                # End New replaced by Graham on Aug 18, 2012
            # Start OLD system replaced by Graham on Aug 18, 2012. This has subtle problems of improper swapping
            #                tmp = freePoints[nbFreePoints-1] #last one
            #                #freePoints.remove(pt)
            #                freePoints[nbFreePoints-1] = pt
            #                tmpDebug2 = freePoints[freePoints[pt]]
            ##                freePoints[nbFreePoints-1] = freePoints[pt]
            #                freePoints[freePoints[pt]] = tmp
            #                nbFreePoints -= 1
            # End OLD system replaced by Graham on Aug 18, 2012. This has subtle problems of improper swapping
            except :
#                print (pt, "not in freeePoints********************************")
                pass 
    
        #Turn on these printlines if there is a problem with incorrect points showing in display points        
#            print("*************pt = masterGridPointValue = ", pt)
#            print("nbFreePointAfter = ", nbFreePoints)    
#            print("vKill = ", vKill)
#            print("vLastFree = ", vLastFree)
#            print("freePoints[vKill] = ", freePoints[vKill])
#            print("freePoints[vLastFree] = ", freePoints[vLastFree])
#            print("pt = masterGridPointValue = ", pt)
#            print("freePoints[nbFreePoints-1] = ", freePoints[nbFreePoints])
#            print("freePoints[pt] = ", freePoints[pt])
                
            
            distChanges[pt] = (masterGridPositions[pt],
                               distance[pt], dist)
            distance[pt] = dist
#            print("distance[pt] = ", distance[pt])
#            print("distChanges[pt] = ", distChanges[pt])

                #self.updateDistanceForOther(pt=pt)
        if verbose >4:       
            print("update freepoints loop",time()-t1)
        if verbose >5:
            print(nbFreePoints)
        t2 = time()
        for pt,dist in list(newDistPoints.items()):
            if pt not in insidePoints:
                distChanges[pt] = (masterGridPositions[pt],
                                   distance[pt], dist)
                distance[pt] = dist                    
            #self.updateDistanceForOther(pt=pt,dist=dist)
        #hack c4d particle
        if verbose==0.4: 
            print("update distance loop",time()-t2)
        #bitmaps.ShowBitmap(bmp)
        #bmp.Save(name,c4d.FILTER_TIF)
        
            
        return nbFreePoints
        
#   DEPRECRATED FUNCTION
#    def updateDistanceForOther(self,pt=None,dist=None):
#        #return
#        r = self.recipe()#stored_recipe it is  weakref
#        for ingr in r.ingredients:
#            if hasattr(ingr,"allIngrPts") and ingr.updateOwnFreePts:
#                if dist is not None and dist  < ingr.cut :
#                    try :
#                        n = histoVol.lmethod.swap_value(ingr.allIngrPts,pt)
#                        ingr.NI = n
#                        #ingr.allIngrPts.remove(pt)
#                        #del ingr.allIngrPts[pt]
#                    except :
#                        pass
#                else :
#                    try :
#                        n = histoVol.lmethod.swap_value(ingr.allIngrPts,pt)
#                        ingr.NI = n
#                        #ingr.allIngrPts.remove(pt)
#                        #del ingr.allIngrPts[pt]
#                    except :
#                        pass
                

    def perturbAxis(self, amplitude):
        # modify axis using gaussian distribution but clamp
        # at amplitutde
        x,y,z = self.principalVector
        stddev = amplitude *.5
        dx = gauss(0., stddev)
        if dx>amplitude: dx = amplitude
        elif dx<-amplitude: dx = -amplitude
        dy = gauss(0., stddev)
        if dy>amplitude: dy = amplitude
        elif dy<-amplitude: dy = -amplitude
        dz = gauss(0., stddev)
        if dz>amplitude: dz = amplitude
        elif dz<-amplitude: dz = -amplitude
        #if self.name=='2bg9 ION CHANNEL/RECEPTOR':
        #    print 'FFFFFFFFFFFFF AXIS', x+dx,y+dy,z+dz
        return (x+dx,y+dy,z+dz)


    def transformPoints(self, trans, rot, points):
        if helper is not None :
            rot[:3,:3] = trans
            return helper.ApplyMatrix(points,rot)
        tx,ty,tz = trans
        pos = []
        for xs,ys,zs in points:
            x = rot[0][0]*xs + rot[0][1]*ys + rot[0][2]*zs + tx
            y = rot[1][0]*xs + rot[1][1]*ys + rot[1][2]*zs + ty
            z = rot[2][0]*xs + rot[2][1]*ys + rot[2][2]*zs + tz
            pos.append( [x,y,z] )
        return pos


    def getAxisRotation(self, rot):
        """
        combines a rotation about axis to incoming rot
        """
        if self.perturbAxisAmplitude!=0.0:
            axis = self.perturbAxis(self.perturbAxisAmplitude)
        else:
            axis = self.principalVector
        tau = uniform(-pi, pi)
        rrot = rotax( (0,0,0), axis, tau, transpose=1 )
        rot = numpy.dot(rot, rrot)

        return rot


    def correctBB(self,p1,p2,radc):
        #unprecised
        x1,y1,z1=p1
        x2,y2,z2=p2
#        bb = ( [x1-radc, y1-radc, z1-radc], [x2+radc, y2+radc, z2+radc] )
        mini=[]
        maxi=[]
        for i in range(3):
            mini.append(min(p1[i],p2[i])-radc)
            maxi.append(max(p1[i],p2[i])+radc)
        return numpy.array([numpy.array(mini).flatten(),numpy.array(maxi).flatten()])
        #precised:
#        kx=sqrt(((A.Y-B.Y)^2+(A.Z-B.Z)^2)/((A.X-B.X)^2+(A.Y-B.Y)^2+(A.Z-B.Z)^2))
#        ky=sqrt(((A.X-B.X)^2+(A.Z-B.Z)^2)/((A.X-B.X)^2+(A.Y-B.Y)^2+(A.Z-B.Z)^2))
#        kz=sqrt(((A.X-B.X)^2+(A.Y-B.Y)^2)/((A.X-B.X)^2+(A.Y-B.Y)^2+(A.Z-B.Z)^2))

    def checkDistSurface(self,point,cutoff):
        if not hasattr(self,"histoVol") :
            return False
        if self.compNum == 0 :
            organelle = self.histoVol
        else :
            organelle = self.histoVol.organelles[abs(self.compNum)-1]
        compNum = self.compNum
#        print "compNum ",compNum
        if compNum < 0 :
            sfpts = organelle.surfacePointsCoords
            delta = numpy.array(sfpts)-numpy.array(point)
            delta *= delta
            distA = numpy.sqrt( delta.sum(1) )
#            print len(distA)
            test = distA < cutoff
            if True in test:
                return True
        elif compNum == 0 :
            for o in self.histoVol.organelles:
                sfpts = o.surfacePointsCoords
                delta = numpy.array(sfpts)-numpy.array(point)
                delta *= delta
                distA = numpy.sqrt( delta.sum(1) )
#                print len(distA)
                test = distA < cutoff
                if True in test:
                    return True
        return False
        
    def getListCompFromMask(self,cId,ptsInSphere):
        #cID ie [-2,-1,-2,0...], ptsinsph = [519,300,etc]
        current = self.compNum
        if current < 0 : #inside
            mask = ["self"] #authorize in and surf
            ins=[i for i,x in enumerate(cId) if x == current]
            #surf=[i for i,x in enumerate(cId) if x == -current]
            liste = ins#+surf
        if current > 0 :#surface
            mask = ["self","neg"] #authorize in and surf and extra but not ther organelle
            ins=[i for i,x in enumerate(cId) if x == current]
            surf=[i for i,x in enumerate(cId) if x == -current]
            extra=[i for i,x in enumerate(cId) if x < 0]
            liste = ins+surf+extra         
        elif current == 0 :#extracellular
            mask = ["self"]
            liste=[i for i,x in enumerate(cId) if x == current]
        return liste

    def isInGoodComp(self,pId,nbs=None):
        #cID ie [-2,-1,-2,0...], ptsinsph = [519,300,etc]
        current = self.compNum
        cId = self.histoVol.grid.gridPtId[pId]
        if current <= 0 : #inside
            if current != cId :
                return False
            return True
        if current > 0 :#surface
            if current != cId and -current != cId :  
                return False
            return True
        return False

    def checkCompartmentAlternative(self,ptsId,histoVol,nbs=None):
        compIds = numpy.take(histoVol.grid.gridPtId,ptsId,0)  
#        print "compId in listPtId",compIds
        if self.compNum <= 0 :
            wrongPt = [ cid for cid in compIds if cid != self.compNum ]
            if len(wrongPt):
#                print wrongPt
                return True
        return False
        
    def checkCompartment(self,ptsInSphere,nbs=None):
        trigger = False
#        print ("checkCompartment using",len(ptsInSphere))
#        print (ptsInSphere)
        if self.compareCompartment:
            cId = numpy.take(self.histoVol.grid.gridPtId,ptsInSphere,0)#shoud be the same ?
            if nbs != None:
                print ("cId ",cId,ptsInSphere)
                if self.compNum <= 0 and nbs != 0 :
                    return trigger,True                               
            L = self.getListCompFromMask(cId,ptsInSphere)
            
            print ("liste",L)
            if len(cId) <= 1 :
                return trigger,True
            p = float(len(L))/float(len(cId))#ratio accepted compId / totalCompId-> want 1.0
            if p < self.compareCompartmentTolerance:
                print ("the ratio is ",p, " threshold is ",self.compareCompartmentThreshold," and tolerance is ",self.compareCompartmentTolerance)
                trigger = True
                return trigger,True
            #threshold
            if self.compareCompartmentThreshold != 0.0 and \
                p < self.compareCompartmentThreshold:
                    return trigger,True
                        #reject the ingr
        return trigger,False

    def checkCylCollisions(self, centers1, centers2, radii, jtrans, rotMat,
                           gridPointsCoords, distance, histoVol):
        """
        Check cylinders for collision
        """
#        print "#######################"
#        print jtrans
#        print rotMat
        cent1T = self.transformPoints(jtrans, rotMat, centers1)
        cent2T = self.transformPoints(jtrans, rotMat, centers2)

        cylNum = 0
        for radc, p1, p2 in zip(radii, cent1T, cent2T):
            if histoVol.runTimeDisplay > 1:
                name = "cyl"
                cyl = self.vi.getObject("cyl")
                if cyl is None:
                    cyl=self.vi.oneCylinder(name,p1,p2,
                                            color=(1.,1.,1.),
                                            radius=radc)
#                    self.vi.updateTubeMesh(cyl,cradius=radc)
                else :
                    self.vi.updateOneCylinder(cyl,p1,p2,radius=radc)
                self.vi.changeObjColorMat(cyl,(1.,1.,1.))
                name = "sph1"
                sph1 = self.vi.getObject("sph1")
                if sph1 is None:
                    sph1=self.vi.Sphere(name,radius=radc*2.)[0]
                self.vi.setTranslation(sph1,p1)
                name = "sph2"
                sph2 = self.vi.getObject("sph2")
                if sph2 is None:
                    sph2=self.vi.Sphere(name,radius=radc*2.)[0]
                self.vi.setTranslation(sph2,p2)
 
                self.vi.update()
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
            lengthsq = vx*vx + vy*vy + vz*vz
            l = sqrt( lengthsq )
            cx, cy, cz = posc = x1+vx*.5, y1+vy*.5, z1+vz*.5
            radt = l + radc
            
            bb = self.correctBB(p1,p2,radc)
#            bb = self.correctBB(posc,posc,radt)
            if histoVol.runTimeDisplay > 1:
                box = self.vi.getObject("collBox")
                if box is None:
                    box = self.vi.Box('collBox', cornerPoints=bb,visible=1)
                else :
#                    self.vi.toggleDisplay(box,True)
                    self.vi.updateBox(box,cornerPoints=bb)
                    self.vi.update()
#                 sleep(1.0)
            pointsInCube = histoVol.getPointsInCube(bb, posc, radt,info=True)
            
            # check for collisions with cylinder            
            pd = numpy.take(gridPointsCoords,pointsInCube,0)-p1
            dotp = numpy.dot(pd, vect)
            rad2 = radc*radc
            dsq = numpy.sum(pd*pd, 1) - dotp*dotp/lengthsq

            ptsWithinCaps = numpy.nonzero( numpy.logical_and(
               numpy.greater_equal(dotp, 0.), numpy.less_equal(dotp, lengthsq)))
#            if not len(ptsWithinCaps[0]):
#                print "no point inside the geom?"
#                return False
            if self.compareCompartment:
                ptsInSphereId = numpy.take(pointsInCube,ptsWithinCaps[0],0)
                compIdsSphere = numpy.take(histoVol.grid.gridPtId,ptsInSphereId,0)  
#                print "compId",compIdsSphere
                if self.compNum <= 0 :
                    wrongPt = [ cid for cid in compIdsSphere if cid != self.compNum ]
                    if len(wrongPt):
#                        print wrongPt
                        return True                
#            trigger, res = self.checkCompartment(numpy.take(pointsInCube,ptsWithinCaps[0],0),nbs=nbs)
#            print ("checkCompartment result",trigger, res)
#            if res :
                #reject
#                return True
            
            for pti in ptsWithinCaps[0]:
                pt = pointsInCube[pti]
                dist = dsq[pti]
                if dist > rad2: continue # outside radius
                elif distance[pt]<-0.0001 :#or trigger: # pt is inside cylinder
                    #changeObjColorMat
                    if histoVol.runTimeDisplay > 1:
                        self.vi.changeObjColorMat(cyl,(1.,0.,0.))
                        self.vi.update()
#                        sleep(1.0)
                    #reject
                    return True
            cylNum += 1
        return False

    def checkCylCompart(self, centers1, centers2, radii, jtrans, rotMat,
                           gridPointsCoords, distance, histoVol):
        """
        Check cylinders for collision
        """
#        print "#######################"
#        print jtrans
#        print rotMat
        cent1T = self.transformPoints(jtrans, rotMat, centers1)
        cent2T = self.transformPoints(jtrans, rotMat, centers2)

        cylNum = 0
        for radc, p1, p2 in zip(radii, cent1T, cent2T):
            x1, y1, z1 = p1
            x2, y2, z2 = p2
            vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
            lengthsq = vx*vx + vy*vy + vz*vz
            l = sqrt( lengthsq )
            cx, cy, cz = posc = x1+vx*.5, y1+vy*.5, z1+vz*.5
            radt = l + radc
            
            bb = self.correctBB(p1,p2,radc)
            pointsInCube = histoVol.getPointsInCube(bb, posc, radt,info=True)
            
            # check for collisions with cylinder            
            pd = numpy.take(gridPointsCoords,pointsInCube,0)-p1
            dotp = numpy.dot(pd, vect)
            rad2 = radc*radc
            dsq = numpy.sum(pd*pd, 1) - dotp*dotp/lengthsq
            ptsWithinCaps = numpy.nonzero( numpy.logical_and(
               numpy.greater_equal(dotp, 0.), numpy.less_equal(dotp, lengthsq)))

            ptsInSphereId = numpy.take(pointsInCube,ptsWithinCaps[0],0)
            compIdsSphere = numpy.take(histoVol.grid.gridPtId,ptsInSphereId,0)  
            if self.compNum <= 0 :
                    wrongPt = [ cid for cid in compIdsSphere if cid != self.compNum ]
                    if len(wrongPt):
#                        print wrongPt
                        return True
            cylNum += 1
        return False

    def checkSphCollisions(self, centers, radii, jtrans, rotMat, level,
                        gridPointsCoords, distance, histoVol):
        """
        Check spheres for collision
        """

        self.centT = centT = self.transformPoints(jtrans, rotMat, centers)#this should be jtrans
#        print "sphCollision",centT,radii
        sphNum = 0
        self.distances_temp=[]
        if self.compareCompartment:
            listeCpmNum=[]
        for radc, posc in zip(radii, centT):
            r=[]
            x,y,z = posc
            bb = ( [x-radc, y-radc, z-radc], [x+radc, y+radc, z+radc] )
#            if histoVol.runTimeDisplay:
#                box = self.vi.getObject("collBox")
#                if box is None:
#                    box = self.vi.Box('collBox', cornerPoints=bb,visible=1)
#                else :
##                    self.vi.toggleDisplay(box,True)
#                    self.vi.updateBox(box,cornerPoints=bb)
#                    self.vi.update()
            pointsInCube = histoVol.getPointsInCube(bb, posc, radc,info=True)#indices
            r.append(pointsInCube)
            
#            print("boundingBox forPointsInCube = ", bb)
#            print "boudnig",bb,len(pointsInCube)
            # check for collisions
            delta = numpy.take(gridPointsCoords,pointsInCube,0)-posc
            delta *= delta
            distA = numpy.sqrt( delta.sum(1) )
            ptsInSphere = numpy.nonzero(numpy.less_equal(distA, radc))[0]
            r.append(ptsInSphere)
            r.append(distA)
            self.distances_temp.append(r)
#            print ("nbPts in sphere",len(ptsInSphere))
#            print ("ptsInSphere = ", ptsInSphere)
#            for pt2 in ptsInSphere:
#                print("ptsInSphere[",pt2,"] = ", pointsInCube[pt2])
#            print ("pointsInCube[pti] = ", pointsInCube)
            #compareComp
#            if not len(ptsInSphere):
#                print "no point inside the geom?"
#                return True
            ptsInSphereId = numpy.take(pointsInCube,ptsInSphere,0)
            if self.compareCompartment:
                compIdsSphere = numpy.take(histoVol.grid.gridPtId,ptsInSphereId,0)  
#                print "compId in sphere",compIdsSphere
                if self.compNum <= 0 :
                    wrongPt = [ cid for cid in compIdsSphere if cid != self.compNum ]
                    if len(wrongPt):
#                        print wrongPt
                        return True
#            trigger, res = self.checkCompartment(ptsInSphereId,nbs=nbs)            
##            print ("checkCompartment result trigger and res",trigger, res)
#            if res :
#                return True
            for pti in ptsInSphere:
                pt = pointsInCube[pti]
                dist = distA[pti]
                d = dist-radc
                #print dist,d,radc,distance[pt]
#                if dist < radc:  # point is inside dropped sphere
#                if self.compareCompartment:
#                    if not self.isInGoodComp(pt):
#                        return True
                if distance[pt]<-0.0001:# or trigger:#trigger mean different compId
#                    print 'Col level:%d  d:%.1f  distance:%.1f'%(level, d, distance[pt]),
                    #return True
                    if level < self.maxLevel:
                        nxtLevelSpheres = self.positions[level+1]
                        nxtLevelRadii = self.radii[level+1]
                        # get sphere that are children of this one
                        ccenters = []
                        cradii = []
                        for sphInd in self.children[level][sphNum]:
                            ccenters.append( nxtLevelSpheres[sphInd] )
                            cradii.append( nxtLevelRadii[sphInd] )
                        collision = self.checkSphCollisions(
                            ccenters, cradii, jtrans, rotMat, level+1,
                            gridPointsCoords, distance, histoVol)
                        if not collision and level>0:
                            #import pdb
                            #pdb.set_trace()
                            #print("returning notCollision and level>0 as Collision")
                            return collision
                        #print("returning regular collision")
                        return collision
                    else:
                        #print("in Collision, but returning True")
                        return True
                    # FIXME DEBUG INFO
                    if d+distance[pt] < histoVol.maxColl:
                        histoVol.maxColl = d+distance[pt]
                            #print("in collision histovol.maxColl if")
                    return True
                        #print("End of collision for pt = ", pt)
            sphNum += 1
                #print("collision returning False")
        
        return False

    def checkSphCompart(self, centers, radii, jtrans, rotMat, level,
                        gridPointsCoords, distance, histoVol):
        """
        Check spheres for collision
        """
        print ("OK sphere compartment checking",self.compNum)
        centT = self.transformPoints(jtrans, rotMat, centers)#this should be jtrans
#        print "sphCollision",centT,radii
        sphNum = 0
#        self.distances_temp=[]
#        if self.compareCompartment:
#            listeCpmNum=[]
        for radc, posc in zip(radii, centT):
#            r=[]
            x,y,z = posc
            bb = ( [x-radc, y-radc, z-radc], [x+radc, y+radc, z+radc] )
            pointsInCube = histoVol.getPointsInCube(bb, posc, radc,info=True)#indices
#            r.append(pointsInCube)
            
            delta = numpy.take(gridPointsCoords,pointsInCube,0)-posc
            delta *= delta
            distA = numpy.sqrt( delta.sum(1) )
            ptsInSphere = numpy.nonzero(numpy.less_equal(distA, radc))[0]
            ptsInSphereId = numpy.take(pointsInCube,ptsInSphere,0)
            compIdsSphere = numpy.take(histoVol.grid.gridPtId,ptsInSphereId,0)  
            print (len(compIdsSphere),compIdsSphere)
            if self.compNum <= 0 :
                wrongPt = [ cid for cid in compIdsSphere if cid != self.compNum ]
                if len(wrongPt):
                    print ("OK false compartment",len(wrongPt))
                    return True
        return False

    def checkCubeCollisions(self, centers1, centers2, radii, jtrans, rotMat,
                           gridPointsCoords, distance, histoVol):
        """
        Check cube for collision
        centers1 and centers2 should be the cornerPoints ?
        can also use the center plus size (radii), or the position/position2
        """
        cent1T = self.transformPoints(jtrans, rotMat, centers1)[0]#bb1
        cent2T = self.transformPoints(jtrans, rotMat, centers2)[0]#bb2
        center = self.transformPoints(jtrans, rotMat, [self.center,])[0]
        
        cylNum = 0
#        for radc, p1, p2 in zip(radii, cent1T, cent2T):
        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
        lengthsq = vx*vx + vy*vy + vz*vz
        l = sqrt( lengthsq )
        cx, cy, cz = posc = center#x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = l/2. + self.encapsulatingRadius
        x,y,z = posc
        bb = ( [x-radt, y-radt, z-radt], [x+radt, y+radt, z+radt] )
        
#        bb = [cent2T,cent1T]#self.correctBB(p1,p2,radc)
#            bb = self.correctBB(posc,posc,radt)
        if histoVol.runTimeDisplay :#> 1:
            print ("collBox",bb)
            box = self.vi.getObject("collBox")
            if box is None:
                box = self.vi.Box('collBox', 
                cornerPoints=bb,
#                center=center, 
#                size = [radt,radt,radt],
                visible=1)# cornerPoints=bb,visible=1)
            else :
#                    self.vi.toggleDisplay(box,True)
                self.vi.updateBox(box,
                cornerPoints=bb,
#                center=center, 
#                size = [radt,radt,radt],
                )#cornerPoints=bb)
            self.vi.update()
#                 sleep(1.0)
#        print ("pointsInCube",bb,posc,radt)        
        pointsInCube = histoVol.getPointsInCube(bb, posc, radt)
        
        # check for collisions with cylinder    
#        print   ("pointsInCube",pointsInCube)      
        pd = numpy.take(gridPointsCoords,pointsInCube,0)-center
#        print ("Cube",rotMat)
        m = numpy.matrix(numpy.array(rotMat).reshape(4,4))#
        mat = m.I
        #need to apply inverse mat to pd
        rpd = ApplyMatrix(pd,mat)
#        print (pd)
#        print (rpd)
        #need to check if these point are inside the cube using the dimension of the cube
#        res = numpy.less(rpd,radii[0])#size ?
        res = numpy.less_equal(numpy.fabs(rpd),numpy.array(radii[0])/2.)
#        print (res)
        c=numpy.average(res,1)#.astype(int)
#        print ("average",c)
        d=numpy.equal(c,1.)
#        print (d)
        ptinside = numpy.nonzero(d)[0]
#        print (ptinside)
#        if not len(ptinside):
#            print "no point inside the geom?"
#            return False
        if self.compareCompartment:
            ptinsideId = numpy.take(pointsInCube,ptinside,0)
            compIdsSphere = numpy.take(histoVol.grid.gridPtId,ptinsideId,0)  
#            print "compId",compIdsSphere
            if self.compNum <= 0 :
                wrongPt = [ cid for cid in compIdsSphere if cid != self.compNum ]
                if len(wrongPt):
#                    print wrongPt
                    return True                
#            
#        trigger, res = self.checkCompartment(numpy.take(pointsInCube,ptinside,0))
#        print ("checkCompartment result",trigger, res)
#        if res :
#            return True
#            for pt in pointsInCube:
        for pti in ptinside:
            pt = pointsInCube[pti]
#            print pt,distance[pt]
#                dist = dsq[pti]
#                if dist > rad2: continue # outside radius
            if distance[pt]<-0.0001 :#or trigger : # pt is inside cylinder
                #changeObjColorMat
#                    if histoVol.runTimeDisplay > 1:
#                        self.vi.changeObjColorMat(cyl,(1.,0.,0.))
#                        self.vi.update()
#                        sleep(1.0)
                return True

#            cylNum += 1
        return False

    def checkCubeCompart(self, centers1, centers2, radii, jtrans, rotMat,
                           gridPointsCoords, distance, histoVol):
        """
        Check cube for collision
        centers1 and centers2 should be the cornerPoints ?
        can also use the center plus size (radii), or the position/position2
        """
        cent1T = self.transformPoints(jtrans, rotMat, centers1)[0]#bb1
        cent2T = self.transformPoints(jtrans, rotMat, centers2)[0]#bb2
        center = self.transformPoints(jtrans, rotMat, [self.center,])[0]
        
        cylNum = 0
#        for radc, p1, p2 in zip(radii, cent1T, cent2T):
        x1, y1, z1 = cent1T
        x2, y2, z2 = cent2T
        vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
        lengthsq = vx*vx + vy*vy + vz*vz
        l = sqrt( lengthsq )
        cx, cy, cz = posc = center#x1+vx*.5, y1+vy*.5, z1+vz*.5
        radt = l/2. + self.encapsulatingRadius
        x,y,z = posc
        bb = ( [x-radt, y-radt, z-radt], [x+radt, y+radt, z+radt] )
        
        pointsInCube = histoVol.getPointsInCube(bb, posc, radt)
        
        pd = numpy.take(gridPointsCoords,pointsInCube,0)-center
        m = numpy.matrix(numpy.array(rotMat).reshape(4,4))#
        mat = m.I
        rpd = ApplyMatrix(pd,mat)
        res = numpy.less_equal(numpy.fabs(rpd),numpy.array(radii[0])/2.)
        c=numpy.average(res,1)#.astype(int)
        d=numpy.equal(c,1.)
        ptinside = numpy.nonzero(d)[0]
        ptinsideId = numpy.take(pointsInCube,ptinside,0)
        compIdsSphere = numpy.take(histoVol.grid.gridPtId,ptinsideId,0)  
#        print "compId",compIdsSphere
        if self.compNum <= 0 :
            wrongPt = [ cid for cid in compIdsSphere if cid != self.compNum ]
            if len(wrongPt):
#                print wrongPt
                return True                
        return False

    def oneJitter(self,spacing,trans,rotMat):
#        spacing = histoVol.smallestProteinSize
        jx, jy, jz = self.jitterMax
        jitter = self.getMaxJitter(spacing)
        jitter2 = jitter * jitter
        compNum = self.compNum
        tx, ty, tz = trans
        verbose=False
        if jitter2 > 0.0:
            found = False
            while not found:
                dx = jx*jitter*gauss(0., 0.3)
                dy = jy*jitter*gauss(0., 0.3)
                dz = jz*jitter*gauss(0., 0.3)
                d2 = dx*dx + dy*dy + dz*dz
                if d2 < jitter2:
                    if compNum > 0: # jitter less among normal
                        #if self.name=='2uuh C4 SYNTHASE':
                        #    import pdb
                        #    pdb.set_trace()
                        dx, dy, dz, dum = numpy.dot(rotMat, (dx,dy,dz,0))
                    jtrans = (tx+dx, ty+dy, tz+dz)
                    found = True
                else:
                    if verbose :
                        print('JITTER REJECTED', d2, jitter2)
        else:
            jtrans = trans
            dx = dy = dz = 0.0
            # randomize rotation about axis
        if compNum>0:
            rotMatj = self.getAxisRotation(rotMat)
        else:
            if self.useRotAxis :# is not None :
                if sum(self.rotAxis) == 0.0 :
                    rotMatj=numpy.identity(4)
                else :
                    rotMatj=self.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
            else :
                rotMatj = rotMat.copy()
        return jtrans,rotMatj
        
    def getInsidePoints(self,grid,gridPointsCoords,dpad,distance,
                       centT=None,jtrans=None, rotMatj=None):
        insidePoints={}
        newDistPoints={}
        if self.modelType=='Spheres':
            for radc, posc in zip(self.radii[-1], centT):
             
                rad = radc + dpad
                x,y,z = posc

                bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
                pointsInCube = grid.getPointsInCube(bb, posc, rad)

                delta = numpy.take(gridPointsCoords,pointsInCube,0)-posc
                delta *= delta
                distA = numpy.sqrt( delta.sum(1) )
                ptsInSphere = numpy.nonzero(numpy.less_equal(distA, rad))[0]

                for pti in ptsInSphere:
                    pt = pointsInCube[pti]
                    if pt in insidePoints: continue
                    dist = distA[pti]
                    d = dist-radc
                    if dist < radc:  # point is inside dropped sphere
                        if pt in insidePoints:
                            if d < insidePoints[pt]:
                                insidePoints[pt] = d
                        else:
                            insidePoints[pt] = d
                    elif d < distance[pt]: # point in region of influence
                        if pt in newDistPoints:
                            if d < newDistPoints[pt]:
                                newDistPoints[pt] = d
                        else:
                            newDistPoints[pt] = d
        elif self.modelType=='Cylinders':
            cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
            cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])
            #print "cent transformed \n",cent1T,cent2T
            for radc, p1, p2 in zip(self.radii[-1], cent1T, cent2T):
                x1, y1, z1 = p1
                x2, y2, z2 = p2
                vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
                lengthsq = vx*vx + vy*vy + vz*vz
                l = sqrt( lengthsq )
                cx, cy, cz = posc = x1+vx*.5, y1+vy*.5, z1+vz*.5
                radt = l + radc + dpad
                #bb = ( [cx-radt, cy-radt, cz-radt], [cx+radt, cy+radt, cz+radt] )
                bb = self.correctBB(posc,posc,radt)#p1,p2,radc
                pointsInCube = grid.getPointsInCube(bb, posc, radt)
                if hasattr(self,"histoVol") and self.histoVol.runTimeDisplay > 1:
                    box = self.vi.getObject("insidePtBox")
                    if box is None:
                        box = self.vi.Box('insidePtBox', cornerPoints=bb,visible=1)
                    else :
#                        self.vi.toggleDisplay(box,False)
                        self.vi.updateBox(box,cornerPoints=bb)
                        self.vi.update()
                    sleep(1.)
                pd = numpy.take(gridPointsCoords,pointsInCube,0) - p1
                dotp = numpy.dot(pd, vect)
                rad2 = radc*radc
                d2toP1 = numpy.sum(pd*pd, 1)
                dsq = d2toP1 - dotp*dotp/lengthsq

                pd2 = numpy.take(gridPointsCoords,pointsInCube,0) - p2
                d2toP2 = numpy.sum(pd2*pd2, 1)

                for pti, pt in enumerate(pointsInCube):
                    if pt in insidePoints: continue

                    if dotp[pti] < 0.0: # outside 1st cap
                        d = sqrt(d2toP1[pti])
                        if d < distance[pt]: # point in region of influence
                            if pt in newDistPoints:
                                if d < newDistPoints[pt]:
                                    newDistPoints[pt] = d
                            else:
                                newDistPoints[pt] = d
                    elif dotp[pti] > lengthsq:
                        d = sqrt(d2toP2[pti])
                        if d < distance[pt]: # point in region of influence
                            if pt in newDistPoints:
                                if d < newDistPoints[pt]:
                                    newDistPoints[pt] = d
                            else:
                                newDistPoints[pt] = d
                    else:
                        d = sqrt(dsq[pti])-radc
                        if d < 0.:  # point is inside dropped sphere
                            if pt in insidePoints:
                                if d < insidePoints[pt]:
                                    insidePoints[pt] = d
                            else:
                                insidePoints[pt] = d
        elif self.modelType=='Cube': 
            insidePoints,newDistPoints = self.getDistancesCube(jtrans, rotMatj,gridPointsCoords, distance, grid)
        return insidePoints,newDistPoints

    def getNeighboursInBox(self,histoVol,jtrans,rotMat,organelle,afvi,rb=False):
        if histoVol.windowsSize_overwrite :
            rad = histoVol.windowsSize
        else :
#            rad = self.minRadius*2.0# + histoVol.largestProteinSize + \
                #histoVol.smallestProteinSize + histoVol.windowsSize
            rad = self.minRadius + histoVol.largestProteinSize + \
            histoVol.smallestProteinSize + histoVol.windowsSize
#        print ("look in cube of radius ",rad)
        x,y,z = jtrans
        bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
        if self.modelType == "Cylinders":
            cent1T = self.transformPoints(jtrans, rotMat, self.positions[self.maxLevel])
            cent2T = self.transformPoints(jtrans, rotMat, self.positions2[self.maxLevel])
            bbs=[]
            for radc, p1, p2 in zip(self.radii, cent1T, cent2T):            
                bb = self.correctBB(p1,p2,radc)
                bbs.append(bb)
            #get min and max from all bbs
            maxBB = [0,0,0]
            minBB = [9999,9999,9999]
            for bb in bbs:
                for i in range(3):
                    if bb[0][i] < minBB[i]:
                        minBB[i] =bb[0][i]
                    if bb[1][i] > maxBB[i]:
                        maxBB[i] = bb[1][i]
                    if bb[1][i] < minBB[i]:
                        minBB[i] = bb[1][i]
                    if bb[0][i] > maxBB[i]:
                        maxBB[i] = bb[0][i]
            bb = [minBB,maxBB]
        if histoVol.runTimeDisplay :
            box = self.vi.getObject("partBox")
            if box is None:
                box = self.vi.Box('partBox', cornerPoints=bb,visible=1)
            else :
                self.vi.toggleDisplay(box,True)
                self.vi.updateBox(box,cornerPoints=bb)
                self.vi.update()
#            sleep(1.0)
        pointsInCube = histoVol.getPointsInCube(bb, jtrans, rad)#sp?
        #should we got all ingre from all recipes?
        #maybe just add the surface if its not already the surface
        mingrs=[]
        if not rb :
            mingrs = [m for m in organelle.molecules if m[3] in pointsInCube  and m[3] != -1]
        #how can I highlight theses objects!         
        else :
            #all recipe/organelle
            mingrs = [m[2].rbnode[m[3]] for m in histoVol.molecules if m[3] in pointsInCube and m[3] != -1]
            for o in histoVol.organelles:
                i = [m[2].rbnode[m[3]] for m in organelle.molecules if m[3] in pointsInCube and m[3] != -1] 
                mingrs.extend(i) 
        #print ("so what is mingrs ",mingrs)           
        if len(histoVol.ingr_added)  : 
            iadd=[]            
            for ingrname in histoVol.ingr_added :
                for no in histoVol.ingr_added[ingrname].rbnode:
                    iadd.extend([histoVol.ingr_added[ingrname].rbnode[no]])
            #print ("do we add",iadd, len(iadd))
            if iadd is not None and len(iadd):
                mingrs.extend(iadd)              
                print ("do we add",iadd, len(iadd))
        #print ("so what is return mingrs ",mingrs)  
        return mingrs
    
    def getListePartners(self,histoVol,jtrans,rotMat,organelle,afvi):
        if histoVol.windowsSize_overwrite :
            rad = histoVol.windowsSize
        else :
            rad = self.minRadius + histoVol.largestProteinSize + \
                histoVol.smallestProteinSize + histoVol.windowsSize
        x,y,z = jtrans
        bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
        if self.modelType == "Cylinders":
            cent1T = self.transformPoints(jtrans, rotMat, self.positions[self.maxLevel])
            cent2T = self.transformPoints(jtrans, rotMat, self.positions2[self.maxLevel])
            bbs=[]
            for radc, p1, p2 in zip(self.radii, cent1T, cent2T):            
                bb = self.correctBB(p1,p2,radc)
                bbs.append(bb)
            #get min and max from all bbs
            maxBB = [0,0,0]
            minBB = [9999,9999,9999]
            for bb in bbs:
                for i in range(3):
                    if bb[0][i] < minBB[i]:
                        minBB[i] =bb[0][i]
                    if bb[1][i] > maxBB[i]:
                        maxBB[i] = bb[1][i]
                    if bb[1][i] < minBB[i]:
                        minBB[i] = bb[1][i]
                    if bb[0][i] > maxBB[i]:
                        maxBB[i] = bb[0][i]
            bb = [minBB,maxBB]
        if histoVol.runTimeDisplay > 1:
            box = self.vi.getObject("partBox")
            if box is None:
                box = self.vi.Box('partBox', cornerPoints=bb,visible=1)
            else :
                self.vi.toggleDisplay(box,True)
                self.vi.updateBox(box,cornerPoints=bb)
                self.vi.update()
#            sleep(1.0)
        pointsInCube = histoVol.getPointsInCube(bb, jtrans, rad)
        #should we got all ingre from all recipes?
        #maybe just add the surface if its not already the surface
        mingrs = [m for m in organelle.molecules if m[3] in pointsInCube]
        listePartner = []
        weight=0.
        if self.packingMode=="closePartner":
#            listePartner = [(i,elem[2]) for i,elem in enumerate(mingrs) \
#                                    if self.partners.has_key(elem[2].name)]
            listePartner = [(i,self.partners[elem[2].name],afvi.vi.measure_distance(jtrans,elem[0]))\
                                    for i,elem in enumerate(mingrs) \
                                    if elem[2].name in self.partners]
        for i,elem in enumerate(mingrs):
            ing = elem[2]
            t = elem[0]
            r = elem[1]
            ind = elem[3]
            #print ing.name        
            if ing.isAttractor and self.compNum <= 0: #always attract! or rol a dice ?sself.excluded_partners.has_key(name)
                if i not in listePartner and self.name not in ing.excluded_partners:
                    #if no already in the partner list 
                    part = self.getPartner(ing.name) 
                    if part is None :
                        part = self.addPartner(ing.name,weight=ing.weight)
                    if ing.distExpression is not None:
                        part.distExpression = ing.distExpression
                    #print "new Partner", part,part.name,part.weight
                    d=afvi.vi.measure_distance(jtrans,t)
                    listePartner.append([i,part,d])
        return mingrs,listePartner

    def getTransform(self):      
        tTrans = self.vi.ToVec(self.vi.getTranslation(self.moving))
        rRot = self.vi.getMatRotation(self.moving)
        self.htrans.append(tTrans)
        avg = numpy.average(numpy.array(self.htrans))
        d=self.vi.measure_distance(tTrans,avg)
        #print "during",d,tTrans
        if d < 5.0:
#            print("during",d,tTrans)#,rRot
            return True
        else :
            return False

    def place(self,histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None):
        success = False
        #print self.placeType
        self.vi = histoVol.afviewer.vi
        self.histoVol=histoVol        
        if self.placeType == "jitter" or self.Type == "Grow" or self.Type == "Actine":
            success, nbFreePoints = self.jitter_place(histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None)
        elif self.placeType == "spring" or self.placeType == "rigid-body":
            success, nbFreePoints = self.rigid_place(histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None)
        elif self.placeType == "pandaBullet":
            success, nbFreePoints = self.pandaBullet_place(histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None)
        elif self.placeType == "pandaBulletRelax" or self.placeType == "pandaBulletSpring":
            success, nbFreePoints = self.pandaBullet_relax(histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None)

              
#        if histoVol.runTimeDisplay:
#            box = self.vi.getObject("collBox")
#            if box is not None:
    #                self.vi.toggleDisplay(box,Tru
#        print("nbFreePoints after jiter_place ", nbFreePoints)
        return success, nbFreePoints
            

    def rigid_place(self, histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None):
        """
        drop the ingredient on grid point ptInd
        """
        #print "rigid",self.placeType
        self.vi = histoVol.afviewer.vi
        afvi = histoVol.afviewer
        windowsSize = histoVol.windowsSize
        simulationTimes = histoVol.simulationTimes
        runTimeDisplay = histoVol.runTimeDisplay
        springOptions = histoVol.springOptions
        self.histoVol = histoVol
        rejectionCount = 0
        spacing = histoVol.smallestProteinSize
        jx, jy, jz = self.jitterMax
        jitter = self.getMaxJitter(spacing)
        jitter2 = jitter * jitter

        if self.compNum == 0 :
            organelle = self.histoVol
        else :
            organelle = self.histoVol.organelles[abs(self.compNum)-1]
            #this is hisotVol for cytoplasme
        compNum = self.compNum
        radius = self.minRadius

        gridPointsCoords = histoVol.grid.masterGridPositions

        # compute rotation matrix rotMat
        if compNum>0:
            # for surface points we compute the rotation which
            # aligns the principalVector with the surface normal
            vx, vy, vz = v1 = self.principalVector
            v2 = organelle.surfacePointsNormals[ptInd]
            try :
                rotMat = numpy.array( rotVectToVect(v1, v2 ), 'f')
            except :
                print('PROBLEM ', self.name)
                rotMat = numpy.identity(4)
        else:
            if self.useRotAxis :
                if sum(self.rotAxis) == 0.0 :
                    rotMat=numpy.identity(4)
                else :
                    rotMat=afvi.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
            else :
                rotMat=histoVol.randomRot.get()

        if verbose :
            pass#print('%s nbs:%2d'%(self.pdb, len(self.positions[0])), end=' ')

        # jitter position loop
        jitterList = []
        collD1 = []
        collD2 = []

        trans = gridPointsCoords[ptInd] # drop point
        gridDropPoint = trans
        jtrans,rotMatj = self.oneJitter(spacing,trans,rotMat)
        
        ok = False
        #here should go the simulation
        #1- we build the ingrediant if not already and place the ingrediant at jtrans, rotMatj
        moving=None
        static=[]
        target=None
        targetPoint = jtrans
#        import c4d
        #c4d.documents.RunAnimation(c4d.documents.GetActiveDocument(), True)

        if self.mesh:
            if hasattr(self,"mesh_3d"):
                #create an instance of mesh3d and place it
                name = self.name + str(ptInd)
                if self.mesh_3d is None :
                    self.moving= moving = afvi.vi.Sphere(name,radius=self.radii[0][0],
                                                    parent=afvi.movingMesh)[0]
                    afvi.vi.setTranslation(moving,pos=jtrans)
                else :
                    #why the GetDown?
                    self.moving= moving = afvi.vi.newInstance(name,self.mesh_3d,#.GetDown()
                                                matrice=rotMatj,
                                                location=jtrans, parent = afvi.movingMesh)
        #2- get the neighboring object from ptInd
        mingrs,listePartner=self.getListePartners(histoVol,jtrans,rotMat,organelle,afvi)
        for i,elem in enumerate(mingrs):
            ing = elem[2]
            t = elem[0]
            r = elem[1]
            ind = elem[3]
            #print "neighbour",ing.name
            if hasattr(ing,"mesh_3d"):
                #create an instance of mesh3d and place it
                name = ing.name + str(ind)
                if ing.mesh_3d is None :
                    ipoly = afvi.vi.Sphere(name,radius=self.radii[0][0],parent=afvi.staticMesh)[0]
                    afvi.vi.setTranslation(ipoly,pos=t)
                else :
                    ipoly =afvi.vi.newInstance(name,ing.mesh_3d,matrice=r,#.GetDown()
                           location=t, parent = afvi.staticMesh)
                static.append(ipoly)
            elif isinstance(ing,GrowIngrediant):
                name = ing.name + str(ind)
                ipoly =afvi.vi.newInstance(name,afvi.orgaToMasterGeom[ing],
                                           parent = afvi.staticMesh)
                static.append(ipoly)
            
        if listePartner : #self.packingMode=="closePartner":
            if verbose:
                print("len listePartner = ", len(listePartner))
            if not self.force_random:
                targetPoint,weight = self.pickPartner(mingrs,listePartner,currentPos=jtrans)
                if targetPoint is None :
                    targetPoint = jtrans
            else :
                targetPoint = jtrans
#        print "targetPt",len(targetPoint),targetPoint   
        #setup the target position
        if self.placeType == "spring":
            afvi.vi.setRigidBody(afvi.movingMesh,**histoVol.dynamicOptions["spring"])
            #target can be partner position?
            target = afvi.vi.getObject("target"+name)
            if target is None :
                target = afvi.vi.Sphere("target"+name,radius=5.0)[0]
            afvi.vi.setTranslation(target,pos=targetPoint)
            afvi.vi.addObjectToScene(None,target)
            #3- we setup the spring (using the sphere position empty)
            spring = afvi.vi.getObject("afspring")
            if spring is None :
                spring = afvi.vi.createSpring("afspring",targetA=moving,tragetB=target,**springOptions)
            else :
                afvi.vi.updateSpring(spring,targetA=moving,tragetB=target,**springOptions)
        else :
            #before assigning should get outside thge object 
            afvi.vi.setRigidBody(afvi.movingMesh,**histoVol.dynamicOptions["moving"])
            afvi.vi.setTranslation(self.moving,pos=targetPoint)
        afvi.vi.setRigidBody(afvi.staticMesh,**histoVol.dynamicOptions["static"])
        #4- we run the simulation
        #c4d.documents.RunAnimation(c4d.documents.GetActiveDocument(), False,True)
        #if runTimeDisplay :
        afvi.vi.update()
#        rTrans = afvi.vi.ToVec(afvi.vi.getTranslation(moving))
#        rRot = afvi.vi.getMatRotation(moving)

        #print afvi.vi.ToVec(moving.GetAllPoints()[0])
        #afvi.vi.animationStart(duration = simulationTimes)
        #afvi.vi.update()
        afvi.vi.frameAdvanced(duration = simulationTimes,display = runTimeDisplay)#,
                              #cb=self.getTransfo)
#        moving=afvi.vi.makeEditable(moving,copy=False)                            
        #5- we get the resuling transofrmation matrix and decompose ->rTrans rRot
        #if runTimeDisplay :
        afvi.vi.update()
        rTrans = afvi.vi.ToVec(afvi.vi.getTranslation(moving))
        rRot = afvi.vi.getMatRotation(moving)
#        M=moving.GetMg()
        #print afvi.vi.ToVec(moving.GetAllPoints()[0])

#        print("OK AFTER",rTrans)#,rRot
#        print("save",self.tTrans)#,self.rRot
        #6- clean and delete everything except the spring
        afvi.vi.deleteObject(moving)        
        afvi.vi.deleteObject(target)
        for o in static:
            afvi.vi.deleteObject(o)
        ok = True
        jtrans = rTrans[:]
        rotMatj = rRot[:]
        jitterPos = 1
        if ok :
            ## get inside points and update distance
            ##
            # use best sperical approcimation
#            print(">>?",self.name,jtrans)
            centT = self.transformPoints(jtrans, rotMatj, self.positions[-1])

            insidePoints = {}
            newDistPoints = {}
            insidePoints,newDistPoints = self.getInsidePoints(histoVol.grid,
                                gridPointsCoords,dpad,distance,centT=centT,
                                jtrans=jtrans, 
                                rotMatj=rotMatj)

            
            # update free points
            nbFreePoints = self.updateDistances(histoVol,insidePoints, newDistPoints, 
                        freePoints, nbFreePoints, distance, 
                        histoVol.grid.masterGridPositions, verbose)

            # save dropped ingredient
            
            organelle.molecules.append([ jtrans, rotMatj, self, ptInd ])
            histoVol.order[ptInd]=histoVol.lastrank
            histoVol.lastrank+=1            
            self.rRot.append(rotMatj)
            self.tTrans.append(jtrans)
            # add one to molecule counter for this ingredient
            self.counter += 1
            self.completion = float(self.counter)/self.nbMol

            if jitterPos>0:
                histoVol.successfullJitter.append(
                    (self, jitterList, collD1, collD2) )  
            if verbose :
                print('Success nbfp:%d %d/%d dpad %.2f'%(
                nbFreePoints, self.counter, self.nbMol, dpad))
            if self.name=='in  inside':
                histoVol.jitterVectors.append( (trans, jtrans) )

            success = True
            self.rejectionCounter = 0
            
        else: # got rejected
            success = False
            histoVol.failedJitter.append(
                (self, jitterList, collD1, collD2) )

            distance[ptInd] = max(0, distance[ptInd]*0.9)
            self.rejectionCounter += 1
            if verbose :
                print('Failed ingr:%s rejections:%d'%(
                self.name, self.rejectionCounter))
            if self.rejectionCounter >= 30:
                if verbose :
                    print('PREMATURE ENDING of ingredient', self.name)
                self.completion = 1.0
        return success, nbFreePoints
    

    def jitter_place(self, histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None,drop=True):
        """
        drop the ingredient on grid point ptInd
        """
#        print("JitterPlace1****************************************************************")
        verbose = histoVol.verbose
        afvi = histoVol.afviewer
        rejectionCount = 0
        spacing = histoVol.smallestProteinSize
        jx, jy, jz = self.jitterMax
        jitter = histoVol.callFunction(self.getMaxJitter,(spacing,))
        jitter2 = jitter * jitter

        if self.compNum == 0 :
            organelle = histoVol
        else :
            organelle = histoVol.organelles[abs(self.compNum)-1]
        compNum = self.compNum
        radius = self.minRadius
        runTimeDisplay = histoVol.runTimeDisplay
        
        gridPointsCoords = histoVol.masterGridPositions
        
        #test force dpad to 1
 #       dpad = 1  Dangerous- this is specifically what is breaking all of the other Sphere/Cylinder test files
        # compute rotation matrix rotMat
        if compNum>0 :
            # for surface points we compute the rotation which
            # aligns the principalVector with the surface normal
            vx, vy, vz = v1 = self.principalVector
                
#            try :
            v2 = organelle.surfacePointsNormals[ptInd]
            rotMat = numpy.array( rotVectToVect(v1, v2 ), 'f')
#            except :
#                print('############ PROBLEM ', self.name, ptInd,len(organelle.surfacePointsNormals))
#                rotMat = numpy.identity(4)
        else:
            if self.useRotAxis :
#                angle = random()*6.2831#math.radians(random()*360.)#random()*pi*2.
#                print "angle",angle,math.degrees(angle)
#                direction = self.rotAxis
                if sum(self.rotAxis) == 0.0 :
                    rotMat=numpy.identity(4)
                else :
                    rotMat=afvi.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
            # for other points we get a random rotation
            else :
                rotMat=histoVol.randomRot.get()

#        if verbose :
#            pass#print('%s nbs:%2d'%(self.pdb, len(self.positions[0])), end=' ')

        # jitter position loop
        jitterList = []
        collD1 = []
        collD2 = []

        trans = gridPointsCoords[ptInd] # drop point, surface points.
        targetPoint = trans
        moving = None
        if runTimeDisplay and self.mesh:
            if hasattr(self,"mesh_3d"):
                #create an instance of mesh3d and place it
                name = self.name + str(ptInd)
                moving = afvi.vi.getObject(name)
                if moving is None :
                    if self.mesh_3d is None :
                        moving = afvi.vi.Sphere(name,radius=self.radii[0][0],
                                                        parent=afvi.staticMesh)[0]
                        afvi.vi.setTranslation(moving,pos=targetPoint)
                    else :
                        moving=  afvi.vi.newInstance(name,self.mesh_3d,#.GetDown(),
                                                    matrice=rotMat,
                                                    location=targetPoint, parent = afvi.staticMesh)
#                else :   #Graham turned off this unnecessary update
                    #afvi.vi.setTranslation(moving,pos=targetPoint)#rot?
#                    mat = rotMat.copy() #Graham turned off this unnecessary update
#                    mat[:3, 3] = targetPoint #Graham turned off this unnecessary update
#                    afvi.vi.setObjectMatrix(moving,mat,transpose=True) #Graham turned off this unnecessary update
#                afvi.vi.update()  #Graham turned off this unnecessary update
#            print ('Must check for collision here before accepting final position')
        #do we get the list of neighbours first > and give a different trans...closer to the partner
        #we should look up for an available ptID around the picked partner if any
        #getListPartner
        if histoVol.ingrLookForNeighbours:
            mingrs,listePartner=self.getListePartners(histoVol,trans,rotMat,organelle,afvi)
            #if liste:pickPartner
            if listePartner : #self.packingMode=="closePartner":
#                print "ok partner",len(listePartner)
                if not self.force_random:
                    targetPoint,weight = self.pickPartner(mingrs,listePartner,currentPos=trans)
                    if targetPoint is None :
                        targetPoint = trans
                    else :#maybe get the ptid that can have it
                        #find a newpoint here?
                        x,y,z = targetPoint
                        rad = self.radii[0][0]*2.#why by 2.0
                        bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
                        pointsInCube = histoVol.getPointsInCube(bb, targetPoint,rad )
                        #is one of this point can receive the current ingredient
                        cut  = rad-jitter
                        for pt in pointsInCube:
                            d = distance[pt]
                            if d>=cut:
                                #lets just take the first one
                                targetPoint = gridPointsCoords[pt]
                                break
                else :
                    targetPoint = trans
            #if partner:pickNewPoit like in fill3
        tx, ty, tz = jtrans = targetPoint
        gridDropPoint = targetPoint        
        #we may increase the jitter, or pick from xyz->Id free for its radius
        
        #jitter loop
        t1 = time()
        for jitterPos in range(self.nbJitter):   #This expensive Gauusian rejection system should not be the default should it?
            # jitter points location
            if jitter2 > 0.0:
                found = False
                while not found:
                    dx = jx*jitter*gauss(0., 0.3)
                    dy = jy*jitter*gauss(0., 0.3)
                    dz = jz*jitter*gauss(0., 0.3)
                    d2 = dx*dx + dy*dy + dz*dz
                    if d2 < jitter2:
                        if compNum > 0: # jitter less among normal
                            #if self.name=='2uuh C4 SYNTHASE':
                            #    import pdb
                            #    pdb.set_trace()
                            dx, dy, dz, dum = numpy.dot(rotMat, (dx,dy,dz,0))
                        jtrans = (tx+dx, ty+dy, tz+dz)
                        found = True
                    else:
                        if verbose :
                            print('JITTER REJECTED', d2, jitter2)
#                    if runTimeDisplay and moving is not None :  #Graham turned off this unnecessary update
#                        afvi.vi.setTranslation(moving,pos=jtrans)   #Graham turned off this unnecessary update
#                        afvi.vi.update()  #Graham turned off this unnecessary update
#                        print "ok moving"
            else:
                jtrans = targetPoint
                dx = dy = dz = 0.0
           
            histoVol.totnbJitter += 1
            histoVol.jitterLength += dx*dx + dy*dy + dz*dz  #Why is this expensive line needed?
            jitterList.append( (dx,dy,dz) )
            
            #print 'j%d %.2f,%.2f,%.2f,'%(jitterPos,tx, ty, tz),
#            if verbose :
#                print('j%d'%jitterPos)# end=' '
            
            # loop over all spheres representing ingredient
            modSphNum = 1
            if sphGeom is not None:
                modCent = []
                modRad = []

            ## check for collisions 
            ## 
            level = self.collisionLevel

            # randomize rotation about axis
            if compNum>0:
                rotMatj = self.getAxisRotation(rotMat)
            else:
                if self.useRotAxis :
                    if sum(self.rotAxis) == 0.0 :
                        rotMatj=numpy.identity(4)  #Graham Oct 16,2012 Turned on always rotate below as default.  If you want no rotation
                                                   #set useRotAxis = 1 and set rotAxis = 0, 0, 0 for that ingredient
                    else :
                        rotMatj=afvi.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
                else :
                    rotMatj=histoVol.randomRot.get()  #Graham turned this back on to replace rotMat.copy() so ing rotate each time
#                    rotMatj = rotMat.copy()
            if runTimeDisplay and moving is not None :
#                print "ok rot copy"
                mat = rotMatj.copy()
                mat[:3, 3] = jtrans
                afvi.vi.setObjectMatrix(moving,mat,transpose=True)
#                afvi.vi.setTranslation(moving,pos=jtrans)
                afvi.vi.update()
            if self.modelType=='Spheres':
#                print("running jitter number ", histoVol.totnbJitter, " on Spheres for pt = ", ptInd)
#                print("jtrans = ", jtrans)
                collision = histoVol.callFunction(self.checkSphCollisions,(
                    self.positions[level], self.radii[level], jtrans, rotMatj,
                    level, gridPointsCoords, distance, histoVol))
#                print("jitter collision = ", collision, " for pt = ", ptInd, " with jtrans = ", jtrans)
            elif self.modelType=='Cylinders':
                collision = histoVol.callFunction(self.checkCylCollisions,(
                    self.positions[level], self.positions2[level],
                    self.radii[level], jtrans, rotMatj, gridPointsCoords,
                    distance, histoVol))
            elif self.modelType=='Cube':
                collision = histoVol.callFunction(self.checkCubeCollisions,(
                    self.positions[0], self.positions2[0], self.radii,
                    jtrans, rotMatj, gridPointsCoords,
                    distance, histoVol))
            if not collision:
                break # break out of jitter pos loop
        if verbose: 
            print("jitter loop ",time()-t1)
        if not collision:
#            print("jtrans for NotCollision= ", jtrans)
            
            ## get inside points and update distance
            ##
            # use best sperical approcimation

            centT = self.centT#self.transformPoints(jtrans, rotMatj, self.positions[-1])

            insidePoints = {}
            newDistPoints = {}
            t3=time()
            #should be replace by self.getPointInside
            if self.modelType=='Spheres':
#                for pointsInCube,ptsInSphere in self.distances_temp:
                for radc, posc in zip(self.radii[-1], centT):
#                for i,radc in enumerate(self.radii[-1]):
#                    pointsInCube,ptsInSphere,distA = self.distances_temp[i]
                    rad = radc + dpad
#                    print ("sphere ingr",rad,dpad,radc,posc)
                    x,y,z = posc
                    #this have already be done in the checkCollision why doing it again
                    bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
                    pointsInCube = histoVol.callFunction(histoVol.getPointsInCube,
                                                         (bb, posc, rad))
              #      print ("sphere ingr",len(pointsInCube))
                    delta = numpy.take(gridPointsCoords,pointsInCube,0)-posc
                    delta *= delta
                    distA = numpy.sqrt( delta.sum(1) )
                    ptsInSphere = numpy.nonzero(numpy.less_equal(distA, rad))[0]

                    for pti in ptsInSphere:
                        pt = pointsInCube[pti]
                        if pt in insidePoints: continue
                        dist = distA[pti]
                        d = dist-radc
                        if dist < radc:  # point is inside dropped sphere
                            if pt in insidePoints:
                                if d < insidePoints[pt]:
                                    insidePoints[pt] = d
                            else:
                                insidePoints[pt] = d
                        elif d < distance[pt]: # point in region of influence
                            if pt in newDistPoints:
                                if d < newDistPoints[pt]:
                                    newDistPoints[pt] = d
                            else:
                                newDistPoints[pt] = d

            elif self.modelType=='Cylinders':
                cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
                cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])

                for radc, p1, p2 in zip(self.radii[-1], cent1T, cent2T):

                    x1, y1, z1 = p1
                    x2, y2, z2 = p2
                    vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
                    lengthsq = vx*vx + vy*vy + vz*vz
                    l = sqrt( lengthsq )
                    cx, cy, cz = posc = x1+vx*.5, y1+vy*.5, z1+vz*.5
                    radt = l + radc + dpad
                    bb = ( [cx-radt, cy-radt, cz-radt], [cx+radt, cy+radt, cz+radt] )
                    pointsInCube = histoVol.callFunction(histoVol.getPointsInCube,
                                                         (bb, posc, radt))

                    pd = numpy.take(gridPointsCoords,pointsInCube,0) - p1
                    dotp = numpy.dot(pd, vect)
                    rad2 = radc*radc
                    d2toP1 = numpy.sum(pd*pd, 1)
                    dsq = d2toP1 - dotp*dotp/lengthsq

                    pd2 = numpy.take(gridPointsCoords,pointsInCube,0) - p2
                    d2toP2 = numpy.sum(pd2*pd2, 1)

                    for pti, pt in enumerate(pointsInCube):
                        if pt in insidePoints: continue

                        if dotp[pti] < 0.0: # outside 1st cap
                            d = sqrt(d2toP1[pti])
                            if d < distance[pt]: # point in region of influence
                                if pt in newDistPoints:
                                    if d < newDistPoints[pt]:
                                        newDistPoints[pt] = d
                                else:
                                    newDistPoints[pt] = d
                        elif dotp[pti] > lengthsq:
                            d = sqrt(d2toP2[pti])
                            if d < distance[pt]: # point in region of influence
                                if pt in newDistPoints:
                                    if d < newDistPoints[pt]:
                                        newDistPoints[pt] = d
                                else:
                                    newDistPoints[pt] = d
                        else:
                            d = sqrt(dsq[pti])-radc
                            if d < 0.:  # point is inside dropped sphere
                                if pt in insidePoints:
                                    if d < insidePoints[pt]:
                                        insidePoints[pt] = d
                                else:
                                    insidePoints[pt] = d
            elif self.modelType=='Cube':
                insidePoints,newDistPoints=self.getDistancesCube(jtrans, rotMatj,gridPointsCoords, distance, histoVol)
            
            # save dropped ingredient
            if verbose:
                print("compute distance loop ",time()-t3)
            if drop:
                #print "ok drop",organelle.name,self.name
                organelle.molecules.append([ jtrans, rotMatj, self, ptInd ])
                histoVol.order[ptInd]=histoVol.lastrank
                histoVol.lastrank+=1
            # update free points
            if verbose:
                print ("updating distances and verbose = ", verbose)
            timeUpDistLoopStart=time()
            nbFreePoints = histoVol.callFunction(self.updateDistances,(histoVol,insidePoints,
                                                newDistPoints,freePoints,nbFreePoints, distance,
                                                histoVol.masterGridPositions, verbose))
            histoVol.timeUpDistLoopTotal+=time()-timeUpDistLoopStart
            
#            distChanges = {}
#            for pt,dist in insidePoints.items():
#                # swap point at ptIndr with last free one
#                try:
#                    ind = freePoints.index(pt)
#                    tmp = freePoints[nbFreePoints] #last one
#                    freePoints[nbFreePoints] = pt
#                    freePoints[ind] = tmp
#                    nbFreePoints -= 1
#                except ValueError: # pt not in list of free points
#                    pass
#                distChanges[pt] = (histoVol.masterGridPositions[pt],
#                                   distance[pt], dist)
#                distance[pt] = dist
#            print "update freepoints loop ",time()-t4
#            t5=time()
#            # update distances
#            for pt,dist in newDistPoints.items():
#                if not insidePoints.has_key(pt):
#                    distChanges[pt] = (histoVol.masterGridPositions[pt],
#                                       distance[pt], dist)
#                    distance[pt] = dist
#            print "update distances loop ",time()-t5
            
            if sphGeom is not None:
                for po1, ra1 in zip(modCent, modRad):
                    sphCenters.append(po1)
                    sphRadii.append(ra1)
                    sphColors.append(self.color)

            if labDistGeom is not None:
                verts = []
                labels = []
                colors = []
                #for po1, d1,d2 in distChanges.values():
                fpts = freePoints
                for i in range(nbFreePoints):
                    pt = fpts[i]
                    verts.append(histoVol.masterGridPositions[pt])
                    labels.append( "%.2f"%distance[pt])                    
#                for pt in freePoints[:nbFreePoints]:
#                    verts.append(histoVol.masterGridPositions[pt])
#                    labels.append( "%.2f"%distance[pt])
                labDistGeom.Set(vertices=verts, labels=labels)
                #materials=colors, inheritMaterial=0)

            # add one to molecule counter for this ingredient
            self.counter += 1
            self.completion = float(self.counter)/float(self.nbMol)

            if jitterPos>0:
                histoVol.successfullJitter.append(
                    (self, jitterList, collD1, collD2) )
               
            if verbose :
                print('Success nbfp:%d %d/%d dpad %.2f'%(
                nbFreePoints, self.counter, self.nbMol, dpad))
            if self.name=='in  inside':
                histoVol.jitterVectors.append( (trans, jtrans) )

            success = True
            self.rejectionCounter = 0
            
        else: # got rejected
            if runTimeDisplay and moving is not None :
                afvi.vi.deleteObject(moving)
            success = False
            self.haveBeenRejected = True
            histoVol.failedJitter.append(
                (self, jitterList, collD1, collD2) )

            distance[ptInd] = max(0, distance[ptInd]*0.9)# ???
            self.rejectionCounter += 1
            if verbose :
                print('Failed ingr:%s rejections:%d'%(
                self.name, self.rejectionCounter))
            if self.rejectionCounter >= self.rejectionThreshold: #Graham set this to 6000 for figure 13b (Results Fig 3 Test1) otehrwise it fails to fill small guys
                #if verbose :
                print('PREMATURE ENDING of ingredient', self.name)
                self.completion = 1.0

        if sphGeom is not None:
            sphGeom.Set(vertices=sphCenters, radii=sphRadii,
                        materials=sphColors)
            sphGeom.viewer.OneRedraw()
            sphGeom.viewer.update()

        if drop :
            return success, nbFreePoints
        else :
            return success, nbFreePoints,jtrans, rotMatj
            
    def pandaBullet_place(self, histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None,drop=True):
        """
        drop the ingredient on grid point ptInd
        """
        histoVol.setupPanda()#do I need this everytime?
        afvi = histoVol.afviewer
        rejectionCount = 0
        spacing = histoVol.smallestProteinSize
        jx, jy, jz = self.jitterMax
        jitter = histoVol.callFunction(self.getMaxJitter,(spacing,))
        jitter2 = jitter * jitter
        
        if self.compNum == 0 :
            organelle = histoVol
        else :
            organelle = histoVol.organelles[abs(self.compNum)-1]
        compNum = self.compNum
        radius = self.minRadius
        runTimeDisplay = histoVol.runTimeDisplay
        
        gridPointsCoords = histoVol.masterGridPositions

        # compute rotation matrix rotMat
        if compNum>0 :
            # for surface points we compute the rotation which
            # aligns the principalVector with the surface normal
            vx, vy, vz = v1 = self.principalVector
            v2 = organelle.surfacePointsNormals[ptInd]#1000 and it is a dictionary ?
            try :
                rotMat = numpy.array( rotVectToVect(v1, v2 ), 'f')
            except :
                print('PROBLEM ', self.name)
                rotMat = numpy.identity(4)
        else:
            if self.useRotAxis :
#                angle = random()*6.2831#math.radians(random()*360.)#random()*pi*2.
#                print "angle",angle,math.degrees(angle)
#                direction = self.rotAxis
                if sum(self.rotAxis) == 0.0 :
                    rotMat=numpy.identity(4)
                else :
                    rotMat=afvi.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
            # for other points we get a random rotation
            else :
                rotMat=histoVol.randomRot.get()

#        if verbose :
#            pass#print('%s nbs:%2d'%(self.pdb, len(self.positions[0])), end=' ')

        # jitter position loop
        jitterList = []
        collD1 = []
        collD2 = []

        trans = gridPointsCoords[ptInd] # drop point, surface points.
        targetPoint = trans
        moving = None
        if runTimeDisplay and self.mesh:
            if hasattr(self,"mesh_3d"):
                #create an instance of mesh3d and place it
                name = self.name + str(ptInd)
                moving = afvi.vi.getObject(name)
                if moving is None :
                    if self.mesh_3d is None :
                        moving = afvi.vi.Sphere(name,radius=self.radii[0][0],
                                                        parent=afvi.staticMesh)[0]
                        afvi.vi.setTranslation(moving,pos=targetPoint)
                    else :
                        moving=  afvi.vi.newInstance(name,self.mesh_3d,#.GetDown(),
                                                    matrice=rotMat,
                                                    location=targetPoint, parent = afvi.staticMesh)
                else :   
                    #afvi.vi.setTranslation(moving,pos=targetPoint)#rot?
                    mat = rotMat.copy()
                    mat[:3, 3] = targetPoint
                    afvi.vi.setObjectMatrix(moving,mat,transpose=True)
#                afvi.vi.update()  #Graham Killed this unneccesarry redraw
#            print ('Must check for collision here before accepting final position')
        #do we get the list of neighbours first > and give a different trans...closer to the partner
        #we should look up for an available ptID around the picked partner if any
        #getListPartner
        if histoVol.ingrLookForNeighbours:
            mingrs,listePartner=self.getListePartners(histoVol,trans,rotMat,organelle,afvi)
            #if liste:pickPartner
            if listePartner : #self.packingMode=="closePartner":
#                print "ok partner",len(listePartner)
                if not self.force_random:
                    targetPoint,weight = self.pickPartner(mingrs,listePartner,currentPos=trans)
                    if targetPoint is None :
                        targetPoint = trans
                    else :#maybe get the ptid that can have it
                        #find a newpoint here?
                        x,y,z = targetPoint
                        rad = self.radii[0][0]*2.
                        bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
                        pointsInCube = histoVol.getPointsInCube(bb, targetPoint,rad )
                        #is one of this point can receive the current ingredient
                        cut  = rad-jitter
                        for pt in pointsInCube:
                            d = distance[pt]
                            if d>=cut:
                                #lets just take the first one
                                targetPoint = gridPointsCoords[pt]
                                break
                else :
                    targetPoint = trans
            #if partner:pickNewPoit like in fill3
        tx, ty, tz = jtrans = targetPoint
        gridDropPoint = targetPoint        
        #we may increase the jitter, or pick from xyz->Id free for its radius
        #create the rb only once and not at ever jitter
        rbnode = histoVol.callFunction(self.histoVol.addRB,(self, jtrans, rotMat,),{"rtype":self.Type},)

        ningr_rb = self.getNeighboursInBox(histoVol,trans,rotMat,organelle,afvi,rb=True)
        print ("we get ",len(ningr_rb))
        #jitter loop
        t1 = time()
        for jitterPos in range(self.nbJitter):  #  This expensive Gauusian rejection system should not be the default should it?
            # jitter points location
            if jitter2 > 0.0:
                found = False
                while not found:
                    dx = jx*jitter*gauss(0., 0.3)
                    dy = jy*jitter*gauss(0., 0.3)
                    dz = jz*jitter*gauss(0., 0.3)
                    d2 = dx*dx + dy*dy + dz*dz
                    if d2 < jitter2:
                        if compNum > 0: # jitter less among normal
                            #if self.name=='2uuh C4 SYNTHASE':
                            #    import pdb
                            #    pdb.set_trace()
                            dx, dy, dz, dum = numpy.dot(rotMat, (dx,dy,dz,0))
                        jtrans = (tx+dx, ty+dy, tz+dz)
                        found = True
#                    else:  #Graham Killed thse unnecessary updates
#                        if verbose :  #Graham Killed thse unnecessary updates
#                            print('JITTER REJECTED', d2, jitter2)  #Graham Killed thse unnecessary updates
#                    if runTimeDisplay and moving is not None :  #Graham Killed thse unnecessary updates
#                        afvi.vi.setTranslation(moving,pos=jtrans)   
#                        afvi.vi.update()  
#                        print "ok moving"
            else:
                jtrans = targetPoint
                dx = dy = dz = 0.0
           
            histoVol.totnbJitter += 1
            histoVol.jitterLength += dx*dx + dy*dy + dz*dz
            jitterList.append( (dx,dy,dz) )
            
            #print 'j%d %.2f,%.2f,%.2f,'%(jitterPos,tx, ty, tz),
#            if verbose :
#                print('j%d'%jitterPos)# end=' '
            
            # loop over all spheres representing ingredient
            modSphNum = 1
            if sphGeom is not None:
                modCent = []
                modRad = []

            ## check for collisions 
            ## 
            level = self.collisionLevel

            # randomize rotation about axis
            if compNum>0:
                rotMatj = self.getAxisRotation(rotMat)
            else:
                if self.useRotAxis :
                    if sum(self.rotAxis) == 0.0 :
                        rotMatj=numpy.identity(4)
                    else :
                        rotMatj=afvi.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
                else :
                    rotMatj=histoVol.randomRot.get()  #Graham turned this back on to replace rotMat.copy() so ing rotate each time
#                    rotMatj = rotMat.copy()
            if runTimeDisplay and moving is not None :
#                print "ok rot copy"
                mat = rotMatj.copy()
                mat[:3, 3] = jtrans
                afvi.vi.setObjectMatrix(moving,mat,transpose=True)
#                afvi.vi.setTranslation(moving,pos=jtrans)
                afvi.vi.update()
                
#            rbnode = histoVol.callFunction(self.histoVol.addRB,(self, jtrans, rotMatj,),{"rtype":self.Type},)
            histoVol.callFunction(histoVol.moveRBnode,(rbnode, jtrans, rotMatj,))
            t=time()
            #       checkif rb collide 
#            result2 = self.histoVol.world.contactTest(rbnode)
#            collision = ( result2.getNumContacts() > 0)    
#            print ("contact All ",collision, time()-t, result2.getNumContacts())                 
#            t=time()     
#            ningr_rb = self.getNeighboursInBox(histoVol,trans,rotMat,organelle,afvi,rb=True)
            r=[False]
            if ningr_rb is not None and len(ningr_rb):
                r=[ (self.histoVol.world.contactTestPair(rbnode, n).getNumContacts() > 0 ) for n in ningr_rb]
            #r=[ (self.histoVol.world.contactTestPair(rbnode, n).getNumContacts() > 0 ) for n in self.histoVol.static]  
            collision2=( True in r)
            collisionComp = False

            #print ("contactTestPair",collision2,time()-t,len(r))
            #print ("contact Pair ", len(r),len(ningr_rb)) #gave nothing ???
            #need to check compartment too
                #Graham here:  If this is less expensive (compareCompartment less exp than mesh collision r=) we should do it first. Feb 28, 2013
            if not collision2 :# and not collision2:
                if self.compareCompartment:
                    if self.modelType=='Spheres':
        #                print("running jitter number ", histoVol.totnbJitter, " on Spheres for pt = ", ptInd)
        #                print("jtrans = ", jtrans)
                        collisionComp = histoVol.callFunction(self.checkSphCompart,(
                            self.positions[level], self.radii[level], jtrans, rotMatj,
                            level, gridPointsCoords, distance, histoVol))
        #                print("jitter collision = ", collision, " for pt = ", ptInd, " with jtrans = ", jtrans)
                    elif self.modelType=='Cylinders':
                        collisionComp = histoVol.callFunction(self.checkCylCompart,(
                            self.positions[level], self.positions2[level],
                            self.radii[level], jtrans, rotMatj, gridPointsCoords,
                            distance, histoVol))
                    elif self.modelType=='Cube':
                        collisionComp = histoVol.callFunction(self.checkCubeCompart,(
                            self.positions[0], self.positions2[0], self.radii,
                            jtrans, rotMatj, gridPointsCoords,
                            distance, histoVol))
                if not collisionComp :
                    self.rbnode[ptInd] = rbnode
                    self.histoVol.static.append(rbnode)
                    self.histoVol.moving = None
                    break # break out of jitter pos loop
                else :
                    collision2 = collisionComp
#            else :
#                histoVol.callFunction(self.histoVol.delRB,(rbnode,))
                #remove the node
#        if verbose: 
#        print("jitter loop ",time()-t1)
        if not collision2 :# and not collision2:
#            print("jtrans for NotCollision= ", jtrans)
            
            ## get inside points and update distance
            ##
            # use best sperical approcimation   

            insidePoints = {}
            newDistPoints = {}
            t3=time()
            #should be replace by self.getPointInside
            if self.modelType=='Spheres':
                self.centT = centT = self.transformPoints(jtrans, rotMatj, self.positions[level])
                centT = self.centT#self.transformPoints(jtrans, rotMatj, self.positions[-1])
#                for pointsInCube,ptsInSphere in self.distances_temp:
                for radc, posc in zip(self.radii[-1], centT):
#                for i,radc in enumerate(self.radii[-1]):
#                    pointsInCube,ptsInSphere,distA = self.distances_temp[i]
#                 
                    rad = radc + dpad
                    x,y,z = posc
#                    #this have already be done in the checkCollision why doing it again
                    bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
                    pointsInCube = histoVol.callFunction(histoVol.getPointsInCube,
                                                         (bb, posc, rad))
#
                    delta = numpy.take(gridPointsCoords,pointsInCube,0)-posc
                    delta *= delta
                    distA = numpy.sqrt( delta.sum(1) )
                    ptsInSphere = numpy.nonzero(numpy.less_equal(distA, rad))[0]

                    for pti in ptsInSphere:
                        pt = pointsInCube[pti]
                        if pt in insidePoints: continue
                        dist = distA[pti]
                        d = dist-radc
                        if dist < radc:  # point is inside dropped sphere
                            if pt in insidePoints:
                                if d < insidePoints[pt]:
                                    insidePoints[pt] = d
                            else:
                                insidePoints[pt] = d
                        elif d < distance[pt]: # point in region of influence
                            if pt in newDistPoints:
                                if d < newDistPoints[pt]:
                                    newDistPoints[pt] = d
                            else:
                                newDistPoints[pt] = d

            elif self.modelType=='Cylinders':
                cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
                cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])

                for radc, p1, p2 in zip(self.radii[-1], cent1T, cent2T):

                    x1, y1, z1 = p1
                    x2, y2, z2 = p2
                    vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
                    lengthsq = vx*vx + vy*vy + vz*vz
                    l = sqrt( lengthsq )
                    cx, cy, cz = posc = x1+vx*.5, y1+vy*.5, z1+vz*.5
                    radt = l + radc + dpad
                    bb = ( [cx-radt, cy-radt, cz-radt], [cx+radt, cy+radt, cz+radt] )
                    pointsInCube = histoVol.callFunction(histoVol.getPointsInCube,
                                                         (bb, posc, radt))

                    pd = numpy.take(gridPointsCoords,pointsInCube,0) - p1
                    dotp = numpy.dot(pd, vect)
                    rad2 = radc*radc
                    d2toP1 = numpy.sum(pd*pd, 1)
                    dsq = d2toP1 - dotp*dotp/lengthsq

                    pd2 = numpy.take(gridPointsCoords,pointsInCube,0) - p2
                    d2toP2 = numpy.sum(pd2*pd2, 1)

                    for pti, pt in enumerate(pointsInCube):
                        if pt in insidePoints: continue

                        if dotp[pti] < 0.0: # outside 1st cap
                            d = sqrt(d2toP1[pti])
                            if d < distance[pt]: # point in region of influence
                                if pt in newDistPoints:
                                    if d < newDistPoints[pt]:
                                        newDistPoints[pt] = d
                                else:
                                    newDistPoints[pt] = d
                        elif dotp[pti] > lengthsq:
                            d = sqrt(d2toP2[pti])
                            if d < distance[pt]: # point in region of influence
                                if pt in newDistPoints:
                                    if d < newDistPoints[pt]:
                                        newDistPoints[pt] = d
                                else:
                                    newDistPoints[pt] = d
                        else:
                            d = sqrt(dsq[pti])-radc
                            if d < 0.:  # point is inside dropped sphere
                                if pt in insidePoints:
                                    if d < insidePoints[pt]:
                                        insidePoints[pt] = d
                                else:
                                    insidePoints[pt] = d
            elif self.modelType=='Cube':
                insidePoints,newDistPoints=self.getDistancesCube(jtrans, rotMatj,gridPointsCoords, distance, histoVol)
            
#            print("Graham.Mira........................insidePoints=", insidePoints,"\n while ptInd = ", ptInd)
            insidePoints[ptInd]=-0.1
#            print("Graham.Mira........AFTER...........insidePoints=", insidePoints,"\n while ptInd = ", ptInd)

            # save dropped ingredient
            if verbose:
                print("compute distance loop ",time()-t3)
            if drop:
                #print "ok drop",organelle.name,self.name
                organelle.molecules.append([ jtrans, rotMatj, self, ptInd ])
                histoVol.order[ptInd]=histoVol.lastrank
                histoVol.lastrank+=1
            # update free points
            nbFreePoints = histoVol.callFunction(self.updateDistances,(histoVol,insidePoints,
                                                            newDistPoints,
                                                freePoints,nbFreePoints, distance,
                                                histoVol.masterGridPositions, verbose))
            
#            distChanges = {}
#            for pt,dist in insidePoints.items():
#                # swap point at ptIndr with last free one
#                try:
#                    ind = freePoints.index(pt)
#                    tmp = freePoints[nbFreePoints] #last one
#                    freePoints[nbFreePoints] = pt
#                    freePoints[ind] = tmp
#                    nbFreePoints -= 1
#                except ValueError: # pt not in list of free points
#                    pass
#                distChanges[pt] = (histoVol.masterGridPositions[pt],
#                                   distance[pt], dist)
#                distance[pt] = dist
#            print "update freepoints loop ",time()-t4
#            t5=time()
#            # update distances
#            for pt,dist in newDistPoints.items():
#                if not insidePoints.has_key(pt):
#                    distChanges[pt] = (histoVol.masterGridPositions[pt],
#                                       distance[pt], dist)
#                    distance[pt] = dist
#            print "update distances loop ",time()-t5
            
            if sphGeom is not None:
                for po1, ra1 in zip(modCent, modRad):
                    sphCenters.append(po1)
                    sphRadii.append(ra1)
                    sphColors.append(self.color)

            if labDistGeom is not None:
                verts = []
                labels = []
                colors = []
                #for po1, d1,d2 in distChanges.values():
                fpts = freePoints
                for i in range(nbFreePoints):
                    pt = fpts[i]
                    verts.append(histoVol.masterGridPositions[pt])
                    labels.append( "%.2f"%distance[pt])                    
#                for pt in freePoints[:nbFreePoints]:
#                    verts.append(histoVol.masterGridPositions[pt])
#                    labels.append( "%.2f"%distance[pt])
                labDistGeom.Set(vertices=verts, labels=labels)
                #materials=colors, inheritMaterial=0)

            # add one to molecule counter for this ingredient
            self.counter += 1
            self.completion = float(self.counter)/float(self.nbMol)

            if jitterPos>0:
                histoVol.successfullJitter.append(
                    (self, jitterList, collD1, collD2) )
               
            if verbose :
                print('Success nbfp:%d %d/%d dpad %.2f'%(
                nbFreePoints, self.counter, self.nbMol, dpad))
            if self.name=='in  inside':
                histoVol.jitterVectors.append( (trans, jtrans) )

            success = True
            self.rejectionCounter = 0
            
        else: # got rejected
            #self.rbnode = None
            histoVol.callFunction(histoVol.delRB,(rbnode,))
            if runTimeDisplay and moving is not None :
                afvi.vi.deleteObject(moving)
            success = False
            self.haveBeenRejected = True
            histoVol.failedJitter.append(
                (self, jitterList, collD1, collD2) )

            distance[ptInd] = max(0, distance[ptInd]*0.9)# ???
            self.rejectionCounter += 1
            if verbose :
                print('Failed ingr:%s rejections:%d'%(
                self.name, self.rejectionCounter))
            if self.rejectionCounter >= self.rejectionThreshold: #Graham set this to 6000 for figure 13b (Results Fig 3 Test1) otehrwise it fails to fill small guys
                #if verbose :
                print('PREMATURE ENDING of ingredient', self.name)
                self.completion = 1.0

        if sphGeom is not None:
            sphGeom.Set(vertices=sphCenters, radii=sphRadii,
                        materials=sphColors)
            sphGeom.viewer.OneRedraw()
            sphGeom.viewer.update()

        if drop :
            return success, nbFreePoints
        else :
            return success, nbFreePoints,jtrans, rotMatj

    def pandaBullet_relax(self, histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None,drop=True):
        """
        drop the ingredient on grid point ptInd
        """
        histoVol.setupPanda()
        self.vi = histoVol.afviewer.vi
        afvi = histoVol.afviewer
        windowsSize = histoVol.windowsSize
        simulationTimes = histoVol.simulationTimes
        runTimeDisplay = histoVol.runTimeDisplay
        springOptions = histoVol.springOptions
        self.histoVol = histoVol
        rejectionCount = 0
        spacing = histoVol.smallestProteinSize
        jx, jy, jz = self.jitterMax
        jitter = self.getMaxJitter(spacing)
        jitter2 = jitter * jitter

        if self.compNum == 0 :
            organelle = self.histoVol
        else :
            organelle = self.histoVol.organelles[abs(self.compNum)-1]
            #this is hisotVol for cytoplasme
        compNum = self.compNum
        radius = self.minRadius

        gridPointsCoords = histoVol.grid.masterGridPositions

        # compute rotation matrix rotMat
        if compNum>0:
            # for surface points we compute the rotation which
            # aligns the principalVector with the surface normal
            vx, vy, vz = v1 = self.principalVector
            v2 = organelle.surfacePointsNormals[ptInd]
            try :
                rotMat = numpy.array( rotVectToVect(v1, v2 ), 'f')
            except :
                print('PROBLEM ', self.name)
                rotMat = numpy.identity(4)
        else:
            if self.useRotAxis :
                if sum(self.rotAxis) == 0.0 :
                    rotMat=numpy.identity(4)
                else :
                    rotMat=afvi.vi.rotation_matrix(random()*self.rotRange,self.rotAxis)
            else :
                rotMat=histoVol.randomRot.get()

        if verbose :
            pass#print('%s nbs:%2d'%(self.pdb, len(self.positions[0])), end=' ')

        # jitter position loop
        jitterList = []
        collD1 = []
        collD2 = []

        trans = gridPointsCoords[ptInd] # drop point
#        print ("ptID ",ptInd," coord ",trans)
        gridDropPoint = trans
        jtrans,rotMatj = self.oneJitter(spacing,trans,rotMat)
#        print ("jtrans ",jtrans)
        ok = False
        #here should go the simulation
        #1- we build the ingrediant if not already and place the ingrediant at jtrans, rotMatj
        moving=None
        static=[]
        target=None
        targetPoint = jtrans
#        import c4d
        #c4d.documents.RunAnimation(c4d.documents.GetActiveDocument(), True)

        if runTimeDisplay and self.mesh:
            if hasattr(self,"mesh_3d"):
                #create an instance of mesh3d and place it
                name = self.name + str(ptInd)
                if self.mesh_3d is None :
                    self.moving_geom= afvi.vi.Sphere(name,radius=self.radii[0][0],
                                                    parent=afvi.movingMesh)[0]
                    afvi.vi.setTranslation(self.moving_geom,pos=jtrans)
                else :
                    self.moving_geom= afvi.vi.newInstance(name,self.mesh_3d,
                                                matrice=rotMatj,
                                                location=jtrans, parent = afvi.movingMesh)
        #2- get the neighboring object from ptInd
        if histoVol.ingrLookForNeighbours:
            mingrs,listePartner=self.getListePartners(histoVol,jtrans,rotMat,organelle,afvi)
            for i,elem in enumerate(mingrs):
                ing = elem[2]
                t = elem[0]
                r = elem[1]
                ind = elem[3]
                #print "neighbour",ing.name
                if hasattr(ing,"mesh_3d"):
                    #create an instance of mesh3d and place it
                    name = ing.name + str(ind)
                    if ing.mesh_3d is None :
                        ipoly = afvi.vi.Sphere(name,radius=self.radii[0][0],parent=afvi.staticMesh)[0]
                        afvi.vi.setTranslation(ipoly,pos=t)
                    else :
                        ipoly =afvi.vi.newInstance(name,ing.mesh_3d,matrice=r,
                               location=t, parent = afvi.staticMesh)
#                    static.append(ipoly)
                elif isinstance(ing,GrowIngrediant):
                    name = ing.name + str(ind)
                    ipoly =afvi.vi.newInstance(name,afvi.orgaToMasterGeom[ing],
                                               parent = afvi.staticMesh)
#                    static.append(ipoly)
            
            if listePartner : #self.packingMode=="closePartner":
                if verbose:
                    print("len listePartner = ", len(listePartner))
                if not self.force_random:
                    targetPoint,weight = self.pickPartner(mingrs,listePartner,currentPos=jtrans)
                    if targetPoint is None :
                        targetPoint = jtrans
                else :
                    targetPoint = jtrans
#        print "targetPt",len(targetPoint),targetPoint   
#       should be panda util
#        add the rigid body
        self.histoVol.moving = rbnode = self.histoVol.callFunction(self.histoVol.addRB,(self, jtrans, rotMat,),{"rtype":self.Type},)
        self.histoVol.callFunction(self.histoVol.moveRBnode,(rbnode, jtrans, rotMatj,))
        #run he simulation for simulationTimes
#        afvi.vi.frameAdvanced(duration = simulationTimes,display = runTimeDisplay)#,
        histoVol.callFunction(self.histoVol.runBullet,(self,simulationTimes, runTimeDisplay,))
                              #cb=self.getTransfo)
        rTrans,rRot = self.histoVol.getRotTransRB(rbnode)
        #5- we get the resuling transofrmation matrix and decompose ->rTrans rRot
        #use
        #r=[ (self.histoVol.world.contactTestPair(rbnode, n).getNumContacts() > 0 ) for n in self.histoVol.static]
        self.histoVol.static.append(rbnode)
#        rbnode.setMass(0.0)#make it non dynmaics
#        rTrans = afvi.vi.ToVec(afvi.vi.getTranslation(moving))#getPos
#        rRot = afvi.vi.getMatRotation(moving)                   #getRot or getMat?
        #continue, we assume the object is droped test for contact ? and continueuntil there is  some ?
        ok = True
        jtrans = rTrans[:]
        rotMatj = rRot[:]
        jitterPos = 1
        if ok :
            level = 0
            ## get inside points and update distance
            ##
            # use best sperical approcimation
#            print(">>?",self.name,jtrans)
            insidePoints = {}
            newDistPoints = {}
            t3=time()
            #should be replace by self.getPointInside
            if self.modelType=='Spheres':
                self.centT = centT = self.transformPoints(jtrans, rotMatj, self.positions[level])
                centT = self.centT#self.transformPoints(jtrans, rotMatj, self.positions[-1])
#                for pointsInCube,ptsInSphere in self.distances_temp:
                for radc, posc in zip(self.radii[-1], centT):
#                for i,radc in enumerate(self.radii[-1]):
#                    pointsInCube,ptsInSphere,distA = self.distances_temp[i]
#                 
                    rad = radc + dpad
                    x,y,z = posc
#                    #this have already be done in the checkCollision why doing it again
                    bb = ( [x-rad, y-rad, z-rad], [x+rad, y+rad, z+rad] )
                    pointsInCube = histoVol.callFunction(histoVol.getPointsInCube,
                                                         (bb, posc, rad))
#
                    delta = numpy.take(gridPointsCoords,pointsInCube,0)-posc
                    delta *= delta
                    distA = numpy.sqrt( delta.sum(1) )
                    ptsInSphere = numpy.nonzero(numpy.less_equal(distA, rad))[0]

                    for pti in ptsInSphere:
                        pt = pointsInCube[pti]
                        if pt in insidePoints: continue
                        dist = distA[pti]
                        d = dist-radc
                        if dist < radc:  # point is inside dropped sphere
                            if pt in insidePoints:
                                if d < insidePoints[pt]:
                                    insidePoints[pt] = d
                            else:
                                insidePoints[pt] = d
                        elif d < distance[pt]: # point in region of influence
                            if pt in newDistPoints:
                                if d < newDistPoints[pt]:
                                    newDistPoints[pt] = d
                            else:
                                newDistPoints[pt] = d

            elif self.modelType=='Cylinders':
                cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
                cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])

                for radc, p1, p2 in zip(self.radii[-1], cent1T, cent2T):

                    x1, y1, z1 = p1
                    x2, y2, z2 = p2
                    vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
                    lengthsq = vx*vx + vy*vy + vz*vz
                    l = sqrt( lengthsq )
                    cx, cy, cz = posc = x1+vx*.5, y1+vy*.5, z1+vz*.5
                    radt = l + radc + dpad
                    bb = ( [cx-radt, cy-radt, cz-radt], [cx+radt, cy+radt, cz+radt] )
                    pointsInCube = histoVol.callFunction(histoVol.getPointsInCube,
                                                         (bb, posc, radt))

                    pd = numpy.take(gridPointsCoords,pointsInCube,0) - p1
                    dotp = numpy.dot(pd, vect)
                    rad2 = radc*radc
                    d2toP1 = numpy.sum(pd*pd, 1)
                    dsq = d2toP1 - dotp*dotp/lengthsq

                    pd2 = numpy.take(gridPointsCoords,pointsInCube,0) - p2
                    d2toP2 = numpy.sum(pd2*pd2, 1)

                    for pti, pt in enumerate(pointsInCube):
                        if pt in insidePoints: continue

                        if dotp[pti] < 0.0: # outside 1st cap
                            d = sqrt(d2toP1[pti])
                            if d < distance[pt]: # point in region of influence
                                if pt in newDistPoints:
                                    if d < newDistPoints[pt]:
                                        newDistPoints[pt] = d
                                else:
                                    newDistPoints[pt] = d
                        elif dotp[pti] > lengthsq:
                            d = sqrt(d2toP2[pti])
                            if d < distance[pt]: # point in region of influence
                                if pt in newDistPoints:
                                    if d < newDistPoints[pt]:
                                        newDistPoints[pt] = d
                                else:
                                    newDistPoints[pt] = d
                        else:
                            d = sqrt(dsq[pti])-radc
                            if d < 0.:  # point is inside dropped sphere
                                if pt in insidePoints:
                                    if d < insidePoints[pt]:
                                        insidePoints[pt] = d
                                else:
                                    insidePoints[pt] = d
            elif self.modelType=='Cube':
                insidePoints,newDistPoints=self.getDistancesCube(jtrans, rotMatj,gridPointsCoords, distance, histoVol)
            # update free points
            organelle.molecules.append([ jtrans, rotMatj, self, ptInd ])
            histoVol.order[ptInd]=histoVol.lastrank
            histoVol.lastrank+=1    
            nbFreePoints = self.updateDistances(histoVol,insidePoints, newDistPoints, 
                        freePoints, nbFreePoints, distance, 
                        histoVol.grid.masterGridPositions, verbose)

            # save dropped ingredient
            
        
            self.rRot.append(rotMatj)
            self.tTrans.append(jtrans)
            # add one to molecule counter for this ingredient
            self.counter += 1
            self.completion = float(self.counter)/self.nbMol

            if jitterPos>0:
                histoVol.successfullJitter.append(
                    (self, jitterList, collD1, collD2) )  
            if verbose :
                print('Success nbfp:%d %d/%d dpad %.2f'%(
                nbFreePoints, self.counter, self.nbMol, dpad))
            if self.name=='in  inside':
                histoVol.jitterVectors.append( (trans, jtrans) )

            success = True
            self.rejectionCounter = 0
            
        else: # got rejected
            success = False
            histoVol.failedJitter.append(
                (self, jitterList, collD1, collD2) )

            distance[ptInd] = max(0, distance[ptInd]*0.9)
            self.rejectionCounter += 1
            if verbose :
                print('Failed ingr:%s rejections:%d'%(
                self.name, self.rejectionCounter))
            if self.rejectionCounter >= 30:
                if verbose :
                    print('PREMATURE ENDING of ingredient', self.name)
                self.completion = 1.0
        if drop :
            return success, nbFreePoints
        else :
            return success, nbFreePoints,jtrans, rotMatj
                
class SingleSphereIngr(Ingredient):
    """
    This Ingredient is represented by a single sphere
    and either a single radius, or a list of radii and offset vectors
    for each sphere representing the ingredient
    """
    def __init__(self, molarity=0.0, radius=None, position=None,sphereFile=None,
                 packingPriority=0, name=None, pdb=None,
                 color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1,
                 principalVector=(1,0,0), meshFile=None, packingMode='random',
                 placeType="jitter",Type="SingleSphere",
                 meshObject=None,nbMol=0,**kw):

        Ingredient.__init__(self, molarity=molarity, radii=[[radius],], positions=[[position]], positions2=None,
                 sphereFile=sphereFile, packingPriority=packingPriority, name=name, pdb=pdb, 
                 color=color, nbJitter=nbJitter, jitterMax=jitterMax,
                 perturbAxisAmplitude = perturbAxisAmplitude, principalVector=principalVector,
                 meshFile=meshFile, packingMode=packingMode,placeType=placeType,
                 meshObject=meshObject,nbMol=nbMol,Type=Type,)

        if name == None:
            name = "%5.2f_%f"% (radius,molarity)
        self.name = name
        self.singleSphere = True
        self.minRadius = self.radii[0][0]
        self.encapsulatingRadius = radius

class SingleCubeIngr(Ingredient):
    """
    This Ingredient is represented by a single cube
    """
    def __init__(self, molarity=0.0, radii=None, 
                 positions=[[[0,0,0],[0,0,0],[0,0,0],]], 
                 positions2=[[[0,0,0]]],
                 sphereFile=None,
                 packingPriority=0, name=None, pdb=None,
                 color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1,
                 principalVector=(1,0,0), meshFile=None, packingMode='random',
                 placeType="jitter",Type="SingleCube",
                 meshObject=None,nbMol=0,**kw):

        Ingredient.__init__(self, molarity=molarity, radii=radii, positions=positions, positions2=None,
                 sphereFile=sphereFile, packingPriority=packingPriority, name=name, pdb=pdb, 
                 color=color, nbJitter=nbJitter, jitterMax=jitterMax,
                 perturbAxisAmplitude = perturbAxisAmplitude, principalVector=principalVector,
                 meshFile=meshFile, packingMode=packingMode,placeType=placeType,
                 meshObject=meshObject,nbMol=nbMol,Type=Type,**kw)

        if name == None:
            name = "%5.2f_%f"% (radii[0][0],molarity)
        self.name = name
        self.singleSphere = False
        self.modelType = "Cube"
        self.collisionLevel = 0
        self.encapsulatingRadius = max(radii[0]) #should the sphere that encapsulated the cube
        self.center = [0.,0.,0.]
        radii = numpy.array(radii)
        self.minRadius =  min(radii[0]/2.0) #should have three radii sizex,sizey,sizez 
        self.encapsulatingRadius = self.maxRadius = math.sqrt(max(radii[0]/2.0)*max(radii[0]/2.0)+min(radii[0]/2.0)*min(radii[0]/2.0))
        self.bb=[-radii[0]/2.,radii[0]/2.]
        self.positions = [[-radii[0]/2.]]
        self.positions2 = [[radii[0]/2.]]
#        if positions2 is not None and positions is not None:
#            self.bb=[positions[0],positions2[0]]
#            x1, y1, z1 = self.bb[0]
#            x2, y2, z2 = self.bb[0]
#            vx, vy, vz = vect = (x2-x1, y2-y1, z2-z1)
#            self.center = x1+vx*.5, y1+vy*.5, z1+vz*.5
#            self.positions = positions
#            self.positions2 = positions2
        #position and position2 are the cornerPoints of the cube
        self.radii = radii


        
class MultiSphereIngr(Ingredient):
    """
    This Ingredient is represented by a collection of spheres specified by radii
    and positions. The principal Vector will be used to align the ingredient
    """
    def __init__(self, molarity=0.0, radii=None, positions=None, sphereFile=None,
                 packingPriority=0, name=None,
                 pdb=None, color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1,Type="MultiSphere",
                 principalVector=(1,0,0), meshFile=None, packingMode='random',
                 placeType="jitter",
                 meshObject=None,nbMol=0,**kw):

        Ingredient.__init__(self, molarity=molarity, radii=radii, positions=positions, positions2=None,
                 sphereFile=sphereFile, packingPriority=packingPriority, name=name, pdb=pdb, 
                 color=color, nbJitter=nbJitter, jitterMax=jitterMax,
                 perturbAxisAmplitude = perturbAxisAmplitude, principalVector=principalVector,
                 meshFile=meshFile, packingMode=packingMode,placeType=placeType,
                 meshObject=meshObject,nbMol=nbMol,Type=Type,**kw)

        if name == None:
            name = "%s_%f"% (str(radii),molarity)
        self.name = name
        self.singleSphere = False
#        print ("done  MultiSphereIngr")
#        raw_input()


class MultiCylindersIngr(Ingredient):
    """
    This Ingredient is represented by a collection of cylinder specified by
    radii, positions and positions2.
    The principal Vector will be used to align the ingredient
    """
    def __init__(self, molarity=0.0, radii=None, positions=None, positions2=None,
                 sphereFile=None, packingPriority=0, name=None,
                 pdb=None, color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1,
                 principalVector=(1,0,0), meshFile=None, packingMode='random',
                 placeType="jitter",Type="MultiCylinder",
                 meshObject=None,nbMol=0,**kw):

        Ingredient.__init__(self, molarity=molarity, radii=radii, positions=positions, positions2=positions2,
                 sphereFile=sphereFile, packingPriority=packingPriority, name=name, pdb=pdb, 
                 color=color, nbJitter=nbJitter, jitterMax=jitterMax,
                 perturbAxisAmplitude = perturbAxisAmplitude, principalVector=principalVector,
                 meshFile=meshFile, packingMode=packingMode,placeType=placeType,
                 meshObject=meshObject,nbMol=nbMol,Type=Type,**kw)

        if name == None:
            name = "%s_%f"% (str(radii),molarity)
        self.name = name
        self.singleSphere = False
        self.modelType = "Cylinders"
        self.collisionLevel = 0
        self.minRadius = radii[0][0]
#        self.encapsulatingRadius = radii[0][0]  #Graham worry: 9/8/11 This is incorrect... shoudl be max(radii[0]) or radii[0][1] 
        self.encapsulatingRadius = radii[0][0]
#        print('encapsulating Radius is probably wrong- fix the array')
        self.useLength = False
        if "useLength" in kw:
            self.useLength = kw["useLength"]
        if positions2 is not None and positions is not None:
            #shoulde the overall length of the object from bottom to top
            bb = self.getBigBB()
            d = numpy.array(bb[1])-numpy.array(bb[0])
            s = numpy.sum(d*d)
            self.length  = math.sqrt(s ) #diagonal
        self.KWDS["useLength"]={}

    def getBigBB(self):
        #one level for cylinder
        bbs=[]
        for radc, p1, p2 in zip(self.radii[0], self.positions[0], self.positions2[0]):            
            bb = self.correctBB(p1,p2,radc)
            bbs.append(bb)
        #get min and max from all bbs
        maxBB = [0,0,0]
        minBB = [9999,9999,9999]
        for bb in bbs:
            for i in range(3):
                if bb[0][i] < minBB[i]:
                    minBB[i] =bb[0][i]
                if bb[1][i] > maxBB[i]:
                    maxBB[i] = bb[1][i]
                if bb[1][i] < minBB[i]:
                    minBB[i] = bb[1][i]
                if bb[0][i] > maxBB[i]:
                    maxBB[i] = bb[0][i]
        bb = [minBB,maxBB]
        return bb        

#do we need this class?
class GrowIngrediant(MultiCylindersIngr):
    def __init__(self, molarity=0.0, radii=None, positions=None, positions2=None,
                 sphereFile=None, packingPriority=0, name=None,
                 pdb=None, color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1,length = 10.,closed = False,
                 modelType="Cylinders",biased=1.0,
                 principalVector=(1,0,0), meshFile=None, packingMode='random',
                 placeType="jitter",marge=20.0,meshObject=None,orientation = (1,0,0),
                 nbMol=0,Type="Grow",walkingMode="sphere",**kw):

        MultiCylindersIngr.__init__(self, molarity=molarity, radii=radii, positions=positions, positions2=positions2,
                 sphereFile=sphereFile, packingPriority=packingPriority, name=name, pdb=pdb, 
                 color=color, nbJitter=nbJitter, jitterMax=jitterMax,
                 perturbAxisAmplitude = perturbAxisAmplitude, principalVector=principalVector,
                 meshFile=meshFile, packingMode=packingMode,placeType=placeType,
                 meshObject=meshObject,nbMol=nbMol,Type=Type,**kw)
        if name == None:
            name = "%s_%f"% (str(radii),molarity)
        self.name = name
        self.singleSphere = False
        self.modelType = modelType
        self.collisionLevel = 0
        self.minRadius = radii[0][0]
#        self.encapsulatingRadius = radii[0][0] #Graham worry: 9/8/11 This is incorrect... shoudl be max(radii[0]) or radii[0][1] 
        self.encapsulatingRadius = radii[0][0]
#        print('encapsulating Radius is probably wrong- fix the array')
        self.marge = marge
        self.length = length
        self.closed = closed
        self.nbCurve=0
        self.results=[]
        self.listePtLinear=[]
        self.listePtCurve=[] #snake
        self.Ptis=[]    #snakePts
        self.currentLength=0.#snakelength
        self.direction=None#direction of growing
        #can be place either using grid point/jittering or dynamics
#        self.uLength = 0. #length of the cylinder or averall radius for sphere, this is the lenght of one unit
        self.uLength = 10
        self.unitNumberF = 0 #number of unit pose so far forward
        self.unitNumberR = 0 #number of unit pose so far reverse
        self.orientation = orientation
        self.seedOnPlus = True   #The filament should continue to grow on its (+) end
        self.seedOnMinus = False #The filamen should continue to grow on its (-) end.
        self.vector=[0.,0.,0.]
        self.biased = biased
        self.absoluteLengthMax =99999999.9999#(default value is infinite or some safety number like 1billion)
        self.probableLengthEquation = None 
        #(this can be a number or an equation, e.g., every actin should grow to 
        #10 units long, or this actin fiber seed instance should grow to (random*10)^2
        #actually its a function of self.uLength like self.uLength * 10. or *(random*10)^2
        self.ingGrowthMatrix = numpy.identity(4)
        #(ultimately, we'll build a database for these (David Goodsell has a few examples), 
        #but users should be able to put in their own, so for a test for now, lets say we'll 
        #grow one unit for a singleSphereIng r=60 along its X as [55,0,0;1,0,0;0,1,0;0,0,1]
        self.ingGrowthWobbleFormula = None
        #(this could be a rotation matrix to make a helix, or just a formula, 
        #like the precession algorithm Michel and I already put in 
        #for surface ingredients.
        self.constraintMarge = False
        self.cutoff_boundary = 1.0
        self.cutoff_surface = 5.0
        #mesh object representing one uLength? or a certain length
        self.unitParent = None
        self.unitParentLength = 0.
        self.walkingMode = walkingMode #["sphere","lattice"]
        
        self.KWDS["length"]={}
        self.KWDS["closed"]={}
        self.KWDS["uLength"]={}        
        self.KWDS["biased"]={}
        self.KWDS["marge"]={}
        self.KWDS["orientation"]={}
        self.KWDS["walkingMode"]={}
        self.KWDS["constraintMarge"]={}
        
        self.OPTIONS["length"]={"name":"length","value":self.length,"default":self.length,"type":"float","min":0,"max":10000,"description":"snake total length"}
        self.OPTIONS["uLength"]={"name":"uLength","value":self.uLength,"default":self.uLength,"type":"float","min":0,"max":10000,"description":"snake unit length"}
        self.OPTIONS["closed"]={"name":"closed","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"closed snake"}                          
        self.OPTIONS["biased"]={"name":"biased","value":0.0,"default":0.0,"type":"float","min":0,"max":10,"description":"snake biased"}
        self.OPTIONS["marge"]={"name":"marge","value":10.0,"default":10.0,"type":"float","min":0,"max":10000,"description":"snake angle marge"}
        self.OPTIONS["constraintMarge"]={"name":"constraintMarge","value":False,"default":False,"type":"bool","min":0.,"max":0.,"description":"lock the marge"}                          
        self.OPTIONS["orientation"]={"name":"orientation","value":[0.,1.,0.],"default":[0.,1.,0.],"min":0,"max":1,"type":"vector","description":"snake orientation"}
        self.OPTIONS["walkingMode"]={"name":"walkingMode","value":"random","values":['sphere', 'lattice'],"min":0.,"max":0.,"default":'sphere',"type":"liste","description":"snake mode"}

                        
    def reset(self):
        self.nbCurve=0
        self.results=[]
        self.listePtLinear=[]
        self.listePtCurve=[] #snake
        self.Ptis=[]    #snakePts
        self.currentLength=0.#snakelength        
        
    def getNextPtIndCyl(self,jtrans, rotMatj,freePoints,histoVol):
#        print jtrans, rotMatj
        cent2T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
        jx, jy, jz = self.jitterMax
        jitter = self.getMaxJitter(histoVol.smallestProteinSize)
        jitter2 = jitter * jitter
        if len(cent2T) == 1 :
            cent2T=cent2T[0]
        tx, ty, tz = cent2T
        dx = jx*jitter*gauss(0., 0.3)
        dy = jy*jitter*gauss(0., 0.3)
        dz = jz*jitter*gauss(0., 0.3)
#        print "d",dx,dy,dz
        nexPt = (tx+dx, ty+dy, tz+dz)
        #where is this point in the grid
        #ptInd = histoVol.grid.getPointFrom3D(nexPt)
        t,r = self.oneJitter(histoVol.smallestProteinSize,cent2T,rotMatj)
        ptInd = histoVol.grid.getPointFrom3D(t)
        dv = numpy.array(nexPt) - numpy.array(cent2T)
        d = numpy.sum(dv*dv)
        return ptInd,dv,sqrt(d)

    def checkPointComp(self,point):
        ptID = self.histoVol.grid.getPointFrom3D(point)
        if self.compNum != self.histoVol.grid.gridPtId[ptID]:
            return False
        else :
            return True
            
    def checkPointSurface(self,point,cutoff):
        if not hasattr(self,"histoVol") :
            return False
        if self.compNum == 0 :
            organelle = self.histoVol
        else :
            organelle = self.histoVol.organelles[abs(self.compNum)-1]
        compNum = self.compNum
#        print "compNum ",compNum
        if compNum < 0 :
            sfpts = organelle.surfacePointsCoords
            delta = numpy.array(sfpts)-numpy.array(point)
            delta *= delta
            distA = numpy.sqrt( delta.sum(1) )
#            print len(distA)
            test = distA < cutoff
            if True in test:
                return True
        elif compNum == 0 :
            for o in self.histoVol.organelles:
                sfpts = o.surfacePointsCoords
                delta = numpy.array(sfpts)-numpy.array(point)
                delta *= delta
                distA = numpy.sqrt( delta.sum(1) )
#                print len(distA)
                test = distA < cutoff
                if True in test:
                    return True
        return False

    def getJtransRot(self,pt1,pt2):
#        print "inut",pt1,pt2
        v,d = self.vi.measure_distance(pt1,pt2,vec=True)

    #Start jtrans section that is new since Sept 8, 2011 version
        n = numpy.array(pt1) - numpy.array(pt2)
        #normalize the vector n
        nn=self.vi.unit_vector(n) #why normalize ?
        
        #get axis of rotation between the plane normal and Z
        v1 = nn
        v2 = [0.,0.,1.0]
        cr = numpy.cross(v1,v2)
        axis = self.vi.unit_vector(cr)
        #get the angle between the plane normal and Z
        angle = self.vi.angle_between_vectors(v2,v1)
        #get the rotation matrix between plane normal and Z
        mx = self.vi.rotation_matrix(-angle, axis)#.transpose()
        jtrans = n
    #End jtrans section that is new since Sept 8, 2011 version
        
        matrix = self.vi.ToMat(mx).transpose()
        rotMatj = matrix.reshape((4,4))
        return rotMatj.transpose(),numpy.array(pt1)+numpy.array(v)/2.#.transpose()jtrans

    def walkLatticeSurface(self,pts,distance,histoVol, size,mask,marge=999.0,
                    checkcollision=True,saw=True):
        #take the next random point in the windows size +1 +2
        #extended = histoVol.getPointsInCube()
        #cx,cy,cz = posc = pts#histoVol.grid.masterGridPositions[ptId]
        #step = histoVol.grid.gridSpacing*size
        #bb = ( [cx-step, cy-step, cz-step], [cx+step, cy+step, cz+step] )
#        print pts,step,bb
        #if self.runTimeDisplay > 1:
        #    box = self.vi.getObject("collBox")
        #    if box is None:
        #        box = self.vi.Box('collBox', cornerPoints=bb,visible=1)
        #    else :
#       #             self.vi.toggleDisplay(box,True)
        #        self.vi.updateBox(box,cornerPoints=bb)
        #        self.vi.update()
        #pointsInCube = histoVol.getPointsInCube(bb, posc, step,addSP=False)
        #pointsInCubeCoords=numpy.take(histoVol.grid.masterGridPositions,pointsInCube,0)
#        print pointsInCube
        #take a random point from it OR use gradient info OR constrain by angle
        o = self.histoVol.organelles[abs(self.compNum)-1]
        sfpts = o.surfacePointsCoords
        
        found = False
        attempted = 0
        safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking"+self.name
            sp = self.vi.getObject(name)
            if sp is None :
                sp=self.vi.Sphere(name,radius=10.0)[0]
            #namep = "latticePoints"
            #pts= self.vi.getObject(namep)
            #if pts is None :
            #    pts = self.vi.Points(namep)
            #pts.Set(vertices = pointsInCubeCoords)
            #sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()        
        while not found :
            #print attempted
            if attempted > safetycutoff:
                return None,False
            newPtId = int(random()*len(sfpts))
            v = sfpts[newPtId]#histoVol.grid.masterGridPositions[newPtId]
#            print newPtId,v,len(pointsInCube)
            if self.runTimeDisplay :
                self.vi.setTranslation(sp,self.vi.FromVec(v))
                self.vi.update()            
            if saw : #check if already taken, but didnt prevent cross
                if pointsInCube[newPtId] in self.Ptis:
                    attempted +=1
                    continue
            angle=self.vi.angle_between_vectors(numpy.array(posc),numpy.array(v))
            v,d = self.vi.measure_distance(numpy.array(posc),numpy.array(v),vec=True)
#            print angle,abs(math.degrees(angle)),marge,d
            if abs(math.degrees(angle)) <= marge :
                closeS = self.checkPointSurface(v,cutoff=self.cutoff_surface)
                inComp = self.checkPointComp(v)
                if closeS or not inComp :#or d > self.uLength:
                    #print "closeS or not good comp or too long"
                    attempted +=1
                    continue
                if checkcollision:
                    #print "checkColl"
                    m = numpy.identity(4)
                    collision = self.checkSphCollisions([v,],[float(self.uLength)*1.,], 
                                            [0.,0.,0.], m, 0,
                                            histoVol.grid.masterGridPositions,
                                            distance, 
                                            histoVol)
                    if not collision :
                        found = True
                        self.Ptis.append(pointsInCube[newPtId])
                        return v,True
                    else : #increment the range
                        #print "collision"
                        if not self.constraintMarge :
                            if marge >=180 :
                                return None,False
                            marge+=1
                        attempted +=1
                        continue
                found = True
                self.Ptis.append(pointsInCube[newPtId])
                return v,True
            else :
                attempted+=1
                continue
        

    def walkLattice(self,pts,distance,histoVol, size,marge=999.0,
                    checkcollision=True,saw=True):
        #take the next random point in the windows size +1 +2
        #extended = histoVol.getPointsInCube()
        cx,cy,cz = posc = pts#histoVol.grid.masterGridPositions[ptId]
        step = histoVol.grid.gridSpacing*size
        bb = ( [cx-step, cy-step, cz-step], [cx+step, cy+step, cz+step] )
#        print pts,step,bb
        if self.runTimeDisplay > 1:
            box = self.vi.getObject("collBox")
            if box is None:
                box = self.vi.Box('collBox', cornerPoints=bb,visible=1)
            else :
#                    self.vi.toggleDisplay(box,True)
                self.vi.updateBox(box,cornerPoints=bb)
                self.vi.update()
        pointsInCube = histoVol.getPointsInCube(bb, posc, step,addSP=False)
        pointsInCubeCoords=numpy.take(histoVol.grid.masterGridPositions,pointsInCube,0)
#        print pointsInCube
        #take a random point from it OR use gradient info OR constrain by angle
        found = False
        attempted = 0
        safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking"+self.name
            sp = self.vi.getObject(name)
            if sp is None :
                sp=self.vi.Sphere(name,radius=10.0)[0]
            namep = "latticePoints"
            pts= self.vi.getObject(namep)
            if pts is None :
                pts = self.vi.Points(namep)
            pts.Set(vertices = pointsInCubeCoords)
            #sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()        
        while not found :
            #print attempted
            if attempted > safetycutoff:
                return None,False
            newPtId = int(random()*len(pointsInCube))
            v = pointsInCubeCoords[newPtId]#histoVol.grid.masterGridPositions[newPtId]
#            print newPtId,v,len(pointsInCube)
            if self.runTimeDisplay :
                self.vi.setTranslation(sp,self.vi.FromVec(v))
                self.vi.update()            
            if saw : #check if already taken, but didnt prevent cross
                if pointsInCube[newPtId] in self.Ptis:
                    attempted +=1
                    continue
            angle=self.vi.angle_between_vectors(numpy.array(posc),numpy.array(v))
            v,d = self.vi.measure_distance(numpy.array(posc),numpy.array(v),vec=True)
#            print angle,abs(math.degrees(angle)),marge,d
            if abs(math.degrees(angle)) <= marge :
                closeS = self.checkPointSurface(v,cutoff=self.cutoff_surface)
                inComp = self.checkPointComp(v)
                if closeS or not inComp :#or d > self.uLength:
                    #print "closeS or not good comp or too long"
                    attempted +=1
                    continue
                if checkcollision:
                    #print "checkColl"
                    m = numpy.identity(4)
                    collision = self.checkSphCollisions([v,],[float(self.uLength)*1.,], 
                                            [0.,0.,0.], m, 0,
                                            histoVol.grid.masterGridPositions,
                                            distance, 
                                            histoVol)
                    if not collision :
                        found = True
                        self.Ptis.append(pointsInCube[newPtId])
                        return v,True
                    else : #increment the range
                        #print "collision"
                        if not self.constraintMarge :
                            if marge >=180 :
                                return None,False
                            marge+=1
                        attempted +=1
                        continue
                found = True
                self.Ptis.append(pointsInCube[newPtId])
                return v,True
            else :
                attempted+=1
                continue
        
    def walkSphere(self,pt1,pt2,distance,histoVol,marge = 90.0,checkcollision=True):
        v,d = self.vi.measure_distance(pt1,pt2,vec=True)
        found = False
        attempted = 0
        pt = [0.,0.,0.]
        angle=0.
        safetycutoff = 10000
        if self.constraintMarge:
            safetycutoff = 200
        if self.runTimeDisplay:
            name = "walking"+self.name
            sp = self.vi.getObject(name)
            if sp is None :
                sp=self.vi.Sphere(name,radius=2.0)[0]
            #sp.SetAbsPos(self.vi.FromVec(startingPoint))
            self.vi.update()
        while not found :
            if attempted >= safetycutoff:
                return None,False#numpy.array(pt2).flatten()+numpy.array(pt),False
            pt = self.vi.randpoint_onsphere(self.uLength)
            newPt = numpy.array(pt2).flatten()+numpy.array(pt)
            if self.runTimeDisplay  >= 2:
                self.vi.setTranslation(sp,newPt)
                self.vi.update()
            angle=self.vi.angle_between_vectors(numpy.array(v),numpy.array(pt))
#            print angle,math.degrees(angle),marge
#            print self.histoVol.grid.boundingBox #left-bottom to right-top
            if abs(math.degrees(angle)) <= marge :
#                print "ok"
                #check if in bounding boc
                inside = histoVol.grid.checkPointInside(newPt,dist=self.cutoff_boundary)
                closeS = self.checkPointSurface(newPt,cutoff=self.cutoff_surface)
                inComp = self.checkPointComp(newPt)
#                print "inside,closeS ",inside,closeS
                if not inside or closeS or not inComp:
#                    print "oustide"
                    if not self.constraintMarge :
                        if marge >=175 :
                            return None,False
                        marge+=1
                    else :
                        attempted +=1
                    continue
                if checkcollision:
#                    print self.modelType
                    if self.modelType=='Cylinders':
                        #outise is consider as collision...?
#                        rotMatj,jtrans=self.getJtransRot(numpy.array(pt2).flatten(),newPt)
                        m=[[ 1.,  0.,  0.,  0.],
                           [ 0.,  1.,  0.,  0.],
                           [ 0.,  0.,  1.,  0.],
                           [ 0.,  0.,  0.,  1.]]
##                        print rotMatj,jtrans
#                        print "before collide"
#                        collision = self.checkSphCollisions([newPt,],[float(self.uLength)*1.,], 
#                                            [0.,0.,0.], m, 0,
#                                            histoVol.grid.masterGridPositions,
#                                            distance, 
#                                            histoVol)
                        collision = self.checkCylCollisions(
                            [numpy.array(pt2).flatten()], [newPt],
                            self.radii[-1], [0.,0.,0.], m, 
                            histoVol.grid.masterGridPositions,
                            distance, 
                            histoVol)
#                        print "collision",collision
                        if not collision :
                            found = True
                            return numpy.array(pt2).flatten()+numpy.array(pt),True
                        else : #increment the range
                            if not self.constraintMarge :
                                if marge >=180 :
                                    return None,False
                                marge+=1
                            else :
                                attempted +=1
                            continue
                else :
                    found = True
                    return numpy.array(pt2).flatten()+numpy.array(pt),True
#                attempted += 1
            else :
                attempted += 1
                continue
            attempted += 1
        return numpy.array(pt2).flatten()+numpy.array(pt),True
        
    def grow(self,previousPoint,startingPoint,secondPoint,listePtCurve,
              listePtLinear,histoVol, ptInd, 
              freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,r=False):
        #r is for reverse growing
        Done = False
        runTimeDisplay = histoVol.runTimeDisplay
        gridPointsCoords = histoVol.grid.masterGridPositions
        #if runTimeDisplay:
        parent = histoVol.afviewer.orgaToMasterGeom[self]
        k=0
        success = False
        safetycutoff = 10000
        if self.constraintMarge:
            safetycutoff = 100
        counter = 0
        mask=None
        if self.walkingMode == "lattice" and self.compNum > 0:
            o = self.histoVol.organelles[abs(self.compNum)-1]
            v=o.surfacePointsCoords
            mask=numpy.one(len(v),int)

        while not Done:
            if k > safetycutoff :
                self.listePtCurve.append(listePtCurve)
#                self.nbCurve+=1
#                self.completion = float(self.nbCurve)/self.nbMol             
                return success, nbFreePoints,freePoints
            else :
                k+=1          
            previousPoint = startingPoint
            startingPoint = secondPoint
            if runTimeDisplay or histoVol.afviewer.doSpheres:
                name = str(len(listePtLinear))+"sp"+self.name + str(ptInd)
                if r :
                    name = str(len(listePtLinear)+1)+"sp"+self.name + str(ptInd)
                sp=self.vi.Sphere(name,radius=self.radii[0][0],parent=parent)[0]
                self.vi.setTranslation(sp,pos=startingPoint)
#                sp.SetAbsPos(self.vi.FromVec(startingPoint))
                #sp=self.vi.newInstance(name,histoVol.afviewer.pesph,
#                                       location=startingPoint,parent=parent)
                #self.vi.scaleObj(sp,self.radii[0][0])                
                if runTimeDisplay : self.vi.update()
#            print "ok,p,start",previousPoint,startingPoint
            if self.walkingMode == "sphere":
                secondPoint,success = self.walkSphere(previousPoint,startingPoint,
                                                      distance,histoVol,
                                                      marge = self.marge,
                                                      checkcollision=True)            
            if self.walkingMode == "lattice" and self.compNum > 0:
                secondPoint,success,mask = self.walkLatticeSurface(startingPoint,distance,histoVol, 
                                                  2,mask,marge=self.marge,
                                            checkcollision=False,saw=True)            
            elif self.walkingMode == "lattice":
                secondPoint,success = self.walkLattice(startingPoint,distance,histoVol, 
                                                  2,marge=self.marge,
                                            checkcollision=False,saw=True)
            #print "afterWalk",secondPoint,success
            #need to check the second point collision
            #checkCylCollisions
            #ssuccess = True#self.checkPoint(secondPoint)
            #do we use the grid ? or the distClostSurface or the distance ?
            if secondPoint is None :
                break
            v,d = self.vi.measure_distance(startingPoint,secondPoint,vec=True)
            
            rotMatj,jtrans=self.getJtransRot(startingPoint,secondPoint)
#            print rotMatj,jtrans
            if r :
                rotMatj,jtrans=self.getJtransRot(secondPoint,startingPoint)
            cent1T = self.transformPoints(jtrans, rotMatj, self.positions[-1])
            cent2T = self.transformPoints(jtrans, rotMatj, self.positions2[-1])
             
#            success, nbFreePoints,jtrans, rotMatj=self._place(histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
#              stepByStep=stepByStep, verbose=verbose,
#              sphGeom=sphGeom, labDistGeom=labDistGeom, debugFunc=debugFunc,
#              sphCenters=sphCenters,  sphRadii=sphRadii, sphColors=sphColors,drop=False)
#            print "done ?",success,k,self.currentLength
            if success:
                self.results.append([jtrans,rotMatj])
                if r :
                    listePtLinear.insert(0,secondPoint)
                else :
                    listePtLinear.append(secondPoint)
                self.currentLength +=d
#                self.completion = float(self.currentLength)/self.length
#                print "compl",self.completion
                cent1T = startingPoint#self.transformPoints(jtrans, rotMatj, self.positions[-1])
                cent2T = secondPoint#self.transformPoints(jtrans, rotMatj, self.positions2[-1])
                if len(cent1T) == 1 :
                    cent1T=cent1T[0]
                if len(cent2T) == 1 :
                    cent2T=cent2T[0]
#                print cent1T,cent2T
                if runTimeDisplay:
                    name = str(len(listePtLinear))+self.name + str(ptInd)+"cyl"
                    if r :
                        name = str(len(listePtLinear)+1)+self.name + str(ptInd)+"cyl"                    
                    cyl=self.vi.oneCylinder(name,cent1T,cent2T,parent=parent,
                                            instance=histoVol.afviewer.becyl,
                                            radius=self.radii[0][0])
                                            
                    #self.vi.updateTubeMesh(cyl,cradius=self.radii[0][0])
                    self.vi.update()
                if r :
                    listePtCurve.insert(0,jtrans)
                else :   
                    listePtCurve.append(jtrans)
#        if success:
#            for jtrans,rotMatj in self.results:
                #every two we update distance from the previous
                if len(self.results) >= 1 :
                    #jtrans, rotMatj = self.results[-1]
#                    print "trasnfor",jtrans,rotMatj
                    cent1T=self.transformPoints(jtrans, rotMatj, self.positions[-1])
                    insidePoints = {}
                    newDistPoints = {}
                    insidePoints,newDistPoints = self.getInsidePoints(histoVol.grid,
                                        gridPointsCoords,dpad,distance,
                                        centT=cent1T,
                                        jtrans=jtrans, 
                                        rotMatj=rotMatj)
                    # update free points
                    #print "update free points",len(insidePoints)
                    nbFreePoints = self.updateDistances(histoVol,insidePoints, newDistPoints, 
                                freePoints, nbFreePoints, distance, 
                                gridPointsCoords, verbose)
    #                print "distance",d
#                    print "free",nbFreePoints
            #Start Graham on 5/16/12 This progress bar doesn't work properly... compare with my version in HistoVol
                if histoVol.afviewer is not None and hasattr(histoVol.afviewer,"vi"):
                    histoVol.afviewer.vi.progressBar(progress=int(self.currentLength / self.length),
                                                         label=self.name)
            #Start Graham on 5/16/12 This progress bar doesn't work properly... compare with my version in HistoVol
                if self.currentLength >= self.length:
                    Done = True
                    self.counter = counter +1
#                    return success, nbFreePoints
            else :
                secondPoint = startingPoint
                break
        return success, nbFreePoints,freePoints

    def updateGrid(self,rg,histoVol,dpad,freePoints, nbFreePoints, distance, 
                        gridPointsCoords, verbose):
        for i in range(rg):#len(self.results)):
            jtrans, rotMatj = self.results[-i]
            cent1T=self.transformPoints(jtrans, rotMatj, self.positions[-1])
            insidePoints = {}
            newDistPoints = {}
            insidePoints,newDistPoints = self.getInsidePoints(histoVol.grid,
                                gridPointsCoords,dpad,distance,
                                centT=cent1T,
                                jtrans=jtrans, 
                                rotMatj=rotMatj)
            # update free points
            nbFreePoints = self.updateDistances(histoVol,insidePoints, newDistPoints, 
                        freePoints, nbFreePoints, distance, 
                        gridPointsCoords, verbose)  
            return nbFreePoints,freePoints

    def getFirstPoint(self,ptInd,seed=0):
        #randomize the orientation in the hemisphere following the direction.
        v = self.vi.rotate_about_axis(numpy.array(self.orientation),
                                      random()*math.radians(self.marge),#or marge ?
                                      axis=list(self.orientation).index(0))
        self.vector = numpy.array(v).flatten()*self.uLength# = (1,0,0)self.vector.flatten()
        secondPoint = self.startingpoint+self.vector
        #seed="F"
        if seed :
            seed="R"
            secondPoint = self.startingpoint-self.vector
        else :
            seed="F"
        inside = self.histoVol.grid.checkPointInside(secondPoint,dist=self.cutoff_boundary)
        closeS = self.checkPointSurface(secondPoint,cutoff=self.cutoff_surface)
        success = False
        if not inside or closeS:
            safety = 200
            k=0
            while not inside or closeS:
                if k > safety :
                    return None
                else :
                    k+=1
                secondPoint = self.startingpoint+numpy.array(self.vi.randpoint_onsphere(self.uLength))
                inside = self.histoVol.grid.checkPointInside(secondPoint,dist=self.cutoff_boundary)
                closeS = self.checkPointSurface(secondPoint,cutoff=self.cutoff_surface)
        if self.runTimeDisplay:
            parent = self.histoVol.afviewer.orgaToMasterGeom[self]
            name = "Startsp"+self.name+seed
            #sp=self.vi.Sphere(name,radius=self.radii[0][0],parent=parent)[0]
            if seed=="F" :
                #sp=self.vi.newInstance(name,self.histoVol.afviewer.pesph,
                #                   location=self.startingpoint,parent=parent)
                #self.vi.scaleObj(sp,self.radii[0][0])
                sp=self.vi.Sphere(name,radius=self.radii[0][0],parent=parent)[0]
                self.vi.setTranslation(sp,pos=self.startingpoint)
#            sp.SetAbsPos(self.vi.FromVec(startingPoint))
            cyl = self.vi.oneCylinder(name+"cyl",self.startingpoint,secondPoint,
                                      instance=self.histoVol.afviewer.becyl,
                                      parent=parent,radius=self.radii[0][0])
#            self.vi.updateTubeMesh(cyl,cradius=self.radii[0][0])
            #laenge,mx=self.getTubeProperties(head,tail)
            self.vi.update()        
        return secondPoint

    #isit the jitter place ? I guess  Why are there two jitter_place functions?  What is this one?
    def jitter_place(self, histoVol, ptInd, freePoints, nbFreePoints, distance, dpad,
              stepByStep=False, verbose=False,
              sphGeom=None, labDistGeom=None, debugFunc=None,
              sphCenters=None,  sphRadii=None, sphColors=None):
        #ptInd is the starting point
        #loop over until length reach or cant grow anymore
#        self.nbMol = 1               
        print("JitterPlace 2....................................................................")
        success = True
        self.vi = histoVol.afviewer.vi
        afvi = histoVol.afviewer
        self.histoVol=histoVol
        windowsSize = histoVol.windowsSize
        simulationTimes = histoVol.simulationTimes
        gridPointsCoords = histoVol.grid.masterGridPositions
        self.runTimeDisplay=runTimeDisplay = histoVol.runTimeDisplay
        self.startingpoint = previousPoint = startingPoint = numpy.array(histoVol.grid.masterGridPositions[ptInd])
        v,u = self.vi.measure_distance(self.positions,
                                                            self.positions2,vec=True)
        self.vector = numpy.array(self.orientation) * self.uLength
        if u != self.uLength :
            self.positions2 = [[self.vector]]      
        if self.compNum == 0 :
            organelle = self.histoVol
        else :
            organelle = self.histoVol.organelles[abs(self.compNum)-1]
#        print self.name, organelle.name,len(organelle.molecules)
        secondPoint = self.getFirstPoint(ptInd)
        if secondPoint is None :
            self.completion = float(self.nbCurve)/self.nbMol
            return success, nbFreePoints
        rotMatj,jtrans=self.getJtransRot(startingPoint,secondPoint)
        self.results.append([jtrans,rotMatj])
        self.currentLength = 0.
        counter = self.counter
        self.Ptis=[ptInd,histoVol.grid.getPointFrom3D(secondPoint)]
        listePtCurve=[]
        listePtLinear=[startingPoint,secondPoint]
        Done = False
        k=0
        v=[0.,0.,0.]
        d=0.
        #loop 1 Forward
        success, nbFreePoints,freePoints = self.grow(previousPoint,startingPoint,secondPoint,
                                          listePtCurve,listePtLinear,histoVol, 
                                          ptInd, freePoints, nbFreePoints, distance, 
                                          dpad,stepByStep=False, verbose=False)
        nbFreePoints,freePoints = self.updateGrid(2,histoVol,dpad,freePoints, nbFreePoints, distance, 
                        gridPointsCoords, verbose)
        if self.seedOnMinus :
#            print "reverse"
            #secondPoint = self.getFirstPoint(ptInd,seed=1)
            success, nbFreePoints,freePoints = self.grow(previousPoint,listePtLinear[1],
                                          listePtLinear[0],
                                          listePtCurve,listePtLinear,histoVol, 
                                          ptInd, freePoints, nbFreePoints, distance, 
                                          dpad,stepByStep=False, verbose=False,r=True)
            nbFreePoints,freePoints = self.updateGrid(2,histoVol,dpad,freePoints, nbFreePoints, distance, 
                               gridPointsCoords, verbose)
        #store result in molecule
        if verbose:
            print("res",len(self.results))
        for i in range(len(self.results)):
            jtrans, rotMatj = self.results[-i]
            ptInd = histoVol.grid.getPointFrom3D(jtrans)
            organelle.molecules.append([ jtrans, rotMatj, self, ptInd ])
            #reset the result ?
        self.results=[]
        self.listePtCurve.append(listePtCurve)
        self.listePtLinear.append(listePtLinear)
        self.nbCurve+=1
        self.completion = float(self.nbCurve)/float(self.nbMol)
        if verbose:
            print("completion",self.completion,self.nbCurve,self.nbMol)
        return success, nbFreePoints            

class ActinIngrediant(GrowIngrediant):
    def __init__(self, molarity, radii=[[50.],], positions=None, positions2=None,
                 sphereFile=None, packingPriority=0, name=None,
                 pdb=None, color=None, nbJitter=5, jitterMax=(1,1,1),
                 perturbAxisAmplitude = 0.1,length = 10.,closed = False,
                 modelType="Cylinders",biased=1.0,Type="Actine",
                 principalVector=(1,0,0), meshFile=None, packingMode='random',
                 placeType="jitter",marge=35.0,influenceRad =100.0,meshObject=None,
                 orientation = (1,0,0),nbMol=0,**kw):
#        Ingredient.__init__(self, molarity, radii, positions, positions2,
#                            sphereFile,
#                            packingPriority, name, pdb, color, nbJitter,
#                            jitterMax, perturbAxisAmplitude, principalVector,
#                            meshFile, packingMode,placeType,meshObject)

        GrowIngrediant.__init__(self, molarity, radii, positions, positions2,
                            sphereFile,
                            packingPriority, name, pdb, color, nbJitter,
                            jitterMax, perturbAxisAmplitude, 
                            length,closed,
                            modelType,biased,
                            principalVector,
                            meshFile, packingMode,placeType,marge,meshObject,
                            orientation ,nbMol,Type,**kw)
        if name == None:
            name = "Actine_%s_%f"% (str(radii),molarity)
        self.isAttractor = True
        self.constraintMarge = True
        self.seedOnMinus = True
        self.influenceRad = influenceRad
        self.oneSuperTurn = 825.545#cm from c4d graham file
        self.oneDimerSize = 100.0#200 =2 
        self.cutoff_surface = 50.
        self.cutoff_boundary = 1.0
        #how to setup the display from the 3dmesh?should I update radius, position from it ?
        #also the mesh should preoriented correctly...
#        self.positions=[[[0,0,0]]], 
#        self.positions2=[[[0.,100.,0]]],
        

#    def build
        
    def updateFromBB(self,grid):
        return
        r = grid.getRadius()
        self.positions = [0.,0.,0.]
        self.positions2 = [r,0.,0.]
        self.principalVector = [1.,0.,0.]
        self.uLength = r
        self.length = 2*r

#import AutoFill
#from AutoFill.Recipe import Recipe
import os
#from DejaVu  import colors
class IngredientDictionary:
    """
    list all available ingrediant, and permit to add user ingrediant
    the listing is based on a scanning of the AutoFill package directory
    under recipe/membrane and recipe/cyto
    """
    def __init__(self):
        """Set up from the default directory"""
        #get the directory and scan all the name
        self.rdir = AutoFill.__path__[0]+'/recipes/'
        self.update()
        self.knownIngr = {}
        self.knownIngr['membrane'] = {
        '1h6i':{'name':'AUQAPORINE','priority':-10,'pVector':(0,0,1),'jitterMax':(0.3,0.3,0.3),'mol':.04,'type':'singleS','mode':'random'},
        '1zll':{'name':'PHOSPHOLAMBAN','priority':-5,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'singleS','mode':'random'},
        '2afl':{'name':'PROTON TRANSPORT','priority':-10,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'singleS','mode':'random'},
        '2uuh':{'name':'C4 SYNTHASE','priority':-5,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'multiS','mode':'random'},
        '1yg1':{'name':'FACILITATIVE GLUCOSE','priority':-5,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':.04,'type':'multiS','mode':'random'},
        '1ojc':{'name':'OXIDOREDUCTASE','priority':-10,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'multiS','mode':'random'},
        'ves34':{'name':'VES34','priority':-100,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'multiS','mode':'random'},
        '1qo1':{'name':'ATP SYNTHASE','priority':-150,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.01,'type':'multiS','mode':'random'},
        '2abm':{'name':'AQUAPORIN TETRAMER','priority':-2,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'multiS','mode':'random'},
        '3g61':{'name':'P-GLYCOPROTEIN','priority':-2,'pVector':(0,0,1),'jitterMax':(1,1,1),'mol':0.04,'type':'multiS','mode':'random'},
        '2bg9':{'name':'ION CHANNEL/RECEPTOR','priority':-2,'pVector':(0,0,-1),'jitterMax':(1,1,1),'mol':0.04,'type':'multiS','mode':'random'},
        '2a79':{'name':'POTASSIUM CHANNEL','priority':-1,'pVector':(0,0,1),'jitterMax':(0.3,0.3,0.3),'mol':0.04,'type':'multiS','mode':'random'}
        }
        self.knownIngr['cyto'] = {
        '1AON_centered':{'name':'GROEL','priority':1,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.0004,'type':'multiS','mode':'random'},
        '2CPK_centered':{'name':'PHOSPHOTRANSFERASE','priority':1,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.0004,'type':'multiS','mode':'close'},
        '1CZA_centered':{'name':'TRANSFERASE','priority':1,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.0002,'type':'multiS','mode':'random'},
        '2OT8_centered':{'name':'TRANSPORT PROTEIN','priority':1,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.0002,'type':'multiS','mode':'random'},
        '1TWT_centered':{'name':'30S RIBOSOME','priority':2,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.0001,'type':'multiS','mode':'random'},
        '1ABL_centered':{'name':'KINASE','priority':0,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.01,'type':'singleS','rad':16.,'mode':'random'}
        }
        self.knownIngr['matrix'] = {
        #'1ABL_centered':{'name':'GLUTAMATE','priority':.0001,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.150,'type':'singleS','rad':3.61,'mode':'random'}
        'Glutamate_centered':{'name':'GLUTAMATE','priority':.0001,'pVector':(1,0,0),'jitterMax':(1,1,1),'mol':.150,'type':'singleS','rad':3.61,'mode':'random'}
        }
        self.MSca = 1.0
    
    def filterList(self,dir):
        #if no .sph file -> single Sphere ingr
        #else ->multiSphIngr
        listDir=os.listdir(dir)
        listeIngr={}
        for item in listDir:
            if item == 'CVS' :
                continue
            sp = item.split('.')
            if sp[0] not in listeIngr :
                if sp[0]+'.sph' in listDir :
                    nbSph = self.getNumberOfSphere(dir+'/'+sp[0]+'.sph')
                    if nbSph > 1 :
                        listeIngr[sp[0]]=['Multi',True]
                    else : 
                        listeIngr[sp[0]]=['Single',True]
                else :
                    listeIngr[sp[0]]=['Single',False]
        return listeIngr
    
    def changeDir(self,newDir):
        self.rdir = newDir
        
    def update(self,newDir=None):
        if newDir is not None :
            self.changeDir(newDir)
        self.listename={}
        self.listename["membrane"] = self.filterList(self.rdir+'membrane')
        self.listename["cyto"] = self.filterList(self.rdir+'cyto')

    def getNumberOfSphere(self,sphFile):
        f = open(sphFile,'r')
        lines = f.readlines()
        f.close()
        for i in range(len(lines)):
            if lines[i] == '# number of spheres in level 1\n':
                nbSphere = eval(lines[i+1])
                return nbSphere

    def makeBiLayerIngrediant(self,molarity,positions=[-.5,0,0], 
                            positions2=[15,0,0],radii=[3],priority = .001,
                            jitterMax=(0.3,0.3,0.3)):
        ############## cylinder Bilayer here##########
        #  jitterMax CRITICAL !!! IF jitter is greater than radius of object, e.g. 5x(1,1,1) the point may not be consumed!!!
        cyl1IngrU = MultiCylindersIngr(molarity,  pdb='LipOutPdb',
                                        name='LipOut', radii=[radii],
                                        positions=[[positions]], positions2=[[positions2]],
                                        packingPriority=priority,
                                        jitterMax=jitterMax, 
                                        principalVector=(1,0,0)#vcolor=colors.bisque,
                                      )        
        cyl1IngrD = MultiCylindersIngr(molarity,  pdb='LipInPdb',
                                        name='LipIn', radii=[radii],
                                        positions=[[positions]], positions2=[[positions2]],
                                        packingPriority=priority,
                                        jitterMax=jitterMax,
                                        principalVector=(-1,0,0)
                                      )#color=colors.burlywood,
        return cyl1IngrU,cyl1IngrD

    def makeKnownIngrediant(self,MSca,listeCol):
        rSurf1 = Recipe()
        rCyto = Recipe()
        rMatrix = Recipe()
        rRec = {'membrane':rSurf1,
                'cyto':rCyto,
                'matrix':rMatrix}
        wrkDir = self.rdir
        i=0
        for k in list(self.knownIngr.keys()):
            for ing_name in list(self.knownIngr[k].keys()):
                ingDic = self.knownIngr[k][ing_name]
                if ingDic['type'] == 'singleS':
                    if 'rad' in ingDic:
                         ingr = SingleSphereIngr( MSca*ingDic['mol'], color=listeCol[i], pdb=ing_name,
                                         name=ingDic['name'],
                                         radius=ingDic['rad'],
                                         meshFile=wrkDir+'/'+k+'/'+ing_name,
                                         packingPriority=ingDic['priority'],
                                         jitterMax=ingDic['jitterMax'],
                                         principalVector=ingDic['pVector'],
                                         packingMode=ingDic['mode'])                       
                    else :
                        ingr = SingleSphereIngr( MSca*ingDic['mol'], color=listeCol[i], pdb=ing_name,
                                         name=ingDic['name'],
                                         sphereFile=wrkDir+'/'+k+'/'+ing_name+'.sph',
                                         meshFile=wrkDir+'/'+k+'/'+ing_name,
                                         packingPriority=ingDic['priority'],
                                         jitterMax=ingDic['jitterMax'],
                                         principalVector=ingDic['pVector'],
                                         packingMode=ingDic['mode'])
                elif ingDic['type'] == 'multiS':
                    ingr = MultiSphereIngr( MSca*ingDic['mol'], color=listeCol[i], pdb=ing_name,
                                         name=ingDic['name'],
                                         sphereFile=wrkDir+'/'+k+'/'+ing_name+'.sph',
                                         meshFile=wrkDir+'/'+k+'/'+ing_name,
                                         packingPriority=ingDic['priority'],
                                         jitterMax=ingDic['jitterMax'],
                                         principalVector=ingDic['pVector'],
                                         packingMode=ingDic['mode'])
                rRec[k].addIngredient(ingr)
                i = i +1
        return rRec


    def getIngrediants(self,name,color):
        wrkDir = self.rdir
        ingr=None
        for k in list(self.knownIngr.keys()):
            for ing_name in list(self.knownIngr[k].keys()):
                ingDic = self.knownIngr[k][ing_name]
                if name == ing_name or name == ingDic['name']:
                    if ingDic['type'] == 'singleS':
                        if 'rad' in ingDic:
                             ingr = SingleSphereIngr( self.MSca*ingDic['mol'], color=color, pdb=ing_name,
                                             name=ingDic['name'],
                                             radius=ingDic['rad'],
                                             meshFile=wrkDir+'/'+k+'/'+ing_name,
                                             packingPriority=ingDic['priority'],
                                             jitterMax=ingDic['jitterMax'],
                                             principalVector=ingDic['pVector'],
                                             packingMode=ingDic['mode'])                       
                        else :
                            ingr = SingleSphereIngr( self.MSca*ingDic['mol'], color=color, pdb=ing_name,
                                             name=ingDic['name'],
                                             sphereFile=wrkDir+'/'+k+'/'+ing_name+'.sph',
                                             meshFile=wrkDir+'/'+k+'/'+ing_name,
                                             packingPriority=ingDic['priority'],
                                             jitterMax=ingDic['jitterMax'],
                                             principalVector=ingDic['pVector'],
                                             packingMode=ingDic['mode'])
                    elif ingDic['type'] == 'multiS':
                        ingr = MultiSphereIngr( self.MSca*ingDic['mol'], color=color, pdb=ing_name,
                                             name=ingDic['name'],
                                             sphereFile=wrkDir+'/'+k+'/'+ing_name+'.sph',
                                             meshFile=wrkDir+'/'+k+'/'+ing_name,
                                             packingPriority=ingDic['priority'],
                                             jitterMax=ingDic['jitterMax'],
                                             principalVector=ingDic['pVector'],
                                             packingMode=ingDic['mode'])
                    break
        return ingr

    def makeIngrediants(self,MSca,listeCol,wanted):
        rSurf1 = Recipe()
        rCyto = Recipe()
        rRec = {'membrane':rSurf1,
                'cyto':rCyto}
        wrkDir = self.rdir
        #excluded = ['ves34']
        i=0
        for k in list(self.listename.keys()):
            for ing_name in list(self.listename[k].keys()):
                #print ing_name
                if ing_name in wanted:
                    if self.listename[k][ing_name][0] == 'Single':
                        sphereFile = None
                        if self.listename[k][ing_name][1] :
                            sphereFile = wrkDir+'/'+k+'/'+ing_name+'.sph'
                        ingr = SingleSphereIngr( MSca*.04, color=listeCol[i], pdb=ing_name,
                                         name=ing_name,
                                         sphereFile=sphereFile,
                                         meshFile=wrkDir+'/'+k+'/'+ing_name,
                                         packingPriority=-2,
                                         jitterMax=(0.3,0.3,0.3),
                                         principalVector=(0,0,1))
                    else :
                        ingr = MultiSphereIngr( MSca*.04, color=listeCol[i], name=ing_name,
                                        sphereFile=wrkDir+'/'+k+'/'+ing_name+'.sph',
                                        meshFile=wrkDir+'/'+k+'/'+ing_name, pdb=ing_name,
                                        packingPriority=-1,
                                        #jitterMax=(1,1,.2),
                                        principalVector=(0,0,-1))
                    rRec[k].addIngredient(ingr)
                    i = i +1
        return rRec

from AutoFill import IOutils as io 
from xml.dom.minidom import getDOMImplementation 
import json   
class IOingredientTool:
    #xml parser that can return an ingredient
    def __init__(self):
        pass

    def read(self,filename):
        pass

    def write(self,ingr,filename,ingr_format="xml"):
        if ingr_format == "json" :
            ingdic = self.ingrJsonNode(ingr)
            with open(filename+".json", 'w') as fp :#doesnt work with symbol link ?
                json.dump(ingdic,fp,indent=4, separators=(',', ': '))#,indent=4, separators=(',', ': ')            
        elif ingr_format == "xml" :
            ingrnode,xmldoc = self.ingrXmlNode(ingr)
            f = open(filename+".xml","w")        
            xmldoc.writexml(f, indent="\t", addindent="", newl="\n")
            f.close()
        elif ingr_format == "python" :
            ingrnode = self.ingrPythonNode(ingr)
        elif ingr_format == "all" :
            ingdic = self.ingrJsonNode(ingr)
            with open(filename+".json", 'w') as fp :#doesnt work with symbol link ?
                json.dump(ingdic,fp,indent=4, separators=(',', ': '))#,indent=4, separators=(',', ': ')            
            ingrnode,xmldoc = self.ingrXmlNode(ingr)
            f = open(filename+".xml","w")        
            xmldoc.writexml(f, indent="\t", addindent="", newl="\n")
            f.close()
            ingrnode = self.ingrPythonNode(ingr)
            f = open(filename+".py","w")        
            f.write(ingrnode)
            f.close()

    def makeIngredientFromXml(self,inode=None,filename=None, recipe="Generic"):
        if filename is None and inode is not None :
            f=str(inode.getAttribute("include"))
            if f != '':
                filename = str(f)
        if filename is not None :
            if filename.find("http") != -1 or filename.find("ftp")!= -1 :
                name = filename.split("/")[-1]
                tmpFileName = AFDIR+os.sep+"autoFillRecipeScripts"+os.sep+recipe+os.sep+"ingredients"+os.sep+name
                #check if exist first
                if not os.path.isfile(tmpFileName) or AutoFill.forceFetch :
                    try :
                        import urllib.request as urllib
                    except :
                        import urllib
                    if checkURL(filename):
                        urllib.urlretrieve(filename, tmpFileName,reporthook=reporthook)
                    else :
                        if not os.path.isfile(tmpFileName)  :
                            return  None
                filename = tmpFileName
            #url ? then where cache ?
            from xml.dom.minidom import parse
            xmlingr = parse(filename) # parse an XML file by name
            ingrnode = xmlingr.documentElement
        elif inode is not None:
            ingrnode = inode
        else :
            return None
        kw=self.parseIngrXmlNode(ingrnode)
        ingre = self.makeIngredient(**kw)                    
        return ingre

    def parseIngrXmlNode(self,ingrnode):
        name = str(ingrnode.getAttribute("name"))
        kw = {}
        for k in KWDS:
            v=io.getValueToXMLNode(KWDS[k]["type"],ingrnode,k)
            if v is not None :
                kw[k]=v                   
        #create the ingredient according the type
#        ingre = self1.makeIngredient(**kw)                    
        return kw 
                
    def ingrXmlNode(self,ingr,xmldoc=None):
        rxmldoc=False
        if xmldoc is None : 
            rxmldoc = True
            impl = getDOMImplementation()
            #what about afviewer
            xmldoc = impl.createDocument(None, "ingredient", None)
            ingrnode = xmldoc.documentElement
            ingrnode.setAttribute("name",str(ingr.name))
        else :
            ingrnode = xmldoc.createElement("ingredient")
            ingrnode.setAttribute("name",str(ingr.name))
        for k in ingr.KWDS:
            v = getattr(ingr,k)
            io.setValueToXMLNode(v,ingrnode,k)
        if rxmldoc :
            return ingrnode,xmldoc
        else :
            return ingrnode

    def ingrJsonNode(self,ingr):
        ingdic={}
        for k in ingr.KWDS:
            v = getattr(ingr,k)
            if hasattr(v,"tolist"):
                v=v.tolist()
            ingdic[k] = v
        ingdic["results"]=[] 
        for r in ingr.results:  
            if hasattr(r[0],"tolist"):
                r[0]=r[0].tolist()
            if hasattr(r[1],"tolist"):
                r[1]=r[1].tolist()
            ingdic["results"].append([r[0],r[1]])
        if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
            ingdic["nbCurve"]=ingr.nbCurve
            for i in range(ingr.nbCurve):
                lp = numpy.array(ingr.listePtLinear[i])
                ingr.listePtLinear[i]=lp.tolist()                 
                ingdic["curve"+str(i)] = ingr.listePtLinear[i]
        return ingdic

    def ingrPythonNode(self,ingr):
        inrStr="#include as follow : execfile('pathto/"+ingr.name+".py',globals(),{'recipe':recipe_variable_name})\n"
        if ingr.Type == "MultiSphere":
            inrStr+="from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr\n"
            inrStr+=ingr.name+"= MultiSphereIngr( \n"  
        if ingr.Type == "MultiCylinder":
            inrStr+="from AutoFill.Ingredient import MultiCylindersIngr\n"
            inrStr+=ingr.name+"= MultiCylindersIngr( \n"                
        for k in ingr.KWDS:
            v = getattr(ingr,k)
            aStr = io.setValueToPythonStr(v,k)
            if aStr is not None :
                inrStr+=aStr+",\n" 
        inrStr+=")\n"
        inrStr+="recipe.addIngredient("+ingr.name+")\n"        
        return inrStr

    def makeIngredient(self,**kw):
#        from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr,SingleCubeIngr
#        from AutoFill.Ingredient import MultiCylindersIngr, GrowIngrediant
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
    