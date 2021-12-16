########################################################################
#
# Date: Jan 2014 Authors: Michel Sanner
#
#   sanner@scripps.edu
#       
#   The Scripps Research Institute (TSRI)
#   Molecular Graphics Lab
#   La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI
#
#########################################################################

#
# $Header: /opt/cvs/FlexTree/rotamer.py,v 1.5 2014/07/31 21:12:52 sanner Exp $
#
# $Id: rotamer.py,v 1.5 2014/07/31 21:12:52 sanner Exp $
#
from numpy import array, dot

from MolKit.molecule import AtomSet
from mglutil.math.rotax import rotax
from mglutil.math.torsion import torsion
from MolKit.rotamerLib import RotamerLib
rotlib = RotamerLib()

from math import pi
degtorad = pi/180.

class Rotamer:
    """
Objet representing a amino acid side chain and allowing to get
coordinates of side chain atoms for rotameric side chain conformations
    """

    def __init__(self, atoms, angleDef, angleList):
        """constructor

        object <- Rotamer(atoms, angleDef)
        
atoms   : amino acid side chain atoms including C-alpha
angleDef: the list of torsion definitions. For each torsion we get
          a list of 4 atoms defining the angle and a list of atoms
          moved only by this angle [ [[a1,a2,a3,a4], [a5,a6,..]], ...]
angleList: list of Chi angles from rotamer library
           NOTE: angleList is not used if we use getCoordsFromAngles
"""       
        assert isinstance(atoms, AtomSet)
        # make sure the number of angular values for each rotamer
        # matches the number of dfined CHI angles
        assert max( [len(x) for x in angleList] ) == len(angleDef)
        assert min( [len(x) for x in angleList] ) == len(angleDef)


        self.angleDef = angleDef # for each angle [a,b,c,d], [e,f,..]]
        self.angleList = angleList # for each rotamer CH1, CH2, CH3 ...
        self.nbChi = len(self.angleDef)
        self.atoms = atoms
        self.originalAngles = []
        
        # compute Chi angles in incomming Residue
        for ang in self.angleDef:
            # get names of atoms forming torsion
            atoms = []
            for atName in ang[0]:
                atoms.append( [x for x in self.atoms if x.name==atName][0] )
            t = torsion(atoms[0].coords, atoms[1].coords,
                        atoms[2].coords, atoms[3].coords)
            self.originalAngles.append(t)

        # build index into self.atoms
        self.rotBondIndices = [] # (i,j) into self.atoms for each CHI
        self.rotatedAtomsIndices = [] # (i,j,..) into self.atoms for moved atoms
        bdAts = []
        for ang in self.angleDef:
            a1, a2, a3, a4 = ang[0]
            atom1 = self.atoms.get(a2)[0]
            atom2 = self.atoms.get(a3)[0]
            self.rotBondIndices.append( (self.atoms.index(atom1),
                                         self.atoms.index(atom2)) )
            movedAtomIndices = []
            for bd in atom2.bonds:
                Atm2 = bd.atom1
                if Atm2 == atom2: Atm2 = bd.atom2
                if Atm2 in self.atoms:
                    if Atm2.element == 'H':
                        movedAtomIndices.append(self.atoms.index(Atm2))

            for atName in ang[1]:
                atom = self.atoms.get(atName)[0]
                movedAtomIndices.append( self.atoms.index(atom) )
                for bd in atom.bonds:
                    Atm1 = bd.atom1
                    if Atm1 == atom: Atm1 = bd.atom2
                    if Atm1 not in self.atoms and Atm1.name =='SG':
                        movedAtomIndices = []
                        break
                    elif (Atm1.parent.name[:3] not in rotlib.residueNames):
                        #print atom, atom.name,Atm1.parent.name
                        movedAtomIndices = []
                        break
                    else:
                        if Atm1 in self.atoms:
                            if Atm1.element == 'H':
                                movedAtomIndices.append( self.atoms.index(Atm1))
               
            # WHAT DOES THIS DO ?
            for atom in self.atoms:
                if atom.name not in ['N','CA','CB'] and atom.name not in ang[0]:
                    if self.atoms.index(atom) not in movedAtomIndices:
                        for bd in atom.bonds:
                            Atm3 = bd.atom1
                            if Atm3 == atom: Atm3 = bd.atom2
                            if (Atm3.parent.name[:3] not in rotlib.residueNames):
                                #print atom, atom.name,Atm3.parent.name
                                movedAtomIndices = []
                                break

