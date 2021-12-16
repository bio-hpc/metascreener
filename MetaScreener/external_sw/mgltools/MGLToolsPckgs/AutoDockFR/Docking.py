#######################################################################
#
# Date: May 2012 Authors: Michel Sanner, Matt Danielson
#
#    sanner@scripps.edu
#
#       The Scripps Research Institute (TSRI)
#       Molecular Graphics Lab
#       La Jolla, CA 92037, USA
#
# Copyright: Michel Sanner and TSRI 2012
#
#########################################################################
#
# $Header: /opt/cvs/AutoDockFR/Docking.py,v 1.75 2014/08/18 21:08:55 pradeep Exp $
#
# $Id: Docking.py,v 1.75 2014/08/18 21:08:55 pradeep Exp $
#
"""
This module implements the base objects used for automatic docking 
"""


import sys, time, types, string, random
import copy, pdb, os
from AutoDockFR.GA import Population, GA, GA1, GA2, GA2_1, GA2_2, GA3, GA4, GA5, GA6, SolisWet
from AutoDockFR.PSO import PSO
from AutoDockFR.utils import pdbqt2XML
from AutoDockFR.ga_util import FlipCoin
from AutoDockFR.orderRefAtoms import orderRefMolAtoms

from MolKit import Read

from Version import printHeader
from random import gauss, uniform


# check if C++ AutoDock is installed
try:
    from AutoDockFR.ADCscorer import AD42ScoreC
    foundAutoDockC = True
except ImportError:
    foundAutoDockC = False

