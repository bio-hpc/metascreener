## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

########################################################################
#
# Date: jan 2004 Author: Michel Sanner, Daniel Stoffler
#
#    sanner@scripps.edu
#    stoffler@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner, Daniel Stoffler, and TSRI
#
#########################################################################

"""
This module implements the base objects used for building a flexibility tree
(FT).
"""
VERBOSE= 0 # no verbose
#VERBOSE= 1 # printing debugging info


from MolKit.molecule import Atom, AtomSet, MoleculeSet
from MolKit.protein import Residue, ResidueSet

from MolKit.tree import TreeNode, TreeNodeSet

from FlexTree.FTMotions import FTMotion, FTMotion_Discrete,defineLocalCoordSys\
     ,FTMotionCombiner
from FlexTree.FTMotions import FTMotion_Rotamer
from FlexTree.FTShapes import FTShape
from FlexTree.FTConvolutions import FTShapeMotionConvolve, FTConvolveIdentity,\
     FTConvolveApplyMatrix
from FlexTree.FTShapeCombiners import FTShapesCombiner

from MolKit.stringSelector import CompoundStringSelector

import weakref, types, string
import numpy


class FlexTree:
    """Base class for a flexibility tree
"""

    def __init__(self, name='flextree', filename=None, mol=None):
        self.name = name
        self.root = None          # root node of the tree
        self.pdbfilename = None   # path and filename of pdb file
        self.xmlfilename = None   # path and filename of xml file
        self._uniqNumbers = {}    # dict holding all uniq numbers:
                                  # key: id, value: FTNode instance
        self._uniqCount = 0       # used to generate unique numbers

        self.rotamerOnly=False     # only rotamer motions available

        if filename!=None:
            from MolKit import Read
            mol=Read(filename)[0]
        self.mol=None
        if mol:
            allAtoms=mol.allAtoms
            self.pdbfilename=mol.parser.filename
            self.root=root=FTNode()
            self.createUniqNumber(root)            
            root._tree = self
            root.tree = weakref.ref(root._tree)
            self.root.configure(molFrag=allAtoms, name=mol.name)
            self.mol=mol

        self.rigidNodeList = []
        self.flexNodeList = []


    def save(self, xmlfilename):
        from FlexTree.XMLParser import WriteXML
        writer = WriteXML(self)
        writer([self], xmlfilename)
        return


    def saveCoords(self, filename):  ### fixme.. on-going.. never debugged.
        coords = self.getCurrentConformation()
        atoms=self.root.getAtoms()[:]
        #atoms.updateCoords(coords, 0)  #?!
        atoms.updateCoords(coords, 1)  
        atoms.sort()
	from MolKit.pdbWriter import PdbWriter
        writer = PdbWriter()
        writer.write(filename, atoms, records=['ATOM', 'HETATM', 'CONECT'])
        return


    def load(self, xmlfilename):
        pass


    def createUniqNumber(self, ftNode, uniqNumber=None):
        """generate a unique number that does not exist yet."""
        assert isinstance(ftNode, FTNode)

        if uniqNumber is not None:
            # Note: we cannot have an xml file where some nodes do have an id
            # set and some do not, this can cause problems like here:
            assert uniqNumber not in self._uniqNumbers.keys()

            ftNode.id = uniqNumber
            self._uniqNumbers[uniqNumber] = ftNode
            return

        c = self._uniqCount
        # find next available unique number
        l = self._uniqNumbers.keys()
        l.sort()
        while c in l:
            c = c + 1
        # update dictionary and return
        ftNode.id = c
        self._uniqCount = c
        self._uniqNumbers[c] = ftNode


    def _getAllMotion(self, node, objList):
        """helper function to recursively return all motion objects"""
        motion = node.motion
        if motion is not None:
            objList.append(motion)
        disMoton=node.discreteMotion
        if disMoton is not None:
            objList.append(disMoton)      
            
        for child in node.children:
            objList = self._getAllMotion(child, objList)
        return objList
    
        
    def getAllMotion(self):
        """return list of all motion objects in the tree"""
        if self.root is None:
            return
        return self._getAllMotion(self.root, [])


    def adoptRandomConformation(self):
        """FlexTree adopts a random conformation"""
        if self.root is None:
            return
        self._randomize(self.root)
        self.root.newMotion=True


    def _randomize(self, node):
        """recursively call randomize() method of motion objects (if assigned),in all FlexTree nodes""" 

        motion = node.motion
        if motion is not None:
            if motion.can_be_modified:
                motion.randomize()
            #node.newMotion=True #?

        discreteMotion = node.discreteMotion
        if discreteMotion is not None:
            if discreteMotion.can_be_modified:
                discreteMotion.randomize()
            #node.newMotion=True #?
            
        for child in node.children:
            self._randomize(child)


    def getNodeByName(self, name, node=None):
        """recursive function to find and return FTNode by name"""
        if node is None:
            node = self.root

        if node.name == name:
            return node
        else:
            for child in node.children:
                n = self.getNodeByName(name, child)
                if n is not None:
                    return n


    def getNodeByAtomName(self, name, node=None):
        """recursive function to find and return FTNode by atom full name"""
        if node is None:
            node = self.root

        if len(node.children) == 0:
            if node.molecularFragment is  None:
                print "Error in tree, leaf node doesn\'t have molFrag"
            else:
                if not isinstance(node.molecularFragment, AtomSet):
                    #atoms = node.molecularFragment.atoms
                    atoms = node.molecularFragment.findType(Atom)
                    found=False
                    for at in atoms:
                        if at.full_name() ==name:
                            found=True
                            break
                    if found:
                        return node
                    else:
                        return None
                else:
                    atoms = node.molecularFragment
                    for a in atoms:
                        if a.full_name() == name:
                            return node
                    return None

        else:
            for child in node.children:
                n = self.getNodeByAtomName(name, child)
                if n is not None:
                    return n
        return None
    
 
    def buildFlexSideChain(self, residueFullName):
        """
        Make the side chain of residue (residue name) flexible, adding the sub FT to the proper position of 'self'
        residueFullName: string of 'molecule:chain:res'
NOTE: This will add the hinge motion to all the rotatable bonds.
      NOT the rotamers !
      NOT the rotamers !
      
        """
        names=residueFullName.split(':')
        assert len(names) == 3

        res = self.root.getAtoms().parent.uniq().objectsFromString(names[2])
        res = ResidueSet(res)
        idx = res.full_name().split(';').index(residueFullName)
        if idx == -1:
            print "Residue %s not found"%(residueFullName)
            return 
        res = res[idx]

        fullName = str(res.atoms.get('CA').full_name())
        node = self.getNodeByAtomName(fullName)
        if node is None:
            print "Warning: ", residueFullName, "not found in the tree"
            print
            print res, res.atoms.get('CA').full_name()
            return

        if len(node.molecularFragment.findType(Atom)) <  len(res.atoms):
            print "Warning: ", residueFullName, "is already assinged "
            print
            return

        from FlexTree.FTRotamers import _chooseFlexResidueSideChainClass
        flexRes = _chooseFlexResidueSideChainClass(res.name)
        chainFT = flexRes(name=names[2], residue = res)
        #chainFT = flexRes(name=residueFullName, residue = res)        

        #self.addSubTree(node.parent(), chainFT)
        self.addSubTree(node, chainFT)        

        # fixme.. generate loooong name at Atom level
        node.molecularFragment = node.molecularFragment.findType(Atom)  - res.atoms
        node.configure( molFrag= node.molecularFragment )        
        
        return 



    def addSubTree(self, node, newTree):
        """ This function merges a newTree (FlexTree) as a subtree of self.
The subtree will be appended as a child of 'node'.

node: the root where new subtree will be added
newTree: a FlexTree instance
"""
        root = newTree.root
        node.addChildren([root])
        self.createUniqNumber(root)
        root.tree = weakref.ref(self)
        #print 'Now, ', root.id, self._uniqNumbers.keys(), self._uniqCount
        root.updateIDs()


    def addRotamerToRootNode(self, res):
        """ add sidechains of residue as a child node of self.root """

        validRotamerName=['CYS', 'GLN', 'ILE', 'SER', 'VAL', 'LYS', 'TRP', 'PRO', 'THR', 'PHE', 'GLU', 'MET', 'HIS', 'LEU', 'ARG', 'ASP', 'ASN', 'TYR']

        print "Adding rotamer\t",res.full_name()
        if res.name[:3] not in validRotamerName:
            print 'No rotamer defined for' , res.name
            return False


        tree=self
        root=tree.root
        if len(root.children)==0:
            # add core node, if not available
            core=root.getAtoms()[:]
            node0=FTNode(molFrag=core, name="Core")
            node0._tree = tree
            node0.tree = weakref.ref(node0._tree)
            tree.createUniqNumber(node0)
            root.addChildren([node0])

        coreNode=root.children[0]
        from FlexTree.utils import getSameAtomsfrom

        # the res and tree are not from the same MolKit.Molecule
        # although they are read from the same file
        resAtoms=getSameAtomsfrom(res.atoms, root.getAtoms())

        #see notes <1> at end of FTGA.py
        sidechain=resAtoms.get('sidechain')-resAtoms.get('CB')

        anchor=[]
        for name in ['CB','CA','C']:
            anchor.append(resAtoms.get(name)[0])
        anchor=AtomSet(anchor)


        motion=FTMotion_Rotamer()
        motion.configure(sideChainAtomNames=sidechain.name)

        node1=FTNode(discreteMotion=motion, name=res.full_name()+'_rotamer',
                     molFrag= sidechain,
                     #refNode=coreNode,
                     refNode=coreNode,
                     anchorAtoms=anchor
                     )

        root.addChildren([node1])
        node1._tree = tree
        node1.tree = weakref.ref(node1._tree)
        tree.createUniqNumber(node1)

        core = coreNode.getAtoms()
        k=len(core)
        core = core-resAtoms.get('sidechain')
        core = core+resAtoms.get('CB')
        coreNode.configure(molFrag=core)
  
        motion._buildConfList()

        return True


    def noShapeUpdate(self):
        """FlexTree does not update any shape.
This is useful for command-line based calculation, where no GUI is involved.
"""
        #### fixme.. not implemented.

        #  loop over nodes and set autoUpdateShape =False
        if self.root is None:
            return
        
    def getCurrentConformation(self):
        """get current of the FlexTree. This function returns the current
conformation of root node"""
        if self.root is not None:
            return self.root.getCurrentConformation()
        else:
            return None


    def isRotamerOnly(self):
        """
        return True if all motions are rotamer motions, False otherwise.
        """
        allMotions=self.getAllMotion()
        if len(allMotions)==0: # no motion
            return False
        rotamerOnly=True
        for m in allMotions:
            if m.__class__.__name__ != "FTMotion_Rotamer":
                rotamerOnly=False
                break

        self.rotamerOnly=rotamerOnly
        return rotamerOnly

    def removeBadRotamers(self):
        """ if the only motion type in the tree is FTMotion_Rotamer, this
function will remove all the conformations that clash with rigid atoms

"""
        if VERBOSE:
            print " --removeBadRotamers"
        
        if self.isRotamerOnly()==False:
            print "Motion object other than FTMotion_Rotamer is found"
            return

        allMotions=self.getAllMotion() # all rotamer motions
        sideChainAtoms=[]
        for m in allMotions:
            sideChainAtoms.extend( m.node()._getAtoms() )
            
        sideChainAtoms=AtomSet(sideChainAtoms)
        rigidAtoms= self.root.getAtoms() - sideChainAtoms

        for m in allMotions:
            m.removeClashWith(rigidAtoms)
        return
    

    def updateStatus(self):
        """ each FTNode has an attribute 'rigid'. If no motion ever applied to this node, node.rigid=True. This is used to reduce redundant calculation.  """

        if self.root.motion is None and self.root.discreteMotion is None:
            self.root.rigid=True            
        else:
            self.root.rigid=False
        if len(self.root.children)==0:
            if self.root.rigid:
                self.rigidNodeList.append(self.root)
            else:
                self.flexNodeList.append(self.root)

        for node in self.root.children:
            self._updateStatus(node)
        return
    
        
    def _updateStatus(self, node):
        if node.motion is not None or node.discreteMotion is not None:
            node.rigid=False
            
        if len(node.children)==0:
            if node.rigid:
                self.rigidNodeList.append(node)
            else:
                self.flexNodeList.append(node)
            
        for ch in node.children:
            self._updateStatus(ch)
        return

    
