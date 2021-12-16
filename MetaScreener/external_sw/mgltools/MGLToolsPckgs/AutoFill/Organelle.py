# -*- coding: utf-8 -*-
"""
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010 
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input 
#   from Arthur Olson's Molecular Graphics Lab
#
# Organelle.py Authors: Graham Johnson & Michel Sanner with editing/enhancement from Ludovic Autin
#
# Translation to Python initiated March 1, 2010 by Michel Sanner with Graham Johnson
#
# Class restructuring and organization: Michel Sanner
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
@author: Graham Johnson, Ludovic Autin, & Michel Sanner

# Hybrid version merged from Graham's Sept 6, 2011 and Ludo's April 2012
#version on May 16, 2012, remerged on July 5, 2012 with thesis versions
"""

# Hybrid version merged from Graham's Sept 2011 and Ludo's April 2012 version on May 16, 2012
# Updated with Sept 16, 2011 thesis versions on July 5, 2012

# TODO: Describe Organelle class here at high level

# TODO: Graham and Ludovic implemented a 2D density function to obtain target numbers for
#   filling surfaces.  This should be formalized and named something other than molarity
#   or molarity should be converted to a 2D value behind the scenes.
# IDEA: We should offer the user an option to override molarity with a specific
#   number, e.g., "I want to place 3 1xyz.pdb files in organelle A" rather than
#   forcing them to calculate- "I need to place 0.00071M of 1xyz.pdb to get 3 of them
#   in an organelle A of volume=V."

## IDEAS

## randomly select recipe and then randomly select free point in set of free
## points corresponding to this recipe would allow giving surface more
## chances to get filled

## NOTE changing smallest molecule radius changes grid spacing and invalidates
##      arrays saved to file
import sys
import numpy.oldnumeric as N
import numpy, pickle, weakref, pdb
from time import time,sleep
from .ray import vlen, vdiff, vcross
import math
from math import sqrt,ceil
import os
try :
    import urllib.request as urllib# , urllib.parse, urllib.error
except :
    import urllib

#from .Ingredient import Ingredient
from .Recipe import Recipe
#print "import AutoFill"
import AutoFill
from AutoFill import checkURL

AFDIR = AutoFill.__path__[0]

try :
    helper = AutoFill.helper
except :
    helper = None
print ("helper is "+str(helper))

from AutoFill import intersect_RayTriangle as iRT
#from AutoFill.HistoVol import Grid   
if sys.version > "3.0.0":
    xrange = range
    
class OrganelleList:
    
    def __init__(self):
        # list of organelles inside this organelle
        self.organelles = []

        # point to parent organelle or HistoVol
        self.parent = None

    def addOrganelle(self, organelle):
        assert organelle.parent == None
        assert isinstance(organelle, Organelle)
        self.organelles.append(organelle)
        organelle.parent = self


#from ray import ray_intersect_polyhedron

class Organelle(OrganelleList):
    """
    This class represents a sub-cellular volume delimited by a polyhedral
    surface. Organelles can be nested
    """

    def __init__(self, name, vertices, faces, vnormals, **kw):
        OrganelleList.__init__(self)
        #print ("organelle init",name,kw)
        self.name = name
        self.vertices = vertices
        self.faces = faces
        self.vnormals = vnormals
        self.fnormals = None
        if "fnormals" in kw :
            self.fnormals = kw["fnormals"]
        self.mesh = None
        self.gname= ""
        self.ghost =False
        self.bb = None
        if "ghost" in kw :
            self.ghost = kw["ghost"]
        self.ref_obj = None
        if "ref_obj" in kw :
            self.ref_obj = kw["ref_obj"]
        if vertices == None :
            if "filename" in kw :
                self.faces,self.vertices,self.vnormals = self.getMesh(filename=kw["filename"])
                self.filename=kw["filename"]
                self.ref_obj = name
                #print ("mesh",self.name,self.filename)
        if self.vertices is not None and len(self.vertices):
            #can be dae/fbx file, object name that have to be in the scene or dejaVu indexedpolygon file
            self.bb = self.getBoundingBox()
        self.checkinside = True
        self.representation = None
        self.representation_file = None
        if "object_name" in kw :
            if kw["object_name"] is not None:
                #print ("rep",kw["object_name"],kw["object_filename"])
                self.representation = kw["object_name"]
                self.representation_file =  kw["object_filename"]
                self.getMesh(filename=self.representation_file,rep=self.representation)
        self.innerRecipe = None
        self.surfaceRecipe = None
        self.surfaceVolume = 0.0
        self.interiorVolume = 0.0
        
        # list of grid point indices inside organelle
        self.insidePoints = None
        # list of grid point indices on organelle surface
        self.surfacePoints = None
        self.surfacePointsNormals = {} # will be point index:normal
        
        self.number = None # will be set to an integer when this organelle
                           # is added to a HistoVol. Positivefor surface pts
                           # negative for interior points
#        self.parent = None
        self.molecules = [] 
        # list of ( (x,y,z), rotation, ingredient) triplet generated by fill 
        self.overwriteSurfacePts = True 
        # do we discretize surface point per edges
        self.highresVertices = None 
        # if a highres vertices is provided this give the surface point, 
        #not the one provides
        self.isBox = False #the organelle shape is a box, no need 
        #to compute inside points.
        if "isBox" in kw :
            self.isBox = kw["isBox"]
                
        self.isOrthogonalBoudingBox = None #the organelle shape is a box, no need
        #to compute inside points.
        if "isOrthogonalBoudingBox" in kw :
            self.isOrthogonalBoudingBox = kw["isOrthogonalBoudingBox"]

    def reset(self):
        # list of grid point indices inside organelle
        self.insidePoints = None
        # list of grid point indices on organelle surface
        self.surfacePoints = None
        self.surfacePointsNormals = {} # will be point index:normal
        self.molecules = [] 
        

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
        print ("dejavu mesh", filename)        
        geom = IndexedPolygonsFromFile(filename, 'mesh_%s'%self.name)
#        if helper is not None:
#            helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0])
        return geom
        
    def getMesh(self,filename=None,rep=None,**kw):
        geom = None
        gname = self.name
        helper = AutoFill.helper
        parent=helper.getObject("AutoFillHider")
        if parent is None:
            parent = helper.newEmpty("AutoFillHider")
        if rep is not None :
            gname =rep 
            parent=helper.getObject('O%s'%self.name)
        print ("organelle",filename,gname,rep,parent)
        if filename.find("http") != -1 or filename.find("ftp")!= -1 :
            try :
                import urllib.request as urllib# , urllib.parse, urllib.error
            except :
                import urllib
            name =   filename.split("/")[-1]
            fileName, fileExtension = os.path.splitext(name)
            tmpFileName = AFDIR+os.sep+"cache_ingredients"+os.sep+name
            print("try to get from cache "+name+" "+fileExtension,fileExtension.find(".fbx"),fileExtension.find(".dae"))
            if fileExtension is '' :   
#            if fileExtension.find(".fbx") == -1 and fileExtension.find(".dae") == -1:
                #need to getboth file
                tmpFileName1 = AFDIR+os.sep+"cache_ingredients"+os.sep+name+".indpolface"
                tmpFileName2 = AFDIR+os.sep+"cache_ingredients"+os.sep+name+".indpolvert"
#                print("#check if exist first1",tmpFileName1)
                #check if exist first
                if not os.path.isfile(tmpFileName1) or AutoFill.forceFetch:
#                    print "download "+filename+".indpolface"
#                    print "download "+filename+".indpolvert"
                    if checkURL(filename+".indpolface"):
                        try :
                            urllib.urlretrieve(filename+".indpolface", tmpFileName1)
                        except :
                            print ("problem downloading "+filename+".indpolface to"+tmpFileName1)
                    else :
                        if not os.path.isfile(tmpFileName1)  :
                            print ("problem downloading "+filename+".indpolface to"+tmpFileName1)
                            return
                if not os.path.isfile(tmpFileName2):
                    if checkURL(filename+".indpolvert"):
                        try :
                            urllib.urlretrieve(filename+".indpolvert", tmpFileName2)
                        except :
                            print ("problem downloading "+filename+".indpolface to"+tmpFileName2)
                    else :
                        if not os.path.isfile(tmpFileName2)  :
                            print ("problem downloading "+filename+".indpolface to"+tmpFileName1)
                            return
            else :
                tmpFileName = AFDIR+os.sep+"cache_ingredients"+os.sep+name
                print("#check if exist first",tmpFileName,os.path.isfile(tmpFileName))
                if not os.path.isfile(tmpFileName) or AutoFill.forceFetch:
                    print("urlretrieve and fetch")
                    if checkURL(filename):
                        urllib.urlretrieve(filename, tmpFileName)
                    else :
                        if not os.path.isfile(tmpFileName)  :
                            print ("problem downloading "+filename)
                            return
                        
            filename = tmpFileName 
        fileName, fileExtension = os.path.splitext(filename)
        print('found fileName '+fileName+' fileExtension '+fileExtension)
        if fileExtension.lower() == ".fbx":
            print ("read withHelper",filename)
            #use the host helper if any to read
            if helper is not None:#neeed the helper
                helper.read(filename)
                geom = helper.getObject(gname)
                #reparent to the fill parent
                if helper.host == "3dsmax" :
                    helper.resetTransformation(geom)#remove rotation and scale from importing
                if helper.host != "c4d" and rep == None  and helper.host != "softimage":
                    #need to rotate the transform that carry the shape
                    helper.rotateObj(geom,[0.,-math.pi/2.0,0.0])
                if helper.host =="softimage"  :
                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0],primitive=True)#need to rotate the primitive                    
#                p=helper.getObject("AutoFillHider")
#                if p is None:
#                    p = helper.newEmpty("AutoFillHider")
#                    helper.toggleDisplay(p,False)
                helper.reParent(geom,parent)
#                return geom
#            return None
        elif fileExtension == ".dae":
            #use the host helper if any to read
            if helper is not None:#neeed the helper
                helper.read(filename)
                geom = helper.getObject(gname)
                print ("should have read...",gname,geom,parent)
#                helper.update()
                if helper.host == "3dsmax" :
                    helper.resetTransformation(geom)#remove rotation and scale from importing
                if helper.host != "c4d"  and helper.host != "dejavu" and helper.host != "softimage":#and helper.host != "dejavu" 
                    #need to rotate the transform that carry the shape, depends on left hand / right hand
                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0])#wayfront as well euler angle
                if helper.host =="softimage"  :
                    helper.rotateObj(geom,[0.0,-math.pi/2.0,0.0],primitive=True)#need to rotate the primitive                    
#                p=helper.getObject("AutoFillHider")
#                if p is None:
#                    p = helper.newEmpty("AutoFillHider")
#                    helper.toggleDisplay(p,False)
                print ("reparent ",geom,parent)
                helper.reParent(geom,parent)   
#                return geom
#            return None
        elif fileExtension is '' :
            geom =  self.getDejaVuMesh(filename, gname)
        else :#speficif host file
            if helper is not None:#neeed the helper
                helper.read(filename)
                geom = helper.getObject(gname)
#                p=helper.getObject("AutoFillHider")
#                if p is None:
#                    p = helper.newEmpty("AutoFillHider")
#                    helper.toggleDisplay(p,False)
                helper.reParent(geom,parent) 
        if rep is None:
            print ("should toggle the mesh",geom,gname,helper.host,( helper.host == "dejavu"))
            if helper.host.find("blender") == -1 :
                helper.toggleDisplay(parent,False) 
            if helper.host == "dejavu":
                helper.toggleDisplay(geom,False)  
        else :
            return None 
        self.gname = gname                    
        if geom is not None and fileExtension != '' and not self.ghost:
            faces,vertices,vnormals = helper.DecomposeMesh(geom,
                                edit=False,copy=False,tri=True,transform=True)
            if helper.host == "dejavu":
                helper.deleteObject(geom)
            return faces,vertices,vnormals
        else :
            if self.ghost:
                return [],[],[]
            faces = geom.getFaces()
            vertices = geom.getVertices()
            vnormals = geom.getVNormals()       
            return faces,vertices,vnormals
        
    def setMesh(self, filename=None,vertices=None, 
                faces=None, vnormals=None, **kw )   :
        if vertices is None and filename is not None:
            self.faces,self.vertices,self.vnormals = self.getMesh(filename)
        else :
            self.vertices = vertices
            self.faces = faces
            self.vnormals = vnormals
        if "fnormals" in kw :
            self.fnormals = kw["fnormals"]
        self.mesh = None
        self.ref_obj = filename 
        self.bb = self.getBoundingBox()

    def saveGridToFile(self, f):
        """Save insidePoints and surfacePoints to file"""
        #print 'surface', len(self.surfacePoints)
        pickle.dump(self.insidePoints, f)
        #print 'interior', len(self.surfacePoints)
        pickle.dump(self.surfacePoints, f)
        pickle.dump(self.surfacePointsNormals, f)
        pickle.dump(self.surfacePointsCoords, f)
        
    def readGridFromFile(self, f):
        """read insidePoints and surfacePoints from file"""
        self.insidePoints = insidePoints = pickle.load(f)
        self.surfacePoints = surfacePoints = pickle.load(f)
        self.surfacePointsNormals = surfacePointsNormals = pickle.load(f)
        self.surfacePointscoords = surfacePointscoords = pickle.load(f)
        return surfacePoints, insidePoints, surfacePointsNormals,surfacePointscoords
        #surfacePointscoords = pickle.load(f)
        #return surfacePoints, insidePoints, surfacePointsNormals, \
        #       surfacePointscoords
        
    def setNumber(self, num):
        self.number = num

    def setInnerRecipe(self, recipe):
        assert self.number is not None
        assert isinstance(recipe, Recipe)
        self.innerRecipe = recipe
        self.innerRecipe.number= self.number
        recipe.organelle = weakref.ref(self)
        for ingr in recipe.ingredients:
            ingr.compNum = -self.number

    def setSurfaceRecipe(self, recipe):
        assert self.number is not None
        assert isinstance(recipe, Recipe)
        self.surfaceRecipe = recipe
        self.surfaceRecipe.number= self.number
        recipe.organelle = weakref.ref(self)
        for ingr in recipe.ingredients:
            ingr.compNum = self.number

    def getCenter(self):
        coords = numpy.array(self.vertices)#self.allAtoms.coords
        center = sum(coords)/(len(coords)*1.0)
        center = list(center)
        for i in range(3):
            center[i] = round(center[i], 4)