##            for atom in self.atoms:
##                if atom.name not in ['N','CA','CB'] and atom.name not in ang[0]:
##                    if self.atoms.index(atom) not in movedAtomIndices:
##                            movedAtomIndices.append(self.atoms.index(atom) )
##
##            for mvatslst in ang[1]:
##                mvats = self.atoms.get(mvatslst)[0]
##                for bd in mvats.bonds:
##                    if bd.atom1.name =="SG" and bd.atom2.name =="SG":
##                        movedAtomIndices = []
            #print movedAtomIndices

###            for bd in atom2.bonds:
###                #print "at2", bd
###                if bd.atom1.name =='SG' and bd.atom2.name =='SG':
###                    movedAtomIndices = []
###                elif (bd.atom1.parent.name[:3] not in rotlib.residueNames) or (bd.atom2.parent.name[:3] not in rotlib.residueNames):
###                    movedAtomIndices = []
###                else:
###                    if bd.atom1.element == 'H': # != atom1:
###                        bdAts.append(bd.atom1)
###                    if bd.atom2.element == 'H': # != atom1:
###                        bdAts.append(bd.atom2)
###            for mvatslst in ang[1]:
###                mvats = self.atoms.get(mvatslst)[0]
###                for bd in mvats.bonds:
###                    #print "mov", bd
###                    #print "parent", bd.atom1.parent.name[:3]
###                    #import pdb
###                    #pdb.set_trace()
###                    if bd.atom1.name =='SG' and bd.atom2.name =='SG':
###                        movedAtomIndices = []
###                    elif (bd.atom1.parent.name[:3] not in rotlib.residueNames) or (bd.atom2.parent.name[:3] not in rotlib.residueNames):
###                        movedAtomIndices = []
###                    else:
###                        if bd.atom1.element == 'H': #!= atom2:
###                            bdAts.append(bd.atom1)
###                        if bd.atom2.element == 'H': # != atom2:
###                            bdAts.append(bd.atom2)
###            if movedAtomIndices:
###                for atom in bdAts:
###                    if atom.parent.name[:3] in rotlib.residueNames:
###                        if self.atoms.index(atom) not in movedAtomIndices:
###                            movedAtomIndices.append(self.atoms.index(atom) )
            #print movedAtomIndices

            self.rotatedAtomsIndices.append( movedAtomIndices )

        # create array of original coordinates
        self.origCoords = [x.coords[:] for x in self.atoms]
        self.horigCoords = [ (x[0],x[1],x[2],1.0) for x in self.atoms.coords]


    ## def zeroTorsion(self):
    ##     # force torsion angles to 0.0
    ##     return
    ##     angInv = [-x for x in self.originalAngles]
    ##     coords0 = self.getCoordsFromAngles(angInv)

    ##     # overwrite coordinates
    ##     self.origCoords = coords0
    ##     for c, x in zip(coords0, self.atoms):
    ##         x.coords = [float(z) for z in c]
    ##     self.horigCoords = [ (x[0],x[1],x[2],1.0) for x in coords0]

    ##     # compute Chi angles after forcing to 0
    ##     for ang in self.angleDef:
    ##         # get names of atoms forming torsion
    ##         atoms = []
    ##         for atName in ang[0]:
    ##             atoms.append( [x for x in self.atoms if x.name==atName][0] )
    ##         t = torsion(atoms[0].coords, atoms[1].coords,
    ##                     atoms[2].coords, atoms[3].coords)
    ##         print ang, t
    ##         assert abs(t)< 0.1, t

    ##     # overwrite angles
    ##     self.originalAngles = [0.0]*len(self.angleDef)

            
