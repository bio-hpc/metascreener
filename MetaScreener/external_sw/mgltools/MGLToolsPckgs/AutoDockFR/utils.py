########################################################################
#
# Date: May 2005 Author: Yong
#
#    yongzhao@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Yong Zhao
#
#########################################################################

"""
This module implements the utilities (tools) related to FlexTree and docking

"""
import types, weakref, os
from FlexTree.FT import FTNode, FlexTree
from MolKit import Read
from FlexTree.XMLParser import ReadXML,WriteXML
from MolKit.protein import Protein, Chain, ChainSet, Residue, ResidueSet, ProteinSet

from MolKit.molecule import Atom, AtomSet
from MolKit.protein import ResidueSet

from AutoDockFR.FTGA import GAFTMotion_Rotamer, GAFTMotion_SoftRotamer
from AutoDockFR.orderRefAtoms import orderRefMolAtoms

import numpy as Numeric
N=Numeric

import string

from AutoDockTools.MoleculePreparation import LigandPreparation


def validate(pyDockLogFileName=None, lines=None ):
    """ make sure the log file is from a completed docking test
    """
    if lines is not None:
        data=lines

    isLogFile=False
    for line in data[:20] :
        if line.find("pyDock") != -1:
            isLogFile= True
    if not isLogFile:
        print "Warning: Not a pyDock log file.. "
        return False
        
    if pyDockLogFileName is not None:
        logFile=open(pyDockLogFileName)
        data=logFile.readlines()

    for line in data[10:] :
        if line.find("evolution finished") != -1:
            return True

    print "Warning: Imcomplete docking log found.. "
    if pyDockLogFileName is not None:
        logFile.close()
    return False
    

def getSettingsFromLog(logFile):
    try:
        logFile=open(logFile)
        data=logFile.readlines()
    except :
        print "Error in opening", logFile
        raise IOError        
    
    tmpSetting={}
    settings={}
    for line in data[:200]:
        if line.find('Setting:')==0:
            tmp = line.replace('\'', '') 
            tmp=line[9:].split()
## <<<<<<< utils.py
##             #key=tmp[0][:-1] ## because of the ":"
##             key=tmp[0]
##             if len(tmp[1:])==1:
##                 try:
##                     value=eval(tmp[1])
##                 except:
##                     value=tmp[1]
##             else:
##                 value=''.join(tmp[1:])
                    
##             tmpSetting[key]=value
##             #print "** --> ", key, value
## =======
            key=tmp[0][:-1] ## because of the ":"
            if len(tmp[1:])==1:
                try:
                    value=eval(tmp[1])
                except:
                    value=tmp[1]
            else:
                value=''.join(tmp[1:])
                    
            tmpSetting[key]=value
            #print "** --> ", key, value

    from AutoDockFR.Param import Params


    #raise
    #p=Params([])
    p=Params()
    
    #options=p.optList.data
    for key in tmpSetting.keys():
        #key=op.dest
        settings[key]=tmpSetting[key]
        #tmpSetting.pop(key)
    #settings['searchingParams']=tmpSetting
    return settings



def getResultsFromLogFile(logFile):
    """locate the best gene from a pyDock docking log file (pyDockLogFileName)
    return the setting of docking and a list of best genes
"""
    try:
        logFile=open(logFile)
        data=logFile.readlines()
    except :
        print "Error in opening", logFile
        raise IOError        

    bestGenes=[]
    
    consolidated_Log=False
    if data[0].find('consolicated docking result') != -1:
        consolidated_Log=True

    #settings['consolidated']=consolidated_Log    
    if consolidated_Log:
        for line in data[1:]:
            if line[0]=='#':
                tmp=line[1:].split()
                if len(tmp)==3:
                    settings[tmp[0]] = tmp[2]
            elif line[0]=='[' :
                #line=line.split()[0]
                bestGenes.append(eval(line))
            else:
                raise ValueError
                print "Invalid format for a consolicated docking log"
                return None, None
    else:
##         for line in data:
##             if line.find("INFO: setting_file") != -1:
##                 tmp=line.split()[1]
##                 settingFile=tmp.split('=')[1]
##                 settings=_parseSettingFile(settingFile)
##             elif line.find("Setting:") == 0:
##                 k,v =line.split()[1:]
##                 try:
##                     v=eval(v)
##                 except:
##                     pass
##                 settings[k]=v
##             else:
##                 if line.find("Docking begins at:") == 0:
##                     break

        for line in data[10:]:
            if line.find("INFO: best_gene") != -1:                
                gene=line.split('=')[1]
                bestGenes.append( list(eval(gene)) )

    return bestGenes



def _parseSettingFile(filename):
    if filename:
        setting={}
        try:
            input_file = file(filename, 'r')
            lines=input_file.readlines()
            for line in lines:
                if line[0] != '#' and line[0] != '\n':
                    line = line.replace(' ', '') 
                    tmp = line.split('\n')[0].split('=')
                    if tmp[1][0] !='\'': # number setting
                        setting[tmp[0]] = eval(tmp[1])
                    else: # string setting
                        strSetting = tmp[1].replace('\'', '') 
                        setting[tmp[0]] = strSetting
        except:
            print
            print "Error in opening ",filename
            print
            return

        if setting.has_key('repeat'):
            self._repeat=setting['repeat']
    else:
        # load default setting ?
        pass
    return setting

def pdbq2XML_old(ligandFile, xmlFilename, printXML=False):
    """automatically generate XML for flexible ligand from pdbq file
ligandFile: ligand file name pdbq format
xmlFilename: output XML file

e.g.
from FlexTree.utils import pdbq2XML
"""
    mol = Read(ligandFile)[0]    
    if mol.torTree is None:
        print "No torTree info found"
    else:
        s=mol.torTree.printXmlTree(mol.allAtoms, 1000)
        file=open(xmlFilename,'w')
        file.write(s)
        file.close()
        if printXML:
            print s
            print "**********************************"
            print "  XML file saved as " + xmlFilename
            print "**********************************"
    return


## <<<<<<< utils.py
## def pdbq2XML(ligandFile, xmlFilename, center=None, dims=None):
##     """automatically generate XML for flexible ligand from pdbq file
## ligandFile: ligand file name pdbq format
## xmlFilename: output XML file
## center: x, y, z center of docking box
## dims: x, y, z diminsions of the docking box
## e.g.
## from FlexTree.utils import pdbq2XML
## """
##     mol = Read(ligandFile)[0]    
##     if mol.torTree is None:
##         print "No torTree info found in", ligandFile
##         return

##     s=mol.torTree.printXmlTree(mol.allAtoms, 1000)
##     file=open(xmlFilename,'w')
##     file.write(s)
##     file.close()

##     if dims==None and center ==None:
##         return

##     # add docking box info
    
##     reader = ReadXML()
##     reader(xmlFilename, cmdLineOnly=True)
##     tree=reader.get()[0]
##     root=tree.root

##     #print "***  ",len(root.getAtoms())

    
##     mol.LPO = LigandPreparation(mol, mode='', root='auto', repairs='',\
##                                 charges_to_add=None, cleanup='')
##     rootOfTorTree=mol.ROOT.coords
##     #assert x !=None and y !=None and z !=None


##     x,y,z=dims
        
##     x2,y2,z2=center   

##     point=[0.,0.,0.]
##     vector=[1.,0.,0.]
##     angle=0.0
##     pointRotationMotion = FTMotion_RotationAboutPoint();
##     pointRotationMotion.configure(angle=angle, vector=vector, \
##                                   point=rootOfTorTree)

##     boxTranslation = FTMotion_BoxTranslation(); 
##     boxTranslation.configure(gridCenter=rootOfTorTree, \
##                              boxDim=dims, point=point)

##     translation2Center=FTMotion_Translation()
##     translation2Center.configure(point1=rootOfTorTree, \
##                                  point2=center,\
##                                  can_be_modified=0)

##     motionList=[pointRotationMotion, boxTranslation,translation2Center]
##     combinedMotion = FTMotionCombiner(); 
##     combinedMotion.configure(motionList =motionList)

##     root.motion=combinedMotion
##     writer = WriteXML()
##     writer([tree], xmlFilename)

##     return


## =======

from MolKit.torTree import TorTree

