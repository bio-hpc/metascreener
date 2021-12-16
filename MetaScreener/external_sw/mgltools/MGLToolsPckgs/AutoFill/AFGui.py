# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 23:53:00 2012

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
# This file "AFGui.py" is part of autoPACK, cellPACK, and AutoFill.
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
    
Name: 'autoPACK/cellPACK GUI'
@author: Ludovic Autin with design/editing/enhancement by Graham Johnson
"""

#this should be part of the adaptor?
__author__ = "Ludovic Autin, Graham Johnson"
__url__ = [""]
__version__="0.0.0.1"
__doc__ = "AP v"+__version__
__doc__+"""\
autoPACK by Graham Johnson, Ludovic Autin, Michel Sanner.
Developed in the Molecular Graphics Laboratory directed by Arthur Olson.
Developed @UCSF by Graham Johnson
"""
# -------------------------------------------------------------------------- 
# ***** BEGIN GPL LICENSE BLOCK ***** 
# 
# This program is free software; you can redistribute it and/or 
# modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation; either version 2 
# of the License, or (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program; if not, write to the Free Software Foundation, 
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA. 
# 
# ***** END GPL LICENCE BLOCK ***** 
# -------------------------------------------------------------------------- 
#=======
#should be universal
import os,sys
from time import time
try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib

import upy
uiadaptor = upy.getUIClass()


import AutoFill
AFwrkDir1 = AutoFill.__path__[0]

try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib
import tarfile
import shutil
COPY="cp"
geturl=None
global OS
OS = os

from AutoFill.ingr_ui import SphereTreeUI
from AutoFill.Recipe import Recipe
from AutoFill.Ingredient import GrowIngrediant,ActinIngrediant
from AutoFill.autofill_viewer import AFViewer
from AutoFill import checkURL
from upy.register_user import Register_User_ui

#need a global Dictionary
#recipename : {"setupfile":"","resultfile":,}

#import here othergui
#import HIV gui ? specfic or generic AF gui for setup ?
#from AutoFill.af_script_ui_AFLightSpecific import AFScriptUI require helper load ?
class SubdialogGradient(uiadaptor):
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1

    def setup(self,**kw):
        self.subdialog = True
#        self.block = True
#        self.scrolling = False
        self.mode = kw["mode"]
        #two mode : Add - Edit
        self.gname = "newGradient"
        if "name" in kw :
            self.gname= kw["name"]
        self.histoVol = None
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        self.parent =None
        if "parent" in kw :
            self.parent = kw["parent"]
        self.title = "Gradient "+self.gname
        witdh=550
        self.h=130
        self.w=300
        self.widget_width  = 50
        self.Widget={}
        self.Widget["options"]={}
        self.Widget["labeloptions"] = {}

        self.SetTitle(self.title)
        
        self.parent = None
        if "parent" in kw :
            self.parent = kw["parent"]
#        print "mode",self.mode
        if self.mode == "Edit":
            self.gradient =  self.histoVol.gradients[self.gname]
#            print (self.gname,self.gradient)
            self.initWidgetEdit()
            self.setupLayoutEdit()
        elif self.mode == "Add":
            from AutoFill.HistoVol import Gradient
            self.histoVol.gradients[self.gname] = self.gradient = Gradient(self.gname)
            if self.parent is not None: 
                self.parent.addItemToPMenu(self.parent.Widget["options"]["gradients"],str(self.gname))
            self.initWidgetAdd()
            self.setupLayoutAdd()
            
    def gradientWidget(self):
        dic={"int":"inputInt","float":"inputFloat","bool":"checkbox","liste":"pullMenu","filename":"inputStr"}
        for option in self.gradient.liste_options  :
            o = self.gradient.OPTIONS[option]
            if o["type"] == "vector" :
                #need three widget
                self.Widget["labeloptions"][option] = self._addElemt(name=o["name"]+"Label",label=o["description"],width=120)
                self.Widget["options"][option]=[]
                for i,x in enumerate(["x","y","z"]):
                    w=self._addElemt(name=o["name"]+x,value=o["value"][i],
                                    width=self.widget_width,height=10,action=None,
                                    mini=o["min"],maxi=o["max"],
                                    #variable=self.addVariable("int",1),
                                    type="inputFloat")
                    self.Widget["options"][option].append(w)
            else :
                if o["type"] == "liste": 
                    v = o["values"]
                else : v = o["value"]
                
                self.Widget["labeloptions"][option] = self._addElemt(name=o["name"]+"Label",label=o["description"],width=120)
                self.Widget["options"][option] = self._addElemt(name=o["name"],value=v,
                                        width=self.widget_width,height=10,action=None,
                                        mini=o["min"],maxi=o["max"],
                                        #variable=self.addVariable("int",1),
                                        type=dic[o["type"]])
        self.BTN={}
        self.BTN["close"]=self._addElemt(name="Close",width=50,height=10,
                         action=self.close,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["apply"]=self._addElemt(name="Apply",width=50,height=10,
                         action=self.ApplyWidgetValue,type="button",icon=None,
                                     variable=self.addVariable("int",0))
 
    def updateWidgetValue(self):
#        for wname in self.Widget["options"]:
        for option in self.gradient.liste_options:
            o = self.gradient.OPTIONS[option]
            if o["type"] == "vector" :
#                print ("update "+option)
                v = getattr(self.gradient,option)
#                print ("valuexyz ",v)
                if v is None :
                    v = [0.,0.,0.]
                for i,x in enumerate(["x","y","z"]):    
                   self.setVal(self.Widget["options"][option][i],v[i]) 
            else :
                w = self.Widget["options"][option]
                v = getattr(self.gradient,option)
#                print("set w v",w,v)
                self.setVal(w,v)

    def ApplyWidgetValue(self, *args, **kw):
        for option in self.gradient.liste_options:
            o = self.gradient.OPTIONS[option]
            if o["type"] == "vector" :
                v=[self.getVal(w) for w in self.Widget["options"][option]]
                setattr(self.gradient,option,v)       
            else :
                w = self.Widget["options"][option]
                v = self.getVal(w)
                setattr(self.gradient,option,v)
#                self.setVal(w,v)

    def setupLayout(self):
        self._layout = []
        for wname in self.gradient.liste_options:        
            widget =[self.Widget["labeloptions"][wname],self.Widget["options"][wname]]
            if type(self.Widget["options"][wname]) == list: 
                widget =[self.Widget["labeloptions"][wname]]
                widget.extend(self.Widget["options"][wname])
            self._layout.append(widget)
        self._layout.append([self.BTN["apply"],self.BTN["close"]])        
 
    def initWidgetEdit(self,):
        self.gradientWidget()
        
    def setupLayoutEdit(self,):
#        self._layout=[]
#        self._layout.append(self.label)
#        print self._layout
        self.setupLayout()
        
    def initWidgetAdd(self,):
        self.gradientWidget()
        
    def setupLayoutAdd(self,):
        self.setupLayout()
    
    #why did the dialog close


class SubdialogIngrdient(uiadaptor):
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1

    def setup(self,**kw):
        self.subdialog = True
#        self.block = True
        self.scrolling = False
        self.ingr = kw["ingr"]
        if self.ingr is None :
            return
        self.histoVol = None
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        self.title = self.ingr.name+" options"#+self.mol.name
        witdh=550
        self.h=130
        self.w=450
        self.SetTitle(self.title)
        self.initWidget()
        self.setupLayout()
#        self.updateWidget()

    def initWidget(self, ):
        self.Widget={}
        self.Widget["options"]={}
        self.Widget["labeloptions"]={}
        self.Widget["edit"]={}
        #what are the option we want from the ingredient
        self.listAttrOrdered = ["rejectionThreshold","nbJitter", "perturbAxisAmplitude", "principalVector","jitterMax",#"principalVector",
         "useRotAxis","rotAxis","rotRange",                      
         "packingMode","gradient","placeType",
         "isAttractor","weight","proba_binding","proba_not_binding",
         "cutoff_boundary","cutoff_surface",
         "compareCompartment","compareCompartmentTolerance","compareCompartmentThreshold",]

        dic={"int":"inputInt","float":"inputFloat","bool":"checkbox","liste":"pullMenu","filename":"inputStr"}
        dic2={"int":"int","float":"float","bool":"int","liste":"int","filename":"str"}  
        if self.ingr is None :
            return
        if isinstance(self.ingr, GrowIngrediant) or isinstance(self.ingr, ActinIngrediant):
            self.listAttrOrdered.extend(["length","uLength","marge","constraintMarge","orientation","walkingMode"])#"biased",
        for option in self.listAttrOrdered:#sqelf.histoVol.OPTIONS:
            o = self.ingr.OPTIONS[option]
            if o["type"] == "vector" :
                #need three widget
                self.Widget["labeloptions"][option] = self._addElemt(name=o["name"]+"Label",label=o["description"],width=120)
                self.Widget["options"][option]=[]
                for i,x in enumerate(["x","y","z"]):
                    w=self._addElemt(name=o["name"]+x,value=o["value"][i],
                                    width=50,height=10,action=None,
                                    mini=o["min"],maxi=o["max"],
                                    variable=self.addVariable("float",v),
                                    type="inputFloat")
                    self.Widget["options"][option].append(w)
            else :
                if o["type"] == "liste": 
                    v = o["values"]
                    if o["name"] == "gradient":
                        v = list(self.histoVol.gradients.keys())
                        v.append("None")
                else : v = o["value"]
                
                self.Widget["labeloptions"][option] = self._addElemt(name=o["name"]+"Label",label=o["description"],width=120)
                self.Widget["options"][option] = self._addElemt(name=o["name"],value=v,
                                        width=200,height=10,action=None,
                                        mini=o["min"],maxi=o["max"],
                                        variable=self.addVariable(dic2[o["type"]],v),
                                        type=dic[o["type"]])
            option_cb = self.getFunctionForWidgetCallBack(option)
            self.Widget["edit"][option] = self._addElemt(name="ApplyToAll",width=50,height=10,
                         action=option_cb,type="button",icon=None,
                                     variable=self.addVariable("int",0))
#        if isinstance(self.ingr, GrowIngrediant) or isinstance(self.ingr, ActinIngrediant):
#            #what do we need to add
            
        self.Apply_btn=self._addElemt(name="Apply",width=100,height=10,
                         action=self.Apply,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.Apply_to_All_btn=self._addElemt(name="ApplyAllToAll",width=100,height=10,
                         action=self.ApplyToAll,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.ResetToDefault_btn=self._addElemt(name="Reset",width=100,height=10,
                         action=self.ResetToDefault,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        
        self.Close_btn=self._addElemt(name="Close",width=100,height=10,
                         action=self.close,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        
    def setupLayout(self):
        self._layout = []
        for wname in self.listAttrOrdered:        
#        for wname in self.Widget["options"]:
            widget =[self.Widget["labeloptions"][wname],self.Widget["options"][wname],self.Widget["edit"][wname]]
            if type(self.Widget["options"][wname]) == list: 
                widget =[self.Widget["labeloptions"][wname]]
                widget.extend(self.Widget["options"][wname])
            self._layout.append(widget) #
        
        self._layout.append([self.Apply_btn,self.Apply_to_All_btn,self.ResetToDefault_btn,self.Close_btn])

    def updateWidget(self):
#        for wname in self.Widget["options"]:
        for option in self.listAttrOrdered:
            o = self.ingr.OPTIONS[option]
            if o["type"] == "vector" :
#                print ("update "+option)
                v = getattr(self.ingr,option)
#                print ("valuexyz ",v)
                if v is None :
                    v = [0.,0.,0.]
                for i,x in enumerate(["x","y","z"]):    
                   self.setVal(self.Widget["options"][option][i],v[i]) 
            else :
                w = self.Widget["options"][option]
                v = getattr(self.ingr,option)
#                print("set w v",w,v)
                if o["name"]=="gradient" :
                    #updat the list of ingredient
                    self.resetPMenu(w)
                    for g in self.histoVol.gradients :
                        self.addItemToPMenu(w,g)
                    self.addItemToPMenu(w,"None") 
#                    print ("gradient for ingr ",g, "x")
                    if v =="" : 
                        v="None"
                self.setVal(w,v)

    def Apply(self, *args, **kw):
        for option in self.listAttrOrdered:
            o = self.ingr.OPTIONS[option]
            if o["type"] == "vector" :
                v=[self.getVal(w) for w in self.Widget["options"][option]]
                setattr(self.ingr,option,v)       
            else :
                w = self.Widget["options"][option]
                v = self.getVal(w)
                setattr(self.ingr,option,v)
#                self.setVal(w,v)

    def ApplyToAll(self, *args, **kw):
        r = self.ingr.recipe()
        for ingre in r.ingredients :
            for option in self.listAttrOrdered:
                o = self.ingr.OPTIONS[option]
                if o["type"] == "vector" :
                    v=[self.getVal(w) for w in self.Widget["options"][option]]
                    setattr(ingre,option,v)       
                else :
                    w = self.Widget["options"][option]
                    v = self.getVal(w)
                    setattr(ingre,option,v)

    def getFunctionForWidgetCallBack(self,name):
        #inr_cb = self.getFunctionForWidgetCallBack(ingr)
        aStr  = "def Apply"+name+"ToAllIngredient(*args):\n"
        aStr += '   r = self.ingr.recipe()\n'        
        aStr += '   o = self.ingr.OPTIONS["'+name+'"]\n'
        aStr += '   for ingre in r.ingredients :\n'
        aStr += '       if o["type"] == "vector" :\n'
        aStr += '           v=[self.getVal(w) for w in self.Widget["options"]["'+name+'"]]\n'
        aStr += '           setattr(ingre,"'+name+'",v)       \n'
        aStr += '       else :\n'
        aStr += '           w = self.Widget["options"]["'+name+'"]\n'
        aStr += '           v = self.getVal(w)\n'
        aStr += '           setattr(ingre,"'+name+'",v)\n'
        code_local = compile(aStr, '<string>', 'exec')
        l_dict={}#{ingr.name:ingr,"gui":self}
        g_dict = globals()
        g_dict["self"] = self
        exec(aStr,g_dict,l_dict)
        return l_dict["Apply"+name+"ToAllIngredient"]

    def ResetToDefault(self, *args, **kw):
        for wname in self.Widget["options"]:
            w = self.Widget["options"][wname]
            v = self.ingr.OPTIONS[wname]["default"]            
#            print (wname,v)
            self.setVal(w,v)
        #apply ?

class SubdialogCustomFiller(uiadaptor):
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1

    def setup(self,**kw):
#        self.subdialog = True
        self.recipe = kw["recipe"]
        self.title = self.recipe+" filler"#+self.mol.name
        witdh=550
        self.h=130
        self.w=220
        #first get the different module
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            helperClass = upy.getHelperClass()
            self.helper = helperClass(kw)#problem for DejaVu 
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        else :
            from AutoFill.autofill_viewer import AFViewer
            self.afviewer = AFViewer(ViewerType=self.host,helper=self.helper)
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        else :
            self.histoVol = None
        if self.histoVol is None :
            # create HistoVol
            from AutoFill.HistoVol import Environment
            self.histo = self.histoVol = Environment()
            self.histo.name = self.recipe
            self.afviewer.SetHistoVol(self.histo,20.,display=False)
        self.ingredients = []
        self.cleared = False
        #define the widget here too
        #create the template scene fromt afviewer
        self.afviewer.createTemplate()
        self.rSurf ={}
        self.rMatrix={}
        self.rCyto = Recipe()
        
        self.SetTitle(self.title)        
        self.initWidget()
        self.setupLayout()

    def initWidget(self, ):
        self.LABELS={}
        self.LABELS["intro"] = self._addElemt(name=self.recipe+"_wizard_intro",label="Setup a custom recipe from the outliner custom_setup object",width=120)
        self.LABELS["sOrga"] = self._addElemt(name=self.recipe+"_sOrga",
                    label="Place an organelle geometry in the Custom setup and click to update the setup",width=180)
        self.btn_setup_orga=self._addElemt(name="SetupOrganelle",width=100,height=10,
                         action=self.SetupOrga,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.LABELS["setup"] = self._addElemt(name=self.recipe+"_setup",
                    label="once ready click to setup the recipe and open the filler dialog",width=160)                             
        self.btn_setup=self._addElemt(name="SetupFill",width=100,height=10,
                         action=self.SetupFill,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        
    def setupLayout(self):
        self._layout = []
        self._layout.append([self.LABELS["intro"]])
        self._layout.append([self.LABELS["sOrga"] ])
        self._layout.append([self.btn_setup_orga])
        self._layout.append([self.LABELS["setup"] ])
        self._layout.append([self.btn_setup])
        
    def SetupOrga (self, *args, **kw):
        p = self.helper.getObject(self.recipe+'_organelles_name_geometries')
        ochild = self.helper.getChilds(p)
        for ob in ochild :
            name = self.helper.getName(ob)
            if name.find("Place") != -1 :
                continue
            for o in self.histoVol.organelles:
                if o.name == name :
                    #compare to the one already there
                    if o.ref_obj != name : 
                        self.histoVol.setOrganelleMesh(o,name)
                        self.afviewer.createOrganelMesh(o)
            orga = self.afviewer.addOrganelleFromGeom(name,ob)
            self.histoVol.addOrganelle(orga)
            self.rSurf[name] = Recipe()
            self.rMatrix[name] = Recipe()
            self.afviewer.createTemplateOrganelle(name)            

    def SetupFill (self, *args, **kw):
        #should parse the outlinr to find :            
        #organelles        
        #ingredients
        #histoVolBox
        p = self.helper.getObject(self.recipe+"_Setup")
        childs = self.helper.getChilds(p)
        if childs is not None :
            for c in childs:
                name = self.helper.getName(c)
#                print ("object",name)
                ochild = self.helper.getChilds(c)
                #first gem
                if name == self.recipe+'_organelles_name_geometries':                    
                    for o in ochild:
                        name = self.helper.getName(o)
                        if name.find("Place") != -1 :
                            continue
                        if name in self.rSurf :
                            continue
                        orga = self.afviewer.addOrganelleFromGeom(name,o)
                        self.histoVol.addOrganelle(orga)
                        self.rSurf[name] = Recipe()
                        self.rMatrix[name] = Recipe()
                if name == self.recipe+'_cytoplasm_ingredient':
                    for o in ochild:
                        name = self.helper.getName(o)
                        if name.find("Place") != -1 :
                            continue
                        ingr = self.afviewer.addIngredientFromGeom(name,o,recipe=self.rCyto)
                        #check if the geom is given then change the mesh_obj
                        mesh = self.helper.getObject(name+"_geom")                        
                        if mesh is not None :
                            ingr.mesh = mesh
                    self.histoVol.setExteriorRecipe(self.rCyto)
                if name == self.recipe+'_organelles_recipes':
                    #we hould have orga_name_recipe, followedby orga_name_surface and matrix
#                    print ("orga",self.histoVol.organelles)
                    for orga in self.histoVol.organelles :
                        name = orga.name+"_surface"
#                        print ("organelle",orga,name) 
                        o = self.helper.getObject(name)
                        if o is not None :
                            ingrchild = self.helper.getChilds(o)
                            for ingro in ingrchild:
                                 n = self.helper.getName(ingro)
                                 if n.find("Place") != -1 :
                                    continue
                                 ingr = self.afviewer.addIngredientFromGeom(n,ingro,recipe=self.rSurf[orga.name])
                                 mesh = self.helper.getObject(n+"_geom")                        
                                 if mesh is not None :
                                    ingr.mesh = mesh
                            orga.setSurfaceRecipe(self.rSurf[orga.name])
                        name = orga.name+"_interior"
                        o = self.helper.getObject(name)
                        if o is not None :
                            ingrchild = self.helper.getChilds(o)
                            for ingro in ingrchild:
                                 n = self.helper.getName(ingro)
                                 if n.find("Place") != -1 :
                                    continue
                                 ingr = self.afviewer.addIngredientFromGeom(n,ingro,recipe=self.rMatrix[orga.name])  
                                 mesh = self.helper.getObject(n+"_geom")                        
                                 if mesh is not None :
                                    ingr.mesh = mesh
                            orga.setInnerRecipe(self.rMatrix[orga.name])
        self.drawSubsetFiller()
        self.close()
           
    def drawSubsetFiller(self,*args):
        self.histoVol.setMinMaxProteinSize()
        self.afviewer.displayPreFill()
        #should drawhe dialog for the seleced recipe
        dlg = SubdialogFiller() 
        dlg.setup(recipe=self.recipe,histoVol=self.histoVol,
                  afviewer=self.histoVol.afviewer,helper=self.helper,version="1.0")
        dlg.gridresultfile = AFwrkDir1+os.sep+"cache_results"+os.sep+self.recipe+"_fillgrid"
#        print  ("draw",dlg.gridresultfile)
        self.drawSubDialog(dlg,555555556)
        dlg.updateWidget()

#create subdialog here
#could be in different file
class SubdialogFiller(uiadaptor):
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1

    def setup(self,**kw):
#        self.subdialog = True
        self.block = True
#        self.scrolling = True
        self.recipe = kw["recipe"]
        self.recipe_version = kw["version"]
        self.title = self.recipe+" Filler v"+self.recipe_version
        
        #first column shoud adapt to ingredients name max length 
        self.h=230
#        self.w=100#sum(self.wicolumn)
        #first get the different module
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            helperClass = upy.getHelperClass()
            self.helper = helperClass(kw)#problem for DejaVu 
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        else :
            from AutoFill.autofill_viewer import AFViewer
            self.afviewer = AFViewer(ViewerType=self.host,helper=self.helper)
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        else :
            self.histoVol = None
        if self.histoVol is None :
            # create HistoVol
            from AutoFill.HistoVol import Environment
            self.histo = self.histoVol = Environment()        
        self.parent = None
        if "parent" in kw :
            self.parent = kw["parent"]
        self.guimode = "Advanced"
        if "guimode" in kw :
            self.guimode = kw["guimode"]
        self.ingredients = []
        self.ingredients_ui = {}
        self.gradients_ui={}
        self.ingr_added={}
        self.orga_added={}
        self.cleared = False
        self.gridresultfile = None #AutoFill.RECIPES[self.recipe]["wrkdir"]+os.sep+"results"+os.sep+"fill_grid"
        self.setupfile= self.histoVol.setupfile#AutoFill.RECIPES[self.recipe]["setupfile"]
        #define the widget here too
        #getingrname longest
        W=self.histoVol.longestIngrdientName()*5
        self.wicolumn = [W,35,35,30,25,50,50,30]
        self.w=sum(self.wicolumn)+5
        self.SetTitle(self.title)
        self.grid_filename = self.recipe+"_gridSetup"
        self.initWidget()
        self.setupLayout_tab()

    def Set(self,**kw):
        if "helper" in kw :
            self.helper = kw["helper"]
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        self.cleared = False
    
        
    def initWidget(self, ):
        #the menu for saving the change
        #and also to add it to the available liste of recipe
        self.menuorder = ["File",]
        self._menu = self.MENU_ID = {"File":
                      [self._addElemt(name="Save",action=self.save),
                      self._addElemt(name="Save as",action=self.saveas),#self.buttonLoad},
                      self._addElemt(name="Append to available recipe as",action=self.appendtoRECIPES),
                      ],#self.buttonLoadData
                       }
        if self.helper.host.find("blender") != -1:
            self.setupMenu()

        self.Widget={}
        self.BTN={}
        self.Widget["labeloptions"]={}
        self.Widget["options"]={}        
        #options widget checkbox and input
        dic={"int":"inputInt","float":"inputFloat","bool":"checkbox","liste":"pullMenu","filename":"inputStr"}
        dic2={"int":"int","float":"float","bool":"int","liste":"int","filename":"str"}        
        #need a histoVol
        if self.histoVol is None or self.afviewer is None:
            print ("no histovol or autoPACKviewer")
            return
#==============================================================================
#         #list of option we want to show to the user        
#==============================================================================
        self.listAFo ={}
        self.listAFoptions = ["runTimeDisplay",#0
                              "overwritePlaceMethod",#1
                              "placeMethod",#2
                               "freePtsUpdateThrehod",#3   
                               "prevIngr",#4
                               "prevFill",#5
                               "forceBuild",#6                           
                              "innerGridMethod",#7
                              "smallestProteinSize",#8
                              "use_gradient",#9
                              "gradients",#10
                              "pickWeightedIngr",#11
                              "pickRandPt",#12
                              "saveResult",#13
                              "resultfile",#14
                              "gridPts",#15
                              "spherePrimitive"#16
                              ]
        self.listAFo["Simple"]=[0,1,2,6,8,13,14]
        self.listAFo["Intermediate"]=[0,1,2,4,5,6,8,9,13,14]
        self.listAFo["Advanced"]= [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        self.listAFo["Debug"]=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]                   
        #add here the optnios you want
#        for option in self.listAFoptions:#self.histoVol.OPTIONS:
        print ("self.guimode",self.guimode)
        for i in self.listAFo["Debug"]:
            option =  self.listAFoptions[i]
            if option not in self.histoVol.OPTIONS:
                if option == "prevIngr":                                   
                    self.Widget["options"][option]= self._addElemt(name=self.recipe+"previousIngr",
                            width=80,height=10,label="Pack around existing objects (place objects under "+self.recipe+"_PreviousIngrOrga)",
                            action=None,type="checkbox",icon=None,
                            variable=self.addVariable("int",1),value=1)
                elif option == "prevFill":                                    
                    self.Widget["options"][option] = self._addElemt(name=self.recipe+"previousFil",
                                        width=80,height=10,label="Pack around a previous fill ([Pack], move or enlarge FillBox & [Pack] again)",
                                        action=None,type="checkbox",icon=None,
                                        variable=self.addVariable("int",0),value=0)
                elif option == "gridPts":
                    self.Widget["options"][option] = self._addElemt(name='dopts',width=100,height=10,
                                              action=None,type="checkbox",icon=None,label="Show grid Points",
                                              variable=self.addVariable("int",0))
                elif option == "spherePrimitive":
                    self.Widget["options"][option] = self._addElemt(name='dosph',width=100,height=10,
                                              action=None,type="checkbox",icon=None,label="Show sphereTree primitives",
                                              variable=self.addVariable("int",0))
                elif option == "forceBuild":                                     
                    self.Widget["options"][option] =self._addElemt(name=self.recipe+"_forceBuildGrid",
                            width=80,height=10,label="Rebuild the grid",
                            action=None,type="checkbox",icon=None,
                            variable=self.addVariable("int",1),value=1)
                continue
            o = self.histoVol.OPTIONS[option]
            if o["type"] == "liste": 
                v = o["values"]
                if o["name"] == "gradients":
                    v = list(self.histoVol.gradients.keys())
            else : v = o["value"]
            mini=0.0
            maxi=200.0
            if "mini" in o:
                mini = o["mini"]
                maxi = o["maxi"]
            if o["name"] == "gradients":
                self.Widget["options"]["gradients"] = self._addElemt(name=o["name"],value=v,
                                    width=120,height=10,action=None,
                                    variable=self.addVariable("int",0),
                                    type=dic[o["type"]])
                self.BTN["edit_gradients"] = self._addElemt(name="Edit Selected Gradient",width=150,height=10,
                         action=self.EditGradient,type="button",icon=None,label="Edit Selected Gradient",
                                     variable=self.addVariable("int",0)) 
                self.BTN["add_gradients"] = self._addElemt(name="Add New Gradient",width=150,height=10,
                                 action=self.AddGradient,type="button",icon=None,label="Add New Gradient",
                                             variable=self.addVariable("int",0))
                                     
            else :
                #print ("should add ",o["name"])
                self.Widget["labeloptions"][option] = self._addElemt(name=o["name"]+"Label",label=o["description"],width=200)
                self.Widget["options"][option] = self._addElemt(name=o["name"],value=v,
                                    width=o["width"],height=10,action=None,label=o["description"],
                                    variable=self.addVariable(dic2[o["type"]],v),
                                    type=dic[o["type"]])

        self.setupRecipeMenu()

        widthButton = 30

#        if self.guimode != "Simple" and self.guimode != "Intermediate":
            #display current gradient, and a button for adding some
#        self.LABELS["gradients"]={}
#        self.LABELS["gradients"]["label"] = self._addElemt(label="Add a Gradient",width=120, height=5) 
                                     
                                     
        self.LABELS["RandomSeed"] = self._addElemt(label="Random seed =",width=50, height=5)  
        self.LABELS["WelcomeVersionNumber"] = self._addElemt(label="Welcome to autoPACK v"+AutoFill.__version__,width=100, height=5)  

        self.seedId = self._addElemt(name='seed',width=30,height=10,
                                              action=None,type="inputFloat",icon=None,
                                              variable=self.addVariable("float",14.),
                                              mini=0.0,maxi=200.0,step=1.,precision=2)



        self.BTN["fill"]=self._addElemt(name="PACK",width=widthButton+30,height=10,
                         action=self.fillGrid,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["updateNMol"]=self._addElemt(name="Update Totals",width=widthButton+30,height=10,
                         action=self.updateNBMOL,type="button",icon=None,
                             #label = "Approximate total to attempt",
                                     variable=self.addVariable("int",0))

        self.BTN["resetAll"]=self._addElemt(name="Clear Recipe",width=widthButton+30,height=10,
                         action=self.clearAll,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["reset"]=self._addElemt(name="Clear Packing",width=widthButton+30,height=10,
                         action=self.clearFill,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["resultFile"]=self._addElemt(name="dlg_result_file",width=15,height=10,
                         action=self.setupResultFile,type="button",icon=None,label="...",
                                     variable=self.addVariable("int",0),alignement="hleft")
        self.LABELSINGR={}
        self.LABELS["Time"] = self._addElemt(label="",width=100, height=10)
#        print ("widget inted with mode ",self.guimode)

    def getLabelIngr1(self,rname):
        self.LABELSINGR[rname]=[]
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"i",label="Include",width=self.wicolumn[0]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"d",label="Density",width=self.wicolumn[1]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"a",label="+ this",width=self.wicolumn[2]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"t",label="Total",width=self.wicolumn[3]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"p",label="",width=self.wicolumn[4]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"c",label="Collision",width=self.wicolumn[5]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"v",label="Visible ",width=self.wicolumn[6]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"o",label="Advanced",width=self.wicolumn[7]))
        return self.LABELSINGR[rname]
    
    def getLabelIngr2(self,rname,name):#o.name+"surface"
        self.LABELSINGR[rname]=[]
        self.LABELSINGR[rname].append(self.ingr_include[name])
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"d",label="(M or surfM)",width=self.wicolumn[1]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"a",label="ingredients",width=self.wicolumn[2]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"t",label="to attempt ",width=self.wicolumn[3]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"p",label="Priority",width=self.wicolumn[4]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"c",label="proxy     ",width=self.wicolumn[5]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"v",label="geometry",width=self.wicolumn[6]))
        self.LABELSINGR[rname].append(self._addElemt(name=rname+"o",label="Options",width=self.wicolumn[7]))
        return self.LABELSINGR[rname]

    def getFunctionForWidgetCallBack(self,ingr):
        #inr_cb = self.getFunctionForWidgetCallBack(ingr)
        aStr  = "def editIngr"+ingr.name+"(*args):\n\tgui.advancedIngr_ui("+ingr.name+")\n"#print("+ingr.name+","+ingr.name+".name)\n
        code_local = compile(aStr, '<string>', 'exec')
        l_dict={}#{ingr.name:ingr,"gui":self}
        g_dict = globals()
        g_dict[ingr.name] = ingr
        g_dict["gui"] = self
        exec(aStr,g_dict,l_dict)
        return l_dict["editIngr"+ingr.name]

    def getFunctionForWidgetCallBackInclude(self,oname,rname,i):
        #inr_cb = self.getFunctionForWidgetCallBack(ingr)
        #def toggleIngrIncOrganelle():                    
            #includeTog  = self.getVal(self.ingr_include[o.name+"surface"])
            #self.togleRecipeIngrInc(rs,includeTog)         
        aStr  = "def toggleIngrInc"+oname+rname+"(*args):\n"
        aStr +="\tincludeTog  = gui.getVal(gui.ingr_include['"+oname+rname+"'])\n"
        if rname =="surface" :
            recipe = "gui.histoVol.organelles["+str(i)+"].surfaceRecipe"
        else :
            recipe = "gui.histoVol.organelles["+str(i)+"].innerRecipe"
        aStr +="\tgui.togleRecipeIngrInc("+recipe+",includeTog)\n"#print("+ingr.name+","+ingr.name+".name)\n
        #code_local = compile(aStr, '<string>', 'exec')
        l_dict={}#{ingr.name:ingr,"gui":self}
        g_dict = globals()
        #g_dict[rname] = recipe
        g_dict["gui"] = self
        exec(aStr,g_dict,l_dict)
        return l_dict["toggleIngrInc"+oname+rname]
                                          
    def setupRecipeMenu(self,):
        self.LABELS={}
        self.Label_spacer={}
        self.ingr_include={}
        self.ingr_molarity={}
        self.ingr_nMol={}
        self.ingr_ref_object={}
        self.ingr_view_object={}
        self.ingr_priority={}
        self.ingr_advanced={} 
        self.ingr_vol_nbmol={} 
        self.Widget["organelles_mesh"]={}   
        self.Widget["organelles_overw"]={}
        
        self.LABELS["fbox"]=self._addElemt(name="fbox",label="Set Filling Box to Object named:",width=120)
        self.fbox_name=self._addElemt(name=self.recipe+"fbox",action=None,width=100,
                          value="fillBB",type="inputStr",variable=self.addVariable("str","fillBB"))       
        self.LABELS["bbox"]=self._addElemt(name="bbox",label="Set padded Bounding Box to Object named:",width=120)
        self.bbox_name=self._addElemt(name=self.recipe+"bbox",action=None,width=100,
                          value="histoVolBB",type="inputStr",variable=self.addVariable("str","histoVolBB"))         

        #cytoplasm first
        self.LABELS["cytoplasm"] = self._addElemt(name=self.recipe+"cyto",label="Setup ingredient for %s exterior space:"%(self.recipe),width=125)#,height=50)
 
        self.LABELS["RecipeColumnsEmptySpace50"] = self._addElemt(label=" ",width=1, height=5)
        self.LABELS["RecipeColumnsEmptySpace100"] = self._addElemt(label=" ",width=10, height=5)  
        self.LABELS["RecipeColumnsEmptySpace120"] = self._addElemt(label=" ",width=12, height=5)  
        self.LABELS["RecipeColumnsPipe"] = self._addElemt(label="|",width=120, height=5)  
        

        ingrWidgetWidth = 25
        r =  self.histoVol.exteriorRecipe
        ingCounter = 0
        if r :           
            for ingr in r.ingredients:
                self.LABELS[ingr.name] = self._addElemt(name=ingr.name+"Label",label="    %s"%ingr.name,width=120)#,height=50)
                self.ingr_include[ingr.name] = self._addElemt(name=ingr.name, width=self.wicolumn[0],height=10,
                            action=None,type="checkbox",icon=None,variable=self.addVariable("int",1),value=1)
                self.ingr_molarity[ingr.name] = self._addElemt(name=ingr.name+"mol",action=None,width=self.wicolumn[1],
                  value=str(ingr.molarity),type="inputStr",variable=self.addVariable("str",str(ingr.molarity)),mini=0.0,maxi=100.0)  
#                print "molarity",ingr.molarity,str(ingr.molarity)
                self.ingr_nMol[ingr.name] = self._addElemt(name=ingr.name+"nMol",action=None,width=self.wicolumn[2],
                  value=ingr.nbMol,type="inputInt",variable=self.addVariable("int",ingr.nbMol),mini=0,maxi=1000)   
                self.ingr_vol_nbmol[ingr.name] = self._addElemt(name=ingr.name+"NB",label=str(ingr.nbMol),width=self.wicolumn[3])
                self.ingr_priority[ingr.name] = self._addElemt(name=ingr.name+"P",action=None,width=self.wicolumn[4],
                  value=ingr.packingPriority,type="inputFloat",variable=self.addVariable("float",ingr.packingPriority),mini=-200.,maxi=50.)                 
                self.ingr_ref_object[ingr.name] = self._addElemt(name=ingr.name+"ref",action=None,width=self.wicolumn[5],
                  value=ingr.modelType,type="inputStr",variable=self.addVariable("str",ingr.modelType))  
                self.ingr_view_object[ingr.name] = self._addElemt(name=ingr.name+"view",action=None,width=self.wicolumn[6],
                  value=self.helper.getName(ingr.mesh),type="inputStr",variable=self.addVariable("str",self.helper.getName(ingr.mesh))) 
#                func = None 
#                print (ingr.name,ingr.packingPriority)
                inr_cb = self.getFunctionForWidgetCallBack(ingr)
                self.ingr_advanced[ingr.name] = self._addElemt(name="Edit",action=inr_cb,width=self.wicolumn[7],height=10,
                        type="button",variable=self.addVariable("int",0)) 
            self.ingr_include["cytoplasm"] = self._addElemt(name="All",#+self.recipe,
                            width=self.wicolumn[0],height=10,
                            action=self.toggleIngrIncExterior,type="checkbox",icon=None,
                            variable=self.addVariable("int",1),value=1)                             
        for i,o in enumerate(self.histoVol.organelles):
            self.LABELS[o.name] = self._addElemt(name="orgalabel",label="Set %s %s to object named :"%(self.recipe, o.name),width=120)#,height=50)
            self.Widget["organelles_mesh"][o.name]=self._addElemt(name=o.name+"mesh",action=None,width=100,
                          value=o.ref_obj,type="inputStr",variable=self.addVariable("str",o.ref_obj)) 
            
            self.Widget["organelles_overw"][o.name]=self._addElemt(name="overwriteSurfacePts "+o.name,
                            width=self.wicolumn[0],height=10,
                            action=self.toggleoverWOrganelle,type="checkbox",icon=None,
                            variable=self.addVariable("int",1),value=1)
              
            self.LABELS[o.name+"surface"+"_ingr"] = self._addElemt(name="ingrorgalabel",label="Setup ingredient for %s %s surface"%(self.recipe, o.name),width=120)#,height=50)
            self.LABELS[o.name+"matrix"+"_ingr"] = self._addElemt(name="ingrorgalabel",label="Setup ingredient for %s %s matrix"%(self.recipe, o.name),width=120)#,height=50)
                        
            rs =  o.surfaceRecipe
            if rs :              
                for ingr in rs.ingredients:
                    self.LABELS[ingr.name] = self._addElemt(name=ingr.name+"Label",label="    %s"%ingr.name,width=120)#,height=50)
                    self.ingr_include[ingr.name] = self._addElemt(name=ingr.name, width=self.wicolumn[0],height=10,
                                action=None,type="checkbox",icon=None,variable=self.addVariable("int",1),value=1)
                    self.ingr_molarity[ingr.name] = self._addElemt(name=ingr.name+"mol",action=None,width=self.wicolumn[1],
                      value=ingr.molarity,type="inputStr",variable=self.addVariable("str",str(ingr.molarity)),mini=0.0,maxi=100.0)  
                    self.ingr_nMol[ingr.name] = self._addElemt(name=ingr.name+"nMol",action=None,width=self.wicolumn[2],
                      value=ingr.nbMol,type="inputInt",variable=self.addVariable("int",ingr.nbMol),mini=0,maxi=1000)   
                    self.ingr_vol_nbmol[ingr.name] = self._addElemt(name=ingr.name+"NB",label=str(ingr.nbMol),width=self.wicolumn[3])
                    self.ingr_priority[ingr.name] = self._addElemt(name=ingr.name+"P",action=None,width=self.wicolumn[4],
                      value=ingr.packingPriority,type="inputFloat",variable=self.addVariable("float",ingr.packingPriority),mini=-200.,maxi=50.)                 
                    self.ingr_ref_object[ingr.name] = self._addElemt(name=ingr.name+"ref",action=None,width=self.wicolumn[5],
                      value=ingr.modelType,type="inputStr",variable=self.addVariable("str",ingr.modelType))  
                    self.ingr_view_object[ingr.name] = self._addElemt(name=ingr.name+"view",action=None,width=self.wicolumn[6],
                      value=self.helper.getName(ingr.mesh),type="inputStr",variable=self.addVariable("str",self.helper.getName(ingr.mesh))) 
    #                func = None 
#                    print (ingr.name,ingr.packingPriority,self.ingr_include[ingr.name])
                    inr_cb = self.getFunctionForWidgetCallBack(ingr)
                    self.ingr_advanced[ingr.name] = self._addElemt(name="Edit",action=inr_cb,width=self.wicolumn[7],height=10,
                            type="button",variable=self.addVariable("int",0))                
                cb= self.getFunctionForWidgetCallBackInclude(o.name,"surface",i)
                self.ingr_include[o.name+"surface"] = self._addElemt(name="All "+o.name,
                            width=self.wicolumn[0],height=10,
                            action=cb,type="checkbox",icon=None,
                            variable=self.addVariable("int",1),value=1) 
   
            ri =  o.innerRecipe
            if ri :                
                for ingr in ri.ingredients:
                    self.LABELS[ingr.name] = self._addElemt(name=ingr.name+"Label",label="    %s"%ingr.name,width=120)#,height=50)
                    self.ingr_include[ingr.name] = self._addElemt(name=ingr.name, width=self.wicolumn[0],height=10,
                                action=None,type="checkbox",icon=None,variable=self.addVariable("int",1),value=1)
                    self.ingr_molarity[ingr.name] = self._addElemt(name=ingr.name+"mol",action=None,width=self.wicolumn[1],
                      value=ingr.molarity,type="inputStr",variable=self.addVariable("str",str(ingr.molarity)),mini=0.0,maxi=100.0)  
                    self.ingr_nMol[ingr.name] = self._addElemt(name=ingr.name+"nMol",action=None,width=self.wicolumn[2],
                      value=ingr.nbMol,type="inputInt",variable=self.addVariable("int",ingr.nbMol),mini=0,maxi=1000)   
                    self.ingr_vol_nbmol[ingr.name] = self._addElemt(name=ingr.name+"NB",label=str(ingr.nbMol),width=self.wicolumn[3])
                    self.ingr_priority[ingr.name] = self._addElemt(name=ingr.name+"P",action=None,width=self.wicolumn[4],
                      value=ingr.packingPriority,type="inputFloat",variable=self.addVariable("float",ingr.packingPriority),mini=-200.,maxi=50.)                 
                    self.ingr_ref_object[ingr.name] = self._addElemt(name=ingr.name+"ref",action=None,width=self.wicolumn[5],
                      value=ingr.modelType,type="inputStr",variable=self.addVariable("str",ingr.modelType))  
                    self.ingr_view_object[ingr.name] = self._addElemt(name=ingr.name+"view",action=None,width=self.wicolumn[6],
                      value=self.helper.getName(ingr.mesh),type="inputStr",variable=self.addVariable("str",self.helper.getName(ingr.mesh))) 
    #                func = None 
#                    print (ingr.name,ingr.packingPriority)
                    inr_cb = self.getFunctionForWidgetCallBack(ingr)
                    self.ingr_advanced[ingr.name] = self._addElemt(name="Edit",action=inr_cb,width=self.wicolumn[7],height=10,
                            type="button",variable=self.addVariable("int",0)) 
                cb= self.getFunctionForWidgetCallBackInclude(o.name,"matrix",i)
                self.ingr_include[o.name+"matrix"] = self._addElemt(name="All "+o.name,
                            width=self.wicolumn[0],height=10,
                            action=cb,type="checkbox",icon=None,
                            variable=self.addVariable("int",1),value=1)
                        
    def setupLayout_tab(self):
        #can handle the gui mode here actually
        self._layout = []
        #one frame for fill option
        elemFrame=[]
        listeoptions=self.listAFo[self.guimode]
        for i in listeoptions: 
            wname = self.listAFoptions[i]
            if wname == "use_gradient":#show up only if self.guimode != "Simple" and self.guimode != "Intermediate":
                if self.guimode != "Simple" and self.guimode != "Intermediate":
                    elemFrame.append([self.Widget["options"][wname]])
                    elemFrame.append([self.BTN["add_gradients"], self.LABELS["RecipeColumnsEmptySpace100"], self.LABELS["RecipeColumnsEmptySpace100"], self.LABELS["RecipeColumnsEmptySpace100"]])
                    elemFrame.append([self.Widget["options"]["gradients"],self.BTN["edit_gradients"], self.LABELS["RecipeColumnsEmptySpace100"], self.LABELS["RecipeColumnsEmptySpace100"]])
                else :
                    elemFrame.append([self.Widget["options"][wname],])
            elif wname == "gradients":
                continue            
            elif wname == "placeMethod" or wname == "innerGridMethod" :
                elemFrame.append([self.Widget["labeloptions"][wname], self.Widget["options"][wname], self.LABELS["RecipeColumnsEmptySpace100"]])
            elif wname == "freePtsUpdateThrehod" or wname == "smallestProteinSize" :
                elemFrame.append([self.Widget["options"][wname],self.Widget["labeloptions"][wname],self.LABELS["RecipeColumnsEmptySpace100"]]) 
            elif wname == "resultfile":
                elemFrame.append([self.Widget["options"][wname],self.BTN["resultFile"]])
            else :
                elemFrame.append([self.Widget["options"][wname],])
        frame = self._addLayout(id=196,name="PACKing Options",elems=elemFrame,collapse=False, type="tab")#,type="tab")
        self._layout.append(frame)
        
        elemFrame=[]
        elemFrame.append([self.LABELS["bbox"],self.bbox_name])
        elemFrame.append([self.LABELS["fbox"],self.fbox_name])
        
#        elemFrame.append(self.LABELSINGR)
        for o in self.histoVol.organelles:
            #each organelle
            subelem=[]
            subelem.append([self.LABELS[o.name],self.Widget["organelles_mesh"][o.name]])
            subelem.append([self.Widget["organelles_overw"][o.name],])
            subelem.append([self.LABELS[o.name+"surface"+"_ingr"] ])#,self.ingr_include[o.name+"surface"]])
            rs =  o.surfaceRecipe
            if rs :
                subelem.append(self.getLabelIngr1(o.name+"surf"))
                subelem.append(self.getLabelIngr2(o.name+"surf", o.name+"surface"))
                for ingr in rs.ingredients:
                    subelem.append([self.ingr_include[ingr.name],
                                 self.ingr_molarity[ingr.name],self.ingr_nMol[ingr.name],self.ingr_vol_nbmol[ingr.name],
                                 self.ingr_priority[ingr.name],
                                self.ingr_ref_object[ingr.name],self.ingr_view_object[ingr.name],
                                self.ingr_advanced[ingr.name]])#
            frame = self._addLayout(id=196,name=o.name+" Surface setup ",elems=subelem,collapse=False)
            elemFrame.append(frame)
            subelem=[]
            subelem.append([self.LABELS[o.name+"matrix"+"_ingr"] ])#,self.ingr_include[o.name+"matrix"]])
#            elemFrame.append(self.LABELSINGR)
            ri =  o.innerRecipe
            if ri :
                subelem.append(self.getLabelIngr1(o.name+"inner"))
                subelem.append(self.getLabelIngr2(o.name+"inner", o.name+"matrix"))
                for ingr in ri.ingredients:
                    subelem.append([self.ingr_include[ingr.name],
                                 self.ingr_molarity[ingr.name],self.ingr_nMol[ingr.name],self.ingr_vol_nbmol[ingr.name],
                                 self.ingr_priority[ingr.name],
                                self.ingr_ref_object[ingr.name],self.ingr_view_object[ingr.name],
                                self.ingr_advanced[ingr.name]])#
        
            frame = self._addLayout(id=196,name=o.name+" Matrix setup ",elems=subelem,collapse=False)  
            elemFrame.append(frame)
        
        subelem=[]
        subelem.append([self.LABELS["cytoplasm"] ])#,self.ingr_include["cytoplasm"]])
        r =  self.histoVol.exteriorRecipe
        if r :
#            subelem.append(self.ingr_include["cytoplasm"])
            subelem.append(self.getLabelIngr1("cyto"))
            subelem.append(self.getLabelIngr2("cyto","cytoplasm"))
            for ingr in r.ingredients:
                subelem.append([self.ingr_include[ingr.name],
                                 self.ingr_molarity[ingr.name],self.ingr_nMol[ingr.name],self.ingr_vol_nbmol[ingr.name],
                                 self.ingr_priority[ingr.name],
                                self.ingr_ref_object[ingr.name],self.ingr_view_object[ingr.name],
                                self.ingr_advanced[ingr.name]])#
        frame = self._addLayout(id=196,name="Exterior ingredients' setup",elems=subelem,collapse=False)
        elemFrame.append(frame)
    
        elemFrame.append([self.LABELS["RecipeColumnsEmptySpace100"],self.LABELS["RecipeColumnsEmptySpace100"],
                          self.LABELS["RecipeColumnsEmptySpace100"],self.BTN["updateNMol"], 
                          self.LABELS["RecipeColumnsEmptySpace100"],self.LABELS["RecipeColumnsEmptySpace100"],
                          self.LABELS["RecipeColumnsEmptySpace100"],self.LABELS["RecipeColumnsEmptySpace100"] ])
#        elemFrame.append([self.BTN["updateNMol"],])
        frame = self._addLayout(id=196,name="Recipe options",elems=elemFrame,collapse=False,scrolling=True, type="tab")
        self._layout.append(frame)    
        
        self._layout.append([self.LABELS["RecipeColumnsEmptySpace50"],
                             self.LABELS["RandomSeed"],
                             self.seedId,self.BTN['fill'],self.BTN["reset"],self.BTN["resetAll"],
                             self.LABELS["RecipeColumnsEmptySpace50"],self.LABELS["RecipeColumnsEmptySpace100"]
                             ])
                             
        self._layout.append([self.LABELS["Time"],#])#self.LABELS["RecipeColumnsEmptySpace100"],
                             #self.LABELS["RecipeColumnsEmptySpace100"],self.LABELS["RecipeColumnsEmptySpace100"],
#                             self.LABELS["RecipeColumnsEmptySpace100"],
#                            self.LABELS["RecipeColumnsEmptySpace100"],
#                             self.LABELS["RecipeColumnsEmptySpace100"],
                            self.LABELS["RecipeColumnsEmptySpace100"],self.LABELS["WelcomeVersionNumber"] ])
#        self._layout.append([self.LABELS["WelcomeVersionNumber"] ])

    def advancedIngr_ui(self,ingr):
#        print(ingr,ingr.name)
        if ingr.name not in self.ingredients_ui or self.ingredients_ui[ingr.name] is None :
            dlg = SubdialogIngrdient()
            dlg.setup(ingr=ingr,subdialog = True,histoVol=self.histoVol)
            self.ingredients_ui[ingr.name] = dlg
        self.drawSubDialog(self.ingredients_ui[ingr.name],555555553)
        self.ingredients_ui[ingr.name].updateWidget()
        
    def delIngr(self,ingr):
        ingrname=ingr.name
        parentname =  "Meshs_"+ingrname.replace(" ","_")
        parent = self.helper.getObject(parentname)
#        print ("Delete",ingrname,parentname,parent)
        if parent is not None :
            if self.helper.host == "dejavu":
                pass
                #self.helper.deleteObject(parent)
            else :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent) #is this dleete the child ?
        #need to do the same for cylinder
        if self.helper.host == "dejavu":
            ingr.ipoly.Set(instanceMatrices=[[[ 1.,  0.,  0.,  0.],
       [ 0.,  1.,  0.,  0.],
       [ 0.,  0.,  1.,  0.],
       [ 0.,  0.,  0.,  1.]]], visible=1)
            ingr.mesh_3d  = ingr.mesh
            #what about sphere gemetry ingredient
            from DejaVu.Spheres import Spheres
            if isinstance(ingr.mesh,Spheres):
                ingr.mesh.Set(centers=[])
        else :
            ingr.ipoly = None
        self.afviewer.addMasterIngr(ingr)#this will restore the correct parent
        if self.afviewer.doSpheres :
            orga = ingr.recipe().organelle()
            name = orga.name+"_Spheres_"+ingr.name.replace(" ","_")    
            parent = self.helper.getObject(name)
#            print (name,parent)            
            if parent is not None :
                if self.helper.host == "dejavu":
                    self.helper.deleteObject(parent)
                else :
                    instances = self.helper.getChilds(parent)
                    [self.helper.deleteObject(o) for o in instances]
                    self.helper.deleteObject(parent)
            name = orga.name+"_Cylinders_"+ingr.name.replace(" ","_")    
            parent = self.helper.getObject(name)
#            print (name,parent)            
            if parent is not None :
                if self.helper.host == "dejavu":
                    self.helper.deleteObject(parent)
                else :
                    instances = self.helper.getChilds(parent)
                    [self.helper.deleteObject(o) for o in instances]
                    self.helper.deleteObject(parent)
        if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
            #need to delete te spline and the data
            o = ingr.recipe().organelle()
            for i in range(ingr.nbCurve):
                name = o.name+str(i)+"snake_"+ingr.name.replace(" ","_")
                snake = self.helper.getObject(name)
                self.helper.deleteObject(snake)
            ingr.reset()

    def clearIngr(self,*args):
        """ will clear all ingredients instances but leave base parent hierarchie intact"""
        self.histoVol.loopThroughIngr(self.delIngr)        
#        [self.delIngr(ingrname) for ingrname in self.ingredients]
    
    def clearRecipe(self,*args):
        """ will clear everything related to self.recipe"""
        parent = self.helper.getObject(self.recipe)
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent)
            else :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent)
            #if dejavu can delete the parent directly

    def clearAll(self,*args):
        #shoud remove everything
        self.clearRecipe()
        #reset the fill
        self.clearFill()
        self.cleared = True
        self.close()
        #should we destroy it ?

    def clearOrgaAdded(self,):
        for oname in self.orga_added:
            o=self.orga_added[oname]
            if o in self.histoVol.organelles:
                i = self.histoVol.organelles.index(o)
                self.histoVol.organelles.pop(o)
                del o
        self.orga_added={}
                
    def clearIngrAdded(self,): 
        for iname in self.ingr_added:
            ingr = self.ingr_added[iname]
            if self.histoVol.exteriorRecipe:
                if ingr in self.histoVol.exteriorRecipe.ingredients:
                    i = self.histoVol.exteriorRecipe.ingredients.index(ingr)
                    self.histoVol.exteriorRecipe.ingredients.pop(i)
                    del ingr
            for o in self.histoVol.organelles:
                if o.surfaceRecipe:
                    if ingr in o.surfaceRecipe.ingredients:
                        i = o.surfaceRecipe.ingredients.index(ingr)
                        o.surfaceRecipe.ingredients.pop(i)
                        del ingr
                if o.innerRecipe:
                    if ingr in o.innerRecipe.ingredients:
                        i = o.innerRecipe.ingredients.index(ingr)
                        o.innerRecipe.ingredients.pop(i)
                        del ingr
                    
        self.ingr_added={}
            
    def clearFill(self,*args):
        #should ony reset the fill
        self.histoVol.reset()
        if self.histoVol.ingr_result is not None :
            self.ingredients =self.histoVol.ingr_result
        self.clearIngr()
        #need to clear also the static object
        parentname =  self.recipe+"static"
        parent = self.helper.getObject(parentname)
#        print (parentname,parent)
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent)
            else :
                static = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in static]
        parentname =  "staticMesh"
        parent = self.helper.getObject(parentname)
#        print (parentname,parent)
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent)
            else :
                static = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in static]
        
        self.clearOrgaAdded()
        self.clearIngrAdded()
        
        #need to clear also the moving object
        parentname =  self.recipe+"moving"
        parent = self.helper.getObject(parentname)
#        print (parentname,parent)
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent)
            else :
                static = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in static]

        parent = self.helper.getObject(self.recipe+"GridPointHider")
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent)
            else :
                point = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in point]
        
        for orga in self.histoVol.organelles:  
            parent = self.helper.getObject(orga.name+"GridPointHider")
            if parent is not None :
                if self.helper.host == "dejavu":
                    self.helper.deleteObject(parent)
                else :
                    point = self.helper.getChilds(parent)
                    [self.helper.deleteObject(o) for o in point]
            
    def togleRecipeIngrInc(self,recipe, includeTog):
        if recipe :
            for ingr in recipe.ingredients:
                self.setVal(self.ingr_include[ingr.name],includeTog)  

    def toggleIngrIncExterior(self,*args):
        r =  self.histoVol.exteriorRecipe
        if r :        
            includeTog  = self.getVal(self.ingr_include["cytoplasm"])
            r =  self.histoVol.exteriorRecipe
            self.togleRecipeIngrInc(r,includeTog) 
            
    def toggleIngrInc(self,*args):
        r =  self.histoVol.exteriorRecipe
        if r :        
            includeTog  = self.getVal(self.ingr_include["cytoplasm"])
            r =  self.histoVol.exteriorRecipe
            self.togleRecipeIngrInc(r,includeTog)
        for o in self.histoVol.organelles:
            rs =  o.surfaceRecipe
            if rs :                
                includeTog  = self.getVal(self.ingr_include[o.name+"surface"])
                self.togleRecipeIngrInc(rs,includeTog)
            ri =  o.innerRecipe
            if ri :                
                includeTog  = self.getVal(self.ingr_include[o.name+"matrix"])
                self.togleRecipeIngrInc(ri,includeTog)
        
    def includeIngredient_cb(self,name,include,m,n,p,ingr=None):
        if ingr == None :
            ingr = self.histoVol.getIngrFromName(name)
        if ingr is not None :
            self.histoVol.includeIngredientRecipe(ingr, include)
            ingr.Set(molarity= float(m),
                         nbMol = int(n),
                        priority = float(p),)
            
    def popIngrs(self,*args):
        for wkey in self.ingr_include:
#            print ("pop ",wkey)
            if wkey.find("cytoplasm") != -1 :#or  wkey.find("surface") != -1 or wkey.find("matrix") != -1:
                continue
            c=False
            for o in self.histoVol.organelles:
                if wkey == o.name+"surface" or wkey == o.name+"matrix":
                    c=True
            if c : continue
            include = self.getVal(self.ingr_include[wkey])
            ingr = self.histoVol.getIngrFromName(wkey)            
#            print ("pop inc Ingr ",wkey,include,ingr," X")
            if ingr is not None :
                self.histoVol.includeIngredientRecipe(ingr, include)
                #change molarity as well 
                m=self.getVal(self.ingr_molarity[wkey])
                n=self.getVal(self.ingr_nMol[wkey])
                p=self.getVal(self.ingr_priority[wkey])
                ingr.Set(molarity= float(m),
                         nbMol = int(n),
                        priority = float(p),)
                        #packingMode="random")
#                ingr.molarity = self.getVal(self.ingr_molarity[wkey])
#                ingr.nbMol = self.getVal(self.ingr_nMol[wkey])
                
    def updateWidget(self):
#        print "updateWidget"
        for wname in self.Widget["options"]:
            if not hasattr(self.histoVol,wname):
                continue
            w = self.Widget["options"][wname]
            v = getattr(self.histoVol,wname)
#            print (wname,v)
            if wname == "gradients" :
                continue
            self.setVal(w,v)
        for o in self.histoVol.organelles:
            if o.name in self.Widget["organelles_mesh"]:
                self.setVal(self.Widget["organelles_mesh"][o.name],o.ref_obj)

    def toggleoverWOrganelle(self,*args):
        for o in self.histoVol.organelles:
            if o.name in self.Widget["organelles_overw"]:
                v = self.getVal(self.Widget["organelles_overw"][o.name])
                o.overwriteSurfacePts = v
                
    def updateOMesh_cb(self,oname,meshname,o=None):
        if o == None :
            for orga in self.histoVol.organelles:
                if orga.name == oname :
                    o = orga
        if o.ref_obj != meshname : 
            self.histoVol.setOrganelleMesh(o,meshname)
            self.afviewer.createOrganelMesh(o)#overwrite if already..user should backup        

    def applyWidgetValue(self):
        self.popIngrs()
        for wname in self.Widget["options"]:
            w = self.Widget["options"][wname]
            v = self.getVal(w)
            if wname == "gradients" :
                continue            
            setattr(self.histoVol,wname,v)
#            print (wname,v)
            self.setVal(w,v)
        self.histoVol.rejectionThreshold= 1000
        #check organelle mesh
        for o in self.histoVol.organelles:
            if o.name in self.Widget["organelles_mesh"]:
                meshname = self.getVal(self.Widget["organelles_mesh"][o.name])
                #compare to the one already there
                if o.ref_obj != meshname and meshname != "None" and meshname != "": 
                    self.histoVol.setOrganelleMesh(o,meshname)
                    self.afviewer.createOrganelMesh(o)#overwrite if already..user should backup
        #applyd option to all ingrdients
        #ingr_molarity
        #ingr_nMol

    def addOnePrevIngr(self,hostobj,recipe=None):
        ingr=None
        array =None
        if recipe is None :
            array = self.histoVol.molecules
        else :
            array = recipe.organelle().molecules
        
        if self.helper.getType(hostobj) == self.helper.EMPTY:
            if not self.getVal(self.Widget["options"]["prevIngr"]):
                self.setVal(self.Widget["options"]["prevIngr"],True)                    
            cc = self.helper.getChilds(hostobj)
            #use the first for creating the ingr
            ingr = self.afviewer.addIngredientFromGeom(self.helper.getName(hostobj),cc[0],recipe=recipe)
            #now use all of them to update the update the grid, and consider this ingredient done
#                    jtrans, rotMatj, ingr, ptInd = mingrs
            ptInd = 0
            for ci in cc :
                mo = self.helper.getTransformation(ci)
                m = self.helper.ToMat(mo)#.transpose()
                mws = m#.transpose()
                jtrans = self.helper.ToVec(self.helper.getTranslation(ci))
                rotMatj = mws[:]
                rotMatj[3][:3]*=0.0
                array.append([jtrans, rotMatj, ingr, ptInd])
                #if panda need to add a rigid body
                if self.getVal( self.Widget["options"]["placeMethod"] ).find("panda") != -1 :
                    rbnode = self.histoVol.addRB(ingr,jtrans, rotMatj,rtype=ingr.Type)
                    ingr.rbnode[ptInd] = rbnode
                    self.histoVol.rb_panda.append(rbnode)
                ptInd += 1

        else :
            ingr = self.afviewer.addIngredientFromGeom(self.helper.getName(hostobj),hostobj,recipe=recipe)
            mo = self.helper.getTransformation(hostobj)
            m = self.helper.ToMat(mo)#.transpose()
            mws = m#.transpose()
            jtrans = self.helper.ToVec(self.helper.getTranslation(hostobj))
            rotMatj = mws[:]
            rotMatj[3][:3]*=0.0
            ptInd = 0
            array.append([jtrans, rotMatj, ingr, ptInd]) 
            if self.getVal( self.Widget["options"]["placeMethod"] ).find("panda") != -1 :
                rbnode = self.histoVol.addRB(ingr,jtrans, rotMatj,rtype=ingr.Type)
                ingr.rbnode[ptInd] = rbnode
                self.histoVol.rb_panda.append(rbnode)
                print ("####RBNODE prev",rbnode, ingr.name)
        
        if ingr is not None:
            ingr.is_previous = True
            ingr.completion = 1.1
            ingr.molarity=0.0
            ingr.nbMol = 0
            ingr.overwrite_nbMol = 0
            ingr.overwrite_nbMol_value= 0                     
            ingr.counter = 999
            self.histoVol.ingr_added[ingr.name] = self.ingr_added[ingr.name]=ingr 
            #use mesh if any ?
            
    def checkAndGetPrevIngredient(self,*args):
        if self.getVal( self.Widget["options"]["placeMethod"] ).find("panda") != -1 :
            self.histoVol.setupPanda()
        p = self.helper.getObject(self.recipe+"_PreviousIngrExterior")
        childs = self.helper.getChilds(p)
        if childs is not None :
            for c in childs:
                #create an ingredient and add it ?
#                print (c, self.helper.getName(c),self.helper.getType(c))
                if self.guimode != "Simple" and self.guimode != "Intermediate":
                    self.addOnePrevIngr(c)
        for i,o in enumerate(self.histoVol.organelles):
            if o.surfaceRecipe :
                p = self.helper.getObject(self.recipe+"_PreviousIngr"+o.name+"_surface")
                childs = self.helper.getChilds(p)
                if childs is not None :
                    for c in childs:
                        #create an ingredient and add it ?
        #                print (c, self.helper.getName(c),self.helper.getType(c))
                        if self.guimode != "Simple" and self.guimode != "Intermediate":
                            self.addOnePrevIngr(c,recipe=o.surfaceRecipe)    
            if o.innerRecipe :   
                p = self.helper.getObject(self.recipe+"_PreviousIngr"+o.name+"_inner")
                childs = self.helper.getChilds(p)
                if childs is not None :
                    for c in childs:
                        #create an ingredient and add it ?
        #                print (c, self.helper.getName(c),self.helper.getType(c))
                        if self.guimode != "Simple" and self.guimode != "Intermediate":
                            self.addOnePrevIngr(c,recipe=o.innerRecipe)                          
        p = self.helper.getObject(self.recipe+"_PreviousOrga")
        childs = self.helper.getChilds(p)
        if childs is not None :
            for c in childs :
                #create and add an organelle to the system
                cname = self.helper.getName(c)
                vertices, faces, vnormals = self.histoVol.extractMeshComponent(c)
                found = False 
                o=None
                for o in self.histoVol.organelles :
                    if o.name == cname :
                        found = True
                        break
                if not found :
                    from AutoFill.Organelle import Organelle
                    o = Organelle(cname,vertices, faces, vnormals,ref_obj=cname)
                    self.histoVol.addOrganelle(o)
                    self.orga_added[cname]=o
#            else :
#                self.histoVol.setOrganelleMesh(o,cname)
#                self.afviewer.createOrganelMesh(o)#this will update the mesh

    def updateNBMOL(self,*args):
        bname= self.getVal(self.fbox_name)#bbox_name)
        if self.guimode == "Advanced" or self.guimode == "Debug":
            spacing = self.getVal(self.Widget["options"]["smallestProteinSize"])*1.1547#still dont know why * 1.1
        else :
            spacing = self.histoVol.smallestProteinSize
        self.popIngrs()
        self.updateNBMOL_cb(bname,spacing)
        for wkey in self.ingr_vol_nbmol:
            ingr = self.histoVol.getIngrFromName(wkey)
            if ingr is not None :
                self.setVal(self.ingr_vol_nbmol[wkey],"%d"%(ingr.vol_nbmol))
                
    def updateNBMOL_cb(self,bname,spacing):
        box = self.helper.getObject(bname)
        if box is None :
            box = self.helper.getObject("histoVolBB")
            if box is None :
                box=self.helper.getCurrentSelection()
                if len(box):
                    box = box[0]
                else:                
                    return
#        print box
        bb=self.afviewer.vi.getCornerPointCube(box)
        #update the molarity       
        self.histoVol.estimateVolume(bb, spacing)#update the value        
        #update the widget
        

    def fillGrid(self,*args):
            #need to prepare the fill
        self.applyWidgetValue()
        seed = self.getVal(self.seedId)
        bname= self.getVal(self.bbox_name)
        fbox_name = self.getVal(self.fbox_name)
        pFill = False
        pIngr = False
        fbuild = True
        doPts = False
        doSphere = False
        if self.guimode != "Simple":
            fbuild = self.getVal(self.Widget["options"]["forceBuild"])
        if self.guimode != "Simple" and self.guimode != "Intermediate":
            pFill = self.getVal(self.Widget["options"]["prevFill"]) 
            pIngr = self.getVal(self.Widget["options"]["prevIngr"])
            doPts = self.getVal(self.Widget["options"]["gridPts"])
        if self.guimode == "Debug":
            doSphere = self.getVal(self.Widget["options"]["spherePrimitive"]) 
        t1 = time()
        self.fillGrid_cb(seed,bname,fbox_name,pFill,pIngr,fbuild,
						doPts=doPts,doSphere=doSphere)
        t2 = time()
        self.setVal(self.LABELS["Time"] ,"Packed in %0.2f sec" % (t2-t1))
        return True
    
    def fillGrid_cb(self,seed,bname,fbox_name,pFill,pIngr,fbuild,doPts=False,
				doSphere=False):
#        if self.gridresultfile == None :
#            if self.recipe in AutoFill.RECIPES:
#                self.gridresultfile = AutoFill.RECIPES[self.recipe]["wrkdir"]+os.sep+"results"+os.sep+"fill_grid"
#            else : 
#                self.gridresultfile = self.histoVol.gridresultfile
#            print (self.recipe,AutoFill.RECIPES[self.recipe]["wrkdir"])
#            print (self.gridresultfile)
#        print "grid"
        if self.recipe in AutoFill.RECIPES and self.recipe_version in AutoFill.RECIPES[self.recipe]:
            self.gridresultfile = AutoFill.RECIPES[self.recipe][self.recipe_version]["wrkdir"]+os.sep+"results"+os.sep+"fill_grid"
            if not os.path.isdir(AutoFill.RECIPES[self.recipe][self.recipe_version]["wrkdir"]+os.sep+"results") :
                os.makedirs(AutoFill.RECIPES[self.recipe][self.recipe_version]["wrkdir"]+os.sep+"results")                
        else :
            self.gridresultfile =  self.grid_filename#or grid_filename?
 
        if not os.path.isfile(self.gridresultfile) and not fbuild :
            self.gridresultfile = None
            fbuid = True
        else :
            print ("gridFileIn ",self.gridresultfile)
        box = self.helper.getObject(bname)
        fbox_bb = None  #Graham Oct 20: Should we set fbox_bb = box here, then replace if fbox_name !=bname on next line?
        if fbox_name != bname :
            fbox = self.helper.getObject(fbox_name) 
            if fbox is not None :
                fbox_bb=self.afviewer.vi.getCornerPointCube(fbox)
                self.afviewer.fbox_bb=fbox_bb
        #overwrite the option for display sphere and point using checkbox ?        
        self.afviewer.doPoints = doPts#self.getVal(self.doPoints) #self.getVal(self.points_display) if maya
        self.afviewer.doSpheres = doSphere
        
        if box is None :
            box=self.helper.getCurrentSelection()[0]
#        print box
        bb=self.afviewer.vi.getCornerPointCube(box)
        print ("##############")
        print (bb,box,bname,fbox_name)
        buildGrid=None
        gridFileOut=None
        gridFileIn =None
        if pIngr :
            pFill = True
            self.checkAndGetPrevIngredient()
#            previngr.completion = 1.1 or 2 ?
#            previngr.nbMol = 0
#            previngr.counter = 0
#            previngr.histoVol = h
#            previngr.vi = afviewer.vi
#            afviewer.appendIngrInstance(previngr,sel = previngrInstance,bb=bb)
        if fbuild :
            gridFileOut=self.gridresultfile
        else :
            gridFileIn=self.gridresultfile
        if type(self.histoVol.innerGridMethod) != str :
            self.histoVol.innerGridMethod = "bhtree"
        print ("##############",fbuild,gridFileIn,gridFileOut)
        self.histoVol.buildGrid(boundingBox=bb,gridFileIn=gridFileIn,rebuild=fbuild ,
                      gridFileOut=gridFileOut,previousFill=pFill)
        #should use some cache for the box here,maybe compreto current one
#        self.afviewer.displayOrganellesPoints() # this is optional and should not be called here
#        print "fill"
        t1 = time()
        #if rigidbody need some code
        #file result !
        if self.histoVol.saveResult:
            self.histoVol.resultfile = self.getVal(self.Widget["options"]["resultfile"])
        self.histoVol.fill5(seedNum=int(seed),fbox = fbox_bb)
        t2 = time()
        print ('time to fill', t2-t1)

        
        self.afviewer.displayFill()
        print ('time to display', t2-t1)
        self.afviewer.displayIngrGrows()
        print ('time to display grow', t2-t1)
#        self.afviewer.vi.toggleDisplay(self.afviewer.bsph,False)
        if self.histoVol.runTimeDisplay :
            parentname =  self.recipe+"static"
            parent = self.helper.getObject(parentname)
            print (parentname,parent)
            if parent is not None :
                if self.helper.host=="dejavu":
                    self.helper.deleteObject(parent)
                else :
                    static = self.helper.getChilds(parent)
                    [self.helper.deleteObject(o) for o in static]
            parentname =  "staticMesh"
            parent = self.helper.getObject(parentname)
            print (parentname,parent)
            if parent is not None :
                if self.helper.host=="dejavu":
                    self.helper.deleteObject(parent)
                else :
                    static = self.helper.getChilds(parent)
                    [self.helper.deleteObject(o) for o in static]
        print ('time to display', time()-t2)
        #self.setVal(self.LABELS["Time"] ,"Time to fill = %0.5f sec" % (t2-t1))
        self.helper.resetProgressBar()
        return True    

    def AddGradient_cb(self,name):
#        print ("should add a gradient")                        
        if name not in self.gradients_ui:
            dlg = SubdialogGradient()
            dlg.setup(name=name,mode="Add",subdialog = True,histoVol=self.histoVol,parent=self)
            self.gradients_ui[name] = dlg
        self.drawSubDialog(self.gradients_ui[name],5555553)
        for iname in self.ingredients_ui:
            self.ingredients_ui[iname].addItemToPMenu(self.ingredients_ui[iname].Widget["options"]["gradients"],str(name))
            
    def AddGradient(self,*args):
#        print ("should add a gradient")
        self.drawInputQuestion(title="Add a Gradient",
                                       question="gradient name",callback=self.AddGradient_cb)

    def EditGradient(self,*args):
        gname = self.getVal(self.Widget["options"]["gradients"])     
#        print ("should edit a gradient : " + gname)
        if gname not in self.gradients_ui:
            dlg = SubdialogGradient()
            dlg.setup(mode="Edit",name=gname,subdialog = True,histoVol=self.histoVol,parent=self)
            self.gradients_ui[gname] = dlg
        self.drawSubDialog(self.gradients_ui[gname],55555543)
        self.gradients_ui[gname].updateWidgetValue()

    def setupResultFile_cb(self,filename):
        self.setVal(self.Widget["options"]["resultfile"],filename)
        self.histoVol.resultfile = filename
        
    def setupResultFile(self,*args):
        self.saveDialog(label="choose a file (result.apr)",callback=self.setupResultFile_cb)

    def savexml(self,filename):
        self.histoVol.save_asXML(filename)
        self.setupfile=filename
        
    def save(self,*args):
        filename= AutoFill.RECIPES[self.recipe]["setupfile"]
        if filename.find(".py") != -1 :
            self.saveDialog(label="choose a xml file",callback=self.savexml)
            return
        self.savexml(filename)
    
    def saveas(self,*args):
        self.saveDialog(label="choose a xml file",callback=self.savexml)
        
    def append2recipe(self,name,version="1.0"):
        n,v = name.split(" ")
        name = n
        version = v
        if name not in AutoFill.USER_RECIPES:
            AutoFill.USER_RECIPES[name]={}
            if version not in AutoFill.USER_RECIPES[name] :
                AutoFill.USER_RECIPES[name][version]={}
        AutoFill.USER_RECIPES[name][version]["setupfile"]=self.setupfile
        AutoFill.USER_RECIPES[name][version]["resultfile"]=self.getVal(self.Widget["options"]["resultfile"])
        AutoFill.USER_RECIPES[name][version]["wrkdir"]=os.path.abspath(self.getVal(self.Widget["options"]["resultfile"]))
        AutoFill.saveRecipeAvailable(AutoFill.USER_RECIPES,AutoFill.recipe_user_pref_file)
#        relem=AutoFill.XML.createElement("recipe")
#        relem.setAttribute("name",name)
#        AutoFill.XML.documentElement.appendChild(relem)
#        for l in ["setupfile","resultfile","wrkdir"]:
#            node = AutoFill.XML.createElement(l)
#            data = AutoFill.XML.createTextNode(AutoFill.RECIPES[name][version][l])
#            node.appendChild(data)
#            relem.appendChild(node)
#        f = open(AutoFill.recipe_user_pref_file,"w")        
#        AutoFill.XML.writexml(f, indent="\t", addindent="", newl="\n")
#        f.close()
        #update the pent menu, so no need to restart
        self.parent.addItemToPMenu(self.parent.WidgetViewer["menuscene"],name)
        self.parent.addItemToPMenu(self.parent.WidgetFiller["menuscene"],name)
        #also add to the version menu
        

    def appendtoRECIPES(self,*args):
        #for appending to recipes we need :name + ["setupfile","resultfile","wrkdir"]
        #ask for a name?
        self.drawInputQuestion(title="append",question="name and version of recipe. e.g myRecipe 1.0",callback=self.append2recipe)

class SubdialogIngredientViewer(uiadaptor):
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1

    def setup(self,**kw):
        self.subdialog = True
#        self.block = True
        self.scrolling = False
        self.ingr = kw["ingr"]
        if self.ingr is None :
            return
        self.histoVol = None
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            helperClass = upy.getHelperClass()
            self.helper = helperClass(kw)#problem for DejaVu 
        self.afviewer =None
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        self.listeRes=self.ingr.available_resolution#how can we check for available resolution
        self.setDefault()
        self.title = self.ingr.name+" display options"#+self.mol.name
        witdh=550
        self.h=130
        self.w=450
        self.SetTitle(self.title)
        self.initWidget()
        self.setupLayout()

    def initWidget(self):
        a="hfit"
        self.LABELS={}
        self.LABELS["obj"] = self._addElemt(name=self.ingr.name+"_lobj",label="Object (leave empty for using current selection)",width=100,alignement=a)
        self.LABELS["res"] = self._addElemt(name=self.ingr.name+"_lres",label="Resolution",width=100,alignement=a)
        self.ingr_resolution = self._addElemt(name=self.ingr.name+"VRes",
                    value=self.listeRes,alignement=a,
                    width=100,height=10,action=None,
                    variable=self.addVariable("int",0),
                    type="pullMenu",)
        self.ingr_basegeom = self._addElemt(name=self.ingr.name+"VGeom",
                    value=self.helper.getName(self.ingr.mesh_3d),
                    width=100,height=10,action=None,#alignement=a,#self.wc[6]
                    type="inputStr",variable=self.addVariable("str","")) 
        
        self.Apply_btn=self._addElemt(name="Apply",width=120,height=10,alignement=a,
                         action=self.applySetting,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        
        self.ResetToDefault_btn=self._addElemt(name="Reset",width=120,height=10,
                         action=self.resetToDefault,type="button",icon=None,alignement=a,
                                     variable=self.addVariable("int",0))
        
        self.Close_btn=self._addElemt(name="Apply and Close",width=120,height=10,alignement=a,
                         action=self.applySettingAndQuit,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        
        
    def setupLayout(self):
        self._layout = []
        self._layout.append([self.LABELS["obj"],self.ingr_basegeom])
        self._layout.append([self.LABELS["res"],self.ingr_resolution])
        self._layout.append([self.ResetToDefault_btn,])
        self._layout.append([self.Apply_btn,self.Close_btn])
        
    def toggleQuality(self,*args):
        print (args)

    def setDefault(self,*args):
        childs = self.helper.getChilds(self.ingr.mesh_3d)  
        if not len(childs):
            return
        instance = childs[0]
        imaster = self.helper.getMasterInstance(instance)
        if self.helper.host == "maya" or self.helper.host.find("blender") != -1:
            imaster = self.ingr.mesh
        self.ingr_basegeom_default = self.helper.getName(imaster)
        self.ingr_resolution_default = self.ingr.current_resolution
        
    def resetToDefault(self,*args):
        self.setVal(self.ingr_resolution,self.ingr_resolution_default) 
        self.setVal(self.ingr_basegeom,self.ingr_basegeom_default) 
        
    def applySetting(self,*args):
        res  = self.getVal(self.ingr_resolution) 
        geom = self.getVal(self.ingr_basegeom)
        #switch using autofill_viewer
        #compare geom to current
#        if geom != self.ingr_basegeom_default:
        if geom == "" :
            geom = self.helper.getCurrentSelection()[0]
        geom = self.helper.getObject(geom)
        if geom is not None:
            self.afviewer.replaceIngrMesh(self.ingr, geom)
        
    def applySettingAndQuit(self,*args):
        self.applySetting()
        self.close()
    
            
class SubdialogViewer(uiadaptor):
    def CreateLayout(self):
        self._createLayout()
        return 1
        
    def Command(self,*args):
        self._command(args)
        return 1

    def setup(self,**kw):
#        self.subdialog = True
        self.block = True
        self.recipe = kw["recipe"]
        self.recipe_version= kw["version"]
        self.title = self.recipe+" viewer v"+self.recipe_version#+self.mol.name
        witdh=550
        self.h=130
        self.w=350
        #first get the different module
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            helperClass = upy.getHelperClass()
            self.helper = helperClass(kw)#problem for DejaVu 
        if "afviewer" in kw :
            self.afviewer = kw["afviewer"]
        else :
            from AutoFill.autofill_viewer import AFViewer
            self.afviewer = AFViewer(ViewerType=self.host,helper=self.helper)
        if "histoVol" in kw :
            self.histoVol = kw["histoVol"]
        else :
            self.histoVol = None
        if self.histoVol is None :
            # create HistoVol
            from AutoFill.HistoVol import Environment
            self.histo = self.histoVol = Environment()        
        self.guimode = "Advanced"
        if "guimode" in kw :
            self.guimode = kw["guimode"]
        self.ingredients = None
        self.ingredients_ui = {}
        self.build = True
        self.build_grid = True
        self.result_filame = None
        if "build_grid" in kw :
            self.build_grid=kw["build_grid"]
        if "build" in kw :
            #need to build all ingredient instance (keep invisible)
            self.build = kw["build"]
        self._show = True
        if "show" in kw :
            #show all ingredient after build 
            self._show = kw["show"]
#        print ("setup",self.build,self.show)
        self.forceResult=False
        if "forceResult" in kw :
            self.forceResult=kw["forceResult"]
        if self.build:
            self.loadResult()
        if self._show :
            self.displayResult()
        
        #second setup the histoVol that will decribe the recipe from 2 files:
        #thi should actuallu go in the main AFGui as reused in Filler
        #- recipe : organelle and ingredient   : execfile or textfile to parse ?  
        #displayPreFill
        #- result file
        W=self.histoVol.longestIngrdientName()*5
        self.wc = [25,25,30,60,35,35,W]
        self.w=sum(self.wc)
        #define the widget here too
        self.SetTitle(self.title)
        self.initWidget()
        self.setupLayout_frame()

    def LoadNewResult_cb(self,filename):
        print (filename)
        self.histoVol.resultfile = filename
        self.clearRecipe()
        def resetIngr(ingr):
            ingr.isph=None
            ingr.icyl=None
            ingr.mesh_3d = None
        self.histoVol.loopThroughIngr(resetIngr)    
        self.afviewer.psph=None
        self.afviewer.displayPreFill()
        res = self.loadAPResult(filename)
        self.displayResult()
    
    def LoadNewResult(self,*args):
        self.fileDialog(label="choose a .apr file",callback=self.LoadNewResult_cb)

    def fetchGridResult(self,fname,name):
        try :
            import urllib.request as urllib# , urllib.parse, urllib.error
        except :
            import urllib
        urllib.urlcleanup()
        tmpFileName = AFwrkDir1+os.sep+"cache_results"+os.sep+name+"freePoints"
        if not os.path.isfile(tmpFileName) or self.forceResult :
            if checkURL(fname+"freePoints") :
                urllib.urlretrieve(fname+"freePoints", tmpFileName,reporthook=self.helper.reporthook)       
        tmpFileName = AFwrkDir1+os.sep+"cache_results"+os.sep+name+"grid"
        if not os.path.isfile(tmpFileName) or self.forceResult :
            if checkURL(fname+"grid") :
                urllib.urlretrieve(fname+"grid", tmpFileName,reporthook=self.helper.reporthook)

    def loadAPResult(self,fname):
        if os.path.isfile(fname):
            self.result_filame = fname
            #what about grid
            if self.build_grid :                     
                self.buildGrid()
            result,orgaresult,freePoint=self.histoVol.load(resultfilename=fname,restore_grid=self.build_grid)#load text ?#this will restore the grid  
            self.ingredients = self.histoVol.restore(result,orgaresult,freePoint)
            return True
        else :
            return False

    def loadResult(self,*args):
        if len(self.histoVol.ingr_result):# is not None :
            self.ingredients =self.histoVol.ingr_result
            return
        fname = AutoFill.RECIPES[self.recipe][self.recipe_version]["resultfile"]
        print ("loadResult ",fname,) 
        if fname.find("http") != -1 or fname.find("ftp") != -1:
            #http://grahamj.com/autofill/autoFillData/HIV/HIVresult_2_afr.afr
            name =   fname.split("/")[-1]
            tmpFileName = AFwrkDir1+os.sep+"cache_results"+os.sep+name
            if not os.path.isfile(tmpFileName) or self.forceResult :
                try :
                    import urllib.request as urllib# , urllib.parse, urllib.error
                except :
                    import urllib
                urllib.urlcleanup()
                if checkURL(fname) :
                    urllib.urlretrieve(fname, tmpFileName,reporthook=self.helper.reporthook)
                else :
                    tmpFileName = None
            if self.build_grid :
                self.fetchGridResult(fname,name)
            fname = tmpFileName
            #try to download the grid information?
        print ("loadResult ",fname,os.path.isfile(fname))
        res = self.loadAPResult(fname)
        return res
#            print (self.ingredients)

    def buildGrid(self,):
        bname = 'histoVolBB'
        box = self.helper.getObject(bname)
        if box is None :
            box=self.helper.getCurrentSelection()[0]
        bb=self.afviewer.vi.getCornerPointCube(box)
        buildGrid=None
        gridFileOut=None
        #the gridfile in ? shoud it be in the histoVol from the xml
        if self.recipe in AutoFill.RECIPES:
            gridFileIn=AutoFill.RECIPES[self.recipe][self.recipe_version]["wrkdir"]+os.sep+"results"+os.sep+"fill_grid"
        else :
            gridFileIn = self.grid_filename#or grid_filename?
#        1 ("gridFileIn check ",gridFileIn)
        if not os.path.isfile(gridFileIn):
            gridFileIn = None
        else :
            print ("gridFileIn ",gridFileIn)
        self.histoVol.buildGrid(boundingBox=bb,gridFileIn=gridFileIn, 
                                    gridFileOut=gridFileOut,previousFill=False)#this will build the grid , rebuild?   
        

    def displayResult(self,*args):
        self.afviewer.doPoints = False #self.getVal(self.points_display)
        self.afviewer.doSpheres = False
        self.afviewer.quality = 1 #lowest quality for sphere and cylinder
        self.afviewer.visibleMesh = True #mesh default visibility 
        self.afviewer.displayFill()
        self.afviewer.displayIngrGrows()
        
    def initWidget(self, ):
        self.menuorder = ["File",]
        self._menu = self.MENU_ID = {"File":
                      [self._addElemt(name="Load (.apr)",action=self.LoadNewResult),
                      ],#self.buttonLoadData
                       }
        if self.helper.host.find("blender") != -1:
            self.setupMenu()

        self.LABELS={}
        self.Widget={}
        self.Widget["clearIng"]=self._addElemt(name="Clear Ingredients",width=55,height=10,
                         action=self.clearIngr,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.Widget["clearRec"]=self._addElemt(name="Clear Recipe",width=40,height=10,
                         action=self.clearRecipe,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.Widget["remake"]=self._addElemt(name="reConstruct Recipe",width=60,height=10,
                         action=self.reMake,type="button",icon=None,
                                     variable=self.addVariable("int",0))

        self.listWidgetGuiMode ={}
        self.listWidgetName =  ["bbox",#0
                              "fbbox",#1
                              "packing_surface",#2
                              "rep_surfce",#3
                              "r_ingr",#4
                               "ingr_build",#5   
                               "ingr_display",#6
                               "ingr_display_primitive",#7
                               "ingr_resolution",#8                    
                              "ingr_name",#9
                              "ingr_options",#10
                              "points",#11
                              ]
        self.listWidget={}
        self.listWidgetGuiMode["Simple"]=[3,4,6,9]
        self.listWidgetGuiMode["Intermediate"]=[3,4,6,8,9]
        self.listWidgetGuiMode["Advanced"]= [0,1,2,3,4,5,6,8,9,10]
        self.listWidgetGuiMode["Debug"]=[0,1,2,3,4,5,6,7,8,9,10,11]  
        
        self.setupRecipeMenu()

    def oneRecipeColumnLabel(self,rname):
#        if self.helper.host.find("maya") == 1:
        hostWidth = 60
        if AutoFill.helper.host == 'maya':
            hostWidth = 30
        a="hfit"
        self.LABELS[rname+"columns"]={}
        self.LABELS[rname+"columns"]["column1"] = self._addElemt(name=self.recipe+rname+"columnLAbel1",label="Show    ",width=hostWidth,alignement=a)
        self.LABELS[rname+"columns"]["column2"] = self._addElemt(name=self.recipe+rname+"columnLAbel2",label="Build    ",width=hostWidth,alignement=a)
        self.LABELS[rname+"columns"]["column3"] = self._addElemt(name=self.recipe+rname+"columnLAbel3",label="Primitives",width=hostWidth,alignement=a)
#        self.LABELS[rname+"columns"]["column4"] = self._addElemt(name=self.recipe+rname+"columnLAbel4",label="Object",width=100,alignement=a)
#        self.LABELS[rname+"columns"]["column5"] = self._addElemt(name=self.recipe+rname+"columnLAbel5",label="Resolution",width=self.wc[4],alignement=a)
        self.LABELS[rname+"columns"]["column6"] = self._addElemt(name=self.recipe+rname+"columnLAbel6",label="Edit",width=hostWidth,alignement=a)
        self.LABELS[rname+"columns"]["column7"] = self._addElemt(name=self.recipe+rname+"columnLAbel7",label="Name",width=self.wc[6],alignement=a)

    def advancedIngr_viewerui(self,ingr):
#        print(ingr,ingr.name)
        if ingr.name not in self.ingredients_ui or self.ingredients_ui[ingr.name] is None :
            dlg = SubdialogIngredientViewer()
            dlg.setup(ingr=ingr,subdialog = True,afviewer=self.afviewer,histoVol=self.histoVol,helper=self.helper)
            self.ingredients_ui[ingr.name] = dlg
        self.drawSubDialog(self.ingredients_ui[ingr.name],555555553)
        self.ingredients_ui[ingr.name].resetToDefault()
#        self.ingredients_ui[ingr.name].updateWidget()

    def getFunctionForWidgetCallBack(self,ingr):
        aStr  = "def adveditIngr"+ingr.name+"(*args):\n\tgui.advancedIngr_viewerui("+ingr.name+")\n"#print("+ingr.name+","+ingr.name+".name)\n
        code_local = compile(aStr, '<string>', 'exec')
        l_dict={}#{ingr.name:ingr,"gui":self}
        g_dict = globals()
        g_dict[ingr.name] = ingr
        g_dict["gui"] = self
        exec(aStr,g_dict,l_dict)
        return l_dict["adveditIngr"+ingr.name]
        
    def getFunctionForWidgetCallBackDisplayBuild(self,ingr,options):
        fctString={}
        fctString["build"]="def buildIngr"+ingr.name+"(*args):\n"
        fctString["build"]+="\ttoggle = gui.getVal(gui.ingr_build['"+ingr.name+"'])\n"
        fctString["build"]+="\ttogglePrimitive = gui.getVal(gui.ingr_display_primitive['"+ingr.name+"'])\n"
        fctString["build"]+="\tif toggle :gui.buildIngredient('"+ingr.name+"',togglePrimitive)\n"
        fctString["build"]+="\telse :gui.delIngr('"+ingr.name+"')\n"
        fctString["show"]="def showIngr"+ingr.name+"(*args):\n"
        fctString["show"]+="\ttoggle = gui.getVal(gui.ingr_display['"+ingr.name+"'])\n"
        fctString["show"]+="\ttogglePrimitive = gui.getVal(gui.ingr_display_primitive['"+ingr.name+"'])\n"
        fctString["show"]+="\tif toggle :\n"
        fctString["show"]+="\t\tgui.setVal(gui.ingr_build['"+ingr.name+"'],toggle)\n"        
        fctString["show"]+="\t\tgui.buildIngredient('"+ingr.name+"',togglePrimitive)\n"
        fctString["show"]+="\tgui.helper.toggleDisplay(gui.afviewer.orgaToMasterGeom["+ingr.name+"],toggle)\n"
        fctString["primitive"]= "def primIngr"+ingr.name+"(*args):\n\tgui.toglleIngrPrimitive("+ingr.name+")\n"
        ldic={"build":"buildIngr"+ingr.name,
              "show":"showIngr"+ingr.name,
              "primitive":"primIngr"+ingr.name}
        aStr  = fctString[options]
        code_local = compile(aStr, '<string>', 'exec')
        l_dict={}#{ingr.name:ingr,"gui":self}
        g_dict = globals()
        g_dict[ingr.name] = ingr
        g_dict["gui"] = self
        exec(aStr,g_dict,l_dict)
        return l_dict[ldic[options]]
        
    def oneIngredientWidget(self,ingr):
        hostWidth = 60
        a="hfit"
        self.LABELS[ingr.name] = self._addElemt(name=ingr.name+"Label",label="%s"%ingr.name,width=self.wc[6],alignement=a)#,height=50)
        if AutoFill.helper.host == 'maya':
                hostWidth = 30
                self.LABELS[ingr.name] = self._addElemt(name=ingr.name+"Label",label="   %s"%ingr.name,width=self.wc[6],alignement=a)#,height=50)
        inr_cb = self.getFunctionForWidgetCallBackDisplayBuild(ingr,"build")
        self.ingr_build[ingr.name] = self._addElemt(name=ingr.name+'Build',
                    width=hostWidth,height=10,alignement=a,#self.wc[1]
                    action=inr_cb,type="checkbox",icon=None,#self.buildIngredients
                    variable=self.addVariable("int",1),value=self.build,label="----")
        inr_cb = self.getFunctionForWidgetCallBackDisplayBuild(ingr,"show")
        self.ingr_display[ingr.name] = self._addElemt(name=ingr.name+'Display',
                    width=hostWidth,height=10,alignement=a,#0
                    action=inr_cb,type="checkbox",icon=None,#self.toggleOrganelDisplay
                    variable=self.addVariable("int",1),value=self._show,label="----")
        hostWidth = 75
        if AutoFill.helper.host == 'maya':
            hostWidth = 30
        inr_cb = self.getFunctionForWidgetCallBackDisplayBuild(ingr,"primitive")
        self.ingr_display_primitive[ingr.name] = self._addElemt(name=ingr.name+'DisplayPrimitive',
                width=hostWidth,height=10,alignement=a,#2
                action=inr_cb,type="checkbox",icon=None,#self.toggleOrganelDisplayPrimitive
                variable=self.addVariable("int",0),value=0,label="----  ")
#        self.ingr_resolution[ingr.name] = self._addElemt(name=ingr.name+"Res",
#                    value=self.listeRes,alignement=a,
#                    width=self.wc[4],height=10,action=self.toggleQuality,
#                    variable=self.addVariable("int",0),
#                    type="pullMenu",)
#        self.ingr_basegeom[ingr.name] = self._addElemt(name=ingr.name+"Geom",
#                    value=self.helper.getName(ingr.mesh_3d),
#                    width=100,height=10,action=None,alignement=a,#self.wc[6]
#                    type="inputStr",variable=self.addVariable("str","")) 
        inr_cb = self.getFunctionForWidgetCallBack(ingr)
        hostWidth = 42
        if AutoFill.helper.host == 'maya':
            hostWidth = 25
        self.ingr_advanced[ingr.name] = self._addElemt(name="Edit",action=inr_cb,width=hostWidth,height=10,
                type="button",variable=self.addVariable("int",0),alignement=a) 
                
    def setupRecipeMenu(self,):
        #dynamic part!
        #cytoplasme?
        self.ingr_display={}
        self.ingr_display_primitive={}
        self.ingr_build={}
        self.ingr_resolution={}
        self.ingr_basegeom={}
        self.ingr_advanced={}
        self.organelles_display={}# if self.histoVol is None else [o.name for o in self.histoVol.organelles]
          
        #Ingredient        Build        Display: Geometry   SphereTree       Geometry Resolution  
#        self.LABELS["points"]=self._addElemt(name=self.recipe+"points",label="Points",width=120)
        self.listWidget["points"] = self.points_display=self._addElemt(name='Display Points '+self.recipe,width=80,height=10,
                                              action=self.togglePoints,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0,
                                                label="Show grid points")         
#        self.LABELS["bbox"]=self._addElemt(name=self.recipe+"bbox",label="BoundingBox",width=120)
        self.listWidget["bbox"] =self.bbox_display=self._addElemt(name='HBB'+self.recipe,width=80,height=10,
                                              action=self.toggleHistoVolDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0,
                                                label="Show grid boundary box")         

#        self.LABELS["fbbox"]=self._addElemt(name=self.recipe+"bbox",label="BoundingBox",width=120)
        self.listWidget["fbbox"] =self.fbbox_display=self._addElemt(name='FBB'+self.recipe,
                                                width=120,height=10,
                                              action=self.toggleHistoVolFBBDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0,
                                                label="Show fill region boundary box")         

        self.listeRes=["High","Med","Low"]
#        self.LABELS["cytoplasm"] = self._addElemt(name=self.recipe+"cyto",label="Exterior",width=120)#,height=50)
        self.listWidget["cytoplasm_ingr"] = self.organelles_display["cytoplasm"] = self._addElemt(name='Display exterior ingredients',
                                    width=120,height=10,
                                      action=self.toggleCytoplasmeDisplay,type="checkbox",icon=None,
                                      variable=self.addVariable("int",1),value=self._show,
                                        label = "Show all exterior ingredients")
        
        r =  self.histoVol.exteriorRecipe
        if r :
            self.oneRecipeColumnLabel("cytoplasm")
            for ingr in r.ingredients:
                self.oneIngredientWidget(ingr)
        
        for o in self.histoVol.organelles:
            self.LABELS[o.name] = self._addElemt(name="orgalabel",label="Organelle #%d:%s"%(o.number,o.name),width=120)#,height=50)
            self.organelles_display['%s_%s'%(o.name,"Mesh")] = self._addElemt(name='Display %s Geom'%(o.name),
                                                width=120,height=10,
                                              action=self.toggleOrganelGeomDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0,label="Display %s packing surface"%(o.name))
            toggle = 1
#            if o.representation is None:
#                toggle = 0
            self.organelles_display['%s_%s'%(o.name,"Rep")] = self._addElemt(name='Display %s Rep'%(o.name),width=135,height=10,
                                              action=self.toggleOrganelRepDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",toggle),value=toggle,
                                            label="Display %s surface representation"%(o.name))

            #for e in ["Matrix","Surface"]:
            self.organelles_display['%s_%s'%(o.name,"Matrix")] = self._addElemt(name='Display %s_%s Ingredients'%(o.name,"Matrix"),
                                            width=120,height=10,
                                              action=self.toggleOrganelMatrixDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=self._show,
                                                label = 'Show all %s %s Ingredients'%(o.name,"Matrix"))
            
            self.organelles_display['%s_%s'%(o.name,"Surface")] = self._addElemt(name='Display %s_%s Ingredients'%(o.name,"Surface"),
                                            width=120,height=10,
                                              action=self.toggleOrganelSurfaceDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=self._show,
                                                label = 'Show all %s %s Ingredients'%(o.name,"Surface"))

            #what about recipe...
            rs =  o.surfaceRecipe
            if rs :
                self.oneRecipeColumnLabel(o.name+"Surface")
                for ingr in rs.ingredients:
                    self.oneIngredientWidget(ingr)
                                
            ri =  o.innerRecipe
            if ri :
                self.oneRecipeColumnLabel(o.name+"Matrix")
                for ingr in ri.ingredients:
                    self.oneIngredientWidget(ingr)

        self.LABELS["lipids"]=self._addElemt(name=self.recipe+"lipids",label="Lipids",width=120)
        self.lipids_display=self._addElemt(name='Display Lipids',width=80,height=10,
                                              action=self.toggleLipidsDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=0)
        self.lipids_build=self._addElemt(name='Build Lipids',width=80,height=10,
                                              action=self.toggleLipidsDisplay,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=0)    
        self.lipids_resolution = self._addElemt(name="LipidRes",
                                    value=self.listeRes,
                                    width=120,height=10,action=self.toggleQuality,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)                                        
                                    
    def layout_oneRecipe(self,r,rname):
        elemFrame=[] 
        w =[self.LABELS[rname+"columns"]["column1"],
            self.LABELS[rname+"columns"]["column7"]]
        if self.guimode == "Intermediate":
            w =[self.LABELS[rname+"columns"]["column1"],
                self.LABELS[rname+"columns"]["column6"],
                self.LABELS[rname+"columns"]["column7"]]
        elif self.guimode == "Advanced" :
            w =[self.LABELS[rname+"columns"]["column1"],self.LABELS[rname+"columns"]["column2"],
#                self.LABELS[rname+"columns"]["column4"],self.LABELS[rname+"columns"]["column5"],
                self.LABELS[rname+"columns"]["column6"],self.LABELS[rname+"columns"]["column7"]]
        elif self.guimode == "Debug":
            w =[self.LABELS[rname+"columns"]["column1"],self.LABELS[rname+"columns"]["column2"],
                self.LABELS[rname+"columns"]["column3"],self.LABELS[rname+"columns"]["column6"],
                self.LABELS[rname+"columns"]["column7"]]
        elemFrame.append(w) 
        for ingr in r.ingredients:
            w =[self.ingr_display[ingr.name],self.LABELS[ingr.name]]
            if self.guimode == "Intermediate":
                w =[self.ingr_display[ingr.name],#self.ingr_resolution[ingr.name],
                    self.ingr_advanced[ingr.name],self.LABELS[ingr.name],]
            elif self.guimode == "Advanced" :
                w =[self.ingr_display[ingr.name],self.ingr_build[ingr.name],
#                    self.ingr_basegeom[ingr.name],self.ingr_resolution[ingr.name],
                    self.ingr_advanced[ingr.name],self.LABELS[ingr.name],]
            elif self.guimode == "Debug":
                w =[self.ingr_display[ingr.name],self.ingr_build[ingr.name],
                    self.ingr_display_primitive[ingr.name],#self.ingr_basegeom[ingr.name],self.ingr_resolution[ingr.name],
                    self.ingr_advanced[ingr.name],
                    self.LABELS[ingr.name],]
            elemFrame.append(w) 
        return elemFrame

    def setupLayout_frame(self):
        self._layout = []
        #depend on the guimode 
        self._layout.append([self.Widget["clearIng"],self.Widget["clearRec"],self.Widget["remake"]])
        if self.guimode == "Advanced" or self.guimode == "Debug":
            elemFrame=[]            
            elemFrame.append([self.bbox_display])
            elemFrame.append([self.fbbox_display])
            if self.guimode == "Debug" : 
                elemFrame.append([self.points_display])
            frame = self._addLayout(id=196,name="Advanced display options "+self.recipe,elems=elemFrame,collapse=False)#,type="tab")
            self._layout.append(frame)
        
        for o in self.histoVol.organelles:
            elemFrame=[]  
            elemFrame.append([self.organelles_display['%s_Rep'%(o.name)],])
            if self.guimode == "Advanced" or self.guimode == "Debug":
                elemFrame.append([self.organelles_display['%s_Mesh'%(o.name)],]) 
            rs =  o.surfaceRecipe
            if rs and len(rs.ingredients):
                elemFrame.append([self.organelles_display['%s_Surface'%(o.name)],])  #self.LABELS[o.name],                       
                elemFrame.extend(self.layout_oneRecipe(rs,o.name+"Surface"))
            
            ri =  o.innerRecipe
            if ri and len(ri.ingredients):
                elemFrame.append([self.organelles_display['%s_Matrix'%(o.name)],]) #self.LABELS[o.name],
                elemFrame.extend(self.layout_oneRecipe(ri,o.name+"Matrix"))        
            frame = self._addLayout(id=196,name="Compartment #%d: %s"%(o.number,o.name),
                                    elems=elemFrame,collapse=False,scrolling=True)#,type="tab")
            self._layout.append(frame)
                                     
        r =  self.histoVol.exteriorRecipe
        if r and len(r.ingredients):
            elemFrame=[]              
            elemFrame.append([self.organelles_display['cytoplasm']])
            elemFrame.extend(self.layout_oneRecipe(r,'cytoplasm'))           
            frame = self._addLayout(id=196,name="Cytoplasm "+self.recipe,
                                    elems=elemFrame,collapse=False,scrolling=True)#,type="tab")
            self._layout.append(frame)
        
        
        #self._layout.append([self.LABELS["lipids"],self.lipids_build,self.lipids_display,self.lipids_resolution])
        
        
    def delIngrPrim(self,ingr):
        if hasattr(ingr,"isph") : ingr.isph = None
        if hasattr(ingr,"icyl") : ingr.icyl = None
        orga = ingr.recipe().organelle()
        name = orga.name+"_Spheres_"+ingr.name.replace(" ","_")    
        parent = self.helper.getObject(name)
#        print (name,parent)            
        if parent is not None :
            instances = self.helper.getChilds(parent)
            if instances is not None :
                [self.helper.deleteObject(o) for o in instances]
            self.helper.deleteObject(parent)
        name = orga.name+"_Cylinders_"+ingr.name.replace(" ","_")    
        parent = self.helper.getObject(name)
#        print (name,parent)            
        if parent is not None :
            instances = self.helper.getChilds(parent)
            if instances is not None :
                [self.helper.deleteObject(o) for o in instances]
            self.helper.deleteObject(parent)
        
    def delIngr(self,ingr):
        if type(ingr) != str :
            ingrname = ingr.name
        else : 
            ingrname = ingr
            ingr = self.histoVol.getIngrFromName(ingrname)
        parentname =  "Meshs_"+ingrname.replace(" ","_")
        parent = self.helper.getObject(parentname)
        print (ingrname,parentname,parent)
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent) 
            else :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent) #is this dleete the child ?
        #need to do the same for cylinder
        if self.helper.host == "dejavu":
            ingr.ipoly.Set(instanceMatrices=[], visible=1)
            print "rest matrice", ingr.ipoly,ingr.mesh, ingr.mesh_3d
            ingr.mesh.Set(instanceMatrices=[], visible=1)
            print "rest matrice",ingr.mesh 
        else :
            ingr.ipoly = None
            del ingr.ipoly
        self.afviewer.addMasterIngr(ingr)#this will restore the correct parent
        if self.afviewer.doSpheres :
            orga = ingr.recipe().organelle()
            name = orga.name+"_Spheres_"+ingr.name.replace(" ","_")    
            parent = self.helper.getObject(name)
#            print (name,parent)            
            if parent is not None :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent)
            name = orga.name+"_Cylinders_"+ingr.name.replace(" ","_")    
            parent = self.helper.getObject(name)
#            print (name,parent)            
            if parent is not None :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent)
        if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
            #need to delete te spline and the data
            o = ingr.recipe().organelle()
            for i in range(ingr.nbCurve):
                name = o.name+str(i)+"snake_"+ingr.name.replace(" ","_")
                snake = self.helper.getObject(name)
                self.helper.deleteObject(snake)
            ingr.reset()
#        parentname =  "Meshs_"+ingrname.replace(" ","_")
#        parent = self.helper.getObject(parentname)
#        #print (parentname,parent)
#        if parent is not None :
#            instances = self.helper.getChilds(parent)
#            if instances is not None :
#                [self.helper.deleteObject(o) for o in instances]
#            self.helper.deleteObject(parent) #is this dleete the child ?
#        ingr.ipoly = None
#        del ingr.ipoly
#        #need to do the same for cylinder
##        if self.afviewer.doSpheres :
##            self.delIngrPrim(ingr)
#        if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
#            #need to delete te spline and the data
#            o = ingr.recipe().organelle()
#            for i in range(ingr.nbCurve):
#                name = o.name+str(i)+"snake_"+ingr.name.replace(" ","_")
#                snake = self.helper.getObject(name)
#                self.helper.deleteObject(snake)
#            ingr.reset()
                
    def clearIngr(self,*args):
        """ will clear all ingredients instances but leave base parent hierarchie intact"""
        self.histoVol.loopThroughIngr(self.delIngr)    
#        [self.delIngr(ingrname) for ingrname in self.ingredients]
    
    def clearRecipe(self,*args):
        """ will clear everything related to self.recipe"""
        parent = self.helper.getObject(self.recipe)
        if parent is not None :
            if self.helper.host == "dejavu":
                self.helper.deleteObject(parent) 
            else :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent)

    def reMake (self,*args):
        """ same effect as AFGui make ? but only curren ? I think we 
        should merge Clear Recipe and reMAke in a Reset button"""
        self.clearRecipe()
        def resetIngr(ingr):
            ingr.isph=None
            ingr.icyl=None
            ingr.mesh_3d = None
        self.histoVol.loopThroughIngr(resetIngr)    
        self.afviewer.psph=None
        self.afviewer.displayPreFill()
        self.displayResult()

    def Set(self,**kw):
        if "build" in kw :
            #need to build all ingredient instance (keep invisible)
            self.build = kw["build"]
        if "show" in kw :
            #show all ingredient after build 
            self._show = kw["show"]

    def togglePoints(self,*args):
        doit = self.afviewer.doPoints= self.getVal(self.points_display)
        self.togglePoints_cb(doit)
        
    def togglePoints_cb(self,doit):
        self.afviewer.doPoints = doit
        if self.afviewer.doPoints:
            if not self.build_grid : #need to build the grid
                self.buildGrid()
                freePoint = self.histoVol.loadFreePoint(self.result_filame)
                self.histoVol.restoreGridFromFile(self.result_filame+"grid")#restore grid distance and ptId
                self.histoVol.restoreFreePoints(freePoints)
            self.afviewer.displayOrganellesPoints()
            self.afviewer.displayFreePoints()
        
    def toggleLipidsDisplay(self,*args):
        pass
 
    def toggleHistoVolFBBDisplay(self,*args):
        if self.histoVol is None :
            return
        toggle = self.getVal(self.fbbox_display)
        name = 'fillBB'
        b=self.helper.getObject(name)#or self.histoVol.histoBox
        self.helper.toggleDisplay(b,toggle)
   
    def toggleHistoVolDisplay(self,*args):
        if self.histoVol is None :
            return
        toggle = self.getVal(self.bbox_display)
        name = 'histoVolBB'
        b=self.helper.getObject(name)#or self.histoVol.histoBox
        self.helper.toggleDisplay(b,toggle)

    def toggleOrganelGeomDisplay(self,*args):
        #too slow for blender...
        #check if they are build prior to toggle the display.
        for o in self.histoVol.organelles:
            toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,"Mesh")])                
            self.helper.toggleDisplay('%s_%s'%(o.name,"Mesh"),toggle)

    def toggleOrganelRepDisplay(self,*args):
        #too slow for blender...
        #check if they are build prior to toggle the display.
        for o in self.histoVol.organelles:
            if o.representation is not None :
                e="Rep"
                toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,e)])                
                self.helper.toggleDisplay('%s_%s'%(o.name,e),toggle)

    def toggleOrganelSurfaceDisplay(self,*args):
        for o in self.histoVol.organelles:
            rs =  o.surfaceRecipe
            if rs :
                toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,"Surface")])
                for ingr in rs.ingredients:
                    self.setVal(self.ingr_display[ingr.name],toggle)
                    togglePrimitive = self.getVal(self.ingr_display_primitive[ingr.name])
                    if (toggle) : 
                        self.setVal(self.ingr_build[ingr.name],toggle)
                        self.buildIngredient(ingr.name,togglePrimitive)
                    self.helper.toggleDisplay(self.afviewer.orgaToMasterGeom[ingr],toggle)

    def toggleOrganelMatrixDisplay(self,*args):
        for o in self.histoVol.organelles:
            ri =  o.innerRecipe
            if ri :
                toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,"Matrix")])
                for ingr in ri.ingredients:
                    self.setVal(self.ingr_display[ingr.name],toggle)
                    togglePrimitive = self.getVal(self.ingr_display_primitive[ingr.name])
                    if (toggle) : 
                        self.setVal(self.ingr_build[ingr.name],toggle)
                        self.buildIngredient(ingr.name,togglePrimitive)
                    self.helper.toggleDisplay(self.afviewer.orgaToMasterGeom[ingr],toggle) 
                    
    def toggleCytoplasmeDisplay(self,*args):
        toggle = self.getVal(self.organelles_display['cytoplasm'])
#        self.helper.toggleDisplay(self.recipe+"_cytoplasm",toggle)
        r =  self.histoVol.exteriorRecipe
        if r :
            self.helper.toggleDisplay(self.recipe+"_cytoplasm",toggle,child=False)
            for ingr in r.ingredients:
                self.setVal(self.ingr_display[ingr.name],toggle)
                togglePrimitive = self.getVal(self.ingr_display_primitive[ingr.name])
                if (toggle) : 
                    self.setVal(self.ingr_build[ingr.name],toggle)
                    self.buildIngredient(ingr.name,togglePrimitive)
                self.helper.toggleDisplay(self.afviewer.orgaToMasterGeom[ingr],toggle) 
                
    def toggleOrganelDisplay(self,*args):
        #too slow for blender...
        #check if they are build prior to toggle the display.
        for o in self.histoVol.organelles:
#            for e in ["Rep","Mesh","Matrix","Surface"]:
#                toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,e)])
#                self.helper.toggleDisplay('%s_%s'%(o.name,e),toggle,child=False)#blender go recursif
            rs =  o.surfaceRecipe
            if rs :
                toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,"Surface")])
                for ingr in rs.ingredients:
                    self.setVal(self.ingr_display[ingr.name],toggle)
                    togglePrimitive = self.getVal(self.ingr_display_primitive[ingr.name])
                    if (toggle) : 
                        self.setVal(self.ingr_build[ingr.name],toggle)
                        self.buildIngredient(ingr.name,togglePrimitive)
                    self.helper.toggleDisplay(self.afviewer.orgaToMasterGeom[ingr],toggle)
            ri =  o.innerRecipe
            if ri :
                toggle = self.getVal(self.organelles_display['%s_%s'%(o.name,"Matrix")])
                for ingr in ri.ingredients:
                    print (ingr,toggle,self.afviewer.orgaToMasterGeom[ingr])
                    self.setVal(self.ingr_display[ingr.name],toggle)
                    togglePrimitive = self.getVal(self.ingr_display_primitive[ingr.name])
                    if (toggle) : 
                        self.setVal(self.ingr_build[ingr.name],toggle)
                        self.buildIngredient(ingr.name,togglePrimitive)
                    self.helper.toggleDisplay(self.afviewer.orgaToMasterGeom[ingr],toggle) 
        toggle = self.getVal(self.organelles_display['cytoplasm'])
#        self.helper.toggleDisplay(self.recipe+"_cytoplasm",toggle)
        r =  self.histoVol.exteriorRecipe
        if r :
            self.helper.toggleDisplay(self.recipe+"_cytoplasm",toggle,child=False)
            for ingr in r.ingredients:
                self.setVal(self.ingr_display[ingr.name],toggle)
                togglePrimitive = self.getVal(self.ingr_display_primitive[ingr.name])
                if (toggle) : 
                    self.setVal(self.ingr_build[ingr.name],toggle)
                    self.buildIngredient(ingr.name,togglePrimitive)
                self.helper.toggleDisplay(self.afviewer.orgaToMasterGeom[ingr],toggle) 

    def toglleIngrPrimitive(self,ingr):
        toggle = self.getVal(self.ingr_display_primitive[ingr.name])
        if toggle: #build and display
            self.afviewer.displayIngrResults(ingr,doSphere=True,doMesh=False)
        else :
            #delete it
            self.delIngrPrim(ingr)
            
    def toggleOrganelDisplayPrimitive(self,*args):
        #display the ingrdients primitive
        self.histoVol.loopThroughIngr(self.toglleIngrPrimitive)

    def buildIngredients(self,*args):
        """build check ingreients"""
        listeIngr=[]        
        for wkey in self.ingr_build:
            toggle = self.getVal(self.ingr_build[wkey])
            togglePrimitive = self.getVal(self.ingr_display_primitive[wkey])
            if toggle : #need to build
                self.buildIngredient(wkey,togglePrimitive)
            else : 
                self.delIngr(wkey) #should we delete it ?
                
    def buildIngredient(self,ingrname,primitive):
       #for this we need to change the way result are represented in AF.
       #modify the restore function to build a dictionary ingrname:[pos,rot, ]
#       print (ingrname)
        if self.ingredients is None :
            self.loadResult()
        if ingrname in self.ingredients :
#            print ("build",ingrname)
            ingr,pos,rot,matrices = self.ingredients[ingrname]
#            print "pos",len(matrices)
            #self.afviewer.displayIngrResults(ingr,doSphere=False,doMesh=True)
#            self.afviewer.displayInstancesIngredient(ingr, matrices)
            self.afviewer.displayIngrResults(ingr,doSphere=primitive,doMesh=True)
    
    def toggleQuality(self,*args):
        print (args)
        

class AFGui(uiadaptor):
    #savedialog dont work
    __url__=["http://autopack.org",
             "http://autopack.org/documentation/autofill-api",
             "http://mgldev.scripps.edu/projects/AF/update_notes.txt"
             #  "https://sites.google.com/site/autofill21/",
             #  "https://sites.google.com/site/autofill21/documentation/autofill-api",
    ]
    def setup(self,id=None,rep="",host="",**kw):
        self.title = "autoPACK"#+" "+AutoFill.__version__#+self.mol.name
        #witdh=350
        self.h=130
        self.w=250
        if id is not None :
            id=id
        else:
            id = self.bid
        self.id = id
        #define the widget here too
        vi = None
        if "vi" in kw :
            vi = kw["vi"]
        self.helper = upy.getHelperClass()(vi=vi)
        AutoFill.helper = self.helper
        self.histoVol={}
        self.recipe_available = AutoFill.RECIPES
        self.SetTitle(self.title)
        self.initWidget()
        self.setupLayout()
        self._store('af',{"afui":self})
        self.current_recipe = ""
        self.newAFv=""
        self.newuPyv=""
        self.register = None
        if self.host != 'qt': # self.host != 'blender25' and
            self.checkRegistration()
        self.server = "http://autofill.googlecode.com/svn/data/"
        #pop up message ?
        self.onlinMessage()
        
    def Set(self,name, **kw):
#        print ("SET",name)
        if "helper" in kw :
            self.helper = kw["helper"]
        else :
            helperClass = upy.getHelperClass()
            self.helper = helperClass(kw)
        if "histoVol" in kw :
            self.histoVol[name] = kw["histoVol"]
            if "afviewer" in kw :
                self.histoVol[name].afviewer = kw["afviewer"]
            else :
                from AutoFill.autofill_viewer import AFViewer
                self.histoVol[name].afviewer = AFViewer(ViewerType=self.host,helper=self.helper)
        else :
            self.histoVol[name] = None
        if "bbox" in kw : 
            self.bbox = kw["bbox"]

    def compareMessage(self,messag):
        draw = False
        if messag != AutoFill.messag:
            f = open(AutoFill.afdir+os.sep+"__init__.py","r")
            text = f.read()
            f.close()
            text = text.replace("messag = '''"+str(AutoFill.messag)+"'''","messag = '''"+str(messag)+"'''")
            f = open(AutoFill.afdir+os.sep+"__init__.py","w")        
            f.write(text)        
            f.close()
            draw = True
        AutoFill.messag = messag
        return draw
        
    def onlinMessage(self,*args):
        URI="http://autofill.googlecode.com/svn/data/message"
        urllib.urlcleanup()
        if checkURL(URI) :
            response = urllib.urlopen(URI)
            html = response.read().decode("utf-8", "strict") 
            if html !='' :
                if self.compareMessage(html):
                    self.drawMessage(title='Message',
                                     message=html)
        
        
    def isRegistred(self,*args):
        #from user import home#this dont work with python3
#        from os.path import expanduser
#        home = expanduser("~")
        regfile = os.path.join(AFwrkDir1,  'AP_registration')
        if not os.path.exists(regfile):        
            return False
        return True
        
    def checkRegistration(self):
        #after 3 use ask for registration or discard epmv
        if not self.isRegistred():
            self.drawRegisterUI()
            if not self.isRegistred():
                return False
        return True

    def drawRegisterUI(self,*args):
        if self.register is None:
            self.register = Register_User_ui()
            self.register.setup(use="AP",where=AFwrkDir1)
        self.drawSubDialog(self.register,255555643)
        
    def initWidget(self):
        #define button and other stuff here
        #need widget for viewer, filler, builder
        self.menuorder = ["Help"]#,"Edit"]
        self._menu = self.MENU_ID = {"Help":
                      [self._addElemt(name="Check for stable updates",action=self.stdCheckUpdate),
                       self._addElemt(name="Check for latest development updates",action=self.devCheckUpdate),
                       self._addElemt(name="Get latest recipes list",action=self.UpdateRecipesList),
                       self._addElemt(name="View updates notes",action=self.visitUpdate),
                      self._addElemt(name="Visit autoPACK website",action=self.visiteAFweb),#self.buttonLoad},
                      self._addElemt(name="Visit autoPACK API documentation",action=self.visiteAFwebAPI),
                      self._addElemt(name="About",action=self.drawAbout),
                      self._addElemt(name="Close autoPACK",action=self.close),
                      ],
#                      "Edit":
#                          [
#                          self._addElemt(name="Clear all caches",action=self.clearCaches),
#                          ]
                          }
        if not self.isRegistred():
            self.MENU_ID["Help"].append(self._addElemt(name="Register",
                                                action=self.drawRegisterUI))
        if self.helper.host.find("blender") != -1:
            self.setupMenu()

        self.LABELGMODE  = self._addElemt(label="GUI mode",width=100, height=5)
        self.LABELSV = self._addElemt(label="Welcome to autoPACK v"+AutoFill.__version__,width=100, height=5)
        self.list_gmode = ["Simple","Intermediate","Advanced","Debug"]
        self.gmode = self._addElemt(name="guimode",
                                    value=self.list_gmode,
                                    width=180,height=10,action=None,
                                    variable=self.addVariable("int",3),
                                    type="pullMenu",)
        self.forceRecipeAvailable = self._addElemt(name="forceRecipeAvailable",
                                            label="Check for latest recipes at startup (takes effect after host restart)",
                                            width=150,height=10,
                                              action=self.toggleCheckLatestRecipe,type="checkbox",icon=None,
                                              variable=self.addVariable("int",int(AutoFill.checkAtstartup)),value=AutoFill.checkAtstartup)
        if self.host.find("blender") != -1 :
            self.use_dupli_vert = self._addElemt(name="useDupli",
                                            label="use vertex instance vs individual instance (only Blender for now)",
                                            width=150,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=True)
        
        self.initWidgetViewer()
        self.initWidgetFiller()
        self.initWidgetBuilder()
        
    def initWidgetViewer(self, ):
        self.WidgetViewer={}
        self.WidgetViewer["labelLoad"] = self._addElemt(name="labelLoad",
                                                label="Load an autoPACK/cellPACK recipe for:",width=120,height=10)
        self.ListCurrentSet = list(self.recipe_available.keys())#["HIV_x_x","Synaptic_Vesicle","Cytoplasme","SimpleSpheres"]["HIV","BloodSerum","GenericCytoplasm"]#,"SynapticVesicle"]#
        self.ListCurrentSet.append("Load")
        self.ListCurrentSet.append("Fetch")
        
        self.WidgetViewer["labelRversion"]=self._addElemt(name="labelRversion",
                                                label="Recipe version",width=120,height=10)
        self.WidgetViewer["recipeversion"] = self._addElemt(name="rversion",
                                    value=list(self.recipe_available["HIV"].keys()),
                                    width=180,height=10,action=self.setRVersion,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)
        
        self.WidgetViewer["menuscene"] = self._addElemt(name="avaset",
                                    value=self.ListCurrentSet,
                                    width=180,height=10,action=self.updateRVersion,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)
                                    
        self.WidgetViewer["BuildUponLoad"] = self._addElemt(name="buildViewer",label="Build ingredient geometries upon loading",width=100,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=1)
        self.WidgetViewer["ShowUponLoad"] = self._addElemt(name="showViewer",label="Show ALL ingredient instances upon loading (may slow viewport)",width=530,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=1)
        self.WidgetViewer["BuildGrid"] = self._addElemt(name="buildGridViewer",label="(Re)Build the grid  upon loading (may slow the loading)",width=530,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0)

        self.WidgetViewer["forceFetch"] = self._addElemt(name="forceFetch",label="Force downloading the ingredients geometries",width=530,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0)
        self.WidgetViewer["forceFetchResult"] = self._addElemt(name="forceFetchResult",label="Force downloading the latest result",width=530,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0)
        self.WidgetViewer["forceFetchRecipe"] = self._addElemt(name="forceFetchRecipe",label="Force downloading the latest recipe",width=530,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=1)
                                              
        self.WidgetViewer["make"]=self._addElemt(name="Construct",width=70,height=10,
                         action=self.drawSubsetViewer,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.WidgetViewer["labelmake"] = self._addElemt(name="labelmake",
                                                label="selected recipe scene into the current document",width=120,height=10)
                                                
        
    def initWidgetFiller(self, ):
        self.WidgetFiller={}
        self.WidgetFiller["labelLoad"] = self._addElemt(name="labelLoadF",
                                                label="Build an autoPACK/cellPACK recipe for:",width=120)
        self.ListCurrentSetFiller = list(self.recipe_available.keys())#["HIV_x_x","Synaptic_Vesicle","Cytoplasme","SimpleSpheres"]
        self.ListCurrentSetFiller.append("Load")
        self.ListCurrentSetFiller.append("Custom")
        
        self.WidgetFiller["labelRversion"]=self._addElemt(name="labelRversion",
                                                label="Recipe version",width=120,height=10)
        self.WidgetFiller["recipeversion"] = self._addElemt(name="rversion",
                                    value=list(self.recipe_available["HIV"].keys()),
                                    width=180,height=10,action=self.setRVersion,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)
        
        self.WidgetFiller["menuscene"] = self._addElemt(name="avasetf",
                                    value=self.ListCurrentSetFiller,
                                    width=200,height=10,action=self.updateRVersionFiller,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)
                                    
        self.WidgetFiller["Startf"]=self._addElemt(name="Start",width=60,height=10,
                         action=self.drawSubsetFiller,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.WidgetFiller["labelstart"] = self._addElemt(name="labelstart",
                                                label="the selected recipe's scene constructor",width=120)
        self.WidgetFiller["forceFetch"] = self._addElemt(name="forceFetchFiller",label="Force downloading the ingredients geometries",width=530,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",0),value=0)

    def initWidgetBuilder(self, ):
        self.WidgetBuilder={}
        self.WidgetBuilder["CreateIngr"]=self._addElemt(name="SphereIngredient",width=100,height=10,
                         action=self.drawSubsetBuilder,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.WidgetBuilder["CreateRec"]=self._addElemt(name="CreateRec",label="Create new Recipe",width=100,height=10,
                         action=self.drawSubsetBuilder,type="button",icon=None,
                                     variable=self.addVariable("int",0))

    def setupLayout(self):
        typeframe = "tab"
        if self.helper.host.find("blender") != -1:
            typeframe="frame"
        #form layout for each SS types ?
        self._layout = []
        elemFrame=[]
        elemFrame.append([self.WidgetViewer["labelLoad"],self.WidgetViewer["menuscene"]])
        elemFrame.append([self.WidgetViewer["labelRversion"],self.WidgetViewer["recipeversion"]])
        elemFrame.append([self.WidgetViewer["BuildUponLoad"],])
        elemFrame.append([self.WidgetViewer["ShowUponLoad"],])
        elemFrame.append([self.WidgetViewer["BuildGrid"],])
        elemFrame.append([self.WidgetViewer["forceFetch"],])
        elemFrame.append([self.WidgetViewer["forceFetchResult"],])
        #elemFrame.append([self.WidgetViewer["forceFetchRecipe"],])
        
        elemFrame.append([self.WidgetViewer["make"],self.WidgetViewer["labelmake"],])
        frame = self._addLayout(id=196,name="Viewer",elems=elemFrame,collapse=True,type=typeframe)#tab is risky in DejaVu
        self._layout.append(frame)

        elemFrame=[]
        elemFrame.append([self.WidgetFiller["labelLoad"],self.WidgetFiller["menuscene"]])
        elemFrame.append([self.WidgetFiller["labelRversion"],self.WidgetFiller["recipeversion"]])
        elemFrame.append([self.WidgetFiller["forceFetch"],])
        elemFrame.append([self.WidgetFiller["Startf"],self.WidgetFiller["labelstart"],])
        frame = self._addLayout(id=196,name="Filler",elems=elemFrame,collapse=True,type=typeframe)#tab is risky in DejaVu
        #if self.helper.host.find("blender") == -1:
        self._layout.append(frame)

        elemFrame=[]
        elemFrame.append([self.WidgetBuilder["CreateIngr"],])
        elemFrame.append([self.WidgetBuilder["CreateRec"],])
        frame = self._addLayout(id=196,name="Builder",elems=elemFrame,collapse=True,type=typeframe)#tab is risky in DejaVu
        #if self.helper.host.find("blender") == -1:
        self._layout.append(frame)
        
        elemFrame=[]
        elemFrame.append([self.LABELGMODE,self.gmode])
        elemFrame.append([self.forceRecipeAvailable])
        elemFrame.append([self.WidgetViewer["forceFetchRecipe"]])
        if self.host.find("blender") != -1 :
            elemFrame.append([self.use_dupli_vert])
        elemFrame.append([self.LABELSV])
        frame = self._addLayout(id=196,name="Options",elems=elemFrame,collapse=True,type=typeframe)#tab is risky in DejaVu
        self._layout.append(frame)



    def UpdateRecipesList(self,*args):
        AutoFill.checkRecipeAvailable()
        AutoFill.updateRecipAvailable(AutoFill.recipe_web_pref_file)
        AutoFill.updateRecipAvailable(AutoFill.recipe_user_pref_file)
        #update menu
        self.recipe_available = AutoFill.RECIPES
        liste_recipe = list(AutoFill.RECIPES.keys())
        self.ListCurrentSet = list(liste_recipe)#["HIV_x_x","Synaptic_Vesicle","Cytoplasme","SimpleSpheres"]["HIV","BloodSerum","GenericCytoplasm"]#,"SynapticVesicle"]#
#        self.ListCurrentSet.sort()
#        self.ListCurrentSet.append("Load")
#        self.ListCurrentSet.append("Fetch")
        self.resetPMenu(self.WidgetViewer["menuscene"] )
        [self.addItemToPMenu(self.WidgetViewer["menuscene"],n) for n in self.ListCurrentSet ]
        self.updateRVersion()
        
        self.ListCurrentSetFiller = list(liste_recipe)#["HIV_x_x","Synaptic_Vesicle","Cytoplasme","SimpleSpheres"]
        self.ListCurrentSetFiller.append("Load")
        self.ListCurrentSetFiller.append("Custom")
#        self.ListCurrentSet.sort()
        self.resetPMenu(self.WidgetFiller["menuscene"] )
        [self.addItemToPMenu(self.WidgetFiller["menuscene"],n) for n in self.ListCurrentSetFiller]
        self.updateRVersionFiller()
        

    def toggleCheckLatestRecipe_cb(self,toggle):
        f = open(AutoFill.afdir+os.sep+"__init__.py","r")
        text = f.read()
        f.close()
        text = text.replace("checkAtstartup = False","checkAtstartup = "+str(toggle))
        f = open(AutoFill.afdir+os.sep+"__init__.py","w")        
        f.write(text)        
        f.close()
        AutoFill.checkAtstartup = toggle

    def toggleCheckLatestRecipe(self,*args):
        toggle = self.getVal(self.forceRecipeAvailable)
        self.toggleCheckLatestRecipe_cb(toggle)
        
    def clearCaches(self,*args):
        #can't work if file are open!
        
        wkr = os.path.abspath(AFwrkDir1)
        #in the preefined working directory
        cache = wkr+os.sep+"cache_results"
        cachei = wkr+os.sep+"cache_ingredients"
        cache_sphere = wkr+os.sep+"cache_ingredients"+os.sep+"sphereTree"
        cacheo = wkr+os.sep+"cache_organelles"
        for d in [cache_sphere,cachei,cache,cacheo]:            
            shutil.rmtree(d)
            os.makedirs(d)

    def checkForUpdate(self,upyv,afv):
        #check on web if update available
        #return boolean for update_PMV,update_ePMV and update_pyubics
        self.newAFv=""
        self.newuPyv=""        
        upAF=False
        upupy=False
        self.update_notes = ""
        #need version
        URI="http://mgldev.scripps.edu/projects/AF/update_notes.txt"
        tmpFileName = AFwrkDir1+os.sep+"update_notes.txt"
#        if not os.path.isfile(tmpFileName):
        urllib.urlcleanup()
        if checkURL(URI) :
            urllib.urlretrieve(URI, tmpFileName)#,reporthook=self.helper.reporthook)
            #geturl(URI, tmpFileName)
        else :
            return upAF,upupy
        f= open(tmpFileName,"r")
        lines = f.readlines()
        f.close()
        #get the version
        n=len(lines)
        for i,l in enumerate(lines) :
            s=l.strip().split(":")
#            print(s,self.PMVv,self.current_version,self.upyv)
            if s[0] == "autoFill":  # Can this become "autoPACK"?
                self.newAFv = s[1]
                if s[1] != afv:
                    upAF= True
                    print (s[1],afv)
            if s[0] == "upy":
                self.newuPyv = s[1]
                if s[1] != upyv:
                    print(s[1],upyv)
                    upupy = True
            if s[0] == "Notes":
#                self.update_notes = lines[i:]
#                break
                for j in range(i+1,n):
                    #print j,lines[j]
                    self.update_notes+=lines[j]
                break
            print(self.update_notes)
        os.remove(tmpFileName)
        return upAF,upupy        

    def update_upy(self,backup=False):
        import zipfile
        p = upy.__path__[0]+os.sep
        os.chdir(p)
        os.chdir("../")
        patchpath = os.path.abspath(os.curdir)
#        patchpath = upy.__path__[0]+os.sep+".."+os.sep
        URI="http://mgldev.scripps.edu/projects/ePMV/updates/upy.zip"#or zip ????
        tmpFileName = patchpath+os.sep+"upy.zip"
#        print tmpFileName
#        if not os.path.isfile(tmpFileName):
        urllib.urlcleanup()
        if checkURL(URI) :
            urllib.urlretrieve(URI, tmpFileName,reporthook=self.helper.reporthook)
            #geturl(URI, tmpFileName)
        else :
            return False
        #try to use zip instead
        zfile = zipfile.ZipFile(tmpFileName)
        
#        TF=tarfile.TarFile(tmpFileName)
        dirname1=upy.__path__[0]+os.sep+".."+os.sep+"upy"
        import shutil        
        if backup :
            #rename ePMV to ePMVv
            dirname2=dirname1+upy.__version__
#            print(dirname1,dirname2)
            if os.path.exists(dirname2):
                shutil.rmtree(dirname2,True)
            shutil.copytree (dirname1, dirname2)
        if os.path.exists(dirname1):
            shutil.rmtree(dirname1,True)           
#        TF.extractall(patchpath)
        zfile.extractall(patchpath)
        zfile.close()
        os.remove(tmpFileName)
        return True
        
    def update_AF(self,backup=False):
        import zipfile
        p = AutoFill.__path__[0]+os.sep       
#        print "update_AF",AFwrkDir1
        URI="http://mgldev.scripps.edu/projects/ePMV/updates/autofill.zip"
        os.chdir(p)
        os.chdir("../")
        patchpath = os.path.abspath(os.curdir)
        tmpFileName = patchpath+os.sep+"autofill.zip"
#        print tmpFileName
#        if not os.path.isfile(tmpFileName):
        urllib.urlcleanup()
        if checkURL(URI) :
            urllib.urlretrieve(URI, tmpFileName,reporthook=self.helper.reporthook)
            #geturl(URI, tmpFileName)
        else :
            return False
        zfile = zipfile.ZipFile(tmpFileName)    
#        TF=tarfile.TarFile(tmpFileName)
        dirname1=AFwrkDir1#+os.sep+".."+os.sep+"AutoFill"
        import shutil
        if backup :
            #rename AF to AFv
            dirname2=dirname1+AutoFill.__version__
#            print(dirname1,dirname2)
            if os.path.exists(dirname2):
                shutil.rmtree(dirname2,True)
            shutil.copytree(dirname1, dirname2)
        if os.path.exists(dirname1):
            shutil.rmtree(dirname1,True)           
#        TF.extractall(patchpath)
        zfile.extractall(patchpath)
        zfile.close()
        os.remove(tmpFileName)
        return True
        
    def update(self,upAF,upupy,backup=False):
        #path should be set up before getting here
        if upAF :
            #it actually depends on the host...
            self.update_AF(backup=backup)
        if upupy :
            #it actually depends on the host...
            self.update_upy(backup=backup)

    def checkUpdate_cb_cb(self,res):
        self.drawMessage(title='update AF',message="AF will now update. Please be patient while the update downloads. This may take several minutes depending on your connection speed.")
        doit=self.checkForUpdate(self.upyv,self.afv)        
        self.update(doit[0],doit[1],backup=res)
        self.drawMessage(title='update AF',message="You are now up to date. Please restart "+self.host)
        self.helper.resetProgressBar()
            
    def checkUpdate_cb(self,res):
        if res :
            self.drawQuestion(question="Do you want to backup the current version?",callback=self.checkUpdate_cb_cb)

    def devCheckUpdate(self,*args):
        liste_plugin={"upy":{"version_current":upy.__version__,"path":upy.__path__[0]},
                      "AutoFill":{"version_current":AutoFill.__version__,"path":AutoFill.__path__[0]}}
        from upy.upy_updater import Updater
        up = Updater(host=self.host,helper=self.helper,gui=self,liste_plugin=liste_plugin,typeUpdate="dev")
        up.checkUpdate()

    def stdCheckUpdate(self,*args):
        liste_plugin={"upy":{"version_current":upy.__version__,"path":upy.__path__[0]},
                      "AutoFill":{"version_current":AutoFill.__version__,"path":AutoFill.__path__[0]}}
        from upy.upy_updater import Updater
        up = Updater(host=self.host,helper=self.helper,gui=self,liste_plugin=liste_plugin)
        up.checkUpdate()

    def checkUpdate(self,*args):
        #get current version
#        import Support
#        self.epmv.inst.current_version = self.__version__
#        self.epmv.inst.PMVv = Support.version.__version__
#        self.epmv.inst.upyv = upy.__version__
        self.upyv = upyv = upy.__version__
        self.afv = afv = AutoFill.__version__
        doit=self.checkForUpdate(upyv,afv)
        if True in doit :
            #need some display?
            msg = "An update is available.\nNotes:\n"
#            msg+= self.epmv.inst.update_notes
            msg+= "Do you want to update?\n"
            self.drawQuestion(question=msg,callback=self.checkUpdate_cb)
        else :
            self.drawMessage(title='update AF',message="You are up to date! No update necessary.")

    def visitUpdate(self,*args):
        import webbrowser
        webbrowser.open(self.__url__[2])

    def visiteAFweb(self,*args):
        import webbrowser
        webbrowser.open(self.__url__[0])

    def visiteAFwebAPI(self,*args):
        import webbrowser
        webbrowser.open(self.__url__[1])

    def drawAbout(self,*args):
        self.upyv = upyv = upy.__version__
        self.afv = afv = AutoFill.__version__        
        #doit=self.checkForUpdate(upyv,afv)
        liste_plugin={"upy":{"version_current":upy.__version__,"path":upy.__path__[0]+os.sep},
                      "AutoFill":{"version_current":AutoFill.__version__,"path":AutoFill.__path__[0]+os.sep}}
        from upy.upy_updater import Updater
        up = Updater(host=self.host,helper=self.helper,gui=self,liste_plugin=liste_plugin,typeUpdate="std")
        up.readUpdateNote()
        self.__about__="v"+AutoFill.__version__ +" of autoPACK is installed.\nv"+up.result_json["AutoFill"]["version_std"]+" is available under Help/Check for Updates.\n\n"
        self.__about__+="v"+upy.__version__+" of uPy is installed.\nv"+up.result_json["upy"]["version_std"]+" is available under Help/Check for Updates.\n"
#        self.__about__="v"+AutoFill.__version__ +" of autoPACK is installed.\nv"+self.newAFv+" is available under Help/Check for Updates.\n\n"
#        self.__about__+="v"+upy.__version__+" of uPy is installed.\nv"+self.newuPyv+" is available under Help/Check for Updates.\n"
        self.__about__+="""
        