#        print "center =", center
        self.center = center
    
    def getRadius(self):
        #should be mini - center ?
        import math
        d = self.center - self.bb[0]
        s = numpy.sum(d*d)
        return math.sqrt(s)
        
    def getBoundingBox(self):
        mini = numpy.min(self.vertices, 0)
        maxi = numpy.max(self.vertices, 0)
        return (mini, maxi)

    def getSizeXYZ(self):
        sizexyz=[0,0,0]
        for i in range(3):
            sizexyz[i] = self.bb[1][i] - self.bb[0][i]
        return sizexyz
        
    def checkPointInsideBBold(self,pt3d,dist=None):
        O = numpy.array(self.bb[0])
        E = numpy.array(self.bb[1])
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
 
    def checkPointInsideBB(self,pt3d,dist=None):
        O = numpy.array(self.bb[0])
        E = numpy.array(self.bb[1])
        P = numpy.array(pt3d)
        
        #a point is inside is  < min and > maxi etc.. 
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
 
    def inBox(self, box):
        """
        check if bounding box of this organelle fits inside the give box
        returns true or false and the extended bounding box if this organelle
        did not fit
        """
        if self.ghost:
            return False, None
        bb = self.bb
        xm,ym,zm = box[0]
        xM,yM,zM = box[1]
        # padding 50 shows problem
        padding = 0.
        
        newBB = [box[0][:], box[1][:]]
        fits = True

        if xm > bb[0][0] - padding:
            newBB[0][0] = bb[0][0] - padding
            fits = False

        if ym > bb[0][1] - padding:
            newBB[0][1] = bb[0][1] - padding
            fits = False

        if zm > bb[0][2] - padding:
            newBB[0][2] = bb[0][2] - padding
            fits = False

        if xM < bb[1][0] + padding:
            newBB[1][0] = bb[1][0] + padding
            fits = False

        if yM < bb[1][1] + padding:
            newBB[1][1] = bb[1][1] + padding
            fits = False

        if zM < bb[1][2] + padding:
            newBB[1][2] = bb[1][2] + padding
            fits = False

        return fits, newBB

    def inGrid(self, point, fillBB):
        """
        check if bounding box of this organelle fits inside the give box
        returns true or false and the extended bounding box if this organelle
        did not fit
        """
        mini, maxi = fillBB
        mx, my, mz = mini
        Mx, My, Mz = maxi
        x,y,z = point
        if (x>=mx and x<=Mx and y>=my and y<=My and z>=mz and z<=Mz):
            return True
        else :
            return False

    def getMinMaxProteinSize(self):
        #for organelle in self.organelles:
        #    mini, maxi = organelle.getSmallestProteinSize(size)
        mini1 = mini2 = 9999999.
        maxi1 = maxi2 = 0.
        if self.surfaceRecipe:
            mini1, maxi1 = self.surfaceRecipe.getMinMaxProteinSize()
        if self.innerRecipe:
            mini2, maxi2 = self.innerRecipe.getMinMaxProteinSize()
        return min(mini1, mini2), max(maxi1, maxi2)

    def getFaceNormals(self, vertices, faces,fillBB=None):
        normals = []
        areas = [] #added by Graham
        face = [[0,0,0],[0,0,0],[0,0,0]]
        v = [[0,0,0],[0,0,0],[0,0,0]]        
        for f in faces:
            for i in range(3) :
                face [i] = vertices[f[i]]
            for i in range(3) :
                v[0][i] = face[1][i]-face[0][i]
                v[1][i] = face[2][i]-face[0][i]                
#            face [0] =  = vertices[f[0]]#x1,y1,z1
#            face [1] = = vertices[f[1]]# x2,y2,z2
#            face [2] =  = vertices[f[2]]#x3,y3,z3
#            v1 = (x2-x1, y2-y1, z2-z1)
#            v2 = (x3-x1, y3-y1, z3-z1)
            normal = vcross(v[0],v[1])
            n = vlen(normal)
            if n == 0. :
                n1=1.
            else :
                n1 = 1./n
            normals.append( (normal[0]*n1, normal[1]*n1, normal[2]*n1) )
            if fillBB is not None:
                if self.inGrid(vertices[f[0]],fillBB) and self.inGrid(vertices[f[0]],fillBB) and self.inGrid(vertices[f[0]],fillBB):
#                    area =  #added by Graham
                    areas.append(0.5*vlen(normal)) #added by Graham
        return normals, areas #areas added by Graham


    def getInterpolatedNormal(self, pt, tri):
        v1,v2,v3 = self.faces[tri]
        verts = self.vertices
        d1 = vlen(vdiff(pt, verts[v1]))
        d2 = vlen(vdiff(pt, verts[v2]))
        d3 = vlen(vdiff(pt, verts[v3]))
        sumlen1 = d1+d2+d3
        w1 = sumlen1/d1
        w2 = sumlen1/d2
        w3 = sumlen1/d3
        n1 = self.vnormals[v1]
        n2 = self.vnormals[v2]
        n3 = self.vnormals[v3]
        norm = ( (n1[0]*w1 + n2[0]*w2 +n3[0]*w3),
                 (n1[1]*w1 + n2[1]*w2 +n3[1]*w3),
                 (n1[2]*w1 + n2[2]*w2 +n3[2]*w3) )
        l1 = 1./vlen(norm)
        return ( norm[0]*l1, norm[1]*l1, norm[2]*l1 )





    def createSurfacePoints(self, maxl=20):
        """
        create points inside edges and faces with max distance between then maxl
        creates self.surfacePoints and self.surfacePointsNormals
        """

        vertices = self.vertices
        faces = self.faces
        vnormals = self.vnormals
        
        points = list(vertices)[:]
        normals = list(vnormals)[:]

        # create points in edges
        edges = {}
        for fn, tri in enumerate(faces):
            s1,s2 = tri[0],tri[1]
            if (s2, s1) in edges:
                edges[(s2,s1)].append(fn)
            else:
                edges[(s1,s2)] = [fn]

            s1,s2 = tri[1],tri[2]
            if (s2, s1) in edges:
                edges[(s2,s1)].append(fn)
            else:
                edges[(s1,s2)] = [fn]

            s1,s2 = tri[2],tri[0]
            if (s2, s1) in edges:
                edges[(s2,s1)].append(fn)
            else:
                edges[(s1,s2)] = [fn]

        lengths = list(map(len, list(edges.values())))
        assert max(lengths)==2
        assert min(lengths)==2

        for edge, faceInd in list(edges.items()):
            s1, s2 = edge
            p1 = vertices[s1]
            p2 = vertices[s2]
            v1 = vdiff(p2, p1) # p1->p2
            l1 = vlen(v1)
            if l1 <= maxl: continue

            # compute number of points
            nbp1 = int(l1 / maxl)
            if nbp1<1: continue

            # compute interval size to spread the points
            dl1 = l1/(nbp1+1)

            # compute interval vector
            dx1 = dl1*v1[0]/l1
            dy1 = dl1*v1[1]/l1
            dz1 = dl1*v1[2]/l1
            x, y, z = p1
            nx1, ny1, nz1 = vnormals[s1]
            nx2, ny2, nz2 = vnormals[s2]
            edgeNorm = ( (nx1+nx2)*.5,  (ny1+ny2)*.5,  (nz1+nz2)*.5 )
            for i in range(1, nbp1+1):
                points.append( (x + i*dx1, y + i*dy1, z + i*dz1) )
                normals.append( edgeNorm )

        for fn,t in enumerate(faces):
            #if t[0]==16 and t[1]==6 and t[2]==11:
            #    pdb.set_trace()
            pa = vertices[t[0]]
            pb = vertices[t[1]]
            pc = vertices[t[2]]

            va = vdiff(pb, pa) # p1->p2
            la = vlen(va)
            if la <= maxl: continue

            vb = vdiff(pc, pb) # p2->p3
            lb = vlen(vb)
            if lb <= maxl: continue

            vc = vdiff(pa, pc) # p3->p1
            lc = vlen(vc)
            if lc <= maxl: continue

            #if fn==0:
            #    pdb.set_trace()
            # pick shortest edge to be second vector
            if la<=lb and la<=lc:
                p1 = pc
                p2 = pa
                p3 = pb
                v1 = vc
                l1 = lc
                v2 = va
                l2 = la
                v3 = vb

            if lb<=la and lb<=lc:
                p1 = pa
                p2 = pb
                p3 = pc
                v1 = va
                l1 = la
                v2 = vb
                l2 = lb
                v3 = vc

            if lc<=lb and lc<=la:
                p1 = pb
                p2 = pc
                p3 = pa
                v1 = vb
                l1 = lb
                v2 = vc
                l2 = lc
                v3 = va

            lengthRatio = l2/l1

            nbp1 = int(l1 / maxl)
            if nbp1<1: continue

            dl1 = l1/(nbp1+1)
            #if dl1<15:
            #    pdb.set_trace()
            #print l1, nbp1, dl1, lengthRatio
            dx1 = dl1*v1[0]/l1
            dy1 = dl1*v1[1]/l1
            dz1 = dl1*v1[2]/l1
            x,y,z = p1
            fn = vcross(v1, (-v3[0], -v3[1], -v3[2]) )
            fnl = 1.0/vlen(fn)
            faceNorm = ( (fn[0]*fnl, fn[1]*fnl, fn[2]*fnl) )

            for i in range(1, nbp1+1):
                l2c = (i*dl1)*lengthRatio
                nbp2 = int(l2c/maxl)
#                percentage = (i*dl1)/l1
                #nbp2 = int(l2*lengthRatio*percentage/maxl)
                if nbp2<1: continue
                #dl2 = l2*percentage/(nbp2+1)
                dl2 = l2c/(nbp2+1)
                #print '   ',i, percentage, dl1, l2c, dl2, nbp2, l2
                #if dl2<15:
                #    pdb.set_trace()

                dx2 = dl2*v2[0]/l2
                dy2 = dl2*v2[1]/l2
                dz2 = dl2*v2[2]/l2
                for j in range(1, nbp2+1):
                    points.append( (
                        x + i*dx1 + j*dx2, y + i*dy1 + j*dy2, z + i*dz1 + j*dz2) )
                    normals.append(faceNorm)

        self.ogsurfacePoints = points
        self.ogsurfacePointsNormals = normals

    #Jordan Curve Theorem
    def BuildGridJordan(self, histoVol,ray=1):
        # create surface points 
        if self.ghost : return
        t0 = t1 = time()        
        if self.isBox :
            self.overwriteSurfacePts = True
        if self.overwriteSurfacePts:
            self.ogsurfacePoints = self.vertices[:]
            self.ogsurfacePointsNormals = self.vnormals[:]
        else :
            self.createSurfacePoints(maxl=histoVol.grid.gridSpacing)
#        helper = None
#        afvi = None
#        if hasattr(histoVol,"afviewer"):
#            if histoVol.afviewer is not None and hasattr(histoVol.afviewer,"vi"):
#                helper = histoVol.afviewer.vi
#            afvi = histoVol.afviewer       
        
        # Graham Sum the SurfaceArea for each polyhedron
        vertices = self.vertices  #NEED to make these limited to selection box, not whole organelle
        faces = self.faces #         Should be able to use self.ogsurfacePoints and collect faces too from above
        normalList2,areas = self.getFaceNormals(vertices, faces,fillBB=histoVol.fillBB)
        vSurfaceArea = sum(areas)
        #for gnum in range(len(normalList2)):
        #    vSurfaceArea = vSurfaceArea + areas[gnum]
