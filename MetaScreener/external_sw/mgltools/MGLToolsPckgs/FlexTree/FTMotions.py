## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: Jan 2004 Authors: Michel Sanner, Yong Zhao, Daniel Stoffler
#
#   sanner@scripps.edu
#   yongzhao@scripps.edu
#   stoffler@scripps.edu
#       
#   The Scripps Research Institute (TSRI)
#   Molecular Graphics Lab
#   La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Yong Zhao, Daniel Stoffler, and TSRI
#
#########################################################################

"""
This modules implements the motion operators fo the Flexibility tree.
Motion object all subclass the FTMotion base class.

Please be notied that after Jan.30th, 2004, the transformation in motion
classes will NOT use the mglutil/math/transformation.py (class Transformation)
Instead, the class rotax in mglutil/math/rotax.py will be used.
The transform object in all motions is now always a 4 by 4 matrix.
rotax returns an clockwise angle around the axis

naming conventions:
1) Motion is defined as "description" plus "parameters". Here description
   defines what the motion is, while the parameter defines how much a object
   can be moved by this motion.
   For example, a hinge motion can be described as rotation about an axis (the
   description) by certain angle (the parameter)
    
2) An axis is the combination of a vector and a point


Sub classes must implement the following methods.
getMatrix() :   returns the transformation matrix, a 4x4 list of float
apply()     :   apply the transformation matrix to a list of points
randomize() :   randomly changes the setting of motion
configure() :   changes the setting of motion
getCurrentSetting():  returns current setting of motion
getParam()  :   returns two lists: list of parameters, list of valid values
                only returns the parameter, not the descrption of the motion.
                (Used by GA searching)                
  
Type of motions defined:

FTMotion (base class)
|
|__ FTMotion_DiscreteRotAboutPoint(discrete rotation about a point, 54000 rots)
|
|__ FTMotion_RotationAboutPoint (continuous rotation about a point, quaternion)
|
|__ FTMotion_RotationAboutAxis: (rotation about an axis by any angle)
|   |
|   |_ FTMotion_Hinge           (rotation about an axis by certain angle)
|
|__ FTMotion_Translation:       (translation along a axis by any magnitude)
|   |
|   |_ FTMotion_BoxTranslation  (translation within a given 3D box)
|   |
|   |_ FTMotion_SegmentTranslation (translation along a axis by any magnitude)
|   
|__ FTMotion_Screw:        (Screwing, combination of rotation and translation )
|
|__ FTMotion_Generic:           (a generic 4x4 transformation)
|
|__ FTMotion_Identity:          (identity motion.) 
|
|__ FTMotion_Discrete:    (vitual class. the points are not rigid body )
    |
    |__ FTMotion_NormalMode:      (normal modes applied as motion)
    |
    |__ FTMotion_Rotamer:         (side chain motion, backbone independent) 
    |
    |__ FTMotion_Absolute (pick one of the n predefined conformation)
                          (NOT implemented yet)

*******************
Notes:
    the OpenGL style 4x4 transformation matrix is stored as self.transform
    
"""
#from FlexTree.FT import VERBOSE

from mglutil.math.transformation import Transformation
import types, os, numpy
from random import uniform, gauss
from mglutil.math.rotax import rotax, rotVectToVect
from math import pi, sqrt, asin, acos, degrees, radians, sin, cos

from MolKit.molecule import Atom, AtomSet
from MolKit.protein import Residue, ResidueSet
from MolKit.tree import TreeNode, TreeNodeSet

from FlexTree.EssentialDynamics import EssentialDynamics

degtorad = pi/180.

from mglutil.math import norm, crossProduct
def defineLocalCoordSys(CB, CA, C):
    """
define the local coordinate system based on CA, CB ,C position
Origin: CA
Y axis: CA -> CB
X axis: in same plane of CB-CA-C, orthogonal with Y axis
Z axis: orthogonal with X and Y axis

CA, CB, C: xyz coords, given as numpy.array type

returns a 3X3 array
    """
    Y=norm(CB-CA)
    tmp=C-CB
    Z=crossProduct(tmp,Y)
    X=crossProduct(Y,Z,False)
    res=numpy.identity(3,'f')
    res[:,0] = X
    res[:,1] = Y.tolist()
    res[:,2] = Z
    return res


def getOthogonalVecter(vector):
    """ returns a vector that is parpendicular with given vector
NOTE: input vector should be normalized, type numpy.array
    """
    v=vector
    tmp=abs(v)
    idx=tmp.tolist().index(min(tmp))
    u=numpy.array(v)
    if v[idx] >= 0:
        u[idx]=1.0
    else:
        u[idx]=-1.0
##     print id(v),v
##     print id(u),u
##     print "-----", idx
    return crossProduct(v,u)
    
    


def dist(a,b):
    """return the distance between point a and point b
(3 dimension)"""
    return sqrt((a[0]-b[0])**2 +(a[1]-b[1])**2 + (a[2]-b[2])**2)

def _distSQR(a,b):
    """return the square of distance between point a and point b
(3 dimension)"""
    return (a[0]-b[0])**2 +(a[1]-b[1])**2 + (a[2]-b[2])**2


class FTMotion:
    """ Defines the types of motion in the Flexibility Tree (FT)
self.name:     name of this motion object
self.node:     weakref of FTNode object, whose motion object is 'self'
self.transform:Transformation object, a GL-style 4x4 matrix
self.percent:  used to randomize currrent motion, a float number, usually
               between 0.0 and 1.0 (0% and 100%)
self.tolerance:a float number specifying how far the percent can go below 0% or
               go above 100%. for example, when self.tolerance = 0.05, the
               self.percent can be anywhere between -5% to 105%
self.can_be_modified: if True, the variables in this motion can be modified (either by randomization or GA) thus generates a new transormation. if False, the motoin can not be modified by any means. Here is an example of can_be_modifed=False: A translation motion that moves a molecule to the center of a docking box should never be modified during the docking process.
               
"""
    
    def __init__(self, name='motion'):
        """constructor"""
        self.node = None         # weakref to FTNode, set in FTNode.configure()
        self.name = name         # description (name) of motion
        self.type = self.__class__.__name__ # type of motion (class name)
        self.transform = None    # Transformation object, a GL-style 4x4 matrix
        self.widgetsDescr = {}   # used to build widgets to manipulate params
        self.percent=1.0         # used to randomize currrent motion
        self.tolerance=0.05      # the tolerance of randomize()
        self.can_be_modified = 1 # True
        self.cutPoints = None    # set to list of alowed cutPoints for cross over
        self.active = True
        #self.configure(name=name, percent=percent, tolerance=tolerance)
        
    def __repr__(self):
        """ The represetation of the Motion object. """
        current = self.getCurrentSetting()
        from types import StringType
        string=self.__class__.__name__ + " object:\n"

        #always move the 4X4 matrix to the end of representation string
        #transform=current['transformation']
        #del current['transformation']
        for k,v in current.items():
            if type(v) is not StringType:
                v=str(v)
                if len(v) > 512:
                    v=v[:512] + " ... ..."
            tmp = k + ' : ' + v + '\n'
            string +=tmp
        
        string += "4X4 transformation matrix:\n"
        string += str(self.getMatrix())
        return string 
    
        
    def getMatrix(self):
        """virtual method
returns a 4x4 transformation matrix corresponding to the current trasnforamtion
NOTES: Here the 4x4 transformation matrix is a numpy Array. ( not a list !)

"""
        pass
        
        
    def apply(self, points):
        """ returns the coordinates after transformation
points: a list of xyz (float number) coordinations (n,3) or (n,4)"""
        sh=numpy.array(points).shape
        if len(sh)==1: # only one point, instead of a list of points           
            if sh[0]==3:
                points.append(1.0)
                return numpy.dot([points], \
                                              self.transform).astype('f')
        if sh[1] == 4:
            homoCoords = points
        elif sh[1] == 3:
            homoCoords = numpy.concatenate((points,
                         numpy.ones( (len(points), 1), 'd')), 1)
        else:
            raise ValueError("The points given are not in right format")

        res=numpy.dot(homoCoords, self.transform).astype('f')
        if sh[1] == 4:
            return res
        else:
            return res[:, :3]


    def perturb(self, amplitude):
        """
        virtual method
        randomly change the configuration of current transformation
        """
        raise RuntimeError, 'ERROR: perturb is not implemented for', self.name


    def mutate(self):
        """
        virtual method
        randomly change the configuration of current transformation
        """
        raise RuntimeError,'mutate is not implemented for', self.name


    def randomize(self):
        """
        virtual method
        randomly change the configuration of current transformation
        """
        raise RuntimeError, 'ERROR: randomize is not implemented for', self.name


    def configure(self, name=None, percent=None,tolerance=None, **kw):
        """Set the parameters of this motion object and update its
transformation. """
        if name is not None:
            self.name = name
        if percent is not None:
            self.percent=percent
        if tolerance is not None:
            self.tolerance = tolerance

        if kw.has_key("can_be_modified"):
            can_be_modified=kw['can_be_modified']
            assert can_be_modified in [True, False]
            self.can_be_modified=can_be_modified

        return

    def getDescr(self):
        """ used by FT.py, returns the motion parameter dictionary
"""
        return self.getCurrentSetting()
    

    def getCurrentSetting(self):
        """returns a dict with motionParams.
"""
        descr={'name':self.name, }
        descr['can_be_modified'] = self.can_be_modified
        return descr


    def getParam(self):
        """virtual method
"""
        pass


    def callConfigure_cb(self, name, value):
        """call configure method for given argument. Used when binding widgets
to FTMotion object"""
        apply( self.node().configure, (), {
            'motionParams':{name:value}, 'autoUpdateConf':True,
            'autoUpdateShape':True})


class FTMotion_Identity(FTMotion):
    """ Defines identity motion """
    def __init__(self, name = 'Identity'):
        self.configure(name=name)
        self.transform = numpy.identity(4, 'f')
        self.widgetsDescr = {}  

    def getMatrix(self):
        return self.transform

    def configure(self, name=None):
        if name is not None:
            FTMotion.configure(self, name=name)

    def apply(self, points):
        """ returns the coordinates after transformation """
        return points  # identity !



class FTMotion_RotationAboutAxis(FTMotion):
    """ Defines a rotation about an arbitrary axis.
The axis can either be specified using the point and a vector or by providing
two points.
"""


    def __init__(self, axis=None, points=None,
                 angle=0.0, name='rotation about an axis',
                 type='FTMotion_RotationAboutAxis',
                 tolerance=None):
        """Constructor
The parameters are an axis which can be specified either using a point in a
vector passed as a dictionnary (i.e. axis={'vector':vector, 'point':point}),
or by passing a sequence of 2 3D points (i.e. ((0.,0,0), (13,3,0)) ).
angle: is an angle in degrees
"""
        self.point1 = (0.,0.,0.)    # first point defining rotation axis
        self.point2 = (1.,0.,0.)    # second point defining rotation axis
        self.angle = 0.0            # rotation angle in degrees
        self.transform = None       # C-style 4x4 transformation matrix
        FTMotion.__init__(self)
        self.tolerance=0.0
        
        self.configure(axis=axis, points=points, angle=angle, name=name,
                       tolerance=tolerance)
        self.widgetsDescr['angle'] = {
        'widget':'Dial', 'callback':FTMotion.callConfigure_cb
        }


    def updateTransformation(self):
        """
        recompute the new 4x4 transformation matrix, stored in
        self.transform
        """
        self.transform = rotax(self.point1, self.point2, self.angle*degtorad,
                               transpose=1)
        
        
    def getMatrix(self, transpose=False):
        """returna 4x4 transformation matrix corresponding to the current 
rotation. If transpose is True, the matrix is a standard 4x4 matrix with the 
translation in the last column, else the matrix is transposed.
NOTES: Here the 4x4 transformation matrix is a numpy Array. ( not a list !)

"""
        if not transpose:
            return numpy.array(self.transform, 'f')        
        else:
            return numpy.array(numpy.transpose(self.transform),'f')
        
        
        
    def configure(self, axis=None, points=None, angle=None, name=None,
                  percent=None, tolerance=None, type=None,
                  update=True, **kw):
        """reset the vector and angle"""

        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        FTMotion.configure(self, name=name,
                           tolerance=tolerance, percent=percent)

        point1 = point2 = None
        if points is not None:
            assert len(points)==2 and len(points[0])==3 and len(points[1])==3
            point1 = points[0]
            point2 = points[1]

        if axis is not None:
            assert isinstance(axis, types.DictType)
            point1 = axis['point']
            v = axis['vector']
            point2 = [point1[0]+v[0], point1[1]+v[1], point1[2]+v[2]]

        if point1 is not None and point2 is not None:
            self.point1 = point1   # defines a rotation axis using 2 points
            self.point2 = point2   

        if angle is not None:
            self.angle = angle

        if update:
            self.updateTransformation()

        if self.node:
            self.node().newMotion = True 
        

    def randomize(self):
        """
        randomize the parameters of rotation motion.
        the default parameters reset the rotation angle
        """
        angle = uniform(0., 360.)
        self.configure(angle=angle)


    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        self.point1==list(self.point1)
        self.point2==list(self.point2)
            
        myDescr = {'point1':self.point1, 'point2':self.point2,
                   'angle':self.angle}

        
     #   print myDescr
        myDescr.update(descr)
        return myDescr
        

    def getParam(self):
        """ get GA related parameters .. returns two lists.
list of parameter names and list of dictionaries
"""
        validParamName =[]
        validParam = []
        validParamName.append('percent')
        validParam.append({'type': 'continuous','dataType':'float',
                           'mutator': 'gaussian',
                           'min':0.0, 'max':1.0})
        
        return validParamName, validParam
        


class FTMotion_Hinge(FTMotion_RotationAboutAxis):
    """ Defines a hinge rotation about an arbitrary axis.
The axis can either be specified using the point and a vector or by providing
two points. The motion is limited to the mini and maxi angles. 
"""


    def __init__(self, axis=None, points=None, angle=0.0, name='hinge',
                 min_angle=None, max_angle=None, tolerance=None):
        """Constructor
The parameters are an axis which can be specified either using a point in a
vector passed as a dictionnary (i.e. axis={'vector':vector, 'point':point}),
or by passing a sequence of 2 3D points (i.e. ((0.,0,0), (13,3,0)) ).
angle: is an angle in degrees
min_angle: minimum hinge angle in degrees
max_angle: maximum hinge angle in degrees
"""
        self.min_angle = 0.0  # minimum hinge angle
        self.max_angle = 360. # maximum hinge angle
        FTMotion_RotationAboutAxis.__init__(self, axis=axis, points=points,
                                            angle=angle, name=name, tolerance=tolerance)
        
        self.configure(min_angle=min_angle, max_angle=max_angle)        
        self.widgetsDescr['angle']['min'] = min_angle
        self.widgetsDescr['angle']['max'] = max_angle


    def configure(self, axis=None, points=None, angle=None, name='hinge',
                  min_angle=None, max_angle=None,type=type,
                  percent=None, tolerance=None, **kw):
        """configure the operator"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw )
            
        if min_angle != None:
            #if abs(min_angle)>360.: min_angle = (abs(min_angle)%360.)
            self.min_angle = min_angle
        if max_angle != None:
            #if abs(max_angle)>360.: max_angle = (abs(max_angle)%360.)
            self.max_angle = max_angle
        assert self.min_angle <= self.max_angle, "min %f should <= max %f"%(
            self.min_angle, self.max_angle)       
        
        kw = {}
        if axis is not None: kw['axis']=axis
        if points is not None: kw['points']=points
        if name is not None: kw['name']=name
        #if percent is not None:kw['percent']=percent
        if tolerance is not None:kw['tolerance']=tolerance        
        updateFLag = False
        if len(kw):
            apply( FTMotion_RotationAboutAxis.configure, (self,), kw )
            updateFlag = True

        angleRange = (self.max_angle-self.min_angle)*(self.tolerance+1.)
        if percent is not None:
            self.angle = percent * angleRange + self.min_angle

        if angle != None: # 'angle' overwrites the 'percent'
            angleRange = (self.max_angle-self.min_angle)*(self.tolerance+1.)
            if angle >= self.min_angle and angle <= self.max_angle:
                self.angle = angle
                updateFlag = True
            else:
                print "Waring  : out-of-range angle ", angle, "specified."
                print "Valid Angle Range:", self.min_angle, self.max_angle
                #print "with", self.tolerance * 100 , "% tolerance"
                 
        if updateFlag:
            #print "hinge angle:", self.angle, self.min_angle,self.max_angle 
            self.updateTransformation()
            if self.node: self.node().newMotion = True 
                

    def randomize(self, angle=False, percent =True):
        import random as r
        if angle or percent:
            t=self.tolerance
            self.percent = r.random()*((1+2*t)-t)
            self.angle = self.percent * (self.max_angle-self.min_angle)\
                                     +self.min_angle

        self.updateTransformation()
        if self.node: self.node().newMotion = True 
        
        
    def getCurrentSetting(self):
        descr = FTMotion_RotationAboutAxis.getCurrentSetting(self)
        myDescr = {'min_angle':self.min_angle, 'max_angle':self.max_angle,
                   }
        myDescr.update(descr)
        return myDescr


    def getParam(self):
        """ get GA related parameters .. returns two lists.
