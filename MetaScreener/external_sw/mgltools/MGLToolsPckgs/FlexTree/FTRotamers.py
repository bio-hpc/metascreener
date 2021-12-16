## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: Jan 2005 Author: Yong Zhao
#
#    yongzhao@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Yong Zhao and TSRI
#
#########################################################################

"""
This module builds the flexibility tree (FT) of the side chain motion
for each of the 20 amino acids. The FT is based on FTMotion_RotationAboutAxis.
"""

"""
fixme: 
       real rotamers to be added..
"""

import weakref, os

from MolKit.protein import Residue, AtomSet
from FlexTree.FTMotions import FTMotion_Identity, FTMotion_RotationAboutAxis,\
     defineLocalCoordSys
from FlexTree.FT import FlexTree, FTNode
import numpy.oldnumeric as Numeric
N=Numeric
from numpy.oldnumeric.linear_algebra import inverse

## def _chooseFlexResidueSideChainClass(resName):
##     """ private function, import different FTRotamer class accordingly."""
##     name =  'FT_'+resName[:3]
##     ftR =__import__('FlexTree.FTRotamers', globals(), locals(),[name])
##     return getattr(ftR, name) 

from mglutil.math.torsion import torsion

def _getDihedralAngle(residue, axis ):
    """
    axis = [a,b,c,d]
    a,b,c,d : Atom name, string type
    this private function returns the
    dihedral angle of a-b-c-d"""
    atoms = residue.atoms
    names = atoms.name
    a,b,c,d = axis
    idx=names.index(a) ; at1 = atoms[idx]
    idx=names.index(b);  at2 = atoms[idx]
    idx=names.index(c) ; at3 = atoms[idx]
    idx=names.index(d) ; at4 = atoms[idx]
    return  torsion(at1.coords, at2.coords, at3.coords, at4.coords)


class FTRotamer:
    """ Class of Rotamer
A FT tree with freely rotatable bonds is built, then configured by the angles
from rotamer library.

"""
    def __init__(self,  residue, angleDef, angleList ,name='Rotamer'):
        """ Constructor.
residue: one Residue instance
angleDef: 
    every angle is defned by list of 4 atom names(A):e.g. ['N','CA','C','O']
    followed by the atoms (B) that are moved by this rotation, e.g. ['CG']
    each row of angleDef is a list [A,B] 
    e.g. [['N', 'CA', 'C', 'O'], ['CG']]
    with n angles defined. n=len(angleDef)
    
angleList: m by n list.
           m conformations, each of which is defined by n angles

        """
        self.name=name
        self.residue=residue
        self.angle_def=angleDef
        # self.tree is a FlexResidue (FlexTree) instance 
        self.tree = FlexResidue(angleDef, residue=residue)
        self.conformation=[]
        self.motionList=[]
        for c in self.tree.root.children:
            self.motionList.append(c.motion)

        self.originalAngles=[]
        angleDefinition=[]
        # only need ['N', 'CA', 'C', 'O'], ignore the moving atom list
        for data in angleDef:
            angleDefinition.append(data[0])

        angleDef = angleDefinition

        for ang in angleDef:
            self.originalAngles.append(_getDihedralAngle(residue, ang))

        assert len(angleList[0]) == len(angleDef)
        nb = len(angleDef)
        root = self.tree.root

        for angles in angleList:
            for i in range(nb):
                angle = angles[i] - self.originalAngles[i]
                if angle < 0: angle +=360
                self.motionList[i].configure(angle=angle)
                
            root.newMotion = True
            root.updateCurrentConformation()

            # fixme.. getCurrentSortedConformation was not working properly
            coords = root.getCurrentSortedConformation2()
            #coords = self._transformToOrigin(coords)
            atoms = root.getAtoms()
            atoms.sort()
            confDict = {}
            for i in range(len(atoms)):
                confDict[atoms[i].name] = coords[i].tolist()
            self.conformation.append(confDict)            

        self.num_conformation = len(self.conformation)


    def getConf(self, index=0, includeBackBone=False):
        if index <  self.num_conformation:
            if includeBackBone:
                return self.conformation[index]
            else:
                return self.conformation[index]
        else:
            print 'Warning.. conformation index out of range'
            return None


    def _transformToOrigin(self, coords):
        """
        transform the residue so that
    1) CA in origin (0,0,0)
    2) CB on axis.
    3) C on (positive X)- (negative Y) plane
    
        """
        ats = self.residue.atoms
        CA = N.array(ats.get('CA')[0].coords)
        CB = N.array(ats.get('CB')[0].coords)
        C  = N.array(ats.get('C')[0].coords )
        rotmat = defineLocalCoordSys(CB,CA,C)
        mat= N.identity(4,'f')
        mat[:3,:3] = rotmat
        mat[:3,3] = CA.tolist()
        mat = N.transpose(mat)
        mat2 = inverse(mat)

        points = N.ones((len(coords),4),'f')
        points[:,:3] = coords
        result = N.dot(points, mat2)[:,:3]
        return result