#        print 'Graham says Surface Area is %d' %(vSurfaceArea)
#        print 'Graham says the last triangle area is is %d' %(areas[-1])
        #print '%d surface points %.2f unitVol'%(len(surfacePoints), unitVol)
        
        # build a BHTree for the vertices
        if self.isBox :
            nbGridPoints = len(histoVol.grid.masterGridPositions)
            insidePoints = histoVol.grid.getPointsInCube(self.bb, None, 
                                                None,addSP=False)     
            for p in insidePoints : histoVol.grid.gridPtId[p]=-self.number
            print('is BOX Total time', time()-t0)
            surfPtsBB,surfPtsBBNorms = self.getSurfaceBB(self.ogsurfacePoints,histoVol)
            srfPts = surfPtsBB
            surfacePoints,surfacePointsNormals  = self.extendGridArrays(nbGridPoints,srfPts,
                        surfPtsBBNorms,histoVol)
            self.insidePoints = insidePoints
            self.surfacePoints = surfacePoints
            self.surfacePointsCoords = surfPtsBB
            self.surfacePointsNormals = surfacePointsNormals
            print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
                len(self.surfacePoints), len(self.insidePoints),
                nbGridPoints, len(histoVol.grid.masterGridPositions)))
        
            self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                          self.insidePoints,areas=vSurfaceArea)    
            print('time to create surface points', time()-t1, len(self.ogsurfacePoints))
            return self.insidePoints, self.surfacePoints
        
        print('time to create surface points', time()-t1, len(self.ogsurfacePoints))

        distances = histoVol.grid.distToClosestSurf
        idarray = histoVol.grid.gridPtId
        diag = histoVol.grid.diag

        t1 = time()

        #build BHTree for off grid surface points
        from bhtree import bhtreelib
        srfPts = self.ogsurfacePoints
#        print len(srfPts),srfPts[0]
#        stemp = afvi.vi.Points("surfacePts", vertices=self.ogsurfacePoints, materials=[[0,1,0],],
#                   inheritMaterial=0, pointWidth=5., inheritPointWidth=0,
#                   visible=1,parent=None)
#        stemp = afvi.vi.Points("surfacePts2", vertices=histoVol.grid.masterGridPositions, materials=[[0,1,0],],
#                   inheritMaterial=0, pointWidth=5., inheritPointWidth=0,
#                   visible=1,parent=None)
        #??why the bhtree behave like this
        self.OGsrfPtsBht = bht =  bhtreelib.BHtree(tuple(srfPts), None, 10)
        res = numpy.zeros(len(srfPts),'f')
        dist2 = numpy.zeros(len(srfPts),'f')
#        print "nspt",len(srfPts)
#        print srfPts
        number = self.number
        ogNormals = self.ogsurfacePointsNormals
        insidePoints = []

        # find closest off grid surface point for each grid point 
        #FIXME sould be diag of organelle BB inside fillBB
        grdPos = histoVol.grid.masterGridPositions
        returnNullIfFail = 0
        print ("organelle build grid ",grdPos,"XX",diag,"XX",len(grdPos))#[],None
        closest = bht.closestPointsArray(tuple(grdPos), diag, returnNullIfFail)
        helper = AutoFill.helper
        geom =   helper.getObject(self.gname)      
        if geom is None :
            self.gname = '%s_Mesh'%self.name            
            geom = helper.getObject(self.gname)
        center = helper.getTranslation( geom )
#        print len(closest),diag,closest[0]
#        print closest
#        bhtreelib.freeBHtree(bht)
        self.closestId = closest
#        print len(self.closestId)
#would it be faster using c4d vector ? or hots system?
##        import c4d
#        c4d.StatusSetBar(0)
        helper.resetProgressBar()
        for ptInd in range(len(grdPos)):#len(grdPos)):
            # find closest OGsurfacepoint
            inside = False
            gx, gy, gz = grdPos[ptInd]
            sptInd = closest[ptInd]
            if closest[ptInd]==-1:
                print("ouhoua, closest OGsurfacePoint = -1")
                #pdb.set_trace()#???  Can be used to debug with http://docs.python.org/library/pdb.html
            if sptInd < len(srfPts):
                sx, sy, sz = srfPts[sptInd]
                d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
                          (gz-sz)*(gz-sz))
            else :
                try :
                    n=bht.closePointsDist2(tuple(grdPos[ptInd]),diag,res,dist2)
                    d = min(dist2[0:n])
                    sptInd = res[tuple(dist2).index(d)]
                except :
                    #this is quite long
                    delta = numpy.array(srfPts)-numpy.array(grdPos[ptInd])
                    delta *= delta
                    distA = numpy.sqrt( delta.sum(1) )
                    d = min(distA)
                    sptInd = list(distA).index(d)
                sx, sy, sz = srfPts[sptInd]
            if distances[ptInd]>d: distances[ptInd] = d  # case a diffent surface ends up being closer in the linear walk through the grid
            #should check if in organelle bounding box
            insideBB  = self.checkPointInsideBB(grdPos[ptInd],dist=d)
            r=False
            if insideBB:
                intersect, count = helper.raycast(geom, grdPos[ptInd], center, diag, count = True )
                r= ((count % 2) == 1)
                if ray == 3 :
                    intersect2, count2 = helper.raycast(geom, grdPos[ptInd], grdPos[ptInd]+[0.,0.,1.1], diag, count = True )
                    center = helper.rotatePoint(helper.ToVec(center),[0.,0.,0.],[1.0,0.0,0.0,math.radians(33.0)])
                    intersect3, count3 = helper.raycast(geom, grdPos[ptInd], grdPos[ptInd]+[0.,1.1,0.], diag, count = True )
                    if r :
                       if (count2 % 2) == 1 and (count3 % 2) == 1 :
                           r=True
                       else : 
                           r=False
            if r : # odd inside
                inside = True
#
#            # check if ptInd in inside
#            intersect, count = helper.raycast(geom, grdPos[ptInd], grdPos[ptInd]+[1.001,0.,0.], diag, count = True )
#            if (count % 2) == 1: # odd inside
                #and the point is actually inside the mesh bounding box
                inside = True
                if inside :
                    insidePoints.append(ptInd)
            p=(ptInd/float(len(grdPos)))*100.0
            helper.progressBar(progress=int(p),label=str(ptInd)+"/"+str(len(grdPos))+" inside "+str(inside))
        print('time to update distance field and idarray', time()-t1)
        
        t1 = time()
        nbGridPoints = len(histoVol.grid.masterGridPositions)
        
        surfPtsBB,surfPtsBBNorms = self.getSurfaceBB(srfPts,histoVol)
        srfPts = surfPtsBB
        print ("compare length id distances",nbGridPoints,(nbGridPoints == len(idarray)),(nbGridPoints == len(distances)))
        ex = True#True if nbGridPoints == len(idarray) else False
        surfacePoints,surfacePointsNormals  = self.extendGridArrays(nbGridPoints,
                                            srfPts,surfPtsBBNorms,histoVol,extended=ex)

        insidePoints = insidePoints
        print('time to extend arrays', time()-t1)

        print('Total time', time()-t0)

        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsCoords = surfPtsBB
        self.surfacePointsNormals = surfacePointsNormals
        print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
            len(self.surfacePoints), len(self.insidePoints),
            nbGridPoints, len(histoVol.grid.masterGridPositions)))

        self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                      self.insidePoints,areas=vSurfaceArea)
        bhtreelib.freeBHtree(bht)
        return self.insidePoints, self.surfacePoints
        
    def BuildGrid(self, histoVol):
        # create surface points 
        if self.ghost : return
        t0 = t1 = time()        
        if self.isBox :
            self.overwriteSurfacePts = True
        if self.overwriteSurfacePts:
            self.ogsurfacePoints = self.vertices[:]
            self.ogsurfacePointsNormals = self.vnormals[:]
        else :
            self.createSurfacePoints(maxl=histoVol.grid.gridSpacing)
#        helper = None
#        afvi = None
#        if hasattr(histoVol,"afviewer"):
#            if histoVol.afviewer is not None and hasattr(histoVol.afviewer,"vi"):
#                helper = histoVol.afviewer.vi
#            afvi = histoVol.afviewer       
        
        # Graham Sum the SurfaceArea for each polyhedron
        vertices = self.vertices  #NEED to make these limited to selection box, not whole organelle
        faces = self.faces #         Should be able to use self.ogsurfacePoints and collect faces too from above
        normalList2,areas = self.getFaceNormals(vertices, faces,fillBB=histoVol.fillBB)
        vSurfaceArea = sum(areas)
        #for gnum in range(len(normalList2)):
        #    vSurfaceArea = vSurfaceArea + areas[gnum]
#        print 'Graham says Surface Area is %d' %(vSurfaceArea)
#        print 'Graham says the last triangle area is is %d' %(areas[-1])
        #print '%d surface points %.2f unitVol'%(len(surfacePoints), unitVol)
        
        # build a BHTree for the vertices
        if self.isBox :
            nbGridPoints = len(histoVol.grid.masterGridPositions)
            insidePoints = histoVol.grid.getPointsInCube(self.bb, None, 
                                                None,addSP=False)     
            for p in insidePoints : histoVol.grid.gridPtId[p]=-self.number
            print('is BOX Total time', time()-t0)
            surfPtsBB,surfPtsBBNorms = self.getSurfaceBB(self.ogsurfacePoints,histoVol)
            srfPts = surfPtsBB
            surfacePoints,surfacePointsNormals  = self.extendGridArrays(nbGridPoints,srfPts,
                        surfPtsBBNorms,histoVol)
            self.insidePoints = insidePoints
            self.surfacePoints = surfacePoints
            self.surfacePointsCoords = surfPtsBB
            self.surfacePointsNormals = surfacePointsNormals
            print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
                len(self.surfacePoints), len(self.insidePoints),
                nbGridPoints, len(histoVol.grid.masterGridPositions)))
        
            self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                          self.insidePoints,areas=vSurfaceArea)    
            print('time to create surface points', time()-t1, len(self.ogsurfacePoints))
            return self.insidePoints, self.surfacePoints
        
        print('time to create surface points', time()-t1, len(self.ogsurfacePoints))

        distances = histoVol.grid.distToClosestSurf
        idarray = histoVol.grid.gridPtId
        diag = histoVol.grid.diag

        t1 = time()

        #build BHTree for off grid surface points
        from bhtree import bhtreelib
        srfPts = self.ogsurfacePoints
#        print len(srfPts),srfPts[0]
#        stemp = afvi.vi.Points("surfacePts", vertices=self.ogsurfacePoints, materials=[[0,1,0],],
#                   inheritMaterial=0, pointWidth=5., inheritPointWidth=0,
#                   visible=1,parent=None)
#        stemp = afvi.vi.Points("surfacePts2", vertices=histoVol.grid.masterGridPositions, materials=[[0,1,0],],
#                   inheritMaterial=0, pointWidth=5., inheritPointWidth=0,
#                   visible=1,parent=None)
        #??why the bhtree behave like this
        self.OGsrfPtsBht = bht =  bhtreelib.BHtree(tuple(srfPts), None, 10)
        res = numpy.zeros(len(srfPts),'f')
        dist2 = numpy.zeros(len(srfPts),'f')
#        print "nspt",len(srfPts)
#        print srfPts
        number = self.number
        ogNormals = self.ogsurfacePointsNormals
        insidePoints = []

        # find closest off grid surface point for each grid point 
        #FIXME sould be diag of organelle BB inside fillBB
        grdPos = histoVol.grid.masterGridPositions
        returnNullIfFail = 0
        print ("organelle build grid ","XX",diag,"XX",len(grdPos))#[],None
        closest = bht.closestPointsArray(tuple(grdPos), diag, returnNullIfFail)
        
#        print len(closest),diag,closest[0]
#        print closest
#        bhtreelib.freeBHtree(bht)
        self.closestId = closest
#        print len(self.closestId)
#would it be faster using c4d vector ? or hots system?
##        import c4d
#        c4d.StatusSetBar(0)
        for ptInd in range(len(grdPos)):#len(grdPos)):
            # find closest OGsurfacepoint
            gx, gy, gz = grdPos[ptInd]
            sptInd = closest[ptInd]
            if closest[ptInd]==-1:
                print("ouhoua, closest OGsurfacePoint = -1")
                #pdb.set_trace()#???  Can be used to debug with http://docs.python.org/library/pdb.html
            if sptInd < len(srfPts):
                sx, sy, sz = srfPts[sptInd]
                d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
                          (gz-sz)*(gz-sz))
            else :
                try :
                    n=bht.closePointsDist2(tuple(grdPos[ptInd]),diag,res,dist2)
                    d = min(dist2[0:n])
                    sptInd = res[tuple(dist2).index(d)]
                except :
                    #this is quite long
                    delta = numpy.array(srfPts)-numpy.array(grdPos[ptInd])
                    delta *= delta
                    distA = numpy.sqrt( delta.sum(1) )
                    d = min(distA)
                    sptInd = list(distA).index(d)
                sx, sy, sz = srfPts[sptInd]
