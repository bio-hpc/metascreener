########################################################################
#
# Date: May 2005 Author: Michel Sanner, Pradeep Ravindranath
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: TSRI
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/bin/randomizeReceptor.py,v 1.2 2014/07/31 20:51:29 sanner Exp $
#
# $Id: randomizeReceptor.py,v 1.2 2014/07/31 20:51:29 sanner Exp $
#

"""
This module implements a utility to randomize rotameric side chains in the receptor

"""

def randomizeSoftRot(mol, flexResSelectionString):
    from AutoDockFR.utils import RecXML4SoftRotamSC

    # make sure the molecule has bonds. Needed to find Hn atom
    assert len(mol.allAtoms.bonds[0]) > len(mol.allAtoms)
    FTgenerator = RecXML4SoftRotamSC(mol, flexResSelectionString)
    ft = FTgenerator.getTree()

    from random import uniform

    # loop over motion objects and for FTMotion_SoftRotamer set random CHI angles
    from FlexTree.FTMotions import FTMotion_SoftRotamer
    allAngles = []
    for m in ft.getAllMotion():
        print 'Random angles for residue', m.name,
        if isinstance(m, FTMotion_SoftRotamer):
            angles = []
            for i in range(len(m.angDef)):
                angles.append( uniform(0., 360.) )
                print angles[-1],
            print
            m.setAngles(angles)
            m.apply(m.node().molecularFragment)
            allAngles.append(angles)
            
    return allAngles

if __name__=='__main__':
    
    import sys
    molfile = sys.argv[1]
    flexResSelectionString = sys.argv[2]
    outFilename = sys.argv[3]

    from MolKit import Read
    mol = Read(molfile)[0]
    mol.buildBondsByDistance()
    angles.append(randomizeSoftRot(mol, flexResSelectionString))

    ## chi = [[], [], [], []]
    ## for i in range(5000):
    ##     print '---->', i
    ##     angsPerCall = randomizeSoftRot(mol, flexResSelectionString)
    ##     for angsPerRot in angsPerCall:
    ##         for i, ang in enumerate(angsPerRot):
    ##             chi[i].append(ang)
        
    # write the molecule
    comments = [
        "*********************************************************\n",
        "receptor with randomized soft rotameric side chains\n",
        '*********************************************************'
        ]
    mol.parser.write_with_new_coords(
        mol.allAtoms.coords, filename=outFilename, comments=comments,
        withBondsFor=mol)

    ## from Vision import runVision
    ## runVision()
    ## Vision.ed.loadNetwork('/home/sanner/plotAngles_net.py')
    