from FlexTree.rotamer import Rotamer

class FTSoftRotamer(FTRotamer):
    """
Class for Rotameric amino acid side chains that deviate from ideal rotameric Chi angles
A FT tree with freely rotatable bonds is built, then configured by the angles
from rotamer library.
"""
    def __init__(self,  residue, angleDef, angleList ,name='Rotamer'):
        """ Constructor.
residue: one Residue instance
angleDef: 
    every angle is defned by list of 4 atom names(A):e.g. ['N','CA','C','O']
    followed by the atoms (B) that are moved by this rotation, e.g. ['CG']
    each row of angleDef is a list [A,B] 
    e.g. [['N', 'CA', 'C', 'O'], ['CG']]
    with n angles defined. n=len(angleDef)
    
angleList: m by n list.
           m conformations, each of which is defined by n angles

        """
        self.name = name
        self.residue = residue
        self.angle_def = angleDef

        # need to remove C, O and HN atoms but keep N and CA
        # to compute the original angles and compute rotation axis for CHI1
        atoms = residue.atoms.copy()
        # remove HN if found
        natom = residue.childByName['N']
        for b in natom.bonds:
            a1 = b.atom1
            if a1==natom: a1 = b.atom2
            if a1.element=='H':
                atoms.remove(a1)
        atoms.remove(residue.childByName['C'])
        atoms.remove(residue.childByName['O'])

        # build an objec to compute coordinates for rotamer side chain atoms
        self.rotamer = Rotamer(atoms, angleDef, angleList)

        self.conformation = []
        self.motionList = []
        for c in self.tree.root.children:
            self.motionList.append(c.motion)

        self.originalAngles=[]
        angleDefinition=[]
        # only need ['N', 'CA', 'C', 'O'], ignore the moving atom list
        for data in angleDef:
            angleDefinition.append(data[0])

        self.angleDef = angleDefinition

        for ang in self.angleDef:
            self.originalAngles.append(_getDihedralAngle(residue, ang))

        assert len(angleList[0]) == len(self.angleDef)

        self.angleList = angleList

        
    def getConf(self, index, deviations):
        angles = self.angleList[index]
        nb = len(self.angleDef)
        root = self.tree.root
        for i in range(nb):
            angle = angles[i] + deviations[i] - self.originalAngles[i]
            if angle < 0: angle += 360.
            elif angle > 360: angle -= 360.
            print 'FT_Rotamer getConf', i, angle, self.originalAngles[i]
            self.motionList[i].configure(angle=angle)
                
        root.newMotion = True
        root.updateCurrentConformation()

        # fixme.. getCurrentSortedConformation was not working properly
        coords = root.getCurrentSortedConformation2()
        #coords = self._transformToOrigin(coords)
        atoms = root.getAtoms()
        atoms.sort()
        confDict={}
        for i in range(len(atoms)):
            confDict[atoms[i].name] = coords[i]
        return confDict



