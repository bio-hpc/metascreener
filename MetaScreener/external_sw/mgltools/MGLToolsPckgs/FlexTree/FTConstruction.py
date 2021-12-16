########################################################################
#
# Date: Jan 2006 Authors:  Yong Zhao
#
#   yongzhao@scripps.edu
#       
#   The Scripps Research Institute (TSRI)
#   Molecular Graphics Lab
#   La Jolla, CA 92037, USA
#
# Copyright: Yong Zhao and TSRI
#
#########################################################################

verbose=1

from MolKit import Read
#from FlexTree.FlexLoop import FlexLoop
from MolKit.molecule import Atom, AtomSet, Bond, Molecule, MoleculeSet
from FlexTree.FTMotions import FTMotion_EssentialDynamics, FTMotion_Rotamer

class FTParam:
    """ parameters for building a flexible protein"""
    def __init__(self):
        self.kw=kw={}
        kw['receptor']=None
        kw['outputXML']=None
        kw['loop']=None
        kw['loopModes']=None
        kw['movingSidechains']=None
        kw['contactCutOff']=None
        kw['usePolorAtomsOnly']=True
        kw['allHydrogenAdded']=False
##         kw['convertToPDBQS']=False # shoudl probably disappear
##                                    # along with using it in GenerateFT
        kw['ED_file']=None
        kw['samplingOffset']=None
        kw['maxFailure']=None

        return
    
        
    def load(self, filename):
        try:
            data=open(filename).readlines()
        except:
            print "Error opening:", filename
            raise
        dict={}
        keys=self.kw.keys()
        for line in data:
            if line[0]=='#':
                continue
            result= line.split('=')
            if len(result)!=2:
                continue
            else:
                k,v=result
                if k in keys:
                    self.kw[k]=eval(v)
        return
    
    def show(self):
        for k in self.kw.keys():
            print k, '=', self.kw[k]
        return



class GenerateFT:
    """ automatically generate a FT based on the user parameter """

    def __init__(self, param, mol=None):
        self.param=param
        kw=self.param.kw
        if mol:
            self.mol = mol
        else:
            try:
                self.mol=Read(kw['receptor'])[0]
                self.mol.buildBondsByDistance()
            except e:
                print "Error in opening file:", kw['receptor'], e
                raise IOError

        self.flexLoop=None
        discreteMotion=None
        
        if kw['loop']!=None:
#            self.flexLoop=loop=FlexLoop(kw['receptor'] , kw['loop'], \
#                                        HsAdded=kw['allHydrogenAdded'])
            self.flexLoop=loop=FlexLoop(self.mol , kw['loop'], \
                                        HsAdded=kw['allHydrogenAdded'],\
                                        contactCutOff=kw['contactCutOff'],\
                                        offset=kw['samplingOffset'])
            loopSize=len(loop.residues)
            if verbose:
                print "The following %d residues will be flexible:"\
                      %(loopSize)
                for res in loop.residues:
                    print res.full_name()
            size= 3*loopSize
            #size=12
            ok=self.flexLoop.sampling(size, \
                                      offset=kw['samplingOffset'], \
                                      maxFailure=kw['maxFailure'], \
                                      #start=0, \
                                      )
            #ok=False
            #ok = True
            if not ok:
                print "loop sampling failure.."
                return
            from FlexTree.EssentialDynamics import EssentialDynamics
            ed=EssentialDynamics()
            if verbose:
                print "Start computing ED."
            filter=self.param.kw['loop']

            ed.compute(kw['receptor'], "linker_*.pdb", filter+':CA')
            filename=kw['ED_file']
            ed.write(filename)
            if verbose:
                print "Computing ED finised"

            discreteMotion=FTMotion_EssentialDynamics(edFile=filename,\
                                 modeNum=kw['loopModes'])

##         if kw['convertToPDBQS']:
##             from AutoDockTools.MoleculePreparation import ReceptorPreparation
##             RPO = ReceptorPreparation(self.mol, \
##                                       cleanup ="nphs_lps_waters")
##             outF=self.mol.name+".pdbqs"
##             RPO.write(outF)
##             self.mol=Read(outF)[0]
            
        ## initialize a FT here.
        from FlexTree.FT import FlexTree
        self.tree=FlexTree(mol=self.mol)
        if kw['loop']:
            self.tree.root.splitNode(kw['loop'], \
                                     discreteMotion=discreteMotion,\
                                     name=kw['loop'])

        from MolKit.stringSelector import CompoundStringSelector
        css = CompoundStringSelector()
        tmp = MoleculeSet()
        tmp.append(self.mol)
##         result = css.select(tmp, kw['loop'])[0]  
##         self.loop=result

        ## select moving sidechains
        result = css.select(tmp, kw['movingSidechains'])[0]                
        if isinstance(result, AtomSet):
            # make sure it's a ResidueSet
            assert len(result)==len(result.parent.uniq().atoms)
            result=result.parent.uniq()            
            
        self.sidechains=result
        print len(result), "sidechains to be flexible"

        for res in self.sidechains:
            print "adding rotamer", res.name
            if res.name[:3] in ['ALA','GLY']:
                print '\tNo rotamer defined for' , res.name
                continue
            
            resAtoms=res.atoms
            sidechain=resAtoms.get('sidechain')-resAtoms.get('CB')
            
            anchor=[]
            for name in ['CB','CA','C']:
                anchor.append(resAtoms.get(name)[0])
            anchor=AtomSet(anchor)
            motion=FTMotion_Rotamer()
            motion.configure(sideChainAtomNames=sidechain.name, \
                             residueName=res.name)
            self.tree.root.splitNode(sidechain.full_name(), \
                                     discreteMotion=motion, \
                                     anchorAtoms=anchor,
                                     name=res.full_name())

        self.tree.updateStatus()
        rigidAtoms=self.tree.getRigidAtoms()
        motions=self.tree.getAllMotion()
        for m in motions:
            if isinstance(m, FTMotion_Rotamer):
                m._buildConfList()
                m.removeClashWith(rigidAtoms)

        outputFile=kw['outputXML']
        if outputFile:
            self.tree.save(outputFile)
            print "Flexibility Tree written to file: %s"%outputFile

        return


    def getTree(self):
        return self.tree
