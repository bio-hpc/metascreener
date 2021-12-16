########################################################################
#
# Date: 2013 Authors: Pradeep Ravindranath, Michel Sanner
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
# $Header: /opt/cvs/AutoDockFR/bin/fixMaps.py,v 1.2 2013/11/21 17:50:51 sanner Exp $
#
# $Id: fixMaps.py,v 1.2 2013/11/21 17:50:51 sanner Exp $
#

#!/usr/bin/env pythonsh
import sys, pdb
from time import time
from bhtree import bhtreelib
import numpy

t0 =  time()                        # Stores the time (float) at the start of the program

if len(sys.argv)==1:  ## print help msg if no input is given
    sys.argv.append('-help')

from AutoDockFR.Docking import AutoDockFR
from AutoDockFR.Param import Params

input=Params(args=sys.argv[1:])
#MLDprint input.optList.setting

#pdb.run("adfr=AutoDockFR(input)")
adfr = AutoDockFR(input)

from AutoDockFR.orderRefAtoms import orderRefMolAtoms
maxTry = adfr.setting['constraintMaxTry']
gscorer=None
if adfr.setting['gridMaps']:
    gscorer = adfr.docking.scoreObject.gridScorer

###if adfr.setting['initPopSize']:
###    print "FUGU####################"
if gscorer:
    gscorer.fixTranslation(adfr.docking, fixMaps=True)
