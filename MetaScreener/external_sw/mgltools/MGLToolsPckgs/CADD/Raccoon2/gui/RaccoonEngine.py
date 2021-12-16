#       
#           AutoDock | Raccoon2
#
#       Copyright 2013, Stefano Forli
#          Molecular Graphics Lab
#  
#     The Scripps Research Institute 
#           _  
#          (,)  T  h e
#         _/
#        (.)    S  c r i p p s
#          \_
#          (,)  R  e s e a r c h
#         ./  
#        ( )    I  n s t i t u t e
#         '
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#################################################################
#
# Hofstadter's Law: It always takes longer than you expect,
#                   even when you take Hofstadter's Law 
#                   into account.
#
#    The Guide is definitive. Reality is frequently inaccurate.
#        Douglas Adams 
#
#################################################################
#
#
# day_1:   Monday, February 6 2012
# day_2:   Monday, February 13 2012
# day_3:   Tuesday, February 14 2012
# day_4:   Wednesday, February 15 2012
# day_X:   Wednesday, February 22 2012  first working GPF generator
# day_X+1: Friday, February 24 2012 first support for flex residues, 
#                                   first totally successful updateStatus()
#          Tuesday, February 29 2012      first complete cycle, 2 ligs, 2 Rec_rigid, 1 Rec_flex, GPF, DPF(sort of)
#          Wednesday, March 1 2012      first complete running cycle 5K ligs, 2 Rec_rigid, 1 Rec_flex, GPF, DPF
#



import platform # system, platform.uname()
import os, gc, errno # error number for handling error
from sys import argv, exc_info
import  time
from CADD.Raccoon2.HelperFunctionsN3P import *
print "**** CORRECT REFERENCES TO HELPERFUNCTION ****"
import shutil
#import Tkinter.Photo



