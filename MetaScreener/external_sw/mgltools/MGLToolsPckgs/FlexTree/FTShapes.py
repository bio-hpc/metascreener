## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

#########################################################################
#
# Date: Jan 2004  Authors: Daniel Stoffler, Michel Sanner
#
# stoffler@scripps.edu
# sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner, and TSRI
#
#########################################################################

"""This module implements the objects used to represent shape in  a
flexibility tree.
"""
import sys
import types
from MolKit.molecule import Atom, AtomSet
from MolKit.tree import TreeNode, TreeNodeSet
    
from numpy.oldnumeric import sum, ArrayType, array, identity
from math import sqrt
import weakref

class FTShape:
    """Base class for describing shapes"""

    def __init__(self, node=None):
        """constructor"""

        self.name = None
        self.ownsGeom = True
        if node is not None:
            from FlexTree.FT import FTNode
            assert isinstance(node, FTNode)
            self.node = weakref.ref(node)  # weak reference to FlexTree node
        else:
            self.node = None
        self.geoms = []                   # list of DejaVu geometries
 

    def updateGeoms(self):
        """to be implemented by subclasses."""
        pass


    def getCoords(self):
        """returns current conformation (coords)"""
        coords = None
        if self.node is not None:
            coords = self.node().getCurrentConformation()
            
        return coords

        
    def getGeoms(self):
        """returns list of geoms currently stored in this object"""
        return self.geoms


    def configure(self, **kw):
        """Configure FTShape attributes"""

        if kw.has_key('name') and kw['name'] is not None:
            self.name = name


    def getDescr(self):
        """returns a dict with shapeParams. Shape type is extracted in FTNode
        getDescr()"""
        return {'name':self.name}


class FTGeom(FTShape):
    """This shape object is built from a DejaVu geoemtry which never changes
"""
    def __init__(self, geom=None, node=None, name='FTGeom'):
        """constructor"""
        FTShape.__init__(self, node)
        self.ownsGeom = False
        if geom:
            self.geoms = [geom]
        return


class FTSphere(FTShape):
    """ Sphere shape """
    def __init__(self, node=None, name='sphere'):
        """constructor"""        
        FTShape.__init__(self, node)
        from DejaVu.Spheres import Spheres
        self.geoms.append( Spheres(name, inheritMaterial=0) )


    def updateGeoms(self):
        coords = self.getCoords()
        if len(coords):
            res, rg = self.gyrationSphere(coords)
            verts = [ res[0], res[1], res[2] ]
            self.geoms[0].Set(vertices=[verts], radii=[rg], quality=30)
    

    def gyrationSphere(self, points):

        if not isinstance(points, ArrayType):
            points = array(points)

        # compute centroid
        center = sum(points)/len(points)
        # compute dist distances (vectorized)
        delta = points-center
        rg = sqrt( sum( sum( delta*delta, 1))/float(len(points)) )
        return center, rg


class FTEllipsoid(FTShape):

    def __init__(self, node=None, name='ellipsoid'):
        """constructor"""

        FTShape.__init__(self, node)
        from DejaVu.Ellipsoids import Ellipsoids
        self.geoms.append( Ellipsoids(name, inheritMaterial=0, quality=30) )
        self.ellipse = None


    def updateGeoms(self):
        coords = self.getCoords()
        if len(coords):
            self.fitEllipsoid(coords)


    def fitEllipsoid(self, coords):
        # FIXME: expose these!
        cov_scale = 1.75
        ell_scale = 1.0

        # create an ellipsoid structure
        #ellipse = efit.efitc.new_ellipsoid()
        # create an ellipsoidInfo structure
        #ellipseInfo = efit.efitc.new_efit_info()
        # compute the ellipsoid
        #status = efit.fitEllipse(coords, ell_scale, cov_scale,
        #                         ellipseInfo, ellipse)

        try:
            #from geomutils import geomutilslib
            from geomutils import efitlib
        except:
            print "Error importing efitlib from geomutils module "
            return
        
        ellipse = efitlib.ellipsoid()
        ellipseInfo = efitlib.efit_info()
        status = efitlib.fitEllipse(coords, ell_scale, cov_scale,
                                         ellipseInfo, ellipse)

        if status==0: # OK
            center = ellipse.getPosition() 
            size = ellipse.getAxis().astype('f')
            orient = identity(4, 'f')
            orient[:3, :3] = ellipse.getOrientation()
            self.geoms[0].Set(
                centers=[center], scaling=[size], orientation=[orient])
            self.ellipse=ellipse


    def showCoords(self):
        """Display the coords system of ellipsoid.."""
        if self.ellipse is None:
            return
        center = self.ellipse.getPosition()
        size = self.ellipse.getAxis().astype('f')
        orient = self.ellipse.getOrientation()
        x=orient[0]
        y=orient[1]
        z=orient[2]        
        ##print "** center at ",center
        ##print "** length of axis", size
        scale=size.tolist()
        shortest = scale.index(min(scale))
        ##print '** shortest axis is  ',shortest
        if self.geoms[0].viewer is not None:
            vi=self.geoms[0].viewer                
            ## draw coordinate system
            from DejaVu.Cylinders import CylinderArrows
            from opengltk.OpenGL import GL
            
            xx=center+x*scale[0]
            yy=center+y*scale[1]
            zz=center+z*scale[2]
            vers=(center, xx.tolist(),yy.tolist(),zz.tolist())
            coordSyst = CylinderArrows('coordSystem',
                       vertices=vers,
                       faces = ([0,1], [0,2], [0,3]),
                       materials = ((1.,0,0), (0,1,0), (0,0,1)),
                       radii = 0.06, inheritMaterial=False,
                       inheritCulling=False,
                       backPolyMode=GL.GL_FILL, inheritBackPolyMode=False,
                       quality=10, visible =0)
            #FIXME does not work if passed to constructor
            coordSyst.Set(culling=GL.GL_NONE) 
            vi.AddObject(coordSyst)



