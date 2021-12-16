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

import Tkinter as tk
import Pmw, tkFont, ImageTk
from PmwOptionMenu import OptionMenu as OptionMenuFix
import os, zlib, json, sys, shutil, copy
from operator import itemgetter
# raccoon modules
#from raccoon import Raccoon
import tkMessageBox as tmb
import DebugTools
import RaccoonEvents # FIXME -> to become CADD.Raccoon2.RaccoonEvents
import RaccoonBasics
import RaccoonEngine
import RaccoonServers
import RaccoonVsResults as vsg
import RaccoonFilterEngine


# mgl modules
import CADD.Raccoon2.HelperFunctionsN3P  as hf
from mglutil.events import Event, EventHandler
from mglutil.util.callback import CallbackFunction #as cb
from mglutil.util.packageFilePath import getResourceFolderWithVersion

# classes

from AA_setup import SetupTab
from BB_ligand import LigandTab
from CC_receptor import ReceptorTab
from DD_config import ConfigTab
from EE_jobmanager import JobManagerTab
from FF_anaylsis import AnalysisTab



class RaccoonMaster(DebugTools.DebugObj):
    """ if racdir is specified, it can be used
        if RACDIR environmental var is set, it override this value
    """
    
    def __init__(self, resource='local', dockengine='vina', eventmanager=None,    
                racdir = None, debug=False):
        DebugTools.DebugObj.__init__(self, debug)

        if eventmanager == None:
            eventmanager = RaccoonEvents.RaccoonEventManager()
        self.eventManager = eventmanager

        self.dockengine = dockengine
        self.engine = RaccoonEngine.RaccoonEngine()
        self.engine.box_center = [ 0., 0., 0.]

        # results business
        self.results = {}
        self.resPropertiesReset()
        #self.eventManager.registerListener( RaccoonEvents.ResultsImportedDeleted, self.resPropertiesReset)
        self.eventManager.registerListener( RaccoonEvents.ResultsImportedDeleted, self.updateResultsProperties)
        self.eventManager.registerListener( RaccoonEvents.SyncJobHistory, self.syncServerHistory)

        self.filterEngine = RaccoonFilterEngine.FilterEngine(self, debug)

        # vs data source 
        self.ligand_source = [] # this will contain objects to be called
                                # to generate ligand filenames:
                                #   { 'lib': RaccoonLibrary, 'filters' : {} }



        self.knownTargets = {} # this is the database of all known and used targets stored with
                               # unique MD5sum id

        # server object to wich we're connected
        # this should be one of RaccoonRemoteServer ('ssh'), RaccoonOpalServer ('opal') or 
        # RaccoonLocalServer ('local') objects
        self.server = None

        self.history = {}
        self.resource = resource # local, ssh, opal
        self.dockingservice = None
        self._system_info = hf.getOsInfo()
        self.ready = False
        self.settings = { 'engine' : dockengine,

                          'options': { 'save_username': True,
                                       'save_password': False,
                                     },
                           # from config files
                          'servers': { 'ssh' : {},  # 'garibaldi' : { ''address': 'garibaldi.scripps.edu',
                                                    #   'username': 'forli',
                                                    #   'password': None,
                                                    #   'pkey' : None, # file
                                                    #   '_save_passwd_' : False,
                                                    #  }
                                       'opal': [],
                                     },

                          'viewer': { }, # 3d viewer settings
                        }

        self.resultsProcessor = vsg.RaccoonVsResultsGenerator(self, self.debug)
        self.setDockEngine(dockengine)

        #self.notebook.component('Config-tab').bind('<1>', cb)

        # less important stuff
        self._lastdir = None

        # /less important stuff
        if racdir == None:
            racdir = os.getenv("RACDIR")
            if racdir == None:
                racdir = os.path.expanduser('~') + os.sep + 'raccoon'
                print "[ RAC DIR SET TO [%s] ]" % racdir
        self.initRac(racdir)

        # functions to be registered for events


    def hostname(self):
        """ return the hostname where the client
            is running
        """
        return self._system_info['hostname']

    def getLigands(self):
        """ function placeholder to remind you how to design the structure
            so that there's a unified call for getting the ligand libraries.
        """

    def getReceptors(self):
        """
        """
        pass

    def setDockEngine(self, dockengine):
        """ set the current session docking engine"""
        self.dockengine = self.settings['engine'] = dockengine
        e = RaccoonEvents.SetDockingEngine(dockengine)
        # NOTE this event will trigger RaccoonVsResultsGenerator.setDockingEngine()
        self.eventManager.dispatchEvent(e)

        self.results.clear()
        e = RaccoonEvents.ResultsImportedDeleted()
        self.eventManager.dispatchEvent(e)
        # results generator
        # 

    def getDockingEngine(self):
        """ return the docking engine currently in use"""
        return self.dockengine


    def initRac(self, path):
        """ start session initialization cascade  (var, dirs...)"""
        self.ready = False
        self.setRacPath(path)
        #print ">>CHECKING DIRS"
        if not self._checkdirs():
            return False
        if not self._checkfiles():
            return False
        self.readConfig()     # init client config
        self.readServerInfo() # init db of known servers
        self.loadTargetDb()   # init db of known targets
        self.loadHistory()    # init known jobs db
        self.ready = True

    def setRacPath(self, path):
        """ initialize variables containing path and files location """
        # dir names
        DATA_PATH = 'data'
        DOCKING_PATH = 'docking'
        TARGET_PATH = 'targets'
        TMP_PATH = 'tmp'
        # file names
        CONFIG_FILE = 'raccoon.conf'       
        SERVER_FILE = 'servers.db'       
        HISTORY_FILE = 'history.log'
        TARGET_FILE = 'targetdb.log'
        # setting dirs
        self.settings['racdir'] = path   # base dir used to store all information
        self.settings['datadir'] = path + os.sep + DATA_PATH # data files are stored here 
        self.settings['dockingdir'] = self.settings['datadir'] + os.sep + DOCKING_PATH # results are stored here
        self.settings['targetdir'] = self.settings['datadir'] + os.sep + TARGET_PATH # known used docking targets stored here
        self.settings['tempdir'] = path + os.sep + TMP_PATH  # temp directory used for temporary transactions
        self.tempdir =  self.settings['tempdir'] # redundant but used by some functions
        # setting files
        self.settings['config_file'] = path + os.sep + CONFIG_FILE # Raccoon client config file
        self.settings['server_dbase'] = path + os.sep + SERVER_FILE # known saved server dbase
        self.settings['history'] = path + os.sep + HISTORY_FILE # history file of all jobs
        self.settings['target_db'] = self.settings['targetdir'] + os.sep + TARGET_FILE # store unique id for each target used in jobs 

    def getHistoryFilename(self):
        """ return the history of jobs run on the server
        
            THIS IS ANOTHER BASIC FUNCTION FOR THE RACCOON CORE SERVER
        """
        return self.settings['history']


    def _checkdirs(self, autocreate =True):
        """ check and create necessary raccoon dirs"""
        dirs = [  self.settings['racdir'], self.settings['datadir'] , 
                  self.settings['tempdir'], self.settings['dockingdir'],
                  self.settings['targetdir'] ]

        for d in dirs:
            if not os.path.isdir(d):
                if autocreate:
                    print "dir [%s] does not exist. Creating it..." % d
                    hf.makeDir( fullpath = d)
                else:
                    return False
        return True


    def _checkfiles(self, autocreate=True):
        """ check and create necessary raccoon files"""
        files = [ self.settings['config_file'], self.settings['history'], 
                self.settings['server_dbase'] , self.settings['target_db'] ]
        for f in files:
            if not os.path.isfile(f):
                if autocreate:
                    t = hf.touch(f)
                    if not t:
                        #print "error in file [%s] : [%s]" % (f,t)
                        return False
        return True

    def getRacPath(self):
        """ check if RACDIR home variable is set, otherwise
            return self.settings['racdir']
        """
        #self.mglroot = getResourceFolderWithVersion()
        #self.raccoon_root = self.mglroot + os.sep + 'Raccoon'
        #home = os.path.expanduser('~')
        #self.settings['racdir'] = home + os.sep + 'raccoon'
        #RACDIR = os.getenv("RACDIR")
        #if RACDIR:
        #    print "RACDIR FOUND", RACDIR
        #    self.settings['racdir'] = RACDIR
        return self.settings['racdir']

    def getTempDir(self):
        """ """
        return self.settings['tempdir']


    def getDataDir(self):
        """ return the directory where all data is going to be saved """
        return self.settings['datadir']

    def getDockingDir(self):
        """ return the directory where docking are going to be saved """
        return self.settings['dockingdir']


    def getTargetDir(self):
        """ return the directory where all docking targets used in 
            docking are going to be saved """
        return self.settings['targetdir']

    def getTargetDbFile(self):
        """ return full filename of database where all target files
            for which dockings have been submitted have been stored
        """
        return self.settings['target_db']

    def getConfigFile(self):
        """ return the config file name """
        return self.settings['config_file']

    def getHistoryFile(self):
        """ return the config file name """
        return self.settings['history']

    def getJobDir(self, job):
        """ retrieve history information about a job[p][e][v]"""
        #datadir = self.getDataDir()
        datadir = self.getDockingDir()
        jobdir = os.sep.join([ datadir, job[0], job[1], job[2] ] )
        return jobdir


    def getServerInfoFile(self):
        """ return the database file where server info are stored"""
        return self.settings['server_dbase']

    def getServerByType(self, _type):
        """return known servers by type"""
        if _type == None:
            #print "ERROR: specify the server '_type'"
            return
        return self.settings['servers'][_type]

    def addServer(self, _type, name, info={}):
        """ add a new server connection to the dbase of 
            known connections
        """
        self.settings['servers'][_type][name] = info
        self.saveServerInfo()
        # self.readServerInfo()

    def delServer(self, _type, name):
        """ remove a server connection from the dbase of 
            known connections
        """
        del self.settings['servers'][_type][name]
        self.saveServerInfo()

    def getServerByName(self, name):
        """ return server by name"""
        if name == None:
            #print "ERROR: specify the server name"
            return
        # server types
        types = self.settings['servers'].keys()
        for t in types:
            for s in self.settings['servers'][t]:
                if s == name:
                    return self.settings['servers'][t][s]
        return False

    def readConfig(self, fname=None):
        """ read the confielf.saveServerInfo()
        # g file """
        #print "READING CONFIG FILE"
        if fname == None:
            fname = self.getConfigFile()
        data = hf.readjson(fname)
        if data:
            self.settings = data

    def writeConfig(self, fname=None):
        """ write the config file """
        # XXX FIXME NOT WORKING
        if fname == None:
            fname = self.getConfigFile()
        self.settings = hf.writejson(fname, self.config)

    def saveServerInfo(self, fname=None):
        """save the server db and handle password saving"""
        if fname==None:
            fname = self.getServerInfoFile()
        srv_db = copy.deepcopy(self.settings['servers'])
        for s in srv_db['ssh'].keys():
            srv = srv_db['ssh'][s]
            if '_save_passwd_' in  srv.keys():
                del srv['_save_passwd_']
            else:
                srv['password'] = None
        hf.writejson(fname, srv_db, compression=True)

    def readServerInfo(self, fname=None):
        """read the server db and handle password saving"""
        if fname==None:
            fname = self.getServerInfoFile()
        data = hf.readjson(fname, compression=True)
        if data:
            srv_db = data
            for _type in srv_db.keys():
                if _type =='ssh':
                    for name in srv_db[_type].keys():
                        srv = srv_db[_type][name]
                        if not srv['password'] == None:
                            srv['_save_passwd_'] = None
            self.settings['servers'] = srv_db


    def loadTargetDb(self, fname=None):
        """ read the database where known used targets
            are stored
        """
        if fname == None:
            fname = self.getTargetDbFile()
        data = hf.readjson(fname, compression = False)
        if data:
            self.knownTargets = data
            self.dprint("Target dbase initialized: %d items" % len(self.knownTargets.keys()) )


    def saveTargetDb(self, fname=None):
        """ write the database of known used targets
        """
        if fname == None:
            fname = self.getTargetDbFile()
        self.dprint("writing [%s] known targets database" % fname)
        return self.writeJson(fname, self.knownTargets)


    def loadHistory(self):
        """ XXX THIS WILL BECOME THE CORE RACCOON SERVER! """
        fname = self.getHistoryFilename()
        self.dprint("reading [%s] history file" % fname)
        self.history = self.readJson(fname)
        if self.history == False:
            self.dprint("empty/unreadable history file")
            self.history = {}        

    def saveHistory(self):
        """ """
        fname = self.getHistoryFilename()
        self.dprint("writing [%s] history file" % fname)
        #print "This is the history file to write:", fname
        return self.writeJson(fname, self.history)


    def writeJson(self, fname, data, mode='w', compression=False):
        """ write a python data type (dict or list) 
            into a JSON file

            optional Zlib compression available
            
            # COMPRESSION
            http://www.blog.pythonlibrary.org/2010/10/20/\
                downloading-encrypted-and-compressed-files-with-python/
        """
        self.dprint("Open file [%s] for writing, mode [%s]" % (fname, mode))
        #report = self.ssh.openfile(fname, mode=mode)
        self.dprint("data type is [%s]" % type(data))
        try:
            fp = open(fname, mode=mode)
        except:
            self.dprint("Error writing JSON file [%s] : [%s]" % (fname, sys.exc_info()[1]))
            return False
        if compression:
            self.dprint("writing (COMPRESSED) to [%s]" % fp)
            data = json.dumps(data, indent=2)
            zdata = zlib.compress(data)
            fp.write(zdata)
        else:
            self.dprint("writing (UNCOMPRESSED) to [%s]" % fp)
            json.dump(obj=data, fp=fp, indent=2)
        self.dprint("Data written")
        fp.close()
        return True


    def readJson(self, fname, compression = False):
        """ read a json data file and perform the 
            opportune conversions to restore python types
            
            supported types are dict and list

            optional Zlib compression available

            # source:
            # http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-unicode-ones-from-json-in-python
        """
        self.dprint("Open file for reading [%s]" % (fname))
        try:
            fp = open(fname, mode='r')
        except:
            self.dprint("Error reading JSON file [%s] : [%s]" % (fname, sys.exc_info()[1]))
            return False
            
        data = fp.read()
        fp.close()
        if compression:
            data = zlib.decompress(data)
        try:
            data = json.loads(data, object_hook=hf.jsonhelper)
        except:
            self.dprint("Problem [%s]" % sys.exc_info()[1])
            return False
        self.dprint("data type read is [%s]" % type(data))
        return data

    def targetFingerprint(self, fname):
        """ return target fingerprint and alias name """
        try:
            fobj = open(fname, 'r')
            self.dprint("file opened [%s]" % fname)
        except:
            e = sys.exc_info()[1]
            self.dprint("error opening file [%s]:%s" % (fname, e))
            return (False, e)
        fingerp = hf.hashfile(fobj)
        alias = os.path.basename(fname)
        return (fingerp, alias)

    def registerTarget(self, fname):
        """ copy receptor structure to $TARGETDIR and register
            the target into the targets db
        """
        fingerp, alias = self.targetFingerprint(fname)
        if fingerp == False:
            return (fingerp, alias) # ->  == (False, e)
        if not fingerp in self.knownTargets.keys():
            self.dprint("new structure [%s], added to the dbase as [%s]" % (alias, fingerp))
            self.knownTargets[fingerp] = [ alias ]
            dest = self.getTargetDir()
            self.dprint("caching receptor structure to [%s]" % (dest) )
            try:
                dest = os.path.join(dest, fingerp)
                shutil.copy2( fname , dest)
            except:
                e = sys.exc_info()[1]
                self.dprint("error caching receptor source[%s] dest[%s] error[%s] " % (fname, dest, e) )
                return (False, e)
        else:
            if alias in self.knownTargets[fingerp]:
                self.dprint("known structure, skipping registration")
                return (fingerp, alias) 
            else:
                self.knownTargets[fingerp].append(alias)
                self.dprint("alias [%s] added to db entry [%s]" % (alias, fingerp))
        self.saveTargetDb()
        return (fingerp, alias) 

    def unregisterTarget(self, targetId, alias=None):
        """ remove target info from db:
            
            if not alias == None:
                remove only this alias from db
            else:
                nuke the entire entry with this targetId
                and delete file from $TARGETDIR
        """
        if alias == None:
            self.dprint("unregistered alias [%s] for recid[%s]" % (alias, targetId) )
            del self.knownTargets[targetId]
            return
        self.dprint("unregistering recid[%s]" % (targetId) )
        try:
            fname = os.path.join( self.getTargetDir(), fingerp)
            self.dprint("deleting file [%s]" % (fname) )
            os.remove(fname)
        except:
            e = sys.exc_info()[1]
            self.dprint("error deleting file [%s]" % (e) )
            return False
        del self.knownTargets[targetId][alias]
        return True
    
    def getTargetCacheFile(self, targetId, alias=None):
        """ copy the targetId receptor in the TEMP directory
            and optionally name it 'alias' (default: first 
            name in record)
            FIXME: currently works only with PDBQT files
        """
        if not targetId in self.knownTargets.keys():
            return (False, 'unknown')
        if alias == None:
            alias = self.knownTargets[targetId][0]
        source =  os.path.join( self.getTargetDir(), targetId)
        dest = os.path.join( self.getTempDir(), alias) # + '.pdbqt')
        try:
            shutil.copy2( source , dest)
        except:
            e = sys.exc_info()[0]
            self.dprint("Error copying receptor [%s=>%s] from cache: [%s]" % (source, dest, e) )
            return (False, e)
        return (True, dest)

        
    def registerJob(self, submission):
        """  register a job in self.history 
            and update the server history file
        """
        #print "CALLED REGISTERJOB", submission
        # project
        prj = submission.keys()[0]
        if not prj in self.history.keys():
            self.history[prj] = {}
        # experiment
        exp = submission[prj].keys()[0]
        if not exp in self.history[prj].keys():
            self.history[prj][exp] = {} #'vs':{} }
        # jobs
        jobname = submission[prj][exp].keys()[0]
        if jobname in self.history[prj][exp].keys():
            self.dprint("*COLLISION AHEAD* : job name already present [%s]" % jobname)
            return False
        self.history[prj][exp][jobname] = submission[prj][exp][jobname]
        # save date into remote history file
        self.saveHistory()

    def findJob(self, prj=None, exp=None, name=None): #,  _type='vs'):
        """ check if jobname has already been found in the currently loaded history file"""
        self.dprint("searching for [%s|%s|%s]" % (prj, exp, name) )#, _type) )
        if prj == None:
            prj_pool = self.history.keys()
        else:
            prj_pool = [prj]
        self.dprint("PRJ POOL [%s]" % ",".join(prj_pool) )
        for p in prj_pool:
            if not p in self.history.keys():
                self.dprint("*NOT FOUND* (no projects with this name)") 
                return ()
            if exp == None:
                exp_pool = self.history[p].keys()
            else:
                exp_pool = [exp]
            self.dprint("EXP POOL [%s]" % ",".join(exp_pool) )
            for e in exp_pool:
                if not e in self.history[p].keys():
                    self.dprint("*NOT FOUND* (no experiments with this name)") 
                    return ()
                else:
                    if name in self.history[p][e].keys():
                        found = ( p, e, name ) 
                        self.dprint("*FOUND* [%s|%s|%s]" % found)
                        return found
        self.dprint("*NOT FOUND*") 
        return ()

    def updateJobHistory(self, name, prj=None, exp=None, properties={}):
        """ update the job info using properties provided 
        """
        self.dprint("Request to update job [%s|%s|%s]" % (prj, exp,name))
        self.dprint("Properties :", properties )
        prj, exp, name = self.findJob(prj, exp, name)
        self.history[prj][exp][name].update(properties)
        self.saveHistory()
        e = RaccoonEvents.UpdateJobHistory(prj = prj, exp=exp, name=name)
        self.eventManager.dispatchEvent(e)

    def connectSshServerSafe(self, server, data=None): #, usekeys=False):
        """ 
        """
        if isinstance(self, RaccoonGUI):
            self.SetupTab.chooseServer(server)
        else:
            data = self.settings['servers']['ssh'][server]
            #msg = 'Enter password for user on server %s' % server
            data['password'] = raw_input('Enter password for user on server %s' % server)
            self.connectSshServer(server, data) #, usekeys=usekeys)

    def connectSshServer(self, server, data=None): #, usekeys=True):
        """ """
        self.setBusy()
        if not self.server == None:
            if self.server.is_connected():
                if server == self.server.properties['name']:
                    self.dprint("The server [%s] is already connected" % server)
                    self.setActive()
                    return 'connected'
                else:
                    #e = RaccoonEvents.ServerDisconnection()
                    #self.eventManager.dispatchEvent(e)
                    #self.server.disconnect()
                    self.disconnectSshServer()

        if data == None:
            data = self.settings['servers']['ssh'][server]
        self.dprint("Initializing the server object")
        self.server = RaccoonServers.RaccoonRemoteServer( address = data['address'],
            username = data['username'], password = data['password'], name = server,
            debug = self.debug, usesyshostkeys=data['load_sys_host_key'], autoaddmissingkeys=True, pkey = data['pkey'],
            autoconnect = False, check = True, prepare=False, autoscan=False)
        conn = self.server.connect()
        if conn == 1:
            # update hostname info
            hostname = self.server.hostname()
            self.settings['servers']['ssh'][server]['hostname'] = hostname
            self.saveServerInfo()
            # trigger event
            event = RaccoonEvents.ServerConnection()
            self.eventManager.dispatchEvent(event)
            #self.statusbar.message('state', 'Connected to "%s"' % hostname)
            self.setReady()
            return 'connected'
        self.setReady()
        return conn

    def copyProject(self, prj):
        """ copy project history"""
        p = {}
        for e in prj.keys():
            p[e] = self.copyExperiment(prj[e])
        return p

    def copyExperiment(self, exp):
        """ copy experiment history """
        e = {}
        for v in exp.keys():
            e[v] = self.copyVs(exp[v])
        return e

    def copyVs(self, vs):
        """ copy vs history"""
        from copy import deepcopy
        return deepcopy(vs)
        pass
        
    def copyDict(self, dictionary):
        """ perform a deepcopy of the dictionary"""
        return 

    def syncServerHistory(self, event=None):
        """ scan the server history and sync the content
            with the local history
        - get the remote server history
        - compare remote and local history, append new
        - update local history file
        """
        self.setBusy()
        added = {'prj': 0, 'exp': 0, 'jobs': 0}  # XXX to be used for the statusbar update
        self.dprint("syncing history with server")
        local = self.history
        remote = self.server.history
        #print "\n\nMATCHER-1", self.history == self.server.history
        # these values could mismatch even with identical jobs
        skip = ['status', 'date', 'downloaded', 'summary'] 
        l_prj = local.keys()
        r_prj = remote.keys()
        to_be_added = []
        for p in r_prj:
            if not p in l_prj: # new project
                self.dprint("New project found on the server:", p)
                #local[p] = {}
                #tocopy = remote[p].copy()
                local[p] = self.copyProject(remote[p] )
                to_be_added.append((p,))


            else: # known project
                r_exp = remote[p].keys()
                l_exp = local[p].keys()
                for e in r_exp:
                    if not e in l_exp: # new experiment
                        self.dprint("New experiment found on the server:", e)
                        local[p][e] = remote[p][e].copy()
                        to_be_added.append((p,e))
                        print "MATCHER-1B", self.history == self.server.history
                    else: # known experiment
                        r_jobs = remote[p][e].keys()
                        l_jobs = local[p][e].keys()
                        for j in r_jobs:
                            if not j in l_jobs: # new job
                                local[p][e][j] = remote[p][e][j].copy()
                                self.dprint("New job found on the server:", j)
                                to_be_added.append((p,e,j))
                            else: # potentially knownw job
                                self.dprint("Potentially known job found on the server:", j)
                                rjob = remote[p][e][j]
                                to_add = True
                                #for lkey in local[p][e].keys():
                                #    ljob = local[p][e][lkey]
                                ljob = local[p][e][j]
                                if self._compareJobs(ljob, rjob):
                                    to_add = False
                                    break
                                if to_add:
                                    # different job with same name -> new name
                                    n = j
                                    c = 1
                                    while n in local[p][e].keys():
                                        n = "%s_%d" % (j, c)
                                        c += 1
                                    local[p][e][n] = remote[p][e][j].copy()
                                    to_be_added.append((p,e,j))
                                    self.dprint("New job with similar properties found on the server [%s->%s]"%  (j, n))
        #print "TOBEADDADE", to_be_added
        self.newJobEvents( newjobs=to_be_added)
        self.saveHistory()
        self.setReady()
        # FIXME STATUS update the status bar with new jobs added


    def newJobEvents(self, newjobs=[]):
        """ receive a pool of new jobs to be 
            added to the history and triggers 
            a UpdateJobHistory event for each of them
        """
        self.dprint("Called with newjobs = %s" % newjobs)
        if not len(newjobs): return
        local = self.history
        remote = self.server.history
        pool = []
        for add in newjobs:
            p = add[0]
            if len(add) >1:
                exp = [ add[1] ]
            else:
                exp = remote[p].keys()
            for e in exp:
                if len(add) > 2:
                    job = [ add[2] ]
                else:
                    job = remote[p][e].keys()
                for j in job:
                    pool.append( (p, e, j) )
        for p,e,j in pool:
            # FIXME ask the server to update jobs that are going to be added...
            info = remote[p][e][j]
            event = RaccoonEvents.UpdateJobHistory(prj=p, exp=e, name=j, jtype=info['resource'], properties = info)
            self.eventManager.dispatchEvent(event)
            self.syncRecStructure(info)

    def syncRecStructure(self, jobinfo):
        """ provide preparatory steps for registration
            of new rec structures coming from newly discovered
            jobs after sync with server
        """
        filename = jobinfo['receptor'] # check if is a PDBQT filename
        sourcedir = jobinfo['vsdir']
        sourcefile = '/'.join([sourcedir, filename])
        destdir = self.getTempDir()
        destfile = destdir + os.sep + filename #$os.path.join([destdir, filename])
        files = [ (sourcefile,destfile) ] 
        # copy the remote receptor file to local temp directory
        problems = self.server.ssh.getfiles(files)
        if len(problems):
            self.dprint("Problems in copying remote receptor files\n%s" % problems)
            return False
        # call the registration function
        return self.registerTarget(destfile)


    def _compareJobs(self, job1, job2):
        """ compare jobs by checking their properties
            to find duplicates
        """
        # these values could mismatch even with identical jobs
        skip = ['status', 'date', 'downloaded', 'summary'] 
        for k1, i1 in job1.items():
            if not k1 in skip:
                try:
                    if not job1[k1] == job2[k1]:
                        return False
                except:
                    return False
        return True
        


    def disconnectSshServer(self):
        """ """
        if self.server == None:
            return
        self.server.disconnect()
        self.server = None
        event = RaccoonEvents.ServerDisconnection()
        self.eventManager.dispatchEvent(event)        

    def getServerInfo(self, name):
        """ retrieve server info from its name """
        return self.settings['servers']['ssh'].get(name, None)

    def findSshServerByHostname(self, name, username=None):
        """ look for server info by hostname """
        self.dprint("searching for server name[%s] username [%s]" % (name, username) )
        print "searching for server name[%s] username [%s]" % (name, username)
        for sname, sinfo in self.settings['servers']['ssh'].items():
            if not sinfo.has_key('hostname'):
                return None
            if sinfo['hostname'] == name:
                if username == None:
                    return sname
                else:
                    if sinfo['username'] == username:
                        return sname
        return None

    def submitLocal(self, job_info):
        """ """
        print "Got job info:", job_info
        return True

    def testSshJobs(self, job_info):
        """ check if jobs that are going to be generated with job_info
            exist already, locally or on the server
        """
        report = {'server_duplicates' : [],
                  'local_duplicates'  : [],
                  }
        server = self.server
        service = self.server.service(self.dockingservice)
        prj = job_info['prj']
        exp = job_info['exp']
        tag = job_info['tag']
        for rec in self.engine.receptors():
            n = service.processor.makeVsName(recname=rec, ligsource=self.ligand_source, tag = tag)
            if server.findJob(prj, exp, n): 
                report['server_duplicates'].append([prj, exp, rec, n])
            else:
                pass
            if self.findJob(prj, exp, n): 
                report['local_duplicates'].append([prj, exp, rec, n])
        return report

    
    def submitSsh(self, job_info, duplicates='skip', cb=None):
        """ job_info = { 'prj' : xxx, 'exp' : xxx, 'tag' : xxx, }
        """
        #self.debug = True
        #report = { 'submissions': [], 'server_duplicates' : [], 'local_duplicates' : [] }
        submissions = []
        server = self.server
        service = self.server.service(self.dockingservice)
        prj = job_info['prj']
        exp = job_info['exp']
        tag = job_info['tag']
        submission_input = []

        # check for duplicate job names XXX FIXME Make this a separate function
        for rec in self.engine.receptors():
            n = service.processor.makeVsName(recname=rec, ligsource=self.ligand_source, tag = tag)
            if server.findJob(prj, exp, n): 
                if duplicates == 'skip': # we don't save the rec + name
                    continue
                elif duplicates == 'rename':
                    curr_name = n
                    c = 0
                    while server.findJob(prj, exp, curr_name):
                        curr_name = "%s__copy%s" % (n, c)
                    n = curr_name
                elif duplicates == 'overwrite': # we delete the vs dir, 'cause we assume it's there
                    # FIXME ? remove also local job info?
                    self.unregisterJob(name = n, prj = prj, exp=exp,  removefiles=True)
                    server.unregisterJob(name = n, prj = prj, exp=exp, 
                            removefiles=True, kill=True)
                submission_input.append([rec, n])
            else:
                submission_input.append([rec, n])
            if self.findJob(prj, exp, n): 
                report['local_duplicates'].append([prj, exp, rec, n])
        ### FIXME end of future separate function

        if len(submission_input) == 0:
            return submissions
    
        status, expdir = server.makeExperimentDir(job_info, _type = 'vs')
        if not status:
            print "FATAL ERROR:", expdir
            return False

        cb = None # gui callback
        for rec, name in submission_input:
            data = job_info.copy()
            data['name'] = name
            # register the receptor in target dbase
            submission_data = service.processor.start(app = self, engine = self.engine, 
                                         jobinfo = data,
                                         expdir=expdir, 
                                         ligsource=self.ligand_source, 
                                         recname=rec, 
                                         callback = cb)
            if submission_data['error'] == None:
                submissions.append(submission_data['info'])
                # register job in local history
                self.registerJob(submission_data['info'])
                submissions.append(submission_data['info'])
                e = RaccoonEvents.UpdateJobHistory(prj=prj, exp=exp, name=name, 
                    jtype='ssh', properties = submission_data['info'][prj][exp][name])
                self.eventManager.dispatchEvent(e)
        #self.debug = False
        return submissions

    def submitOpal(self, job_info):
        """ """
        print "Got job info:", job_info
        return True

    def unregisterJob(self, name, prj=None, exp=None, removefiles=True):
        """ unregister single vs jobs
            from the CLIENT and update the history file

            by default associated result files, if any, will be deleted 
            (removefiles option) and running jobs killed (kill option)
        """
        # check that status is useful
        #safe_list = ['downloaded', 'killed', 'transferred']
        print "APPUNREGISTERJOB, p[%s] e[%s] n[%s" % (prj, exp, name)
        found = self.findJob(prj, exp, name)
        if found == ():
            return
        status = self.history[prj][exp][name]['status']
        if removefiles:
            #print "Warning: deleting job record but files are still in Raccoon directory!"
            self.deleteJobData(name, prj, exp)
        self.deleteJobRecord(name, prj, exp)
        self.saveHistory()
        return True

    def deleteJobData(self, name, prj=None, exp=None):
        """ delete local copies of the job files
        """
        print "APCALLED deleteJobData" , name, prj,exp
        vsdir = self.history[prj][exp][name]['vsdir']
        self.dprint("deleting vsdir [%s]" % vsdir)
        try:
            shutil.rmtree(vsdir)
            return True
        except:
            e = sys.exc_info()[1]
            self.dprint("Error deleting job dir [%s] : %s" % (vsdir, e) )
            return e

    def deleteJobRecord(self, name, prj=None, exp=None):
        """ remove a job record from the history dictionary
            if it is the only item in the experiment and the project,
            remove them too
        """
        data = self.history[prj][exp][name]
        self.dprint("deleting job record of [%s]" % name)
        del self.history[prj][exp][name]
        if len(self.history[prj][exp].keys()):
            return True
        self.dprint("Exp [%s] is now empty, deleting" % exp)
        del self.history[prj][exp]
        if len(self.history[prj].keys()):
            return True
        self.dprint("Prj [%s] is now empty, deleting" % prj)
        del self.history[prj]
        return True
    # XXX 


    def deleteResults(self, resname=None):
        """ remove results from the current session
            if resname is not specified, all results are removed
        """
        if not len(self.results.keys()):
            return
        if resname == None:
            self.results.clear()
        else:
            if isinstance(resname, list):
                items = resname
            else:
                items = [resname]
            for i in items:
                self.results.pop(i)
        e = RaccoonEvents.ResultsImportedDeleted()
        self.eventManager.dispatchEvent(e)

    def importResults(self, data, name, path, rec=None):
        """ add results contained in {data} to 
            the current session; the format is { 'name' : { 'results : {data}, 
                                                            'path' : path, ...  } }
            TODO check for duplicates?
        """
        for n, d in data.items():
            d['selected'] = False
        
        if rec == None:
            lig = data.keys()[0]
            recname = data[lig]['data'][0]['recname']
            rec = "%s%s%s%s" % (path, os.sep, recname, '.pdbqt')

        info = {name : { 'results' : data,
                         'path': path,
                         'rec': rec,
                         } }
        self.results.update(info)
        e = RaccoonEvents.ResultsImportedDeleted()
        self.eventManager.dispatchEvent(e)

    def resPropertiesReset(self, event=None):
        """ reset the results properties to the initial state
        """
        self.results_properties = {}
        self.results_properties['energy'] = [0,1]
        self.results_properties['leff'] = [0,1]

    def updateResultsProperties(self, event=None):
        """ this function is called when new data is added
            to provide the min/max properties range
            of the current set
        """
        try:
            self.setBusy()
        except:
            pass
        ebest  = lebest = 10E99
        eworst = leworst = -10E99

        self.resPropertiesReset()
        for rname, rinfo in self.results.items():
            rdata = rinfo['results']
            for lname, linfo in rdata.items():
                try:
                    prop = linfo['data']
                except:
                    #print "=" * 10
                    #print linfo
                    #print "=" * 10
                    pass
                ebest = min(ebest, prop[0]['energy'])
                eworst = max(eworst, prop[0]['energy'])
                lebest = min(lebest, prop[0]['leff'])
                leworst = max(leworst, prop[0]['leff'])
        if not len(self.results.keys()):
            eworst, ebest = 0,1
            leworst, lebest = 0,1
        self.results_properties['energy'] = [eworst, ebest]
        self.results_properties['leff'] = [leworst, lebest]
        try:
            self.setReady()
        except:
            pass


    def countResults(self):
        """ return the total number of ligand results
            currently present in the session
        """
        c=0
        for n, info in self.results.items():
            d = info['results']
            c += len(d.items())
        return c


    def acceptedResults(self, anything=False):
        """ return accepted results"""
        accepted = []
        for rname, rinfo in self.results.items():
            rdata = rinfo['results']
            for lname, linfo in rdata.items():
                if len(linfo['accepted']):
                    d = linfo['data'][linfo['accepted'][0]] # only first accepted pose will be reported
                elif anything:
                    d = linfo['data'][0] # first pose
                else:
                    continue
                a = { 'selected' : linfo['selected'],
                      'name': lname,
                      'recname': d['recname'],
                      'energy': d['energy'],
                      'leff': d['leff'],
                      'poses': d['total'],
                      'job': rname,
                      'filename': d['pdbqt'],
		              'path' : rinfo['path'],
                     }
                accepted.append(a)
        return sorted(accepted, key=itemgetter('energy'))
            
    def selectedResults(self):
        """ return selected results"""
        return [ a for a in self.acceptedResults() if a['selected'] ]