##     def getCoords1(self, index, deviations):
##         """
## returns coordinates of side chain atoms for rotamer index with the
## provided deviations

##         coords <- getCoords(index, deviations)
##         """

##         # create array of transformed coordinates (initially orig)
##         coords = copy.deepcopy(self.origCoords)
##         oc = self.origCoords
        
##         # used to propagate tansformation along the chain
##         cmat = identity(4)
        
##         angles = self.angleList[index]
##         #print 'angles:', index, deviations
##         for i in range(self.nbChi):
##             # compute angle
##             angle = angles[i] + deviations[i] - self.originalAngles[i]
##             if angle < 0: angle += 360.
##             elif angle > 360: angle -= 360.
##             #print '    ', angle, angles[i], deviations[i], self.originalAngles[i]
##             a1Ind, a2Ind = self.rotBondIndices[i]
##             # compute xform matrix for Chi x withthis angle
##             mat = rotax(oc[a1Ind], oc[a2Ind], angle*degtorad, transpose=1)
            
##             # add mat to cmat
##             cmat = dot(mat, cmat)
            
##             # transform atoms effected by Chi x
##             for j in self.rotatedAtomsIndices[i]:
##                 x,y,z = oc[j]
##                 coords[j][0] = cmat[0][0]*x + cmat[1][0]*y + cmat[2][0]*z + cmat[3][0]
##                 coords[j][1] = cmat[0][1]*x + cmat[1][1]*y + cmat[2][1]*z + cmat[3][1]
##                 coords[j][2] = cmat[0][2]*x + cmat[1][2]*y + cmat[2][2]*z + cmat[3][2]

##         #print coords[3:]
##         return coords
    
##     def getCoords(self, index, deviations):
##         """
## returns coordinates of side chain atoms for rotamer index with the
## provided deviations

##         coords <- getCoords(index, deviations)
##         """

##         # create array of transformed coordinates (initially orig)
##         coords = array(self.origCoords, 'f')
##         oc = self.origCoords
        
##         # used to propagate tansformation along the chain
##         cmat = identity(4)
        
##         angles = self.angleList[index]
##         #print 'angles:', index, deviations
##         for i in range(self.nbChi):
##             # compute angle
##             angle = angles[i] + deviations[i] - self.originalAngles[i]
##             if angle < 0: angle += 360.
##             elif angle > 360: angle -= 360.
##             #print '    ', angle, angles[i], deviations[i], self.originalAngles[i]
##             a1Ind, a2Ind = self.rotBondIndices[i]
##             # compute xform matrix for Chi x withthis angle
##             mat = rotax(oc[a1Ind], oc[a2Ind], angle*degtorad, transpose=1)

##             # add mat to cmat
##             cmat = dot(mat, cmat)

##             # transform atoms effected by CHIi
##             for j in self.rotatedAtomsIndices[i]:
##                 x,y,z = oc[j]
##                 coords[j][0] = cmat[0][0]*x + cmat[1][0]*y + cmat[2][0]*z + cmat[3][0]
##                 coords[j][1] = cmat[0][1]*x + cmat[1][1]*y + cmat[2][1]*z + cmat[3][1]
##                 coords[j][2] = cmat[0][2]*x + cmat[1][2]*y + cmat[2][2]*z + cmat[3][2]