class RotamerLib:
    def __init__(self, libFile, defFile, confFile=None):
        """
libFile: rotamer library file name
defFile: rotamer angle definition file name
confFile: conformation of amino acids. 
"""
        self.angleList= None
        self.angleDef = None
        self.loadRotamerLib(libFile, defFile)
        from MolKit import Read
        if confFile is None:
            import FlexTree
            confFile = os.path.join(FlexTree.__path__[0], 'AminoAcids.pdb')
            m = Read(confFile)[0]
            self.residues = m.chains[0].residues
        else:
            self.residues = None

    def loadRotamerLib(self, libFile, defFile):
        """ load backbone-independent rotamer library May 15, 2002
http://dunbrack.fccc.edu/bbdep/bbind02.May.lib.gz
libFile: bbind02.May.lib, all descriptive lines begin with '#'
defFile: define the chi angles and the atoms that are moved by the chi rotation

Roland L. Dunbrack, Jr., Ph. D.
Institute for Cancer Research, Fox Chase Cancer Center                  
7701 Burholme Avenue, Philadelphia PA 19111
"""
        try:
            input_file = file(libFile, 'r')
            lines=input_file.readlines()
        except:
            print "Error in opening ",libFile
            return 
        try:
            input_file = file(defFile, 'r')
            defLines =input_file.readlines()
        except:
            print "Error in opening ",defFile
            return 

        self.angleList = {}
        self.angleDef = {}
        self.angleStddev = {}
        rotlib = self.angleList
        angdef = self.angleDef
        angledev = self.angleStddev
        # parsing angle definition
        for line in defLines:
            data= line.split()
            if len(data) ==0:
                continue
            if data[0][0] == '#':
                continue                
            name = data[0]
                        
            X = data[1:5]
            moving = data[5:]
            if angdef.has_key(name):
                angdef[name].append([X, moving])
            else:
                angdef[name]= [[X, moving]]

        # parsing angleList
        name=''
        for line in lines:
            data= line.split()
            if len(data) ==0:
                continue
            if data[0][0] == '#':
                continue                
            name = data[0]            
            # hardwired code for parsing Dunbrack's lib
            number = (len(data) - 11)/2 # number of CHI angles
            chi_angles=[]
            stdev = []
            for i in range(number):
                chi_angles.append(float(data[11 + i*2]))
                stdev.append(float(data[12+ i*2]))
            if rotlib.has_key(name):
                rotlib[name].append(chi_angles)
                angledev[name].append(stdev)                
            else:
                rotlib[name]= [chi_angles]
                angledev[name]= [stdev]
            

    def get(self, residueName ):
        """ returns the angle definition and the angle lists of the residue (residueName) """
        
        if self.angleDef.has_key(residueName) and \
               self.angleList.has_key(residueName):
            return self.angleDef[residueName], self.angleList[residueName], \
                   self.angleStddev[residueName]
        
        else:
            print residueName, "is not found in the library"
            print self.angleDef.keys(), 'are defined'
            print self.angleDef.keys(), 'angles are loaded '            
            raise KeyError
                
    
    def getResidue(self, residueName):
        """Returns the Residue instance with name (residueName) """        
        names = self.residues.name
        found=False
        index = -1
        for i in range(len(names)):
            if residueName == names[i][:3] :
                found= True
                index = i
                break
        if not found :
            print 'Error ..', residueName, 'is not found'
            return None

        return self.residues[index]

        

## class FlexResidueSideChain(FlexTree):
##     """ Defines the Flexibility Tree (FT) of the side chain motion.
## """
##     def __init__(self, residue=None, name='Flexible SideChain'):
##         """ Constructor. Build FT for a residue"""

##         FlexTree.__init__(self, name)
##         # type-checing for residue
##         assert isinstance(residue, Residue)
##         self.residue = residue        
##         #self.pdbfilename = self.residue.top.parser.filename
##         self.buildFT()
        