#            target = afvi.vi.getObject("test")
#            if target is None :
#                target = afvi.vi.Sphere("test",radius=10.0,color=[0,0,1])[0]
#            afvi.vi.setTranslation(target,pos=srfPts[sptInd])
#            target2 = afvi.vi.getObject("test2")
#            if target2 is None :
#                target2 = afvi.vi.Sphere("test2",radius=10.0,color=[0,0,1])[0]
#            afvi.vi.changeObjColorMat(target2,[0,0,1])
#            afvi.vi.setTranslation(target2,pos=grdPos[ptInd])
#            afvi.vi.update()
            # update distance field
            # we should not reompute this ...
            #if ptInd < len(distances)-1:  # Oct. 20, 2012 Graham turned this if off because this dist override is necessary in
            if distances[ptInd]>d: distances[ptInd] = d  # case a diffent surface ends up being closer in the linear walk through the grid

            # check if ptInd in inside
            nx, ny, nz = numpy.array(ogNormals[sptInd])
#            target3 = afvi.vi.getObject("test3")
#            if target3 is None :
#                target3 = afvi.vi.Sphere("test3",radius=10.0,color=[0,0,1])[0]
#            afvi.vi.changeObjColorMat(target3,[0,0,1])
#            afvi.vi.setTranslation(target3,pos=numpy.array(srfPts[sptInd])+numpy.array(ogNormals[sptInd])*10.)
#            afvi.vi.update()
            
            # check on what side of the surface point the grid point is
            vx,vy,vz = (gx-sx, gy-sy, gz-sz)
            dot = vx*nx + vy*ny + vz*nz
            if dot <= 0: # inside
                #and the point is actually inside the mesh bounding box
                inside = True
                if self.checkinside :
                    inside  = self.checkPointInsideBB(grdPos[ptInd],dist=d)
                #this is not working for a plane, or any unclosed organelle...
                if inside :
                    if ptInd < len(idarray)-1:   #Oct 20, 2012 Graham asks: why do we do this if test? not in old code
                        idarray[ptInd] = -number
                    insidePoints.append(ptInd)
#                if target2 is not None :
#                    afvi.vi.changeObjColorMat(target2,[1,0,0])
            #sleep(0.01)
#            c4d.StatusSetBar(int((ptInd/len(grdPos)*100)))
        print('time to update distance field and idarray', time()-t1)
        
        t1 = time()
        nbGridPoints = len(histoVol.grid.masterGridPositions)
        
        surfPtsBB,surfPtsBBNorms = self.getSurfaceBB(srfPts,histoVol)
        srfPts = surfPtsBB
        print ("compare length id distances",nbGridPoints,(nbGridPoints == len(idarray)),(nbGridPoints == len(distances)))
        ex = True#True if nbGridPoints == len(idarray) else False
        surfacePoints,surfacePointsNormals  = self.extendGridArrays(nbGridPoints,
                                            srfPts,surfPtsBBNorms,histoVol,extended=ex)

        insidePoints = insidePoints
        print('time to extend arrays', time()-t1)

        print('Total time', time()-t0)

        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsCoords = surfPtsBB
        self.surfacePointsNormals = surfacePointsNormals
        print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
            len(self.surfacePoints), len(self.insidePoints),
            nbGridPoints, len(histoVol.grid.masterGridPositions)))

        self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                      self.insidePoints,areas=vSurfaceArea)
        bhtreelib.freeBHtree(bht)
        return self.insidePoints, self.surfacePoints

    def extendGridArrays(self,nbGridPoints,srfPts,surfPtsBBNorms,histoVol,extended=True):
        if extended  :      
            length = len(srfPts)
            pointArrayRaw = numpy.zeros( (nbGridPoints + length, 3), 'f')
            pointArrayRaw[:nbGridPoints] = histoVol.grid.masterGridPositions
            pointArrayRaw[nbGridPoints:] = srfPts
            self.surfacePointscoords = srfPts
            histoVol.grid.nbSurfacePoints += length
            histoVol.grid.masterGridPositions = pointArrayRaw
            histoVol.grid.distToClosestSurf.extend( [histoVol.grid.diag]*length )
            histoVol.grid.gridPtId=numpy.append(numpy.array(histoVol.grid.gridPtId), [self.number]*length ,axis=0)#surface point ID
            
            surfacePoints = list(range(nbGridPoints, nbGridPoints+length))
            histoVol.grid.freePoints.extend(surfacePoints)
    
            surfacePointsNormals = {}
            for i, n in enumerate(surfPtsBBNorms):
                surfacePointsNormals[nbGridPoints + i] = n
        else :
            length = len(srfPts)
            pointArrayRaw = histoVol.grid.masterGridPositions
            self.surfacePointscoords = srfPts
            histoVol.grid.nbSurfacePoints += length
            surfacePoints = list(range(nbGridPoints-length, nbGridPoints))
            surfacePointsNormals = {}
            for i, n in enumerate(surfPtsBBNorms):
                surfacePointsNormals[nbGridPoints-length + i] = n            
        return surfacePoints,surfacePointsNormals
    
    def getSurfaceBB(self,srfPts,histoVol):
        surfPtsBB = []
        surfPtsBBNorms  = []
        mini, maxi = histoVol.fillBB
        mx, my, mz = mini
        Mx, My, Mz = maxi
        ogNorms = self.ogsurfacePointsNormals
        for i,p in enumerate(srfPts):
            x,y,z = p
            if (x>=mx and x<=Mx and y>=my and y<=My and z>=mz and z<=Mz):
                surfPtsBB.append(p)
                surfPtsBBNorms.append(ogNorms[i])        
        if self.highresVertices is not None :
            srfPts = self.highresVertices   
            surfPtsBB = []     
            for i,p in enumerate(srfPts):
                x,y,z = p
                if (x>=mx and x<=Mx and y>=my and y<=My and z>=mz and z<=Mz):
                    surfPtsBB.append(p)
        print('surf points going from to', len(srfPts), len(surfPtsBB))
        srfPts = surfPtsBB
        return surfPtsBB,surfPtsBBNorms

    def BuildGrid_break(self, histoVol):
        # create surface points
        t0 = t1 = time()
        self.createSurfacePoints(maxl=histoVol.grid.gridSpacing)
        print("Creating surface points and preparing to sum the surface area, TODO- limit to selection box")
        # Graham Sum the SurfaceArea for each polyhedron
        vertices = self.vertices  #NEED to make these limited to selection box, not whole organelle
        faces = self.faces #         Should be able to use self.ogsurfacePoints and collect faces too from above
        normalList2,areas = self.getFaceNormals(vertices, faces,fillBB=histoVol.fillBB)
        vSurfaceArea = sum(areas)
        #for gnum in range(len(normalList2)):
        #    vSurfaceArea = vSurfaceArea + areas[gnum]
        print('Graham says Surface Area is %d' %(vSurfaceArea))
        print('Graham says the last triangle area is is %d' %(areas[-1]))
        #print '%d surface points %.2f unitVol'%(len(surfacePoints), unitVol)
        
        # build a BHTree for the vertices
        
        print('time to create surface points', time()-t1, len(self.ogsurfacePoints))
        
        distances = histoVol.grid.distToClosestSurf
        idarray = histoVol.grid.gridPtId
        diag = histoVol.grid.diag

        t1 = time()

        #build BHTree for off grid surface points
        from bhtree import bhtreelib
        srfPts = self.ogsurfacePoints
        bht = self.OGsrfPtsBht = bhtreelib.BHtree( srfPts, None, 10)

        number = self.number
        ogNormals = self.ogsurfacePointsNormals
        insidePoints = []
        #self.vnormals = ogNormals = normalList2
        # find closest off grid surface point for each grid point 
        #FIXME sould be diag of organelle BB inside fillBB
        grdPos = histoVol.grid.masterGridPositions
        returnNullIfFail = 0
        closest = bht.closestPointsArray(grdPos, diag, returnNullIfFail)
#        def distanceLoop(ptInd,distances,grdPos,closest,srfPts,ogNormals,idarray,insidePoints,number):
#            # find closest OGsurfacepoint
#            gx, gy, gz = grdPos[ptInd]
#            sptInd = closest[ptInd]
#            if closest[ptInd]==-1:
#                pdb.set_trace()
#            sx, sy, sz = srfPts[sptInd]
#
#            # update distance field
#            d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
#                      (gz-sz)*(gz-sz))
#            if distances[ptInd]>d: distances[ptInd] = d
#
#            # check if ptInd in inside
#            nx, ny, nz = ogNormals[sptInd]
#            # check on what side of the surface point the grid point is
#            vx,vy,vz = (gx-sx, gy-sy, gz-sz)
#            dot = vx*nx + vy*ny + vz*nz
#            if dot < 0: # inside
#                idarray[ptInd] = -number
#                insidePoints.append(ptInd)
            
        
        #[distanceLoop(x,distances,grdPos,closest,srfPts,ogNormals,idarray,insidePoints,number) for x in xrange(len(grdPos))]
        for ptInd in range(len(grdPos)):

            # find closest OGsurfacepoint
            gx, gy, gz = grdPos[ptInd]
            sptInd = closest[ptInd]
            if closest[ptInd]==-1:
                pdb.set_trace()
            sx, sy, sz = srfPts[sptInd]

            # update distance field
            #measure distance between the grid Point and the surface point
            d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
                      (gz-sz)*(gz-sz))
            if distances[ptInd] > d : 
                distances[ptInd] = d

            # check if ptInd in inside, and look at the normal at this points
            nx, ny, nz = ogNormals[sptInd]
            # check on what side of the surface point the grid point is
            vx,vy,vz = (gx-sx, gy-sy, gz-sz)
            dot = vx*nx + vy*ny + vz*nz
            if dot < 0: # inside
                idarray[ptInd] = -number
                insidePoints.append(ptInd)

        print('time to update distance field and idarray', time()-t1)

        t1 = time()
        nbGridPoints = len(histoVol.grid.masterGridPositions)

        surfPtsBB = []
        surfPtsBBNorms  = []
        mini, maxi = histoVol.fillBB
        mx, my, mz = mini
        Mx, My, Mz = maxi
        ogNorms = self.ogsurfacePointsNormals
        for i,p in enumerate(srfPts):
            x,y,z = p
            if (x>=mx and x<=Mx and y>=my and y<=My and z>=mz and z<=Mz):
                surfPtsBB.append(p)
                surfPtsBBNorms.append(ogNorms[i])

        print('surf points going from to', len(srfPts), len(surfPtsBB))
        srfPts = surfPtsBB
        length = len(srfPts)

        pointArrayRaw = numpy.zeros( (nbGridPoints + length, 3), 'f')
        pointArrayRaw[:nbGridPoints] = histoVol.grid.masterGridPositions
        pointArrayRaw[nbGridPoints:] = srfPts
        self.surfacePointsCoords = srfPts #surfacePointscoords ?
        histoVol.grid.nbSurfacePoints += length
        histoVol.grid.masterGridPositions = pointArrayRaw
        histoVol.grid.distToClosestSurf.extend( [histoVol.grid.diag]*length )
        
        histoVol.grid.gridPtId.extend( [number]*length )
        surfacePoints = list(range(nbGridPoints, nbGridPoints+length))
        histoVol.grid.freePoints.extend(surfacePoints)

        surfacePointsNormals = {}
        for i, n in enumerate(surfPtsBBNorms):
            surfacePointsNormals[nbGridPoints + i] = n

        insidePoints = insidePoints
        print('time to extend arrays', time()-t1)

        print('Total time', time()-t0)

        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsCoords = surfPtsBB
        self.surfacePointsNormals = surfacePointsNormals
        print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
            len(self.surfacePoints), len(self.insidePoints),
            nbGridPoints, len(histoVol.grid.masterGridPositions)))

        self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                      self.insidePoints,areas=vSurfaceArea)
        return self.insidePoints, self.surfacePoints

    
    def BuildGridEnviroOnly(self, histoVol, location=None):
        # create surface points
        t0 = t1 = time()
        self.createSurfacePoints(maxl=histoVol.grid.gridSpacing)
        
        # Graham Sum the SurfaceArea for each polyhedron
        vertices = self.vertices  #NEED to make these limited to selection box, not whole organelle
        faces = self.faces #         Should be able to use self.ogsurfacePoints and collect faces too from above
        normalList2,areas = self.getFaceNormals(vertices, faces,fillBB=histoVol.fillBB)
        vSurfaceArea = sum(areas)
        #for gnum in range(len(normalList2)):
        #    vSurfaceArea = vSurfaceArea + areas[gnum]
        #print 'Graham says Surface Area is %d' %(vSurfaceArea)
        #print 'Graham says the last triangle area is is %d' %(areas[-1])
        #print '%d surface points %.2f unitVol'%(len(surfacePoints), unitVol)
        
        # build a BHTree for the vertices
        
        print('time to create surface points', time()-t1, len(self.ogsurfacePoints))

        
        distances = histoVol.grid.distToClosestSurf
        idarray = histoVol.grid.gridPtId