class FTBox(FTShape):

    def __init__(self, node=None, name='box'):
        """constructor"""

        FTShape.__init__(self, node)


class FTConvexHull(FTShape):
    
    def __init__(self, node=None, name='convexhull'):
        """constructor"""

        try:
            from binaries.qconvex import QConvex
        except:
            print "Warning: could not import QConvex. ", sys.exc_info()[1]
            return

        FTShape.__init__(self, node)
        self.QConvex = QConvex(name)
        self.geoms.append( self.QConvex.getGeom() )


    def updateGeoms(self):
        coords = self.getCoords()
        if len(coords):
            self.QConvex.computeConvex(coords) # this also sets the geom


class FTMsms(FTShape):
    """ Defines the MSMS shape for FTNode.
FIXME: In the future we will have to expose more parameters, especially the
all-components flag and the list of atoms for seeding the calculation
Yong 4-8-2004
"""
    def __init__(self, node=None, name='msms'):
        """constructor"""

        FTShape.__init__(self, node)
        surfName = 'MSMS'
        self.density = 1.0
        self.pRadius = 1.5

        from DejaVu.IndexedPolygons import IndexedPolygons
        g = IndexedPolygons( surfName, pickableVertices=1)
        g.userName = surfName
        from opengltk.OpenGL import GL
        g.RenderMode(GL.GL_FILL, face=GL.GL_FRONT, redo=0)
        self.geoms.append(g)        


    def updateGeoms(self):         
        if self.node is None:
            return

        from MolKit.molecule import Atom
        molFrag = self.node().molecularFragment.findType(Atom)
        c=molFrag.coords
        mol = molFrag.top.uniq()[0]
        r=mol.defaultRadii(united=0, atomSet= molFrag)
        from mslib import MSMS
        srf = MSMS(coords=c, radii=r)
        srf.compute(probe_radius=self.pRadius, density=self.density)
        
        vf,vi,f = srf.getTriangles()
        g = self.geoms[0]
        #col = geomC.getGeomColor(surfName)
        g.Set( vertices=vf[:,:3], vnormals=vf[:,3:6], faces=f[:,:3],
               # materials=col
              visible=1 )        

    def configure(self, density=1.0, pRadius=1.5):
        self.density = density
        self.pRadius = pRadius


    def getDescr(self):
        descr = FTShape.getDescr(self)
        descr['density'] = self.density
        descr['pRadius'] = self.pRadius
        return descr
        


class FTLines(FTShape):
    """ Defines the Line shape for FTNode
"""
    def __init__(self, node=None, name='FTLines'):
        """constructor"""

        self.cutoff = 1.85 # for build bonds by distance
        FTShape.__init__(self, node)

        from DejaVu.IndexedPolylines import IndexedPolylines

        self.geoms.append( IndexedPolylines(name, inheritMaterial=0) )
        self.hasBonds = False # flag for buildBondsByDistance
        self.crossSetGeoms = False # flag for build cross set geometries..
        self.neighborAtoms = AtomSet()
        self.bondIndexBuilt=False # flag for build bondIndeces.
        self.bondIndices = []

    def updateGeoms(self):
        if self.node is None:
            return

        ftNode=self.node()
        if not self.hasBonds:
            # the buildBondsByDistance is called when parsing XML file
            # since rotamer lib or other discreteMotion can result in bad
            # conformations ==> wrong bonds will be built here.
            # self.cutoff is not used .. as Jun 23, 2005
            
