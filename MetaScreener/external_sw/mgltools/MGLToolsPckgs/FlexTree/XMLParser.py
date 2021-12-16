#########################################################################
#
# Date: Jan 2004 Authors: Daniel Stoffler, Michel Sanner, Yong Zhao
#
#    stoffler@scripps.edu
#      sanner@scripps.edu
#    yongzhao@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Daniel Stoffler, Michel Sanner , Yong Zhao and TSRI
#
#########################################################################

import weakref
import string, re, os

import xml.dom.minidom
from xml.dom.minidom import Node

from FlexTree.FT import FTNode, FlexTree
from MolKit.molecule import Atom, AtomSet
from FlexTree.FTMotions import FTMotionCombiner, FTMotion_BoxTranslation

from MolKit import Read

# find path to XML data directory
DATA_DIR = os.getenv('AUTODOCKFR_DATADIR')
if DATA_DIR is None:
    DATA_DIR = '.'

XML_DIR=''


def updateXMLPath(filename):
    """ update XML_DIR """
    bb=filename.split('/')
    file=bb[-1]
    tmpPath=string.join(bb[:-1], '/')
    return tmpPath

    

class ReadXML:
    """This object parses XML files containing a 'partitioned' pdb file and
builds a list of FlexTree trees.

- call this object with a filename to run
- use the get() method to retrieve the result"""
    

    def __init__(self, filename=None):
        self.flextrees = [] # contains the resulting flextree(s)
        self.molecules = [] # used only internally, list of molecules
        
        if filename is not None:
            self.doit(filename)  


    def __call__(self, filename, cmdLineOnly=False):
        """call the doit() method by calling this object"""
        if filename is not None:
            self.doit(filename, cmdLineOnly)


    def doit(self, filename, cmdLineOnly=False):
        """read <filename> XML file, builds partition objects"""

        if filename is None or not len(filename):
            return
        #FIXME this should only happen if filename is not an absolute path
        self.filename = os.path.join(DATA_DIR,filename)
        if not os.path.exists(filename):            
            tmpName=os.path.join(DATA_DIR,filename)
            if not os.path.exists(tmpName):
                tmpName=os.path.join(os.getcwd(),filename)
                if not os.path.exists(tmpName):
                    print 'File "%s" not found in data path or current path.'\
                          %self.filename
                    raise
                else:
                    self.filename=tmpName
            else:
                self.filename=tmpName
        else:
            self.filename = filename

        # get absolute path xml file
        folder, xmlfilename = os.path.split(self.filename)
        xmlFilePath = os.path.abspath(folder)
        print 'READING XML file %s'%os.path.join(xmlFilePath, xmlfilename)

        XML_DIR=updateXMLPath(self.filename)
            
        self.flextrees = []
        self.molecules = []
       
        doc = xml.dom.minidom.parse(self.filename)

        rootNumber = 0 # counter for roots in a given XML file
        
        # now loop over all roots in XML file and build partitions
        for xmlTree in doc.getElementsByTagName("root"):
            self.refNodes = {} # dict used to set refNodes correctly

            name = str( xmlTree.getAttribute("name") )
            
            # create new FlexTree
            tree = FlexTree(name=name)
            # create new FTNode
            ftNode = FTNode()

            # build root node, get various strings
            selString = str( xmlTree.getAttribute("selectionString") )

            if not cmdLineOnly:            
                # get shape
                shape, shapeParams = self.parseShape(xmlTree)
            else:
                shape=None
                shapeParams=None
            # get motion
            motion, motionParams = self.parseMotion(xmlTree)
            # get discrete motion
            discreteMotion, discreteMotionParams=self.parseDiscreteMotion(\
                xmlTree)

            # get convolution
            convolution = self.parseConvolution(xmlTree, ftNode)
            # get combiner
            if not cmdLineOnly:
                combiner = self.parseCombiner(xmlTree)
            else:
                combiner=None

            # read pdb file and append to list of molecules

            # FIXME ... we have to fix path to use proper separator
            #molFileName=fixFileName(xmlTree.getAttribute('file'))
            molFileName=xmlTree.getAttribute('file')
            molFileName=str(molFileName)  # cast <type 'unicode'>

            # make sure we read the molecule from the same location as the xml
            folder, molFileName = os.path.split(molFileName)
            if folder is '':
                folder = xmlFilePath
            print "READING Molecule %s"%os.path.join(folder, molFileName)

            ## #filePath = os.path.realpath(fff)
            ## # path of pdb(qs) file: 1) data dir, 2) from current working dir 
            ## if not os.path.exists(molFileName):
            ##     tmpName=os.path.join(DATA_DIR,molFileName)
            ##     if not os.path.exists(tmpName):
            ##         tmpName=os.path.join(XML_DIR,molFileName)
            ##         if not os.path.exists(tmpName):
            ##             tmpName=os.path.join(os.getcwd(),molFileName)
            ##             if not os.path.exists(tmpName):
            ##                 print 'File "%s" not found in data path or current path.'\
            ##                       %molFileName
            ##                 raise
            ##             else:
            ##                 filePath=tmpName
            ##         else:
            ##             filePath=tmpName
            ##     else:
            ##         filePath=tmpName
            ## else:
            ##     filePath=molFileName

            ## filePath=str(filePath)  # cast <type 'unicode'>
            filePath = os.path.join(folder, molFileName)
            mol = Read(filePath)
            mol[0].buildBondsByDistance(1.85) # fixme.. 1.85 default
            
            self.molecules.extend(mol)
            
            molFrag = None
            noChildren=True
            for child in xmlTree.childNodes:
                if child.nodeType != Node.TEXT_NODE:
                    noChildren=False
                    break
                
            if noChildren:
                from MolKit.molecule import MoleculeSet
                tmpMS=MoleculeSet()
                tmpMS.append(self.molecules[rootNumber])
                molFrag = tmpMS.NodesFromName(selString)

            # now configure the node with what we found
            ftNode.configure(
                name=name, selectionString=selString, shape=shape,
                shapeParams=shapeParams, motion=motion, molFrag=molFrag,
                motionParams=motionParams, convolution=convolution,
                shapeCombiner=combiner, discreteMotion=discreteMotion,
                discreteMotionParams=discreteMotionParams)

            # add root node to FlexTree
            tree.root = ftNode
            # add weakref tree to root node
            ftNode._tree = tree
            ftNode.tree = weakref.ref(ftNode._tree)
            # create unique number
            u = xmlTree.getAttribute("id")
            if not u or len(u) == 0:
                u = None
            else:
                u = int( string.split(u)[-1] )
            tree.createUniqNumber(ftNode, uniqNumber=u)

            
            # add pdb file path to FlexTree tree
            tree.pdbfilename = filePath
            tree.xmlfilename = self.filename

            # update refNodes dict:
            self.updateRefNodesDict(xmlTree, ftNode)

            # now loop over children of root node
            for child in xmlTree.childNodes:
                if child.nodeType==Node.TEXT_NODE:
                    continue
                elif child.nodeType==Node.ELEMENT_NODE:
                    self._buildTree(child, xmlTree, ftNode, rootNumber,
                                    cmdLineOnly )

            # set the refNodes,
            if len(self.refNodes.keys()):
                for node, id in self.refNodes.items():
                    # NOTE added by Yong
                    # every refNode-id will have to browse whole tree once?
                    self.setRefNode(tree.root, node, id)

            # make sure the transformation is up-to-date
            rootMotion=tree.root.motion
            if isinstance(rootMotion, FTMotionCombiner):
                # translate the center of ligand to center of docking box
                for motion in rootMotion.motionList:
                    if isinstance(motion, FTMotion_BoxTranslation):
                        motion.configure(update=True)
                        rootMotion.updateTransformation()             

            # append flextree and increment rootNumber counter
            self.flextrees.append(tree)
            rootNumber = rootNumber + 1
            # update status
            tree.updateStatus()
            
           

    def _buildTree(self, xmlNode, xmlParent, ftNode, rootNumber,cmdLineOnly):
        """called recursively, parsing XML, building tree node structure"""
        
        ftn = FTNode()
        # get name
        name = str( xmlNode.getAttribute("name") )
        # get selectionString
        selString = str( xmlNode.getAttribute("selectionString") )
        # get shape
        if not cmdLineOnly:
            shape, shapeParams = self.parseShape(xmlNode)
        else:
            shape=None
            shapeParams=None            
        # get motion
        motion, motionParams = self.parseMotion(xmlNode)
        # get discrete motion
        discreteMotion, discreteMotionParams=self.parseDiscreteMotion(\
                xmlNode)
        # get convolution
        convolution = self.parseConvolution(xmlNode, ftn)
        # get combiner
        if not cmdLineOnly:
            combiner = self.parseCombiner(xmlNode)
        else:
            combiner =None
        
        # get molFrag, this is always only in the leaf nodes
        molFrag=None

        # anchor Atoms
        anchorAts=None
        anchorAtomNames= str( xmlNode.getAttribute("anchorAtoms") )

        # is this node a true leaf? (We can be leaf, but still have children
        # such as TextNodes, that have \n or whitespaces...
        noChildren=False
        if not len(xmlNode.childNodes):
            noChildren = True
        else:
            for child in xmlNode.childNodes:
                if child.nodeType==Node.TEXT_NODE:
                    noChildren=True
                else:
                    noChildren=False
                    break
       
        # if we are a leaf node, we can append stuff
        if noChildren is True:
            #molFrag = self.molecules[rootNumber].NodesFromName(selString)
            from MolKit.molecule import MoleculeSet
            tmpMS=MoleculeSet()
            tmpMS.append(self.molecules[rootNumber])
            molFrag = tmpMS.NodesFromName(selString)
            #print selString
            #print 'molfrag', len(molFrag.findType(Atom))
            if anchorAtomNames !="":
                anchorAts = tmpMS.NodesFromName(anchorAtomNames)
            else:
                anchorAts=None

            if molFrag is None :
                print "Error in molFrag"
                # molFrag should NOT be empty
                raise
            if  len(molFrag)==0 :
                print "Error in MolFrag"
                raise ValueError("selection string %s in node %s selects nothing"%(selString, name))

        # every node gets a weakref to FlexTree tree 
        tree = ftNode.tree()
        ftn.tree = weakref.ref(tree)

        # append node
        ftNode.addChildren([ftn])

        # create unique number
        u = xmlNode.getAttribute("id")
        if not u or len(u) == 0:
            u = None
        else:
            u = int(u)
        ftn.tree().createUniqNumber(ftn, uniqNumber=u)
       
        ftn.configure(
            name=name, molFrag=molFrag, selectionString=selString,
            motion=motion,  motionParams=motionParams,
            shape=shape,shapeParams=shapeParams,
            convolution=convolution, shapeCombiner=combiner,
            discreteMotion=discreteMotion,
            discreteMotionParams=discreteMotionParams,
            anchorAtoms=anchorAts)

        # update refNodes dict
        self.updateRefNodesDict(xmlNode, ftn)

        # because we run recursively:
        ftNode = ftn
            
        #print "creating node", node.getAttribute("name"), 'child of', \
        #      parent.getAttribute("name"),node.getAttribute("data")

        # loop recursively over children of this node
        for child in xmlNode.childNodes:
            if child.nodeType==Node.TEXT_NODE:
                continue
            self._buildTree(child, xmlNode, ftNode, rootNumber, cmdLineOnly)


    def get(self):
        """return the result"""
        return self.flextrees


    def parseParams(self, text):
        """parse params and return dictionary.
The string has to follow these conventions:
ATTRIBUTENAME DATATYPE VALUE
- multiple attributes have to be separated by comma
- 'list' datatypes have to define the datatype too, the values are separated
by whitespace
example:
        'angle: float 5.0, vector: list float 5.0 2.3 1.0, quality: int 20'
"""
        
        params = {}
        typesDict = {
            'int':int, 'float':float, 'list':list, 'tuple':tuple, 'str':str,
            }

        splitText = string.split(text, ",")
        for spl in splitText:
             spl2 = string.split(spl, ":")
             key = string.strip(spl2[0])
             valueSpl = string.split(spl2[1])

             if valueSpl[0] == 'list': # list type
                 value = []
                 valType = typesDict[valueSpl[1]]
                 vals = valueSpl[2:]
                 value = []
                 for v in vals:
                     value.append( valType(v) )
             else:
                 valType = typesDict[valueSpl[0]]
                 value = valType(valueSpl[1])

             # and finally, append key, value to dictionary
             params[key] = value

        return params


    def parseShape(self, xml):
        import FlexTree.FTShapes
        s = str( xml.getAttribute("shape") )
        shape = None
        shapeParams = None
        if s is not None and len(s):
            shape = getattr(FlexTree.FTShapes, s)\
                    (name=str(xml.getAttribute("name") ))
            # get shape params
            sp = str( xml.getAttribute("shapeParams") )
            if len(sp):
                shapeParams = self.parseParams(sp)
        return shape, shapeParams


    def parseMotion(self, xml):
        from FlexTree.FTMotions import FTMotionCombiner, FTMotion
        m = str( xml.getAttribute("motion") )
        motion = None
        motionParams = None
        if m is not None and len(m):
            mname = xml.getAttribute("motion")
            module = __import__(xml.getAttribute("module"), globals(), locals(),
                                             [mname])
            motion = getattr(module, mname)()
            if motion is None:
                raise RuntimeError, "motion object not found"

            #motion = getattr(FlexTree.FTMotions, m)()
            # get motion params
            mp = str( xml.getAttribute("motionParams") )
            if len(mp):
                motionParams = self.parseParams(mp)
                try: # if we have 2 individual points, convert them back to
                     # a list of of two points:
                    p1 = motionParams.pop('point1')
                    p2 = motionParams.pop('point2')
                    motionParams['points'] = [p1, p2]
                except:
                    pass
            # special case: FTMotionCombiner
            # fetch motion parameters, save as dictionaries, then make a list
            # of all these dictionaries.
            if isinstance(motion, FTMotionCombiner):
                num = motionParams['numMotion']
                paramDictList=[]
                for i in range(num):
                    mp = str( xml.getAttribute("motion_"+str(i)) )
                    if len(mp):
                        paramDict = self.parseParams(mp)
                        try: # if we have 2 individual points,
                            # convert them back to
                            # a list of of two points:
                            p1 = paramDict.pop('point1')
                            p2 = paramDict.pop('point2')
                            paramDict['points'] = [p1, p2]
                        except:
                            pass
                        paramDictList.append(paramDict)
                motionParams={}
                motionParams['motionParamDictList'] = paramDictList
            
        return motion, motionParams

    def parseDiscreteMotion(self, xml):
        import FlexTree.FTMotions
        m = str( xml.getAttribute("discreteMotion") )
        motion = None
        motionParams = None
        if m is not None and len(m):
            motion = getattr(FlexTree.FTMotions, m)()
            # get motion params
            mp = str( xml.getAttribute("discreteMotionParams") )
            if len(mp):
                motionParams = self.parseParams(mp)

        return motion, motionParams

    def parseConvolution(self, xml, ftNode):
        import FlexTree.FTConvolutions
        c = str( xml.getAttribute("convolve") )
        convolution = None
        if c is not None and len(c):
            convolution = getattr(FlexTree.FTConvolutions, c)(ftNode)
        return convolution


    def parseCombiner(self, xml):
        import FlexTree.FTShapeCombiners
        c = str( xml.getAttribute("combiner") )
        combiner = None
        if c is not None and len(c):
            combiner = getattr(FlexTree.FTShapeCombiners, c)()
        return combiner


    def updateRefNodesDict(self, xml, ftNode):
        """update the refNodes dict"""
        if ftNode.parent:
            self.refNodes[ftNode] = ftNode.parent().id
        
        r = str( xml.getAttribute("refNode") )
        if r is not None and len(r):
            self.refNodes[ftNode] = int(r)

        
    def setRefNode(self, parent, node, id):
        if parent.id == id:
            node.refNode = weakref.ref(parent)
            parent.refBy.append(node)
            return True
        else:
            for child in parent.children:
                found = self.setRefNode(child, node, id)
                if found:
                    return True
            return False

    def setCrossSet(self, root):
        """Set the line geometry for the lines between Nodes"""
        for child in root.children:
            self._setCrossSet(child)        


    def _setCrossSet(self, node):
        """Set the line geometry for the lines between Nodes"""
        if node.shape is not None : # or node is not FTLines : fix me
            shape=node.shape
            print 'set cross set '
            shape.updateCrossSetGeoms()
        if len(node.children) != 0:
            for child in node.children:
                self._setCrossSet(child)        

        