list of parameter names and list of dictionaries
"""
        t=self.tolerance
        validParamName =[]
        validParam = []
##         validParamName.append('angle')
##         angleRange = self.max_angle - self.min_angle
##         validParam.append({'type': 'continuous', 'dataType':'float',
##                            'min': self.min_angle - t * angleRange , 
##                            'max': self.max_angle + t * angleRange ,
##                            })

        validParamName.append('percent')
        angleRange = self.max_angle - self.min_angle
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min': 0.0, 'max': 1.0, 
                           })

        
        return validParamName, validParam



class FTMotion_DiscreteRotAboutPoint(FTMotion_RotationAboutAxis):  
    """ Defines a rotation about an arbitrary point (self.point), with discrete
rotation matrices ( 54000 rotation matrices)
"""
    # class variable, shared by all objects
    from os import path
    from mglutil.util.packageFilePath import findFilePath
    DIR= path.split( findFilePath('julie12019854k.rot',
              'mglutil.math') )[0]
    dataFile=path.join(DIR, "julie12019854k.rot")

    # rotMatList  : a list of rotation matrix
    rotMatList  = open(dataFile,'r').readlines()
        
    
    def __init__(self, point=None, index=None, 
                 name='discrete rotation about a point',
                 percent=None, tolerance=None):
        """Constructor
The parameters are
point       : the motion is a rotation about this point
index       : index within the rotMatList (scaled from 0.0 to 1.0)
"""
        self.rotMatIdx = -1
        self.vList=[]
        self.point=[0.0, 0.0, 0.0]
        FTMotion.__init__(self)
#        self.type = 'FTMotion_RotationAboutPoint'
        self.configure(name=name,point=point,
                       percent=percent, tolerance=tolerance,
                       index=index)

        self.widgetsDescr['index'] = {
            'widget':'Thumbwheel', 'callback':FTMotion.callConfigure_cb }
        self.widgetsDescr['point'] = {
        'widget':'Dial', 'callback':FTMotion.callConfigure_cb }
        
        
    def configure(self, name='rotation about a point',
                  point=None, index=None,
                  percent=None, tolerance=None, **kw):
        """configure the motion"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        FTMotion_RotationAboutAxis.configure(self, axis=None, points=None,
                  angle=0.0, name=name, percent=None, tolerance=None)
        update = False
        if point != None:
            self.point = point
            update=True
        if index is not None:
            self.rotMatIdx = index * len(self.rotMatList)
            update=True
        if update:
            self.updateTransformation()
            if self.node: self.node().newMotion = True 


    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'index':self.rotMatIdx, 'type':self.type,
                   'point':self.point}
        myDescr.update(descr)
        return myDescr
 

    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""
        if self.rotMatList is None or self.rotMatIdx==-1:
            self.transform = numpy.identity(4, 'f' )
            return
        self.transform = numpy.identity(4, 'f' )        
        
        data = self.rotMatList[self.rotMatIdx]
        data = data.split(' ')
        rot=[]
        for i in range(len(data)):
            if data[i] !='' and data[i]!='\n':
                rot.append(eval(data[i]))
        if len(rot) is not 9:
            raise ValueError("Error in reading rotation data file")

        # transform = T_1 * R * T
        rot=numpy.reshape(numpy.array(rot,'f'),(3,3))
        T=numpy.identity( 4, 'f' )
        R=numpy.identity( 4, 'f' )
        R[:3,:3] = rot
        T[3,:3]=self.point         # translation 4x4
        T_1 = numpy.identity( 4, 'f' ) # transposed 4x4 translation
        T_1[3,:3] = (-1*numpy.array(self.point)).tolist()        
        
        res = numpy.dot(T_1, R)
        self.transform = numpy.dot(res, T)
       

    def randomize(self):
        """ generate a random rotation
"""
        import random as r
        self.rotMatIdx = int(r.random()* len(self.rotMatList))
        self.updateTransformation()
        if self.node: self.node().newMotion = True 
        

from math import sqrt, sin, cos, pi
TWOPI = pi*2.0

class FTMotion_RotationAboutPointQuat(FTMotion_RotationAboutAxis):
    """
    Defines a rotation about an arbitrary point (self.point)
    Using Quaternion to represent the rotation 
    quternion = z,y,z,w NOT vector axis
    """
   
    def __init__(self, point=None, quat=None,
                 name='rotation about a point',
                 percent=None, tolerance=None):
        """Constructor
        The parameters are
        point  : the motion is a rotation about this point
        quat : x,y,z,w
        """
        self.point=[0.0, 0.0, 0.0]
        
        # format:  x, y, z, w
        self.quat = [0.0, 0.0, 0.0, 1.0] # identity
        
        FTMotion.__init__(self)
        self.configure(name=name, point=point, quat=quat,
                       percent=percent, tolerance=tolerance )        

        
    def configure(self, name='rotation about a point (quat)',
                  qx=None, qy=None, qz=None, qw=None, 
                  point=None, quat=None,
                  percent=None, tolerance=None, update=True, **kw):
        """configure the motion"""

        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        FTMotion.configure(self, name=name, percent=None, tolerance=None)
        update = False

        if point != None:
            self.point = point
            update=True

        if quat is not None:
            assert len(quat)==4
            self.quat = quat
            update = True

        if update:
            #print '** rotate about point', self.point, "ang =",self.angle
            self.updateTransformation()

        if self.node: self.node().newMotion = True 


    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'quat':self.quat, 'point':self.point, 'type':self.type}
        myDescr.update(descr)
        return myDescr
 


    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""
        if self.quat is None or self.point==None:### or self.active == False:
            self.transform = numpy.identity(4, 'f' )
            return

        x,y,z = self.point
        trans = numpy.identity(4)
        trans[:3, 3] = (x,y,z)
        
        trans1 = numpy.identity(4)

        trans1[:3, 3] = (-x,-y,-z)

        x, y, z, w = self.quat
        tx  = x+x; ty  = y+y; tz  = z+z

        twx = w*tx
        omtxx = 1. - x*tx
        txy = y*tx
        txz = z*tx

        twy = w*ty
        tyy = y*ty
        tyz = z*ty

        twz = w*tz
        tzz = z*tz

        r11 = 1. - tyy - tzz
        r12 =      txy - twz
        r13 =      txz + twy
        r21 =      txy + twz
        r22 = omtxx    - tzz
        r23 =      tyz - twx
        r31 =      txz - twy
        r32 =      tyz + twx
        r33 = omtxx    - tyy

        rot = numpy.array( ( (r11, r12, r13, 0.0), (r21, r22, r23, 0.0),
                             (r31, r32, r33, 0.0), (0.,0., 0., 1.)), 'f' )

        # compute T*R*T-1
        m1 = numpy.dot(rot, trans1)
        m2 = numpy.dot(trans, m1)
        self.transform = m2.transpose()
        
        
    def randomize(self):
        """
        generate a random motion 
        """
        t1 = uniform(0., TWOPI)
        x0 = uniform(0., 1.)
        r1 = sqrt( 1. - x0 )
        x = sin( t1 ) * r1
        y = cos( t1 ) * r1
        t2 = uniform(0., TWOPI)
        r2 = sqrt( x0 )
        z = sin( t2 ) * r2
        w = cos( t2 ) * r2
        self.configure( quat = [x, y, z, w])


class FTMotion_RotationAboutPoint(FTMotion_RotationAboutAxis):
    """ Defines a rotation about an arbitrary point (self.point)
Using Quaternion
quternion = [vector[0], vector[1], vector[2], angle]
"""
   
    def __init__(self, point=None, angle=None, vector=None,
                 name='rotation about a point',
                 percent=None, tolerance=None):
        """Constructor
The parameters are
point  : the motion is a rotation about this point
vector : the vector to rotate about
angle  : the angle to rotate
quaternion is [vector[0], vector[1],vector[2],angle]

"""
        self.point=[0.0, 0.0, 0.0]
        
        # format:  [vx , vy , vz , angle]
        self.quat =[1.0, 0.0, 0.0, 0.0] # rotate 0.0 degree along X axis
        
        self.angle=0.0
        FTMotion.__init__(self)
        self.configure(name=name,point=point,angle=angle,vector=vector,
                       percent=percent, tolerance=tolerance )        

        
    def configure(self, angle=None, name='rotation about a point',
                  point=None, vector=None,x=None, y=None,z=None,
                  percent=None, tolerance=None, **kw):
        """configure the motion"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        FTMotion.configure(self, name=name, percent=None, tolerance=None)
        update = False
        if point != None:
            self.point = point
            update=True
        if vector is not None:
            self.vector=vector
            self.quat[:3]=vector
            update=True
        if x is not None and y is not None and z is not None:
            # [x,y,z] overwrites the vector
            # input x,y,z in range [0.0, 1.0]
            # however to cover the space, x,y should be in [-1, 1]
            # z in [0, 1], angle in [0, 360) degrees
            assert x>=0.0 and x<=1.0
            assert y>=0.0 and y<=1.0
            assert z>=0.0 and z<=1.0
            x=x*2.0 - 1.0
            y=y*2.0 - 1.0
            self.vector=[x,y,z]
            self.quat[:3]=self.vector
            update=True
        if angle is not None:
            self.angle=angle
            self.quat[3]=angle
            update=True

        if percent is not None:
            #print "percent=", percent
            assert percent >=0.0 and percent <=1.0
            self.percent=percent
            self.angle=self.percent * 360.0
            self.quat[3]=self.angle
            update=True

        if update:
            #print '** rotate about point', self.point, "ang =",self.angle
            self.updateTransformation()
            if self.node: self.node().newMotion = True 


    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'vector':self.quat[:3], 'angle':self.quat[3],
                   'type':self.type, 'point':self.point}
        myDescr.update(descr)
        return myDescr
 

    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""
        if self.quat is None or self.point==None:
            self.transform = numpy.identity(4, 'f' )
            return

        from mglutil.math.transformation import Transformation
        R = Transformation(quaternion=self.quat)
        T=Transformation(trans=self.point)
        transform = T * R * T.inverse()
        self.transform = transform.getMatrix(transpose=1)
        
        
    def getParam(self):
        """ returns the GA related parameters
"""
        validParamName =[]
        validParam = []
        validParamName.append('x')
        validParam.append({'type': 'continuous','dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        validParamName.append('y')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        validParamName.append('z') 
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        validParamName.append('percent')  
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian',
                           #'mutator': 'uniform', 
                           'min': 0.0, 'max':1.0})
        return validParamName, validParam
        

    def randomize(self):
        """ generate a random motion 
"""
        import random as r
        x=r.random()           # [0,1]
        y=r.random()           # [0,1]
        z=r.random()           # [0,1]
        ang = r.random()*360       # [0,360]
        self.configure(angle=ang, x=x,y=y,z=z)



class FTMotion_ConeRotation(FTMotion_RotationAboutPoint):
    """ Defines a rotation about an arbitrary point (self.point) and restrained
cone angle.
The point (root point) is restricted within a 3D box, rotation axis is defined from two points, the root point and moving point. The angle between rotation axis and motion direction (dVector) must be within a predefined angle(alpha).
The moving point is defined as a point on the cone bottom. The position can be derived from an angle (beta).

delta is the angle of rotation about the rotation axis, value ranges from
[-maxDelta, +maxDelta]

fixme.. need more explicit explaination

"""
    def __init__(self, point=None,vector=None,alpha=None,beta=None, delta=None,
                 maxDelta = 180.0, 
                 maxAlpha = 90., name='point rotation with restriction'):
        """ Constructor
The parameters are
alpha, beta, delta: see module document
alpha  : the maximum alpha angle between motion direction and rotation axis
vector : the motion direction (unit vector !)
point  : the point where unit vector begins

"""
        self.point=[0.0, 0.0, 0.0]
        self.vector= [1.0, 0.0, 0.0]

        # format:  [vx , vy , vz , angle]
        self.quat =[1.0, 0.0, 0.0, 0.0] # rotate 0.0 degree along X axis
        FTMotion.__init__(self)
        self.maxAlpha = 0.
        self.maxDelta = 0.
        self.alpha = 0.0
        self.beta  = 0.0
        self.delta = 0.0
        self.alpha_angle=0.0 # alpha angle
        self.beta_angle=0.0 # beta angle
        self.delta_angle=0.0 # delta angle
        
        self.hasFTNode = False
        self.points = [] # two points that definds the axis 
       # FTMotion_RotationAboutPoint.__init__(self, name=name, point=point)
        self.configure(name=name,point=point,alpha = alpha, beta = beta,
                       delta = delta,vector=vector,maxAlpha = maxAlpha,
                       maxDelta=maxDelta)
        return
    
        
    def configure(self, name=None,
                  alpha=None,beta=None,
                  delta=None,maxDelta=None,
                  point=None, vector=None, maxAlpha=None,
                  points = None, **kw
                  ):
        """configure the motion

Note: If any FTNode associated with this motion, and the FTNode
has molecularFragment, the vector will be overwritten by the
shortest axises of the convolving ellipsoid.
"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        update=False
        if points is not None:
            self.points=points
            p1=self.points[0]
            p2=self.points[1]
            self.vector= [p2[0] - p1[0], p2[1] - p1[1],p2[2] - p1[2] ]
            self.point = self.points[0]
            update= True
        
        if name is not None: self.name = name
        if point is not None:            
            self.point = point
            update=True

        # the ellipsoid axis overwrites the vector
        # the center of molecularFragment overwrites the point        
        if hasattr(self, 'node'):
            if self.node and self.hasFTNode==False : # do it only once
                if self.node().molecularFragment != None:
                    self.hasFTNode=True
                    self.point, self.vector = self._findEllipsoidAxis()
                    update=True
                    
        if vector is not None and self.hasFTNode==False:            
            self.vector = vector
            update=True
        if alpha is not None:
            self.alpha=alpha
            self.alpha_angle = self.alpha * self.maxAlpha
            update=True
        if delta is not None:
            self.delta=delta
            self.delta_angle = self.delta * self.maxDelta
            update=True                
        if beta is not None:
            self.beta=beta
            self.beta_angle = beta * 360.0
            update=True

        if maxAlpha is not None:
            self.maxAlpha = maxAlpha
            self.alpha_angle = self.alpha * self.maxAlpha
            if self.alpha_angle > maxAlpha:
                self.alpha_angle = maxAlpha
                update= True
        if maxDelta is not None:
            self.maxDelta = maxDelta
            self.delta_angle = self.delta  * self.maxDelta
            if self.delta_angle  > maxDelta:
                self.delta_angle = maxDelta
                update= True

        if update:
            self.updateTransformation()
            if hasattr(self, 'node'):
                if self.node:
                    self.node().newMotion = True 
        return
    

    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform
Cone motion is essentially a rotation about a point, with restricted choice of
vector. this updateTransformation computes the vector, set it as quaternion,
and updates the transformation matrix by calling
FTMotion_RotationAboutPoint.updateTransformation(self)
"""
        alpha = self.alpha_angle
        beta  = self.beta_angle
        delta = self.delta_angle
        vector_u = getOthogonalVecter(numpy.array(self.vector))
        x1,y1,z1 = self.vector
        x2,y2,z2 = vector_u
        p1=numpy.array([0,0,0,1],'f')
        p2=numpy.array([0,0,0,1],'f')
        p3=numpy.array([0,0,0,1],'f')
        p1[:3] = self.point
        p2[:3] = [p1[0] + x1, p1[1] + y1, p1[2] + z1 ]
        p3[:3] = [p1[0] + x2, p1[1] + y2, p1[2] + z2 ]

        transform1 = rotax(p1[:3], p3[:3], alpha*degtorad, transpose=1)
        transform2 = rotax(p1[:3], p2[:3], beta*degtorad, transpose=1)

        tmp1 =numpy.dot(p2, transform1).astype('f')
        p4 =numpy.dot(tmp1, transform2).astype('f')[:3]

##         print 'u:',vector_u
##         print alpha, beta, delta
##         print "P1:", p1  
##         print "P2:", p2
##         print "P3:", p3
##         print "P4:", p4

        transform3 = rotax(p1[:3], p4, delta*degtorad, transpose=1)
        self.transform = transform3
        return
        
##         x,y,z = self.vector
##         l = sqrt(x*x + y*y + z*z)
##         ang1 = degrees( asin(y/l) )
##         m= (l  * cos(radians(ang1)) )
##         ang2 = degrees( acos(x/ m ))
##         L = l / cos(radians(alpha))
##         newX = L * cos( radians(alpha + ang1)) * cos( radians(ang2))
##         newY = L * sin( radians(alpha + ang1))
##         newZ = L * cos( radians(alpha + ang1)) * sin( radians(ang2))
##         point2 = [newX, newY, newZ, 1]
##         p1 = self.point
##         p2 = [p1[0] + x, p1[1] + y, p1[2] + z ]
##         transform1 = rotax(p1, p2, beta*degtorad, transpose=1)
##         point3 =numpy.dot(point2, transform1).astype('f')[:3]
##         point3=point3.tolist()
##         matrix2=rotax(p1, point3, self.delta_angle * degtorad, transpose=0)
##         self.transform = matrix2
##         return
 
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'vector':self.vector, 'point':self.point,
                   'maxAlpha':self.maxAlpha, 'maxDelta':self.maxDelta, 
                   'alpha_angle':self.alpha_angle,
                   'beta_angle':self.beta_angle,'delta_angle':self.delta_angle,
                   'type':self.type}
        myDescr.update(descr)
        return myDescr


    def getParam(self):
        """ returns the GA related parameters
"""
        validParamName =[]
        validParam = []
        validParamName.append('alpha')  
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min': 0.0, 'max': 1.0 })
        validParamName.append('beta')  
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min': 0.0, 'max': 1.0 })
        validParamName.append('delta')  
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min': -1, 'max': 1.0 })

        return validParamName, validParam

    def randomize(self):
        """ generate a random motion """
        import random as r
        alpha = r.random()
        beta  = r.random()
        delta = r.random() * 2 - 1.0  # between [-1, 1]
        self.configure(alpha=alpha, beta=beta, delta=delta)        
        if self.node: self.node().newMotion = True
        return
    

    def _findEllipsoidAxis(self, molecularFragment=None):
        """Find the ellipsoid that covers the molecularFragment and returns
the vector of cone motion (the shortest axis of the ellipsoid approximation

when molecularFragment is None, check the self.node().molecularFragment
otherwise, check the ellipsoid around molecularFragment (AtomSet)

NOTE: This should be called only once."""
        #from geomutils import geomutilslib
        from geomutils import efitlib
        if molecularFragment is None:
            frag= self.node().molecularFragment
        else:
            frag=molecularFragment

        if isinstance(frag, TreeNodeSet):
            atoms = frag.findType(Atom)
        else:
            atoms = frag.getAtoms()

        # NOTICE: after hinge angle applied.. coords might be changed
        # and thus the ellipsoid axis etc is changed
        coords = atoms.coords 
        ellipse = efitlib.ellipsoid()
        ellipseInfo = efitlib.efit_info()
        cov_scale = 1.75
        ell_scale = 1.0

        #print 'you can see me only once'
        coords = [list(x) for x in coords]
        #if isinstance(coords[0], numpy.ArrayType):
        #    tmp=[]
        #    for c in coords:
        #        tmp.append(c.tolist())
        #    coords=tmp

        status = efitlib.fitEllipse(coords, ell_scale, cov_scale,
                                         ellipseInfo, ellipse)
        if status!=0:
            print "***********************************"
            print "***  Error in fitting ellipise..***"
            print "***********************************"
            return [[1,0,0]] # returns X axis
        
        # see FTShapes.py for more about how to get center/size/axises..

        size = ellipse.getAxis().astype('f').tolist()
        shortest=size.index(min(size)) # index of shortest axis
        orient = ellipse.getOrientation()
        center = ellipse.getPosition()        
        axis = orient.tolist()
        tmp={}
        tmp[size[0]] = axis[0]
        tmp[size[1]] = axis[1]
        tmp[size[2]] = axis[2]

        keys= tmp.keys()
        keys.sort()
        # sorted by length(size) of axis
        axis = [tmp[keys[0]], tmp[keys[1]], tmp[keys[2]]]
        return center.tolist(), axis[0] # shortest axis
    
    def _getConeApex(self):
        """returns the apex(top) of cone """
        atomSet = self.node().molecularFragment
        coords=numpy.array(atomSet.coords)
        x=coords[:,0]
        y=coords[:,1]
        z=coords[:,2]
        centerX=numpy.add.reduce(x)
        centerY=numpy.add.reduce(y)
        centerZ=numpy.add.reduce(z)
        return [centerX, centerY, centerZ]

#FTMotion_Pertb = FTMotion_ConeRotation
    
class FTMotion_Translation(FTMotion):
    """ Defines motion type: translation
"""
    def __init__(self, axis=None, points=None, magnitude=None, 
                 name='translation', percent=None, tolerance=None, \
                 beginPoint=None, endPoint=None):
        """Constructor
The parameters are an axis which can be specified either using a point in a
vector passed as a dictionnary (i.e. axis={'vector':vector, 'point':point}),
or by passing a sequence of 2 3D points (i.e. ((0.,0,0), (13,3,0)) ).
magnitude: the magnitude of translation along the axis
beginPoint, endPoint: beginning and ending points of the translation

""" 
        self.point1 = (0.,0.,0.)    # first point defining translation axis
        self.point2 = (1.,0.,0.)    # second point defining translation axis
        self.magnitude = None       # translation magnitude
        self.transform = numpy.identity(4,'f') #4x4 transformation matrix

        FTMotion.__init__(self) 
        FTMotion_Translation.configure(self,axis=axis, points=points,
                       magnitude=magnitude,
                       name=name, percent=percent, tolerance=tolerance,
                       beginPoint=beginPoint, endPoint=endPoint)
        self.widgetsDescr['translation'] = {
            'widget':'Thumbwheel', 'callback':FTMotion.callConfigure_cb}

        
    def updateTransformation(self):
        """recompute the transformation"""
        
        if self.magnitude is None:            
            self.transform=numpy.identity(4,'f')
            return
        
        p1=self.point1
        p2=self.point2
        v=(p2[0]-p1[0],p2[1]-p1[1],p2[2]-p1[2])
        s=numpy.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])
        
        if s<0.00001:   
            #raise ValueError("The two points given are too close")
            self.transform=numpy.identity(4,'f')
        else:
            t = numpy.identity( 4, 'f' )
            t[3][0] = v[0]/s*self.magnitude * self.percent
            t[3][1] = v[1]/s*self.magnitude * self.percent
            t[3][2] = v[2]/s*self.magnitude * self.percent
            self.transform = t
        return
        
        
        
    def getMatrix(self, transpose=False):
        """return a 4x4 transformation matrix corresponding to the current
translation.
If transpose is True, the matrix is a standard 4x4 matrix with the translation
in the last column, else the matrix is transposed.

NOTES: Here the 4x4 transformation matrix is a numpy Array. ( not a list !)
"""
        if not transpose:
            return self.transform
        else:
            return numpy.array( numpy.transpose(self.transform), 'f')
        
        
    def configure(self, axis=None, points=None,
                  magnitude=None, name=None,
                  percent=None, tolerance=None,
                  beginPoint=None, endPoint=None, **kw):
        """reset the vector and translation magnitude"""
        
        if len(kw):
            apply( FTMotion.configure, (self,), kw )
            if kw.has_key("point1") and kw.has_key("point2"):
                if beginPoint is None and endPoint is None:
                    beginPoint=kw['point1']
                    endPoint=kw['point2']
                else:
                    print "Both beginPoint/endPoint and point1/point2 are specified"
                    raise ValueError
            
            
        FTMotion.configure(self,name=name,
                           percent=percent,tolerance=tolerance)  
        point1 = point2 = None
        update=False
        if points != None:
            assert len(points)==2 and len(points[0])==3 and len(points[1])==3
            point1 = points[0]
            point2 = points[1]
            update=True

        if axis is not None:
            assert isinstance(axis, types.DictType)
            point1 = axis['point']
            v = axis['vector']
            point2 = [point1[0]+v[0], point1[1]+v[1], point1[2]+v[2]]
            update=True
            
        if point1 and point2:
            self.point1 = point1   # defines a translation axis using 2 points
            self.point2 = point2
            update=True
        if magnitude and magnitude != self.magnitude:
            self.magnitude = magnitude
            update=True

        if beginPoint!=None and endPoint!=None:
            self.point1 = beginPoint
            self.point2 = endPoint
            self.percent=1.0
            self.magnitude =dist(self.point1, self.point2)
            update=True
            
        if update:
            self.updateTransformation()
            if self.node: self.node().newMotion = True 
        return
    
        
    def randomize(self,axis=False, points=False, magnitude=False,
                  percent=True):
        import random as r
        if axis or points:
            # generate random number [-1.0, 1.0)
            self.points[0]=[r.random()*2.0-1.0,
                            r.random()*2.0-1.0,
                            r.random()*2.0-1.0]
            self.points[1]=[r.random()*2.0-1.0,
                            r.random()*2.0-1.0,
                            r.random()*2.0-1.0]
        if magnitude or percent :
            t=self.tolerance
            self.percent = r.random()*((1+2*t)-t)
            # generate random number [-t, 1.0+t)
            #self.magnitude = self.percent * 1.0
        
        self.updateTransformation()
        if self.node: self.node().newMotion = True 


    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'point1':self.point1, 'point2':self.point2,
                   'magnitude':self.magnitude}
        myDescr.update(descr)
        return myDescr



class FTMotion_BoxTranslation(FTMotion_Translation):
    """ Defines a translation within a given box.
"""
    def __init__(self,  name='translation within a box',
                 boxDim=None, point=None, 
                 percent=None, tolerance=None):
        """
        Constructor
        The motion object defines a translation vector V with
          -dim[0]/2 <= vx <= dim[0]/2
          -dim[1]/2 <= vy <= dim[1]/2
          -dim[z]/2 <= vz <= dim[2]/2

        The parameters are:
            boxDim: (dim[0]. dim[1], dim[2]) the length of box edges. (aligned with X,Y,Z axis)
            point : x, y, z in box centered at (0,0,0) 

        FIXME: percent and tolerance is not used, for now
        """
        
        # boxDim defines the (Height, width, length) of the box, positive float
        self.boxDim= None # [1.0, 1.0, 1.0]
        # point defines a point in box coordinates (take gridCenter as origin)
        self.point = [0.0, 0.0, 0.0]
        
        FTMotion_Translation.__init__(self, name=name,
                                      percent=percent, tolerance=tolerance)
        
        # move the root of ligand to center of the box
        self.configure(boxDim=boxDim, point=point)
        self.cutPoints = [1,2,3]

        
    def configure(self, name=None, boxDim=None, point=None, 
                  percent=None, tolerance=None, update=False, **kw):
        """
        configure the motion
        point_X, point_Y and point_Z are percentage (0.0, 1.0) of dimension X,Y,Z
        """
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        if name != None:
            self.name = name

        update = update

        if boxDim is not None:
            if self.boxDim is not None:
                p = self.point
                p[0] *= boxDim[0]/self.boxDim[0]
                p[1] *= boxDim[1]/self.boxDim[1]
                p[2] *= boxDim[2]/self.boxDim[2]

            self.boxDim=boxDim
            update=True

        # set the translation to be from the grid center to a point in the box
        if point is not None:
            for i in range(3):
                # make sure the point is inside the box
                if self.point[i] > (self.boxDim[i] / 2.0) or \
                       self.point[i] < (-self.boxDim[i] / 2.0):
                    print "Error: point",  self.point, self.boxDim[i] / 2.0
                    raise
            self.point = list(point)
            update=True

        if update:
            self.updateTransformation()
            if self.node: self.node().newMotion = True 


    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""        
        self.transform = numpy.identity( 4, 'f')
        #if self.active == False:
        self.transform[3,:3] = self.point                
        return

    
    def randomize(self):
        """
        generate a random translation within the given box
        """
        dx, dy, dz = self.boxDim
        x = uniform(0, dx) - 0.5*dx 
        y = uniform(0, dy) - 0.5*dy 
        z = uniform(0, dz) - 0.5*dz 
        self.configure(point = (x,y,z))

        
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'boxDim':self.boxDim, 'point':self.point,
                   'type':self.type}
        myDescr.update(descr)
        return myDescr


class FTMotion_BoxTranslation1(FTMotion_Translation):
    """
    Defines a translation within a given box.
"""
    def __init__(self,  boxDim, toOriginTranslation = [0,0,0],
                 name='translation within a box from Origin'):
#                 percent=None, tolerance=None):
        """
        Constructor
        The motion object defines a translation vector V with
        from the box origin  (aligned with X,Y,Z axis)

        The parameters are:
            boxDim: (sx, sy,sz) the length of box edges
            toOriginTranslation : (x, y, z) a static translation vector to move
                                  an object to the origin of the box
        """
        self.vector = [0,0,0]
        # boxDim defines the (Height, width, length) of the box, positive float
        self.boxDim = boxDim
        # point defines a point in box coordinates (take gridCenter as origin)
        self.toOriginTranslation = toOriginTranslation
        FTMotion_Translation.__init__(self, name=name)
#                                      percent=percent, tolerance=tolerance)
        
        # move the root of ligand to center of the box
        self.configure(boxDim=boxDim, toOriginTranslation=toOriginTranslation)

        
    def configure(self, name=None, boxDim=None, toOriginTranslation=None,
                  vector=None, tolerance=None, update=False, **kw):
        """
        configure the motion
        point_X, point_Y and point_Z are percentage (0.0, 1.0) of dimension X,Y,Z
        """
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        if name != None:
            self.name = name

        update = update

        if toOriginTranslation is not None:
            assert len(toOriginTranslation)==3
            self.toOriginTranslation = toOriginTranslation
            update=True

        if boxDim is not None:
            self.boxDim=boxDim
            update=True

        # set the translation to be from the grid center to a point in the box
        if vector is not None:
            for i in range(3):
                # make sure the point is inside the box
                if vector[i]>self.boxDim[i] or vector[i]<0.0:
                    print "Error: vector outside box",  vector, self.boxDim
                    raise
            self.vector = list(vector)
            update=True

        if update:
            self.updateTransformation()
            if self.node: self.node().newMotion = True 


    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""        
        self.transform = numpy.identity( 4, 'f')
        ox, oy, oz = self.toOriginTranslation
        vx, vy, vz = self.vector
        self.transform[3,0] = ox+vx
        self.transform[3,1] = oy+vy
        self.transform[3,2] = oz+vz                
        return

    
    def randomize(self):
        """
        generate a random translation within the given box
        """
        dx, dy, dz = self.boxDim
        x = uniform(0, dx)
        y = uniform(0, dy)
        z = uniform(0, dz)
        self.configure(vector = (x,y,z))

        
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'boxDim':self.boxDim,
                   'toOriginTranslation':self.toOriginTranslation,
                   'vector':self.vector,
                   'type':self.type}
        myDescr.update(descr)
        return myDescr

        

class FTMotion_SegmentTranslation(FTMotion_Translation):
    """Defines the class for parametric traslation motion of the FT
The translation can occur from 
Defines a hinge rotation about an arbitrary axis.
The axis can either be specified using the point and a vector or by providing
two points. The motion is limited to the mini and maxi angles. 
"""

    def __init__(self, axis=None, points=None, name='segment_translation',
                    magnitude=None, 
                    max_length=0.0, percent=0.0, tolerance=0.05):
        """Constructor
The parameters are an axis which can be specified either using a point in a
vector passed as a dictionnary (i.e. axis={'vector':vector, 'point':point}),
or by passing a sequence of 2 3D points (i.e. ((0.,0,0), (13,3,0)) ).
max_length: the maximum length of translation along the axis
percent:   percentage of the segment, float value from 0.0 to 100.0 (percentage)
Noticed that the magnitude of translation is stored in self.magnitude
    and self.magnitude = max_length * percent
    setting the magnitude can ONLY be done by chaning max_length and/or percent
    setting the magnitude by  magnitude=1.0, for example, will NOT work
    (the magnitude parameter is used here only because it's part of parameter 
    list in parent class: FTMotion_Translation)
"""
        self.max_length=0.0
        self.percent=0.0
        
        FTMotion_Translation.__init__(self, axis=axis, points=points, 
                name=name, percent=percent, tolerance=tolerance)        
        self.configure(max_length=max_length)        


    def configure(self, axis=None, points=None, name='segment_translation',
                  percent=None, tolerance=None, max_length=None, **kw):
        """reset the parameters"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)
        
        if max_length !=None:
            self.max_length = max_length 
        
        kw = {}
        if axis is not None: kw['axis']=axis
        if points is not None: kw['points']=points
        if name is not None: kw['name']=name
        if percent is not None: kw['percent']=percent
        if tolerance is not None:kw['tolerance']=tolerance
        if len(kw):
            apply( FTMotion_Translation.configure, (self,), kw )
            self.magnitude=self.max_length * self.percent /100.0

        #self.magnitude=self.percent*self.max_length
        self.magnitude= self.max_length  # see updateTransformation()
        self.updateTransformation()
        if self.node: self.node().newMotion = True 
        

    def randomize(self,axis=False, points=False, magnitude=False,
                  percent=True):
        # NOTE: self.max_length can NOT be randomized.
        # call self.configure(max_length=n) to change it to be n
        import random as r
        if axis or points:
            self.points[0]=[r.random()*2.0-1.0,
                            r.random()*2.0-1.0,
                            r.random()*2.0-1.0]
            self.points[1]=[r.random()*2.0-1.0,
                            r.random()*2.0-1.0,
                            r.random()*2.0-1.0]
        if magnitude or percent :
            t=self.tolerance
            self.percent = r.random()*((1+2*t)-t)
            # generate random number [-t*100%, (1.0+t)*100%]
            self.magnitude = self.percent * self.max_length
        
        self.updateTransformation()
        if self.node: self.node().newMotion = True 

    
    def getCurrentSetting(self):
        descr = FTMotion_Translation.getCurrentSetting(self)
        myDescr = {'percent':self.percent}
        myDescr.update(descr)
        return myDescr


class FTMotion_Screw(FTMotion):
    """ Defines motion type: screw
FIXME:
     not fully implemented. randomize()
     
"""
    def __init__(self, axis=None, points=None, magnitude=0.0, name='screw', 
                 angle=0.0, max_angle=360.0, min_angle=0.0, mpc=0.0
                ):
        """Constructor
Two ways of specifing the screwing axis, either using a point in a vector passed
as a dictionnary (i.e. axis={'vector':vector, 'point':point}),
or by passing a sequence of 2 3D points (i.e. ((0.,0,0), (13,3,0)) ).
magnitude: the magnitude of translation along the axis 

mpc: (magnitude per cycle) 
    defines the translation magnitude along the axis per cycle of rotation
    
""" 
       
        #FTMotion.__init__(self)
        # rotation operator of Screwing
        self.r = FTMotion_Hinge(axis=axis, points=points, angle=angle,
                 name='hinge',min_angle=min_angle,max_angle=max_angle)
                 
        self.t = FTMotion_Translation(axis=axis, points=points, 
                 name='translation',magnitude=0.0)

        FTMotion.__init__(self)
        self.configure(mpc=mpc)
        self.widgetsDescr['angle'] = {
        'widget':'Dial', 'callback':FTMotion.callConfigure_cb }
        self.widgetsDescr['translation'] = {
            'widget':'Thumbwheel', 'callback':FTMotion.callConfigure_cb }
        
    
    def updateTransformation(self):
        """recompute the transformation"""
        t=self.t.getMatrix()
        vector=numpy.array(self.r.point2) - numpy.array(self.r.point1)
        #fixme: transform is wrong here... use rotax instead of Transformation
        transf = Transformation(
            trans=[t[0][3],t[1][3],t[2][3]],
            quaternion=[vector[0],vector[1],vector[2],self.r.angle])        

        self.transform = transf.getMatrix()
        
        
    def getMatrix(self, transpose=False):
        """return a 4x4 transformation matrix corresponding to the current
screwing motion.
If transpose is True, the matrix is a standard 4x4 matrix with the translation
in the last column, else the matrix is transposed.
NOTES: Here the 4x4 transformation matrix is a numpy Array. ( not a list !)
"""
        if not transpose:
            return self.transform
        else:
            return numpy.array( 
                        numpy.transpose(self.transform), 'f')
        
                
        
    def configure(self, axis=None, points=None, name='screw',  angle=None,
                  max_angle=None, min_angle=None, mpc=None, percent=None,
                  tolerance=None, **kw):
        """reset the parameters"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)
        if name:
            FTMotion.configure(self, name=name)
        
        self.r.configure(axis=axis, points=points, angle=angle, name='hinge',
                  min_angle=min_angle, max_angle=max_angle, percent=percent,
                  tolerance=tolerance)
        
        if mpc is not None:
            self.mpc = mpc
        magnitude = self.r.angle / 360.0 * self.mpc
        self.t.configure(axis=axis, points=points, magnitude=magnitude)

        self.updateTransformation()
        if self.node: self.node().newMotion = True 


    def getCurrentSetting(self):
        descr = FTMotion_Hinge.getCurrentSetting(self)
        myDescr = {'mpc':self.mpc}
        myDescr.update(descr)
        return myDescr
    

    def randomize(self,axis=False, points=False, magnitude=False,
                  percent=True):
        self.r.randomize(axis=axis, points=points, percent=percent)
        self.t.randomize(magnitude=magnitude, percent=percent)
        self.updateTransformation()
        if self.node: self.node().newMotion = True 



class FTMotion_Generic(FTMotion):
    """ Defines a generic transformation (with a given 4x4 transformation
matrix). 
"""
    def __init__(self, matrixList=None, indexList=None, percent=1.0,
                 name='generic transformation'):
        """Constructor
The parameters are a list of  4x4 transformation matrices and a positive float
number p.  The parameter p defines the percentage of the transformation.
if matrixList has only one matrix:
percent = 0.0 means no tranformation (identity)
percent = 1.0 means applying the 4x4 transformation matrix
when percent is between 0.0 and 1.0, e.g. 0.45, then 45% of rotation and
translation will be applied.
percent can go above 1.0

If matrixList has more than one matrix:
matrixList=[M1,  M2,  M3]     #Note: All M uses the same reference frame
indexList =[0.2, 0.5, 1.0]    #Note: assume the list sorted ascendingly
percent = 0.5 means apply M2
percent = 0.8 means apply M3
percent = 0.9 means apply M2 first, then apply 50% of M'.
                    M' is the transformation
                    from M2 to M3.   50% = (0.9-0.8) / (1.0-0.8)
                    M2 x M' = M3
                    -->   M'= M2.inverse x M3 
"""
        FTMotion.__init__(self)
        self.percent = 1.0
        self.matrixList = []    # a list of matrices for discrete conformations
        self.indexList  = []    # a list of indexes (percent) for each matrix
        self.transform = numpy.identity(4, 'f')
        self.configure(matrixList = matrixList, indexList=indexList,
                       percent = percent, name=name)
        self.widgetsDescr['percent'] = {
        'widget':'Dial', 'callback':FTMotion.callConfigure_cb
        }


    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""
        from mglutil.math.rotax import interpolate3DTransform
        self.transform = interpolate3DTransform(
            self.matrixList, self.indexList, \
                #  numpy.array(self.matrixList),\
                #  NUmeric.array(self.indexList), \
                  self.percent)
    
                                
    def getMatrix(self, transpose=False):
        """returna 4x4 transformation matrix corresponding to the current 
rotation. If transpose is True, the matrix is a standard 4x4 matrix with the 
translation in the last column, else the matrix is transposed.
NOTES: Here the 4x4 transformation matrix is a numpy Array. ( not a list !)

"""
        if not transpose:
            return self.transform
        
        else:
            return numpy.array( numpy.transpose(self.transform),'f')
        
        
    def configure(self, matrixList=None,indexList=None,name=None,
                  percent=None, tolerance=None, **kw):
        """reset the matrix and percentage
The matrixList can be
1)a list of 4x4 transform matrices, shape(n,4,4)
2)a single 4x4 transform matrix     shape(4,4) or shape(16,)
3)a long list of float, with every 16 floats making a 4x4 matrix, shape(16*n,)
4)a list of list, shape(n,16), with every 16 floats making a 4x4 matrix
n is the number of 4x4 matrices

