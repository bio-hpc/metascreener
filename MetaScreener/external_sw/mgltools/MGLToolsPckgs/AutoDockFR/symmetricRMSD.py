
from MolKit.molecule import AtomSet
from mglutil.math.rmsd import RMSDCalculator
from AutoDockFR.orderRefAtoms import orderRefMolAtoms

class Atom:

    def __init__(self, mol):
        self.mol = mol
        
        
class RMSDwithAutomosphisms:
    """
    class to compute RMSD between 2 poses of the same molecule while taking into account
    symmetry described by a list fo automorphisms.

    the object is created for a set of atoms and a list of automosphisms.
    Each automorphisms is a list of atom names that has to be as long as the set of
    atoms given to the constructor.

    the rmsd is computed for the identity pairing and for each given automorphism. The
    minimum valus of all these RMSDs is return by computeRMSD(coords)
    """

    def __init__(self, atoms, automorphisms):
        # create rmsd calculator
        self.sortedRefAts = atoms

        # atoms may not be sorted in the same way the list of atoms was sorted
        # when computing the RMSD, This could lead to a wrong set of automorphismsIndices
        # to fix that we create a copy of the AtomSet and sort it to obtain the order
        # of the atoms in the PDB file, then we create a lookup that tells us the index
        # of each atom in the list of atoms in the original order and we use lookup to
        # build automorphismsIndices
        # create a list of atoms in the original order (used to compute automorphisms)
        self.atomsInOriginalOrder = AtomSet(atoms)
        self.atomsInOriginalOrder.sort()
        # build a lookup table for automorphisms atom names
        lookup = []
        oriOrderAtomNames = self.atomsInOriginalOrder.name
        for a in atoms:
            lookup.append(oriOrderAtomNames.index(a.name))
            
        self.refCoords = atoms.coords
        self.rmsdCalc = RMSDCalculator(refCoords=self.refCoords)
        self.automorphisms = automorphisms
        # build a list of indices used to compute the RMSD
        self.automorphismsIndices = [] # list of 0-based indices
        atNames = atoms.name
        for names in automorphisms:
            indices = []
            for i in range(len(names)):
                indices.append(atNames.index(names[lookup[i]]))
            self.automorphismsIndices.append(indices)
            
            
    def setRefCoords(self, coords):
        """
        set the reference atoms
        """
        self.rmsdCalc.setRefCoords(coords)
        self.refCoords = coords


    def computeRMSD(self, coords):
        """
        compute RMSD with reference atoms. coords are assumed to be in the same order
        as self.sortedRefAts
        """
        minRMSD = 99999.

        # compute rmsd of each automorphism
        for indices in self.automorphismsIndices:
            sortedCoords = [coords[i] for i in indices]
            rmsd = self.rmsdCalc.computeRMSD(sortedCoords)
            if rmsd < minRMSD:
                minRMSD = rmsd

        return minRMSD

 