#        diag = histoVol.grid.diag

        t1 = time()

        #build BHTree for off grid surface points
#        from bhtree import bhtreelib
        srfPts = self.ogsurfacePoints
#        bht = self.OGsrfPtsBht = bhtreelib.BHtree( srfPts, None, 10)

        number = self.number
        ogNormals = self.ogsurfacePointsNormals
        insidePoints = []

        # find closest off grid surface point for each grid point 
        #FIXME sould be diag of organelle BB inside fillBB
        grdPos = histoVol.grid.masterGridPositions
#        returnNullIfFail = 0
        closest = []#bht.closestPointsArray(grdPos, diag, returnNullIfFail)
        def distanceLoop(ptInd,distances,grdPos,closest,srfPts,ogNormals,idarray,insidePoints,number):
            # find closest OGsurfacepoint
            gx, gy, gz = grdPos[ptInd]
            sptInd = closest[ptInd]
            if closest[ptInd]==-1:
                pdb.set_trace()
            sx, sy, sz = srfPts[sptInd]

            # update distance field
            d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
                      (gz-sz)*(gz-sz))
            if distances[ptInd]>d: distances[ptInd] = d

            # check if ptInd in inside
            nx, ny, nz = ogNormals[sptInd]
            # check on what side of the surface point the grid point is
            vx,vy,vz = (gx-sx, gy-sy, gz-sz)
            dot = vx*nx + vy*ny + vz*nz
            if dot < 0: # inside
                idarray[ptInd] = -number
                insidePoints.append(ptInd)
            
        if location is None :
            re=[distanceLoop(x, distances, grdPos, closest, srfPts,
                              ogNormals, idarray, insidePoints,
                               number) for x in range(len(grdPos))]
        else :
            insidePoints = list(range(len(grdPos)))
            for ptInd in range(len(grdPos)):
                distances[ptInd] = 99999.
                idarray[ptInd] = location

#        for ptInd in xrange(len(grdPos)):

            # find closest OGsurfacepoint
#            gx, gy, gz = grdPos[ptInd]
#            sptInd = closest[ptInd]
#            if closest[ptInd]==-1:
#                pdb.set_trace()
#            sx, sy, sz = srfPts[sptInd]

            # update distance field
#            d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
#                      (gz-sz)*(gz-sz))
#            if distances[ptInd]>d: distances[ptInd] = d

            # check if ptInd in inside
#            nx, ny, nz = ogNormals[sptInd]
            # check on what side of the surface point the grid point is
#            vx,vy,vz = (gx-sx, gy-sy, gz-sz)
#            dot = vx*nx + vy*ny + vz*nz
#            if dot < 0: # inside
#                idarray[ptInd] = -number
#                insidePoints.append(ptInd)

        print('time to update distance field and idarray', time()-t1)

        t1 = time()
        nbGridPoints = len(histoVol.grid.masterGridPositions)

        surfPtsBB = []
        surfPtsBBNorms  = []
        mini, maxi = histoVol.fillBB
        mx, my, mz = mini
        Mx, My, Mz = maxi
        ogNorms = self.ogsurfacePointsNormals
        for i,p in enumerate(srfPts):
            x,y,z = p
            if (x>=mx and x<=Mx and y>=my and y<=My and z>=mz and z<=Mz):
                surfPtsBB.append(p)
                surfPtsBBNorms.append(ogNorms[i])

        print('surf points going from to', len(srfPts), len(surfPtsBB))
        srfPts = surfPtsBB
        length = len(srfPts)

        pointArrayRaw = numpy.zeros( (nbGridPoints + length, 3), 'f')
        pointArrayRaw[:nbGridPoints] = histoVol.grid.masterGridPositions
        pointArrayRaw[nbGridPoints:] = srfPts
        self.surfacePointsCoords = srfPts #surfacePointscoords ?
        histoVol.grid.nbSurfacePoints += length
        histoVol.grid.masterGridPositions = pointArrayRaw
        histoVol.grid.distToClosestSurf.extend( [histoVol.grid.diag]*length )
        
        histoVol.grid.gridPtId.extend( [number]*length )
        surfacePoints = list(range(nbGridPoints, nbGridPoints+length))
        histoVol.grid.freePoints.extend(surfacePoints)

        surfacePointsNormals = {}
        for i, n in enumerate(surfPtsBBNorms):
            surfacePointsNormals[nbGridPoints + i] = n

        insidePoints = insidePoints
        print('time to extend arrays', time()-t1)

        print('Total time', time()-t0)

        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsCoords = surfPtsBB
        self.surfacePointsNormals = surfacePointsNormals
        print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
            len(self.surfacePoints), len(self.insidePoints),
            nbGridPoints, len(histoVol.grid.masterGridPositions)))

        self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                      self.insidePoints,areas=vSurfaceArea)
        return self.insidePoints, self.surfacePoints

    def BuildGrid_OrthogonalBox(self, histoVol):
        t0 = time()
        self.ogsurfacePoints = None
        self.ogsurfacePointsNormals = None
#        vertices = None
#        faces = None
        normalList2,areas = None # in future, get area of box from corner points
        vSurfaceArea = None#sum(areas)
#        bbox = self.bb
#        xmin = bbox[0][0]; ymin = bbox[0][1]; zmin = bbox[0][2]
#        xmax = bbox[1][0]; ymax = bbox[1][1]; zmax = bbox[1][2]
#        sizex = self.getSizeXYZ()
#        gboundingBox = histoVol.grid.boundingBox
#        gspacing = histoVol.grid.gridSpacing
#        
#        from UTpackages.UTsdf import utsdf
#        #can be 16,32,64,128,256,512,1024
#        #        if spacing not in [16,32,64,128,256,512,1024]:
#        #            spacing = self.find_nearest(numpy.array([16,32,64,128,256,512,1024]),spacing)
#        # compute SDF
#        dim=16
#        dim1=dim+1
#        print ("ok2 dim ",dim)
#        size = dim1*dim1*dim1
#        from UTpackages.UTsdf import utsdf
#        verts = N.array(self.vertices,dtype='f')
#        
#        tris = N.array(self.faces,dtype="int")
#        utsdf.setParameters(dim,0,1,[0,0,0,0,0,0])#size, bool isNormalFlip, bool insideZero,bufferArr
#        surfacePoints = srfPts = self.vertices
#        print ("ok grid points")
#        datap = utsdf.computeSDF(N.ascontiguousarray(verts, dtype=N.float32),N.ascontiguousarray(tris, dtype=N.int32))
#        print ("ok computeSDF")
#        data = utsdf.createNumArr(datap,size)
#        volarr = data[:]
#        volarr.shape = (dim1, dim1, dim1)
#        volarr = numpy.ascontiguousarray(numpy.transpose(volarr), 'f')
#        
#        # get grid points distances to organelle surface
#        from Volume.Operators.trilinterp import trilinterp
#        invstep =(1./(sizex[0]/dim), 1./(sizex[1]/dim), 1./(sizex[2]/dim))
#        origin = self.bb[0]
#        distFromSurf = trilinterp(histoVol.grid.masterGridPositions,
#                                  volarr, invstep, origin)
#        
#        
#        # save SDF
#        #        self.sdfData = volarr
#        #        self.sdfOrigin = origin
#        #        self.sdfGridSpacing = (gSizeX, gSizeY, gSizeZ)
#        #        self.sdfDims = (dimx, dimy, dimz)
#        
#        ## update histoVol.distToClosestSurf
#        distance = histoVol.grid.distToClosestSurf
#        for i,d in enumerate(distFromSurf):
#            if distance[i] > d:
#                distance[i] = d
        
        # loop over fill box grid points and build the idarray
        # identify inside and surface points and update the distance field
        number = self.number
        insidePoints = []
        surfacePoints = []
        allNormals = {}
        idarray = histoVol.grid.gridPtId
        #surfaceCutOff = histoVol.gridSpacing*.5
        #print 'BBBBBBBBBBBBBB', surfaceCutOff, min(distFromSurf), max(distFromSurf)
        #print 'We should get', len(filter(lambda x:fabs(x)<surfaceCutOff, distance))
    
        #import pdb
        #pdb.set_trace()
        indice = numpy.nonzero(numpy.less(distance,0.0))
        pointinside = numpy.take(histoVol.grid.masterGridPositions,indice,0)[0]
        #        print (len(indice[0]),indice,len(pointinside))
        if len(indice) == 1  and len(indice[0]) != 1:
            indice = indice[0]
        if len(pointinside) == 1  and len(pointinside[0]) != 1:
            pointinside = pointinside[0]
        histoVol.grid.gridPtId[indice] = -self.number
        print ("sdf pointID N ",self.number,len(histoVol.grid.gridPtId[indice]),histoVol.grid.gridPtId[indice])
        t1 = time()
        nbGridPoints = len(histoVol.grid.masterGridPositions)

        surfPtsBB,surfPtsBBNorms = self.getSurfaceBB(srfPts,histoVol)
        srfPts = surfPtsBB
        surfacePoints,surfacePointsNormals  = self.extendGridArrays(nbGridPoints,
                                                                    srfPts,surfPtsBBNorms,histoVol)
        
        print (len(histoVol.grid.gridPtId[indice]),histoVol.grid.gridPtId[indice])
        insidePoints = pointinside
        print('time to extend arrays', time()-t1)
        
        print('Total time', time()-t0)
        
        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsCoords = surfPtsBB
        self.surfacePointsNormals = surfacePointsNormals
        print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
                                                                                len(self.surfacePoints), len(self.insidePoints),
                                                                                nbGridPoints, len(histoVol.grid.masterGridPositions)))
        self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                      self.insidePoints,areas=vSurfaceArea)    
        return insidePoints, surfacePoints



    def BuildGrid_utsdf(self, histoVol):
        t0 = time()
        self.ogsurfacePoints = self.vertices[:]
        self.ogsurfacePointsNormals = self.vnormals[:]
        vertices = self.vertices
        faces = self.faces
        normalList2,areas = self.getFaceNormals(vertices, faces,fillBB=histoVol.fillBB)
        vSurfaceArea = sum(areas)
#        labels = numpy.ones(len(faces), 'i')
        
        # FIXME .. dimensions on SDF should addapt to organelle size
        bbox = self.bb
        xmin = bbox[0][0]; ymin = bbox[0][1]; zmin = bbox[0][2]
        xmax = bbox[1][0]; ymax = bbox[1][1]; zmax = bbox[1][2]
        sizex = self.getSizeXYZ()
        gboundingBox = histoVol.grid.boundingBox
        gspacing = histoVol.grid.gridSpacing
        
        from UTpackages.UTsdf import utsdf
        #can be 16,32,64,128,256,512,1024
#        if spacing not in [16,32,64,128,256,512,1024]:
#            spacing = self.find_nearest(numpy.array([16,32,64,128,256,512,1024]),spacing)
        # compute SDF
        dim=16
        dim1=dim+1        
        print ("ok2 dim ",dim)
        size = dim1*dim1*dim1
        from UTpackages.UTsdf import utsdf        
        verts = N.array(self.vertices,dtype='f')
        
        tris = N.array(self.faces,dtype="int")
        utsdf.setParameters(dim,0,1,[0,0,0,0,0,0])#size, bool isNormalFlip, bool insideZero,bufferArr
        surfacePoints = srfPts = self.vertices
        print ("ok grid points")
        datap = utsdf.computeSDF(N.ascontiguousarray(verts, dtype=N.float32),N.ascontiguousarray(tris, dtype=N.int32))
        print ("ok computeSDF")
        data = utsdf.createNumArr(datap,size)
        volarr = data[:]
        volarr.shape = (dim1, dim1, dim1)
        volarr = numpy.ascontiguousarray(numpy.transpose(volarr), 'f')
        
        # get grid points distances to organelle surface
        from Volume.Operators.trilinterp import trilinterp
        invstep =(1./(sizex[0]/dim), 1./(sizex[1]/dim), 1./(sizex[2]/dim))
        origin = self.bb[0]
        distFromSurf = trilinterp(histoVol.grid.masterGridPositions,
                                  volarr, invstep, origin)

        
        # save SDF
#        self.sdfData = volarr
#        self.sdfOrigin = origin
#        self.sdfGridSpacing = (gSizeX, gSizeY, gSizeZ)
#        self.sdfDims = (dimx, dimy, dimz)

        ## update histoVol.distToClosestSurf
        distance = histoVol.grid.distToClosestSurf
        for i,d in enumerate(distFromSurf):
            if distance[i] > d:
                distance[i] = d
        
        # loop over fill box grid points and build the idarray
        # identify inside and surface points and update the distance field
        number = self.number
        insidePoints = []
        surfacePoints = []
        allNormals = {}
        idarray = histoVol.grid.gridPtId
        #surfaceCutOff = histoVol.gridSpacing*.5
        #print 'BBBBBBBBBBBBBB', surfaceCutOff, min(distFromSurf), max(distFromSurf)
        #print 'We should get', len(filter(lambda x:fabs(x)<surfaceCutOff, distance))

        #import pdb
        #pdb.set_trace()
        indice = numpy.nonzero(numpy.less(distance,0.0))
        pointinside = numpy.take(histoVol.grid.masterGridPositions,indice,0)[0]
