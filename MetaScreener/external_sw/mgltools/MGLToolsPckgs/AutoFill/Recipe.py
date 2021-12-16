# -*- coding: utf-8 -*-
"""
############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin,
# and Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010 
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input 
#   from Arthur Olson's Molecular Graphics Lab
#
# Recipe.py Authors: Graham Johnson & Michel Sanner with editing/
# enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner
# with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
#
# This file "Recipe.py" is part of autoPACK, cellPACK, and AutoFill.
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

# Hybrid version merged from Graham's Sept 6, 2011 and Ludo's April 2012 
#version on May 16, 2012, remerged on July 5, 2012 with thesis versions
"""

from .Ingredient import Ingredient
import weakref
from random import random, seed 
#randint,gauss,uniform added by Graham 8/18/11
#seedNum = 14
#seed(seedNum)               #Mod by Graham 8/18/11

class Recipe:
    """
    a recipe provides ingredients that are each defining a protein identity
    along with radius and molarity for this protein.
    """
    def __init__(self):
        
        self.ingredients = []
        self.activeIngredients = []
        self.organelle = None 
        # will be set when recipe is added to organelle
        self.exclude = []
        self.number=0
        
    def delIngredient(self, ingr):
        """ remove the given ingredient from the recipe """ 
#        print ingr,ingr.name
        if ingr in self.ingredients : 
            ind = self.ingredients.index(ingr)
            self.ingredients.pop(ind)
        if ingr not in self.exclude :
            self.exclude.append(ingr)
    
    def addIngredient(self, ingr):
        """ add the given ingredient from the recipe """ 
#        assert isinstance(ingr, Ingredient)
#        print ingr,ingr.name
        if ingr not in self.ingredients :
            self.ingredients.append(ingr)
        ingr.recipe = weakref.ref(self)
        if ingr in self.exclude:
            ind = self.exclude.index(ingr)
            self.exclude.pop(ind)

    def setCount(self, volume, reset=True, **kw):#area=False,
        """ set the count of n of molecule for every ingredients 
        in the recipe, and push them in te activeIngredient list 
        """ 
        seedNum = 14
        seed(seedNum)               
        #Mod by Graham 8/18/11, revised 9/6... 
        #this now allows consistent refilling via seed)
        # compute number of molecules for a given volume
        for i, ingr in enumerate(self.ingredients):
            #6.02 / 10000)# 1x10^27 / 1x10^23 = 10000
            if reset :
                self.resetIngr(ingr)
#            nb = int(ingr.molarity * volume * .000602)   
            # Overridden by next 18 lines marked Mod 
            #by Graham 8/18/11 into Hybrid on 5/16/12
            #Mod by Graham 8/18/11: Needed this to give 
            #ingredients an increasing chance to add one more molecule
                # based on modulus proximity to the next integer
            nbr = ingr.molarity * volume * .000602 #Mod by Graham 8/18/11
            nbi = int(nbr)              #Mod by Graham 8/18/11
#            print 'ingr.molarity = ', ingr.molarity
#            print 'volume = ', volume
#            print 'nbr = ', nbr
#            print 'nbi = ', nbi         #Mod by Graham 8/18/11
            if nbi == 0 :
                nbmod = nbr
            else :
                nbmod = nbr % nbi             #Mod by Graham 8/18/11
            randval = random()               #Mod by Graham 8/18/11
#            print 'randval = ', randval
            if nbmod >= randval :               #Mod by Graham 8/18/11
                nbi = int(nbi+1)             #Mod by Graham 8/18/11
#            print 'nbi = ', nbi         #Mod by Graham 8/18/11
            nb = nbi                    #Mod by Graham 8/18/11
#            print'nb = ', nb            #Mod by Graham 8/18/11
            if ingr.overwrite_nbMol  :#DEPREATED
                ingr.vol_nbmol = nb
                ingr.nbMol = ingr.overwrite_nbMol_value
            else :
                ingr.vol_nbmol = ingr.nbMol = nb + ingr.overwrite_nbMol_value
            print(('RECIPE IS ON' + ingr.name + 'volume' + "%d" 'nb' "%d") % (volume, nb))
            #print '*************************************volume = '%(volume)
            if ingr.nbMol == 0:
                print('WARNING GRAHAM: recipe ingredient %s has 0 molecules as target'%(
                    ingr.name))
            else:
                self.activeIngredients.append(i)

    def resetIngr(self, ingr):
        """ reset the states of the given ingredient """ 
        ingr.counter = 0
        ingr.nbMol = 0
        ingr.completion = 0.0
        
    def resetIngrs(self,):
        """ reset the states of all recipe ingredients """
        for ingr in self.ingredients:
            ingr.counter = 0
            ingr.nbMol = 0
            ingr.completion = 0.0

    def getMinMaxProteinSize(self):
        """ get the mini and maxi radius from all recipe ingredients """
        mini = 9999999.
        maxi = 0
        for ingr in self.ingredients:
            if ingr.encapsulatingRadius > maxi:
                maxi = ingr.encapsulatingRadius
            if ingr.minRadius < mini:
                mini = ingr.minRadius 
        return mini, maxi


    def sort(self):
        """ sort the ingredients using the min Radius """
        # sort tuples in molecule list according to radius
        self.ingredients.sort(key=lambda x : x.minRadius ) 
        #cmp(y.minRadius, x. minRadius))#(a > b) - (a < b)
#        self.ingredients.sort(lambda x,y: cmp(y.minRadius, x. minRadius))
# Do we need to sort y.minRadius too for ellipses/Cyl? 
# This line is from August 2011 version of code


    def printFillInfo(self, indent = ''):
        """ print the states of all recipe ingredients """
        for ingr in self.ingredients:
            print(indent+'ingr: %s target: %3d placed %3d %s'%(
                ingr.pdb, ingr.nbMol, ingr.counter, ingr.name))
