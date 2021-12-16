# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 15:04:18 2010

###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# autofill_viewer.py Authors: Ludovic Autin with minor editing/enhancement from G Johnson
#
# Copyright: Graham Johnson ©2010
#
# This file "autofill_viewer.py" is part of autoPACK.
#
#    autoPack is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    autoPack is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with autoPack (See "CopyingGNUGPL" in the installation.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
@author: Ludovic Autin

Viewer/helper of AutoFill result.
"""
import os
import math
#DEJAVU COLORS

from time import time
     
#from DejaVu.colorTool import Map
#from pyubic import colors as c
from upy import colors as c

#===============================================================================
# to do :
#      - use layer for hiding the parent of ingredient ! probably faster than creating a specific hider object
#      - save-restore + grid interesectnio continuation
#          =>imply deocmpose histoVol in Grid class and HistoVol class
#      - hierarchy
#   
#===============================================================================
import numpy
import upy
from upy.colors import red, aliceblue, antiquewhite, aqua, \
     aquamarine, azure, beige, bisque, black, blanchedalmond, \
     blue, blueviolet, brown, burlywood, cadetblue, \
     chartreuse, chocolate, coral, cornflowerblue, cornsilk, \
     crimson, cyan, darkblue, darkcyan, darkgoldenrod, \
     orange, purple, deeppink, lightcoral, \
     blue, cyan, mediumslateblue, steelblue, darkcyan, \
     limegreen, darkorchid, tomato, khaki, gold, magenta, green

from AutoFill.Ingredient import GrowIngrediant,ActinIngrediant
try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib

class AFViewer:

    """
    the base class for viewing/displaying autoFill result in a specified viewer
    ie DejaVu, Cinema4D, Maya or Blender (which are supported hostApp by ePMV)
    """
    
    def __init__(self, helper=None, ViewerType='dejavu'):
        """
        Constructor of the AFViewer. Define the needed function for constructing
        the geometry representing the different organelle and recipe that have 
        been used for the filling.
        
        @type  ViewerType: string
        @param ViewerType: name of the viewer / host application
        """    
        self.ViewerType = ViewerType.lower()
        #get helperClass
        self.vi = helper
        if self.vi is None :
            helperClass = upy.getHelperClass()
            if self.ViewerType == 'dejavu':
#                from DejaVu import Viewer
#                master = Viewer()
                self.vi = helperClass()#master=master)
            else :
                self.vi = helperClass()
        sc = self.vi.getCurrentScene()
        self.wrkdir = "."

        #here can be add other viewer...
        self.vi.Box = self.vi.box
        self.sc = sc
        #need some option such as display Point cloud, overall resolution, etc...
        self.doPoints = True
        self.pointWidth = 3.
        self.quality = 1
        self.doSpheres = True
        self.visibleMesh = True
        self.orgaToMasterGeom = {}
        self.psph = None
        self.staticMesh = None
        self.movingMesh=None
        self.helper = self.vi
        self.doOrder = False
        self.renderDistance = False
        self._timer = False
        self.fbb = None   
        self.meshGeoms={}
        self.OPTIONS = {
                    "doPoints":{"name":"doPoints","value":True,"default":True,"type":"bool"},
                    "doSpheres":{"name":"doSpheres","value":True,"default":True,"type":"bool"},
                    "quality":{"name":"quality","value":1,"default":1,"type":"int"},
                    "pointWidth":{"name":"pointWidth","value":3.,"default":3.,"type":"float"},
                    "visibleMesh":{"name":"visibleMesh","value":True,"default":True,"type":"bool"},
                    "doOrder":{"name":"doOrder","value":False,"default":False,"type":"bool"},
                    "renderDistance":{"name":"renderDistance","value":False,"default":True,"type":"bool"},
                    "_timer":{"name":"_timer","value":False,"default":False,"type":"bool"},
                    }

    def callFunction(self,function,*args,**kw):
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

    def SetHistoVol(self,histo,pad,display=True):
        """
        Define the current histo volume.
        
        @type  histo: AutoFill.HistoVol
        @param histo: the current histo-volume
        @type  pad: float
        @param pad: the pading value to extend the histo volume bounding box
        @type  display: boolean
        @param display: if a geometry is created to represent the histoVolume box
        
        """    
         
        self.histo = histo
        self.name = self.histo.name
        print (self.name,self.histo.name)
        self.histo.afviewer = self
        # add padding
        bb = self.histo.boundingBox
        if bb == ([0,0,0], [.1,.1,.1]):
            print('no organelle no bb')
            return
        x,y,z = bb[0]
        px,py,pz = [0.,0.,0.]  #Oct 16,2012 Graham- need to control padding on 3 sides.
        if type( pad ) != list :
            px=pad
            py=pad
            pz=pad
        else:
            px,py,pz = pad
#        bb[0] = [x-pad+pad, y-pad, z-pad+pad]  
        bb[0] = [x-px, y-py, z-pz]
        x,y,z = bb[1]
#        bb[1] = [x+pad-pad, y+pad, z+pad-pad]
        bb[1] = [x+px, y+py, z+pz]
        print('Bounding box x with padding', self.histo.boundingBox)
        if display : 
            self.displayHistoVol()        


    def addMasterIngr(self,ingr,parent=None):
        """
        Create a empty master/parent geometry for a ingredient
        
        @type  ingr: AutoFill.Ingredient
        @param ingr: the ingredient 
        @type  parent: hostObject
        @param parent: specifiy a parent to insert under
        """ 
        if ingr.compNum == 0 :
            organelle = self.histo
        else :
            organelle = self.histo.organelles[abs(ingr.compNum)-1]
        #print("parent",parent,self.vi.getName(parent))
        name = '%s_%s'%(ingr.name,organelle.name)
        gi = self.vi.getObject(name)
        print(gi,name)
        if gi is None :
            gi = self.vi.newEmpty(name, parent=parent)
#            self.vi.AddObject(gi)
#            print(gi,name)
        self.orgaToMasterGeom[ingr] = gi

    def prepareMaster(self):
        """
        Create all empty master/parent geometry for the cytoplasm and 
        all ingredient. If not in DejaVu prepare the meshs use for instanced 
        geometry such as spheres and cylinders
        """    
        
        # create master for cytoplasm compartment
        #
        self.master = self.vi.getObject(self.name)
        if self.master is None :
            self.master = self.vi.newEmpty(self.name)
        print ("master",self.name,self.master)
        name = self.name+'_cytoplasm'
        g = self.vi.getObject(name)
        if g is None:
            g = self.vi.newEmpty(name, visible=0,parent=self.master)
            self.orgaToMasterGeom[0] = g
            self.orgaToMasterGeom[self.histo] = g
        else :
            self.vi.reParent(g,self.master)
        # create masters for ingredients
        r =  self.histo.exteriorRecipe
        if r :
            for ingr in r.ingredients:
                self.addMasterIngr(ingr,parent=g)
                
        #fpg = self.vi.Geom('notFreePoints')
        #self.vi.AddObject(fpg)
        vParentHiders = self.vi.getObject(self.name+"ParentHiders") #g
        if vParentHiders is None : #g
            vParentHiders=self.vi.newEmpty(self.name+"ParentHiders",parent=self.master)
        #if self.ViewerType != 'dejavu':
        #    #define the base shape for instance objects
        if self.psph is None:
            self.psph=self.vi.newEmpty(self.name+"base_shape",parent=vParentHiders)
#            self.vi.AddObject(self.psph)            
            self.pesph=self.vi.newEmpty(self.name+"base_sphere",parent=self.psph)
#            self.vi.AddObject(self.pesph)                    
            self.bsph=self.vi.Sphere(self.name+"sphere",res=self.quality,parent=self.pesph)[0]
            #self.vi.AddObject(self.bsph,parent=self.pesph)
            self.becyl=self.vi.newEmpty(self.name+"base_cylinder",parent=self.psph)
#            self.vi.AddObject(self.becyl,parent=self.psph)
            self.bcyl=self.vi.Cylinder(self.name+"cylinder",res=self.quality,parent=self.becyl)
            #self.vi.AddObject(self.bcyl,parent=self.becyl)                       
#        if self.staticMesh is None :#and self.helper.host == "dejavu" :
#            #dynamic object
#            self.staticMesh=self.vi.newEmpty(self.name+"static",parent=self.master)
#            self.vi.AddObject(self.staticMesh)
#            self.movingMesh=self.vi.newEmpty(self.name+"moving",parent=self.master)
#            self.vi.AddObject(self.movingMesh)
        
        self.prevIngrOrga = self.vi.getObject(self.name+"_PreviousIngrOrga") #g
        if self.prevIngrOrga is None : #g
            self.prevIngrOrga=self.vi.newEmpty(self.name+"_PreviousIngrOrga",parent=self.master)
        
        self.prevIngr = self.vi.getObject(self.name+"_PreviousIngrExterior") #g
        if self.prevIngr is None : #g
            self.prevIngr=self.vi.newEmpty(self.name+"_PreviousIngrExterior",parent=self.prevIngrOrga)
        self.prevIngrOrg={}
        for i,o in enumerate(self.histo.organelles):
            self.prevIngrOrg[i]  = self.vi.getObject(self.name+"_PreviousIngr"+o.name+"_surface") #g
            if self.prevIngrOrg[i] is None : #g
                self.prevIngrOrg[i]=self.vi.newEmpty(self.name+"_PreviousIngr"+o.name+"_surface",parent=self.prevIngrOrga)
            self.prevIngrOrg[-i]  = self.vi.getObject(self.name+"_PreviousIngr"+o.name+"_inner") #g
            if self.prevIngrOrg[-i] is None : #g
                self.prevIngrOrg[-i]=self.vi.newEmpty(self.name+"_PreviousIngr"+o.name+"_inner",parent=self.prevIngrOrga)
                
        self.prevOrga = self.vi.getObject(self.name+"_PreviousOrga") #g
        if self.prevOrga is None : #g
            self.prevOrga=self.vi.newEmpty(self.name+"_PreviousOrga",parent=self.prevIngrOrga)
            
    def displayHistoVol(self):        
        """
        display histo volume bounding box 
        """
        name = 'histoVolBB'
        b=self.helper.getObject(name)
        if b is None :
            self.histoBox = self.vi.Box(name, cornerPoints=self.histo.boundingBox,parent=self.master)[0]
            self.vi.AddObject(self.histoBox)
        else :
            self.histoBox = b
            self.vi.reParent(self.histoBox,self.master)
            
    def displayFillBox(self,bb):
        """
        display the box used for compute the grid and fill
        """
        if self.fbb is None :
            self.fbb = self.vi.Box('fillBox',cornerPoints=bb,visible=1) #maybe /10.
            self.vi.AddObject(self.fbb)

    def displayOrganelle(self,orga):
        """
        Create and display geometry for an organelle.
        
        @type  orga: AutoFill.Organelle
        @param orga: the organelle 
        """    

        # create master for organelle
        name = 'O%s'%orga.name
        g = self.helper.getObject(name)
        if g is None :
            g = self.vi.newEmpty(name,parent=self.master)
#            self.vi.AddObject(g)
            gs = self.vi.newEmpty('%s_Surface'%orga.name, parent=g)
#            self.vi.AddObject(gs)
            gc = self.vi.newEmpty('%s_Matrix'%orga.name, parent=g)
#            self.vi.AddObject(gc)
            self.orgaToMasterGeom[orga] = g
            self.orgaToMasterGeom[orga.number] = gs
            self.orgaToMasterGeom[-orga.number] = gc
        else :
            gs =  self.helper.getObject('%s_Surface'%orga.name)
            gc =  self.helper.getObject('%s_Matrix'%orga.name)
            self.orgaToMasterGeom[orga] = g
            self.orgaToMasterGeom[orga.number] = gs
            self.orgaToMasterGeom[-orga.number] = gc
            
        # create masters for ingredients
        r =  orga.surfaceRecipe
        if r :
            for ingr in r.ingredients:
                self.addMasterIngr(ingr,parent=gs)
        r =  orga.innerRecipe
        if r :
            for ingr in r.ingredients:
                self.addMasterIngr(ingr,parent=gc)
        
        if orga.isOrthogonalBoudingBox != 1:
            #create the mesh for the organelle
            name = '%s_Mesh'%orga.name
            tet = self.helper.getObject(name)
            if tet is None :
                tet = self.vi.IndexedPolygons(name, vertices=orga.vertices,
                                  faces=orga.faces, normals=orga.vnormals,
                                  inheritFrontPolyMode=False,
                                  frontPolyMode='line',dejavu=True, 
                                  inheritCulling=0, culling='none',
                                  inheritShading=0, shading='flat')
                self.vi.AddObject(tet, parent=g)
                if self.ViewerType == 'dejavu':
                    self.vi.toggleDisplay(tet,False)
#            if self.ViewerType == 'dejavu':
#                cp = self.vi.viewer.clipP[0]
#                self.vi.viewer.GUI.clipvar[0][0].set(1)
#                tet.AddClipPlane( cp, 1, False)    
            orga.mesh = tet
        if orga.representation != None:
            name = '%s_Rep'%orga.name
            p = self.vi.getObject(name)
            if p is None :
                p = self.vi.newEmpty(name,parent='O%s'%orga.name)
            print ("orga.representation ",name, p, orga.representation)
            self.vi.reParent(orga.representation,p)  
    #        orga.ref_obj = name

    def createOrganelMesh(self, orga ):
        if orga.isOrthogonalBoudingBox != 1 :
            name = '%s_Mesh'%orga.name
            if self.helper.host == "maya" :
                name = "mesh_"+name #TODO fix this in maya
            tet = self.helper.getObject(name)
            if tet is None :
                tet = self.vi.IndexedPolygons(name, vertices=orga.vertices,
                                  faces=orga.faces, normals=orga.vnormals,
                                  inheritFrontPolyMode=False,
                                  frontPolyMode='line',dejavu=True, 
                                  inheritCulling=0, culling='none',
                                  inheritShading=0, shading='flat')
                self.vi.AddObject(tet, parent=self.orgaToMasterGeom[orga])
            else :
                self.vi.updateMesh(tet,vertices=orga.vertices,
                                  faces=orga.faces)

    def toggleOrganelMesh(self,organame,display):
        for orga in self.histo.organelles:
            if orga.name == organame :
                self.vi.toggleDisplay('%s_Mesh'%orga.name,display)
    
    def toggleOrganelMatr(self,organame,display):
        for orga in self.histo.organelles:
            if orga.name == organame :
                self.vi.toggleDisplay('%s_Matrix'%orga.name,display)
    
    def toggleOrganelSurf(self,organame,display):
        for orga in self.histo.organelles:
            if orga.name == organame :
                self.vi.toggleDisplay('%s_Surface'%orga.name,display)
        
    def displayOrganelles(self):
        """
        Create and display geometry for all organelles defined for the histoVolume.
        """            
        for orga in self.histo.organelles:
#            print("In orga $$$$$$$$$$$$$$$$$$$$$$$$ with orthogonalBoundingBox = ", orga.isOrthogonalBoudingBox)
#            if orga.isOrthogonalBoudingBox != 1:
#                print("in orga is box because isOrthogonalBoudingBox = ", orga.isOrthogonalBoudingBox)
            self.displayOrganelle(orga)

    def displayPreFill(self):
        """
        Use this function once a histoVol and his organelles are defined. 
        displayPreFill will prepare all master, and will create the geometry for 
        the histovolume bounding box, and the different organelles defined.
        """            

        #use this script once a histoVol and organelles are defined
        self.prepareMaster()
        self.displayOrganelles()
        self.displayHistoVol()
        self.prepareIngrediant()
        self.prepareDynamic()
        if self.vi.host.find("blender") != -1 :
            #change the viewportshadr
            from .ray import vlen, vdiff, vcross
            boundingBox=self.histo.boundingBox
            xl,yl,zl = boundingBox[0]
            xr,yr,zr = boundingBox[1]
            diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
            if diag < 10000.0 :
                diag = 10000.0
            self.vi.setViewport(clipstart=0,clipend=diag,center=True)#shader="glsl",
            print ("#########VIEWPORT SET#######")
#        elif self.ViewerType == 'dejavu':
#            self.vi.viewer.Reset_cb()
#            self.vi.viewer.Normalize_cb()
#            self.vi.viewer.Center_cb()
#            cam = self.vi.viewer.currentCamera
#            #cam.master.master.geometry('%dx%d+%d+%d'%(400,400, 92, 73))
#            self.vi.viewer.update()
#            cam.fog.Set(enabled=1)
#            sph = self.vi.Spheres('debugSph', inheritMaterial=False)
#            self.vi.AddObject(sph)
#        else :
#            #we can probably setup here the overall quality in the viewport
#            pass

    def colorPT(self,name,values):
        pass
#        pt = self.vi.getObject(name)
#        from DejaVu.colorTool import Map, RGBRamp
#        from DejaVu.colorMap import ColorMap
#        #from DejaVu.colorMapLegend import ColorMapLegend
#        ramp = RGBRamp()
#        v=values
#        colors = Map(v, ramp)
#        self.vi.changeColor(pt,colors)

    def prepareDynamic(self):
        #create two empty for static and moving object
        if self.movingMesh is None :
            self.movingMesh = self.vi.newEmpty("movingMesh")
#            self.vi.addObjectToScene(None,self.movingMesh)
        self.vi.setRigidBody(self.movingMesh,**self.histo.dynamicOptions["moving"])
        if self.staticMesh is None :
            self.staticMesh = self.vi.newEmpty("staticMesh")
#            self.vi.addObjectToScene(None,self.staticMesh)
        self.vi.setRigidBody(self.staticMesh,**self.histo.dynamicOptions["static"])

    def displayFill(self):
        """
        Use this function once a Box have been filled. displayFill will display 
        all placed ingredients in the Box, and affilated them according if they are
        on surface, in cytoplasme or in the organelle. displayFill also display 
        optionally the differnt point grid.
        """     
        if self.master is None :
            self.displayPreFill()
        self.vi.resetProgressBar()  
        self.vi.progressBar(label="displayFill")
        if self.doPoints:
            self.vi.progressBar(label="displayPoints")
            self.callFunction(self.displayOrganellesPoints)#()
            self.callFunction(self.displayFreePoints)#()
        self.vi.progressBar(label="displayCytoplasmIngredients")
        self.callFunction(self.displayCytoplasmIngredients)#
        self.vi.progressBar(label="displayOrganellesIngredients")
        self.callFunction(self.displayOrganellesIngredients)#
        
        if self.vi.host.find("blender") != -1 :
            p=self.vi.getObject("AutoFillHider")
            self.vi.setLayers(p,[1])
            
        if self.ViewerType == 'dejavu':
#            from DejaVu.colorTool import RGBRamp#, Map
            verts = []
            labels = []
            p=self.vi.getObject("AutoFillHider")
            self.vi.toggleDisplay(p,True)
            if hasattr(self.histo, 'distToClosestSurf'):
                for i, value in enumerate(self.histo.distToClosestSurf):
                    if self.histo.gridPtId[i]==1:
                        verts.append( self.histo.masterGridPositions[i] )
                        labels.append("%.2f"%value)
                lab = self.vi.Labels('distanceLab', vertices=verts, labels=labels, visible=0)
                self.vi.AddObject(lab)
            
            if hasattr(self.histo, 'jitter_vectors'):
#                from DejaVu.Polylines import Polylines
                verts = []
                for p1, p2 in (self.histo.jitterVectors):
                    verts.append( (p1, p2))
        
                jv = self.vi.Polylines('jitter_vectors', vertices=verts, visible=1,
                               inheritLineWidth=0, lineWidth=4)
                self.vi.AddObject(jv, parent=self.master)
        self.vi.resetProgressBar()
        if self.vi.host.find("blender") != -1 :
            #change the viewportshadr
            self.vi.setViewport(center=1)

    def displayPoints(self,name,points,parent,colors=[[1,1,0]]):
        """
        Use this function to display a pointCloud. By default, theses points 
        are not visible in the viewport.

        @type  name: string
        @param name: the name of the point cloud object
        @type  points: list
        @param points: list of point indice or list point array 
        @type  parent: hostObject
        @param parent: the parent of the point cloud
        @type  colors: list
        @param colors: point color array [r,g,b]

        """            

        verts = []
        labels = []
        if len(points) == 0 :
            print (name, " have no points") 
        if type(points[0]) is int :
#            verts,labels=[(self.histo.grid.masterGridPositions[ptInd],"%d"%ptInd) for ptInd in points]
            for ptInd in points:
                verts.append( self.histo.grid.masterGridPositions[ptInd])
                labels.append("%d"%ptInd)
        else :
#            verts,labels=[(pt,"%d"%i) for i,pt in enumerate(points)]
            for i,pt in enumerate(points):
                verts.append( pt )
                labels.append("%d"%i)
        s = self.vi.getObject(name)
        if s is None and verts:
            s = self.vi.Points(name, vertices=verts, materials=colors,
                   inheritMaterial=0, pointWidth=self.pointWidth, inheritPointWidth=0,
                   visible=0,parent = parent)
        if self.ViewerType == 'dejavu':
            self.vi.AddObject(s, parent=parent)
            labDistg = self.vi.Labels(name+'Lab', vertices=verts, labels=labels,
                             visible=0)
            self.vi.AddObject(labDistg, parent=parent)

    def displayOrganellePoints(self,orga):
        """
        Use this function to display grid pointCloud for an organelle

        @type  orga: AutoFill.Organelle
        @param orga: the organelle 
        """            
        vGridPointHider = self.vi.getObject(orga.name+"GridPointHider") #g
        if vGridPointHider is None : #g
            vGridPointHider=self.vi.newEmpty(orga.name+"GridPointHider",parent=self.orgaToMasterGeom[orga])
        if self.ViewerType == 'dejavu':
            verts = []
            for i, p in enumerate(orga.surfacePoints):
                pt = self.histo.masterGridPositions[p]
                norm = orga.surfacePointsNormals[p]
                verts.append( (pt, (pt[0]+norm[0]*10, pt[1]+norm[1]*10, pt[2]+norm[2]*10) ) )
            n = self.vi.Polylines('normals', vertices=verts, visible=0)
            self.vi.AddObject(n, parent=self.orgaToMasterGeom[orga])

        if orga.isOrthogonalBoudingBox != 1:
            if hasattr(orga, 'ogsurfacePoints'):
                # display off grid surface grid points
                self.displayPoints('%s_OGsurfacePts'%orga.name,orga.ogsurfacePoints,
                                   vGridPointHider)    
            if hasattr(orga, 'surfacePoints'):
                # display surface grid points
                self.displayPoints('%s_surfacePts'%orga.name,orga.surfacePoints,
                                   vGridPointHider,colors = [(1,0,0)])
        if hasattr(orga, 'insidePoints'):
            # display interior grid points
            print("orga.name =", orga.name)
            print("orga.insidePoints =", orga.insidePoints)
            print("self.orgaToMasterGeom[orga] =", self.orgaToMasterGeom[orga])
            self.displayPoints('%s_insidePts'%orga.name,orga.insidePoints,
                               vGridPointHider,colors = [(0,1,0)])

    def displayOrganellesPoints(self):
        """
        Create and display grid points for all organelles defined for the histoVolume.
        """            
        for orga in self.histo.organelles:
            self.displayOrganellePoints(orga)
    #        print("In orga $$$$$$$$$$$$$$$$$$$$$$$$ with orthogonalBoundingBox = ", orga.isOrthogonalBoudingBox)
#            if orga.isOrthogonalBoudingBox != 1:
    #            print("in orga is box because isOrthogonalBoudingBox = ", orga.isOrthogonalBoudingBox)
#                self.displayOrganellePoints(orga)

    def displayIngrSpheres(self,ingr,verts,radii,visible=1):
        o = ingr.recipe().organelle()
        if len(verts[ingr]):
            if ingr.modelType=='Spheres':
                name = o.name+"_Spheres_"+ingr.name.replace(" ","_")
                if self.ViewerType == 'dejavu':
                    sph = self.vi.Spheres(name, inheritMaterial=0,
                              centers=verts[ingr], materials=[ingr.color],
                              radii=radii[ingr], visible=visible)
                    self.vi.AddObject(sph, parent=self.orgaToMasterGeom[ingr])
                    #print ingr.name, verts[ingr]                    
                else :
                    parent = self.vi.getObject(name)
                    names=self.histo.FillName[self.histo.cFill]+"S"+ingr.name.replace(" ","_")
                    if parent is None:
                        parent=self.vi.newEmpty(name,parent=self.orgaToMasterGeom[ingr])
#                        self.vi.AddObject(parent,parent=self.orgaToMasterGeom[ingr])                            
                    if not hasattr(ingr,'isph') or ingr.isph is None:
                        ingr.isph=self.vi.instancesSphere(names,verts[ingr],radii[ingr],
                                    self.pesph,[ingr.color],self.sc,parent=parent)
                                    
                    else :
                        self.vi.updateInstancesSphere(names,ingr.isph,verts[ingr],
                                    radii[ingr],self.pesph,[ingr.color],self.sc,
                                    parent=parent,delete=True)
                        
    def displayIngrCylinders(self,ingr,verts,radii,visible=0):
        #dont do it for a snake ingredient...
        #just use the realtime capbility
        if isinstance(ingr,GrowIngrediant):
            return
        o = ingr.recipe().organelle()
        v = numpy.array(verts[ingr])
        f = numpy.arange(len(v))
        f.shape=(-1,2)
        name = o.name+"_Cylinders_"+ingr.name.replace(" ","_")
        if self.ViewerType == 'dejavu':                
            cyl = self.vi.Cylinders(name, inheritMaterial=0,
                            vertices=v, faces=f, materials=[ingr.color],
                            radii=radii[ingr], visible=visible,
                            inheritCulling=0, culling='None',
                            inheritFrontPolyMode=0, frontPolyMode='line')
            self.vi.AddObject(cyl, parent=self.orgaToMasterGeom[ingr])
        else :
            parent = self.vi.getObject(name)
            names=self.histo.FillName[self.histo.cFill]+"C"+ingr.name.replace(" ","_")
            #name=self.orgaToMasterGeom[ingr].GetName()+"Cylinders"
            #parent=self.vi.newEmpty(name)
            if parent is None :
                parent=self.vi.newEmpty(name,parent=self.orgaToMasterGeom[ingr])
            if not hasattr(ingr,'icyl') or ingr.icyl is None: 
                ingr.icyl=self.vi.instancesCylinder(names,verts[ingr],f,radii[ingr],
                    self.becyl,[ingr.color],self.sc,parent=parent)
            else :
                ingr.icyl=self.vi.updateInstancesCylinder(names,ingr.icyl,verts[ingr],
                                f,radii[ingr],self.becyl,[ingr.color],self.sc,
                                parent=parent,delete=True)

    def displayIngrGrows(self):
        r =  self.histo.exteriorRecipe
        if r :
            for ingr in r.ingredients:
                if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
                    self.displayIngrGrow(ingr)
        #organelle ingr
        for orga in self.histo.organelles:
            #organelle surface ingr
            rs =  orga.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
                        self.displayIngrGrow(ingr)
            #organelle matrix ingr
            ri =  orga.innerRecipe
            if ri :
                for ingr in ri.ingredients:
                    if isinstance(ingr, GrowIngrediant) or isinstance(ingr, ActinIngrediant):
                        self.displayIngrGrow(ingr)
    
    def displayIngrGrow(self,ingr,visible=1):
        print ("displayIngrGrow",ingr,ingr.nbCurve)
        #how to restore / store gro ingedient
        o = ingr.recipe().organelle()
        parent=self.orgaToMasterGeom[ingr]
        pobj = None
        if ingr.unitParent is not None:
            pobj=ingr.unitParent
        for i in range(ingr.nbCurve):
            name = o.name+str(i)+"snake_"+ingr.name.replace(" ","_")
            snake = self.helper.getObject(name)
            if snake is None :
                snake=self.vi.spline(name, ingr.listePtLinear[i],close=0,type=1,
                             scene=self.sc,parent=parent)[0]
            else :
                self.vi.update_spline(name,ingr.listePtLinear[i])
            self.vi.toggleDisplay(snake,visible)
            if pobj is not None :
                name = o.name+str(i)+"_unit_"+ingr.name.replace(" ","_")
                #pathDeform instance of one turn using snake
                actine = self.helper.getObject(name)
                if actine is None :
                    actine = self.vi.newInstance(name,pobj)
                modifier = self.helper.getObject(name+"pd")
                if modifier is None :
                    modifier = self.vi.pathDeform(actine,snake)
                else :
                    self.vi.updatePathDeform(modifier,object=actine,spline=snake)
                #what about a reall long one -> cloner or instance
            else :
                    circle = self.vi.build_2dshape(name+"_shape",opts=[ ingr.encapsulatingRadius,])
                    extruder,shape = self.vi.extrudeSpline(snake,shape=circle)#shoud use the radius for a circle ?
                    #reparent ?
                    
    def prepareIngrediant(self,):
       #cyto ingr
        r =  self.histo.exteriorRecipe
        if r :
            self.displayIngrediants(r)

        #organelle ingr
        for orga in self.histo.organelles:
            #organelle surface ingr
            rs =  orga.surfaceRecipe
            #organelle matrix ingr
            ri =  orga.innerRecipe
            if rs :
                self.displayIngrediants(rs)
            if ri:
                self.displayIngrediants(ri)
                
    def displayIngrediants(self,recipes):
        for ingr in recipes.ingredients:
            if ingr.mesh == None :#mes_3d?
                #try get it
                ingr.mesh = self.helper.getObject(ingr.name) 
            if ingr.mesh: # display mesh
                if self.ViewerType != 'dejavu':
                    self.createIngrMesh(ingr)
                else :
                    ingr.mesh_3d = ingr.mesh
                    if ingr.color != None :
                        ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)
                        
                    
    def createIngrMesh(self,ingr):
        o = ingr.recipe().organelle()
        geom = ingr.mesh   
        print ("createIngrMesh ",ingr.name, ingr.mesh, self.helper.getName(ingr.mesh) )
# START New section added by Graham on July 16, 2012 replaces section below
# This version allows the user to hide the parent geometry from the center of the scene very easily
# This version MAY NOT be safe outside of Cinema 4D  Can we test it ???
        vParentHiders = self.vi.getObject(self.name+"ParentHiders") #g
        if vParentHiders is None : #g
            vParentHiders=self.vi.newEmpty(self.name+"ParentHiders",parent=self.master) #g
        if self.vi.host.find("blender") == -1 :
            self.vi.toggleDisplay(vParentHiders,False)
        parent = self.vi.getObject(ingr.name+"MeshsParent") 
        
        if parent is None : #g
            parent=self.vi.newEmpty(ingr.name+"MeshsParent", parent=vParentHiders)#g
            print ("ok",ingr.name+"MeshsParent",vParentHiders,type(vParentHiders))            
#            self.vi.reParent(parent,vParentHiders)
#        else :
#            self.vi.reParent(parent,vParentHiders)
#        print("ingredient Mesh_3d to build",ingr.mesh_3d)#when reset should delete it
        if not hasattr(ingr,"mesh_3d") or ingr.mesh_3d is None :# or parent is None:  #mod by g
            #        if not hasattr(ingr,"mesh_3d") or ingr.mesh_3d is None or parent is None:  #off by g
            #            parent=self.vi.newEmpty(ingr.name+"MeshsParent", parent=self.orgaToMasterGeom[ingr]) # off by g
# END New section added by Graham on July 16, 2012    

# START original section removed by Graham on July 16, 2012
#        parent = self.vi.getObject(ingr.name+"MeshsParent")
#        if not hasattr(ingr,"mesh_3d") or ingr.mesh_3d is None or parent is None:
#            parent=self.vi.newEmpty(ingr.name+"MeshsParent", parent=self.orgaToMasterGeom[ingr])
# END original section removed by Graham on July 16, 2012
 
            #create the polygon    
            #from DejaVu.IndexedPolygons import IndexedPolygons 
            name = o.name+ingr.name+"Mesh"
            material = None
            if ingr.color != None :
                material=self.vi.retrieveColorMat(ingr.color)
#            print ("parent is ", ingr.name+"MeshsParent",vParentHiders,parent)
            if isinstance(geom,int):
                polygon = self.vi.createsNmesh(name,geom.getVertices(),None,
                                       geom.getFaces(),
                                       material=material,
                                       parent=parent)  
            else :
                polygon = self.vi.newInstance(name,geom,
                                       material=material,
                                       parent=parent)#identity?
            #self.vi.toggleDisplay(parent,False)
            if not self.visibleMesh : 
                self.vi.toggleDisplay(parent,False)
                self.vi.toggleDisplay(polygon[0],False)
#            self.vi.setTranslation(parent,pos=[1000.,1000.,1000.]) 
#            if self.vi.host.find("blender") != -1 :
#                self.orgaToMasterGeom[ingr]= polygon            
        if not hasattr(ingr,"mesh_3d") or ingr.mesh_3d is None:
            ingr.mesh_3d = parent#polygon[0] is this will work in other host
        print ("after build",ingr.mesh_3d)
#        self.vi.reParent(parent,vParentHiders)
        
    def displayIngrMesh(self,matrices,ingr):
        matrices[ingr] = []
        #ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)
        if self.ViewerType != 'dejavu':
            self.createIngrMesh(ingr)
        else :
            ingr.mesh_3d = ingr.mesh
            if ingr.color != None :
                ingr.mesh.Set(materials=[ingr.color], inheritMaterial=0)
            
    def printOneIngr(self,ingr):
        print(ingr.name, ingr.molarity,ingr.pdb,ingr.principalVector,\
                ingr.packingPriority,ingr.jitterMax)

    def printIngrediants(self):
        r =  self.histo.exteriorRecipe
        if r :
            res = [self.printOneIngr(ingr) for ingr in r.ingredients]                 
        for orga in self.histo.organelles:
            rs =  orga.surfaceRecipe
            if rs :
                res =[self.printOneIngr(ingr) for ingr in rs.ingredients]  
            ri =  orga.innerRecipe
            if ri:
                res = [self.printOneIngr(ingr) for ingr in ri.ingredients]  

    def collectResult(self,ingr,pos,rot):
        verts=[]
        radii=[]
        level = ingr.maxLevel
        px = ingr.transformPoints(pos, rot, ingr.positions[level])
        if ingr.modelType=='Spheres':
            for ii in range(len(ingr.radii[level])):
                verts.append( px[ii] )
                radii.append( ingr.radii[level][ii] )
        elif ingr.modelType=='Cylinders':
            px2 = ingr.transformPoints(pos, rot, ingr.positions2[level])
            for ii in range(len(ingr.radii[level])):
                verts.append( px[ii] )
                verts.append( px2[ii] )
                radii.append( ingr.radii[level][ii] )
                radii.append( ingr.radii[level][ii] )
        mat = rot.copy()
        mat[:3, 3] = pos
        return verts,radii,numpy.array(mat)

    def replaceIngrMesh(self,ingredient, newMesh):
        polygon = ingredient.mesh_3d
        o = self.vi.getObject(polygon)#should be an empty or locator
        childs = self.vi.getChilds(o)  
        instance = None
        if not len(childs):
            print ("no Childs")
        else :
            instance = childs[0]
#        print (polygon,instance,newMesh)
#        if self.vi.host == "maya" :
#            instance = ingredient.mesh
        if self.vi.host.find("blender") != -1 :
            instance = self.orgaToMasterGeom[ingredient]
        elif self.vi.host == "dejavu" or self.vi.host == "softimage":
            instance = polygon
#        print (polygon,instance,newMesh)
        self.vi.updateMasterInstance(instance,[newMesh])
        if self.vi.host.find("blender") != -1 :
            newMesh = self.vi.getObject(newMesh)
            #ingredient.mesh_3d = newMesh
            self.orgaToMasterGeom[ingredient] = newMesh#permit to toggle the display
            self.vi.setLayers(newMesh,[1])
            
    def displayIngrResults(self,ingredient,doSphere=False,doMesh=True):
        """
        Display the result for the given ingr after filling
        """
        
        if ingredient is None :
            print ("no ingredient provided")
            return
        o =  ingredient.recipe().organelle()
#        comp = ingredient.compNum
        verts = []
        radii = []
        matrices = []
        #retrieve the result from the molecules array of the recipes
        res = [self.collectResult(ingr,pos,rot) \
                                    for pos, rot, ingr, ptInd in o.molecules \
                                    if ingr == ingredient]
        
        for r in res :
            verts.extend(r[0])
            radii.extend(r[1])
            matrices.append(r[2])
        print ("collected ",len(res),len(matrices),doMesh)
        if doSphere and verts:
            if ingredient.modelType=='Spheres':
                self.displayIngrSpheres(ingredient,{ingredient:verts},
                                        {ingredient:radii},visible=1)
            elif ingredient.modelType=='Cylinders':
                self.displayIngrCylinders(ingredient,{ingredient:verts},
                                          {ingredient:radii},visible=1)
        if doMesh and matrices:
            dejavui = False
            #recipe can be orga name or cyto_
            #o =  ingredient.recipe().organelle()
#            geom = ingredient.mesh     
            if self.ViewerType != 'dejavu':
                polygon = ingredient.mesh_3d
                if polygon is None :
                    self.createIngrMesh(ingredient)
                    polygon = ingredient.mesh_3d
                name = "Meshs_"+ingredient.name.replace(" ","_")
                parent = self.vi.getObject(name)
                if parent is None :
                    parent=self.vi.newEmpty(name, parent=self.orgaToMasterGeom[ingredient])
#                    self.vi.AddObject(parent)
                instances = self.vi.getChilds(parent)  
                dejavui = not len(instances)
            if not hasattr(ingredient,'ipoly') or ingredient.ipoly is None or dejavui:
                color = [ingredient.color] if ingredient.color is not None else None
#                print o.name+self.histo.FillName[self.histo.cFill]+ingredient.name
                ingredient.ipoly = self.vi.instancePolygon(o.name+self.histo.FillName[self.histo.cFill]+ingredient.name,
                                        matrices=matrices,
                                        mesh=polygon,parent = parent,
                                        transpose= True,colors=color,
                                        axis=ingredient.principalVector)
        
    
    def displayInstancesIngredient(self,ingredient, matrices):
#        geom = ingredient.mesh     
        if self.ViewerType != 'dejavu':
            polygon = ingredient.mesh_3d
            if polygon is None :
                self.createIngrMesh(ingredient)
                polygon = ingredient.mesh_3d
            name = "Meshs_"+ingredient.name.replace(" ","_")
            parent = self.vi.getObject(name)
            if parent is None :
                parent=self.vi.newEmpty(name, parent=self.orgaToMasterGeom[ingredient])
#                    self.vi.AddObject(parent)
            ingredient.ipoly = self.vi.instancePolygon(self.histo.FillName[self.histo.cFill]+ingredient.name,
                                        matrices=matrices,
                                        mesh=polygon,parent = parent,
                                        transpose= True,colors=[ingredient.color],
                                        axis=ingredient.principalVector)
        
    def displayCytoplasmIngredients(self):
        verts = {}
        radii = {}
        r =  self.histo.exteriorRecipe
        ningr =0
        if r :
            ningr=len(r.ingredients)
            for ingr in r.ingredients:
                verts[ingr] = []
                radii[ingr] = []
        else :
            return
        if self.doSpheres :
            for pos, rot, ingr, ptInd in self.histo.molecules:
                level = ingr.maxLevel
                px = ingr.transformPoints(pos, rot, ingr.positions[level])
                if ingr.modelType=='Spheres':
                    for ii in range(len(ingr.radii[level])):
                        verts[ingr].append( px[ii] )
                        radii[ingr].append( ingr.radii[level][ii] )
                elif ingr.modelType=='Cylinders':
                    px2 = ingr.transformPoints(pos, rot, ingr.positions2[level])
                    for ii in range(len(ingr.radii[level])):
                        verts[ingr].append( px[ii] )
                        verts[ingr].append( px2[ii] )
                        radii[ingr].append( ingr.radii[level][ii] )
                        radii[ingr].append( ingr.radii[level][ii] )                    
#        ingr.verts = verts[ingr]
#        ingr.rad = radii[ingr]
        # display cytoplasm spheres
        #if self.doSpheres :#or ingr.mesh is None:
            if r :
                for ingr in r.ingredients:
#                    self.displayIngrSpheres(ingr,verts,radii)
                    if ingr.modelType=='Spheres':
                        self.displayIngrSpheres(ingr,verts,radii,visible=1)
                    elif ingr.modelType=='Cylinders':
                        print(ingr.name,verts)
                        self.displayIngrCylinders(ingr,verts,radii,visible=1)
         
        # display cytoplasm meshes
        r =  self.histo.exteriorRecipe
        if r :
            meshGeoms = {}#self.meshGeoms#{}
            inds = {}
            for pos, rot, ingr, ptInd in self.histo.molecules:
                #print "ingr",ingr,ingr.mesh,ingr.mesh_3d                
                if ingr.mesh: # display mesh
#                    geom = ingr.mesh
                    mat = rot.copy()
                    mat[:3, 3] = pos
                    if self.helper.host == 'dejavu':
                        mry90 = self.helper.rotation_matrix(-math.pi/2.0, [0.0,1.0,0.0])#?
                        mat = numpy.array(numpy.matrix(mat)*numpy.matrix(mry90))
                    if ingr not in meshGeoms:
                        inds[ingr] = [ptInd]
                        meshGeoms[ingr] = [mat]
                        if self.ViewerType != 'dejavu':
                            self.createIngrMesh(ingr)
                        #else :
                        #    geom.Set(materials=[ingr.color], inheritMaterial=0, visible=0)
                    else:
                        inds[ingr].append(ptInd)
                        meshGeoms[ingr].append(mat)
                        #if self.ViewerType == 'dejavu': 
                        #    self.vi.AddObject(geom, parent=self.orgaToMasterGeom[ingr])
            j=0
            for ingr in r.ingredients:
                #self.vi.progressBar(j/ningr,label="instances for "+str(j)+" "+ingr.name+" "+str(len(meshGeoms[ingr]))) 
                geom = ingr.mesh
                #geom.Set(instanceMatrices=meshGeoms[ingr], visible=1)        
                #if self.ViewerType != 'dejavu':
                    #find the polygon and the ingr?#polygon = ingr.mesh_3d
                polygon = ingr.mesh_3d
                name = "Meshs_"+ingr.name.replace(" ","_")
                parent = self.vi.getObject(name)
                if parent is None :
                    parent=self.vi.newEmpty(name, parent=self.orgaToMasterGeom[ingr])
#                    self.vi.AddObject(parent)
                if self.helper.host == 'dejavu':
                    parent = None
                if ingr not in meshGeoms:
                    continue
                ingr.ipoly = self.vi.instancePolygon("cyto_"+self.histo.FillName[self.histo.cFill]+ingr.name,
                                            matrices=meshGeoms[ingr],
                                            mesh=polygon,parent = parent,
                                            transpose= True,colors=[ingr.color],
                                            axis=ingr.principalVector)
#                if self.doOrder :
                #print ingr.ipoly
                if self.vi.host.find("blender") != -1 :
                    self.orgaToMasterGeom[ingr] = polygon
                    if not self.vi.dupliVert :
                        self.vi.setLayers(polygon,[1])#and do it for child too.
                elif self.vi.host == "dejavu" or self.vi.host == "softimage":
                    self.orgaToMasterGeom[ingr] = ingr.mesh
                if self.helper.host != 'dejavu':
                    if type(ingr.ipoly) != list : return
                    for i,ip in enumerate(ingr.ipoly):
    #                    print i,ip,type(ip)
                        name = self.vi.getName(ip)
                        if inds[ingr][i] in self.histo.order:
    #                        print name,name+"_"+str(self.histo.order[inds[ingr][i]])
                            self.vi.setName(ip,name+"_"+str(self.histo.order[inds[ingr][i]]))
#                self.vi.progressBar(j/ningr,label="instances for "+str(j)+" "+ingr.name+" "+str(len(meshGeoms[ingr]))) 
                j+=1
                
    def displayOrganellesIngredients(self):
        # display organelle ingredients
        for orga in self.histo.organelles:
            #Sphere and Cylinders
            verts = {}
            radii = {}
            rs =  orga.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    verts[ingr] = []
                    radii[ingr] = []
            ri =  orga.innerRecipe
            if self.doSpheres :
                if ri:
                    for ingr in ri.ingredients:
                        verts[ingr] = []
                        radii[ingr] = []
                for pos, rot, ingr, ptInd in orga.molecules:
                    level = ingr.maxLevel
                    px = ingr.transformPoints(pos, rot, ingr.positions[level])
                    if ingr.modelType=='Spheres':
                        for ii in range(len(ingr.radii[level])):
                            verts[ingr].append( px[ii] )
                            radii[ingr].append( ingr.radii[level][ii] )
                    elif ingr.modelType=='Cylinders':
                        px2 = ingr.transformPoints(pos, rot, ingr.positions2[level])
                        for ii in range(len(ingr.radii[level])):
                            verts[ingr].append( px[ii] )
                            verts[ingr].append( px2[ii] )
                            radii[ingr].append( ingr.radii[level][ii] )
#                            radii[ingr].append( ingr.radii[level][ii] )
                        
            #if self.doSpheres :
                if rs :
                    for ingr in rs.ingredients:
                        if len(verts[ingr]):
                            if ingr.modelType=='Spheres':
                                self.displayIngrSpheres(ingr,verts,radii,visible=0)
                            elif ingr.modelType=='Cylinders':
                                print('display',ingr.name)
                                self.displayIngrCylinders(ingr,verts,radii,visible=1)
                if ri:
                    for ingr in ri.ingredients:
                        if len(verts[ingr]):
                            if ingr.modelType=='Spheres':
                                self.displayIngrSpheres(ingr,verts,radii,visible=0)
                            elif ingr.modelType=='Cylinders':
                                self.displayIngrCylinders(ingr,verts,radii,visible=1)
                                    
            #Meshs
            matrices = {}
            rs =  orga.surfaceRecipe
#            if rs :
#                for ingr in rs.ingredients:
#                    if ingr.mesh: # display mesh
#                        self.displayIngrMesh(matrices,ingr)
#            ri =  orga.innerRecipe
#            if ri :
#                for ingr in ri.ingredients:
#                    if ingr.mesh: # display mesh
#                        self.displayIngrMesh(matrices,ingr)
            for pos, rot, ingr, ptInd in orga.molecules:
                if ingr.mesh: # display mesh
#                    geom = ingr.mesh
                    #print ingr,ingr.mesh.name
                    #print pos                          
                    mat = rot.copy()
                    mat[:3, 3] = pos
                    if self.helper.host == 'dejavu':
                        mry90 = self.helper.rotation_matrix(-math.pi/2.0, [0.0,1.0,0.0])
                        mat = numpy.array(numpy.matrix(mat)*numpy.matrix(mry90))

                    if ingr not in matrices:
                        matrices[ingr] = []
                    matrices[ingr].append(mat)
#                    if self.ViewerType == 'dejavu': 
#                        self.vi.AddObject(geom, parent=self.orgaToMasterGeom[ingr])
#                    else :
                    if not hasattr(ingr,'mesh_3d') or ingr.mesh_3d is None :
                        if self.ViewerType == 'dejavu': 
                            ingr.mesh_3d = ingr.mesh
                        else :
                            self.createIngrMesh(ingr) 
            print("nbMAtrices",len(matrices))
            if ri :
                ningri=len(ri.ingredients)
                j=0
                for ingr in ri.ingredients:
                    if ingr.mesh:
#                        self.vi.progressBar(j/ningri,label="instances for "+str(j)+" "+ingr.name+" "+str(len(matrices[ingr]))) 
                        geom = ingr.mesh
                        #geom.Set(instanceMatrices=matrices[ingr], visible=1)        
#                        if self.ViewerType != 'dejavu':
                            #find the polygon and the ingr?#polygon = ingr.mesh_3d
                        polygon = ingr.mesh_3d
                        name = "Meshs_"+ingr.name.replace(" ","_")
                        parent = self.vi.getObject(name)
                        if ingr not in matrices:
                            continue
                        else :
                            print(name,len(matrices[ingr]))
                        if parent is None :
                            parent=self.vi.newEmpty(name, parent=self.orgaToMasterGeom[ingr])
                            self.vi.AddObject(parent)
                        if self.helper.host == 'dejavu':
                            parent = None                           
                        print("ri instanciation of polygon",polygon)
                        ingr.ipoly = self.vi.instancePolygon(orga.name+self.histo.FillName[self.histo.cFill]+ingr.name,
                                                    matrices=matrices[ingr],
                                                    mesh=polygon,
                                                    parent = parent,
                                                    transpose=True,colors=[ingr.color],
                                                    axis=ingr.principalVector)
                        if self.vi.host.find("blender") != -1 :
                            self.orgaToMasterGeom[ingr] = polygon
                            if not self.vi.dupliVert : 
                                self.vi.setLayers(polygon,[1])#and do it for child too.
                        elif self.vi.host == "dejavu":
                            self.orgaToMasterGeom[ingr] = ingr.mesh
                        elif self.vi.host == "softimage":
                            self.orgaToMasterGeom[ingr] = ingr.mesh#self.getMasterInstance(polygon)
                            #polygon already an instance from a different object\
                            
                    j+=1
            if rs:
                ningrs=len(rs.ingredients)
                j=0
                for ingr in rs.ingredients:
                    if ingr.mesh:
                        geom = ingr.mesh
#                        geom.Set(instanceMatrices=meshGeoms[ingr], visible=1)        
#                        if self.ViewerType != 'dejavu':
                        #find the polygon and the ingr?#polygon = ingr.mesh_3d
                        polygon = ingr.mesh_3d
                        name = "Meshs_"+ingr.name.replace(" ","_")
                        parent = self.vi.getObject(name)
                        if ingr not in matrices:
                            continue
                        else :
                            print(name,len(matrices[ingr]))                        
#                        self.vi.progressBar(j/ningrs,label="instances for "+str(j)+" "+ingr.name+" "+str(len(matrices[ingr]))) 
                        if parent is None :
                            parent=self.vi.newEmpty(name, parent=self.orgaToMasterGeom[ingr])
#                            self.vi.AddObject(parent)
                        if self.helper.host == 'dejavu':
                            parent = None                           
                        print("rs instanciation of polygon",polygon)
                        ingr.ipoly = self.vi.instancePolygon(orga.name+self.histo.FillName[self.histo.cFill]+ingr.name,
                                                    matrices=matrices[ingr],
                                                    mesh=polygon,
                                                    parent = parent,
                                                    transpose= True,colors=[ingr.color],
                                                    axis=ingr.principalVector)            
                        if self.vi.host.find("blender") != -1 :
                            self.orgaToMasterGeom[ingr] = polygon
                            if not self.vi.dupliVert :
                                self.vi.setLayers(polygon,[1])#and do it for child too.
                        elif self.vi.host == "dejavu":
                            self.orgaToMasterGeom[ingr] = ingr.mesh
                    j+=1

    
    def appendIngrInstance(self,ingr,sel = None,bb=None):
        if self is None :
            sel = self.helper.getCurrentSelection()
        #should have a parent and take all children or take all selection
        #what about the ptId
        #molecules is [pos, rot, ingr, ptInd]
        #whats the compartiments, so the ingr have to be reviously add to a compartiments
        orga = ingr.recipe().organelle()#what if it is cytoplsme?
        #res = o.molecules[:]
        res=[]
        if self.histo.grid is None :
            if bb is None :
                bb=self.histo.boundingBox
            spacing = self.histo.smallestProteinSize*1.1547
            v,nb = self.histo.computeGridNumberOfPoint(bb,spacing)
        for o in sel:
            if self.helper.getType(o) == self.helper.EMPTY:
                childs = self.helper.getChilds(o)
                for ch in childs:
#                    name = self.helper.getName(ch)
                    rotMatj = self.helper.getMatRotation(ch)
                    jtrans = self.helper.ToVec(self.helper.getTranslation(ch))
                    ptId = self.histo.getPointFrom3D(jtrans,bb,spacing,nb)
                    res.append([jtrans,rotMatj,ingr,ptId])
                    #need to handle the PtID none
            else :
                rotMatj = self.helper.getMatRotation(o)
                jtrans = self.helper.ToVec(self.helper.getTranslation(o))
                ptId = self.histo.getPointFrom3D(jtrans,bb,spacing,nb)
                res.append([jtrans,rotMatj,ingr,ptId])
        ingr.counter = 0
        orga.molecules.extend(res)

#    def displayFreePoints(self):
#        # display grid points with positive distances left
#        verts = []
#        rads = []
#        fpts = self.histo.freePointsAfterFill[:self.histo.nbFreePointsAfterFill]
##        if self.histo.use_clist : 
##            fpts = self.histo.lmethod.get_valuesL(self.histo.freePointsAfterFill)
#        #for i in xrange(self.histo.nbFreePointsAfterFill-1):
#        #    pt = fpts[i]
#        for pt in self.histo.freePointsAfterFill[:self.histo.nbFreePointsAfterFill]:
#            d = self.histo.distancesAfterFill[pt]
#            if d>self.histo.smallestProteinSize-0.001:
#                verts.append(self.histo.masterGridPositions[pt])
#                rads.append(d)
#        if self.ViewerType == 'dejavu':
#            if len(verts):
#                sph1 = self.vi.Spheres('unusedSph', centers=verts, radii=rads, 
#                                       inheritFrontPolyMode=0,
#                                       frontPolyMode='line', visible=0)
#                self.vi.AddObject(sph1)
#
#        if len(verts):
#            #unusedPtsds
#            pts1 = self.vi.Points('zeroDistPts', vertices=verts, inheritPointWidth=0,
#                          pointWidth=self.pointWidth, inheritMaterial=0, materials=[(0,1,0)], visible=0,
#                          parent=None)
#            verts = []
#            for pt in fpts:#[:self.histo.nbFreePointsAfterFill]:
#                verts.append(self.histo.masterGridPositions[pt])
#        
#            unpts = self.vi.Points('unusedGridPoints', vertices=verts, inheritMaterial=0,
#                          materials=[green], visible=0,parent=None)
#            verts = []
#            for pt in fpts:#[self.histo.nbFreePointsAfterFill:]:
#                verts.append(self.histo.masterGridPositions[pt])
#        
#            uspts = self.vi.Points('usedGridPoints', vertices=verts, inheritMaterial=0,
#                          materials=[red], visible=0,parent=None)
#            
#            if self.ViewerType == 'dejavu':
#                self.vi.AddObject(pts1)
#                self.vi.AddObject(unpts)
#                self.vi.AddObject(uspts)

                    
    def displayFreePoints(self, vDebug=0):
        # display grid points with positive distances left
        vertsFreePts = []
        vertsAll = []  #Graham debugTrashLine
        verts = []
        rads = []
        fpts = self.histo.freePointsAfterFill[:self.histo.nbFreePointsAfterFill]
        NPTS = len(self.histo.masterGridPositions) # or self.histo.grid.gridVolume
        #        for pt in self.histo.freePointsAfterFill[:self.histo.nbFreePointsAfterFill]:
        #        for pt in self.histo.freePointsAfterFill:
        for pt in range(NPTS):
            vertsAll.append(self.histo.masterGridPositions[pt])  #Graham debugTrashLine
            d = self.histo.distancesAfterFill[pt]
            #            print("distAfterFill for pt ", pt," = ", d)
            if d>self.histo.smallestProteinSize-0.001:
                verts.append(self.histo.masterGridPositions[pt])
                rads.append(d)
        if self.ViewerType == 'dejavu':
            if len(verts):
                sph1 = self.vi.Spheres('unusedSph', centers=verts, radii=rads, 
                                       inheritFrontPolyMode=0,
                                       frontPolyMode='line', visible=0)
                self.vi.AddObject(sph1)
        
        if len(verts):
            #unusedPtsds
            #           ptsAll = self.vi.Points('AllPoints', vertices=verts, inheritPointWidth=0,
            #                         pointWidth=self.pointWidth, inheritMaterial=0, materials=[(0,1,0)], visible=0,
            #                         parent=None)
            
            verts0 = []
            vertsIn = []
            vertsOut = []
            
            #      for pt in fpts:#[:self.histo.nbFreePointsAfterFill]:
            for pt in range(NPTS):
                #            for pt in self.histo.freePointsAfterFill:
                d = self.histo.distancesAfterFill[pt]
                #                print("d for pt ", pt," = ", d)
                if d==0:
                    verts0.append(self.histo.masterGridPositions[pt])    
                #   print("Verts0 adding d==0 for pt = ", pt)
                elif d<0:
                    vertsIn.append(self.histo.masterGridPositions[pt])
                #   print("VertsIn adding d<0 for pt = ", pt)
                elif d>0:
                    vertsOut.append(self.histo.masterGridPositions[pt])
            
            for pt in fpts :
                    vertsFreePts.append(self.histo.masterGridPositions[pt])
            #   print("VertsOut adding d>0 for pt = ", pt)

                        #         ptsFull = self.vi.Points('completeDistPts', vertices=vertsAll, inheritMaterial=0,   #Graham debugTrashLine
            #           materials=[blue], visible=0, parent=None)  #Graham debugTrashLine
            vDebug=0 # Aug 19, 2012: Set vDebug = 1 if you want the grids to be at top of hierarchy for easy access
            vParent = self.master
            if vDebug:
                vParent = None
            vGridPointHider = self.vi.getObject(self.name+"GridPointHider") #g
            if vGridPointHider is None : #g
                vGridPointHider=self.vi.newEmpty(self.name+"GridPointHider",parent=vParent)
            #if self.ViewerType != 'dejavu':
            #    #define the base shape for instance objects
            if self.psph is None:
                self.psph=self.vi.newEmpty(self.name+"base_shape",parent=vParentHiders)
                        
            
            ptsAll = self.vi.Points('allDistPts', vertices=vertsAll,inheritPointWidth=0, #Graham debugTrashLine
                                    pointWidth=self.pointWidth, inheritMaterial=0,
                                    materials=[blue], visible=0, parent=vGridPointHider) 
            
            pts0 = self.vi.Points('zeroDistPts', vertices=verts0, inheritPointWidth=0,
                                    pointWidth=self.pointWidth, inheritMaterial=0, 
                                    materials=[(0,1,0)], visible=0, parent=vGridPointHider)
            #            verts = []
            #            for pt in fpts:#[:self.histo.nbFreePointsAfterFill]:
            #                d = self.histo.distancesAfterFill[pt]
            #                if d>0:
            #                    verts.append(self.histo.masterGridPositions[pt])
            
            unUspts = self.vi.Points('UnusedGridPoints', vertices=vertsOut, inheritPointWidth=0,
                                     pointWidth=self.pointWidth, inheritMaterial=0,
                                     materials=[green], visible=0,parent=vGridPointHider)
    
            ptsFree = self.vi.Points('FreePoints', vertices=vertsFreePts, inheritPointWidth=0,  #Graham debugTrashLine
                                     pointWidth=self.pointWidth, inheritMaterial=0, 
                                     materials=[orange], visible=0, parent=vGridPointHider)  
            #            verts = []
            #            for pt in fpts:#[self.histo.nbFreePointsAfterFill:]:
            #                d = self.histo.distancesAfterFill[pt]
            #                if d<=0:
            #                    verts.append(self.histo.masterGridPositions[pt])
            
            Uspts = self.vi.Points('UsedGridPoints', vertices=vertsIn, inheritPointWidth=0,
                                    pointWidth=self.pointWidth, inheritMaterial=0,
                                    materials=[red], visible=0,parent=vGridPointHider)
            
            if self.ViewerType == 'dejavu':
                #              self.vi.AddObject(ptsAll)
                self.vi.AddObject(pts0)
                self.vi.AddObject(unUspts)
                self.vi.AddObject(Uspts)
 
    def dspMesh(self,geom):
        #specific to C4D
        if self.ViewerType != 'dejavu':
            for ch in geom.GetDown()():
                if ch.GetName() == "Meshs":
                    self.vi.toggleDisplay(ch,True)                        
        else :
            for c in geom.children:
                if c.name=='mesh':
                    c.Set(visible=1)
                    
    def undspMesh(self,geom):
        if self.ViewerType != 'dejavu':
            for ch in geom.GetDown():
                if ch.GetName() == "Meshs":
                    self.vi.toggleDisplay(ch,False)                        
        else :
            for c in geom.children:
                if c.name=='mesh':
                    c.Set(visible=0)
    
    def dspSph(self,geom):
        if self.ViewerType != 'dejavu':
            for ch in geom.GetDown():
                if ch.GetName() == "spheres":
                    self.vi.toggleDisplay(ch,True)                        
        else :
            for ch in geom.children:
                if ch.name=='spheres':
                    ch.Set(visible=1)
    
    def undspSph(self,geom):
        if self.ViewerType!= 'dejavu':
            for ch in geom.GetDown():
                if ch.GetName() == "spheres":
                    self.vi.toggleDisplay(ch,False)                        
        else :
            for ch in geom.children:
                if ch.name=='spheres':
                    ch.Set(visible=0)
    
    def showHide(self,func):
        r =  self.histo.exteriorRecipe
        if r :
            for ingr in r.ingredients:
                master = self.orgaToMasterGeom[ingr]
                func(master)
        for orga in self.histo.organelles:
            rs =  orga.surfaceRecipe
            if rs :
                for ingr in rs.ingredients:
                    master = self.orgaToMasterGeom[ingr]
                    func(master)
            ri =  orga.innerRecipe
            if ri:
                for ingr in ri.ingredients:
                    master = self.orgaToMasterGeom[ingr]
                    func(master)
#==============================================================================
# custom filling
#==============================================================================
    def createTemplate(self,**kw):
        self.prepareMaster()
        self.displayHistoVol()
#        g = self.vi.newEmpty("--------------",parent=self.master)
        setup = self.vi.newEmpty(self.name+"_Setup",parent=self.master)        
        g = self.vi.newEmpty(self.name+'_organelles_name_geometries',parent=setup)
        orgamesh = self.vi.newEmpty("Place here your organelles geometries",parent=g)
        name = self.name+'_cytoplasm_ingredient'
        g = self.vi.newEmpty(self.name+'_cytoplasm_ingredient',parent=setup)
        ingrcyto = self.vi.newEmpty("Place here your cytoplasm ingredients",parent=g)
        
        g = self.vi.newEmpty(self.name+'_organelles_recipes',parent=setup)
        s = self.vi.newEmpty('Setup following the template',parent=g)
        r = self.vi.newEmpty('organellename_recipe',parent=g)
        rs = self.vi.newEmpty('organellename_surface',parent=r)
        ingrorga = self.vi.newEmpty("Place here your surface ingredients",parent=rs)
        ri = self.vi.newEmpty('organellename_interior',parent=r)
        ingrorga = self.vi.newEmpty("Place here your interior ingredients",parent=ri)
        
    def createTemplateOrganelle(self,organame,**kw):
        parent= self.vi.getObject(self.name+'_organelles_recipes')
        r = self.vi.getObject(organame+'_recipe')
        if r is None :
            r = self.vi.newEmpty(organame+'_recipe',parent=parent)
        rs = self.vi.getObject(organame+'_surface')
        if rs is None :
            rs = self.vi.newEmpty(organame+'_surface',parent=r)
            ingrorga = self.vi.newEmpty("Place here your surface ingredients "+organame,parent=rs)
        ri = self.vi.getObject(organame+'_interior')
        if ri is None :
            ri = self.vi.newEmpty(organame+'_interior',parent=r)
            ingrorga = self.vi.newEmpty("Place here your interior ingredients"+organame,parent=ri)
        
    
    def addIngredientFromGeom(self,name, ingrobj, recipe=None, **kw):
        #print ("######ADD",ingrobj, self.helper.getName(ingrobj),self.helper.getType(ingrobj))
        ingr = None 
        obj = ingrobj
        if self.helper.getType(ingrobj) == self.helper.INSTANCE :
            obj = self.helper.getMasterInstance(ingrobj)
        if self.helper.getType(obj) == self.helper.EMPTY :
            child = self.helper.getChilds(obj)
            nchilds = len(child)
            #the ingredient is composed by theses different childs that ca be n sphere n cylinder 1 cube, and n instance of ...
            #which is a spheretree, or a cylindertree    
            #get the first one to recognized the type
            if not nchilds :
                print ("PROBLEM")
                return None 
            child0=child[0]
            ingtype = self.helper.getType(child0)
            if ingtype == self.helper.INSTANCE :
                child0 = self.helper.getMasterInstance(child0)
                ingtype = self.helper.getType(child0)
            if ingtype == self.helper.SPHERE :
                from AutoFill.Ingredient import MultiSphereIngr
                positions=[]
                radius = []
                for io in child :
                    #get the radius and the translation
                    pos,s,r = self.helper.getPropertyObject(io,key=["pos","scale","radius"])
                    if self.helper.getType(io) == self.helper.INSTANCE :
                        r = self.helper.getPropertyObject(self.helper.getMasterInstance(io),key=["radius"])[0]
                    positions.append(pos)
                    radius.append(r*s[0])#should be one
#                    self.helper.Sphere(self.helper.getName(io)+"_sp",radius=r)
                ingr = MultiSphereIngr(1.0, name=name, 
                    radii=[radius],positions=[positions], 
                    meshObject=obj)
#                print("spheres ",positions)
            if ingtype == self.helper.CYLINDER :
                from AutoFill.Ingredient import MultiCylindersIngr
                positions=[]
                positions2=[]
                radius = []
                axis = self.helper.getPropertyObject(child[0],key=["axis"])[0]
                for io in child :
                    #get the radius and the translation
                    s = self.helper.getPropertyObject(io,key=["scale"])[0]
                    if self.helper.getType(io) == self.helper.INSTANCE :
                        io = self.helper.getMasterInstance(io)
                    r = self.helper.getPropertyObject(io,key=["radius"])[0]
                    head,tail = self.helper.CylinderHeadTails(io)
                    positions.append(tail)
                    positions2.append(head)
                    radius.append(r*s[0])
#                    self.helper.oneCylinder(self.helper.getName(io)+"_cyl",head,tail,radius=r)
                ingr = MultiCylindersIngr(1.0, name=name, 
                    radii=[radius],positions=[numpy.array(positions)], positions2=[numpy.array(positions2)],
                    meshObject=obj,
                    principalVector=axis)
#                print (name, [radius],[positions],[positions2]) 
            if ingtype == self.helper.CUBE :
                from AutoFill.Ingredient import SingleCubeIngr
                #need to create a SphereIngredient
                s = self.helper.getPropertyObject(child0,key=["scale"])[0]
                if self.helper.getType(child0) == self.helper.INSTANCE :
                    child0 = self.helper.getMasterInstance(io)
                size = self.helper.getPropertyObject(child0,key=["length"])[0]
                ingr = SingleCubeIngr( 1.0,  [self.helper.ToVec(size*s[0]),],name=name,
                                  positions=[[[0,0,0],[0,0,0],[0,0,0],]],
                                    meshObject=obj,)
        if self.helper.getType(obj) == self.helper.SPHERE :
            from AutoFill.Ingredient import SingleSphereIngr
            #need to create a SphereIngredient
            ingr = SingleSphereIngr( 1.0, 
                    name=name,
                    radius=self.helper.getPropertyObject(obj,key=["radius"])[0],
#                    meshFile=wrkDir+'/'+k+'/'+ing_name,
                    meshObject = ingrobj)
            #compartiment ?
        elif self.helper.getType(obj) == self.helper.CYLINDER :
            from AutoFill.Ingredient import MultiCylindersIngr
            #need to create a SphereIngredient
            r,h,axis = res = self.helper.getPropertyObject(obj,key=["radius","length","axis"])
            ingr = MultiCylindersIngr(1.0, name=name, 
                radii=[[r,]],positions=[[[0,-h/2.,0]]], 
                positions2=[[[0,h/2.,0]]],
                meshObject=ingrobj,
#                jitterMax=(1.,1.,1.),#how to customize
#                rotAxis=(0.,0.,1.0),#how to customize
#                nbJitter = 10,
                #  CRITICAL !!! IF jitter is greater than radius of object, 
                #e.g. 5x(1,1,1) the point may not be consumed!!!
                principalVector=axis,#should come from the object
                )
        elif self.helper.getType(obj) == self.helper.CUBE :
            from AutoFill.Ingredient import SingleCubeIngr
            #need to create a SphereIngredient
            size = self.helper.getPropertyObject(obj,key=["length"])[0]
            ingr = SingleCubeIngr( 1.0,  [self.helper.ToVec(size),],name=name,
                              positions=[[[0,0,0],[0,0,0],[0,0,0],]],
                                meshObject=ingrobj,)
        if ingr is not None:
            if recipe == None:
                self.histo.exteriorRecipe.addIngredient(ingr)
                ingr.compNum = 0
                g = self.vi.getObject(self.name+'_cytoplasm')
                self.addMasterIngr(ingr,parent=g)
                ingr.histoVol = self.histo
            else :
                recipe.addIngredient( ingr ) 
                o = recipe.organelle()
                ingr.compNum = recipe.number
                g = self.vi.getObject("O"+o.name)
                ingr.histoVol = self.histo
            rep = self.vi.getObject(ingr.name+'_mesh')
            print (ingr.name+'_mesh is',rep)
            if rep is not None :
               ingr.mesh=rep
               ingr.use_mesh_rb=True
            self.addMasterIngr(ingr,parent=g)
        return ingr

    
    def addOrganelleFromGeom(self,name, obj, **kw):
        from AutoFill.Organelle import Organelle
        o1 = None
        print ("ADD ORGA",name,obj,self.helper.getType(obj) ) 
        if self.helper.getType(obj) == self.helper.EMPTY: #Organelle master parent?
            childs = self.helper.getChilds(obj)
            for ch in childs:
                chname = self.helper.getName(ch)
                if self.helper.host == "maya" :
                    if chname.find("Shape") == -1 :
                        name=chname
                else :
                    name=chname
                print ("name 1 org",name)
#                print name,helper.getType(ch),helper.EMPTY,helper.POLYGON
                if self.helper.getType(ch) == self.helper.EMPTY:
                    c = self.helper.getChilds(ch)
                    #should be all polygon
                    faces=[]
                    vertices=[]
                    vnormals=[]
                    for pc in c :
                        f,v,vn = self.helper.DecomposeMesh(pc,edit=False,
                                                copy=False,tri=True,transform=True)
                        faces.extend(f)
                        vertices.extend(v)
                        vnormals.extend(vn)
                    o1 = Organelle(name,vertices, faces, vnormals)
                    o1.overwriteSurfacePts = True
                elif self.helper.getType(ch) == self.helper.POLYGON :
                    #each childs is polygin ->organelle                
                    faces,vertices,vnormals = self.helper.DecomposeMesh(ch,
                                    edit=False,copy=False,tri=True,transform=True)
                    o1 = Organelle(name,vertices, faces, vnormals)
                    o1.overwriteSurfacePts = True
                else :
                    continue
#                h1.addOrganelle(o1)
#                if rSurf.has_key(name): 
#                    if rSurf[name].ingredients:
#                        r  = rSurf[name]
#                        o1.setSurfaceRecipe(r)
#                if rMatrix.has_key(name):
#                    if rMatrix[name].ingredients:
#                        r = rMatrix[name]
#                        o1.setInnerRecipe(r)
#                print o1.name,o1.number
        elif self.helper.getType(obj) == self.helper.POLYGON :
            c4dorganlle = obj
            nname = self.helper.getName(obj)
            if self.helper.host == "maya" :
                if nname.find("Shape") == -1 :
                    name=nname
            else :
                name=nname            #name = self.helper.getName(obj)
            print ("name 2 org",name)
            #helper.triangulate(c4dorganlle)
            faces,vertices,vnormals = self.helper.DecomposeMesh(c4dorganlle,
                                    edit=False,copy=False,tri=True,transform=True)
            o1 = Organelle(name,vertices, faces, vnormals)
            o1.overwriteSurfacePts = True
        return o1        
#            h1.addOrganelle(o1)
#            if rSurf.has_key(name): 
#                if rSurf[name].ingredients:
#                    r  = rSurf[name]
#                    o1.setSurfaceRecipe(r)
#            if rMatrix.has_key(name):
#                if rMatrix[name].ingredients:
#                    r = rMatrix[name]
#                    o1.setInnerRecipe(r)
        
#===============================================================================
# color tools
#===============================================================================
    def color(self,mode="distance",target=None, parents=None,data=None, 
              objects=None, colors=[red,black],**options):
        
        mini=None
        maxi=None
        useMaterial = False
        useObjectColors = False
        if "mini" in options:
            mini = options["mini"]
        if "maxi" in options:
            maxi = options["maxi"]
        if "useMaterial" in options:
            useMaterial = options["useMaterial"]
        if "useObjectColors" in options:
            useObjectColors = options["useObjectColors"]
        ramp = c.getRamp(colors)
        datas = None
        listeObjs = None
        if mode == "distance":            
            listeObjs,datas = self.colorByDistanceFrom(target,
                            parents=parents,distances=data, 
                            objects=objects,ramp=ramp,
                            colors=colors,**options)
        elif mode == "order":
            #the order is in the name
            listeObjs,datas = self.colorByOrder(parents=parents,orders=data, 
                            objects=objects,ramp=ramp,
                            colors=colors,**options)
        print("datas",len(datas))
        print("objs",len(listeObjs))
        if datas and datas is not None :
            from DejaVu.colorTool import Map
            lcol = Map(datas, ramp,mini=mini, maxi=maxi)
            for i,io in enumerate(listeObjs) :
                #print io
                io = self.vi.getObject(io)
                if useMaterial :
                    #this will add a material if no material
                    self.vi.changeObjColorMat(io,lcol[i])
                if useObjectColors:
                    import c4d
                    io[c4d.ID_BASEOBJECT_USECOLOR] = 1 #automatic
                    io[c4d.ID_BASEOBJECT_COLOR] = self.vi.FromVec(lcol[i],pos=False) #get a vector 0,0,0
        return datas,listeObjs
        
    def colorByDistanceFrom(self,target,parents=None,distances=None, objects=None,
                            ramp=None,
                            colors=[red,black],**options):
        """
        target : name or host object target
        """
        #get distance from object to the target.
        #all object are in h.molecules and orga.molecules
        #get options
        usePoint = False
        threshold = 99999.
        if "usePoint" in options:
            usePoint = options["usePoint"]        
        if "threshold" in options:
            threshold = options["threshold"]
        if ramp is None :
            ramp = c.getRamp(colors)
            if ramp is None :
                return
        o = self.vi.getObject(target)
#        print "target",o
        if o is None :
            return
        targetPos = self.vi.ToVec(self.vi.getTranslation(o)) #hostForm
        listeObjs=[]
        listeDistances = []
        if distances is None :
            #get all object except itself,use hierarchy from host
            #cytoplasme,organellename
            if parents is None :
                listeParent = ["cytoplasme"]
                for o in self.histo.organelles :
                    listeParent.append(o.name+"_Matrix")
                    listeParent.append(o.name+"_surface")
            else :
                listeParent = parents
            for parent in listeParent:
                obparent = self.vi.getObject(parent)
#                print "parent",obparent
                childs = self.vi.getChilds(obparent)
                for ch in childs:
                    ingr_name = self.vi.getName(ch)
#                    print "ingr",ingr_name
                    #ingr_childs = self.vi.getChilds(ch)
                    meshp = self.vi.getObject("Meshs_"+ingr_name.split("_")[0])
                    #for all instance get the position and measure the distance to target
#                    print "meshi",meshp
                    if meshp is None :
                        continue #should get sphere/cylnder parent ?
                    meshpchilds = self.vi.getChilds(meshp)
                    for cc in meshpchilds:
#                        print "child",cc
                        pos = self.vi.ToVec(self.vi.getTranslation(cc))
                        if usePoint:
                            d=self.vi.findClosestPoint(pos,o)
                        else :
                            d=self.vi.measure_distance(pos,targetPos)
#                        print d,threshold
                        if d < threshold :
                            listeDistances.append(d)
                            listeObjs.append(cc)
        else :
            listeDistances = distances
            listeObjs = objects
        return listeObjs,listeDistances
        
    def colorByOrder(self,parents=None,orders=None, objects=None,
                            ramp=None,
                            colors=[red,black],**options):
        """
        target : name or host object target
        """
        #get distance from object to the target.
        #all object are in h.molecules and orga.molecules
        #get options
        orderInName = False
        threshold = 999999
        if "orderInName" in options:
            orderInName = options["orderInName"]
        if "threshold" in options:
            threshold = options["threshold"]
        if ramp is None :
            ramp = c.getRamp(colors)
            if ramp is None :
                return
        listeObjs=[]
        listeOrder = []

        if orders is None :
            if orderInName :
                #get all object except itself,use hierarchy from host
                #cytoplasme,organellename
                if parents is None :
                    listeParent = ["cytoplasm"]
                    for o in self.histo.organelles :
                        listeParent.append(o.name+"_Matrix")
                        listeParent.append(o.name+"_surface")
                else :
                    listeParent = parents
                for parent in listeParent:
                    obparent = self.vi.getObject(parent)
                    print("parent",obparent)
                    childs = self.vi.getChilds(obparent)
                    for ch in childs:
                        ingr_name = self.vi.getName(ch)
                        print("ingr",ingr_name)
                        #ingr_childs = self.vi.getChilds(ch)
                        meshp = None
                        for z in self.vi.getChilds(ch) :
                            if self.vi.getName(z).find("Meshs_") == 0 :
                                meshp = z
                                break
                        #meshp = self.vi.getObject("Meshs_"+ingr_name.split("_")[0])
                        #for all instance get the position and measure the distance to target
                        print("meshi",meshp)
                        if meshp is None :
                            continue #should get sphere/cylnder parent ?
                        meshpchilds = self.vi.getChilds(meshp)
                        for cc in meshpchilds:
                            name = self.vi.getName(cc)
                            print("child order",name.split("_")[-1])
                            order = int(name.split("_")[-1])#first caracter is "n"
                            print(order)
                            if order < threshold :
                                listeOrder.append(order)
                                listeObjs.append(cc)
            else :
                #use histovol.molecules and .order
                #for each mol get the order and color the poly
                inds={}
                for pos, rot, ingr, ptInd in self.histo.molecules:
                    if ingr not in inds:
                        inds[ingr] = [ptInd]
                    else :
                        inds[ingr].append(ptInd)
                               
        else :
            listeOrder = orders
            listeObjs = objects
        return listeObjs,listeOrder

    def exportIngredient(self,ingr):
#        from DejaVu.IndexedPolygons import IndexedPolygons
        print(ingr.name)
        if ingr.meshFile is None or os.path.splitext(ingr.meshFile)[0] != '':
#            if isinstance(ingr.mesh,IndexedPolygons):
#                ingr.mesh.writeToFile(self.wrkdir+os.sep+ingr.name)
#            else :
            if ingr.mesh is not None :
                m = self.helper.getMesh(ingr.mesh)
                if self.helper.getType(m) == self.helper.POLYGON :
                    self.helper.writeToFile(ingr.mesh,self.wrkdir+os.sep+ingr.name)
            else :
                print(ingr.name+" no mesh",ingr.mesh)
        else :
            print(ingr.name+" mesh already exist: "+ingr.meshFile)
            
    def exportRecipeIngredients(self,recipe):
        if recipe:  
            r = [self.exportIngredient(ingr) for ingr in recipe.ingredients]
        
    def exportAsIndexedMeshs(self,):
        #organelle mesh and ingredient
        for o in self.histo.organelles:
            if o.mesh is None :
                v,f,vn,fn = o.vertices,o.faces,o.vnormals,o.fnormals
                self.helper.writeMeshToFile(self.wrkdir+os.sep+o.name,
                                        verts=v,faces=f,vnorms=vn,fnorms=fn)
            else :
                self.helper.writeToFile(o.mesh,self.wrkdir+os.sep+o.name)
            self.exportRecipeIngredients(o.surfaceRecipe)
            self.exportRecipeIngredients(o.innerRecipe)
        #ingredients in out recipe
        self.exportRecipeIngredients(self.histo.exteriorRecipe)

    def displayParticleVolumeDistance(self,distance,histoVol):
        N = len(distance)
        helper = self.vi
        import c4d
        doc = c4d.documents.GetActiveDocument()
        PS = doc.GetParticleSystem()
        PS.FreeAllParticles()
        ids = list(range(N))
        PS = helper.particle(histoVol.grid.masterGridPositions)
        life = [c4d.BaseTime(10.0),]*N
        list(map(PS.SetLife,ids,life))#should avoid map
        ages = [c4d.BaseTime((d/100.0)*10.) for d in distance]
        list(map(PS.SetAge,ids,ages))#should avoid map
#        #render ?
#        #render("md%.4d" % i,640,480)
#        name = "/Users/ludo/DEV/AutoFill/TestSnake/render/renderdistance"
        
        rd = doc.GetActiveRenderData().GetData()
        bmp = c4d.bitmaps.BaseBitmap()
        #Initialize the bitmap with the result size.
        #The resolution must match with the output size of the render settings.
        bmp.Init(x=640, y=480, depth=32)
#        fps = doc.GetFps()
#        next = c4d.BaseTime(self.i/fps)
#        doc.SetTime(bc2)
        c4d.documents.RenderDocument(doc, rd, bmp, c4d.RENDERFLAGS_EXTERNAL)
        c4d.CallCommand(12414)                 

    def displayFreePointsAsPS(self):
        #self.histo.freePointsAfterFill[:self.histo.nbFreePointsAfterFill]
        N = self.histo.nbFreePointsAfterFill
        helper = self.vi
        import c4d
        doc = c4d.documents.GetActiveDocument()
        PS = doc.GetParticleSystem()
        PS.FreeAllParticles()
        ids = list(range(N))
        gridC = self.histo.grid.masterGridPositions
        pts = self.histo.freePointsAfterFill
        coords = [gridC[pts[i]] for i in range(N)]
        PS = helper.particle(coords)
        life = [c4d.BaseTime(10.0),]*N
        list(map(PS.SetLife,ids,life))
#        ages = [c4d.BaseTime((d/100.0)*10.) for d in distance]
#        map(PS.SetAge,ids,ages)
#        #render ?
#        #render("md%.4d" % i,640,480)
#        name = "/Users/ludo/DEV/AutoFill/TestSnake/render/renderdistance"
        
#        rd = doc.GetActiveRenderData().GetData()
#        bmp = c4d.bitmaps.BaseBitmap()
        #Initialize the bitmap with the result size.
        #The resolution must match with the output size of the render settings.
#        bmp.Init(x=640, y=480, depth=32)
#        fps = doc.GetFps()
#        next = c4d.BaseTime(self.i/fps)
#        doc.SetTime(bc2)
#        c4d.documents.RenderDocument(doc, rd, bmp, c4d.RENDERFLAGS_EXTERNAL)
#        c4d.CallCommand(12414)                 
    
    def delIngr(self,ingr):
        ingrname=ingr.name
        parentname =  "Meshs_"+ingrname.replace(" ","_")
        parent = self.helper.getObject(parentname)
        print (parentname,parent)
        if parent is not None :
            instances = self.helper.getChilds(parent)
            [self.helper.deleteObject(o) for o in instances]
            self.helper.deleteObject(parent) #is this dleete the child ?
        #need to do the same for cylinder
        if self.doSpheres :
            orga = ingr.recipe().organelle()
            name = orga.name+"_Spheres_"+ingr.name.replace(" ","_")    
            parent = self.helper.getObject(name)
            print (name,parent)            
            if parent is not None :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent)
            name = orga.name+"_Cylinders_"+ingr.name.replace(" ","_")    
            parent = self.helper.getObject(name)
            print (name,parent)            
            if parent is not None :
                instances = self.helper.getChilds(parent)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(parent)

    def clearIngr(self,*args):
        """ will clear all ingredients instances but leave base parent hierarchie intact"""
        self.histo.loopThroughIngr(self.delIngr)        
#        [self.delIngr(ingrname) for ingrname in self.ingredients]
                
    def clearRecipe(self,recipe,*args):
        """ will clear everything related to self.recipe"""
        parent = self.helper.getObject(recipe)
        if parent is not None :
            instances = self.helper.getChilds(parent)
            [self.helper.deleteObject(o) for o in instances]
            self.helper.deleteObject(parent)

    def clearAll(self,recipe):
        #shoud remove everything
        self.clearRecipe(recipe)
        #reset the fill
        self.clearFill(recipe)
        
    def clearFill(self,recipe):
        #should ony reset the fill
        self.histo.reset()
#        if self.histo.ingr_result is not None :
#            self.ingredients =self.histo.ingr_result
        self.clearIngr()
        #need to clear also the static object
        parentname =  recipe+"static"
        parent = self.helper.getObject(parentname)
#        print (parentname,parent)
        if parent is not None :
            static = self.helper.getChilds(parent)
            [self.helper.deleteObject(o) for o in static]
        
        #need to clear also the moving object
        parentname =  recipe+"moving"
        parent = self.helper.getObject(parentname)
#        print (parentname,parent)
        if parent is not None :
            static = self.helper.getChilds(parent)
            [self.helper.deleteObject(o) for o in static]

        parent = self.helper.getObject(recipe+"GridPointHider")
        if parent is not None :
            point = self.helper.getChilds(parent)
            [self.helper.deleteObject(o) for o in point]
                        