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
#!/usr/bin/env python


import sys
from DebugTools import DebugObj
import json, tarfile, urllib2
import AutoDockTools.HelperFunctionsN3P as hf
import os
from datetime import datetime

"""
This file provides the classes for creating Raccoon services.

All services are sub-classes of RaccoonService class that
defines the basic functions and attributes a service should have.

NOTE: To be recognized by the RaccoonServer, services must be added 
      to the dictionary at the end of this file
"""




class RaccoonService(DebugObj):
    """ Base class for Raccoon services.
        Provides:

          self._knownkw      : LIST of know keywords for the configuration
                               of the service

          self._requiredkw   : LIST of minimum set of keywords that need to be 
                               defined for the service to be active

          self.ready         : BOOL of the service passed all validation tests
                               every service must have a self.initService() that
                               check for all requirements for this to be true

          self.config        : DICT containing the configuration of the service;
                               keys in self._knownkwd will be used

          self._srvtype      : STR defining the type of server 

          self._validatekw() : parse the config dictionary 
          self._makeConfigText() : generate the config file of the service using the current
                               service configuration
          self.initService() : initialize the server with the provided configuration dictionary

    """
    def __init__(self, server, debug=False):
        DebugObj.__init__(self, debug)
        self.config = { 'file' : None, 'name' : '', 'comment': '',
                    'service' : None, 'validated' : False}
        # hosting Raccoon server obj
        self.server = server
        # service type
        self._srvtype = None
        # processor, provide the .submit() method
        self.processor = None
        # mandatory kw that need to be set for the service to run
        self._requiredkw = [] 
        # storage for unknown kw
        self._unknownkw = []
        # accepted values for kw (can be empty)
        self._legal_values = {} 
        # text config template
        self._config_template = []
        # service status, when True, it can be initialized
        self.ready = False


    def validateConfig(self, config={}):
        """ validate the config dictionary checking that
            all required kw are presents and that returning
            recognized and unknown keywords
        """
        self.dprint("service current name to validate [%s]" % self.config['name'], new=1)
        # always reset always to default values
        self.config['validated'] = False
        req = 0
        status = { 'accepted' : False, 'reason' : None }
        if 'service' in config.keys():
            if not config['service'] == self._srvtype:
                msg = 'service type mismatch: config[%s] service_obj[%s]'
                msg = msg % (config['service'], self._srvtype) 
                status['reason'] = msg
                self.dprint(msg)
                return False
        else:
            msg = 'server type not defined in the config'
            status['reason'] = msg
            self.dprint(msg)
            return status
        del self._unknownkw[:]
        for k in config.keys():
            if k in self.config:
                if k in self._legal_values.keys():
                    test = self._legal_values[k]
                    if isinstance(test, list):
                        valid = config[k] in test
                    elif isinstance(test, type):
                        valid = False
                        try: 
                            config[k] = test(config[k])
                            valid = True
                        except: pass
                    ## if not config[k] in self._legal_values[k]:
                    if not valid:
                        msg = 'illegal value for kw[%s=%s] (allowed: %s)'
                        #print k, config[k], self._legal_values[k]
                        msg = msg % (k, config[k], self._legal_values[k])
                        status['reason'] = msg
                        self.dprint(msg)
                        return status
                self.config[k] = config[k]
                if k in self._requiredkw:
                    req += 1
            else:
                self.dprint('unknown kw[%s=%s]' % (k,config[k]))
                self._unknownkw.append([k,config[k]])
        if req == len(self._requiredkw):
            self.config['validated'] = True
            self.dprint("Service named [%s] is ready." % self.config['name'])
            status['accepted'] = True
        if len(self._unknownkw):
            print "WARNING: unwknown keywords in service config initialization."
            status['reason'] = 'unkown keywords found'
        return status    
 
    def _makeConfigText(self, template=[]):
        """basic function to generate a config file 
           from the service template

           every service should define a self.makeConfig()
           function built on top of this one
           then add the service-specific customizations
        """
        conf = "\n".join(template)
        conf = conf % self.config
        return conf
        
    def writeServiceConfig(self, fname=None, config_txt=None, force = False):
        """ write the config file on the server """
        status = {'success' : False, 'reason' : None }
        self.dprint("called", new=1, args=1)
        fn = 'writeServiceConfig>'
        # test config dictionary
        if not self.config['validated']:
            msg = 'config not validated'
            status['reason'] = msg
            self.dprint(msg)
            print fn, msg
            return status
        config_txt = self.makeConfig()
        # test filename cases
        if not self.config['file'] == None:
            # service loaded from existing config
            self.dprint('config filename already defined [%s]' % self.config['file'])
            # overwriting original service file
            if self.config['file'] == fname:
                self.dprint( "files saved and to save have same name")
                if not force:
                    msg = 'skipping existing filename'
                    status['reason'] = msg
                    self.dprint(msg)
                    return status
                else:
                    msg = 'updating old config file'
                    self.dprint(msg)
                    status['reason'] = msg
            # writing a (likely) duplicate service 
            elif not self.config['file'] == fname:
                self.dprint( ("pontential service duplicate,"
                             "config loaded from existing "
                             "file[%s]") % self.config['file'])
                if not force:
                    msg = 'potential duplicate services:\n- %s\n- %s\nSkipping...' % (self.config['file'], fname)
                    status['reason'] = msg
                    self.dprint(msg)
                    print fn, msg
                    return status
                else:
                    msg = 'potential duplicate service, proceding'
                    status['reason'] = msg
                    self.dprint(msg)
        # none of the above (or forced to believe so...)
        racfname = self.server.getConfigPath() + '/' + fname
        self.dprint("writing config text to [%s]" % racfname)
        report = self.server.ssh.openfile(racfname, 'w')
        if not type(report) == type(()):
            msg = 'error opening file [%s]' % report
            status['reason'] = msg
            self.dprint(msg)
        else:
            fp, sftp = report
            try:
                fp.write(config_txt+'\n')
                fp.close()
                sftp.close()
                status['success'] = True
                self.config['file'] = racfname
            except:
                msg = "error writing file [%s]" % sys.exc_info()[1]
                status['reason'] = msg
                self.dprint(msg)
        return status


