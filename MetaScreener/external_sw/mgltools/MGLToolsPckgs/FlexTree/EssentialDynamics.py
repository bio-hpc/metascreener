## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

######################################################################
#
# Date: Jan 2004 Author: Yong Zhao
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

import string, types
from math import sqrt
import numpy.oldnumeric as Numeric
N=Numeric
from MolKit import Read
from MolKit.molecule import MoleculeSet, AtomSet

import glob

class EssentialDynamics:
    """ """
    def __init__(self):
        self.vectors=[]
        self.amplitudes=[]
        self.pdbFile=None
        self.mol = AtomSet([])
        self.coords=[]
        self.atomsInResidue=None
        self.scale=1.0
        self.movingAtoms=AtomSet([])

    def load(self, filename):        
        ok = self._parseEssentialDynamicsFile(filename)
        if ok:
            self._flattenCoords()
        return ok
        
    def compute(self, originalPDB, pdbFiles=None, filter='backbone'):
        """ compute essential dynamics from files in pdfFiles,
filter one of ['CA', 'backbone', 'all']
            or  'CA+selection string'], e.g. CA+W:WTR:O
            NOTE that selection are in 'chain:residue:atom' format
pdbFiles: string such as '../Research/concoord/test/test*.pdb'
          These files are generated from ConCOORD, Using originalPDB as input
originalPDB: file name for starting structure.        
        """
        self.mol=Read(originalPDB)[0]
        data=self.__getDataFrom(files=pdbFiles, filter=filter)
        data=N.array(data)

        from numpy.oldnumeric.linear_algebra import eigenvectors
        from numpy.oldnumeric import mlab as MLab
        covMatrix=MLab.cov(data)
        egvalues, egvectors = eigenvectors(covMatrix)
        self.vectors=egvectors
        self.amplitudes=N.sqrt(egvalues)  # sqrt(eigen value) is amplitide
        self.pdbFile=originalPDB
        self.filter=filter
        self._flattenCoords()
        return


    def __getDataFrom(self, files, filter):
        data=[]
        counter=0
        files=glob.glob(files)
        files.sort()
        assert len(files) > 3 
        for f in files:
            m=Read(f)
            counter +=1
            coords=m[0].allAtoms.get('CA').coords
            #coords=N.reshape(N.array(coords), (len(coords)*3,))
            coords=N.reshape(N.array(coords), (-1,))
            data.append(coords.tolist())
            del m
            if counter > len(coords):
                print "Need %d files, found %d " %(len(coords), len(files) )
                print "more than enough pdb files found.. stop."
                break
        return data



##     def __getDataFrom(self, files, filter):
##         data=[]
##         counter=0
##         files=glob.glob(files)
##         assert len(files) > 3 
##         for f in files:
##             m=Read(f)
##             counter +=1
##             if filter=='backbone':
##                 coords=m[0].getAtoms().NodesFrget('backbone').coords
##             elif filter=='all':
##                 coords=m[0].getAtoms().coords
##             elif filter=='CA':
##                 coords=m[0].getAtoms().get('CA').coords
##             else: # if filter is 'CA+selection_string'
##                 tmp=filter.split('+')
##                 if len(tmp)==2 and tmp[0]=='CA':
##                     atms=m[0].getAtoms()
##                     coords=atms.get('CA').coords
##                     resSet=atms.parent.uniq()
##                     from MolKit.stringSelector import StringSelector
##                     stringSel = StringSelector()
##                     atoms, msg=stringSel.select(m, m[0].name+":"+tmp[1])
##                     assert len(atoms) ==1              
##                     coords.extend(atoms.coords)
##                 else:
##                     name=m[0].name
##                     atms=m[0].allAtoms.NodesFromName(name+filter)
##                     if len(atms):
##                         coords=atms.coords
##                     else:
##                         raise
##                         print "Unknown filter", filter
##                         return

