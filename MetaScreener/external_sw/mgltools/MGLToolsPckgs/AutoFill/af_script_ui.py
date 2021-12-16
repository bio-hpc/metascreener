# -*- coding: utf-8 -*-
"""
Created on Sun Mar  4 10:11:34 2012
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Ludovic Autin, Mostafa Al-Alusi, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# AFGui.py Authors: Ludovic Autin with minor editing/enhancement from Graham Johnson
#
# Copyright: Graham Johnson ©2010
#
# This file "af_script_ui.py" is part of autoPACK, cellPACK, and AutoFill.
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
###############################################################################
Name: -
@author: Ludovic Autin with minor editing/enhancement by Graham Johnson
"""
PLUGIN_ID = 102380125
import sys
import os
import random
from functools import partial
from time import time

#sys.path.append("/Users/ludo/DEV/af_svn/trunk/")

#shoud display general option for AutoFill and simplify testing.
from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr
from AutoFill.Ingredient import MultiCylindersIngr,GrowIngrediant,ActinIngrediant
from AutoFill.Ingredient import IngredientDictionary
from AutoFill.Organelle import Organelle
from AutoFill.Recipe import Recipe
from AutoFill.HistoVol import Environment
from AutoFill.autofill_viewer import AFViewer

import AutoFill
wrkDir = AutoFill.__path__[0]

import upy
upy.setUIClass()
from upy import uiadaptor
helperClass = upy.getHelperClass()

class AFScriptUI(uiadaptor):
    def setup(self,**kw):
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            self.helper = helperClass(kw)
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        else :
            self.afviewer = AFViewer(ViewerType=self.host,helper=self.helper)
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        else :
            self.histoVol = None
        if self.histoVol is None :
            # create HistoVol
            self.histo = self.histoVol = Environment()        
        self.orga = []
#        self.initColor()
        #self.rRec=self.dicIngr.makeKnownIngrediant(self.MSca,self.listeCol)
        
        self.rSurf = []#self.rRec['membrane']
        self.rCyto = Recipe()#self.rRec['cyto']
        self.rMatrix = []#self.rRec['matrix']
        self.bbox = None
        self.scriptname=""
        self.recipes = None#[self.rSurf,self.rCyto,self.rMatrix]

        self.indiceOrga = 0
        self.indiceIngr = 1000
            
        self.title = "AutoFill"

        self.initWidget()
        self.setupLayout()
        
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1
    
    def initColor(self):
        self.listeCol=[red, aliceblue, antiquewhite, aqua, 
     aquamarine, azure, beige, bisque, blanchedalmond, 
     blue, blueviolet, brown, burlywood, cadetblue, 
     chartreuse, chocolate, coral, cornflowerblue, cornsilk, 
     crimson, cyan, darkblue, darkcyan, darkgoldenrod, 
     orange, purple, deeppink, lightcoral, 
     blue, cyan, mediumslateblue, steelblue, darkcyan, 
     limegreen, darkorchid, tomato, khaki, gold, magenta, green]        
    
    def initWidget(self,id=None):
        self.BTN={}        
        #options widget checkbox and input
        dic={"int":"inputInt","float":"inputFloat","bool":"checkbox","liste":"pullMenu","filename":"inputStr"}
        #need a histoVol
        if self.histoVol is None or self.afviewer is None:
            #just a Label
            return
        self.widgets={"options":{"histoVol":{},"afviewer":{}},"recipe":{}}
        for option in self.histoVol.OPTIONS:
            o = self.histoVol.OPTIONS[option]
            if o["type"] == "liste": v = o["values"]
            else : v = o["value"]
            self.widgets["options"]["histoVol"][option] = self._addElemt(name=o["name"],value=v,
                                    width=200,height=10,action=None,
                                    #variable=self.addVariable("int",1),
                                    type=dic[o["type"]])
        for option in self.afviewer.OPTIONS:
            o = self.afviewer.OPTIONS[option]
            if o["type"] == "liste": v = o["values"]
            else : v = o["value"]
            self.widgets["options"]["afviewer"][option] = self._addElemt(name=o["name"],value=v,
                                    width=200,height=10,action=None,
                                    #variable=self.addVariable("int",1),
                                    type=dic[o["type"]])
 
         
    def setupLayout(self):
        self._layout = []
        
        elemFrame=[]
        for wname in self.widgets["options"]["histoVol"]:
            w = self.widgets["options"]["histoVol"][wname]
            elemFrame.append([w,])        
        frame = self._addLayout(id=196,name="histoVol",elems=elemFrame,collapse=True)#,type="tab")
        self._layout.append(frame)

        elemFrame=[]
        for wname in self.widgets["options"]["afviewer"]:
            w = self.widgets["options"]["afviewer"][wname]
            elemFrame.append([w,]) 
        frame = self._addLayout(id=196,name="afviewer",elems=elemFrame,collapse=True)#,type="tab")
        self._layout.append(frame)

        elemFrame=[]
        elemFrame.append([self.SCRIPT,self.BTN['loadscript']])
        for wname in self.LABELS:
            w = self.LABELS[wname]
            elemFrame.append([w,])        
        frame = self._addLayout(id=193,name="RECIPE",elems=elemFrame,collapse=True)#,type="tab")
        self._layout.append(frame)
        
        self._layout.append([self.BTN['histo'],self.BTN['reset']])
        self._layout.append([self.seedId,self.BTN['fill']])

    def updateWidget(self):
        for wname in self.widgets["options"]["histoVol"]:
            w = self.widgets["options"]["histoVol"][wname]
            v = getattr(self.histoVol,wname)
            print (wname,v)
            self.setVal(w,v)
        for wname in self.widgets["options"]["afviewer"]:
            w = self.widgets["options"]["afviewer"][wname]
            v = getattr(self.afviewer,wname)
            print (wname,v)
            self.setVal(w,v)