autoPACK uPy GUI: Ludovic Autin, Graham Jonhson, & Michel Sanner.

autoPACK code authors: Graham T. Johnson, Ludovic Autin, Mostafa Al-Alusi, & Michel Sanner
            
autoPACK main paper authors: Graham T. Johnson, Ludovic Autin, Mostafa Al-Alusi, David Goodsell, Michel Sanner, & Arthur Olson. Citation coming in 2013.
            
Developed in the Molecular Graphics Lab at Scripps directed by Arthur Olson.
            
Developed in qb3@UCSF by Graham Johnson
            
Open-source project: http://autopack.org
Copyright: Graham Johnson ©2010
        """
        self.drawMessage(title='About autoPACK',message=self.__about__)

    def CreateLayout(self):
        self._createLayout()
        #self.restorePreferences()
        return True

    def Command(self,*args):
#        print args
        self._command(args)
        return True
    
    def setRVersion(self,*args):
        pass

    def updateRVersion(self,*args):
        recipe = self.getVal(self.WidgetViewer["menuscene"])
        if recipe != "Load" and recipe != "Fetch":
            #get the recipe version..mean there is older version ?
            liste_version = list(self.recipe_available[recipe].keys())
            liste_version.sort()
            self.resetPMenu(self.WidgetViewer["recipeversion"] )
            [self.addItemToPMenu(self.WidgetViewer["recipeversion"],n) for n in liste_version]
            self.setVal(self.WidgetViewer["recipeversion"],0)

    def updateRVersionFiller(self,*args):
        recipe = self.getVal(self.WidgetFiller["menuscene"])
        if recipe != "Load" and recipe != "Fetch" and recipe != "Custom":
            #get the recipe version..mean there is older version ?
            liste_version = list(self.recipe_available[recipe].keys())
            liste_version.sort()
            self.resetPMenu(self.WidgetFiller["recipeversion"] )
            [self.addItemToPMenu(self.WidgetFiller["recipeversion"],n) for n in liste_version]
            self.setVal(self.WidgetFiller["recipeversion"],0)
    

        
    def preparePreFill(self,recipe,version="1.0",forceRecipe=False):
        #need a histoVol, afviewer, and helper  
        print (recipe,version)
        print (self.recipe_available[recipe][version]["setupfile"])        
        setupfile = self.recipe_available[recipe][version]["setupfile"]
        if setupfile.find("http") != -1 or setupfile.find("ftp") != -1:
            try :
                import urllib.request as urllib# , urllib.parse, urllib.error
            except :
                import urllib
            print ("setupfile to prepare",setupfile)
            #http://grahamj.com/autofill/autoFillData/HIV/HIVresult_2_afr.afr
            name =   setupfile.split("/")[-1]
            tmpFileName = self.recipe_available[recipe][version]["wrkdir"]+os.sep+name
            if not os.path.isdir(self.recipe_available[recipe][version]["wrkdir"]) :
                os.makedirs(self.recipe_available[recipe][version]["wrkdir"])                
                os.makedirs(self.recipe_available[recipe][version]["wrkdir"]+os.sep+"ingredients")
            if not os.path.isfile(tmpFileName) or forceRecipe :
                urllib.urlcleanup()
                if checkURL(setupfile) :
                    urllib.urlretrieve(setupfile, tmpFileName,reporthook=self.helper.reporthook)
                else :
                    if not os.path.isfile(tmpFileName):
                        print (" didnt found ",tmpFileName)
                        return False
            #this code is for Max to ensurehe xml file is there too
            xmlfile = self.server+recipe+"/recipe/"+recipe+version+".xml"
            tmpFileName2 = self.recipe_available[recipe][version]["wrkdir"]+os.sep+recipe+version+".xml"
            if not os.path.isfile(tmpFileName2) or forceRecipe :
                urllib.urlcleanup()
                if checkURL(xmlfile) :
                    urllib.urlretrieve(xmlfile, tmpFileName2,reporthook=self.helper.reporthook)
                else :
                    if not os.path.isfile(tmpFileName2):
                        print (" didnt found ",tmpFileName2)
                        return False
            setupfile = tmpFileName
        fileName, fileExtension = os.path.splitext(setupfile)
        print("prepare fill with ",recipe,version,setupfile)
        if fileExtension == ".py":
            if sys.version > "3.0.0":                
                setupfilebytes = os.fsencode(setupfile)
                setupfile = setupfilebytes.decode("utf-8","replace")
                print (setupfile)
                file = open(setupfile,"r", encoding="utf-8")
            else :
                file = open(setupfile,"r")
            commmands = file.read()
            if sys.version > "3.0.0":                
                commmands_bytes = os.fsencode(commmands)
                commmands = commmands_bytes.decode('utf-8', "replace")
            exec(commmands,globals(),{"AFGui":self})            
            #execfile(setupfile,globals(),{"h1":h1,"afviewer":afviewer})#how to get back the value
#            print (recipe)
#            print (self.histoVol) 
            self.histoVol[recipe].setupfile = setupfile
            return True
        elif  fileExtension == ".xml":
            self.loadxml(setupfile,recipe=recipe)
            return True

    def loadxml(self, filename,recipe=None):
        from AutoFill.HistoVol import Environment
        fileName, fileExtension = os.path.splitext(filename)
        n=recipe#os.path.basename(fileName)#version with it ...
        if n is None:
            n=os.path.basename(fileName)
        self.histoVol[n] = Environment(name=n)
        recipe=n
        self.histoVol[n].load_XML(filename)
        afviewer = AFViewer(ViewerType=self.helper.host,helper=self.helper)
        self.histoVol[n].name=n
        afviewer.SetHistoVol(self.histoVol[n],20.0,display=False)
        self.histoVol[n].host=self.helper.host
#        afviewer.doSpheres = True
#        afviewer.doPoints = True
        afviewer.displayPreFill()
        self.current_recipe = recipe

    def drawSubsetBuilder(self,*args):
        dlg = SphereTreeUI()
        dlg.setup(helper=self.helper,subdialog = True)
        self.sptui = dlg
        self.drawSubDialog(dlg,555555553)

    def Viewer_dialog(self,recipe,version="1.0"):
        buildUponLoad = self.getVal(self.WidgetViewer["BuildUponLoad"]) 
        showUponLoad = self.getVal(self.WidgetViewer["ShowUponLoad"])  
        BuildGrid = self.getVal(self.WidgetViewer["BuildGrid"])  
        Force = self.getVal(self.WidgetViewer["forceFetchResult"])
        gui = self.getVal(self.gmode)
        if not hasattr(self,recipe+"_viewerdlg"):
            dlg = SubdialogViewer() 
            dlg.setup(recipe=recipe,histoVol=self.histoVol[recipe],
                      afviewer=self.histoVol[recipe].afviewer,helper=self.helper,
                      build=buildUponLoad, show=showUponLoad, build_grid = BuildGrid,
                      guimode = gui,version=version,forceResult=Force)
            setattr(self,recipe+"_viewerdlg",dlg)
        else :
            dlg = getattr(self,recipe+"_viewerdlg")
            dlg.Set(build=buildUponLoad, show=showUponLoad)
#        print ("open ",dlg)
        self.drawSubDialog(dlg,555555555)
        dlg.toggleOrganelRepDisplay(None)
        dlg.toggleOrganelGeomDisplay(None)
        dlg.toggleHistoVolDisplay(None)        
              
    def drawSubsetViewer(self,*args):
        AutoFill.forceFetch = self.getVal(self.WidgetViewer["forceFetch"])
        #should drawhe dialog for the seleced recipe
        recipe = self.getVal(self.WidgetViewer["menuscene"]) 
        version = self.getVal(self.WidgetViewer["recipeversion"])
        forceRecipe = self.getVal(self.WidgetViewer["forceFetchRecipe"]) 
        if self.host.find("blender") != -1 :
            self.helper.dupliVert = self.getVal(self.use_dupli_vert)
        if recipe == "Load":
            self.fileDialog(label="choose a file",callback=self.loadxml)
            self.Viewer_dialog(self.current_recipe,version=version)
            return

        #first prepare the fill
        #is the fill already loaded
#        if recipe not in self.histoVol:
        if not self.preparePreFill(recipe,version=version,forceRecipe=forceRecipe):
            return
        #exec or call it as a subdialog ?
        self.Viewer_dialog(recipe,version=version)
        
    
    def Filler_dialog(self,recipe,version="1.0"):
        gui = self.getVal(self.gmode)
        if not hasattr(self,recipe+"_fillerdlg"):
            dlg = SubdialogFiller() 
            dlg.setup(recipe=recipe,histoVol=self.histoVol[recipe],
                      afviewer=self.histoVol[recipe].afviewer,helper=self.helper,
                        guimode = gui,version=version)
            setattr(self,recipe+"_fillerdlg",dlg)
        else :
            dlg = getattr(self,recipe+"_fillerdlg")
            if dlg.cleared :#probem with xml
                if self.current_recipe != recipe :
                	self.preparePreFill(recipe,version=version)
                dlg.Set(histoVol=self.histoVol[recipe],
                      afviewer=self.histoVol[recipe].afviewer,helper=self.helper)
#        print "DRAW DLG FILLER"
        self.drawSubDialog(dlg,555555556)
        #if self.helper.host.find("blender") == -1: 
        dlg.updateWidget()
        
    def drawSubsetFiller(self,*args):
        AutoFill.forceFetch = self.getVal(self.WidgetFiller["forceFetch"])
        #should drawhe dialog for the seleced recipe
        recipe = self.getVal(self.WidgetFiller["menuscene"]) 
        version = self.getVal(self.WidgetFiller["recipeversion"])
        self.setVal(self.WidgetViewer["BuildUponLoad"],False) 
        forceRecipe = self.getVal(self.WidgetViewer["forceFetchRecipe"])  
        if self.host.find("blender") != -1 :
            self.helper.dupliVert = self.getVal(self.use_dupli_vert)
#        print "drawSubsetFiller", recipe,version
#        self.setVal(self.WidgetViewer["ShowUponLoad"]) 
        if recipe == "Load":
            self.fileDialog(label="choose a xml file",callback=self.loadxml)
            self.Filler_dialog(self.current_recipe,version=version)
            return

        if recipe == "Custom" :
            #need to create the template scene
            #need to open a temporary dialog that wait for the setup and that can offer some option
            if not hasattr(self,recipe+"_customfillerdlg"):
                dlg = SubdialogCustomFiller() 
                dlg.setup(recipe=recipe,helper=self.helper,parent=self,version=version)
                setattr(self,recipe+"_customfillerdlg",dlg)
            else :
                dlg = getattr(self,recipe+"_customfillerdlg")   
            self.drawSubDialog(dlg,555555556)
            return
        #first prepare the fill
        #is the fill already loaded
#        if recipe not in self.histoVol:
        if not self.preparePreFill(recipe,version=version,forceRecipe=forceRecipe):
            return
        #exec or call it as a subdialog ?
        self.Filler_dialog(recipe,version=version)
        #or
#print __name__
#if __name__ == '__main__' :    
#if "self" in dir()   :
#    vi = self.GUI.VIEWER
#else :
#    from DejaVu import Viewer
#    vi = Viewer()
#mygui = AFGui(title="AFGui",master=vi)
##    print "init"
#mygui.setup(vi=vi)
##    print "setup"
#mygui.display() 
#    print "display"
#execfile("/Users/ludo/DEV/autofill_svn_test/autofill/trunk/AutoFillClean/AFGui.py")