##     def getMovingAtoms(self):
##         """ get all the moving (flexible) atoms """
##         if not hasattr(self, 'allMotions'):
##             self.allMotions=self.getAllMotion()
##         if not hasattr(self, 'flexAtoms'):
##             flexAtoms=[]
##             for m in self.allMotions:
##                 flexAtoms.extend( m.node()._getAtoms() )   
##             self.flexAtoms=AtomSet(flexAtoms)
##         return self.flexAtoms
    
##     def getRigidAtoms(self):
##         """ get all the rigid (fixed) atoms """
##         if not hasattr(self, 'rigidAtoms'):
##             self.rigidAtoms=self.root.getAtoms()-self.getMovingAtoms()
##             self.rigidAtoms.sort()
##             self.rigidAtomsCoords=self.rigidAtoms.coords            
##         return self.rigidAtoms

    def getMovingAtoms(self):
        """ get all the moving (flexible) atoms """
        if not hasattr(self, 'flexAtoms'):
            flexAtoms=[]
            for node in self.flexNodeList:
                flexAtoms.extend( node.getAtoms() )   
            self.flexAtoms = AtomSet(flexAtoms)
        return self.flexAtoms

    def getRigidAtoms(self):
        """ get all the rigid (fixed) atoms """
        if not hasattr(self, 'rigidAtoms'):
            rigidAtoms=[]
            for node in self.rigidNodeList:
                rigidAtoms.extend( node.getAtoms() )   
            self.rigidAtoms=AtomSet(rigidAtoms)
            #self.rigidAtoms.sort()
            #self.rigidAtomsCoords=numpy.array(self.rigidAtoms.coords, 'f')
            self.rigidAtomsCoords=self.rigidAtoms.coords
        return self.rigidAtoms
            
    def getMovingAtomCoords(self):
        """ get currrentConf of all flexible nodes """        
        coords=[]
        for node in self.flexNodeList:
            coords.extend(node.currentConf)
        return coords


    def getRigidAtomCoords(self):
        """ get currrentConf of all rigid nodes """
        if not hasattr(self, 'rigidAtomsCoords'):
            self.getRigidAtoms()
        return self.rigidAtomsCoords


    def newNode(self, **kw):
        node0 = FTNode(**kw)
        node0._tree = self
        node0.tree = weakref.ref(node0._tree)
        self.createUniqNumber(node0)
        return node0