##     def buildFT(self):
##         """vitual function that must be overriden  """
##         print 'should not see this line !!'
##         print 'Error Error Error'
##         pass

##     def buildRootNode(self):
##         """ build the root node of FT """
##         root = self.root = FTNode()
##         res = self.residue
##         root.id =  0
##         root.tree = weakref.ref(self)

##         root.configure(name=self.name , \
##                        molFrag = res, 
##                        selectionString= None,
##                        motion=FTMotion_Identity(),
##                        shape=None,
##                        shapeParams=None,
##                        refNode=None,             # set refNode ?  
##                        convolution=None,
##                        shapeCombiner=None,
##                        autoUpdateConf=True,
##                        autoUpdateShape=True )

##         self._addFTNode('core', ['N','CA','C','O','CB'], refName = None) # 'HN'
        
        
##     def _validateTree():
##         """private function, check if the FT just built includes all the atoms
## in the residue.

## fixme: should be moved ot FT class

## """
##         atoms = self.residue.getAtoms()
##         treeAtoms = self.root.getAtoms()

##         if len(atoms) > len(treeAtoms):
##             print "Error in FT building: some atoms are not assigned to any treenode"

##         return

##     def _addFTNode(self, name, atomNameList, refName, motion=None ):
##         """ private function called by BuildNode"""
##         root = self.root
##         res  = self.residue
##         #tree = self.tree()
        
##         ftn = FTNode()
##         fragment = AtomSet()
##         for n in atomNameList:
##             fragment.append(res.get(n)[0])

##         fragment.sort()
##         if refName is None:
##             refNode = weakref.ref(root)
##         else:
##             ref = self.getNodeByAtomName(refName)
##             refNode = weakref.ref(ref)

##         if motion is None:
##             motion=FTMotion_Identity()
            
            
##         ftn.configure(name=self.name+"_"+name , \
##                        molFrag = fragment, 
##                        selectionString= None,
##                        motion=motion,
##                        shape=None,
##                        shapeParams=None,
##                        refNode=refNode,                  # set refNode
##                        convolution=None,
##                        shapeCombiner=None,
##                        autoUpdateConf=True,
##                        autoUpdateShape=True
##                        )
##         root.addChildren([ftn])
##         #ftn.parent = weakref.ref(root)

        
##     def buildNode(self, axisPointsName, movingHeavyAtoms ):
##         """
## build a FTNode for movingHeavyAtoms, with a hinge motion defined by axisPointsName
## axisPointsName: list of two atom names(strings). e.g. ['CA'.'CB']
## movingHeavyAtoms: list of atom names that transformed by the hinge motion
##                   heaveAtoms: all but H

##         """
##         assert len(axisPointsName) is 2
##         num = len(self.root.children)
##         res = self.residue   
##         points = [res.get(axisPointsName[0]).coords[0], \
##                   res.get(axisPointsName[1]).coords[0]]
##         hingeMotion = FTMotion_Hinge(name='hinge'+str(num), points=points)

##         H_NameList = AtomSet()
##         found_H = False
## ##         for atomName in movingHeavyAtoms:
## ##             print 'bar',atomName,
## ##             atom=res.atoms.get(atomName)
## ##             print 'foo', atom
## ##             H = atom[0].findHydrogens()
## ##             if len(H) !=0:
## ##                 H =AtomSet(H)
## ##                 H_NameList += H
## ##                 found_H = True

##         atomName = axisPointsName[1]
##         atom=res.atoms.get(atomName)
##         H = atom[0].findHydrogens()
##         if len(H) !=0:
##             H =AtomSet(H)
##             H_NameList += H
##             found_H = True
        
##         if found_H:  # add the H, if any
##             #H_NameList = AtomSet(H_NameList)
##             movingHeavyAtoms += H_NameList.name

##         refAtom = res.atoms.get(axisPointsName[1])