def getTreeXML(tortree, allAtoms, index=1, selStr=None, rotBondMotion='FTMotion_RotationAboutAxis',
                 module='AutoDockFR.FTMotions'):
    """This function is used to generate XML file for FlexTree package"""
    if not tortree.rootNode: return
    if selStr is None:
        selStr = allAtoms[0].top.name + ":::"
    ostr = '<?xml version="1.0" ?>\n'
    ostr = ostr + '\t<root\n\t\tname="Ligand"\n\t\tid="%d"\n\t\tselectionString="%s"\n\t\tconvolve="FTConvolveApplyMatrixToCoords"\n\t\t'%(99,selStr)
    ostr = ostr + 'file="%s">\n\t'%allAtoms[0].top.parser.filename
    ostr = ostr + '\t<node\n\t\t\tname="Core Ligand"\n\t\t\tid="'+ str(index) +'"\n\t\t\t'
    ostr = ostr + 'shapeParams="cutoff: float 1.85"\n\t\t\t'
    sub_ats=allAtoms.get(lambda x: x.number-1 in tortree.rootNode.atomList)
    selString = sub_ats.full_name()
    ostr = ostr + 'selectionString="%s"\n\t\t\t'%(selString)
    ostr = ostr + 'shape="FTLines"\n\t\t\t'
    ostr = ostr + 'convolve="FTConvolveApplyMatrixToCoords"\n\t\t\t'
    ostr = ostr + '>\n\t\t</node>\n'
    next_index = index + 1
    for c in tortree.rootNode.children:
        ost, next_index = getNodeXML(tortree, c, next_index, index, allAtoms, rotBondMotion, module)
        ostr = ostr + ost
    ostr = ostr + "</root>\n\n"
    return ostr


def getNodeXML(tortree, node, next_index, refNode, allAtoms, rotBondMotion='FTMotion_RotationAboutAxis',
                   module='AutoDockFR.FTMotions'):
    ostr = '\t\t<node\n\t\t\tname="sidechain%d"\n\t\t\tid="%d"\n\t\t\trefNode="%d"\n\t\t\t'%(node.number, next_index, refNode)
    this_nodes_index = next_index
    next_index += 1
    ostr = ostr + 'shapeParams= "cutoff: float 1.85"\n\t\t\t'
    at1 = allAtoms.get(lambda x: x.number-1==node.bond[0])[0]
    at2 = allAtoms.get(lambda x: x.number-1==node.bond[1])[0]
    atmList = node.atomList[:]
    sub_ats=allAtoms.get(lambda x: x.number-1 in atmList)
    ##IS THIS CORRECT??
    ##sub_ats.insert(0, at2)
    #print "len(sub_ats)=", len(sub_ats), " for node number ", node.number
    selectionString = sub_ats.full_name()
    ostr = ostr + 'selectionString="%s"\n\t\t\t'%(selectionString)
    ostr = ostr + 'module="%s"\n\t\t\t'%module
    ostr = ostr + 'motion="%s"\n\t\t\t'%rotBondMotion
    ostr = ostr + 'shape = "FTLines"\n\t\t\t'
    ostr = ostr + 'convolve="FTConvolveApplyMatrixToCoords"\n\t\t\t'
    mPs = '"'
    ats = [at1, at2]
    for i in [0,1]:
        at = ats[i]
        mPs = mPs + "point%d: list float %f %f %f, "%(i+1, at.coords[0], at.coords[1], at.coords[2])
    mPs = mPs + ' percent: float 1.0, angle: float 0.0, name: str rotatableBond">'
    ostr = ostr + 'motionParams=%s"\n\t\t'%mPs
    ostr = ostr + "</node>\n\n"

    for c in node.children:
        ost, next_index =  getNodeXML(tortree, c, next_index, this_nodes_index, allAtoms, rotBondMotion, module)
        ostr = ostr + ost
    return ostr, next_index


def pdbqt2XML(mol, xmlFilename, center, dims):
    """automatically generate XML for flexible ligand from pdbqt file
ligandFile: ligand file name pdbqt format
xmlFilename: output XML file
center: x, y, z center of docking box
dims: x, y, z diminsions of the docking box
e.g.
from FlexTree.utils import pdbq2XML
    """
    #from MolKit import Read
    #mol = Read(ligandFile)[0]    
    if mol.torTree is None:
        print "No torTree info found in", ligandFile
        return

    s = getTreeXML(mol.torTree, mol.allAtoms, 1000,
                   rotBondMotion = 'GAFTMotion_RotationAboutAxis',
                   module = 'AutoDockFR.FTGA')
    file = open(xmlFilename,'w')
    file.write(s)
    file.close()

    # add docking box info
    from FlexTree.XMLParser import ReadXML,WriteXML
    reader = ReadXML()
    reader(xmlFilename, cmdLineOnly=True)
    tree=reader.get()[0]
    root=tree.root

    #print "***  ",len(root.getAtoms())

    from AutoDockTools.MoleculePreparation import LigandPreparation
    #from MolKit import Read
    #mol = Read(ligandFile)[0]
    #mol.ROOT = mol.allAtoms[0]

    # LigandPreparation modifies TORSDOF and sets ROOT
    #torsdof = mol.TORSDOF
    #mol.LPO = LigandPreparation(mol, mode='', root='auto', repairs='',\
    #                            charges_to_add=None, cleanup='')
    # restore correct mol.TORSDOF
    #mol.TORSDOF = torsdof

    # rootOfTorTree is the atom that is selected that must be inside the docking box.
    print "Ligand ROOT atom: %s" % mol.ROOT.full_name()
    if mol.ROOT != mol.allAtoms[0]:
        print 'WARNING: POSSIBLE ROOT PROBLEM first atom is %s but ROOT is set to %s'%(
            mol.allAtoms[0].full_name(), mol.ROOT.full_name()) 
    rootOfTorTree=mol.ROOT.coords

    #assert x !=None and y !=None and z !=None
    x,y,z=dims
        
    #if auto:  # docking box center at root of ligand torTree. (redocking?)
    #    dockingBoxCenter=rootOfTorTree
    #else:
    #    assert x2!=None and y2!=None and z2!=None        
    #    dockingBoxCenter=[x2,y2,z2]
    
    #assert x2!=None and y2!=None and z2!=None
    x2,y2,z2=center   

    point=[0.,0.,0.]
    vector=[1.,0.,0.]
    angle=0.0
    ## pointRotationMotion = FTMotion_RotationAboutPoint();
    ## pointRotationMotion.configure(angle=angle, vector=vector, \
    ##                               point=rootOfTorTree)
    from FTGA import GAFTMotion_BoxTranslation,\
         GAFTMotion_RotationAboutPointQuat, GAFTMotion_Translation
    
    pointRotationMotion = GAFTMotion_RotationAboutPointQuat();
    pointRotationMotion.configure(quat = (0,0,0,1), point=rootOfTorTree)

    boxTranslation = GAFTMotion_BoxTranslation(); 
    boxTranslation.configure(gridCenter=rootOfTorTree, \
                             boxDim=dims, point=point)

    translation2Center = GAFTMotion_Translation()
    translation2Center.configure(point1=rootOfTorTree, \
                                 point2=center,\
                                 can_be_modified=0)

    motionList=[pointRotationMotion, boxTranslation, translation2Center]

    from FlexTree.FTMotions import FTMotionCombiner
    combinedMotion = FTMotionCombiner(); 
    combinedMotion.configure(motionList = motionList)

    root.motion=combinedMotion
    writer = WriteXML()
    writer([tree], xmlFilename)

    return

from MolKit.molecule import MoleculeSet