class RaccoonGUI(RaccoonMaster, RaccoonBasics.RaccoonDefaultWidget):
    """
    top object for RaccoonGUI app
    
    event manager is an external instance of an EventHandler class
    """
    def __init__(self, parent=None, resource = 'local', dockengine='vina', eventmanager=None,
        racdir=None, debug=False):
        self.master = parent
        RaccoonMaster.__init__(self, resource, dockengine, eventmanager,racdir, debug)
        RaccoonBasics.RaccoonDefaultWidget.__init__(self,parent)
        self.parent.title("AutoDock | Raccoon2 [ resource : %s ]")

        # MOVE THIS TO THE VIEIWER TAB OBJ
        #self.settings['viewer'] = {}
        self.parent.wm_protocol("WM_DELETE_WINDOW", self.confirm)

        self.viewer = None
        self.active_camera = None

        Pmw.initialise()
        # create notebook
        self.notebook = Pmw.NoteBook(self.parent)
        self.tabs = {}
        for tab in ['Setup', 'Ligands', 'Receptors', 'Config', 'Job manager',
                    'Analysis']: 
            self.tabs[tab] = self.notebook.add(tab)
        self.notebook.pack(expand=1, fill='both')
        #self.notebook.setnaturalsize(self.tabs.keys())

        # add status bar
        self.statusbar = Pmw.MessageBar(self.parent,
            entry_width=80,
            entry_relief='groove',
            entry_background='white',
            labelpos='w',
            label_text='Status:') 
        self.statusbar.pack(fill='x', expand=0,padx=3,pady=3,anchor='s',side='bottom')

        # create setup tab 1
        self.setupTab = SetupTab(self, self.tabs['Setup'])

        # create ligand tab 2
        self.ligandTab = LigandTab(self, self.tabs['Ligands'])

        # create receptor tab 3
        self.receptorTab = ReceptorTab(self, self.tabs['Receptors'])

        # create config tab 4
        self.configTab = ConfigTab(self, self.tabs['Config'])
        cb = CallbackFunction( self.switchCams, self.configTab.camera_name )
        self.notebook.component('Config-tab').bind('<ButtonRelease-1>', cb)

        # create jobman tab 5
        self.jobmanTab = JobManagerTab(self, self.tabs['Job manager'])


        # create analysis tab 6
        # hack to trigger optimal Analysis tab size
        # only the first time it is shown
        self._firstclick = True 
        self.analysisTab = AnalysisTab(self, self.tabs['Analysis'])
        cb = CallbackFunction( self.switchCams, self.analysisTab.visualTab.camera_name )
        self.notebook.component('Analysis-tab').bind('<ButtonRelease-1>', cb)
        self.setResource()

        self.notebook.setnaturalsize(self.tabs.keys())
        #self.analysisTab.dataTab.setOptimalSize()

        #self._debug()

    def _debug(self):
        """ """
        p = self.tabs['debug']
        cb = CallbackFunction( RaccoonBasics.About, (p,))
        tk.Button(p, text='test', command = cb).pack()

    def confirm(self, event=None):
        """ confirm exit """
        t = 'Confirm exit Raccoon'
        i = 'info'
        m = 'Are you sure you want to close Raccoon?'
        if tmb.askyesno(parent=self.master, title=t, icon=i, message=m):
            #self.parent.update_idletasks()
            #self.parent.destroy()
            sys.exit()

    def setResource(self):
        """ """
        # FIXME this is only for released version
        self.setupTab.b2.invoke()

    def switchCams(self, cam, event=None):
        """callback used to turn on cameras exclusively"""
        self.viewer.activateCam([cam], only=1)
        if self._firstclick and cam == self.analysisTab.visualTab.camera_name:
            # hack to trigger optimal Analysis tab size
            # only the first time it is shown
            self.master.after(100, self.analysisTab.dataTab.setOptimalSize)
            self._firstclick = False

    def setBusy(self, event=None):
        """ set cursor to busy"""
        self.parent.configure(cursor='watch')
        self.parent.update_idletasks()

    def setReady(self, event=None):
        """ set cursor to default"""
        self.parent.configure(cursor='arrow')
        self.parent.update_idletasks()



if __name__ == '__main__':
    import sys
    import Tkinter as tk
    root = tk.Tk()
    rac = RaccoonGUI(parent=root)
    #rac.settings['servers']['ssh']['Garibaldi (Scripps only)'] = { 'address': 'garibaldi.scripps.edu',
    #    'username' : 'forli', 'password' : None, 'pkey': None}
    if len(sys.argv) > 1: 
        for i in sys.argv:
            if i == '-i':
                print "INTERACTIVE"

                sys.stdin = sys.__stdin__
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                #print "HERE", rac
                import code
                try: # hack to really exit code.interact 
                    mod = __import__('__main__')
                    code.interact( 'Pmv Interactive Shell', local=mod.__dict__)
                except:
                    pass
    else:
        print "AUTO"
        root.mainloop()   #root.mainloop()


        