class WriteXML:
    """This object builds a DOM structure and uses DOM functionality to
generate XML and save it.

Input: A list of FlexTrees and a filename.
For example:  W=WriteXML()
              W(trees, 'myTree.xml'"""
    

    def __init__(self, treeList=None, filename=None):
        self.treeList = treeList  # list of FlexTree trees
        self.filename = filename  # XML filename to save file
        self.doc = None           # DOM object, created in doit()
        self.format = FormatXML() # formatter object to format xml
        
        if treeList is not None and filename is not None:
            self.doit()

    def __call__(self, treeList=None, filename=None):
        """call the doit() method by calling this object"""
        if treeList is not None and filename is not None:
            self.filename = filename
            self.treeList = treeList
            self.doit()


    def doit(self):
        """build XML DOM structures, get XML and save file
        Note: attributes are sorted by name in the toprettyxml() method"""

        # Note: most of the work here is done in FT.py: FTNode.getDescrXML()
        
        # create DOM object
        self.doc = xml.dom.minidom.Document()
        for tree in self.treeList:
            assert isinstance(tree, FlexTree)
            descr = tree.root.getDescrXML()
            domRoot = self.doc.createElement('root')

            # set the attributes
            for k, v in descr.items():
                domRoot.setAttribute(k, v)

            # and also append attribute file
            # only save the filename, not the path.
            # the XML should always be in the same directory of data file
            filename=tree.pdbfilename.split('/')[-1]
            domRoot.setAttribute('file', filename)
            # add to DOM
            self.doc.appendChild(domRoot)

            # now, loop over children
            for ftChild in tree.root.children:
                self.buildDom(ftChild, domRoot)


        # and save it
        try:
            f = open(self.filename, 'w')
            f.writelines(self.get())
            f.close()
        except:
            print 'WRITE XML ERROR: Failed to write %s'%self.filename


    def buildDom(self, ftChild, domParent):
        """recursive function, builds DOM structure"""
        
        domNode = self.doc.createElement('node')
        descr = ftChild.getDescrXML()

        # set attributes
        for k, v in descr.items():
            domNode.setAttribute(k, str(v))
        
        domParent.appendChild(domNode)
        domParent = domNode
        for c in ftChild.children:
            self.buildDom(c, domParent)


    def get(self):
        
        xml = self.doc.toxml()
        newxml = self.format.doit(xml)
        return newxml
        
        
        

