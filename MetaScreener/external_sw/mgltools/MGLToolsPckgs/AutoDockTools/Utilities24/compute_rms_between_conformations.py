#!/usr/bin/env python
#
# 
#
# $Header: /opt/cvs/python/packages/share1.5/AutoDockTools/Utilities24/compute_rms_between_conformations.py,v 1.3 2012/04/05 21:12:25 rhuey Exp $
#
import os, glob
import numpy.oldnumeric as Numeric
from math import sqrt

from MolKit import Read
from AutoDockTools.Docking import Docking
from mglutil.math.rmsd import RMSDCalculator


def dist(coords1, coords2):
    """return distance between two atoms, a and b.
    """
    npts = len(coords1)
    pt1 = Numeric.add.reduce(coords1)/npts
    pt2 = Numeric.add.reduce(coords2)/npts
    d = Numeric.array(pt1) - Numeric.array(pt2)
    return sqrt(Numeric.sum(d*d))


if __name__ == '__main__':
    import sys
    import getopt


    def usage():
        "Print helpful, accurate usage statement to stdout."
        print "Usage: compute_rms_between_conformations.py -r reference"
        print
        print "  Description of command..."
        print "    Computes rms between two conformations of a molecule and stores it in 'summary_rms_results.txt'"
        print "      -f     first filename"
        print "      -s     second filename"
        print "  Optional parameters:"
        print "     [-x]    omit hydrogen atoms from the calculation"
        print "     [-o]    output filename"
        print "     [-v]    verbose output"


    # process command arguments
    try:
        opt_list, args = getopt.getopt(sys.argv[1:], 'f:s:o:xvh')
    except getopt.GetoptError, msg:
        print 'compute_rms_between_conformations.py: %s' %msg
        usage()
        sys.exit(2)

    # initialize required parameters
    #-f: first filename
    first =  None
    #-s: second filename
    second =  None
    #-o outputfilename
    outputfilename = "summary_rms_results.txt"
    # optional parameters
    #-x exclude hydrogen atoms from calculation
    omit_hydrogens = False
    #-v detailed output 
    verbose = None

    #'f:s:o:xvh'
    for o, a in opt_list:
        #print "o=", o, " a=", a
        if o in ('-f', '--f'):
            first = a
            if verbose: print 'set first filename to ', a
        if o in ('-s', '--s'):
            second = a
            if verbose: print 'set second filename to ', a
        if o in ('-o', '--o'):
            outputfilename = a
            if verbose: print 'set outputfilename to ', a
        if o in ('-x', '--x'):
            omit_hydrogens = True
            if omit_hydrogens: print 'set omit_hydrogens to ', True
        if o in ('-v', '--v'):
            verbose = True
            if verbose: print 'set verbose to ', True
        if o in ('-h', '--'):
            usage()
            sys.exit()

    if not first:
        print 'compute_rms_between_conformations: reference filename must be specified.'
        usage()
        sys.exit()

    if not second:
        print 'compute_rms_between_conformations: second filename must be specified.'
        usage()
        sys.exit()

    #process docking in reference directory
    #read the molecules
    first = Read(first)[0]
    second = Read(second)[0]
    assert len(first.allAtoms)==len(second.allAtoms)
    first_ats = first.allAtoms
    second_ats = second.allAtoms
    if omit_hydrogens:
        first_ats = first.allAtoms.get(lambda x: x.element!='H')
        second_ats = second.allAtoms.get(lambda x: x.element!='H')
    #setup rmsd tool
    rmsTool = RMSDCalculator(first_ats.coords)
    need_to_open = not os.path.exists(outputfilename)
    if need_to_open:
        fptr = open(outputfilename, 'w')
        ostr= "reference filename      test filename\t\trms \n"
        fptr.write(ostr)
    else:
        fptr = open(outputfilename, 'a')
   
    ostr = "% 10s,\t% 10s,  % 10.4f\n" %(first.parser.filename, second.parser.filename, rmsTool.computeRMSD(second_ats.coords))
    fptr.write(ostr)
    fptr.close()
    

# To execute this command type:
# compute_rms_between_conformations.py -f filename -s secondfilename 
#           -o  outputfilename  -v verbose
# NOTE: -f, -d and -t require arguments whereas the other, -v, sets a boolean