class DockingService(RaccoonService):
    """ 

    """

    def __init__(self, server, config={}, debug=False):
        """
        """
        RaccoonService.__init__(self, server, debug)

        # default config file structure for the docking server
        self._config_template = [
            '############# Raccoon service config file #################',
            '# NAME',
            '# The name of the service as it will be shown in the services list',
            'name = "%(name)s"',
            '\n# COMMENT',
            '# contains a one line description of the service',
            '# this is optional, so leave emtpy quotes if nothing is used',
            'comment = "%(comment)s"',
            '\n# SERVICE TYPE',
            '# define the calculation/data type provided',
            'service = docking',
            '\n# ENGINE TYPE',
            '# this must be a recognized Raccoon engine (i.e. autodock, vina)',
            'engine = %(engine)s',
            '\n# BINARY NAME',
            '# command that is going to be used to run the docking',
            '# if full path is specified, it must be accessible from all nodes',
            'command = "%(command)s"',
            '\n# ENGINE VERSION',
            '# this value will be checked by the service, it can be left blank',
            'ver = "%(ver)s"',
            '\n# MULTITHREAD CALCULATIONS',
            '# specify how many threads are going to be used job;',
            '# if nodes have 4 cores, for example multithread should be',
            '# set to 4; if nodes are single core machines, then multithread',
            '# shuld be set to 1',
            '#      1 : no multithread',
            '#     >1 : use specified cores',
            'multithread = %(multithread)s',
#            '\n# OUTPUT DIRECTORY',
#            '# specify a path where the jobs must be written',
#            '# and the calculations are going to be performed',
#            '# if nothing is specified, the jobs directory',
#            '# will be created in the user home',
#            'outdir = "%(outdir)s"',
            ]
        self._srvtype = 'docking'
        self.config['service'] = self._srvtype
        self.config.update({ 'engine' : None, 'command' : None, 'ver' : None, 
                            'multithread' : 1} )
        self._requiredkw += ['engine', 'command']
        self._legal_values.update( { 'engine': ['autodock', 'vina'] ,
                     'multithread' : int } )

        # links used to install the services on the server
        self.data_source = { 'vina' : {'url': 'http://vina.scripps.edu/download/autodock_vina_1_1_2_linux_x86.tgz',
                                'ver': '1.1.2',
                                'binary': ['vina'],
                                'text' : 'vina --version',
                                },
                    'autodock' : {'url': 'http://autodock.scripps.edu/downloads/autodock-registration/tars/dist423/autodocksuite-4.2.3-i86Linux2.tar.gz',
                                  'ver': '4.2.1',
                                  'binary' : ['autodock4', 'autogrid4'],
                                  'test' : 'autodock4 -v',
                                }
                    }


        if config:
            self.initService(config)



    def makeConfig(self):
        """create the config text for saving to files"""
        template = self._config_template[:]
        return self._makeConfigText(template)


    def initService(self, config):
        """initialize the service from a config dictionary:
            - test if the config is valid
            - validate the executable command
            - 
        """
        self.dprint("==============[ config file ]=============", new=1)
        for c, i in config.items():
            self.dprint("%s : [%s]" % (c,i) )
        self.dprint("==========================================")
        self.dprint("attempt to initialize service [%s]" % config['name'], args=1,new=1)
        self.ready = False
        # config validation
        self.validateConfig(config)
        if not self.config['validated']:
            self.dprint("Service *FAILED* config validation")
            return False
        # command validation
        if not self.validateCommand(which=True):
            self.dprint("Service *FAILED* command validation")
            return False
        # test version (not required.. but important)
        if self.config['ver'] == None:
            if not self.getVersion():
                self.dprint("Service *FAILED* version validation")
                return False
        self.ready = True
        self.dprint("Service [%s] is ready." % self.config['name'])


        scheduler = self.server.systemInfo('scheduler')
        engine = self.config['engine']

        if engine == 'vina':
            #if scheduler == 'pbs':
            #    self.processor = VinaPBSgenerator(self, debug=self.debug)
            #elif scheduler == 'sge':
            #    self.processor = None
            self.processor = VinaSchedulerGenerator(self, debug=self.debug)
        elif engine == 'autodock':
            if scheduler == 'pbs':
                self.processor = None
            elif scheduler == 'sge':
                self.processor = None
        return True



    def validateCommand(self, which=True):
        """ test it if the binary is correct and 
            if so, get the version of the binary
        """ 
        if not self.config['validated']:
            print ("validateCommand> the service config has not been",
                   "validated yet ( use self.validateConfig() )")
            self.dprint("config file not validated yet, returning")
            return False   
        if not self.testCommand(which=which):
            self.dprint("the command wasn't found")
            return False
        self.getVersion()
        return True


    def testCommand(self, which=True, inraccoon=True):
        """ test if the command specified in the config can be found
            as full-path or can be found by the UNIX command 'which'.

            By default, the binary will be searched also in the $RACDIR/bin
            directory, that has priority over system-installed one:
                1. fullpath
                2. racdir (-> set the $RACDIR/bin/ fullpath)
                3. which 
        """
        if not self.config['validated']:
            print ("testCommand> the service config has not been",
                   "validated yet ( use self.validateConfig() )")
            self.dprint("config file not validated yet, returning")
            return False    
        found = False
        bincmd = self.config['command']
        # 1 try fullpath
        found = self.server.ssh.findcommand(bincmd, which=False)
        self.dprint("found (no which) : [%s]" % found)
        # 2. try raccoon
        if not found and inraccoon:
            racbinpath = self.server.getBinPath() 
            found = self.server.ssh.findcommand(racbinpath+bincmd, which=False)
            self.dprint("found (Raccoon path[%s]) :[%s]" % (racbinpath, found) )
        # 3. try which (last resort)
        if not found:
            found = self.server.ssh.findcommand(bincmd, which=which)
        # debug stuff
        if found:
            self.dprint("found binary (final) => [%s]" % (found))
            self.config['command'] = found
        else:
            self.dprint("Impossible to find %s binary => [??]" % (bincmd))
        return found

    def getVersion(self):
        """ get the version of the binary depending on the engine
        
            modify it so the parameters necessary for it will be stored
            at the __init__ time
        """
        if not self.config['validated']:
            print ("getVersion> the service config has not been",
                   "validated yet ( use self.validateConfig() )")
            self.dprint("config file not validated yet, returning")
            return
        engine = self.config['engine']
        bincmd = self.config['command']
        ver = self.config['ver']
        if engine == 'vina':
            cmd = """%s --version | head -1 | awk '{print $3}'""" % bincmd
        elif engine == 'autodock':
            cmd = """%s --version | head -1 | awk '{print $2}'""" % bincmd
        else:
            print "getVersion> UNKNOWN ENGINE!"
            return False
        report = self.server.ssh.execmd(cmd)
        if report == False:
            print "getVersion> no connection... returning"
            self.config['ver'] = '(unknown)'
            return False
        stdout, stderr = report
        self.dprint("STDOUT[%s]" % stdout)
        if len(stdout) > 0:
            if stdout[0] == '':
                print "getVersion> WARNING: no version reported by the binary!"
                ver = '(unknown)'
            else:
                ver = stdout[0]
        else:
            print "getVersion> WARNING: no version found due to possible errors (using the config one)"
        if not ver == self.config['ver']:
            self.dprint("*WARNING* version mismatch: binary[%s] | config[%s]" % (ver, self.config['ver']) )
        self.dprint('Updating service config')
        self.config['ver'] = ver
        return True

    def checkEngine(self):
        """ check if the docking engine binary has been installed already"""
        s = self.server
        engine = self.config['engine']
        info = self.data_source[engine] 
        found = 0
        for bin_name in info['binary']:
            fname = s.getBinPath() + bin_name
            self.dprint('Checking if binary [%s] is on the server' % fname)
            if s.ssh.exists(fname):
                self.dprint('Found.')
                found += 1
        return found == len(info['binary'])


    def installEngine(self, url=None, force=False):
        """
        install the docking engine on the server hosting the service
        """
        status = { 'success': False, 'reason' : None }
        if self.config['engine'] == None:
            self.dprint('No engine defined in the service yet')
            status['reason'] = 'no engine defined'
            return
        engine = self.config['engine']
        # checking url or engine
        if url == None:
            url = self.data_source[ engine ]
            self.dprint("No URL specified, using default:[%s]" % url)
        s = self.server
        info = self.data_source[engine]
        # check if the file is already there
        if self.checkEngine():
            if not force:
                self.dprint('Found! aborting installation')
                status['reason'] = 'binaries already installed'
                return status
            else:
                self.dprint('Found, forced requested, overwriting (maybe)...')
                #s.ssh.delfiles(info[fname])
        # guessing the program link
        if not url:
            url = info['url']
            self.dprint("downloading %s [%s]" % (engine, url))
        else:
            self.dprint("downloading from link: [%s]" % (url))
        # downloading
        success, reply = hf.downloadfile(url, localdirectory=s.scratchdir)
        print "RACCSERVC>", success, reply
        if not success:
            self.dprint("Error downloading [%s]" % reply)
            status['reason'] = reply
            return status
        else:
            installer = reply
        # extracting tar file
        result, source_files = hf.tarextract(tarfilename=installer, 
                                    filelist=info['binary'], outdir=s.scratchdir)
        if result:
            dest_files = [ s.getBinPath() + os.path.basename(f) for f in source_files ]
            files = zip(source_files, dest_files)
            problems = s.ssh.putfiles( flist = files, mode=700) # <-executable
            if len(problems):
                err = "Error copying files:\n"+'\n'.join(problems)
                self.dprint('Found problems:\n%s' % '\n'.join(problems) )
                status['reason'] = err
                return status
            # return the fullpath of binaries
            status['success'] = True
            status['reason'] = dest_files
        return status




