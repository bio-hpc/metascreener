# -*- coding: utf-8 -*-
"""
Created on Tue Aug 28 20:47:45 2012

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

Name: 'pandautil'
@author: Ludovic Autin
"""
import sys
import numpy
try :
    import AutoFill
    helper = AutoFill.helper
except :
    helper= None
try :
    import panda3d
except :    
    p="/Developer/Panda3D/lib"
    sys.path.append(p)
try :
    import panda3d
    
    from panda3d.core import Mat4,Vec3,Point3
    from panda3d.core import TransformState
    from panda3d.core import BitMask32
    from panda3d.core import GeomVertexFormat,GeomVertexWriter,GeomVertexData,Geom,GeomTriangles
    from panda3d.core import GeomVertexReader
    from panda3d.bullet import BulletSphereShape,BulletBoxShape,BulletCylinderShape,BulletPlaneShape
    from panda3d.bullet import BulletTriangleMesh,BulletTriangleMeshShape,BulletConvexHullShape
    from panda3d.bullet import BulletSoftBodyConfig,BulletSoftBodyNode
    from panda3d.bullet import BulletRigidBodyNode,BulletGhostNode
    from panda3d.core import NodePath,GeomNode
    from panda3d.bullet import BulletWorld,BulletHelper
    from panda3d.core import Vec3
    from pandac.PandaModules import InternalName
except :
    panda3d = None


class PandaUtil:
    def __init__(self,*args,**kw):
        if panda3d is None :
            return
        from panda3d.core import loadPrcFileData
        
        loadPrcFileData("", "window-type none" ) 
        # Make sure we don't need a graphics engine 
        #(Will also prevent X errors / Display errors when starting on linux without X server)
        loadPrcFileData("", "audio-library-name null" ) # Prevent ALSA errors 
        loadPrcFileData('', 'bullet-max-objects 100240')#what number here ?
        import direct.directbase.DirectStart
        self.scale  = 10.0   
        self.worldNP = render.attachNewNode('World')            
        self.world = BulletWorld()
        if "gravity" in kw and kw["gravity"]:
            self.world.setGravity(Vec3(0, -9.81, 0))
        else :
            self.world.setGravity(Vec3(0, 0, 0))
        self.static=[]
        self.moving = None
        self.rb_panda = []
        self.rb_func_dic={
        "SingleSphere":self.addSingleSphereRB,
        "SingleCube":self.addSingleCubeRB,
        "MultiSphere":self.addMultiSphereRB,
        "MultiCylinder":self.addMultiCylinderRB,

        }        

    def delRB(self, node):
        if panda3d is None :
                return
        self.world.removeRigidBody(node)
        if node in self.rb_panda: self.rb_panda.pop(self.rb_panda.index(node))
        if node in self.static: self.static.pop(self.static.index(node))
        if node == self.moving: self.moving = None
        np = NodePath(node)
        np.removeNode()

    def setRB(self,inodenp,**kw):
        if "adamping" in kw :
            inodenp.node().setAngularDamping(kw["adamping"])
        if "ldamping" in kw :
            inodenp.node().setLinearDamping(kw["ldamping"])
        if "mass" in kw :
            inodenp.node().setMass(kw["mass"])
        if "pos" in kw :
            inodenp.setPos(kw["pos"][0],kw["pos"][1],kw["pos"][2])

    def addSinglePlaneRB(self,up,const,**kw):
        pup = Vec3(up[0],up[1],up[2])
        shape = BulletPlaneShape(pup,const)#nomal and constant
        name = "plane"
        if "name" in kw :
            name = kw["name"]
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(name))
#        inodenp.node().setMass(1.0)
#        inodenp.node().addShape(shape)
        inodenp.node().addShape(shape)#rotation ?      ,TransformState.makePos(Point3(0, 0, 0))  
#        spherenp.setPos(-2, 0, 4)
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())    
        self.world.attachRigidBody(inodenp.node())
        return inodenp

    def addSingleSphereRB(self,rad,**kw):
        shape = BulletSphereShape(rad)
        name = "sphere"
        if "name" in kw :
            name = kw["name"]
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode(name))
        inodenp.node().setMass(1.0)
#        inodenp.node().addShape(shape)
        inodenp.node().addShape(shape,TransformState.makePos(Point3(0, 0, 0)))#rotation ?