class RecXML4SoftRotamSC:
    """
Automatically generate a FT for a receptor with soft rotameric side chains
"""

    def __init__(self, mol, movingSC):
        """
        constructor RecXML4SoftRotamSC class

        mol - receptor molecule in pdbqt format
        movingSC - string specifying flexible side chains (e.g. as specified
                   in setting file uing movingSC keyword
                   '1HVI:A:ARG8;1HVI:B:ARG8;' 
        """

        from MolKit.stringSelector import CompoundStringSelector
        css = CompoundStringSelector()

        # we overwrite the molecule name with the mol.name
        if  movingSC.find(';') != -1:
            flexchains = movingSC.split(';')
            ww = flexchains[0]
            for i in range(len(flexchains)-1):
                flexc2 = flexchains[i+1].split(':')
                ww = ww +','+flexc2[2]
            w = ww.split(':')
        else:
            w = movingSC.split(':')
        #w = movingSC.split(':')
        #if len(w)==3:
        #    movingSC = '%s:%s:%s'%(mol.name, w[1], w[2])

        result = css.select(MoleculeSet([mol]), movingSC)
        if len(result[0])==0:
            raise ValueError("ERROR: %s does not select anything in molecule %s"%(movingSC, mol.name))
        elif len(result[0])!=len(w[2].split(',')):
            raise ValueError("ERROR: %s selected %d residues while %d were expected"%(movingSC, len(result[0]), len(w[2].split(','))))

        result = result[0]                

        # make sure it's a ResidueSet
        if not isinstance(result, ResidueSet):
            raise ValueError("ERROR: %s does not select residues in molecule %s"%(movingSC, mol.name))

        from AutoDockFR.FTGA import GAFTMotion_SoftRotamer
        from FlexTree.FT import FlexTree
        tree = FlexTree(name="receptorFR")
        tree.root = tree.newNode(name='recFT_root') # create empty root node
        tree.root.rigid = True
        tree.flexNodeList=[]
        
        from MolKit.molecule import AtomSet
        self.interfaceAtoms = AtomSet([])

        motions = []
        for res in result: # loop over moving residues
            print "adding rotamer", res.name
            if res.name[:3] in ['ALA','GLY']:
                print '\tNo rotamer defined for' , res.name
                continue

            resAtoms = res.atoms
            if len(resAtoms[0]._coords)==1:
                resAtoms.addConformation(resAtoms.coords)

            self.interfaceAtoms.append( res.childByName['CA'] )
            self.interfaceAtoms.append( res.childByName['CB'] )
            anchorAtoms = None
            # GAFTMotion_SoftRotamer(res reorders atoms in residue so that
            # the first 6 are Hn C O N CA CB
            motion = GAFTMotion_SoftRotamer(res, anchorAtoms)
            motions.append(motion)
            node = tree.newNode(molFrag=res.atoms[6:], discreteMotion=motion,
                                refNode=tree.root, name=res.name)
            node.rigid = False
            tree.root.children.append(node)
            tree.flexNodeList.append(node)
        self.tree = tree

    def writeXML(self, filename):
        self.tree.save(filename)
        
    
    def getTree(self):
        return self.tree


class RecXML4SoftRotamSC_OLD:
    """
Automatically generate a FT for a receptor with soft rotameric side chains
"""

    def __init__(self, mol, movingSC):
        """
        constructor RecXML4SoftRotamSC class

        mol - receptor molecule in pdbqt format
        movingSC - string specifying flexible side chains (e.g. as specified
                   in setting file uing movingSC keyword
                   '1HVI:A:ARG8;1HVI:B:ARG8;' 
        """
        ## initialize a FT here.
        from FlexTree.FT import FlexTree
        self.tree = FlexTree(mol=mol)

        from MolKit.stringSelector import CompoundStringSelector
        css = CompoundStringSelector()
        tmp = MoleculeSet()
        tmp.append(mol)

        ## select moving sidechains
        result = css.select(tmp, movingSC)
        if len(result)==0:
            raise ValueError("ERROR: %s does not select anything in molecule %s"%(movingSC, mol.name))
        result = result[0]                

        # we do not really need the whole receptor in the root node
        # just put the residues with flexible side chains
        self.tree.root.molecularFragment = result.atoms
        
        # make sure it's a ResidueSet
        if not isinstance(result, ResidueSet):
            raise ValueError("ERROR: %s does not select residues in molecule %s"%(movingSC, mol.name))

        self.sidechains = result
        print len(result), "sidechains to be flexible"
        self.interfaceAtoms = AtomSet([])
        
        for res in self.sidechains:
            print "adding rotamer", res.name
            if res.name[:3] in ['ALA','GLY']:
                print '\tNo rotamer defined for' , res.name
                continue
            
            resAtoms = res.atoms
            resAtoms.addConformation(resAtoms.coords)
            # get residue CA and CB atoms. They are interface atoms
            self.interfaceAtoms.append( res.childByName['CA'] )
            self.interfaceAtoms.append( res.childByName['CB'] )
            # get side chain moving atoms
            sidechain = resAtoms.get('sidechain') - resAtoms.get('CB')
            
            # do not define anchorAtoms, else it will setup a localFrame
            # which includes the transformation of anchor atoms at origine
            # to actual residue position
            #anchor=[]
            #for name in ['CB','CA','C']:
            #    anchor.append(resAtoms.get(name)[0])
            #anchor = AtomSet(anchor)
            motion = GAFTMotion_SoftRotamer(res, None)
            motion.configure(sideChainAtomNames=sidechain.name, 
                             residueName=res.name)
            self.tree.root.splitNode(sidechain.full_name(),
                                     discreteMotion=motion,
            #                         anchorAtoms=anchor,
                                     name=res.full_name())

        self.tree.updateStatus()
        rigidAtoms = self.tree.getRigidAtoms()
        motions = self.tree.getAllMotion()
        for m in motions:
            if isinstance(m, GAFTMotion_Rotamer):
                m._buildConfList()
                m.removeClashWith(rigidAtoms)
            #elif isinstance(m, GAFTMotion_SoftRotamer):
            #    m.removeClashWith(rigidAtoms)

        # set originalConf to None for the root node and the first child which
        # is the core. This is done to avoid extra calculation in
        # updateCurrentConformation
        self.tree.root.originalConf = None
        self.tree.root.children[0].originalConf = None

        
    def writeXML(self, filename):
        self.tree.save(filename)
        
    
    def getTree(self):
        return self.tree


class RecXML4RotamSC:
    """
    automatically generate a FT for a receptor that has rotameric side chains
"""

    def __init__(self, mol, movingSC):
        """
        constructor ReceptorXMLwithRotamericSideChains class

        mol - receptor molecule in pdbqt format
        movingSC - string specifying flexible side chains (e.g. as specified
                   in setting file uing movingSC keyword
                   '1HVI:A:ARG8;1HVI:B:ARG8;' 
        """
        ## initialize a FT here.
        from FlexTree.FT import FlexTree
        self.tree = FlexTree(mol=mol)

        from MolKit.stringSelector import CompoundStringSelector
        css = CompoundStringSelector()
        tmp = MoleculeSet()
        tmp.append(mol)

        ## select moving sidechains
        result = css.select(tmp, movingSC)
        if len(result)==0:
            raise ValueError("ERROR: %s does not select anything in molecule %s"%(movingSC, mol.name))
        result = result[0]                

        # make sure it's a ResidueSet
        if not isinstance(result, ResidueSet):
            raise ValueError("ERROR: %s does not select residues in molecule %s"%(movingSC, mol.name))

        self.sidechains = result
        print len(result), "sidechains to be flexible"

        for res in self.sidechains:
            print "adding rotamer", res.name
            if res.name[:3] in ['ALA','GLY']:
                print '\tNo rotamer defined for' , res.name
                continue
            
            resAtoms=res.atoms
            sidechain = resAtoms.get('sidechain')-resAtoms.get('CB')
            
            anchor=[]
            for name in ['CB','CA','C']:
                anchor.append(resAtoms.get(name)[0])
            anchor = AtomSet(anchor)
            motion = GAFTMotion_Rotamer()
            motion.configure(sideChainAtomNames=sidechain.name, \
                             residueName=res.name)
            self.tree.root.splitNode(sidechain.full_name(), \
                                     discreteMotion=motion, \
                                     anchorAtoms=anchor,
                                     name=res.full_name())

        self.tree.updateStatus()
        rigidAtoms = self.tree.getRigidAtoms()
        motions = self.tree.getAllMotion()
        for m in motions:
            if isinstance(m, GAFTMotion_Rotamer):
                m._buildConfList()
                m.removeClashWith(rigidAtoms)

        # set originalConf to None for the root node and the first child which
        # is the core. This is done to avoid extra calculation in
        # updateCurrentConformation
        self.tree.root.originalConf = None
        self.tree.root.children[0].originalConf = None

        
    def writeXML(self, filename):
        self.tree.save(filename)
        
    
    def getTree(self):
        return self.tree

