#######################################################################
#
# Date: July 2007 Authors:  Yong Zhao
#
#   yongzhao@scripps.edu
#       
#   The Scripps Research Institute (TSRI)
#   Molecular Graphics Lab
#   La Jolla, CA 92037, USA
#
# Copyright: Yong Zhao, Michel Sanner and TSRI
#
#########################################################################

"""
 AutoDockFR parameters..
 optparse.OptionParser is not used because it's too restrictive.

"""
import sys, pdb, os
defaultParams = {}

class OptionItem:
    def __init__(self,  name="no name", type="string", \
                 dest=None, help="no help available", \
                 default=None, validValues=None, group=None, \
                 enableGUI=False):
        
        self.type = type
        self.dest = dest
        ## Note: 'name' is never used.
        ## prefix "--" is added when used as commandline option
        ## e.g.  --repeat 3
        if dest:
            self.name="--"+self.dest
        else:
            self.name = name
            
        self.help = help
        self.default = default
        self.value = default
        self.group = group
        self.enableGUI = enableGUI
        return

    def __repr__(self):
        rep = "%s = %s" % (self.dest, self.value)
        return rep

    def isValid(self):
        return True
##         if validValues is None: ## no valid values specified..
##             return True
##         if validValues=="xmlfile":
##             if not os.path.exists(self.value):
##                 return False
##             ## readxml here
##         else:
##             raise


        