class FTNode:
    """Base class of a Flexibility Tree node """

    def __init__(self, **kw):
        """constructor
valid keywords are:
name: node name
molFrag: set of TreeNodes from MolKit describing apart of a molecule
motion: an FTMotion object
shape: an FTShape object

discreteMotion: motion object that changes rigid conformation of the molecular
             fragment.. e.g.  pick one out of n conformations. normal mode
             motion, pick one of the rotamers.. etc.
"""

        # tree related attributes
        self.name = 'node'
        self.children = []   # will be an instance of a FTNodeSet
        self.parent = None   # will be a weakref to an FTNode
        self.tree = None     # will be a weakref to a FlexTree
        self.id = None       # unique number,
                             # assigned through the build tree process

        # molecule related attributes
        self.molecularFragment = None # subset of a molecule that is considered
                                      # to be rigid at this level of the tree
        self.selectionString = None   # string describing molecularFragment

        self.newAtoms = False         # flag switched to True if new atoms

        # motion related attributes
        self.refNode = None
        self.refFrame = numpy.identity(4).astype('f')
                                      # reference frame related to parent node
        self.localFrame = numpy.identity(4).astype('f')# 4x4 transformation
                                      # matrix defining the coordinate system
                                      # in which this node moves
                               
        self.motion = None            # motion operator
        self.newMotion = False

        self.discreteMotion = None       # local motion that deforms the rigid
                                      # rigid molecular fragment..
        self.anchorAtoms = None
        
        self.localConf = None         # coordinate changed by discreteMotion

        self.originalConf = None      # these atomic coordinate do not change
        self.currentConf = None       # current, transformed coordinates
        self.autoUpdateConf = True    # update current conformation whenever
                                      # the motion is configured
        
        # shape related attributes
        self.shape = None      # will be an FTShape object
        self.newShape = False

        # motion-shape convolution
        self.convolveShapeWithMotion = FTConvolveApplyMatrix(self)
        self.refBy = []            # list of nodes whose refNode is this node  
                                   # refBy is used for convolution operation
        # shape combination
        self.shapeCombiner = None  # instance of FTShapesCombiner
        self.combinedShape = None  # will store the result of combining
                                   # shapes of children nodes
        self.autoUpdateShape=True  # update current shape whenr motion is configured
        self.rigid         =True   # no motion ever applied? True or False
        #self.foo=0
        ###self.active = True
        self.configure(**kw)
        #apply( self.configure, (), kw)


    def getSelString(self, atoms):
        """ return selection string at residue level.
e.g. atoms with name
1crn: :CYS3:N;1crn: :CYS3:CA;1crn: :CYS3:C;1crn: :CYS3:O;1crn: :CYS3:CB;1crn: :CYS3:SG;1crn: :CYS4:N;1crn: :CYS4:CA;1crn: :CYS4:C;1crn: :CYS4:O;1crn: :CYS4:CB;1crn: :CYS4:SG;1crn: :PRO5:N;1crn: :PRO5:CA;1crn: :PRO5:C;1crn: :PRO5:O;1crn: :PRO5:CB;1crn: :PRO5:CG;1crn: :PRO5:CD;1crn: :SER6:N;1crn: :SER6:CA;1crn: :SER6:C;1crn: :SER6:O;1crn: :SER6:CB;1crn: :SER6:OG
should be consolidated at residue level as '1crn: :CYS3,CYS4,PRO5,SER6', if equivalent..
This is useful to reduce the length of selection string in XML (easier to read)


"""
        #return atoms.getStringRepr()
    
        ##fixme should use getStringRepr
        # error when mixed residual level with atoms levels
        ## return atoms.getStringRepr()

        assert len(atoms) != 0
        residues = atoms.parent.uniq()
        residues.sort()
        if len(residues.atoms)  == len(atoms):
            return residues.full_name()
        resWithAllMembers = ResidueSet()
        atomsFromPartialResidue = AtomSet()
        data=AtomSet(atoms)
        data.sort()
        for r in residues:
            length = len(r.atoms)
            all =  data[:length].parent.uniq()
            
            first = all[0]
            if len(all) == 1 and len(data[:length]) >= length:
                # only one residue found
                resWithAllMembers.append(first)
                del data[:length]
            else:
                num = 0
                for atom in data[:length]:
                    if atom in first.atoms:
                        atomsFromPartialResidue.append(atom)
                        num +=1
                del data[:num]

        names=""
        chains=residues.parent.uniq()
        for chain in chains:
            resInCurrentChain=ResidueSet()
            for r in resWithAllMembers:
                if r in chain.residues:
                    resInCurrentChain.append(r)
            if len(resInCurrentChain):
                names+=resInCurrentChain.full_name()
                names += ':;'
            
        names += atomsFromPartialResidue.full_name()
        return names

        
    def configure(self, name=None, molFrag=None, selectionString=None,
                  motion=None, motionParams=None,
                  shape=None, shapeParams=None,
                  refNode=None, convolution=None,
                  shapeCombiner=None, autoUpdateConf=None,
                  autoUpdateShape=None,
                  discreteMotion=None,
                  anchorAtoms=None,
                  discreteMotionParams=None):
        
        """configuration method. Allows to set all attributes of this node
refNode should be an instance of FTNode, not the weak reference
"""

        if name is not None:
            self.name = name

        if autoUpdateConf is not None:
            self.autoUpdateConf = autoUpdateConf

        if autoUpdateShape is not None:
            self.autoUpdateShape = autoUpdateShape

        if selectionString is not None:
            self.selectionString = selectionString