#        print (len(indice[0]),indice,len(pointinside))
        if len(indice) == 1  and len(indice[0]) != 1:
            indice = indice[0]
        if len(pointinside) == 1  and len(pointinside[0]) != 1:
            pointinside = pointinside[0]
        histoVol.grid.gridPtId[indice] = -self.number
        print ("sdf pointID N ",self.number,len(histoVol.grid.gridPtId[indice]),histoVol.grid.gridPtId[indice])
        t1 = time()
        nbGridPoints = len(histoVol.grid.masterGridPositions)
        
        surfPtsBB,surfPtsBBNorms = self.getSurfaceBB(srfPts,histoVol)
        srfPts = surfPtsBB
        surfacePoints,surfacePointsNormals  = self.extendGridArrays(nbGridPoints,
                                            srfPts,surfPtsBBNorms,histoVol)

        print (len(histoVol.grid.gridPtId[indice]),histoVol.grid.gridPtId[indice])                
        insidePoints = pointinside
        print('time to extend arrays', time()-t1)

        print('Total time', time()-t0)

        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsCoords = surfPtsBB
        self.surfacePointsNormals = surfacePointsNormals
        print('%s surface pts, %d inside pts, %d tot grid pts, %d master grid'%(
            len(self.surfacePoints), len(self.insidePoints),
            nbGridPoints, len(histoVol.grid.masterGridPositions)))
        self.computeVolumeAndSetNbMol(histoVol, self.surfacePoints,
                                      self.insidePoints,areas=vSurfaceArea)    
        return insidePoints, surfacePoints
        
    def get_bbox(self, vert_list, BB_SCALE = 0.0):
        from multisdf import multisdf
        multisdf.cvar.BB_SCALE = BB_SCALE
        HUGE = 999999

        bbox = []
        x_min = HUGE; x_max = -HUGE
        y_min = HUGE; y_max = -HUGE
        z_min = HUGE; z_max = -HUGE
        for i in range(len(vert_list)):
            p = vert_list[i]
            #check x-span
            if p[0] < x_min: 
                x_min = p[0]
            if p[0] > x_max: 
                x_max = p[0]
            #check y-span
            if p[1] < y_min: 
                y_min = p[1]
            if p[1] > y_max: 
                y_max = p[1]
            #check z-span
            if p[2] < z_min: 
                z_min = p[2]
            if p[2] > z_max: 
                z_max = p[2]

        bbox.append(x_min - BB_SCALE*(x_max-x_min))
        bbox.append(y_min - BB_SCALE*(y_max-y_min))
        bbox.append(z_min - BB_SCALE*(z_max-z_min))

        bbox.append(x_max + BB_SCALE*(x_max-x_min))
        bbox.append(y_max + BB_SCALE*(y_max-y_min))
        bbox.append(z_max + BB_SCALE*(z_max-z_min))
        return bbox

        
    def BuildGrid_multisdf(self, histoVol):
#        t1 = time()
        vertices = self.vertices
        faces = self.faces
        labels = numpy.ones(len(faces), 'i')
        
        # FIXME .. dimensions on SDF should addapt to organelle size
        bbox = self.get_bbox(vertices)
        xmin = bbox[0]; ymin = bbox[1]; zmin = bbox[2]
        xmax = bbox[3]; ymax = bbox[4]; zmax = bbox[5]

        # compute SDF
        from multisdf import multisdf
        gridSpacing = 30.
        dimx = int( (xmax-xmin)/gridSpacing ) + 1
        dimy = int( (ymax-ymin)/gridSpacing ) + 1
        dimz = int( (zmax-zmin)/gridSpacing ) + 1

        gSizeX = (xmax-xmin)/(dimx-1) 
        gSizeY = (ymax-ymin)/(dimy-1)
        gSizeZ = (zmax-zmin)/(dimz-1)

        print('SDF grid size', dimx,dimy,dimz,gSizeX, gSizeY, gSizeZ)

        mind = -1000.
        maxd = 1000.
        datap = multisdf.computeSDF(vertices, faces, labels, dimx, dimy, dimz,
                                    maxd, mind)
        grid_size  = dimx*dimy*dimz
        volarr = multisdf.createNumArr(datap, grid_size)
        volarr.shape = (dimz, dimy, dimx)
        volarr = numpy.ascontiguousarray(numpy.transpose(volarr), 'f')

        # get grid points distances to organelle surface
        from Volume.Operators.trilinterp import trilinterp
        invstep =(1./gridSpacing, 1./gridSpacing, 1./gridSpacing)
        origin = (xmin, ymin, zmin)
        distFromSurf = trilinterp(histoVol.masterGridPositions,
                                  volarr, invstep, origin)

        # save SDF
        self.sdfData = volarr
        self.sdfOrigin = origin
        self.sdfGridSpacing = (gSizeX, gSizeY, gSizeZ)
        self.sdfDims = (dimx, dimy, dimz)

        ## update histoVol.distToClosestSurf
        distance = histoVol.distToClosestSurf
        for i,d in enumerate(distFromSurf):
            if distance[i] > d:
                distance[i] = d
        
        # loop over fill box grid points and build the idarray
        # identify inside and surface points and update the distance field
        number = self.number
        insidePoints = []
        surfacePoints = []
        allNormals = {}
        idarray = histoVol.gridPtId
        #surfaceCutOff = histoVol.gridSpacing*.5
        #print 'BBBBBBBBBBBBBB', surfaceCutOff, min(distFromSurf), max(distFromSurf)
        #print 'We should get', len(filter(lambda x:fabs(x)<surfaceCutOff, distance))

        #import pdb
        #pdb.set_trace()
        
        for i, d in enumerate(distance):

            # identify surface and interior points
            # there is a problem with SDF putting large negative values
            # for inside points. For now we pick all negative != mind as
            # surface points
            if d>0:
                continue
            elif d<mind:
                surfacePoints.append(i)
                idarray[i] = number
                allNormals[i] = (1,0,0)
            else:
                insidePoints.append(i)
                idarray[i] = -number

        self.computeVolumeAndSetNbMol(histoVol, surfacePoints, insidePoints)

        self.insidePoints = insidePoints
        self.surfacePoints = surfacePoints
        self.surfacePointsNormals = allNormals
        print('AAAAAAAAAAAA', len(surfacePoints))
        
        return insidePoints, surfacePoints


    def getSurfacePoint( self, p1, p2, w1, w2):
        # compute point between p1 and p2 with weight w1 and w2
        x1,y1,z1 = p1
        x2,y2,z2 = p2
#        totalWeight = w1+w2
        ratio = w1/(w1+w2)
        vec = (x2-x1, y2-y1, z2-z1)
        return x1 + ratio*vec[0], y1 + ratio*vec[1], z1 + ratio*vec[2]

    def estimateVolume(self,unitVol=None,hBB=None):
        """ v: A pointer to the array of vertices
        // i: A pointer to the array of indices
        // n: The number of indices (multiple of 3)
        // This function uses Gauss's Theorem to calculate the volume of a body
        // enclosed by a set of triangles. The triangle set must form a closed
        // surface in R3 and be outward facing. Outward facing triangles index
        // their vertices in a counterclockwise order where the x-axis points
        // left, the y-axis point up and the z-axis points toward you (rhs).
        // from http://www.gamedev.net/page/resources/_/technical/game-programming/area-and-volume-calculations-r2247
        """
        if self.interiorVolume is None or self.interiorVolume == 0.0:
            v = self.vertices
            i = self.faces
            n = len(self.faces)
            volume = 0.0
            for j in range(n):#(j = 0; j < n; j+=3)
                v1 = v[i[j][0]]
                v2 = v[i[j][1]]
                v3 = v[i[j][2]]    
                volume += ((v2[1]-v1[1])*(v3[2]-v1[2])-(v2[2]-v1[2])*(v3[1]-v1[1]))*(v1[0]+v2[0]+v3[0])    
            self.interiorVolume =  volume / 6.0
        if self.surfaceVolume is None or self.surfaceVolume == 0.0:
            if hBB is not None :
                normalList2,areas = self.getFaceNormals(self.vertices,self.faces,fillBB=hBB)
                self.surfaceVolume =  sum(areas)            
            elif unitVol != None :
                self.surfaceVolume = len(self.vertices) * unitVol
        


    def computeVolumeAndSetNbMol(self, histoVol, surfacePoints, insidePoints,
                                 areas=None):
        # compute volume of surface and interior
        # set 'nbMol' in each ingredient of both recipes
        unitVol = histoVol.grid.gridSpacing**3
        if surfacePoints !=None:
            print('%d surface points %.2f unitVol'%(len(surfacePoints), unitVol))
        #FIXME .. should be surface per surface point instead of unitVol
            self.surfaceVolume = len(surfacePoints)*unitVol 
        area = False
        if areas is not None :
            self.surfaceVolume = areas
            area = True
        self.interiorVolume = len(insidePoints)*unitVol
        if self.surfaceVolume != None:
            print('%d surface volume %.2f interior volume'%(self.surfaceVolume, self.interiorVolume))
        print('%.2f interior volume'%(self.interiorVolume))


        # compute number of molecules and save in recipes
        rs = self.surfaceRecipe
        if rs:
            volume = self.surfaceVolume
            rs.setCount(volume,area=area)

        ri = self.innerRecipe
        if ri:
            volume = self.interiorVolume
            a = ri.setCount(volume)
            print ("number of molecules for Special Cube = ", a, ", because interiorVolume = ", volume)

    def getFacesNfromV(self,vindice,ext=0):
        f=[]        
        for i,af in enumerate(self.faces) :
            if vindice in af :
                if ext :
                    for vi in af :
                        if vi != vindice :
                            ff=self.getFacesNfromV(vi)
                            f.extend(ff)
                else :
                    f.append(self.fnormals[i])
        return f

    def getVNfromF(self,i):
        self.normals
        fi=[]        
        for k,af in enumerate(self.faces) :
            if i in af :
                for j in af :
                    if j not in fi :
                        fi.append(j)
        n=[]
        for ind in fi:
            n.append(self.normals[ind])
        return n

    def create3DPointLookup(self, nbGridPoints,gridSpacing,dim,boundingBox=None):
        #pFinalNumberOfPoints, pGridSpacing, pArrayOfTwoTotalCorners):
        # Fill the orthogonal bounding box described by two global corners
        # with an array of points spaces pGridSpacing apart.
        if boundingBox is None :
            boundingBox= self.bb
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]

        nx,ny,nz = nbGridPoints
        pointArrayRaw = numpy.zeros( (nx*ny*nz, 3), 'f')
        ijkPtIndice = numpy.zeros( (nx*ny*nz, 3), 'i')
        space = gridSpacing
        size = self.getSizeXYZ()
        # Vector for lower left broken into real of only the z coord.
        i = 0
        for zi in range(nz):
            for yi in range(ny):
                for xi in range(nx):
                    pointArrayRaw[i] = (xl+xi*(size[0]/dim), yl+yi*(size[1]/dim), zl+zi*(size[2]/dim))
                    ijkPtIndice[i] = (xi,yi,zi)
                    i+=1
        return ijkPtIndice,pointArrayRaw

    def find_nearest(self,array,value):
        idx=(numpy.abs(array-value)).argmin()
        return array[idx]


    def getSurfaceInnerPoints_sdf(self,boundingBox,spacing,display = True,useFix=False):
        print ("beforea import" )        
        print ("ok1" )
        from UTpackages.UTsdf import utsdf
        #can be 16,32,64,128,256,512,1024
        if spacing not in [16,32,64,128,256,512,1024]:
            spacing = self.find_nearest(numpy.array([16,32,64,128,256,512,1024]),spacing)
        dim = spacing
        dim1=dim+1
        
        print ("ok2 ",dim1,dim)
        size = dim1*dim1*dim1
         #can be 16,32,64,128,256,512,1024
        verts = N.array(self.vertices,dtype='f')
        tris = N.array(self.faces,dtype="int")
        utsdf.setParameters(int(dim),0,1,[0,0,0,0,0,0])#size, bool isNormalFlip, bool insideZero,bufferArr
        print ("ok3")

        #spacing = length / 64
        sizes=self.getSizeXYZ()
        L = max(sizes)        
        spacing = L/dim# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
#        helper.progressBar(label="BuildGRid")        
#        grid.gridVolume,grid.nbGridPoints = grid.computeGridNumberOfPoint(boundingBox,spacing)
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        
        print (len(verts),len(tris),type(verts),type(tris),verts[0],tris[0])
        surfacePoints = srfPts = self.vertices
        print ("ok grid points")