#### VINA ####
#
# to run a calculation the following files will be needed:
#
# - list_of_ligands
# - receptor file
# - config file
# 

############### AUTODOCK ###############
# to run a calculation the following files will be needed:
#
#           FULL             CACHED
#     -----------------+------------------
#      list of ligands |  list of ligands
#      receptor file   |  map files
#      list of GPF     | 
#      list of DPF     |  list of DPF
#
#   FULL
#  (list)            (list)         
# ligand_01.pdbqt   ligand_01.gpf   ligand_01_receptor.dpf
# ligand_02.pdbqt   ligand_02.gpf   ligand_02_receptor.dpf
# ligand_03.pdbqt   ligand_03.gpf   ligand_03_receptor.dpf
#




    
class VinaSchedulerGenerator(DebugObj):
    """
            service provide binary and multithread info
    
        Variable names for the pre/post processing
        ==========================================

        $DOCKED_LIGAND  : result of the docking
        $STATUS         : log file where calculations info results are stored


        The start() function provides all functionalities to
            - copy local files to the server
            - generate the config file
            - create index and log files
            - generate scripts for submission (with service and scheduler parms)
    """

    # http://www.brown.edu/Departments/CCV/doc/job-arrays
    # http://stackoverflow.com/questions/2053281/how-to-limit-number-of-concurrently-running-pbs-jobs
    # PBS attributes (max job arrays) : http://linux.die.net/man/7/pbs_server_attributes

    def __init__(self, service, scheduler_parms = {}, debug=True): #, config, preprocess = None, postprocess = None) : # , jobseed, ):
        DebugObj.__init__(self, debug=True)
        print "VINASERVICE INIT"
        self.service = service
        self.server = service.server
        self.preprocess = None
        self.postprocess = None

        self.scheduler_parms = {'walltime' : '24:00:00', 'cputime':'24:00:00', 'queue' : ''}
        for k, v in scheduler_parms.items():
            self.scheduler_parms[k] = v
        self.JOBFILE = 'submission%s.j'
        self.MASTERLOG = "scheduler_master.log"
        self.LOGFILE = 'scheduler_job%s.log'
        self.CONFIGFILE = 'docking.conf'
        self.STATUS = 'status.log'       # each job writes a line when ending
        self.SEEDFILE = 'job.index'         # seed file with all the ligands to dock and dirs to create
                                            #   LIGSOURCE:DOCKING_PATH
                                            #   LIGSOURCE:DOCKING_PATH
                                            #   LIGSOURCE:DOCKING_PATH
        self.options = { 'split' : 1000 }

        self.rec_remote = self.flex_remote = None # populated by the engine later
        # XXX TODO XXX
        # - add support for queues
        # - add specification for mail notifications
        # - add support for non-home dirs
        # - use "-N" option for PBS/SGE job naming (then modify collector to wait for name)

        self._pbs_job_template = [
            """#!/bin/bash""",
            """#PBS -S /bin/bash """,                   # set the shell
            # """#PBS -m %(email)s""",                  # user email for notifications # XXX MISSING GUI
            """#PBS -t %(j_start)d-%(j_end)d""",        # jobs range (1...X, because is used to instruct AWK)
            """#PBS -l nodes=1:ppn=%(multithread)d""",  # multithread value here
            """#PBS -l walltime=%(walltime)s""",        # xx:xx:xx
            """#PBS -d %(vsdir)s""",                    # initial array directory
            """#PBS -o %(vsdir)s/%(logfile)s""",        # log file
            """#PBS -j oe """,                          # combine output and error logs in the same file
            """%(queue)s""",                            # specific queue (optional)
            """# input variables""",                    # -where the input data is injected in the script
            """MASTERLOG="%(vsdir)s/%(masterlog)s" """, # masterlog where all PBS log files of this array are combined
            """SEEDFILE="%(seedfile)s" """,             # 'job.index'
            """STATUS="%(vsdir)s/%(status)s" """,       # 'job_completion.log' where to write update status
            """CONFIG="%(config)s" """,                 # vina config file
            """# end input data""",
            """LINE=`awk "NR==${PBS_ARRAYID}" $SEEDFILE`""",
            """LIGSOURCE=`echo $LINE | awk '{split($0,array,":")} END{print array[1]}'`""",
            """DOCKINGPATH=`echo $LINE | awk '{split($0,array,":")} END{print array[2]}'`""",
            """LIGFILE=`basename $LIGSOURCE`""",
            """LIGNAME=`basename $LIGFILE .pdbqt`""",
            """DOCKLOG=${LIGNAME}.log""",
            """DOCKED_LIGAND=${LIGNAME}_out.pdbqt""",
            """mkdir -p $DOCKINGPATH """,
            """cd $DOCKINGPATH """,
            """touch $STATUS""",
            """%(preprocess)s""",                       # fill here with any pre-processing operation
            """%(binary)s --config "$CONFIG" --ligand "$LIGSOURCE" --out "$DOCKED_LIGAND" --log "$DOCKLOG" """, 
            """%(postprocess)s""",                      # append here any post-processing operations
            """echo $DOCKINGPATH/$DOCKED_LIGAND >> $STATUS""", 
            """echo "====================[ $LIGNAME ]============================" >> $MASTERLOG""",
            """cat %(vsdir)s/%(logfile)s-${PBS_ARRAYID} >> $MASTERLOG """,
            """rm  %(vsdir)s/%(logfile)s-${PBS_ARRAYID}""",
            ]

        self._sge_job_template = [
            """#!/bin/bash""",
            #"""#$ -M %(email)s""",                     # user email for notifications XXX missing interface
            """#$ -S /bin/bash """,                     # set the shell
            """#$ -t %(j_start)d-%(j_end)d""",          # jobs range (1...X, because is used to instruct AWK)
            #"""#$ -l slots=%(multithread)d""",         # multithread DISABLE! THIS WORKS ONLY WITH PARALLEL ENVIRONMENTS!
                                                        # to be checked with :
                                                        #    $ qconf -spl
                                                        #
            """#$ -l h_rt=%(walltime)s""",              # xx:xx:xx
            """#$ -wd %(vsdir)s""",                     # initial array directory
            """#$ -o %(vsdir)s/%(logfile)s""",          # log file
            """#$ -j y """,                             # combine output and error logs in the same file
            """%(queue)s""",                            # specific queue (optional)
            #"""#$ -l qname=queueName """,  #_Clem_ queue name this is site specific, on our clusters _must_ be omitted
            """# input variables""",                    # -where the input data is injected in the script
            """MASTERLOG="%(vsdir)s/%(masterlog)s" """,           # masterlog where all PBS log files of this array are combined
            """SEEDFILE="%(seedfile)s" """,             # 'job.index'
            """STATUS="%(vsdir)s/%(status)s" """,       # 'job_completion.log' where to write update status
            """CONFIG="%(config)s" """,                 # vina config file
            """# end input data""",
            """LINE=`awk "NR==${SGE_TASK_ID}" $SEEDFILE`""", 
            """LIGSOURCE=`echo $LINE | awk '{split($0,array,":")} END{print array[1]}'`""",
            """DOCKINGPATH=`echo $LINE | awk '{split($0,array,":")} END{print array[2]}'`""",
            """LIGFILE=`basename $LIGSOURCE`""",
            """LIGNAME=`basename $LIGFILE .pdbqt`""",
            """DOCKLOG=${LIGNAME}.log""",
            """DOCKED_LIGAND=${LIGNAME}_out.pdbqt""",
            """mkdir -p $DOCKINGPATH """,
            """cd $DOCKINGPATH """,
            """touch $STATUS""",
            """%(preprocess)s""",                       # fill here with any pre-processing operation
            """%(binary)s --config "$CONFIG" --ligand "$LIGSOURCE" --out "$DOCKED_LIGAND" --log "$DOCKLOG" """, 
            """%(postprocess)s""",                      # append here any post-processing operations
            """echo $DOCKINGPATH/$DOCKED_LIGAND >> $STATUS""", 
            #"""echo "====================[ $LIGNAME ]============================" >> $MASTERLOG""",
            #"""cat %(vsdir)s/%(logfile)s-${SGE_TASK_ID} >> $MASTERLOG """,
            #"""rm  %(vsdir)s/%(logfile)s-${SGE_TASK_ID}""",
            ]

    def makeVsName(self, recname=None, ligsource=None, tag=None):
        """ generate the vs name
            this function should be called before the start() to
            generate the name to be checked for duplicate experiments
        """
        if tag == None:
            tag = self.jobinfo['tag']
        if recname == None:
            recname = self.recname
        if ligsource == None:
            ligsource = self.ligsource
        self.dprint("recname = [%s]")
        self.dprint("ligsource = ", ligsource)
        self.dprint("tag [%s]"% tag)
        # library name (combining all libraries selected)
        libname = "_".join([ x.name() for x in ligsource])
        libname = hf.validFilename(libname)
        name = "%s--%s" % (recname, libname)
        if tag: name = '%s_%s' % (name, tag)
        self.dprint("generated name [%s]" % name)
        return name

    def start(self, jobinfo, engine, expdir, ligsource, recname, preprocess='', postprocess='', submit=True, callback=None ):
        """ 
            jobinfo     : dictionary with prj and exp names
            engine      : Raccoon engine object
            expdir      : experiment directory (already created)
            ligsource   : list of RaccoonLibrary objects
            recname     : receptor name (to retrieve rec info with the engine)
            preprocess  : preprocessing objects to call for generating the script code 
            postprocess : postprocessing objects to call for generating the script code
                            [ default echoing into the $STATUS]
        """
        # XXX preprocess and postprocess
        #     should become the names of the other services to be called
        #     to generate the text to be added to the script...
        # postprocess = server.service(preprocess)
        # text = postprocess.generate()
        # append text to the service
        self.job_id = []
        self.jobinfo = jobinfo
        self.engine = engine
        self.expdir = expdir
        self.ligsource = ligsource
        self.recname = recname
        self.recinfo = self.engine.RecBook[self.recname]
        if not preprocess == '':
            self.preprocess = preprocess.generate(lig='$LIGSOURCE', rec=self.rec_remote)
        else:
            self.preprocess = ''
        if not postprocess == '':
            self.postprocess = postprocess.generate(lig='$DOCKED_LIGAND', rec=self.rec_remote)
        else:
            self.postprocess = ''
        self.callback = callback

        if self.jobinfo.has_key('name'):
            self.name = self.jobinfo['name']
            self.dprint("got name [%s]" % self.name)
        else:
            self.name = self.makeVsName()
            self.dprint("made name [%s]" % self.name)
        vsdir = '/'.join([self.expdir,self.name]) 
        vsdir = hf.validPath(vsdir)
        self.dprint("VS dir generated [%s]" % vsdir)

        submission_data = {'error' : None , 'info' : None}
        # make vsdir
        if self.callback: callback("Creating VS directories...")
        result = self.server.ssh.makedir(vsdir)
        if not result == True:
            error = 'error creating vsdir[%s] (aborting)' % vsdir
            submission_data['errors'] = error
            self.dprint(error)
            return submission_data
        self.vsdir = self.server.ssh.normpath(vsdir)
        # copy rec files
        if self.callback: callback("Copying receptor files...")
        if not self.copyrecfiles():
            error = "Copy receptor error: aborting"
            submission_data['errors'] = error
            self.dprint(error)
            return submission_data
        if not self.makeliglist():
            error = "Error generating ligand list, aborting"
            self.dprint(error)
            submission_data['errors'] = error
            return submission_data
        # generate config file
        if self.callback: callback("Generating docking config file...")
        if not self.makeconf():
            error = "Generate config: aborting"
            self.dprint(error)
            submission_data['errors'] = error
            return submission_data
        # generate jobs
        if self.callback: callback("Generating PBS jobs...")
        if not self.generatejobs():
            error = "Generating jobs error: aborting"
            self.dprint(error)
            submission_data['errors'] = error
            return submission_data
        if submit:
            if self.callback: callback("Submitting jobs...")
            submission_data = self.submit()
            return submission_data

    def copyrecfiles(self):
        """ transfer local receptor files to the remote server"""
        # copy receptor on vsdir
        self.dprint("copying rec files")
        files = []
        rec_local = self.recinfo['filename']
        self.rec_remote = self.vsdir + '/' + os.path.basename(rec_local)
        self.rec_remote = self.server.ssh.normpath(self.rec_remote) 
        files.append([rec_local, self.rec_remote])
        if self.recinfo['is_flexible']:
            flex_local = self.recinfo['flex_res_file']
            self.flex_remote = self.vsdir + '/' + os.path.basename(flex_local)
            self.flex_remote = self.server.ssh.normpath(self.flex_remote)
            files.append([flex_local, self.flex_remote])
        problems = self.server.ssh.putfiles(files)
        if len(problems):
            self.dprint("errors copying receptor/flex files:", problems)
            return False
        return True


    def retrieveligands(self, normpath=True):
        """ get all ligands from ligand sources"""
        ligs = []
        for source in self.ligsource:
            ligs += [ self.server.ssh.normpath(x) for x in source.getItems() ]
        return ligs

    def makeliglist(self):
        """ generate the ligand index file parse by the job array"""
        source_ligs = self.retrieveligands()
        total = len(source_ligs)
        count = 0
        step = self.options['split']
        dest_ligs = []
        for lig in source_ligs:
            lig_name = hf.simplebasename(lig)
            actual_fname = '/'.join([ hf.splitdir(count, total, step), lig_name])
            #dest_ligs.append(vsdir + '/' + actual_fname) # LONGER SAFER
            dest_ligs.append(actual_fname) # SHORTER COMPACT
            count += 1
        seed_data = [ '%s:%s' % (s,d) for s,d in zip(source_ligs, dest_ligs) ]
        seed_data = '\n'.join(seed_data) + '\n'
        seed_file = self.vsdir + '/'+ self.SEEDFILE 
        if not self.server.writetext(seed_file, seed_data) == True:
            print "FATALERROR INDEX FILE"
            return False
        return True


    def makeconf(self):
        """ generate the config for docking including :
            - receptor name
            - flex_res name (if any)
            - cpu to use (from service settings)

        The engine.VinaGenConf is used in raw mode to modify files path to point
        to the fullpath, avoiding to copy rec+flex in each ligand directory
        """
        self.engine.vina_settings['cpu'] = self.service.config['multithread']
        config_text = self.engine.VinaGenConf(receptor = self.recname, raw=True)
        config_text['receptor'] = self.rec_remote
        if self.recinfo['is_flexible']:
            config_text['flex'] = self.flex_remote
        config_text = [ "%s = %s" % (k,v) for k,v in config_text.items() ]
        config_text = "\n".join(config_text) + "\n"
        self.config_file = self.vsdir + '/' + self.CONFIGFILE
        if not self.server.writetext(self.config_file, config_text):
            return False
        return True


    def setSchedulerParms(self, parm={}):
        # it must be a 
        pass

    def makejobtext(self, settings):
        """ create the text of job file with the specified settings"""
        sched = self.server.getScheduler()
        if sched == 'pbs':
            template = self._pbs_job_template
        elif sched == 'sge':
            template = self._sge_job_template
        text = "\n".join(template) + "\n"
        text = text % settings
        return text



    def generatejobs(self):
        """ generate the job script text file(s), depending on the max_job_arrays allowed"""
        self.jobs = []
        job_settings = { 'j_start'    : None, # |_ managed by the generation loop 
                         'j_end'      : None, # | 
                         'multithread' : self.service.config['multithread'],
                         'walltime'   : self.scheduler_parms['walltime'],
                         'queue'      : self.scheduler_parms['queue'],
                         'logfile'    : self.LOGFILE,
                         'vsdir'      : self.vsdir,
                         'seedfile'   : self.SEEDFILE,
                         'masterlog'  : self.MASTERLOG,
                         'status'     : self.STATUS,
                         'config'     : self.config_file,
                         'binary'     : self.server.ssh.normpath(self.service.config['command']),
                         'preprocess' : self.preprocess,
                         'postprocess': self.postprocess,
                       }
        # calculate how many separate jobs must be submitted (JOB ARRAY LIMIT)
        self.total_ligands = len(self.retrieveligands())
        #sched_info = self.server.properties['system']['scheduler_info'] 
        #max_jarrays = sched_info.get('max_job_array_size', total_ligands)
        max_jarrays = self.server.getMaxJobsPerArray()
        if max_jarrays == None:
            max_jarrays = self.total_ligands
        if max_jarrays >= self.total_ligands:
            jobs_count = 1
            max_jarrays = self.total_ligands
        else:
            jobs_count = self.total_ligands / max_jarrays
            if self.total_ligands % max_jarrays > 0:
                jobs_count += 1 
        for c in range(jobs_count): 
            j_start = 1 + max_jarrays * c
            j_end   = max_jarrays + max_jarrays * c
            if j_end > self.total_ligands:
                j_end = self.total_ligands
            job_settings['j_start'] = j_start
            job_settings['j_end'] = j_end
            if jobs_count > 1:
                job_settings['logfile'] = self.LOGFILE % c
            else:
                job_settings['logfile'] = self.LOGFILE % ""
            text = self.makejobtext(job_settings)
            self.jobs.append(text)
        self.status_file = self.vsdir + '/' + self.SEEDFILE
        return True

    def generateCollector(self):
        """ generate the script file for the collector job that runs tar on the list of dirs from self.STATUS
            to generate the final tar.gz file to be transferred

            possibly this job can be used to go on the nodes and recollect
            all the data to be moved back to homes if necessary
            (i.e. home not visible from nodes)
        """
        name = 'collector.j'
        self._collector_sge_template = [
            """#!/bin/bash""",
            """#$ -S /bin/bash""",
            """#$ -l h_rt=%(walltime)s""",
            """#$ -wd %(vsdir)s""",
            """#$ -o %(vsdir)s/%(logfile)s""",
            """#$ -j y""",
            """#$ -hold_jid %(dependency)s""",
            """# input variables""",
            #"""VSNAME='%(vsname)s'""",
            """STATUS='%(vsdir)s/%(status)s'""",
            """if [ ! -e $STATUS ]""",
            """  then""",
            """    echo "LOG FILE [$STATUS] DOES NOT EXIST!" 1>&2""",
            """    exit 1""",
            """fi""",
            """touch %(vsdir)s/.collecting""",
            #"""tar zcf %(vsname)s.tar.gz -T $STATUS %(receptor)s %(config)s""",
            """tar zcf %(vsname)s.tar.gz -T $STATUS %(receptor)s %(config)s %(seedfile)s""",
            """echo "tar file generated" >> %(vsdir)s/.collected""",
            """rm %(vsdir)s/.collecting""",
            ]

        self._collector_pbs_template = [
            """#!/bin/bash""",
            """#PBS -S /bin/bash """,                   # set the shell
            """#PBS -l nodes=1:ppn=1""",
            """#PBS -l walltime=%(walltime)s""",        # xx:xx:xx
            """#PBS -d %(vsdir)s""",                    # initial array directory
            """#PBS -o %(vsdir)s/%(logfile)s""",        # log file
            """#PBS -j oe """,                          # combine output and error logs in the same file
            """#PBS -W depend=%(dependency)s""",             # jobs to be waited for completion
            """VSNAME='%(vsname)s'""",
            """STATUS='%(vsdir)s/%(status)s'""",
            """if [ ! -e $STATUS ]""",
            """  then""",
            """    echo "LOG FILE [$STATUS] DOES NOT EXIST!" 1>&2""",
            """    exit 1""",
            """fi""",
            """touch %(vsdir)s/.collecting""",
            """tar zcf %(vsname)s.tar.gz -T $STATUS %(receptor)s %(config)s %(seedfile)s""",
            """echo "tar file generated" >> %(vsdir)s/.collected""",
            """rm %(vsdir)s/.collecting""",
            ]
        sched = self.server.getScheduler()
        if sched == 'pbs':
            template = self._collector_pbs_template
            cmd = """qsub %s"""
            #dependency = "afterany:"+ ",".join(self.job_id)
            dependency = "afteranyarray:"+ ",".join(self.job_id)
        elif sched == 'sge':
            template = self._collector_sge_template
            cmd = """qsub -terse %s"""
            #print "JOBID", self.job_id
            job_id = [ x.split(".", 1)[0] for x in self.job_id]
            #print "JOBID POST",job_id
            dependency = ",".join(job_id)

        data = { 'walltime'  : self.scheduler_parms['walltime'],
                 'vsdir'     : self.vsdir,
                 'logfile'   : 'collector_issues.log',
                 'vsname'    : self.name,
                 'dependency': dependency,
                 'status'    : self.STATUS,
                 'receptor'  : self.rec_remote.rsplit('/',1)[1],
                 'config'    : self.config_file.rsplit('/',1)[1],
                 'seedfile'  : self.SEEDFILE,
                }
        # generate text
        text = "\n".join(template) + "\n"
        text = text % data
        fname = self.vsdir + '/' + name
        cmd = cmd % fname
        if not self.server.writetext(fname, text):
            self.dprint("error writing text file")
            return False
        # submit with dependency from run jobs
        report = self.server.ssh.execmd(cmd)
        if report == False:
            self.dprint("error submitting the job script")
            return False
        stdout, stderr = report
        if len(stderr):
            print "SUBMISSION ERROR"
            print stderr
            return stderr
        self.job_id.append(stdout[0])
        return True


    def submit(self):
        """ write the job script files
            perform the submission on the server
            return the submission info (for the hosting app for a local copy)
        """
        submission_data = { 'error': None, 'info' : None }
        sched = self.server.getScheduler()
        for j in range(len(self.jobs)):
            text = self.jobs[j]
            if len(self.jobs) > 1:
                fname = self.JOBFILE % j
            else:
                fname = self.JOBFILE % ""
            # write job script
            fname = self.vsdir + '/' + fname
            if not self.server.writetext(fname, text):
                self.dprint("error writing text file")
                return False
            if sched == 'pbs':
                cmd = 'qsub %s' % fname
            elif sched == 'sge':
                cmd = 'qsub -terse %s' % fname
            report = self.server.ssh.execmd(cmd)
            if report == False:
                self.dprint("error executing the submission")
                return False
            stdout, stderr = report
            if len(stderr):
                self.dprint("submission returned errors", stderr)
                submission_data['error']  = stderr
                return submission_data
            job_id = stdout[0]
            if sched == 'sge':
                job_id = job_id.split(".", 1)[0]
            self.job_id.append(job_id)
        prj = self.jobinfo['prj']
        exp = self.jobinfo['exp']
        collector = self.generateCollector()
        if not collector == True:
            submission_data['error'] = 'Error in generating the collector [%s]' % collector

        info =  { prj : { exp : {  self.name : {  'type' : 'vs',
                                                  'date' : self.server.date(),
                                                  'hostname' : self.server.hostname(),
                                                  'servername': self.server.name(),
                                                  'status': 'submitted',
                                                  'statusfile' : self.STATUS,
                                                  'masterlog'  : self.MASTERLOG,
                                                  'jobid' : self.job_id,
                                                  'vsdir' : self.vsdir,
                                                  'total' : self.total_ligands,
                                                  'downloaded' : False,
                                                  'engine' : 'vina',
                                                  'resource' : 'ssh', } } } }  
        submission_data['info'] = info
        print "SUBMISSION INFO", info
        self.server.registerJob(info)
        return submission_data