##             print 'build bonds...at', ftNode.name
##             for m in ftNode.getAtoms().top.uniq():
##                 m.buildBondsByDistance(self.cutoff)
            self.hasBonds = True

            coords = self.getCoords()            
            if not self.bondIndexBuilt and len(coords):
                atoms = ftNode.getAtoms()
                oldConf= atoms[0].conformation
                if oldConf !=0:
                    atoms.setConformation(0)
                bnds, nobnds = atoms.bonds            
                atoms._bndNb = range(len(atoms))
                self.bondIndices = map(lambda x:
                                       (x.atom1._bndNb,x.atom2._bndNb),
                                       bnds)
                if oldConf !=0:
                    atoms.setConformation(oldConf)
                self.bondIndexBuilt=True
                
            self.geoms[0].Set(vertices=coords, faces=self.bondIndices)
            # dirty hack for showing secondary structure
            if len(self.geoms) ==2:               
                self.geoms[1].Set(vertices=coords)
        else:
            coords = self.getCoords()
            self.geoms[0].Set(vertices=coords)

    def updateCrossSetGeoms(self):
        """ the lines between two FT nodes"""
        # fixme: this should be moved to shape-combiner class..
        if self.node is None:
            return        

        ftNode=self.node()        
        if not self.crossSetGeoms:
            newAtomsCoords = []
            atoms = ftNode.getAtoms()
            bnds, nobnds = atoms.bonds
            if ftNode.refNode is not None:
                parentAtoms=ftNode.refNode().molecularFragment
                if parentAtoms is not None:
                    for a in parentAtoms:
                        for b in atoms:
                            if b.isBonded(a):
                                self.neighborAtoms.append(a)

            if  len(self.neighborAtoms) != 0:
                atoms.extend(self.neighborAtoms)
            bnds, nobnds = atoms.bonds            
            atoms._bndNb = range(len(atoms))

            
            bondIndices = map(lambda x: (x.atom1._bndNb,x.atom2._bndNb), bnds)
            
            coords = self.getCoords()
            
##            if coords is not None and len(newAtomsCoords) != 0:
##                 if type(coords) is not types.ListType:                
##                     coords = coords.tolist()
##                     coords.extend(newAtomsCoords)
##                 else:
##                     coords.extend(newAtomsCoords)
                   
            self.geoms[0].Set(vertices=coords, faces=bondIndices)
            self.crossSetGeoms=True
        else:
            coords = self.getCoords()
            self.geoms[0].Set(vertices=coords)
        ##

    def getCoords(self):
        """
returns current conformation (coords) and the cross_set (neighbors)
"""
        
        coords = FTShape.getCoords(self)
        if len(self.neighborAtoms) ==0:
            #print self.node().name,'no neighbor'
            return coords

        if type(coords) is not types.ListType:
            coords = coords.tolist()
            
        coords.extend(self.neighborAtoms.coords)

        return coords
        


    def configure(self, cutoff=1.85, **kw):
        self.cutoff = cutoff
        

    def getDescr(self):
        descr = FTShape.getDescr(self)
        descr['cutoff'] = self.cutoff
        return descr
        

class FTCPK(FTShape):

     def __init__(self, node=None, name='cpk'):
        """constructor"""

        self.quality = 20     # sphere quality
        self.united = False   # radii keywords

        FTShape.__init__(self, node)
        from DejaVu.Spheres import Spheres
        self.geoms.append( Spheres(name, inheritMaterial=0) )


     def updateGeoms(self):
         
        if self.node is None:
            return
        # get radii
        radii = []
        for m in self.node().getAtoms().top.uniq():
            m.defaultRadii(united=self.united)
            radii.extend(m.allAtoms.radius)
        coords = self.getCoords()
        if len(coords):
            self.geoms[0].Set(vertices=coords, radii=radii,
                              quality=self.quality)
        

     def configure(self, quality=20, united=False):
        self.quality = quality
        self.united = united


     def getDescr(self):
         descr = FTShape.getDescr(self)
         descr['quality'] = self.quality
         descr['united'] = self.united
         return descr
        
        
class FTStickAndBalls(FTShape):

    def __init__(self, node=None, name='stickandballs'):
        """constructor"""

        FTShape.__init__(self, node)


if __name__=='__main__':
    from MolKit import Read
    mol = Read('1crn.pdb')
    ats = mol.chains.residues.atoms

    # test Sphere
    SphereShape = FTSphere(ats)

    # test Lines
    LineShape = FTLines(ats)

    # test CPK
    CPKShape = FTCPK(ats)

    # test Convex
    ConvexShape = FTConvexhull(ats)

    # test Ellipsoid
    EllipsoidShape = FTEllipsoid(ats)
    
    from DejaVu import Viewer
    vi = Viewer()

    vi.AddObject(SphereShape.getGeoms()[0])
    #vi.AddObject(LineShape.getGeoms()[0])
    #vi.AddObject(CPKShape.getGeoms()[0])
    #vi.AddObject(ConvexShape.getGeoms()[0])
    #vi.AddObject(EllipsoidShape.getGeoms()[0])