#        spherenp.setPos(-2, 0, 4)
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())    
        self.world.attachRigidBody(inodenp.node())
        return inodenp
        
    def addMultiSphereRB(self,rads,centT,**kw):
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode("Sphere"))
        inodenp.node().setMass(1.0)
        for radc, posc in zip(rads, centT):
            shape = BulletSphereShape(radc)#if radis the same can use the same shape for each node
            inodenp.node().addShape(shape, TransformState.makePos(Point3(posc[0],posc[1],posc[2])))#
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())    
        self.world.attachRigidBody(inodenp.node())
        return inodenp

    def addMultiSphereGhost(self,rads,centT,**kw):
        inodenp = self.worldNP.attachNewNode(BulletGhostNode("Sphere"))
        for radc, posc in zip(rads, centT):
            shape = BulletSphereShape(radc)
            inodenp.node().addShape(shape, TransformState.makePos(Point3(posc[0],posc[1],posc[2])))#
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())    
        self.world.attachRigidBody(inodenp.node())
        return inodenp     
        
    def addSingleCubeRB(self,halfextents,**kw):
        shape = BulletBoxShape(Vec3(halfextents[0], halfextents[1], halfextents[2]))#halfExtents
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode("Box"))
#        inodenp.node().setMass(1.0)
#        inodenp.node().addShape(shape)
        inodenp.node().addShape(shape,TransformState.makePos(Point3(0, 0, 0)))#, pMat)#TransformState.makePos(Point3(jtrans[0],jtrans[1],jtrans[2])))#rotation ?
#        spherenp.setPos(-2, 0, 4)
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())    
        self.world.attachRigidBody(inodenp.node())
        return inodenp
        
    def addMultiCylinderRB(self,rads,centT1,centT2,**kw):   
        inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode("Cylinder"))
        inodenp.node().setMass(1.0)
        centT1 = ingr.positions[0]#ingr.transformPoints(jtrans, rotMat, ingr.positions[0])
        centT2 = ingr.positions2[0]#ingr.transformPoints(jtrans, rotMat, ingr.positions2[0])
        for radc, p1, p2 in zip(rads, centT1, centT2):
            length, mat = helper.getTubePropertiesMatrix(p1,p2)
            pMat = self.pandaMatrice(mat)
#            d = numpy.array(p1) - numpy.array(p2)
#            s = numpy.sum(d*d)
            shape = BulletCylinderShape(radc, length,1)#math.sqrt(s), 1)# { XUp = 0, YUp = 1, ZUp = 2 } or LVector3f const half_extents
            inodenp.node().addShape(shape, TransformState.makeMat(pMat))#
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())    
        self.world.attachRigidBody(inodenp.node())
        return inodenp
    
    def setGeomFaces(self,tris,face):                
        #have to add vertices one by one since they are not in order
        if len(face) == 2 :
            face = numpy.array([face[0],face[1],face[1],face[1]],dtype='int')
        for i in face :        
            tris.addVertex(i)
        tris.closePrimitive()

    def addMeshRB(self,vertices, faces,ghost=False,**kw):
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

        shape = BulletTriangleMeshShape(mesh, dynamic=not ghost)#BulletConvexHullShape
        if ghost :
            inodenp = self.worldNP.attachNewNode(BulletGhostNode('Mesh'))
        else :
            inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode('Mesh'))
        inodenp.node().addShape(shape)
#        inodenp.setPos(0, 0, 0.1)
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())
   
        self.world.attachRigidBody(inodenp.node())
        return inodenp

    def addMeshConvexRB(self,vertices, faces,ghost=False,**kw):
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

        shape = BulletConvexHullShape(mesh, dynamic=not ghost)#
        if ghost :
            inodenp = self.worldNP.attachNewNode(BulletGhostNode('Mesh'))
        else :
            inodenp = self.worldNP.attachNewNode(BulletRigidBodyNode('Mesh'))
        inodenp.node().addShape(shape)