if foundAutoDockC:
    ## start of Docking class
    class AutoDockFR:
        def __init__(self, param):
            """ param is a AutoDockFR.Param object
            """
            self.param = param
            self.setting = self.param.get()
	    #MLDprint self.setting 
        
            # set the current working directory to be the folder containing
            # the setting file so that filename in settings are relative to the
            # setting location
	    folder = os.path.split(param.optList.filename)[0]
	    if folder:
                os.chdir(folder)

            # Sanity checks on keywords in the settings file
            if not self.param.validParams():
                sys.exit(1)
                return

            # Create an instance of the docking search (GA, DACGA, PSO)
            if self.setting['scoringFunction'] in ['AutoDock4.2', 'RMSD']:
                search = self.setting['search']	
                if search not in AvailableSearch.keys():
                    print "searching methond %s is not supported" % search
                    raise TypeError
                else:
                    # AvailableSearch is a global dictionary of search 
                    # algormithms:  See EOF
		    # (Dock_Serial) that inherits Parms class
                    self.docking = AvailableSearch[search](param) 
 
            elif self.setting['scoringFunction'] == 'USRscore':
                self.docking = Shape_Docking(param)
            else:
                print "Unknown scoring function..", \
                      self.setting['scoringFunction']
                raise 
            return


        def initialPopulationForLocalSearch(self, popSize, individual):
            # create an initial population for searching within 2 Angs RMSD
            # of a given solution
            # FIXME: currently hardwired for 2 Ang RMSD and rigid receptor

            def makeIndividual(ind, delta):
                newInd = ind.clone()
                # rotation
                for i in range(4):
                    newInd[i]._value += gauss (0.0, delta[i])
                # translation
                for i in range(4, 7):
                    newInd[i]._value += uniform(-delta[i], delta[i])
                # torsions
                for i in range(7, len(delta)):
                    newInd[i]._value += gauss(0.0, delta[i])
                return newInd

            pop = self.docking.search.pop
            pop._size(popSize)
            rmsdcalc = self.docking.search.rmsdCalculators[0]

            boxDim = self.docking.LigandTree.getAllMotion()[0].motionList[1].boxDim
            # compute vector of deviations 
            delta = [0.1,0.1,0.1,0.1,
                     # compute translation fraction for 1 Angstrom
                     1./boxDim[0], 1./boxDim[1], 1./boxDim[2]]
            for i in range(7, len(individual)):
                delta.append(0.1)
            
            nb = 0
            GAminimize = self.setting['GAminimize']
            while nb < len(pop):
                nind = makeIndividual(individual, delta)
                a, b, c = nind.toPhenotype()
                rmsd = rmsdcalc.computeRMSD(c)
                if rmsd <= 2.0:
                    score = nind.score()
                    mind = self.docking.search.minimize(nind, **GAminimize)
                    rmsd = rmsdcalc.computeRMSD(mind.phenotype[2])
                    if rmsd <= 2.0:
                        pop[nb] = mind
                        score = pop[nb].score()
                        print "\n", nb, rmsd
                        nb += 1
                else:
                    print rmsd,
            return pop

    
        # Calls the dock() function of docking search defined in the __init__ 
        def dock(self, initialPopulation=None):

            # start evolution

            self.docking.dock(initialPopulation)

            best = self.docking.search.getTopSolutions(cut=1.0)
            print 'Solutions:'

            ligname = os.path.split(self.setting['Ligand'])[1][:-6]
            recname = os.path.split(self.setting['Receptor'])[1][:-6]
            i = 0
            for ind, rmsds, rmsdsR, idx in best:
                # generate a recName if receptor is flexible                
                if self.setting.has_key("movingSC"):
                    recFilename = "%s_%s_job%s_flexrecsol_%d.pdbqt"%(
                        recname, ligname, self.setting['jobID'], i)
                #self.docking.xmlReader.molecules[0] is the ligand although not sure about [0]
                ligFilename = "%s_%s_job%s_sol_%d.pdbqt"%(
                    recname, ligname, self.setting['jobID'], i)

                # configure FT for this individuals and get score
                ind.score()
                scorer = self.docking.scoreObject
                if self.setting.has_key("movingSC"):
                    RecLigEnergy = scorer.scoreBreakdown['RRL']+scorer.scoreBreakdown['FRL']
		    RecRecEnergy = scorer.scoreBreakdown['RRFR']+scorer.scoreBreakdown['FRFR']
                else:
                    RecLigEnergy = scorer.scoreBreakdown['RRL']
		    RecRecEnergy = 0.0
                InternalLigEnergy = scorer.scoreBreakdown.get('LL', 999999999)
                from AutoDockFR.ScoringFunction import FE_coeff_tors_42
                tor = scorer.TORSDOF * FE_coeff_tors_42
                ene = RecLigEnergy + tor
                print 'FINAL SOLUTION: %3d FEB: %9.3f R-L: %9.3f L: %9.3f R-R: %9.3f Tor: %9.3f Score: %9.3f '%(
                    idx, ene, RecLigEnergy, InternalLigEnergy, RecRecEnergy, tor, -ind._fitness_score),
                for rmsd,rmsdR in zip(rmsds,rmsdsR):
                    print 'rmsdL: %5.2f rmsdR: %5.2f'%(rmsd,rmsdR),
                print ' filename: %s '%ligFilename
                
                print '  hist:',  ind.history
                print '      ', ind.values()

                ###scorer.printAllScoreTerms(ind)

                comments = []
                comments.append('*********************************************************')
                comments.append('Solution %d'%idx)
                comments.append('gene: ')#%s'%ind.values())
                nbginit = 0
                for motion in ind.motionObjs:
                    nbg = motion.nbGenes
                    comments.append("%s #%s,"%(ind.values()[nbginit:nbg+nbginit],motion.name))
                    nbginit = nbg+nbginit


                comments.append('FINAL SOLUTION: %3d FEB: %9.3f R-L: %9.3f L: %9.3f R-R: %9.3f Tor: %9.3f Score: %9.3f'%(
                    idx, ene, RecLigEnergy, InternalLigEnergy, RecRecEnergy, tor, -ind._fitness_score))

                line = 'rmsdsL: '
                for rmsd in rmsds:
                    line += " %6.2f"%rmsd
                line2 = 'rmsdsR: '
                for rmsd in rmsdsR:
                    line2 += " %6.2f"%rmsd

                comments.append(line)
                comments.append(line2)  
                comments.append('*********************************************************')

                a, b, newCoords = ind.phenotype#toPhenotype(sort=True)
                if self.setting.has_key("movingSC"):
                    self.docking.flexRecAtoms.updateCoords(b)
                    self.docking.receptor.parser.write_with_new_coords(
                        self.docking.receptor.allAtoms.coords, filename=recFilename, comments=comments,withBondsFor=self.docking.receptor)

                # assing coordinates from tree to ligand atoms ordered according to tree
                self.docking.sortedMovAts.updateCoords(newCoords)
            
                # write with ligand with newCoords sorted to match order in ligand file
                self.docking.ligand.parser.write_with_new_coords(
                    self.docking.ligand.allAtoms.coords, filename=ligFilename, comments=comments,withBondsFor=self.docking.ligand)
                if self.setting['scoringFunction'] != 'RMSD':
                    scorer.printAllScoreTerms(ind)
                i += 1

            # save final population
            ##self.docking.search.savePopulation( "Pop_%s_%s_job_%s_Final"%(
            ##    recname, ligname, self.setting['jobID']), self.docking.search.gen)
            
            return best



    class Docking:

        """ base class for protein-ligand docking"""
        def __init__(self, param):
            """ param is a AutoDockFR.Param object"""

            self.param = param
            self.setting = param.get()
            self.setLogFile()
            self._repeat = self.setting['repeat']
            printHeader()
            from FlexTree.XMLParser import ReadXML
            self.xmlReader = ReadXML()
            self.setRandomSeed()
	    self.pre_docking()


        def setRandomSeed(self):
            sd = self.setting['rand_seed']
            seed = random.seed
            t = type(sd)
            if sd == "time" or sd == -1:
                currentTime = time.time()
                seed(currentTime)
                print 'Using system time as random seed :',currentTime
            else:
                if (t == types.FloatType or t == types.IntType):
                    print 'Using ',sd,' as random seed '
                    seed(sd)
                else:
                    print "Warning: Wrong random seed", sd
                    print "Warning: Using system time as seed"
                    seed(time.time())


        def setLogFile(self):
            logfile = self.setting['log_file']
            if logfile != None:
                sys.stdout = file(logfile, 'wb')


        # configure the parameters
        def configure(self):
            pass

        def getSearchingParam(self):
            """ Obsolete !!!  returns GA related settings"""
            return self.setting.copy()


        def print_setting(self):
	    """
	    None <- print_setting()

	    Call to param.optList.__repr__().  
	    Prints a string with key,value from settings
	    """

            print repr(self.param.optList)


        def dock(self):
            print "This should never be called.. see derivative classes.."
            pass


        def checkSetting(self):
            """ make sure all the necessory settings are in place"""
            status = True
            for k in self.must_have_settings:
                if not self.setting.has_key(k):
                    print "Missing key:%s in the setting file %s"%\
                          (k,self.settingFileName)
                    status = False
                    raise ValueError
            return status


        def pre_docking(self):
	    """
	    None <- pre_docking()

            Prepare the receptor, prep the ligand, load the XML, 
            setup the search, & print thsettings
	    """

            self._prepareReceptor()
            self._prepareLigand()
            self._loadXML()
            self._setupSearch()
            self.print_setting()


        def _prepareReceptor(self):
            setting = self.setting
            # No .xml supplied in the settings file
            if not setting.has_key("ReceptorXML"):
                name = os.path.splitext(os.path.basename(setting['Receptor']))[0]
                ## generate XML file for receptor
                mol = Read(setting['Receptor'])[0]
                # MLD: bonds Needed to mask 1-1, 1-2, 1-3, 1-4 interactions
                # in ADCscorer.py ~> createRecRecScorer()
                if setting["ReceptorCONECT"]:
                    print "I Am HERE"
                    assert len(mol.allAtoms.bonds[0]) > len(mol.allAtoms), 'Bonds should be read from receptor input file'
                else:
                    mol.buildBondsByDistance()
                self.receptor = mol
                
                if not setting.has_key("movingSC"):  ## a rigid receptor
                    from AutoDockFR.utils import rigidReceptor2XML
                    #rigidReceptor2XML(setting['Receptor'], "%s.xml" % name)
                    ###self.tree = tree = rigidReceptor2XML(mol)
                    #self.rigidRecAtoms = self.tree.getRigidAtoms()
                    #self.flexRecAtoms = None
                    xmlbuilder = rigidReceptor2XML(mol)
                    xmlbuilder.writeXML("%s.xml"%name)
                    self.tree = tree = xmlbuilder.getTree()
                    setting['ReceptorXML'] = "%s.xml"%name
                    self.ReceptorTree = ReceptorTree =  tree
                    from MolKit.molecule import AtomSet
                    self.flexRecAtoms = AtomSet([])
                    self.interfaceAtoms = AtomSet([])
                    self.rigidRecAtoms = mol.allAtoms

                else:  ## with moving sidechains..
                    #from AutoDockFR.utils import RecXML4RotamSC
                    #xmlbuilder = RecXML4RotamSC(mol, setting["movingSC"])
                    from AutoDockFR.utils import RecXML4SoftRotamSC
                    xmlbuilder = RecXML4SoftRotamSC(mol, setting["movingSC"])
                    #xmlbuilder.writeXML("%s.xml"%name)
                    self.tree = tree = xmlbuilder.getTree()
                    setting['ReceptorXML'] = "%s.xml"%name
                    self.ReceptorTree = ReceptorTree =  tree
                    self.interfaceAtoms = xmlbuilder.interfaceAtoms
                    self.ReceptorTree.interfaceAtoms = xmlbuilder.interfaceAtoms
                    self.flexRecAtoms = self.tree.getMovingAtoms()
                    self.rigidRecAtoms = mol.allAtoms-(self.flexRecAtoms+self.interfaceAtoms)
                    
            else: # and XML file was provided
                self.xmlReader(setting['ReceptorXML'], True)
                self.tree = tree = self.xmlReader.get()[0]
                self.receptor = self.tree.mol
            
            # build BHTree of receptor atoms used to prune translations of individuals
            # FIXME use the BHTree to compute a distance field
            from bhtree import bhtreelib
            coords = self.rigidRecAtoms.coords
            self.receptorBht = bhtreelib.BHtree( coords, None, 10)
                                
            # load Receptor
            # MS Jun 2012 we no longer need the following lines
            # as the tree is returned by GenerateFT
            #self.root = root = tree.root
            #self.atmSet = root.getAtoms()
            #self.atmSet = self.tree.getRigidAtoms()+self.tree.getMovingAtoms()
            #self.ReceptorTree = ReceptorTree =  tree
            #if len(ReceptorTree.getMovingAtoms()) == 0:
            #    if setting['calcRecIE'] == True:
            #        setting['calcRecIE'] = False
            #        print "Error: a rigid receptor was found. "
            #        print "Please set -calcRecIE to be False"
            #        sys.exit(1)
            #    return
            self.root = root = tree.root
            self.ReceptorTree = ReceptorTree =  tree


        def _prepareLigand(self):
            """ prepare ligand related files"""
            setting = self.setting

            if not (self.setting['Ligand'].rsplit('.')[1] == 'xml'):
                filename = self.setting['Ligand']
                self.ligand = Read(filename)[0]
                assert hasattr(self.ligand, 'torTree')
                # we read the PDBQT in order to get the torsion tree build
                # MLD: bonds Needed to mask 1-1, 1-2, 1-3, 1-4 interactions
                # in ADCscorer.py ~> createLigLigScorer()
                # Ligand Internal Energy wasn't correct without this.
		self.ligand.buildBondsByDistance()
                
                self.ligandTorTree = self.ligand.torTree
                # Ligand torsion degrees of freedom - needed for 4.2 scoring
                if self.setting['gridMaps']:
                    from Volume.IO.AutoGridReader import ReadAutoGrid
                    reader = ReadAutoGrid()
                    mapName = self.setting['gridMaps'][0]
                    emap = reader.read(mapName, 0)
                    ox, oy, oz = emap.origin
                    sx, sy, sz =  emap.stepSize
                    nbptx, nbpty, nbptz = emap.data.shape
                    sizeX, sizeY, sizeZ = boxDim = ((nbptx-1)*sx, (nbpty-1)*sy, (nbptz-1)*sz)
                    cx = ox + (sizeX*.5)
                    cy = oy + (sizeY*.5)
                    cz = oz + (sizeZ*.5)

                    center = self.setting['box_center'] = (cx, cy, cz)
                    if self.setting['useXmlBox']:
                        dims = boxDim =self.setting['box_dimensions']
                        #added on 18thApr2014 to make the usexml box
                        #center the ligand root's center
                        refMolName = self.setting['rmsdRef'][0]
                        refMol = Read(refMolName)[0]
                        refMol.buildBondsByDistance()

                        center = self.setting['box_center'] = refMol.ROOT.coords
                    else:
                        dims = self.setting['box_dimensions'] = boxDim

                    #dims = self.setting['box_dimensions'] = boxDim
                    print "box_center", center
                    print "box_dimensions", dims
                else:
                    center = self.setting['box_center']
                    dims = self.setting['box_dimensions']
                    
		## # MLD: need a unique filename when runing repeat in the same folder
                import tempfile, os
                prefix = os.path.splitext(filename)[0]+"_"
                xmlFilename = tempfile.mkstemp(suffix=".xml", prefix=prefix,
                                               dir=os.getcwd())
                ## print 'Ligand xml', xmlFilename[1]
                ###xmlFilename = self.setting['Ligand'].rsplit('.')[0]+'.xml'
                pdbqt2XML(self.ligand, xmlFilename[1], center, dims)
                setting['LigandXML'] = xmlFilename[1]
                #xmlFilename = filename.split('.')[0]+".xml"
                #pdbqt2XML(filename, xmlFilename, center, dims)
                #setting['LigandXML'] = xmlFilename
            else:
                setting['LigandXML'] = self.setting['Ligand']
                self.ligand = None
                
            # load ligand
            self.xmlReader(setting['LigandXML'], True)
            self.LigandTree = LigTree = self.xmlReader.get()[0]
            self.ligRoot = ligRoot = LigTree.root
            self.ligandSet = ligandSet = ligRoot.getAtoms()

            if self.ligand is None:
                self.ligand = ligRoot.getAtoms()[0].top

            self.ligandFile = LigTree.pdbfilename

            self.TORSDOF = self.ligand.TORSDOF
            self.ligandTorTree = self.ligand.torTree

            #if not self.setting("LigandXML"):
                 # Remove the temporary ligand.xml file
            os.remove(xmlFilename[1])

            # _handleRigidBody() handle one rigid body at a time and need atom
            # indices of atoms in this rigid body, node.atomList provides a list
            # if indices but corresponding to the atom list in the molecule read
            # from the pdbqt files. We need a list of indices corresponding to
            # the order of the atoms in the ligand's Flexibility Tree
            #i = 0
            #for a,b in zip(self.ligand.allAtoms, self.ligandSet):
            #    print i, a.name, b.name
            #    i+=1
                
            ligandSetNames = self.ligandSet.name
            for a in self.ligand.allAtoms:
                a._FTindex = ligandSetNames.index(a.name)

            def _renumberTorTreeAtomsList(node, atoms):
                atomListFT = [atoms[i]._FTindex for i in node.atomList]
                node.atomList = atomListFT
                if node.bond[0] is not None:
                    node.bond = (atoms[node.bond[0]]._FTindex, 
                                 atoms[node.bond[1]]._FTindex)
                else:
                    node.bond = (None, None)

                #print '========================='
                #print node.atomList
                #print node.atomListFT
                for c in node.children:
                    _renumberTorTreeAtomsList(c, atoms)

            _renumberTorTreeAtomsList(self.ligand.torTree.rootNode,
                                      self.ligand.allAtoms)

            #import pdb
            #pdb.set_trace()



        def post_one_docking(self, number=0):
            """ 
	    run this function after each one_dock(),
	    overwrite it if necessary
	    """

            self.scoreObject.numEval = 0
            return
            ## # Retreive the best gene & its score
            ## vars, bestScore  = self.search.best()  
  
            ## print "\nINFO: best_gene=" + str(vars.values())
            ## print "\nINFO: best_score = %f" % bestScore
            ## print " ***  evolution finished at ", time.ctime(), "  ***"
            ## print "\nINFO: number_evaluation="+ str(self.scoreObject.numEval)
            ## print "-----------------\n"
            
            ##from AutoDockFR.utils import getRMSD, saveAutoDockFRPrediction
	    ## #import pdb
	    ## #pdb.set_trace()
            ## # Transform the gene into x,y,z coords
            ## RR_coords, FR_Coords, L_coords = vars.phenotype#, sort = True)

            ## if self.setting['rmsdRef']:
            ##     # Returns a list, only want the lowest RMSD
            ##     rmsd = getRMSD(self.setting,self.search, [L_coords], origAtomSet = self.ligRoot.getAtoms())[0]
            ##     print "INFO: best_RMSD =", rmsd
            ## print ""
	    ## #import pdb
	    ## #pdb.set_trace()
            ## # Check the score of the best gene, print scoring breakdown
            ## self.validateScore(vars)

            ## ## save the prediction to files
            ## prefix = self.setting['out']
	    ###prefix = "Final"
            ##if prefix != None:
            ##     recName = '%s_rec_%d'%(prefix, number)
            ##     ligName = '%s_lig_%d'%(prefix, number)
            ## else:
            ##     recName = 'rec_%d'%(number)
            ##     ligName = 'lig_%d'%(number)
                 
            ## saveAutoDockFRPrediction(vars, self.setting, self.scoreObject,
            ##                          R_tree = self.ReceptorTree,
            ##                          L_tree = self.LigandTree, 
            ##                          recName = recName, ligName = ligName)
            ## return
                

        def _loadXML(self):

            return

        def _setupSearch(self):
            setting = self.setting
            ##
            ## build objects used for RMSD calculations
            ##
            from AutoDockFR.symmetricRMSD import RMSDwithSymmetry, \
                 RMSDwithAutomosphisms
            from mglutil.math.rmsd import RMSDCalculator, HungarianMatchingRMSD, getAtomIndicesPerType
            from MolKit import Read

            # build RMSD calculators for reference ligand molecule
            rmsdCalculators = []
            for refMolName in self.setting['rmsdRef']:
                refMol = Read(refMolName)[0]
                refMol.buildBondsByDistance()
                sortedRefAts = orderRefMolAtoms(refMol.allAtoms, self.ligandSet)
                if self.setting['rmsdSym']:
                    symmDescr = self.setting['rmsdSym']
                    if isinstance(symmDescr, list):
                        assert len({}.fromkeys(self.ligandSet.name))==len(self.ligandSet), \
                               "ligand atom names are not unique, Automorphisms will not map properly"
                        lengths = [len(x) for x in symmDescr]
                        if min(lengths)==len(self.ligand.allAtoms) and max(lengths)==len(self.ligand.allAtoms):
                            RMSDcalc = RMSDwithAutomosphisms(sortedRefAts, self.setting['rmsdSym'])
                            rmsdCalculators.append( RMSDcalc )
                        else:
                            RMSDcalc = RMSDwithSymmetry(sortedRefAts, self.setting['rmsdSym'])
                            rmsdCalculators.append( RMSDcalc )
                    else:
                        if self.setting['rmsdSym']=='HungarianMatching':
                            d1 = getAtomIndicesPerType(sortedRefAts)
                            RMSDcalc = HungarianMatchingRMSD(sortedRefAts, d1, d1)
                            rmsdCalculators.append( RMSDcalc )
                        else:
                            RMSDcalc = RMSDwithSymmetry(sortedRefAts, self.setting['rmsdSym'])
                            rmsdCalculators.append( RMSDcalc )
                else:
                    RMSDcalc = RMSDCalculator(refCoords=sortedRefAts.coords)
                    rmsdCalculators.append( RMSDcalc )
            rmsdCalculators1 = rmsdCalculators

            # build RMSD calculators for reference moving receptor
            rmsdCalculators = []
            for refMolName in self.setting['rmsdRecRef']:
                refMol = Read(refMolName)[0]
                refMol.buildBondsByDistance()
                if len(self.flexRecAtoms)==0: # self.flexRecAtom is empty when we fix the maps
                    self.flexRecAtom = refMol.allAtoms
                    sortedRefAts = refMol.allAtoms
                else:
                    sortedRefAts = orderRefMolAtoms(refMol.allAtoms, self.flexRecAtoms)
                self.sortedRecRefAts = sortedRefAts
                if self.setting['rmsdSym']:
                    symmDescr = self.setting['rmsdSym']
                    if isinstance(symmDescr, list):
                        raise 'NOT implemented yet' # automorphism
                        assert len({}.fromkeys(self.flexRecAtoms.name))==len(self.flexRecAtoms), \
                               "ligand atom names are not unique, Automorphisms will not map properly"
                        lengths = [len(x) for x in symmDescr]
                        if min(lengths)==len(self.flexRecAtoms.allAtoms) and max(lengths)==len(self.ligand.allAtoms):
                            RMSDcalc = RMSDwithAutomosphisms(sortedRefAts, self.setting['rmsdSym'])
                            rmsdCalculators.append( RMSDcalc )
                        else:
                            RMSDcalc = RMSDwithSymmetry(sortedRefAts, self.setting['rmsdSym'])
                            rmsdCalculators.append( RMSDcalc )
                    else:
                        if self.setting['rmsdSym']=='HungarianMatching':
                            d1 = getAtomIndicesPerType(sortedRefAts)
                            RMSDcalc = HungarianMatchingRMSD(sortedRefAts, d1, d1)
                            rmsdCalculators.append( RMSDcalc )
                        else:
                            RMSDcalc = RMSDwithSymmetry(sortedRefAts, self.setting['rmsdSym'])
                            rmsdCalculators.append( RMSDcalc )
                else:
                    RMSDcalc = RMSDCalculator(refCoords=sortedRefAts.coords)
                    rmsdCalculators.append( RMSDcalc )

            rmsdCalculators2 = rmsdCalculators

            # sortedMovAts is used in GA to compute RMSD of best solutions
            # and to save pdbqs.This uses self.ligand.allAtoms
            # call self.sortedMovAts.updateCoords(L_coords) to update coords
            # then RMSDcalc.computeRMSD(L_coords)
            self.sortedMovAts = orderRefMolAtoms(
                self.ligand.allAtoms, self.ligandSet)

            # build RMSD calculator for clustering population
            # read the ligand again to have a distinct set of atom
            if self.setting['rmsdSym']:
                symmDescr = self.setting['rmsdSym']
                if isinstance(symmDescr, list):
                    lengths = [len(x) for x in symmDescr]
                    if min(lengths)==len(self.ligand.allAtoms) and max(lengths)==len(self.ligand.allAtoms):
                        RMSDcalc = RMSDwithAutomosphisms(self.sortedMovAts, self.setting['rmsdSym'])
                        rmsdCalc0 = RMSDcalc
                    else:
                        RMSDcalc = RMSDwithSymmetry(self.sortedMovAts, self.setting['rmsdSym'])
                        rmsdCalc0 = RMSDcalc
                else:
                    if self.setting['rmsdSym']=='HungarianMatching':
                        d1 = getAtomIndicesPerType(self.sortedMovAts)
                        RMSDcalc = HungarianMatchingRMSD(self.sortedMovAts, d1, d1)
                        rmsdCalc0 = RMSDcalc
                    else:
                        RMSDcalc = RMSDwithSymmetry(self.sortedMovAts, self.setting['rmsdSym'])
                        rmsdCalc0 = RMSDcalc
            else:
                RMSDcalc = RMSDCalculator(refCoords=self.sortedMovAts.coords)
                rmsdCalc0 = RMSDcalc



            from AutoDockFR.FTGA import FTtreeGaRepr
            
            # Create an instance of the scoring function
            gscorer=None
            if self.setting['scoringFunction'] == 'AutoDock4.2': 
                if setting['gridMaps'] is not None:
                    from AutoDockFR.gridScorer import GridScorer
                    #gscorer = GridScorer(self.ligandSet, setting['gridMaps'])
                    gscorer = GridScorer(setting['gridMaps'])
                    gscorer.addAtomSet(self.ligandSet, 'RRL')
                    if len(self.flexRecAtoms):
                        gscorer.addAtomSet(self.flexRecAtoms, 'RRFR')
                
                for refMolName in self.setting['rmsdRecRef']:
                    # temporarily set flexRecAtoms coordinates to Xtal coordinates
                    # so that C scorer build correct bonds
                    flexRecCoords = self.flexRecAtoms.coords
                    self.flexRecAtoms.coords = self.sortedRecRefAts.coords

    
		from AutoDockFR.ADCscorer import AD42ScoreC
                scoreObject = AD42ScoreC(
                    rigidRecAtoms=self.rigidRecAtoms, 
                    ligAtoms=self.ligandSet,
                    ligandTorTree=self.ligandTorTree, 
                    TORSDOF=self.TORSDOF, 
                    flexRecAtoms=self.flexRecAtoms,
                    interfaceAtoms=self.interfaceAtoms,
                    RR_L=setting['RR_L'],
                    FR_L=setting['FR_L'],
                    L_L=setting['L_L'],
                    RR_RR=setting['RR_RR'],
                    RR_FR=setting['RR_FR'],
                    FR_FR=setting['FR_FR'],
                    RR_L_Fitness=setting['RR_L_Fitness'],
                    FR_L_Fitness=setting['FR_L_Fitness'],
                    L_L_Fitness=setting['L_L_Fitness'],
                    RR_RR_Fitness=setting['RR_RR_Fitness'],
                    RR_FR_Fitness=setting['RR_FR_Fitness'],
                    FR_FR_Fitness=setting['FR_FR_Fitness'],
                    gridScorer=gscorer
                    )
		
                # restore flexRecAtomCoords of randomized receptor
                if self.setting.has_key("movingSC"):
                    self.flexRecAtoms.coords = flexRecCoords
                else:
                    from MolKit.molecule import AtomSet
                    self.flexRecAtoms = AtomSet([])

			  
            elif self.setting['scoringFunction'] == 'RMSD':
                from MolKit import Read
                refLigMol = Read(self.setting['rmsdScorerTargetLigMol'])[0]
                sortedRefLigAts = orderRefMolAtoms(refLigMol.allAtoms, self.ligandSet)

                if self.setting['rmsdScorerTargetRecMol'] != '':
                    refRecMol = Read(self.setting['rmsdScorerTargetRecMol'])[0]
                    sortedRefRecAts = orderRefMolAtoms(refRecMol.allAtoms, self.flexRecAtoms)
                    flexRecRefCoords = sortedRefRecAts.coords
                else:
                    flexRecRefCoords = None

                from AutoDockFR.RMSDScorer import RMSDScorer
                scoreObject = RMSDScorer(sortedRefLigAts.coords, flexRecRefCoords)
					  
            elif self.setting['scoringFunction'] == 'USRscore':
                from AutoDockFR.USRscorer import USRscore
                scoreObject = USRscore(self.ligandSet, self.atmSet)

            elif self.setting['scoringFunction'] == 'PLP':
                from AutoDockFR.PLPscorer import PLPScoring
                scoreObject = PLPScoring(self.atmSet, self.ligandSet)
            else:
                print "Unknown scoring functions:", \
                      self.setting['scoringFunction']
                raise

            self.scoreObject = scoreObject
            # Reads the FTtree info stored in Receprtor/LigandTree and creates
            # a GA representation (template of a gene)
            self.gnm = gnm = FTtreeGaRepr(self.ReceptorTree, self.LigandTree,
                                          scoreObject, optFEB=setting['GA_optFEB'])
            print "Number of genes:", gnm.totalGeneNum

            if gscorer:
                gscorer.fixTranslation(self)
                
            # set torsions of flexible side chains to 0
            # this is done here AFTER the C scorer has been built to avoid
            # spurious bonds to be created when the geometry of the side chain
            # is not bad
            # DOES NOT WORK we should randomize flexible side cahins outside
            # ADFR to avoid questions about bias

            ## R_MotionObjs = self.ReceptorTree.getAllMotion()
            ## from FlexTree.FTMotions import FTMotion_SoftRotamer
            ## for m in R_MotionObjs:
            ##     if isinstance(m, FTMotion_SoftRotamer):
            ##         m.rotamer.zeroTorsion()


            L_MotionObjs = self.LigandTree.getAllMotion()
            from AutoDockFR.FTGA import GAFTMotion_RotationAboutPointQuat, \
                 GAFTMotion_BoxTranslation, GAFTMotion_RotationAboutAxis
            from FlexTree.FTMotions import FTMotionCombiner
            for m in L_MotionObjs:
                if isinstance(m, GAFTMotion_RotationAboutPointQuat):
                    if self.setting['fixedLigandRotation']:
                        m.active = False
                elif isinstance(m, GAFTMotion_BoxTranslation):
                    if self.setting['fixedLigandTranslation']:
                        m.active = False
                elif isinstance(m, GAFTMotion_RotationAboutAxis):
                    if self.setting['fixedLigandConformation']:
                        m.active = False
                elif isinstance(m, FTMotionCombiner):
                    if self.setting['fixedLigandMotionCombiner']:
                        m.active = False

                    
            #import pdb
            #pdb.set_trace()

            if self.setting['GA_pop_size']=='auto':
                #tmpNoVar=(7+self.TORSDOF+(gnm.totalGeneNum-7-self.TORSDOF)/4)
                #self.setting['GA_pop_size'] = (50 + 10*tmpNoVar)#gnm.totalGeneNum)
                self.setting['GA_pop_size'] = 2*(50 + 10*gnm.totalGeneNum)
                print "Population size:", self.setting['GA_pop_size']

            ###if gscorer:
            ###    gscorer.fixTranslation(self)
                #gscorer.initReallyGoodPop(self)
                
            # Creates a population of genes (template of a population)
            #import pdb
            #pdb.set_trace()
            self.pop = pop = Population(self.gnm)
            ## self.pop = pop = Population(self.gnm, size=self.setting['GA_pop_size'])
            ## for ind in pop:
            ##    ind.randomize()
            ##     ind.initialize(self.setting)

            ## pop.initialize()
            ## pop.evaluate()
            ## pop.scale()
            ## pop.sort()

            ## # Update the population stats dictionary
            ## pop.update_stats()
            ## pop.stats['initial']['avg'] = pop.stats['current']['avg']
            ## pop.stats['initial']['max'] = pop.stats['current']['max']
            ## pop.stats['initial']['min'] = pop.stats['current']['min']
            ## pop.stats['initial']['dev'] = pop.stats['current']['dev']

            ##
            # Instance of GA class (passed template of population)
            if self.setting['search'] == 'GA':
                self.search = galg = GA(pop, self.setting)
            elif self.setting['search'] == 'GA1':
                self.search = galg = GA1(pop, self.setting)
            elif self.setting['search'] == 'GA2':
                self.search = galg = GA2(pop, self.setting)
            elif self.setting['search'] == 'GA2_1':
                self.search = galg = GA2_1(pop, self.setting)
            elif self.setting['search'] == 'GA2_2':
                self.search = galg = GA2_2(pop, self.setting)
            elif self.setting['search'] == 'GA3':
                self.search = galg = GA3(pop, self.setting)
            elif self.setting['search'] == 'GA4':
                self.search = galg = GA4(pop, self.setting)
            elif self.setting['search'] == 'GA5':
                self.search = galg = GA5(pop, self.setting)
            elif self.setting['search'] == 'GA6':
                self.search = galg = GA6(pop, self.setting)

            if self.setting['GA_enableLocalSearch'] or self.setting['AnnealSteps'] > 0:
                print "Local search enabled"
                kw = {
                    'search_rate' :  self.setting.get('GA_localsearchrate', 0.3),
                    'MAX_FAIL' : self.setting.get('GA_localSearchMaxFail', 4),
                    'MAX_SUCCESS' : self.setting.get('GA_localSearchMaxSuccess', 4),
                    'MIN_VAR' : self.setting.get('GA_localSearchMinVar', 0.01),
                    'FACTOR_EXPANSION' : self.setting.get('GA_localSearchFactorExpansion', 2.0),
                    'FACTOR_CONTRACTION' : self.setting.get('GA_localSearchFactorContraction', 0.5),
                    'max_steps' : self.setting.get('GA_localSearchMaxIts', 500)
                    }
                # Instance of  SolisWet class
                self.search.localSearch = SolisWet(**kw)
                # If local Search is enabled, create an instance of FlipCoin 
                # (random number sequence independent from other random # calls)
                self.search.localSearchFlipCoin = FlipCoin(self.setting['rand_seed'])
            else:
                self.search.localSearch = None

            self.search.rmsdCalculators = rmsdCalculators1
            self.search.rmsdCalculatorsRec = rmsdCalculators2
            self.search.rmsdCalc = rmsdCalc0
 
            # add scoreObject to GA so that in evolve we can check numEvals
            galg.scoreObject = self.scoreObject
            galg.receptorBht = self.receptorBht

            # set original anchor atom coords and box translation
            # use to eliminate bad translation individuals
            boxTrans = self.ligRoot.motion.motionList[1]
            fixTrans = self.ligRoot.motion.motionList[2]
            galg.origAnchor = fixTrans.point1
            # FIXME  the offset of the translation could be different
            galg.transOff = 4
            galg.boxTrans = boxTrans
            galg.ligRoot = self.ligRoot
            galg.docking = self
            
            # Max number of evals set, sets a Callback
            if 'GA_max_eval' in setting.keys(): 
                from mglutil.util.callback import CallBackFunction
                cb = CallBackFunction(self.max_evaluation_cb)
                galg.addCallback('postGeneration', cb)
                self.max_evaluation = setting['GA_max_eval']            



        def max_evaluation_cb(self):
	    """
	    None or 'end' <- max_evaluation_cb()

            This function will determine if the scoreObject.numEval 
            > max_evaluation set in the settings file.  Returns none if 
            scoreOject.numEval < max_evaluation & 'end' if scoreOject.numEval 
            > max_evaluation.  'end' is useful in GA.py where
            this keyword causes the callback to end the GA. 
	    """
            ## this function is called after every generation.
            #t = time.time()-self.search.beginTime
            #n = self.scoreObject.numEval
            #print "Evals = %d, elapsed time: %7.2f secs, %7.2f sec per eval"\
            #      %(n,t, t/n)
            galg = self.search
            if self.scoreObject.numEval > self.max_evaluation:
                galg.gen = galg.settings['GA_gens']  # hack to stop GA running
                return 'end'
            else:
                return 


        def saveOneResult(self, ind, ligFilename, recFilename=None):
            from AutoDockFR.utils import saveAutoDockFRPrediction
            RR_coords, FR_Coords, L_coords = ind.toPhenotype()
            saveAutoDockFRPrediction(
                ind, self.setting, self.scoreObject,
                R_tree = self.ReceptorTree,
                L_tree = self.LigandTree, 
                recName=recFilename, ligName=ligFilename)
            

        def _printSetting(self, settingDict):

	    print settingDict
            for k,v in settingDict.items():
                print k, '=',v
            return



    ## end of Docking class

    ## start of Dock_Serial class
    class Dock_Serial(Docking):
        """ serial (one processer) docking """

        def one_docking(self, initialPopulation=None):
            searchingParam = self.setting.copy()
            galg = self.search
            # Update the default GA settings with ones defined in settings
            galg.updateSetting(searchingParam)
            # Evolve the Genetic Algorithm
            galg.evolve(initialPopulation)
            return


        def dock(self, initialPopulation=None):
            # Prepare receptor, prep ligand, load XML, setup search, print settings
            #self.pre_docking()    
            # Multiple Docking runs
            for i in range(1, self._repeat+1):
                print "Docking test #", i
                print "Docking begins at:", time.ctime() , "\n"
                beginTime = time.time()
                self.search.startTime = beginTime
                self.one_docking(initialPopulation)
                print " ***  docking takes %10.2f minutes"%\
                      ((time.time()-beginTime)/60.)
                print ""
                self.post_one_docking(i)
            return
	

        def validateScore(self, best):
            # Take the best gene, create coords, score it
	    ##import pdb
	    ##pdb.set_trace()
            bestScore = best._fitness_score
            TotalScore = best.score() # computes coordinates from genome
                                      # configures scorers with coordinates
            assert bestScore==TotalScore
            # If the difference between the score and the "stored best_score" is > 1e-4          
            if abs(TotalScore-self.search.db_entry['best_scores'][-1]) > 1e-4:
                print "Error : best gene does not point to best score !"
                print "best_gene: %s    db_entry_best_score: %s\n" % (TotalScore, self.search.db_entry['best_scores'][-1])
                print
                for gene in self.search.pop:
                    TotalScore = gene.score() #self.scoreObject.score(gene)
                    #print gene
                    ##print "==>", TotalScore
                ##raise
                ##sys.exit(1)
                self.scoreObject.printAllScoreTerms(best)
            else:
                # Print the scoring terms broken down
                self.scoreObject.printAllScoreTerms(best)

    ## end of Dock_Serial class


    ## start of Dock_DivideAndConquer class    
    class Dock_DivideAndConquer(Dock_Serial):
        """ Divide the docking box into smaller boxes """

        def configure(self, debug = 0):
            """
            debug: debugging level
                    0: no debugging
                    1: output best gene of each smaller boxes
                    2: ...
            """
            if debug is not None:
                self.debug = debug
            return

        
        def _setupSearch(self):
            boxTranslation = self.LigandTree.root.motion.motionList[1]
            boxTranslation.divide_and_conquar = True
            Dock_Serial._setupSearch(self)
            self.bloodBank = Population(self.gnm)
        
        def checkSetting(self):
	    """ make sure all the necessory settings are in place"""
            self.must_have_settings.extend(['x_div', 'y_div', 'z_div', \
                                            'box_pop_size',
                                            'box_p_replace',
                                            'box_p_cross', 
                                            'box_mutation_rate',
                                            'box_gens', 
                                            'box_p_mutate',
                                            'box_p_deviation', 
                                            ])
            status = Docking.checkSetting(self)

            for k in self.must_have_settings:
                if not self.setting.has_key(k):
                    print "Cannot find the setting of %s in the file %s"%\
                          (k,self.settingFileName)
                    status = False
            return status

        def getGASetting(self):
            ### returns GA related settings for docking in small box ###
            ga_setting = {}
            ga_keys = ['DAC_box_pop_size','DAC_box_p_replace','DAC_box_p_cross','DAC_box_mutation_rate','DAC_box_gens',\
                     'DAC_box_p_deviation','DAC_box_enableLocalSearch','DAC_box_localsearchrate','DAC_box_max_evaluation']

            keys = self.setting.keys()
            for k in ga_keys:               
                if k == 'DAC_box_pop_size':
                    # if pop_size = '10X'
                    v = self.setting[k]
                    if type(v) is types.StringType:
                        v = string.upper(v)
                        tmp = v.split('X')
                        if len(tmp)<2:
                            raise ValueError
                        factor = eval(tmp[0])
                        self.setting[k] = factor * self.gnm.totalGeneNum
                if k == 'DAC_box_enableLocalSearch' and self.setting['DAC_box_enableLocalSearch'] == True:
                    # add the localSearch Parameters to the dictionary
		    ga_setting['GA_localSearchMaxSuccess']        = 4.0
		    ga_setting['GA_localSearchMaxFail']           = 4.0
		    ga_setting['GA_localSearchFactorExpansion']   = 2.0
		    ga_setting['GA_localSearchFactorContraction'] = 0.5
		    ga_setting['GA_localSearchMaxIts']            = 0.1
		    ga_setting['GA_localSearchMinVar']            = 0.01
		    ga_setting['GA_localSearchRho']               = 0.1

                key = k.split('DAC_box_')[1]        
                ga_setting["GA_"+key] = self.setting[k]
                

            #raise
            return ga_setting
        #""" 


        def one_docking(self):
            LigandTree = self.LigandTree

            # Reads the variable to divide the docking box by
            searchingParam = self.setting.copy()
            x_div = self.setting['DAC_x_div']
            y_div = self.setting['DAC_y_div']
            z_div = self.setting['DAC_z_div']

            import numpy as N
            from AutoDockFR.utils import divideAndConquer,updateDockingBoxInfo,locateDockingBoxInfo

            originalCenter, originalDim = locateDockingBoxInfo(LigandTree)
            if originalCenter is None:
                print "Error: class Dock_DivideAndConquer:one_docking can not read the box center"
                raise ValueError

            originalCenter = N.array(originalCenter, 'f')
            originalDim = N.array(originalDim, 'f')

            ### Will divide the docking box into smaller boxes.  X-dimension divided into x_div segments, Y-dimension divided into y_div segments, 
            ### Z-dimension divided into z_div segments. x_div * y_div * z_div boxes will be generated. returns a list of box centers:
	    ### e.g:  [[0,0,0],[0,0,3],[0,1,3],...,[3,3,3]]. 
            ### MLD: Note if you take default for x_div = 1 you get the same box back.  3A/1A = 3A still."""
            centers, newDim = divideAndConquer(LigandTree, x_div, y_div, z_div)
            if centers is None:
                raise ValueError
                sys.exit(1)

            idx = 0
            totalBoxNum = x_div*y_div*z_div
            galg = self.search
            gnm = self.gnm

            GA_settings = self.getGASetting()

            # save good genes here
            self.bloodBank.initialize(searchingParam)
            del self.bloodBank[0]  # remove the first (and only ) genome
            #print "Setting of GA searching in small boxes:"
            #self._printSetting(GA_settings)

            # Run Docking in each sub-box of the docking search space
            for center in centers:
                idx += 1
                # clear the flag of ligand translation
                #self.boxTranslation.ligand_translation = None 
                updateDockingBoxInfo(LigandTree, center, newDim)

                # Update the GA default settings 
                galg.updateSetting(GA_settings)
                print "*** docking box # %d of %d :"%(idx, totalBoxNum)
                print "    center at %s"%(str(center))

                ## reset the number of evaluations
                self.scoreObject.numEval = 0
                #raise
                galg.evolve()

                best = galg.pop.best()    