""" MLD: I dont think this is function is called anywhere and is old 3.05 legacy code
def getClosestEnergyRotamer(flexResidueSet, coreAtomSet, E_cutoff=10.0):
    ### this function get input of a residue set. For each residue, the rotamer
    ### library will be loaded. The most similar rotamer (by RMSD) will be located.
    ### After checking the AutoDock energy,(make sure no clash with  coreAtomSet),
    ### the rotamer conformation will be the conformation of the residue.

    ### E_cutoff is used to check if there's clash between sidechain and core atoms

    ### output: The same residue set with rotamer conformation

    if not isinstance(flexResidueSet, ResidueSet):
        return

    if not isinstance(coreAtomSet, AtomSet):
        return

    from AutoDockFR.ScoringFunction import AD305ScoreC,ADSinglePoint

    newResSet=flexResidueSet[:]    
    from FlexTree.RotLib import RotLib
    from FlexTree.FTMotions import defineLocalCoordSys
    from mglutil.math.rmsd import RMSDCalculator   
    bestRotamerConf=[]

    for i in range(len(flexResidueSet[:])):
        residueName = newResSet[i].name
        residueName=residueName[:3]
        if residueName not in RotLib.keys():
            print
            print residueName, "not found in rotamer library\n"
            return None

        allAtm=newResSet[i].atoms
        anchorAtoms=allAtm.get('CB,CA,C')
        anchors= anchorAtoms.coords
        CB=N.array(anchors[0],'f')
        CA=N.array(anchors[1],'f')
        C =N.array(anchors[2],'f')            
        mat=defineLocalCoordSys(CB, CA, C)
        transform = Numeric.identity(4, 'f')
        transform[:3,:3] = mat
        transform[:3,3] = anchorAtoms[1].coords #C-Alpha
        transform=N.transpose(transform)

        sidechainAts=allAtm.get('sidechain')        
        RMSD = RMSDCalculator(refCoords =sidechainAts.coords)
        lib=RotLib[residueName]
        data={}
        for j in range(len(lib)):
            conf=lib[j]
            coords=[]
            for a in sidechainAts:
                coords.append(conf[a.name])

            hcoords = N.concatenate((coords,N.ones( (len(coords), 1), 'd')), 1)
            mob=N.matrixmultiply(hcoords,transform).astype('f')
            mob=mob[:,:3]
            rmsd=RMSD.computeRMSD(mob)
            data[rmsd]=mob.tolist()

        # now make sure no clash with core atoms.
        keys=data.keys()
        keys.sort()
        found=False
        for key in keys:
            sidechainAts.updateCoords(data[key])
            scoreObject = AD305ScoreC(coreAtomSet, sidechainAts)
            s0=scoreObject.scorer.get_score()
            if s0 < E_cutoff:
                bestRotamerConf.extend(data[key] )
                found=True
                break
            else:
                print newResSet[i].name, key, s0

        if not found:
            print "No rotamer conformation for %s is found."%newResSet[i].name

    return bestRotamerConf
"""


def selectFlexSideChainInNbr(allAtoms, nbr, cutoff=100):
    """select flexible sidechains within neighbor..\

    fixme... self=Pmv
    this should NOT be put here..
    fixme..
    """
    result=[]
    for at in allAtoms:
        if at not in nbr:
            continue
        if at.name in ['C','CA','CB','O','N']:
            continue
        if at.constraint < cutoff:
            result.append(at)
    result= AtomSet(result)
    res=result.parent.uniq()
    print res.name
    return  res


def adjustDockingBoxSize(ligandXMLFile, newDim=None):
    """ this function will adjust the docking box dimensions defined in
    ligand XML file.

    if newDim is NOT specified:
    The ligand in AutoDock can not move outside of the grid map. The actual
    docking box size is SMALLER than the grid map size.

    if newDim is not None, the box dimension is updated to newDim
    
    """

    from FlexTree.XMLParser import ReadXML,WriteXML
    reader = ReadXML()
    reader(ligandXMLFile, cmdLineOnly=True)
    tree=reader.get()[0]
    root=tree.root
    from FlexTree.FTMotions import FTMotionCombiner,\
         FTMotion_BoxTranslation, dist
    if not isinstance(root.motion, FTMotionCombiner):
        return

    motions= root.motion.motionList
    ligCenter=motions[0].point
    assert (ligCenter!=None)    
    #print "ligand center at ", ligCenter
    motion=motions[1]
    #print "original box dim",motion.boxDim


    if newDim is None:
        from MolKit import Read
        ligMol=Read(tree.pdbfilename)[0]
        allAtoms=ligMol.allAtoms
        MAX_DIST=-1
        for a in allAtoms:
            d = dist(a.coords, ligCenter)
            if d > MAX_DIST:
                MAX_DIST=d
        motion.boxDim[0] -=  MAX_DIST
        motion.boxDim[1] -=  MAX_DIST
        motion.boxDim[2] -=  MAX_DIST
        print "max dist", MAX_DIST
    else:
        assert len(newDim)==3
        motion.configure(boxDim=newDim)
        
    writor = WriteXML(tree)
    writor([tree], ligandXMLFile)
    return
    
def locateDockingBoxInfo(flextree):
    """ this function will extract the docking box center and dimenstions
    """
    try:
        from FlexTree.FT import FlexTree
        from FlexTree.FTMotions import FTMotionCombiner
        assert isinstance(flextree, FlexTree)
        motion=flextree.root.motion
        assert isinstance(motion, FTMotionCombiner)        
        motions= motion.motionList
        return motions[2].point2, motions[1].boxDim
    except: 
        return None,None
    

## obsolete after Feb 2006
## def updateDockingBoxInfo(flextree, newCenter, newDim):
##     """ this function will update the docking box center and dimenstions
##     return True if sucess, False otherwise
##     """
##     dockingBox=_findBoxTranslationMotion(flextree)
##     if dockingBox:
##         ## Notice that no transformation is updated.
##         dockingBox.gridCenter=newCenter
##         dockingBox.boxDim=newDim
##         return True
##     else:
##         return False


def updateDockingBoxInfo(flextree, newCenter, newDim):
    """ this function will update the docking box center and dimenstions
    return True if sucess, False otherwise
    """
    motions=flextree.root.motion.motionList
    translate_to_BoxCenter=motions[2]
    beginPoint=translate_to_BoxCenter.point1[:]
    translate_to_BoxCenter.configure(beginPoint=beginPoint,endPoint=newCenter)
    box_translation=motions[1]
    box_translation.configure(boxDim=newDim)
    return

def addDockingBox(flextree, newCenter, newDim):
    """ this function will add a docking box to the root of the given FT.
docking box center and dimenstions must be specified.
return True if sucess, False otherwise
    """
    root=flextree.root
    from FlexTree.FTMotions import FTMotionCombiner,\
         FTMotion_BoxTranslation,\
         FTMotion_RotationAboutPoint, FTMotion_Translation

    from AutoDockTools.MoleculePreparation import LigandPreparation
    from MolKit import Read
    mol=Read(flextree.pdbfilename)[0]
    mol.LPO = LigandPreparation(mol, mode='', root='auto')
    rootOfTorTree=mol.ROOT.coords

    point=[0.,0.,0.]
    vector=[1.,0.,0.]
    angle=0.0

    pointRotationMotion = FTMotion_RotationAboutPoint();
    pointRotationMotion.configure(angle=angle, vector=vector, \
                                  point=rootOfTorTree)

    boxTranslation = FTMotion_BoxTranslation(); 
    boxTranslation.configure(gridCenter=rootOfTorTree,
                             boxDim=newDim, point=point)

    translation2Center=FTMotion_Translation()
    translation2Center.configure(point1=rootOfTorTree,
                                 point2=newCenter,\
                                 can_be_modified=0)

    motionList=[pointRotationMotion, boxTranslation,translation2Center]
    combinedMotion = FTMotionCombiner(); 
    combinedMotion.configure(motionList =motionList)

    root.motion=combinedMotion


    ##
    motions=flextree.root.motion.motionList
    translate_to_BoxCenter=motions[2]
    beginPoint=translate_to_BoxCenter.point1[:]
    translate_to_BoxCenter.configure(beginPoint=beginPoint,\
                                     endPoint=newCenter)
    box_translation=motions[1]
    box_translation.configure(boxDim=newDim)
    return