##             print 'called..', self.name
##             print selectionString
##             print '----------'

        if discreteMotion is not None:
            assert isinstance(discreteMotion, FTMotion_Discrete)
            self.discreteMotion=discreteMotion
            self.newMotion = True
            # need this? fixme
            self.discreteMotion.node = weakref.ref(self)

        newMolFrag = False
        if molFrag is not None:
            assert isinstance(molFrag, TreeNode) or \
            isinstance( molFrag, TreeNodeSet)

            if isinstance(molFrag, TreeNodeSet):
                molFrag.sort()
            self.molecularFragment = molFrag.findType(Atom)
            
            self.newAtoms = True
            # also set self.originalConf:
            if isinstance(self.molecularFragment, TreeNodeSet):
                atoms = self.molecularFragment.findType(Atom)
            else:
                atoms = self.molecularFragment.getAtoms()

            currentConfNumber= atoms[0].conformation

            if  currentConfNumber==0:
                self.originalConf = atoms.coords
            else:
                atoms.setConformation(0)
                self.originalConf = atoms.coords
                atoms.setConformation(currentConfNumber)

            # set the local Conf.. ( can only changed by discreteMotion)
            self.localConf=self.originalConf
            
            # add another conformation here, next time when refer to
            # atoms.coords, the updated (current) coords are returned
            atoms.sort()
            confNB = len(atoms[0]._coords)

            # the _coords[0] is the original coords as in PDB file
            # the _coords[1] is the transformed coords after FlexTree motion
            if  confNB == 1 :
                atoms.addConformation(atoms.coords)
                atoms.setConformation(1)
            elif confNB == 2:
                atoms.setConformation(1)
            elif confNB == 3:
                #print "3 conformations found"
                pass
            else:
                print "Warning: Only one or two conformations are allowed."
                print "Found", confNB
                print "*********************************"

            # overwrite the selectionString, if molFrag is specified
            #self.selectionString = self.molecularFragment.full_name()
            self.selectionString = self.getSelString(atoms)

            self.currentConf = numpy.array(atoms.coords,'f')
                
        if refNode is not None:
            refType = type(refNode)
            if refType is types.IntType:
                if self.tree  :
                    refNode = self.tree()._uniqNumbers[refNode]
                else:
                    print 'WARNING: weakref "tree" not found !'
            elif refType is weakref.ReferenceType:
                self.refNode = refNode
                print "Warning: Got a weakref as refNode..."                
            else :
                self.refNode = weakref.ref(refNode)
                self.refFrame = self.refNode().getLocalFrame()
                self.refNode().refBy.append(self)

        if anchorAtoms is not None:
            # anchorAtoms given as list of full_atom_name
            if self.molecularFragment is None:
                pass
            else:
                # for now. only support CB-CA-C as anchor atoms
                assert len(anchorAtoms) == 3

                if type(anchorAtoms[0])==types.StringType:
                    frag = self.molecularFragment.findType(Atom)
                    frag=frag.parent.uniq().atoms
                    anchors=AtomSet()
                    anchors.append(frag.get(anchorAtoms[0])[0])
                    anchors.append(frag.get(anchorAtoms[1])[0])
                    anchors.append(frag.get(anchorAtoms[2])[0])
                    anchorAtoms=anchors
                    
                assert anchorAtoms[0].name=='CB'
                assert anchorAtoms[1].name=='CA'
                assert anchorAtoms[2].name=='C'
                self.anchorAtoms = anchorAtoms
                # make sure 3 conformations with anchors
                # 0: original PDB coords
                # 1: FlexTree transformed coords
                # 2: discrete motion transformed coords
                confNB=len(anchorAtoms[0]._coords)
                if confNB==1:
                    self.anchorAtoms.addConformation(anchorAtoms.coords)
                    self.anchorAtoms.addConformation(anchorAtoms.coords)
                elif confNB==2:
                    self.anchorAtoms.addConformation(anchorAtoms.coords)
                else:
                    pass
                    
        if motion is not None:
            assert isinstance(motion, FTMotion)
            self.newMotion = True
            self.motion = motion
            self.motion.node = weakref.ref(self)

        if motionParams is not None:
            apply( self.motion.configure, (), motionParams)
            # have to do this because..when start from Vision,
            # motion node doesn't know FTNode...
            if not self.motion.node :
                self.motion.node = weakref.ref(self)
            else: # make sure we do this only once
                pass
            self.newMotion = True

        if discreteMotionParams is not None:
            apply( self.discreteMotion.configure, (), discreteMotionParams)
            # have to do this because..when start from Vision,
            # motion node doesn't know FTNode...
            if not self.discreteMotion.node :
                self.discreteMotion.node = weakref.ref(self)
            self.newMotion = True

        if convolution is not None:
            assert isinstance(convolution, FTShapeMotionConvolve)
            self.convolveShapeWithMotion = convolution

        if shapeCombiner is not None:
            assert isinstance(shapeCombiner, FTShapesCombiner)
            self.shapeCombiner = shapeCombiner

        if shape is not None:
            assert isinstance(shape, FTShape)
            if self.shape is not None and self.shape != shape \
                   and self.shape.ownsGeom:
                # remove the old shape, if there's any
                for g in self.shape.geoms:
                    if g.viewer:
                        print 'removing shape', g
                        g.viewer.RemoveObject(g)

            self.shape = shape
            self.shape.node = weakref.ref(self)
            self.newShape = True
            self.shape.hasBonds=False
            self.shape.updateGeoms()

            # we do this to avoid the geoms having same name..
            geomName=self.shape.__class__.__name__ + "_" +self.name
            self.shape.geoms[0].Set(name=geomName)
        
        if shapeParams is not None:
            apply( self.shape.configure, (), shapeParams)
            self.shape.updateGeoms()

        # update from Vision Interface
        # also as flag to make sure localframe is calculated only once
        if self.newMotion == True:
            if self.autoUpdateConf:
                self.updateCurrentConformation( updateAtom = True)
                # set the flag so that
                # updateConvolution() doesn't update localframe again
                self.newMotion=False 

            if self.autoUpdateShape and self.shape:
                self.updateConvolution()
                
            self.newMotion=False
        return
    

    def getLocalFrame(self,anchorAtoms=None):
        """ returns the local frame of self.
if anchorAtoms is specified and this node (self) has local discrete motion.
the localFrame for the anchorAtoms will be returned

anchorAtoms: Atom instance
"""
        
        if VERBOSE:
            if anchorAtoms:
                print 'FTNode %s ::getLocalFrame, anchorAtoms=%s'%(\
                    self.name, anchorAtoms.name), "has anchorAtoms"
            else:
                print 'FTNode %s ::getLocalFrame, anchorAtoms=%s'%(\
                    self.name, "None")
                
        if anchorAtoms is None:
            return self.localFrame
        else:
            if self.molecularFragment is None:
                ## the reference node was not set YET when XML was loaded
                ## a quick hack
                return numpy.identity(4, 'f')
            
            #self.molecularFragment.updateCoords(self.currentConf, 1)
            if not self.rigid:
                self.molecularFragment.updateCoords(self.originalConf, 1)

            mat=self._localFrameByAnchorAtoms(anchorAtoms)
            if self.motion is None:
                mat2 = numpy.identity(4, 'f')
            else:
                mat2 = self.motion.getMatrix()
            tmpFrame=numpy.dot(mat, mat2).astype('f')
            return tmpFrame

            
    def _localFrameByAnchorAtoms(self, anchorAtoms):
        ## use conformation 1
        #assert anchorAtoms[0].conformation == 1
        #assert anchorAtoms[1].conformation == 1
        #assert anchorAtoms[2].conformation == 1        
        data=anchorAtoms.get('CA,CB,C').coords
        CA=numpy.array(data[0],'f')
        CB=numpy.array(data[1],'f')
        C =numpy.array(data[2],'f')
        rotmat = defineLocalCoordSys(CB,CA,C)
        mat= numpy.identity(4,'f')
        mat[:3,:3] = rotmat
        mat[:3,3] = CA.tolist()
        mat=numpy.transpose(mat)
        return mat
        

    def getDescr(self):
        """returns a dictionary describing the configuration of this node.
This dictionary can be passed to configure.
"""
        descr = {
            'name':self.name, 'selectionString':self.selectionString,
            'id':self.id
            }

        if self.shape is not None:
            descr['shape'] = self.shape.sType
            descr['shapeParams'] = self.shape.getDescr()
             
        if self.motion is not None:
            descr['motion'] = self.motion.mType
            descr['motionParams'] = self.motion.getDescr()
            
        if self.convolveShapeWithMotion is not None:
            descr['convolve'] = self.convolveShapeWithMotion.cType

        if self.shapeCombiner is not None:
            descr['combiner'] = self.shapeCombiner.scType

        if self.refNode is not None:
            descr['refNode'] = self.refNode

        return descr


    def getDescrXML(self):
        """returns a dictionary describing the configuration of this node,
which is pre-formated to be saved as XML: for example, all values are of
type string. DO NOT pass this dict to configrue,
use the result of getDescr() instead."""
        descr = {
            'name':self.name, 'selectionString':self.selectionString,
            'id':str(self.id)
            }

        if self.refNode is not None:
            # assume all refNode are weakref..
            descr['refNode'] = str(self.refNode().id) 

        if self.shape is not None:
            descr['shape'] = self.shape.__class__.__name__
            sdescr = "" # build shape params
            for k, v in self.shape.getDescr().items():
                sdescr += self._getParamsXML(k, v)
            descr['shapeParams'] = string.strip(sdescr)[:-1] # to get rid of
                                                             # last comma
             
        if self.motion is not None:
            descr['motion'] = self.motion.__class__.__name__
            descr['module'] = self.motion.__module__
            mdescr = "" # build motion params

            # FTMotionCombiner combines a list of motion objects,
            # we write down parameters for each of the motion objects here
            if isinstance(self.motion, FTMotionCombiner):
                num = self.motion.getDescr()['numMotion']
                mdescr +='numMotion: int ' +str(num)+', '                
                descr['motionParams'] = string.strip(mdescr)[:-1]              
                for i in range(num):
                    mdescr=""
                    self.motion.updateMotionParamDictList()
                    for k, v in self.motion.motionParamDictList[i].items():
                        mdescr += self._getParamsXML(k, v)
                    mdescr += 'module: str '
                    mdescr += self.motion.motionList[i].__module__+', '
                    if self.motion.motionParamDictList[i].has_key('type'):
                        # get rid of last comma
                        descr['motion_'+str(i)]=string.strip(mdescr)[:-1]
                    else:
                        mdescr += 'type: str '
                        mdescr += self.motion.motionList[i].__class__.__name__
                        descr['motion_'+str(i)]=mdescr                    
            else:
                for k, v in self.motion.getDescr().items():
                    mdescr += self._getParamsXML(k, v)
                # to get rid of last comma
                descr['motionParams'] = string.strip(mdescr)[:-1]
                
        if self.anchorAtoms is not None:
            descr['anchorAtoms'] = self.anchorAtoms.full_name()

        if self.discreteMotion is not None:
            descr['discreteMotion'] = self.discreteMotion.__class__.__name__
            mdescr = "" # build motion params
            for k, v in self.discreteMotion.getDescr().items():
                mdescr += self._getParamsXML(k, v)
                # to get rid of last comma
                descr['discreteMotionParams'] = string.strip(mdescr)[:-1]
            
        if self.convolveShapeWithMotion is not None:
            descr['convolve'] = self.convolveShapeWithMotion.__class__.__name__

        if self.shapeCombiner is not None:
            descr['combiner'] = self.shapeCombiner.__class__.__name__


        return descr


    def _getParamsXML(self, name, value):
        """helper function for getDescrXML(): this builds a string describing
a value suitable for saving as XML. For example: a name of 'angle' and a
value of 5.0 is returned as:
    'angle: float 5.0, ' """
        if name is None or value is None:
            return ""

        legalTypes = [types.IntType, types.FloatType, types.StringType,
                      types.ListType, types.TupleType,types.BooleanType]

        if type(value) not in legalTypes:
            print "XML WRITER ERROR! Illegal %s for keyword %s"%(
                type(value), name)
            return ""
        
        # list and tuple types have to be treated differently
        if type(value) == types.ListType or type(value) == types.TupleType:
            descr = name +": list " + type(value[0]).__name__
            for v in value:
                descr += " "+str(v)
            descr += ", "
        
        else: # int, float, string
            descr = name +": " + type(value).__name__ + " " + str(value) +", "

        return descr


    def combineShapes(self):
        if self.shapeCombiner is None:
            return
        shapes = []
        for c in self.children:
            shapes.extend( c.shapes.geoms )
        self.combinedShape = self.shapeCombiner.combine( shapes )


    def addChildren(self, children):
        """add a list of FTNode as children nodes of current node
Noticed that duplication is not allowed."""
        for c in children:
            if isinstance(c, FTNode):
                try:
                    idx = self.children.index(c)