class RaccoonEngine:
    def __init__ (self, mode='autodock', debug = False):

        # AutoDock, Vina modes
        self.mode = mode # 'autodock', 'vina'
        self.debug=debug

        # System identification
        self.system_info = platform.uname()
        if self.debug: print "Raccoon> system info:", self.system_info
        self.platform = self.system_info[0]

        # checking that the right modules are in place.

        # MolKit stuff
        try:
            # from the prepare_ligand code
            from MolKit import Read
            from AutoDockTools.MoleculePreparation import AD4LigandPreparation, AD4ReceptorPreparation, AD4FlexibleReceptorPreparation
            # from the prepare_flexres code
            from MolKit.protein import ProteinSet, ResidueSet
            from MolKit.molecule import BondSet
            from MolKit.stringSelector import CompoundStringSelector
            from AutoDockTools.MoleculePreparation import AD4FlexibleReceptorPreparation
        except:
            error_title = "MolKit error!"
            error_msg = "Impossible to find the MolKit module."
            error_msg += "\n\nMGLTools is required to run Raccoon but is either misconfigured or not installed"
            if not self.platform == "Windows":
                suggestion = "\n\nPlease install it or be sure to use the right Python interpreter."
            else:
                suggestion = "\n\nPlease install it, or try to run Raccoon with:\n\n $MGLROOT/bin/pythonsh raccoon.py"
            print error_title, error_msg, suggestion
            exit(1)    

        self.hcovbond = 1.1
        self.acceptedFiles = ['pdbqt', 'pdb', 'mol2']

        self.initLigData()
        self.initRecData()
        self.initLigFilters(mode=self.mode) # provide self.filterSettings
        self.initCommonSettings() 
        self.initAutoDockGpfSettings()
        self.initAutoDockDpfSettings()
        self.initVinaSettings()
        self.initSystemOptions()

    def initCommonSettings(self):
        """ initialize common settings for AutoDock and Vina """
        # search space center
        self.box_center = [ None, None, None ]
        # search space dimensions
        self.box_size = [ None, None, None ]
        # output directory
        self.output_dir = { 'path' : None,     # full path
                            'freespace': None, # available disk space (used for predictions?)
                            'used' : False,    # flag to tag the dir once used in a (partial?) generation
                             }

        self.status = { 'lig': False,          # variables for keeping
                        'rec': False,          # track of Raccoon status 
                        'grid_box': False,     # and when the generation
                        'docking': False,      # is allowed
                        'directory': False}

    def initAutoDockGpfSettings(self):
        """ initialize settings for AutoGrid """

        self.autogrid_parameters = { 'gridcenter': [ None, None, None ],
                                    'npts' : [ None, None, None ],
                                    'parameter_file' : None,
                                    'spacing': 0.375,
                                    'receptor_types' : [],
                                    'ligand_types': [],
                                    'receptor': '',
                                    'gridfld' : '',
                                    'smooth' : 0.5,
                                    'map' : [],
                                    'dielectric': -0.1456,
                                    'KEYWORD_ORDER' : [ 'npts', 'gridfld', 'spacing', 'receptor_types', 
                                                        'ligand_types', 'receptor','gridcenter',
                                                        'smooth', 'map', 'dielectric'] }
        ## raccoon options
        #
        # map mode
        self.autogrid_mode = 'always' # 'now' or 'never' (C) 1960 Elvis
        # map copy/link
        self.autogrid_map_file = 'copy' # 'link'
        # binary to use for calculations
        self.autogrid_bin = None # will be initialized with a 'which'
        # map files per atom types
        self.autogrid_maps = {} # { 'A': 'protein.A.map', 'C' : 'protein.C.map', 


    def initAutoDockDpfSettings(self):
        """ initialize settings for AutoDock """

        self.autodock_parameters = {


        'search_mode'   : 'lga', # lga, ga, sa, ls
        'runs'          :  100,  # common to all search methods
        'do_clustering' : True,  # perform clustering
        'complexity_map': None,  # map used to calculate ligand accessibility (usually *.C.map)
        'dpf_mode'      : 'template', # dpf can be generated from'template' or 'auto' (complexity map)


        # generic common settings
        'generic' : {
            'autodock_parameter_version' : '4.2',
            'parameter_file' : None,
            'outlev' : 0,
            'intelec': True,
            'seed' : [ 'pid time'],
            'unbound_model' : 'bound',
            'KEYWORD_ORDER'  : ['outlev','intelec', 'seed', 'unbound_model' ],
            'OPTIONAL'       : [],
            },

        # ligand specific settings
        'ligand' : { 'ligand_types' : [],
                   'map' : [],
                   'move' : '',
                   'flexres' : '',
                   'about' : [0.0, 0.0, 0.0], 
                   'KEYWORD_ORDER' : [ 'ligand_types', 'map', 
                        'fld', 'elecmap', 'desolvmap', 'move', 'flexres', 'about'],
                   'OPTIONAL' : []
            },

        # genetic algorithm search settings
        'ga'     : {
            'ga_pop_size' : 150,
            'ga_num_evals': 2500000,
            'ga_num_generations':   27000,
            'ga_elitism'    : 1,
            'ga_mutation_rate': 0.02,
            'ga_crossover_rate': 0.8,
            'ga_window_size' : 10,
            'ga_cauchy_alpha': 0.0,
            'ga_cauchy_beta': 1.0,
            'set_ga'    : '',
            'KEYWORD_ORDER':['ga_pop_size','ga_num_evals', 
                             'ga_num_generations', 'ga_elitism', 
                             'ga_mutation_rate', 'ga_crossover_rate',
                             'ga_window_size', 'ga_cauchy_alpha',
                             'ga_cauchy_beta', 'set_ga'],
            'OPTIONAL'     :[],
            },

        # simulated annealing search settings
        'sa': { 'tstep': 2.0,
                'qstep': 50.0,
                'dstep': 50.0,
                'rt0':   1000.0,
                'scheduler': 'linear_schedule', # 'linear_schedule', None
                'rtrf': 0.95,
                'trnrf': 1.0,
                'quarf': 1.0,
                'dihrf': 1.0,
                'cycles': 50,
                'accs': 100,
                'rejs': 100,
                'select': 'm',
                'KEYWORD_ORDER': [ 'tstep', 'qstep', 'dstep', 'rt0', 'scheduler',
                                  'rtrf', 'trnrf', 'quarf', 'dihrf', 'cycles', 'accs',
                                  'rejs', 'select']
               },

        # local search settings
        'ls' : { 
            'ga_pop_size' : 150,
            'sw_max_its': 300,
            'sw_max_succ' : 4,
            'sw_max_fail' : 4,
            'sw_rho'    : 1.0,
            'sw_lb_rho' : 0.01,
            'ls_search_freq': 0.06,
            'set_psw1' : '',
            'KEYWORD_ORDER' : [ 'ga_pop_size', 'sw_max_its', 'sw_max_succ', 'sw_max_fail',
                               'sw_rho', 'sw_lb_rho', 'ls_search_freq', 
                               'set_psw1'],
            },

        # clustering analysis settings
        'clustering': {
            'rmstol' : 2.0,
            'analysis' : '',
            'KEYWORD_ORDER': ['rmstol', 'analysis']
            },
                # activate GA           : 'ga_run'
                # activate LS             : 'set_psw1', 'set_sw1'
                # activate Clustering   : 'analysis'
                # ACTIVATION ORDER: generic, ls, ga, clustering

            } # end autodocking settings
    
        # XXX unbound energies... calculate?
        #  LS = (ga_pop_size + ls_block + do_local_only XX + analysis )
        # LGA = (ga_block + ls_block + ga_run XX + analysis)
        # Refer to "self.autodock_runs" value

    def initVinaSettings(self):
        # vina data
        self.vina_settings = { 
               'center_x': 0.0,
               'center_y': 0.0,
               'center_z': 0.0,
               'size_x'  : 0.0,
               'size_y'  : 0.0,
               'size_z'  : 0.0,
               'out'     : '',
               'log'     : '',
               'cpu'     : 1,
               'exhaustiveness': 8,
               'num_modes' : 9,
               'energy_range': 3.,
               'KEYWORD_ORDER': [ 'center_x', 'center_y', 'center_z',
                                  'size_x', 'size_y', 'size_z',
                                  'exhaustiveness', 'cpu', 'out', 'log',
                                  'num_modes', 'energy_range',
                                ],
               'OPTIONAL' : {'out': False, 'log' : False, 'num_modes' : False, 'energy_range': False }, 
        }


    def initSystemOptions(self):
        """ initialize general options 'self.generalOpts', used 
            during the generation of the jobs
        """

        self.generalOpts = { 
           'generic': {  'computing'            : 'workstation', # workstation, linux_cluster
                         'platform'             : 'current', # current (sys.platform), 'posix', 'windows', 'cygwin'
                         'split'                : 1000,  # None, 10, 100, 1000, 10K 100K
                         'script'               : 'master', # master, single, off
                         'package'              : 'off', # tar, targz, tarbz2, zip, off
                         'delete_maps'          : True, # true/false
                         'out_file_per_ligand'  : 1,  # 1  
                         'cpu_per_job'          : 1,  # 1, 2, 3
                      },

           'scheduler': 'pbs', # currently, only 'pbs'; FUTURE: sungrid, opal ...?

           'scheduler_pbs': { 
                         'cput'        : '24:00:00',
                         'walltime'    : '24:00:00',
                         'nodes'       : 1,
                         'ppn'         : 1,
                         'mem'         : '512mb',
                         'scratch_dir' : '',
                         'qsub_bin'    : 'qsub',
                         'autodock_bin': 'autodock4',
                         'autogrid_bin': 'autogrid4',
                         'vina_bin'    : 'vina',
                         'options'     : '', #OPT="-q MyPriorQueue"
                    },
            }



    def setMode(self, mode ='autodock'):
        """handle all the changes to be made to Raccoon
            to handle the different engines (autodock,vina)
        """
        # if current settings are previous mode default
        # this setting must be updated
        self.mode = mode
        if self.filterSettings == self.FILTER_DEF:
            current_default = True
        else:
            current_default = False
        self.initLigFilters(mode=mode)

        if current_default: 
            self.filterSettings = self.FILTER_DEF.copy()
        # XXX incomplete... XXX


    def setBoxCenter(self, coord):
        """ accepts a vector with 3 coordinates (A)"""
        try:
            self.box_center = [ float(coord[0]), float(coord[1]), float(coord[2]) ]
            # update the vina config template
            self.vina_settings['center_x'] = self.box_center[0]
            self.vina_settings['center_y'] = self.box_center[1]
            self.vina_settings['center_z'] = self.box_center[2]
            # update the autodock config template
            self.autogrid_parameters['gridcenter'] = self.box_center[:]

            return True
        except:
            if self.debug:
                print "setBoxCenter> ERROR in setting coords(%s) : %s" % (coord, exc_info()[1]  )
            return False 
            

    def setBoxSize(self, size):
        """ accepts a vector with three dimensions (A)
            numbers are adapted later on to be points 
            (AD) or actual angstroms (VINA)
        """
        try:
            self.box_size = [ float(size[0]), float(size[1]), float(size[2]) ]
            # update the vina config template
            self.vina_settings['size_x'] = self.box_size[0]
            self.vina_settings['size_y'] = self.box_size[1]
            self.vina_settings['size_z'] = self.box_size[2]
            # update the autogrid config template
            self.autogrid_parameters['npts'] = [ int(x/self.autogrid_parameters['spacing'])+1 for x in self.box_size ]
            return True
        except:
            if self.debug:
                print "setBoxSize> ERROR in setting size (%s) : %s" % (size, exc_info()[1]  )
            return False

    def setAutoGridResolution(self, spacing):
        try:
            spacing = float(spacing)
        except:
            if self.debug: print "setAutoGridResolution> ERROR setting grid resolution [%s]: %s" % (spacing, exc_info()[1])
            return False
        self.autogrid_parameters['spacing'] = spacing
        size = [ x * spacing for x in self.autogrid_parameters['npts'] ]
        self.setBoxSize(size)
        return True


    def setOutputDir(self, dir_path, autoCreate=True, checkEmpty=True):
        try:
            # check if dir exists
            if not os.path.exists(dir_path):
                if not autoCreate:
                    if self.debug: print "setOutputDir> ERROR directory (%s) doesn't exist (autoCreate:False)" % (dir_path)
                    return (False, 'inexistent')
                try:
                    os.makedirs(dir_path)
                except:
                    # XXX add here all teh tests.. /dev/null dev/full
                    if self.debug: print "setOutputDir> ERROR impossible to create dir (%s): %s" % (dir_path, exc_info()[1])  
                    return (False, ('error creating dir %s: %s' % (dir_path, exc_info()[1]) ) )

            # check if dir is empty
            if checkEmpty and not os.listdir(dir_path) == []: 
                if self.debug: print "setOutputDir> ERROR directory not empty (%s) (checkEmpty:True)" % dir_path
                return (False, 'not empty')

            # successful
            self.output_dir['path'] = dir_path
            self.output_dir['freespace'] = checkDiskSpace(dir_path)
            checkDiskSpace(dir_path, human=True)
            self.output_dir['used'] = False
            self.updateStatus()
            return (True, 'no errors')
        except:
            print "setOutputDir> ERROR impossible to access directory (%s) : %s" % (dir_path, exc_info()[1])
            return (False, ('error accessing %s: %s' % (dir_path, exc_info()[1]) ) )

    def initLigData(self):
        """ initialize ligand dictionaries of the Raccoon session"""
        try: del self.LigBook
        except: pass
        self.LigBook = {}

        try: del self.atypelist
        except: pass
        try: del self.unknownAtypes
        except: pass
        # AutoDock atom type list and their count (updated with ligands imported)
        ## Warning: atomic weights are inaccurate and there is no account for merged non-polar H's
        self.defaultAtWeight = 12 # default atomic weight for unknown atype
            

        self.atypelist = {   # count  MW
                    'H'      : [ 0,  1    ],
                    'HD'     : [ 0,  1    ],
                    'HS'     : [ 0,  1    ],
                    'C'      : [ 0,  12   ],
                    'A'      : [ 0,  12   ],
                    'N'      : [ 0,  14   ],
                    'NA'     : [ 0,  14   ],
                    'NS'     : [ 0,  14   ],
                    'OA'     : [ 0,  16   ],
                    'OS'     : [ 0,  16   ],
                    'F'      : [ 0,  19   ],
                    'Mg'     : [ 0,  24   ],
                    'MG'     : [ 0,  24   ],
                    'P'      : [ 0,  31   ],
                    'SA'     : [ 0,  32   ],
                    'S'      : [ 0,  32   ],
                    'Cl'     : [ 0,  35.4 ],
                    'CL'     : [ 0,  35.4 ],
                    'Ca'     : [ 0,  40   ],
                    'CA'     : [ 0,  40   ],
                    'Mn'     : [ 0,  55   ],
                    'MN'     : [ 0,  55   ],
                    'Fe'     : [ 0,  56   ],
                    'FE'     : [ 0,  56   ],
                    'Zn'     : [ 0,  65.4 ],
                    'ZN'     : [ 0,  65.4 ],
                    'Br'     : [ 0,  80   ],
                    'BR'     : [ 0,  80   ],
                    'I'      : [ 0, 126   ],
                                                # XXX remember to put W and G atoms!
                    'e'      : [ 1,   0   ], # always 1 by default XXX check this in the new raccoon
                    'd'      : [ 1,   0   ]  # always 1 by default
                    }
        self.unknownAtypes = {} # 'type' : [ filenames ]


    def initRecData(self):
        """ initialize receptor dictionaries of the Raccoon session"""
        try: del self.RecBook
        except: pass
        self.RecBook = {}

        try: del self.atypelistRec
        except: pass
        self.atypelistRec = {   # count  MW
                    'H'      : [ 0,  1    ],
                    'HD'     : [ 0,  1    ],
                    'HS'     : [ 0,  1    ],
                    'C'      : [ 0,  12   ],
                    'A'      : [ 0,  12   ],
                    'N'      : [ 0,  14   ],
                    'NA'     : [ 0,  14   ],
                    'NS'     : [ 0,  14   ],
                    'OA'     : [ 0,  16   ],
                    'OS'     : [ 0,  16   ],
                    'F'      : [ 0,  19   ],
                    'Mg'     : [ 0,  24   ],
                    'MG'     : [ 0,  24   ],
                    'P'      : [ 0,  31   ],
                    'SA'     : [ 0,  32   ],
                    'S'      : [ 0,  32   ],
                    'Cl'     : [ 0,  35.4 ],
                    'CL'     : [ 0,  35.4 ],
                    'Ca'     : [ 0,  40   ],
                    'CA'     : [ 0,  40   ],
                    'Mn'     : [ 0,  55   ],
                    'MN'     : [ 0,  55   ],
                    'Fe'     : [ 0,  56   ],
                    'FE'     : [ 0,  56   ],
                    'Zn'     : [ 0,  65.4 ],
                    'ZN'     : [ 0,  65.4 ],
                    'Br'     : [ 0,  80   ],
                    'BR'     : [ 0,  80   ],
                    'I'      : [ 0, 126   ],
                                                # XXX remember to put W and G atoms!
                    'e'      : [ 1,   0   ], # always 1 by default XXX check this in the new raccoon
                    'd'      : [ 1,   0   ]  # always 1 by default
                    }

        try: del self.resRotatableBondTable
        except: pass

        # XXX potentially useless... (see self.addReceptor
        self.resRotatableBondTable = {
                'GLY'    : [ 0, [""] ],  # XXX this should raise an error message?
                'ALA'    : [ 0, [""] ],
                'PRO'    : [ 0, [""] ],
                'VAL'    : [ 1, ["C"] ],
                'LEU'    : [ 2, ["C"] ],
                'SER'    : [ 2, ["C", "OA", "HD"] ],
                'THR'    : [ 2, ["C", "OA", "HD"] ],
                'CYS'    : [ 2, ["C", "SA", "HD"] ],
                'ASN'    : [ 2, ["", "", ""] ],
                'PHE'    : [ 2, ["A", "C"] ],
                'TRP'    : [ 2, ["C", "A", "N", "HD"] ],
                'HIE'    : [ 2, ["C", "A", "NA", "N", "HD"] ],
                'HIS'    : [ 2, ["C", "A", "NA", "N", "HD"] ],
                'ASP'    : [ 2, ["C", "OA"] ],
                'ILE'    : [ 2, ["C"] ],
                'GLN'    : [ 3, ["C", "OA","N","HD"] ],
                'TYR'    : [ 3, ["C", "A", "OA", "HD"] ],
                'GLU'    : [ 3, ["C", "OA"] ],
                'MET'    : [ 3, ["C", "S"] ],
                'ARG'    : [ 4, ["C", "N", "HD"] ],
                'LYS'    : [ 5, ["C", "N", "HD"] ] }


    def initLigFilters(self, mode='autodock'):
        """
            create the pre-set filter settings
            (mode-dependent)
        """
        self.autodockMaxRot = 32
        self.vinaMaxRot = 50

        if self.mode == 'autodock':
            self.maxTors = self.autodockMaxRot
        elif self.mode == 'vina':
            self.maxTors = self.vinaMaxRot

        # TODO check if they exist first?


        self.FILTER_DEF = { 'hbd' : [0,99],  'hba' : [0,99],
                            'mw'  : [0,9999],'nat' : [0,999],
                            'tors': [0,self.maxTors], 'accept_unk_atypes': False,
                            'title': 'Default'}
        self.FILTER_DEF_LIPINSKY = { 'hbd' : [0,5],  'hba' : [0,10],
                            'mw'  : [0,500],'nat' : [0,999],
                            'tors': [0,self.maxTors], 'accept_unk_atypes': False,
                            'title': 'Lipinsky-like'}
        self.FILTER_DEF_DRUGLIKE = { 'hbd' : [0,5],  'hba' : [0,10],
                            'mw'  : [160,480],'nat' : [20,70],
                            'tors': [0,self.maxTors], 'accept_unk_atypes': False,
                            'title': 'Drug-like'}
        self.FILTER_DEF_DRUGLIKE_FRAG = { 'hbd' : [0,3],  'hba' : [0,6],
                            'mw'  : [160,300],'nat' : [6,45],
                            'tors': [0,self.maxTors], 'accept_unk_atypes': False,
                            'title': 'Drug-like (fragments)'}

        self.setFilterSet(filterSet='default')


    def setFilterSet(self, filterSet=None, customFilter=None):
        """
            change the current filter set.
            It is possible to specify any of the predefined or
            provide a custom one.

            predefined: default, lipinsky, druglike, druglike_frag

            accepted filter format: { 'hbd': [min,MAX] , 'hba':[min,MAX] ,
                                      'mw' : [min,MAX] , 'nat':[min,MAX] ,
                                      'tors': [min,MAX], 'accept_unk_atype : False,
                                      'title': '' }
        """
        if customFilter:
            setting = customFilter
        else:
            if filterSet == 'default' or filterSet==None:
                setting = self.FILTER_DEF
            elif filterSet == 'lipinsky':
                setting = self.FILTER_DEF_LIPINSKY
            elif filterSet =='druglike':
                setting = self.FILTER_DEF_DRUGLIKE
            elif filterSet =='druglike_frag':
                setting = self.FILTER_DEF_DRUGLIKE_FRAG

        self.filterSettings = setting.copy() # initialize the current filter settings with the default Raccoon

        

            
    #def ligands(self, atLeastOne=False):
    def ligands(self, atLeastOne=False):
        """ return accepted ligands """
        out = []
        for l in self.LigBook.keys():
            if self.LigBook[l]['accepted']:
                out.append(l)
                if atLeastOne:
                    return out
        return out

    #def receptors(self):
    def receptors(self):
        """ return accepted receptors"""
        out = []
        for r in self.RecBook.keys():
            if self.RecBook[r]['accepted']:
                out.append(r)
        return out

    def atomTypes(self):
        alist = []
        for a in self.atypes:
            if a[0] > 0:
                alist.append(a)
        return alist


    def allLigands(self):
        """ return all ligands """
        return self.LigBook.keys()

    def currentLigAtypes(self):
        """ 
            return atom types employed in the 
            current session (accepted ligands
        """
        atypes = []
        for a in self.atypelist.keys():
            if self.atypelist[a][0] > 0:
                atypes.append(a)
        return sorted(atypes)

    def removeReceptors(self, rec_list=None):
        """ remove receptors from the session"""
        # XXX TODO
        if rec_list == None:
            print "Engine:removeReceptors> wyping out everything..."
            self.RecBook.clear()
        else:
            for r in rec_list:
                del self.RecBook[r]
        self.updateStatus()
 
    def removeLigands(self, lig_list=None):
        """ remove requested ligands from the Great Book of Ligands
        """
        #print "removeLigands>"
        if lig_list == None:
            self.initLigData()
        else:
            for l in lig_list:
                self.registerLigand(action='del', **self.LigBook[l])
        self.updateStatus()

    def updateStatus(self, report=False):
        """
        check the status of the session for the generation step:
        - at least one ligand is present and filter-accepted;
        - at least one receptor is present and accepted
        - grid box params are defined (size, position)
        - docking params are defined
        - output dir is defined
        """
        # ligands
        self.status['lig'] = ( len(self.ligands(atLeastOne=True)) > 0 )
        # receptor
        self.status['rec'] = ( len(self.RecBook.keys()) > 0 )
        # grid_box
        center = True
        size = True
        for c in self.box_center:
            if c == None:
                center = False
                #if self.debug: print "MISSING CENTER", self.box_center
                break
        if center:
            for s in self.box_size:
                if s == None:
                    size = False
                    #if self.debug: print "MISSING SIZE", self.box_size
                    break
        self.status['grid_box'] = (center and size)
        # docking
        self.status['docking'] = True
        # directory
        valid_path = False
        if not self.output_dir['path'] == None:
            if not self.output_dir['used']:
                if self.output_dir['freespace'] > 0: # XXX useless placeholder /to be improved
                    valid_path = True    
        self.status['directory'] = valid_path
        # FINAL STATUS
        final_status = (self.status['lig'] and 
                self.status['rec'] and 
                self.status['grid_box'] and 
                self.status['docking'] and 
                self.status['directory'] )

        if report: # or self.debug:
            print "\nupdateStatus>"
            for i in sorted(self.status.keys()):
                print "\t[   %s\t]\t %s" %(self.status[i], i)
            print '\t---------------------\n\t  FINAL  :\t %s' % final_status 
        return final_status

    def generateLigPdbqt(self, filelist, GUIcallback=None):
        """callback is a function that is called at every step...
        """
        pass


    def checkPdbqt(self, fname):
        """ 
            check if the file is a valid AutoDock(Vina) file (mode):
                - 'lig' : formatted ligand file
                - 'rec' : target structure file
                - 'flex': formatted flexible residue(s)
                - 'result' : a Vina result or a PDBQT+ (ad, vina)
                - 'error'  : an error has been catched ( see 'error' key)
            return dictionary { 'type' : found, 'error' : error }
        FIXME : replace checkPdbqtList code?
        """
        _type = None
        error = ''
        try:
            data = getLines(fname)
            if len(data) == 0:
                _type = 'empty'
            for l in data:
                if l.startswith('BEGIN_RES'):
                    _type = 'flex'
                    break
                elif l.startswith('ROOT'):
                    _type = 'lig'
                    break
                elif l.startswith('MODEL'):
                    _type = 'result'
                    break
                elif 'ADVS' in l:
                    _type = 'result'
                    break
                elif l.startswith('ATOM') or l.startswith('HETATM'):
                    _type = 'rec'
                    # if no keywords have been found so far
                    # a PDBQT can be only a rec file
                    break
        except: 
            _type = 'error'
            error = 'file_error [%s]: %s' % (fname, exc_info()[1] )
        return {'type': _type, 'error' : error}

    def checkPdbqtList(self, filelist):
        """ 
            check if the file is a valid AutoDock(Vina) file (mode):
                - 'lig' : formatted ligand file
                - 'rec' : target structure file
                - 'flex': formatted flexible residue(s)
            return dictionary { lig, rec, flex, error}
        """
        lig = []
        rec = []
        flex = []
        result = []
        error = []
        for f in filelist:
            found = None
            try:
                data = getLines(f)
                for l in data:
                    if l.startswith('BEGIN_RES'):
                        found = 'flex'
                        flex.append(f)
                        break
                    elif l.startswith('ROOT'):
                        found = 'lig'
                        lig.append(f)
                        break
                    elif l.startswith('MODEL'):
                        found = 'result'
                        result.append(f)
                    elif 'ADVS' in l:
                        result.append(f)
                        found = 'result'
                    elif l.startswith('ATOM') or l.startswith('HETATM'):
                        found = 'rec'
                        rec.append(f)
                        # if no keywords have been found so far
                        # a PDBQT can be only a rec file
                        break
            except: 
                found = 'file_error [%s]: %s' % (f, exc_info()[1] )
                error.append([f, found])
        return {'lig' : lig, 'rec': rec, 'flex':flex, 'result': result, 'error': error}        

    def addLigandList(self, filelist, prefilter=False, GUI = None, stopcheck = None, showpercent=None):
        """ accept a list of files to be registered in the 
            Great Book of Ligands
            
            prefilter (true,false) : if true, ligands not 
                                     satisfying filtering criteria 
                                     would not be imported in the session 
            return a dictionary:
                'accepted' : accepted
                'duplicate': already present
                'filtered' : not matching filter criteria
                'rejected' : problematic files
        """
        def avg(lst):
            return sum(lst)/float(len(lst))
        accepted  = []
        rejected = { 'error' : [] }
        # return {'lig' : lig, 'rec': rec, 'flex':flex, 'result': result, 'error': error}
        c = 1
        #gc.disable()
        for f in filelist:
            # check if it is a valid PDBQT
            report = self.checkPdbqt(f)
            _type = report['type']
            error = report['error']
            if _type == 'lig': # valid ligand PDBQT
                response = self.addLigand(f, prefilter=prefilter, skipupdate=True)
                #   n {'accepted': is_wanted, 'reason': reason}  
                if response['accepted']:
                    accepted.append((f, response['name']))
                else:
                    rejected['error'].append([f, response['reason']])
            else: # not valid file
                if not _type in rejected.keys():
                    rejected[_type] = []
                rejected[_type].append([f, error])
            c += 1
            # check stop
            if not stopcheck == None:
                if stopcheck():
                    break
            # update progress
            if not showpercent == None:
                pc = percent(c, len(filelist) )
                showpercent(pc)
            # update GUI
            if not GUI == None:
                GUI.update()
        # NOTE THAT THIS TAKES A WHILE!
        #gc.enable()
        #gc.collect()
        self.updateStatus()
        #print "DEBUG WRITING JSON"
        #writejson('_debug_LigBook.log', self.LigBook)
        return {'accepted': accepted, 'rejected': rejected }

    def addLigand(self, ligand, prefilter=False, skipupdate=False):
        """ accept a ligand fileto be registered in the 
            Great Book of Ligands
            
            prefilter (true,false) : if true, ligands not 
                                     satisfying filtering criteria 
                                     would not be imported in the session 

            report the exit status of the ligand registration {accepted:10, rejected :'reason'}
        """ 
        lig_data = self.extractLigProperties(ligand)
        if not lig_data['success']:
            return { 'accepted': False, 'reason': lig_data['reason'] }
        name = lig_data['name']
        if prefilter:
            pass_filter = self.filterLigProp(**lig_data)
        else:
            pass_filter = True
        lig_data['accepted'] = pass_filter
        is_wanted = False
        if prefilter and not pass_filter:
            reason = 'filtered'
        else:
            #reason = 'new'
            #is_wanted = True
            #try:
            #    found = self.LigBook.get(name)
            if self.LigBook.get(name):
                #if not name in self.LigBook.keys():
                # potential duplicate
                #print "potential duplicate...",
                if self.LigBook[name]['filename'] == lig_data['filename']:
                    # real duplicate
                    #print "real duplicate"
                    reason = 'duplicate'
                else:
                    is_wanted = True
                    # omonimy
                    #print "same name, different mols"
                    c = 1
                    suggest = "%s_v%d" % (name, c)
                    while suggest in self.LigBook.keys():
                        c += 1
                        suggest = "%s_v%d" % (name, c)
                        if c==99:
                            #print "addLigand> too many attempts guessing name", suggest
                            is_wanted = False
                            reason = 'too many name guessing attempts: %s' % suggest
                            break
                    if is_wanted: 
                        name = suggest
                        reason = 'homonimy avoided'
                        #print ": found suggested name:",suggest
                        lig_data['name'] = name
            #except:
            else:
                # new molecule
                is_wanted = True
                reason = 'new'
        if is_wanted:
            self.registerLigand(action='add', **lig_data)
        if not skipupdate:
            self.updateStatus()
        return {'accepted': is_wanted, 'reason': reason, 'name': name} 

    def addReceptorList(self, receptor_files=None, receptor_flex_pairs_list=None): 
        """ accept a list of PDBQT to be included in receptor's list
            - scan the list
            - reject ligs
            - identify rec, rigid_rec, flex
            - attempt to combine...?

            return a dictionary:
                'accepted' : accepted
                'duplicate': already present
                'rejected' : problematic files

        """
        accepted = []
        rejected = []
        # clean up the list of PDBQT (lig, rec, flex)
        checked_files = self.checkPdbqtList(receptor_files)
        for l in checked_files['lig']:
            rejected.append([l, 'is_ligand'])
        for f in checked_files['error']:
            rejected.append(l)
        # find pairs of rec+flex, if any
        rec_flex_pair = self.findRecFlexPairs(mode='name', **checked_files)
        for p in rec_flex_pair:
            r = p[0]
            f = p[1]
            response = self.addReceptor(receptor = r, flex=f)
            if response['accepted']:
                #print "RESPONSE", response
                #item = [response['name'], p]
                #print "ITEM>", item
                accepted.append([response['name'], p])
            else:
                rejected.append([response['reason'], r, f])
        self.updateStatus()
        #print "addReceptorList> ACCEPTED", accepted
        return {'accepted': accepted, 'rejected': rejected}
    
    def findRecFlexPairs(self, mode='name', **files):
        """ from a dictionary of files (generated with checkPdbqtList)
            try to identify if there are rec+flex pairs

            - mode 'name'   ('_rigid', '_flex')
            - mode 'coord' ( 'CA' connected with two atoms)

            WARNING: if '*_rigid.pdbqt' and '*_flex.pdbqt'
                     are generated there is no guarantee 
                     of actual correspondence between the two!

                    Raccoon generation should avoid this problems:
                        
                        1jff.pdbqt -> (B:THR276) -> 1jff_B-THR276_rigid.pdbqt
                                                    1jff_B-THR276_flex.pdbqt

                        1jff.pdbqt -> (B:THR276, -> 1jff_B-THR276_B-HIS229_rigid.pdbqt
                                       B:HIS229)    1jff_B-THR276_B-HIS229_flex.pdbqt
        """
        pairs = []
        if mode == 'name':
            for r in files['rec']:
                rname = os.path.basename(r)
                rname = rname[:-12]
                flex_match = ''
                for f in files['flex']:
                    fname = os.path.basename(f)
                    fname = fname[:-11]
                    if fname == rname:
                        flex_match = f
                        break
                pairs.append( [r, flex_match] )
        elif mode =='coord':
            print "findRecFlexPairs> coord pairing Rec+Flex [ not implemented yet ]"
        return pairs

    def addReceptor(self, receptor, flex=None):
        """ add the receptor to the session"""

        rec_data = self.getRecData(receptor, flex)
        #
        # XXX filter here receptor against allowed atypes/special parm file
        #
        rec_data['accepted'] = True
        #
        name = rec_data['name']
        is_wanted = False
        if not name in self.RecBook.keys():
            is_wanted = True
            reason = 'new'
        else:
            if self.RecBook[name]['filename'] == rec_data['filename']:
                # real duplicate
                print "real duplicate"
                reason = 'duplicate'
            else:
                is_wanted = True
                # omonimy
                #print "omonimy"
                c = 1
                suggest = "%s_v%d" % (name, c)
                while suggest in self.LigBook.keys():
                    c += 1
                    suggest = "%s_v%d" % (name, c)
                    if c == 99:
                        #print "addReceptor> too many attempts to find name", suggest
                        is_wanted = False
                        reason = 'no available name up to %s' % suggest
                        break
                if is_wanted: 
                    #print ": found suggested name:",suggest
                    rec_data['name'] = suggest
                    name = suggest
                    reason = 'homonimy avoided'
        if is_wanted:
            self.registerReceptor(action='add', **rec_data)
        return { 'accepted' : is_wanted, 'reason': reason, 'name': name}

    def getRecData(self, receptor, flex=None):
        """ get receptor data and incorporate flex residues if present"""
        rec_data = self.extractRecProperties(receptor)
        rec_data['is_flexible'] = False
        if flex:
            flex_res_data = self.extractRecProperties(flex)
            rec_data['flex_res_file'] = flex
            rec_data['chains'] = sorted(set(rec_data['chains']+flex_res_data['chains']))
            rec_data['residues'] = sorted(set(rec_data['residues']+flex_res_data['residues']))
            #rec_data['residues'] += flex_res_data['residues']
            rec_data['flex_res'] = sorted(flex_res_data['residues'])
            rec_data['flex_atypes'] = flex_res_data['atypes']
            rec_data['flex_atypes_unknown'] = flex_res_data['atypes_unknown']
            rec_data['flex_tors'] = getPdbqtTors(flex)
            rec_data['is_flexible'] = True
            # C:THR276 -> C-THR276
            flex_names = [ i.replace(":","-") for i in sorted(flex_res_data['residues']) ]
            rec_data['name'] += "_"+"_".join(flex_names) 
        return rec_data


    def getRecFiles(self, receptor):
        """ return the file list of the current receptor
            (1 or 2 files depending on the flex res)
        """
        rec_data = self.RecBook[receptor]
        recfiles = [ rec_data['filename'] ]
        if rec_data['is_flexible']:
            recfiles.append( rec_data['flex_res_file'] )
        return recfiles


    def generateFlexRes(self):
        # - generate the rigid+flex pair
        # - remove the original FULL_RIGID
        # - import rigid+flex_pair
        pass

    def extractRecProperties(self,filename):
        # -receptor types
        # -residues
        # -residues in the grid?
        name = filetoname(filename)
        data = getLines(filename)
        atoms = getAtoms(data)
        rec_structure = getReceptorResidues(data=atoms)
        rec_types = []
        rec_types_unk = []
        chains = rec_structure.keys()
        res_list = []
        for c in chains:
            res = rec_structure[c]
            for r in res:
                res_list.append( ("%s:%s" % (c.strip(),r)) )
        for a in atoms:          
            at = getAtype(a)
            if at in self.atypelistRec:
                if not at in rec_types:
                    rec_types.append(at)
            else:
                rec_types_unk.append(at)
        return {'name': name,
                'atypes':rec_types,
                'atypes_unknown': rec_types_unk,
                'structure': rec_structure, 
                'chains' : chains,
                'residues': res_list,
                'filename': filename}

    def registerLigand(self, action='add', **lig_data):
        """ register the ligand in the Great Book of Ligands
            action can be 'add' or 'del' 
        
            TODO: include different registration methods, 
                   i.e. Sqlite3, remote Opal...
        """
        name = lig_data['name']
        if action =='add':
            self.LigBook[name] = lig_data
            if self.LigBook[name]['accepted']:
                self.updateAtomPoolLig(action=action, **lig_data)
        elif action =='del':
            if self.LigBook[name]['accepted']:
                self.updateAtomPoolLig(action=action, **lig_data)
            del self.LigBook[name]

    def registerReceptor(self,action='add', **rec_data):
        """ register the receptor in the Great Book of Receptors

        """
        name = rec_data['name']
        if action =='add':
            self.RecBook[name] = rec_data
        elif action =='del':
            del selfRecBook[name]
        self.updateAtomPoolRecUnk(action=action, **rec_data)

    def updateAtomPoolRecUnk(self, action='add', **rec_data):
        """ update receptor unknown atom types """
        #print "updateAtomPoolRecUnk> xxx not working xxx"
        pass
    # XXX probably useless...

    def updateAtomPoolLig(self, action='add', **lig_data):
        """ update the pool of atom types (to cache maps, for example)
            action:  'add'  -> ligand is added (atypes incremented)
                     'del'  -> ligand is deleted (atypes decremented)

            the atom pool is going to be updated only if the ligand is accepted.???
        """
        accepted = lig_data['accepted']
        if action =='add':
            value = 1
        elif action =='del':
            value = -1
        for a in lig_data['atypes']:
            self.atypelist[a][0] += (value * accepted)
        if len(lig_data['atypes_unknown'])>0:
            self.updateAtomPoolLigUnk(action=action, **lig_data)

    def updateAtomPoolLigUnk(self, action='add', **lig_data):
        """ update the count of the unknown atom types and the list of 
            ligand filenames containing them
        """
        name = lig_data['name']
        filename = self.LigBook[name]['filename']
        for a in lig_data['atypes_unknown']:
            if action=='add' and lig_data['accepted']:
                if not a in self.unknownAtypes.keys():
                    self.unknownAtypes[a] = []
                self.unknownAtypes[a].append(filename)
            elif action=='del':
                self.unknownAtypes[a].remove(filename)
                if len(self.unknownAtypes[a]) == 0:
                    del self.unknownAtypes[a]

    def extractLigProperties(self, filename):
        """parse PDBQT and returns ligand properties"""
        try:
            data = getLines(filename)
        except:
            print "extractLigProperties> error parsing |%s|" % filename
            return {'success':False, 'reason': exc_info()[1] }
        atype_list = []
        acc_list = ['OA', 'NA', 'SA']
        don_list = ['N', 'OA', 'NA']
        hba = hbd = 0
        hbd_candidate = []
        hbd_hd = []
        heavy = 0
        mw = 0
        unknown_type = []
        tors =0
        name = filetoname(filename)
        #basename = os.path.basename(filename)
        #print self.atypelist
        #name = os.path.splitext(basename)[0]
        for l in data:
            if isAtom(l):
                at = getAtype(l)
                if at in self.atypelist:
                    if not at in atype_list: atype_list.append(at) # collect atom type
                    if at in acc_list: hba+=1 # hba
                    if at in don_list: # hbd
                        hbd_candidate.append(l)
                    if at =='HD':
                        hbd_hd.append(l)
                    else:
                        heavy +=1
                    mw += self.atypelist[at][1]
                else:
                    unknown_type.append(at)
            elif 'TORSDOF' in l:
                tors=int(l.split()[1])
        for c in hbd_candidate:
            mated = 0
            for h in hbd_hd:
                if dist(h,c,sq=1) < self.hcovbond:
                    hbd+=1
                    break
        return {'name'   : name, 'tors'   : tors, 
                'hba'    : hba,  'hbd'    : hbd, 
                'mw'     : mw,   'nat'    : heavy,
                'atypes' : atype_list,
                'atypes_unknown' : unknown_type,
                'filename'       : filename,
                'success'        : True}

    def filterLigands(self,lig_list=None, previewOnly=False):
        """ filter a list of ligands
            if the list is not provided, all ligands 
            in the current session will be filtered

            if previewOnly, only the count of ligands passing
            the filters will be reported
        """
        c = 0
        if not lig_list:
            lig_list = self.LigBook.keys()
        for l in lig_list:
            lig_data = self.LigBook[l]
            if previewOnly:
                c += self.filterLigProp(**lig_data)
            else:
                pre = lig_data['accepted'] # pre-filter acceptance
                self.LigBook[l]['accepted'] = self.filterLigProp(**lig_data)
                post = self.LigBook[l]['accepted'] # post-filter acceptance
                if not pre == post: # the status of the ligand changed
                    if post:
                        self.updateAtomPoolLig(action='add', **lig_data)
                    else:
                        self.updateAtomPoolLig(action='del', **lig_data)
        if previewOnly: return c

    def filterLigProp(self, **lig_data):
        hba = self.filterSettings['hba']
        hbd = self.filterSettings['hbd']
        mw = self.filterSettings['mw']
        tors = self.filterSettings['tors']
        nat = self.filterSettings['nat']
        unk = self.filterSettings['accept_unk_atypes']
        if (hba[0] <= lig_data['hba'] <= hba[1]):
            if (hbd[0] <= lig_data['hbd'] <= hbd[1]):
                if (mw[0] <= lig_data['mw'] <= mw[1]):
                    if (tors[0] <= lig_data['tors'] <= tors[1]):
                        if (nat[0] <= lig_data['nat'] <= nat[1]):
                            if len(lig_data['atypes_unknown'])<1 or unk:
                                return True
        return False

    def ligToBox(self, ligand, tolerance=5):
        """ accept a ligand or a AL result (file or lines list) and returns
            the bounding box and the center plus a tolerance (angstroms)
        """
        try:
            #tolerance = 0
            atoms = getAtoms(getLines(ligand))
            lig_bbox = boundingBox(atoms, tolerance)
            self.ligBox = lig_bbox
            return True
        except:
            print "ligToBox> ERROR reading ligand [%s] : [%s]" % (ligand, exc_info()[1])
            return False
            

    def importGpfTemplate(self, gpf):
        """read a GPF file template to set values in the 
           grid box of current session
        """
        try:
            gpf_data = getGPFdata(gpf)
            self.autogrid_parameters['gridcenter'] = gpf_data['center']
            self.autogrid_parameters['npts']       = gpf_data['pts']
            self.autogrid_parameters['spacing']    = gpf_data['res']
            self.autogrid_parameters['smooth']     = gpf_data['smooth']
            self.autogrid_parameters['dielectric'] = gpf_data['dielectric']
            self.gridBoxFromGpf(gpf_data)
            return True
        except:
            print "importGpfTemplate> ERROR reading data file %s: %s" % (gpf, exc_info()[1])
            return False


    def importDpfTemplate(self, dpf):
        """read a DPF file template to set values in the 
           parmeter search
        """
        # XXX INCOMPLETE NOT WORKING!!
        try:
            dpf_data = getPFdata(gpf)
            self.autogrid_parameters['gridcenter'] = gpf_data['center']
            self.autogrid_parameters['npts']       = gpf_data['pts']
            self.autogrid_parameters['spacing']    = gpf_data['res']
            self.autogrid_parameters['smooth']     = gpf_data['smooth']
            self.autogrid_parameters['dielectric'] = gpf_data['dielectric']
            self.gridBoxFromGpf(gpf_data)
            return True
        except:
            print "importDpfTemplate> ERROR reading data file %s: %s" % (gpf, exc_info()[1])
            retu



    def gridBoxFromGpf(self, gpf_data):
        """set the grid box from an AutoDock GPF """
        size = [ gpf_data['g_max'][0] - gpf_data['g_min'][0],
                 gpf_data['g_max'][1] - gpf_data['g_min'][1],
                 gpf_data['g_max'][2] - gpf_data['g_min'][2] ]

        self.setBoxSize( size )
        self.setBoxCenter( gpf_data['center'])
        return True

    def gridBoxFromConf(self, conf):
        """set the grid box from a Vina config file
           vina conf files don't contain any mandatory parameter,
           therefore a check is provided for missing values 

        """
        # XXX TODO this should change also other keyword settings!
        try:
        #if True:
            conf_data = getVinaConfData(conf)
            center = [ conf_data['center_x'],  conf_data['center_y'],  conf_data['center_z'] ]
            size = [ conf_data['size_x'],  conf_data['size_y'],  conf_data['size_z'] ]
            #print "XXX", center, size
            c = 0
            print center, size
            missing = False
            for v in center:
                if v == None:
                    missing = True
                    break
            if not missing:
                #print self.setBoxCenter, type(self.setBoxCenter)
                self.setBoxCenter( center )
                c +=1
            missing = False
            for v in size:
                if v == None:
                    size = True
                    break
            if not missing:
                self.setBoxSize( size )
                c +=1
            if c==1:
                if self.debug: print "gridBoxFromConf> WARNING incomplete data in file %s " % (conf)
            elif c==0:
                raise "No values found"
            return conf_data

        #else:
        except:
            print "gridBoxFromConf> ERROR reading data file %s : %s" % (conf, exc_info()[1])
            return False

    def gridBox(self):
        return {'center' : self.box_center,
                'size'   : self.box_size,
               }

    def gridBoxFromLigand(self, ligand, tolerance=5):
        """
        used to set grid center and size by using a ligand pdb/qt or 
        an AutoLigand output
        a tolerance can be added (Angstrom)
        """
        try:
            #ligand_lines = getLines(ligand)
    
            self.ligToBox(ligand, tolerance=tolerance)

            self.ligBox['file'] = ligand

            size = [ self.ligBox['x'][1] -  self.ligBox['x'][0],
                     self.ligBox['y'][1] -  self.ligBox['y'][0],
                     self.ligBox['z'][1] -  self.ligBox['z'][0] ]
    
            self.setBoxSize( size )
            self.setBoxCenter( self.ligBox['center'] ) 
        except:
            print "gridBoxFromLigand> ERROR reading ligand [%s] : %s" % (ligand, exc_info()[1])
            return False


    def getVinaSettingsFromConf(self,config):
        """ extract search and parms settings from a config file

        """
        accepted = [ 'exhaustiveness', 'num_modes', 'energy_range' ]

        for k in accepted:    
            if k in conf_data.keys():
                self.vina_settings[k] = conf_data[k]

    def AutoDockMakeDpf(self, ligand, receptor, settings = None):
        ''' build the dpf for ligand+receptor using the
            common settings in self.autodock_parameters{}

            the dpf is build in a modular fashion:
                    generic
                    ligand
                    search(ga,sa)
                    local(ls, None)
                    clustering(analysis,None)
        '''
        def generic_settings():
            # generic settings
            source = current_dpf_settings['generic']
            dpf.append( 'autodock_parameter_version %s' % 
                        source['autodock_parameter_version'] )
            if not source['parameter_file'] == None:
                parfile = os.path.basename( source['parameter_file'] )
                dpf.append( 'parameter_file %s' %  parfile )
            dpf.append( 'outlev %s' %  source['outlev'] )
            if source['intelec']:
                dpf.append('intelec')
            if current_dpf_settings['search_mode'] == 'sa': seeding = 'pid'
            else: seeding  = 'pid time'
            dpf.append('seed %s' % seeding)
            dpf.append('unbound_model %s' % source['unbound_model'])

        def ligand_settings():
            # XXX UNKNOWN ATOM TYPES ARE NOT HANDLED YET!
            ltypes = sorted(self.LigBook[ligand]['atypes'])
            if 'flex_res' in self.RecBook[receptor].keys():
                ltypes = sorted(list(set(ltypes + self.RecBook[receptor]['flex_atypes'] )))
            dpf.append( 'ligand_types ' + " ".join(ltypes) )
            dpf.append( 'fld %s.maps.fld' % rec_name)
            for a in ltypes:
                line = 'map %s.%s.map' % (rec_name, a)
                dpf.append(line)
            dpf.append( "elecmap %s.e.map" % rec_name )
            dpf.append( "desolvmap %s.d.map" % rec_name )
            dpf.append( 'move %s' % lig_file )
            if self.RecBook[receptor]['is_flexible']: # in self.RecBook[receptor].keys():
                dpf.append( 'flexres %s' % (os.path.basename(self.RecBook[receptor]['flex_res_file'])))
            dpf.append( 'about %2.3f %2.3f %2.3f' % tuple(about) )    

        def ga_settings():
            source =  current_dpf_settings['ga']
            for k in source['KEYWORD_ORDER']:
                dpf.append( "%s %s" % (k, source[k]))

        def sa_settings():
            source =  current_dpf_settings['sa']
            for k in source['KEYWORD_ORDER']:
                dpf.append( "%s %s" % (k, source[k]))

        def ls_settings():
            source =  current_dpf_settings['ls']
            for k in source['KEYWORD_ORDER']:
                if k =='ga_pop_size':
                    if current_dpf_settings['search_mode'] =='ls':
                        dpf.append( "%s %s" % (k, source[k]))
                elif k =='ls_search_freq':
                    if not current_dpf_settings['search_mode'] == 'ls':
                        dpf.append( "%s %s" % (k, source[k]))
                else:
                    dpf.append( "%s %s" % (k, source[k]))

        def set_docking_runs():
            # depending on the self.autodock_search value
            # set the opportune run_command (ga_run, do_local_only)

            # sa : (runs:xx, simanneal)
            # ga : (do_global_only:xx)
            # lga: (ga_run:xx)
            # ls : (do_local_only:xx)
            starting_keyword = { 'lga' : 'ga_run %d',
                                 'ga'  : 'do_global_only %d',
                                 'sa'  : 'runs %d\nsimanneal', # XXX likely to change, check AD 4.3
                                 'ls'  : 'do_local_only %d',
                                 }
            sm = current_dpf_settings['search_mode']
            dpf.append( starting_keyword[sm] % runs )
             
        def clustering_settings():
            source = current_dpf_settings['clustering']
            for k in source['KEYWORD_ORDER']:
                dpf.append("%s %s" % (k, source[k]))

        # starting...
        dpf = []
        if settings == None:
            settings = self.autodock_parameters['dpf_mode']
        if settings == 'template':
            current_dpf_settings = self.autodock_parameters.copy()
        elif settings == 'auto':
            settings = self.dpfComplexityEstimator(lig = lig, 
                rec = rec, grid = self.autodock_parameters['complexity_map'])
        # total runs
        runs = current_dpf_settings['runs']
        # search mode
        search_mode = current_dpf_settings['search_mode']
        # lig properties
        lig_file = os.path.basename( self.LigBook[ligand]['filename'])
        about = getLigAbout( self.LigBook[ligand]['filename'] )
        # rec properties
        rec_file = os.path.basename( self.RecBook[receptor]['filename'] )
        rec_name = os.path.splitext( rec_file )[0]
        generic_settings()
        ligand_settings()
        if search_mode == 'lga':
            ga_settings()
            ls_settings()
        elif search_mode =='ga':
            ga_settings()
        elif search_mode =='sa':
            sa_settings()
        elif search_mode =='ls':
            ls_settings()
        set_docking_runs()
        if current_dpf_settings['do_clustering']:
            clustering_settings()
        return dpf


    def AutoDockMakeGpf(self, receptor, ligand=None, types=None):
        """
            generate GPF for ligand/receptor combination
        """
        print "AutoDockMakeGpf> called with [LIG:%s] [REC:%s] [TYPES:%s]" %  (ligand, receptor, types)
        if ligand == None and types == None:
            print "AutoDockMakeGpf> ERROR no ligand, no types specified"
            return False
        current_gpf = self.autogrid_parameters.copy()

        # ligand atom types
        if ligand:
            # XXX BUG HERE! no unkAtypes recognized!
            ltypes = self.LigBook[ligand]['atypes']
        else:
            ltypes = types
        if self.RecBook[receptor]['is_flexible']:
            #rec_data['flex_atypes'] = flex_res_data['atypes']
            ltypes = list(set(ltypes+ self.RecBook[receptor]['flex_atypes']))
        ltypes = sorted(ltypes)

        # receptor atom types
        rtypes = sorted(self.RecBook[receptor]['atypes'])

        current_gpf['ligand_types']   = " ".join(ltypes)
        current_gpf['receptor_types'] = " ".join(rtypes)
        current_gpf['receptor'] = os.path.basename( self.RecBook[receptor]['filename'] )

        rec_name = os.path.splitext(current_gpf['receptor'])[0]
            
        gpf_file = []
        for k in self.autogrid_parameters['KEYWORD_ORDER']:
        # XXX BUG HERE! missing parameter file code!
            if k == 'gridfld':
                gpf_file.append( "gridfld %s.maps.fld" % (rec_name) )
            elif k == 'gridcenter':
                gpf_file.append( "%s %2.3f %2.3f %2.3f" % ( tuple([k]+current_gpf[k]) ) )
            elif k == 'npts':
                gpf_file.append( "%s %d %d %d" % ( tuple([k]+current_gpf[k]) ) )
            elif k == 'map':
                for a in ltypes:
                    line = 'map %s.%s.map' % (rec_name, a)
                    gpf_file.append(line)
                elec = "elecmap %s.e.map" % rec_name
                desolv = "dsolvmap %s.d.map" % rec_name
                gpf_file.append(elec)
                gpf_file.append(desolv)
            else:
                line = "%s %s" % (k, current_gpf[k])
                gpf_file.append(line)
        return gpf_file
        

    def VinaGenConf(self, ligand=None, receptor=None, raw=False):
        """
            generate the vina config file
        """
        print "VinaGenConf> called with", ligand, receptor
        vina_settings = self.vina_settings.copy()
        vina_settings['center_x']
        if raw:
            config = {}
        else:
            config = []
        if not ligand==None:
            lig = os.path.basename(self.LigBook[ligand]['filename'])
            config.append('ligand = %s' % lig)
        if not receptor == None:
            rec = os.path.basename(self.RecBook[receptor]['filename'])
            if raw: config['receptor'] = rec
            else: config.append('receptor = %s' % rec)
            if self.RecBook[receptor]['is_flexible']:
                flex = os.path.basename(self.RecBook[receptor]['flex_res_file'])
                if raw: config['flex'] = flex
                else: config.append('flex = %s' % flex)
        for k in vina_settings['KEYWORD_ORDER']:
            #print "VinaGenConf> kw[%s] value[%s]" % (k,vina_settings[k])
            if k in vina_settings['OPTIONAL']:
                if vina_settings['OPTIONAL'][k]:
                    if raw : config[k] = vina_settings[k]
                    else:    config.append('%s = %s' % (k, vina_settings[k]) )
            else:
                if raw : config[k] = vina_settings[k]
                else:    config.append('%s = %s' % (k, vina_settings[k]) )
                #config.append('%s = %s' % (k, vina_settings[k]) )
        return config



    def makeLogFunction(self):
        pass

    def TheFunction(self, callback=None):

        # - MAIN_DIR
        #      |
        #      |---REC_1_DIR
        #      |      |
        #      |      |-MAPS [opt,AD-only]
        #      |      |-[ split_suff ]- LIG_1_REC_1_DIR
        #      |      |-[ split_suff ]- LIG_2_REC_1_DIR
        #      |      ...
        #      |
        #      |---REC_2_DIR
        #      |      |
        #      |      |-MAPS [opt,AD-only]
        #      |      |-LIG_1_REC_2_DIR
        #      |      |-LIG_2_REC_2_DIR
        #      |      ...

        # create REC dir
        #   - (A) copy rec file
        #   - (B) calculate grid maps ( + parm file )
        
        # create LIG dir ( + split_number )
        #   - copy lig file
        #   - copy flex file
        #   - make DPF file        ( + parm file)
        #   - (A) make GPF         ( + parm file)
        #   - (B) copy/link maps
        #   - create single_job script

        # create master script
        # 
        # create package
        #
        #
        # Directory naming flow
        # ---------------------
        #
        # current_dir = OUTPUT_DIR
        # 
        #   for r in rec:
        #
        #       rec_dir = OUTPUT_DIR + REC
        #
        #       for l in lig:
        #
        #           lig_dir = rec_dir + SPLIT + LIG
        #

        # get the initial data and freeze static numbers
        ligands = self.ligands()
        receptors = self.receptors()
        lig_types = self.currentLigAtypes()

        self.TOTAL_LIGANDS = len(ligands) # useful for self.makeLigDir!

        # naming section
        cached_maps_dir_name = 'maps'
        gpf_suffix = '_all_maps.gpf'
  
        #self.autogrid_mode = 'always' # 'now' or 'never' (C) 1960 Elvis

        print "TheFunction> start"
        # XXX Numbering voodoo for percentages:
        # tot = rec# * lig# ?
        #       count autogrid step?
        # XXX 
        for rec in receptors: # XXX receptor loop XXX 
            self._recdir = self.makeDir(self.output_dir['path'], rec)
            self._current_rec = rec
            if not self._recdir:
                print "TheFunction> error in creating receptor dir ABORTING"
                return False
            # check map operations
            if self.mode == 'autodock':
                if self.autogrid_mode == 'always':
                    # self._map_dir is used during the calculation
                    # to track the source of the map files
                    # it is populated by:
                    #     - calculateCacheMaps() -> AutGrid run inside Raccoon
                    #     - copyCacheMaps()      -> pre-calc maps are copied from the specified dir
                    self._map_dir = None
                else:
                    self._map_dir = self.makeDir(self._recdir, cached_maps_dir_name)
                    if self.autogrid_mode == 'now':     # Raccoon maps
                        self.calculateCacheMaps(mapdir=self._map_dir, lig_types=lig_types)
                    elif self.autogrid_mode == 'never': # pre-cached maps
                        print self._map_dir, lig_types
                        self.copyCacheMaps(target=self._map_dir, lig_types=lig_types, file_policy ='copy')
            self.LIGAND_COUNTER = 0
            for lig in ligands: # 
                self._current_lig = lig # XXX possibly useless
                self._curr_lig_dir = self.makeLigDir(lig)
                # copy receptor rigid+flex
                self.copyRecFiles(rec, self._curr_lig_dir)
                # copy ligand file and flex if necessary
                self.copyLigFiles(lig, self._curr_lig_dir)
                if self.mode == 'autodock':
                    #   provide map data (GPF/cached)
                    if self.autogrid_mode == 'always':
                        self.prepareLigGpf(path=self._curr_lig_dir, rec=rec, lig=lig)
                    else:
                        self.copyCacheMaps(self._map_dir, lig_types, self.autogrid_map_file)
                    # generate DPF
                    self.prepareLigDpf(path=self._curr_lig_dir, rec=rec, lig=lig)
                    # copy Parmfile if necessary
                    # XXX self.copyAdParmFile()
                elif self.mode == 'vina':
                    self.prepareLigVina(path=self._curr_lig_dir, rec=rec, lig=lig)
                # update the jobs list status...
                # XXX store the lig_dir for the job script
                self.LIGAND_COUNTER += 1

            # XXX update the master-job list status 
            # and generate the actual script here


    def prepareLigVina(self, path, rec, lig, fname=None):
        """ generate GPF for the lig/rec combination"""
        conf = self.VinaGenConf(ligand=lig, receptor=rec)
        if lig:
            conf_filename = path + os.sep + ('%s_%s.conf' % (lig, rec) )
        else:
            conf_filename = path + os.sep + fname
        writeList( conf_filename, conf, addNewLine=True)
        return conf_filename
        

    #def provideMapData(self, lig, rec=None):
    #    """handle the grid data issue,
    #    """
    #    self._current_rec # curent receptor that is going processed
    #    self._current_lig # current lig processed

    def calculateCacheMaps(self, mapdir, rec, lig_types):
        """ run AutoGrid n the to calculate grid maps on the atom 
            types requested for chaching
        """
        # prepare the AutoGrid calculation 
        gpf = self.prepareCacheMapCalc(path=mapdir, rec=rec, lig_types=lig_types)
        # run AutoGrid at the specified path
        self.runAutoGrid(path, gpf)
        # self.autogrid_maps = {} # { 'A': 'protein.A.map', 'C' : 'protein.C.map', 
        return True


    def prepareCacheMapCalc(self, path, rec, lig_types): 
        """ generate the calculation for caching map files
            - copy receptor files ( + flex )
            - generate GPF for all requested ligand types
        """
        # copy receptor files
        response = self.copyRecFiles( path, rec )
        # XXX if parameter files specified copy it here

        self.copyAdParmFile()
        if response['success']:
            # generate the gpf
            gpf = self.AutoDockMakeGpf(receptor = rec, types=lig_types)
            gpf_filename = self._mapdir + os.sep + rec + gpf_suffix
            writeList( gpf_filename, gpf, addNewLine=True)
            return gpf_filename
        else:
            return False

    def prepareLigGpf(self, path, rec, lig):
        """ generate GPF for the lig/rec combination"""
        gpf = self.AutoDockMakeGpf(receptor = rec, ligand = lig)
        gpf_filename = path + os.sep + rec + '.gpf'
        writeList( gpf_filename, gpf, addNewLine=True)
        return gpf_filename
        
    
    def prepareLigDpf(self,path, rec, lig, settings=None):
        """generate DPF for the lig/rec combination

            'settings' is an option to specify if the DPF will
            be generated:

              - 'template' : by using the same settings template 
                             for every ligand

              - 'auto'     : by adapting the search parameters
                             to the bindig volume and the ligand
        """
        if settings == None and self.autodock_parameters['dpf_mode'] == None:  
            settings = None
        elif settings == 'auto':
            settings = self.dpfComplexityEstimator(lig = lig, 
                rec = rec, grid = self.autodock_parameters['complexity_map'])

        dpf = self.AutoDockMakeDpf(receptor=rec, ligand=lig, settings = None)

        dpf_filename = path + os.sep + "%s_%s"  + '.dpf'
        dpf_filename = dpf_filename % (lig, rec)
        writeList( dpf_filename, dpf, addNewLine=True)
        return dpf_filename
        

    def dpfComplexityEstimator(self, lig, rec, grid=None):
        """ estimate the complexity of the search by analyzing
            the grid box volume and ligand properties
            (+ flex_res, if defined )
        """
        if grid == None:
            grid = self.autodock_parameters['complexity_map'] 
        # XXX not working yet...
        return self.autodock_parameters.copy()
        


    def copyAdParmFile(self, path, filename):
        """copy parameter AD parameter file to requested path
        """
        # XXX it doesn't work yet!
        print "copyAdParmFile> checking if parm.dat requested [NOT WORKING YET]"
        pass

    def runAutoGrid(self, path, gpf, binary=None):
        """run AutoGrid binary in the specified path using
            the GPF specified.
            By default the self.autogrid_bin is used
        """
        # XXX remember to trigger the update of the  self.autogrid_options['complexity_map']
        #     map used to calculate ligand accessibility (usually *.C.map)
        if binary == None:
            binary = self.autogrid_bin
        # cd to path
        # extract basename(gpf)
        # check if gpf is present
        # run autogrid

    def copyCacheMaps(self, target, lig_types = [], file_policy = 'copy'):
        """ copy cache map files in place
            'mode' can be 'copy' or 'link'
            
            this function can be used to copy map files in 
            ligand directories or on cached_map directories
        """
        # self.autogrid_maps = {} # { 'A': 'protein.A.map', 'C' : 'protein.C.map', 
        if file_policy == 'copy':
            copy_func = shutil.copy2
        elif file_policy == 'link':
            copy_func = os.symlink
        for a in lig_types :
            copy_func( self.autogrid_maps[a], target)



    def copyRecFiles(self, rec, target_dir):
        """ copy receptor file and flex_res, if specified
            in the directory specified
        """
        try: 
            shutil.copy2( self.RecBook[rec]['filename'], target_dir)
            reason = 'rigid'
            if self.RecBook[rec]['is_flexible']:
                shutil.copy2( self.RecBook[rec]['flex_res_file'], target_dir)
                reason += '_flex'
            return { 'success': True, 'reason': reason }
        except:
            error = "%s" % exc_info()[1]
            return { 'success': False, 'reason': error }

    def copyLigFiles(self,lig, target_dir):
        """ copy ligand file and flex_res, if specified,
            in the directory specified
        """
        try: 
            shutil.copy2( self.LigBook[lig]['filename'], target_dir)
            reason = 'ligand'
            #if self.RecBook[self._current_rec]['is_flexible']:
            #    shutil.copy2( self.RecBook[self._current_rec]['flex_res_file'], target_dir)
            #    reason += '_flex'
            return { 'success': True, 'reason': reason }
        except:
            error = "%s" % exc_info()[1]
            return { 'success': False, 'reason': error }

        


    def makeDir(self, path, name):
        """ create dir for the generation process"""
        print "path", path
        print "name",name
        dirname = path + os.sep + name
        try:
            os.makedirs(dirname)
            return dirname
        except:
            print "makeDir> ERROR creating dir [%s]: %s" % (dirname, exc_info()[1])
            return False



    def makeLigDir(self, ligand):
        """create the ligand directory, adding 
           the splitting suffix, if necessary
        """
        if not self.generalOpts['generic']['split'] == None:
            split = self.generalOpts['generic']['split']
            if self.TOTAL_LIGANDS <= split:
                suffix = ''
            else:
                # zeropadding = "%%0%dd" % len(str(self.LIGAND_COUNTER/split)) XXX WRONG?
                zeropadding = "%%0%dd" % len(str(self.TOTAL_LIGANDS/split))
                suffix = (zeropadding+os.sep) % (self.LIGAND_COUNTER/split)
        else: suffix = ''
        dir_name = self._recdir+os.sep+suffix+ligand+os.sep
        try:
            os.makedirs(dir_name)
        except:
            print "problem: %s" % exc_info()[1]
            return False    
        return dir_name