def divideAndConquer(ligandTree, x_div=1, y_div=1, z_div=1):
    """ this function will divide the docking box into smaller boxes
, with x dimention be divided into x_div segments, y dimention be divided into
y_div segments and z dimention be divided into z_div segments
i.e. x_div * y_div * z_div boxes will be generated.
returns a list of box centers
e.g.  [[0,0,0],[0,0,3],[0,1,3], ... [3,3,3] ]
    """
    assert type(x_div)==types.IntType and \
           type(y_div)==types.IntType and \
           type(z_div)==types.IntType
    
    center,dim=locateDockingBoxInfo(ligandTree)
    if center is None and dim is None:
        return None
    center=N.array(center, 'f')
    dim=N.array(dim, 'f')
    newDim=dim/N.array([x_div,y_div,z_div], 'f')
    minCorner=center-dim/2.0
    maxCorner=center+dim/2.0
    
    centerList=[]
    dimList=[]
    from math import ceil, floor
    for x in range(1,x_div+1):
        for y in range(1, y_div+1):
            for z in range(1,z_div+1):
                pX= minCorner[0] + newDim[0]*(x-0.5)
                pY= minCorner[1] + newDim[1]*(y-0.5)
                pZ= minCorner[2] + newDim[2]*(z-0.5)
                centerList.append([pX, pY, pZ])

    return centerList, newDim.tolist()
    


from AutoDockFR.ADCscorer import AD42ScoreC


## def saveGA_Result(xmlFileName, pyDockLogFileName, outputFileName):
##     """ This function opens pyDock log file (pyDockLogFileName) and FlexTree definition file (xmlFileName) and saves the best (last) docking conformation as PDB file (outputFileName)

##     e.g.
##     from FlexTree.utils import *
##     saveGAResult('rigidMonomer.xml', 'rLog.txt', 'result.pdb')


##     """
##     # begin docking test
##     from FlexTree.XMLParser import ReadXML
##     reader = ReadXML()
##     reader(xmlFileName)
##     tree=reader.get()
##     root=tree[0].root

##     ga_value=findBestGenes(pyDockLogFileName)

##     atmSet=root.children[0].getAtoms()
##     for i in range(1,len(root.children) -1):
##         atmSet += root.children[i].getAtoms()

##     ligandSet = tree[0].root.children[-1].getAtoms()

##     #from FlexTree.VisionInterface.FlexTreeNodes import FTtreeGaRepr
##     from AutoDockFR.FTGA import FTtreeGaRepr

##     setting={}
##     setting['calcIE']=True
##     scorerVersion = "C++"

##     if scorerVersion == "C++":
##         # C++ scorer
##         from AutoDockFR.ADCscorer import AD42ScoreC
##         scoreObject = AD42ScoreC(atmSet, ligandSet, setting['calcIE'])
##     elif scorerVersion == "Python":
##         # Python scorer
##         from AutoDockFR.AutoDockPyscorer import AD305Scoring
##         scoreObject = AD305Scoring(atmSet, ligandSet, setting['calcIE'])
##     #MLD: I think this is now gone due to old 3.05 code
##     #elif scorerVersion == "IEC++":
##     #    # Internal Energy C++  scorer
##     #    from AutoDockFR.ScoringFunction import ADSinglePoint
##     #    atmSet=root.getAtoms()
##     #    scoreObject = ADSinglePoint(atmSet)
##     #
##     elif scorerVersion == "Amber": # fixme.. not available yet
##         # Python scorer
##         from AutoDockFR.AMBERscorer import AmberScoringIE
##         atmSet=root.getAtoms()
##         scoreObject = AmberScoringIE(atmSet)
##     elif scorerVersion == "RMSD": # fixme.. not available yet.
##         # RMSD compare as a scorer
##         from AutoDockFR.RMSDscorer import RMSDScoring
##         atmSet=root.getAtoms()
##         scoreObject = RMSDScoring()
##         print "Using Amber scorer"
##     else:
##         print "Unknown scorer"
##         raise ValueError

##     print

##     FlexTree = tree[0]
##     gnm = FTtreeGaRepr(FlexTree, scoreObject)
##     nodes=root.getAtoms()

##     RR_coords, FR_coords, L_coords = ga_value.toPhenotype(sort=True)
##     nodes.sort()
##     nodes.updateCoords(coords, 1)
##     nodes.setConformation(1)
##     mol = nodes.top.uniq()
##     assert len(mol)==1
##     recType = 'all'  

##     from MolKit import WritePDB
##     WritePDB(outputFileName, nodes)


## def saveGA(receptorXML, ligandXML, geneList, output, \
##            calcLigIE=True, calcRecIE=True):
##     """ This function generate PDB file for FlexTree configured by the gene
## e.g.
## from FlexTree.utils import saveGA
## geneList=[0.36715177893638618, 0.60282641649246216, 0.71397606134414671, 1.014633196592331, 0.55035650730133057, -0.19258373975753784, 0.21273575723171234, 128.99987697601318, 0.65661728382110596, 1.6163424253463745, 1.5744699239730835, 0.7795202553272248, 0.96915743350982675, 1.0348480147123338, 0.26760440468788149, -0.014060399308800695, 0.021154772490262985, 0.92297428846359253, 0.70623414635658266, 0.12198185473680496, 0.81448343992233274]

## from FlexTree.utils import saveGA
## saveGA(receptorXML='1hvr_docking.xml', ligandXML='1hvrLig.xml',\
##        geneList = geneList, output='test00')

##     """
##     # begin docking test
##     from FlexTree.XMLParser import ReadXML
##     reader = ReadXML()
##     reader(receptorXML, cmdLineOnly=True)
##     R_tree=reader.get()[0]
##     R_root=R_tree.root

##     reader(ligandXML, cmdLineOnly=True)
##     L_tree=reader.get()[0]
##     L_root=L_tree.root

##     R_root.updateCurrentConformation()
##     L_root.updateCurrentConformation()

##     recAtms = R_root.getAtoms()[:]
##     ligAtms = L_root.getAtoms()[:]
##     setting={}
##     setting['calcIE']=True
##     scorerVersion = "C++"

##     from AutoDockFR.FTGA import FTtreeGaRepr
##     from AutoDockFR.ADCscorer import  AD42ScoreC

##     from MolKit.pdbWriter import PdbqsWriter, PdbqWriter
##     rec=recAtms[:]
##     lig=ligAtms[:]
##     scoreObject = AD42ScoreC(rec, lig, calcLigIE=calcLigIE, \
##                               calcRecIE=calcRecIE,receptorFT=R_tree)

##     for i in  range(len(geneList)):
##         gene=geneList[i]
##         gnm = FTtreeGaRepr(R_tree, L_tree, scoreObject)
##         TotalScore=scoreObject.score(gnm, gene)
##         #print TotalScore
##         scoreObject.printAllScoreTerms()

##         if output !=None and output !="":
##             R_coords, L_coords = gene.toPhenotype(sort=True)
##             rec.sort()  #?
##             rec.updateCoords(R_coords, 1)
##             rec.setConformation(1)
##             lig.sort()  #?
##             lig.updateCoords(L_coords, 1)
##             lig.setConformation(1)

##             writer=PdbqWriter()
##             writer.write(output+str(i)+'.pdbq', lig)
##             writer = PdbqsWriter()
##             writer.write(output+str(i)+'.pdbqs', rec)

##     # cleaning up
##     #scoreObject.freeSharedMem()
##     return

## def saveGA_RMSD(settingFile, geneList, output):        
##     """ This function generate PDB file for RMSD docking result
## e.g.
## from FlexTree.utils import saveGA_RMSD
## geneList=[0.20734765008091927, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.66432253159582599, 0.5177152425050735]
## #saveGA_RMSD(receptorXML='1cew_ED.xml',refMol='1A90_10.pdb',
## #geneList=[geneList],output='test00')
##     """
##     # begin docking test
##     setting=_parseSettingFile(settingFile)
##     must_have_keys=['mobAtomStr', 'XML_file', 'reference', 'refAtomStr', \
##                     'superimpose']
##     keys=setting.keys()
##     for k in must_have_keys:
##         assert k in keys