##                     print 'WARNING Node %s is already a child node of %s'%(
##                         c.name, self.name)
                except:
                    self.children.append(c)
                    c.parent = weakref.ref(self)
                    c.tree   = weakref.ref(self.tree())
                
            else:
                print 'WARNING trying to add unsuitable child %s to node %s'%(
                    str(c), self.name)
        return
    

    def splitNode(self, frag, motion=None, discreteMotion=None, \
                  name='node', anchorAtoms=None):
        if self.molecularFragment is None:
            print "Error: The node %s has no molecular fragment assigned."\
                  %(self.name)
            return
        fragments = []
        css = CompoundStringSelector()
        tmp = MoleculeSet()
        tmp.append(self.tree().mol)
        tree = self.tree()
        
        molFrag = css.select(tmp, frag)[0]
        node=tree.newNode(molFrag)
        node.configure(motion=motion, name=name,
                       discreteMotion=discreteMotion, anchorAtoms=anchorAtoms)
        if len(self.children)==0:  ## split this node
            coreNode=tree.newNode(self.molecularFragment-molFrag, name='core')
            self.children.append(coreNode)
            self.children.append(node)
            node.configure(refNode=coreNode)
            coreNode.configure(refNode=self)
        else:  ## split from one of the child node
            tmpSet=set(molFrag)
            found=False
            parent=None
            for ch in self.children:
                chTmp=set(ch.molecularFragment)
                if tmpSet==tmpSet.intersection(chTmp):
                    found=True
                    parent=ch
                    break
            if not found:
                print "Can not split node from any child node of",\
                      self.name
                print "please check the syntax of", frag
                return
            else:
                parent.configure(molFrag=parent.molecularFragment-molFrag)
                node.configure(refNode=parent)
                tree.root.children.append(node)
        return                      

    def updateShape(self, node=None):
        """Convolves the all geoms rooted from node"""
        if node is None:
            node = self.tree().root