##         if len(movingHeavyAtoms) > 0:
##             self._addFTNode(name = str(num), atomNameList =movingHeavyAtoms,
##                         refName = refAtom.full_name(), \
##                         motion=hingeMotion )

   

########  20 amino acides ########

## class FT_VAL(FlexResidueSideChain):

##     """rotamer based flextree for valine (VAL) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Valine  """
##         FlexResidueSideChain.__init__(self, residue=residue,  name=name)

    
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA', 'CB'], ['CG1', 'CG2'])
##         self.buildNode(['CB', 'CG1'], [] )
##         self.buildNode(['CB', 'CG2'], [] )

##         return



## class FT_ARG(FlexResidueSideChain):

##     """rotamer based flextree for Arginine (ARG) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Arginine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)

    
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue

## ##         self.buildNode(['CA','CB'],  ['CG'])
## ##         self.buildNode(['CB','CG'],  ['CD'])
## ##         self.buildNode(['CG','CD'],  ['NE'])
## ##         self.buildNode(['CD','NE'],  ['CZ'])
## ##         self.buildNode(['NE','CZ'],  ['NH1', 'NH2'])
## ##         self.buildNode(['CZ','NH1'], [] ) # will add H  to the tree, if any
## ##         self.buildNode(['CZ','NH2'], [] )

##         self.buildNode(['CA','CB'],  ['CG'])
##         self.buildNode(['CB','CG'],  ['CD'])
##         self.buildNode(['CG','CD'],  ['NE'])
##         self.buildNode(['CD','NE'],  ['CZ', 'NH1', 'NH2'])
        
##         return



## class FT_HIS(FlexResidueSideChain):

##     """rotamer based flextree for Histidine (HIS) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Histidine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)

    
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'],  \
##                        ['CG', 'ND1', 'CE1', 'NE2', 'CD2', 'HE2', 'HD1'])
        
##         return


## class FT_PHE(FlexResidueSideChain):

##     """rotamer based flextree for Pheylalanine (PHE) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Pheylalanine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)

    
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'],  \
##                        ['CG', 'CD1', 'CE1', 'CZ', 'CE2', 'CD2'])
        
##         return


## class FT_TYR(FlexResidueSideChain):
##     """rotamer based flextree for Tyrosine (TYR) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Tyrosine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)
## 	# name = 'Tyrosine')

    
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'],  \
##                        ['CG', 'CD1', 'CE1', 'CZ', 'CE2', 'CD2', 'OH'])
##         self.buildNode(['CZ','OH'], [] ) # HH, if any
##         return



## class FT_THR(FlexResidueSideChain):

##     """rotamer based flextree for Threonine (THR) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Threonine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name= name)

    
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'],  \
##                        ['CG2', 'OG1'])
## 	self.buildNode(['CB','OG1'], [] ) # HG1, if any
##         return


## class FT_CYS(FlexResidueSideChain):

##     """rotamer based flextree for Cysteine (CYS) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Cysteine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)

   
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'],  \
##                        ['SG'])        
##         return

## class FT_LEU(FlexResidueSideChain):
##     """rotamer based flextree for Leucine (LEU) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Leucine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)

   
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'], ['CG'])
## 	self.buildNode(['CB','CG'], ['CD1', 'CD2'])
##         return


## class FT_LYS(FlexResidueSideChain):
##     """rotamer based flextree for Lysine (LYS) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Lysine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)
   
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'], ['CG'])
## 	self.buildNode(['CB','CG'], ['CD'])
## 	self.buildNode(['CG','CD'], ['CE'])
## 	self.buildNode(['CD','CE'], ['NZ'])
## 	self.buildNode(['CE','NZ'], [])	# HZ1, HZ2, HZ3
##         return


## class FT_GLU(FlexResidueSideChain):
##     """rotamer based flextree for Glutamic acid (GLU) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Glutamic acid  """
##         FlexResidueSideChain.__init__(self, residue=residue, name=name)
   
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'], ['CG'])
## 	self.buildNode(['CB','CG'], ['CD'])
## 	self.buildNode(['CG','CD'], ['OE1','OE2'])
##         return