"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)
        
        FTMotion.configure(self, name=name,percent=percent,tolerance=tolerance)
        update = False    # if True, the transform should be updated
        singleMat = False # if True, the matList is not a list of 4x4 matrices
                          # instead, the matList is a 4x4 matrix itself.
        if percent is not None:
            #self.percent = percent  #already configrued in FTMotion.configure
            update = True

        # the matrixList is always converted to shape (n,4,4), a list of 4x4
        # matrices before further operation.
        if matrixList is not None:
            from types import FloatType
            sh= numpy.array(matrixList).shape    
            dimension = len(sh)
            if dimension ==1:        # a list of float is given
                listLen = len(matrixList)
                if listLen%16!=0:
                    raise ValueError("Error. Expecting 16xN floating numbers.")
                # check how many matrices in the matrixList
                if sh ==(16,):
                    # a single 4x4 is given
                    matrixList=numpy.reshape(matrixList, (4,4))
                    matrixList = [matrixList]
                else:
                    num = listLen / 16
                    matList=[]
                    for i in range(num):
                        tmp=numpy.reshape(matrixList[num:num+16], (4,4))
                        matList.append(tmp)
                    matrixList = matList                  
                self.matrixList = matrixList
                update = True                
            elif dimension ==2:                
                if sh ==(4,4):# a single 4x4 is given                    
                    matrixList = [numpy.array(matrixList)]
                if sh[1] == 16:   # a n by 16 array is given
                    num = matrixList.shape[0]
                    matList=[]
                    for i in range(num):
                        tmp=numpy.reshape(matrixList[num:num+16], (4,4))
                        matList.append(tmp)
                    matrixList = matList                
                self.matrixList = matrixList
                update = True
            elif dimension ==3:
                self.matrixList = matrixList
                update = True

            # now (n,4,4) matrix list is constructed.
            # check if the matrix is in Fortran-style or in C style
            # Note: rotax() is used in FTMotions, so Fortran style is used
            if matrixList[0][3][0]==matrixList[0][3][0]==0.0:
                # C-style found..transpose them.
                for m in range(len(matrixList)):
                    matrixList[m]= numpy.transpose(matrixList[m])  
        
        if indexList is not None and len(indexList)!=0:
            self.indexList = indexList
            update = True

        if update:
            if len(self.matrixList)!=0 and  len(self.indexList)!=0 \
                      and  len(self.matrixList)==len(self.indexList) :
                self.updateTransformation()
                if self.node: self.node().newMotion = True
            
    
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        # build a long flat list here to be stored in XML
        matrixListLong =[]
        d0,d1,d2 = numpy.array(self.matrixList).shape
#       d0 = d[0]; d1 = d[1]; d2 = d[2];                                
        matList=self.matrixList
        for i in range(len(matList)):
            mat=matList[i]
            if mat.flags.contiguous: # 
                matrixListLong += mat.ravel().tolist()
            else:
                matrixListLong += numpy.array(mat).ravel().tolist()

        myDescr = {'matrixList':matrixListLong, # use one dimension list
                   'indexList':self.indexList,
                   'percent':self.percent}
        myDescr.update(descr)
        return myDescr


    def randomize(self,percent=True):
        """ randomize the generic motion.
percent: True => to generate a random percentage of generic motion.
tolerance: float number specifying how much the motion can go above 100%
           tolerance=0.05 means the motion can go between 0% ~ 105%
one of the typical calls is,
motion.randomize(tolerance=0.10)
"""    
        import random as r
        if percent :
            t=self.tolerance
            self.percent = r.random()*(1+2*t)-t
            self.updateTransformation()
            if self.node: self.node().newMotion = True 


    def getParam(self):
        """get the GA related parameters"""
        validParamName =[]
        validParam = []
        validParamName.append('percent')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'gaussian', 
                           'min':0.0, 'max':1.0})

        return validParamName, validParam

 

class FTMotionCombiner(FTMotion):
    """ Defines a combination of motion objects
"""
    def __init__(self, motionParamDictList=None,motionList=None,
                 name='combination of motion objects'):
        """Constructor
motionParamDictList : a list of dictionaries, (motion parameters)

"""
        FTMotion.__init__(self)
        self.motionList=[]
        self.motionParamDictList=[]
        self.transform = numpy.identity(4, 'f')
        self.configure(motionParamDictList=motionParamDictList, \
                       motionList=motionList, name=name)


    def updateTransformation(self):
        """recompute the new 4x4 transformation matrix, stored in
self.transform"""
        res = numpy.identity(4,'f')
        matList=self.motionList
        for i in range(len(matList)):
            mat=matList[i].getMatrix()