##         if node.shape is not None:
##             if node.autoUpdateShape:
##                 node.shape.updateGeoms() 
##         for child in node.children:
##             self.updateShape(node=child)

        if node.shape is not None:
            if node.autoUpdateShape:
                node.updateConvolution()
#        for child in node.children:
#            self.updateShape(node=child)



##         if node is None:
##             node = self.tree().root
##         if node.shape is not None:
##             if node.autoUpdateShape:
##                 node.shape.crossSetGeoms=False
##                 node.shape.updateCrossSetGeoms()
##                 #node.shape.updateGeoms() 
##         for child in node.children:
##             self.updateShape(node=child)



    def updateMotion(self):
        pass

                
    def applyMat(self, mat, points):
        """ returns the coordinates after transformation
points: a list of xyz (float number) coordinations (n,3) or (n,4)"""
        if mat.shape != (4,4):
            raise ValueError("Need a 4x4 transformation matrix")
        sh=numpy.array(points).shape
        if sh[1] == 4:
            homoCoords = points
        elif sh[1] == 3:
            homoCoords = numpy.concatenate((points,
                         numpy.ones( (len(points), 1), 'd')), 1)
        else:
            raise ValueError("The points given are not in right format")

        res=numpy.dot(homoCoords, mat).astype('f')
        if sh[1] == 4:    return res
        else: return res[:, :3].tolist()

       # tpts = []
       # for pt in points:
       #     ptx = mat[0][0]*pt[0]+mat[0][1]*pt[1]+mat[0][2]*pt[2]
       #     pty = mat[1][0]*pt[0]+mat[1][1]*pt[1]+mat[1][2]*pt[2]
       #     ptz = mat[2][0]*pt[0]+mat[2][1]*pt[1]+mat[2][2]*pt[2]
       #     tpts.append( (ptx, pty, ptz) )
       # return tpts
        

    def updateConvolution(self):
        """ convolve the shapes with motion """

        #print 'updateConvolution...', self.name
        if self.newMotion:
            self._updateLocalFrame()
            self.newMotion = False
            
        if len(self.refBy)!=0:
            for child in self.refBy :                
                child.updateConvolution()
        self.convolveShapeWithMotion.convolve()
        

    def _updateLocalFrame(self):
        """ updates the localFrame (4x4) of current FTNode
This function should only be caleld by updateCurrentConformation() and
updateConvolution()"""

        if self.discreteMotion:
            if self.molecularFragment is not None:
                atoms = self.molecularFragment
            else:
                atoms = self.getAtoms()
            #if not self.discreteMotion.active:
            if self.discreteMotion.active == False:
                # MS THIS WILL FAIL AS NO DISCRETE MOTION HAS defaultCoords
                # yet
                for a,c in zip(atoms, self.defaultCoords):
                    a._coords[1] = c
            else:
                self.discreteMotion.apply(atoms)

            #self._adaptLocalConformation(atoms)
            
        if self.refNode is None:
            if self.parent is not None:
                parent = self.parent()
                if self.anchorAtoms is None:
                    #print self.name,'no anchor'
                    self.refFrame = parent.getLocalFrame()
                else:
                    #print self.name,'has anchor'
                    self.refFrame = parent.getLocalFrame(\
                                    anchorAtoms=self.anchorAtoms)
            else:
                self.refFrame = numpy.identity(4,'f')
        else:
            if self.anchorAtoms is None:
                #print self.name, 'no anchor'
                self.refFrame = self.refNode().getLocalFrame()
            else:
                #print self.name, 'has anchor', self.refNode().name
                self.refFrame = self.refNode().getLocalFrame(\
                                    anchorAtoms=self.anchorAtoms)
                #print self.refFrame


        #if self.motion is None or not self.motion.active:
        #if self.motion is not None:
        #    print self.motion.name, self.motion.active,
        if self.motion is None or self.motion.active == False:
            mat = numpy.identity(4, 'f')
        else:
            mat = self.motion.getMatrix()

        # !!! the proper order of matrixmultiply !!!
        self.localFrame = numpy.dot(mat, self.refFrame).astype('f')
        return
    
    
    def updateCurrentConformation(self, updateAtom=False, force=False):
        """
Update current coordinates, including all the children(refBy) nodes
Noted that only leaf nodes store the coordinates
updateAtom = False (default): update the self.currentConf
           = True           : update the coords of each atom (conformation 1)
                              Useful when comparing RMSD with original molecule
force : when True, redo all the update 
"""
        if force is True:
            self.newMotion=True
        
        if VERBOSE:
            print 'updateCurrentConformation for', self.name
            
        if self.newMotion:# and self.molecularFragment and len(self.refBy):
            self._updateLocalFrame()
            
        self.newMotion = False

        # MS the root node of the receptor has an orginal conformation
        # but we do not want to apply identity matrix every time
        if self.originalConf is not None:
            mat = self.localFrame  ## up-to-date localFrame
            self.currentConf = self.applyMat(mat, self.originalConf)
            
        if len(self.refBy)!=0:
            for child in self.refBy:
                # newMotion is a flag of updating localFrame 
                child.newMotion = True 
                child.updateCurrentConformation(updateAtom=updateAtom)

        if updateAtom and self.molecularFragment:
            if isinstance(self.molecularFragment, TreeNodeSet):
                atoms = self.molecularFragment.findType(Atom)
            else:
                atoms = self.molecularFragment.getAtoms()
            atoms.updateCoords(self.currentConf, 1)

        return
    

    def _updateOriginalConf(self):
        """ set the self.originalConf to the #2 conformation of molFrag"""

        if self.children: # or refBy ?
            for c in self.children:
                c._updateOriginalConf()
        else:
            atoms = self.molecularFragment.findType(Atom)
            atoms.sort()
            confNB = atoms[0].conformation
            if confNB !=2:
                atoms.setConformation(2)
            self.originalConf = atoms.coords
            #print self.name, "  ** ",  self.originalConf[:3]
            if confNB !=2:
                atoms.setConformation(confNB)


    def _adaptLocalConformation(self, atoms):
        ##coords = self.originalConf
        if len(atoms)==0:
            return

        self.discreteMotion.apply(atoms)
        