#        inodenp.setPos(0, 0, 0.1)
        self.setRB(inodenp,**kw)
        inodenp.setCollideMask(BitMask32.allOn())
   
        self.world.attachRigidBody(inodenp.node())
        return inodenp
        
    def addTriMeshSB(self,vertices, faces,normals = None,ghost=False,**kw):
        #step 1) create GeomVertexData and add vertex information
        # Soft body world information
        info = self.world.getWorldInfo()
        info.setAirDensity(0.0)
        info.setWaterDensity(0)
        info.setWaterOffset(0)
        info.setWaterNormal(Vec3(0, 0, 0))
        
        format=GeomVertexFormat.getV3n3() #getV3()#http://www.panda3d.org/manual/index.php/Pre-defined_vertex_formats
#        vdata = GeomVertexData('name', format, Geom.UHStatic)
        vdata=GeomVertexData("Mesh", format, Geom.UHStatic)
        
        vertexWriter=GeomVertexWriter(vdata, "vertex")
        [vertexWriter.addData3f(v[0],v[1],v[2]) for v in vertices]

        if normals is not None :
            normalWriter = GeomVertexWriter(vdata, 'normal')
            [normalWriter.addData3f(n[0],n[1],n[2]) for n in normals] 
        else :
            print "we need normals to bind geom to SoftBody"
            return None
        
        #step 2) make primitives and assign vertices to them
        tris=GeomTriangles(Geom.UHStatic)
        [self.setGeomFaces(tris,face) for face in faces]
        
        #step 3) make a Geom object to hold the primitives
        geom=Geom(vdata)
        geom.addPrimitive(tris)
        
        vdata = geom.getVertexData()
#        print (vdata,vdata.hasColumn(InternalName.getVertex()))
        geomNode = GeomNode('')
        geomNode.addGeom(geom)

        #step 4) create the bullet softbody and node
        bodyNode = BulletSoftBodyNode.makeTriMesh(info, geom)
#        bodyNode.linkGeom(geomNode.modifyGeom(0))
        bodyNode.setName('Tri')
        bodyNode.linkGeom(geom)  
        bodyNode.generateBendingConstraints(1)#???
        #bodyNode.getMaterial(0).setLinearStiffness(0.8)
        bodyNode.getCfg().setPositionsSolverIterations(4)
#        bodyNode.getCfg().setCollisionFlag(BulletSoftBodyConfig.CFVertexFaceSoftSoft, True)
        bodyNode.getCfg().setDynamicFrictionCoefficient(1)
        bodyNode.getCfg().setDampingCoefficient(0.001)
        bodyNode.getCfg().setPressureCoefficient(15000*10.0)  
        bodyNode.getCfg().setPoseMatchingCoefficient(0.2)
        bodyNode.setPose(True, True)
#        bodyNode.randomizeConstraints()
        bodyNode.setTotalMass(50000*10, True)
        
        bodyNP = self.worldNP.attachNewNode(bodyNode)
#        fmt = GeomVertexFormat.getV3n3t2()
#        geom = BulletHelper.makeGeomFromFaces(bodyNode, fmt,True)

#        bodyNode.linkGeom(geomNode.modifyGeom(0))
#        geomNode = GeomNode('')
#        geomNode.addGeom(geom)
        
#        world.attachSoftBody(bodyNode)
#        inodenp.setPos(0, 0, 0.1)
#        self.setRB(bodyNP,**kw)#set po
#        inodenp.setCollideMask(BitMask32.allOn())
        self.world.attachSoftBody(bodyNode)
        geomNP = bodyNP.attachNewNode(geomNode)
        return bodyNP,geomNP

    def addTetraMeshSB(self,vertices, faces,normals = None,ghost=False,**kw):
        #step 1) create GeomVertexData and add vertex information
        # Soft body world information
        info = self.world.getWorldInfo()
        info.setAirDensity(1.2)
        info.setWaterDensity(0)
        info.setWaterOffset(0)
        info.setWaterNormal(Vec3(0, 0, 0))
    
        points = [Point3(x,y,z) * 3 for x,y,z in vertices]
        indices = sum([list(x) for x in faces], [])
        #step 4) create the bullet softbody and node
        bodyNode = BulletSoftBodyNode.makeTetMesh(info, points, indices, True)

        bodyNode.setName('Tetra')
        bodyNode.setVolumeMass(150000)
        bodyNode.getShape(0).setMargin(0.01)
        bodyNode.getMaterial(0).setLinearStiffness(0.9)
        bodyNode.getCfg().setPositionsSolverIterations(4)
        bodyNode.getCfg().clearAllCollisionFlags()
        bodyNode.getCfg().setCollisionFlag(BulletSoftBodyConfig.CFClusterSoftSoft, True)
        bodyNode.getCfg().setCollisionFlag(BulletSoftBodyConfig.CFClusterRigidSoft, True)
        bodyNode.generateClusters(12)
        bodyNode.setPose(True, True)
        bodyNP = self.worldNP.attachNewNode(bodyNode)
        
        geom = BulletHelper.makeGeomFromFaces(bodyNode)
        geomNode = GeomNode('vtetra')
        geomNode.addGeom(geom)
        