##                 print "\nBest Gene of last generation: "
##                 print best
                bestScore = -1*max(galg.db_entry['best_scores'])
                print "Best Score:",bestScore
                print "-----------------\n"

                ## convert genes from smaller box into new form,as in overall docking box
		tr = N.array([x.value() for x in best[gnm.box_start : gnm.box_end]])
                assert len(tr) == 3
                c = N.array(center,'f')
                d = N.array(newDim,'f')
                # pointInOrigBox are three float, from 0.0 to 1.0
                pointInOrigBox = (c-originalCenter+(tr-0.5)*d)/originalDim+0.5
                pointInOrigBox = pointInOrigBox.tolist()

                # make sure the values are between 0.0 and 1.0
                # sometimes, 1.0 is written as 1.0000000170809082..  !!
                for i in range(len(pointInOrigBox)):
                    if pointInOrigBox[i] > 1.0:
                        pointInOrigBox[i] = 1.0
                    elif pointInOrigBox[i] < 0.0:
                        pointInOrigBox[i] = 0.0

                tmpGenome = best.clone()
                for i in range(gnm.box_start,gnm.box_end):
                    tmpGenome.data[i].set_value(pointInOrigBox[i-gnm.box_start])
                self.bloodBank.append(tmpGenome)
                print "INFO_BOX: best_gene=", tmpGenome
                print
                