##             coords=N.reshape(N.array(coords), (len(coords)*3,))
##             data.append(coords.tolist())
##             del m
##             if counter > len(coords):
##                 print "Need %d files, found %d " %(len(coords), len(files) )
##                 print "more than enough pdb files found.. stop."
##                 break
##         return data


    def write(self,outputFilename):
        """Write Essential Dynamics into file """
        file=open(outputFilename, 'w')
        file.write(self.pdbFile+'\n')
        file.write(self.filter+'\n')
        num=len(self.vectors)
        assert num==len(self.amplitudes)
        egvalues=self.amplitudes
        egvectors=self.vectors
        for i in range(num):
            e=egvalues[i]
            if types.ComplexType==type(e):
                e=e.real
            v=egvectors[i].tolist()
            if types.ComplexType==type(v[0]):
                for i in range(len(v)):
                    v[i]=v[i].real

            file.write('%f, %s'%(e, str(v)))
            file.write('\n')        
        file.close()


    def chooseModes(self, modeNum):
        """ only used the first n modes of the available data .
n=modeNum
        """
        num=len(self.vectors)
        if num==0 or num < modeNum:
            return
        else:
            self.vectors=self.vectors[:modeNum]
            self.amplitudes=self.amplitudes[:modeNum]
            
        
    def _parseEssentialDynamicsFile(self, filename):
        """
    format of input file:
    first line: PDB file name
    second line: filter
    all other lines: eigen value, eigen vector
        """
        try:
            data=file(filename, 'r').readlines()            
            pdbFile=data[0].split()[0]
            filter=data[1].split('\n')[0]
            egValues=[]
            egVectors=[]
            for line in data[2:]: 
                tmp=line.split(',')
                egValues.append(eval(tmp[0]))
                vector=string.join(tmp[1:],',')
                egVectors.append(eval(vector))

            self.vectors=N.array(egVectors,'f')
            self.amplitudes=N.array(egValues,'f')
            self.pdbFile=pdbFile
            try:
                self.mol = Read(pdbFile)[0]
                atoms=self.mol.allAtoms
                atoms.addConformation(atoms.coords)
            except:
                print "file %s in essential dynamics file not found"%pdbFile
                raise ValueError

            self.filter=filter
            #self.atoms=self.mol.NodesFromName(self.mol.name+filter)
            self.atoms=self.mol.NodesFromName(filter)
            if len(self.atoms)==0:
                self.movingAtoms=self.mol.allAtoms
            else:
                self.movingAtoms=self.atoms.parent.atoms

            assert len(self.movingAtoms)!=0
            assert len(self.vectors)!=0
            return True
        except:
            return False

    def _flattenCoords(self):
        if not self.mol:
            return
        coords=self.mol.allAtoms.coords
        length=len(coords)
        coords=N.array(coords, 'f')
        self.coords=N.reshape(coords, (length*3, ) )


    def getCoords(self, indexes, weights, scale=None, allAtoms=True):
        """ weight: [-1.0, 1,0]
scale: if None, use the default self.scale, otherwise use the user value
allAtoms True: return coords of all atoms
allAtoms False: return filter atoms only. If CA or CA+XXX is specified, return all the backbone atom coords. (Useful for visualization in Pmv)
        """
        if not scale:
            scale=self.scale
        
        index=indexes
        weight=weights # fixme.. should pass a list
        #amplitude=self.amplitudes[index] * weight
        amplitude=sqrt(self.amplitudes[index]) * weight
        vector= N.array(self.vectors[index],'f') * amplitude*scale

        if self.filter=='CA':
            if allAtoms:
                newCoords=self._allCoordsByResidue(vector)
                newCoords=N.reshape(newCoords, (len(self.coords)/3, 3) )
                return newCoords
            else:
                newCoords=self._backboneByResidue(vector)
                return newCoords

        tmp=self.filter.split('+')
        # filter is "CA+W:WTR301:O"  
        if len(tmp)==2 and tmp[0]=='CA':
            ## hack here.. the W:WTR301:O has to be at the end of all CAs
            if allAtoms:
                newCoords=self._allCoordsByResidue(vector)
            else:
                newCoords=self._backboneByResidue(vector)
            newCoords=N.reshape(newCoords, (len(self.coords)/3, 3) )
            return newCoords
        elif self.filter=='backbone':
            print "Not implemented" # fixme.
            return 
        elif self.filter=='all':        
            newCoords=[]
            coords=self.coords
            newCoords = coords + vector
            newCoords=N.reshape(newCoords, (len(coords)/3, 3) )
            return newCoords
        elif self.filter.split(':')[-1]=='CA': 
            newCoords=self._allCoordsByResidue(vector)
            return newCoords
        elif self.filter.split(':')[-1]=='backbone': 
            newCoords=self._allCoordsByResidue(vector)
            return newCoords        
        else:
            print "Unknown filter:", self.filter
            raise

    def _backboneByResidue(self, vector):
        """ One vector applied to every CA,only return backbone atoms"""

        if len(self.atoms)==0:
            atoms=self.mol.allAtoms
        else:
            atoms=self.atoms.parent.atoms

        ## conformation 1 is the trasnformed coords
        ## keep the original coords in conformation 0
        currentConf = atoms[0].conformation
        if currentConf!=0:
            atoms.setConformation(0)

        atomsInRes=[]
        if self.filter.split(':')[-1]=='CA' and self.atomsInResidue is None:
            resSet=atoms.parent.uniq()            
            if self.atomsInResidue is None:                
                for r in resSet:
                    ats = r.atoms.get('backbone') \
                          & atoms # make sure in the molecularFragment
                    atomsInRes.append(ats)

            self.atomsInResidue=atomsInRes
            