class FormatXML:
    """This class parses a xmlstring and returns a formated list that can
    be saved"""

    def __init__(self):
        import xml.parsers.expat
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler  = self.start_element
        self.parser.EndElementHandler    = self.end_element
        self.data = []


    def __call__(self, data):
        self.doit(data)
        

    def doit(self, data):
        self.__init__() # need to create fresh parser object!?
        self.indent = ""
        self.data = []
        self.data.append('<?xml version="1.0" ?>\n')
        self.parser.Parse(data)
        return self.data


    def start_element(self, name, attrs):
        self.indent = self.indent + 4*" "
        self.data.append(self.indent + '<' + name + '\n')
        self.indent = self.indent + 4*" "

        # attrs is a dict, we want name and id first, so lets pop the out
        v = attrs.pop('name', None)
        if v:
            self.data.append(self.indent + 'name="' + v + '"\n')
        v = attrs.pop('id', None)
        if v:
            self.data.append(self.indent + 'id="' + v + '"\n')

        # and loop over the remaining keys,values:
        for k, v in attrs.items():
            self.data.append(self.indent + k + '="' + v + '"\n')
        self.indent = self.indent[:-4]
        self.data[-1] = self.data[-1][:-1] + '>\n'

        
    def end_element(self, name):
        self.data.append(self.indent + '</' + name + '>\n')
        self.indent = self.indent[:-4]


        