##     from FlexTree.XMLParser import ReadXML
##     reader = ReadXML()
##     reader(setting['XML_file'], cmdLineOnly=True)
##     tree=reader.get()[0]
##     mobAtms = tree.root.getAtoms()[:]

##     from AutoDockFR.FTGA import OneFT_GaRepr
##     from MolKit.pdbWriter import PdbqsWriter, PdbWriter, PdbqWriter
##     from AutoDockFR.RMSDscorer import RMSDScoring
##     rec=mobAtms[:]
##     mol=Read(setting['reference'])[0]
##     refAtoms=mol.allAtoms

##     scoreObject = RMSDScoring(mobAtomset=mobAtms,
##                               refAtomset=refAtoms,
##                               mobAtomStr=setting['mobAtomStr'],
##                               refAtomStr=setting['refAtomStr'],
##                               superimpose=setting['superimpose'] )
##     rec.sort()
##     parser=mol.parser.__class__.__name__
##     ext=''
##     if parser == 'PdbParser':
##         writer = PdbWriter()
##         ext='.pdb'
##     elif parser == 'PdbqParser':
##         writer = PdbqWriter()
##         ext='.pdbq'
##     elif parser == 'PdbqsParser':
##         writer = PdbqsWriter()
##         ext='.pdbqs'
##     else:
##         print "unknown parser found:", parser
##         return
##     gnm = OneFT_GaRepr(tree, scoreObject)
##     for i in  range(len(geneList)):
##         gene=geneList[i]
##         R_coords=gnm.toPhenotype(gene, sort=True )
##         rec.updateCoords(R_coords, 1)
##         rec.setConformation(1)            
##         writer.write(output+str(i)+ext, rec)
##         print gene
##         print -gnm.scorer.score(gnm, gene)

##     return


def RMSDLog_to_PDB(rmsdDockingLog, outputPrefix=None):
    """ This function generate PDB(Q,QS) file from RMSD docking log
"""
    def _validate(setting):
        mustHaveKeys=['LigandXML', 'reference']
        keys=setting.keys()
        for k in mustHaveKeys:
            if k not in keys:
                print "setting file '%s' does not have the setting for %s"\
                      %(setting, k)
                return False
        return True

    data, setting=findBestGenes(rmsdDockingLog)
    if setting==None and data==None: # when error in loading file
        return 
    if not _validate(setting):
        return  

    if outputPrefix is not None:
        output=outputPrefix
    else:
        output=setting['reference'].split('/')[-1]
        output=output.split('.')[-2]
    saveGA_RMSD(setting['LigandXML'],setting['reference'], data,
                output,setting['selection'], setting['superimpose'] )

    return 


## def getCoordsAndScores(R_tree, L_tree, geneList, scoreObject,
##                        calcLigandIE=True, calcReceptorIE=False):
##     """ returns the coords of ligand and receptor, as well as the scores"""
##     R_root=R_tree.root
##     L_root=L_tree.root
##     R_root.updateCurrentConformation()
##     L_root.updateCurrentConformation()

##     recAtms = R_root.getAtoms()
##     ligAtms = L_root.getAtoms()

##     setting={}
##     setting['calcIE']=True
##     scorerVersion = "C++"

##     from MolKit.pdbWriter import PdbqsWriter, PdbqWriter
##     from AutoDockFR.FTGA import FTtreeGaRepr
##     #scoreObject = AD305ScoreC(recAtms, ligAtms, calcLigIE=calcLigandIE, \
##     #                          calcRecIE=calcReceptorIE, receptorFT=R_tree)
##     receptorCoords=[]
##     ligandCoords=[]
##     scores=[]
##     gnm = FTtreeGaRepr(R_tree, L_tree, scoreObject)
##     for i in  range(len(geneList)):
##         gene=geneList[i]
##         score= 0.0 - scoreObject.score(gnm, gene)
##         #print "score =",score
##         #print scoreObject.printAllScoreTerms()
##         scores.append(score)
##         R_coords, L_coords=gnm.toPhenotype(gene, sort=True)
##         receptorCoords.append(R_tree.root.getCurrentSortedConformation2())
##         ligandCoords.append(L_tree.root.getCurrentSortedConformation2())

## ##             rec = R_root.getAtoms()[:]
## ##             lig = L_root.getAtoms()[:]

## ##             conf=rec[0].conformation
## ##             if conf != 1:
## ##                 rec.setConformation(1)
## ##             rec.updateCoords(R_coords, 1)
## ##             rec.sort()
## ##             receptorCoords.append(rec.coords)
## ##             if conf != 1: 
## ##                 rec.setConformation(conf)

## ##             conf=lig[0].conformation    
## ##             if conf != 1:
## ##                 lig.setConformation(1)
## ##             lig.updateCoords(L_coords, 1)
## ##             lig.sort()
## ##             ligandCoords.append(lig.coords)
## ##             if conf != 1:
## ##                 lig.setConformation(conf)

##     #scoreObject.freeSharedMem()
##     #print 'ok'
##     return receptorCoords, ligandCoords , scores



def geneToScore(settings, geneList):

    receptorXML=settings['ReceptorXML']
    ligandXML=settings['LigandXML']
    from FlexTree.XMLParser import ReadXML

    reader = ReadXML()
    reader(receptorXML, cmdLineOnly=True)
    R_tree=reader.get()[0]
    R_root=R_tree.root

    reader(ligandXML, cmdLineOnly=True)
    L_tree=reader.get()[0]
    L_root=L_tree.root

    ga_value=geneList

    atmSet=R_root.getAtoms()[:]
    ligandSet = L_root.getAtoms()[:]

    #from FlexTree.VisionInterface.FlexTreeNodes import FTtreeGaRepr
    from AutoDockFR.FTGA import FTtreeGaRepr

    setting={}
    setting['calcIE']=True
    scorerVersion = "C++"

    if scorerVersion == "C++":
        # C++ scorer
        from AutoDockFR.ADCscorer import AD42ScoreC
        scoreObject = AD42ScoreC(atmSet, ligandSet, settings['calcLigIE'],\
                                  settings['calcLigIE'], R_tree)
    else:
        print "Unknown scorer"
        raise

    #print 'before docking, score = %7.5f'%scoreObject.scorer.get_score()

    gnm = FTtreeGaRepr(R_tree, L_tree, scoreObject)

    """
    #R_coords, L_coords=gnm.toPhenotype(ga_value, sort=True)
    R_coords, L_coords=gnm.toPhenotype(ga_value, sort=False)    
    #scoreObject.sharedMem[:] = Numericarray(R_coords+L_coords, 'f')[:]
    scoreObject.sharedMem[scoreObject.numRigidAtoms:]=N.array(R_coords+\
                                                              L_coords, \
                                                              'f')[:]
    print
    print 'after AD305ScoreC...',
    scoreObject.updateCoords(scoreObject.proteinLen, scoreObject.msLen,
                             scoreObject.molSyst,
                             scoreObject.sharedMemPtr)
    """
    AutoDockFR_Scores=[]
    E_lig_rec=[]
    for gene in geneList:
        AutoDockFR_Scores.append(0-scoreObject.score(gnm, gene) )
        E_lig_rec.append(scoreObject.scorer.get_score())
    return AutoDockFR_Scores, E_lig_rec


def flexLigandXML(ligandFile, xmlFilename, printXML=False):
    """automatically generate XML for flexible ligand
ligandFile: ligand file name (in pdb, pdbq, pdbqs format)
xmlFilename: output XML file

e.g.
from FlexTree.utils import flexLigandXML

    """
    m2 = Read(ligandFile)[0]
    m2.buildBondsByDistance()
    ligandName=ligandFile.split(".")[0]
    outFilename="./"+ligandName+".pdbq"

    from AutoDockTools.MoleculePreparation import LigandPreparation
    LPO = LigandPreparation(m2)
    LPO.write(outFilename)

    mol=Read(outFilename)[0]
    if mol and xmlFilename:
        if mol.torTree is None:
            print "No torTree info found"
        else:
            s=mol.torTree.printXmlTree(mol.allAtoms, 1000)
            file=open(xmlFilename,'w')
            file.write(s)
            file.close()
            if printXML:
                print s
                print "**********************************"
                print "  XML file saved as " + xmlFilename
                print "**********************************"