import UserList
class OptionList(UserList.UserList):
    def __init__(self, inputs=None):
        self.data = []
        # Set the default values for parameters
        self.setDefaultValues()   
        self.setting = {}
        self.undefinedSettings = {}

        if inputs is None:
            return
       
        filename = None
        # Setting the filename variable
        for i in range(len(inputs)): #sys.argv[1:]:
            arg = inputs[i]
            if arg == '-p':
                filename = inputs[i+1]
                break
                
        # Read the settings file
        if filename is not None:        
            if not os.path.exists(filename):
                print "Error: file %s not found"%filename
                return

            self.filename = filename
            
            # open the setting file
            ## inputs_file = file(filename, 'r')
            ## lines = inputs_file.readlines()
            ## for line in lines:
            ##     # Read the lines that do not begin with # or \n
            ##     if line[0] != '#' and line[0] != '\n':
            ##         #Removes spaces such as: ReceptorXML = 'AutoDockFR/Tests/Data/1HBV_example.xml' ~> ReceptorXML='AutoDockFR/Tests/Data/1HBV_example.xml'
            ##         line = line.replace(' ', '') 
            ##         tmp = line.split('\n')[0].split('=')
            ##         if tmp[1][0] !='\'': # number setting
            ##             try:
            ##                 self.setting[tmp[0]] = eval(tmp[1])
            ##             except:
            ##                 self.setting[tmp[0]] = tmp[1]
            ##         else: # string setting
            ##             strSetting = tmp[1].replace('\'', '') 
            ##             self.setting[tmp[0]] = strSetting
            execfile(filename, self.setting)
            del self.setting['__builtins__']
            # Appears to check the values
            for k, v in self.setting.items():
                optItem = self.get(k)
                if optItem != None:
                    optItem.value = v
                    #print "new setting:", k,v
                else:
                    print "Warning: unknown setting:", k,v
                    #self.undefinedSettings[k] = v
                    self.setting[k] = v             

        ## the command line options overwrites the parameters in the file
        self.groups = list(set(self.group))
        self.groups.append('all')
        printHelp = False
        argLen = len(inputs)
        i = 0
        while i < argLen: 
            argName = inputs[i][1:]
            if argName not in self.dest:
                print "Error: Unknown parameter:", inputs[i]
                print "Use runadfr -help [topics] for more information.\n"
                raise RuntimeError, "Error: Unknown parameter %s"% inputs[i]
            if argName == "help":
                value = "brief"
                try:
                    value = inputs[i+1]
                    if value not in self.groups:                        
                        value = "brief"
                except:
                    pass
                printHelp = True
                break
            if argName == "box_center" or argName == 'box_dimensions':
                value = [eval(inputs[i+1]),eval(inputs[i+2]),eval(inputs[i+3])]
                i += 4
            else:
                try:
                    value = eval(inputs[i+1])  ## a string
                except:
                    value = inputs[i+1]
                i+=2

            optItem = self.get(argName)
            optItem.value = value
            self.setting[argName] = value

        if printHelp:
            from Version import printHeader
            printHeader()
            self.printHelp(type=value)
            #print self.printHelp
            sys.exit(1)

        return


    def add_option(self,  name="no name", type="string", \
                   dest=None, help="no help available", \
                   default=None, validValues=None, group=None, \
                   enableGUI=False):
        """add an option to the list"""

        item = OptionItem(name=name, type=type, dest=dest, help=help, \
                          default=default, validValues=validValues, \
                          group=group, enableGUI=enableGUI)
        #print ("Default: % s" % item)
        self.data.append(item)
        return
        

    def get(self, dest):
        """returns an Item with name=dest """
        for o in self.data:
            if o.dest == dest:
                return o
        return None



    def setDefaultValues(self, enableGUI=False):
        """set default values for docking parameters"""

        ## parameter file name
        self.add_option('--p', type='string', dest='p',
                        help='docking parameter file', default=None,\
                        group="file",
                        #validValues="xmlfile",
                        enableGUI=enableGUI)

        ## print help
        self.add_option('--h', type='string', dest='help',
                        help='print this', default="all",\
                        group="help",
                        #validValues="xmlfile",
                        enableGUI=enableGUI)

	### Input files ###
        ## ## ligand xml file name
        ## self.add_option('--ligXML', type='string', dest='LigandXML',
        ##                 help='XML file for the ligand', default=None,\
        ##                 group="ligand",
        ##                 validValues="xmlfile",
        ##                 enableGUI=enableGUI)
        ## ## Receptor xml file name        
        ## self.add_option('--recXML', type='string', dest='ReceptorXML',
        ##                 help='XML file for the receptor', default=None,
        ##                 group="receptor",
        ##                 validValues="xmlfile",
        ##                 enableGUI=enableGUI)
        ## ligand .pdbqt file name
        self.add_option('--ligand', type='string', dest='Ligand',
                        help='PDBQ file for the ligand', default=None,\
                        group="ligand",
                        enableGUI=enableGUI)
        ## receptor .pdbqt file name
        self.add_option('--receptor', type='string', dest='Receptor',
                        help='PDBQS file for the receptor', default=None,
                        group="receptor",
                        enableGUI=enableGUI)
        #movingSidechains
        self.add_option('--movingSidechain', type='string', dest='movingSC',
                        help='moving sidechains in the receptor', default=None,
                        group="receptor",
                        enableGUI=enableGUI)


        ### General Docking Settings ###
        ## search methods
        self.add_option('--search',type='choice',
                        dest='search',
                        default='GA',
                        #choices=['GA', 'DACGA', 'PSO'],
                        group="searching",
                        help='Searching method',
                        enableGUI=enableGUI)

        self.add_option('--refGenes', type=None, dest='refGenes',
                        default=None, group="GA",
                        help='individual around which the search is performed',
                        enableGUI=enableGUI)

        ## center of docking box
        self.add_option('--center', type='list', dest='box_center',
                        help='center of the dockng box', default=None,\
                        group="ligand",
                        enableGUI=enableGUI)
	## dimension of the docking box
        self.add_option('--dimension', type='list', dest='box_dimensions',
                        help='dimensions of the docking box', default=None,
                        group="ligand",
                        enableGUI=enableGUI)
        self.add_option('--useXmlBox',type='choice',
                        dest='useXmlBox',
                        default=False,
                        help='Set to True to limit AutoDock grid point to pints inside box defined in Ligand XML file',
                        group="ligand",
                        enableGUI=enableGUI)
        ##
        self.add_option('--pop_size',type='int', dest='initPopSize',
                help='population size',
                group="GA",
                enableGUI=enableGUI)
        
        self.add_option('--usePop',type='string',
                dest='usePop',
                group="GA",
                enableGUI=enableGUI)


        ##  restrict
        self.add_option('--constraintMaxTry',type='int',
                        dest='constraintMaxTry',
                        default=0,
                        help='0 will simply randomize with anchor on good point, Larger value will be the number of attempts to find an individual overlapping good points',
                        group="ligand",)
        self.add_option('--GAminimize', type='{}', dest='GAminimize',
                        help='list of minimize parameters [nbsteps, noImproveStop, max_steps, MAX_FAIL, MINVAR]', 
                        group="score",
                        default=None)
        ## self.add_option('--nbSteps', type='', dest='minimize',
        ##                 help='list of minimize parameters [nbsteps, noImproveStop, max_steps, MAX_FAIL, MINVAR]', 
        ##                 group="score",
        ##                 default=None)
        ## self.add_option('--noImproveStop', type='', dest='minimize',
        ##                 help='list of minimize parameters [nbsteps, noImproveStop, max_steps, MAX_FAIL, MINVAR]', 
        ##                 group="score",
        ##                 default=None)
        ## self.add_option('--max_steps', type='', dest='minimize',
        ##                 help='list of minimize parameters [nbsteps, noImproveStop, max_steps, MAX_FAIL, MINVAR]', 
        ##                 group="score",
        ##                 default=None)
        ## self.add_option('--MAX_FAIL', type='', dest='minimize',
        ##                 help='list of minimize parameters [nbsteps, noImproveStop, max_steps, MAX_FAIL, MINVAR]', 
        ##                 group="score",
        ##                 default=None)
        ## self.add_option('--MINVAR', type='', dest='minimize',
        ##                 help='list of minimize parameters [nbsteps, noImproveStop, max_steps, MAX_FAIL, MINVAR]', 
        ##                 group="score",
        ##                 default=None)
 
        
        ## self.add_option('--constraint_ls',type='choice',
        ##                 dest='constraint_ls',
        ##                 help='Set to True to include local search when limiting the whole ligand within the good points',
        ##                 group="ligand",)

        ##  repeat
        self.add_option('--repeat', type='int', dest='repeat',
                        help='number of docking tests', default=1,
                        group="repeat",
                        enableGUI=enableGUI)
        ##  Reference structure for RMSD calculation after docking
        self.add_option('--rmsdRef',type='list',
                        dest='rmsdRef',
                        default=[],
                        group="ref",
                        help='After docking, compute RMSD between the predicted ligand pose and these reference structures.')
        ##  Reference structure for RMSD calculation for moving receptor
        self.add_option('--rmsdRecRef',type='list',
                        dest='rmsdRecRef',
                        default=[],
                        group="ref",
                        help='After docking, compute RMSD between the predicted Receptor pose and these reference structures.')
        self.add_option('--rmsdSym',type='',
                        dest='rmsdSym',
                        default=None,
                        group="ref",
                        help='Equivalent atoms (root atoms) that makes the ligand symmetric')


	## Output files ##
        ## log file
        self.add_option('--log_file',type='string',
                        dest='log_file',
                        default=None,
                        help='save the output to file',
                        group="log",
                        enableGUI=enableGUI)        
        ## prefix for name of outputted XXX_rec_Y.pdb XXX_lig_Y.pdb files
        #self.add_option('--out',type='string',
        #                dest='out',
        #                default=None,
        #                help='prefix for docking prediction files',
        #                group="output",
        #                enableGUI=enableGUI)

        ## jobID
        self.add_option('--jobID', type='string', dest='jobID',
                        help='ID for this job', default='1',
                        group="output",
                        enableGUI=enableGUI)
        
        #self.add_option('--popOutName',type='string',
        #                dest='popOutName',
        #                default=None,
        #                help='save the output to file',
        #                group="log",
        #                enableGUI=enableGUI)        


        self.add_option('--savePopulationGenes',type='list', default=[],
                        dest='savePopulationGenes',
                        help='save the output to file',
                        group="log",
                        enableGUI=enableGUI)
        self.add_option('--savePopulationGenesBest',type='list', default=[],
                        dest='savePopulationGenesBest',
                        help='save the output to file',
                        group="log",
                        enableGUI=enableGUI)  
        self.add_option('--savePopulationHist',type='list', default=[],
                        dest='savePopulationHist',
                        help='save the output to file',
                        group="log",
                        enableGUI=enableGUI)      
        self.add_option('--savePopulationMols',type='list', default=[],
                        dest='savePopulationMols',
                        help='save the output to file',
                        group="log",
                        enableGUI=enableGUI)      

        ### GA settings ###
        ## random seed
        self.add_option('--rand_seed',type='float',
                        dest='rand_seed',
                        default=-1, ## -1 for "using system time"
                        help='seed for random number generator',
                        group="seed",
                        enableGUI=enableGUI)

        self.add_option('--optFEB', type='int', dest='GA_optFEB',
                        help='optimize FEB rather than interaction+internal',
                        default=False, group="GA",
                        enableGUI=enableGUI)

	self.add_option('--gens',type='int', dest='GA_gens',
                        help='number of generations', default=100,
                        group="GA",
                        enableGUI=enableGUI)
        self.add_option('--pop_size',type='int', dest='GA_pop_size',
                        help='population size',default=100,
                        group="GA",
                        enableGUI=enableGUI)        
        self.add_option('--p_replace',type='float', dest='GA_replace',
                        default=0.5, enableGUI=enableGUI,
                        group="GA",
                        help='replace rate in each generation')        
        self.add_option('--p_injectRandomInd',type='float', \
                        dest='GA_injectRandomInd',
                        default=0, enableGUI=enableGUI,
                        group="GA",
                        help='at each generation we inject random new indivduals. The number injected individuals is injectRandomInd*GA_pop_size')
        self.add_option('--p_cross',type='float', dest='GA_crossover',
                        default=0.5, enableGUI=enableGUI,
                        group="GA",
                        help='probability of cross-over')
        self.add_option('--mutation_rate',type='float', \
                        dest='GA_mutation',
                        default=0.3, enableGUI=enableGUI,
                        group="GA",
                        help='probability of mutation')        
        self.add_option('--p_deviation',type='float', dest='GA_deviation',
                        default=1e-4, enableGUI=enableGUI,
                        group="GA",
                        help='stop evolution when the standard deviation of scores are below this value')
        self.add_option('--max_evaluation',type='int', dest='GA_max_eval',
                        default=1000, enableGUI=enableGUI,
                        group="GA",
                        help='maximum number of evaluations allowed.')
        ## Local Search settings        
        self.add_option('--enableLocalSearch',type='choice', \
                        dest='GA_enableLocalSearch',
                        default=False, enableGUI=enableGUI,
                        group="GA",
                        #choices=[True, False],
                        help='enable the local search')
        self.add_option('--p_localsearchfreq',type='float', \
                         dest='GA_localsearchfreq',
                         default=0.05, enableGUI=enableGUI,
                         group="GA",
                         help='local search probability')
        self.add_option('--p_localsearch',type='float', \
                        dest='GA_localsearchrate',
                        default=0.3, enableGUI=enableGUI,
                        group="GA",
                        help='probability of modifying a gene in LS')
        ## self.add_option('--p_localsearchTopPopSize',type='float', \
        ##                 dest='GA_localsearchTopPopSize',
        ##                 default=10, enableGUI=enableGUI,
        ##                 group="GA",
        ##                 help='numer of top ranking individuals to optimize')
        ## self.add_option('--p_localsearchRandPopSize',type='float', \
        ##                 dest='GA_localsearchRandPopSize',
        ##                 default=10, enableGUI=enableGUI,
        ##                 group="GA",
        ##                 help='Number of random individuals to optimize')
        self.add_option('--MAX_SUCCESS',type='int', \
                        dest='GA_localSearchMaxSuccess',
                        default=4, enableGUI=enableGUI,
                        group="GA",
                        help='number of successes in a row before a change is made to the rho parameter in Solis& Wets algorithms. This is an unsigned integer and is typically around four')
        self.add_option('--MAX_FAIL',type='int', \
                        dest='GA_localSearchMaxFail',
                        default=4, enableGUI=enableGUI,
                        group="GA",
                        help='This is the number of failures in a row before Solis & Wets algorithms adjust rho. This is an unsigned integer and is usually around four.')
        self.add_option('--FACTOR_EXPANSION',type='float', \
                        dest='GA_localSearchFactorExpansion',
                        default=2.0, enableGUI=enableGUI,
                        group="GA",
                        help='value to increase rho by after the maximum number of consecutive sucesses')
        self.add_option('--FACTOR_CONTRACTION',type='float', \
                        dest='GA_localSearchFactorContraction',
                        default=0.5, enableGUI=enableGUI,
                        group="GA",
                        help='value to decrease rho by after the maximum number of consecutive failures')
        self.add_option('--MAX_ITS',type='int', \
                        dest='GA_localSearchMaxIts',
                        default=5, enableGUI=enableGUI,
                        group="GA",
                        help='maximum number of iterations that the local search applies to the phenotype of the individual')
        self.add_option('--MIN_VAR',type='float', \
                        dest='GA_localSearchMinVar',
                        default=0.01, enableGUI=enableGUI,
                        group="GA",
                        help='This is the lower bound on rho, the variance for making changes to genes (i.e. translations, rotations, and torsions). rho can never be modified to a value smaller than this value')
        ## self.add_option('--Rho',type='float', \
        ##                 dest='GA_localSearchRho',
        ##                 default=0.10, enableGUI=enableGUI,
        ##                 group="GA",
        ##                 help='Initial variance for making changes to genes; specifies the size of the local space to sample')

        self.add_option('--annealSteps',type='int', \
                        dest='AnnealSteps',
                        default=10, enableGUI=enableGUI,
                        group="GA",
                        help='number of steps for simulated annealing of top solutions')



        ## ## Divide and Conquer GA
        ## self.add_option('--x_div',type='int', dest='DAC_x_div',
        ##                 default=1,
        ##                 group="DACGA",
        ##                 help='divide X of docking box into xDiv pieces')
        ## self.add_option('--y_div',type='int', dest='DAC_y_div',
        ##                 default=1,
        ##                 group="DACGA",
        ##                 help='divide Y of docking box into yDiv pieces')
        ## self.add_option('--z_div',type='int', dest='DAC_z_div',
        ##                 default=1,
        ##                 group="DACGA",
        ##                 help='divide Z of docking box into zDiv pieces')
        ## self.add_option('--box_pop_size',type='int', dest='DAC_box_pop_size',
        ##                 default=100,
        ##                 group="DACGA",
        ##                 help='population size for a DAC GA')
        ## self.add_option('--box_gens',type='int', dest='DAC_box_gens',
        ##                 default=10,
        ##                 group="DACGA",
        ##                 help='number of generations for a DAC GA')
        ## self.add_option('--box_p_replace',type='float', \
        ##                 dest='DAC_box_p_replace',
        ##                 default=0.5,
        ##                 group="DACGA",
        ##                 help='replace rate in each generation')
        ## self.add_option('--box_p_cross',type='float', dest='DAC_box_p_cross',
        ##                 default=0.5,
        ##                 group="DACGA",
        ##                 help='probability of cross-over')
        ## self.add_option('--box_mutation_rate',type='float',
        ##                 dest='DAC_box_mutation_rate',
        ##                 default=0.3,
        ##                 group="DACGA",
        ##                 help='probability of mutation')
        ## self.add_option('--box_p_deviation',type='float',
        ##                 dest='DAC_box_p_deviation',
        ##                 default=1e-4,
        ##                 group="DACGA",
        ##                 help='stop when deviation of scores is below this value')        
        ## self.add_option('--box_enableLocalSearch',type='choice',
        ##                 dest='DAC_box_enableLocalSearch',
        ##                 #choices=[True, False],
        ##                 group="DACGA",
        ##                 default=True,                        
        ##                 help='enable the local search in a DAC GA')
        ## self.add_option('--box_p_localsearch',type='float',
        ##                 dest='DAC_box_localsearchrate',
        ##                 default=0.3,
        ##                 group="DACGA",
        ##                 help='local search probability in a DAC GA')

        ## self.add_option('--box_max_evaluation',type='long',
        ##                 dest='DAC_box_max_evaluation',
        ##                 default=1e5,
        ##                 group="DACGA",
        ##                 help='maximum number of evaluations in a DAC GA.')



        ##  scoring function
        self.add_option('--scoringFunction',type='choice',
                        dest='scoringFunction',
                        default='AutoDock4.2',
                        #choices=['AutoDock4.2', 'RMSD'],
                        help='Scoring function',
                        group="score",
                        enableGUI=enableGUI)
        ## gridMaps
        self.add_option('--gridMaps', type='', dest='gridMaps',
                        help='list of grid maps for RRL scoring', 
                        group="score",
                        default=None)

        ## translationPoints
        self.add_option('--transPoints', type='', dest='transPointsFile',
                        help='filename for list of 3D points where the root atom can be moved', 
                        group="score",
                        default=None)

        self.add_option('--gridMapsEcutOff', type='float', dest='mapECutOff',
                        help='energy cutoff value used to find anchor points', 
                        group="score",
                        default=-0.10)

        self.add_option('--fixedLigandRotation',type='choice',
                        dest='fixedLigandRotation',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='freeze fixedLigandRotation',
                        group="ligand",
                        )
        self.add_option('--fixedLigandTranslation',type='choice',
                        dest='fixedLigandTranslation',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='freeze fixedLigandTranslation',
                        group="ligand",
                        )
        self.add_option('--fixedLigandConformation',type='choice',
                        dest='fixedLigandConformation',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='freeze fixedLigandConformation',
                        group="ligand",
                        )
        self.add_option('--fixedLigandMotionCombiner',type='choice',
                        dest='fixedLigandMotionCombiner',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='freeze fixedLigandMotionCombiner',
                        group="ligand",
                        )
        self.add_option('--ReceptorCONECT',type='choice',
                        dest='ReceptorCONECT',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='if enabled the bond CONECT records should be provided',
                        group="receptor",
                        )
        
        # RigidRec-Ligand scoring term
        self.add_option('--RR_L',type='choice',
                        dest='RR_L',
                        default=True,
                        #choices=['AutoDock4.2'],
                        help='RigidRec-Ligand scoring term',
                        group="score",
                        enableGUI=enableGUI)
        # FlexRec-Ligand scoring term
        self.add_option('--FR_L',type='choice',
                        dest='FR_L',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='FlexRec-Ligand scoring term',
                        group="score",
                        enableGUI=enableGUI)
        # Ligand-Ligand scoring term
        self.add_option('--L_L',type='choice',
                        dest='L_L',
                        default=True,
                        #choices=['AutoDock4.2'],
                        help='Ligand-Ligand scoring term',
                        group="score",
                        enableGUI=enableGUI)
        # RigidRec-RigidRec scoring term
        self.add_option('--RR_RR',type='choice',
                        dest='RR_RR',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='RigidRec-RigidRec scoring term',
                        group="score",
                        enableGUI=enableGUI)
        # RigidRec-FlexRec scoring term
        self.add_option('--RR_FR',type='choice',
                        dest='RR_FR',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='RigidRec-FlexRec scoring term',
                        group="score",
                        enableGUI=enableGUI)
        # FlexRec-FlexRec scoring term
        self.add_option('--FR_FR',type='choice',
                        dest='FR_FR',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='FlexRec-FlexRec scoring term',
                        group="score",
                        enableGUI=enableGUI)
        # RigidRec-Ligand GA fitness flag
        self.add_option('--RR_L_Fitness',type='choice',
                        dest='RR_L_Fitness',
                        default=True,
                        #choices=['AutoDock4.2'],
                        help='RigidRec-Ligand scoring term included in GA fitness function',
                        group="score",
                        enableGUI=enableGUI)
        # FlexRec-Ligand GA fitness flag
        self.add_option('--FR_L_Fitness',type='choice',
                        dest='FR_L_Fitness',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='FlexRec-Ligand scoring term included in GA fitness function',
                        group="score",
                        enableGUI=enableGUI)
        # Ligand-Ligand GA fitness flag
        self.add_option('--L_L_Fitness',type='choice included in GA fitness function',
                        dest='L_L_Fitness',
                        default=True,
                        #choices=['AutoDock4.2'],
                        help='Ligand-Ligand scoring term included in GA fitness function',
                        group="score",
                        enableGUI=enableGUI)
        # RigidRec-RigidRec GA fitness flag
        self.add_option('--RR_RR_Fitness',type='choice included in GA fitness function',
                        dest='RR_RR_Fitness',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='RigidRec-RigidRec scoring term included in GA fitness function',
                        group="score",
                        enableGUI=enableGUI)
        # RigidRec-FlexRec GA fitness flag
        self.add_option('--RR_FR_Fitness',type='choice',
                        dest='RR_FR_Fitness',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='RigidRec-FlexRec scoring term included in GA fitness function',
                        group="score",
                        enableGUI=enableGUI)
        # FlexRec-FlexRec GA fitness flag
        self.add_option('--FR_FR_Fitness',type='choice',
                        dest='FR_FR_Fitness',
                        default=False,
                        #choices=['AutoDock4.2'],
                        help='FlexRec-FlexRec scoring term included in GA fitness function',
                        group="score",
                        enableGUI=enableGUI)

        # rmsdScorerTargetLigMol -- molecule used by the RMSDScorer as its target for the ligand
        self.add_option('--rmsdScorerTargetLigMol',type='string',
                        dest='rmsdScorerTargetLigMol',
                        default='',
                        help='molecule used by the RMSDScorer as its target for ligand atoms',
                        group="score",
                        enableGUI=enableGUI)

        # rmsdScorerTargetRecMol -- molecule used by the RMSDScorer as its target for the flexible receptor
        self.add_option('--rmsdScorerTargetRecMol',type='string',
                        dest='rmsdScorerTargetRecMol',
                        default='',
                        help='molecule used by the RMSDScorer as its target for flexible atoms in the receptor',
                        group="score",
                        enableGUI=enableGUI)

        #self.add_option('--calcLigIE',type='choice', dest='calcLigIE',
        #                default=True,
        #                #choices=[True, False],
        #                group="score",
        #                enableGUI=enableGUI,
        #                help='calculate ligand internal energy')
        #self.add_option('--calcRecIE',type='choice', dest='calcRecIE',
        #                default=True,
        #                #choices=[True, False, 'True', 'False'],
        #                group="score",
        #                help='calculate receptor internal energy',
        #                enableGUI=enableGUI)

        UserList.UserList.__init__(self,self.data)   
        return



    def __getattr__(self, member):
        """ """
        result = []
        for o in self.data:
            result.append( o.__dict__[member] )
        return result


    def getSettings(self, returnDict=False):

        currentSettings = []
        
        tmp = [x for x in self.data if x.group == 'ligand' \
               and x.value == None]        
        tmp.extend([x for x in self.data if x.group == 'receptor' \
                    and x.value == None])
        for x in tmp:
            self.data.remove(x)

        searchMethod = ""
        groups = ["file",'ligand','receptor','seed', 'score', \
                'repeat', 'searching', 'ref', 'log', 'output']

        for g in groups:
            for o in self.data:
                if o.group == g:
                    currentSettings.append(o)
                    if o.group == "searching":
                        searchMethod = o.value
        
        ## DACGA shares setting with GA
        if searchMethod == 'DACGA':
            searchMethod = ['GA', 'DACGA']
        
        for o in self.data:
            if o.group in searchMethod:
                currentSettings.append(o)

        if returnDict:
            data = {}
            for o in currentSettings:
                data[o.dest] = o.value
            return data
        else:
            return currentSettings
    
    
    def __repr__(self):
	"""
	String <- __repr__()

	Returns a string with key,value from settings
	"""

        currentSettings = self.getSettings()
        rep = ""
        for item in currentSettings:
            rep += "Setting: %s: %s\n"%(item.dest, item.value)
        return rep

    def printHelp(self, type='brief'):
        rep = "\nusage: flipdock [-p parameter_file] [-parameter value] [-help]\n\n"

        if type == "brief":
            rep += "Use flipdock -help [topics] for more information.\n"
            rep += "Valid topics are:\n"
            for g in self.groups:
                rep += "%s "%g
            rep += "\n"
        elif type == "all":
            rep += "%25s: %10s;  %s"%("Parameter name",\
                                        "Default", "Description\n")
            for item in self.data:
                rep += "%25s: %10s;  %s\n"%(item.dest, \
                                          str(item.default),\
                                          item.help,)
        else:
            items = [x for x in self.data if x.group == type]
            rep += "%25s: %10s;  %s"%("Parameter name",\
                                        "Default", "Description\n")
            rep += "-"*80
            rep += "\n"            
            for item in items:
                rep += "%25s: %10s;  %s\n"%(item.dest, \
                                          str(item.default),\
                                          item.help,)
        print rep
        #raise
        return 