if __name__ == '__main__':


    from sys import argv

    # -g  gpf_template_file 
    # -c  config_file
    # -d  dpf_template_file
    # -r  receptor.pdbqt
    # -R  receptor.list
    # -x  flex.pdbqt
    # -l  ligand.pdbqt
    # -L  ligand.list
    # -ld ligand_dir/
    # -rd receptor_dir/


    def usage():
        print "Usage: raccoon -d . -r protein.pdbqt -x"
    lig_list = ['data/lig/ZINC00913760.pdbqt',
                'data/lig/ZINC01365912.pdbqt']

    rec_list = ['data/rec/single/frame_001.pdbqt',
                'data/rec/single/frame_002.pdbqt',
                'data/rec/flex/1JFF_rigid.pdbqt',
                'data/rec/flex/1JFF_flex.pdbqt',
                ]

    xray_lig = 'data/lig/ZINC00913760.pdbqt'

    autoligand = 'data/al/FILL_250out1.pdb'


    gpf_template = 'data/etc/template_without_paramfile.gpf'
    conf_template = 'data/etc/test.conf'
    map_policy = '' # always, now, never

    gpf_center = [ 0.5, -12, 24 ]
    gpf_size   = [ 15.5, 20, 10 ]
    gpf_center_WRONG = [1,2,'a']
    gpf_size_WRONG = [1,2,'a']


    dpf_template = None
    flex_res_names = []
    flex_res_file = ''

    out_dir = 'data/NEW_CLASS_TEST/aaa'
    #out_dir = '/media/iguana/TEST_RACCOON_SPEED/'

    #lig_list = getLines('/media/mammoth/database/zinc/ChEBI/ChEBI_total.2011.8.3/files_pdbqt.lst', doStrip=True)

    test = 'autodock'
    #test = 'vina'


    ##################################################################
    # TESTING 

    raccoon = Raccoon(debug=True)
    # adding a ligand list
    raccoon.setMode('vina')

    print "- importing ligands... ",
    raccoon.addLigandList(lig_list)
    print len(raccoon.ligands())

    # adding a receptor list
    raccoon.addReceptorList(rec_list)
    print "- check receptor status"
    for r in raccoon.RecBook.keys():
        rec = raccoon.RecBook[r]
        if 'flex_res' in rec.keys():
            flex = " %s : %s types(%s)" % (",".join(rec['flex_res']),
                 rec['flex_res_file'], ",".join(rec['flex_atypes'])) 
        else:
            flex = 'None'
        print "\t%s : rigid[%s] \t flex[%s]" % (r,
            raccoon.RecBook[r]['filename'], flex)

    # setting the grid center (tuple, vector...)
    #raccoon.setBoxCenter([1,2,'a'])
    raccoon.setBoxCenter(gpf_center)

    # setting the grid size (tuple, vector...)
    #raccoon.setBoxSize([1,2,'a'])
    raccoon.setBoxSize(gpf_size)

    # setting the output dir
    response = raccoon.setOutputDir(out_dir)
    print "\n- check selected directory properties ( %s : %s ):" % response
    for i in raccoon.output_dir.keys():
        print "\t%s : %s" % (i, raccoon.output_dir[i])
    #self.output_dir['freespace'] = checkDiskSpace(dir_path)


    # testing filtering sets

    # setting custom filter settings
    custom_filter_set = raccoon.filterSettings.copy()
    custom_filter_set['hba'][0] = 28
    custom_filter_set['hbd'][1] = 76  
    custom_filter_set['title'] = 'TESTING'
    raccoon.setFilterSet(customFilter=custom_filter_set)
    print "\n- current filter set", raccoon.filterSettings

    # perform the filter with the current settings
    raccoon.filterLigands()
    print "- previewing ligands passing current filter:",
    print raccoon.filterLigands(previewOnly=True)

    raccoon.filterLigands()
    print "- filtering with '%s'" % (raccoon.filterSettings['title'])
    print "- updating status..."
    status = raccoon.updateStatus(report=True)


    # setting default filter settings (lipinsky)
    raccoon.setFilterSet(filterSet = 'lipinsky')
    print "\n- current filter set ", raccoon.filterSettings
    
    # perform the filter with the current settings
    raccoon.filterLigands()
    print "- filtering with '%s'" % (raccoon.filterSettings['title'])
    print "- updating status..."
    status = raccoon.updateStatus(report=True)


    gpf_source = 'lig' # gpf, lig, al, conf
    gpf_source = 'conf'

    if gpf_source == 'gpf':
        # use template GPF to set center and size"
        print "\n- setting the center with GPF (%s) " % gpf_template
        # raccoon.gridBoxFromGpf(gpf_template)
        raccoon.importGpfTemplate(gpf_template)

        print "\tcenter (%2.3f, %2.3f, %2.3f)" % (raccoon.box_center[0],
                    raccoon.box_center[1], raccoon.box_center[2] )
        print "\tsize   (%2.3f, %2.3f, %2.3f)" % (raccoon.box_size[0],
                    raccoon.box_size[1], raccoon.box_size[2] )

    elif gpf_source == 'lig':
        # use reference ligand to set center and size"
        print "\n- setting center with ligand (%s)" % xray_lig
        raccoon.gridBoxFromLigand(xray_lig, tolerance=5)

        print "\tcenter (%02.3f, %02.3f, %02.3f)" % (raccoon.box_center[0],
                    raccoon.box_center[1], raccoon.box_center[2] )
        print "\tsize   (%02.3f, %02.3f, %02.3f)" % (raccoon.box_size[0],
                    raccoon.box_size[1], raccoon.box_size[2] ) 

    elif gpf_source == 'al':
        # use AutoLigand result to set center and size"
        print "\n- setting center with ligand (%s)" % autoligand
        raccoon.gridBoxFromLigand(autoligand, tolerance=2)

        print "\tcenter (%02.3f, %02.3f, %02.3f)" % (raccoon.box_center[0],
                    raccoon.box_center[1], raccoon.box_center[2] )
        print "\tsize   (%02.3f, %02.3f, %02.3f)" % (raccoon.box_size[0],
                    raccoon.box_size[1], raccoon.box_size[2] ) 

    elif gpf_source == 'conf':
        print '\n- setting center with config file (%s)' % conf_template

        raccoon.gridBoxFromConf(conf_template)
        print "\tcenter (%02.3f, %02.3f, %02.3f)" % (raccoon.box_center[0],
                    raccoon.box_center[1], raccoon.box_center[2] )
        print "\tsize   (%02.3f, %02.3f, %02.3f)" % (raccoon.box_size[0],
                    raccoon.box_size[1], raccoon.box_size[2] ) 
        


    # generate GPF for ligands/rec combinations
    raccoon.autodock_parameters['search_mode'] = 'lga'

    if test == 'autodock':
        raccoon.setMode('autodock')
    elif test =='vina':
        raccoon.setMode('vina')

    print 
    raccoon.TheFunction()
    exit()



    """
    for r in raccoon.receptors():
        print "\n##########\nREC [ %s ]" % ( raccoon.RecBook[r]['name'] )
        for l in raccoon.ligands():
            print "\t - GPF for %s" % l
            settings = { 'center' : raccoon.box_center,
                         'size'   : raccoon.box_size,
                       }
            box = raccoon.gridBox()
            gpf = raccoon.AutoDockMakeGpf(receptor=r, ligand=l)
            outname = "%s_%s.gpf" % (l, r)
            outname = raccoon.output_dir['path']+os.sep+outname
            writeList(outname, gpf, addNewLine=True)
    
            dpf=raccoon.AutoDockMakeDpf(ligand=l, receptor=r)
            outname = "%s_%s.dpf" % (l, r)
            outname = raccoon.output_dir['path']+os.sep+outname
            writeList(outname, dpf, addNewLine=True)

            conf=raccoon.VinaGenConf(ligand=l, receptor=r)
            outname = "%s_%s.conf" % (l, r)
            outname = raccoon.output_dir['path']+os.sep+outname
            writeList(outname, conf, addNewLine=True)
            

    if test == 'autodock':
        # gpf
        pass

        # dpf

    elif test =='vina':
        raccoon.setMode(mode ='vina')
    """





# NOTES
# - leading zeroes for Mol2 http://docs.python.org/release/2.4.4/lib/typesseq-strings.html
# - string.rjust(value, 'padder')
# YELD for ITERATORS: http://docs.python.org/tutorial/classes.html