def Save_NormalModes(pdbFileName, outFileName, num=None, model='calpha' ):
    """
    This function calculates normal modes for protein (pdbFileName) and
    saves the top (num) modes into file (outFileName)
    if num is None, save all modes

    """
    # This example shows how to calculate approximate low-frequency
    # modes for big proteins. For a description of the techniques,
    # see
    #      K. Hinsen
    #      Analysis of domain motions by approximate normal mode calculations
    #      Proteins 33, 417 (1998)
    #

    from MMTK import InfiniteUniverse
    from MMTK.Proteins import Protein
    from MMTK.ForceFields import DeformationForceField
    from MMTK.FourierBasis import FourierBasis, estimateCutoff
    from MMTK.NormalModes import NormalModes, SubspaceNormalModes
    from MMTK.Visualization import view

    # Construct system
    universe = InfiniteUniverse(DeformationForceField())
    universe.protein = Protein(
        pdbFileName, model=model        
        #'/export/people/yongzhao/dev/FlexTree/Tests/Data/1HIV.pdb',
        #model='calpha'
        )

    # Find a reasonable basis set size and cutoff
    nbasis = max(10, universe.numberOfAtoms()/5)
    cutoff, nbasis = estimateCutoff(universe, nbasis)
    print "Calculating %d low-frequency modes." % nbasis

    if cutoff is None:
        # Do full normal mode calculation
        modes = NormalModes(universe)
    else:
        # Do subspace mode calculation with Fourier basis
        subspace = FourierBasis(universe, cutoff)
        modes = SubspaceNormalModes(universe, subspace)

    # Show animation of the first non-trivial mode
    #view(modes[6], 15.)

    def writeMode(modes, fileName="normalModes"):
        file=open(fileName, 'w')
        for mode in modes:
            vectors=mode.array
            for v in vectors:
                file.write(str(v)[1:-1])
                file.write('\n')        
        file.close()

    ###    
    writeMode(modes[6:6+num], fileName=outFileName)
    return modes.getEigenValues()[6:6+num]


def consolidateLogs(fileNames, outputFileName='All_logs'):
    """ This function consolidate all the docking logs files that matches
    'fileNames' and consolidate the results into single file.
    """
    import sys, glob, os
    msg=''
    files=glob.glob(fileNames)
    if len(files) ==0:
        msg= "No file matches :", fileNames
        return msg
    allGenes=[]
    commonSetting={}

    for file in files:
        bestGenes,settings=findBestGenes(file)
        if bestGenes is None and settings is None:
            print file, "is not a docking log file"
            continue

        if len(allGenes)==0 and len(commonSetting)==0:  # initialize
            if settings.has_key('ReceptorXML') and \
               settings.has_key('LigandXML'):
                allGenes=bestGenes
                commonSetting = settings
            else:
                msg += 'XML information missing in %s. Ignored.\n' %(file,)
            continue


        if not settings.has_key('ReceptorXML') or \
           not settings.has_key('LigandXML') or  \
           commonSetting['ReceptorXML']!=settings['ReceptorXML'] or \
           commonSetting['LigandXML']!=settings['LigandXML']:
            msg+= 'XML information missing or not consistent in %s. Ignored.' %(file,)
            continue

        # more than one docking in a log file

        allGenes.extend(bestGenes)                    

    outFile=open(outputFileName, 'wb')
    outFile.write("# consolicated docking results \n")
    keys=commonSetting.keys()
    keys.sort()
    for k in keys:
        outFile.write("# %s = %s \n"%(k, commonSetting[k]) )

    for geneList in allGenes:
        outFile.write("%s \n"%(geneList) )

    outFile.close()
    return msg



def getClosestRotamer(flexResidueSet):
    """ this function get input of a residue set. For each residue, the rotamer
library will be loaded and the most similar rotamer will be located and set to
be the conformation of the residue

output: The same residue set with rotamer conformation

"""
    if not isinstance(flexResidueSet, ResidueSet):
        return

    newResSet=flexResidueSet[:]
    from FlexTree.RotLib import RotLib
    from FlexTree.FTMotions import defineLocalCoordSys
    from mglutil.math.rmsd import RMSDCalculator   
    bestRotamerConf=[]
    for i in range(len(flexResidueSet[:])):
        residueName = newResSet[i].name
        residueName=residueName[:3]
        if residueName not in RotLib.keys():
            print
            print residueName, "not found in rotamer library\n"
            return None

        allAtm=newResSet[i].atoms
        anchorAtoms=allAtm.get('CB,CA,C')
        anchors= anchorAtoms.coords
        CB=N.array(anchors[0],'f')
        CA=N.array(anchors[1],'f')
        C =N.array(anchors[2],'f')            
        mat=defineLocalCoordSys(CB, CA, C)
        transform = Numeric.identity(4, 'f')
        transform[:3,:3] = mat
        transform[:3,3] = anchorAtoms[1].coords #C-Alpha
        transform=N.transpose(transform)

        sidechainAts=allAtm.get('sidechain')        
        RMSD = RMSDCalculator(refCoords =sidechainAts.coords)
        lib=RotLib[residueName]
        data={}
        for j in range(len(lib)):
            conf=lib[j]
            coords=[]
            for a in sidechainAts:
                coords.append(conf[a.name])

            hcoords = N.concatenate((coords,N.ones( (len(coords), 1), 'd')), 1)
            mob=N.matrixmultiply(hcoords,transform).astype('f')
            mob=mob[:,:3]
            rmsd=RMSD.computeRMSD(mob)
            data[rmsd]=mob.tolist()

        bestRotamerConf.extend(data[min( data.keys() )] )

    return bestRotamerConf



def computeConstraint(fileName, allAtoms, ignoreList=[]):
    file = open(fileName)
    lines=file.readlines()
    data=[]
    dataLines=[]
    ignoreFlag=True
    start=True
    currentSection=""
    for line in lines:
        if line.find('#') ==0:
            currentSection=line[:-1]
            if line[:-1] not in ignoreList:
                start=True
                #print line
                continue
            else:
                start=False
                continue
        elif start:
            dataLines.append(line)
            
    for line in dataLines:
        tmp=line.split()
        weight=1/(float(tmp[2]) - float(tmp[3]))
        data.append([int(tmp[0]), int(tmp[1]), weight])

    for a in allAtoms: a.constraint=0.0

    for d in data:
        allAtoms[ d[0] - 1].constraint += d[2]
        allAtoms[ d[1] - 1].constraint += d[2]
    return

def getRMSD(setting, GA, ligandCoords, origAtomSet=None):
    """ return a list of RMSDs.reference structures \ 
    are starting PDB conformation and those specifed in \
    the 'setting' dictionary"""
    from MolKit import Read
    from mglutil.math.rmsd import RMSDCalculator

    rmsdList = []
    refConformations = []
    keys = setting.keys()
    refConformations = refs = setting['rmsdRef']

    # Append the rmsdRef structures from settings file to refConformations
    #if refs!= None and refs != orig:
    #    if type(refs)==types.ListType:
    #        refConformations.extend(refs)
    #if orig:
    #    # Dont need to duplicate files in the list
    #    if orig in refConformations:
    #        pass
    #    else:
    #        refConformations.append(orig)
#	# get the set of atoms in the ligand
#	# will be used to assert that reference molecule atoms are in the same order
#	origAtomSet = (Read(orig)[0]).allAtoms
#	origAtomSet.sort()

    # used the reference conformation in setting file.
    # NOTE: more than one reference structure might be specified.
    for coords in ligandCoords:
        bestRMSD=None
        for ref in refConformations:
            if not os.path.exists(ref):
                continue
            refMol=Read(ref)[0]
            ligAts=refMol.getAtoms()

            # Make sure the ligAts match the order of the reference
	    sortedLigAts = orderRefMolAtoms(ligAts, origAtomSet)
	    if sortedLigAts:
		ligAts = sortedLigAts
                
                # Instance of RMSDCalculator
	        ##calc = RMSDCalculator(refCoords=ligAts.coords)
                # Calculate RMSD between the docked ligand and the ref. structure
		##rmsd = calc.computeRMSD(coords)
                for RMSDcalc in GA.rmsdCalculators:
                    rmsd = RMSDcalc.computeRMSD(coords)

		print ref, " ---> rmsd=", rmsd
		if bestRMSD is None:
		   bestRMSD=rmsd
		elif rmsd < bestRMSD:
		   bestRMSD=rmsd
		else: pass
	    else:
	        print "WARNING: reference molecule %s can not be ordered to match \
                and the reported RMSD value is wrong"% ref
        rmsdList.append(bestRMSD)                
    return rmsdList