#            if mat==None:
#                print matList[i].name
            # the sequence of matrices was DOUBLE checked. March. 15th. 2004
            res=numpy.dot(res, mat)

        self.transform = res.tolist()

                                        
    def getMatrix(self, transpose=False):
        """returna 4x4 transformation matrix corresponding to the current 
rotation. If transpose is True, the matrix is a standard 4x4 matrix with the 
translation in the last column, else the matrix is transposed. 
"""
        import types
        
        if not transpose:
            return numpy.array(self.transform, 'f')
            #if isinstance(self.transform, numpy.ArrayType):
            #    #return self.transform.tolist()
            #    return self.transform
            #else:
            #    return numpy.array(self.transform, 'f')
        else:
            return numpy.array( numpy.transpose(self.transform),\
                                  'f')

    def motionOfType(self, type, module='FlexTree.FTMotions'):
        """ returns an FTMotion object with name = 'type' """
        module = __import__(module, globals(), locals(),[type])
        motion = getattr(module, type)
        if motion is None:
            return None
        else:
            return motion()

        
    def configure(self, motionParamDictList = None, motionList=None,
                  name=None, percent=None, tolerance=None, **kw):
        """reset the list of parameter dictionaries
"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)      

        FTMotion.configure(self, name=name,
                           percent=percent, tolerance=tolerance)
        update=False
        if motionList is not None:
            for m in motionList:
                assert isinstance(m, FTMotion)
            self.motionList = motionList
            self.motionParamDictList=[]
            for i in range(len(motionList)):
                self.motionParamDictList.append(\
                    motionList[i].getCurrentSetting())
            update=True

        if motionParamDictList is not None:
            self.parseMotionSettings(motionParamDictList)
            update=True

        if update:
            self.updateTransformation()
        if self.node:
            self.node().newMotion = True


    def parseMotionSettings(self, motionParamDictList):
        if len(motionParamDictList) == len(self.motionList):
            for i in range(len(self.motionList)):
                motion = self.motionList[i]
                config = motionParamDictList[i]
                del config['type'] # obsolete
                del self.motionParamDictList[i]['type']
                apply( motion.configure, (), config)
        else:
            self.motionParamDictList=motionParamDictList
            # reconstruct the motionList the combiner is configured.
            # motion in motionList can be changed by user (in Vision)
            self.motionList=[]
            for dict in motionParamDictList:
                module = dict.pop('module')
                motion=self.motionOfType(dict['type'], module=module)
                #print dict['type']
                if motion is None:
                    raise ValueError("Unknown motion found.") 
                del dict['type']
##                 if self.node:       # pointing to same node, if any.
##                     motion.node=self.node
                apply( motion.configure, (), dict)
                self.motionList.append(motion)
        return
    
    def updateMotionParamDictList(self):
        """ update the list of motion parameters (dict)"""
        self.motionParamDictList=[]
        for m in self.motionList:
            self.motionParamDictList.append(m.getCurrentSetting())
        return 
    
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        number= len(self.motionList)
        myDescr = {'numMotion': number}
#        for i in range(number):
#            myDescr['motion'+str(i)]=self.motionParamDictList[i]
#        myDescr = {'motionParamDictList':self.motionParamDictList}
        myDescr.update(descr)
        return myDescr
#        return self.motionParamDictList

    def getParam(self):
        """Get the GA related parameters"""
        validParamName =[]
        validParam = []
        for m in self.motionList:
            nameList, paramList = m.getParam()
            validParamName += nameList
            validParam += paramList
      
        return validParamName, validParam


    def randomize(self,rot=True, trans=True, percent=True):
        """ randomize the combined motion.
"""
        update=False
        for m in self.motionList:
            if m.can_be_modified:
                m.randomize()
                update=True
        if update:
            self.updateTransformation()
            if self.node: self.node().newMotion=True        
        return
    

class LocalPerturbation(FTMotionCombiner):
    """Defines a combination of rotation and translation
self.rotMotion  :  a FTMotion_ConeRotation object
self.transMotion:  a FTMotion_BoxTranslation object
"""
    def __init__(self, motionParamDictList=None,
                 name='ligand_rotation_translation_in_a_box'):
        """Constructor
motionParamDictList : a list of dictionaries, (motion parameters)
"""
        self.coneMotion=None
        self.transMotion=None
        FTMotionCombiner.__init__(self, name=name, \
                                  motionParamDictList=motionParamDictList)

    def parseMotionSettings(self,motionParamDictList):
        #print motionParamDictList        
        if len(motionParamDictList) == len(self.motionList):
            for i in range(len(self.motionList)):
                motion = self.motionList[i]
                config = motionParamDictList[i]
                del config['type'] # obsolete
                del self.motionParamDictList[i]['type']
                apply( motion.configure, (), config)
        else:
            self.motionParamDictList=motionParamDictList
            # reconstruct the motionList the combiner is configured.
            # motion in motionList can be changed by user (in Vision)
            self.motionList=[]
            for dict in motionParamDictList:
                motion=self.motionOfType(dict['type'])
                #print dict['type']
                if motion is None:
                    raise ValueError("Unknown motion found.") 
                del dict['type']
                if self.node:       # pointing to same node, if any.
                    motion.node=self.node
                apply(motion.configure, (), dict)
                self.motionList.append(motion)
                if isinstance(motion, FTMotion_BoxTranslation):
                    self.transMotion=motion
                elif isinstance(motion, FTMotion_ConeRotation):
                    self.coneMotion=motion
                else:
                    pass
        return

    def apply(self, points, translate_to_box_center=False):
        """ if translate_to_box_center is true, first translate the root of \
the points  (the first point in points) to self.gridCenter, then apply the \
transformation. """
        if translate_to_box_center:
            tr=self.transMotion
            tr.ligand_translation=numpy.array(tr.gridCenter,'f') - \
                                   numpy.array(points[0],'f')
            tr.updateTransformation()
            self.updateTransformation()
        else:
            # NOTE: should have already translated the ligand center to \
            #       box center (self.transMotion.gridCenter)
            pass
        
        return FTMotion.apply(self, points)

    def randomize(self):
        self.transMotion.randomize()
        self.coneMotion.randomize()        
        self.updateTransformation()
        return

    def updateTransformation(self):
        """ update self.transform, the transformation matrix"""
        # make sure the "rotation about point" is rotating about
        # the "translated point".
        # i.e. first translate to new point (P) in box, then rotate about P
        point=numpy.array(self.transMotion.gridCenter) + \
               numpy.array(self.transMotion.point) 
        self.coneMotion.configure(point=point.tolist())
        
        res = numpy.identity(4,'f')

##         rMat=self.coneMotion.getMatrix()
##         res=numpy.dot(res, rMat)

        tMat=self.transMotion.getMatrix()
        res=numpy.dot(res, tMat)
        
        rMat=self.coneMotion.getMatrix()
        res=numpy.dot(res, rMat)
        
        self.transform = res.tolist()
        return



### fixme...
class BuildRotamer:
    """
    Defines the sidechain motion of an amino acid. The conformation of side chain will be one of the pre-defined conformations,  based on chi (X) angles from rotamer library file.
    """
#    from FlexTree.FTRotamers import loadRotamerLib
#    preLoaded = loadRotamerLib()


    def __init__(self,  residueName=None, 
                 name='discrete rotamer motion', 
                 libFile='FlexTree/bbind02.May.lib',
                 defFile='FlexTree/rotamer.def',
                 index=-1):
        """Constructor
libFile : the rotamer lib file
defFile : the definition of angles and moving atoms
index: the index-th conformation in the rotamer library
"""
        FTMotion.__init__(self)
        from FlexTree.FTRotamers import  FTRotamer, RotamerLib
        preloadedLib = RotamerLib(libFile,defFile )

        self.libFile = libFile
        self.defFile = defFile
        
        if libFile != None and defFile != None:
            self.rotlib = RotamerLib(libFile, defFile)
        else:
            self.rotlib = preloadedLib
            
        self.transform = numpy.identity(4, 'f') # transformation of ref frame
        self.residueName = None
        self.rotamer = None
        self.index =  -1   # index of rotamer in the library
        self.confList = [] # conformation list
        self.confNB = 0 # number of conformation

        self.configure(residueName= residueName, index = index, name = name)
        

    def getRotamerInfo(self):
        if self.residueName == None or self.rotlib == None:            
            return None, None
        else:
            return self.rotlib.get(self.residueName)
        

    def configure(self, name=None, residueName=None, index=None, \
                  percent=None, **kw):
        """
configure the motion
index is an integer, the index of rotamer in the lib
percent is a float nubmer, between 0 and 1.0. the index will be rounded integer
of (percent * maximum_index).. percent will overwrite the index.
# Q: why introduced percent instead of using index alone.
# A: since different residues have different number of rotamers ( e.g. ARG:81, PHE:6.. etc.).. the GA crossover will generate non-sense indexes. If these indexes are ignored, the GA will converge too fast. By introduceing the uniformed percent, no bad index will be generated.
when percent = 0.8, for ARG, index will be 0.8*81 = 64
                    for PHE, index will be 0.8*6  = 4
                   
"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        if name != None:
            self.name = name
        update = False
        
        from FlexTree.FTRotamers import  FTRotamer, RotamerLib
        if residueName == None and self.residueName == None:
            if self.node:
                molFrag = self.node().molecularFragment[0]
                print molFrag
                if isinstance(molFrag, Residue):
                    residueName=molFrag.name[:3]

        if index != None:
            if index >= 0:
                self.index = int(index)                
                update=True
            else:
                pass

        if residueName != None:
            if residueName != self.residueName:
                frg = None
                if self.node:
                    node=self.node()
                    frg = node.molecularFragment 
                    assert frg !=None
                    assert isinstance(frg, Residue) or \
                           isinstance(frg, ResidueSet)
                    if isinstance(frg, ResidueSet):
                        frg = frg[0] # frg is always a Residue object

                lib=self.rotlib
                if lib.angleDef.has_key(residueName) != True:
                    print "Warning: %s not defined in rotamer library."\
                          %(residueName)
                    return
                
                self.residueName = residueName
                self.index = 0  # index of rotamer in the library
                self.confList = [] # conformation list
                
                angDef, anglist = lib.get(self.residueName)
                result = lib.getResidue(residueName)
                if result is not None:
                    #print 'setting residue..'                  
                    if frg: # use the molecularFragment of FTNode, if available
                        fragment = frg
                    else:   # otherwise use random conformation of the Residue
                            # (by default, from AminoAcids.pdb)
                        fragment = result
                    self.rotamer = FTRotamer(residue = fragment, \
                                             angleDef = angDef, \
                                             angleList =anglist , \
                                             name=result.name)
                    self.confNB = len(anglist)
                    #print self.confNB, 'conformations for', residueName
                else:
                    print 'Residue', residueName, ' not found'
            
        if percent != None:
            self.index = int(percent*self.confNB)
#            print self.residueName, self.index,self.confNB #, "\t",
            update=True
           
        if update:
            if  self.index < self.confNB:
                self.updateTransformation()
            else:
                # the bad index will be ignored..
                # however, we observe that these bad indexes will make the GA
                # converge too fast.  ( Yong Zhao, April, 2005)
                print 'bad index for',self.residueName, self.index, self.confNB
                
            
            if self.node: self.node().newMotion = True 

    def getMatrix(self):
        """Anways return identity. No matrix operation is involved here"""
        self.transform = numpy.identity(4, 'f') 
        return self.transform

    def getConf(self, index):
        """Get index-th conformation based on rotamer library"""
        if self.rotamer is None or index <0:
            return None
        else:
            return self.rotamer.getConf(index)

    def updateTransformation(self):
        """       
this is a special case for self.transform 
 Here, self.transform is always an identity matrix every time the index is changed, we change the original coords of the whole residue to be one of the pre-calculated conformations 
        """                  
        if self.node:
            if self.rotamer is None:
                print 'Error'
                return
            else:
                coords = self.getConf(self.index)
                if coords is not None:
                    self.node().originalConf =  coords
                else:
                    print "Error in updateTransformation."

            
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        if self.residueName is None:
            resName="Not defined"
        else:
            resName = self.residueName
        myDescr = {'index':self.index, 'residueName': resName}
        myDescr.update(descr)
        return myDescr
    
    def getParam(self):
        """ get GA-related parameters
"""
        validParamName =[]
        validParam = []
        validParamName.append('percent')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'mutator': 'uniform', 
                           'min': 0.0, 'max': 0.9999,
                           }) 
        return validParamName, validParam


    def randomize(self):
        """ generate a random translation within the given box
"""
        import random as r

        self.index=int(r.random()* self.confNB)
        #print self.index,
        self.updateTransformation()
        if self.node: self.node().newMotion = True 
     

class FTMotion_Discrete(FTMotion):
    def __init__(self):
        FTMotion.__init__(self)

    def updateTransformation(self):
        print "updateTransformation: virtual method"

    def getMatrix(self, transpose=False):
        print "getMatrix: virtual method"

    def configure(self):
        print "configure: virtual method"

    def getCurrentSetting(self):
        print "getCurrentSetting: virtual method"
        
    def randomize(self):
        print "randomize: virtual method"
        
    def apply(self):
        print "apply: virtual method"

    def updateLocalConf(self, atoms):
        print "updateLocalConf: virtual method"