#        self.setRB(bodyNP,**kw)#set po
#        inodenp.setCollideMask(BitMask32.allOn())
        self.world.attachSoftBody(bodyNode)
        geomNP = bodyNP.attachNewNode(geomNode)
        bodyNode.linkGeom(geom)
        return bodyNP,geomNP

    def getVertices(self,node,gnode):
        geomNode = gnode.node()
        ts = node.getTransform() 
        m = ts.getMat().getUpper3()
        p = ts.getMat().getRow3(3)
        points=[]
        geom = geomNode.getGeoms()[0]
        vdata = geom.getVertexData()
        reader = GeomVertexReader(vdata, 'vertex')
        while not reader.isAtEnd():
            v = reader.getData3f()
            v = m.xform(v) + p
            points.append(Point3(v))
        return numpy.array(points,dtype=numpy.float32)
        
    def pandaMatrice(self,mat):
        mat = mat.transpose().reshape((16,))
#        print mat,len(mat),mat.shape
        pMat = Mat4(mat[0],mat[1],mat[2],mat[3],
                   mat[4],mat[5],mat[6],mat[7],
                   mat[8],mat[9],mat[10],mat[11],
                   mat[12],mat[13],mat[14],mat[15],)
        return pMat
        
#    
#    def addRB(self,rtype,static,**kw):
#        # Sphere
#        if panda3d is None :
#            return None
#        if rotMatis not None and trans is not None:
#            mat = rotMat.copy()
#            mat = mat.transpose().reshape((16,))
#
#            pMat = TransformState.makeMat(Mat4(mat[0],mat[1],mat[2],mat[3],
#                                           mat[4],mat[5],mat[6],mat[7],
#                                           mat[8],mat[9],mat[10],mat[11],
#                                           trans[0],trans[1],trans[2],mat[15],))
#        shape = None
#        inodenp = None
##        print (pMat) 
#        inodenp = self.rb_func_dic[rtype](ingr,pMat,trans,rotMat)

#        inodenp.setCollideMask(BitMask32.allOn())
    
#        self.world.attachRigidBody(inodenp.node())
#        if static :
#            self.static.append(inodenp.node())
#        else :
#            self.moving = inodenp.node()
#        self.rb_panda.append(inodenp.node())
#        return inodenp.node()
    
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

    def applyForce(self,node,F):
        F*=self.scale
        node.node().applyCentralForce(Vec3(F[0],F[1],F[2]))
#        node.node().applyForce(Vec3(F[0],F[1],F[2]),Point3(0, 0, 0))
#        print F
        
    def rayCast(self, startp,endp,closest=False):
        start=Point3(startp[0],startp[1],startp[2])
        end=Point3(endp[0],endp[1],endp[2])
        if closest :
            res = self.world.rayTestClosest(start, end)
        else :
            res = self.world.rayTestAll(start, end)  
        return res

    def sweepRay(self, startp,endp):
        tsFrom = TransformState.makePos(Point3(0, 0, 0))
        tsTo = TransformState.makePos(Point3(10, 0, 0))
        shape = BulletSphereShape(0.5)
        penetration = 0.0
        result = self.world.sweepTestClosest(shape, tsFrom, tsTo, penetration)
        return result 

    def update(self,task,cb=None):
#        print "update"
        dt = globalClock.getDt()
#        print dt
        self.world.doPhysics(dt, 10, 0.008)#,100,1.0/500.0)#world.doPhysics(dt, 10, 1.0/180.0)
        #this may be different for relaxing ?
#        print task.time
        if cb is not None :
            cb()
        if task is not None:
            return task.cont
        #look at modeer update-> AF update