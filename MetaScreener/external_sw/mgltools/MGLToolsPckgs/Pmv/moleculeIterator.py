
# class used to iterate over molecules in  a molecule file parcer such as SDF.
class MoleculeIterator:

    def __init__(self, object, vf):
        self.object = object
        self.vf = vf
        self.parser = self.object.parser
        self.filename = self.parser.filename
        self.numMols = self.parser.numOfMolecules()
        self.currentMolInd = self.parser.getMolIndex(self.object.name)
        self.top = object.top
        self.parent = object.parent
        self.name = object.name
        self.molcache = {}
        self.numStoredMols = 10
        from Pmv.dashboard import MolFragIteratorNodeWithButtons
        self.molIteratorNodeClass = MolFragIteratorNodeWithButtons
	self.counter = None


    def getMolName(self, molind):
        return self.object.parser.getMolName(molind)


    def getNextMolecule(self, molind):
        assert molind < self.numMols
        molname = self.getMolName(molind)
        if self.molcache.has_key(molind) and self.molcache[molind].name == molname:
             mol = self.molcache[molind]
             tree = self.vf.dashboard.tree
             for col in tree.columns:
                 if col.showPercent:
                     if hasattr (mol ,col.showPercent):
                         if col.showPercent != "_showLinesStatus":
                             setattr(mol ,col.showPercent, 0.0)
        else:
            mol = self.parser.getMolecule(molind)[0]
        self.currentMolInd = molind

        self.object = mol
        self.top = self.object.top
        self.parent = self.object.parent
        self.name = self.object.name
        return mol


    def clearMolCache(self):
        for k in self.molcache.keys():
            self.deleteMolecule(self.molchache.pop(k))


    def addToMolCache(self, molind, mol):
        #print "addToMolCache:", molind, mol
        if not self.molcache.has_key(molind):
            #print "len molcache:", len(self.molcache), self.numStoredMols
            if len(self.molcache) > self.numStoredMols:
                inds = self.molcache.keys()
                inds.sort()
                minind = inds[0]
                if id(self.molcache[minind]) == id(self.object):
                    minind = inds[1]
                #print "minind", minind
                self.deleteMolecule(self.molcache.pop(minind))
                #print "len molcache2:", len(self.molcache)
            self.molcache[molind] = mol
            

    def deleteMolecule(self, mol):
        #print "deleteMolecule", mol
        # Delete all the reference to the atoms
        vf = self.vf
        if hasattr(mol.allAtoms, 'bonds'):
            bnds = mol.allAtoms.bonds[0]
            for b in bnds:
                b.__dict__.clear()
                del(b)

        mol.allAtoms.__dict__.clear()
        del mol.allAtoms
        if vf.hasGui and hasattr(mol, 'geomContainer'):
            for g in mol.geomContainer.geoms.values():
                if hasattr(g, 'mol'):
                    delattr(g, 'mol')
            mol.geomContainer.geoms.clear()
            mol.geomContainer.atoms.clear()
            delattr(mol.geomContainer, 'mol')
            del mol.geomContainer

        if hasattr(mol, 'atmNum'):
            mol.atmNum.clear()
            del mol.atmNum

        if hasattr(mol, 'childByName'):
            mol.childByName.clear()
            del mol.childByName

        if len(mol.children):
            deletedLevels = mol.deleteSubTree()
        else:
            deletedLevels = []
        # then delete all the refences to the molecule
        del mol.top
        # Then delete the molecule
        deletedLevels.insert(0, mol.__class__)
        mol.__dict__.clear()
        del mol
        vf._deletedLevels = deletedLevels 