class SGEgenerator:
    """provides the submit() method for the
        generation of SGE-compliant jobs
    """
    # http://wiki.ibest.uidaho.edu/index.php/Tutorials:_SGE_PBS_Converting
    # XXX CONVERSION PBS TO SGE
    def __init__(self):
        pass

#class VinaPBS(VinaPBSgenerator, VinaRunner):
#
#    pass

"""

class VinaSGE(SGEgenerator, VinaRunner):
    pass

class AutoDockPBS(PBSgenerator, AutoDockRunner):
    pass
    
class AutoDockSGE(SGEgenerator, AutoDockRunner):
    pass
""" 

    

class DockPostProcessing(RaccoonService):
    """
    DISABLED USELESS FOR NOW
    """
    
    def __init__(self, server, lig, rec, debug=False):
        RaccoonService.__init__(self, server, debug)
        

        self._srvtype = 'postprocess'
        self.lig = lig
        self.rec = rec

        self._requiredkw += ['command']
        #self._legal_values.update({'dockingengine': ['vina', 'autodock']})



        self._config_template = [
            '############# Raccoon service config file #################',
            '# NAME',
            '# The name of the service as it will be shown in the services list',
            'name = "%(name)s"',
            '\n# COMMENT',
            '# contains a one line description of the service',
            '# this is optional, so leave emtpy quotes if nothing is used',
            'comment = "%(comment)s"',
            '\n# SERVICE TYPE',
            '# define the calculation/data type provided',
            'service = postprocess',
            '\n# DATA SOURCE',
            '# specify which kind of data is required for the processing',
            '# allowed values are : ligand, receptor, both',
            'engine = %(engine)s',
            '\n# COMMAND NAME',
            '# command that is going to be used to run the docking',
            '# if full path is specified, it must be accessible from all nodes',
            'command = "%(command)s"',
            ]