## class FT_GLN(FlexResidueSideChain):
##     """rotamer based flextree for Glutamine (GLN) """
##     def __init__(self, residue=None, name='rotamer'):
##         """ FT for Glutamine  """
##         FlexResidueSideChain.__init__(self, residue=residue, name = name)
   
##     def buildFT(self):
##         self.buildRootNode()
##         res = self.residue
##         self.buildNode(['CA','CB'], ['CG'])
## 	self.buildNode(['CB','CG'], ['CD'])
## 	self.buildNode(['CG','CD'], ['OE1','NE2'])
## 	self.buildNode(['CD','NE2'], []) # HE21, HE22
##         return

# fixme... not all 20 of them yet !
# Note: as of March 2005. The class FT_XXX are all abandoned
# Use the FlexResidue instead !
########  end of 20 amino acides ########



## class FlexResidue(FlexTree):
##     """
## Amino acid with flexible side chain (from rotamer library)
## """
##     def __init__(self, angleDef, residue=None, name=''):
##         """constructor
## angleDef: the list of four angles that defines the torsion angles
## residue : the Residue instance, to which the rotamer lib is applied

## """
##         FlexTree.__init__(self, name)
##         # type-checking for residue
##         assert isinstance(residue, Residue)
##         self.residue = residue
##         self.angleDef = angleDef
##         self.buildFT()
##         assert self._validateTree() 


##     def buildRootNode(self):
##         """ build the root node of FT """
##         root = self.root = FTNode()
##         res = self.residue
##         root.id =  0
##         root.tree = weakref.ref(self)

##         root.configure(name=self.name+"_root" , \
##                        molFrag = None, 
##                        selectionString= None,
##                        motion=FTMotion_Identity(),
##                        shape=None,
##                        shapeParams=None,
##                        refNode=None,             # set refNode ?  
##                        convolution=None,
##                        shapeCombiner=None,
##                        autoUpdateConf=True,
##                        autoUpdateShape=True )

##         moving=[]
##         for i in range(len(self.angleDef)):
##             moving.extend(self.angleDef[i][1])

##         core = self.residue.atoms[:]
##         # only keep the core (backbone) atoms in the 'core' node
##         for name in moving:            
##             # find moving atom to remove them from core
##             # also look for H attached to moving atoms and remove them too
##             tmp = core.objectsFromString(name)
##             if tmp:
##                 for atom in tmp:
##                     # remove all H bound to moving atom
##                     H = atom.findHydrogens()
##                     if len(H) !=0:
##                         for h_atom in H:
##                             core.remove(h_atom)
##                 core.remove(tmp[0]) # remove moving atoms

##         # now only backbone atoms are kept
##         coreAtomNames = core.name
##         self._addFTNode('core', coreAtomNames, refName = None)

        
##     def buildFT(self):
##         """build FT for the side chain"""
##         #self.buildRootNode()
##         root = self.root = FTNode()
##         res = self.residue
##         root.id =  0
##         root.tree = weakref.ref(self)
##         root.configure(name=self.name+"_root" , \
##                        molFrag = None, 
##                        selectionString= None,
##                        motion=FTMotion_Identity(),
##                        shape=None,
##                        shapeParams=None,
##                        refNode=None,             # set refNode ?  
##                        convolution=None,
##                        shapeCombiner=None,
##                        autoUpdateConf=True,
##                        autoUpdateShape=True )

##         res = self.residue
##         nbr = len(self.angleDef)

##         #ref = root
##         ref = None
##         for i in range(nbr):
##             ref = self.buildNode( self.angleDef[i][0], self.angleDef[i][1], ref)
## ##         for i in range(nbr):
## ##             if i != nbr-1: 
## ##                 self.buildNode( self.angleDef[i][0], self.angleDef[i][1])
## ##             else: # the last angle
## ##                 self.buildNode( self.angleDef[i][0], self.angleDef[i][1], True)