def getBestRMSD(setting, ligandCoords):
    """ this function has same input and provides same output as getRMSD()
In addition, the function assumes the reference structure is a pdbq file with
EXACTLY the same torTree as in the ligand pdbq file. The rotatable single bonds
are rotated by 120,180,240 degrees and check if any chemically equavilent
structure can be found. (ring flipping: 180 degrees, CH3 like rotation: 120,240
degrees)

NOTE: If the ligand are not C1 symmetry, the symmetrical structures must be
      specified as alternative reference conformations.
"""
    rmsdList=[]
    refConformations=[]
    from mglutil.math.rmsd import RMSDCalculator
    keys= setting.keys()
    for k in keys:
        if k.find('reference_conformation')!=-1:
            refConformations.append(k)

    from MolKit import Read
    # Use alternative structures?
    use_alternative_structures=False
    refMols=[]
    for ref in refConformations:
        rm=Read(setting[ref])[0]
        if rm.parser.__class__.__name__ == "PdbqParser":
            use_alternative_structures=True
            refMols.append(rm)

    if not use_alternative_structures:
        return getRMSD(setting, ligandCoords)


    for ref in refMols:
        flextree=torTree2FlexTree(ref.torTree, ref.allAtoms)
        atoms=ref.allAtoms[:]
        atoms.sort()
        coords = flextree.getCurrentSortedConformation2()
        atoms.updateCoords(coords, 0)

        
    for coords in ligandCoords:
        bestRMSD=9999
        for ref in refConformations:
            refMol=Read(setting[ref])[0]
            ligAts=refMol.getAtoms()
            calc = RMSDCalculator(refCoords=ligAts.coords)
            rmsd = calc.computeRMSD(coords)
            #print setting[ref], " ---> rmsd=", rmsd
            if rmsd < bestRMSD:
                bestRMSD=rmsd
        rmsdList.append(bestRMSD)                




def torTree2FlexTree(torTree, allAtoms):
    """ convert a torTree into a FlexTree data structure"""
    if not torTree.rootNode: return None
    mol=allAtoms.top.uniq()[0]
    tree = FlexTree(name=mol.name)
    tree.pdbfilename=mol.parser.filename
    ftRoot=FTNode()
    tree.root = ftRoot
    ftRoot._tree = tree
    ftRoot.tree = weakref.ref(ftRoot._tree)
    tree.createUniqNumber(ftRoot)
    molFrag=mol
    ftRoot.configure(name='root', motion=None, molFrag=molFrag)

    coreFTNode=FTNode()
    coreFTNode.tree = weakref.ref(ftRoot._tree)
    #tree.createUniqNumber(ftRoot) ??
    core=allAtoms.get(lambda x: x.number-1 in torTree.rootNode.atomList)
    coreFTNode.configure(name='root', motion=None, molFrag=core)

    ftRoot.children.append(coreFTNode)
    index=0
    next_index = index + 1
    for c in torTree.rootNode.children:
        node, next_index = __torTree2FlexTree(torTree, c, next_index, \
                                              index, allAtoms)
        ftRoot.children.append(node)
    return tree

   

def __torTree2FlexTree(torTree, node, next_index, refNode, allAtoms):
    ftn=FTNode()
    this_nodes_index = next_index
    next_index += 1
    at1 = allAtoms.get(lambda x: x.number-1==node.bond[0])[0]
    at2 = allAtoms.get(lambda x: x.number-1==node.bond[1])[0]
    atmList = node.atomList[:]
    if len(atmList)<1:
        raise
    from FTGA import GAFTMotion_RotationAboutAxis
    motion = GAFTMotion_RotationAboutAxis()
    motion.configure(points=[at1.coords, at2.coords])
    molFrag=allAtoms.get(lambda x: x.number-1 in atmList)
    ftn.configure(motion=motion, molFrag=molFrag)

    for c in node.children:
        childNode, next_index =  __torTree2FlexTree(torTree, c, next_index, this_nodes_index, allAtoms)
        ftn.children.append(childNode)
    return ftn, next_index


from FlexTree.FTMotions import dist
def isAlternative(frag1, frag2):
    size=len(frag1)
    data=N.zeros((size,size),'f')    
    for i in range(size):
        at1=frag1[i]
        for j in range(size):
            at2=frag2[j]
            dd=dist(at1.coords, at2.coords)
            #raise
            if dd < 1.0 and at1.element==at2.element:
                data[i][j] += dd
                print at1.name, at2.name
                
    if abs(N.sum(data) - size*size) < 1e-4:
        return True
    else:
        return False


## def foo(tree):
##     for m in tree.getAllMotion():
##         if m.__class__.__name__ !='FTMotion_RotationAboutAxis':
##             continue
##         node=m.node()
##         orig=[]
##         for at in node.molecularFragment:
##             tmp=Atom()
##             tmp.element=at.element
##             tmp.name=at.name
##             tmp._coords=at._coords[:]
##             orig.append(tmp)            
##         orig=AtomSet(orig)
##         tmpAtoms=node.molecularFragment
##         for angle in [120, 180, 240]:
##             node.configure(motionParams={'angle':angle})
##             tmpAtoms.updateCoords(node.currentConf, 1)
##             if isAlternative(orig, tmpAtoms):
##                 print angle
##             else:
##                 print "..", 


def replace(filename, origStr, newStr, newFileName=None):
    if newFileName is not None:
        outputFileName=newFileName
    else:
        outputFileName=filename
    lines=open(filename).readlines()
    outF=open(outputFileName,'w')
    for line in lines:
        line = line.replace(origStr, newStr)
        outF.write(line)
    outF.close()

class rigidReceptor2XML:

    def __init__(self, mol):
     	from FlexTree.FT import FlexTree
     	self.tree = FlexTree(mol=mol)
        self.tree.updateStatus()
        rigidAtoms = self.tree.getRigidAtoms()

    def writeXML(self, filename):
        self.tree.save(filename)

    def getTree(self):
        return self.tree


#def rigidReceptor2XML(mol):
#    """ private function.."""
#
#    # create new FlexTree
#    tree = FlexTree(name=mol.name, mol=mol)
#    # create some attributes such as rigidNodeList
#    tree.updateStatus()
#    return tree

    # create new FTNode
    #ftNode = FTNode()
    # 
    #lines1=['<?xml version="1.0" ?>',
    #        '   <root',
    #        '     name="Root" ',
    #        '     id="0"',
    #        '     convolve="FTConvolveApplyMatrix"']
    #lines2= '     selectionString="%s"'
    #lines3= '     file="%s">'
    #lines4= '   </root>' 
    #outXML=open(filename, 'w')
    #for line in lines1:
    #    outXML.write(line + '\n')
    #outXML.write(lines2%(mol.name) + '\n')
    #outXML.write(lines3%mol.parser.filename + '\n')
    #outXML.write(lines4 + '\n')
    #outXML.close()
    #return
    


def saveAutoDockFRPrediction(vars, settings, scoreObject,
                             R_tree=None, L_tree=None,
                             recName="receptor.pdb", ligName="ligand.pdb"):
    """ vars is the optimized variables, settings is a dict"""
    
    if R_tree and recName:
        R_tree.saveCoords(recName)
    if L_tree and ligName:
        L_tree.saveCoords(ligName)


def rmsdScoreFromLog(log):
    data=open(log).readlines()
    RMSDs=[]
    Scores=[]
    for line in data[10:]:
        if line.find("INFO: best_RMSD") != -1:
            rmsd=line.split('=')[1]
            RMSDs.append( eval(rmsd) )
        elif line.find("INFO: best_score") != -1:
            score=line.split('=')[1]
            Scores.append( eval(score) )
            
    return RMSDs, Scores

##  EOF