##################################################################################
##################################################################################
####################   LIBRARY SECTION BELOW #####################################
##################################################################################
##################################################################################



class LibraryHostService(RaccoonService):
    """
        service that host libraries of structural data
        for docking outside the current server (i.e. providing remote
        access of libraries to other servers)
    """
    # XXX IT MUST PROVIDE A DOWNLOAD MECHANISM!
    # XXX remote_tar, transfer, local_untar?

    def __init__(self, server, config={}, debug=False):
        RaccoonService.__init__(self, server, debug)
        # default config file structure for the library server
        self._config_template = [
            '############# Raccoon Library Host config file #################',
            '# ',
            '# This file defines the configuration of a Raccoon Docking Library',
            '# hosting service.',
            '# ',
            '# A library is a homogeneus collection of structural files (ligands,',
            '# receptors, ...) that can be used for molecular mechanics',
            '# simulations.',
            '# ',
            '# NAME',
            '# The name of the library service (i.e. "commercially available compounds"',
            '# as it will be shown in the services list',
            'name = "%(name)s"',
            '\n# COMMENT',
            '# contains a one line description of the service',
            '# this is optional, so leave emtpy quotes if nothing is used',
            'comment = "%(comment)s"',
            '\n# SERVICE TYPE',
            '# define the calculation/data type provided'
            '# allowed values could: docking, md, filtering ...',
            'service = library_host',
            '\n# LIBRARIES',
            '# list of libraries that are served to clients',
            '# library names must be in the $RACDIR/library/index.lib',
            '# where the info on their files and properties is stored',
            '# for example:',
            '# lib = "nci_div2"',
            '#',
            '# to host automatically all libraries installed on the server',
            '# set "lib" to "_all_"',
            'lib = "_all_"',
            ]
        self._srvtype = 'library_host'
        self.config['service'] = self._srvtype
        self.config.update({ 'lib':[]} )
        self._requiredkw += ['service', 'lib']
        #self._legal_values.update( { 'engine': ['autodock', 'vina'] ,
        #             'multithread' : int } )
        if config:
            self.initService(config)


    def initService(self, config={}):
        """ initialize the service from the config"""
        self.dprint("attempt to initialize service [%s]" % config['name'], args=1,new=1)
        self.ready = False
        # config validation
        self.validateConfig(config)
        if not self.config['validated']:
            self.dprint("Service *FAILED* config validation")
            return False
        return self.validateLibNames()


    def validateLibNames(self, names=[]):
        """ check that names requested for the hosting
            are known to the server, i.e. listed in 
            the library index file
        """
        if names == []:
            names = self.config['lib']
        registered_libs = self.server.getLibraryNames()
        if '_all_' in names:
            self.dprint("all libraries requested ['_all_' kw]")
            if len(registered_libs) > 0:
                self.dprint("there is at least a library installed on the server")
                return True
            else:
                self.dprint("no libraries registered on the server... what to do? returning FALSE for now")
                return False
        else:
            for n in names:
                if not n in registered_libs:
                    return False
            return True


    def makeConfig(self):
        """generate a config file from the library service template
           populating the lib entries
        """
        template = self._config_template[:]
        # lib keyword in the config file can be specified one or more times
        if type(self.config['lib']) == type([]):
            lib_list = self.config['lib']
        else:
            lib_list = [ self.config['lib'] ]
        for lib in lib_list:
            l = 'lib = "%s"' % lib
            template.append(l)
        conf = self._makeConfigText(template)
        return conf

    def _checkLibraryFiles(self):
        """ maybe this should become a RacconService parent class
            method
        """
        pass


    def checkLibraryNodeAccessibility(self, libname):
        """
        depending on the scheduler/resmanager do this operation?

        NO! THIS IS RISKY! IF THE QUEUE IS FULL THE TIME IS INFINITE!
         - qsub -I
         - stat $theFirstFileOfTheLibrary
         - if it's ok, the file is accessible from the nodes

        """
        pass