##         else:
##             tmp=self.filter.split('+')
##             self.atomsInResidue=atoms.get('backbone')
##             ## fixme !!!! W:WTR301:O
##             self.atomsInResidue.append([])
            
        vectorList=N.reshape(vector, (len(vector)/3, 3))
        data=map(None, vectorList, self.atomsInResidue)
        origCoords=[]
        for v, ats in data:                        
            tmp=[]
            for at in ats:
                try:
                    tmp.append( (N.array(at.coords) + v).tolist() )
                except ValueError:
                    print N.array(v,'f').shape, N.array(at.coords).shape
            origCoords.extend(tmp)

        if currentConf!=0:
            atoms.setConformation(currentConf)
        atoms.updateCoords(origCoords, 1) 
        return origCoords

    def _allCoordsByResidue(self, vector):
        """ One vector applied to one residue (CA)."""        
        if len(self.atoms)==0:
            atoms=self.mol.allAtoms
        else:
            atoms=self.atoms.parent.atoms

        if len(atoms[0]._coords)==1:
            atoms.addConformation(atoms.coords)
        currentConf = atoms[0].conformation

        if currentConf!=0:
            atoms.setConformation(0)
            
        resSet=atoms.parent.uniq()
        origCoords=[]        
        if self.atomsInResidue is None:
            atomsInRes=[]
            for r in resSet:
                ats = r.atoms & atoms # make sure in the molecularFragment
                atomsInRes.append(ats)
            self.atomsInResidue=atomsInRes

        vectorList=N.reshape(vector, (len(vector)/3, 3))
        data=map(None, vectorList, self.atomsInResidue)
        for v, ats in data:                        
            tmp=[]
            for at in ats:
                try:
                    tmp.append( (N.array(at.coords) + v).tolist() )
                except ValueError:
                    print N.array(v,'f').shape, N.array(at.coords).shape
            origCoords.extend(tmp)

        atoms.updateCoords(origCoords, 1)
        return origCoords


    def getFilteredCoords(self, indexes, weights):
        """ weight: [-1.0, 1,0] """
        index=indexes
        weight=weights # fixme.. should pass a list

        #sqrt(eigenValue) =  amplitude
        amplitude=sqrt(self.amplitudes[index] ) * weight
        vector= N.array(self.vectors[index],'f') * amplitude

        all=self.mol.getAtoms()
        if self.filter=='CA':
            coords=all.get('CA').coords
        elif self.filter=='backbone':
            coords=all.get('backbone').coords
        elif self.filter=='all':
            coords=all.coords

        coords=N.reshape(coords, (len(vector), ) )            
        newCoords = coords + vector
        newCoords=N.reshape(newCoords, (len(vector)/3,3 ) )        
        return newCoords


    def writeXML(self, modeNum, xmlFileName, filter='CA'):
        """ write an XML, the only motion is normal mode motion, applied to the root of the pdb file
    """
        ####
        print "Use Pmv -->FlexTreeCommands to do this." # fixme
        return 
        
        lines1=['<?xml version="1.0" ?>',
        ' <root',
        '  name="node" ',
        '  id="0"']
        lines2='  discreteMotionParams="weightList: list float %s, name: str combined_Normal_Modes, vectorNum: int %d, modeNum: int %d, modeVectorFile: str %s, amplitudeList: list float %s'
        lines3=' selectionString="%s"'
        lines4=[' discreteMotion="FTMotion_NormalMode"',
        ' convolve="FTConvolveApplyMatrix"']
        lines5=' file="%s">'
        lines6= ' </root>' 

        from FlexTree.XMLParser import ReadXML
        reader = ReadXML()

        mol=self.mol.name

        all=self.mol.getAtoms()
        vectorPerMode=0
        if filter=='CA':
            vectorPerMode = len(all.get('CA') )
        elif filter=='backbone':
            vectorPerMode = len(all.get('backbone') )
        elif filter=='all':
            vectorPerMode = len(all)

        #amplitudes = Save_NormalModes(self.pdbFile, '%s.Modes'%mol, modeNum)

        xx=file('kkk.abc', 'w')
        for vec in self.vectors[:modeNum]:
            vec=N.reshape(vec, (vectorPerMode, 3))
            for v in vec:
                xx.write("%s %s %s\n"%(v[0], v[1], v[2]))
        xx.close()           

        
        amplitudes=self.amplitudes.tolist()[:modeNum]
        tmp=amplitudes.__repr__()
        tmp= tmp[1:-1].split(',')
        tmp=''.join(tmp)
        outXML=file(xmlFileName, 'w')
        for line in lines1:
            outXML.write(line + '\n')

        jj = '0 '*modeNum
        outXML.write(lines2%(jj,         
                             vectorPerMode,     #     
                             modeNum,    
                             'kkk.abc',  
                             tmp)
                              + ' " \n')
        outXML.write(lines3%mol + '\n')
        for line in lines4:
            outXML.write(line + '\n')
        outXML.write(lines5%self.pdbFile + '\n')
        outXML.write(lines6 + '\n')
        outXML.close()

        reader(xmlFileName)
        tree=reader.get()[0]
        root=tree.root
        tree.adoptRandomConformation()
        root.updateCurrentConformation()
        print '------------ done with ' , mol



"""
# testers

from FlexTree.EssentialDynamics import EssentialDynamics
ed=EssentialDynamics()
ed.compute('1crn_top3.pdb', "../Research/concoord/test/test*.pdb", 'CA')
ed.write('fff')


###################
from math import sqrt
for i  in range(len(ed.vectors)):   
   a=max(ed.vectors[i])
   b=abs(min(ed.vectors[i]))
   x=max(a,b)
   print "max offset of %d is %f"%( i,  sqrt(ed.amplitudes[i])*x)

"""