class Params:
    def __init__(self, args=None, enableGUI=False, **kw):
        self.kw = kw = {}
        self.args = args
        self.setting = {}
        # Instance of OptionList class, builds parameter list
        self.optList = OptionList(inputs = args)
        return

    def get(self, item=None):
        if len(self.setting) == 0:
            self.setting = self.optList.getSettings(returnDict = True)

        if item == None:
            return self.setting
        elif item in self.setting.keys():
            return self.setting[item]
        else:
            raise ValueError, "Error: %s is not a valid parameter"%item
            return None


    def validParams(self):
	"""
	True/False <- validParams()

        Preforms sanity checks on SOME keywords in settings file.
        Will return True if all checks pass
	"""

        setting = self.get()
        if len(setting) == 0:
            return False

        ## files exist
        files = ["ReceptorXML","Receptor",'LigandXML','Ligand']
        for f in files:
            if setting.has_key(f) and setting[f] != None:
                if not os.path.exists(setting[f]):
                    print "Fatal Error: file %s not found."%setting[f]
                    return False
        ## has receptor
        if not setting.has_key("ReceptorXML") and \
           not setting.has_key("Receptor"):
            print "Fatal Error: no receptor specified."
            return False

        # If there are not flexible side chains
        if setting.has_key("Receptor"):
            if not setting.has_key("movingSC"):
                if (setting['FR_L'] or setting['RR_FR'] or setting['FR_FR']) or \
			(setting['FR_L_Fitness'] or setting['RR_FR_Fitness'] or setting['FR_FR_Fitness']):
                	print "Error: a rigid receptor was specified. Please set FR_L, RR_FR, FR_FR \
                        FR_L_Fitness, R_FR_Fitness, FR_FR_Fitness to be False"
                	return False
                
        ## has ligand
        if not setting.has_key("LigandXML") and \
           not setting.has_key("Ligand"):
            print "Fatal Error: no Ligand specified."
            return False

        ## box defined
        if setting.has_key("Ligand"):
            if not setting.has_key("gridMaps"):
                if ((not setting.has_key("box_dimensions")) or \
                    (not setting.has_key("box_center"))):
                    print 
                    print "Fatal Error: box_dimensions and box_center must be specified."
                    return False

                
        return True