#            TODO : update upy to handle dynamics label in dejavu tkinter
#        if self.histoVol.exteriorRecipe is not None:
#            label = self.getString(self.LABELS["rCyto"])
#            self.setString(self.LABELS["rCyto"],"rCyto")
#            for ingr in self.histoVol.exteriorRecipe.ingredients:
#                labelin = self.getString(self.LABELS["ingredients"])
#                self.setString(self.LABELS["ingredients"],labelin+"\n"+ingr.name)          
#            
#        for orga in self.histoVol.organelles:
#            label = self.getString(self.LABELS["organelles"])
#            self.setString(self.LABELS["organelles"],label+" "+orga.name)
#            r =  orga.surfaceRecipe
#            if r :
#                labelrs = self.getString(self.LABELS["recipes"])
#                self.setString(self.LABELS["recipes"],labelrs+" surface"+orga.name)
#                for ingr in r.ingredients:
#                    labelin = self.getString(self.LABELS["ingredients"])
#                    self.setString(self.LABELS["ingredients"],labelin+" "+ingr.name)          
#            r =  orga.innerRecipe
#            if r :
#                labelrs = self.getString(self.LABELS["recipes"])
#                self.setString(self.LABELS["recipes"],labelrs+" inner"+orga.name)                
#                for ingr in r.ingredients:
#                    labelin = self.getString(self.LABELS["ingredients"])
#                    self.setString(self.LABELS["ingredients"],labelin+" "+ingr.name)  
        self.setVal(self.SCRIPT,self.scriptname)

    def applyWidgetValue(self):
        for wname in self.widgets["options"]["histoVol"]:
            w = self.widgets["options"]["histoVol"][wname]
            v = self.getVal(w)
            setattr(self.histoVol,wname,v)
            print (wname,v)
            self.setVal(w,v)
        for wname in self.widgets["options"]["afviewer"]:
            w = self.widgets["options"]["afviewer"][wname]
            v = self.getVal(w)
            setattr(self.histoVol,wname,v)
            print (wname,v)
            self.setVal(w,v)

    def Set(self,**kw):
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            self.helper = helperClass(kw)
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        else :
            self.afviewer = AFViewer(ViewerType=self.host,helper=self.helper)
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        else :
            self.histoVol = None
        if "bbox" in kw : self.bbox = kw["bbox"]
        
    def reset(self,*args):
        self.histoVol = None
        self.rCyto = None
        self.rMatrix = None
        self.rSurf = None
        self.recipes = None
#        self.resetPMenu(self.ORGA_BOX)   
        #del self.viewer
        self.orga = None
        #should reexec the file, except the gui ?
        execfile(self.scriptname,{"mygui":self})        
        #self.setup()

    def loadPyScript(self,fname):
        self.scriptname = fname
        self.reset()

    def loadScript(self,*args):
        #browse to script
        try :
            self.fileDialog(label="choose a af-python script",callback=self.loadPyScript)
        except :
            self.drawError()
        
    def setupHistoVol(self,*args):
        #need that all ingredient/recipes are set for each organelle
        #thus we can compute the histo volume bounding box and prepare the display
        self.histoVol.setMinMaxProteinSize()
        #for i in range(len(self.orga)):
        #    print 'Surf', self.rSurf.getMinMaxProteinSize()
        #    print 'Matrix', self.rMatrix.getMinMaxProteinSize()
        #    #print 'o1', o1.getMinMaxProteinSize()
        print 'Cyto', self.rCyto.getMinMaxProteinSize()
        self.histoVol.smallestProteinSize = self.getVal(self.widgets["options"]["histoVol"]["smallestProteinSize"])
        #print 'smallest', self.histo.smallestProteinSize
        #print 'largest', self.histo.largestProteinSize
        self.pad = 100.
        self.afviewer.SetHistoVol(self.histoVol,self.pad,display=False)
        self.afviewer.displayPreFill()        
        
    def fillGrid(self,*args):
        self.applyWidgetValue()
        print "grid"
        seed = self.getVal(self.seedId)
        if self.bbox is None :
            box=self.helper.getCurrentSelection()[0]
        else :
            box = self.bbox
        print box
        bb=self.afviewer.vi.getCornerPointCube(box)
        self.histoVol.buildGrid(boundingBox=bb)
#        self.afviewer.displayOrganellesPoints() # this is optional and should not be called here
        print "fill"
        t1 = time()
        self.histoVol.fill5(seedNum=int(seed))
        t2 = time()
        print 'time to fill', t2-t1
        self.afviewer.displayFill()
        self.afviewer.vi.toggleDisplay(self.afviewer.bsph,False)
        print 'time to display', time()-t2
        return True