##     def _origCoordsByResidue(self):
##         """help function to return a list of Original coords..
## [ [coords from resdidue 1 ], [coords from resdidue 2 ], ...  [ n] ]
##         """

##         atoms=self.molecularFragment.findType(Atom)
##         atoms.setConformation(0)
##         resSet=atoms.parent.uniq()
##         origCoords=[]

## #        for a in atoms:
## #       fixme.. redundant calculation... ugly !!
##         for r in resSet:
##             ats = r.atoms & atoms
##             origCoords.append(ats.coords)

##         atoms.setConformation(1)
##         return origCoords
    
        

    def getAtoms(self, select='all'):
        """Returns an AtomSet composed of Atom objects from all leaf nodes of this node
       selection: all : all the atoms
                  rigid : only rigid atoms below this node
                  flex  : only flexible atoms below this node
"""

        atomList = self._getAtoms(select=select)
        atoms = AtomSet(atomList)
        return atoms


    def _getAtoms(self, select='all'):
        """Recursive helper method to get molecular fragments of leaf nodes
        This method should only be called by self.getAtoms()"""
        
        # molecularFragment can be either an instance of a MolKit TreeNodeSet
        # or of a MolKit molecule
        
        if len(self.children):
            atoms=[]
            for child in self.children:
                aList = child._getAtoms(select=select)
                atoms.extend(aList)
            return atoms
        else:
            if select=='all' or \
               (select=='rigid' and self.rigid==True) or \
               (select=='flex' and self.rigid==False):

                molFrag = self.molecularFragment
                if molFrag == None: return []
            else:
                return []
            
            if isinstance(molFrag, TreeNodeSet):
                atoms = molFrag.findType(Atom)
            else:
                atoms = self.molecularFragment.getAtoms()
            return atoms
    

    def getOriginalConformation(self):
        """Returns original conformation (i.e. self.originalConf)

        Returns the conformation according to the tree.
        This doesnt match the .pdb file.  Use 
        """
        # 
        coords = self._getOriginalConformation()
        return coords   # coords not sorted as in pdb file        
        

    def _getOriginalConformation(self):
        """Recursive private function for getOriginalConformation"""
        if len(self.children):
            coordList=[]
            for child in self.children:
                coords = child._getOriginalConformation()
                if len(coords):
                    coordList.extend(coords)
            return coordList
        else:
            # we are at leaf node
            return self.originalConf


    def getPDBConformation(self):
        """Returns original conformation (i.e. self.originalConf) and sorts
the coords in the same order as in PDB file"""
        atoms=self.getAtoms()
        atoms.sort()
        atoms.setConformation(0)
        originalConf = atoms.coords
        atoms.setConformation(1)
        return originalConf # coords are sorted as in pdb file


    def getCurrentConformation(self):
        """Returns the current conformation (i.e. the transformed coords)
Please be noted that the ordering of returned coords may not be the same as
in PDB file. Instead, the FlexTree is (depth-first) traversed.
To get the transformed coords as in PDB file order, see:
getCurrentSortedConformation()

"""
        if VERBOSE:
            print self.name,'getCurrentConformation'

        coords = self._getCurrentConformation()
        return coords        