class LibraryUploadService(RaccoonService):
    """
        service that allow to upload libraries of structural data
        for docking
    """
    def __init__(self, server, config={}, debug=False):
        RaccoonService.__init__(self, server, debug)
        # default config file structure for the library server
        self._config_template = [
            '############# Raccoon Library Upload config file #################',
            '# ',
            '# This file defines the configuration of a Raccoon Docking Library',
            '# upload service.',
            '# ',
            '# A library is a homogeneus collection of structural files (ligands,',
            '# receptors, ...) that can be used for molecular mechanics',
            '# simulations.',
            '# ',
            '# NAME',
            '# The name of the library as it will be shown in the services list',
            'name = "%(name)s"',
            '\n# COMMENT',
            '# contains a one line description of the service',
            '# this is optional, so leave emtpy quotes if nothing is used',
            'comment = "%(comment)s"',
            '\n# SERVICE TYPE',
            '# define the calculation/data type provided'
            '# allowed values could: docking, md, filtering ...',
            'service = library_upload',
            '\n# LIBRARY STORAGE PATH',
            '# define where the files are going to be updloaded on the server'
            '# allowed values could: docking, md, filtering ...',
            'location = library_upload',
            '\n# LIMITATIONS',
            '# limitations in library properties (i.e. number of files,',
            '# max_items = [ leave it empty if not enforced ]',
            'max_items =  ',
            ]
        self._srvtype = 'library_upload'
        self.config.update({'location':'', 'max_items':''})
        self._requiredkw += ['service', 'location' ]
        if config:
            self.initService(config)


    def uploadLibrary(self, info={}):
        """ upload the library in the path set in 'location'
            - read the self.config['location'] path
                - if the value is '' (empty) then use the $LIBRARY location
            - copy the files in that location
            - add the entry in the $LIBRARY/index.lib file

        info = { 'source' : '/local/path/to/lib_dir/',
                   'name'   : 'ThisIsTheLibraryNameOnTheServer',
                   'items'  : -1,
                   'destination': '/remote/path/on/the/server/where/to/write',
                   }
        """
        # path where to save the libraries
        if config.haskey('destination'):
            path = config['destination']
        else:
            path = self.server.ssh.getLibraryPath()

        if self._checkpathwritable( config['']):
            return
        # check the path is writable
        # check enough disk space?
        # check the name has not been used already
        # count that items match the maximum number of items allowed
        pass