##     def _validateTree(self):
##         """private function, check if the FT just built includes all the atoms
## in the residue.
## fixme: shoudl be moved ot FT class
## """
##         return True
##         atoms = self.residue.getAtoms()
##         treeAtoms = self.root.getAtoms()


##         if len(atoms) > len(treeAtoms):
##             print "Error in FT building: some atoms are not assigned to any treenode"
##             print atoms.name
##             print treeAtoms.name

##             return False

##         return True


##     def buildNode(self, axisPointsName, movingHeavyAtoms, refNode):
##         """
## build a FTNode for movingHeavyAtoms, with a FTMotion_RotationAboutAxis defined by axisPointsName
## axisPointsName: list of two atom names(strings). e.g. ['CA'.'CB']
## movingHeavyAtoms: list of atom names that transformed by the hinge motion
##                   heaveAtoms: all but H
##         """
##         assert len(axisPointsName) is 4
##         num = len(self.root.children)
##         res = self.residue

##         # axis is from axisPointsName[1], to axisPointsName[2]
##         points = [res.get(axisPointsName[1]).coords[0], \
##                   res.get(axisPointsName[2]).coords[0]]
##         motion = FTMotion_RotationAboutAxis(name='Chi'+str(num), points=points)

##         H_NameList = AtomSet()
##         found_H = False       

##         atom = res.get(axisPointsName[2])
##         H = atom[0].findHydrogens()
##         if len(H) !=0:
##             H = AtomSet(H)
##             H_NameList += H
##             found_H = True

##        # if lastNode:
##             #print 'last node'
##             #print "***", movingHeavyAtoms
##         for atomName in movingHeavyAtoms:
##             atom = res.atoms.get(atomName)
##             H1 = atom[0].findHydrogens()
##             if len(H1) != 0:
##                 H1 = AtomSet(H1)
##                 H_NameList += H1
##                 found_H = True

##         if found_H:  # add the H, if any
##             #H_NameList = AtomSet(H_NameList)
##             movingHeavyAtoms += H_NameList.name
            
##         #refAtom = res.atoms.get(axisPointsName[2])

##         if len(movingHeavyAtoms) > 0:
##             node = self._addFTNode(str(num), movingHeavyAtoms,
##                                    refNode, motion=motion )
##                             #refName=refAtom.full_name(), motion=motion )
##             return node
##         else:
##             return None

        
##     #def _addFTNode(self, name, atomNameList, refName, motion=None ):
##     def _addFTNode(self, name, atomNameList, refNode, motion=None ):
##         """ private function called by BuildNode"""
##         root = self.root
##         res  = self.residue
##         #tree = self.tree()
        
##         ftn = FTNode()
##         fragment = AtomSet()
##         for n in atomNameList:
##             at = res.get(n)
##             if len(at)>1:
##                 raise ValueError, "atoms with identical name (%s) in residue %s"%(n, res.full_name())
##             fragment.append(at[0])

##         fragment.sort()
##         #if self.residue.name == 'ARG76': print "Name of current AtomSet",fragment.name
##         ## if refName is None:
##         ##     #refNode = weakref.ref(root)
##         ##     refNode = root
##         ## else:
##         ##     refNode = self.getNodeByAtomName(refName)

##         if motion is None:
##             motion = FTMotion_Identity()
            
##         ftn.configure(name=self.name+"_"+name , \
##                       molFrag = fragment, 
##                       selectionString= None,
##                       motion=motion,
##                       shape=None,
##                       shapeParams=None,
##                       refNode=refNode,                  # set refNode
##                       convolution=None,
##                       shapeCombiner=None,
##                       autoUpdateConf=True,
##                       autoUpdateShape=True
##                       )
##         root.addChildren([ftn])
##         #ftn.parent = weakref.ref(root)
##         return ftn
    
##
## end of file