class FTMotion_NormalMode(FTMotion_Discrete):
    """Normal modes are applied as motion.
self.direction = [[eigen vector 1] ,[eigen vector 2] ... [eigen vector n ]]
n is self.modeNum , number of modes
self.amplitude = [a1, a2, ... an]
    
"""

    def __init__(self, directionList=None, amplitudeList=None, weightList=None,
                 vectorLen=None, modeNum=None, name='combined_Normal_Modes',
                 modeVectorFile=None):
        """Constructor
directionList: list of eigen vectors
amplitudeList: list of amplitudes ( often derived from eigen values )
weightList : list of weight for each eigen vector
name: name of the motion
        
"""
        FTMotion.__init__(self, name = name)
        self.directionList = None
        self.amplitudeList = None
        self.weightList = None
        self.transform = numpy.identity(4, 'f')
        self.modeNum = 0 # number of mode
        self.vectorLen = 0 # number of points that defined the mode
        self.vectorList=None
        self.configure(directionList=directionList,
                       amplitudeList=amplitudeList,
                       weightList=weightList,modeVectorFile=modeVectorFile,
                       modeNum=modeNum, vectorLen=vectorLen)
        
        self.atomsInResidue=None # a list of AtomSet, each AtomSet contains
                                 # atoms from the same Residue
                                 # save this to reduce computational cost
        
        
    def configure(self, name=None,directionList=None, amplitudeList=None,
                  weightList=None, vectorLen=None, modeVectorFile=None,
                  modeNum=None, **kw):
        """
vectorLen : length of eigen vector 
directionList:  a list in shape(modeNum, vectorLen, 3)
amplitudeList:  a list in shape(modeNum,)
weightList:     a list in shape(modeNum,)
modeVectorFile : file name for [eigen vectors..]
                 format: N x 3 (3 float per line), N=vectorLen

NOTE: the **kw is used to configure weightList..
      GA will call
      configure( weight_1= someFloatNumber,weight_2= someFloatNumber, ... )
      we do this because GA can only handel a long list of float.
      see self.getParam
                 
"""
        
        FTMotion.configure(self, name=name)
        update = False    # if True, the transform should be updated
        
        if vectorLen is not None:
            self.vectorLen =vectorLen
            update=True

        if modeNum is not None:
            self.modeNum = modeNum
            update=True

        # modeVectorFile will overwrite directionList
        if modeVectorFile is not None:
            try:
                file=open(modeVectorFile)
                data=file.readlines()
                directionList=[]
                for line in data:
                    tmp=line.split()
                    if tmp[0][-1]==',': # if comma seperated..
                        tmp=line.split(',')
                    tmpList=[]
                    for t in tmp:
                        tmpList.append(float(t))
                    directionList.append(tmpList)
                    
                file.close()
                self.vectorLen = len(directionList)/self.modeNum 
                self.modeVectorFile = modeVectorFile
            except:
                print "Error in processing eigen vectors in",modeVectorFile
                raise
                return

        if directionList is not None:            
            directionList=numpy.array(directionList,'f')            
            sh=directionList.shape
            if len(sh) == 1: # a long 1-D list as input
                modeNum=sh[0]/self.vectorLen/3                
                try:
                    directionList=numpy.reshape(directionList,
                         (modeNum, self.vectorLen,3)).tolist()
                except:
                    print directionList
                    print sh, modeNum, self.vectorLen
                    print "Error in directionList"
                    raise
            elif len(sh) == 2:                
                if sh[0] / self.modeNum == self.vectorLen :
                    #print sh[0] , self.modeNum , self.vectorLen
                    directionList=numpy.reshape(directionList,
                         (self.modeNum, self.vectorLen,3)).tolist()
                else:
                    print sh
                    print sh[0] , self.modeNum , self.vectorLen
                    print "Invalid format for eigne vector list .."
                    raise
            elif len(sh) == 3:
                pass            
            else:
                print "Unknown format .."
                raise
            
            sh=numpy.shape(directionList)
            self.directionList=directionList
            self.modeNum = sh[0]
            self.vectorLen = sh[1]
            update = True

        if amplitudeList is not None:
            self.amplitudeList=amplitudeList
            update = True
            

        if kw:
            keys=kw.keys()
            weights={}
            # weights are in range(0,1)
            for k in keys:
                tmp = k.split('weight_')
                if len(tmp) ==2:
                    index=int(tmp[1])
                    # make the weight in range(-1, 1)
                    weights[index]=kw[k] * 2.0 - 1.0 
            lw = len(weights)
            if  lw == self.modeNum  and lw !=0:
                weightList=numpy.zeros(self.modeNum, 'f')
                for k,v in weights.items():
                    weightList[k]=v  # construct a weightList

        if weightList is not None:
            self.weightList=weightList
            #print 'weight..',self.weightList[0]
            update = True            

        if update:
            self.updateTransformation()            
            if self.node:
                n=self.node()
                n.newMotion = True
                n.localMotion=self
                
        

    def updateTransformation (self):
        """recompute the new translation vector list, stored in
self.vectorList
returns self.transform     (identity)
"""
        self.vectorList=numpy.zeros( (self.vectorLen, 3), 'f')
        for m in range(self.modeNum):

## the vectors from MMTK has already multiplied with             
##             vectors=numpy.array(self.directionList[m], 'f' ) * \
##                      numpy.array(sqrt(self.amplitudeList[m]), 'f')
            vectors=numpy.array(self.directionList[m], 'f' )
                                            
            self.vectorList += vectors * numpy.array(self.weightList[m], 'f')

        return self.transform
    
                                
    def getMatrix(self, anchorAtoms=None,  transpose=False):
        """ returns the transformation(translation) matrix of anchor atom
"""
        if anchorAtoms is None:
            return self.transform
        else:
            ## NOTE: as of Jun 22, 2005, only support anchor (CB,CA,C)
            #assert anchorAtoms[0].conformation == 1
            currentConf = anchorAtoms[0].conformation
            if currentConf !=2:
                anchorAtoms.setConformation(2)
            
            anchors= anchorAtoms.coords
            CB=numpy.array(anchors[0],'f')
            CA=numpy.array(anchors[1],'f')
            C =numpy.array(anchors[2],'f')            
            mat=defineLocalCoordSys(CB, CA, C)

            #print 'CA=',CA

            transform = numpy.identity(4, 'f')
            transform[:3,:3] = mat
            transform[:3,3] = anchorAtoms[1].coords #C-Alpha
            transform=numpy.transpose(transform)

            #print transform
            if currentConf !=2:
                anchorAtoms.setConformation(currentConf)
            
            return transform

 
    def _coordsByResidue(self, atoms):
        """ One Normal Mode applied to one residue ."""
        
        #atoms=self.node().molecularFragment.findType(Atom)
        currentConf = atoms[0].conformation
        if currentConf!=0:
            atoms.setConformation(0)
            
        resSet=atoms.parent.uniq()
        origCoords=[]

        # must keep the origCoords as in order of atoms
        #atoms.sort()  ### NO sorting !! NO sorting !! 
        if self.atomsInResidue is None:
            atomsInRes=[]
            for r in resSet:
                ats = r.atoms & atoms # make sure in the molecularFragment
                #ats=r.atoms
                atomsInRes.append(ats)
            self.atomsInResidue=atomsInRes
            
        data=map(None, self.vectorList, self.atomsInResidue)
        for v, ats in data:                        
            tmp=[]
            for at in ats:
                tmp.append( (numpy.array(at.coords) + v).tolist() )
            origCoords.extend(tmp)

        if currentConf!=0:
            atoms.setConformation(currentConf)

        # for debugging    
        #assert len(origCoords)==len(atoms)
        
        return origCoords


    def apply(self, atoms):
        """ returns the coordinates after normal mode transformation
atoms: an AtomSet to which the normal mode will apply
lenth of points must equal to number of vectors..
"""
        v_num=self.vectorLen
        if len(atoms) == self.vectorLen:
            newPoints=[]
            data=map(None, self.vectorList, atoms.coords)
            for d in data:
                v=numpy.array(d[0])
                newPoints.append((numpy.array(d[1])+v).tolist())
            return newPoints
        else:
            res=atoms.parent.uniq()
            if len(res) == v_num: # one vector per residue
##                 print '********'
##                 print 'one vector per residue'
##                 print '********'
                return  self._coordsByResidue(atoms)
            elif len(res)*4 == v_num: # one vector per backbone atom
                ## fix me !! not working ..
                print "one vector per backbone atom, not working .. "
                result = self.apply(self.originalCoords)
                return result
            else:
                print "Don't know how to map AtomSet with normal mode vectors"
                print self.vectorLen, "vectors found"
                print len(res), "residues found"
                raise RuntimeError
                return atoms.coods

    
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr={}
        # build a long flat list here to be stored in XML
        matrixListLong =[]
        matrixListLong2 =[]
        matrixListLong3 =[]
        #d0,d1,d2 = numpy.array(self.directionList).shape

        dList = self.directionList
        for i in range(len(dList)):
            mat=dList[i]
            matrixListLong += numpy.array(mat).ravel().tolist()

        aList=self.amplitudeList
        for i in range(len(aList)):
            mat=aList[i]
            matrixListLong2 += numpy.array(mat).ravel().tolist()

        wList=self.weightList
        for i in range(len(wList)):
            mat=wList[i]
            matrixListLong3 += numpy.array(mat).ravel().tolist()

            
        myDescr = { # use one dimension list
                   'amplitudeList':matrixListLong2,
                   'weightList':matrixListLong3,
                   'vectorLen': self.vectorLen,
                   'modeNum': self.modeNum,
                   }
        # if vectors given as in file, save the filename
        # otherwise, save the list
        if hasattr(self, 'modeVectorFile'):
            myDescr['modeVectorFile'] = self.modeVectorFile
        else:
            myDescr['directionList'] = matrixListLong
            
        myDescr.update(descr)
        return myDescr


    def randomize(self):
        """ randomize the motion. """    
        import random as r
        for i in range(self.modeNum):
            # range from [ -amplitudeList[i], +amplitudeList[i]  ]
            self.weightList[i] = (r.random()*2 - 1.0) * self.amplitudeList[i]

            
            # range from [ -1.0 , +1.0  ]
            #self.weightList[i] = (r.random()*2. - 1.0) 


        self.updateTransformation()
        if self.node:
            self.node().newMotion = True 


    def getParam(self):
        """get the GA related parameters"""
        t=self.tolerance
        validParamName =[]
        validParam = []

        # the validParam will be passed to self.configure as **kw        
        for i in range(self.modeNum):
            validParamName.append('weight_'+str(i))
            validParam.append({'type': 'continuous', 'dataType':'float',
                               'mutator': 'gaussian', 
                               'min': 0.0, 'max':1.0 }
                              )
        return validParamName, validParam



class FTMotion_EssentialDynamics(FTMotion_NormalMode):
    """Normal modes are applied as motion.
self.direction = [[eigen vector 1] ,[eigen vector 2] ... [eigen vector n ]]
n is self.modeNum , number of modes
self.amplitude = [a1, a2, ... an]    
"""

    def __init__(self, edFile=None, modeNum=None, name='Essential_Dynamics'):
        """Constructor
name: name of the motion
edFile: Essential Dynamics file
   format of Essential Dynamics file:
     first line: name of PDB file that all vectors are derived from
     second line: filter, one of ['CA', 'backbone', 'all']
     from third line to EOF:
     eigen value(a float), eigen vector( a list)     
     """
        FTMotion.__init__(self, name = name)
        self.directionList = None
        self.amplitudeList = None
        self.weightList = None
        self.transform = numpy.identity(4, 'f')
        self.modeNum = 0 # number of mode
        self.vectorLen = 0 # number of points that defined the mode
        self.vectorList=None
        self.scalingFactor=1.0
        self.edFile=None
        self.configure(edFile=edFile, modeNum=modeNum)
        
        
                
        self.atomsInResidue=None # a list of AtomSet, each AtomSet contains
                                 # atoms from the same Residue
                                 # save this to reduce computational cost
        
        
    def configure(self, name=None,edFile=None, modeNum=None,
                  weightList=None, scalingFactor=None, **kw):
        """
weightList:     a list in shape(modeNum,)
edFile    : file name for Essential Dynamics file
   format of Essential Dynamics file:
     first line: name of PDB file that all vectors are derived from
     second line: filter, one of ['CA', 'backbone', 'all']
     from third line to EOF:
     eigen value(a float), eigen vector( a list)

NOTE: the **kw is used to configure weightList..
      GA will call
      configure( weight_1= someFloatNumber,weight_2= someFloatNumber, ... )
      we do this because GA can only handel a long list of float.
      see self.getParam
"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)

        FTMotion.configure(self, name=name)
        update = False    # if True, the transform should be updated

        if edFile is not None:
            ed=EssentialDynamics()
            ok=ed.load(edFile)
            if ok:
                self.edFile=edFile
                # number of points that defined the mode
                self.vectorLen =len(ed.vectors[0])/3
                if modeNum is not None:
                    if modeNum<=len(ed.vectors):
                        self.modeNum=modeNum
                    else:
                        ## too large.. 
                        self.modeNum = len(ed.vectors) # number of mode
                else:
                    self.modeNum = len(ed.vectors) # number of mode

                tmp=numpy.array(ed.vectors[:self.modeNum],'f')
                tmp=numpy.reshape(tmp, (self.modeNum, self.vectorLen, 3) )
                self.directionList = tmp.tolist()
                self.amplitudeList = ed.amplitudes
                self.weightList=numpy.zeros(self.modeNum, 'f')
                self.vectorList=None
                update=True
            else:
                print 'Error in loading essential dynamics file:', edFile
                raise ValueError
        if kw:
            keys=kw.keys()
            weights={}
            # weights are in range(0,1)
            for k in keys:
                tmp = k.split('weight_')
                if len(tmp) ==2:
                    index=int(tmp[1])
                    # make the weight in range(-1, 1)
                    weights[index]=kw[k] * 2.0 - 1.0 
            lw = len(weights)
            if  lw == self.modeNum  and lw !=0:
                weightList=numpy.zeros(self.modeNum, 'f')
                for k,v in weights.items():
                    weightList[k]=v  # construct a weightList

        if weightList is not None:
            self.weightList=weightList
            update = True            

        if scalingFactor is not None:
            self.scalingFactor=scalingFactor
            update = True

        if update:
            self.updateTransformation()            
            if self.node:
                n=self.node()
                n.newMotion = True
                n.localMotion=self


    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr={}
        # build a long flat list here to be stored in XML
        matrixListLong =[]
        matrixListLong2 =[]
        matrixListLong3 =[]
        #d0,d1,d2 = numpy.array(self.directionList).shape

        dList = self.directionList
        for i in range(len(dList)):
            mat=dList[i]
            matrixListLong += numpy.array(mat).ravel().tolist()

        aList=self.amplitudeList
        for i in range(len(aList)):
            mat=aList[i]
            matrixListLong2 += numpy.array(mat).ravel().tolist()

        wList=self.weightList
        for i in range(len(wList)):
            mat=wList[i]
            matrixListLong3 += numpy.array(mat).ravel().tolist()
            
        myDescr = { # use one dimension list
                   'weightList':matrixListLong3,
                   'edFile': self.edFile,
                   'modeNum': self.modeNum,
                   'scalingFactor': self.scalingFactor,
                   }            
        myDescr.update(descr)
        return myDescr


    def updateTransformation (self):
        """recompute the new translation vector list, stored in
self.vectorList
returns self.transform     (identity)
"""
        self.vectorList=numpy.zeros( (self.vectorLen, 3), 'f')
        for m in range(self.modeNum):
            vectors=numpy.array(self.directionList[m],'f')*self.amplitudeList[m]
            self.vectorList = self.vectorList + \
                              vectors *(self.weightList[m]*self.scalingFactor)

        return self.transform

#### end of FTMotion_EssentialDynamics

 

class FTMotion_Rotamer(FTMotion_Discrete):
    """ Defines the sidechain motion of an amino acid. The conformation of side chain will be one of the pre-defined conformations,  based on chi (X) angles from rotamer library file.
"""
#    from FlexTree.FTRotamers import loadRotamerLib
#    preLoaded = loadRotamerLib()

    def __init__(self, # residueName=None, 
                 name='discrete_rotamer_motion',
                 sideChainAtoms=None,
                 anchorAtomNames=['CB','CA','C'],
                 index=-1,
                 exclude=[]):
        """Constructor
index: the index-th conformation in the rotamer library
"""
        FTMotion_Discrete.__init__(self)

        self.transform = numpy.identity(4, 'f') # transformation of ref frame
        self.residueName = None
        self.index = -1    # index of rotamer in the library
        self.confList = [] # conformation list
        self.confNB = 0    # number of conformation
        self.sideChainAtoms = None
        self.anchorAtomNames = None
        self.exclude = None
        self.configure(index=index, name=name,
                       sideChainAtoms=sideChainAtoms,
                       anchorAtomNames=anchorAtomNames,
                       exclude=exclude)        


##     def getRotamerInfo(self):
##         if self.residueName == None or self.rotlib == None:            
##             return None, None
##         else:
##             return self.rotlib.get(self.residueName)
        

    def _buildConfList(self):
        """construct the conformation list from RotLib
NOTE: this should be called only when residueName is specified or changed.

