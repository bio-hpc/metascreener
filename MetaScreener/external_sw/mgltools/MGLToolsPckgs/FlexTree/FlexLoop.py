########################################################################
#
# Date: Nov 2006 Author: Yong Zhao
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

from FlexTree.FTAmber import FTAmber94
import types, random, Numeric
N=Numeric
from MolKit.protein import Protein, ProteinSet, Chain, Residue, ResidueSet
from MolKit.stringSelector import CompoundStringSelector
from MolKit.molecule import Atom, AtomSet, Bond, Molecule, MoleculeSet

from MolKit.pdbWriter import PdbWriter
writer = PdbWriter()
from MolKit import Read

import sys

debug=1
verbose=1


def rand(offset):
    return (random.random()*2.0-1.0)*offset


class FlexLoop:
    def __init__(self, mol, loopAtoms=None, HsAdded=False, \
                 offset=1.0, contactCutOff=None):
        """ a loop object.
        mol: the molecule
        loopAtoms: the atoms in the loop
        HsAdded: all the hydrogen atoms have already been added (True/False)
        offset: the atoms in the loop can move within this range.

        The randomized loop comformations will be minimized by SFF (amber)
        """
        self.offset=offset
        
        if type(mol) is types.StringType:
            try:
                mol=Read(mol)[0] ## assume Hs are properly added..
                mol.buildBondsByDistance()
                self.mol=mol
            except:
                print 'error in opening', mol
                raise IOError
        else:
            assert isinstance( mol, Protein)
            self.mol=mol
        
        if not HsAdded:
            if verbose:
                print "Adding Hydrogen atoms..."
            from MolKit.hydrogenBuilder import HydrogenBuilder
            h_builder = HydrogenBuilder()#method='withBondOrder')
            h_builder.addHydrogens(mol)
            mol.allAtoms.sort()  ## important !
            if debug:
                from MolKit.pdbWriter import PdbWriter #, PdbqWriter
                writer = PdbWriter()
                filename="foo_Hs.pdb"
                writer.write(filename, mol, \
                             records=['ATOM', 'HETATM', 'CONECT'])
        
        self.atoms=self.mol.allAtoms
        self.amberConf=len(self.atoms[0]._coords)  # conformation number
        self.atoms.addConformation(self.atoms.coords[:])
        
        if loopAtoms !=None:
            if type(loopAtoms) is types.StringType:
                css = CompoundStringSelector()
                tmp=MoleculeSet()
                tmp.append(self.mol)
                result = css.select(tmp, loopAtoms)[0]
                self.loopAtoms=result.findType(Atom)
                
            elif isinstance( loopAtoms, TreeNodeSet):
                self.loopAtoms=loopAtoms.findType(Atom)
            else:
                print "error in movingAtoms"
                return
        else:
            self.loopAtoms=AtomSet()

        self.movingAtoms=self.loopAtoms
        if contactCutOff!=None:
            ## allow the atoms within cutoff to move during minimization
            nbr=self.mol.getNbrAtoms(self.loopAtoms,\
                                     contactCutOff)
            print '!!', nbr.parent.uniq().name
            nbr=nbr.parent.uniq().atoms
            self.movingAtoms=(nbr+self.movingAtoms).uniq()
            names=self.movingAtoms.parent.uniq().name
            print "%d moving residues during sampling :"%len(names),
            print names

        
        self.residues=self.movingAtoms.parent.uniq()
        self.frozenAtoms=self.mol.allAtoms-self.movingAtoms
        self.amber=FTAmber94(mol, self.movingAtoms)
        
        self.counter=0
        self.startNumber=0
        self.maxFailure=10
        return
            

    def randomizeLoopAtoms(self):
        ## randomize the loop atoms
        oldConf=self.loopAtoms[0].conformation
        self.loopAtoms.setConformation(0)
        coords=self.loopAtoms.coords  
        newCoords=coords[:]
        OFFSET=self.offset
        for i in range(len(coords)):
            c=coords[i]
            newCoords[i]=[c[0] + rand(OFFSET),\
                          c[1] + rand(OFFSET),\
                          c[2] + rand(OFFSET)]

        self.loopAtoms.updateCoords(newCoords, self.amberConf)
        #self.movingAtoms.setConformation(oldConf)


    def sampling(self, number=1, start=None, writeToFile=True, offset=None,\
                 maxFailure=None):
        """
        number: number of samplings.
        start:  output prefix
                e.g.  start = 10: the output filename will be molName_10.pdb
                      molName_11.pdb ...etc.
        offset:
        maxFailure: maximum number of failed trials.
        """
        if offset !=None:
            self.offset=offset
        if maxFailure!=None:
            self.maxFailure=maxFailure
        if start:
            self.startNumber=start
        else:
            self.startNumber=0
        self.counter=0
        self.confs=[]
        self.Es=[]
        failed=0
        success=0
        returnValue=True
        while 1:
            res=self.sampleOne(writeToFile=writeToFile)
            if res==False:
                failed+=1
                #if verbose: print "failed =", failed
                #print '.',
                #sys.stdout.flush()
            else:
                success+=1                
                if verbose: print " success =", success
                self.Es.append(res[0])
                self.confs.append(res[1])
            if failed >=maxFailure:
                returnValue=False
                break
            if success>=number:
                returnValue=True
                break
        return returnValue



    def sampleOne(self, writeToFile=True):
        """ one random sampling.."""
        maxFailNum=10
        failed=0
        converged=False
        self.randomizeLoopAtoms()
        amber=self.amber.amber
        tmp=self.atoms.coords
        tmp=N.reshape(N.array(tmp), (-1,) )   
        amber.coords=tmp[:]
        amber.setMinimizeOptions(cut=20)
        while failed < maxFailNum:                                   
            res=amber.minimize(drms=0.01, dfpred=1e10, maxIter=10000)
            E=amber.energies[8] #???
            if res>0:
                converged=True                
                #print "**  converged.. E =", E
                #if verbose:
                print "# %d: iter=%d, E=%f"%(self.counter, res, E)
                sys.stdout.flush()
                break
            else:
                failed +=1
                if verbose:
                    print "failed..", res

        if converged:            
            newcoords = Numeric.array(amber.coords[:])
            newcoords.shape = (-1,3)
            if writeToFile:
                atoms=amber.atoms                
                atoms.updateCoords(newcoords.tolist(), 1)

                outputFileName="linker_%d.pdb"% (self.counter+self.startNumber)
                writer.write(outputFileName, self.loopAtoms, \
                             records=['ATOM', 'HETATM', 'CONECT'],\
                             bondOrigin='all')
                self.counter +=1
            
            return E, newcoords
        else:
            #print 'failed', failed, E
            if debug:
                newcoords = Numeric.array(amber.coords[:])
                newcoords.shape = (-1,3)
                atoms=amber.atoms                
                atoms.updateCoords(newcoords.tolist(), 1)

                outputFileName="failed_%d.pdb"% (self.counter+self.startNumber)
                writer.write(outputFileName, self.mol, \
                             records=['ATOM', 'HETATM', 'CONECT'],\
                             bondOrigin='all')
            return False