#        verts = N.ascontiguousarray(verts, dtype='f')
#        tris = N.ascontiguousarray(tris, dtype=N.int32)
#        verts = N.ascontiguousarray(verts, dtype='f')
#        tris = N.ascontiguousarray(tris, dtype=N.int32)

        datap = utsdf.computeSDF(verts,tris)
        #datap = utsdf.computeSDF(verts,tris)
        print ("ok computeSDF")
        data = utsdf.createNumArr(datap,size)

        nbGridPoints = [dim1,dim1,dim1]
        ijkPtIndice,pointArrayRaw = self.create3DPointLookup(nbGridPoints,spacing,dim)
        print ("ok grid",len(data),size)
        nbPoints = len(pointArrayRaw)
        print ("n pts",nbPoints)
        gridPtId = [0]*nbPoints
        grdPos = pointArrayRaw        
        indice = numpy.nonzero(numpy.less(data,0.0))
        pointinside = numpy.take(grdPos,indice,0)
        #need to update the surface. need to create a aligned grid
        return pointinside[0],self.vertices

    def getSurfaceInnerPoints_jordan(self,boundingBox,spacing,display = True,useFix=False,ray=1):
        from AutoFill.HistoVol import Grid        
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        helper.progressBar(label="BuildGRid")        
        grid.gridVolume,grid.nbGridPoints = grid.computeGridNumberOfPoint(boundingBox,spacing)
        grid.create3DPointLookup()
        nbPoints = grid.gridVolume
        grid.gridPtId = [0]*nbPoints
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
        grid.distToClosestSurf = [diag]*nbPoints        
        distances = grid.distToClosestSurf
        idarray = grid.gridPtId
        diag = grid.diag
        
        from bhtree import bhtreelib
        self.ogsurfacePoints = self.vertices[:]
        self.ogsurfacePointsNormals = self.vnormals[:]#helper.FixNormals(self.vertices,self.faces,self.vnormals,fn=self.fnormals)
        mat = helper.getTransformation(self.ref_obj)
        surfacePoints = srfPts = self.ogsurfacePoints
        self.OGsrfPtsBht = bht =  bhtreelib.BHtree(tuple(srfPts), None, 10)

        res = numpy.zeros(len(srfPts),'f')
        dist2 = numpy.zeros(len(srfPts),'f')
        number = self.number
        insidePoints = []
        grdPos = grid.masterGridPositions
        returnNullIfFail = 0
        t1=time()
        center = helper.getTranslation( self.ref_obj )
        helper.resetProgressBar()
        if display :
            cyl2 = helper.oneCylinder("ray",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0)
            if ray == 3 :
                cyl1 = helper.oneCylinder("ray2",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0)
                cyl3 = helper.oneCylinder("ray3",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0) 
                helper.changeObjColorMat(cyl1,(1.,1.,1.))
                helper.changeObjColorMat(cyl3,(1.,1.,1.))
        for ptInd in xrange(len(grdPos)):#len(grdPos)):
            inside = False
            t2=time()
            gx, gy, gz = grdPos[ptInd]
            if display :
                helper.updateOneCylinder("ray",grdPos[ptInd],grdPos[ptInd]+(numpy.array([1.1,0.,0.])*spacing*10.0),radius=10.0)
                helper.changeObjColorMat(cyl2,(1.,1.,1.))
                helper.update()
            intersect, count = helper.raycast(self.ref_obj, grdPos[ptInd], grdPos[ptInd]+[1.1,0.,0.], diag, count = True )
            r= ((count % 2) == 1)
            if ray == 3 :
                if display :
                    helper.updateOneCylinder("ray2",grdPos[ptInd],grdPos[ptInd]+(numpy.array([0.,0.0,1.1])*spacing*10.0),radius=10.0)
                    helper.changeObjColorMat(cyl1,(1.,1.,1.))
                    helper.update()
                intersect2, count2 = helper.raycast(self.ref_obj, grdPos[ptInd], grdPos[ptInd]+[0.,0.,1.1], diag, count = True )
                center = helper.rotatePoint(helper.ToVec(center),[0.,0.,0.],[1.0,0.0,0.0,math.radians(33.0)])
                if display :
                    helper.updateOneCylinder("ray3",grdPos[ptInd],grdPos[ptInd]+(numpy.array([0.,1.1,0.])*spacing*10.0),radius=10.0)
                    helper.changeObjColorMat(cyl3,(1.,1.,1.))
                    helper.update()
                intersect3, count3 = helper.raycast(self.ref_obj, grdPos[ptInd], grdPos[ptInd]+[0.,1.1,0.], diag, count = True )
                if r :
                   if (count2 % 2) == 1 and (count3 % 2) == 1 :
                       r=True
                   else : 
                       r=False
            if r : # odd inside
                inside = True
                if inside :
                    if display :
                        helper.changeObjColorMat(cyl2,(1.,0.,0.))
                        if ray == 3 :
                            helper.changeObjColorMat(cyl1,(1.,0.,0.))
                            helper.changeObjColorMat(cyl3,(1.,0.,0.))    
                    #idarray[ptInd] = -number
                    insidePoints.append(grdPos[ptInd]) 
            p=(ptInd/float(len(grdPos)))*100.0
            helper.progressBar(progress=int(p),label=str(ptInd)+"/"+str(len(grdPos))+" inside "+str(inside))
        print('total time', time()-t1)
        return insidePoints, surfacePoints

         
    def getSurfaceInnerPoints_sdf_interpolate(self,boundingBox,spacing,display = True,useFix=False):
        from AutoFill.HistoVol import Grid        
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        helper.progressBar(label="BuildGRid")        
        grid.gridVolume,grid.nbGridPoints = grid.computeGridNumberOfPoint(boundingBox,spacing)
        grid.create3DPointLookup()
        nbPoints = grid.gridVolume
        grid.gridPtId = [0]*nbPoints
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
        grid.distToClosestSurf = [diag]*nbPoints        
        distances = grid.distToClosestSurf
        idarray = grid.gridPtId
        diag = grid.diag
        dim=16
        dim1=dim+1        
        print ("ok2")
        size = dim1*dim1*dim1
        from UTpackages.UTsdf import utsdf        
        verts = N.array(self.vertices,dtype='f')
        tris = N.array(self.faces,dtype="int")
        utsdf.setParameters(dim,0,1,[0,0,0,0,0,0])#size, bool isNormalFlip, bool insideZero,bufferArr
        surfacePoints = srfPts = self.vertices
        print ("ok grid points")
        #datap = utsdf.computeSDF(N.ascontiguousarray(verts, dtype=N.float32),N.ascontiguousarray(tris, dtype=N.int32))
        datap = utsdf.computeSDF(verts,tris) #noncontiguous?
        print ("ok computeSDF ",len(verts),len(tris))
        data = utsdf.createNumArr(datap,size)
        volarr = data[:]
        volarr.shape = (dim1, dim1, dim1)
        volarr = numpy.ascontiguousarray(numpy.transpose(volarr), 'f')
        
        # get grid points distances to organelle surface
        from Volume.Operators.trilinterp import trilinterp
        sizex = self.getSizeXYZ()
        invstep =(1./(sizex[0]/dim), 1./(sizex[0]/dim), 1./(sizex[0]/dim))
        origin = self.bb[0]
        distFromSurf = trilinterp(grid.masterGridPositions,
                                  volarr, invstep, origin)
        ## update histoVol.distToClosestSurf
        distance = grid.distToClosestSurf
        for i,d in enumerate(distFromSurf):
            if distance[i] > d:
                distance[i] = d
        
        number = self.number
        insidePoints = []
        surfacePoints = []
        allNormals = {}
#        idarray = histoVol.gridPtId
        indice = numpy.nonzero(numpy.less(distance,0.0))
        pointinside = numpy.take(grid.masterGridPositions,indice,0)
        #need to update the surface. need to create a aligned grid
        return pointinside[0],self.vertices

             
         
    def getSurfaceInnerPoints(self,boundingBox,spacing,display = True,useFix=False):
        from AutoFill.HistoVol import Grid        
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        helper.progressBar(label="BuildGRid")        
        grid.gridVolume,grid.nbGridPoints = grid.computeGridNumberOfPoint(boundingBox,spacing)
        grid.create3DPointLookup()
        nbPoints = grid.gridVolume
        grid.gridPtId = [0]*nbPoints
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
        grid.distToClosestSurf = [diag]*nbPoints        
        distances = grid.distToClosestSurf
        idarray = grid.gridPtId
        diag = grid.diag
        
        from bhtree import bhtreelib
        self.ogsurfacePoints = self.vertices[:]
        self.ogsurfacePointsNormals = self.vnormals[:]#helper.FixNormals(self.vertices,self.faces,self.vnormals,fn=self.fnormals)
        mat = helper.getTransformation(self.ref_obj)
            #c4dmat = poly.GetMg()
            #mat,imat = self.c4dMat2numpy(c4dmat)
        self.normals= helper.FixNormals(self.vertices,self.faces,self.vnormals,fn=self.fnormals)
        self.ogsurfacePointsNormals = helper.ApplyMatrix(numpy.array(self.normals),helper.ToMat(mat))
#        faces = self.faces[:]
#        self.createSurfacePoints(maxl=grid.gridSpacing/2.0)
        surfacePoints = srfPts = self.ogsurfacePoints
        print (len(self.ogsurfacePointsNormals),self.ogsurfacePointsNormals)
        self.OGsrfPtsBht = bht =  bhtreelib.BHtree(tuple(srfPts), None, 10)

        res = numpy.zeros(len(srfPts),'f')
        dist2 = numpy.zeros(len(srfPts),'f')

        number = self.number
        ogNormals = numpy.array(self.ogsurfacePointsNormals)
        insidePoints = []

        # find closest off grid surface point for each grid point 
        #FIXME sould be diag of organelle BB inside fillBB
        grdPos = grid.masterGridPositions
        returnNullIfFail = 0
        closest = bht.closestPointsArray(tuple(grdPos), diag, returnNullIfFail)#diag is  cutoff ? meanin max distance ?
        
        self.closestId = closest
        t1=time()
        helper.resetProgressBar()
#        helper.progressBar(label="checking point %d" % point)
#       what abou intractive display ?
        if display :
            sph = helper.Sphere("gPts",res=10,radius=20.0)[0]
            sph2 = helper.Sphere("sPts",res=10,radius=20.0)[0]
            cylN = helper.oneCylinder("normal",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0)
            cyl2 = helper.oneCylinder("V",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0)
            helper.changeObjColorMat(sph2,(0.,0.,1.))
        for ptInd in xrange(len(grdPos)):#len(grdPos)):
            # find closest OGsurfacepoint
            if display :
                helper.changeObjColorMat(sph,(1.,1.,1.))
                helper.changeObjColorMat(cylN,(1.,0.,0.))
            inside = False
            t2=time()
            gx, gy, gz = grdPos[ptInd]
            sptInd = closest[ptInd]#this is a vertices 
            if display :
                helper.setTranslation(sph,grdPos[ptInd])
                helper.setTranslation(sph2,srfPts[sptInd])
#            helper.update()
            if closest[ptInd]==-1:
                print("ouhoua, closest OGsurfacePoint = -1")
                pdb.set_trace()
            if sptInd < len(srfPts):
                sx, sy, sz = srfPts[sptInd]
                d = sqrt( (gx-sx)*(gx-sx) + (gy-sy)*(gy-sy) +
                          (gz-sz)*(gz-sz))
            else :
                t0=times()
#                try :
                n=bht.closePointsDist2(tuple(grdPos[ptInd]),diag,res,dist2)#wthis is not working  
                d = min(dist2[0:n])
                sptInd = res[tuple(dist2).index(d)]
#                except :
                    #this is quite long
                    #what about C4d/host
#                delta = ((numpy.array(srfPts)-numpy.array(grdPos[ptInd]))**2).sum(axis=1)  # compute distances
#                ndx = delta.argsort() # indirect sort 
#                d = delta[ndx[0]]
#                sptInd = ndx[0]
#                    delta = numpy.array(srfPts)-numpy.array(grdPos[ptInd])
#                    delta *= delta
#                    distA = numpy.sqrt( delta.sum(1) )
#                    d = min(distA)
#                print('distance time', time()-t0)
                sptInd = list(distA).index(d)
                sx, sy, sz = srfPts[sptInd]
            if distances[ptInd]>d: distances[ptInd] = d

            if self.fnormals is not None and useFix:
                #too slow
                facesN = self.getFacesNfromV(sptInd,ext=1)
                #now lets get all fnormals and averge them
                n = nx, ny, nz = numpy.average( numpy.array(facesN),0)
#            print (faces)
        
            # check if ptInd in inside
            else :
                n = nx, ny, nz = numpy.array(ogNormals[sptInd])
