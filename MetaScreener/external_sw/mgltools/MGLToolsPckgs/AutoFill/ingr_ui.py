# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 10:21:38 2011
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# ingr_ui.py Authors: Ludovic Autin with minor editing/enhancement from Graham Johnson
#
# Copyright: Graham Johnson ©2010
#
# This file "Organelle.py" is part of autoPACK, cellPACK, and AutoFill.
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
@author: Ludovic Autin with design/editing/enhancement by Graham Johnson
"""
import sys,os
import random
import numpy
from math import sqrt

from upy.colors import red, green, blue, cyan, magenta, yellow, \
     pink, brown, orange, burlywood, darkcyan, gainsboro
from upy import colors as upy_colors

from bhtree import bhtreelib
import AutoFill
from AutoFill.Ingredient import SingleSphereIngr, MultiSphereIngr
from AutoFill.Ingredient import MultiCylindersIngr,GrowIngrediant,ActinIngrediant
from AutoFill.Ingredient import IOingredientTool

def principal_axes(points,return_eigvals=False):
    """
    From http://python-geoprobe.googlecode.com/hg-history/eabee6e95acc3e110ebc36a3fc587e25942cd430/geoprobe/utilities.py        
    Finds the principal axes of a 3D point cloud.
    Input:
        x, y, z:
            numpy arrays of x, y, and z, respectively
        return_eigvals (default: False):
            A boolean specifying whether to return the eigenvalues.
    Returns:
        eigvecs : A 3x3 numpy array whose columns represent 3 orthogonal
            vectors. The first column corresponds to the axis with the largest
            degree of variation (the principal axis) and the last column 
            correspons to the axis with the smallest degree of variation.
        eigvals : (Only returned if `return_eigvals` is True) A 3-length vector
            of the eigenvalues of the point cloud.
    """
    coords = numpy.array(points)
    coords = numpy.array(coords,'f')
#        coords = np.vstack([x,y,z]).T
    coords -= coords.mean(axis=0)
    cov = numpy.dot(coords.T,coords)
    print (coords,cov)
    eigvals, eigvecs = numpy.linalg.eigh(cov)
    eigvecs = eigvecs[:, eigvals.argsort()[::-1]]
    if return_eigvals:
        return eigvecs, eigvals
    else:
        return eigvecs
        
# -- The Point class represents points in n-dimensional space
class Point:
    # Instance variables
    # self.coords is a list of coordinates for this Point
    # self.n is the number of dimensions this Point lives in (ie, its space)
    # self.reference is an object bound to this Point
    # Initialize new Points

    def __init__(self, coords, reference=None):
        self.coords = coords
        self.n = len(coords)
        self.reference = reference
    # Return a string representation of this Point

    def __repr__(self):
        return str(self.coords)
# -- The Cluster class represents clusters of points in n-dimensional space


class Cluster:
    # Instance variables
    # self.points is a list of Points associated with this Cluster
    # self.n is the number of dimensions this Cluster's Points live in
    # self.centroid is the sample mean Point of this Cluster

    def __init__(self, points):
        # We forbid empty Clusters (they don't make mathematical sense!)
        if len(points) == 0: raise Exception("ILLEGAL: EMPTY CLUSTER")
        self.points = points
        self.n = points[0].n
        # We also forbid Clusters containing Points in different spaces
        # Ie, no Clusters with 2D Points and 3D Points
        for p in points:
            if p.n != self.n: raise Exception("ILLEGAL: MULTISPACE CLUSTER")
        # Figure out what the centroid of this Cluster should be
        self.centroid = self.calculateCentroid()
    # Return a string representation of this Cluster

    def __repr__(self):
        return str(self.points)
    # Update function for the K-means algorithm
    # Assigns a new list of Points to this Cluster, returns centroid difference

    def update(self, points):
        old_centroid = self.centroid
        self.points = points
        self.centroid = self.calculateCentroid()
        x1,y1,z1 = old_centroid.coords
        x2,y2,z2 = self.centroid.coords
        return sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) + (z1-z2)*(z1-z2) )

    # Calculates the centroid Point - the centroid is the sample mean Point
    # (in plain English, the average of all the Points in the Cluster)
    def calculateCentroid(self):
        centroid_coords = []
        # For each coordinate:
        for i in range(self.n):
            # Take the average across all Points
            centroid_coords.append(0.0)
            for p in self.points:
                centroid_coords[i] = centroid_coords[i]+p.coords[i]
            centroid_coords[i] = centroid_coords[i]/len(self.points)
        # Return a Point object using the average coordinates
        return Point(centroid_coords)

    def radiusOfGyration(self):
        ptCoords = [x.coords for x in self.points]
        delta = numpy.array(ptCoords)-self.centroid.coords
        rg = sqrt( sum( numpy.sum( delta*delta, 1))/float(len(ptCoords)) )
        return rg

    def encapsualtingRadius(self):
        ptCoords = [x.coords for x in self.points]
        delta = numpy.array(ptCoords)-self.centroid.coords
        rM = sqrt( max( numpy.sum( delta*delta, 1)) )
        return rM
        
    def principal_axes(self,points,return_eigvals=False):
        """
        From http://python-geoprobe.googlecode.com/hg-history/eabee6e95acc3e110ebc36a3fc587e25942cd430/geoprobe/utilities.py        
        Finds the principal axes of a 3D point cloud.
        Input:
            x, y, z:
                numpy arrays of x, y, and z, respectively
            return_eigvals (default: False):
                A boolean specifying whether to return the eigenvalues.
        Returns:
            eigvecs : A 3x3 numpy array whose columns represent 3 orthogonal
                vectors. The first column corresponds to the axis with the largest
                degree of variation (the principal axis) and the last column 
                correspons to the axis with the smallest degree of variation.
            eigvals : (Only returned if `return_eigvals` is True) A 3-length vector
                of the eigenvalues of the point cloud.
        """
        coords = numpy.array(points)
        coords = numpy.array(coords,'f')
#        coords = np.vstack([x,y,z]).T
        coords -= coords.mean(axis=0)
        cov = numpy.dot(coords.T,coords)
        print (coords,cov)
        eigvals, eigvecs = numpy.linalg.eigh(cov)
        eigvecs = eigvecs[:, eigvals.argsort()[::-1]]
        if return_eigvals:
            return eigvecs, eigvals
        else:
            return eigvecs

# -- Return Clusters of Points formed by K-means clustering

from time import time
import upy
uiadaptor = upy.getUIClass()
#helperClass = upy.getHelperClass()

class SphereTreeUI(uiadaptor):   
    isSetup = False
#    def __init__(self,**kw):
    def setup(self,**kw):
        self.title = "SphereTreeMaker"
        #we need the helper
        if "helper" in kw:
            self.helper = kw["helper"]
        else :
            self.helper = upy.getHelperClass()()
        self.sc = self.helper.getCurrentScene()
        self.dock = False
        if "subdialog" in kw :
            if kw["subdialog"]:
                self.subdialog = True
                self.block = True      
        self.points = []
        self.seeds = []
        self.seedsCoords = []

        self.object_target_name = "ObjectName"
        self.object_target = self.helper.getCurrentSelection()[0]
        if self.object_target is not None :
            self.object_target_name = self.helper.getName(self.object_target)
            
        self.sphere = self.helper.getObject('Sphere')
        if self.sphere is None :
            self.sphere = self.helper.newEmpty('Sphere')
            self.helper.addObjectToScene(self.sc,self.sphere)
        
        self.baseSphere = self.helper.getObject('baseSphere')
        if self.baseSphere is None :       
            self.baseSphere = self.helper.Sphere('baseSphere',parent=self.sphere)[0]
        self.principal_axes = (1,0,0)
        self.principal_axes_cylinder = None
        self.clusterCenterSpheres=[]
        self.clusterSpheres=[]
        self.clusterCenterCyl={}
        
        self.root_cluster = self.helper.getObject('Cluster')
        if self.root_cluster is None :       
            self.root_cluster = self.helper.newEmpty("Cluster")
            self.helper.addObjectToScene(self.sc,self.root_cluster)
        
        self.Spheres = self.helper.getObject('Spheres')
        if self.Spheres is None :         
            self.Spheres=self.helper.newEmpty("Spheres")
            self.helper.addObjectToScene(self.sc,self.Spheres,parent =self.root_cluster)
        
        self.CenterSpheres = self.helper.getObject('CenterSpheres')
        if self.CenterSpheres is None : 
            self.CenterSpheres=self.helper.newEmpty("CenterSpheres")
            self.helper.addObjectToScene(self.sc,self.CenterSpheres,parent =self.root_cluster)
        
        self.keptCenters = []
        self.keptRadii = []
        
        self.factor = 0.5
        self.clusters = None
        self.initWidget(id=1005)
        self.setupLayout()
        self.isSetup = True
        self.io = IOingredientTool()
        self.ingr = None
        self.setTarget()
        
    def CreateLayout(self):
        self._createLayout()
        return 1

    def Command(self,*args):
#        print args
        self._command(args)
        return 1
        
    def initWidget(self,id=0):
        #getThelist of available ingredient
        self.id = id
        self.BTN={}
        self.BTN["keepS"]=self._addElemt(name="keep Geometry",width=100,height=10,
                                     action=self.keepSpheres,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["delkeepS"]=self._addElemt(name="delete kept Geometry",width=100,height=10,
                         action=self.deleteSpheres,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["saveS"]=self._addElemt(name="write File...",width=100,height=10,
                         action=self.save_cb,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["close"]=self._addElemt(name="Close",width=100,height=10,
                         action=self.close,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["gridify"]=self._addElemt(name="Gridify",width=100,height=10,
                         action=self.gridify,type="button",icon=None,
                                     variable=self.addVariable("int",0))
        self.BTN["clearPoint"]=self._addElemt(name="Clear Points",width=100,height=10,
                         action=self.clearPoints,type="button",icon=None,
                                     variable=self.addVariable("int",0))

        self.available_mode=["bhtree_dot","sdf_fixdimension","sdf_interpolate","jordan_raycast","jordan_3raycast"]
        self.mode=self._addElemt(name="gridify_mode",
                                    value=self.available_mode,
                                    width=180,height=10,action=None,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)
        self.grid_step = self._addElemt(name='step',width=100,height=10,
                                              action=None,type="inputFloat",icon=None,
                                              value = 20.,
                                              variable=self.addVariable("float",1.),
                                              mini=0.00,maxi=1000.00,step=1.0)
        self.rt_display=self._addElemt(name='Display Real Time (debug)',width=80,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=0)
        self.useFix =self._addElemt(name='Use neighbours faces normals average fix',width=80,height=10,
                                              action=None,type="checkbox",icon=None,
                                              variable=self.addVariable("int",1),value=0)                                     
        self.LABELS={}
        
        self.LABELS["algo"] = self._addElemt(label="Using :",width=100)
        self.LABELS["scale"] = self._addElemt(label="Scale :",width=100)
        self.LABELS["nbS"] = self._addElemt(label="#sph :",width=100)  
        self.LABELS["geom"] = self._addElemt(label="enter a geom or nothing for selection :",width=100)
        self.LABELS["geomtype"] = self._addElemt(label="choose schem type",width=100)
        self.LABELS["ei"]= self._addElemt(label="bond cutoff",width=100)
        self.IN={}
        self.IN["scale"]= self._addElemt(name='scale',width=100,height=10,
                                              action=self.scale_cb,type="inputFloat",icon=None,
                                              value = 1.,
                                              variable=self.addVariable("float",1.),
                                              mini=0.00,maxi=10.00,step=0.01)
        self.IN["nbS"]= self._addElemt(name='nbsphere',width=100,height=10,
                                              action=self.clusterN,type="inputInt",icon=None,
                                              value = self.factor,
                                              variable=self.addVariable("int",2),
                                              mini=1,maxi=200,step=1)  
        self.IN["geom"]= self._addElemt(name='geometry',width=100,height=10,
                                              action=self.setTarget,type="inputStr",icon=None,
                                              value = self.object_target_name,
                                              variable=self.addVariable("str",self.object_target_name)) 
                                              
        self.eigenv= self._addElemt(name='eigen',width=100,height=10,
                                              action=self.cutoff_cb,type="inputFloat",icon=None,
                                              value = 1.0,
                                              variable=self.addVariable("float",1.0),
                                              mini=0.,maxi=500.,step=0.1)  
        self.available_type=["sphere","cylinder"]
        self.typegeom=self._addElemt(name="geomtype",
                                    value=self.available_type,
                                    width=180,height=10,action=None,
                                    variable=self.addVariable("int",0),
                                    type="pullMenu",)
        
                                                              
    def setupLayout(self):
        #this where we define the Layout
        #this wil make three button on a row
        self._layout = []
        self._layout.append([self.LABELS["geom"],self.IN["geom"],])
        self._layout.append([self.LABELS["geomtype"],self.typegeom])
        self._layout.append([self.BTN["keepS"],])
        self._layout.append([self.BTN["delkeepS"],])
        self._layout.append([self.BTN["saveS"],])
        self._layout.append([self.LABELS["scale"],self.IN["scale"]])
        self._layout.append([self.LABELS["nbS"],self.IN["nbS"]])
        self._layout.append([self.LABELS["ei"],self.eigenv])
        #separtor ?
        self._layout.append([self.grid_step,self.BTN["gridify"],])
        self._layout.append([self.LABELS["algo"],self.mode,])
        self._layout.append([self.rt_display,])
        self._layout.append([self.useFix,])
        self._layout.append([self.BTN["clearPoint"],])
        self._layout.append([self.BTN["close"],])

#===============================================================================
# callback
#===============================================================================
    def setTarget(self,*args):
        obj = self.getVal(self.IN["geom"])
        self.setTarget_cb(obj)
        
    def setTarget_cb(self,objname):
        self.object_target_name = objname
        if self.object_target_name == "" :
            self.object_target = None    
        else :
            self.object_target = self.helper.getObject(self.object_target_name)            
        coords= self.getCurrentSelectedPoints()
        #retrieve the principal axis of the object
        eivec,eival = principal_axes(coords,return_eigvals=True)
        #eivec[0] is the main
        self.principal_axes = eivec[0]
        w1,ax1 = self.helper.getAngleAxis(self.principal_axes,[0.,0.,1.])
        w2,ax2 = self.helper.getAngleAxis(self.principal_axes,[0.,0.,-1.])
        if w1 < w2 : #closest to [0.,0.,1.]
            self.principal_axes = [0.,0.,1.]
        else :
            self.principal_axes = [0.,0.,-1.]            
        #where does point the axis 0,0,1 or 0,0,-1
        head = numpy.array(self.principal_axes ) * 10.0
        tail = - numpy.array(self.principal_axes ) * 10.0
        if len(head) == 1 : head = head[0]
        if len(tail) == 1 : tail = tail[0]        
        if self.principal_axes_cylinder is None:
            self.principal_axes_cylinder=self.helper.oneCylinder("axis",head,tail,radius=1.0)
        else :
            self.helper.updateOneCylinder("axis",head,tail,radius=1.0)            
        
    def keepSpheres(self,*args):
        sph = self.clusterSpheres
        currentNum = len(self.keptRadii)
        #need to get the position of the current sphere instance
        # go throught them and get ther position
        listeCenter=[self.helper.ToVec(self.helper.getTranslation(x)) for x in sph]
        listeRadii =[self.helper.ToVec(self.helper.getScale(x)) for x in sph]
        self.keptCenters.extend( listeCenter[currentNum:] )
        self.keptRadii.extend( [r[0] for r in listeRadii[currentNum:]] )
        self.helper.clearSelection() #clear the current selection in the viewer??

    def deleteSpheres(self,*args):
        self.keptCenters = []
        self.keptRadii = []
        self.setLong(self.IN["nbS"],1)
        self.clusterN(None)

    def save_cb(self,*args):
        #get name
#        name = "default"
#        initialFile = name+'_%d.sph'%len(self.keptRadii)
#        self.saveDialog(label='AutoFill Sph files',callback=self.saveSphereModel)
        self.saveDialog(label='AutoPACK Ingredient files',callback=self.saveIngredent)
#        file = tkFileDialog.asksaveasfilename(
#            parent = master,
#            filetypes=[ ('AutoFill Sph files', '*.sph'),('All files', '*') ],
#            initialdir='.',
#            initialfile=initialFile,
#            title='save sphere file')
#        if file=='': file = None
#        if file:
#            self.saveSphereModel(file)

    def scale_cb(self,*args):
        self.factor = scale = self.getReal(self.IN["scale"])
        gtype = self.getVal(self.typegeom)
        if gtype == "sphere":
            self.displayClustersSpheres(self.clusters, factor=self.factor)
        else :
            ev = self.getVal(self.eigenv)
            self.displayClustersBonds(self.clusters, factor=self.factor,ev=ev)

    def cutoff_cb(self,*args):
        self.factor = scale = self.getReal(self.IN["scale"])
        gtype = self.getVal(self.typegeom)
        if gtype == "sphere":
            self.displayClustersSpheres(self.clusters, factor=self.factor)
        else :
            ev = self.getVal(self.eigenv)
            self.displayClustersBonds(self.clusters, factor=self.factor,ev=ev)

    def clusterN(self,*args):
        howMany = self.getLong(self.IN["nbS"])
        gtype = self.getVal(self.typegeom)
        ev = self.getVal(self.eigenv)
        scale = self.getReal(self.IN["scale"])
        self.clusterN_cb(howMany,gtype,scale,ev)

    def clusterN_cb(self,howMany,gtype,scale,ev):
        #global clusters, seeds, seedsCoords, points
        from random import uniform
        seedsInd = []
        self.seeds = []
        self.seedsCoords = []
        
        #get the currentpointSelected. use sphere or actual mesh points ?
        coords= self.getCurrentSelectedPoints()
#        allAtoms = self.getSelection().findType(Atom)
        self.points = [Point(c) for c in coords]
        for i in range(howMany):
            ind = int(uniform(0, len(self.points)))
            print ("uniform ",ind,len(self.points))
            self.seeds.append(self.points[ind])
            self.seedsCoords.append(self.points[ind])
            seedsInd.append( ind)
        t1 = time()
        self.clusters = self.kmeans(self.points, len(self.seeds), 0.5, self.seeds)
#        print 'time to cluster points', time()-t1
        if gtype == "sphere":
            self.displayClustersSpheres(self.clusters, factor=scale)
        else :
            self.displayClustersBonds(self.clusters, factor=scale,ev=ev)
#            ev = self.getVal(self.eigenv)
#            self.displayClustersCylinders(self.clusters, factor=self.factor,ev=ev)

    def saveIngredent(self,filename):
        name = self.getVal(self.IN["geom"])
        gtype = self.getVal(self.typegeom)
        self.saveIngredent_cb(filename,name,gtype)
        
    def saveIngredent_cb(self,filename,name,gtype,**kw):
        #use histoVol ?        
        #we needtype Sphere/Cylinder/MixSC
        #
        molarity=1.0
        color=[1,0,0]
        pdb=None
        sphereFile=filename+".sph"        
        geomFile=filename+"."+self.helper.hext
        if "geomFile" in kw :
            geomFile = kw["geomFile"]
        packingPriority=0
        jitterMax=(0.2,0.1,0.2)
        if "jitterMax" in kw :
            jitterMax = kw["jitterMax"]
        resolution=None
        if "resolution" in kw :
            resolution= kw["resolution"]
        resolution_dictionary = None
        if "resolution_dictionary" in kw:
            resolution_dictionary=kw["resolution_dictionary"]
        recipe_name = None
        if "recipe_name" in kw :
            recipe_name = kw["recipe_name"]
        principalVector=self.principal_axes
        packingMode="random"
        gftype = "host"
        rotAxis = [0.,2.,1.]
        useRotAxis = 1
        self.helper.write(geomFile,[self.object_target],gftype)
#        self.saveGeom(geomFile, gftype)
        if gtype == "sphere":
            self.saveSphereModel(sphereFile)
            self.ingr = MultiSphereIngr( molarity, color=color, pdb=pdb,
                                 name=name,
                                 sphereFile=sphereFile,#or directly sphere radius and pos
                                 meshFile=geomFile,
                                 packingPriority=packingPriority,
                                 jitterMax=jitterMax,
                                 principalVector=principalVector,
                                 packingMode=packingMode,
                                 rotAxis=rotAxis,useRotAxis = useRotAxis,
                                 resolution_dictionary=resolution_dictionary)
            if recipe_name is not None:
                self.ingr.sphereFile = AutoFill.autoPACKserver+os.sep+recipe_name+os.sep+"spheres"+os.sep+os.path.basename(sphereFile)
        else :
            positions=[]
            positions2=[]
            radius = []
#            axis = self.helper.getPropertyObject(child[0],key=["axis"])[0]
#            axis should be main eigen vector ? of all point
            for ioname in self.clusterCenterCyl:                
#            for io in child :
                #get the radius and the translation
                io = self.helper.getObject(ioname)
                if io is None :
                    continue
                head,tail,rad = self.clusterCenterCyl[ioname]
                positions.append(head)
                positions2.append(tail)
                radius.append(rad)
#                    self.helper.oneCylinder(self.helper.getName(io)+"_cyl",head,tail,radius=r)
            self.ingr = MultiCylindersIngr( molarity,
                                 name=name,color=color, pdb=pdb,
                                 radii=[radius],
                                 positions=[numpy.array(positions).tolist()], 
                                 positions2=[numpy.array(positions2).tolist()],
                                 meshFile=geomFile,
                                 packingPriority=packingPriority,
                                 jitterMax=jitterMax,
                                 principalVector=principalVector,
                                 packingMode=packingMode,
                                 rotAxis=rotAxis,useRotAxis = useRotAxis,
                                 resolution_dictionary=resolution_dictionary)
        #before saving can point meshfile and sphereFile to server
        if recipe_name is not None:
            self.ingr.meshFile = AutoFill.autoPACKserver+os.sep+recipe_name+os.sep+"geoms"+os.sep+str(resolution)+os.sep+os.path.basename(geomFile)                
        #save the ingredient
        self.io.write(self.ingr,filename,ingr_format="all")
        #should we replace by local directory ?
        #write it ? add it o exist file ?
        #python string ?
        #texture ?
                                
    def saveSphereModel(self,filename, minR=-1, maxR=-1 ):
        sph = self.clusterSpheres
        centers=[self.helper.ToVec(self.helper.getTranslation(x)) for x in sph]
        radii =[self.helper.ToVec(self.helper.getScale(x)) for x in sph]
        
        minR = self.radg #added by Graham 4/4/11
        maxR = self.radm #added by Graham 4/4/11
        
        f = open(filename, 'w')
        f.write("# rmin rmax\n")
        f.write("%6.2f  %6.2f\n"%(minR, maxR))
        f.write("\n")
        f.write("# number of levels\n")
        f.write("1\n")
        f.write("\n")
        f.write("# number of spheres in level 1\n")
        f.write("%d\n"%len(centers))
        f.write("\n")
        f.write("# x y z r of spheres in level 1\n")
        if not len(self.keptCenters):
            self.keepSpheres(None)
        for r,c in zip(self.keptRadii, self.keptCenters):
            x,y,z = c
            f.write("%6.2f %6.2f %6.2f %6.2f\n"%(x,y,z,r))
        f.write("\n")
        f.close()


        
    def displayClustersSpheres(self,clusters, factor=0.7):
        colors = [ getattr(upy_colors, name) for name in  upy_colors.cnames ]

        centers = []
        radiiG = []
        radiiM = []
        radii = []
        if clusters is None:
            return
        for i,cluster in enumerate(clusters):
            centers.append(cluster.centroid.coords)
            radg = cluster.radiusOfGyration()
            radm = cluster.encapsualtingRadius()
            self.radg = radg  #added by Graham 4/4/11
            self.radm = radm  #added by Graham 4/4/11
            #rad = radg/0.7
            rad = radg + factor*(radm-radg)
            radiiG.append(radg)
            radiiM.append(radm)
            radii.append(rad)
            
            ptCoords = [x.coords for x in cluster.points]

        nbc = len(clusters)
        #instancesSphere for center
        if not self.clusterCenterSpheres:
            self.clusterCenterSpheres=self.helper.instancesSphere("clcspheres",
                                    self.keptCenters+centers,[2.],
                                    self.sphere,colors[:nbc],self.sc,
                                    parent=self.CenterSpheres)
        else :
            self.clusterCenterSpheres=self.helper.updateInstancesSphere("clcspheres",
                                    self.clusterCenterSpheres,self.keptCenters+centers,
                                    self.keptRadii+radii,
                                    self.sphere,colors[:nbc],self.sc,
                                    parent=self.CenterSpheres,delete=True)
                            
#        print 'cluster with %d points rg:%.2f rM:%.2f ratio:%.2f %.2f'%(
#            len(cluster.points), radg, radm, radg/radm, rad)
        if not self.clusterSpheres:
            self.clusterSpheres=self.helper.instancesSphere("clspheres",
                                    self.keptCenters+centers,self.keptRadii+radii,
                                    self.sphere,colors[:nbc],self.sc,
                                    parent=self.Spheres)
        else :
            self.clusterSpheres=self.helper.updateInstancesSphere("clspheres",
                                    self.clusterSpheres,self.keptCenters+centers,
                                    self.keptRadii+radii,
                                    self.sphere,colors[:nbc],self.sc,
                                    parent=self.Spheres,delete=True)

    def displayClustersCylinders(self,clusters, factor=0.7,ev=0):
        colors = [ getattr(upy_colors, name) for name in  upy_colors.cnames ]

        centers = []
        radiiG = []
        radiiM = []
        radii = []
        self.clusterCenterCyl={}
        if clusters is None:
            return
        nbc = len(clusters)
        pinstance = self.helper.getObject("BC")
        if pinstance is None :
            pinstance=self.helper.Cylinder("BC",radius=1.,length=1.,res=10, pos = [0.,0.,0.],parent=None)[0]        
        for i,cluster in enumerate(clusters):
            centers = cluster.centroid.coords
            radg = cluster.radiusOfGyration()
            radm = cluster.encapsualtingRadius()
            self.radg = radg  #added by Graham 4/4/11
            self.radm = radm  #added by Graham 4/4/11
            #rad = radg/0.7
            rad = radg + factor*(radm-radg)
            radiiG.append(radg)
            radiiM.append(radm)
            radii.append(rad)
            
            ptCoords = [x.coords for x in cluster.points]
            delta = (numpy.array(ptCoords)-numpy.array(centers))
            delta *= delta
            distA = numpy.sqrt( delta.sum(1) )
            dmin = min(distA)
            dmax = max(distA)
            minInd = list(distA).index(dmin)
            maxInd = list(distA).index(dmax)

            eivec,eival = cluster.principal_axes(ptCoords,return_eigvals=True)
            cyl_direction = (ptCoords[maxInd]-numpy.array(centers))/dmax#eivec[ev]
            cyl_length = dmax
            cyl_radius = dmin
            head = numpy.array(centers) + numpy.array(cyl_direction) * cyl_length
            tail = numpy.array(centers) - numpy.array(cyl_direction) * cyl_length
            if len(head) == 1 : head = head[0]
            if len(tail) == 1 : tail = tail[0]
            for j in range(3):
                self.axe(i,numpy.array(centers),eivec[j]*cyl_length,j,colors[nbc])
#                self.axe("a"+str(i),numpy.array(centers),eivec[j],j,colors[nbc])
#            cyl = self.helper.getObject("clcyl"+str(i))
#            if cyl is None :
#                cyl=self.helper.oneCylinder("clcyl"+str(i),head,tail,radius=cyl_radius,instance=pinstance,material=None,
#                    parent = self.CenterSpheres,color=colors[nbc])
#                self.clusterCenterCyl.append(cyl)
#            else :
#                self.helper.updateOneCylinder("clcyl"+str(i),head,tail,radius=cyl_radius,color=colors[nbc])

            

    def axe(self,i,c,d,axe,color):
        head = c+d
        tail = c-d
        pinstance = self.helper.getObject("BC")
        if pinstance is None :
            pinstance=self.helper.Cylinder("BC",radius=2.,length=1.,res=10, pos = [0.,0.,0.],parent=None)[0]        
        cyl = self.helper.getObject("clcyl"+str(i)+str(axe))
        if cyl is None :
            cyl=self.helper.oneCylinder("clcyl"+str(i)+str(axe),head,tail,radius=1.,instance=pinstance,material=None,
                parent = self.CenterSpheres,color=color)
#            self.clusterCenterCyl.append(cyl)
        else :
            self.helper.updateOneCylinder("clcyl"+str(i)+str(axe),head,tail,radius=2.,color=color)


    def clear(self,*args):
        pass
    
    def clear_cb(self,gtype):
        if gtype == "sphere":
            [self.helper.deleteObject(o) for o in self.clusterCenterSpheres]
            [self.helper.deleteObject(o) for o in self.clusterSpheres]
        else :
            for j in range(len(self.clusterCenterCyl)):
                self.helper.deleteObject("clbond"+str(j))            

    def displayClustersBonds(self,clusters, factor=0.7,ev=1.0):
        colors = [ getattr(upy_colors, name) for name in  upy_colors.cnames ]

        centers = []
        radiiG = []
        radiiM = []
        radii = []
        if clusters is None:
            return
        
        for i,cluster in enumerate(clusters):
            centers.append(cluster.centroid.coords)
            radg = cluster.radiusOfGyration()
            radm = cluster.encapsualtingRadius()
            self.radg = radg  #added by Graham 4/4/11
            self.radm = radm  #added by Graham 4/4/11
            #rad = radg/0.7
            rad = radg + factor*(radm-radg)
            radiiG.append(radg)
            radiiM.append(radm)
            radii.append(rad)
            
            ptCoords = [x.coords for x in cluster.points]
        # Create a bhtree for the ptCoords using a granility of 10
        bht = bhtreelib.BHtree( centers, radiiM, 10)
        # find all pairs of atoms for which the distance is less than 1.1
        # times the sum of the radii
        print ("cutoff ",ev)
        pairs = bht.closePointsPairsInTree(ev)
        bhtreelib.freeBHtree(bht)
        # pairs is list of tuple of atom indices.
        nbc = len(clusters)
        bonds = {}
        for i,pair in enumerate(pairs):
            # 1- Get the atoms corresponding of the indices of the pair
            cl1 = clusters[int(pair[0])]
            cl2 = clusters[int(pair[1])]
            head = cl1.centroid.coords
            tail = cl2.centroid.coords
            rad = cl1.radiusOfGyration() + factor*(cl1.encapsualtingRadius()-cl1.radiusOfGyration())#or diameter ?
            pinstance = self.helper.getObject("BC")
            if pinstance is None :
                pinstance=self.helper.Cylinder("BC",radius=1.,length=1.,res=10, pos = [0.,0.,0.],parent=None)[0]        
            cyl = self.helper.getObject("clbond"+str(i))
            if cyl is None :
                cyl=self.helper.oneCylinder("clbond"+str(i),head,tail,radius=rad,instance=pinstance,material=None,
                    parent = self.CenterSpheres,color=colors[nbc])
            else :
                self.helper.updateOneCylinder("clbond"+str(i),head,tail,radius=rad,color=colors[nbc])
            self.clusterCenterCyl["clbond"+str(i)] = [head,tail,rad]
        if len(self.clusterCenterCyl) > len(pairs):
            for j in range(len(pairs),len(self.clusterCenterCyl)):
#            for cy in self.clusterCenterCyl[len(pair):]:
#                o=self.clusterCenterCyl[]   
                self.helper.deleteObject("clbond"+str(j))
#            self.clusterCenterCyl = self.clusterCenterCyl[:len(pairs)]
                                    
    def kmeans(self,points, k, cutoff, initial=None):
        # Randomly sample k Points from the points list, build Clusters around them
        if initial is None:
            # Randomly sample k Points from the points list, build Clusters around them
            initial = random.sample(self.points, k)
        else:
            assert len(initial)==k
    
        clusters = []
        for p in initial: clusters.append(Cluster([p]))
        # Enter the program loop
        while True:
            # Make a list for each Cluster
            lists = []
            for c in clusters: lists.append([])
            # For each Point:
            for p in points:
                # Figure out which Cluster's centroid is the nearest
                x1,y1,z1 = p.coords
                x2,y2,z2 = clusters[0].centroid.coords
                smallest_distance = sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) +
                                          (z1-z2)*(z1-z2) )
                index = 0
                for i in range(len(clusters[1:])):
                    x2,y2,z2 = clusters[i+1].centroid.coords
                    distance = sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) +
                                     (z1-z2)*(z1-z2) )
                    if distance < smallest_distance:
                        smallest_distance = distance
                        index = i+1
                # Add this Point to that Cluster's corresponding list
                lists[index].append(p)
            # Update each Cluster with the corresponding list
            # Record the biggest centroid shift for any Cluster
            biggest_shift = 0.0
            for i in range(len(clusters)):
                if len(lists[i]):
                    shift = clusters[i].update(lists[i])
                    biggest_shift = max(biggest_shift, shift)
            # If the biggest centroid shift is less than the cutoff, stop
            if biggest_shift < cutoff: break
        # Return the list of Clusters
        return clusters

    def getCurrentSelectedPoints(self):
        #molkit ? sphere ?
        #lets first get the selection
        points = [] 
        if self.object_target is None :
            sel= self.helper.getCurrentSelection()
            if len(sel) == 1 :
                self.object_target = sel[0]
                self.object_target_name = self.helper.getName(self.object_target)
                #type of seletcted object ?
                for s in sel :
                    print ("type",self.helper.getType(s),self.helper.MESH,self.helper.POLYGON)
                if self.helper.getType(sel[0]) == self.helper.POLYGON or self.helper.getType(sel[0]) == self.helper.MESH:
#                    points,point_index= self.helper.getMeshVertices(sel[0],selected=True)#selected ? not working in maya for ow
#                    if not len(points) :
#                        points= self.helper.getMeshVertices(sel[0])
                    points = self.helper.getMeshVertices(sel[0],transform=True)
                    print ("pts ",len(points))
            else :
                points=[self.helper.ToVec(self.helper.getTranslation(x)) for x in sel]
        else :
           if self.helper.getType(self.object_target) == self.helper.POLYGON or self.helper.getType(self.object_target) == self.helper.MESH: 
                    points = self.helper.getMeshVertices(self.object_target,transform=True)               
        print ("pts ",len(points))
        return points

    def gridify(self,*args):
        #take the selected object and create a new object that are the point inside
        #use a default stepsize for the grid
        #use some usefull tools from histovol.grid ?
        #probably need the normal for that
        mode = self.getVal(self.mode)
        step = self.getVal(self.grid_step)
        if self.object_target is None :
            self.object_target = self.helper.getCurrentSelection()[0]
        mesh = self.object_target
        #canwe usethe ogranelle mesh system from autofill
        from AutoFill.Organelle import Organelle
        faces,vertices,vnormals,fn = self.helper.DecomposeMesh(mesh,
                                    edit=False,copy=False,tri=True,transform=True,fn=True)
        o1 = Organelle(self.helper.getName(mesh),vertices, faces, vnormals,fnormals=fn)
        o1.ref_obj = mesh
        o1.number = 1
        b=self.helper.getObject("BBOX")
        if b is None :
            b = self.helper.Box("BBOX", cornerPoints=o1.bb)
            bb=o1.bb
        else :
            bb=self.helper.getCornerPointCube(b)
        display = self.getVal(self.rt_display)
        useFix= self.getVal(self.useFix)
        if mode =="bhtree_dot":
            inner, surface = o1.getSurfaceInnerPoints(bb,step,display=display,useFix=useFix)
        elif mode ==  "sdf_fixdimension":
            inner, surface = o1.getSurfaceInnerPoints_sdf(bb,step,display=display,useFix=useFix)
        elif mode ==  "sdf_interpolate":
            inner, surface = o1.getSurfaceInnerPoints_sdf_interpolate(bb,step,display=display,useFix=useFix)
        elif mode ==  "jordan_raycast":
            inner, surface = o1.getSurfaceInnerPoints_jordan(bb,step,display=display,useFix=useFix)
        elif mode ==  "jordan_3raycast":
            inner, surface = o1.getSurfaceInnerPoints_jordan(bb,step,display=display,useFix=useFix,ray=3)
#        inner, surface = o1.getSurfaceInnerPoints(bb,step,display=display,useFix=useFix)
        n1=n=o1.name+"_innerPts"
        n2=o1.name+"_surfacePts"
        if self.helper.host == "maya" :
            n=o1.name+"_innerPtsds"
        s = self.helper.getObject(n)
        if s is None :
            s = self.helper.PointCloudObject(n1, vertices=inner )
            s2 = self.helper.PointCloudObject(n2, vertices=surface )
        else :
            if self.helper.host == "c4d" :
                self.helper.updateMesh(s,vertices=inner)
            else :
                self.helper.updateParticle(s,inner,None)
#            self.helper.updateMesh(s2,vertices=surface)
            
    def clearPoints(self,*args):
        name = self.helper.getName(self.object_target)
#        n1 = name+"_innerPts"
#        n2 = name+"_surfacePts"
#        if self.helper.host == "maya" :
        n1 = name+"_innerPtsds"
        n2 = name+"_surfacePtsds"
        s = self.helper.getObject(n1)
        if s is not None :
            instances = self.helper.getChilds(s)
            [self.helper.deleteObject(o) for o in instances]
            self.helper.deleteObject(s) #is this dleete the child ?
            s2 = self.helper.getObject(n2)
            if s2 is not None :
                instances = self.helper.getChilds(s2)
                [self.helper.deleteObject(o) for o in instances]
                self.helper.deleteObject(s2) #is this dleete the child ?
            
#if __name__ == '__main__' or __name__ == 'c4d': 
#    #create the gui
#    if uiadaptor.host == "tk":
#        from DejaVu import Viewer
#        vi = Viewer()    
#        #require a master   
#        mygui = clusterGui(master=vi)
#    else :
#        mygui = clusterGui()
#    #call it
#    mygui.display()

#execfile('/Library/MGLTools/1.5.6.up/MGLToolsPckgs/AutoFill/scripts/clusterGUIp.py')