"""
        if self.node is None:
            return False
        
        frag = self.node().molecularFragment
        if frag is None:
            return

        atoms = frag.findType(Atom)
        atoms.sort() ## always sort it.. if the self.sideChainAtomNames are
                     ## not in order, we can still do the right mapping
                     ## between atom name and coords
        assert len(atoms.get('backbone'))==0 # should contain NO backbone atoms
        all = atoms.parent.uniq()
        residueName = all.name
        #assert residueName == self.residueName
        
        assert len(residueName)==1  # all atoms from the same residue
        
        self.anchorAtoms = []
        all = all.atoms
        for name in self.anchorAtomNames:
            try:
                self.anchorAtoms.append(all.get(name)[0])
            except:
                print "Error in anchor atoms name"
                raise
                return

        self.anchorAtoms = AtomSet(self.anchorAtoms)
        
        residueName = residueName[0][:3]
        from FlexTree.RotLib import RotLib

        if residueName not in RotLib.keys():
            print
            print residueName, "not found in rotamer library\n"
            return False

        if self.sideChainAtomNames:
            assert len(self.sideChainAtomNames) == len(atoms)

        lib = RotLib[residueName]
        for i in range(len(lib)):
            if i in self.exclude: # exclusions..
                continue
            conf = lib[i]
            coords = []
            for a in atoms:
                coords.append(conf[a.name])

            # conformation saved in the same order of atoms
            self.confList.append(coords)

        self.confNB = len(self.confList)
        assert self.confNB == len(lib) -len(self.exclude)
        self.index=0 
        return True
    
        

    def configure(self, name=None, residueName = None, index=None, \
                  percent=None, \
                  sideChainAtoms=None,anchorAtoms=None, \
                  sideChainAtomNames=None, anchorAtomNames=None,
                  exclude=None, redo=True, **kw):
        """configure the motion
index is an integer, the index of rotamer in the lib
percent is a float nubmer, between 0 and 1.0. the index will be rounded integer
of (percent * maximum_index).. percent will overwrite the index.
# Q: why introduced percent instead of using index along.
# A: since difference residue has difference number of rotamers ( e.g. ARG:81, PHE:6.. etc.).. the GA crossover will generate non-sense indexes. If these indexes are ignored, the GA will converge too fast. By introduceing the uniformed percent, no bad index will be generated.
when percent = 0.8, for ARG, index will be 0.8*81 = 64
                    for PHE, index will be 0.8*6  = 4                   
"""
        if len(kw):
            apply( FTMotion.configure, (self,), kw)
        
        if name != None:
            self.name = name
        update = False
        rebuildConfList = False

        if residueName !=None:
            self.residueName = residueName
            rebuildConfList=True
        
        if index != None:
            if index >= 0 and index < self.confNB:
                self.index = int(index)                
                update=True
            else:
                pass

        if exclude != None:
            self.exclude=exclude
            rebuildConfList=True
            if self.node:
                if self.node().tree:
                    self.node().tree().rotamerOnly=True
            
        if sideChainAtomNames!=None :
            self.sideChainAtomNames=sideChainAtomNames
            rebuildConfList=True
            
        if anchorAtomNames :
            self.anchorAtomNames=anchorAtomNames            
            if self.node:
                frag = self.node().molecularFragment
                if frag is None:
                    pass
                else:
                    pass #####  fixme !!
                    #self.anchorAtoms=[]
                    #print '### ',anchorAtomNames
#            if self.node:
#                self.node().configure(anchorAtoms=anchorAtomNames)
            rebuildConfList=True
                
        if percent != None:
            # MS this version never gets index 0
            #self.index = int(percent*self.confNB)

            # MS this version provides a uniform mapping from % to indices
            # proof
            #  for in in range(10):
            #     print i*.01, int(round(i*0.1*5-0.49999)
            self.index = int(round(percent*(self.confNB)-0.49999))
            update = True

        if rebuildConfList:
            self._buildConfList()
           
        if redo and update:
            if  self.index < self.confNB:
                self.updateTransformation()
            else:
                # the bad index will be ignored..
                # however, we observe that these bad indexes will make the GA
                # converge too fast.  ( Yong Zhao, April, 2005)
                print 'bad index for',self.residueName, self.index, self.confNB
                            
            if self.node: self.node().newMotion = True 


    def getMatrix(self, anchorAtoms=None):
        """  returns self.transform.. see def updateTransformation() about
how self.transform was calculated.
"""
        # fixme .. anchorAtoms not supported
        
        #self.transform = numpy.identity(4, 'f')
        #print 'getMatrix is called'
        return self.transform


    def apply(self, atoms):
        """
    This apply is different from FTMotion.apply()
This function returns the self.index-th conformer for sidechains atoms
"""
        #import pdb
        #pdb.set_trace()
        coords = self.getConf(self.index)
        if coords is None:
            return None
        if len(atoms)==len(coords):
            # assume the self.transform is already updated
            # since the conformation from rotamer lib are aligned at origin.
            # self.transform will transform it to the right place
            
            if self.node:
                # order is the same as MolFrag.. (the way confList is built)
                self.node().originalConf = coords  

            return coords # CA at the origin..
            #return FTMotion.apply(self, coords)
        else:
            print "Warning..."
            return None
        

    def getConf(self, index):
        """Get index-th conformation based on rotamer library"""
        if  index < 0 or index > self.confNB:
            return None
        else:
            return self.confList[index]
   

    def updateTransformation(self):
        """this is a special case for self.transform 
        Here, self.transform is always an identity matrix every time the index is changed,
        we change the original coords of the whole residue to be one of the pre-calculated conformations 
        """
        if self.anchorAtoms:
            currentConf = self.anchorAtoms[0].conformation
            if currentConf != 0:
                self.anchorAtoms.setConformation(0)
            anchors = self.anchorAtoms.coords
            CB = numpy.array(anchors[0],'f')
            CA = numpy.array(anchors[1],'f')
            C  = numpy.array(anchors[2],'f')            
            mat = defineLocalCoordSys(CB, CA, C)

            self.transform = numpy.identity(4, 'f')
            self.transform[:3,:3] = mat
            self.transform[:3,3] = self.anchorAtoms[1].coords #C-Alpha
            self.transform = numpy.transpose(self.transform)

            if currentConf !=0:
                self.anchorAtoms.setConformation(currentConf)            
            return
        else:
            self.transform = numpy.identity(4, 'f') 
            return
        
            
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        if self.residueName is None:
            resName=None
        else:
            resName = self.residueName
        myDescr = {'index':self.index, 'residueName': resName,
                   'sideChainAtomNames':self.sideChainAtomNames,
                   'anchorAtomNames': self.anchorAtomNames,
                   }
        if len(self.exclude):
            myDescr['exclude']=self.exclude
            
        myDescr.update(descr)
        return myDescr

    
    def getParam(self):
        """ get GA-related parameters
"""
        validParamName =[]
        validParam = []
        validParamName.append('percent')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'min': 0.0,'max': 0.9999,
                           'mutator': 'uniform'
                           }) 
        return validParamName, validParam


    def randomize(self):
        """ generate a random translation within the given box
"""
        import random as r

        self.index=int(r.random()* self.confNB)
        self.updateTransformation()
        if self.node: self.node().newMotion = True 
     

    def removeClashWith(self, rigidAtoms, cutoff=1.85):
        """ loop over conformation list and remove the ones that clashs with
rigidAtoms. (within the cutoff) 
"""
        if not self.node:
            return

        cutoff = cutoff * cutoff # square of cutoff

        ftNode = self.node()
        rigidCoords = rigidAtoms.coords

        # build a bhtree for the rigid atoms
        from bhtree import bhtreelib
        bht = bhtreelib.BHtree( rigidCoords, None, 10)

        result = numpy.zeros( (len(rigidCoords),), 'i' )
        dist2 = numpy.zeros( (len(rigidCoords),), 'f' )
        maxbo = max([a.bondOrderRadius for a in rigidAtoms])

        goodList=[]
        for i in range(self.confNB):            
            ftNode.newMotion = True
            if hasattr(self, 'deviations'):
                self.configure(index=i, deviations=self.deviations)
            else:
                self.configure(index=i)
            ftNode.updateCurrentConformation()
            hasClash = False
            current = ftNode.currentConf
            # move the far-end atoms first
            # because they have more chance to clash with others
            current.reverse()
            sidechain = ftNode.getAtoms()
            sidechain.reverse()
            maxbo = max(maxbo, max([a.bondOrderRadius for a in sidechain]))
            cutoff = maxbo+maxbo
            for j in range(len(sidechain)):
                clashed=False
                nb = bht.closePointsDist2(
                    tuple(current[j]), cutoff, result, dist2)
                bo1 = sidechain[j].bondOrderRadius
                for n, ind in enumerate(result[:nb]):
                    bo = bo1 + rigidAtoms[ind].bondOrderRadius
                    if dist2[n] < bo*bo*0.81: #clash
                        clashed=True
                        break                        
##                 for r in rigidAtoms:
##                     sum=sidechain[j].bondOrderRadius + r.bondOrderRadius
##                     if _distSQR(current[j], r.coords) < sum * sum *0.81 : #90%
##                         clashed=True
##                         break
                if clashed:
                    break
            
            if not clashed:
                goodList.append(i)  # the i-th conf in confList
        
        if len(goodList) == 0:
            print ftNode.name, "no conformers found !"
            raise

        if len(self.confList):
            newConfList=[]
            for i in goodList:
                newConfList.append(self.confList[i])

            self.confList = newConfList

            all = range(self.confNB)
            self.exclude=[]
            for i in all:
                if i not in goodList:
                    self.exclude.append(i)
        else:
            self.goodRotamerIndices = goodList[:]
            
        print "Removing %d bad rotamers for %s, kept %d" %\
              (self.confNB - len(goodList), self.node().name, len(goodList)) 
        self.confNB = len(goodList)

## class FTMotion_SoftRotamer(FTMotion_Discrete):
##     """
##     Motion object for rotameric amino acide side chain.
##     This motion object uses an integer to select a given rotamer and a
##     vector of diviation from the rotameric position.
## """
    
##     def __init__(self, residue, anchorAtoms, name='softRotamer_motion'):
## #                 sideChainAtoms=None, anchorAtomNames=['CB','CA','C'],
## #                 exclude=[]):
##         """
## Constructor

## index: the index-th conformation in the rotamer library
## deviations: vector or angular deviations
## """
##         self.name = name
##         FTMotion_Discrete.__init__(self)
        
##         self.anchorAtoms = anchorAtoms
##         # MS Jan 2014
##         # rotamerLib should be a class library but it creates import problems
##         #from FlexTree.FTRotamers import  FTSoftRotamer, RotamerLib
##         from FlexTree.FTRotamers import RotamerLib
##         import FlexTree
##         self.rotamerLib = RotamerLib(
##             os.path.join(FlexTree.__path__[0], 'bbind02.May.lib'),
##             os.path.join(FlexTree.__path__[0], 'rotamer.def'))
##         angleDef, angleList, angleDev = self.rotamerLib.get(residue.type)
##         self.angDef = angleDef
##         self.angDev = angleDev
##         self.angleList = angleList
        
##         # reorder atoms in residue.atoms in the following order
##         # HN C O N CA CB ....
        
##         # need to remove C, O and HN atoms but keep N and CA
##         # to compute the original angles and compute rotation axis for CHI1

##         # find and remove backboen atoms
##         Natom = residue.childByName['N']
##         residue.atoms.remove(Natom)
##         CAatom = residue.childByName['CA']
##         residue.atoms.remove(CAatom)
##         CBatom = residue.childByName['CB']
##         residue.atoms.remove(CBatom)
##         Catom = residue.childByName['C']
##         residue.atoms.remove(Catom)
##         Oatom = residue.childByName['O']
##         residue.atoms.remove(Oatom)
##         # remove HN if found
##         hn = None
##         for b in Natom.bonds:
##             a1 = b.atom1
##             if a1==Natom: a1 = b.atom2
##             if a1.element=='H':
##                 hn = a1
##                 break
##         if hn is not None:
##             residue.atoms.remove(hn)

##         # re-insert N CA CB at the begining
##         residue.atoms.insert(0, CBatom)
##         residue.atoms.insert(0, CAatom)
##         residue.atoms.insert(0, Natom)

##         # create an atom set wihout C O HN for Rotamer object
##         atoms = residue.atoms.copy()

##         # re-insert C O HN at the begining 
##         residue.atoms.insert(0, Oatom)
##         residue.atoms.insert(0, Catom)
##         if hn is not None:
##             residue.atoms.insert(0, hn)

##         # build an objec to compute coordinates for rotamer side chain atoms
##         from FlexTree.rotamer import Rotamer
##         self.rotamer = Rotamer(atoms, angleDef, angleList)

##         self.angles = [0]*len(angleDef)
##         self.confNB = len(angleList) # number of rotamers in library


##     def setAngles(self, angles):
##         for i,a in enumerate(angles):
##             self.angles[:] = a


##     def apply(self, atoms):
##         """
##     This apply is different from FTMotion.apply()
## This function returns the self.index-th conformer for sidechains atoms
## """
##         coords = self.rotamer.getCoordsFromAngles(self.angles)
##         self.node().originalConf = coords[3:] # skip N, CA, CB
##         for a,c in zip(self.rotamer.atoms[3:], coords[3:]):
##             a._coords[1] = c

class FTMotion_SoftRotamer(FTMotion_Discrete):
    """
    Motion object for rotameric amino acide side chain.
    This motion object uses an integer to select a given rotamer and a
    vector of diviation from the rotameric position.
"""
    
    def __init__(self, residue, anchorAtoms, name='softRotamer_motion'):
#                 sideChainAtoms=None, anchorAtomNames=['CB','CA','C'],
#                 exclude=[]):
        """
Constructor

index: the index-th conformation in the rotamer library
deviations: vector or angular deviations
"""
        FTMotion_Discrete.__init__(self)
        self.name = name
        
        self.anchorAtoms = anchorAtoms
        # MS Jan 2014
        # rotamerLib should be a class library but it creates import problems
        #from FlexTree.FTRotamers import  FTSoftRotamer, RotamerLib
        from FlexTree.FTRotamers import RotamerLib
        import FlexTree
        self.rotamerLib = RotamerLib(
            os.path.join(FlexTree.__path__[0], 'bbind02.May.lib'),
            os.path.join(FlexTree.__path__[0], 'rotamer.def'))
        angleDef, angleList, angleDev = self.rotamerLib.get(residue.type)
        self.angDef = angleDef
        self.angDev = angleDev
        self.angleList = angleList
        
        # reorder atoms in residue.atoms in the following order
        # HN C O N CA CB ....
        
        # need to remove C, O and HN atoms but keep N and CA
        # to compute the original angles and compute rotation axis for CHI1

        # find and remove backboen atoms
        Natom = residue.childByName['N']
        residue.atoms.remove(Natom)
        CAatom = residue.childByName['CA']
        residue.atoms.remove(CAatom)
        CBatom = residue.childByName['CB']
        residue.atoms.remove(CBatom)
        Catom = residue.childByName['C']
        residue.atoms.remove(Catom)
        Oatom = residue.childByName['O']
        residue.atoms.remove(Oatom)
        # remove HN if found
        hn = None
        for b in Natom.bonds:
            a1 = b.atom1
            if a1==Natom: a1 = b.atom2
            if a1.element=='H':
                hn = a1
                break
        if hn is not None:
            residue.atoms.remove(hn)

        # re-insert N CA CB at the begining
        residue.atoms.insert(0, CBatom)
        residue.atoms.insert(0, CAatom)
        residue.atoms.insert(0, Natom)

        # create an atom set wihout C O HN for Rotamer object
        atoms = residue.atoms.copy()

        # re-insert C O HN at the begining 
        residue.atoms.insert(0, Oatom)
        residue.atoms.insert(0, Catom)
        if hn is not None:
            residue.atoms.insert(0, hn)

        # build an object to compute coordinates for rotamer side chain atoms
        from FlexTree.rotamer import Rotamer
        self.rotamer = Rotamer(atoms, angleDef, angleList)

        self.angles = [0]*len(angleDef)
        self.confNB = len(angleList) # number of rotamers in library


    def setAngles(self, *angles):
        for i,a in enumerate(angles):
            self.angles[:] = a[:]


    def apply(self, atoms):
        """
    This apply is different from FTMotion.apply()
This function returns the self.index-th conformer for sidechains atoms
"""
        coords = self.rotamer.getCoordsFromAngles(self.angles)
        self.node().originalConf = coords[3:] # skip N, CA, CB
        for a,c in zip(self.rotamer.atoms[3:], coords[3:]):
            a._coords[1] = c