##                 print "\nINFO--2: number_evaluation="+ \
##                       str(self.scoreObject.numEval)
##                 print "Updated genes are"
##                 print tmpGenome
##                 print 

            self.scoreObject.numEval = 0                
            ## Now run GA again with "seeds" from different smaller boxes
            print " ***  start searching with 'seeds' from smaller boxes ***"
            updateDockingBoxInfo(LigandTree, originalCenter, originalDim) 

            setting = Dock_Serial.getSearchingParam(self)
            galg.settings = copy.copy(galg.default_settings)

            # if pop_size is small, we only take the best genes
            if setting['GA_pop_size'] < len(self.bloodBank):
                self.bloodBank.sort() # by score
                del self.bloodBank[setting['GA_pop_size']:]
            galg.updateSetting(setting)
            #print "Setting of GA searching:"
            #self._printSetting(setting)
            galg.evolve(init_Population = self.bloodBank.data)
            return


    ## start of Dock_RMSD class    
    class Dock_RMSD(Dock_Serial):
        """ Dock_RMSD docking class takes a flexible ligand and try to optimize
the variables in order to fit the conformation to a target conformation."""
        def __init__(self, settingFile = None, repeat = None):
            self.setting = {}
            self.must_have_settings = ['p_replace', 'p_cross', 'p_deviation',\
                                     'gens', 'rand_seed', 'p_mutate',
                                     'rand_alg', 'mutation_rate',
                                     'scorerVersion', 'pop_size',
                                     'XML_file', 'reference','superimpose',
                                     'mobAtomStr','refAtomStr'] 
            self.settingFileName = settingFile
            printHeader()
            self._repeat = 1
            self._parseSettingFile(filename = settingFile)
            if repeat != None:
                self._repeat = repeat
            return

        def _loadXML(self):
            setting = self.setting
            from FlexTree.XMLParser import ReadXML
            reader = ReadXML()
            # load ligand
            reader(setting['XML_file'], True)
            self.LigTree = LigTree = reader.get()
            self.ligRoot = ligRoot = LigTree[0].root
            self.ligandSet = ligandSet = ligRoot.getAtoms()
            self.ligandFile = LigTree.pdbfilename
            self.LigandTree = LigandTree = LigTree[0]
            self.ligandSet.sort()

            # load reference conformation
            from MolKit import Read
            self.refAtoms = Read(setting['reference'])[0].allAtoms
            self.refAtoms.sort()
            return


        def _setupSearch(self):
            setting = self.setting
            from AutoDockFR.FTGA import FTtreeGaRepr, OneFT_GaRepr
            from AutoDockFR.RMSDscorer import RMSDScoring
            scoreObject = RMSDScoring(mobAtomset = self.ligandSet,
                                      refAtomset = self.refAtoms,
                                      mobAtomStr = setting['mobAtomStr'],
                                      refAtomStr = setting['refAtomStr'],
                                      superimpose = setting['superimpose'] )
            self.scoreObject = scoreObject
            self.gnm = gnm = OneFT_GaRepr(self.LigandTree,\
                                      scoreObject)
            print "Number of genes:", gnm.totalGeneNum

            self.pop = pop = Population(self.gnm)
            self.search = galg = GA(pop)
            if 'GA_max_eval' in setting['searchingParams'].keys(): 
                from mglutil.util.callback import CallBackFunction
                cb = CallBackFunction(self.max_evaluation_cb)
                galg.addCallback('postGeneration', cb)
                self.max_evaluation = setting['searchingParams']\
                                     ['GA_max_eval']
            if 'stop_score' in setting.keys():
                galg.settings['stop_score'] = setting['stop_score']
            return

        def validateScore(self,best):
            """ does nothing.."""
            pass

        def post_one_docking(self):
            """ overwrite the default post_one_docking. """
            return
 

    
    ######
    # Particle Swarm Optimization based docking
    class PSO_Docking(Dock_Serial):
        """ base class for protein-ligand docking"""
        def __init__(self, param):
            Dock_Serial.__init__(self, param)
            #self.must_have_settings = ['xmax', 'xmin', 'enable_local_search', 'ls_max_steps', 'neighborhood_szie', 'number_of_particles', 'w_max', 'w_min', 'freq']
            self.must_have_settings = []
            return
            
        # configure the docking
        def configure(self):
            pass


        def _parseSettingFile(self, filename):
            if filename:
                setting = self.setting
                try:
                    input_file = file(filename, 'r')
                    lines = input_file.readlines()
                    for line in lines:
                        if line[0] != '#' and line[0] != '\n':
                            line = line.replace(' ', '') 
                            tmp = line.split('\n')[0].split('=')
                            if tmp[1][0] !='\'': # number setting
                                setting[tmp[0]] = eval(tmp[1])
                            else: # string setting
                                strSetting = tmp[1].replace('\'', '') 
                                setting[tmp[0]] = strSetting
                    print "\nINFO: setting_file="+ filename , "\n"
                except:
                    print
                    print "Error in opening ",filename
                    print
                    sys.exit(1)

                if setting.has_key('repeat'):
                    self._repeat = setting['repeat']
            else:
                # load default setting ?
                pass



        def pre_docking(self):
            self._prepareReceptor()
            self._prepareLigand()
            #self._loadXML()
            self._setupSearch()
            self.print_setting()

            


        def _loadXML(self):
            setting = self.setting
            from FlexTree.XMLParser import ReadXML
            reader = ReadXML()

            # load Receptor
            reader(setting['ReceptorXML'], True)
            self.tree = tree = reader.get()
            self.root = root = tree[0].root
            self.atmSet = root.getAtoms()
            self.ReceptorTree = ReceptorTree = tree[0]

            # load ligand
            reader(setting['LigandXML'], True)
            self.LigTree = LigTree = reader.get()
            self.ligRoot = ligRoot = LigTree[0].root
            self.ligandSet = ligandSet = ligRoot.getAtoms()
            self.LigandTree = LigandTree = LigTree[0]

        def _setupSearch(self):
            setting = self.setting
            from AutoDockFR.FTGA import FTtreeGaRepr, OneFT_GaRepr
            from AutoDockFR.ADCscorer import AD42ScoreC
            scoreObject = AD42ScoreC(self.atmSet, self.ligandSet,
                                      setting['calcLigIE'],
                                      setting['calcRecIE'],
                                      self.ReceptorTree)
            self.scoreObject = scoreObject
            self.gnm = gnm = FTtreeGaRepr(self.ReceptorTree, 
				self.LigandTree, scoreObject, optFEB=setting['GA_optFEB'])
            print "Number of genes:", gnm.totalGeneNum

            #self.pop = pop = Population(self.gnm)

            self.search = PSO(scoreObject, gnm, \
		neval_max = self.setting['PSO_max_eval'],
		enable_local_search = self.setting['PSO_enableLocalSearch'],
		ls_max_steps = 3, 
		neighborhood_size = self.setting['PSO_neighbor'],
		number_of_particles = self.setting['PSO_pop_size'],
		w_max = 0.9, w_min = 0.4, freq = 100,
		max_gens = self.setting['PSO_gens'],
		mutation_rate = self.setting['PSO_mutation'],
		seed = self.setting['rand_seed'])
            #raise