class RMSDwithSymmetry:
    """
    class to compute RMSD between 2 identical molecules when the molecule has sysmmetry

    the object is created for a set of atoms with bonds and  string specifying sets of
    atoms at the centers of symmetry. Centers can be specified using a selection string
    (NOTE no spaces are allowed in comma separated lists) or by specifying a list of
    explicit equivalences e.g. [['A24', 'A20'], ['A21', 'A23']]

    The first generation of atoms are all the center atoms. next generation are obtained
    by selecting all atoms (not yet seen) linked by a bond to an atom of the previous generation.
    Atoms within the same generation are considered identical and can be interchanged during RMSD
    calculation. Every pointis equivalent to itself.

    When we compute RMSD we compute the identity pairing (i.e. first coordinate passed to
    computeRMSD is matched to first reference coordinate). Then we compute a coordinate pair
    assignment in which each point is assigned to the closest equivalent reference point, and
    compute the RMSD using this pairs of points.

    We return the lowest of the 2 RMSDs
    """

    def __init__(self, atoms, centerSelStr):
        """
        atoms are the reference atoms
        """
        assert len(atoms.bonds[0]) > 0 # we nee bonds        

        # for each atom in atoms build a list of atoms that can be exchanged
        # traverse molecule graph and at each generation tag atoms of same type as equivalent
        self.sortedRefAts = atoms
        self.refCoords = atoms.coords

        # find AtomSet of central atoms
        # this code does not work work. get() only returns 1 atom
        #center = atoms.get(centerSelStr)
        if isinstance(centerSelStr, str):
            centers = [atoms.get(x.strip())[0] for x in centerSelStr.split(',')]
            self.equiv = self.findEquivalentIndices(atoms, centers)
        else:
            idAts = [-1]*len(atoms)
            for i, a in enumerate(atoms):
                a._num = i
                idAts[a._num] = [a._num]
            for equiVlist in centerSelStr:
                #print centerSelStr, equiVlist
                indices = [atoms.get(atName)[0]._num for atName in equiVlist]
                for i in range(len(indices)):
                    a = indices[i]
                    for j in range( i+1, len(indices)):
                        b = indices[j]
                        idAts[a].append(b)
                        idAts[b].append(a)
            self.equiv = idAts
            #print self.equiv
            
        # create rmsd calculator
        self.rmsdCalc = RMSDCalculator(refCoords=self.refCoords)


    def printEquiv(self):
        for num, atom in enumerate(self.sortedRefAts):
            print atom.name, [self.sortedRefAts[x].name for x in self.equiv[num]]
        

    def setRefCoords(self, coords):
        """
        set the reference atoms
        """
        self.rmsdCalc.setRefCoords(coords)
        self.refCoords = coords
        

    def computeRMSD(self, coords):
        """
        compute RMSD with reference atoms. coords are assumed to be in the same order
        as self.sortedRefAts
        """
        # compute rmsd with identity assignment
        rmsd1 = self.rmsdCalc.computeRMSD(coords)
	#print "rmsd1 ID:", rmsd1

        # get a sorted list of atoms for atoms
        matchedCoords = self.pairPoints(coords, self.equiv)

        # compute rmsd with assignment based on distance
        rmsd2 = self.rmsdCalc.computeRMSD(matchedCoords)
	#print "rmsd2:", rmsd2
        return min(rmsd1, rmsd2)
        

    def pairPoints(self, coords, equiv):
        """
        sort atoms to match each of the to its closest partner according to
        idAts
        """
        ##print equiv
        import itertools
        used = [0]*len(self.refCoords)
	##used1 = [0]*len(self.refCoords)
        sortedPoints = []
        for i in range(len(coords)):
            xr, yr, zr = self.refCoords[i]
	    ##print "refcoord1:", xr,yr,zr
            mind = 99999.
            bondedpair=[]
            #dist=[]
            c1 = None
            
                #if len(xx) >1 and len(equiv[i])  >1:
            for b in equiv[i]:
                if used[b]: continue
                ## FIX ME
                ## for bond in self.sortedRefAts[b].bonds:
                ##     a2 = bond.atom1
                ##     if a2==self.sortedRefAts[b]: a2 = bond.atom2
                ##     print a2
                ##     for xx in equiv:
                ##         if len(xx) >1 and len(equiv[i])  >1:
                ##             if a2 in [self.sortedRefAts[atm] for atm in xx]:
                ##                 bondedpair.append([b,a2._num])
                ## bondedsym = [center for center,_ in itertools.groupby(bondedpair)]
                ## print bondedsym
                ## ##(xr21,yr21,zr21)=(xr22,yr22,zr22) = (9999,9999,9999)
                ## if bondedsym:
                ##     for k,aa in enumerate(bondedsym):
                ##         for ii,n in enumerate(equiv):
                ##             if aa[1] in n:
		## 		if used1[ii]: continue
                ##                 #print aa[1],self.sortedRefAts[aa[1]],n,self.sortedRefAts[n[1]],ii
                ##                 ##if (xr21, yr21, zr21) != self.refCoords[ii]:
                ##                 ##    xr21, yr21, zr21 =  self.refCoords[ii]
                ##                 ##else:
                ##                 ##    xr22, yr22, zr22 =  self.refCoords[ii]
                ##                 else:
                ##                     xr2, yr2, zr2 =  self.refCoords[ii]
                ##                     print "refcoord2:", self.refCoords[ii] 
                ##                     used1[ii]=True
                ##                     break
                ##         x1, y1, z1 = coords[aa[0]]
                ##         x2, y2, z2 = coords[aa[1]]
                ##         dist = ((xr-x1)*(xr-x1) + (yr-y1)*(yr-y1) + (zr-z1)*(zr-z1) +(xr2-x2)*(xr2-x2) + (yr2-y2) *(yr2-y2) + (zr2-z2)*(zr2-z2))
                ##         ##dist1 = ((xr-x1)*(xr-x1) + (yr-y1)*(yr-y1) + (zr-z1)*(zr-z1) +(xr21-x2)*(xr21-x2) + (yr21-y2) *(yr21-y2) + (zr21-z2)*(zr21-z2))
                ##         ##dist2 = ((xr-x1)*(xr-x1) + (yr-y1)*(yr-y1) + (zr-z1)*(zr-z1) +(xr22-x2)*(xr22-x2) + (yr22-y2) *(yr22-y2) + (zr22-z2)*(zr22-z2))
                ##         ##if dist1 < dist2:
                ##         ##    dist = dist1
                ##         ##else:
                ##         ##    dist = dist2
                ##         if dist<mind:
                ##             mind = dist
                ##             c = aa[0]
                ##             #print "FUGU"
                ##             #c1 = aa[1]
                ##     #sortedPoints.append(coords[c])
                ##     #used[c] = True
                ##     #if c1:
                ##     #    sortedPoints.append(coords[c1])
                ##     #    used[c1] = True
                ## else:
                x, y, z = coords[b]
                d = (xr-x)*(xr-x) + (yr-y)*(yr-y) + (zr-z)*(zr-z)
                if d<mind:
                    mind = d
                    c = b
                        #print "FUGU1"

                ## else:
                ##     for b in equiv[i]:
                ##         if used[b]: continue 
                ##         x, y, z = coords[b]
                ##         d = (xr-x)*(xr-x) + (yr-y)*(yr-y) + (zr-z)*(zr-z)
                ##         if d<mind:
                ##             mind = d
                ##             c = b
                ##             print "FUGU2" 
            ##print 'pair ', i, c, self.sortedRefAts[i].name ,self.sortedRefAts[c].name, mind
            sortedPoints.append(coords[c])
            used[c] = True
        #print c
        return sortedPoints


    def findEquivalentIndices(self, atoms, centers):
        # breadth first traversal of the molecule to find all atoms at
        # a the same distance (in number of bonds) from the centers and that 
        # have the same type
        idAts = [-1]*len(atoms)
        for i, a in enumerate(atoms):
            a._num = i
            a.dist = -1
            idAts[a._num] = [a._num]

        children = centers
        for c in centers:
            c.dist = 0

        if len(centers)>1:
            for i in range(len(centers)):
                a = centers[i]
                for j in range( i+1, len(centers)):
                    b = centers[j]
                    if a.autodock_element==b.autodock_element:
                        idAts[a._num].append(b._num)
                        idAts[b._num].append(a._num)

        while len(children):
            nextGen = []
            for current in children:
                for bond in current.bonds:
                    a2 = bond.atom1
                    if a2==current: a2 = bond.atom2
                    if a2.dist==-1:
                        nextGen.append(a2)
                        a2.dist=current.dist+1
            for i in range(len(nextGen)):
                a = nextGen[i]
                for j in range( i+1, len(nextGen)):
                    b = nextGen[j]
                    if a.autodock_element==b.autodock_element:
                        idAts[a._num].append(b._num)
                        idAts[b._num].append(a._num)
            #print nextGen
            children = nextGen

        return idAts
        

    ## below is old implementation using atoms
    ##
    def closestAtomsOfSameType(self, refAtoms, atoms, idAts):
        """
        sort atoms to match each of the to its closest partner according to
        idAts
        """
        for a in atoms: a.used = False # prevent re-using an atom in pairs
        sortedMolAtoms = []
        for i in range(len(refAtoms)):
            a = refAtoms[i]
            xr, yr, zr = a.coords
            mind = 99999.
            for b in idAts[atoms[i]]:
                if b.used: continue 
                x, y, z = b.coords
                d = (xr-x)*(xr-x) + (yr-y)*(yr-y) + (zr-z)*(zr-z)
                if d<mind:
                    mind = d
                    c = b
            sortedMolAtoms.append(c)
            c.used = True

        for a in atoms: del a.used
        return AtomSet(sortedMolAtoms)


    def findEquivalence(self, atoms, center):
        # breadth first traversal of the molecule to find all atoms at
        # a given distance (in number of bonds) that have the same type
        # center is the atom what is the symmetry center
        idAts = {}
        for a in atoms:
            a.dist = -1
            idAts[a] = [a]

        children = center
        for c in center:
            c.dist = 0

        if len(center)>1:
            for i in range(len(center)):
                a = center[i]
                for j in range( i+1, len(center)):
                    b = center[j]
                    if a.autodock_element==b.autodock_element:
                        idAts[a].append(b)
                        idAts[b].append(a)

        while len(children):
            nextGen = []
            for current in children:
                for bond in current.bonds:
                    a2 = bond.atom1
                    if a2==current: a2 = bond.atom2
                    if a2.dist==-1:
                        nextGen.append(a2)
                        a2.dist=current.dist+1
            for i in range(len(nextGen)):
                a = nextGen[i]
                for j in range( i+1, len(nextGen)):
                    b = nextGen[j]
                    if a.autodock_element==b.autodock_element:
                        idAts[a].append(b)
                        idAts[b].append(a)
            #print nextGen
            children = nextGen

        return idAts


    def __call__(self, refAtoms, movAtoms, centerSelStr):
        # obsolete
        assert len(refAtoms) == len(movAtoms)
        self.refAtoms = refAtoms # atom set that are the reference we compute RMSD from (e.g. Xray)
        self.movAtoms = movAtoms # atoms that are moving (e.g. docking pose)

        # sort reference atoms to match order in movAtoms
        sortedRefAts = orderRefMolAtoms(refAtoms, movAtoms)

        # create rmsd calculator
        rmsdCalc = RMSDCalculator(refCoords=sortedRefAts.coords)

        # compute rmsd with identity assignment
        rmsd = rmsd1 = rmsdCalc.computeRMSD(movAtoms.coords)

        # find AtomSet of central atoms 
        center = movAtoms.get(centerSelStr)
        # for each atom in atoms build a list of atoms that can be exchanged
        atEquiv = self.findEquivalence(movAtoms, center)
        # get a sorted list of atoms for atoms
        ordered1 = self.closestAtomsOfSameType(sortedRefAts, movAtoms, atEquiv)
        # compute rmsd with assignment based on distance
        rmsd2 = rmsdCalc.computeRMSD(ordered1.coords)

        ## if __debug__:
        ##     print 'Symmetric atoms ====================='
        ##     for a, al in atEquiv.items():
        ##         if len(al)>1:
        ##             print a.name, '  ',
        ##             for b in al[1:]:
        ##                 print b.name,
        ##             print
        ##     print 'END Symmetric atoms ====================='

        ## for a1,a2 in zip(refAtoms, ordered1):
        ##     print "(%s,%s) "%(a1.name, a2.name),
        ## print
        return min(rmsd, rmsd2)

