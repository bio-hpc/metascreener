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
This module implements the utilities (tools) related to FlexTree

"""

from MolKit.molecule import AtomSet

def getSameAtomsfrom(targetAtoms, srcAtoms):
    """ Select the atoms in targetAtoms from srcAtom
targetAtoms, srcAtoms are both AtomSet()
e.g. select backbone of Residue 18-32 (targetAtoms) from srcAtoms (chain A atoms)
"""
    result=[]
    openRes=srcAtoms.parent.uniq()

    for atom  in targetAtoms:
        name=atom.full_name()
        nameList  = name.split(':')
        chainName=nameList[1]
        resName = nameList[2]
        atomName = nameList[3]
        found=False

        ch = openRes.parent.uniq().objectsFromString(chainName)[0]
        res = ch.residues.objectsFromString(resName)[0]            
        atom  = res.atoms.objectsFromString(atomName)[0]
        if atom in srcAtoms:
            found = True

        if not found:
            print "Error..", atom.full_name() , "not found"
            ff=1+'dfsa' ## for debug
            return None
        else:
            #print "appending ", atom.name
            result.append(atom)

    result=AtomSet(result)
    assert result.full_name() == targetAtoms.full_name()
    return result