##             if 'PSO_max_eval' in setting.keys():                
##                 from mglutil.util.callback import CallBackFunction
##                 cb = CallBackFunction(self.max_evaluation_cb)
##                 galg.addCallback('postGeneration', cb)
##                 self.max_evaluation = setting['PSO_max_eval']
            return


        def one_docking(self):           
            self.search.go()
            return



        def max_evaluation_cb(self):
            ## this function is called after every generation.
            #t = time.time()-self.search.beginTime
            #n = self.scoreObject.numEval
            #print "Evals = %d, elapsed time: %7.2f secs, %7.2f sec per eval"\
            #      %(n,t, t/n)
            if self.scoreObject.numEval >self.max_evaluation:
                galg.gen = galg.settings['gens']  # hack to stop GA running
                return 'end'
            else:
                return None

        def _printSetting(self, settingDict):
            for k,v in settingDict.items():
                print k, '=',v




    ######
    # USR
    class Shape_Docking(Docking):
        """ Dock a ligand into a <shape> """
        
        def pre_docking(self):
            self._prepareShape()
            self._prepareLigand()
            self._loadXML()
            self._setupSearch()
            self.print_setting()

        def _prepareShape(self):
            setting = self.setting
            from MolKit import Read
            self.atmSet = Read(setting['Receptor'])[0].allAtoms
            return

        def dock(self):
            self.pre_docking()                        
            for i in range(1, self._repeat+1):
                print "Docking test #", i
                print "Docking begins at:", time.ctime() , "\n"
                beginTime = time.time()
                self.one_docking()
                best = self.search.pop.best()    
                #print "\nBest Gene of last generation: "
                print "\nINFO: best_gene="+str(best)
                
                print "\nINFO: best_score="+ \
                      str(-1*max(self.search.db_entry['best_scores']))
                print " ***  evolution finished at ", time.ctime(), "  ***"
                print " ***  docking takes %10.2f minutes"%\
                      ((time.time()-beginTime)/60.)
                print "\nINFO: number_evaluation="+ \
                      str(self.scoreObject.numEval)
                print "-----------------\n"
                self.post_one_docking()
            return


        def _prepareLigand(self):
            """ prepare ligand related files"""
            setting = self.setting
            if not self.setting.has_key("LigandXML"):
                filename = self.setting['Ligand']
                   
                xmlFilename = filename.split('.')[0]+".xml"

                pdbqt2XML(filename, xmlFilename, center = None, dims = None)

                

            # load ligand
            self.xmlReader(setting['LigandXML'], True)
            self.LigandTree = LigTree = self.xmlReader.get()[0]
            self.ligRoot = ligRoot = LigTree.root
            # ligandSet is the the set of atoms orders according to the tree
            self.ligandSet = ligandSet = ligRoot.getAtoms()
            self.ligandFile = LigTree.pdbfilename
            return



        def _setupSearch(self):
            setting = self.setting
            from AutoDockFR.FTGA import FTtreeGaRepr, OneFT_GaRepr
            from AutoDockFR.USRscorer import USRscore
            scoreObject = USRscore(atoms = self.ligandSet,
                                   refShape = self.atmSet)
            self.scoreObject = scoreObject

            self.gnm = gnm = OneFT_GaRepr(self.LigandTree,\
                                      scoreObject, optFEB=setting['GA_optFEB'])
            print "Number of genes:", gnm.totalGeneNum
            
            self.pop = pop = Population(self.gnm)
            self.search = galg = GA(pop)
            if 'GA_max_eval' in setting.keys(): 
                from mglutil.util.callback import CallBackFunction
                cb = CallBackFunction(self.max_evaluation_cb)
                galg.addCallback('postGeneration', cb)
                self.max_evaluation = setting['GA_max_eval']
            #if 'stop_score' in setting.keys():
            #    galg.settings['stop_score'] = setting['stop_score']
            return

        def one_docking(self):
            searchingParam = self.setting.copy()
            galg = self.search
            galg.updateSetting(searchingParam)
            galg.evolve()
            return

        def post_one_docking(self):
            """ run this function after each one_dock(),
overwrite it if necessory"""
            best = self.search.pop.best()   
            from AutoDockFR.utils import getRMSD
            L_coords = best.toPhenotype(sort = False)
            rmsd = getRMSD(self.setting, [L_coords], \
                         origAtomSet = self.ligRoot.getAtoms())[0]

            #print "INFO: best_USR =", self.scoreObject.bestScore
            #print
            print "USR", self.scoreObject.bestScore,
            print "RMSD", rmsd
            
            #self.validateScore(best)
            self.scoreObject.numEval = 0
            self.scoreObject.bestScore = -1e9
            
            from MolKit.pdbWriter import PdbqsWriter, PdbWriter, PdbqWriter
            writer = PdbqWriter()
            self.ligandSet.updateCoords(L_coords, 1)
            name = "out_"+self.ligandSet.top.uniq()[0].name
            writer.write("foo.pdbq", self.ligandSet)
            return


## global.. map searching methods to classes..
AvailableSearch = {
    'GA': Dock_Serial,
    'GA1': Dock_Serial,
    'GA2': Dock_Serial,
    'GA2_1': Dock_Serial,
    'GA2_2': Dock_Serial,
    'GA3': Dock_Serial,
    'GA4': Dock_Serial,
    'GA5': Dock_Serial,
    'GA6': Dock_Serial,
    'DACGA': Dock_DivideAndConquer,
    'PSO': PSO_Docking}