##         return coords

            
    def getCoordsFromAngles(self, angles, check=True):
        """
returns coordinates of side chain atoms for the specified CHI angles

        coords <- getCoords(angles)
        """
        # create array of transformed coordinates (initially orig)
        coords = array(self.horigCoords, 'd')
        oc = self.origCoords
        hoc = self.horigCoords
        # used to propagate tansformation along the chain
        #cmat = identity(4)
        cmat = None
        
        #print 'angles:', index, deviations
        for i, angle in enumerate(angles):
            #print 'origAngle', self.originalAngles[i]
            #print 'ANGLE1', angle
            angleDelta = angle - self.originalAngles[i]
            if angle < 0:
                angleDelta = self.originalAngles[i] - angle
            #print 'angleDeltaorig', angleDelta
            if angleDelta>180.:
                angleDelta = -360.+angleDelta
            elif angleDelta<-180.:
                angleDelta = 360.+angleDelta
            #print 'ANGLEDelta', angleDelta
            a1Ind, a2Ind = self.rotBondIndices[i]

            # compute xform matrix for Chi x with this angle
            #mat = rotax(oc[a1Ind], oc[a2Ind], (angle-self.originalAngles[i])*degtorad,
            #            transpose=1)
            mat = rotax(oc[a1Ind], oc[a2Ind], angleDelta*degtorad, transpose=1)
            
            # add mat to cmat
            if cmat is None:
                cmat = mat
            else:
                cmat = dot(mat, cmat)

            # transform atoms effected by Chi x
            for j in self.rotatedAtomsIndices[i]:
                coords[j] = dot( [hoc[j]], cmat)
                #x,y,z = oc[j]
                #coords[j][0] = cmat[0][0]*x + cmat[1][0]*y + cmat[2][0]*z + cmat[3][0]
                #coords[j][1] = cmat[0][1]*x + cmat[1][1]*y + cmat[2][1]*z + cmat[3][1]
                #coords[j][2] = cmat[0][2]*x + cmat[1][2]*y + cmat[2][2]*z + cmat[3][2]

            #sanity check
            if check:
                atoms = []
                for atName in self.angleDef[i][0]:
                    atoms.append( [x for x in self.atoms if x.name==atName][0] )
                t = torsion(coords[self.atoms.index(atoms[0])][:3],
                            coords[self.atoms.index(atoms[1])][:3],
                            coords[self.atoms.index(atoms[2])][:3],
                            coords[self.atoms.index(atoms[3])][:3])
                if t< 0.:
                    t += 360.0
                #sa1 = min( abs(angle), abs(angle)-180, abs(angle)-360) 
                #sa2 = min( abs(t), abs(t)-180, abs(t)-360)
                #sa1 = min( angle, abs(angle)-180,abs(angle)-360.0) 
                #sa2 = min( t,360-abs(t))
                #print 'FUGU', angle, t
                #if abs(sa1-sa2) > 1.0:
                
                if abs(angle-t) > 1.0 and abs(angle-360.0+t) > 1.0:
                    print 'WANTED', angle, 'GOTTEN', t, 'DIFF', abs(angle-t)
                    raise RuntimeError
                    import pdb
                    pdb.set_trace()


        #print coords[3:]

        return coords[:,:3]


if __name__=='__main__':
    from MolKit import Read
    mol = Read('/gpfs/home/pradeep/Workspace/Astex-jan2014/receptors/1k3u_rec.pdbqt')[0]#'1v0p/1v0p_rec.pdbqt')[0]
    residue = mol.chains[0].childByName['ILE214','ILE232']#'ILE10']
    
    import FlexTree
    from FlexTree.FTRotamers import  FTSoftRotamer, RotamerLib
    import os
    rotamerLib = RotamerLib(
        os.path.join(FlexTree.__path__[0], 'bbind02.May.lib'),
        os.path.join(FlexTree.__path__[0], 'rotamer.def'))

    angDef, angList, angDev = rotamerLib.get(residue.type)

    atoms = residue.atoms.copy()
    #atoms.remove(residue.childByName['N'])
    atoms.remove(residue.childByName['HA'])
    atoms.remove(residue.childByName['C'])
    atoms.remove(residue.childByName['O'])

    rota = Rotamer(atoms, angDef, angList)
    c = rota.getCoords(0, (0,0))
    print c
    
    angles = [122.736690428, 266.331375378]
    t0 = time()
    for ti in xrange(10000):
        c = rota.getCoordsFromAngles( angles )
    print 'time1',ti,  time()-t0
    print c
