#######################################################################
#
# Date: May 2012 Authors: Michel Sanner
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2013
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/orderRefAtoms.py,v 1.3 2014/08/18 21:17:42 pradeep Exp $
#
# $Id: orderRefAtoms.py,v 1.3 2014/08/18 21:17:42 pradeep Exp $
#
"""
This module implements a function to order reference molecules to match the
order of the atoms in the docked ligand
"""
from MolKit.molecule import AtomSet

def orderRefMolAtoms(ligAts, origAtomSet):
    """
    Try to re-order ligAts to match origAtomSet (if needed)
    returns an AtomSet containing the sorted list of atoms
    or None if atoms do not match between the files
    """
    sortedAtoms = []
    if len(ligAts)!=len(origAtomSet): return None
    for a in origAtomSet:
	matches = [b for b in ligAts if b.name==a.name and b.parent.name==a.parent.name\
		and b.parent.parent.id==a.parent.parent.id]
	#import pdb; pdb.set_trace() #Debugging
        #print matches
	if len(matches)!=1:
            raise RuntimeError, 'NO MATCH %s %d'%(a.full_name(), len(matches))
	else:
	    sortedAtoms.append(matches[0])

    #Create an AtomSet out of the list of atoms
    return AtomSet(sortedAtoms)