class LinkerToXML:
    """ convert a flexible linker (residueSet) to FlexTree based on phi and
psi angles, and convert the FT to XML"""
    def __init__(self, residueSet=None):
        self.residueSet = None
        self.tree = None
        self.configure(residueSet=residueSet)

    def __call__(self, data=None):
        if data is not None:
            from MolKit.protein import ResidueSet
            assert isinstance(data, ResidueSet)
            self.configure(residueSet=data)
        self.doit()


    def configure(self,  residueSet=None):
        if residueSet is not None:
            if self.validLinker(residueSet):
                self.residueSet = residueSet
        

    def doit(self):        
        
        from FlexTree.FT import FTNode, FlexTree
        from MolKit.molecule import AtomSet
        from FlexTree.FTMotions import FTMotion_Hinge
        from FlexTree.FTShapes import FTLines
        
        tree = self.tree = FlexTree(name="Flex Linker")
        root = FTNode(name = 'Root of Flex Linker')
        tree.root = root
        tree.pdbfilename = self.residueSet[0].top.parser.filename

        root._tree = tree
        root.tree = weakref.ref(root._tree)
        selString = self.residueSet.full_name()
        #shape = FTLines()
        #shapeParams = ##
        tree.createUniqNumber(root)
        root.configure(name='Linker root', selectionString=selString,
                       #shape=shape,
                       #shapeParams=shapeParams
                       )

        firstChild = True
        for res in self.residueSet:
            names=res.atoms.name
            phiNode = FTNode()
            #idx=names.index('C') ; at3 = self.atoms[idx]
            atoms=res.atoms
            psiAtoms= atoms.objectsFromString('O|C')
            psiAtoms = AtomSet(psiAtoms)
            phiAtoms = atoms.xor(psiAtoms)            

            N = atoms.objectsFromString('N')[0]
            CA = atoms.objectsFromString('CA')[0]
            C =  atoms.objectsFromString('C')[0]

            # phi node here
            phiNode = FTNode()
            #shape = FTLines()
            shape=None
            phiMotion = FTMotion_Hinge(name = res.name+'_phi hinge',
                                       points=[N.coords, CA.coords],
                                       )
            tree.createUniqNumber(phiNode)
            phiNode.configure(name=res.name+'_phi', molFrag = phiAtoms,
                              motion = phiMotion ,
                              shape = shape)

            root.addChildren([phiNode])
            if firstChild:
                phiNode.refNode = weakref.ref(root)
                firstChild = False
            else:
                phiNode.refNode = weakref.ref(phiNode.parent().children[-2])

            # psi node here
            psiNode = FTNode()
            #shape = FTLines()
            shape=None
            psiMotion = FTMotion_Hinge(name = res.name+'_psi hinge',
                                       #points=[CA.coords, C.coords],
                                       points=[N.coords, CA.coords],
                                       )
            tree.createUniqNumber(psiNode)
            psiNode.configure(name=res.name+'_psi', molFrag = psiAtoms,
                              motion = psiMotion,
                              shape = shape)
            
            root.addChildren([psiNode])
            psiNode.refNode = weakref.ref(psiNode.parent().children[-2])
            
        # now generate XML here
        writer = WriteXML(self.tree)
        

    def validLinker(self, residueSet):
        """ validate residueSet, shoudl be connected residues"""
        if len(residueSet) is 0: return False
        residueSet.sort()
        for i in range(len(residueSet) -1 ):
            if residueSet[i].getNext() != residueSet[i].getNext():
                return False        
        return True