#            vRayCollidePos = iRT.f_ray_intersect_polyhedron(numpy.array(grdPos[ptInd]), numpy.array(srfPts[sptInd]), self.ref_obj, 0,point = ptInd);
#            if (vRayCollidePos %  2):
#                print ("inside")
#                inside = True
#                idarray[ptInd] = -number
#                insidePoints.append(grdPos[ptInd]) 
#            vnpos = numpy.array(npost[sptInd])
            facesN = self.getVNfromF(sptInd)
            d1 = helper.measure_distance(numpy.array(grdPos[ptInd]),numpy.array(srfPts[sptInd])+(n*0.00001))
            d2 = helper.measure_distance(numpy.array(grdPos[ptInd]),numpy.array(srfPts[sptInd]))
            print ("gridpont distance from surf normal %0.10f from surf  %0.10f closer to snormal %s" % (d1,d2,str(d1 < d2)))
#             check on what side of the surface point the grid point is
            vptos = numpy.array(srfPts[sptInd]) - numpy.array(grdPos[ptInd])
            if display : 
#                helper.updateOneCylinder("normal",[0.,0.,0.],(n*spacing),radius=1.0)#srfPts[sptInd],numpy.array(srfPts[sptInd])+(n*spacing*10.0),radius=10.0)
#                helper.updateOneCylinder("V",[0.,0,0.],vptos,radius=1.0)#srfPts[sptInd],numpy.array(srfPts[sptInd])+(v*spacing*10.0),radius=10.0)
                helper.updateOneCylinder("normal",srfPts[sptInd],numpy.array(srfPts[sptInd])+(n*spacing*10.0),radius=10.0)
                helper.updateOneCylinder("V",srfPts[sptInd],numpy.array(srfPts[sptInd])+(vptos*spacing*10.0),radius=10.0)
                helper.update()
            dots=[]
            vptos=helper.normalize(vptos)
            for fn in facesN :
                dot = numpy.dot(vptos,fn)
                dots.append(dot)
                if display : 
                    helper.updateOneCylinder("normal",srfPts[sptInd],numpy.array(srfPts[sptInd])+(fn*spacing*10.0),radius=10.0)
                    helper.update()
            gr=numpy.greater(dots, 0.0)
#            print dots
#            print gr
            include = True
            if True in gr and False in gr:
                include = False 
            dot = numpy.dot(vptos,n)#project vptos on n -1 0 1 
            vx,vy,vz = (gx-sx, gy-sy, gz-sz)
            dot2 = vx*nx + vy*ny + vz*nz
            a = helper.angle_between_vectors(vptos,n)
            print (dot,dot2,math.degrees(a),include)
#            if math.degrees(a) > 250. :#and math.degrees(a) <= 271 :
#                print (dot,dot2,a,math.degrees(a))
#            if a > (math.pi/2.)+0.1 and a < (math.pi+(math.pi/2.)):#<= gave he outside points 
            if dot > 0 and a < math.pi/2.0 and include :#and d1 > d2 :#and dot < (-1.*10E-5): # inside ?
                print("INSIDE",dot,dot2,a,math.degrees(a))  
                
#                print (grdPos[ptInd],srfPts[sptInd])
#                print ("point ",v," normal ",n)
#                print ("inside",dot,dot2,a,math.degrees(a),helper.vector_norm(v),helper.vector_norm(n))
                #and the point is actually inside the mesh bounding box
                inside = True
#                if self.checkinside :
#                    inside  = self.checkPointInsideBB(grdPos[ptInd])
                #this is not working for a plane, or any unclosed organelle...
                if inside :
                    idarray[ptInd] = -number
                    insidePoints.append(grdPos[ptInd]) 
                if display : 
                    helper.changeObjColorMat(sph,(1.,0.,0.))
                    helper.update()                    
                    res = helper.drawQuestion(title="Inside?",question="%0.2f %0.2f %0.2f %0.2f %s" % (d1,d2,a,math.degrees(a),str(inside)))
                    if not res :
                        return insidePoints, surfacePoints
#                sleep(5.0)
                
            p=(ptInd/float(len(grdPos)))*100.0
            helper.progressBar(progress=int(p),label=str(ptInd)+"/"+str(len(grdPos))+" inside "+str(inside))

#            print('inside time', time()-t2)
        print('total time', time()-t1)
        return insidePoints, surfacePoints

    def getSurfaceInnerPointsPandaRay(self,boundingBox,spacing,display = True,useFix=False):
        #should use the ray and see if it gave better reslt
        from AutoFill.pandautil import PandaUtil
        pud = PandaUtil()
        from AutoFill.HistoVol import Grid        
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        t=time()
        helper.progressBar(label="BuildGRid")
        grid.gridVolume,grid.nbGridPoints = grid.computeGridNumberOfPoint(boundingBox,spacing)
        grid.create3DPointLookup()
        nbPoints = grid.gridVolume
        grid.gridPtId = [0]*nbPoints
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
#        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
#        grid.distToClosestSurf = [diag]*nbPoints        
#        distances = grid.distToClosestSurf
#        idarray = grid.gridPtId
#        diag = grid.diag
        grdPos = grid.masterGridPositions
        insidePoints = []
        surfacePoints = self.vertices
        NPT=len(grdPos)
        meshnode = pud.addMeshRB(self.vertices, self.faces)
        #then sed ray from pointgrid to closest surface oint and see if collide ?
        #distance ? dot ? angle 
        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
        grid.distToClosestSurf = [diag]*nbPoints        
        distances = grid.distToClosestSurf
        idarray = grid.gridPtId
        diag = grid.diag
        
        from bhtree import bhtreelib
        self.ogsurfacePoints = self.vertices[:]
        self.ogsurfacePointsNormals = helper.FixNormals(self.vertices,self.faces,self.vnormals,fn=self.fnormals)
#        faces = self.faces[:]
#        self.createSurfacePoints(maxl=grid.gridSpacing)
        surfacePoints = srfPts = self.ogsurfacePoints
        print (len(self.ogsurfacePointsNormals),self.ogsurfacePointsNormals)
        self.OGsrfPtsBht = bht =  bhtreelib.BHtree(tuple(srfPts), None, 10)

        res = numpy.zeros(len(srfPts),'f')
        dist2 = numpy.zeros(len(srfPts),'f')

        number = self.number
        ogNormals = numpy.array(self.ogsurfacePointsNormals)
        insidePoints = []

        # find closest off grid surface point for each grid point 
        #FIXME sould be diag of organelle BB inside fillBB
        grdPos = grid.masterGridPositions
        returnNullIfFail = 0
        closest = bht.closestPointsArray(tuple(grdPos), diag, returnNullIfFail)#diag is  cutoff ? meanin max distance ?
        
        self.closestId = closest
        t1=time()
        helper.resetProgressBar()
#        helper.progressBar(label="checking point %d" % point)
#       what abou intractive display ?
        if display :
            sph = helper.Sphere("gPts",res=10,radius=20.0)[0]
            sph2 = helper.Sphere("sPts",res=10,radius=20.0)[0]
            sph3 = helper.Sphere("hitPos",res=10,radius=20.0)[0]
            cylN = helper.oneCylinder("normal",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0)
            cyl2 = helper.oneCylinder("V",[0.,0.,0.],[1.0,1.0,1.0],radius=20.0)
            helper.changeObjColorMat(sph2,(0.,0.,1.))
        for ptInd in xrange(len(grdPos)):#len(grdPos)):
            inside = False
            sptInd=closest[ptInd]
            v =- numpy.array(grdPos[ptInd]) + numpy.array(srfPts[closest[ptInd]])
            an = nx, ny, nz = numpy.array(ogNormals[sptInd])
#            start = Point3(grdPos[i][0],grdPos[i][1],grdPos[i][2])
            if display :
                helper.setTranslation(sph,grdPos[ptInd])
                helper.setTranslation(sph2,srfPts[closest[ptInd]])
                helper.update()  
#            end = Point3(srfPts[closest[i]][0]*diag,srfPts[closest[i]][1]*diag,srfPts[closest[i]][2]*diag)
            #raycats and see what it it on the mesh
            #or result = world.sweepTestClosest(shape, tsFrom, tsTo, penetration)
            res = pud.rayCast(grdPos[ptInd],(numpy.array(grdPos[ptInd])+v)*99999,closest=True)#world.rayTestAll(start, end)
            #can we get the number of hit?
            if res.hasHit():
                h = res
#                hit=res.getHits() 
##                for h in hit :
#                if len(hit):
#                h = hit[0]
                n = numpy.array(h.getHitNormal())
                a = helper.angle_between_vectors(v,n)
                dot = numpy.dot(v,n)
                dot2 = numpy.dot(an,v)
                a2 = helper.angle_between_vectors(-v,an)
                print ("hit with ",a,math.degrees(a),a2,math.degrees(a2),dot,dot2)
                if display : 
                    helper.setTranslation(sph3,numpy.array(h.getHitPos()))
                    helper.updateOneCylinder("normal",srfPts[sptInd],numpy.array(srfPts[sptInd])+(n*spacing*10.0),radius=10.0)
                    helper.updateOneCylinder("V",grdPos[ptInd],numpy.array(grdPos[ptInd])+(v),radius=10.0)
                    helper.update()
#                    if dot < 0 :#and dot < (-1.*10E-5): # inside ?
                if dot < 0.0 and dot2 < 0.0 :#a2 < (math.pi/2.)+0.1 and a > (math.pi/2.):# and a < (math.pi/2.) :#and a > (math.pi+(math.pi/2.)):
                    print("INSIDE",dot,a,math.degrees(a))
                    inside = True
                    if inside :
                        idarray[ptInd] = -number
                        insidePoints.append(grdPos[ptInd]) 
                    if display : 
                        helper.changeObjColorMat(sph,(1.,0.,0.))
                        helper.update()                    
                        res = helper.drawQuestion(title="Inside?",question="%0.2f %0.2f %0.2f %0.2f %s" % (dot,dot2,a,math.degrees(a),str(inside)))
                        if not res :
                            return insidePoints, surfacePoints
            p=(ptInd/float(len(grdPos)))*100.0
            helper.progressBar(progress=int(p),label=str(ptInd)+"/"+str(len(grdPos))+" inside "+str(inside))
                   
        return insidePoints, surfacePoints
        
    def getSurfaceInnerPointsPanda(self,boundingBox,spacing,display = True,useFix=False):
        #work for small object
        from AutoFill.pandautil import PandaUtil
        pud = PandaUtil()
        from AutoFill.HistoVol import Grid        
        grid = Grid()
        grid.boundingBox = boundingBox
        grid.gridSpacing = spacing# = self.smallestProteinSize*1.1547  # 2/sqrt(3)????
        t=time()
        helper.progressBar(label="BuildGRid")
        grid.gridVolume,grid.nbGridPoints = grid.computeGridNumberOfPoint(boundingBox,spacing)
        grid.create3DPointLookup()
        nbPoints = grid.gridVolume
        grid.gridPtId = [0]*nbPoints
        xl,yl,zl = boundingBox[0]
        xr,yr,zr = boundingBox[1]
        # distToClosestSurf is set to self.diag initially
#        grid.diag = diag = vlen( vdiff((xr,yr,zr), (xl,yl,zl) ) )
#        grid.distToClosestSurf = [diag]*nbPoints        
#        distances = grid.distToClosestSurf
#        idarray = grid.gridPtId
#        diag = grid.diag
        grdPos = grid.masterGridPositions
        insidePoints = []
        surfacePoints = self.vertices
        NPT=len(grdPos)
        rads = [spacing,]*NPT
        helper.progressBar(label="BuildWorldAndNode")
        t=time()
        def addSphere(r,pos,i):
            node = pud.addSingleSphereRB(r,name=str(i))
            node.setPos(pos[0],pos[1],pos[2])
            helper.progressBar(progress=int((i/float(NPT))*100.0),label=str(i)+"/"+str(NPT))           
            return node
        nodes =[addSphere(rads[i],grdPos[i],i) for i in range(NPT)  ]
#        node = pud.addMultiSphereRB(rads,grdPos)
        helper.progressBar(label="OK SPHERE %0.2f" % (time()-t))# ("time sphere ",time()-t)
        t=time()
        #add the mesh
        meshnode = pud.addMeshRB(self.vertices, self.faces)
        helper.progressBar(label="OK MESH %0.2f" % (time()-t))#
        #computeCollisionTest
        t=time()   
        iPtList=[]
        meshcontacts = pud.world.contactTest(meshnode.node())
        N=meshcontacts.getNumContacts()
        for ct in meshcontacts.getContacts():
            m=ct.getManifoldPoint ()
            d = m.getDistance ()
            print (ct.getNode0().getName(), ct.getNode1().getName(),d)
            i = eval(ct.getNode0().getName())
            if i not in iPtList :
                insidePoints.append(grdPos[i])
                iPtList.append(i)
        print ("N",len(insidePoints),NPT)
        print ("time contact",time()-t)
        return insidePoints, surfacePoints

    def printFillInfo(self):
        print('organelle %d'%self.number)
        r = self.surfaceRecipe
        if r is not None:
            print('    surface recipe:')
            r.printFillInfo('        ')

        r = self.innerRecipe
        if r is not None:
            print('    interior recipe:')
            r.printFillInfo('        ')
        