if __name__=='__main__':
    from MolKit import Read

    centers = {
        '1HVI': 'C46,C49',
        '1HVJ': 'C47,C49',
        '1HVK': 'C46,C49',
        '1HVL': 'C46,C49',
        '1HVS': 'C46,C49',
        '4PHV': 'C1',
        '1HVR': 'C1,C3,C4,C5,C6,N2,N7',
        '9HVP': 'C3',
        }

    lig = '1HVR'
    lig = '1HVJ'
    lig = '1HVK'
    lig = '1HVL'
    lig = '1HVS' #check
    lig = '4PHV' #check
    lig = '9HVP'

    ref = Read('%s_%s_Lig_random/%s_Lig.pdbqt'%(lig,lig,lig))[0]

    if lig=='4PHV':
        m1 = Read('%s_%s_Lig_random/%s_%s_Lig_random_job_4014_sol_0.pdbqt'%(lig,lig,lig,lig))[0]
        m2 = Read('%s_%s_Lig_random/%s_%s_Lig_random_job_4014_sol_1.pdbqt'%(lig,lig,lig,lig))[0]
    else:
        m1 = Read('%s_%s_Lig_random/%s_%s_Lig_random_job_4011_sol_0.pdbqt'%(lig,lig,lig,lig))[0]
        m2 = Read('%s_%s_Lig_random/%s_%s_Lig_random_job_4011_sol_1.pdbqt'%(lig,lig,lig,lig))[0]

    m1.buildBondsByDistance()
    m2.buildBondsByDistance()

    rmsdCWS  = RMSDwithSymmetry()
    sortedRefAts = orderRefMolAtoms(ref.allAtoms, m1.allAtoms)
    rmsdCalc = RMSDCalculator(refCoords=sortedRefAts.coords)
    print 'M1 identity: ', rmsdCalc.computeRMSD(m1.allAtoms.coords)
    print 'M2 identity: ', rmsdCalc.computeRMSD(m2.allAtoms.coords)

    print 'M1 with Sym: ', rmsdCWS(ref.allAtoms, m1.allAtoms, centers[lig])
    print 'M1 with Sym: ',rmsdCWS(ref.allAtoms, m2.allAtoms, centers[lig])


## ## WARNING: it is critical that sortedRefAts has the same order as m1.allAtoms
## ##          i.e. sortedRefAts is the result of
## ##              orderRefMolAtoms(ref.allAtoms, m1.allAtoms)
## ##          where ref is the molecule we want to compute the RMSD from
## ##
## center = m1.allAtoms.get(centers[lig])
## atEquiv = findEquivalence(m1.allAtoms, center)
## ordered1 = closestAtomsOfSameType(sortedRefAts, m1.allAtoms, atEquiv)
## print rmsdCalc.computeRMSD(ordered1.coords)

## for a1,a2 in zip(ref.allAtoms, ordered1):
##     print "(%s,%s) "%(a1.name, a2.name),
## print

## print

## center = m2.allAtoms.get(centers[lig])
## atEquiv = findEquivalence(m2.allAtoms, center)
## ordered2 = closestAtomsOfSameType(sortedRefAts, m2.allAtoms, atEquiv)
## print rmsdCalc.computeRMSD(ordered2.coords)

## for a1,a2 in zip(ref.allAtoms, ordered2):
##     print "(%s,%s) "%(a1.name, a2.name),
## print

## #for k,v in idAts.items():
## #    print k, len(v)