class RemoteResources(RaccoonService):
    """ create a service that allow other services hosted 
        on this server to access remote files
        (i.e. if this service is active together with a docking
        service, it will allow it to get remote libraries or
        write the results into another server
    """
    def __init__(self, server, config = {}, debug=False):
        RaccoonService.__init__(self, server, debug)
        # USE WGET? SCP?
        # REQUIRE KEYS?
        from RaccoonSshTools import RaccoonServer, RaccoonSshClient
        #self.remoteserver = RaccoonServer()
        self.ssh = RaccoonSshClient()
        self.config.update( { 'server' : None, 
                            })
        # TODO INCOMPLETE

class Library:
    """ object to manage library properties

    """
    def __init__(self, server, libinfo = {}):
        self.server = server
        self.name = libinfo['name']
        self._type = libinfo['type']
        self.path = libinfo['path']
        self.date = libinfo['date']
        self.properties = {}

    def addLibToIndex(self, fname, force=False):
        """ add library info to an index file
            if a library with same name and type already exists,
            data will not be written, unless 'force=True'
        """
        libindex = self.server.ssh.readJson(fname)


class LigandLibrary(Library):
    """ object to manage library properties (LIGAND)
    """
    def __init__(self, server, libinfo={}):
        RemoteLibrary(self.server, libinfo)



    def updateProperties(self):
        """ populate and update properties of the
            ligand library
        """ 
        self.properties = {}
        for p in ['heavy', 'mw', 'tors', 'hbacc', 'hbdon']:
            try:
                self.properties[p] = libinfo[p]
            except:
                self.properties[p] = None



knownservices = { 'docking': DockingService, # AutoDock/Vina docking service
                  'library_host': LibraryHostService, # Library hosting service
                  'library_upload': LibraryUploadService, # Library hosting service
                  # XXX generic class to create?
                  'remoteresources' : RemoteResources, # Access to remote locations (read/write)
                }