##         atmSet = self.getAtoms()        
##         return atmSet.coords
    
    def _getCurrentConformation(self):
        """Recursive helper function for getCurrentConformation"""
        if len(self.children):
            coordList=[]
            for child in self.children:
                coords = child._getCurrentConformation()
                if len(coords):
                    coordList.extend(coords)
            return coordList
        else: # we are at leaf node
            if self.parent:
                return self.currentConf  # array type
            else:
                # self has no parent -> a tree with only one FTNode (root)
                # do this because getCurrentSortedConformation returns a list
                if self.currentConf is not None:
                    return self.currentConf#.tolist()
                else:
                    return []


# fixme.. not working?
    def getCurrentSortedConformation(self):
        """Returns current conformation , coordinates sorted in the same order
as in PDB file, useful for RMSD caculation"""

        if VERBOSE:
            print self.name,'getCurrentSortedConformation'

        #self.updateCurrentConformation(updateAtom = True)
        atoms = self.getAtoms()
        atoms.sort()
        #atoms.setConformation(1) # 1: the default set of conformation.
        return atoms.coords


    def getCurrentSortedConformation2(self):
        """Returns current conformation , coordinates sorted in the same order
as in PDB file, useful for RMSD caculation,
implement # 2
"""
        if VERBOSE:
            print self.name,'getCurrentSortedConformation2'

        coords = self.getCurrentConformation()
        atoms = self.getAtoms()[:]
	###print "Old :", atoms.coords
        #atoms.updateCoords(coords, 0)  #?!
        atoms.updateCoords(coords, 1)
	###print "New :", atoms.coords
        atoms.sort()
        return atoms.coords


    def getBackBoneConformation(self, backbone='C,N,O,CA'):
        """
Returns current conformation of backbone atoms
Atoms are sorted (for RMSD caculation)
backbone: string of backbone definition.
         e.g. if backbone='CA', this function returns the C-alpha conformation.
"""

        self.updateCurrentConformation(updateAtom = True)
        atoms=self.getAtoms()
        aa=atoms.get(backbone)
        aa.sort()
        #atoms.setConformation(1) # 1: the default set of conformation.
        return aa.coords


    def updateIDs(self):
        """
updates the id after adding self to another FlexTree as a subtree
Please notice that the id of root node should have already been changed to
a uniq number in the new tree..
        """
        tree=self.tree()
        for node in self.refBy:
            tree.createUniqNumber(node)
            node.tree = self.tree  # pointing to new tree
            node.updateIDs()
        return
        

# end of FT.py

## NOTES
"""
<1> the coordinate data in atoms
    The _coords is a list of conformations for given Atom(s).
    Three conformations are used in FlexTree:
    index 0: the conformation read from PDB file
    index 1: conformation transformed by motion objects. (for docking)
    index 2: alternative conformation (such as rotamer, discrete conformations)


"""