## class FTMotion_SoftRotamer1(FTMotion_Rotamer):
##     """
##     Motion object for rotameric amino acide side chain.
##     This motion object uses an integer to select a given rotamer and a
##     vector of diviation from the rotameric position.
## """
    
##     def __init__(self, residue, anchorAtoms, name='discrete_softrotamer_motion',
##                  sideChainAtoms=None, anchorAtomNames=['CB','CA','C'],
##                  index=-1, deviations=None, exclude=[]):
##         """
## Constructor

## index: the index-th conformation in the rotamer library
## deviations: vector or angular deviations
## """
##         FTMotion_Rotamer.__init__(
##             self, name=name, sideChainAtoms=sideChainAtoms,
##             anchorAtomNames=anchorAtomNames, index=index, exclude=exclude)

##         self.anchorAtoms = anchorAtoms
##         # MS Jan 2014
##         # rotamerLib should be a class library but it creates import problems
##         #from FlexTree.FTRotamers import  FTSoftRotamer, RotamerLib
##         from FlexTree.FTRotamers import RotamerLib
##         import FlexTree
##         self.rotamerLib = RotamerLib(
##             os.path.join(FlexTree.__path__[0], 'bbind02.May.lib'),
##             os.path.join(FlexTree.__path__[0], 'rotamer.def'))
##         angleDef, angleList, angleDev = self.rotamerLib.get(residue.type)
##         self.angDef = angleDef
##         self.angDev = angleDev

##         # reorder atoms in residue.atoms in the following order
##         # HN C O N CA CB ....
        
##         # need to remove C, O and HN atoms but keep N and CA
##         # to compute the original angles and compute rotation axis for CHI1

##         # find and remove backboen atoms
##         Natom = residue.childByName['N']
##         residue.atoms.remove(Natom)
##         CAatom = residue.childByName['CA']
##         residue.atoms.remove(CAatom)
##         CBatom = residue.childByName['CB']
##         residue.atoms.remove(CBatom)
##         Catom = residue.childByName['C']
##         residue.atoms.remove(Catom)
##         Oatom = residue.childByName['O']
##         residue.atoms.remove(Oatom)
##         # remove HN if found
##         hn = None
##         for b in Natom.bonds:
##             a1 = b.atom1
##             if a1==Natom: a1 = b.atom2
##             if a1.element=='H':
##                 hn = a1
##                 break
##         if hn is not None:
##             residue.atoms.remove(hn)

##         # re-insert N CA CB at the begining
##         residue.atoms.insert(0, CBatom)
##         residue.atoms.insert(0, CAatom)
##         residue.atoms.insert(0, Natom)

##         # create an atom set wihout C O HN for Rotamer object
##         atoms = residue.atoms.copy()

##         # re-insert C O HN at the begining 
##         residue.atoms.insert(0, Oatom)
##         residue.atoms.insert(0, Catom)
##         if hn is not None:
##             residue.atoms.insert(0, hn)

##         # build an objec to compute coordinates for rotamer side chain atoms
##         from FlexTree.rotamer import  Rotamer
##         self.rotamer = Rotamer(atoms, angleDef, angleList)

##         self.deviations = [0]*len(angleDef)
##         self.confNB = len(angleList) # number of rotamers in library
##         self.configure(deviations=deviations)


##     def setRotamer(self, index, deviations=None):
##         if deviations:
##             self.deviations[:] = deviations[:]

##         if index < 0:
##             raise ValueError, "index has to be >=0, got %d"%index
##         if index == self.confNB and self.confNB>0:
##             index -= 1 # we should prevent the gene percent from going t0 1.0
##         self.index = index


##     def apply(self, atoms):
##         """
##     This apply is different from FTMotion.apply()
## This function returns the self.index-th conformer for sidechains atoms
## """
##         coords = self.rotamer.getCoords(self.index, self.deviations)
##         self.node().originalConf = coords[3:] # skip N, CA, CB
##         for a,c in zip(self.rotamer.atoms[3:], coords[3:]):
##             a._coords[1] = c


##     def configure(self, name=None, index=None,
##                   percent=None, sideChainAtoms=None, anchorAtoms=None,
##                   sideChainAtomNames=None, anchorAtomNames=None,
##                   exclude=None, deviations=None, redo=True, **kw):
##         """configure the motion
## index is an integer, the index of rotamer in the lib
## percent is a float number, between 0 and 1.0. the index will be rounded integer
## of (percent * maximum_index).. percent will overwrite the index.
## # Q: why introduced percent instead of using index along.
## # A: since difference residue has difference number of rotamers ( e.g. ARG:81, PHE:6.. etc.).. the GA crossover will generate non-sense indexes. If these indexes are ignored, the GA will converge too fast. By introduceing the uniformed percent, no bad index will be generated.
## when percent = 0.8, for ARG, index will be 0.8*81 = 64
##                     for PHE, index will be 0.8*6  = 4                   
## """
##         kw['name'] = name
##         #kw['index'] = index
##         #kw['percent'] = percent
##         kw['sideChainAtoms'] = sideChainAtoms
##         kw['anchorAtoms'] = anchorAtoms
##         kw['sideChainAtomNames'] = sideChainAtomNames
##         kw['anchorAtomNames'] = anchorAtomNames
##         kw['exclude'] = exclude
##         kw['redo'] = deviations == None # if not deviations we update 
        
##         FTMotion_Rotamer.configure( *(self,), **kw)

##         update = False
##         if deviations:
##             self.deviations[:] = deviations[:]
##             update = True

##         if percent != None:
##             self.index = self.goodRotamerIndices[int(
##                 round(percent*(self.confNB)-0.49999))]
##             update = True

##         if index != None:
##             if index < 0:
##                 raise
##             if index == self.confNB and self.confNB>0:
##                 index -= 1 # we shoudl prevent the gene percent from going t0 1.0
##             self.index = int(index)                
##             update=True

##         if redo and update:
##             self.updateTransformation()
##             if self.node: self.node().newMotion = True 


        

##     ## def getConf(self, atoms, index, deviations):
##     ##     """Get index-th conformation based on rotamer library"""
##     ##     coordsDict = self.rotamerFT.getConf(self.index, self.deviations)
##     ##     sortedCoords = []
##     ##     for atom in atoms:
##     ##         sortedCoords.append(coordsDict[atom.name])
##     ##     #print 'SORTEDCONF', sortedCoords
##     ##     return sortedCoords
   

##     def updateTransformation(self):
##         """this is a special case for self.transform 
##         Here, self.transform is always an identity matrix every time the index is changed,
##         we change the original coords of the whole residue to be one of the pre-calculated conformations 
##         """
##         self.transform = numpy.identity(4, 'f') 
##         ## if self.anchorAtoms:
##         ##     currentConf = self.anchorAtoms[0].conformation
##         ##     if currentConf != 0:
##         ##         self.anchorAtoms.setConformation(0)
##         ##     anchors = self.anchorAtoms.coords
##         ##     CB = numpy.array(anchors[0],'f')
##         ##     CA = numpy.array(anchors[1],'f')
##         ##     C  = numpy.array(anchors[2],'f')            
##         ##     mat = defineLocalCoordSys(CB, CA, C)

##         ##     self.transform = numpy.identity(4, 'f')
##         ##     self.transform[:3,:3] = mat
##         ##     self.transform[:3,3] = self.anchorAtoms[1].coords #C-Alpha
##         ##     self.transform = numpy.transpose(self.transform)

##         ##     if currentConf !=0:
##         ##         self.anchorAtoms.setConformation(currentConf)            
##         ## else:
##         ##     self.transform = numpy.identity(4, 'f') 
        
            
##     def getCurrentSetting(self):
##         descr = FTMotion.getCurrentSetting(self)
##         if self.residueName is None:
##             resName=None
##         else:
##             resName = self.residueName
##         myDescr = {'index':self.index, 'residueName': resName,
##                    'sideChainAtomNames':self.sideChainAtomNames,
##                    'anchorAtomNames': self.anchorAtomNames,
##                    'deviations' : '%s'%self.deviations
##                    }
##         if len(self.exclude):
##             myDescr['exclude']=self.exclude
            
##         myDescr.update(descr)
##         return myDescr

    
##     def getParam(self):
##         """ get GA-related parameters
## """
##         validParamName =[]
##         validParam = []
##         validParamName.append('percent')
##         validParam.append({'type': 'continuous', 'dataType':'float',
##                            'min': 0.0,'max': 0.9999,
##                            'mutator': 'uniform'
##                            }) 
##         return validParamName, validParam


##     def randomize(self):
##         """ generate a random translation within the given box
## """
##         import random as r

##         self.index = int(r.random()* self.confNB)
##         #self.updateTransformation()
##         if self.node: self.node().newMotion = True 
     


class FTMotion_LoopRotamer(FTMotion_Discrete):
    """ Defines the loop motion using a predefined set of loop conformations.
    """

    ## FIXME: anchor atoms are not supported yet
    def __init__(self, 
                 conformerFile=None,
                 name='discrete_loop_rotamer_motion',
                 anchorAtomNames=None,
                 index=-1):
        """Constructor
        conformerFile is a Python script providing a list of coordinates for each conformation
        anchorAtoms: 4 atoms defining the loop anchor points. This is used is the
                     the loop in on a domain that moves.
        index: the index-th conformation in the rotamer library
        """
        FTMotion_Discrete.__init__(self)

        self.transform = numpy.identity(4, 'f') # transformation of ref frame
        self.index = -1    # index of rotamer in the library
        self.confList = [] # list of coordinates for each conformation of the molecuar fragments
        self.confNB = 0    # number of conformation
        self.anchorAtomNames = None
        self.configure( conformerFile=conformerFile,
                        index=index, name=name,
                        anchorAtomNames=anchorAtomNames)        


    def updateTransformation(self):
        """this is a special case for self.transform 
        Here, self.transform is always an identity matrix every time the index is changed,
        we change the original coords of the whole residue to be one of the pre-calculated conformations 
        """
        ## FIXME: anchor atoms are not supported yet
        self.transform = numpy.identity(4, 'f')
        return
    

    def getMatrix(self, anchorAtoms=None):
        """returns self.transform.. see def updateTransformation() about
        how self.transform was calculated.
        """
        # FIXME .. anchorAtoms not supported
        
        #self.transform = numpy.identity(4, 'f')
        #print 'getMatrix is called'
        return self.transform


    def apply(self, atoms):
        """This apply is different from FTMotion.apply()
        This function returns the self.index-th conformer for sidechains atoms
        """
        coords=self.getConf(self.index)
        if coords is None:
            return None
        if len(atoms)==len(coords):
            # assume the self.transform is already updated
            # since the conformation from rotamer lib are aligned at origin.
            # self.transform will transform it to the right place
            
            if self.node:
                # order is the same as MolFrag.. (the way confList is built)
                self.node().originalConf = coords  

            return coords # CA at the origin..
            #return FTMotion.apply(self, coords)
        else:
            print "Warning..."
            return None


    def getConf(self, index):
        """Get index-th conformation based on rotamer library"""
        if  index <0 or index > self.confNB:
            return None
        else:
            return self.confList[index]
        
            
    def getCurrentSetting(self):
        descr = FTMotion.getCurrentSetting(self)
        myDescr = {'index':self.index}

        if self.anchorAtomNames:
            myDescr['anchorAtomNames'] = self.anchorAtomNames

        myDescr.update(descr)
        return myDescr

    
    def getParam(self):
        """get GA-related parameters
        """
        validParamName =[]
        validParam = []
        validParamName.append('percent')
        validParam.append({'type': 'continuous', 'dataType':'float',
                           'min': 0.0,'max': 0.9999,
                           'mutator': 'uniform'
                           }) 
        return validParamName, validParam


    def randomize(self):
        """pick a conformation randomly
        """
        import random as r

        self.index=int(r.random()* self.confNB)
        self.updateTransformation()
        if self.node:
            self.node().newMotion = True 


    def buildConfList(self, conformerFile):
        """construct the conformation list from 
        """

        # get a list of atoms in the fragment
        if self.node is None:
            return False
        
        frag = self.node().molecularFragment
        if frag is None:
            return

        atoms=frag.findType(Atom)
        atoms.sort() ## always sort it.. if the self.sideChainAtomNames are
                     ## not in order, we can still do the right mapping
                     ## between atom name and coords

        # get a list of corrdinates for the atoms in the fragments for each conformation
        loc = {}
        execfile(conformerFile, loc)
        confList = loc['loopConf']

        for l in confList:
            assert len(l)==len(atoms)

        self.confList = confList
        self.confNB = len(confList)
        self.index=0 

##         self.anchorAtoms=[]
##         for name in self.anchorAtomNames:
##             try:
##                 self.anchorAtoms.append(atoms.get(name)[0])
##             except:
##                 print "Error in anchor atoms name"
##                 raise
##                 return

        
##         self.anchorAtoms=AtomSet(self.anchorAtoms)
        
        return True
        

    def configure(self, conformerFile=None, name=None, index=None, percent=None,
                  anchorAtoms=None, anchorAtomNames=None, **kw):
        """configure the motion
        index is an integer, the index of rotamer in the lib
        percent is a float nubmer, between 0 and 1.0. the index will be rounded integer
        of (percent * maximum_index).. percent will overwrite the index.
        # Q: why introduced percent instead of using index along.
        # A: since difference residue has difference number of rotamers ( e.g. ARG:81, PHE:6.. etc.)..
        the GA crossover will generate non-sensical indices.
        If these indices are ignored, the GA will converge too fast.
        By introduceing the uniformed percent, no bad index will be generated.
        when percent = 0.8, for ARG, index will be 0.8*81 = 64  for PHE, index will be 0.8*6  = 4                   
        """
        if conformerFile:
            self.buildConfList(conformerFile)
            
        if len(kw):
            apply( FTMotion.configure, (self,), kw)
        
        if name != None:
            self.name = name
        update = False
        rebuildConfList=False

        if index != None:
            if index >= 0 and index < self.confNB:
                self.index = int(index)                
                update=True
            else:
                pass

        if anchorAtomNames :
            self.anchorAtomNames=anchorAtomNames            
            if self.node:
                frag = self.node().molecularFragment
                if frag is None:
                    pass
                else:
                    pass #####  fixme !!
                    #self.anchorAtoms=[]
                    #print '### ',anchorAtomNames
#            if self.node:
#                self.node().configure(anchorAtoms=anchorAtomNames)
            rebuildConfList=True
                
        if percent != None:
            self.index = int(percent*self.confNB)
            update=True
           
        if update:
            if  self.index < self.confNB:
                self.updateTransformation()
            else:
                # the bad index will be ignored..
                # however, we observe that these bad indexes will make the GA
                # converge too fast.  ( Yong Zhao, April, 2005)
                print 'bad index for',self.residueName, self.index, self.confNB
                            
            if self.node: self.node().newMotion = True 
     

# end of FTMotions.py

## EOF notes
"""
<1> why not use ligandAtoms?
   The LigandPreparation will restore the autodock_element of each atom. This
   will mess up the further calculation of autodock score. (e.g. 'c' for Cl)

"""
